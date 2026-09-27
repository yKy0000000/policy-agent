# Oracle Repair V1 - Human-Primary Summary

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
