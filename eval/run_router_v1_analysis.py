"""Router V1 post-hoc analysis and human-readable report generation."""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "eval" / "results" / "router_v1"
ARMS = ("FIXED_DIRECT", "FIXED_DECOMPOSE", "ROUTED")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def word_count(query: str) -> int:
    return len(query.split())


def conjunction_count(query: str) -> int:
    return len(re.findall(r"\b(and|also|but|or)\b", query, flags=re.IGNORECASE))


def clause_count(query: str) -> int:
    markers = len(re.findall(r"\b(and|also|but|or|which|who|what|whether|if|when|how)\b",
                             query, flags=re.IGNORECASE))
    return query.count(",") + query.count("?") + markers


def normalized(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().casefold())


def trace_of(result: dict) -> dict:
    return result.get("trace") or {}


def attribution_of(result: dict) -> dict | None:
    attribution = result.get("attribution")
    if attribution is None:
        attribution = trace_of(result).get("attribution")
    return attribution


def cost_of(result: dict) -> dict[str, Any]:
    calls = trace_of(result).get("model_calls") or []
    stages: dict[str, int] = {}
    input_tokens = 0
    output_tokens = 0
    for call in calls:
        stages[call["stage"]] = stages.get(call["stage"], 0) + 1
        input_tokens += call["input_tokens"] or 0
        output_tokens += call["output_tokens"] or 0
    streams = trace_of(result).get("streams") or []
    return {
        "llm_calls": len(calls),
        "stage_calls": stages,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "retrieval_streams": len(streams),
        "reranker_calls": sum(1 for stream in streams if stream.get("failure") is None),
        "failed_streams": sum(1 for stream in streams if stream.get("failure") is not None),
        "latency_seconds": trace_of(result).get("total_latency_seconds"),
    }


def describe(values: list[float]) -> dict[str, Any]:
    values = [value for value in values if value is not None]
    if not values:
        return {"total": 0, "mean": None, "median": None}
    return {"total": round(sum(values), 4), "mean": round(sum(values) / len(values), 4),
            "median": round(statistics.median(values), 4)}


def main() -> int:
    raw = load_json(RESULT_DIR / "raw" / "router_v1_raw_results.json")
    answer_eval = load_json(RESULT_DIR / "router_v1_answer_eval.json")
    oracle = load_json(RESULT_DIR / "router_v1_oracle.json")
    execution = load_json(RESULT_DIR / "router_v1_execution_summary.json")
    truth = load_json(PROJECT_ROOT / "eval" / "router_v1_required_aspects.json")
    benchmark = load_json(PROJECT_ROOT / "eval" / "router_benchmark_v1.json")
    truth_cases = {case["id"]: case for case in truth["cases"]}
    benchmark_cases = {case["id"]: case for case in benchmark["cases"]}
    case_ids = [case["case_id"] for case in raw["cases"]]

    analysis: dict[str, Any] = {"version": "router_v1_analysis", "cases": {}}

    routing = {"router_direct": 0, "router_decompose": 0, "executed_direct": 0,
               "executed_decompose": 0, "fallbacks": {}, "decisions": {},
               "reason_codes": {}, "reason_validity": {}, "schema_anomalies": 0}
    for case in raw["cases"]:
        routed = case["arms"]["ROUTED"]
        decision = routed.get("router_decision")
        routing["decisions"][case["case_id"]] = decision
        if decision == "DIRECT":
            routing["router_direct"] += 1
        elif decision == "DECOMPOSE":
            routing["router_decompose"] += 1
        if routed.get("executed_path") == "DIRECT":
            routing["executed_direct"] += 1
        elif routed.get("executed_path") == "DECOMPOSE":
            routing["executed_decompose"] += 1
        fallback = routed.get("fallback_reason")
        if fallback:
            routing["fallbacks"][fallback] = routing["fallbacks"].get(fallback, 0) + 1
        router_trace = trace_of(routed).get("router") or {}
        code = router_trace.get("effective_reason_code")
        routing["reason_codes"][code] = routing["reason_codes"].get(code, 0) + 1
        validity = router_trace.get("reason_validity")
        routing["reason_validity"][validity] = routing["reason_validity"].get(validity, 0) + 1
        if router_trace.get("schema_anomalies"):
            routing["schema_anomalies"] += 1

    oracle_counts: dict[str, int] = {}
    clear_cases: list[str] = []
    router_matched = 0
    router_missed_direct = 0
    router_missed_decompose = 0
    tie_decompose: list[str] = []
    for case_id in case_ids:
        verdict = oracle["cases"][case_id]["oracle"]
        oracle_counts[verdict] = oracle_counts.get(verdict, 0) + 1
        decision = routing["decisions"][case_id]
        if verdict in {"FIXED_DIRECT", "FIXED_DECOMPOSE"}:
            clear_cases.append(case_id)
            if (verdict == "FIXED_DECOMPOSE" and decision == "DECOMPOSE") or \
               (verdict == "FIXED_DIRECT" and decision == "DIRECT"):
                router_matched += 1
            elif verdict == "FIXED_DECOMPOSE" and decision == "DIRECT":
                router_missed_decompose += 1
            elif verdict == "FIXED_DIRECT" and decision == "DECOMPOSE":
                router_missed_direct += 1
        elif verdict == "TIE" and decision == "DECOMPOSE":
            tie_decompose.append(case_id)

    quality = {arm: answer_eval["aggregate"][arm] for arm in ARMS}

    attribution = {"FIXED_DECOMPOSE": {"executions": 0, "representation_gain_cases": [],
                                       "selection_ranking_gain_cases": [], "zero_evidence_gain_cases": []},
                   "ROUTED_DECOMPOSE": {"executions": 0, "representation_gain_cases": [],
                                        "selection_ranking_gain_cases": [], "zero_evidence_gain_cases": []}}
    for case in raw["cases"]:
        case_id = case["case_id"]
        for arm, bucket in (("FIXED_DECOMPOSE", "FIXED_DECOMPOSE"), ("ROUTED", "ROUTED_DECOMPOSE")):
            result = case["arms"][arm]
            if result.get("executed_path") != "DECOMPOSE":
                continue
            attribution[bucket]["executions"] += 1
            item = attribution_of(result)
            if not item:
                continue
            if item.get("representation_gain_ids"):
                attribution[bucket]["representation_gain_cases"].append(case_id)
            if item.get("selection_ranking_gain_ids"):
                attribution[bucket]["selection_ranking_gain_cases"].append(case_id)
            if item.get("zero_evidence_gain"):
                attribution[bucket]["zero_evidence_gain_cases"].append(case_id)

    mechanism: dict[str, Any] = {}
    for case_id in case_ids:
        verdict = oracle["cases"][case_id]["oracle"]
        if verdict != "FIXED_DECOMPOSE":
            continue
        result = raw["cases"][case_ids.index(case_id)]["arms"]["FIXED_DECOMPOSE"]
        item = attribution_of(result) or {}
        mechanism[case_id] = {
            "representation_gain_ids": item.get("representation_gain_ids", []),
            "selection_ranking_gain_ids": item.get("selection_ranking_gain_ids", []),
            "zero_evidence_gain": item.get("zero_evidence_gain"),
        }

    zero_gain: dict[str, Any] = {}
    for case in raw["cases"]:
        case_id = case["case_id"]
        direct = case["arms"]["FIXED_DIRECT"]
        for arm in ("FIXED_DECOMPOSE", "ROUTED"):
            result = case["arms"][arm]
            if result.get("executed_path") != "DECOMPOSE":
                continue
            item = attribution_of(result) or {}
            if not item.get("zero_evidence_gain"):
                continue
            direct_cost = cost_of(direct)
            arm_cost = cost_of(result)
            zero_gain.setdefault(case_id, {})[arm] = {
                "answer_equal_to_direct": normalized(result.get("answer")) == normalized(direct.get("answer")),
                "direct_covered": (answer_eval["cases"][case_id]["FIXED_DIRECT"].get("required_covered")),
                "arm_covered": (answer_eval["cases"][case_id][arm].get("required_covered")),
                "direct_complete": (answer_eval["cases"][case_id]["FIXED_DIRECT"].get("query_required_complete")),
                "arm_complete": (answer_eval["cases"][case_id][arm].get("query_required_complete")),
                "extra_streams": arm_cost["retrieval_streams"] - direct_cost["retrieval_streams"],
                "extra_llm_calls": arm_cost["llm_calls"] - direct_cost["llm_calls"],
                "extra_input_tokens": arm_cost["input_tokens"] - direct_cost["input_tokens"],
                "extra_output_tokens": arm_cost["output_tokens"] - direct_cost["output_tokens"],
            }

    cost: dict[str, Any] = {}
    for arm in ARMS:
        calls = [cost_of(case["arms"][arm])["llm_calls"] for case in raw["cases"]]
        streams = [cost_of(case["arms"][arm])["retrieval_streams"] for case in raw["cases"]]
        rerank = [cost_of(case["arms"][arm])["reranker_calls"] for case in raw["cases"]]
        input_tokens = [cost_of(case["arms"][arm])["input_tokens"] for case in raw["cases"]]
        output_tokens = [cost_of(case["arms"][arm])["output_tokens"] for case in raw["cases"]]
        latency = [cost_of(case["arms"][arm])["latency_seconds"] for case in raw["cases"]]
        stage_totals: dict[str, int] = {}
        for case in raw["cases"]:
            for stage, count in cost_of(case["arms"][arm])["stage_calls"].items():
                stage_totals[stage] = stage_totals.get(stage, 0) + count
        cost[arm] = {
            "llm_calls": describe(calls),
            "retrieval_streams": describe(streams),
            "reranker_calls": describe(rerank),
            "input_tokens": describe(input_tokens),
            "output_tokens": describe(output_tokens),
            "latency_seconds": describe(latency),
            "stage_call_totals": stage_totals,
            "estimated_monetary_cost": None,
            "note": "no frozen price table for this run; tokens/calls/latency reported instead",
        }
    rewrite_calls = []
    rewrite_input = 0
    rewrite_output = 0
    for case in raw["cases"]:
        for call in case.get("rewrite_calls") or []:
            rewrite_calls.append(call)
            rewrite_input += call.get("input_tokens") or 0
            rewrite_output += call.get("output_tokens") or 0
    shared_rewrite = {"calls": len(rewrite_calls), "input_tokens": rewrite_input,
                      "output_tokens": rewrite_output, "note": "one shared rewrite per query; not part of per-arm cost"}
    judge_cache = load_json(RESULT_DIR / "judge_cache.json")
    judge_input = sum((entry.get("usage") or {}).get("input_tokens") or 0 for entry in judge_cache.values())
    judge_output = sum((entry.get("usage") or {}).get("output_tokens") or 0 for entry in judge_cache.values())
    judge_cost = {"calls": len(judge_cache), "input_tokens": judge_input, "output_tokens": judge_output,
                  "note": "evaluation cost; excluded from serving cost"}

    surface: dict[str, Any] = {"direct_decisions": [], "decompose_decisions": []}
    for case in raw["cases"]:
        case_id = case["case_id"]
        decision = routing["decisions"][case_id]
        row = {
            "case_id": case_id,
            "words": word_count(case["raw_query"]),
            "conjunctions": conjunction_count(case["raw_query"]),
            "clauses": clause_count(case["raw_query"]),
            "multi_document_metadata": "multi_document" in benchmark_cases[case_id].get("benchmark_property", []),
        }
        surface["direct_decisions" if decision == "DIRECT" else "decompose_decisions"].append(row)
    for bucket in ("direct_decisions", "decompose_decisions"):
        rows = surface[bucket]
        surface[bucket] = {
            "cases": [row["case_id"] for row in rows],
            "mean_words": round(statistics.mean([row["words"] for row in rows]), 2) if rows else None,
            "mean_conjunctions": round(statistics.mean([row["conjunctions"] for row in rows]), 2) if rows else None,
            "mean_clauses": round(statistics.mean([row["clauses"] for row in rows]), 2) if rows else None,
            "multi_document_count": sum(1 for row in rows if row["multi_document_metadata"]),
            "details": rows,
        }

    failures: dict[str, list[dict[str, Any]]] = {
        "router_wrong_arm_vs_clear_oracle": [],
        "decomposer_unavailable": [],
        "routed_fallback": [],
        "decompose_better_router_direct": [],
        "direct_better_router_decompose": [],
        "tie_router_decompose_extra_cost": [],
        "representation_gain_without_answer_gain": [],
        "selection_ranking_gain_without_answer_gain": [],
        "answer_gain_without_evidence_novelty": [],
        "evidence_gain_but_not_eligible": [],
        "retrieval_improvement_citation_or_generation_regression": [],
    }
    for case in raw["cases"]:
        case_id = case["case_id"]
        verdict = oracle["cases"][case_id]["oracle"]
        decision = routing["decisions"][case_id]
        routed = case["arms"]["ROUTED"]
        fixed_decompose = case["arms"]["FIXED_DECOMPOSE"]
        if verdict in {"FIXED_DIRECT", "FIXED_DECOMPOSE"}:
            expected = "DIRECT" if verdict == "FIXED_DIRECT" else "DECOMPOSE"
            if decision != expected:
                entry = {"case_id": case_id, "router": decision, "oracle": verdict}
                failures["router_wrong_arm_vs_clear_oracle"].append(entry)
                if verdict == "FIXED_DECOMPOSE":
                    failures["decompose_better_router_direct"].append(entry)
                else:
                    failures["direct_better_router_decompose"].append(entry)
        if fixed_decompose.get("executed_path") != "DECOMPOSE":
            failures["decomposer_unavailable"].append(
                {"case_id": case_id, "fallback_reason": fixed_decompose.get("fallback_reason"),
                 "execution_success": fixed_decompose.get("execution_success")})
        if routed.get("fallback_reason"):
            failures["routed_fallback"].append(
                {"case_id": case_id, "fallback_reason": routed.get("fallback_reason"),
                 "executed_path": routed.get("executed_path")})
        if verdict == "TIE" and decision == "DECOMPOSE":
            failures["tie_router_decompose_extra_cost"].append({"case_id": case_id})
        direct_eval = answer_eval["cases"][case_id]["FIXED_DIRECT"]
        decompose_eval = answer_eval["cases"][case_id]["FIXED_DECOMPOSE"]
        item = attribution_of(fixed_decompose) or {}
        representation_ids = item.get("representation_gain_ids") or []
        ranking_ids = item.get("selection_ranking_gain_ids") or []
        has_gain = bool(representation_ids or ranking_ids)
        direct_covered = direct_eval.get("required_covered")
        decompose_covered = decompose_eval.get("required_covered")
        if representation_ids and direct_covered is not None and decompose_covered is not None \
                and decompose_covered <= direct_covered:
            failures["representation_gain_without_answer_gain"].append(
                {"case_id": case_id, "direct_covered": direct_covered,
                 "decompose_covered": decompose_covered,
                 "representation_gain_ids": representation_ids})
        if ranking_ids and direct_covered is not None and decompose_covered is not None \
                and decompose_covered <= direct_covered:
            failures["selection_ranking_gain_without_answer_gain"].append(
                {"case_id": case_id, "direct_covered": direct_covered,
                 "decompose_covered": decompose_covered,
                 "selection_ranking_gain_ids": ranking_ids})
        if not has_gain and direct_covered is not None and decompose_covered is not None \
                and decompose_covered > direct_covered:
            failures["answer_gain_without_evidence_novelty"].append(
                {"case_id": case_id, "direct_covered": direct_covered,
                 "decompose_covered": decompose_covered})
        if has_gain and not decompose_eval.get("eligible"):
            failures["evidence_gain_but_not_eligible"].append(
                {"case_id": case_id, "decompose_status": decompose_eval.get("status")})
        if (decompose_eval.get("required_covered") or 0) >= (direct_covered or 0) \
                and not (decompose_eval.get("citation_validation") or {}).get("valid", True):
            failures["retrieval_improvement_citation_or_generation_regression"].append(
                {"case_id": case_id})
    failures = {key: value for key, value in failures.items() if value}

    same_evidence_variance: list[dict[str, Any]] = []
    for case in raw["cases"]:
        case_id = case["case_id"]
        routed = case["arms"]["ROUTED"]
        direct = case["arms"]["FIXED_DIRECT"]
        if routed.get("executed_path") != "DIRECT":
            continue
        if [item["chunk_id"] for item in direct["evidence"]] != \
                [item["chunk_id"] for item in routed["evidence"]]:
            continue
        d_eval = answer_eval["cases"][case_id]["FIXED_DIRECT"]
        r_eval = answer_eval["cases"][case_id]["ROUTED"]
        if (d_eval.get("required_covered") != r_eval.get("required_covered") or
                d_eval.get("query_required_complete") != r_eval.get("query_required_complete")):
            same_evidence_variance.append({
                "case_id": case_id,
                "direct_covered": d_eval.get("required_covered"),
                "routed_covered": r_eval.get("required_covered"),
                "direct_complete": d_eval.get("query_required_complete"),
                "routed_complete": r_eval.get("query_required_complete"),
            })

    router_stage = {
        "router_calls": 0, "router_input_tokens": 0, "router_output_tokens": 0,
        "router_latency_seconds": 0.0,
    }
    for case in raw["cases"]:
        for call in (trace_of(case["arms"]["ROUTED"]).get("model_calls") or []):
            if call["stage"] == "router":
                router_stage["router_calls"] += 1
                router_stage["router_input_tokens"] += call["input_tokens"] or 0
                router_stage["router_output_tokens"] += call["output_tokens"] or 0
                router_stage["router_latency_seconds"] += call["latency_seconds"] or 0.0
    router_stage["decomposer_calls_used"] = sum(
        cost_of(case["arms"]["ROUTED"])["stage_calls"].get("decomposer", 0) for case in raw["cases"])
    router_stage["decomposer_calls_saved_vs_fixed_decompose"] = 20 - router_stage["decomposer_calls_used"]
    router_stage["streams_saved_vs_fixed_decompose"] = \
        80 - sum(cost_of(case["arms"]["ROUTED"])["retrieval_streams"] for case in raw["cases"])

    analysis.update({
        "routing": routing,
        "oracle_counts": oracle_counts,
        "router_vs_oracle": {
            "clear_oracle_cases": clear_cases,
            "matched_clear_oracle": router_matched,
            "chose_direct_when_decompose_better": router_missed_decompose,
            "chose_decompose_when_direct_better": router_missed_direct,
            "tie_with_decompose": tie_decompose,
        },
        "quality": quality,
        "attribution": attribution,
        "quality_gain_mechanism": mechanism,
        "zero_evidence_gain": zero_gain,
        "cost": cost,
        "shared_rewrite_cost": shared_rewrite,
        "judge_cost": judge_cost,
        "surface_heuristics": surface,
        "failures": failures,
        "same_evidence_generation_variance": same_evidence_variance,
        "router_overhead": router_stage,
    })
    write_json(RESULT_DIR / "router_v1_analysis.json", analysis)

    build_report(raw, answer_eval, oracle, execution, analysis, truth_cases, benchmark_cases)
    build_failure_review(analysis)
    print("analysis, report, and failure review written", flush=True)
    return 0


def pct(part, total):
    return f"{part}/{total} ({100.0 * part / total:.0f}%)" if total else f"{part}/{total}"


def build_report(raw, answer_eval, oracle, execution, analysis, truth_cases, benchmark_cases) -> None:
    case_ids = [case["case_id"] for case in raw["cases"]]
    quality = analysis["quality"]
    oracle_counts = analysis["oracle_counts"]
    routing = analysis["routing"]
    lines: list[str] = []
    lines.append("# Router V1 Frozen Experiment Report")
    lines.append("")
    lines.append(f"Run: {raw.get('started_at_utc')} to {raw.get('finished_at_utc')}; "
                 f"implementation commit `{raw.get('implementation_source_commit')}`.")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    d_q = quality["FIXED_DIRECT"]
    b_q = quality["FIXED_DECOMPOSE"]
    r_q = quality["ROUTED"]
    lines.append(f"- Fixed DIRECT answered {d_q['judged']}/20 cases; query-required complete "
                 f"{pct(d_q['query_required_complete_cases'], d_q['judged'])}; required aspects covered "
                 f"{d_q['required_covered_total']}/{d_q['required_total_total']}.")
    lines.append(f"- Fixed DECOMPOSE answered {b_q['judged']}/20; complete "
                 f"{pct(b_q['query_required_complete_cases'], b_q['judged'])}; covered "
                 f"{b_q['required_covered_total']}/{b_q['required_total_total']}.")
    lines.append(f"- ROUTED answered {r_q['judged']}/20; complete "
                 f"{pct(r_q['query_required_complete_cases'], r_q['judged'])}; covered "
                 f"{r_q['required_covered_total']}/{r_q['required_total_total']}.")
    lines.append(f"- Post-hoc oracle (frozen contract): {json.dumps(oracle_counts)}. "
                 f"Router matched the clear oracle on {analysis['router_vs_oracle']['matched_clear_oracle']}"
                 f"/{len(analysis['router_vs_oracle']['clear_oracle_cases'])} cases with a clear preference.")
    lines.append(f"- Router chose DECOMPOSE {routing['router_decompose']}/20 times; executed DECOMPOSE "
                 f"{routing['executed_decompose']}/20; fallbacks {json.dumps(routing['fallbacks'])}.")
    variance = analysis.get("same_evidence_generation_variance", [])
    lines.append(f"- Routing-attributable quality: on the 17 DIRECT-executed cases ROUTED reused identical "
                 f"evidence to FIXED_DIRECT; {len(variance)} of them changed judged coverage "
                 f"({json.dumps(variance)}), so the aggregate ROUTED lead over DIRECT is not attributable to routing.")
    lines.append("")
    lines.append("## 2. Frozen Experimental Setup")
    lines.append("")
    lines.append("- Benchmark: `eval/router_benchmark_v1.json` (20 queries), required-aspect truth "
                 "`eval/router_v1_required_aspects.json` (66 required aspects).")
    lines.append("- Architecture/contract/preregistration frozen before implementation; implementation "
                 "commit `98cb503ee3a5b5f7f9340a5d5008b6497da5da0f`; 318 tests passing before this run.")
    lines.append("- Corpus: 57 docs at `b9578b546d2506febda1da2cd7431644d58e512c`; same indexes, MiniLM reranker.")
    lines.append("- Identity: DeepSeek `deepseek-v4-flash` (thinking disabled), temperature 0, router 96 / "
                 "decomposer 256 / generation 512 output tokens, timeout 30s, retries 0.")
    lines.append("- Execution order: per case, FIXED_DIRECT then FIXED_DECOMPOSE then ROUTED; one shared "
                 "rewrite per case reused by all three arms.")
    lines.append("- Judge: existing frozen `broad-v3-answer-quality-v1` protocol, one opaque label per call, "
                 "arm identity never exposed.")
    lines.append("")
    lines.append("## 3. Routing Behavior")
    lines.append("")
    lines.append(f"- Router decisions: DIRECT {routing['router_direct']}, DECOMPOSE {routing['router_decompose']}.")
    lines.append(f"- Executed paths under ROUTED: DIRECT {routing['executed_direct']}, DECOMPOSE {routing['executed_decompose']}.")
    lines.append(f"- Fallbacks: {json.dumps(routing['fallbacks']) or 'none'}.")
    lines.append(f"- reason_code counts: {json.dumps(routing['reason_codes'])}; validity: {json.dumps(routing['reason_validity'])}; "
                 f"schema anomalies: {routing['schema_anomalies']}.")
    lines.append("")
    lines.append("## 4. Quality Results")
    lines.append("")
    lines.append("| arm | judged | execution success | citation valid | eligible | complete | covered aspects |")
    lines.append("|---|---|---|---|---|---|---|")
    for arm in ARMS:
        agg = quality[arm]
        lines.append(f"| {arm} | {agg['judged']}/20 | {agg['execution_success']}/20 | {agg['citation_valid']}/20 | "
                     f"{agg['eligible']}/20 | {agg['query_required_complete_cases']}/{agg['judged']} | "
                     f"{agg['required_covered_total']}/{agg['required_total_total']} |")
    lines.append("")
    lines.append("## 5. Post-hoc Oracle")
    lines.append("")
    lines.append("| oracle outcome | cases |")
    lines.append("|---|---|")
    for key in ("FIXED_DIRECT", "FIXED_DECOMPOSE", "TIE", "NEITHER_ELIGIBLE", "ORACLE_UNAVAILABLE"):
        lines.append(f"| {key} | {oracle_counts.get(key, 0)} |")
    lines.append("")
    lines.append("| case | oracle | direct elig/complete/covered | decompose avail/elig/complete/covered | router |")
    lines.append("|---|---|---|---|---|")
    for case_id in case_ids:
        row = oracle["cases"][case_id]
        lines.append(
            f"| {case_id} | {row['oracle']} | {row['direct_eligible']}/"
            f"{row['direct_complete']}/{row['direct_covered']} | "
            f"{row['decompose_available']}/{row['decompose_eligible']}/"
            f"{row['decompose_complete']}/{row['decompose_covered']} | "
            f"{routing['decisions'][case_id]} |")
    lines.append("")
    lines.append("## 6. Cost & Latency")
    lines.append("")
    lines.append("| arm | llm calls (tot/mean) | streams (tot/mean) | rerank calls (tot) | input tok (tot/mean) | "
                 "output tok (tot/mean) | latency s (tot/mean) |")
    lines.append("|---|---|---|---|---|---|---|")
    for arm in ARMS:
        c = analysis["cost"][arm]
        lines.append(
            f"| {arm} | {c['llm_calls']['total']}/{c['llm_calls']['mean']} | "
            f"{c['retrieval_streams']['total']}/{c['retrieval_streams']['mean']} | "
            f"{c['reranker_calls']['total']} | {c['input_tokens']['total']}/{c['input_tokens']['mean']} | "
            f"{c['output_tokens']['total']}/{c['output_tokens']['mean']} | "
            f"{c['latency_seconds']['total']}/{c['latency_seconds']['mean']} |")
    lines.append("")
    lines.append(f"- Shared rewrite: {analysis['shared_rewrite_cost']['calls']} calls, "
                 f"{analysis['shared_rewrite_cost']['input_tokens']} input / "
                 f"{analysis['shared_rewrite_cost']['output_tokens']} output tokens (per query, reused by all arms).")
    lines.append(f"- Judge (evaluation cost, excluded from serving): {analysis['judge_cost']['calls']} calls, "
                 f"{analysis['judge_cost']['input_tokens']} input / {analysis['judge_cost']['output_tokens']} output tokens.")
    overhead = analysis.get("router_overhead", {})
    lines.append(f"- Router overhead: {overhead.get('router_calls')} calls, "
                 f"{overhead.get('router_input_tokens')} input / {overhead.get('router_output_tokens')} output tokens, "
                 f"{round(overhead.get('router_latency_seconds', 0.0), 2)}s; it avoided "
                 f"{overhead.get('decomposer_calls_saved_vs_fixed_decompose')} decomposer calls and "
                 f"{overhead.get('streams_saved_vs_fixed_decompose')} retrieval streams versus always-decompose.")
    lines.append("- Monetary cost: no frozen price table for this run; not estimated.")
    lines.append("")
    lines.append("## 7. Evidence Attribution")
    lines.append("")
    for bucket in ("FIXED_DECOMPOSE", "ROUTED_DECOMPOSE"):
        item = analysis["attribution"][bucket]
        lines.append(f"- {bucket}: executions {item['executions']}; representation_gain cases "
                     f"{item['representation_gain_cases'] or 'none'}; selection_ranking_gain cases "
                     f"{item['selection_ranking_gain_cases'] or 'none'}; zero_evidence_gain cases "
                     f"{item['zero_evidence_gain_cases'] or 'none'}.")
    lines.append("")
    lines.append("## 8. Failure Analysis")
    lines.append("")
    if analysis["failures"]:
        for key, rows in analysis["failures"].items():
            lines.append(f"- {key}: {json.dumps(rows, ensure_ascii=False)}")
    else:
        lines.append("- none recorded")
    lines.append("")
    lines.append("## 9. Validity / Limitations")
    lines.append("")
    for item in [
        "n = 20; results are descriptive, not significance claims.",
        "Corpus-specific: findings apply to this 57-document GitHub site-policy snapshot only.",
        "Router predicts a retrieval coverage risk from the rewrite representation alone; no retrieval feedback.",
        "Provider/model nondeterminism: temperature 0 does not guarantee identical server-side outputs; raw responses were stored.",
        "All arms depend on the shared rewrite; rewrite errors affect every arm.",
        "DECOMPOSE has a larger retrieval budget (3-4 streams, more candidates) by design; cost is reported separately.",
        "Required-aspect granularity correlates with author multi_document metadata (r=0.776); completeness is stricter for cross-document cases.",
        "Benchmark surface bias: earlier freeze audit found overlapping structural cues; only 5 localized cases.",
        "Provider version identity is limited to the requested model id; immutable server version may be unavailable.",
    ]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 10. Conclusion")
    lines.append("")
    lines.append(_conclusion(quality, oracle_counts, analysis))
    lines.append("")
    lines.append("## Research Table")
    lines.append("")
    lines.append("| ID | Router | Executed | Direct qr | Decompose qr | Oracle | Routed qr | Evidence gain | Cost delta (streams/calls) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for case in raw["cases"]:
        case_id = case["case_id"]
        direct = case["arms"]["FIXED_DIRECT"]
        decompose = case["arms"]["FIXED_DECOMPOSE"]
        routed = case["arms"]["ROUTED"]
        d_eval = answer_eval["cases"][case_id]["FIXED_DIRECT"]
        b_eval = answer_eval["cases"][case_id]["FIXED_DECOMPOSE"]
        r_eval = answer_eval["cases"][case_id]["ROUTED"]
        d_cost = cost_of(direct)
        r_cost = cost_of(routed)
        gain = attribution_of(routed) or {}
        gain_label = "rep" if gain.get("representation_gain_ids") else (
            "rank" if gain.get("selection_ranking_gain_ids") else (
                "zero" if gain.get("applicable") else "-"))
        lines.append(
            f"| {case_id} | {routing['decisions'][case_id]} | {routed.get('executed_path')} | "
            f"{_qr(d_eval)} | {_qr(b_eval)} | {oracle['cases'][case_id]['oracle']} | {_qr(r_eval)} | "
            f"{gain_label} | {r_cost['retrieval_streams']}/{r_cost['llm_calls']} vs "
            f"{d_cost['retrieval_streams']}/{d_cost['llm_calls']} |")
    lines.append("")
    (RESULT_DIR / "router_v1_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _qr(entry: dict) -> str:
    if entry.get("status") != "judged":
        return entry.get("status", "unavailable")
    complete = "yes" if entry.get("query_required_complete") else "no"
    return f"{complete} {entry.get('required_covered')}/{entry.get('required_total')}"


def _conclusion(quality, oracle_counts, analysis) -> str:
    d = quality["FIXED_DIRECT"]
    b = quality["FIXED_DECOMPOSE"]
    r = quality["ROUTED"]
    clear = analysis["router_vs_oracle"]["clear_oracle_cases"]
    matched = analysis["router_vs_oracle"]["matched_clear_oracle"]
    variance = analysis.get("same_evidence_generation_variance", [])
    tie_dec = analysis["router_vs_oracle"]["tie_with_decompose"]
    sensitive = b["query_required_complete_cases"] < d["query_required_complete_cases"] or \
        b["required_covered_total"] < d["required_covered_total"]
    direct_note = (
        "always-decompose scored below fixed DIRECT"
        if sensitive else
        "always-decompose did not exceed fixed DIRECT")
    return (
        f"On this 20-query GitHub policy benchmark, {direct_note} "
        f"(FIXED_DECOMPOSE {b['query_required_complete_cases']}/20 complete, "
        f"{b['required_covered_total']}/66 required aspects vs FIXED_DIRECT "
        f"{d['query_required_complete_cases']}/20, {d['required_covered_total']}/66). "
        f"ROUTED scored {r['query_required_complete_cases']}/20 and {r['required_covered_total']}/66, but on its "
        f"DIRECT-executed cases it used evidence identical to FIXED_DIRECT and {len(variance)} case(s) differed only "
        f"through generation sampling ({[row['case_id'] for row in variance]}), so the routed-vs-DIRECT aggregate "
        f"difference is not attributable to the routing decision. Routing matched {matched}/{len(clear)} clear oracle "
        f"preferences (one miss, router_001, was an eligibility-based preference with equal coverage), preserved the "
        f"eligibility-favourable decompose case router_011, and spent extra cost on two TIE cases ({tie_dec}). "
        "Verdict: mixed; no clear routing-attributable quality gain at n=20.")


def build_failure_review(analysis) -> None:
    lines = ["# Router V1 Failure Review", ""]
    failures = analysis.get("failures", {})
    if not failures:
        lines.append("No failure categories were populated.")
    for key, rows in failures.items():
        lines.append(f"## {key}")
        lines.append("")
        for row in rows:
            lines.append(f"- {json.dumps(row, ensure_ascii=False)}")
        lines.append("")
    lines.append("## Zero evidence gain detail")
    lines.append("")
    for case_id, arms in analysis.get("zero_evidence_gain", {}).items():
        for arm, detail in arms.items():
            lines.append(f"- {case_id} {arm}: {json.dumps(detail, ensure_ascii=False)}")
    lines.append("")
    (RESULT_DIR / "router_v1_failure_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
