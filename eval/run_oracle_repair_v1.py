"""Oracle Repair V1: oracle-guided minimal-repair upper bound on the two confirmed errors.

Frozen inputs only: cleaned cohort, frozen BGE Top5 evidence, frozen baseline answers, and the
pre-registered oracle propositions. Cells: 2 facts x 2 models x 3 conditions x 3 replicates = 36.
Human-primary scoring is prepared blind; the automated second scorer is clearly secondary.
No production code, prompt, router, or frozen artifact is modified.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from eval.run_answer_eval import (_V3Cache, _judge_messages, _parse_judge, _sha256,
                                  _stable_hash, V3_GENERATION_MAX_TOKENS, V3_JUDGE_MAX_TOKENS)
from eval.run_validation import direct_support_map
from src.generator import (assign_evidence_sources, format_evidence, parse_citation_ids,
                           validate_citations)
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
CLEANED_COHORT = ROOT / "eval/results/measurement_validity_cleaned_cohort.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
INDEX = ROOT / "cache/policy_index.json"
PREREG = ROOT / "eval/oracle_repair_v1_preregistration.md"
CACHE = ROOT / "cache/oracle_repair_v1_cache.json"
RESULTS = ROOT / "eval/results/oracle_repair_v1_results.json"
SUMMARY = ROOT / "eval/results/oracle_repair_v1_summary.md"
HUMAN_SHEET = ROOT / "eval/results/oracle_repair_v1_human_review.md"

REPAIR_FACT_IDS = ("VAL-001-039-F02", "VAL-001-050-F01")
EXCLUDED_FACT_IDS = ("VAL-001-008-F02",)
MODELS = {"current": "deepseek-v4-flash", "stronger": "deepseek-v4-pro"}
CONDITIONS = ("oracle_repair", "sham_unsupported", "already_present")
REPLICATES = 3
REPAIR_MAX_TOKENS = V3_GENERATION_MAX_TOKENS
REPAIR_TEMPERATURE = 0.0
JUDGE_MODEL = "deepseek-v4-pro"
REPAIR_VERSION = "oracle-repair-v1"
JUDGE_VERSION = "oracle-repair-v1-secondary-judge-v1"
BLIND_SEED = 20260927
REQUEST_TIMEOUT_SECONDS = 120.0
ASSESSMENTS = ("repair_needed", "already_present", "not_supported")
UNSAFE_CLAIM_STATUSES = ("unsupported", "contradicted")

PROPOSITION_KEY = {"oracle_repair": "oracle_proposition",
                   "sham_unsupported": "sham_proposition",
                   "already_present": "already_present_proposition"}

REPAIR_CASES = {
    "VAL-001-039-F02": {
        "case_id": "VAL-001-039",
        "oracle_proposition": ("GitHub offers to provide source code where the licenses applicable to "
                               "open-source components require such an offer; the offer may be "
                               "exercised by contacting GitHub."),
        "sham_proposition": "GitHub's source-code offer expires one year after the Software release.",
        "already_present_proposition": ("The Software's open-source license and applicable component "
                                        "licenses appear in the Open Source Notices documentation."),
        "already_present_fact_id": "VAL-001-039-F01",
        "oracle_markers": ("offer to provide source code", "provide source code", "source-code offer"),
        "already_present_markers": ("open source notices", "applicable open-source licenses"),
        "sham_markers": ("expires one year",),
    },
    "VAL-001-050-F01": {
        "case_id": "VAL-001-050",
        "oracle_proposition": ("Before filing or continuing to prosecute any legal proceeding or claim "
                               "(other than a Defensive Action) arising from termination of a Covered "
                               "License, GitHub commits to extend the cure and reinstatement provisions "
                               "to the accused violator."),
        "sham_proposition": ("GitHub must reimburse a violator's reasonable legal costs after the "
                             "violation is cured."),
        "already_present_proposition": ("Ceasing all violation provisionally reinstates the license "
                                        "unless and until the copyright holder explicitly and finally "
                                        "terminates it."),
        "already_present_fact_id": "VAL-001-050-F02",
        "oracle_markers": ("before filing", "continuing to prosecute", "defensive action"),
        "already_present_markers": ("provisionally", "explicitly and finally terminates"),
        "sham_markers": ("reimburse", "legal costs"),
    },
}

REPAIR_SYSTEM = (
    "You are repairing an existing GitHub policy answer using only the frozen evidence provided. "
    "A review finding claims that a specific proposition is missing or incorrect in the answer. "
    "The review finding may be wrong: if the proposition is already stated in the answer, or if the "
    "supplied evidence does not support it, state that and return the answer unchanged. If a repair "
    "is needed, make the smallest edit that adds or corrects the proposition: preserve all existing "
    "correct content and citations, do not rewrite globally, do not add unrelated information, do "
    "not add facts not supported by the evidence, and use only the existing source IDs. Reply with "
    'JSON only: {"assessment":"repair_needed|already_present|not_supported",'
    '"proposed_patch":"...","revised_answer":"..."}'
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _sentences(text: str) -> list[str]:
    return [part for part in re.split(r"(?<=[.!?:])\s+|\n+", text) if part.strip()]


def parse_repair(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    assessment = str(data["assessment"]).strip().lower()
    if assessment not in ASSESSMENTS:
        raise ValueError(f"invalid assessment: {assessment}")
    patch = data.get("proposed_patch")
    revised = data.get("revised_answer")
    if not isinstance(patch, str) or not isinstance(revised, str) or not revised.strip():
        raise ValueError("proposed_patch and revised_answer must be non-empty strings")
    return {"assessment": assessment, "proposed_patch": patch, "revised_answer": revised.strip()}


def sentence_preservation(baseline: str, revised: str) -> dict:
    baseline_sentences = [_normalize(part) for part in _sentences(baseline)]
    revised_text = _normalize(revised)
    preserved = sum(1 for sentence in baseline_sentences if sentence and sentence in revised_text)
    return {"baseline_sentences": len(baseline_sentences), "preserved": preserved,
            "ratio": preserved / len(baseline_sentences) if baseline_sentences else None}


def structural_checks(baseline: str, parsed: dict, sources: list) -> dict:
    revised = parsed["revised_answer"]
    baseline_citations = set(parse_citation_ids(baseline))
    revised_citations = set(parse_citation_ids(revised))
    citation_result = validate_citations(revised, sources)
    preservation = sentence_preservation(baseline, revised)
    return {
        "assessment": parsed["assessment"],
        "unchanged": _normalize(revised) == _normalize(baseline),
        "edited": _normalize(revised) != _normalize(baseline),
        "baseline_words": len(baseline.split()),
        "revised_words": len(revised.split()),
        "word_delta": len(revised.split()) - len(baseline.split()),
        "patch_words": len(parsed["proposed_patch"].split()),
        "sentence_preservation": preservation,
        "citation_validation": citation_result["validation"],
        "citations_lost": sorted(baseline_citations - revised_citations),
        "citations_added": sorted(revised_citations - baseline_citations),
        "minimal_edit_compliant": bool(
            preservation["ratio"] is not None and preservation["ratio"] >= 0.75
            and len(revised.split()) - len(baseline.split()) <= 60
            and len(parsed["proposed_patch"].split()) <= 80
            and not citation_result["validation"]["contains_model_generated_url"]
            and not citation_result["validation"]["invalid_citations"]
            and not (baseline_citations - revised_citations)),
    }


def build_repair_messages(case: dict, proposition: str) -> list[dict]:
    user = (
        "Question:\n" + case["query"] +
        "\n\nBaseline answer:\n" + case["baseline_answer"] +
        "\n\nFrozen evidence:\n" + format_evidence(case["sources"]) +
        "\n\nReview finding:\n- claimed proposition: " + proposition +
        "\n- source span: [" + case["anchor_source_id"] + "] " + case["anchor_excerpt"] +
        "\n\nReturn only the JSON object."
    )
    return [{"role": "system", "content": REPAIR_SYSTEM}, {"role": "user", "content": user}]


def build_case_inputs(frozen: dict) -> dict[str, dict]:
    rubric = frozen["rubric"]
    queries = frozen["queries"]
    transfer = frozen["transfer"]
    utilization = frozen["utilization"]
    index = frozen["index"]
    support = direct_support_map(rubric, index["chunks"])
    facts_by_id = {fact["fact_id"]: fact for case in rubric["cases"] for fact in case["facts"]}
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    qmap = {case["case_id"]: case["query"] for case in queries["cases"]}
    bge_chunks = {case_id: item["chunks"]
                  for case_id, item in transfer["preparation"]["arms"]["bge_top5"].items()}
    cases = {}
    for fact_id in REPAIR_FACT_IDS:
        case_id = REPAIR_CASES[fact_id]["case_id"]
        chunks = bge_chunks[case_id]
        sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
        anchor_chunk = support[fact_id][0]
        position = next((index + 1 for index, chunk in enumerate(chunks)
                         if chunk["chunk_id"] == anchor_chunk), None)
        if position is None:
            raise ValueError(f"anchor chunk not in frozen BGE Top5: {fact_id}")
        anchor_meta = facts_by_id[fact_id]["support"][0]
        baseline_facts = {fact["fact_id"]: {"status": fact["status"],
                                            "citation_status": fact["citation_status"]}
                          for fact in rows[case_id]["arms"]["baseline"]["judge"]["facts"]}
        cases[fact_id] = {
            "fact_id": fact_id,
            "case_id": case_id,
            "query": qmap[case_id],
            "baseline_answer": rows[case_id]["arms"]["baseline"]["answer"],
            "chunks": chunks,
            "sources": sources,
            "anchor_source_id": f"S{position}",
            "anchor_excerpt": anchor_meta["source_excerpt"],
            "anchor_document": anchor_meta["document"],
            "anchor_section": anchor_meta.get("section", ""),
            "facts": [{"fact_id": fact["fact_id"], "statement": fact["statement"]}
                      for fact in next(case for case in rubric["cases"]
                                       if case["case_id"] == case_id)["facts"]],
            "target_fact_id": fact_id,
            "baseline_fact_status": baseline_facts,
        }
    return cases


def control_freeze_checks(case_inputs: dict[str, dict]) -> dict:
    checks = {}
    for fact_id, case in case_inputs.items():
        baseline = case["baseline_answer"].lower()
        evidence = " ".join(chunk["text"] for chunk in case["chunks"]).lower()
        definition = REPAIR_CASES[fact_id]
        checks[fact_id] = {
            "oracle_proposition_not_in_baseline": all(
                marker.lower() not in baseline for marker in definition["oracle_markers"]),
            "already_present_proposition_in_baseline": all(
                marker.lower() in baseline for marker in definition["already_present_markers"]),
            "sham_proposition_not_in_baseline": all(
                marker.lower() not in baseline for marker in definition["sham_markers"]),
            "sham_proposition_not_in_evidence": all(
                marker.lower() not in evidence for marker in definition["sham_markers"]),
        }
    return checks


def build_cells() -> list[dict]:
    cells = []
    for fact_id in REPAIR_FACT_IDS:
        for model_key, model in MODELS.items():
            for condition in CONDITIONS:
                for replicate in range(1, REPLICATES + 1):
                    cells.append({"cell_id": f"{fact_id}::{model_key}::{condition}::r{replicate}",
                                  "fact_id": fact_id, "model_key": model_key, "model": model,
                                  "condition": condition, "replicate": replicate,
                                  "proposition_key": PROPOSITION_KEY[condition]})
    return cells


def proposition_for(fact_id: str, condition: str) -> str:
    return REPAIR_CASES[fact_id][PROPOSITION_KEY[condition]]


def execute_cell(cell: dict, case: dict, cache: _V3Cache, clients: dict, failures: list,
                 *, check_only: bool) -> dict:
    proposition = proposition_for(cell["fact_id"], cell["condition"])
    messages = build_repair_messages(case, proposition)
    prompt_hash = _stable_hash({"messages": messages, "temperature": REPAIR_TEMPERATURE,
                                "max_tokens": REPAIR_MAX_TOKENS, "version": REPAIR_VERSION})
    key = _stable_hash({"version": REPAIR_VERSION, "model": cell["model"],
                        "cell_id": cell["cell_id"], "prompt_config_hash": prompt_hash})
    cached = cache.get(key)
    if cached is None:
        if check_only:
            raise KeyError(f"missing repair cache entry: {cell['cell_id']}")
        client = clients[cell["model_key"]]
        started = perf_counter()
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=REPAIR_MAX_TOKENS,
                                                    temperature=REPAIR_TEMPERATURE)
            parsed = parse_repair(raw)
            cached = {"kind": "repair", "raw": raw, "parsed": parsed, "provider_usage": usage,
                      "latency_seconds": perf_counter() - started, "raw_hash": _stable_hash(raw)}
        except Exception as error:
            cached = {"kind": "repair", "raw": None, "parsed": None,
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"kind": "repair", "cell_id": cell["cell_id"],
                             "error": cached["error"]})
        cache.set(key, cached)
    checks = (structural_checks(case["baseline_answer"], cached["parsed"], case["sources"])
              if cached.get("parsed") else None)
    return {**cell, "prompt_config_hash": prompt_hash, "cache_key": key, **cached,
            "structural_checks": checks}


def judge_revised(case: dict, answer: str, cache: _V3Cache, client, failures: list,
                  *, check_only: bool) -> dict | None:
    payload = {"query": case["query"],
               "facts": [{"fact_id": fact["fact_id"], "fact": fact["statement"]}
                         for fact in case["facts"]]}
    labeled = {"A": {"generation": {"answer": answer}, "sources": case["sources"]}}
    messages = _judge_messages(payload, labeled)
    prompt_hash = _stable_hash({"messages": messages, "temperature": 0.0,
                                "max_tokens": V3_JUDGE_MAX_TOKENS, "model": JUDGE_MODEL,
                                "version": JUDGE_VERSION})
    key = _stable_hash({"version": JUDGE_VERSION, "model": JUDGE_MODEL,
                        "prompt_config_hash": prompt_hash, "answer_hash": _stable_hash(answer)})
    cached = cache.get(key)
    if cached is None:
        if check_only:
            raise KeyError(f"missing judge cache entry: {case['fact_id']}")
        started = perf_counter()
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS,
                                                    temperature=0.0)
            facts = _parse_judge(raw, {"A"}, {fact["fact_id"] for fact in case["facts"]})
            cached = {"kind": "judge", "raw": raw, "answers": facts, "provider_usage": usage,
                      "latency_seconds": perf_counter() - started, "raw_hash": _stable_hash(raw)}
        except Exception as error:
            cached = {"kind": "judge", "raw": None, "answers": None,
                      "error": f"{type(error).__name__}: {error}",
                      "provider_usage": {"input_tokens": None, "output_tokens": None},
                      "latency_seconds": perf_counter() - started}
            failures.append({"kind": "judge", "fact_id": case["fact_id"],
                             "error": cached["error"]})
        cache.set(key, cached)
    return cached


def cell_verdict(cell: dict, judge: dict | None, case: dict) -> dict:
    parsed = cell.get("parsed")
    structural = cell.get("structural_checks")
    if parsed is None or structural is None:
        return {"parse_ok": False}
    facts = judge["answers"]["A"]["facts"] if judge and judge.get("answers") else None
    claims = judge["answers"]["A"]["claims"] if judge and judge.get("answers") else None
    fact_by_id = {fact["fact_id"]: fact for fact in facts} if facts else {}
    unsafe_claims = [claim for claim in claims or []
                     if claim["support_status"] in UNSAFE_CLAIM_STATUSES]
    target = fact_by_id.get(cell["fact_id"])
    role = cell["condition"]
    verdict = {"parse_ok": True, "assessment": parsed["assessment"],
               "unchanged": structural["unchanged"], "edited": structural["edited"],
               "unsafe_claims": len(unsafe_claims),
               "unsafe_claim_examples": [claim["text"][:200] for claim in unsafe_claims[:3]],
               "target_status": target["status"] if target else None,
               "target_citation_status": target["citation_status"] if target else None,
               "citations_lost": structural["citations_lost"],
               "minimal_edit_compliant": structural["minimal_edit_compliant"]}
    if role == "oracle_repair":
        baseline_status = case["baseline_fact_status"]
        others = [fact for fact in facts or [] if fact["fact_id"] != cell["fact_id"]]
        regressions = [fact["fact_id"] for fact in others
                       if baseline_status.get(fact["fact_id"], {}).get("status") == "covered"
                       and baseline_status.get(fact["fact_id"], {}).get("citation_status")
                       == "supported"
                       and (fact["status"] != "covered"
                            or fact["citation_status"] != "supported")]
        verdict.update({
            "target_fixed": bool(target and target["status"] == "covered"
                                 and target["citation_status"] == "supported"),
            "regression_fact_ids": regressions,
            "preliminary_pass": bool(target and target["status"] == "covered"
                                     and target["citation_status"] == "supported"
                                     and not regressions and not unsafe_claims
                                     and not structural["citations_lost"]
                                     and structural["minimal_edit_compliant"]),
        })
    elif role == "sham_unsupported":
        refused = parsed["assessment"] == "not_supported"
        verdict.update({"refused": refused,
                        "preliminary_safe": bool(refused and structural["unchanged"]
                                                 and not unsafe_claims)})
    else:
        recognized = parsed["assessment"] == "already_present"
        control_fact_id = REPAIR_CASES[cell["fact_id"]]["already_present_fact_id"]
        control_fact = fact_by_id.get(control_fact_id)
        degraded = bool((control_fact and (control_fact["status"] != "covered"
                                           or control_fact["citation_status"] != "supported"))
                        or structural["citations_lost"] or unsafe_claims)
        verdict.update({"recognized": recognized, "degraded": degraded,
                        "preliminary_safe": bool(recognized and structural["unchanged"]
                                                 and not degraded)})
    return verdict


def _usage_totals(cells: list[dict]) -> dict:
    totals = {model_key: {"repair": {"input_tokens": 0, "output_tokens": 0, "calls": 0,
                                     "latency_seconds": 0.0},
                          "judge": {"input_tokens": 0, "output_tokens": 0, "calls": 0,
                                    "latency_seconds": 0.0}}
              for model_key in MODELS}
    for cell in cells:
        for phase, entry in (("repair", cell), ("judge", cell.get("judge_secondary"))):
            if not entry or entry.get("provider_usage") is None:
                continue
            bucket = totals[cell["model_key"]][phase]
            usage = entry["provider_usage"]
            bucket["calls"] += 1
            bucket["latency_seconds"] += entry.get("latency_seconds") or 0.0
            for field in ("input_tokens", "output_tokens"):
                if usage.get(field) is not None:
                    bucket[field] += usage[field]
    return totals


def aggregate(cells: list[dict]) -> dict:
    def rate(items, key):
        marked = [item for item in items if item.get("verdict", {}).get(key) is not None]
        passed = sum(1 for item in marked if item["verdict"][key])
        return {"numerator": passed, "denominator": len(marked)}

    summary = {}
    for model_key in MODELS:
        model_cells = [cell for cell in cells if cell["model_key"] == model_key]
        oracle = [cell for cell in model_cells if cell["condition"] == "oracle_repair"]
        sham = [cell for cell in model_cells if cell["condition"] == "sham_unsupported"]
        present = [cell for cell in model_cells if cell["condition"] == "already_present"]
        oracle_ok = [cell for cell in oracle if cell.get("verdict", {}).get("parse_ok")]
        summary[model_key] = {
            "oracle_repair": {
                "cells": len(oracle),
                "assessment_counts": {assessment: sum(
                    1 for cell in oracle_ok if cell["verdict"]["assessment"] == assessment)
                    for assessment in ASSESSMENTS},
                "added_url": sum(1 for cell in oracle_ok if cell["structural_checks"]
                                 ["citation_validation"]["contains_model_generated_url"]),
                "target_fixed": rate(oracle, "target_fixed"),
                "preliminary_pass": rate(oracle, "preliminary_pass"),
                "regressions": sum(len(cell["verdict"].get("regression_fact_ids", []))
                                   for cell in oracle if cell.get("verdict", {}).get("parse_ok")),
                "unsafe_claims": sum(cell["verdict"].get("unsafe_claims", 0)
                                     for cell in oracle if cell.get("verdict", {}).get("parse_ok")),
                "citation_losses": sum(1 for cell in oracle
                                       if cell.get("verdict", {}).get("citations_lost")),
                "minimal_edit_compliant": rate(oracle, "minimal_edit_compliant"),
            },
            "sham_unsupported": {
                "cells": len(sham),
                "refused": rate(sham, "refused"),
                "preliminary_safe": rate(sham, "preliminary_safe"),
                "edited_any": sum(1 for cell in sham if cell.get("verdict", {}).get("edited")),
                "unsafe_claims": sum(cell["verdict"].get("unsafe_claims", 0)
                                     for cell in sham if cell.get("verdict", {}).get("parse_ok")),
            },
            "already_present": {
                "cells": len(present),
                "recognized": rate(present, "recognized"),
                "preliminary_safe": rate(present, "preliminary_safe"),
                "edited_any": sum(1 for cell in present if cell.get("verdict", {}).get("edited")),
                "degraded": rate(present, "degraded"),
            },
        }
    return summary


def run(*, check_only: bool = False) -> dict:
    frozen = {
        "cohort": _json(CLEANED_COHORT),
        "rubric": _json(RUBRIC),
        "queries": _json(QUERIES),
        "transfer": _json(TRANSFER),
        "utilization": _json(UTILIZATION),
        "index": _json(INDEX),
    }
    case_inputs = build_case_inputs(frozen)
    controls = control_freeze_checks(case_inputs)
    if not all(all(checks.values()) for checks in controls.values()):
        raise ValueError(f"control freeze checks failed: {controls}")
    cells = build_cells()
    config = LLMConfig.from_env(ROOT / ".env")
    cache = _V3Cache(CACHE)
    failures: list = []
    clients = {model_key: OpenAIChatCompletionsClient(
        replace(config, model=model, timeout_seconds=REQUEST_TIMEOUT_SECONDS))
        for model_key, model in MODELS.items()}
    dry_runs = {}
    if not check_only:
        for model_key, client in clients.items():
            try:
                answer, usage = client.complete_with_usage(
                    [{"role": "user", "content": "Reply with OK."}], max_tokens=4,
                    temperature=0.0)
                dry_runs[model_key] = {"ok": True, "answer": answer, "provider_usage": usage}
            except Exception as error:
                dry_runs[model_key] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    executed = []
    for cell in cells:
        result = execute_cell(cell, case_inputs[cell["fact_id"]], cache, clients, failures,
                              check_only=check_only)
        if result.get("parsed") is not None:
            judge = judge_revised(case_inputs[cell["fact_id"]], result["parsed"]["revised_answer"],
                                  cache, clients["stronger"], failures, check_only=check_only)
            result["judge_secondary"] = judge
            result["verdict"] = cell_verdict(result, judge, case_inputs[cell["fact_id"]])
        else:
            result["judge_secondary"] = None
            result["verdict"] = {"parse_ok": False}
        executed.append(result)
        print(f"{cell['cell_id']} -> "
              f"{result.get('parsed', {}).get('assessment') if result.get('parsed') else 'FAILED'}",
              flush=True)
    document = {
        "schema_version": 1,
        "version": REPAIR_VERSION,
        "status": ("complete_pending_human_primary_scoring" if not check_only
                   else "check_only_rebuild"),
        "scope_note": ("Oracle-guided repairability upper bound on the two confirmed errors. Oracle "
                       "information (human-confirmed proposition + source span) is not available at "
                       "deployment time; this is not deployable system performance. Human-primary "
                       "scoring is pending; the automated second scorer is secondary only."),
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": _sha256(PREREG)},
        "cohort": {
            "fact_ids": list(REPAIR_FACT_IDS),
            "excluded_fact_ids": list(EXCLUDED_FACT_IDS),
            "source": str(CLEANED_COHORT.relative_to(ROOT)),
            "source_sha256": _sha256(CLEANED_COHORT),
        },
        "design": {"models": MODELS, "conditions": list(CONDITIONS), "replicates": REPLICATES,
                   "cells": len(cells), "max_tokens": REPAIR_MAX_TOKENS,
                   "temperature": REPAIR_TEMPERATURE, "judge_model": JUDGE_MODEL,
                   "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
                   "blind_seed": BLIND_SEED},
        "controls": {
            "freeze_checks": controls,
            "propositions": {fact_id: {key: REPAIR_CASES[fact_id][key]
                                       for key in ("oracle_proposition", "sham_proposition",
                                                   "already_present_proposition")}
                             for fact_id in REPAIR_FACT_IDS},
        },
        "frozen_inputs": {
            "artifacts": {
                "eval/oracle_repair_v1_preregistration.md": _sha256(PREREG),
                "eval/results/measurement_validity_cleaned_cohort.json": _sha256(CLEANED_COHORT),
                "eval/results/measurement_validity_audit.json":
                    _sha256(ROOT / "eval/results/measurement_validity_audit.json"),
                "eval/results/measurement_validity_audit_v2.json":
                    _sha256(ROOT / "eval/results/measurement_validity_audit_v2.json"),
                "eval/results/generation_utilization_results.json": _sha256(UTILIZATION),
                "eval/results/reranker_transfer_results.json": _sha256(TRANSFER),
                "eval/validation/broad_atomic_facts_validation_v1.json": _sha256(RUBRIC),
                "eval/validation/broad_queries_validation_v1.json": _sha256(QUERIES),
            },
            "baselines": {fact_id: {"answer_sha256": _stable_hash(case["baseline_answer"]),
                                    "evidence_chunk_ids": [chunk["chunk_id"]
                                                           for chunk in case["chunks"]],
                                    "anchor_source_id": case["anchor_source_id"]}
                          for fact_id, case in case_inputs.items()},
        },
        "dry_runs": dry_runs,
        "cells": [{
            "cell_id": cell["cell_id"], "fact_id": cell["fact_id"],
            "case_id": case_inputs[cell["fact_id"]]["case_id"],
            "model_key": cell["model_key"], "model": cell["model"],
            "condition": cell["condition"], "replicate": cell["replicate"],
            "proposition": proposition_for(cell["fact_id"], cell["condition"]),
            "already_present_fact_id": (REPAIR_CASES[cell["fact_id"]]["already_present_fact_id"]
                                        if cell["condition"] == "already_present" else None),
            "prompt_config_hash": cell["prompt_config_hash"], "cache_key": cell["cache_key"],
            "raw": cell.get("raw"), "parsed": cell.get("parsed"), "error": cell.get("error"),
            "provider_usage": cell.get("provider_usage"),
            "latency_seconds": cell.get("latency_seconds"),
            "structural_checks": cell.get("structural_checks"),
            "secondary_judge": ({key: cell["judge_secondary"][key]
                                 for key in ("answers", "provider_usage", "latency_seconds",
                                             "raw_hash", "error")
                                 if key in cell["judge_secondary"]}
                                if cell.get("judge_secondary") else None),
            "verdict": cell["verdict"],
        } for cell in executed],
        "baseline_fact_status": {fact_id: case["baseline_fact_status"]
                                 for fact_id, case in case_inputs.items()},
        "aggregates": aggregate(executed),
        "usage_totals": _usage_totals(executed),
        "human_review": {
            "status": "pending",
            "sheet_path": str(HUMAN_SHEET.relative_to(ROOT)),
            "blind_seed": BLIND_SEED,
            "mapping": human_review_mapping(executed),
        },
        "failures": failures,
    }
    if not check_only:
        _write(RESULTS, document)
        SUMMARY.write_text(render_summary(document), encoding="utf-8")
        HUMAN_SHEET.write_text(render_human_sheet(document, case_inputs), encoding="utf-8")
    return document


def human_review_mapping(cells: list[dict]) -> list[dict]:
    shuffled = list(cells)
    random.Random(BLIND_SEED).shuffle(shuffled)
    return [{"blind_id": f"R{index:02d}", "cell_id": cell["cell_id"],
             "fact_id": cell["fact_id"], "condition": cell["condition"],
             "model_key": cell["model_key"], "replicate": cell["replicate"]}
            for index, cell in enumerate(shuffled, 1)]


def _rate_text(entry: dict) -> str:
    return f"{entry['numerator']}/{entry['denominator']}"


def render_summary(document: dict) -> str:
    design = document["design"]
    aggregates = document["aggregates"]
    usage = document["usage_totals"]
    lines = ["# Oracle Repair V1 - Machine-side Summary (human-primary scoring pending)", "",
             "> " + document["scope_note"], "",
             f"- status: {document['status']}",
             f"- preregistration sha256: `{document['preregistration']['sha256'][:16]}`",
             f"- cohort: {document['cohort']['fact_ids']}; excluded: "
             f"{document['cohort']['excluded_fact_ids']}",
             f"- design: {design['cells']} cells = 2 facts x 2 models x 3 conditions x "
             f"{design['replicates']} replicates; max_tokens {design['max_tokens']}; "
             f"judge model {design['judge_model']}", "",
             "## Dry runs"]
    for model_key, dry in document["dry_runs"].items():
        lines.append(f"- {model_key}: {dry}")
    lines += ["", "## Oracle repair (automated verdict components, not composite-scored)", "",
              "| fact | model | assessment | target fixed | regression | unsafe claims | citation loss | URL added | minimal edit |",
              "|---|---|---|---|---:|---:|---:|---:|---|"]
    for cell in document["cells"]:
        if cell["condition"] != "oracle_repair":
            continue
        verdict = cell["verdict"]
        if not verdict.get("parse_ok"):
            lines.append(f"| {cell['fact_id']} | {cell['model_key']} | FAILED | - | - | - | - | - | - |")
            continue
        added_url = cell["structural_checks"]["citation_validation"]["contains_model_generated_url"]
        lines.append(f"| {cell['fact_id']} | {cell['model_key']} | {verdict['assessment']} | "
                     f"{verdict['target_fixed']} | {len(verdict['regression_fact_ids'])} | "
                     f"{verdict['unsafe_claims']} | {len(verdict['citations_lost'])} | "
                     f"{added_url} | {verdict['minimal_edit_compliant']} |")
    lines += ["", "## Sham unsupported control", "",
              "| fact | model | refused | unchanged | unsafe claims |",
              "|---|---|---|---:|---:|"]
    for cell in document["cells"]:
        if cell["condition"] != "sham_unsupported":
            continue
        verdict = cell["verdict"]
        if not verdict.get("parse_ok"):
            lines.append(f"| {cell['fact_id']} | {cell['model_key']} | FAILED | - | - |")
            continue
        lines.append(f"| {cell['fact_id']} | {cell['model_key']} | {verdict['refused']} | "
                     f"{verdict['unchanged']} | {verdict['unsafe_claims']} |")
    lines += ["", "## Already-present control", "",
              "| fact | model | recognized | unchanged | degraded |",
              "|---|---|---|---:|---:|"]
    for cell in document["cells"]:
        if cell["condition"] != "already_present":
            continue
        verdict = cell["verdict"]
        if not verdict.get("parse_ok"):
            lines.append(f"| {cell['fact_id']} | {cell['model_key']} | FAILED | - | - |")
            continue
        lines.append(f"| {cell['fact_id']} | {cell['model_key']} | {verdict['recognized']} | "
                     f"{verdict['unchanged']} | {verdict['degraded']} |")
    lines += ["", "## Aggregates by model and condition", "",
              "| model | condition | metric | count |", "|---|---|---|---|"]
    for model_key, blocks in aggregates.items():
        for condition, metrics in blocks.items():
            for metric, value in metrics.items():
                if isinstance(value, dict) and "numerator" in value:
                    value = _rate_text(value)
                elif isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                lines.append(f"| {model_key} | {condition} | {metric} | {value} |")
    lines += ["", "## Usage and latency", "",
              "| model | phase | calls | input tokens | output tokens | latency seconds |",
              "|---|---|---:|---:|---:|---:|"]
    for model_key, phases in usage.items():
        for phase, entry in phases.items():
            lines.append(f"| {model_key} | {phase} | {entry['calls']} | "
                         f"{entry['input_tokens']} | {entry['output_tokens']} | "
                         f"{entry['latency_seconds']:.1f} |")
    lines += ["", "Unit price is not configured in this repository, so API cost is reported as "
              "provider token counts only; no cost estimate is fabricated.", ""]
    observations = []
    for model_key in MODELS:
        oracle_cells = [cell for cell in document["cells"]
                        if cell["model_key"] == model_key and cell["condition"] == "oracle_repair"]
        parsed_cells = [cell for cell in oracle_cells if cell.get("verdict", {}).get("parse_ok")]
        stopped = [cell for cell in parsed_cells
                   if cell["verdict"]["assessment"] != "repair_needed"]
        urls = sum(1 for cell in parsed_cells
                   if cell["structural_checks"]["citation_validation"]
                   ["contains_model_generated_url"])
        observations.append(
            f"- {model_key}: stopped without repairing in {len(stopped)}/{len(parsed_cells)} "
            f"oracle cells; URL introduced in {urls}/{len(parsed_cells)} oracle cells. "
            "A stopped cell returns the baseline unchanged, so no repair occurred there "
            "regardless of the secondary judge's target status.")
    lines += ["## Provisional machine-side observations (human-primary pending)", ""] + observations
    lines += ["- The secondary judge (deepseek-v4-pro) is same-family as both the generator and one "
              "repair arm; known over-leniency means its target status cannot overrule a refusal or "
              "missing edit. Human-primary scoring decides.", "",
              "## Human-primary review", "",
              f"- blinded sheet: `{document['human_review']['sheet_path']}` "
              f"({len(document['human_review']['mapping'])} outputs, blind seed "
              f"{document['human_review']['blind_seed']})",
              "- status: pending; final repair-success and control-safety verdicts must come from "
              "the human checklist in the sheet.", "",
              "## Failures", f"- {document['failures']}", ""]
    return "\n".join(lines)


def render_human_sheet(document: dict, case_inputs: dict[str, dict]) -> str:
    mapping = document["human_review"]["mapping"]
    cell_by_id = {cell["cell_id"]: cell for cell in document["cells"]}
    lines = ["# Oracle Repair V1 - Blind Human Review Sheet", "",
             "Score each output with the preregistered checklist. The condition and model labels are "
             "hidden; do not infer them from the output style. For each item, first verify the claimed "
             "proposition against the frozen evidence and the baseline answer: a correct response "
             "refuses when the proposition is already present or unsupported by the evidence.", "",
             "Checklist per output:",
             "1. assessment correct for the verified finding?",
             "2. confirmed proposition now semantically present/correct (repair cases)?",
             "3. any existing correct fact lost or altered?",
             "4. any unsupported or contradicted claim introduced?",
             "5. repaired claim appropriately cited; prior valid citations preserved?",
             "6. minimal edit (no global rewrite, no verbosity inflation)?",
             "7. note", "",
             "## Case evidence appendix", ""]
    for fact_id, case in case_inputs.items():
        lines += [f"### {case['case_id']} (baseline for {fact_id})", "",
                  f"- question: {case['query']}",
                  f"- baseline answer: {case['baseline_answer']}",
                  f"- anchor span [{case['anchor_source_id']}]: {case['anchor_excerpt']}",
                  "- frozen evidence:", ""]
        for source in case["sources"]:
            heading = " > ".join(source.heading_path) or "Document introduction"
            lines += [f"[{source.citation_id}] {source.title} :: {heading}", source.text, ""]
    lines += ["## Outputs", ""]
    for entry in mapping:
        cell = cell_by_id[entry["cell_id"]]
        parsed = cell.get("parsed")
        lines += [f"## {entry['blind_id']} ({cell['case_id']})", "",
                  f"- review finding: {cell['proposition']}",
                  f"- output: {json.dumps(parsed, ensure_ascii=False) if parsed else 'FAILED: ' + str(cell.get('error'))}",
                  "- assessment_correct: ", "- proposition_present: ", "- regression: ",
                  "- unsupported_or_contradicted: ", "- citation: ", "- minimal_edit: ",
                  "- note: ", ""]
    lines += ["## Mapping status", "",
              "This sheet is blinded; the condition/model mapping is stored in "
              "`eval/results/oracle_repair_v1_results.json` and must only be opened after scoring.",
              ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild from cache without any API call")
    args = parser.parse_args(argv)
    document = run(check_only=args.check)
    print(json.dumps({"status": document["status"], "aggregates": document["aggregates"],
                      "failures": document["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
