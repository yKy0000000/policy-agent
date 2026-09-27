# eval/legacy/archive — Provenance & Process Evidence

This directory holds research **process evidence** that the final conclusions depend on but that a normal reader does not need. It is intentionally outside the active evaluation workflow.

## Structure

```text
eval/legacy/archive/
├── MANIFEST.md          # this file
├── stage0/              # (reserved) Stage 0 freeze pointers
├── human_truth/         # Human Truth process evidence
├── a1_execution/        # (reserved) A1 execution pointers
├── a1_reviews/          # (reserved) A1 review pointers
└── exploratory/         # abandoned exploration artifacts
```

## Physically moved here

| File | Origin | Why archived |
|---|---|---|
| `human_truth/human_truth_review_assistant_v1.json` | `eval/results/` | Human-review process input; final truth is `frozen_human_verdicts_v1.json` |
| `human_truth/human_truth_review_assistant_summary.md` | `eval/results/` | process summary |
| `human_truth/human_truth_dual_review_summary.md` | `eval/results/` | dual-review process summary |
| `exploratory/candidate_discovery_v1_reviewer_packet_VAL001039F02.md` | `eval/results/` | abandoned exploration review packet |
| `exploratory/candidate_discovery_v1_reviewer_packet_VAL001050F01.md` | `eval/results/` | abandoned exploration review packet |
| `exploratory/candidate_discovery_v1_reviewer_response_form.md` | `eval/results/` | abandoned exploration response form |

These had **zero references** from `tests/`, any runner, or `README.md`.

## Archived "in place" (manifest-only, not moved)

Most research provenance is still referenced by runners imported in `tests/test_eval.py`, so those files stay at their original paths. The earlier cleanup inventory is preserved at `eval/legacy/cleanup_inventory_v1.md` (Category 3). Examples:

- Human Truth process: `eval/results/human_truth_disagreements_v1.json`, `human_truth_reviewer1_v1.json`, `human_truth_reviewer2_v1.json`, `human_truth_stage0_worksheet.json`.
- A1 process: `eval/results/a1_blind_answer_eval_v1.json`, `a1_blind_judge_cache_v1.json`, `a1_blind_answer_mapping_v1.json`, `a1_blind_human_resolution_v1.json`, `a1_failure_inventory_raw_v1.json`, `a1_representation_probe_v1.json`.
- Stage 0 / execution: `eval/results/a0_bge_rerank_orders.json`, `stage0_replay_results.json`, `query_aware_stage1_dry_run.json`, `query_aware_stage1_live_journal.jsonl`, `eval/query_aware_stage1_live_freeze.json`, `eval/query_aware_stage1_live_reconciliation_freeze.json`.
- Abandoned exploration runners/results: measurement-validity, oracle-repair, decision/execution-coupling, semantic-gap, task-conditioned-action, reranker-ab.

## Frozen configs (kept in place, `eval/`)

`eval/query_aware_arms_v1.json`, `eval/query_aware_router_v1.json`, `eval/query_aware_stage0_config.json`, `eval/economics_contract_v1.md`, `eval/human_truth_contract_v1.md`, `eval/human_truth_stage1_preregistration_v1.md`.

## Rule

Preserve anything a final decision depended on (frozen experiment provenance, human review provenance, generation provenance). See `eval/legacy/cleanup_inventory_v1.md` §E for the earlier cleanup snapshot.
