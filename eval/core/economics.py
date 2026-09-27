"""Provider usage and evidence budget; judge usage is intentionally excluded."""

from __future__ import annotations

from .schemas import PipelineResult


class EconomicsEvaluator:
    def evaluate(self, result: PipelineResult) -> dict:
        input_tokens, output_tokens = result.provider_input_tokens, result.provider_output_tokens
        return {"case_id": result.case_id, "provider_input_tokens": input_tokens,
                "provider_output_tokens": output_tokens,
                "provider_total_tokens": input_tokens + output_tokens if input_tokens is not None and output_tokens is not None else None,
                "evidence_tokens": result.evidence_tokens, "latency_seconds": result.latency_seconds,
                "estimated_cost_usd": result.estimated_cost_usd}

    def aggregate(self, rows: list[dict]) -> dict:
        measured = [row for row in rows if row["provider_total_tokens"] is not None]
        values = [row["estimated_cost_usd"] for row in rows if row["estimated_cost_usd"] is not None]
        latencies = [row["latency_seconds"] for row in rows if row["latency_seconds"] is not None]
        return {"cases": len(rows), "provider_usage_rows": len(measured),
                "provider_input_tokens": sum(row["provider_input_tokens"] for row in measured),
                "provider_output_tokens": sum(row["provider_output_tokens"] for row in measured),
                "provider_total_tokens": sum(row["provider_total_tokens"] for row in measured),
                "provider_tokens_per_query": sum(row["provider_total_tokens"] for row in measured) / len(measured) if measured else None,
                "evidence_tokens": sum(row["evidence_tokens"] or 0 for row in rows),
                "estimated_cost_usd": sum(values) if len(values) == len(rows) else None,
                "latency_mean_seconds": sum(latencies) / len(latencies) if len(latencies) == len(rows) else None,
                "latency_rows": len(latencies)}
