"""Focused tests for structure-aware chunk generation."""

import unittest

from src.chunking import ChunkingConfig, build_embedding_text, chunk_document
from src.ingest import PolicyDocument


def make_document(text: str) -> PolicyDocument:
    return PolicyDocument(
        source_path="Policies/example/policy.md",
        title="Example Policy",
        headings=(),
        source_url="https://github.com/github/site-policy/blob/main/Policies/example/policy.md",
        text=text,
    )


class ChunkingTests(unittest.TestCase):
    def test_preserves_nested_heading_paths_and_metadata(self) -> None:
        document = make_document(
            "Introduction.\n\n"
            "## Accounts\n\nAccount rules.\n\n"
            "### Suspension\n\nSuspension rules.\n\n"
            "## Privacy\n\nPrivacy rules.\n"
        )

        chunks = chunk_document(document)

        self.assertEqual(
            [chunk.heading_path for chunk in chunks],
            [(), ("Accounts",), ("Accounts", "Suspension"), ("Privacy",)],
        )
        self.assertEqual(chunks[2].source_path, document.source_path)
        self.assertEqual(chunks[2].source_url, document.source_url)
        self.assertEqual(chunks[2].title, document.title)
        self.assertEqual(chunks[2].chunk_index, 2)
        self.assertIn("### Suspension", chunks[2].text)

    def test_chunk_ids_are_stable(self) -> None:
        document = make_document("## Rules\n\nPolicy text.\n")
        first = chunk_document(document)
        second = chunk_document(document)
        self.assertEqual([chunk.chunk_id for chunk in first], [chunk.chunk_id for chunk in second])

    def test_long_section_splits_below_hard_limit_with_overlap(self) -> None:
        paragraphs = [f"Paragraph {index} " + ("policy words " * 45) for index in range(18)]
        document = make_document("## Long section\n\n" + "\n\n".join(paragraphs))
        config = ChunkingConfig(target_size=3_000, max_size=4_500, overlap=400)

        chunks = chunk_document(document, config)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.text) <= config.max_size for chunk in chunks))
        self.assertTrue(set(chunks[0].text.split()) & set(chunks[1].text.split()))

    def test_embedding_text_adds_context_without_mutating_text(self) -> None:
        chunk = chunk_document(make_document("## Rules\n\nOriginal body."))[0]
        original = chunk.text
        embedding_text = build_embedding_text(chunk)
        self.assertIn("Document: Example Policy", embedding_text)
        self.assertIn("Section: Rules", embedding_text)
        self.assertTrue(embedding_text.endswith(original))
        self.assertEqual(chunk.text, original)


if __name__ == "__main__":
    unittest.main()

