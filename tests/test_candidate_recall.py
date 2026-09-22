"""Focused tests for candidate-union recall analysis."""

import unittest

from eval.analyze_candidate_recall import (
    candidate_hit,
    candidate_source_coverage,
    candidate_union,
    first_candidate_depth,
)
from src.retriever import RetrievalResult


def result(chunk_id: str, path: str, heading: str) -> RetrievalResult:
    return RetrievalResult(
        score=1.0,
        chunk_id=chunk_id,
        text="text",
        source_path=path,
        source_url=f"https://example.test/{path}",
        title="Policy",
        heading_path=(heading,),
        chunk_index=0,
    )


class CandidateRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = result("a", "Policies/a.md", "First")
        self.b = result("b", "Policies/b.md", "Target")
        self.c = result("c", "Policies/c.md", "Other")
        self.d = result("d", "Policies/d.md", "Second")

    def test_candidate_union_deduplicates_and_is_deterministic_across_depths(self) -> None:
        lexical = [self.a, self.b, self.c]
        semantic = [self.b, self.d, self.a]

        depth_one = candidate_union(lexical, semantic, 1)
        depth_three_first = candidate_union(lexical, semantic, 3)
        depth_three_second = candidate_union(lexical, semantic, 3)

        self.assertEqual([item.chunk_id for item in depth_one], ["a", "b"])
        self.assertEqual(
            [item.chunk_id for item in depth_three_first],
            [item.chunk_id for item in depth_three_second],
        )
        self.assertEqual(len({item.chunk_id for item in depth_three_first}), 4)

    def test_candidate_hit_and_multi_source_coverage(self) -> None:
        union = [self.a, self.b]
        expected = [
            {"source_path": "Policies/b.md", "heading_contains": "Target"},
            {"source_path": "Policies/d.md", "heading_contains": "Second"},
        ]

        self.assertTrue(candidate_hit(union, expected))
        self.assertEqual(candidate_source_coverage(union, expected), 0.5)

    def test_first_hit_depth_uses_best_component_rank(self) -> None:
        lexical = [self.a, self.c, self.b]
        semantic = [self.c, self.b, self.a]
        expected = [{"source_path": "Policies/b.md", "heading_contains": "Target"}]

        self.assertEqual(first_candidate_depth(lexical, semantic, expected), (3, 2, 2))


if __name__ == "__main__":
    unittest.main()

