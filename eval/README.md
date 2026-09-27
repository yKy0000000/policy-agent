# Canonical evaluation framework

The completed A1–A3 research is preserved at local Git tag `research-complete-v1`; its identity and artifact hashes are in [`final/research_snapshot_v1.md`](final/research_snapshot_v1.md). Frozen files under `validation/`, `results/`, `final/`, and the legacy runners remain in place. New experiments use `eval/core/`, `eval/benchmarks/`, `eval/pipelines/`, and `eval/run_experiment.py`.

## Run Validation V1

Offline historical replay makes **no model or judge calls**. It imports frozen candidate orders, selected contexts, answers, judgments, and per-arm provider usage into the same result schema used for future live pipelines:

```powershell
python -m eval.run_experiment --benchmark validation_v1 --pipeline bge_fixed_top5 --offline --evaluate --report
python -m eval.run_experiment --benchmark validation_v1 --pipeline bge_coverage_selector_v2 --offline --evaluate --report
```

Each command writes a new `eval/experiments/<timestamp>_<pipeline>_frozen_replay/` directory containing `config.json`, `pipeline_results.json`, four separate metric files, and `summary.md`. Supply `--experiment-id <name>` for a stable folder name. An existing nonempty directory is never overwritten.

`--generate` uses the live component adapters instead of frozen rows. It requires the local indexes/models and `.env` endpoint already used by `src/`. Add `--evaluate` to judge generated answers with the existing answer-judge prompt/schema, cached outside frozen research files under `eval/experiments/judge_cache.json`. **A new live judge result is not a human-confirmed regression:** the report distinguishes candidate complete regressions from confirmed ones. `--generate` is intentionally never implied by `--report` or `--evaluate`.

## Benchmark and metric meanings

`eval.core.load_benchmark("validation_v1")` verifies hashes before loading 50 original queries and IDs. Its case object keeps the **239 original rubric facts** and the **208 QUERY_REQUIRED Human Truth aspects** in separate fields, with supporting source records and chunk IDs. The loader does not regenerate or re-adjudicate Human Truth.

| Layer | Denominator | Question | Main fields |
|---|---|---|---|
| Retrieval | 239 original facts | Did a supporting chunk enter the candidate union or BGE Top5? | `candidate_available`, `candidate_complete_cases`, `ranked_top5`, per-fact best rank |
| Context | 208 QUERY_REQUIRED aspects | Did a required source reach selected generator evidence? | `required_covered`, `context_complete_cases`, evidence tokens |
| Answer | 208 QUERY_REQUIRED aspects | Did the final answer state the required information? | `required_covered`, `query_required_complete_cases`, candidate/confirmed regressions, grounding diagnostics |
| Economics | pipeline provider usage | What did this arm consume? | input/output/total tokens, tokens/query, evidence tokens, estimated cost, live latency where measured |

Retrieval availability, context coverage, and answer coverage are different measures; their numerators and denominators are not interchangeable. Frozen replay has no comparable live latency and no historical lexical/semantic component scores; those fields remain `null` instead of being fabricated. USD cost uses the historical per-arm counterfactual accounting for replay, not physical experiment spend. Judge tokens are not included in pipeline economics.

The saved regression references are [`historical_fixed_top5_v1/summary.md`](experiments/historical_fixed_top5_v1/summary.md) and [`historical_selector_v2_v1/summary.md`](experiments/historical_selector_v2_v1/summary.md). Both reproduce candidate availability **235/239** and BGE Top5 **224/239**. Fixed Top5 reproduces context **193/208, 46/50**, answer **196/208, 43/50**, and **2,533.12** provider tokens/query; selector reproduces context **195/208, 47/50**, answer **196/208, 44/50**, and **3,281.06** tokens/query. The final research table rounds those token means to one decimal.

## Add a new pipeline

1. Implement only the needed stage class in `eval/core/product_components.py` or another small module. The interfaces are in `eval/core/pipeline.py`: rewrite, optional requirement planner, retrieval, merge, rerank, context, generate, validate. A multi-requirement planner returns `Requirement` objects; `PipelineResult.retrieval_by_requirement` preserves each query's candidates, while merged `Evidence.query_ids` records shared chunks. The same result schema supports whole-query and requirement-query paths.
2. Register its component ID in `build_live_pipeline` and add `eval/pipelines/<pipeline_id>.json`. No benchmark or evaluator code changes are needed. Keep product `src/` independent of gold labels.
3. Run `python -m eval.run_experiment --benchmark validation_v1 --pipeline <pipeline_id> --generate --evaluate --report`. Inspect the four separate metrics and per-case rows. A new answer judge uses the same QUERY_REQUIRED rubric; targeted human review is needed before calling any observed regression confirmed.
4. Compare its report against the saved fixed Top5 and selector reports. The baseline is research BGE + fixed Top5, not the repository's MiniLM production default.

The runner accepts any object with `pipeline_id` and `run(BenchmarkCase) -> PipelineResult`; tests can inject small component implementations without loading models. `Pipeline.run` passes components only query/history-derived data, never original rubric or Human Truth labels. Evaluators consume the result afterward. The framework is intentionally narrow: no workflow DSL or general plugin system.

## Historical research boundary

The old `eval/run_*`, `eval/results/*`, `eval/validation/*`, and `eval/archive/*` are research provenance and remain reproducible. The canonical loader references frozen source hashes rather than copying mutable labels. `FrozenReplayPipeline` reads historical rows and validates answer identity before reusing adjudicated blind judgments. New reports are separate artifacts under `eval/experiments/`; they do not rewrite a frozen A1/A2 decision or start A3.
