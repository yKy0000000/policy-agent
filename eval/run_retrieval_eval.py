"""Run one retrieval backend against the shared retrieval candidate cases.

This runner measures retrieval only. It does not rewrite multi-turn queries,
judge unsupported cases, or change the retriever/index in any way.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping, Protocol, Sequence

from src.indexing import load_index
from src.retriever import PolicyRetriever, RetrievalResult


DISPLAY_TOP_K = 5
HIT_CUTOFFS = (1, 3, 5)
COVERAGE_CUTOFFS = (3, 5)
SUPPORTED_CATEGORIES = ("direct", "semantic", "broad", "specific", "multi_turn_oracle")


class RetrieverBackend(Protocol):
    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]: ...


def source_matches(result: RetrievalResult, expected_source: Mapping[str, Any]) -> bool:
    """Return whether a retrieved chunk satisfies one expected source rule."""

    if result.source_path != expected_source["source_path"]:
        return False
    heading_contains = str(expected_source.get("heading_contains", "")).strip()
    if not heading_contains:
        return True
    heading_path = " > ".join(result.heading_path)
    return heading_contains.casefold() in heading_path.casefold()


def first_relevant_rank(
    results: Sequence[RetrievalResult],
    expected_sources: Sequence[Mapping[str, Any]],
) -> int | None:
    """Return the one-based rank of the first chunk matching any source."""

    for rank, result in enumerate(results, start=1):
        if any(source_matches(result, source) for source in expected_sources):
            return rank
    return None


def source_coverage_at_k(
    results: Sequence[RetrievalResult],
    expected_sources: Sequence[Mapping[str, Any]],
    k: int,
) -> float:
    """Return the fraction of distinct expected source rules covered by top-k."""

    if not expected_sources:
        raise ValueError("source coverage requires at least one expected source")
    top_results = results[:k]
    covered = sum(
        any(source_matches(result, source) for result in top_results)
        for source in expected_sources
    )
    return covered / len(expected_sources)


def aggregate_metrics(case_results: Iterable[Mapping[str, Any]]) -> dict[str, float | int]:
    """Aggregate supported-case Hit@k and reciprocal-rank values."""

    rows = list(case_results)
    if not rows:
        return {"case_count": 0, "hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr": 0.0}
    count = len(rows)
    return {
        "case_count": count,
        "hit_at_1": sum(bool(row["hit_at_1"]) for row in rows) / count,
        "hit_at_3": sum(bool(row["hit_at_3"]) for row in rows) / count,
        "hit_at_5": sum(bool(row["hit_at_5"]) for row in rows) / count,
        "mrr": sum(float(row["reciprocal_rank"]) for row in rows) / count,
    }


def evaluate_candidates(
    candidates: Sequence[Mapping[str, Any]],
    retriever: RetrieverBackend,
    *,
    ranking_depth: int,
) -> list[dict[str, Any]]:
    """Evaluate candidates using standalone questions and full index rankings."""

    evaluated: list[dict[str, Any]] = []
    for candidate in candidates:
        original_category = str(candidate["category"])
        is_multi_turn = original_category == "multi_turn"
        query = str(candidate["standalone_reference"] if is_multi_turn else candidate["question"])
        expected_sources = list(candidate["expected_sources"])
        full_ranking = retriever.search(query, top_k=ranking_depth)
        top_results = [_serialize_result(rank, result) for rank, result in enumerate(full_ranking[:DISPLAY_TOP_K], start=1)]

        row: dict[str, Any] = {
            "id": candidate["id"],
            "category": original_category,
            "evaluation_group": "multi_turn_oracle" if is_multi_turn else original_category,
            "query_used": query,
            "query_source": "standalone_reference" if is_multi_turn else "question",
            "expected_sources": expected_sources,
            "top_5": top_results,
        }

        if not expected_sources:
            row.update(
                {
                    "supported": False,
                    "hit_at_1": None,
                    "hit_at_3": None,
                    "hit_at_5": None,
                    "first_relevant_rank": None,
                    "reciprocal_rank": None,
                }
            )
        else:
            rank = first_relevant_rank(full_ranking, expected_sources)
            row.update(
                {
                    "supported": True,
                    "hit_at_1": rank is not None and rank <= 1,
                    "hit_at_3": rank is not None and rank <= 3,
                    "hit_at_5": rank is not None and rank <= 5,
                    "first_relevant_rank": rank,
                    "reciprocal_rank": 1.0 / rank if rank is not None else 0.0,
                }
            )
            if len(expected_sources) > 1:
                row["source_coverage_at_3"] = source_coverage_at_k(full_ranking, expected_sources, 3)
                row["source_coverage_at_5"] = source_coverage_at_k(full_ranking, expected_sources, 5)
        evaluated.append(row)
    return evaluated


def validate_reranked_candidate_recall(
    candidates: Sequence[Mapping[str, Any]],
    retriever: Any,
) -> dict[str, Any]:
    """Verify the fixed pre-reranking union contains evidence for every supported case."""

    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        expected_sources = list(candidate["expected_sources"])
        if not expected_sources:
            continue
        is_multi_turn = candidate["category"] == "multi_turn"
        query = str(candidate["standalone_reference"] if is_multi_turn else candidate["question"])
        pool = retriever.candidates(query)
        hit = any(
            source_matches(item.result, expected)
            for item in pool
            for expected in expected_sources
        )
        rows.append(
            {
                "id": candidate["id"],
                "candidate_count": len(pool),
                "hit": hit,
            }
        )
    hits = sum(bool(row["hit"]) for row in rows)
    report = {
        "supported_case_count": len(rows),
        "hits": hits,
        "recall": hits / len(rows) if rows else 0.0,
        "failures": [row["id"] for row in rows if not row["hit"]],
        "cases": rows,
    }
    if rows and hits != len(rows):
        raise RuntimeError(
            "reranked candidate recall must be 1.0000 before evaluation; "
            f"missing: {', '.join(report['failures'])}"
        )
    return report


def summarize_rerank_performance(timings: Sequence[Any]) -> dict[str, Any]:
    """Summarize candidate counts and model/pipeline latency for one eval run."""

    if not timings:
        return {
            "query_count": 0,
            "candidate_count_average": 0.0,
            "candidate_count_minimum": 0,
            "candidate_count_maximum": 0,
            "reranker_total_seconds": 0.0,
            "reranker_mean_seconds_per_query": 0.0,
            "reranker_p50_seconds": 0.0,
            "reranker_p95_seconds": 0.0,
            "pipeline_total_seconds": 0.0,
        }
    counts = [int(row.candidate_count) for row in timings]
    reranker_seconds = [float(row.reranker_seconds) for row in timings]
    return {
        "query_count": len(timings),
        "candidate_count_average": mean(counts),
        "candidate_count_minimum": min(counts),
        "candidate_count_maximum": max(counts),
        "reranker_total_seconds": sum(reranker_seconds),
        "reranker_mean_seconds_per_query": mean(reranker_seconds),
        "reranker_p50_seconds": median(reranker_seconds),
        "reranker_p95_seconds": _percentile(reranker_seconds, 0.95),
        "pipeline_total_seconds": sum(float(row.total_seconds) for row in timings),
    }


def build_report(
    backend: str,
    candidates_path: Path,
    index_path: Path,
    index_model: str,
    index_provider: str,
    index_chunk_count: int,
    case_results: Sequence[Mapping[str, Any]],
    extra_configuration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    supported = [row for row in case_results if row["supported"]]
    unsupported = [row for row in case_results if not row["supported"]]
    by_category = {
        category: aggregate_metrics(
            row for row in supported if row["evaluation_group"] == category
        )
        for category in SUPPORTED_CATEGORIES
    }
    multi_source = [row for row in supported if len(row["expected_sources"]) > 1]
    multi_source_summary = {
        "case_count": len(multi_source),
        "mean_coverage_at_3": (
            sum(float(row["source_coverage_at_3"]) for row in multi_source) / len(multi_source)
            if multi_source
            else 0.0
        ),
        "mean_coverage_at_5": (
            sum(float(row["source_coverage_at_5"]) for row in multi_source) / len(multi_source)
            if multi_source
            else 0.0
        ),
        "cases": [
            {
                "id": row["id"],
                "expected_source_count": len(row["expected_sources"]),
                "coverage_at_3": row["source_coverage_at_3"],
                "coverage_at_5": row["source_coverage_at_5"],
            }
            for row in multi_source
        ],
    }
    review_priority = {
        "hit_at_5_zero": [row["id"] for row in supported if not row["hit_at_5"]],
        "hit_at_1_zero_but_hit_at_5_one": [
            row["id"] for row in supported if not row["hit_at_1"] and row["hit_at_5"]
        ],
    }
    configuration = {
            "backend": backend,
            "candidates_path": candidates_path.as_posix(),
            "candidates_sha256": _sha256(candidates_path),
            "index_path": index_path.as_posix(),
            "index_sha256": _sha256(index_path),
            "embedding_provider": index_provider,
            "embedding_model": index_model,
            "index_chunk_count": index_chunk_count,
            "ranking_depth": index_chunk_count,
            "display_top_k": DISPLAY_TOP_K,
            "multi_turn_query_mode": "standalone_reference_only",
            "unsupported_scoring": "excluded_from_hit_and_mrr",
            "matching": "exact source_path; when non-empty, case-insensitive heading_contains substring in joined heading_path",
        }
    if extra_configuration:
        configuration.update(extra_configuration)
    return {
        "configuration": configuration,
        "summary": {
            "overall_supported": aggregate_metrics(supported),
            "by_category": by_category,
            "multi_source_coverage": multi_source_summary,
            "unsupported_case_count": len(unsupported),
            "review_priority": review_priority,
        },
        "cases": list(case_results),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    config = report["configuration"]
    summary = report["summary"]
    cases = report["cases"]
    lines = [
        f"# Retrieval {config['backend']} baseline",
        "",
        "This report evaluates retrieval only. Multi-turn cases use their standalone references; unsupported cases are displayed but not scored.",
        "",
        "## Configuration",
        "",
        f"- Embedding: `{config['embedding_provider']}/{config['embedding_model']}`",
        f"- Index chunks / ranking depth: {config['index_chunk_count']}",
        f"- Candidate SHA-256: `{config['candidates_sha256']}`",
        f"- Index SHA-256: `{config['index_sha256']}`",
        "- Source match: exact `source_path`, plus case-insensitive `heading_contains` matching when non-empty.",
        "",
        "## Overall supported-case metrics",
        "",
    ]
    if config["backend"] == "reranked":
        lines[4:4] = [
            f"- Candidate union: lexical Top-{config['lexical_candidate_k']} + semantic Top-{config['semantic_candidate_k']}, deduplicated by `chunk_id`",
            f"- Reranker: `{config['reranker_model']}`",
            "- Reranker features: query + structured candidate text only; component scores and ranks excluded.",
            "",
        ]
    lines.extend(_metric_bullets(summary["overall_supported"]))
    lines.extend(["", "## Metrics by category", ""])
    for category in SUPPORTED_CATEGORIES:
        lines.extend([f"### {category}", ""])
        lines.extend(_metric_bullets(summary["by_category"][category]))
        lines.append("")

    coverage = summary["multi_source_coverage"]
    lines.extend(
        [
            "## Multi-source coverage",
            "",
            f"- Multi-source cases: {coverage['case_count']}",
            f"- Mean coverage@3: {_format_metric(coverage['mean_coverage_at_3'])}",
            f"- Mean coverage@5: {_format_metric(coverage['mean_coverage_at_5'])}",
            "",
        ]
    )
    for row in coverage["cases"]:
        lines.append(
            f"- `{row['id']}` ({row['expected_source_count']} expected): "
            f"coverage@3={_format_metric(row['coverage_at_3'])}, "
            f"coverage@5={_format_metric(row['coverage_at_5'])}"
        )

    if config["backend"] == "reranked":
        candidate_recall = summary["candidate_recall_before_reranking"]
        performance = summary["performance"]
        lines.extend(
            [
                "",
                "## Candidate recall before reranking",
                "",
                f"- Supported: {candidate_recall['hits']}/{candidate_recall['supported_case_count']}",
                f"- Recall: {_format_metric(candidate_recall['recall'])}",
                "",
                "## Reranking performance",
                "",
                f"- Queries: {performance['query_count']}",
                f"- Candidate count average/min/max: {performance['candidate_count_average']:.2f} / "
                f"{performance['candidate_count_minimum']} / {performance['candidate_count_maximum']}",
                f"- Cross-Encoder total: {performance['reranker_total_seconds']:.4f}s",
                f"- Mean per query: {performance['reranker_mean_seconds_per_query']:.4f}s",
                f"- p50 / p95: {performance['reranker_p50_seconds']:.4f}s / "
                f"{performance['reranker_p95_seconds']:.4f}s",
                f"- End-to-end retrieval plus reranking total: {performance['pipeline_total_seconds']:.4f}s",
            ]
        )

    review = summary["review_priority"]
    lines.extend(
        [
            "",
            "## Priority cases for human review",
            "",
            "### Supported cases with Hit@5 = 0",
            "",
            _id_list(review["hit_at_5_zero"]),
            "",
            "### Supported cases with Hit@1 = 0 and Hit@5 = 1",
            "",
            _id_list(review["hit_at_1_zero_but_hit_at_5_one"]),
            "",
            "## Unsupported cases (not scored)",
            "",
        ]
    )
    for row in cases:
        if not row["supported"]:
            lines.extend(_unsupported_overview(row))

    lines.extend(["## Per-case results", ""])
    for row in cases:
        lines.extend(_case_markdown(row))
    return "\n".join(lines).rstrip() + "\n"


def _serialize_result(rank: int, result: RetrievalResult) -> dict[str, Any]:
    serialized = {
        "rank": rank,
        "score": result.score,
        "title": result.title,
        "heading_path": list(result.heading_path),
        "source_path": result.source_path,
        "chunk_id": result.chunk_id,
    }
    if hasattr(result, "lexical_rank"):
        serialized["lexical_rank"] = getattr(result, "lexical_rank")
    if hasattr(result, "semantic_rank"):
        serialized["semantic_rank"] = getattr(result, "semantic_rank")
    if hasattr(result, "reranker_score"):
        serialized["reranker_score"] = getattr(result, "reranker_score")
    return serialized


def _metric_bullets(metrics: Mapping[str, Any]) -> list[str]:
    return [
        f"- Cases: {metrics['case_count']}",
        f"- Hit@1: {_format_metric(metrics['hit_at_1'])}",
        f"- Hit@3: {_format_metric(metrics['hit_at_3'])}",
        f"- Hit@5: {_format_metric(metrics['hit_at_5'])}",
        f"- MRR: {_format_metric(metrics['mrr'])}",
    ]


def _format_metric(value: Any) -> str:
    return f"{float(value):.4f}"


def _id_list(ids: Sequence[str]) -> str:
    return ", ".join(f"`{case_id}`" for case_id in ids) if ids else "None."


def _expected_source_line(source: Mapping[str, Any]) -> str:
    heading = source.get("heading_contains") or "(path only)"
    return f"`{source['title']}` | heading contains `{heading}` | `{source['source_path']}`"


def _retrieval_line(item: Mapping[str, Any]) -> str:
    heading = " > ".join(item["heading_path"]) or "(document introduction)"
    line = (
        f"{item['rank']}. score={float(item['score']):.4f} | `{item['title']}` | "
        f"heading `{heading}` | `{item['source_path']}`"
    )
    if "lexical_rank" in item or "semantic_rank" in item:
        line += (
            f" | lexical_rank={item.get('lexical_rank')}"
            f" | semantic_rank={item.get('semantic_rank')}"
        )
    if "reranker_score" in item:
        line += f" | reranker_score={float(item['reranker_score']):.4f}"
    return line


def _unsupported_overview(row: Mapping[str, Any]) -> list[str]:
    lines = [f"### {row['id']}", "", f"- Query: {row['query_used']}", "- Top-5:"]
    lines.extend(f"  - {_retrieval_line(item)}" for item in row["top_5"])
    lines.append("")
    return lines


def _case_markdown(row: Mapping[str, Any]) -> list[str]:
    lines = [
        f"### {row['id']}",
        "",
        f"- Category: `{row['category']}`",
        f"- Evaluation group: `{row['evaluation_group']}`",
        f"- Query source: `{row['query_source']}`",
        f"- Query actually used: {row['query_used']}",
        "- Expected sources:",
    ]
    if row["expected_sources"]:
        lines.extend(f"  - {_expected_source_line(source)}" for source in row["expected_sources"])
    else:
        lines.append("  - `[]` (unsupported; not scored)")

    if row["supported"]:
        rank = row["first_relevant_rank"] if row["first_relevant_rank"] is not None else "not found"
        lines.extend(
            [
                f"- Hit@1 / Hit@3 / Hit@5: {int(row['hit_at_1'])} / {int(row['hit_at_3'])} / {int(row['hit_at_5'])}",
                f"- First relevant rank: {rank}",
                f"- Reciprocal rank: {_format_metric(row['reciprocal_rank'])}",
            ]
        )
        if "source_coverage_at_3" in row:
            lines.extend(
                [
                    f"- Source coverage@3: {_format_metric(row['source_coverage_at_3'])}",
                    f"- Source coverage@5: {_format_metric(row['source_coverage_at_5'])}",
                ]
            )
    else:
        lines.append("- Hit/MRR: not computed")

    lines.append("- Top-5 retrieved chunks:")
    lines.extend(f"  - {_retrieval_line(item)}" for item in row["top_5"])
    lines.extend(["", "---", ""])
    return lines


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _percentile(values: Sequence[float], quantile: float) -> float:
    """Return a linearly interpolated percentile for a small timing sample."""

    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=("lexical", "semantic", "hybrid", "reranked"),
        default="lexical",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=project_root / "eval" / "retrieval_candidates.json",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--lexical-index",
        type=Path,
        default=project_root / "cache" / "policy_index.json",
        help="lexical component index (hybrid backend)",
    )
    parser.add_argument(
        "--semantic-index",
        type=Path,
        default=project_root / "cache" / "semantic_index.json",
        help="semantic component index (hybrid backend)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=project_root / "cache" / "huggingface",
        help="sentence-transformers model cache (semantic backend only)",
    )
    parser.add_argument("--device", default="cpu", help="semantic model device")
    parser.add_argument("--rrf-k", type=int, default=60, help="hybrid RRF rank constant")
    parser.add_argument(
        "--hybrid-candidate-depth",
        type=int,
        default=20,
        help="candidates requested from each component retriever",
    )
    parser.add_argument(
        "--reranker-model",
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="local sentence-transformers Cross-Encoder model",
    )
    parser.add_argument("--reranker-batch-size", type=int, default=16)
    parser.add_argument(
        "--allow-reranker-download",
        action="store_true",
        help="allow one-time model download into --model-cache; otherwise require local files",
    )
    args = parser.parse_args(argv)

    if args.backend in ("hybrid", "reranked") and args.index is not None:
        parser.error(
            "--index is only for lexical or semantic; use component index flags for combined backends"
        )
    index_path = args.index or (
        args.lexical_index if args.backend == "lexical" else args.semantic_index
    )
    json_output = args.json_output or (
        project_root / "eval" / "results" / "retrieval_baseline.json"
        if args.backend == "lexical"
        else (
            project_root / "eval" / "results" / "retrieval_semantic.json"
            if args.backend == "semantic"
            else (
                project_root / "eval" / "results" / "retrieval_hybrid.json"
                if args.backend == "hybrid"
                else project_root / "eval" / "results" / "retrieval_reranked.json"
            )
        )
    )
    markdown_output = args.markdown_output or (
        project_root / "eval" / "results" / "retrieval_baseline.md"
        if args.backend == "lexical"
        else (
            project_root / "eval" / "results" / "retrieval_semantic.md"
            if args.backend == "semantic"
            else (
                project_root / "eval" / "results" / "retrieval_hybrid.md"
                if args.backend == "hybrid"
                else project_root / "eval" / "results" / "retrieval_reranked.md"
            )
        )
    )

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        raise ValueError("candidate dataset must be a JSON array")
    if args.backend == "lexical":
        index = load_index(index_path)
        retriever: RetrieverBackend = PolicyRetriever(index)
        index_model = index.embedder.model
        index_provider = index.embedder.provider
        index_chunk_count = len(index.chunks)
        extra_configuration: dict[str, Any] = {}
    elif args.backend == "semantic":
        from src.semantic_embeddings import SentenceTransformerEncoder
        from src.semantic_indexing import load_semantic_index
        from src.semantic_retriever import SemanticPolicyRetriever

        semantic_index = load_semantic_index(index_path)
        encoder = SentenceTransformerEncoder(
            semantic_index.model_name,
            cache_folder=args.model_cache,
            device=args.device,
            local_files_only=True,
        )
        retriever = SemanticPolicyRetriever(semantic_index, encoder)
        index_model = semantic_index.model_name
        index_provider = semantic_index.provider
        index_chunk_count = len(semantic_index.chunks)
        extra_configuration = {}
    elif args.backend == "hybrid":
        from src.hybrid_retriever import HybridConfig, HybridPolicyRetriever
        from src.semantic_embeddings import SentenceTransformerEncoder
        from src.semantic_indexing import load_semantic_index
        from src.semantic_retriever import SemanticPolicyRetriever

        lexical_index = load_index(args.lexical_index)
        semantic_index = load_semantic_index(args.semantic_index)
        if [chunk.to_dict() for chunk in lexical_index.chunks] != [
            chunk.to_dict() for chunk in semantic_index.chunks
        ]:
            raise ValueError("hybrid component indexes do not contain identical chunks")
        semantic_encoder = SentenceTransformerEncoder(
            semantic_index.model_name,
            cache_folder=args.model_cache,
            device=args.device,
            local_files_only=True,
        )
        lexical_retriever = PolicyRetriever(lexical_index)
        semantic_retriever = SemanticPolicyRetriever(semantic_index, semantic_encoder)
        hybrid_config = HybridConfig(
            rrf_k=args.rrf_k,
            candidate_depth=args.hybrid_candidate_depth,
        )
        retriever = HybridPolicyRetriever(
            lexical_retriever,
            semantic_retriever,
            hybrid_config,
        )
        index_model = f"{lexical_index.embedder.model} + {semantic_index.model_name}"
        index_provider = "hybrid-rrf"
        index_chunk_count = len(lexical_index.chunks)
        extra_configuration = {
            "lexical_index_path": args.lexical_index.as_posix(),
            "lexical_index_sha256": _sha256(args.lexical_index),
            "semantic_index_path": args.semantic_index.as_posix(),
            "semantic_index_sha256": _sha256(args.semantic_index),
            "rrf_k": hybrid_config.rrf_k,
            "hybrid_candidate_depth": hybrid_config.candidate_depth,
            "fusion": "unweighted reciprocal rank fusion by chunk_id",
        }

    else:
        from src.reranked_retriever import RerankedPolicyRetriever
        from src.reranker import CrossEncoderReranker
        from src.semantic_embeddings import SentenceTransformerEncoder
        from src.semantic_indexing import load_semantic_index
        from src.semantic_retriever import SemanticPolicyRetriever

        lexical_index = load_index(args.lexical_index)
        semantic_index = load_semantic_index(args.semantic_index)
        if [chunk.to_dict() for chunk in lexical_index.chunks] != [
            chunk.to_dict() for chunk in semantic_index.chunks
        ]:
            raise ValueError("reranked component indexes do not contain identical chunks")
        semantic_encoder = SentenceTransformerEncoder(
            semantic_index.model_name,
            cache_folder=args.model_cache,
            device=args.device,
            local_files_only=True,
        )
        pair_scorer = CrossEncoderReranker(
            args.reranker_model,
            cache_folder=args.model_cache,
            device=args.device,
            batch_size=args.reranker_batch_size,
            local_files_only=not args.allow_reranker_download,
        )
        retriever = RerankedPolicyRetriever(
            PolicyRetriever(lexical_index),
            SemanticPolicyRetriever(semantic_index, semantic_encoder),
            pair_scorer,
        )
        index_model = args.reranker_model
        index_provider = pair_scorer.provider
        index_chunk_count = len(lexical_index.chunks)
        extra_configuration = {
            "lexical_index_path": args.lexical_index.as_posix(),
            "lexical_index_sha256": _sha256(args.lexical_index),
            "semantic_index_path": args.semantic_index.as_posix(),
            "semantic_index_sha256": _sha256(args.semantic_index),
            "lexical_candidate_k": retriever.lexical_candidate_k,
            "semantic_candidate_k": retriever.semantic_candidate_k,
            "candidate_union": "chunk_id deduplication",
            "reranker_model": pair_scorer.model_name,
            "reranker_batch_size": pair_scorer.batch_size,
            "reranker_input": "query paired with Document/Section/chunk text; no component scores or ranks",
        }

    candidate_recall: dict[str, Any] | None = None
    if args.backend == "reranked":
        candidate_recall = validate_reranked_candidate_recall(candidates, retriever)

    case_results = evaluate_candidates(candidates, retriever, ranking_depth=index_chunk_count)
    report = build_report(
        args.backend,
        args.candidates,
        index_path,
        index_model,
        index_provider,
        index_chunk_count,
        case_results,
        extra_configuration,
    )
    if args.backend == "reranked":
        report["summary"]["candidate_recall_before_reranking"] = candidate_recall
        report["summary"]["performance"] = summarize_rerank_performance(retriever.timings)

    _write_text_atomic(
        json_output,
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(markdown_output, render_markdown(report))

    overall = report["summary"]["overall_supported"]
    print(f"Supported cases: {overall['case_count']}")
    print(
        "Hit@1={:.4f} Hit@3={:.4f} Hit@5={:.4f} MRR={:.4f}".format(
            overall["hit_at_1"],
            overall["hit_at_3"],
            overall["hit_at_5"],
            overall["mrr"],
        )
    )
    print(f"Backend: {args.backend}")
    print(f"JSON: {json_output.resolve()}")
    print(f"Markdown: {markdown_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
