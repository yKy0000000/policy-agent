"""Freeze the approved human-truth labels and rescore the frozen Stage 0 contexts.

Offline only: reads the five selected-context policies from the Stage 0 replay,
does not run retrieval, generation, a model, or an API. Does not edit Stage 0 files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


POLICIES = (
    "fixed_top5",
    "adaptive_prefix_v1",
    "coverage_selector_v2",
    "no_router_adaptive_v1",
    "query_router_v1",
)
VERDICTS = {"QUERY_REQUIRED", "RELEVANT_BUT_OPTIONAL", "AMBIGUOUS"}
RESOLUTIONS = {
    "VAL-001-003-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting the separate copyright referral still answers which disclosures fall outside private-information removal."),
    "VAL-001-007-F02": ("RELEVANT_BUT_OPTIONAL", "Omitting advice about professional review of bulk submissions leaves this individual's preparation and delay question complete."),
    "VAL-001-007-F03": ("QUERY_REQUIRED", "Omitting the high-risk scope and inability to bundle unrelated requests leaves material preparation and delay limits unanswered."),
    "VAL-001-022-F05": ("RELEVANT_BUT_OPTIONAL", "Omitting a generic statement that GitHub follows legal limits does not omit a concrete disclosure rule requested by the query."),
    "VAL-001-031-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting one illustrative higher-risk supplier category still permits a complete account of risk identification and response."),
    "VAL-001-032-F01": ("RELEVANT_BUT_OPTIONAL", "Omitting generic agreement compliance still answers the specific Actions compute and delivery limits and misuse consequences."),
    "VAL-001-036-F03": ("QUERY_REQUIRED", "Omitting the immediate emergency route leaves the asked urgent-reporting path incomplete."),
    "VAL-001-040-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting general-availability-equivalent data handling still answers internal evaluation and production-use permission."),
    "VAL-001-040-F05": ("RELEVANT_BUT_OPTIONAL", "Omitting the DPA start-date detail still answers whether evaluation and live-customer production use are allowed."),
    "VAL-001-044-F01": ("RELEVANT_BUT_OPTIONAL", "Omitting where Enterprise Server is hosted still answers permission for export-controlled material and remaining export limits."),
    "VAL-001-048-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting SIRT's internal risk and priority triage detail still explains the SIRT/customer responsibility boundary."),
    "VAL-001-048-F05": ("QUERY_REQUIRED", "Omitting SIRT's investigation of whether an incident occurred and its impact leaves its asked handling role incomplete."),
    "V3-02-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting the approximate one-business-day window still explains what may happen before and after disablement."),
    "V3-03-F04": ("RELEVANT_BUT_OPTIONAL", "Omitting line-number precision still explains how GitHub handles a secret-removal request."),
    "V3-03-F07": ("QUERY_REQUIRED", "Omitting the repository owner's dispute route leaves a material branch of the requested handling process incomplete."),
    "V3-05-F04": ("QUERY_REQUIRED", "Omitting payment-method removal leaves part of what GitHub can still do for a locked account unanswered."),
    "V3-14-F06": ("RELEVANT_BUT_OPTIONAL", "Omitting who makes the final appeal decision still explains what can be challenged and how to seek restoration."),
}
STAGE0_HASHES = {
    "eval/query_aware_stage0_config.json": "744ed411e301aaf28a3751be99c31157b26dcbcf524673f749aa711d2a82e3a6",
    "eval/query_aware_router_v1.json": "dcc7d4953f3ba9794c35f2168e29f419bbb40eb014775cf8ccb5e0e7ae913bd7",
    "eval/query_aware_arms_v1.json": "18d7adbfd1ac8a1802dbf29d2c222fb988d0c495ca4f979c24297a406f0112c9",
    "eval/results/a0_bge_rerank_orders.json": "fb15b316c4b5170514e6f1c5140689ba0e77869dd516b7c7e170593c4db5b2e2",
    "eval/results/human_truth_stage0_worksheet.json": "86926d6290a60f5a9b9b1ad2ffa638a6206e028bfa0d97a8581f7aa632f3244b",
    "eval/results/stage0_replay_results.json": "5e7d665bdae13803dd00d39756881f55e5a6792eb01ca37d0e2f63a4e1563703",
    "eval/human_truth_contract_v1.md": "1b131832cbca8d3529473d65dbb3c48ea80957c88aead225f147ff6870aa6d74",
    "eval/economics_contract_v1.md": "8ec4f46dc10e9fc36fdee9dd17b34915ae6cd2eef8b7c969a6504208e5c77540",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_once(path: Path, content: str):
    data = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing frozen output differs: {path}")
        return
    path.write_bytes(data)


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def verify_stage0(root: Path) -> dict:
    config = load(root / "eval/query_aware_stage0_config.json")
    expected = {**config["artifact_hashes"], **STAGE0_HASHES}
    mismatches = {relative: {"expected": digest, "actual": sha256(root / relative)}
                  for relative, digest in expected.items()
                  if sha256(root / relative) != digest}
    if mismatches:
        raise ValueError(f"Frozen Stage 0 hash mismatch: {mismatches}")
    return {"checked": len(expected), "mismatches": [], "hashes": STAGE0_HASHES}


def freeze_truth(root: Path, out: Path, hash_audit: dict) -> tuple[dict, str]:
    base = root / "eval/results"
    source_names = (
        "human_truth_stage0_worksheet.json",
        "human_truth_reviewer1_v1.json",
        "human_truth_reviewer2_v1.json",
        "human_truth_disagreements_v1.json",
    )
    worksheet, r1, r2, packet = (load(base / name) for name in source_names)
    rows = worksheet["items"]
    ids = [row["aspect_id"] for row in rows]
    labels1, labels2 = r1["judgments"], r2["items"]
    assert worksheet["status"] == "pending_human_verdicts"
    assert len(ids) == len(set(ids)) == len(labels1) == len(labels2) == 331
    assert [x["aspect_id"] for x in labels1] == [x["aspect_id"] for x in labels2] == ids
    assert all(x["verdict"] in VERDICTS and x.get("reason") for x in labels1 + labels2)
    assert all(row["verdict"] is row["reviewer_1"] is row["reviewer_2"] is row["final"] is None for row in rows)
    candidate = {x["aspect_id"]: x["candidate_final"] for x in packet["agreement_candidates"]}
    disputed = {x["aspect_id"]: x for x in packet["disagreements"]}
    assert len(candidate) == 314 and len(disputed) == len(RESOLUTIONS) == 17
    assert set(candidate).isdisjoint(disputed) and set(candidate) | set(disputed) == set(ids)
    assert set(disputed) == set(RESOLUTIONS)
    assert len(worksheet["sentinel_queries"]) == len(set(worksheet["sentinel_queries"])) == 8
    items = []
    initial_agreements = 0
    for row, one, two in zip(rows, labels1, labels2):
        aspect_id = row["aspect_id"]
        if one["verdict"] == two["verdict"]:
            assert aspect_id in candidate and candidate[aspect_id] == one["verdict"]
            final, reason, basis = one["verdict"], None, "independent_reviewer_agreement"
            initial_agreements += 1
        else:
            assert aspect_id in disputed
            entry = disputed[aspect_id]
            assert entry["reviewer_1"]["verdict"] == one["verdict"]
            assert entry["reviewer_2"]["verdict"] == two["verdict"]
            assert entry["original_query"] == row["query"]
            assert entry["aspect_statement"] == row["statement"]
            final, reason = RESOLUTIONS[aspect_id]
            basis = "user_confirmed_final_adjudication"
        assert final in VERDICTS
        item = dict(row)
        item.update(verdict=final, reviewer_1=one["verdict"], reviewer_2=two["verdict"],
                    final=final, adjudication_basis=basis, resolution_reason=reason)
        items.append(item)
    assert initial_agreements == 314
    counts = Counter(item["final"] for item in items)
    assert (counts["QUERY_REQUIRED"], counts["RELEVANT_BUT_OPTIONAL"], counts["AMBIGUOUS"]) == (296, 35, 0)
    assert sum(item["source"] == "validation_v1_rubric" for item in items) == 239
    assert sum(item["source"] == "broad_v3_rubric" for item in items) == 92
    sentinel_rows = [item for item in items if item["case_id"] in worksheet["sentinel_queries"]]
    assert len(sentinel_rows) == 41 and all(item["route"] == "SIMPLE" for item in sentinel_rows)
    source_hashes = {f"eval/results/{name}": sha256(base / name) for name in source_names}
    document = {
        "schema_version": 1,
        "version": "frozen-human-verdicts-v1",
        "status": "frozen_human_verdicts",
        "truth_scope": "331 adjudicated aspects across Validation V1 (239) and Broad Query V3 (92)",
        "provenance": {
            "initial_reviewer_type": "two independent Work model agents; final disagreement labels explicitly confirmed by user",
            "sources_sha256": {**source_hashes, "eval/human_truth_contract_v1.md": hash_audit["hashes"]["eval/human_truth_contract_v1.md"]},
            "final_adjudication_source": "explicit user-provided 17-item final verdict map in this task; omission-test reasons recorded per disputed item",
            "final_adjudication_map": {key: value[0] for key, value in RESOLUTIONS.items()},
            "stage0_frozen_hashes_verified": hash_audit["checked"],
            "sentinel_queries": worksheet["sentinel_queries"],
            "sentinel_integrity": {"case_count": 8, "aspect_count": len(sentinel_rows), "all_simple": True},
        },
        "counts": {"total": 331, "QUERY_REQUIRED": 296, "RELEVANT_BUT_OPTIONAL": 35,
                   "AMBIGUOUS": 0, "initial_agreement": 314,
                   "initial_agreement_rate": 314 / 331, "disagreements": 17,
                   "disagreements_resolved": 17},
        "shrinkage_rule": worksheet["shrinkage_rule"],
        "items": items,
    }
    truth_path = out / "frozen_human_verdicts_v1.json"
    write_once(truth_path, json_text(document))
    digest = sha256(truth_path)
    write_once(out / "frozen_human_verdicts_v1.sha256", f"{digest}  frozen_human_verdicts_v1.json\n")
    return document, digest


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def direct_support_map(rubric: dict, chunks: list[dict]) -> dict[str, list[str]]:
    """Same frozen verbatim-span rule as eval.run_validation.direct_support_map."""
    by_path = defaultdict(list)
    for chunk in chunks:
        by_path[chunk["source_path"].removeprefix("Policies/")].append(chunk)
    mapping = {}
    for case in rubric["cases"]:
        for fact in case["facts"]:
            matches = set()
            for support in fact["support"]:
                excerpt = normalized(support["source_excerpt"])
                context = normalized(support.get("context_excerpt", ""))
                matches.update(chunk["chunk_id"] for chunk in by_path[support["document"]]
                               if excerpt in normalized(chunk["text"]) and
                               (not context or context in normalized(chunk["text"])))
            if not matches:
                raise ValueError(f"No indexed direct support for {fact['fact_id']}")
            mapping[fact["fact_id"]] = sorted(matches)
    return mapping


def rescore_context(root: Path, truth: dict, truth_hash: str, hash_audit: dict) -> tuple[dict, str]:
    replay = load(root / "eval/results/stage0_replay_results.json")
    arms = load(root / "eval/query_aware_arms_v1.json")
    orders = load(root / "eval/results/a0_bge_rerank_orders.json")["cases"]
    rubric = load(root / "eval/validation/broad_atomic_facts_validation_v1.json")
    index = load(root / "cache/policy_index.json")
    assert tuple(arm["policy_id"] for arm in arms["arms"]) == POLICIES
    assert tuple(replay["policy_per_case"]) == tuple(replay["policy_context_table"]) == POLICIES
    assert replay["gates"]["artifact_hashes_verified"] and replay["gates"]["frozen_artifacts_replayable"]
    support = direct_support_map(rubric, index["chunks"])
    case_ids = [case["case_id"] for case in rubric["cases"]]
    assert len(case_ids) == 50 and set(case_ids) == set(orders)
    assert all(set(replay["policy_per_case"][policy]) == set(case_ids) for policy in POLICIES)
    truth_v1 = [item for item in truth["items"] if item["source"] == "validation_v1_rubric"]
    required = defaultdict(list)
    for item in truth_v1:
        if item["final"] == "QUERY_REQUIRED":
            required[item["case_id"]].append(item["aspect_id"])
    rubric_ids = {fact["fact_id"] for case in rubric["cases"] for fact in case["facts"]}
    assert {item["aspect_id"] for item in truth_v1} == rubric_ids == set(support)
    assert all(required[case_id] for case_id in case_ids), "FULL requires a nonempty per-case truth denominator"

    per_case = {}
    policy_totals = {}
    for policy in POLICIES:
        policy_cases = {}
        covered_total = required_total = full_total = token_total = chunk_total = 0
        old_covered_total = old_required_total = old_full_total = 0
        for case_id in case_ids:
            frozen = replay["policy_per_case"][policy][case_id]
            selected = frozen["selected_chunk_ids"]
            candidate = orders[case_id]
            assert len(selected) == len(set(selected)) == frozen["chunks"]
            assert set(selected) <= {row["chunk_id"] for row in candidate}
            token_by_id = {row["chunk_id"]: row["tokens"] for row in candidate}
            assert sum(token_by_id[cid] for cid in selected) == frozen["evidence_tokens"]
            if policy == "fixed_top5":
                assert selected == [row["chunk_id"] for row in candidate[:5]]
            selected_set = set(selected)
            covered = [fact_id for fact_id in required[case_id]
                       if selected_set.intersection(support[fact_id])]
            all_fact_ids = [fact["fact_id"] for fact in next(c for c in rubric["cases"] if c["case_id"] == case_id)["facts"]]
            old_covered = sum(bool(selected_set.intersection(support[fact_id])) for fact_id in all_fact_ids)
            assert abs(old_covered / len(all_fact_ids) - frozen["coverage"]) < 1e-12
            assert (old_covered == len(all_fact_ids)) == frozen["full"]
            old_covered_total += old_covered
            old_required_total += len(all_fact_ids)
            old_full_total += int(frozen["full"])
            full = len(covered) == len(required[case_id])
            policy_cases[case_id] = {
                "query_required_covered_ids": covered,
                "query_required_missing_ids": [fid for fid in required[case_id] if fid not in covered],
                "query_required_covered": len(covered),
                "query_required_total": len(required[case_id]),
                "QueryRequiredCoverage": len(covered) / len(required[case_id]),
                "QueryRequiredFULL": full,
                "evidence_tokens": frozen["evidence_tokens"],
                "selected_chunk_ids": selected,
                "route": frozen["route"],
            }
            covered_total += len(covered)
            required_total += len(required[case_id])
            full_total += int(full)
            token_total += frozen["evidence_tokens"]
            chunk_total += len(selected)
        stored = replay["policy_context_table"][policy]
        assert old_required_total == 239 and abs(old_covered_total / 239 - stored["mean_coverage"]) < 1e-12
        assert old_full_total == stored["full_cases"]
        assert token_total == stored["total_evidence_tokens"]
        assert chunk_total / 50 == stored["mean_chunks"]
        policy_totals[policy] = {
            "cases": 50,
            "query_required_aspects": required_total,
            "query_required_covered": covered_total,
            "QueryRequiredCoverage": covered_total / required_total,
            "mean_case_QueryRequiredCoverage": sum(x["QueryRequiredCoverage"] for x in policy_cases.values()) / 50,
            "QueryRequiredFULL": full_total,
            "full_denominator_cases": 50,
            "evidence_tokens": token_total,
            "mean_evidence_tokens": token_total / 50,
            "mean_chunks": chunk_total / 50,
        }
        per_case[policy] = policy_cases

    pairs = {}
    for left, right in combinations(POLICIES, 2):
        gained_by_case, lost_by_case = {}, {}
        full_gained, full_lost = [], []
        for case_id in case_ids:
            a, b = per_case[left][case_id], per_case[right][case_id]
            gain = sorted(set(b["query_required_covered_ids"]) - set(a["query_required_covered_ids"]))
            loss = sorted(set(a["query_required_covered_ids"]) - set(b["query_required_covered_ids"]))
            if gain:
                gained_by_case[case_id] = gain
            if loss:
                lost_by_case[case_id] = loss
            if b["QueryRequiredFULL"] and not a["QueryRequiredFULL"]:
                full_gained.append(case_id)
            if a["QueryRequiredFULL"] and not b["QueryRequiredFULL"]:
                full_lost.append(case_id)
        a, b = policy_totals[left], policy_totals[right]
        gained = sum(map(len, gained_by_case.values()))
        lost = sum(map(len, lost_by_case.values()))
        assert gained - lost == b["query_required_covered"] - a["query_required_covered"]
        pairs[f"{right}_vs_{left}"] = {
            "from": left, "to": right,
            "required_aspects_gained": gained,
            "required_aspects_lost": lost,
            "net_required_aspects": gained - lost,
            "gained_by_case": gained_by_case,
            "lost_by_case": lost_by_case,
            "paired_full_gained_cases": full_gained,
            "paired_full_lost_cases": full_lost,
            "net_FULL_cases": len(full_gained) - len(full_lost),
            "QueryRequiredCoverage_delta_percentage_points": 100 * (b["QueryRequiredCoverage"] - a["QueryRequiredCoverage"]),
            "evidence_tokens_delta": b["evidence_tokens"] - a["evidence_tokens"],
        }
    dominance = []
    for better in POLICIES:
        for worse in POLICIES:
            if better == worse:
                continue
            a, b = policy_totals[better], policy_totals[worse]
            no_worse = (a["QueryRequiredCoverage"] >= b["QueryRequiredCoverage"] and
                        a["QueryRequiredFULL"] >= b["QueryRequiredFULL"] and
                        a["evidence_tokens"] <= b["evidence_tokens"])
            strict = (a["QueryRequiredCoverage"] > b["QueryRequiredCoverage"] or
                      a["QueryRequiredFULL"] > b["QueryRequiredFULL"] or
                      a["evidence_tokens"] < b["evidence_tokens"])
            if no_worse and strict:
                dominance.append({"dominant_arm": better, "dominated_arm": worse})
    result = {
        "schema_version": 1,
        "version": "human-aware-context-v1",
        "status": "offline_pre_A1_generation",
        "scope": "Validation V1 50 frozen replay cases only; 16 Broad Query V3 cases have truth labels but no five-arm Stage 0 selected-context replay",
        "truth_artifact": "eval/results/frozen_human_verdicts_v1.json",
        "truth_sha256": truth_hash,
        "frozen_inputs_sha256": hash_audit["hashes"],
        "method": {
            "selection": "Reuse each policy's selected_chunk_ids from frozen stage0_replay_results.json; no policy rerun or tuning",
            "support": "Frozen Validation V1 verbatim direct-support spans mapped to indexed chunks using the Stage 0 rule",
            "QueryRequiredCoverage": "Micro coverage: covered query-required aspect IDs / all query-required aspect IDs over 50 cases",
            "QueryRequiredFULL": "Cases in which every query-required aspect has direct support in the selected context",
            "paired_deltas": "Right policy minus left policy on the same 50 cases and same required aspect IDs",
            "dominance": "Aggregate quality-cost Pareto: at least as high coverage and FULL, at most as many evidence tokens, with at least one strict improvement; context only, not architecture adoption",
        },
        "policy_order": list(POLICIES),
        "policy_metrics": policy_totals,
        "policy_per_case": per_case,
        "paired_comparisons": pairs,
        "strictly_dominated_aggregate_arms": dominance,
        "validation": {"frozen_stage0_hashes_checked": hash_audit["checked"],
                       "legacy_context_metrics_reproduced_for_all_five_arms": True,
                       "policy_ids_match_frozen_arms": True},
    }
    return result, summary_text(result, truth)


def summary_text(result: dict, truth: dict) -> str:
    metrics = result["policy_metrics"]
    pairs = result["paired_comparisons"]
    lines = [
        "# Human truth freeze and pre-A1 context rescore",
        "",
        "## Frozen truth",
        "",
        f"- Final artifact SHA-256: `{result['truth_sha256']}`.",
        "- 331 aspects: 296 QUERY_REQUIRED, 35 RELEVANT_BUT_OPTIONAL, 0 AMBIGUOUS. Initial reviewer agreement: 314/331 (94.864%); all 17 disagreements resolved by the user-confirmed labels with omission-test reasons.",
        "- Eight frozen SIMPLE sentinel cases and their 41 aspect rows are intact. The source worksheet and all frozen Stage 0 artifacts are unchanged; frozen hashes verified.",
        "",
        "## Human-aware context metrics (Validation V1, 50 paired cases)",
        "",
        "Coverage is micro coverage over query-required aspects. FULL counts cases with all query-required aspects supported by selected context. Evidence tokens are the frozen Stage 0 diagnostic costs, not live generation tokens.",
        "",
        "| Frozen arm | QueryRequiredCoverage | QueryRequiredFULL | Required aspects covered | Evidence tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for policy in POLICIES:
        x = metrics[policy]
        lines.append(f"| `{policy}` | {x['QueryRequiredCoverage']:.2%} | {x['QueryRequiredFULL']}/50 | {x['query_required_covered']}/{x['query_required_aspects']} | {x['evidence_tokens']:,} |")
    lines += ["", "## Paired deltas vs fixed_top5", "",
              "Gained and lost count required aspect IDs whose direct support enters or leaves the selected context on the same query.", "",
              "| Arm | Gained | Lost | Net | FULL gained/lost | Coverage Δ (pp) | Evidence-token Δ |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES[1:]:
        x = pairs[f"{policy}_vs_fixed_top5"]
        lines.append(f"| `{policy}` | {x['required_aspects_gained']} | {x['required_aspects_lost']} | {x['net_required_aspects']:+} | {len(x['paired_full_gained_cases'])}/{len(x['paired_full_lost_cases'])} | {x['QueryRequiredCoverage_delta_percentage_points']:+.2f} | {x['evidence_tokens_delta']:+,} |")
    lines += ["", "## All-arm paired comparisons", "",
              "The JSON result records gained/lost aspect IDs, case IDs, FULL transitions, coverage deltas, and token deltas for all 10 pairs. Key comparisons:", ""]
    for key in ("coverage_selector_v2_vs_adaptive_prefix_v1", "no_router_adaptive_v1_vs_adaptive_prefix_v1", "query_router_v1_vs_coverage_selector_v2", "query_router_v1_vs_no_router_adaptive_v1"):
        x = pairs[key]
        lines.append(f"- `{x['to']}` vs `{x['from']}`: {x['required_aspects_gained']} gained, {x['required_aspects_lost']} lost; FULL +{len(x['paired_full_gained_cases'])}/-{len(x['paired_full_lost_cases'])}; tokens {x['evidence_tokens_delta']:+,}.")
    dominance = result["strictly_dominated_aggregate_arms"]
    lines += ["", "## Context-level dominance", ""]
    if dominance:
        for x in dominance:
            lines.append(f"- `{x['dominated_arm']}` is strictly dominated in aggregate by `{x['dominant_arm']}` under the stated coverage/FULL/evidence-token rule.")
    else:
        lines.append("- No frozen arm is strictly dominated in aggregate under the stated coverage/FULL/evidence-token rule.")
    lines += ["", "This is a pre-generation context diagnostic. It does not make an architecture kill/adoption decision or evaluate answer quality, provider tokens, or latency. The 16 V3 cases are excluded from the five-arm rescore because the frozen replay has no selected contexts for them.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.output_dir or root / "eval/results").resolve()
    out.mkdir(parents=True, exist_ok=True)
    audit = verify_stage0(root)
    truth, truth_hash = freeze_truth(root, out, audit)
    result, summary = rescore_context(root, truth, truth_hash, audit)
    write_once(out / "human_aware_context_v1.json", json_text(result))
    write_once(out / "human_aware_context_v1_summary.md", summary)
    print(json.dumps({"truth_sha256": truth_hash, "truth_counts": truth["counts"],
                      "stage0_hashes_checked": audit["checked"],
                      "policy_metrics": result["policy_metrics"],
                      "dominance": result["strictly_dominated_aggregate_arms"]}, indent=2))


if __name__ == "__main__":
    main()
