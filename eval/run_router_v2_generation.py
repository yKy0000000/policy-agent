"""Router V2 selection study - stage 2: downstream generation and answer evaluation.

Uses the frozen grounded generator and the frozen blind answer judge on the
evidence sets selected by the predeclared generation-stage rule:
DIRECT_TOP5, ROUND_ROBIN, GLOBAL_BASE_RERANK, the best MMR representative, the
best EACL bandit representative, and the analysis-only ORACLE_TOP5 upper bound.

Resumable: generation and judge caches are written immediately after each call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.router_v2_study_lib import (  # noqa: E402
    BANDIT_REPRESENTATIVE_SEED,
    CONFIG_PATH,
    EVIDENCE_BUDGET,
    STUDY_DIR,
    load_json,
    write_json,
)

EVIDENCE_RESULTS_PATH = STUDY_DIR / "evidence_policy_results.json"
GENERATION_RESULTS_PATH = STUDY_DIR / "generation_results.json"
ANSWER_EVAL_PATH = STUDY_DIR / "answer_eval.json"
GENERATION_CACHE_PATH = STUDY_DIR / "generation_cache.json"
ANSWER_JUDGE_CACHE_PATH = STUDY_DIR / "answer_judge_cache.json"
ANSWER_JUDGE_FAILURES_PATH = STUDY_DIR / "answer_judge_failures.json"
COST_LEDGER_PATH = STUDY_DIR / "cost_ledger.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Generation-stage policy selection (predeclared rule)
# ---------------------------------------------------------------------------


def case_metric(instance: Mapping[str, Any], case_id: str, field: str) -> Any:
    case = instance["cases"].get(case_id) or {}
    metrics = case.get("metrics") or {}
    return metrics.get(field)


def pooled_metrics(instances: Mapping[str, Any], policy_ids: Sequence[str]) -> dict[str, Any]:
    supported = 0
    required = 0
    complete = 0
    precision_values: list[float] = []
    displaced = 0
    for policy_id in policy_ids:
        instance = instances[policy_id]
        for case in instance["cases"].values():
            if case.get("status") != "judged":
                continue
            supported += case["metrics"]["supported_count"]
            required += case["metrics"]["required_total"]
            complete += int(case["metrics"]["evidence_required_complete"])
            precision_values.append(case["metrics"]["required_context_precision"])
            displaced += int(case["metrics"]["displaced"])
    return {
        "supported": supported,
        "required": required,
        "recall": supported / required if required else None,
        "complete": complete,
        "precision": sum(precision_values) / len(precision_values) if precision_values else None,
        "displaced": displaced,
        "instances": list(policy_ids),
        "cases_evaluated": sum(
            len([c for c in instances[p]["cases"].values() if c.get("status") == "judged"])
            for p in policy_ids
        ),
    }


def select_generation_policies(evidence: Mapping[str, Any]) -> dict[str, Any]:
    instances = evidence["instances"]
    rr = pooled_metrics(instances, ["ROUND_ROBIN"])
    mmr_ids = sorted(pid for pid in instances if pid.startswith("MMR_"))
    bandit_variants = sorted(
        {
            instances[pid]["variant"] or pid
            for pid in instances
            if pid.startswith("EACL_")
        }
    )
    bandit_by_variant: dict[str, list[str]] = {
        variant: sorted(pid for pid in instances if (instances[pid]["variant"] or pid) == variant)
        for variant in bandit_variants
    }

    families: dict[str, Any] = {
        "mmr": {
            "members": {pid: pooled_metrics(instances, [pid]) for pid in mmr_ids},
        },
        "bandit": {
            "members": {
                variant: pooled_metrics(instances, ids)
                for variant, ids in bandit_by_variant.items()
            },
        },
    }

    def dominated(member: Mapping[str, Any]) -> bool:
        return (
            member["recall"] <= rr["recall"]
            and member["precision"] <= rr["precision"]
            and member["displaced"] >= rr["displaced"]
        )

    def representative(members: Mapping[str, Any], order_key) -> str:
        ordered = sorted(
            members,
            key=lambda name: (
                -members[name]["recall"],
                -(members[name]["precision"] or 0.0),
                members[name]["displaced"],
                order_key(name),
            ),
        )
        return ordered[0]

    mmr_rep = representative(families["mmr"]["members"], lambda pid: float(pid.split("_")[1]))
    bandit_rep_variant = representative(
        families["bandit"]["members"], lambda name: bandit_variants.index(name)
    )
    bandit_rep_seed = BANDIT_REPRESENTATIVE_SEED
    bandit_rep_instance = f"{bandit_rep_variant}::seed{bandit_rep_seed}"

    mmr_dominated = all(dominated(member) for member in families["mmr"]["members"].values())
    bandit_dominated = all(dominated(member) for member in families["bandit"]["members"].values())

    generation_policy_ids = ["DIRECT_TOP5", "ROUND_ROBIN", "GLOBAL_BASE_RERANK"]
    if not mmr_dominated:
        generation_policy_ids.append(mmr_rep)
    if not bandit_dominated:
        generation_policy_ids.append(bandit_rep_instance)
    generation_policy_ids.append("ORACLE_TOP5")

    return {
        "round_robin_reference": rr,
        "families": families,
        "mmr_dominated": mmr_dominated,
        "bandit_dominated": bandit_dominated,
        "mmr_representative": mmr_rep,
        "bandit_representative": {
            "variant": bandit_rep_variant,
            "instance": bandit_rep_instance,
            "generation_seed": bandit_rep_seed,
        },
        "generation_policy_ids": generation_policy_ids,
    }


# ---------------------------------------------------------------------------
# Evidence reconstruction for generation
# ---------------------------------------------------------------------------


def load_case_evidence(raw: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for case in raw["cases"]:
        evidence_by_id: dict[str, dict[str, Any]] = {}
        for stream in case["arms"]["FIXED_DECOMPOSE"]["trace"]["streams"]:
            for item in stream["evidence"]:
                evidence_by_id[item["chunk_id"]] = dict(item)
        cases[case["case_id"]] = {
            "raw_query": case["raw_query"],
            "frozen_evidence": evidence_by_id,
            "frozen_direct_order": list(case["arms"]["FIXED_DIRECT"]["evidence_chunk_ids"]),
            "frozen_decompose_order": list(case["arms"]["FIXED_DECOMPOSE"]["evidence_chunk_ids"]),
        }
    return cases


def evidence_item_for_generation(
    chunk_id: str,
    chunk_records: Mapping[str, Mapping[str, Any]],
    frozen_evidence: Mapping[str, Mapping[str, Any]],
) -> Any:
    if chunk_id in frozen_evidence:
        item = dict(frozen_evidence[chunk_id])
        return SimpleNamespace(
            text=item["text"],
            title=item["title"],
            heading_path=tuple(item["heading_path"]),
            source_url=item["source_url"],
            source_path=item["source_path"],
            chunk_id=item["chunk_id"],
        )
    chunk = chunk_records[chunk_id]
    return SimpleNamespace(
        text=chunk["text"],
        title=chunk["title"],
        heading_path=tuple(chunk["heading_path"]),
        source_url=chunk["source_url"],
        source_path=chunk["source_path"],
        chunk_id=chunk_id,
    )


def evidence_dict_for_judge(item: Any) -> dict[str, Any]:
    return {
        "text": item.text,
        "title": item.title,
        "heading_path": list(item.heading_path),
        "source_url": item.source_url,
        "source_path": item.source_path,
        "chunk_id": item.chunk_id,
    }


# ---------------------------------------------------------------------------
# Answer evaluation (frozen blind judge protocol)
# ---------------------------------------------------------------------------


def judge_answers_case(
    case_id: str,
    query: str,
    facts: list[dict[str, str]],
    answers: Mapping[str, dict[str, Any]],
    client: Any,
    model: str,
    cache: dict[str, Any],
    failures: dict[str, Any],
    usage: dict[str, float],
) -> dict[str, dict[str, Any]]:
    from eval.run_answer_eval import (
        V3_JUDGE_MAX_TOKENS,
        V3_JUDGE_VERSION,
        _judge_messages,
        _parse_judge,
    )
    from eval.run_router_v1_eval import build_sources, _shape_judgment

    ordered = sorted(answers, key=lambda policy_id: sha256_text(f"{case_id}:{policy_id}"))
    label_to_policy = {chr(65 + index): policy_id for index, policy_id in enumerate(ordered)}

    def build_labeled(subset: Mapping[str, str]) -> dict[str, dict[str, Any]]:
        return {
            label: {
                "generation": {"answer": answers[policy_id]["answer"]},
                "sources": build_sources(answers[policy_id]["evidence"]),
            }
            for label, policy_id in subset.items()
        }

    def call(subset: Mapping[str, str]) -> dict[str, Any]:
        messages = _judge_messages(
            {"query": query, "facts": facts}, build_labeled(subset)
        )
        key = stable_hash(
            {
                "case_id": case_id,
                "policy_labels": subset,
                "messages": messages,
                "model": model,
                "judge_version": V3_JUDGE_VERSION,
                "max_tokens": V3_JUDGE_MAX_TOKENS,
            }
        )
        entry = cache.get(key)
        if entry is None:
            started = time.perf_counter()
            raw, provider_usage = client.complete_with_usage(
                messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0
            )
            latency = time.perf_counter() - started
            try:
                parsed = _parse_judge(raw, set(subset), {fact["fact_id"] for fact in facts})
            except Exception as error:
                failures[key] = {
                    "case_id": case_id,
                    "labels": dict(subset),
                    "error": str(error),
                    "raw_response": raw,
                }
                write_json(ANSWER_JUDGE_FAILURES_PATH, failures)
                raise
            entry = {
                "parsed": parsed,
                "usage": {
                    "input_tokens": provider_usage.get("input_tokens"),
                    "output_tokens": provider_usage.get("output_tokens"),
                },
                "latency_seconds": latency,
            }
            cache[key] = entry
            usage["new_calls"] += 1
            usage["input_tokens"] += provider_usage.get("input_tokens") or 0
            usage["output_tokens"] += provider_usage.get("output_tokens") or 0
            usage["latency_seconds"] += latency
            write_json(ANSWER_JUDGE_CACHE_PATH, cache)
        else:
            usage["cache_hits"] += 1
        return entry["parsed"]

    try:
        parsed = call(label_to_policy)
    except Exception:
        parsed = {}
        for label, policy_id in label_to_policy.items():
            try:
                parsed.update(call({label: policy_id}))
            except Exception:
                continue
    return {
        policy_id: _shape_judgment(label, "", facts, parsed[label])
        for label, policy_id in label_to_policy.items()
        if label in parsed
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-new-generations", type=int, default=0)
    parser.add_argument("--skip-judge", action="store_true")
    args = parser.parse_args()

    started_at = time.perf_counter()
    config = load_json(CONFIG_PATH)
    evidence = load_json(EVIDENCE_RESULTS_PATH)
    plan = select_generation_policies(evidence)
    policy_ids = plan["generation_policy_ids"]
    print(f"generation policies: {policy_ids}", flush=True)
    print(
        "MMR dominated: {mmr} | bandit dominated: {bandit} | MMR rep: {mmr_rep} | "
        "bandit rep: {rep}".format(
            mmr=plan["mmr_dominated"], bandit=plan["bandit_dominated"],
            mmr_rep=plan["mmr_representative"],
            rep=plan["bandit_representative"]["instance"],
        ),
        flush=True,
    )

    from src.generator import GeneratedAnswerCache, generate_grounded_answer
    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    from src.router_v1_pipeline import ObservedChatClient
    from eval.router_v2_study_lib import load_chunk_records

    raw = load_json(PROJECT_ROOT / "eval" / "results" / "router_v1" / "raw" / "router_v1_raw_results.json")
    truth = load_json(PROJECT_ROOT / "eval" / "router_v1_required_aspects.json")
    truth_cases = {case["id"]: case for case in truth["cases"]}
    chunk_records = load_chunk_records()
    case_evidence = load_case_evidence(raw)

    llm_config = LLMConfig.from_env(PROJECT_ROOT / ".env")
    base_client = OpenAIChatCompletionsClient(llm_config)
    generation_cache = GeneratedAnswerCache(GENERATION_CACHE_PATH)

    selections = evidence["instances"]
    case_ids = list(case_evidence.keys())
    generation_records: dict[str, Any] = {}
    generation_usage = {
        "new_calls": 0, "cache_hits": 0, "input_tokens": 0, "output_tokens": 0, "latency_seconds": 0.0,
    }
    stop = False
    for policy_id in policy_ids:
        instance = selections[policy_id]
        cases_out: dict[str, Any] = {}
        for case_id in case_ids:
            case = instance["cases"].get(case_id) or {}
            if case.get("status") != "judged":
                cases_out[case_id] = {"status": "missing_evidence"}
                continue
            ids = case["metrics"]["evidence_ids"]
            frozen = case_evidence[case_id]["frozen_evidence"]
            items = [
                evidence_item_for_generation(chunk_id, chunk_records, frozen)
                for chunk_id in ids
            ]
            observed = ObservedChatClient(base_client)
            observed.stage = "generation"
            try:
                generated = generate_grounded_answer(
                    case_evidence[case_id]["raw_query"],
                    [],
                    items,
                    observed,
                    model=llm_config.model,
                    cache=generation_cache,
                )
                calls = observed.calls
                usage_tokens = {
                    "input_tokens": sum(call.input_tokens or 0 for call in calls),
                    "output_tokens": sum(call.output_tokens or 0 for call in calls),
                    "latency_seconds": sum(call.latency_seconds for call in calls),
                }
                if generated["response_source"] == "api":
                    generation_usage["new_calls"] += 1
                else:
                    generation_usage["cache_hits"] += 1
                generation_usage["input_tokens"] += usage_tokens["input_tokens"]
                generation_usage["output_tokens"] += usage_tokens["output_tokens"]
                generation_usage["latency_seconds"] += usage_tokens["latency_seconds"]
                cases_out[case_id] = {
                    "status": "generated",
                    "role": instance["role"],
                    "analysis_only_oracle": policy_id == "ORACLE_TOP5",
                    "evidence_ids": ids,
                    "evidence": [evidence_dict_for_judge(item) for item in items],
                    "answer": generated["answer"],
                    "citation_ids": generated["citation_ids"],
                    "citation_validation": generated["validation"],
                    "response_source": generated["response_source"],
                    "provider_usage": usage_tokens,
                    "execution_success": bool(generated["validation"].get("valid")),
                }
                print(
                    f"generated {policy_id} {case_id} [{generated['response_source']}]",
                    flush=True,
                )
            except Exception as error:
                cases_out[case_id] = {
                    "status": "generation_error",
                    "error": str(error),
                    "evidence_ids": ids,
                }
                print(f"generation-error {policy_id} {case_id}: {error}", flush=True)
            if args.max_new_generations and generation_usage["new_calls"] >= args.max_new_generations:
                stop = True
                break
        generation_records[policy_id] = {
            "policy_id": policy_id,
            "family": instance["family"],
            "role": instance["role"],
            "analysis_only_oracle": policy_id == "ORACLE_TOP5",
            "cases": cases_out,
        }
        if stop:
            break

    generation_payload = {
        "version": "router_v2_generation_results",
        "generation_policy_plan": plan,
        "generator": {
            "prompt_version": "grounded-policy-answer-v1",
            "max_tokens": 512,
            "temperature": 0.0,
            "model": llm_config.model,
        },
        "analysis_only_oracle_marking": "ORACLE_TOP5 outputs carry analysis_only_oracle=true",
        "policies": generation_records,
        "usage_this_run": generation_usage,
        "wall_clock_seconds": round(time.perf_counter() - started_at, 3),
    }
    ledger = load_json(COST_LEDGER_PATH) if COST_LEDGER_PATH.exists() else {
        "generation_calls": 0,
        "generation_input_tokens": 0,
        "generation_output_tokens": 0,
        "answer_judge_calls": 0,
        "answer_judge_input_tokens": 0,
        "answer_judge_output_tokens": 0,
    }
    ledger["generation_calls"] += generation_usage["new_calls"]
    ledger["generation_input_tokens"] += generation_usage["input_tokens"]
    ledger["generation_output_tokens"] += generation_usage["output_tokens"]
    write_json(COST_LEDGER_PATH, ledger)
    generation_payload["usage_cumulative"] = {
        "generation_calls": ledger["generation_calls"],
        "generation_input_tokens": ledger["generation_input_tokens"],
        "generation_output_tokens": ledger["generation_output_tokens"],
    }
    write_json(GENERATION_RESULTS_PATH, generation_payload)
    print(f"generation results written ({len(generation_records)} policies)", flush=True)
    if stop or args.skip_judge:
        print("stopping before answer judging; rerun to continue", flush=True)
        return 0

    # ------------------------------------------------------------------
    # Answer judging
    # ------------------------------------------------------------------
    answer_cache = load_json(ANSWER_JUDGE_CACHE_PATH) if ANSWER_JUDGE_CACHE_PATH.exists() else {}
    judge_failures = load_json(ANSWER_JUDGE_FAILURES_PATH) if ANSWER_JUDGE_FAILURES_PATH.exists() else {}
    judge_usage = {
        "new_calls": 0, "cache_hits": 0, "input_tokens": 0, "output_tokens": 0, "latency_seconds": 0.0,
    }
    answer_eval: dict[str, Any] = {
        "version": "router_v2_answer_eval",
        "judge_version": "broad-v3-answer-quality-v1",
        "judge_model": llm_config.model,
        "blind": {"labels": "hashed opaque labels per case", "policy_identity_exposed": False},
        "eligibility_rule": "same frozen router_v1 eligibility logic; citation validation + no incorrect facts + no disqualifying claim statuses",
        "cases": {},
    }
    from eval.run_router_v1_eval import eligibility  # noqa: E402

    case_entries: dict[str, list[dict[str, Any]]] = {policy_id: [] for policy_id in policy_ids}
    for case_id in case_ids:
        facts = [
            {"fact_id": aspect["aspect_id"], "fact": aspect["statement"]}
            for aspect in truth_cases[case_id]["required_aspects"]
        ]
        answers = {
            policy_id: generation_records[policy_id]["cases"][case_id]
            for policy_id in policy_ids
            if generation_records[policy_id]["cases"].get(case_id, {}).get("status") == "generated"
        }
        judged = {}
        if answers:
            judged = judge_answers_case(
                case_id, case_evidence[case_id]["raw_query"], facts, answers,
                base_client, llm_config.model, answer_cache, judge_failures, judge_usage,
            )
        case_eval: dict[str, Any] = {}
        for policy_id in policy_ids:
            record = generation_records[policy_id]["cases"].get(case_id) or {}
            verdict = judged.get(policy_id)
            entry: dict[str, Any] = {
                "status": "judged" if verdict else ("unavailable" if record.get("status") != "generated" else "judge_error"),
                "analysis_only_oracle": policy_id == "ORACLE_TOP5",
                "execution_success": record.get("execution_success"),
                "citation_validation": record.get("citation_validation"),
                "eligible": bool(verdict) and eligibility(record, verdict),
            }
            if verdict:
                entry.update(
                    {
                        "required_total": verdict["required_total"],
                        "required_covered": verdict["required_covered"],
                        "covered_ids": verdict["covered_ids"],
                        "missing_ids": verdict["missing_ids"],
                        "incorrect_ids": verdict["incorrect_ids"],
                        "query_required_complete": verdict["query_required_complete"],
                        "claim_counts": verdict["claim_counts"],
                        "claim_citation_counts": verdict["claim_citation_counts"],
                        "judge_label": verdict["judge_label"],
                    }
                )
            case_eval[policy_id] = entry
            case_entries[policy_id].append(entry)
        answer_eval["cases"][case_id] = case_eval
        print(f"answer-judged {case_id}", flush=True)

    aggregates: dict[str, Any] = {}
    for policy_id in policy_ids:
        entries = case_entries[policy_id]
        judged_entries = [entry for entry in entries if entry["status"] == "judged"]
        evidence_instance = selections[policy_id]
        utilization_num = 0
        utilization_den = 0
        for case_id in case_ids:
            evidence_case = evidence_instance["cases"].get(case_id) or {}
            if evidence_case.get("status") != "judged":
                continue
            supported = set(evidence_case["evidence"]["supported_aspect_ids"])
            entry = answer_eval["cases"][case_id][policy_id]
            if entry["status"] != "judged":
                continue
            covered = set(entry["covered_ids"])
            utilization_num += len(supported & covered)
            utilization_den += len(supported)
        aggregates[policy_id] = {
            "attempts": len(entries),
            "judged": len(judged_entries),
            "analysis_only_oracle": policy_id == "ORACLE_TOP5",
            "execution_success": sum(1 for entry in entries if entry["execution_success"]),
            "citation_valid": sum(
                1 for entry in entries if (entry.get("citation_validation") or {}).get("valid")
            ),
            "eligible": sum(1 for entry in entries if entry["eligible"]),
            "query_required_complete_cases": sum(
                1 for entry in judged_entries if entry["query_required_complete"]
            ),
            "required_covered_total": sum(entry["required_covered"] for entry in judged_entries),
            "required_total_total": sum(entry["required_total"] for entry in judged_entries),
            "context_utilization": (
                utilization_num / utilization_den if utilization_den else None
            ),
        }
    answer_eval["aggregate"] = aggregates
    answer_eval["judge_usage"] = judge_usage
    answer_eval["judge_usage_cumulative"] = {
        "calls": len(answer_cache),
        "input_tokens": sum(
            (entry.get("usage") or {}).get("input_tokens") or 0
            for entry in answer_cache.values()
        ),
        "output_tokens": sum(
            (entry.get("usage") or {}).get("output_tokens") or 0
            for entry in answer_cache.values()
        ),
    }
    answer_eval["judge_failures"] = {
        key: {field: value for field, value in entry.items() if field != "raw_response"}
        for key, entry in judge_failures.items()
    }
    write_json(ANSWER_EVAL_PATH, answer_eval)

    generation_payload["usage"] = generation_usage
    write_json(GENERATION_RESULTS_PATH, generation_payload)
    print(f"answer eval written to {ANSWER_EVAL_PATH}", flush=True)
    for policy_id in policy_ids:
        item = aggregates[policy_id]
        print(
            f"  {policy_id}: complete {item['query_required_complete_cases']}/"
            f"{item['judged']} covered {item['required_covered_total']}/"
            f"{item['required_total_total']} eligible {item['eligible']} util {item['context_utilization']}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
