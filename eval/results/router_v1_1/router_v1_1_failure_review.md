# Router V1.1 Failure Mechanism Review

## DECOMPOSITION_DISPLACEMENT

- router_003: tags ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_008: tags ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']
- router_010: tags ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_011: tags ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']
- router_016: tags ['DECOMPOSITION_DISPLACEMENT', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']

## DECOMPOSITION_NOISY_EXPLORATION

- router_002: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_004: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_005: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_006: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_007: tags ['RETRIEVAL_LIMITED', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_012: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST', 'GENERATION_LIMITED']
- router_013: tags ['RETRIEVAL_LIMITED', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_014: tags ['RETRIEVAL_LIMITED', 'DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_015: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_017: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']
- router_020: tags ['DECOMPOSITION_NOISY_EXPLORATION', 'ZERO_GAIN_COST']

## DECOMPOSITION_USEFUL_EXPLORATION

- router_001: tags ['DECOMPOSITION_USEFUL_EXPLORATION', 'GENERATION_LIMITED']
- router_019: tags ['RETRIEVAL_LIMITED', 'DECOMPOSITION_USEFUL_EXPLORATION']

## STABLE

- router_009: tags ['STABLE']
- router_018: tags ['STABLE']

## Displacement detail

- router_003: useful_gain [], useful_lost [{'chunk_id': 'chunk_23acf65f48bfbc0fd2b142a9', 'lost_aspects': ['router_003_a2']}], gained chunks ['chunk_aa63f943bce73a501994f897', 'chunk_85867a0b6a0b9d17cba279d7', 'chunk_a3593c3652416f4582a78c12'], lost chunks ['chunk_648a4d2bbb17b6b1207a8f13', 'chunk_0c3995fedc5f327566f40bfe', 'chunk_23acf65f48bfbc0fd2b142a9'], lost aspects ['router_003_a2']
- router_008: useful_gain [], useful_lost [], gained chunks ['chunk_c05a222b5013b1f82b468408', 'chunk_d3da9ce046c8ea901e71a245'], lost chunks ['chunk_d37c28ee1a7e663c3e069148', 'chunk_d6d1c627931350dcab91a60d'], lost aspects ['router_008_a2']
- router_010: useful_gain [], useful_lost [{'chunk_id': 'chunk_80d71a13ddfac8eb977f9541', 'lost_aspects': ['router_010_a1', 'router_010_a2']}], gained chunks ['chunk_d47c7ab9c53cc480c3c2c069'], lost chunks ['chunk_80d71a13ddfac8eb977f9541'], lost aspects ['router_010_a1', 'router_010_a2']
- router_011: useful_gain [], useful_lost [{'chunk_id': 'chunk_a761f910df2bb1e22f5a4020', 'lost_aspects': ['router_011_a5']}], gained chunks ['chunk_3fe67c4153c058347f190445', 'chunk_0cc6709199187f11f4436f08'], lost chunks ['chunk_a761f910df2bb1e22f5a4020', 'chunk_8f7ea30ed2b0f19beac07dfc'], lost aspects ['router_011_a5']
- router_016: useful_gain [], useful_lost [{'chunk_id': 'chunk_53cfaee79a6c3b7ee9eed1d1', 'lost_aspects': ['router_016_a1', 'router_016_a3']}], gained chunks ['chunk_93b24002aa9b46b386d2061c', 'chunk_87071e099cc59566a1079a0f'], lost chunks ['chunk_53cfaee79a6c3b7ee9eed1d1', 'chunk_621bbabad1d6f0cff7038c2c'], lost aspects ['router_016_a1', 'router_016_a3']

## Answer-without-detected-evidence (manual review)

- router_007 FIXED_DIRECT: ['router_007_a1']
- router_007 FIXED_DECOMPOSE: ['router_007_a1']
- router_007 ROUTED: ['router_007_a1']

