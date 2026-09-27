# Router V1 Frozen Experiment Report

Run: 2026-09-27T14:39:55Z to 2026-09-27T14:47:55Z; implementation commit `98cb503ee3a5b5f7f9340a5d5008b6497da5da0f`.

## 1. Executive Summary

- Fixed DIRECT answered 20/20 cases; query-required complete 12/20 (60%); required aspects covered 54/66.
- Fixed DECOMPOSE answered 20/20; complete 9/20 (45%); covered 51/66.
- ROUTED answered 20/20; complete 13/20 (65%); covered 55/66.
- Post-hoc oracle (frozen contract): {"FIXED_DECOMPOSE": 2, "TIE": 8, "FIXED_DIRECT": 6, "NEITHER_ELIGIBLE": 4}. Router matched the clear oracle on 7/8 cases with a clear preference.
- Router chose DECOMPOSE 3/20 times; executed DECOMPOSE 3/20; fallbacks {}.
- Routing-attributable quality: on the 17 DIRECT-executed cases ROUTED reused identical evidence to FIXED_DIRECT; 1 of them changed judged coverage ([{"case_id": "router_016", "direct_covered": 2, "routed_covered": 3, "direct_complete": false, "routed_complete": true}]), so the aggregate ROUTED lead over DIRECT is not attributable to routing.

## 2. Frozen Experimental Setup

- Benchmark: `eval/router_benchmark_v1.json` (20 queries), required-aspect truth `eval/router_v1_required_aspects.json` (66 required aspects).
- Architecture/contract/preregistration frozen before implementation; implementation commit `98cb503ee3a5b5f7f9340a5d5008b6497da5da0f`; 318 tests passing before this run.
- Corpus: 57 docs at `b9578b546d2506febda1da2cd7431644d58e512c`; same indexes, MiniLM reranker.
- Identity: DeepSeek `deepseek-v4-flash` (thinking disabled), temperature 0, router 96 / decomposer 256 / generation 512 output tokens, timeout 30s, retries 0.
- Execution order: per case, FIXED_DIRECT then FIXED_DECOMPOSE then ROUTED; one shared rewrite per case reused by all three arms.
- Judge: existing frozen `broad-v3-answer-quality-v1` protocol, one opaque label per call, arm identity never exposed.

## 3. Routing Behavior

- Router decisions: DIRECT 17, DECOMPOSE 3.
- Executed paths under ROUTED: DIRECT 17, DECOMPOSE 3.
- Fallbacks: {}.
- reason_code counts: {"COHERENT_SINGLE_REPRESENTATION": 17, "COVERAGE_SPLIT_RISK": 3}; validity: {"valid": 20}; schema anomalies: 0.

## 4. Quality Results

| arm | judged | execution success | citation valid | eligible | complete | covered aspects |
|---|---|---|---|---|---|---|
| FIXED_DIRECT | 20/20 | 20/20 | 20/20 | 14/20 | 12/20 | 54/66 |
| FIXED_DECOMPOSE | 20/20 | 20/20 | 20/20 | 11/20 | 9/20 | 51/66 |
| ROUTED | 20/20 | 20/20 | 20/20 | 15/20 | 13/20 | 55/66 |

## 5. Post-hoc Oracle

| oracle outcome | cases |
|---|---|
| FIXED_DIRECT | 6 |
| FIXED_DECOMPOSE | 2 |
| TIE | 8 |
| NEITHER_ELIGIBLE | 4 |
| ORACLE_UNAVAILABLE | 0 |

| case | oracle | direct elig/complete/covered | decompose avail/elig/complete/covered | router |
|---|---|---|---|---|
| router_001 | FIXED_DECOMPOSE | False/False/3 | True/True/False/3 | DIRECT |
| router_002 | TIE | True/True/3 | True/True/True/3 | DIRECT |
| router_003 | FIXED_DIRECT | True/True/4 | True/False/False/3 | DIRECT |
| router_004 | TIE | True/True/3 | True/True/True/3 | DIRECT |
| router_005 | TIE | True/True/3 | True/True/True/3 | DIRECT |
| router_006 | TIE | True/True/4 | True/True/True/4 | DIRECT |
| router_007 | NEITHER_ELIGIBLE | False/False/2 | True/False/False/2 | DIRECT |
| router_008 | NEITHER_ELIGIBLE | False/False/0 | True/False/False/1 | DIRECT |
| router_009 | TIE | True/True/3 | True/True/True/3 | DECOMPOSE |
| router_010 | FIXED_DIRECT | True/True/3 | True/False/False/1 | DIRECT |
| router_011 | FIXED_DECOMPOSE | False/False/3 | True/True/False/3 | DECOMPOSE |
| router_012 | FIXED_DIRECT | True/True/3 | True/True/False/2 | DIRECT |
| router_013 | NEITHER_ELIGIBLE | False/False/2 | True/False/False/2 | DIRECT |
| router_014 | FIXED_DIRECT | True/False/2 | True/False/False/2 | DIRECT |
| router_015 | TIE | True/True/3 | True/True/True/3 | DIRECT |
| router_016 | FIXED_DIRECT | True/False/2 | True/False/False/1 | DIRECT |
| router_017 | TIE | True/True/3 | True/True/True/3 | DIRECT |
| router_018 | FIXED_DIRECT | True/True/3 | True/False/True/3 | DIRECT |
| router_019 | NEITHER_ELIGIBLE | False/False/1 | True/False/False/2 | DIRECT |
| router_020 | TIE | True/True/4 | True/True/True/4 | DECOMPOSE |

## 6. Cost & Latency

| arm | llm calls (tot/mean) | streams (tot/mean) | rerank calls (tot) | input tok (tot/mean) | output tok (tot/mean) | latency s (tot/mean) |
|---|---|---|---|---|---|---|
| FIXED_DIRECT | 20/1.0 | 20/1.0 | 20 | 39105/1955.25 | 5920/296.0 | 88.04/4.402 |
| FIXED_DECOMPOSE | 40/2.0 | 80/4.0 | 80 | 38660/1933.0 | 7364/368.2 | 249.7907/12.4895 |
| ROUTED | 43/2.15 | 29/1.45 | 29 | 45840/2292.0 | 6809/340.45 | 125.559/6.278 |

- Shared rewrite: 20 calls, 3887 input / 655 output tokens (per query, reused by all arms).
- Judge (evaluation cost, excluded from serving): 20 calls, 136937 input / 41461 output tokens.
- Router overhead: 20 calls, 5555 input / 480 output tokens, 13.7s; it avoided 17 decomposer calls and 51 retrieval streams versus always-decompose.
- Monetary cost: no frozen price table for this run; not estimated.

## 7. Evidence Attribution

- FIXED_DECOMPOSE: executions 20; representation_gain cases ['router_001', 'router_003', 'router_004', 'router_006', 'router_007', 'router_011']; selection_ranking_gain cases ['router_001', 'router_002', 'router_003', 'router_005', 'router_008', 'router_010', 'router_011', 'router_012', 'router_013', 'router_014', 'router_015', 'router_016', 'router_017', 'router_019', 'router_020']; zero_evidence_gain cases ['router_009', 'router_018'].
- ROUTED_DECOMPOSE: executions 3; representation_gain cases ['router_011']; selection_ranking_gain cases ['router_020']; zero_evidence_gain cases ['router_009'].

## 8. Failure Analysis

- router_wrong_arm_vs_clear_oracle: [{"case_id": "router_001", "router": "DIRECT", "oracle": "FIXED_DECOMPOSE"}]
- decompose_better_router_direct: [{"case_id": "router_001", "router": "DIRECT", "oracle": "FIXED_DECOMPOSE"}]
- tie_router_decompose_extra_cost: [{"case_id": "router_009"}, {"case_id": "router_020"}]
- representation_gain_without_answer_gain: [{"case_id": "router_001", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_0d2d5abd2784cfcf630269b4", "chunk_65d9607208f5f96afca0d68c"]}, {"case_id": "router_003", "direct_covered": 4, "decompose_covered": 3, "representation_gain_ids": ["chunk_85867a0b6a0b9d17cba279d7"]}, {"case_id": "router_004", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_1b7a4f11eb7eec7619ddab24"]}, {"case_id": "router_006", "direct_covered": 4, "decompose_covered": 4, "representation_gain_ids": ["chunk_aa63f943bce73a501994f897"]}, {"case_id": "router_007", "direct_covered": 2, "decompose_covered": 2, "representation_gain_ids": ["chunk_8214a742720124ff8bdcbf21"]}, {"case_id": "router_011", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_3fe67c4153c058347f190445"]}]
- selection_ranking_gain_without_answer_gain: [{"case_id": "router_001", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_0ef6386af9657bbfb48bef55"]}, {"case_id": "router_002", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_18898aa0b0208d333109b1e0", "chunk_82b71e1d710271179f8b4bdd"]}, {"case_id": "router_003", "direct_covered": 4, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_aa63f943bce73a501994f897", "chunk_a3593c3652416f4582a78c12"]}, {"case_id": "router_005", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_1b7a4f11eb7eec7619ddab24", "chunk_e921fe7a8e1eeb16ec85d0b4", "chunk_eebcff7d8379f37aaf1bf06f"]}, {"case_id": "router_010", "direct_covered": 3, "decompose_covered": 1, "selection_ranking_gain_ids": ["chunk_d47c7ab9c53cc480c3c2c069"]}, {"case_id": "router_011", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_0cc6709199187f11f4436f08"]}, {"case_id": "router_012", "direct_covered": 3, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_58ee210103515124e3a18e67"]}, {"case_id": "router_013", "direct_covered": 2, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_503d0f8451cd132a55e45b74", "chunk_a241a064615d0fdcc343c6bf"]}, {"case_id": "router_014", "direct_covered": 2, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_d47c7ab9c53cc480c3c2c069", "chunk_04504541348ed0c60511a490"]}, {"case_id": "router_015", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_69ac95f0ac7598ae7a1b0520", "chunk_2dbae335078ac45aaeafe49b"]}, {"case_id": "router_016", "direct_covered": 2, "decompose_covered": 1, "selection_ranking_gain_ids": ["chunk_93b24002aa9b46b386d2061c", "chunk_87071e099cc59566a1079a0f"]}, {"case_id": "router_017", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_42a4d7c9a708df455947bda2"]}, {"case_id": "router_020", "direct_covered": 4, "decompose_covered": 4, "selection_ranking_gain_ids": ["chunk_76a40eef1f0fee4df26723be"]}]
- evidence_gain_but_not_eligible: [{"case_id": "router_003", "decompose_status": "judged"}, {"case_id": "router_007", "decompose_status": "judged"}, {"case_id": "router_008", "decompose_status": "judged"}, {"case_id": "router_010", "decompose_status": "judged"}, {"case_id": "router_013", "decompose_status": "judged"}, {"case_id": "router_014", "decompose_status": "judged"}, {"case_id": "router_016", "decompose_status": "judged"}, {"case_id": "router_019", "decompose_status": "judged"}]

## 9. Validity / Limitations

- n = 20; results are descriptive, not significance claims.
- Corpus-specific: findings apply to this 57-document GitHub site-policy snapshot only.
- Router predicts a retrieval coverage risk from the rewrite representation alone; no retrieval feedback.
- Provider/model nondeterminism: temperature 0 does not guarantee identical server-side outputs; raw responses were stored.
- All arms depend on the shared rewrite; rewrite errors affect every arm.
- DECOMPOSE has a larger retrieval budget (3-4 streams, more candidates) by design; cost is reported separately.
- Required-aspect granularity correlates with author multi_document metadata (r=0.776); completeness is stricter for cross-document cases.
- Benchmark surface bias: earlier freeze audit found overlapping structural cues; only 5 localized cases.
- Provider version identity is limited to the requested model id; immutable server version may be unavailable.

## 10. Conclusion

On this 20-query GitHub policy benchmark, always-decompose scored below fixed DIRECT (FIXED_DECOMPOSE 9/20 complete, 51/66 required aspects vs FIXED_DIRECT 12/20, 54/66). ROUTED scored 13/20 and 55/66, but on its DIRECT-executed cases it used evidence identical to FIXED_DIRECT and 1 case(s) differed only through generation sampling (['router_016']), so the routed-vs-DIRECT aggregate difference is not attributable to the routing decision. Routing matched 7/8 clear oracle preferences (one miss, router_001, was an eligibility-based preference with equal coverage), preserved the eligibility-favourable decompose case router_011, and spent extra cost on two TIE cases (['router_009', 'router_020']). Verdict: mixed; no clear routing-attributable quality gain at n=20.

## Research Table

| ID | Router | Executed | Direct qr | Decompose qr | Oracle | Routed qr | Evidence gain | Cost delta (streams/calls) |
|---|---|---|---|---|---|---|---|---|
| router_001 | DIRECT | DIRECT | no 3/4 | no 3/4 | FIXED_DECOMPOSE | no 3/4 | - | 1/2 vs 1/1 |
| router_002 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | TIE | yes 3/3 | - | 1/2 vs 1/1 |
| router_003 | DIRECT | DIRECT | yes 4/4 | no 3/4 | FIXED_DIRECT | yes 4/4 | - | 1/2 vs 1/1 |
| router_004 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | TIE | yes 3/3 | - | 1/2 vs 1/1 |
| router_005 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | TIE | yes 3/3 | - | 1/2 vs 1/1 |
| router_006 | DIRECT | DIRECT | yes 4/4 | yes 4/4 | TIE | yes 4/4 | - | 1/2 vs 1/1 |
| router_007 | DIRECT | DIRECT | no 2/4 | no 2/4 | NEITHER_ELIGIBLE | no 2/4 | - | 1/2 vs 1/1 |
| router_008 | DIRECT | DIRECT | no 0/2 | no 1/2 | NEITHER_ELIGIBLE | no 0/2 | - | 1/2 vs 1/1 |
| router_009 | DECOMPOSE | DECOMPOSE | yes 3/3 | yes 3/3 | TIE | yes 3/3 | zero | 4/3 vs 1/1 |
| router_010 | DIRECT | DIRECT | yes 3/3 | no 1/3 | FIXED_DIRECT | yes 3/3 | - | 1/2 vs 1/1 |
| router_011 | DECOMPOSE | DECOMPOSE | no 3/4 | no 3/4 | FIXED_DECOMPOSE | no 3/4 | rep | 4/3 vs 1/1 |
| router_012 | DIRECT | DIRECT | yes 3/3 | no 2/3 | FIXED_DIRECT | yes 3/3 | - | 1/2 vs 1/1 |
| router_013 | DIRECT | DIRECT | no 2/4 | no 2/4 | NEITHER_ELIGIBLE | no 2/4 | - | 1/2 vs 1/1 |
| router_014 | DIRECT | DIRECT | no 2/3 | no 2/3 | FIXED_DIRECT | no 2/3 | - | 1/2 vs 1/1 |
| router_015 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | TIE | yes 3/3 | - | 1/2 vs 1/1 |
| router_016 | DIRECT | DIRECT | no 2/3 | no 1/3 | FIXED_DIRECT | yes 3/3 | - | 1/2 vs 1/1 |
| router_017 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | TIE | yes 3/3 | - | 1/2 vs 1/1 |
| router_018 | DIRECT | DIRECT | yes 3/3 | yes 3/3 | FIXED_DIRECT | yes 3/3 | - | 1/2 vs 1/1 |
| router_019 | DIRECT | DIRECT | no 1/3 | no 2/3 | NEITHER_ELIGIBLE | no 1/3 | - | 1/2 vs 1/1 |
| router_020 | DECOMPOSE | DECOMPOSE | yes 4/4 | yes 4/4 | TIE | yes 4/4 | rank | 4/3 vs 1/1 |

