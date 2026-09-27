"""Pipeline output contains observations and provenance, never benchmark judgments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    query: str
    source: str = "original_query"


@dataclass(frozen=True, slots=True)
class Evidence:
    chunk_id: str
    query_id: str = "whole"
    query_ids: tuple[str, ...] = ()
    source_path: str = ""
    source_url: str = ""
    title: str = ""
    heading_path: tuple[str, ...] = ()
    text: str = ""
    retrieval_score: float | None = None
    reranker_score: float | None = None
    lexical_rank: int | None = None
    semantic_rank: int | None = None
    rank: int | None = None
    token_count: int | None = None


@dataclass(slots=True)
class PipelineResult:
    case_id: str
    pipeline_id: str
    original_query: str
    rewritten_query: str
    requirements: list[Requirement] = field(default_factory=list)
    retrieval_by_requirement: dict[str, list[Evidence]] = field(default_factory=dict)
    retrieval_candidates: list[Evidence] = field(default_factory=list)
    ranked_candidates: list[Evidence] = field(default_factory=list)
    selected_evidence: list[Evidence] = field(default_factory=list)
    serialized_context: str = ""
    evidence_tokens: int | None = None
    answer: str | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    latency_seconds: float | None = None
    timings: dict[str, float | None] = field(default_factory=dict)
    status: str = "complete"
    errors: list[dict[str, str]] = field(default_factory=list)
    component_provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineResult":
        values = dict(data)
        values["requirements"] = [Requirement(**item) for item in values.get("requirements", [])]
        def evidence(item):
            return Evidence(**{**item, "heading_path": tuple(item.get("heading_path", [])),
                               "query_ids": tuple(item.get("query_ids", []))})
        values["retrieval_by_requirement"] = {
            key: [evidence(item) for item in rows] for key, rows in values.get("retrieval_by_requirement", {}).items()
        }
        for key in ("retrieval_candidates", "ranked_candidates", "selected_evidence"):
            values[key] = [evidence(item) for item in values.get(key, [])]
        return cls(**values)
