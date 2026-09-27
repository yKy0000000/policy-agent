# Task-Conditioned Action V1 - Summary (Mechanism / H2)

> Mechanism / H2 diagnostic: action decision without generation under three framings (A frozen classification, B neutral action decision, C repair intent without editing). No patch, revised answer, citation, or URL is produced. MISSING n=2; no population inference.

- status: complete
- preregistration sha256: `7527b283bda3dfe6`
- dataset: reused H1 27-item probe ({'MISSING': 2, 'ALREADY_PRESENT': 19, 'UNSUPPORTED': 6, 'items': 27})
- design: 324 new cells = 27 items x 2 models x 2 frames (B, C) x 3 replicates; Frame A frozen

## current

### A -> B (canonical action states)

| from \ to | REPAIR | NO_CHANGE_PRESENT | NO_CHANGE_UNSUPPORTED | UNRESOLVED |
|---|---:|---:|---:|---:|
| REPAIR | 0 | 0 | 2 | 0 |
| NO_CHANGE_PRESENT | 0 | 18 | 1 | 0 |
| NO_CHANGE_UNSUPPORTED | 0 | 0 | 6 | 0 |
| UNRESOLVED | 0 | 0 | 0 | 0 |

### A -> C (canonical action states)

| from \ to | REPAIR | NO_CHANGE_PRESENT | NO_CHANGE_UNSUPPORTED | UNRESOLVED |
|---|---:|---:|---:|---:|
| REPAIR | 2 | 0 | 0 | 0 |
| NO_CHANGE_PRESENT | 0 | 18 | 1 | 0 |
| NO_CHANGE_UNSUPPORTED | 0 | 0 | 6 | 0 |
| UNRESOLVED | 0 | 0 | 0 | 0 |

### Frame consistency (A/B/C canonical states)

- {'consistent': 24, 'two_states': 3, 'three_states': 0}

- Frame A gold-action recall: REPAIR 1/2, NO_CHANGE_PRESENT 18/19, NO_CHANGE_UNSUPPORTED 6/6
- Frame B gold-action recall: REPAIR 0/2, NO_CHANGE_PRESENT 17/19, NO_CHANGE_UNSUPPORTED 6/6
- Frame C gold-action recall: REPAIR 1/2, NO_CHANGE_PRESENT 17/19, NO_CHANGE_UNSUPPORTED 6/6

### Replicate consistency (3/3, 2/3, 1/3)

- {'A': {'3/3': 26, '2/3': 1, '1/3': 0}, 'B': {'3/3': 27, '2/3': 0, '1/3': 0}, 'C': {'3/3': 25, '2/3': 2, '1/3': 0}}

### Key cases

- M-VAL-001-039-F02: A=MISSING/MISSING/MISSING -> REPAIR; B=NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED -> NO_CHANGE_UNSUPPORTED; C=WOULD_REPAIR/WOULD_REPAIR/WOULD_REPAIR -> REPAIR
- M-VAL-001-050-F01: A=ALREADY_PRESENT/ALREADY_PRESENT/ALREADY_PRESENT -> NO_CHANGE_PRESENT; B=NO_CHANGE_ALREADY_PRESENT/NO_CHANGE_ALREADY_PRESENT/NO_CHANGE_ALREADY_PRESENT -> NO_CHANGE_PRESENT; C=WOULD_NOT_REPAIR_ALREADY_PRESENT/WOULD_NOT_REPAIR_ALREADY_PRESENT/WOULD_REPAIR -> NO_CHANGE_PRESENT

## stronger

### A -> B (canonical action states)

| from \ to | REPAIR | NO_CHANGE_PRESENT | NO_CHANGE_UNSUPPORTED | UNRESOLVED |
|---|---:|---:|---:|---:|
| REPAIR | 0 | 4 | 2 | 0 |
| NO_CHANGE_PRESENT | 0 | 14 | 1 | 0 |
| NO_CHANGE_UNSUPPORTED | 0 | 0 | 6 | 0 |
| UNRESOLVED | 0 | 0 | 0 | 0 |

### A -> C (canonical action states)

| from \ to | REPAIR | NO_CHANGE_PRESENT | NO_CHANGE_UNSUPPORTED | UNRESOLVED |
|---|---:|---:|---:|---:|
| REPAIR | 1 | 3 | 2 | 0 |
| NO_CHANGE_PRESENT | 0 | 14 | 1 | 0 |
| NO_CHANGE_UNSUPPORTED | 0 | 0 | 6 | 0 |
| UNRESOLVED | 0 | 0 | 0 | 0 |

### Frame consistency (A/B/C canonical states)

- {'consistent': 20, 'two_states': 7, 'three_states': 0}

- Frame A gold-action recall: REPAIR 1/2, NO_CHANGE_PRESENT 14/19, NO_CHANGE_UNSUPPORTED 6/6
- Frame B gold-action recall: REPAIR 0/2, NO_CHANGE_PRESENT 18/19, NO_CHANGE_UNSUPPORTED 6/6
- Frame C gold-action recall: REPAIR 0/2, NO_CHANGE_PRESENT 17/19, NO_CHANGE_UNSUPPORTED 6/6

### Replicate consistency (3/3, 2/3, 1/3)

- {'A': {'3/3': 25, '2/3': 2, '1/3': 0}, 'B': {'3/3': 26, '2/3': 1, '1/3': 0}, 'C': {'3/3': 27, '2/3': 0, '1/3': 0}}

### Key cases

- M-VAL-001-039-F02: A=MISSING/MISSING/MISSING -> REPAIR; B=NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED -> NO_CHANGE_UNSUPPORTED; C=WOULD_NOT_REPAIR_UNSUPPORTED/WOULD_NOT_REPAIR_UNSUPPORTED/WOULD_NOT_REPAIR_UNSUPPORTED -> NO_CHANGE_UNSUPPORTED
- M-VAL-001-050-F01: A=UNSUPPORTED/ALREADY_PRESENT/ALREADY_PRESENT -> NO_CHANGE_PRESENT; B=NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED/NO_CHANGE_UNSUPPORTED -> NO_CHANGE_UNSUPPORTED; C=WOULD_NOT_REPAIR_UNSUPPORTED/WOULD_NOT_REPAIR_UNSUPPORTED/WOULD_NOT_REPAIR_UNSUPPORTED -> NO_CHANGE_UNSUPPORTED

## Preregistered outcome rules

- OA current framing shift: True (['M-VAL-001-039-F02'])
- OB action correct but generation failed: False
- OC stronger framing shift: False
- OD unstable: False
- overall mapping: **A**

## Failures
- []
