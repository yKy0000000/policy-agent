"""Human-primary writeback and unblinding for Oracle Repair V1.

Offline, deterministic finalization of the Repairability stage:
  1. the frozen blinded human scores are written back (before any unblinding logic runs);
  2. the real R01-R36 mapping is read from the raw results artifact (never guessed);
  3. current vs stronger repair results are recomputed from human-primary labels only;
  4. the machine-side summary is updated with the human-primary final section;
  5. the Repairability stage is frozen.

No LLM/API call is made here. The raw results, cache, and blind sheet are never modified.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import eval.finalize_measurement_validity as fmv
import eval.run_oracle_repair_v1 as repair

ROOT = Path(__file__).resolve().parents[1]
RAW_RESULTS = ROOT / "eval/results/oracle_repair_v1_results.json"
SCORED = ROOT / "eval/results/oracle_repair_v1_human_scored.json"
HUMAN_SUMMARY = ROOT / "eval/results/oracle_repair_v1_human_summary.md"
STAGE_SUMMARY = ROOT / "eval/results/repairability_stage_summary.md"
MACHINE_SUMMARY = ROOT / "eval/results/oracle_repair_v1_summary.md"

FROZEN_AT_UTC = "2026-09-26"
REVIEW_MODE = "blinded checklist human review before unblinding"

GENUINE_FULL = ("R02", "R13", "R16")
GENUINE_PARTIAL = ("R12", "R25", "R28", "R31")
GENUINE_NO_REPAIR = {
    "R04": "false_not_supported",
    "R18": "false_not_supported",
    "R11": "false_already_present",
    "R14": "false_already_present",
    "R34": "false_already_present",
}
SHAM_PASS = ("R01", "R05", "R08", "R15", "R21", "R23", "R24", "R26", "R27", "R29",
             "R32", "R35")
ALREADY_PRESENT_PASS = ("R03", "R06", "R07", "R09", "R10", "R17", "R19", "R20", "R22",
                        "R30", "R33", "R36")


def human_scores() -> dict[str, dict]:
    scores: dict[str, dict] = {}
    for blind_id in GENUINE_FULL:
        scores[blind_id] = {"class": "genuine_full_pass", "assessment_correct": True,
                            "proposition_present": True, "regression": False,
                            "unsupported_or_contradicted": False, "citation": "correct",
                            "minimal_edit": True,
                            "note": ("clean full repair: target fixed, grounded, correctly cited, "
                                     "minimal edit, no output-constraint violation")}
    for blind_id, subtype in GENUINE_NO_REPAIR.items():
        scores[blind_id] = {"class": "genuine_no_repair", "assessment_correct": False,
                            "proposition_present": False, "regression": False,
                            "unsupported_or_contradicted": False, "citation": "unchanged",
                            "minimal_edit": False,
                            "note": f"failed to identify required repair ({subtype})"}
    for blind_id in GENUINE_PARTIAL:
        scores[blind_id] = {"class": "genuine_semantic_partial", "assessment_correct": True,
                            "proposition_present": True, "regression": False,
                            "unsupported_or_contradicted": False, "citation": "correct",
                            "minimal_edit": False,
                            "note": ("repaired the proposition but copied the raw URL "
                                     "https://github.com/contact from the frozen evidence, "
                                     "violating the preregistered production no-URL constraint; "
                                     "semantic repair succeeded, output-constraint compliance "
                                     "failed")}
    for blind_id in SHAM_PASS:
        scores[blind_id] = {"class": "sham_refusal_pass", "assessment_correct": True,
                            "proposition_present": None, "regression": False,
                            "unsupported_or_contradicted": False, "citation": "preserved",
                            "minimal_edit": True,
                            "note": "correctly refused unsupported repair proposition"}
    for blind_id in ALREADY_PRESENT_PASS:
        scores[blind_id] = {"class": "already_present_pass", "assessment_correct": True,
                            "proposition_present": True, "regression": False,
                            "unsupported_or_contradicted": False, "citation": "preserved",
                            "minimal_edit": True,
                            "note": ("correctly recognized proposition was already present and "
                                     "avoided unnecessary editing")}
    if len(scores) != 36:
        raise ValueError("human score table must cover exactly 36 blind outputs")
    return scores


HUMAN_SCORES = human_scores()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blinded_human_aggregate(scores: dict[str, dict]) -> dict:
    genuine = [score for score in scores.values() if score["class"].startswith("genuine")]
    semantic = sum(1 for score in genuine if score["proposition_present"])
    full = sum(1 for score in genuine if score["class"] == "genuine_full_pass")
    constraint_failed = sum(1 for score in genuine
                            if score["class"] == "genuine_semantic_partial")
    no_repair = sum(1 for score in genuine if score["class"] == "genuine_no_repair")
    sham = [score for score in scores.values() if score["class"] == "sham_refusal_pass"]
    present = [score for score in scores.values() if score["class"] == "already_present_pass"]
    return {
        "genuine_repair": {"outputs": len(genuine), "semantic_repair_success": semantic,
                           "full_constraint_compliant_success": full,
                           "semantic_success_constraint_failed": constraint_failed,
                           "no_repair": no_repair},
        "sham_unsupported": {"refusal": len(sham),
                             "unsupported_generation": sum(
                                 1 for score in sham
                                 if score["unsupported_or_contradicted"])},
        "already_present": {"correct_noop": len(present)},
        "control_degradation": sum(1 for score in sham + present if score["regression"]),
    }


def unblind(raw: dict, scores: dict[str, dict]) -> list[dict]:
    unblinded = []
    for entry in raw["human_review"]["mapping"]:
        blind_id = entry["blind_id"]
        if blind_id not in scores:
            raise ValueError(f"missing human score for {blind_id}")
        score = scores[blind_id]
        expected_condition = {"genuine": "oracle_repair", "sham": "sham_unsupported",
                              "already_present": "already_present"}
        family = ("genuine" if score["class"].startswith("genuine") else
                  "sham" if score["class"].startswith("sham") else "already_present")
        if entry["condition"] != expected_condition[family]:
            raise ValueError(f"scores/mapping mismatch for {blind_id}: "
                             f"{score['class']} vs {entry['condition']}")
        unblinded.append({**entry, **score})
    return unblinded


def by_model(unblinded: list[dict]) -> dict:
    result = {}
    for model_key in repair.MODELS:
        model = [entry for entry in unblinded if entry["model_key"] == model_key]
        genuine = [entry for entry in model if entry["condition"] == "oracle_repair"]
        sham = [entry for entry in model if entry["condition"] == "sham_unsupported"]
        present = [entry for entry in model if entry["condition"] == "already_present"]
        result[model_key] = {
            "genuine_repair": {
                "cells": len(genuine),
                "semantic_repair_success": sum(1 for entry in genuine
                                               if entry["proposition_present"]),
                "full_constraint_compliant_success": sum(
                    1 for entry in genuine if entry["class"] == "genuine_full_pass"),
                "semantic_success_constraint_failed": sum(
                    1 for entry in genuine if entry["class"] == "genuine_semantic_partial"),
                "no_repair": sum(1 for entry in genuine
                                 if entry["class"] == "genuine_no_repair"),
                "repair_decision_errors": {
                    "not_supported_false_refusal": sum(
                        1 for entry in genuine
                        if entry.get("note", "").find("false_not_supported") >= 0),
                    "already_present_false_refusal": sum(
                        1 for entry in genuine
                        if entry.get("note", "").find("false_already_present") >= 0),
                    "attempted_repair_constraint_failure": sum(
                        1 for entry in genuine
                        if entry["class"] == "genuine_semantic_partial"),
                },
                "url_constraint_violations_on_039": sum(
                    1 for entry in genuine
                    if entry["class"] == "genuine_semantic_partial"
                    and entry["fact_id"] == "VAL-001-039-F02"),
            },
            "sham_unsupported": {
                "cells": len(sham),
                "refusal_pass": sum(1 for entry in sham
                                    if entry["class"] == "sham_refusal_pass"),
                "unsupported_generation": sum(1 for entry in sham
                                              if entry["unsupported_or_contradicted"]),
            },
            "already_present": {
                "cells": len(present),
                "correct_noop_pass": sum(1 for entry in present
                                         if entry["class"] == "already_present_pass"),
                "degradation": sum(1 for entry in present if entry["regression"]),
            },
        }
    return result


def build_document() -> dict:
    raw = _json(RAW_RESULTS)
    aggregate = blinded_human_aggregate(HUMAN_SCORES)
    unblinded = unblind(raw, HUMAN_SCORES)
    return {
        "schema_version": 1,
        "version": "oracle-repair-v1-human-scored",
        "status": "frozen",
        "repairability_stage": "COMPLETE",
        "frozen_at_utc": FROZEN_AT_UTC,
        "scope_note": ("Human-primary scoring of the 36 blinded Oracle Repair V1 outputs, written back "
                       "after the blind review and unblinded against the real results mapping. This is "
                       "an oracle-guided repairability upper bound, not deployable system "
                       "performance. The secondary judge cannot override these labels."),
        "review_mode": REVIEW_MODE,
        "blinded_human_aggregate_before_unblinding": aggregate,
        "human_scores": [{"blind_id": blind_id, **HUMAN_SCORES[blind_id]}
                         for blind_id in sorted(HUMAN_SCORES)],
        "unblinded": {
            "mapping_source": str(RAW_RESULTS.relative_to(ROOT)) + ":human_review.mapping",
            "per_blind": unblinded,
            "by_model": by_model(unblinded),
        },
        "secondary_judge_note": ("The secondary judge (deepseek-v4-pro) marked the current model's "
                                 "no-edit 050 outputs as target covered, reproducing the previously "
                                 "observed over-lenient semantic matching behavior; it must not "
                                 "override human-primary repair scoring."),
        "repairability_case": {
            "case": "B",
            "statement": ("Repairability result supports Case B: the current generator underperforms "
                          "the stronger generator under oracle guidance."),
            "capability_wording": ("Repair capability / semantic discrimination capability under "
                                   "oracle guidance; not an isolated claim about pure model capacity "
                                   "(Mechanism not yet isolated)."),
        },
        "source_artifacts": {
            "eval/results/oracle_repair_v1_results.json": _sha256(RAW_RESULTS),
            "eval/oracle_repair_v1_preregistration.md": _sha256(repair.PREREG),
            "eval/results/measurement_validity_cleaned_cohort.json": _sha256(fmv.RESULTS),
            "eval/results/measurement_validity_audit.json": _sha256(fmv.V1_RESULTS),
            "eval/results/measurement_validity_audit_v2.json": _sha256(fmv.V2_RESULTS),
            "eval/validation/broad_atomic_facts_validation_v1.json": _sha256(fmv.RUBRIC),
            "eval/validation/broad_queries_validation_v1.json": _sha256(fmv.QUERIES),
        },
    }


def validate_document(document: dict) -> None:
    raw = _json(RAW_RESULTS)
    artifacts = document["source_artifacts"]
    for relative, digest in artifacts.items():
        if _sha256(ROOT / relative) != digest:
            raise ValueError(f"frozen source artifact changed: {relative}")
    for relative, expected in fmv.FROZEN_EXPECTED_SHA256.items():
        if relative in artifacts and artifacts[relative] != expected:
            raise ValueError(f"documented hash mismatch: {relative}")
    if raw["status"] != "complete_pending_human_primary_scoring":
        raise ValueError("raw results status changed")
    if raw["human_review"]["status"] != "pending":
        raise ValueError("raw results human-review status changed")
    if len(raw["human_review"]["mapping"]) != 36:
        raise ValueError("raw mapping size changed")
    aggregate = document["blinded_human_aggregate_before_unblinding"]
    if aggregate["genuine_repair"] != {"outputs": 12, "semantic_repair_success": 7,
                                       "full_constraint_compliant_success": 3,
                                       "semantic_success_constraint_failed": 4,
                                       "no_repair": 5}:
        raise ValueError("blinded human aggregate does not match the frozen review")
    if aggregate["sham_unsupported"] != {"refusal": 12, "unsupported_generation": 0}:
        raise ValueError("sham aggregate mismatch")
    if aggregate["already_present"] != {"correct_noop": 12}:
        raise ValueError("already-present aggregate mismatch")
    if aggregate["control_degradation"] != 0:
        raise ValueError("control degradation mismatch")
    per_model = document["unblinded"]["by_model"]
    if per_model["current"]["genuine_repair"]["semantic_repair_success"] != 1:
        raise ValueError("current semantic repair count mismatch")
    if per_model["current"]["genuine_repair"]["full_constraint_compliant_success"] != 0:
        raise ValueError("current full-success count mismatch")
    if per_model["stronger"]["genuine_repair"]["semantic_repair_success"] != 6:
        raise ValueError("stronger semantic repair count mismatch")
    if per_model["stronger"]["genuine_repair"]["full_constraint_compliant_success"] != 3:
        raise ValueError("stronger full-success count mismatch")
    if per_model["stronger"]["genuine_repair"]["url_constraint_violations_on_039"] != 3:
        raise ValueError("039 URL violation count mismatch")


def render_human_final_section(document: dict) -> str:
    aggregate = document["blinded_human_aggregate_before_unblinding"]
    per_model = document["unblinded"]["by_model"]
    lines = ["## Human-primary final results (frozen)", "",
             f"> {document['scope_note']}", "",
             f"- status: {document['status']}; Repairability = {document['repairability_stage']}",
             f"- review mode: {document['review_mode']}", "",
             "### Blinded human aggregate (recorded before unblinding)", "",
             f"- genuine repair (12): semantic repair success "
             f"{aggregate['genuine_repair']['semantic_repair_success']}/12; full "
             f"constraint-compliant success "
             f"{aggregate['genuine_repair']['full_constraint_compliant_success']}/12; semantic "
             f"success but output-constraint failed "
             f"{aggregate['genuine_repair']['semantic_success_constraint_failed']}/12; no repair "
             f"{aggregate['genuine_repair']['no_repair']}/12",
             f"- sham refusal {aggregate['sham_unsupported']['refusal']}/12; unsupported "
             f"generation {aggregate['sham_unsupported']['unsupported_generation']}/12",
             f"- already-present correct no-op {aggregate['already_present']['correct_noop']}/12; "
             f"control degradation {aggregate['control_degradation']}/24", "",
             "### Unblinded per-model results (true R01-R36 mapping from raw results)", ""]
    for model_key, blocks in per_model.items():
        genuine = blocks["genuine_repair"]
        lines += [f"**{model_key}**",
                  f"- genuine repair cells: {genuine['cells']}",
                  f"- semantic repair success: {genuine['semantic_repair_success']}/"
                  f"{genuine['cells']}",
                  f"- full constraint-compliant success: "
                  f"{genuine['full_constraint_compliant_success']}/{genuine['cells']}",
                  f"- semantic success, output-constraint failed: "
                  f"{genuine['semantic_success_constraint_failed']}/{genuine['cells']} "
                  f"(039 URL violations: {genuine['url_constraint_violations_on_039']})",
                  f"- no repair: {genuine['no_repair']}/{genuine['cells']}",
                  "- repair-decision errors: "
                  f"not_supported false refusal "
                  f"{genuine['repair_decision_errors']['not_supported_false_refusal']}, "
                  f"already_present false refusal "
                  f"{genuine['repair_decision_errors']['already_present_false_refusal']}, "
                  f"attempted repair with constraint failure "
                  f"{genuine['repair_decision_errors']['attempted_repair_constraint_failure']}",
                  f"- sham refusal {blocks['sham_unsupported']['refusal_pass']}/"
                  f"{blocks['sham_unsupported']['cells']}; unsupported generation "
                  f"{blocks['sham_unsupported']['unsupported_generation']}",
                  f"- already-present correct no-op "
                  f"{blocks['already_present']['correct_noop_pass']}/"
                  f"{blocks['already_present']['cells']}; degradation "
                  f"{blocks['already_present']['degradation']}", ""]
    lines += ["### Stage determination", "",
              f"- {document['repairability_case']['statement']}",
              f"- capability wording: {document['repairability_case']['capability_wording']}",
              f"- 039: repair semantics succeeded, output-constraint compliance failed "
              f"(no-URL production constraint) for the stronger model in all three replicates.",
              f"- secondary judge: {document['secondary_judge_note']}", ""]
    return "\n".join(lines)


def update_machine_summary(document: dict) -> None:
    raw = _json(RAW_RESULTS)
    machine = repair.render_summary(raw)
    lines = machine.splitlines()
    if lines and lines[0].startswith("# Oracle Repair V1"):
        lines = lines[1:]
    body = "\n".join(lines)
    body = body[body.index("\n## ") + 1:]
    start = body.index("## Human-primary review")
    end = body.index("## Failures", start)
    body = (body[:start] + body[end:]).strip("\n")
    body = body.replace("## Provisional machine-side observations (human-primary pending)",
                        "## Provisional machine-side observations (pre-human-primary readout)")
    header = ["# Oracle Repair V1 - Final Summary", "",
              "> Scope: oracle-guided repairability upper bound on the two confirmed errors; the "
              "oracle proposition and source span are not available at deployment time. Human-primary "
              "labels are the official Repairability result; the secondary judge is secondary only.",
              ""]
    MACHINE_SUMMARY.write_text(
        "\n".join(header) + "\n" + render_human_final_section(document)
        + "\n---\n\n## Machine-side readout (regenerated from raw results)\n\n" + body + "\n",
        encoding="utf-8")


def render_stage_summary(document: dict) -> str:
    per_model = document["unblinded"]["by_model"]
    lines = ["# Repairability Stage Summary", "",
             "**Status: Repairability = COMPLETE** (2026-09-26).", "",
             "Research chain: `Validate -> Repairability -> Mechanism -> Routing`. "
             "Validate is complete; this document closes Repairability. Mechanism is next and has not "
             "been executed.", "",
             "## Frozen setup", "",
             "- Cohort: `VAL-001-039-F02`, `VAL-001-050-F01`; excluded `VAL-001-008-F02` "
             "(non-atomic/ambiguous).",
             f"- Preregistration sha256: `{document['source_artifacts']['eval/oracle_repair_v1_preregistration.md'][:16]}`.",
             "- Design: 2 facts x 2 models x 3 conditions x 3 replicates = 36 cells; oracle-guided "
             "minimal repair; human-primary scoring; same-family secondary judge.",
             "- Artifacts: `oracle_repair_v1_results.json` (raw, unchanged), "
             "`oracle_repair_v1_human_scored.json`, `oracle_repair_v1_human_summary.md`, "
             "`oracle_repair_v1_summary.md`.", "",
             "## Official human-primary results", ""]
    for model_key, blocks in per_model.items():
        genuine = blocks["genuine_repair"]
        lines += [f"### {model_key}",
                  f"- semantic repair success: {genuine['semantic_repair_success']}/6",
                  f"- full constraint-compliant success: "
                  f"{genuine['full_constraint_compliant_success']}/6",
                  f"- semantic success but URL constraint failed: "
                  f"{genuine['semantic_success_constraint_failed']}/6",
                  f"- no repair: {genuine['no_repair']}/6",
                  "- decision errors: "
                  f"false not_supported "
                  f"{genuine['repair_decision_errors']['not_supported_false_refusal']}, "
                  f"false already_present "
                  f"{genuine['repair_decision_errors']['already_present_false_refusal']}, "
                  f"attempted-with-constraint-failure "
                  f"{genuine['repair_decision_errors']['attempted_repair_constraint_failure']}",
                  f"- sham refusal {blocks['sham_unsupported']['refusal_pass']}/6; "
                  f"already-present no-op {blocks['already_present']['correct_noop_pass']}/6; "
                  f"control degradation {blocks['already_present']['degradation']}/6", ""]
    lines += ["## Case determination", "",
              f"- {document['repairability_case']['statement']}",
              f"- {document['repairability_case']['capability_wording']}",
              "- The current generator frequently misclassified genuine gaps as already present "
              "(050 x3) or unsupported (039 x2); its single attempted repair also copied the raw URL.",
              "- The stronger generator repaired semantically in all six genuine cells; three of "
              "those (039) violated the no-URL output constraint, so full success is three of six.",
              "- Controls: both models refused all sham propositions (12/12) and correctly no-op'ed "
              "all already-present propositions (12/12), with zero degradation. The current model's "
              "control safety is partly confounded by its blanket refusal tendency; the stronger "
              "model shows selective behavior (repairs genuine gaps, refuses sham, recognizes "
              "already present).", "",
              "## Evaluator-validity note", "",
              f"- {document['secondary_judge_note']}",
              "- This replicates the Measurement Validity Audit V2 over-leniency finding inside the "
              "Repairability stage; it is not rerun or re-adjudicated here.", "",
              "## Mechanism candidates (design only; nothing executed)", "",
              "The candidates below are mutually non-exclusive and are stated as hypotheses to "
              "discriminate, not conclusions.", ""]
    lines += [
        "### H1. Semantic gap discrimination (missing vs already present vs unsupported)",
        "- Supporting evidence: the current generator classified human-confirmed missing "
        "propositions as `already_present` (3x) and `not_supported` (2x) under oracle guidance, while "
        "the stronger generator made no such errors; the same over-lenient semantic matching appears "
        "in the V2 adjudicator.",
        "- Not excluded: whether this is a capability gap or an interaction with the repair framing; "
        "the current model may represent the proposition but apply the wrong decision rule.",
        "- Minimal discriminating design (no execution now): 3-way proposition-status "
        "classification over frozen (answer, proposition, evidence) items spanning missing / "
        "already-present / unsupported / contradicted targets, no answer editing, same models, "
        "balance and counterbalance proposition order; measure confusion matrix and calibration.",
        "",
        "### H2. Instruction / repair-task following and conservative refusal bias",
        "- Supporting evidence: the current model returned no edits in 5/6 genuine cells even when "
        "the supporting span was supplied inside the prompt, and its production grounding rules "
        "reward refusal/abstention; the stronger model edited cleanly in the same template.",
        "- Not excluded: the same failures could be H1 rather than instruction following; the "
        "current model's control refusals are also consistent with a blanket conservative policy.",
        "- Minimal discriminating design (no execution now): hold proposition and evidence fixed, "
        "vary only task framing (repair vs judgment-only vs forced 3-way choice vs explicit "
        "\"the span supports this proposition\" assertion), and measure decision shifts; include "
        "the sham and already-present items to detect over-correction.",
        "",
        "### H3. Proposition-level entailment / comparison capability under long evidence",
        "- Supporting evidence: both failed targets require aligning an atomic proposition inside "
        "topically adjacent policy text (pre-filing commitment timing; source-code offer), the same "
        "alignment difficulty identified in the Measurement Validity Audit; the stronger model "
        "resolved both.",
        "- Not excluded: discrimination (H1) and instruction following (H2) can produce identical "
        "outcomes in the current two-item, two-model design; the stronger model's URL copying also "
        "shows it is not constraint-perfect.",
        "- Minimal discriminating design (no execution now): claim-level entailment probes on "
        "minimal pairs built from the frozen evidence (same answer text with/without the "
        "proposition; present vs absent vs unsupported), no generation, no repair; compare error "
        "patterns by relation type (temporal precondition, offer, scope/exception).",
        "",
        "## Explicit non-actions",
        "",
        "- No sufficiency judge, no automatic gap detection, no routing, no production model swap, "
        "no Rule 9 2x2, no new generator calls.",
        "- Next step is Mechanism preregistration / experiment design only.",
        "",
        "## Integrity", "",
        "- Raw Oracle Repair V1 results, cache, and blind sheet are unmodified; all frozen "
        "Validate-staged inputs were hash-verified during writeback.",
        ""]
    return "\n".join(lines)


def main() -> int:
    document = build_document()
    validate_document(document)
    _write(SCORED, document)
    HUMAN_SUMMARY.write_text("# Oracle Repair V1 - Human-Primary Summary\n\n"
                             + render_human_final_section(document), encoding="utf-8")
    update_machine_summary(document)
    STAGE_SUMMARY.write_text(render_stage_summary(document), encoding="utf-8")
    print(json.dumps({"status": document["status"],
                      "repairability": document["repairability_stage"],
                      "case": document["repairability_case"]["case"],
                      "blinded": document["blinded_human_aggregate_before_unblinding"],
                      "by_model": document["unblinded"]["by_model"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
