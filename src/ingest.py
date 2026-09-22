"""Load whole policy documents from a local clone of github/site-policy.

This module intentionally does not chunk documents, generate embeddings, or
prepare a retrieval index. Each returned ``PolicyDocument`` corresponds to one
source Markdown file.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import quote


DEFAULT_REPOSITORY_URL = "https://github.com/github/site-policy"
DEFAULT_BRANCH = "main"
POLICY_DIRECTORY = "Policies"

_FRONT_MATTER_BOUNDARY = "---"
_TITLE_PATTERN = re.compile(r"^title:\s*(.*?)\s*$", re.MULTILINE)
_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Heading:
    """A Markdown heading found in a policy document."""

    level: int
    text: str


@dataclass(frozen=True, slots=True)
class PolicyDocument:
    """One unchunked policy source file and its useful source metadata."""

    source_path: str
    title: str
    headings: tuple[Heading, ...]
    source_url: str
    text: str


def discover_policy_files(policy_repository: Path | str) -> list[Path]:
    """Return policy Markdown files in stable source-relative path order.

    Only files below the upstream ``Policies`` directory are included. Root
    repository documents such as README, CONTRIBUTING, and LICENSE describe the
    repository itself and are not policy-agent sources.
    """

    repository = Path(policy_repository).expanduser().resolve()
    policies_root = repository / POLICY_DIRECTORY

    if not policies_root.is_dir():
        raise FileNotFoundError(
            f"Expected a github/site-policy clone with a Policies directory at: "
            f"{policies_root}"
        )

    return sorted(
        (path for path in policies_root.rglob("*.md") if path.is_file()),
        key=lambda path: path.relative_to(repository).as_posix().casefold(),
    )


def load_policy_documents(
    policy_repository: Path | str,
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    branch: str = DEFAULT_BRANCH,
) -> list[PolicyDocument]:
    """Load each discovered Markdown policy as one ``PolicyDocument``.

    Front matter is removed from ``text`` because it is publishing metadata,
    while its title is retained separately. Documents are not split or altered
    further.
    """

    repository = Path(policy_repository).expanduser().resolve()
    documents = [
        _load_policy_file(path, repository, repository_url, branch)
        for path in discover_policy_files(repository)
    ]

    if not documents:
        raise ValueError(f"No Markdown policy files found below {repository / POLICY_DIRECTORY}")

    return documents


def _load_policy_file(
    path: Path,
    repository: Path,
    repository_url: str,
    branch: str,
) -> PolicyDocument:
    raw_text = path.read_text(encoding="utf-8-sig")
    front_matter, text = _split_front_matter(raw_text)
    source_path = path.relative_to(repository).as_posix()
    title = _extract_title(front_matter) or _first_heading_text(text) or _title_from_filename(path)
    headings = tuple(_extract_headings(text))
    encoded_path = quote(source_path, safe="/")
    source_url = f"{repository_url.rstrip('/')}/blob/{quote(branch, safe='')}/{encoded_path}"

    return PolicyDocument(
        source_path=source_path,
        title=title,
        headings=headings,
        source_url=source_url,
        text=text,
    )


def _split_front_matter(raw_text: str) -> tuple[str, str]:
    lines = raw_text.splitlines(keepends=True)
    if not lines or lines[0].strip() != _FRONT_MATTER_BOUNDARY:
        return "", raw_text

    for index in range(1, len(lines)):
        if lines[index].strip() == _FRONT_MATTER_BOUNDARY:
            front_matter = "".join(lines[1:index])
            document_text = "".join(lines[index + 1 :]).lstrip("\r\n")
            return front_matter, document_text

    # An opening marker without a closing marker is treated as ordinary text.
    return "", raw_text


def _extract_title(front_matter: str) -> str | None:
    match = _TITLE_PATTERN.search(front_matter)
    if not match:
        return None

    title = match.group(1).strip()
    if len(title) >= 2 and title[0] == title[-1] and title[0] in {'"', "'"}:
        title = title[1:-1].strip()
    return title or None


def _extract_headings(text: str) -> Iterable[Heading]:
    for match in _HEADING_PATTERN.finditer(text):
        yield Heading(level=len(match.group(1)), text=match.group(2).strip())


def _first_heading_text(text: str) -> str | None:
    return next((heading.text for heading in _extract_headings(text)), None)


def _title_from_filename(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def _snippet(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 1].rstrip()}…"


def _print_summary(documents: Sequence[PolicyDocument], sample_count: int) -> None:
    print(f"Loaded {len(documents)} policy documents.")
    for index, document in enumerate(documents[:sample_count], start=1):
        print(f"\nSample {index}: {document.title}")
        print(f"Path: {document.source_path}")
        print(f"URL: {document.source_url}")
        print(f"Headings: {len(document.headings)}")
        print(f"Text: {_snippet(document.text)}")


def main(argv: Sequence[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=project_root / "data" / "site-policy",
        help="path to a local github/site-policy clone",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=3,
        help="number of loaded documents to display (default: 3)",
    )
    args = parser.parse_args(argv)

    if args.sample_count < 0:
        parser.error("--sample-count must be zero or greater")

    _print_summary(load_policy_documents(args.repository), args.sample_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

