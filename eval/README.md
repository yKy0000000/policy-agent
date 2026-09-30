# Evaluation / Research Guide

这里是研究材料的中文导航。建议先读结论，再看对照数据和失败机制；原始冻结文件、预注册与复现输入保留在各自原路径。以下阅读顺序不改变任何实验口径。

## 从哪里开始看？

先看[主 README](../README.md)了解当前 Fast / Search+ 产品选择，再读[研究架构决策](reports/research_v1/architecture_decision.md)，最后按下面主题追到具体证据。架构决策记录的是当时的研究配置；当前产品模式以主 README 为准。

## Baseline Retrieval

先看[证据几何诊断](results/evidence_geometry_summary.md)，了解候选覆盖、Top5 排序与缺口分别是什么；再看[MiniLM / BGE 运行决策](reports/runtime_reranker_decision_v1.md)，理解离线质量与 CPU latency 的取舍。

## Answer Evaluation

先看[冻结答案评测摘要](results/a1_blind_answer_quality_frozen_summary.md)，再看[Judge 校准报告](reports/judge_calibration_v1.md)。前者是原始评测记录，后者审计小样本测量误差；校准不重算 benchmark 分数。

## Adaptive / Budget Study

从[A1 最终决策](results/a1_final_decision_v1.md)读预算策略的历史结论，再看[70 题对照中文阅读版](reports/zh/multiarm_70_summary_zh.md)中 Adaptive 的总体质量与 provider token 代价。当前 Search+ 的 Adaptive 实现与历史对照臂的配置边界见主 README。

## Router Exploration

先读[Router V1 中文阅读版](reports/zh/router_v1_report_zh.md)，再读[V1.1 证据诊断中文阅读版](reports/zh/router_v1_1_report_zh.md)。前者比较 Direct、Decompose 与 Router；后者追查新证据是否真的补到必需信息。

## 70-Query Comparative Snapshot

读[70 题对照中文阅读版](reports/zh/multiarm_70_summary_zh.md)，需要逐题表格与完整方法时返回[原始冻结摘要](results/multiarm_70/multiarm_70_summary.md)。50 题和 20 题来自不同 cohort；合并只提供工程对照，不是新的独立 holdout。

## Failure / Mechanism Analysis

先看[A1 失败归因](results/a1_failure_analysis_summary.md)，再看[A2 最小机制验证](results/a2_minimal_mechanism_probe_summary.md)。单个 requirement-query 案例说明 decomposition 可能补回证据，但不足以支持默认启用。

## Final Controller Gate / Research Closure

最后一次架构门槛已完成，决策为 **STOP**：12 个冻结 BGE context/draft 输入、每题两次，共 24 个 non-oracle sensor 调用；PATCH 0/2、REFRESH 0/3 稳定发现。没有执行后续动作、E2E 或实现 Controller，当前 Fast（MiniLM + fixed Top5）和 Search+ 保持不变。

先读[归档导航及 release 澄清](reports/final_controller_gate_v1/README.md)，再看[最终报告](reports/final_controller_gate_v1/final_report.md)、[机器决策](reports/final_controller_gate_v1/decision.json)和[逐调用原始结果](reports/final_controller_gate_v1/gate1_sensor_results.json)。`009-F01`、`022-F02` 的 canonical A1 与 generation-utilization judge 分歧保留为 secondary，不进入主正例分母；`039-F02` 为 optional，不能改写成 required failure。

`run_final_controller_gate_v1.py` 是原实验的归档脚本，不是新的产品入口。该 release 只进行无网络归档完整性检查与现有测试，不重新运行 sensor、不重建 eligibility、不重新生成报告。本项目架构研究已封板；下方通用 runner 说明用于理解和审计现有工具，不授权继续本项目架构实验。

## Reproducibility & Frozen Artifacts

需要核对研究身份时读[复现清单](reports/research_v1/reproducibility_manifest.md)，再查[Router V1 freeze manifest](router_v1_freeze_manifest.json)及[历史材料索引](legacy/MANIFEST.md)。中文阅读版只解释原始结果，不属于 frozen identity；请以原始文件和 manifest 为审计依据。

Final Controller Gate 的原始文件身份另见[归档校验和](reports/final_controller_gate_v1/archive_checksums.json)。归档检查无需 `.env`、LLM endpoint 或本地运行 cache：`python -m unittest discover -s tests -p test_final_controller_gate_v1.py`。原报告中的 planned-call 计数、latency 分位数及历史摘要勘误见[release 澄清](reports/final_controller_gate_v1/README.md)。

## 评测工作区与运行说明

## 当前开发入口

| 路径 | 用途 |
|---|---|
| `core/` | Benchmark loader、pipeline 接口、evaluators、runner、reporting |
| `benchmarks/validation_v1/` | 唯一的 canonical benchmark 定义及说明 |
| `pipelines/` | 已注册的 pipeline 配置 |
| `run_experiment.py` | Canonical 实验入口 |
| `experiments/<experiment_id>/` | 新运行的输出；各自保存 config、results、metrics 与 summary |
| `reports/research_v1/` | 已完成研究的精简可读汇总 |
| `legacy/` | 保留的研究过程证据及索引 |

后续工作遵循 **component → pipeline config → `run_experiment` → `experiments/<experiment_id>/`**。新实验不要复制历史 `run_xxx.py` 脚本；它们是冻结研究的复现工具，不是新的开发模板。

已完成的研究保存在本地 Git tag `research-complete-v1`；身份与 artifact 哈希见 [`reports/research_v1/research_snapshot_v1.md`](reports/research_v1/research_snapshot_v1.md)。阅读结果可先看[架构决策](reports/research_v1/architecture_decision.md)和[研究摘要](reports/research_v1/research_summary.md)；复现或审计旧工作则看 [legacy 索引](legacy/MANIFEST.md)。

## 运行 benchmark：Validation V1

离线历史 replay **不调用模型或 judge**。它将冻结的候选排序、所选 context、答案、判定和各 arm 的 provider usage 导入与未来 live pipelines 相同的结果 schema：

```powershell
python -m eval.run_experiment --benchmark validation_v1 --pipeline bge_fixed_top5 --offline --evaluate --report
python -m eval.run_experiment --benchmark validation_v1 --pipeline bge_coverage_selector_v2 --offline --evaluate --report
```

每条命令新建 `eval/experiments/<timestamp>_<pipeline>_frozen_replay/`，其中含 `config.json`、`pipeline_results.json`、四个独立 metric 文件和 `summary.md`。用 `--experiment-id <name>` 可指定稳定的目录名；已有且非空的目录不会被覆盖。

`--generate` 改用 live component adapters，而非冻结行；它需要本地索引、模型和 `src/` 所用的 `.env` endpoint。加上 `--evaluate` 后，生成答案使用现有 answer-judge prompt/schema 评测，缓存位于冻结研究文件之外的 `eval/experiments/judge_cache.json`。**新的 live judge 结果不是人工确认的 regression**：报告区分 candidate complete regressions 与 confirmed regressions。`--report` 或 `--evaluate` 都不会隐含触发 `--generate`。

## Benchmark 与指标口径

`eval.core.load_benchmark("validation_v1")` 校验哈希后加载 50 道原始问题及 IDs。Case 对象分别保存 **239 个早期来源/rubric facts** 和 **208 个 QUERY_REQUIRED Frozen Adjudicated Labels V1 aspects**，以及支持来源记录和 chunk IDs。V1/V3 标签由两个独立 model agents 初评，314/331 初始一致；另 17 条由项目作者人工裁决。历史 `human_truth` 文件名为复现保持不变；loader 不重新生成或裁决标签。Validation V1 现在是 development / research benchmark，不是 fresh holdout。

| 层级 | 分母 | 要回答的问题 | 主要字段 |
|---|---|---|---|
| Retrieval | 239 个原始 facts | 支持 chunk 是否进入 candidate union 或 BGE Top5？ | `candidate_available`、`candidate_complete_cases`、`ranked_top5`、各 fact 最佳 rank |
| Context | 208 个 QUERY_REQUIRED aspects | 必需来源是否进入选定的 generator evidence？ | `required_covered`、`context_complete_cases`、evidence tokens |
| Answer | 208 个 QUERY_REQUIRED aspects | 最终答案是否说出必需信息？ | `required_covered`、`query_required_complete_cases`、candidate/confirmed regressions、grounding diagnostics |
| Economics | pipeline provider usage | 该 arm 消耗了什么？ | input/output/total tokens、tokens/query、evidence tokens、estimated cost、已测量的 live latency |

Retrieval availability、context coverage 和 answer coverage 是不同测量，分子分母不能互换。冻结 replay 没有可比较的 live latency，也没有历史 lexical/semantic component scores；这些字段保持 `null`，不伪造数值。Replay 的美元成本采用历史各 arm 的 counterfactual accounting，不是实验实际支出；judge tokens 不计入 pipeline economics。

保存的 regression 参考为 [`historical_fixed_top5_v1/summary.md`](experiments/historical_fixed_top5_v1/summary.md) 和 [`historical_selector_v2_v1/summary.md`](experiments/historical_selector_v2_v1/summary.md)。两者均复现 candidate availability **235/239**、BGE Top5 **224/239**。Fixed Top5 复现 context **193/208、46/50**，answer **196/208、43/50**，provider tokens/query **2,533.12**；selector 复现 context **195/208、47/50**，answer **196/208、44/50**，tokens/query **3,281.06**。最终研究表将 token 均值四舍五入至一位小数。

后续的 [MiniLM vs BGE runtime 决策](reports/runtime_reranker_decision_v1.md)通过配对的历史 208-aspect 再分析及 warm CPU 计时，保留 MiniLM 为可执行默认值。它的历史 judge 协议不同于 A1 blind evaluation，不能把两者的完整题数串成系统提升曲线。新的端到端计时包含独立在线 rewrite/generation 调用，严格的同输入 rerank 对比才隔离了 reranker 本身。

## 添加 pipeline

1. 只在 `eval/core/product_components.py` 或其他小模块中实现需要的 stage class。接口见 `eval/core/pipeline.py`：rewrite、可选 requirement planner、retrieval、merge、rerank、context、generate、validate。多要求 planner 返回 `Requirement` 对象；`PipelineResult.retrieval_by_requirement` 保留各 query 的候选，合并后的 `Evidence.query_ids` 记录共享 chunks。相同结果 schema 支持整个 query 与 requirement-query 两种路径。
2. 在 `build_live_pipeline` 注册 component ID，新增 `eval/pipelines/<pipeline_id>.json`。无需更改 benchmark 或 evaluator 代码；产品 `src/` 应与 gold labels 保持独立。
3. 运行 `python -m eval.run_experiment --benchmark validation_v1 --pipeline <pipeline_id> --generate --evaluate --report`，查看四份独立 metrics 和逐题结果。新 answer judge 沿用 QUERY_REQUIRED rubric；把观察到的 regression 称为 confirmed 前，需要有针对性的人工复核。
4. 将报告与已保存的 fixed Top5、selector 报告比较。研究 baseline 是 BGE + fixed Top5，不是仓库的 MiniLM production default。

Runner 接受任意具备 `pipeline_id` 与 `run(BenchmarkCase) -> PipelineResult` 的对象；测试可注入小型组件，而无需加载模型。`Pipeline.run` 只向组件传递来自 query/history 的数据，不传递原始 rubric 或裁决标签；evaluators 在结果生成后才使用它们。框架刻意保持窄范围：没有 workflow DSL 或通用 plugin 系统。

## Legacy 文件与兼容路径

旧 `eval/run_*`、`eval/results/*`、`eval/validation/*` 及 `eval/` 根目录历史文件属于研究 provenance。Regression suite、来源哈希和 replay 代码依赖这些原路径，因此予以保留。角色和例外见 [`LEGACY_FILES.md`](LEGACY_FILES.md)；分阶段索引见 [`legacy/MANIFEST.md`](legacy/MANIFEST.md)。不要将它们用作新入口。`eval.core.load_benchmark("validation_v1")` 是新工作读取 benchmark 数据的唯一 canonical loader，会验证冻结来源哈希。`FrozenReplayPipeline` 在复用裁决后的 blind judgments 前验证答案身份。新报告写入 `eval/experiments/`，不改写冻结的 A1/A2 决策。
