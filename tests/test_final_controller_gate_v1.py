"""Offline integrity checks for the terminal gate; no API, cache, or result writes."""

from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

from eval import run_final_controller_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "eval/reports/final_controller_gate_v1"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FinalControllerArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = load(REPORT / "gate1_sensor_results.json")
        cls.manifest = load(REPORT / "gate_manifest_v1.json")
        cls.eligibility = load(REPORT / "sample_eligibility.json")
        cls.decision = load(REPORT / "decision.json")
        cls.adjudication = load(REPORT / "gate1_adjudication.json")
        cls.economics = load(REPORT / "economics_summary.json")
        cls.frozen = gate.FrozenData()

    def test_original_archive_bytes_and_input_identities(self):
        archive = load(REPORT / "archive_checksums.json")
        self.assertEqual(len(archive["files"]), 13)
        for relative, expected in archive["files"].items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)
        for relative, expected in self.eligibility["frozen_inputs"].items():
            with self.subTest(input=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)
        self.assertEqual(
            hashlib.sha256((REPORT / "sample_eligibility.json").read_bytes()).hexdigest(),
            self.manifest["sample"]["eligibility_sha256"],
        )
        for name, expected in self.decision["frozen_inputs_hashes"].items():
            actual = (self.results["sensor_system_sha256"] if name == "sensor_system_prompt_sha256"
                      else hashlib.sha256((REPORT / name).read_bytes()).hexdigest())
            self.assertTrue(actual.startswith(expected), name)

    def test_frozen_prompt_and_settings(self):
        sensor = self.manifest["sensor"]
        digest = hashlib.sha256(gate.SENSOR_SYSTEM.encode("utf-8")).hexdigest()
        self.assertEqual(digest, sensor["system_prompt_sha256"])
        self.assertEqual(digest, self.results["sensor_system_sha256"])
        self.assertEqual(gate.SENSOR_MODEL, sensor["model"])
        self.assertEqual(gate.REPLICATES, sensor["replicates"])
        self.assertEqual(gate.TEMPERATURE, sensor["temperature"])
        self.assertEqual(gate.MAX_TOKENS, sensor["max_tokens"])

    def test_runtime_message_does_not_receive_hidden_truth(self):
        scenario = {
            "query": "visible question", "evidence_text": "visible source", "draft": "visible draft",
            "target_fact_ids": "HIDDEN_FACT_SENTINEL", "expected_action": "HIDDEN_ACTION_SENTINEL",
            "human_diagnosis": "HIDDEN_REVIEW_SENTINEL", "truth": "HIDDEN_TRUTH_SENTINEL",
        }
        messages = gate.sensor_messages(scenario)
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertEqual(messages[0]["content"], gate.SENSOR_SYSTEM)
        text = messages[1]["content"]
        for visible in (scenario["query"], scenario["evidence_text"], scenario["draft"]):
            self.assertIn(visible, text)
        for hidden in ("HIDDEN_FACT_SENTINEL", "HIDDEN_ACTION_SENTINEL",
                       "HIDDEN_REVIEW_SENTINEL", "HIDDEN_TRUTH_SENTINEL"):
            self.assertNotIn(hidden, text)

    def test_primary_eligibility_and_judge_disagreements_remain_separate(self):
        cases = {case["case_id"]: case for case in self.eligibility["cases"]}
        self.assertEqual(self.eligibility, gate.build_eligibility())
        for case in cases.values():
            if case["role"] in ("patch_positive", "refresh_positive"):
                self.assertTrue(case["draft_omits"])
                self.assertEqual(case["support_in_context"], case["role"] == "patch_positive")
                self.assertTrue(all(row["final"] == "QUERY_REQUIRED" for row in case["truth"]))
                self.assertTrue(all(row["label"] == "NOT_COVERED"
                                    for row in case["a1_fixed_top5_labels"].values()))
        for cid in ("VAL-001-009", "VAL-001-022"):
            self.assertEqual(cases[cid]["role"], "patch_judge_disagreement")
            self.assertFalse(cases[cid]["draft_omits"])
            self.assertTrue(all(row["label"] == "COVERED"
                                for row in cases[cid]["a1_fixed_top5_labels"].values()))
        self.assertEqual(self.frozen.verdicts["VAL-001-039-F02"]["final"], "RELEVANT_BUT_OPTIONAL")
        self.assertEqual(self.frozen.verdicts["VAL-001-050-F01"]["final"], "QUERY_REQUIRED")

    def test_executed_cells_exclude_recorded_secondary_case(self):
        cells = self.results["cells"]
        executed = {case["case_id"] for case in self.eligibility["cases"]
                    if case["role"] != "secondary_refresh"}
        self.assertEqual(len(cells), 24)
        self.assertEqual(len({cell["cell_id"] for cell in cells}), 24)
        self.assertEqual({cell["case_id"] for cell in cells}, executed)
        self.assertNotIn("VAL-001-001", executed)
        self.assertEqual(self.eligibility["replicate_calls"], 26)
        for cid in executed:
            self.assertEqual({c["replicate"] for c in cells if c["case_id"] == cid}, {1, 2})
        self.assertEqual(self.results["failures"], [])
        self.assertEqual(Counter(c["parsed"]["action"] for c in cells),
                         {"RETURN_DRAFT": 23, "REFRESH_CONTEXT": 1})
        actions = {case["case_id"]: case["sensor_actions"]
                   for case in self.adjudication["cases"]}
        for cid in executed:
            ordered = sorted((c for c in cells if c["case_id"] == cid), key=lambda c: c["replicate"])
            self.assertEqual([c["parsed"]["action"] for c in ordered], actions[cid])

    def test_archived_responses_replay_without_api_or_local_cache(self):
        cache = Mock()
        cache.get.side_effect = {c["cache_key"]: c for c in self.results["cells"]}.get
        cache.set.side_effect = AssertionError("archive check must not write cache")
        client = Mock()
        client.complete_with_usage.side_effect = AssertionError("archive check must not call provider")
        failures = []
        for cell in self.results["cells"]:
            with self.subTest(cell=cell["cell_id"]):
                scenario = self.frozen.scenario(cell["case_id"])
                self.assertEqual(gate.parse_sensor(cell["raw"]), cell["parsed"])
                self.assertEqual(gate.deterministic_check(cell["parsed"], scenario), cell["deterministic"])
                replay = gate.execute_sensor(cell, scenario, cache, client, failures, check_only=True)
                self.assertEqual(replay, cell)
        client.complete_with_usage.assert_not_called()
        cache.set.assert_not_called()
        self.assertEqual(failures, [])

    def test_economics_agrees_with_recorded_usage_and_empirical_quantiles(self):
        cells = self.results["cells"]
        sensor = self.economics["sensor"]
        incoming = sum(c["provider_usage"]["input_tokens"] for c in cells)
        outgoing = sum(c["provider_usage"]["output_tokens"] for c in cells)
        self.assertEqual(incoming, sensor["provider_input_tokens_total"])
        self.assertEqual(outgoing, sensor["provider_output_tokens_total"])
        self.assertEqual(incoming + outgoing, sensor["provider_total_tokens"])
        self.assertEqual(round((incoming + outgoing) / len(cells), 1),
                         sensor["provider_total_tokens_per_request"])
        times = sorted(c["latency_seconds"] for c in cells)
        for probability, key in ((0.5, "latency_p50_seconds"), (0.95, "latency_p95_seconds")):
            self.assertEqual(round(times[min(len(times) - 1, int(len(times) * probability))], 3), sensor[key])
        self.assertEqual(round(sum(times) / len(times), 3), sensor["latency_mean_seconds"])
        estimate = self.economics["cost_estimate"]
        self.assertAlmostEqual(estimate["sensor_cost_per_request_usd_est"],
                               (incoming + outgoing) / len(cells) * estimate["blended_rate_usd_per_token"],
                               places=8)

    def test_terminal_decision_has_no_action_or_production_migration(self):
        self.assertEqual(self.decision["decision"], "STOP")
        self.assertFalse(self.decision["implemented"])
        self.assertFalse(self.decision["production_default_changed"])
        self.assertEqual(self.economics["actions"]["executed_actions"], 0)
        for branch in ("patch", "refresh"):
            verdict = self.adjudication["branch_verdicts"][branch]
            self.assertEqual(verdict["verdict"], "FAIL")
            self.assertEqual(verdict["stable_hits"], 0)
        self.assertEqual(self.adjudication["branch_verdicts"]["controls"]["harmful_false_positives"], 0)
        self.assertEqual(self.adjudication["branch_verdicts"]["optional_pressure"]["upgrades_to_required"], 0)
        for pattern in ("gate2_*results.json", "e2e_*"):
            self.assertEqual(list(REPORT.glob(pattern)), [])


if __name__ == "__main__":
    unittest.main()
