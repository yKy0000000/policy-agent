"""Grounded policy answer generation with program-owned source citations."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .conversation import DEFAULT_HISTORY_TURNS, select_recent_history


GENERATION_PROMPT_VERSION = "grounded-policy-answer-v1"
DEFAULT_GENERATION_MAX_TOKENS = 512
_CITATION_PATTERN = re.compile(r"\[S(\d+)\]")
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


GROUNDING_SYSTEM_PROMPT = """You answer questions using only the provided GitHub policy evidence.

Rules:
1. Treat the Sources section as the only authority for policy facts. Do not use model memory as policy authority.
2. Conversation history is only for understanding the user's context. It is not policy evidence.
3. Support every material policy claim with one or more inline source IDs such as [S1].
4. Use only source IDs explicitly supplied in the Sources section.
5. Never invent a source ID or URL, and never output a URL.
6. Cite a source only when its content actually supports the associated claim, not merely because it is topically related.
7. If the supplied evidence does not answer the specific question, explicitly say that the provided published policies do not specify the requested information. Cite relevant context without claiming it contains the missing fact.
8. Do not infer legal conclusions beyond the evidence or present uncertainty as certainty.
9. Keep the answer concise and useful.
10. Return only the answer with claim-level inline citations. Do not add a Sources section."""


class GenerationClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = DEFAULT_GENERATION_MAX_TOKENS,
        temperature: float = 0.0,
    ) -> str: ...


class GroundedGenerationError(RuntimeError):
    """The grounded generation request did not produce a usable answer."""


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    citation_id: str
    text: str
    title: str
    heading_path: tuple[str, ...]
    source_url: str
    source_path: str
    chunk_id: str

    def source_metadata(self) -> dict[str, object]:
        data = asdict(self)
        data.pop("text")
        data["heading_path"] = list(self.heading_path)
        return data


def assign_evidence_sources(evidence: Sequence[Any]) -> list[EvidenceSource]:
    """Assign stable per-request S1..Sn IDs in the reranked evidence order."""

    return [
        EvidenceSource(
            citation_id=f"S{index}",
            text=str(item.text),
            title=str(item.title),
            heading_path=tuple(str(value) for value in item.heading_path),
            source_url=str(item.source_url),
            source_path=str(item.source_path),
            chunk_id=str(item.chunk_id),
        )
        for index, item in enumerate(evidence, start=1)
    ]


def format_evidence(sources: Sequence[EvidenceSource]) -> str:
    """Format evidence for the model without exposing source URLs."""

    blocks: list[str] = []
    for source in sources:
        heading = " > ".join(source.heading_path) or "Document introduction"
        blocks.append(
            f"[{source.citation_id}]\n"
            f"Title: {source.title}\n"
            f"Section: {heading}\n"
            f"Content:\n{source.text}"
        )
    return "\n\n---\n\n".join(blocks)


def build_grounded_messages(
    question: str,
    history: Sequence[Mapping[str, str]],
    sources: Sequence[EvidenceSource],
    *,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """Build the grounded prompt with history separated from policy sources."""

    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("question must not be blank")
    if not sources:
        raise ValueError("at least one evidence source is required")
    recent_history = select_recent_history(history, max_turns=max_history_turns)
    history_text = "\n".join(
        f"{message['role'].capitalize()}: {message['content']}"
        for message in recent_history
    ) or "(none)"
    user_prompt = (
        "Conversation context (not policy evidence):\n"
        f"{history_text}\n\n"
        "User question:\n"
        f"{cleaned_question}\n\n"
        "Sources (the only policy evidence):\n"
        f"{format_evidence(sources)}"
    )
    return [
        {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_citation_ids(answer: str) -> list[str]:
    """Return cited IDs once each, preserving their first appearance."""

    cited: list[str] = []
    seen: set[str] = set()
    for match in _CITATION_PATTERN.finditer(answer):
        citation_id = f"S{match.group(1)}"
        if citation_id not in seen:
            seen.add(citation_id)
            cited.append(citation_id)
    return cited


def validate_citations(
    answer: str,
    sources: Sequence[EvidenceSource],
) -> dict[str, Any]:
    """Validate citation IDs and build the cited-only structured source list."""

    source_map = {source.citation_id: source for source in sources}
    cited_ids = parse_citation_ids(answer)
    invalid = [citation_id for citation_id in cited_ids if citation_id not in source_map]
    valid_ids = [citation_id for citation_id in cited_ids if citation_id in source_map]
    warnings: list[str] = []
    if not cited_ids:
        warnings.append("missing_citations")
    if invalid:
        warnings.append("invalid_citations")
    contains_url = bool(_URL_PATTERN.search(answer))
    if contains_url:
        warnings.append("model_generated_url")
    return {
        "citation_ids": valid_ids,
        "sources": [source_map[citation_id].source_metadata() for citation_id in valid_ids],
        "validation": {
            "valid": not warnings,
            "has_citations": bool(cited_ids),
            "invalid_citations": invalid,
            "contains_model_generated_url": contains_url,
            "warnings": warnings,
        },
    }


def generation_cache_key(
    *,
    model: str,
    question: str,
    history: Sequence[Mapping[str, str]],
    sources: Sequence[EvidenceSource],
    prompt_version: str = GENERATION_PROMPT_VERSION,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
    max_tokens: int = DEFAULT_GENERATION_MAX_TOKENS,
) -> str:
    """Bind cached output to the model, prompt, context, and evidence chunk IDs."""

    identity = {
        "model": model,
        "prompt_version": prompt_version,
        "question": question.strip(),
        "history": select_recent_history(history, max_turns=max_history_turns),
        "evidence_chunk_ids": [source.chunk_id for source in sources],
        "max_history_turns": max_history_turns,
    }
    # Preserve default-mode cache identities. A larger replay budget must not
    # read a 512-token answer from cache or overwrite one under the same key.
    if max_tokens != DEFAULT_GENERATION_MAX_TOKENS:
        identity["max_tokens"] = max_tokens
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class GeneratedAnswerCache:
    """Atomic local cache for successful raw generated answers."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._entries: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("generated-answer cache must contain a JSON object")
            self._entries = {
                str(key): dict(value)
                for key, value in data.items()
                if isinstance(value, Mapping)
            }

    def get(self, key: str) -> str | None:
        entry = self._entries.get(key)
        answer = entry.get("answer") if entry else None
        return str(answer) if isinstance(answer, str) and answer.strip() else None

    def set(self, key: str, answer: str, metadata: Mapping[str, Any]) -> None:
        self._entries[key] = {"answer": answer, **dict(metadata)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)


def generate_grounded_answer(
    question: str,
    history: Sequence[Mapping[str, str]],
    evidence: Sequence[Any],
    client: GenerationClient,
    *,
    model: str,
    cache: GeneratedAnswerCache | None = None,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
    max_tokens: int = DEFAULT_GENERATION_MAX_TOKENS,
) -> dict[str, Any]:
    """Generate from supplied evidence only, then validate and map citations."""

    sources = assign_evidence_sources(evidence)
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    key = generation_cache_key(
        model=model,
        question=question,
        history=history,
        sources=sources,
        max_history_turns=max_history_turns,
        max_tokens=max_tokens,
    )
    cached_answer = cache.get(key) if cache else None
    if cached_answer is not None:
        answer = cached_answer
        response_source = "cache"
    else:
        messages = build_grounded_messages(
            question,
            history,
            sources,
            max_history_turns=max_history_turns,
        )
        try:
            answer = client.complete(
                messages,
                max_tokens=max_tokens,
                temperature=0.0,
            ).strip()
        except Exception as error:
            raise GroundedGenerationError(
                f"grounded answer generation failed: {error}"
            ) from error
        if not answer:
            raise GroundedGenerationError("grounded generator returned an empty answer")
        response_source = "api"

    validation_started = perf_counter()
    citation_result = validate_citations(answer, sources)
    validation_seconds = perf_counter() - validation_started
    if (
        cache
        and cached_answer is None
        and citation_result["validation"]["valid"]
    ):
        cache.set(
            key,
            answer,
            {
                "model": model,
                "prompt_version": GENERATION_PROMPT_VERSION,
                "evidence_chunk_ids": [source.chunk_id for source in sources],
                "max_tokens": max_tokens,
            },
        )
    return {
        "answer": answer,
        "citation_ids": citation_result["citation_ids"],
        "sources": citation_result["sources"],
        "validation": citation_result["validation"],
        "cache_key": key,
        "response_source": response_source,
        "validation_seconds": validation_seconds,
    }
