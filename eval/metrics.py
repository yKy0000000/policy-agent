"""Stable, label-based metrics for offline evidence evaluation."""

from __future__ import annotations

from collections import Counter
from statistics import mean

POLICIES = ("fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2")


def score_facts(facts: list[dict], chunks: list[dict]) -> dict:
    """Score direct-support mappings in selection order."""
    required = {fact["fact_id"]: set(fact["direct_chunk_ids"]) for fact in facts}
    if not required or any(not ids for ids in required.values()):
        raise ValueError("every case needs directly supported required facts")
    seen: set[str] = set()
    first_complete_k = None
    for index, chunk in enumerate(chunks, 1):
        seen.add(chunk["chunk_id"])
        if all(ids & seen for ids in required.values()):
            first_complete_k = index
            break
    selected_ids = {chunk["chunk_id"] for chunk in chunks}
    covered = [fid for fid, ids in required.items() if ids & selected_ids]
    missing = [fid for fid in required if fid not in covered]
    return {
        "covered_fact_ids": covered,
        "missing_fact_ids": missing,
        "covered_count": len(covered),
        "coverage": len(covered) / len(required),
        "fact_complete": not missing,
        "first_complete_k": first_complete_k,
        "post_completion_evidence_tokens": (
            sum(chunk["token_count"] for chunk in chunks[first_complete_k:])
            if first_complete_k is not None else None
        ),
    }


def summarize_cases(rows: list[dict], field: str) -> dict:
    items = ([row["policies"][field] for row in rows] if field in POLICIES
             else [row[field] for row in rows])
    total_facts = sum(row["required_fact_count"] for row in rows)
    tokens = sum(item["evidence_tokens"] for item in items)
    result = {
        "fact_complete_cases": sum(item["fact_complete"] for item in items),
        "macro_fact_coverage": mean(item["coverage"] for item in items),
        "micro_fact_coverage": sum(item["covered_count"] for item in items) / total_facts,
        "covered_facts": sum(item["covered_count"] for item in items),
        "total_evidence_tokens": tokens,
        "avg_k": mean(item["selected_k"] for item in items),
    }
    if field in POLICIES:
        post = sum(item["post_completion_evidence_tokens"] or 0 for item in items)
        result.update({
            "post_completion_evidence_tokens": post,
            "post_completion_share_of_tokens": post / tokens,
        })
    return result


def select_oracle(options: dict[str, dict]) -> dict:
    """Offline upper bound only: uses gold required-fact labels unavailable at inference time."""
    best = min((-item["covered_count"], item["evidence_tokens"], item["selected_k"])
               for item in options.values())
    winners = [name for name in POLICIES
               if (-options[name]["covered_count"], options[name]["evidence_tokens"],
                   options[name]["selected_k"]) == best]
    chosen = dict(options[winners[0]])
    chosen.update({"selected_strategy": winners[0] if len(winners) == 1 else None,
                   "co_optimal_strategies": winners})
    return chosen


def winner_counts(rows: list[dict]) -> tuple[dict[str, int], dict[str, list[str]]]:
    unique = Counter(row["oracle"]["selected_strategy"] for row in rows
                     if row["oracle"]["selected_strategy"])
    ties = {row["case_id"]: row["oracle"]["co_optimal_strategies"] for row in rows
            if row["oracle"]["selected_strategy"] is None}
    return {name: unique[name] for name in POLICIES}, ties


def evidence_utilization(available_fact_ids: list[str], answered_fact_ids: list[str]) -> dict:
    """Only facts present in supplied evidence belong in the denominator."""
    available = set(available_fact_ids)
    used = available.intersection(answered_fact_ids)
    return {"answered_available_facts": len(used),
            "available_facts": len(available),
            "rate": len(used) / len(available) if available else None}


def answer_quality_key(item: dict) -> tuple:
    """Quality dimensions precede evidence cost for the offline answer oracle."""
    quality = item["quality"]
    claims = quality["claims"]
    return (
        int(quality.get("grounded_fact_complete", quality["fact_complete"])),
        quality.get("grounded_covered_count", quality["covered_count"]),
        int(quality["fact_complete"]),
        quality["covered_count"],
        -quality["synthesis_error_count"],
        -claims["contradicted"],
        -claims["unsupported"],
        -claims["partial"],
        -claims.get("uncertain", 0),
        -(quality.get("claim_citations", {}).get("unsupported", 0) +
          quality.get("claim_citations", {}).get("missing", 0)),
        quality["fact_citation_supported_count"],
    )


def select_answer_oracle(options: dict[str, dict]) -> dict:
    """Offline analysis only; answer quality is lexicographic before token cost."""
    best_quality = max(answer_quality_key(options[name]) for name in POLICIES)
    quality_ties = [name for name in POLICIES
                    if answer_quality_key(options[name]) == best_quality]
    min_tokens = min(options[name]["evidence_tokens"] for name in quality_ties)
    winners = [name for name in quality_ties
               if options[name]["evidence_tokens"] == min_tokens]
    return {"selected_strategy": winners[0] if len(winners) == 1 else None,
            "co_optimal_strategies": winners,
            "quality_ties_before_cost": quality_ties,
            "evidence_tokens": min_tokens,
            "quality_key": best_quality}
