"""Local sentence-transformers encoding for semantic retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np


DEFAULT_SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEncoder:
    """Thin local encoder wrapper shared by indexing and query retrieval."""

    provider = "sentence-transformers"

    def __init__(
        self,
        model_name: str = DEFAULT_SEMANTIC_MODEL,
        *,
        cache_folder: Path | str | None = None,
        device: str = "cpu",
        local_files_only: bool = False,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:  # pragma: no cover - exercised by environment setup
            raise RuntimeError(
                "Semantic retrieval requires sentence-transformers. "
                "Install the dependencies from requirements.txt."
            ) from error

        self.model_name = model_name
        self.device = device
        self._model = SentenceTransformer(
            model_name,
            cache_folder=str(cache_folder) if cache_folder else None,
            device=device,
            local_files_only=local_files_only,
        )

    def encode_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        return self._encode(texts, batch_size=batch_size, show_progress_bar=show_progress_bar)

    def encode_query(self, query: str) -> np.ndarray:
        return self._encode([query], batch_size=1, show_progress_bar=False)[0]

    def _encode(
        self,
        texts: Sequence[str],
        *,
        batch_size: int,
        show_progress_bar: bool,
    ) -> np.ndarray:
        vectors = self._model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(vectors, dtype=np.float32)
