"""Local Cross-Encoder relevance scoring for retrieval candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class PairScorer(Protocol):
    """Minimal scoring interface used by the reranked retriever."""

    model_name: str

    def score(self, query: str, candidate_texts: Sequence[str]) -> list[float]: ...


class CrossEncoderReranker:
    """Thin sentence-transformers CrossEncoder wrapper for local inference."""

    provider = "sentence-transformers-cross-encoder"

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        *,
        cache_folder: Path | str | None = None,
        device: str = "cpu",
        batch_size: int = 16,
        local_files_only: bool = False,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as error:  # pragma: no cover - environment setup failure
            raise RuntimeError(
                "Cross-Encoder reranking requires sentence-transformers. "
                "Install the dependencies from requirements.txt."
            ) from error

        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = CrossEncoder(
            model_name,
            cache_folder=str(cache_folder) if cache_folder else None,
            device=device,
            local_files_only=local_files_only,
        )

    def score(self, query: str, candidate_texts: Sequence[str]) -> list[float]:
        """Score each query/candidate pair in one batched model call."""

        if not query.strip():
            raise ValueError("query must not be blank")
        if not candidate_texts:
            return []
        pairs = [(query, text) for text in candidate_texts]
        scores = self._model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [float(score) for score in scores.reshape(-1)]
