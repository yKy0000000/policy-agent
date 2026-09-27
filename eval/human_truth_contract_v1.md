# Human Truth Contract v1 — Query-Required Aspect Adjudication

**Status: rules FROZEN for Stage 1 (verdicts pending).** This document defines how human reviewers turn
the frozen aspect lists (Validation V1 rubric, Broad Query V3 rubric) into the primary truth used by
Stage 1. It does not itself contain verdicts; verdicts live in
`eval/results/human_truth_stage0_worksheet.json` and must be frozen and hashed before any Stage 1
answer-level conclusion.

Background measurement finding to be preserved: a policy fact that is *missing* or *relevant* is not
automatically a *query-required* answer error (`missing policy fact ≠ query-required answer error`).
Rubric coverage therefore stays diagnostic until adjudicated here.

## 1. Scope

- Validation V1 aspects: `eval/validation/broad_atomic_facts_validation_v1.json` (239 items).
- Broad Query V3 aspects: `eval/broad_query_v3_atomic_facts_frozen_candidate.json`, `required == true`
  only (92 items).
- Worksheet: `eval/results/human_truth_stage0_worksheet.json` (331 rows, one per aspect).
- Route labels in the worksheet come from the frozen `query-structure-router-v1`
  (`eval/query_aware_router_v1.json`); they are not re-derived by reviewers.

## 2. Adjudication question and verdicts

For each row, using the query and the frozen aspect statement (support/evidence is shown for context only):

> For this user's query, is this statement a required part of a correct answer?

- `QUERY_REQUIRED` — a correct answer to this query must include or directly address this statement.
- `RELEVANT_BUT_OPTIONAL` — true and related policy content, but a correct answer to this query can omit it.
- `AMBIGUOUS` — cannot be decided reliably from the query text and the frozen statement.

## 3. Frozen adjudication rules

1. Judge from **query intent + the frozen statement**, not from what the evidence contains or how easy the
   answer is. Evidence is context only.
2. A statement is `QUERY_REQUIRED` only if omitting it would make the answer substantively incomplete for
   the query as asked; topical relevance alone is not enough.
3. Scope qualifiers in the query are honored: if the query says "summary" or asks for one step, secondary
   conditions/exceptions are `RELEVANT_BUT_OPTIONAL` unless the query explicitly asks for conditions,
   exceptions, or risks.
4. Comparison and process queries: comparison aspects are required only when the query asks for the
   comparison; procedural steps are required only when the query asks how to do something.
5. Overlapping or duplicate aspects are adjudicated independently by aspect ID; no deduplication across
   rows.
6. Reviewers must not consult model outputs or prior stage results while adjudicating; each reviewer records
   their visible-information scope.

## 4. Review protocol

1. Reviewer 1 adjudicates every row.
2. Reviewer 2 independently adjudicates all high-priority rows: all V1 `BROAD`-routed rows, all V3 rows,
   and all SIMPLE sentinel rows (sentinel list frozen in the worksheet).
3. Initial labels are recorded before any discussion.
4. Disagreements are adjudicated before hashing using the rules above; unresolved disagreements are recorded
   as `AMBIGUOUS` (never forced to `QUERY_REQUIRED`).
5. `final` is the verdict that counts; it must be one of the three verdicts.

## 5. Primary-set shrinkage

- Primary set = rows with `final == QUERY_REQUIRED` only.
- `RELEVANT_BUT_OPTIONAL` and `AMBIGUOUS` rows are excluded from the primary denominator and reported
  separately as secondary diagnostics.
- `relevant_but_optional_share` and `ambiguous_share` are reported for every Stage 1 comparison so that
  shrinkage is visible and cannot silently change the benchmark.
- The shrinkage rule and the frozen verdict file are hashed before Stage 1; they must not change afterward.

## 6. SIMPLE sentinels

The frozen sentinel list is the deterministic 8-case sample recorded in the worksheet
(`sentinel_queries`). Sentinel cases receive full answer-level human review in Stage 1 for non-inferiority,
in addition to automatic metrics.

## 7. Freeze requirements (Stage 1 preconditions)

- All `final` fields populated; `status` set to `frozen_human_verdicts`.
- Worksheet SHA-256 and this contract's SHA-256 recorded in the Stage 1 preregistration before any Stage 1
  evaluation call.
- No post-hoc re-adjudication after Stage 1 outputs are seen; any correction requires a new version and
  re-run.
