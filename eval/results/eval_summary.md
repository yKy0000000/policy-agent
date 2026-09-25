# Evaluation Summary

## Dataset

- 16 human-adjudicated Broad Query V3 diagnostic queries: `eval/broad_queries_v3_adjudicated.json`.
- 92 frozen required atomic facts: `eval/broad_query_v3_atomic_facts_frozen_candidate.json`.
- Fixed, V1, and V2 selections reuse the saved Top20 retrieval snapshot. Run `python -m eval.run_evidence_eval --check` to verify the machine-readable result in `eval/results/evidence_eval.json`.

## Evidence Evaluation

| Strategy | Macro | Micro | Complete | Tokens | Avg K | Post-completion tokens |
|---|---:|---:|---:|---:|---:|---:|
| Fixed Top5 | 0.749 | 0.750 | 7/16 | 27,274 | 5.00 | 6,653 (24.4%) |
| Adaptive V1 | 0.930 | 0.935 | 12/16 | 50,530 | 10.25 | 19,013 (37.6%) |
| Coverage V2 | 0.873 | 0.880 | 10/16 | 41,134 | 7.88 | 13,371 (32.5%) |
| Oracle | 0.930 | 0.935 | 12/16 | 40,073 | 8.25 | — |

## Candidate Recall

Candidate pool covers 89/92 required facts (96.7%) and is fact-complete for 14/16 cases. V3-03 and V3-11 have candidate ceilings. V3-01 has required evidence in the pool beyond Top20.

## Key Findings

- Broad-query failures have distinct candidate, ranking, and selection causes.
- V1 gives the highest evidence coverage among the three tested strategies.
- The oracle matches V1 coverage using 10,457 fewer evidence tokens (20.7%). Unique wins: Fixed 5, V1 4, V2 3; four cases have exact ties.
- Answer-quality validation against the frozen facts remains pending.

## Limitations

- The oracle uses gold labels unavailable during inference. It is an offline upper bound, not a deployable router.
- Fact coverage measures evidence availability, not answer correctness or citation support.
- This is a 16-case diagnostic set, not a population estimate.
