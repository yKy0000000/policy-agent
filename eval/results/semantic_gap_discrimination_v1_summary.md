# Semantic Gap Discrimination V1 - Summary (Mechanism / H1)

> Mechanism / H1 mechanism diagnostic: proposition-level semantic state classification on frozen answers and evidence. No repair generation; MISSING n=2, so no population inference.

- status: complete
- preregistration sha256: `eef5b220aa7520e4`
- dataset: {'MISSING': 2, 'ALREADY_PRESENT': 19, 'UNSUPPORTED': 6, 'items': 27}; excluded: ['VAL-001-008-F02']
- design: 162 cells = 27 items x 2 models x 3 replicates; max_tokens 200

## Confusion matrices (modal label; rows = gold, columns = predicted)

### current

| gold \ predicted | MISSING | ALREADY_PRESENT | UNSUPPORTED | excluded inconsistent |
|---|---:|---:|---:|---:|
| MISSING | 1 | 1 | 0 | 0 |
| ALREADY_PRESENT | 1 | 18 | 0 | 0 |
| UNSUPPORTED | 0 | 0 | 6 | 0 |

- per-class recall: MISSING 1/2, ALREADY_PRESENT 18/19, UNSUPPORTED 6/6
- overall accuracy (modal): 0.9259259259259259
- MISSING -> ALREADY_PRESENT: 1; MISSING -> UNSUPPORTED: 0; MISSING unresolved: 0
- consistency (3/3, 2/3, 1/3): {'3/3': 26, '2/3': 1, '1/3': 0}

### stronger

| gold \ predicted | MISSING | ALREADY_PRESENT | UNSUPPORTED | excluded inconsistent |
|---|---:|---:|---:|---:|
| MISSING | 1 | 1 | 0 | 0 |
| ALREADY_PRESENT | 5 | 14 | 0 | 0 |
| UNSUPPORTED | 0 | 0 | 6 | 0 |

- per-class recall: MISSING 1/2, ALREADY_PRESENT 14/19, UNSUPPORTED 6/6
- overall accuracy (modal): 0.7777777777777778
- MISSING -> ALREADY_PRESENT: 1; MISSING -> UNSUPPORTED: 0; MISSING unresolved: 0
- consistency (3/3, 2/3, 1/3): {'3/3': 25, '2/3': 2, '1/3': 0}

## Item-level readout (Repairability-linked items)

| item | model | replicate labels | modal | consistency |
|---|---|---|---|---|
| M-VAL-001-039-F02 | current | MISSING, MISSING, MISSING | MISSING | 3/3 |
| M-VAL-001-050-F01 | current | ALREADY_PRESENT, ALREADY_PRESENT, ALREADY_PRESENT | ALREADY_PRESENT | 3/3 |
| M-VAL-001-039-F02 | stronger | MISSING, MISSING, MISSING | MISSING | 3/3 |
| M-VAL-001-050-F01 | stronger | UNSUPPORTED, ALREADY_PRESENT, ALREADY_PRESENT | ALREADY_PRESENT | 2/3 |

## Strict 3/3-agreement sensitivity

- current: matrix {'MISSING': {'MISSING': 1, 'ALREADY_PRESENT': 1, 'UNSUPPORTED': 0}, 'ALREADY_PRESENT': {'MISSING': 0, 'ALREADY_PRESENT': 18, 'UNSUPPORTED': 0}, 'UNSUPPORTED': {'MISSING': 0, 'ALREADY_PRESENT': 0, 'UNSUPPORTED': 6}}; excluded 1
- stronger: matrix {'MISSING': {'MISSING': 1, 'ALREADY_PRESENT': 0, 'UNSUPPORTED': 0}, 'ALREADY_PRESENT': {'MISSING': 5, 'ALREADY_PRESENT': 13, 'UNSUPPORTED': 0}, 'UNSUPPORTED': {'MISSING': 0, 'ALREADY_PRESENT': 0, 'UNSUPPORTED': 6}}; excluded 2

## Gold-caveat sensitivity (excluding P-VAL-001-050-F05)

- current: MISSING 1/2, ALREADY_PRESENT 17/18, UNSUPPORTED 6/6
- stronger: MISSING 1/2, ALREADY_PRESENT 13/18, UNSUPPORTED 6/6

## Preregistered outcome mapping

- operational mapping: **mixed/unresolved**
- 039-F02 modal: current MISSING / stronger MISSING
- 050-F01 modal: current ALREADY_PRESENT / stronger ALREADY_PRESENT
- MISSING n=2: mechanism diagnostic only; no statistical generalization.

## Failures
- []
