# Adaptive Evidence Strategy Signal Study

## Development Set

- 16 frozen Broad Query V3 cases, 92 facts; prior four cases excluded because their rubric and three-strategy answer results do not align.
- All labels and thresholds were developed on these cases; no validation or generalization claim.

## Fixed Sufficiency

- fixed_sufficient 11; escalation_needed 4; ambiguous 1.
- Candidate ceilings V3-03/V3-11 require retrieval escalation, not a larger evidence K. V3-01 is a candidate-depth/deep-ranking failure.

## Signals

- Minimum Top5 reranker score: sufficient median 1.67 (range -7.74–3.76); escalation median 1.07 (range -1.87–2.07). A high threshold is a conservative stop signal, not a general difficulty predictor.
- Top1-to-Top5 score gap: sufficient 2.56 (range 1.13–6.55); escalation 1.15 (range 0.78–2.71).
- Top5 distinct documents: sufficient 2.00 (range 1.00–5.00); escalation 3.00 (range 1.00–4.00).
- Tail document gain, lexical/semantic overlap and query multi-part markers overlap strongly between groups; they remain exploratory only.

## Candidate Strategy

```text
Run the existing retrieval and reranker.
If every Top5 reranker score is at least 2.5: use Fixed Top5.
Otherwise: use existing V1 adaptive prefix.
Do not route to V2 yet; there is insufficient evidence for a second-stage rule.
```

## Dev Results

- Fixed stops 4/16; V1 escalations 12/16.
- Candidate grounded macro/micro 0.889/0.902 vs V1 0.889/0.902; grounded complete 10/16 vs 10/16.
- Answer macro/micro 0.889/0.902; grounded and factual regret vs V1 0/0 facts.
- Evidence tokens 42,773 vs V1 50,530; saving 7,757 (15.4%).
- Candidate/selection/utilization/synthesis failure counts are unchanged from V1 on this development set.

## Known Failure Modes

- Candidate ceilings: V3-03/V3-11. Candidate depth: V3-01. Answer utilization: V3-07/V3-08. None is fixed by this stop rule.
- V3-04 is a Fixed stop with an unsupported meta-claim shared by V1; zero regret against V1 does not mean the answer is risk-free.
- The stop threshold uses reranker score scale and may fail under calibration shift. Frozen evidence mappings contain documented direct-support gaps.

## Next Step

- Candidate config is frozen for untouched validation only. Build 50–60 new broad queries across policy scopes, then evaluate grounded quality regret before token savings.
