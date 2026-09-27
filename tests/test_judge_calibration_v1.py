"""Integrity checks for the frozen blind calibration inputs."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from eval.core.benchmark import load_benchmark
from eval.run_judge_calibration_analysis import build
from eval.run_judge_calibration_v1 import (
    codex_executable,
    judge_batch_prompt,
    judge_prompt,
    prepare,
    sample_case_ids,
)


class JudgeCalibrationV1Tests(unittest.TestCase):
    def test_case_sample_is_deterministic_and_verdict_independent(self) -> None:
        ids = [case.case_id for case in load_benchmark().cases]
        chosen = sample_case_ids(ids)
        self.assertEqual(len(chosen), 15)
        self.assertEqual(chosen, sample_case_ids(list(reversed(ids))))
        self.assertEqual(chosen[0], "VAL-001-005")
        self.assertEqual(chosen[-1], "VAL-001-049")

    def test_packet_is_blinded_and_complete(self) -> None:
        sample, inputs, packet = prepare()
        self.assertEqual(sample["sampled_judgments"], 60)
        self.assertEqual(len(inputs["items"]), 60)
        self.assertEqual(packet.count("verdict:** PENDING"), 60)
        for secret in ("judge_status", "fixed_top5", "MiniLM", "BGE", "historical score"):
            self.assertNotIn(secret, packet)

    def test_codex_executable_prefers_path_then_fallback(self) -> None:
        existing = str(Path(__file__))
        with mock.patch("eval.run_judge_calibration_v1.shutil.which", return_value=existing):
            self.assertEqual(codex_executable(), existing)
        with mock.patch("eval.run_judge_calibration_v1.shutil.which", return_value=None), \
                mock.patch("eval.run_judge_calibration_v1.CODEX_FALLBACK", Path(existing)):
            self.assertEqual(codex_executable(), existing)
        with mock.patch("eval.run_judge_calibration_v1.shutil.which", return_value=None), \
                mock.patch("eval.run_judge_calibration_v1.CODEX_FALLBACK", Path("Z:/missing/codex.exe")):
            with self.assertRaises(FileNotFoundError):
                codex_executable()

    def test_calibration_analysis_is_deterministic_and_aligned(self) -> None:
        summary, disagreements = build()
        summary_again, _ = build()
        self.assertEqual(summary, summary_again)
        self.assertEqual(summary["verdict_totals"]["human"], {"COVERED": 55, "MISSING": 5})
        for pair in ("historical_vs_human", "sol_vs_human", "historical_vs_sol"):
            self.assertEqual(summary[pair]["comparable"], 60, pair)
        self.assertEqual(summary["historical_vs_human"]["false_positives"], 2)
        self.assertEqual(summary["historical_vs_human"]["false_negatives"], 0)
        self.assertEqual(len(disagreements["human_missing_boundary"]), 5)

    def test_cross_family_prompt_excludes_sample_metadata(self) -> None:
        _, inputs, _ = prepare()
        prompt = judge_prompt(inputs["items"][0])
        self.assertIn("candidate_answer", prompt)
        self.assertIn("required_aspect", prompt)
        self.assertNotIn("fixed_top5", prompt)
        self.assertNotIn("review_id", prompt)
        self.assertNotIn("judge_status", prompt)
        batch_prompt = judge_batch_prompt(inputs["items"][:20])
        self.assertNotIn("review_id", batch_prompt)
        self.assertNotIn("fixed_top5", batch_prompt)
        self.assertIn("exactly one entry per input item", batch_prompt)


if __name__ == "__main__":
    unittest.main()
