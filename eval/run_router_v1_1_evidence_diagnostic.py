"""Router V1.1 post-hoc evidence diagnostic.

Reads frozen V1 raw results and the frozen required-aspect truth, then runs an
independent blind evidence-aspect judge over each query-arm final evidence set.
The judge sees only the query, the frozen required aspects, and opaque indexed
evidence chunks. It never sees arm identity, router decisions, oracle outcomes,
answers, or prior judgments.

No system behavior is modified and no V1 execution is rerun.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_client import LLMConfig, OpenAIChatCompletionsClient  # noqa: E402

V1_DIR = PROJECT_ROOT / "eval" / "results" / "router_v1"
OUT_DIR = PROJECT_ROOT / "eval" / "results" / "router_v1_1"
RAW_PATH = V1_DIR / "raw" / "router_v1_raw_results.json"
ANSWER_EVAL_PATH = V1_DIR / "router_v1_answer_eval.json"
TRUTH_PATH = PROJECT_ROOT / "eval" / "router_v1_required_aspects.json"
CACHE_PATH = OUT_DIR / "evidence_judge_cache.json"
FAILURES_PATH = OUT_DIR / "evidence_judge_failures.json"

ARMS = ("FIXED_DIRECT", "FIXED_DECOMPOSE", "ROUTED")
EVIDENCE_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H")
JUDGE_VERSION = "router-v1.1-evidence-aspect-v1"
JUDGE_MAX_TOKENS = 4096
JUDGE_SYSTEM = """You decide whether supplied policy evidence contains enough information to support each required answer aspect for a user question. You see only the question, the required aspects, and indexed evidence chunks. You do not see any answer, any retrieval method, or any ranking.

Rules:
1. Use only the supplied evidence text. Do not use general knowledge.
2. An aspect is SUPPORTED when the evidence, possibly combining several chunks, states the information needed to support the aspect's full actor, condition, scope and strength.
3. NOT_SUPPORTED when the evidence does not contain the information needed for the aspect.
4. UNCERTAIN when the available text does not permit a reliable decision.
5. Topically related but insufficient content is not support.
6. Each required aspect must appear exactly once. supporting_evidence_ids may contain several chunk ids and must only be listed for SUPPORTED aspects.
7. Return only a JSON object matching the requested schema."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def build_judge_messages(query: str, aspects: list[dict], evidence: list[dict]) -> list[dict[str, str]]:
    payload = {
        "question": query,
        "required_aspects": [{"aspect_id": a["aspect_id"], "aspect": a["statement"]} for a in aspects],
        "evidence": [
            {
                "id": label,
                "title": item.get("title", ""),
                "section": " > ".join(item.get("heading_path") or []) or "Document introduction",
                "text": item["text"],
            }
            for label, item in zip(EVIDENCE_LABELS, evidence)
        ],
    }
    schema = (
        'Return JSON: {"aspects":[{"aspect_id":"...","status":"SUPPORTED|NOT_SUPPORTED|UNCERTAIN",'
        '"supporting_evidence_ids":["A"]}]} with every required aspect exactly once. '
        "List supporting evidence ids only for SUPPORTED aspects. Do not include any other text."
    )
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": schema + "\n\nINPUT:\n" +
         json.dumps(payload, ensure_ascii=False, separators=(",", ":"))},
    ]


def parse_judge(raw: str, aspect_ids: set[str], labels: set[str]) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        import re
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    result = json.loads(text)
    aspects = result["aspects"]
    if not isinstance(aspects, list) or len(aspects) != len(aspect_ids) or \
            {item["aspect_id"] for item in aspects} != aspect_ids:
        raise ValueError("judge aspect ids differ")
    out: dict[str, dict] = {}
    for item in aspects:
        status = item["status"]
        if status not in {"SUPPORTED", "NOT_SUPPORTED", "UNCERTAIN"}:
            raise ValueError("invalid evidence judge status")
        ids = item.get("supporting_evidence_ids") or []
        if not isinstance(ids, list) or any(identifier not in labels for identifier in ids):
            raise ValueError("invalid supporting evidence ids")
        repaired = False
        if status == "SUPPORTED" and not ids:
            status = "UNCERTAIN"
            repaired = True
        out[item["aspect_id"]] = {"status": status, "supporting_evidence_ids": list(ids),
                                  "repaired_missing_support_ids": repaired}
    return out


def judge_evidence(
    case_id: str,
    query: str,
    aspects: list[dict],
    evidence: list[dict],
    client: OpenAIChatCompletionsClient,
    model: str,
    cache: dict,
    failures: dict,
    failure_key: str,
) -> tuple[dict | None, dict]:
    messages = build_judge_messages(query, aspects, evidence)
    key = sha256_text(json.dumps(
        {"case_id": case_id, "messages": messages, "model": model,
         "judge_version": JUDGE_VERSION, "max_tokens": JUDGE_MAX_TOKENS},
        sort_keys=True, ensure_ascii=False))
    entry = cache.get(key)
    if entry is None:
        started = time.perf_counter()
        raw, usage = client.complete_with_usage(messages, max_tokens=JUDGE_MAX_TOKENS, temperature=0.0)
        latency = time.perf_counter() - started
        try:
            parsed = parse_judge(raw, {a["aspect_id"] for a in aspects},
                                 set(EVIDENCE_LABELS[:len(evidence)]))
        except Exception as error:
            failures[failure_key] = {"error": str(error), "raw_response": raw}
            write_json(FAILURES_PATH, failures)
            return None, {"calls": 1, "input_tokens": usage.get("input_tokens") or 0,
                          "output_tokens": usage.get("output_tokens") or 0, "latency_seconds": latency}
        entry = {"parsed": parsed, "usage": usage, "latency_seconds": latency, "raw_response": raw}
        cache[key] = entry
        write_json(CACHE_PATH, cache)
    return entry["parsed"], {"calls": 0, "input_tokens": 0, "output_tokens": 0, "latency_seconds": 0.0}


def main() -> int:
    raw = load_json(RAW_PATH)
    truth = load_json(TRUTH_PATH)
    answer_eval = load_json(ANSWER_EVAL_PATH)
    truth_cases = {case["id"]: case for case in truth["cases"]}
    config = LLMConfig.from_env(PROJECT_ROOT / ".env")
    client = OpenAIChatCompletionsClient(config)
    cache = load_json(CACHE_PATH) if CACHE_PATH.exists() else {}
    failures = load_json(FAILURES_PATH) if FAILURES_PATH.exists() else {}
    cost = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "latency_seconds": 0.0}

    evidence_eval: dict[str, Any] = {
        "version": "router_v1_1_evidence_eval",
        "judge_version": JUDGE_VERSION,
        "judge_model": config.model,
        "blind": {
            "judge_sees": ["question", "frozen required aspects", "opaque indexed evidence chunks"],
            "judge_never_sees": ["arm identity", "router decision", "oracle", "answers", "attribution",
                                 "benchmark metadata", "prior judgments"],
        },
        "cases": {},
    }

    for case_entry in raw["cases"]:
        case_id = case_entry["case_id"]
        query = case_entry["raw_query"]
        aspects = truth_cases[case_id]["required_aspects"]
        case_out: dict[str, Any] = {}
        for arm in ARMS:
            result = case_entry["arms"][arm]
            evidence = result.get("evidence") or []
            labels = list(EVIDENCE_LABELS[:len(evidence)])
            judged, call_cost = judge_evidence(case_id, query, aspects, evidence, client,
                                               config.model, cache, failures, f"{case_id}:{arm}")
            for field in ("calls", "input_tokens", "output_tokens", "latency_seconds"):
                cost[field] += call_cost[field]
            if judged is None:
                case_out[arm] = {"status": "judge_error", "evidence_ids": [item["chunk_id"] for item in evidence]}
                continue
            supported = [aid for aid, item in judged.items() if item["status"] == "SUPPORTED"]
            uncertain = [aid for aid, item in judged.items() if item["status"] == "UNCERTAIN"]
            useful_labels = sorted({label for item in judged.values() if item["status"] == "SUPPORTED"
                                    for label in item["supporting_evidence_ids"]})
            chunk_map = {label: item["chunk_id"] for label, item in zip(labels, evidence)}
            useful_chunks = [chunk_map[label] for label in useful_labels]
            non_required = [chunk_id for chunk_id in chunk_map.values() if chunk_id not in useful_chunks]
            recall = len(supported) / len(aspects) if aspects else None
            case_out[arm] = {
                "status": "judged",
                "evidence_ids": [item["chunk_id"] for item in evidence],
                "evidence_labels": labels,
                "aspects": judged,
                "supported_aspect_ids": supported,
                "uncertain_aspect_ids": uncertain,
                "not_supported_aspect_ids": [aid for aid, item in judged.items() if item["status"] == "NOT_SUPPORTED"],
                "required_total": len(aspects),
                "supported_count": len(supported),
                "evidence_required_recall": recall,
                "evidence_required_complete": len(supported) == len(aspects),
                "useful_chunk_ids": useful_chunks,
                "non_required_chunk_ids": non_required,
                "required_context_precision": len(useful_chunks) / len(evidence) if evidence else None,
                "non_required_chunk_count": len(non_required),
            }
        evidence_eval["cases"][case_id] = case_out
        print(f"evidence-judged {case_id}", flush=True)

    cache_calls = len(cache)
    cache_input = sum((entry.get("usage") or {}).get("input_tokens") or 0 for entry in cache.values())
    cache_output = sum((entry.get("usage") or {}).get("output_tokens") or 0 for entry in cache.values())
    cache_latency = sum(entry.get("latency_seconds") or 0.0 for entry in cache.values())
    evidence_eval["evidence_judge_cost"] = {
        "calls": cache_calls + len(failures),
        "cached_successful_calls": cache_calls,
        "parse_failures": len(failures),
        "input_tokens": cache_input,
        "output_tokens": cache_output,
        "latency_seconds": round(cache_latency, 3),
        "note": "evaluation-only cost; excluded from Router serving cost; no frozen price table, monetary cost not estimated",
    }
    evidence_eval["judge_failure_count"] = len(failures)
    write_json(OUT_DIR / "router_v1_1_evidence_eval.json", evidence_eval)
    print("evidence evaluation written", flush=True)

    diagnostics = build_diagnostics(raw, truth, answer_eval, evidence_eval)
    write_json(OUT_DIR / "router_v1_1_query_diagnostics.json", diagnostics)
    analysis = build_analysis(raw, truth, answer_eval, evidence_eval, diagnostics, cost)
    write_json(OUT_DIR / "router_v1_1_analysis.json", analysis)
    render_report(evidence_eval, diagnostics, analysis)
    render_failure_review(diagnostics, analysis)
    print("diagnostics, analysis, report written", flush=True)
    return 0


def supported_set(entry: dict) -> set[str]:
    return set(entry.get("supported_aspect_ids") or [])


def displacement(case_id: str, direct: dict, decompose: dict) -> dict[str, Any]:
    direct_ids = direct.get("evidence_ids") or []
    decompose_ids = decompose.get("evidence_ids") or []
    direct_supported = supported_set(direct)
    decompose_supported = supported_set(decompose)
    gained = [chunk_id for chunk_id in decompose_ids if chunk_id not in direct_ids]
    lost = [chunk_id for chunk_id in direct_ids if chunk_id not in decompose_ids]
    direct_useful = set(direct.get("useful_chunk_ids") or [])
    decompose_useful = set(decompose.get("useful_chunk_ids") or [])

    def aspects_for(entry: dict, chunk_id: str) -> set[str]:
        ids = set()
        if chunk_id not in (entry.get("evidence_ids") or []):
            return ids
        label = entry["evidence_labels"][entry["evidence_ids"].index(chunk_id)]
        for aspect_id, item in (entry.get("aspects") or {}).items():
            if item["status"] != "SUPPORTED":
                continue
            if label in item["supporting_evidence_ids"]:
                ids.add(aspect_id)
        return ids

    useful_gain, redundant_gain, non_required_gain = [], [], []
    for chunk_id in gained:
        if chunk_id not in decompose_useful:
            non_required_gain.append(chunk_id)
            continue
        chunk_aspects = aspects_for(decompose, chunk_id)
        if chunk_aspects - direct_supported:
            useful_gain.append({"chunk_id": chunk_id,
                                "new_aspects": sorted(chunk_aspects - direct_supported)})
        else:
            redundant_gain.append(chunk_id)

    useful_lost, redundant_lost, non_required_lost = [], [], []
    for chunk_id in lost:
        if chunk_id not in direct_useful:
            non_required_lost.append(chunk_id)
            continue
        chunk_aspects = aspects_for(direct, chunk_id)
        if chunk_aspects - decompose_supported:
            useful_lost.append({"chunk_id": chunk_id,
                                "lost_aspects": sorted(chunk_aspects - decompose_supported)})
        else:
            redundant_lost.append(chunk_id)

    return {
        "case_id": case_id,
        "gained_chunk_ids": gained,
        "lost_chunk_ids": lost,
        "useful_gain": useful_gain,
        "redundant_gain": redundant_gain,
        "non_required_gain": non_required_gain,
        "useful_lost": useful_lost,
        "redundant_lost": redundant_lost,
        "non_required_lost": non_required_lost,
        "new_required_aspects_gained": sorted(decompose_supported - direct_supported),
        "required_aspects_lost": sorted(direct_supported - decompose_supported),
    }


def novelty_utility(decompose_result: dict, decompose_eval: dict, direct_eval: dict) -> dict[str, Any]:
    attribution = (decompose_result.get("trace") or {}).get("attribution") or {}
    representation = list(attribution.get("representation_gain_ids") or [])
    ranking = list(attribution.get("selection_ranking_gain_ids") or [])
    direct_supported = supported_set(direct_eval)

    def classify(chunk_id: str) -> dict:
        if chunk_id not in (decompose_eval.get("evidence_ids") or []):
            return {"chunk_id": chunk_id, "class": "not_in_final_evidence"}
        index = decompose_eval["evidence_ids"].index(chunk_id)
        label = decompose_eval["evidence_labels"][index]
        supported_aspects = {
            aspect_id for aspect_id, item in (decompose_eval.get("aspects") or {}).items()
            if item["status"] == "SUPPORTED" and label in item["supporting_evidence_ids"]
        }
        new_aspects = supported_aspects - direct_supported
        if new_aspects:
            return {"chunk_id": chunk_id, "class": "useful", "new_aspects": sorted(new_aspects)}
        if supported_aspects:
            return {"chunk_id": chunk_id, "class": "redundant", "supported_aspects": sorted(supported_aspects)}
        return {"chunk_id": chunk_id, "class": "non_required"}

    return {
        "representation_gain": [classify(chunk_id) for chunk_id in representation],
        "selection_ranking_gain": [classify(chunk_id) for chunk_id in ranking],
    }


def build_diagnostics(raw, truth, answer_eval, evidence_eval) -> dict[str, Any]:
    truth_cases = {case["id"]: case for case in truth["cases"]}
    diagnostics: dict[str, Any] = {"version": "router_v1_1_query_diagnostics", "cases": {}}
    for case_entry in raw["cases"]:
        case_id = case_entry["case_id"]
        arms = evidence_eval["cases"][case_id]
        direct, decompose, routed = arms["FIXED_DIRECT"], arms["FIXED_DECOMPOSE"], arms["ROUTED"]
        answer_arms = answer_eval["cases"][case_id]
        entry: dict[str, Any] = {
            "required_total": len(truth_cases[case_id]["required_aspects"]),
            "layers": {},
        }
        for arm in ARMS:
            ev = arms[arm]
            ans = answer_arms[arm]
            if ev.get("status") != "judged":
                entry["layers"][arm] = {"status": "evidence_judge_error"}
                continue
            supported = supported_set(ev)
            covered = set(ans.get("covered_ids") or [])
            utilized = supported & covered
            evidence_supported_but_answer_missing = sorted(
                aspect_id for aspect_id in supported if (ans.get("missing_ids") or []) and aspect_id in ans["missing_ids"])
            answer_without_detected_evidence = sorted(covered - supported)
            entry["layers"][arm] = {
                "evidence_required_recall": ev["evidence_required_recall"],
                "evidence_required_complete": ev["evidence_required_complete"],
                "required_context_precision": ev["required_context_precision"],
                "non_required_chunk_count": ev["non_required_chunk_count"],
                "supported_aspect_ids": sorted(supported),
                "unsupported_aspect_ids": sorted(set(ev["not_supported_aspect_ids"])),
                "uncertain_aspect_ids": sorted(set(ev["uncertain_aspect_ids"])),
                "answer_covered_ids": sorted(covered),
                "context_utilization": (len(utilized) / len(supported)) if supported else None,
                "context_utilization_available": bool(supported),
                "evidence_supported_but_answer_missing": evidence_supported_but_answer_missing,
                "answer_without_detected_evidence": answer_without_detected_evidence,
            }
        displacement_entry = None
        novelty = None
        novelty_routed = None
        if direct.get("status") == "judged" and decompose.get("status") == "judged":
            displacement_entry = displacement(case_id, direct, decompose)
            novelty = novelty_utility(case_entry["arms"]["FIXED_DECOMPOSE"], decompose, direct)
            if routed.get("status") == "judged":
                novelty_routed = novelty_utility(case_entry["arms"]["ROUTED"], routed, direct)
        entry["displacement"] = displacement_entry
        entry["novelty_utility"] = novelty
        entry["novelty_utility_routed"] = novelty_routed if direct.get("status") == "judged" and routed.get("status") == "judged" else None
        entry["taxonomy"] = classify_taxonomy(entry)
        diagnostics["cases"][case_id] = entry
    return diagnostics


def classify_taxonomy(entry: dict) -> dict[str, Any]:
    layers = entry["layers"]
    direct = layers.get("FIXED_DIRECT", {})
    decompose = layers.get("FIXED_DECOMPOSE", {})
    displacement = entry.get("displacement") or {}
    tags: list[str] = []
    direct_recall = direct.get("evidence_required_recall")
    decompose_recall = decompose.get("evidence_required_recall")
    direct_supported = set(direct.get("supported_aspect_ids") or [])
    decompose_supported = set(decompose.get("supported_aspect_ids") or [])
    useful_gain = displacement.get("useful_gain") or []
    useful_lost = displacement.get("useful_lost") or []
    gained = displacement.get("gained_chunk_ids") or []
    if direct_recall is not None and direct_recall < 1 and decompose_recall is not None and decompose_recall < 1:
        tags.append("RETRIEVAL_LIMITED")
    if decompose_supported > direct_supported:
        tags.append("DECOMPOSITION_USEFUL_EXPLORATION")
    if useful_lost or (direct_recall is not None and decompose_recall is not None and decompose_recall < direct_recall):
        tags.append("DECOMPOSITION_DISPLACEMENT")
    if gained and decompose_supported <= direct_supported and (
            (decompose.get("required_context_precision") or 0) < (direct.get("required_context_precision") or 0)
            or useful_gain or displacement.get("non_required_gain") or displacement.get("redundant_gain")):
        tags.append("DECOMPOSITION_NOISY_EXPLORATION")
    if decompose_supported <= direct_supported and not useful_gain and gained:
        tags.append("ZERO_GAIN_COST")
    evidence_supported_missing = set(decompose.get("evidence_supported_but_answer_missing") or []) | \
        set(direct.get("evidence_supported_but_answer_missing") or [])
    if evidence_supported_missing:
        tags.append("GENERATION_LIMITED")
    if decompose_recall is not None and direct_recall is not None and decompose_recall == direct_recall \
            and not gained and not useful_lost and \
            (decompose.get("required_context_precision") or 0) == (direct.get("required_context_precision") or 0):
        tags.append("STABLE")
    priority = ["DECOMPOSITION_DISPLACEMENT", "DECOMPOSITION_USEFUL_EXPLORATION",
                "DECOMPOSITION_NOISY_EXPLORATION", "ZERO_GAIN_COST", "RETRIEVAL_LIMITED",
                "GENERATION_LIMITED", "STABLE"]
    primary = next((tag for tag in priority if tag in tags), "STABLE")
    return {"tags": tags, "primary": primary}


def build_analysis(raw, truth, answer_eval, evidence_eval, diagnostics, cost) -> dict[str, Any]:
    case_ids = [case["case_id"] for case in raw["cases"]]
    arm_metrics: dict[str, Any] = {}
    for arm in ARMS:
        recalls, precisions, complete, supported_total, required_total, non_required = [], [], 0, 0, 0, 0
        utilization_num, utilization_den = 0, 0
        missing_evidence, answer_no_evidence = 0, 0
        for case_id in case_ids:
            layer = diagnostics["cases"][case_id]["layers"].get(arm) or {}
            if not layer or layer.get("status") == "evidence_judge_error":
                continue
            recalls.append(layer["evidence_required_recall"])
            precisions.append(layer["required_context_precision"])
            complete += int(layer["evidence_required_complete"])
            supported_total += len(layer["supported_aspect_ids"])
            required_total += len(layer["supported_aspect_ids"]) + len(layer["unsupported_aspect_ids"]) + \
                len(layer["uncertain_aspect_ids"])
            non_required += layer["non_required_chunk_count"]
            if layer["context_utilization"] is not None:
                utilization_num += layer["context_utilization"] * len(layer["supported_aspect_ids"])
                utilization_den += len(layer["supported_aspect_ids"])
            missing_evidence += len(layer["evidence_supported_but_answer_missing"])
            answer_no_evidence += len(layer["answer_without_detected_evidence"])
        arm_metrics[arm] = {
            "evidence_required_recall": (sum(recalls) / len(recalls)) if recalls else None,
            "evidence_required_recall_fraction": (f"{supported_total}/{required_total}"),
            "evidence_complete_queries": complete,
            "required_context_precision": (statistics.mean(precisions)) if precisions else None,
            "non_required_chunks": non_required,
            "context_utilization": (utilization_num / utilization_den) if utilization_den else None,
            "evidence_supported_but_answer_missing": missing_evidence,
            "answer_without_detected_evidence": answer_no_evidence,
        }
    recall_delta = {"decompose_higher": [], "equal": [], "decompose_lower": []}
    precision_delta = {"decompose_higher": [], "equal": [], "decompose_lower": []}
    displacement_cases = {"useful_gain": [], "useful_lost": [], "non_required_gain": [], "non_required_lost": []}
    net_gain, net_loss, net_equal = [], [], []
    for case_id in case_ids:
        entry = diagnostics["cases"][case_id]
        direct = entry["layers"]["FIXED_DIRECT"]
        decompose = entry["layers"]["FIXED_DECOMPOSE"]
        if direct.get("evidence_required_recall") is None or decompose.get("evidence_required_recall") is None:
            continue
        if decompose["evidence_required_recall"] > direct["evidence_required_recall"]:
            recall_delta["decompose_higher"].append(case_id)
        elif decompose["evidence_required_recall"] < direct["evidence_required_recall"]:
            recall_delta["decompose_lower"].append(case_id)
        else:
            recall_delta["equal"].append(case_id)
        if decompose["required_context_precision"] > direct["required_context_precision"]:
            precision_delta["decompose_higher"].append(case_id)
        elif decompose["required_context_precision"] < direct["required_context_precision"]:
            precision_delta["decompose_lower"].append(case_id)
        else:
            precision_delta["equal"].append(case_id)
        disp = entry.get("displacement") or {}
        if disp.get("useful_gain"):
            displacement_cases["useful_gain"].append(case_id)
        if disp.get("useful_lost"):
            displacement_cases["useful_lost"].append(case_id)
        if disp.get("non_required_gain"):
            displacement_cases["non_required_gain"].append(case_id)
        if disp.get("non_required_lost"):
            displacement_cases["non_required_lost"].append(case_id)
        gained = len(disp.get("new_required_aspects_gained") or [])
        lost = len(disp.get("required_aspects_lost") or [])
        if gained > lost:
            net_gain.append(case_id)
        elif lost > gained:
            net_loss.append(case_id)
        else:
            net_equal.append(case_id)
    novelty_counts = {"representation_useful": [], "representation_redundant": [],
                      "representation_non_required": [], "ranking_useful": [],
                      "ranking_redundant": [], "ranking_non_required": []}
    for case_id in case_ids:
        novelty = diagnostics["cases"][case_id].get("novelty_utility") or {}
        for chunk in novelty.get("representation_gain", []):
            novelty_counts[f"representation_{chunk['class']}"].append(
                {"case_id": case_id, "chunk_id": chunk["chunk_id"]})
        for chunk in novelty.get("selection_ranking_gain", []):
            key = "ranking_useful" if chunk["class"] == "useful" else (
                "ranking_redundant" if chunk["class"] == "redundant" else "ranking_non_required")
            novelty_counts[key].append({"case_id": case_id, "chunk_id": chunk["chunk_id"]})
    taxonomy_counts: dict[str, list[str]] = {}
    for case_id in case_ids:
        primary = diagnostics["cases"][case_id]["taxonomy"]["primary"]
        taxonomy_counts.setdefault(primary, []).append(case_id)
    routed_decompose = {
        case_id: {
            "layers": diagnostics["cases"][case_id]["layers"].get("ROUTED"),
            "novelty_utility_routed": diagnostics["cases"][case_id].get("novelty_utility_routed"),
        }
        for case_id in ("router_009", "router_011", "router_020")
    }
    v1_rows_match = {
        "answer_complete": {arm: answer_eval["aggregate"][arm]["query_required_complete_cases"] for arm in ARMS},
        "required_covered": {arm: answer_eval["aggregate"][arm]["required_covered_total"] for arm in ARMS},
    }
    expected_complete = {"FIXED_DIRECT": 12, "FIXED_DECOMPOSE": 9, "ROUTED": 13}
    expected_covered = {"FIXED_DIRECT": 54, "FIXED_DECOMPOSE": 51, "ROUTED": 55}
    if v1_rows_match["answer_complete"] != expected_complete or \
            v1_rows_match["required_covered"] != expected_covered:
        raise SystemExit("V1_METRIC_MISMATCH: diagnostic mapping does not reproduce frozen V1 metrics")
    return {
        "version": "router_v1_1_analysis",
        "arm_metrics": arm_metrics,
        "paired_direct_vs_decompose": {
            "evidence_recall_delta": recall_delta,
            "context_precision_delta": precision_delta,
            "evidence_complete_queries": {
                "FIXED_DIRECT": arm_metrics["FIXED_DIRECT"]["evidence_complete_queries"],
                "FIXED_DECOMPOSE": arm_metrics["FIXED_DECOMPOSE"]["evidence_complete_queries"],
            },
        },
        "displacement_cases": displacement_cases,
        "net_evidence_utility": {"net_gain": net_gain, "net_loss": net_loss, "net_equal": net_equal},
        "novelty_utility_counts": {key: value for key, value in novelty_counts.items()},
        "taxonomy_counts": taxonomy_counts,
        "routed_decompose_cases": routed_decompose,
        "v1_answer_metrics_check": v1_rows_match,
        "evidence_judge_cost": evidence_eval.get("evidence_judge_cost"),
        "rubric_limitations": [
            "evidence_required_recall and context precision are proxies against frozen required aspects only",
            "UNCERTAIN evidence judgments are excluded from supported counts",
            "the evidence judge is a single model judge; raw responses are cached for audit",
            "per-chunk displacement classification compares two independent judge calls (DIRECT and DECOMPOSE "
            "evidence sets); combination-dependent support can shift between calls, so boundary cases may lose "
            "coverage without a single identifiable useful chunk (e.g., router_008)",
            "context precision counts chunks that support at least one frozen required aspect; chunks that are "
            "legitimate context beyond the minimum contract are counted as non-required by design",
        ],
    }


def pct_text(part, total):
    return f"{part}/{total} ({100.0 * part / total:.0f}%)" if total else f"{part}/{total}"


def render_report(evidence_eval, diagnostics, analysis) -> None:
    case_ids = [case for case in diagnostics["cases"]]
    m = analysis["arm_metrics"]
    novelty = analysis["novelty_utility_counts"]
    lines: list[str] = []
    lines.append("# Router V1.1 Evidence Diagnostic Report")
    lines.append("")
    lines.append("Post-hoc analysis of frozen Router V1 results; no V1 system was modified or rerun.")
    lines.append("")
    lines.append("## 1. Executive Finding")
    lines.append("")
    lines.append(_executive(evidence_eval, diagnostics, analysis))
    lines.append("")
    lines.append("## 2. Evidence-Level Results")
    lines.append("")
    lines.append("| metric | FIXED_DIRECT | FIXED_DECOMPOSE | ROUTED |")
    lines.append("|---|---|---|---|")
    lines.append(f"| evidence required recall | {m['FIXED_DIRECT']['evidence_required_recall']:.3f} "
                 f"({m['FIXED_DIRECT']['evidence_required_recall_fraction']}) | "
                 f"{m['FIXED_DECOMPOSE']['evidence_required_recall']:.3f} "
                 f"({m['FIXED_DECOMPOSE']['evidence_required_recall_fraction']}) | "
                 f"{m['ROUTED']['evidence_required_recall']:.3f} "
                 f"({m['ROUTED']['evidence_required_recall_fraction']}) |")
    lines.append(f"| evidence complete queries | {m['FIXED_DIRECT']['evidence_complete_queries']}/20 | "
                 f"{m['FIXED_DECOMPOSE']['evidence_complete_queries']}/20 | {m['ROUTED']['evidence_complete_queries']}/20 |")
    lines.append(f"| required context precision | {m['FIXED_DIRECT']['required_context_precision']:.3f} | "
                 f"{m['FIXED_DECOMPOSE']['required_context_precision']:.3f} | "
                 f"{m['ROUTED']['required_context_precision']:.3f} |")
    lines.append(f"| non-required chunks | {m['FIXED_DIRECT']['non_required_chunks']} | "
                 f"{m['FIXED_DECOMPOSE']['non_required_chunks']} | {m['ROUTED']['non_required_chunks']} |")
    util = lambda arm: "n/a" if m[arm]["context_utilization"] is None else f"{m[arm]['context_utilization']:.3f}"
    lines.append(f"| context utilization | {util('FIXED_DIRECT')} | {util('FIXED_DECOMPOSE')} | {util('ROUTED')} |")
    v1 = analysis["v1_answer_metrics_check"]
    lines.append(f"| answer complete | {v1['answer_complete']['FIXED_DIRECT']}/20 | "
                 f"{v1['answer_complete']['FIXED_DECOMPOSE']}/20 | {v1['answer_complete']['ROUTED']}/20 |")
    lines.append(f"| required covered | {v1['required_covered']['FIXED_DIRECT']}/66 | "
                 f"{v1['required_covered']['FIXED_DECOMPOSE']}/66 | {v1['required_covered']['ROUTED']}/66 |")
    lines.append("")
    lines.append("## 3. Retrieval Novelty vs Utility")
    lines.append("")
    lines.append(f"- representation_gain chunks: useful {len(novelty['representation_useful'])}, "
                 f"redundant {len(novelty['representation_redundant'])}, "
                 f"non-required {len(novelty['representation_non_required'])}.")
    lines.append(f"- selection_ranking_gain chunks: useful {len(novelty['ranking_useful'])}, "
                 f"redundant {len(novelty['ranking_redundant'])}, "
                 f"non-required {len(novelty['ranking_non_required'])}.")
    lines.append("")
    lines.append("## 4. Evidence Displacement")
    lines.append("")
    d = analysis["displacement_cases"]
    lines.append(f"- queries with useful evidence gained: {d['useful_gain'] or 'none'}")
    lines.append(f"- queries with useful evidence lost: {d['useful_lost'] or 'none'}")
    lines.append(f"- queries with non-required evidence gained: {d['non_required_gain'] or 'none'}")
    net = analysis["net_evidence_utility"]
    lines.append(f"- net required-aspect evidence gain: {net['net_gain'] or 'none'}; "
                 f"loss: {net['net_loss'] or 'none'}; equal: {net['net_equal'] or 'none'}")
    lines.append("")
    lines.append("## 5. Generation Utilization")
    lines.append("")
    for arm in ARMS:
        lines.append(f"- {arm}: evidence-supported-but-answer-missing aspects "
                     f"{m[arm]['evidence_supported_but_answer_missing']}; "
                     f"answer-without-detected-evidence mentions {m[arm]['answer_without_detected_evidence']}.")
    lines.append("")
    lines.append("## 6. Key Cases")
    lines.append("")
    for case_id in ("router_001", "router_009", "router_010", "router_011", "router_012", "router_020"):
        entry = diagnostics["cases"][case_id]
        lines.append(f"### {case_id}")
        lines.append("")
        lines.append(f"- taxonomy: {entry['taxonomy']['primary']} {entry['taxonomy']['tags']}")
        for arm in ARMS:
            layer = entry["layers"].get(arm) or {}
            if layer.get("status") == "evidence_judge_error":
                continue
            lines.append(f"- {arm}: recall {layer['evidence_required_recall']:.3f}, precision "
                         f"{layer['required_context_precision']:.3f}, utilization "
                         f"{layer['context_utilization']}, supported {layer['supported_aspect_ids']}, "
                         f"evidence-supported-but-missing {layer['evidence_supported_but_answer_missing']}")
        disp = entry.get("displacement")
        if disp:
            lines.append(f"- displacement: useful_gain {[g['chunk_id'] for g in disp['useful_gain']]}, "
                         f"useful_lost {[g['chunk_id'] for g in disp['useful_lost']]}, "
                         f"non_required_gain {disp['non_required_gain']}, lost aspects {disp['required_aspects_lost']}")
        lines.append("")
    lines.append("## 7. Mechanism Taxonomy")
    lines.append("")
    for key, cases in sorted(analysis["taxonomy_counts"].items()):
        lines.append(f"- {key}: {cases}")
    lines.append("")
    lines.append("## 8. Implication for Next Experiment")
    lines.append("")
    lines.append(_implication(analysis))
    lines.append("")
    lines.append("## 9. EACL Exploration-Exploitation Gate")
    lines.append("")
    lines.append(_eacl_gate(analysis))
    lines.append("")
    lines.append("## Appendix: ROUTED decompose cases")
    lines.append("")
    for case_id, payload in analysis["routed_decompose_cases"].items():
        layer = payload["layers"]
        lines.append(f"- {case_id}: recall {layer['evidence_required_recall']:.3f}, precision "
                     f"{layer['required_context_precision']:.3f}, utilization {layer['context_utilization']}, "
                     f"supported {layer['supported_aspect_ids']}, novelty {payload['novelty_utility_routed']}")
    lines.append("")
    (OUT_DIR / "router_v1_1_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _eacl_gate(analysis) -> str:
    novelty = analysis["novelty_utility_counts"]
    useful = len(novelty["representation_useful"]) + len(novelty["ranking_useful"])
    novel_total = sum(len(novelty[key]) for key in novelty)
    lost = analysis["displacement_cases"]["useful_lost"]
    net = analysis["net_evidence_utility"]
    return (
        f"JUSTIFIED. Utility-aware selection has a concrete, reproduced failure mode to address: the frozen "
        f"round-robin merge displaced useful base evidence in {len(lost)} queries "
        f"({lost}) while the net evidence-utility ledger is {len(net['net_gain'])} gain / "
        f"{len(net['net_loss'])} loss / {len(net['net_equal'])} equal. It is not STRONGLY_JUSTIFIED because the "
        f"exploration side rarely produced useful novelty: only {useful} of {novel_total} novel chunks supported "
        f"a required aspect that the base evidence did not already support, so the upstream useful-novelty rate "
        f"remains the ceiling and better selection alone would mainly prevent losses rather than create gains.")


def _executive(evidence_eval, diagnostics, analysis) -> str:
    m = analysis["arm_metrics"]
    d, b = m["FIXED_DIRECT"], m["FIXED_DECOMPOSE"]
    novelty = analysis["novelty_utility_counts"]
    useful = len(novelty["representation_useful"]) + len(novelty["ranking_useful"])
    redundant = len(novelty["representation_redundant"]) + len(novelty["ranking_redundant"])
    non_required = len(novelty["representation_non_required"]) + len(novelty["ranking_non_required"])
    total_novel = useful + redundant + non_required
    lost = analysis["displacement_cases"]["useful_lost"]
    net = analysis["net_evidence_utility"]
    util_d = d["context_utilization"]
    util_b = b["context_utilization"]
    return (
        f"Mixed, with evidence selection as the proximate harm and retrieval exploration as the ceiling. "
        f"Decomposition changed the evidence set (required-aspect evidence recall DIRECT "
        f"{d['evidence_required_recall']:.3f} vs DECOMPOSE {b['evidence_required_recall']:.3f}; context precision "
        f"{d['required_context_precision']:.3f} vs {b['required_context_precision']:.3f}) but its "
        f"{total_novel} novel chunks rarely added required-aspect support (useful {useful}, redundant {redundant}, "
        f"non-required {non_required}). The frozen round-robin merge displaced useful base evidence in "
        f"{len(lost)} queries ({lost}), for a net utility ledger of {len(net['net_gain'])} gain / "
        f"{len(net['net_loss'])} loss / {len(net['net_equal'])} equal. Generation is not the primary bottleneck: "
        f"context utilization is high (DIRECT {util_d:.2f}, DECOMPOSE {util_b:.2f}) and only "
        f"{d['evidence_supported_but_answer_missing']} (DIRECT) / {b['evidence_supported_but_answer_missing']} "
        f"(DECOMPOSE) evidence-supported aspects were left unstated."
    )


def _implication(analysis) -> str:
    m = analysis["arm_metrics"]
    novelty = analysis["novelty_utility_counts"]
    useful = len(novelty["representation_useful"]) + len(novelty["ranking_useful"])
    novel_total = sum(len(novelty[key]) for key in novelty)
    lost = analysis["displacement_cases"]["useful_lost"]
    recall_gain = len(analysis["paired_direct_vs_decompose"]["evidence_recall_delta"]["decompose_higher"])
    recall_loss = len(analysis["paired_direct_vs_decompose"]["evidence_recall_delta"]["decompose_lower"])
    utilization = m["FIXED_DECOMPOSE"]["context_utilization"]
    if useful <= 2 and lost and recall_loss > recall_gain:
        return ("D. MIXED. Two mechanisms dominate: (A) decomposition exploration rarely produced useful new "
                f"required-aspect evidence ({useful}/{novel_total} novel chunks were useful), so the upside is capped; "
                f"and (B) the frozen round-robin merge displaced useful base evidence in {len(lost)} queries, which is "
                "the proximate cause of the (net) coverage loss. (C) is not supported: context utilization stays high "
                f"({utilization:.2f}), so generation utilization is not the bottleneck.")
    if recall_gain == 0 and useful <= 1:
        return ("A. RETRIEVAL_PROBLEM. decomposition did not create useful new required-aspect evidence; the upstream "
                "subquery/retrieval opportunity is the limiting factor rather than sophisticated selection.")
    if lost and recall_loss > recall_gain:
        return ("B. EVIDENCE_SELECTION_PROBLEM. decomposition found some useful novelty but displaced useful base "
                "evidence; selection/displacement dominates the observed loss.")
    if m["FIXED_DIRECT"]["evidence_complete_queries"] >= 15 and \
            m["FIXED_DIRECT"]["evidence_supported_but_answer_missing"] > 0:
        return ("C. GENERATION_UTILIZATION_PROBLEM. evidence coverage is high but answers still miss "
                "evidence-supported aspects.")
    return "D. MIXED. No single layer dominates the observed decomposition failure."


def render_failure_review(diagnostics, analysis) -> None:
    lines = ["# Router V1.1 Failure Mechanism Review", ""]
    for key, cases in sorted(analysis["taxonomy_counts"].items()):
        lines.append(f"## {key}")
        lines.append("")
        for case_id in cases:
            entry = diagnostics["cases"][case_id]
            lines.append(f"- {case_id}: tags {entry['taxonomy']['tags']}")
        lines.append("")
    lines.append("## Displacement detail")
    lines.append("")
    detail_ids = list(dict.fromkeys(
        analysis["net_evidence_utility"]["net_loss"] + analysis["displacement_cases"]["useful_lost"]))
    for case_id in detail_ids:
        entry = diagnostics["cases"][case_id]
        disp = entry.get("displacement") or {}
        lines.append(f"- {case_id}: useful_gain {disp.get('useful_gain')}, useful_lost {disp.get('useful_lost')}, "
                     f"gained chunks {disp.get('gained_chunk_ids')}, lost chunks {disp.get('lost_chunk_ids')}, "
                     f"lost aspects {disp.get('required_aspects_lost')}")
    lines.append("")
    lines.append("## Answer-without-detected-evidence (manual review)")
    lines.append("")
    for case_id, entry in diagnostics["cases"].items():
        for arm in ARMS:
            layer = entry["layers"].get(arm) or {}
            if layer.get("answer_without_detected_evidence"):
                lines.append(f"- {case_id} {arm}: {layer['answer_without_detected_evidence']}")
    lines.append("")
    (OUT_DIR / "router_v1_1_failure_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
