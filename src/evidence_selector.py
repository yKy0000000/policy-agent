"""Deterministic set selection over reranked evidence and existing index vectors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np


_WORDS = re.compile(r"[a-z]{3,}")
_STOP = frozenset("a an the and or to of in on by for with from what how can could should would is are be my your our this that it its do does if i we you".split())


def _terms(value: str) -> set[str]:
    return {word.rstrip("s") for word in _WORDS.findall(value.casefold()) if word not in _STOP}


def _default_tokens(item: Any) -> int:
    count = getattr(item, "token_count", None)
    return count if isinstance(count, int) and count >= 0 else len(re.findall(r"\w+|[^\w\s]", item.text))


@dataclass(frozen=True, slots=True)
class CoverageSelectorConfig:
    min_k: int = 5
    max_k: int = 12
    max_evidence_tokens: int = 6000
    min_marginal_utility: float = 0.28
    relevance_weight: float = 0.4
    novelty_weight: float = 0.4
    query_gain_weight: float = 0.2

    def __post_init__(self) -> None:
        if not 1 <= self.min_k <= self.max_k <= 20 or self.max_evidence_tokens <= 0:
            raise ValueError("invalid evidence count or token budget")
        if not 0 <= self.min_marginal_utility <= 1:
            raise ValueError("utility threshold must be in [0, 1]")
        weights = (self.relevance_weight, self.novelty_weight, self.query_gain_weight)
        if any(weight < 0 for weight in weights) or not np.isclose(sum(weights), 1):
            raise ValueError("nonnegative utility weights must sum to one")


@dataclass(frozen=True, slots=True)
class CoverageSelectionDecision:
    selected_indices: tuple[int, ...]
    selected_k: int
    evidence_tokens: int
    token_budget: int
    stop_reason: str
    selection_steps: tuple[dict[str, Any], ...]


def select_evidence_set(
    query: str,
    ranked: Sequence[Any],
    *,
    vectors: Mapping[str, np.ndarray],
    config: CoverageSelectorConfig | None = None,
    token_count: Callable[[Any], int] = _default_tokens,
) -> CoverageSelectionDecision:
    """Greedy relevance, semantic novelty and query-term gain; indices are zero-based.

    Existing document vectors are required, so missing IDs fail visibly instead
    of silently replacing semantic novelty with a different scoring method.
    """
    cfg = config or CoverageSelectorConfig()
    if not query.strip() or not ranked:
        raise ValueError("query and ranked candidates must be nonempty")
    pool = list(ranked[:20])
    ids = [item.chunk_id for item in pool]
    if len(set(ids)) != len(ids):
        raise ValueError("candidate chunk IDs must be unique")
    missing = set(ids) - vectors.keys()
    if missing:
        raise ValueError(f"semantic vectors missing for {len(missing)} candidates")
    matrix = np.stack([np.asarray(vectors[chunk_id], dtype=np.float32) for chunk_id in ids])
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms == 0) or not np.all(np.isfinite(matrix)):
        raise ValueError("candidate semantic vectors must be finite and nonzero")
    matrix = matrix / norms[:, None]
    similarity = np.clip(matrix @ matrix.T, -1, 1)
    counts = [int(token_count(item)) for item in pool]
    if any(count < 0 for count in counts):
        raise ValueError("evidence token counts must be nonnegative")
    scores = [float(item.reranker_score) for item in pool]
    if not np.all(np.isfinite(scores)):
        raise ValueError("reranker scores must be finite")
    spread = max(scores) - min(scores)
    relevance = [(score - min(scores)) / spread if spread else 1.0 for score in scores]
    query_terms = _terms(query)
    item_terms = [_terms(" ".join((item.title, " ".join(item.heading_path), item.text))) & query_terms for item in pool]
    selected: list[int] = []
    covered: set[str] = set()
    used = 0
    steps: list[dict[str, Any]] = []
    limit = min(cfg.max_k, len(pool))
    while len(selected) < limit:
        candidates = []
        for index, item in enumerate(pool):
            if index in selected:
                continue
            novelty = 1.0 if not selected else 1.0 - max(0.0, float(max(similarity[index, chosen] for chosen in selected)))
            gain = len(item_terms[index] - covered) / len(query_terms) if query_terms else 0.0
            utility = cfg.relevance_weight * relevance[index] + cfg.novelty_weight * novelty + cfg.query_gain_weight * gain
            candidates.append({"rank": index + 1, "chunk_id": item.chunk_id, "relevance": round(relevance[index], 6),
                               "novelty": round(novelty, 6), "query_gain": round(gain, 6),
                               "utility": round(utility, 6), "tokens": counts[index],
                               "fits_budget": used + counts[index] <= cfg.max_evidence_tokens})
        affordable = [row for row in candidates if row["fits_budget"]]
        if not affordable:
            if len(selected) < cfg.min_k:
                raise ValueError("token budget cannot fit required min_k evidence")
            stop = "token_budget" if candidates else "candidate_exhausted"
            break
        # Keep the reranker's high-confidence Top-min_k as a relevance floor.
        # Beyond that floor, selection is non-contiguous and utility-driven.
        best = (next((row for row in affordable if row["rank"] == len(selected) + 1), None)
                if len(selected) < cfg.min_k else None)
        if best is None and len(selected) < cfg.min_k:
            raise ValueError("token budget cannot fit required min_k evidence")
        if best is None:
            best = max(affordable, key=lambda row: (row["utility"], -row["rank"]))
        if len(selected) >= cfg.min_k and best["utility"] < cfg.min_marginal_utility:
            stop = "marginal_utility"
            steps.append({"selection_order": len(selected) + 1, "chosen": None, "candidates": candidates})
            break
        index = best["rank"] - 1
        selected.append(index)
        used += counts[index]
        covered |= item_terms[index]
        steps.append({"selection_order": len(selected), "chosen": best, "candidates": candidates})
    else:
        stop = "max_k" if len(selected) == cfg.max_k else "candidate_exhausted"
    if not selected:
        raise ValueError("no candidate fits evidence token budget")
    return CoverageSelectionDecision(tuple(selected), len(selected), used, cfg.max_evidence_tokens, stop, tuple(steps))
