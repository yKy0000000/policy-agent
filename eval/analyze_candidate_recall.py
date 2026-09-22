"""Measure lexical+semantic candidate-union recall without reranking."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

from eval.run_retrieval_eval import (
    SUPPORTED_CATEGORIES,
    first_relevant_rank,
    source_matches,
)
from src.indexing import load_index
from src.retriever import PolicyRetriever, RetrievalResult


DEFAULT_DEPTHS = (1, 3, 5, 10, 20, 40)


def candidate_union(
    lexical_results: Sequence[RetrievalResult],
    semantic_results: Sequence[RetrievalResult],
    depth: int,
) -> list[RetrievalResult]:
    """Return a deterministic chunk-ID union of each retriever's top-N."""

    if depth <= 0:
        raise ValueError("candidate depth must be positive")
    union: list[RetrievalResult] = []
    seen: set[str] = set()
    for result in (*lexical_results[:depth], *semantic_results[:depth]):
        if result.chunk_id not in seen:
            seen.add(result.chunk_id)
            union.append(result)
    return union


def candidate_hit(
    candidates: Sequence[RetrievalResult],
    expected_sources: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether any candidate matches any acceptable expected source."""

    return any(
        source_matches(result, expected)
        for result in candidates
        for expected in expected_sources
    )


def candidate_source_coverage(
    candidates: Sequence[RetrievalResult],
    expected_sources: Sequence[Mapping[str, Any]],
) -> float:
    """Return the fraction of expected source rules present in the union."""

    if not expected_sources:
        raise ValueError("source coverage requires at least one expected source")
    covered = sum(
        any(source_matches(result, expected) for result in candidates)
        for expected in expected_sources
    )
    return covered / len(expected_sources)


def first_candidate_depth(
    lexical_results: Sequence[RetrievalResult],
    semantic_results: Sequence[RetrievalResult],
    expected_sources: Sequence[Mapping[str, Any]],
) -> tuple[int | None, int | None, int | None]:
    """Return lexical, semantic, and best exact first-relevant ranks."""

    lexical_rank = first_relevant_rank(lexical_results, expected_sources)
    semantic_rank = first_relevant_rank(semantic_results, expected_sources)
    available = [rank for rank in (lexical_rank, semantic_rank) if rank is not None]
    return lexical_rank, semantic_rank, min(available) if available else None


def analyze_candidate_recall(
    candidates: Sequence[Mapping[str, Any]],
    lexical_retriever: PolicyRetriever,
    semantic_retriever: Any,
    *,
    ranking_depth: int,
    depths: Sequence[int] = DEFAULT_DEPTHS,
) -> dict[str, Any]:
    """Run both retrievers once per supported case and analyze union recall."""

    ordered_depths = tuple(sorted(set(depths)))
    if not ordered_depths or ordered_depths[0] <= 0:
        raise ValueError("depths must contain positive integers")

    supported = [candidate for candidate in candidates if candidate["expected_sources"]]
    case_rows: list[dict[str, Any]] = []
    pool_sizes: defaultdict[int, list[int]] = defaultdict(list)
    category_hits: defaultdict[str, defaultdict[int, list[bool]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for candidate in supported:
        is_multi_turn = candidate["category"] == "multi_turn"
        category = "multi_turn_oracle" if is_multi_turn else str(candidate["category"])
        query = str(candidate["standalone_reference"] if is_multi_turn else candidate["question"])
        expected_sources = list(candidate["expected_sources"])
        lexical_results = lexical_retriever.search(query, top_k=ranking_depth)
        semantic_results = semantic_retriever.search(query, top_k=ranking_depth)
        lexical_rank, semantic_rank, best_rank = first_candidate_depth(
            lexical_results,
            semantic_results,
            expected_sources,
        )

        hits: dict[str, bool] = {}
        union_sizes: dict[str, int] = {}
        coverage: dict[str, float] | None = {} if len(expected_sources) > 1 else None
        for depth in ordered_depths:
            union = candidate_union(lexical_results, semantic_results, depth)
            hit = candidate_hit(union, expected_sources)
            hits[str(depth)] = hit
            union_sizes[str(depth)] = len(union)
            pool_sizes[depth].append(len(union))
            category_hits[category][depth].append(hit)
            if coverage is not None:
                coverage[str(depth)] = candidate_source_coverage(union, expected_sources)

        case_rows.append(
            {
                "id": candidate["id"],
                "category": str(candidate["category"]),
                "evaluation_group": category,
                "query_used": query,
                "query_source": "standalone_reference" if is_multi_turn else "question",
                "expected_source_count": len(expected_sources),
                "lexical_first_relevant_rank": lexical_rank,
                "semantic_first_relevant_rank": semantic_rank,
                "best_first_relevant_rank": best_rank,
                "candidate_hit_by_depth": hits,
                "union_size_by_depth": union_sizes,
                **({"source_coverage_by_depth": coverage} if coverage is not None else {}),
            }
        )

    total = len(case_rows)
    overall = {
        str(depth): {
            "hits": sum(bool(row["candidate_hit_by_depth"][str(depth)]) for row in case_rows),
            "total": total,
            "hit_rate": (
                sum(bool(row["candidate_hit_by_depth"][str(depth)]) for row in case_rows) / total
                if total
                else 0.0
            ),
        }
        for depth in ordered_depths
    }
    by_category = {
        category: {
            str(depth): {
                "hits": sum(category_hits[category][depth]),
                "total": len(category_hits[category][depth]),
                "hit_rate": (
                    sum(category_hits[category][depth]) / len(category_hits[category][depth])
                    if category_hits[category][depth]
                    else 0.0
                ),
            }
            for depth in ordered_depths
        }
        for category in SUPPORTED_CATEGORIES
    }
    multi_source_rows = [row for row in case_rows if row["expected_source_count"] > 1]
    multi_source = {
        "case_count": len(multi_source_rows),
        "mean_coverage_by_depth": {
            str(depth): (
                mean(float(row["source_coverage_by_depth"][str(depth)]) for row in multi_source_rows)
                if multi_source_rows
                else 0.0
            )
            for depth in ordered_depths
        },
        "cases": [
            {
                "id": row["id"],
                "expected_source_count": row["expected_source_count"],
                "coverage_by_depth": row["source_coverage_by_depth"],
            }
            for row in multi_source_rows
        ],
    }
    failures = {
        str(depth): [
            row["id"]
            for row in case_rows
            if not row["candidate_hit_by_depth"][str(depth)]
        ]
        for depth in ordered_depths
    }
    pool_summary = {
        str(depth): {
            "average": mean(pool_sizes[depth]) if pool_sizes[depth] else 0.0,
            "minimum": min(pool_sizes[depth]) if pool_sizes[depth] else 0,
            "maximum": max(pool_sizes[depth]) if pool_sizes[depth] else 0,
        }
        for depth in ordered_depths
    }
    exact_depths = [
        int(row["best_first_relevant_rank"])
        for row in case_rows
        if row["best_first_relevant_rank"] is not None
    ]
    depth_distribution = dict(sorted(Counter(exact_depths).items()))
    final_rate = overall[str(ordered_depths[-1])]["hit_rate"]
    tested_plateau_start = next(
        (
            depth
            for index, depth in enumerate(ordered_depths)
            if all(
                overall[str(later)]["hit_rate"] == final_rate
                for later in ordered_depths[index:]
            )
        ),
        ordered_depths[-1],
    )
    plateau = {
        "final_tested_hit_rate": final_rate,
        "first_tested_depth_at_final_rate": tested_plateau_start,
        "exact_depth_recalling_all_supported": (
            max(exact_depths) if len(exact_depths) == total else None
        ),
    }
    return {
        "depths": list(ordered_depths),
        "supported_case_count": total,
        "overall_candidate_recall": overall,
        "by_category": by_category,
        "multi_source_coverage": multi_source,
        "failures_by_depth": failures,
        "candidate_pool_size": pool_summary,
        "first_candidate_depth_distribution": {
            str(depth): count for depth, count in depth_distribution.items()
        },
        "plateau": plateau,
        "cases": case_rows,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    config = report["configuration"]
    analysis = report["analysis"]
    depths = analysis["depths"]
    lines = [
        "# Candidate recall upper-bound analysis",
        "",
        f"- Supported cases: {analysis['supported_case_count']}",
        f"- Candidate depths per retriever: {', '.join(str(depth) for depth in depths)}",
        f"- Lexical: `{config['lexical_model']}`",
        f"- Semantic: `{config['semantic_model']}`",
        f"- Candidate SHA-256: `{config['candidates_sha256']}`",
        f"- Multi-turn mode: `{config['multi_turn_query_mode']}`",
        "",
        "## Overall candidate recall",
        "",
    ]
    for depth in depths:
        row = analysis["overall_candidate_recall"][str(depth)]
        lines.append(f"- @{depth}: {row['hits']}/{row['total']} = {row['hit_rate']:.4f}")

    lines.extend(["", "## Recall by category", ""])
    for category in SUPPORTED_CATEGORIES:
        values = ", ".join(
            f"@{depth}={analysis['by_category'][category][str(depth)]['hit_rate']:.4f}"
            for depth in depths
        )
        lines.append(f"- {category}: {values}")

    multi = analysis["multi_source_coverage"]
    lines.extend(["", "## Multi-source coverage", ""])
    lines.append(
        "- Mean: "
        + ", ".join(
            f"@{depth}={multi['mean_coverage_by_depth'][str(depth)]:.4f}"
            for depth in depths
        )
    )
    for row in multi["cases"]:
        values = ", ".join(
            f"@{depth}={row['coverage_by_depth'][str(depth)]:.4f}"
            for depth in depths
        )
        lines.append(f"- `{row['id']}` ({row['expected_source_count']} expected): {values}")

    lines.extend(["", "## Failures by depth", ""])
    for depth in depths:
        failures = analysis["failures_by_depth"][str(depth)]
        rendered = ", ".join(f"`{case_id}`" for case_id in failures) if failures else "None."
        lines.append(f"- @{depth}: {rendered}")

    lines.extend(["", "## First relevant ranks", ""])
    for row in analysis["cases"]:
        lines.append(
            f"- `{row['id']}`: lexical={row['lexical_first_relevant_rank']}, "
            f"semantic={row['semantic_first_relevant_rank']}, best={row['best_first_relevant_rank']}"
        )

    distribution = analysis["first_candidate_depth_distribution"]
    lines.extend(["", "## First candidate depth distribution", ""])
    for depth, count in distribution.items():
        lines.append(f"- Depth {depth}: {count} case(s)")

    lines.extend(["", "## Candidate pool size", ""])
    for depth in depths:
        row = analysis["candidate_pool_size"][str(depth)]
        lines.append(
            f"- @{depth}: average={row['average']:.2f}, minimum={row['minimum']}, maximum={row['maximum']}"
        )

    plateau = analysis["plateau"]
    lines.extend(
        [
            "",
            "## Recall plateau",
            "",
            f"- Final tested hit rate: {plateau['final_tested_hit_rate']:.4f}",
            f"- First tested depth at the final rate: {plateau['first_tested_depth_at_final_rate']}",
            f"- Exact depth that recalls all supported cases: {plateau['exact_depth_recalling_all_supported']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=project_root / "eval" / "retrieval_candidates.json",
    )
    parser.add_argument(
        "--lexical-index",
        type=Path,
        default=project_root / "cache" / "policy_index.json",
    )
    parser.add_argument(
        "--semantic-index",
        type=Path,
        default=project_root / "cache" / "semantic_index.json",
    )
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=project_root / "cache" / "huggingface",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "candidate_recall_analysis.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "candidate_recall_analysis.md",
    )
    args = parser.parse_args(argv)

    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.semantic_indexing import load_semantic_index
    from src.semantic_retriever import SemanticPolicyRetriever

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    lexical_index = load_index(args.lexical_index)
    semantic_index = load_semantic_index(args.semantic_index)
    if [chunk.to_dict() for chunk in lexical_index.chunks] != [
        chunk.to_dict() for chunk in semantic_index.chunks
    ]:
        raise ValueError("lexical and semantic indexes do not contain identical chunks")

    lexical_retriever = PolicyRetriever(lexical_index)
    semantic_encoder = SentenceTransformerEncoder(
        semantic_index.model_name,
        cache_folder=args.model_cache,
        device=args.device,
        local_files_only=True,
    )
    semantic_retriever = SemanticPolicyRetriever(semantic_index, semantic_encoder)
    analysis = analyze_candidate_recall(
        candidates,
        lexical_retriever,
        semantic_retriever,
        ranking_depth=len(lexical_index.chunks),
    )
    report = {
        "configuration": {
            "candidates_path": args.candidates.as_posix(),
            "candidates_sha256": _sha256(args.candidates),
            "lexical_index_path": args.lexical_index.as_posix(),
            "lexical_index_sha256": _sha256(args.lexical_index),
            "semantic_index_path": args.semantic_index.as_posix(),
            "semantic_index_sha256": _sha256(args.semantic_index),
            "lexical_model": lexical_index.embedder.model,
            "semantic_model": semantic_index.model_name,
            "chunk_count": len(lexical_index.chunks),
            "multi_turn_query_mode": "standalone_reference_only",
            "union_deduplication": "chunk_id",
            "matching": "shared eval source_path and optional heading_contains logic",
        },
        "analysis": analysis,
    }
    _write_atomic(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    _write_atomic(args.markdown_output, render_markdown(report))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Markdown: {args.markdown_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

