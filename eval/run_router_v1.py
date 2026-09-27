"""Router V1 experiment runner.

The runner never auto-loads the frozen benchmark. Running against
``eval/router_benchmark_v1.json`` requires the explicit
``--allow-frozen-benchmark`` flag so the pre-freeze blindness guard cannot be
bypassed accidentally.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from src.router_v1_identity import DEFAULT_CONTRACT_PATH, verify_contract_identity
from src.router_v1_pipeline import ARM_NAMES, RouterV1Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_BENCHMARK_PATH = PROJECT_ROOT / "eval" / "router_benchmark_v1.json"
RUNNER_VERSION = "router_v1_runner"


class BlindnessGuardError(RuntimeError):
    """The runner was pointed at the frozen benchmark without an explicit override."""


def resolve_arm_selection(value: str) -> tuple[str, ...]:
    if value == "ALL":
        return ARM_NAMES
    if value not in ARM_NAMES:
        raise ValueError(f"unknown arm selection: {value}")
    return (value,)


def load_query_cases(
    path: Path | str,
    *,
    allow_frozen_benchmark: bool = False,
) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    if resolved == FROZEN_BENCHMARK_PATH.resolve() and not allow_frozen_benchmark:
        raise BlindnessGuardError(
            "refusing to load the frozen benchmark without --allow-frozen-benchmark"
        )
    data = json.loads(resolved.read_text(encoding="utf-8"))
    raw_cases = data.get("cases") if isinstance(data, dict) else data
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("query file must contain a non-empty list of cases")
    cases: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"case {index} must be an object")
        query = str(raw.get("query", "")).strip()
        if not query:
            raise ValueError(f"case {index} is missing a query")
        history = raw.get("history") or []
        if not isinstance(history, list):
            raise ValueError(f"case {index} history must be a list")
        cases.append(
            {
                "case_id": str(raw.get("case_id") or raw.get("id") or f"case_{index:03d}"),
                "query": query,
                "history": history,
                "history_id": raw.get("history_id"),
            }
        )
    return cases


def load_shared_rewrites(path: Path | str | None) -> dict[str, str]:
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("rewrites file must be a JSON object mapping case_id to rewrite")
    return {str(key): str(value) for key, value in data.items()}


def build_pipeline(project_root: Path | str = PROJECT_ROOT, *, device: str = "cpu") -> RouterV1Pipeline:
    """Assemble the frozen pipeline from the existing baseline components."""

    from src.indexing import load_index
    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    from src.reranked_retriever import RerankedPolicyRetriever
    from src.reranker import CrossEncoderReranker
    from src.retriever import PolicyRetriever
    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.semantic_indexing import load_semantic_index
    from src.semantic_retriever import SemanticPolicyRetriever

    root = Path(project_root).resolve()
    config = LLMConfig.from_env(root / ".env")
    lexical_index = load_index(root / "cache" / "policy_index.json")
    semantic_index = load_semantic_index(root / "cache" / "semantic_index.json")
    if [chunk.to_dict() for chunk in lexical_index.chunks] != [
        chunk.to_dict() for chunk in semantic_index.chunks
    ]:
        raise ValueError("lexical and semantic indexes do not contain identical chunks")
    model_cache = root / "cache" / "huggingface"
    semantic_encoder = SentenceTransformerEncoder(
        semantic_index.model_name,
        cache_folder=model_cache,
        device=device,
        local_files_only=True,
    )
    reranker = CrossEncoderReranker(
        cache_folder=model_cache,
        device=device,
        local_files_only=True,
    )
    retriever = RerankedPolicyRetriever(
        PolicyRetriever(lexical_index),
        SemanticPolicyRetriever(semantic_index, semantic_encoder),
        reranker,
    )
    return RouterV1Pipeline(
        retriever,
        OpenAIChatCompletionsClient(config),
        model=config.model,
    )


def run_cases(
    pipeline: RouterV1Pipeline,
    cases: Sequence[dict[str, Any]],
    *,
    arms: Sequence[str],
    shared_rewrites: dict[str, str] | None = None,
    frozen_benchmark_executed: bool = False,
) -> dict[str, Any]:
    shared_rewrites = shared_rewrites or {}
    outputs: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["case_id"]
        run = pipeline.run_case(
            case["query"],
            case.get("history", []),
            arms=arms,
            case_id=case_id,
            history_identifier=case.get("history_id"),
            shared_rewrite=shared_rewrites.get(case_id),
        )
        outputs.append(run.to_dict())
    return {
        "runner_version": RUNNER_VERSION,
        "arms": list(arms),
        "frozen_benchmark_executed": frozen_benchmark_executed,
        "cases": outputs,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the frozen Router V1 experiment arms.")
    parser.add_argument("--queries", required=True, help="JSON file with synthetic or post-freeze cases")
    parser.add_argument("--arm", default="ROUTED", choices=["FIXED_DIRECT", "FIXED_DECOMPOSE", "ROUTED", "ALL"])
    parser.add_argument("--output", help="optional path for the run record JSON")
    parser.add_argument("--rewrites", help="optional JSON map of case_id to shared rewrite")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH))
    parser.add_argument("--allow-frozen-benchmark", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        arms = resolve_arm_selection(args.arm)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    verify_contract_identity(args.contract)
    try:
        cases = load_query_cases(args.queries, allow_frozen_benchmark=args.allow_frozen_benchmark)
    except BlindnessGuardError as error:
        print(str(error), file=sys.stderr)
        return 3
    pipeline = build_pipeline(device=args.device)
    frozen_benchmark_executed = (
        Path(args.queries).resolve() == FROZEN_BENCHMARK_PATH.resolve()
    )
    record = run_cases(
        pipeline,
        cases,
        arms=arms,
        shared_rewrites=load_shared_rewrites(args.rewrites),
        frozen_benchmark_executed=frozen_benchmark_executed,
    )
    rendered = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
