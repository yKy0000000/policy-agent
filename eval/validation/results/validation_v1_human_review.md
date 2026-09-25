# Validation V1 Human Review

Review judge uncertainty, evidence mapping gaps, false stops, and claims with weak support. Frozen files must not be edited based on these results.

## VAL-001-001 — unobserved
- Route: adaptive_prefix_v1; min Top5: 1.344.
- New selection misses: [].
- always_v1: grounded 0/4; missing ['VAL-001-001-F01', 'VAL-001-001-F02', 'VAL-001-001-F03', 'VAL-001-001-F04']; claims {'supported': 12, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 0/4; missing ['VAL-001-001-F01', 'VAL-001-001-F02', 'VAL-001-001-F03', 'VAL-001-001-F04']; claims {'supported': 12, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-002 — false_stop
- Route: fixed_top5; min Top5: 2.713.
- New selection misses: ['VAL-001-002-F01'].
- always_v1: grounded 5/5; missing []; claims {'supported': 15, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 3/5; missing ['VAL-001-002-F01', 'VAL-001-002-F02']; claims {'supported': 22, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-005 — safe_stop
- Route: fixed_top5; min Top5: 4.372.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 11, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 14, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-006 — unobserved
- Route: adaptive_prefix_v1; min Top5: 2.235.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 20, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 20, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-009 — unobserved
- Route: adaptive_prefix_v1; min Top5: -0.555.
- New selection misses: [].
- always_v1: grounded 4/5; missing ['VAL-001-009-F02']; claims {'supported': 9, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 4/5; missing ['VAL-001-009-F02']; claims {'supported': 9, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-010 — unobserved
- Route: adaptive_prefix_v1; min Top5: -2.511.
- New selection misses: [].
- always_v1: grounded 6/6; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 6/6; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-014 — unobserved
- Route: adaptive_prefix_v1; min Top5: -1.030.
- New selection misses: [].
- always_v1: grounded 4/4; missing []; claims {'supported': 6, 'partial': 0, 'unsupported': 1, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 4/4; missing []; claims {'supported': 6, 'partial': 0, 'unsupported': 1, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-018 — unobserved
- Route: adaptive_prefix_v1; min Top5: -4.188.
- New selection misses: [].
- always_v1: grounded 4/4; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 4/4; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-019 — unobserved
- Route: adaptive_prefix_v1; min Top5: -2.088.
- New selection misses: [].
- always_v1: grounded 4/4; missing []; claims {'supported': 5, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 4/4; missing []; claims {'supported': 5, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-020 — safe_stop
- Route: fixed_top5; min Top5: 2.554.
- New selection misses: [].
- always_v1: grounded 4/4; missing []; claims {'supported': 7, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 4/4; missing []; claims {'supported': 7, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-024 — safe_stop
- Route: fixed_top5; min Top5: 2.693.
- New selection misses: [].
- always_v1: grounded 4/4; missing []; claims {'supported': 18, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 4/4; missing []; claims {'supported': 18, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-027 — unobserved
- Route: adaptive_prefix_v1; min Top5: 1.813.
- New selection misses: [].
- always_v1: grounded 0/6; missing ['VAL-001-027-F01', 'VAL-001-027-F02', 'VAL-001-027-F03', 'VAL-001-027-F04', 'VAL-001-027-F05', 'VAL-001-027-F06']; claims {'supported': 6, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 0/6; missing ['VAL-001-027-F01', 'VAL-001-027-F02', 'VAL-001-027-F03', 'VAL-001-027-F04', 'VAL-001-027-F05', 'VAL-001-027-F06']; claims {'supported': 6, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-030 — unobserved
- Route: adaptive_prefix_v1; min Top5: -0.888.
- New selection misses: [].
- always_v1: grounded 0/4; missing ['VAL-001-030-F01', 'VAL-001-030-F02', 'VAL-001-030-F03', 'VAL-001-030-F04']; claims {'supported': 16, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 0/4; missing ['VAL-001-030-F01', 'VAL-001-030-F02', 'VAL-001-030-F03', 'VAL-001-030-F04']; claims {'supported': 16, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-034 — unobserved
- Route: adaptive_prefix_v1; min Top5: 2.143.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 41, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 41, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-038 — unobserved
- Route: adaptive_prefix_v1; min Top5: 1.236.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 10, 'partial': 0, 'unsupported': 1, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 10, 'partial': 0, 'unsupported': 1, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-040 — unobserved
- Route: adaptive_prefix_v1; min Top5: -2.048.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 9, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 9, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-041 — safe_stop
- Route: fixed_top5; min Top5: 4.282.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 8, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-043 — unobserved
- Route: adaptive_prefix_v1; min Top5: 1.696.
- New selection misses: [].
- always_v1: grounded 5/5; missing []; claims {'supported': 6, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 5/5; missing []; claims {'supported': 6, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.

## VAL-001-046 — unobserved
- Route: adaptive_prefix_v1; min Top5: 0.048.
- New selection misses: [].
- always_v1: grounded 0/4; missing ['VAL-001-046-F01', 'VAL-001-046-F02', 'VAL-001-046-F03', 'VAL-001-046-F04']; claims {'supported': 4, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.
- frozen_adaptive: grounded 0/4; missing ['VAL-001-046-F01', 'VAL-001-046-F02', 'VAL-001-046-F03', 'VAL-001-046-F04']; claims {'supported': 4, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 0}.

## VAL-001-048 — unobserved
- Route: adaptive_prefix_v1; min Top5: 1.908.
- New selection misses: [].
- always_v1: grounded 6/6; missing []; claims {'supported': 11, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
- frozen_adaptive: grounded 6/6; missing []; claims {'supported': 11, 'partial': 0, 'unsupported': 0, 'contradicted': 0, 'uncertain': 1}.
