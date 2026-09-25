"""Deterministic evidence-prefix budgeting over an already reranked list.

The selector never sees policy labels or calls retrieval, reranking, or an LLM.
It uses query structure and a lexical saturation proxy; neither proves that
every answer aspect is covered. Its limits and decisions are exposed in trace.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Sequence


_WORDS = re.compile(r"[a-z]{3,}")
_BREADTH = re.compile(r"\b(and|or|if|before|after|which|including)\b|,", re.I)
_CONDITION = re.compile(r"\b(if|limits?|conditions?|exceptions?|delay|withhold|affect|before|after)\b", re.I)
_STOPWORDS = frozenset(
    "a an the on in of for to with by from my me i we our it its what who when how why "
    "can could does do did is are be been that this there their them have has had "
    "or and about through github account policy policies someone something which your "
    "you us after before will should would as at one some".split()
)


def _terms(value: str) -> set[str]:
    return {word.rstrip("s") for word in _WORDS.findall(value.casefold()) if word not in _STOPWORDS}


def _coverage(query_terms: set[str], evidence: Sequence[Any]) -> float:
    if not query_terms:
        return 1.0
    body = " ".join(
        " ".join((str(item.title), " ".join(item.heading_path), str(item.text)))
        for item in evidence
    )
    return len(query_terms & _terms(body)) / len(query_terms)


def _default_token_count(item: Any) -> int:
    count = getattr(item, "token_count", None)
    if isinstance(count, int) and count >= 0:
        return count
    # Test/fake retrievers may not expose a tokenizer. Production passes the
    # existing CrossEncoder tokenizer through the retriever helper instead.
    return len(re.findall(r"\w+|[^\w\s]", str(item.text)))


def _dominant_source_fraction(evidence: Sequence[Any]) -> float:
    paths = [str(item.source_path) for item in evidence]
    return max(Counter(paths).values()) / len(paths)


@dataclass(frozen=True, slots=True)
class EvidenceBudgetConfig:
    initial_k: int = 5
    first_expansion_k: int = 8
    max_k: int = 20
    max_evidence_tokens: int = 6000
    saturation_coverage: float = 0.8
    deep_expansion_coverage: float = 0.8
    plateau_score_drop: float = 1.5
    max_score_drop: float = 3.0

    def __post_init__(self) -> None:
        if not 1 <= self.initial_k <= self.first_expansion_k <= self.max_k <= 20:
            raise ValueError("require 1 <= initial_k <= first_expansion_k <= max_k <= 20")
        if self.max_evidence_tokens <= 0:
            raise ValueError("max_evidence_tokens must be positive")
        if not 0 <= self.saturation_coverage <= 1 or not 0 <= self.deep_expansion_coverage <= 1:
            raise ValueError("coverage thresholds must be in [0, 1]")
        if self.plateau_score_drop < 0 or self.max_score_drop < self.plateau_score_drop:
            raise ValueError("score-drop thresholds must be nonnegative and ordered")


@dataclass(frozen=True, slots=True)
class EvidenceBudgetDecision:
    selected_k: int
    expansion_reason: str | None
    stop_reason: str
    evidence_tokens: int
    token_budget: int
    initial_query_coverage: float
    final_query_coverage: float
    candidate_count: int


def select_evidence_prefix(
    query: str,
    ranked: Sequence[Any],
    *,
    config: EvidenceBudgetConfig | None = None,
    token_count: Callable[[Any], int] = _default_token_count,
) -> EvidenceBudgetDecision:
    """Select a contiguous prefix, beginning at Top5 and never beyond Top20.

    Expansion first needs an explicit broad-query cue plus weak Top5 query-term
    coverage or a conditional/exception cue. It then takes at most Top8. A
    deeper scan requires unresolved query terms and a flat score tail; a
    conditional query with low reranker confidence and one dominant Top5 source
    also continues, since repeated text can falsely saturate query terms. It ends
    on coverage saturation, score decay, token cap, exhaustion, or Top20.
    """

    cfg = config or EvidenceBudgetConfig()
    if not query.strip() or not ranked:
        raise ValueError("query and ranked evidence must be nonempty")
    available = min(len(ranked), cfg.max_k)
    k = min(cfg.initial_k, available)
    counts = [int(token_count(item)) for item in ranked[:available]]
    if any(count < 0 for count in counts):
        raise ValueError("evidence token counts must be nonnegative")
    used = sum(counts[:k])
    words = _terms(query)
    initial_coverage = _coverage(words, ranked[:k])
    broad = bool(_BREADTH.search(query))
    conditional = bool(_CONDITION.search(query))
    if not broad:
        return EvidenceBudgetDecision(k, None, "query_not_broad", used, cfg.max_evidence_tokens,
                                      initial_coverage, initial_coverage, len(ranked))
    if initial_coverage >= cfg.saturation_coverage and not conditional:
        return EvidenceBudgetDecision(k, None, "top5_query_terms_saturated", used, cfg.max_evidence_tokens,
                                      initial_coverage, initial_coverage, len(ranked))

    reason = "conditional_scope" if conditional else "broad_query_low_top5_coverage"
    target = min(cfg.first_expansion_k, available)
    while k < target:
        if used + counts[k] > cfg.max_evidence_tokens:
            return EvidenceBudgetDecision(k, reason, "token_budget", used, cfg.max_evidence_tokens,
                                          initial_coverage, _coverage(words, ranked[:k]), len(ranked))
        used += counts[k]
        k += 1

    current_coverage = _coverage(words, ranked[:k])
    top5_score = float(ranked[min(cfg.initial_k, available) - 1].reranker_score)
    single_source_uncertainty = (
        conditional and top5_score < 0
        and _dominant_source_fraction(ranked[:min(cfg.initial_k, available)]) >= 0.8
    )
    needs_deeper_scan = current_coverage < cfg.deep_expansion_coverage or single_source_uncertainty
    if k == available:
        stop = "max_k" if k == cfg.max_k else "candidate_exhausted"
    elif not needs_deeper_scan:
        stop = "query_terms_saturated"
    elif float(ranked[cfg.initial_k - 1].reranker_score) - float(ranked[k - 1].reranker_score) > cfg.plateau_score_drop:
        stop = "score_plateau_ended"
    else:
        baseline_score = float(ranked[cfg.initial_k - 1].reranker_score)
        while k < available:
            if not single_source_uncertainty and _coverage(words, ranked[:k]) >= cfg.deep_expansion_coverage:
                stop = "query_terms_saturated"
                break
            if baseline_score - float(ranked[k].reranker_score) > cfg.max_score_drop:
                stop = "score_decay"
                break
            if used + counts[k] > cfg.max_evidence_tokens:
                stop = "token_budget"
                break
            used += counts[k]
            k += 1
        else:
            stop = "max_k" if k == cfg.max_k else "candidate_exhausted"

    return EvidenceBudgetDecision(k, reason, stop, used, cfg.max_evidence_tokens,
                                  initial_coverage, _coverage(words, ranked[:k]), len(ranked))
