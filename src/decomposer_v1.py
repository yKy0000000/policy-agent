"""Frozen Router V1 Decomposer stage with deterministic subquery validation."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .router_v1_prompts import DECOMPOSER_SYSTEM, DECOMPOSER_USER_TEMPLATE

DECOMPOSER_MAX_OUTPUT_TOKENS = 256
DECOMPOSER_TEMPERATURE = 0.0
DECOMPOSER_TIMEOUT_SECONDS = 30.0
DECOMPOSER_RETRY_COUNT = 0
RAW_SUBQUERY_MIN = 2
RAW_SUBQUERY_MAX = 3
VALIDATED_DISTINCT_MIN = 2
VALIDATED_DISTINCT_MAX = 3
_WHITESPACE = re.compile(r"\s+")
_TRAILING_PUNCTUATION = "?.!"


class DecomposerChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = DECOMPOSER_MAX_OUTPUT_TOKENS,
        temperature: float = DECOMPOSER_TEMPERATURE,
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class RemovedSubquery:
    text: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class DecomposerOutcome:
    called: bool
    available: bool
    subqueries: tuple[str, ...]
    raw_subqueries: tuple[Any, ...] | None
    removed: tuple[RemovedSubquery, ...]
    raw_response: str | None
    failure: str | None
    fallback_reason: str | None
    latency_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "called": self.called,
            "available": self.available,
            "subqueries": list(self.subqueries),
            "raw_subqueries": list(self.raw_subqueries) if self.raw_subqueries is not None else None,
            "removed_subqueries_with_reason": [item.to_dict() for item in self.removed],
            "raw_response": self.raw_response,
            "failure": self.failure,
            "fallback_reason": self.fallback_reason,
            "latency_seconds": self.latency_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


def not_called() -> DecomposerOutcome:
    return DecomposerOutcome(
        called=False,
        available=False,
        subqueries=(),
        raw_subqueries=None,
        removed=(),
        raw_response=None,
        failure=None,
        fallback_reason=None,
    )


def normalize_subquery_text(text: str) -> str:
    """Apply the frozen normalization; normalized text is used for dedup only."""

    normalized = text.strip()
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = normalized.casefold()
    normalized = _WHITESPACE.sub(" ", normalized)
    return normalized.rstrip(_TRAILING_PUNCTUATION)


def validate_subqueries(
    raw_subqueries: Any,
    base_query: str,
) -> tuple[tuple[str, ...], tuple[RemovedSubquery, ...], str | None]:
    """Return retained subqueries, removals, or a schema failure reason."""

    if not isinstance(raw_subqueries, list):
        return (), (), "schema_invalid:subqueries_not_a_list"
    if not (RAW_SUBQUERY_MIN <= len(raw_subqueries) <= RAW_SUBQUERY_MAX):
        return (), (), "schema_invalid:subquery_count_out_of_range"
    if any(not isinstance(item, str) for item in raw_subqueries):
        return (), (), "schema_invalid:subquery_not_a_string"
    if any(item == "" for item in raw_subqueries):
        return (), (), "schema_invalid:subquery_below_min_length"
    base_normalized = normalize_subquery_text(base_query)
    retained: list[str] = []
    retained_normalized: set[str] = set()
    removed: list[RemovedSubquery] = []
    for item in raw_subqueries:
        trimmed = item.strip()
        normalized = normalize_subquery_text(item)
        if not trimmed:
            removed.append(RemovedSubquery(text=item, reason="blank_after_trim"))
            continue
        if normalized == base_normalized:
            removed.append(RemovedSubquery(text=item, reason="duplicate_of_base"))
            continue
        if normalized in retained_normalized:
            removed.append(RemovedSubquery(text=item, reason="duplicate_subquery"))
            continue
        retained.append(trimmed)
        retained_normalized.add(normalized)
    return tuple(retained), tuple(removed), None


def build_decomposer_messages(rewritten_query: str) -> list[dict[str, str]]:
    query = rewritten_query.strip()
    if not query:
        raise ValueError("rewritten_query must not be blank")
    return [
        {"role": "system", "content": DECOMPOSER_SYSTEM},
        {"role": "user", "content": DECOMPOSER_USER_TEMPLATE.format(rewritten_query=query)},
    ]


class DecomposerClient:
    """One constrained call, only reachable after a legal DECOMPOSE decision."""

    def __init__(self, client: DecomposerChatClient, *, request_model: str) -> None:
        if not request_model.strip():
            raise ValueError("request_model must not be blank")
        self._client = client
        self.request_model = request_model

    def decompose(self, rewritten_query: str) -> DecomposerOutcome:
        started = perf_counter()
        messages = build_decomposer_messages(rewritten_query)
        input_tokens: int | None = None
        output_tokens: int | None = None
        raw_response: str | None = None
        try:
            with_metadata = getattr(self._client, "complete_with_metadata", None)
            if callable(with_metadata):
                raw_response, metadata = with_metadata(
                    messages,
                    max_tokens=DECOMPOSER_MAX_OUTPUT_TOKENS,
                    temperature=DECOMPOSER_TEMPERATURE,
                )
                if isinstance(metadata, Mapping):
                    input_tokens = _as_int(metadata.get("input_tokens"))
                    output_tokens = _as_int(metadata.get("output_tokens"))
            else:
                raw_response = self._client.complete(
                    messages,
                    max_tokens=DECOMPOSER_MAX_OUTPUT_TOKENS,
                    temperature=DECOMPOSER_TEMPERATURE,
                )
        except Exception as error:
            return self._failure(
                started, f"decomposer_call_failed: {error}", None, input_tokens, output_tokens
            )
        if not isinstance(raw_response, str) or not raw_response.strip():
            return self._failure(
                started, "empty_or_non_text_response", raw_response, input_tokens, output_tokens
            )
        try:
            obj = json.loads(raw_response.strip())
        except json.JSONDecodeError as error:
            return self._failure(
                started, f"malformed_json: {error.msg}", raw_response, input_tokens, output_tokens
            )
        if not isinstance(obj, dict):
            return self._failure(
                started, "response_is_not_a_json_object", raw_response, input_tokens, output_tokens
            )
        unexpected = sorted(str(key) for key in obj if key != "subqueries")
        if unexpected:
            return self._failure(
                started,
                f"schema_invalid:unexpected_fields:{','.join(unexpected)}",
                raw_response,
                input_tokens,
                output_tokens,
            )
        if "subqueries" not in obj:
            return self._failure(
                started, "schema_invalid:missing_subqueries", raw_response, input_tokens, output_tokens
            )
        raw_subqueries = obj["subqueries"]
        retained, removed, schema_failure = validate_subqueries(raw_subqueries, rewritten_query)
        latency = perf_counter() - started
        if schema_failure is not None:
            return DecomposerOutcome(
                called=True,
                available=False,
                subqueries=(),
                raw_subqueries=tuple(raw_subqueries) if isinstance(raw_subqueries, list) else None,
                removed=removed,
                raw_response=raw_response,
                failure=schema_failure,
                fallback_reason="decomposer_failure",
                latency_seconds=latency,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        available = len(retained) >= VALIDATED_DISTINCT_MIN
        return DecomposerOutcome(
            called=True,
            available=available,
            subqueries=retained if available else (),
            raw_subqueries=tuple(str(item) for item in raw_subqueries),
            removed=removed,
            raw_response=raw_response,
            failure=None,
            fallback_reason=None if available else "insufficient_distinct_subqueries",
            latency_seconds=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def _failure(
        self,
        started: float,
        reason: str,
        raw_response: str | None,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> DecomposerOutcome:
        return DecomposerOutcome(
            called=True,
            available=False,
            subqueries=(),
            raw_subqueries=None,
            removed=(),
            raw_response=raw_response,
            failure=reason,
            fallback_reason="decomposer_failure",
            latency_seconds=perf_counter() - started,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
