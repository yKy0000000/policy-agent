"""Offline Stage 1 identity, reuse, and fail-closed checks."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eval import run_query_aware_stage1 as stage1
from src.generator import GROUNDING_SYSTEM_PROMPT


class Stage1PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = stage1.build_plan()
        cls.config = stage1.load(stage1.ROOT / "eval/query_aware_stage0_config.json")
        cls.router = stage1.load(stage1.ROOT / "eval/query_aware_router_v1.json")
        cls.arms = stage1.load(stage1.ROOT / "eval/query_aware_arms_v1.json")
        cls.index = stage1.load(stage1.ROOT / "cache/policy_index.json")
        cls.chunks = {item["chunk_id"]: item for item in cls.index["chunks"]}
        cls.row = cls.plan["cases"][0]
        cls.legacy_cache = stage1.load(stage1.ROOT / "cache/validation_v1_llm_cache.json")
        cls.price_table = {"input_per_million": 1, "output_per_million": 2}

    def synthetic_results(self):
        rows = []
        for planned in self.plan["cases"]:
            row = copy.deepcopy(planned)
            if row["requires_provider_call"]:
                generation = {"provider": "synthetic", "model": row["generation_model"],
                    "input_tokens": 1000, "output_tokens": 200, "latency_seconds": 1.0,
                    "cache_hit": False, "error": None, "retry_count": 0,
                    "request_id": None, "estimated_cost": 0.0014}
            else:
                generation = {"cache_hit": True}
            row["telemetry"] = {"rewrite": {"invoked": False, "cache_hit": False},
                                "generation": generation}
            row["validation"] = {"valid": True}
            rows.append(row)
        return rows

    def synthetic_economics(self):
        return stage1.aggregate_live_results(self.synthetic_results(),
            price_table=self.price_table, legacy_cache=self.legacy_cache)

    def identity(self, *, chunks=None, model=None, rewritten=None):
        row = self.row
        selected = chunks or [self.chunks[cid] for cid in row["selected_chunk_ids"]]
        policy = next(arm for arm in self.arms["arms"] if arm["policy_id"] == row["arm"])
        return stage1.canonical_identity(row["case_id"], row["original_query"],
            rewritten or row["rewritten_query"], selected,
            model or row["generation_model"], policy,
            self.plan["frozen_integrity"]["artifact_hashes"])

    def test_frozen_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "eval/query_aware_stage0_config.json"
            path.parent.mkdir()
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "frozen hash mismatch"):
                stage1.check_hashes(Path(temp))

    def test_missing_frozen_artifact_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "missing frozen artifact"):
                stage1.check_hashes(Path(temp))

    def test_frozen_arm_mismatch_fails(self):
        arms = copy.deepcopy(self.arms)
        arms["arms"][1]["params"]["initial_k"] += 1
        with self.assertRaisesRegex(ValueError, "frozen arm mismatch"):
            stage1.validate_arms(arms, self.config, self.router)

    def test_unknown_policy_fails(self):
        arms = copy.deepcopy(self.arms)
        arms["arms"][0]["policy_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "frozen arm mismatch"):
            stage1.validate_arms(arms, self.config, self.router)

    def test_route_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "route mismatch"):
            stage1.validate_route(self.row["case_id"], self.row["original_query"],
                                  self.router, "SIMPLE" if self.row["route"] == "BROAD" else "BROAD")

    def test_identical_input_reuses(self):
        left = self.identity()
        right = self.identity()
        self.assertEqual(left["generation_key"], right["generation_key"])
        self.assertTrue(stage1.same_generation_input(left["canonical"], right["canonical"]))
        self.assertEqual(self.plan["per_arm"]["fixed_top5"]["exact_reuse"], 50)

    def test_same_chunks_different_serialized_input_no_reuse(self):
        original = self.identity()
        chunks = [copy.deepcopy(self.chunks[cid]) for cid in self.row["selected_chunk_ids"]]
        chunks[0]["title"] += " changed"
        changed = self.identity(chunks=chunks)
        self.assertEqual(original["canonical"]["selected_chunk_ids"], changed["canonical"]["selected_chunk_ids"])
        self.assertNotEqual(original["context_hash"], changed["context_hash"])
        self.assertFalse(stage1.same_generation_input(original["canonical"], changed["canonical"]))

    def test_same_context_different_model_or_prompt_no_reuse(self):
        original = self.identity()
        other_model = self.identity(model="another-model")
        self.assertEqual(original["context_hash"], other_model["context_hash"])
        self.assertFalse(stage1.same_generation_input(original["canonical"], other_model["canonical"]))
        with patch.object(stage1, "build_grounded_messages", wraps=stage1.build_grounded_messages) as builder:
            altered = self.identity()
            self.assertTrue(builder.called)
        prompt_changed = copy.deepcopy(original["canonical"])
        prompt_changed["messages"][0]["content"] += " changed"
        self.assertFalse(stage1.same_generation_input(original["canonical"], prompt_changed))
        self.assertEqual(original["context_hash"], altered["context_hash"])

    def test_cross_arm_identical_input_shared(self):
        rows = [row for row in self.plan["cases"] if row["cross_arm_shared"]]
        self.assertTrue(rows)
        first = rows[0]
        peers = [row for row in self.plan["cases"] if row["canonical_input_hash"] == first["canonical_input_hash"]]
        self.assertGreater(len({row["arm"] for row in peers}), 1)
        self.assertEqual({row["generation_source"] for row in peers}, {first["generation_source"]})

    def test_dry_run_never_invokes_llm_client(self):
        with patch("src.llm_client.OpenAIChatCompletionsClient", side_effect=AssertionError("LLM called")):
            plan = stage1.build_plan()
        self.assertEqual(plan["llm_calls_made"], 0)

    def test_human_truth_never_enters_generation_prompt(self):
        identity = self.identity()
        messages = identity["canonical"]["messages"]
        self.assertEqual(messages[0]["content"], GROUNDING_SYSTEM_PROMPT)
        self.assertNotIn("QUERY_REQUIRED", str(messages))
        self.assertNotIn("frozen_human_verdicts", str(messages))

    def test_generation_key_deterministic(self):
        self.assertEqual(self.identity()["generation_key"], self.identity()["generation_key"])

    def test_conflicting_generation_key_fails(self):
        registry = {}
        stage1.register_generation_key(registry, "key", "a")
        with self.assertRaisesRegex(ValueError, "duplicate conflicting"):
            stage1.register_generation_key(registry, "key", "b")

    def test_telemetry_schema_complete(self):
        telemetry = {field: None for field in stage1.TELEMETRY_FIELDS}
        telemetry.update(provider="test", model="test", input_tokens=1, output_tokens=2,
                         latency_seconds=0.5, cache_hit=False, retry_count=0,
                         estimated_cost=0.1)
        stage1.validate_live_telemetry(telemetry)
        del telemetry["request_id"]
        with self.assertRaisesRegex(ValueError, "provider telemetry unavailable"):
            stage1.validate_live_telemetry(telemetry)

    def test_context_ordering_affects_hash(self):
        chunks = [self.chunks[cid] for cid in self.row["selected_chunk_ids"]]
        self.assertNotEqual(self.identity()["context_hash"],
                            self.identity(chunks=list(reversed(chunks)))["context_hash"])

    def test_rewrite_identity_affects_reuse(self):
        original = self.identity()
        changed = self.identity(rewritten=self.row["original_query"] + " extra")
        self.assertEqual(original["context_hash"], changed["context_hash"])
        self.assertFalse(stage1.same_generation_input(original["canonical"], changed["canonical"]))

    def test_provider_tokens_required_for_live_execution(self):
        telemetry = {field: None for field in stage1.TELEMETRY_FIELDS}
        telemetry.update(provider="test", model="test", output_tokens=2,
                         latency_seconds=0.5, cache_hit=False, retry_count=0,
                         estimated_cost=0.1)
        with self.assertRaisesRegex(ValueError, "input_tokens"):
            stage1.validate_live_telemetry(telemetry)

    def test_rewrite_cache_hit_is_not_live_call(self):
        self.assertFalse(stage1.rewrite_was_live({"invoked": True, "cache_hit": True,
                                                  "cache_key": "key"}))
        self.assertTrue(stage1.rewrite_was_live({"invoked": True, "cache_hit": False,
                                                 "cache_key": "key"}))
        with self.assertRaisesRegex(ValueError, "cache_key"):
            stage1.rewrite_was_live({"invoked": True, "cache_hit": False})

    def test_cost_requires_external_price_table(self):
        self.assertEqual(stage1.estimate_cost(1_000_000, 2_000_000,
                         {"input_per_million": 1, "output_per_million": 2}), 5)
        with self.assertRaisesRegex(ValueError, "price table"):
            stage1.estimate_cost(1, 2, {})

    def test_incomplete_generation_identity_fails(self):
        policy = self.arms["arms"][0]
        with self.assertRaisesRegex(ValueError, "incomplete generation identity"):
            stage1.canonical_identity("case", "", "", [], "model", policy, {})

    def test_shared_non_owner_receives_owner_usage(self):
        economics = self.synthetic_economics()
        cases = { (row["case_id"], row["arm"]): row
                  for row in economics["per_case_counterfactual"] }
        shared = next(row for row in self.plan["cases"]
                      if row["generation_source"] == "new" and not row["requires_provider_call"])
        owner = shared["provider_call_owner"]
        self.assertEqual(cases[(shared["case_id"], shared["arm"])]["generation_input_tokens"],
                         cases[(owner["case_id"], owner["arm"])]["generation_input_tokens"])
        self.assertEqual(cases[(shared["case_id"], shared["arm"])]["generation_output_tokens"], 200)
        self.assertEqual(cases[(shared["case_id"], shared["arm"])]["generation_usage_source"],
                         shared["reuse_source"])

    def test_shared_usage_not_double_counted_in_physical_spend(self):
        economics = self.synthetic_economics()
        physical = economics["experiment_physical_execution"]
        self.assertEqual(physical["unique_generation_calls"], 106)
        self.assertEqual(physical["provider_input_tokens"], 106_000)
        self.assertEqual(physical["provider_output_tokens"], 21_200)
        counterfactual_input = sum(row["provider_input_tokens"] for row in
                                   economics["per_arm_counterfactual"].values())
        self.assertGreater(counterfactual_input, physical["provider_input_tokens"])

    def test_legacy_reuse_uses_historical_provider_usage(self):
        economics = self.synthetic_economics()
        row = next(row for row in self.plan["cases"] if row["generation_source"] == "reused")
        key = row["reuse_source"].split(":", 1)[1]
        resolved = next(item for item in economics["per_case_counterfactual"]
                        if (item["case_id"], item["arm"]) == (row["case_id"], row["arm"]))
        self.assertEqual(resolved["generation_input_tokens"],
                         self.legacy_cache[key]["provider_usage"]["input_tokens"])
        self.assertEqual(resolved["generation_output_tokens"],
                         self.legacy_cache[key]["provider_usage"]["output_tokens"])

    def test_missing_legacy_usage_fails_closed(self):
        row = next(row for row in self.plan["cases"] if row["generation_source"] == "reused")
        key = row["reuse_source"].split(":", 1)[1]
        cache = dict(self.legacy_cache)
        cache[key] = copy.deepcopy(cache[key])
        del cache[key]["provider_usage"]["input_tokens"]
        with self.assertRaisesRegex(ValueError, "missing legacy provider usage"):
            stage1.aggregate_live_results(self.synthetic_results(),
                price_table=self.price_table, legacy_cache=cache)

    def test_router_counterfactual_economics_not_zero(self):
        economics = self.synthetic_economics()
        router = economics["per_arm_counterfactual"]["query_router_v1"]
        self.assertEqual(router["cases"], 50)
        self.assertGreater(router["provider_input_tokens"], 0)
        self.assertGreater(router["cost_per_query"], 0)

    def test_fixed_top5_cache_economics_not_zero(self):
        economics = self.synthetic_economics()
        fixed = economics["per_arm_counterfactual"]["fixed_top5"]
        self.assertEqual(fixed["reused_result_rows"], 50)
        self.assertGreater(fixed["provider_input_tokens"], 0)
        self.assertGreater(fixed["cost_per_query"], 0)

    def test_counterfactual_and_physical_accounts_are_separate(self):
        economics = self.synthetic_economics()
        self.assertIn("per_arm_counterfactual", economics)
        self.assertIn("experiment_physical_execution", economics)
        self.assertEqual(economics["per_arm_counterfactual"]["query_router_v1"]["generation_calls_if_independent"], 50)
        self.assertEqual(economics["experiment_physical_execution"]["unique_generation_calls"], 106)

    def test_unexpected_live_rewrite_fails_before_result_is_recorded(self):
        rewrite = {"invoked": True, "cache_hit": False, "cache_key": "rewrite-key"}
        with patch.object(stage1, "load", side_effect=AssertionError("should fail before index load")):
            with self.assertRaisesRegex(ValueError, "unexpected rewrite"):
                stage1.record_live_result(self.row, "Answer [S1]", rewrite,
                    {"cache_hit": True}, wall_seconds=0.1)

    def test_unexpected_cached_rewrite_also_fails(self):
        with self.assertRaisesRegex(ValueError, "unexpected rewrite"):
            stage1.record_live_result(self.row, "Answer [S1]",
                {"invoked": False, "cache_hit": True}, {"cache_hit": True},
                wall_seconds=0.1)

    def test_normal_rewrite_not_invoked_passes(self):
        row = self.row
        result = stage1.record_live_result(row, "Answer [S1]",
            {"invoked": False, "cache_hit": False}, {"cache_hit": True},
            wall_seconds=0.1, legacy_cache=self.legacy_cache)
        self.assertGreater(result["telemetry"]["total"]["provider_tokens"], 0)
        self.assertEqual(result["telemetry"]["physical_execution"]["new_generation_calls"], 0)

    def test_generation_plan_identity_and_owner_unchanged(self):
        keys = ("case_id", "arm", "context_hash", "generation_key", "canonical_input_hash",
                "provider_call_owner", "requires_provider_call", "reuse_source",
                "generation_source", "selected_chunk_ids")
        rows = [{key: row[key] for key in keys} for row in self.plan["cases"]]
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(digest, "f50270d74d624ae18c8a3c59053a99dfd1c1942f9738c91e818d9d6b7bc1c00f")
        self.assertEqual(self.plan["totals"]["case_arm_rows"], 250)
        self.assertEqual(self.plan["totals"]["exact_reuse_rows"], 103)
        self.assertEqual(self.plan["totals"]["unique_provider_generations_expected"], 106)
        self.assertEqual(self.plan["frozen_integrity"]["artifact_hashes"], stage1.check_hashes())


if __name__ == "__main__":
    unittest.main()
