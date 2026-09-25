from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.agent import AgentPipelineError, AgentResult, ExecutionTrace
from src.reranked_retriever import RerankedRetrievalResult
from eval.run_answer_eval import (
    acceptable_source_matches,
    aggregate_deterministic_metrics,
    behavior_passes,
    detect_behavior,
    find_forbidden_claims,
    render_human_review,
    run_answer_eval,
)


def completed_row(case_id="case", expected="answer", **checks):
    defaults = {
        "behavior_check": True,
        "citation_validation": True,
        "source_check": True,
        "forbidden_claim_matches": [],
    }
    defaults.update(checks)
    return {
        "id": case_id,
        "expected_behavior": expected,
        "pipeline": {"status": "completed", "execution_success": True},
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
            "pipeline": {"status": "error", "execution_success": False},
        }

        metrics = aggregate_deterministic_metrics([success, error])

        self.assertEqual(metrics["completed_cases"], 1)
        self.assertEqual(metrics["errored_cases"], 1)
        self.assertEqual(metrics["execution_success_rate"], 0.5)
        self.assertEqual(metrics["behavior_check_rate"], 1.0)

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
                "behavior_check": True,
                "citation_validation": True,
                "source_check": True,
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

    def test_answer_eval_calls_the_production_answer_entry_point(self) -> None:
        source = RerankedRetrievalResult(
            reranker_score=1.0, chunk_id="chunk-1", text="Policy text",
            source_path="Policies/policy.md", source_url="https://example.test/policy",
            title="Policy", heading_path=(), chunk_index=0,
            lexical_rank=1, semantic_rank=1,
        )
        trace = ExecutionTrace(
            original_query="Question?", rewritten_query="Question?",
            evidence_chunk_ids=("chunk-1",), generated_answer="Answer [S1]",
            citation_validation={"valid": True, "warnings": []},
            rewrite_source="cache", generation_source="cache",
            rewrite_seconds=0.0, retrieval_seconds=0.0, rerank_seconds=0.0,
            generation_seconds=0.0, validation_seconds=0.0, total_seconds=0.0,
        )
        result = AgentResult(
            answer="Answer [S1]", citations=({
                "citation_id": "S1", "source_path": "Policies/policy.md",
                "source_url": "https://example.test/policy", "heading_path": [],
            },), citation_ids=("S1",), rewritten_query="Question?",
            evidence=(source,), citation_validation={"valid": True, "warnings": []},
            rewrite_response_source="cache", generation_response_source="cache",
            trace=trace,
        )
        agent = Mock()
        agent.answer.return_value = result
        case = {
            "id": "case", "source_case_id": "ret_001", "category": "direct",
            "expected_behavior": "answer", "question": "Question?", "history": [],
            "required_points": [], "acceptable_sources": [{"source_path": "Policies/policy.md"}],
            "forbidden_claims": [], "supporting_snippets": [], "notes": "",
        }

        rows, usage = run_answer_eval([case], agent)

        agent.answer.assert_called_once_with("Question?", [])
        self.assertEqual(rows[0]["generated_answer"], result.answer)
        self.assertEqual(rows[0]["retrieved_evidence"][0]["chunk_id"], "chunk-1")
        self.assertEqual(rows[0]["execution_trace"]["original_query"], "Question?")
        self.assertEqual(usage["remote_llm_calls"], 0)

    def test_eval_preserves_production_stage_error_trace(self) -> None:
        trace = ExecutionTrace(
            original_query="Question?", rewrite_source="api",
            rewrite_seconds=0.2, total_seconds=0.2,
            remote_llm_calls=1, error_stage="rewrite", error="unavailable",
        )
        agent = Mock()
        agent.answer.side_effect = AgentPipelineError("rewrite", "unavailable", trace)
        case = {
            "id": "case", "source_case_id": "ret_001", "category": "direct",
            "expected_behavior": "answer", "question": "Question?", "history": [],
            "required_points": [], "acceptable_sources": [],
            "forbidden_claims": [], "supporting_snippets": [], "notes": "",
        }

        rows, usage = run_answer_eval([case], agent)

        self.assertEqual(rows[0]["pipeline"]["error_stage"], "rewrite")
        self.assertFalse(rows[0]["pipeline"]["execution_success"])
        self.assertEqual(rows[0]["execution_trace"]["remote_llm_calls"], 1)
        self.assertEqual(usage["remote_llm_calls"], 1)
        self.assertEqual(usage["errors"], 1)


if __name__ == "__main__":
    unittest.main()
