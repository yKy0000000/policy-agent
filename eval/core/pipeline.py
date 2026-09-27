"""Small component interfaces and an evaluator-free pipeline dataflow."""

from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any, Protocol, Sequence

from .benchmark import BenchmarkCase
from .schemas import Evidence, PipelineResult, Requirement


class Rewriter(Protocol):
    def rewrite(self, query: str, history: Sequence[dict[str, str]]) -> str: ...


class RequirementPlanner(Protocol):
    def plan(self, rewritten_query: str) -> list[Requirement]: ...


class Retriever(Protocol):
    def retrieve(self, query: str, requirement_id: str) -> list[Evidence]: ...


class CandidateMerger(Protocol):
    def merge(self, by_requirement: dict[str, list[Evidence]]) -> list[Evidence]: ...


class Reranker(Protocol):
    def rerank(self, rewritten_query: str, requirements: list[Requirement], candidates: list[Evidence]) -> list[Evidence]: ...


class ContextBuilder(Protocol):
    def build(self, rewritten_query: str, ranked: list[Evidence]) -> "ContextSelection": ...


class Generator(Protocol):
    def generate(self, query: str, history: Sequence[dict[str, str]], selection: "ContextSelection") -> "Generation": ...


class Validator(Protocol):
    def validate(self, answer: str, selected: list[Evidence], citations: list[dict[str, Any]]) -> dict[str, Any]: ...


@dataclass(slots=True)
class ContextSelection:
    evidence: list[Evidence]
    serialized_context: str
    evidence_tokens: int | None


@dataclass(slots=True)
class Generation:
    answer: str
    citations: list[dict[str, Any]]
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None
    estimated_cost_usd: float | None = None


class WholeQueryPlanner:
    def plan(self, rewritten_query: str) -> list[Requirement]:
        return [Requirement("whole", rewritten_query)]


class UnionByChunkId:
    def merge(self, by_requirement: dict[str, list[Evidence]]) -> list[Evidence]:
        positions: dict[str, int] = {}
        merged: list[Evidence] = []
        for requirement_id, rows in by_requirement.items():
            for row in rows:
                if row.chunk_id in positions:
                    index = positions[row.chunk_id]
                    prior = merged[index]
                    merged[index] = replace(prior, query_ids=tuple(dict.fromkeys((*prior.query_ids, requirement_id))))
                else:
                    positions[row.chunk_id] = len(merged)
                    merged.append(replace(row, query_ids=(requirement_id,)))
        return merged


@dataclass(slots=True)
class Pipeline:
    pipeline_id: str
    rewriter: Rewriter
    planner: RequirementPlanner
    retriever: Retriever
    merger: CandidateMerger
    reranker: Reranker
    context_builder: ContextBuilder
    generator: Generator
    validator: Validator
    provenance: dict[str, Any]

    def run(self, case: BenchmarkCase) -> PipelineResult:
        """Components see only the query/history, never rubric or Human Truth."""
        result = PipelineResult(case.case_id, self.pipeline_id, case.query, case.query, component_provenance=dict(self.provenance))
        started = perf_counter()
        stage = "rewrite"
        try:
            t = perf_counter()
            result.rewritten_query = self.rewriter.rewrite(case.query, case.history)
            result.timings[stage] = perf_counter() - t
            stage = "planning"
            t = perf_counter()
            result.requirements = self.planner.plan(result.rewritten_query)
            if not result.requirements:
                raise ValueError("planner returned no requirements")
            result.timings[stage] = perf_counter() - t
            stage = "retrieval"
            t = perf_counter()
            by_req = {req.requirement_id: self.retriever.retrieve(req.query, req.requirement_id) for req in result.requirements}
            result.retrieval_by_requirement = by_req
            result.retrieval_candidates = self.merger.merge(by_req)
            result.timings[stage] = perf_counter() - t
            stage = "rerank"
            t = perf_counter()
            result.ranked_candidates = self.reranker.rerank(result.rewritten_query, result.requirements, result.retrieval_candidates)
            result.timings[stage] = perf_counter() - t
            stage = "context"
            t = perf_counter()
            selection = self.context_builder.build(result.rewritten_query, result.ranked_candidates)
            result.selected_evidence = selection.evidence
            result.serialized_context = selection.serialized_context
            result.evidence_tokens = selection.evidence_tokens
            result.timings[stage] = perf_counter() - t
            stage = "generation"
            t = perf_counter()
            generated = self.generator.generate(case.query, case.history, selection)
            result.answer, result.citations = generated.answer, generated.citations
            result.provider_input_tokens = generated.provider_input_tokens
            result.provider_output_tokens = generated.provider_output_tokens
            result.estimated_cost_usd = generated.estimated_cost_usd
            result.timings[stage] = perf_counter() - t
            stage = "validation"
            t = perf_counter()
            result.validation = self.validator.validate(generated.answer, selection.evidence, generated.citations)
            result.timings[stage] = perf_counter() - t
            if not result.validation.get("valid", False):
                result.status = "invalid"
        except Exception as error:
            result.status = "error"
            result.errors.append({"stage": stage, "message": str(error)})
        result.latency_seconds = perf_counter() - started
        return result
