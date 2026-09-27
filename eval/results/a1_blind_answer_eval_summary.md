# Blind A1 answer evaluation (Validation V1)

**Blind:** the judge saw only anonymized answer labels; no arm, policy, route, evidence/cost telemetry, or generation source was exposed. Judge = frozen `broad-v3-answer-quality-v1` over frozen `QUERY_REQUIRED` aspects.

## Dataset

- 50 Validation V1 cases; 250 arm-case rows.
- Required aspects: 50 cases, 208 QUERY_REQUIRED aspects.
- Unique answers actually evaluated (identical/shared generations deduplicated): **156**; judged: 156, judge errors: 0.

## Required-aspect evaluation (unique answers)

- aspect judgments: 654
- covered: 628; missing: 26; incorrect: 0; uncertain(PARTIAL): 0

## Candidate quality by arm (after unblinding)

| Arm | covered | missing | incorrect | uncertain | QueryRequiredComplete cases | judge-error cases |
|---|---:|---:|---:|---:|---:|---:|
| fixed_top5 | 197 | 11 | 0 | 0 | 44/50 | 0 |
| adaptive_prefix_v1 | 201 | 7 | 0 | 0 | 45/50 | 0 |
| coverage_selector_v2 | 197 | 11 | 0 | 0 | 45/50 | 0 |
| no_router_adaptive_v1 | 202 | 6 | 0 | 0 | 46/50 | 0 |
| query_router_v1 | 197 | 11 | 0 | 0 | 45/50 | 0 |

## Pairwise vs fixed_top5 (candidate regressions/improvements)

| Arm | required gained | required lost | complete improved | complete regressed | complete same |
|---|---:|---:|---:|---:|---:|
| adaptive_prefix_v1 | 7 | 3 | 3 | 2 | 45 |
| coverage_selector_v2 | 1 | 1 | 1 | 0 | 49 |
| no_router_adaptive_v1 | 8 | 3 | 4 | 2 | 44 |
| query_router_v1 | 2 | 2 | 2 | 1 | 47 |

## Grounding / citation diagnostics by arm

| Arm | supported claims | partial | unsupported | contradicted | uncertain | unsupported citations | missing citations |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed_top5 | 516 | 1 | 0 | 0 | 9 | 1 | 10 |
| adaptive_prefix_v1 | 556 | 2 | 1 | 0 | 15 | 1 | 18 |
| coverage_selector_v2 | 528 | 2 | 0 | 0 | 13 | 1 | 15 |
| no_router_adaptive_v1 | 616 | 1 | 0 | 1 | 10 | 0 | 15 |
| query_router_v1 | 541 | 1 | 0 | 0 | 11 | 2 | 13 |

## Review queue

- total items: 8
- by priority: {1: 6, 3: 2}
- by kind: {'complete_regression_vs_fixed_top5': 5, 'contradicted_claim': 1, 'selector_vs_router': 2}
- selector-vs-router dispute cases: 2

## Blind integrity

- Evaluator input contained only: anonymized case label, original query, answer text, cited evidence, and frozen QUERY_REQUIRED aspects.
- Not exposed: arm identity, policy, route, evidence/context token counts, cost, latency, generation source.
- Label->arm mapping stored only in `a1_blind_answer_mapping_v1.json`.

No economics, no Pareto, no keep/kill decision.
