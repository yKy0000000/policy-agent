# Marginal-Information Dynamic-K

## Motivation

Reranker relevance does not measure how much information a chunk adds to selected evidence.

## Method

Top5 start; per-query Top20 min-max relevance; semantic novelty = 1 − maximum selected-evidence cosine similarity. Scan in rank order, skip low-gain chunks, stop after 2–3 consecutive low gains; K≤20 and tokens≤6,000.
Product gain = relevance × novelty; additive gain = 0.5 × relevance + 0.5 × novelty. One variant adds 0.08 for a new document/heading pair. Thresholds and patience are recorded in the JSON result.

## Evidence Results

| Strategy | Macro | Micro | Complete | Avg K | Tokens | Post-completion |
|---|---:|---:|---:|---:|---:|---:|
| fixed_top5 | 0.749 | 0.750 | 7/16 | 5.00 | 27,274 | 6,653 |
| adaptive_prefix_v1 | 0.930 | 0.935 | 12/16 | 10.25 | 50,530 | 19,013 |
| product_p2 | 0.853 | 0.859 | 9/16 | 7.44 | 39,666 | 12,308 |
| product_p3 | 0.879 | 0.880 | 10/16 | 10.06 | 51,548 | 19,693 |
| additive_p2 | 0.863 | 0.870 | 9/16 | 7.38 | 38,148 | 12,371 |
| product_section_p3 | 0.939 | 0.946 | 13/16 | 18.06 | 78,458 | 44,083 |

## K Distribution

- product_p2: K=5×3, K=6×3, K=7×3, K=8×3, K=9×1, K=10×2, K=12×1.
- product_p3: K=5×1, K=6×1, K=8×4, K=9×2, K=11×2, K=12×2, K=13×3, K=15×1.
- additive_p2: K=5×3, K=6×3, K=7×3, K=8×4, K=9×1, K=10×1, K=13×1.
- product_section_p3: K=8×1, K=14×1, K=16×2, K=17×1, K=18×1, K=20×10.

## Key Observation

- No recommended configuration: token-saving variants lose 6–7 facts and three complete cases versus V1.
- The section-bonus variant covers one additional fact, but spends 55% more tokens and selects K=20 for 10/16 cases.
- Product/additive variants produce varied K values, yet semantic novelty misses required policy distinctions.
- V3-03 and V3-11 have candidate-pool ceilings; V3-01 has a Top20 depth ceiling.

## Status

Exploratory — not independently validated.
