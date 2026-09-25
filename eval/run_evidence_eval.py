"""Reproduce the frozen Broad Query V3 evidence baseline from saved inputs.

The oracle is an offline upper bound only. It uses gold required-fact labels
unavailable at inference time and must never be used as a production router.
No retrieval, reranking, or generation runs here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from eval.metrics import POLICIES, score_facts, select_oracle, summarize_cases, winner_counts

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "eval/broad_queries_v3_adjudicated.json"
RUBRIC = ROOT / "eval/broad_query_v3_atomic_facts_frozen_candidate.json"
TOP20 = ROOT / "eval/results/broad_v3_frozen_top20.json"
STRATEGIES = ROOT / "eval/results/broad_v3_coverage_selector_eval.json"
OUTPUT = ROOT / "eval/results/evidence_eval.json"
FROZEN_SHA256 = {
    "benchmark": "9e15b40cc5068aa4fc52ce3e7a5c154c90733156f66e5c92bc688c19a6b919e4",
    "rubric": "616e0968038a26b27b7a4d8a90293b100d9a2287da0038caa9cbe3f258646534",
    "top20": "a2106ab1b2a25c0600b89ca52c281705e2612914230b83ba5b31fe807ba2441e",
    "strategies": "713d773c5e1fe9f59f0bd0e40e22fc649c945665d99a2d4a30f9d6e104f3ef4c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs() -> tuple[dict, dict, dict, dict, dict[str, list[dict]]]:
    for name, path in (("benchmark", BENCHMARK), ("rubric", RUBRIC),
                       ("top20", TOP20), ("strategies", STRATEGIES)):
        if sha256(path) != FROZEN_SHA256[name]:
            raise ValueError(f"{name} SHA differs from the frozen baseline")
    benchmark, rubric, top20, strategies = map(
        load_json, (BENCHMARK, RUBRIC, TOP20, STRATEGIES))
    if not rubric.get("ready_to_freeze") or rubric["summary"]["required_facts"] != 92:
        raise ValueError("rubric is not the 92-fact frozen candidate")
    if sha256(BENCHMARK) != top20["annotation_sha256"]:
        raise ValueError("benchmark SHA differs from frozen retrieval")
    if sha256(TOP20) != strategies["source_sha256"]["frozen"]:
        raise ValueError("strategy selections differ from frozen retrieval")
    chunks = {}
    for snapshot in top20["cases"]:
        for chunk in snapshot["candidate_pool"]:
            existing = chunks.setdefault(chunk["chunk_id"], chunk)
            if existing["source_path"] != chunk["source_path"]:
                raise ValueError(f"inconsistent frozen chunk mapping: {chunk['chunk_id']}")
    ids = [[case["case_id"] for case in source["cases"]]
           for source in (benchmark, top20, strategies)]
    if len(ids[0]) != 16 or len(set(ids[0])) != 16 or any(x != ids[0] for x in ids[1:]):
        raise ValueError("case IDs or order differ")
    if len({fact["fact_id"] for fact in rubric["facts"]}) != len(rubric["facts"]):
        raise ValueError("duplicate fact IDs")
    facts_by_case = {case_id: [] for case_id in ids[0]}
    for fact in rubric["facts"]:
        if fact["case_id"] not in facts_by_case:
            raise ValueError(f"unknown fact case: {fact['case_id']}")
        if not fact["required"]:
            continue
        direct_ids = set()
        for mapping in fact["evidence"]:
            chunk = chunks.get(mapping["chunk_id"])
            if not mapping["chunk_id"] or not mapping["doc"] or mapping["entailment"] not in (
                    "direct", "partial", "invalid"):
                raise ValueError(f"stale evidence mapping: {fact['fact_id']}")
            if chunk is not None and not chunk["source_path"].endswith(mapping["doc"]):
                raise ValueError(f"stale evidence mapping: {fact['fact_id']}")
            if mapping["entailment"] == "direct":
                direct_ids.add(mapping["chunk_id"])
        if not direct_ids:
            raise ValueError(f"required fact lacks direct support: {fact['fact_id']}")
        facts_by_case[fact["case_id"]].append({"fact_id": fact["fact_id"],
                                                "direct_chunk_ids": direct_ids})
    if sum(map(len, facts_by_case.values())) != rubric["summary"]["required_facts"]:
        raise ValueError("required fact inventory differs")
    return benchmark, rubric, top20, strategies, facts_by_case


def evaluate() -> dict:
    benchmark, rubric, frozen, strategies, facts_by_case = load_inputs()
    rows = []
    for case, snapshot, saved in zip(benchmark["cases"], frozen["cases"], strategies["cases"]):
        cid = case["case_id"]
        if not case["query"] == snapshot["query"] or snapshot["candidate_pool"][:20] != snapshot["top20"]:
            raise ValueError(f"query or frozen Top20 differs: {cid}")
        facts = facts_by_case[cid]
        pool = score_facts(facts, snapshot["candidate_pool"])
        top = score_facts(facts, snapshot["top20"])
        options = {}
        for name in POLICIES:
            selection = saved[name]
            ranks = selection["original_ranks"]
            if len(ranks) != selection["selected_k"] or len(set(ranks)) != len(ranks) or any(
                    not 1 <= rank <= len(snapshot["top20"]) for rank in ranks):
                raise ValueError(f"invalid selected ranks: {cid}/{name}")
            chunks = [snapshot["top20"][rank - 1] for rank in ranks]
            if ([chunk["chunk_id"] for chunk in chunks] != selection["selected_chunk_ids"] or
                    sum(chunk["token_count"] for chunk in chunks) != selection["evidence_tokens"]):
                raise ValueError(f"selection or tokens differ: {cid}/{name}")
            options[name] = {**score_facts(facts, chunks),
                             "selected_k": selection["selected_k"],
                             "evidence_tokens": selection["evidence_tokens"]}
        oracle = select_oracle(options)
        if not pool["fact_complete"]:
            taxonomy = "candidate_retrieval_ceiling"
        elif not top["fact_complete"]:
            taxonomy = "candidate_present_beyond_top20"
        elif top["first_complete_k"] <= 5:
            taxonomy = "top5_complete"
        elif top["first_complete_k"] <= 8:
            taxonomy = "shallow_cutoff"
        else:
            taxonomy = "deep_ranking"
        rows.append({"case_id": cid, "required_fact_count": len(facts),
                     "candidate_pool": pool, "top20": top, "policies": options,
                     "oracle": oracle, "taxonomy": taxonomy})
    total = sum(row["required_fact_count"] for row in rows)
    candidate_covered = sum(row["candidate_pool"]["covered_count"] for row in rows)
    policies = {name: summarize_cases(rows, name) for name in POLICIES}
    oracle = summarize_cases(rows, "oracle")
    unique, ties = winner_counts(rows)
    v1_tokens = policies["adaptive_prefix_v1"]["total_evidence_tokens"]
    oracle.update({"token_savings_vs_v1": v1_tokens - oracle["total_evidence_tokens"],
                   "token_savings_fraction_vs_v1": (v1_tokens - oracle["total_evidence_tokens"]) / v1_tokens,
                   "unique_winners": unique, "exact_ties": ties})
    return {"schema_version": 1, "name": "Broad Query V3 frozen atomic-fact evidence evaluation",
            "oracle_warning": "offline upper bound using evaluation labels unavailable at inference time",
            "source_sha256": {"benchmark": sha256(BENCHMARK), "frozen_rubric": sha256(RUBRIC),
                              "frozen_top20": sha256(TOP20), "strategy_outputs": sha256(STRATEGIES)},
            "case_count": len(rows), "required_fact_count": total,
            "candidate_pool": {"covered_facts": candidate_covered, "total_facts": total,
                               "micro_recall": candidate_covered / total,
                               "macro_recall": sum(row["candidate_pool"]["coverage"] for row in rows) / len(rows),
                               "fact_complete_cases": sum(row["candidate_pool"]["fact_complete"] for row in rows),
                               "ceiling_case_ids": [row["case_id"] for row in rows
                                                    if not row["candidate_pool"]["fact_complete"]]},
            "policies": policies, "oracle": oracle,
            "taxonomy_counts": dict(Counter(row["taxonomy"] for row in rows)), "cases": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved result without writing")
    args = parser.parse_args()
    result = evaluate()
    if args.check:
        if result != load_json(OUTPUT):
            raise SystemExit("saved evidence evaluation differs from frozen inputs")
        print("Frozen evidence evaluation matches saved result.")
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
