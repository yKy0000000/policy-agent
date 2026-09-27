"""Independent answer evaluation over frozen QUERY_REQUIRED aspects.

FrozenAnswerJudge replays adjudicated A1 judgments. LiveAnswerJudge reuses the
existing judge prompt/schema for future pipelines and keeps its cache separate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from .benchmark import BenchmarkCase, PROJECT_ROOT
from .schemas import PipelineResult


def _read(path: str) -> dict:
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


class AnswerJudge(Protocol):
    def judge(self, case: BenchmarkCase, result: PipelineResult) -> dict[str, Any]: ...

    def confirmed_regressions(self, pipeline_id: str) -> int | None: ...


class FrozenAnswerJudge:
    """Replay final blind quality by generation identity, without judging again."""

    def __init__(self, arm: str):
        self.arm = arm
        self.mapping = _read("eval/results/a1_blind_answer_mapping_v1.json")["cases"]
        self.quality = {row["case_id"]: row for row in _read("eval/results/a1_blind_answer_quality_frozen_v1.json")["cases"]}
        table = _read("eval/results/a1_blind_answer_quality_arm_table_v1.json")["table"]
        self.arm_row = next(row for row in table if row["arm"] == arm)

    def judge(self, case: BenchmarkCase, result: PipelineResult) -> dict[str, Any]:
        if result.component_provenance.get("execution") != "frozen_replay":
            raise ValueError("frozen verdict cannot be applied to a non-frozen generation")
        identity = result.component_provenance["generation_identity"]
        labels = [label for label, owner in self.mapping[case.case_id].items()
                  if self.arm in owner["arms"] and owner["generation_identity"] == identity]
        if len(labels) != 1:
            raise ValueError(f"frozen answer identity mismatch: {case.case_id}/{self.arm}")
        return self.quality[case.case_id]["answers"][labels[0]]

    def confirmed_regressions(self, pipeline_id: str) -> int | None:
        return self.arm_row["confirmed_regressions_vs_fixed"]

    def confirmed_grounding_issues(self, pipeline_id: str) -> int | None:
        return self.arm_row["correctness_grounding_issues"]


def frozen_fixed_baseline_complete() -> dict[str, bool]:
    from .historical import FrozenReplayPipeline
    from .benchmark import load_benchmark

    benchmark = load_benchmark()
    pipeline = FrozenReplayPipeline("bge_fixed_top5", "fixed_top5")
    judge = FrozenAnswerJudge("fixed_top5")
    return {case.case_id: bool(judge.judge(case, pipeline.run(case))["query_required_complete"]) for case in benchmark.cases}


class LiveAnswerJudge:
    """Existing answer judge protocol with an independent, content-bound cache."""

    def __init__(self, cache_path: Path, env_file: Path | None = None):
        from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

        self.config = LLMConfig.from_env(env_file or PROJECT_ROOT / ".env")
        self.client = OpenAIChatCompletionsClient(self.config)
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    def judge(self, case: BenchmarkCase, result: PipelineResult) -> dict[str, Any]:
        from src.generator import assign_evidence_sources
        from eval.run_answer_eval import V3_JUDGE_MAX_TOKENS, V3_JUDGE_VERSION, _judge_messages, _parse_judge

        if result.answer is None or any(not evidence.text for evidence in result.selected_evidence):
            raise ValueError("live judging requires an answer and full selected evidence text")
        judge_case = {"case_id": case.case_id, "query": case.query, "facts": list(case.required_statements())}
        sources = assign_evidence_sources(result.selected_evidence)
        owner = {"generation": {"answer": result.answer}, "sources": sources}
        messages = _judge_messages(judge_case, {"A": owner})
        key_input = {"case_id": case.case_id, "messages": messages, "model": self.config.model,
                     "judge_version": V3_JUDGE_VERSION, "max_tokens": V3_JUDGE_MAX_TOKENS}
        key = hashlib.sha256(json.dumps(key_input, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        if key not in self.cache:
            raw, usage = self.client.complete_with_usage(messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
            parsed = _parse_judge(raw, {"A"}, set(case.query_required_aspects))["A"]
            self.cache[key] = {"judgment": parsed, "usage": usage}
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.cache_path.with_suffix(".tmp")
            temp.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp.replace(self.cache_path)
        parsed = self.cache[key]["judgment"]
        return {"aspects": {fact["fact_id"]: {"judge_status": fact["status"],
                                           "citation_status": fact["citation_status"], "note": fact.get("note", "")}
                            for fact in parsed["facts"]},
                "claim_counts": {status: sum(claim["support_status"] == status for claim in parsed["claims"])
                                 for status in {claim["support_status"] for claim in parsed["claims"]}},
                "claim_citation_counts": {status: sum(claim["citation_status"] == status for claim in parsed["claims"])
                                          for status in {claim["citation_status"] for claim in parsed["claims"]}},
                "query_required_complete": all(fact["status"] == "covered" for fact in parsed["facts"]),
                "judge_error": None}

    def confirmed_regressions(self, pipeline_id: str) -> int | None:
        return None  # requires targeted human review

    def confirmed_grounding_issues(self, pipeline_id: str) -> int | None:
        return None


class AnswerEvaluator:
    def __init__(self, judge: AnswerJudge, baseline_complete: dict[str, bool] | None = None):
        self.judge_backend = judge
        self.baseline_complete = baseline_complete or {}

    def evaluate(self, case: BenchmarkCase, result: PipelineResult) -> dict:
        if result.status != "complete" or result.answer is None:
            return {"case_id": case.case_id, "denominator": "QUERY_REQUIRED", "status": "unavailable",
                    "required_total": len(case.query_required_aspects), "required_covered": None,
                    "query_required_complete": None, "error": "pipeline result has no valid answer"}
        try:
            judged = self.judge_backend.judge(case, result)
            if judged.get("judge_error"):
                raise ValueError(str(judged["judge_error"]))
            aspects = judged["aspects"]
            if set(aspects) != set(case.query_required_aspects):
                raise ValueError(f"judge aspect IDs differ: {case.case_id}")
            covered = [fid for fid in case.query_required_aspects if aspects[fid]["judge_status"] == "covered"]
            incorrect = [fid for fid in case.query_required_aspects if aspects[fid]["judge_status"] == "incorrect"]
            uncertain = [fid for fid in case.query_required_aspects if aspects[fid]["judge_status"] == "uncertain"]
            missing = [fid for fid in case.query_required_aspects if aspects[fid]["judge_status"] == "missing"]
            complete = len(covered) == len(case.query_required_aspects)
            if bool(judged["query_required_complete"]) != complete:
                raise ValueError(f"frozen completeness mismatch: {case.case_id}")
            return {"case_id": case.case_id, "denominator": "QUERY_REQUIRED", "status": "judged",
                    "required_total": len(case.query_required_aspects), "required_covered": len(covered),
                    "covered_ids": covered, "missing_ids": missing, "incorrect_ids": incorrect, "uncertain_ids": uncertain,
                    "query_required_complete": complete, "claim_counts": judged.get("claim_counts", {}),
                    "claim_citation_counts": judged.get("claim_citation_counts", {})}
        except Exception as error:
            return {"case_id": case.case_id, "denominator": "QUERY_REQUIRED", "status": "judge_error",
                    "required_total": len(case.query_required_aspects), "required_covered": None,
                    "query_required_complete": None, "error": str(error)}

    def aggregate(self, rows: list[dict], pipeline_id: str) -> dict:
        judged = [row for row in rows if row["status"] == "judged"]
        required = sum(row["required_total"] for row in rows)
        covered = sum(row["required_covered"] for row in judged)
        complete = sum(row["query_required_complete"] for row in judged)
        candidates = sum(self.baseline_complete.get(row["case_id"], False) and not row["query_required_complete"] for row in judged)
        grounding = getattr(self.judge_backend, "confirmed_grounding_issues", lambda _: None)(pipeline_id)
        return {"denominator": "QUERY_REQUIRED", "cases": len(rows), "required_aspects": required,
                "judged_cases": len(judged), "required_covered": covered if len(judged) == len(rows) else None,
                "required_missing": required - covered if len(judged) == len(rows) else None,
                "query_required_complete_cases": complete if len(judged) == len(rows) else None,
                "candidate_complete_regressions_vs_fixed": candidates if self.baseline_complete else None,
                "confirmed_complete_regressions_vs_fixed": self.judge_backend.confirmed_regressions(pipeline_id),
                "confirmed_correctness_grounding_issues": grounding,
                "status": "complete" if len(judged) == len(rows) else "partial"}
