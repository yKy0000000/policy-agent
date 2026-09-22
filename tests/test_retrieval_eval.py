"""Focused tests for retrieval evaluation matching and metrics."""

import unittest

from eval.run_retrieval_eval import (
    aggregate_metrics,
    first_relevant_rank,
    source_coverage_at_k,
    source_matches,
)
from src.retriever import RetrievalResult


def result(path: str, *headings: str) -> RetrievalResult:
    return RetrievalResult(
        score=0.5,
        chunk_id=f"chunk-{path}-{'-'.join(headings)}",
        text="text",
        source_path=path,
        source_url=f"https://example.test/{path}",
        title="Policy",
        heading_path=headings,
        chunk_index=0,
    )


class RetrievalEvalTests(unittest.TestCase):
    def test_source_matching_uses_path_and_optional_heading(self) -> None:
        retrieved = result("Policies/policy.md", "Parent", "Appeals")
        self.assertTrue(
            source_matches(
                retrieved,
                {"source_path": "Policies/policy.md", "heading_contains": "appeals"},
            )
        )
        self.assertTrue(
            source_matches(
                retrieved,
                {"source_path": "Policies/policy.md", "heading_contains": ""},
            )
        )
        self.assertFalse(
            source_matches(
                retrieved,
                {"source_path": "Policies/other.md", "heading_contains": "Appeals"},
            )
        )

    def test_first_rank_and_aggregate_metrics(self) -> None:
        rankings = [result("Policies/a.md"), result("Policies/b.md", "Target")]
        expected = [{"source_path": "Policies/b.md", "heading_contains": "Target"}]
        self.assertEqual(first_relevant_rank(rankings, expected), 2)

        metrics = aggregate_metrics(
            [
                {"hit_at_1": False, "hit_at_3": True, "hit_at_5": True, "reciprocal_rank": 0.5},
                {"hit_at_1": True, "hit_at_3": True, "hit_at_5": True, "reciprocal_rank": 1.0},
            ]
        )
        self.assertEqual(metrics["case_count"], 2)
        self.assertEqual(metrics["hit_at_1"], 0.5)
        self.assertEqual(metrics["hit_at_3"], 1.0)
        self.assertEqual(metrics["mrr"], 0.75)

    def test_multi_source_coverage_counts_each_expected_rule(self) -> None:
        rankings = [
            result("Policies/shared.md", "First"),
            result("Policies/noise.md"),
            result("Policies/shared.md", "Second"),
        ]
        expected = [
            {"source_path": "Policies/shared.md", "heading_contains": "First"},
            {"source_path": "Policies/shared.md", "heading_contains": "Second"},
        ]
        self.assertEqual(source_coverage_at_k(rankings, expected, 1), 0.5)
        self.assertEqual(source_coverage_at_k(rankings, expected, 3), 1.0)


if __name__ == "__main__":
    unittest.main()

