"""Focused tests for semantic index persistence, search, and eval reuse."""

from pathlib import Path
import tempfile
import unittest

import numpy as np

from eval.run_retrieval_eval import evaluate_candidates
from src.chunking import PolicyChunk
from src.indexing import build_index
from src.retriever import PolicyRetriever
from src.semantic_indexing import (
    SemanticIndex,
    build_semantic_index,
    load_semantic_index,
    save_semantic_index,
)
from src.semantic_retriever import SemanticPolicyRetriever


def chunk(chunk_id: str, text: str, path: str, heading: str) -> PolicyChunk:
    return PolicyChunk(
        chunk_id=chunk_id,
        text=text,
        source_path=path,
        source_url=f"https://example.test/{path}",
        title="Example Policy",
        heading_path=(heading,),
        chunk_index=0,
    )


class FakeEncoder:
    provider = "fake"
    model_name = "fake-semantic-model"

    def encode_documents(self, texts, *, batch_size=32, show_progress_bar=False):
        del batch_size, show_progress_bar
        return np.asarray(
            [[1.0, 0.0] if "malware" in text.lower() else [0.0, 1.0] for text in texts],
            dtype=np.float32,
        )

    def encode_query(self, query):
        return np.asarray(
            [1.0, 0.0] if "malware" in query.lower() else [0.0, 1.0],
            dtype=np.float32,
        )


class SemanticRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            chunk("malware", "Malware policy text.", "Policies/malware.md", "Malware"),
            chunk("privacy", "Privacy policy text.", "Policies/privacy.md", "Privacy"),
        ]

    def test_semantic_index_build_and_load_preserves_chunks_and_vectors(self) -> None:
        index = build_semantic_index(self.chunks, FakeEncoder())
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "semantic.json"
            save_semantic_index(index, path)
            restored = load_semantic_index(path)

        self.assertEqual([item.chunk_id for item in restored.chunks], ["malware", "privacy"])
        np.testing.assert_allclose(restored.vectors, index.vectors)
        self.assertEqual(restored.model_name, FakeEncoder.model_name)

    def test_semantic_search_matches_lexical_result_shape_and_can_coexist(self) -> None:
        semantic_index = SemanticIndex(
            chunks=tuple(self.chunks),
            vectors=np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
            model_name=FakeEncoder.model_name,
            provider=FakeEncoder.provider,
        )
        semantic = SemanticPolicyRetriever(semantic_index, FakeEncoder())
        lexical = PolicyRetriever(build_index(self.chunks))

        semantic_result = semantic.search("malware", top_k=1)[0]
        lexical_result = lexical.search("malware", top_k=1)[0]

        self.assertEqual(semantic_result.chunk_id, "malware")
        self.assertEqual(set(semantic_result.to_dict()), set(lexical_result.to_dict()))

    def test_eval_runner_accepts_semantic_backend(self) -> None:
        semantic_index = SemanticIndex(
            chunks=tuple(self.chunks),
            vectors=np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
            model_name=FakeEncoder.model_name,
            provider=FakeEncoder.provider,
        )
        semantic = SemanticPolicyRetriever(semantic_index, FakeEncoder())
        candidates = [
            {
                "id": "case",
                "category": "semantic",
                "question": "What is the malware policy?",
                "expected_sources": [
                    {
                        "title": "Example Policy",
                        "heading_contains": "Malware",
                        "source_path": "Policies/malware.md",
                    }
                ],
            }
        ]

        evaluated = evaluate_candidates(candidates, semantic, ranking_depth=2)

        self.assertTrue(evaluated[0]["hit_at_1"])
        self.assertEqual(evaluated[0]["top_5"][0]["chunk_id"], "malware")


if __name__ == "__main__":
    unittest.main()

