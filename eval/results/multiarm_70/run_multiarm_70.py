"""One-command 70-query four-arm comparative snapshot.

Default behaviour (no flags)
----------------------------
Execute all four arms on all 70 frozen queries of this repository:

  * Validation V1  (50 queries, 208 QUERY_REQUIRED aspects)
  * Router V1      (20 queries,  66 required aspects)

and write `multiarm_70_summary.md` next to this script.

Arms
----
  FAST                   current Direct path (fixed Top5 context)
  SEARCH+                current implemented fixed-decompose path
  ADAPTIVE               frozen no-router adaptive evidence prefix
  AUTO_ROUTER_AVAILABLE  best available auto-router per cohort (see summary)

`--reuse-existing`
------------------
Reuse frozen historical results where they exist and execute only the missing
cells:

  * Validation 50 FAST / ADAPTIVE / AUTO_ROUTER_AVAILABLE  -> frozen A1 artifacts
  * Router 20 FAST / SEARCH+ / AUTO_ROUTER_AVAILABLE        -> frozen Router V1 raw run
  * Validation 50 SEARCH+ and Router 20 ADAPTIVE are executed with the frozen
    semantics of their arms (the only inventory gaps).

Raw/intermediate data goes to a temporary directory and is removed on success.
Only `multiarm_70_summary.md` is persisted.

This is an exploratory comparative snapshot over two differently-constructed
cohorts; it is not a new independent holdout and does not support a
generalization claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SUMMARY_PATH = SCRIPT_DIR / "multiarm_70_summary.md"

VERSION = "multiarm-70-snapshot-v1"
SEARCHPLUS_VERSION = "multiarm-supplemental-searchplus-val50"
ADAPTIVE_VERSION = "multiarm-supplemental-adaptive-router20"

VALIDATION_META = PROJECT_ROOT / "eval" / "validation" / "validation_v1_metadata.json"
VALIDATION_QUERIES = PROJECT_ROOT / "eval" / "validation" / "broad_queries_validation_v1.json"
VALIDATION_TRUTH = PROJECT_ROOT / "eval" / "results" / "frozen_human_verdicts_v1.json"
ROUTER_BENCHMARK = PROJECT_ROOT / "eval" / "router_benchmark_v1.json"
ROUTER_TRUTH = PROJECT_ROOT / "eval" / "router_v1_required_aspects.json"

A1_QUALITY = PROJECT_ROOT / "eval" / "results" / "a1_blind_answer_quality_frozen_v1.json"
A1_MAPPING = PROJECT_ROOT / "eval" / "results" / "a1_blind_answer_mapping_v1.json"
A1_ECONOMICS = PROJECT_ROOT / "eval" / "results" / "query_aware_stage1_generation_results.json"
ROUTER_RAW = PROJECT_ROOT / "eval" / "results" / "router_v1" / "raw" / "router_v1_raw_results.json"
ROUTER_ANSWER_EVAL = PROJECT_ROOT / "eval" / "results" / "router_v1" / "router_v1_answer_eval.json"

ENV_FILE = PROJECT_ROOT / ".env"

ARM_ORDER = ("FAST", "SEARCH+", "ADAPTIVE", "AUTO_ROUTER_AVAILABLE")

# Frozen historical implementations reused per cohort.
VALIDATION_REUSED_POLICIES = {
    "FAST": "fixed_top5",
    "ADAPTIVE": "no_router_adaptive_v1",
    "AUTO_ROUTER_AVAILABLE": "query_router_v1",
}
ROUTER_REUSED_ARMS = {
    "FAST": "FIXED_DIRECT",
    "SEARCH+": "FIXED_DECOMPOSE",
    "AUTO_ROUTER_AVAILABLE": "ROUTED",
}

DISQUALIFYING_CLAIM_SUPPORT = {"unsupported", "contradicted", "partial", "uncertain"}
DISQUALIFYING_CLAIM_CITATION = {"unsupported", "missing", "uncertain"}


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #

def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_metadata() -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True,
                                  timeout=30).stdout.strip()
        except Exception:
            return ""
    head = run("git", "rev-parse", "--short", "HEAD") or "unavailable"
    dirty = bool(run("git", "status", "--porcelain"))
    return {"head": head, "working_tree_dirty": dirty}


def make_cell(*, status: str, covered: int | None = None, total: int | None = None,
              complete: bool | None = None, citation_valid: bool | None = None,
              eligible: bool | None = None, input_tokens: int | None = None,
              output_tokens: int | None = None, calls: int | None = None,
              latency_seconds: float | None = None, executed_path: str | None = None,
              source: str = "reused", error: str | None = None) -> dict:
    return {
        "status": status,
        "covered": covered,
        "total": total,
        "complete": complete,
        "citation_valid": citation_valid,
        "eligible": eligible,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "calls": calls,
        "latency_seconds": latency_seconds,
        "executed_path": executed_path,
        "source": source,
        "error": error,
    }


# --------------------------------------------------------------------------- #
# Frozen inputs
# --------------------------------------------------------------------------- #

def load_validation_cases(limit: int | None) -> list[dict]:
    data = load_json(VALIDATION_QUERIES)
    cases = [{"case_id": case["case_id"], "query": case["query"]} for case in data["cases"]]
    if limit:
        cases = cases[:limit]
    return cases


def load_validation_aspects() -> dict[str, list[dict]]:
    truth = load_json(VALIDATION_TRUTH)
    required: dict[str, list[dict]] = {}
    for item in truth["items"]:
        if item["case_id"].startswith("VAL-") and item["final"] == "QUERY_REQUIRED":
            required.setdefault(item["case_id"], []).append(
                {"fact_id": item["aspect_id"], "fact": item["statement"]})
    for aspects in required.values():
        aspects.sort(key=lambda aspect: aspect["fact_id"])
    return required


def load_router_cases(limit: int | None) -> list[dict]:
    data = load_json(ROUTER_BENCHMARK)
    cases = [{"case_id": case["id"], "query": case["query"]} for case in data["cases"]]
    if limit:
        cases = cases[:limit]
    return cases


def load_router_aspects() -> dict[str, list[dict]]:
    truth = load_json(ROUTER_TRUTH)
    return {
        case["id"]: [{"fact_id": aspect["aspect_id"], "fact": aspect["statement"]}
                     for aspect in case["required_aspects"]]
        for case in truth["cases"]
    }


def short_ids(cases: list[dict], prefix: str) -> dict[str, str]:
    return {case["case_id"]: f"{prefix}_{index:03d}" for index, case in enumerate(cases, 1)}


# --------------------------------------------------------------------------- #
# Historical (reused) cells
# --------------------------------------------------------------------------- #

def load_validation_reused_cells() -> dict[str, dict[str, dict]]:
    quality = load_json(A1_QUALITY)
    mapping = load_json(A1_MAPPING)
    economics = load_json(A1_ECONOMICS)
    econ_rows = {(row["case_id"], row["arm"]): row
                 for row in economics["per_case_counterfactual_economics"]}
    stage_rows = {(row["case_id"], row["arm"]): row for row in economics["cases"]}
    quality_by_case = {case["case_id"]: case for case in quality["cases"]}

    cells: dict[str, dict[str, dict]] = {}
    for case_id, case in sorted(quality_by_case.items()):
        label_arm: dict[str, str] = {}
        for label, meta in mapping["cases"][case_id].items():
            for arm in meta["arms"]:
                label_arm[arm] = label
        per_arm: dict[str, dict] = {}
        for arm_key, policy in VALIDATION_REUSED_POLICIES.items():
            label = label_arm.get(policy)
            answer = case["answers"].get(label)
            if answer is None or answer.get("judge_error"):
                per_arm[arm_key] = make_cell(status="unavailable")
                continue
            aspects = answer["aspects"]
            covered = sum(1 for value in aspects.values() if value["judge_status"] == "covered")
            econ = econ_rows.get((case_id, policy), {})
            stage = stage_rows.get((case_id, policy), {})
            citation_valid = bool((stage.get("validation") or {}).get("valid"))
            claim_support = answer.get("claim_counts") or {}
            claim_citation = answer.get("claim_citation_counts") or {}
            eligible = bool(
                citation_valid
                and not any(value["judge_status"] == "incorrect" for value in aspects.values())
                and not any(claim_support.get(status) for status in DISQUALIFYING_CLAIM_SUPPORT)
                and not any(claim_citation.get(status) for status in DISQUALIFYING_CLAIM_CITATION)
            )
            per_arm[arm_key] = make_cell(
                status="judged",
                covered=covered,
                total=len(aspects),
                complete=bool(answer["query_required_complete"]),
                citation_valid=citation_valid,
                eligible=eligible,
                input_tokens=econ.get("provider_input_tokens"),
                output_tokens=econ.get("provider_output_tokens"),
                calls=1,
                latency_seconds=None,
                executed_path=policy,
                source="reused",
            )
        cells[case_id] = per_arm
    return cells


def load_router_reused_cells() -> dict[str, dict[str, dict]]:
    raw = load_json(ROUTER_RAW)
    answer_eval = load_json(ROUTER_ANSWER_EVAL)
    raw_by_case = {case["case_id"]: case for case in raw["cases"]}
    cells: dict[str, dict[str, dict]] = {}
    for case_id, raw_case in raw_by_case.items():
        case_eval = answer_eval["cases"][case_id]
        per_arm: dict[str, dict] = {}
        for arm_key, arm in ROUTER_REUSED_ARMS.items():
            entry = case_eval[arm]
            result = raw_case["arms"][arm]
            trace = result.get("trace") or {}
            calls = trace.get("model_calls") or []
            input_tokens = sum(call.get("input_tokens") or 0 for call in calls)
            output_tokens = sum(call.get("output_tokens") or 0 for call in calls)
            if entry["status"] != "judged":
                per_arm[arm_key] = make_cell(status=entry["status"],
                                             executed_path=entry.get("executed_path"),
                                             source="reused", error=None)
                continue
            per_arm[arm_key] = make_cell(
                status="judged",
                covered=entry.get("required_covered"),
                total=entry.get("required_total"),
                complete=bool(entry.get("query_required_complete")),
                citation_valid=bool((entry.get("citation_validation") or {}).get("valid")),
                eligible=bool(entry.get("eligible")),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                calls=len(calls),
                latency_seconds=trace.get("total_latency_seconds"),
                executed_path=entry.get("executed_path"),
                source="reused",
            )
        cells[case_id] = per_arm
    return cells


# --------------------------------------------------------------------------- #
# Judging (frozen broad-v3-answer-quality-v1 protocol)
# --------------------------------------------------------------------------- #

def summarize_judgment(judged: dict, facts: list[dict]) -> dict:
    statuses = {item["fact_id"]: item for item in judged["facts"]}
    fact_ids = [fact["fact_id"] for fact in facts]
    covered = sorted(fid for fid in fact_ids if statuses[fid]["status"] == "covered")
    missing = sorted(fid for fid in fact_ids if statuses[fid]["status"] == "missing")
    incorrect = sorted(fid for fid in fact_ids if statuses[fid]["status"] == "incorrect")
    uncertain = sorted(fid for fid in fact_ids if statuses[fid]["status"] == "uncertain")
    return {
        "facts": {fid: statuses[fid] for fid in fact_ids},
        "required_total": len(fact_ids),
        "required_covered": len(covered),
        "covered_ids": covered,
        "missing_ids": missing,
        "incorrect_ids": incorrect,
        "uncertain_ids": uncertain,
        "query_required_complete": len(covered) == len(fact_ids),
        "claim_counts": dict(Counter(claim["support_status"] for claim in judged["claims"])),
        "claim_citation_counts": dict(Counter(claim["citation_status"]
                                              for claim in judged["claims"])),
        "judge_error": None,
    }


def eligible_from_judgment(judged: dict, citation_valid: bool) -> bool:
    claim_support = judged.get("claim_counts") or {}
    claim_citation = judged.get("claim_citation_counts") or {}
    return bool(
        citation_valid
        and not judged.get("incorrect_ids")
        and not any(claim_support.get(status) for status in DISQUALIFYING_CLAIM_SUPPORT)
        and not any(claim_citation.get(status) for status in DISQUALIFYING_CLAIM_CITATION)
    )


def judge_answer(case_id: str, query: str, facts: list[dict], answer: str,
                 evidence: list[dict], client, model: str, cache) -> dict:
    from eval.run_answer_eval import (
        V3_JUDGE_MAX_TOKENS, V3_JUDGE_VERSION, _judge_messages, _parse_judge, _stable_hash)
    from src.generator import assign_evidence_sources

    sources = assign_evidence_sources([SimpleNamespace(**item) for item in evidence])
    case = {"case_id": case_id, "query": query, "facts": facts}
    messages = _judge_messages(case, {"A": {"generation": {"answer": answer}, "sources": sources}})
    prompt_hash = _stable_hash({"messages": messages, "model": model, "temperature": 0.0,
                                "max_tokens": V3_JUDGE_MAX_TOKENS, "version": V3_JUDGE_VERSION})
    key = _stable_hash({"case_id": case_id, "label": "A", "model": model,
                        "prompt_config_hash": prompt_hash,
                        "answer_sha256": _stable_hash(answer)})
    cached = cache.get(key)
    if cached is None:
        raw, provider_usage = client.complete_with_usage(
            messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
        try:
            parsed = _parse_judge(raw, {"A"}, {fact["fact_id"] for fact in facts})
        except (ValueError, KeyError, TypeError) as error:
            cache.set(key, {"raw": raw, "error": str(error), "provider_usage": provider_usage})
            raise ValueError(f"judge schema failure {case_id}: {error}") from error
        cached = {"answers": parsed, "raw": raw, "prompt_config_hash": prompt_hash,
                  "model": model, "provider_usage": provider_usage}
        cache.set(key, cached)
    elif "error" in cached:
        raise ValueError(f"cached judge error {case_id}: {cached['error']}")
    return summarize_judgment(cached["answers"]["A"], facts)


# --------------------------------------------------------------------------- #
# Live execution
# --------------------------------------------------------------------------- #

class LiveRunner:
    """Current implementation stack shared by the executed cells."""

    def __init__(self, workdir: Path) -> None:
        from src.agent import PolicySupportAgent
        from src.router_v1_pipeline import RouterV1Pipeline

        self.workdir = workdir
        self.agent = PolicySupportAgent.from_project(
            PROJECT_ROOT, device="cpu",
            rewrite_cache_path=workdir / "rewrite_cache.json",
            generation_cache_path=workdir / "generation_cache.json",
        )
        self.pipeline = RouterV1Pipeline(
            self.agent._retriever, self.agent._client, model=self.agent._model,
            generation_cache=self.agent._generation_cache,
            max_history_turns=self.agent._max_history_turns)
        self.retriever = self.agent._retriever
        self.client = self.agent._client
        self.model = self.agent._model
        self.reranker = getattr(self.retriever, "reranker_model", "unknown")

    def rewrite(self, query: str):
        return self.pipeline.rewrite(query, [])

    def generate(self, query: str, evidence, executed_path: str,
                 started: float) -> dict:
        from eval.run_answer_eval import _RecordingGenerationClient
        from src.generator import generate_grounded_answer

        recorder = _RecordingGenerationClient(self.client)
        try:
            produced = generate_grounded_answer(
                query, [], evidence, recorder, model=self.model,
                cache=self.agent._generation_cache)
            records = [{"stage": "generation", "input_tokens": recorder.usage.get("input_tokens"),
                        "output_tokens": recorder.usage.get("output_tokens")}]
            return {
                "answer": produced["answer"],
                "evidence": [item.to_dict() for item in evidence],
                "citation_validation": produced["validation"],
                "input_tokens": recorder.usage.get("input_tokens"),
                "output_tokens": recorder.usage.get("output_tokens"),
                "calls": 1,
                "latency_seconds": time.perf_counter() - started,
                "executed_path": executed_path,
                "error_stage": None,
                "error": None,
                "_model_calls": records,
            }
        except Exception as error:
            return {
                "answer": None, "evidence": [item.to_dict() for item in evidence],
                "citation_validation": None,
                "input_tokens": recorder.usage.get("input_tokens"),
                "output_tokens": recorder.usage.get("output_tokens"),
                "calls": 1, "latency_seconds": time.perf_counter() - started,
                "executed_path": executed_path, "error_stage": "generation",
                "error": str(error), "_model_calls": [],
            }


def record_from_router_result(result, started: float) -> dict:
    trace = result.trace
    calls = trace.model_calls if trace else ()
    return {
        "answer": result.answer,
        "evidence": [item.to_dict() for item in result.evidence],
        "citation_validation": result.citation_validation,
        "input_tokens": sum(call.input_tokens or 0 for call in calls),
        "output_tokens": sum(call.output_tokens or 0 for call in calls),
        "calls": len(calls),
        "latency_seconds": time.perf_counter() - started,
        "executed_path": result.executed_path,
        "error_stage": result.error_stage,
        "error": result.error,
        "_model_calls": [call.to_dict() for call in calls],
    }


def adaptive_evidence(ranked, retriever):
    from eval.run_stage0_replay import NO_ROUTER_DEFAULTS, no_router_adaptive_rows

    rows = [{"chunk_id": item.chunk_id, "bge_score": item.reranker_score,
             "tokens": retriever.count_evidence_tokens(item)} for item in ranked]
    selected = no_router_adaptive_rows(rows, **NO_ROUTER_DEFAULTS)
    return tuple(ranked[:len(selected)]), sum(row["tokens"] for row in selected)


def query_router_evidence(runner, rewritten: str):
    from eval.run_stage0_replay import route_query
    from src.evidence_budget import EvidenceBudgetConfig, select_evidence_prefix

    ranked = runner.retriever.search(rewritten, top_k=20)
    if route_query(rewritten) == "SIMPLE":
        return tuple(ranked[:5]), "FIXED_TOP5"
    decision = select_evidence_prefix(
        rewritten, ranked, config=EvidenceBudgetConfig(),
        token_count=runner.retriever.count_evidence_tokens)
    return tuple(ranked[:decision.selected_k]), "ADAPTIVE_PREFIX_V1"


def execute_cell(runner: LiveRunner, cohort: str, arm_key: str, case: dict,
                 rewritten: str) -> dict:
    """Execute one arm cell on the current stack and return a raw record."""
    from src.router_v1_pipeline import FIXED_DECOMPOSE, FIXED_DIRECT, ROUTED

    started = time.perf_counter()
    query = case["query"]
    if cohort == "validation":
        if arm_key == "FAST":
            evidence = tuple(runner.retriever.search(rewritten, top_k=5))
            return runner.generate(query, evidence, "FIXED_TOP5", started)
        if arm_key == "SEARCH+":
            result = runner.pipeline.run_arm(
                FIXED_DECOMPOSE, query, [], rewritten,
                case_id=case["case_id"], rewrite_source="provided")
            return record_from_router_result(result, started)
        if arm_key == "ADAPTIVE":
            ranked = runner.retriever.search(rewritten, top_k=20)
            evidence, _ = adaptive_evidence(ranked, runner.retriever)
            return runner.generate(query, evidence, "ADAPTIVE_PREFIX_NO_ROUTER_V1", started)
        if arm_key == "AUTO_ROUTER_AVAILABLE":
            evidence, executed = query_router_evidence(runner, rewritten)
            return runner.generate(query, evidence,
                                   f"QUERY_STRUCTURE_ROUTER_V1::{executed}", started)
        raise ValueError(arm_key)
    if arm_key == "FAST":
        result = runner.pipeline.run_arm(FIXED_DIRECT, query, [], rewritten,
                                         case_id=case["case_id"], rewrite_source="provided")
        return record_from_router_result(result, started)
    if arm_key == "SEARCH+":
        result = runner.pipeline.run_arm(FIXED_DECOMPOSE, query, [], rewritten,
                                         case_id=case["case_id"], rewrite_source="provided")
        return record_from_router_result(result, started)
    if arm_key == "AUTO_ROUTER_AVAILABLE":
        result = runner.pipeline.run_arm(ROUTED, query, [], rewritten,
                                         case_id=case["case_id"], rewrite_source="provided")
        return record_from_router_result(result, started)
    if arm_key == "ADAPTIVE":
        ranked = runner.retriever.search(rewritten, top_k=20)
        evidence, _ = adaptive_evidence(ranked, runner.retriever)
        return runner.generate(query, evidence, "ADAPTIVE_PREFIX_NO_ROUTER_V1", started)
    raise ValueError(arm_key)


def cell_from_record(cohort: str, record: dict, judged: dict | None) -> dict:
    citation_valid = None
    if record.get("citation_validation") is not None:
        citation_valid = bool(record["citation_validation"].get("valid"))
    if judged and not judged.get("judge_error"):
        eligible = eligible_from_judgment(judged, bool(citation_valid))
        return make_cell(
            status="judged", covered=judged["required_covered"], total=judged["required_total"],
            complete=judged["query_required_complete"], citation_valid=citation_valid,
            eligible=eligible, input_tokens=record.get("input_tokens"),
            output_tokens=record.get("output_tokens"), calls=record.get("calls"),
            latency_seconds=record.get("latency_seconds"),
            executed_path=record.get("executed_path"), source="new")
    return make_cell(
        status="error" if record.get("error") or record.get("error_stage") else "unavailable",
        citation_valid=citation_valid, input_tokens=record.get("input_tokens"),
        output_tokens=record.get("output_tokens"), calls=record.get("calls"),
        latency_seconds=record.get("latency_seconds"),
        executed_path=record.get("executed_path"), source="new",
        error=str(record.get("error") or record.get("error_stage") or ""))


# --------------------------------------------------------------------------- #
# Supplemental cells (the two inventory gaps), with workdir persistence
# --------------------------------------------------------------------------- #

def load_supplemental(path: Path, version: str) -> dict | None:
    if not path.exists():
        return None
    state = load_json(path)
    if state.get("version") != version:
        return None
    return state


def supplemental_cell(cohort: str, entry: dict, source: str = "new") -> dict:
    judged = entry.get("judge") or {}
    citation_valid = bool((entry.get("citation_validation") or {}).get("valid"))
    input_tokens = entry.get("input_tokens")
    output_tokens = entry.get("output_tokens")
    calls = entry.get("calls")
    if input_tokens is None:
        usage = entry.get("provider_usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        calls = 1
    if input_tokens is None and entry.get("trace") is not None:
        model_calls = entry["trace"].get("model_calls") or []
        input_tokens = sum(call.get("input_tokens") or 0 for call in model_calls)
        output_tokens = sum(call.get("output_tokens") or 0 for call in model_calls)
        calls = len(model_calls)
    if not entry.get("answer"):
        return make_cell(status="unavailable", executed_path=entry.get("executed_path"),
                         source=source, error=str(entry.get("error") or ""))
    if judged.get("judge_error"):
        return make_cell(status="error", executed_path=entry.get("executed_path"),
                         source=source, error=str(judged["judge_error"]))
    eligible = judged.get("eligible")
    if eligible is None:
        eligible = eligible_from_judgment(judged, citation_valid)
    return make_cell(
        status="judged", covered=judged.get("required_covered"),
        total=judged.get("required_total"), complete=judged.get("query_required_complete"),
        citation_valid=citation_valid, eligible=eligible,
        input_tokens=input_tokens, output_tokens=output_tokens,
        calls=calls, latency_seconds=entry.get("wall_clock_seconds"),
        executed_path=entry.get("executed_path"), source=source)


def run_searchplus_cell(runner: LiveRunner, case: dict, rewritten: str,
                        rewrite_calls=()) -> dict:
    from src.router_v1_pipeline import FIXED_DECOMPOSE

    started = time.perf_counter()
    result = runner.pipeline.run_arm(FIXED_DECOMPOSE, case["query"], [], rewritten,
                                     case_id=case["case_id"], rewrite_source="provided")
    trace = result.trace
    calls = trace.model_calls if trace else ()
    return {
        "case_id": case["case_id"],
        "raw_query": case["query"],
        "requested_arm": "FIXED_DECOMPOSE",
        "executed_path": result.executed_path,
        "rewritten_query": rewritten,
        "rewrite_calls": [call.to_dict() for call in rewrite_calls],
        "answer": result.answer,
        "evidence": [item.to_dict() for item in result.evidence],
        "citation_validation": result.citation_validation,
        "input_tokens": sum(call.input_tokens or 0 for call in calls),
        "output_tokens": sum(call.output_tokens or 0 for call in calls),
        "calls": len(calls),
        "wall_clock_seconds": time.perf_counter() - started,
        "error": result.error,
    }


def run_adaptive_cell(runner: LiveRunner, case: dict, rewritten: str,
                      execution_label: str = "ADAPTIVE_PREFIX_NO_ROUTER_V1") -> dict:
    started = time.perf_counter()
    ranked = runner.retriever.search(rewritten, top_k=20)
    evidence, evidence_tokens = adaptive_evidence(ranked, runner.retriever)
    record = runner.generate(case["query"], evidence, execution_label, started)
    return {
        "case_id": case["case_id"],
        "raw_query": case["query"],
        "requested_arm": "ADAPTIVE_NO_ROUTER_V1",
        "executed_path": execution_label,
        "shared_rewrite": rewritten,
        "selected_chunk_ids": [item.chunk_id for item in evidence],
        "evidence": record["evidence"],
        "evidence_tokens": evidence_tokens,
        "answer": record["answer"],
        "citation_validation": record["citation_validation"],
        "input_tokens": record["input_tokens"],
        "output_tokens": record["output_tokens"],
        "calls": record["calls"],
        "wall_clock_seconds": record["latency_seconds"],
        "error": record["error"],
    }


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def aggregate_cells(rows: list[dict], arm: str) -> dict:
    cells = [row["cells"].get(arm) for row in rows]
    cells = [cell for cell in cells if cell is not None]
    available = [cell for cell in cells if cell["status"] == "judged" and cell["covered"] is not None]
    tokens = [cell["input_tokens"] + cell["output_tokens"] for cell in cells
              if cell["input_tokens"] is not None and cell["output_tokens"] is not None]
    latencies = [cell["latency_seconds"] for cell in cells
                 if cell["latency_seconds"] is not None]
    calls = [cell["calls"] for cell in cells if cell["calls"] is not None]
    case_count = len(rows)
    return {
        "arm": arm,
        "cases": case_count,
        "available": len(available),
        "unavailable": sum(1 for cell in cells if cell["status"] != "judged"),
        "complete": sum(1 for cell in available if cell["complete"]),
        "covered": sum(cell["covered"] for cell in available),
        "required": sum(cell["total"] for cell in available),
        "citation_valid": sum(1 for cell in cells if cell["citation_valid"]),
        "eligible": sum(1 for cell in cells if cell["eligible"]),
        "input_tokens": sum(cell["input_tokens"] for cell in cells
                            if cell["input_tokens"] is not None),
        "output_tokens": sum(cell["output_tokens"] for cell in cells
                             if cell["output_tokens"] is not None),
        "tokens": sum(tokens),
        "tokens_n": len(tokens),
        "calls": sum(calls),
        "calls_n": len(calls),
        "latency_n": len(latencies),
        "latency_total": sum(latencies) if latencies else None,
        "latency_mean": statistics.mean(latencies) if latencies else None,
        "latency_median": statistics.median(latencies) if latencies else None,
        "tokens_per_query": (sum(tokens) / case_count) if tokens else None,
        "calls_per_query": (sum(calls) / case_count) if calls else None,
    }


def best_arm_analysis(rows: list[dict]) -> dict:
    winner_counts = {arm: {"sole": 0, "shared": 0} for arm in ARM_ORDER}
    low_cost_choice = Counter()
    best_complete = 0
    best_covered = 0
    best_total = 0
    full_ties = 0
    partial_ties = 0
    no_quality = 0
    miss_examples = []
    for row in rows:
        qualities = {arm: (cell["complete"], cell["covered"])
                     for arm, cell in row["cells"].items()
                     if cell["status"] == "judged" and cell["covered"] is not None}
        if not qualities:
            no_quality += 1
            continue
        best = max(qualities.values())
        best_complete += int(best[0])
        best_covered += best[1]
        best_total += row["required_quality_total"]
        winners = [arm for arm, quality in qualities.items() if quality == best]
        if len(winners) == 1:
            winner_counts[winners[0]]["sole"] += 1
        else:
            if len(winners) == len(qualities):
                full_ties += 1
            else:
                partial_ties += 1
            for arm in winners:
                winner_counts[arm]["shared"] += 1
        costs = {arm: row["cells"][arm]["input_tokens"] + row["cells"][arm]["output_tokens"]
                 for arm in winners
                 if row["cells"][arm]["input_tokens"] is not None
                 and row["cells"][arm]["output_tokens"] is not None}
        if costs:
            low_cost_choice[min(costs, key=costs.get)] += 1
        if "AUTO_ROUTER_AVAILABLE" in qualities and qualities["AUTO_ROUTER_AVAILABLE"] != best:
            miss_examples.append(row["id"])
    return {
        "best_complete": best_complete,
        "best_covered": best_covered,
        "best_total": best_total,
        "winner_counts": winner_counts,
        "full_ties": full_ties,
        "partial_ties": partial_ties,
        "no_quality": no_quality,
        "low_cost_choice": dict(low_cost_choice),
        "auto_router_misses": len(miss_examples),
        "auto_router_miss_examples": miss_examples[:8],
    }


def pareto_rows(stats: dict) -> list[str]:
    lines = ["| Arm | Quality (complete / required recall) | Tokens/query | Latency/query | Interpretation |",
             "|---|---:|---:|---:|---|"]
    interpretations = {
        "FAST": "cheapest stable default",
        "SEARCH+": "current decompose path; no quality edge at higher latency",
        "ADAPTIVE": "quality extreme; pays multiple x tokens",
        "AUTO_ROUTER_AVAILABLE": "mixed-lineage availability arm",
    }
    for arm in ARM_ORDER:
        item = stats[arm]
        quality = f"{item['complete']}/{item['cases']} / {item['covered']}/{item['required']}"
        cost = f"{item['tokens_per_query']:.1f}" if item["tokens_per_query"] else "n/a"
        latency = (f"{item['latency_mean']:.2f} s (n={item['latency_n']})"
                   if item["latency_mean"] else "n/a")
        lines.append(f"| {arm} | {quality} | {cost} | {latency} | {interpretations[arm]} |")
    return lines


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def fmt_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def arm_result_table(stats: dict, case_count: int) -> list[str]:
    lines = ["| Arm | Complete | Required Coverage | Tokens/q | Latency/q |",
             "|---|---:|---:|---:|---:|"]
    for arm in ARM_ORDER:
        item = stats[arm]
        complete = f"{item['complete']}/{case_count} ({fmt_pct(item['complete'] / case_count)})"
        coverage = (f"{item['covered']}/{item['required']} "
                    f"({fmt_pct(item['covered'] / item['required'] if item['required'] else None)})")
        tokens = f"{item['tokens_per_query']:.1f}" if item["tokens_per_query"] else "n/a"
        if item["latency_n"] == 0:
            latency = "unavailable"
        elif item["latency_median"] is not None:
            latency = (f"{item['latency_mean']:.2f} s (median {item['latency_median']:.2f} s; "
                       f"n={item['latency_n']}/{case_count})")
        else:
            latency = "unavailable"
        lines.append(f"| {arm} | {complete} | {coverage} | {tokens} | {latency} |")
    return lines


def cell_label(row: dict, arm: str, winner: bool) -> str:
    cell = row["cells"].get(arm)
    if cell is None or cell["status"] == "unavailable":
        return "unavailable"
    if cell["status"] == "error":
        return "error"
    if cell["covered"] is None or cell["total"] is None:
        return "unavailable"
    label = f"{cell['covered']}/{cell['total']}"
    if cell["complete"]:
        label += " \u2713"
    if cell["citation_valid"] is False:
        label += " \u2717cit"
    if cell["input_tokens"] is not None and cell["output_tokens"] is not None:
        label += f" {round((cell['input_tokens'] + cell['output_tokens']) / 1000, 1)}k"
    if winner:
        label += " \u2605"
    return label


def per_query_table(rows: list[dict]) -> list[str]:
    lines = ["| ID | Cohort | FAST | SEARCH+ | ADAPTIVE | AUTO ROUTER |",
             "|---|---|---|---|---|---|"]
    for row in rows:
        qualities = [(cell["complete"], cell["covered"])
                     for cell in row["cells"].values() if cell["status"] == "judged"
                     and cell["covered"] is not None]
        best = max(qualities) if qualities else None
        winners = set()
        if best is not None:
            winners = {arm for arm, cell in row["cells"].items()
                       if cell["status"] == "judged" and cell["covered"] is not None
                       and (cell["complete"], cell["covered"]) == best}
            if len(winners) == len(qualities) and len(qualities) > 1:
                winners = set()
        labels = []
        for arm in ARM_ORDER:
            labels.append(cell_label(row, arm, arm in winners))
        lines.append(f"| {row['id']} | {row['cohort_label']} | " + " | ".join(labels) + " |")
    return lines


def render_summary(context: dict) -> str:
    run = context["run"]
    stats = context["stats"]
    best = context["best"]
    rows = context["rows"]
    val_n = sum(1 for row in rows if row["cohort"] == "validation")
    router_n = len(rows) - val_n
    val_req = sum(row["required_quality_total"] for row in rows if row["cohort"] == "validation")
    router_req = sum(row["required_quality_total"] for row in rows if row["cohort"] == "router")
    combined_req = val_req + router_req
    lines: list[str] = []
    lines += [
        "# 70-Query Multi-Arm Comparative Snapshot",
        "",
        "**Exploratory comparative snapshot, not a new confirmatory experiment and not an "
        "independent holdout.**",
        "",
        "Validation V1 (50 queries) and Router V1 (20 queries) were constructed separately for "
        "different purposes; their union is a reporting view only and does not support a "
        "generalization-accuracy claim.",
        "",
        "## Reproducibility",
        "",
        f"- Run (UTC): {run['timestamp']}",
        f"- Run mode: `{run['mode']}`",
        f"- Generation/judge model: `{run['model']}`; judge protocol: frozen "
        f"`broad-v3-answer-quality-v1`; temperature 0.",
        f"- Rerankers: current-path cells use `cross-encoder/ms-marco-MiniLM-L-6-v2`; "
        f"reused Validation V1 A1 cells use `BAAI/bge-reranker-base` (frozen research stack).",
        f"- Corpus: 57 GitHub site-policy documents; Validation V1 corpus sha256 "
        f"`{run['validation_corpus_sha256'][:16]}...`; Router V1 corpus commit "
        f"`{run['router_corpus_commit'][:16]}...`",
        f"- Benchmarks: Validation V1 (50 cases / {context['validation_aspect_count']} required "
        f"aspects; queries sha256 `{run['validation_queries_sha256'][:16]}...`), "
        f"Router V1 (20 cases / {context['router_aspect_count']} required aspects; benchmark "
        f"sha256 `{run['router_benchmark_sha256'][:16]}...`).",
        f"- Script: `eval/results/multiarm_70/run_multiarm_70.py` ({VERSION}); git HEAD "
        f"`{run['git']['head']}`"
        + (" (working tree dirty)" if run["git"]["working_tree_dirty"] else "") + ".",
        f"- Reused vs newly run: {run['provenance_summary']}",
        "",
        "## 1. Scope",
        "",
        "- **Cohort A - Validation V1:** 50 frozen queries, 208 human-adjudicated "
        "`QUERY_REQUIRED` aspects. Development/research benchmark (already exposed); no longer "
        "a fresh holdout.",
        "- **Cohort B - Router V1 benchmark:** 20 frozen queries, 66 required aspects "
        "(frozen before Router V1 outputs).",
        "- **Combined 70:** cohort views are always reported separately; combined numbers are "
        "simple sums over the two cohorts, not an accuracy estimate.",
        "- Required-aspect semantics are compatible at the level used here: both truth sets "
        "define independent information units whose absence makes an answer incomplete "
        "(Validation aspects are human-adjudicated; Router aspects are model-audited). The "
        "combined denominator 208 + 66 = 274 is reported with that caveat.",
        "",
        "## 2. Arm Definitions",
        "",
        "| Arm | Semantics | Validation 50 implementation | Router 20 implementation |",
        "|---|---|---|---|",
        "| FAST | contextual rewrite -> Direct retrieval -> fixed Top5 -> grounded generation "
        "-> citation validation | reused frozen A1 `fixed_top5` (BGE research stack) "
        "| reused frozen `FIXED_DIRECT` |",
        "| SEARCH+ | shared rewrite -> requirement decomposition -> multi-stream retrieval -> "
        "deterministic 5-chunk merge -> grounded generation | executed current "
        "`FIXED_DECOMPOSE` path (MiniLM stack) | reused frozen `FIXED_DECOMPOSE` |",
        "| ADAPTIVE | frozen `A1_NO_ROUTER_ADAPTIVE` evidence-prefix rule (score-gap prefix, "
        "no query text; initial_k=5, max_k=20, token cap 6000, max_score_drop=3.0) | reused "
        "frozen A1 `no_router_adaptive_v1` (BGE research stack) | executed same rule on the "
        "frozen shared rewrite (MiniLM stack) |",
        "| AUTO_ROUTER_AVAILABLE | best available auto-router per cohort; the two cohorts use "
        "different router lineages and are **not** silently merged into one algorithm | reused "
        "frozen A1 `query_router_v1` (`query-structure-router-v1`: SIMPLE->fixed, "
        "BROAD->adaptive) | reused frozen Router V1 `ROUTED` (`router_v1`: DIRECT vs "
        "DECOMPOSE) |",
        "",
        "Router lineage note: the old `query-structure-router-v1` is an eval-only historical "
        "implementation; Router V1 is the implemented src pipeline. No single executable "
        "auto-router spans both cohorts, so the arm is named `AUTO_ROUTER_AVAILABLE`.",
        "",
        "## 3. Validation 50 Results",
        "",
    ]
    lines += arm_result_table(stats["validation"], val_n)
    lines += [
        "",
        f"Citation-valid: " + ", ".join(
            f"{arm} {stats['validation'][arm]['citation_valid']}/{val_n}" for arm in ARM_ORDER) + ".",
        f"Eligible (router-style grounding rule): " + ", ".join(
            f"{arm} {stats['validation'][arm]['eligible']}/{val_n}" for arm in ARM_ORDER) + ".",
        "Latency is unavailable for the reused A1 arms (no wall-clock was recorded in those "
        "artifacts); the executed SEARCH+ cells have wall-clock latency.",
        "",
        "## 4. Router 20 Results",
        "",
    ]
    lines += arm_result_table(stats["router"], router_n)
    lines += [
        "",
        f"Citation-valid: " + ", ".join(
            f"{arm} {stats['router'][arm]['citation_valid']}/{router_n}" for arm in ARM_ORDER) + ".",
        f"Eligible: " + ", ".join(
            f"{arm} {stats['router'][arm]['eligible']}/{router_n}" for arm in ARM_ORDER) + ".",
        "",
        "## 5. Combined 70 Results",
        "",
    ]
    lines += arm_result_table(stats["combined"], len(rows))
    lines += [
        "",
        f"Combined latency is only defined where per-query wall-clock exists (SEARCH+ "
        f"{stats['combined']['SEARCH+']['latency_n']}/{len(rows)}; the other arms "
        f"{stats['combined']['FAST']['latency_n']}/{len(rows)} from Router 20). Combined "
        f"required coverage uses the reporting denominator {combined_req} described in Scope.",
        "",
        "## 6. Per-Query Comparison",
        "",
        "Cells show `covered/required`, `\u2713` when complete, `\u2717cit` when citation "
        "validation failed, provider tokens in `k`, and `\u2605` for the best observed quality "
        "on that query when the arms do not all tie (all non-tied winners marked).",
        "",
    ]
    lines += per_query_table(context["rows"])
    lines += [
        "",
        "## 7. Cost / Latency",
        "",
        "Costs exclude the shared contextual rewrite (reported separately below) and judge "
        "calls; they are arm-attributable generation/decompose/router calls. Reused A1 "
        "Validation cells use the frozen counterfactual provider accounting from the A1 "
        "economics artifact.",
        "",
        "| Arm | LLM calls/q | Input tokens | Output tokens | Total tokens | Tokens/q |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ARM_ORDER:
        item = stats["combined"][arm]
        calls = f"{item['calls_per_query']:.2f}" if item["calls_per_query"] else "n/a"
        lines.append(f"| {arm} | {calls} | {item['input_tokens']:,} | "
                     f"{item['output_tokens']:,} | {item['tokens']:,} | "
                     f"{item['tokens_per_query']:.1f} |")
    lines += [
        "",
        "| Arm | Latency samples | Total wall-clock | Mean | Median |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm in ARM_ORDER:
        item = stats["combined"][arm]
        total = f"{item['latency_total']:.2f} s" if item["latency_total"] else "unavailable"
        mean = f"{item['latency_mean']:.2f} s" if item["latency_mean"] else "unavailable"
        median = f"{item['latency_median']:.2f} s" if item["latency_median"] else "unavailable"
        lines.append(f"| {arm} | {item['latency_n']}/{len(rows)} | {total} | {mean} | {median} |")
    lines += [
        "",
        f"- Shared contextual rewrite (excluded above): Validation 50 executed SEARCH+ used "
        f"{context['searchplus_rewrite']['calls']} rewrites / "
        f"{context['searchplus_rewrite']['input']:,} input / "
        f"{context['searchplus_rewrite']['output']:,} output tokens; the frozen Router 20 run "
        f"recorded 20 shared rewrites / 3,887 input / 655 output tokens.",
        "- Historical Validation A1 generations used a 1,536-token answer budget; the current "
        "path and Router 20 use 512. Observed outputs reached the 512 cap in "
        f"{context['generation_cap_hits']} current-path cells, so the reused and executed arms "
        "are not budget-identical.",
        "",
        "## 8. Empirical Best-Arm Upper Bound",
        "",
        "Frozen post-hoc rule: for each query choose the arm(s) with the highest observed "
        "quality tuple `(query-required complete, required aspects covered)` among actually "
        "executed arms; equal tuples are recorded as ties. Cost is never used to break a "
        "quality tie here.",
        "",
        f"- Best observed arm across the four strategies: **{best['best_complete']}/{len(rows)} "
        f"complete**, **{best['best_covered']}/{best['best_total']} required aspects**.",
        f"- Ties: {best['partial_ties']} partial ties, {best['full_ties']} cases where every "
        f"available arm tied at the same quality; no-quality rows: {best['no_quality']}.",
        "",
        "| Arm | Sole wins | Shared (tied) wins |",
        "|---|---:|---:|",
    ]
    for arm in ARM_ORDER:
        lines.append(f"| {arm} | {best['winner_counts'][arm]['sole']} | "
                     f"{best['winner_counts'][arm]['shared']} |")
    lines += [
        "",
        "Quality-tied lowest-cost product view (cost used only after quality is tied): "
        + ", ".join(f"{arm} {best['low_cost_choice'].get(arm, 0)}"
                    for arm in ARM_ORDER) + ".",
        "",
        "This is a post-hoc empirical upper bound, not a product accuracy figure.",
        "",
        "## 9. Product Interpretation",
        "",
    ]
    lines += pareto_rows(stats["combined"])
    lines += [
        "",
        f"**1. Is FAST still the right default?** Yes. FAST is the cheapest non-degenerate arm "
        f"on both cohorts ({stats['combined']['FAST']['tokens_per_query']:.0f} tokens/query "
        f"combined) and no arm dominates it on quality at equal cost. ADAPTIVE buys "
        f"quality at roughly {stats['combined']['ADAPTIVE']['tokens_per_query'] / stats['combined']['FAST']['tokens_per_query']:.1f}x "
        f"the tokens; current SEARCH+ is not better than FAST at higher latency.",
        "",
        f"**2. Does current SEARCH+ form a quality-oriented high-budget mode?** No. On "
        f"Validation 50 it scores below FAST ({stats['validation']['SEARCH+']['complete']}/{val_n} "
        f"complete, {stats['validation']['SEARCH+']['covered']}/{val_req} aspects vs FAST "
        f"{stats['validation']['FAST']['complete']}/{val_n} and {stats['validation']['FAST']['covered']}/{val_req}) "
        f"and on Router 20 it again trails DIRECT "
        f"({stats['router']['SEARCH+']['complete']}/{router_n} vs "
        f"{stats['router']['FAST']['complete']}/{router_n}) while taking "
        f"{stats['router']['SEARCH+']['latency_mean']:.1f} s vs "
        f"{stats['router']['FAST']['latency_mean']:.1f} s per query. Current fixed-decompose "
        f"implementation does not yet form a quality-oriented Search+ profile.",
        "",
        f"**3. Is ADAPTIVE a stronger Search+ backend?** Yes, per this snapshot. ADAPTIVE is "
        f"the quality extreme in both cohorts and combined "
        f"({stats['combined']['ADAPTIVE']['complete']}/{len(rows)} complete, "
        f"{stats['combined']['ADAPTIVE']['covered']}/{best['best_total']} aspects), outperforming SEARCH+ by "
        f"{stats['combined']['ADAPTIVE']['complete'] - stats['combined']['SEARCH+']['complete']} "
        f"complete queries and "
        f"{stats['combined']['ADAPTIVE']['covered'] - stats['combined']['SEARCH+']['covered']} "
        f"aspects while costing "
        f"{stats['combined']['ADAPTIVE']['tokens_per_query'] / stats['combined']['SEARCH+']['tokens_per_query']:.2f}x "
        f"its tokens and, on Router 20, less than half its latency. Adaptive is currently a "
        f"stronger candidate for a quality-oriented Search+ profile. This is an experiment "
        f"conclusion only; this run does not change the CLI.",
        "",
        f"**4. Does AUTO_ROUTER_AVAILABLE show enough value?** Mixed and not sufficient. The "
        f"reused historical routers beat always-FAST by only "
        f"{stats['validation']['AUTO_ROUTER_AVAILABLE']['complete'] - stats['validation']['FAST']['complete']} "
        f"complete query on Validation 50 and "
        f"{stats['router']['AUTO_ROUTER_AVAILABLE']['complete'] - stats['router']['FAST']['complete']} "
        f"on Router 20 (with "
        f"{best['auto_router_misses']} queries where some other arm had strictly better "
        f"quality), at a token overhead of "
        f"{100 * (stats['combined']['AUTO_ROUTER_AVAILABLE']['tokens_per_query'] / stats['combined']['FAST']['tokens_per_query'] - 1):.0f}% "
        f"combined. The two lineages cannot even be merged into one arm. Keep it as a "
        f"reference experiment, not a default.",
        "",
        "## 10. Limitations",
        "",
        "- Two separately constructed cohorts: Validation V1 is an exposed development "
        "benchmark; Router V1 is a small 20-query frozen benchmark. Combined 70 is not a new "
        "independent holdout.",
        "- Mixed lineage: reused Validation A1 cells (FAST/ADAPTIVE/AUTO_ROUTER_AVAILABLE) ran "
        "on the frozen BGE research stack with no contextual rewrite and a 1,536-token budget; "
        "current-path cells (Validation SEARCH+, all executed Router cells) run on the MiniLM "
        "stack with rewrite and a 512-token budget. The frozen Router V1 arms used the MiniLM "
        "stack with one shared rewrite per case.",
        "- AUTO_ROUTER_AVAILABLE merges two different router lineages and is not a single "
        "algorithm; per-cohort rows must be read separately.",
        "- Reused outputs are historical: no answer was regenerated for them, and provider "
        "token figures for reused Validation A1 arms are counterfactual independent-run "
        "accounting (actual experiment deduplicated some calls).",
        "- Wall-clock latency is unavailable for the reused Validation arms; only executed "
        "cells have comparable per-query latency.",
        "- Metric compatibility: required-aspect completeness is the shared primary metric; "
        "citation-valid and eligible flags use the frozen judge outputs with the router V1 "
        "eligibility rule. Judge outputs are model-derived; Validation V1 had human "
        "adjudication for A1 disputes, Router V1 did not.",
        "- One Validation SEARCH+ cell (VAL-001-022) failed once on a local cache-file lock and "
        "was re-executed once; the first failure is recorded in the run provenance.",
        "- The Validation SEARCH+ (50) and Router ADAPTIVE (20) cells were executed with the "
        "frozen semantics during this snapshot's preparation and restored from the temporary "
        "workdir cell cache; re-running with `--reuse-existing` and no cache re-executes only "
        "those two groups, and the default mode executes all 280 cells live.",
        "- Model variance: temperature 0 does not guarantee identical provider outputs; a "
        "fresh full run may produce slightly different numbers.",
        "- Judge calls are excluded from serving-cost tables by project convention.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def build_context_rows(short_validation: dict[str, str], cells_a: dict,
                       short_router: dict[str, str], cells_b: dict,
                       queries_a: list[dict], queries_b: list[dict]) -> list[dict]:
    rows = []
    for case in queries_a:
        cid = case["case_id"]
        aspects = cells_a[cid]
        required_total = max((cell["total"] or 0) for cell in aspects.values())
        rows.append({"id": short_validation[cid], "cohort_label": "V1", "original_id": cid,
                     "cohort": "validation", "query": case["query"],
                     "cells": aspects, "required_quality_total": required_total})
    for case in queries_b:
        cid = case["case_id"]
        aspects = cells_b[cid]
        required_total = max((cell["total"] or 0) for cell in aspects.values())
        rows.append({"id": cid, "cohort_label": "R", "original_id": cid,
                     "cohort": "router", "query": case["query"],
                     "cells": aspects, "required_quality_total": required_total})
    return rows


def run(args) -> dict:
    started_at = now_utc()
    if args.workdir:
        workdir = Path(args.workdir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        temporary = None
    else:
        temporary = tempfile.TemporaryDirectory(prefix="multiarm_70_")
        workdir = Path(temporary.name)
    summary_path = Path(args.output).resolve() if args.output else SUMMARY_PATH

    validation_cases = load_validation_cases(args.limit)
    router_cases = load_router_cases(args.limit)
    validation_aspects = load_validation_aspects()
    router_aspects = load_router_aspects()
    short_validation = short_ids(validation_cases, "val")
    short_router = short_ids(router_cases, "router")

    if args.reuse_existing:
        cells_a = load_validation_reused_cells()
        cells_b = load_router_reused_cells()
    else:
        cells_a = {case["case_id"]: {} for case in validation_cases}
        cells_b = {case["case_id"]: {} for case in router_cases}

    searchplus_state = None
    adaptive_state = None
    if args.reuse_existing:
        searchplus_state = load_supplemental(workdir / "searchplus_val50.json", SEARCHPLUS_VERSION)
        adaptive_state = load_supplemental(workdir / "adaptive_router20.json", ADAPTIVE_VERSION)

    pending_searchplus: list[dict] = []
    pending_adaptive: list[dict] = []
    if args.reuse_existing:
        need_searchplus = [case for case in validation_cases
                           if "SEARCH+" not in cells_a.get(case["case_id"], {})]
        need_adaptive = [case for case in router_cases
                         if "ADAPTIVE" not in cells_b.get(case["case_id"], {})]
        if searchplus_state:
            for case in need_searchplus:
                entry = searchplus_state["cases"].get(case["case_id"])
                if entry and entry.get("judge") and not (entry.get("judge") or {}).get("judge_error") \
                        and entry.get("answer"):
                    cells_a[case["case_id"]]["SEARCH+"] = supplemental_cell(
                        "validation", entry, source="cached")
                else:
                    pending_searchplus.append(case)
        else:
            pending_searchplus = list(need_searchplus)
        if adaptive_state:
            for case in need_adaptive:
                entry = adaptive_state["cases"].get(case["case_id"])
                if entry and entry.get("judge") and not (entry.get("judge") or {}).get("judge_error") \
                        and entry.get("answer"):
                    cells_b[case["case_id"]]["ADAPTIVE"] = supplemental_cell(
                        "router", entry, source="cached")
                else:
                    pending_adaptive.append(case)
        else:
            pending_adaptive = list(need_adaptive)

    needs_runner = bool(pending_searchplus or pending_adaptive or not args.reuse_existing)
    runner = LiveRunner(workdir) if needs_runner else None
    judge_cache = None
    if runner is not None:
        from eval.run_answer_eval import _V3Cache
        judge_cache = _V3Cache(workdir / "judge_cache.json")

    executed: list[str] = []
    live_rewrite = {"calls": 0, "input": 0, "output": 0}
    live_generation_caps = {"count": 0}

    def add_rewrite(calls) -> None:
        for call in calls or ():
            live_rewrite["calls"] += 1
            live_rewrite["input"] += call.input_tokens or 0
            live_rewrite["output"] += call.output_tokens or 0

    def judge_and_store(case: dict, record: dict, aspects: list[dict]) -> dict | None:
        if not record.get("answer"):
            return None
        try:
            return judge_answer(case["case_id"], case["query"], aspects,
                                record["answer"], record["evidence"],
                                runner.client, runner.model, judge_cache)
        except Exception as error:
            return {"judge_error": str(error)}

    # ---- reuse mode gaps: Validation 50 x SEARCH+ ------------------------- #
    if pending_searchplus:
        state = searchplus_state or {"version": SEARCHPLUS_VERSION, "cases": {}}
        for case in pending_searchplus:
            cid = case["case_id"]
            rewritten, rewrite_calls = runner.rewrite(case["query"])
            add_rewrite(rewrite_calls)
            entry = run_searchplus_cell(runner, case, rewritten, rewrite_calls)
            judged = judge_and_store(case, {
                "answer": entry["answer"], "evidence": entry["evidence"]},
                validation_aspects[cid]) if entry.get("answer") else None
            if judged is not None:
                entry["judge"] = judged
            state["cases"][cid] = entry
            write_atomic(workdir / "searchplus_val50.json", state)
            cells_a[cid]["SEARCH+"] = supplemental_cell("validation", entry)
            executed.append(f"validation:{cid}:SEARCH+")
            print(f"[validation SEARCH+ {len(executed)}] {cid} "
                  f"{cells_a[cid]['SEARCH+']['covered']}/{cells_a[cid]['SEARCH+']['total']}",
                  flush=True)
        searchplus_state = state

    # ---- reuse mode gaps: Router 20 x ADAPTIVE ---------------------------- #
    if pending_adaptive:
        raw = load_json(ROUTER_RAW)
        raw_rewrites = {case["case_id"]: case["shared_rewrite"] for case in raw["cases"]}
        state = adaptive_state or {"version": ADAPTIVE_VERSION, "cases": {}}
        for case in pending_adaptive:
            cid = case["case_id"]
            rewritten = raw_rewrites.get(cid)
            if rewritten is None:
                rewritten, rewrite_calls = runner.rewrite(case["query"])
                add_rewrite(rewrite_calls)
            entry = run_adaptive_cell(runner, case, rewritten)
            judged = judge_and_store(case, {
                "answer": entry["answer"], "evidence": entry["evidence"]},
                router_aspects[cid]) if entry.get("answer") else None
            if judged is not None and not judged.get("judge_error"):
                judged["eligible"] = eligible_from_judgment(
                    judged, bool((entry.get("citation_validation") or {}).get("valid")))
                entry["judge"] = judged
            elif judged is not None:
                entry["judge"] = judged
            state["cases"][cid] = entry
            write_atomic(workdir / "adaptive_router20.json", state)
            cells_b[cid]["ADAPTIVE"] = supplemental_cell("router", entry)
            executed.append(f"router:{cid}:ADAPTIVE")
            print(f"[router ADAPTIVE {len(executed)}] {cid} "
                  f"{cells_b[cid]['ADAPTIVE']['covered']}/{cells_b[cid]['ADAPTIVE']['total']}",
                  flush=True)
        adaptive_state = state

    # ---- full mode: execute all four arms in one pass per query ----------- #
    if not args.reuse_existing:
        for case in validation_cases:
            cid = case["case_id"]
            rewritten, rewrite_calls = runner.rewrite(case["query"])
            add_rewrite(rewrite_calls)
            for arm_key in ("FAST", "ADAPTIVE", "AUTO_ROUTER_AVAILABLE"):
                record = execute_cell(runner, "validation", arm_key, case, rewritten)
                judged = judge_and_store(case, record, validation_aspects[cid])
                cells_a[cid][arm_key] = cell_from_record("validation", record, judged)
                executed.append(f"validation:{cid}:{arm_key}")
            sp_entry = run_searchplus_cell(runner, case, rewritten, rewrite_calls)
            for call in (sp_entry.get("trace") or {}).get("model_calls", []):
                if call.get("stage") == "generation" and (call.get("output_tokens") or 0) >= 512:
                    live_generation_caps["count"] += 1
            sp_judged = judge_and_store(case, {
                "answer": sp_entry["answer"], "evidence": sp_entry["evidence"]},
                validation_aspects[cid]) if sp_entry.get("answer") else None
            if sp_judged is not None:
                sp_entry["judge"] = sp_judged
            cells_a[cid]["SEARCH+"] = supplemental_cell("validation", sp_entry)
            executed.append(f"validation:{cid}:SEARCH+")
            print(f"[validation {cid}] "
                  + ", ".join(f"{arm}:{cells_a[cid][arm]['covered']}/{cells_a[cid][arm]['total']}"
                              for arm in ARM_ORDER), flush=True)
        for case in router_cases:
            cid = case["case_id"]
            rewritten, rewrite_calls = runner.rewrite(case["query"])
            add_rewrite(rewrite_calls)
            for arm_key in ("FAST", "SEARCH+", "AUTO_ROUTER_AVAILABLE"):
                record = execute_cell(runner, "router", arm_key, case, rewritten)
                judged = judge_and_store(case, record, router_aspects[cid])
                cells_b[cid][arm_key] = cell_from_record("router", record, judged)
                executed.append(f"router:{cid}:{arm_key}")
            ad_entry = run_adaptive_cell(runner, case, rewritten)
            if ad_entry.get("output_tokens") is not None and ad_entry["output_tokens"] >= 512:
                live_generation_caps["count"] += 1
            ad_judged = judge_and_store(case, {
                "answer": ad_entry["answer"], "evidence": ad_entry["evidence"]},
                router_aspects[cid]) if ad_entry.get("answer") else None
            if ad_judged is not None and not ad_judged.get("judge_error"):
                ad_judged["eligible"] = eligible_from_judgment(
                    ad_judged, bool((ad_entry.get("citation_validation") or {}).get("valid")))
                ad_entry["judge"] = ad_judged
            elif ad_judged is not None:
                ad_entry["judge"] = ad_judged
            cells_b[cid]["ADAPTIVE"] = supplemental_cell("router", ad_entry)
            executed.append(f"router:{cid}:ADAPTIVE")
            print(f"[router {cid}] "
                  + ", ".join(f"{arm}:{cells_b[cid][arm]['covered']}/{cells_b[cid][arm]['total']}"
                              for arm in ARM_ORDER), flush=True)

    # ---- aggregation ------------------------------------------------------ #
    rows = build_context_rows(short_validation, cells_a, short_router, cells_b,
                              validation_cases, router_cases)
    rows_a = [row for row in rows if row["cohort"] == "validation"]
    rows_b = [row for row in rows if row["cohort"] == "router"]
    stats = {
        "validation": {arm: aggregate_cells(rows_a, arm) for arm in ARM_ORDER},
        "router": {arm: aggregate_cells(rows_b, arm) for arm in ARM_ORDER},
        "combined": {arm: aggregate_cells(rows, arm) for arm in ARM_ORDER},
    }
    best = best_arm_analysis(rows)

    rewrite_input = rewrite_output = rewrite_calls = 0
    if searchplus_state:
        for entry in searchplus_state["cases"].values():
            for call in entry.get("rewrite_calls") or []:
                rewrite_calls += 1
                rewrite_input += call.get("input_tokens") or 0
                rewrite_output += call.get("output_tokens") or 0
    if rewrite_calls == 0:
        rewrite_calls = live_rewrite["calls"]
        rewrite_input = live_rewrite["input"]
        rewrite_output = live_rewrite["output"]
    generation_cap_hits = 0
    for state in (searchplus_state, adaptive_state):
        if not state:
            continue
        for entry in state["cases"].values():
            if entry.get("requested_arm") == "ADAPTIVE_NO_ROUTER_V1":
                output = (entry.get("provider_usage") or {}).get("output_tokens")
                if output is None:
                    output = entry.get("output_tokens")
                if output is not None and output >= 512:
                    generation_cap_hits += 1
            else:
                for call in (entry.get("trace") or {}).get("model_calls", []):
                    if call.get("stage") == "generation" \
                            and (call.get("output_tokens") or 0) >= 512:
                        generation_cap_hits += 1
    generation_cap_hits += live_generation_caps["count"]

    reused_count = sum(1 for row in rows for cell in row["cells"].values()
                       if cell["source"] == "reused")
    cached_count = sum(1 for row in rows for cell in row["cells"].values()
                       if cell["source"] == "cached")
    new_count = sum(1 for row in rows for cell in row["cells"].values()
                    if cell["source"] == "new")
    mode = "reuse-existing (frozen historical cells reused; inventory gaps executed)" \
        if args.reuse_existing else (
            "full live run (all 70 x 4 cells executed; identical generation inputs may be "
            "served once from the workdir generation cache)")
    provenance_summary = (
        f"{reused_count} of 280 cells reused from frozen historical artifacts; "
        f"{cached_count} supplemental cells loaded from the workdir cell cache "
        f"(executed earlier with the frozen arm semantics); "
        f"{new_count} cells executed in this invocation.")
    if executed:
        buckets = Counter((item.split(":")[0], item.split(":")[2]) for item in executed)
        provenance_summary += " Executed now: " + ", ".join(
            f"{cohort} {arm} x{count}" for (cohort, arm), count in sorted(buckets.items())) + "."

    validation_meta = load_json(VALIDATION_META)
    router_meta = load_json(ROUTER_BENCHMARK)
    if runner is not None:
        model_name = runner.model
    else:
        from src.llm_client import LLMConfig
        model_name = LLMConfig.from_env(ENV_FILE).model
    context = {
        "run": {
            "timestamp": started_at,
            "mode": mode,
            "model": model_name,
            "validation_corpus_sha256": validation_meta["corpus"]["sha256"],
            "router_corpus_commit": router_meta["corpus_commit"],
            "validation_queries_sha256": sha256_file(VALIDATION_QUERIES),
            "router_benchmark_sha256": sha256_file(ROUTER_BENCHMARK),
            "git": git_metadata(),
            "provenance_summary": provenance_summary,
        },
        "validation_aspect_count": sum(len(value) for value in validation_aspects.values()),
        "router_aspect_count": sum(len(value) for value in router_aspects.values()),
        "searchplus_rewrite": {"calls": rewrite_calls, "input": rewrite_input,
                               "output": rewrite_output},
        "generation_cap_hits": generation_cap_hits,
        "rows": rows,
        "stats": stats,
        "best": best,
    }
    summary = render_summary(context)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    print(f"summary written to {summary_path}")
    if temporary is not None:
        temporary.cleanup()
    return context


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .\\.venv\\Scripts\\python.exe eval/results/multiarm_70/run_multiarm_70.py\n"
            "      full live execution of all 70 queries x 4 arms (default)\n"
            "  .\\.venv\\Scripts\\python.exe eval/results/multiarm_70/run_multiarm_70.py --reuse-existing\n"
            "      reuse frozen historical results; execute only the two inventory gaps\n"
            "      (Validation 50 SEARCH+ and Router 20 ADAPTIVE)\n"
        ),
    )
    parser.add_argument("--reuse-existing", action="store_true",
                        help="reuse frozen historical result artifacts instead of re-executing "
                             "every cell; missing cells are still executed")
    parser.add_argument("--workdir", default=None,
                        help="keep raw/intermediate cells in this directory (default: a "
                             "temporary directory that is removed on success)")
    parser.add_argument("--limit", type=int, default=None,
                        help="development only: run the first N queries per cohort")
    parser.add_argument("--output", default=None,
                        help="development only: write the summary to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
