# Human truth freeze and pre-A1 context rescore

## Frozen truth

- Final artifact SHA-256: `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716`.
- 331 aspects: 296 QUERY_REQUIRED, 35 RELEVANT_BUT_OPTIONAL, 0 AMBIGUOUS. Initial reviewer agreement: 314/331 (94.864%); all 17 disagreements resolved by the user-confirmed labels with omission-test reasons.
- Eight frozen SIMPLE sentinel cases and their 41 aspect rows are intact. The source worksheet and all frozen Stage 0 artifacts are unchanged; frozen hashes verified.

## Human-aware context metrics (Validation V1, 50 paired cases)

Coverage is micro coverage over query-required aspects. FULL counts cases with all query-required aspects supported by selected context. Evidence tokens are the frozen Stage 0 diagnostic costs, not live generation tokens.

| Frozen arm | QueryRequiredCoverage | QueryRequiredFULL | Required aspects covered | Evidence tokens |
|---|---:|---:|---:|---:|
| `fixed_top5` | 92.79% | 46/50 | 193/208 | 91,699 |
| `adaptive_prefix_v1` | 96.15% | 48/50 | 200/208 | 176,934 |
| `coverage_selector_v2` | 93.75% | 47/50 | 195/208 | 125,648 |
| `no_router_adaptive_v1` | 96.15% | 48/50 | 200/208 | 256,422 |
| `query_router_v1` | 93.75% | 47/50 | 195/208 | 143,319 |

## Paired deltas vs fixed_top5

Gained and lost count required aspect IDs whose direct support enters or leaves the selected context on the same query.

| Arm | Gained | Lost | Net | FULL gained/lost | Coverage Δ (pp) | Evidence-token Δ |
|---|---:|---:|---:|---:|---:|---:|
| `adaptive_prefix_v1` | 7 | 0 | +7 | 2/0 | +3.37 | +85,235 |
| `coverage_selector_v2` | 2 | 0 | +2 | 1/0 | +0.96 | +33,949 |
| `no_router_adaptive_v1` | 7 | 0 | +7 | 2/0 | +3.37 | +164,723 |
| `query_router_v1` | 2 | 0 | +2 | 1/0 | +0.96 | +51,620 |

## All-arm paired comparisons

The JSON result records gained/lost aspect IDs, case IDs, FULL transitions, coverage deltas, and token deltas for all 10 pairs. Key comparisons:

- `coverage_selector_v2` vs `adaptive_prefix_v1`: 0 gained, 5 lost; FULL +0/-1; tokens -51,286.
- `no_router_adaptive_v1` vs `adaptive_prefix_v1`: 0 gained, 0 lost; FULL +0/-0; tokens +79,488.
- `query_router_v1` vs `coverage_selector_v2`: 0 gained, 0 lost; FULL +0/-0; tokens +17,671.
- `query_router_v1` vs `no_router_adaptive_v1`: 0 gained, 5 lost; FULL +0/-1; tokens -113,103.

## Context-level dominance

- `no_router_adaptive_v1` is strictly dominated in aggregate by `adaptive_prefix_v1` under the stated coverage/FULL/evidence-token rule.
- `query_router_v1` is strictly dominated in aggregate by `coverage_selector_v2` under the stated coverage/FULL/evidence-token rule.

This is a pre-generation context diagnostic. It does not make an architecture kill/adoption decision or evaluate answer quality, provider tokens, or latency. The 16 V3 cases are excluded from the five-arm rescore because the frozen replay has no selected contexts for them.
