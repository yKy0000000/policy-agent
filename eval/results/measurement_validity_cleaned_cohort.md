# Measurement Validity Cleaned Cohort (frozen)

> Human-review writeback and cleaned nominal cohort for Measurement Validity Audit V2. Human verdicts are added as a fourth layer; no model artifact is modified. Only the pre-registered 20-item subset was human reviewed: the 10 nominal problematic facts and 10 of the 40 covered-side facts. Model adjudication evidence (V2 40/40 covered PRESENT) is not human-confirmed ground truth.

- status: frozen
- validate stage: COMPLETE
- frozen at: 2026-09-26

## Human-review writeback (three layers preserved)

| fact | side | type/stratum | original judge | V2 model | human |
|---|---|---|---|---|---|
| VAL-001-008-F02 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | AMBIGUOUS |
| VAL-001-009-F01 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-009-F02 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-011-F01 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-022-F02 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-026-F02 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-037-F01 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-039-F02 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | ABSENT_OR_INCORRECT |
| VAL-001-050-F01 | nominal | omission | missing / not_applicable | SEMANTICALLY_PRESENT | ABSENT_OR_INCORRECT |
| VAL-001-050-F05 | nominal | incorrect_synthesis | incorrect / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-009-F03 | covered | stratum A | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-008-F03 | covered | stratum A | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-008-F01 | covered | stratum A | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-022-F03 | covered | stratum A | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-011-F03 | covered | stratum A | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-004-F02 | covered | stratum B | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-007-F03 | covered | stratum B | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-024-F03 | covered | stratum B | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-042-F05 | covered | stratum B | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |
| VAL-001-017-F03 | covered | stratum B | covered / supported | SEMANTICALLY_PRESENT | SEMANTICALLY_PRESENT |

## Human vs V2 model agreement

- subset size: 20
- V2 model labels: {'SEMANTICALLY_PRESENT': 20, 'ABSENT_OR_INCORRECT': 0, 'AMBIGUOUS': 0}
- human labels: {'SEMANTICALLY_PRESENT': 17, 'ABSENT_OR_INCORRECT': 2, 'AMBIGUOUS': 1}
- exact agreement: 17/20 = 85%
- disagreement: 3/20 = 15%

### Disagreement detail

- `VAL-001-008-F02` (V2 SEMANTICALLY_PRESENT → human AMBIGUOUS; attributed to evaluation_case_representation, mechanism: non_atomic_anchor_target_ambiguity): The baseline answer covers email as a submission channel and that plain-text email is usually faster than a PDF attachment or physical mail, but it does not explicitly cover the requirement that an attachment also be accompanied by a plain-text version in the email body. The review packet does not state whether the atomic target is 'email is an allowed submission channel', 'an attachment requires a plain-text copy in the body', or both, so no reliable binary human verdict is possible. This is a target-ambiguity / non-atomic-anchor problem, not a model error, and the item is excluded from the repair cohort.

- `VAL-001-039-F02` (V2 SEMANTICALLY_PRESENT → human ABSENT_OR_INCORRECT; attributed to v2_adjudicator, mechanism: anchor_drift_false_present): The anchor requires that GitHub makes an offer to provide source code where component licenses require such an offer. The baseline answer discusses Open Source Notices and when an open-source license overrides the Application Terms, but never states the source-code offer. The V2 model found topically related content in the full Top5 evidence without aligning it to the atomic fact (topical relevance is not proposition equivalence).

- `VAL-001-050-F01` (V2 SEMANTICALLY_PRESENT → human ABSENT_OR_INCORRECT; attributed to v2_adjudicator, mechanism: over_lenient_semantic_match_incomplete_proposition_coverage): The anchor requires that, before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend cure/reinstatement provisions. The baseline answer explains the cure/reinstatement mechanism and reinstatement conditions, but not the pre-filing commitment or its timing. The V2 model treated the related reinstatement content as covering the commitment as well.

## Layer summary (10 nominal problematic facts)

- original judge (deepseek-v4-flash): missing 9, incorrect 1, covered 0
- V1 adjudicator (deepseek-v4-pro): ['SEMANTICALLY_PRESENT=7', 'ABSENT_OR_INCORRECT=3', 'AMBIGUOUS=0']
- V2 adjudicator (deepseek-v4-pro): ['SEMANTICALLY_PRESENT=10', 'ABSENT_OR_INCORRECT=0', 'AMBIGUOUS=0']
- human review: {'SEMANTICALLY_PRESENT': 7, 'ABSENT_OR_INCORRECT': 2, 'AMBIGUOUS': 1}

## Cleaned nominal cohort

- nominal problematic facts: 10
- confirmed errors: 2 (['VAL-001-039-F02', 'VAL-001-050-F01'])
- ambiguous: 1 (['VAL-001-008-F02'])
- human-confirmed present: 7 (['VAL-001-009-F01', 'VAL-001-009-F02', 'VAL-001-011-F01', 'VAL-001-022-F02', 'VAL-001-026-F02', 'VAL-001-037-F01', 'VAL-001-050-F05'])

Repair cohort (Repairability stage): ['VAL-001-039-F02', 'VAL-001-050-F01']; excluded: ['VAL-001-008-F02'].

## Covered side

- covered-side sample: 40
- V2 model labels: {'SEMANTICALLY_PRESENT': 40} (model evidence only)
- human-reviewed subset: 10 (['VAL-001-009-F03', 'VAL-001-008-F03', 'VAL-001-008-F01', 'VAL-001-022-F03', 'VAL-001-011-F03', 'VAL-001-004-F02', 'VAL-001-007-F03', 'VAL-001-024-F03', 'VAL-001-042-F05', 'VAL-001-017-F03'])
- human-confirmed present in subset: 10
- model-only facts without human gold: 30
- caveat: The V2 model adjudicated all 40 covered-side facts as SEMANTICALLY_PRESENT, but only the 10 pre-registered human-review items are human-confirmed. Do not report 40/40 as human-confirmed.

## Integrity

- production generation prompt: grounded-policy-answer-v1 (sha256 5f7018961248fe4d)
- generator / original judge model: deepseek-v4-flash
- frozen source artifact hashes:
  - `eval/broad_queries_v3_adjudicated.json`: `9e15b40cc5068aa4`
  - `eval/broad_query_v3_atomic_facts_frozen_candidate.json`: `616e0968038a26b2`
  - `eval/results/generation_utilization_results.json`: `01be9f9c3a3c26b8`
  - `eval/results/measurement_validity_audit.json`: `d8d90af8b2e17be1`
  - `eval/results/measurement_validity_audit_v2.json`: `516afe9a0185920a`
  - `eval/results/reranker_transfer_results.json`: `bbce7fa512bfbf9d`
  - `eval/validation/broad_atomic_facts_validation_v1.json`: `451a583f5ce88e0b`
  - `eval/validation/broad_queries_validation_v1.json`: `1fb2b03d752343ea`
  - `eval/validation/validation_v1_metadata.json`: `a91ab96a6c3f2555`
