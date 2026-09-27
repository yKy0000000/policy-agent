"""Router V1 frozen evaluation: blind answer judging, oracle comparison.

Reuses the frozen answer-judge protocol from eval/run_answer_eval.py. Answers
are judged one case at a time under opaque labels assigned in a deterministic
hashed order; the judge never sees arm identity.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import EvidenceSource  # noqa: E402
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient  # noqa: E402
from eval.run_answer_eval import (  # noqa: E402
    V3_JUDGE_MAX_TOKENS,
    V3_JUDGE_VERSION,
    _judge_messages,
    _parse_judge,
)

RESULT_DIR = PROJECT_ROOT / "eval" / "results" / "router_v1"
RAW_PATH = RESULT_DIR / "raw" / "router_v1_raw_results.json"
TRUTH_PATH = PROJECT_ROOT / "eval" / "router_v1_required_aspects.json"
JUDGE_CACHE_PATH = RESULT_DIR / "judge_cache.json"
ARMS = ("FIXED_DIRECT", "FIXED_DECOMPOSE", "ROUTED")
DISQUALIFYING_CLAIM_SUPPORT = {"unsupported", "contradicted", "partial", "uncertain"}
DISQUALIFYING_CLAIM_CITATION = {"unsupported", "missing", "uncertain"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_judge_cache() -> dict:
    return load_json(JUDGE_CACHE_PATH) if JUDGE_CACHE_PATH.exists() else {}


def save_judge_cache(cache: dict) -> None:
    JUDGE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = JUDGE_CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(JUDGE_CACHE_PATH)


def build_sources(evidence: list[dict]) -> list[EvidenceSource]:
    return [
        EvidenceSource(
            citation_id=f"S{index}",
            text=str(item["text"]),
            title=str(item["title"]),
            heading_path=tuple(str(value) for value in item["heading_path"]),
            source_url=str(item["source_url"]),
            source_path=str(item["source_path"]),
            chunk_id=str(item["chunk_id"]),
        )
        for index, item in enumerate(evidence, start=1)
    ]


def _shape_judgment(label: str, key: str, facts: list[dict], answer: dict) -> dict:
    aspect_status = {fact["fact_id"]: fact["status"] for fact in answer["facts"]}
    covered = sorted(fid for fid, status in aspect_status.items() if status == "covered")
    missing = sorted(fid for fid, status in aspect_status.items() if status == "missing")
    incorrect = sorted(fid for fid, status in aspect_status.items() if status == "incorrect")
    uncertain = sorted(fid for fid, status in aspect_status.items() if status == "uncertain")
    claim_counts: dict[str, int] = {}
    claim_citation_counts: dict[str, int] = {}
    for claim in answer["claims"]:
        claim_counts[claim["support_status"]] = claim_counts.get(claim["support_status"], 0) + 1
        claim_citation_counts[claim["citation_status"]] = claim_citation_counts.get(claim["citation_status"], 0) + 1
    return {
        "judge_label": label,
        "judge_key": key,
        "required_total": len(facts),
        "required_covered": len(covered),
        "covered_ids": covered,
        "missing_ids": missing,
        "incorrect_ids": incorrect,
        "uncertain_ids": uncertain,
        "query_required_complete": len(covered) == len(facts),
        "claim_counts": claim_counts,
        "claim_citation_counts": claim_citation_counts,
        "claims": answer["claims"],
    }


def judge_case(
    case_id: str,
    query: str,
    facts: list[dict],
    answers: dict[str, dict],
    client: OpenAIChatCompletionsClient,
    model: str,
    cache: dict,
    failures: dict,
) -> dict[str, dict]:
    """Judge all answerable arms for one case under opaque labels."""

    ordered = sorted(answers, key=lambda arm: sha256_text(f"{case_id}:{arm}"))
    label_to_arm = {chr(65 + index): arm for index, arm in enumerate(ordered)}
    judge_case_payload = {"case_id": case_id, "query": query, "facts": facts}
    labeled = {
        label: {
            "generation": {"answer": answers[arm]["answer"]},
            "sources": build_sources(answers[arm]["evidence"]),
        }
        for label, arm in label_to_arm.items()
    }
    messages = _judge_messages(judge_case_payload, labeled)
    key = sha256_text(json.dumps(
        {"case_id": case_id, "messages": messages, "model": model,
         "judge_version": V3_JUDGE_VERSION, "max_tokens": V3_JUDGE_MAX_TOKENS},
        sort_keys=True, ensure_ascii=False))
    entry = cache.get(key)
    if entry is None:
        raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
        try:
            parsed = _parse_judge(raw, set(labeled), {fact["fact_id"] for fact in facts})
        except Exception as error:
            failures[case_id] = {"mode": "batch", "error": str(error), "raw_response": raw,
                                 "labels": label_to_arm}
            return _judge_single_answers(case_id, query, facts, answers, client, model, cache, failures)
        entry = {"parsed": parsed, "usage": usage, "label_to_arm": label_to_arm}
        cache[key] = entry
        save_judge_cache(cache)
    parsed = cache[key]["parsed"]
    return {
        arm: _shape_judgment(label, key, facts, parsed[label])
        for label, arm in label_to_arm.items()
    }


def _judge_single_answers(
    case_id: str,
    query: str,
    facts: list[dict],
    answers: dict[str, dict],
    client: OpenAIChatCompletionsClient,
    model: str,
    cache: dict,
    failures: dict,
) -> dict[str, dict]:
    """Protocol-consistent fallback: one opaque-label call per answer."""

    out: dict[str, dict] = {}
    for arm, result in answers.items():
        judge_case_payload = {"case_id": case_id, "query": query, "facts": facts}
        labeled = {"A": {"generation": {"answer": result["answer"]},
                         "sources": build_sources(result["evidence"])}}
        messages = _judge_messages(judge_case_payload, labeled)
        key = sha256_text(json.dumps(
            {"case_id": case_id, "arm": arm, "messages": messages, "model": model,
             "judge_version": V3_JUDGE_VERSION, "max_tokens": V3_JUDGE_MAX_TOKENS},
            sort_keys=True, ensure_ascii=False))
        entry = cache.get(key)
        if entry is None:
            raw, usage = client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
            try:
                parsed = _parse_judge(raw, {"A"}, {fact["fact_id"] for fact in facts})
            except Exception as error:
                failures[f"{case_id}:{arm}"] = {"mode": "single", "error": str(error), "raw_response": raw}
                continue
            entry = {"parsed": parsed, "usage": usage}
            cache[key] = entry
            save_judge_cache(cache)
        out[arm] = _shape_judgment("A", key, facts, cache[key]["parsed"]["A"])
    return out


def eligibility(result: dict, judged: dict | None) -> bool:
    if not result.get("execution_success"):
        return False
    validation = result.get("citation_validation") or {}
    if not validation.get("valid"):
        return False
    if judged is None:
        return False
    if judged["incorrect_ids"]:
        return False
    if any(count for status, count in judged["claim_counts"].items()
           if status in DISQUALIFYING_CLAIM_SUPPORT):
        return False
    if any(count for status, count in judged["claim_citation_counts"].items()
           if status in DISQUALIFYING_CLAIM_CITATION):
        return False
    return True


def oracle_for_case(direct: dict, decompose: dict,
                    direct_judged: dict | None, decompose_judged: dict | None) -> dict[str, Any]:
    decompose_available = (
        decompose.get("executed_path") == "DECOMPOSE"
        and bool(decompose.get("counterfactual_decompose_available"))
    )
    if not decompose_available:
        return {"oracle": "ORACLE_UNAVAILABLE", "decompose_available": False,
                "direct_eligible": None, "decompose_eligible": None}
    direct_eligible = eligibility(direct, direct_judged)
    decompose_eligible = eligibility(decompose, decompose_judged)
    out = {"oracle": None, "decompose_available": True,
           "direct_eligible": direct_eligible, "decompose_eligible": decompose_eligible}
    if direct_eligible and not decompose_eligible:
        out["oracle"] = "FIXED_DIRECT"
    elif decompose_eligible and not direct_eligible:
        out["oracle"] = "FIXED_DECOMPOSE"
    elif not direct_eligible and not decompose_eligible:
        out["oracle"] = "NEITHER_ELIGIBLE"
    else:
        dc = bool(direct_judged and direct_judged["query_required_complete"])
        bc = bool(decompose_judged and decompose_judged["query_required_complete"])
        if dc and not bc:
            out["oracle"] = "FIXED_DIRECT"
        elif bc and not dc:
            out["oracle"] = "FIXED_DECOMPOSE"
        else:
            dcv = direct_judged["required_covered"] if direct_judged else 0
            bcv = decompose_judged["required_covered"] if decompose_judged else 0
            if dcv > bcv:
                out["oracle"] = "FIXED_DIRECT"
            elif bcv > dcv:
                out["oracle"] = "FIXED_DECOMPOSE"
            else:
                out["oracle"] = "TIE"
    return out


def aggregate_arm(entries: list[dict]) -> dict[str, Any]:
    judged = [entry for entry in entries if entry["status"] == "judged"]
    return {
        "attempts": len(entries),
        "judged": len(judged),
        "execution_success": sum(1 for entry in entries if entry["execution_success"]),
        "citation_valid": sum(1 for entry in entries
                              if (entry.get("citation_validation") or {}).get("valid")),
        "eligible": sum(1 for entry in entries if entry["eligible"]),
        "query_required_complete_cases": sum(1 for entry in judged if entry["query_required_complete"]),
        "required_covered_total": sum(entry["required_covered"] for entry in judged),
        "required_total_total": sum(entry["required_total"] for entry in judged),
        "failure_stages": {
            stage: sum(1 for entry in entries if entry.get("error_stage") == stage)
            for stage in sorted({entry.get("error_stage") for entry in entries if entry.get("error_stage")})
        },
    }


def main() -> int:
    raw = load_json(RAW_PATH)
    truth = load_json(TRUTH_PATH)
    truth_cases = {case["id"]: case for case in truth["cases"]}
    if len(raw["cases"]) != 20:
        raise SystemExit("raw results are incomplete")

    config = LLMConfig.from_env(PROJECT_ROOT / ".env")
    client = OpenAIChatCompletionsClient(config)
    cache = load_judge_cache()
    judge_failures: dict[str, dict] = {}
    failures_path = RESULT_DIR / "judge_failures.json"
    if failures_path.exists():
        judge_failures = load_json(failures_path)

    answer_eval: dict[str, Any] = {
        "version": "router_v1_answer_eval",
        "judge_version": V3_JUDGE_VERSION,
        "judge_model": config.model,
        "truth_path": "eval/router_v1_required_aspects.json",
        "truth_sha256": sha256_text(TRUTH_PATH.read_text(encoding="utf-8")),
        "blind": {"labels": "hashed opaque labels A..C per case", "arm_identity_exposed": False},
        "cases": {},
    }
    oracle: dict[str, Any] = {"version": "router_v1_oracle", "cases": {}}
    execution_summary: dict[str, Any] = {"version": "router_v1_execution_summary", "cases": {}}
    arm_entries: dict[str, list[dict]] = {arm: [] for arm in ARMS}

    for case_entry in raw["cases"]:
        case_id = case_entry["case_id"]
        query = case_entry["raw_query"]
        facts = [
            {"fact_id": aspect["aspect_id"], "fact": aspect["statement"]}
            for aspect in truth_cases[case_id]["required_aspects"]
        ]
        answers = {
            arm: case_entry["arms"][arm]
            for arm in ARMS
            if case_entry["arms"][arm].get("answer")
        }
        judged_by_arm: dict[str, dict] = {}
        if answers:
            judged_by_arm = judge_case(case_id, query, facts, answers, client, config.model, cache, judge_failures)
            write_json(failures_path, judge_failures)
            print(f"judged {case_id}: labels {json.dumps({a: j['judge_label'] for a, j in judged_by_arm.items()})}",
                  flush=True)
        case_eval: dict[str, Any] = {}
        case_exec: dict[str, Any] = {}
        for arm in ARMS:
            result = case_entry["arms"][arm]
            judged = judged_by_arm.get(arm)
            entry = {
                "status": "judged" if judged else ("unavailable" if not result.get("answer") else "judge_error"),
                "execution_success": result.get("execution_success"),
                "error_stage": result.get("error_stage"),
                "executed_path": result.get("executed_path"),
                "fallback_reason": result.get("fallback_reason"),
                "citation_validation": result.get("citation_validation"),
                "eligible": eligibility(result, judged),
            }
            if judged:
                entry.update({
                    "required_total": judged["required_total"],
                    "required_covered": judged["required_covered"],
                    "covered_ids": judged["covered_ids"],
                    "missing_ids": judged["missing_ids"],
                    "incorrect_ids": judged["incorrect_ids"],
                    "uncertain_ids": judged["uncertain_ids"],
                    "query_required_complete": judged["query_required_complete"],
                    "claim_counts": judged["claim_counts"],
                    "claim_citation_counts": judged["claim_citation_counts"],
                    "judge_label": judged["judge_label"],
                })
            case_eval[arm] = entry
            case_exec[arm] = {
                "executed_path": result.get("executed_path"),
                "execution_success": result.get("execution_success"),
                "error_stage": result.get("error_stage"),
                "fallback_reason": result.get("fallback_reason"),
                "decompose_available": result.get("decompose_available"),
                "counterfactual_decompose_available": result.get("counterfactual_decompose_available"),
            }
            arm_entries[arm].append(entry)
        answer_eval["cases"][case_id] = case_eval
        execution_summary["cases"][case_id] = case_exec
        direct_result = case_entry["arms"]["FIXED_DIRECT"]
        decompose_result = case_entry["arms"]["FIXED_DECOMPOSE"]
        case_oracle = oracle_for_case(
            direct_result, decompose_result,
            judged_by_arm.get("FIXED_DIRECT"), judged_by_arm.get("FIXED_DECOMPOSE"))
        case_oracle["direct_complete"] = bool(
            judged_by_arm.get("FIXED_DIRECT") and judged_by_arm["FIXED_DIRECT"]["query_required_complete"])
        case_oracle["decompose_complete"] = bool(
            judged_by_arm.get("FIXED_DECOMPOSE") and judged_by_arm["FIXED_DECOMPOSE"]["query_required_complete"])
        case_oracle["direct_covered"] = judged_by_arm.get("FIXED_DIRECT", {}).get("required_covered")
        case_oracle["decompose_covered"] = judged_by_arm.get("FIXED_DECOMPOSE", {}).get("required_covered")
        oracle["cases"][case_id] = case_oracle

    answer_eval["aggregate"] = {arm: aggregate_arm(arm_entries[arm]) for arm in ARMS}
    answer_eval["judge_failures"] = {
        key: {field: value for field, value in entry.items() if field != "raw_response"}
        for key, entry in judge_failures.items()
    }
    answer_eval["judge_failure_count"] = len(judge_failures)
    write_json(RESULT_DIR / "router_v1_answer_eval.json", answer_eval)
    write_json(RESULT_DIR / "router_v1_oracle.json", oracle)
    write_json(RESULT_DIR / "router_v1_execution_summary.json", execution_summary)
    print("answer evaluation, oracle, and execution summary written", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
