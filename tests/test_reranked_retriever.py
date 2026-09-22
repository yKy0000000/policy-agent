from __future__ import annotations

import unittest

from eval.run_retrieval_eval import evaluate_candidates, validate_reranked_candidate_recall
from src.reranked_retriever import RerankedPolicyRetriever, candidate_union
from src.retriever import RetrievalResult


def result(chunk_id: str, *, heading: str | None = None) -> RetrievalResult:
    heading_value = heading or chunk_id
    return RetrievalResult(
        score=0.5,
        chunk_id=chunk_id,
        text=f"body {chunk_id}",
        source_path=f"Policies/{chunk_id}.md",
        source_url=f"https://example.test/{chunk_id}",
        title=f"Policy {chunk_id}",
        heading_path=(heading_value,),
        chunk_index=0,
    )


class FixedRetriever:
    def __init__(self, results):
        self.results = results
        self.requested_depths: list[int] = []

    def search(self, query, top_k=5):
        del query
        self.requested_depths.append(top_k)
        return self.results[:top_k]


class FakePairScorer:
    model_name = "fake-cross-encoder"

    def score(self, query, candidate_texts):
        del query
        return [float(text.rsplit("body ", 1)[-1] == "target") for text in candidate_texts]


class RerankedRetrieverTests(unittest.TestCase):
    def test_candidate_union_deduplicates_and_preserves_component_ranks(self) -> None:
        merged = candidate_union(
            [result("a"), result("b")],
            [result("b"), result("c")],
        )

        self.assertEqual([item.result.chunk_id for item in merged], ["a", "b", "c"])
        by_id = {item.result.chunk_id: item for item in merged}
        self.assertEqual((by_id["b"].lexical_rank, by_id["b"].semantic_rank), (2, 1))
        self.assertEqual((by_id["c"].lexical_rank, by_id["c"].semantic_rank), (None, 2))

    def test_reranking_shape_score_order_and_determinism(self) -> None:
        lexical = FixedRetriever([result("other"), result("target")])
        semantic = FixedRetriever([result("target"), result("second")])
        retriever = RerankedPolicyRetriever(lexical, semantic, FakePairScorer())

        first = retriever.search("query", top_k=3)
        second = retriever.search("query", top_k=3)

        self.assertEqual(lexical.requested_depths, [20, 20])
        self.assertEqual(semantic.requested_depths, [20, 20])
        self.assertEqual([item.chunk_id for item in first], ["target", "other", "second"])
        self.assertEqual([item.chunk_id for item in first], [item.chunk_id for item in second])
        self.assertEqual([item.reranker_score for item in first], sorted(
            [item.reranker_score for item in first], reverse=True
        ))
        self.assertEqual(
            set(first[0].to_dict()),
            {
                "reranker_score",
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

    def test_reranked_backend_can_be_evaluated(self) -> None:
        retriever = RerankedPolicyRetriever(
            FixedRetriever([result("other"), result("target", heading="TARGET")]),
            FixedRetriever([result("target", heading="TARGET")]),
            FakePairScorer(),
        )
        candidates = [
            {
                "id": "reranked-case",
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

        evaluated = evaluate_candidates(candidates, retriever, ranking_depth=10)

        self.assertTrue(evaluated[0]["hit_at_1"])
        self.assertIn("reranker_score", evaluated[0]["top_5"][0])
        self.assertIn("lexical_rank", evaluated[0]["top_5"][0])
        self.assertIn("semantic_rank", evaluated[0]["top_5"][0])

    def test_candidate_recall_is_checked_before_reranking(self) -> None:
        retriever = RerankedPolicyRetriever(
            FixedRetriever([result("target", heading="Evidence")]),
            FixedRetriever([result("other")]),
            FakePairScorer(),
        )
        candidates = [
            {
                "id": "supported",
                "category": "direct",
                "question": "query",
                "expected_sources": [
                    {
                        "title": "Policy target",
                        "heading_contains": "Evidence",
                        "source_path": "Policies/target.md",
                    }
                ],
            }
        ]

        report = validate_reranked_candidate_recall(candidates, retriever)

        self.assertEqual(report["recall"], 1.0)
        self.assertEqual(report["cases"][0]["candidate_count"], 2)


if __name__ == "__main__":
    unittest.main()
