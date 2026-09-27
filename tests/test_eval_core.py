"""Canonical benchmark, component boundaries, and frozen regression oracles."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace

from eval.core.answer_eval import AnswerEvaluator, FrozenAnswerJudge, frozen_fixed_baseline_complete
from eval.core.benchmark import load_benchmark
from eval.core.context_eval import ContextEvaluator
from eval.core.economics import EconomicsEvaluator
from eval.core.historical import FrozenReplayPipeline
from eval.core.pipeline import ContextSelection, Generation, Pipeline, UnionByChunkId
from eval.core.retrieval_eval import RetrievalEvaluator
from eval.core.runner import ExperimentRunner
from eval.core.schemas import Evidence, PipelineResult, Requirement


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_benchmark()

    def test_frozen_identity_and_distinct_denominators(self):
        benchmark = self.benchmark
        self.assertEqual((len(benchmark.cases), benchmark.original_fact_count, benchmark.query_required_count), (50, 239, 208))
        self.assertEqual(len(benchmark.by_id()), 50)
        self.assertEqual(len({fact.fact_id for case in benchmark.cases for fact in case.original_rubric_facts}), 239)
        self.assertTrue(all(set(case.query_required_aspects) <= set(case.original_fact_ids) for case in benchmark.cases))
        self.assertEqual(benchmark.cases[0].case_id, "VAL-001-001")

    def test_result_roundtrip_with_optional_requirements_and_provenance(self):
        original = PipelineResult("case", "pipeline", "question", "question",
            requirements=[Requirement("r1", "first"), Requirement("r2", "second")],
            retrieval_by_requirement={"r2": [Evidence("chunk", query_id="r2", query_ids=("r2",))]},
            retrieval_candidates=[Evidence("chunk", query_id="r2", heading_path=("Heading",), retrieval_score=0.7)],
            selected_evidence=[Evidence("chunk", query_id="r2")],
            component_provenance={"retriever": "per_requirement_v1", "model": "m"})
        decoded = PipelineResult.from_dict(json.loads(json.dumps(original.to_dict())))
        self.assertEqual(decoded.to_dict(), original.to_dict())
        self.assertEqual(decoded.retrieval_candidates[0].query_id, "r2")


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_benchmark()
        cls.baseline = frozen_fixed_baseline_complete()

    def report(self, arm, pipeline_id):
        pipeline = FrozenReplayPipeline(pipeline_id, arm)
        return ExperimentRunner(self.benchmark, pipeline,
            AnswerEvaluator(FrozenAnswerJudge(arm), self.baseline)).run({"pipeline_id": pipeline_id, "execution": "frozen_replay"})

    def test_fixed_top5_exact_replay(self):
        report = self.report("fixed_top5", "bge_fixed_top5")
        r, c, a, e = (report.retrieval["summary"], report.context["summary"],
                      report.answer["summary"], report.economics["summary"])
        self.assertEqual((r["facts"], r["candidate_available"], r["candidate_complete_cases"], r["ranked_top5"]), (239, 235, 49, 224))
        self.assertEqual((c["required_aspects"], c["required_covered"], c["context_complete_cases"], c["evidence_tokens"]), (208, 193, 46, 91699))
        self.assertEqual((a["required_covered"], a["query_required_complete_cases"], a["confirmed_complete_regressions_vs_fixed"]), (196, 43, 0))
        self.assertEqual((e["provider_input_tokens"], e["provider_output_tokens"], e["provider_tokens_per_query"]), (110674, 15982, 2533.12))
        self.assertEqual(e["latency_rows"], 0)

    def test_selector_same_runner_and_evaluators(self):
        report = self.report("coverage_selector_v2", "bge_coverage_selector_v2")
        r, c, a, e = (report.retrieval["summary"], report.context["summary"],
                      report.answer["summary"], report.economics["summary"])
        self.assertEqual((r["candidate_available"], r["ranked_top5"]), (235, 224))
        self.assertEqual((c["required_covered"], c["context_complete_cases"], c["evidence_tokens"]), (195, 47, 125648))
        self.assertEqual((a["required_covered"], a["query_required_complete_cases"], a["confirmed_complete_regressions_vs_fixed"]), (196, 44, 0))
        self.assertEqual((e["provider_input_tokens"], e["provider_output_tokens"], e["provider_tokens_per_query"]), (147045, 17008, 3281.06))
        self.assertTrue(all(row.component_provenance["execution"] == "frozen_replay" for row in report.pipeline_results))

    def test_denominator_boundaries(self):
        case = self.benchmark.cases[0]
        result = FrozenReplayPipeline("bge_fixed_top5", "fixed_top5").run(case)
        retrieval = RetrievalEvaluator().evaluate(case, result)
        context = ContextEvaluator().evaluate(case, result)
        answer = AnswerEvaluator(FrozenAnswerJudge("fixed_top5")).evaluate(case, result)
        self.assertEqual(retrieval["total"], len(case.original_rubric_facts))
        self.assertEqual(context["required_total"], len(case.query_required_aspects))
        self.assertEqual(answer["required_total"], len(case.query_required_aspects))
        self.assertEqual(retrieval["denominator"], "original_rubric_facts")
        self.assertEqual(context["denominator"], answer["denominator"])
        # A frozen quality verdict cannot be silently applied to a changed answer.
        altered = replace(result, component_provenance={**result.component_provenance, "execution": "live"})
        self.assertEqual(AnswerEvaluator(FrozenAnswerJudge("fixed_top5")).evaluate(case, altered)["status"], "judge_error")


class PipelineBoundaryTests(unittest.TestCase):
    def test_live_generation_adapter_uses_shared_result_contract(self):
        from eval.core.product_components import ProjectContextBuilder, ProjectGenerator, ProjectRewriter, ProjectValidator

        class FakeScorer:
            def count_tokens(self, text): return len(text.split())

        class FakeClient:
            def complete_with_usage(self, messages, *, max_tokens, temperature):
                self.messages = messages
                return "Policy answer [S1]", {"input_tokens": 12, "output_tokens": 5}

        client = FakeClient()
        rewriter = ProjectRewriter(client, "single_turn_identity")
        self.assertEqual(rewriter.rewrite("question", ()), "question")
        evidence = [Evidence("chunk", text="Policy source text", title="Policy", source_path="policy.md", source_url="https://example.test/policy", reranker_score=1.0)]
        selection = ProjectContextBuilder("fixed_top5", FakeScorer(), None).build("question", evidence)
        generation = ProjectGenerator(client, "test-model", rewriter,
            {"input_per_million": 0.15, "output_per_million": 0.6}).generate("question", (), selection)
        validation = ProjectValidator().validate(generation.answer, selection.evidence, generation.citations)
        self.assertTrue(validation["valid"])
        self.assertEqual((generation.provider_input_tokens, generation.provider_output_tokens), (12, 5))
        self.assertEqual(generation.citations[0]["chunk_id"], "chunk")

    def test_optional_multi_requirement_flow_without_gold_leakage(self):
        case = load_benchmark().cases[0]

        class Rewrite:
            def rewrite(self, query, history): return query

        class Plan:
            def plan(self, query): return [Requirement("r1", query + " part 1"), Requirement("r2", query + " part 2")]

        class Retrieve:
            def retrieve(self, query, requirement_id):
                return [Evidence("shared", query_id=requirement_id, text="support"),
                        Evidence(requirement_id, query_id=requirement_id, text="support")]

        class Rerank:
            def rerank(self, query, requirements, candidates):
                return [replace(item, rank=index, reranker_score=1 / index) for index, item in enumerate(candidates, 1)]

        class Context:
            def build(self, query, ranked): return ContextSelection(ranked[:2], "context", 10)

        class Generate:
            def generate(self, query, history, selection): return Generation("answer", [], 3, 4, 0.001)

        class Validate:
            def validate(self, answer, selected, citations): return {"valid": True}

        pipeline = Pipeline("future_stub", Rewrite(), Plan(), Retrieve(), UnionByChunkId(), Rerank(), Context(), Generate(), Validate(), {"test": True})
        result = pipeline.run(case)
        self.assertEqual(result.status, "complete")
        self.assertEqual([r.requirement_id for r in result.requirements], ["r1", "r2"])
        self.assertEqual({row.chunk_id for row in result.retrieval_candidates}, {"shared", "r1", "r2"})
        self.assertEqual(set(result.retrieval_by_requirement), {"r1", "r2"})
        self.assertEqual(next(row for row in result.retrieval_candidates if row.chunk_id == "shared").query_ids, ("r1", "r2"))
        self.assertEqual(result.provider_input_tokens, 3)
        self.assertEqual(EconomicsEvaluator().evaluate(result)["provider_total_tokens"], 7)


if __name__ == "__main__":
    unittest.main()
