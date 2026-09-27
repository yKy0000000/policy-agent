# Evidence Geometry Diagnostic (Step -1 + Step 0)

Offline, gold-aware, read-only over the frozen Validation V1 benchmark.
No generation, no judge, no network.

## A. Step -1 Audit
- disagreement events: 11 (6 unique facts)
- categories: {'judge_false_positive': 6, 'existing_direct_mapping_sufficient': 5, 'missing_direct_mapping_candidate': 0, 'partial_support': 0, 'unresolved': 0}
- missing mapping candidates: 0
- facts removed from available: []

## B. Candidate Geometry
- full-union available coverage: 235/239
- reranked-Top20 available coverage: 235/239
- candidate-missing facts: 4
- oracle-complete cases (full union): 49/50

## C. Oracle Minimum (full union)
- min K: median 1.0, mean 1.14, min 0, max 3
- min tokens: median 323.0, mean 384.16

## D. V1 Gap
- median K gap (V1 - oracle): 7.0
- median token gap (V1 - oracle): 2776.5
- oracle <=5 & V1 >=10: 21 cases
- oracle <=6 & V1 >=10: 21 cases

## E. Representation Counterfactual
| level | units | unit tok p50 | unit tok p90 | median min K | median min tokens |
|---|---:|---:|---:|---:|---:|
| L0 current | 655 | 120 | 467 | 1.0 | 323.0 |
| L1 3-window | 655 | 395 | 1146 | 1.0 | 497.5 |
| L2 top-1 subtree | 362 | 208 | 691 | 1.0 | 373.5 |
- strong fragmentation cases: 3 (VAL-001-002, VAL-001-006, VAL-001-048)

## F. Support Geometry
- candidate-missing: 4
- sparse (1 group): 235
- robust (>=2 groups): 0
- sparse fact share: 98.3%

## G. Diagnosis
- distribution: {'ranking_selection_headroom': 46, 'fragmentation': 3, 'candidate_ceiling': 1}
- cases carrying ranking headroom flag: 50
- primary ranking/selection headroom cases: 46
- intrinsic breadth cases: 0
- strong fragmentation cases: 3

## H. Sensitivity
- directionally robust to audit adjustment

## Tail Ranking Baseline
- gold-rank histogram (facts): {'1': 162, '2': 30, '3': 11, '4': 8, '6': 15, '11': 1, '12': 4, '17': 4}
- top1: 162; top5: 211; buckets: {'rank_1': 162, 'rank_2_5': 49, 'rank_6_8': 15, 'rank_9_10': 0, 'rank_11_20': 9, 'rank_gt_20': 0, 'candidate_missing': 4}
- tail facts (rank 6-20): 24; deep-tail (rank>=11): 9; outside top5: 24
- affected cases outside top5: 6 (VAL-001-001, VAL-001-002, VAL-001-027, VAL-001-029, VAL-001-030, VAL-001-048)
- deepest gold rank: median 1, mean 2.4285714285714284, max 17
- cases deepest>5: 6; >8: 3; >10: 3
- V1 expansion cases: 42; expansion-recovered facts: 10
- tail policy families: {'content-removal-policies': 6, 'github-terms': 15, 'security-policies': 3}
- tail query types: {'process': 6, 'eligibility': 11, 'scope': 7}

## Answer Conversion Gap
- evidence-complete cases: 46; grounded-complete among them: 39; conversion rate (cases): 0.848
- gap cases: 7; fact conversion rate: 0.964
- attribution (facts): {'utilization_miss': 8, 'partial_synthesis': 0, 'citation_grounding_issue': 0, 'judge_rubric_disagreement': 0, 'compression_organization_loss': 0, 'other_or_unclear': 0}
- attribution (case primary): {'utilization_miss': 7, 'partial_synthesis': 0, 'citation_grounding_issue': 0, 'judge_rubric_disagreement': 0, 'compression_organization_loss': 0, 'other_or_unclear': 0}
- claim-level context: {'note': 'claim-level grounding/citation diagnoses are a different unit than facts', 'citation_error_claims': 14, 'grounding_review_claims': 13}
- utilization pattern verdict: MIXED GENERATION PATTERN
- pattern flags: {'single_dense_gold_chunk': 8, 'enumeration_query': 7, 'many_selected_chunks': 6, 'high_evidence_to_answer_compression': 3}
- VAL-001-009 [content-removal-policies] primary=utilization_miss secondary=[] missing_facts=['VAL-001-009-F02']
    - VAL-001-009-F02 pos=2/5 (0.25) intra=middle_third flags=['single_dense_gold_chunk'] ev_tokens=2977 ans_words=203 comp/1k=68.19
- VAL-001-011 [acceptable-use-policies] primary=utilization_miss secondary=[] missing_facts=['VAL-001-011-F01']
    - VAL-001-011-F01 pos=1/5 (0.0) intra=front_third flags=['enumeration_query', 'single_dense_gold_chunk'] ev_tokens=1744 ans_words=235 comp/1k=134.75
- VAL-001-013 [acceptable-use-policies] primary=utilization_miss secondary=[] missing_facts=['VAL-001-013-F04']
    - VAL-001-013-F04 pos=1/10 (0.0) intra=middle_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk'] ev_tokens=3283 ans_words=228 comp/1k=69.45
- VAL-001-026 [github-terms] primary=utilization_miss secondary=[] missing_facts=['VAL-001-026-F02']
    - VAL-001-026-F02 pos=1/12 (0.0) intra=front_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk'] ev_tokens=3568 ans_words=281 comp/1k=78.76
- VAL-001-032 [github-terms] primary=utilization_miss secondary=[] missing_facts=['VAL-001-032-F01', 'VAL-001-032-F02']
    - VAL-001-032-F01 pos=1/8 (0.0) intra=front_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk', 'high_evidence_to_answer_compression'] ev_tokens=3577 ans_words=195 comp/1k=54.51
    - VAL-001-032-F02 pos=1/8 (0.0) intra=front_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk', 'high_evidence_to_answer_compression'] ev_tokens=3577 ans_words=195 comp/1k=54.51
- VAL-001-037 [github-terms] primary=utilization_miss secondary=[] missing_facts=['VAL-001-037-F01']
    - VAL-001-037-F01 pos=1/12 (0.0) intra=front_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk'] ev_tokens=3816 ans_words=257 comp/1k=67.35
- VAL-001-039 [github-terms] primary=utilization_miss secondary=[] missing_facts=['VAL-001-039-F02']
    - VAL-001-039-F02 pos=1/14 (0.0) intra=middle_third flags=['enumeration_query', 'many_selected_chunks', 'single_dense_gold_chunk', 'high_evidence_to_answer_compression'] ev_tokens=2900 ans_words=98 comp/1k=33.79

## I. Decision
### PROCEED TO STRONGER RERANKER A/B
50 cases have small oracle min-cover but deep V1 selection vs 3 fragmentation cases; the recoverable headroom looks rankable.
