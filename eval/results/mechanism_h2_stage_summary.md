# Mechanism H2 Stage Summary — Task-Conditioned Action

**Status: Mechanism H2 diagnostic = COMPLETE** (2026-09-26). No repair generation, no routing, no
production change.

Research chain: `Validate ✅ → Repairability ✅ → Mechanism H1 ✅ → Mechanism H2 → Routing`. This document
records the H2 action-decision probe and the preregistered outcome mapping. No follow-up experiment is
executed here.

## Frozen setup

- Preregistration: `eval/task_conditioned_action_v1_preregistration.md` (sha256 `…`; full hash in the
  results artifact).
- Dataset: the frozen H1 27-item probe reused item-by-item, asserted equal (2 MISSING / 19 ALREADY_PRESENT /
  6 UNSUPPORTED); `VAL-001-008-F02` excluded.
- Frames: **A** = frozen H1 semantic classification (reused, no new calls); **B** = neutral action decision
  (`REPAIR_NEEDED / NO_CHANGE_ALREADY_PRESENT / NO_CHANGE_UNSUPPORTED`); **C** = repair intent without editing
  (`WOULD_REPAIR / WOULD_NOT_REPAIR_ALREADY_PRESENT / WOULD_NOT_REPAIR_UNSUPPORTED`).
- Hard constraint respected: no patch, no revised answer, no citation insertion, no URL, no rewriting.
- Design: 27 items × 2 models × 2 frames × 3 replicates = 324 new calls, 0 failures.

## Results

### Current (`deepseek-v4-flash`)

- A → B canonical transitions: `REPAIR → NO_CHANGE_UNSUPPORTED 2`; `NO_CHANGE_PRESENT → NO_CHANGE_PRESENT 18,
  → NO_CHANGE_UNSUPPORTED 1`; `NO_CHANGE_UNSUPPORTED → NO_CHANGE_UNSUPPORTED 6`.
- A → C: `REPAIR → REPAIR 2`; `NO_CHANGE_PRESENT → NO_CHANGE_PRESENT 18, → NO_CHANGE_UNSUPPORTED 1`;
  `NO_CHANGE_UNSUPPORTED` stable.
- Frame consistency across A/B/C: 24 consistent, 3 two-state flips (039-F02 `[REPAIR, UNSUPPORTED, REPAIR]`,
  P-009-F02 `[REPAIR, UNSUPPORTED, REPAIR]`, P-037-F01 `[PRESENT, UNSUPPORTED, UNSUPPORTED]`).
- Gold-action recall: Frame A `REPAIR 1/2, PRESENT 18/19, UNSUPPORTED 6/6`; Frame B **`REPAIR 0/2`**,
  `PRESENT 17/19`, `UNSUPPORTED 6/6`; Frame C `REPAIR 1/2, PRESENT 17/19, UNSUPPORTED 6/6`.
- Replicate consistency: A 26/1/0, B 27/0/0, C 25/2/0 (3/3, 2/3, 1/3).

### Stronger (`deepseek-v4-pro`)

- A → B transitions: `REPAIR → NO_CHANGE_PRESENT 4, → NO_CHANGE_UNSUPPORTED 2`;
  `NO_CHANGE_PRESENT → NO_CHANGE_PRESENT 14, → NO_CHANGE_UNSUPPORTED 1`; `UNSUPPORTED` stable.
- A → C: `REPAIR → REPAIR 1, → NO_CHANGE_PRESENT 3, → NO_CHANGE_UNSUPPORTED 2`;
  `NO_CHANGE_PRESENT → NO_CHANGE_PRESENT 14, → NO_CHANGE_UNSUPPORTED 1`.
- Frame consistency: 20 consistent, 7 two-state flips (including 039-F02, 050-F01, P-008-F03, P-009-F02,
  P-022-F02, P-026-F02, P-037-F01).
- Gold-action recall: Frame A `REPAIR 1/2, PRESENT 14/19, UNSUPPORTED 6/6`; Frame B `REPAIR 0/2`,
  **`PRESENT 18/19`**, `UNSUPPORTED 6/6`; Frame C `REPAIR 0/2, PRESENT 17/19, UNSUPPORTED 6/6`.
- Replicate consistency: A 25/2/0, B 26/1/0, C 27/0/0.

### Key cases

| item | model | A (frozen H1) | B | C | Oracle Repair V1 |
|---|---|---|---|---|---|
| 039-F02 | current | MISSING 3/3 → REPAIR | NO_CHANGE_UNSUPPORTED 3/3 | WOULD_REPAIR 3/3 | refused 2/3 (`not_supported`) |
| 039-F02 | stronger | MISSING 3/3 → REPAIR | NO_CHANGE_UNSUPPORTED 3/3 | NO_CHANGE_UNSUPPORTED 3/3 | repaired 3/3 (with URL) |
| 050-F01 | current | ALREADY_PRESENT 3/3 | NO_CHANGE_ALREADY_PRESENT 3/3 | NO_CHANGE 2/3 + WOULD_REPAIR 1/3 | refused 3/3 |
| 050-F01 | stronger | ALREADY_PRESENT modal 2/3 | NO_CHANGE_UNSUPPORTED 3/3 | NO_CHANGE_UNSUPPORTED 3/3 | repaired 3/3 |

## Preregistered outcome mapping

- OA (current framing shift): **true** — `039-F02`: A = `REPAIR`, B = `NO_CHANGE_UNSUPPORTED`, and the
  current model refused that item in Oracle Repair V1.
- OB (action correct, generation failed): false.
- OC (stronger framing shift to repair): false.
- OD (unstable): false — every frame × item × model has a modal label.
- **Overall: A — H2 supported.**

## Interpretation

1. **Task framing systematically changes the action decision.** In Frame B both models moved every
   genuine-MISSING item to `NO_CHANGE_UNSUPPORTED` (`REPAIR` recall 0/2 in both models), even though Frame A
   and the stronger model's evidence reading support repair. The current model's B decision on `039-F02`
   coincides exactly with its Oracle Repair refusal (`not_supported`), while its C frame returns to
   `WOULD_REPAIR` — i.e. the action state is set by the task framing, not by a stable proposition belief.
2. **Decision and generation are dissociated.** The stronger model declared `NO_CHANGE_UNSUPPORTED` for both
   genuine items in B and C, yet generated successful repairs for both in Oracle Repair V1. The current
   model declared `WOULD_REPAIR` for `039-F02` in C while refusing it in 2/3 generation replicates. Neither
   model's generation is governed by its declared action decision. This is the sharpest new lead.
3. **The failure is specific to the REPAIR class.** ALREADY_PRESENT and UNSUPPORTED action accuracy stay high
   in every frame (no safety regression, `UNSUPPORTED 6/6` everywhere); only the genuine-repair decision is
   suppressed by the action framings.
4. **Stronger framing had a corrective side effect on present items** (B raised its PRESENT recall from
   14/19 to 18/19 while its A classification was over-strict), but this is not the preregistered OC pattern
   and is reported descriptively only.
5. H1 remains weakened: classification is not the bottleneck; the action/execution relationship is.

## Limitations

- MISSING n = 2; the OA/OB rules are key-case diagnostics, not population estimates.
- Frame A is frozen reuse from H1, not re-collected in the same session; its source artifact is hash-frozen.
- B/C measure declared intent only; no generation was allowed, so the decision → execution gap is inferred
  from cross-experiment comparison with Oracle Repair V1.
- Items cluster by case/evidence/query.
- H3 (proposition-level entailment / evidence load) was not tested and remains plausible but less indicated.

## Next step (design only)

- **Deepen the action/execution split** as the leading next mechanism question: why does generation produce
  repairs that the declared action decision rejects (stronger), and why does repair-intent framing change the
  decision (current)?
- H3 stays available as a secondary branch if the execution-layer work does not explain the pattern.
- No sufficiency judge, routing, production swap, or new calls are authorized by this result. Mechanism H3 /
  execution-stage preregistration is the next step, pending explicit instruction.
