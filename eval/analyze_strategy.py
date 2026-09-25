"""Offline development-only signal study for the frozen Broad Query V3 set."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median

from eval.metrics import POLICIES
from eval.run_evidence_eval import load_inputs


ROOT = Path(__file__).resolve().parents[1]
ANSWER = ROOT / "eval/results/answer_eval_results.json"
TOP20 = ROOT / "eval/results/broad_v3_frozen_top20.json"
CONFIG = ROOT / "eval/adaptive_strategy_candidate.json"
OUTPUT = ROOT / "eval/results/adaptive_strategy_analysis.json"
SUMMARY = ROOT / "eval/results/adaptive_strategy_summary.md"
FIXED, V1, V2 = POLICIES


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _signals(snapshot: dict) -> dict:
    chunks = snapshot["top20"]
    top5, next5 = chunks[:5], chunks[5:10]
    scores = [item["reranker_score"] for item in top5]
    next_scores = [item["reranker_score"] for item in next5]
    top5_docs = {item["source_path"] for item in top5}
    next_docs = {item["source_path"] for item in next5}
    pool = snapshot["candidate_pool"]
    lexical = {item["chunk_id"] for item in pool if item["lexical_rank"] is not None
               and item["lexical_rank"] <= 5}
    semantic = {item["chunk_id"] for item in pool if item["semantic_rank"] is not None
                and item["semantic_rank"] <= 5}
    query = snapshot["query"]
    return {
        "query_word_count": len(query.split()),
        "query_multi_part_markers": len(re.findall(r"\b(?:and|or|when|if|what|how)\b", query, re.I)),
        "candidate_union_size": snapshot["candidate_count"],
        "lexical_semantic_top5_overlap": len(lexical & semantic),
        "top5_document_count": len(top5_docs),
        "new_documents_at_ranks_6_10": len(next_docs - top5_docs),
        "top5_source_repeat_ratio": 1 - len(top5_docs) / 5,
        "top5_evidence_tokens": sum(item["token_count"] for item in top5),
        "top1_reranker_score": scores[0],
        "top5_mean_reranker_score": mean(scores),
        "top5_min_reranker_score": min(scores),
        "top1_to_top5_score_gap": scores[0] - scores[-1],
        "top5_to_next5_mean_score_gap": mean(scores) - mean(next_scores),
    }


def _label(row: dict) -> tuple[str, str]:
    options = row["strategies"]
    fixed = options[FIXED]["quality"]
    best_grounded = max(item["quality"]["grounded_covered_count"]
                        for item in options.values())
    if fixed["grounded_covered_count"] < best_grounded:
        return "escalation_needed", "A broader strategy covers more grounded required facts."
    if fixed["claims"]["unsupported"] > min(
            item["quality"]["claims"]["unsupported"] for item in options.values()):
        return "escalation_needed", "A broader strategy avoids an unsupported claim."
    fixed_citations = sum(fixed["claim_citations"][key] for key in ("missing", "unsupported"))
    best_citations = min(sum(item["quality"]["claim_citations"][key]
                             for key in ("missing", "unsupported")) for item in options.values())
    if fixed_citations > best_citations:
        return "ambiguous", "Required facts tie; another answer has fewer claim citation issues."
    return "fixed_sufficient", "Fixed matches the best grounded fact count without a harder claim issue."


def _describe(values: list[float]) -> dict:
    return {"count": len(values), "median": median(values),
            "min": min(values), "max": max(values)} if values else {"count": 0}


def analyze() -> dict:
    load_inputs()  # Validate all frozen evidence input hashes and aligned case IDs.
    answer = json.loads(ANSWER.read_text(encoding="utf-8"))["broad_v3_controlled"]
    if answer.get("status") != "complete" or answer.get("adjudication_status") != "frozen_offline_source_review":
        raise ValueError("answer quality evaluation is not source-reviewed and frozen")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config["development_answer_eval_freeze_hash"] != answer["answer_eval_freeze_hash"]:
        raise ValueError("candidate rule is tied to a different answer evaluation")
    if (config["if_stop"], config["otherwise"], config["second_stage_v2_rule"]) != (
            FIXED, V1, None):
        raise ValueError("unsupported candidate rule")
    frozen = json.loads(TOP20.read_text(encoding="utf-8"))
    snapshots = {row["case_id"]: row for row in frozen["cases"]}
    if set(snapshots) != {row["case_id"] for row in answer["cases"]}:
        raise ValueError("answer and retrieval cases differ")
    cases = []
    for row in answer["cases"]:
        case_id = row["case_id"]
        signals = _signals(snapshots[case_id])
        label, reason = _label(row)
        selected = (FIXED if signals["top5_min_reranker_score"] >=
                    config["fixed_stop_min_top5_score"] else V1)
        candidate = row["strategies"][selected]
        baseline = row["strategies"][V1]
        special = []
        if not row["candidate_pool_complete"]:
            special.append("retrieval_escalation_needed")
        if case_id == "V3-01":
            special.append("candidate_depth_deep_ranking_failure")
        if any(item["cause"] == "utilization_miss" for item in candidate["pipeline_diagnosis"]):
            special.append("generator_utilization_failure")
        cases.append({
            "case_id": case_id, "development_label": label, "label_reason": reason,
            "special_diagnosis": special, "signals": signals,
            "candidate_selected_strategy": selected,
            "candidate_evidence_tokens": candidate["evidence_tokens"],
            "v1_evidence_tokens": baseline["evidence_tokens"],
            "grounded_fact_regret_vs_v1": (baseline["quality"]["grounded_covered_count"] -
                                            candidate["quality"]["grounded_covered_count"]),
            "answer_fact_regret_vs_v1": (baseline["quality"]["covered_count"] -
                                          candidate["quality"]["covered_count"]),
            "grounded_complete_regret_vs_v1": (int(baseline["quality"]["grounded_fact_complete"]) -
                                                int(candidate["quality"]["grounded_fact_complete"])),
            "candidate_grounded_covered": candidate["quality"]["grounded_covered_count"],
            "candidate_answer_covered": candidate["quality"]["covered_count"],
            "candidate_grounded_complete": candidate["quality"]["grounded_fact_complete"],
            "candidate_answer_complete": candidate["quality"]["fact_complete"],
            "candidate_failure_counts": dict(Counter(item["cause"] for item in
                                                     candidate["pipeline_diagnosis"])),
        })
    counts = Counter(item["development_label"] for item in cases)
    described = {}
    for field in ("top5_min_reranker_score", "top5_mean_reranker_score",
                  "top1_to_top5_score_gap", "top5_to_next5_mean_score_gap",
                  "top5_document_count", "new_documents_at_ranks_6_10",
                  "lexical_semantic_top5_overlap", "query_multi_part_markers"):
        described[field] = {label: _describe([item["signals"][field] for item in cases
                                              if item["development_label"] == label])
                            for label in ("fixed_sufficient", "escalation_needed", "ambiguous")}
    required = sum(row["required_fact_count"] for row in answer["cases"])
    candidate_tokens = sum(item["candidate_evidence_tokens"] for item in cases)
    v1_tokens = answer["summary"]["strategies"][V1]["total_evidence_tokens"]
    chosen = {item["case_id"]: item["candidate_selected_strategy"] for item in cases}
    selected_rows = [row["strategies"][chosen[row["case_id"]]] for row in answer["cases"]]
    candidate_summary = {
        "fixed_stops": sum(item["candidate_selected_strategy"] == FIXED for item in cases),
        "escalations_to_v1": sum(item["candidate_selected_strategy"] == V1 for item in cases),
        "macro_answer_fact_coverage": mean(item["quality"]["fact_coverage"] for item in selected_rows),
        "micro_answer_fact_coverage": sum(item["quality"]["covered_count"] for item in selected_rows) / required,
        "macro_grounded_fact_coverage": mean(item["quality"]["grounded_fact_coverage"] for item in selected_rows),
        "micro_grounded_fact_coverage": sum(item["quality"]["grounded_covered_count"] for item in selected_rows) / required,
        "answer_fact_complete_cases": sum(item["quality"]["fact_complete"] for item in selected_rows),
        "grounded_fact_complete_cases": sum(item["quality"]["grounded_fact_complete"] for item in selected_rows),
        "grounded_fact_regret_vs_v1": sum(item["grounded_fact_regret_vs_v1"] for item in cases),
        "answer_fact_regret_vs_v1": sum(item["answer_fact_regret_vs_v1"] for item in cases),
        "grounded_complete_regret_vs_v1": sum(item["grounded_complete_regret_vs_v1"] for item in cases),
        "evidence_tokens": candidate_tokens,
        "v1_evidence_tokens": v1_tokens,
        "token_saving_vs_v1": v1_tokens - candidate_tokens,
        "token_saving_fraction_vs_v1": (v1_tokens - candidate_tokens) / v1_tokens,
        "failure_counts": dict(sum((Counter(item["candidate_failure_counts"]) for item in cases), Counter())),
    }
    v1_failures = answer["summary"]["strategies"][V1]["pipeline_failure_counts"]
    candidate_summary["failure_count_change_vs_v1"] = {
        cause: candidate_summary["failure_counts"].get(cause, 0) - v1_failures.get(cause, 0)
        for cause in ("candidate_miss", "selection_miss", "utilization_miss", "synthesis_error")}
    escalation_cases = [row for row in answer["cases"] if _label(row)[0] == "escalation_needed"]
    second_stage = [{"case_id": row["case_id"],
                     "v1_grounded_facts": row["strategies"][V1]["quality"]["grounded_covered_count"],
                     "v2_grounded_facts": row["strategies"][V2]["quality"]["grounded_covered_count"],
                     "v1_evidence_tokens": row["strategies"][V1]["evidence_tokens"],
                     "v2_evidence_tokens": row["strategies"][V2]["evidence_tokens"]}
                    for row in escalation_cases]
    return {
        "name": "adaptive_evidence_strategy_signal_study",
        "status": "development_only_not_generalization",
        "source": {"answer_eval_freeze_hash": answer["answer_eval_freeze_hash"],
                   "frozen_top20_sha256": _sha256(TOP20),
                   "candidate_config_sha256": _sha256(CONFIG),
                   "prior_four_cases": "excluded: no aligned frozen rubric and three-strategy answer results"},
        "case_count": len(cases), "required_fact_count": required,
        "development_labels": {name: counts[name] for name in
                               ("fixed_sufficient", "escalation_needed", "ambiguous")},
        "signal_descriptives": described, "second_stage_comparison": second_stage,
        "second_stage_conclusion": "insufficient evidence for second-stage routing rule",
        "candidate_config": config, "candidate_dev_summary": candidate_summary,
        "cases": cases,
    }


def render_summary(result: dict) -> str:
    labels = result["development_labels"]
    dev = result["candidate_dev_summary"]
    v1 = json.loads(ANSWER.read_text(encoding="utf-8"))["broad_v3_controlled"]["summary"]["strategies"][V1]
    signal = result["signal_descriptives"]
    def med(field: str, label: str) -> str:
        value = signal[field][label]
        return f"{value['median']:.2f} (range {value['min']:.2f}–{value['max']:.2f})"
    lines = ["# Adaptive Evidence Strategy Signal Study", "", "## Development Set", "",
             "- 16 frozen Broad Query V3 cases, 92 facts; prior four cases excluded because "
             "their rubric and three-strategy answer results do not align.",
             "- All labels and thresholds were developed on these cases; no validation or generalization claim.",
             "", "## Fixed Sufficiency", "",
             f"- fixed_sufficient {labels['fixed_sufficient']}; escalation_needed "
             f"{labels['escalation_needed']}; ambiguous {labels['ambiguous']}.",
             "- Candidate ceilings V3-03/V3-11 require retrieval escalation, not a larger evidence K. "
             "V3-01 is a candidate-depth/deep-ranking failure.",
             "", "## Signals", "",
             f"- Minimum Top5 reranker score: sufficient median {med('top5_min_reranker_score', 'fixed_sufficient')}; "
             f"escalation median {med('top5_min_reranker_score', 'escalation_needed')}. "
             "A high threshold is a conservative stop signal, not a general difficulty predictor.",
             f"- Top1-to-Top5 score gap: sufficient {med('top1_to_top5_score_gap', 'fixed_sufficient')}; "
             f"escalation {med('top1_to_top5_score_gap', 'escalation_needed')}.",
             f"- Top5 distinct documents: sufficient {med('top5_document_count', 'fixed_sufficient')}; "
             f"escalation {med('top5_document_count', 'escalation_needed')}.",
             "- Tail document gain, lexical/semantic overlap and query multi-part markers overlap strongly "
             "between groups; they remain exploratory only.",
             "", "## Candidate Strategy", "",
             "```text", "Run the existing retrieval and reranker.",
             "If every Top5 reranker score is at least 2.5: use Fixed Top5.",
             "Otherwise: use existing V1 adaptive prefix.",
             "Do not route to V2 yet; there is insufficient evidence for a second-stage rule.",
             "```", "",
             "## Dev Results", "",
             f"- Fixed stops {dev['fixed_stops']}/16; V1 escalations {dev['escalations_to_v1']}/16.",
             f"- Candidate grounded macro/micro {dev['macro_grounded_fact_coverage']:.3f}/"
             f"{dev['micro_grounded_fact_coverage']:.3f} vs V1 "
             f"{v1['macro_grounded_fact_coverage']:.3f}/{v1['micro_grounded_fact_coverage']:.3f}; "
             f"grounded complete {dev['grounded_fact_complete_cases']}/16 vs "
             f"{v1['grounded_fact_complete_cases']}/16.",
             f"- Answer macro/micro {dev['macro_answer_fact_coverage']:.3f}/"
             f"{dev['micro_answer_fact_coverage']:.3f}; grounded and factual regret vs V1 "
             f"{dev['grounded_fact_regret_vs_v1']}/{dev['answer_fact_regret_vs_v1']} facts.",
             f"- Evidence tokens {dev['evidence_tokens']:,} vs V1 {dev['v1_evidence_tokens']:,}; "
             f"saving {dev['token_saving_vs_v1']:,} ({dev['token_saving_fraction_vs_v1']:.1%}).",
             "- Candidate/selection/utilization/synthesis failure counts are unchanged from V1 "
             "on this development set.",
             "", "## Known Failure Modes", "",
             "- Candidate ceilings: V3-03/V3-11. Candidate depth: V3-01. "
             "Answer utilization: V3-07/V3-08. None is fixed by this stop rule.",
             "- V3-04 is a Fixed stop with an unsupported meta-claim shared by V1; "
             "zero regret against V1 does not mean the answer is risk-free.",
             "- The stop threshold uses reranker score scale and may fail under calibration shift. "
             "Frozen evidence mappings contain documented direct-support gaps.",
             "", "## Next Step", "",
             "- Candidate config is frozen for untouched validation only. Build 50–60 new broad queries "
             "across policy scopes, then evaluate grounded quality regret before token savings.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = analyze()
    machine = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    summary = render_summary(result)
    if args.check:
        if not OUTPUT.exists() or not SUMMARY.exists() or (
                OUTPUT.read_text(encoding="utf-8") != machine or
                SUMMARY.read_text(encoding="utf-8") != summary):
            raise SystemExit("saved adaptive strategy analysis differs")
        print("Adaptive strategy analysis matches saved results.")
        return 0
    OUTPUT.write_text(machine, encoding="utf-8")
    SUMMARY.write_text(summary, encoding="utf-8")
    print(f"Analyzed {result['case_count']} development cases; "
          f"candidate saves {result['candidate_dev_summary']['token_saving_vs_v1']:,} evidence tokens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
