"""Dependency-free local text embeddings for the initial retrieval baseline."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence


SparseVector = dict[int, float]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*", re.IGNORECASE)
_CONTEXT_LINE_PATTERN = re.compile(r"^(?:Document|Section):\s*(.+)$", re.MULTILINE)
_STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "does",
    "for",
    "from",
    "github",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "regarding",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


@dataclass(slots=True)
class HashingTfidfEmbedder:
    """Hashing TF-IDF embeddings with persisted corpus-level IDF weights.

    This is a deterministic, local lexical baseline rather than a neural
    semantic embedding model. Word unigrams and bigrams are hashed into a fixed
    feature space, weighted with TF-IDF, and L2-normalized.
    """

    dimensions: int = 32_768
    idf: tuple[float, ...] | None = None

    provider: str = "local"
    model: str = "hashing-tfidf-v4"

    def __post_init__(self) -> None:
        if self.dimensions <= 0:
            raise ValueError("dimensions must be positive")
        if self.idf is not None and len(self.idf) != self.dimensions:
            raise ValueError("idf length must match dimensions")

    def fit(self, texts: Sequence[str]) -> None:
        if not texts:
            raise ValueError("at least one text is required to fit embeddings")

        document_frequency: Counter[int] = Counter()
        for text in texts:
            document_frequency.update(set(self._feature_counts(text)))

        document_count = len(texts)
        self.idf = tuple(
            math.log((1 + document_count) / (1 + document_frequency.get(index, 0))) + 1.0
            for index in range(self.dimensions)
        )

    def fit_transform(self, texts: Sequence[str], *, batch_size: int = 32) -> list[SparseVector]:
        self.fit(texts)
        return self.transform_batched(texts, batch_size=batch_size)

    def transform_batched(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
    ) -> list[SparseVector]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        vectors: list[SparseVector] = []
        for start in range(0, len(texts), batch_size):
            vectors.extend(self.transform(texts[start : start + batch_size]))
        return vectors

    def transform(self, texts: Iterable[str]) -> list[SparseVector]:
        if self.idf is None:
            raise RuntimeError("embedder must be fitted or loaded before transform")

        vectors: list[SparseVector] = []
        for text in texts:
            counts = self._feature_counts(text)
            weighted = {
                index: (1.0 + math.log(count)) * self.idf[index]
                for index, count in counts.items()
            }
            norm = math.sqrt(sum(value * value for value in weighted.values()))
            vectors.append(
                {index: value / norm for index, value in weighted.items()} if norm else {}
            )
        return vectors

    def to_dict(self) -> dict[str, object]:
        if self.idf is None:
            raise RuntimeError("cannot serialize an unfitted embedder")
        return {
            "provider": self.provider,
            "model": self.model,
            "dimensions": self.dimensions,
            "idf": list(self.idf),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "HashingTfidfEmbedder":
        if data.get("provider") != "local" or data.get("model") != "hashing-tfidf-v4":
            raise ValueError("unsupported embedding provider or model in index")
        return cls(
            dimensions=int(data["dimensions"]),
            idf=tuple(float(value) for value in data["idf"]),  # type: ignore[arg-type]
        )

    def _feature_counts(self, text: str) -> Counter[int]:
        tokens = self._tokens(text)
        counts = Counter(self._hash_feature(feature) for feature in self._features(tokens))

        # Titles and heading paths are concise, high-value context. They already
        # appear once in the embedding text; weight their features eight-fold so
        # long section bodies do not drown them out.
        for context in _CONTEXT_LINE_PATTERN.findall(text):
            context_counts = Counter(
                self._hash_feature(feature) for feature in self._features(self._tokens(context))
            )
            for index, count in context_counts.items():
                counts[index] += count * 7
        return counts

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [
            token
            for match in _TOKEN_PATTERN.finditer(text)
            if (token := match.group(0).lower()) not in _STOP_WORDS
        ]

    @staticmethod
    def _features(tokens: Sequence[str]) -> list[str]:
        unigrams = [f"word:{token}" for token in tokens]
        prefixes = [f"prefix:{token[:5]}" for token in tokens if len(token) >= 6]
        bigrams = [f"bigram:{left}::{right}" for left, right in zip(tokens, tokens[1:])]
        return unigrams + prefixes + bigrams

    def _hash_feature(self, feature: str) -> int:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dimensions
