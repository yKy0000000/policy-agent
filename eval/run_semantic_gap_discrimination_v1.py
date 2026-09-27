"""Semantic Gap Discrimination V1 (Mechanism / H1).

Proposition-level 3-way classification (MISSING / ALREADY_PRESENT / UNSUPPORTED) on frozen baseline
answers and frozen evidence. No repair generation, no rewriting, no routing, no production change.
Dataset: 2 human-confirmed MISSING + 19 human-confirmed ALREADY_PRESENT + 6 validated UNSUPPORTED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from eval.run_answer_eval import _V3Cache, _sha256, _stable_hash
from eval.run_oracle_repair_v1 import REPAIR_CASES
from src.generator import assign_evidence_sources, format_evidence
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
CLEANED_COHORT = ROOT / "eval/results/measurement_validity_cleaned_cohort.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
PREREG = ROOT / "eval/semantic_gap_discrimination_v1_preregistration.md"
CACHE = ROOT / "cache/semantic_gap_discrimination_v1_cache.json"
RESULTS = ROOT / "eval/results/semantic_gap_discrimination_v1_results.json"
SUMMARY = ROOT / "eval/results/semantic_gap_discrimination_v1_summary.md"

VERSION = "semantic-gap-discrimination-v1"
MODELS = {"current": "deepseek-v4-flash", "stronger": "deepseek-v4-pro"}
LABELS = ("MISSING", "ALREADY_PRESENT", "UNSUPPORTED")
REPLICATES = 3
MAX_TOKENS = 200
TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 120.0

MISSING_FACT_IDS = ("VAL-001-039-F02", "VAL-001-050-F01")
EXCLUDED_FACT_IDS = ("VAL-001-008-F02",)
CAVEAT_PRESENT_FACT_IDS = ("VAL-001-050-F05",)

CONTROL_PRESENT_FACT_IDS = ("VAL-001-039-F01", "VAL-001-050-F02")

UNSUPPORTED_ITEMS = (
    {"item_id": "U-039-01", "case_id": "VAL-001-039",
     "proposition": "GitHub's source-code offer expires one year after the Software release.",
     "markers": ("expire", "one year", "1 year", "expiry"),
     "source": "oracle_repair_sham",
     "validation": "frozen Oracle Repair V1 sham; non-entailment/non-contradiction review recorded"},
    {"item_id": "U-039-02", "case_id": "VAL-001-039",
     "proposition": ("GitHub must deliver the complete source code of open-source components within 30 "
                    "days of a written request."),
     "markers": ("30 days", "thirty days", "written request"),
     "source": "preregistered_alternate_sham",
     "validation": "no timeline sentence in any full-Top5 chunk"},
    {"item_id": "U-039-03", "case_id": "VAL-001-039",
     "proposition": "GitHub provides a written warranty for the Software's open-source components.",
     "markers": ("warrant",),
     "source": "new_validated",
     "validation": "no warranty sentence in the full Top5 (including Miscellanea)"},
    {"item_id": "U-039-04", "case_id": "VAL-001-039",
     "proposition": "The Software's open-source components are licensed under the MIT license.",
     "markers": ("mit license", "mit licence", "licensed under mit"),
     "source": "new_validated",
     "validation": "no license is named; only generic open source software license agreements"},
    {"item_id": "U-050-01", "case_id": "VAL-001-050",
     "proposition": ("GitHub must reimburse a violator's reasonable legal costs after the violation is "
                     "cured."),
     "markers": ("reimburse", "legal cost", "attorney", "fees"),
     "source": "oracle_repair_sham",
     "validation": "frozen Oracle Repair V1 sham; non-entailment/non-contradiction review recorded"},
    {"item_id": "U-050-02", "case_id": "VAL-001-050",
     "proposition": "GitHub must publish an annual compliance report for this Commitment.",
     "markers": ("compliance report", "annual report", "publish a report"),
     "source": "new_validated",
     "validation": "no reporting duty; the only publication is new editions of the commitment"},
)

CLASSIFIER_SYSTEM = (
    "You are a precise proposition-state classifier for GitHub policy answers. You receive a user "
    "question, a baseline answer, the frozen evidence (sources S1..Sn), and one atomic proposition. "
    "Classify the proposition into exactly one label:\n"
    "- MISSING: the frozen evidence supports the proposition, and the baseline answer does not "
    "semantically express it (including incomplete or incorrect expression).\n"
    "- ALREADY_PRESENT: the frozen evidence supports the proposition, and the baseline answer already "
    "expresses it semantically; paraphrase, compression, or merged expression counts; literal wording "
    "is not required.\n"
    "- UNSUPPORTED: the frozen evidence does not support the proposition; plausibility, topical "
    "relevance, or prior knowledge must not be accepted as support.\n"
    "Do not rewrite, repair, or improve the answer. Judge only the proposition's relation to the frozen "
    "evidence and to the baseline answer. Reply with JSON only: "
    '{"label":"MISSING|ALREADY_PRESENT|UNSUPPORTED","evidence_source_ids":["S1"],'
    '"answer_support":"brief semantic justification (<= 40 words)"}'
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_classification(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    label = str(data["label"]).strip().upper()
    if label not in LABELS:
        raise ValueError(f"invalid label: {label}")
    source_ids = data.get("evidence_source_ids") or []
    if not isinstance(source_ids, list):
        raise ValueError("evidence_source_ids must be a list")
    support = str(data.get("answer_support", ""))[:400]
    return {"label": label, "evidence_source_ids": [str(value) for value in source_ids],
            "answer_support": support}


def build_messages(item: dict) -> list[dict]:
    user = (
        "Question:\n" + item["query"] +
        "\n\nBaseline answer:\n" + item["baseline_answer"] +
        "\n\nFrozen evidence:\n" + item["evidence_text"] +
        "\n\nAtomic proposition:\n" + item["proposition"] +
        "\n\nReturn only the JSON object."
    )
    return [{"role": "system", "content": CLASSIFIER_SYSTEM},
            {"role": "user", "content": user}]


def _case_context(frozen: dict) -> dict:
    rubric = frozen["rubric"]
    queries = frozen["queries"]
    transfer = frozen["transfer"]
    utilization = frozen["utilization"]
    facts = {}
    for case in rubric["cases"]:
        for fact in case["facts"]:
            facts[fact["fact_id"]] = {**fact, "case_id": case["case_id"]}
    qmap = {case["case_id"]: case["query"] for case in queries["cases"]}
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    bge = {case_id: item["chunks"]
           for case_id, item in transfer["preparation"]["arms"]["bge_top5"].items()}
    contexts = {}
    for case_id in {fact["case_id"] for fact in facts.values()}:
        chunks = bge.get(case_id)
        if chunks is None or case_id not in rows:
            continue
        sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
        contexts[case_id] = {
            "query": qmap[case_id],
            "baseline_answer": rows[case_id]["arms"]["baseline"]["answer"],
            "chunks": chunks,
            "sources": sources,
            "evidence_text": format_evidence(sources),
            "evidence_joined": " ".join(chunk["text"] for chunk in chunks).lower(),
        }
    return {"facts": facts, "contexts": contexts}


def build_dataset() -> dict:
    frozen = {key: _json(path) for key, path in {
        "cohort": CLEANED_COHORT, "rubric": RUBRIC, "queries": QUERIES,
        "transfer": TRANSFER, "utilization": UTILIZATION}.items()}
    context = _case_context(frozen)
    facts = context["facts"]
    contexts = context["contexts"]
    writeback = {entry["fact_id"]: entry
                 for entry in frozen["cohort"]["human_review"]["frozen_human_review_writeback"]}
    items = []
    for fact_id in MISSING_FACT_IDS:
        entry = writeback[fact_id]
        items.append({"item_id": f"M-{fact_id}", "gold": "MISSING",
                      "source": "cleaned_cohort_confirmed_error", "fact_id": fact_id,
                      "case_id": entry["case_id"],
                      "proposition": facts[fact_id]["statement"]})
    present_ids = sorted(fact_id for fact_id, entry in writeback.items()
                         if entry["human_adjudication"] == "SEMANTICALLY_PRESENT")
    for fact_id in present_ids:
        entry = writeback[fact_id]
        items.append({"item_id": f"P-{fact_id}", "gold": "ALREADY_PRESENT",
                      "source": "mva_human_present", "fact_id": fact_id,
                      "case_id": entry["case_id"],
                      "proposition": facts[fact_id]["statement"]})
    for fact_id in CONTROL_PRESENT_FACT_IDS:
        case_id = facts[fact_id]["case_id"]
        items.append({"item_id": f"P-{fact_id}", "gold": "ALREADY_PRESENT",
                      "source": "oracle_repair_control", "fact_id": fact_id,
                      "case_id": case_id,
                      "proposition": next(value["already_present_proposition"]
                                          for value in REPAIR_CASES.values()
                                          if value["already_present_fact_id"] == fact_id)})
    for spec in UNSUPPORTED_ITEMS:
        items.append({"item_id": spec["item_id"], "gold": "UNSUPPORTED",
                      "source": spec["source"], "fact_id": None, "case_id": spec["case_id"],
                      "proposition": spec["proposition"], "markers": list(spec["markers"]),
                      "validation": spec["validation"]})
    for item in items:
        case = contexts[item["case_id"]]
        item.update({"query": case["query"], "baseline_answer": case["baseline_answer"],
                     "chunks": case["chunks"], "sources": case["sources"],
                     "evidence_text": case["evidence_text"],
                     "evidence_joined": case["evidence_joined"]})
    return {"items": items, "contexts": contexts}


def validate_dataset(dataset: dict) -> None:
    cohort = _json(CLEANED_COHORT)
    confirmed_errors = [item["fact_id"] for item in
                        cohort["cleaned_nominal_cohort"]["confirmed_errors"]]
    writeback = {entry["fact_id"]: entry
                 for entry in cohort["human_review"]["frozen_human_review_writeback"]}
    items = dataset["items"]
    missing = [item for item in items if item["gold"] == "MISSING"]
    present = [item for item in items if item["gold"] == "ALREADY_PRESENT"]
    unsupported = [item for item in items if item["gold"] == "UNSUPPORTED"]
    if [item["fact_id"] for item in missing] != confirmed_errors:
        raise ValueError("MISSING items must be exactly the cleaned-cohort confirmed errors")
    if any(item["source"] != "cleaned_cohort_confirmed_error" for item in missing):
        raise ValueError("MISSING items must come from the cleaned cohort")
    if any(item["fact_id"] in EXCLUDED_FACT_IDS for item in items):
        raise ValueError("ambiguous/non-atomic fact must not enter the dataset")
    if len(present) != 19:
        raise ValueError("expected 17 MVA + 2 oracle-control present items")
    mva_present = [item for item in present if item["source"] == "mva_human_present"]
    if len(mva_present) != 17:
        raise ValueError("expected 17 MVA human-present items")
    for item in mva_present:
        if writeback[item["fact_id"]]["human_adjudication"] != "SEMANTICALLY_PRESENT":
            raise ValueError(f"present item is not human-confirmed present: {item['item_id']}")
    control_targets = {value["already_present_fact_id"] for value in REPAIR_CASES.values()}
    if {item["fact_id"] for item in present if item["source"] == "oracle_repair_control"} \
            != control_targets:
        raise ValueError("oracle-control present items mismatch")
    if len(unsupported) != 6:
        raise ValueError("expected 6 validated unsupported items")
    for item in unsupported:
        if not item.get("validation"):
            raise ValueError(f"unsupported validation missing: {item['item_id']}")
        for marker in item["markers"]:
            if marker in item["evidence_joined"]:
                raise ValueError(f"unsupported marker {marker!r} found in evidence: "
                                 f"{item['item_id']}")
    for item in items:
        user = build_messages(item)[1]["content"]
        for token in LABELS:
            if token in user:
                raise ValueError(f"label token leaked into prompt: {item['item_id']}")
        for token in ("sham", "gold", "human_review", "oracle_repair", "repairability"):
            if token in user.lower():
                raise ValueError(f"metadata token leaked into prompt: {item['item_id']}")
    if len({item["item_id"] for item in items}) != len(items):
        raise ValueError("duplicate item ids")


def build_cells(dataset: dict) -> list[dict]:
    cells = []
    for item in dataset["items"]:
        for model_key, model in MODELS.items():
            for replicate in range(1, REPLICATES + 1):
                cells.append({"cell_id": f"{item['item_id']}::{model_key}::r{replicate}",
                              "item_id": item["item_id"], "gold": item["gold"],
                              "model_key": model_key, "model": model, "replicate": replicate})
    return cells


def execute_cell(cell: dict, item: dict, cache: _V3Cache, clients: dict, failures: list,
                 *, check_only: bool) -> dict:
    messages = build_messages(item)
    prompt_hash = _stable_hash({"messages": messages, "temperature": TEMPERATURE,
                                "max_tokens": MAX_TOKENS, "version": VERSION})
    key = _stable_hash({"version": VERSION, "model": cell["model"], "item_id": cell["item_id"],
                        "replicate": cell["replicate"], "prompt_config_hash": prompt_hash})
    cached = cache.get(key)
    if cached is None:
        if check_only:
            raise KeyError(f"missing cache entry: {cell['cell_id']}")
        client = clients[cell["model_key"]]
        started = perf_counter()
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=MAX_TOKENS,
                                                    temperature=TEMPERATURE)
            cached = {"kind": "classification", "raw": raw, "parsed": parse_classification(raw),
                      "provider_usage": usage, "latency_seconds": perf_counter() - started,
                      "raw_hash": _stable_hash(raw)}
        except Exception as error:
            cached = {"kind": "classification", "raw": None, "parsed": None,
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"kind": "classification", "cell_id": cell["cell_id"],
                             "error": cached["error"]})
        cache.set(key, cached)
    return {**cell, "prompt_config_hash": prompt_hash, "cache_key": key, **cached}


def modal_label(labels: list[str]) -> str | None:
    for label in LABELS:
        if labels.count(label) >= 2:
            return label
    return None


def _consistency(labels: list[str]) -> str:
    distinct = set(labels)
    if len(distinct) == 1 and "FAILED" not in distinct:
        return "3/3"
    if modal_label(labels) is not None:
        return "2/3"
    return "1/3"


def _confusion(item_rows: list[dict], strict: bool = False) -> dict:
    matrix = {gold: {label: 0 for label in LABELS} for gold in LABELS}
    excluded = 0
    for row in item_rows:
        if strict:
            usable = row["consistency"] == "3/3"
            prediction = row["labels"][0] if usable else None
        else:
            usable = row["modal"] is not None
            prediction = row["modal"]
        if not usable or prediction is None:
            excluded += 1
            continue
        matrix[row["gold"]][prediction] += 1
    return {"matrix": matrix, "excluded_inconsistent": excluded}


def _recall(matrix: dict, gold: str) -> dict:
    total = sum(matrix[gold].values())
    correct = matrix[gold].get(gold, 0)
    return {"numerator": correct, "denominator": total,
            "recall": correct / total if total else None}


def summarize(dataset: dict, cells: list[dict]) -> dict:
    gold_by_item = {item["item_id"]: item["gold"] for item in dataset["items"]}
    output = {}
    for model_key in MODELS:
        model_cells = [cell for cell in cells if cell["model_key"] == model_key]
        by_item: dict[str, dict[int, dict]] = {}
        for cell in model_cells:
            by_item.setdefault(cell["item_id"], {})[cell["replicate"]] = cell
        rows = []
        for item_id in sorted(by_item, key=lambda value: (gold_by_item[value], value)):
            labels = []
            for replicate in range(1, REPLICATES + 1):
                cell = by_item[item_id].get(replicate)
                labels.append(cell["parsed"]["label"]
                              if cell and cell.get("parsed") else "FAILED")
            rows.append({"item_id": item_id, "gold": gold_by_item[item_id], "labels": labels,
                         "modal": modal_label(labels), "consistency": _consistency(labels)})
        matrix = _confusion(rows)
        strict = _confusion(rows, strict=True)
        recalls = {label: _recall(matrix["matrix"], label) for label in LABELS}
        missing_rows = [row for row in rows if row["gold"] == "MISSING"]
        missing_errors = {"to_already_present": sum(
            1 for row in missing_rows if row["modal"] == "ALREADY_PRESENT"),
            "to_unsupported": sum(1 for row in missing_rows
                                  if row["modal"] == "UNSUPPORTED"),
            "unresolved_inconsistent": sum(1 for row in missing_rows
                                           if row["modal"] is None)}
        consistency_counts = {band: sum(1 for row in rows if row["consistency"] == band)
                              for band in ("3/3", "2/3", "1/3")}
        modal_rows = [row for row in rows if row["modal"] is not None]
        accuracy = (sum(1 for row in modal_rows if row["modal"] == row["gold"])
                    / len(modal_rows) if modal_rows else None)
        valid_ids = {f"S{index}" for index in range(1, 6)}
        invalid_evidence_ids = sum(
            1 for cell in model_cells
            if cell.get("parsed") and any(identifier not in valid_ids
                                          for identifier in cell["parsed"]["evidence_source_ids"]))
        unsupported_cited = sum(
            1 for cell in model_cells
            if cell.get("parsed") and cell["gold"] == "UNSUPPORTED"
            and cell["parsed"]["evidence_source_ids"])
        output[model_key] = {
            "items": rows,
            "confusion": matrix,
            "confusion_strict_3_of_3": strict,
            "per_class_recall": recalls,
            "missing_errors": missing_errors,
            "consistency": consistency_counts,
            "overall_accuracy_modal": accuracy,
            "auxiliary": {"invalid_evidence_source_ids_cells": invalid_evidence_ids,
                          "unsupported_cells_citing_sources": unsupported_cited},
        }
    output["sensitivity_excluding_050_F05"] = _sensitivity(dataset, cells)
    output["preregistered_outcome"] = _outcome(dataset, cells)
    return output


def _sensitivity(dataset: dict, cells: list[dict]) -> dict:
    caveat = f"P-{CAVEAT_PRESENT_FACT_IDS[0]}"
    result = {}
    for model_key in MODELS:
        rows = []
        by_item: dict[str, dict[int, dict]] = {}
        for cell in cells:
            if cell["model_key"] != model_key:
                continue
            by_item.setdefault(cell["item_id"], {})[cell["replicate"]] = cell
        for item_id, replicates in by_item.items():
            labels = [replicates[r]["parsed"]["label"] if replicates.get(r) and
                      replicates[r].get("parsed") else "FAILED" for r in range(1, REPLICATES + 1)]
            rows.append({"item_id": item_id, "gold": cell_gold(dataset, item_id),
                         "modal": modal_label(labels)})
        rows = [row for row in rows if row["item_id"] != caveat]
        matrix = {gold: {label: 0 for label in LABELS} for gold in LABELS}
        for row in rows:
            if row["modal"]:
                matrix[row["gold"]][row["modal"]] += 1
        result[model_key] = {"per_class_recall": {label: _recall(matrix, label)
                                                  for label in LABELS}}
    return result


def cell_gold(dataset: dict, item_id: str) -> str:
    return next(item["gold"] for item in dataset["items"] if item["item_id"] == item_id)


def _outcome(dataset: dict, cells: list[dict]) -> dict:
    missing_ids = [f"M-{fact_id}" for fact_id in MISSING_FACT_IDS]

    def modals(model_key: str) -> dict:
        values = {}
        for item_id in missing_ids:
            labels = [cell["parsed"]["label"] if cell.get("parsed") else "FAILED"
                      for cell in cells
                      if cell["model_key"] == model_key and cell["item_id"] == item_id]
            values[item_id] = modal_label(labels)
        return values

    current = modals("current")
    stronger = modals("stronger")
    all_items = sorted({cell["item_id"] for cell in cells})

    def full_modals(model_key: str) -> dict:
        output = {}
        for item_id in all_items:
            labels = [cell["parsed"]["label"] if cell.get("parsed") else "FAILED"
                      for cell in cells
                      if cell["model_key"] == model_key and cell["item_id"] == item_id]
            output[item_id] = modal_label(labels)
        return output

    if all(current[item_id] == "MISSING" for item_id in missing_ids):
        outcome = "B"
    elif (all(stronger[item_id] == "MISSING" for item_id in missing_ids)
          and any(current[item_id] != "MISSING" for item_id in missing_ids)):
        outcome = "A"
    elif full_modals("current") == full_modals("stronger"):
        outcome = "C"
    else:
        outcome = "mixed/unresolved"
    return {"outcome": outcome, "current_missing_modals": current,
            "stronger_missing_modals": stronger,
            "039_current": current.get(f"M-{MISSING_FACT_IDS[0]}"),
            "039_stronger": stronger.get(f"M-{MISSING_FACT_IDS[0]}"),
            "050_current": current.get(f"M-{MISSING_FACT_IDS[1]}"),
            "050_stronger": stronger.get(f"M-{MISSING_FACT_IDS[1]}")}


def run(*, check_only: bool = False) -> dict:
    dataset = build_dataset()
    validate_dataset(dataset)
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
              f"{result.get('parsed', {}).get('label') if result.get('parsed') else 'FAILED'}",
              flush=True)
    document = {
        "schema_version": 1,
        "version": VERSION,
        "status": "complete",
        "scope_note": ("Mechanism / H1 mechanism diagnostic: proposition-level semantic state "
                       "classification on frozen answers and evidence. No repair generation; MISSING "
                       "n=2, so no population inference."),
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": _sha256(PREREG)},
        "dataset": {
            "composition": {"MISSING": sum(1 for item in dataset["items"]
                                           if item["gold"] == "MISSING"),
                            "ALREADY_PRESENT": sum(1 for item in dataset["items"]
                                                   if item["gold"] == "ALREADY_PRESENT"),
                            "UNSUPPORTED": sum(1 for item in dataset["items"]
                                               if item["gold"] == "UNSUPPORTED"),
                            "items": len(dataset["items"])},
            "items": [{key: item[key] for key in
                       ("item_id", "gold", "source", "fact_id", "case_id", "proposition")}
                      | ({"validation": item["validation"]} if "validation" in item else {})
                      for item in dataset["items"]],
            "excluded_fact_ids": list(EXCLUDED_FACT_IDS),
            "caveats": [f"gold caveat item: {CAVEAT_PRESENT_FACT_IDS[0]}; sensitivity reported"],
        },
        "design": {"models": MODELS, "replicates": REPLICATES, "max_tokens": MAX_TOKENS,
                   "temperature": TEMPERATURE, "cells": len(cells),
                   "classifier_prompt_sha256": hashlib.sha256(
                       CLASSIFIER_SYSTEM.encode("utf-8")).hexdigest(),
                   "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS},
        "frozen_inputs": {relative: _sha256(ROOT / relative) for relative in (
            "eval/semantic_gap_discrimination_v1_preregistration.md",
            "eval/results/measurement_validity_cleaned_cohort.json",
            "eval/results/measurement_validity_audit.json",
            "eval/results/measurement_validity_audit_v2.json",
            "eval/results/generation_utilization_results.json",
            "eval/results/reranker_transfer_results.json",
            "eval/results/oracle_repair_v1_results.json",
            "eval/results/oracle_repair_v1_human_scored.json",
            "eval/results/repairability_stage_summary.md",
            "eval/validation/broad_atomic_facts_validation_v1.json",
            "eval/validation/broad_queries_validation_v1.json",
        )},
        "cells": [{key: cell[key] for key in
                   ("cell_id", "item_id", "gold", "model_key", "model", "replicate",
                    "prompt_config_hash", "cache_key", "parsed", "provider_usage",
                    "latency_seconds", "error") if key in cell} for cell in executed],
        "aggregates": summarize(dataset, executed),
        "failures": failures,
    }
    if not check_only:
        _write(RESULTS, document)
        SUMMARY.write_text(render_summary(document), encoding="utf-8")
    return document


def render_summary(document: dict) -> str:
    aggregates = document["aggregates"]
    dataset = document["dataset"]
    lines = ["# Semantic Gap Discrimination V1 - Summary (Mechanism / H1)", "",
             "> " + document["scope_note"], "",
             f"- status: {document['status']}",
             f"- preregistration sha256: `{document['preregistration']['sha256'][:16]}`",
             f"- dataset: {dataset['composition']}; excluded: {dataset['excluded_fact_ids']}",
             f"- design: {document['design']['cells']} cells = 27 items x 2 models x "
             f"{document['design']['replicates']} replicates; max_tokens "
             f"{document['design']['max_tokens']}", "",
             "## Confusion matrices (modal label; rows = gold, columns = predicted)", ""]
    for model_key in MODELS:
        block = aggregates[model_key]
        lines += [f"### {model_key}", "",
                  "| gold \\ predicted | MISSING | ALREADY_PRESENT | UNSUPPORTED | excluded inconsistent |",
                  "|---|---:|---:|---:|---:|"]
        for gold in LABELS:
            row = block["confusion"]["matrix"][gold]
            lines.append(f"| {gold} | {row['MISSING']} | {row['ALREADY_PRESENT']} | "
                         f"{row['UNSUPPORTED']} | {block['confusion']['excluded_inconsistent']} |")
        lines += ["", f"- per-class recall: " +
                  ", ".join(f"{label} {block['per_class_recall'][label]['numerator']}/"
                            f"{block['per_class_recall'][label]['denominator']}"
                            for label in LABELS),
                  f"- overall accuracy (modal): {block['overall_accuracy_modal']}",
                  f"- MISSING -> ALREADY_PRESENT: "
                  f"{block['missing_errors']['to_already_present']}; MISSING -> UNSUPPORTED: "
                  f"{block['missing_errors']['to_unsupported']}; MISSING unresolved: "
                  f"{block['missing_errors']['unresolved_inconsistent']}",
                  f"- consistency (3/3, 2/3, 1/3): {block['consistency']}",
                  ""]
    lines += ["## Item-level readout (Repairability-linked items)", "",
              "| item | model | replicate labels | modal | consistency |", "|---|---|---|---|---|"]
    for model_key in MODELS:
        for row in aggregates[model_key]["items"]:
            if row["gold"] != "MISSING":
                continue
            lines.append(f"| {row['item_id']} | {model_key} | {', '.join(row['labels'])} | "
                         f"{row['modal']} | {row['consistency']} |")
    lines += ["", "## Strict 3/3-agreement sensitivity", ""]
    for model_key in MODELS:
        strict = aggregates[model_key]["confusion_strict_3_of_3"]
        lines.append(f"- {model_key}: matrix {strict['matrix']}; excluded "
                     f"{strict['excluded_inconsistent']}")
    lines += ["", "## Gold-caveat sensitivity (excluding P-VAL-001-050-F05)", ""]
    for model_key in MODELS:
        recalls = aggregates["sensitivity_excluding_050_F05"][model_key]["per_class_recall"]
        lines.append(f"- {model_key}: " + ", ".join(
            f"{label} {recalls[label]['numerator']}/{recalls[label]['denominator']}"
            for label in LABELS))
    lines += ["", "## Preregistered outcome mapping", "",
              f"- operational mapping: **{aggregates['preregistered_outcome']['outcome']}**",
              f"- 039-F02 modal: current "
              f"{aggregates['preregistered_outcome']['039_current']} / stronger "
              f"{aggregates['preregistered_outcome']['039_stronger']}",
              f"- 050-F01 modal: current "
              f"{aggregates['preregistered_outcome']['050_current']} / stronger "
              f"{aggregates['preregistered_outcome']['050_stronger']}",
              "- MISSING n=2: mechanism diagnostic only; no statistical generalization.", "",
              "## Failures", f"- {document['failures']}", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild from cache without any API call")
    args = parser.parse_args(argv)
    document = run(check_only=args.check)
    print(json.dumps({"status": document["status"],
                      "outcome": document["aggregates"]["preregistered_outcome"],
                      "current": {key: document["aggregates"]["current"][key]
                                  for key in ("confusion", "per_class_recall",
                                              "missing_errors", "consistency",
                                              "overall_accuracy_modal")},
                      "stronger": {key: document["aggregates"]["stronger"][key]
                                   for key in ("confusion", "per_class_recall",
                                               "missing_errors", "consistency",
                                               "overall_accuracy_modal")},
                      "failures": document["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
