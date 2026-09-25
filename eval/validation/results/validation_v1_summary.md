# Validation V1

## Setup
- 50 untouched cases; 239 required facts.
- Strategy SHA-256: `e4863b1a0b0d27a396220d9eddc3fcef9cdada5e5e7dd41120152fa63dfdfe90`.
- Rubric SHA-256: `451a583f5ce88e0b573e61e5af073e34748b35900fa3ecd3d3f00b001699df50`.

## Frozen Strategy
Minimum Top5 reranker score ≥ 2.5 → Fixed; otherwise V1.

## Quality Gate
| Metric | V1 | Adaptive | Regret | Gate |
|---|---:|---:|---:|---|
| Answer micro | 0.912 | 0.908 | — | diagnostic |
| Grounded micro | 0.891 | 0.883 | 0.008 | PASS |
| Grounded complete | 39 | 38 | 1 | PASS |
| Unsupported + contradicted | 2 | 2 | 0 | PASS |
| Paired claim worse / better | — | 0 / 0 | — | PASS |

## Efficiency
Evidence tokens: V1 176,464; Adaptive 160,764; saving 8.9%.
Interpretation: effective but limited.

## Stopping Behavior
Fixed 11/50; V1 39/50. Safe 10; false 1; other 0.
Conservative misses are unobserved because Fixed was not generated for V1-route cases.

## Failure Diagnosis
V1: {'selection_miss': 11, 'citation_error': 14, 'grounding_review': 13, 'utilization_miss': 8, 'grounding_error': 2, 'candidate_miss': 2}. Adaptive: {'selection_miss': 12, 'citation_error': 13, 'grounding_review': 11, 'utilization_miss': 8, 'grounding_error': 2, 'candidate_miss': 2}.
False-stop clusters: {'policy_family': {'content-removal-policies': 1}, 'query_type': {'process': 1}, 'difficulty': {'moderate': 1}}.

## Verdict
PASS
