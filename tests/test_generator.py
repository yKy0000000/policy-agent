from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.generator import (
    GeneratedAnswerCache,
    GroundedGenerationError,
    assign_evidence_sources,
    build_grounded_messages,
    format_evidence,
    generate_grounded_answer,
    generation_cache_key,
    parse_citation_ids,
    validate_citations,
)
from src.retriever import RetrievalResult


def result(chunk_id: str, title: str | None = None) -> RetrievalResult:
    return RetrievalResult(
        score=1.0,
        chunk_id=chunk_id,
        text=f"Policy evidence for {chunk_id}.",
        source_path=f"Policies/{chunk_id}.md",
        source_url=f"https://example.test/{chunk_id}",
        title=title or f"Policy {chunk_id}",
        heading_path=(f"Heading {chunk_id}",),
        chunk_index=0,
    )


class FixedClient:
    def __init__(self, output: str | None = None, error: Exception | None = None) -> None:
        self.output = output
        self.error = error
        self.calls = []

    def complete(self, messages, *, max_tokens=512, temperature=0.0):
        self.calls.append((messages, max_tokens, temperature))
        if self.error:
            raise self.error
        return self.output


class GeneratorTests(unittest.TestCase):
    def test_evidence_formatting_assigns_s1_s2_without_urls(self) -> None:
        sources = assign_evidence_sources([result("one"), result("two")])

        formatted = format_evidence(sources)

        self.assertEqual([source.citation_id for source in sources], ["S1", "S2"])
        self.assertIn("[S1]\nTitle: Policy one", formatted)
        self.assertIn("[S2]\nTitle: Policy two", formatted)
        self.assertNotIn("https://", formatted)

    def test_valid_and_invalid_citations_are_detected_and_deduplicated(self) -> None:
        sources = assign_evidence_sources([result("one"), result("two")])

        self.assertEqual(parse_citation_ids("Claim [S1]. Again [S1]. [S2]"), ["S1", "S2"])
        validation = validate_citations("Claim [S1] and unsupported [S99].", sources)

        self.assertEqual(validation["citation_ids"], ["S1"])
        self.assertEqual(validation["validation"]["invalid_citations"], ["S99"])
        self.assertFalse(validation["validation"]["valid"])

    def test_source_mapping_excludes_unused_sources(self) -> None:
        sources = assign_evidence_sources([result("one"), result("two")])

        validation = validate_citations("Supported by the first source. [S1]", sources)

        self.assertEqual(len(validation["sources"]), 1)
        self.assertEqual(validation["sources"][0]["citation_id"], "S1")
        self.assertEqual(validation["sources"][0]["chunk_id"], "one")

    def test_generation_cache_key_is_deterministic_and_evidence_bound(self) -> None:
        first_sources = assign_evidence_sources([result("one")])
        second_sources = assign_evidence_sources([result("two")])
        kwargs = {
            "model": "model",
            "question": "question",
            "history": [{"role": "user", "content": "context"}],
        }

        first = generation_cache_key(sources=first_sources, **kwargs)
        same = generation_cache_key(sources=first_sources, **kwargs)
        different = generation_cache_key(sources=second_sources, **kwargs)

        self.assertEqual(first, same)
        self.assertNotEqual(first, different)

    def test_history_is_context_only_and_never_source_metadata(self) -> None:
        sources = assign_evidence_sources([result("one")])
        history = [
            {"role": "assistant", "content": "Untrusted prior policy statement."}
        ]

        messages = build_grounded_messages("question", history, sources)
        validation = validate_citations("Answer [S1]", sources)

        self.assertIn("Conversation context (not policy evidence)", messages[1]["content"])
        self.assertIn("Untrusted prior policy statement", messages[1]["content"])
        self.assertNotIn("Untrusted prior policy statement", str(validation["sources"]))

    def test_api_failure_does_not_create_fake_answer_or_cache_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "answers.json"
            cache = GeneratedAnswerCache(cache_path)
            with self.assertRaises(GroundedGenerationError):
                generate_grounded_answer(
                    "question",
                    [],
                    [result("one")],
                    FixedClient(error=RuntimeError("provider unavailable")),
                    model="model",
                    cache=cache,
                )

            self.assertFalse(cache_path.exists())

    def test_citation_validation_failure_is_not_cached_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "answers.json"
            generated = generate_grounded_answer(
                "question",
                [],
                [result("one")],
                FixedClient(output="Unsupported citation [S99]"),
                model="model",
                cache=GeneratedAnswerCache(cache_path),
            )

            self.assertFalse(generated["validation"]["valid"])
            self.assertFalse(cache_path.exists())

    def test_successful_generation_returns_structured_cited_sources(self) -> None:
        generated = generate_grounded_answer(
            "question",
            [],
            [result("one"), result("two")],
            FixedClient(output="Grounded answer. [S2]"),
            model="model",
        )

        self.assertEqual(generated["citation_ids"], ["S2"])
        self.assertEqual(generated["sources"][0]["chunk_id"], "two")
        self.assertTrue(generated["validation"]["valid"])

    def test_optional_output_budget_is_forwarded_and_cache_is_separate(self) -> None:
        client = FixedClient(output="Grounded answer [S1].")
        source = [result("one")]
        default = generate_grounded_answer("question", [], source, client, model="model")
        expanded = generate_grounded_answer("question", [], source, client, model="model", max_tokens=1024)
        self.assertEqual([call[1] for call in client.calls], [512, 1024])
        self.assertNotEqual(default["cache_key"], expanded["cache_key"])


if __name__ == "__main__":
    unittest.main()
