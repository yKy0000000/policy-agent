"""Focused tests for rank-based hybrid retrieval."""

import unittest

from eval.run_retrieval_eval import evaluate_candidates
from src.hybrid_retriever import (
    HybridConfig,
    HybridPolicyRetriever,
    fuse_rankings,
    reciprocal_rank_fusion_score,
)
from src.retriever import RetrievalResult


def result(chunk_id: str, score: float = 1.0) -> RetrievalResult:
    return RetrievalResult(
        score=score,
        chunk_id=chunk_id,
        text=f"text for {chunk_id}",
        source_path=f"Policies/{chunk_id}.md",
        source_url=f"https://example.test/{chunk_id}",
        title=f"Policy {chunk_id}",
        heading_path=(chunk_id.upper(),),
        chunk_index=0,
    )


class FixedRetriever:
    def __init__(self, results):
        self.results = list(results)
        self.requested_depths = []

    def search(self, query, top_k=5):
        del query
        self.requested_depths.append(top_k)
        return self.results[:top_k]


class HybridRetrieverTests(unittest.TestCase):
    def test_rrf_score_uses_available_ranks(self) -> None:
        self.assertAlmostEqual(
            reciprocal_rank_fusion_score((1, 2), rrf_k=60),
            1 / 61 + 1 / 62,
        )
        self.assertAlmostEqual(
            reciprocal_rank_fusion_score((3, None), rrf_k=60),
            1 / 63,
        )

    def test_merge_deduplicates_by_chunk_and_is_deterministic(self) -> None:
        lexical = [result("a"), result("b"), result("c")]
        semantic = [result("c"), result("a"), result("d")]

        first = fuse_rankings(lexical, semantic, top_k=4, rrf_k=60)
        second = fuse_rankings(lexical, semantic, top_k=4, rrf_k=60)

        self.assertEqual([item.chunk_id for item in first], [item.chunk_id for item in second])
        self.assertEqual(len({item.chunk_id for item in first}), 4)
        by_id = {item.chunk_id: item for item in first}
        self.assertEqual((by_id["a"].lexical_rank, by_id["a"].semantic_rank), (1, 2))
        self.assertEqual((by_id["d"].lexical_rank, by_id["d"].semantic_rank), (None, 3))

    def test_hybrid_search_uses_configured_depth_and_unified_shape(self) -> None:
        lexical = FixedRetriever([result("a"), result("b")])
        semantic = FixedRetriever([result("b"), result("c")])
        hybrid = HybridPolicyRetriever(
            lexical,
            semantic,
            HybridConfig(rrf_k=60, candidate_depth=20),
        )

        retrieved = hybrid.search("query", top_k=3)

        self.assertEqual(lexical.requested_depths, [20])
        self.assertEqual(semantic.requested_depths, [20])
        self.assertEqual(retrieved[0].chunk_id, "b")
        self.assertEqual(
            set(retrieved[0].to_dict()),
            {
                "score",
                "chunk_id",
                "text",
                "source_path",
                "source_url",
                "title",
                "heading_path",
                "chunk_index",
                "lexical_rank",
                "semantic_rank",
            },
        )

    def test_eval_runner_accepts_hybrid_backend(self) -> None:
        hybrid = HybridPolicyRetriever(
            FixedRetriever([result("target"), result("other")]),
            FixedRetriever([result("other"), result("target")]),
            HybridConfig(candidate_depth=2),
        )
        candidates = [
            {
                "id": "hybrid-case",
                "category": "semantic",
                "question": "query",
                "expected_sources": [
                    {
                        "title": "Policy target",
                        "heading_contains": "TARGET",
                        "source_path": "Policies/target.md",
                    }
                ],
            }
        ]

        evaluated = evaluate_candidates(candidates, hybrid, ranking_depth=10)

        self.assertTrue(evaluated[0]["hit_at_3"])
        self.assertIn("lexical_rank", evaluated[0]["top_5"][0])
        self.assertIn("semantic_rank", evaluated[0]["top_5"][0])


if __name__ == "__main__":
    unittest.main()

