"""Compare lexical, semantic, RRF hybrid, and Cross-Encoder reranked retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .run_retrieval_eval import SUPPORTED_CATEGORIES, _write_text_atomic


BACKENDS = ("lexical", "semantic", "hybrid", "reranked")
METRICS = ("hit_at_1", "hit_at_3", "hit_at_5", "mrr")
TRACKED_CASE_IDS = (
    "ret_001",
    "ret_003",
    "ret_004",
    "ret_007",
    "ret_008",
    "ret_009",
    "ret_011",
    "ret_012",
    "ret_013",
    "ret_015",
    "ret_016",
    "multi_001",
    "multi_003",
)


def compare_four_way(reports: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    if tuple(reports) != BACKENDS:
        raise ValueError(f"reports must be ordered as {BACKENDS}")
    candidate_hashes = {
        report["configuration"]["candidates_sha256"] for report in reports.values()
    }
    chunk_counts = {
        report["configuration"]["index_chunk_count"] for report in reports.values()
    }
    if len(candidate_hashes) != 1 or len(chunk_counts) != 1:
        raise ValueError("four-way reports must use the same candidates and chunks")

    cases = {
        backend: {row["id"]: row for row in report["cases"]}
        for backend, report in reports.items()
    }
    case_sets = [set(rows) for rows in cases.values()]
    if any(case_set != case_sets[0] for case_set in case_sets[1:]):
        raise ValueError("four-way reports contain different case IDs")

    return {
        "configuration": {
            "candidates_sha256": next(iter(candidate_hashes)),
            "chunk_count": next(iter(chunk_counts)),
            "models": {
                backend: report["configuration"]["embedding_model"]
                for backend, report in reports.items()
            },
            "lexical_candidate_k": reports["reranked"]["configuration"]["lexical_candidate_k"],
            "semantic_candidate_k": reports["reranked"]["configuration"]["semantic_candidate_k"],
            "multi_turn_query_mode": reports["reranked"]["configuration"]["multi_turn_query_mode"],
            "candidate_recall_before_reranking": reports["reranked"]["summary"][
                "candidate_recall_before_reranking"
            ],
            "reranking_performance": reports["reranked"]["summary"]["performance"],
        },
        "overall": _metric_group(
            {
                backend: report["summary"]["overall_supported"]
                for backend, report in reports.items()
            }
        ),
        "by_category": {
            category: _metric_group(
                {
                    backend: report["summary"]["by_category"][category]
                    for backend, report in reports.items()
                }
            )
            for category in SUPPORTED_CATEGORIES
        },
        "multi_source_coverage": {
            **{
                backend: {
                    "mean_coverage_at_3": report["summary"]["multi_source_coverage"][
                        "mean_coverage_at_3"
                    ],
                    "mean_coverage_at_5": report["summary"]["multi_source_coverage"][
                        "mean_coverage_at_5"
                    ],
                }
                for backend, report in reports.items()
            },
            "cases": _coverage_cases(reports),
        },
        "tracked_rank_movements": [
            {
                "id": case_id,
                **{
                    f"{backend}_rank": cases[backend][case_id]["first_relevant_rank"]
                    for backend in BACKENDS
                },
            }
            for case_id in TRACKED_CASE_IDS
        ],
        "reranked_hit_at_5_failures": reports["reranked"]["summary"]["review_priority"][
            "hit_at_5_zero"
        ],
        "unsupported_reranked_top_5": [
            {
                "id": row["id"],
                "query_used": row["query_used"],
                "top_5": row["top_5"],
            }
            for row in reports["reranked"]["cases"]
            if not row["supported"]
        ],
    }


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
    case_sets = [set(group) for group in rows.values()]
    if any(case_set != case_sets[0] for case_set in case_sets[1:]):
        raise ValueError("multi-source case sets differ between reports")
    return [
        {
            "id": case_id,
            **{
                f"{backend}_coverage_at_{cutoff}": rows[backend][case_id][
                    f"coverage_at_{cutoff}"
                ]
                for backend in BACKENDS
                for cutoff in (3, 5)
            },
        }
        for case_id in rows["lexical"]
    ]


def render_markdown(comparison: Mapping[str, Any]) -> str:
    config = comparison["configuration"]
    lines = [
        "# Four-way retrieval comparison",
        "",
        f"- Chunks: {config['chunk_count']}",
        f"- Candidate union: lexical Top-{config['lexical_candidate_k']} + semantic Top-{config['semantic_candidate_k']}",
        f"- Candidate recall before reranking: {config['candidate_recall_before_reranking']['recall']:.4f}",
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
        values = ", ".join(
            f"{backend}={row[f'{backend}_coverage_at_3']:.4f}/{row[f'{backend}_coverage_at_5']:.4f}"
            for backend in BACKENDS
        )
        lines.append(f"- `{row['id']}`: {values} (@3/@5)")

    lines.extend(["", "## Tracked rank movement", ""])
    for row in comparison["tracked_rank_movements"]:
        lines.append(
            f"- `{row['id']}`: lexical={row['lexical_rank']}, semantic={row['semantic_rank']}, "
            f"RRF={row['hybrid_rank']}, reranked={row['reranked_rank']}"
        )

    failures = comparison["reranked_hit_at_5_failures"]
    lines.extend(
        [
            "",
            "## Reranked Hit@5 failures",
            "",
            ", ".join(f"`{case_id}`" for case_id in failures) if failures else "None.",
            "",
            "## Unsupported reranked Top-5",
            "",
        ]
    )
    for row in comparison["unsupported_reranked_top_5"]:
        lines.extend([f"### {row['id']}", "", f"- Query: {row['query_used']}"])
        for item in row["top_5"]:
            heading = " > ".join(item["heading_path"]) or "(document introduction)"
            lines.append(
                f"- {item['rank']}. score={item['reranker_score']:.4f} | `{item['title']}` | "
                f"`{heading}` | `{item['source_path']}` | lexical_rank={item.get('lexical_rank')} | "
                f"semantic_rank={item.get('semantic_rank')}"
            )
        lines.append("")

    perf = config["reranking_performance"]
    lines.extend(
        [
            "## Reranking performance",
            "",
            f"- Queries: {perf['query_count']}",
            f"- Candidate count average/min/max: {perf['candidate_count_average']:.2f} / "
            f"{perf['candidate_count_minimum']} / {perf['candidate_count_maximum']}",
            f"- Cross-Encoder total/mean: {perf['reranker_total_seconds']:.4f}s / "
            f"{perf['reranker_mean_seconds_per_query']:.4f}s",
            f"- p50/p95: {perf['reranker_p50_seconds']:.4f}s / {perf['reranker_p95_seconds']:.4f}s",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _metric_lines(metrics: Mapping[str, Any]) -> list[str]:
    lines = [f"- Cases: {metrics['case_count']}"]
    for metric in METRICS:
        values = metrics[metric]
        lines.append(
            f"- {metric}: "
            + ", ".join(f"{backend}={values[backend]:.4f}" for backend in BACKENDS)
        )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    for backend, filename in (
        ("lexical", "retrieval_baseline.json"),
        ("semantic", "retrieval_semantic.json"),
        ("hybrid", "retrieval_hybrid.json"),
        ("reranked", "retrieval_reranked.json"),
    ):
        parser.add_argument(
            f"--{backend}",
            type=Path,
            default=project_root / "eval" / "results" / filename,
        )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_four_way_comparison.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_four_way_comparison.md",
    )
    args = parser.parse_args(argv)
    reports = {
        backend: json.loads(getattr(args, backend).read_text(encoding="utf-8"))
        for backend in BACKENDS
    }
    comparison = compare_four_way(reports)
    _write_text_atomic(args.json_output, json.dumps(comparison, ensure_ascii=False, indent=2) + "\n")
    _write_text_atomic(args.markdown_output, render_markdown(comparison))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Markdown: {args.markdown_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
