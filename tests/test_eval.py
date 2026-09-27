"""Long-lived invariants for the frozen evidence evaluation."""

from __future__ import annotations

import ast
import hashlib
import json
import random
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from eval.metrics import (POLICIES, answer_quality_key, evidence_utilization,
                          score_facts, select_answer_oracle, select_oracle)
from eval.analyze_strategy import analyze as analyze_strategy
from eval.analyze_dynamic_k import (CONFIGS as DYNAMIC_CONFIGS, DynamicConfig,
                                   _relevance as dynamic_relevance,
                                   analyze as analyze_dynamic_k,
                                   select_dynamic)
from eval.run_answer_eval import (_V3Cache, _parse_judge, _run_v3_generation,
                                  _score_v3_answer,
                                  broad_v3_main, build_v3_plan)
from eval.run_evidence_eval import OUTPUT, ROOT, evaluate, load_inputs
from eval.run_validation import (adaptive_decision, classify_stop, direct_support_map,
                                 quality_gates, _generation_identity, _judge_case,
                                 _get_judgment, _prepared_public_row, _unique_routes,
                                 _fingerprint_changes, _material_prepared_identity)
from eval.analyze_evidence_geometry import (GAP_CATEGORIES, audit_disagreements,
                                            build_local_windows, build_top1_subtrees,
                                            fragmentation_signal, min_cardinality_cover,
                                            min_token_cover, overlap_aware_merge,
                                            support_groups, _answer_conversion_gap,
                                            _attribute_gap_fact, _cover_block,
                                            _prefix_status, _sensitivity, _tail_baseline)
from eval.compare_rerankers import (complete_at_k, coverage_at_k, deepest_gold_rank,
                                    evaluate_model, gold_rank_rows, length_bias,
                                    rank_histogram, summarize_model, tail_rank_movement,
                                    token_view, compare, _verdict)
import eval.run_reranker_transfer_eval as transfer
import eval.run_generation_utilization_eval as util
import eval.run_measurement_validity_audit as mva
import eval.run_measurement_validity_audit_v2 as mva2
import eval.finalize_measurement_validity as fmv
import eval.run_oracle_repair_v1 as repair
import eval.finalize_oracle_repair as repair_final
import eval.run_semantic_gap_discrimination_v1 as sgd
import eval.run_task_conditioned_action_v1 as tca
import eval.run_decision_execution_coupling_v1 as dec
import eval.run_stage0_replay as stage0
from src.llm_client import LLMConfig
import numpy as np


def _check_frozen_inputs_and_result_schema() -> None:
    benchmark, rubric, frozen, strategies, facts = load_inputs()
    assert len(benchmark["cases"]) == len(frozen["cases"]) == len(strategies["cases"]) == 16
    assert sum(map(len, facts.values())) == 92
    assert len({fact["fact_id"] for fact in rubric["facts"]}) == len(rubric["facts"])
    report = evaluate()
    assert set(report) == {"schema_version", "name", "oracle_warning", "source_sha256",
                           "case_count", "required_fact_count", "candidate_pool", "policies",
                           "oracle", "taxonomy_counts", "cases"}
    assert report["schema_version"] == 1
    assert report == json.loads(OUTPUT.read_text(encoding="utf-8"))


def _check_fact_coverage_completion_and_post_completion_tokens() -> None:
    facts = [{"fact_id": "a", "direct_chunk_ids": {"x"}},
             {"fact_id": "b", "direct_chunk_ids": {"y", "z"}}]
    chunks = [{"chunk_id": "x", "token_count": 3},
              {"chunk_id": "y", "token_count": 5},
              {"chunk_id": "z", "token_count": 7}]
    incomplete = score_facts(facts, chunks[:1])
    assert incomplete["coverage"] == .5
    assert incomplete["missing_fact_ids"] == ["b"]
    assert incomplete["first_complete_k"] is None
    assert incomplete["post_completion_evidence_tokens"] is None
    complete = score_facts(facts, chunks)
    assert complete["fact_complete"] and complete["first_complete_k"] == 2
    assert complete["post_completion_evidence_tokens"] == 7


def _check_oracle_lexicographic_choice_and_exact_tie() -> None:
    options = {name: {"covered_count": count, "evidence_tokens": tokens, "selected_k": k}
               for name, count, tokens, k in zip(POLICIES, (3, 4, 4), (10, 20, 15), (5, 8, 7))}
    assert select_oracle(options)["selected_strategy"] == "coverage_selector_v2"
    options["adaptive_prefix_v1"] = dict(options["coverage_selector_v2"])
    choice = select_oracle(options)
    assert choice["selected_strategy"] is None
    assert choice["co_optimal_strategies"] == list(POLICIES[1:])


def _check_known_frozen_baseline() -> None:
    report = evaluate()
    candidate = report["candidate_pool"]
    assert (candidate["covered_facts"], candidate["total_facts"],
            candidate["fact_complete_cases"]) == (89, 92, 14)
    assert candidate["ceiling_case_ids"] == ["V3-03", "V3-11"]
    expected = {
        "fixed_top5": (.749, .750, 7, 27274, 6653),
        "adaptive_prefix_v1": (.930, .935, 12, 50530, 19013),
        "coverage_selector_v2": (.873, .880, 10, 41134, 13371),
    }
    for name, (macro, micro, complete, tokens, post) in expected.items():
        item = report["policies"][name]
        assert (round(item["macro_fact_coverage"], 3), round(item["micro_fact_coverage"], 3),
                item["fact_complete_cases"], item["total_evidence_tokens"],
                item["post_completion_evidence_tokens"]) == (macro, micro, complete, tokens, post)
    oracle = report["oracle"]
    assert (round(oracle["macro_fact_coverage"], 3), round(oracle["micro_fact_coverage"], 3),
            oracle["fact_complete_cases"], oracle["total_evidence_tokens"],
            oracle["token_savings_vs_v1"], round(oracle["token_savings_fraction_vs_v1"], 3)) == (
                .930, .935, 12, 40073, 10457, .207)
    assert oracle["unique_winners"] == dict(zip(POLICIES, (5, 4, 3)))
    assert len(oracle["exact_ties"]) == 4
    assert next(row for row in report["cases"] if row["case_id"] == "V3-01")["taxonomy"] == "candidate_present_beyond_top20"


def _check_production_does_not_import_eval_or_oracle() -> None:
    for path in (ROOT / "src").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("eval") for alias in node.names), path
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("eval"), path


class FrozenEvalTests(unittest.TestCase):
    test_frozen_inputs_and_result_schema = staticmethod(_check_frozen_inputs_and_result_schema)
    test_fact_coverage_completion_and_post_completion_tokens = staticmethod(_check_fact_coverage_completion_and_post_completion_tokens)
    test_oracle_lexicographic_choice_and_exact_tie = staticmethod(_check_oracle_lexicographic_choice_and_exact_tie)
    test_known_frozen_baseline = staticmethod(_check_known_frozen_baseline)
    test_production_does_not_import_eval_or_oracle = staticmethod(_check_production_does_not_import_eval_or_oracle)


class ControlledAnswerEvalTests(unittest.TestCase):
    def test_frozen_source_review_and_strategy_study(self) -> None:
        results = json.loads((Path(__file__).resolve().parents[1] /
                              "eval/results/answer_eval_results.json").read_text(encoding="utf-8"))
        section = results["broad_v3_controlled"]
        self.assertEqual(section["adjudication_status"], "frozen_offline_source_review")
        decisions = section["adjudication"]
        self.assertEqual(len(decisions["facts"]), 11)
        self.assertEqual(len(decisions["claims"]), 8)
        self.assertEqual(sum(x["classification"] == "evidence_mapping_gap"
                             for x in decisions["facts"]), 10)
        study = analyze_strategy()
        self.assertEqual(study["development_labels"], {
            "fixed_sufficient": 11, "escalation_needed": 4, "ambiguous": 1})
        self.assertEqual(study["candidate_dev_summary"]["grounded_fact_regret_vs_v1"], 0)
        self.assertEqual(study["candidate_dev_summary"]["token_saving_vs_v1"], 7757)
        self.assertEqual(study["second_stage_conclusion"],
                         "insufficient evidence for second-stage routing rule")

    def test_dedup_plan_and_stable_keys(self) -> None:
        first, second = build_v3_plan("test-model"), build_v3_plan("test-model")
        self.assertEqual(len(first), 16)
        self.assertEqual(sum(len(case["groups"]) for case in first), 42)
        self.assertEqual(
            [[case["variants"][name]["generation_key"] for name in POLICIES]
             for case in first],
            [[case["variants"][name]["generation_key"] for name in POLICIES]
             for case in second],
        )
        self.assertEqual(len(first[8]["groups"]), 1)  # V3-09: all three prompts identical.
        self.assertNotIn("oracle", first[0]["variants"])
        self.assertNotEqual(first[0]["variants"][POLICIES[0]]["request_key"],
                            first[0]["variants"][POLICIES[1]]["request_key"])

    def test_generation_cache_resumes_without_duplicate_call(self) -> None:
        class Client:
            calls = 0

            def complete_with_usage(self, messages, *, max_tokens, temperature):
                self.calls += 1
                return "A policy answer [S1]", {"input_tokens": 10, "output_tokens": 5}

        case = build_v3_plan("test-model")[0]
        with tempfile.TemporaryDirectory() as directory:
            client = Client()
            cache = _V3Cache(Path(directory) / "generation.json")
            first = _run_v3_generation(case, POLICIES[0], cache, client, "test-model")
            second = _run_v3_generation(case, POLICIES[0],
                                        _V3Cache(cache.path), client, "test-model")
            self.assertEqual(client.calls, 1)
            self.assertEqual(first["response_source"], "api")
            self.assertEqual(second["response_source"], "cache")
            self.assertEqual(first["generation_hash"], second["generation_hash"])

    def test_fact_judgment_schema_and_utilization_denominator(self) -> None:
        raw = json.dumps({"answers": {"A": {
            "facts": [{"fact_id": "F1", "status": "covered", "citation_status": "supported"},
                      {"fact_id": "F2", "status": "missing", "citation_status": "not_applicable"}],
            "claims": [{"text": "Policy claim", "support_status": "supported",
                        "citation_status": "supported"}],
        }}})
        parsed = _parse_judge(raw, {"A"}, {"F1", "F2"})
        self.assertEqual(parsed["A"]["facts"][0]["status"], "covered")
        self.assertEqual(evidence_utilization(["F1", "F2"], ["F1"])["rate"], .5)
        self.assertEqual(evidence_utilization(["F1"], ["F1", "F2"])["rate"], 1.0)
        self.assertIsNone(evidence_utilization([], ["F1"])["rate"])

    def test_answer_oracle_uses_tokens_only_after_quality(self) -> None:
        def option(covered, tokens, unsupported=0):
            return {"evidence_tokens": tokens, "quality": {
                "fact_complete": covered == 2, "covered_count": covered,
                "synthesis_error_count": 0, "fact_citation_supported_count": covered,
                "supported_claim_rate": 1.0 if not unsupported else .5,
                "claims": {"contradicted": 0, "unsupported": unsupported,
                           "partial": 0, "supported": 2},
            }}

        options = {POLICIES[0]: option(1, 100), POLICIES[1]: option(2, 300),
                   POLICIES[2]: option(2, 200, unsupported=1)}
        self.assertEqual(select_answer_oracle(options)["selected_strategy"], POLICIES[1])
        options[POLICIES[2]] = option(2, 200)
        self.assertEqual(answer_quality_key(options[POLICIES[1]]),
                         answer_quality_key(options[POLICIES[2]]))
        self.assertEqual(select_answer_oracle(options)["selected_strategy"], POLICIES[2])
        options[POLICIES[0]] = option(2, 50)
        options[POLICIES[0]]["quality"].update(grounded_fact_complete=False,
                                               grounded_covered_count=1)
        options[POLICIES[1]]["quality"].update(grounded_fact_complete=True,
                                               grounded_covered_count=2)
        options[POLICIES[2]]["quality"].update(grounded_fact_complete=True,
                                               grounded_covered_count=2)
        self.assertEqual(select_answer_oracle(options)["selected_strategy"], POLICIES[2])

    def test_judge_coverage_outside_frozen_evidence_mapping_requires_review(self) -> None:
        case = build_v3_plan("test-model")[0]
        strategy = POLICIES[0]
        case["variants"][strategy]["generation"] = {
            "citation_validation": {"valid": True}, "generation_hash": "test-answer"}
        judged = {"facts": [{"fact_id": fact["fact_id"], "status": "covered",
                             "citation_status": "supported"} for fact in case["facts"]],
                  "claims": [{"text": "Policy claim", "support_status": "unsupported",
                              "citation_status": "missing"}]}
        result = _score_v3_answer(case, strategy, judged)
        self.assertTrue(result["review_required"])
        self.assertEqual(set(result["quality"]["answered_without_mapped_evidence_fact_ids"]),
                         {fact["fact_id"] for fact in case["facts"]})
        self.assertIsNone(result["quality"]["evidence_utilization"]["rate"])
        self.assertEqual({item["cause"] for item in result["claim_diagnosis"]},
                         {"grounding_error", "citation_error"})
        first_fact = case["facts"][0]["fact_id"]
        reviewed = _score_v3_answer(case, strategy, judged, {first_fact: {
            "generation_hash": "test-answer", "classification": "evidence_mapping_gap",
            "source_chunk_id": case["variants"][strategy]["chunks"][0]["chunk_id"]}})
        self.assertEqual(reviewed["quality"]["grounded_covered_count"], 1)

    def test_full_offline_simulation_and_resume(self) -> None:
        class FakeClient:
            generation_calls = 0
            judge_calls = 0

            def __init__(self, config):
                pass

            def complete_with_usage(self, messages, *, max_tokens, temperature):
                if "INPUT:\n" not in messages[-1]["content"]:
                    self.generation_calls += 1
                    return "A short policy answer [S1]", {"input_tokens": 10, "output_tokens": 5}
                self.judge_calls += 1
                payload = json.loads(messages[-1]["content"].split("INPUT:\n", 1)[1])
                answers = {}
                for label in payload["answers"]:
                    facts = [{"fact_id": fact["fact_id"],
                              "status": "covered" if index == 0 else "missing",
                              "citation_status": "supported" if index == 0 else "not_applicable"}
                             for index, fact in enumerate(payload["required_facts"])]
                    answers[label] = {"facts": facts, "claims": [
                        {"text": "A short policy answer", "support_status": "supported",
                         "citation_status": "supported"}]}
                return json.dumps({"answers": answers}), {"input_tokens": 20, "output_tokens": 10}

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            args = ["--generation-cache", str(base / "generation.json"),
                    "--judge-cache", str(base / "judge.json"),
                    "--json-output", str(base / "results.json"),
                    "--summary-output", str(base / "summary.md"),
                    "--review-output", str(base / "review.md")]
            config = LLMConfig(api_key="fake", base_url="https://example.invalid",
                               model="fake-model")
            with patch("eval.run_answer_eval.LLMConfig.from_env", return_value=config), \
                 patch("eval.run_answer_eval.OpenAIChatCompletionsClient", FakeClient):
                self.assertEqual(broad_v3_main(args), 0)
                report = json.loads((base / "results.json").read_text(encoding="utf-8"))
                section = report["broad_v3_controlled"]
                self.assertEqual(section["status"], "complete")
                self.assertEqual(len(section["cases"]), 16)
                self.assertEqual(section["usage"]["generation_api_calls"], 42)
                self.assertEqual(section["usage"]["judge_api_calls"], 16)
                self.assertEqual(section["usage"]["dedup_reuses"], 6)
                self.assertEqual(broad_v3_main(args), 0)
                second = json.loads((base / "results.json").read_text(encoding="utf-8"))
                self.assertEqual(second["broad_v3_controlled"]["usage"]["generation_api_calls"], 0)
                self.assertEqual(second["broad_v3_controlled"]["usage"]["judge_api_calls"], 0)


class ValidationBenchmarkTests(unittest.TestCase):
    """Corpus-only invariants; these tests do not execute any strategy."""

    @classmethod
    def setUpClass(cls) -> None:
        base = ROOT / "eval/validation"
        cls.queries_path = base / "broad_queries_validation_v1.json"
        cls.rubric_path = base / "broad_atomic_facts_validation_v1.json"
        cls.metadata = json.loads((base / "validation_v1_metadata.json").read_text(encoding="utf-8"))
        cls.queries = json.loads(cls.queries_path.read_text(encoding="utf-8"))
        cls.rubric = json.loads(cls.rubric_path.read_text(encoding="utf-8"))

    def test_unique_cases_and_development_separation(self) -> None:
        cases = self.queries["cases"]
        development = json.loads((ROOT / "eval/broad_queries_v3_adjudicated.json")
                                 .read_text(encoding="utf-8"))["cases"]
        ids = [case["case_id"] for case in cases]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(case_id.startswith("VAL-001-") for case_id in ids))
        self.assertFalse(set(ids) & {case["case_id"] for case in development})
        self.assertEqual(len({case["query"] for case in cases}), 50)
        self.assertEqual(ids, [case["case_id"] for case in self.rubric["cases"]])

    def test_required_facts_and_direct_corpus_support(self) -> None:
        corpus = (ROOT / "data/site-policy/Policies").resolve()
        fact_ids = []
        normalize = lambda value: re.sub(r"\s+", " ", value).strip()
        for query, case in zip(self.queries["cases"], self.rubric["cases"]):
            self.assertTrue(case["core_requirement"])
            self.assertGreaterEqual(len(case["facts"]), 4)
            self.assertLessEqual(len(case["facts"]), 8)
            documents = set()
            for fact in case["facts"]:
                with self.subTest(fact_id=fact["fact_id"]):
                    fact_ids.append(fact["fact_id"])
                    self.assertEqual(fact["requirement"], "required")
                    self.assertTrue(fact["statement"])
                    self.assertTrue(fact["support"])
                    self.assertTrue(any(item["entailment"] == "direct"
                                        for item in fact["support"]))
                    for support in fact["support"]:
                        self.assertEqual(support["entailment"], "direct")
                        path = (corpus / support["document"]).resolve()
                        self.assertTrue(path.is_relative_to(corpus))
                        source = path.read_text(encoding="utf-8")
                        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                                         support["document_sha256"])
                        self.assertIn(normalize(support["source_excerpt"]), normalize(source))
                        if "context_excerpt" in support:
                            self.assertIn(normalize(support["context_excerpt"]),
                                          normalize(source))
                        self.assertTrue(support["section"] == "document body" or
                                        support["section"] in source)
                        documents.add(support["document"])
            self.assertEqual(sorted(documents), query["source_documents"])
        self.assertEqual(len(fact_ids), self.rubric["required_fact_count"])
        self.assertEqual(len(fact_ids), len(set(fact_ids)))
        self.assertEqual(self.metadata["evidence_review"]["unresolved"], 0)

    def test_frozen_hashes_and_preregistration(self) -> None:
        metadata = self.metadata
        self.assertEqual(self.queries["status"], "frozen")
        self.assertEqual(self.rubric["status"], "frozen")
        self.assertEqual(metadata["role"], "untouched_validation")
        self.assertEqual(metadata["status"], "frozen")
        self.assertEqual(hashlib.sha256(self.queries_path.read_bytes()).hexdigest(),
                         metadata["dataset"]["queries_sha256"])
        self.assertEqual(hashlib.sha256(self.rubric_path.read_bytes()).hexdigest(),
                         metadata["dataset"]["rubric_sha256"])
        config = ROOT / metadata["frozen_strategy"]["config_path"]
        self.assertEqual(hashlib.sha256(config.read_bytes()).hexdigest(),
                         metadata["frozen_strategy"]["config_sha256"])
        self.assertEqual(metadata["frozen_strategy"]["fixed_stop_min_top5_score"], 2.5)
        gates = metadata["preregistration"]["primary_quality_gates"]
        self.assertEqual(gates["grounded_micro_fact_coverage"]["maximum_regret_absolute"], .02)
        self.assertEqual(gates["grounded_fact_complete_cases"]["maximum_case_deficit"], 1)
        self.assertIn("unsupported_or_contradicted_claims", gates)
        self.assertIn("secondary_efficiency_after_quality_gates", metadata["preregistration"])

    def test_frozen_direct_support_maps_to_current_index(self) -> None:
        index = json.loads((ROOT / "cache/policy_index.json").read_text(encoding="utf-8"))
        mapping = direct_support_map(self.rubric, index["chunks"])
        self.assertEqual(len(mapping), 239)
        self.assertTrue(all(mapping.values()))


class ValidationRunnerTests(unittest.TestCase):
    def test_runtime_fingerprint_changes_are_explicit(self) -> None:
        self.assertEqual(_fingerprint_changes({"index": "a", "selector": "b"},
                                              {"index": "a", "selector": "b"}), [])
        self.assertEqual(_fingerprint_changes({"index": "a", "selector": "b"},
                                              {"index": "c", "selector": "b"}), ["index"])
        self.assertEqual(_fingerprint_changes({"index": "a"},
                                              {"index": "a", "selector": "b"}), ["selector"])

    def test_load_prepared_rejects_real_runtime_change(self) -> None:
        import eval.run_validation as validation
        from eval.run_answer_eval import _stable_hash
        metadata, config, queries, rubric = validation._frozen_inputs()
        prepared = {"frozen_hash": _stable_hash({"metadata": metadata, "queries": queries,
            "rubric": rubric, "strategy": config}), "runtime_fingerprints": {"selector": "old"},
            "cases": [{} for _ in range(50)]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "prepared.json"
            path.write_text(json.dumps(prepared), encoding="utf-8")
            with patch.object(validation, "PREPARED", path), \
                 patch.object(validation, "_runtime_fingerprints", return_value={"selector": "new"}):
                with self.assertRaisesRegex(ValueError, "selector"):
                    validation._load_prepared()

    def test_material_identity_ignores_derived_chunk_token_field(self) -> None:
        chunk = {"chunk_id": "x", "text": "X", "token_count": 3}
        evidence = {"covered_fact_ids": ["F1"], "evidence_tokens": 3,
                    "evidence_hash": "h"}
        row = {"case_id": "T", "query": "Q", "facts": [{"fact_id": "F1"}],
               "candidate_count": 1, "top5_scores": [3.0] * 5,
               "minimum_top5_score": 3.0, "adaptive_decision": "fixed_top5",
               "candidate_pool": {"covered_fact_ids": ["F1"]},
               "selector_trace": {"selected_k": 5},
               "variants": {"fixed_top5": {"chunks": [chunk], "evidence": evidence}}}
        earlier = json.loads(json.dumps(row))
        earlier["variants"]["fixed_top5"]["chunks"][0].pop("token_count")
        self.assertEqual(_material_prepared_identity(row), _material_prepared_identity(earlier))
        earlier["variants"]["fixed_top5"]["chunks"][0]["chunk_id"] = "y"
        self.assertNotEqual(_material_prepared_identity(row), _material_prepared_identity(earlier))

    def test_deterministic_decision_and_dedup(self) -> None:
        self.assertEqual(adaptive_decision([2.5] * 5, 2.5), "fixed_top5")
        self.assertEqual(adaptive_decision([3, 3, 2.49, 3, 3], 2.5), "adaptive_prefix_v1")
        with self.assertRaises(ValueError):
            adaptive_decision([3] * 4, 2.5)
        row = {"adaptive_decision": "adaptive_prefix_v1", "variants": {
            "fixed_top5": {"evidence": {"evidence_hash": "a"}},
            "adaptive_prefix_v1": {"evidence": {"evidence_hash": "b"}}}}
        self.assertEqual(_unique_routes(row), ["adaptive_prefix_v1"])
        row["adaptive_decision"] = "fixed_top5"
        self.assertEqual(_unique_routes(row), ["adaptive_prefix_v1", "fixed_top5"])
        row["variants"]["fixed_top5"]["evidence"]["evidence_hash"] = "b"
        self.assertEqual(_unique_routes(row), ["adaptive_prefix_v1"])

    def test_generation_and_judge_cache_resume(self) -> None:
        chunk = {"chunk_id": "x", "text": "Policy says X.", "title": "Policy",
                 "source_path": "Policies/x.md", "source_url": "https://example.test/x",
                 "heading_path": [], "chunk_index": 0, "token_count": 4}
        from eval.run_answer_eval import _stable_hash
        evidence_hash = _stable_hash([{"chunk_id": "x", "text": chunk["text"],
                                      "title": chunk["title"], "heading_path": [],
                                      "source_path": chunk["source_path"]}])
        row = {"case_id": "T-1", "query": "What is X?", "adaptive_decision": "adaptive_prefix_v1",
               "variants": {"adaptive_prefix_v1": {"chunks": [chunk],
                   "evidence": {"evidence_hash": evidence_hash}}}}
        rubric_case = {"facts": [{"fact_id": "F1", "statement": "X is required."}]}
        one = _generation_identity(row, "adaptive_prefix_v1", "model-a")
        self.assertEqual(one["key"], _generation_identity(row, "adaptive_prefix_v1", "model-a")["key"])
        self.assertNotEqual(one["key"], _generation_identity(row, "adaptive_prefix_v1", "model-b")["key"])
        with tempfile.TemporaryDirectory() as temp:
            cache = _V3Cache(Path(temp) / "cache.json")
            cache.set(one["key"], {"kind": "generation", "answer": "X is required. [S1]",
                                   "generation_hash": _stable_hash("X is required. [S1]")})
            raw = json.dumps({"answers": {"A": {"facts": [{"fact_id": "F1",
                "status": "covered", "citation_status": "supported"}],
                "claims": [{"text": "X is required", "support_status": "supported",
                            "citation_status": "supported"}]}}})
            class FakeClient:
                calls = 0
                def complete_with_usage(self, *args, **kwargs):
                    self.calls += 1
                    return raw, {"input_tokens": 1, "output_tokens": 1}
            client = FakeClient()
            self.assertEqual(_judge_case(row, rubric_case, "model-a", cache, client), 1)
            cache = _V3Cache(Path(temp) / "cache.json")
            self.assertEqual(_judge_case(row, rubric_case, "model-a", cache, client), 0)
            self.assertEqual(client.calls, 1)
            self.assertEqual(_get_judgment(row, rubric_case, "model-a", cache)
                             ["adaptive_prefix_v1"]["facts"][0]["status"], "covered")

    def test_generate_command_resumes_without_another_model_call(self) -> None:
        import eval.run_validation as validation
        from eval.run_answer_eval import _stable_hash
        chunk = {"chunk_id": "x", "text": "X is required.", "title": "Policy",
                 "source_path": "Policies/x.md", "source_url": "https://example.test/x",
                 "heading_path": [], "chunk_index": 0, "token_count": 4}
        evidence_hash = _stable_hash([{"chunk_id": "x", "text": chunk["text"],
                                      "title": chunk["title"], "heading_path": [],
                                      "source_path": chunk["source_path"]}])
        row = {"case_id": "T-1", "query": "What is X?", "adaptive_decision": "adaptive_prefix_v1",
               "variants": {"adaptive_prefix_v1": {"chunks": [chunk],
                   "evidence": {"evidence_hash": evidence_hash}}}}
        class FakeClient:
            calls = 0
            def complete_with_usage(self, *args, **kwargs):
                self.calls += 1
                return "X is required. [S1]", {"input_tokens": 1, "output_tokens": 1}
        client = FakeClient()
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(validation, "CACHE", Path(temp) / "cache.json"), \
                 patch.object(validation, "_load_prepared", return_value=({"cases": [row]}, {}, {})), \
                 patch("src.llm_client.LLMConfig.from_env", return_value=LLMConfig("key", "url", "model-a")), \
                 patch("src.llm_client.OpenAIChatCompletionsClient", return_value=client):
                validation.generate()
                validation.generate()
            self.assertEqual(client.calls, 1)

    def test_grouped_judge_fallback_resumes_successful_singletons(self) -> None:
        from eval.run_answer_eval import _stable_hash
        def variant(chunk_id: str) -> dict:
            chunk = {"chunk_id": chunk_id, "text": "X is required.", "title": "Policy",
                     "source_path": "Policies/x.md", "source_url": "https://example.test/x",
                     "heading_path": [], "chunk_index": 0, "token_count": 4}
            evidence_hash = _stable_hash([{"chunk_id": chunk_id, "text": chunk["text"],
                "title": chunk["title"], "heading_path": [], "source_path": chunk["source_path"]}])
            return {"chunks": [chunk], "evidence": {"evidence_hash": evidence_hash}}
        row = {"case_id": "T-2", "query": "What is X?", "adaptive_decision": "fixed_top5",
               "variants": {"adaptive_prefix_v1": variant("a"), "fixed_top5": variant("b")}}
        rubric_case = {"facts": [{"fact_id": "F1", "statement": "X is required."}]}
        with tempfile.TemporaryDirectory() as temp:
            cache = _V3Cache(Path(temp) / "cache.json")
            for route in _unique_routes(row):
                identity = _generation_identity(row, route, "model-a")
                cache.set(identity["key"], {"kind": "generation", "answer": f"{route} [S1]",
                                            "generation_hash": _stable_hash(f"{route} [S1]")})
            class FakeClient:
                calls = 0
                def complete_with_usage(self, messages, **kwargs):
                    self.calls += 1
                    if self.calls == 1:
                        return "truncated", {"input_tokens": 1, "output_tokens": 1}
                    payload = json.loads(messages[-1]["content"].split("INPUT:\n", 1)[1])
                    answers = {label: {"facts": [{"fact_id": "F1", "status": "covered",
                        "citation_status": "supported"}], "claims": [{"text": "X",
                        "support_status": "supported", "citation_status": "supported"}]}
                        for label in payload["answers"]}
                    return json.dumps({"answers": answers}), {"input_tokens": 1, "output_tokens": 1}
            client = FakeClient()
            self.assertEqual(_judge_case(row, rubric_case, "model-a", cache, client), 3)
            cache = _V3Cache(Path(temp) / "cache.json")
            self.assertEqual(_judge_case(row, rubric_case, "model-a", cache, client), 0)
            self.assertEqual(client.calls, 3)
            self.assertEqual(set(_get_judgment(row, rubric_case, "model-a", cache)),
                             {"adaptive_prefix_v1", "fixed_top5"})

    def test_preregistered_gates_and_stop_classes(self) -> None:
        metadata = json.loads((ROOT / "eval/validation/validation_v1_metadata.json")
                              .read_text(encoding="utf-8"))
        v1 = {"grounded_micro": .90, "grounded_complete_cases": 40,
              "claim_counts": {"unsupported": 1, "contradicted": 0}}
        adaptive = {"grounded_micro": .88, "grounded_complete_cases": 39,
                    "claim_counts": {"unsupported": 1, "contradicted": 0}}
        quality = {"claims": {"unsupported": 0, "contradicted": 0},
                   "grounded_covered_count": 4, "grounded_fact_complete": True,
                   "claim_citations": {"unsupported": 0, "missing": 0}}
        paired = [{"always_v1": {"quality": quality},
                   "frozen_adaptive": {"quality": quality}}]
        self.assertEqual(quality_gates(v1, adaptive, paired, metadata)["overall"], "PASS")
        adaptive["grounded_micro"] = .879
        self.assertEqual(quality_gates(v1, adaptive, paired, metadata)["overall"], "FAIL")
        item = {"quality": quality}
        self.assertEqual(classify_stop("fixed_top5", item, item), "safe_stop")
        worse = {"quality": quality | {"grounded_covered_count": 3}}
        self.assertEqual(classify_stop("fixed_top5", item, worse), "false_stop")
        self.assertEqual(classify_stop("adaptive_prefix_v1", item, item), "unobserved")
        self.assertEqual(classify_stop("adaptive_prefix_v1", item, item, item), "conservative_miss")

    def test_prepared_result_schema(self) -> None:
        sample = {"case_id": "T-1", "query": "Question", "policy_family": "terms",
                  "query_type": "scope", "difficulty": "easy", "candidate_count": 23,
                  "top5_scores": [3.0] * 5, "minimum_top5_score": 3.0,
                  "adaptive_decision": "fixed_top5", "candidate_pool": {"coverage": 1.0},
                  "selector_trace": {"selected_k": 8},
                  "variants": {"fixed_top5": {"evidence": {"selected_k": 5}},
                               "adaptive_prefix_v1": {"evidence": {"selected_k": 8}}}}
        public = _prepared_public_row(sample)
        self.assertEqual(public["always_v1_evidence"]["selected_k"], 8)
        self.assertEqual(public["frozen_adaptive_evidence"]["selected_k"], 5)
        self.assertEqual(public["minimum_top5_score"], 3.0)
        self.assertNotIn("variants", public)


class DynamicKExploratoryTests(unittest.TestCase):
    def test_normalization_and_novelty_patience(self) -> None:
        self.assertEqual(dynamic_relevance([-10.0, 0.0, 10.0]), [0.0, 0.5, 1.0])
        self.assertEqual(dynamic_relevance([2.0, 2.0]), [1.0, 1.0])
        chunks = [{"chunk_id": f"c{i}", "reranker_score": 11-i,
                   "token_count": 100, "source_path": "doc",
                   "heading_path": ["one"]} for i in range(1, 10)]
        vectors = {f"c{i}": np.array([1.0, 0.0]) for i in range(1, 10)}
        vectors["c7"] = np.array([0.0, 1.0])
        chosen = select_dynamic(chunks, vectors, DynamicConfig("test", "product", .1, 2))
        self.assertEqual([c["chunk_id"] for c in chosen["selected_chunks"]],
                         ["c1", "c2", "c3", "c4", "c5", "c7"])
        self.assertEqual(chosen["stop_reason"], "patience")
        self.assertEqual(chosen["scan_depth"], 9)

    def test_budget_and_dev_only_result_integrity(self) -> None:
        chunks = [{"chunk_id": f"c{i}", "reranker_score": 11-i,
                   "token_count": 1000 if i <= 5 else 1500,
                   "source_path": "doc", "heading_path": [str(i)]}
                  for i in range(1, 8)]
        vectors = {f"c{i}": np.array([1.0, 0.0]) if i <= 5 else
                   np.array([0.0, 1.0]) for i in range(1, 8)}
        chosen = select_dynamic(chunks, vectors, DynamicConfig("test", "additive", 0.0, 2))
        self.assertEqual(chosen["selected_k"], 5)
        self.assertEqual(chosen["stop_reason"], "token_budget")
        result = analyze_dynamic_k()
        self.assertEqual(len(DYNAMIC_CONFIGS), 4)
        self.assertEqual(result["case_count"], 16)
        self.assertEqual(result["required_fact_count"], 92)
        self.assertEqual(result["summaries"]["fixed_top5"]["covered_facts"], 69)
        self.assertEqual(result["summaries"]["adaptive_prefix_v1"]["covered_facts"], 86)
        self.assertFalse(result["answer_quality_next_stage"])
        self.assertNotIn("validation_v1", json.dumps(result["source_sha256"]))


def _unit(unit_id: str, chunk_ids: list[str], token_count: int = 1) -> dict:
    return {"unit_id": unit_id, "chunk_ids": chunk_ids, "token_count": token_count,
            "source_path": "doc", "heading_path": (), "chunk_index": 0}


class EvidenceGeometryTests(unittest.TestCase):
    def test_min_cardinality_and_min_token_cover(self) -> None:
        fact_units = {"a": {"x", "y"}, "b": {"y", "z"}}
        self.assertEqual(min_cardinality_cover(fact_units), (1, ["y"]))
        tokens = {"x": 5, "y": 1, "z": 5}
        self.assertEqual(min_token_cover(fact_units, tokens), (1, ["y"]))
        weighted = {"x": 1, "y": 4, "z": 1}
        value, units = min_token_cover(fact_units, weighted)
        self.assertEqual(value, 2)
        self.assertEqual(sorted(units), ["x", "z"])

    def test_impossible_cover(self) -> None:
        self.assertEqual(min_cardinality_cover({"a": set(), "b": {"y"}}), (None, []))
        self.assertEqual(min_cardinality_cover({"a": set(), "b": {"y"}},
                                               require_all=False), (1, ["y"]))

    def test_full_union_and_top20_scope_difference(self) -> None:
        facts = [{"fact_id": "f1", "direct_chunk_ids": ["x"]},
                 {"fact_id": "f2", "direct_chunk_ids": ["y"]}]
        union_units = [_unit("z", ["x", "y"], 10), _unit("x", ["x"], 4), _unit("y", ["y"], 4)]
        top20_units = [_unit("x", ["x"], 4), _unit("y", ["y"], 4)]
        union_block = _cover_block(facts, union_units, {})
        top20_block = _cover_block(facts, top20_units, {})
        self.assertEqual(union_block["min_k"], 1)
        self.assertEqual(top20_block["min_k"], 2)
        self.assertEqual(top20_block["min_tokens"], 8)

    def test_support_groups_collapse_overlap_duplicates(self) -> None:
        overlap = "OVERLAP" * 30
        chunks = {
            "a": {"source_path": "d", "heading_path": ["H"], "chunk_index": 0,
                  "text": "x" * 100 + overlap},
            "b": {"source_path": "d", "heading_path": ["H"], "chunk_index": 1,
                  "text": overlap + "y" * 100},
            "c": {"source_path": "e", "heading_path": ["H"], "chunk_index": 0, "text": "distinct"},
        }
        self.assertEqual(len(support_groups(["a", "b"], chunks)), 1)
        self.assertEqual(len(support_groups(["a", "b", "c"], chunks)), 2)

    def test_local_windows_do_not_cross_documents(self) -> None:
        chunks = [{"chunk_id": f"d{i}", "source_path": "d", "chunk_index": i,
                   "text": f"d{i}", "heading_path": []} for i in range(3)]
        chunks += [{"chunk_id": f"e{i}", "source_path": "e", "chunk_index": i,
                    "text": f"e{i}", "heading_path": []} for i in range(2)]
        windows = build_local_windows(chunks, size=3)
        for window in windows:
            self.assertEqual(len({cid[0] for cid in window["chunk_ids"]}), 1)
        self.assertEqual(len(windows), 5)
        self.assertTrue(any(len(w["chunk_ids"]) == 3 for w in windows))

    def test_top1_subtree_grouping_is_deterministic(self) -> None:
        chunks = [{"chunk_id": "a", "source_path": "d", "chunk_index": 1,
                   "text": "a", "heading_path": ["Top", "Sub"]},
                  {"chunk_id": "b", "source_path": "d", "chunk_index": 0,
                   "text": "b", "heading_path": ["Top"]},
                  {"chunk_id": "c", "source_path": "d", "chunk_index": 2,
                   "text": "c", "heading_path": []}]
        first = build_top1_subtrees(chunks)
        self.assertEqual([u["unit_id"] for u in first],
                         ["SUB::d::Top", "SUB::d::__document_root__"])
        self.assertEqual(first[0]["chunk_ids"], ["b", "a"])
        self.assertEqual([u["unit_id"] for u in build_top1_subtrees(chunks)],
                         [u["unit_id"] for u in first])

    def test_fragmentation_threshold_rule(self) -> None:
        self.assertTrue(fragmentation_signal(10, 6, 3000, 3200))
        self.assertFalse(fragmentation_signal(10, 8, 3000, 3200))
        self.assertFalse(fragmentation_signal(10, 6, 3000, 4000))
        self.assertFalse(fragmentation_signal(None, 6, 3000, 3000))

    def test_overlap_merge_and_sensitivity_schema(self) -> None:
        self.assertEqual(overlap_aware_merge(["abcdef", "cdefgh"]), "abcdefgh")
        stable = {"facts_removed_from_available": [], "missing_direct_mapping_candidates": {}}
        self.assertIn("robust", _sensitivity(stable, {})["verdict"])
        changed = {"facts_removed_from_available": ["F1"], "missing_direct_mapping_candidates": {}}
        self.assertIn("changes", _sensitivity(changed, {})["verdict"])

    def test_gold_rank_buckets_and_candidate_missing(self) -> None:
        rows = [{"case_id": "C1", "policy_family": "f", "query_type": "q",
                 "deepest_gold_rank": 12, "facts_outside_top5": 2, "candidate_ceiling": False,
                 "fact_ranks": [{"fact_id": "F1", "union_rank": 1, "candidate_missing": False},
                                {"fact_id": "F2", "union_rank": 8, "candidate_missing": False},
                                {"fact_id": "F3", "union_rank": 12, "candidate_missing": False},
                                {"fact_id": "F4", "union_rank": None, "candidate_missing": True}]}]
        tail = _tail_baseline(rows)
        self.assertEqual(tail["top1"], 1)
        self.assertEqual(tail["top5"], 1)
        self.assertEqual(tail["buckets"]["rank_6_8"], 1)
        self.assertEqual(tail["buckets"]["rank_11_20"], 1)
        self.assertEqual(tail["buckets"]["candidate_missing"], 1)
        self.assertEqual(tail["tail_facts_rank_6_20"], 2)
        self.assertEqual(tail["deep_tail_facts_rank_ge_11"], 1)
        self.assertEqual(tail["affected_case_count_outside_top5"], 1)
        self.assertEqual(tail["case_with_candidate_missing"], [])
        self.assertEqual(tail["deepest_gold_rank"]["max"], 12)

    def test_first_complete_equals_deepest_gold_rank_single_support(self) -> None:
        facts = [{"fact_id": "F1", "direct_chunk_ids": ["a"]},
                 {"fact_id": "F2", "direct_chunk_ids": ["b"]}]
        support = {"F1": ["a"], "F2": ["b"]}
        tokens = {"a": 1, "x": 1, "b": 1}
        top20 = ["a", "x", "b"]
        status = _prefix_status(top20, top20, facts, support, tokens)
        self.assertTrue(status["complete"])
        self.assertEqual(status["k"], 3)
        self.assertEqual(status["k"], max(1, 3))

    def test_attribution_categories_are_from_frozen_labels(self) -> None:
        self.assertEqual(_attribute_gap_fact("F", {"status": "covered",
                     "citation_status": "partial"}, None, "ans", set())[0],
                     "citation_grounding_issue")
        self.assertEqual(_attribute_gap_fact("F", {"status": "missing"},
                     {"cause": "utilization_miss"}, "ans", set())[0], "utilization_miss")
        self.assertEqual(_attribute_gap_fact("F", {"status": "incorrect"},
                     None, "ans", set())[0], "partial_synthesis")
        self.assertEqual(_attribute_gap_fact("F", {"status": "uncertain"},
                     None, "ans", set())[0], "other_or_unclear")
        self.assertEqual(_attribute_gap_fact("F", {"status": "missing"},
                     None, "ans", {"F"})[0], "judge_rubric_disagreement")
        for category in ("citation_grounding_issue", "utilization_miss", "partial_synthesis",
                         "other_or_unclear", "judge_rubric_disagreement"):
            self.assertIn(category, GAP_CATEGORIES)

    def test_conversion_gap_units_and_rate(self) -> None:
        def variant(case_id, complete, grounded_missing, required, grounded_covered):
            quality = {"required_fact_count": required, "grounded_covered_count": grounded_covered,
                       "grounded_fact_complete": complete, "grounded_missing_fact_ids": grounded_missing,
                       "covered_count": grounded_covered, "covered_fact_ids": grounded_missing,
                       "evidence_tokens": 1000}
            return {"case_id": case_id, "query": "What are the terms?",
                    "always_v1_evidence": {"fact_complete": True},
                    "always_v1": {"quality": quality, "pipeline_diagnosis": [],
                                  "claim_diagnosis": [], "judge": {"facts": []},
                                  "selected_chunk_ids": [], "generation": {"answer": "answer"}},
                    "policy_family": "f", "query_type": "q"}
        good = variant("C1", True, [], 4, 4)
        bad = variant("C2", False, ["F2"], 4, 3)
        bad["always_v1"]["judge"] = {"facts": [{"fact_id": "F2", "status": "covered",
                                                "citation_status": "partial"}]}
        results = {"cases": [good, bad]}
        gap = _answer_conversion_gap(results, {}, {"entries": []})
        self.assertEqual(gap["evidence_complete_cases"], 2)
        self.assertEqual(gap["grounded_complete_among_evidence_complete"], 1)
        self.assertEqual(gap["conversion_rate_cases"], 0.5)
        self.assertEqual(gap["gap_case_count"], 1)
        self.assertEqual(gap["attribution_unit"], "facts")
        self.assertEqual(gap["attribution_fact_counts"]["citation_grounding_issue"], 1)
        self.assertEqual(set(gap["units"]), {"case", "fact", "claim"})
        self.assertEqual(gap["cases"][0]["grounded_missing_facts"][0]["primary"],
                         "citation_grounding_issue")

    def test_utilization_pattern_evidence_and_chunk_position(self) -> None:
        import eval.analyze_evidence_geometry as geometry
        saved = geometry._FACT_TEXT
        geometry._FACT_TEXT = {"F1": ("needle", ""), "F2": ("needle", "")}
        try:
            row = {"case_id": "C", "query": "What and where, if any?", "query_type": "scope",
                   "always_v1": {
                       "quality": {"required_fact_count": 2, "covered_count": 1,
                                   "evidence_tokens": 1000},
                       "selected_chunk_ids": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
                       "judge": {"facts": [{"fact_id": "F1"}, {"fact_id": "F2"}]},
                       "generation": {"answer": "short"}}}
            support = {"F1": ["c8"], "F2": ["c8"]}
            meta = {"c8": {"text": "x" * 100 + "needle"}}
            pattern = geometry._utilization_pattern(row, "F1", support, meta)
            self.assertEqual(pattern["evidence_position"], 8)
            self.assertEqual(pattern["evidence_percentile"], 1.0)
            self.assertFalse(pattern["evidence_first_half"])
            self.assertEqual(pattern["intra_chunk_position"], "back_third")
            self.assertIn("late_evidence_position", pattern["pattern_flags"])
            self.assertIn("late_in_chunk", pattern["pattern_flags"])
            self.assertIn("many_selected_chunks", pattern["pattern_flags"])
            self.assertTrue(pattern["single_dense_gold_chunk"])
            self.assertEqual(pattern["selected_chunks_mapped"], 1)
            summary = geometry._utilization_pattern_summary(
                [{"grounded_missing_facts": [{"pattern": pattern}]}], [], [])
            self.assertEqual(summary["unit"], "facts")
            self.assertEqual(summary["text"]["concentrated_in_evidence_back_half"], 1)
            self.assertIn(summary["verdict"], {"CLEAR GENERATION PATTERN",
                                               "MIXED GENERATION PATTERN", "NO DOMINANT PATTERN"})
        finally:
            geometry._FACT_TEXT = saved

    def test_compare_rerankers_pure_metrics(self) -> None:
        rows = [{"fact_id": "F1", "union_rank": 1}, {"fact_id": "F2", "union_rank": 6},
                {"fact_id": "F3", "union_rank": None}]
        hist = rank_histogram(rows)
        self.assertEqual(hist["top1"], 1)
        self.assertEqual(hist["buckets"]["rank_6_8"], 1)
        self.assertEqual(hist["buckets"]["missing"], 1)
        self.assertEqual(coverage_at_k(rows, 5), 1)
        self.assertEqual(coverage_at_k(rows, 10), 2)
        self.assertEqual(deepest_gold_rank(rows), 6)
        self.assertEqual(complete_at_k({"C1": rows}, 5), 0)
        self.assertEqual(complete_at_k({"C1": rows}, 20), 0)
        available_only = [r for r in rows if r["union_rank"] is not None]
        self.assertEqual(complete_at_k({"C1": available_only}, 6), 1)

    def test_tail_movement_and_token_length_views(self) -> None:
        base = {"F1": {"union_rank": 1}, "F2": {"union_rank": 6}, "F3": {"union_rank": 15}}
        chal = {"F1": {"union_rank": 1}, "F2": {"union_rank": 4}, "F3": {"union_rank": 18}}
        movement = tail_rank_movement(base, chal, ["F2", "F3"])
        self.assertEqual(movement["improved"], 1)
        self.assertEqual(movement["regressed"], 1)
        self.assertEqual(movement["moved_into_top5"], 1)
        self.assertEqual(movement["moved_into_top8"], 1)
        facts = [{"fact_id": "F1", "direct_chunk_ids": ["c0"]},
                 {"fact_id": "F2", "direct_chunk_ids": ["c2"]}]
        tokens = {"c0": 100, "c1": 100, "c2": 100}
        view = token_view(["c0", "c1", "c2"], tokens, facts, checkpoints=(100, 200, 300))
        self.assertEqual(view["coverage_at_token_checkpoints"][100], 1)
        self.assertEqual(view["coverage_at_token_checkpoints"][200], 1)
        self.assertEqual(view["coverage_at_token_checkpoints"][300], 2)
        self.assertEqual(view["first_complete_tokens"], 300)
        bias = length_bias(["c0", "c1"], {"c0": 100, "c1": 300}, 2)
        self.assertEqual(bias["total_tokens"], 400)
        self.assertEqual(bias["median_chunk_tokens"], 200)

    def test_reranker_same_union_and_schema(self) -> None:
        chunks = {f"c{i}": {"chunk_id": f"c{i}", "title": "T", "heading_path": [],
                            "text": f"text {i}"} for i in range(6)}
        support = {"F1": ["c0"], "F2": ["c5"]}
        cases = [{"case_id": "C1", "query": "q", "fact_ids": ["F1", "F2"]}]
        unions = {"C1": sorted(chunks)}

        class BestFirst:
            def score(self, query, texts):
                return [6 - i for i in range(len(texts))]

        class RewardGold:
            def score(self, query, texts):
                return [10.0 if index in (0, 5) else 0.0 for index in range(len(texts))]

        baseline = evaluate_model("baseline", BestFirst(), cases, support, unions, chunks, {})
        challenger = evaluate_model("challenger", RewardGold(), cases, support, unions, chunks, {})
        self.assertEqual(set(baseline["per_case_order"]["C1"]), set(chunks))
        self.assertEqual(set(challenger["per_case_order"]["C1"]), set(chunks))
        base_summary = summarize_model(baseline, cases, {c: 100 for c in chunks})
        chal_summary = summarize_model(challenger, cases, {c: 100 for c in chunks})
        self.assertEqual(base_summary["coverage_at_k"][5], 1)
        self.assertEqual(chal_summary["coverage_at_k"][5], 2)
        self.assertEqual(base_summary["length_bias"]["top5"]["total_tokens"], 500)
        comparison = compare(base_summary, chal_summary, cases)
        self.assertEqual(comparison["tail_movement"]["improved"], 1)
        gate = _verdict({"baseline": base_summary, "challenger": chal_summary}, comparison)
        self.assertIn(gate["evidence_gate"],
                      {"CLEAR EVIDENCE WIN", "SMALL / MIXED WIN", "WASH", "REGRESSION"})

    def test_gold_rank_rows_missing_gold(self) -> None:
        facts = [{"fact_id": "F1", "direct_chunk_ids": ["c0"]},
                 {"fact_id": "F2", "direct_chunk_ids": ["c9"]}]
        rows = gold_rank_rows(facts, ["c0", "c1"])
        self.assertEqual(rows[0]["union_rank"], 1)
        self.assertIsNone(rows[1]["union_rank"])

    def test_transfer_blind_order_and_order_sensitive_hash(self) -> None:
        first = transfer.blind_order("VAL-001-001")
        self.assertEqual(first, transfer.blind_order("VAL-001-001"))
        self.assertEqual(set(first.values()), {"minilm_top5", "bge_top5"})
        self.assertNotEqual(first["A"], first["B"])
        transfer._CASE_QUERY["C1"] = "What are the terms?"
        chunk = lambda cid, txt: {"chunk_id": cid, "text": txt, "title": "T",
                                  "source_path": "Policies/x.md", "source_url": "u",
                                  "heading_path": ["H"], "chunk_index": 0, "token_count": 3}
        forward = transfer._generation_identity("C1", [chunk("a", "A"), chunk("b", "B")], "m")
        reverse = transfer._generation_identity("C1", [chunk("b", "B"), chunk("a", "A")], "m")
        self.assertNotEqual(forward["key"], reverse["key"])
        self.assertNotEqual(forward["evidence_hash"], reverse["evidence_hash"])
        same = transfer._generation_identity("C1", [chunk("a", "A"), chunk("b", "B")], "m")
        self.assertEqual(forward["key"], same["key"])

    def test_transition_bucket_and_paired_transitions(self) -> None:
        self.assertEqual(transfer.transition_bucket(True, True), "both_right")
        self.assertEqual(transfer.transition_bucket(True, False), "right_to_wrong")
        self.assertEqual(transfer.transition_bucket(False, True), "wrong_to_right")
        self.assertEqual(transfer.transition_bucket(False, False), "both_wrong")
        def row(cid, mini, bge, status="complete"):
            return {"case_id": cid, "status": status,
                    "arms": {"minilm_top5": {"quality": {"grounded_fact_complete": mini}},
                             "bge_top5": {"quality": {"grounded_fact_complete": bge}}}}
        buckets = transfer.paired_transitions([row("A", False, True), row("B", True, False),
                                               row("C", True, True), row("D", False, False),
                                               row("E", False, True, "technical_failure")])
        self.assertEqual(buckets["wrong_to_right"], ["A"])
        self.assertEqual(buckets["right_to_wrong"], ["B"])
        self.assertEqual(buckets["both_right"], ["C"])
        self.assertEqual(buckets["both_wrong"], ["D"])

    def test_transfer_accounting(self) -> None:
        pairs = [{"case_id": "C1", "minilm_available": ["f1"], "bge_available": ["f1", "f2"],
                  "minilm_grounded": ["f1"], "bge_grounded": ["f1", "f2"]},
                 {"case_id": "C2", "minilm_available": ["f3", "f4"], "bge_available": ["f3"],
                  "minilm_grounded": ["f3", "f4"], "bge_grounded": ["f3"]}]
        report = transfer.transfer_accounting(pairs)
        self.assertEqual(report["newly_available_required_facts"], 1)
        self.assertEqual(report["lost_evidence_facts"], 1)
        self.assertEqual(report["grounded_facts_gained"], 1)
        self.assertEqual(report["grounded_facts_lost"], 1)
        self.assertEqual(report["positive_transfer_rate"], 1.0)
        self.assertEqual(report["negative_transfer_rate"], 1.0)

    def test_utilization_gap_cohort_and_historical_unchanged(self) -> None:
        import hashlib
        before = hashlib.sha256(transfer.HISTORICAL.read_bytes()).hexdigest()
        gap_ids = transfer._utilization_gap_ids()
        self.assertEqual(len(gap_ids), 7)
        self.assertIn("VAL-001-009", gap_ids)
        reference = transfer._historical_reference()
        self.assertEqual(reference["validation_v1_verdict"], "PASS")
        after = hashlib.sha256(transfer.HISTORICAL.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_utilization_cohort_and_gap_selection(self) -> None:
        facts_by_case = {"C1": [{}, {}, {}], "C2": [{}, {}]}
        bge_evidence = {"C1": {"available_fact_ids": ["a", "b", "c"]},
                        "C2": {"available_fact_ids": ["x"]}}
        self.assertEqual(util.evidence_complete_ids(bge_evidence, facts_by_case), ["C1"])
        gaps, controls = util.split_gap_and_control(["C1", "C2"], {"C1": False, "C2": True})
        self.assertEqual(gaps, ["C1"])
        self.assertEqual(controls, ["C2"])
        self.assertEqual(util.rescued_cases(["C1", "C2"], {"C1": True, "C2": False}), ["C1"])
        self.assertEqual(util.control_regressions(["C3"], {"C3": False}), ["C3"])

    def test_utilization_prompt_variant_and_evidence_invariant(self) -> None:
        from types import SimpleNamespace
        from src.generator import assign_evidence_sources, build_grounded_messages
        chunks = [{"chunk_id": "a", "text": "A", "title": "T", "source_path": "Policies/x.md",
                   "source_url": "u", "heading_path": ["H"], "chunk_index": 0, "token_count": 1},
                  {"chunk_id": "b", "text": "B", "title": "T", "source_path": "Policies/x.md",
                   "source_url": "u", "heading_path": ["H"], "chunk_index": 1, "token_count": 1}]
        base = util.identity_for("C", "q", chunks, "m", "baseline")
        cov = util.identity_for("C", "q", chunks, "m", "coverage_aware")
        self.assertEqual(base["evidence_hash"], cov["evidence_hash"])
        self.assertNotEqual(base["key"], cov["key"])
        self.assertNotEqual(base["messages"][0]["content"], cov["messages"][0]["content"])
        self.assertEqual(base["messages"][1], cov["messages"][1])
        production = build_grounded_messages("q", [], assign_evidence_sources(
            [SimpleNamespace(**chunk) for chunk in chunks]))
        self.assertEqual(base["messages"], production)

    def test_utilization_blind_order_and_length_guardrail(self) -> None:
        first = util.blind_order("VAL-001-001")
        self.assertEqual(first, util.blind_order("VAL-001-001"))
        self.assertEqual(set(first.values()), {"baseline", "coverage_aware"})
        stats = util.length_stats(["a b c d", "a b"])
        self.assertEqual(stats["n"], 2)
        self.assertEqual(stats["median"], 3.0)
        self.assertEqual(util.facts_per_extra_100_tokens(3, 300), 1.0)
        self.assertIsNone(util.facts_per_extra_100_tokens(2, 0))

    def test_utilization_historical_unchanged(self) -> None:
        import hashlib
        before = hashlib.sha256(util.HISTORICAL.read_bytes()).hexdigest()
        completed = util.evidence_complete_ids({"x": {"available_fact_ids": []}}, {"x": []})
        self.assertEqual(completed, ["x"])
        after = hashlib.sha256(util.HISTORICAL.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_mva_nominal_split_and_deterministic_sampling(self) -> None:
        utilization = {"cohort": {"gap_ids": ["C1", "C2"]}, "cases": [
            {"case_id": "C1", "status": "complete", "arms": {"baseline": {
                "pipeline_diagnosis": [{"fact_id": "C1-F01", "cause": "utilization_miss"},
                                       {"fact_id": "C1-F02", "cause": "synthesis_error"}],
                "quality": {"grounded_missing_fact_ids": ["C1-F01", "C1-F02"]}}}},
            {"case_id": "C2", "status": "complete", "arms": {"baseline": {
                "pipeline_diagnosis": [{"fact_id": "C2-F01", "cause": "utilization_miss"}],
                "quality": {"grounded_missing_fact_ids": ["C2-F01"]}}}}]}
        facts = mva.nominal_problematic_facts(utilization)
        types = {item["fact_id"]: item["nominal_type"] for item in facts}
        self.assertEqual(types["C1-F02"], "incorrect_synthesis")
        self.assertEqual(types["C1-F01"], "omission")
        self.assertEqual(types["C2-F01"], "omission")
        covered = {"C1": ["C1-F01", "C1-F02", "C1-F03"], "C2": ["C2-F01", "C2-F02", "C2-F03"]}
        first = mva.sample_stratum_a(["C1", "C2"], covered, random.Random(mva.SEED))
        again = mva.sample_stratum_a(["C1", "C2"], covered, random.Random(mva.SEED))
        self.assertEqual(first, again)
        self.assertEqual(len(first), 4)
        strat_b = mva.sample_stratum_b(["C3", "C4", "C5"],
                                       {"C3": ["x"], "C4": ["y"], "C5": ["z"]},
                                       random.Random(mva.SEED), exclude=(), count=2)
        self.assertEqual(len(strat_b), 2)
        self.assertEqual(strat_b, mva.sample_stratum_b(["C3", "C4", "C5"],
                                                       {"C3": ["x"], "C4": ["y"], "C5": ["z"]},
                                                       random.Random(mva.SEED), exclude=(), count=2))

    def test_mva_packet_blinding_and_label_parsing(self) -> None:
        fact = {"fact_id": "F1", "statement": "SECRET STATEMENT",
                "support": [{"document": "doc", "section": "sec", "source_excerpt": "EX"}]}
        packet = mva.build_packet("q", "answer", fact)
        serialized = json.dumps(packet)
        self.assertIn("EX", serialized)
        self.assertNotIn("SECRET STATEMENT", serialized)
        self.assertNotIn("F1", serialized)
        parsed = mva.parse_adjudication('{"label":"semantically_present",'
                                        '"diagnostic_tag":"paraphrase","reason":"x"}')
        self.assertEqual(parsed["label"], "SEMANTICALLY_PRESENT")
        with self.assertRaises(ValueError):
            mva.parse_adjudication('{"label":"NOPE"}')

    def test_mva_wilson_and_stability_metrics(self) -> None:
        low, high = mva.wilson_interval(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)
        labels = {"S1_isolated": {"F1": {"status": "covered", "citation_status": "supported"}},
                  "S3_coverage_partner": {"F1": {"status": "missing",
                                                 "citation_status": "not_applicable"}}}
        metrics = mva.stability_metrics(labels)
        self.assertEqual(metrics["E_fact"], 1)
        self.assertEqual(metrics["E_case"], 1)
        self.assertEqual(metrics["fact_count"], 1)

    def test_mva_cleaned_cohort_rules(self) -> None:
        nominal = [{"case_id": "C", "fact_id": "F1", "nominal_type": "omission"},
                   {"case_id": "C", "fact_id": "F2", "nominal_type": "omission"},
                   {"case_id": "C", "fact_id": "F3", "nominal_type": "omission"}]
        adjudications = {"F1": {"label": "ABSENT_OR_INCORRECT"}, "F2": {"label": "AMBIGUOUS"},
                         "F3": {"label": "SEMANTICALLY_PRESENT"}}
        cleaned = mva.cleaned_cohort(nominal, adjudications)
        self.assertEqual([i["fact_id"] for i in cleaned["genuine_error_facts"]], ["F1"])
        self.assertEqual(cleaned["ambiguous_facts"], ["F2"])
        self.assertEqual(cleaned["semantically_present_facts"], ["F3"])
        negated = mva.cleaned_cohort(nominal, adjudications, {"F1": "SEMANTICALLY_PRESENT"})
        self.assertEqual(negated["genuine_error_facts"], [])
        self.assertEqual(negated["human_negated_facts"], ["F1"])

    def test_mva2_reuses_v1_frozen_selection(self) -> None:
        stored, selection = mva2.load_frozen_selection()
        v1 = json.loads(mva2.V1_RESULTS.read_text(encoding="utf-8"))["selection"]
        self.assertEqual(stored, v1)
        self.assertEqual([i["fact_id"] for i in selection["nominal"]],
                         [i["fact_id"] for i in v1["nominal_problematic_facts"]])
        covered = [i["fact_id"] for i in selection["covered_sample"]]
        self.assertEqual(covered, v1["stratum_a_facts"] + v1["stratum_b_facts"])
        self.assertEqual([i["fact_id"] for i in v1["human_review_items"]][:10],
                         [i["fact_id"] for i in v1["nominal_problematic_facts"]])
        self.assertEqual(len(v1["human_review_items"]), 20)
        self.assertEqual(v1["seed"], 20260926)

    def test_mva2_packet_scope_and_blinding(self) -> None:
        chunks = [{"chunk_id": f"c{i}", "title": f"T{i}", "heading_path": ["H", f"S{i}"],
                   "text": f"VERBATIM-{i}", "source_path": f"Policies/d{i}.md",
                   "source_url": "u", "chunk_index": i, "token_count": 1} for i in range(5)]
        packet = mva2.build_v2_packet(
            "the question", "the answer", chunks, "ANCHOR-EXCERPT", "S3",
            {"document": "Policies/d2.md", "section": "S"})
        self.assertEqual([entry["source_id"] for entry in packet["full_evidence"]],
                         ["S1", "S2", "S3", "S4", "S5"])
        for i in range(5):
            self.assertIn(f"VERBATIM-{i}", json.dumps(packet))
        self.assertEqual(packet["full_evidence"][2]["heading_path"], ["H", "S2"])
        self.assertEqual(packet["anchor"]["source_id"], "S3")
        self.assertTrue(all(leak == [] for leak in [mva2.packet_leaks(
            packet, ["SECRET FACT STATEMENT", "minilm_top5", "coverage_aware",
                     "ABSENT_OR_INCORRECT original", "judge_label=missing"])]))
        self.assertIn("VERBATIM-0",
                      mva2.packet_leaks(packet, ["VERBATIM-0"]))

    def test_mva2_ambiguous_is_valid_and_v1_untouched(self) -> None:
        parsed = mva.parse_adjudication('{"label":"ambiguous","diagnostic_tag":'
                                        '"unclear_source","reason":"insufficient"}')
        self.assertEqual(parsed["label"], "AMBIGUOUS")
        before = hashlib.sha256(mva2.V1_RESULTS.read_bytes()).hexdigest()
        stored, _ = mva2.load_frozen_selection()
        self.assertIn("nominal_problematic_facts", stored)
        after = hashlib.sha256(mva2.V1_RESULTS.read_bytes()).hexdigest()
        self.assertEqual(before, after)
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")
        self.assertNotIn("Before finalizing", gen.GROUNDING_SYSTEM_PROMPT)

    def test_audit_classifies_agreement_and_sensitivity(self) -> None:
        import eval.analyze_evidence_geometry as geometry
        saved = geometry._FACT_TEXT
        geometry._FACT_TEXT = {"F1": ("needs a good faith belief", ""), "F2": ("sworn", "")}
        try:
            results = {"cases": [{"case_id": "C1",
                "always_v1": {"quality": {"answered_without_mapped_evidence_fact_ids": ["F1", "F2"]},
                              "generation": {"answer": "answer"}, "selected_chunk_ids": []},
                "frozen_adaptive": {"quality": {"answered_without_mapped_evidence_fact_ids": []},
                                    "generation": {"answer": "answer"}, "selected_chunk_ids": []}}]}
            prepared = {"cases": [{"case_id": "C1", "adaptive_decision": "adaptive_prefix_v1",
                                   "variants": {"adaptive_prefix_v1": {"chunks": [
                                       {"chunk_id": "chunk_a", "text": "unrelated"}]}}}]}
            support = {"F1": ["chunk_a"], "F2": []}
            audit = audit_disagreements(results, prepared, support)
            self.assertEqual(audit["disagreement_events"], 2)
            self.assertEqual(audit["category_counts"]["existing_direct_mapping_sufficient"], 1)
            self.assertEqual(audit["category_counts"]["unresolved"], 1)
            self.assertEqual(audit["facts_removed_from_available"], ["F2"])
        finally:
            geometry._FACT_TEXT = saved


class MeasurementValidityWritebackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.cohort = json.loads(fmv.RESULTS.read_text(encoding="utf-8"))
        cls.v1 = json.loads(mva.RESULTS.read_text(encoding="utf-8"))
        cls.v2 = json.loads(mva2.RESULTS.read_text(encoding="utf-8"))
        cls.utilization = json.loads(util.RESULTS.read_text(encoding="utf-8"))

    def _original_judge(self, fact_id: str) -> dict:
        row = next(row for row in self.utilization["cases"]
                   if fact_id.startswith(row["case_id"] + "-") and row["status"] == "complete")
        return next(fact for fact in row["arms"]["baseline"]["judge"]["facts"]
                    if fact["fact_id"] == fact_id)

    def test_human_review_writeback_preserves_all_three_layers(self) -> None:
        items = self.cohort["human_review"]["frozen_human_review_writeback"]
        self.assertEqual(len(items), 20)
        self.assertEqual({item["fact_id"] for item in items},
                         {item["fact_id"] for item in self.v2["selection"]["human_review_items"]})
        for item in items:
            fact_id = item["fact_id"]
            self.assertTrue(item["human_reviewed"])
            self.assertEqual(item["human_adjudication"], fmv.HUMAN_REVIEW[fact_id]["verdict"])
            self.assertIn(item["human_adjudication"], fmv.LABELS)
            v2_entry = self.v2["adjudications"][fact_id]
            self.assertEqual(item["v2_model_adjudication"]["label"], v2_entry["label"])
            self.assertEqual(item["v2_model_adjudication"]["reason"], v2_entry["reason"])
            self.assertEqual(item["v2_model_adjudication"]["diagnostic_tag"],
                             v2_entry["diagnostic_tag"])
            original = self._original_judge(fact_id)
            self.assertEqual(item["original_judge"]["status"], original["status"])
            self.assertEqual(item["original_judge"]["citation_status"],
                             original["citation_status"])

    def test_cleaned_cohort_frozen_membership(self) -> None:
        cohort = self.cohort["cleaned_nominal_cohort"]
        self.assertEqual([item["fact_id"] for item in cohort["confirmed_errors"]],
                         ["VAL-001-039-F02", "VAL-001-050-F01"])
        self.assertEqual([item["fact_id"] for item in cohort["ambiguous"]],
                         ["VAL-001-008-F02"])
        self.assertNotIn("VAL-001-008-F02",
                         [item["fact_id"] for item in cohort["confirmed_errors"]])
        self.assertEqual(cohort["counts"], {"nominal_problematic_facts": 10,
                                            "confirmed_errors": 2, "ambiguous": 1,
                                            "confirmed_present": 7})
        self.assertEqual(cohort["confirmed_present_fact_ids"],
                         ["VAL-001-009-F01", "VAL-001-009-F02", "VAL-001-011-F01",
                          "VAL-001-022-F02", "VAL-001-026-F02", "VAL-001-037-F01",
                          "VAL-001-050-F05"])
        self.assertEqual(cohort["repair_cohort"]["fact_ids"],
                         ["VAL-001-039-F02", "VAL-001-050-F01"])
        self.assertEqual([item["fact_id"] for item in cohort["repair_cohort"]["excluded"]],
                         ["VAL-001-008-F02"])

    def test_cleaned_cohort_agreement_and_disagreement_classes(self) -> None:
        agreement = self.cohort["human_review"]["agreement"]
        self.assertEqual(agreement["exact_agreement"],
                         {"numerator": 17, "denominator": 20, "proportion": 0.85})
        self.assertEqual(agreement["disagreement"]["numerator"], 3)
        self.assertEqual(agreement["v2_model_labels"],
                         {"SEMANTICALLY_PRESENT": 20, "ABSENT_OR_INCORRECT": 0, "AMBIGUOUS": 0})
        self.assertEqual(agreement["human_labels"],
                         {"SEMANTICALLY_PRESENT": 17, "ABSENT_OR_INCORRECT": 2, "AMBIGUOUS": 1})
        mechanisms = {item["fact_id"]: item["mechanism"]
                      for item in agreement["disagreement"]["items"]}
        self.assertEqual(mechanisms["VAL-001-039-F02"], "anchor_drift_false_present")
        self.assertEqual(mechanisms["VAL-001-050-F01"],
                         "over_lenient_semantic_match_incomplete_proposition_coverage")
        self.assertEqual(mechanisms["VAL-001-008-F02"], "non_atomic_anchor_target_ambiguity")
        attributed = {item["fact_id"]: item["attributed_to"]
                      for item in agreement["disagreement"]["items"]}
        self.assertEqual(attributed["VAL-001-008-F02"], "evaluation_case_representation")
        self.assertEqual(attributed["VAL-001-039-F02"], "v2_adjudicator")

    def test_source_artifacts_unchanged_and_model_results_not_overwritten(self) -> None:
        for relative, digest in self.cohort["source_artifacts"].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        self.assertEqual(self.cohort["source_artifacts"]["eval/results/"
                                                         "measurement_validity_audit_v2.json"],
                         fmv.FROZEN_EXPECTED_SHA256["eval/results/"
                                                    "measurement_validity_audit_v2.json"])
        self.assertEqual(self.v2["v1_reference_sha256"],
                         self.cohort["source_artifacts"]["eval/results/"
                                                         "measurement_validity_audit.json"])
        model_artifacts = json.dumps(self.v1) + json.dumps(self.v2)
        self.assertNotIn("human_adjudication", model_artifacts)
        self.assertNotIn("human_note", model_artifacts)

    def test_covered_side_separates_model_evidence_from_human_gold(self) -> None:
        covered = self.cohort["covered_side"]
        self.assertEqual(covered["v2_model_labels"], {"SEMANTICALLY_PRESENT": 40})
        self.assertEqual(covered["covered_sample_size"], 40)
        self.assertEqual(covered["human_reviewed_subset_size"], 10)
        self.assertEqual(len(covered["human_reviewed_fact_ids"]), 10)
        self.assertEqual(covered["human_confirmed_present"], 10)
        self.assertEqual(len(covered["model_only_fact_ids"]), 30)
        self.assertTrue(set(covered["human_reviewed_fact_ids"]).isdisjoint(
            covered["model_only_fact_ids"]))
        self.assertNotIn("human-confirmed 40/40", self.cohort["scope_note"])

    def test_production_prompt_and_frozen_benchmark_hashes_unchanged(self) -> None:
        import src.generator as gen
        self.assertEqual(self.cohort["production"]["generation_prompt_version"],
                         "grounded-policy-answer-v1")
        self.assertEqual(self.cohort["production"]["generation_prompt_version"],
                         gen.GENERATION_PROMPT_VERSION)
        self.assertEqual(self.cohort["production"]["generation_prompt_sha256"],
                         hashlib.sha256(gen.GROUNDING_SYSTEM_PROMPT.encode("utf-8")).hexdigest())
        self.assertEqual(self.cohort["production"]["generator_model"], "deepseek-v4-flash")
        validation_doc = (self.root / "eval/validation/VALIDATION.md").read_text(encoding="utf-8")
        self.assertIn(fmv.FROZEN_EXPECTED_SHA256[
            "eval/validation/broad_atomic_facts_validation_v1.json"], validation_doc)
        provenance = (self.root / "eval/PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn(fmv.FROZEN_EXPECTED_SHA256["eval/broad_queries_v3_adjudicated.json"],
                      provenance)
        self.assertIn(fmv.FROZEN_EXPECTED_SHA256[
            "eval/broad_query_v3_atomic_facts_frozen_candidate.json"], provenance)

    def test_writeback_builder_reproduces_frozen_artifact(self) -> None:
        self.assertEqual(fmv.build_document(), self.cohort)
        self.assertEqual(fmv.render_markdown(self.cohort),
                         fmv.SUMMARY.read_text(encoding="utf-8"))


class OracleRepairV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.results = json.loads(repair.RESULTS.read_text(encoding="utf-8"))
        cls.frozen = {
            "cohort": json.loads(repair.CLEANED_COHORT.read_text(encoding="utf-8")),
            "rubric": json.loads(repair.RUBRIC.read_text(encoding="utf-8")),
            "queries": json.loads(repair.QUERIES.read_text(encoding="utf-8")),
            "transfer": json.loads(repair.TRANSFER.read_text(encoding="utf-8")),
            "utilization": json.loads(repair.UTILIZATION.read_text(encoding="utf-8")),
            "index": json.loads(repair.INDEX.read_text(encoding="utf-8")),
        }
        cls.cases = repair.build_case_inputs(cls.frozen)

    def test_cohort_is_exactly_the_two_confirmed_errors(self) -> None:
        self.assertEqual(repair.REPAIR_FACT_IDS,
                         ("VAL-001-039-F02", "VAL-001-050-F01"))
        self.assertEqual(repair.EXCLUDED_FACT_IDS, ("VAL-001-008-F02",))
        self.assertEqual(self.results["cohort"]["fact_ids"],
                         ["VAL-001-039-F02", "VAL-001-050-F01"])
        self.assertEqual(self.results["cohort"]["excluded_fact_ids"], ["VAL-001-008-F02"])
        self.assertNotIn("VAL-001-008-F02",
                         [cell["fact_id"] for cell in self.results["cells"]])
        cleaned = self.frozen["cohort"]["cleaned_nominal_cohort"]
        self.assertEqual(cleaned["repair_cohort"]["fact_ids"],
                         ["VAL-001-039-F02", "VAL-001-050-F01"])
        self.assertEqual([item["fact_id"] for item in cleaned["repair_cohort"]["excluded"]],
                         ["VAL-001-008-F02"])

    def test_design_and_controls_correctly_constructed(self) -> None:
        self.assertEqual(len(repair.build_cells()), 36)
        self.assertEqual(self.results["design"]["cells"], 36)
        self.assertEqual(self.results["design"]["replicates"], 3)
        checks = repair.control_freeze_checks(self.cases)
        for fact_id, entry in checks.items():
            self.assertTrue(all(entry.values()), (fact_id, entry))
        for fact_id in repair.REPAIR_FACT_IDS:
            propositions = {condition: repair.proposition_for(fact_id, condition)
                            for condition in repair.CONDITIONS}
            self.assertEqual(len(set(propositions.values())), 3)
            self.assertNotEqual(propositions["sham_unsupported"],
                                propositions["oracle_repair"])
            self.assertNotEqual(propositions["already_present"],
                                propositions["oracle_repair"])
        for fact_id, case in self.cases.items():
            control_fact_id = repair.REPAIR_CASES[fact_id]["already_present_fact_id"]
            self.assertEqual(case["baseline_fact_status"][control_fact_id]["status"],
                             "covered")
            self.assertEqual(case["baseline_fact_status"][control_fact_id]["citation_status"],
                             "supported")

    def test_oracle_proposition_not_leaked_into_baseline(self) -> None:
        case_039 = self.cases["VAL-001-039-F02"]
        self.assertNotIn("offer", case_039["baseline_answer"].lower())
        case_050 = self.cases["VAL-001-050-F01"]
        for marker in ("before filing", "continuing to prosecute", "defensive action"):
            self.assertNotIn(marker, case_050["baseline_answer"].lower())
        for fact_id, case in self.cases.items():
            self.assertNotEqual(case["baseline_answer"].strip(),
                                repair.REPAIR_CASES[fact_id]["oracle_proposition"])

    def test_parse_and_structural_helpers(self) -> None:
        parsed = repair.parse_repair('{"assessment":"REPAIR_NEEDED",'
                                     '"proposed_patch":"p","revised_answer":"r"}')
        self.assertEqual(parsed["assessment"], "repair_needed")
        with self.assertRaises(ValueError):
            repair.parse_repair('{"assessment":"nope","proposed_patch":"p",'
                                '"revised_answer":"r"}')
        preservation = repair.sentence_preservation("One. Two. Three.", "One. Two. Four.")
        self.assertEqual(preservation["preserved"], 2)
        case = self.cases["VAL-001-039-F02"]
        messages = repair.build_repair_messages(
            case, repair.proposition_for(case["fact_id"], "oracle_repair"))
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertEqual(messages[0]["content"], repair.REPAIR_SYSTEM)
        self.assertIn(case["anchor_source_id"], messages[1]["content"])
        checks = repair.structural_checks(case["baseline_answer"], parsed, case["sources"])
        self.assertEqual(checks["baseline_words"], len(case["baseline_answer"].split()))
        self.assertFalse(checks["citation_validation"]["valid"])

    def test_frozen_inputs_and_historical_validate_artifacts_unchanged(self) -> None:
        for relative, digest in self.results["frozen_inputs"]["artifacts"].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        expected = fmv.FROZEN_EXPECTED_SHA256
        self.assertEqual(self.results["frozen_inputs"]["artifacts"][
            "eval/results/measurement_validity_audit.json"],
            expected["eval/results/measurement_validity_audit.json"])
        self.assertEqual(self.results["frozen_inputs"]["artifacts"][
            "eval/results/measurement_validity_audit_v2.json"],
            expected["eval/results/measurement_validity_audit_v2.json"])
        self.assertEqual(self.frozen["cohort"]["validate_stage"], "COMPLETE")
        for fact_id, entry in self.results["frozen_inputs"]["baselines"].items():
            case = self.cases[fact_id]
            self.assertEqual(entry["answer_sha256"], repair._stable_hash(case["baseline_answer"]))
            self.assertEqual(entry["evidence_chunk_ids"],
                             [chunk["chunk_id"] for chunk in case["chunks"]])
            self.assertEqual(entry["anchor_source_id"], case["anchor_source_id"])
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")
        self.assertEqual(self.frozen["cohort"]["production"]["generation_prompt_version"],
                         gen.GENERATION_PROMPT_VERSION)

    def test_blind_human_sheet_and_mapping(self) -> None:
        mapping = self.results["human_review"]["mapping"]
        self.assertEqual(len(mapping), 36)
        self.assertEqual(len({entry["blind_id"] for entry in mapping}), 36)
        sheet = repair.HUMAN_SHEET.read_text(encoding="utf-8")
        self.assertEqual(sheet.count("\n## R"), 36)
        for token in ("deepseek", "::current::", "::stronger::", "cell_id"):
            self.assertNotIn(token, sheet)
        self.assertEqual(self.results["human_review"]["status"], "pending")

    def test_results_record_all_cells_and_usage(self) -> None:
        self.assertEqual(len(self.results["cells"]), 36)
        self.assertEqual(self.results["failures"], [])
        self.assertTrue(self.results["dry_runs"]["current"]["ok"])
        self.assertTrue(self.results["dry_runs"]["stronger"]["ok"])
        for cell in self.results["cells"]:
            self.assertIsNotNone(cell["provider_usage"])
            self.assertIsNotNone(cell["structural_checks"])
            self.assertIn("verdict", cell)
            self.assertEqual(cell["fact_id"],
                             next(fid for fid in repair.REPAIR_FACT_IDS
                                  if cell["cell_id"].startswith(fid)))


class OracleRepairHumanPrimaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.artifact = json.loads(repair_final.SCORED.read_text(encoding="utf-8"))
        cls.raw = json.loads(repair.RESULTS.read_text(encoding="utf-8"))
        cls.scores = {entry["blind_id"]: entry
                      for entry in cls.artifact["human_scores"]}
        cls.raw_mapping = {entry["blind_id"]: entry
                           for entry in cls.raw["human_review"]["mapping"]}
        cls.per_blind = {entry["blind_id"]: entry
                         for entry in cls.artifact["unblinded"]["per_blind"]}

    def test_blind_human_labels_written_back(self) -> None:
        self.assertEqual(len(self.scores), 36)
        classes = {blind_id: entry["class"] for blind_id, entry in self.scores.items()}
        for blind_id in repair_final.GENUINE_FULL:
            self.assertEqual(classes[blind_id], "genuine_full_pass")
        for blind_id in repair_final.GENUINE_NO_REPAIR:
            self.assertEqual(classes[blind_id], "genuine_no_repair")
            self.assertIn("failed to identify required repair", self.scores[blind_id]["note"])
        for blind_id in repair_final.GENUINE_PARTIAL:
            self.assertEqual(classes[blind_id], "genuine_semantic_partial")
            self.assertTrue(self.scores[blind_id]["proposition_present"])
            self.assertFalse(self.scores[blind_id]["minimal_edit"])
        for blind_id in repair_final.SHAM_PASS:
            self.assertEqual(classes[blind_id], "sham_refusal_pass")
        for blind_id in repair_final.ALREADY_PRESENT_PASS:
            self.assertEqual(classes[blind_id], "already_present_pass")
        self.assertEqual(len(repair_final.GENUINE_FULL) + len(repair_final.GENUINE_NO_REPAIR)
                         + len(repair_final.GENUINE_PARTIAL), 12)

    def test_blinded_aggregate_matches_frozen_review(self) -> None:
        aggregate = self.artifact["blinded_human_aggregate_before_unblinding"]
        self.assertEqual(aggregate["genuine_repair"],
                         {"outputs": 12, "semantic_repair_success": 7,
                          "full_constraint_compliant_success": 3,
                          "semantic_success_constraint_failed": 4, "no_repair": 5})
        self.assertEqual(aggregate["sham_unsupported"],
                         {"refusal": 12, "unsupported_generation": 0})
        self.assertEqual(aggregate["already_present"], {"correct_noop": 12})
        self.assertEqual(aggregate["control_degradation"], 0)

    def test_unblind_mapping_comes_from_raw_results(self) -> None:
        self.assertEqual(set(self.per_blind), set(self.raw_mapping))
        for blind_id, source in self.raw_mapping.items():
            entry = self.per_blind[blind_id]
            for field in ("cell_id", "fact_id", "condition", "model_key", "replicate"):
                self.assertEqual(entry[field], source[field], (blind_id, field))
        condition_by_class = {"genuine": "oracle_repair", "sham": "sham_unsupported",
                              "already_present": "already_present"}
        for blind_id, entry in self.per_blind.items():
            family = ("genuine" if entry["class"].startswith("genuine") else
                      "sham" if entry["class"].startswith("sham") else "already_present")
            self.assertEqual(entry["condition"], condition_by_class[family])

    def test_per_model_official_results(self) -> None:
        by_model = self.artifact["unblinded"]["by_model"]
        current = by_model["current"]["genuine_repair"]
        self.assertEqual(current["semantic_repair_success"], 1)
        self.assertEqual(current["full_constraint_compliant_success"], 0)
        self.assertEqual(current["no_repair"], 5)
        self.assertEqual(current["repair_decision_errors"],
                         {"not_supported_false_refusal": 2,
                          "already_present_false_refusal": 3,
                          "attempted_repair_constraint_failure": 1})
        stronger = by_model["stronger"]["genuine_repair"]
        self.assertEqual(stronger["semantic_repair_success"], 6)
        self.assertEqual(stronger["full_constraint_compliant_success"], 3)
        self.assertEqual(stronger["semantic_success_constraint_failed"], 3)
        self.assertEqual(stronger["no_repair"], 0)
        for model_key in ("current", "stronger"):
            self.assertEqual(by_model[model_key]["sham_unsupported"]["refusal_pass"], 6)
            self.assertEqual(by_model[model_key]["sham_unsupported"]["unsupported_generation"], 0)
            self.assertEqual(by_model[model_key]["already_present"]["correct_noop_pass"], 6)
            self.assertEqual(by_model[model_key]["already_present"]["degradation"], 0)

    def test_url_violation_is_separated_from_semantic_success(self) -> None:
        partials = [entry for entry in self.per_blind.values()
                    if entry["class"] == "genuine_semantic_partial"]
        self.assertEqual(len(partials), 4)
        self.assertTrue(all(entry["proposition_present"] for entry in partials))
        self.assertTrue(all(not entry["unsupported_or_contradicted"] for entry in partials))
        stronger_partials = [entry for entry in partials if entry["model_key"] == "stronger"]
        self.assertEqual(len(stronger_partials), 3)
        self.assertTrue(all(entry["fact_id"] == "VAL-001-039-F02"
                            for entry in stronger_partials))
        self.assertEqual(self.artifact["unblinded"]["by_model"]["stronger"]["genuine_repair"]
                         ["url_constraint_violations_on_039"], 3)

    def test_raw_results_and_frozen_artifacts_unchanged(self) -> None:
        artifacts = self.artifact["source_artifacts"]
        for relative, digest in artifacts.items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        self.assertEqual(self.raw["status"], "complete_pending_human_primary_scoring")
        self.assertEqual(self.raw["human_review"]["status"], "pending")
        expected = fmv.FROZEN_EXPECTED_SHA256
        self.assertEqual(artifacts["eval/results/measurement_validity_audit.json"],
                         expected["eval/results/measurement_validity_audit.json"])
        self.assertEqual(artifacts["eval/results/measurement_validity_audit_v2.json"],
                         expected["eval/results/measurement_validity_audit_v2.json"])
        self.assertEqual(artifacts["eval/validation/broad_atomic_facts_validation_v1.json"],
                         expected["eval/validation/broad_atomic_facts_validation_v1.json"])
        self.assertEqual(artifacts["eval/validation/broad_queries_validation_v1.json"],
                         expected["eval/validation/broad_queries_validation_v1.json"])
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")

    def test_stage_and_final_summaries(self) -> None:
        final = repair_final.MACHINE_SUMMARY.read_text(encoding="utf-8")
        self.assertIn("Human-primary final results (frozen)", final)
        self.assertIn("Case B", final)
        self.assertIn("Repairability = COMPLETE", final)
        self.assertIn("pre-human-primary readout", final)
        stage = repair_final.STAGE_SUMMARY.read_text(encoding="utf-8")
        self.assertIn("Repairability = COMPLETE", stage)
        for hypothesis in ("H1.", "H2.", "H3."):
            self.assertIn(hypothesis, stage)
        human = repair_final.HUMAN_SUMMARY.read_text(encoding="utf-8")
        self.assertIn("full constraint-compliant success", human)
        self.assertEqual(self.artifact["repairability_stage"], "COMPLETE")
        self.assertEqual(self.artifact["repairability_case"]["case"], "B")

    def test_writeback_builder_reproduces_frozen_artifact(self) -> None:
        self.assertEqual(repair_final.build_document(), self.artifact)


class SemanticGapDiscriminationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.artifact = json.loads(sgd.RESULTS.read_text(encoding="utf-8"))
        cls.dataset = sgd.build_dataset()
        sgd.validate_dataset(cls.dataset)
        cls.items = {item["item_id"]: item for item in cls.dataset["items"]}
        cls.cells = cls.artifact["cells"]
        cls.aggregates = cls.artifact["aggregates"]

    def test_dataset_composition_and_sources(self) -> None:
        self.assertEqual(self.artifact["dataset"]["composition"],
                         {"MISSING": 2, "ALREADY_PRESENT": 19, "UNSUPPORTED": 6, "items": 27})
        missing_ids = [item["fact_id"] for item in self.dataset["items"]
                       if item["gold"] == "MISSING"]
        cohort = json.loads(sgd.CLEANED_COHORT.read_text(encoding="utf-8"))
        confirmed = [entry["fact_id"] for entry in
                     cohort["cleaned_nominal_cohort"]["confirmed_errors"]]
        self.assertEqual(missing_ids, confirmed)
        self.assertNotIn("VAL-001-008-F02", missing_ids)
        self.assertFalse(any(item["fact_id"] == "VAL-001-008-F02"
                             for item in self.dataset["items"]))
        writeback = {entry["fact_id"]: entry for entry in
                     cohort["human_review"]["frozen_human_review_writeback"]}
        mva_present = [item for item in self.dataset["items"]
                       if item["source"] == "mva_human_present"]
        self.assertEqual(len(mva_present), 17)
        for item in mva_present:
            self.assertEqual(writeback[item["fact_id"]]["human_adjudication"],
                             "SEMANTICALLY_PRESENT")
        controls = {item["fact_id"] for item in self.dataset["items"]
                    if item["source"] == "oracle_repair_control"}
        self.assertEqual(controls, set(sgd.CONTROL_PRESENT_FACT_IDS))
        for item in self.dataset["items"]:
            if item["gold"] == "UNSUPPORTED":
                self.assertTrue(item["validation"])
                for marker in item["markers"]:
                    self.assertNotIn(marker, item["evidence_joined"])

    def test_prompt_is_shared_and_labels_do_not_leak(self) -> None:
        for item_id, item in self.items.items():
            messages = sgd.build_messages(item)
            self.assertEqual(messages[0]["content"], sgd.CLASSIFIER_SYSTEM)
            for token in sgd.LABELS:
                self.assertNotIn(token, messages[1]["content"], item_id)
            for token in ("sham", "gold", "oracle_repair"):
                self.assertNotIn(token, messages[1]["content"].lower(), item_id)
        by_item: dict[str, set] = {}
        for cell in self.cells:
            by_item.setdefault(cell["item_id"], set()).add(cell["prompt_config_hash"])
        self.assertTrue(all(len(hashes) == 1 for hashes in by_item.values()))
        for item_id, item in self.items.items():
            expected = sgd._stable_hash({"messages": sgd.build_messages(item),
                                         "temperature": sgd.TEMPERATURE,
                                         "max_tokens": sgd.MAX_TOKENS,
                                         "version": sgd.VERSION})
            self.assertEqual(by_item[item_id], {expected})
        self.assertEqual(self.artifact["design"]["replicates"], 3)
        self.assertEqual(len(self.cells), 162)

    def test_confusion_and_metrics_frozen(self) -> None:
        current = self.aggregates["current"]
        self.assertEqual(current["confusion"]["matrix"]["MISSING"],
                         {"MISSING": 1, "ALREADY_PRESENT": 1, "UNSUPPORTED": 0})
        self.assertEqual(current["confusion"]["matrix"]["ALREADY_PRESENT"],
                         {"MISSING": 1, "ALREADY_PRESENT": 18, "UNSUPPORTED": 0})
        self.assertEqual(current["confusion"]["matrix"]["UNSUPPORTED"],
                         {"MISSING": 0, "ALREADY_PRESENT": 0, "UNSUPPORTED": 6})
        self.assertEqual(current["per_class_recall"]["ALREADY_PRESENT"]["numerator"], 18)
        self.assertEqual(current["missing_errors"],
                         {"to_already_present": 1, "to_unsupported": 0,
                          "unresolved_inconsistent": 0})
        self.assertEqual(current["consistency"], {"3/3": 26, "2/3": 1, "1/3": 0})
        stronger = self.aggregates["stronger"]
        self.assertEqual(stronger["per_class_recall"]["ALREADY_PRESENT"]["numerator"], 14)
        self.assertEqual(stronger["confusion"]["matrix"]["ALREADY_PRESENT"]["MISSING"], 5)
        self.assertEqual(stronger["missing_errors"],
                         {"to_already_present": 1, "to_unsupported": 0,
                          "unresolved_inconsistent": 0})
        self.assertEqual(stronger["per_class_recall"]["UNSUPPORTED"]["numerator"], 6)
        outcome = self.aggregates["preregistered_outcome"]
        self.assertEqual(outcome["outcome"], "mixed/unresolved")
        self.assertEqual(outcome["039_current"], "MISSING")
        self.assertEqual(outcome["039_stronger"], "MISSING")
        self.assertEqual(outcome["050_current"], "ALREADY_PRESENT")
        self.assertEqual(outcome["050_stronger"], "ALREADY_PRESENT")
        self.assertEqual(current["auxiliary"]["invalid_evidence_source_ids_cells"], 0)
        self.assertEqual(stronger["auxiliary"]["invalid_evidence_source_ids_cells"], 0)

    def test_aggregate_recompute_is_deterministic(self) -> None:
        self.assertEqual(sgd.summarize(self.dataset, self.cells), self.aggregates)

    def test_frozen_inputs_and_historical_artifacts_untouched(self) -> None:
        for relative, digest in self.artifact["frozen_inputs"].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        self.assertEqual(self.artifact["preregistration"]["sha256"],
                         hashlib.sha256(sgd.PREREG.read_bytes()).hexdigest())
        expected = fmv.FROZEN_EXPECTED_SHA256
        for relative in ("eval/results/measurement_validity_audit.json",
                         "eval/results/measurement_validity_audit_v2.json",
                         "eval/validation/broad_atomic_facts_validation_v1.json",
                         "eval/validation/broad_queries_validation_v1.json"):
            self.assertEqual(self.artifact["frozen_inputs"][relative], expected[relative])
        repaired = json.loads(repair.RESULTS.read_text(encoding="utf-8"))
        scored = json.loads(repair_final.SCORED.read_text(encoding="utf-8"))
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/oracle_repair_v1_results.json"],
            hashlib.sha256(repair.RESULTS.read_bytes()).hexdigest())
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/oracle_repair_v1_human_scored.json"],
            hashlib.sha256(repair_final.SCORED.read_bytes()).hexdigest())
        self.assertEqual(repaired["status"], "complete_pending_human_primary_scoring")
        self.assertEqual(scored["repairability_stage"], "COMPLETE")
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")

    def test_mechanism_h1_stage_summary(self) -> None:
        summary = (self.root / "eval/results/mechanism_h1_stage_summary.md").read_text(
            encoding="utf-8")
        self.assertIn("mixed/unresolved", summary)
        self.assertIn("H2", summary)
        self.assertIn("H3", summary)
        self.assertIn("1/2", summary)
        self.assertIn("18/19", summary)
        self.assertIn("14/19", summary)


class TaskConditionedActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.artifact = json.loads(tca.RESULTS.read_text(encoding="utf-8"))
        cls.dataset, cls.h1 = tca.load_frozen_dataset()
        cls.cells = cls.artifact["cells"]
        cls.aggregates = cls.artifact["aggregates"]

    def test_h1_dataset_reused_exactly(self) -> None:
        fields = ("item_id", "gold", "source", "fact_id", "case_id", "proposition")
        projected = [{key: item[key] for key in fields} for item in self.dataset["items"]]
        h1_projected = [{key: item[key] for key in fields}
                        for item in self.h1["dataset"]["items"]]
        self.assertEqual(projected, h1_projected)
        self.assertEqual(len(projected), 27)
        self.assertFalse(any(item["fact_id"] == "VAL-001-008-F02"
                             for item in self.dataset["items"]))
        self.assertTrue(self.artifact["dataset"]["reused_from_h1"])

    def test_only_framing_changes_between_b_and_c(self) -> None:
        item = self.dataset["items"][0]
        prefix = tca.context_block(item)
        message_b = tca.build_messages(item, "B")
        message_c = tca.build_messages(item, "C")
        self.assertTrue(message_b[1]["content"].startswith(prefix))
        self.assertTrue(message_c[1]["content"].startswith(prefix))
        suffix_b = message_b[1]["content"][len(prefix):]
        suffix_c = message_c[1]["content"][len(prefix):]
        self.assertNotEqual(suffix_b, suffix_c)
        self.assertNotEqual(message_b[0]["content"], message_c[0]["content"])
        hashes: dict[tuple[str, str], set] = {}
        for cell in self.cells:
            hashes.setdefault((cell["item_id"], cell["frame"]), set()).add(
                cell["prompt_config_hash"])
        for item_entry in self.dataset["items"]:
            for frame in ("B", "C"):
                self.assertEqual(len(hashes[(item_entry["item_id"], frame)]), 1)
        self.assertEqual(len(self.cells), 324)

    def test_no_repair_text_is_allowed(self) -> None:
        self.assertIn("Do not generate, patch, rewrite", tca.FRAME_SYSTEMS["B"])
        self.assertIn("Never output a patch", tca.FRAME_SYSTEMS["C"])
        for cell in self.cells:
            parsed = cell["parsed"]
            self.assertIsNotNone(parsed)
            self.assertEqual(set(parsed), {"decision", "evidence_source_ids", "brief_reason",
                                           "reason_words"})
            self.assertNotIn("revised_answer", parsed)
            self.assertNotIn("proposed_patch", parsed)

    def test_canonical_mapping_and_parsing(self) -> None:
        self.assertEqual(tca.canonical("MISSING"), "REPAIR")
        self.assertEqual(tca.canonical("REPAIR_NEEDED"), "REPAIR")
        self.assertEqual(tca.canonical("WOULD_REPAIR"), "REPAIR")
        self.assertEqual(tca.canonical("NO_CHANGE_ALREADY_PRESENT"), "NO_CHANGE_PRESENT")
        self.assertEqual(tca.canonical("WOULD_NOT_REPAIR_ALREADY_PRESENT"),
                         "NO_CHANGE_PRESENT")
        self.assertEqual(tca.canonical("UNSUPPORTED"), "NO_CHANGE_UNSUPPORTED")
        self.assertIsNone(tca.canonical("NOPE"))
        parsed = tca.parse_decision('{"decision":"no_change_unsupported",'
                                    '"evidence_source_ids":["S1"],"brief_reason":"x"}', "B")
        self.assertEqual(parsed["decision"], "NO_CHANGE_UNSUPPORTED")
        with self.assertRaises(ValueError):
            tca.parse_decision('{"decision":"WOULD_REPAIR"}', "B")

    def test_frozen_artifacts_untouched(self) -> None:
        for relative, digest in self.artifact["frozen_inputs"].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        expected = fmv.FROZEN_EXPECTED_SHA256
        for relative in ("eval/results/measurement_validity_audit.json",
                         "eval/results/measurement_validity_audit_v2.json",
                         "eval/validation/broad_atomic_facts_validation_v1.json",
                         "eval/validation/broad_queries_validation_v1.json"):
            self.assertEqual(self.artifact["frozen_inputs"][relative], expected[relative])
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/semantic_gap_discrimination_v1_results.json"],
            hashlib.sha256(sgd.RESULTS.read_bytes()).hexdigest())
        repair_scored = json.loads(repair_final.SCORED.read_text(encoding="utf-8"))
        self.assertEqual(repair_scored["repairability_stage"], "COMPLETE")
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")

    def test_aggregates_and_outcomes_frozen(self) -> None:
        current = self.aggregates["current"]
        self.assertEqual(current["transitions_A_to_B"]["REPAIR"]["NO_CHANGE_UNSUPPORTED"], 2)
        self.assertEqual(current["transitions_A_to_B"]["REPAIR"]["REPAIR"], 0)
        self.assertEqual(current["transitions_A_to_C"]["REPAIR"]["REPAIR"], 2)
        self.assertEqual(current["frame_consistency"]["counts"],
                         {"consistent": 24, "two_states": 3, "three_states": 0})
        self.assertEqual(current["action_accuracy"]["B"]["per_class_recall"]["REPAIR"],
                         {"numerator": 0, "denominator": 2, "recall": 0.0})
        self.assertEqual(current["action_accuracy"]["C"]["per_class_recall"]["REPAIR"],
                         {"numerator": 1, "denominator": 2, "recall": 0.5})
        stronger = self.aggregates["stronger"]
        self.assertEqual(stronger["transitions_A_to_B"]["REPAIR"],
                         {"REPAIR": 0, "NO_CHANGE_PRESENT": 4, "NO_CHANGE_UNSUPPORTED": 2,
                          "UNRESOLVED": 0})
        self.assertEqual(stronger["action_accuracy"]["B"]["per_class_recall"]["REPAIR"],
                         {"numerator": 0, "denominator": 2, "recall": 0.0})
        for model_key in ("current", "stronger"):
            for frame in ("A", "B", "C"):
                recall = self.aggregates[model_key]["action_accuracy"][frame][
                    "per_class_recall"]["NO_CHANGE_UNSUPPORTED"]
                self.assertEqual(recall["numerator"], 6)
        outcomes = self.aggregates["outcomes"]
        self.assertTrue(outcomes["OA_current_framing_shift"])
        self.assertEqual(outcomes["OA_items"], ["M-VAL-001-039-F02"])
        self.assertFalse(outcomes["OB_action_correct_but_generation_failed"])
        self.assertFalse(outcomes["OC_stronger_framing_shift"])
        self.assertFalse(outcomes["OD_unstable"])
        self.assertEqual(outcomes["overall"], "A")
        self.assertTrue(self.aggregates["refusals"]["current|VAL-001-039-F02"])
        self.assertFalse(self.aggregates["refusals"]["stronger|VAL-001-050-F01"])

    def test_key_case_readouts(self) -> None:
        current = self.aggregates["current"]["key_cases"]["M-VAL-001-039-F02"]
        self.assertEqual(current["A"]["modal"], "REPAIR")
        self.assertEqual(current["B"]["labels"],
                         ["NO_CHANGE_UNSUPPORTED"] * 3)
        self.assertEqual(current["C"]["labels"], ["WOULD_REPAIR"] * 3)
        current_050 = self.aggregates["current"]["key_cases"]["M-VAL-001-050-F01"]
        self.assertEqual(current_050["B"]["modal"], "NO_CHANGE_PRESENT")
        stronger = self.aggregates["stronger"]["key_cases"]
        self.assertEqual(stronger["M-VAL-001-039-F02"]["B"]["modal"],
                         "NO_CHANGE_UNSUPPORTED")
        self.assertEqual(stronger["M-VAL-001-050-F01"]["C"]["modal"],
                         "NO_CHANGE_UNSUPPORTED")

    def test_aggregate_recompute_is_deterministic(self) -> None:
        self.assertEqual(tca.summarize(self.dataset, self.cells, self.h1),
                         self.aggregates)

    def test_mechanism_h2_stage_summary(self) -> None:
        summary = (self.root / "eval/results/mechanism_h2_stage_summary.md").read_text(
            encoding="utf-8")
        self.assertIn("Mechanism H2 diagnostic = COMPLETE", summary)
        self.assertIn("Overall: A", summary)
        self.assertIn("action/execution", summary)
        self.assertIn("REPAIR 0/2", summary)


class DecisionExecutionCouplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.artifact = json.loads(dec.RESULTS.read_text(encoding="utf-8"))
        cls.items = dec.build_items()
        cls.cells = cls.artifact["cells"]
        cls.aggregates = cls.artifact["aggregates"]

    def test_dataset_is_frozen_confirmed_cases_and_controls(self) -> None:
        self.assertEqual(tuple(self.items), dec.ITEM_IDS)
        self.assertEqual(dec.PRIMARY_ITEMS, ("M-VAL-001-039-F02", "M-VAL-001-050-F01"))
        self.assertEqual(dec.CONTROL_ITEMS, ("P-VAL-001-050-F02", "U-039-01"))
        self.assertEqual(self.items["M-VAL-001-039-F02"]["kind"], "missing")
        self.assertEqual(self.items["M-VAL-001-050-F01"]["kind"], "missing")
        self.assertEqual(self.items["P-VAL-001-050-F02"]["kind"], "already_present_control")
        self.assertEqual(self.items["U-039-01"]["kind"], "unsupported_control")
        self.assertEqual(self.items["M-VAL-001-039-F02"]["gold_decision"], "REPAIR_NEEDED")
        self.assertEqual(self.items["U-039-01"]["gold_decision"], "NO_CHANGE_UNSUPPORTED")
        self.assertFalse(any(item["fact_id"] == "VAL-001-008-F02"
                             for item in self.items.values()))
        h1_items = {item["item_id"]: item for item in self.h1_dataset_items()}
        for item_id in dec.PRIMARY_ITEMS:
            self.assertEqual(self.items[item_id]["proposition"],
                             h1_items[item_id]["proposition"])
        self.assertEqual(self.items["P-VAL-001-050-F02"]["proposition"],
                         h1_items["P-VAL-001-050-F02"]["proposition"])
        self.assertEqual(self.items["U-039-01"]["proposition"],
                         h1_items["U-039-01"]["proposition"])

    @staticmethod
    def h1_dataset_items() -> list:
        artifact = json.loads(sgd.RESULTS.read_text(encoding="utf-8"))
        return artifact["dataset"]["items"]

    def test_only_injected_decision_changes(self) -> None:
        item = self.items["M-VAL-001-039-F02"]
        prefix = tca.context_block(item)
        injections = set()
        for decision in dec.DECISIONS:
            messages = dec.build_messages(item, decision)
            self.assertTrue(messages[1]["content"].startswith(prefix))
            injections.add(messages[1]["content"][len(prefix):])
            self.assertEqual(messages[0]["content"], dec.DECISION_SYSTEM[decision])
        self.assertEqual(len(injections), 3)
        hashes: dict[tuple[str, str], set] = {}
        for cell in self.cells:
            hashes.setdefault((cell["item_id"], cell["decision"]), set()).add(
                cell["prompt_config_hash"])
        for item_id in dec.ITEM_IDS:
            for decision in dec.DECISIONS:
                self.assertEqual(len(hashes[(item_id, decision)]), 1)
        self.assertEqual(len(self.cells), 72)

    def test_no_gold_leakage_in_user_messages(self) -> None:
        for item_id, item in self.items.items():
            for decision in dec.DECISIONS:
                user = dec.build_messages(item, decision)[1]["content"].lower()
                for token in ("gold", "human", "sham", "already_present_control",
                              "unsupported_control"):
                    self.assertNotIn(token, user, (item_id, decision))

    def test_baseline_and_evidence_frozen_and_historical_artifacts_untouched(self) -> None:
        for relative, digest in self.artifact["frozen_inputs"].items():
            self.assertEqual(hashlib.sha256((self.root / relative).read_bytes()).hexdigest(),
                             digest, relative)
        expected = fmv.FROZEN_EXPECTED_SHA256
        for relative in ("eval/results/measurement_validity_audit.json",
                         "eval/results/measurement_validity_audit_v2.json",
                         "eval/validation/broad_atomic_facts_validation_v1.json",
                         "eval/validation/broad_queries_validation_v1.json"):
            self.assertEqual(self.artifact["frozen_inputs"][relative], expected[relative])
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/semantic_gap_discrimination_v1_results.json"],
            hashlib.sha256(sgd.RESULTS.read_bytes()).hexdigest())
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/task_conditioned_action_v1_results.json"],
            hashlib.sha256(tca.RESULTS.read_bytes()).hexdigest())
        self.assertEqual(self.artifact["frozen_inputs"][
            "eval/results/oracle_repair_v1_results.json"],
            hashlib.sha256(repair.RESULTS.read_bytes()).hexdigest())
        h1 = self.h1_dataset_items()
        self.assertEqual(len(h1), 27)
        import src.generator as gen
        self.assertEqual(gen.GENERATION_PROMPT_VERSION, "grounded-policy-answer-v1")

    def test_adherence_scoring_is_deterministic(self) -> None:
        item = self.items["M-VAL-001-039-F02"]
        baseline = item["baseline_answer"]
        d1_edit = dec.execution_checks(item, "D1", {
            "execution_status": "REPAIRED", "proposed_patch": "p",
            "revised_answer": baseline + " added [S1]", "brief_note": ""})
        self.assertTrue(d1_edit["adherence"])
        d1_noop = dec.execution_checks(item, "D1", {
            "execution_status": "REPAIRED", "proposed_patch": "p",
            "revised_answer": baseline, "brief_note": ""})
        self.assertFalse(d1_noop["adherence"])
        d2_noop = dec.execution_checks(item, "D2", {
            "execution_status": "NO_CHANGE", "proposed_patch": "",
            "revised_answer": baseline, "brief_note": ""})
        self.assertTrue(d2_noop["adherence"])
        d2_edit = dec.execution_checks(item, "D2", {
            "execution_status": "NO_CHANGE", "proposed_patch": "p",
            "revised_answer": baseline + " x", "brief_note": ""})
        self.assertFalse(d2_edit["adherence"])
        self.assertEqual(dec.summarize(self.cells), self.aggregates)

    def test_primary_results_and_outcomes_frozen(self) -> None:
        current = self.aggregates["current"]
        stronger = self.aggregates["stronger"]
        for model_key, block in (("current", current), ("stronger", stronger)):
            self.assertEqual(block["decisions"]["D1"]["adherence"], 6, model_key)
            self.assertEqual(block["decisions"]["D1"]["actual_repairs"], 6, model_key)
            self.assertEqual(block["decisions"]["D1"]["secondary_target_correct"], 6, model_key)
            self.assertEqual(block["decisions"]["D1"]["explicit_overrides"], 0, model_key)
            self.assertEqual(block["decisions"]["D3"]["adherence"], 6, model_key)
            self.assertTrue(block["OA"], model_key)
            self.assertFalse(block["OB"], model_key)
        self.assertEqual(current["decisions"]["D2"]["adherence"], 6)
        self.assertEqual(stronger["decisions"]["D2"]["adherence"], 5)
        self.assertEqual(current["rates"]["d1_repair_rate"], 1.0)
        self.assertEqual(current["rates"]["d23_noop_rate"], 1.0)
        self.assertEqual(stronger["rates"]["d23_noop_rate"], 11 / 12)
        self.assertEqual(current["decisions"]["controls"]["unsupported_D1_insertions"], 0)
        self.assertEqual(stronger["decisions"]["controls"]["unsupported_D1_insertions"], 3)
        self.assertEqual(current["decisions"]["controls"]
                         ["already_present_D1_unnecessary_repairs"], 0)
        self.assertEqual(stronger["decisions"]["controls"]
                         ["already_present_D1_unnecessary_repairs"], 1)
        outcomes = self.aggregates["outcomes"]
        self.assertEqual(outcomes["overall"], "A")
        self.assertFalse(outcomes["OC_model_split"])
        self.assertFalse(outcomes["OD_controllable_but_safety_critical"])
        self.assertEqual(len(self.artifact["failures"]), 1)
        self.assertEqual(self.artifact["failures"][0]["cell_id"],
                         "M-VAL-001-039-F02::stronger::D2::r1")

    def test_human_sheet_and_stage_summary(self) -> None:
        mapping = self.artifact["human_review"]["mapping"]
        self.assertEqual(len(mapping), 72)
        self.assertEqual(len({entry["blind_id"] for entry in mapping}), 72)
        sheet = dec.HUMAN_SHEET.read_text(encoding="utf-8")
        self.assertEqual(sheet.count("\n## X"), 72)
        self.assertNotIn("deepseek", sheet)
        summary = (self.root / "eval/results/mechanism_h3_stage_summary.md").read_text(
            encoding="utf-8")
        self.assertIn("Mechanism H3 diagnostic = COMPLETE", summary)
        self.assertIn("Overall: A", summary)
        self.assertIn("strong decision", summary)
        self.assertIn("H4", summary)


class Stage0FreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.config = json.loads(stage0.CONFIG.read_text(encoding="utf-8"))
        cls.router = json.loads(stage0.ROUTER.read_text(encoding="utf-8"))
        cls.arms = json.loads(stage0.ARMS.read_text(encoding="utf-8"))
        cls.worksheet = json.loads(stage0.WORKSHEET.read_text(encoding="utf-8"))
        cls.replay = json.loads(stage0.OUTPUT.read_text(encoding="utf-8"))
        cls.context = stage0._load_context()
        cls.context_replay = stage0.replay_policies(cls.context)

    def test_artifact_hashes_frozen(self) -> None:
        for relative, expected in self.config["artifact_hashes"].items():
            digest = hashlib.sha256((self.root / relative).read_bytes()).hexdigest()
            self.assertEqual(digest, expected, relative)
        self.assertEqual(len(self.config["artifact_hashes"]), 36)

    def test_router_rule_frozen_and_distribution(self) -> None:
        v1 = {case["case_id"]: stage0.route_query(case["query"])
              for case in self.context["queries"]["cases"]}
        self.assertEqual(v1, self.router["distribution"]["validation_v1_50"]["labels"])
        self.assertEqual(Counter(v1.values()), Counter({"BROAD": 29, "SIMPLE": 21}))
        self.assertEqual(self.replay["route_distribution"]["v1_counts"],
                         {"BROAD": 29, "SIMPLE": 21})
        self.assertEqual(self.replay["route_distribution"]["v3_counts"],
                         {"BROAD": 9, "SIMPLE": 7})
        self.assertTrue(self.replay["route_distribution"]["sentinel_match_worksheet"])

    def test_arms_frozen(self) -> None:
        arms = self.arms["arms"]
        self.assertEqual(len(arms), 5)
        ids = [arm["arm_id"] for arm in arms]
        self.assertEqual(len(set(ids)), 5)
        policies = [arm["policy_id"] for arm in arms]
        for expected in ("fixed_top5", "adaptive_prefix_v1", "coverage_selector_v2",
                         "no_router_adaptive_v1", "query_router_v1"):
            self.assertIn(expected, policies)
        no_router = next(arm for arm in arms if arm["policy_id"] == "no_router_adaptive_v1")
        self.assertIn("query_text", no_router["prohibited_signals"])
        self.assertIn("stage2_shared_rerank_rule", self.arms)
        rule = self.arms["stage2_shared_rerank_rule"]
        self.assertIn("cross_query_scores_prohibited", rule)
        self.assertIn("mechanism_vs_adoption", self.arms)
        self.assertIn("no_post_filtering", self.arms["mechanism_vs_adoption"])

    def test_a0_bge_reproduction(self) -> None:
        audit = stage0.audit_a0_bge(self.context)
        self.assertEqual(audit["selected_id_mismatches"], [])
        self.assertEqual(audit["evidence_token_mismatches"], [])
        self.assertEqual(audit["available_fact_mismatches"], [])
        self.assertEqual(audit["utilization_case_id_mismatches"], [])
        self.assertEqual(audit["summary_evidence_tokens"]["stored"],
                         audit["summary_evidence_tokens"]["replayed"])
        self.assertTrue(audit["context_full_cases"]["comparable"])
        self.assertEqual(audit["context_full_cases"]["replayed"], 46)

    def test_policy_replay_matches_frozen_results(self) -> None:
        self.assertEqual(self.context_replay["table"], self.replay["policy_context_table"])
        self.assertEqual(self.context_replay["per_case"], self.replay["policy_per_case"])
        fixed = self.replay["policy_context_table"]["fixed_top5"]
        self.assertEqual(fixed["full_cases"], 46)
        self.assertEqual(fixed["total_evidence_tokens"], 91699)

    def test_provider_accounting_clean(self) -> None:
        audit = stage0.audit_provider_accounting(self.context)
        self.assertTrue(all(value == 0 for value in audit["checks"].values()))
        self.assertEqual(audit["a0_bge_provider_totals_50_cases"],
                         {"input_tokens": 110674, "output_tokens": 15982, "calls": 50})
        self.assertEqual(audit["utilization_baseline_provider_totals_46_cases"],
                         {"input_tokens": 98824, "output_tokens": 14299, "calls": 46})

    def test_human_truth_worksheet_structure(self) -> None:
        self.assertEqual(self.worksheet["status"], "pending_human_verdicts")
        self.assertEqual(self.worksheet["counts"],
                         {"validation_v1_aspects": 239, "broad_v3_required_aspects": 92,
                          "total": 331})
        self.assertEqual(len(self.worksheet["items"]), 331)
        self.assertTrue(all(item["verdict"] is None for item in self.worksheet["items"]))
        self.assertEqual(self.worksheet["sentinel_queries"],
                         ["VAL-001-002", "VAL-001-004", "VAL-001-010", "VAL-001-013",
                          "VAL-001-015", "VAL-001-027", "VAL-001-030", "VAL-001-032"])
        for item in self.worksheet["items"]:
            if item["source"] == "validation_v1_rubric":
                self.assertEqual(item["route"], stage0.route_query(item["query"]))

    def test_stage0_contracts_present(self) -> None:
        human = (self.root / "eval/human_truth_contract_v1.md").read_text(encoding="utf-8")
        economics = (self.root / "eval/economics_contract_v1.md").read_text(encoding="utf-8")
        self.assertIn("QUERY_REQUIRED", human)
        self.assertIn("shrinkage", human.lower())
        self.assertIn("Material benefit", economics)
        self.assertIn("provider input tokens", economics)
        require_gates = self.replay["gates"]
        self.assertTrue(require_gates["frozen_artifacts_replayable"])
        self.assertTrue(require_gates["artifact_hashes_verified"])
        self.assertTrue(require_gates["token_accounting_reliable"])
        self.assertTrue(require_gates["human_verdicts_pending"])
