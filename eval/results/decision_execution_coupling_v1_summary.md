# Decision-Execution Coupling V1 - Summary (Mechanism / H3)

> Mechanism / H3 diagnostic: externally injected action decisions with execution. Decision adherence is deterministic and primary; semantic correctness is secondary (same-family judge + blinded human sheet). MISSING n=2; no population inference.

- status: complete
- preregistration sha256: `6f6736b6f01ac23b`
- primary items: ['M-VAL-001-039-F02', 'M-VAL-001-050-F01']; controls: ['P-VAL-001-050-F02', 'U-039-01']
- design: 72 cells = 4 items x 2 models x 3 decisions x 3 replicates

## current

| injected decision | adherence | overrides | actual repair | secondary target correct |
|---|---:|---:|---:|---:|
| D1 | 6/6 | 0/6 | 6/6 | 6/6 |
| D2 | 6/6 | 0/6 | 0/6 | 0/0 |
| D3 | 6/6 | 0/6 | 0/6 | 0/0 |

- rates: {'d1_repair_rate': 1.0, 'd23_noop_rate': 1.0, 'override_rate': 0.0}
- OA (strong coupling): True; OB (weak coupling): False
- controls: {'already_present_D1_unnecessary_repairs': 0, 'already_present_D1_cells': 3, 'unsupported_D1_insertions': 0, 'unsupported_D1_cells': 3, 'already_present_adherence': {'D1': 0, 'D2': 3, 'D3': 3}, 'unsupported_adherence': {'D1': 0, 'D2': 3, 'D3': 3}}

### Per-item decision labels (status:edit/noop)

- D1: {"M-VAL-001-039-F02": {"labels": ["REPAIRED:edit", "REPAIRED:edit", "REPAIRED:edit"], "adherence": 3, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["REPAIRED:edit", "REPAIRED:edit", "REPAIRED:edit"], "adherence": 3, "overrides": 0}}
- D2: {"M-VAL-001-039-F02": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}}
- D3: {"M-VAL-001-039-F02": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}}

## stronger

| injected decision | adherence | overrides | actual repair | secondary target correct |
|---|---:|---:|---:|---:|
| D1 | 6/6 | 0/6 | 6/6 | 6/6 |
| D2 | 5/5 | 0/5 | 0/5 | 0/0 |
| D3 | 6/6 | 0/6 | 0/6 | 0/0 |

- rates: {'d1_repair_rate': 1.0, 'd23_noop_rate': 0.9166666666666666, 'override_rate': 0.0}
- OA (strong coupling): True; OB (weak coupling): False
- controls: {'already_present_D1_unnecessary_repairs': 1, 'already_present_D1_cells': 3, 'unsupported_D1_insertions': 3, 'unsupported_D1_cells': 3, 'already_present_adherence': {'D1': 1, 'D2': 3, 'D3': 3}, 'unsupported_adherence': {'D1': 3, 'D2': 3, 'D3': 3}}

### Per-item decision labels (status:edit/noop)

- D1: {"M-VAL-001-039-F02": {"labels": ["REPAIRED:edit", "REPAIRED:edit", "REPAIRED:edit"], "adherence": 3, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["REPAIRED:edit", "REPAIRED:edit", "REPAIRED:edit"], "adherence": 3, "overrides": 0}}
- D2: {"M-VAL-001-039-F02": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 2, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}}
- D3: {"M-VAL-001-039-F02": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}, "M-VAL-001-050-F01": {"labels": ["NO_CHANGE:noop", "NO_CHANGE:noop", "NO_CHANGE:noop"], "adherence": 3, "overrides": 0}}

## Preregistered outcome mapping

- OC model split: False
- OD controllable but safety-critical: False
- overall: **A**

## Failures
- [{'kind': 'execution', 'cell_id': 'M-VAL-001-039-F02::stronger::D2::r1', 'error': 'LLMClientError: LLM API request failed: The read operation timed out'}]
