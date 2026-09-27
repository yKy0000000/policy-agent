from __future__ import annotations

import unittest
from dataclasses import replace

from eval.results.multiarm_70.run_multiarm_70 import adaptive_evidence
from eval.run_stage0_replay import NO_ROUTER_DEFAULTS, no_router_adaptive_rows
from src.agent import PolicySupportAgent
from src.no_router_adaptive import NO_ROUTER_DEFAULTS as RUNTIME_DEFAULTS
from src.no_router_adaptive import no_router_adaptive_rows as runtime_rows
from src.response_modes import AdaptiveEvidenceRetriever, AdaptiveModeAdapter
from tests.test_agent import evidence


class FakeRetriever:
    def __init__(self, *, fail_count_once: bool = False) -> None:
        self.items = [replace(evidence(i), reranker_score=10 - i * 0.2) for i in range(1, 9)]
        self.calls = []
        self.fail_count_once = fail_count_once

    def search(self, query, top_k=5):
        self.calls.append((query, top_k))
        return self.items[:top_k]

    def count_evidence_tokens(self, item):
        if self.fail_count_once:
            self.fail_count_once = False
            raise RuntimeError("synthetic token counter failure")
        return 1000


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append(max_tokens)
        if max_tokens == 512:
            return "Synthetic answer [S1]."
        if max_tokens == 96:
            return "rewritten follow-up"
        raise AssertionError("Router or Decomposer must not be called")


class ResponseModeTests(unittest.TestCase):
    def test_runtime_rule_matches_frozen_rule_at_all_stop_boundaries(self) -> None:
        self.assertEqual(RUNTIME_DEFAULTS, NO_ROUTER_DEFAULTS)
        for count, tokens, score_step in (
            (0, 1000, 0.2),
            (3, 1000, 0.2),
            (8, 1000, 0.2),
            (8, 1500, 0.2),
            (8, 1000, 0.6),
            (25, 100, 0.1),
            (8, 2000, 0.2),
        ):
            with self.subTest(count=count, tokens=tokens, score_step=score_step):
                rows = [
                    {"chunk_id": f"chunk_{i}", "bge_score": 10 - i * score_step, "tokens": tokens}
                    for i in range(count)
                ]
                self.assertEqual(runtime_rows(rows, **RUNTIME_DEFAULTS), no_router_adaptive_rows(rows, **NO_ROUTER_DEFAULTS))

    def test_selector_is_identical_to_frozen_a1_and_70_query_runner(self) -> None:
        retriever = FakeRetriever()
        selected = AdaptiveEvidenceRetriever(retriever).search("policy question")
        rows = [
            {"chunk_id": item.chunk_id, "bge_score": item.reranker_score, "tokens": 1000}
            for item in retriever.items
        ]
        frozen = no_router_adaptive_rows(rows, **NO_ROUTER_DEFAULTS)
        runner_selected, _ = adaptive_evidence(retriever.items, retriever)
        self.assertEqual([item.chunk_id for item in selected], [row["chunk_id"] for row in frozen])
        self.assertEqual(selected, runner_selected)
        self.assertEqual(len(selected), 6)
        self.assertEqual(retriever.calls, [("policy question", 20)])

    def test_search_plus_runs_adaptive_with_existing_agent_generation_and_history(self) -> None:
        retriever, client = FakeRetriever(), FakeClient()
        agent = PolicySupportAgent(retriever, client, model="synthetic-model")
        adapter = AdaptiveModeAdapter(agent)
        history = [
            {"role": "user", "content": "Earlier question"},
            {"role": "assistant", "content": "Earlier answer"},
        ]

        response = adapter.answer("Follow-up", history)

        self.assertEqual(response.executed_path, "ADAPTIVE")
        self.assertIsNone(response.fallback_reason)
        self.assertEqual(len(response.result.evidence), 6)
        self.assertEqual(response.result.rewritten_query, "rewritten follow-up")
        self.assertEqual(response.result.trace.evidence_mode, "no_router_adaptive_v1")
        self.assertEqual(response.result.trace.evidence_token_budget, 6000)
        self.assertEqual(retriever.calls, [("rewritten follow-up", 20)])
        self.assertEqual(client.calls, [96, 512])

    def test_adaptive_retrieval_failure_falls_back_to_direct(self) -> None:
        retriever, client = FakeRetriever(fail_count_once=True), FakeClient()
        agent = PolicySupportAgent(retriever, client, model="synthetic-model")

        response = AdaptiveModeAdapter(agent).answer("Standalone question")

        self.assertEqual(response.executed_path, "DIRECT")
        self.assertIsNotNone(response.fallback_reason)
        self.assertEqual(len(response.result.evidence), 5)
        self.assertEqual(retriever.calls, [("rewritten follow-up", 20), ("rewritten follow-up", 5)])
        self.assertEqual(client.calls, [96, 96, 512])


if __name__ == "__main__":
    unittest.main()
