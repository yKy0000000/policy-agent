"""Structure-aware chunking for loaded GitHub policy documents."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

from .ingest import PolicyDocument


DEFAULT_TARGET_SIZE = 3_200
DEFAULT_MAX_SIZE = 4_500
DEFAULT_OVERLAP = 400

_HEADING_LINE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*(?:\r?\n)?$")
_FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Approximate character limits used only after Markdown section splitting."""

    target_size: int = DEFAULT_TARGET_SIZE
    max_size: int = DEFAULT_MAX_SIZE
    overlap: int = DEFAULT_OVERLAP

    def __post_init__(self) -> None:
        if self.target_size <= 0:
            raise ValueError("target_size must be positive")
        if self.max_size < self.target_size:
            raise ValueError("max_size must be at least target_size")
        if not 0 <= self.overlap < self.target_size:
            raise ValueError("overlap must be non-negative and smaller than target_size")


@dataclass(frozen=True, slots=True)
class PolicyChunk:
    """One retrievable text unit with grounding metadata."""

    chunk_id: str
    text: str
    source_path: str
    source_url: str
    title: str
    heading_path: tuple[str, ...]
    chunk_index: int

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["heading_path"] = list(self.heading_path)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PolicyChunk":
        return cls(
            chunk_id=str(data["chunk_id"]),
            text=str(data["text"]),
            source_path=str(data["source_path"]),
            source_url=str(data["source_url"]),
            title=str(data["title"]),
            heading_path=tuple(str(item) for item in data["heading_path"]),  # type: ignore[arg-type]
            chunk_index=int(data["chunk_index"]),
        )


@dataclass(frozen=True, slots=True)
class _MarkdownSection:
    heading_path: tuple[str, ...]
    text: str


def chunk_documents(
    documents: Iterable[PolicyDocument],
    config: ChunkingConfig | None = None,
) -> list[PolicyChunk]:
    """Chunk documents by Markdown structure, then size only long sections."""

    chunking_config = config or ChunkingConfig()
    return [
        chunk
        for document in documents
        for chunk in chunk_document(document, chunking_config)
    ]


def chunk_document(
    document: PolicyDocument,
    config: ChunkingConfig | None = None,
) -> list[PolicyChunk]:
    """Create stable, document-local chunks from one loaded policy document."""

    chunking_config = config or ChunkingConfig()
    chunks: list[PolicyChunk] = []
    path_occurrences: defaultdict[tuple[str, ...], int] = defaultdict(int)

    for section in _split_markdown_sections(document.text):
        occurrence = path_occurrences[section.heading_path]
        path_occurrences[section.heading_path] += 1

        for part_index, text in enumerate(_split_long_section(section.text, chunking_config)):
            chunk_index = len(chunks)
            chunk_id = _stable_chunk_id(
                source_path=document.source_path,
                heading_path=section.heading_path,
                heading_occurrence=occurrence,
                part_index=part_index,
                text=text,
            )
            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    text=text,
                    source_path=document.source_path,
                    source_url=document.source_url,
                    title=document.title,
                    heading_path=section.heading_path,
                    chunk_index=chunk_index,
                )
            )

    return chunks


def build_embedding_text(chunk: PolicyChunk) -> str:
    """Add source context to text used for embedding without changing chunk text."""

    section = " > ".join(chunk.heading_path) if chunk.heading_path else "Document introduction"
    return f"Document: {chunk.title}\nSection: {section}\n\n{chunk.text}"


def _split_markdown_sections(text: str) -> list[_MarkdownSection]:
    sections: list[_MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []
    current_path: tuple[str, ...] = ()
    current_lines: list[str] = []
    active_fence: str | None = None

    def flush() -> None:
        section_text = "".join(current_lines).strip()
        if section_text and _has_retrievable_content(section_text, bool(current_path)):
            sections.append(_MarkdownSection(current_path, section_text))

    for line in text.splitlines(keepends=True):
        fence_match = _FENCE_LINE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            if active_fence is None:
                active_fence = marker
            elif marker == active_fence:
                active_fence = None
            current_lines.append(line)
            continue

        heading_match = None if active_fence else _HEADING_LINE.match(line)
        if not heading_match:
            current_lines.append(line)
            continue

        flush()
        level = len(heading_match.group(1))
        heading = heading_match.group(2).strip()
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, heading))
        current_path = tuple(item[1] for item in heading_stack)
        current_lines = [line]

    flush()
    return sections


def _has_retrievable_content(section_text: str, has_heading: bool) -> bool:
    if not has_heading:
        return bool(section_text)
    _, separator, body = section_text.partition("\n")
    return bool(separator and body.strip())


def _split_long_section(text: str, config: ChunkingConfig) -> list[str]:
    text = text.strip()
    if len(text) <= config.max_size:
        return [text] if text else []

    parts: list[str] = []
    start = 0
    text_length = len(text)

    while text_length - start > config.max_size:
        end = _find_natural_end(text, start, config)
        part = text[start:end].strip()
        if part:
            parts.append(part)
        next_start = _find_overlap_start(text, start, end, config.overlap)
        if next_start <= start:
            next_start = end
        start = next_start

    final_part = text[start:].strip()
    if final_part:
        parts.append(final_part)
    return parts


def _find_natural_end(text: str, start: int, config: ChunkingConfig) -> int:
    desired = min(start + config.target_size, len(text))
    lower = min(start + max(config.target_size - 600, 1), desired)
    upper = min(start + min(config.target_size + 300, config.max_size), len(text))

    for pattern in ("\n\n", ". ", "\n", " "):
        position = text.rfind(pattern, lower, upper)
        if position >= lower:
            return min(position + len(pattern), start + config.max_size)
    return desired


def _find_overlap_start(text: str, section_start: int, end: int, overlap: int) -> int:
    if overlap == 0:
        return end

    desired = max(section_start, end - overlap)
    lower = max(section_start, end - overlap - 100)
    upper = min(end, end - overlap + 100)

    candidates: list[int] = []
    for match in re.finditer(r"\n\s*\n|\s+", text[lower:upper]):
        candidates.append(lower + match.end())
    if candidates:
        return min(candidates, key=lambda position: abs(position - desired))
    return desired


def _stable_chunk_id(
    *,
    source_path: str,
    heading_path: Sequence[str],
    heading_occurrence: int,
    part_index: int,
    text: str,
) -> str:
    identity = {
        "source_path": source_path,
        "heading_path": list(heading_path),
        "heading_occurrence": heading_occurrence,
        "part_index": part_index,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"chunk_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:24]}"

