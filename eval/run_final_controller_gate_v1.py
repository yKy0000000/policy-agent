"""Final Controller Gate V1 — non-oracle action discovery + bounded action probes.

This is the last architecture experiment for the GitHub Policy Support Agent. It does NOT build a
controller up front. It answers one question: can a runtime sensor, with no gold aspects, no target
proposition, no oracle evidence and no human diagnosis, discover a real query-required gap from
(query + actual generation context + draft answer) and choose a bounded action (PATCH_CONTEXT /
REFRESH_CONTEXT) that is worth executing?

Phases are executed through explicit subcommands so nothing is implied:

    --mode eligibility   Phase 0: derive frozen natural positives / controls, write sample artifacts
    --mode gate1         Gate 1: run the frozen sensor over the frozen sample
    --mode gate2_patch   Gate 2A: bounded repair on real sensor-detected PATCH gaps (Gate 1 PASS only)
    --mode gate2_refresh Gate 2B: targeted vs blind refresh (Gate 1 PASS only)
    --mode economics     Gate 3: cost/latency from recorded usage

The sensor prompt, sample, thresholds and action definitions are frozen in gate_manifest_v1.json and
must not change after the first call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from statistics import mean
from time import perf_counter
from types import SimpleNamespace

from eval.run_answer_eval import _V3Cache, _sha256, _stable_hash
from src.generator import assign_evidence_sources, format_evidence
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "eval/reports/final_controller_gate_v1"
CACHE_PATH = ROOT / "cache/final_controller_gate_v1_cache.json"

QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
VERDICTS = ROOT / "eval/results/frozen_human_verdicts_v1.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
CLEANED_COHORT = ROOT / "eval/results/measurement_validity_cleaned_cohort.json"
A1_BLIND = ROOT / "eval/results/a1_blind_answer_quality_frozen_v1.json"
A1_MAP = ROOT / "eval/results/a1_blind_answer_mapping_v1.json"

VERSION = "final-controller-gate-v1"
SENSOR_MODEL = "deepseek-v4-flash"
REPLICATES = 2
MAX_TOKENS = 700
TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 120.0

ACTIONS = ("RETURN_DRAFT", "PATCH_CONTEXT", "REFRESH_CONTEXT")

# --- frozen Phase 0 selection (recorded here; the eligibility artifact mirrors it) --------------- #
# Primary positives require agreement between the canonical frozen A1 blind judge (which carries the
# human resolutions) and the generation-utilization judge where both exist. PATCH primary = required
# fact NOT_COVERED in the draft and its evidence present in the actual context.
PATCH_POSITIVES = {
    "VAL-001-011": ["VAL-001-011-F01"],
    "VAL-001-050": ["VAL-001-050-F01"],
}
# Judge-disagreement candidates: the generation-utilization judge calls these missing, but the
# canonical A1 blind judge calls them COVERED. Recorded, excluded from the primary denominator.
PATCH_JUDGE_DISAGREEMENT = {
    "VAL-001-009": ["VAL-001-009-F01"],
    "VAL-001-022": ["VAL-001-022-F02"],
}
REFRESH_POSITIVES = {
    "VAL-001-006": ["VAL-001-006-F02"],
    "VAL-001-033": ["VAL-001-033-F01", "VAL-001-033-F02", "VAL-001-033-F03",
                    "VAL-001-033-F04", "VAL-001-033-F05"],
    "VAL-001-046": ["VAL-001-046-F03", "VAL-001-046-F04"],
}
OPTIONAL_PRESSURE = {
    "VAL-001-026": ["VAL-001-026-F02"],
    "VAL-001-039": ["VAL-001-039-F02"],
}
SECONDARY_REFRESH = {"VAL-001-001": ["VAL-001-001-F02", "VAL-001-001-F03"]}
CONTROL_COUNT = 3
CONTROL_EXCLUDE = (set(PATCH_POSITIVES) | set(PATCH_JUDGE_DISAGREEMENT) | set(REFRESH_POSITIVES)
                   | set(OPTIONAL_PRESSURE) | set(SECONDARY_REFRESH) | {"VAL-001-008"})

SENSOR_SYSTEM = (
    "You are a runtime answer-quality controller for a GitHub policy support agent.\n\n"
    "You are given: the user question; the evidence sources (S1..Sn) that were supplied to the "
    "answer generator; and the draft answer that was produced from those sources.\n\n"
    "Decide whether the draft has a substantive, query-required answer obligation that is missing, "
    "and if so choose exactly one bounded action.\n\n"
    "Definitions:\n"
    "- An answer obligation is a piece of policy information that a correct, complete answer to the "
    "user's question must address (for example a required condition, scope, exception, step, actor, "
    "or outcome that the question asks about).\n"
    "- PATCH_CONTEXT: a query-required obligation is missing from the draft AND the current sources "
    "(S1..Sn) already contain evidence that directly supports it. The fix is to add that obligation "
    "using the current sources only.\n"
    "- REFRESH_CONTEXT: a query-required obligation is missing from the draft AND the current sources "
    "do NOT contain enough evidence to support it. The fix is to search the policy corpus again.\n"
    "- RETURN_DRAFT: no missing query-required obligation can be reliably identified. This does not "
    "assert that the answer is complete.\n\n"
    "Rules:\n"
    "- Choose at most one action.\n"
    "- Only report an obligation that the user's question actually requires. Do not invent "
    "requirements and do not pad with related-but-unasked policy content.\n"
    "- Do not claim an obligation is missing if the draft already expresses it; paraphrase counts as "
    "expressed.\n"
    "- For PATCH_CONTEXT, evidence_refs must cite sources that exist in the current sources: a "
    "source_id such as S1 plus a short evidence_span copied verbatim from that source.\n"
    "- For REFRESH_CONTEXT, refresh_query must be a short open retrieval query for the missing "
    "obligation. It must be a query only: never write the answer or a guessed policy statement into "
    "it.\n"
    "- Do not output URLs. Do not output a confidence value.\n"
    "- Return only the JSON object, with no prose.\n\n"
    "JSON schema:\n"
    '{"action":"RETURN_DRAFT|PATCH_CONTEXT|REFRESH_CONTEXT","target":"<the missing obligation in one '
    'sentence, or empty>","reason":"<why the question requires it and why the draft lacks it>",'
    '"evidence_refs":[{"source_id":"S1","evidence_span":"..."}],"refresh_query":"<query or empty>"}'
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"\s+", " ", text).strip().lower().split())


# -------------------------------------------------------------------------------------------- #
# Data access
# -------------------------------------------------------------------------------------------- #

class FrozenData:
    def __init__(self) -> None:
        self.queries = {c["case_id"]: c["query"] for c in _json(QUERIES)["cases"]}
        self.verdicts = {r["aspect_id"]: r for r in _json(VERDICTS)["items"]}
        self.rubric_facts: dict[str, dict] = {}
        for case in _json(RUBRIC)["cases"]:
            for fact in case["facts"]:
                self.rubric_facts[fact["fact_id"]] = {**fact, "case_id": case["case_id"]}
        transfer = _json(TRANSFER)
        self.bge_arm = transfer["preparation"]["arms"]["bge_top5"]
        self.answers = {c["case_id"]: c["arms"]["bge_top5"]["answer"] for c in transfer["cases"]
                        if c["status"] == "complete"}
        self.available_facts = {cid: set(item["available_fact_ids"])
                                for cid, item in self.bge_arm.items()}
        gu = _json(UTILIZATION)
        self.baseline_quality = {c["case_id"]: c["arms"]["baseline"]["quality"]
                                 for c in gu["cases"] if c["status"] == "complete"}
        self.control_ids = gu["cohort"]["control_ids"]
        a1 = _json(A1_BLIND)
        self.a1_cases = {c["case_id"]: c for c in a1["cases"]}
        self.a1_mapping = _json(A1_MAP)["cases"]

    def a1_fixed_top5_label(self, case_id: str, fact_id: str) -> dict:
        """Canonical A1 blind label for the fixed_top5 (BGE research stack) answer."""
        mapping = self.a1_mapping.get(case_id, {})
        label = next((lab for lab, info in mapping.items() if "fixed_top5" in info["arms"]), None)
        entry = self.a1_cases.get(case_id, {}).get("answers", {}).get(label, {}).get("aspects", {})
        cell = entry.get(fact_id)
        if cell is None:
            return {"label": None, "note": "not_in_required_aspects"}
        return {"label": cell.get("category"), "note": cell.get("note", "")}

    def scenario(self, case_id: str) -> dict:
        chunks = self.bge_arm[case_id]["chunks"]
        sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
        return {
            "case_id": case_id,
            "query": self.queries[case_id],
            "chunks": chunks,
            "sources": sources,
            "evidence_text": format_evidence(sources),
            "draft": self.answers[case_id],
        }

    def mark(self, fact_id: str) -> dict:
        v = self.verdicts[fact_id]
        return {
            "fact_id": fact_id,
            "statement": self.rubric_facts[fact_id]["statement"],
            "final": v["final"],
            "route": v.get("route"),
            "in_context": fact_id in self.available_facts[v["case_id"]],
        }

    def control_selection(self) -> list[str]:
        pool = [cid for cid in self.control_ids if cid not in CONTROL_EXCLUDE]
        pool.sort(key=lambda cid: hashlib.sha256(
            ("final-controller-gate-v1" + cid).encode("utf-8")).hexdigest())
        return pool[:CONTROL_COUNT]


# -------------------------------------------------------------------------------------------- #
# Phase 0 — eligibility
# -------------------------------------------------------------------------------------------- #

def build_eligibility() -> dict:
    frozen = FrozenData()
    controls = frozen.control_selection()

    def entry(case_id: str, role: str, target_facts: list[str], expected: str) -> dict:
        a1 = {fid: frozen.a1_fixed_top5_label(case_id, fid) for fid in target_facts}
        gu = {fid: ("missing" if fid in frozen.baseline_quality.get(case_id, {}).get(
            "missing_fact_ids", []) else "covered") for fid in target_facts}
        return {
            "case_id": case_id,
            "role": role,
            "expected_action": expected,
            "target_fact_ids": target_facts,
            "route": frozen.verdicts[target_facts[0]]["route"] if target_facts else None,
            "draft_omits": bool(target_facts) and all(
                a1[fid]["label"] == "NOT_COVERED" for fid in target_facts),
            "a1_fixed_top5_labels": a1,
            "generation_utilization_judge": gu,
            "support_in_context": all(frozen.mark(fid)["in_context"] for fid in target_facts) if target_facts else None,
            "truth": [frozen.mark(fid) for fid in target_facts],
        }

    cases = []
    for cid, facts in PATCH_POSITIVES.items():
        cases.append(entry(cid, "patch_positive", facts, "PATCH_CONTEXT"))
    for cid, facts in PATCH_JUDGE_DISAGREEMENT.items():
        cases.append(entry(cid, "patch_judge_disagreement", facts, "PATCH_CONTEXT"))
    for cid, facts in REFRESH_POSITIVES.items():
        cases.append(entry(cid, "refresh_positive", facts, "REFRESH_CONTEXT"))
    for cid in controls:
        q = frozen.baseline_quality.get(cid, {})
        cases.append({
            "case_id": cid, "role": "complete_control", "expected_action": "RETURN_DRAFT",
            "target_fact_ids": [], "route": frozen.verdicts[[k for k in frozen.verdicts
                                                              if k.startswith(cid)][0]]["route"],
            "draft_omits": False, "support_in_context": None, "truth": [],
            "baseline_fact_complete": q.get("fact_complete"),
            "baseline_grounded_fact_complete": q.get("grounded_fact_complete"),
        })
    for cid, facts in OPTIONAL_PRESSURE.items():
        cases.append(entry(cid, "optional_pressure", facts, "RETURN_DRAFT"))
    for cid, facts in SECONDARY_REFRESH.items():
        cases.append(entry(cid, "secondary_refresh", facts, "REFRESH_CONTEXT"))

    return {
        "schema_version": 1,
        "version": VERSION,
        "frozen_inputs": {
            "eval/validation/broad_queries_validation_v1.json": _sha256(QUERIES),
            "eval/validation/broad_atomic_facts_validation_v1.json": _sha256(RUBRIC),
            "eval/results/frozen_human_verdicts_v1.json": _sha256(VERDICTS),
            "eval/results/reranker_transfer_results.json": _sha256(TRANSFER),
            "eval/results/generation_utilization_results.json": _sha256(UTILIZATION),
            "eval/results/a1_blind_answer_quality_frozen_v1.json": _sha256(A1_BLIND),
            "eval/results/a1_blind_answer_mapping_v1.json": _sha256(A1_MAP),
        },
        "roles": {
            "patch_positive": "QUERY_REQUIRED aspect omitted by the draft, evidence present in context",
            "patch_judge_disagreement": "generation-utilization judge says missing, canonical A1 judge says covered; not in the primary denominator",
            "refresh_positive": "QUERY_REQUIRED aspect omitted by the draft, evidence absent from context",
            "complete_control": "baseline grounded-fact-complete case (harmful-action control)",
            "optional_pressure": "RELEVANT_BUT_OPTIONAL omitted fact (must not become a required action)",
            "secondary_refresh": "ranking-weakness case; recorded, not in the primary denominator",
        },
        "counts": {
            "patch_positive": len(PATCH_POSITIVES),
            "patch_judge_disagreement": len(PATCH_JUDGE_DISAGREEMENT),
            "refresh_positive": len(REFRESH_POSITIVES),
            "complete_control": len(controls),
            "optional_pressure": len(OPTIONAL_PRESSURE),
            "secondary_refresh": len(SECONDARY_REFRESH),
        },
        "cases": cases,
        "replicate_calls": (len(cases)) * REPLICATES,
    }


def render_eligibility_md(document: dict) -> str:
    lines = ["# Final Controller Gate V1 - Sample Eligibility (Phase 0)", "",
             "> Frozen selection derived from existing frozen artifacts only. No new questions, no new",
             "> labels, no benchmark construction. `039-F02` is `RELEVANT_BUT_OPTIONAL` and is therefore",
             "> an optional-pressure control, never a required positive.", "",
             f"- counts: {document['counts']}",
             f"- planned sensor calls: {document['replicate_calls']} ({REPLICATES} replicates)", "",
             "| case | role | expected action | route | draft omits (A1) | in-context | A1 label | target facts |",
             "|---|---|---|---|---|---|---|---|"]
    for case in document["cases"]:
        labels = ", ".join(f"{fid}:{(lab.get('label'))}"
                           for fid, lab in case.get("a1_fixed_top5_labels", {}).items()) or "-"
        lines.append("| {case_id} | {role} | {expected_action} | {route} | {om} | {ctx} | {lab} | {facts} |".format(
            case_id=case["case_id"], role=case["role"], expected_action=case["expected_action"],
            route=case.get("route"), om=case.get("draft_omits"),
            ctx=case.get("support_in_context"), lab=labels,
            facts=", ".join(case.get("target_fact_ids", [])) or "-"))
    lines += ["", "## Truth rows", ""]
    for case in document["cases"]:
        for truth in case.get("truth", []):
            lines.append(f"- {truth['fact_id']} ({truth['final']}, in_context={truth['in_context']}): "
                         f"{truth['statement']}")
    return "\n".join(lines)


# -------------------------------------------------------------------------------------------- #
# Sensor
# -------------------------------------------------------------------------------------------- #

def sensor_messages(scenario: dict) -> list[dict]:
    user = (
        "User question:\n" + scenario["query"] +
        "\n\nEvidence sources (the only policy evidence the draft was allowed to use):\n" +
        scenario["evidence_text"] +
        "\n\nDraft answer:\n" + scenario["draft"] +
        "\n\nReturn only the JSON object."
    )
    return [{"role": "system", "content": SENSOR_SYSTEM}, {"role": "user", "content": user}]


def parse_sensor(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    action = str(data["action"]).strip().upper()
    if action not in ACTIONS:
        raise ValueError(f"invalid action: {action}")
    refs = data.get("evidence_refs") or []
    if not isinstance(refs, list):
        raise ValueError("evidence_refs must be a list")
    parsed_refs = []
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError("evidence_ref must be an object")
        parsed_refs.append({"source_id": str(ref.get("source_id", "")).strip(),
                            "evidence_span": str(ref.get("evidence_span", "")).strip()})
    return {
        "action": action,
        "target": str(data.get("target", "")).strip(),
        "reason": str(data.get("reason", "")).strip()[:600],
        "evidence_refs": parsed_refs,
        "refresh_query": str(data.get("refresh_query", "")).strip(),
    }


def deterministic_check(parsed: dict, scenario: dict) -> dict:
    source_map = {source.citation_id: source.text for source in scenario["sources"]}
    issues: list[str] = []
    if parsed["action"] in ("PATCH_CONTEXT", "REFRESH_CONTEXT") and not parsed["target"]:
        issues.append("empty_target")
    if parsed["action"] == "PATCH_CONTEXT":
        if not parsed["evidence_refs"]:
            issues.append("missing_evidence_refs")
        for ref in parsed["evidence_refs"]:
            if ref["source_id"] not in source_map:
                issues.append(f"unknown_source:{ref['source_id']}")
            elif ref["evidence_span"] and _normalize(ref["evidence_span"]) not in _normalize(
                    source_map[ref["source_id"]]):
                issues.append(f"span_not_in_source:{ref['source_id']}")
    if parsed["action"] == "REFRESH_CONTEXT":
        query = parsed["refresh_query"]
        if len(query.split()) < 3:
            issues.append("refresh_query_too_short")
        if re.search(r"https?://", query, re.IGNORECASE):
            issues.append("refresh_query_has_url")
    if re.search(r"https?://", " ".join(ref["evidence_span"] for ref in parsed["evidence_refs"])):
        issues.append("evidence_span_has_url")
    return {"valid": not issues, "issues": issues}


def execute_sensor(cell: dict, scenario: dict, cache: _V3Cache, client, failures: list,
                   *, check_only: bool) -> dict:
    messages = sensor_messages(scenario)
    prompt_hash = _stable_hash({"messages": messages, "temperature": TEMPERATURE,
                                "max_tokens": MAX_TOKENS, "version": VERSION,
                                "system_sha256": hashlib.sha256(SENSOR_SYSTEM.encode()).hexdigest()})
    key = _stable_hash({"version": VERSION, "model": SENSOR_MODEL, "case_id": cell["case_id"],
                        "replicate": cell["replicate"], "prompt_config_hash": prompt_hash})
    cached = cache.get(key)
    if cached is None:
        if check_only:
            raise KeyError(f"missing cache entry: {cell['cell_id']}")
        started = perf_counter()
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=MAX_TOKENS,
                                                    temperature=TEMPERATURE)
            parsed = parse_sensor(raw)
            cached = {"raw": raw, "parsed": parsed,
                      "deterministic": deterministic_check(parsed, scenario),
                      "provider_usage": usage, "latency_seconds": perf_counter() - started}
        except Exception as error:
            cached = {"raw": None, "parsed": None,
                      "deterministic": {"valid": False, "issues": ["sensor_error"]},
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"cell_id": cell["cell_id"], "error": cached["error"]})
        cache.set(key, cached)
    return {**cell, "prompt_config_hash": prompt_hash, "cache_key": key, **cached}


def run_gate1(*, check_only: bool = False) -> dict:
    frozen = FrozenData()
    eligibility = build_eligibility()
    scenarios = {case["case_id"]: frozen.scenario(case["case_id"]) for case in eligibility["cases"]}
    cells = []
    for case in eligibility["cases"]:
        if case["role"] == "secondary_refresh":
            continue  # recorded in eligibility, not part of the frozen Gate 1 call set (budget)
        for replicate in range(1, REPLICATES + 1):
            cells.append({"cell_id": f"{case['case_id']}::{case['role']}::r{replicate}",
                          "case_id": case["case_id"], "role": case["role"],
                          "expected_action": case["expected_action"], "replicate": replicate})
    config = LLMConfig.from_env(ROOT / ".env")
    client = OpenAIChatCompletionsClient(replace(config, model=SENSOR_MODEL,
                                                 timeout_seconds=REQUEST_TIMEOUT_SECONDS))
    cache = _V3Cache(CACHE_PATH)
    failures: list = []
    executed = []
    for cell in cells:
        result = execute_sensor(cell, scenarios[cell["case_id"]], cache, client, failures,
                                check_only=check_only)
        executed.append(result)
        print(f"{cell['cell_id']} -> {(result.get('parsed') or {}).get('action')}", flush=True)
    document = {
        "schema_version": 1,
        "version": VERSION,
        "phase": "gate1_non_oracle_action_discovery",
        "status": "complete",
        "sensor_model": SENSOR_MODEL,
        "sensor_system_sha256": hashlib.sha256(SENSOR_SYSTEM.encode("utf-8")).hexdigest(),
        "design": {"replicates": REPLICATES, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
                   "cells": len(cells)},
        "eligibility": eligibility,
        "cells": executed,
        "failures": failures,
    }
    if not check_only:
        _write(REPORT_DIR / "gate1_sensor_results.json", document)
    return document


# -------------------------------------------------------------------------------------------- #
# CLI
# -------------------------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="eligibility",
                        choices=("eligibility", "gate1", "check"))
    args = parser.parse_args(argv)
    if args.mode == "eligibility":
        document = build_eligibility()
        _write(REPORT_DIR / "sample_eligibility.json", document)
        (REPORT_DIR / "sample_eligibility.md").write_text(render_eligibility_md(document), encoding="utf-8")
        print(json.dumps(document["counts"], ensure_ascii=False))
    elif args.mode == "gate1":
        document = run_gate1()
        print(json.dumps({"cells": len(document["cells"]), "failures": document["failures"]},
                         ensure_ascii=False))
    elif args.mode == "check":
        run_gate1(check_only=True)
        print("cache complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
