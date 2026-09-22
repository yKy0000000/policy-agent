"""Run a small manual inspection set through rewrite, retrieval, and generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from eval.evaluate_multiturn_strategies import _load_frozen_retriever
from src.conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    DEFAULT_HISTORY_TURNS,
    RewriteCache,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from src.generator import (
    GENERATION_PROMPT_VERSION,
    GeneratedAnswerCache,
    generate_grounded_answer,
)
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient


MANUAL_CASE_IDS = (
    "ret_002",
    "ret_012",
    "ret_013",
    "multi_001",
    "ret_022",
    "ret_023",
    "ret_024",
)


def _standalone_query(
    case: Mapping[str, Any],
    client: OpenAIChatCompletionsClient,
    cache: RewriteCache,
    model: str,
    stats: dict[str, int],
) -> str:
    history = list(case.get("history", []))
    question = str(case["question"])
    key = rewrite_cache_key(
        model=model,
        history=history,
        latest_question=question,
    )
    cached = cache.get(key)
    if cached is not None:
        stats["rewrite_cache_hits"] += 1
        return cached
    stats["rewrite_api_calls"] += 1
    rewritten = rewrite_or_keep(history, question, client)
    cache.set(
        key,
        rewritten,
        {
            "model": model,
            "prompt_version": CONTEXTUALIZER_PROMPT_VERSION,
            "case_id": case["id"],
        },
    )
    return rewritten


def inspect_cases(
    cases: Sequence[Mapping[str, Any]],
    retriever: Any,
    client: OpenAIChatCompletionsClient,
    *,
    model: str,
    rewrite_cache: RewriteCache,
    generation_cache: GeneratedAnswerCache,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Run the fixed manual set without scoring answer correctness."""

    stats = {
        "rewrite_api_calls": 0,
        "rewrite_cache_hits": 0,
        "generation_api_calls": 0,
        "generation_cache_hits": 0,
        "errors": 0,
    }
    rows: list[dict[str, Any]] = []
    for case in cases:
        history = list(case.get("history", []))
        try:
            query = _standalone_query(
                case, client, rewrite_cache, model, stats
            )
            evidence = retriever.search(query, top_k=5)
            generated = generate_grounded_answer(
                str(case["question"]),
                history,
                evidence,
                client,
                model=model,
                cache=generation_cache,
            )
            if generated["response_source"] == "cache":
                stats["generation_cache_hits"] += 1
            else:
                stats["generation_api_calls"] += 1
        except Exception as error:
            stats["errors"] += 1
            rows.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "question": case["question"],
                    "history": select_recent_history(history),
                    "status": "error",
                    "error": str(error),
                }
            )
            continue

        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "history": select_recent_history(history),
                "standalone_retrieval_query": query,
                "status": "success",
                "evidence": [
                    {
                        "citation_id": f"S{rank}",
                        "rank": rank,
                        "reranker_score": item.reranker_score,
                        "chunk_id": item.chunk_id,
                        "title": item.title,
                        "heading_path": list(item.heading_path),
                        "source_path": item.source_path,
                        "source_url": item.source_url,
                    }
                    for rank, item in enumerate(evidence, start=1)
                ],
                "generation": generated,
            }
        )
    return rows, stats


def render_review(report: Mapping[str, Any]) -> str:
    config = report["configuration"]
    lines = [
        "# Grounded generation manual review",
        "",
        "This is a manual inspection artifact. It does not contain automated answer-quality scores.",
        "",
        "## Configuration",
        "",
        f"- Model: `{config['model']}`",
        f"- Generation prompt: `{config['generation_prompt_version']}`",
        f"- History window: {config['max_history_turns']} turns",
        "- Retrieval: frozen lexical Top20 + semantic Top20 union + Cross-Encoder reranker Top5",
        "",
        "## API/cache usage",
        "",
    ]
    usage = report["usage"]
    lines.extend(
        [
            f"- Rewrite API calls: {usage['rewrite_api_calls']}",
            f"- Rewrite cache hits: {usage['rewrite_cache_hits']}",
            f"- Generation API calls: {usage['generation_api_calls']}",
            f"- Generation cache hits: {usage['generation_cache_hits']}",
            f"- Errors: {usage['errors']}",
            "",
        ]
    )
    for row in report["cases"]:
        lines.extend(
            [
                f"## {row['id']} — {row['category']}",
                "",
                f"**Question:** {row['question']}",
                "",
            ]
        )
        if row["history"]:
            lines.extend(["### History", ""])
            for message in row["history"]:
                lines.append(f"- **{message['role'].capitalize()}:** {message['content']}")
            lines.append("")
        if row["status"] == "error":
            lines.extend([f"**Error:** {row['error']}", "", "---", ""])
            continue
        lines.extend(
            [
                f"**Standalone retrieval query:** {row['standalone_retrieval_query']}",
                "",
                "### Retrieved Top5 evidence",
                "",
            ]
        )
        for source in row["evidence"]:
            heading = " > ".join(source["heading_path"]) or "Document introduction"
            lines.append(
                f"- [{source['citation_id']}] `{source['title']}` — {heading} "
                f"(`{source['source_path']}`)"
            )
        generation = row["generation"]
        validation = generation["validation"]
        lines.extend(
            [
                "",
                "### Generated answer",
                "",
                generation["answer"],
                "",
                f"**Citation IDs:** {', '.join(generation['citation_ids']) or '(none)'}",
                "",
                "### Rendered sources",
                "",
            ]
        )
        if generation["sources"]:
            for source in generation["sources"]:
                heading = " > ".join(source["heading_path"]) or "Document introduction"
                lines.extend(
                    [
                        f"- [{source['citation_id']}] **{source['title']}**",
                        f"  - Section: {heading}",
                        f"  - URL: {source['source_url']}",
                        f"  - Path: `{source['source_path']}`",
                        f"  - Chunk: `{source['chunk_id']}`",
                    ]
                )
        else:
            lines.append("- None.")
        lines.extend(
            [
                "",
                "### Citation validation",
                "",
                f"- Valid: `{validation['valid']}`",
                f"- Has citations: `{validation['has_citations']}`",
                f"- Invalid citations: `{validation['invalid_citations']}`",
                f"- Model-generated URL: `{validation['contains_model_generated_url']}`",
                f"- Warnings: `{validation['warnings']}`",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


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
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "generation_manual_review.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=project_root / "eval" / "results" / "generation_manual_review.md",
    )
    args = parser.parse_args(argv)

    config = LLMConfig.from_env(args.env_file)
    client = OpenAIChatCompletionsClient(config)
    dataset = json.loads(args.candidates.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in dataset}
    cases = [by_id[case_id] for case_id in MANUAL_CASE_IDS]
    retriever, _ = _load_frozen_retriever(project_root, args.device)
    rows, usage = inspect_cases(
        cases,
        retriever,
        client,
        model=config.model,
        rewrite_cache=RewriteCache(project_root / "cache" / "query_rewrites.json"),
        generation_cache=GeneratedAnswerCache(
            project_root / "cache" / "generated_answers.json"
        ),
    )
    report = {
        "configuration": {
            "provider": "openai-compatible-chat-completions",
            "base_url": config.base_url,
            "model": config.model,
            "thinking_mode": config.thinking_mode,
            "temperature": 0.0,
            "generation_max_tokens": 512,
            "generation_prompt_version": GENERATION_PROMPT_VERSION,
            "max_history_turns": DEFAULT_HISTORY_TURNS,
            "retrieval_pipeline": "lexical Top20 + semantic Top20 union, Cross-Encoder reranker Top5",
            "candidate_dataset_sha256": _sha256(args.candidates),
            "manual_case_ids": list(MANUAL_CASE_IDS),
        },
        "usage": usage,
        "cases": rows,
    }
    _write_atomic(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    _write_atomic(args.markdown_output, render_review(report))
    print(
        f"Cases={len(rows)} errors={usage['errors']} rewrite_api={usage['rewrite_api_calls']} "
        f"rewrite_cache={usage['rewrite_cache_hits']} generation_api={usage['generation_api_calls']} "
        f"generation_cache={usage['generation_cache_hits']}"
    )
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Markdown: {args.markdown_output.resolve()}")
    return 1 if usage["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
