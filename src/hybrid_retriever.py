"""Rank-based hybrid retrieval using Reciprocal Rank Fusion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol, Sequence

from .retriever import RetrievalResult


DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_DEPTH = 20


class RetrieverBackend(Protocol):
    def search(self, query: str, top_k: int = 5) -> Sequence[RetrievalResult]: ...


@dataclass(frozen=True, slots=True)
class HybridConfig:
    rrf_k: int = DEFAULT_RRF_K
    candidate_depth: int = DEFAULT_CANDIDATE_DEPTH

    def __post_init__(self) -> None:
        if self.rrf_k < 0:
            raise ValueError("rrf_k must be non-negative")
        if self.candidate_depth <= 0:
            raise ValueError("candidate_depth must be positive")


@dataclass(frozen=True, slots=True)
class HybridRetrievalResult:
    """A unified retrieval result with optional component ranks for inspection."""

    score: float
    chunk_id: str
    text: str
    source_path: str
    source_url: str
    title: str
    heading_path: tuple[str, ...]
    chunk_index: int
    lexical_rank: int | None
    semantic_rank: int | None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["heading_path"] = list(self.heading_path)
        return data


def reciprocal_rank_fusion_score(
    ranks: Sequence[int | None],
    *,
    rrf_k: int = DEFAULT_RRF_K,
) -> float:
    """Calculate the standard unweighted RRF score for available ranks."""

    if rrf_k < 0:
        raise ValueError("rrf_k must be non-negative")
    score = 0.0
    for rank in ranks:
        if rank is None:
            continue
        if rank <= 0:
            raise ValueError("ranks must be positive")
        score += 1.0 / (rrf_k + rank)
    return score


class HybridPolicyRetriever:
    """Fuse fixed-depth lexical and semantic rankings with unweighted RRF."""

    def __init__(
        self,
        lexical_retriever: RetrieverBackend,
        semantic_retriever: RetrieverBackend,
        config: HybridConfig | None = None,
    ) -> None:
        self._lexical = lexical_retriever
        self._semantic = semantic_retriever
        self.config = config or HybridConfig()

    def search(self, query: str, top_k: int = 5) -> list[HybridRetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        lexical = list(self._lexical.search(query, top_k=self.config.candidate_depth))
        semantic = list(self._semantic.search(query, top_k=self.config.candidate_depth))
        return fuse_rankings(
            lexical,
            semantic,
            top_k=top_k,
            rrf_k=self.config.rrf_k,
        )


def fuse_rankings(
    lexical_results: Sequence[RetrievalResult],
    semantic_results: Sequence[RetrievalResult],
    *,
    top_k: int,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[HybridRetrievalResult]:
    """Merge two rankings by chunk ID and return a deterministic RRF ranking."""

    if top_k <= 0:
        raise ValueError("top_k must be positive")

    records: dict[str, dict[str, object]] = {}
    for source_name, results in (("lexical", lexical_results), ("semantic", semantic_results)):
        rank_key = f"{source_name}_rank"
        for rank, result in enumerate(results, start=1):
            record = records.setdefault(
                result.chunk_id,
                {
                    "result": result,
                    "lexical_rank": None,
                    "semantic_rank": None,
                },
            )
            if record[rank_key] is None:
                record[rank_key] = rank

    fused: list[HybridRetrievalResult] = []
    for record in records.values():
        result = record["result"]
        if not isinstance(result, RetrievalResult):
            raise TypeError("component retrievers must return RetrievalResult values")
        lexical_rank = record["lexical_rank"]
        semantic_rank = record["semantic_rank"]
        score = reciprocal_rank_fusion_score(
            (
                int(lexical_rank) if lexical_rank is not None else None,
                int(semantic_rank) if semantic_rank is not None else None,
            ),
            rrf_k=rrf_k,
        )
        fused.append(
            HybridRetrievalResult(
                score=score,
                chunk_id=result.chunk_id,
                text=result.text,
                source_path=result.source_path,
                source_url=result.source_url,
                title=result.title,
                heading_path=result.heading_path,
                chunk_index=result.chunk_index,
                lexical_rank=int(lexical_rank) if lexical_rank is not None else None,
                semantic_rank=int(semantic_rank) if semantic_rank is not None else None,
            )
        )

    fused.sort(key=lambda item: (-item.score, item.chunk_id))
    return fused[: min(top_k, len(fused))]

