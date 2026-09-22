from __future__ import annotations

import unittest
from unittest.mock import patch

from src.agent import AgentPipelineError, AgentResult
from src.cli import main, run_chat
from src.reranked_retriever import RerankedRetrievalResult


def make_result(answer: str, *, citation_id: str = "S1") -> AgentResult:
    evidence = RerankedRetrievalResult(
        reranker_score=4.25,
        chunk_id="chunk-1",
        text="Policy evidence.",
        source_path="Policies/example.md",
        source_url="https://example.test/example",
        title="Example Policy",
        heading_path=("Example heading",),
        chunk_index=0,
        lexical_rank=1,
        semantic_rank=1,
    )
    return AgentResult(
        answer=answer,
        citations=(
            {
                "citation_id": citation_id,
                "title": "Example Policy",
                "heading_path": ["Example heading"],
                "source_path": "Policies/example.md",
                "source_url": "https://example.test/example",
                "chunk_id": "chunk-1",
            },
        ),
        citation_ids=(citation_id,),
        rewritten_query="standalone rewritten query",
        evidence=(evidence,),
        citation_validation={"valid": True, "warnings": []},
        rewrite_response_source="cache",
        generation_response_source="cache",
    )


class ScriptedInput:
    def __init__(self, values: list[str]) -> None:
        self._values = iter(values)

    def __call__(self, prompt: str) -> str:
        return next(self._values)


class FakeAgent:
    def __init__(self, outcomes) -> None:
        self._outcomes = iter(outcomes)
        self.calls = []

    def answer(self, question, history):
        self.calls.append(
            (question, [dict(message) for message in history])
        )
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class CliTests(unittest.TestCase):
    def test_main_initializes_the_agent_once_before_starting_chat(self) -> None:
        agent = object()
        with patch(
            "src.cli.PolicySupportAgent.from_project",
            return_value=agent,
        ) as factory, patch("src.cli.run_chat", return_value=0) as chat:
            exit_code = main(["--debug"])

        self.assertEqual(exit_code, 0)
        factory.assert_called_once_with(device="cpu")
        chat.assert_called_once_with(agent, debug=True)

    def test_successful_turns_accumulate_history(self) -> None:
        agent = FakeAgent(
            [
                make_result("First answer [S1]."),
                make_result("Follow-up answer [S1]."),
            ]
        )
        output = []

        exit_code = run_chat(
            agent,
            input_fn=ScriptedInput(["First question", "Follow-up", "quit"]),
            output_fn=output.append,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(agent.calls[0], ("First question", []))
        self.assertEqual(
            agent.calls[1],
            (
                "Follow-up",
                [
                    {"role": "user", "content": "First question"},
                    {"role": "assistant", "content": "First answer [S1]."},
                ],
            ),
        )
        rendered = "\n".join(output)
        self.assertIn("[S1] Example Policy", rendered)
        self.assertIn("https://example.test/example", rendered)
        self.assertNotIn("standalone rewritten query", rendered)

    def test_technical_failure_does_not_enter_history(self) -> None:
        agent = FakeAgent(
            [
                AgentPipelineError("retrieval", "reranker unavailable"),
                make_result("Recovered answer [S1]."),
            ]
        )
        output = []

        run_chat(
            agent,
            input_fn=ScriptedInput(["Failed question", "Next question", "exit"]),
            output_fn=output.append,
        )

        self.assertEqual(agent.calls[1], ("Next question", []))
        self.assertIn("Error [retrieval]", "\n".join(output))

    def test_supported_abstention_is_recorded_as_a_successful_turn(self) -> None:
        abstention = "The provided published policies do not specify that detail [S1]."
        agent = FakeAgent(
            [
                make_result(abstention),
                make_result("Second answer [S1]."),
            ]
        )
        output = []

        run_chat(
            agent,
            input_fn=ScriptedInput(
                ["Unsupported question", "Related follow-up", "quit"]
            ),
            output_fn=output.append,
        )

        self.assertEqual(
            agent.calls[1][1],
            [
                {"role": "user", "content": "Unsupported question"},
                {"role": "assistant", "content": abstention},
            ],
        )
        self.assertIn(abstention, "\n".join(output))

    def test_debug_output_is_opt_in(self) -> None:
        result = make_result("Answer [S1].")
        normal_output = []
        debug_output = []

        run_chat(
            FakeAgent([result]),
            input_fn=ScriptedInput(["question", "quit"]),
            output_fn=normal_output.append,
        )
        run_chat(
            FakeAgent([result]),
            debug=True,
            input_fn=ScriptedInput(["question", "quit"]),
            output_fn=debug_output.append,
        )

        self.assertNotIn("Rewritten query", "\n".join(normal_output))
        rendered_debug = "\n".join(debug_output)
        self.assertIn("Rewritten query: standalone rewritten query", rendered_debug)
        self.assertIn("score=4.2500", rendered_debug)
        self.assertIn("Rewrite source: cache", rendered_debug)


if __name__ == "__main__":
    unittest.main()
