"""Blind A1 answer evaluation over frozen QUERY_REQUIRED aspects (Validation V1).

Reuses the frozen answer-eval judge (V3_JUDGE_SYSTEM / _judge_messages / _parse_judge /
_V3Cache from eval.run_answer_eval). No new evaluator, no generation, no economics.

Blindness: the judge sees only an anonymized answer label and never the arm, policy,
route, evidence-token count, cost, or generation source. The label->arm map is written
to a separate mapping artifact used only for unblinding.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from eval.run_answer_eval import (V3_JUDGE_MAX_TOKENS, V3_JUDGE_VERSION, _V3Cache,
                                  _judge_messages, _parse_judge, _stable_hash)
from src.generator import assign_evidence_sources
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval/results/query_aware_stage1_generation_results.json"
TRUTH = ROOT / "eval/results/frozen_human_verdicts_v1.json"
INDEX = ROOT / "cache/policy_index.json"
CACHE = ROOT / "eval/results/a1_blind_judge_cache_v1.json"
MAPPING = ROOT / "eval/results/a1_blind_answer_mapping_v1.json"
EVAL = ROOT / "eval/results/a1_blind_answer_eval_v1.json"
SUMMARY = ROOT / "eval/results/a1_blind_answer_eval_summary.md"
QUEUE = ROOT / "eval/results/a1_answer_review_queue_v1.json"

SEED = "a1-blind-v1-2026-09-27"
ARMS = ("fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2",
        "no_router_adaptive_v1", "query_router_v1")
CATEGORY = {"covered": "COVERED", "missing": "NOT_COVERED",
            "incorrect": "INCORRECT_OR_CONTRADICTED", "uncertain": "PARTIAL"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def generation_identity(row: dict) -> str:
    return row["reuse_source"] if row["generation_source"] == "reused" else row["canonical_input_hash"]


def label_map(case_id: str, identities: list[str]) -> dict[str, str]:
    ordered = sorted(identities, key=lambda gid: _stable_hash(
        {"seed": SEED, "case_id": case_id, "gid": gid}))
    return {chr(65 + index): gid for index, gid in enumerate(ordered)}


def build_sources(row: dict, chunk_meta: dict):
    return assign_evidence_sources([SimpleNamespace(**chunk_meta[cid])
                                    for cid in row["selected_chunk_ids"]])


def judge_one(case: dict, label: str, owner: dict, client, model: str,
              cache: _V3Cache, usage: dict) -> dict:
    fact_ids = {fact["fact_id"] for fact in case["facts"]}
    messages = _judge_messages(case, {label: owner})
    prompt_hash = _stable_hash({"messages": messages, "model": model, "temperature": 0.0,
                                "max_tokens": V3_JUDGE_MAX_TOKENS, "version": V3_JUDGE_VERSION})
    key = _stable_hash({"case_id": case["case_id"], "label": label, "model": model,
                        "prompt_config_hash": prompt_hash,
                        "answer_sha256": _stable_hash(owner["generation"]["answer"])})
    cached = cache.get(key)
    if cached is None:
        raw, provider_usage = client.complete_with_usage(
            messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
        usage["judge_api_calls"] += 1
        for field in ("input_tokens", "output_tokens"):
            if provider_usage[field] is not None:
                usage[f"judge_{field}_this_run"] += provider_usage[field]
        try:
            parsed = _parse_judge(raw, {label}, fact_ids)
        except (ValueError, KeyError, TypeError) as error:
            cache.set(key, {"raw": raw, "error": str(error), "provider_usage": provider_usage})
            raise ValueError(f"judge schema failure {case['case_id']}/{label}: {error}") from error
        cached = {"answers": parsed, "raw": raw, "prompt_config_hash": prompt_hash,
                  "model": model, "provider_usage": provider_usage}
        cache.set(key, cached)
    else:
        usage["judge_cache_hits"] += 1
        if "error" in cached:
            raise ValueError(f"cached judge error {case['case_id']}/{label}: {cached['error']}")
    return cached["answers"][label]


def run(env_file: Path) -> int:
    results = load(RESULTS)
    truth = load(TRUTH)
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in load(INDEX)["chunks"]}
    required: dict[str, list[dict]] = defaultdict(list)
    for item in truth["items"]:
        if item["case_id"].startswith("VAL-") and item["final"] == "QUERY_REQUIRED":
            required[item["case_id"]].append({"fact_id": item["aspect_id"], "fact": item["statement"]})
    for cid in required:
        required[cid].sort(key=lambda f: f["fact_id"])

    rows_by_case: dict[str, list[dict]] = defaultdict(list)
    for row in results["cases"]:
        if row["case_id"].startswith("VAL-"):
            rows_by_case[row["case_id"]].append(row)

    config = LLMConfig.from_env(env_file)
    client = OpenAIChatCompletionsClient(config)
    cache = _V3Cache(CACHE)
    usage = {"judge_api_calls": 0, "judge_cache_hits": 0,
             "judge_input_tokens_this_run": 0, "judge_output_tokens_this_run": 0}

    mapping: dict[str, dict] = {}
    blind_cases: list[dict] = []
    aspect_totals = {"judged": 0, "covered": 0, "missing": 0, "incorrect": 0, "uncertain": 0}
    unique_answers = 0
    judged_answers = 0

    for case_id in sorted(rows_by_case):
        rows = rows_by_case[case_id]
        by_identity: dict[str, dict] = {}
        arms_by_identity: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            gid = generation_identity(row)
            by_identity.setdefault(gid, row)  # identical generation -> identical answer/sources
            arms_by_identity[gid].append(row["arm"])
        labels = label_map(case_id, list(by_identity))
        query = rows[0]["original_query"]
        case = {"case_id": case_id, "query": query, "facts": required[case_id]}
        mapping[case_id] = {label: {"arms": sorted(arms_by_identity[gid]),
                                    "generation_identity": gid,
                                    "generation_source": by_identity[gid]["generation_source"]}
                            for label, gid in labels.items()}
        answers = {}
        for label, gid in labels.items():
            row = by_identity[gid]
            unique_answers += 1
            owner = {"generation": {"answer": row["answer"]}, "sources": build_sources(row, chunk_meta)}
            try:
                judged = judge_one(case, label, owner, client, config.model, cache, usage)
                judged_answers += 1
                statuses = {fact["fact_id"]: fact for fact in judged["facts"]}
                aspect_rows = {}
                for fact in case["facts"]:
                    fid = fact["fact_id"]
                    raw = statuses[fid]["status"]
                    aspect_totals["judged"] += 1
                    aspect_totals[raw] += 1
                    aspect_rows[fid] = {"judge_status": raw, "category": CATEGORY[raw],
                                        "citation_status": statuses[fid]["citation_status"],
                                        "note": statuses[fid].get("note", "")}
                answers[label] = {
                    "aspects": aspect_rows,
                    "query_required_complete": all(v["judge_status"] == "covered"
                                                   for v in aspect_rows.values()),
                    "claim_counts": dict(Counter(c["support_status"] for c in judged["claims"])),
                    "claim_citation_counts": dict(Counter(c["citation_status"] for c in judged["claims"])),
                    "judge_error": None,
                }
            except Exception as error:  # judge failure -> human review, never treated as covered
                answers[label] = {"aspects": {}, "query_required_complete": None,
                                  "claim_counts": {}, "claim_citation_counts": {},
                                  "judge_error": str(error)}
        blind_cases.append({"case_id": case_id, "query": query,
                            "required_aspects": case["facts"], "answers": answers})

    MAPPING.write_text(json.dumps({"version": "a1-blind-answer-mapping-v1", "seed": SEED,
        "note": "UNBLIND ONLY - not visible to the evaluator", "cases": mapping},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    EVAL.write_text(json.dumps({
        "version": "a1-blind-answer-eval-v1", "status": "complete", "seed": SEED,
        "blind": True,
        "aspect_source": "frozen_human_verdicts_v1.json final==QUERY_REQUIRED (Validation V1 only)",
        "judge": {"model": config.model, "prompt_version": V3_JUDGE_VERSION,
                  "max_tokens": V3_JUDGE_MAX_TOKENS, "temperature": 0.0},
        "case_count": len(blind_cases), "unique_answers_evaluated": unique_answers,
        "required_aspects_per_case": {c["case_id"]: len(c["required_aspects"]) for c in blind_cases},
        "aspect_totals": aspect_totals, "cases": blind_cases}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    # ---- unblind + arm-level candidate table ----
    blind_by_case = {c["case_id"]: c for c in blind_cases}
    arm_aspects = {arm: {"covered": 0, "missing": 0, "incorrect": 0, "uncertain": 0,
                         "complete_cases": 0, "judge_error_cases": 0} for arm in ARMS}
    pair = {arm: {"gained": 0, "lost": 0, "complete_improved": 0, "complete_regressed": 0,
                  "complete_same": 0} for arm in ARMS}
    ground = {arm: {"claim_supported": 0, "claim_partial": 0, "claim_unsupported": 0,
                    "claim_contradicted": 0, "claim_uncertain": 0,
                    "citation_unsupported": 0, "citation_missing": 0} for arm in ARMS}
    name_by_identity = {}
    for cid, labels in mapping.items():
        for label, meta in labels.items():
            for arm in meta["arms"]:
                name_by_identity[(cid, arm)] = label
    for cid in sorted(mapping):
        blind = blind_by_case[cid]
        # per-arm status for this case (shared generations copy the same result to every arm)
        arm_status = {}
        for label, meta in mapping[cid].items():
            for arm in meta["arms"]:
                arm_status[arm] = (blind["answers"].get(label) or {})
        base = arm_status.get("fixed_top5") or {}
        for arm in ARMS:
            res = arm_status.get(arm) or {}
            aspects = res.get("aspects") or {}
            for value in aspects.values():
                arm_aspects[arm][value["judge_status"]] += 1
            if res.get("query_required_complete"):
                arm_aspects[arm]["complete_cases"] += 1
            if res.get("judge_error"):
                arm_aspects[arm]["judge_error_cases"] += 1
            for name, count in (res.get("claim_counts") or {}).items():
                key = "claim_" + name
                if key in ground[arm]:
                    ground[arm][key] += count
            for name, count in (res.get("claim_citation_counts") or {}).items():
                if name in ("unsupported", "missing"):
                    ground[arm]["citation_" + name] += count
            if arm != "fixed_top5" and base.get("aspects") is not None:
                gained = lost = 0
                for fid, value in (aspects or {}).items():
                    b = (base.get("aspects") or {}).get(fid)
                    if b is None:
                        continue
                    if value["judge_status"] == "covered" and b["judge_status"] != "covered":
                        gained += 1
                    if b["judge_status"] == "covered" and value["judge_status"] != "covered":
                        lost += 1
                pair[arm]["gained"] += gained
                pair[arm]["lost"] += lost
                if base.get("query_required_complete") and res.get("query_required_complete") is False:
                    pair[arm]["complete_regressed"] += 1
                elif base.get("query_required_complete") is False and res.get("query_required_complete"):
                    pair[arm]["complete_improved"] += 1
                elif base.get("query_required_complete") == res.get("query_required_complete"):
                    pair[arm]["complete_same"] += 1

    # ---- review queue ----
    queue = []
    for cid in sorted(mapping):
        blind = blind_by_case[cid]
        for label, meta in mapping[cid].items():
            res = blind["answers"].get(label) or {}
            arms = list(meta["arms"])
            if res.get("judge_error"):
                queue.append({"case_id": cid, "arms": arms, "label": label,
                              "priority": 1, "kind": "judge_error", "detail": res["judge_error"]})
                continue
            for fid, value in (res.get("aspects") or {}).items():
                if value["judge_status"] in ("uncertain", "incorrect"):
                    queue.append({"case_id": cid, "arms": arms, "label": label,
                                  "priority": 1 if value["judge_status"] == "incorrect" else 2,
                                  "kind": value["category"], "aspect_id": fid,
                                  "judge_status": value["judge_status"], "note": value.get("note", "")})
        base_label = next((l for l, m in mapping[cid].items() if "fixed_top5" in m["arms"]), None)
        base = (blind["answers"].get(base_label) or {}) if base_label else {}
        for label, meta in mapping[cid].items():
            res = blind["answers"].get(label) or {}
            if base.get("query_required_complete") and res.get("query_required_complete") is False:
                for arm in meta["arms"]:
                    if arm != "fixed_top5":
                        queue.append({"case_id": cid, "arm": arm, "label": label, "priority": 1,
                                      "kind": "complete_regression_vs_fixed_top5",
                                      "detail": "QueryRequiredComplete true->false"})
            if (res.get("claim_counts") or {}).get("contradicted"):
                for arm in meta["arms"]:
                    if arm != "fixed_top5":
                        queue.append({"case_id": cid, "arm": arm, "label": label, "priority": 1,
                                      "kind": "contradicted_claim",
                                      "detail": f"{res['claim_counts']['contradicted']} contradicted claim(s)"})
    # selector vs router: only material coverage / completeness / contradiction differences
    disputes = []
    for cid in sorted(mapping):
        labels = mapping[cid]
        def find(arm):
            return next((l for l, m in labels.items() if arm in m["arms"]), None)
        sel = (blind_by_case[cid]["answers"].get(find("coverage_selector_v2")) or {})
        rou = (blind_by_case[cid]["answers"].get(find("query_router_v1")) or {})
        def covered(res):
            return sum(1 for v in (res.get("aspects") or {}).values() if v["judge_status"] == "covered")
        def contradicted(res):
            return (res.get("claim_counts") or {}).get("contradicted", 0)
        if (sel.get("query_required_complete") != rou.get("query_required_complete")
                or covered(sel) != covered(rou) or contradicted(sel) != contradicted(rou)):
            disputes.append({"case_id": cid,
                             "selector_complete": sel.get("query_required_complete"),
                             "router_complete": rou.get("query_required_complete"),
                             "selector_covered": covered(sel), "router_covered": covered(rou),
                             "selector_contradicted": contradicted(sel),
                             "router_contradicted": contradicted(rou)})
    for d in disputes:
        queue.append({"case_id": d["case_id"], "arm": "coverage_selector_v2|query_router_v1",
                      "priority": 3, "kind": "selector_vs_router", "detail": d})

    QUEUE.write_text(json.dumps({"version": "a1-answer-review-queue-v1",
        "note": "Minimal human queue; arms shown for resolution, evaluator/judge was blind.",
        "counts": {"total": len(queue), "by_priority": dict(Counter(q["priority"] for q in queue)),
                   "by_kind": dict(Counter(q["kind"] for q in queue))},
        "selector_vs_router_disputes": disputes, "items": queue},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- summary ----
    total_required_instances = aspect_totals["judged"]
    lines = ["# Blind A1 answer evaluation (Validation V1)", "",
             "**Blind:** the judge saw only anonymized answer labels; no arm, policy, route, "
             "evidence/cost telemetry, or generation source was exposed. Judge = frozen "
             f"`{V3_JUDGE_VERSION}` over frozen `QUERY_REQUIRED` aspects.", "",
             "## Dataset", "",
             f"- 50 Validation V1 cases; {results['case_count']} arm-case rows.",
             f"- Required aspects: {len(required)} cases, {sum(len(v) for v in required.values())} QUERY_REQUIRED aspects.",
             f"- Unique answers actually evaluated (identical/shared generations deduplicated): "
             f"**{unique_answers}**; judged: {judged_answers}, judge errors: {unique_answers - judged_answers}.",
             "", "## Required-aspect evaluation (unique answers)", "",
             f"- aspect judgments: {total_required_instances}",
             f"- covered: {aspect_totals['covered']}; missing: {aspect_totals['missing']}; "
             f"incorrect: {aspect_totals['incorrect']}; uncertain(PARTIAL): {aspect_totals['uncertain']}",
             "", "## Candidate quality by arm (after unblinding)", "",
             "| Arm | covered | missing | incorrect | uncertain | QueryRequiredComplete cases | judge-error cases |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        a = arm_aspects[arm]
        lines.append(f"| {arm} | {a['covered']} | {a['missing']} | {a['incorrect']} | "
                     f"{a['uncertain']} | {a['complete_cases']}/50 | {a['judge_error_cases']} |")
    lines += ["", "## Pairwise vs fixed_top5 (candidate regressions/improvements)", "",
              "| Arm | required gained | required lost | complete improved | complete regressed | complete same |",
              "|---|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        if arm == "fixed_top5":
            continue
        p = pair[arm]
        lines.append(f"| {arm} | {p['gained']} | {p['lost']} | {p['complete_improved']} | "
                     f"{p['complete_regressed']} | {p['complete_same']} |")
    lines += ["", "## Grounding / citation diagnostics by arm", "",
              "| Arm | supported claims | partial | unsupported | contradicted | uncertain | unsupported citations | missing citations |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        g = ground[arm]
        lines.append(f"| {arm} | {g['claim_supported']} | {g['claim_partial']} | {g['claim_unsupported']} | "
                     f"{g['claim_contradicted']} | {g['claim_uncertain']} | {g['citation_unsupported']} | {g['citation_missing']} |")
    lines += ["", "## Review queue", "",
              f"- total items: {len(queue)}",
              f"- by priority: {dict(Counter(q['priority'] for q in queue))}",
              f"- by kind: {dict(Counter(q['kind'] for q in queue))}",
              f"- selector-vs-router dispute cases: {len(disputes)}", "",
              "## Blind integrity", "",
              "- Evaluator input contained only: anonymized case label, original query, answer text, "
              "cited evidence, and frozen QUERY_REQUIRED aspects.",
              "- Not exposed: arm identity, policy, route, evidence/context token counts, cost, latency, generation source.",
              "- Label->arm mapping stored only in `a1_blind_answer_mapping_v1.json`.", "",
              "No economics, no Pareto, no keep/kill decision."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"unique_answers": unique_answers, "judged": judged_answers,
                      "aspect_totals": aspect_totals,
                      "judge_api_calls": usage["judge_api_calls"],
                      "judge_cache_hits": usage["judge_cache_hits"],
                      "review_queue": len(queue),
                      "selector_vs_router_disputes": len(disputes)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    return run(args.env_file)


if __name__ == "__main__":
    raise SystemExit(main())
