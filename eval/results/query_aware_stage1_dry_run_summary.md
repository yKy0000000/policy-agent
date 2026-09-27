# Query-aware Stage 1 0-LLM dry run

## Frozen integrity

- `eval/query_aware_stage0_config.json`: `744ed411e301aaf28a3751be99c31157b26dcbcf524673f749aa711d2a82e3a6`
- `eval/query_aware_router_v1.json`: `dcc7d4953f3ba9794c35f2168e29f419bbb40eb014775cf8ccb5e0e7ae913bd7`
- `eval/query_aware_arms_v1.json`: `18d7adbfd1ac8a1802dbf29d2c222fb988d0c495ca4f979c24297a406f0112c9`
- `eval/results/frozen_human_verdicts_v1.json`: `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716`
- `eval/results/a0_bge_rerank_orders.json`: `fb15b316c4b5170514e6f1c5140689ba0e77869dd516b7c7e170593c4db5b2e2`
- `eval/results/stage0_replay_results.json`: `5e7d665bdae13803dd00d39756881f55e5a6792eb01ca37d0e2f63a4e1563703`
- Model: `deepseek-v4-flash`; prompt: `grounded-policy-answer-v1` (`5f7018961248fe4d4d53fba8e15c409cb6de42260bf3acc05e7279c2d8e0b603`).
- Stage 0 input/source hashes checked: 36.

## Generation plan

| Arm | Cases | Exact reuse | New required | Cross-arm shared |
|---|---:|---:|---:|---:|
| fixed_top5 | 50 | 50 | 0 | 33 |
| adaptive_prefix_v1 | 50 | 5 | 45 | 37 |
| coverage_selector_v2 | 50 | 25 | 25 | 25 |
| no_router_adaptive_v1 | 50 | 0 | 50 | 14 |
| query_router_v1 | 50 | 23 | 27 | 50 |

Unique provider generations expected: **106**.
Reused result references: **103**.

## Rewrite plan

Frozen Validation V1 is single-turn and its replay has no rewrite. Cached: 0; missing: 0; expected live rewrite calls: 0. The result adapter rejects any unexpected rewrite before recording a generation.

## Provenance validation

Missing/invalid: 0; context collisions: 0; generation-key collisions: 0; selected-context mismatches: 0; frozen-policy mismatches: 0.

## Per-arm counterfactual provider usage (known at dry run)

Cached historical usage is attributed to every arm-case that consumes it. New generation usage awaits live owner telemetry; full per-arm totals and cost are unavailable until then.

| Arm | Known cached rows | Known input tokens | Known output tokens | New rows awaiting usage |
|---|---:|---:|---:|---:|
| fixed_top5 | 50 | 110674 | 15982 | 0 |
| adaptive_prefix_v1 | 5 | 11624 | 1557 | 45 |
| coverage_selector_v2 | 25 | 54357 | 7137 | 25 |
| no_router_adaptive_v1 | 0 | 0 | 0 | 50 |
| query_router_v1 | 23 | 49371 | 7839 | 27 |

## Experiment physical execution plan

Unique new generation calls expected: 106; live rewrite calls expected: 0. Shared results count once in physical spend; no calls were made in this dry run.
No live latency or monetary cost was measured.

The frozen Stage 1 key does not include serialized context, rewritten query, or all generation settings. The plan retains the frozen key and records these fields plus a canonical input hash for exact validation. The older `cache/generated_answers.json` lacks this full provenance and is excluded from reuse.

## Blocking issues

READY FOR FINAL RE-AUDIT
