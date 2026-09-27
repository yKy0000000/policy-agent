"""Minimal terminal chat interface for the GitHub policy support agent."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .agent import AgentPipelineError, AgentResult, PolicySupportAgent
from .response_modes import AdaptiveModeAdapter, SearchPlusResult


EXIT_COMMANDS = {"exit", "quit"}
FAST = "fast"
SEARCH_PLUS = "search+"

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


def format_debug(result: AgentResult, *, mode: str = FAST, fallback_reason: str | None = None) -> str:
    """Render opt-in pipeline details without changing the answer path."""

    lines = [
        "Debug:",
        f"- Mode: {'Fast' if mode == FAST else 'Search+'} | Retrieval streams: 1 | Evidence used: {len(result.evidence)}",
        f"- Backend: {'Direct' if mode == FAST or fallback_reason else 'Adaptive'}",
        f"- Rewritten query: {result.rewritten_query}",
        f"- Rewrite source: {result.rewrite_response_source}",
        f"- Generation source: {result.generation_response_source}",
        f"- Evidence budget: {result.trace.to_dict()['evidence_budget'] if result.trace else None}",
        "- Reranked evidence:",
    ]
    if fallback_reason:
        lines.insert(3, f"- Fallback reason: {fallback_reason}")
    for rank, item in enumerate(result.evidence, start=1):
        heading = " > ".join(item.heading_path) or "(document introduction)"
        lines.append(
            f"  {rank}. score={item.reranker_score:.4f} | "
            f"{item.title} | {heading} | {item.source_path}"
        )
    return "\n".join(lines)


def choose_mode(
    *,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> str:
    output_fn("Response mode:")
    output_fn("  [f] Fast     Standard retrieval, lower compute")
    output_fn("  [s] Search+  Higher-budget retrieval, prioritizes completeness")
    output_fn("Press Enter for Fast.")
    while True:
        choice = input_fn("Mode [f]: ").strip().casefold()
        if choice in ("", "f"):
            return FAST
        if choice == "s":
            return SEARCH_PLUS
        output_fn("Choose f or s, or press Enter for Fast.")


def show_mode(mode: str, output_fn: Callable[[str], None]) -> None:
    output_fn(f"Current mode: {mode.upper()}")
    output_fn("  [f] Fast")
    output_fn("  [s] Search+")


def show_help(output_fn: Callable[[str], None]) -> None:
    output_fn("Commands: /f Fast | /s Search+ | /mode current mode | /help | /exit")
    output_fn("You can also type exit or quit to leave.")


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
    search_adapter: AdaptiveModeAdapter | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    """Run an in-process conversation and retain only successful turns."""

    history: list[dict[str, str]] = []
    output_fn("GitHub Policy Support Agent")
    try:
        mode = choose_mode(input_fn=input_fn, output_fn=output_fn)
    except (EOFError, KeyboardInterrupt):
        output_fn("\nGoodbye.")
        return 0
    output_fn("Type /help for commands.")

    while True:
        try:
            raw_question = input_fn(f"[{mode.upper()}] > ")
        except (EOFError, KeyboardInterrupt):
            output_fn("\nGoodbye.")
            return 0

        question = raw_question.strip()
        if not question:
            continue
        command = question.casefold()
        if command in EXIT_COMMANDS or command == "/exit":
            output_fn("Goodbye.")
            return 0
        if command == "/f":
            mode = FAST
            output_fn("Mode switched to FAST.")
            continue
        if command == "/s":
            mode = SEARCH_PLUS
            output_fn("Mode switched to SEARCH+.")
            continue
        if command == "/mode":
            show_mode(mode, output_fn)
            continue
        if command == "/help":
            show_help(output_fn)
            continue

        try:
            if mode == FAST:
                result = agent.answer(question, history)
            else:
                if search_adapter is None:
                    search_adapter = AdaptiveModeAdapter(agent)
                result = search_adapter.answer(question, history)
        except AgentPipelineError as error:
            if mode == SEARCH_PLUS:
                output_fn(f"Error [{error.stage}]: Search+ request failed.")
                if debug:
                    output_fn(f"Debug: {error}")
            else:
                output_fn(f"Error [{error.stage}]: {error}")
            continue
        except KeyboardInterrupt:
            output_fn("\nGoodbye.")
            return 0

        fallback_reason = None
        if isinstance(result, SearchPlusResult):
            fallback_reason = result.fallback_reason
            result = result.result
        if fallback_reason:
            output_fn("Higher-budget retrieval unavailable; used Fast retrieval for this turn.")
        if debug:
            output_fn(format_debug(result, mode=mode, fallback_reason=fallback_reason))

        assert result.answer is not None
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
