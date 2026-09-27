# Final Research Summary (v1) — Query-Aware Retrieval Study

**Status: RESEARCH PHASE COMPLETE — A3 NOT TRIGGERED.** Frozen results only; no new metrics, no composite score, no new mechanism.

## 1. Baseline diagnosis

Candidate retrieval is already near saturation on the GitHub Policy benchmark: candidate required-fact coverage is ~98.3% (235/239 Validation V1 facts), so the binding constraint is **evidence allocation and utilization**, not candidate recall. The study therefore fixed the retrieval stack and varied only the **context-allocation policy** (which/how many chunks enter the generation context).

Frozen stack: multi-turn rewrite → Lexical Top20 + Semantic Top20 → union/chunk-ID dedup → BGE reranker → context policy → grounded generation → deterministic citation validation.

## 2. A1 — Query routing

- **Hypothesis:** SIMPLE/BROAD query structure can guide the context budget.
- **Result:** `query_router_v1` produced no unique quality gain and was **strictly dominated by `coverage_selector_v2`** (equal 196/208 covered and 44/50 complete; 1 vs 0 confirmed regressions; 2 vs 1 grounding issues; 3,667.7 vs 3,281.1 tokens/query).
- **Decision:** **KILL router.**

Quality–cost headline (no composite score):

| Arm | Required Covered | Complete | Confirmed regressions | tokens/query | $/query |
|---|---:|---:|---:|---:|---:|
| `fixed_top5` | 196/208 | 43/50 | 0 | 2,533.1 | 0.00052381 |
| `coverage_selector_v2` | 196/208 | 44/50 | 0 | 3,281.1 | 0.00064523 |
| `query_router_v1` | 196/208 | 44/50 | 1 | 3,667.7 | 0.00069980 |
| `adaptive_prefix_v1` | 200/208 | 44/50 | 2 | 4,417.8 | 0.00082328 |
| `no_router_adaptive_v1` | 202/208 | 46/50 | 1 | 6,188.9 | 0.00109824 |

`query_router_v1` is strictly dominated; `no_router_adaptive_v1` is the quality ceiling/reference; `fixed_top5` is the simplest, cheapest, regression-free working baseline.

## 3. A2 — Requirement decomposition (mechanism probe)

- **Hypothesis:** a single representation of a multi-requirement query can suppress visibility of an independent requirement.
- **Result:** on `VAL-001-046` the mechanism is confirmed and **uniquely** effective:

| Strategy | Supporting evidence visibility | Final retrieval result |
|---|---|---|
| Original query | absent | 0/4 |
| Deeper original | rank 79/91 | 0/4 |
| Diversity/MMR | absent from pool | 0/4 |
| Requirement query | rank 2 | 4/4 |

- **Incidence:** 1 clear representation case / 50 V1 cases.
- **Decision:** **Mechanism confirmed; default adoption rejected** (`A2_MECHANISM_CONFIRMED_BUT_NOT_ADOPTED`). Kept as an evidence-gated dormant mechanism, not a hot path.

## 4. Residual-failure postmortem

16 residual QUERY_REQUIRED missing aspects (10 cases): `GENERATION_MISS` 6, `SELECTION_BUDGET` 6, `RANKING_WEAKNESS` 2, `REPRESENTATION_CANDIDATE` 2 (1 clear case), `FRAGMENTATION_CANDIDATE` **0**. Dominant layers are generation and context selection — not representation and not fragmentation.

## 5. A3 — Hierarchical / parent context

- **Trigger hypothesis:** residual failures come from chunk fragmentation.
- **Observed evidence:** 0 confirmed fragmentation cases.
- **Decision:** **NOT TRIGGERED.** No A3 probe was run.

## 6. What survived / what was removed

### What survived
- Hybrid lexical + semantic retrieval — candidate coverage ≈ 98.3%; retrieval is not the bottleneck.
- BGE reranking — prior transfer gain (answer macro 0.866 → 0.920, complete 36 → 38).
- Simple `fixed_top5` context policy — cheapest non-dominated arm with zero confirmed regressions.
- Grounded generation — ~96.5% utilization when required evidence is in context; remaining losses are utilization, not retrieval.
- Deterministic citation/output validation — structural/source validation only.
- Replay / evaluation / economics framework — enables frozen, comparable decisions and preserves negative results.

### Removed / not adopted
- SIMPLE/BROAD router — strictly dominated by the evidence selector.
- Default requirement decomposition — mechanism proven but incidence 1/50 is insufficient for a hot path.
- Hierarchical parent expansion — no observed fragmentation failure mode.

## 7. Architecture implication

Final working architecture is the simple deterministic pipeline (rewrite → hybrid Top20 union → BGE rerank → fixed Top5 → grounded generation → deterministic validation). Complexity was removed rather than added. The one proven advanced mechanism (decomposition) stays dormant pending evidence of materially higher incidence.

## 8. Lessons

- Measure the bottleneck before adding machinery; candidate recall was already saturated.
- A mechanism can be real and still not worth adopting — incidence matters as much as effect size.
- Remove components that are dominated or that buy no material benefit at extra cost.
- Freeze quality before looking at economics; keep negative results in the record.
- **Add complexity only when a measured failure mode justifies it.**

## 9. Artifacts

`a1_blind_answer_quality_frozen_v1.json`, `a1_final_pareto_v1.json`, `a1_final_decision_v1.md`, `a1_failure_analysis_v1.json`, `a2_minimal_mechanism_probe_v1.json`, `final_architecture_decision_v1.md`, `final_results_table_v1.json`, `gradual_delivery_narrative_v1.md`.
