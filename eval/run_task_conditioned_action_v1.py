"""Task-Conditioned Action V1 (Mechanism / H2).

Same frozen 27-item probe as H1, same models, same evidence/answer/proposition; only the instruction
framing changes (Frame B: neutral action decision; Frame C: repair intent without editing). No patch, no
revised answer, no citations, no URL. Frame A is the frozen H1 classification result, reused without new
calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from eval.run_answer_eval import _V3Cache, _sha256, _stable_hash
from eval.run_semantic_gap_discrimination_v1 import (build_dataset as build_h1_dataset,
                                                     validate_dataset as validate_h1_dataset)
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
H1_RESULTS = ROOT / "eval/results/semantic_gap_discrimination_v1_results.json"
H1_PREREG = ROOT / "eval/semantic_gap_discrimination_v1_preregistration.md"
REPAIR_SCORED = ROOT / "eval/results/oracle_repair_v1_human_scored.json"
PREREG = ROOT / "eval/task_conditioned_action_v1_preregistration.md"
CACHE = ROOT / "cache/task_conditioned_action_v1_cache.json"
RESULTS = ROOT / "eval/results/task_conditioned_action_v1_results.json"
SUMMARY = ROOT / "eval/results/task_conditioned_action_v1_summary.md"
STAGE_SUMMARY = ROOT / "eval/results/mechanism_h2_stage_summary.md"

VERSION = "task-conditioned-action-v1"
MODELS = {"current": "deepseek-v4-flash", "stronger": "deepseek-v4-pro"}
FRAMES = ("B", "C")
REPLICATES = 3
MAX_TOKENS = 200
TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 120.0
MISSING_ITEMS = ("M-VAL-001-039-F02", "M-VAL-001-050-F01")
KEY_ITEMS = MISSING_ITEMS

FRAME_DECISIONS = {
    "B": ("REPAIR_NEEDED", "NO_CHANGE_ALREADY_PRESENT", "NO_CHANGE_UNSUPPORTED"),
    "C": ("WOULD_REPAIR", "WOULD_NOT_REPAIR_ALREADY_PRESENT", "WOULD_NOT_REPAIR_UNSUPPORTED"),
}
CANONICAL = {
    "MISSING": "REPAIR", "REPAIR_NEEDED": "REPAIR", "WOULD_REPAIR": "REPAIR",
    "ALREADY_PRESENT": "NO_CHANGE_PRESENT", "NO_CHANGE_ALREADY_PRESENT": "NO_CHANGE_PRESENT",
    "WOULD_NOT_REPAIR_ALREADY_PRESENT": "NO_CHANGE_PRESENT",
    "UNSUPPORTED": "NO_CHANGE_UNSUPPORTED", "NO_CHANGE_UNSUPPORTED": "NO_CHANGE_UNSUPPORTED",
    "WOULD_NOT_REPAIR_UNSUPPORTED": "NO_CHANGE_UNSUPPORTED",
}
GOLD_ACTION = {"MISSING": "REPAIR", "ALREADY_PRESENT": "NO_CHANGE_PRESENT",
               "UNSUPPORTED": "NO_CHANGE_UNSUPPORTED"}
ACTION_STATES = ("REPAIR", "NO_CHANGE_PRESENT", "NO_CHANGE_UNSUPPORTED")

FRAME_SYSTEMS = {
    "B": (
        "You are deciding whether a baseline GitHub policy answer requires repair for one atomic "
        "proposition. You receive the question, the baseline answer, the frozen evidence (sources "
        "S1..Sn), and the atomic proposition. Decide the required action:\n"
        "- REPAIR_NEEDED: the frozen evidence supports the proposition, and the baseline answer does "
        "not correctly express it (missing, incomplete, or incorrect).\n"
        "- NO_CHANGE_ALREADY_PRESENT: the frozen evidence supports the proposition, and the baseline "
        "answer already expresses it semantically; paraphrase counts.\n"
        "- NO_CHANGE_UNSUPPORTED: the frozen evidence does not support the proposition.\n"
        "Do not generate, patch, rewrite, or propose any answer text; do not insert citations or URLs. "
        "Make the decision only. Reply with JSON only: "
        '{"decision":"REPAIR_NEEDED|NO_CHANGE_ALREADY_PRESENT|NO_CHANGE_UNSUPPORTED",'
        '"evidence_source_ids":["S1"],"brief_reason":"<= 40 words"}'
    ),
    "C": (
        "You are in an answer-repair task for one atomic proposition. You receive the question, the "
        "baseline answer, the frozen evidence (sources S1..Sn), and the atomic proposition. Decide "
        "whether the baseline answer would need to be modified, but do NOT produce any modification. "
        "Decide the action:\n"
        "- WOULD_REPAIR: the frozen evidence supports the proposition, and the baseline answer does not "
        "correctly express it (missing, incomplete, or incorrect), so a repair would be needed.\n"
        "- WOULD_NOT_REPAIR_ALREADY_PRESENT: the frozen evidence supports the proposition, and the "
        "baseline answer already expresses it semantically; paraphrase counts.\n"
        "- WOULD_NOT_REPAIR_UNSUPPORTED: the frozen evidence does not support the proposition.\n"
        "Never output a patch, a revised answer, inserted citations, or any URL. Reply with JSON only: "
        '{"decision":"WOULD_REPAIR|WOULD_NOT_REPAIR_ALREADY_PRESENT|WOULD_NOT_REPAIR_UNSUPPORTED",'
        '"evidence_source_ids":["S1"],"brief_reason":"<= 40 words"}'
    ),
}
FRAME_INSTRUCTION = {
    "B": ("Decision task: decide the required action for this proposition. Do not modify the answer. "
          "Return only the JSON object."),
    "C": ("Repair-intent task: decide whether the answer would need modification, without producing any "
          "modification. Return only the JSON object."),
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def context_block(item: dict) -> str:
    return ("Question:\n" + item["query"] +
            "\n\nBaseline answer:\n" + item["baseline_answer"] +
            "\n\nFrozen evidence:\n" + item["evidence_text"] +
            "\n\nAtomic proposition:\n" + item["proposition"])


def build_messages(item: dict, frame: str) -> list[dict]:
    return [{"role": "system", "content": FRAME_SYSTEMS[frame]},
            {"role": "user", "content": context_block(item) + "\n\n" + FRAME_INSTRUCTION[frame]}]


def parse_decision(raw: str, frame: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    decision = str(data["decision"]).strip().upper()
    if decision not in FRAME_DECISIONS[frame]:
        raise ValueError(f"invalid decision for frame {frame}: {decision}")
    source_ids = data.get("evidence_source_ids") or []
    if not isinstance(source_ids, list):
        raise ValueError("evidence_source_ids must be a list")
    reason = str(data.get("brief_reason", ""))[:400]
    return {"decision": decision, "evidence_source_ids": [str(value) for value in source_ids],
            "brief_reason": reason, "reason_words": len(reason.split())}


def canonical(label: str | None) -> str | None:
    return CANONICAL.get(label) if label else None


def load_frozen_dataset() -> tuple[dict, dict]:
    dataset = build_h1_dataset()
    validate_h1_dataset(dataset)
    h1 = _json(H1_RESULTS)
    fields = ("item_id", "gold", "source", "fact_id", "case_id", "proposition")
    projected = [{key: item[key] for key in fields} for item in dataset["items"]]
    h1_projected = [{key: item[key] for key in fields} for item in h1["dataset"]["items"]]
    if projected != h1_projected:
        raise ValueError("H2 dataset does not match the frozen H1 27-item probe set")
    if len(projected) != 27:
        raise ValueError("H2 must reuse the 27-item H1 probe set")
    return dataset, h1


def build_cells(dataset: dict) -> list[dict]:
    cells = []
    for item in dataset["items"]:
        for model_key, model in MODELS.items():
            for frame in FRAMES:
                for replicate in range(1, REPLICATES + 1):
                    cells.append({"cell_id": f"{item['item_id']}::{model_key}::{frame}::r{replicate}",
                                  "item_id": item["item_id"], "gold": item["gold"],
                                  "model_key": model_key, "model": model, "frame": frame,
                                  "replicate": replicate})
    return cells


def execute_cell(cell: dict, item: dict, cache: _V3Cache, clients: dict, failures: list,
                 *, check_only: bool) -> dict:
    messages = build_messages(item, cell["frame"])
    prompt_hash = _stable_hash({"messages": messages, "temperature": TEMPERATURE,
                                "max_tokens": MAX_TOKENS, "version": VERSION})
    key = _stable_hash({"version": VERSION, "model": cell["model"], "item_id": cell["item_id"],
                        "frame": cell["frame"], "replicate": cell["replicate"],
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
            cached = {"kind": "action", "raw": raw,
                      "parsed": parse_decision(raw, cell["frame"]), "provider_usage": usage,
                      "latency_seconds": perf_counter() - started, "raw_hash": _stable_hash(raw)}
        except Exception as error:
            cached = {"kind": "action", "raw": None, "parsed": None,
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"kind": "action", "cell_id": cell["cell_id"],
                             "error": cached["error"]})
        cache.set(key, cached)
    return {**cell, "prompt_config_hash": prompt_hash, "cache_key": key, **cached}


def _modal(labels: list[str], allowed: tuple[str, ...]) -> str | None:
    for label in allowed:
        if labels.count(label) >= 2:
            return label
    return None


def _consistency(labels: list[str]) -> str:
    if len(set(labels)) == 1 and labels and labels[0] != "FAILED":
        return "3/3"
    if any(labels.count(label) >= 2 for label in set(labels)):
        return "2/3"
    return "1/3"


def _frame_rows(dataset: dict, cells: list[dict], h1: dict) -> dict:
    gold_by_item = {item["item_id"]: item["gold"] for item in dataset["items"]}
    rows: dict[tuple[str, str], dict] = {}
    for model_key in MODELS:
        for row in h1["aggregates"][model_key]["items"]:
            states = [canonical(label) if label in CANONICAL else None for label in row["labels"]]
            rows[(model_key, row["item_id"], "A")] = {
                "labels": row["labels"], "modal_label": row["modal"],
                "states": states, "modal_state": canonical(row["modal"]),
                "consistency": row["consistency"], "gold": gold_by_item[row["item_id"]]}
    for cell in cells:
        entry = rows.setdefault((cell["model_key"], cell["item_id"], cell["frame"]), {
            "labels": [], "states": [], "gold": gold_by_item[cell["item_id"]]})
        entry["labels"].append(cell["parsed"]["decision"] if cell.get("parsed") else "FAILED")
    for (model_key, item_id, frame), entry in rows.items():
        if frame == "A":
            continue
        entry["labels"].sort()
        entry["states"] = [canonical(label) for label in entry["labels"]]
        entry["modal_label"] = _modal(entry["labels"], FRAME_DECISIONS[frame])
        entry["modal_state"] = canonical(entry["modal_label"])
        entry["consistency"] = _consistency(entry["labels"])
    for key, entry in rows.items():
        entry["labels"] = list(entry["labels"])
    return rows


def _compute_transitions(rows: dict, dataset: dict, model_key: str, target_frame: str) -> dict:
    table = {source: {dest: 0 for dest in ACTION_STATES + ("UNRESOLVED",)}
             for source in ACTION_STATES + ("UNRESOLVED",)}
    for item in dataset["items"]:
        source = rows[(model_key, item["item_id"], "A")]["modal_state"] or "UNRESOLVED"
        dest = rows[(model_key, item["item_id"], target_frame)]["modal_state"] or "UNRESOLVED"
        table[source][dest] += 1
    return table


def _action_accuracy(rows: dict, dataset: dict, model_key: str, frame: str) -> dict:
    matrix = {gold: {action: 0 for action in ACTION_STATES + ("UNRESOLVED",)}
              for gold in ACTION_STATES}
    per_item = []
    for item in dataset["items"]:
        entry = rows[(model_key, item["item_id"], frame)]
        predicted = entry["modal_state"] or "UNRESOLVED"
        gold_action = GOLD_ACTION[item["gold"]]
        matrix[gold_action][predicted] += 1
        per_item.append({"item_id": item["item_id"], "gold": gold_action,
                         "predicted": predicted, "labels": entry["labels"]})
    recall = {}
    for gold_action in ACTION_STATES:
        total = sum(matrix[gold_action].values())
        correct = matrix[gold_action][gold_action]
        recall[gold_action] = {"numerator": correct, "denominator": total,
                               "recall": correct / total if total else None}
    return {"matrix": matrix, "per_class_recall": recall, "per_item": per_item}


def _frame_consistency(rows: dict, dataset: dict, model_key: str) -> dict:
    counts = {"consistent": 0, "two_states": 0, "three_states": 0}
    flips = []
    for item in dataset["items"]:
        states = [rows[(model_key, item["item_id"], frame)]["modal_state"]
                  for frame in ("A", "B", "C")]
        distinct = {state for state in states if state}
        if None in states:
            category = "unresolved"
        elif len(distinct) == 1:
            category = "consistent"
        elif len(distinct) == 2:
            category = "two_states"
        else:
            category = "three_states"
        if category == "unresolved":
            counts.setdefault("unresolved", 0)
            counts["unresolved"] += 1
        else:
            counts[category] += 1
        flips.append({"item_id": item["item_id"], "states": states, "category": category})
    return {"counts": counts, "items": flips}


def _replicate_consistency(rows: dict, dataset: dict, model_key: str) -> dict:
    counts = {frame: {"3/3": 0, "2/3": 0, "1/3": 0} for frame in ("A", "B", "C")}
    for item in dataset["items"]:
        for frame in ("A", "B", "C"):
            counts[frame][rows[(model_key, item["item_id"], frame)]["consistency"]] += 1
    return counts


def _oracle_refusals() -> dict:
    scored = _json(REPAIR_SCORED)
    refusals: dict[tuple[str, str], bool] = {}
    for entry in scored["unblinded"]["per_blind"]:
        key = (entry["model_key"], entry["fact_id"])
        if entry["class"] == "genuine_no_repair":
            refusals[key] = True
        else:
            refusals.setdefault(key, False)
    return refusals


def _outcomes(rows: dict, dataset: dict, refusals: dict) -> dict:
    def states(model_key: str, item_id: str, frame: str):
        return rows[(model_key, item_id, frame)]

    missing_facts = {"M-VAL-001-039-F02": "VAL-001-039-F02",
                     "M-VAL-001-050-F01": "VAL-001-050-F01"}
    oa_items = []
    for item_id, fact_id in missing_facts.items():
        entry_a = states("current", item_id, "A")
        entry_b = states("current", item_id, "B")
        entry_c = states("current", item_id, "C")
        if (entry_a["modal_state"] == "REPAIR"
                and (entry_b["modal_state"] != "REPAIR" or entry_c["modal_state"] != "REPAIR")
                and refusals.get(("current", fact_id))):
            oa_items.append(item_id)
    oa = bool(oa_items)
    ob = all(states("current", item_id, frame)["modal_state"] == "REPAIR"
             for item_id in MISSING_ITEMS for frame in ("A", "B", "C")) \
        and any(refusals.get(("current", fact_id)) for fact_id in missing_facts.values())
    stronger_050 = states("stronger", "M-VAL-001-050-F01", "A")["modal_state"] != "REPAIR" \
        and (states("stronger", "M-VAL-001-050-F01", "B")["modal_state"] == "REPAIR"
             or states("stronger", "M-VAL-001-050-F01", "C")["modal_state"] == "REPAIR") \
        and not refusals.get(("stronger", "VAL-001-050-F01"))
    oc = bool(stronger_050)
    od = any(rows[(model_key, item_id, frame)]["modal_state"] is None
             for model_key in MODELS for item_id in MISSING_ITEMS for frame in ("A", "B", "C"))
    if oa:
        overall = "A"
    elif ob:
        overall = "B"
    elif oc:
        overall = "C"
    elif od:
        overall = "D"
    else:
        overall = "no pattern"
    return {"OA_current_framing_shift": oa, "OA_items": oa_items,
            "OB_action_correct_but_generation_failed": ob,
            "OC_stronger_framing_shift": oc, "OD_unstable": od, "overall": overall}


def summarize(dataset: dict, cells: list[dict], h1: dict) -> dict:
    rows = _frame_rows(dataset, cells, h1)
    refusals = _oracle_refusals()
    output = {"refusals": {f"{model}|{fact}": value
                           for (model, fact), value in sorted(refusals.items())}}
    for model_key in MODELS:
        output[model_key] = {
            "transitions_A_to_B": _compute_transitions(rows, dataset, model_key, "B"),
            "transitions_A_to_C": _compute_transitions(rows, dataset, model_key, "C"),
            "frame_consistency": _frame_consistency(rows, dataset, model_key),
            "replicate_consistency": _replicate_consistency(rows, dataset, model_key),
            "action_accuracy": {frame: _action_accuracy(rows, dataset, model_key, frame)
                                for frame in ("A", "B", "C")},
            "key_cases": {item_id: {frame: {"labels": rows[(model_key, item_id, frame)]["labels"],
                                            "modal": rows[(model_key, item_id, frame)]["modal_state"],
                                            "consistency": rows[(model_key, item_id, frame)]
                                            ["consistency"]}
                                    for frame in ("A", "B", "C")}
                          for item_id in KEY_ITEMS},
        }
    output["outcomes"] = _outcomes(rows, dataset, refusals)
    return output


def run(*, check_only: bool = False) -> dict:
    dataset, h1 = load_frozen_dataset()
    cells = build_cells(dataset)
    config = LLMConfig.from_env(ROOT / ".env")
    cache = _V3Cache(CACHE)
    failures: list = []
    clients = {model_key: OpenAIChatCompletionsClient(
        replace(config, model=model, timeout_seconds=REQUEST_TIMEOUT_SECONDS))
        for model_key, model in MODELS.items()}
    executed = []
    for cell in cells:
        item = next(entry for entry in dataset["items"] if entry["item_id"] == cell["item_id"])
        result = execute_cell(cell, item, cache, clients, failures, check_only=check_only)
        executed.append(result)
        print(f"{cell['cell_id']} -> "
              f"{result.get('parsed', {}).get('decision') if result.get('parsed') else 'FAILED'}",
              flush=True)
    document = {
        "schema_version": 1,
        "version": VERSION,
        "status": "complete",
        "scope_note": ("Mechanism / H2 diagnostic: action decision without generation under three framings "
                       "(A frozen classification, B neutral action decision, C repair intent without "
                       "editing). No patch, revised answer, citation, or URL is produced. MISSING n=2; no "
                       "population inference."),
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": _sha256(PREREG)},
        "dataset": {
            "source": str(H1_RESULTS.relative_to(ROOT)),
            "reused_from_h1": True,
            "composition": h1["dataset"]["composition"],
            "items": h1["dataset"]["items"],
        },
        "design": {"models": MODELS, "frames": {"A": "frozen_h1", "B": "action_decision",
                                                "C": "repair_intent_no_edit"},
                   "replicates": REPLICATES, "max_tokens": MAX_TOKENS,
                   "temperature": TEMPERATURE, "cells": len(cells),
                   "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS},
        "frozen_inputs": {relative: _sha256(ROOT / relative) for relative in (
            "eval/task_conditioned_action_v1_preregistration.md",
            "eval/semantic_gap_discrimination_v1_preregistration.md",
            "eval/results/semantic_gap_discrimination_v1_results.json",
            "eval/results/oracle_repair_v1_results.json",
            "eval/results/oracle_repair_v1_human_scored.json",
            "eval/results/mechanism_h1_stage_summary.md",
            "eval/results/measurement_validity_cleaned_cohort.json",
            "eval/results/measurement_validity_audit.json",
            "eval/results/measurement_validity_audit_v2.json",
            "eval/results/repairability_stage_summary.md",
            "eval/validation/broad_atomic_facts_validation_v1.json",
            "eval/validation/broad_queries_validation_v1.json",
        )},
        "cells": [{key: cell[key] for key in
                   ("cell_id", "item_id", "gold", "model_key", "model", "frame", "replicate",
                    "prompt_config_hash", "cache_key", "parsed", "provider_usage",
                    "latency_seconds", "error") if key in cell} for cell in executed],
        "aggregates": summarize(dataset, executed, h1),
        "failures": failures,
    }
    if not check_only:
        _write(RESULTS, document)
        SUMMARY.write_text(render_summary(document), encoding="utf-8")
        STAGE_SUMMARY.write_text(render_stage_summary(document), encoding="utf-8")
    return document


def _matrix_md(matrix: dict) -> list[str]:
    header = "| from \\ to | " + " | ".join(ACTION_STATES + ("UNRESOLVED",)) + " |"
    lines = [header, "|---|" + "---:|" * (len(ACTION_STATES) + 1)]
    for source in ACTION_STATES + ("UNRESOLVED",):
        row = matrix[source]
        lines.append(f"| {source} | " + " | ".join(str(row[dest]) for dest in
                                                   ACTION_STATES + ("UNRESOLVED",)) + " |")
    return lines


def render_summary(document: dict) -> str:
    aggregates = document["aggregates"]
    lines = ["# Task-Conditioned Action V1 - Summary (Mechanism / H2)", "",
             "> " + document["scope_note"], "",
             f"- status: {document['status']}",
             f"- preregistration sha256: `{document['preregistration']['sha256'][:16]}`",
             f"- dataset: reused H1 27-item probe ({document['dataset']['composition']})",
             f"- design: {document['design']['cells']} new cells = 27 items x 2 models x "
             f"2 frames (B, C) x {document['design']['replicates']} replicates; Frame A frozen",
             ""]
    for model_key in MODELS:
        block = aggregates[model_key]
        lines += [f"## {model_key}", "", "### A -> B (canonical action states)", ""]
        lines += _matrix_md(block["transitions_A_to_B"])
        lines += ["", "### A -> C (canonical action states)", ""]
        lines += _matrix_md(block["transitions_A_to_C"])
        lines += ["", "### Frame consistency (A/B/C canonical states)", "",
                  f"- {block['frame_consistency']['counts']}", ""]
        for frame in ("A", "B", "C"):
            accuracy = block["action_accuracy"][frame]
            recalls = ", ".join(
                f"{action} {accuracy['per_class_recall'][action]['numerator']}/"
                f"{accuracy['per_class_recall'][action]['denominator']}"
                for action in ACTION_STATES)
            lines.append(f"- Frame {frame} gold-action recall: {recalls}")
        lines += ["", "### Replicate consistency (3/3, 2/3, 1/3)", "",
                  f"- {block['replicate_consistency']}", "",
                  "### Key cases", ""]
        for item_id, frames in block["key_cases"].items():
            lines.append(f"- {item_id}: " + "; ".join(
                f"{frame}={'/'.join(entry['labels'])} -> {entry['modal']}"
                for frame, entry in frames.items()))
        lines.append("")
    outcomes = aggregates["outcomes"]
    lines += ["## Preregistered outcome rules", "",
              f"- OA current framing shift: {outcomes['OA_current_framing_shift']} "
              f"({outcomes['OA_items']})",
              f"- OB action correct but generation failed: {outcomes['OB_action_correct_but_generation_failed']}",
              f"- OC stronger framing shift: {outcomes['OC_stronger_framing_shift']}",
              f"- OD unstable: {outcomes['OD_unstable']}",
              f"- overall mapping: **{outcomes['overall']}**", "",
              "## Failures", f"- {document['failures']}", ""]
    return "\n".join(lines)


def render_stage_summary(document: dict) -> str:
    aggregates = document["aggregates"]
    outcomes = aggregates["outcomes"]
    lines = ["# Mechanism H2 Stage Summary - Task-Conditioned Action", "",
             "**Status: Mechanism H2 diagnostic = COMPLETE** (2026-09-26). No repair generation, no "
             "routing, no production change.", "",
             "Research chain: `Validate ✅ → Repairability ✅ → Mechanism H1 ✅ → Mechanism H2 → Routing`. "
             "This document records the H2 action-decision probe and the preregistered outcome mapping. It "
             "executes no follow-up experiment.", "",
             "## Frozen setup", "",
             "- Preregistration: `eval/task_conditioned_action_v1_preregistration.md` "
             f"(sha256 `{document['preregistration']['sha256'][:16]}…`).",
             "- Dataset: frozen H1 27-item probe reused item-by-item (asserted), `VAL-001-008-F02` "
             "excluded.",
             "- Frames: A = frozen H1 classification; B = neutral action decision; C = repair intent "
             "without editing. No patch/revised answer/citation/URL output.",
             "- Design: 27 items x 2 models x 2 frames x 3 replicates = 324 new calls; Frame A reused.",
             "",
             "## Results", ""]
    for model_key in MODELS:
        block = aggregates[model_key]
        lines += [f"### {model_key}",
                  f"- frame consistency: {block['frame_consistency']['counts']}",
                  f"- replicate consistency: {block['replicate_consistency']}",
                  "- gold-action recall: " + "; ".join(
                      f"Frame {frame}: " + ", ".join(
                          f"{action} "
                          f"{block['action_accuracy'][frame]['per_class_recall'][action]['numerator']}/"
                          f"{block['action_accuracy'][frame]['per_class_recall'][action]['denominator']}"
                          for action in ACTION_STATES)
                      for frame in ("A", "B", "C")),
                  "- 039-F02: " + "; ".join(
                      f"{frame}={'/'.join(entry['labels'])}->{entry['modal']}"
                      for frame, entry in block["key_cases"]["M-VAL-001-039-F02"].items()),
                  "- 050-F01: " + "; ".join(
                      f"{frame}={'/'.join(entry['labels'])}->{entry['modal']}"
                      for frame, entry in block["key_cases"]["M-VAL-001-050-F01"].items()),
                  ""]
    lines += ["## Preregistered outcome mapping", "",
              f"- OA (current framing shift): **{outcomes['OA_current_framing_shift']}** "
              f"({outcomes['OA_items']})",
              f"- OB (action correct, generation failed): "
              f"**{outcomes['OB_action_correct_but_generation_failed']}**",
              f"- OC (stronger framing shift): **{outcomes['OC_stronger_framing_shift']}**",
              f"- OD (unstable): **{outcomes['OD_unstable']}**",
              f"- overall: **{outcomes['overall']}**", "",
              "## Interpretation", ""]
    if outcomes["overall"] == "A":
        lines += ["- H2 is supported: task framing changes the current model's action policy even when "
                  "its semantic-state classification is correct."]
    elif outcomes["overall"] == "B":
        lines += ["- H2 is weakened at the action-decision layer: failures sit downstream, in the "
                  "execution/generation stage."]
    elif outcomes["overall"] == "C":
        lines += ["- Stronger-only framing shift observed; do not describe this as better reasoning."]
    elif outcomes["overall"] == "D":
        lines += ["- H2 unresolved: replicate instability; inspect instruction sensitivity."]
    else:
        lines += ["- No stable framing effect observed; report descriptively."]
    lines += ["- MISSING n = 2: mechanism diagnostic only; no population inference.",
              "- H3 (proposition-level entailment / evidence load) remains out of scope for this stage.", "",
              "## Next step", "",
              "- Recommended next branch depends on the overall mapping above; no automatic next "
              "experiment is executed.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild from cache without any API call")
    args = parser.parse_args(argv)
    document = run(check_only=args.check)
    print(json.dumps({"status": document["status"],
                      "outcomes": document["aggregates"]["outcomes"],
                      "current": {"frame_consistency":
                                  document["aggregates"]["current"]["frame_consistency"]["counts"]},
                      "stronger": {"frame_consistency":
                                   document["aggregates"]["stronger"]["frame_consistency"]["counts"]},
                      "failures": document["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
