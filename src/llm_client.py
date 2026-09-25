"""Minimal OpenAI-compatible Chat Completions client."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 30.0


class LLMClientError(RuntimeError):
    """A configuration, transport, or response error from the LLM API."""


@dataclass(frozen=True, slots=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    thinking_mode: str | None = None

    @classmethod
    def from_env(cls, env_file: Path | str | None = None) -> "LLMConfig":
        if env_file is not None:
            load_env_file(env_file)
        missing = [
            name
            for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
            if not os.environ.get(name, "").strip()
        ]
        if missing:
            raise LLMClientError(
                "Missing required LLM configuration: " + ", ".join(missing)
            )
        timeout_text = os.environ.get("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout = float(timeout_text)
        except ValueError as error:
            raise LLMClientError("LLM_TIMEOUT_SECONDS must be numeric") from error
        if timeout <= 0:
            raise LLMClientError("LLM_TIMEOUT_SECONDS must be positive")
        base_url = os.environ["LLM_BASE_URL"].strip()
        thinking_mode = os.environ.get("LLM_THINKING_MODE", "").strip().lower() or None
        if thinking_mode is None and "api.deepseek.com" in base_url.casefold():
            thinking_mode = "disabled"
        if thinking_mode not in {None, "enabled", "disabled"}:
            raise LLMClientError("LLM_THINKING_MODE must be enabled or disabled")
        return cls(
            api_key=os.environ["LLM_API_KEY"].strip(),
            base_url=base_url,
            model=os.environ["LLM_MODEL"].strip(),
            timeout_seconds=timeout,
            thinking_mode=thinking_mode,
        )


def load_env_file(path: Path | str) -> None:
    """Load simple KEY=VALUE entries without overriding process environment."""

    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or not name.replace("_", "a").isalnum() or name[0].isdigit():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


class OpenAIChatCompletionsClient:
    """Send deterministic text requests to an OpenAI-style endpoint."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str:
        answer, _ = self.complete_with_usage(
            messages, max_tokens=max_tokens, temperature=temperature
        )
        return answer

    def complete_with_usage(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> tuple[str, dict[str, int | None]]:
        """Return the same answer plus provider-reported tokens, when present."""
        if not messages:
            raise ValueError("messages must not be empty")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        payload = {
            "model": self.config.model,
            "messages": [dict(message) for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.config.thinking_mode is not None:
            payload["thinking"] = {"type": self.config.thinking_mode}
        request = Request(
            _chat_completions_url(self.config.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")[:500]
            raise LLMClientError(
                f"LLM API returned HTTP {error.code}: {details}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise LLMClientError(f"LLM API request failed: {error}") from error
        try:
            data = json.loads(body)
        except json.JSONDecodeError as error:
            raise LLMClientError("LLM API returned invalid JSON") from error
        answer = parse_chat_completion(data)
        usage = data.get("usage")
        usage = usage if isinstance(usage, Mapping) else {}

        def token_count(name: str) -> int | None:
            value = usage.get(name)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return value
            return None

        return answer, {
            "input_tokens": token_count("prompt_tokens"),
            "output_tokens": token_count("completion_tokens"),
        }


def parse_chat_completion(data: Mapping[str, Any]) -> str:
    """Extract the first assistant text from a Chat Completions response."""

    try:
        choices = data["choices"]
        first = choices[0]
        content = first["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise LLMClientError("LLM response is missing choices[0].message.content") from error
    if not isinstance(content, str) or not content.strip():
        raise LLMClientError("LLM response content is empty or not text")
    return content.strip()


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return normalized + "/chat/completions"
