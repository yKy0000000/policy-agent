"""Thin live adapters over existing src/ components; product code is unchanged."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from .benchmark import PROJECT_ROOT
from .pipeline import ContextSelection, Generation, Pipeline, UnionByChunkId, WholeQueryPlanner
from .schemas import Evidence, Requirement


class ProjectRewriter:
    def __init__(self, client, mode: str):
        self.client, self.mode = client, mode
        self.last_input_tokens = 0
        self.last_output_tokens = 0

    def rewrite(self, query: str, history: Sequence[dict[str, str]]) -> str:
        self.last_input_tokens = self.last_output_tokens = 0
        if not history:
            return query
        if self.mode != "contextual_rewrite_v1":
            raise ValueError("history requires contextual_rewrite_v1")
        from src.conversation import build_rewrite_messages

        answer, usage = self.client.complete_with_usage(build_rewrite_messages(history, query), max_tokens=96, temperature=0.0)
        self.last_input_tokens = usage.get("input_tokens") or 0
        self.last_output_tokens = usage.get("output_tokens") or 0
        answer = answer.strip()
        if not answer or "\n" in answer:
            raise ValueError("contextual rewrite must return one nonempty line")
        return answer


class HybridRetriever:
    def __init__(self, lexical, semantic):
        self.lexical, self.semantic = lexical, semantic

    def retrieve(self, query: str, requirement_id: str) -> list[Evidence]:
        from src.reranked_retriever import candidate_union

        union = candidate_union(self.lexical.search(query, top_k=20), self.semantic.search(query, top_k=20))
        return [Evidence(chunk_id=item.result.chunk_id, query_id=requirement_id,
                         source_path=item.result.source_path, source_url=item.result.source_url,
                         title=item.result.title, heading_path=item.result.heading_path,
                         text=item.result.text, lexical_rank=item.lexical_rank,
                         semantic_rank=item.semantic_rank) for item in union]


class BGEReranker:
    def __init__(self, scorer):
        self.scorer = scorer

    def rerank(self, rewritten_query: str, requirements: list[Requirement], candidates: list[Evidence]) -> list[Evidence]:
        if len(requirements) != 1:
            raise ValueError("bge_whole_query reranker handles one requirement; register a multi-query reranker for decomposition")
        query = requirements[0].query
        texts = [f"Document: {item.title}\nSection: {' > '.join(item.heading_path) or 'Document introduction'}\n\n{item.text}" for item in candidates]
        scores = self.scorer.score(query, texts)
        if len(scores) != len(candidates):
            raise ValueError("reranker score count differs from candidate count")
        ranked = sorted((replace(item, reranker_score=float(score)) for item, score in zip(candidates, scores)),
                        key=lambda item: (-float(item.reranker_score), item.chunk_id))
        return [replace(item, rank=index) for index, item in enumerate(ranked, 1)]


class ProjectContextBuilder:
    def __init__(self, policy_id: str, scorer, semantic):
        self.policy_id, self.scorer, self.semantic = policy_id, scorer, semantic

    def build(self, rewritten_query: str, ranked: list[Evidence]) -> ContextSelection:
        from src.generator import assign_evidence_sources, format_evidence

        if not ranked:
            raise ValueError("no ranked evidence")
        count = lambda item: self.scorer.count_tokens(item.text)
        if self.policy_id == "fixed_top5":
            selected = ranked[:5]
        elif self.policy_id == "coverage_selector_v2":
            from src.evidence_selector import select_evidence_set

            decision = select_evidence_set(rewritten_query, ranked,
                vectors=self.semantic.evidence_vectors([item.chunk_id for item in ranked]), token_count=count)
            selected = [ranked[index] for index in decision.selected_indices]
        elif self.policy_id == "no_router_adaptive_v1":
            selected = ranked[:5]
            used = sum(count(item) for item in selected)
            for item in ranked[5:20]:
                if float(ranked[0].reranker_score) - float(item.reranker_score) > 3.0 or used + count(item) > 6000:
                    break
                selected.append(item)
                used += count(item)
        else:
            raise ValueError(f"unknown context policy: {self.policy_id}")
        sources = assign_evidence_sources(selected)
        return ContextSelection(list(selected), format_evidence(sources), sum(count(item) for item in selected))


class ProjectGenerator:
    def __init__(self, client, model: str, rewriter: ProjectRewriter, price: dict[str, float] | None):
        self.client, self.model, self.rewriter, self.price = client, model, rewriter, price

    def generate(self, query: str, history: Sequence[dict[str, str]], selection: ContextSelection) -> Generation:
        from src.generator import assign_evidence_sources, build_grounded_messages, validate_citations

        sources = assign_evidence_sources(selection.evidence)
        messages = build_grounded_messages(query, history, sources)
        answer, usage = self.client.complete_with_usage(messages, max_tokens=1536, temperature=0.0)
        answer = answer.strip()
        if not answer:
            raise ValueError("generator returned an empty answer")
        cited = validate_citations(answer, sources)
        inp = (usage.get("input_tokens") or 0) + self.rewriter.last_input_tokens
        out = (usage.get("output_tokens") or 0) + self.rewriter.last_output_tokens
        if usage.get("input_tokens") is None or usage.get("output_tokens") is None:
            inp = out = None
        cost = ((inp * self.price["input_per_million"] + out * self.price["output_per_million"]) / 1_000_000
                if self.price and inp is not None and out is not None else None)
        return Generation(answer, cited["sources"], inp, out, cost)


class ProjectValidator:
    def validate(self, answer: str, selected: list[Evidence], citations: list[dict[str, Any]]) -> dict[str, Any]:
        from src.generator import assign_evidence_sources, validate_citations

        return dict(validate_citations(answer, assign_evidence_sources(selected))["validation"])


def build_live_pipeline(config: dict[str, Any], project_root: Path = PROJECT_ROOT) -> Pipeline:
    """Resolve only known component IDs; add future components here, not a new runner."""
    from src.indexing import load_index
    from src.llm_client import LLMConfig, OpenAIChatCompletionsClient
    from src.reranker import CrossEncoderReranker
    from src.retriever import PolicyRetriever
    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.semantic_indexing import load_semantic_index
    from src.semantic_retriever import SemanticPolicyRetriever

    ids = config["components"]
    expected = {"planner": "whole_query", "retriever": "hybrid_20_20", "merger": "union_by_chunk_id",
                "reranker": "bge", "generator": "grounded_policy_answer_v1", "validator": "deterministic_v1"}
    for key, value in expected.items():
        if ids.get(key) != value:
            raise ValueError(f"unsupported live component {key}={ids.get(key)}; register its factory before use")
    if ids["rewriter"] not in {"single_turn_identity", "contextual_rewrite_v1"}:
        raise ValueError("unsupported rewriter")
    lexical_index = load_index(project_root / "cache" / "policy_index.json")
    semantic_index = load_semantic_index(project_root / "cache" / "semantic_index.json")
    if [chunk.to_dict() for chunk in lexical_index.chunks] != [chunk.to_dict() for chunk in semantic_index.chunks]:
        raise ValueError("lexical and semantic index chunks differ")
    model_cache = project_root / "cache" / "huggingface"
    encoder = SentenceTransformerEncoder(semantic_index.model_name, cache_folder=model_cache, device="cpu", local_files_only=True)
    semantic = SemanticPolicyRetriever(semantic_index, encoder)
    scorer = CrossEncoderReranker(model_name="BAAI/bge-reranker-base", cache_folder=model_cache, device="cpu", local_files_only=True)
    client_config = LLMConfig.from_env(project_root / ".env")
    client = OpenAIChatCompletionsClient(client_config)
    rewriter = ProjectRewriter(client, ids["rewriter"])
    return Pipeline(
        config["pipeline_id"], rewriter, WholeQueryPlanner(), HybridRetriever(PolicyRetriever(lexical_index), semantic),
        UnionByChunkId(), BGEReranker(scorer), ProjectContextBuilder(ids["context_builder"], scorer, semantic),
        ProjectGenerator(client, client_config.model, rewriter, config.get("price_per_million")), ProjectValidator(),
        {"execution": "live", **ids, "generation_model": client_config.model},
    )
