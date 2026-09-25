from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.evidence_budget import EvidenceBudgetConfig, select_evidence_prefix


def _ranked(*, text: str = "unrelated policy text", score_step: float = 0.1, tokens: int = 30):
    return [
        SimpleNamespace(
            title="Policy", heading_path=("Section",), text=text,
            source_path=f"Policies/policy-{rank}.md", reranker_score=3 - rank * score_step,
            token_count=tokens,
        )
        for rank in range(1, 21)
    ]


class EvidenceBudgetTests(unittest.TestCase):
    def test_simple_question_stays_at_five(self):
        result = select_evidence_prefix("When can GitHub suspend an account?", _ranked())
        self.assertEqual(result.selected_k, 5)
        self.assertEqual(result.stop_reason, "query_not_broad")
        self.assertIsNone(result.expansion_reason)

    def test_saturated_broad_question_stays_at_five(self):
        result = select_evidence_prefix(
            "Can users recover their account and billing data?",
            _ranked(text="Users recover their account and billing data."),
        )
        self.assertEqual(result.selected_k, 5)
        self.assertEqual(result.stop_reason, "top5_query_terms_saturated")

    def test_unsatisfied_broad_question_expands_with_a_hard_cap(self):
        result = select_evidence_prefix(
            "What protection applies and who handles appeals?", _ranked(),
        )
        self.assertEqual(result.selected_k, 20)
        self.assertEqual(result.stop_reason, "max_k")
        self.assertEqual(result.expansion_reason, "broad_query_low_top5_coverage")

    def test_token_budget_prevents_next_chunk_without_dropping_top_five(self):
        result = select_evidence_prefix(
            "What protection applies and who handles appeals?", _ranked(tokens=100),
            config=EvidenceBudgetConfig(max_evidence_tokens=650),
        )
        self.assertEqual(result.selected_k, 6)
        self.assertEqual(result.evidence_tokens, 600)
        self.assertEqual(result.stop_reason, "token_budget")

    def test_candidate_exhaustion_and_invalid_config(self):
        result = select_evidence_prefix("What happens if an appeal fails?", _ranked()[:7])
        self.assertEqual(result.selected_k, 7)
        self.assertEqual(result.stop_reason, "candidate_exhausted")
        with self.assertRaises(ValueError):
            EvidenceBudgetConfig(initial_k=9, first_expansion_k=8)


if __name__ == "__main__":
    unittest.main()
