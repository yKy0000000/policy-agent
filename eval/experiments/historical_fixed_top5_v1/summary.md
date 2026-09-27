# bge_fixed_top5 on validation_v1

Execution: `frozen_replay`. Benchmark source hashes are recorded in `config.json`.

## Retrieval — original rubric facts

- Candidate availability: **235/239**; candidate-complete cases: **49/50**.
- Ranked Top5: **224/239**.

## Context — QUERY_REQUIRED aspects

- Required evidence covered: **193/208**.
- Context-complete cases: **46/50**.
- Selected evidence tokens: **91,699**.

## Answer — QUERY_REQUIRED aspects

- Status: **complete**; judged cases: **50/50**.
- Required answer aspects covered: **196 / 208**.
- QueryRequiredComplete: **43 / 50**.
- Candidate complete regressions vs fixed: **0**; confirmed: **0**. `None` means not adjudicated.

## Economics — pipeline provider usage

- Measured provider rows: **50/50**.
- Provider tokens/query: **2533.12**.
- Evidence tokens: **91,699**.
- Live latency rows: **0/50**. Reused historical answers have no comparable live latency.

The three layers use different denominators and must not be combined into one accuracy score. See the JSON files for per-case details and provenance.
