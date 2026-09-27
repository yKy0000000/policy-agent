# Final Architecture Decision (v1)

**Status: RESEARCH PHASE COMPLETE — A3 NOT TRIGGERED.** This document freezes the production/working architecture and records what was adopted and what was deliberately not adopted. No new retrieval mechanism, no parameter change, no new generation.

## 1. Final production / working architecture

```text
Query
→ existing multi-turn rewrite when applicable
→ Lexical Top20 + Semantic Top20
→ union / chunk-ID dedup
→ BGE reranker
→ fixed Top5 context
→ frozen grounded generation
→ deterministic citation/output validation
```

Explicitly **not** in the final architecture:

- `query_router_v1` (SIMPLE/BROAD router) — KILLED;
- default requirement decomposition — mechanism confirmed, not adopted;
- hierarchical / parent context expansion — no observed failure mode.

Configuration note (from the Stage 0 freeze): the research A0-BGE stack uses `BAAI/bge-reranker-base` with `fixed_top5`. The repository production default uses the MiniLM cross-encoder with `fixed_top5`. Per the Stage 0 separation rule the two configurations are never compared as a single baseline; the research decision above applies to the A0-BGE stack.

## 2. Architecture decisions by mechanism

| Mechanism | Hypothesis | Evidence | Decision |
|---|---|---|---|
| BGE reranker | better ranking improves evidence quality | prior transfer gain (MiniLM-Top5 vs BGE-Top5: answer macro 0.866 → 0.920, complete 36 → 38, contradicted 5 → 1, missing citations 16 → 6) | **KEEP** |
| SIMPLE/BROAD router | query structure improves allocation | strictly dominated by `coverage_selector_v2` (equal coverage/completeness; more regressions and grounding issues; higher tokens) | **KILL** |
| Evidence selector (`coverage_selector_v2`) | allocation without query classification | non-dominated but no material adoption gain over the simplest baseline vs `fixed_top5` (gained 1 / lost 1 required aspect, 0 confirmed regressions, +29.5% tokens) | **REFERENCE / NON-DEFAULT** |
| Requirement decomposition | fixes representation failures on multi-requirement queries | uniquely fixes `VAL-001-046` (rank 2/selected vs absent / rank 79 / absent); clear incidence 1/50 | **CONFIRMED, NOT ADOPTED** |
| Parent / hierarchical context | fixes chunk-boundary fragmentation | 0 confirmed fragmentation cases in the residual-failure postmortem | **NOT TRIGGERED** |

## 3. A1 router verdict (frozen)

`query_router_v1` is **KILLED**. It is strictly dominated by `coverage_selector_v2`: equal `QueryRequiredComplete` (44/50) and required coverage (196/208), fewer confirmed regressions (0 vs 1), fewer correctness/grounding issues (1 vs 2), and lower provider tokens/query (3,281.1 vs 3,667.7). It also fails the frozen rule that the router must beat the no-router adaptive arm on quality–cost Pareto. No router tuning was performed.

## 4. Dormant (evidence-gated) mechanism — not a runtime feature

**Requirement decomposition** is retained as a **research finding**, not a production branch:

- mechanism experimentally confirmed (offline retrieval probe on `VAL-001-046`);
- clear representation-failure incidence: **1 / 50** Validation V1 cases;
- **not adopted by default**;
- future activation only if production telemetry or an expanded benchmark reveals a materially higher representation-failure frequency.

No fallback branch or analyzer is added to the production pipeline.

## 5. A3 trigger decision: `A3_NOT_TRIGGERED`

The frozen road map permits A3 only when there is explicit fragmentation evidence (relevant child retrieved/selected, query-required qualifier in a sibling/nearby/parent chunk, and the failure not explainable by ranking/budget/generation). The residual-failure postmortem records **0 confirmed chunk-boundary fragmentation cases** and no contrary evidence. Therefore hierarchical / parent expansion has **no observed failure mode** to justify it, and A3 is not run.

## 6. Research vs production separation

- **Production path:** the simple `fixed_top5` deterministic pipeline above. Readable, testable, unchanged by this round.
- **Evaluation/research layer:** benchmarks, frozen Human Truth, A1/A2 artifacts, blind evaluation, economics, replay, negative results, and decision records. Experiment runners and any state-machine/audit machinery stay in this layer and are never wired into the production flow.

## 7. Rationale

The project prioritized **evidence allocation** over retrieval growth because candidate retrieval was already near saturation (Validation V1 candidate required-fact coverage ≈ 98.3%). A1 tested whether query structure could guide allocation and answered **no**. The residual-failure analysis then showed the remaining losses are dominated by answer utilization (generation) and context budget/selection, with only one clear representation case (A2) and zero fragmentation cases. The consistent conclusion is the project theme: **add complexity only when a measured failure mode justifies it** — so the final system is simpler, not larger.
