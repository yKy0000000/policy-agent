"""Human-review writeback and frozen cleaned genuine-error cohort.

Offline, deterministic finalization of Measurement Validity Audit V2: the
pre-registered 20-item human review is written back as a fourth evidence layer
without touching any model artifact, and the cleaned nominal cohort is frozen
for the Repairability stage. No network calls, no production change.

Layers preserved per item:
  1. original judge result (deepseek-v4-flash, frozen in generation utilization)
  2. V2 model adjudication (deepseek-v4-pro, frozen in the V2 audit)
  3. human review (this round, recorded here for the first time)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.generator import GENERATION_PROMPT_VERSION, GROUNDING_SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parents[1]
V1_RESULTS = ROOT / "eval/results/measurement_validity_audit.json"
V2_RESULTS = ROOT / "eval/results/measurement_validity_audit_v2.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
VALIDATION_METADATA = ROOT / "eval/validation/validation_v1_metadata.json"
V3_BENCHMARK = ROOT / "eval/broad_queries_v3_adjudicated.json"
V3_RUBRIC = ROOT / "eval/broad_query_v3_atomic_facts_frozen_candidate.json"
RESULTS = ROOT / "eval/results/measurement_validity_cleaned_cohort.json"
SUMMARY = ROOT / "eval/results/measurement_validity_cleaned_cohort.md"

FROZEN_AT_UTC = "2026-09-26"
ORIGINAL_JUDGE_MODEL = "deepseek-v4-flash"
V1_ADJUDICATOR_MODEL = "deepseek-v4-pro"
V2_ADJUDICATOR_MODEL = "deepseek-v4-pro"

FROZEN_EXPECTED_SHA256 = {
    "eval/validation/broad_atomic_facts_validation_v1.json":
        "451a583f5ce88e0b573e61e5af073e34748b35900fa3ecd3d3f00b001699df50",
    "eval/validation/broad_queries_validation_v1.json":
        "1fb2b03d752343ea19d83283dff92d066febe357178cb93a5cf7c603c1fe4858",
    "eval/broad_queries_v3_adjudicated.json":
        "9e15b40cc5068aa4fc52ce3e7a5c154c90733156f66e5c92bc688c19a6b919e4",
    "eval/broad_query_v3_atomic_facts_frozen_candidate.json":
        "616e0968038a26b27b7a4d8a90293b100d9a2287da0038caa9cbe3f258646534",
    "eval/results/measurement_validity_audit.json":
        "d8d90af8b2e17be167ed4b73c3f649ffec6bb4a3398114ae92f80a458dfcd036",
    "eval/results/measurement_validity_audit_v2.json":
        "516afe9a0185920aae493d01030f2ddee56ba9cee042014ccc569c0d9d1a416f",
    "eval/results/generation_utilization_results.json":
        "01be9f9c3a3c26b845df83475013c12838e67e55eb7967b7c3a4fda15f5d6963",
    "eval/results/reranker_transfer_results.json":
        "bbce7fa512bfbf9d31b719ea3983934ce4a4781ce4caae6bb5751906a59cd589",
    "eval/validation/validation_v1_metadata.json":
        "a91ab96a6c3f25551753b18bf647c718bdd7b3226fe59f3ebece26a2210c0339",
}

HUMAN_REVIEW = {
    "VAL-001-039-F02": {
        "verdict": "ABSENT_OR_INCORRECT",
        "attributed_to": "v2_adjudicator",
        "mechanism": "anchor_drift_false_present",
        "note": ("The anchor requires that GitHub makes an offer to provide source code where "
                 "component licenses require such an offer. The baseline answer discusses Open "
                 "Source Notices and when an open-source license overrides the Application Terms, "
                 "but never states the source-code offer. The V2 model found topically related "
                 "content in the full Top5 evidence without aligning it to the atomic fact "
                 "(topical relevance is not proposition equivalence)."),
    },
    "VAL-001-050-F01": {
        "verdict": "ABSENT_OR_INCORRECT",
        "attributed_to": "v2_adjudicator",
        "mechanism": "over_lenient_semantic_match_incomplete_proposition_coverage",
        "note": ("The anchor requires that, before filing or continuing to prosecute any legal "
                 "proceeding or claim (other than a Defensive Action) arising from termination of "
                 "a Covered License, GitHub commits to extend cure/reinstatement provisions. The "
                 "baseline answer explains the cure/reinstatement mechanism and reinstatement "
                 "conditions, but not the pre-filing commitment or its timing. The V2 model "
                 "treated the related reinstatement content as covering the commitment as well."),
    },
    "VAL-001-008-F02": {
        "verdict": "AMBIGUOUS",
        "attributed_to": "evaluation_case_representation",
        "mechanism": "non_atomic_anchor_target_ambiguity",
        "note": ("The baseline answer covers email as a submission channel and that plain-text "
                 "email is usually faster than a PDF attachment or physical mail, but it does not "
                 "explicitly cover the requirement that an attachment also be accompanied by a "
                 "plain-text version in the email body. The review packet does not state whether "
                 "the atomic target is 'email is an allowed submission channel', 'an attachment "
                 "requires a plain-text copy in the body', or both, so no reliable binary human "
                 "verdict is possible. This is a target-ambiguity / non-atomic-anchor problem, "
                 "not a model error, and the item is excluded from the repair cohort."),
    },
}

_PRESENT = {"verdict": "SEMANTICALLY_PRESENT", "attributed_to": None, "mechanism": None, "note": ""}
for _fact_id in ("VAL-001-009-F01", "VAL-001-009-F02", "VAL-001-011-F01", "VAL-001-022-F02",
                 "VAL-001-026-F02", "VAL-001-037-F01", "VAL-001-050-F05",
                 "VAL-001-008-F01", "VAL-001-008-F03", "VAL-001-009-F03", "VAL-001-011-F03",
                 "VAL-001-022-F03", "VAL-001-004-F02", "VAL-001-007-F03", "VAL-001-017-F03",
                 "VAL-001-024-F03", "VAL-001-042-F05"):
    HUMAN_REVIEW[_fact_id] = dict(_PRESENT)
del _PRESENT, _fact_id

LABELS = ("SEMANTICALLY_PRESENT", "ABSENT_OR_INCORRECT", "AMBIGUOUS")
CONFIRMED_ERROR_FACT_IDS = ("VAL-001-039-F02", "VAL-001-050-F01")
AMBIGUOUS_FACT_IDS = ("VAL-001-008-F02",)
REPAIR_COHORT_EXCLUDED = ("VAL-001-008-F02",)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_frozen() -> dict:
    return {"v1": _json(V1_RESULTS), "v2": _json(V2_RESULTS), "utilization": _json(UTILIZATION),
            "transfer": _json(TRANSFER), "rubric": _json(RUBRIC), "queries": _json(QUERIES)}


def source_artifact_hashes() -> dict[str, str]:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in FROZEN_EXPECTED_SHA256}


def _case_id_of(fact_id: str, case_ids: list[str]) -> str:
    return next(case_id for case_id in case_ids if fact_id.startswith(case_id + "-"))


def _original_judge(utilization: dict, fact_id: str, case_ids: list[str]) -> dict:
    case_id = _case_id_of(fact_id, case_ids)
    row = next(row for row in utilization["cases"] if row["case_id"] == case_id)
    arm = row["arms"]["baseline"]
    fact = next(fact for fact in arm["judge"]["facts"] if fact["fact_id"] == fact_id)
    cause = next((entry["cause"] for entry in arm["pipeline_diagnosis"]
                  if entry["fact_id"] == fact_id), None)
    return {"model": utilization.get("model", ORIGINAL_JUDGE_MODEL),
            "status": fact["status"], "citation_status": fact["citation_status"],
            "pipeline_cause": cause}


def build_writeback(frozen: dict) -> list[dict]:
    v2, utilization = frozen["v2"], frozen["utilization"]
    case_ids = sorted(row["case_id"] for row in utilization["cases"]
                      if row.get("status") == "complete")
    facts = {fact["fact_id"]: fact
             for case in frozen["rubric"]["cases"] for fact in case["facts"]}
    items = []
    for item in v2["selection"]["human_review_items"]:
        fact_id = item["fact_id"]
        if fact_id not in HUMAN_REVIEW:
            raise ValueError(f"human review missing for pre-registered item: {fact_id}")
        human = HUMAN_REVIEW[fact_id]
        if human["verdict"] not in LABELS:
            raise ValueError(f"invalid human verdict for {fact_id}: {human['verdict']}")
        adjudication = v2["adjudications"].get(fact_id)
        if adjudication is None:
            raise ValueError(f"V2 adjudication missing for {fact_id}")
        anchor = v2["anchors"][fact_id]
        items.append({
            "fact_id": fact_id,
            "case_id": _case_id_of(fact_id, case_ids),
            "side": "nominal" if item.get("nominal_type") else "covered",
            "nominal_type": item.get("nominal_type"),
            "stratum": item.get("stratum"),
            "fact_statement": facts[fact_id]["statement"],
            "anchor": {"anchor_chunk_id": anchor["anchor_chunk_id"],
                       "anchor_source_id": anchor["anchor_source_id"],
                       "evidence_chunk_ids": anchor["evidence_chunk_ids"],
                       "evidence_source_ids": anchor["evidence_source_ids"]},
            "original_judge": _original_judge(utilization, fact_id, case_ids),
            "v2_model_adjudication": {"model": V2_ADJUDICATOR_MODEL,
                                      "label": adjudication["label"],
                                      "diagnostic_tag": adjudication["diagnostic_tag"],
                                      "reason": adjudication["reason"]},
            "human_adjudication": human["verdict"],
            "human_note": human["note"],
            "human_reviewed": True,
        })
    if {item["fact_id"] for item in items} != set(HUMAN_REVIEW):
        raise ValueError("writeback items do not match the frozen human review set")
    return items


def agreement_summary(writeback: list[dict]) -> dict:
    disagreements = []
    for item in writeback:
        model_label = item["v2_model_adjudication"]["label"]
        if item["human_adjudication"] == model_label:
            continue
        human = HUMAN_REVIEW[item["fact_id"]]
        disagreements.append({
            "fact_id": item["fact_id"],
            "human_adjudication": item["human_adjudication"],
            "v2_model_adjudication": model_label,
            "attributed_to": human["attributed_to"],
            "mechanism": human["mechanism"],
            "note": human["note"],
        })
    agreed = len(writeback) - len(disagreements)
    return {
        "subset_size": len(writeback),
        "v2_model_labels": {label: sum(1 for item in writeback
                                       if item["v2_model_adjudication"]["label"] == label)
                            for label in LABELS},
        "human_labels": {label: sum(1 for item in writeback
                                    if item["human_adjudication"] == label) for label in LABELS},
        "exact_agreement": {"numerator": agreed, "denominator": len(writeback),
                            "proportion": agreed / len(writeback)},
        "disagreement": {"numerator": len(disagreements), "denominator": len(writeback),
                         "proportion": len(disagreements) / len(writeback),
                         "items": disagreements},
        "classification_note": ("039-F02 and 050-F01 are V2-adjudicator errors of different kinds "
                                "(anchor drift / false PRESENT; over-lenient incomplete "
                                "proposition coverage). 008-F02 is not a model error: the human "
                                "reviewer could not reliably determine the atomic target because "
                                "the anchor is non-atomic."),
    }


def _human_reviewed_covered_ids(v2: dict) -> list[str]:
    return [item["fact_id"] for item in v2["selection"]["human_review_items"]
            if not item.get("nominal_type")]


def build_document() -> dict:
    frozen = load_frozen()
    v1, v2, utilization = frozen["v1"], frozen["v2"], frozen["utilization"]
    writeback = build_writeback(frozen)
    by_id = {item["fact_id"]: item for item in writeback}
    covered_items = [item for item in writeback if item["side"] == "covered"]

    nominal_ids = [item["fact_id"] for item in v2["selection"]["nominal_problematic_facts"]]
    confirmed_errors = [{"fact_id": fact_id, "case_id": by_id[fact_id]["case_id"],
                         "nominal_type": by_id[fact_id]["nominal_type"],
                         "original_judge": by_id[fact_id]["original_judge"],
                         "v2_model_adjudication": by_id[fact_id]["v2_model_adjudication"],
                         "human_adjudication": by_id[fact_id]["human_adjudication"],
                         "human_note": by_id[fact_id]["human_note"]}
                        for fact_id in CONFIRMED_ERROR_FACT_IDS]
    ambiguous = [{"fact_id": fact_id, "case_id": by_id[fact_id]["case_id"],
                  "nominal_type": by_id[fact_id]["nominal_type"],
                  "human_note": by_id[fact_id]["human_note"]} for fact_id in AMBIGUOUS_FACT_IDS]
    confirmed_present_ids = [fact_id for fact_id in nominal_ids
                             if fact_id not in CONFIRMED_ERROR_FACT_IDS
                             and fact_id not in AMBIGUOUS_FACT_IDS]

    covered_ids = list(v2["selection"]["stratum_a_facts"]) + list(v2["selection"]["stratum_b_facts"])
    reviewed_covered = _human_reviewed_covered_ids(v2)
    model_only_covered = [fact_id for fact_id in covered_ids if fact_id not in reviewed_covered]
    covered_counts = {}
    for fact_id in covered_ids:
        label = v2["adjudications"][fact_id]["label"]
        covered_counts[label] = covered_counts.get(label, 0) + 1

    def layer_counts(labels: dict) -> dict:
        return {label: sum(1 for fact_id in nominal_ids if labels.get(fact_id) == label)
                for label in LABELS}

    original_statuses = {fact_id: by_id[fact_id]["original_judge"]["status"]
                         for fact_id in nominal_ids}
    v1_labels = {fact_id: v1["adjudications"][fact_id]["label"] for fact_id in nominal_ids}
    v2_labels = {fact_id: v2["adjudications"][fact_id]["label"] for fact_id in nominal_ids}

    prompt_sha = _sha256_text(GROUNDING_SYSTEM_PROMPT)
    artifacts = source_artifact_hashes()
    return {
        "schema_version": 1,
        "version": "measurement-validity-cleaned-cohort-v1",
        "status": "frozen",
        "validate_stage": "COMPLETE",
        "frozen_at_utc": FROZEN_AT_UTC,
        "scope_note": ("Human-review writeback and cleaned nominal cohort for Measurement Validity "
                       "Audit V2. Human verdicts are added as a fourth layer; no model artifact is "
                       "modified. Only the pre-registered 20-item subset was human reviewed: the 10 "
                       "nominal problematic facts and 10 of the 40 covered-side facts. Model "
                       "adjudication evidence (V2 40/40 covered PRESENT) is not human-confirmed "
                       "ground truth."),
        "human_review": {
            "subset_size": len(writeback),
            "subset_construction": ("V2 selection.human_review_items: 10 nominal problematic facts "
                                    "+ 5 stratum A covered facts + 5 stratum B covered facts"),
            "review_mode": "pre-registered blind human review before model comparison",
            "frozen_human_review_writeback": writeback,
            "agreement": agreement_summary(writeback),
        },
        "layer_summary_nominal": {
            "original_judge": {"model": ORIGINAL_JUDGE_MODEL,
                               "missing": sum(1 for status in original_statuses.values()
                                              if status == "missing"),
                               "incorrect": sum(1 for status in original_statuses.values()
                                                if status == "incorrect"),
                               "covered": sum(1 for status in original_statuses.values()
                                              if status == "covered")},
            "v1_adjudicator": {"model": V1_ADJUDICATOR_MODEL, **layer_counts(v1_labels)},
            "v2_adjudicator": {"model": V2_ADJUDICATOR_MODEL, **layer_counts(v2_labels)},
            "human_review": {"SEMANTICALLY_PRESENT": sum(
                1 for fact_id in nominal_ids if by_id[fact_id]["human_adjudication"]
                == "SEMANTICALLY_PRESENT"),
                "ABSENT_OR_INCORRECT": sum(
                    1 for fact_id in nominal_ids if by_id[fact_id]["human_adjudication"]
                    == "ABSENT_OR_INCORRECT"),
                "AMBIGUOUS": sum(1 for fact_id in nominal_ids
                                 if by_id[fact_id]["human_adjudication"] == "AMBIGUOUS")},
        },
        "cleaned_nominal_cohort": {
            "counts": {"nominal_problematic_facts": len(nominal_ids),
                       "confirmed_errors": len(CONFIRMED_ERROR_FACT_IDS),
                       "ambiguous": len(AMBIGUOUS_FACT_IDS),
                       "confirmed_present": len(confirmed_present_ids)},
            "confirmed_errors": confirmed_errors,
            "ambiguous": ambiguous,
            "confirmed_present_fact_ids": confirmed_present_ids,
            "repair_cohort": {"fact_ids": list(CONFIRMED_ERROR_FACT_IDS),
                              "excluded": [{"fact_id": fact_id,
                                            "reason": "non_atomic_anchor_target_ambiguity"}
                                           for fact_id in REPAIR_COHORT_EXCLUDED]},
        },
        "covered_side": {
            "covered_sample_size": len(covered_ids),
            "v2_model_labels": covered_counts,
            "human_reviewed_subset_size": len(covered_items),
            "human_reviewed_fact_ids": reviewed_covered,
            "human_confirmed_present": sum(1 for item in covered_items
                                           if item["human_adjudication"]
                                           == "SEMANTICALLY_PRESENT"),
            "model_only_fact_ids": model_only_covered,
            "interpretation": ("The V2 model adjudicated all 40 covered-side facts as "
                               "SEMANTICALLY_PRESENT, but only the 10 pre-registered human-review "
                               "items are human-confirmed. Do not report 40/40 as human-confirmed."),
        },
        "production": {
            "generation_prompt_version": GENERATION_PROMPT_VERSION,
            "generation_prompt_sha256": prompt_sha,
            "generator_model": ORIGINAL_JUDGE_MODEL,
            "baseline_answer_source": ("eval/results/generation_utilization_results.json: "
                                       "cases[].arms.baseline.answer"),
        },
        "source_artifacts": artifacts,
    }


def validate_document(document: dict) -> None:
    artifacts = document["source_artifacts"]
    for relative, expected in FROZEN_EXPECTED_SHA256.items():
        if artifacts[relative] != expected:
            raise ValueError(f"frozen source artifact changed: {relative}")
    v2 = _json(V2_RESULTS)
    if v2.get("v1_reference_sha256") != FROZEN_EXPECTED_SHA256[
            "eval/results/measurement_validity_audit.json"]:
        raise ValueError("V2 no longer references the frozen V1 artifact")
    agreement = document["human_review"]["agreement"]
    if agreement["disagreement"]["numerator"] != 3 or agreement["subset_size"] != 20:
        raise ValueError("unexpected human/model agreement structure")
    cohort = document["cleaned_nominal_cohort"]
    if cohort["repair_cohort"]["fact_ids"] != list(CONFIRMED_ERROR_FACT_IDS):
        raise ValueError("repair cohort must be exactly the two confirmed errors")
    if any(item["fact_id"] not in REPAIR_COHORT_EXCLUDED for item in cohort["ambiguous"]):
        raise ValueError("ambiguous list must contain the excluded non-atomic item")
    writeback = document["human_review"]["frozen_human_review_writeback"]
    if any(item["human_adjudication"] not in LABELS for item in writeback):
        raise ValueError("invalid human label in writeback")
    for item in writeback:
        if not item["human_reviewed"]:
            raise ValueError("all writeback items must be marked human reviewed")


def render_markdown(document: dict) -> str:
    writeback = document["human_review"]["frozen_human_review_writeback"]
    agreement = document["human_review"]["agreement"]
    cohort = document["cleaned_nominal_cohort"]
    covered = document["covered_side"]
    layers = document["layer_summary_nominal"]
    lines = ["# Measurement Validity Cleaned Cohort (frozen)", "",
             "> " + document["scope_note"].replace("\n", " "), "",
             f"- status: {document['status']}",
             f"- validate stage: {document['validate_stage']}",
             f"- frozen at: {document['frozen_at_utc']}", "",
             "## Human-review writeback (three layers preserved)", "",
             "| fact | side | type/stratum | original judge | V2 model | human |",
             "|---|---|---|---|---|---|"]
    for item in writeback:
        kind = item["nominal_type"] or (f"stratum {item['stratum']}" if item["stratum"] else "covered")
        judge = item["original_judge"]
        original = f"{judge['status']} / {judge['citation_status']}"
        lines.append(f"| {item['fact_id']} | {item['side']} | {kind} | {original} | "
                     f"{item['v2_model_adjudication']['label']} | {item['human_adjudication']} |")
    lines += ["", "## Human vs V2 model agreement", "",
              f"- subset size: {agreement['subset_size']}",
              f"- V2 model labels: {agreement['v2_model_labels']}",
              f"- human labels: {agreement['human_labels']}",
              f"- exact agreement: {agreement['exact_agreement']['numerator']}/"
              f"{agreement['exact_agreement']['denominator']} = "
              f"{agreement['exact_agreement']['proportion']:.0%}",
              f"- disagreement: {agreement['disagreement']['numerator']}/"
              f"{agreement['disagreement']['denominator']} = "
              f"{agreement['disagreement']['proportion']:.0%}", "",
              "### Disagreement detail", ""]
    for item in agreement["disagreement"]["items"]:
        lines += [f"- `{item['fact_id']}` (V2 {item['v2_model_adjudication']} → human "
                  f"{item['human_adjudication']}; attributed to {item['attributed_to']}, "
                  f"mechanism: {item['mechanism']}): {item['note']}", ""]
    lines += ["## Layer summary (10 nominal problematic facts)", "",
              f"- original judge ({layers['original_judge']['model']}): "
              f"missing {layers['original_judge']['missing']}, "
              f"incorrect {layers['original_judge']['incorrect']}, "
              f"covered {layers['original_judge']['covered']}",
              f"- V1 adjudicator ({layers['v1_adjudicator']['model']}): "
              f"{[f'{k}={v}' for k, v in layers['v1_adjudicator'].items() if k != 'model']}",
              f"- V2 adjudicator ({layers['v2_adjudicator']['model']}): "
              f"{[f'{k}={v}' for k, v in layers['v2_adjudicator'].items() if k != 'model']}",
              f"- human review: {layers['human_review']}", "",
              "## Cleaned nominal cohort", "",
              f"- nominal problematic facts: {cohort['counts']['nominal_problematic_facts']}",
              f"- confirmed errors: {cohort['counts']['confirmed_errors']} "
              f"({[item['fact_id'] for item in cohort['confirmed_errors']]})",
              f"- ambiguous: {cohort['counts']['ambiguous']} "
              f"({[item['fact_id'] for item in cohort['ambiguous']]})",
              f"- human-confirmed present: {cohort['counts']['confirmed_present']} "
              f"({cohort['confirmed_present_fact_ids']})", "",
              "Repair cohort (Repairability stage): "
              f"{cohort['repair_cohort']['fact_ids']}; excluded: "
              f"{[item['fact_id'] for item in cohort['repair_cohort']['excluded']]}.", "",
              "## Covered side", "",
              f"- covered-side sample: {covered['covered_sample_size']}",
              f"- V2 model labels: {covered['v2_model_labels']} (model evidence only)",
              f"- human-reviewed subset: {covered['human_reviewed_subset_size']} "
              f"({covered['human_reviewed_fact_ids']})",
              f"- human-confirmed present in subset: {covered['human_confirmed_present']}",
              f"- model-only facts without human gold: "
              f"{len(covered['model_only_fact_ids'])}",
              f"- caveat: {covered['interpretation']}", "",
              "## Integrity", "",
              f"- production generation prompt: {document['production']['generation_prompt_version']} "
              f"(sha256 {document['production']['generation_prompt_sha256'][:16]})",
              f"- generator / original judge model: {document['production']['generator_model']}",
              "- frozen source artifact hashes:"]
    for relative, digest in sorted(document["source_artifacts"].items()):
        lines.append(f"  - `{relative}`: `{digest[:16]}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    document = build_document()
    validate_document(document)
    _write(RESULTS, document)
    SUMMARY.write_text(render_markdown(document), encoding="utf-8")
    agreement = document["human_review"]["agreement"]
    print(json.dumps({"cohort": document["cleaned_nominal_cohort"]["counts"],
                      "agreement": {"exact": agreement["exact_agreement"],
                                    "disagreement": agreement["disagreement"]["numerator"]},
                      "covered": {"model": document["covered_side"]["v2_model_labels"],
                                  "human_reviewed": document["covered_side"]
                                  ["human_reviewed_subset_size"]}},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
