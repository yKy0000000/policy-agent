# Router V1.1 Evidence Diagnostic Report

Post-hoc analysis of frozen Router V1 results; no V1 system was modified or rerun.

## 1. Executive Finding

Mixed, with evidence selection as the proximate harm and retrieval exploration as the ceiling. Decomposition changed the evidence set (required-aspect evidence recall DIRECT 0.875 vs DECOMPOSE 0.787; context precision 0.390 vs 0.450) but its 31 novel chunks rarely added required-aspect support (useful 2, redundant 8, non-required 21). The frozen round-robin merge displaced useful base evidence in 4 queries (['router_003', 'router_010', 'router_011', 'router_016']), for a net utility ledger of 2 gain / 5 loss / 13 equal. Generation is not the primary bottleneck: context utilization is high (DIRECT 0.93, DECOMPOSE 0.96) and only 4 (DIRECT) / 2 (DECOMPOSE) evidence-supported aspects were left unstated.

## 2. Evidence-Level Results

| metric | FIXED_DIRECT | FIXED_DECOMPOSE | ROUTED |
|---|---|---|---|
| evidence required recall | 0.875 (57/66) | 0.787 (52/66) | 0.875 (57/66) |
| evidence complete queries | 15/20 | 11/20 | 15/20 |
| required context precision | 0.390 | 0.450 | 0.410 |
| non-required chunks | 61 | 55 | 59 |
| context utilization | 0.930 | 0.962 | 0.947 |
| answer complete | 12/20 | 9/20 | 13/20 |
| required covered | 54/66 | 51/66 | 55/66 |

## 3. Retrieval Novelty vs Utility

- representation_gain chunks: useful 0, redundant 1, non-required 6.
- selection_ranking_gain chunks: useful 2, redundant 7, non-required 15.

## 4. Evidence Displacement

- queries with useful evidence gained: ['router_001', 'router_019']
- queries with useful evidence lost: ['router_003', 'router_010', 'router_011', 'router_016']
- queries with non-required evidence gained: ['router_001', 'router_002', 'router_003', 'router_004', 'router_005', 'router_006', 'router_007', 'router_008', 'router_010', 'router_013', 'router_014', 'router_015', 'router_016', 'router_017']
- net required-aspect evidence gain: ['router_001', 'router_019']; loss: ['router_003', 'router_008', 'router_010', 'router_011', 'router_016']; equal: ['router_002', 'router_004', 'router_005', 'router_006', 'router_007', 'router_009', 'router_012', 'router_013', 'router_014', 'router_015', 'router_017', 'router_018', 'router_020']

## 5. Generation Utilization

- FIXED_DIRECT: evidence-supported-but-answer-missing aspects 4; answer-without-detected-evidence mentions 1.
- FIXED_DECOMPOSE: evidence-supported-but-answer-missing aspects 2; answer-without-detected-evidence mentions 1.
- ROUTED: evidence-supported-but-answer-missing aspects 3; answer-without-detected-evidence mentions 1.

## 6. Key Cases

### router_001

- taxonomy: DECOMPOSITION_USEFUL_EXPLORATION ['DECOMPOSITION_USEFUL_EXPLORATION', 'GENERATION_LIMITED']
- FIXED_DIRECT: recall 0.750, precision 0.200, utilization 1.0, supported ['router_001_a1', 'router_001_a2', 'router_001_a3'], evidence-supported-but-missing []
- FIXED_DECOMPOSE: recall 1.000, precision 0.600, utilization 0.75, supported ['router_001_a1', 'router_001_a2', 'router_001_a3', 'router_001_a4'], evidence-supported-but-missing ['router_001_a4']
- ROUTED: recall 0.750, precision 0.200, utilization 1.0, supported ['router_001_a1', 'router_001_a2', 'router_001_a3'], evidence-supported-but-missing []
- displacement: useful_gain ['chunk_0ef6386af9657bbfb48bef55'], useful_lost [], non_required_gain ['chunk_0d2d5abd2784cfcf630269b4', 'chunk_65d9607208f5f96afca0d68c'], lost aspects []

### router_009

- taxonomy: STABLE ['STABLE']
- FIXED_DIRECT: recall 1.000, precision 0.800, utilization 1.0, supported ['router_009_a1', 'router_009_a2', 'router_009_a3'], evidence-supported-but-missing []
- FIXED_DECOMPOSE: recall 1.000, precision 0.800, utilization 1.0, supported ['router_009_a1', 'router_009_a2', 'router_009_a3'], evidence-supported-but-missing []
- ROUTED: recall 1.000, precision 0.800, utilization 1.0, supported ['router_009_a1', 'router_009_a2', 'router_009_a3'], evidence-supported-but-missing []
- displacement: useful_gain [], useful_lost [], non_required_gain [], lost aspects []

### router_010

- taxonomy: DECOMPOSITION_DISPLACEMENT ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- FIXED_DIRECT: recall 1.000, precision 0.400, utilization 1.0, supported ['router_010_a1', 'router_010_a2', 'router_010_a3'], evidence-supported-but-missing []
- FIXED_DECOMPOSE: recall 0.333, precision 0.200, utilization 1.0, supported ['router_010_a3'], evidence-supported-but-missing []
- ROUTED: recall 1.000, precision 0.400, utilization 1.0, supported ['router_010_a1', 'router_010_a2', 'router_010_a3'], evidence-supported-but-missing []
- displacement: useful_gain [], useful_lost ['chunk_80d71a13ddfac8eb977f9541'], non_required_gain ['chunk_d47c7ab9c53cc480c3c2c069'], lost aspects ['router_010_a1', 'router_010_a2']

### router_011

- taxonomy: DECOMPOSITION_DISPLACEMENT ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']
- FIXED_DIRECT: recall 1.000, precision 0.600, utilization 0.75, supported ['router_011_a1', 'router_011_a3', 'router_011_a4', 'router_011_a5'], evidence-supported-but-missing ['router_011_a3']
- FIXED_DECOMPOSE: recall 0.750, precision 0.800, utilization 1.0, supported ['router_011_a1', 'router_011_a3', 'router_011_a4'], evidence-supported-but-missing []
- ROUTED: recall 1.000, precision 0.800, utilization 0.75, supported ['router_011_a1', 'router_011_a3', 'router_011_a4', 'router_011_a5'], evidence-supported-but-missing ['router_011_a3']
- displacement: useful_gain [], useful_lost ['chunk_a761f910df2bb1e22f5a4020'], non_required_gain [], lost aspects ['router_011_a5']

### router_012

- taxonomy: DECOMPOSITION_NOISY_EXPLORATION ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']
- FIXED_DIRECT: recall 1.000, precision 0.200, utilization 1.0, supported ['router_012_a1', 'router_012_a2', 'router_012_a3'], evidence-supported-but-missing []
- FIXED_DECOMPOSE: recall 1.000, precision 0.400, utilization 0.6666666666666666, supported ['router_012_a1', 'router_012_a2', 'router_012_a3'], evidence-supported-but-missing ['router_012_a3']
- ROUTED: recall 1.000, precision 0.200, utilization 1.0, supported ['router_012_a1', 'router_012_a2', 'router_012_a3'], evidence-supported-but-missing []
- displacement: useful_gain [], useful_lost [], non_required_gain [], lost aspects []

### router_020

- taxonomy: DECOMPOSITION_NOISY_EXPLORATION ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- FIXED_DIRECT: recall 1.000, precision 0.800, utilization 1.0, supported ['router_020_a1', 'router_020_a2', 'router_020_a3', 'router_020_a5'], evidence-supported-but-missing []
- FIXED_DECOMPOSE: recall 1.000, precision 1.000, utilization 1.0, supported ['router_020_a1', 'router_020_a2', 'router_020_a3', 'router_020_a5'], evidence-supported-but-missing []
- ROUTED: recall 1.000, precision 1.000, utilization 1.0, supported ['router_020_a1', 'router_020_a2', 'router_020_a3', 'router_020_a5'], evidence-supported-but-missing []
- displacement: useful_gain [], useful_lost [], non_required_gain [], lost aspects []

## 7. Mechanism Taxonomy

- DECOMPOSITION_DISPLACEMENT: ['router_003', 'router_008', 'router_010', 'router_011', 'router_016']
- DECOMPOSITION_NOISY_EXPLORATION: ['router_002', 'router_004', 'router_005', 'router_006', 'router_007', 'router_012', 'router_013', 'router_014', 'router_015', 'router_017', 'router_020']
- DECOMPOSITION_USEFUL_EXPLORATION: ['router_001', 'router_019']
- STABLE: ['router_009', 'router_018']

## 8. Implication for Next Experiment

D. MIXED. Two mechanisms dominate: (A) decomposition exploration rarely produced useful new required-aspect evidence (2/31 novel chunks were useful), so the upside is capped; and (B) the frozen round-robin merge displaced useful base evidence in 4 queries, which is the proximate cause of the (net) coverage loss. (C) is not supported: context utilization stays high (0.96), so generation utilization is not the bottleneck.

## 9. EACL Exploration-Exploitation Gate

JUSTIFIED. Utility-aware selection has a concrete, reproduced failure mode to address: the frozen round-robin merge displaced useful base evidence in 4 queries (['router_003', 'router_010', 'router_011', 'router_016']) while the net evidence-utility ledger is 2 gain / 5 loss / 13 equal. It is not STRONGLY_JUSTIFIED because the exploration side rarely produced useful novelty: only 2 of 31 novel chunks supported a required aspect that the base evidence did not already support, so the upstream useful-novelty rate remains the ceiling and better selection alone would mainly prevent losses rather than create gains.

## Appendix: ROUTED decompose cases

- router_009: recall 1.000, precision 0.800, utilization 1.0, supported ['router_009_a1', 'router_009_a2', 'router_009_a3'], novelty {'representation_gain': [], 'selection_ranking_gain': []}
- router_011: recall 1.000, precision 0.800, utilization 0.75, supported ['router_011_a1', 'router_011_a3', 'router_011_a4', 'router_011_a5'], novelty {'representation_gain': [{'chunk_id': 'chunk_3fe67c4153c058347f190445', 'class': 'redundant', 'supported_aspects': ['router_011_a4']}], 'selection_ranking_gain': []}
- router_020: recall 1.000, precision 1.000, utilization 1.0, supported ['router_020_a1', 'router_020_a2', 'router_020_a3', 'router_020_a5'], novelty {'representation_gain': [], 'selection_ranking_gain': [{'chunk_id': 'chunk_76a40eef1f0fee4df26723be', 'class': 'redundant', 'supported_aspects': ['router_020_a5']}]}

