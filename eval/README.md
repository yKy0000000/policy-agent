# Evaluation workspace

## Active development

| Path | Role |
|---|---|
| `core/` | Benchmark loader, pipeline interfaces, evaluators, runner, reporting |
| `benchmarks/validation_v1/` | One canonical benchmark definition and its documentation |
| `pipelines/` | Registered pipeline configurations |
| `run_experiment.py` | Canonical experiment entry point |
| `experiments/<experiment_id>/` | New run outputs; each run owns its config, results, metrics, and summary |
| `reports/research_v1/` | Small, reader-facing consolidated result from the completed research |
| `legacy/` | Index and preserved research process evidence |

Future work follows **component → pipeline config → `run_experiment` → `experiments/<experiment_id>/`**. New experiments must not copy the historical `run_xxx.py` scripts. Those scripts are frozen research reproduction tools, unsupported as templates for development.

The completed research is preserved at local Git tag `research-complete-v1`; its identity and artifact hashes are in [`reports/research_v1/research_snapshot_v1.md`](reports/research_v1/research_snapshot_v1.md). Start with the [architecture decision](reports/research_v1/architecture_decision.md) and [research summary](reports/research_v1/research_summary.md) to read results. See the [legacy index](legacy/MANIFEST.md) to reproduce or audit old work.

## Run benchmark: Validation V1

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

## Add a pipeline

1. Implement only the needed stage class in `eval/core/product_components.py` or another small module. The interfaces are in `eval/core/pipeline.py`: rewrite, optional requirement planner, retrieval, merge, rerank, context, generate, validate. A multi-requirement planner returns `Requirement` objects; `PipelineResult.retrieval_by_requirement` preserves each query's candidates, while merged `Evidence.query_ids` records shared chunks. The same result schema supports whole-query and requirement-query paths.
2. Register its component ID in `build_live_pipeline` and add `eval/pipelines/<pipeline_id>.json`. No benchmark or evaluator code changes are needed. Keep product `src/` independent of gold labels.
3. Run `python -m eval.run_experiment --benchmark validation_v1 --pipeline <pipeline_id> --generate --evaluate --report`. Inspect the four separate metrics and per-case rows. A new answer judge uses the same QUERY_REQUIRED rubric; targeted human review is needed before calling any observed regression confirmed.
4. Compare its report against the saved fixed Top5 and selector reports. The baseline is research BGE + fixed Top5, not the repository's MiniLM production default.

The runner accepts any object with `pipeline_id` and `run(BenchmarkCase) -> PipelineResult`; tests can inject small component implementations without loading models. `Pipeline.run` passes components only query/history-derived data, never original rubric or Human Truth labels. Evaluators consume the result afterward. The framework is intentionally narrow: no workflow DSL or general plugin system.

## Legacy policy and compatibility paths

The old `eval/run_*`, `eval/results/*`, `eval/validation/*`, and historical files at `eval/` root are research provenance. They remain at their original paths because the regression suite, source hashes, and replay code refer to them. Their role and exceptions are listed in [`LEGACY_FILES.md`](LEGACY_FILES.md); the stage-oriented index is [`legacy/MANIFEST.md`](legacy/MANIFEST.md). Do not use them as new entry points. The canonical loader, `eval.core.load_benchmark("validation_v1")`, remains the sole entry to benchmark data for new work; it verifies frozen source hashes. `FrozenReplayPipeline` validates answer identity before reusing adjudicated blind judgments. New reports go under `eval/experiments/` and do not rewrite frozen A1/A2 decisions.
