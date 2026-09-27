"""Execute only the frozen Stage 1 generation owners; --check makes no provider calls.

No retry policy is frozen for generation. A started attempt without a validated
SUCCESS is treated as unknown completion and requires manual reconciliation.

This version adds one explicit, gated, one-shot manual reconciliation path for a
generation whose original attempt is an unobservable UNKNOWN_COMPLETION_STATE.
It is never triggered by --execute; it requires the dedicated CLI
--reconcile-generation-key with --confirm-manual-reconciliation. The original
UNKNOWN attempt is preserved permanently and a reconciliation can run at most once.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval import run_query_aware_stage1 as planner
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "eval/results/query_aware_stage1_dry_run.json"
FREEZE = ROOT / "eval/query_aware_stage1_live_reconciliation_freeze.json"
JOURNAL = ROOT / "eval/results/query_aware_stage1_live_journal.jsonl"
RESULTS = ROOT / "eval/results/query_aware_stage1_generation_results.json"
SUMMARY = ROOT / "eval/results/query_aware_stage1_generation_summary.md"
ORDINARY_STATUSES = {"ATTEMPT_STARTED", "SUCCESS", "FAILED_KNOWN_NOT_COMPLETED",
                     "UNKNOWN_COMPLETION_STATE"}
RECONCILIATION_STATUSES = {"MANUAL_RECONCILIATION_AUTHORIZED", "RECONCILIATION_ATTEMPT_STARTED",
                           "RECONCILIATION_SUCCESS", "RECONCILIATION_FAILED_KNOWN_NOT_COMPLETED",
                           "RECONCILIATION_UNKNOWN_COMPLETION_STATE"}
STATUSES = ORDINARY_STATUSES | RECONCILIATION_STATUSES
ORDINARY_TERMINAL = {"SUCCESS", "FAILED_KNOWN_NOT_COMPLETED", "UNKNOWN_COMPLETION_STATE"}
RECONCILIATION_TERMINAL = {"RECONCILIATION_SUCCESS", "RECONCILIATION_FAILED_KNOWN_NOT_COMPLETED",
                           "RECONCILIATION_UNKNOWN_COMPLETION_STATE"}
_TRANSITIONS = {
    "ATTEMPT_STARTED": set(ORDINARY_TERMINAL),
    "UNKNOWN_COMPLETION_STATE": {"MANUAL_RECONCILIATION_AUTHORIZED"},
    "MANUAL_RECONCILIATION_AUTHORIZED": {"RECONCILIATION_ATTEMPT_STARTED"},
    "RECONCILIATION_ATTEMPT_STARTED": set(RECONCILIATION_TERMINAL),
}
EXPECTED = {"case_arm_rows": 250, "exact_reuse_rows": 103,
            "unique_provider_generations_expected": 106}
PROVIDER = "openai-compatible-chat-completions"
RECONCILIATION_REASON = "manual reconciliation retry after unobservable UNKNOWN"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"required file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _price_hash(price_table: dict) -> str:
    return _hash_text(json.dumps(price_table, ensure_ascii=False,
                                 sort_keys=True, separators=(",", ":")))


def validate_source_freeze(root: Path = ROOT, freeze_path: Path = FREEZE) -> dict:
    frozen = _json(freeze_path)
    for relative, expected in frozen["source_hashes"].items():
        path = root / relative
        if not path.is_file() or planner.sha(path) != expected:
            raise ValueError(f"live source freeze mismatch: {relative}")
    if frozen["frozen_artifact_hashes"] != planner.check_hashes(root):
        raise ValueError("live freeze frozen-artifact mismatch")
    if (frozen["expected_unique_owners"] != EXPECTED["unique_provider_generations_expected"] or
        frozen["expected_final_rows"] != EXPECTED["case_arm_rows"] or
        frozen["expected_legacy_reuse"] != EXPECTED["exact_reuse_rows"]):
        raise ValueError("live freeze count mismatch")
    return frozen


def validate_plan(root: Path = ROOT, plan_path: Path = PLAN,
                  freeze: dict | None = None) -> tuple[dict, list[dict]]:
    current = planner.build_plan(root)
    saved = _json(plan_path)
    if saved != current:
        raise ValueError("saved Stage 1 plan differs from freshly validated frozen plan")
    if freeze is not None and planner.sha(plan_path) != freeze["source_hashes"]["eval/results/query_aware_stage1_dry_run.json"]:
        raise ValueError("dry-run plan hash mismatch")
    if freeze is not None and (
        freeze["provider"] != PROVIDER or
        freeze["generation_model"] != saved["frozen_integrity"]["generation_model"] or
        freeze["generation_prompt_sha256"] != saved["frozen_integrity"]["generation_prompt_sha256"] or
        freeze["generation_prompt_version"] != saved["frozen_integrity"]["generation_prompt_version"]
    ):
        raise ValueError("live freeze provider/model/prompt mismatch")
    for field, expected in EXPECTED.items():
        if saved["totals"].get(field) != expected:
            raise ValueError(f"Stage 1 plan invariant mismatch: {field}")
    for field in ("frozen_policy_mismatches", "selected_context_mismatches",
                  "generation_key_collisions", "context_hash_collisions",
                  "invalid_missing_provenance", "rewrite_live_expected"):
        if saved["totals"].get(field) != 0:
            raise ValueError(f"Stage 1 plan mismatch: {field}")
    rows = saved["cases"]
    if len(rows) != EXPECTED["case_arm_rows"]:
        raise ValueError("Stage 1 plan row count mismatch")
    owners = [row for row in rows if row["requires_provider_call"]]
    if len(owners) != EXPECTED["unique_provider_generations_expected"]:
        raise ValueError("unique generation owner count mismatch")
    owner_hashes = {row["canonical_input_hash"] for row in owners}
    if len(owner_hashes) != len(owners) or len({row["generation_key"] for row in owners}) != len(owners):
        raise ValueError("duplicate generation owner")
    for row in rows:
        if row["rewritten_query"] != row["original_query"] or row["rewrite_live_expected"] != 0:
            raise ValueError("unexpected rewrite in frozen plan")
        if row["generation_source"] == "reused" and row["requires_provider_call"]:
            raise ValueError("legacy reused row is marked as provider owner")
        if row["generation_source"] == "new" and row["canonical_input_hash"] not in owner_hashes:
            raise ValueError("new generation has no frozen owner")
    return saved, owners


def _journal_identity(owner: dict) -> dict:
    return {"generation_key": owner["generation_key"],
            "owner_case_id": owner["case_id"], "owner_arm": owner["arm"],
            "canonical_input_hash": owner["canonical_input_hash"],
            "context_hash": owner["context_hash"],
            "generation_prompt_hash": owner["generation_prompt_hash"],
            "model": owner["generation_model"],
            "generation_config": owner["generation_config"],
            "selected_chunk_ids": owner["selected_chunk_ids"],
            "shared_arms": owner["shared_generation_arms"]}


def _validate_success_event(event: dict, owner: dict, key: str, status: str) -> None:
    if not isinstance(event.get("answer"), str) or not event["answer"].strip():
        raise ValueError(f"journal success missing answer: {key}")
    if event.get("answer_sha256") != _hash_text(event["answer"]):
        raise ValueError(f"journal answer hash mismatch: {key}")
    planner.validate_live_telemetry(event.get("telemetry", {}))
    telemetry = event["telemetry"]
    if (telemetry["model"] != owner["generation_model"] or
        telemetry["provider"] != PROVIDER or
        telemetry["cache_hit"] is not False or
        telemetry["error"] is not None or
        telemetry["retry_count"] != 0):
        raise ValueError(f"journal success provider telemetry mismatch: {key}")
    if event.get("live_request_hash") != owner["canonical_input_hash"]:
        raise ValueError(f"journal request identity mismatch: {key}")
    if not isinstance(event.get("validation"), dict) or not isinstance(event.get("citations"), list):
        raise ValueError(f"journal success missing validation: {key}")
    if not isinstance(event.get("price_table_sha256"), str) or len(event["price_table_sha256"]) != 64:
        raise ValueError(f"journal success missing price provenance: {key}")
    if status == "RECONCILIATION_SUCCESS":
        if not isinstance(event.get("reconciliation_reason"), str) or not event["reconciliation_reason"].strip():
            raise ValueError(f"journal reconciliation success missing reason: {key}")


def read_journal(path: Path, owners: list[dict]) -> dict:
    owner_by_key = {row["generation_key"]: row for row in owners}
    latest: dict[str, dict] = {}
    original_unknown: dict[str, dict] = {}
    if not path.exists():
        return {"completed": {}, "reconciled": {}, "unknown": {}, "known_failed": {},
                "pending": owner_by_key, "event_count": 0, "price_table_sha256": None}
    count = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid journal JSON at line {number}") from error
        if not isinstance(event, dict) or event.get("status") not in STATUSES:
            raise ValueError(f"invalid journal state at line {number}")
        owner = owner_by_key.get(event.get("generation_key"))
        if owner is None:
            raise ValueError(f"journal contains non-owner key at line {number}")
        for field, expected in _journal_identity(owner).items():
            if event.get(field) != expected:
                raise ValueError(f"journal identity mismatch at line {number}: {field}")
        key, status = event["generation_key"], event["status"]
        expected_attempt = 2 if status in RECONCILIATION_STATUSES else 1
        if event.get("attempt") != expected_attempt or event.get("retry_count") != 0:
            raise ValueError(f"journal attempt semantics mismatch: {key}")
        prior = latest.get(key)
        if prior is None:
            if status != "ATTEMPT_STARTED":
                raise ValueError(f"journal terminal state without started attempt: {key}")
        elif status not in _TRANSITIONS.get(prior["status"], set()):
            prior_status = prior["status"]
            if prior_status in {"SUCCESS", "FAILED_KNOWN_NOT_COMPLETED"} or prior_status in RECONCILIATION_TERMINAL:
                raise ValueError(f"journal attempted terminal generation again: {key}")
            if prior_status == "UNKNOWN_COMPLETION_STATE":
                if status in RECONCILIATION_STATUSES:
                    raise ValueError(f"journal reconciliation without authorization: {key}")
                raise ValueError(f"journal ordinary event after UNKNOWN rejected: {key}")
            raise ValueError(f"journal invalid transition: {key}")
        if status == "UNKNOWN_COMPLETION_STATE":
            original_unknown[key] = event
        if status in {"SUCCESS", "RECONCILIATION_SUCCESS"}:
            _validate_success_event(event, owner, key, status)
        if status == "MANUAL_RECONCILIATION_AUTHORIZED":
            if not isinstance(event.get("reconciliation_reason"), str) or not event["reconciliation_reason"].strip():
                raise ValueError(f"journal reconciliation authorization missing reason: {key}")
            if event.get("provider_called") not in (False, None):
                raise ValueError(f"journal reconciliation authorization must not call provider: {key}")
        if status == "RECONCILIATION_ATTEMPT_STARTED":
            if event.get("provider_called") is not True:
                raise ValueError(f"journal reconciliation attempt must record provider_called: {key}")
            if event.get("live_request_hash") != owner["canonical_input_hash"]:
                raise ValueError(f"journal reconciliation request identity mismatch: {key}")
        if status in {"RECONCILIATION_FAILED_KNOWN_NOT_COMPLETED",
                      "RECONCILIATION_UNKNOWN_COMPLETION_STATE"}:
            if not isinstance(event.get("error"), str) or not event["error"].strip():
                raise ValueError(f"journal reconciliation failure missing error: {key}")
        latest[key] = event
        count += 1
    completed = {k: v for k, v in latest.items() if v["status"] in {"SUCCESS", "RECONCILIATION_SUCCESS"}}
    reconciled = {k: {"reconciliation": v, "original_unknown": original_unknown.get(k)}
                  for k, v in completed.items() if v["status"] == "RECONCILIATION_SUCCESS"}
    unknown = {k: v for k, v in latest.items() if v["status"] in
               {"ATTEMPT_STARTED", "UNKNOWN_COMPLETION_STATE", "MANUAL_RECONCILIATION_AUTHORIZED",
                "RECONCILIATION_ATTEMPT_STARTED", "RECONCILIATION_UNKNOWN_COMPLETION_STATE"}}
    known_failed = {k: v for k, v in latest.items() if v["status"] in
                    {"FAILED_KNOWN_NOT_COMPLETED", "RECONCILIATION_FAILED_KNOWN_NOT_COMPLETED"}}
    pending = {k: v for k, v in owner_by_key.items() if k not in latest}
    price_hashes = {v["price_table_sha256"] for v in latest.values()
                    if v["status"] in {"SUCCESS", "RECONCILIATION_SUCCESS"}}
    if len(price_hashes) > 1:
        raise ValueError("completed journal uses inconsistent price tables")
    return {"completed": completed, "reconciled": reconciled, "unknown": unknown,
            "known_failed": known_failed, "pending": pending, "event_count": count,
            "price_table_sha256": next(iter(price_hashes)) if price_hashes else None}


def append_journal_many(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n" for event in events)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(lines)
        stream.flush()
        os.fsync(stream.fileno())


def append_journal(path: Path, event: dict) -> None:
    append_journal_many(path, [event])


def audit(root: Path = ROOT, *, plan_path: Path = PLAN, freeze_path: Path = FREEZE,
          journal_path: Path = JOURNAL) -> tuple[dict, list[dict], dict, dict]:
    freeze = validate_source_freeze(root, freeze_path)
    plan, owners = validate_plan(root, plan_path, freeze)
    journal = read_journal(journal_path, owners)
    info = {"frozen_hashes": plan["frozen_integrity"]["artifact_hashes"],
            "planned_unique_owners": len(owners),
            "completed": len(journal["completed"]),
            "reconciled": len(journal["reconciled"]),
            "pending": len(journal["pending"]),
            "unknown": len(journal["unknown"]), "known_failed": len(journal["known_failed"]),
            "reusable_legacy_rows": plan["totals"]["exact_reuse_rows"],
            "expected_final_rows": plan["totals"]["case_arm_rows"],
            "provider": PROVIDER, "model": plan["frozen_integrity"]["generation_model"],
            "journal_price_table_sha256": journal["price_table_sha256"],
            "journal_path": str(journal_path), "result_path": str(root / RESULTS.relative_to(ROOT)),
            "summary_path": str(root / SUMMARY.relative_to(ROOT)),
            "mismatches": 0}
    return plan, owners, journal, info


def build_request(owner: dict, plan: dict, root: Path = ROOT) -> dict:
    """Rebuild only for comparison; any difference from the frozen plan blocks the call."""
    if not owner["requires_provider_call"] or owner["generation_source"] != "new":
        raise ValueError("provider call requested for non-owner")
    if owner["rewritten_query"] != owner["original_query"] or owner["rewrite_live_expected"] != 0:
        raise ValueError("unexpected rewrite in frozen owner")
    policy = next((item for item in _json(root / "eval/query_aware_arms_v1.json")["arms"]
                   if item["policy_id"] == owner["policy_id"]), None)
    if policy is None:
        raise ValueError("unknown frozen policy")
    chunks = {item["chunk_id"]: item for item in _json(root / "cache/policy_index.json")["chunks"]}
    identity = planner.canonical_identity(owner["case_id"], owner["original_query"],
        owner["rewritten_query"], [chunks[cid] for cid in owner["selected_chunk_ids"]],
        owner["generation_model"], policy, plan["frozen_integrity"]["artifact_hashes"])
    comparisons = {"context_hash": identity["context_hash"],
                   "serialized_context": identity["canonical"]["serialized_context"],
                   "generation_prompt_hash": identity["prompt_hash"],
                   "generation_key": identity["generation_key"],
                   "generation_key_fields": identity["generation_key_fields"],
                   "canonical_input_hash": planner.provider_input_hash(identity["canonical"]),
                   "generation_config": identity["canonical"]["generation_config"]}
    for field, actual in comparisons.items():
        if owner.get(field) != actual:
            raise ValueError(f"live request identity mismatch: {field}")
    return {"messages": identity["canonical"]["messages"],
            "model": owner["generation_model"],
            "temperature": owner["generation_config"]["temperature"],
            "max_tokens": owner["generation_config"]["max_tokens"],
            "live_request_hash": comparisons["canonical_input_hash"]}


def _live_telemetry(owner: dict, answer_metadata: dict, latency: float, price_table: dict) -> dict:
    if not isinstance(answer_metadata, dict):
        raise ValueError("provider metadata unavailable")
    tokens = (answer_metadata.get("input_tokens"), answer_metadata.get("output_tokens"))
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in tokens):
        raise ValueError("provider token usage unavailable after generation")
    return {"provider": PROVIDER, "model": owner["generation_model"],
            "input_tokens": tokens[0], "output_tokens": tokens[1],
            "latency_seconds": latency, "cache_hit": False, "error": None,
            "retry_count": 0, "request_id": answer_metadata.get("request_id"),
            "response_id": answer_metadata.get("response_id"),
            "cache_metadata": answer_metadata.get("cache_metadata"),
            "estimated_cost": planner.estimate_cost(tokens[0], tokens[1], price_table)}


def execute_owner(owner: dict, plan: dict, client, journal_path: Path,
                  price_table: dict, *, root: Path = ROOT) -> dict:
    """Make one provider attempt. Call only from a locked, audited execution loop."""
    planned = {row["generation_key"]: row for row in plan["cases"] if row["requires_provider_call"]}
    if len(planned) != EXPECTED["unique_provider_generations_expected"] or planned.get(owner.get("generation_key")) != owner:
        raise ValueError("owner is outside the frozen 106 generation plan")
    state = read_journal(journal_path, list(planned.values()))
    key = owner["generation_key"]
    if key not in state["pending"]:
        raise ValueError("generation already attempted; automatic retry prohibited")
    base = {**_journal_identity(owner), "attempt": 1, "retry_count": 0,
            "price_table_sha256": _price_hash(price_table)}
    try:
        request = build_request(owner, plan, root)
    except Exception as error:
        append_journal_many(journal_path, [
            {**base, "status": "ATTEMPT_STARTED", "timestamp": _now(), "provider_called": False},
            {**base, "status": "FAILED_KNOWN_NOT_COMPLETED", "timestamp": _now(),
             "provider_called": False, "error": f"{type(error).__name__}: {error}"}])
        raise
    append_journal(journal_path, {**base, "status": "ATTEMPT_STARTED", "timestamp": _now(),
                                  "live_request_hash": request["live_request_hash"],
                                  "provider_called": True})
    started = perf_counter()
    try:
        answer, metadata = client.complete_with_metadata(request["messages"],
            max_tokens=request["max_tokens"], temperature=request["temperature"])
        latency = perf_counter() - started
        telemetry = _live_telemetry(owner, metadata, latency, price_table)
        result = planner.record_live_result(owner, answer,
            {"invoked": False, "cache_hit": False, "rewritten_query": owner["original_query"]},
            telemetry, wall_seconds=latency)
        event = {**base, "status": "SUCCESS", "timestamp": _now(),
            "live_request_hash": request["live_request_hash"], "provider_called": True,
            "answer": result["answer"], "answer_sha256": _hash_text(result["answer"]),
            "citations": result["citations"],
            "validation": result["validation"], "telemetry": telemetry}
        append_journal(journal_path, event)
        return event
    except Exception as error:
        append_journal(journal_path, {**base, "status": "UNKNOWN_COMPLETION_STATE",
            "timestamp": _now(), "live_request_hash": request["live_request_hash"],
            "provider_called": True, "latency_seconds": perf_counter() - started,
            "error": f"{type(error).__name__}: {error}"})
        raise RuntimeError(f"generation completion uncertain for {key}; manual reconciliation required") from error


def reconcile_owner(owner: dict, plan: dict, client, journal_path: Path, price_table: dict,
                    *, reason: str = RECONCILIATION_REASON, root: Path = ROOT) -> dict:
    """One authorized reconciliation attempt for an unobservable UNKNOWN generation.

    Never called by --execute. Enforces: latest state is UNKNOWN_COMPLETION_STATE,
    no prior reconciliation, identical frozen canonical identity, and at most one
    reconciliation attempt. The original UNKNOWN events are never modified.
    """
    planned = {row["generation_key"]: row for row in plan["cases"] if row["requires_provider_call"]}
    if len(planned) != EXPECTED["unique_provider_generations_expected"] or planned.get(owner.get("generation_key")) != owner:
        raise ValueError("owner is outside the frozen 106 generation plan")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("manual reconciliation requires a reason")
    state = read_journal(journal_path, list(planned.values()))
    key = owner["generation_key"]
    current = state["unknown"].get(key)
    if current is None or current["status"] != "UNKNOWN_COMPLETION_STATE":
        raise ValueError("generation is not an eligible unreconciled UNKNOWN_COMPLETION_STATE")
    if key in state["completed"] or key in state["reconciled"]:
        raise ValueError("generation already resolved")
    request = build_request(owner, plan, root)
    base = {**_journal_identity(owner), "attempt": 2, "retry_count": 0,
            "price_table_sha256": _price_hash(price_table),
            "reconciliation_reason": reason,
            "original_attempt_status": "UNKNOWN_COMPLETION_STATE"}
    append_journal_many(journal_path, [
        {**base, "status": "MANUAL_RECONCILIATION_AUTHORIZED", "timestamp": _now(),
         "authorized": True, "provider_called": False},
        {**base, "status": "RECONCILIATION_ATTEMPT_STARTED", "timestamp": _now(),
         "live_request_hash": request["live_request_hash"], "provider_called": True}])
    started = perf_counter()
    try:
        answer, metadata = client.complete_with_metadata(request["messages"],
            max_tokens=request["max_tokens"], temperature=request["temperature"])
        latency = perf_counter() - started
        telemetry = _live_telemetry(owner, metadata, latency, price_table)
        result = planner.record_live_result(owner, answer,
            {"invoked": False, "cache_hit": False, "rewritten_query": owner["original_query"]},
            telemetry, wall_seconds=latency)
        event = {**base, "status": "RECONCILIATION_SUCCESS", "timestamp": _now(),
            "live_request_hash": request["live_request_hash"], "provider_called": True,
            "answer": result["answer"], "answer_sha256": _hash_text(result["answer"]),
            "citations": result["citations"],
            "validation": result["validation"], "telemetry": telemetry}
        append_journal(journal_path, event)
        return event
    except Exception as error:
        append_journal(journal_path, {**base, "status": "RECONCILIATION_UNKNOWN_COMPLETION_STATE",
            "timestamp": _now(), "live_request_hash": request["live_request_hash"],
            "provider_called": True, "latency_seconds": perf_counter() - started,
            "error": f"{type(error).__name__}: {error}"})
        raise RuntimeError(f"reconciliation completion uncertain for {key}; manual reconciliation required") from error


def _reconciliation_provenance(entry: dict) -> dict:
    original = entry.get("original_unknown") or {}
    reconciliation = entry.get("reconciliation") or {}
    telemetry = reconciliation.get("telemetry", {})
    return {"original_attempt_status": original.get("status", "UNKNOWN_COMPLETION_STATE"),
            "original_attempt_timestamp": original.get("timestamp"),
            "original_attempt_error": original.get("error"),
            "original_attempt_usage": "unknown/unmeasured",
            "original_completion_observed": False,
            "reconciliation_authorized_before_answer": True,
            "reconciliation_timestamp": reconciliation.get("timestamp"),
            "reconciliation_reason": reconciliation.get("reconciliation_reason"),
            "reconciliation_usage": {"input_tokens": telemetry.get("input_tokens"),
                                      "output_tokens": telemetry.get("output_tokens"),
                                      "estimated_cost": telemetry.get("estimated_cost")}}


def materialize(plan: dict, journal: dict, price_table: dict, *, root: Path = ROOT) -> dict:
    owners = [row for row in plan["cases"] if row["requires_provider_call"]]
    if len(journal["completed"]) != len(owners) or journal["unknown"] or journal["known_failed"]:
        raise ValueError("cannot materialize incomplete or uncertain generation journal")
    if any(event["price_table_sha256"] != _price_hash(price_table)
           for event in journal["completed"].values()):
        raise ValueError("journal price table differs from final economics price table")
    reconciled = journal.get("reconciled", {})
    cache = _json(root / "cache/validation_v1_llm_cache.json")
    chunks = {item["chunk_id"]: item for item in _json(root / "cache/policy_index.json")["chunks"]}
    owner_by_hash = {row["canonical_input_hash"]: row for row in owners}
    results = []
    for row in plan["cases"]:
        reconciled_owner = None
        if row["generation_source"] == "reused":
            key = row["reuse_source"].split(":", 1)[1]
            answer = cache[key]["answer"]
            generation = {"cache_hit": True}
            latency = 0.0  # observed replay work only; historical generation latency is unavailable
        else:
            owner = owner_by_hash[row["canonical_input_hash"]]
            event = journal["completed"][owner["generation_key"]]
            answer = event["answer"]
            generation = event["telemetry"] if row["requires_provider_call"] else {
                **event["telemetry"], "cache_hit": True}
            latency = event["telemetry"]["latency_seconds"] if row["requires_provider_call"] else 0.0
            if owner["generation_key"] in reconciled:
                reconciled_owner = owner
        result = planner.record_live_result(row, answer,
            {"invoked": False, "cache_hit": False, "rewritten_query": row["original_query"]},
            generation, wall_seconds=latency, legacy_cache=cache, chunk_meta=chunks)
        if reconciled_owner is not None:
            result["generation_source"] = "manual_reconciliation_after_unknown"
            result["manual_reconciliation"] = _reconciliation_provenance(
                reconciled[reconciled_owner["generation_key"]])
        results.append(result)
    if len(results) != EXPECTED["case_arm_rows"]:
        raise ValueError("final materialization row count mismatch")
    for row in results:
        if row["generation_source"] in {"new", "manual_reconciliation_after_unknown"} and not row["requires_provider_call"]:
            owner = owner_by_hash[row["canonical_input_hash"]]
            original = next(item for item in results if item["case_id"] == owner["case_id"] and
                            item["arm"] == owner["arm"])
            if row["answer"] != original["answer"]:
                raise ValueError("shared generation answer mismatch")
    economics = planner.aggregate_live_results(results, price_table=price_table, legacy_cache=cache)
    physical = economics["experiment_physical_execution"]
    if physical["unique_generation_calls"] != len(owners):
        raise ValueError("physical execution count mismatch")
    physical["observable_generation_completions"] = len(owners)
    physical["manual_reconciliation_attempts"] = len(reconciled)
    physical["unknown_usage_provider_attempts"] = len(reconciled)
    physical["total_provider_attempts"] = len(owners) + len(reconciled)
    physical["unknown_usage_generation_keys"] = sorted(reconciled.keys())
    physical["usage_measurement_status"] = (
        "measured spend from observable completions plus "
        f"{len(reconciled)} original attempt(s) with unknown usage"
        if reconciled else "fully measured")
    return {"schema_version": 1, "version": "query-aware-stage1-generation-v1",
            "status": "complete", "case_count": len(results),
            "price_table": price_table, "price_table_sha256": _price_hash(price_table),
            "frozen_integrity": plan["frozen_integrity"],
            "per_arm_counterfactual_economics": economics["per_arm_counterfactual"],
            "experiment_physical_execution_economics": physical,
            "per_case_counterfactual_economics": economics["per_case_counterfactual"],
            "manual_reconciliation_events": [
                {"generation_key": key, **_reconciliation_provenance(entry)}
                for key, entry in reconciled.items()],
            "cases": results}


def _write_atomic(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_final(result: dict, root: Path) -> None:
    output = root / RESULTS.relative_to(ROOT)
    summary = root / SUMMARY.relative_to(ROOT)
    _write_atomic(output, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    physical = result["experiment_physical_execution_economics"]
    lines = ["# Query-aware Stage 1 generation", "", f"Rows: {result['case_count']}.", "",
             "## Experiment physical execution", "",
             f"Unique new generation calls (observable completions): {physical['unique_generation_calls']}.",
             f"Total provider attempts (incl. unknown completions): {physical['total_provider_attempts']}.",
             f"Unknown-usage provider attempts: {physical['unknown_usage_provider_attempts']}.",
             f"Usage measurement status: {physical['usage_measurement_status']}.",
             f"Provider tokens: {physical['provider_input_tokens']} input / {physical['provider_output_tokens']} output.",
             f"Estimated cost from the supplied price table: {physical['estimated_cost']:.8f}.",
             "", "## Per-arm counterfactual economics", "",
             "Each arm is charged for the generation it consumes, including shared and historical results. These totals are not this experiment's physical spend.",
             "", "| Arm | Cases | Provider input | Provider output | Cost/query | Reused rows |",
             "|---|---:|---:|---:|---:|---:|"]
    for arm, value in result["per_arm_counterfactual_economics"].items():
        lines.append(f"| {arm} | {value['cases']} | {value['provider_input_tokens']} | {value['provider_output_tokens']} | {value['cost_per_query']:.8f} | {value['reused_result_rows']} |")
    if result.get("manual_reconciliation_events"):
        lines += ["", "## Manual reconciliation events", "",
                  "One or more generations were resolved by an explicitly authorized manual reconciliation retry after an unobservable UNKNOWN. The original UNKNOWN attempt is preserved in the journal with unknown/unmeasured usage."]
        for item in result["manual_reconciliation_events"]:
            lines.append(f"- `{item['generation_key']}`: original={item['original_attempt_status']} "
                         f"({item['original_attempt_usage']}); reconciliation usage={item['reconciliation_usage']}.")
    lines += ["", "Per-case provenance and citation validation are in the JSON artifact. No answer-quality evaluation was run."]
    _write_atomic(summary, "\n".join(lines) + "\n")


def _execution_config(root: Path, freeze: dict) -> LLMConfig:
    config = LLMConfig.from_env(root / ".env")
    if (config.model != freeze["generation_model"] or
        _hash_text(config.base_url) != freeze["provider_base_url_sha256"] or
        config.thinking_mode != freeze["provider_thinking_mode"]):
        raise ValueError("provider/model/settings differ from live executor freeze")
    return config


def _lock(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise ValueError(f"execution lock exists; inspect before retry: {path}") from error
    os.write(descriptor, f"pid={os.getpid()} timestamp={_now()}\n".encode())
    return descriptor


def run_execute(root: Path = ROOT, *, price_path: Path,
                client_factory=OpenAIChatCompletionsClient) -> dict:
    lock_path = root / "eval/results/query_aware_stage1_live_journal.lock"
    descriptor = _lock(lock_path)
    try:
        plan_path = root / PLAN.relative_to(ROOT)
        freeze_path = root / FREEZE.relative_to(ROOT)
        journal_path = root / JOURNAL.relative_to(ROOT)
        plan, owners, journal, info = audit(root, plan_path=plan_path,
            freeze_path=freeze_path, journal_path=journal_path)
        freeze = _json(freeze_path)
        config = _execution_config(root, freeze)
        price_table = _json(price_path)
        planner.estimate_cost(0, 0, price_table)
        if journal["unknown"] or journal["known_failed"]:
            raise ValueError("journal contains uncertain/failed owner; automatic retry prohibited")
        if any(event["price_table_sha256"] != _price_hash(price_table)
               for event in journal["completed"].values()):
            raise ValueError("resume price table differs from completed journal")
        client = client_factory(config)
        for owner in owners:
            if owner["generation_key"] in journal["completed"]:
                continue
            execute_owner(owner, plan, client, journal_path, price_table, root=root)
        final_journal = read_journal(journal_path, owners)
        result = materialize(plan, final_journal, price_table, root=root)
        _write_final(result, root)
        return {**info, "completed": len(final_journal["completed"]),
                "reconciled": len(final_journal["reconciled"]), "pending": 0,
                "result_path": str(root / RESULTS.relative_to(ROOT))}
    finally:
        os.close(descriptor)
        lock_path.unlink()


def run_reconcile(root: Path = ROOT, *, generation_key: str, price_path: Path,
                  reason: str = RECONCILIATION_REASON,
                  client_factory=OpenAIChatCompletionsClient) -> dict:
    """Perform exactly one authorized reconciliation attempt; never resumes or materializes."""
    lock_path = root / "eval/results/query_aware_stage1_live_journal.lock"
    descriptor = _lock(lock_path)
    try:
        plan_path = root / PLAN.relative_to(ROOT)
        freeze_path = root / FREEZE.relative_to(ROOT)
        journal_path = root / JOURNAL.relative_to(ROOT)
        plan, owners, journal, info = audit(root, plan_path=plan_path,
            freeze_path=freeze_path, journal_path=journal_path)
        freeze = _json(freeze_path)
        config = _execution_config(root, freeze)
        price_table = _json(price_path)
        planner.estimate_cost(0, 0, price_table)
        owner_by_key = {owner["generation_key"]: owner for owner in owners}
        if generation_key not in owner_by_key:
            raise ValueError("reconciliation target is not a frozen generation owner")
        if any(event["price_table_sha256"] != _price_hash(price_table)
               for event in journal["completed"].values()):
            raise ValueError("reconciliation price table differs from completed journal")
        client = client_factory(config)
        event = reconcile_owner(owner_by_key[generation_key], plan, client, journal_path,
                                price_table, reason=reason, root=root)
        return {**info, "reconciled_generation_key": generation_key,
                "reconciliation_status": event["status"]}
    finally:
        os.close(descriptor)
        lock_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="audit and resume preview; no provider call")
    action.add_argument("--execute", action="store_true", help="execute frozen generation owners")
    action.add_argument("--reconcile-generation-key", metavar="KEY",
                        help="one authorized reconciliation attempt for an unobservable UNKNOWN key")
    parser.add_argument("--confirm-frozen-plan", action="store_true")
    parser.add_argument("--confirm-manual-reconciliation", action="store_true")
    parser.add_argument("--price-table", type=Path,
                        help="JSON with input_per_million and output_per_million")
    args = parser.parse_args()
    if args.check:
        _, _, _, info = audit()
    elif args.execute:
        if not args.confirm_frozen_plan or args.price_table is None:
            parser.error("--execute requires --confirm-frozen-plan and --price-table")
        info = run_execute(price_path=args.price_table)
    else:
        if not args.confirm_manual_reconciliation or args.price_table is None:
            parser.error("--reconcile-generation-key requires --confirm-manual-reconciliation and --price-table")
        info = run_reconcile(generation_key=args.reconcile_generation_key,
                             price_path=args.price_table)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
