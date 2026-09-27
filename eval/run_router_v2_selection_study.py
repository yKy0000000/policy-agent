"""Router V2 selection study - stage 1: evidence selection and blind evidence judging.

Builds the per-case candidate super-pool from frozen Router V1 artifacts, runs
runtime-legal selection policies and analysis-only oracle bounds, then judges
every selected evidence set with the frozen Router V1.1 blind evidence judge.

Resumable: every new judge call is persisted immediately; rerunning continues
from the cache. No decomposition, router, or retrieval API call is made.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.router_v2_study_lib import (  # noqa: E402
    CONFIG_PATH,
    EVIDENCE_BUDGET,
    EVIDENCE_CACHE_PATH,
    SELECTIONS_PATH,
    STUDY_DIR,
    V1_1_EVIDENCE_CACHE,
    StreamData,
    build_contexts,
    build_policy_selections,
    compute_or_load_local_scores,
    compute_oracle_bounds,
    judge_evidence_selection,
    load_frozen_inputs,
    load_json,
    provenance_for,
    shape_evidence_judgment,
    sha256_file,
    superpool_ids_for,
    write_json,
)

CANDIDATE_POOL_PATH = STUDY_DIR / "candidate_pool_analysis.json"
ORACLE_PATH = STUDY_DIR / "oracle_upper_bound.json"
EVIDENCE_RESULTS_PATH = STUDY_DIR / "evidence_policy_results.json"


def verify_frozen_inputs(config: dict[str, Any]) -> None:
    inputs = config["frozen_inputs"]
    checks = [
        (PROJECT_ROOT / inputs["raw_results_path"], inputs["raw_results_sha256"]),
        (PROJECT_ROOT / inputs["required_aspects_path"], inputs["required_aspects_sha256"]),
        (PROJECT_ROOT / inputs["benchmark_path"], inputs["benchmark_sha256"]),
        (PROJECT_ROOT / inputs["lexical_index_path"], inputs["lexical_index_sha256"]),
        (PROJECT_ROOT / inputs["semantic_index_path"], inputs["semantic_index_sha256"]),
        (PROJECT_ROOT / inputs["semantic_vectors_path"], inputs["semantic_vectors_sha256"]),
    ]
    for path, expected in checks:
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"FROZEN_INPUT_CHANGED: {path} sha256 {actual} != {expected}")


def pre_contexts_from_raw(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    contexts = []
    for case in raw["cases"]:
        streams = [
            StreamData(
                stream_id=stream["stream_id"],
                stream_type=stream["stream_type"],
                query_text=stream["query_text"],
                union_ids=tuple(stream["union_ids"]),
                reranked_ids=tuple(stream["reranked_ids"]),
                stream_top5_ids=tuple(stream["stream_top5_ids"]),
            )
            for stream in case["arms"]["FIXED_DECOMPOSE"]["trace"]["streams"]
        ]
        contexts.append(
            {
                "case_id": case["case_id"],
                "shared_rewrite": case["shared_rewrite"],
                "chunk_ids": list(superpool_ids_for(streams)),
                "chunks": None,
                "streams": [
                    {
                        "stream_id": stream.stream_id,
                        "query_text": stream.query_text,
                        "union_ids": list(stream.union_ids),
                    }
                    for stream in streams
                ],
            }
        )
    from eval.router_v2_study_lib import load_chunk_records

    chunks = load_chunk_records()
    for context in contexts:
        context["chunks"] = chunks
    return contexts


def candidate_pool_analysis(contexts, oracle: dict[str, Any]) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    totals = {
        "superpool_size": 0,
        "novel_chunk_count": 0,
        "novel_supporting_chunk_count": 0,
        "aspects_only_coverable_by_novel_chunks": 0,
        "oracle_top5_covered": 0,
        "oracle_base_top5_covered": 0,
        "superpool_recall": 0,
        "base_union_recall": 0,
    }
    for context in contexts:
        entry = oracle["cases"][context.case_id]
        cases[context.case_id] = {
            "required_total": context.required_total,
            "stream_union_sizes": entry["candidate_pool"]["stream_union_sizes"],
            "superpool_size": entry["candidate_pool"]["superpool_size"],
            "base_union_size": entry["candidate_pool"]["base_union_size"],
            "superpool_minus_base_union": entry["candidate_pool"]["superpool_size"]
            - entry["candidate_pool"]["base_union_size"],
            "novel_chunk_count": entry["novel_chunk_count"],
            "novel_supporting_chunk_count": entry["novel_supporting_chunk_count"],
            "aspects_only_coverable_by_novel_chunks": entry["aspects_only_coverable_by_novel_chunks"],
            "base_union_recall": entry["base_union_recall"],
            "superpool_recall": entry["superpool_recall"],
            "oracle_base_top5_covered": entry["oracle_base_top5"]["covered_count"],
            "oracle_top5_covered": entry["oracle_top5"]["covered_count"],
            "direct_truth_covered": entry["direct_truth_covered"],
            "round_robin_truth_covered": entry["round_robin_truth_covered"],
        }
        totals["superpool_size"] += entry["candidate_pool"]["superpool_size"]
        totals["novel_chunk_count"] += entry["novel_chunk_count"]
        totals["novel_supporting_chunk_count"] += entry["novel_supporting_chunk_count"]
        totals["aspects_only_coverable_by_novel_chunks"] += len(
            entry["aspects_only_coverable_by_novel_chunks"]
        )
        totals["oracle_top5_covered"] += entry["oracle_top5"]["covered_count"]
        totals["oracle_base_top5_covered"] += entry["oracle_base_top5"]["covered_count"]
        totals["superpool_recall"] += entry["superpool_recall"]
        totals["base_union_recall"] += entry["base_union_recall"]
    totals["required_total"] = oracle["totals"]["required_total"]
    totals["novel_supporting_rate"] = (
        totals["novel_supporting_chunk_count"] / totals["novel_chunk_count"]
        if totals["novel_chunk_count"]
        else None
    )
    return {
        "version": "router_v2_candidate_pool_analysis",
        "note": (
            "candidate pools are frozen V1 FIXED_DECOMPOSE lexical Top20 + semantic Top20 unions "
            "per stream; truth-based counts are analysis-only"
        ),
        "totals": totals,
        "cases": cases,
    }


def evidence_items_for(context, chunk_ids) -> list[dict[str, Any]]:
    items = []
    for chunk_id in chunk_ids:
        chunk = context.chunks[chunk_id]
        items.append(
            {
                "chunk_id": chunk_id,
                "title": chunk["title"],
                "heading_path": list(chunk["heading_path"]),
                "text": chunk["text"],
            }
        )
    return items


def useful_exploratory(selection_ids, shaped, direct_shaped) -> dict[str, Any]:
    direct_supported = set(direct_shaped["supported_aspect_ids"]) if direct_shaped else set()
    direct_ids = set(direct_shaped["evidence_ids"]) if direct_shaped else set()
    aspects = shaped["aspects"]
    labels = {chunk_id: chr(65 + index) for index, chunk_id in enumerate(shaped["evidence_ids"])}
    exploratory = [chunk_id for chunk_id in selection_ids if chunk_id not in direct_ids]
    useful = []
    for chunk_id in exploratory:
        label = labels[chunk_id]
        chunk_supported = {
            aspect_id
            for aspect_id, item in aspects.items()
            if item["status"] == "SUPPORTED" and label in item["supporting_evidence_ids"]
        }
        if chunk_supported - direct_supported:
            useful.append(
                {"chunk_id": chunk_id, "new_aspects": sorted(chunk_supported - direct_supported)}
            )
    return {
        "exploratory_chunk_ids": exploratory,
        "useful_exploratory": useful,
        "useful_exploratory_count": len(useful),
        "exploratory_chunk_count": len(exploratory),
        "exploration_efficiency": (len(useful) / len(exploratory)) if exploratory else None,
    }


def base_preservation(shaped, direct_shaped) -> dict[str, Any]:
    if not direct_shaped:
        return {"useful_base_chunk_count": 0, "preserved": [], "preservation_rate": None,
                "displaced_query": False}
    useful_base = list(direct_shaped["useful_chunk_ids"])
    selected = set(shaped["evidence_ids"])
    preserved = [chunk_id for chunk_id in useful_base if chunk_id in selected]
    return {
        "useful_base_chunk_count": len(useful_base),
        "preserved": preserved,
        "preservation_rate": (len(preserved) / len(useful_base)) if useful_base else None,
        "displaced_query": len(preserved) < len(useful_base),
    }


def derive_case_metrics(selection_ids, shaped, direct_shaped, oracle_shaped) -> dict[str, Any]:
    direct_supported = set(direct_shaped["supported_aspect_ids"]) if direct_shaped else set()
    supported = set(shaped["supported_aspect_ids"])
    exploration = useful_exploratory(selection_ids, shaped, direct_shaped)
    preservation = base_preservation(shaped, direct_shaped)
    return {
        "evidence_ids": list(selection_ids),
        "evidence_required_recall": shaped["evidence_required_recall"],
        "evidence_required_complete": shaped["evidence_required_complete"],
        "supported_count": shaped["supported_count"],
        "required_total": shaped["required_total"],
        "supported_aspect_ids": shaped["supported_aspect_ids"],
        "required_context_precision": shaped["required_context_precision"],
        "non_required_chunk_count": shaped["non_required_chunk_count"],
        "useful_chunk_ids": shaped["useful_chunk_ids"],
        "new_required_aspects_gained": sorted(supported - direct_supported),
        "required_aspects_lost": sorted(direct_supported - supported),
        "net_required_aspect_delta": len(supported) - len(direct_supported),
        "exploratory_chunks_selected": exploration["exploratory_chunk_count"],
        "useful_exploratory_chunks": exploration["useful_exploratory_count"],
        "exploration_efficiency": exploration["exploration_efficiency"],
        "useful_base_chunks_preserved": len(preservation["preserved"]),
        "useful_base_chunk_count": preservation["useful_base_chunk_count"],
        "useful_base_preservation_rate": preservation["preservation_rate"],
        "displaced": preservation["displaced_query"],
        "oracle_supported_count": oracle_shaped["supported_count"] if oracle_shaped else None,
        "oracle_gap": (oracle_shaped["supported_count"] - shaped["supported_count"])
        if oracle_shaped
        else None,
        "direct_supported_count": len(direct_supported),
        "below_direct": len(supported) < len(direct_supported),
        "reaches_oracle": bool(
            oracle_shaped is not None and len(supported) >= oracle_shaped["supported_count"]
        ),
    }


def instance_selection_ids(
    policy_id: str,
    selections: Mapping[str, Any],
    oracle: Mapping[str, Any],
) -> dict[str, list[str]]:
    if policy_id == "ORACLE_BASE_TOP5":
        return {
            case_id: list(entry["oracle_base_top5"]["ids"])
            for case_id, entry in oracle["cases"].items()
        }
    if policy_id == "ORACLE_TOP5":
        return {
            case_id: list(entry["oracle_top5"]["ids"])
            for case_id, entry in oracle["cases"].items()
        }
    return {
        case_id: list(record["ids"]) for case_id, record in selections[policy_id]["cases"].items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-new-calls", type=int, default=0,
                        help="stop after N new judge calls (0 = no limit)")
    parser.add_argument("--skip-judge", action="store_true",
                        help="only rebuild selections, candidate pool analysis and oracle bounds")
    args = parser.parse_args()

    started_at = time.perf_counter()
    config = load_json(CONFIG_PATH)
    verify_frozen_inputs(config)
    print(f"config verified: {config['study_version']}", flush=True)

    inputs = load_frozen_inputs()
    pre_contexts = pre_contexts_from_raw(inputs["raw"])
    local_scores, meter = compute_or_load_local_scores(pre_contexts)
    print(
        f"local reranker meter: calls={meter.get('calls', 'cached')} "
        f"pairs={meter.get('pairs', '')}",
        flush=True,
    )
    contexts = build_contexts(local_scores=local_scores)
    context_by_id = {context.case_id: context for context in contexts}

    selections = build_policy_selections(contexts)
    selection_payload = {
        "version": "router_v2_policy_selections",
        "budget": EVIDENCE_BUDGET,
        "policies": {
            policy_id: {
                "policy_id": policy_id,
                "family": entry["family"],
                "role": entry["role"],
                "cases": {
                    case_id: {
                        key: value for key, value in record.items() if key != "pulls"
                    }
                    for case_id, record in entry["cases"].items()
                },
            }
            for policy_id, entry in selections.items()
        },
        "provenance": {
            context.case_id: provenance_for(context, context.superpool_ids) for context in contexts
        },
    }
    write_json(SELECTIONS_PATH, selection_payload)
    print(f"selections written: {len(selections)} policy instances", flush=True)

    oracle = compute_oracle_bounds(contexts)
    write_json(ORACLE_PATH, oracle)
    pool = candidate_pool_analysis(contexts, oracle)
    write_json(CANDIDATE_POOL_PATH, pool)
    print(
        f"oracle totals: superpool recall {oracle['totals']['superpool_recall']}/"
        f"{oracle['totals']['required_total']}, base-union recall "
        f"{oracle['totals']['base_union_recall']}, ORACLE_TOP5 "
        f"{oracle['totals']['oracle_top5']}, ORACLE_BASE_TOP5 "
        f"{oracle['totals']['oracle_base_top5']}",
        flush=True,
    )
    if args.skip_judge:
        print("skip-judge set; stopping after local artifacts", flush=True)
        return 0

    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

    llm_config = LLMConfig.from_env(PROJECT_ROOT / ".env")
    client = OpenAIChatCompletionsClient(llm_config)
    new_cache = load_json(EVIDENCE_CACHE_PATH) if EVIDENCE_CACHE_PATH.exists() else {}
    v1_1_cache = load_json(V1_1_EVIDENCE_CACHE) if V1_1_EVIDENCE_CACHE.exists() else {}
    usage: dict[str, float] = {
        "new_calls": 0, "cache_hits": 0, "input_tokens": 0, "output_tokens": 0,
        "latency_seconds": 0.0,
    }

    ordered_ids = (
        ["DIRECT_TOP5", "ROUND_ROBIN", "GLOBAL_BASE_RERANK"]
        + sorted([pid for pid in selections if pid.startswith("MMR_")])
        + sorted([pid for pid in selections if pid.startswith("EACL_")])
        + ["ORACLE_BASE_TOP5", "ORACLE_TOP5"]
    )

    shaped_store: dict[str, dict[str, Any]] = {pid: {} for pid in ordered_ids}
    stop = False
    for policy_id in ordered_ids:
        ids_map = instance_selection_ids(policy_id, selections, oracle)
        for case_id in [case["case_id"] for case in inputs["raw"]["cases"]]:
            ids = ids_map.get(case_id)
            if not ids:
                shaped_store[policy_id][case_id] = None
                continue
            context = context_by_id[case_id]
            aspects = [
                {"aspect_id": aspect.aspect_id, "statement": aspect.statement}
                for aspect in context.aspects
            ]
            items = evidence_items_for(context, ids)
            result = judge_evidence_selection(
                case_id=case_id,
                query=context.raw_query,
                aspects=aspects,
                evidence=items,
                client=client,
                model=llm_config.model,
                new_cache=new_cache,
                v1_1_cache=v1_1_cache,
                usage=usage,
            )
            status = result.pop("status")
            source = result.pop("cache_source", None)
            result.pop("judge_key", None)
            if status != "judged":
                shaped_store[policy_id][case_id] = None
                print(f"judge-error {policy_id} {case_id}", flush=True)
            else:
                shaped_store[policy_id][case_id] = shape_evidence_judgment(
                    ids, result, context.required_total
                )
                print(f"judged {policy_id} {case_id} [{source}]", flush=True)
            if args.max_new_calls and usage["new_calls"] >= args.max_new_calls:
                stop = True
                break
        if stop:
            print(
                f"stopping after {usage['new_calls']} new judge calls; rerun to continue "
                "(no partial evidence results written)",
                flush=True,
            )
            return 0

    missing = [
        f"{policy_id}:{case_id}"
        for policy_id in ordered_ids
        for case_id in [case["case_id"] for case in inputs["raw"]["cases"]]
        if shaped_store[policy_id].get(case_id) is None
    ]
    if missing:
        print(
            f"evidence judging incomplete ({len(missing)} missing, first: {missing[:5]}); "
            "rerun to continue",
            flush=True,
        )
        return 0

    instance_results: dict[str, Any] = {}
    direct_by_case = shaped_store["DIRECT_TOP5"]
    oracle_by_case = shaped_store["ORACLE_TOP5"]
    for policy_id in ordered_ids:
        entry = selections.get(policy_id)
        if entry is None:
            variant = policy_id if policy_id.startswith("ORACLE") else None
            seed = None
            family = "oracle"
            role = "oracle"
        else:
            family = entry["family"]
            role = entry["role"]
            variant = None
            seed = None
            if policy_id.startswith("EACL_"):
                record = next(iter(entry["cases"].values()))
                variant = record.get("variant")
                seed = record.get("seed")
        cases_out: dict[str, Any] = {}
        ids_map = instance_selection_ids(policy_id, selections, oracle)
        for case_id, ids in ids_map.items():
            shaped = shaped_store[policy_id].get(case_id)
            if shaped is None:
                cases_out[case_id] = {"status": "judge_error"}
                continue
            cases_out[case_id] = {
                "status": "judged",
                "evidence": shaped,
                "metrics": derive_case_metrics(
                    ids, shaped, direct_by_case.get(case_id), oracle_by_case.get(case_id)
                ),
            }
        instance_results[policy_id] = {
            "policy_id": policy_id,
            "family": family,
            "role": role,
            "variant": variant,
            "seed": seed,
            "cases": cases_out,
        }
        print(f"assembled {policy_id}", flush=True)

    evidence_results = {
        "version": "router_v2_evidence_policy_results",
        "budget": EVIDENCE_BUDGET,
        "judge_protocol": "frozen Router V1.1 blind evidence-aspect judge (same prompt, schema, model)",
        "judge_model": llm_config.model,
        "runtime_policy_instances": [
            pid for pid in instance_results if instance_results[pid]["role"] == "runtime"
        ],
        "oracle_policy_instances": [
            pid for pid in instance_results if instance_results[pid]["role"] != "runtime"
        ],
        "instances": instance_results,
        "cost": {
            "study_cache_entries": len(new_cache),
            "new_calls_this_run": usage["new_calls"],
            "cache_hits_this_run": usage["cache_hits"],
            "input_tokens_this_run": usage["input_tokens"],
            "output_tokens_this_run": usage["output_tokens"],
            "judge_latency_seconds_this_run": round(usage["latency_seconds"], 3),
            "local_reranker_meter": meter,
            "wall_clock_seconds_this_run": round(time.perf_counter() - started_at, 3),
        },
    }
    write_json(EVIDENCE_RESULTS_PATH, evidence_results)
    print(f"evidence results written to {EVIDENCE_RESULTS_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
