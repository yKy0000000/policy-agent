"""Focused tests for local index persistence and retrieval output."""

from pathlib import Path
import tempfile
import unittest

from src.chunking import PolicyChunk
from src.indexing import build_index, load_index, save_index
from src.retriever import PolicyRetriever


class RetrieverTests(unittest.TestCase):
    def test_returns_ranked_results_with_required_shape(self) -> None:
        chunks = [
            PolicyChunk(
                chunk_id="malware",
                text="GitHub prohibits active malware and malicious delivery infrastructure.",
                source_path="Policies/malware.md",
                source_url="https://example.test/malware",
                title="Malware Policy",
                heading_path=("Active malware",),
                chunk_index=0,
            ),
            PolicyChunk(
                chunk_id="privacy",
                text="GitHub collects account information supplied by users.",
                source_path="Policies/privacy.md",
                source_url="https://example.test/privacy",
                title="Privacy Policy",
                heading_path=("Information collection",),
                chunk_index=0,
            ),
        ]
        index = build_index(chunks)
        retriever = PolicyRetriever(index)

        results = retriever.search("What malware does GitHub prohibit?", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk_id, "malware")
        self.assertGreaterEqual(results[0].score, results[1].score)
        self.assertEqual(
            set(results[0].to_dict()),
            {
                "score",
                "chunk_id",
                "text",
                "source_path",
                "source_url",
                "title",
                "heading_path",
                "chunk_index",
            },
        )

    def test_index_round_trip_preserves_retrieval(self) -> None:
        chunk = PolicyChunk(
            chunk_id="appeal",
            text="A user may appeal an account suspension.",
            source_path="Policies/appeal.md",
            source_url="https://example.test/appeal",
            title="Appeal Policy",
            heading_path=("Appeals",),
            chunk_index=0,
        )
        index = build_index([chunk])

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "index.json"
            save_index(index, path)
            restored = load_index(path)

        result = PolicyRetriever(restored).search("account suspension appeal", top_k=1)[0]
        self.assertEqual(result.chunk_id, chunk.chunk_id)
        self.assertEqual(result.heading_path, chunk.heading_path)


if __name__ == "__main__":
    unittest.main()

