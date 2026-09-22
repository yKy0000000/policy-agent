"""Deterministic orchestration for the GitHub policy support pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .conversation import (
    CONTEXTUALIZER_PROMPT_VERSION,
    DEFAULT_HISTORY_TURNS,
    RewriteCache,
    rewrite_cache_key,
    rewrite_or_keep,
    select_recent_history,
)
from .generator import GeneratedAnswerCache, generate_grounded_answer
from .reranked_retriever import RerankedRetrievalResult


EVIDENCE_TOP_K = 5


class AgentChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int = 96,
        temperature: float = 0.0,
    ) -> str: ...


class AgentRetriever(Protocol):
    def search(
        self,
        query: str,
        top_k: int = EVIDENCE_TOP_K,
    ) -> Sequence[RerankedRetrievalResult]: ...


class AgentPipelineError(RuntimeError):
    """A technical failure at one explicit orchestration stage."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        super().__init__(f"policy agent {stage} stage failed: {message}")


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Structured successful output from one deterministic pipeline run."""

    answer: str
    citations: tuple[dict[str, Any], ...]
    citation_ids: tuple[str, ...]
    rewritten_query: str
    evidence: tuple[RerankedRetrievalResult, ...]
    citation_validation: dict[str, Any]
    rewrite_response_source: str
    generation_response_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [dict(citation) for citation in self.citations],
            "citation_ids": list(self.citation_ids),
            "rewritten_query": self.rewritten_query,
            "evidence": [item.to_dict() for item in self.evidence],
            "citation_validation": dict(self.citation_validation),
            "rewrite_response_source": self.rewrite_response_source,
            "generation_response_source": self.generation_response_source,
        }


class PolicySupportAgent:
    """Run the fixed rewrite, retrieval, generation, and validation workflow."""

    def __init__(
        self,
        retriever: AgentRetriever,
        client: AgentChatClient,
        *,
        model: str,
        rewrite_cache: RewriteCache | None = None,
        generation_cache: GeneratedAnswerCache | None = None,
        max_history_turns: int = DEFAULT_HISTORY_TURNS,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be blank")
        if max_history_turns < 0:
            raise ValueError("max_history_turns must be non-negative")
        self._retriever = retriever
        self._client = client
        self._model = model
        self._rewrite_cache = rewrite_cache
        self._generation_cache = generation_cache
        self._max_history_turns = max_history_turns

    @classmethod
    def from_project(
        cls,
        project_root: Path | str | None = None,
        *,
        env_file: Path | str | None = None,
        device: str = "cpu",
    ) -> "PolicySupportAgent":
        """Load the existing indexes, local models, LLM client, and caches."""

        from .indexing import load_index
        from .llm_client import LLMConfig, OpenAIChatCompletionsClient
        from .reranked_retriever import RerankedPolicyRetriever
        from .reranker import CrossEncoderReranker
        from .retriever import PolicyRetriever
        from .semantic_embeddings import SentenceTransformerEncoder
        from .semantic_indexing import load_semantic_index
        from .semantic_retriever import SemanticPolicyRetriever

        root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        config = LLMConfig.from_env(env_file or root / ".env")
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
        return cls(
            retriever,
            OpenAIChatCompletionsClient(config),
            model=config.model,
            rewrite_cache=RewriteCache(root / "cache" / "query_rewrites.json"),
            generation_cache=GeneratedAnswerCache(
                root / "cache" / "generated_answers.json"
            ),
        )

    def answer(
        self,
        latest_question: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> AgentResult:
        """Answer one question through the fixed pipeline, or raise a staged error."""

        question = latest_question.strip()
        if not question:
            raise ValueError("latest_question must not be blank")
        recent_history = select_recent_history(
            history,
            max_turns=self._max_history_turns,
        )

        try:
            rewritten_query, rewrite_source = self._rewrite(
                recent_history,
                question,
            )
        except Exception as error:
            if isinstance(error, AgentPipelineError):
                raise
            raise AgentPipelineError("rewrite", str(error)) from error

        try:
            evidence = tuple(
                self._retriever.search(rewritten_query, top_k=EVIDENCE_TOP_K)
            )
            if not evidence:
                raise RuntimeError("retrieval returned no evidence")
        except Exception as error:
            raise AgentPipelineError("retrieval", str(error)) from error

        try:
            generated = generate_grounded_answer(
                question,
                recent_history,
                evidence,
                self._client,
                model=self._model,
                cache=self._generation_cache,
                max_history_turns=self._max_history_turns,
            )
        except Exception as error:
            raise AgentPipelineError("generation", str(error)) from error

        validation = dict(generated["validation"])
        if not validation.get("valid", False):
            warnings = validation.get("warnings", [])
            detail = ", ".join(str(value) for value in warnings) or "invalid citations"
            raise AgentPipelineError("citation_validation", detail)

        return AgentResult(
            answer=str(generated["answer"]),
            citations=tuple(dict(source) for source in generated["sources"]),
            citation_ids=tuple(str(value) for value in generated["citation_ids"]),
            rewritten_query=rewritten_query,
            evidence=evidence,
            citation_validation=validation,
            rewrite_response_source=rewrite_source,
            generation_response_source=str(generated["response_source"]),
        )

    def _rewrite(
        self,
        history: Sequence[Mapping[str, str]],
        question: str,
    ) -> tuple[str, str]:
        key = rewrite_cache_key(
            model=self._model,
            history=history,
            latest_question=question,
            max_history_turns=self._max_history_turns,
        )
        cached = self._rewrite_cache.get(key) if self._rewrite_cache else None
        if cached is not None:
            return cached, "cache"

        rewritten = rewrite_or_keep(
            history,
            question,
            self._client,
            max_history_turns=self._max_history_turns,
        )
        if self._rewrite_cache:
            self._rewrite_cache.set(
                key,
                rewritten,
                {
                    "model": self._model,
                    "prompt_version": CONTEXTUALIZER_PROMPT_VERSION,
                },
            )
        return rewritten, "api"
