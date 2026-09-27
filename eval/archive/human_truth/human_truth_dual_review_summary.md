# Human truth dual-review summary (pre-final)

This is a dual **model-agent** initial review of the 331 frozen aspects. It is not a human gold freeze. Reviewer 1 and Reviewer 2 each read the contract and the same blinded query/statement packet; their initial labels were recorded independently. The DeepSeek advisory artifact was opened only after both reviews were complete and contributes priority flags only.

## Integrity and scope

- 331/331 aspect IDs present, unique, and in worksheet order in both reviews; every label is in the contract vocabulary and has a reason.
- Source worksheet remains `pending_human_verdicts`, with `verdict`, `reviewer_1`, `reviewer_2`, and `final` null throughout. No frozen Stage 0 artifact was edited.
- The blinded packet contains only `case_id`, `aspect_id`, original `query`, and frozen `statement`. Neither reviewer had route, source, evidence, assistant suggestions, model answers, or experiment metrics in the packet.
- Reviewers applied the contract omission test to all 331 aspects. The worksheet contains 66 distinct query cases and no separate multi-turn context field.

## Agreement

- Exact agreement: **314/331 = 94.86%**; disagreements: **17**.
- Reviewer 1: QUERY_REQUIRED 300 / RELEVANT_BUT_OPTIONAL 31 / AMBIGUOUS 0.
- Reviewer 2: QUERY_REQUIRED 299 / RELEVANT_BUT_OPTIONAL 32 / AMBIGUOUS 0.
- Agreement candidate distribution: QUERY_REQUIRED 291 / RELEVANT_BUT_OPTIONAL 23 / AMBIGUOUS 0.
- Disagreement types (order independent): QUERY_REQUIRED / RELEVANT_BUT_OPTIONAL: 17.

## Cross-distribution

### SIMPLE / BROAD route

| Segment | Total | Agree | Disagree |
|---|---:|---:|---:|
| BROAD | 192 | 183 | 9 |
| SIMPLE | 139 | 131 | 8 |

### SIMPLE sentinels

| Segment | Total | Agree | Disagree |
|---|---:|---:|---:|
| non_sentinel | 290 | 274 | 16 |
| sentinel | 41 | 40 | 1 |

### Aspect source set

| Segment | Total | Agree | Disagree |
|---|---:|---:|---:|
| validation_v1_rubric | 239 | 227 | 12 |
| broad_v3_rubric | 92 | 87 | 5 |

### Assistant priority metadata (overlapping groups)

| Segment | Total | Agree | Disagree |
|---|---:|---:|---:|
| no_assistant_priority | 292 | 283 | 9 |
| any_assistant_priority | 39 | 31 | 8 |
| assistant_broad_boundary | 30 | 23 | 7 |
| assistant_contamination_risk | 15 | 13 | 2 |
| assistant_ambiguity | 2 | 2 | 0 |

Priority metadata definitions: `assistant_ambiguity` = DeepSeek marked AMBIGUOUS or LOW confidence; `assistant_contamination_risk` = related-fact drift or rubric contamination attention flag; `assistant_broad_boundary` = BROAD aspect with a non-HIGH confidence or non-REQUIRED suggestion. These markers were attached after the two reviews and are not verdict evidence.

## Minimum final-adjudication list

Every row below needs an explicit final decision; none was silently merged. The disagreement packet contains both independent reasons and the original query/statement for each ID.

| Aspect ID | Reviewer 1 | Reviewer 2 | Route | Sentinel | Priority flags |
|---|---|---|---|---|---|
| VAL-001-003-F04 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| VAL-001-007-F02 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |
| VAL-001-007-F03 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |
| VAL-001-022-F05 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_contamination_risk, assistant_broad_boundary |
| VAL-001-031-F04 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | SIMPLE | no | — |
| VAL-001-032-F01 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | SIMPLE | yes | assistant_contamination_risk |
| VAL-001-036-F03 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | BROAD | no | — |
| VAL-001-040-F04 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| VAL-001-040-F05 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| VAL-001-044-F01 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |
| VAL-001-048-F04 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |
| VAL-001-048-F05 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |
| V3-02-F04 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| V3-03-F04 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| V3-03-F07 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | SIMPLE | no | — |
| V3-05-F04 | RELEVANT_BUT_OPTIONAL | QUERY_REQUIRED | BROAD | no | — |
| V3-14-F06 | QUERY_REQUIRED | RELEVANT_BUT_OPTIONAL | BROAD | no | assistant_broad_boundary |

The agreement candidates remain provisional. Final gold, `frozen_human_verdicts` status, and a final hash require a later, explicitly authorized adjudication step. No A1/A2/A3 was started.
