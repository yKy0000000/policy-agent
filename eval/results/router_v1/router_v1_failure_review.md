# Router V1 Failure Review

## router_wrong_arm_vs_clear_oracle

- {"case_id": "router_001", "router": "DIRECT", "oracle": "FIXED_DECOMPOSE"}

## decompose_better_router_direct

- {"case_id": "router_001", "router": "DIRECT", "oracle": "FIXED_DECOMPOSE"}

## tie_router_decompose_extra_cost

- {"case_id": "router_009"}
- {"case_id": "router_020"}

## representation_gain_without_answer_gain

- {"case_id": "router_001", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_0d2d5abd2784cfcf630269b4", "chunk_65d9607208f5f96afca0d68c"]}
- {"case_id": "router_003", "direct_covered": 4, "decompose_covered": 3, "representation_gain_ids": ["chunk_85867a0b6a0b9d17cba279d7"]}
- {"case_id": "router_004", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_1b7a4f11eb7eec7619ddab24"]}
- {"case_id": "router_006", "direct_covered": 4, "decompose_covered": 4, "representation_gain_ids": ["chunk_aa63f943bce73a501994f897"]}
- {"case_id": "router_007", "direct_covered": 2, "decompose_covered": 2, "representation_gain_ids": ["chunk_8214a742720124ff8bdcbf21"]}
- {"case_id": "router_011", "direct_covered": 3, "decompose_covered": 3, "representation_gain_ids": ["chunk_3fe67c4153c058347f190445"]}

## selection_ranking_gain_without_answer_gain

- {"case_id": "router_001", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_0ef6386af9657bbfb48bef55"]}
- {"case_id": "router_002", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_18898aa0b0208d333109b1e0", "chunk_82b71e1d710271179f8b4bdd"]}
- {"case_id": "router_003", "direct_covered": 4, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_aa63f943bce73a501994f897", "chunk_a3593c3652416f4582a78c12"]}
- {"case_id": "router_005", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_1b7a4f11eb7eec7619ddab24", "chunk_e921fe7a8e1eeb16ec85d0b4", "chunk_eebcff7d8379f37aaf1bf06f"]}
- {"case_id": "router_010", "direct_covered": 3, "decompose_covered": 1, "selection_ranking_gain_ids": ["chunk_d47c7ab9c53cc480c3c2c069"]}
- {"case_id": "router_011", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_0cc6709199187f11f4436f08"]}
- {"case_id": "router_012", "direct_covered": 3, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_58ee210103515124e3a18e67"]}
- {"case_id": "router_013", "direct_covered": 2, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_503d0f8451cd132a55e45b74", "chunk_a241a064615d0fdcc343c6bf"]}
- {"case_id": "router_014", "direct_covered": 2, "decompose_covered": 2, "selection_ranking_gain_ids": ["chunk_d47c7ab9c53cc480c3c2c069", "chunk_04504541348ed0c60511a490"]}
- {"case_id": "router_015", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_69ac95f0ac7598ae7a1b0520", "chunk_2dbae335078ac45aaeafe49b"]}
- {"case_id": "router_016", "direct_covered": 2, "decompose_covered": 1, "selection_ranking_gain_ids": ["chunk_93b24002aa9b46b386d2061c", "chunk_87071e099cc59566a1079a0f"]}
- {"case_id": "router_017", "direct_covered": 3, "decompose_covered": 3, "selection_ranking_gain_ids": ["chunk_42a4d7c9a708df455947bda2"]}
- {"case_id": "router_020", "direct_covered": 4, "decompose_covered": 4, "selection_ranking_gain_ids": ["chunk_76a40eef1f0fee4df26723be"]}

## evidence_gain_but_not_eligible

- {"case_id": "router_003", "decompose_status": "judged"}
- {"case_id": "router_007", "decompose_status": "judged"}
- {"case_id": "router_008", "decompose_status": "judged"}
- {"case_id": "router_010", "decompose_status": "judged"}
- {"case_id": "router_013", "decompose_status": "judged"}
- {"case_id": "router_014", "decompose_status": "judged"}
- {"case_id": "router_016", "decompose_status": "judged"}
- {"case_id": "router_019", "decompose_status": "judged"}

## Zero evidence gain detail

- router_009 FIXED_DECOMPOSE: {"answer_equal_to_direct": false, "direct_covered": 3, "arm_covered": 3, "direct_complete": true, "arm_complete": true, "extra_streams": 3, "extra_llm_calls": 1, "extra_input_tokens": 163, "extra_output_tokens": 47}
- router_009 ROUTED: {"answer_equal_to_direct": false, "direct_covered": 3, "arm_covered": 3, "direct_complete": true, "arm_complete": true, "extra_streams": 3, "extra_llm_calls": 2, "extra_input_tokens": 437, "extra_output_tokens": 150}
- router_018 FIXED_DECOMPOSE: {"answer_equal_to_direct": false, "direct_covered": 3, "arm_covered": 3, "direct_complete": true, "arm_complete": true, "extra_streams": 3, "extra_llm_calls": 1, "extra_input_tokens": 172, "extra_output_tokens": 153}

