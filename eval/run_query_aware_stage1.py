"""Offline Stage 1 generation planner. This module has no live execution entry point."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import median
from types import SimpleNamespace

from eval.run_answer_eval import V3_GENERATION_MAX_TOKENS, _stable_hash
from eval.run_stage0_replay import no_router_adaptive_rows, route_query
from eval.run_validation import VERSION, _evidence_hash
from src.evidence_budget import EvidenceBudgetConfig
from src.evidence_selector import CoverageSelectorConfig
from src.generator import (GENERATION_PROMPT_VERSION, GROUNDING_SYSTEM_PROMPT,
                           assign_evidence_sources, build_grounded_messages,
                           format_evidence)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "eval/results/query_aware_stage1_dry_run.json"
SUMMARY = ROOT / "eval/results/query_aware_stage1_dry_run_summary.md"
FROZEN_HASHES = {
    "eval/query_aware_stage0_config.json": "744ed411e301aaf28a3751be99c31157b26dcbcf524673f749aa711d2a82e3a6",
    "eval/query_aware_router_v1.json": "dcc7d4953f3ba9794c35f2168e29f419bbb40eb014775cf8ccb5e0e7ae913bd7",
    "eval/query_aware_arms_v1.json": "18d7adbfd1ac8a1802dbf29d2c222fb988d0c495ca4f979c24297a406f0112c9",
    "eval/results/frozen_human_verdicts_v1.json": "85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716",
    "eval/results/a0_bge_rerank_orders.json": "fb15b316c4b5170514e6f1c5140689ba0e77869dd516b7c7e170593c4db5b2e2",
    "eval/results/stage0_replay_results.json": "5e7d665bdae13803dd00d39756881f55e5a6792eb01ca37d0e2f63a4e1563703",
}
POLICIES = ("fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2",
            "no_router_adaptive_v1", "query_router_v1")
SETTINGS = {"temperature": 0.0, "max_tokens": V3_GENERATION_MAX_TOKENS}
TELEMETRY_FIELDS = ("provider", "model", "input_tokens", "output_tokens",
                    "latency_seconds", "cache_hit", "error", "retry_count",
                    "request_id", "estimated_cost")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"missing frozen artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_hashes(root: Path = ROOT) -> dict[str, str]:
    for relative, expected in FROZEN_HASHES.items():
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing frozen artifact: {relative}")
        if sha(path) != expected:
            raise ValueError(f"frozen hash mismatch: {relative}")
    config = load(root / "eval/query_aware_stage0_config.json")
    for relative, expected in config["artifact_hashes"].items():
        path = root / relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"Stage 0 artifact hash mismatch: {relative}")
    return {name: sha(root / name) for name in FROZEN_HASHES}


def validate_arms(arms: dict, config: dict, router: dict) -> dict[str, dict]:
    rows = arms["arms"]
    if tuple(row["policy_id"] for row in rows) != POLICIES:
        raise ValueError("frozen arm mismatch: policy IDs/order")
    if arms["cache_key_schema"]["stage1_generation_key"] != (
            "stable_hash({validation_version, case_id, evidence_hash, prompt_config_hash, "
            "generator_model, context_policy_id, context_policy_hash})"):
        raise ValueError("frozen generation-key schema mismatch")
    for row in rows:
        policy, params = row["policy_id"], row["params"]
        if policy == "fixed_top5":
            if params != {"k": config["research_baseline"]["context_k"]}:
                raise ValueError("fixed policy parameter mismatch")
        elif policy in ("adaptive_prefix_v1", "coverage_selector_v2"):
            cls = EvidenceBudgetConfig if policy == "adaptive_prefix_v1" else CoverageSelectorConfig
            if params != asdict(cls()) or params != config["policy_configs"][policy]["config"]:
                raise ValueError(f"frozen arm mismatch: {policy} parameters")
            if _stable_hash(params) != row["policy_hash"] or row["policy_hash"] != config["policy_configs"][policy]["config_hash"]:
                raise ValueError(f"frozen arm mismatch: {policy} hash")
        elif policy == "no_router_adaptive_v1":
            # The replay implementation uses these defaults. Verify every value before invoking it.
            from eval.run_stage0_replay import NO_ROUTER_DEFAULTS
            if params != NO_ROUTER_DEFAULTS:
                raise ValueError("frozen arm mismatch: no-router parameters")
        elif policy == "query_router_v1":
            if (params["router_version"] != router["version"] or
                params["router_rule_hash"] != config["router"]["rule_hash"] or
                params["simple_policy"] != POLICIES[0] or
                params["broad_policy"] != POLICIES[1]):
                raise ValueError("frozen arm mismatch: router mapping")
        else:
            raise ValueError(f"unknown policy ID: {policy}")
    return {row["policy_id"]: row for row in rows}


def canonical_identity(case_id: str, query: str, rewritten_query: str, chunks: list[dict],
                       model: str, policy: dict, frozen: dict[str, str]) -> dict:
    if not all((case_id, query, rewritten_query, model, chunks)):
        raise ValueError("incomplete generation identity")
    sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
    context = format_evidence(sources)
    messages = build_grounded_messages(rewritten_query, [], sources)
    if context not in messages[1]["content"] or messages[0]["content"] != GROUNDING_SYSTEM_PROMPT:
        raise ValueError("context serialization mismatch")
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    evidence_hash = _evidence_hash(chunks)
    prompt_hash = _stable_hash({"messages": messages, **SETTINGS,
                                "prompt_version": GENERATION_PROMPT_VERSION})
    policy_hash = policy["policy_hash"] or _stable_hash(policy["params"])
    key_fields = {"validation_version": VERSION, "case_id": case_id,
                  "evidence_hash": evidence_hash, "prompt_config_hash": prompt_hash,
                  "generator_model": model, "context_policy_id": policy["policy_id"],
                  "context_policy_hash": policy_hash}
    canonical = {"case_id": case_id, "original_query": query,
                 "rewritten_query": rewritten_query,
                 "selected_chunk_ids": [chunk["chunk_id"] for chunk in chunks],
                 "serialized_context": context, "context_hash": context_hash,
                 "messages": messages, "generation_prompt_hash": prompt_hash,
                 "generation_model": model, "generation_config": dict(SETTINGS),
                 "frozen_artifact_hashes": frozen}
    return {"canonical": canonical, "canonical_hash": _stable_hash(canonical),
            "context_hash": context_hash, "evidence_hash": evidence_hash,
            "prompt_hash": prompt_hash, "generation_key": _stable_hash(key_fields),
            "generation_key_fields": key_fields, "sources": sources}


def same_generation_input(left: dict, right: dict) -> bool:
    """Policy and artifact provenance are excluded; the actual provider request is compared."""
    fields = ("case_id", "original_query", "rewritten_query", "selected_chunk_ids",
              "serialized_context", "messages", "generation_model", "generation_config")
    return all(left[field] == right[field] for field in fields)


def provider_input_hash(canonical: dict) -> str:
    """Identity shared by arm rows making the same provider request."""
    fields = ("case_id", "original_query", "rewritten_query", "selected_chunk_ids",
              "serialized_context", "messages", "generation_model", "generation_config")
    return _stable_hash({field: canonical[field] for field in fields})


def register_generation_key(registry: dict[str, str], key: str, canonical_hash: str) -> None:
    if key in registry and registry[key] != canonical_hash:
        raise ValueError(f"duplicate conflicting generation key: {key}")
    registry[key] = canonical_hash


def validate_route(case_id: str, query: str, router: dict, replay_route: str) -> str:
    actual = route_query(query)
    if actual != router["distribution"]["validation_v1_50"]["labels"][case_id] or actual != replay_route:
        raise ValueError(f"route mismatch: {case_id}")
    return actual


def old_cache_reuse(identity: dict, case_id: str, chunks: list[dict], model: str,
                    cache: dict, top5_ids: list[str]) -> str | None:
    if identity["canonical"]["selected_chunk_ids"] != top5_ids:
        return None
    legacy_key = _stable_hash({"validation_version": VERSION, "case_id": case_id,
                               "evidence_hash": identity["evidence_hash"],
                               "prompt_config_hash": identity["prompt_hash"],
                               "generator_model": model})
    entry = cache.get(legacy_key)
    if entry is None:
        return None
    if (entry.get("kind") != "generation" or entry.get("model") != model or
        entry.get("evidence_hash") != _evidence_hash(chunks) or
        entry.get("prompt_config_hash") != identity["prompt_hash"] or
        not isinstance(entry.get("answer"), str) or not entry["answer"].strip() or
        entry.get("generation_hash") != _stable_hash(entry["answer"])):
        raise ValueError(f"invalid legacy generation provenance: {case_id}")
    return legacy_key


def validate_live_telemetry(row: dict) -> None:
    missing = [field for field in TELEMETRY_FIELDS if field not in row]
    if missing:
        raise ValueError("provider telemetry unavailable: " + ", ".join(missing))
    for field in ("input_tokens", "output_tokens"):
        value = row[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"provider telemetry unavailable: {field}")
    if not isinstance(row["latency_seconds"], (float, int)) or row["latency_seconds"] < 0:
        raise ValueError("provider telemetry unavailable: latency_seconds")
    if not row["provider"] or not row["model"]:
        raise ValueError("provider telemetry unavailable: provider/model")
    if not isinstance(row["cache_hit"], bool) or not isinstance(row["retry_count"], int):
        raise ValueError("provider telemetry unavailable: cache_hit/retry_count")
    if row["estimated_cost"] is None or not isinstance(row["estimated_cost"], (int, float)):
        raise ValueError("provider telemetry unavailable: estimated_cost")


def estimate_cost(input_tokens: int, output_tokens: int, price: dict) -> float:
    """External price table supplies currency per million provider tokens."""
    if any(not isinstance(value, (int, float)) or value < 0 for value in
           (input_tokens, output_tokens, price.get("input_per_million"),
            price.get("output_per_million"))):
        raise ValueError("valid external provider price table and token counts required")
    return (input_tokens * price["input_per_million"] +
            output_tokens * price["output_per_million"]) / 1_000_000


def rewrite_was_live(rewrite: dict) -> bool:
    if not isinstance(rewrite.get("invoked"), bool) or not isinstance(rewrite.get("cache_hit"), bool):
        raise ValueError("rewrite provenance unavailable: invoked/cache_hit")
    if rewrite["invoked"] and not rewrite.get("cache_key"):
        raise ValueError("rewrite provenance unavailable: cache_key")
    return rewrite["invoked"] and not rewrite["cache_hit"]


def legacy_generation_usage(plan_row: dict, cache: dict) -> dict[str, int]:
    """Recover historical provider usage for an exact frozen-cache reuse."""
    source = plan_row.get("reuse_source")
    prefix = "cache/validation_v1_llm_cache.json:"
    if plan_row.get("generation_source") != "reused" or not isinstance(source, str) or not source.startswith(prefix):
        raise ValueError("legacy generation cache provenance unavailable")
    key = source[len(prefix):]
    entry = cache.get(key)
    if (not isinstance(entry, dict) or entry.get("kind") != "generation" or
        entry.get("model") != plan_row["generation_model"] or
        entry.get("prompt_config_hash") != plan_row["generation_prompt_hash"] or
        entry.get("evidence_hash") != plan_row["generation_key_fields"]["evidence_hash"] or
        not isinstance(entry.get("answer"), str) or
        entry.get("generation_hash") != _stable_hash(entry["answer"])):
        raise ValueError(f"invalid legacy generation provenance: {plan_row['case_id']}/{plan_row['arm']}")
    usage = entry.get("provider_usage")
    if not isinstance(usage, dict):
        raise ValueError(f"missing legacy provider usage: {source}")
    for field in ("input_tokens", "output_tokens"):
        value = usage.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"missing legacy provider usage: {source}/{field}")
    return {field: usage[field] for field in ("input_tokens", "output_tokens")}


def validate_frozen_rewrite(plan_row: dict, rewrite: dict) -> None:
    rewrite_was_live(rewrite)
    frozen_off = (plan_row.get("rewrite_live_expected") == 0 or
                  plan_row.get("rewrite", {}).get("status") == "not_applicable_single_turn")
    if frozen_off and (rewrite["invoked"] or rewrite["cache_hit"]):
        raise ValueError("unexpected rewrite in frozen single-turn generation plan")
    if rewrite.get("rewritten_query") not in (None, plan_row["rewritten_query"]):
        raise ValueError("rewrite changed canonical generation identity")


def record_live_result(plan_row: dict, answer: str, rewrite: dict, generation: dict,
                       *, wall_seconds: float, legacy_cache: dict | None = None,
                       chunk_meta: dict | None = None) -> dict:
    """Future execution adapter: accept measured calls only; never invoke a provider here."""
    from src.generator import validate_citations

    if not answer.strip() or wall_seconds < 0:
        raise ValueError("invalid live result")
    validate_frozen_rewrite(plan_row, rewrite)
    if rewrite_was_live(rewrite):
        validate_live_telemetry(rewrite)
    if plan_row["requires_provider_call"]:
        validate_live_telemetry(generation)
        if generation["cache_hit"]:
            raise ValueError("new generation owner unexpectedly hit cache")
    else:
        if generation.get("cache_hit") is not True:
            raise ValueError("reused generation lacks cache provenance")
    generation = dict(generation)
    if plan_row["generation_source"] == "reused":
        cache = legacy_cache if legacy_cache is not None else load(ROOT / "cache/validation_v1_llm_cache.json")
        usage = legacy_generation_usage(plan_row, cache)
        for field, value in usage.items():
            if generation.get(field) not in (None, value):
                raise ValueError("legacy cache usage conflicts with supplied generation telemetry")
        generation.update(usage)
        generation["usage_source"] = plan_row["reuse_source"]
    elif not plan_row["requires_provider_call"]:
        generation["usage_source"] = plan_row["reuse_source"]
    else:
        generation["usage_source"] = "live_provider"
    chunks = chunk_meta if chunk_meta is not None else {
        chunk["chunk_id"]: chunk for chunk in load(ROOT / "cache/policy_index.json")["chunks"]}
    sources = assign_evidence_sources([SimpleNamespace(**chunks[cid])
                                       for cid in plan_row["selected_chunk_ids"]])
    if format_evidence(sources) != plan_row["serialized_context"]:
        raise ValueError("context serialization mismatch")
    cited = validate_citations(answer, sources)
    rewrite_tokens = ((rewrite.get("input_tokens") or 0) +
                      (rewrite.get("output_tokens") or 0)) if rewrite_was_live(rewrite) else 0
    generation_tokens = ((generation["input_tokens"] + generation["output_tokens"])
                         if all(isinstance(generation.get(field), int) for field in ("input_tokens", "output_tokens"))
                         else None)
    result = {key: value for key, value in plan_row.items() if key not in ("answer", "citations", "telemetry", "validation")}
    result.update({"answer": answer, "citations": cited["sources"],
                   "telemetry": {"rewrite": rewrite, "generation": generation,
                     "total": {"provider_tokens": rewrite_tokens + generation_tokens if generation_tokens is not None else None,
                               "estimated_cost": ((rewrite.get("estimated_cost") or 0) if rewrite_was_live(rewrite) else 0) +
                                                 generation["estimated_cost"] if isinstance(generation.get("estimated_cost"), (int, float)) else None,
                               "wall_seconds": wall_seconds,
                               "evidence_tokens": plan_row["evidence_tokens"],
                               "local_work": plan_row["local_work"]},
                     "physical_execution": {"new_generation_calls": int(plan_row["requires_provider_call"]),
                       "input_tokens": generation["input_tokens"] if plan_row["requires_provider_call"] else 0,
                       "output_tokens": generation["output_tokens"] if plan_row["requires_provider_call"] else 0,
                       "estimated_cost": generation["estimated_cost"] if plan_row["requires_provider_call"] else 0}},
                   "validation": cited["validation"]})
    return result


def aggregate_live_results(results: list[dict], *, price_table: dict,
                           legacy_cache: dict | None = None) -> dict:
    """Separate each arm's stand-alone economics from this experiment's actual spend."""
    cache = legacy_cache if legacy_cache is not None else load(ROOT / "cache/validation_v1_llm_cache.json")
    owners = {}
    for row in results:
        validate_frozen_rewrite(row, row["telemetry"]["rewrite"])
        if row["requires_provider_call"]:
            identity = row["canonical_input_hash"]
            if identity in owners:
                raise ValueError(f"duplicate physical generation owner: {identity}")
            validate_live_telemetry(row["telemetry"]["generation"])
            owners[identity] = row
    resolved = []
    for row in results:
        generation = row["telemetry"]["generation"]
        if row["generation_source"] == "reused":
            if row["requires_provider_call"] or generation.get("cache_hit") is not True:
                raise ValueError("legacy generation reuse provenance mismatch")
            usage = legacy_generation_usage(row, cache)
            usage_source = row["reuse_source"]
        elif row["requires_provider_call"]:
            if generation["cache_hit"]:
                raise ValueError("physical generation owner unexpectedly hit cache")
            usage = {field: generation[field] for field in ("input_tokens", "output_tokens")}
            usage_source = "live_provider"
        else:
            if generation.get("cache_hit") is not True:
                raise ValueError("shared generation lacks reuse provenance")
            owner = owners.get(row["canonical_input_hash"])
            if owner is None or row["provider_call_owner"] != {"case_id": owner["case_id"], "arm": owner["arm"]}:
                raise ValueError(f"shared generation owner missing: {row['case_id']}/{row['arm']}")
            if row["reuse_source"] != f"planned:{owner['case_id']}:{owner['arm']}":
                raise ValueError("shared generation provenance mismatch")
            source = owner["telemetry"]["generation"]
            usage = {field: source[field] for field in ("input_tokens", "output_tokens")}
            for field in usage:
                if generation.get(field) not in (None, usage[field]):
                    raise ValueError("shared generation usage conflicts with owner")
            usage_source = row["reuse_source"]
        rewrite = row["telemetry"]["rewrite"]
        rewrite_live = rewrite_was_live(rewrite)
        if rewrite_live:
            validate_live_telemetry(rewrite)
        input_tokens = usage["input_tokens"] + (rewrite["input_tokens"] if rewrite_live else 0)
        output_tokens = usage["output_tokens"] + (rewrite["output_tokens"] if rewrite_live else 0)
        resolved.append({"case_id": row["case_id"], "arm": row["arm"],
            "canonical_input_hash": row["canonical_input_hash"],
            "generation_usage_source": usage_source,
            "provider_call_owner": row["provider_call_owner"],
            "generation_input_tokens": usage["input_tokens"],
            "generation_output_tokens": usage["output_tokens"],
            "provider_input_tokens": input_tokens, "provider_output_tokens": output_tokens,
            "estimated_cost": estimate_cost(input_tokens, output_tokens, price_table)})
    by_case = {(item["case_id"], item["arm"]): item for item in resolved}
    per_arm = {}
    for arm in POLICIES:
        rows = [row for row in results if row["arm"] == arm]
        costs = [by_case[(row["case_id"], arm)] for row in rows]
        # Cached answers have no historic latency, so no counterfactual provider percentile is inferred.
        latencies = [row["telemetry"]["generation"].get("latency_seconds") for row in rows]
        complete_latency = bool(rows) and all(isinstance(value, (int, float)) for value in latencies)
        def percentile(values: list[float], p: float) -> float:
            ordered = sorted(values)
            rank = (len(ordered) - 1) * p
            lo, hi = int(rank), min(int(rank) + 1, len(ordered) - 1)
            return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)
        per_arm[arm] = {"cases": len(rows), "generation_calls_if_independent": len(rows),
            "reused_result_rows": sum(row["generation_source"] == "reused" for row in rows),
            "rewrite_calls": sum(rewrite_was_live(row["telemetry"]["rewrite"]) for row in rows),
            "provider_input_tokens": sum(item["provider_input_tokens"] for item in costs),
            "provider_output_tokens": sum(item["provider_output_tokens"] for item in costs),
            "cost_per_query": (sum(item["estimated_cost"] for item in costs) / len(rows)) if rows else None,
            "generation_latency_p50_seconds": median(latencies) if complete_latency else None,
            "generation_latency_p95_seconds": percentile(latencies, 0.95) if complete_latency else None,
            "failure_count": sum(not row["validation"]["valid"] for row in rows),
            "evidence_tokens": sum(row["evidence_tokens"] for row in rows),
            "rerank_pairs": sum(row["local_work"]["rerank_pairs"] for row in rows)}
    physical_in = sum(row["telemetry"]["generation"]["input_tokens"] for row in owners.values())
    physical_out = sum(row["telemetry"]["generation"]["output_tokens"] for row in owners.values())
    return {"per_arm_counterfactual": per_arm,
            "per_case_counterfactual": resolved,
            "experiment_physical_execution": {
                "unique_generation_calls": len(owners),
                "provider_input_tokens": physical_in,
                "provider_output_tokens": physical_out,
                "estimated_cost": estimate_cost(physical_in, physical_out, price_table)}}


def build_plan(root: Path = ROOT) -> dict:
    frozen = check_hashes(root)
    config = load(root / "eval/query_aware_stage0_config.json")
    router = load(root / "eval/query_aware_router_v1.json")
    arms = validate_arms(load(root / "eval/query_aware_arms_v1.json"), config, router)
    truth = load(root / "eval/results/frozen_human_verdicts_v1.json")
    if truth.get("status") != "frozen_human_verdicts":
        raise ValueError("human truth is not frozen")
    replay = load(root / "eval/results/stage0_replay_results.json")
    orders = load(root / "eval/results/a0_bge_rerank_orders.json")["cases"]
    cases = load(root / "eval/validation/broad_queries_validation_v1.json")["cases"]
    index = load(root / "cache/policy_index.json")
    cache = load(root / "cache/validation_v1_llm_cache.json")
    chunk_meta = {chunk["chunk_id"]: chunk for chunk in index["chunks"]}
    model = config["research_baseline"]["generation_model"]
    if (model != load(root / "eval/validation/results/validation_v1_results.json")["model"] or
        config["research_baseline"]["generation_prompt_version"] != GENERATION_PROMPT_VERSION):
        raise ValueError("generation model/prompt mismatch")
    if hashlib.sha256(GROUNDING_SYSTEM_PROMPT.encode("utf-8")).hexdigest() != config["research_baseline"]["generation_prompt_sha256"]:
        raise ValueError("generation prompt hash mismatch")
    if config["research_baseline"]["rewrite_applied_in_frozen_replay"] is not False:
        raise ValueError("rewrite pipeline changed; single-turn plan is invalid")
    if len(cases) != 50 or set(orders) != {case["case_id"] for case in cases}:
        raise ValueError("frozen case/order mismatch")
    rows, by_key, by_context, groups = [], {}, {}, defaultdict(list)
    for case in cases:
        case_id, query = case["case_id"], case["query"]
        route = validate_route(case_id, query, router,
                               replay["policy_per_case"][POLICIES[0]][case_id]["route"])
        order = orders[case_id]
        top5 = [item["chunk_id"] for item in order[:arms["fixed_top5"]["params"]["k"]]]
        for policy_id, policy in arms.items():
            replay_row = replay["policy_per_case"][policy_id][case_id]
            if replay_row["route"] != route:
                raise ValueError(f"route mismatch in replay: {case_id}/{policy_id}")
            selected = replay_row["selected_chunk_ids"]
            available = {item["chunk_id"] for item in order}
            if not selected or len(selected) != len(set(selected)) or not set(selected) <= available:
                raise ValueError(f"selected-context mismatch: {case_id}/{policy_id}")
            if policy_id == "fixed_top5" and selected != top5:
                raise ValueError(f"selected-context mismatch: {case_id}/{policy_id}")
            if policy_id == "no_router_adaptive_v1" and selected != [x["chunk_id"] for x in no_router_adaptive_rows(order, **policy["params"])]:
                raise ValueError(f"selected-context mismatch: {case_id}/{policy_id}")
            if policy_id == "query_router_v1":
                expected_policy = policy["params"]["simple_policy" if route == "SIMPLE" else "broad_policy"]
                if selected != replay["policy_per_case"][expected_policy][case_id]["selected_chunk_ids"]:
                    raise ValueError(f"selected-context mismatch: {case_id}/{policy_id}")
            chunks = [chunk_meta[chunk_id] for chunk_id in selected]
            identity = canonical_identity(case_id, query, query, chunks, model, policy, frozen)
            key = identity["generation_key"]
            register_generation_key(by_key, key, identity["canonical_hash"])
            context_hash = identity["context_hash"]
            if context_hash in by_context and by_context[context_hash] != identity["canonical"]["serialized_context"]:
                raise ValueError("context hash collision")
            by_context[context_hash] = identity["canonical"]["serialized_context"]
            reuse_key = old_cache_reuse(identity, case_id, chunks, model, cache, top5)
            provider_input = {k: identity["canonical"][k] for k in (
                "case_id", "original_query", "rewritten_query", "selected_chunk_ids",
                "serialized_context", "messages", "generation_model", "generation_config")}
            provider_hash = provider_input_hash(identity["canonical"])
            groups[provider_hash].append((case_id, policy_id, reuse_key, provider_input))
            rows.append({"case_id": case_id, "arm": policy_id, "policy_id": policy_id,
                         "route": route, "original_query": query, "rewritten_query": query,
                         "selected_chunk_ids": selected, "serialized_context": identity["canonical"]["serialized_context"],
                         "context_hash": context_hash, "generation_prompt_hash": identity["prompt_hash"],
                         "generation_model": model, "generation_config": dict(SETTINGS),
                         "generation_key": key, "generation_key_fields": identity["generation_key_fields"],
                         "canonical_input_hash": provider_hash, "frozen_artifact_hashes": frozen,
                         "rewrite": {"invoked": False, "status": "not_applicable_single_turn",
                                     "cache_hit": False, "cache_key": None, "provider_input_tokens": None,
                                     "provider_output_tokens": None, "latency_seconds": None},
                         "rewrite_live_expected": 0,
                         "evidence_tokens": replay_row["evidence_tokens"],
                         "local_work": {"retrieval_count": 0, "rerank_pairs": 0,
                                        "source": "frozen_stage0_replay"},
                         "expected_telemetry_fields": list(TELEMETRY_FIELDS),
                         "answer": None, "citations": [], "telemetry": {"rewrite": None,
                              "generation": None, "total": None}, "validation": None,
                         "_legacy_key": reuse_key})
    for row in rows:
        group = groups[row["canonical_input_hash"]]
        if any(item[3] != group[0][3] for item in group):
            raise ValueError("canonical generation input hash collision")
        reusable = sorted({item[2] for item in group if item[2]})
        if len(reusable) > 1:
            raise ValueError("conflicting reused generations")
        row["generation_source"] = "reused" if reusable else "new"
        owner = group[0]
        row["provider_call_owner"] = {"case_id": owner[0], "arm": owner[1]}
        row["requires_provider_call"] = not reusable and (row["case_id"], row["arm"]) == (owner[0], owner[1])
        row["reuse_source"] = (f"cache/validation_v1_llm_cache.json:{reusable[0]}" if reusable else
                               (f"planned:{owner[0]}:{owner[1]}" if not row["requires_provider_call"] else None))
        row["shared_generation_arms"] = sorted({item[1] for item in group})
        row["cross_arm_shared"] = len(row["shared_generation_arms"]) > 1
        row.pop("_legacy_key")
    counts = {}
    for policy_id in POLICIES:
        selected = [row for row in rows if row["arm"] == policy_id]
        counts[policy_id] = {"cases": len(selected),
                             "exact_reuse": sum(row["generation_source"] == "reused" for row in selected),
                             "new_required": sum(row["generation_source"] == "new" for row in selected),
                             "cross_arm_shared": sum(row["cross_arm_shared"] for row in selected),
                             "rewrite_cached": 0, "rewrite_required": 0,
                             "invalid_missing_provenance": 0, "context_hash_collisions": 0,
                             "generation_key_collisions": 0, "selected_context_mismatches": 0,
                             "frozen_policy_mismatches": 0}
    unique_new = sum(not any(item[2] for item in group) for group in groups.values())
    if unique_new != sum(row["requires_provider_call"] for row in rows):
        raise ValueError("cross-arm provider call ownership mismatch")
    economics_preview = {}
    for policy_id in POLICIES:
        arm_rows = [row for row in rows if row["arm"] == policy_id]
        cached_usage = [legacy_generation_usage(row, cache) for row in arm_rows
                        if row["generation_source"] == "reused"]
        economics_preview[policy_id] = {
            "known_cached_generation_rows": len(cached_usage),
            "known_cached_provider_input_tokens": sum(item["input_tokens"] for item in cached_usage),
            "known_cached_provider_output_tokens": sum(item["output_tokens"] for item in cached_usage),
            "new_generation_rows_awaiting_live_usage": sum(row["generation_source"] == "new" for row in arm_rows),
            "complete_counterfactual_usage_available": len(cached_usage) == len(arm_rows)}
    return {"schema_version": 1, "version": "query-aware-stage1-dry-run-v1",
            "status": "ready_for_final_reaudit", "llm_calls_made": 0,
            "frozen_integrity": {"artifact_hashes": frozen,
                                 "stage0_checked_artifacts": len(config["artifact_hashes"]),
                                 "generation_model": model,
                                 "generation_prompt_version": GENERATION_PROMPT_VERSION,
                                 "generation_prompt_sha256": config["research_baseline"]["generation_prompt_sha256"]},
            "per_arm": counts, "per_arm_counterfactual_usage_preview": economics_preview,
            "experiment_physical_execution_plan": {"unique_generation_calls_expected": unique_new,
                "provider_input_tokens": None, "provider_output_tokens": None,
                "estimated_cost": None},
            "rewrite_fail_closed": {"frozen_single_turn_live_rewrite_allowed": False},
            "totals": {"case_arm_rows": len(rows),
                "exact_reuse_rows": sum(v["exact_reuse"] for v in counts.values()),
                "new_required_rows": sum(v["new_required"] for v in counts.values()),
                "cross_arm_shared_rows": sum(v["cross_arm_shared"] for v in counts.values()),
                "unique_provider_generations_expected": unique_new,
                "rewrite_cached": 0, "rewrite_live_expected": 0,
                "context_hash_collisions": 0, "generation_key_collisions": 0,
                "selected_context_mismatches": 0, "frozen_policy_mismatches": 0,
                "invalid_missing_provenance": 0}, "blocking_issues": [], "cases": rows}


def write_report(plan: dict, output: Path = OUTPUT, summary: Path = SUMMARY) -> None:
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Query-aware Stage 1 0-LLM dry run", "", "## Frozen integrity", ""]
    lines += [f"- `{key}`: `{value}`" for key, value in plan["frozen_integrity"]["artifact_hashes"].items()]
    lines += [f"- Model: `{plan['frozen_integrity']['generation_model']}`; prompt: `{plan['frozen_integrity']['generation_prompt_version']}` (`{plan['frozen_integrity']['generation_prompt_sha256']}`).",
              f"- Stage 0 input/source hashes checked: {plan['frozen_integrity']['stage0_checked_artifacts']}.",
              "", "## Generation plan", "", "| Arm | Cases | Exact reuse | New required | Cross-arm shared |",
              "|---|---:|---:|---:|---:|"]
    for arm, data in plan["per_arm"].items():
        lines.append(f"| {arm} | {data['cases']} | {data['exact_reuse']} | {data['new_required']} | {data['cross_arm_shared']} |")
    total = plan["totals"]
    lines += ["", f"Unique provider generations expected: **{total['unique_provider_generations_expected']}**.",
              f"Reused result references: **{total['exact_reuse_rows']}**.", "", "## Rewrite plan", "",
              "Frozen Validation V1 is single-turn and its replay has no rewrite. Cached: 0; missing: 0; expected live rewrite calls: 0. The result adapter rejects any unexpected rewrite before recording a generation.",
              "", "## Provenance validation", "",
              f"Missing/invalid: {total['invalid_missing_provenance']}; context collisions: {total['context_hash_collisions']}; generation-key collisions: {total['generation_key_collisions']}; selected-context mismatches: {total['selected_context_mismatches']}; frozen-policy mismatches: {total['frozen_policy_mismatches']}.",
              "", "## Per-arm counterfactual provider usage (known at dry run)", "",
              "Cached historical usage is attributed to every arm-case that consumes it. New generation usage awaits live owner telemetry; full per-arm totals and cost are unavailable until then.",
              "", "| Arm | Known cached rows | Known input tokens | Known output tokens | New rows awaiting usage |",
              "|---|---:|---:|---:|---:|"]
    for arm, usage in plan["per_arm_counterfactual_usage_preview"].items():
        lines.append(f"| {arm} | {usage['known_cached_generation_rows']} | {usage['known_cached_provider_input_tokens']} | {usage['known_cached_provider_output_tokens']} | {usage['new_generation_rows_awaiting_live_usage']} |")
    lines += ["", "## Experiment physical execution plan", "",
              f"Unique new generation calls expected: {total['unique_provider_generations_expected']}; live rewrite calls expected: 0. Shared results count once in physical spend; no calls were made in this dry run.",
              "No live latency or monetary cost was measured.", "",
              "The frozen Stage 1 key does not include serialized context, rewritten query, or all generation settings. The plan retains the frozen key and records these fields plus a canonical input hash for exact validation. The older `cache/generated_answers.json` lacks this full provenance and is excluded from reuse.",
              "", "## Blocking issues", ""]
    lines += plan["blocking_issues"] or ["READY FOR FINAL RE-AUDIT"]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", required=True,
                        help="only supported mode; never calls an LLM")
    args = parser.parse_args()
    assert args.dry_run
    plan = build_plan()
    write_report(plan)
    print(json.dumps(plan["totals"], indent=2))


if __name__ == "__main__":
    main()
