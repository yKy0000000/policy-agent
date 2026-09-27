# Mechanism H1 Stage Summary — Semantic Gap Discrimination

**Status: Mechanism H1 diagnostic = COMPLETE** (2026-09-26). No repair, no routing, no production change.

Research chain: `Validate ✅ → Repairability ✅ → Mechanism (H1) → Routing`. This document records the H1
probe result and the preregistered outcome mapping. It executes no follow-up experiment.

## Frozen setup

- Preregistration: `eval/semantic_gap_discrimination_v1_preregistration.md` (sha256
  `eef5b220aa7520e4…`; full hash in the results artifact).
- Dataset: 27 items = 2 MISSING (both human-confirmed genuine errors: `VAL-001-039-F02`,
  `VAL-001-050-F01`) + 19 ALREADY_PRESENT (17 MVA human-confirmed present + 2 Oracle Repair controls) +
  6 UNSUPPORTED (2 frozen shams + 1 preregistered alternate + 3 validated additions). `VAL-001-008-F02`
  excluded.
- Design: 27 items × 2 models × 3 replicates = 162 calls; identical prompt/evidence/schema/budget;
  classification only.

## Results (human-independent, modal label; rows = gold)

| model | MISSING recall | ALREADY_PRESENT recall | UNSUPPORTED recall | overall |
|---|---:|---:|---:|---:|
| current (`deepseek-v4-flash`) | 1/2 | 18/19 | 6/6 | 26/27 (96.3%) |
| stronger (`deepseek-v4-pro`) | 1/2 | 14/19 | 6/6 | 21/27 (77.8%) |

- MISSING → ALREADY_PRESENT: current 1/2, stronger 1/2. MISSING → UNSUPPORTED: 0/0.
- Consistency (3/3, 2/3, 1/3): current 26 / 1 / 0; stronger 25 / 2 / 0.
- `VAL-001-039-F02`: current MISSING 3/3, stronger MISSING 3/3.
- `VAL-001-050-F01`: current ALREADY_PRESENT 3/3; stronger UNSUPPORTED, ALREADY_PRESENT, ALREADY_PRESENT.
- UNSUPPORTED: 6/6 for both models; no sham acceptance in classification.
- Preregistered operational outcome: **mixed/unresolved** (not A: stronger is not correct on both MISSING
  items; not B: current is not correct on both; not C: modal matrices differ).

## Descriptive mechanism readout

1. **H1 is not supported as a between-model explanation of the Repairability gap.** The classification
   probe does not reproduce the Repairability ordering: the stronger model is *worse* on ALREADY_PRESENT
   (14/19 vs 18/19; five human-confirmed present paraphrase facts labeled MISSING, most 3/3), equal on
   UNSUPPORTED (6/6), and equal on the two MISSING items (1/2 each). Overall accuracy is higher for the
   current model (96.3% vs 77.8%).
2. **The 039 repair failure is not reproduced at classification.** Both models classify
   `VAL-001-039-F02` as MISSING 3/3, yet in Repairability the current model refused it as `not_supported`
   in 2/3 cells. Correct classification followed by refusal is task/action-policy evidence, not a
   proposition-classification deficit → **H2 rises** for this item.
3. **The 050 failure is shared.** Both models misclassify `VAL-001-050-F01` as ALREADY_PRESENT (current
   3/3; stronger 2/3 plus one UNSUPPORTED). The current model's justifications use merged
   "implicitly covering" reasoning, the same over-lenient semantic matching pattern seen in the V2
   adjudicator. This is a shared proposition-level alignment difficulty, not a current-specific deficit;
   it keeps an H3-adjacent (proposition-level entailment / evidence load) explanation plausible, but this
   experiment cannot isolate it (no short-span condition).
4. **The stronger model repairs despite misclassifying.** In Repairability, the stronger model repaired
   050 3/3 while classifying it ALREADY_PRESENT here; the current model failed both. The current-vs-
   stronger Repairability gap is therefore more consistent with task framing / action policy on top of a
   shared 050 difficulty than with a general classification-capability gap.
5. **Safety**: zero UNSUPPORTED misclassifications and zero sham acceptance in classification for both
   models; the Repairability controls remain the stronger safety evidence.

## Validity notes (do not over-read)

- MISSING n = 2; 050 contributes one item; no population or "overall reasoning ability" claim.
- The stronger model's five MISSING labels on human-confirmed present facts (008-F03, 009-F02, 022-F02,
  026-F02, 037-F01) have proposition-specific justifications; whether they are over-strict errors or
  latent gold-boundary issues cannot be decided without re-adjudication, which is out of scope. The frozen
  human gold is kept; the preregistered 050-F05 sensitivity is reported in the machine summary (does not
  change the ordering).
- Items cluster by case/evidence/query; effective sample size is below 27.
- Full BGE Top5 only; no short-span or prompt-framing variation was tested.

## Next-step recommendation (design only)

- **Prioritize H2** (instruction / repair-task framing / conservative action policy): the 039
  correct-classification-but-refused pattern and the stronger model repairing a proposition it
  misclassifies both point to the action policy, not classification.
- **H3 remains plausible as secondary** for the shared 050 alignment difficulty (proposition-level
  entailment under long evidence); a dedicated evidence-length / entailment experiment would be needed,
  and this probe cannot settle it.
- No sufficiency judge, routing, production swap, or new generation calls are authorized by this result.
  Mechanism H2 preregistration / experiment design is the next step, pending explicit instruction.
