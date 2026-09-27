# Router V2 Selection Study - Failure Review

## Where frozen round-robin fails

- router_003: lost ['router_003_a2']; gained []; 3 exploratory chunks (0 useful)
- router_010: lost ['router_010_a1', 'router_010_a2']; gained []; 1 exploratory chunks (0 useful)
- router_011: lost ['router_011_a5']; gained []; 2 exploratory chunks (0 useful)
- router_016: lost ['router_016_a1', 'router_016_a3']; gained []; 2 exploratory chunks (0 useful)
- router_020: lost []; gained []; 1 exploratory chunks (0 useful)

## Oracle-only aspects and runtime capture

- router_001: ['router_001_a4'] -> best runtime {'policy_id': 'ROUND_ROBIN', 'captured': 1}
- router_007: ['router_007_a1', 'router_007_a2', 'router_007_a4'] -> best runtime {'policy_id': 'EACL_TS_TOPK_DIV::seed20260928', 'captured': 2}
- router_013: ['router_013_a4', 'router_013_a5'] -> best runtime {'policy_id': 'MMR_0.25', 'captured': 2}
- router_014: ['router_014_a3'] -> best runtime {'policy_id': 'DIRECT_TOP5', 'captured': 0}
- router_019: ['router_019_a1', 'router_019_a3'] -> best runtime {'policy_id': 'ROUND_ROBIN', 'captured': 1}

## Why runtime proxies cannot find oracle evidence

Truth-oracle chunks missing from DIRECT top5 sit at global cross-encoder ranks median=15.0, min=7, max=62 over the case super-pools (analysis-only). The frozen MiniLM cross-encoder under the shared rewrite does not rank required-utility evidence at the top, which caps every policy that leans on relevance scores, and the same scores are the bandit reward.

## Bandit instability

- EACL_TS_RESERVE: per-seed supported 54/66, 51/66, 54/66 (spread 3 aspects); displaced [6, 8, 5]
- EACL_TS_TOPK: per-seed supported 47/66, 52/66, 41/66 (spread 11 aspects); displaced [7, 7, 11]
- EACL_TS_TOPK_DIV: per-seed supported 53/66, 55/66, 53/66 (spread 2 aspects); displaced [6, 8, 3]

## Answer-level deltas vs DIRECT (covered aspects, per case)

- router_001: {'ROUND_ROBIN': 1, 'EACL_TS_TOPK_DIV::seed20260927': 1, 'ORACLE_TOP5': 1}
- router_003: {'ROUND_ROBIN': -1, 'MMR_0.25': -1, 'EACL_TS_TOPK_DIV::seed20260927': -3}
- router_007: {'GLOBAL_BASE_RERANK': -1, 'MMR_0.25': -1, 'ORACLE_TOP5': 2}
- router_008: {'ROUND_ROBIN': 1, 'EACL_TS_TOPK_DIV::seed20260927': 2, 'ORACLE_TOP5': 2}
- router_010: {'ROUND_ROBIN': -2}
- router_011: {'EACL_TS_TOPK_DIV::seed20260927': -1, 'ORACLE_TOP5': 1}
- router_012: {'ORACLE_TOP5': 1}
- router_013: {'MMR_0.25': 2, 'ORACLE_TOP5': 2}
- router_014: {'ORACLE_TOP5': 1}
- router_016: {'ROUND_ROBIN': -2, 'EACL_TS_TOPK_DIV::seed20260927': -2}
- router_018: {'MMR_0.25': -1}
- router_019: {'ROUND_ROBIN': 1, 'MMR_0.25': 1, 'EACL_TS_TOPK_DIV::seed20260927': 1, 'ORACLE_TOP5': 2}
- router_020: {'ORACLE_TOP5': 1}

## Diagnosis to keep on record

- primary: UTILITY_ESTIMATION_LIMITED
- secondary: EXPLORATION_LIMITED
- The dominant failure is not 'decomposition retrieved nothing': the pools contain 65/66 truth-coverable aspects. The failure is that no runtime-legal utility signal (frozen reranker score, MMR novelty, bandit reward) can tell required-aspect support from topical similarity at the 5-slot budget.
