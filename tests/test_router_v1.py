from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.decomposer_v1 import DecomposerClient, normalize_subquery_text, validate_subqueries
from src.router_v1 import (
    DECOMPOSE,
    DIRECT,
    UNRECOGNIZED_REASON,
    RouterClient,
    parse_router_response,
)
from src.router_v1_identity import (
    canonical_json_sha256,
    decomposer_prompt_identity,
    load_contract,
    router_prompt_identity,
    verify_contract_identity,
)
from src.router_v1_prompts import (
    DECOMPOSER_SCHEMA,
    DECOMPOSER_SYSTEM,
    DECOMPOSER_USER_TEMPLATE,
    ROUTER_SCHEMA,
    ROUTER_SYSTEM,
    ROUTER_USER_TEMPLATE,
)


class ScriptedChatClient:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = []

    def complete(self, messages, *, max_tokens=96, temperature=0.0):
        self.calls.append((messages, max_tokens, temperature))
        if self.error is not None:
            raise self.error
        return self.output


class RouterParsingTests(unittest.TestCase):
    def test_valid_direct(self) -> None:
        decision = RouterClient(ScriptedChatClient('{"decision": "DIRECT"}'), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertFalse(decision.fallback)
        self.assertEqual(decision.effective_reason_code, UNRECOGNIZED_REASON)
        self.assertEqual(decision.reason_validity, "missing")

    def test_valid_decompose_with_reason(self) -> None:
        raw = '{"decision": "DECOMPOSE", "reason_code": "COVERAGE_SPLIT_RISK"}'
        decision = RouterClient(ScriptedChatClient(raw), request_model="m").decide("q")
        self.assertEqual(decision.decision, DECOMPOSE)
        self.assertEqual(decision.effective_reason_code, "COVERAGE_SPLIT_RISK")
        self.assertEqual(decision.reason_validity, "valid")
        self.assertFalse(decision.fallback)

    def test_unknown_reason_keeps_legal_decision(self) -> None:
        raw = '{"decision": "DIRECT", "reason_code": "MADE_UP"}'
        decision = RouterClient(ScriptedChatClient(raw), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertEqual(decision.raw_reason_code, "MADE_UP")
        self.assertEqual(decision.effective_reason_code, UNRECOGNIZED_REASON)
        self.assertEqual(decision.reason_validity, "unknown")
        self.assertFalse(decision.fallback)

    def test_inconsistent_reason_keeps_legal_decision(self) -> None:
        raw = '{"decision": "DIRECT", "reason_code": "COVERAGE_SPLIT_RISK"}'
        decision = RouterClient(ScriptedChatClient(raw), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertEqual(decision.reason_validity, "inconsistent_with_decision")
        self.assertEqual(decision.effective_reason_code, UNRECOGNIZED_REASON)
        self.assertFalse(decision.fallback)

    def test_extra_fields_are_recorded_not_fatal(self) -> None:
        raw = '{"decision": "DECOMPOSE", "reason_code": "COVERAGE_SPLIT_RISK", "confidence": 0.9}'
        decision = RouterClient(ScriptedChatClient(raw), request_model="m").decide("q")
        self.assertEqual(decision.decision, DECOMPOSE)
        self.assertEqual(decision.schema_anomalies, ("confidence",))
        self.assertFalse(decision.fallback)

    def test_invalid_decision_falls_back_to_direct(self) -> None:
        raw = '{"decision": "MAYBE"}'
        decision = RouterClient(ScriptedChatClient(raw), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertTrue(decision.fallback)
        self.assertIn("invalid_decision", decision.failure or "")

    def test_missing_decision_falls_back_to_direct(self) -> None:
        decision = RouterClient(ScriptedChatClient('{"reason_code": "COVERAGE_SPLIT_RISK"}'), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertTrue(decision.fallback)
        self.assertEqual(decision.failure, "missing_decision")

    def test_malformed_json_falls_back_to_direct(self) -> None:
        decision = RouterClient(ScriptedChatClient("not json at all"), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertTrue(decision.fallback)
        self.assertIn("malformed_json", decision.failure or "")
        self.assertEqual(decision.raw_response, "not json at all")

    def test_api_failure_falls_back_to_direct(self) -> None:
        decision = RouterClient(ScriptedChatClient(error=RuntimeError("connection reset")), request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertTrue(decision.fallback)
        self.assertIn("router_call_failed", decision.failure or "")
        self.assertIn("connection reset", decision.failure or "")

    def test_timeout_falls_back_to_direct_without_retry(self) -> None:
        client = ScriptedChatClient(error=TimeoutError("timed out"))
        decision = RouterClient(client, request_model="m").decide("q")
        self.assertEqual(decision.decision, DIRECT)
        self.assertTrue(decision.fallback)
        self.assertEqual(len(client.calls), 1)

    def test_parse_rejects_non_object_json(self) -> None:
        decision, failure = parse_router_response("[1, 2, 3]")
        self.assertIsNone(decision)
        self.assertEqual(failure, "response_is_not_a_json_object")

    def test_blank_query_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RouterClient(ScriptedChatClient('{"decision": "DIRECT"}'), request_model="m").decide("  ")


class DecomposerValidationTests(unittest.TestCase):
    def _decompose(self, payload, base="base query"):
        client = ScriptedChatClient(json.dumps(payload))
        return DecomposerClient(client, request_model="m").decompose(base)

    def test_valid_two(self) -> None:
        outcome = self._decompose({"subqueries": ["first target", "second target"]})
        self.assertTrue(outcome.available)
        self.assertEqual(outcome.subqueries, ("first target", "second target"))
        self.assertEqual(outcome.removed, ())

    def test_valid_three(self) -> None:
        outcome = self._decompose({"subqueries": ["one", "two", "three"]})
        self.assertTrue(outcome.available)
        self.assertEqual(len(outcome.subqueries), 3)

    def test_duplicate_subquery_removed(self) -> None:
        outcome = self._decompose({"subqueries": ["same target", "same target"]})
        self.assertFalse(outcome.available)
        self.assertEqual(outcome.fallback_reason, "insufficient_distinct_subqueries")
        self.assertEqual([item.reason for item in outcome.removed], ["duplicate_subquery"])

    def test_duplicate_of_base_removed(self) -> None:
        outcome = self._decompose({"subqueries": ["Base Query", "new target"]}, base="base query")
        self.assertFalse(outcome.available)
        self.assertEqual(outcome.removed[0].reason, "duplicate_of_base")

    def test_unicode_and_punctuation_normalization_dedup(self) -> None:
        outcome = self._decompose({"subqueries": ["Hello World?", "ｈｅｌｌｏ   ｗｏｒｌｄ！"]})
        self.assertFalse(outcome.available)
        self.assertEqual(outcome.removed[0].reason, "duplicate_subquery")

    def test_one_valid_after_cleaning_is_unavailable(self) -> None:
        outcome = self._decompose({"subqueries": ["kept", "kept?", "   "]})
        self.assertFalse(outcome.available)
        self.assertEqual(outcome.subqueries, ())
        self.assertEqual({item.reason for item in outcome.removed}, {"duplicate_subquery", "blank_after_trim"})

    def test_malformed_json_is_unavailable(self) -> None:
        client = ScriptedChatClient("{broken")
        outcome = DecomposerClient(client, request_model="m").decompose("q")
        self.assertTrue(outcome.called)
        self.assertFalse(outcome.available)
        self.assertIn("malformed_json", outcome.failure or "")
        self.assertEqual(outcome.fallback_reason, "decomposer_failure")

    def test_api_failure_is_unavailable(self) -> None:
        client = ScriptedChatClient(error=RuntimeError("timeout"))
        outcome = DecomposerClient(client, request_model="m").decompose("q")
        self.assertFalse(outcome.available)
        self.assertIn("decomposer_call_failed", outcome.failure or "")

    def test_schema_failures(self) -> None:
        self.assertFalse(self._decompose({"subqueries": ["only one"]}).available)
        self.assertFalse(self._decompose({"subqueries": ["a", "b", "c", "d"]}).available)
        self.assertFalse(self._decompose({"subqueries": [1, 2]}).available)
        self.assertFalse(self._decompose({"subqueries": ["a", ""]}).available)
        self.assertFalse(self._decompose({"subqueries": ["a", "b"], "extra": 1}).available)
        self.assertFalse(self._decompose({"other": []}).available)

    def test_normalize_preserves_original_for_retrieval(self) -> None:
        outcome = self._decompose({"subqueries": ["  Keep Me? ", "other target"]})
        self.assertEqual(outcome.subqueries[0], "Keep Me?")
        self.assertEqual(normalize_subquery_text("  Keep Me? "), "keep me")

    def test_validate_subqueries_is_pure(self) -> None:
        retained, removed, failure = validate_subqueries(["a", "b"], "base")
        self.assertEqual(retained, ("a", "b"))
        self.assertEqual(removed, ())
        self.assertIsNone(failure)


class IdentityTests(unittest.TestCase):
    def test_runtime_hashes_match_frozen_contract(self) -> None:
        contract = load_contract()
        self.assertEqual(
            router_prompt_identity()["prompt_sha256"], contract["router"]["prompt_sha256"]
        )
        self.assertEqual(
            router_prompt_identity()["schema_sha256"], contract["router"]["schema_sha256"]
        )
        self.assertEqual(
            decomposer_prompt_identity()["prompt_sha256"], contract["decomposer"]["prompt_sha256"]
        )
        self.assertEqual(
            decomposer_prompt_identity()["schema_sha256"], contract["decomposer"]["schema_sha256"]
        )

    def test_verify_contract_identity_passes(self) -> None:
        identity = verify_contract_identity()
        self.assertEqual(identity.requested_model_id, "deepseek-v4-flash")
        self.assertEqual(identity.provider_host, "api.deepseek.com")
        self.assertTrue(len(identity.contract_sha256) == 64)

    def test_canonical_hashing_convention(self) -> None:
        expected = canonical_json_sha256(
            {"system": ROUTER_SYSTEM, "user_template": ROUTER_USER_TEMPLATE}
        )
        self.assertEqual(expected, load_contract()["router"]["prompt_sha256"])
        self.assertEqual(canonical_json_sha256(ROUTER_SCHEMA), load_contract()["router"]["schema_sha256"])
        self.assertEqual(
            canonical_json_sha256({"system": DECOMPOSER_SYSTEM, "user_template": DECOMPOSER_USER_TEMPLATE}),
            load_contract()["decomposer"]["prompt_sha256"],
        )
        self.assertEqual(
            canonical_json_sha256(DECOMPOSER_SCHEMA), load_contract()["decomposer"]["schema_sha256"]
        )

    def test_tampered_contract_is_rejected(self) -> None:
        contract = load_contract()
        contract["router"]["prompt_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaises(Exception):
                verify_contract_identity(path)


class RunnerGuardTests(unittest.TestCase):
    def test_frozen_benchmark_is_refused_by_default(self) -> None:
        from eval.run_router_v1 import FROZEN_BENCHMARK_PATH, BlindnessGuardError, load_query_cases

        with self.assertRaises(BlindnessGuardError):
            load_query_cases(FROZEN_BENCHMARK_PATH)

    def test_synthetic_case_file_loads(self) -> None:
        from eval.run_router_v1 import load_query_cases, resolve_arm_selection

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(
                json.dumps([{"case_id": "s1", "query": "Does the neutral rule apply?"}]),
                encoding="utf-8",
            )
            cases = load_query_cases(path)
        self.assertEqual(cases[0]["case_id"], "s1")
        self.assertEqual(resolve_arm_selection("ROUTED"), ("ROUTED",))
        self.assertEqual(len(resolve_arm_selection("ALL")), 3)


if __name__ == "__main__":
    unittest.main()
