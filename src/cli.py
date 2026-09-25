"""Minimal terminal chat interface for the GitHub policy support agent."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .agent import AgentPipelineError, AgentResult, PolicySupportAgent


EXIT_COMMANDS = {"exit", "quit"}

ASSISTANT_LABEL = "Assistant"
SEPARATOR = "─" * 40


def format_citations(citations: Sequence[Mapping[str, Any]]) -> str:
    """Render only the structured citation metadata returned by the agent."""

    lines = ["Sources:"]
    for citation in citations:
        citation_id = str(citation.get("citation_id", "source"))
        title = str(citation.get("title", "Untitled source"))
        heading_path = citation.get("heading_path", [])
        if isinstance(heading_path, Sequence) and not isinstance(
            heading_path, (str, bytes)
        ):
            heading = " > ".join(str(value) for value in heading_path)
        else:
            heading = str(heading_path)
        label = f"- [{citation_id}] {title}"
        if heading:
            label += f" — {heading}"
        lines.append(label)
        location = citation.get("source_url") or citation.get("source_path")
        if location:
            lines.append(f"  {location}")
    return "\n".join(lines)


def format_debug(result: AgentResult) -> str:
    """Render opt-in pipeline details without changing the answer path."""

    lines = [
        "Debug:",
        f"- Rewritten query: {result.rewritten_query}",
        f"- Rewrite source: {result.rewrite_response_source}",
        f"- Generation source: {result.generation_response_source}",
        f"- Evidence budget: {result.trace.to_dict()['evidence_budget'] if result.trace else None}",
        "- Reranked evidence:",
    ]
    for rank, item in enumerate(result.evidence, start=1):
        heading = " > ".join(item.heading_path) or "(document introduction)"
        lines.append(
            f"  {rank}. score={item.reranker_score:.4f} | "
            f"{item.title} | {heading} | {item.source_path}"
        )
    return "\n".join(lines)


def render_assistant_answer(
    answer: str,
    *,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Print the model answer between fixed visual boundaries.

    The boundaries are presentation-only: the answer string is written
    verbatim and never altered or echoed back into conversation history.
    """

    output_fn("")
    output_fn(ASSISTANT_LABEL)
    output_fn(SEPARATOR)
    output_fn(answer)
    output_fn(SEPARATOR)


def run_chat(
    agent: PolicySupportAgent,
    *,
    debug: bool = False,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    """Run an in-process conversation and retain only successful turns."""

    history: list[dict[str, str]] = []
    output_fn("GitHub Policy Support Agent")
    output_fn("Type 'exit' or 'quit' to leave.")

    while True:
        try:
            raw_question = input_fn("You > ")
        except (EOFError, KeyboardInterrupt):
            output_fn("\nGoodbye.")
            return 0

        question = raw_question.strip()
        if not question:
            continue
        if question.casefold() in EXIT_COMMANDS:
            output_fn("Goodbye.")
            return 0

        try:
            result = agent.answer(question, history)
        except AgentPipelineError as error:
            output_fn(f"Error [{error.stage}]: {error}")
            continue
        except KeyboardInterrupt:
            output_fn("\nGoodbye.")
            return 0

        if debug:
            output_fn(format_debug(result))

        render_assistant_answer(result.answer, output_fn=output_fn)
        output_fn(format_citations(result.citations))

        history.extend(
            (
                {"role": "user", "content": question},
                {"role": "assistant", "content": result.answer},
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show rewritten query, reranked evidence, and cache sources",
    )
    parser.add_argument(
        "--adaptive-evidence",
        action="store_true",
        help="select a bounded adaptive evidence prefix from the existing reranked Top20",
    )
    parser.add_argument("--evidence-mode", choices=("fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2"),
                        help="evidence selection mode; --adaptive-evidence is an alias for adaptive_prefix_v1")
    args = parser.parse_args(argv)

    if args.adaptive_evidence and args.evidence_mode not in (None, "adaptive_prefix_v1"):
        parser.error("--adaptive-evidence requires adaptive_prefix_v1 when --evidence-mode is set")

    try:
        options = {"device": "cpu"}
        if args.adaptive_evidence:
            options["adaptive_evidence"] = True
        if args.evidence_mode:
            options["evidence_mode"] = args.evidence_mode
        agent = PolicySupportAgent.from_project(**options)
    except KeyboardInterrupt:
        print("\nInitialization cancelled.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Failed to initialize policy agent: {error}", file=sys.stderr)
        return 1

    return run_chat(agent, debug=args.debug)


if __name__ == "__main__":
    raise SystemExit(main())
