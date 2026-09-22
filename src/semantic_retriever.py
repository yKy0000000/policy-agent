"""Semantic cosine retrieval over a local sentence-transformers index."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .retriever import RetrievalResult
from .semantic_embeddings import SentenceTransformerEncoder
from .semantic_indexing import SemanticIndex, load_semantic_index


class QueryEncoder(Protocol):
    model_name: str

    def encode_query(self, query: str) -> np.ndarray: ...


class SemanticPolicyRetriever:
    """Top-k semantic retrieval with the same result structure as lexical retrieval."""

    def __init__(self, index: SemanticIndex, encoder: QueryEncoder) -> None:
        if encoder.model_name != index.model_name:
            raise ValueError(
                f"query model {encoder.model_name!r} does not match index model {index.model_name!r}"
            )
        self._index = index
        self._encoder = encoder

    @classmethod
    def from_index(
        cls,
        path: Path | str,
        *,
        model_cache: Path | str | None = None,
        device: str = "cpu",
    ) -> "SemanticPolicyRetriever":
        index = load_semantic_index(path)
        encoder = SentenceTransformerEncoder(
            index.model_name,
            cache_folder=model_cache,
            device=device,
            local_files_only=True,
        )
        return cls(index, encoder)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_vector = np.asarray(self._encoder.encode_query(query), dtype=np.float32)
        if query_vector.ndim != 1 or query_vector.shape[0] != self._index.vectors.shape[1]:
            raise ValueError("query embedding dimension does not match semantic index")
        query_norm = float(np.linalg.norm(query_vector))
        if query_norm == 0.0:
            scores = np.zeros(len(self._index.chunks), dtype=np.float32)
        elif self._index.normalized:
            scores = self._index.vectors @ (query_vector / query_norm)
        else:
            document_norms = np.linalg.norm(self._index.vectors, axis=1)
            denominators = document_norms * query_norm
            scores = np.divide(
                self._index.vectors @ query_vector,
                denominators,
                out=np.zeros_like(document_norms),
                where=denominators != 0,
            )

        ranking = sorted(
            range(len(self._index.chunks)),
            key=lambda index: (-float(scores[index]), self._index.chunks[index].chunk_id),
        )
        return [
            RetrievalResult.from_chunk(float(scores[index]), self._index.chunks[index])
            for index in ranking[: min(top_k, len(ranking))]
        ]
