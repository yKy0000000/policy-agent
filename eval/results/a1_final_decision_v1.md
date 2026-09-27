# A1 Final Decision — Query-Aware Retrieval (Quality–Economics Pareto)

**Status: FINAL.** Frozen inputs only. No answers regenerated, no quality label changed, no arm/router/selector parameter changed, no A2/A3 implemented.

## A. Frozen inputs

- Quality: `a1_blind_answer_quality_frozen_v1.json` — SHA-256 `96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35`
- Quality arm table: `a1_blind_answer_quality_arm_table_v1.json` — SHA-256 `4a737bb502f9a2d57b0edb328d300bd8bbe468dfdbbe869dd6853e8b2583b217`
- Economics source: `query_aware_stage1_generation_results.json` → `per_arm_counterfactual_economics` — SHA-256 `1a0c2f0d873c93dcd58b1ff362e56001b99bf610c188671607aec3c6d81d2f11`; price table `21699903…`.
- Preregistration: `query_aware_arms_v1.json` `18d7adbf…`, `economics_contract_v1.md` `8ec4f46d…`, `query_aware_stage0_config.json` `744ed411…`, `query_aware_router_v1.json` `dcc7d495…`; router rule `04bb954e…`.
- Human truth: `frozen_human_verdicts_v1.json` `85199cfa…` (208 QUERY_REQUIRED aspects, Validation V1).
- 50 Validation V1 cases; 250 arm-case rows; 156 unique answers; 654 aspect judgments (626 covered / 28 missing / 0 partial / 0 incorrect after dispute resolution).

No threshold was invented after seeing results; the primary metric (provider total tokens/query) and the quality hierarchy are as preregistered.

## B. Final quality table

| Arm | Required Covered | Required Missing | QueryRequiredComplete | Confirmed regressions vs fixed | Correctness/Grounding issues |
|---|---:|---:|---:|---:|---:|
| fixed_top5 | 196 | 12 | 43/50 | 0 | 1 |
| adaptive_prefix_v1 | 200 | 8 | 44/50 | 2 | 1 |
| coverage_selector_v2 | 196 | 12 | 44/50 | 0 | 1 |
| no_router_adaptive_v1 | 202 | 6 | 46/50 | 1 | 1 |
| query_router_v1 | 196 | 12 | 44/50 | 1 | 2 |

## C. Final economics table

| Arm | input | output | total provider tokens | tokens/query | cost/query (USD) | evidence tokens | latency p50/p95 (s) |
|---|---:|---:|---:|---:|---:|---:|---|
| fixed_top5 | 110,674 | 15,982 | 126,656 | 2,533.1 | 0.00052381 | 91,699 | n/a |
| adaptive_prefix_v1 | 203,042 | 17,846 | 220,888 | 4,417.8 | 0.00082328 | 176,934 | n/a |
| coverage_selector_v2 | 147,045 | 17,008 | 164,053 | 3,281.1 | 0.00064523 | 125,648 | n/a |
| no_router_adaptive_v1 | 290,565 | 18,879 | 309,444 | 6,188.9 | 0.00109824 | 256,422 | 1.99 / 3.49 |
| query_router_v1 | 166,760 | 16,627 | 183,387 | 3,667.7 | 0.00069980 | 143,319 | n/a |

Primary measure = provider total tokens/query. `rewrite_calls = 0` for every arm. Only `no_router_adaptive_v1` has live latency (it had no reusable answers); the other four reused cached generations, so latency is **not** treated as zero and is **not** used for fair pairwise latency comparison. USD figures are uncached-equivalent estimates.

## D. Pairwise dominance

Dominance rule: A strictly dominates B iff A is not worse on primary quality (QueryRequiredComplete, required coverage), has no more confirmed regressions, no worse grounding, and strictly lower tokens/query.

**Only strict dominance: `coverage_selector_v2` dominates `query_router_v1`.**

### selector vs router (the decisive test)
| | complete | covered | regressions | grounding | tokens/query | $/query |
|---|---:|---:|---:|---:|---:|---:|
| coverage_selector_v2 | 44/50 | 196 | 0 | 1 | 3,281.1 | 0.00064523 |
| query_router_v1 | 44/50 | 196 | 1 | 2 | 3,667.7 | 0.00069980 |

Selector is equal or better on **every** axis and cheaper. The router is strictly dominated by a strategy that uses no query classification.

### fixed_top5 vs coverage_selector_v2
Frozen pairwise: gained 1 (VAL-001-006-F02, which completes that case) / lost 1 (VAL-001-001-F03); complete 43→44, regressions 0→0. **The extra ~29.5% tokens buy +1 complete case but net-zero required coverage (one aspect gained, one lost).** No material benefit under the contract's "gained with zero lost" rule → this is a genuine but offsetting trade-off; both remain Pareto non-dominated.

### coverage_selector_v2 vs adaptive_prefix_v1
Adaptive gains +4 covered aspects but carries **2 confirmed complete-regressions** and ~35% more tokens than selector at equal QueryRequiredComplete (44/50). Aggregate-coverage gain with confirmed regressions is not a clean win — it is a documented quality–cost trade-off; both non-dominated.

### adaptive_prefix_v1 vs no_router_adaptive_v1
no_router gains +2 covered and +2 complete cases but costs ~1.40× adaptive's tokens (6,188.9 vs 4,417.8) and has 1 confirmed regression vs adaptive's 2. The extra quality is bought with a very large cost increase; non-dominated trade-off.

### fixed_top5 vs no_router_adaptive_v1
Quality ceiling vs cost ceiling: no_router is the quality extreme (202/208, 46/50) at ~2.44× tokens; fixed is the cost extreme (2,533.1 tokens/query, 43/50).

## E. Pareto frontier

- **Strictly dominated:** `query_router_v1`
- **Pareto non-dominated:** `fixed_top5`, `coverage_selector_v2`, `adaptive_prefix_v1`, `no_router_adaptive_v1`
- **Quality-maximizing extreme:** `no_router_adaptive_v1` (202 covered, 46/50, 6,188.9 tokens/query)
- **Cost-minimizing extreme:** `fixed_top5` (196 covered, 43/50, 2,533.1 tokens/query)

No composite score was constructed; comparison is multi-metric.

## F. A1 router verdict

# KILL

Evidence: `query_router_v1` is strictly dominated by `coverage_selector_v2` (equal completeness and coverage; fewer confirmed regressions 0 vs 1; fewer grounding issues 1 vs 2; lower tokens/query 3,281.1 vs 3,667.7; lower $/query). Per the frozen arms rule ("A1_ROUTER must beat no-router adaptive on quality-cost Pareto, otherwise delete router") and the frozen complexity-deletion rule, the router is deleted. No tuning, no SIMPLE/BROAD redesign, no second router round.

## G. A1 research conclusion

Query-side SIMPLE/BROAD routing did **not** earn its existence. The router produced no unique answer-quality gain over a query-classification-free evidence strategy (equal required coverage and QueryRequiredComplete) while adding cost and regressions. In this experiment the evidence-side selector already captured the allocation signal, so the extra routing context did not convert into required-aspect quality. This is a formal negative A1 result, scoped to the GitHub Policy benchmark, the frozen SIMPLE/BROAD rule, the frozen context policies, and the current model/retrieval setup — not a claim that query routing is universally useless.

## H. Surviving architecture

- **Working / default baseline (next stage): `fixed_top5` (A0-BGE).** Simplest, cheapest non-dominated arm, zero confirmed complete-regressions. No more-complex component earns a material benefit (zero-loss gained aspect) that justifies its added cost under the frozen complexity-deletion rule.
- **Quality ceiling / reference (not default): `no_router_adaptive_v1`.** Non-dominated quality extreme kept as a reference only; it is ~2.44× tokens with 1 confirmed regression.
- `coverage_selector_v2` and `adaptive_prefix_v1` remain Pareto non-dominated but are **not adopted** (no material benefit; adaptive adds 2 confirmed regressions).

Roles differ: the default is the simplest survivor; the ceiling is a reference bound, not the working baseline.

## I. A2 trigger

# REQUIRES_FAILURE_ANALYSIS

Reason: the frozen A2 condition needs a **human-confirmed BROAD multi-requirement failure** with evidence that the cause is original-query representation rather than context budget/selection. A1 produced aggregate required-aspect data only (the ceiling arm still misses 6 aspects across 4 incomplete cases), with no failure-type decomposition. The trigger therefore cannot be decided from the current aggregates; a targeted failure analysis is required before A2 can start. A2 is **not** implemented here.

## J. Artifacts

- `eval/results/a1_final_pareto_v1.json`
- `eval/results/a1_final_decision_v1.md` (this file)
- Inputs (unchanged): `a1_blind_answer_quality_frozen_v1.json`, `a1_blind_answer_quality_arm_table_v1.json`, `query_aware_stage1_generation_results.json`, `query_aware_arms_v1.json`, `economics_contract_v1.md`.

## K. Tests / integrity

- Frozen quality hash verified as `96bf5fa6…`; economics read from `per_arm_counterfactual_economics` and matches the frozen values.
- No quality label, Human Truth, router, selector, or arm parameter was modified; no answers regenerated; no new evaluator; no composite score; no A2/A3.
- `python -m unittest discover -s tests` → 254 passed (last full run in this session).
