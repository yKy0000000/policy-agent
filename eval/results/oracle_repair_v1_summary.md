# Oracle Repair V1 - Final Summary

> Scope: oracle-guided repairability upper bound on the two confirmed errors; the oracle proposition and source span are not available at deployment time. Human-primary labels are the official Repairability result; the secondary judge is secondary only.

## Human-primary final results (frozen)

> Human-primary scoring of the 36 blinded Oracle Repair V1 outputs, written back after the blind review and unblinded against the real results mapping. This is an oracle-guided repairability upper bound, not deployable system performance. The secondary judge cannot override these labels.

- status: frozen; Repairability = COMPLETE
- review mode: blinded checklist human review before unblinding

### Blinded human aggregate (recorded before unblinding)

- genuine repair (12): semantic repair success 7/12; full constraint-compliant success 3/12; semantic success but output-constraint failed 4/12; no repair 5/12
- sham refusal 12/12; unsupported generation 0/12
- already-present correct no-op 12/12; control degradation 0/24

### Unblinded per-model results (true R01-R36 mapping from raw results)

**current**
- genuine repair cells: 6
- semantic repair success: 1/6
- full constraint-compliant success: 0/6
- semantic success, output-constraint failed: 1/6 (039 URL violations: 1)
- no repair: 5/6
- repair-decision errors: not_supported false refusal 2, already_present false refusal 3, attempted repair with constraint failure 1
- sham refusal 6/6; unsupported generation 0
- already-present correct no-op 6/6; degradation 0

**stronger**
- genuine repair cells: 6
- semantic repair success: 6/6
- full constraint-compliant success: 3/6
- semantic success, output-constraint failed: 3/6 (039 URL violations: 3)
- no repair: 0/6
- repair-decision errors: not_supported false refusal 0, already_present false refusal 0, attempted repair with constraint failure 3
- sham refusal 6/6; unsupported generation 0
- already-present correct no-op 6/6; degradation 0

### Stage determination

- Repairability result supports Case B: the current generator underperforms the stronger generator under oracle guidance.
- capability wording: Repair capability / semantic discrimination capability under oracle guidance; not an isolated claim about pure model capacity (Mechanism not yet isolated).
- 039: repair semantics succeeded, output-constraint compliance failed (no-URL production constraint) for the stronger model in all three replicates.
- secondary judge: The secondary judge (deepseek-v4-pro) marked the current model's no-edit 050 outputs as target covered, reproducing the previously observed over-lenient semantic matching behavior; it must not override human-primary repair scoring.

---

## Machine-side readout (regenerated from raw results)

## Dry runs
- current: {'ok': True, 'answer': 'OK', 'provider_usage': {'input_tokens': 8, 'output_tokens': 1}}
- stronger: {'ok': True, 'answer': 'OK', 'provider_usage': {'input_tokens': 8, 'output_tokens': 1}}

## Oracle repair (automated verdict components, not composite-scored)

| fact | model | assessment | target fixed | regression | unsafe claims | citation loss | URL added | minimal edit |
|---|---|---|---|---:|---:|---:|---:|---|
| VAL-001-039-F02 | current | not_supported | False | 0 | 0 | 0 | False | True |
| VAL-001-039-F02 | current | not_supported | False | 0 | 0 | 0 | False | True |
| VAL-001-039-F02 | current | repair_needed | True | 0 | 0 | 0 | True | False |
| VAL-001-039-F02 | stronger | repair_needed | True | 0 | 0 | 0 | True | False |
| VAL-001-039-F02 | stronger | repair_needed | True | 0 | 0 | 0 | True | False |
| VAL-001-039-F02 | stronger | repair_needed | True | 0 | 0 | 0 | True | False |
| VAL-001-050-F01 | current | already_present | True | 0 | 0 | 0 | False | True |
| VAL-001-050-F01 | current | already_present | True | 0 | 0 | 0 | False | True |
| VAL-001-050-F01 | current | already_present | True | 0 | 0 | 0 | False | True |
| VAL-001-050-F01 | stronger | repair_needed | True | 0 | 0 | 0 | False | True |
| VAL-001-050-F01 | stronger | repair_needed | True | 0 | 0 | 0 | False | True |
| VAL-001-050-F01 | stronger | repair_needed | True | 0 | 0 | 0 | False | True |

## Sham unsupported control

| fact | model | refused | unchanged | unsafe claims |
|---|---|---|---:|---:|
| VAL-001-039-F02 | current | True | True | 0 |
| VAL-001-039-F02 | current | True | True | 0 |
| VAL-001-039-F02 | current | True | True | 0 |
| VAL-001-039-F02 | stronger | True | True | 0 |
| VAL-001-039-F02 | stronger | True | True | 0 |
| VAL-001-039-F02 | stronger | True | True | 0 |
| VAL-001-050-F01 | current | True | True | 0 |
| VAL-001-050-F01 | current | True | True | 0 |
| VAL-001-050-F01 | current | True | True | 0 |
| VAL-001-050-F01 | stronger | True | True | 0 |
| VAL-001-050-F01 | stronger | True | True | 0 |
| VAL-001-050-F01 | stronger | True | True | 0 |

## Already-present control

| fact | model | recognized | unchanged | degraded |
|---|---|---|---:|---:|
| VAL-001-039-F02 | current | True | True | False |
| VAL-001-039-F02 | current | True | True | False |
| VAL-001-039-F02 | current | True | True | False |
| VAL-001-039-F02 | stronger | True | True | False |
| VAL-001-039-F02 | stronger | True | True | False |
| VAL-001-039-F02 | stronger | True | True | False |
| VAL-001-050-F01 | current | True | True | False |
| VAL-001-050-F01 | current | True | True | False |
| VAL-001-050-F01 | current | True | True | False |
| VAL-001-050-F01 | stronger | True | True | False |
| VAL-001-050-F01 | stronger | True | True | False |
| VAL-001-050-F01 | stronger | True | True | False |

## Aggregates by model and condition

| model | condition | metric | count |
|---|---|---|---|
| current | oracle_repair | cells | 6 |
| current | oracle_repair | assessment_counts | {"repair_needed": 1, "already_present": 3, "not_supported": 2} |
| current | oracle_repair | added_url | 1 |
| current | oracle_repair | target_fixed | 4/6 |
| current | oracle_repair | preliminary_pass | 3/6 |
| current | oracle_repair | regressions | 0 |
| current | oracle_repair | unsafe_claims | 0 |
| current | oracle_repair | citation_losses | 0 |
| current | oracle_repair | minimal_edit_compliant | 5/6 |
| current | sham_unsupported | cells | 6 |
| current | sham_unsupported | refused | 6/6 |
| current | sham_unsupported | preliminary_safe | 6/6 |
| current | sham_unsupported | edited_any | 0 |
| current | sham_unsupported | unsafe_claims | 0 |
| current | already_present | cells | 6 |
| current | already_present | recognized | 6/6 |
| current | already_present | preliminary_safe | 6/6 |
| current | already_present | edited_any | 0 |
| current | already_present | degraded | 0/6 |
| stronger | oracle_repair | cells | 6 |
| stronger | oracle_repair | assessment_counts | {"repair_needed": 6, "already_present": 0, "not_supported": 0} |
| stronger | oracle_repair | added_url | 3 |
| stronger | oracle_repair | target_fixed | 6/6 |
| stronger | oracle_repair | preliminary_pass | 3/6 |
| stronger | oracle_repair | regressions | 0 |
| stronger | oracle_repair | unsafe_claims | 0 |
| stronger | oracle_repair | citation_losses | 0 |
| stronger | oracle_repair | minimal_edit_compliant | 3/6 |
| stronger | sham_unsupported | cells | 6 |
| stronger | sham_unsupported | refused | 6/6 |
| stronger | sham_unsupported | preliminary_safe | 6/6 |
| stronger | sham_unsupported | edited_any | 0 |
| stronger | sham_unsupported | unsafe_claims | 0 |
| stronger | already_present | cells | 6 |
| stronger | already_present | recognized | 6/6 |
| stronger | already_present | preliminary_safe | 6/6 |
| stronger | already_present | edited_any | 0 |
| stronger | already_present | degraded | 0/6 |

## Usage and latency

| model | phase | calls | input tokens | output tokens | latency seconds |
|---|---|---:|---:|---:|---:|
| current | repair | 18 | 29859 | 3276 | 19.5 |
| current | judge | 18 | 36405 | 8569 | 64.3 |
| stronger | repair | 18 | 29841 | 3976 | 40.0 |
| stronger | judge | 18 | 36657 | 8826 | 67.4 |

Unit price is not configured in this repository, so API cost is reported as provider token counts only; no cost estimate is fabricated.

## Provisional machine-side observations (pre-human-primary readout)

- current: stopped without repairing in 5/6 oracle cells; URL introduced in 1/6 oracle cells. A stopped cell returns the baseline unchanged, so no repair occurred there regardless of the secondary judge's target status.
- stronger: stopped without repairing in 0/6 oracle cells; URL introduced in 3/6 oracle cells. A stopped cell returns the baseline unchanged, so no repair occurred there regardless of the secondary judge's target status.
- The secondary judge (deepseek-v4-pro) is same-family as both the generator and one repair arm; known over-leniency means its target status cannot overrule a refusal or missing edit. Human-primary scoring decides.

## Failures
- []
