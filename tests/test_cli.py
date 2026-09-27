from __future__ import annotations

import unittest
from unittest.mock import patch

from src.agent import AgentPipelineError, AgentResult
from src.cli import ASSISTANT_LABEL, SEPARATOR, main, run_chat
from src.reranked_retriever import RerankedRetrievalResult
from src.response_modes import SearchPlusResult


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
        self.prompts = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self._values)


class FakeAgent:
    def __init__(self, outcomes) -> None:
        self._outcomes = iter(outcomes)
        self.calls = []
        self.adaptive_calls = []

    def answer(self, question, history):
        self.calls.append(
            (question, [dict(message) for message in history])
        )
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeSearchAdapter:
    def __init__(self, agent: FakeAgent) -> None:
        self.agent = agent

    def answer(self, question, history):
        self.agent.adaptive_calls.append((question, [dict(message) for message in history]))
        outcome = next(self.agent._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_adaptive_result(*, fallback: str | None = None) -> SearchPlusResult:
    return SearchPlusResult(
        make_result("Search answer [S1]."),
        "DIRECT" if fallback else "ADAPTIVE",
        fallback,
    )


class CliTests(unittest.TestCase):
    def test_startup_choices_and_invalid_retry(self) -> None:
        for choices, expected_prompt, expected_calls in (
            ([""], "[FAST] > ", (0, 0)),
            (["f"], "[FAST] > ", (0, 0)),
            (["F"], "[FAST] > ", (0, 0)),
            (["s"], "[SEARCH+] > ", (0, 0)),
            (["S"], "[SEARCH+] > ", (0, 0)),
            (["invalid", "s"], "[SEARCH+] > ", (0, 0)),
        ):
            with self.subTest(choices=choices):
                scripted = ScriptedInput([*choices, "/exit"])
                output = []
                agent = FakeAgent([])
                self.assertEqual(run_chat(agent, input_fn=scripted, output_fn=output.append), 0)
                self.assertEqual(scripted.prompts[-1], expected_prompt)
                self.assertEqual((len(agent.calls), len(agent.adaptive_calls)), expected_calls)
                self.assertEqual(
                    sum("Choose f or s" in line for line in output),
                    1 if choices[0] == "invalid" else 0,
                )

    def test_switching_modes_preserves_history_and_selects_paths(self) -> None:
        agent = FakeAgent(
            [make_result("Fast first [S1]."), make_adaptive_result(), make_result("Fast again [S1].")]
        )
        scripted = ScriptedInput(
            ["", "First question", "/s", "/mode", "Follow-up", "/f", "Third question", "/help", "/exit"]
        )
        output = []

        run_chat(agent, search_adapter=FakeSearchAdapter(agent), input_fn=scripted, output_fn=output.append)

        self.assertEqual(agent.calls[0], ("First question", []))
        self.assertEqual(agent.adaptive_calls[0][0], "Follow-up")
        self.assertEqual(agent.adaptive_calls[0][1][-1]["content"], "Fast first [S1].")
        self.assertEqual(agent.calls[1][0], "Third question")
        self.assertEqual(agent.calls[1][1][-1]["content"], "Search answer [S1].")
        self.assertEqual(scripted.prompts.count("[SEARCH+] > "), 3)
        self.assertIn("Mode switched to SEARCH+.", output)
        self.assertIn("Mode switched to FAST.", output)
        self.assertIn("Current mode: SEARCH+", output)
        self.assertTrue(any("/help" in line for line in output))

    def test_search_plus_fallback_and_failed_turn(self) -> None:
        agent = FakeAgent([AgentPipelineError("generation", "synthetic failure"), make_adaptive_result(fallback="adaptive selection failed"), make_result("Final [S1].")])
        output = []
        run_chat(
            agent,
            search_adapter=FakeSearchAdapter(agent),
            input_fn=ScriptedInput(["s", "Failed", "Fallback", "/f", "Next", "exit"]),
            output_fn=output.append,
        )
        self.assertEqual(agent.adaptive_calls[1][1], [])
        self.assertEqual(agent.calls[0][1][-1]["content"], "Search answer [S1].")
        self.assertIn("Higher-budget retrieval unavailable; used Fast retrieval for this turn.", output)
        self.assertTrue(any("Error [generation]" in line for line in output))
        self.assertNotIn("synthetic failure", "\n".join(output))

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
            input_fn=ScriptedInput(["", "First question", "Follow-up", "quit"]),
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
            input_fn=ScriptedInput(["", "Failed question", "Next question", "exit"]),
            output_fn=output.append,
        )

        self.assertEqual(agent.calls[1], ("Next question", []))
        self.assertIn("Error [retrieval]", "\n".join(output))

    def test_assistant_answer_is_bounded_and_excluded_from_history(self) -> None:
        answer = "GitHub may reinstate content after a valid counter notice [S1]."
        agent = FakeAgent([make_result(answer), make_result("Second answer [S1].")])
        output = []

        run_chat(
            agent,
            input_fn=ScriptedInput(["", "First question", "Follow-up", "quit"]),
            output_fn=output.append,
        )

        label_index = output.index(ASSISTANT_LABEL)
        opening_separator = output.index(SEPARATOR, label_index)
        answer_index = output.index(answer, opening_separator)
        closing_separator = output.index(SEPARATOR, answer_index)
        self.assertLess(label_index, opening_separator)
        self.assertLess(opening_separator, answer_index)
        self.assertLess(answer_index, closing_separator)

        history = agent.calls[1][1]
        self.assertEqual(history[0]["content"], "First question")
        self.assertEqual(history[1]["content"], answer)
        for message in history:
            self.assertNotIn(ASSISTANT_LABEL, message["content"])
            self.assertNotIn(SEPARATOR, message["content"])

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
                ["", "Unsupported question", "Related follow-up", "quit"]
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
            input_fn=ScriptedInput(["", "question", "quit"]),
            output_fn=normal_output.append,
        )
        run_chat(
            FakeAgent([result]),
            debug=True,
            input_fn=ScriptedInput(["", "question", "quit"]),
            output_fn=debug_output.append,
        )

        self.assertNotIn("Rewritten query", "\n".join(normal_output))
        self.assertNotIn("Debug:", normal_output)
        self.assertIn(ASSISTANT_LABEL, normal_output)
        self.assertIn(SEPARATOR, normal_output)

        rendered_debug = "\n".join(debug_output)
        self.assertIn("Rewritten query: standalone rewritten query", rendered_debug)
        self.assertIn("score=4.2500", rendered_debug)
        self.assertIn("Rewrite source: cache", rendered_debug)
        debug_label_index = debug_output.index(ASSISTANT_LABEL)
        debug_separator_index = debug_output.index(SEPARATOR, debug_label_index)
        debug_answer_index = debug_output.index("Answer [S1].", debug_separator_index)
        self.assertLess(debug_label_index, debug_separator_index)
        self.assertLess(debug_separator_index, debug_answer_index)


if __name__ == "__main__":
    unittest.main()
