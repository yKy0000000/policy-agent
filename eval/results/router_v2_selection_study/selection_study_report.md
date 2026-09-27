# Router V2 Selection Study Report

**Role: exploratory mechanism study.** The same frozen 20 queries and 66 required aspects are reused to compare many selection policies, so nothing here is an independent confirmatory test. Oracle policies are ANALYSIS_ONLY_ORACLE.

## Executive Summary (Q1-Q5)

- **Q1 candidate-pool upper bound**: judge-verified ORACLE_TOP5 supports **66/66** aspects vs DIRECT 57/66 (+9). Decomposition-specific upside is tiny: ORACLE_TOP5 vs ORACLE_BASE_TOP5 = +1 judge-verified aspect (truth-based 65 vs 63, super-pool 65/66 vs base-union 63/66).
- **Q2 round-robin gap**: ROUND_ROBIN 52/66 sits 14 aspects below ORACLE_TOP5 and 5 below frozen DIRECT, with the highest displacement count of the frozen baselines.
- **Q3 simple selectors**: GLOBAL_BASE_RERANK 55/66 and best simple instance MMR_0.25 56/66 recover only 0.29 of the ROUND_ROBIN-to-oracle gap; no simple selector matches frozen DIRECT.
- **Q4 bandit value**: best bandit instance EACL_TS_TOPK_DIV::seed20260928 = 55/66; bandit minus best simple = -1. Bandit seed variance is large (EACL_TS_RESERVE 51-54/66, EACL_TS_TOPK 41-52/66, EACL_TS_TOPK_DIV 53-55/66). No measured bandit value.
- **Q5 evidence-to-answer transfer**: ORACLE_TOP5 evidence (+9 aspects vs DIRECT, analysis-only) transfers **+13 covered aspects and +9 complete answers** (context utilization 1.00). Generation does not cap the upper bound; evidence selection does.

**Primary diagnosis: UTILITY_ESTIMATION_LIMITED** — Two mechanisms coexist: (1) decomposition-specific exploration upside is immaterial (ORACLE_TOP5 66 vs ORACLE_BASE_TOP5 65, +1 aspect); (2) even within the existing pools the runtime evidence utility proxies leave a large oracle gap (9 aspects vs the base-pool oracle; every runtime selector is at or below frozen DIRECT). Because (2) is the actionable, larger gap, UTILITY_ESTIMATION_LIMITED is primary; the decomposition direction is closed by EXPLORATION_LIMITED as secondary.
**Secondary diagnosis: EXPLORATION_LIMITED.**
**EACL follow-up decision: `IMPROVE_UTILITY_ESTIMATION_FIRST`** — the decomposition/exploration-specific upside is too small to justify the EACL main line, but the measured pool-level oracle gap (mostly inside the base pool) is a utility-estimation problem, not a bandit or allocation problem

## A. Candidate-Pool Upper Bound (truth-based, analysis-only)

- DIRECT required-aspect coverage (truth chunk-ids): 51/66
- ROUND_ROBIN (truth chunk-ids): 46/66
- Base-stream candidate union coverage: 63/66
- Decomposition candidate super-pool coverage: 65/66
- ORACLE_BASE_TOP5 (<=5 chunks from base union): 63/66
- ORACLE_TOP5 (<=5 chunks from super-pool): 65/66
- Decomposition-specific exploration upside (ORACLE_TOP5 - ORACLE_BASE_TOP5): **+1**
- Total possible judge-verified gain over DIRECT: **+9** aspects (ORACLE_TOP5, analysis-only)

## B. Evidence Policy Comparison (blind evidence judge)

Complete/displaced/below-DIRECT denominators are judged cases: 20 for single policies, 60 for the 3-seed pooled bandit rows; recall denominators are aspects (66 / 198).

| policy | recall | complete | precision | useful exploration | base preservation | oracle gap | displaced | below DIRECT |
|---|---|---|---|---|---|---|---|---|
| DIRECT_TOP5 | 57/66 | 15/20 | 0.390 | 0/0 (n/a) | 39/39 (1.00) | 9 | 0/20 | 0/20 |
| ROUND_ROBIN | 52/66 | 11/20 | 0.450 | 2/31 (0.06) | 33/39 (0.85) | 14 | 5/20 | 5/20 |
| GLOBAL_BASE_RERANK | 55/66 | 14/20 | 0.380 | 0/6 (0.00) | 37/39 (0.95) | 11 | 2/20 | 2/20 |
| MMR lambda=0.10 | 51/66 | 10/20 | 0.350 | 0/10 (0.00) | 34/39 (0.87) | 15 | 4/20 | 6/20 |
| MMR lambda=0.25 | 56/66 | 13/20 | 0.370 | 2/18 (0.11) | 34/39 (0.87) | 10 | 4/20 | 4/20 |
| MMR lambda=0.50 | 53/66 | 11/20 | 0.350 | 2/25 (0.08) | 33/39 (0.85) | 13 | 5/20 | 6/20 |
| MMR lambda=0.75 | 50/66 | 9/20 | 0.340 | 2/34 (0.06) | 31/39 (0.79) | 16 | 7/20 | 8/20 |
| EACL_TS_TOPK (3 seeds pooled) | 140/198 | 30/60 | 0.363 | 8/126 (0.06) | 83/117 (0.71) | 58 | 25/60 | 21/60 |
| EACL_TS_TOPK_DIV (3 seeds pooled) | 161/198 | 37/60 | 0.417 | 9/117 (0.08) | 95/117 (0.81) | 37 | 17/60 | 11/60 |
| EACL_TS_RESERVE (3 seeds pooled) | 159/198 | 33/60 | 0.390 | 7/103 (0.07) | 96/117 (0.82) | 39 | 19/60 | 15/60 |
| ORACLE_BASE_TOP5 | 65/66 | 19/20 | 1.000 | 7/12 (0.58) | 31/39 (0.79) | 1 | 7/20 | 0/20 |
| ORACLE_TOP5 | 66/66 | 20/20 | 0.988 | 9/14 (0.64) | 31/39 (0.79) | 0 | 7/20 | 0/20 |

Exploration-exploitation ledger (judge-based, vs frozen DIRECT):

| policy | exploratory selected | useful exploratory | useful base preserved | new aspects gained | old aspects lost | net aspect delta |
|---|---|---|---|---|---|---|
| DIRECT_TOP5 | 0 | 0 | 39/39 | 0 | 0 | +0 |
| ROUND_ROBIN | 31 | 2 | 33/39 | 2 | 7 | -5 |
| GLOBAL_BASE_RERANK | 6 | 0 | 37/39 | 0 | 2 | -2 |
| MMR lambda=0.10 | 10 | 0 | 34/39 | 0 | 6 | -6 |
| MMR lambda=0.25 | 18 | 2 | 34/39 | 3 | 4 | -1 |
| MMR lambda=0.50 | 25 | 2 | 33/39 | 3 | 7 | -4 |
| MMR lambda=0.75 | 34 | 2 | 31/39 | 3 | 10 | -7 |
| EACL_TS_TOPK (3 seeds pooled) | 126 | 8 | 83/117 | 9 | 40 | -31 |
| EACL_TS_TOPK_DIV (3 seeds pooled) | 117 | 9 | 95/117 | 8 | 18 | -10 |
| EACL_TS_RESERVE (3 seeds pooled) | 103 | 7 | 96/117 | 7 | 19 | -12 |
| ORACLE_BASE_TOP5 | 12 | 7 | 31/39 | 8 | 0 | +8 |
| ORACLE_TOP5 | 14 | 9 | 31/39 | 9 | 0 | +9 |

Per-seed bandit detail (no seed cherry-picking; mean and spread):

| bandit instance | supported | recall | complete | precision | displaced | exploration rate | base preservation | oracle gap |
|---|---|---|---|---|---|---|---|---|
| EACL_TS_RESERVE::seed20260927 | 54/66 | 0.818 | 11/20 | 0.400 | 6 | 0.10 | 0.82 | 12 |
| EACL_TS_RESERVE::seed20260928 | 51/66 | 0.773 | 11/20 | 0.370 | 8 | 0.06 | 0.77 | 15 |
| EACL_TS_RESERVE::seed20260929 | 54/66 | 0.818 | 11/20 | 0.400 | 5 | 0.05 | 0.87 | 12 |
| EACL_TS_TOPK::seed20260927 | 47/66 | 0.712 | 11/20 | 0.380 | 7 | 0.08 | 0.74 | 19 |
| EACL_TS_TOPK::seed20260928 | 52/66 | 0.788 | 12/20 | 0.390 | 7 | 0.08 | 0.74 | 14 |
| EACL_TS_TOPK::seed20260929 | 41/66 | 0.621 | 7/20 | 0.320 | 11 | 0.03 | 0.64 | 25 |
| EACL_TS_TOPK_DIV::seed20260927 | 53/66 | 0.803 | 12/20 | 0.400 | 6 | 0.05 | 0.79 | 13 |
| EACL_TS_TOPK_DIV::seed20260928 | 55/66 | 0.833 | 12/20 | 0.430 | 8 | 0.10 | 0.79 | 11 |
| EACL_TS_TOPK_DIV::seed20260929 | 53/66 | 0.803 | 13/20 | 0.420 | 3 | 0.09 | 0.85 | 13 |

## C. Downstream Answer Results

| policy | complete | required covered | eligible | citation valid | context utilization | role |
|---|---|---|---|---|---|---|
| DIRECT_TOP5 | 11/20 | 53/66 | 19 | 20 | 0.912 | runtime |
| ROUND_ROBIN | 9/20 | 51/66 | 14 | 20 | 0.962 | runtime |
| GLOBAL_BASE_RERANK | 11/20 | 52/66 | 17 | 20 | 0.927 | runtime |
| MMR_0.25 | 10/20 | 53/66 | 14 | 20 | 0.929 | runtime |
| EACL_TS_TOPK_DIV::seed20260927 | 11/20 | 51/66 | 15 | 20 | 0.943 | runtime |
| ORACLE_TOP5 | 20/20 | 66/66 | 19 | 20 | 1.000 | ANALYSIS_ONLY_ORACLE |

DIRECT/ROUND_ROBIN answers here are fresh generations under the same frozen generator and judge protocol (V1 replications); small deltas vs frozen V1 numbers are generation/judge replication variance, not policy effects.

## D. Mechanism Diagnosis

- primary: **UTILITY_ESTIMATION_LIMITED**
- secondary: EXPLORATION_LIMITED

Measured signals (aspects out of 66, blind-judged):

- exploration_upside_aspects: 1
- oracle_upside_vs_direct_aspects: 9
- round_robin_oracle_gap_aspects: 14
- best_runtime_any_policy: DIRECT_TOP5 = 57/66
- best_selectable_policy: MMR_0.25 = 56/66, recovery of RR-to-oracle gap 0.29
- best_simple: MMR_0.25 = 56/66, recovery of RR-to-oracle gap 0.29
- best_bandit: EACL_TS_TOPK_DIV::seed20260928 = 55/66
- bandit_gain_vs_simple_aspects: -1
- base_pool_oracle_gap_vs_best_selectable_aspects: 9
- base_pool_oracle_gap_vs_direct_aspects: 8
- base_pool_utility_estimation_limited_signal: True

A. Exploration quality: the decomposition candidate super-pool adds only 1 aspect(s) over the base candidate union (truth-based: +2). Novel chunks (not in base union) are numerous (767 total, 3 supporting) but almost never add required-aspect support.
B. Evidence selection/allocation: frozen ROUND_ROBIN repeats the V1.1 pattern (31 exploratory chunks, 2 useful = 6.5%); every runtime policy including the bandit family keeps a 0.29 or lower recovery of the ROUND_ROBIN-to-ORACLE gap and none beats frozen DIRECT.
C. Utility estimation: ORACLE_TOP5 is perfect (66/66) but runtime proxies cannot find the same chunks; even the base-pool-only oracle (ORACLE_BASE_TOP5 65/66, precision 1.0) is 9 aspects above the best runtime selector.

## E. Bandit Value

Compared with GLOBAL_BASE_RERANK (55/66) and best simple instance MMR_0.25 (56/66), the best bandit instance EACL_TS_TOPK_DIV::seed20260928 scores 55/66. Across seeds: EACL_TS_RESERVE 51-54/66, EACL_TS_TOPK 41-52/66, EACL_TS_TOPK_DIV 53-55/66; the spread is comparable to the total bandit 'signal'. Exploration efficiency stays in the 2.6-10% band already visible in V1 (6.5%), and base preservation is not improved relative to GLOBAL_BASE_RERANK. Conclusion: exploration-exploitation framing describes the allocation problem, but full bandit complexity adds no measurable value at this scale (3 subqueries, 5-slot budget, noisy continuous reward proxy).

## F. Main Cases

- router_001: oracle-only aspects vs DIRECT ['router_001_a4']; best runtime capture {'policy_id': 'ROUND_ROBIN', 'captured': 1}
- router_007: oracle-only aspects vs DIRECT ['router_007_a1', 'router_007_a2', 'router_007_a4']; best runtime capture {'policy_id': 'EACL_TS_TOPK_DIV::seed20260928', 'captured': 2}
- router_013: oracle-only aspects vs DIRECT ['router_013_a4', 'router_013_a5']; best runtime capture {'policy_id': 'MMR_0.25', 'captured': 2}
- router_014: oracle-only aspects vs DIRECT ['router_014_a3']; best runtime capture {'policy_id': 'DIRECT_TOP5', 'captured': 0}
- router_019: oracle-only aspects vs DIRECT ['router_019_a1', 'router_019_a3']; best runtime capture {'policy_id': 'ROUND_ROBIN', 'captured': 1}

ROUND_ROBIN displacement cases:
- router_003: lost ['router_003_a2'], gained [], exploratory 3 (useful 0)
- router_010: lost ['router_010_a1', 'router_010_a2'], gained [], exploratory 1 (useful 0)
- router_011: lost ['router_011_a5'], gained [], exploratory 2 (useful 0)
- router_016: lost ['router_016_a1', 'router_016_a3'], gained [], exploratory 2 (useful 0)
- router_020: lost [], gained [], exploratory 1 (useful 0)

## G. EACL Transferability (Petcu et al., EACL 2026)

Paper mechanism: subqueries as bandit arms; one document observed per pull down each arm's ranked list; Thompson Sampling with Beta posteriors; utilities from relevance judgments or rank scores; top-k rank-aware Bernoulli rewards; cosine novelty term and small UCB exploration bonus; fixed document budget; hierarchical correlated arms.

**What transferred**: the arm-per-subquery abstraction maps cleanly onto our frozen streams; rank-derived continuous relevance rewards (no human labels at runtime) work as a runtime-legal utility proxy; top-k window rewards, the cosine novelty penalty and the budget framing are all implementable on precomputed ranked lists with zero extra model calls.

**What did not transfer**: at 3 subqueries + base and a 5-slot evidence budget, the exploration-exploitation trade-off is nearly degenerate (5 pulls over 4 arms); the paper's 35% precision gains come from large budgets (10-30% of hundreds of documents) where allocation actually matters. Our oracle shows the pool's required-aspect upside is concentrated in the base pool, so subquery-arm allocation cannot be the main lever. Binary-relevance Bernoulli rewards in the paper come from human/LLM-judged relevance; we substituted normalized cross-encoder scores, which V1.1 already showed are a weak required-utility proxy. Also, the paper's final document set is the union of observed documents, while our answer needs a strict Top-5, making displacement risk higher.

**Faithfulness statement**: this study is *inspired/adapted*, not a faithful reproduction. Deviations: 3 subqueries instead of ~16; chunk-level evidence instead of documents; frozen strong base retrieval kept as an additional arm (paper has no base); continuous normalized CE reward instead of binary labels; fixed small c for the UCB term (paper drives c->0); cross-stream duplicate suppression for the 5-slot budget; 3 seeds instead of 1000 repeats. Hierarchical correlated bandits were not applicable (no hierarchy exists in Router V1).

## H. Next Direction

**Primary recommendation: `IMPROVE_UTILITY_ESTIMATION_FIRST`**

the decomposition/exploration-specific upside is too small to justify the EACL main line, but the measured pool-level oracle gap (mostly inside the base pool) is a utility-estimation problem, not a bandit or allocation problem

Explicit decomposition verdict: `DECOMPOSITION_UPSIDE_TOO_SMALL` — the EACL-style decomposition/bandit line should not become the next main line. The measured opportunity is utility estimation for evidence selection from already-retrieved pools (oracle +9 facts over DIRECT, mostly inside the base pool, unreachable by frozen reranker scores, MMR novelty, or bandit rewards).

## I. Files

- eval/results/router_v2_selection_study/selection_study_config.json
- eval/results/router_v2_selection_study/candidate_pool_analysis.json
- eval/results/router_v2_selection_study/oracle_upper_bound.json
- eval/results/router_v2_selection_study/policy_selections.json
- eval/results/router_v2_selection_study/evidence_policy_results.json
- eval/results/router_v2_selection_study/generation_results.json
- eval/results/router_v2_selection_study/answer_eval.json
- eval/results/router_v2_selection_study/selection_study_analysis.json
- eval/results/router_v2_selection_study/selection_study_report.md
- eval/results/router_v2_selection_study/selection_study_failure_review.md
- eval/run_router_v2_preregister.py
- eval/run_router_v2_selection_study.py
- eval/run_router_v2_generation.py
- eval/run_router_v2_analysis.py
- eval/router_v2_study_lib.py

## Cost and Reproducibility

- local reranker replay: 80 calls, 3364 pairs, 222.8s (CPU, deterministic)
- evidence judge: 360 calls (244 new, 116 reused from V1.1 cache), 475922 input / 21864 output tokens
- generation: 102 provider calls, 167838 input / 31267 output tokens (512-token answers, frozen prompt)
- answer judge: 20 calls, 238496 input / 78575 output tokens
- no decomposer, router, or retrieval API call was made; candidate pools, rewrites and subqueries are frozen V1 artifacts

## Limitations

- 20-query, 66-aspect exploratory comparison; per-policy deltas of 1-2 aspects are within judge/selection noise and are not confirmatory.
- The frozen truth marks verified supporting chunks, not an exhaustive gold set; truth-based oracle bounds are lower bounds (judge-based oracle numbers are reported for comparability).
- The blind evidence judge is a single LLM judge (deepseek-v4-flash) with the frozen V1.1 prompt; its aspect-support decisions inherit that protocol's limitations, including combination-dependent support across different evidence sets (router_008-style boundary cases).
- DIRECT/ROUND_ROBIN answers were regenerated (same frozen generator settings), so their downstream numbers are replications of V1, not the frozen V1 outputs.
- Bandit results use 3 predeclared seeds; seed spread is reported, but a 1000-run average as in the paper is out of scope at this budget.
