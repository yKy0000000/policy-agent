"""Deterministic orchestration for the GitHub policy support pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    DEFAULT_HISTORY_TURNS,
    RewriteCache,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from .evidence_budget import EvidenceBudgetConfig, select_evidence_prefix
from .evidence_selector import CoverageSelectorConfig, select_evidence_set
from .generator import GeneratedAnswerCache, generate_grounded_answer
from .reranked_retriever import RerankedRetrievalResult


EVIDENCE_TOP_K = 5


class AgentChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str: ...


class AgentRetriever(Protocol):
    def search(
        self,
        query: str,
        top_k: int = EVIDENCE_TOP_K,
    ) -> Sequence[RerankedRetrievalResult]: ...


class AgentPipelineError(RuntimeError):
    """A technical failure at one explicit orchestration stage."""

    def __init__(self, stage: str, message: str, trace: ExecutionTrace | None = None) -> None:
        self.stage = stage
        self.trace = trace
        super().__init__(f"policy agent {stage} stage failed: {message}")


@dataclass(slots=True)
class ExecutionTrace:
    """Request-local observations; no field influences pipeline decisions."""

    original_query: str
    rewritten_query: str | None = None
    evidence_chunk_ids: tuple[str, ...] = ()
    generated_answer: str | None = None
    citation_validation: dict[str, Any] | None = None
    rewrite_source: str | None = None
    generation_source: str | None = None
    rewrite_seconds: float | None = None
    retrieval_seconds: float | None = None
    rerank_seconds: float | None = None
    evidence_selection_seconds: float | None = None
    generation_seconds: float | None = None
    validation_seconds: float | None = None
    total_seconds: float | None = None
    rewrite_input_tokens: int | None = None
    rewrite_output_tokens: int | None = None
    generation_input_tokens: int | None = None
    generation_output_tokens: int | None = None
    remote_llm_calls: int = 0
    evidence_mode: str = "fixed_top5"
    selected_k: int | None = None
    available_evidence_candidates: int | None = None
    evidence_expansion_reason: str | None = None
    evidence_stop_reason: str | None = None
    evidence_token_count: int | None = None
    evidence_token_budget: int | None = None
    evidence_original_ranks: tuple[int, ...] = ()
    evidence_selection_steps: tuple[dict[str, Any], ...] = ()
    error_stage: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "evidence_chunk_ids": list(self.evidence_chunk_ids),
            "generated_answer": self.generated_answer,
            "citation_validation": self.citation_validation,
            "rewrite_source": self.rewrite_source,
            "generation_source": self.generation_source,
            "latency_seconds": {
                "rewrite": self.rewrite_seconds,
                "retrieval": self.retrieval_seconds,
                "rerank": self.rerank_seconds,
                "evidence_selection": self.evidence_selection_seconds,
                "generation": self.generation_seconds,
                "validation": self.validation_seconds,
                "total": self.total_seconds,
            },
            "token_usage": {
                "rewrite_input": self.rewrite_input_tokens,
                "rewrite_output": self.rewrite_output_tokens,
                "generation_input": self.generation_input_tokens,
                "generation_output": self.generation_output_tokens,
            },
            "remote_llm_calls": self.remote_llm_calls,
            "evidence_budget": {
                "mode": self.evidence_mode,
                "selected_k": self.selected_k,
                "available_candidates": self.available_evidence_candidates,
                "expansion_reason": self.evidence_expansion_reason,
                "stop_reason": self.evidence_stop_reason,
                "selected_token_count": self.evidence_token_count,
                "token_budget": self.evidence_token_budget,
                "original_ranks": list(self.evidence_original_ranks),
                "selection_steps": list(self.evidence_selection_steps),
            },
            "error_stage": self.error_stage,
            "error": self.error,
        }


class _ObservedClient:
    """Capture model-call usage without changing the existing text interface."""

    def __init__(self, client: AgentChatClient, trace: ExecutionTrace) -> None:
        self.client = client
        self.trace = trace
        self.stage = "rewrite"

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str:
        self.trace.remote_llm_calls += 1
        with_usage = getattr(self.client, "complete_with_usage", None)
        if callable(with_usage):
            answer, usage = with_usage(messages, max_tokens=max_tokens, temperature=temperature)
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            if self.stage == "rewrite":
                self.trace.rewrite_input_tokens = input_tokens
                self.trace.rewrite_output_tokens = output_tokens
            else:
                self.trace.generation_input_tokens = input_tokens
                self.trace.generation_output_tokens = output_tokens
            return answer
        return self.client.complete(messages, max_tokens=max_tokens, temperature=temperature)


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Structured successful output from one deterministic pipeline run."""

    answer: str
    citations: tuple[dict[str, Any], ...]
    citation_ids: tuple[str, ...]
    rewritten_query: str
    evidence: tuple[RerankedRetrievalResult, ...]
    citation_validation: dict[str, Any]
    rewrite_response_source: str
    generation_response_source: str
    trace: ExecutionTrace | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [dict(citation) for citation in self.citations],
            "citation_ids": list(self.citation_ids),
            "rewritten_query": self.rewritten_query,
            "evidence": [item.to_dict() for item in self.evidence],
            "citation_validation": dict(self.citation_validation),
            "rewrite_response_source": self.rewrite_response_source,
            "generation_response_source": self.generation_response_source,
            "trace": self.trace.to_dict() if self.trace else None,
        }


class PolicySupportAgent:
    """Run the fixed rewrite, retrieval, generation, and validation workflow."""

    def __init__(
        self,
        retriever: AgentRetriever,
        client: AgentChatClient,
        *,
        model: str,
        rewrite_cache: RewriteCache | None = None,
        generation_cache: GeneratedAnswerCache | None = None,
        max_history_turns: int = DEFAULT_HISTORY_TURNS,
        adaptive_evidence: bool = False,
        evidence_budget: EvidenceBudgetConfig | None = None,
        evidence_mode: str | None = None,
        coverage_config: CoverageSelectorConfig | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be blank")
        if max_history_turns < 0:
            raise ValueError("max_history_turns must be non-negative")
        self._retriever = retriever
        self._client = client
        self._model = model
        self._rewrite_cache = rewrite_cache
        self._generation_cache = generation_cache
        self._max_history_turns = max_history_turns
        if evidence_mode not in (None, "fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2"):
            raise ValueError("unknown evidence mode")
        if adaptive_evidence and evidence_mode not in (None, "adaptive_prefix_v1"):
            raise ValueError("--adaptive-evidence conflicts with evidence_mode")
        self._evidence_mode = evidence_mode or ("adaptive_prefix_v1" if adaptive_evidence else "fixed_top5")
        self._evidence_budget = evidence_budget or EvidenceBudgetConfig()
        self._coverage_config = coverage_config or CoverageSelectorConfig()

    @classmethod
    def from_project(
        cls,
        project_root: Path | str | None = None,
        *,
        env_file: Path | str | None = None,
        device: str = "cpu",
        rewrite_cache_path: Path | str | None = None,
        generation_cache_path: Path | str | None = None,
        adaptive_evidence: bool = False,
        evidence_budget: EvidenceBudgetConfig | None = None,
        evidence_mode: str | None = None,
        coverage_config: CoverageSelectorConfig | None = None,
    ) -> "PolicySupportAgent":
        """Load the existing indexes, local models, LLM client, and caches."""

        from .indexing import load_index
        from .llm_client import LLMConfig, OpenAIChatCompletionsClient
        from .reranked_retriever import RerankedPolicyRetriever
        from .reranker import CrossEncoderReranker
        from .retriever import PolicyRetriever
        from .semantic_embeddings import SentenceTransformerEncoder
        from .semantic_indexing import load_semantic_index
        from .semantic_retriever import SemanticPolicyRetriever

        root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        config = LLMConfig.from_env(env_file or root / ".env")
        lexical_index = load_index(root / "cache" / "policy_index.json")
        semantic_index = load_semantic_index(root / "cache" / "semantic_index.json")
        if [chunk.to_dict() for chunk in lexical_index.chunks] != [
            chunk.to_dict() for chunk in semantic_index.chunks
        ]:
            raise ValueError("lexical and semantic indexes do not contain identical chunks")

        model_cache = root / "cache" / "huggingface"
        semantic_encoder = SentenceTransformerEncoder(
            semantic_index.model_name,
            cache_folder=model_cache,
            device=device,
            local_files_only=True,
        )
        reranker = CrossEncoderReranker(
            cache_folder=model_cache,
            device=device,
            local_files_only=True,
        )
        retriever = RerankedPolicyRetriever(
            PolicyRetriever(lexical_index),
            SemanticPolicyRetriever(semantic_index, semantic_encoder),
            reranker,
        )
        return cls(
            retriever,
            OpenAIChatCompletionsClient(config),
            model=config.model,
            rewrite_cache=RewriteCache(
                rewrite_cache_path if rewrite_cache_path is not None
                else root / "cache" / "query_rewrites.json"
            ),
            generation_cache=GeneratedAnswerCache(
                generation_cache_path if generation_cache_path is not None
                else root / "cache" / "generated_answers.json"
            ),
            adaptive_evidence=adaptive_evidence,
            evidence_budget=evidence_budget,
            evidence_mode=evidence_mode,
            coverage_config=coverage_config,
        )

    def answer(
        self,
        latest_question: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> AgentResult:
        """Answer one question through the fixed pipeline, or raise a staged error."""

        started = perf_counter()
        question = latest_question.strip()
        if not question:
            raise ValueError("latest_question must not be blank")
        recent_history = select_recent_history(
            history,
            max_turns=self._max_history_turns,
        )
        trace = ExecutionTrace(original_query=latest_question)
        trace.evidence_mode = self._evidence_mode
        observed_client = _ObservedClient(self._client, trace)

        stage_started = perf_counter()
        try:
            rewritten_query, rewrite_source = self._rewrite(
                recent_history,
                question,
                client=observed_client,
            )
        except Exception as error:
            trace.rewrite_seconds = perf_counter() - stage_started
            trace.rewrite_source = "api" if trace.remote_llm_calls else None
            trace.error_stage, trace.error = "rewrite", str(error)
            trace.total_seconds = perf_counter() - started
            raise AgentPipelineError("rewrite", str(error), trace) from error
        trace.rewrite_seconds = perf_counter() - stage_started
        trace.rewritten_query = rewritten_query
        trace.rewrite_source = rewrite_source

        stage_started = perf_counter()
        timings = getattr(self._retriever, "timings", None)
        timing_count = len(timings) if isinstance(timings, list) else None
        try:
            ranked = tuple(self._retriever.search(
                rewritten_query,
                top_k=(self._evidence_budget.max_k if self._evidence_mode == "adaptive_prefix_v1" else
                       20 if self._evidence_mode == "coverage_selector_v2" else EVIDENCE_TOP_K),
            ))
            if not ranked:
                raise RuntimeError("retrieval returned no evidence")
            trace.available_evidence_candidates = len(ranked)
            count_tokens = getattr(self._retriever, "count_evidence_tokens", None)
            selection_started = perf_counter()
            if self._evidence_mode == "adaptive_prefix_v1":
                options = {"config": self._evidence_budget}
                if callable(count_tokens):
                    options["token_count"] = count_tokens
                decision = select_evidence_prefix(rewritten_query, ranked, **options)
                evidence = ranked[:decision.selected_k]
                trace.selected_k = decision.selected_k
                trace.evidence_expansion_reason = decision.expansion_reason
                trace.evidence_stop_reason = decision.stop_reason
                trace.evidence_token_count = decision.evidence_tokens
                trace.evidence_token_budget = decision.token_budget
                trace.evidence_original_ranks = tuple(range(1, len(evidence) + 1))
            elif self._evidence_mode == "coverage_selector_v2":
                vector_lookup = getattr(self._retriever, "evidence_vectors", None)
                if not callable(vector_lookup):
                    raise RuntimeError("coverage selector needs indexed evidence vectors")
                options = {"config": self._coverage_config,
                           "vectors": vector_lookup([item.chunk_id for item in ranked])}
                if callable(count_tokens):
                    options["token_count"] = count_tokens
                decision = select_evidence_set(rewritten_query, ranked, **options)
                evidence = tuple(ranked[index] for index in decision.selected_indices)
                trace.selected_k = decision.selected_k
                trace.evidence_stop_reason = decision.stop_reason
                trace.evidence_token_count = decision.evidence_tokens
                trace.evidence_token_budget = decision.token_budget
                trace.evidence_original_ranks = tuple(index + 1 for index in decision.selected_indices)
                trace.evidence_selection_steps = decision.selection_steps
            else:
                evidence = ranked
                trace.selected_k = len(evidence)
                trace.evidence_stop_reason = "fixed_top5"
                trace.evidence_original_ranks = tuple(range(1, len(evidence) + 1))
                if callable(count_tokens):
                    trace.evidence_token_count = sum(count_tokens(item) for item in evidence)
            trace.evidence_selection_seconds = perf_counter() - selection_started
        except Exception as error:
            trace.retrieval_seconds = perf_counter() - stage_started
            trace.error_stage, trace.error = "retrieval", str(error)
            trace.total_seconds = perf_counter() - started
            raise AgentPipelineError("retrieval", str(error), trace) from error
        trace.retrieval_seconds = perf_counter() - stage_started
        trace.evidence_chunk_ids = tuple(item.chunk_id for item in evidence)
        if timing_count is not None and len(timings) > timing_count:
            trace.rerank_seconds = timings[-1].reranker_seconds

        observed_client.stage = "generation"
        calls_before_generation = trace.remote_llm_calls
        stage_started = perf_counter()
        try:
            generated = generate_grounded_answer(
                question,
                recent_history,
                evidence,
                observed_client,
                model=self._model,
                cache=self._generation_cache,
                max_history_turns=self._max_history_turns,
            )
        except Exception as error:
            trace.generation_seconds = perf_counter() - stage_started
            trace.generation_source = (
                "api" if trace.remote_llm_calls > calls_before_generation else None
            )
            trace.error_stage, trace.error = "generation", str(error)
            trace.total_seconds = perf_counter() - started
            raise AgentPipelineError("generation", str(error), trace) from error

        generated_elapsed = perf_counter() - stage_started
        validation_inside = float(generated["validation_seconds"])
        trace.generation_seconds = max(0.0, generated_elapsed - validation_inside)
        trace.generated_answer = str(generated["answer"])
        trace.generation_source = str(generated["response_source"])
        validation_started = perf_counter()
        validation = dict(generated["validation"])
        trace.citation_validation = validation
        trace.validation_seconds = validation_inside + (perf_counter() - validation_started)
        if not validation.get("valid", False):
            warnings = validation.get("warnings", [])
            detail = ", ".join(str(value) for value in warnings) or "invalid citations"
            trace.error_stage, trace.error = "citation_validation", detail
            trace.total_seconds = perf_counter() - started
            raise AgentPipelineError("citation_validation", detail, trace)

        trace.total_seconds = perf_counter() - started
        return AgentResult(
            answer=str(generated["answer"]),
            citations=tuple(dict(source) for source in generated["sources"]),
            citation_ids=tuple(str(value) for value in generated["citation_ids"]),
            rewritten_query=rewritten_query,
            evidence=evidence,
            citation_validation=validation,
            rewrite_response_source=rewrite_source,
            generation_response_source=str(generated["response_source"]),
            trace=trace,
        )

    def _rewrite(
        self,
        history: Sequence[Mapping[str, str]],
        question: str,
        *,
        client: AgentChatClient | None = None,
    ) -> tuple[str, str]:
        key = rewrite_cache_key(
            model=self._model,
            history=history,
            latest_question=question,
            max_history_turns=self._max_history_turns,
        )
        cached = self._rewrite_cache.get(key) if self._rewrite_cache else None
        if cached is not None:
            return cached, "cache"

        rewritten = rewrite_or_keep(
            history,
            question,
            client or self._client,
            max_history_turns=self._max_history_turns,
        )
        if self._rewrite_cache:
            self._rewrite_cache.set(
                key,
                rewritten,
                {
                    "model": self._model,
                    "prompt_version": CONTEXTUALIZER_PROMPT_VERSION,
                },
            )
        return rewritten, "api"
