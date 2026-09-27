# Research Summary — Query-Aware Retrieval Study

A 3–5 minute read. Frozen results only; no new experiments, no composite score.

## 1. Problem

A GitHub-policy Q&A agent over the local `github/site-policy` corpus. Broad policy questions require several conditions, exceptions, actors, and process facts at once, so high-relevance evidence is not necessarily *complete* evidence. The question this study asks: which extra mechanisms actually deserve to be in the system?

## 2. Baseline

Fixed deterministic stack, frozen before experiments:

```text
multi-turn rewrite → Lexical Top20 + Semantic Top20 → union/dedup → BGE reranker
→ fixed Top5 context → grounded generation → deterministic citation validation
```

Benchmark: Validation V1 — 50 broad queries, 239 required atomic facts, 208 `QUERY_REQUIRED` aspects, frozen Human Truth (independent dual review, 94.86% initial agreement, disagreements adjudicated before any A1 quality analysis).

## 3. Bottleneck diagnosis

Candidate retrieval is near-saturated: candidate required-fact coverage ≈ **98.3% (235/239)**. Expansion of retrieval therefore has limited upside; the binding constraint is **context allocation and answer utilization**.

## 4. A1 — Does query routing help?

Hypothesis: SIMPLE/BROAD query structure can guide the context budget.

| Arm | Required Covered | Complete | Regressions | Tokens/query |
|---|---:|---:|---:|---:|
| `fixed_top5` | 196/208 | 43/50 | 0 | 2,533 |
| `coverage_selector_v2` | 196/208 | 44/50 | 0 | 3,281 |
| `query_router_v1` | 196/208 | 44/50 | 1 | 3,668 |
| `no_router_adaptive_v1` | 202/208 | 46/50 | 1 | 6,189 |

`coverage_selector_v2` matches the router on required coverage and completeness while being cheaper and having fewer regressions. The router is **strictly dominated** → **KILL**. No tuning; the negative result is the formal A1 result.

## 5. A2 — When decomposition actually helps

Hypothesis: a single representation of a multi-requirement query can suppress visibility of one requirement. Minimal offline mechanism probe on `VAL-001-046`:

| Strategy | Evidence visibility | Coverage |
|---|---|---|
| Original query | absent | 0/4 |
| Deeper original | rank 79/91 | 0/4 |
| MMR / diversity | absent from pool | 0/4 |
| Requirement query | rank 2 | 4/4 |

Decomposition uniquely restores the missing evidence (deeper retrieval and MMR cannot). But the clear representation failure occurs in only **1/50** cases, so it is **not adopted** by default and kept as a dormant, evidence-gated mechanism.

## 6. A3 decision

Parent/hierarchical retrieval was **not tested**: the residual-failure postmortem found **0 confirmed chunk-fragmentation cases**, so the mechanism had no observed failure mode to justify experimentation. `A3_NOT_TRIGGERED`.

## 7. Final architecture

Hybrid retrieval → BGE reranker → `fixed_top5` context → grounded generation → deterministic validation. BGE is the research-recommended configuration; the repository production default remains MiniLM + `fixed_top5`. The final system is **simpler** than the candidate set: one validated mechanism kept, one killed, one confirmed-but-dormant, one never triggered.

## 8. Lessons

- Measure the bottleneck before adding machinery; candidate recall was already saturated.
- A real mechanism can still be non-adoptable when incidence is low.
- Remove dominated components; keep negative results in the record.
- **Add complexity only when a measured failure mode justifies it.**

See `architecture_decision.md`, `final_metrics.json`, `failure_analysis.json`, `a2_case_study.json`, `figures/`.
