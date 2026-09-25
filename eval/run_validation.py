"""Frozen Broad Query Validation V1; preparation and reporting are fully offline."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

from eval.metrics import score_facts
from eval.run_answer_eval import (
    V3_GENERATION_MAX_TOKENS, V3_JUDGE_MAX_TOKENS, V3_JUDGE_SYSTEM,
    _RecordingGenerationClient, _V3Cache, _judge_messages, _parse_judge,
    _score_v3_answer, _sha256, _stable_hash, _write_atomic,
)
from src.evidence_budget import select_evidence_prefix
from src.generator import (
    GENERATION_PROMPT_VERSION, assign_evidence_sources, build_grounded_messages,
    generate_grounded_answer, validate_citations,
)


ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "eval/validation/validation_v1_metadata.json"
PREPARED = ROOT / "cache/validation_v1_prepare.json"
CACHE = ROOT / "cache/validation_v1_llm_cache.json"
RESULTS = ROOT / "eval/validation/results/validation_v1_results.json"
SUMMARY = ROOT / "eval/validation/results/validation_v1_summary.md"
REVIEW = ROOT / "eval/validation/results/validation_v1_human_review.md"
VERSION = "validation-v1"
JUDGE_VERSION = "validation-v1-answer-quality-v1"
STRATEGIES = ("always_v1", "frozen_adaptive")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, value: dict) -> None:
    _write_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _frozen_inputs() -> tuple[dict, dict, dict, dict]:
    metadata = _json(META)
    dataset = metadata["dataset"]
    strategy = metadata["frozen_strategy"]
    for path, expected in (
        (ROOT / dataset["queries_path"], dataset["queries_sha256"]),
        (ROOT / dataset["rubric_path"], dataset["rubric_sha256"]),
        (ROOT / strategy["config_path"], strategy["config_sha256"]),
    ):
        if _sha256(path) != expected:
            raise ValueError(f"frozen input hash mismatch: {path}")
    config = _json(ROOT / strategy["config_path"])
    if (config["fixed_stop_min_top5_score"] != strategy["fixed_stop_min_top5_score"] or
            config["if_stop"] != "fixed_top5" or
            config["otherwise"] != "adaptive_prefix_v1" or
            config["second_stage_v2_rule"] is not None):
        raise ValueError("frozen strategy differs from metadata")
    queries = _json(ROOT / dataset["queries_path"])
    rubric = _json(ROOT / dataset["rubric_path"])
    if len(queries["cases"]) != 50 or sum(len(c["facts"]) for c in rubric["cases"]) != 239:
        raise ValueError("frozen validation case/fact count changed")
    return metadata, config, queries, rubric


def _runtime_fingerprints() -> dict[str, str]:
    semantic = _json(ROOT / "cache/semantic_index.json")
    paths = [ROOT / "cache/policy_index.json", ROOT / "cache/semantic_index.json",
             ROOT / "cache" / semantic["vectors_file"],
             ROOT / "src/evidence_budget.py", ROOT / "src/reranked_retriever.py",
             ROOT / "src/reranker.py", ROOT / "src/semantic_embeddings.py"]
    return {str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path) for path in paths}


def _fingerprint_changes(saved: dict[str, str], current: dict[str, str]) -> list[str]:
    return sorted(key for key in saved.keys() | current.keys()
                  if saved.get(key) != current.get(key))


def adaptive_decision(scores: list[float], threshold: float) -> str:
    if len(scores) < 5:
        raise ValueError("Top5 scores unavailable")
    return "fixed_top5" if min(scores[:5]) >= threshold else "adaptive_prefix_v1"


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def direct_support_map(rubric: dict, index_chunks: list[dict]) -> dict[str, list[str]]:
    """Map frozen verbatim source spans to indexed chunks without changing the rubric."""
    by_path: dict[str, list[dict]] = defaultdict(list)
    for chunk in index_chunks:
        by_path[chunk["source_path"].removeprefix("Policies/")].append(chunk)
    mapping = {}
    for case in rubric["cases"]:
        for fact in case["facts"]:
            matches = set()
            for support in fact["support"]:
                excerpt = _normalized(support["source_excerpt"])
                context = _normalized(support.get("context_excerpt", ""))
                matches.update(chunk["chunk_id"] for chunk in by_path[support["document"]]
                               if excerpt in _normalized(chunk["text"]) and
                               (not context or context in _normalized(chunk["text"])))
            if not matches:
                raise ValueError(f"validation_rubric_issue: no indexed direct source for {fact['fact_id']}")
            mapping[fact["fact_id"]] = sorted(matches)
    return mapping


def _local_retriever():
    from src.indexing import load_index
    from src.reranker import CrossEncoderReranker
    from src.reranked_retriever import RerankedPolicyRetriever
    from src.retriever import PolicyRetriever
    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.semantic_indexing import load_semantic_index
    from src.semantic_retriever import SemanticPolicyRetriever

    index = load_index(ROOT / "cache/policy_index.json")
    semantic_index = load_semantic_index(ROOT / "cache/semantic_index.json")
    folder = ROOT / "cache/huggingface"
    encoder = SentenceTransformerEncoder(semantic_index.model_name, cache_folder=folder,
                                         device="cpu", local_files_only=True)
    reranker = CrossEncoderReranker(cache_folder=folder, device="cpu", local_files_only=True)
    retriever = RerankedPolicyRetriever(PolicyRetriever(index),
        SemanticPolicyRetriever(semantic_index, encoder), reranker)
    return retriever, index


def _evidence_hash(chunks: list[dict]) -> str:
    return _stable_hash([{"chunk_id": c["chunk_id"], "text": c["text"],
                          "title": c["title"], "heading_path": c["heading_path"],
                          "source_path": c["source_path"]} for c in chunks])


def _score_evidence(facts: list[dict], chunks: list[dict], tokens: int) -> dict:
    result = score_facts(facts, chunks)
    result.update(selected_k=len(chunks), evidence_tokens=tokens,
                  grounded_available_fact_count=result["covered_count"],
                  selected_chunk_ids=[c["chunk_id"] for c in chunks],
                  evidence_hash=_evidence_hash(chunks))
    return result


def _evidence_summary(items: list[dict], total_facts: int) -> dict:
    return {"macro_fact_coverage": mean(item["coverage"] for item in items),
            "micro_fact_coverage": sum(item["covered_count"] for item in items) / total_facts,
            "covered_facts": sum(item["covered_count"] for item in items),
            "grounded_available_facts": sum(item["covered_count"] for item in items),
            "fact_complete_cases": sum(item["fact_complete"] for item in items),
            "evidence_tokens": sum(item.get("evidence_tokens", 0) for item in items)}


def _trigger_breakdown(rows: list[dict], field: str) -> dict[str, dict]:
    values = defaultdict(lambda: {"total": 0, "fixed": 0, "v1": 0})
    for row in rows:
        item = values[row[field]]
        item["total"] += 1
        item["fixed" if row["adaptive_decision"] == "fixed_top5" else "v1"] += 1
    return {key: value | {"fixed_rate": value["fixed"] / value["total"]}
            for key, value in sorted(values.items())}


def _material_prepared_identity(row: dict) -> dict:
    """Fields that determine routing, evidence, and downstream model inputs."""
    return {"case_id": row["case_id"], "query": row["query"],
            "fact_ids": [fact["fact_id"] for fact in row["facts"]],
            "candidate_count": row["candidate_count"],
            "top5_scores": row["top5_scores"],
            "minimum_top5_score": row["minimum_top5_score"],
            "adaptive_decision": row["adaptive_decision"],
            "selector_trace": row["selector_trace"],
            "variants": {route: {"chunks": [{key: value for key, value in chunk.items()
                                               if key != "token_count"}
                                              for chunk in variant["chunks"]],
                                 "evidence_tokens": variant["evidence"]["evidence_tokens"],
                                 "evidence_hash": variant["evidence"]["evidence_hash"]}
                         for route, variant in row["variants"].items()}}


def _material_public_identity(row: dict) -> dict:
    return {"case_id": row["case_id"], "query": row["query"],
            "candidate_count": row["candidate_count"],
            "top5_scores": row["top5_scores"],
            "minimum_top5_score": row["minimum_top5_score"],
            "adaptive_decision": row["adaptive_decision"],
            "selector_trace": row["selector_trace"],
            "always_v1": {key: row["always_v1_evidence"][key]
                          for key in ("selected_chunk_ids", "selected_k",
                                      "evidence_tokens", "evidence_hash")},
            "frozen_adaptive": {key: row["frozen_adaptive_evidence"][key]
                                for key in ("selected_chunk_ids", "selected_k",
                                            "evidence_tokens", "evidence_hash")}}


def prepare() -> dict:
    metadata, config, queries, rubric = _frozen_inputs()
    fact_by_id = {item["case_id"]: item["facts"] for item in rubric["cases"]}
    previous = _json(PREPARED) if PREPARED.exists() else None
    previous_result = _json(RESULTS) if RESULTS.exists() else None
    frozen_hash = _stable_hash({"metadata": metadata, "queries": queries, "rubric": rubric,
                                "strategy": config})
    if previous and previous.get("frozen_hash") != frozen_hash:
        raise ValueError("prepared cache belongs to different frozen inputs")
    fingerprints = _runtime_fingerprints()
    saved_fingerprints = previous.get("runtime_fingerprints") if previous else None
    if saved_fingerprints:
        changes = _fingerprint_changes(saved_fingerprints, fingerprints)
        if changes:
            raise ValueError("retrieval index or selector changed after preparation: " +
                             ", ".join(changes))
    # An earlier runner failed to persist these fingerprints when all 50 cases
    # were already complete. Recompute and compare each row before attesting it.
    legacy_hashes = (dict(previous.get("legacy_identity_hashes", {}))
                     if previous and saved_fingerprints else
                     {row["case_id"]: _stable_hash(_material_prepared_identity(row))
                      for row in previous["cases"]}
                     if previous else {})
    prepared = (previous if saved_fingerprints else
                {"schema_version": 1, "version": VERSION,
                 "frozen_hash": frozen_hash, "cases": []})
    prepared["runtime_fingerprints"] = fingerprints
    if legacy_hashes:
        prepared["legacy_identity_hashes"] = legacy_hashes
    done = {row["case_id"] for row in prepared["cases"]}
    retriever = None
    support = None
    for position, case in enumerate(queries["cases"], 1):
        if case["case_id"] in done:
            continue
        if retriever is None:
            retriever, index = _local_retriever()
            support = direct_support_map(rubric, [c.to_dict() for c in index.chunks])
        ranked = retriever.search(case["query"], top_k=20)
        if len(ranked) < 5:
            raise ValueError(f"fewer than five reranked chunks: {case['case_id']}")
        candidate_count = retriever.timings[-1].candidate_count
        candidate_ids = {candidate.result.chunk_id for candidate in retriever.candidates(case["query"])}
        facts = [{"fact_id": f["fact_id"], "direct_chunk_ids": support[f["fact_id"]]}
                 for f in fact_by_id[case["case_id"]]]
        candidate = score_facts(facts, [{"chunk_id": cid, "token_count": 0}
                                         for cid in sorted(candidate_ids)])
        selected = select_evidence_prefix(case["query"], ranked,
                                           token_count=retriever.count_evidence_tokens)
        fixed = ranked[:5]
        v1 = ranked[:selected.selected_k]
        fixed_chunks = [item.to_dict() | {"token_count": retriever.count_evidence_tokens(item)}
                        for item in fixed]
        v1_chunks = [item.to_dict() | {"token_count": retriever.count_evidence_tokens(item)}
                     for item in v1]
        fixed_tokens = sum(retriever.count_evidence_tokens(item) for item in fixed)
        v1_tokens = sum(retriever.count_evidence_tokens(item) for item in v1)
        route = adaptive_decision([item.reranker_score for item in ranked[:5]],
                                  config["fixed_stop_min_top5_score"])
        row = {"case_id": case["case_id"], "query": case["query"],
               "policy_family": case["policy_family"], "query_type": case["query_type"],
               "difficulty": case["difficulty"], "exception_heavy": case["exception_heavy"],
               "required_fact_count": len(facts), "facts": facts,
               "candidate_count": candidate_count, "top5_scores":
                   [item.reranker_score for item in ranked[:5]],
               "minimum_top5_score": min(item.reranker_score for item in ranked[:5]),
               "adaptive_decision": route,
               "candidate_pool": candidate,
               "selector_trace": asdict(selected),
               "variants": {
                   "fixed_top5": {"chunks": fixed_chunks,
                                  "evidence": _score_evidence(facts, fixed_chunks, fixed_tokens)},
                   "adaptive_prefix_v1": {"chunks": v1_chunks,
                                          "evidence": _score_evidence(facts, v1_chunks, v1_tokens)},
               }}
        if (case["case_id"] in legacy_hashes and
                _stable_hash(_material_prepared_identity(row)) !=
                legacy_hashes[case["case_id"]]):
            raise ValueError("legacy prepared routing or evidence differs on " +
                             case["case_id"] + "; inspect retrieval and selector before continuing")
        prepared["cases"].append(row)
        legacy_hashes.pop(case["case_id"], None)
        if legacy_hashes:
            prepared["legacy_identity_hashes"] = legacy_hashes
        else:
            prepared.pop("legacy_identity_hashes", None)
        _save(PREPARED, prepared)
        print(f"Prepared {position}/50 {case['case_id']} -> {route}", flush=True)
    # Recheck every frozen source mapping, including a resumed run.
    if retriever is None:
        from src.indexing import load_index
        index = load_index(ROOT / "cache/policy_index.json")
        support = direct_support_map(rubric, [c.to_dict() for c in index.chunks])
    if len(prepared["cases"]) != 50:
        raise ValueError("preparation incomplete")
    if legacy_hashes:
        raise ValueError("legacy prepared cases remain unverified: " + ", ".join(sorted(legacy_hashes)))
    prepared.pop("legacy_identity_hashes", None)
    _save(PREPARED, prepared)
    fixed_count = sum(r["adaptive_decision"] == "fixed_top5" for r in prepared["cases"])
    calls = sum(1 + (r["adaptive_decision"] == "fixed_top5" and
                     r["variants"]["fixed_top5"]["evidence"]["evidence_hash"] !=
                     r["variants"]["adaptive_prefix_v1"]["evidence"]["evidence_hash"])
                for r in prepared["cases"])
    result = {"schema_version": 1, "version": VERSION, "status": "prepared",
              "frozen": {"strategy_sha256": metadata["frozen_strategy"]["config_sha256"],
                         "rubric_sha256": metadata["dataset"]["rubric_sha256"],
                         "query_sha256": metadata["dataset"]["queries_sha256"],
                         "threshold": config["fixed_stop_min_top5_score"]},
              "case_count": 50, "required_fact_count": 239,
              "preparation": {"fixed_triggers": fixed_count, "v1_routes": 50-fixed_count,
                              "unique_generation_calls": calls, "judge_case_calls": 50,
                              "direct_mapped_facts": len(support),
                              "trigger_breakdown": {field: _trigger_breakdown(prepared["cases"], field)
                                                    for field in ("difficulty", "policy_family", "query_type")}},
              "evidence": {
                  "candidate_pool": _evidence_summary([r["candidate_pool"] for r in prepared["cases"]], 239),
                  "always_v1": _evidence_summary([r["variants"]["adaptive_prefix_v1"]["evidence"]
                                                   for r in prepared["cases"]], 239),
                  "frozen_adaptive": _evidence_summary([r["variants"][r["adaptive_decision"]]["evidence"]
                                                         for r in prepared["cases"]], 239)},
              "cases": [_prepared_public_row(r) for r in prepared["cases"]]}
    if (previous_result and previous_result.get("status") == "prepared" and
            previous_result.get("frozen") == result["frozen"]):
        old_rows = {r["case_id"]: r for r in previous_result["cases"]}
        for row in result["cases"]:
            if (row["case_id"] not in old_rows or
                    _material_public_identity(row) !=
                    _material_public_identity(old_rows[row["case_id"]])):
                raise ValueError("prepared routing/evidence changed on " + row["case_id"] +
                                 "; do not overwrite the frozen validation result")
    if previous_result and previous_result.get("status") == "complete":
        if previous_result.get("frozen") != result["frozen"]:
            raise ValueError("completed validation belongs to different frozen inputs")
        print(json.dumps(result["preparation"], ensure_ascii=False))
        return previous_result
    _save(RESULTS, result)
    print(json.dumps(result["preparation"], ensure_ascii=False))
    return result


def _prepared_public_row(row: dict) -> dict:
    route = row["adaptive_decision"]
    variants = row["variants"]
    return {k: row[k] for k in ("case_id", "query", "policy_family", "query_type",
                                  "difficulty", "candidate_count", "top5_scores",
                                  "minimum_top5_score", "adaptive_decision")} | {
        "candidate_pool": row["candidate_pool"], "selector_trace": row["selector_trace"],
        "always_v1_evidence": variants["adaptive_prefix_v1"]["evidence"],
        "frozen_adaptive_evidence": variants[route]["evidence"],
    }


def _load_prepared() -> tuple[dict, dict, dict]:
    metadata, config, queries, rubric = _frozen_inputs()
    if not PREPARED.exists():
        raise ValueError("run --prepare first")
    data = _json(PREPARED)
    if data["frozen_hash"] != _stable_hash({"metadata": metadata, "queries": queries,
                                             "rubric": rubric, "strategy": config}):
        raise ValueError("prepared cache is stale")
    saved_fingerprints = data.get("runtime_fingerprints")
    if not saved_fingerprints:
        raise ValueError("prepared state lacks runtime fingerprints; run --prepare to verify and rebuild it")
    changes = _fingerprint_changes(saved_fingerprints, _runtime_fingerprints())
    if changes:
        raise ValueError("retrieval index or selector changed after preparation: " +
                         ", ".join(changes))
    if len(data["cases"]) != 50:
        raise ValueError("prepared cache is incomplete")
    return data, metadata, rubric


def _llm_model() -> str:
    import os
    from src.llm_client import load_env_file
    load_env_file(ROOT / ".env")
    model = os.environ.get("LLM_MODEL", "").strip()
    if not model:
        raise ValueError("LLM_MODEL is required to identify cached generation and judge outputs")
    return model


def _generation_identity(row: dict, route: str, model: str) -> dict:
    variant = row["variants"][route]
    chunks = variant["chunks"]
    sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
    messages = build_grounded_messages(row["query"], [], sources)
    prompt_hash = _stable_hash({"messages": messages, "temperature": 0.0,
                                "max_tokens": V3_GENERATION_MAX_TOKENS,
                                "prompt_version": GENERATION_PROMPT_VERSION})
    evidence_hash = variant["evidence"]["evidence_hash"]
    key = _stable_hash({"validation_version": VERSION, "case_id": row["case_id"],
                        "evidence_hash": evidence_hash, "prompt_config_hash": prompt_hash,
                        "generator_model": model})
    return {"key": key, "prompt_hash": prompt_hash, "evidence_hash": evidence_hash,
            "sources": sources, "chunks": chunks}


def _unique_routes(row: dict) -> list[str]:
    routes = ["adaptive_prefix_v1"]
    if (row["adaptive_decision"] == "fixed_top5" and
        row["variants"]["fixed_top5"]["evidence"]["evidence_hash"] !=
            row["variants"]["adaptive_prefix_v1"]["evidence"]["evidence_hash"]):
        routes.append("fixed_top5")
    return routes


def generate() -> None:
    prepared, _, _ = _load_prepared()
    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    config = LLMConfig.from_env(ROOT / ".env")
    model = config.model
    client = OpenAIChatCompletionsClient(config)
    cache = _V3Cache(CACHE)
    calls = 0
    for row in prepared["cases"]:
        for route in _unique_routes(row):
            identity = _generation_identity(row, route, model)
            existing = cache.get(identity["key"])
            if existing is not None:
                if (existing.get("kind") != "generation" or
                    not isinstance(existing.get("answer"), str) or
                    not existing["answer"].strip() or
                    existing.get("generation_hash") != _stable_hash(existing["answer"])):
                    raise ValueError(f"invalid cached generation: {row['case_id']}/{route}")
                continue
            recorder = _RecordingGenerationClient(client)
            produced = generate_grounded_answer(row["query"], [],
                [SimpleNamespace(**chunk) for chunk in identity["chunks"]],
                recorder, model=model, cache=None,
                max_tokens=V3_GENERATION_MAX_TOKENS)
            cache.set(identity["key"], {"kind": "generation", "answer": produced["answer"],
                "generation_hash": _stable_hash(produced["answer"]),
                "evidence_hash": identity["evidence_hash"],
                "prompt_config_hash": identity["prompt_hash"],
                "model": model, "provider_usage": recorder.usage})
            calls += 1
            print(f"Generated {row['case_id']} {route}", flush=True)
    print(f"Generation complete: {calls} new API calls")


def _judge_request(row: dict, rubric_case: dict, model: str, cache: _V3Cache,
                   routes: list[str] | None = None) -> tuple[str, list[dict], dict]:
    owners = []
    for route in routes or _unique_routes(row):
        identity = _generation_identity(row, route, model)
        generation = cache.get(identity["key"])
        if generation is None or generation.get("kind") != "generation":
            raise ValueError(f"missing generation: {row['case_id']}/{route}")
        owners.append({"generation": generation, "sources": identity["sources"],
                       "evidence_hash": identity["evidence_hash"],
                       "generation_key": identity["key"]})
    owners.sort(key=lambda item: _stable_hash({"case_id": row["case_id"],
                                                "generation_key": item["generation_key"]}))
    labeled = {chr(65+i): owner for i, owner in enumerate(owners)}
    prompt_case = {"case_id": row["case_id"], "query": row["query"],
                   "facts": [{"fact_id": f["fact_id"], "fact": f["statement"]}
                             for f in rubric_case["facts"]]}
    messages = _judge_messages(prompt_case, labeled)
    rubric_sha = _sha256(ROOT / "eval/validation/broad_atomic_facts_validation_v1.json")
    prompt_hash = _stable_hash({"messages": messages, "temperature": 0.0,
                                "max_tokens": V3_JUDGE_MAX_TOKENS, "version": JUDGE_VERSION})
    key = _stable_hash({"validation_version": VERSION, "rubric_sha256": rubric_sha,
                        "case_id": row["case_id"], "judge_model": model,
                        "judge_prompt_config_hash": prompt_hash,
                        "answer_hashes": {label: item["generation"]["generation_hash"]
                                          for label, item in labeled.items()},
                        "evidence_hashes": {label: item["evidence_hash"]
                                            for label, item in labeled.items()}})
    return key, messages, labeled


def _judge_case(row: dict, rubric_case: dict, model: str, cache: _V3Cache,
                client) -> int:
    routes = _unique_routes(row)
    grouped_key, _, _ = _judge_request(row, rubric_case, model, cache)
    if cache.get(grouped_key) is not None:
        return 0
    single_keys = [_judge_request(row, rubric_case, model, cache, [route])[0]
                   for route in routes]
    if len(routes) > 1 and all(cache.get(key) is not None for key in single_keys):
        return 0

    def call(subset: list[str]) -> int:
        key, messages, labeled = _judge_request(row, rubric_case, model, cache, subset)
        if cache.get(key) is not None:
            return 0
        raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS,
                                                temperature=0.0)
        try:
            parsed = _parse_judge(raw, set(labeled),
                                  {f["fact_id"] for f in rubric_case["facts"]})
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError(f"judge output failed schema for {row['case_id']}: {error}") from error
        cache.set(key, {"kind": "judge", "answers": parsed, "raw_hash": _stable_hash(raw),
                        "provider_usage": usage,
                        "generation_keys": {label: item["generation_key"]
                                            for label, item in labeled.items()}})
        return 1

    if len(routes) > 1 and any(cache.get(key) is not None for key in single_keys):
        calls = sum(call([route]) for route in routes)
    else:
        try:
            calls = call(routes)
        except ValueError:
            if len(routes) == 1:
                raise
            # A two-answer response can truncate. Retry each independently and cache successes.
            calls = 1 + sum(call([route]) for route in routes)
    print(f"Judged {row['case_id']}", flush=True)
    return calls


def judge() -> None:
    prepared, _, rubric = _load_prepared()
    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    config = LLMConfig.from_env(ROOT / ".env")
    client = OpenAIChatCompletionsClient(config)
    cache = _V3Cache(CACHE)
    cases = {case["case_id"]: case for case in rubric["cases"]}
    calls = sum(_judge_case(row, cases[row["case_id"]], config.model, cache, client)
                for row in prepared["cases"])
    print(f"Judging complete: {calls} new API calls")


def _get_judgment(row: dict, rubric_case: dict, model: str, cache: _V3Cache) -> dict:
    key, _, _ = _judge_request(row, rubric_case, model, cache)
    entry = cache.get(key)
    identities = {_generation_identity(row, route, model)["key"]: route
                  for route in _unique_routes(row)}
    if entry is not None:
        return {identities[generation_key]: entry["answers"][label]
                for label, generation_key in entry["generation_keys"].items()}
    judged = {}
    for route in _unique_routes(row):
        single_key, _, _ = _judge_request(row, rubric_case, model, cache, [route])
        single = cache.get(single_key)
        if single is None:
            raise ValueError(f"missing successful judge: {row['case_id']}/{route}")
        judged[route] = single["answers"]["A"]
    return judged


def _scored_variant(row: dict, rubric_case: dict, route: str, judged: dict,
                    model: str, cache: _V3Cache) -> dict:
    identity = _generation_identity(row, route, model)
    cached = cache.get(identity["key"])
    citation = validate_citations(cached["answer"], identity["sources"])
    generation = {**cached, "generation_key": identity["key"],
                  "citation_validation": citation["validation"],
                  "citation_ids": citation["citation_ids"],
                  "cited_sources": citation["sources"]}
    evidence = row["variants"][route]["evidence"]
    case = {"case_id": row["case_id"],
            "facts": [{"fact_id": f["fact_id"]} for f in rubric_case["facts"]],
            "evidence": {"candidate_pool": row["candidate_pool"]},
            "variants": {route: {"chunks": identity["chunks"],
                                  "generation": generation,
                                  "available_fact_ids": evidence["covered_fact_ids"],
                                  "evidence_tokens": evidence["evidence_tokens"]}}}
    return _score_v3_answer(case, route, judged)


def _quality_summary(items: list[dict], total_facts: int) -> dict:
    qualities = [item["quality"] for item in items]
    claims = Counter()
    citations = Counter()
    failures = Counter()
    for item in items:
        claims.update(item["quality"]["claims"])
        citations.update(item["quality"]["claim_citations"])
        failures.update(d["cause"] for d in item["pipeline_diagnosis"])
        failures.update(d["cause"] for d in item["claim_diagnosis"])
    return {"answer_macro": mean(q["fact_coverage"] for q in qualities),
            "answer_micro": sum(q["covered_count"] for q in qualities) / total_facts,
            "fact_complete_cases": sum(q["fact_complete"] for q in qualities),
            "grounded_macro": mean(q["grounded_fact_coverage"] for q in qualities),
            "grounded_micro": sum(q["grounded_covered_count"] for q in qualities) / total_facts,
            "grounded_complete_cases": sum(q["grounded_fact_complete"] for q in qualities),
            "evidence_utilization": _mean_non_null(q["evidence_utilization"]["rate"]
                                                    for q in qualities),
            "grounded_utilization": _mean_non_null(q["grounded_evidence_utilization"]["rate"]
                                                    for q in qualities),
            "claim_counts": dict(claims), "citation_counts": dict(citations),
            "valid_citation_id_cases": sum(q["citation_id_valid"] for q in qualities),
            "pipeline_failure_counts": dict(failures),
            "evidence_tokens": sum(item["evidence_tokens"] for item in items)}


def _mean_non_null(values) -> float | None:
    data = [v for v in values if v is not None]
    return mean(data) if data else None


def classify_stop(route: str, v1: dict, adaptive: dict,
                  fixed_reference: dict | None = None) -> str:
    if route != "fixed_top5":
        return ("conservative_miss" if fixed_reference is not None and
                _equivalent(v1, fixed_reference) else "unobserved")
    before, after = v1["quality"], adaptive["quality"]
    if (after["grounded_covered_count"] < before["grounded_covered_count"] or
        before["grounded_fact_complete"] and not after["grounded_fact_complete"] or
        after["claims"].get("unsupported", 0) > before["claims"].get("unsupported", 0) or
        after["claims"].get("contradicted", 0) > before["claims"].get("contradicted", 0)):
        return "false_stop"
    if _equivalent(v1, adaptive):
        return "safe_stop"
    return "other_stop"


def _bad_claims(quality: dict) -> int:
    return quality["claims"].get("unsupported", 0) + quality["claims"].get("contradicted", 0)


def _bad_citations(quality: dict) -> int:
    return quality["claim_citations"].get("unsupported", 0) + quality["claim_citations"].get("missing", 0)


def _equivalent(v1: dict, adaptive: dict) -> bool:
    before, after = v1["quality"], adaptive["quality"]
    return (after["grounded_covered_count"] == before["grounded_covered_count"] and
            after["grounded_fact_complete"] == before["grounded_fact_complete"] and
            _bad_claims(after) <= _bad_claims(before) and
            _bad_citations(after) <= _bad_citations(before))


def quality_gates(v1: dict, adaptive: dict, paired: list[dict], metadata: dict) -> dict:
    rules = metadata["preregistration"]["primary_quality_gates"]
    regret = v1["grounded_micro"] - adaptive["grounded_micro"]
    complete_deficit = v1["grounded_complete_cases"] - adaptive["grounded_complete_cases"]
    v1_bad = v1["claim_counts"].get("unsupported", 0) + v1["claim_counts"].get("contradicted", 0)
    adaptive_bad = (adaptive["claim_counts"].get("unsupported", 0) +
                    adaptive["claim_counts"].get("contradicted", 0))
    worse = sum(_bad_claims(row["frozen_adaptive"]["quality"]) >
                _bad_claims(row["always_v1"]["quality"]) for row in paired)
    better = sum(_bad_claims(row["frozen_adaptive"]["quality"]) <
                 _bad_claims(row["always_v1"]["quality"]) for row in paired)
    claims_rule = rules["unsupported_or_contradicted_claims"]
    gates = {
        "grounded_micro_regret": {"value": regret,
            "limit": rules["grounded_micro_fact_coverage"]["maximum_regret_absolute"],
            "pass": regret <= rules["grounded_micro_fact_coverage"]["maximum_regret_absolute"] + 1e-12},
        "grounded_complete_deficit": {"value": complete_deficit,
            "limit": rules["grounded_fact_complete_cases"]["maximum_case_deficit"],
            "pass": complete_deficit <= rules["grounded_fact_complete_cases"]["maximum_case_deficit"]},
        "claim_quality": {"total_excess": adaptive_bad-v1_bad,
            "paired_worse": worse, "paired_better": better,
            "pass": (adaptive_bad-v1_bad <= claims_rule["maximum_total_claim_excess"] and
                     worse-better <= claims_rule["maximum_paired_worse_minus_better_cases"])}
    }
    gates["overall"] = "PASS" if all(item["pass"] for item in gates.values()) else "FAIL"
    return gates


def report() -> dict:
    prepared, metadata, rubric = _load_prepared()
    model = _llm_model()
    cache = _V3Cache(CACHE)
    by_id = {case["case_id"]: case for case in rubric["cases"]}
    rows = []
    for row in prepared["cases"]:
        judged = _get_judgment(row, by_id[row["case_id"]], model, cache)
        v1 = _scored_variant(row, by_id[row["case_id"]], "adaptive_prefix_v1",
                             judged["adaptive_prefix_v1"], model, cache)
        route = row["adaptive_decision"]
        adaptive = (v1 if route == "adaptive_prefix_v1" or route not in judged else
                    _scored_variant(row, by_id[row["case_id"]], route,
                                    judged[route], model, cache))
        row_result = _prepared_public_row(row) | {"always_v1": v1,
            "frozen_adaptive": adaptive, "stop_classification": classify_stop(route, v1, adaptive),
            "new_selection_misses": sorted(set(d["fact_id"] for d in adaptive["pipeline_diagnosis"]
                                                  if d["cause"] == "selection_miss") -
                                            set(d["fact_id"] for d in v1["pipeline_diagnosis"]
                                                if d["cause"] == "selection_miss"))}
        rows.append(row_result)
    total = sum(row["required_fact_count"] for row in prepared["cases"])
    v1_summary = _quality_summary([row["always_v1"] for row in rows], total)
    adaptive_summary = _quality_summary([row["frozen_adaptive"] for row in rows], total)
    gates = quality_gates(v1_summary, adaptive_summary, rows, metadata)
    saving = 1-adaptive_summary["evidence_tokens"]/v1_summary["evidence_tokens"]
    efficiency = None
    if gates["overall"] == "PASS":
        efficiency = ("strong" if saving > .10 else "effective but limited" if saving >= .05
                      else "conservative" if saving >= 0 else "failure")
    counts = Counter(row["stop_classification"] for row in rows)
    false_rows = [row for row in rows if row["stop_classification"] == "false_stop"]
    false_clusters = {field: dict(Counter(row[field] for row in false_rows))
                      for field in ("policy_family", "query_type", "difficulty")}
    potential_mapping_issues = [
        {"case_id": row["case_id"], "strategy": name,
         "fact_ids": row[name]["quality"]["answered_without_mapped_evidence_fact_ids"],
         "status": "requires human review"}
        for row in rows for name in STRATEGIES
        if row[name]["quality"]["answered_without_mapped_evidence_fact_ids"]]
    result = {"schema_version": 1, "version": VERSION, "status": "complete",
              "verdict": gates["overall"], "frozen": _json(RESULTS)["frozen"],
              "case_count": 50, "required_fact_count": total, "model": model,
              "preparation": _json(RESULTS)["preparation"],
              "evidence": _json(RESULTS)["evidence"],
              "strategies": {"always_v1": v1_summary, "frozen_adaptive": adaptive_summary},
              "quality_gates": gates,
              "efficiency": {"evidence_token_saving_fraction": saving,
                             "interpretation": efficiency},
              "stopping": {"safe_stops": counts["safe_stop"],
                           "false_stops": counts["false_stop"],
                           "other_stops": counts["other_stop"],
                           "false_stop_clusters": false_clusters,
                           "conservative_misses": None,
                           "conservative_miss_note": "Fixed answers were not generated on V1-route cases, so this is unobserved."},
              "validation_rubric_issues": potential_mapping_issues, "cases": rows}
    _save(RESULTS, result)
    _write_atomic(SUMMARY, _render_summary(result))
    _write_atomic(REVIEW, _render_review(result))
    print(f"Validation {gates['overall']}; reports written")
    return result


def _render_summary(result: dict) -> str:
    prep = result["preparation"]
    v1 = result["strategies"]["always_v1"]
    adaptive = result["strategies"]["frozen_adaptive"]
    gates = result["quality_gates"]
    lines = ["# Validation V1", "", "## Setup",
        f"- 50 untouched cases; 239 required facts.",
        f"- Strategy SHA-256: `{result['frozen']['strategy_sha256']}`.",
        f"- Rubric SHA-256: `{result['frozen']['rubric_sha256']}`.", "",
        "## Frozen Strategy", "Minimum Top5 reranker score ≥ 2.5 → Fixed; otherwise V1.", "",
        "## Quality Gate", "| Metric | V1 | Adaptive | Regret | Gate |",
        "|---|---:|---:|---:|---|",
        f"| Answer micro | {v1['answer_micro']:.3f} | {adaptive['answer_micro']:.3f} | — | diagnostic |",
        f"| Grounded micro | {v1['grounded_micro']:.3f} | {adaptive['grounded_micro']:.3f} | {gates['grounded_micro_regret']['value']:.3f} | {'PASS' if gates['grounded_micro_regret']['pass'] else 'FAIL'} |",
        f"| Grounded complete | {v1['grounded_complete_cases']} | {adaptive['grounded_complete_cases']} | {gates['grounded_complete_deficit']['value']} | {'PASS' if gates['grounded_complete_deficit']['pass'] else 'FAIL'} |",
        f"| Unsupported + contradicted | {_claim_total(v1)} | {_claim_total(adaptive)} | {gates['claim_quality']['total_excess']} | {'PASS' if gates['claim_quality']['pass'] else 'FAIL'} |",
        f"| Paired claim worse / better | — | {gates['claim_quality']['paired_worse']} / {gates['claim_quality']['paired_better']} | — | {'PASS' if gates['claim_quality']['pass'] else 'FAIL'} |",
        "", "## Efficiency", f"Evidence tokens: V1 {v1['evidence_tokens']:,}; Adaptive {adaptive['evidence_tokens']:,}; saving {result['efficiency']['evidence_token_saving_fraction']:.1%}."]
    if result["verdict"] == "PASS":
        lines.append(f"Interpretation: {result['efficiency']['interpretation']}.")
    lines += ["", "## Stopping Behavior",
        f"Fixed {prep['fixed_triggers']}/50; V1 {prep['v1_routes']}/50. Safe {result['stopping']['safe_stops']}; false {result['stopping']['false_stops']}; other {result['stopping']['other_stops']}.",
        "Conservative misses are unobserved because Fixed was not generated for V1-route cases.",
        "", "## Failure Diagnosis",
        f"V1: {v1['pipeline_failure_counts']}. Adaptive: {adaptive['pipeline_failure_counts']}.",
        f"False-stop clusters: {result['stopping']['false_stop_clusters']}.",
        "", "## Verdict", result["verdict"], ""]
    return "\n".join(lines)


def _claim_total(summary: dict) -> int:
    return summary["claim_counts"].get("unsupported", 0) + summary["claim_counts"].get("contradicted", 0)


def _render_review(result: dict) -> str:
    lines = ["# Validation V1 Human Review", "",
        "Review judge uncertainty, evidence mapping gaps, false stops, and claims with weak support. Frozen files must not be edited based on these results.", ""]
    for row in result["cases"]:
        if row["stop_classification"] != "false_stop" and not any(
                row[name]["review_required"] for name in STRATEGIES):
            continue
        lines += [f"## {row['case_id']} — {row['stop_classification']}",
                  f"- Route: {row['adaptive_decision']}; min Top5: {row['minimum_top5_score']:.3f}.",
                  f"- New selection misses: {row['new_selection_misses']}."]
        for name in STRATEGIES:
            item = row[name]
            lines += [f"- {name}: grounded {item['quality']['grounded_covered_count']}/{item['quality']['required_fact_count']}; missing {item['quality']['grounded_missing_fact_ids']}; claims {item['quality']['claims']}."]
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    phase = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "generate", "judge", "report"):
        phase.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args(argv)
    if args.prepare:
        prepare()
    elif args.generate:
        generate()
    elif args.judge:
        judge()
    else:
        report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
