# Repairability Stage Summary

**Status: Repairability = COMPLETE** (2026-09-26).

Research chain: `Validate -> Repairability -> Mechanism -> Routing`. Validate is complete; this document closes Repairability. Mechanism is next and has not been executed.

## Frozen setup

- Cohort: `VAL-001-039-F02`, `VAL-001-050-F01`; excluded `VAL-001-008-F02` (non-atomic/ambiguous).
- Preregistration sha256: `3fb448c664a34c4f`.
- Design: 2 facts x 2 models x 3 conditions x 3 replicates = 36 cells; oracle-guided minimal repair; human-primary scoring; same-family secondary judge.
- Artifacts: `oracle_repair_v1_results.json` (raw, unchanged), `oracle_repair_v1_human_scored.json`, `oracle_repair_v1_human_summary.md`, `oracle_repair_v1_summary.md`.

## Official human-primary results

### current
- semantic repair success: 1/6
- full constraint-compliant success: 0/6
- semantic success but URL constraint failed: 1/6
- no repair: 5/6
- decision errors: false not_supported 2, false already_present 3, attempted-with-constraint-failure 1
- sham refusal 6/6; already-present no-op 6/6; control degradation 0/6

### stronger
- semantic repair success: 6/6
- full constraint-compliant success: 3/6
- semantic success but URL constraint failed: 3/6
- no repair: 0/6
- decision errors: false not_supported 0, false already_present 0, attempted-with-constraint-failure 3
- sham refusal 6/6; already-present no-op 6/6; control degradation 0/6

## Case determination

- Repairability result supports Case B: the current generator underperforms the stronger generator under oracle guidance.
- Repair capability / semantic discrimination capability under oracle guidance; not an isolated claim about pure model capacity (Mechanism not yet isolated).
- The current generator frequently misclassified genuine gaps as already present (050 x3) or unsupported (039 x2); its single attempted repair also copied the raw URL.
- The stronger generator repaired semantically in all six genuine cells; three of those (039) violated the no-URL output constraint, so full success is three of six.
- Controls: both models refused all sham propositions (12/12) and correctly no-op'ed all already-present propositions (12/12), with zero degradation. The current model's control safety is partly confounded by its blanket refusal tendency; the stronger model shows selective behavior (repairs genuine gaps, refuses sham, recognizes already present).

## Evaluator-validity note

- The secondary judge (deepseek-v4-pro) marked the current model's no-edit 050 outputs as target covered, reproducing the previously observed over-lenient semantic matching behavior; it must not override human-primary repair scoring.
- This replicates the Measurement Validity Audit V2 over-leniency finding inside the Repairability stage; it is not rerun or re-adjudicated here.

## Mechanism candidates (design only; nothing executed)

The candidates below are mutually non-exclusive and are stated as hypotheses to discriminate, not conclusions.

### H1. Semantic gap discrimination (missing vs already present vs unsupported)
- Supporting evidence: the current generator classified human-confirmed missing propositions as `already_present` (3x) and `not_supported` (2x) under oracle guidance, while the stronger generator made no such errors; the same over-lenient semantic matching appears in the V2 adjudicator.
- Not excluded: whether this is a capability gap or an interaction with the repair framing; the current model may represent the proposition but apply the wrong decision rule.
- Minimal discriminating design (no execution now): 3-way proposition-status classification over frozen (answer, proposition, evidence) items spanning missing / already-present / unsupported / contradicted targets, no answer editing, same models, balance and counterbalance proposition order; measure confusion matrix and calibration.

### H2. Instruction / repair-task following and conservative refusal bias
- Supporting evidence: the current model returned no edits in 5/6 genuine cells even when the supporting span was supplied inside the prompt, and its production grounding rules reward refusal/abstention; the stronger model edited cleanly in the same template.
- Not excluded: the same failures could be H1 rather than instruction following; the current model's control refusals are also consistent with a blanket conservative policy.
- Minimal discriminating design (no execution now): hold proposition and evidence fixed, vary only task framing (repair vs judgment-only vs forced 3-way choice vs explicit "the span supports this proposition" assertion), and measure decision shifts; include the sham and already-present items to detect over-correction.

### H3. Proposition-level entailment / comparison capability under long evidence
- Supporting evidence: both failed targets require aligning an atomic proposition inside topically adjacent policy text (pre-filing commitment timing; source-code offer), the same alignment difficulty identified in the Measurement Validity Audit; the stronger model resolved both.
- Not excluded: discrimination (H1) and instruction following (H2) can produce identical outcomes in the current two-item, two-model design; the stronger model's URL copying also shows it is not constraint-perfect.
- Minimal discriminating design (no execution now): claim-level entailment probes on minimal pairs built from the frozen evidence (same answer text with/without the proposition; present vs absent vs unsupported), no generation, no repair; compare error patterns by relation type (temporal precondition, offer, scope/exception).

## Explicit non-actions

- No sufficiency judge, no automatic gap detection, no routing, no production model swap, no Rule 9 2x2, no new generator calls.
- Next step is Mechanism preregistration / experiment design only.

## Integrity

- Raw Oracle Repair V1 results, cache, and blind sheet are unmodified; all frozen Validate-staged inputs were hash-verified during writeback.
