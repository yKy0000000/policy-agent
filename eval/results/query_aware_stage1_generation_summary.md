# Query-aware Stage 1 generation

Rows: 250.

## Experiment physical execution

Unique new generation calls (observable completions): 106.
Total provider attempts (incl. unknown completions): 107.
Unknown-usage provider attempts: 1.
Usage measurement status: measured spend from observable completions plus 1 original attempt(s) with unknown usage.
Provider tokens: 491727 input / 39157 output.
Estimated cost from the supplied price table: 0.09725325.

## Per-arm counterfactual economics

Each arm is charged for the generation it consumes, including shared and historical results. These totals are not this experiment's physical spend.

| Arm | Cases | Provider input | Provider output | Cost/query | Reused rows |
|---|---:|---:|---:|---:|---:|
| fixed_top5 | 50 | 110674 | 15982 | 0.00052381 | 50 |
| adaptive_prefix_v1 | 50 | 203042 | 17846 | 0.00082328 | 5 |
| coverage_selector_v2 | 50 | 147045 | 17008 | 0.00064523 | 25 |
| no_router_adaptive_v1 | 50 | 290565 | 18879 | 0.00109824 | 0 |
| query_router_v1 | 50 | 166760 | 16627 | 0.00069980 | 23 |

## Manual reconciliation events

One or more generations were resolved by an explicitly authorized manual reconciliation retry after an unobservable UNKNOWN. The original UNKNOWN attempt is preserved in the journal with unknown/unmeasured usage.
- `9c33e81f12de3057f4a023110f5eb8cfd4c6c59e79f3378daf88e917c3221e7f`: original=UNKNOWN_COMPLETION_STATE (unknown/unmeasured); reconciliation usage={'input_tokens': 5127, 'output_tokens': 310, 'estimated_cost': 0.0009550499999999999}.

Per-case provenance and citation validation are in the JSON artifact. No answer-quality evaluation was run.
