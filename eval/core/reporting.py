"""Compact human-readable experiment summary with explicit metric scopes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner import ExperimentReport


def render_summary(report: "ExperimentReport") -> str:
    r = report.retrieval["summary"]
    c = report.context["summary"]
    a = report.answer["summary"]
    e = report.economics["summary"]
    return f"""# {report.config['pipeline_id']} on {report.config['benchmark_name']}

Execution: `{report.config.get('execution', 'unknown')}`. Benchmark source hashes are recorded in `config.json`.

## Retrieval — original rubric facts

- Candidate availability: **{r['candidate_available']}/{r['facts']}**; candidate-complete cases: **{r['candidate_complete_cases']}/{r['cases']}**.
- Ranked Top5: **{r['ranked_top5']}/{r['facts']}**.

## Context — QUERY_REQUIRED aspects

- Required evidence covered: **{c['required_covered']}/{c['required_aspects']}**.
- Context-complete cases: **{c['context_complete_cases']}/{c['cases']}**.
- Selected evidence tokens: **{c['evidence_tokens']:,}**.

## Answer — QUERY_REQUIRED aspects

- Status: **{a['status']}**; judged cases: **{a.get('judged_cases', 0)}/{r['cases']}**.
- Required answer aspects covered: **{a.get('required_covered')} / {a.get('required_aspects')}**.
- QueryRequiredComplete: **{a.get('query_required_complete_cases')} / {r['cases']}**.
- Candidate complete regressions vs fixed: **{a.get('candidate_complete_regressions_vs_fixed')}**; confirmed: **{a.get('confirmed_complete_regressions_vs_fixed')}**. `None` means not adjudicated.

## Economics — pipeline provider usage

- Measured provider rows: **{e['provider_usage_rows']}/{e['cases']}**.
- Provider tokens/query: **{e['provider_tokens_per_query']}**.
- Evidence tokens: **{e['evidence_tokens']:,}**.
- Live latency rows: **{e['latency_rows']}/{e['cases']}**. Reused historical answers have no comparable live latency.

The three layers use different denominators and must not be combined into one accuracy score. See the JSON files for per-case details and provenance.
"""
