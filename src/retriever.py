"""Conversation-agnostic cosine retrieval over a local policy index."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

from .chunking import PolicyChunk
from .embeddings import SparseVector
from .indexing import PolicyIndex, load_index


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A ranked chunk with its cosine similarity score."""

    score: float
    chunk_id: str
    text: str
    source_path: str
    source_url: str
    title: str
    heading_path: tuple[str, ...]
    chunk_index: int

    @classmethod
    def from_chunk(cls, score: float, chunk: PolicyChunk) -> "RetrievalResult":
        return cls(
            score=score,
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            source_path=chunk.source_path,
            source_url=chunk.source_url,
            title=chunk.title,
            heading_path=chunk.heading_path,
            chunk_index=chunk.chunk_index,
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["heading_path"] = list(self.heading_path)
        return data


class PolicyRetriever:
    """Top-k retrieval for standalone query strings."""

    def __init__(self, index: PolicyIndex) -> None:
        self._index = index

    @classmethod
    def from_index(cls, path: Path | str) -> "PolicyRetriever":
        return cls(load_index(path))

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_vector = self._index.embedder.transform([query])[0]
        scored = [
            (cosine_similarity(query_vector, vector), chunk)
            for chunk, vector in zip(self._index.chunks, self._index.vectors)
        ]
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return [
            RetrievalResult.from_chunk(score, chunk)
            for score, chunk in scored[: min(top_k, len(scored))]
        ]


def cosine_similarity(left: SparseVector, right: SparseVector) -> float:
    """Compute cosine similarity for two sparse vectors."""

    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot_product = sum(value * right.get(index, 0.0) for index, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot_product / (left_norm * right_norm) if left_norm and right_norm else 0.0
