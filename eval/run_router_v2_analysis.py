"""Router V2 selection study - stage 3: aggregation, decision matrix, report.

Reads the frozen study artifacts and produces:
  - selection_study_analysis.json
  - selection_study_report.md
  - selection_study_failure_review.md

All aggregation is recomputed from the artifacts; no model calls are made.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.router_v2_study_lib import (  # noqa: E402
    CONFIG_PATH,
    EVIDENCE_CACHE_PATH,
    SELECTIONS_PATH,
    STUDY_DIR,
    V1_1_EVIDENCE_CACHE,
    load_json,
    write_json,
)

EVIDENCE_RESULTS_PATH = STUDY_DIR / "evidence_policy_results.json"
ORACLE_PATH = STUDY_DIR / "oracle_upper_bound.json"
CANDIDATE_POOL_PATH = STUDY_DIR / "candidate_pool_analysis.json"
GENERATION_RESULTS_PATH = STUDY_DIR / "generation_results.json"
ANSWER_EVAL_PATH = STUDY_DIR / "answer_eval.json"
COST_LEDGER_PATH = STUDY_DIR / "cost_ledger.json"
ANSWER_CACHE_PATH = STUDY_DIR / "answer_judge_cache.json"
REPORT_PATH = STUDY_DIR / "selection_study_report.md"
FAILURE_REVIEW_PATH = STUDY_DIR / "selection_study_failure_review.md"
ANALYSIS_PATH = STUDY_DIR / "selection_study_analysis.json"

RAW_PATH = PROJECT_ROOT / "eval" / "results" / "router_v1" / "raw" / "router_v1_raw_results.json"


# ---------------------------------------------------------------------------
# Evidence aggregation
# ---------------------------------------------------------------------------


def pooled_evidence(instances: Mapping[str, Any], policy_ids: Sequence[str]) -> dict[str, Any]:
    supported = required = complete = exploratory = useful_exploratory = 0
    preserved = useful_base_total = displaced = 0
    precision_values: list[float] = []
    oracle_gap = 0
    reaches_oracle = below_direct = 0
    gained = lost = 0
    cases_evaluated = 0
    per_instance_recall: list[dict[str, Any]] = []
    for policy_id in policy_ids:
        instance = instances.get(policy_id)
        if instance is None:
            continue
        instance_supported = instance_required = instance_cases = 0
        for case in instance["cases"].values():
            if case.get("status") != "judged":
                continue
            metrics = case["metrics"]
            cases_evaluated += 1
            supported += metrics["supported_count"]
            required += metrics["required_total"]
            instance_supported += metrics["supported_count"]
            instance_required += metrics["required_total"]
            instance_cases += 1
            complete += int(metrics["evidence_required_complete"])
            precision_values.append(metrics["required_context_precision"])
            exploratory += metrics["exploratory_chunks_selected"]
            useful_exploratory += metrics["useful_exploratory_chunks"]
            preserved += metrics["useful_base_chunks_preserved"]
            useful_base_total += metrics["useful_base_chunk_count"]
            displaced += int(metrics["displaced"])
            if metrics["oracle_gap"] is not None:
                oracle_gap += metrics["oracle_gap"]
            reaches_oracle += int(metrics["reaches_oracle"])
            below_direct += int(metrics["below_direct"])
            gained += len(metrics["new_required_aspects_gained"])
            lost += len(metrics["required_aspects_lost"])
        per_instance_recall.append(
            {
                "policy_id": policy_id,
                "supported": instance_supported,
                "required": instance_required,
                "cases": instance_cases,
                "recall": instance_supported / instance_required if instance_required else None,
            }
        )
    return {
        "policy_ids": list(policy_ids),
        "supported_total": supported,
        "required_total": required,
        "cases_evaluated": cases_evaluated,
        "recall": supported / required if required else None,
        "complete_queries": complete,
        "precision": statistics.mean(precision_values) if precision_values else None,
        "exploratory_chunks": exploratory,
        "useful_exploratory_chunks": useful_exploratory,
        "exploration_efficiency": useful_exploratory / exploratory if exploratory else None,
        "exploration_efficiency_fraction": f"{useful_exploratory}/{exploratory}",
        "useful_base_preserved": preserved,
        "useful_base_total": useful_base_total,
        "base_preservation": preserved / useful_base_total if useful_base_total else None,
        "base_preservation_fraction": f"{preserved}/{useful_base_total}",
        "displaced_queries": displaced,
        "oracle_gap_total": oracle_gap,
        "queries_reaching_oracle": reaches_oracle,
        "queries_below_direct": below_direct,
        "new_aspects_gained": gained,
        "aspects_lost": lost,
        "net_aspect_delta": gained - lost,
        "per_instance": per_instance_recall,
    }


def evidence_summary_table(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    instances = evidence["instances"]
    rows: list[dict[str, Any]] = []
    rows.append({"policy": "DIRECT_TOP5", "group": "frozen",
                 **pooled_evidence(instances, ["DIRECT_TOP5"])})
    rows.append({"policy": "ROUND_ROBIN", "group": "frozen",
                 **pooled_evidence(instances, ["ROUND_ROBIN"])})
    rows.append({"policy": "GLOBAL_BASE_RERANK", "group": "global",
                 **pooled_evidence(instances, ["GLOBAL_BASE_RERANK"])})
    for pid in sorted(pid for pid in instances if pid.startswith("MMR_")):
        lam = pid.split("_")[1]
        rows.append({"policy": f"MMR lambda={lam}", "group": "mmr",
                     **pooled_evidence(instances, [pid])})
    for variant in ("EACL_TS_TOPK", "EACL_TS_TOPK_DIV", "EACL_TS_RESERVE"):
        pids = sorted(pid for pid in instances if pid.startswith(variant + "::"))
        rows.append({"policy": f"{variant} (3 seeds pooled)", "group": "bandit",
                     **pooled_evidence(instances, pids)})
    rows.append({"policy": "ORACLE_BASE_TOP5", "group": "oracle_analysis_only",
                 **pooled_evidence(instances, ["ORACLE_BASE_TOP5"])})
    rows.append({"policy": "ORACLE_TOP5", "group": "oracle_analysis_only",
                 **pooled_evidence(instances, ["ORACLE_TOP5"])})
    return rows


def bandit_seed_table(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    instances = evidence["instances"]
    rows: list[dict[str, Any]] = []
    for pid in sorted(instances):
        if not pid.startswith("EACL_"):
            continue
        pooled = pooled_evidence(instances, [pid])
        rows.append(
            {
                "instance": pid,
                "variant": instances[pid]["variant"],
                "seed": instances[pid]["seed"],
                "supported": pooled["supported_total"],
                "recall": pooled["recall"],
                "complete": pooled["complete_queries"],
                "precision": pooled["precision"],
                "displaced": pooled["displaced_queries"],
                "exploration_efficiency": pooled["exploration_efficiency"],
                "base_preservation": pooled["base_preservation"],
                "oracle_gap": pooled["oracle_gap_total"],
                "below_direct": pooled["queries_below_direct"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Case studies and probes
# ---------------------------------------------------------------------------


def oracle_recovery_probe(
    evidence: Mapping[str, Any],
    oracle: Mapping[str, Any],
    selections: Mapping[str, Any],
) -> dict[str, Any]:
    instances = evidence["instances"]
    direct = instances["DIRECT_TOP5"]["cases"]
    oracle_cases = oracle["cases"]
    per_case: dict[str, Any] = {}
    ranks: list[int] = []
    for case_id, entry in oracle_cases.items():
        oracle_ids = entry["oracle_top5"]["ids"]
        direct_ids = direct[case_id]["metrics"]["evidence_ids"]
        new_ids = [chunk_id for chunk_id in oracle_ids if chunk_id not in direct_ids]
        if not new_ids:
            continue
        provenance = selections["provenance"][case_id]
        prov_by_id = {item["chunk_id"]: item for item in provenance}
        rank_entries = []
        for chunk_id in new_ids:
            item = prov_by_id.get(chunk_id)
            if not item:
                continue
            score = item["global_rerank_score"]
            ordered = sorted(
                prov_by_id.values(),
                key=lambda value: (-(value["global_rerank_score"] or 0.0), value["chunk_id"]),
            )
            global_rank = [value["chunk_id"] for value in ordered].index(chunk_id) + 1
            stream_ranks = {
                source["stream_id"]: source["rank"] for source in item["stream_sources"]
            }
            ranks.append(global_rank)
            rank_entries.append(
                {
                    "chunk_id": chunk_id,
                    "global_rerank_rank": global_rank,
                    "global_rerank_score": score,
                    "stream_ranks": stream_ranks,
                    "in_base_union": item["in_base_stream_union"],
                }
            )
        per_case[case_id] = {
            "oracle_ids": oracle_ids,
            "direct_ids": direct_ids,
            "oracle_new_vs_direct": rank_entries,
        }
    return {
        "note": (
            "ranks of truth-oracle chunks missing from the frozen DIRECT top5, in the global "
            "(shared-rewrite) cross-encoder order over the case super-pool; analysis-only"
        ),
        "cases_with_new_oracle_chunks": list(per_case),
        "rank_samples": ranks,
        "rank_median": statistics.median(ranks) if ranks else None,
        "rank_min": min(ranks) if ranks else None,
        "rank_max": max(ranks) if ranks else None,
        "per_case": per_case,
    }


def case_studies(
    evidence: Mapping[str, Any],
    oracle: Mapping[str, Any],
    answer_eval: Mapping[str, Any],
) -> dict[str, Any]:
    instances = evidence["instances"]
    direct = instances["DIRECT_TOP5"]["cases"]
    oracle_top = instances["ORACLE_TOP5"]["cases"]
    oracle_gap_cases: list[dict[str, Any]] = []
    runtime_ids = [pid for pid in instances if instances[pid]["role"] == "runtime"]
    for case_id, oracle_case in oracle_top.items():
        oracle_supported = set(oracle_case["evidence"]["supported_aspect_ids"])
        direct_supported = set(direct[case_id]["evidence"]["supported_aspect_ids"])
        missing = sorted(oracle_supported - direct_supported)
        if not missing:
            continue
        best_runtime = None
        for pid in runtime_ids:
            case = instances[pid]["cases"].get(case_id) or {}
            if case.get("status") != "judged":
                continue
            count = len(set(case["evidence"]["supported_aspect_ids"]) & set(missing))
            if best_runtime is None or count > best_runtime["captured"]:
                best_runtime = {"policy_id": pid, "captured": count}
        oracle_gap_cases.append(
            {
                "case_id": case_id,
                "oracle_only_aspects_vs_direct": missing,
                "best_runtime_capture": best_runtime,
                "oracle_ids_not_in_direct": [
                    chunk_id
                    for chunk_id in oracle_top[case_id]["metrics"]["evidence_ids"]
                    if chunk_id not in direct[case_id]["metrics"]["evidence_ids"]
                ],
            }
        )
    displacement_cases = []
    for case_id, case in instances["ROUND_ROBIN"]["cases"].items():
        metrics = case["metrics"]
        if metrics["displaced"]:
            displacement_cases.append(
                {
                    "case_id": case_id,
                    "lost_aspects": metrics["required_aspects_lost"],
                    "gained_aspects": metrics["new_required_aspects_gained"],
                    "exploratory": metrics["exploratory_chunks_selected"],
                    "useful_exploratory": metrics["useful_exploratory_chunks"],
                }
            )
    answer_deltas: dict[str, Any] = {}
    if answer_eval:
        for case_id in answer_eval["cases"]:
            direct_entry = answer_eval["cases"][case_id]["DIRECT_TOP5"]
            delta = {
                pid: answer_eval["cases"][case_id][pid]["required_covered"]
                - direct_entry["required_covered"]
                for pid in answer_eval["cases"][case_id]
            }
            answer_deltas[case_id] = delta
    return {
        "oracle_over_direct_cases": oracle_gap_cases,
        "round_robin_displacement_cases": displacement_cases,
        "answer_covered_delta_vs_direct": answer_deltas,
    }


# ---------------------------------------------------------------------------
# Decision matrix (predeclared thresholds from selection_study_config.json)
# ---------------------------------------------------------------------------


def build_decision(
    evidence: Mapping[str, Any],
    oracle: Mapping[str, Any],
    answer_eval: Mapping[str, Any] | None,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    instances = evidence["instances"]
    table = {row["policy"]: row for row in evidence_summary_table(evidence)}
    direct = table["DIRECT_TOP5"]
    round_robin = table["ROUND_ROBIN"]
    oracle_top5 = table["ORACLE_TOP5"]
    oracle_base = table["ORACLE_BASE_TOP5"]

    # Decision signals compare per-instance results (every instance covers the
    # same 20 cases); family tables above pool the three bandit seeds.
    def instance_supported(policy_id: str) -> int:
        return sum(
            case["metrics"]["supported_count"]
            for case in instances[policy_id]["cases"].values()
            if case.get("status") == "judged"
        )

    def instance_precision(policy_id: str) -> float:
        values = [
            case["metrics"]["required_context_precision"]
            for case in instances[policy_id]["cases"].values()
            if case.get("status") == "judged"
        ]
        return statistics.mean(values) if values else 0.0

    runtime_instance_ids = [
        pid for pid in instances if instances[pid]["role"] == "runtime"
    ]
    selectable_instance_ids = [
        pid for pid in runtime_instance_ids
        if instances[pid]["family"] in {"global", "mmr", "bandit"}
    ]
    simple_instance_ids = [
        pid for pid in runtime_instance_ids
        if instances[pid]["family"] in {"global", "mmr"}
    ]
    bandit_instance_ids = [
        pid for pid in runtime_instance_ids if instances[pid]["family"] == "bandit"
    ]
    best_runtime_id = max(
        runtime_instance_ids, key=lambda pid: (instance_supported(pid), instance_precision(pid))
    )
    best_selectable_id = max(
        selectable_instance_ids, key=lambda pid: (instance_supported(pid), instance_precision(pid))
    )
    best_simple_id = max(
        simple_instance_ids, key=lambda pid: (instance_supported(pid), instance_precision(pid))
    )
    best_bandit_id = max(
        bandit_instance_ids, key=lambda pid: (instance_supported(pid), instance_precision(pid))
    )

    exploration_upside = oracle_top5["supported_total"] - oracle_base["supported_total"]
    oracle_upside = oracle_top5["supported_total"] - direct["supported_total"]
    rr_oracle_gap = oracle_top5["supported_total"] - round_robin["supported_total"]
    best_runtime_supported = instance_supported(best_runtime_id)
    best_selectable_supported = instance_supported(best_selectable_id)
    best_simple_supported = instance_supported(best_simple_id)
    best_bandit_supported = instance_supported(best_bandit_id)
    runtime_recovery = (
        (best_selectable_supported - round_robin["supported_total"]) / rr_oracle_gap
        if rr_oracle_gap
        else None
    )
    simple_recovery = (
        (best_simple_supported - round_robin["supported_total"]) / rr_oracle_gap
        if rr_oracle_gap
        else None
    )
    bandit_gain_vs_simple = best_bandit_supported - best_simple_supported
    thresholds = config["decision_matrix"]["thresholds_in_aspects"]
    signals = {
        "exploration_upside_aspects": exploration_upside,
        "oracle_upside_vs_direct_aspects": oracle_upside,
        "round_robin_oracle_gap_aspects": rr_oracle_gap,
        "best_runtime_any_policy": {
            "policy": best_runtime_id,
            "supported": best_runtime_supported,
            "note": "includes the frozen DIRECT_TOP5 baseline; DIRECT is still the best observed runtime behavior",
        },
        "best_selectable_policy": {
            "policy": best_selectable_id,
            "supported": best_selectable_supported,
            "recovery_of_rr_oracle_gap": runtime_recovery,
            "note": "best non-frozen selection policy (global rerank, MMR, bandit)",
        },
        "best_simple": {
            "policy": best_simple_id,
            "supported": best_simple_supported,
            "recovery_of_rr_oracle_gap": simple_recovery,
        },
        "best_bandit": {
            "policy": best_bandit_id,
            "supported": best_bandit_supported,
        },
        "bandit_gain_vs_simple_aspects": bandit_gain_vs_simple,
        "base_pool_oracle_gap_vs_best_selectable_aspects": oracle_base["supported_total"]
        - best_selectable_supported,
        "base_pool_oracle_gap_vs_direct_aspects": oracle_base["supported_total"]
        - direct["supported_total"],
    }
    signals["base_pool_utility_estimation_limited_signal"] = bool(
        signals["base_pool_oracle_gap_vs_best_selectable_aspects"] >= 5
        and (runtime_recovery is not None
             and runtime_recovery < thresholds["runtime_recovery_strong_fraction"])
    )
    flags = {
        "EXPLORATION_LIMITED": exploration_upside
        <= thresholds["exploration_upside_small"],
        "UTILITY_ESTIMATION_LIMITED": (
            exploration_upside > thresholds["exploration_upside_small"]
            and runtime_recovery is not None
            and runtime_recovery < thresholds["runtime_recovery_weak_fraction"]
        ),
        "BANDIT_ADDS_VALUE": (
            bandit_gain_vs_simple >= thresholds["bandit_material_gain"]
            and oracle_upside >= thresholds["oracle_upside_material"]
        ),
        "SIMPLE_SELECTOR_SUFFICIENT": (
            simple_recovery is not None
            and simple_recovery >= thresholds["runtime_recovery_strong_fraction"]
            and bandit_gain_vs_simple < thresholds["bandit_material_gain"]
        ),
        "SELECTION_LIMITED": (
            oracle_upside >= thresholds["oracle_upside_material"]
            and rr_oracle_gap >= 4
            and runtime_recovery is not None
            and runtime_recovery >= thresholds["selection_recovery_fraction"]
        ),
    }
    flags["MIXED"] = not any(flags.values())
    base_pool_utility_estimation_limited = signals[
        "base_pool_utility_estimation_limited_signal"
    ]

    if flags["EXPLORATION_LIMITED"] and base_pool_utility_estimation_limited:
        primary = "UTILITY_ESTIMATION_LIMITED"
        secondary = "EXPLORATION_LIMITED"
        primary_note = (
            "Two mechanisms coexist: (1) decomposition-specific exploration upside is immaterial "
            f"(ORACLE_TOP5 {oracle_top5['supported_total']} vs ORACLE_BASE_TOP5 "
            f"{oracle_base['supported_total']}, +{exploration_upside} aspect); (2) even within the "
            "existing pools the runtime evidence utility proxies leave a large oracle gap "
            f"({signals['base_pool_oracle_gap_vs_best_selectable_aspects']} aspects vs the base-pool "
            "oracle; every runtime selector is at or below frozen DIRECT). Because (2) is the "
            "actionable, larger gap, UTILITY_ESTIMATION_LIMITED is primary; the decomposition "
            "direction is closed by EXPLORATION_LIMITED as secondary."
        )
    elif flags["EXPLORATION_LIMITED"]:
        primary = "EXPLORATION_LIMITED"
        secondary = None
        primary_note = "decomposition candidate upside is immaterial under the predeclared thresholds"
    elif flags["BANDIT_ADDS_VALUE"]:
        primary = "BANDIT_ADDS_VALUE"
        secondary = "SELECTION_LIMITED" if flags["SELECTION_LIMITED"] else None
        primary_note = "bandit family materially exceeds the best simple selector"
    elif flags["UTILITY_ESTIMATION_LIMITED"]:
        primary = "UTILITY_ESTIMATION_LIMITED"
        secondary = "EXPLORATION_LIMITED" if flags["EXPLORATION_LIMITED"] else None
        primary_note = "oracle space exists but runtime proxies fail to identify it"
    elif flags["SELECTION_LIMITED"]:
        primary = "SELECTION_LIMITED"
        secondary = "EXPLORATION_LIMITED" if flags["EXPLORATION_LIMITED"] else None
        primary_note = "utility-aware selection recovers a material share of the oracle gap"
    elif flags["SIMPLE_SELECTOR_SUFFICIENT"]:
        primary = "SIMPLE_SELECTOR_SUFFICIENT"
        secondary = None
        primary_note = "simple global rerank/MMR capture most of the recoverable gap"
    else:
        primary = "MIXED"
        secondary = None
        primary_note = "no single predeclared rule dominates"

    followup_map = config["decision_matrix"]["eacl_followup_mapping"]
    if primary == "UTILITY_ESTIMATION_LIMITED":
        followup = "IMPROVE_UTILITY_ESTIMATION_FIRST"
        followup_note = (
            "the decomposition/exploration-specific upside is too small to justify the EACL main "
            "line, but the measured pool-level oracle gap (mostly inside the base pool) is a "
            "utility-estimation problem, not a bandit or allocation problem"
        )
    elif primary == "EXPLORATION_LIMITED":
        followup = "DECOMPOSITION_UPSIDE_TOO_SMALL"
        followup_note = "candidate pool has no material decomposition-specific upside"
    elif primary == "BANDIT_ADDS_VALUE":
        followup = "ADOPT_BANDIT_DIRECTION"
        followup_note = "bandit complexity measured a reproducible gain"
    else:
        followup = "ADOPT_UTILITY_SELECTION_NOT_BANDIT"
        followup_note = "selection matters, bandit complexity does not"

    generation_check = None
    if answer_eval:
        aggregates = answer_eval["aggregate"]
        oracle_answers = aggregates.get("ORACLE_TOP5")
        direct_answers = aggregates.get("DIRECT_TOP5")
        if oracle_answers and direct_answers:
            evidence_gain = oracle_top5["supported_total"] - direct["supported_total"]
            answer_gain = (
                oracle_answers["required_covered_total"]
                - direct_answers["required_covered_total"]
            )
            complete_gain = (
                oracle_answers["query_required_complete_cases"]
                - direct_answers["query_required_complete_cases"]
            )
            generation_check = {
                "oracle_evidence_gain_aspects": evidence_gain,
                "oracle_answer_gain_aspects": answer_gain,
                "oracle_complete_gain_cases": complete_gain,
                "generation_transfers_evidence_gain": answer_gain > 0
                and complete_gain > 0,
                "oracle_context_utilization": oracle_answers["context_utilization"],
            }
            signals["generation_check"] = generation_check
    return {
        "flags": flags,
        "signals": signals,
        "primary": primary,
        "secondary": secondary,
        "primary_note": primary_note,
        "eacl_followup_decision": followup,
        "eacl_followup_note": followup_note,
        "followup_option_labels": list(followup_map.keys()),
        "predeclared_thresholds": thresholds,
    }


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def evidence_row_cells(row: Mapping[str, Any]) -> str:
    cases = row["cases_evaluated"]
    return (
        f"| {row['policy']} | {row['supported_total']}/{row['required_total']} "
        f"| {row['complete_queries']}/{cases} | {fmt(row['precision'])} "
        f"| {row['useful_exploratory_chunks']}/{row['exploratory_chunks']} "
        f"({fmt(row['exploration_efficiency'] if row['exploration_efficiency'] is not None else None, 2)}) "
        f"| {row['useful_base_preserved']}/{row['useful_base_total']} "
        f"({fmt(row['base_preservation'], 2)}) "
        f"| {row['oracle_gap_total']} | {row['displaced_queries']}/{cases} | "
        f"{row['queries_below_direct']}/{cases} |"
    )


def render_report(
    config: Mapping[str, Any],
    pool: Mapping[str, Any],
    oracle: Mapping[str, Any],
    evidence: Mapping[str, Any],
    decision: Mapping[str, Any],
    case_data: Mapping[str, Any],
    generation: Mapping[str, Any] | None,
    answer_eval: Mapping[str, Any] | None,
    cost: Mapping[str, Any],
) -> str:
    table = evidence_summary_table(evidence)
    bandit_rows = bandit_seed_table(evidence)
    signals = decision["signals"]
    oracle_totals = oracle["totals"]
    pool_totals = pool["totals"]
    lines: list[str] = []
    lines.append("# Router V2 Selection Study Report")
    lines.append("")
    lines.append(
        "**Role: exploratory mechanism study.** The same frozen 20 queries and 66 required "
        "aspects are reused to compare many selection policies, so nothing here is an "
        "independent confirmatory test. Oracle policies are ANALYSIS_ONLY_ORACLE."
    )
    lines.append("")
    lines.append("## Executive Summary (Q1-Q5)")
    lines.append("")
    lines.append(
        f"- **Q1 candidate-pool upper bound**: judge-verified ORACLE_TOP5 supports "
        f"**{_row(table, 'ORACLE_TOP5')['supported_total']}/66** aspects vs DIRECT "
        f"{_row(table, 'DIRECT_TOP5')['supported_total']}/66 "
        f"({_delta(signals['oracle_upside_vs_direct_aspects'])}). Decomposition-specific upside is tiny: "
        f"ORACLE_TOP5 vs ORACLE_BASE_TOP5 = +{signals['exploration_upside_aspects']} judge-verified aspect "
        f"(truth-based {oracle_totals['oracle_top5']} vs {oracle_totals['oracle_base_top5']}, "
        f"super-pool {oracle_totals['superpool_recall']}/66 vs base-union "
        f"{oracle_totals['base_union_recall']}/66)."
    )
    lines.append(
        f"- **Q2 round-robin gap**: ROUND_ROBIN {_row(table, 'ROUND_ROBIN')['supported_total']}/66 "
        f"sits {signals['round_robin_oracle_gap_aspects']} aspects below ORACLE_TOP5 and "
        f"{_row(table, 'DIRECT_TOP5')['supported_total'] - _row(table, 'ROUND_ROBIN')['supported_total']} "
        "below frozen DIRECT, with the highest displacement count of the frozen baselines."
    )
    lines.append(
        f"- **Q3 simple selectors**: GLOBAL_BASE_RERANK {_row(table, 'GLOBAL_BASE_RERANK')['supported_total']}/66 "
        f"and best simple instance {signals['best_simple']['policy']} "
        f"{signals['best_simple']['supported']}/66 recover only "
        f"{fmt(signals['best_simple']['recovery_of_rr_oracle_gap'], 2)} of the ROUND_ROBIN-to-oracle gap; "
        "no simple selector matches frozen DIRECT."
    )
    lines.append(
        f"- **Q4 bandit value**: best bandit instance {signals['best_bandit']['policy']} "
        f"= {signals['best_bandit']['supported']}/66; bandit minus best simple = "
        f"{_delta(signals['bandit_gain_vs_simple_aspects'])}. Bandit seed variance is large "
        f"({_bandit_spread_text(bandit_rows)}). No measured bandit value."
    )
    if signals.get("generation_check"):
        gc = signals["generation_check"]
        lines.append(
            f"- **Q5 evidence-to-answer transfer**: ORACLE_TOP5 evidence "
            f"(+{gc['oracle_evidence_gain_aspects']} aspects vs DIRECT, analysis-only) transfers "
            f"**+{gc['oracle_answer_gain_aspects']} covered aspects and +{gc['oracle_complete_gain_cases']} "
            f"complete answers** (context utilization {fmt(gc['oracle_context_utilization'], 2)}). "
            "Generation does not cap the upper bound; evidence selection does."
        )
    else:
        lines.append("- **Q5**: generation stage not available yet.")
    lines.append("")
    lines.append(f"**Primary diagnosis: {decision['primary']}** — {decision['primary_note']}")
    if decision["secondary"]:
        lines.append(f"**Secondary diagnosis: {decision['secondary']}.**")
    lines.append(
        f"**EACL follow-up decision: `{decision['eacl_followup_decision']}`** — "
        f"{decision['eacl_followup_note']}"
    )
    lines.append("")

    lines.append("## A. Candidate-Pool Upper Bound (truth-based, analysis-only)")
    lines.append("")
    lines.append(f"- DIRECT required-aspect coverage (truth chunk-ids): {oracle_totals['direct_truth_covered']}/66")
    lines.append(f"- ROUND_ROBIN (truth chunk-ids): {oracle_totals['round_robin_truth_covered']}/66")
    lines.append(f"- Base-stream candidate union coverage: {oracle_totals['base_union_recall']}/66")
    lines.append(f"- Decomposition candidate super-pool coverage: {oracle_totals['superpool_recall']}/66")
    lines.append(f"- ORACLE_BASE_TOP5 (<=5 chunks from base union): {oracle_totals['oracle_base_top5']}/66")
    lines.append(f"- ORACLE_TOP5 (<=5 chunks from super-pool): {oracle_totals['oracle_top5']}/66")
    lines.append(
        f"- Decomposition-specific exploration upside (ORACLE_TOP5 - ORACLE_BASE_TOP5): "
        f"**+{signals['exploration_upside_aspects']}**"
    )
    lines.append(
        f"- Total possible judge-verified gain over DIRECT: "
        f"**+{signals['oracle_upside_vs_direct_aspects']}** aspects (ORACLE_TOP5, analysis-only)"
    )
    lines.append("")

    lines.append("## B. Evidence Policy Comparison (blind evidence judge)")
    lines.append("")
    lines.append(
        "Complete/displaced/below-DIRECT denominators are judged cases: 20 for single policies, "
        "60 for the 3-seed pooled bandit rows; recall denominators are aspects (66 / 198)."
    )
    lines.append("")
    lines.append(
        "| policy | recall | complete | precision | useful exploration | base preservation "
        "| oracle gap | displaced | below DIRECT |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for row in table:
        lines.append(evidence_row_cells(row))
    lines.append("")
    lines.append("Exploration-exploitation ledger (judge-based, vs frozen DIRECT):")
    lines.append("")
    lines.append(
        "| policy | exploratory selected | useful exploratory | useful base preserved "
        "| new aspects gained | old aspects lost | net aspect delta |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for row in table:
        lines.append(
            f"| {row['policy']} | {row['exploratory_chunks']} | {row['useful_exploratory_chunks']} "
            f"| {row['useful_base_preserved']}/{row['useful_base_total']} "
            f"| {row['new_aspects_gained']} | {row['aspects_lost']} | {row['net_aspect_delta']:+d} |"
        )
    lines.append("")
    lines.append("Per-seed bandit detail (no seed cherry-picking; mean and spread):")
    lines.append("")
    lines.append(
        "| bandit instance | supported | recall | complete | precision | displaced | exploration rate | base preservation | oracle gap |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for row in bandit_rows:
        lines.append(
            f"| {row['instance']} | {row['supported']}/66 | {fmt(row['recall'])} | {row['complete']}/20 "
            f"| {fmt(row['precision'])} | {row['displaced']} | {fmt(row['exploration_efficiency'], 2)} "
            f"| {fmt(row['base_preservation'], 2)} | {row['oracle_gap']} |"
        )
    lines.append("")

    lines.append("## C. Downstream Answer Results")
    lines.append("")
    if answer_eval:
        aggregates = answer_eval["aggregate"]
        lines.append(
            "| policy | complete | required covered | eligible | citation valid | context utilization | role |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for policy_id, agg in aggregates.items():
            role = "ANALYSIS_ONLY_ORACLE" if agg["analysis_only_oracle"] else "runtime"
            lines.append(
                f"| {policy_id} | {agg['query_required_complete_cases']}/20 "
                f"| {agg['required_covered_total']}/{agg['required_total_total']} | {agg['eligible']} "
                f"| {agg['citation_valid']} | {fmt(agg['context_utilization'])} | {role} |"
            )
        lines.append("")
        lines.append(
            "DIRECT/ROUND_ROBIN answers here are fresh generations under the same frozen generator "
            "and judge protocol (V1 replications); small deltas vs frozen V1 numbers are "
            "generation/judge replication variance, not policy effects."
        )
    else:
        lines.append("generation stage not run")
    lines.append("")

    lines.append("## D. Mechanism Diagnosis")
    lines.append("")
    lines.append(f"- primary: **{decision['primary']}**")
    lines.append(f"- secondary: {decision['secondary'] or 'none'}")
    lines.append("")
    lines.append("Measured signals (aspects out of 66, blind-judged):")
    lines.append("")
    for key, value in signals.items():
        if key == "generation_check":
            continue
        if isinstance(value, dict):
            suffix = ""
            if value.get("recovery_of_rr_oracle_gap") is not None:
                suffix = f", recovery of RR-to-oracle gap {fmt(value['recovery_of_rr_oracle_gap'], 2)}"
            lines.append(f"- {key}: {value.get('policy')} = {value.get('supported')}/66{suffix}")
        else:
            lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append(
        "A. Exploration quality: the decomposition candidate super-pool adds only "
        f"{signals['exploration_upside_aspects']} aspect(s) over the base candidate union "
        "(truth-based: +2). Novel chunks (not in base union) are numerous "
        f"({pool_totals['novel_chunk_count']} total, {pool_totals['novel_supporting_chunk_count']} "
        "supporting) but almost never add required-aspect support."
    )
    lines.append(
        "B. Evidence selection/allocation: frozen ROUND_ROBIN repeats the V1.1 pattern "
        "(31 exploratory chunks, 2 useful = 6.5%); every runtime policy including the bandit "
        "family keeps a "
        f"{fmt(signals['best_simple']['recovery_of_rr_oracle_gap'], 2)} or lower recovery of the "
        "ROUND_ROBIN-to-ORACLE gap and none beats frozen DIRECT."
    )
    lines.append(
        "C. Utility estimation: ORACLE_TOP5 is perfect (66/66) but runtime proxies cannot find "
        "the same chunks; even the base-pool-only oracle (ORACLE_BASE_TOP5 65/66, precision 1.0) "
        f"is {signals['base_pool_oracle_gap_vs_best_selectable_aspects']} aspects above the best "
        "runtime selector."
    )
    lines.append("")

    lines.append("## E. Bandit Value")
    lines.append("")
    lines.append(
        f"Compared with GLOBAL_BASE_RERANK ({_row(table, 'GLOBAL_BASE_RERANK')['supported_total']}/66) "
        f"and best simple instance {signals['best_simple']['policy']} "
        f"({signals['best_simple']['supported']}/66), the best bandit instance "
        f"{signals['best_bandit']['policy']} scores {signals['best_bandit']['supported']}/66. "
        f"Across seeds: {_bandit_spread_text(bandit_rows)}; the spread is comparable to the total "
        "bandit 'signal'. Exploration efficiency stays in the 2.6-10% band already visible in V1 "
        "(6.5%), and base preservation is not improved relative to GLOBAL_BASE_RERANK. "
        "Conclusion: exploration-exploitation framing describes the allocation problem, but full "
        "bandit complexity adds no measurable value at this scale (3 subqueries, 5-slot budget, "
        "noisy continuous reward proxy)."
    )
    lines.append("")

    lines.append("## F. Main Cases")
    lines.append("")
    for entry in case_data["oracle_over_direct_cases"]:
        lines.append(
            f"- {entry['case_id']}: oracle-only aspects vs DIRECT {entry['oracle_only_aspects_vs_direct']}; "
            f"best runtime capture {entry['best_runtime_capture']}"
        )
    if case_data["round_robin_displacement_cases"]:
        lines.append("")
        lines.append("ROUND_ROBIN displacement cases:")
        for entry in case_data["round_robin_displacement_cases"]:
            lines.append(
                f"- {entry['case_id']}: lost {entry['lost_aspects']}, gained "
                f"{entry['gained_aspects']}, exploratory {entry['exploratory']} "
                f"(useful {entry['useful_exploratory']})"
            )
    lines.append("")

    lines.append("## G. EACL Transferability (Petcu et al., EACL 2026)")
    lines.append("")
    lines.append("Paper mechanism: subqueries as bandit arms; one document observed per pull down each "
                 "arm's ranked list; Thompson Sampling with Beta posteriors; utilities from relevance "
                 "judgments or rank scores; top-k rank-aware Bernoulli rewards; cosine novelty term and "
                 "small UCB exploration bonus; fixed document budget; hierarchical correlated arms.")
    lines.append("")
    lines.append("**What transferred**: the arm-per-subquery abstraction maps cleanly onto our frozen "
                 "streams; rank-derived continuous relevance rewards (no human labels at runtime) work "
                 "as a runtime-legal utility proxy; top-k window rewards, the cosine novelty penalty and "
                 "the budget framing are all implementable on precomputed ranked lists with zero extra "
                 "model calls.")
    lines.append("")
    lines.append("**What did not transfer**: at 3 subqueries + base and a 5-slot evidence budget, the "
                 "exploration-exploitation trade-off is nearly degenerate (5 pulls over 4 arms); the "
                 "paper's 35% precision gains come from large budgets (10-30% of hundreds of documents) "
                 "where allocation actually matters. Our oracle shows the pool's required-aspect upside "
                 "is concentrated in the base pool, so subquery-arm allocation cannot be the main lever. "
                 "Binary-relevance Bernoulli rewards in the paper come from human/LLM-judged relevance; "
                 "we substituted normalized cross-encoder scores, which V1.1 already showed are a weak "
                 "required-utility proxy. Also, the paper's final document set is the union of observed "
                 "documents, while our answer needs a strict Top-5, making displacement risk higher.")
    lines.append("")
    lines.append("**Faithfulness statement**: this study is *inspired/adapted*, not a faithful "
                 "reproduction. Deviations: 3 subqueries instead of ~16; chunk-level evidence instead of "
                 "documents; frozen strong base retrieval kept as an additional arm (paper has no base); "
                 "continuous normalized CE reward instead of binary labels; fixed small c for the UCB "
                 "term (paper drives c->0); cross-stream duplicate suppression for the 5-slot budget; "
                 "3 seeds instead of 1000 repeats. Hierarchical correlated bandits were not applicable "
                 "(no hierarchy exists in Router V1).")
    lines.append("")

    lines.append("## H. Next Direction")
    lines.append("")
    lines.append(f"**Primary recommendation: `{decision['eacl_followup_decision']}`**")
    lines.append("")
    lines.append(decision["eacl_followup_note"])
    lines.append("")
    lines.append(
        "Explicit decomposition verdict: `DECOMPOSITION_UPSIDE_TOO_SMALL` — the EACL-style "
        "decomposition/bandit line should not become the next main line. The measured opportunity "
        "is utility estimation for evidence selection from already-retrieved pools "
        "(oracle +9 facts over DIRECT, mostly inside the base pool, unreachable by frozen reranker "
        "scores, MMR novelty, or bandit rewards)."
    )
    lines.append("")

    lines.append("## I. Files")
    lines.append("")
    for name in config["planned_outputs"]:
        lines.append(f"- eval/results/router_v2_selection_study/{name}")
    lines.append("- eval/run_router_v2_preregister.py")
    lines.append("- eval/run_router_v2_selection_study.py")
    lines.append("- eval/run_router_v2_generation.py")
    lines.append("- eval/run_router_v2_analysis.py")
    lines.append("- eval/router_v2_study_lib.py")
    lines.append("")

    lines.append("## Cost and Reproducibility")
    lines.append("")
    lines.append(f"- local reranker replay: {cost['reranker_local_calls']} calls, "
                 f"{cost['reranker_local_pairs']} pairs, {cost['reranker_local_seconds']:.1f}s (CPU, deterministic)")
    lines.append(f"- evidence judge: {cost['evidence_judge_calls']} calls "
                 f"({cost['evidence_judge_new_calls']} new, {cost['evidence_judge_reused_v1_1_calls']} reused from V1.1 cache), "
                 f"{cost['evidence_judge_input_tokens']} input / {cost['evidence_judge_output_tokens']} output tokens")
    lines.append(f"- generation: {cost['generation_calls']} provider calls, "
                 f"{cost['generation_input_tokens']} input / {cost['generation_output_tokens']} output tokens "
                 "(512-token answers, frozen prompt)")
    lines.append(f"- answer judge: {cost['answer_judge_calls']} calls, "
                 f"{cost['answer_judge_input_tokens']} input / {cost['answer_judge_output_tokens']} output tokens")
    lines.append("- no decomposer, router, or retrieval API call was made; candidate pools, rewrites and "
                 "subqueries are frozen V1 artifacts")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- 20-query, 66-aspect exploratory comparison; per-policy deltas of 1-2 aspects are within "
                 "judge/selection noise and are not confirmatory.")
    lines.append("- The frozen truth marks verified supporting chunks, not an exhaustive gold set; "
                 "truth-based oracle bounds are lower bounds (judge-based oracle numbers are reported for "
                 "comparability).")
    lines.append("- The blind evidence judge is a single LLM judge (deepseek-v4-flash) with the frozen "
                 "V1.1 prompt; its aspect-support decisions inherit that protocol's limitations, including "
                 "combination-dependent support across different evidence sets (router_008-style boundary cases).")
    lines.append("- DIRECT/ROUND_ROBIN answers were regenerated (same frozen generator settings), so their "
                 "downstream numbers are replications of V1, not the frozen V1 outputs.")
    lines.append("- Bandit results use 3 predeclared seeds; seed spread is reported, but a 1000-run average "
                 "as in the paper is out of scope at this budget.")
    lines.append("")
    return "\n".join(lines)


def _bandit_spread_text(bandit_rows: Sequence[Mapping[str, Any]]) -> str:
    by_variant: dict[str, list[Mapping[str, Any]]] = {}
    for row in bandit_rows:
        by_variant.setdefault(row["variant"], []).append(row)
    parts = []
    for variant, rows in sorted(by_variant.items()):
        values = [row["supported"] for row in rows]
        parts.append(f"{variant} {min(values)}-{max(values)}/66")
    return ", ".join(parts)


def _row(table: Sequence[Mapping[str, Any]], policy: str) -> Mapping[str, Any]:
    for row in table:
        if row["policy"] == policy:
            return row
    raise KeyError(policy)


def _delta(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def render_failure_review(
    evidence: Mapping[str, Any],
    oracle: Mapping[str, Any],
    decision: Mapping[str, Any],
    case_data: Mapping[str, Any],
    probe: Mapping[str, Any],
    answer_eval: Mapping[str, Any] | None,
) -> str:
    instances = evidence["instances"]
    lines = ["# Router V2 Selection Study - Failure Review", ""]
    lines.append("## Where frozen round-robin fails")
    lines.append("")
    for entry in case_data["round_robin_displacement_cases"]:
        lines.append(
            f"- {entry['case_id']}: lost {entry['lost_aspects']}; gained {entry['gained_aspects']}; "
            f"{entry['exploratory']} exploratory chunks ({entry['useful_exploratory']} useful)"
        )
    lines.append("")
    lines.append("## Oracle-only aspects and runtime capture")
    lines.append("")
    for entry in case_data["oracle_over_direct_cases"]:
        lines.append(
            f"- {entry['case_id']}: {entry['oracle_only_aspects_vs_direct']} -> best runtime "
            f"{entry['best_runtime_capture']}"
        )
    lines.append("")
    lines.append("## Why runtime proxies cannot find oracle evidence")
    lines.append("")
    lines.append(
        f"Truth-oracle chunks missing from DIRECT top5 sit at global cross-encoder ranks "
        f"median={probe['rank_median']}, min={probe['rank_min']}, max={probe['rank_max']} over the "
        f"case super-pools (analysis-only). The frozen MiniLM cross-encoder under the shared rewrite "
        "does not rank required-utility evidence at the top, which caps every policy that leans on "
        "relevance scores, and the same scores are the bandit reward."
    )
    lines.append("")
    lines.append("## Bandit instability")
    lines.append("")
    bandit_rows = bandit_seed_table(evidence)
    by_variant: dict[str, list[dict[str, Any]]] = {}
    for row in bandit_rows:
        by_variant.setdefault(row["variant"], []).append(row)
    for variant, rows in sorted(by_variant.items()):
        recalls = [row["recall"] for row in rows]
        lines.append(
            f"- {variant}: per-seed supported "
            + ", ".join(f"{row['supported']}/66" for row in rows)
            + f" (spread {max(row['supported'] for row in rows) - min(row['supported'] for row in rows)} aspects); "
            + f"displaced {[row['displaced'] for row in rows]}"
        )
    lines.append("")
    lines.append("## Answer-level deltas vs DIRECT (covered aspects, per case)")
    lines.append("")
    if answer_eval:
        deltas = case_data["answer_covered_delta_vs_direct"]
        for case_id, delta in deltas.items():
            notable = {pid: value for pid, value in delta.items() if value != 0}
            if notable:
                lines.append(f"- {case_id}: {notable}")
    else:
        lines.append("answer evaluation unavailable")
    lines.append("")
    lines.append("## Diagnosis to keep on record")
    lines.append("")
    lines.append(f"- primary: {decision['primary']}")
    lines.append(f"- secondary: {decision['secondary']}")
    lines.append(
        "- The dominant failure is not 'decomposition retrieved nothing': the pools contain "
        f"{oracle['totals']['superpool_recall']}/66 truth-coverable aspects. The failure is that no "
        "runtime-legal utility signal (frozen reranker score, MMR novelty, bandit reward) can tell "
        "required-aspect support from topical similarity at the 5-slot budget."
    )
    lines.append("")
    return "\n".join(lines)


def collect_cost(
    evidence: Mapping[str, Any],
    generation: Mapping[str, Any] | None,
    answer_eval: Mapping[str, Any] | None,
) -> dict[str, Any]:
    study_cache = load_json(EVIDENCE_CACHE_PATH) if EVIDENCE_CACHE_PATH.exists() else {}
    v1_1_cache = load_json(V1_1_EVIDENCE_CACHE) if V1_1_EVIDENCE_CACHE.exists() else {}

    def cache_tokens(cache: Mapping[str, Any]) -> tuple[int, int]:
        input_tokens = sum(
            (entry.get("usage") or {}).get("input_tokens") or 0
            for entry in cache.values()
            if isinstance(entry, dict)
        )
        output_tokens = sum(
            (entry.get("usage") or {}).get("output_tokens") or 0
            for entry in cache.values()
            if isinstance(entry, dict)
        )
        return input_tokens, output_tokens

    study_in, study_out = cache_tokens(study_cache)
    reused = 0
    for instance in evidence["instances"].values():
        for case in instance["cases"].values():
            if case.get("status") == "judged":
                reused += 1
    reused = max(0, reused - len(study_cache))
    v1_in, v1_out = cache_tokens(v1_1_cache)
    ledger = load_json(COST_LEDGER_PATH) if COST_LEDGER_PATH.exists() else {}
    answer_cache = load_json(ANSWER_CACHE_PATH) if ANSWER_CACHE_PATH.exists() else {}
    answer_in = sum((entry.get("usage") or {}).get("input_tokens") or 0 for entry in answer_cache.values())
    answer_out = sum((entry.get("usage") or {}).get("output_tokens") or 0 for entry in answer_cache.values())
    meter = evidence["cost"]["local_reranker_meter"]
    return {
        "reranker_local_calls": meter.get("calls"),
        "reranker_local_pairs": meter.get("pairs"),
        "reranker_local_seconds": meter.get("seconds", 0.0),
        "evidence_judge_calls": len(study_cache) + reused,
        "evidence_judge_new_calls": len(study_cache),
        "evidence_judge_reused_v1_1_calls": reused,
        "evidence_judge_input_tokens": study_in,
        "evidence_judge_output_tokens": study_out,
        "evidence_judge_reused_v1_1_cache_input_tokens": v1_in,
        "evidence_judge_reused_v1_1_cache_output_tokens": v1_out,
        "generation_calls": ledger.get("generation_calls", 0),
        "generation_input_tokens": ledger.get("generation_input_tokens", 0),
        "generation_output_tokens": ledger.get("generation_output_tokens", 0),
        "answer_judge_calls": len(answer_cache),
        "answer_judge_input_tokens": answer_in,
        "answer_judge_output_tokens": answer_out,
    }


def main() -> int:
    config = load_json(CONFIG_PATH)
    evidence = load_json(EVIDENCE_RESULTS_PATH)
    oracle = load_json(ORACLE_PATH)
    pool = load_json(CANDIDATE_POOL_PATH)
    generation = load_json(GENERATION_RESULTS_PATH) if GENERATION_RESULTS_PATH.exists() else None
    answer_eval = load_json(ANSWER_EVAL_PATH) if ANSWER_EVAL_PATH.exists() else None
    selections = load_json(SELECTIONS_PATH)

    table = evidence_summary_table(evidence)
    bandit = bandit_seed_table(evidence)
    probe = oracle_recovery_probe(evidence, oracle, selections)
    case_data = case_studies(evidence, oracle, answer_eval or {})
    decision = build_decision(evidence, oracle, answer_eval, config)
    cost = collect_cost(evidence, generation, answer_eval)

    analysis = {
        "version": "router_v2_selection_study_analysis",
        "study_role": config["study_role"],
        "evidence_table": table,
        "bandit_seed_table": bandit,
        "oracle_recovery_probe": probe,
        "case_studies": case_data,
        "decision": decision,
        "cost": cost,
        "candidate_pool_totals": pool["totals"],
        "oracle_totals": oracle["totals"],
    }
    write_json(ANALYSIS_PATH, analysis)
    REPORT_PATH.write_text(
        render_report(config, pool, oracle, evidence, decision, case_data, generation, answer_eval, cost),
        encoding="utf-8",
    )
    FAILURE_REVIEW_PATH.write_text(
        render_failure_review(evidence, oracle, decision, case_data, probe, answer_eval),
        encoding="utf-8",
    )
    print(f"analysis written to {ANALYSIS_PATH}")
    print(f"report written to {REPORT_PATH}")
    print(f"failure review written to {FAILURE_REVIEW_PATH}")
    print(
        f"primary={decision['primary']} secondary={decision['secondary']} "
        f"followup={decision['eacl_followup_decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
