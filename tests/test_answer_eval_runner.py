from __future__ import annotations

import unittest

from eval.run_answer_eval import (
    acceptable_source_matches,
    aggregate_deterministic_metrics,
    behavior_passes,
    detect_behavior,
    find_forbidden_claims,
    render_human_review,
)


def completed_row(case_id="case", expected="answer", **checks):
    defaults = {
        "behavior_pass": True,
        "citation_validation_pass": True,
        "acceptable_source_hit": True,
        "forbidden_claim_matches": [],
    }
    defaults.update(checks)
    return {
        "id": case_id,
        "expected_behavior": expected,
        "pipeline": {"status": "completed", "overall_pipeline_success": True},
        "deterministic_checks": defaults,
    }


class AnswerEvalRunnerTests(unittest.TestCase):
    def test_abstention_detector_requires_explicit_policy_insufficiency(self) -> None:
        self.assertEqual(
            detect_behavior("The provided published policies do not specify a deadline. [S1]"),
            "abstain",
        )
        self.assertEqual(detect_behavior("I am not sure."), "answer")

    def test_answer_behavior_detection(self) -> None:
        self.assertTrue(behavior_passes("answer", "GitHub prohibits this use. [S1]"))
        self.assertFalse(
            behavior_passes("answer", "The provided policies do not specify this. [S1]")
        )
        self.assertFalse(behavior_passes("answer", ""))

    def test_unsupported_behavior_logic(self) -> None:
        self.assertTrue(
            behavior_passes(
                "abstain", "The provided sources do not state an uptime percentage. [S1]"
            )
        )
        self.assertFalse(behavior_passes("abstain", "I am not sure about uptime."))

    def test_acceptable_source_matching_checks_optional_heading(self) -> None:
        cited = [
            {
                "source_path": "Policies/policy.md",
                "heading_path": ["Parent", "Expected Section"],
            }
        ]
        self.assertTrue(
            acceptable_source_matches(
                cited,
                [
                    {
                        "source_path": "Policies/policy.md",
                        "heading_contains": "expected section",
                    }
                ],
            )
        )
        self.assertFalse(
            acceptable_source_matches(
                cited,
                [
                    {
                        "source_path": "Policies/policy.md",
                        "heading_contains": "different section",
                    }
                ],
            )
        )

    def test_forbidden_claim_matching_normalizes_case_whitespace_and_punctuation(self) -> None:
        claims = ["GitHub guarantees a decision within six months."]
        answer = "GITHUB guarantees a decision—within   six months!"

        self.assertEqual(find_forbidden_claims(answer, claims), claims)

    def test_metric_aggregation_excludes_errors_from_answer_metrics(self) -> None:
        success = completed_row()
        error = {
            "id": "error",
            "expected_behavior": "answer",
            "pipeline": {"status": "error", "overall_pipeline_success": False},
        }

        metrics = aggregate_deterministic_metrics([success, error])

        self.assertEqual(metrics["completed_cases"], 1)
        self.assertEqual(metrics["errored_cases"], 1)
        self.assertEqual(metrics["pipeline_success_rate"], 0.5)
        self.assertEqual(metrics["behavior_accuracy"], 1.0)

    def test_human_review_template_leaves_semantic_checks_unchecked(self) -> None:
        row = {
            "id": "broad",
            "source_case_id": "ret_013",
            "category": "broad",
            "expected_behavior": "answer",
            "question": "When?",
            "history": [],
            "rewritten_query": "When can GitHub terminate an account?",
            "retrieved_evidence": [],
            "generated_answer": "Answer [S1]",
            "citation_ids": ["S1"],
            "sources": [],
            "required_points": ["One required point"],
            "supporting_snippets": ["Policy text"],
            "forbidden_claims": [],
            "pipeline": {"status": "completed"},
            "deterministic_checks": {
                "detected_behavior": "answer",
                "behavior_pass": True,
                "citation_validation_pass": True,
                "acceptable_source_hit": True,
                "forbidden_claim_matches": [],
            },
            "generator_validation": {
                "invalid_citations": [],
                "warnings": [],
                "contains_model_generated_url": False,
            },
        }
        review = render_human_review({"cases": [row]})

        self.assertIn("BROAD CASE REVIEW NOTE", review)
        self.assertIn("- [ ] covered", review)
        self.assertIn("- [ ] pass", review)
        self.assertNotIn("- [x]", review.casefold())


if __name__ == "__main__":
    unittest.main()
