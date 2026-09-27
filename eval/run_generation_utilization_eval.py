"""Coverage-aware generation prompt A/B on BGE Fixed-Top5 evidence.

Arm A: the unmodified production generation prompt (reuses the BGE Top5 answers
from the reranker transfer study). Arm B: the same prompt plus one short
completeness instruction. Everything else is identical (query, ordered BGE Top5
evidence, generator model, temperature, citations, validator, output schema).

Primary cohort: cases whose BGE Fixed-Top5 evidence is fact-complete. Only the
prompt differs. Validation V1 is development/diagnostic data, not untouched.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, median
from types import SimpleNamespace

from eval.analyze_evidence_geometry import _query_tags
from eval.metrics import score_facts
from eval.run_answer_eval import (_RecordingGenerationClient, _V3Cache, _judge_messages,
                                  _parse_judge, _score_v3_answer, _sha256, _stable_hash,
                                  V3_GENERATION_MAX_TOKENS, V3_JUDGE_MAX_TOKENS)
from eval.run_reranker_transfer_eval import transition_bucket
from eval.run_validation import VERSION as VALIDATION_VERSION
from eval.run_validation import _evidence_hash, _quality_summary
from src.generator import (GENERATION_PROMPT_VERSION, assign_evidence_sources,
                           build_grounded_messages, validate_citations)

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
GEOMETRY = ROOT / "eval/results/evidence_geometry_analysis.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
CACHE = ROOT / "cache/validation_v1_llm_cache.json"
RESULTS = ROOT / "eval/results/generation_utilization_results.json"
SUMMARY = ROOT / "eval/results/generation_utilization_summary.md"
HISTORICAL = ROOT / "eval/validation/results/validation_v1_results.json"

ARMS = ("baseline", "coverage_aware")
PROMPT_VARIANT = {"baseline": "production-v1", "coverage_aware": "coverage-aware-v1"}
COVERAGE_INSTRUCTION = (
    "Before finalizing the answer, make sure you have addressed every distinct part of the "
    "user's question that is directly supported by the provided evidence, including relevant "
    "conditions, scope, exceptions, steps, and list items. Do not omit a necessary point merely "
    "for brevity. Completeness must not come at the expense of grounding: do not add claims that "
    "are not supported by the provided evidence.")
JUDGE_VERSION = "generation-utilization-v1-answer-quality-v1"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Pure cohort / metric helpers
# --------------------------------------------------------------------------- #

def evidence_complete_ids(bge_evidence: dict, facts_by_case: dict) -> list[str]:
    return sorted(case_id for case_id, item in bge_evidence.items()
                  if len(item["available_fact_ids"]) == len(facts_by_case[case_id]))


def split_gap_and_control(cohort_ids: list[str], baseline_complete: dict) -> tuple[list, list]:
    gaps = [cid for cid in cohort_ids if not baseline_complete[cid]]
    controls = [cid for cid in cohort_ids if baseline_complete[cid]]
    return gaps, controls


def rescued_cases(gap_ids: list[str], challenger_complete: dict) -> list[str]:
    return [cid for cid in gap_ids if challenger_complete.get(cid)]


def control_regressions(control_ids: list[str], challenger_complete: dict) -> list[str]:
    return [cid for cid in control_ids if not challenger_complete.get(cid)]


def length_stats(answers: list[str]) -> dict:
    words = sorted(len(answer.split()) for answer in answers)
    if not words:
        return {"mean": None, "median": None, "p90": None, "n": 0}
    index = min(len(words) - 1, int(round(0.9 * (len(words) - 1))))
    return {"mean": mean(words), "median": median(words), "p90": words[index], "n": len(words)}


def facts_per_extra_100_tokens(facts_gained: int, token_delta: int) -> float | None:
    if token_delta <= 0:
        return None
    return facts_gained / (token_delta / 100.0)


# --------------------------------------------------------------------------- #
# Prompt variants (eval-only)
# --------------------------------------------------------------------------- #

def blind_order(case_id: str) -> dict[str, str]:
    first = "baseline" if int(_stable_hash({"case_id": case_id})[:8], 16) % 2 == 0 else "coverage_aware"
    return {"A": first, "B": "coverage_aware" if first == "baseline" else "baseline"}


def messages_for_variant(query: str, sources: list, variant: str) -> list[dict]:
    messages = build_grounded_messages(query, [], sources)
    if variant == "coverage_aware":
        messages = [dict(message) for message in messages]
        messages[0]["content"] = messages[0]["content"] + "\n\n" + COVERAGE_INSTRUCTION
    return messages


def identity_for(case_id: str, query: str, chunks: list[dict], model: str, variant: str) -> dict:
    sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
    messages = messages_for_variant(query, sources, variant)
    prompt_hash = _stable_hash({"messages": messages, "temperature": 0.0,
                                "max_tokens": V3_GENERATION_MAX_TOKENS,
                                "prompt_version": GENERATION_PROMPT_VERSION})
    evidence_hash = _evidence_hash(chunks)
    identity = {"validation_version": VALIDATION_VERSION, "case_id": case_id,
                "evidence_hash": evidence_hash, "prompt_config_hash": prompt_hash,
                "generator_model": model}
    # The production prompt keeps the historical key so BGE Top5 answers are reused
    # verbatim; a non-default variant is explicitly tagged to forge a distinct key.
    if variant != "baseline":
        identity["prompt_variant"] = PROMPT_VARIANT[variant]
    key = _stable_hash(identity)
    return {"key": key, "prompt_hash": prompt_hash, "evidence_hash": evidence_hash,
            "sources": sources, "messages": messages}


def generate_variant(case_id: str, query: str, chunks: list[dict], model: str, variant: str,
                     cache: _V3Cache, client, failures: list) -> dict | None:
    identity = identity_for(case_id, query, chunks, model, variant)
    cached = cache.get(identity["key"])
    if cached is None:
        try:
            recorder = _RecordingGenerationClient(client)
            answer = recorder.complete(identity["messages"],
                                       max_tokens=V3_GENERATION_MAX_TOKENS, temperature=0.0).strip()
            if not answer:
                raise ValueError("empty answer")
            cached = {"kind": "generation", "answer": answer,
                      "generation_hash": _stable_hash(answer), "evidence_hash": identity["evidence_hash"],
                      "prompt_config_hash": identity["prompt_hash"], "model": model,
                      "prompt_variant": PROMPT_VARIANT[variant], "provider_usage": recorder.usage}
            cache.set(identity["key"], cached)
        except Exception as error:
            failures.append({"kind": "generation", "case_id": case_id, "variant": variant,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    citation = validate_citations(cached["answer"], identity["sources"])
    return {"answer": cached["answer"], "generation_key": identity["key"],
            "generation_hash": cached["generation_hash"], "evidence_hash": identity["evidence_hash"],
            "provider_usage": cached["provider_usage"], "citation_validation": citation["validation"],
            "sources": identity["sources"], "chunks": chunks}


# --------------------------------------------------------------------------- #
# Judge
# --------------------------------------------------------------------------- #

_CASE_QUERY: dict[str, str] = {}
_CASE_FACTS: dict[str, list[dict]] = {}
_FACT_STATEMENT: dict[str, str] = {}
_CANDIDATE_FACTS: dict[str, list[str]] = {}


def judge_case(case_id: str, variants: dict, cache: _V3Cache, client, model: str,
               failures: list) -> dict | None:
    mapping = blind_order(case_id)
    labeled = {label: {"generation": {"answer": variants[arm]["answer"]},
                       "sources": variants[arm]["sources"]} for label, arm in mapping.items()}
    payload = {"query": _CASE_QUERY[case_id],
               "facts": [{"fact_id": fact["fact_id"], "fact": _FACT_STATEMENT[fact["fact_id"]]}
                         for fact in _CASE_FACTS[case_id]]}
    messages = _judge_messages(payload, labeled)
    key = _stable_hash({"validation_version": JUDGE_VERSION, "rubric_sha256": _sha256(RUBRIC),
                        "case_id": case_id, "judge_model": model,
                        "judge_prompt_config_hash": _stable_hash(
                            {"messages": messages, "temperature": 0.0,
                             "max_tokens": V3_JUDGE_MAX_TOKENS, "version": JUDGE_VERSION}),
                        "answer_hashes": {l: variants[a]["generation_hash"]
                                          for l, a in mapping.items()},
                        "evidence_hashes": {l: variants[a]["evidence_hash"]
                                            for l, a in mapping.items()}})
    cached = cache.get(key)
    if cached is None:
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS,
                                                    temperature=0.0)
            parsed = _parse_judge(raw, set(mapping), {f["fact_id"] for f in _CASE_FACTS[case_id]})
            cached = {"kind": "judge", "answers": parsed, "raw_hash": _stable_hash(raw),
                      "provider_usage": usage}
            cache.set(key, cached)
        except Exception as error:
            failures.append({"kind": "judge", "case_id": case_id,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    return {mapping[label]: cached["answers"][label] for label in mapping}


def score_arm(case_id: str, arm: str, variant: dict, judged: dict) -> dict:
    facts = _CASE_FACTS[case_id]
    chunks = variant["chunks"]
    scored = score_facts(facts, chunks)
    from eval.analyze_evidence_geometry import approx_tokens
    case = {"case_id": case_id, "facts": [{"fact_id": fact["fact_id"]} for fact in facts],
            "evidence": {"candidate_pool": {"covered_fact_ids": _CANDIDATE_FACTS[case_id]}},
            "variants": {arm: {"chunks": chunks,
                               "generation": {"answer": variant["answer"],
                                              "citation_validation": variant["citation_validation"]},
                               "available_fact_ids": scored["covered_fact_ids"],
                               "evidence_tokens": sum(approx_tokens(c["text"]) for c in chunks)}}}
    return _score_v3_answer(case, arm, judged)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def evaluate() -> dict:
    global _CASE_QUERY
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    transfer = _json(TRANSFER)
    bge_evidence = transfer["preparation"]["arms"]["bge_top5"]
    baseline_rows = {row["case_id"]: row for row in transfer["cases"]
                     if row["status"] == "complete"}
    _CASE_QUERY = {case["case_id"]: case["query"] for case in queries["cases"]}
    _load_support()
    for case in rubric["cases"]:
        _CASE_FACTS[case["case_id"]] = [{"fact_id": fact["fact_id"],
                                         "direct_chunk_ids": _SUPPORT[fact["fact_id"]]}
                                        for fact in case["facts"]]
        for fact in case["facts"]:
            _FACT_STATEMENT[fact["fact_id"]] = fact["statement"]
    _load_candidates(queries)

    facts_by_case = {cid: _CASE_FACTS[cid] for cid in _CASE_FACTS}
    cohort = evidence_complete_ids(bge_evidence, facts_by_case)
    baseline_complete = {cid: baseline_rows[cid]["arms"]["bge_top5"]["quality"]["grounded_fact_complete"]
                         for cid in cohort}
    gap_ids, control_ids = split_gap_and_control(cohort, baseline_complete)

    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    config = LLMConfig.from_env(ROOT / ".env")
    client = OpenAIChatCompletionsClient(config)
    cache = _V3Cache(CACHE)
    failures: list = []
    rows = []
    for case in queries["cases"]:
        case_id = case["case_id"]
        if case_id not in cohort:
            continue
        chunks = bge_evidence[case_id]["chunks"]
        variants = {}
        for variant in ARMS:
            generated = generate_variant(case_id, case["query"], chunks, config.model, variant,
                                         cache, client, failures)
            if generated is None:
                variants = {}
                break
            variants[variant] = generated
        if not variants:
            rows.append({"case_id": case_id, "status": "technical_failure"})
            continue
        judged = judge_case(case_id, variants, cache, client, config.model, failures)
        if judged is None:
            rows.append({"case_id": case_id, "status": "judge_failure"})
            continue
        row = {"case_id": case_id, "status": "complete", "blind_order": {
            label: arm for label, arm in judge_blind_map(case_id).items()}, "arms": {}}
        for variant in ARMS:
            row["arms"][variant] = {"answer": variants[variant]["answer"],
                                    "generation_key": variants[variant]["generation_key"],
                                    "provider_usage": variants[variant]["provider_usage"],
                                    **score_arm(case_id, variant, variants[variant], judged[variant])}
        rows.append(row)
        print(f"Completed {case_id}", flush=True)

    result = _finalize(rows, cohort, gap_ids, control_ids, baseline_complete,
                       bge_evidence, failures, config.model)
    _write(RESULTS, result)
    _write(SUMMARY, _render(result))
    return result


def judge_blind_map(case_id: str) -> dict:
    mapping = blind_order(case_id)
    return {label: ("baseline" if arm.endswith("minilm_top5") else "coverage_aware")
            for label, arm in mapping.items()}


_SUPPORT: dict[str, list[str]] = {}


def _load_support() -> None:
    global _SUPPORT
    from eval.run_validation import direct_support_map
    index = _json(ROOT / "cache/policy_index.json")
    _SUPPORT = direct_support_map(_json(RUBRIC), index["chunks"])


def _load_candidates(queries: dict) -> None:
    from eval.analyze_evidence_geometry import approx_tokens
    index = _json(ROOT / "cache/policy_index.json")
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in index["chunks"]}
    scopes = _json(GEOMETRY)["retrieval_cache"]["scopes"]
    for case in queries["cases"]:
        union = [chunk_meta[c] for c in sorted(scopes[case["case_id"]]["union"]) if c in chunk_meta]
        union = [{**chunk, "token_count": approx_tokens(chunk["text"])} for chunk in union]
        _CANDIDATE_FACTS[case["case_id"]] = score_facts(
            _CASE_FACTS[case["case_id"]], union)["covered_fact_ids"]


def _finalize(rows, cohort, gap_ids, control_ids, baseline_complete, bge_evidence,
              failures, model) -> dict:
    complete = [row for row in rows if row["status"] == "complete"]
    total_facts = sum(len(_CASE_FACTS[row["case_id"]]) for row in complete)
    summaries = {}
    for variant in ARMS:
        items = [{"quality": row["arms"][variant]["quality"],
                  "evidence_tokens": row["arms"][variant]["evidence_tokens"],
                  "pipeline_diagnosis": row["arms"][variant]["pipeline_diagnosis"],
                  "claim_diagnosis": row["arms"][variant]["claim_diagnosis"]}
                 for row in complete]
        summaries[variant] = _quality_summary(items, total_facts)
    # The paired grouped judge defines baseline AND challenger in the same controlled
    # context, so the gap/control split must come from THIS run, not the transfer study.
    cohort_ids = [row["case_id"] for row in complete]
    challenger_complete = {row["case_id"]: row["arms"]["coverage_aware"]["quality"]["grounded_fact_complete"]
                           for row in complete}
    baseline_complete_full = {row["case_id"]: row["arms"]["baseline"]["quality"]["grounded_fact_complete"]
                              for row in complete}
    gap_ids = [cid for cid in cohort_ids if not baseline_complete_full[cid]]
    control_ids = [cid for cid in cohort_ids if baseline_complete_full[cid]]
    rescued = rescued_cases(gap_ids, challenger_complete)
    regressed_controls = control_regressions(control_ids, challenger_complete)
    missing_facts = {row["case_id"]: row["arms"]["baseline"]["quality"]["grounded_missing_fact_ids"]
                     for row in complete if row["case_id"] in gap_ids}
    buckets = {"wrong_to_right": [], "right_to_wrong": [], "both_right": [], "both_wrong": []}
    for row in complete:
        key = transition_bucket(baseline_complete_full[row["case_id"]],
                                challenger_complete[row["case_id"]])
        buckets[key].append(row["case_id"])

    gained = lost = 0
    for row in complete:
        b = set(row["arms"]["baseline"]["quality"]["grounded_covered_fact_ids"])
        c = set(row["arms"]["coverage_aware"]["quality"]["grounded_covered_fact_ids"])
        gained += len(c - b)
        lost += len(b - c)

    base_words = [row["arms"]["baseline"]["answer"] for row in complete]
    chal_words = [row["arms"]["coverage_aware"]["answer"] for row in complete]
    base_stats, chal_stats = length_stats(base_words), length_stats(chal_words)
    base_tokens = sum((row["arms"]["baseline"]["provider_usage"].get("output_tokens") or 0)
                      for row in complete)
    chal_tokens = sum((row["arms"]["coverage_aware"]["provider_usage"].get("output_tokens") or 0)
                      for row in complete)
    length = {"baseline": {**base_stats, "output_tokens_total": base_tokens},
              "coverage_aware": {**chal_stats, "output_tokens_total": chal_tokens},
              "words_pct_increase": ((chal_stats["mean"] - base_stats["mean"]) / base_stats["mean"]
                                     if base_stats["mean"] else None),
              "facts_gained_per_extra_100_tokens": facts_per_extra_100_tokens(gained, chal_tokens - base_tokens)}

    enum_gaps = [cid for cid in cohort_ids
                 if _query_tags(_CASE_QUERY[cid], None)["enumeration_query"]]
    def cohort_delta(ids):
        b = sum(1 for cid in ids if baseline_complete_full.get(cid))
        c = sum(1 for cid in ids if challenger_complete.get(cid))
        return {"cases": len(ids), "baseline_complete": b, "coverage_complete": c, "delta": c - b}
    enumeration = {"enumeration": cohort_delta(enum_gaps),
                   "non_enumeration": cohort_delta([cid for cid in cohort if cid not in enum_gaps]),
                   "note": "secondary / post-hoc diagnostic; not a gate"}

    verdict = _verdict(summaries, rescued, regressed_controls, buckets, length)
    return {"schema_version": 1, "version": "generation-utilization-v1", "status": "complete",
            "scope_note": ("Validation V1 is development/diagnostic data; BGE Fixed Top5 evidence; "
                           "only the generation prompt differs."),
            "model": model, "prompt_variant_hashes": {v: PROMPT_VARIANT[v] for v in ARMS},
            "cohort": {"evidence_complete_cases": len(complete), "ids": cohort_ids,
                       "baseline_complete": sum(baseline_complete_full.values()),
                       "baseline_gap_cases": len(gap_ids), "gap_ids": gap_ids,
                       "control_cases": len(control_ids), "control_ids": control_ids,
                       "missing_facts": missing_facts},
            "summaries": summaries, "rescued_cases": rescued, "control_regressions": regressed_controls,
            "paired_transitions": buckets,
            "fact_level": {"grounded_facts_gained": gained, "grounded_facts_lost": lost,
                           "net_grounded_fact_gain": gained - lost},
            "length": length, "enumeration_diagnostic": enumeration,
            "failures": failures, "verdict": verdict, "cases": rows}


def _missing_facts(gap_ids: list[str]) -> dict:
    result = {}
    for cid in gap_ids:
        baseline = _json(TRANSFER)["cases"]
        # missing grounded facts are recomputed in _finalize context; here use frozen transfer row
        row = next((r for r in baseline if r["case_id"] == cid and r["status"] == "complete"), None)
        if row:
            result[cid] = row["arms"]["bge_top5"]["quality"]["grounded_missing_fact_ids"]
    return result


def _verdict(summaries, rescued, regressed_controls, buckets, length) -> dict:
    bge, cov = summaries["baseline"], summaries["coverage_aware"]
    micro_delta = cov["grounded_micro"] - bge["grounded_micro"]
    complete_delta = cov["grounded_complete_cases"] - bge["grounded_complete_cases"]
    bad_delta = ((cov["claim_counts"].get("unsupported", 0) + cov["claim_counts"].get("contradicted", 0)) -
                 (bge["claim_counts"].get("unsupported", 0) + bge["claim_counts"].get("contradicted", 0)))
    words_increase = length["words_pct_increase"] or 0.0
    if micro_delta < -1e-9 or complete_delta < 0 or bad_delta > 0:
        gate = "REGRESSION"
    elif len(rescued) == 0 and complete_delta <= 0:
        gate = "WASH"
    elif len(rescued) >= 3 and micro_delta > 0 and bad_delta <= 0 and len(regressed_controls) <= 1 \
            and words_increase <= 0.35:
        gate = "CLEAR UTILIZATION WIN"
    else:
        gate = "SMALL / MIXED WIN"
    return {"utilization_verdict": gate, "rescued_cases": len(rescued),
            "control_regressions": len(regressed_controls), "grounded_micro_delta": micro_delta,
            "grounded_complete_delta": complete_delta, "bad_claims_delta": bad_delta,
            "words_pct_increase": words_increase,
            "wrong_to_right": len(buckets["wrong_to_right"]),
            "right_to_wrong": len(buckets["right_to_wrong"])}


def _render(result: dict) -> str:
    base, cov = result["summaries"]["baseline"], result["summaries"]["coverage_aware"]
    v = result["verdict"]
    lines = ["# Generation Utilization A/B (coverage-aware prompt)", "",
             "> " + result["scope_note"], "",
             "## Cohort",
             f"- BGE evidence-complete cases: {result['cohort']['evidence_complete_cases']}",
             f"- baseline grounded-complete: {result['cohort']['baseline_complete']}",
             f"- baseline gap cases: {result['cohort']['baseline_gap_cases']} {result['cohort']['gap_ids']}",
             f"- missing facts: {result['cohort']['missing_facts']}",
             "", "## Overall Quality", "| Metric | Baseline | Coverage | Delta |", "|---|---:|---:|---:|"]
    for label, key in (("Answer Macro", "answer_macro"), ("Answer Micro", "answer_micro"),
                       ("Answer Complete", "fact_complete_cases"), ("Grounded Macro", "grounded_macro"),
                       ("Grounded Micro", "grounded_micro"), ("Grounded Complete", "grounded_complete_cases")):
        lines.append(f"| {label} | {base[key]:.3f} | {cov[key]:.3f} | {cov[key]-base[key]:+.3f} |"
                     if isinstance(base[key], float) else
                     f"| {label} | {base[key]} | {cov[key]} | {cov[key]-base[key]:+d} |")
    for label, key in (("Unsupported", "unsupported"), ("Contradicted", "contradicted")):
        lines.append(f"| {label} | {base['claim_counts'].get(key,0)} | {cov['claim_counts'].get(key,0)} | "
                     f"{cov['claim_counts'].get(key,0)-base['claim_counts'].get(key,0):+d} |")
    t = result["paired_transitions"]
    lines += ["", "## Gap Rescue", f"- rescued cases: {result['rescued_cases']}",
              f"- still incomplete: {[c for c in result['cohort']['gap_ids'] if c not in result['rescued_cases']]}",
              "", "## Control Regression",
              f"- baseline-complete controls: {result['cohort']['control_cases']}",
              f"- regressed controls: {result['control_regressions']}",
              "", "## Paired Transitions",
              f"- wrong→right {len(t['wrong_to_right'])}; right→wrong {len(t['right_to_wrong'])}; "
              f"both right {len(t['both_right'])}; both wrong {len(t['both_wrong'])}",
              f"- net complete gain: {v['grounded_complete_delta']}",
              "", "## Fact-Level",
              f"- grounded facts gained {result['fact_level']['grounded_facts_gained']}; "
              f"lost {result['fact_level']['grounded_facts_lost']}; "
              f"net {result['fact_level']['net_grounded_fact_gain']}",
              "", "## Answer Length",
              f"- words mean: baseline {v and result['length']['baseline']['mean']:.1f} → "
              f"coverage {result['length']['coverage_aware']['mean']:.1f} "
              f"({v['words_pct_increase']*100:+.1f}%)",
              f"- median: {result['length']['baseline']['median']} → {result['length']['coverage_aware']['median']}; "
              f"p90: {result['length']['baseline']['p90']} → {result['length']['coverage_aware']['p90']}",
              f"- output tokens: {result['length']['baseline']['output_tokens_total']} → "
              f"{result['length']['coverage_aware']['output_tokens_total']}; "
              f"facts per extra 100 tokens: {result['length']['facts_gained_per_extra_100_tokens']}",
              "", "## Enumeration Diagnostic (secondary / post-hoc)",
              f"- {result['enumeration_diagnostic']}",
              "", "## Verdict", f"### {v['utilization_verdict']}", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    result = evaluate()
    print(json.dumps({"cohort": result["cohort"]["evidence_complete_cases"],
                      "gap_cases": result["cohort"]["gap_ids"],
                      "rescued": result["rescued_cases"],
                      "regressed_controls": result["control_regressions"],
                      "verdict": result["verdict"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
