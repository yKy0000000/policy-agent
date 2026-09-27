# Economics Contract v1 — Query-Aware Retrieval

**Status: FROZEN before Stage 1.** All Stage 1 comparisons use these accounting definitions. Not a single
number may be redefined after seeing results; any change requires a new version and a full replay.

## 1. What is counted per query

| Component | Unit | Authoritative source | Role |
|---|---|---|---|
| rewrite calls | calls | live pipeline (`trace.remote_llm_calls` before generation) | cost |
| decomposition calls | calls | Stage 2 only (analyzer); counted even when rejected | cost |
| retrieval count | searches | local lexical + semantic retrievals executed | informational |
| rerank workload | candidate pairs, seconds | local BGE calls | informational/latency |
| evidence tokens | approx tokens of selected chunks | `eval.analyze_evidence_geometry.approx_tokens` | diagnostic (not cost) |
| serialized context tokens | tokens of the exact serialized Sources/context block | local reranker tokenizer estimate | diagnostic |
| provider input tokens | tokens | provider `usage.prompt_tokens` | **authoritative cost basis** |
| provider output tokens | tokens | provider `usage.completion_tokens` | **authoritative cost basis** |
| cache hits / misses | calls | cache key lookups | informational |
| latency | seconds | live per-stage timers | p50 / p95 gate |
| cost | money | provider token counts × external price table | reported, price table supplied at run time |

Rules:

- evidence tokens must never be reported alone; always alongside provider input tokens and total context
  size.
- judge calls are analysis-only and are excluded from user-facing cost, but their tokens are reported.
- frozen artifacts (transfer/utilization) contain provider usage for every answer; per-call latency is not
  in those artifacts and must be instrumented live in Stage 1.
- Stage 1 uses the frozen single-turn queries; rewrite calls are 0 in replay and must be added explicitly if
  the live pipeline applies rewrite.

## 2. Aggregation

For each arm: per-query values, then mean / median / p90 / p95 for tokens and latency, plus totals.
Quality–cost comparison uses the **Pareto frontier** over (human-confirmed query-required answer quality,
total tokens per query); a component is kept only if it produces a non-dominated point.

## 3. Preregistered decision rules

**Material benefit** (per component compared with its simplest competitor): on the changed-context subset,
human review confirms at least one gained query-required aspect with zero lost query-required aspects and no
new unsupported/contradicted claim or citation failure; and the arm is not dominated on tokens/latency.

**Material regression**: any confirmed lost query-required aspect, any new unsupported or contradicted
claim, any invalid citation, or a confirmed answer-quality regression on sentinel cases.

**Complexity deletion**: if the simpler competitor ties on confirmed quality (no material benefit) at equal or
lower total tokens (±10% band), the more complex component is deleted. Deletion does not delete results;
negative results are documented.

**Latency gate**: Stage 1 reports p50/p95; escalation to the next stage requires p95 not materially worse
than the simpler arm (threshold fixed in the Stage 1 preregistration before calls).

## 4. Mandatory reporting table

| Arm | cases | quality (human query-required) | evidence tokens | provider in/out | total tokens/query | calls | rerank pairs | latency p50/p95 | cost |
|---|---|---|---|---|---|---|---|---|---|

Every Stage 1 result artifact must contain this table; no composite score replaces it.
