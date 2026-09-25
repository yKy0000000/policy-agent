"""Long-lived invariants for the frozen evidence evaluation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import tempfile
import unittest
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
