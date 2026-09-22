"""Build and persist a dense semantic index over the existing policy chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np

from .chunking import PolicyChunk, build_embedding_text
from .indexing import load_index
from .semantic_embeddings import DEFAULT_SEMANTIC_MODEL, SentenceTransformerEncoder


SEMANTIC_INDEX_SCHEMA_VERSION = 1


class DocumentEncoder(Protocol):
    model_name: str
    provider: str

    def encode_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> np.ndarray: ...


@dataclass(frozen=True, slots=True)
class SemanticIndex:
    """The unchanged policy chunks and their normalized dense vectors."""

    chunks: tuple[PolicyChunk, ...]
    vectors: np.ndarray
    model_name: str
    provider: str = "sentence-transformers"
    normalized: bool = True

    def __post_init__(self) -> None:
        if self.vectors.ndim != 2:
            raise ValueError("semantic vectors must be a two-dimensional matrix")
        if len(self.chunks) != self.vectors.shape[0]:
            raise ValueError("semantic index must contain one vector per chunk")


def build_semantic_index(
    chunks: Sequence[PolicyChunk],
    encoder: DocumentEncoder,
    *,
    batch_size: int = 32,
    show_progress_bar: bool = False,
) -> SemanticIndex:
    """Encode the same contextual text used by the lexical index foundation."""

    if not chunks:
        raise ValueError("cannot build a semantic index without chunks")
    embedding_texts = [build_embedding_text(chunk) for chunk in chunks]
    vectors = encoder.encode_documents(
        embedding_texts,
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
    )
    return SemanticIndex(
        chunks=tuple(chunks),
        vectors=np.asarray(vectors, dtype=np.float32),
        model_name=encoder.model_name,
        provider=encoder.provider,
    )


def save_semantic_index(index: SemanticIndex, metadata_path: Path | str) -> None:
    """Persist metadata as JSON and dense vectors as a reusable NumPy array."""

    destination = Path(metadata_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    vectors_path = destination.with_suffix(".npy")
    vectors_temporary = vectors_path.with_suffix(".npy.tmp")
    metadata_temporary = destination.with_suffix(f"{destination.suffix}.tmp")

    with vectors_temporary.open("wb") as output:
        np.save(output, index.vectors.astype(np.float32, copy=False), allow_pickle=False)

    payload = {
        "schema_version": SEMANTIC_INDEX_SCHEMA_VERSION,
        "provider": index.provider,
        "model": index.model_name,
        "normalized": index.normalized,
        "dimensions": int(index.vectors.shape[1]),
        "vectors_file": vectors_path.name,
        "chunk_count": len(index.chunks),
        "chunks_sha256": chunk_fingerprint(index.chunks),
        "embedding_input": "Document title + heading path + unchanged chunk text",
        "chunks": [chunk.to_dict() for chunk in index.chunks],
    }
    metadata_temporary.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    vectors_temporary.replace(vectors_path)
    metadata_temporary.replace(destination)


def load_semantic_index(metadata_path: Path | str) -> SemanticIndex:
    source = Path(metadata_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SEMANTIC_INDEX_SCHEMA_VERSION:
        raise ValueError(f"unsupported semantic index schema in {source}")

    chunks = tuple(PolicyChunk.from_dict(item) for item in payload["chunks"])
    if payload.get("chunks_sha256") != chunk_fingerprint(chunks):
        raise ValueError("semantic index chunk metadata fingerprint does not match")
    vectors_path = source.parent / payload["vectors_file"]
    vectors = np.load(vectors_path, allow_pickle=False)
    if vectors.shape != (len(chunks), int(payload["dimensions"])):
        raise ValueError("semantic vector matrix shape does not match metadata")
    return SemanticIndex(
        chunks=chunks,
        vectors=np.asarray(vectors, dtype=np.float32),
        model_name=str(payload["model"]),
        provider=str(payload["provider"]),
        normalized=bool(payload["normalized"]),
    )


def chunk_fingerprint(chunks: Sequence[PolicyChunk]) -> str:
    encoded = json.dumps(
        [chunk.to_dict() for chunk in chunks],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lexical-index",
        type=Path,
        default=project_root / "cache" / "policy_index.json",
        help="existing lexical index whose exact chunks will be reused",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "cache" / "semantic_index.json",
    )
    parser.add_argument("--model", default=DEFAULT_SEMANTIC_MODEL)
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=project_root / "cache" / "huggingface",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)

    lexical_index = load_index(args.lexical_index)
    encoder = SentenceTransformerEncoder(
        args.model,
        cache_folder=args.model_cache,
        device=args.device,
    )
    semantic_index = build_semantic_index(
        lexical_index.chunks,
        encoder,
        batch_size=args.batch_size,
        show_progress_bar=True,
    )
    save_semantic_index(semantic_index, args.output)
    print(f"Chunks encoded: {len(semantic_index.chunks)}")
    print(f"Model: {semantic_index.model_name}")
    print(f"Dimensions: {semantic_index.vectors.shape[1]}")
    print(f"Metadata: {args.output.resolve()}")
    print(f"Vectors: {args.output.with_suffix('.npy').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

