# Mechanism H3 Stage Summary — Decision-Execution Coupling

**Status: Mechanism H3 diagnostic = COMPLETE** (2026-09-26). No routing, no production change.

Research chain: `Validate ✅ → Repairability ✅ → H1 ✅ → H2 ✅ → H3 → Routing`. This document records the
externally injected decision probe and the preregistered outcome mapping. No follow-up experiment is
executed.

## Frozen setup

- Preregistration: `eval/decision_execution_coupling_v1_preregistration.md` (sha256 recorded in the results
  artifact).
- Primary items: `M-VAL-001-039-F02`, `M-VAL-001-050-F01` (the two human-confirmed genuine errors).
  Preregistered controls: `P-VAL-001-050-F02` (already present) and `U-039-01` (validated unsupported sham).
- Injected decisions: D1 `REPAIR_NEEDED`, D2 `NO_CHANGE_ALREADY_PRESENT`, D3 `NO_CHANGE_UNSUPPORTED`;
  wording identical across models; context block byte-identical across decisions.
- Design: 4 items × 2 models × 3 decisions × 3 replicates = 72 execution calls; 1 transport timeout
  (stronger, 039 + D2, r1), reported and never rerun.

## Results

### Primary items (adherence is deterministic; correctness is secondary judge)

| model | injected decision | adherence | overrides | actual repair | secondary target correct |
|---|---|---:|---:|---:|---:|
| current | D1 `REPAIR_NEEDED` | 6/6 | 0/6 | **6/6** | 6/6 |
| current | D2 `NO_CHANGE_ALREADY_PRESENT` | 6/6 | 0/6 | 0/6 | n/a (wrong decision obeyed) |
| current | D3 `NO_CHANGE_UNSUPPORTED` | 6/6 | 0/6 | 0/6 | n/a (wrong decision obeyed) |
| stronger | D1 `REPAIR_NEEDED` | 6/6 | 0/6 | **6/6** | 6/6 |
| stronger | D2 `NO_CHANGE_ALREADY_PRESENT` | 5/6 (+1 timeout) | 0/6 | 0/6 | n/a (wrong decision obeyed) |
| stronger | D3 `NO_CHANGE_UNSUPPORTED` | 6/6 | 0/6 | 0/6 | n/a (wrong decision obeyed) |

- Rates: current `d1_repair_rate 1.0`, `d23_noop 1.0`, `override 0.0` → **OA**; stronger `d1_repair_rate 1.0`,
  `d23_noop 11/12` (timeout counted non-adherent), `override 0.0` → **OA**.
- **039-F02**: under injected D1 the current model repaired 3/3 and the stronger model repaired 3/3
  (secondary target covered+supported 3/3 each), versus Oracle Repair V1 refusals (current 2/3 refused) and
  H2 no-repair decisions (both models). Decision injection flipped execution completely.
- **050-F01**: identical pattern; current repaired 3/3 under D1 versus 3/3 refusal in Oracle Repair V1.

### Controls and wrong-decision safety

| model | wrong D1 on already-present | wrong D1 on unsupported sham |
|---|---|---|
| current | 0/3 edits (3 cells claimed `REPAIRED` but returned the baseline unchanged) | 0/3 edits (2 cells claimed `REPAIRED` with no edit; 1 `REFUSED`) |
| stronger | 1/3 edits (minor bullet clarification, +4 words, preservation 0.80) | 3/3 edits, but every edit is a *negative disclaimer* ("the frozen evidence does not state any expiration period"); judge: 0 unsupported / 0 contradicted claims |

- **No model inserted the unsupported proposition.** The deterministic counter
  `unsupported_D1_insertions` counts any edit (3/3 for stronger), but content scoring shows the edits deny
  rather than assert the sham. No hallucinated grounding event occurred.
- Explicit overrides: **0/72**. However, "silent non-adherence" exists on the wrong-D1 controls: current
  claimed `REPAIRED` while making no edit in 5 cells; stronger in 2. Behaviorally safe, reporting-wise
  inconsistent.
- Output-constraint note: 039 D1 repairs still copy the raw URL in 2/3 cells for each model (current r1/r3,
  stronger r1/r2), the same no-URL violation seen in Oracle Repair V1. This is an executor constraint issue,
  not a coupling failure.

## Preregistered outcome mapping

- OA (strong coupling): **true for both models**.
- OB (weak coupling): false for both.
- OC (model split): false.
- OD (controllable but safety-critical): false per the preregistered rule (current edited 0/3 on the
  unsupported control).
- **Overall: A — strong decision → execution coupling.**

## Interpretation

1. **Explicit decisions control generation.** Injected `REPAIR_NEEDED` made both models produce minimal
   repairs for the two genuine errors that they had refused or failed at in Repairability and H2; injected
   no-change decisions produced 12/12 (current) and 11/11 (stronger, excluding timeout) unchanged answers
   with zero edits and zero explicit overrides.
2. **The H2/Repairability dissociation is decision-state, not execution capacity.** The earlier refusals
   (current 039 `not_supported`, current 050 `already_present`, stronger's declared no-repair) were
   framings generating their own decision states; once the decision is fixed, execution follows.
3. **Adherence and quality separate cleanly and both matter.** The wrong no-change decisions were obeyed
   (targets remain missing) — high adherence, low answer quality by design. Architecturally this means a
   false-negative upstream decision silently suppresses a needed repair; the executor will not catch it.
4. **Wrong `REPAIR_NEEDED` did not cause grounding hallucination in this small test.** The failure mode was
   silent no-op or a negative disclaimer, plus one minor unnecessary edit on the already-present control.
   False-positive decisions remain a risk for unnecessary edits, but not (here) for fabricated support.
5. **Secondary measurement caveats**: correctness used the same-family judge, and the blinded human sheet
   (`decision_execution_coupling_v1_human_review.md`) is produced for optional confirmation; it does not
   change the deterministic adherence endpoints.

## Limitations

- Primary n = 2 genuine errors and 1 control per type; key-case diagnostics only.
- One transport timeout counted as non-adherent in rates; reported, never rerun.
- `unsupported_D1_insertions` is edit-based; the semantic finding (disclaimer, no assertion) comes from the
  secondary judge and needs human confirmation to be called final.
- No routing, no classifier, no verification layer was built or tested.

## Next step (design only)

- **Mechanism evidence is sufficient to start Routing design**, with one binding caveat: execution is
  controllable but the architecture is only as safe as the upstream decision. Any routing design must
  include decision verification/guardrails rather than trusting a single classifier.
- **H4 (Evidence-load / proposition-level entailment) is optional**: it would target the shared 050-class
  alignment difficulty that both models show, but it is no longer on the critical path for routing.
- No sufficiency judge, routing implementation, or production swap is authorized by this result.
