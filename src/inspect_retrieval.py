"""Print inspectable retrieval results without generating answers."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .retriever import PolicyRetriever


EXAMPLE_QUERIES = (
    "When can GitHub suspend an account?",
    "Can a user appeal a GitHub account suspension?",
    "What does GitHub prohibit regarding malware?",
    "What information does GitHub collect about users?",
)


def _preview(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 1].rstrip()}…"


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        type=Path,
        default=project_root / "cache" / "policy_index.json",
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="query to inspect; repeat for more than one (defaults to four examples)",
    )
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(argv)

    retriever = PolicyRetriever.from_index(args.index)
    for query in args.queries or EXAMPLE_QUERIES:
        print(f"\nQUERY: {query}")
        for rank, result in enumerate(retriever.search(query, args.top_k), start=1):
            heading = " > ".join(result.heading_path) or "(document introduction)"
            print(f"{rank}. score={result.score:.4f} | {result.title}")
            print(f"   heading: {heading}")
            print(f"   source: {result.source_url}")
            print(f"   preview: {_preview(result.text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

