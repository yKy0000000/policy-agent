"""Offline marginal-information Dynamic-K study on the 16 V3 development cases.

This module never reads Validation V1 outcomes or calls an LLM. Its labels are
used only for retrospective evidence scoring, never by the selector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median

import numpy as np

from eval.metrics import score_facts
from eval.run_evidence_eval import ROOT, load_inputs, sha256
from src.semantic_indexing import load_semantic_index


OUTPUT = ROOT / "eval/results/dynamic_k_analysis.json"
SUMMARY = ROOT / "eval/results/dynamic_k_summary.md"
EVIDENCE_BASELINE = ROOT / "eval/results/evidence_eval.json"
SEMANTIC_INDEX = ROOT / "cache/semantic_index.json"
K_MIN = 5
K_MAX = 20
TOKEN_BUDGET = 6000


@dataclass(frozen=True)
class DynamicConfig:
    name: str
    formulation: str
    threshold: float
    patience: int
    structural_bonus: float = 0.0


# Four small, interpretable alternatives fixed before reading fact outcomes.
CONFIGS = (
    DynamicConfig("product_p2", "product", 0.10, 2),
    DynamicConfig("product_p3", "product", 0.07, 3),
    DynamicConfig("additive_p2", "additive", 0.35, 2),
    DynamicConfig("product_section_p3", "product", 0.08, 3, 0.08),
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _relevance(scores: list[float]) -> list[float]:
    """Per-query Top20 min-max; never mix raw cross-encoder scores with cosine."""
    low, high = min(scores), max(scores)
    if high == low:
        return [1.0] * len(scores)
    return [(score - low) / (high - low) for score in scores]


def _section(chunk: dict) -> tuple[str, tuple[str, ...]]:
    return chunk["source_path"], tuple(chunk["heading_path"])


def select_dynamic(chunks: list[dict], vectors: dict[str, np.ndarray],
                   config: DynamicConfig) -> dict:
    """Select Top5, then scan in rank order until patience or a hard limit."""
    if len(chunks) < K_MIN:
        raise ValueError("fewer than five reranked candidates")
    if config.patience not in (1, 2, 3) or config.formulation not in ("product", "additive"):
        raise ValueError("unsupported exploratory configuration")
    ranked = chunks[:K_MAX]
    relevance = _relevance([float(chunk["reranker_score"]) for chunk in ranked])
    selected = list(ranked[:K_MIN])
    tokens = sum(int(chunk["token_count"]) for chunk in selected)
    if tokens > TOKEN_BUDGET:
        raise ValueError("Top5 exceeds the fixed token budget")
    low_streak = 0
    trace = []
    stop = "max_k"
    for rank, candidate in enumerate(ranked[K_MIN:], K_MIN + 1):
        vector = vectors[candidate["chunk_id"]]
        similarity = max(float(np.dot(vector, vectors[item["chunk_id"]]))
                         for item in selected)
        novelty = min(1.0, max(0.0, 1.0 - similarity))
        bonus = config.structural_bonus if _section(candidate) not in {
            _section(item) for item in selected} else 0.0
        rel = relevance[rank - 1]
        gain = ((rel * novelty) if config.formulation == "product" else
                (0.5 * rel + 0.5 * novelty)) + bonus
        decision = "skip_low_gain"
        if gain >= config.threshold:
            if tokens + int(candidate["token_count"]) > TOKEN_BUDGET:
                decision = "stop_token_budget"
                stop = "token_budget"
            else:
                selected.append(candidate)
                tokens += int(candidate["token_count"])
                low_streak = 0
                decision = "add"
        else:
            low_streak += 1
            if low_streak >= config.patience:
                decision = "stop_patience"
                stop = "patience"
        trace.append({"rank": rank, "chunk_id": candidate["chunk_id"],
                      "relevance": rel, "max_similarity": similarity,
                      "novelty": novelty, "structural_bonus": bonus,
                      "gain": gain, "decision": decision,
                      "selected_k_after": len(selected)})
        if decision.startswith("stop"):
            break
    else:
        stop = "max_k" if len(ranked) == K_MAX else "candidate_exhausted"
    return {"selected_chunks": selected, "selected_k": len(selected),
            "scan_depth": trace[-1]["rank"] if trace else K_MIN,
            "evidence_tokens": tokens, "stop_reason": stop, "trace": trace}


def _option(facts: list[dict], selected: list[dict], scan_depth: int | None = None,
            stop_reason: str | None = None, trace: list[dict] | None = None) -> dict:
    scored = score_facts(facts, selected)
    return {**scored, "selected_k": len(selected),
            "selected_ranks": [chunk["reranker_rank"] for chunk in selected],
            "selected_chunk_ids": [chunk["chunk_id"] for chunk in selected],
            "evidence_tokens": sum(chunk["token_count"] for chunk in selected),
            "scan_depth": scan_depth or len(selected), "stop_reason": stop_reason,
            "trace": trace or []}


def _summary(rows: list[dict], name: str) -> dict:
    options = [row["options"][name] for row in rows]
    total = sum(row["required_fact_count"] for row in rows)
    ks = [item["selected_k"] for item in options]
    post = sum(item["post_completion_evidence_tokens"] or 0 for item in options)
    return {"macro_atomic_fact_coverage": mean(item["coverage"] for item in options),
            "micro_atomic_fact_coverage": sum(item["covered_count"] for item in options) / total,
            "covered_facts": sum(item["covered_count"] for item in options),
            "fact_complete_cases": sum(item["fact_complete"] for item in options),
            "evidence_tokens": sum(item["evidence_tokens"] for item in options),
            "average_k": mean(ks), "median_k": median(ks),
            "min_k": min(ks), "max_k": max(ks),
            "k_distribution": {str(k): count for k, count in sorted(Counter(ks).items())},
            "post_completion_evidence_tokens": post,
            "post_completion_share": post / sum(item["evidence_tokens"] for item in options),
            "selection_misses": sum(row["top20"]["covered_count"] -
                                    row["options"][name]["covered_count"] for row in rows),
            "candidate_ceiling_cases": [row["case_id"] for row in rows
                                        if not row["candidate_pool"]["fact_complete"]],
            "top20_depth_ceiling_cases": [row["case_id"] for row in rows
                                          if row["candidate_pool"]["fact_complete"] and
                                          not row["top20"]["fact_complete"]]}


def _comparison(candidate: dict, v1: dict) -> dict:
    return {"micro_coverage_regret_vs_v1":
                v1["micro_atomic_fact_coverage"] - candidate["micro_atomic_fact_coverage"],
            "complete_case_deficit_vs_v1": v1["fact_complete_cases"] - candidate["fact_complete_cases"],
            "token_saving_vs_v1": v1["evidence_tokens"] - candidate["evidence_tokens"],
            "token_saving_fraction_vs_v1":
                1 - candidate["evidence_tokens"] / v1["evidence_tokens"],
            "post_completion_reduction_vs_v1":
                v1["post_completion_evidence_tokens"] - candidate["post_completion_evidence_tokens"],
            "post_completion_reduction_fraction_vs_v1":
                1 - candidate["post_completion_evidence_tokens"] /
                v1["post_completion_evidence_tokens"]}


def analyze() -> dict:
    benchmark, rubric, frozen, strategies, facts_by_case = load_inputs()
    semantic = load_semantic_index(SEMANTIC_INDEX)
    vector_by_id = {chunk.chunk_id: semantic.vectors[index]
                    for index, chunk in enumerate(semantic.chunks)}
    text_by_id = {chunk.chunk_id: chunk.text for chunk in semantic.chunks}
    rows = []
    for case, snapshot, saved in zip(benchmark["cases"], frozen["cases"], strategies["cases"]):
        cid = case["case_id"]
        ranked = [chunk | {"reranker_rank": rank}
                  for rank, chunk in enumerate(snapshot["top20"], 1)]
        if any(chunk["chunk_id"] not in vector_by_id or
               chunk["text"] != text_by_id.get(chunk["chunk_id"]) for chunk in ranked):
            raise ValueError(f"semantic index is not aligned with frozen V3 chunks: {cid}")
        facts = facts_by_case[cid]
        options = {}
        for label, strategy_name in (("fixed_top5", "fixed_top5"),
                                     ("adaptive_prefix_v1", "adaptive_prefix_v1")):
            ranks = saved[strategy_name]["original_ranks"]
            options[label] = _option(facts, [ranked[rank - 1] for rank in ranks])
        for config in CONFIGS:
            selected = select_dynamic(ranked, vector_by_id, config)
            options[config.name] = _option(facts, selected["selected_chunks"],
                selected["scan_depth"], selected["stop_reason"], selected["trace"])
        pool = score_facts(facts, snapshot["candidate_pool"])
        top20 = score_facts(facts, ranked)
        rows.append({"case_id": cid, "query": case["query"],
                     "required_fact_count": len(facts), "candidate_pool": pool,
                     "top20": top20, "options": options})
    summaries = {name: _summary(rows, name) for name in
                 ("fixed_top5", "adaptive_prefix_v1", *(config.name for config in CONFIGS))}
    saved_baseline = json.loads(EVIDENCE_BASELINE.read_text(encoding="utf-8"))["policies"]
    for name in ("fixed_top5", "adaptive_prefix_v1"):
        current, saved = summaries[name], saved_baseline[name]
        checks = ((current["covered_facts"], saved["covered_facts"]),
                  (current["fact_complete_cases"], saved["fact_complete_cases"]),
                  (current["evidence_tokens"], saved["total_evidence_tokens"]),
                  (current["post_completion_evidence_tokens"],
                   saved["post_completion_evidence_tokens"]))
        if any(left != right for left, right in checks):
            raise ValueError(f"{name} differs from frozen evidence baseline")
    baseline = summaries["adaptive_prefix_v1"]
    comparisons = {config.name: _comparison(summaries[config.name], baseline)
                   for config in CONFIGS}
    return {"schema_version": 1, "name": "marginal_information_dynamic_k",
            "status": "exploratory_development_only_not_independently_validated",
            "case_count": 16, "required_fact_count": 92,
            "source_sha256": {"benchmark": sha256(ROOT / "eval/broad_queries_v3_adjudicated.json"),
                              "rubric": sha256(ROOT / "eval/broad_query_v3_atomic_facts_frozen_candidate.json"),
                              "frozen_top20": sha256(ROOT / "eval/results/broad_v3_frozen_top20.json"),
                              "strategy_outputs": sha256(ROOT / "eval/results/broad_v3_coverage_selector_eval.json"),
                              "evidence_baseline": sha256(EVIDENCE_BASELINE),
                              "semantic_index": sha256(SEMANTIC_INDEX),
                              "semantic_vectors": sha256(SEMANTIC_INDEX.with_suffix(".npy"))},
            "method": {"relevance": "per-query min-max over frozen reranked Top20",
                       "novelty": "clamp(1 - maximum cosine similarity to selected evidence, 0, 1)",
                       "structural_bonus": "0.08 for a previously unseen source document/heading pair in one candidate",
                       "initial_k": K_MIN, "maximum_k": K_MAX,
                       "token_budget": TOKEN_BUDGET,
                       "low_gain_candidates": "skipped; stop after patience consecutive skips"},
            "configs": [asdict(config) for config in CONFIGS],
            "exploratory_recommended_config": None,
            "recommendation_reason": "The configurations that reduce tokens lose 6–7 required facts and three complete cases versus V1; the configuration that improves coverage uses 55% more tokens.",
            "answer_quality_next_stage": False,
            "summaries": summaries, "comparisons_vs_v1": comparisons,
            "cases": rows}


def render_summary(result: dict, recommended: str | None) -> str:
    summaries = result["summaries"]
    lines = ["# Marginal-Information Dynamic-K", "", "## Motivation", "",
             "Reranker relevance does not measure how much information a chunk adds to selected evidence.",
             "", "## Method", "",
             "Top5 start; per-query Top20 min-max relevance; semantic novelty = 1 − maximum selected-evidence cosine similarity. Scan in rank order, skip low-gain chunks, stop after 2–3 consecutive low gains; K≤20 and tokens≤6,000.",
             "Product gain = relevance × novelty; additive gain = 0.5 × relevance + 0.5 × novelty. One variant adds 0.08 for a new document/heading pair. Thresholds and patience are recorded in the JSON result.",
             "", "## Evidence Results", "",
             "| Strategy | Macro | Micro | Complete | Avg K | Tokens | Post-completion |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name in ("fixed_top5", "adaptive_prefix_v1", *(config["name"] for config in result["configs"])):
        item = summaries[name]
        lines.append(f"| {name} | {item['macro_atomic_fact_coverage']:.3f} | "
                     f"{item['micro_atomic_fact_coverage']:.3f} | {item['fact_complete_cases']}/16 | "
                     f"{item['average_k']:.2f} | {item['evidence_tokens']:,} | "
                     f"{item['post_completion_evidence_tokens']:,} |")
    lines += ["", "## K Distribution", ""]
    for config in result["configs"]:
        name = config["name"]
        distribution = ", ".join(f"K={k}×{count}"
                                 for k, count in summaries[name]["k_distribution"].items())
        lines.append(f"- {name}: {distribution}.")
    lines += ["", "## Key Observation", ""]
    if recommended:
        comparison = result["comparisons_vs_v1"][recommended]
        lines.append(f"- Exploratory recommendation: `{recommended}`; micro regret "
                     f"{comparison['micro_coverage_regret_vs_v1']:.3f}, "
                     f"complete-case deficit {comparison['complete_case_deficit_vs_v1']}, "
                     f"token saving {comparison['token_saving_fraction_vs_v1']:.1%}.")
    else:
        lines.append("- No recommended configuration: token-saving variants lose 6–7 facts and three complete cases versus V1.")
    lines.append("- The section-bonus variant covers one additional fact, but spends 55% more tokens and selects K=20 for 10/16 cases.")
    lines.append("- Product/additive variants produce varied K values, yet semantic novelty misses required policy distinctions.")
    lines.append("- V3-03 and V3-11 have candidate-pool ceilings; V3-01 has a Top20 depth ceiling.")
    lines += ["", "## Status", "", "Exploratory — not independently validated.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved exploratory result")
    args = parser.parse_args()
    result = analyze()
    if args.check:
        saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if result != saved:
            raise SystemExit("dynamic-K result differs from frozen development inputs")
        print("Dynamic-K exploratory evidence result matches saved inputs.")
        return
    _write(OUTPUT, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    _write(SUMMARY, render_summary(result, None))
    print(f"Wrote {OUTPUT} and {SUMMARY}")


if __name__ == "__main__":
    main()
