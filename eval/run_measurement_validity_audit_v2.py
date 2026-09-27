"""Measurement Validity Audit V2: V1 with the adjudication packet-scope flaw fixed.

Single intervention vs V1: the adjudicator now sees the FULL frozen BGE Top5 evidence
the generator saw (with source IDs, headings, chunk boundaries), instead of one narrow
mapped span; and AMBIGUOUS is an explicit, non-penalized outcome when the full evidence
still cannot decide. Selection, baseline answers, adjudicator model, labels, and
diagnostic tags are reused verbatim from the frozen V1 audit. V1 artifacts are untouched.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from eval.run_answer_eval import _V3Cache, _sha256, _stable_hash
from eval.run_measurement_validity_audit import (LABELS, SEED, STRATUM_A_EXTRA, _json,
                                                 _write, nominal_problematic_facts,
                                                 parse_adjudication, sample_stratum_a,
                                                 sample_stratum_b, wilson_interval,
                                                 cleaned_cohort)
from eval.run_validation import direct_support_map
from src.generator import assign_evidence_sources, format_evidence
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

ROOT = Path(__file__).resolve().parents[1]
V1_RESULTS = ROOT / "eval/results/measurement_validity_audit.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
INDEX = ROOT / "cache/policy_index.json"
TRANSFER = ROOT / "eval/results/reranker_transfer_results.json"
UTILIZATION = ROOT / "eval/results/generation_utilization_results.json"
CACHE = ROOT / "cache/measurement_validity_audit_v2_cache.json"
RESULTS = ROOT / "eval/results/measurement_validity_audit_v2.json"
SUMMARY = ROOT / "eval/results/measurement_validity_audit_v2.md"
HUMAN_SHEET = ROOT / "eval/results/measurement_validity_audit_v2_human_review.md"

ADJUDICATOR_MODEL = "deepseek-v4-pro"

V2_SYSTEM = (
    "You are a rigorous policy-answer adjudicator. You receive: the user question, an answer, "
    "an ANCHOR span naming the specific information to check, and the FULL frozen evidence "
    "(sources S1..Sn) that the answer writer actually saw. Decide whether the answer, judged "
    "against the full evidence, already conveys the anchor information and whether any statement "
    "of it is semantically correct in condition, scope, actor, relation, and conclusion. Do not "
    "require literal wording. Ignore citation-marker bookkeeping; judge content, not which source "
    "ID is attached. The answer may legitimately draw on any part of the full evidence. If the "
    "full evidence is still insufficient to decide reliably, or the source support is genuinely "
    "ambiguous, return AMBIGUOUS with the reason; never force ABSENT_OR_INCORRECT when you cannot "
    "verify that the information is absent or wrong. Reply with JSON only: "
    '{\"label\":\"SEMANTICALLY_PRESENT|ABSENT_OR_INCORRECT|AMBIGUOUS\",'
    '\"diagnostic_tag\":\"genuine_omission|incorrect_synthesis|paraphrase|merged_expression|'
    'rubric_overgranular|judge_error|unclear_source|other\",\"reason\":\"brief\"}.')


# --------------------------------------------------------------------------- #
# Frozen V1 selection (load + independently re-derive, then assert equal)
# --------------------------------------------------------------------------- #

def load_frozen_selection() -> tuple[dict, dict]:
    v1 = _json(V1_RESULTS)
    stored = v1["selection"]
    utilization = _json(UTILIZATION)
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    covered_by_case = {case_id: [fact["fact_id"] for fact in row["arms"]["baseline"]["judge"]["facts"]
                                 if fact["status"] == "covered"]
                       for case_id, row in rows.items()}
    controls = [case_id for case_id, row in rows.items()
                if row["arms"]["baseline"]["quality"]["grounded_fact_complete"]]
    nominal = nominal_problematic_facts(utilization)
    stratum_a = sample_stratum_a(sorted(set(utilization["cohort"]["gap_ids"]) | set(STRATUM_A_EXTRA)),
                                 covered_by_case, __import__("random").Random(SEED))
    stratum_b = sample_stratum_b(controls, covered_by_case, __import__("random").Random(SEED))
    if ([i["fact_id"] for i in nominal] != [i["fact_id"] for i in stored["nominal_problematic_facts"]]
            or stratum_a != stored["stratum_a_facts"] or stratum_b != stored["stratum_b_facts"]):
        raise ValueError("V2 recomputed selection differs from frozen V1 selection")
    covered_sample = [{"fact_id": fid, "stratum": "A"} for fid in stratum_a] + \
                     [{"fact_id": fid, "stratum": "B"} for fid in stratum_b]
    return stored, {"nominal": nominal, "covered_sample": covered_sample}


# --------------------------------------------------------------------------- #
# V2 packet: full frozen BGE Top5 evidence + anchor
# --------------------------------------------------------------------------- #

def build_v2_packet(query: str, answer: str, chunks: list[dict], anchor_excerpt: str,
                    anchor_source_id: str, anchor_meta: dict) -> dict:
    sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
    full_evidence = [{"source_id": source.citation_id, "title": source.title,
                      "heading_path": list(source.heading_path), "content": source.text}
                     for source in sources]
    return {"question": query, "answer": answer,
            "anchor": {"source_id": anchor_source_id, "document": anchor_meta["document"],
                       "section": anchor_meta.get("section", ""), "excerpt": anchor_excerpt},
            "full_evidence": full_evidence,
            "evidence_text": format_evidence(sources)}


def packet_leaks(packet: dict, forbidden: list[str]) -> list[str]:
    serialized = json.dumps(packet, ensure_ascii=False)
    return [token for token in forbidden if token in serialized]


# --------------------------------------------------------------------------- #
# Adjudication (V2 cache + V2 prompt)
# --------------------------------------------------------------------------- #

def adjudicate_v2(packet: dict, cache: _V3Cache, client, failures: list,
                  item_id: str) -> dict | None:
    key = _stable_hash({"version": "measurement-validity-v2", "model": client.config.model,
                        "packet": packet})
    cached = cache.get(key)
    if cached is None:
        messages = [{"role": "system", "content": V2_SYSTEM},
                    {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}]
        try:
            raw, usage = client.complete_with_usage(messages, max_tokens=400, temperature=0.0)
            cached = {"kind": "adjudication_v2", "model": client.config.model,
                      "parsed": parse_adjudication(raw), "raw_hash": _stable_hash(raw),
                      "provider_usage": usage}
            cache.set(key, cached)
        except Exception as error:
            failures.append({"kind": "adjudication_v2", "item": item_id,
                             "error": f"{type(error).__name__}: {error}"})
            return None
    return cached["parsed"]


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def run(*, skip_adjudication: bool = False, human_reviewed: dict[str, str] | None = None) -> dict:
    stored, selection = load_frozen_selection()
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    index = _json(INDEX)
    transfer = _json(TRANSFER)
    utilization = _json(UTILIZATION)
    rows = {row["case_id"]: row for row in utilization["cases"] if row["status"] == "complete"}
    qmap = {case["case_id"]: case["query"] for case in queries["cases"]}
    facts = {fact["fact_id"]: fact for case in rubric["cases"] for fact in case["facts"]}
    support = direct_support_map(rubric, index["chunks"])
    bge_chunks = {case_id: item["chunks"]
                  for case_id, item in transfer["preparation"]["arms"]["bge_top5"].items()}

    items = ([(i["fact_id"], "nominal") for i in selection["nominal"]]
             + [(i["fact_id"], "covered") for i in selection["covered_sample"]])
    packets, anchors = {}, {}
    for fact_id, _ in items:
        case_id = next(c for c in rows if fact_id.startswith(c + "-"))
        chunks = bge_chunks[case_id]
        gold = support[fact_id][0]
        position = next((i for i, chunk in enumerate(chunks) if chunk["chunk_id"] == gold), None)
        if position is None:
            raise ValueError(f"anchor chunk not in frozen BGE Top5: {fact_id}")
        anchor_source_id = f"S{position + 1}"
        anchor_meta = facts[fact_id]["support"][0]
        packets[fact_id] = build_v2_packet(qmap[case_id], rows[case_id]["arms"]["baseline"]["answer"],
                                           chunks, anchor_meta["source_excerpt"],
                                           anchor_source_id, anchor_meta)
        anchors[fact_id] = {"case_id": case_id, "anchor_chunk_id": gold,
                            "anchor_source_id": anchor_source_id,
                            "evidence_chunk_ids": [chunk["chunk_id"] for chunk in chunks],
                            "evidence_source_ids": [f"S{i+1}" for i in range(len(chunks))]}

    config = LLMConfig.from_env(ROOT / ".env")
    cache = _V3Cache(CACHE)
    failures: list = []
    adjudicator = OpenAIChatCompletionsClient(replace(config, model=ADJUDICATOR_MODEL))
    adjudications: dict[str, dict] = {}
    if not skip_adjudication:
        for fact_id, kind in items:
            verdict = adjudicate_v2(packets[fact_id], cache, adjudicator, failures, fact_id)
            adjudications[fact_id] = {"kind": kind, "anchor": anchors[fact_id],
                                      **(verdict or {"label": "FAILED",
                                                     "diagnostic_tag": "other", "reason": ""})}
            print(f"V2 {fact_id} ({kind}) -> {adjudications[fact_id]['label']}", flush=True)

    result = _finalize(stored, selection, anchors, adjudications, packets, human_reviewed, failures)
    _write(RESULTS, result)
    _write(SUMMARY, _render(result))
    _write(HUMAN_SHEET, _render_human_sheet(result, packets))
    return result


def _finalize(stored, selection, anchors, adjudications, packets, human_reviewed, failures) -> dict:
    nominal = selection["nominal"]
    omission = [i for i in nominal if i["nominal_type"] == "omission"]
    incorrect = [i for i in nominal if i["nominal_type"] == "incorrect_synthesis"]
    covered = selection["covered_sample"]

    def tally(items):
        counts = {label: 0 for label in LABELS}
        for item in items:
            label = adjudications.get(item["fact_id"], {}).get("label")
            if label in counts:
                counts[label] += 1
        return counts

    def proportion(items, target="ABSENT_OR_INCORRECT"):
        k = sum(1 for item in items
                if adjudications.get(item["fact_id"], {}).get("label") == target)
        lo, hi = wilson_interval(k, len(items))
        return {"numerator": k, "denominator": len(items),
                "proportion": k / len(items) if items else None, "wilson_95": [lo, hi]}

    v1 = _json(V1_RESULTS)["adjudications"]
    v1_tag = sum(1 for f, a in v1.items() if a.get("diagnostic_tag") == "unclear_source")
    v2_tag = sum(1 for f, a in adjudications.items() if a.get("diagnostic_tag") == "unclear_source")

    def transitions(items):
        table = {}
        for item in items:
            fid = item["fact_id"]
            before = v1.get(fid, {}).get("label", "MISSING")
            after = adjudications.get(fid, {}).get("label", "MISSING")
            table.setdefault(before, {})
            table[before][after] = table[before].get(after, 0) + 1
        return table

    cleaned = cleaned_cohort(nominal, adjudications, human_reviewed)
    return {"schema_version": 1, "version": "measurement-validity-audit-v2", "status": "complete",
            "scope_note": ("V1 confirmation ablation. Single intervention: adjudicator packet now "
                           "carries the full frozen BGE Top5 evidence and AMBIGUOUS is a real "
                           "outcome. Selection/baseline answers/model/labels reused from V1; V1 "
                           "artifacts untouched. Same-family adjudicator (deepseek-v4-pro)."),
            "v1_reference_sha256": _sha256(V1_RESULTS),
            "selection_reused_from_v1": True,
            "selection": stored,
            "anchors": anchors,
            "adjudications": adjudications,
            "nominal_side": {"omission": {"counts": tally(omission),
                                          "real_error": proportion(omission)},
                             "incorrect_synthesis": {"counts": tally(incorrect),
                                                     "real_error": proportion(incorrect)},
                             "combined_descriptive": proportion(nominal)},
            "covered_side": {"counts": tally(covered),
                             "genuinely_covered": proportion(covered, "SEMANTICALLY_PRESENT"),
                             "hidden_error": proportion(covered, "ABSENT_OR_INCORRECT"),
                             "ambiguous": tally(covered)["AMBIGUOUS"],
                             "real_covered_proportion": (
                                 (len(covered) - proportion(covered)["numerator"] - tally(covered)["AMBIGUOUS"])
                                 / len(covered) if covered else None)},
            "transitions": {"nominal": transitions(nominal), "covered": transitions(covered)},
            "diagnostic_tags": {"v1_unclear_source": v1_tag, "v2_unclear_source": v2_tag},
            "cleaned_cohort": cleaned, "failures": failures}


def _render(result: dict) -> str:
    n, c = result["nominal_side"], result["covered_side"]
    lines = ["# Measurement Validity Audit V2", "", "> " + result["scope_note"], "",
             f"- V1 reference sha256: `{result['v1_reference_sha256'][:16]}`",
             f"- selection reused from V1: {result['selection_reused_from_v1']}", "",
             "## Nominal side",
             f"- omission counts: {n['omission']['counts']}; real error {n['omission']['real_error']}",
             f"- incorrect_synthesis counts: {n['incorrect_synthesis']['counts']}; "
             f"real error {n['incorrect_synthesis']['real_error']}",
             f"- combined descriptive: {n['combined_descriptive']}", "", "## Covered side",
             f"- counts: {c['counts']}",
             f"- genuinely covered: {c['genuinely_covered']}",
             f"- hidden error: {c['hidden_error']}",
             f"- ambiguous: {c['ambiguous']}",
             f"- P(real covered | judge=covered): {c['real_covered_proportion']}", "",
             "## V1 -> V2 transitions",
             f"- nominal: {result['transitions']['nominal']}",
             f"- covered: {result['transitions']['covered']}", "",
             "## Diagnostic tags",
             f"- unclear_source V1: {result['diagnostic_tags']['v1_unclear_source']}; "
             f"V2: {result['diagnostic_tags']['v2_unclear_source']}", "",
             "## Cleaned cohort",
             f"- status: {result['cleaned_cohort']['status']}",
             f"- genuine_error_facts: {[i['fact_id'] for i in result['cleaned_cohort']['genuine_error_facts']]}",
             f"- ambiguous: {result['cleaned_cohort']['ambiguous_facts']}",
             f"- semantically_present: {result['cleaned_cohort']['semantically_present_facts']}", "",
             "## Failures", f"- {result['failures']}", ""]
    return "\n".join(lines)


def _render_human_sheet(result: dict, packets: dict) -> str:
    lines = ["# Measurement Validity Audit V2 - Blind Human Review Sheet", "",
             "Same information the V2 adjudicator saw: query, baseline answer, full frozen BGE Top5 evidence.",
             "Record your verdict BEFORE comparing with any model.",
             "Allowed verdicts: SEMANTICALLY_PRESENT / ABSENT_OR_INCORRECT / AMBIGUOUS", ""]
    for item in result["selection"]["human_review_items"]:
        fact_id = item["fact_id"]
        packet = packets[fact_id]
        evidence = "\n".join(
            f"[{entry['source_id']}] {entry['title']} :: {' > '.join(entry['heading_path']) or 'Document introduction'}\n"
            f"{entry['content']}" for entry in packet["full_evidence"])
        lines += [f"## {fact_id}" + (f" ({item['nominal_type']})" if item.get("nominal_type") else ""),
                  f"- question: {packet['question']}",
                  f"- answer: {packet['answer']}",
                  f"- anchor: [{packet['anchor']['source_id']}] {packet['anchor']['excerpt']}",
                  f"- full_evidence:\n{evidence}",
                  "- your_verdict: ", "- your_note: ", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-adjudication", action="store_true")
    args = parser.parse_args(argv)
    result = run(skip_adjudication=args.skip_adjudication)
    print(json.dumps({"nominal": result["nominal_side"], "covered": result["covered_side"],
                      "tags": result["diagnostic_tags"], "transitions": result["transitions"],
                      "failures": result["failures"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
