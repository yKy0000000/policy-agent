"""Build and persist the local policy retrieval index."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .chunking import ChunkingConfig, PolicyChunk, build_embedding_text, chunk_documents
from .embeddings import HashingTfidfEmbedder, SparseVector
from .ingest import load_policy_documents


INDEX_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PolicyIndex:
    """Chunks, normalized sparse vectors, and the fitted local embedder."""

    chunks: tuple[PolicyChunk, ...]
    vectors: tuple[SparseVector, ...]
    embedder: HashingTfidfEmbedder
    chunking_config: ChunkingConfig

    def __post_init__(self) -> None:
        if len(self.chunks) != len(self.vectors):
            raise ValueError("index must contain one vector per chunk")


def build_index(
    chunks: Sequence[PolicyChunk],
    *,
    embedder: HashingTfidfEmbedder | None = None,
    chunking_config: ChunkingConfig | None = None,
    batch_size: int = 32,
) -> PolicyIndex:
    """Generate contextual embedding text and embed chunks in batches."""

    if not chunks:
        raise ValueError("cannot build an index without chunks")
    model = embedder or HashingTfidfEmbedder()
    texts = [build_embedding_text(chunk) for chunk in chunks]
    vectors = model.fit_transform(texts, batch_size=batch_size)
    return PolicyIndex(
        chunks=tuple(chunks),
        vectors=tuple(vectors),
        embedder=model,
        chunking_config=chunking_config or ChunkingConfig(),
    )


def save_index(index: PolicyIndex, path: Path | str) -> None:
    """Atomically persist an inspectable JSON index."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "embedding": index.embedder.to_dict(),
        "chunking": {
            "target_size": index.chunking_config.target_size,
            "max_size": index.chunking_config.max_size,
            "overlap": index.chunking_config.overlap,
        },
        "chunks": [
            {
                **chunk.to_dict(),
                "embedding": [[feature, value] for feature, value in sorted(vector.items())],
            }
            for chunk, vector in zip(index.chunks, index.vectors)
        ],
    }
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary.replace(destination)


def load_index(path: Path | str) -> PolicyIndex:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise ValueError(f"unsupported index schema in {source}")

    embedding_data = payload["embedding"]
    chunking_data = payload["chunking"]
    entries = payload["chunks"]
    embedder = HashingTfidfEmbedder.from_dict(embedding_data)
    config = ChunkingConfig(
        target_size=int(chunking_data["target_size"]),
        max_size=int(chunking_data["max_size"]),
        overlap=int(chunking_data["overlap"]),
    )
    chunks = tuple(PolicyChunk.from_dict(entry) for entry in entries)
    vectors = tuple(
        {int(feature): float(value) for feature, value in entry["embedding"]}
        for entry in entries
    )
    return PolicyIndex(chunks, vectors, embedder, config)


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        default=project_root / "data" / "site-policy",
        help="path to the local github/site-policy clone",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "cache" / "policy_index.json",
        help="index output path",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)

    config = ChunkingConfig()
    documents = load_policy_documents(args.repository)
    chunks = chunk_documents(documents, config)
    index = build_index(chunks, chunking_config=config, batch_size=args.batch_size)
    save_index(index, args.output)
    print(f"Loaded documents: {len(documents)}")
    print(f"Generated chunks: {len(chunks)}")
    print(f"Embedding: {index.embedder.provider}/{index.embedder.model}")
    print(f"Saved index: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

