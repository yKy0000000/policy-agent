"""Compare lexical, semantic, and hybrid retrieval on the shared eval set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .run_retrieval_eval import SUPPORTED_CATEGORIES, _write_text_atomic


TRACKED_CASE_IDS = (
    "ret_001",
    "ret_003",
    "ret_004",
    "ret_007",
    "ret_008",
    "ret_009",
    "ret_011",
    "ret_012",
    "ret_015",
    "ret_016",
    "multi_001",
    "multi_003",
)
BACKENDS = ("lexical", "semantic", "hybrid")
METRICS = ("hit_at_1", "hit_at_3", "hit_at_5", "mrr")


def compare_three_way(
    lexical: Mapping[str, Any],
    semantic: Mapping[str, Any],
    hybrid: Mapping[str, Any],
) -> dict[str, Any]:
    reports = {"lexical": lexical, "semantic": semantic, "hybrid": hybrid}
    candidate_hashes = {
        report["configuration"]["candidates_sha256"] for report in reports.values()
    }
    chunk_counts = {
        report["configuration"]["index_chunk_count"] for report in reports.values()
    }
    if len(candidate_hashes) != 1 or len(chunk_counts) != 1:
        raise ValueError("three-way reports must use the same candidates and chunks")

    cases = {
        backend: {row["id"]: row for row in report["cases"]}
        for backend, report in reports.items()
    }
    if not (cases["lexical"].keys() == cases["semantic"].keys() == cases["hybrid"].keys()):
        raise ValueError("three-way reports contain different case IDs")

    overall = _metric_group(
        {backend: report["summary"]["overall_supported"] for backend, report in reports.items()}
    )
    by_category = {
        category: _metric_group(
            {
                backend: report["summary"]["by_category"][category]
                for backend, report in reports.items()
            }
        )
        for category in SUPPORTED_CATEGORIES
    }
    coverage = {
        backend: {
            "mean_coverage_at_3": report["summary"]["multi_source_coverage"]["mean_coverage_at_3"],
            "mean_coverage_at_5": report["summary"]["multi_source_coverage"]["mean_coverage_at_5"],
        }
        for backend, report in reports.items()
    }
    coverage["cases"] = _coverage_cases(reports)
    supported_ids = [
        case_id for case_id, row in cases["lexical"].items() if row["supported"]
    ]
    oracle_union = {
        f"hit_at_{k}": sum(
            bool(cases["lexical"][case_id][f"hit_at_{k}"])
            or bool(cases["semantic"][case_id][f"hit_at_{k}"])
            for case_id in supported_ids
        )
        / len(supported_ids)
        for k in (1, 3, 5)
    }
    movements = [
        {
            "id": case_id,
            "lexical_rank": cases["lexical"][case_id]["first_relevant_rank"],
            "semantic_rank": cases["semantic"][case_id]["first_relevant_rank"],
            "hybrid_rank": cases["hybrid"][case_id]["first_relevant_rank"],
        }
        for case_id in TRACKED_CASE_IDS
    ]
    unsupported = [
        {
            "id": row["id"],
            "query_used": row["query_used"],
            "hybrid_top_5": row["top_5"],
        }
        for row in hybrid["cases"]
        if not row["supported"]
    ]
    return {
        "configuration": {
            "candidates_sha256": next(iter(candidate_hashes)),
            "chunk_count": next(iter(chunk_counts)),
            "lexical_model": lexical["configuration"]["embedding_model"],
            "semantic_model": semantic["configuration"]["embedding_model"],
            "hybrid_model": hybrid["configuration"]["embedding_model"],
            "rrf_k": hybrid["configuration"]["rrf_k"],
            "hybrid_candidate_depth": hybrid["configuration"]["hybrid_candidate_depth"],
            "multi_turn_query_mode": hybrid["configuration"]["multi_turn_query_mode"],
        },
        "overall": overall,
        "by_category": by_category,
        "multi_source_coverage": coverage,
        "oracle_union": oracle_union,
        "tracked_rank_movements": movements,
        "hybrid_hit_at_5_failures": hybrid["summary"]["review_priority"]["hit_at_5_zero"],
        "unsupported_hybrid_top_5": unsupported,
    }


def render_markdown(comparison: Mapping[str, Any]) -> str:
    config = comparison["configuration"]
    lines = [
        "# Lexical vs semantic vs hybrid retrieval",
        "",
        f"- Chunks: {config['chunk_count']}",
        f"- Lexical: `{config['lexical_model']}`",
        f"- Semantic: `{config['semantic_model']}`",
        f"- Hybrid: unweighted RRF, k={config['rrf_k']}, candidate depth={config['hybrid_candidate_depth']}",
        f"- Candidate SHA-256: `{config['candidates_sha256']}`",
        f"- Multi-turn mode: `{config['multi_turn_query_mode']}`",
        "",
        "## Overall",
        "",
    ]
    lines.extend(_metric_lines(comparison["overall"]))
    lines.extend(["", "## By category", ""])
    for category in SUPPORTED_CATEGORIES:
        lines.extend([f"### {category}", ""])
        lines.extend(_metric_lines(comparison["by_category"][category]))
        lines.append("")

    coverage = comparison["multi_source_coverage"]
    lines.extend(["## Multi-source coverage", ""])
    for backend in BACKENDS:
        lines.append(
            f"- {backend}: coverage@3={coverage[backend]['mean_coverage_at_3']:.4f}, "
            f"coverage@5={coverage[backend]['mean_coverage_at_5']:.4f}"
        )
    lines.append("")
    for row in coverage["cases"]:
        lines.append(
            f"- `{row['id']}`: lexical={row['lexical_coverage_at_3']:.4f}/{row['lexical_coverage_at_5']:.4f}, "
            f"semantic={row['semantic_coverage_at_3']:.4f}/{row['semantic_coverage_at_5']:.4f}, "
            f"hybrid={row['hybrid_coverage_at_3']:.4f}/{row['hybrid_coverage_at_5']:.4f} (@3/@5)"
        )

    oracle = comparison["oracle_union"]
    lines.extend(
        [
            "",
            "## Oracle union upper bound",
            "",
            f"- Hit@1: {oracle['hit_at_1']:.4f}",
            f"- Hit@3: {oracle['hit_at_3']:.4f}",
            f"- Hit@5: {oracle['hit_at_5']:.4f}",
            "",
            "## Tracked rank movement",
            "",
        ]
    )
    for row in comparison["tracked_rank_movements"]:
        lines.append(
            f"- `{row['id']}`: {row['lexical_rank']} -> {row['semantic_rank']} -> {row['hybrid_rank']}"
        )

    failures = comparison["hybrid_hit_at_5_failures"]
    lines.extend(
        [
            "",
            "## Hybrid Hit@5 failures",
            "",
            ", ".join(f"`{case_id}`" for case_id in failures) if failures else "None.",
            "",
            "## Unsupported hybrid top-5",
            "",
        ]
    )
    for row in comparison["unsupported_hybrid_top_5"]:
        lines.extend([f"### {row['id']}", "", f"- Query: {row['query_used']}"])
        for item in row["hybrid_top_5"]:
            heading = " > ".join(item["heading_path"]) or "(document introduction)"
            lines.append(
                f"- {item['rank']}. RRF={item['score']:.6f} | `{item['title']}` | `{heading}` | "
                f"lexical_rank={item.get('lexical_rank')} | semantic_rank={item.get('semantic_rank')}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _metric_group(groups: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    counts = {group["case_count"] for group in groups.values()}
    if len(counts) != 1:
        raise ValueError("metric groups contain different case counts")
    return {
        "case_count": next(iter(counts)),
        **{
            metric: {backend: groups[backend][metric] for backend in BACKENDS}
            for metric in METRICS
        },
    }


def _coverage_cases(reports: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = {
        backend: {
            row["id"]: row
            for row in report["summary"]["multi_source_coverage"]["cases"]
        }
        for backend, report in reports.items()
    }
    if not (rows["lexical"].keys() == rows["semantic"].keys() == rows["hybrid"].keys()):
        raise ValueError("multi-source case sets differ between reports")
    return [
        {
            "id": case_id,
            **{
                f"{backend}_coverage_at_{k}": rows[backend][case_id][f"coverage_at_{k}"]
                for backend in BACKENDS
                for k in (3, 5)
            },
        }
        for case_id in rows["lexical"]
    ]


def _metric_lines(metrics: Mapping[str, Any]) -> list[str]:
    lines = [f"- Cases: {metrics['case_count']}"]
    for metric in METRICS:
        values = metrics[metric]
        lines.append(
            f"- {metric}: lexical={values['lexical']:.4f}, "
            f"semantic={values['semantic']:.4f}, hybrid={values['hybrid']:.4f}"
        )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lexical",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_baseline.json",
    )
    parser.add_argument(
        "--semantic",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_semantic.json",
    )
    parser.add_argument(
        "--hybrid",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_hybrid.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_three_way_comparison.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_three_way_comparison.md",
    )
    args = parser.parse_args(argv)

    lexical = json.loads(args.lexical.read_text(encoding="utf-8"))
    semantic = json.loads(args.semantic.read_text(encoding="utf-8"))
    hybrid = json.loads(args.hybrid.read_text(encoding="utf-8"))
    comparison = compare_three_way(lexical, semantic, hybrid)
    _write_text_atomic(
        args.json_output,
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(args.markdown_output, render_markdown(comparison))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Markdown: {args.markdown_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

