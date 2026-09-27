"""Runtime copy of the frozen A1 no-router Adaptive evidence-prefix rule.

Keep this function and its parameters in parity with
``eval/run_stage0_replay.py:no_router_adaptive_rows``. The evaluation file is
frozen and production modules must not import from eval.
"""

from __future__ import annotations


NO_ROUTER_DEFAULTS = {
    "initial_k": 5,
    "max_k": 20,
    "max_evidence_tokens": 6000,
    "max_score_drop": 3.0,
}


def no_router_adaptive_rows(
    rows: list[dict],
    *,
    initial_k: int = 5,
    max_k: int = 20,
    max_evidence_tokens: int = 6000,
    max_score_drop: float = 3.0,
) -> list[dict]:
    """Select the contiguous score-gap prefix after an unconditional Top5."""

    if not rows:
        return []
    limit = min(max_k, len(rows))
    k = min(initial_k, limit)
    used = sum(row["tokens"] for row in rows[:k])
    top_score = rows[0]["bge_score"]
    while k < limit:
        nxt = rows[k]
        if top_score - nxt["bge_score"] > max_score_drop:
            break
        if used + nxt["tokens"] > max_evidence_tokens:
            break
        used += nxt["tokens"]
        k += 1
    return rows[:k]
