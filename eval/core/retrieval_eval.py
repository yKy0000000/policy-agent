"""Original-rubric retrieval metrics. Denominator is 239, not Human Truth 208."""

from __future__ import annotations

from .benchmark import BenchmarkCase
from .schemas import PipelineResult


class RetrievalEvaluator:
    def evaluate(self, case: BenchmarkCase, result: PipelineResult) -> dict:
        candidates = {item.chunk_id for item in result.retrieval_candidates}
        ranks = {item.chunk_id: index for index, item in enumerate(result.ranked_candidates, 1)}
        rows = []
        for fact in case.original_rubric_facts:
            rank = min((ranks[cid] for cid in fact.supporting_chunk_ids if cid in ranks), default=None)
            rows.append({"fact_id": fact.fact_id, "candidate_available": bool(candidates.intersection(fact.supporting_chunk_ids)),
                         "best_rank": rank, "top5": rank is not None and rank <= 5})
        return {"case_id": case.case_id, "denominator": "original_rubric_facts", "total": len(rows),
                "candidate_available": sum(row["candidate_available"] for row in rows),
                "ranked_top5": sum(row["top5"] for row in rows),
                "candidate_complete": all(row["candidate_available"] for row in rows), "facts": rows}

    def aggregate(self, rows: list[dict]) -> dict:
        total = sum(row["total"] for row in rows)
        available = sum(row["candidate_available"] for row in rows)
        top5 = sum(row["ranked_top5"] for row in rows)
        return {"denominator": "original_rubric_facts", "cases": len(rows), "facts": total,
                "candidate_available": available, "candidate_recall": available / total,
                "candidate_complete_cases": sum(row["candidate_complete"] for row in rows),
                "ranked_top5": top5, "ranked_top5_recall": top5 / total}
