"""Conversation-only contextual query rewriting for retrieval."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


CONTEXTUALIZER_PROMPT_VERSION = "contextual-query-rewrite-v1"
DEFAULT_HISTORY_TURNS = 2

SYSTEM_PROMPT = """You rewrite a user's latest question into a self-contained search query.

Rules:
1. Resolve pronouns, references, and omitted context using only the recent conversation history.
2. If the latest question is already fully self-contained, preserve its meaning and avoid unnecessary expansion.
3. Do not answer the question.
4. Do not introduce GitHub policy facts that were not present in the conversation.
5. Do not treat prior assistant statements as authoritative policy evidence; use them only to identify references and topic.
6. Do not speculate.
7. Return exactly one plain-text query on one line, with no prefix, explanation, JSON, or Markdown."""


class ChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str: ...


class QueryRewriteError(RuntimeError):
    """The contextualizer could not produce a valid standalone query."""


def select_recent_history(
    history: Sequence[Mapping[str, str]],
    *,
    max_turns: int = DEFAULT_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """Keep at most the most recent N user/assistant conversation turns."""

    if max_turns < 0:
        raise ValueError("max_turns must be non-negative")
    normalized: list[dict[str, str]] = []
    for message in history:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"}:
            raise ValueError("history roles must be user or assistant")
        if not content:
            raise ValueError("history content must not be blank")
        normalized.append({"role": role, "content": content})
    if max_turns == 0:
        return []
    return normalized[-(max_turns * 2) :]


def build_rewrite_messages(
    history: Sequence[Mapping[str, str]],
    latest_question: str,
    *,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """Build the deterministic contextualizer prompt."""

    question = latest_question.strip()
    if not question:
        raise ValueError("latest_question must not be blank")
    recent = select_recent_history(history, max_turns=max_history_turns)
    history_text = "\n".join(
        f"{message['role'].capitalize()}: {message['content']}" for message in recent
    ) or "(none)"
    user_prompt = (
        "Recent conversation history:\n"
        f"{history_text}\n\n"
        "Latest user question:\n"
        f"{question}\n\n"
        "Return only the rewritten self-contained search query."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def rewrite_query(
    history: Sequence[Mapping[str, str]],
    latest_question: str,
    client: ChatClient,
    *,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> str:
    """Rewrite one question without answering it or performing retrieval."""

    messages = build_rewrite_messages(
        history,
        latest_question,
        max_history_turns=max_history_turns,
    )
    try:
        rewritten = client.complete(messages, max_tokens=96, temperature=0.0).strip()
    except Exception as error:
        if isinstance(error, QueryRewriteError):
            raise
        raise QueryRewriteError(f"contextual query rewrite failed: {error}") from error
    if not rewritten:
        raise QueryRewriteError("contextualizer returned an empty query")
    if "\n" in rewritten or "\r" in rewritten:
        raise QueryRewriteError("contextualizer must return exactly one line")
    return rewritten


def rewrite_or_keep(
    history: Sequence[Mapping[str, str]],
    latest_question: str,
    client: ChatClient,
    *,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> str:
    """Apply the same contextualizer to every query, including self-contained ones."""

    return rewrite_query(
        history,
        latest_question,
        client,
        max_history_turns=max_history_turns,
    )


def rewrite_cache_key(
    *,
    model: str,
    history: Sequence[Mapping[str, str]],
    latest_question: str,
    prompt_version: str = CONTEXTUALIZER_PROMPT_VERSION,
    max_history_turns: int = DEFAULT_HISTORY_TURNS,
) -> str:
    """Return a stable cache key bound to model, prompt, history, and question."""

    identity = {
        "model": model,
        "prompt_version": prompt_version,
        "history": select_recent_history(history, max_turns=max_history_turns),
        "latest_question": latest_question.strip(),
        "max_history_turns": max_history_turns,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RewriteCache:
    """Small JSON cache with atomic writes; cache directory remains gitignored."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._entries: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("rewrite cache must contain a JSON object")
            self._entries = {
                str(key): dict(value)
                for key, value in data.items()
                if isinstance(value, Mapping)
            }

    def get(self, key: str) -> str | None:
        entry = self._entries.get(key)
        rewrite = entry.get("rewrite") if entry else None
        return str(rewrite) if isinstance(rewrite, str) and rewrite.strip() else None

    def set(self, key: str, rewrite: str, metadata: Mapping[str, Any]) -> None:
        self._entries[key] = {"rewrite": rewrite, **dict(metadata)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
