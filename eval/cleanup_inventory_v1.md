# Cleanup Inventory v1

Snapshot after the A1–A3 research phase. **Nothing that the final result, a test, or a runner depends on was deleted.** Where provenance is not needed for daily use, it was either physically moved to `eval/archive/` (only truly orphaned files) or left in place and hidden behind this manifest (files still referenced by runners/tests).

## Method

1. Full scan of `src/`, `eval/`, `eval/results/`, `tests/`, project root.
2. Dependency scan: for every `eval/results/*` and `eval/*`, counted references from `tests/*.py`, `eval/*.py`, `eval/*.md`, and `README.md`.
3. **Key constraint found:** `tests/test_eval.py` imports every research runner (`run_oracle_repair_v1`, `run_measurement_validity_audit(_v2)`, `run_decision_execution_coupling_v1`, `run_task_conditioned_action_v1`, `run_semantic_gap_discrimination_v1`, `run_generation_utilization_eval`, `finalize_measurement_validity`, `finalize_oracle_repair`, `run_reranker_transfer_eval`, `run_evidence_eval`, `analyze_*`, `compare_rerankers`, `metrics`, `run_validation`, `run_answer_eval`, `run_query_aware_stage1(_live)`, `run_stage0_replay`). Therefore those scripts and the result files they read **cannot be moved or deleted** without breaking the suite. Per the task rule ("如果移动会导致大量代码路径失效，则不要强行移动；可以只通过 manifest 隐藏复杂度"), they are `ARCHIVE (in place via manifest)`.

## Action summary

| Action | Count | Notes |
|---|---:|---|
| KEEP | most files | production code, tests, final artifacts, test/runtime-referenced artifacts |
| CONSOLIDATE | 6 | final reader-facing artifacts in `eval/final/` built from the `*_v1` sources |
| ARCHIVE (moved) | 6 | truly orphaned process files -> `eval/archive/` |
| DELETE | 0 | no artifact passed the "one-off AND unreferenced AND no provenance value" bar |

## A. Category 1 — Final artifacts (KEEP)

| Path | Type | Purpose | Dep. by final result | Repro value | Action |
|---|---|---|---|---|---|
| `eval/results/frozen_human_verdicts_v1.json` | truth | frozen QUERY_REQUIRED Human Truth | yes | high | KEEP |
| `eval/results/a1_blind_answer_quality_frozen_v1.json` | quality | frozen A1 blind quality | yes | high | KEEP |
| `eval/results/a1_blind_answer_quality_arm_table_v1.json` | quality | frozen arm table | yes | high | KEEP |
| `eval/results/a1_final_pareto_v1.json` | decision | A1 Pareto + router KILL | yes | high | KEEP |
| `eval/results/a1_final_decision_v1.md` | decision | A1 final decision | yes | high | KEEP |
| `eval/results/a1_failure_analysis_v1.json` | analysis | residual-failure taxonomy | yes | high | KEEP |
| `eval/results/a2_minimal_mechanism_probe_v1.json` | probe | A2 mechanism probe | yes | high | KEEP |
| `eval/results/a2_minimal_mechanism_probe_summary.md` | probe | A2 summary | yes | high | KEEP |
| `eval/final/architecture_decision.md` | final | consolidated decisions | yes | high | CONSOLIDATE |
| `eval/final/research_summary.md` | final | consolidated narrative | yes | high | CONSOLIDATE |
| `eval/final/final_metrics.json` | final | validated metrics | yes | high | CONSOLIDATE |
| `eval/final/failure_analysis.json` | final | consolidated taxonomy | yes | high | CONSOLIDATE |
| `eval/final/a2_case_study.json` | final | consolidated A2 case | yes | high | CONSOLIDATE |
| `eval/final/reproducibility_manifest.md` | final | hashes/manifest | yes | high | CONSOLIDATE |
| `eval/final/figures/*` | figure | 4 figures | yes | medium | KEEP |
| `eval/a2_minimal_probe_requirements_v1.json` | config | frozen query-derived requirements | yes | high | KEEP |

## B. Category 2 — Test / runtime dependencies (KEEP in place)

Counted by the scan; representative set (all referenced by `tests/test_eval.py` or a runner):

- `eval/results/answer_eval_results.json`, `eval/results/measurement_validity_audit.json`, `eval/results/measurement_validity_audit_v2.json`, `eval/results/oracle_repair_v1_results.json`, `eval/results/oracle_repair_v1_human_scored.json`, `eval/results/semantic_gap_discrimination_v1_results.json`, `eval/results/task_conditioned_action_v1_results.json`, `eval/results/mechanism_h1/h2/h3_stage_summary.md`.
- All `eval/*.py` runners imported by tests (see Method).
- `eval/results/a0_bge_rerank_orders.json`, `eval/results/stage0_replay_results.json`, `eval/results/human_truth_stage0_worksheet.json`, `eval/results/human_aware_context_v1.json`, `eval/results/query_aware_stage1_generation_results.json`, `eval/results/query_aware_stage1_dry_run.json`, `eval/results/query_aware_stage1_live_journal.jsonl`, `eval/results/a1_blind_judge_cache_v1.json`, `eval/results/a1_blind_answer_eval_v1.json`, `eval/results/a1_blind_answer_mapping_v1.json`, `eval/results/a1_answer_review_queue_v1.json`.

Action: **KEEP** (removal breaks tests/reproducibility).

## C. Category 3 — Provenance / intermediate (ARCHIVE in place via manifest)

Referenced only by a runner or pre-registration/freeze document, not by tests or the final reader path. Kept in place because runners read them; hidden behind this manifest.

- Measurement-validity line: `measurement_validity_audit.md`, `measurement_validity_audit_human_review.md`, `measurement_validity_audit_v2.md`, `measurement_validity_audit_v2_human_review.md`, `measurement_validity_cleaned_cohort.json/.md`, `validation_mapping_audit.json`.
- Oracle-repair line: `oracle_repair_v1_*` (interviewer never needs these).
- Decision/action coupling line: `decision_execution_coupling_v1_*`.
- Semantic-gap line: `semantic_gap_discrimination_v1_*`, `repairability_stage_summary.md`, `validate_stage_summary.md`.
- Generation-utilization line: `generation_utilization_results.json`, `generation_utilization_summary.md`, `evidence_complete_answer_gap_analysis.json`, `evidence_geometry_analysis.json`, `evidence_geometry_summary.md`.
- Reranker studies: `reranker_ab_analysis.json`, `reranker_ab_summary.md`, `reranker_transfer_results.json`, `reranker_transfer_summary.md`.
- Human Truth process: `human_truth_disagreements_v1.json`, `human_truth_reviewer1_v1.json`, `human_truth_reviewer2_v1.json`.
- A1 process: `a1_blind_human_resolution_v1.json`, `a1_failure_inventory_raw_v1.json`, `a1_representation_probe_v1.json`, `a1_failure_analysis_summary.md`, `a1_blind_answer_quality_frozen_summary.md`.

Action: **ARCHIVE** (provenance value high, daily value low).

## D. Category 4 — Physically archived (ARCHIVE moved)

Truly orphaned process files (0 references from tests, runners, or README), not needed for the final result:

| Path (new) | Origin | Reason |
|---|---|---|
| `eval/archive/exploratory/candidate_discovery_v1_reviewer_packet_VAL001039F02.md` | `eval/results/` | abandoned exploration review packet |
| `eval/archive/exploratory/candidate_discovery_v1_reviewer_packet_VAL001050F01.md` | `eval/results/` | abandoned exploration review packet |
| `eval/archive/exploratory/candidate_discovery_v1_reviewer_response_form.md` | `eval/results/` | abandoned exploration response form |
| `eval/archive/human_truth/human_truth_review_assistant_v1.json` | `eval/results/` | Human Truth process input, superseded by frozen verdicts |
| `eval/archive/human_truth/human_truth_review_assistant_summary.md` | `eval/results/` | Human Truth process summary |
| `eval/archive/human_truth/human_truth_dual_review_summary.md` | `eval/results/` | dual-review process summary |

## E. Category 5 — Deleted

**None.** No file satisfied all of: one-off, no import, no test dependency, no final-provenance dependency, fully superseded, and no reproducibility value. The 6 orphaned files above were archived instead of deleted to preserve the evidence chain.

## F. Root / source / tests

| Path | Type | Purpose | Action |
|---|---|---|---|
| `src/*` | code | production modules | KEEP |
| `tests/*` | tests | unit + pipeline-boundary tests | KEEP |
| `eval/*.py` | code | evaluation runners (all imported by tests) | KEEP |
| `eval/validation/` | data | frozen benchmark + rubric + metadata | KEEP |
| `README.md` | doc | project README (rewritten this phase) | KEEP |
| `README_RESTRUCTURE_PLAN.md` | doc | restructure plan record | KEEP |
| `DEMO.md` | doc | gitignored per `.gitignore` | KEEP |

## G. Git cleanliness

- `.gitignore` already covers `.env`, `.venv/`, `__pycache__/`, `cache/*`, `data/site-policy/`, `*.log`, `DEMO.md`. No secrets, `.env`, or model cache are tracked.
- Large artifacts (`reranker_transfer_results.json` ~21 MB, `query_aware_stage1_generation_results.json` ~6.7 MB) are kept for reproducibility; they are research provenance, not production assets. `.env` was not read or printed.
