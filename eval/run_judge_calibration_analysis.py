"""Deterministic judge-calibration analysis for the frozen random audit sample.

Reads only frozen artifacts (sample, human packet, cross-family judgments, historical
quality labels) and emits the calibration artifacts. It never re-judges, resamples, or
edits any frozen input.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from statistics import NormalDist

from eval.core.benchmark import PROJECT_ROOT
from eval.run_judge_calibration_v1 import prepare

OUTPUT = PROJECT_ROOT / "eval" / "results" / "judge_calibration_v1"
PACKET = PROJECT_ROOT / "eval" / "judge_calibration_v1_human_review.md"
HISTORICAL = PROJECT_ROOT / "eval" / "results" / "a1_blind_answer_quality_frozen_v1.json"
MAPPING = PROJECT_ROOT / "eval" / "results" / "a1_blind_answer_mapping_v1.json"
SUMMARY = OUTPUT / "calibration_summary.json"
DISAGREEMENTS = OUTPUT / "disagreements.json"

EXPECTED_SEED = 20260927
EXPECTED_SAMPLE_SHA = "222ba9eb3858bacbdf6f53257154f7dd54079c8155f77ba1c6c005fabcd02230"
EXPECTED_SOL_SHA = "041f895533117c39beb1d7fced50cc64f456c20b1f9b2884053ae1cd7069cc6f"
EXPECTED_SOURCE_SHA = {
    "quality": "96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35",
    "generation": "1a0c2f0d873c93dcd58b1ff362e56001b99bf610c188671607aec3c6d81d2f11",
    "labels": "85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716",
}
VERDICTS = ("COVERED", "MISSING", "AMBIGUOUS")
Z95 = NormalDist().inv_cdf(0.975)

VERDICT_LINE = re.compile(r"^\*\*(JC-\d{3}) verdict:\*\* (.*)$", re.M)
REASON_LINE = re.compile(r"^\*\*(JC-\d{3}) brief_reason:\*\*(.*)$", re.M)

# Lightweight, hand-assigned taxonomy for the human-grounded disagreements only.
# Both models over-credit the same two aspects; the other three human-MISSING items
# are unanimous across all three judges.
DISAGREEMENT_PATTERN = {
    "JC-013": "partial semantic match",
    "JC-053": "scope mismatch",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k: int, n: int) -> list[float]:
    """95% Wilson score interval for a binomial proportion."""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    z2 = Z95 * Z95
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (Z95 / denom) * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5)
    return [max(0.0, center - half), min(1.0, center + half)]


def load_inputs() -> dict:
    sample = json.loads((OUTPUT / "sample.json").read_text(encoding="utf-8"))
    if sha256(OUTPUT / "sample.json") != EXPECTED_SAMPLE_SHA:
        raise ValueError("sample.json changed since it was frozen")
    if sample["random_seed"] != EXPECTED_SEED or sample["sampled_cases"] != 15 or sample["sampled_judgments"] != 60:
        raise ValueError("frozen sample identity changed")
    if sample["source_sha256"] != EXPECTED_SOURCE_SHA:
        raise ValueError("sample source hashes are not the frozen ones")

    for name, digest in EXPECTED_SOURCE_SHA.items():
        actual = sha256({
            "quality": HISTORICAL,
            "generation": PROJECT_ROOT / "eval" / "results" / "query_aware_stage1_generation_results.json",
            "labels": PROJECT_ROOT / "eval" / "results" / "frozen_human_verdicts_v1.json",
        }[name])
        if actual != digest:
            raise ValueError(f"frozen {name} source hash changed")

    sol_path = OUTPUT / "cross_family_judgments.json"
    if sha256(sol_path) != EXPECTED_SOL_SHA:
        raise ValueError("cross_family_judgments.json does not match the frozen SHA-256")
    sol = json.loads(sol_path.read_text(encoding="utf-8"))

    human_packet = PACKET.read_text(encoding="utf-8")
    human = dict(VERDICT_LINE.findall(human_packet))
    reasons = dict(REASON_LINE.findall(human_packet))

    _, _, generated = prepare()
    if _masked_body(human_packet) != _masked_body(generated):
        raise ValueError("human packet body changed (answer/criterion/source/IDs)")

    ids = [item["review_id"] for item in sample["items"]]
    expected_ids = [f"JC-{n:03d}" for n in range(1, 61)]
    if ids != expected_ids:
        raise ValueError("sample review IDs changed")
    if list(human) != expected_ids:
        raise ValueError("human packet review IDs changed")
    if len(sol["judgments"]) != 60:
        raise ValueError("cross-family judgments are not 60/60")
    sol_ids = [row["review_id"] for row in sol["judgments"]]
    if sol_ids != expected_ids:
        raise ValueError("cross-family review IDs changed")
    if any(value == "PENDING" for value in human.values()):
        raise ValueError("human review still has PENDING verdicts")
    for source in (human, {row["review_id"]: row["verdict"] for row in sol["judgments"]}):
        if any(value not in VERDICTS for value in source.values()):
            raise ValueError("unexpected verdict label")

    historical = _historical_fixed_top5(ids, sample)

    return {
        "sample": sample,
        "human": human,
        "reasons": reasons,
        "sol": {row["review_id"]: row["verdict"] for row in sol["judgments"]},
        "historical": historical,
    }


def _masked_body(text: str) -> str:
    body = text.split("\n## VAL-", 1)[1]
    body = VERDICT_LINE.sub(lambda m: f"**{m.group(1)} verdict:** <V>", body)
    body = REASON_LINE.sub(lambda m: f"**{m.group(1)} brief_reason:**<R>", body)
    return body


def _historical_fixed_top5(ids: list[str], sample: dict) -> dict[str, str]:
    quality = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in quality["cases"]}
    label_map = mapping["cases"]
    result: dict[str, str] = {}
    for item, review_id in zip(sample["items"], ids):
        case_id, aspect_id = item["case_id"], item["aspect_id"]
        labels = [label for label, info in label_map[case_id].items() if "fixed_top5" in info["arms"]]
        if len(labels) != 1:
            raise ValueError(f"{case_id}: fixed_top5 does not map to exactly one blind answer")
        aspects = cases[case_id]["answers"][labels[0]]["aspects"]
        if aspect_id not in aspects:
            raise ValueError(f"{aspect_id}: missing historical verdict for fixed_top5")
        status = aspects[aspect_id]["judge_status"]
        if status == "covered":
            result[review_id] = "COVERED"
        elif status == "missing":
            result[review_id] = "MISSING"
        else:
            raise ValueError(f"{aspect_id}: unexpected historical status {status!r}")
    return result


def confusion(reference: dict[str, str], other: dict[str, str], ref_values: tuple[str, ...], other_values: tuple[str, ...]) -> dict:
    matrix = {r: {o: 0 for o in other_values} for r in ref_values}
    ids = list(reference)
    for review_id in ids:
        matrix[reference[review_id]][other[review_id]] += 1
    comparable = [review_id for review_id in ids if reference[review_id] in ("COVERED", "MISSING") and other[review_id] in ("COVERED", "MISSING")]
    agreement = sum(1 for review_id in comparable if reference[review_id] == other[review_id])
    fp = [review_id for review_id in ids if other[review_id] == "COVERED" and reference[review_id] == "MISSING"]
    fn = [review_id for review_id in ids if other[review_id] == "MISSING" and reference[review_id] == "COVERED"]
    return {
        "matrix": matrix,
        "comparable_ids": comparable,
        "comparable": len(comparable),
        "agreement": agreement,
        "agreement_rate": agreement / len(comparable) if comparable else None,
        "wilson_95": wilson(agreement, len(comparable)) if comparable else None,
        "false_positive_ids": fp,
        "false_positives": len(fp),
        "false_negative_ids": fn,
        "false_negatives": len(fn),
    }


def complete_cases(sample: dict, verdicts: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    by_case: dict[str, list[str]] = {}
    for item in sample["items"]:
        by_case.setdefault(item["case_id"], []).append(item["review_id"])
    status: dict[str, str] = {}
    indeterminate: list[str] = []
    for case_id, review_ids in by_case.items():
        values = [verdicts[review_id] for review_id in review_ids]
        if "AMBIGUOUS" in values:
            status[case_id] = "Indeterminate"
            indeterminate.append(case_id)
        elif all(value == "COVERED" for value in values):
            status[case_id] = "Complete"
        else:
            status[case_id] = "Incomplete"
    return status, indeterminate


def count_status(status: dict[str, str]) -> dict[str, int]:
    counter = Counter(status.values())
    return {"Complete": counter["Complete"], "Incomplete": counter["Incomplete"], "Indeterminate": counter["Indeterminate"]}


def build() -> tuple[dict, dict]:
    data = load_inputs()
    sample, human, sol, historical = data["sample"], data["human"], data["sol"], data["historical"]

    hist_vs_human = confusion(human, historical, ("COVERED", "MISSING"), ("COVERED", "MISSING"))
    sol_vs_human = confusion(human, sol, ("COVERED", "MISSING"), VERDICTS)
    hist_vs_sol = confusion(historical, sol, ("COVERED", "MISSING"), VERDICTS)

    aspect_text = {}
    for item in json.loads((OUTPUT / "judge_inputs.json").read_text(encoding="utf-8"))["items"]:
        aspect_text[item["review_id"]] = {
            "case_id": item["case_id"],
            "aspect_id": item["aspect_id"],
            "required_aspect": item["required_aspect"],
        }

    hist_status, hist_ind = complete_cases(sample, historical)
    sol_status, sol_ind = complete_cases(sample, sol)
    human_status, human_ind = complete_cases(sample, human)

    hist_mismatch = sorted(c for c in human_status if human_status[c] != hist_status[c])
    sol_mismatch = sorted(c for c in human_status if human_status[c] != sol_status[c])
    sample_review_ids = [item["review_id"] for item in sample["items"]]

    summary = {
        "version": "judge-calibration-v1-analysis",
        "provenance": "AI-assisted blinded project-author review",
        "seed": EXPECTED_SEED,
        "sample": {"cases": 15, "aspects": 60, "universe_aspects": 208, "universe_cases": 50},
        "integrity": {
            "sample_sha256": EXPECTED_SAMPLE_SHA,
            "cross_family_sha256": EXPECTED_SOL_SHA,
            "human_packet_sha256": sha256(PACKET),
            "judge_inputs_sha256": sha256(OUTPUT / "judge_inputs.json"),
            "source_sha256": EXPECTED_SOURCE_SHA,
            "jc_ids": "JC-001..JC-060 exactly once",
            "human_pending": 0,
            "cross_family_completed": 60,
        },
        "verdict_totals": {
            "human": dict(Counter(human.values())),
            "historical": dict(Counter(historical.values())),
            "sol": dict(Counter(sol.values())),
        },
        "historical_vs_human": hist_vs_human,
        "sol_vs_human": sol_vs_human,
        "historical_vs_sol": {
            **hist_vs_sol,
            "historical_covered_sol_missing": sum(
                1 for r in hist_vs_sol["comparable_ids"] if historical[r] == "COVERED" and sol[r] == "MISSING"),
            "historical_missing_sol_covered": sum(
                1 for r in hist_vs_sol["comparable_ids"] if historical[r] == "MISSING" and sol[r] == "COVERED"),
            "ambiguous_involvement": sum(1 for r in sample_review_ids if historical[r] == "AMBIGUOUS" or sol[r] == "AMBIGUOUS"),
        },
        "headline_sensitivity": {
            "label": "illustrative sensitivity analysis — not a corrected benchmark score",
            "historical_vs_human_disagreements": hist_vs_human["false_positives"] + hist_vs_human["false_negatives"],
            "n": hist_vs_human["comparable"],
            "observed_disagreement_rate": (hist_vs_human["false_positives"] + hist_vs_human["false_negatives"]) / hist_vs_human["comparable"],
            "observed_disagreement_rate_wilson_95": wilson(hist_vs_human["false_positives"] + hist_vs_human["false_negatives"], hist_vs_human["comparable"]),
            "false_positives": hist_vs_human["false_positives"],
            "false_negatives": hist_vs_human["false_negatives"],
        },
        "taxonomy": {
            "scope": "human-grounded disagreements (model vs project-author human review)",
            "pattern_counts": dict(Counter(DISAGREEMENT_PATTERN.values())),
            "by_review_id": dict(DISAGREEMENT_PATTERN),
        },
        "complete_case": {
            "definition": "all sampled QUERY_REQUIRED aspects COVERED; any AMBIGUOUS makes the case indeterminate",
            "historical": {"counts": count_status(hist_status), "status": hist_status, "indeterminate": hist_ind},
            "sol": {"counts": count_status(sol_status), "status": sol_status, "indeterminate": sol_ind},
            "human": {"counts": count_status(human_status), "status": human_status, "indeterminate": human_ind},
            "historical_vs_human_mismatch_case_ids": hist_mismatch,
            "sol_vs_human_mismatch_case_ids": sol_mismatch,
        },
        "bias_direction": None,
        "notes": [
            "inter-model agreement is not accuracy",
            "aspect-level agreement does not replace case-level reliability",
            "sample-level sensitivity only; not a corrected benchmark score",
        ],
    }
    if hist_vs_human["false_positives"] > hist_vs_human["false_negatives"]:
        summary["bias_direction"] = "observed over-credit tendency in the audited sample"
    elif hist_vs_human["false_negatives"] > hist_vs_human["false_positives"]:
        summary["bias_direction"] = "observed under-credit tendency in the audited sample"
    else:
        summary["bias_direction"] = "no clear directional tendency in this sample"

    disagreements = {"version": "judge-calibration-v1-disagreements", "taxonomy": summary["taxonomy"], "items": [], "human_missing_boundary": []}
    for review_id in sample_review_ids:
        human_grounded = historical[review_id] != human[review_id] or sol[review_id] != human[review_id]
        row = {
            "review_id": review_id,
            "case_id": aspect_text[review_id]["case_id"],
            "aspect_id": aspect_text[review_id]["aspect_id"],
            "required_aspect": aspect_text[review_id]["required_aspect"],
            "human": human[review_id],
            "historical": historical[review_id],
            "sol": sol[review_id],
            "human_grounded_disagreement": human_grounded,
            "pattern": DISAGREEMENT_PATTERN.get(review_id) if human_grounded else None,
            "human_brief_reason": data["reasons"].get(review_id, ""),
        }
        if len({row["human"], row["historical"], row["sol"]}) > 1 or row["human"] == "MISSING":
            disagreements["items"].append(row)
        if row["human"] == "MISSING":
            disagreements["human_missing_boundary"].append(row)
    return summary, disagreements


def write(summary: dict, disagreements: dict) -> None:
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DISAGREEMENTS.write_text(json.dumps(disagreements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    summary, disagreements = build()
    write(summary, disagreements)
    print("wrote", SUMMARY.name, "and", DISAGREEMENTS.name)
    print("historical_vs_human:", {k: summary["historical_vs_human"][k] for k in ("comparable", "agreement", "agreement_rate", "false_positives", "false_negatives")})
    print("sol_vs_human:", {k: summary["sol_vs_human"][k] for k in ("comparable", "agreement", "agreement_rate", "false_positives", "false_negatives")})
    print("bias_direction:", summary["bias_direction"])
    print("disagreement_rows:", len(disagreements["items"]), [row["review_id"] for row in disagreements["items"]])


if __name__ == "__main__":
    main()
