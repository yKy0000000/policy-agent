"""Measurement Validity Audit V1 (Validate only).

Question 1: how many of the 10 nominal problematic facts are real answer-level errors?
Question 2: are there hidden errors among judge-marked-covered facts?
Question 3: are the 022/032 flips partner-context sensitivity, forced-differentiation,
or plain test-retest nondeterminism?
Question 4: can a trustworthy cleaned genuine-error cohort be frozen?

Read-only over frozen artifacts; no production change, no sufficiency judge, no repair.
Adjudication uses a different model (deepseek-v4-pro) than the generator/judge
(deepseek-v4-flash), which is different-model but same-provider/family.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from eval.run_answer_eval import (_V3Cache, _judge_messages, _parse_judge, _sha256,
                                  _stable_hash, V3_JUDGE_MAX_TOKENS)
from src.generator import assign_evidence_sources
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
CACHE = ROOT / "cache/measurement_validity_audit_cache.json"
RESULTS = ROOT / "eval/results/measurement_validity_audit.json"
SUMMARY = ROOT / "eval/results/measurement_validity_audit.md"
HUMAN_SHEET = ROOT / "eval/results/measurement_validity_audit_human_review.md"

SEED = 20260926
ADJUDICATOR_MODEL = "deepseek-v4-pro"
JUDGE_MODEL_EXPECTED = "deepseek-v4-flash"
STRATUM_A_EXTRA = ("VAL-001-030", "VAL-001-032")
STABILITY_CASES = ("VAL-001-008", "VAL-001-022", "VAL-001-030", "VAL-001-032", "VAL-001-050")
STABILITY_CONDITIONS = ("S1_isolated", "S2_minilm_partner", "S3_coverage_partner",
                        "S4_identical_copy", "S5_repeat_s3")
LABELS = ("SEMANTICALLY_PRESENT", "ABSENT_OR_INCORRECT", "AMBIGUOUS")
NOMINAL_FACT_RE = re.compile(r"^VAL-001-\d{3}-F\d+[ab]?$")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Pure selection / metric helpers
# --------------------------------------------------------------------------- #

def nominal_problematic_facts(utilization: dict) -> list[dict]:
    """9 nominal omission facts + 1 nominal incorrect-synthesis fact, from frozen results."""
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    facts = []
    for case_id in utilization["cohort"]["gap_ids"]:
        arm = rows[case_id]["arms"]["baseline"]
        diagnosis = {d["fact_id"]: d for d in arm["pipeline_diagnosis"]}
        for fact_id in arm["quality"]["grounded_missing_fact_ids"]:
            cause = (diagnosis.get(fact_id) or {}).get("cause")
            facts.append({"case_id": case_id, "fact_id": fact_id,
                          "nominal_type": ("incorrect_synthesis" if cause == "synthesis_error"
                                           else "omission")})
    facts.sort(key=lambda item: item["fact_id"])
    return facts


def sample_stratum_a(cases: list[str], covered_by_case: dict[str, list[str]],
                     rng: random.Random, per_case: int = 2) -> list[str]:
    """Deterministic round-robin sample; backfill deficit in fixed case order."""
    picked: list[tuple[str, str]] = []
    for case_id in cases:
        for fact_id in sorted(covered_by_case.get(case_id, []))[:per_case]:
            picked.append((case_id, fact_id))
    deficit = per_case * len(cases) - len(picked)
    while deficit > 0:
        for case_id in cases:
            extra = [f for f in sorted(covered_by_case.get(case_id, [])) if (case_id, f) not in picked]
            if extra:
                picked.append((case_id, rng.choice(extra)))
                deficit -= 1
                if deficit == 0:
                    break
    return [fact_id for _, fact_id in picked]


def sample_stratum_b(control_cases: list[str], covered_by_case: dict[str, list[str]],
                     rng: random.Random, exclude: tuple[str, ...] = STRATUM_A_EXTRA,
                     count: int = 20) -> list[str]:
    eligible = sorted(c for c in control_cases if c not in exclude and covered_by_case.get(c))
    chosen = rng.sample(eligible, min(count, len(eligible)))
    return [rng.choice(sorted(covered_by_case[c])) for c in sorted(chosen)]


def build_packet(query: str, answer: str, fact: dict) -> dict:
    """Blinded adjudication packet: query + answer + verbatim frozen source spans only."""
    return {"question": query, "answer": answer,
            "evidence": [{"source_id": f"E{index}",
                          "document": support["document"],
                          "section": support.get("section", ""),
                          "excerpt": support["source_excerpt"],
                          "context": support.get("context_excerpt", "")}
                         for index, support in enumerate(fact["support"], 1)]}


def parse_adjudication(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    data = json.loads(text)
    label = str(data["label"]).upper()
    if label not in LABELS:
        raise ValueError(f"invalid adjudication label: {label}")
    return {"label": label, "diagnostic_tag": str(data.get("diagnostic_tag", "other")),
            "reason": str(data.get("reason", ""))[:400]}


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n == 0:
        return None, None
    p = k / n
    denominator = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, (centre - margin) / denominator), min(1.0, (centre + margin) / denominator))


def _case_complete(judged_facts: list[dict]) -> bool:
    return bool(judged_facts) and all(
        fact["status"] == "covered" and fact["citation_status"] == "supported"
        for fact in judged_facts)


def stability_metrics(target_labels: dict[str, dict[str, dict]]) -> dict:
    """target_labels: condition -> {fact_id: {status, citation_status}} for the fixed target."""
    fact_ids = sorted({fid for labels in target_labels.values() for fid in labels})
    conditions = list(target_labels)

    def grounded(fid, condition):
        entry = target_labels[condition].get(fid, {})
        return entry.get("status") == "covered" and entry.get("citation_status") == "supported"

    e_fact = sum(1 for fid in fact_ids
                 if len({grounded(fid, c) for c in conditions}) > 1)
    case_complete = {c: _case_complete([{"status": "covered" if grounded(fid, c) else "missing",
                                         "citation_status": "supported"}
                                        for fid in fact_ids]) for c in conditions}
    e_case = 1 if len(set(case_complete.values())) > 1 else 0
    partner = target_labels.get("S2_minilm_partner", {})
    coverage = target_labels.get("S3_coverage_partner", {})
    e_partner = sum(1 for fid in fact_ids if partner.get(fid) != coverage.get(fid)) \
        if partner and coverage else None
    repeat = target_labels.get("S5_repeat_s3", {})
    e_repeat = sum(1 for fid in fact_ids if coverage.get(fid) != repeat.get(fid)) \
        if coverage and repeat else None
    identical = target_labels.get("S4_identical_copy", {})
    # In S4 both A and B are the target; forced differentiation is measured elsewhere by
    # comparing the target label under S4 with the target label under S1/S3.
    e_identical = sum(1 for fid in fact_ids
                      if identical.get(fid) != coverage.get(fid)) if identical and coverage else None
    return {"E_fact": e_fact, "fact_count": len(fact_ids), "E_case": e_case,
            "E_partner": e_partner, "E_repeat": e_repeat,
            "E_identical_copy_vs_coverage": e_identical,
            "case_complete_by_condition": case_complete,
            "grounded_by_condition": {c: {fid: grounded(fid, c) for fid in fact_ids}
                                      for c in conditions}}


def cleaned_cohort(nominal: list[dict], adjudications: dict[str, dict],
                   human_reviewed: dict[str, str] | None = None) -> dict:
    human_reviewed = human_reviewed or {}
    genuine, ambiguous, present, negated = [], [], [], []
    for item in nominal:
        verdict = adjudications.get(item["fact_id"], {}).get("label")
        if verdict == "ABSENT_OR_INCORRECT":
            if human_reviewed.get(item["fact_id"]) == "SEMANTICALLY_PRESENT":
                negated.append(item["fact_id"])
            else:
                genuine.append(item)
        elif verdict == "AMBIGUOUS":
            ambiguous.append(item["fact_id"])
        elif verdict == "SEMANTICALLY_PRESENT":
            present.append(item["fact_id"])
    return {"status": "pending_human_review" if human_reviewed else "pending_human_review",
            "genuine_error_facts": genuine, "ambiguous_facts": ambiguous,
            "semantically_present_facts": present, "human_negated_facts": negated}


# --------------------------------------------------------------------------- #
# Adjudication (different model)
# --------------------------------------------------------------------------- #

ADJUDICATOR_SYSTEM = (
    "You are a rigorous policy-answer adjudicator. You decide ONLY whether the supplied answer "
    "already conveys, in meaning, the information supported by the supplied source evidence. "
    "Do not use outside knowledge. Do not require literal wording. If the answer states related "
    "content, judge whether its condition, scope, relationship, and conclusion are semantically "
    "correct with respect to the evidence. Reply with JSON only: "
    '{\"label\":\"SEMANTICALLY_PRESENT|ABSENT_OR_INCORRECT|AMBIGUOUS\",'
    '\"diagnostic_tag\":\"genuine_omission|incorrect_synthesis|paraphrase|merged_expression|'
    'rubric_overgranular|judge_error|unclear_source|other\",\"reason\":\"brief\"}.')


def adjudicate(packet: dict, cache: _V3Cache, client, failures: list, item_id: str) -> dict | None:
    key = _stable_hash({"version": "measurement-validity-v1", "model": client.config.model,
                        "packet": packet})
    cached = cache.get(key)
    if cached is None:
        messages = [{"role": "system", "content": ADJUDICATOR_SYSTEM},
                    {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}]
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=400, temperature=0.0)
            cached = {"kind": "adjudication", "model": client.config.model,
                      "parsed": parse_adjudication(raw), "raw_hash": _stable_hash(raw),
                      "provider_usage": usage}
            cache.set(key, cached)
        except Exception as error:
            failures.append({"kind": "adjudication", "item": item_id,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    return cached["parsed"]


# --------------------------------------------------------------------------- #
# Partner-context stability (existing judge)
# --------------------------------------------------------------------------- #

def judge_target(case_id: str, condition: str, labeled_answers: dict[str, str],
                 chunk_meta: dict, rubric_case: dict, cache: _V3Cache, client,
                 failures: list, *, replicate: int = 0,
                 return_all_labels: bool = False) -> dict | None:
    sources = assign_evidence_sources([SimpleNamespace(**chunk)
                                       for chunk in _case_chunks(case_id, chunk_meta)])
    labeled = {label: {"generation": {"answer": answer}, "sources": sources}
               for label, answer in labeled_answers.items()}
    payload = {"query": _CASE_QUERY[case_id],
               "facts": [{"fact_id": fact["fact_id"], "fact": fact["statement"]}
                         for fact in rubric_case["facts"]]}
    messages = _judge_messages(payload, labeled)
    key = _stable_hash({"version": "measurement-validity-stability-v1", "case_id": case_id,
                        "condition": condition, "replicate": replicate,
                        "model": client.config.model, "messages": messages})
    cached = cache.get(key)
    if cached is None:
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS,
                                                    temperature=0.0)
            parsed = _parse_judge(raw, set(labeled),
                                  {f["fact_id"] for f in rubric_case["facts"]})
            cached = {"kind": "stability_judge", "answers": parsed,
                      "raw_hash": _stable_hash(raw), "provider_usage": usage}
            cache.set(key, cached)
        except Exception as error:
            failures.append({"kind": "stability", "case_id": case_id, "condition": condition,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    def labels_for(label: str) -> dict[str, dict]:
        return {fact["fact_id"]: {"status": fact["status"],
                                  "citation_status": fact["citation_status"]}
                for fact in cached["answers"][label]["facts"]}
    if return_all_labels:
        return {label: labels_for(label) for label in labeled}
    return labels_for("A")


_CASE_QUERY: dict[str, str] = {}
_CASE_CHUNKS: dict[str, list[dict]] = {}


def _case_chunks(case_id: str, chunk_meta: dict) -> list[dict]:
    return [_CHUNKS[(case_id, cid)] for cid in _CASE_CHUNKS[case_id]]


_CHUNKS: dict[tuple[str, str], dict] = {}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def run(*, skip_adjudication: bool = False, skip_stability: bool = False,
        human_reviewed: dict[str, str] | None = None) -> dict:
    global _CASE_QUERY
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    transfer = _json(TRANSFER)
    utilization = _json(UTILIZATION)
    utilization_rows = {row["case_id"]: row for row in utilization["cases"]
                        if row["status"] == "complete"}
    transfer_rows = {row["case_id"]: row for row in transfer["cases"] if row["status"] == "complete"}
    rubric_cases = {case["case_id"]: case for case in rubric["cases"]}
    facts_by_id = {fact["fact_id"]: fact for case in rubric["cases"] for fact in case["facts"]}
    _CASE_QUERY = {case["case_id"]: case["query"] for case in queries["cases"]}
    for case_id, item in transfer["preparation"]["arms"]["bge_top5"].items():
        _CASE_CHUNKS[case_id] = [chunk["chunk_id"] for chunk in item["chunks"]]
        for chunk in item["chunks"]:
            _CHUNKS[(case_id, chunk["chunk_id"])] = chunk

    # --- selection (frozen before any adjudication) ---
    nominal = nominal_problematic_facts(utilization)
    covered_by_case = {case_id: [fact["fact_id"] for fact in row["arms"]["baseline"]["judge"]["facts"]
                                 if fact["status"] == "covered"]
                       for case_id, row in utilization_rows.items()}
    baseline_complete = {case_id: row["arms"]["baseline"]["quality"]["grounded_fact_complete"]
                         for case_id, row in utilization_rows.items()}
    controls = [case_id for case_id, complete in baseline_complete.items() if complete]
    rng_a = random.Random(SEED)
    stratum_a = sample_stratum_a(sorted(set(utilization["cohort"]["gap_ids"]) | set(STRATUM_A_EXTRA)),
                                 covered_by_case, rng_a)
    rng_b = random.Random(SEED)
    stratum_b = sample_stratum_b(controls, covered_by_case, rng_b)
    covered_sample = [{"fact_id": fid, "stratum": "A"} for fid in stratum_a] + \
                     [{"fact_id": fid, "stratum": "B"} for fid in stratum_b]
    rng_h = random.Random(SEED)
    human_covered = ([{"fact_id": fid, "stratum": "A"} for fid in sorted(stratum_a)[:0]] +
                     [{"fact_id": fid, "stratum": "A"} for fid in rng_h.sample(stratum_a, 5)] +
                     [{"fact_id": fid, "stratum": "B"} for fid in rng_h.sample(stratum_b, 5)])
    human_items = [{"fact_id": item["fact_id"], "nominal_type": item["nominal_type"]}
                   for item in nominal] + human_covered

    selection = {"seed": SEED, "adjudicator_model": ADJUDICATOR_MODEL,
                 "nominal_problematic_facts": nominal,
                 "nominal_counts": {"omission": sum(1 for i in nominal if i["nominal_type"] == "omission"),
                                    "incorrect_synthesis": sum(1 for i in nominal
                                                               if i["nominal_type"] == "incorrect_synthesis")},
                 "stratum_a_case_ids": sorted(set(utilization["cohort"]["gap_ids"]) | set(STRATUM_A_EXTRA)),
                 "stratum_a_facts": stratum_a, "stratum_b_facts": stratum_b,
                 "covered_sample_size": len(covered_sample), "human_review_items": human_items}

    config = LLMConfig.from_env(ROOT / ".env")
    cache = _V3Cache(CACHE)
    failures: list = []
    adjudicator = OpenAIChatCompletionsClient(replace(config, model=ADJUDICATOR_MODEL))
    judge = OpenAIChatCompletionsClient(replace(config, model=JUDGE_MODEL_EXPECTED))

    adjudications: dict[str, dict] = {}
    if not skip_adjudication:
        for item in [{"fact_id": i["fact_id"]} for i in nominal] + covered_sample:
            fact_id = item["fact_id"]
            row = utilization_rows[next(c for c in utilization_rows
                                        if fact_id.startswith(c + "-"))]
            packet = build_packet(_CASE_QUERY[row["case_id"]],
                                  row["arms"]["baseline"]["answer"], facts_by_id[fact_id])
            verdict = adjudicate(packet, cache, adjudicator, failures, fact_id)
            adjudications[fact_id] = {"nominal": any(i["fact_id"] == fact_id for i in nominal),
                                      "stratum": next((s["stratum"] for s in covered_sample
                                                       if s["fact_id"] == fact_id), None),
                                      "packet_source_ids": [e["source_id"] for e in packet["evidence"]],
                                      **(verdict or {"label": "FAILED", "diagnostic_tag": "other",
                                                     "reason": ""})}
            print(f"Adjudicated {fact_id} -> {adjudications[fact_id]['label']}", flush=True)

    stability: dict[str, dict] = {}
    if not skip_stability:
        for case_id in STABILITY_CASES:
            target = utilization_rows[case_id]["arms"]["baseline"]["answer"]
            minilm = transfer_rows[case_id]["arms"]["minilm_top5"]["answer"]
            coverage = utilization_rows[case_id]["arms"]["coverage_aware"]["answer"]
            conditions = {
                "S1_isolated": {"A": target},
                "S2_minilm_partner": {"A": target, "B": minilm},
                "S3_coverage_partner": {"A": target, "B": coverage},
                "S4_identical_copy": {"A": target, "B": target},
                "S5_repeat_s3": {"A": target, "B": coverage},
            }
            case_labels = {}
            for condition in STABILITY_CONDITIONS:
                labels = judge_target(case_id, condition, conditions[condition], _CHUNKS,
                                      rubric_cases[case_id], cache, judge, failures,
                                      replicate=1 if condition == "S5_repeat_s3" else 0)
                if labels is not None:
                    case_labels[condition] = labels
            pair = judge_target(case_id, "S4_identical_copy", conditions["S4_identical_copy"],
                                _CHUNKS, rubric_cases[case_id], cache, judge, failures,
                                return_all_labels=True)
            identical_within = None
            if pair and "A" in pair and "B" in pair:
                def grounded(entry):
                    return (entry["status"] == "covered"
                            and entry["citation_status"] == "supported")
                identical_within = sum(1 for fid in pair["A"]
                                       if grounded(pair["A"][fid]) != grounded(pair["B"][fid]))
            stability[case_id] = {"target_answer_hash": _stable_hash(target),
                                  "labels": case_labels,
                                  "E_identical_pair_within": identical_within,
                                  **stability_metrics(case_labels)}
            print(f"Stability {case_id}: {stability[case_id]['case_complete_by_condition']}",
                  flush=True)

    result = _finalize(selection, adjudications, stability, nominal, covered_sample,
                       facts_by_id, failures, human_reviewed)
    _write(RESULTS, result)
    _write(SUMMARY, _render(result))
    _write(HUMAN_SHEET, _render_human_sheet(result, facts_by_id))
    return result


def _finalize(selection, adjudications, stability, nominal, covered_sample, facts_by_id,
              failures, human_reviewed) -> dict:
    nominal_labels = [adjudications.get(item["fact_id"], {}).get("label") for item in nominal]
    omission = [item for item in nominal if item["nominal_type"] == "omission"]
    incorrect = [item for item in nominal if item["nominal_type"] == "incorrect_synthesis"]

    def real_error(items):
        k = sum(1 for item in items
                if adjudications.get(item["fact_id"], {}).get("label") == "ABSENT_OR_INCORRECT")
        lo, hi = wilson_interval(k, len(items))
        return {"numerator": k, "denominator": len(items), "proportion": k / len(items) if items else None,
                "wilson_95": [lo, hi]}
    covered_hidden = sum(1 for item in covered_sample
                         if adjudications.get(item["fact_id"], {}).get("label") == "ABSENT_OR_INCORRECT")
    lo, hi = wilson_interval(len(covered_sample) - covered_hidden, len(covered_sample))
    covered_side = {"sample_size": len(covered_sample), "hidden_errors": covered_hidden,
                    "real_covered_numerator": len(covered_sample) - covered_hidden,
                    "proportion_real_covered": (len(covered_sample) - covered_hidden) / len(covered_sample)
                    if covered_sample else None, "wilson_95": [lo, hi]}
    return {"schema_version": 1, "version": "measurement-validity-audit-v1", "status": "complete",
            "scope_note": ("Development/diagnostic audit on frozen artifacts; Validate only. "
                           "Adjudication is different-model, same-family (deepseek-v4-pro vs "
                           "deepseek-v4-flash), not family-independent."),
            "selection": selection,
            "adjudications": adjudications,
            "nominal_error_side": {"omission": real_error(omission),
                                   "incorrect_synthesis": real_error(incorrect),
                                   "combined_descriptive": real_error(nominal),
                                   "labels": dict(zip([i["fact_id"] for i in nominal], nominal_labels))},
            "covered_side": covered_side,
            "stability": stability,
            "stability_metrics": {case_id: {k: v for k, v in data.items()
                                            if k.startswith("E_") or k == "case_complete_by_condition"}
                                  for case_id, data in stability.items()},
            "cleaned_cohort": cleaned_cohort(nominal, adjudications, human_reviewed),
            "failures": failures}


def _render(result: dict) -> str:
    nominal = result["nominal_error_side"]
    covered = result["covered_side"]
    lines = ["# Measurement Validity Audit V1", "", "> " + result["scope_note"], "",
             "## Selection (frozen before adjudication)",
             f"- seed: {result['selection']['seed']}",
             f"- nominal problematic facts: {result['selection']['nominal_counts']}",
             f"- Stratum A cases: {result['selection']['stratum_a_case_ids']}",
             f"- Stratum A facts: {result['selection']['stratum_a_facts']}",
             f"- Stratum B facts: {result['selection']['stratum_b_facts']}",
             f"- covered-side sample: {result['selection']['covered_sample_size']}",
             f"- human-review subset: {[i['fact_id'] for i in result['selection']['human_review_items']]}",
             "", "## Nominal-error side",
             f"- omission: {nominal['omission']}",
             f"- incorrect_synthesis: {nominal['incorrect_synthesis']}",
             f"- combined (descriptive only): {nominal['combined_descriptive']}",
             f"- labels: {nominal['labels']}", "", "## Covered side",
             f"- {covered}", "", "## Stability"]
    for case_id, data in result["stability"].items():
        lines.append(f"- {case_id}: E_fact={data['E_fact']}/{data['fact_count']} "
                     f"E_case={data['E_case']} E_partner={data['E_partner']} "
                     f"E_repeat={data['E_repeat']} "
                     f"E_identical_within={data.get('E_identical_pair_within')} "
                     f"E_identical_vs_coverage={data.get('E_identical_copy_vs_coverage')} "
                     f"complete_by_condition={data['case_complete_by_condition']}")
    lines += ["", "## Cleaned cohort",
              f"- status: {result['cleaned_cohort']['status']}",
              f"- genuine_error_facts: {[i['fact_id'] for i in result['cleaned_cohort']['genuine_error_facts']]}",
              f"- ambiguous: {result['cleaned_cohort']['ambiguous_facts']}",
              f"- semantically_present: {result['cleaned_cohort']['semantically_present_facts']}",
              "", "## Failures", f"- {result['failures']}", ""]
    return "\n".join(lines)


def _render_human_sheet(result: dict, facts_by_id: dict) -> str:
    lines = ["# Measurement Validity Audit V1 - Blind Human Review Sheet", "",
             "Same information the adjudicator saw. Record your verdict BEFORE comparing with the model.",
             "Allowed verdicts: SEMANTICALLY_PRESENT / ABSENT_OR_INCORRECT / AMBIGUOUS", ""]
    utilization = _json(UTILIZATION)
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    for item in result["selection"]["human_review_items"]:
        fact_id = item["fact_id"]
        case_id = next(c for c in rows if fact_id.startswith(c + "-"))
        source = " || ".join(
            f"[{support['document']} :: {support.get('section', '')}] {support['source_excerpt']}"
            for support in facts_by_id[fact_id]["support"])
        lines += [f"## {fact_id}" + (" (nominal)" if item.get("nominal_type") else ""),
                  f"- question: {_CASE_QUERY.get(case_id, '')}",
                  f"- answer: {rows[case_id]['arms']['baseline']['answer']}",
                  f"- source: {source}",
                  "- your_verdict: ", "- your_note: ", ""]
    return "\n".join(lines)


def _source_text(fact: dict) -> str:
    return " || ".join(f"[{support['document']} :: {support.get('section','')}] "
                       f"{support['source_excerpt'][:600]}" for support in fact["support"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-adjudication", action="store_true")
    parser.add_argument("--skip-stability", action="store_true")
    args = parser.parse_args(argv)
    result = run(skip_adjudication=args.skip_adjudication, skip_stability=args.skip_stability)
    print(json.dumps({"nominal": result["nominal_error_side"],
                      "covered_side": result["covered_side"],
                      "cleaned": {k: v for k, v in result["cleaned_cohort"].items() if k != "genuine_error_facts"},
                      "failures": result["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
