from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from src.evidence_selector import CoverageSelectorConfig, select_evidence_set


def item(rank, title):
    return SimpleNamespace(chunk_id=f"c{rank}", reranker_score=float(8-rank),
                           text=title, title=title, heading_path=(), token_count=10)


class SelectorTests(unittest.TestCase):
    def test_skips_redundant_rank_two_for_complementary_rank_three(self):
        ranked = [item(1, "alpha"), item(2, "alpha"), item(3, "beta")]
        vectors = {"c1": np.array([1., 0.]), "c2": np.array([1., 0.]), "c3": np.array([0., 1.])}
        config = CoverageSelectorConfig(min_k=1, max_k=2)
        result = select_evidence_set("alpha beta", ranked, vectors=vectors, config=config)
        self.assertEqual(result.selected_indices, (0, 2))
        self.assertEqual(result.evidence_tokens, 20)
        self.assertEqual(result.selection_steps[1]["chosen"]["rank"], 3)
        self.assertGreater(result.selection_steps[1]["chosen"]["utility"],
                           result.selection_steps[1]["candidates"][0]["utility"])

    def test_budget_and_missing_vector_fail_visibly(self):
        ranked = [item(1, "alpha"), item(2, "beta")]
        vectors = {"c1": np.array([1., 0.]), "c2": np.array([0., 1.])}
        config = CoverageSelectorConfig(min_k=1, max_k=2, max_evidence_tokens=10)
        decision = select_evidence_set("alpha", ranked, vectors=vectors, config=config)
        self.assertEqual(decision.stop_reason, "token_budget")
        with self.assertRaisesRegex(ValueError, "vectors missing"):
            select_evidence_set("alpha", ranked, vectors={"c1": vectors["c1"]})
        with self.assertRaisesRegex(ValueError, "cannot fit required min_k"):
            select_evidence_set("alpha", ranked, vectors=vectors,
                                config=CoverageSelectorConfig(min_k=2, max_k=2, max_evidence_tokens=10))

    def test_local_score_normalization_ignores_affine_shift(self):
        ranked = [item(1, "alpha"), item(2, "beta"), item(3, "gamma")]
        vectors = {f"c{i}": np.eye(3)[i-1] for i in range(1, 4)}
        cfg = CoverageSelectorConfig(min_k=2, max_k=2)
        baseline = select_evidence_set("alpha beta", ranked, vectors=vectors, config=cfg)
        shifted = [SimpleNamespace(**{**vars(row), "reranker_score": row.reranker_score * 3 + 11}) for row in ranked]
        self.assertEqual(baseline.selected_indices, select_evidence_set("alpha beta", shifted, vectors=vectors, config=cfg).selected_indices)


if __name__ == "__main__":
    unittest.main()
