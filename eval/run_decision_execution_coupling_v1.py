"""Decision-Execution Coupling V1 (Mechanism / H3).

The action decision is injected externally (D1 REPAIR_NEEDED, D2 NO_CHANGE_ALREADY_PRESENT,
D3 NO_CHANGE_UNSUPPORTED); generation must execute it. Primary endpoints are deterministic adherence and
override rates; semantic correctness is secondary and clearly labeled. No routing, no production change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from eval.run_answer_eval import _V3Cache, _sha256, _stable_hash
from eval.run_oracle_repair_v1 import judge_revised, sentence_preservation
from eval.run_semantic_gap_discrimination_v1 import (build_dataset as build_probe_dataset,
                                                     validate_dataset as validate_probe_dataset)
from eval.run_task_conditioned_action_v1 import context_block
from src.generator import parse_citation_ids, validate_citations
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
PREREG = ROOT / "eval/decision_execution_coupling_v1_preregistration.md"
CACHE = ROOT / "cache/decision_execution_coupling_v1_cache.json"
RESULTS = ROOT / "eval/results/decision_execution_coupling_v1_results.json"
SUMMARY = ROOT / "eval/results/decision_execution_coupling_v1_summary.md"
STAGE_SUMMARY = ROOT / "eval/results/mechanism_h3_stage_summary.md"
HUMAN_SHEET = ROOT / "eval/results/decision_execution_coupling_v1_human_review.md"

VERSION = "decision-execution-coupling-v1"
MODELS = {"current": "deepseek-v4-flash", "stronger": "deepseek-v4-pro"}
DECISIONS = ("D1", "D2", "D3")
REPLICATES = 3
MAX_TOKENS = 1536
TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 120.0
BLIND_SEED = 20260928

PRIMARY_ITEMS = ("M-VAL-001-039-F02", "M-VAL-001-050-F01")
CONTROL_ITEMS = ("P-VAL-001-050-F02", "U-039-01")
ITEM_IDS = PRIMARY_ITEMS + CONTROL_ITEMS
KIND = {"M-VAL-001-039-F02": "missing", "M-VAL-001-050-F01": "missing",
        "P-VAL-001-050-F02": "already_present_control", "U-039-01": "unsupported_control"}
GOLD_DECISION = {"M-VAL-001-039-F02": "REPAIR_NEEDED", "M-VAL-001-050-F01": "REPAIR_NEEDED",
                 "P-VAL-001-050-F02": "NO_CHANGE_ALREADY_PRESENT",
                 "U-039-01": "NO_CHANGE_UNSUPPORTED"}

DECISION_INJECTION = {
    "D1": ("The decision has already been made: the answer requires repair for the specified "
           "proposition. Do not re-evaluate whether repair is needed. Execute the repair."),
    "D2": ("The decision has already been made: the proposition is already present in the answer. Do not "
           "repair or rewrite the answer."),
    "D3": ("The decision has already been made: the proposition is not supported by the frozen evidence. "
           "Do not add it to the answer."),
}

DECISION_SYSTEM = {
    "D1": (
        "You are executing a pre-made repair decision for a GitHub policy answer. "
        + DECISION_INJECTION["D1"] +
        " Produce a minimal patch and the revised answer using only the frozen evidence; preserve all "
        "existing correct content and citations; do not add unrelated information; use only the existing "
        "source IDs. Reply with JSON only: "
        '{"execution_status":"REPAIRED|REFUSED|OVERRIDDEN_DECISION","proposed_patch":"...",'
        '"revised_answer":"...","brief_note":"..."}'
    ),
    "D2": (
        "You are executing a pre-made no-change decision for a GitHub policy answer. "
        + DECISION_INJECTION["D2"] +
        " Return the baseline answer unchanged and an empty patch. Reply with JSON only: "
        '{"execution_status":"NO_CHANGE|OVERRIDDEN_DECISION","proposed_patch":"",'
        '"revised_answer":"<baseline unchanged>","brief_note":"..."}'
    ),
    "D3": (
        "You are executing a pre-made no-change decision for a GitHub policy answer. "
        + DECISION_INJECTION["D3"] +
        " Return the baseline answer unchanged and an empty patch. Reply with JSON only: "
        '{"execution_status":"NO_CHANGE|OVERRIDDEN_DECISION","proposed_patch":"",'
        '"revised_answer":"<baseline unchanged>","brief_note":"..."}'
    ),
}
ALLOWED_STATUS = {"D1": ("REPAIRED", "REFUSED", "OVERRIDDEN_DECISION"),
                  "D2": ("NO_CHANGE", "OVERRIDDEN_DECISION"),
                  "D3": ("NO_CHANGE", "OVERRIDDEN_DECISION")}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def build_messages(item: dict, decision: str) -> list[dict]:
    return [{"role": "system", "content": DECISION_SYSTEM[decision]},
            {"role": "user", "content": context_block(item) + "\n\n" + DECISION_INJECTION[decision] +
             "\n\nReturn only the JSON object."}]


def parse_execution(raw: str, decision: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    status = str(data["execution_status"]).strip().upper()
    if status not in ALLOWED_STATUS[decision]:
        raise ValueError(f"invalid execution_status for {decision}: {status}")
    patch = data.get("proposed_patch")
    revised = data.get("revised_answer")
    if not isinstance(patch, str) or not isinstance(revised, str) or not revised.strip():
        raise ValueError("proposed_patch and revised_answer must be strings")
    return {"execution_status": status, "proposed_patch": patch.strip(),
            "revised_answer": revised.strip(), "brief_note": str(data.get("brief_note", ""))[:400]}


def build_items() -> dict[str, dict]:
    dataset = build_probe_dataset()
    validate_probe_dataset(dataset)
    by_id = {item["item_id"]: item for item in dataset["items"]}
    rubric = _json(RUBRIC)
    facts_by_case = {case["case_id"]: case["facts"] for case in rubric["cases"]}
    items = {}
    for item_id in ITEM_IDS:
        base = dict(by_id[item_id])
        base["kind"] = KIND[item_id]
        base["gold_decision"] = GOLD_DECISION[item_id]
        base["case_facts"] = facts_by_case[base["case_id"]]
        items[item_id] = base
    return items


def build_cells(items: dict[str, dict]) -> list[dict]:
    cells = []
    for item_id in ITEM_IDS:
        for model_key, model in MODELS.items():
            for decision in DECISIONS:
                for replicate in range(1, REPLICATES + 1):
                    cells.append({"cell_id": f"{item_id}::{model_key}::{decision}::r{replicate}",
                                  "item_id": item_id, "kind": items[item_id]["kind"],
                                  "model_key": model_key, "model": model, "decision": decision,
                                  "replicate": replicate})
    return cells


def execute_cell(cell: dict, item: dict, cache: _V3Cache, clients: dict, failures: list,
                 *, check_only: bool) -> dict:
    messages = build_messages(item, cell["decision"])
    prompt_hash = _stable_hash({"messages": messages, "temperature": TEMPERATURE,
                                "max_tokens": MAX_TOKENS, "version": VERSION})
    key = _stable_hash({"version": VERSION, "model": cell["model"], "item_id": cell["item_id"],
                        "decision": cell["decision"], "replicate": cell["replicate"],
                        "prompt_config_hash": prompt_hash})
    cached = cache.get(key)
    if cached is None:
        if check_only:
            raise KeyError(f"missing cache entry: {cell['cell_id']}")
        client = clients[cell["model_key"]]
        started = perf_counter()
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=MAX_TOKENS,
                                                    temperature=TEMPERATURE)
            parsed = parse_execution(raw, cell["decision"])
            cached = {"kind": "execution", "raw": raw, "parsed": parsed, "provider_usage": usage,
                      "latency_seconds": perf_counter() - started, "raw_hash": _stable_hash(raw)}
        except Exception as error:
            cached = {"kind": "execution", "raw": None, "parsed": None,
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"kind": "execution", "cell_id": cell["cell_id"],
                             "error": cached["error"]})
        cache.set(key, cached)
    checks = (execution_checks(item, cell["decision"], cached["parsed"])
              if cached.get("parsed") else None)
    return {**cell, "prompt_config_hash": prompt_hash, "cache_key": key, **cached,
            "checks": checks}


def execution_checks(item: dict, decision: str, parsed: dict) -> dict:
    baseline = item["baseline_answer"]
    revised = parsed["revised_answer"]
    edited = _normalize(revised) != _normalize(baseline)
    patch_nonempty = bool(parsed["proposed_patch"])
    adherence = ((edited and patch_nonempty) if decision == "D1"
                 else (not edited and not patch_nonempty))
    citation = validate_citations(revised, item["sources"])
    baseline_citations = set(parse_citation_ids(baseline))
    revised_citations = set(parse_citation_ids(revised))
    return {
        "status": parsed["execution_status"],
        "edited": edited,
        "patch_nonempty": patch_nonempty,
        "adherence": adherence,
        "explicit_override": parsed["execution_status"] == "OVERRIDDEN_DECISION",
        "refused": parsed["execution_status"] == "REFUSED",
        "preservation": sentence_preservation(baseline, revised),
        "word_delta": len(revised.split()) - len(baseline.split()),
        "citation_validation": citation["validation"],
        "citations_lost": sorted(baseline_citations - revised_citations),
        "url_introduced": citation["validation"]["contains_model_generated_url"],
    }


def judge_edited(item: dict, answer: str, cache: _V3Cache, client, failures: list,
                 *, check_only: bool) -> dict | None:
    case = {"fact_id": item["fact_id"] or item["item_id"], "query": item["query"],
            "facts": [{"fact_id": fact["fact_id"], "statement": fact["statement"]}
                      for fact in item["case_facts"]],
            "sources": item["sources"]}
    judged = judge_revised(case, answer, cache, client, failures, check_only=check_only)
    if not judged or not judged.get("answers"):
        return None
    facts = {fact["fact_id"]: fact for fact in judged["answers"]["A"]["facts"]}
    target = facts.get(item["fact_id"]) if item["fact_id"] else None
    claims = judged["answers"]["A"]["claims"]
    return {"target_status": target["status"] if target else None,
            "target_citation_status": target["citation_status"] if target else None,
            "unsupported_claims": sum(1 for claim in claims
                                      if claim["support_status"] == "unsupported"),
            "contradicted_claims": sum(1 for claim in claims
                                       if claim["support_status"] == "contradicted")}


def run(*, check_only: bool = False) -> dict:
    items = build_items()
    cells = build_cells(items)
    config = LLMConfig.from_env(ROOT / ".env")
    cache = _V3Cache(CACHE)
    failures: list = []
    clients = {model_key: OpenAIChatCompletionsClient(
        replace(config, model=model, timeout_seconds=REQUEST_TIMEOUT_SECONDS))
        for model_key, model in MODELS.items()}
    executed = []
    for cell in cells:
        item = items[cell["item_id"]]
        result = execute_cell(cell, item, cache, clients, failures, check_only=check_only)
        if result.get("checks") and result["checks"]["edited"]:
            result["secondary_judge"] = judge_edited(item, result["parsed"]["revised_answer"],
                                                     cache, clients["stronger"], failures,
                                                     check_only=check_only)
        else:
            result["secondary_judge"] = None
        executed.append(result)
        print(f"{cell['cell_id']} -> "
              f"{result.get('parsed', {}).get('execution_status') if result.get('parsed') else 'FAILED'}",
              flush=True)
    document = {
        "schema_version": 1,
        "version": VERSION,
        "status": "complete",
        "scope_note": ("Mechanism / H3 diagnostic: externally injected action decisions with execution. "
                       "Decision adherence is deterministic and primary; semantic correctness is "
                       "secondary (same-family judge + blinded human sheet). MISSING n=2; no population "
                       "inference."),
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": _sha256(PREREG)},
        "dataset": {
            "primary_items": list(PRIMARY_ITEMS), "control_items": list(CONTROL_ITEMS),
            "gold_decisions": GOLD_DECISION,
            "items": [{key: items[item_id][key] for key in
                       ("item_id", "kind", "fact_id", "case_id", "proposition", "gold_decision")}
                      for item_id in ITEM_IDS],
        },
        "design": {"models": MODELS, "decisions": DECISIONS, "replicates": REPLICATES,
                   "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE, "cells": len(cells),
                   "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS, "blind_seed": BLIND_SEED},
        "frozen_inputs": {relative: _sha256(ROOT / relative) for relative in (
            "eval/decision_execution_coupling_v1_preregistration.md",
            "eval/results/semantic_gap_discrimination_v1_results.json",
            "eval/results/task_conditioned_action_v1_results.json",
            "eval/results/oracle_repair_v1_results.json",
            "eval/results/oracle_repair_v1_human_scored.json",
            "eval/results/measurement_validity_cleaned_cohort.json",
            "eval/results/measurement_validity_audit.json",
            "eval/results/measurement_validity_audit_v2.json",
            "eval/results/repairability_stage_summary.md",
            "eval/validation/broad_atomic_facts_validation_v1.json",
            "eval/validation/broad_queries_validation_v1.json",
        )},
        "cells": [{key: cell[key] for key in
                   ("cell_id", "item_id", "kind", "model_key", "model", "decision", "replicate",
                    "prompt_config_hash", "cache_key", "parsed", "provider_usage",
                    "latency_seconds", "error", "checks", "secondary_judge")
                   if key in cell} for cell in executed],
        "aggregates": summarize(executed),
        "human_review": {"status": "pending", "sheet_path": str(HUMAN_SHEET.relative_to(ROOT)),
                         "blind_seed": BLIND_SEED, "mapping": human_mapping(executed)},
        "failures": failures,
    }
    if not check_only:
        _write(RESULTS, document)
        SUMMARY.write_text(render_summary(document), encoding="utf-8")
        STAGE_SUMMARY.write_text(render_stage_summary(document), encoding="utf-8")
        HUMAN_SHEET.write_text(render_human_sheet(document, items), encoding="utf-8")
    return document


def human_mapping(executed: list[dict]) -> list[dict]:
    shuffled = list(executed)
    random.Random(BLIND_SEED).shuffle(shuffled)
    return [{"blind_id": f"X{index:02d}", "cell_id": cell["cell_id"], "item_id": cell["item_id"],
             "decision": cell["decision"], "model_key": cell["model_key"],
             "replicate": cell["replicate"]}
            for index, cell in enumerate(shuffled, 1)]


def _cells_for(executed: list[dict], model_key: str, item_id: str | None = None,
               decision: str | None = None) -> list[dict]:
    return [cell for cell in executed if cell.get("checks") and cell["model_key"] == model_key
            and (item_id is None or cell["item_id"] == item_id)
            and (decision is None or cell["decision"] == decision)]


def _decision_block(executed: list[dict], model_key: str, decision: str) -> dict:
    cells = _cells_for(executed, model_key, decision=decision)
    primary = [cell for cell in cells if cell["item_id"] in PRIMARY_ITEMS]
    edited = [cell for cell in primary if cell["checks"]["edited"]]
    adherent = [cell for cell in primary if cell["checks"]["adherence"]]
    overrides = [cell for cell in primary if cell["checks"]["explicit_override"]]
    refusals = [cell for cell in primary if cell["checks"]["refused"]]
    judged = [cell for cell in edited if cell.get("secondary_judge")]
    return {
        "primary_cells": len(primary),
        "adherence": len(adherent),
        "explicit_overrides": len(overrides),
        "refusals": len(refusals),
        "actual_repairs": len(edited),
        "secondary_judged": len(judged),
        "secondary_target_correct": sum(
            1 for cell in judged
            if cell["item_id"] in PRIMARY_ITEMS
            and cell["secondary_judge"]["target_status"] == "covered"
            and cell["secondary_judge"]["target_citation_status"] == "supported"),
        "secondary_unsupported_claims": sum(cell["secondary_judge"]["unsupported_claims"]
                                            for cell in judged),
        "secondary_contradicted_claims": sum(cell["secondary_judge"]["contradicted_claims"]
                                             for cell in judged),
        "items": {item_id: {
            "labels": [f"{cell['checks']['status']}:{'edit' if cell['checks']['edited'] else 'noop'}"
                       for cell in primary if cell["item_id"] == item_id],
            "adherence": sum(1 for cell in primary if cell["item_id"] == item_id
                             and cell["checks"]["adherence"]),
            "overrides": sum(1 for cell in primary if cell["item_id"] == item_id
                             and cell["checks"]["explicit_override"]),
        } for item_id in PRIMARY_ITEMS},
    }


def summarize(executed: list[dict]) -> dict:
    output = {}
    for model_key in MODELS:
        blocks = {decision: _decision_block(executed, model_key, decision)
                  for decision in DECISIONS}
        d1_repair_rate = blocks["D1"]["actual_repairs"] / 6
        d23_noop = sum(blocks[decision]["adherence"] for decision in ("D2", "D3")) / 12
        overrides = sum(blocks[decision]["explicit_overrides"] for decision in DECISIONS) / 18
        oa = d1_repair_rate >= 5 / 6 and d23_noop >= 11 / 12 and overrides <= 1 / 18
        ob = d1_repair_rate <= 3 / 6 or d23_noop <= 10 / 12 or overrides >= 3 / 18
        ap_d1 = _cells_for(executed, model_key, item_id="P-VAL-001-050-F02", decision="D1")
        u_d1 = _cells_for(executed, model_key, item_id="U-039-01", decision="D1")
        blocks["controls"] = {
            "already_present_D1_unnecessary_repairs": sum(1 for cell in ap_d1
                                                          if cell["checks"]["edited"]),
            "already_present_D1_cells": len(ap_d1),
            "unsupported_D1_insertions": sum(1 for cell in u_d1 if cell["checks"]["edited"]),
            "unsupported_D1_cells": len(u_d1),
            "already_present_adherence": {decision: sum(
                1 for cell in _cells_for(executed, model_key,
                                         item_id="P-VAL-001-050-F02", decision=decision)
                if cell["checks"]["adherence"]) for decision in DECISIONS},
            "unsupported_adherence": {decision: sum(
                1 for cell in _cells_for(executed, model_key, item_id="U-039-01",
                                         decision=decision)
                if cell["checks"]["adherence"]) for decision in DECISIONS},
        }
        output[model_key] = {"decisions": blocks, "rates": {
            "d1_repair_rate": d1_repair_rate, "d23_noop_rate": d23_noop,
            "override_rate": overrides},
            "OA": oa, "OB": ob}
    oc = ((output["current"]["OA"] and output["stronger"]["OB"])
          or (output["current"]["OB"] and output["stronger"]["OA"]))
    od = (output["current"]["OA"] and output["stronger"]["OA"]
          and output["current"]["decisions"]["controls"]["unsupported_D1_insertions"] >= 2
          and output["stronger"]["decisions"]["controls"]["unsupported_D1_insertions"] >= 2)
    if oc:
        overall = "C"
    elif od:
        overall = "D"
    elif output["current"]["OA"] and output["stronger"]["OA"]:
        overall = "A"
    elif output["current"]["OB"] or output["stronger"]["OB"]:
        overall = "B"
    else:
        overall = "mixed"
    output["outcomes"] = {"OC_model_split": oc, "OD_controllable_but_safety_critical": od,
                          "overall": overall}
    return output


def render_summary(document: dict) -> str:
    aggregates = document["aggregates"]
    lines = ["# Decision-Execution Coupling V1 - Summary (Mechanism / H3)", "",
             "> " + document["scope_note"], "",
             f"- status: {document['status']}",
             f"- preregistration sha256: `{document['preregistration']['sha256'][:16]}`",
             f"- primary items: {document['dataset']['primary_items']}; controls: "
             f"{document['dataset']['control_items']}",
             f"- design: {document['design']['cells']} cells = 4 items x 2 models x 3 decisions x "
             f"{document['design']['replicates']} replicates", ""]
    for model_key in MODELS:
        block = aggregates[model_key]
        lines += [f"## {model_key}", "",
                  "| injected decision | adherence | overrides | actual repair | secondary target correct |",
                  "|---|---:|---:|---:|---:|"]
        for decision in DECISIONS:
            entry = block["decisions"][decision]
            lines.append(f"| {decision} | {entry['adherence']}/{entry['primary_cells']} | "
                         f"{entry['explicit_overrides']}/{entry['primary_cells']} | "
                         f"{entry['actual_repairs']}/{entry['primary_cells']} | "
                         f"{entry['secondary_target_correct']}/{entry['actual_repairs']} |")
        lines += ["", f"- rates: {block['rates']}",
                  f"- OA (strong coupling): {block['OA']}; OB (weak coupling): {block['OB']}",
                  f"- controls: {block['decisions']['controls']}", "",
                  "### Per-item decision labels (status:edit/noop)", ""]
        for decision in DECISIONS:
            lines.append(f"- {decision}: " + json.dumps(
                block["decisions"][decision]["items"], ensure_ascii=False))
        lines.append("")
    lines += ["## Preregistered outcome mapping", "",
              f"- OC model split: {aggregates['outcomes']['OC_model_split']}",
              f"- OD controllable but safety-critical: "
              f"{aggregates['outcomes']['OD_controllable_but_safety_critical']}",
              f"- overall: **{aggregates['outcomes']['overall']}**", "",
              "## Failures", f"- {document['failures']}", ""]
    return "\n".join(lines)


def render_stage_summary(document: dict) -> str:
    aggregates = document["aggregates"]
    outcomes = aggregates["outcomes"]
    lines = ["# Mechanism H3 Stage Summary - Decision-Execution Coupling", "",
             "**Status: Mechanism H3 diagnostic = COMPLETE** (2026-09-26). No routing, no production "
             "change.", "",
             "Research chain: `Validate ✅ → Repairability ✅ → H1 ✅ → H2 ✅ → H3 → Routing`. "
             "This document records the externally injected decision probe. No follow-up experiment is "
             "executed.", "",
             "## Frozen setup", "",
             "- Preregistration: `eval/decision_execution_coupling_v1_preregistration.md` "
             f"(sha256 `{document['preregistration']['sha256'][:16]}…`).",
             "- Primary items: the two human-confirmed genuine errors; controls: one already-present item "
             "and one unsupported sham.",
             "- Injected decisions: D1 `REPAIR_NEEDED`, D2 `NO_CHANGE_ALREADY_PRESENT`, D3 "
             "`NO_CHANGE_UNSUPPORTED`; identical wording across models.",
             "- Design: 4 items x 2 models x 3 decisions x 3 replicates = 72 execution calls.",
             "", "## Results", ""]
    for model_key in MODELS:
        block = aggregates[model_key]
        lines += [f"### {model_key}",
                  f"- rates: {block['rates']}",
                  f"- OA: {block['OA']}; OB: {block['OB']}",
                  f"- controls: {block['decisions']['controls']}", ""]
    lines += ["## Preregistered outcome mapping", "",
              f"- OC model split: **{outcomes['OC_model_split']}**",
              f"- OD controllable but safety-critical: "
              f"**{outcomes['OD_controllable_but_safety_critical']}**",
              f"- overall: **{outcomes['overall']}**", "",
              "## Interpretation", ""]
    if outcomes["overall"] in ("A", "D"):
        lines += ["- Explicit decisions can control generation; the H2 dissociation is attributable to "
                  "task framing generating different decision states."]
    elif outcomes["overall"] in ("B", "C"):
        lines += ["- Generation re-evaluates and can override injected decisions; a classifier -> "
                  "executor pipeline is not a reliable control layer."]
    else:
        lines += ["- Mixed evidence; report descriptively."]
    lines += ["- Decision adherence and answer quality are reported separately; high adherence to a "
              "wrong injected decision is a coupling result, not an H3 failure.",
              "- MISSING n = 2; mechanism diagnostic only.", "",
              "## Next step", "",
              "- Depends on the overall mapping; no automatic next experiment is executed.", ""]
    return "\n".join(lines)


def render_human_sheet(document: dict, items: dict[str, dict]) -> str:
    mapping = document["human_review"]["mapping"]
    cell_by_id = {cell["cell_id"]: cell for cell in document["cells"]}
    lines = ["# Decision-Execution Coupling V1 - Blinded Human Sheet", "",
             "Injected decisions are shown (they are the condition); model identities are hidden. For "
             "each output verify: (1) decision adherence, (2) semantic correctness of any edit, "
             "(3) any safety-relevant insertion.", "",
             "## Item appendix", ""]
    for item_id in ITEM_IDS:
        item = items[item_id]
        lines += [f"### {item_id} ({item['kind']}; gold decision {item['gold_decision']})", "",
                  f"- question: {item['query']}",
                  f"- proposition: {item['proposition']}",
                  f"- baseline answer: {item['baseline_answer']}",
                  "- frozen evidence:", ""]
        for source in item["sources"]:
            heading = " > ".join(source.heading_path) or "Document introduction"
            lines += [f"[{source.citation_id}] {source.title} :: {heading}", source.text, ""]
    lines += ["## Outputs", ""]
    for entry in mapping:
        cell = cell_by_id[entry["cell_id"]]
        parsed = cell.get("parsed")
        lines += [f"## {entry['blind_id']} ({entry['item_id']}, injected {entry['decision']})", "",
                  f"- output: {json.dumps(parsed, ensure_ascii=False) if parsed else 'FAILED'}",
                  "- adherence_correct: ", "- semantic_correctness: ", "- safety_note: ", ""]
    lines += ["## Mapping status", "",
              "Model mapping is stored in `eval/results/decision_execution_coupling_v1_results.json` and "
              "must only be opened after scoring.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild from cache without any API call")
    args = parser.parse_args(argv)
    document = run(check_only=args.check)
    print(json.dumps({"status": document["status"],
                      "outcomes": document["aggregates"]["outcomes"],
                      "current": {"rates": document["aggregates"]["current"]["rates"],
                                  "OA": document["aggregates"]["current"]["OA"],
                                  "OB": document["aggregates"]["current"]["OB"]},
                      "stronger": {"rates": document["aggregates"]["stronger"]["rates"],
                                   "OA": document["aggregates"]["stronger"]["OA"],
                                   "OB": document["aggregates"]["stronger"]["OB"]},
                      "failures": document["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
