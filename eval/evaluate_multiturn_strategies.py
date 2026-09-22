"""Evaluate multi-turn query strategies through the frozen reranked pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from eval.run_retrieval_eval import first_relevant_rank, source_coverage_at_k
from src.conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    DEFAULT_HISTORY_TURNS,
    QueryRewriteError,
    RewriteCache,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from src.llm_client import LLMClientError, LLMConfig, OpenAIChatCompletionsClient


STRATEGIES = ("latest_only", "raw_concat", "llm_rewrite", "oracle")
HIT_CUTOFFS = (1, 3, 5)


def raw_concat_query(
    history: Sequence[Mapping[str, str]],
    latest_question: str,
    *,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> str:
    """Concatenate the limited history and latest question without an LLM."""

    recent = select_recent_history(history, max_turns=max_history_turns)
    lines = [f"{item['role'].capitalize()}: {item['content']}" for item in recent]
    lines.append(f"User: {latest_question.strip()}")
    return "\n".join(lines)


def generate_rewrites(
    cases: Sequence[Mapping[str, Any]],
    client: Any,
    cache: RewriteCache,
    *,
    model: str,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """Generate or load cached rewrites while preserving explicit failures."""

    rewrites: dict[str, dict[str, Any]] = {}
    stats = {"api_calls": 0, "cache_hits": 0, "cache_misses": 0, "errors": 0}
    for case in cases:
        history = list(case["history"])
        question = str(case["question"])
        key = rewrite_cache_key(
            model=model,
            history=history,
            latest_question=question,
            max_history_turns=max_history_turns,
        )
        cached = cache.get(key)
        if cached is not None:
            stats["cache_hits"] += 1
            rewrites[str(case["id"])] = {
                "status": "success",
                "rewrite": cached,
                "source": "cache",
                "cache_key": key,
            }
            continue

        stats["cache_misses"] += 1
        stats["api_calls"] += 1
        try:
            rewritten = rewrite_or_keep(
                history,
                question,
                client,
                max_history_turns=max_history_turns,
            )
        except QueryRewriteError as error:
            stats["errors"] += 1
            rewrites[str(case["id"])] = {
                "status": "error",
                "rewrite": None,
                "source": "api",
                "cache_key": key,
                "error": str(error),
            }
            continue
        cache.set(
            key,
            rewritten,
            {
                "model": model,
                "prompt_version": CONTEXTUALIZER_PROMPT_VERSION,
                "case_id": case["id"],
            },
        )
        rewrites[str(case["id"])] = {
            "status": "success",
            "rewrite": rewritten,
            "source": "api",
            "cache_key": key,
        }
    return rewrites, stats


def evaluate_strategies(
    cases: Sequence[Mapping[str, Any]],
    retriever: Any,
    rewrites: Mapping[str, Mapping[str, Any]],
    *,
    ranking_depth: int,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> dict[str, Any]:
    """Evaluate four query forms through one unchanged retrieval pipeline."""

    case_rows: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case["id"])
        history = list(case["history"])
        latest = str(case["question"])
        expected_sources = list(case["expected_sources"])
        rewrite_record = rewrites[case_id]
        queries: dict[str, str | None] = {
            "latest_only": latest,
            "raw_concat": raw_concat_query(
                history,
                latest,
                max_history_turns=max_history_turns,
            ),
            "llm_rewrite": (
                str(rewrite_record["rewrite"])
                if rewrite_record["status"] == "success"
                else None
            ),
            "oracle": str(case["standalone_reference"]),
        }
        strategy_results: dict[str, dict[str, Any]] = {}
        for strategy in STRATEGIES:
            query = queries[strategy]
            if query is None:
                strategy_results[strategy] = {
                    "status": "rewrite_error",
                    "query": None,
                    "first_relevant_rank": None,
                    "hit_at_1": None,
                    "hit_at_3": None,
                    "hit_at_5": None,
                    "reciprocal_rank": None,
                    "error": rewrite_record.get("error"),
                }
                continue
            ranking = retriever.search(query, top_k=ranking_depth)
            rank = first_relevant_rank(ranking, expected_sources)
            row = {
                "status": "success",
                "query": query,
                "first_relevant_rank": rank,
                "hit_at_1": rank is not None and rank <= 1,
                "hit_at_3": rank is not None and rank <= 3,
                "hit_at_5": rank is not None and rank <= 5,
                "reciprocal_rank": 1.0 / rank if rank is not None else 0.0,
            }
            if len(expected_sources) > 1:
                row["source_coverage_at_3"] = source_coverage_at_k(
                    ranking, expected_sources, 3
                )
                row["source_coverage_at_5"] = source_coverage_at_k(
                    ranking, expected_sources, 5
                )
            strategy_results[strategy] = row

        case_rows.append(
            {
                "id": case_id,
                "history": select_recent_history(
                    history, max_turns=max_history_turns
                ),
                "latest_question": latest,
                "llm_rewrite": rewrite_record.get("rewrite"),
                "rewrite_status": rewrite_record["status"],
                "rewrite_source": rewrite_record["source"],
                **(
                    {"rewrite_error": rewrite_record["error"]}
                    if rewrite_record["status"] == "error"
                    else {}
                ),
                "oracle_standalone_reference": case["standalone_reference"],
                "expected_sources": expected_sources,
                "strategies": strategy_results,
            }
        )

    strategy_metrics = {
        strategy: _aggregate_strategy(case_rows, strategy) for strategy in STRATEGIES
    }
    return {"metrics": strategy_metrics, "cases": case_rows}


def _aggregate_strategy(
    cases: Sequence[Mapping[str, Any]], strategy: str
) -> dict[str, Any]:
    rows = [case["strategies"][strategy] for case in cases]
    errors = [row for row in rows if row["status"] != "success"]
    if errors:
        return {
            "case_count": len(rows),
            "successful_case_count": len(rows) - len(errors),
            "error_count": len(errors),
            "complete": False,
            "hit_at_1": None,
            "hit_at_3": None,
            "hit_at_5": None,
            "mrr": None,
        }
    count = len(rows)
    return {
        "case_count": count,
        "successful_case_count": count,
        "error_count": 0,
        "complete": True,
        "hit_at_1": sum(bool(row["hit_at_1"]) for row in rows) / count,
        "hit_at_3": sum(bool(row["hit_at_3"]) for row in rows) / count,
        "hit_at_5": sum(bool(row["hit_at_5"]) for row in rows) / count,
        "mrr": sum(float(row["reciprocal_rank"]) for row in rows) / count,
    }


def render_summary(report: Mapping[str, Any]) -> str:
    lines = [
        "# Multi-turn query strategy evaluation",
        "",
        "All query strategies use the same frozen lexical Top20 + semantic Top20 candidate union and Cross-Encoder reranker.",
        "",
        "## Configuration",
        "",
        f"- Provider: `{report['configuration']['provider']}`",
        f"- Base URL: `{report['configuration']['base_url']}`",
        f"- Model: `{report['configuration']['model']}`",
        f"- History window: {report['configuration']['max_history_turns']} turns",
        f"- Prompt version: `{report['configuration']['prompt_version']}`",
        "",
        "## Metrics",
        "",
    ]
    for strategy in STRATEGIES:
        metric = report["evaluation"]["metrics"][strategy]
        if not metric["complete"]:
            lines.append(
                f"- {strategy}: incomplete ({metric['error_count']} rewrite error(s)); metrics not computed"
            )
        else:
            lines.append(
                f"- {strategy}: Hit@1={metric['hit_at_1']:.4f}, "
                f"Hit@3={metric['hit_at_3']:.4f}, Hit@5={metric['hit_at_5']:.4f}, "
                f"MRR={metric['mrr']:.4f}"
            )
    stats = report["rewrite_usage"]
    lines.extend(
        [
            "",
            "## Rewrite API/cache usage",
            "",
            f"- API calls: {stats['api_calls']}",
            f"- Cache hits: {stats['cache_hits']}",
            f"- Cache misses: {stats['cache_misses']}",
            f"- Errors: {stats['errors']}",
            "",
            "## Per-case ranks",
            "",
        ]
    )
    for case in report["evaluation"]["cases"]:
        ranks = ", ".join(
            f"{strategy}={case['strategies'][strategy]['first_relevant_rank']}"
            for strategy in STRATEGIES
        )
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Latest: {case['latest_question']}",
                f"- LLM rewrite: {case['llm_rewrite'] or '(rewrite error)'}",
                f"- Oracle: {case['oracle_standalone_reference']}",
                f"- Ranks: {ranks}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_review(report: Mapping[str, Any]) -> str:
    lines = [
        "# Multi-turn rewrite review",
        "",
        "This file is for human comparison only; no LLM-generated quality score is included.",
        "",
    ]
    for case in report["evaluation"]["cases"]:
        lines.extend([f"## {case['id']}", "", "### History", ""])
        for message in case["history"]:
            lines.append(f"- **{message['role'].capitalize()}:** {message['content']}")
        lines.extend(
            [
                "",
                "### Queries",
                "",
                f"- **Latest question:** {case['latest_question']}",
                f"- **LLM rewrite:** {case['llm_rewrite'] or '(rewrite error)'}",
                f"- **Oracle reference:** {case['oracle_standalone_reference']}",
            ]
        )
        if "rewrite_error" in case:
            lines.append(f"- **Rewrite error:** {case['rewrite_error']}")
        lines.extend(["", "### Retrieval ranks", ""])
        for strategy in STRATEGIES:
            row = case["strategies"][strategy]
            lines.append(
                f"- **{strategy}:** {row['first_relevant_rank']}"
            )
        lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def _load_frozen_retriever(project_root: Path, device: str) -> tuple[Any, int]:
    from src.indexing import load_index
    from src.reranked_retriever import RerankedPolicyRetriever
    from src.reranker import CrossEncoderReranker
    from src.retriever import PolicyRetriever
    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.semantic_indexing import load_semantic_index
    from src.semantic_retriever import SemanticPolicyRetriever

    lexical_index = load_index(project_root / "cache" / "policy_index.json")
    semantic_index = load_semantic_index(project_root / "cache" / "semantic_index.json")
    if [chunk.to_dict() for chunk in lexical_index.chunks] != [
        chunk.to_dict() for chunk in semantic_index.chunks
    ]:
        raise ValueError("lexical and semantic indexes do not contain identical chunks")
    model_cache = project_root / "cache" / "huggingface"
    semantic_encoder = SentenceTransformerEncoder(
        semantic_index.model_name,
        cache_folder=model_cache,
        device=device,
        local_files_only=True,
    )
    reranker = CrossEncoderReranker(
        cache_folder=model_cache,
        device=device,
        local_files_only=True,
    )
    retriever = RerankedPolicyRetriever(
        PolicyRetriever(lexical_index),
        SemanticPolicyRetriever(semantic_index, semantic_encoder),
        reranker,
    )
    return retriever, len(lexical_index.chunks)


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=project_root / "eval" / "retrieval_candidates.json",
    )
    parser.add_argument("--env-file", type=Path, default=project_root / ".env")
    parser.add_argument(
        "--cache",
        type=Path,
        default=project_root / "cache" / "query_rewrites.json",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "multiturn_query_strategies.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "multiturn_query_strategies.md",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=project_root / "eval" / "results" / "multiturn_rewrite_review.md",
    )
    args = parser.parse_args(argv)

    all_cases = json.loads(args.candidates.read_text(encoding="utf-8"))
    cases = [case for case in all_cases if case["category"] == "multi_turn"]
    configuration_error: str | None = None
    try:
        config = LLMConfig.from_env(args.env_file)
    except LLMClientError as error:
        configuration_error = str(error)
        model = os.environ.get("LLM_MODEL", "(not configured)") or "(not configured)"
        base_url = os.environ.get("LLM_BASE_URL", "(not configured)") or "(not configured)"
        timeout_seconds = None
        thinking_mode = None
        rewrites = {
            str(case["id"]): {
                "status": "error",
                "rewrite": None,
                "source": "configuration",
                "error": configuration_error,
            }
            for case in cases
        }
        usage = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": len(cases),
            "configuration_error": configuration_error,
        }
    else:
        model = config.model
        base_url = config.base_url
        timeout_seconds = config.timeout_seconds
        thinking_mode = config.thinking_mode
        client = OpenAIChatCompletionsClient(config)
        cache = RewriteCache(args.cache)
        rewrites, usage = generate_rewrites(
            cases,
            client,
            cache,
            model=config.model,
        )
    retriever, ranking_depth = _load_frozen_retriever(project_root, args.device)
    evaluation = evaluate_strategies(
        cases,
        retriever,
        rewrites,
        ranking_depth=ranking_depth,
    )
    report = {
        "configuration": {
            "provider": "openai-compatible-chat-completions",
            "base_url": base_url,
            "model": model,
            "timeout_seconds": timeout_seconds,
            "thinking_mode": thinking_mode,
            "temperature": 0.0,
            "max_output_tokens": 96,
            "prompt_version": CONTEXTUALIZER_PROMPT_VERSION,
            "max_history_turns": DEFAULT_HISTORY_TURNS,
            "retrieval_pipeline": "lexical Top20 + semantic Top20 union, Cross-Encoder reranker",
            "candidate_dataset_sha256": _sha256(args.candidates),
            "multi_turn_case_count": len(cases),
        },
        "rewrite_usage": usage,
        "evaluation": evaluation,
    }
    _write_atomic(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    _write_atomic(args.markdown_output, render_summary(report))
    _write_atomic(args.review_output, render_review(report))
    for strategy in STRATEGIES:
        metric = evaluation["metrics"][strategy]
        if metric["complete"]:
            print(
                f"{strategy}: Hit@1={metric['hit_at_1']:.4f} Hit@3={metric['hit_at_3']:.4f} "
                f"Hit@5={metric['hit_at_5']:.4f} MRR={metric['mrr']:.4f}"
            )
        else:
            print(f"{strategy}: incomplete ({metric['error_count']} error(s))")
    print(f"API calls={usage['api_calls']} cache hits={usage['cache_hits']}")
    if configuration_error:
        print(f"LLM configuration error: {configuration_error}")
    return 2 if usage["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
