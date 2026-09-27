"""Session-only high-budget mode using the frozen no-router Adaptive rule."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .agent import AgentPipelineError, AgentResult, PolicySupportAgent
from .no_router_adaptive import NO_ROUTER_DEFAULTS, no_router_adaptive_rows
from .reranked_retriever import RerankedRetrievalResult


class AdaptiveEvidenceRetriever:
    """Select the A1/70-query score-gap prefix from the current reranked Top20."""

    def __init__(self, retriever: Any) -> None:
        self._retriever = retriever
        self.timings = getattr(retriever, "timings", None)
        self.available_candidates = 0
        self.selected_tokens = 0
        self.stop_reason = ""

    def count_evidence_tokens(self, item: RerankedRetrievalResult) -> int:
        return self._retriever.count_evidence_tokens(item)

    def search(self, query: str, top_k: int = 5) -> tuple[RerankedRetrievalResult, ...]:
        # Agent.answer owns rewrite, generation and validation. This adapter owns
        # only the frozen no-router evidence rule; top_k=5 is Agent's Direct call.
        ranked = tuple(self._retriever.search(query, top_k=NO_ROUTER_DEFAULTS["max_k"]))
        self.available_candidates = len(ranked)
        rows = [
            {
                "chunk_id": item.chunk_id,
                "bge_score": item.reranker_score,
                "tokens": self.count_evidence_tokens(item),
            }
            for item in ranked
        ]
        selected = no_router_adaptive_rows(rows, **NO_ROUTER_DEFAULTS)
        self.selected_tokens = sum(row["tokens"] for row in selected)
        if len(selected) == len(ranked):
            self.stop_reason = "candidate_exhausted_or_max_k"
        elif rows[0]["bge_score"] - rows[len(selected)]["bge_score"] > NO_ROUTER_DEFAULTS["max_score_drop"]:
            self.stop_reason = "score_drop"
        else:
            self.stop_reason = "token_cap"
        return ranked[: len(selected)]


@dataclass(frozen=True, slots=True)
class SearchPlusResult:
    result: AgentResult
    executed_path: str
    fallback_reason: str | None = None


class AdaptiveModeAdapter:
    """Reuse the loaded Direct agent while changing only evidence selection."""

    def __init__(self, agent: PolicySupportAgent) -> None:
        self._direct_agent = agent
        self._retriever = AdaptiveEvidenceRetriever(agent._retriever)
        self._adaptive_agent = PolicySupportAgent(
            self._retriever,
            agent._client,
            model=agent._model,
            rewrite_cache=agent._rewrite_cache,
            generation_cache=agent._generation_cache,
            max_history_turns=agent._max_history_turns,
        )

    def answer(
        self,
        question: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> SearchPlusResult:
        try:
            result = self._adaptive_agent.answer(question, history)
        except AgentPipelineError as error:
            if error.stage != "retrieval":
                raise
            direct = self._direct_agent.answer(question, history)
            return SearchPlusResult(direct, "DIRECT", str(error))

        if result.trace is not None:
            result.trace.evidence_mode = "no_router_adaptive_v1"
            result.trace.available_evidence_candidates = self._retriever.available_candidates
            result.trace.evidence_token_count = self._retriever.selected_tokens
            result.trace.evidence_token_budget = NO_ROUTER_DEFAULTS["max_evidence_tokens"]
            result.trace.evidence_expansion_reason = (
                "score_gap_prefix" if len(result.evidence) > NO_ROUTER_DEFAULTS["initial_k"] else None
            )
            result.trace.evidence_stop_reason = self._retriever.stop_reason
        return SearchPlusResult(result, "ADAPTIVE")
