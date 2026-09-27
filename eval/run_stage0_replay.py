"""Stage 0 replay harness for Query-Aware Retrieval V1 (offline; no LLM, no model load).

Verifies the frozen A0-BGE baseline against existing artifacts, replays the five frozen
context-allocation policies over the frozen BGE reranked orders, audits provider token
accounting, and records the Stage 0 gate status. This module implements no production code
and makes no API call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "eval/query_aware_stage0_config.json"
ROUTER = ROOT / "eval/query_aware_router_v1.json"
ARMS = ROOT / "eval/query_aware_arms_v1.json"
ORDERS = ROOT / "eval/results/a0_bge_rerank_orders.json"
WORKSHEET = ROOT / "eval/results/human_truth_stage0_worksheet.json"
OUTPUT = ROOT / "eval/results/stage0_replay_results.json"

QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
INDEX = ROOT / "cache/policy_index.json"
SEMANTIC_INDEX = ROOT / "cache/semantic_index.json"
SEMANTIC_VECTORS = ROOT / "cache/semantic_index.npy"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
VALIDATION_RESULTS = ROOT / "eval/results/validation_v1_results.json"
LLM_CACHE = ROOT / "cache/validation_v1_llm_cache.json"
V3_QUERIES = ROOT / "eval/broad_queries_v3_adjudicated.json"

BUDGET_GRID = tuple(range(500, 6001, 250))
NO_ROUTER_DEFAULTS = {"initial_k": 5, "max_k": 20, "max_evidence_tokens": 6000,
                      "max_score_drop": 3.0}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_query(query: str) -> str:
    """Frozen query-structure-router-v1 (mirrors eval/query_aware_router_v1.json)."""
    import re
    interrogative = re.compile(r"\b(what|where|when|which|who|whom|whose|how|why)\b", re.I)
    list_markers = re.compile(r"(^|\n)\s*([-*\u2022]|\d+[.)])\s")
    andor = re.compile(r"\b(and|or)\b", re.I)
    q = " ".join(query.split())
    broad = (q.count("?") >= 2
             or len(interrogative.findall(q)) >= 2
             or bool(list_markers.search(q)) or ";" in q
             or (q.count(",") >= 2 and bool(andor.search(q)))
             or len(q.split()) > 35)
    return "BROAD" if broad else "SIMPLE"


def no_router_adaptive_rows(rows: list[dict], *, initial_k: int = 5, max_k: int = 20,
                            max_evidence_tokens: int = 6000,
                            max_score_drop: float = 3.0) -> list[dict]:
    """Evidence-side score-gap prefix (frozen arms definition A1_NO_ROUTER_ADAPTIVE)."""
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


def prefix_rows(rows: list[dict], budget: int, max_k: int = 20) -> list[dict]:
    selected, used = [], 0
    for row in rows[:max_k]:
        if used + row["tokens"] > budget:
            break
        selected.append(row)
        used += row["tokens"]
    return selected


def context_metrics(selected_ids: list[str], fact_ids: list[str],
                    support: dict[str, list[str]], rows: list[dict]) -> dict:
    selected = set(selected_ids)
    covered = [fact_id for fact_id in fact_ids
               if any(chunk_id in selected for chunk_id in support[fact_id])]
    tokens = sum(row["tokens"] for row in rows if row["chunk_id"] in selected)
    return {"covered": len(covered), "required": len(fact_ids),
            "coverage": len(covered) / len(fact_ids) if fact_ids else None,
            "full": len(covered) == len(fact_ids), "evidence_tokens": tokens,
            "chunks": len(selected_ids), "covered_fact_ids": covered}


def _items(rows: list[dict], chunk_meta: dict) -> list[SimpleNamespace]:
    items = []
    for row in rows:
        chunk = chunk_meta[row["chunk_id"]]
        items.append(SimpleNamespace(
            reranker_score=row["bge_score"], chunk_id=row["chunk_id"],
            text=chunk["text"], title=chunk["title"],
            heading_path=tuple(chunk.get("heading_path") or ()),
            source_path=chunk["source_path"], token_count=row["tokens"]))
    return items


def select_policy(policy_id: str, case_id: str, query: str, rows: list[dict],
                  chunk_meta: dict, vectors: dict[str, np.ndarray]) -> list[str]:
    """Return selected chunk IDs for one frozen policy (reference replay implementation)."""
    from src.evidence_budget import EvidenceBudgetConfig, select_evidence_prefix
    from src.evidence_selector import CoverageSelectorConfig, select_evidence_set

    if policy_id == "fixed_top5":
        return [row["chunk_id"] for row in rows[:5]]
    items = _items(rows, chunk_meta)
    if policy_id == "adaptive_prefix_v1":
        decision = select_evidence_prefix(query, items, config=EvidenceBudgetConfig(),
                                          token_count=lambda item: item.token_count)
        return [row["chunk_id"] for row in rows[:decision.selected_k]]
    if policy_id == "coverage_selector_v2":
        decision = select_evidence_set(
            query, items, vectors=vectors, config=CoverageSelectorConfig(),
            token_count=lambda item: item.token_count)
        return [rows[index]["chunk_id"] for index in decision.selected_indices]
    if policy_id == "no_router_adaptive_v1":
        return [row["chunk_id"] for row in no_router_adaptive_rows(rows, **NO_ROUTER_DEFAULTS)]
    if policy_id == "query_router_v1":
        if route_query(query) == "SIMPLE":
            return [row["chunk_id"] for row in rows[:5]]
        decision = select_evidence_prefix(query, items, config=EvidenceBudgetConfig(),
                                          token_count=lambda item: item.token_count)
        return [row["chunk_id"] for row in rows[:decision.selected_k]]
    raise ValueError(f"unknown policy: {policy_id}")


def load_semantic_vectors() -> tuple[dict[str, np.ndarray], dict]:
    index = _json(SEMANTIC_INDEX)
    matrix = np.load(SEMANTIC_VECTORS)
    if matrix.shape[0] != len(index["chunks"]):
        raise ValueError("semantic vectors and index chunks disagree")
    vectors = {chunk["chunk_id"]: matrix[position]
               for position, chunk in enumerate(index["chunks"])}
    return vectors, index


def _load_context():
    config = _json(CONFIG)
    router = _json(ROUTER)
    arms = _json(ARMS)
    orders = _json(ORDERS)["cases"]
    queries = _json(QUERIES)
    rubric = _json(RUBRIC)
    index = _json(INDEX)
    transfer = _json(TRANSFER)
    utilization = _json(UTILIZATION)
    from eval.run_validation import direct_support_map
    support = direct_support_map(rubric, index["chunks"])
    case_facts = {case["case_id"]: [fact["fact_id"] for fact in case["facts"]]
                  for case in rubric["cases"]}
    query_map = {case["case_id"]: case["query"] for case in queries["cases"]}
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in index["chunks"]}
    return {"config": config, "router": router, "arms": arms, "orders": orders,
            "queries": queries, "rubric": rubric, "index": index, "transfer": transfer,
            "utilization": utilization, "support": support, "case_facts": case_facts,
            "query_map": query_map, "chunk_meta": chunk_meta}


# --------------------------------------------------------------------------- #
# Audits
# --------------------------------------------------------------------------- #

def audit_hashes(config: dict) -> dict:
    mismatches, missing = [], []
    for relative, expected in config["artifact_hashes"].items():
        path = ROOT / relative
        if not path.exists():
            missing.append(relative)
        elif _sha256(path) != expected:
            mismatches.append(relative)
    return {"checked": len(config["artifact_hashes"]), "mismatches": mismatches,
            "missing": missing}


def audit_a0_bge(context: dict) -> dict:
    orders, transfer, utilization = context["orders"], context["transfer"], context["utilization"]
    id_mismatches, token_mismatches, coverage_mismatches = [], [], []
    for row in transfer["cases"]:
        case_id = row["case_id"]
        stored = row["arms"]["bge_top5"]
        top = orders[case_id][:5]
        recomputed_ids = [item["chunk_id"] for item in top]
        if stored["selected_chunk_ids"] != recomputed_ids:
            id_mismatches.append(case_id)
        recomputed_tokens = sum(item["tokens"] for item in top)
        if stored["evidence_tokens"] != recomputed_tokens:
            token_mismatches.append(case_id)
        metrics = context_metrics(recomputed_ids, context["case_facts"][case_id],
                                  context["support"], top)
        if sorted(stored["available_fact_ids"]) != sorted(metrics["covered_fact_ids"]):
            coverage_mismatches.append(case_id)
    summary = transfer["summaries"]["bge_top5"]
    replay_tokens = sum(sum(item["tokens"] for item in orders[case["case_id"]][:5])
                        for case in transfer["cases"])
    replay_full = sum(1 for case in transfer["cases"]
                      if context_metrics([item["chunk_id"] for item in orders[case["case_id"]][:5]],
                                         context["case_facts"][case["case_id"]],
                                         context["support"], orders[case["case_id"]][:5])["full"])
    ab = _json(ROOT / "eval/results/reranker_ab_analysis.json")
    ab_full_at5 = sum(1 for case in ab["challenger"]["per_case"].values()
                      if case.get("fact_complete@5"))
    utilization_row = utilization["cases"][0]["arms"]["baseline"]
    utilization_replay_id_mismatches = []
    for row in utilization["cases"]:
        if row["status"] != "complete":
            continue
        stored_ids = row["arms"]["baseline"]["selected_chunk_ids"]
        recomputed_ids = [item["chunk_id"] for item in orders[row["case_id"]][:5]]
        if stored_ids != recomputed_ids:
            utilization_replay_id_mismatches.append(row["case_id"])
    return {
        "transfer_cases": len(transfer["cases"]),
        "selected_id_mismatches": id_mismatches,
        "evidence_token_mismatches": token_mismatches,
        "available_fact_mismatches": coverage_mismatches,
        "summary_evidence_tokens": {"stored": summary["evidence_tokens"],
                                    "replayed": replay_tokens},
        "context_full_cases": {"replayed": replay_full, "ab_challenger_fact_complete_at_5": ab_full_at5,
                               "comparable": replay_full == ab_full_at5},
        "stored_answer_level_grounded_complete_cases": summary["grounded_complete_cases"],
        "utilization_case_id_mismatches": utilization_replay_id_mismatches,
    }


def audit_provider_accounting(context: dict) -> dict:
    cache = _json(LLM_CACHE)
    checks = {"transfer_generation_keys_missing": 0,
              "transfer_provider_usage_missing": 0,
              "transfer_cache_usage_mismatch": 0,
              "utilization_generation_keys_missing": 0,
              "utilization_provider_usage_missing": 0,
              "utilization_cache_usage_mismatch": 0}
    transfer_totals = Counter()
    utilization_totals = Counter()
    for row in context["transfer"]["cases"]:
        for arm in ("minilm_top5", "bge_top5"):
            entry = row["arms"][arm]
            usage = entry.get("provider_usage") or {}
            if entry.get("generation_key") not in cache:
                checks["transfer_generation_keys_missing"] += 1
                continue
            cached = cache[entry["generation_key"]]
            if not isinstance(usage.get("input_tokens"), int) or not isinstance(
                    usage.get("output_tokens"), int):
                checks["transfer_provider_usage_missing"] += 1
                continue
            cached_usage = cached.get("provider_usage") or {}
            if (cached_usage.get("input_tokens"), cached_usage.get("output_tokens")) != (
                    usage["input_tokens"], usage["output_tokens"]):
                checks["transfer_cache_usage_mismatch"] += 1
            if arm == "bge_top5":
                transfer_totals["input_tokens"] += usage["input_tokens"]
                transfer_totals["output_tokens"] += usage["output_tokens"]
                transfer_totals["calls"] += 1
    for row in context["utilization"]["cases"]:
        if row["status"] != "complete":
            continue
        for arm in ("baseline", "coverage_aware"):
            entry = row["arms"][arm]
            usage = entry.get("provider_usage") or {}
            if entry.get("generation_key") not in cache:
                checks["utilization_generation_keys_missing"] += 1
                continue
            cached = cache[entry["generation_key"]]
            if not isinstance(usage.get("input_tokens"), int) or not isinstance(
                    usage.get("output_tokens"), int):
                checks["utilization_provider_usage_missing"] += 1
                continue
            cached_usage = cached.get("provider_usage") or {}
            if (cached_usage.get("input_tokens"), cached_usage.get("output_tokens")) != (
                    usage["input_tokens"], usage["output_tokens"]):
                checks["utilization_cache_usage_mismatch"] += 1
            if arm == "baseline":
                utilization_totals["input_tokens"] += usage["input_tokens"]
                utilization_totals["output_tokens"] += usage["output_tokens"]
                utilization_totals["calls"] += 1
    return {
        "checks": checks,
        "a0_bge_provider_totals_50_cases": dict(transfer_totals),
        "utilization_baseline_provider_totals_46_cases": dict(utilization_totals),
        "rewrite_calls_in_frozen_replay": 0,
        "rewrite_note": ("The frozen transfer/utilization artifacts used prepared single-turn "
                         "queries with no rewrite call; production rewrite cost must be counted "
                         "separately in Stage 1 economics."),
        "latency_note": ("Frozen artifacts do not store per-call latency; Stage 1 must record "
                         "latency p50/p95 from the live pipeline (trace.latency_seconds)."),
    }


def replay_policies(context: dict) -> dict:
    vectors, _ = load_semantic_vectors()
    policies = [arm["policy_id"] for arm in context["arms"]["arms"]]
    per_case, table = {}, {}
    for policy in policies:
        covered_total = required_total = full_count = tokens_total = chunks_total = 0
        changed = []
        per_case[policy] = {}
        for case in context["queries"]["cases"]:
            case_id = case["case_id"]
            rows = context["orders"][case_id]
            selected = select_policy(policy, case_id, case["query"], rows,
                                     context["chunk_meta"], vectors)
            metrics = context_metrics(selected, context["case_facts"][case_id],
                                      context["support"], rows)
            per_case[policy][case_id] = {
                "selected_chunk_ids": selected, "coverage": metrics["coverage"],
                "full": metrics["full"], "evidence_tokens": metrics["evidence_tokens"],
                "chunks": metrics["chunks"], "route": route_query(case["query"]),
            }
            covered_total += metrics["covered"]
            required_total += metrics["required"]
            full_count += int(metrics["full"])
            tokens_total += metrics["evidence_tokens"]
            chunks_total += metrics["chunks"]
            base_ids = [item["chunk_id"] for item in rows[:5]]
            if selected != base_ids:
                changed.append(case_id)
        table[policy] = {
            "mean_coverage": covered_total / required_total if required_total else None,
            "full_cases": full_count, "cases": len(context["queries"]["cases"]),
            "total_evidence_tokens": tokens_total,
            "mean_evidence_tokens": tokens_total / len(context["queries"]["cases"]),
            "mean_chunks": chunks_total / len(context["queries"]["cases"]),
            "changed_cases_vs_A0": changed,
        }
    return {"table": table, "per_case": per_case}


def budget_sweep(context: dict) -> dict:
    result = {}
    for route in ("SIMPLE", "BROAD"):
        case_ids = [case["case_id"] for case in context["queries"]["cases"]
                    if route_query(case["query"]) == route]
        curve = []
        for budget in BUDGET_GRID:
            covered = required = full = tokens = 0
            for case_id in case_ids:
                rows = context["orders"][case_id]
                selected = prefix_rows(rows, budget)
                metrics = context_metrics([row["chunk_id"] for row in selected],
                                          context["case_facts"][case_id],
                                          context["support"], rows)
                covered += metrics["covered"]
                required += metrics["required"]
                full += int(metrics["full"])
                tokens += metrics["evidence_tokens"]
            curve.append({"budget": budget, "cases": len(case_ids),
                          "mean_coverage": covered / required if required else None,
                          "full_cases": full,
                          "total_evidence_tokens": tokens})
        best_full = max(point["full_cases"] for point in curve)
        candidates = [point["budget"] for point in curve if point["full_cases"] == best_full]
        reference = min(candidates) if candidates else BUDGET_GRID[-1]
        result[route] = {"curve": curve, "best_full_cases": best_full,
                         "reference_budget": reference,
                         "reference_budget_rule": ("smallest grid budget reaching the best FULL "
                                                   "count for this route (diagnostic only)")}
    return result


def audit_route_sets(context: dict) -> dict:
    labels = {case["case_id"]: route_query(case["query"])
              for case in context["queries"]["cases"]}
    stored = context["router"]["distribution"]["validation_v1_50"]["labels"]
    v3 = _json(V3_QUERIES)["cases"]
    v3_labels = {case["case_id"]: route_query(case["query"]) for case in v3}
    stored_v3 = context["router"]["distribution"]["broad_v3_16"]["labels"]
    worksheet = _json(WORKSHEET)
    simple_ids = sorted(cid for cid, label in labels.items() if label == "SIMPLE")
    step = max(1, len(simple_ids) // 8)
    sentinel = [simple_ids[min(len(simple_ids) - 1, index)]
                for index in range(0, len(simple_ids), step)][:8]
    return {"v1_labels_match_router": labels == stored,
            "v3_labels_match_router": v3_labels == stored_v3,
            "v1_counts": dict(Counter(labels.values())),
            "v3_counts": dict(Counter(v3_labels.values())),
            "sentinel_queries": sentinel,
            "sentinel_match_worksheet": sentinel == worksheet["sentinel_queries"],
            "worksheet_counts": worksheet["counts"],
            "worksheet_status": worksheet["status"]}


def run() -> dict:
    context = _load_context()
    hashes = audit_hashes(context["config"])
    a0 = audit_a0_bge(context)
    policies = replay_policies(context)
    provider = audit_provider_accounting(context)
    sweep = budget_sweep(context)
    routes = audit_route_sets(context)
    a0_clean = (not a0["selected_id_mismatches"] and not a0["evidence_token_mismatches"]
                and not a0["available_fact_mismatches"]
                and not a0["utilization_case_id_mismatches"]
                and a0["summary_evidence_tokens"]["stored"] == a0["summary_evidence_tokens"]["replayed"]
                and a0["context_full_cases"]["comparable"])
    accounting_clean = all(value == 0 for value in provider["checks"].values())
    gates = {
        "a0_bge_config_explicit": True,
        "frozen_artifacts_replayable": a0_clean,
        "artifact_hashes_verified": not hashes["mismatches"] and not hashes["missing"],
        "token_accounting_reliable": accounting_clean,
        "human_adjudication_rules_frozen": (ROOT / "eval/human_truth_contract_v1.md").exists(),
        "economics_contract_frozen": (ROOT / "eval/economics_contract_v1.md").exists(),
        "router_rule_frozen": context["router"]["status"] == "frozen",
        "arms_definition_frozen": context["arms"]["status"] == "frozen_before_stage1",
        "human_verdicts_pending": _json(WORKSHEET)["status"] != "frozen_human_verdicts",
    }
    return {
        "schema_version": 1,
        "version": "query-aware-stage0-replay-v1",
        "status": "complete",
        "hashes": hashes,
        "a0_bge_reproduction": a0,
        "policy_context_table": policies["table"],
        "policy_per_case": policies["per_case"],
        "route_distribution": routes,
        "budget_sweep": sweep,
        "provider_accounting": provider,
        "gates": gates,
        "artifact_hashes": {
            "eval/query_aware_stage0_config.json": _sha256(CONFIG),
            "eval/query_aware_router_v1.json": _sha256(ROUTER),
            "eval/query_aware_arms_v1.json": _sha256(ARMS),
            "eval/results/a0_bge_rerank_orders.json": _sha256(ORDERS),
            "eval/results/human_truth_stage0_worksheet.json": _sha256(WORKSHEET),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="offline replay only; no API call is ever made")
    args = parser.parse_args(argv)
    document = run()
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: document[key] for key in
                      ("hashes", "a0_bge_reproduction", "policy_context_table",
                       "route_distribution", "budget_sweep", "provider_accounting", "gates")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
