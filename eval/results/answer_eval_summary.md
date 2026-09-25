# Answer Quality Evaluation

## Dataset

- 16 Broad Query V3 cases; 92 frozen required facts.
- Fixed / V1 / V2 answers use one production generator prompt and temperature 0.
- Raw model judgments are retained; 11 fact and 8 claim discrepancies received targeted source review.

## Answer Quality

| Strategy | Answer macro/micro | Grounded macro/micro | Complete/grounded | Utilization/grounded | Unsupported | Contradicted |
|---|---:|---:|---:|---:|---:|---:|
| Fixed | 0.800/0.804 | 0.800/0.804 | 7/7 of 16 | 0.971/0.974 | 2 | 0 |
| V1 | 0.889/0.902 | 0.889/0.902 | 10/10 of 16 | 0.965/0.965 | 1 | 0 |
| V2 | 0.881/0.891 | 0.881/0.891 | 9/9 of 16 | 0.975/0.976 | 1 | 0 |

## Source Review

- Mapping discrepancies: 10 direct-support mapping gaps and 1 judge false positive; frozen rubric unchanged.
- Claim citation issues: 4 unsupported, 2 missing citations, 2 partial support.
- Direct mapping gaps are a provenance risk for the frozen evidence coverage baseline; reviewed selected chunks are used only in answer evaluation.

## Citation / Grounding

| Strategy | Supported claims | Valid citation IDs | Supported fact citations |
|---|---:|---:|---:|
| Fixed | 0.988 | 16/16 | 74 |
| V1 | 0.979 | 16/16 | 83 |
| V2 | 0.989 | 16/16 | 82 |

All citation IDs resolve to supplied evidence. Source review classified 3/3/2 claim citation issues for Fixed/V1/V2, respectively; factual correctness and citation support remain separate judgments.

## Evidence → Answer Patterns

Cases with A/B/C/D/E: **4/4/12/3/2**. A: evidence and answer coverage rise; B: evidence rises without answer gain; C: equal evidence and answer quality at higher token cost; D: answer quality falls; E: available required evidence is omitted from an answer.

## Pipeline Failure Breakdown

- Fixed: candidate 3, selection 13, utilization 2, synthesis 0, unresolved 0 missing-fact labels.
- V1: candidate 3, selection 3, utilization 3, synthesis 0, unresolved 0 missing-fact labels.
- V2: candidate 3, selection 5, utilization 2, synthesis 0, unresolved 0 missing-fact labels.

## Answer Oracle

- Offline quality-first oracle: answer macro/micro 0.889/0.902; grounded macro/micro 0.889/0.902; complete/grounded 10/10 of 16.
- Unique wins {'fixed_top5': 7, 'adaptive_prefix_v1': 1, 'coverage_selector_v2': 4}; exact ties 4. Evidence tokens 34,712; difference vs V1 -15,818.

## Key Findings

- V1 has the highest answer coverage and completeness; V2 is close, while Fixed is lower. The answer oracle matches V1's coverage and completeness at lower evidence cost, using hindsight labels.
- Evidence gains improve answer coverage in 4 cases but leave it unchanged in 4; V3-07 and V3-08 contain required evidence omitted from answers.
- Three cases show lower adjudicated claim quality with more evidence, without losing required answer facts; evidence overload is unconfirmed.
- 10 covered strategy-fact judgments lack a frozen mapping; review found direct support in selected chunks for all of them.
- V3-01 deep-ranking case: Fixed 1/4, V1 2/4, V2 2/4; none is complete.
- Candidate-ceiling cases: V3-03 (Fixed 7/9, V1 7/9, V2 7/9); V3-11 (Fixed 3/4, V1 3/4, V2 3/4).

## Efficiency

- 48 strategy answers required 42 unique generation inputs; 6 answers reused; 16 grouped judge results.

## Limitations

- This 16-case diagnostic set is not an untouched validation set.
- Most semantic labels depend on judge model `deepseek-v4-flash`; targeted source review is not independent human sign-off.
- Claim segmentation and entailment are semantic judgments, not deterministic validator guarantees.
- The frozen evidence mapping and baseline retain the documented gap risk.
