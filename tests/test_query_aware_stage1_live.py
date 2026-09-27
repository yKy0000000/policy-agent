"""No-network checks for the frozen Stage 1 live executor."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eval import run_query_aware_stage1 as planner
from eval import run_query_aware_stage1_live as live
from src.llm_client import LLMClientError


PRICE = {"input_per_million": 1.0, "output_per_million": 2.0}


class FakeClient:
    def __init__(self, *, metadata=None, error=None):
        self.calls = []
        self.metadata = metadata if metadata is not None else {
            "input_tokens": 1000, "output_tokens": 200,
            "request_id": "request-test", "response_id": "response-test",
            "cache_metadata": {"cached_tokens": 0}}
        self.error = error

    def complete_with_metadata(self, messages, *, max_tokens, temperature):
        self.calls.append((messages, max_tokens, temperature))
        if self.error:
            raise self.error
        return "Answer [S1]", self.metadata


class Stage1LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = planner.build_plan()
        cls.owners = [row for row in cls.plan["cases"] if row["requires_provider_call"]]
        cls.owner = cls.owners[0]
        cls.cache = planner.load(planner.ROOT / "cache/validation_v1_llm_cache.json")

    def journal_event(self, owner, status):
        event = {**live._journal_identity(owner), "status": status, "attempt": 1,
                 "retry_count": 0, "timestamp": "2026-09-27T00:00:00+00:00",
                 "live_request_hash": owner["canonical_input_hash"],
                 "price_table_sha256": live._price_hash(PRICE)}
        if status == "SUCCESS":
            event.update({"answer": "Answer [S1]", "answer_sha256": live._hash_text("Answer [S1]"),
                "citations": [],
                "validation": {"valid": True},
                "telemetry": {"provider": live.PROVIDER,
                    "model": owner["generation_model"], "input_tokens": 1000,
                    "output_tokens": 200, "latency_seconds": 0.2, "cache_hit": False,
                    "error": None, "retry_count": 0, "request_id": None,
                    "estimated_cost": 0.0014}})
        return event

    def test_check_never_constructs_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            journal_path = Path(temp) / "journal.jsonl"
            with patch.object(live, "OpenAIChatCompletionsClient",
                              side_effect=AssertionError("provider constructed")):
                _, owners, journal, info = live.audit(journal_path=journal_path)
            self.assertEqual(len(owners), 106)
            self.assertEqual(info["completed"], 0)
            self.assertEqual(info["pending"], 106)
            self.assertEqual(info["unknown"], 0)
            self.assertEqual(journal["event_count"], 0)

    def test_unique_owners_and_nonowners_never_call_provider(self):
        self.assertEqual(len(self.owners), 106)
        shared = next(row for row in self.plan["cases"] if row["generation_source"] == "new"
                      and not row["requires_provider_call"])
        reused = next(row for row in self.plan["cases"] if row["generation_source"] == "reused")
        for row in (shared, reused):
            client = FakeClient()
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaisesRegex(ValueError, "outside the frozen 106"):
                    live.execute_owner(row, self.plan, client, Path(temp) / "journal.jsonl", PRICE)
            self.assertEqual(client.calls, [])

    def test_completed_journal_is_skipped_on_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            live.append_journal(path, self.journal_event(self.owner, "ATTEMPT_STARTED"))
            live.append_journal(path, self.journal_event(self.owner, "SUCCESS"))
            state = live.read_journal(path, self.owners)
            self.assertIn(self.owner["generation_key"], state["completed"])
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "already attempted"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            self.assertEqual(client.calls, [])

    def test_journal_context_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            event = self.journal_event(self.owner, "ATTEMPT_STARTED")
            event["context_hash"] = "wrong"
            live.append_journal(path, event)
            with self.assertRaisesRegex(ValueError, "journal identity mismatch"):
                live.read_journal(path, self.owners)

    def test_source_freeze_mismatch_fails(self):
        with patch.object(planner, "sha", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "live source freeze mismatch"):
                live.validate_source_freeze()

    def test_journal_inconsistent_price_tables_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            first, second = self.owners[:2]
            for owner in (first, second):
                live.append_journal(path, self.journal_event(owner, "ATTEMPT_STARTED"))
                success = self.journal_event(owner, "SUCCESS")
                if owner is second:
                    success["price_table_sha256"] = "f" * 64
                live.append_journal(path, success)
            with self.assertRaisesRegex(ValueError, "inconsistent price tables"):
                live.read_journal(path, self.owners)

    def test_unknown_completion_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            client = FakeClient(error=TimeoutError("timeout"))
            with self.assertRaisesRegex(RuntimeError, "completion uncertain"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            state = live.read_journal(path, self.owners)
            self.assertIn(self.owner["generation_key"], state["unknown"])
            with self.assertRaisesRegex(ValueError, "already attempted"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            self.assertEqual(len(client.calls), 1)

    def test_known_failed_not_completed_has_no_automatic_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            live.append_journal(path, self.journal_event(self.owner, "ATTEMPT_STARTED"))
            live.append_journal(path, self.journal_event(self.owner, "FAILED_KNOWN_NOT_COMPLETED"))
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "already attempted"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            self.assertEqual(client.calls, [])

    def test_unexpected_rewrite_blocks_request(self):
        changed = copy.deepcopy(self.owner)
        changed["rewritten_query"] += " modified"
        with self.assertRaisesRegex(ValueError, "unexpected rewrite"):
            live.build_request(changed, self.plan)

    def test_request_identity_mismatch_blocks_before_provider_call(self):
        changed = copy.deepcopy(self.owner)
        changed["serialized_context"] += " changed"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "outside the frozen 106"):
                live.execute_owner(changed, self.plan, client, path, PRICE)
            self.assertEqual(client.calls, [])
        with self.assertRaisesRegex(ValueError, "live request identity mismatch"):
            live.build_request(changed, self.plan)

    def test_human_truth_never_enters_provider_request(self):
        request = live.build_request(self.owner, self.plan)
        messages = json.dumps(request["messages"])
        self.assertNotIn("QUERY_REQUIRED", messages)
        self.assertNotIn("frozen_human_verdicts", messages)
        self.assertEqual(request["live_request_hash"], self.owner["canonical_input_hash"])

    def test_missing_api_key_fails_before_client_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            freeze = root / live.FREEZE.relative_to(live.ROOT)
            freeze.parent.mkdir(parents=True)
            freeze.write_text("{}", encoding="utf-8")
            journal = {"completed": {}, "pending": {}, "unknown": {}, "known_failed": {}}
            with patch.object(live, "audit", return_value=(self.plan, self.owners, journal, {})), \
                 patch.object(live, "_execution_config", side_effect=LLMClientError("Missing required LLM configuration: LLM_API_KEY")):
                factory = FakeClient()
                with self.assertRaisesRegex(LLMClientError, "LLM_API_KEY"):
                    live.run_execute(root, price_path=root / "price.json", client_factory=lambda _: factory)
                self.assertEqual(factory.calls, [])

    def test_missing_provider_usage_rejects_success(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            client = FakeClient(metadata={"input_tokens": None, "output_tokens": 5})
            with self.assertRaisesRegex(RuntimeError, "completion uncertain"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            state = live.read_journal(path, self.owners)
            self.assertEqual(len(state["completed"]), 0)
            self.assertEqual(len(state["unknown"]), 1)

    def test_success_immediately_journals_answer_and_telemetry(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            client = FakeClient()
            event = live.execute_owner(self.owner, self.plan, client, path, PRICE)
            self.assertEqual(event["status"], "SUCCESS")
            self.assertEqual(event["telemetry"]["input_tokens"], 1000)
            self.assertEqual(event["telemetry"]["request_id"], "request-test")
            self.assertEqual(live.read_journal(path, self.owners)["event_count"], 2)

    def test_crash_restart_does_not_repeat_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "journal.jsonl"
            client = FakeClient(error=KeyboardInterrupt())
            with self.assertRaises(KeyboardInterrupt):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            state = live.read_journal(path, self.owners)
            self.assertEqual(len(state["unknown"]), 1)
            with self.assertRaisesRegex(ValueError, "already attempted"):
                live.execute_owner(self.owner, self.plan, client, path, PRICE)
            self.assertEqual(len(client.calls), 1)

    def test_materialization_250_rows_and_shared_answer(self):
        journal = {"completed": {row["generation_key"]: self.journal_event(row, "SUCCESS")
                                 for row in self.owners},
                   "unknown": {}, "known_failed": {}}
        result = live.materialize(self.plan, journal, PRICE)
        self.assertEqual(result["case_count"], 250)
        self.assertEqual(len(result["cases"]), 250)
        shared = next(row for row in result["cases"] if row["generation_source"] == "new"
                      and not row["requires_provider_call"])
        owner = shared["provider_call_owner"]
        owner_row = next(row for row in result["cases"] if row["case_id"] == owner["case_id"]
                         and row["arm"] == owner["arm"])
        self.assertEqual(shared["answer"], owner_row["answer"])
        self.assertGreater(result["per_arm_counterfactual_economics"]["query_router_v1"]["provider_input_tokens"], 0)
        self.assertEqual(result["experiment_physical_execution_economics"]["unique_generation_calls"], 106)
        self.assertEqual(result["experiment_physical_execution_economics"]["provider_input_tokens"], 106000)

    def test_materialization_rejects_price_table_drift(self):
        journal = {"completed": {row["generation_key"]: self.journal_event(row, "SUCCESS")
                                 for row in self.owners},
                   "unknown": {}, "known_failed": {}}
        with self.assertRaisesRegex(ValueError, "price table differs"):
            live.materialize(self.plan, journal,
                {"input_per_million": 2.0, "output_per_million": 2.0})

    def test_no_owner_beyond_106(self):
        changed = copy.deepcopy(self.owner)
        changed["generation_key"] = "extra-owner"
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "outside the frozen 106"):
                live.execute_owner(changed, self.plan, client, Path(temp) / "journal.jsonl", PRICE)
            self.assertEqual(client.calls, [])

    def test_planner_invariants_and_frozen_hashes(self):
        saved, owners = live.validate_plan()
        self.assertEqual(saved["totals"]["case_arm_rows"], 250)
        self.assertEqual(saved["totals"]["exact_reuse_rows"], 103)
        self.assertEqual(len(owners), 106)
        self.assertEqual(saved["frozen_integrity"]["artifact_hashes"], planner.check_hashes())


class Stage1ReconciliationTests(unittest.TestCase):
    """One-shot manual UNKNOWN reconciliation path."""

    @classmethod
    def setUpClass(cls):
        cls.plan = planner.build_plan()
        cls.owners = [row for row in cls.plan["cases"] if row["requires_provider_call"]]
        cls.owner = cls.owners[0]
        cls.key = cls.owner["generation_key"]

    def base(self, owner, status):
        recon = status in live.RECONCILIATION_STATUSES
        event = {**live._journal_identity(owner), "status": status,
                 "attempt": 2 if recon else 1, "retry_count": 0,
                 "timestamp": "2026-09-27T00:00:00+00:00",
                 "live_request_hash": owner["canonical_input_hash"],
                 "price_table_sha256": live._price_hash(PRICE)}
        if recon:
            event["reconciliation_reason"] = live.RECONCILIATION_REASON
        return event

    def telemetry(self, owner):
        return {"provider": live.PROVIDER, "model": owner["generation_model"],
                "input_tokens": 1000, "output_tokens": 200, "latency_seconds": 0.2,
                "cache_hit": False, "error": None, "retry_count": 0, "request_id": None,
                "estimated_cost": 0.0014}

    def unknown_events(self, owner):
        return [{**self.base(owner, "ATTEMPT_STARTED"), "provider_called": True},
                {**self.base(owner, "UNKNOWN_COMPLETION_STATE"), "provider_called": True,
                 "latency_seconds": 30.0, "error": "LLMClientError: read timed out"}]

    def recon_events(self, owner, terminal="RECONCILIATION_SUCCESS"):
        events = self.unknown_events(owner)
        events.append({**self.base(owner, "MANUAL_RECONCILIATION_AUTHORIZED"),
                       "authorized": True, "provider_called": False})
        events.append({**self.base(owner, "RECONCILIATION_ATTEMPT_STARTED"), "provider_called": True})
        if terminal == "RECONCILIATION_SUCCESS":
            events.append({**self.base(owner, "RECONCILIATION_SUCCESS"), "provider_called": True,
                           "answer": "Answer [S1]", "answer_sha256": live._hash_text("Answer [S1]"),
                           "citations": [], "validation": {"valid": True},
                           "telemetry": self.telemetry(owner)})
        else:
            events.append({**self.base(owner, terminal), "provider_called": True,
                           "latency_seconds": 30.0, "error": "LLMClientError: read timed out"})
        return events

    def owner_success_events(self, owner):
        return [{**self.base(owner, "ATTEMPT_STARTED"), "provider_called": True},
                {**self.base(owner, "SUCCESS"), "provider_called": True,
                 "answer": "Answer [S1]", "answer_sha256": live._hash_text("Answer [S1]"),
                 "citations": [], "validation": {"valid": True}, "telemetry": self.telemetry(owner)}]

    def write(self, events):
        path = Path(tempfile.mkdtemp()) / "journal.jsonl"
        for event in events:
            live.append_journal(path, event)
        return path

    def full_journal(self, terminal="RECONCILIATION_SUCCESS"):
        events = []
        for owner in self.owners:
            events.extend(self.recon_events(owner, terminal)
                          if owner["generation_key"] == self.key
                          else self.owner_success_events(owner))
        return live.read_journal(self.write(events), self.owners)

    def test_original_unknown_journal_parses(self):
        state = live.read_journal(self.write(self.unknown_events(self.owner)), self.owners)
        self.assertIn(self.key, state["unknown"])
        self.assertEqual(state["unknown"][self.key]["status"], "UNKNOWN_COMPLETION_STATE")

    def test_unknown_then_authorization_parses(self):
        events = self.unknown_events(self.owner)
        events.append({**self.base(self.owner, "MANUAL_RECONCILIATION_AUTHORIZED"),
                       "authorized": True, "provider_called": False})
        state = live.read_journal(self.write(events), self.owners)
        self.assertIn(self.key, state["unknown"])
        self.assertEqual(state["unknown"][self.key]["status"], "MANUAL_RECONCILIATION_AUTHORIZED")

    def test_authorized_reconciliation_success_parses(self):
        state = live.read_journal(self.write(self.recon_events(self.owner)), self.owners)
        self.assertIn(self.key, state["completed"])
        self.assertIn(self.key, state["reconciled"])
        self.assertEqual(state["reconciled"][self.key]["original_unknown"]["status"],
                         "UNKNOWN_COMPLETION_STATE")

    def test_reconciliation_without_authorization_rejected(self):
        events = self.unknown_events(self.owner)
        events.append({**self.base(self.owner, "RECONCILIATION_ATTEMPT_STARTED"), "provider_called": True})
        with self.assertRaisesRegex(ValueError, "without authorization"):
            live.read_journal(self.write(events), self.owners)

    def test_ordinary_success_after_unknown_rejected(self):
        events = self.unknown_events(self.owner)
        events.append({**self.base(self.owner, "SUCCESS"), "provider_called": True,
                       "answer": "A [S1]", "answer_sha256": live._hash_text("A [S1]"),
                       "citations": [], "validation": {"valid": True}, "telemetry": self.telemetry(self.owner)})
        with self.assertRaisesRegex(ValueError, "ordinary event after UNKNOWN"):
            live.read_journal(self.write(events), self.owners)

    def test_ordinary_retry_after_unknown_rejected(self):
        events = self.unknown_events(self.owner)
        events.append({**self.base(self.owner, "ATTEMPT_STARTED"), "provider_called": True})
        with self.assertRaisesRegex(ValueError, "ordinary event after UNKNOWN"):
            live.read_journal(self.write(events), self.owners)

    def test_second_reconciliation_attempt_rejected(self):
        events = self.recon_events(self.owner)
        events.append({**self.base(self.owner, "RECONCILIATION_ATTEMPT_STARTED"), "provider_called": True})
        with self.assertRaisesRegex(ValueError, "terminal generation again"):
            live.read_journal(self.write(events), self.owners)

    def test_reconciliation_identity_mismatch_rejected(self):
        events = self.recon_events(self.owner)
        events[2]["context_hash"] = "wrong"
        with self.assertRaisesRegex(ValueError, "journal identity mismatch"):
            live.read_journal(self.write(events), self.owners)

    def test_reconciliation_success_resolves_blocking_unknown(self):
        state = live.read_journal(self.write(self.recon_events(self.owner)), self.owners)
        self.assertIn(self.key, state["completed"])
        self.assertNotIn(self.key, state["unknown"])

    def test_reconciliation_unknown_remains_blocking(self):
        state = live.read_journal(
            self.write(self.recon_events(self.owner, "RECONCILIATION_UNKNOWN_COMPLETION_STATE")),
            self.owners)
        self.assertIn(self.key, state["unknown"])
        self.assertNotIn(self.key, state["completed"])

    def test_resume_skips_reconciled_generation(self):
        path = self.write(self.recon_events(self.owner))
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "already attempted"):
            live.execute_owner(self.owner, self.plan, client, path, PRICE)
        self.assertEqual(client.calls, [])

    def test_resume_blocked_after_reconciliation_unknown(self):
        path = self.write(self.recon_events(self.owner, "RECONCILIATION_UNKNOWN_COMPLETION_STATE"))
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "already attempted"):
            live.execute_owner(self.owner, self.plan, client, path, PRICE)
        self.assertEqual(client.calls, [])

    def test_materialize_accepts_reconciled_success(self):
        result = live.materialize(self.plan, self.full_journal(), PRICE)
        self.assertEqual(result["case_count"], 250)
        row = next(item for item in result["cases"]
                   if item["generation_key"] == self.key and item["requires_provider_call"])
        self.assertEqual(row["generation_source"], "manual_reconciliation_after_unknown")

    def test_materialize_rejects_unresolved_unknown(self):
        journal = self.full_journal("RECONCILIATION_UNKNOWN_COMPLETION_STATE")
        with self.assertRaisesRegex(ValueError, "incomplete or uncertain"):
            live.materialize(self.plan, journal, PRICE)

    def test_final_result_preserves_original_unknown_provenance(self):
        result = live.materialize(self.plan, self.full_journal(), PRICE)
        provenance = next(item for item in result["manual_reconciliation_events"]
                          if item["generation_key"] == self.key)
        self.assertEqual(provenance["original_attempt_status"], "UNKNOWN_COMPLETION_STATE")
        self.assertEqual(provenance["original_attempt_usage"], "unknown/unmeasured")
        self.assertFalse(provenance["original_completion_observed"])
        self.assertTrue(provenance["reconciliation_authorized_before_answer"])

    def test_per_arm_economics_uses_reconciliation_usage(self):
        result = live.materialize(self.plan, self.full_journal(), PRICE)
        cases = {(item["case_id"], item["arm"]): item for item in result["per_case_counterfactual_economics"]}
        self.assertEqual(cases[(self.owner["case_id"], self.owner["arm"])]["generation_input_tokens"], 1000)

    def test_physical_economics_preserves_unknown_usage(self):
        physical = live.materialize(self.plan, self.full_journal(), PRICE)[
            "experiment_physical_execution_economics"]
        self.assertEqual(physical["unique_generation_calls"], 106)
        self.assertEqual(physical["manual_reconciliation_attempts"], 1)
        self.assertEqual(physical["unknown_usage_provider_attempts"], 1)
        self.assertEqual(physical["total_provider_attempts"], 107)
        self.assertEqual(physical["unknown_usage_generation_keys"], [self.key])

    def test_no_second_reconciliation_provider_call(self):
        path = self.write(self.recon_events(self.owner))
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "not an eligible"):
            live.reconcile_owner(self.owner, self.plan, client, path, PRICE)
        self.assertEqual(client.calls, [])

    def test_frozen_plan_and_hashes_unchanged(self):
        saved, owners = live.validate_plan()
        self.assertEqual(saved["totals"]["case_arm_rows"], 250)
        self.assertEqual(saved["totals"]["exact_reuse_rows"], 103)
        self.assertEqual(len(owners), 106)
        self.assertEqual(saved["frozen_integrity"]["artifact_hashes"], planner.check_hashes())


if __name__ == "__main__":
    unittest.main()
