"""Offline evidence-level A/B for pointwise rerankers on frozen Validation V1.

Fixed: queries, chunking, lexical/semantic retrieve, full candidate union,
candidate dedup, metadata, the model-independent token counter, and the frozen
gold mapping. The only variable is the pointwise reranker model.

No generation, no judge, no external LLM/API. The production default reranker is
never modified; the challenger exists only as an eval-runner argument.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from statistics import mean, median

from eval.analyze_evidence_geometry import approx_tokens
from eval.run_validation import direct_support_map
from src.reranked_retriever import build_reranker_text

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "eval/validation/validation_v1_metadata.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
INDEX = ROOT / "cache/policy_index.json"
GEOMETRY = ROOT / "eval/results/evidence_geometry_analysis.json"
OUTPUT = ROOT / "eval/results/reranker_ab_analysis.json"
SUMMARY = ROOT / "eval/results/reranker_ab_summary.md"

BASELINE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_CHALLENGER = "BAAI/bge-reranker-base"
CHECKPOINT_TOKENS = (1000, 2000, 3000, 4000, 5000, 6000)
RANK_BUCKETS = (("rank_1", 1, 1), ("rank_2_5", 2, 5), ("rank_6_8", 6, 8),
                ("rank_9_10", 9, 10), ("rank_11_20", 11, 20))


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Pure metric helpers (unit-testable, no model)
# --------------------------------------------------------------------------- #

def gold_rank_rows(facts: list[dict], ranked_ids: list[str]) -> list[dict]:
    position = {chunk_id: index for index, chunk_id in enumerate(ranked_ids, 1)}
    rows = []
    for fact in facts:
        ranks = [position[chunk_id] for chunk_id in fact["direct_chunk_ids"]
                 if chunk_id in position]
        rows.append({"fact_id": fact["fact_id"], "gold_chunk_ids": list(fact["direct_chunk_ids"]),
                     "union_rank": min(ranks) if ranks else None})
    return rows


def rank_histogram(rank_rows: list[dict]) -> dict:
    ranks = [row["union_rank"] for row in rank_rows if row["union_rank"] is not None]
    buckets = {name: sum(1 for rank in ranks if low <= rank <= high)
               for name, low, high in RANK_BUCKETS}
    buckets["rank_gt_20"] = sum(1 for rank in ranks if rank > 20)
    buckets["missing"] = sum(1 for row in rank_rows if row["union_rank"] is None)
    return {"unit": "facts", "total": len(rank_rows), "buckets": buckets,
            "top1": sum(1 for rank in ranks if rank == 1),
            "top5": sum(1 for rank in ranks if rank <= 5),
            "exact": {str(k): v for k, v in sorted(Counter(ranks).items())}}


def coverage_at_k(rank_rows: list[dict], k: int) -> int:
    return sum(1 for row in rank_rows if row["union_rank"] is not None
               and row["union_rank"] <= k)


def complete_at_k(case_rank_rows: dict[str, list[dict]], k: int) -> int:
    return sum(1 for rows in case_rank_rows.values()
               if rows and all(row["union_rank"] is not None and row["union_rank"] <= k
                               for row in rows))


def deepest_gold_rank(rank_rows: list[dict]) -> int | None:
    ranks = [row["union_rank"] for row in rank_rows if row["union_rank"] is not None]
    return max(ranks) if ranks else None


def tail_rank_movement(baseline_rows: dict[str, dict], challenger_rows: dict[str, dict],
                       tail_ids: list[str], fact_meta: dict[str, dict] | None = None) -> dict:
    fact_meta = fact_meta or {}
    improved = unchanged = regressed = into_top5 = into_top8 = 0
    items = []
    for fact_id in tail_ids:
        before = baseline_rows[fact_id]["union_rank"]
        after = challenger_rows[fact_id]["union_rank"]
        delta = (before - after) if (before is not None and after is not None) else None
        if delta is None:
            movement = "unknown"
        elif delta > 0:
            improved += 1
            movement = "improved"
        elif delta < 0:
            regressed += 1
            movement = "regressed"
        else:
            unchanged += 1
            movement = "unchanged"
        if after is not None and after <= 5:
            into_top5 += 1
        if after is not None and after <= 8:
            into_top8 += 1
        items.append({"fact_id": fact_id, "case_id": fact_meta.get(fact_id, {}).get("case_id"),
                      "gold_chunk_id": fact_meta.get(fact_id, {}).get("gold_chunk_id"),
                      "baseline_rank": before, "challenger_rank": after,
                      "delta": delta, "movement": movement,
                      "moved_into_top5": after is not None and after <= 5,
                      "moved_into_top8": after is not None and after <= 8})
    return {"tail_fact_count": len(tail_ids), "improved": improved, "unchanged": unchanged,
            "regressed": regressed, "moved_into_top5": into_top5, "moved_into_top8": into_top8,
            "items": items}


def token_view(ranked_ids: list[str], tokens: dict[str, int], facts: list[dict],
               checkpoints: tuple[int, ...] = CHECKPOINT_TOKENS) -> dict:
    support = {fact["fact_id"]: set(fact["direct_chunk_ids"]) for fact in facts}
    covered: set[str] = set()
    cumulative = 0
    curve = []
    for chunk_id in ranked_ids:
        cumulative += tokens.get(chunk_id, 0)
        covered.update(fact_id for fact_id, ids in support.items() if chunk_id in ids)
        curve.append((cumulative, len(covered)))
    first_complete = next((cum for cum, count in curve if count == len(support)), None)
    at = {}
    for checkpoint in checkpoints:
        value = curve[-1][1] if curve else 0
        for cum, count in curve:
            if cum >= checkpoint:
                value = count
                break
        at[checkpoint] = value
    return {"coverage_at_token_checkpoints": at, "first_complete_tokens": first_complete}


def length_bias(ranked_ids: list[str], tokens: dict[str, int], k: int) -> dict:
    values = [tokens.get(chunk_id, 0) for chunk_id in ranked_ids[:k]]
    return {"avg_chunk_tokens": mean(values) if values else 0.0,
            "median_chunk_tokens": median(values) if values else 0.0,
            "total_tokens": sum(values)}


# --------------------------------------------------------------------------- #
# Model-backed ranking (integration path; not exercised by unit tests)
# --------------------------------------------------------------------------- #

def load_unions(queries: dict, chunk_meta: dict) -> dict[str, list[str]]:
    """The candidate union is model-independent; reuse the geometry cache."""
    if GEOMETRY.exists():
        cached = _json(GEOMETRY).get("retrieval_cache", {}).get("scopes", {})
        if cached and all(case["case_id"] in cached for case in queries["cases"]):
            return {case_id: [cid for cid in scope["union"] if cid in chunk_meta]
                    for case_id, scope in cached.items()}
    from eval.run_validation import _local_retriever
    retriever, index = _local_retriever()
    return {case["case_id"]: sorted(candidate.result.chunk_id
                                    for candidate in retriever.candidates(case["query"]))
            for case in queries["cases"]}


def rank_union(scorer, query: str, union_ids: list[str], chunk_meta: dict) -> list[str]:
    texts = [build_reranker_text(_Result(chunk_meta[chunk_id])) for chunk_id in union_ids]
    scores = scorer.score(query, texts)
    if len(scores) != len(union_ids):
        raise ValueError("reranker returned a different number of scores than candidates")
    ordered = sorted(zip(union_ids, scores), key=lambda item: (-item[1], item[0]))
    return [chunk_id for chunk_id, _ in ordered]


class _Result:
    """Adapter exposing the attribute surface build_reranker_text expects."""

    def __init__(self, chunk: dict) -> None:
        self.title = chunk["title"]
        self.heading_path = tuple(chunk.get("heading_path") or ())
        self.text = chunk["text"]


def evaluate_model(name: str, scorer, cases: list[dict], support: dict,
                   unions: dict[str, list[str]], chunk_meta: dict,
                   tokens: dict[str, int]) -> dict:
    per_case, per_fact = {}, {}
    for case in cases:
        case_id = case["case_id"]
        facts = [{"fact_id": fact_id, "direct_chunk_ids": support[fact_id]}
                 for fact_id in case["fact_ids"]]
        ranked = rank_union(scorer, case["query"], unions[case_id], chunk_meta)
        rows = gold_rank_rows(facts, ranked)
        per_case[case_id] = rows
        per_fact[case_id] = ranked
    return {"model": name, "per_case_ranks": per_case, "per_case_order": per_fact}


def _cache_folder() -> Path:
    """Pick the Hugging Face hub folder that actually holds the models."""
    import os
    candidates = [ROOT / "cache/huggingface"]
    if os.environ.get("HF_HOME"):
        candidates.append(Path(os.environ["HF_HOME"]) / "hub")
    candidates.append(Path.home() / ".cache/huggingface/hub")
    for candidate in candidates:
        if candidate.exists() and any(candidate.glob("models--*")):
            return candidate
    return ROOT / "cache/huggingface"


def _make_scorer(model_name: str, *, cache_folder: Path | None = None):
    from src.reranker import CrossEncoderReranker
    return CrossEncoderReranker(model_name, cache_folder=cache_folder or _cache_folder(),
                                device="cpu", local_files_only=True)


# --------------------------------------------------------------------------- #
# Comparison and reporting
# --------------------------------------------------------------------------- #

def summarize_model(result: dict, cases: list[dict], tokens: dict[str, int]) -> dict:
    all_rows = [row for case_id in result["per_case_ranks"]
                for row in result["per_case_ranks"][case_id]]
    by_case = result["per_case_ranks"]
    per_case_metrics = {}
    for case in cases:
        case_id = case["case_id"]
        rows = by_case[case_id]
        per_case_metrics[case_id] = {
            "deepest_gold_rank": deepest_gold_rank(rows),
            "first_complete_k": deepest_gold_rank(rows),
            "fact_complete@5": bool(rows) and all(
                r["union_rank"] is not None and r["union_rank"] <= 5 for r in rows),
            "fact_complete@8": bool(rows) and all(
                r["union_rank"] is not None and r["union_rank"] <= 8 for r in rows),
            "fact_complete@10": bool(rows) and all(
                r["union_rank"] is not None and r["union_rank"] <= 10 for r in rows),
        }
    token_views = {}
    for case in cases:
        case_id = case["case_id"]
        facts = [{"fact_id": row["fact_id"], "direct_chunk_ids": row["gold_chunk_ids"]}
                 for row in by_case[case_id]]
        token_views[case_id] = token_view(result["per_case_order"][case_id], tokens, facts)
    pooled_checkpoints = {checkpoint: sum(view["coverage_at_token_checkpoints"][checkpoint]
                                          for view in token_views.values())
                          for checkpoint in CHECKPOINT_TOKENS}
    lengths = {}
    for k in (5, 8, 10):
        per_case_length = [length_bias(result["per_case_order"][case["case_id"]], tokens, k)
                           for case in cases]
        lengths[f"top{k}"] = {
            "avg_chunk_tokens": mean(item["avg_chunk_tokens"] for item in per_case_length),
            "median_chunk_tokens": median(item["median_chunk_tokens"] for item in per_case_length),
            "total_tokens": sum(item["total_tokens"] for item in per_case_length)}
    return {
        "model": result["model"],
        "rank_histogram": rank_histogram(all_rows),
        "coverage_at_k": {k: coverage_at_k(all_rows, k) for k in (1, 3, 5, 8, 10, 20)},
        "fact_complete_cases_at_k": {k: complete_at_k(by_case, k) for k in (5, 8, 10, 20)},
        "deepest_gold_rank": _distribution([m["deepest_gold_rank"]
                                            for m in per_case_metrics.values()]),
        "per_case": per_case_metrics,
        "first_complete_tokens": _distribution([view["first_complete_tokens"]
                                                for view in token_views.values()]),
        "coverage_at_token_checkpoints_pooled": pooled_checkpoints,
        "length_bias": lengths,
        "per_case_ranks": by_case,
    }


def _distribution(values: list) -> dict:
    data = sorted(value for value in values if value is not None)
    if not data:
        return {"n": 0, "median": None, "mean": None, "min": None, "max": None}
    return {"n": len(data), "median": median(data), "mean": mean(data),
            "min": data[0], "max": data[-1]}


def compare(baseline: dict, challenger: dict, cases: list[dict]) -> dict:
    base_fact = {fact_id: row for case_id, rows in baseline["per_case_ranks"].items()
                 for fact_id, row in ((r["fact_id"], r) for r in rows)}
    chal_fact = {fact_id: row for case_id, rows in challenger["per_case_ranks"].items()
                 for fact_id, row in ((r["fact_id"], r) for r in rows)}
    tail_ids = [fact_id for fact_id, row in base_fact.items()
                if row["union_rank"] is not None and 6 <= row["union_rank"] <= 20]
    tail_ids.sort(key=lambda fid: base_fact[fid]["union_rank"])
    deep_tail_ids = [fact_id for fact_id in tail_ids if base_fact[fact_id]["union_rank"] >= 11]
    fact_meta = {}
    for case_id, rows in baseline["per_case_ranks"].items():
        for row in rows:
            fact_meta[row["fact_id"]] = {
                "case_id": case_id,
                "gold_chunk_id": next(iter(row["gold_chunk_ids"]), None)}
    movement = tail_rank_movement(base_fact, chal_fact, tail_ids, fact_meta)
    movement["deep_tail_items"] = [item for item in movement["items"]
                                   if item["fact_id"] in deep_tail_ids]
    return {"tail_movement": movement,
            "deep_tail_ids": deep_tail_ids,
            "tail_ids": tail_ids}


def _verdict(summary: dict, comparison: dict) -> dict:
    base_cov5 = summary["baseline"]["coverage_at_k"][5]
    chal_cov5 = summary["challenger"]["coverage_at_k"][5]
    base_complete5 = summary["baseline"]["fact_complete_cases_at_k"][5]
    chal_complete5 = summary["challenger"]["fact_complete_cases_at_k"][5]
    mov = comparison["tail_movement"]
    delta_cov5 = chal_cov5 - base_cov5
    improved = mov["improved"]
    regressed = mov["regressed"]
    if delta_cov5 < 1 and base_complete5 == chal_complete5 and improved == 0 and regressed == 0:
        gate = "WASH"
    elif regressed > improved or delta_cov5 < 0:
        gate = "REGRESSION"
    elif improved >= max(1, round((improved + regressed + mov["unchanged"]) * 0.4)) and delta_cov5 >= 1:
        gate = "CLEAR EVIDENCE WIN"
    else:
        gate = "SMALL / MIXED WIN"
    return {"evidence_gate": gate, "coverage_at_5_delta": delta_cov5,
            "fact_complete_at_5_delta": chal_complete5 - base_complete5,
            "tail_improved": improved, "tail_regressed": regressed}


def _render_summary(result: dict) -> str:
    base, chal = result["baseline"], result["challenger"]
    lines = ["# Stronger Pointwise Reranker A/B (evidence level)", "",
             "Frozen Validation V1, fixed candidate union; only the reranker model varies.",
             "No generation, no judge, no external API.", "",
             "## Models",
             f"- baseline: `{result['models']['baseline']}`",
             f"- challenger: `{result['models']['challenger']}` ({result['challenger_status']})",
             f"- candidate union hash: `{result['candidate_invariant']['union_hash'][:16]}`; "
             f"baseline==challenger union: {result['candidate_invariant']['baseline_equals_challenger']}",
             f"- runtime (s): {result['runtime_seconds']}",
             "", "## Gold Rank Distribution (facts)"]
    if chal is None:
        lines += ["- baseline buckets: " + json.dumps(base["rank_histogram"]["buckets"]),
                  "- baseline coverage@k: " + json.dumps(base["coverage_at_k"]),
                  "- baseline fact-complete cases@k: " +
                  json.dumps(base["fact_complete_cases_at_k"]),
                  "", "## Evidence Gate",
                  f"### {result['verdict']['evidence_gate']}", ""]
        return "\n".join(lines)
    lines += ["| bucket | baseline | challenger |", "|---|---:|---:|"]
    for bucket in list(base["rank_histogram"]["buckets"]):
        lines.append(f"| {bucket} | {base['rank_histogram']['buckets'][bucket]} | "
                     f"{chal['rank_histogram']['buckets'][bucket]} |")
    lines += ["", "## Coverage / Completeness",
              "| metric | baseline | challenger |", "|---|---:|---:|"]
    for k in (1, 3, 5, 8, 10, 20):
        lines.append(f"| coverage@{k} | {base['coverage_at_k'][k]} | {chal['coverage_at_k'][k]} |")
    for k in (5, 8, 10, 20):
        lines.append(f"| fact-complete cases@{k} | {base['fact_complete_cases_at_k'][k]} | "
                     f"{chal['fact_complete_cases_at_k'][k]} |")
    mov = result["comparison"]["tail_movement"]
    lines += ["", "## Tail Movement (baseline rank 6-20)",
              f"- tail facts {mov['tail_fact_count']}; improved {mov['improved']}; "
              f"unchanged {mov['unchanged']}; regressed {mov['regressed']}",
              f"- moved into Top5 {mov['moved_into_top5']}; into Top8 {mov['moved_into_top8']}",
              "", "## Deep-tail (baseline rank >= 11)",
              "| case | fact | gold chunk | baseline | challenger | delta |",
              "|---|---|---|---:|---:|---:|"]
    for item in mov["deep_tail_items"]:
        lines.append(f"| {item['case_id']} | {item['fact_id']} | {item['gold_chunk_id']} | "
                     f"{item['baseline_rank']} | {item['challenger_rank']} | {item['delta']} |")
    lines += ["", "## Evidence Gate", f"### {result['verdict']['evidence_gate']}",
              f"- coverage@5 delta {result['verdict']['coverage_at_5_delta']}, "
              f"fact-complete@5 delta {result['verdict']['fact_complete_at_5_delta']}", ""]
    return "\n".join(lines)


def run(challenger_model: str = DEFAULT_CHALLENGER, *, challenger_scorer=None) -> dict:
    metadata = _json(METADATA)
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    index = _json(INDEX)
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in index["chunks"]}
    support = direct_support_map(rubric, index["chunks"])
    cases = [{"case_id": case["case_id"], "query": case["query"],
              "fact_ids": [fact["fact_id"] for case_facts in rubric["cases"]
                           if case_facts["case_id"] == case["case_id"]
                           for fact in case_facts["facts"]]}
             for case in queries["cases"]]
    tokens = {chunk_id: approx_tokens(chunk["text"]) for chunk_id, chunk in chunk_meta.items()}
    unions = load_unions(queries, chunk_meta)
    union_hash = hashlib.sha256(json.dumps(
        {case_id: sorted(ids) for case_id, ids in sorted(unions.items())},
        ensure_ascii=False).encode()).hexdigest()

    started = time.perf_counter()
    baseline_result = evaluate_model("baseline", _make_scorer(BASELINE_MODEL), cases, support,
                                     unions, chunk_meta, tokens)
    baseline_seconds = time.perf_counter() - started
    baseline = summarize_model(baseline_result, cases, tokens)
    challenger_status = "ran"
    challenger_seconds = None
    try:
        started = time.perf_counter()
        scorer = challenger_scorer if challenger_scorer is not None else _make_scorer(challenger_model)
        challenger_result = evaluate_model("challenger", scorer, cases, support, unions,
                                           chunk_meta, tokens)
        challenger_seconds = time.perf_counter() - started
        challenger = summarize_model(challenger_result, cases, tokens)
        comparison = compare(baseline, challenger, cases)
        verdict = _verdict({"baseline": baseline, "challenger": challenger}, comparison)
        invariant = all(set(baseline_result["per_case_order"][case_id]) ==
                        set(challenger_result["per_case_order"][case_id]) ==
                        set(unions[case_id]) for case_id in unions)
    except Exception as error:  # environment/network failure; harness stays valid
        challenger_status = f"unavailable: {type(error).__name__}: {error}"
        challenger = None
        comparison = None
        invariant = None
        verdict = {"evidence_gate": "NOT EVALUABLE (challenger unavailable)"}
    result = {
        "schema_version": 1, "name": "Stronger pointwise reranker A/B (evidence level)",
        "status": "diagnostic",
        "provenance": {"rubric_sha256": _sha256(RUBRIC), "queries_sha256": _sha256(QUERIES),
                       "index_sha256": _sha256(INDEX)},
        "models": {"baseline": BASELINE_MODEL, "challenger": challenger_model},
        "challenger_status": challenger_status,
        "fixed": ["queries", "chunking", "lexical", "semantic", "candidate_union", "dedup",
                  "metadata", "token_counter", "gold_mapping"],
        "candidate_invariant": {"union_hash": union_hash,
                                "union_size_total": sum(len(ids) for ids in unions.values()),
                                "union_sizes": {case_id: len(ids) for case_id, ids in unions.items()},
                                "baseline_equals_challenger": invariant},
        "runtime_seconds": {"baseline": round(baseline_seconds, 2),
                            "challenger": round(challenger_seconds, 2)
                            if challenger_seconds is not None else None},
        "baseline": baseline, "challenger": challenger, "comparison": comparison,
        "verdict": verdict,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMMARY.write_text(_render_summary(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--challenger", default=DEFAULT_CHALLENGER)
    args = parser.parse_args(argv)
    result = run(args.challenger)
    print(json.dumps({"baseline": result["models"]["baseline"],
                      "challenger": result["models"]["challenger"],
                      "challenger_status": result["challenger_status"],
                      "verdict": result["verdict"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
