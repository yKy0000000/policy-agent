"""One experiment runner for frozen replay and future live component pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .answer_eval import AnswerEvaluator
from .benchmark import Benchmark
from .context_eval import ContextEvaluator
from .economics import EconomicsEvaluator
from .retrieval_eval import RetrievalEvaluator
from .schemas import PipelineResult


class RunnablePipeline(Protocol):
    pipeline_id: str

    def run(self, case) -> PipelineResult: ...


@dataclass(slots=True)
class ExperimentReport:
    config: dict[str, Any]
    pipeline_results: list[PipelineResult]
    retrieval: dict[str, Any]
    context: dict[str, Any]
    answer: dict[str, Any]
    economics: dict[str, Any]

    def save(self, directory: Path) -> None:
        if directory.exists() and any(directory.iterdir()):
            raise FileExistsError(f"experiment directory is not empty: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        documents = {
            "config.json": self.config,
            "pipeline_results.json": [row.to_dict() for row in self.pipeline_results],
            "retrieval_metrics.json": self.retrieval,
            "context_metrics.json": self.context,
            "answer_metrics.json": self.answer,
            "economics.json": self.economics,
        }
        for name, body in documents.items():
            (directory / name).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        from .reporting import render_summary

        (directory / "summary.md").write_text(render_summary(self), encoding="utf-8")


class ExperimentRunner:
    def __init__(self, benchmark: Benchmark, pipeline: RunnablePipeline,
                 answer_evaluator: AnswerEvaluator | None = None):
        self.benchmark = benchmark
        self.pipeline = pipeline
        self.answer_evaluator = answer_evaluator
        self.retrieval_evaluator = RetrievalEvaluator()
        self.context_evaluator = ContextEvaluator()
        self.economics_evaluator = EconomicsEvaluator()

    def run(self, config: dict[str, Any]) -> ExperimentReport:
        results = [self.pipeline.run(case) for case in self.benchmark.cases]
        if any(result.case_id != case.case_id or result.pipeline_id != self.pipeline.pipeline_id
               for case, result in zip(self.benchmark.cases, results)):
            raise ValueError("pipeline identity drift")
        retrieval_rows = [self.retrieval_evaluator.evaluate(case, result) for case, result in zip(self.benchmark.cases, results)]
        context_rows = [self.context_evaluator.evaluate(case, result) for case, result in zip(self.benchmark.cases, results)]
        economics_rows = [self.economics_evaluator.evaluate(result) for result in results]
        if self.answer_evaluator:
            answer_rows = [self.answer_evaluator.evaluate(case, result) for case, result in zip(self.benchmark.cases, results)]
            answer = {"summary": self.answer_evaluator.aggregate(answer_rows, self.pipeline.pipeline_id), "cases": answer_rows}
        else:
            answer = {"summary": {"status": "not_evaluated", "denominator": "QUERY_REQUIRED"}, "cases": []}
        return ExperimentReport(
            config={**config, "benchmark_name": self.benchmark.name, "benchmark_version": self.benchmark.version,
                    "benchmark_source_hashes": self.benchmark.source_hashes},
            pipeline_results=results,
            retrieval={"summary": self.retrieval_evaluator.aggregate(retrieval_rows), "cases": retrieval_rows},
            context={"summary": self.context_evaluator.aggregate(context_rows), "cases": context_rows},
            answer=answer,
            economics={"summary": self.economics_evaluator.aggregate(economics_rows), "cases": economics_rows},
        )
