# Broad Query Validation V1

**Status:** frozen untouched validation set, independently constructed from the local policy corpus before any validation strategy run. The 16 V3 cases remain development data.

- Screening: 98 corpus opportunities; 50 accepted; 48 excluded (19 V3 overlap, 14 redundant, 15 narrow or unstable).
- Rubric: 239 answer-required atomic facts; mean 4.78, range 4–6 per case. All 239 have direct source support; no unresolved mappings.
- Sources: 38 policy documents across seven families; 47 single-document and 3 multi-document cases.
- Families: content removal 10; acceptable use 8; other site policies 6; privacy 5; GitHub terms 17; company policies 3; security 1.
- Query types: process 14; scope 18; eligibility 8; comparison 7; rights 3.
- Structural difficulty: easy 8; moderate 30; deep 12. These labels describe query and corpus structure, not observed retrieval ranks. Exception-heavy: 25.
- V3 duplicate review: all 16 development queries and core aspects compared semantically; no accepted duplicate core fact set.

## Pre-registered outcome criteria

Primary gates against always-V1: grounded micro fact-coverage regret ≤ 0.02; grounded fact-complete cases at most one fewer; total unsupported or contradicted claims cannot exceed V1, and cases with more such claims cannot outnumber cases with fewer. Assess evidence-token saving only after all quality gates pass: >10% strong, 5–10% effective but limited, 0–5% conservative, <0% failure.

The candidate strategy is frozen at **minimum Top5 reranker score 2.5 → Fixed; otherwise V1**. Config SHA-256: `e4863b1a0b0d27a396220d9eddc3fcef9cdada5e5e7dd41120152fa63dfdfe90`. Rubric SHA-256: `451a583f5ce88e0b573e61e5af073e34748b35900fa3ecd3d3f00b001699df50`. File hashes, corpus hash, freeze timestamp, and the exact gates are in `validation_v1_metadata.json`.

Validation outcomes must not be used to edit this rubric or tune the strategy. If a change is made based on those outcomes, this set becomes development data and a new untouched validation set is required.
