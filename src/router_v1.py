"""Frozen Router V1 decision stage: one call, decision is the only contract field."""

from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Mapping, Protocol, Sequence

from .router_v1_prompts import ROUTER_SYSTEM, ROUTER_USER_TEMPLATE

DIRECT = "DIRECT"
DECOMPOSE = "DECOMPOSE"
ALLOWED_DECISIONS = (DIRECT, DECOMPOSE)
DIRECT_REASON_CODES = ("COHERENT_SINGLE_REPRESENTATION", "NO_CLEAR_FAITHFUL_SPLIT")
DECOMPOSE_REASON_CODES = ("COVERAGE_SPLIT_RISK",)
KNOWN_REASON_CODES = DIRECT_REASON_CODES + DECOMPOSE_REASON_CODES
UNRECOGNIZED_REASON = "UNRECOGNIZED"
ROUTER_MAX_OUTPUT_TOKENS = 96
ROUTER_TEMPERATURE = 0.0
ROUTER_TIMEOUT_SECONDS = 30.0
ROUTER_RETRY_COUNT = 0


class RouterChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = ROUTER_MAX_OUTPUT_TOKENS,
        temperature: float = ROUTER_TEMPERATURE,
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class RouterDecision:
    """Parsed Router output; the decision field is the only execution contract."""

    decision: str
    raw_reason_code: str | None
    effective_reason_code: str
    reason_validity: str
    raw_response: str | None
    failure: str | None
    fallback: bool
    schema_anomalies: tuple[str, ...]
    latency_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    request_id: str | None = None
    response_id: str | None = None

    @property
    def reason_code(self) -> str:
        return self.effective_reason_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "raw_reason_code": self.raw_reason_code,
            "effective_reason_code": self.effective_reason_code,
            "reason_validity": self.reason_validity,
            "raw_response": self.raw_response,
            "failure": self.failure,
            "fallback": self.fallback,
            "schema_anomalies": list(self.schema_anomalies),
            "latency_seconds": self.latency_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "request_id": self.request_id,
            "response_id": self.response_id,
        }


def reason_codes_for(decision: str) -> tuple[str, ...]:
    return DECOMPOSE_REASON_CODES if decision == DECOMPOSE else DIRECT_REASON_CODES


def build_router_messages(rewritten_query: str) -> list[dict[str, str]]:
    query = rewritten_query.strip()
    if not query:
        raise ValueError("rewritten_query must not be blank")
    return [
        {"role": "system", "content": ROUTER_SYSTEM},
        {"role": "user", "content": ROUTER_USER_TEMPLATE.format(rewritten_query=query)},
    ]


def _classify_reason(obj: Mapping[str, Any], decision: str) -> tuple[str | None, str, str]:
    if "reason_code" not in obj:
        return None, "missing", UNRECOGNIZED_REASON
    raw = obj["reason_code"]
    if not isinstance(raw, str):
        return raw, "invalid_type", UNRECOGNIZED_REASON
    if raw not in KNOWN_REASON_CODES:
        return raw, "unknown", UNRECOGNIZED_REASON
    if raw not in reason_codes_for(decision):
        return raw, "inconsistent_with_decision", UNRECOGNIZED_REASON
    return raw, "valid", raw


def parse_router_response(
    raw_response: str | None,
) -> tuple[RouterDecision | None, str | None]:
    """Parse one raw Router response; return a decision or a fallback reason."""

    if not isinstance(raw_response, str) or not raw_response.strip():
        return None, "empty_or_non_text_response"
    try:
        obj = json.loads(raw_response.strip())
    except json.JSONDecodeError as error:
        return None, f"malformed_json: {error.msg}"
    if not isinstance(obj, dict):
        return None, "response_is_not_a_json_object"
    decision = obj.get("decision")
    if decision is None:
        return None, "missing_decision"
    if not isinstance(decision, str) or decision not in ALLOWED_DECISIONS:
        return None, f"invalid_decision: {decision!r}"
    anomalies = tuple(sorted(str(key) for key in obj if key not in {"decision", "reason_code"}))
    raw_reason, validity, effective = _classify_reason(obj, decision)
    return (
        RouterDecision(
            decision=decision,
            raw_reason_code=raw_reason,
            effective_reason_code=effective,
            reason_validity=validity,
            raw_response=raw_response,
            failure=None,
            fallback=False,
            schema_anomalies=anomalies,
        ),
        None,
    )


class RouterClient:
    """One constrained DeepSeek-compatible call; failure falls back to DIRECT."""

    def __init__(self, client: RouterChatClient, *, request_model: str) -> None:
        if not request_model.strip():
            raise ValueError("request_model must not be blank")
        self._client = client
        self.request_model = request_model

    def decide(self, rewritten_query: str) -> RouterDecision:
        started = perf_counter()
        messages = build_router_messages(rewritten_query)
        input_tokens: int | None = None
        output_tokens: int | None = None
        request_id: str | None = None
        response_id: str | None = None
        raw_response: str | None = None
        try:
            with_metadata = getattr(self._client, "complete_with_metadata", None)
            if callable(with_metadata):
                raw_response, metadata = with_metadata(
                    messages,
                    max_tokens=ROUTER_MAX_OUTPUT_TOKENS,
                    temperature=ROUTER_TEMPERATURE,
                )
                if isinstance(metadata, Mapping):
                    input_tokens = _as_int(metadata.get("input_tokens"))
                    output_tokens = _as_int(metadata.get("output_tokens"))
                    request_id = _as_str(metadata.get("request_id"))
                    response_id = _as_str(metadata.get("response_id"))
            else:
                raw_response = self._client.complete(
                    messages,
                    max_tokens=ROUTER_MAX_OUTPUT_TOKENS,
                    temperature=ROUTER_TEMPERATURE,
                )
        except Exception as error:
            return RouterDecision(
                decision=DIRECT,
                raw_reason_code=None,
                effective_reason_code=UNRECOGNIZED_REASON,
                reason_validity="not_evaluated",
                raw_response=None,
                failure=f"router_call_failed: {error}",
                fallback=True,
                schema_anomalies=(),
                latency_seconds=perf_counter() - started,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_id=request_id,
                response_id=response_id,
            )

        latency = perf_counter() - started
        decision, fallback_reason = parse_router_response(raw_response)
        if decision is None:
            return RouterDecision(
                decision=DIRECT,
                raw_reason_code=None,
                effective_reason_code=UNRECOGNIZED_REASON,
                reason_validity="not_evaluated",
                raw_response=raw_response,
                failure=fallback_reason,
                fallback=True,
                schema_anomalies=(),
                latency_seconds=latency,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_id=request_id,
                response_id=response_id,
            )
        return RouterDecision(
            decision=decision.decision,
            raw_reason_code=decision.raw_reason_code,
            effective_reason_code=decision.effective_reason_code,
            reason_validity=decision.reason_validity,
            raw_response=decision.raw_response,
            failure=None,
            fallback=False,
            schema_anomalies=decision.schema_anomalies,
            latency_seconds=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            request_id=request_id,
            response_id=response_id,
        )


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _as_str(value: Any) -> str | None:
    return str(value) if isinstance(value, str) and value else None
