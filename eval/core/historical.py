"""Read-only adapter from frozen A1 artifacts to the canonical PipelineResult."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .benchmark import BenchmarkCase, PROJECT_ROOT
from .schemas import Evidence, PipelineResult, Requirement


SOURCES = {
    "orders": "eval/results/a0_bge_rerank_orders.json",
    "context": "eval/results/human_aware_context_v1.json",
    "generation": "eval/results/query_aware_stage1_generation_results.json",
}


def _load(path: str) -> tuple[dict[str, Any], str]:
    raw = (PROJECT_ROOT / path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


class FrozenReplayPipeline:
    """Same runner interface as a live Pipeline; never invokes a model/provider."""

    def __init__(self, pipeline_id: str, arm: str):
        self.pipeline_id, self.arm = pipeline_id, arm
        artifacts = {key: _load(path) for key, path in SOURCES.items()}
        self.hashes = {SOURCES[key]: pair[1] for key, pair in artifacts.items()}
        self.orders = artifacts["orders"][0]["cases"]
        context = artifacts["context"][0]
        if arm not in context["policy_per_case"]:
            raise ValueError(f"arm has no frozen context: {arm}")
        self.context = context["policy_per_case"][arm]
        generation = artifacts["generation"][0]
        self.generations = {row["case_id"]: row for row in generation["cases"] if row["arm"] == arm}
        self.economics = {row["case_id"]: row for row in generation["per_case_counterfactual_economics"] if row["arm"] == arm}
        if len(self.generations) != 50 or len(self.economics) != 50:
            raise ValueError("frozen replay rows are incomplete")

    def run(self, case: BenchmarkCase) -> PipelineResult:
        row, ctx, econ = self.generations[case.case_id], self.context[case.case_id], self.economics[case.case_id]
        if row["original_query"] != case.query or row["selected_chunk_ids"] != ctx["selected_chunk_ids"]:
            raise ValueError(f"historical query/context identity mismatch: {case.case_id}")
        ranked = [Evidence(chunk_id=item["chunk_id"], reranker_score=item["bge_score"], rank=index,
                           token_count=item.get("tokens")) for index, item in enumerate(self.orders[case.case_id], 1)]
        by_id = {item.chunk_id: item for item in ranked}
        if any(chunk_id not in by_id for chunk_id in row["selected_chunk_ids"]):
            raise ValueError(f"historical selected chunk outside candidate union: {case.case_id}")
        identity = row["reuse_source"] if row["generation_source"] == "reused" else row["canonical_input_hash"]
        return PipelineResult(
            case_id=case.case_id, pipeline_id=self.pipeline_id, original_query=case.query,
            rewritten_query=row["rewritten_query"], requirements=[Requirement("whole", row["rewritten_query"])],
            retrieval_by_requirement={"whole": list(ranked)}, retrieval_candidates=list(ranked), ranked_candidates=ranked,
            selected_evidence=[by_id[cid] for cid in row["selected_chunk_ids"]],
            serialized_context=row["serialized_context"], evidence_tokens=row["evidence_tokens"],
            answer=row["answer"], citations=list(row["citations"]), validation=dict(row["validation"]),
            provider_input_tokens=econ["provider_input_tokens"], provider_output_tokens=econ["provider_output_tokens"],
            estimated_cost_usd=econ["estimated_cost"], latency_seconds=None,
            component_provenance={
                "execution": "frozen_replay", "retriever": "hybrid_20_20", "reranker": "bge",
                "context_policy": self.arm, "generator": row["generation_model"],
                "prompt_hash": row["generation_prompt_hash"], "generation_identity": identity,
                "source_hashes": self.hashes,
                "unavailable_historical_fields": ["retrieval_component_scores", "live_latency"],
            },
        )
