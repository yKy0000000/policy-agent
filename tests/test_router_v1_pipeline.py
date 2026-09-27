from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from src.decomposer_v1 import DecomposerOutcome
from src.reranked_retriever import RerankedRetrievalResult
from src.router_v1 import DECOMPOSE, DIRECT, RouterDecision
from src.router_v1_pipeline import (
    DECOMPOSE_UNAVAILABLE,
    FIXED_DECOMPOSE,
    FIXED_DIRECT,
    INSUFFICIENT_SUBQUERY_STREAMS,
    ROUTED,
    RouterV1Pipeline,
    classify_attribution,
    merge_streams,
    run_stream,
)
from src.router_v1_trace import StreamResult


def ev(chunk_id: str, *, lexical_rank=None, semantic_rank=None, score: float = 1.0) -> RerankedRetrievalResult:
    return RerankedRetrievalResult(
        reranker_score=score,
        chunk_id=chunk_id,
        text=f"policy text for {chunk_id}",
        source_path=f"Policies/{chunk_id}.md",
        source_url=f"https://example.test/{chunk_id}",
        title=f"Policy {chunk_id}",
        heading_path=(chunk_id,),
        chunk_index=0,
        lexical_rank=lexical_rank,
        semantic_rank=semantic_rank,
    )


def stream(
    stream_id: str,
    chunk_ids,
    *,
    stream_type: str = "subquery",
    union=None,
    failure=None,
) -> StreamResult:
    evidence = tuple(ev(chunk_id, lexical_rank=index + 1) for index, chunk_id in enumerate(chunk_ids))
    return StreamResult(
        stream_id=stream_id,
        stream_type=stream_type,
        query_text=stream_id,
        lexical_candidate_ids=tuple(chunk_ids),
        semantic_candidate_ids=(),
        union_ids=tuple(union if union is not None else chunk_ids),
        reranked_ids=tuple(chunk_ids),
        stream_top5_ids=tuple(chunk_ids),
        evidence=evidence if failure is None else (),
        latency_seconds=0.0,
        rerank_latency_seconds=0.0,
        failure=failure,
    )


def decision(value: str, reason=None) -> RouterDecision:
    return RouterDecision(
        decision=value,
        raw_reason_code=reason,
        effective_reason_code=reason or "UNRECOGNIZED",
        reason_validity="valid" if reason else "missing",
        raw_response="{}",
        failure=None,
        fallback=False,
        schema_anomalies=(),
    )


def decomposer_outcome(subqueries, *, failure=None, fallback_reason=None) -> DecomposerOutcome:
    available = failure is None and len(subqueries) >= 2
    return DecomposerOutcome(
        called=True,
        available=available,
        subqueries=tuple(subqueries) if available else (),
        raw_subqueries=tuple(subqueries),
        removed=(),
        raw_response="{}",
        failure=failure,
        fallback_reason=fallback_reason or (None if available else "decomposer_failure"),
        latency_seconds=0.0,
    )


class FakeRouter:
    def __init__(self, value: RouterDecision) -> None:
        self.value = value
        self.calls = 0

    def decide(self, rewritten_query):
        self.calls += 1
        return self.value


class FakeDecomposer:
    def __init__(self, outcome: DecomposerOutcome) -> None:
        self.value = outcome
        self.calls = 0

    def decompose(self, rewritten_query):
        self.calls += 1
        return self.value


class ScriptedRetriever:
    def __init__(self, mapping, *, fail_queries=()) -> None:
        self.mapping = mapping
        self.fail = set(fail_queries)
        self.calls = []
        self.timings = []

    def search(self, query, top_k=5):
        self.calls.append((query, top_k))
        if query in self.fail:
            raise RuntimeError(f"retrieval failed for {query!r}")
        results = list(self.mapping.get(query, []))
        self.timings.append(
            SimpleNamespace(reranker_seconds=0.01, candidate_count=len(results), total_seconds=0.02)
        )
        return results[:top_k]


class StageClient:
    def __init__(self, *, rewrite="rewritten query", router=None, decomposer=None, answer="Answer [S1]."):
        self.rewrite = rewrite
        self.router = router
        self.decomposer = decomposer
        self.answer = answer
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append(max_tokens)
        if max_tokens == 512:
            return self.answer
        if max_tokens == 256:
            if self.decomposer is None:
                raise AssertionError("unexpected decomposer call")
            return self.decomposer
        if max_tokens == 96:
            if self.router is not None:
                return self.router
            return self.rewrite
        raise AssertionError(f"unexpected max_tokens {max_tokens}")


BASE = [ev("b1", lexical_rank=1), ev("b2", lexical_rank=2), ev("b3", lexical_rank=3)]


class MergeTests(unittest.TestCase):
    def test_three_stream_round_robin_order(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3", "b4", "b5"], stream_type="base"),
                stream("subquery_1", ["a1", "a2"]),
                stream("subquery_2", ["c1", "c2"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "a1", "c1", "b2", "a2"])
        self.assertEqual([item.source_stream for item in result.selections], ["base", "subquery_1", "subquery_2", "base", "subquery_1"])
        self.assertEqual([item.selection_order for item in result.selections], [1, 2, 3, 4, 5])

    def test_four_stream_round_robin_order(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3", "b4", "b5"], stream_type="base"),
                stream("subquery_1", ["a1", "a2"]),
                stream("subquery_2", ["c1", "c2"]),
                stream("subquery_3", ["d1", "d2"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "a1", "c1", "d1", "b2"])

    def test_duplicates_across_streams_are_skipped(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2"], stream_type="base"),
                stream("subquery_1", ["b1", "a1"]),
                stream("subquery_2", ["a1", "c1"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "a1", "c1", "b2"])
        duplicate_map = dict(result.duplicate_sources)
        self.assertEqual(duplicate_map["b1"], ("base", "subquery_1"))
        self.assertEqual(duplicate_map["a1"], ("subquery_1", "subquery_2"))

    def test_base_duplicate_selected_once_by_first_offering_stream(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3", "b4", "b5"], stream_type="base"),
                stream("subquery_1", ["b1", "b2"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "b2", "b3", "b4", "b5"])
        self.assertEqual(len({item.chunk_id for item in result.selections}), 5)
        sources = {item.chunk_id: item.source_stream for item in result.selections}
        self.assertEqual(sources["b1"], "base")
        self.assertEqual(sources["b2"], "subquery_1")

    def test_fully_duplicated_subquery_stream_contributes_nothing(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3"], stream_type="base"),
                stream("subquery_1", ["b1"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "b2", "b3"])
        self.assertEqual({item.source_stream for item in result.selections}, {"base"})

    def test_exhausted_stream_is_skipped(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3", "b4"], stream_type="base"),
                stream("subquery_1", ["b1"]),
                stream("subquery_2", ["c1"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "c1", "b2", "b3", "b4"])

    def test_fewer_than_five_unique_chunks(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2"], stream_type="base"),
                stream("subquery_1", ["a1"]),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "a1", "b2"])
        self.assertEqual(len(result.selections), 3)

    def test_failed_streams_are_not_merged(self) -> None:
        result = merge_streams(
            [
                stream("base", ["b1", "b2", "b3"], stream_type="base"),
                stream("subquery_1", [], failure="retrieval failed"),
            ]
        )
        self.assertEqual([item.chunk_id for item in result.final_evidence], ["b1", "b2", "b3"])


class AttributionTests(unittest.TestCase):
    def test_representation_gain(self) -> None:
        base = stream("base", ["b1", "b2"], stream_type="base", union=["b1", "b2"])
        merged = merge_streams([base, stream("subquery_1", ["a1"])])
        attribution = classify_attribution(merged, base, applicable=True)
        self.assertEqual(attribution.representation_gain_ids, ("a1",))
        self.assertEqual(attribution.selection_ranking_gain_ids, ())
        self.assertFalse(attribution.zero_evidence_gain)

    def test_selection_ranking_gain(self) -> None:
        base = stream("base", ["b1", "b2"], stream_type="base", union=["b1", "b2", "b9"])
        merged = merge_streams([base, stream("subquery_1", ["b9"])])
        attribution = classify_attribution(merged, base, applicable=True)
        self.assertEqual(attribution.representation_gain_ids, ())
        self.assertEqual(attribution.selection_ranking_gain_ids, ("b9",))
        self.assertFalse(attribution.zero_evidence_gain)

    def test_zero_evidence_gain(self) -> None:
        base = stream("base", ["b1", "b2"], stream_type="base", union=["b1", "b2"])
        merged = merge_streams([base, stream("subquery_1", ["b1", "b2"])])
        attribution = classify_attribution(merged, base, applicable=True)
        self.assertEqual(attribution.representation_gain_ids, ())
        self.assertEqual(attribution.selection_ranking_gain_ids, ())
        self.assertTrue(attribution.zero_evidence_gain)


class StreamRunnerTests(unittest.TestCase):
    def test_stream_records_candidates_and_ranks(self) -> None:
        retriever = ScriptedRetriever(
            {"q": [ev("x", lexical_rank=1, semantic_rank=2), ev("y", semantic_rank=1)]}
        )
        result = run_stream(retriever, "q", "base", "base")
        self.assertTrue(result.ok)
        self.assertEqual(result.lexical_candidate_ids, ("x",))
        self.assertEqual(result.semantic_candidate_ids, ("y", "x"))
        self.assertEqual(result.union_ids, ("x", "y"))
        self.assertEqual(result.stream_top5_ids, ("x", "y"))
        self.assertEqual(retriever.calls, [("q", 40)])
        self.assertAlmostEqual(result.rerank_latency_seconds, 0.01)

    def test_stream_failure_is_recorded(self) -> None:
        retriever = ScriptedRetriever({}, fail_queries={"q"})
        result = run_stream(retriever, "q", "subquery_1", "subquery")
        self.assertFalse(result.ok)
        self.assertIn("retrieval failed", result.failure or "")


class ArmTests(unittest.TestCase):
    def _pipeline(self, retriever, client, router=None, decomposer=None):
        return RouterV1Pipeline(
            retriever,
            client,
            model="test-model",
            router=router,
            decomposer=decomposer,
        )

    def test_fixed_direct_never_calls_router_or_decomposer(self) -> None:
        router = FakeRouter(decision(DECOMPOSE, "COVERAGE_SPLIT_RISK"))
        decomposer = FakeDecomposer(decomposer_outcome(["one", "two"]))
        retriever = ScriptedRetriever({"rewritten": BASE, "one": [ev("a1")], "two": [ev("c1")]})
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(FIXED_DIRECT, "raw?", [], "rewritten")
        self.assertEqual(result.executed_path, DIRECT)
        self.assertIsNone(result.router_decision)
        self.assertEqual(router.calls, 0)
        self.assertEqual(decomposer.calls, 0)
        self.assertEqual([item.chunk_id for item in result.evidence], ["b1", "b2", "b3"])

    def test_fixed_decompose_never_calls_router(self) -> None:
        router = FakeRouter(decision(DIRECT))
        decomposer = FakeDecomposer(decomposer_outcome(["target one", "target two"]))
        retriever = ScriptedRetriever(
            {
                "rewritten": BASE,
                "target one": [ev("a1", lexical_rank=1), ev("b1", lexical_rank=2)],
                "target two": [ev("c1", lexical_rank=1), ev("b2", lexical_rank=2)],
            }
        )
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(FIXED_DECOMPOSE, "raw?", [], "rewritten")
        self.assertEqual(router.calls, 0)
        self.assertEqual(result.executed_path, DECOMPOSE)
        self.assertTrue(result.counterfactual_decompose_available)
        self.assertEqual([item.chunk_id for item in result.evidence], ["b1", "a1", "c1", "b2", "b3"])

    def test_fixed_decompose_unavailable_is_not_a_decompose_result(self) -> None:
        decomposer = FakeDecomposer(
            decomposer_outcome([], failure="schema_invalid", fallback_reason="decomposer_failure")
        )
        retriever = ScriptedRetriever({"rewritten": BASE})
        pipeline = self._pipeline(retriever, StageClient(), decomposer=decomposer)
        result = pipeline.run_arm(FIXED_DECOMPOSE, "raw?", [], "rewritten")
        self.assertEqual(result.executed_path, DIRECT)
        self.assertEqual(result.fallback_reason, DECOMPOSE_UNAVAILABLE)
        self.assertFalse(result.decompose_available)
        self.assertFalse(result.counterfactual_decompose_available)

    def test_routed_obeys_direct_decision(self) -> None:
        router = FakeRouter(decision(DIRECT))
        decomposer = FakeDecomposer(decomposer_outcome(["one", "two"]))
        retriever = ScriptedRetriever({"rewritten": BASE})
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertEqual(router.calls, 1)
        self.assertEqual(decomposer.calls, 0)
        self.assertEqual(result.executed_path, DIRECT)
        self.assertEqual(result.router_decision, DIRECT)

    def test_routed_obeys_decompose_decision(self) -> None:
        router = FakeRouter(decision(DECOMPOSE, "COVERAGE_SPLIT_RISK"))
        decomposer = FakeDecomposer(decomposer_outcome(["target one", "target two"]))
        retriever = ScriptedRetriever(
            {
                "rewritten": BASE,
                "target one": [ev("a1", lexical_rank=1)],
                "target two": [ev("c1", lexical_rank=1)],
            }
        )
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertEqual(result.executed_path, DECOMPOSE)
        self.assertEqual(result.router_decision, DECOMPOSE)
        self.assertEqual(len(result.streams), 3)

    def test_one_subquery_stream_failure_still_decomposes(self) -> None:
        router = FakeRouter(decision(DECOMPOSE, "COVERAGE_SPLIT_RISK"))
        decomposer = FakeDecomposer(decomposer_outcome(["one", "two", "three"]))
        retriever = ScriptedRetriever(
            {
                "rewritten": BASE,
                "one": [ev("a1", lexical_rank=1)],
                "three": [ev("c1", lexical_rank=1)],
            },
            fail_queries={"two"},
        )
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertEqual(result.executed_path, DECOMPOSE)
        failures = [stream.failure for stream in result.streams if stream.stream_id == "subquery_2"]
        self.assertEqual(len(failures), 1)
        self.assertIsNotNone(failures[0])
        self.assertIn("c1", [item.chunk_id for item in result.evidence])

    def test_too_few_surviving_subquery_streams_fall_back_to_direct(self) -> None:
        router = FakeRouter(decision(DECOMPOSE, "COVERAGE_SPLIT_RISK"))
        decomposer = FakeDecomposer(decomposer_outcome(["one", "two"]))
        retriever = ScriptedRetriever({"rewritten": BASE, "one": [ev("a1")]}, fail_queries={"two"})
        pipeline = self._pipeline(retriever, StageClient(), router=router, decomposer=decomposer)
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertEqual(result.executed_path, DIRECT)
        self.assertEqual(result.fallback_reason, INSUFFICIENT_SUBQUERY_STREAMS)
        self.assertEqual([item.chunk_id for item in result.evidence], ["b1", "b2", "b3"])
        self.assertFalse(result.attribution.applicable)

    def test_base_stream_failure_is_a_retrieval_failure(self) -> None:
        router = FakeRouter(decision(DIRECT))
        retriever = ScriptedRetriever({"rewritten": BASE}, fail_queries={"rewritten"})
        pipeline = self._pipeline(retriever, StageClient(), router=router)
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertFalse(result.execution_success)
        self.assertEqual(result.error_stage, "retrieval")
        self.assertIsNone(result.answer)
        self.assertEqual(result.evidence, ())


class IntegrationTests(unittest.TestCase):
    def test_full_mocked_flow_and_direct_parity(self) -> None:
        router = FakeRouter(decision(DECOMPOSE, "COVERAGE_SPLIT_RISK"))
        decomposer = FakeDecomposer(decomposer_outcome(["target one", "target two"]))
        mapping = {
            "rewritten": BASE,
            "target one": [ev("a1", lexical_rank=1), ev("b1", lexical_rank=2)],
            "target two": [ev("c1", lexical_rank=1), ev("b2", lexical_rank=2)],
        }
        client = StageClient(rewrite="rewritten", answer="Grounded answer [S1].")
        retriever = ScriptedRetriever(mapping)
        pipeline = RouterV1Pipeline(
            retriever, client, model="test-model", router=router, decomposer=decomposer
        )
        run = pipeline.run_case("neutral raw question", arms=(ROUTED,))
        result = run.arm(ROUTED)
        self.assertEqual(run.shared_rewrite, "rewritten")
        self.assertEqual(result.executed_path, DECOMPOSE)
        self.assertEqual([item.chunk_id for item in result.evidence], ["b1", "a1", "c1", "b2", "b3"])
        self.assertTrue(result.attribution.applicable)
        self.assertEqual(result.attribution.representation_gain_ids, ("a1", "c1"))
        self.assertTrue(result.citation_validation["valid"])
        trace = result.trace.to_dict()
        self.assertEqual(trace["input"]["shared_rewrite"], "rewritten")
        self.assertEqual(trace["input"]["rewrite_source"], "api")
        self.assertEqual(trace["router"]["parsed_decision"], DECOMPOSE)
        self.assertEqual(trace["decomposer"]["validated_subqueries"], ["target one", "target two"])
        self.assertEqual(len(trace["streams"]), 3)
        self.assertEqual(trace["merge"]["final_evidence_ids"], ["b1", "a1", "c1", "b2", "b3"])
        self.assertEqual(trace["outcome"]["executed_path"], DECOMPOSE)
        self.assertTrue(trace["outcome"]["execution_success"])

        direct = pipeline.run_arm(FIXED_DIRECT, "neutral raw question", [], "rewritten")
        baseline = retriever.search("rewritten", top_k=5)
        self.assertEqual(
            [item.chunk_id for item in direct.evidence],
            [item.chunk_id for item in baseline],
        )

    def test_real_router_and_decomposer_stages_record_usage(self) -> None:
        router_payload = '{"decision": "DECOMPOSE", "reason_code": "COVERAGE_SPLIT_RISK"}'
        decomposer_payload = json.dumps({"subqueries": ["target one", "target two"]})
        client = StageClient(
            router=router_payload,
            decomposer=decomposer_payload,
            answer="Grounded answer [S1].",
        )
        retriever = ScriptedRetriever(
            {
                "rewritten": BASE,
                "target one": [ev("a1", lexical_rank=1)],
                "target two": [ev("c1", lexical_rank=1)],
            }
        )
        pipeline = RouterV1Pipeline(retriever, client, model="test-model")
        result = pipeline.run_arm(ROUTED, "raw?", [], "rewritten")
        self.assertEqual(result.router_decision, DECOMPOSE)
        self.assertEqual(result.executed_path, DECOMPOSE)
        stages = [call.stage for call in result.trace.model_calls]
        self.assertEqual(stages, ["router", "decomposer", "generation"])
        self.assertEqual(result.trace.router.effective_reason_code, "COVERAGE_SPLIT_RISK")
        self.assertEqual(result.trace.decomposer.validated_subqueries, ("target one", "target two"))


if __name__ == "__main__":
    unittest.main()
