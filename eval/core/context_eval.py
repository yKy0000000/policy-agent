"""Context support metrics over frozen QUERY_REQUIRED aspects only."""

from __future__ import annotations

from .benchmark import BenchmarkCase
from .schemas import PipelineResult


class ContextEvaluator:
    def evaluate(self, case: BenchmarkCase, result: PipelineResult) -> dict:
        selected = {item.chunk_id for item in result.selected_evidence}
        covered = [aspect_id for aspect_id in case.query_required_aspects if selected.intersection(case.supporting_chunks(aspect_id))]
        missing = [aspect_id for aspect_id in case.query_required_aspects if aspect_id not in covered]
        return {"case_id": case.case_id, "denominator": "QUERY_REQUIRED", "required_total": len(case.query_required_aspects),
                "required_covered": len(covered), "covered_ids": covered, "missing_ids": missing,
                "context_complete": not missing, "evidence_tokens": result.evidence_tokens}

    def aggregate(self, rows: list[dict]) -> dict:
        total = sum(row["required_total"] for row in rows)
        covered = sum(row["required_covered"] for row in rows)
        tokens = [row["evidence_tokens"] for row in rows]
        return {"denominator": "QUERY_REQUIRED", "cases": len(rows), "required_aspects": total,
                "required_covered": covered, "required_missing": total - covered,
                "required_coverage": covered / total, "context_complete_cases": sum(row["context_complete"] for row in rows),
                "evidence_tokens": sum(value for value in tokens if value is not None),
                "evidence_token_rows": sum(value is not None for value in tokens)}
