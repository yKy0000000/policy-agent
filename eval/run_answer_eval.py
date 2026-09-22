"""Run deterministic answer checks and produce a claim-level human review sheet."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from eval.evaluate_multiturn_strategies import _load_frozen_retriever
from src.conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    RewriteCache,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from src.generator import GeneratedAnswerCache, generate_grounded_answer
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient


CATEGORIES = ("direct", "specific", "semantic", "broad", "multi_turn", "unsupported")
_ABSTENTION_PATTERNS = (
    re.compile(
        r"\b(?:the\s+)?provided(?:\s+published|\s+github)?\s+policies\s+"
        r"(?:do|does)\s+not\s+(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?published\s+policies\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?(?:provided\s+)?evidence\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?provided\s+sources\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:this|the requested)\s+information\s+is\s+not\s+specified\s+"
        r"in\s+the\s+provided\s+policies\b",
        re.IGNORECASE,
    ),
)


def detect_behavior(answer: str) -> str:
    """Conservatively classify an explicit evidence-based abstention."""

    if not answer.strip():
        return "empty"
    if any(pattern.search(answer) for pattern in _ABSTENTION_PATTERNS):
        return "abstain"
    return "answer"


def behavior_passes(expected_behavior: str, answer: str) -> bool:
    detected = detect_behavior(answer)
    if expected_behavior == "abstain":
        return detected == "abstain"
    if expected_behavior == "answer":
        return detected == "answer"
    raise ValueError(f"unsupported expected behavior: {expected_behavior}")


def normalize_for_matching(text: str) -> str:
    """Normalize case, whitespace, and punctuation for conservative phrase matching."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in normalized
    )
    return " ".join(normalized.split())


def find_forbidden_claims(answer: str, forbidden_claims: Sequence[str]) -> list[str]:
    normalized_answer = normalize_for_matching(answer)
    return [
        claim
        for claim in forbidden_claims
        if normalize_for_matching(claim) in normalized_answer
    ]


def acceptable_source_matches(
    cited_sources: Sequence[Mapping[str, Any]],
    acceptable_sources: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether at least one cited source satisfies an acceptable-source rule."""

    for cited in cited_sources:
        for acceptable in acceptable_sources:
            if cited.get("source_path") != acceptable.get("source_path"):
                continue
            heading_contains = str(acceptable.get("heading_contains", "")).strip()
            if not heading_contains:
                return True
            heading_path = " > ".join(str(value) for value in cited.get("heading_path", []))
            if heading_contains.casefold() in heading_path.casefold():
                return True
    return False


def aggregate_deterministic_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate completed cases while reporting technical errors separately."""

    completed = [row for row in rows if row["pipeline"]["status"] == "completed"]
    errors = [row for row in rows if row["pipeline"]["status"] == "error"]
    answer_rows = [row for row in completed if row["expected_behavior"] == "answer"]
    abstain_rows = [row for row in completed if row["expected_behavior"] == "abstain"]

    def rate(group: Sequence[Mapping[str, Any]], field: str) -> float | None:
        return (
            sum(bool(row["deterministic_checks"][field]) for row in group) / len(group)
            if group
            else None
        )

    forbidden_count = sum(
        len(row["deterministic_checks"]["forbidden_claim_matches"])
        for row in completed
    )
    cases_with_forbidden = sum(
        bool(row["deterministic_checks"]["forbidden_claim_matches"])
        for row in completed
    )
    return {
        "total_cases": len(rows),
        "completed_cases": len(completed),
        "errored_cases": len(errors),
        "error_case_ids": [row["id"] for row in errors],
        "pipeline_success_rate": (
            sum(bool(row["pipeline"]["overall_pipeline_success"]) for row in rows)
            / len(rows)
            if rows
            else 0.0
        ),
        "behavior_accuracy": rate(completed, "behavior_pass"),
        "answer_behavior_accuracy": rate(answer_rows, "behavior_pass"),
        "abstention_accuracy": rate(abstain_rows, "behavior_pass"),
        "citation_validation_pass_rate": rate(completed, "citation_validation_pass"),
        "acceptable_source_hit_rate": rate(completed, "acceptable_source_hit"),
        "forbidden_claim_violation_count": forbidden_count,
        "cases_with_forbidden_claim_violation": cases_with_forbidden,
        "forbidden_claim_violation_rate": (
            cases_with_forbidden / len(completed) if completed else None
        ),
        "unsupported_abstention_accuracy": rate(abstain_rows, "behavior_pass"),
    }


def _get_rewritten_query(
    case: Mapping[str, Any],
    client: OpenAIChatCompletionsClient,
    cache: RewriteCache,
    model: str,
    usage: dict[str, int],
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
        usage["rewrite_cache_hits"] += 1
        return cached
    usage["rewrite_api_calls"] += 1
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


def run_answer_eval(
    cases: Sequence[Mapping[str, Any]],
    retriever: Any,
    client: OpenAIChatCompletionsClient,
    *,
    model: str,
    rewrite_cache: RewriteCache,
    generation_cache: GeneratedAnswerCache,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Run every case through the real pipeline and deterministic checks."""

    usage = {
        "rewrite_api_calls": 0,
        "rewrite_cache_hits": 0,
        "generation_api_calls": 0,
        "generation_cache_hits": 0,
        "errors": 0,
    }
    rows: list[dict[str, Any]] = []
    for case in cases:
        pipeline = {
            "status": "error",
            "rewrite_success": False,
            "retrieval_success": False,
            "generation_success": False,
            "citation_validation_success": False,
            "overall_pipeline_success": False,
            "error_stage": None,
            "error": None,
        }
        base = {
            "id": case["id"],
            "source_case_id": case["source_case_id"],
            "category": case["category"],
            "expected_behavior": case["expected_behavior"],
            "question": case["question"],
            "history": select_recent_history(list(case.get("history", []))),
            "required_points": list(case["required_points"]),
            "acceptable_sources": list(case["acceptable_sources"]),
            "forbidden_claims": list(case["forbidden_claims"]),
            "supporting_snippets": list(case["supporting_snippets"]),
            "notes": case["notes"],
        }
        try:
            rewritten = _get_rewritten_query(
                case, client, rewrite_cache, model, usage
            )
            pipeline["rewrite_success"] = True
        except Exception as error:
            pipeline.update(error_stage="rewrite", error=str(error))
            usage["errors"] += 1
            rows.append({**base, "rewritten_query": None, "pipeline": pipeline})
            continue

        try:
            evidence = retriever.search(rewritten, top_k=5)
            if not evidence:
                raise RuntimeError("retrieval returned no evidence")
            pipeline["retrieval_success"] = True
        except Exception as error:
            pipeline.update(error_stage="retrieval", error=str(error))
            usage["errors"] += 1
            rows.append({**base, "rewritten_query": rewritten, "pipeline": pipeline})
            continue

        evidence_summary = [
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
        ]
        try:
            generated = generate_grounded_answer(
                str(case["question"]),
                list(case.get("history", [])),
                evidence,
                client,
                model=model,
                cache=generation_cache,
            )
            if generated["response_source"] == "cache":
                usage["generation_cache_hits"] += 1
            else:
                usage["generation_api_calls"] += 1
            pipeline["generation_success"] = True
        except Exception as error:
            pipeline.update(error_stage="generation", error=str(error))
            usage["errors"] += 1
            rows.append(
                {
                    **base,
                    "rewritten_query": rewritten,
                    "retrieved_evidence": evidence_summary,
                    "pipeline": pipeline,
                }
            )
            continue

        validation = generated["validation"]
        citation_valid = bool(validation["valid"])
        pipeline.update(
            status="completed",
            citation_validation_success=citation_valid,
            overall_pipeline_success=(
                bool(pipeline["rewrite_success"])
                and bool(pipeline["retrieval_success"])
                and bool(pipeline["generation_success"])
                and citation_valid
            ),
        )
        answer = str(generated["answer"])
        detected_behavior = detect_behavior(answer)
        forbidden_matches = find_forbidden_claims(
            answer, list(case["forbidden_claims"])
        )
        source_hit = acceptable_source_matches(
            list(generated["sources"]), list(case["acceptable_sources"])
        )
        behavior_pass = behavior_passes(str(case["expected_behavior"]), answer)
        checks = {
            "detected_behavior": detected_behavior,
            "behavior_pass": behavior_pass,
            "citation_validation_pass": citation_valid,
            "acceptable_source_hit": source_hit,
            "forbidden_claim_matches": forbidden_matches,
            "forbidden_claim_pass": not forbidden_matches,
        }
        checks["all_deterministic_checks_pass"] = all(
            (
                checks["behavior_pass"],
                checks["citation_validation_pass"],
                checks["acceptable_source_hit"],
                checks["forbidden_claim_pass"],
            )
        )
        rows.append(
            {
                **base,
                "rewritten_query": rewritten,
                "retrieved_evidence": evidence_summary,
                "generated_answer": answer,
                "citation_ids": generated["citation_ids"],
                "sources": generated["sources"],
                "generator_validation": validation,
                "generation_response_source": generated["response_source"],
                "pipeline": pipeline,
                "deterministic_checks": checks,
            }
        )
    return rows, usage


def category_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["category"])].append(row)
    return {
        category: aggregate_deterministic_metrics(grouped.get(category, []))
        for category in CATEGORIES
    }


def render_summary(report: Mapping[str, Any]) -> str:
    metrics = report["summary"]["overall"]
    lines = [
        "# Answer eval deterministic summary",
        "",
        "Semantic correctness and claim-level citation entailment are intentionally not auto-scored.",
        "",
        "## Overall deterministic metrics",
        "",
        f"- Total cases: {metrics['total_cases']}",
        f"- Completed cases: {metrics['completed_cases']}",
        f"- Errored cases: {metrics['errored_cases']}",
        f"- Pipeline success rate: {_metric(metrics['pipeline_success_rate'])}",
        f"- Behavior accuracy: {_metric(metrics['behavior_accuracy'])}",
        f"- Answer-case behavior accuracy: {_metric(metrics['answer_behavior_accuracy'])}",
        f"- Abstention accuracy: {_metric(metrics['abstention_accuracy'])}",
        f"- Citation validation pass rate: {_metric(metrics['citation_validation_pass_rate'])}",
        f"- Acceptable source hit rate: {_metric(metrics['acceptable_source_hit_rate'])}",
        f"- Forbidden claim violations: {metrics['forbidden_claim_violation_count']}",
        f"- Forbidden claim violation rate: {_metric(metrics['forbidden_claim_violation_rate'])}",
        f"- Unsupported abstention accuracy: {_metric(metrics['unsupported_abstention_accuracy'])}",
        "",
        "## Metrics by category",
        "",
    ]
    for category in CATEGORIES:
        row = report["summary"]["by_category"][category]
        lines.extend(
            [
                f"### {category}",
                "",
                f"- Cases/completed/errors: {row['total_cases']}/{row['completed_cases']}/{row['errored_cases']}",
                f"- Pipeline success: {_metric(row['pipeline_success_rate'])}",
                f"- Behavior accuracy: {_metric(row['behavior_accuracy'])}",
                f"- Citation validation: {_metric(row['citation_validation_pass_rate'])}",
                f"- Acceptable source hit: {_metric(row['acceptable_source_hit_rate'])}",
                f"- Forbidden claim violation rate: {_metric(row['forbidden_claim_violation_rate'])}",
                "",
            ]
        )
    failures = report["summary"]["deterministic_failures"]
    lines.extend(["## Failed deterministic checks", ""])
    if failures:
        for row in failures:
            lines.append(f"- `{row['id']}`: {', '.join(row['failed_checks'])}")
    else:
        lines.append("None.")
    lines.extend(["", "## Unsupported cases", ""])
    for row in report["cases"]:
        if row["category"] == "unsupported":
            checks = row.get("deterministic_checks", {})
            lines.append(
                f"- `{row['id']}`: detected={checks.get('detected_behavior')}, "
                f"behavior_pass={checks.get('behavior_pass')}, "
                f"forbidden_matches={checks.get('forbidden_claim_matches')}"
            )
    usage = report["usage"]
    lines.extend(
        [
            "",
            "## API and cache usage",
            "",
            f"- Rewrite API calls/cache hits: {usage['rewrite_api_calls']}/{usage['rewrite_cache_hits']}",
            f"- Generation API calls/cache hits: {usage['generation_api_calls']}/{usage['generation_cache_hits']}",
            f"- Errors: {usage['errors']}",
            "",
            "## Methodology and limitations",
            "",
            "- Behavior detection requires an explicit evidence/policy insufficiency marker; vague uncertainty such as 'I am not sure' is not counted as abstention.",
            "- Forbidden claims use normalized exact-phrase matching. Semantically equivalent paraphrases may not be detected.",
            "- Acceptable-source checks validate cited metadata, not whether the source entails the adjacent claim.",
            "- Required-point coverage, semantic correctness, claim-level grounding, citation entailment, and overclaiming remain human-review tasks.",
            "- No LLM judge or automated semantic score is used.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_human_review(report: Mapping[str, Any]) -> str:
    lines = [
        "# Answer eval human review",
        "",
        "Semantic fields below are intentionally left unchecked for human reviewers.",
        "",
    ]
    for row in report["cases"]:
        lines.extend([f"## {row['id']} — {row['category']}", ""])
        if row["category"] == "broad":
            lines.extend(
                [
                    "> **BROAD CASE REVIEW NOTE:** Check whether the answer limits itself to supported major circumstances, avoids claiming an exhaustive list, and gives enough qualification to prevent an exhaustive reading.",
                    "",
                ]
            )
        if row["category"] == "unsupported":
            lines.extend(
                [
                    "> **UNSUPPORTED CASE:** Check that related policy context was not converted into an unsupported percentage, physical location, or decision deadline.",
                    "",
                ]
            )
        lines.extend(
            [
                f"- **Source case:** `{row['source_case_id']}`",
                f"- **Expected behavior:** `{row['expected_behavior']}`",
                f"- **Question:** {row['question']}",
            ]
        )
        if row["history"]:
            lines.extend(["- **Original history:**", ""])
            for message in row["history"]:
                lines.append(f"  - **{message['role'].capitalize()}:** {message['content']}")
        lines.extend(
            [
                f"- **LLM rewritten query:** {row.get('rewritten_query') or '(unavailable)'}",
                "",
                "### Retrieved Top5 evidence",
                "",
            ]
        )
        for evidence in row.get("retrieved_evidence", []):
            heading = " > ".join(evidence["heading_path"]) or "Document introduction"
            lines.append(
                f"- [{evidence['citation_id']}] **{evidence['title']}** — {heading} — "
                f"`{evidence['source_path']}`"
            )
        lines.extend(["", "### Generated answer", ""])
        lines.append(row.get("generated_answer") or f"(pipeline error: {row['pipeline'].get('error')})")
        lines.extend(["", "### Inline citations and actual cited sources", ""])
        lines.append(
            f"- Citation IDs: {', '.join(row.get('citation_ids', [])) or '(none)'}"
        )
        for source in row.get("sources", []):
            heading = " > ".join(source["heading_path"]) or "Document introduction"
            lines.append(
                f"- [{source['citation_id']}] **{source['title']}** — {heading} — "
                f"`{source['source_path']}` — {source['source_url']}"
            )
        lines.extend(["", "### Required points", ""])
        for point in row["required_points"]:
            lines.extend(
                [
                    f"- {point}",
                    "  - [ ] covered",
                    "  - [ ] partially covered",
                    "  - [ ] missing",
                ]
            )
        lines.extend(["", "### Supporting snippets", ""])
        for snippet in row["supporting_snippets"]:
            lines.extend(["> " + line if line else ">" for line in snippet.splitlines()])
            lines.append("")
        lines.extend(["### Forbidden claims", ""])
        if row["forbidden_claims"]:
            lines.extend(f"- {claim}" for claim in row["forbidden_claims"])
        else:
            lines.append("- None specified.")
        checks = row.get("deterministic_checks", {})
        validation = row.get("generator_validation", {})
        lines.extend(
            [
                "",
                "### Deterministic checks",
                "",
                f"- Pipeline: `{row['pipeline']}`",
                f"- Detected behavior: `{checks.get('detected_behavior')}`",
                f"- Behavior pass: `{checks.get('behavior_pass')}`",
                f"- Citation validation pass: `{checks.get('citation_validation_pass')}`",
                f"- Invalid citations: `{validation.get('invalid_citations')}`",
                f"- Missing citations: `{'missing_citations' in validation.get('warnings', [])}`",
                f"- Model-generated URL: `{validation.get('contains_model_generated_url')}`",
                f"- Acceptable source hit: `{checks.get('acceptable_source_hit')}`",
                f"- Forbidden claim matches: `{checks.get('forbidden_claim_matches')}`",
                "",
                "### Human Review",
                "",
                "**Claim-level grounding:**",
                "- [ ] pass",
                "- [ ] partial",
                "- [ ] fail",
                "",
                "**Citation entailment:**",
                "- [ ] pass",
                "- [ ] partial",
                "- [ ] fail",
                "",
                "**Overclaim / unsupported inference:**",
                "- [ ] none",
                "- [ ] present",
                "",
                "**Reviewer notes:**",
                "",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _metric(value: Any) -> str:
    return "N/A" if value is None else f"{float(value):.4f}"


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
        "--cases",
        type=Path,
        default=project_root / "eval" / "answer_eval_candidates.json",
    )
    parser.add_argument("--env-file", type=Path, default=project_root / ".env")
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_results.json",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_summary.md",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_human_review.md",
    )
    args = parser.parse_args(argv)

    config = LLMConfig.from_env(args.env_file)
    client = OpenAIChatCompletionsClient(config)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("answer eval cases must be a JSON array")
    retriever, _ = _load_frozen_retriever(project_root, args.device)
    rows, usage = run_answer_eval(
        cases,
        retriever,
        client,
        model=config.model,
        rewrite_cache=RewriteCache(project_root / "cache" / "query_rewrites.json"),
        generation_cache=GeneratedAnswerCache(
            project_root / "cache" / "generated_answers.json"
        ),
    )
    overall = aggregate_deterministic_metrics(rows)
    by_category = category_metrics(rows)
    failures = []
    for row in rows:
        if row["pipeline"]["status"] == "error":
            failures.append({"id": row["id"], "failed_checks": ["pipeline_error"]})
            continue
        checks = row["deterministic_checks"]
        failed = [
            name
            for name, passed in (
                ("behavior", checks["behavior_pass"]),
                ("citation_validation", checks["citation_validation_pass"]),
                ("acceptable_source", checks["acceptable_source_hit"]),
                ("forbidden_claim", checks["forbidden_claim_pass"]),
            )
            if not passed
        ]
        if failed:
            failures.append({"id": row["id"], "failed_checks": failed})
    report = {
        "configuration": {
            "provider": "openai-compatible-chat-completions",
            "base_url": config.base_url,
            "model": config.model,
            "thinking_mode": config.thinking_mode,
            "candidate_dataset": args.cases.as_posix(),
            "candidate_dataset_sha256": _sha256(args.cases),
            "retrieval_pipeline": "lexical Top20 + semantic Top20 union, Cross-Encoder reranker Top5",
            "automatic_semantic_scoring": False,
            "llm_judge": False,
        },
        "usage": usage,
        "summary": {
            "overall": overall,
            "by_category": by_category,
            "deterministic_failures": failures,
        },
        "cases": rows,
    }
    _write_atomic(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    _write_atomic(args.summary_output, render_summary(report))
    _write_atomic(args.review_output, render_human_review(report))
    print(json.dumps(overall, ensure_ascii=False, indent=2))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Summary: {args.summary_output.resolve()}")
    print(f"Human review: {args.review_output.resolve()}")
    return 1 if usage["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
