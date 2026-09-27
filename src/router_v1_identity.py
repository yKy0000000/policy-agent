"""Runtime identity verification against the frozen Router V1 contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .router_v1_prompts import (
    DECOMPOSER_SCHEMA,
    DECOMPOSER_SYSTEM,
    DECOMPOSER_USER_TEMPLATE,
    ROUTER_SCHEMA,
    ROUTER_SYSTEM,
    ROUTER_USER_TEMPLATE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = PROJECT_ROOT / "eval" / "router_v1_contract.json"
REWRITE_SOURCE_PATH = PROJECT_ROOT / "src" / "conversation.py"


class ContractIdentityError(RuntimeError):
    """Runtime prompts, schemas, or rewrite source do not match the frozen contract."""


def canonical_json_sha256(value: Any) -> str:
    """Hash JSON with the contract's canonical convention."""

    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def router_prompt_identity() -> dict[str, str]:
    return {
        "prompt_sha256": canonical_json_sha256(
            {"system": ROUTER_SYSTEM, "user_template": ROUTER_USER_TEMPLATE}
        ),
        "schema_sha256": canonical_json_sha256(ROUTER_SCHEMA),
        "system_component_sha256": text_sha256(ROUTER_SYSTEM),
        "user_template_component_sha256": text_sha256(ROUTER_USER_TEMPLATE),
    }


def decomposer_prompt_identity() -> dict[str, str]:
    return {
        "prompt_sha256": canonical_json_sha256(
            {"system": DECOMPOSER_SYSTEM, "user_template": DECOMPOSER_USER_TEMPLATE}
        ),
        "schema_sha256": canonical_json_sha256(DECOMPOSER_SCHEMA),
        "system_component_sha256": text_sha256(DECOMPOSER_SYSTEM),
        "user_template_component_sha256": text_sha256(DECOMPOSER_USER_TEMPLATE),
    }


@dataclass(frozen=True, slots=True)
class ContractIdentity:
    contract_path: str
    contract_sha256: str
    router_prompt_sha256: str
    router_schema_sha256: str
    decomposer_prompt_sha256: str
    decomposer_schema_sha256: str
    rewrite_source_sha256: str
    requested_model_id: str
    provider_host: str
    provider_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_path": self.contract_path,
            "contract_sha256": self.contract_sha256,
            "router_prompt_sha256": self.router_prompt_sha256,
            "router_schema_sha256": self.router_schema_sha256,
            "decomposer_prompt_sha256": self.decomposer_prompt_sha256,
            "decomposer_schema_sha256": self.decomposer_schema_sha256,
            "rewrite_source_sha256": self.rewrite_source_sha256,
            "requested_model_id": self.requested_model_id,
            "provider_host": self.provider_host,
            "provider_endpoint": self.provider_endpoint,
        }


def load_contract(path: Path | str | None = None) -> dict[str, Any]:
    contract_path = Path(path) if path is not None else DEFAULT_CONTRACT_PATH
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractIdentityError("frozen contract must be a JSON object")
    return data


def verify_contract_identity(
    path: Path | str | None = None,
    *,
    check_rewrite_source: bool = True,
) -> ContractIdentity:
    """Fail fast when runtime identity does not match the frozen contract."""

    contract_path = Path(path) if path is not None else DEFAULT_CONTRACT_PATH
    contract = load_contract(contract_path)
    router_identity = router_prompt_identity()
    decomposer_identity = decomposer_prompt_identity()
    expected_router_prompt = str(contract["router"]["prompt_sha256"])
    expected_router_schema = str(contract["router"]["schema_sha256"])
    expected_decomposer_prompt = str(contract["decomposer"]["prompt_sha256"])
    expected_decomposer_schema = str(contract["decomposer"]["schema_sha256"])
    mismatches: list[str] = []
    if router_identity["prompt_sha256"] != expected_router_prompt:
        mismatches.append(
            f"router prompt: runtime {router_identity['prompt_sha256']} != contract {expected_router_prompt}"
        )
    if router_identity["schema_sha256"] != expected_router_schema:
        mismatches.append(
            f"router schema: runtime {router_identity['schema_sha256']} != contract {expected_router_schema}"
        )
    if decomposer_identity["prompt_sha256"] != expected_decomposer_prompt:
        mismatches.append(
            "decomposer prompt: "
            f"runtime {decomposer_identity['prompt_sha256']} != contract {expected_decomposer_prompt}"
        )
    if decomposer_identity["schema_sha256"] != expected_decomposer_schema:
        mismatches.append(
            "decomposer schema: "
            f"runtime {decomposer_identity['schema_sha256']} != contract {expected_decomposer_schema}"
        )
    rewrite_source_sha256 = file_sha256(REWRITE_SOURCE_PATH)
    if check_rewrite_source:
        expected_rewrite_source = str(contract["rewrite"]["prompt_source_sha256"])
        if rewrite_source_sha256 != expected_rewrite_source:
            mismatches.append(
                "rewrite source: "
                f"runtime {rewrite_source_sha256} != contract {expected_rewrite_source}"
            )
    if mismatches:
        raise ContractIdentityError("; ".join(mismatches))
    router_model = contract["router"]["model"]
    return ContractIdentity(
        contract_path=str(contract_path),
        contract_sha256=file_sha256(contract_path),
        router_prompt_sha256=router_identity["prompt_sha256"],
        router_schema_sha256=router_identity["schema_sha256"],
        decomposer_prompt_sha256=decomposer_identity["prompt_sha256"],
        decomposer_schema_sha256=decomposer_identity["schema_sha256"],
        rewrite_source_sha256=rewrite_source_sha256,
        requested_model_id=str(router_model["requested_model_id"]),
        provider_host=str(router_model["provider_host"]),
        provider_endpoint=str(router_model["provider_endpoint"]),
    )
