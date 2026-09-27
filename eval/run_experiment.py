"""Common benchmark + pipeline-config entry point.

Offline replay is read-only with respect to frozen sources and makes no model
calls. Live generation and live judging require explicit flags.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from eval.core.answer_eval import AnswerEvaluator, FrozenAnswerJudge, LiveAnswerJudge, frozen_fixed_baseline_complete
from eval.core.benchmark import PROJECT_ROOT, load_benchmark
from eval.core.historical import FrozenReplayPipeline
from eval.core.runner import ExperimentRunner


PIPELINES = PROJECT_ROOT / "eval" / "pipelines"
EXPERIMENTS = PROJECT_ROOT / "eval" / "experiments"


def load_pipeline_config(name: str) -> dict:
    if not name or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in name):
        raise ValueError("pipeline name must be a simple ID")
    config = json.loads((PIPELINES / f"{name}.json").read_text(encoding="utf-8"))
    if config["pipeline_id"] != name:
        raise ValueError("pipeline ID does not match config filename")
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the canonical policy benchmark through one pipeline")
    parser.add_argument("--benchmark", default="validation_v1")
    parser.add_argument("--pipeline", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="replay frozen historical rows without model calls")
    mode.add_argument("--generate", action="store_true", help="run live components and generation")
    parser.add_argument("--evaluate", action="store_true", help="run answer evaluation; live mode may call a judge")
    parser.add_argument("--report", action="store_true", help="print the Markdown summary")
    parser.add_argument("--experiment-id", help="output directory name under eval/experiments")
    args = parser.parse_args(argv)

    config = load_pipeline_config(args.pipeline)
    benchmark = load_benchmark(args.benchmark)
    if args.offline:
        if not config.get("historical_arm"):
            parser.error("this pipeline config has no frozen historical arm")
        pipeline = FrozenReplayPipeline(args.pipeline, config["historical_arm"])
        judge = FrozenAnswerJudge(config["historical_arm"]) if args.evaluate else None
        execution = "frozen_replay"
    else:
        from eval.core.product_components import build_live_pipeline

        pipeline = build_live_pipeline(config)
        judge = LiveAnswerJudge(EXPERIMENTS / "judge_cache.json") if args.evaluate else None
        execution = "live"
    baseline = frozen_fixed_baseline_complete() if args.evaluate else None
    runner = ExperimentRunner(benchmark, pipeline, AnswerEvaluator(judge, baseline) if judge else None)
    report = runner.run({**config, "execution": execution})
    identifier = args.experiment_id or f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{args.pipeline}_{execution}"
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in identifier):
        parser.error("experiment ID must be a simple directory name")
    output = EXPERIMENTS / identifier
    report.save(output)
    if args.report:
        print((output / "summary.md").read_text(encoding="utf-8"))
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
