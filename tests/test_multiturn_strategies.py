from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval.evaluate_multiturn_strategies import evaluate_strategies, generate_rewrites
from src.conversation import RewriteCache
from src.retriever import RetrievalResult


def result(chunk_id: str) -> RetrievalResult:
    return RetrievalResult(
        score=1.0,
        chunk_id=chunk_id,
        text=f"text {chunk_id}",
        source_path=f"Policies/{chunk_id}.md",
        source_url=f"https://example.test/{chunk_id}",
        title=f"Policy {chunk_id}",
        heading_path=(chunk_id,),
        chunk_index=0,
    )


class QueryAwareRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query, top_k=5):
        self.queries.append(query)
        if query == "What about it?":
            ranking = [result("other"), result("target")]
        elif query.startswith("User:"):
            ranking = [result("other"), result("second"), result("target")]
        else:
            ranking = [result("target"), result("other")]
        return ranking[:top_k]


class FixedClient:
    def __init__(self, output=None, error=None) -> None:
        self.output = output
        self.error = error

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        del messages, max_tokens, temperature
        if self.error:
            raise self.error
        return self.output


def case():
    return {
        "id": "multi_test",
        "category": "multi_turn",
        "history": [
            {"role": "user", "content": "Tell me about target policy."},
            {"role": "assistant", "content": "The topic is target policy."},
        ],
        "question": "What about it?",
        "standalone_reference": "Oracle target question",
        "expected_sources": [
            {
                "title": "Policy target",
                "heading_contains": "target",
                "source_path": "Policies/target.md",
            }
        ],
    }


class MultiTurnStrategyTests(unittest.TestCase):
    def test_strategy_runner_compares_all_four_queries(self) -> None:
        retriever = QueryAwareRetriever()
        rewrites = {
            "multi_test": {
                "status": "success",
                "rewrite": "LLM target question",
                "source": "api",
            }
        }

        report = evaluate_strategies([case()], retriever, rewrites, ranking_depth=10)

        row = report["cases"][0]["strategies"]
        self.assertEqual(row["latest_only"]["first_relevant_rank"], 2)
        self.assertEqual(row["raw_concat"]["first_relevant_rank"], 3)
        self.assertEqual(row["llm_rewrite"]["first_relevant_rank"], 1)
        self.assertEqual(row["oracle"]["first_relevant_rank"], 1)
        self.assertTrue(report["metrics"]["llm_rewrite"]["complete"])

    def test_api_failure_is_not_recorded_as_success_or_oracle_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rewrites, usage = generate_rewrites(
                [case()],
                FixedClient(error=RuntimeError("provider unavailable")),
                RewriteCache(Path(directory) / "cache.json"),
                model="test-model",
            )
            retriever = QueryAwareRetriever()
            report = evaluate_strategies(
                [case()], retriever, rewrites, ranking_depth=10
            )

        llm_row = report["cases"][0]["strategies"]["llm_rewrite"]
        self.assertEqual(rewrites["multi_test"]["status"], "error")
        self.assertEqual(usage["errors"], 1)
        self.assertEqual(llm_row["status"], "rewrite_error")
        self.assertIsNone(llm_row["hit_at_5"])
        self.assertFalse(report["metrics"]["llm_rewrite"]["complete"])
        self.assertEqual(len(retriever.queries), 3)

    def test_successful_rewrite_is_cached(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = RewriteCache(Path(directory) / "cache.json")
            first, first_usage = generate_rewrites(
                [case()], FixedClient(output="LLM target question"), cache, model="test-model"
            )
            second, second_usage = generate_rewrites(
                [case()], FixedClient(error=RuntimeError("must not call")), cache, model="test-model"
            )

        self.assertEqual(first["multi_test"]["rewrite"], second["multi_test"]["rewrite"])
        self.assertEqual(first_usage["api_calls"], 1)
        self.assertEqual(second_usage["api_calls"], 0)
        self.assertEqual(second_usage["cache_hits"], 1)


if __name__ == "__main__":
    unittest.main()
