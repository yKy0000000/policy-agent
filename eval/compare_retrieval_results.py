"""Create a reproducible lexical-versus-semantic retrieval comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .run_retrieval_eval import SUPPORTED_CATEGORIES, _write_text_atomic


TRACKED_FAILURE_IDS = (
    "ret_001",
    "ret_003",
    "ret_007",
    "ret_009",
    "ret_012",
    "ret_015",
    "ret_016",
    "multi_001",
)
METRIC_NAMES = ("hit_at_1", "hit_at_3", "hit_at_5", "mrr")


def compare_reports(
    lexical: Mapping[str, Any],
    semantic: Mapping[str, Any],
) -> dict[str, Any]:
    lexical_config = lexical["configuration"]
    semantic_config = semantic["configuration"]
    if lexical_config["candidates_sha256"] != semantic_config["candidates_sha256"]:
        raise ValueError("lexical and semantic reports used different candidate datasets")
    if lexical_config["index_chunk_count"] != semantic_config["index_chunk_count"]:
        raise ValueError("lexical and semantic reports used different chunk counts")

    lexical_cases = {row["id"]: row for row in lexical["cases"]}
    semantic_cases = {row["id"]: row for row in semantic["cases"]}
    if lexical_cases.keys() != semantic_cases.keys():
        raise ValueError("lexical and semantic reports contain different case IDs")

    overall = _compare_metrics(
        lexical["summary"]["overall_supported"],
        semantic["summary"]["overall_supported"],
    )
    by_category = {
        category: _compare_metrics(
            lexical["summary"]["by_category"][category],
            semantic["summary"]["by_category"][category],
        )
        for category in SUPPORTED_CATEGORIES
    }
    coverage = {
        "lexical_mean_coverage_at_3": lexical["summary"]["multi_source_coverage"]["mean_coverage_at_3"],
        "semantic_mean_coverage_at_3": semantic["summary"]["multi_source_coverage"]["mean_coverage_at_3"],
        "delta_coverage_at_3": (
            semantic["summary"]["multi_source_coverage"]["mean_coverage_at_3"]
            - lexical["summary"]["multi_source_coverage"]["mean_coverage_at_3"]
        ),
        "lexical_mean_coverage_at_5": lexical["summary"]["multi_source_coverage"]["mean_coverage_at_5"],
        "semantic_mean_coverage_at_5": semantic["summary"]["multi_source_coverage"]["mean_coverage_at_5"],
        "delta_coverage_at_5": (
            semantic["summary"]["multi_source_coverage"]["mean_coverage_at_5"]
            - lexical["summary"]["multi_source_coverage"]["mean_coverage_at_5"]
        ),
        "cases": _compare_coverage_cases(lexical, semantic),
    }
    movements = [
        {
            "id": case_id,
            "lexical_rank": lexical_cases[case_id]["first_relevant_rank"],
            "semantic_rank": semantic_cases[case_id]["first_relevant_rank"],
        }
        for case_id in TRACKED_FAILURE_IDS
    ]
    unsupported = [
        {
            "id": row["id"],
            "query_used": row["query_used"],
            "semantic_top_5": row["top_5"],
        }
        for row in semantic["cases"]
        if not row["supported"]
    ]
    return {
        "configuration": {
            "candidates_sha256": lexical_config["candidates_sha256"],
            "chunk_count": lexical_config["index_chunk_count"],
            "lexical_model": lexical_config["embedding_model"],
            "semantic_model": semantic_config["embedding_model"],
            "multi_turn_query_mode": semantic_config["multi_turn_query_mode"],
        },
        "overall": overall,
        "by_category": by_category,
        "multi_source_coverage": coverage,
        "tracked_failure_rank_movements": movements,
        "semantic_hit_at_5_failures": semantic["summary"]["review_priority"]["hit_at_5_zero"],
        "unsupported_semantic_top_5": unsupported,
    }


def render_comparison_markdown(comparison: Mapping[str, Any]) -> str:
    config = comparison["configuration"]
    lines = [
        "# Lexical vs semantic retrieval",
        "",
        f"- Chunks: {config['chunk_count']}",
        f"- Lexical: `{config['lexical_model']}`",
        f"- Semantic: `{config['semantic_model']}`",
        f"- Candidate SHA-256: `{config['candidates_sha256']}`",
        f"- Multi-turn mode: `{config['multi_turn_query_mode']}`",
        "",
        "## Overall",
        "",
    ]
    lines.extend(_comparison_metric_lines(comparison["overall"]))
    lines.extend(["", "## By category", ""])
    for category in SUPPORTED_CATEGORIES:
        lines.extend([f"### {category}", ""])
        lines.extend(_comparison_metric_lines(comparison["by_category"][category]))
        lines.append("")

    coverage = comparison["multi_source_coverage"]
    lines.extend(
        [
            "## Multi-source coverage",
            "",
            f"- coverage@3: lexical={coverage['lexical_mean_coverage_at_3']:.4f}, semantic={coverage['semantic_mean_coverage_at_3']:.4f}, delta={coverage['delta_coverage_at_3']:+.4f}",
            f"- coverage@5: lexical={coverage['lexical_mean_coverage_at_5']:.4f}, semantic={coverage['semantic_mean_coverage_at_5']:.4f}, delta={coverage['delta_coverage_at_5']:+.4f}",
            "",
        ]
    )
    for row in coverage["cases"]:
        lines.append(
            f"- `{row['id']}`: @3 {row['lexical_coverage_at_3']:.4f} -> {row['semantic_coverage_at_3']:.4f}; "
            f"@5 {row['lexical_coverage_at_5']:.4f} -> {row['semantic_coverage_at_5']:.4f}"
        )

    lines.extend(["", "## Tracked failure rank movement", ""])
    for row in comparison["tracked_failure_rank_movements"]:
        lines.append(f"- `{row['id']}`: {row['lexical_rank']} -> {row['semantic_rank']}")

    failures = comparison["semantic_hit_at_5_failures"]
    lines.extend(
        [
            "",
            "## Semantic Hit@5 failures",
            "",
            ", ".join(f"`{case_id}`" for case_id in failures) if failures else "None.",
            "",
            "## Unsupported semantic top-5",
            "",
        ]
    )
    for row in comparison["unsupported_semantic_top_5"]:
        lines.extend([f"### {row['id']}", "", f"- Query: {row['query_used']}"])
        for item in row["semantic_top_5"]:
            heading = " > ".join(item["heading_path"]) or "(document introduction)"
            lines.append(
                f"- {item['rank']}. {item['score']:.4f} | `{item['title']}` | `{heading}` | `{item['source_path']}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _compare_metrics(lexical: Mapping[str, Any], semantic: Mapping[str, Any]) -> dict[str, Any]:
    compared: dict[str, Any] = {"case_count": lexical["case_count"]}
    if lexical["case_count"] != semantic["case_count"]:
        raise ValueError("metric groups contain different case counts")
    for metric in METRIC_NAMES:
        compared[metric] = {
            "lexical": lexical[metric],
            "semantic": semantic[metric],
            "delta": semantic[metric] - lexical[metric],
        }
    return compared


def _compare_coverage_cases(
    lexical: Mapping[str, Any],
    semantic: Mapping[str, Any],
) -> list[dict[str, Any]]:
    lexical_rows = {
        row["id"]: row for row in lexical["summary"]["multi_source_coverage"]["cases"]
    }
    semantic_rows = {
        row["id"]: row for row in semantic["summary"]["multi_source_coverage"]["cases"]
    }
    if lexical_rows.keys() != semantic_rows.keys():
        raise ValueError("multi-source case sets differ between reports")
    return [
        {
            "id": case_id,
            "lexical_coverage_at_3": lexical_rows[case_id]["coverage_at_3"],
            "semantic_coverage_at_3": semantic_rows[case_id]["coverage_at_3"],
            "lexical_coverage_at_5": lexical_rows[case_id]["coverage_at_5"],
            "semantic_coverage_at_5": semantic_rows[case_id]["coverage_at_5"],
        }
        for case_id in lexical_rows
    ]


def _comparison_metric_lines(metrics: Mapping[str, Any]) -> list[str]:
    return [
        f"- Cases: {metrics['case_count']}",
        *[
            f"- {metric}: lexical={metrics[metric]['lexical']:.4f}, semantic={metrics[metric]['semantic']:.4f}, delta={metrics[metric]['delta']:+.4f}"
            for metric in METRIC_NAMES
        ],
    ]


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
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_ab_comparison.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "retrieval_ab_comparison.md",
    )
    args = parser.parse_args(argv)

    lexical = json.loads(args.lexical.read_text(encoding="utf-8"))
    semantic = json.loads(args.semantic.read_text(encoding="utf-8"))
    comparison = compare_reports(lexical, semantic)
    _write_text_atomic(
        args.json_output,
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(args.markdown_output, render_comparison_markdown(comparison))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Markdown: {args.markdown_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

