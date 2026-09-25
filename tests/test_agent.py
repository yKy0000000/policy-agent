from __future__ import annotations

import unittest

import numpy as np

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


class TimedRetriever(FixedRetriever):
    def __init__(self) -> None:
        super().__init__()
        self.timings = []

    def search(self, query: str, top_k: int = 5):
        results = super().search(query, top_k)
        self.timings.append(type("Timing", (), {"reranker_seconds": 0.01})())
        return results


class VectorRetriever(FixedRetriever):
    def __init__(self):
        super().__init__(results=[evidence(i) for i in range(1, 8)])

    def evidence_vectors(self, chunk_ids):
        return {chunk_id: np.eye(7)[int(chunk_id.split("-")[1]) - 1] for chunk_id in chunk_ids}

    def count_evidence_tokens(self, item):
        return 5


class FixedPipelineClient:
    def __init__(self, rewrite: str, answer: str) -> None:
        self.rewrite = rewrite
        self.answer = answer
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append((messages, max_tokens, temperature))
        return self.rewrite if max_tokens == 96 else self.answer


class MemoryCache:
    def __init__(self) -> None:
        self.entries = {}

    def get(self, key):
        return self.entries.get(key)

    def set(self, key, value, metadata):
        self.entries[key] = value


class UsageClient(FixedPipelineClient):
    def complete_with_usage(self, messages, *, max_tokens=96, temperature=0.0):
        answer = self.complete(messages, max_tokens=max_tokens, temperature=temperature)
        return answer, {"input_tokens": 10, "output_tokens": 4}


class AgentTests(unittest.TestCase):
    def test_coverage_mode_reads_top20_once_and_traces_selection(self) -> None:
        retriever = VectorRetriever()
        agent = PolicySupportAgent(retriever, FixedPipelineClient("standalone", "Answer [S1]."),
                                   model="test-model", evidence_mode="coverage_selector_v2")
        result = agent.answer("standalone")
        self.assertEqual(retriever.calls, [("standalone", 20)])
        self.assertEqual(result.trace.evidence_mode, "coverage_selector_v2")
        self.assertEqual(len(result.trace.evidence_original_ranks), result.trace.selected_k)
        self.assertTrue(result.trace.evidence_selection_steps[0]["candidates"])
        self.assertEqual(result.trace.evidence_token_count, 5 * result.trace.selected_k)

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
        self.assertEqual(caught.exception.trace.error_stage, "citation_validation")
        self.assertEqual(caught.exception.trace.generated_answer, "Answer [S99].")
        self.assertFalse(caught.exception.trace.citation_validation["valid"])
        self.assertGreaterEqual(caught.exception.trace.validation_seconds, 0.0)

    def test_trace_and_cache_do_not_change_answer_or_evidence(self) -> None:
        client = FixedPipelineClient("standalone", "Supported answer [S1].")
        agent = PolicySupportAgent(
            FixedRetriever(), client, model="test-model",
            rewrite_cache=MemoryCache(), generation_cache=MemoryCache(),
        )

        first = agent.answer("question")
        second = agent.answer("question")

        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.evidence, second.evidence)
        self.assertEqual(first.citations, second.citations)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual((first.trace.rewrite_source, first.trace.generation_source), ("api", "api"))
        self.assertEqual((second.trace.rewrite_source, second.trace.generation_source), ("cache", "cache"))
        self.assertEqual((first.trace.remote_llm_calls, second.trace.remote_llm_calls), (2, 0))
        self.assertEqual(first.trace.evidence_chunk_ids, tuple(item.chunk_id for item in first.evidence))
        for trace in (first.trace, second.trace):
            self.assertEqual(trace.original_query, "question")
            self.assertEqual(trace.generated_answer, "Supported answer [S1].")
            self.assertTrue(trace.citation_validation["valid"])
            for stage in ("rewrite", "retrieval", "generation", "validation", "total"):
                self.assertGreaterEqual(trace.to_dict()["latency_seconds"][stage], 0.0)
            self.assertIsNone(trace.rerank_seconds)  # Fake retriever has no timing signal.
            self.assertTrue(all(value is None for value in trace.to_dict()["token_usage"].values()))

    def test_failure_carries_partial_trace(self) -> None:
        client = FixedPipelineClient("standalone", "unused")
        agent = PolicySupportAgent(
            FixedRetriever(error=RuntimeError("reranker unavailable")),
            client, model="test-model",
        )

        with self.assertRaises(AgentPipelineError) as caught:
            agent.answer("question")

        trace = caught.exception.trace
        self.assertEqual(trace.error_stage, "retrieval")
        self.assertEqual(trace.rewritten_query, "standalone")
        self.assertEqual(trace.remote_llm_calls, 1)
        self.assertGreaterEqual(trace.retrieval_seconds, 0.0)
        self.assertGreaterEqual(trace.total_seconds, 0.0)
        self.assertIsNone(trace.generation_seconds)

    def test_provider_tokens_are_attached_to_the_correct_stage(self) -> None:
        agent = PolicySupportAgent(
            FixedRetriever(), UsageClient("standalone", "Answer [S1]."),
            model="test-model",
        )

        trace = agent.answer("question").trace

        self.assertEqual(trace.remote_llm_calls, 2)
        self.assertEqual(trace.rewrite_input_tokens, 10)
        self.assertEqual(trace.rewrite_output_tokens, 4)
        self.assertEqual(trace.generation_input_tokens, 10)
        self.assertEqual(trace.generation_output_tokens, 4)

    def test_rerank_timing_is_captured_when_retriever_reports_it(self) -> None:
        agent = PolicySupportAgent(
            TimedRetriever(), FixedPipelineClient("standalone", "Answer [S1]."),
            model="test-model",
        )

        trace = agent.answer("question").trace

        self.assertEqual(trace.rerank_seconds, 0.01)
        self.assertGreaterEqual(trace.retrieval_seconds, 0.0)

    def test_adaptive_mode_uses_one_top20_retrieval_and_records_budget(self) -> None:
        retriever = FixedRetriever(results=[evidence(i) for i in range(1, 21)])
        question = "What protections apply and who handles appeals?"
        client = FixedPipelineClient(question, "The policy describes a process [S6].")
        agent = PolicySupportAgent(retriever, client, model="test-model", adaptive_evidence=True)

        result = agent.answer(question)

        self.assertEqual(retriever.calls, [(question, 20)])
        self.assertGreater(result.trace.selected_k, 5)
        self.assertEqual(len(result.evidence), result.trace.selected_k)
        self.assertEqual(result.trace.evidence_mode, "adaptive_prefix_v1")
        self.assertEqual(result.trace.evidence_token_budget, 6000)
        self.assertIsNotNone(result.trace.evidence_expansion_reason)
        self.assertGreaterEqual(result.trace.evidence_selection_seconds, 0.0)
        self.assertEqual(result.trace.remote_llm_calls, 2)


if __name__ == "__main__":
    unittest.main()
