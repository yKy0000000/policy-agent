# 70-Query Multi-Arm Comparative Snapshot

**Exploratory comparative snapshot, not a new confirmatory experiment and not an independent holdout.**

Validation V1 (50 queries) and Router V1 (20 queries) were constructed separately for different purposes; their union is a reporting view only and does not support a generalization-accuracy claim.

## Reproducibility

- Run (UTC): 2026-09-27T17:50:35Z
- Run mode: `reuse-existing (frozen historical cells reused; inventory gaps executed)`
- Generation/judge model: `deepseek-v4-flash`; judge protocol: frozen `broad-v3-answer-quality-v1`; temperature 0.
- Rerankers: current-path cells use `cross-encoder/ms-marco-MiniLM-L-6-v2`; reused Validation V1 A1 cells use `BAAI/bge-reranker-base` (frozen research stack).
- Corpus: 57 GitHub site-policy documents; Validation V1 corpus sha256 `cfc24f11467fdc40...`; Router V1 corpus commit `b9578b546d2506fe...`
- Benchmarks: Validation V1 (50 cases / 208 required aspects; queries sha256 `1fb2b03d752343ea...`), Router V1 (20 cases / 66 required aspects; benchmark sha256 `a345ccfd8dabaded...`).
- Script: `eval/results/multiarm_70/run_multiarm_70.py` (multiarm-70-snapshot-v1); git HEAD `98cb503` (working tree dirty).
- Reused vs newly run: 210 of 280 cells reused from frozen historical artifacts; 70 supplemental cells loaded from the workdir cell cache (executed earlier with the frozen arm semantics); 0 cells executed in this invocation.

## 1. Scope

- **Cohort A - Validation V1:** 50 frozen queries, 208 human-adjudicated `QUERY_REQUIRED` aspects. Development/research benchmark (already exposed); no longer a fresh holdout.
- **Cohort B - Router V1 benchmark:** 20 frozen queries, 66 required aspects (frozen before Router V1 outputs).
- **Combined 70:** cohort views are always reported separately; combined numbers are simple sums over the two cohorts, not an accuracy estimate.
- Required-aspect semantics are compatible at the level used here: both truth sets define independent information units whose absence makes an answer incomplete (Validation aspects are human-adjudicated; Router aspects are model-audited). The combined denominator 208 + 66 = 274 is reported with that caveat.

## 2. Arm Definitions

| Arm | Semantics | Validation 50 implementation | Router 20 implementation |
|---|---|---|---|
| FAST | contextual rewrite -> Direct retrieval -> fixed Top5 -> grounded generation -> citation validation | reused frozen A1 `fixed_top5` (BGE research stack) | reused frozen `FIXED_DIRECT` |
| SEARCH+ | shared rewrite -> requirement decomposition -> multi-stream retrieval -> deterministic 5-chunk merge -> grounded generation | executed current `FIXED_DECOMPOSE` path (MiniLM stack) | reused frozen `FIXED_DECOMPOSE` |
| ADAPTIVE | frozen `A1_NO_ROUTER_ADAPTIVE` evidence-prefix rule (score-gap prefix, no query text; initial_k=5, max_k=20, token cap 6000, max_score_drop=3.0) | reused frozen A1 `no_router_adaptive_v1` (BGE research stack) | executed same rule on the frozen shared rewrite (MiniLM stack) |
| AUTO_ROUTER_AVAILABLE | best available auto-router per cohort; the two cohorts use different router lineages and are **not** silently merged into one algorithm | reused frozen A1 `query_router_v1` (`query-structure-router-v1`: SIMPLE->fixed, BROAD->adaptive) | reused frozen Router V1 `ROUTED` (`router_v1`: DIRECT vs DECOMPOSE) |

Router lineage note: the old `query-structure-router-v1` is an eval-only historical implementation; Router V1 is the implemented src pipeline. No single executable auto-router spans both cohorts, so the arm is named `AUTO_ROUTER_AVAILABLE`.

## 3. Validation 50 Results

| Arm | Complete | Required Coverage | Tokens/q | Latency/q |
|---|---:|---:|---:|---:|
| FAST | 43/50 (86.0%) | 196/208 (94.2%) | 2533.1 | unavailable |
| SEARCH+ | 42/50 (84.0%) | 190/208 (91.3%) | 2538.5 | 11.44 s (median 11.58 s; n=50/50) |
| ADAPTIVE | 46/50 (92.0%) | 202/208 (97.1%) | 6188.9 | unavailable |
| AUTO_ROUTER_AVAILABLE | 44/50 (88.0%) | 196/208 (94.2%) | 3667.7 | unavailable |

Citation-valid: FAST 50/50, SEARCH+ 50/50, ADAPTIVE 50/50, AUTO_ROUTER_AVAILABLE 50/50.
Eligible (router-style grounding rule): FAST 34/50, SEARCH+ 32/50, ADAPTIVE 32/50, AUTO_ROUTER_AVAILABLE 34/50.
Latency is unavailable for the reused A1 arms (no wall-clock was recorded in those artifacts); the executed SEARCH+ cells have wall-clock latency.

## 4. Router 20 Results

| Arm | Complete | Required Coverage | Tokens/q | Latency/q |
|---|---:|---:|---:|---:|
| FAST | 12/20 (60.0%) | 54/66 (81.8%) | 2251.2 | 4.40 s (median 4.44 s; n=20/20) |
| SEARCH+ | 9/20 (45.0%) | 51/66 (77.3%) | 2301.2 | 12.49 s (median 12.39 s; n=20/20) |
| ADAPTIVE | 16/20 (80.0%) | 60/66 (90.9%) | 3155.0 | 4.24 s (median 4.26 s; n=20/20) |
| AUTO_ROUTER_AVAILABLE | 13/20 (65.0%) | 55/66 (83.3%) | 2632.4 | 6.28 s (median 5.23 s; n=20/20) |

Citation-valid: FAST 20/20, SEARCH+ 20/20, ADAPTIVE 20/20, AUTO_ROUTER_AVAILABLE 20/20.
Eligible: FAST 14/20, SEARCH+ 11/20, ADAPTIVE 11/20, AUTO_ROUTER_AVAILABLE 15/20.

## 5. Combined 70 Results

| Arm | Complete | Required Coverage | Tokens/q | Latency/q |
|---|---:|---:|---:|---:|
| FAST | 55/70 (78.6%) | 250/274 (91.2%) | 2452.6 | 4.40 s (median 4.44 s; n=20/70) |
| SEARCH+ | 51/70 (72.9%) | 241/274 (88.0%) | 2470.7 | 11.74 s (median 11.92 s; n=70/70) |
| ADAPTIVE | 62/70 (88.6%) | 262/274 (95.6%) | 5322.1 | 4.24 s (median 4.26 s; n=20/70) |
| AUTO_ROUTER_AVAILABLE | 57/70 (81.4%) | 251/274 (91.6%) | 3371.9 | 6.28 s (median 5.23 s; n=20/70) |

Combined latency is only defined where per-query wall-clock exists (SEARCH+ 70/70; the other arms 20/70 from Router 20). Combined required coverage uses the reporting denominator 274 described in Scope.

## 6. Per-Query Comparison

Cells show `covered/required`, `✓` when complete, `✗cit` when citation validation failed, provider tokens in `k`, and `★` for the best observed quality on that query when the arms do not all tie (all non-tied winners marked).

| ID | Cohort | FAST | SEARCH+ | ADAPTIVE | AUTO ROUTER |
|---|---|---|---|---|---|
| val_001 | V1 | 3/4 4.2k ★ | 2/4 4.0k | 2/4 6.9k | 2/4 6.9k |
| val_002 | V1 | 5/5 ✓ 4.2k | 5/5 ✓ 4.2k | 5/5 ✓ 7.2k | 5/5 ✓ 4.2k |
| val_003 | V1 | 3/3 ✓ 2.4k | 3/3 ✓ 2.6k | 3/3 ✓ 5.4k | 3/3 ✓ 2.4k |
| val_004 | V1 | 6/6 ✓ 2.7k | 6/6 ✓ 2.3k | 6/6 ✓ 6.9k | 6/6 ✓ 2.7k |
| val_005 | V1 | 5/5 ✓ 3.2k | 5/5 ✓ 3.3k | 5/5 ✓ 6.6k | 5/5 ✓ 4.5k |
| val_006 | V1 | 4/5 4.1k | 2/5 3.9k | 5/5 ✓ 7.2k ★ | 5/5 ✓ 7.2k ★ |
| val_007 | V1 | 3/3 ✓ 2.2k | 3/3 ✓ 2.6k | 3/3 ✓ 5.3k | 3/3 ✓ 5.3k |
| val_008 | V1 | 3/4 2.8k | 3/4 2.6k | 4/4 ✓ 5.9k ★ | 4/4 ✓ 3.8k ★ |
| val_009 | V1 | 4/4 ✓ 2.8k | 4/4 ✓ 3.3k | 4/4 ✓ 6.7k | 4/4 ✓ 2.8k |
| val_010 | V1 | 5/5 ✓ 3.0k | 5/5 ✓ 3.3k | 5/5 ✓ 6.3k | 5/5 ✓ 3.0k |
| val_011 | V1 | 3/4 2.1k | 4/4 ✓ 2.6k ★ | 3/4 6.9k | 3/4 2.1k |
| val_012 | V1 | 4/4 ✓ 1.9k | 4/4 ✓ 2.4k | 4/4 ✓ 5.5k | 4/4 ✓ 5.5k |
| val_013 | V1 | 4/4 ✓ 2.3k | 4/4 ✓ 2.6k | 4/4 ✓ 6.9k | 4/4 ✓ 2.3k |
| val_014 | V1 | 4/4 ✓ 2.8k | 4/4 ✓ 2.5k | 4/4 ✓ 5.6k | 4/4 ✓ 2.8k |
| val_015 | V1 | 3/3 ✓ 3.1k | 3/3 ✓ 2.1k | 3/3 ✓ 7.1k | 3/3 ✓ 3.1k |
| val_016 | V1 | 4/4 ✓ 2.6k | 4/4 ✓ 2.4k | 4/4 ✓ 6.7k | 4/4 ✓ 6.7k |
| val_017 | V1 | 4/4 ✓ 2.9k | 4/4 ✓ 2.8k | 4/4 ✓ 6.7k | 4/4 ✓ 6.7k |
| val_018 | V1 | 3/3 ✓ 3.2k | 3/3 ✓ 2.4k | 3/3 ✓ 7.2k | 3/3 ✓ 5.9k |
| val_019 | V1 | 4/4 ✓ 2.8k | 4/4 ✓ 2.8k | 4/4 ✓ 6.9k | 4/4 ✓ 6.9k |
| val_020 | V1 | 4/4 ✓ 3.9k | 4/4 ✓ 3.1k | 4/4 ✓ 6.1k | 4/4 ✓ 6.1k |
| val_021 | V1 | 4/4 ✓ 2.2k | 4/4 ✓ 2.0k | 4/4 ✓ 6.9k | 4/4 ✓ 2.2k |
| val_022 | V1 | 4/4 ✓ 3.4k | 4/4 ✓ 3.5k | 4/4 ✓ 6.5k | 4/4 ✓ 4.9k |
| val_023 | V1 | 4/4 ✓ 3.0k | 4/4 ✓ 3.0k | 4/4 ✓ 6.5k | 4/4 ✓ 3.0k |
| val_024 | V1 | 4/4 ✓ 2.4k | 4/4 ✓ 3.1k | 4/4 ✓ 6.8k | 4/4 ✓ 2.4k |
| val_025 | V1 | 3/3 ✓ 2.9k ★ | 0/3 2.0k | 3/3 ✓ 6.8k ★ | 3/3 ✓ 4.3k ★ |
| val_026 | V1 | 3/3 ✓ 2.7k | 3/3 ✓ 2.5k | 3/3 ✓ 5.2k | 3/3 ✓ 3.9k |
| val_027 | V1 | 5/5 ✓ 2.0k ★ | 0/5 2.0k | 4/5 4.0k | 5/5 ✓ 2.0k ★ |
| val_028 | V1 | 4/4 ✓ 1.8k | 4/4 ✓ 2.1k | 4/4 ✓ 5.0k | 4/4 ✓ 1.8k |
| val_029 | V1 | 6/6 ✓ 1.9k | 6/6 ✓ 2.0k | 6/6 ✓ 4.7k | 6/6 ✓ 4.7k |
| val_030 | V1 | 3/3 ✓ 2.3k | 3/3 ✓ 1.8k | 3/3 ✓ 7.1k | 3/3 ✓ 2.3k |
| val_031 | V1 | 5/5 ✓ 2.0k | 5/5 ✓ 2.2k | 5/5 ✓ 7.0k | 5/5 ✓ 2.0k |
| val_032 | V1 | 4/4 ✓ 2.6k ★ | 3/4 2.2k | 4/4 ✓ 6.4k ★ | 4/4 ✓ 2.6k ★ |
| val_033 | V1 | 0/5 3.1k | 5/5 ✓ 3.1k ★ | 5/5 ✓ 6.7k ★ | 0/5 3.1k |
| val_034 | V1 | 5/5 ✓ 3.3k | 5/5 ✓ 3.2k | 5/5 ✓ 6.3k | 5/5 ✓ 3.3k |
| val_035 | V1 | 4/4 ✓ 0.9k | 4/4 ✓ 2.0k | 4/4 ✓ 5.3k | 4/4 ✓ 0.9k |
| val_036 | V1 | 4/4 ✓ 1.7k | 4/4 ✓ 1.7k | 4/4 ✓ 5.2k | 4/4 ✓ 2.5k |
| val_037 | V1 | 5/5 ✓ 2.6k | 5/5 ✓ 2.6k | 5/5 ✓ 6.0k | 5/5 ✓ 3.7k |
| val_038 | V1 | 5/5 ✓ 1.9k | 5/5 ✓ 2.7k | 5/5 ✓ 6.5k | 5/5 ✓ 5.5k |
| val_039 | V1 | 3/3 ✓ 1.4k ★ | 3/3 ✓ 1.7k ★ | 3/3 ✓ 6.2k ★ | 2/3 2.6k |
| val_040 | V1 | 3/3 ✓ 2.0k | 3/3 ✓ 2.1k | 3/3 ✓ 6.6k | 3/3 ✓ 2.0k |
| val_041 | V1 | 5/5 ✓ 2.7k | 5/5 ✓ 2.5k | 5/5 ✓ 6.7k | 5/5 ✓ 4.4k |
| val_042 | V1 | 5/5 ✓ 1.1k | 5/5 ✓ 1.4k | 5/5 ✓ 4.1k | 5/5 ✓ 2.3k |
| val_043 | V1 | 4/4 ✓ 1.8k | 4/4 ✓ 1.5k | 4/4 ✓ 5.1k | 4/4 ✓ 2.9k |
| val_044 | V1 | 4/4 ✓ 2.4k | 4/4 ✓ 2.0k | 4/4 ✓ 6.1k | 4/4 ✓ 3.4k |
| val_045 | V1 | 6/6 ✓ 3.2k | 6/6 ✓ 3.3k | 6/6 ✓ 6.8k | 6/6 ✓ 5.1k |
| val_046 | V1 | 2/4 2.2k | 2/4 2.5k | 2/4 6.7k | 2/4 3.8k |
| val_047 | V1 | 3/3 ✓ 2.7k | 3/3 ✓ 2.7k | 3/3 ✓ 6.6k | 3/3 ✓ 3.9k |
| val_048 | V1 | 4/4 ✓ 1.0k | 4/4 ✓ 1.3k | 4/4 ✓ 3.5k | 4/4 ✓ 2.8k |
| val_049 | V1 | 4/4 ✓ 2.4k | 4/4 ✓ 2.6k | 4/4 ✓ 5.8k | 4/4 ✓ 2.4k |
| val_050 | V1 | 3/4 1.8k | 3/4 1.6k | 4/4 ✓ 6.2k ★ | 3/4 1.8k |
| router_001 | R | 3/4 2.0k | 3/4 2.3k | 3/4 2.4k | 3/4 2.3k |
| router_002 | R | 3/3 ✓ 2.2k | 3/3 ✓ 2.3k | 3/3 ✓ 2.1k | 3/3 ✓ 2.5k |
| router_003 | R | 4/4 ✓ 2.8k ★ | 3/4 2.4k | 4/4 ✓ 2.7k ★ | 4/4 ✓ 3.0k ★ |
| router_004 | R | 3/3 ✓ 2.2k | 3/3 ✓ 2.1k | 3/3 ✓ 5.2k | 3/3 ✓ 2.5k |
| router_005 | R | 3/3 ✓ 3.0k | 3/3 ✓ 2.3k | 3/3 ✓ 3.1k | 3/3 ✓ 3.4k |
| router_006 | R | 4/4 ✓ 2.8k | 4/4 ✓ 3.0k | 4/4 ✓ 2.8k | 4/4 ✓ 3.2k |
| router_007 | R | 2/4 1.6k | 2/4 1.7k | 2/4 2.9k | 2/4 2.0k |
| router_008 | R | 0/2 2.4k | 1/2 2.1k | 2/2 ✓ 4.8k ★ | 0/2 2.6k |
| router_009 | R | 3/3 ✓ 1.9k | 3/3 ✓ 2.1k | 3/3 ✓ 2.2k | 3/3 ✓ 2.5k |
| router_010 | R | 3/3 ✓ 3.2k ★ | 1/3 3.2k | 3/3 ✓ 5.6k ★ | 3/3 ✓ 3.5k ★ |
| router_011 | R | 3/4 1.9k | 3/4 2.4k | 4/4 ✓ 3.9k ★ | 3/4 2.8k |
| router_012 | R | 3/3 ✓ 1.6k ★ | 2/3 1.2k | 3/3 ✓ 2.9k ★ | 3/3 ✓ 1.8k ★ |
| router_013 | R | 2/4 1.4k | 2/4 1.5k | 2/4 1.6k | 2/4 2.0k |
| router_014 | R | 2/3 2.0k | 2/3 2.6k | 2/3 3.0k | 2/3 2.4k |
| router_015 | R | 3/3 ✓ 3.2k | 3/3 ✓ 2.5k | 3/3 ✓ 3.2k | 3/3 ✓ 3.5k |
| router_016 | R | 2/3 2.7k | 1/3 3.0k | 3/3 ✓ 4.0k ★ | 3/3 ✓ 3.0k ★ |
| router_017 | R | 3/3 ✓ 1.5k | 3/3 ✓ 1.6k | 3/3 ✓ 1.6k | 3/3 ✓ 1.8k |
| router_018 | R | 3/3 ✓ 1.7k | 3/3 ✓ 2.0k | 3/3 ✓ 2.2k | 3/3 ✓ 2.0k |
| router_019 | R | 1/3 1.7k | 2/3 2.0k | 3/3 ✓ 2.3k ★ | 1/3 1.9k |
| router_020 | R | 4/4 ✓ 3.1k | 4/4 ✓ 3.6k | 4/4 ✓ 4.6k | 4/4 ✓ 4.0k |

## 7. Cost / Latency

Costs exclude the shared contextual rewrite (reported separately below) and judge calls; they are arm-attributable generation/decompose/router calls. Reused A1 Validation cells use the frozen counterfactual provider accounting from the A1 economics artifact.

| Arm | LLM calls/q | Input tokens | Output tokens | Total tokens | Tokens/q |
|---|---:|---:|---:|---:|---:|
| FAST | 1.00 | 149,779 | 21,902 | 171,681 | 2452.6 |
| SEARCH+ | 2.00 | 147,136 | 25,812 | 172,948 | 2470.7 |
| ADAPTIVE | 1.00 | 347,259 | 25,285 | 372,544 | 5322.1 |
| AUTO_ROUTER_AVAILABLE | 1.33 | 212,600 | 23,436 | 236,036 | 3371.9 |

| Arm | Latency samples | Total wall-clock | Mean | Median |
|---|---:|---:|---:|---:|
| FAST | 20/70 | 88.04 s | 4.40 s | 4.44 s |
| SEARCH+ | 70/70 | 821.93 s | 11.74 s | 11.92 s |
| ADAPTIVE | 20/70 | 84.79 s | 4.24 s | 4.26 s |
| AUTO_ROUTER_AVAILABLE | 20/70 | 125.56 s | 6.28 s | 5.23 s |

- Shared contextual rewrite (excluded above): Validation 50 executed SEARCH+ used 50 rewrites / 9,066 input / 1,161 output tokens; the frozen Router 20 run recorded 20 shared rewrites / 3,887 input / 655 output tokens.
- Historical Validation A1 generations used a 1,536-token answer budget; the current path and Router 20 use 512. Observed outputs reached the 512 cap in 4 current-path cells, so the reused and executed arms are not budget-identical.

## 8. Empirical Best-Arm Upper Bound

Frozen post-hoc rule: for each query choose the arm(s) with the highest observed quality tuple `(query-required complete, required aspects covered)` among actually executed arms; equal tuples are recorded as ties. Cost is never used to break a quality tie here.

- Best observed arm across the four strategies: **64/70 complete**, **265/274 required aspects**.
- Ties: 11 partial ties, 53 cases where every available arm tied at the same quality; no-quality rows: 0.

| Arm | Sole wins | Shared (tied) wins |
|---|---:|---:|
| FAST | 1 | 60 |
| SEARCH+ | 1 | 55 |
| ADAPTIVE | 4 | 63 |
| AUTO_ROUTER_AVAILABLE | 0 | 62 |

Quality-tied lowest-cost product view (cost used only after quality is tied): FAST 40, SEARCH+ 20, ADAPTIVE 8, AUTO_ROUTER_AVAILABLE 2.

This is a post-hoc empirical upper bound, not a product accuracy figure.

## 9. Product Interpretation

| Arm | Quality (complete / required recall) | Tokens/query | Latency/query | Interpretation |
|---|---:|---:|---:|---|
| FAST | 55/70 / 250/274 | 2452.6 | 4.40 s (n=20) | cheapest stable default |
| SEARCH+ | 51/70 / 241/274 | 2470.7 | 11.74 s (n=70) | current decompose path; no quality edge at higher latency |
| ADAPTIVE | 62/70 / 262/274 | 5322.1 | 4.24 s (n=20) | quality extreme; pays multiple x tokens |
| AUTO_ROUTER_AVAILABLE | 57/70 / 251/274 | 3371.9 | 6.28 s (n=20) | mixed-lineage availability arm |

**1. Is FAST still the right default?** Yes. FAST is the cheapest non-degenerate arm on both cohorts (2453 tokens/query combined) and no arm dominates it on quality at equal cost. ADAPTIVE buys quality at roughly 2.2x the tokens; current SEARCH+ is not better than FAST at higher latency.

**2. Does current SEARCH+ form a quality-oriented high-budget mode?** No. On Validation 50 it scores below FAST (42/50 complete, 190/208 aspects vs FAST 43/50 and 196/208) and on Router 20 it again trails DIRECT (9/20 vs 12/20) while taking 12.5 s vs 4.4 s per query. Current fixed-decompose implementation does not yet form a quality-oriented Search+ profile.

**3. Is ADAPTIVE a stronger Search+ backend?** Yes, per this snapshot. ADAPTIVE is the quality extreme in both cohorts and combined (62/70 complete, 262/274 aspects), outperforming SEARCH+ by 11 complete queries and 21 aspects while costing 2.15x its tokens and, on Router 20, less than half its latency. Adaptive is currently a stronger candidate for a quality-oriented Search+ profile. This is an experiment conclusion only; this run does not change the CLI.

**4. Does AUTO_ROUTER_AVAILABLE show enough value?** Mixed and not sufficient. The reused historical routers beat always-FAST by only 1 complete query on Validation 50 and 1 on Router 20 (with 8 queries where some other arm had strictly better quality), at a token overhead of 37% combined. The two lineages cannot even be merged into one arm. Keep it as a reference experiment, not a default.

## 10. Limitations

- Two separately constructed cohorts: Validation V1 is an exposed development benchmark; Router V1 is a small 20-query frozen benchmark. Combined 70 is not a new independent holdout.
- Mixed lineage: reused Validation A1 cells (FAST/ADAPTIVE/AUTO_ROUTER_AVAILABLE) ran on the frozen BGE research stack with no contextual rewrite and a 1,536-token budget; current-path cells (Validation SEARCH+, all executed Router cells) run on the MiniLM stack with rewrite and a 512-token budget. The frozen Router V1 arms used the MiniLM stack with one shared rewrite per case.
- AUTO_ROUTER_AVAILABLE merges two different router lineages and is not a single algorithm; per-cohort rows must be read separately.
- Reused outputs are historical: no answer was regenerated for them, and provider token figures for reused Validation A1 arms are counterfactual independent-run accounting (actual experiment deduplicated some calls).
- Wall-clock latency is unavailable for the reused Validation arms; only executed cells have comparable per-query latency.
- Metric compatibility: required-aspect completeness is the shared primary metric; citation-valid and eligible flags use the frozen judge outputs with the router V1 eligibility rule. Judge outputs are model-derived; Validation V1 had human adjudication for A1 disputes, Router V1 did not.
- One Validation SEARCH+ cell (VAL-001-022) failed once on a local cache-file lock and was re-executed once; the first failure is recorded in the run provenance.
- The Validation SEARCH+ (50) and Router ADAPTIVE (20) cells were executed with the frozen semantics during this snapshot's preparation and restored from the temporary workdir cell cache; re-running with `--reuse-existing` and no cache re-executes only those two groups, and the default mode executes all 280 cells live.
- Model variance: temperature 0 does not guarantee identical provider outputs; a fresh full run may produce slightly different numbers.
- Judge calls are excluded from serving-cost tables by project convention.
