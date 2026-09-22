"""Cross-Encoder reranking over a fixed lexical/semantic candidate union."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Protocol, Sequence

from .reranker import PairScorer
from .retriever import RetrievalResult


LEXICAL_CANDIDATE_K = 20
SEMANTIC_CANDIDATE_K = 20


class RetrieverBackend(Protocol):
    def search(self, query: str, top_k: int = 5) -> Sequence[RetrievalResult]: ...


@dataclass(frozen=True, slots=True)
class Candidate:
    """One deduplicated candidate plus component ranks used only for debugging."""

    result: RetrievalResult
    lexical_rank: int | None
    semantic_rank: int | None


@dataclass(frozen=True, slots=True)
class RerankedRetrievalResult:
    """A candidate independently scored by the Cross-Encoder."""

    reranker_score: float
    chunk_id: str
    text: str
    source_path: str
    source_url: str
    title: str
    heading_path: tuple[str, ...]
    chunk_index: int
    lexical_rank: int | None
    semantic_rank: int | None

    @property
    def score(self) -> float:
        """Compatibility alias for the shared eval runner."""

        return self.reranker_score

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["heading_path"] = list(self.heading_path)
        return data


@dataclass(frozen=True, slots=True)
class RerankTiming:
    candidate_count: int
    reranker_seconds: float
    total_seconds: float


def candidate_union(
    lexical_results: Sequence[RetrievalResult],
    semantic_results: Sequence[RetrievalResult],
) -> list[Candidate]:
    """Deduplicate component results by chunk ID while preserving their ranks."""

    records: dict[str, dict[str, object]] = {}
    order: list[str] = []
    for source_name, results in (("lexical", lexical_results), ("semantic", semantic_results)):
        rank_key = f"{source_name}_rank"
        for rank, result in enumerate(results, start=1):
            if result.chunk_id not in records:
                records[result.chunk_id] = {
                    "result": result,
                    "lexical_rank": None,
                    "semantic_rank": None,
                }
                order.append(result.chunk_id)
            if records[result.chunk_id][rank_key] is None:
                records[result.chunk_id][rank_key] = rank

    return [
        Candidate(
            result=records[chunk_id]["result"],  # type: ignore[arg-type]
            lexical_rank=records[chunk_id]["lexical_rank"],  # type: ignore[arg-type]
            semantic_rank=records[chunk_id]["semantic_rank"],  # type: ignore[arg-type]
        )
        for chunk_id in order
    ]


def build_reranker_text(result: RetrievalResult) -> str:
    """Use the same title/heading/body structure as semantic document embeddings."""

    section = " > ".join(result.heading_path) if result.heading_path else "Document introduction"
    return f"Document: {result.title}\nSection: {section}\n\n{result.text}"


class RerankedPolicyRetriever:
    """Rerank a fixed Top20+Top20 union without using component scores or ranks."""

    lexical_candidate_k = LEXICAL_CANDIDATE_K
    semantic_candidate_k = SEMANTIC_CANDIDATE_K

    def __init__(
        self,
        lexical_retriever: RetrieverBackend,
        semantic_retriever: RetrieverBackend,
        reranker: PairScorer,
    ) -> None:
        self._lexical = lexical_retriever
        self._semantic = semantic_retriever
        self._reranker = reranker
        self.timings: list[RerankTiming] = []

    @property
    def reranker_model(self) -> str:
        return self._reranker.model_name

    def candidates(self, query: str) -> list[Candidate]:
        """Build the fixed candidate pool without invoking the Cross-Encoder."""

        if not query.strip():
            raise ValueError("query must not be blank")
        lexical = self._lexical.search(query, top_k=self.lexical_candidate_k)
        semantic = self._semantic.search(query, top_k=self.semantic_candidate_k)
        return candidate_union(lexical, semantic)

    def search(self, query: str, top_k: int = 5) -> list[RerankedRetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        pipeline_started = perf_counter()
        candidates = self.candidates(query)
        texts = [build_reranker_text(candidate.result) for candidate in candidates]
        started = perf_counter()
        scores = self._reranker.score(query, texts)
        reranker_elapsed = perf_counter() - started
        if len(scores) != len(candidates):
            raise ValueError("reranker returned a different number of scores than candidates")
        self.timings.append(
            RerankTiming(
                candidate_count=len(candidates),
                reranker_seconds=reranker_elapsed,
                total_seconds=perf_counter() - pipeline_started,
            )
        )

        reranked = [
            RerankedRetrievalResult(
                reranker_score=score,
                chunk_id=candidate.result.chunk_id,
                text=candidate.result.text,
                source_path=candidate.result.source_path,
                source_url=candidate.result.source_url,
                title=candidate.result.title,
                heading_path=candidate.result.heading_path,
                chunk_index=candidate.result.chunk_index,
                lexical_rank=candidate.lexical_rank,
                semantic_rank=candidate.semantic_rank,
            )
            for candidate, score in zip(candidates, scores)
        ]
        reranked.sort(key=lambda result: (-result.reranker_score, result.chunk_id))
        return reranked[: min(top_k, len(reranked))]
