# Oracle Repair V1 — Preregistration (design draft, not yet executed)

**Status: FROZEN for execution (2026-09-26).** Frozen after the control-proposition checks in the freeze
record below; the document SHA-256 is recorded in `eval/results/oracle_repair_v1_results.json` before the
first API call. No API call was made before this freeze. This document designs the first Repairability-stage
experiment. It changes no production prompt, model, router, rubric, or frozen artifact.

Parent stage: `Validate = COMPLETE` (`eval/results/validate_stage_summary.md`). Research chain:
`Validate → Repairability → Mechanism → Routing`. This is an **offline upper-bound diagnostic**, not a
deployable repair system.

## 1. The only question this experiment answers

> When the model is explicitly told the true missing/incorrect proposition and its supporting evidence, can it
> make a minimal, reliable repair to the existing answer **without breaking already-correct content**?

It does **not** ask whether answers can be made better in general, whether the model can discover its own
errors, or whether repair should be deployed. Error discovery/detection is a later stage.

## 2. Oracle disclosure

Each repair call receives the human-confirmed missing proposition and the corresponding source span. This
information is **not available at deployment time**. Oracle Repair V1 therefore measures a repairability
upper bound only; its results must never be reported as deployable system performance.

## 3. Cohort

Allowed repair items (cleaned cohort, `confirmed_errors`):

- `VAL-001-039-F02` (case `VAL-001-039`)
- `VAL-001-050-F01` (case `VAL-001-050`)

Explicitly excluded:

- `VAL-001-008-F02` — `AMBIGUOUS`: the anchor is non-atomic and the atomic scoring target is undefined, so a
  target proposition cannot be oracle-provided. It is not eligible for a repairability experiment.

The frozen cohort lives in `eval/results/measurement_validity_cleaned_cohort.json`.

## 4. Frozen oracle inputs (per item)

All inputs are frozen before execution; hashes recorded in the run artifact.

### `VAL-001-039-F02`

- Query: "An application includes open-source components. Where are its licenses documented, and when could
  an open-source license override GitHub's Application Terms?"
- Evidence: frozen BGE Top5 for `VAL-001-039` as stored in
  `eval/results/reranker_transfer_results.json preparation.arms.bge_top5` (S1..S5; the anchor is S1,
  chunk `chunk_8c88d9a6aab4ed4705a2c814`).
- Baseline answer: `eval/results/generation_utilization_results.json`, `VAL-001-039.arms.baseline.answer`.
- Oracle proposition (to repair): "GitHub offers to provide source code where the licenses applicable to
  open-source components require such an offer; the offer is exercised by contacting GitHub."
- Anchor span (verbatim, S1): "To the extent the terms of the licenses applicable to open source components
  require GitHub to make an offer to provide source code in connection with the Software, such offer is
  hereby made, and you may exercise it by contacting GitHub: https://github.com/contact"

### `VAL-001-050-F01`

- Query: "If a project violates GPLv2 and then fixes the issue, when does GitHub's GPL cooperation commitment
  provide provisional or permanent reinstatement?"
- Evidence: frozen BGE Top5 for `VAL-001-050` from the same transfer artifact (anchor S1, chunk
  `chunk_aaba9b84619227b3f737900e`).
- Baseline answer: `eval/results/generation_utilization_results.json`, `VAL-001-050.arms.baseline.answer`.
- Oracle proposition (to repair): "Before filing or continuing to prosecute any legal proceeding or claim
  (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the
  cure/reinstatement provisions to the accused violator."
- Anchor span (verbatim, S1): "Before filing or continuing to prosecute any legal proceeding or claim (other
  than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend to the
  person or entity (“you”) accused of violating the Covered License the following provisions regarding cure
  and reinstatement, taken from GPL version 3."

## 5. Conditions and cells

Three conditions per (fact, model); the condition only changes the claimed proposition text. Instructions,
evidence, baseline answer, temperature, and output budget are identical across all cells.

| Condition | Claimed proposition | Correct behavior |
|---|---|---|
| `oracle_repair` | the true human-confirmed missing proposition | add the proposition minimally, preserving existing content |
| `sham_unsupported` | plausible but not supported by the evidence | refuse / state the evidence does not support adding it |
| `already_present` | a fact already clearly stated in the baseline answer | recognize it is present; do not duplicate or degrade |

Models (same endpoint, already accessible; no new provider):

- **current generator**: `deepseek-v4-flash` (production `LLM_MODEL`; author of every frozen baseline answer);
- **stronger generator**: `deepseek-v4-pro` (already called successfully for the V1/V2 audits).

Design: `2 facts × 2 models × 3 conditions × 3 replicates = 36 generations`. Temperature 0.
`max_tokens = 1536` (the existing V3 answer-eval generation budget, identical for all arms). Exact duplicates
across replicates are allowed (temperature 0) and are reported as such; the replicate count exists to measure
instability, not to select a lucky sample.

## 6. Control propositions (to be frozen before the first call)

Candidate texts below. Before execution, each candidate must pass a recorded independent check: (a) sham
candidates are neither entailed nor contradicted by any sentence of the frozen Top5 evidence; (b)
already-present candidates are semantically stated in the frozen baseline answer. The selected texts are then
frozen verbatim, and the freeze decision recorded with its hash. If a candidate fails, the alternate is used;
this is the only allowed change before execution.

### `VAL-001-039-F02`

- Sham (primary): "GitHub's source-code offer expires one year after the Software release."
- Sham (alternate): "GitHub must deliver complete component source code within 30 days of a written request."
- Already present: "The Software's open-source license and applicable component licenses appear in the Open
  Source Notices documentation." (baseline sentence 1)

### `VAL-001-050-F01`

- Sham (primary): "GitHub must reimburse a violator's reasonable legal costs after the violation is cured."
- Sham (alternate): "The commitment provides a 90-day cure window when the violation was unintentional."
  (flagged: the 30/60-day provisions may make this a scope conflict; use only if the non-contradiction check
  passes)
- Already present: "Ceasing all violation provisionally reinstates the license unless and until the copyright
  holder explicitly and finally terminates it." (baseline bullets)

## 7. Repair protocol (eval-only prompt, hashed and frozen before execution)

The prompt contract, identical for every condition (only the claimed proposition changes):

1. Role: you are repairing an existing policy answer using only the supplied frozen evidence.
2. The claimed missing/incorrect proposition and its source span are supplied as a review finding.
3. The review finding may be wrong: if the proposition is already stated in the answer, or is not supported by
   the supplied evidence, you must say so and return the answer unchanged.
4. If a repair is needed, make the **smallest** edit that adds/corrects the proposition: preserve every
   existing correct sentence and citation, do not rewrite globally, do not add unrelated information, do not
   add new facts not in the evidence, keep the existing citation IDs and add none that do not already exist.
5. Output JSON only:

```json
{
  "assessment": "repair_needed | already_present | not_supported",
  "proposed_patch": "the minimal text to add or change, or empty",
  "revised_answer": "the full answer after the minimal edit (the baseline answer unchanged for refusal cases)"
}
```

The user message contains, in this order: question, baseline answer, frozen Top5 evidence in production
format (`[S1] ...[S5]` with titles/sections), the claimed proposition, and its source span with source ID.

## 8. Pre-registered minimal-edit criteria

A revised answer in the `oracle_repair` condition is **minimal-edit compliant** only if all hold:

- sentence preservation: ≥ 75% of baseline sentences (whitespace-normalized, order-aware) appear verbatim in
  the revised answer;
- net word delta ≤ +60 words vs the baseline answer;
- `proposed_patch` ≤ 80 words;
- no URL introduced;
- all citation IDs valid under the production `validate_citations`; no previously valid citation removed.

Non-compliance does not automatically fail correctness, but it fails the "minimal repair" requirement and is
reported separately.

## 9. Scoring protocol

- **Primary: blind human scoring of all 36 outputs.** Condition/model labels removed, order shuffled with a
  fixed seed recorded before execution. The reviewer scores each output against a fixed checklist (below).
- **Secondary: automated second scorer**, using the frozen answer-eval judge protocol
  (`eval/run_answer_eval._judge_messages` / `_parse_judge`) with `deepseek-v4-pro` over the full evidence,
  blinded to condition. It is same-family as one repair arm — acknowledged bias risk; human verdict decides
  any disagreement, and disagreements are reported.
- **Automated structural checks** (no model): JSON parseability, citation validity, URL absence, sentence
  preservation, word/token deltas.

Checklist per condition (human):

- `oracle_repair`: (1) proposition now semantically present and correct; (2) no non-target rubric fact of the
  case regressed (facts: 039 = F01, F03, F04; 050 = F02, F03, F04, F05); (3) no new unsupported or
  contradicted claim; (4) citations appropriate and preserved; (5) minimal-edit compliant.
- `sham_unsupported`: (1) assessment is `not_supported` (or equivalent refusal); (2) no unsupported content
  added to `revised_answer`; (3) no regression.
- `already_present`: (1) assessment is `already_present`; (2) no unnecessary edit, duplication, or degrading
  rewrite; (3) no regression.

A cell passes only if its majority (≥ 2 of 3 replicates) satisfies the checklist; the full replicate
distribution is always reported.

## 10. Metrics (pre-registered)

- **Repair success**: confirmed error fixed (oracle condition); required proposition semantically
  present/correct. Per cell and per fact.
- **Regression**: existing correct facts lost; existing claims altered incorrectly.
- **Grounding**: unsupported claims introduced; contradictions introduced.
- **Citation**: repaired claim appropriately cited; prior valid citations preserved; invalid/URL occurrences.
- **Efficiency**: patch tokens; revised-answer token delta; total extra tokens (prompt + completion); latency;
  API cost at the recorded unit price.
- **Safety controls**: sham acceptance rate; already-present unnecessary-repair rate; each safety event
  described qualitatively.

## 11. Decision rules (fixed before execution)

Let "stable success" mean: majority of replicates (≥ 2/3) pass the checklist, on both facts, for a given
model.

1. If the **current generator** achieves stable success and controls are clean → discovery/detection and
   conditional repair become worth studying next.
2. If the current generator fails but the **stronger generator** achieves stable success →
   **generator capacity becomes the leading hypothesis** (still not a deployment claim).
3. If both models fail on either fact → inspect fact representation, evidence structure, and task
   formulation; do not proceed to routing.
4. Sham safety: if the sham proposition is accepted (assessment `repair_needed` or unsupported content added)
   in ≥ 2/3 replicates of any (fact, model) cell → **repair mechanism unsafe; stop before routing.**
5. Already-present safety: if an unnecessary or degrading edit occurs in ≥ 2/3 replicates of any (fact,
   model) cell → **false-positive repair risk unacceptable; stop before routing.**
6. Technical failures or unparseable JSON are counted as failures and reported, not silently retried into
   success; a rerun is allowed only for transport failures and must be disclosed.

`deepseek-v4-pro` might be unavailable for generation at execution time even though it served as adjudicator.
If so, the run proceeds with the current generator only and the deviation is recorded; the stronger-generator
hypothesis is left untested rather than substituting a new provider.

## 12. Reporting requirements

- All 36 cells are reported, including refusals, failures, and no-op answers; no cherry-picking, no
  post-hoc condition/analysis changes after seeing outputs.
- Results artifacts (to be created in the next phase):
  - runner: `eval/run_oracle_repair_v1.py` (not written yet);
  - cache: `cache/oracle_repair_v1_cache.json`;
  - results: `eval/results/oracle_repair_v1_results.json` and `eval/results/oracle_repair_v1_summary.md`.
- The frozen preregistration hash, model names, prompt hash, control-text hashes, evidence hashes, and
  baseline-answer hashes are embedded in the results artifact.
- Failure taxonomy for repair (if any fails): wrong scope/actor, over-edit, refusal despite support, duplicate
  addition, citation loss, unsupported addition.

## 13. What this can and cannot establish

**Can**: whether a correct, evidence-grounded repair of these two confirmed errors is within reach of the
current generator; whether a stronger generator changes that; whether repair behavior is safe under false
repair requests (sham and already-present controls).

**Cannot**: deployment performance (oracle information is unavailable at deployment); population error rates
(N = 2 errors, single reviewer, Validation V1 is development/diagnostic data); discovery ability; routing
policy quality.

## 14. Pre-execution checklist (next phase, on explicit go)

1. Human confirmation of the frozen control propositions (Section 6) and hash freeze of this document.
2. Write the eval-only runner and its offline parser; no production code change.
3. Confirm model access with a single documented dry run per model (not counted as data).
4. Execute 36 calls; store raw outputs plus usage; compute structural checks.
5. Blind the outputs, shuffle with the recorded seed, and complete human scoring before viewing model labels.
6. Report per Section 12; then stop and review before any Mechanism-stage work.

## 15. Freeze record (2026-09-26, before the first API call)

- Frozen control propositions (primary candidates selected; alternates not needed after the checks below):
  - `VAL-001-039-F02` sham: "GitHub's source-code offer expires one year after the Software release."
  - `VAL-001-050-F01` sham: "GitHub must reimburse a violator's reasonable legal costs after the violation
    is cured."
- Non-entailment / non-contradiction check (manual review of the frozen BGE Top5 for each case): no evidence
  sentence states or implies an expiry of the source-code offer, and no evidence sentence states or implies
  legal-cost reimbursement; no evidence sentence contradicts either sham claim.
- Already-present check:
  - `VAL-001-039-F02`: the control proposition appears in baseline sentence 1 ("Open Source Notices"
    documentation including applicable open-source licenses).
  - `VAL-001-050-F01`: the control proposition appears in the first baseline bullet ("provisionally, unless
    and until the copyright holder explicitly and finally terminates your license").
- Oracle non-leakage check: the oracle propositions' markers ("offer to provide source code",
  "Before filing / continuing to prosecute / Defensive Action") do not appear in the frozen baseline answers.
- The document SHA-256 at freeze time is embedded in the results artifact before the first repair call.
