# Stronger Pointwise Reranker A/B (evidence level)

Frozen Validation V1, fixed candidate union; only the reranker model varies.
No generation, no judge, no external API.

## Models
- baseline: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- challenger: `BAAI/bge-reranker-base` (ran)
- candidate union hash: `d09e85acd86c8c89`; baseline==challenger union: True
- runtime (s): {'baseline': 107.6, 'challenger': 636.63}

## Gold Rank Distribution (facts)
| bucket | baseline | challenger |
|---|---:|---:|
| rank_1 | 162 | 166 |
| rank_2_5 | 49 | 58 |
| rank_6_8 | 15 | 7 |
| rank_9_10 | 0 | 0 |
| rank_11_20 | 9 | 0 |
| rank_gt_20 | 0 | 4 |
| missing | 4 | 4 |

## Coverage / Completeness
| metric | baseline | challenger |
|---|---:|---:|
| coverage@1 | 162 | 166 |
| coverage@3 | 203 | 219 |
| coverage@5 | 211 | 224 |
| coverage@8 | 226 | 231 |
| coverage@10 | 226 | 231 |
| coverage@20 | 235 | 231 |
| fact-complete cases@5 | 43 | 46 |
| fact-complete cases@8 | 46 | 48 |
| fact-complete cases@10 | 46 | 48 |
| fact-complete cases@20 | 49 | 48 |

## Tail Movement (baseline rank 6-20)
- tail facts 24; improved 20; unchanged 0; regressed 4
- moved into Top5 20; into Top8 20

## Deep-tail (baseline rank >= 11)
| case | fact | gold chunk | baseline | challenger | delta |
|---|---|---|---:|---:|---:|
| VAL-001-048 | VAL-001-048-F06 | chunk_90eac1d0ab31f74bae4a5f67 | 11 | 5 | 6 |
| VAL-001-001 | VAL-001-001-F01 | chunk_dfcbf6c0856007fb39268709 | 12 | 22 | -10 |
| VAL-001-001 | VAL-001-001-F02 | chunk_dfcbf6c0856007fb39268709 | 12 | 22 | -10 |
| VAL-001-001 | VAL-001-001-F03 | chunk_dfcbf6c0856007fb39268709 | 12 | 22 | -10 |
| VAL-001-001 | VAL-001-001-F04 | chunk_dfcbf6c0856007fb39268709 | 12 | 22 | -10 |
| VAL-001-030 | VAL-001-030-F01 | chunk_34136e4d23182639a9255feb | 17 | 5 | 12 |
| VAL-001-030 | VAL-001-030-F02 | chunk_34136e4d23182639a9255feb | 17 | 5 | 12 |
| VAL-001-030 | VAL-001-030-F03 | chunk_34136e4d23182639a9255feb | 17 | 5 | 12 |
| VAL-001-030 | VAL-001-030-F04 | chunk_34136e4d23182639a9255feb | 17 | 5 | 12 |

## Evidence Gate
### CLEAR EVIDENCE WIN
- coverage@5 delta 13, fact-complete@5 delta 3
