from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from src.conversation import (
    RewriteCache,
    build_rewrite_messages,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from src.llm_client import LLMClientError, LLMConfig, OpenAIChatCompletionsClient, parse_chat_completion


class EchoClient:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append((messages, max_tokens, temperature))
        return self.output


class ConversationTests(unittest.TestCase):
    def test_provider_usage_is_reported_only_when_present(self) -> None:
        class Response:
            def __init__(self, data):
                self.data = data

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def read(self):
                return json.dumps(self.data).encode("utf-8")

        client = OpenAIChatCompletionsClient(LLMConfig("key", "https://example.test", "model"))
        messages = [{"role": "user", "content": "Question?"}]
        with patch("src.llm_client.urlopen", return_value=Response({
            "choices": [{"message": {"content": "Answer"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        })):
            answer, usage = client.complete_with_usage(messages)
        self.assertEqual(answer, "Answer")
        self.assertEqual(usage, {"input_tokens": 12, "output_tokens": 3})

        with patch("src.llm_client.urlopen", return_value=Response({
            "choices": [{"message": {"content": "Answer"}}],
        })):
            answer, usage = client.complete_with_usage(messages)
        self.assertEqual(usage, {"input_tokens": None, "output_tokens": None})

    def test_history_window_keeps_only_two_recent_turns(self) -> None:
        history = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ]

        selected = select_recent_history(history, max_turns=2)

        self.assertEqual([item["content"] for item in selected], ["u2", "a2", "u3", "a3"])

    def test_prompt_contains_rules_history_and_latest_question(self) -> None:
        messages = build_rewrite_messages(
            [
                {"role": "user", "content": "Tell me about private information removal."},
                {"role": "assistant", "content": "It may disable qualifying content."},
            ],
            "What happens to forks?",
        )

        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("Do not answer", messages[0]["content"])
        self.assertIn("User: Tell me about private information removal.", messages[1]["content"])
        self.assertIn("What happens to forks?", messages[1]["content"])

    def test_self_contained_query_uses_same_contextualizer_interface(self) -> None:
        question = "What personal information does GitHub collect?"
        client = EchoClient(question)

        rewritten = rewrite_or_keep([], question, client)

        self.assertEqual(rewritten, question)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][1:], (96, 0.0))

    def test_chat_completion_response_parsing(self) -> None:
        self.assertEqual(
            parse_chat_completion(
                {"choices": [{"message": {"content": "  standalone query  "}}]}
            ),
            "standalone query",
        )
        with self.assertRaises(LLMClientError):
            parse_chat_completion({"choices": []})

    def test_rewrite_cache_key_is_deterministic_and_model_bound(self) -> None:
        history = [{"role": "user", "content": "topic"}]
        first = rewrite_cache_key(
            model="model-a", history=history, latest_question="follow-up"
        )
        second = rewrite_cache_key(
            model="model-a", history=history, latest_question="follow-up"
        )
        different = rewrite_cache_key(
            model="model-b", history=history, latest_question="follow-up"
        )

        self.assertEqual(first, second)
        self.assertNotEqual(first, different)

    def test_rewrite_cache_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rewrites.json"
            cache = RewriteCache(path)
            cache.set("key", "rewrite", {"model": "test"})

            self.assertEqual(RewriteCache(path).get("key"), "rewrite")


if __name__ == "__main__":
    unittest.main()
