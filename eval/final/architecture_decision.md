# Final Architecture Decisions (A1–A3)

Frozen research phase. Final working / recommended research configuration:

```text
Query
→ multi-turn rewrite when applicable
→ Lexical Top20 + Semantic Top20
→ union / chunk-ID dedup
→ BGE reranker
→ fixed Top5 context
→ grounded generation
→ deterministic citation/output validation
```

| Mechanism | Tested? | Evidence | Decision | Runtime status |
|---|---|---|---|---|
| Hybrid retrieval | yes | strong candidate recall (≈ 98.3% required-fact coverage) | **KEEP** | active (production) |
| BGE reranker | yes | measured improvement (answer macro 0.866 → 0.920, complete 36 → 38) | **KEEP** | research recommended |
| SIMPLE/BROAD router | yes | strictly dominated by `coverage_selector_v2` | **KILL** | removed |
| Evidence selector (`coverage_selector_v2`) | yes | non-dominated but no material adoption gain over the simplest baseline | **REFERENCE** | inactive (explicit opt-in) |
| Requirement decomposition | minimal mechanism probe | uniquely repairs one representation failure (1/50) | **CONFIRMED / NOT ADOPTED** | dormant |
| Parent / hierarchical expansion | no | 0 confirmed fragmentation failures | **NOT TRIGGERED** | absent |

## Configuration caveat

The repository production default is currently **MiniLM cross-encoder + fixed Top5**. The research-selected recommended configuration is **BGE reranker + fixed Top5**; BGE is **not** production-active. The two configurations are never compared as one baseline (Stage 0 separation rule). No production default was changed by this study.

## Operational rules

- `query_router_v1` is not available in the final architecture.
- Decomposition is a **research finding**, not a runtime feature; no fallback branch was added.
- Hierarchical/parent expansion was never implemented because no failure mode justified it.

See `research_summary.md`, `final_metrics.json`, `failure_analysis.json`, `a2_case_study.json`.
