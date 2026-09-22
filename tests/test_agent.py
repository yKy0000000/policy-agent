from __future__ import annotations

import unittest

from src.agent import AgentPipelineError, PolicySupportAgent
from src.reranked_retriever import RerankedRetrievalResult


def evidence(rank: int) -> RerankedRetrievalResult:
    return RerankedRetrievalResult(
        reranker_score=float(6 - rank),
        chunk_id=f"chunk-{rank}",
        text=f"Policy evidence {rank}.",
        source_path=f"Policies/policy-{rank}.md",
        source_url=f"https://example.test/policy-{rank}",
        title=f"Policy {rank}",
        heading_path=(f"Heading {rank}",),
        chunk_index=rank,
        lexical_rank=rank,
        semantic_rank=rank,
    )


class FixedRetriever:
    def __init__(self, results=None, error: Exception | None = None) -> None:
        self.results = results if results is not None else [evidence(i) for i in range(1, 6)]
        self.error = error
        self.calls = []

    def search(self, query: str, top_k: int = 5):
        self.calls.append((query, top_k))
        if self.error:
            raise self.error
        return self.results[:top_k]


class FixedPipelineClient:
    def __init__(self, rewrite: str, answer: str) -> None:
        self.rewrite = rewrite
        self.answer = answer
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append((messages, max_tokens, temperature))
        return self.rewrite if max_tokens == 96 else self.answer


class AgentTests(unittest.TestCase):
    def test_single_turn_runs_the_complete_pipeline(self) -> None:
        client = FixedPipelineClient(
            "When can GitHub suspend an account?",
            "GitHub may suspend an account in supported circumstances [S1].",
        )
        retriever = FixedRetriever()
        agent = PolicySupportAgent(retriever, client, model="test-model")

        result = agent.answer("When can GitHub suspend an account?")

        self.assertEqual(
            retriever.calls,
            [("When can GitHub suspend an account?", 5)],
        )
        self.assertEqual(result.citation_ids, ("S1",))
        self.assertEqual(result.citations[0]["chunk_id"], "chunk-1")
        self.assertEqual(len(result.evidence), 5)
        self.assertTrue(result.citation_validation["valid"])

    def test_multi_turn_rewrite_drives_retrieval_and_history_reaches_generation(self) -> None:
        history = [
            {
                "role": "user",
                "content": "Does GitHub prohibit repositories that support malware?",
            },
            {
                "role": "assistant",
                "content": "Direct support of unlawful attacks is prohibited.",
            },
        ]
        rewritten = "Does that prohibition apply to legitimate security research?"
        client = FixedPipelineClient(
            rewritten,
            "Dual-use security research may be allowed, subject to policy limits [S2].",
        )
        retriever = FixedRetriever()
        agent = PolicySupportAgent(retriever, client, model="test-model")

        result = agent.answer("What if it is for security research?", history)

        self.assertEqual(result.rewritten_query, rewritten)
        self.assertEqual(retriever.calls, [(rewritten, 5)])
        generation_prompt = client.calls[1][0][1]["content"]
        self.assertIn(history[0]["content"], generation_prompt)
        self.assertIn("What if it is for security research?", generation_prompt)
        self.assertEqual(result.citation_ids, ("S2",))

    def test_supported_abstention_is_a_successful_answer(self) -> None:
        client = FixedPipelineClient(
            "Where is a specific repository physically stored?",
            "The provided published policies do not specify that location [S1].",
        )
        agent = PolicySupportAgent(FixedRetriever(), client, model="test-model")

        result = agent.answer("Where is my repository physically stored?")

        self.assertIn("do not specify", result.answer)
        self.assertTrue(result.citation_validation["valid"])

    def test_technical_failures_include_the_pipeline_stage(self) -> None:
        client = FixedPipelineClient("rewritten", "Answer [S1].")
        agent = PolicySupportAgent(
            FixedRetriever(error=RuntimeError("reranker unavailable")),
            client,
            model="test-model",
        )

        with self.assertRaises(AgentPipelineError) as caught:
            agent.answer("question")

        self.assertEqual(caught.exception.stage, "retrieval")
        self.assertIn("reranker unavailable", str(caught.exception))

    def test_invalid_model_citation_fails_at_validation_boundary(self) -> None:
        client = FixedPipelineClient("rewritten", "Answer [S99].")
        agent = PolicySupportAgent(FixedRetriever(), client, model="test-model")

        with self.assertRaises(AgentPipelineError) as caught:
            agent.answer("question")

        self.assertEqual(caught.exception.stage, "citation_validation")
        self.assertIn("invalid_citations", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
