"""Typed trace and result structures for the frozen Router V1 experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .reranked_retriever import RerankedRetrievalResult


@dataclass(frozen=True, slots=True)
class ModelCallRecord:
    stage: str
    max_tokens: int
    input_tokens: int | None
    output_tokens: int | None
    request_id: str | None
    response_id: str | None
    latency_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "max_tokens": self.max_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "request_id": self.request_id,
            "response_id": self.response_id,
            "latency_seconds": self.latency_seconds,
        }


@dataclass(frozen=True, slots=True)
class RouterTrace:
    called: bool
    provider: str
    request_model: str | None
    response_model: str | None
    prompt_sha256: str | None
    schema_sha256: str | None
    raw_response: str | None
    parsed_decision: str | None
    raw_reason_code: str | None
    effective_reason_code: str | None
    reason_validity: str | None
    schema_anomalies: tuple[str, ...]
    failure: str | None
    fallback: bool
    input_tokens: int | None
    output_tokens: int | None
    latency_seconds: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "called": self.called,
            "provider": self.provider,
            "request_model": self.request_model,
            "response_model": self.response_model,
            "prompt_sha256": self.prompt_sha256,
            "schema_sha256": self.schema_sha256,
            "raw_response": self.raw_response,
            "parsed_decision": self.parsed_decision,
            "raw_reason_code": self.raw_reason_code,
            "effective_reason_code": self.effective_reason_code,
            "reason_validity": self.reason_validity,
            "schema_anomalies": list(self.schema_anomalies),
            "failure": self.failure,
            "fallback": self.fallback,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_seconds": self.latency_seconds,
        }


@dataclass(frozen=True, slots=True)
class DecomposerTrace:
    called: bool
    available: bool
    model_version: str | None
    prompt_sha256: str | None
    schema_sha256: str | None
    raw_response: str | None
    raw_subqueries: tuple[Any, ...] | None
    validated_subqueries: tuple[str, ...]
    removed_subqueries_with_reason: tuple[dict[str, str], ...]
    failure: str | None
    fallback: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_seconds: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "called": self.called,
            "available": self.available,
            "model_version": self.model_version,
            "prompt_sha256": self.prompt_sha256,
            "schema_sha256": self.schema_sha256,
            "raw_response": self.raw_response,
            "raw_subqueries": list(self.raw_subqueries) if self.raw_subqueries is not None else None,
            "validated_subqueries": list(self.validated_subqueries),
            "removed_subqueries_with_reason": [dict(item) for item in self.removed_subqueries_with_reason],
            "failure": self.failure,
            "fallback": self.fallback,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_seconds": self.latency_seconds,
        }


@dataclass(frozen=True, slots=True)
class StreamResult:
    stream_id: str
    stream_type: str
    query_text: str
    lexical_candidate_ids: tuple[str, ...] = ()
    semantic_candidate_ids: tuple[str, ...] = ()
    union_ids: tuple[str, ...] = ()
    reranked_ids: tuple[str, ...] = ()
    stream_top5_ids: tuple[str, ...] = ()
    evidence: tuple[RerankedRetrievalResult, ...] = ()
    latency_seconds: float | None = None
    rerank_latency_seconds: float | None = None
    failure: str | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None and bool(self.evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "stream_type": self.stream_type,
            "query_text": self.query_text,
            "lexical_candidate_ids": list(self.lexical_candidate_ids),
            "semantic_candidate_ids": list(self.semantic_candidate_ids),
            "union_ids": list(self.union_ids),
            "reranked_ids": list(self.reranked_ids),
            "stream_top5_ids": list(self.stream_top5_ids),
            "evidence": [item.to_dict() for item in self.evidence],
            "latency_seconds": self.latency_seconds,
            "rerank_latency_seconds": self.rerank_latency_seconds,
            "failure": self.failure,
        }


@dataclass(frozen=True, slots=True)
class MergeSelection:
    chunk_id: str
    source_stream: str
    source_rank: int
    selection_order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_stream": self.source_stream,
            "source_rank": self.source_rank,
            "selection_order": self.selection_order,
        }


@dataclass(frozen=True, slots=True)
class MergeResult:
    selections: tuple[MergeSelection, ...]
    final_evidence: tuple[RerankedRetrievalResult, ...]
    duplicate_sources: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_evidence_ids": [item.chunk_id for item in self.final_evidence],
            "source_stream": [item.source_stream for item in self.selections],
            "source_rank": [item.source_rank for item in self.selections],
            "selection_order": [item.selection_order for item in self.selections],
            "duplicate_sources": [
                {"chunk_id": chunk_id, "streams": list(streams)}
                for chunk_id, streams in self.duplicate_sources
            ],
        }


@dataclass(frozen=True, slots=True)
class AttributionResult:
    representation_gain_ids: tuple[str, ...]
    selection_ranking_gain_ids: tuple[str, ...]
    zero_evidence_gain: bool
    applicable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation_gain_ids": list(self.representation_gain_ids),
            "selection_ranking_gain_ids": list(self.selection_ranking_gain_ids),
            "zero_evidence_gain": self.zero_evidence_gain,
            "applicable": self.applicable,
        }


@dataclass(frozen=True, slots=True)
class RouterV1Trace:
    case_id: str | None
    raw_query: str
    history_present: bool
    history_identifier: str | None
    shared_rewrite: str
    rewrite_source: str
    rewrite_model_version: str
    rewrite_prompt_version: str
    rewrite_prompt_hash: str | None
    router: RouterTrace
    decomposer: DecomposerTrace
    streams: tuple[StreamResult, ...]
    merge: MergeResult | None
    attribution: AttributionResult | None
    requested_arm: str
    executed_path: str
    router_decision: str | None
    fallback_reason: str | None
    decompose_available: bool
    counterfactual_decompose_available: bool
    execution_success: bool
    error_stage: str | None
    error: str | None
    generation_source: str | None
    model_calls: tuple[ModelCallRecord, ...] = ()
    total_latency_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": {
                "case_id": self.case_id,
                "raw_query": self.raw_query,
                "history_present": self.history_present,
                "history_identifier": self.history_identifier,
                "shared_rewrite": self.shared_rewrite,
                "rewrite_source": self.rewrite_source,
                "rewrite_model_version": self.rewrite_model_version,
                "rewrite_prompt_version": self.rewrite_prompt_version,
                "rewrite_prompt_hash": self.rewrite_prompt_hash,
            },
            "router": self.router.to_dict(),
            "decomposer": self.decomposer.to_dict(),
            "streams": [stream.to_dict() for stream in self.streams],
            "merge": self.merge.to_dict() if self.merge else None,
            "attribution": self.attribution.to_dict() if self.attribution else None,
            "outcome": {
                "requested_arm": self.requested_arm,
                "executed_path": self.executed_path,
                "router_decision": self.router_decision,
                "fallback_reason": self.fallback_reason,
                "decompose_available": self.decompose_available,
                "counterfactual_decompose_available": self.counterfactual_decompose_available,
                "execution_success": self.execution_success,
                "error_stage": self.error_stage,
                "error": self.error,
                "generation_source": self.generation_source,
            },
            "model_calls": [call.to_dict() for call in self.model_calls],
            "total_latency_seconds": self.total_latency_seconds,
        }


@dataclass(frozen=True, slots=True)
class RouterV1Result:
    case_id: str | None
    requested_arm: str
    executed_path: str
    router_decision: str | None
    fallback_reason: str | None
    decompose_available: bool
    counterfactual_decompose_available: bool
    execution_success: bool
    error_stage: str | None
    error: str | None
    raw_query: str
    rewritten_query: str
    evidence: tuple[RerankedRetrievalResult, ...]
    streams: tuple[StreamResult, ...]
    merge: MergeResult | None
    attribution: AttributionResult | None
    answer: str | None
    citations: tuple[dict[str, Any], ...]
    citation_validation: dict[str, Any] | None
    generation_source: str | None
    trace: RouterV1Trace

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "requested_arm": self.requested_arm,
            "executed_path": self.executed_path,
            "router_decision": self.router_decision,
            "fallback_reason": self.fallback_reason,
            "decompose_available": self.decompose_available,
            "counterfactual_decompose_available": self.counterfactual_decompose_available,
            "execution_success": self.execution_success,
            "error_stage": self.error_stage,
            "error": self.error,
            "raw_query": self.raw_query,
            "rewritten_query": self.rewritten_query,
            "evidence_chunk_ids": [item.chunk_id for item in self.evidence],
            "evidence": [item.to_dict() for item in self.evidence],
            "answer": self.answer,
            "citations": [dict(citation) for citation in self.citations],
            "citation_validation": self.citation_validation,
            "generation_source": self.generation_source,
            "trace": self.trace.to_dict(),
        }
