"""Frozen Router V1 orchestration: streams, deterministic merge, attribution, arms."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    DEFAULT_HISTORY_TURNS,
    rewrite_or_keep,
)
from .decomposer_v1 import DecomposerClient, DecomposerOutcome, not_called
from .generator import GeneratedAnswerCache, generate_grounded_answer
from .reranked_retriever import RerankedRetrievalResult
from .router_v1 import (
    DIRECT,
    DECOMPOSE,
    RouterChatClient,
    RouterClient,
    RouterDecision,
)
from .router_v1_identity import decomposer_prompt_identity, file_sha256, router_prompt_identity
from .router_v1_trace import (
    AttributionResult,
    DecomposerTrace,
    MergeResult,
    MergeSelection,
    ModelCallRecord,
    RouterTrace,
    RouterV1Result,
    RouterV1Trace,
    StreamResult,
)

FIXED_DIRECT = "FIXED_DIRECT"
FIXED_DECOMPOSE = "FIXED_DECOMPOSE"
ROUTED = "ROUTED"
ARM_NAMES = (FIXED_DIRECT, FIXED_DECOMPOSE, ROUTED)

BASE_STREAM_ID = "base"
EVIDENCE_TARGET_COUNT = 5
STREAM_TOP_K = 5
STREAM_DIAGNOSTIC_K = 40
DECOMPOSE_UNAVAILABLE = "DECOMPOSE_UNAVAILABLE"
INSUFFICIENT_SUBQUERY_STREAMS = "insufficient_successful_subquery_streams"
SUBQUERY_STREAM_TYPES = ("subquery", "base")


class RetrieverBackend(Protocol):
    def search(self, query: str, top_k: int = STREAM_TOP_K) -> Sequence[RerankedRetrievalResult]: ...


class ObservedChatClient:
    """Record per-stage provider usage without changing the chat interface."""

    def __init__(self, client: RouterChatClient) -> None:
        self._client = client
        self.stage = "unassigned"
        self.calls: list[ModelCallRecord] = []

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str:
        started = perf_counter()
        metadata: Mapping[str, Any] = {}
        with_metadata = getattr(self._client, "complete_with_metadata", None)
        if callable(with_metadata):
            answer, metadata = with_metadata(
                messages, max_tokens=max_tokens, temperature=temperature
            )
        else:
            answer = self._client.complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )
        if not isinstance(metadata, Mapping):
            metadata = {}
        self.calls.append(
            ModelCallRecord(
                stage=self.stage,
                max_tokens=max_tokens,
                input_tokens=_as_int(metadata.get("input_tokens")),
                output_tokens=_as_int(metadata.get("output_tokens")),
                request_id=_as_str(metadata.get("request_id")),
                response_id=_as_str(metadata.get("response_id")),
                latency_seconds=perf_counter() - started,
            )
        )
        return answer

    def calls_for(self, stage: str) -> tuple[ModelCallRecord, ...]:
        return tuple(call for call in self.calls if call.stage == stage)


@dataclass(frozen=True, slots=True)
class CaseRunResult:
    case_id: str | None
    raw_query: str
    shared_rewrite: str
    rewrite_source: str
    rewrite_calls: tuple[ModelCallRecord, ...]
    results: tuple[tuple[str, RouterV1Result], ...]

    def arm(self, name: str) -> RouterV1Result:
        for arm_name, result in self.results:
            if arm_name == name:
                return result
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "raw_query": self.raw_query,
            "shared_rewrite": self.shared_rewrite,
            "rewrite_source": self.rewrite_source,
            "rewrite_calls": [call.to_dict() for call in self.rewrite_calls],
            "arms": {name: result.to_dict() for name, result in self.results},
        }


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _as_str(value: Any) -> str | None:
    return str(value) if isinstance(value, str) and value else None


def _reconstruct_candidate_orders(
    reranked: Sequence[RerankedRetrievalResult],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    lexical = sorted(
        (item for item in reranked if item.lexical_rank is not None),
        key=lambda item: int(item.lexical_rank),  # type: ignore[arg-type]
    )
    semantic = sorted(
        (item for item in reranked if item.semantic_rank is not None),
        key=lambda item: int(item.semantic_rank),  # type: ignore[arg-type]
    )
    lexical_ids = tuple(item.chunk_id for item in lexical)
    semantic_ids = tuple(item.chunk_id for item in semantic)
    union_ids: list[str] = []
    seen: set[str] = set()
    for item in list(lexical) + list(semantic):
        if item.chunk_id not in seen:
            seen.add(item.chunk_id)
            union_ids.append(item.chunk_id)
    return lexical_ids, semantic_ids, tuple(union_ids)


def run_stream(
    retriever: RetrieverBackend,
    query: str,
    stream_id: str,
    stream_type: str,
    *,
    diagnostic_k: int = STREAM_DIAGNOSTIC_K,
    top_k: int = STREAM_TOP_K,
) -> StreamResult:
    """Run one stream through the existing reranked retriever exactly once."""

    started = perf_counter()
    if not isinstance(query, str) or not query.strip():
        return StreamResult(
            stream_id=stream_id,
            stream_type=stream_type,
            query_text=query if isinstance(query, str) else "",
            failure="blank_query",
            latency_seconds=perf_counter() - started,
        )
    timings = getattr(retriever, "timings", None)
    timing_count = len(timings) if isinstance(timings, list) else None
    try:
        reranked = tuple(retriever.search(query, top_k=diagnostic_k))
        if not reranked:
            raise RuntimeError("stream returned no evidence")
    except Exception as error:
        return StreamResult(
            stream_id=stream_id,
            stream_type=stream_type,
            query_text=query,
            failure=str(error),
            latency_seconds=perf_counter() - started,
        )
    lexical_ids, semantic_ids, union_ids = _reconstruct_candidate_orders(reranked)
    rerank_seconds: float | None = None
    if timing_count is not None and isinstance(timings, list) and len(timings) > timing_count:
        rerank_seconds = float(getattr(timings[-1], "reranker_seconds", 0.0))
    evidence = tuple(reranked[:top_k])
    return StreamResult(
        stream_id=stream_id,
        stream_type=stream_type,
        query_text=query,
        lexical_candidate_ids=lexical_ids,
        semantic_candidate_ids=semantic_ids,
        union_ids=union_ids,
        reranked_ids=tuple(item.chunk_id for item in reranked),
        stream_top5_ids=tuple(item.chunk_id for item in evidence),
        evidence=evidence,
        latency_seconds=perf_counter() - started,
        rerank_latency_seconds=rerank_seconds,
        failure=None,
    )


def merge_streams(
    streams: Sequence[StreamResult],
    *,
    target: int = EVIDENCE_TARGET_COUNT,
) -> MergeResult:
    """Frozen deterministic round-robin merge over per-stream Top5 evidence."""

    if target <= 0:
        raise ValueError("target must be positive")
    usable = [stream for stream in streams if stream.ok]
    pointers = {id(stream): 0 for stream in usable}
    seen: set[str] = set()
    selections: list[MergeSelection] = []
    evidence_by_id: dict[str, RerankedRetrievalResult] = {}
    order = 0
    progress = True
    while len(selections) < target and progress:
        progress = False
        for stream in usable:
            if len(selections) >= target:
                break
            index = pointers[id(stream)]
            while index < len(stream.evidence) and stream.evidence[index].chunk_id in seen:
                index += 1
            pointers[id(stream)] = index
            if index < len(stream.evidence):
                item = stream.evidence[index]
                seen.add(item.chunk_id)
                evidence_by_id[item.chunk_id] = item
                order += 1
                selections.append(
                    MergeSelection(
                        chunk_id=item.chunk_id,
                        source_stream=stream.stream_id,
                        source_rank=index + 1,
                        selection_order=order,
                    )
                )
                pointers[id(stream)] = index + 1
                progress = True
    duplicate_sources: list[tuple[str, tuple[str, ...]]] = []
    for selection in selections:
        sources = tuple(
            stream.stream_id
            for stream in usable
            if selection.chunk_id in stream.stream_top5_ids
        )
        duplicate_sources.append((selection.chunk_id, sources))
    return MergeResult(
        selections=tuple(selections),
        final_evidence=tuple(evidence_by_id[item.chunk_id] for item in selections),
        duplicate_sources=tuple(duplicate_sources),
    )


def classify_attribution(
    merge: MergeResult,
    base_stream: StreamResult,
    *,
    applicable: bool,
) -> AttributionResult:
    """Classify evidence first selected through a subquery stream."""

    base_top5 = set(base_stream.stream_top5_ids)
    base_union = set(base_stream.union_ids)
    representation_gain: list[str] = []
    selection_ranking_gain: list[str] = []
    for selection in merge.selections:
        if selection.source_stream == base_stream.stream_id:
            continue
        if selection.chunk_id not in base_union:
            representation_gain.append(selection.chunk_id)
        elif selection.chunk_id not in base_top5:
            selection_ranking_gain.append(selection.chunk_id)
    zero_evidence_gain = not any(
        selection.chunk_id not in base_top5 for selection in merge.selections
    )
    return AttributionResult(
        representation_gain_ids=tuple(representation_gain),
        selection_ranking_gain_ids=tuple(selection_ranking_gain),
        zero_evidence_gain=zero_evidence_gain,
        applicable=applicable,
    )


class RouterV1Pipeline:
    """Execute FIXED_DIRECT, FIXED_DECOMPOSE, or ROUTED for one shared rewrite."""

    def __init__(
        self,
        retriever: RetrieverBackend,
        client: RouterChatClient,
        *,
        model: str,
        router: RouterClient | None = None,
        decomposer: DecomposerClient | None = None,
        generation_cache: GeneratedAnswerCache | None = None,
        max_history_turns: int = DEFAULT_HISTORY_TURNS,
        provider: str = "deepseek",
        rewrite_prompt_hash: str | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be blank")
        self._retriever = retriever
        self._client = client
        self._model = model
        self._router = router
        self._decomposer = decomposer
        self._generation_cache = generation_cache
        self._max_history_turns = max_history_turns
        self._provider = provider
        self._router_identity = router_prompt_identity()
        self._decomposer_identity = decomposer_prompt_identity()
        if rewrite_prompt_hash is None:
            try:
                rewrite_prompt_hash = file_sha256(Path(__file__).with_name("conversation.py"))
            except OSError:
                rewrite_prompt_hash = None
        self._rewrite_prompt_hash = rewrite_prompt_hash

    def rewrite(
        self,
        raw_query: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> tuple[str, tuple[ModelCallRecord, ...]]:
        observed = ObservedChatClient(self._client)
        observed.stage = "rewrite"
        rewritten = rewrite_or_keep(
            history,
            raw_query,
            observed,
            max_history_turns=self._max_history_turns,
        )
        return rewritten, tuple(observed.calls)

    def run_case(
        self,
        raw_query: str,
        history: Sequence[Mapping[str, str]] = (),
        *,
        arms: Sequence[str] = ARM_NAMES,
        case_id: str | None = None,
        history_identifier: str | None = None,
        shared_rewrite: str | None = None,
    ) -> CaseRunResult:
        if shared_rewrite is None:
            rewritten, rewrite_calls = self.rewrite(raw_query, history)
            rewrite_source = "api"
        else:
            rewritten, rewrite_calls = shared_rewrite, ()
            rewrite_source = "provided"
        results = tuple(
            (
                arm,
                self.run_arm(
                    arm,
                    raw_query,
                    history,
                    rewritten,
                    case_id=case_id,
                    history_identifier=history_identifier,
                    rewrite_source=rewrite_source,
                ),
            )
            for arm in arms
        )
        return CaseRunResult(
            case_id=case_id,
            raw_query=raw_query,
            shared_rewrite=rewritten,
            rewrite_source=rewrite_source,
            rewrite_calls=rewrite_calls,
            results=results,
        )

    def run_arm(
        self,
        arm: str,
        raw_query: str,
        history: Sequence[Mapping[str, str]],
        rewritten_query: str,
        *,
        case_id: str | None = None,
        history_identifier: str | None = None,
        rewrite_source: str = "provided",
    ) -> RouterV1Result:
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm: {arm}")
        started = perf_counter()
        observed = ObservedChatClient(self._client)
        router = self._router or RouterClient(observed, request_model=self._model)
        decomposer = self._decomposer or DecomposerClient(observed, request_model=self._model)
        router_decision: RouterDecision | None = None
        decomposer_outcome: DecomposerOutcome = not_called()
        fallback_reason: str | None = None
        counterfactual_decompose_available = True
        executed_path = DIRECT

        if arm == FIXED_DECOMPOSE:
            observed.stage = "decomposer"
            decomposer_outcome = decomposer.decompose(rewritten_query)
            if decomposer_outcome.available:
                executed_path = DECOMPOSE
            else:
                fallback_reason = DECOMPOSE_UNAVAILABLE
                counterfactual_decompose_available = False
        elif arm == ROUTED:
            observed.stage = "router"
            router_decision = router.decide(rewritten_query)
            if router_decision.decision == DECOMPOSE:
                observed.stage = "decomposer"
                decomposer_outcome = decomposer.decompose(rewritten_query)
                if decomposer_outcome.available:
                    executed_path = DECOMPOSE
                else:
                    fallback_reason = decomposer_outcome.fallback_reason or "decomposer_failure"

        streams: list[StreamResult] = [
            run_stream(self._retriever, rewritten_query, BASE_STREAM_ID, "base")
        ]
        base_stream = streams[0]
        if executed_path == DECOMPOSE:
            for index, subquery in enumerate(decomposer_outcome.subqueries, start=1):
                streams.append(
                    run_stream(self._retriever, subquery, f"subquery_{index}", "subquery")
                )
            successful_subqueries = [
                stream
                for stream in streams
                if stream.stream_type == "subquery" and stream.ok
            ]
            if len(successful_subqueries) < 2:
                executed_path = DIRECT
                fallback_reason = INSUFFICIENT_SUBQUERY_STREAMS
                counterfactual_decompose_available = False

        execution_success = True
        error_stage: str | None = None
        error: str | None = None
        answer: str | None = None
        citations: tuple[dict[str, Any], ...] = ()
        citation_validation: dict[str, Any] | None = None
        generation_source: str | None = None
        merge: MergeResult | None = None
        attribution: AttributionResult | None = None

        if base_stream.failure is not None:
            execution_success = False
            error_stage = "retrieval"
            error = base_stream.failure
        else:
            merge_streams_input = (
                streams if executed_path == DECOMPOSE else [base_stream]
            )
            merge = merge_streams(merge_streams_input)
            attribution = classify_attribution(
                merge, base_stream, applicable=executed_path == DECOMPOSE
            )
            observed.stage = "generation"
            try:
                generated = generate_grounded_answer(
                    raw_query,
                    history,
                    merge.final_evidence,
                    observed,
                    model=self._model,
                    cache=self._generation_cache,
                    max_history_turns=self._max_history_turns,
                )
                answer = str(generated["answer"])
                citations = tuple(dict(source) for source in generated["sources"])
                citation_validation = dict(generated["validation"])
                generation_source = str(generated["response_source"])
                if not citation_validation.get("valid", False):
                    execution_success = False
                    error_stage = "citation_validation"
                    warnings = citation_validation.get("warnings", [])
                    error = ", ".join(str(value) for value in warnings) or "invalid citations"
            except Exception as generation_error:
                execution_success = False
                error_stage = "generation"
                error = str(generation_error)

        trace = RouterV1Trace(
            case_id=case_id,
            raw_query=raw_query,
            history_present=bool(history),
            history_identifier=history_identifier,
            shared_rewrite=rewritten_query,
            rewrite_source=rewrite_source,
            rewrite_model_version=self._model,
            rewrite_prompt_version=CONTEXTUALIZER_PROMPT_VERSION,
            rewrite_prompt_hash=self._rewrite_prompt_hash,
            router=self._router_trace(router_decision, observed),
            decomposer=self._decomposer_trace(decomposer_outcome),
            streams=tuple(streams),
            merge=merge,
            attribution=attribution,
            requested_arm=arm,
            executed_path=executed_path,
            router_decision=router_decision.decision if router_decision else None,
            fallback_reason=fallback_reason,
            decompose_available=decomposer_outcome.available,
            counterfactual_decompose_available=counterfactual_decompose_available,
            execution_success=execution_success,
            error_stage=error_stage,
            error=error,
            generation_source=generation_source,
            model_calls=tuple(observed.calls),
            total_latency_seconds=perf_counter() - started,
        )
        evidence = merge.final_evidence if merge is not None else ()
        return RouterV1Result(
            case_id=case_id,
            requested_arm=arm,
            executed_path=executed_path,
            router_decision=router_decision.decision if router_decision else None,
            fallback_reason=fallback_reason,
            decompose_available=decomposer_outcome.available,
            counterfactual_decompose_available=counterfactual_decompose_available,
            execution_success=execution_success,
            error_stage=error_stage,
            error=error,
            raw_query=raw_query,
            rewritten_query=rewritten_query,
            evidence=evidence,
            streams=tuple(streams),
            merge=merge,
            attribution=attribution,
            answer=answer,
            citations=citations,
            citation_validation=citation_validation,
            generation_source=generation_source,
            trace=trace,
        )

    def _router_trace(
        self,
        decision: RouterDecision | None,
        observed: ObservedChatClient,
    ) -> RouterTrace:
        calls = observed.calls_for("router")
        return RouterTrace(
            called=decision is not None,
            provider=self._provider,
            request_model=self._model,
            response_model=None,
            prompt_sha256=self._router_identity["prompt_sha256"],
            schema_sha256=self._router_identity["schema_sha256"],
            raw_response=decision.raw_response if decision else None,
            parsed_decision=decision.decision if decision else None,
            raw_reason_code=decision.raw_reason_code if decision else None,
            effective_reason_code=decision.effective_reason_code if decision else None,
            reason_validity=decision.reason_validity if decision else None,
            schema_anomalies=decision.schema_anomalies if decision else (),
            failure=decision.failure if decision else None,
            fallback=decision.fallback if decision else False,
            input_tokens=decision.input_tokens if decision else None,
            output_tokens=decision.output_tokens if decision else None,
            latency_seconds=decision.latency_seconds if decision else None,
        )

    def _decomposer_trace(self, outcome: DecomposerOutcome) -> DecomposerTrace:
        return DecomposerTrace(
            called=outcome.called,
            available=outcome.available,
            model_version=self._model if outcome.called else None,
            prompt_sha256=self._decomposer_identity["prompt_sha256"] if outcome.called else None,
            schema_sha256=self._decomposer_identity["schema_sha256"] if outcome.called else None,
            raw_response=outcome.raw_response,
            raw_subqueries=outcome.raw_subqueries,
            validated_subqueries=outcome.subqueries,
            removed_subqueries_with_reason=tuple(
                item.to_dict() for item in outcome.removed
            ),
            failure=outcome.failure,
            fallback=outcome.fallback_reason,
            input_tokens=outcome.input_tokens,
            output_tokens=outcome.output_tokens,
            latency_seconds=outcome.latency_seconds,
        )
