# Reproducibility Manifest

Key frozen artifacts only. Full provenance chain lives under `eval/archive/` and in the dated `*_v1` artifacts in `eval/results/`.

## Benchmark / Human Truth

| Artifact | SHA-256 |
|---|---|
| `eval/results/frozen_human_verdicts_v1.json` | `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716` |
| `eval/validation/broad_queries_validation_v1.json` | `1fb2b03d752343ea19d83283dff92d066febe357178cb93a5cf7c603c1fe4858` |
| `eval/validation/broad_atomic_facts_validation_v1.json` | `451a583f5ce88e0b573e61e5af073e34748b35900fa3ecd3d3f00b001699df50` |
| `eval/validation/validation_v1_metadata.json` | `a91ab96a6c3f25551753b18bf647c718bdd7b3226fe59f3ebece26a2210c0339` |

## A1 quality

| Artifact | SHA-256 |
|---|---|
| `eval/results/a1_blind_answer_quality_frozen_v1.json` | `96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35` |
| `eval/results/a1_blind_answer_quality_arm_table_v1.json` | `4a737bb502f9a2d57b0edb328d300bd8bbe468dfdbbe869dd6853e8b2583b217` |

## A1 economics

| Artifact | SHA-256 |
|---|---|
| `eval/results/query_aware_stage1_generation_results.json` (per-arm counterfactual economics) | `1a0c2f0d873c93dcd58b1ff362e56001b99bf610c188671607aec3c6d81d2f11` |

## A1 decision

| Artifact | SHA-256 |
|---|---|
| `eval/results/a1_final_pareto_v1.json` | `5629d050e4e099547449ff57d1b9bb423a8d1a7786d9fa855331ebaef0be3628` |
| `eval/results/a1_final_decision_v1.md` | `f3481095ed5045c8fe9f27d17485c4ebfceb638812d72b18b3de1c13f3e1c607` |

## A1 failure analysis

| Artifact | SHA-256 |
|---|---|
| `eval/results/a1_failure_analysis_v1.json` | `c0baf21496e86916b6e62b0328dfb1dcb44ce3ab1097cea02a36d88ad2c564b3` |

## A2 probe

| Artifact | SHA-256 |
|---|---|
| `eval/a2_minimal_probe_requirements_v1.json` | `fa564dac8eb9a95f2208d06429f7c661b47c110d0df8ecdac0a797c84414562a` |
| `eval/results/a2_minimal_mechanism_probe_v1.json` | `ceba0ffa54a6e4f6039ebf2cac82284a42349ef8a9a61942c91be70f93c08cde` |

## Final architecture / summary

| Artifact | SHA-256 |
|---|---|
| `eval/results/final_architecture_decision_v1.md` | `d3aa604ad216e17c48519407f332981b99aef2f7e733afcb7e923de60c76dc28` |
| `eval/results/final_research_summary_v1.md` | `31551d2f5a5e552d02fdd8b0c8d244bf43abf8dc235c4640483051fdbc1ffe63` |
| `eval/results/final_results_table_v1.json` | `7af09fddaff35262ad8666e3076ce4f9e34359f6a5635d2e839819b8c0a64ee7` |
| `eval/results/gradual_delivery_narrative_v1.md` | `fbf6b8bd2082e7a1cf371431992e17f686e01ef3e16996aca075f6720c0da97d` |
| `README.md` (pre-editorial snapshot) | `d0994d93b02fc40aabbd1856753a3ea4e1dacbbf75bf5c5848fccb6e4749dc92` |

The current README and reader-facing figures were redesigned after this frozen research snapshot; this historical README hash is retained for provenance and is not a checksum of the current file.

## Reranker transfer evidence

`eval/results/reranker_transfer_summary.md` (MiniLM-Top5 vs BGE-Top5); machine-readable source `eval/results/reranker_transfer_results.json`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m eval.run_stage0_replay --check
.\.venv\Scripts\python.exe -m eval.run_validation --report
```

Archived provenance and process evidence: `eval/archive/` (see `eval/archive/MANIFEST.md`).
