# Task-Conditioned Action V1 — Preregistration (Mechanism / H2)

**Status: FROZEN for execution (2026-09-26).** Frozen before the first H2 call; the document SHA-256 is
recorded in `eval/results/task_conditioned_action_v1_results.json`. Hard constraint: **no repair text is
generated** — no patch, no revised answer, no citation insertion, no URL, no rewriting. No routing, no
production change, no evaluator redesign.

Parent chain: `Validate ✅ → Repairability ✅ → Mechanism H1 ✅ → Mechanism H2 → Routing`. H1 showed that the
current model is not worse than the stronger model at pure semantic-state classification, yet the two
models' Repairability behavior differed sharply. H2 isolates the middle layer: semantic state → action
decision.

## 1. Research question

With query, baseline answer, frozen evidence, and atomic proposition held exactly fixed, does changing only
the task framing systematically change whether the model decides that a repair action is required?

Three layers are separated:

1. semantic-state classification (H1, reused);
2. **action decision without generation (this experiment)**;
3. actual repair generation (Oracle Repair V1, already complete).

## 2. Frames

### Frame A — Semantic Classification (frozen reuse, no new calls)

The H1 probe, reused verbatim from `eval/results/semantic_gap_discrimination_v1_results.json`:
`MISSING | ALREADY_PRESENT | UNSUPPORTED`. No repair.

### Frame B — Action Decision (new calls)

System role: decide whether the baseline answer requires repair for the proposition. Output only
`REPAIR_NEEDED | NO_CHANGE_ALREADY_PRESENT | NO_CHANGE_UNSUPPORTED`, evidence source IDs, and a brief
reason (<= 40 words). No patch, no revised answer, no rewriting.

### Frame C — Repair Intent Without Editing (new calls)

System role: an answer-repair task; decide whether the answer would need modification. Output only
`WOULD_REPAIR | WOULD_NOT_REPAIR_ALREADY_PRESENT | WOULD_NOT_REPAIR_UNSUPPORTED`, evidence source IDs, and a
brief reason. Producing any modification, patch, revised answer, citation insertion, or URL is forbidden.

Both B and C use the same context block as A; only the instruction/schema block differs. B and C share an
identical context prefix.

## 3. Canonical action mapping (deterministic)

| semantic / decision label | canonical action state |
|---|---|
| `MISSING`, `REPAIR_NEEDED`, `WOULD_REPAIR` | `REPAIR` |
| `ALREADY_PRESENT`, `NO_CHANGE_ALREADY_PRESENT`, `WOULD_NOT_REPAIR_ALREADY_PRESENT` | `NO_CHANGE_PRESENT` |
| `UNSUPPORTED`, `NO_CHANGE_UNSUPPORTED`, `WOULD_NOT_REPAIR_UNSUPPORTED` | `NO_CHANGE_UNSUPPORTED` |

Any other label is invalid and non-parseable output counts as a technical failure (reported, not retried
into success).

## 4. Dataset (frozen reuse)

The H1 27-item probe set is reused without modification:

- MISSING = 2 (`VAL-001-039-F02`, `VAL-001-050-F01`);
- ALREADY_PRESENT = 19 (17 MVA human-confirmed present + 2 Oracle Repair controls);
- UNSUPPORTED = 6 (2 frozen shams + 1 preregistered alternate + 3 validated additions);
- `VAL-001-008-F02` excluded.

The H2 runner rebuilds the dataset from the same frozen artifacts and asserts item-by-item equality with
`eval/results/semantic_gap_discrimination_v1_results.json` (`dataset.items`), plus the frozen input hashes.
No re-sampling, no new items.

## 5. Models, budget, replicates

- current = `deepseek-v4-flash`; stronger = `deepseek-v4-pro` (same as Repairability and H1).
- Identical item set, evidence, proposition, `temperature = 0.0`, `max_tokens = 200`, timeout 120 s.
- 3 replicates per item × model × frame: 27 × 2 × 2 = 324 new calls (B and C), plus frozen Frame A.
- No selective rerun after seeing results; technical failures are reported.

## 6. Metrics (primary)

1. **A→B and A→C canonical transition matrices** per model over the 27 items (modal label per frame).
2. **Frame consistency** per item: how many distinct canonical states appear across A/B/C; count of
   consistent items and action-flip items; pairwise flip counts (A-B, A-C, B-C).
3. **Per-gold-class action accuracy** per frame per model: gold MISSING → `REPAIR`, gold ALREADY_PRESENT →
   `NO_CHANGE_PRESENT`, gold UNSUPPORTED → `NO_CHANGE_UNSUPPORTED`; reported as per-class recall plus
   canonical confusion matrices, never a single accuracy alone.
4. **Key-case readouts** for `VAL-001-039-F02` and `VAL-001-050-F01`: per-frame replicate labels, modal
   label, canonical state.
5. **Replicate consistency** per item × model × frame (3/3, 2/3, 1/3).

Auxiliary: evidence-ID validity; `brief_reason` length; forbidden-output audit (no patch/revised answer
fields present).

## 7. Preregistered outcome rules (fixed before execution)

Let `missing = {M-VAL-001-039-F02, M-VAL-001-050-F01}`; modal canonical states per frame are used.
`current_refused(item)` / `stronger_refused(item)` come from the frozen human-scored Repairability artifact
(any Repairability cell for that fact classified `genuine_no_repair` = refused).

- **OA (strong H2 support)**: for current, some item in `missing` has A = `REPAIR` and (B ≠ `REPAIR` or
  C ≠ `REPAIR`), and `current_refused(item)` is true. Conclusion: task framing changes the model's action
  policy even when semantic-state classification is correct.
- **OB (H2 weakened)**: for current, every item in `missing` has A = B = C = `REPAIR`, yet
  `current_refused` is true for at least one. Conclusion: failure is downstream of action decision
  (execution/generation stage).
- **OC (stronger-only beneficial framing shift)**: for stronger on `VAL-001-050-F01`, A ≠ `REPAIR` and
  (B = `REPAIR` or C = `REPAIR`), and the stronger model repaired that item in Oracle Repair V1.
  Conclusion: repair-oriented framing changes the stronger model's action state (not "better reasoning").
- **OD (unstable)**: any item × model × frame among `missing` has no modal label (all three replicates
  differ). Conclusion: H2 unresolved; inspect instruction sensitivity / nondeterminism.

Overall determination order: OA > OB > OC > OD > "no pattern". All flags are reported regardless of order.
No framing change beyond B/C, no H3, no generation.

## 8. Limitations (declared)

- MISSING n = 2; the OA/OB rules are key-case diagnostics, not population estimates.
- Frame A is reused from H1 (frozen), not re-collected in the same session; source artifacts are
  hash-verified and the A reference is frozen.
- Items cluster by case/evidence/query.
- B/C measure declared action intent, not executed edits; the action-decision → generation gap remains
  untested here.
- H3 (proposition-level entailment / evidence load) is explicitly out of scope.

## 9. Artifacts and stop condition

- runner `eval/run_task_conditioned_action_v1.py`; cache `cache/task_conditioned_action_v1_cache.json`;
  results `eval/results/task_conditioned_action_v1_results.json`; summary
  `eval/results/task_conditioned_action_v1_summary.md`; stage summary
  `eval/results/mechanism_h2_stage_summary.md`.
- After completion: report transitions, consistency, per-class action accuracy, key cases, and whether H2
  is supported/weakened/unresolved, then stop. No automatic next experiment.
