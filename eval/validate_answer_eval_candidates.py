"""Validate and render the human review sheet for answer-eval candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ingest import PolicyDocument, load_policy_documents


ALLOWED_BEHAVIORS = {"answer", "abstain"}


def validate_candidates(
    candidates: Sequence[Mapping[str, Any]],
    retrieval_cases: Sequence[Mapping[str, Any]],
    documents: Sequence[PolicyDocument],
) -> dict[str, Any]:
    """Raise on invalid candidate data and return a compact validation summary."""

    errors: list[str] = []
    ids = [str(case.get("id", "")) for case in candidates]
    duplicate_ids = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate case IDs: {', '.join(duplicate_ids)}")

    retrieval_by_id = {str(case["id"]): case for case in retrieval_cases}
    documents_by_path = {document.source_path: document for document in documents}
    validated_snippets = 0
    validated_sources = 0

    for case in candidates:
        case_id = str(case.get("id", "(missing id)"))
        source_case_id = str(case.get("source_case_id", ""))
        source_case = retrieval_by_id.get(source_case_id)
        if source_case is None:
            errors.append(f"{case_id}: source_case_id {source_case_id!r} does not exist")
            continue
        if str(case.get("question", "")) != str(source_case.get("question", "")):
            errors.append(f"{case_id}: question differs from source retrieval case")

        behavior = case.get("expected_behavior")
        if behavior not in ALLOWED_BEHAVIORS:
            errors.append(f"{case_id}: invalid expected_behavior {behavior!r}")
        source_is_unsupported = source_case.get("category") == "unsupported"
        expected_behavior = "abstain" if source_is_unsupported else "answer"
        if behavior != expected_behavior:
            errors.append(
                f"{case_id}: {source_case.get('category')} source case must use {expected_behavior!r}"
            )
        if source_case.get("category") == "multi_turn":
            if case.get("history") != source_case.get("history"):
                errors.append(f"{case_id}: multi-turn history differs from source case")
        elif case.get("history") not in ([], None):
            errors.append(f"{case_id}: non-multi-turn case must have empty history")

        required_points = case.get("required_points")
        if not isinstance(required_points, list) or not (1 <= len(required_points) <= 3):
            errors.append(f"{case_id}: required_points must contain 1-3 items")

        acceptable_sources = case.get("acceptable_sources")
        if not isinstance(acceptable_sources, list) or not acceptable_sources:
            errors.append(f"{case_id}: acceptable_sources must not be empty")
            continue
        acceptable_documents: list[PolicyDocument] = []
        for source in acceptable_sources:
            source_path = str(source.get("source_path", ""))
            document = documents_by_path.get(source_path)
            if document is None:
                errors.append(f"{case_id}: source path does not exist: {source_path}")
                continue
            acceptable_documents.append(document)
            validated_sources += 1
            if str(source.get("title", "")) != document.title:
                errors.append(
                    f"{case_id}: source title does not match corpus for {source_path}"
                )
            heading_contains = str(source.get("heading_contains", "")).strip()
            if heading_contains and not any(
                heading_contains.casefold() in heading.text.casefold()
                for heading in document.headings
            ):
                errors.append(
                    f"{case_id}: heading {heading_contains!r} not found in {source_path}"
                )

        snippets = case.get("supporting_snippets")
        if not isinstance(snippets, list) or not snippets:
            errors.append(f"{case_id}: supporting_snippets must not be empty")
        else:
            for snippet in snippets:
                if not isinstance(snippet, str) or not snippet:
                    errors.append(f"{case_id}: supporting snippet must be non-empty text")
                elif not any(snippet in document.text for document in acceptable_documents):
                    errors.append(
                        f"{case_id}: supporting snippet is not verbatim in an acceptable source"
                    )
                else:
                    validated_snippets += 1

        if not isinstance(case.get("forbidden_claims"), list):
            errors.append(f"{case_id}: forbidden_claims must be a list")
        if not str(case.get("notes", "")).strip():
            errors.append(f"{case_id}: notes must not be blank")

    if errors:
        raise ValueError("Answer-eval candidate validation failed:\n- " + "\n- ".join(errors))

    return {
        "case_count": len(candidates),
        "unique_case_ids": len(set(ids)),
        "validated_source_references": validated_sources,
        "validated_verbatim_snippets": validated_snippets,
        "category_distribution": dict(
            sorted(Counter(str(case["category"]) for case in candidates).items())
        ),
        "behavior_distribution": dict(
            sorted(Counter(str(case["expected_behavior"]) for case in candidates).items())
        ),
        "status": "passed",
    }


def render_review(candidates: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# Answer eval candidate review",
        "",
        "Candidate data only. No answer generation or automatic scoring was run.",
        "",
    ]
    for case in candidates:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- **Source case:** `{case['source_case_id']}`",
                f"- **Category:** `{case['category']}`",
                f"- **Question:** {case['question']}",
            ]
        )
        history = case.get("history", [])
        if history:
            lines.extend(["- **History:**", ""])
            for message in history:
                lines.append(f"  - **{message['role'].capitalize()}:** {message['content']}")
            if case.get("reference_query"):
                lines.append(
                    f"- **Reference query (not user input):** {case['reference_query']}"
                )
        lines.extend(
            [
                f"- **Expected behavior:** `{case['expected_behavior']}`",
                "",
                "### Required points",
                "",
            ]
        )
        lines.extend(f"- {point}" for point in case["required_points"])
        lines.extend(["", "### Acceptable sources", ""])
        for source in case["acceptable_sources"]:
            heading = source.get("heading_contains") or "(path only)"
            lines.append(
                f"- **{source['title']}** — `{source['source_path']}` — heading contains `{heading}`"
            )
        lines.extend(["", "### Forbidden claims", ""])
        if case["forbidden_claims"]:
            lines.extend(f"- {claim}" for claim in case["forbidden_claims"])
        else:
            lines.append("- None specified.")
        lines.extend(["", "### Supporting snippets", ""])
        for snippet in case["supporting_snippets"]:
            lines.extend(["> " + line if line else ">" for line in snippet.splitlines()])
            lines.append("")
        lines.extend(["### Notes", "", str(case["notes"]), "", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


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
        default=project_root / "eval" / "answer_eval_candidates.json",
    )
    parser.add_argument(
        "--retrieval-candidates",
        type=Path,
        default=project_root / "eval" / "retrieval_candidates.json",
    )
    parser.add_argument(
        "--policy-repository",
        type=Path,
        default=project_root / "data" / "site-policy",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=project_root / "eval" / "answer_eval_candidates_review.md",
    )
    args = parser.parse_args(argv)

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    retrieval_cases = json.loads(args.retrieval_candidates.read_text(encoding="utf-8"))
    if not isinstance(candidates, list) or not isinstance(retrieval_cases, list):
        raise ValueError("candidate files must contain JSON arrays")
    documents = load_policy_documents(args.policy_repository)
    summary = validate_candidates(candidates, retrieval_cases, documents)
    _write_atomic(args.review_output, render_review(candidates))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Review: {args.review_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
