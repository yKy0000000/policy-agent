"""Controlled end-to-end transfer study: MiniLM-Top5 vs BGE-Top5 answers.

Fixed: 50 Validation V1 queries, frozen facts/mappings, lexical+semantic
retrieval, candidate union, chunking, generator, generation prompt, temperature,
citation validation, judge model, judge rubric, answer-eval schema.
Variable: the pointwise reranker only (MiniLM vs BGE), each feeding Fixed Top5.

Validation V1 has already been inspected; this is development/diagnostic data,
not an untouched validation. Generation/judge use the existing cache and the
external LLM API; production defaults and frozen artifacts are never modified.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, median
from types import SimpleNamespace

from eval.compare_rerankers import (BASELINE_MODEL, DEFAULT_CHALLENGER, _make_scorer,
                                    load_unions, rank_union)
from eval.metrics import score_facts
from eval.run_answer_eval import (_RecordingGenerationClient, _V3Cache, _judge_messages,
                                  _parse_judge, _score_v3_answer, _sha256, _stable_hash,
                                  V3_GENERATION_MAX_TOKENS, V3_JUDGE_MAX_TOKENS)
from eval.run_validation import VERSION as VALIDATION_VERSION
from eval.run_validation import _evidence_hash, _quality_summary
from src.generator import (GENERATION_PROMPT_VERSION, assign_evidence_sources,
                           build_grounded_messages, generate_grounded_answer, validate_citations)

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "eval/validation/validation_v1_metadata.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
INDEX = ROOT / "cache/policy_index.json"
GEOMETRY = ROOT / "eval/results/evidence_geometry_analysis.json"
CACHE = ROOT / "cache/validation_v1_llm_cache.json"
RESULTS = ROOT / "eval/results/reranker_transfer_results.json"
SUMMARY = ROOT / "eval/results/reranker_transfer_summary.md"
HISTORICAL = ROOT / "eval/validation/results/validation_v1_results.json"

ARMS = ("minilm_top5", "bge_top5")
ARM_MODEL = {"minilm_top5": BASELINE_MODEL, "bge_top5": DEFAULT_CHALLENGER}
JUDGE_VERSION = "reranker-transfer-v1-answer-quality-v1"
SENTINEL_CASES = ("VAL-001-027", "VAL-001-030", "VAL-001-001", "VAL-001-006", "VAL-001-033")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Evidence preparation (model touch: rerank the frozen union once per arm)
# --------------------------------------------------------------------------- #

def prepare_evidence(queries: dict, rubric: dict, chunk_meta: dict, support: dict,
                     *, refresh: bool = False) -> dict:
    if RESULTS.exists() and not refresh:
        saved = _json(RESULTS).get("preparation")
        if saved and saved.get("complete") and saved.get("arms") and saved.get("union_hash"):
            return saved
    from eval.compare_rerankers import _cache_folder  # local import keeps module light
    unions = load_unions(queries, chunk_meta)
    union_hash = _stable_hash({cid: sorted(ids) for cid, ids in sorted(unions.items())})
    scorers = {arm: _make_scorer(ARM_MODEL[arm], cache_folder=_cache_folder()) for arm in ARMS}
    facts_by_case = {case["case_id"]: [{"fact_id": fact["fact_id"],
                                        "direct_chunk_ids": support[fact["fact_id"]]}
                                       for fact in case["facts"]]
                     for case in rubric["cases"]}
    preparation = {"union_hash": union_hash, "arms": {arm: {} for arm in ARMS},
                   "models": {"minilm_top5": BASELINE_MODEL, "bge_top5": DEFAULT_CHALLENGER},
                   "k": 5, "complete": False}
    for case in queries["cases"]:
        case_id = case["case_id"]
        for arm in ARMS:
            order = rank_union(scorers[arm], case["query"], unions[case_id], chunk_meta)
            top = [{**chunk_meta[cid], "token_count": _approx(chunk_meta[cid]["text"])}
                   for cid in order[:5]]
            scored = score_facts(facts_by_case[case_id], top)
            preparation["arms"][arm][case_id] = {
                "chunks": top, "evidence_hash": _evidence_hash(top),
                "available_fact_ids": scored["covered_fact_ids"]}
        _write(RESULTS, {"schema_version": 1, "version": "reranker-transfer-v1",
                         "status": "preparing", "preparation": preparation})
        print(f"Prepared {case_id}", flush=True)
    preparation["complete"] = True
    return preparation


# --------------------------------------------------------------------------- #
# Generation (exact input-keyed cache; reuses historical validation cache)
# --------------------------------------------------------------------------- #

def _generation_identity(case_id: str, chunks: list[dict], model: str) -> dict:
    sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
    messages = build_grounded_messages(_CASE_QUERY[case_id], [], sources)
    prompt_hash = _stable_hash({"messages": messages, "temperature": 0.0,
                                "max_tokens": V3_GENERATION_MAX_TOKENS,
                                "prompt_version": GENERATION_PROMPT_VERSION})
    evidence_hash = _evidence_hash(chunks)
    key = _stable_hash({"validation_version": VALIDATION_VERSION, "case_id": case_id,
                        "evidence_hash": evidence_hash, "prompt_config_hash": prompt_hash,
                        "generator_model": model})
    return {"key": key, "prompt_hash": prompt_hash, "evidence_hash": evidence_hash,
            "sources": sources, "order": [chunk["chunk_id"] for chunk in chunks]}


_CASE_QUERY: dict[str, str] = {}


def generate_arm(case_id: str, chunks: list[dict], model: str, cache: _V3Cache,
                 client, failures: list) -> dict | None:
    identity = _generation_identity(case_id, chunks, model)
    cached = cache.get(identity["key"])
    if cached is None:
        try:
            recorder = _RecordingGenerationClient(client)
            produced = generate_grounded_answer(_CASE_QUERY[case_id], [],
                [SimpleNamespace(**chunk) for chunk in chunks], recorder, model=model,
                cache=None, max_tokens=V3_GENERATION_MAX_TOKENS)
            cached = {"kind": "generation", "answer": produced["answer"],
                      "generation_hash": _stable_hash(produced["answer"]),
                      "evidence_hash": identity["evidence_hash"],
                      "prompt_config_hash": identity["prompt_hash"], "model": model,
                      "provider_usage": recorder.usage}
            cache.set(identity["key"], cached)
        except Exception as error:  # technical failure; never an answer-quality failure
            failures.append({"kind": "generation", "case_id": case_id, "model": model,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    citation = validate_citations(cached["answer"], identity["sources"])
    return {"answer": cached["answer"], "generation_key": identity["key"],
            "generation_hash": cached["generation_hash"], "evidence_hash": identity["evidence_hash"],
            "prompt_config_hash": identity["prompt_hash"], "provider_usage": cached["provider_usage"],
            "citation_ids": citation["citation_ids"], "citation_validation": citation["validation"],
            "cited_sources": citation["sources"], "sources": identity["sources"]}


# --------------------------------------------------------------------------- #
# Blind grouped judge
# --------------------------------------------------------------------------- #

def blind_order(case_id: str) -> dict[str, str]:
    first = "minilm_top5" if int(_stable_hash({"case_id": case_id})[:8], 16) % 2 == 0 else "bge_top5"
    second = "bge_top5" if first == "minilm_top5" else "minilm_top5"
    return {"A": first, "B": second}


def judge_case(case: dict, variants: dict, cache: _V3Cache, client, model: str,
               failures: list) -> dict | None:
    mapping = blind_order(case["case_id"])
    labeled = {label: {"generation": {"answer": variants[arm]["answer"]},
                       "sources": variants[arm]["sources"]}
               for label, arm in mapping.items()}
    payload = {"query": case["query"],
               "facts": [{"fact_id": fact["fact_id"], "fact": _FACT_STATEMENT[fact["fact_id"]]}
                         for fact in _CASE_FACTS[case["case_id"]]]}
    messages = _judge_messages(payload, labeled)
    answer_hashes = {label: variants[arm]["generation_hash"] for label, arm in mapping.items()}
    evidence_hashes = {label: variants[arm]["evidence_hash"] for label, arm in mapping.items()}
    key = _stable_hash({"validation_version": JUDGE_VERSION,
                        "rubric_sha256": _sha256(RUBRIC), "case_id": case["case_id"],
                        "judge_model": model,
                        "judge_prompt_config_hash": _stable_hash(
                            {"messages": messages, "temperature": 0.0,
                             "max_tokens": V3_JUDGE_MAX_TOKENS, "version": JUDGE_VERSION}),
                        "answer_hashes": answer_hashes, "evidence_hashes": evidence_hashes})
    cached = cache.get(key)
    if cached is None:
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS,
                                                    temperature=0.0)
            parsed = _parse_judge(raw, set(labeled), {f["fact_id"] for f in _CASE_FACTS[case["case_id"]]})
            cached = {"kind": "judge", "answers": parsed, "raw_hash": _stable_hash(raw),
                      "provider_usage": usage}
            cache.set(key, cached)
        except Exception as error:
            failures.append({"kind": "judge", "case_id": case["case_id"],
                             "error": f"{type(error).__name__}: {error}"})
            return None
    return {mapping[label]: cached["answers"][label] for label in labeled}


# --------------------------------------------------------------------------- #
# Scoring and aggregation
# --------------------------------------------------------------------------- #

_CASE_FACTS: dict[str, list[dict]] = {}
_FACT_STATEMENT: dict[str, str] = {}


def score_arm(case_id: str, arm: str, variant: dict, judged: dict) -> dict:
    facts = [{"fact_id": fact["fact_id"], "direct_chunk_ids": fact["direct_chunk_ids"]}
             for fact in _CASE_FACTS[case_id]]
    chunks = variant["chunks"]
    scored = score_facts(facts, chunks)
    case = {"case_id": case_id, "facts": [{"fact_id": fact["fact_id"]} for fact in facts],
            "evidence": {"candidate_pool": {"covered_fact_ids": _CANDIDATE_FACTS[case_id]}},
            "variants": {arm: {"chunks": chunks,
                               "generation": {"answer": variant["answer"],
                                              "citation_validation": variant["citation_validation"]},
                               "available_fact_ids": scored["covered_fact_ids"],
                               "evidence_tokens": sum(_approx(chunk["text"]) for chunk in chunks)}}}
    return _score_v3_answer(case, arm, judged)


def _approx(text: str) -> int:
    from eval.analyze_evidence_geometry import approx_tokens
    return approx_tokens(text)


_CANDIDATE_FACTS: dict[str, list[str]] = {}


def evaluate(*, refresh_evidence: bool = False) -> dict:
    global _CASE_QUERY
    metadata = _json(METADATA)
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    index = _json(INDEX)
    from eval.run_validation import direct_support_map
    support = direct_support_map(rubric, index["chunks"])
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in index["chunks"]}
    _CASE_QUERY = {case["case_id"]: case["query"] for case in queries["cases"]}
    for case in rubric["cases"]:
        _CASE_FACTS[case["case_id"]] = [{"fact_id": fact["fact_id"],
                                         "direct_chunk_ids": support[fact["fact_id"]]}
                                        for fact in case["facts"]]
        for fact in case["facts"]:
            _FACT_STATEMENT[fact["fact_id"]] = fact["statement"]

    preparation = prepare_evidence(queries, rubric, chunk_meta, support, refresh=refresh_evidence)
    _write(RESULTS, {"schema_version": 1, "version": "reranker-transfer-v1",
                     "status": "prepared", "preparation": preparation})
    for case in queries["cases"]:
        case_id = case["case_id"]
        union = set(_json(GEOMETRY)["retrieval_cache"]["scopes"][case_id]["union"]) \
            if GEOMETRY.exists() else set()
        union_chunks = [{**chunk_meta[c], "token_count": _approx(chunk_meta[c]["text"])}
                        for c in sorted(union) if c in chunk_meta]
        _CANDIDATE_FACTS[case_id] = score_facts(_CASE_FACTS[case_id],
                                                union_chunks)["covered_fact_ids"]

    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    config = LLMConfig.from_env(ROOT / ".env")
    client = OpenAIChatCompletionsClient(config)
    cache = _V3Cache(CACHE)
    failures: list = []
    case_rows = []
    for case in queries["cases"]:
        case_id = case["case_id"]
        variants = {}
        for arm in ARMS:
            chunks = preparation["arms"][arm][case_id]["chunks"]
            generated = generate_arm(case_id, chunks, config.model, cache, client, failures)
            if generated is None:
                variants = {}
                break
            generated["chunks"] = chunks
            variants[arm] = generated
        if not variants:
            case_rows.append({"case_id": case_id, "status": "technical_failure"})
            continue
        judged = judge_case(case, variants, cache, client, config.model, failures)
        if judged is None:
            case_rows.append({"case_id": case_id, "status": "judge_failure"})
            continue
        row = {"case_id": case_id, "status": "complete",
               "blind_order": blind_order(case_id), "arms": {}}
        for arm in ARMS:
            scored = score_arm(case_id, arm, variants[arm], judged[arm])
            row["arms"][arm] = {"answer": variants[arm]["answer"],
                                "generation_key": variants[arm]["generation_key"],
                                "evidence_hash": variants[arm]["evidence_hash"],
                                "provider_usage": variants[arm]["provider_usage"],
                                "selected_chunk_ids": [c["chunk_id"] for c in variants[arm]["chunks"]],
                                **scored}
        case_rows.append(row)
        print(f"Completed {case_id}", flush=True)

    result = _finalize(case_rows, preparation, failures, config.model, metadata)
    _write(RESULTS, result)
    _write(SUMMARY, _render(result))
    return result


def transition_bucket(minilm_complete: bool, bge_complete: bool) -> str:
    if minilm_complete and bge_complete:
        return "both_right"
    if minilm_complete:
        return "right_to_wrong"
    if bge_complete:
        return "wrong_to_right"
    return "both_wrong"


def paired_transitions(rows: list[dict]) -> dict:
    buckets = {"wrong_to_right": [], "right_to_wrong": [], "both_right": [], "both_wrong": []}
    for row in rows:
        if row["status"] != "complete":
            continue
        key = transition_bucket(row["arms"]["minilm_top5"]["quality"]["grounded_fact_complete"],
                                row["arms"]["bge_top5"]["quality"]["grounded_fact_complete"])
        buckets[key].append(row["case_id"])
    return buckets


def transfer_accounting(pairs: list[dict]) -> dict:
    newly_available = lost_evidence = grounded_gained = grounded_lost = 0
    cases = []
    for pair in pairs:
        gained_ev = set(pair["bge_available"]) - set(pair["minilm_available"])
        lost_ev = set(pair["minilm_available"]) - set(pair["bge_available"])
        gained_g = set(pair["bge_grounded"]) - set(pair["minilm_grounded"])
        lost_g = set(pair["minilm_grounded"]) - set(pair["bge_grounded"])
        newly_available += len(gained_ev)
        lost_evidence += len(lost_ev)
        grounded_gained += len(gained_g)
        grounded_lost += len(lost_g)
        if gained_ev or lost_ev:
            cases.append({"case_id": pair["case_id"], "evidence_gained": sorted(gained_ev),
                          "evidence_lost": sorted(lost_ev), "grounded_gained": sorted(gained_g),
                          "grounded_lost": sorted(lost_g)})
    return {"newly_available_required_facts": newly_available,
            "lost_evidence_facts": lost_evidence,
            "grounded_facts_gained": grounded_gained, "grounded_facts_lost": grounded_lost,
            "positive_transfer_rate": grounded_gained / newly_available if newly_available else None,
            "negative_transfer_rate": grounded_lost / lost_evidence if lost_evidence else None,
            "cases": cases}


def _finalize(rows: list[dict], preparation: dict, failures: list, model: str,
              metadata: dict) -> dict:
    complete = [row for row in rows if row["status"] == "complete"]
    total_facts = sum(len(_CASE_FACTS[row["case_id"]]) for row in complete)
    summaries = {}
    for arm in ARMS:
        items = [{"quality": row["arms"][arm]["quality"],
                  "evidence_tokens": row["arms"][arm]["evidence_tokens"],
                  "pipeline_diagnosis": row["arms"][arm]["pipeline_diagnosis"],
                  "claim_diagnosis": row["arms"][arm]["claim_diagnosis"]}
                 for row in complete]
        summaries[arm] = _quality_summary(items, total_facts)

    transitions = paired_transitions(rows)
    pairs = [{"case_id": row["case_id"],
              "minilm_available": row["arms"]["minilm_top5"]["available_fact_ids"],
              "bge_available": row["arms"]["bge_top5"]["available_fact_ids"],
              "minilm_grounded": row["arms"]["minilm_top5"]["quality"]["grounded_covered_fact_ids"],
              "bge_grounded": row["arms"]["bge_top5"]["quality"]["grounded_covered_fact_ids"]}
             for row in complete]
    transfer = transfer_accounting(pairs)

    def sentinel(case_id: str) -> dict:
        row = next((r for r in complete if r["case_id"] == case_id), None)
        if row is None:
            return {"case_id": case_id, "status": "unavailable"}
        return {"case_id": case_id, "blind_order": row["blind_order"],
                "minilm": {"evidence_facts": sorted(row["arms"]["minilm_top5"]["available_fact_ids"]),
                           "grounded_covered": row["arms"]["minilm_top5"]["quality"]["grounded_covered_count"],
                           "complete": row["arms"]["minilm_top5"]["quality"]["grounded_fact_complete"]},
                "bge": {"evidence_facts": sorted(row["arms"]["bge_top5"]["available_fact_ids"]),
                        "grounded_covered": row["arms"]["bge_top5"]["quality"]["grounded_covered_count"],
                        "complete": row["arms"]["bge_top5"]["quality"]["grounded_fact_complete"]}}

    gap_ids = _utilization_gap_ids()
    cohort = []
    for case_id in gap_ids:
        row = next((r for r in complete if r["case_id"] == case_id), None)
        if row is None:
            cohort.append({"case_id": case_id, "status": "unavailable"})
            continue
        cohort.append({"case_id": case_id,
                       "minilm_complete": row["arms"]["minilm_top5"]["quality"]["grounded_fact_complete"],
                       "bge_complete": row["arms"]["bge_top5"]["quality"]["grounded_fact_complete"],
                       "minilm_grounded": row["arms"]["minilm_top5"]["quality"]["grounded_covered_count"],
                       "bge_grounded": row["arms"]["bge_top5"]["quality"]["grounded_covered_count"]})

    length = {}
    for arm in ARMS:
        words = [len(row["arms"][arm]["answer"].split()) for row in complete]
        out_tokens = [row["arms"][arm]["provider_usage"].get("output_tokens") or 0 for row in complete]
        length[arm] = {"answer_words_mean": mean(words) if words else None,
                       "answer_words_median": median(words) if words else None,
                       "output_tokens_total": sum(out_tokens),
                       "evidence_tokens_total": summaries[arm]["evidence_tokens"]}

    verdict = _verdict(summaries, transitions)

    return {"schema_version": 1, "version": "reranker-transfer-v1", "status": "complete",
            "scope_note": ("Validation V1 has already been inspected and is used here as "
                           "development/diagnostic data, not an untouched validation."),
            "model": model, "k": 5, "arms": {"minilm_top5": BASELINE_MODEL,
                                             "bge_top5": DEFAULT_CHALLENGER},
            "preparation": preparation,
            "case_count": len(rows), "complete_cases": len(complete), "total_facts": total_facts,
            "summaries": summaries, "paired_transitions": transitions, "transfer": transfer,
            "sentinel_cases": {case_id: sentinel(case_id) for case_id in SENTINEL_CASES},
            "utilization_gap_cohort": cohort, "length": length,
            "failures": failures, "verdict": verdict,
            "historical_reference": _historical_reference(),
            "cases": rows}


def _utilization_gap_ids() -> list[str]:
    results = _json(HISTORICAL)
    return sorted(row["case_id"] for row in results["cases"]
                  if row["always_v1_evidence"]["fact_complete"]
                  and not row["always_v1"]["quality"]["grounded_fact_complete"])


def _historical_reference() -> dict:
    results = _json(HISTORICAL)
    strategies = results["strategies"]
    return {"always_v1_grounded_micro": strategies["always_v1"]["grounded_micro"],
            "frozen_adaptive_grounded_micro": strategies["frozen_adaptive"]["grounded_micro"],
            "validation_v1_verdict": results["verdict"],
            "note": "Different evidence policies; context only, not a causal A/B."}


def _verdict(summaries: dict, transitions: dict) -> dict:
    mini = summaries["minilm_top5"]["grounded_micro"]
    bge = summaries["bge_top5"]["grounded_micro"]
    complete_delta = (summaries["bge_top5"]["grounded_complete_cases"] -
                      summaries["minilm_top5"]["grounded_complete_cases"])
    wrong_to_right = len(transitions["wrong_to_right"])
    right_to_wrong = len(transitions["right_to_wrong"])
    bad_claims_delta = ((summaries["bge_top5"]["claim_counts"].get("unsupported", 0) +
                         summaries["bge_top5"]["claim_counts"].get("contradicted", 0)) -
                        (summaries["minilm_top5"]["claim_counts"].get("unsupported", 0) +
                         summaries["minilm_top5"]["claim_counts"].get("contradicted", 0)))
    if bge < mini - 1e-9 or complete_delta < 0 or right_to_wrong > wrong_to_right:
        gate = "REGRESSION"
    elif (bge - mini) <= 0 and complete_delta <= 0:
        gate = "WASH"
    elif complete_delta >= 2 and wrong_to_right > right_to_wrong and bad_claims_delta <= 0:
        gate = "CLEAR END-TO-END WIN"
    else:
        gate = "SMALL / MIXED WIN"
    return {"transfer_verdict": gate, "grounded_micro_delta": bge - mini,
            "grounded_complete_delta": complete_delta, "wrong_to_right": wrong_to_right,
            "right_to_wrong": right_to_wrong, "bad_claims_delta": bad_claims_delta}


def _metric(value) -> str:
    return "—" if value is None else (f"{value:.3f}" if isinstance(value, float) else str(value))


def _render(result: dict) -> str:
    mini, bge = result["summaries"]["minilm_top5"], result["summaries"]["bge_top5"]
    verdict = result["verdict"]
    lines = ["# Reranker → Answer Transfer (MiniLM-Top5 vs BGE-Top5)", "",
             "> " + result["scope_note"], "",
             "## Overall Answer Quality", "| Metric | MiniLM Top5 | BGE Top5 | Delta |",
             "|---|---:|---:|---:|"]
    for label, key, scale in (("Answer Macro", "answer_macro", 1), ("Answer Micro", "answer_micro", 1),
                              ("Answer Complete", "fact_complete_cases", 1),
                              ("Grounded Macro", "grounded_macro", 1),
                              ("Grounded Micro", "grounded_micro", 1),
                              ("Grounded Complete", "grounded_complete_cases", 1)):
        lines.append(f"| {label} | {_metric(mini[key])} | {_metric(bge[key])} | "
                     f"{_metric((bge[key] - mini[key]) if isinstance(mini[key], float) else bge[key] - mini[key])} |")
    for label, key in (("Unsupported", "unsupported"), ("Contradicted", "contradicted")):
        lines.append(f"| {label} | {mini['claim_counts'].get(key, 0)} | "
                     f"{bge['claim_counts'].get(key, 0)} | "
                     f"{bge['claim_counts'].get(key, 0) - mini['claim_counts'].get(key, 0)} |")
    for label, key in (("Citation unsupported", "unsupported"), ("Citation missing", "missing")):
        lines.append(f"| {label} | {mini['citation_counts'].get(key, 0)} | "
                     f"{bge['citation_counts'].get(key, 0)} | "
                     f"{bge['citation_counts'].get(key, 0) - mini['citation_counts'].get(key, 0)} |")
    t = result["paired_transitions"]
    lines += ["", "## Paired Transitions (grounded fact-complete)",
              f"- wrong→right {len(t['wrong_to_right'])}: {t['wrong_to_right']}",
              f"- right→wrong {len(t['right_to_wrong'])}: {t['right_to_wrong']}",
              f"- both right {len(t['both_right'])}; both wrong {len(t['both_wrong'])}",
              f"- net complete gain: {verdict['grounded_complete_delta']}",
              "", "## Fact-level Transfer",
              f"- newly available evidence facts: {result['transfer']['newly_available_required_facts']}",
              f"- lost evidence facts: {result['transfer']['lost_evidence_facts']}",
              f"- grounded facts gained: {result['transfer']['grounded_facts_gained']}; "
              f"lost: {result['transfer']['grounded_facts_lost']}",
              f"- positive transfer rate: {_metric(result['transfer']['positive_transfer_rate'])}; "
              f"negative transfer rate: {_metric(result['transfer']['negative_transfer_rate'])}",
              "", "## Sentinel Cases"]
    for case_id, data in result["sentinel_cases"].items():
        if data.get("status") == "unavailable":
            lines.append(f"- {case_id}: unavailable")
            continue
        lines.append(f"- {case_id}: mini complete={data['minilm']['complete']} "
                     f"(grounded {data['minilm']['grounded_covered']}), "
                     f"bge complete={data['bge']['complete']} (grounded {data['bge']['grounded_covered']})")
    lines += ["", "## Utilization-Gap Cohort"]
    for item in result["utilization_gap_cohort"]:
        if item.get("status") == "unavailable":
            lines.append(f"- {item['case_id']}: unavailable")
        else:
            lines.append(f"- {item['case_id']}: mini grounded {item['minilm_grounded']} "
                         f"(complete {item['minilm_complete']}) -> bge grounded {item['bge_grounded']} "
                         f"(complete {item['bge_complete']})")
    length = result["length"]
    lines += ["", "## Length / Cost",
              f"- answer words mean/median: MiniLM {_metric(length['minilm_top5']['answer_words_mean'])}/"
              f"{length['minilm_top5']['answer_words_median']}, "
              f"BGE {_metric(length['bge_top5']['answer_words_mean'])}/"
              f"{length['bge_top5']['answer_words_median']}",
              f"- output tokens total: MiniLM {length['minilm_top5']['output_tokens_total']}, "
              f"BGE {length['bge_top5']['output_tokens_total']}",
              f"- evidence tokens total: MiniLM {length['minilm_top5']['evidence_tokens_total']}, "
              f"BGE {length['bge_top5']['evidence_tokens_total']}",
              "", "## Transfer Verdict", f"### {verdict['transfer_verdict']}",
              f"- grounded micro delta {verdict['grounded_micro_delta']:.4f}; "
              f"complete delta {verdict['grounded_complete_delta']}; "
              f"wrong→right {verdict['wrong_to_right']}; right→wrong {verdict['right_to_wrong']}",
              "", "## Historical Reference (context only)",
              f"- Always V1 grounded micro {result['historical_reference']['always_v1_grounded_micro']:.3f}; "
              f"Frozen Adaptive {result['historical_reference']['frozen_adaptive_grounded_micro']:.3f}; "
              f"Validation V1 {result['historical_reference']['validation_v1_verdict']}.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-evidence", action="store_true")
    args = parser.parse_args(argv)
    result = evaluate(refresh_evidence=args.refresh_evidence)
    print(json.dumps({"complete_cases": result["complete_cases"],
                      "verdict": result["verdict"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

