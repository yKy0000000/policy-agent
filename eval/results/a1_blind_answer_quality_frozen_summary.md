# Blind A1 answer-quality freeze (Validation V1)

**Frozen blind.** Labels only; no arm/policy identity or telemetry is present. Judge = frozen `broad-v3-answer-quality-v1` over frozen `QUERY_REQUIRED` aspects, adjusted by the 8 blind human resolutions.

## Dataset

- total cases: 50
- total arm-case rows: 250
- unique answers evaluated: 156
- required aspect instances judged: 654

## Frozen required-aspect totals

- covered: 626
- missing: 28
- partial: 0
- incorrect: 0
- answers with QueryRequiredComplete: 138/156

## Driving corrections

- VAL-001-011 VAL-001-011-F01 answer A: covered -> missing
- VAL-001-011 VAL-001-011-F01 answer B: covered -> missing

## Dispute resolution

- resolved disputes: 8/8
- confirmed regressions: 4
- rejected regression candidates: 1
- confirmed improvements: 0
- confirmed grounding/citation issues: 1
- unresolved quality disputes: 0

No economics, no Pareto, no keep/kill decision.

**SHA-256 (`a1_blind_answer_quality_frozen_v1.json`):** `96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35`
