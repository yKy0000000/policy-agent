# Compatibility-only historical files

The active workflow is `core/` + `benchmarks/` + `pipelines/` + `run_experiment.py` + `experiments/`. The files below remain at the `eval/` root or in their original directories for frozen research reproduction. They are not templates for new experiments.

## Historical Python runners at `eval/` root

These modules are imported by the existing regression suite, by other historical modules, or invoked through their old `python -m eval.<module>` path. Relocating them would change imports, root-relative paths, and replay commands across the frozen evidence chain.

- Core historical helpers: `metrics.py`, `run_validation.py`, `run_retrieval_eval.py`, `run_evidence_eval.py`, `run_answer_eval.py`, `run_generation_utilization_eval.py`.
- Stage 0 / Human Truth: `run_stage0_replay.py`, `finalize_human_truth_v1.py`.
- Reranker and validity: `compare_rerankers.py`, `analyze_dynamic_k.py`, `analyze_evidence_geometry.py`, `analyze_strategy.py`, `run_reranker_transfer_eval.py`, `run_measurement_validity_audit.py`, `run_measurement_validity_audit_v2.py`, `finalize_measurement_validity.py`, `run_oracle_repair_v1.py`, `finalize_oracle_repair.py`.
- A1/A2 and exploratory: `run_a1_blind_answer_eval.py`, `run_query_aware_stage1.py`, `run_query_aware_stage1_live.py`, `run_decision_execution_coupling_v1.py`, `run_semantic_gap_discrimination_v1.py`, `run_task_conditioned_action_v1.py`.

`run_experiment.py` is the only entry point for new runs. `__init__.py` is package infrastructure.

## Historical data and documents at `eval/` root

- Frozen config and inputs: `a2_minimal_probe_requirements_v1.json`, `adaptive_strategy_candidate.json`, `answer_eval_candidates.json`, `broad_queries_v3_adjudicated.json`, `broad_query_v3_atomic_facts_frozen_candidate.json`, `query_aware_arms_v1.json`, `query_aware_router_v1.json`, `query_aware_stage0_config.json`, `query_aware_stage1_live_freeze.json`, `query_aware_stage1_live_reconciliation_freeze.json`, `query_aware_stage1_price_table_offpeak.json`, `retrieval_candidates.json`.
- Research contracts, preregistrations, and freezes: `candidate_discovery_v1_preregistration.md`, `decision_execution_coupling_v1_preregistration.md`, `economics_contract_v1.md`, `human_truth_contract_v1.md`, `human_truth_stage1_preregistration_v1.md`, `oracle_repair_v1_preregistration.md`, `PROVENANCE.md`, `query_aware_stage0_freeze.md`, `semantic_gap_discrimination_v1_preregistration.md`, `task_conditioned_action_v1_preregistration.md`.

These names and locations appear in tests, frozen manifests, old commands, or research records. Do not rename them solely to match future naming conventions.

## Historical directories retained in place

- `results/`: frozen generation, human review, A1/A2 decision evidence, replay rows, and intermediate analyses. Many individual paths are read by tests and replay loaders. The consolidated reader result is under `reports/research_v1/`; `results/` remains provenance. The prior [`legacy/cleanup_inventory_v1.md`](legacy/cleanup_inventory_v1.md) classifies the files by dependency and provenance value.
- `validation/`: the original rubric, query source, metadata, and validation document. The one canonical API for new code is `eval.core.load_benchmark("validation_v1")`, whose hashes verify these sources. Do not read an alternate worksheet directly in new benchmark code.

No historical asset met the conservative deletion test (regenerable, no decision or provenance value, and no path or test dependency). No duplicate JSON trees or symlinks were introduced.
