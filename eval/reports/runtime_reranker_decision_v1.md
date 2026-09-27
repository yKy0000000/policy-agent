# MiniLM vs BGE：runtime 默认值决策 v1

**决策：可执行默认值保持 MiniLM + fixed Top5。** BGE 仍是质量导向的离线研究候选方案。此决策依据[冻结契约](../runtime_reranker_decision_v1_preregistration.md)，不等同于此前的 BGE 研究推荐。Validation V1 是已暴露的 development / research benchmark，不是新的确认性 holdout。

## 配对质量：相同历史协议（50 题）

历史 `reranker_transfer_results.json` 保存了两个 reranker 的生成答案和 judge 结果。这里对两组沿用同一历史 judge 协议，并在每题只保留冻结的 208 个 `QUERY_REQUIRED` IDs。它**不是**后来 A1 的 blind evaluation 协议；BGE 的 42/50 不能与 A1 的 43/50 比作模型增益。本表没有重新生成答案或调用 judge。

| 指标 | MiniLM | BGE |
|---|---:|---:|
| 共享候选池的证据可用性，早期 239-fact 诊断 | 235/239 | 235/239 |
| fixed Top5 context 支持的必需信息 | 184/208 | 193/208 |
| Context-complete 题数 | 43/50 | 46/50 |
| 答案覆盖的必需信息 | 185/208 | 195/208 |
| 完整答案题数 | 40/50 | 42/50 |
| 历史 judge 判定的矛盾论断 | 5 | 1 |

按整题完整性配对：**BGE 赢 6 题，MiniLM 赢 4 题，40 题持平**。BGE 修复 `VAL-001-027`、`-028`、`-029`、`-030`、`-032`、`-048`，但在 `VAL-001-006`、`-011`、`-033`、`-050` 引入完整答案回归。按 aspect 计算，BGE 增加 18 个、失去 8 个 `QUERY_REQUIRED` IDs。净增 2 道完整题的同时出现 **4 题**整题回归，超过冻结门槛允许的最多 1 题。208 个 aspects 聚集在 50 题内，这些差异不证明对外部问题分布的泛化。

## Runtime 测量：20 个配对 query IDs

两组使用相同原始问题 `VAL-001-001`、`-003`、…、`-039`，相同语料与索引、lexical Top20 + semantic Top20、去重候选并集、CPU、batch size 16、Torch intra/inter-op threads 8/8，以及 fixed Top5。每组在单独进程中从本地缓存加载模型一次，先运行一对不计时 warmup，再处理 20 题。BGE 从缓存的 `BAAI/bge-reranker-base` snapshot 加载，以避免向 Hugging Face 发起库元数据请求；权重和 tokenizer 仍属于该模型。两组本地 Top5 列表均与归档质量输入 **20/20 一致**。

| 测量秒数 | MiniLM | BGE |
|---|---:|---:|
| 模型构造/加载（一次，不计入请求） | 0.05 | 0.86 |
| Warm rerank mean（n=20） | 2.09 | 12.49 |
| Warm rerank p50 | 2.10 | 12.70 |
| Warm rerank p95 | 2.55 | 14.78 |
| 本地 lexical + semantic retrieval p50（不含 rerank） | 0.042 | 0.033 |
| 本地 lexical + semantic retrieval p95（不含 rerank） | 0.052 | 0.040 |

Rerank p95 比值为 **5.80×**，超过冻结的 **2.0×** 晋升上限。加载时间是在 OS 文件缓存已预热时测得的构造时间，不是首次启动的 cold-start 时间。进程内存采样器不可用，因此 RSS 为 N/A；CPU device、batch size 和线程数记录在原始输出中。

同样的每组 20 个 IDs 还进行了新的端到端调用：关闭 rewrite 与 generation 缓存，使用已配置的 `deepseek-v4-flash` endpoint、现有 grounded-answer prompt 和确定性 citation validation，且不复用冻结答案。这些只是**描述性的部署计时**，不能单独归因于 reranker：可执行 Agent 即使处理无历史的问题也调用 rewrite model，两个组也各自独立调用 rewrite/generation。在 MiniLM 组，live Top5 列表仅 **1/20** 与原问题本地运行完全匹配；BGE 组也是 **1/20**。协议偏差已记录在契约中，不会放宽决策门槛。

| 新端到端计时秒数（每组 n=20） | MiniLM | BGE |
|---|---:|---:|
| Rewrite p50 / p95 | 0.76 / 1.06 | 0.87 / 1.03 |
| Rerank p50 / p95 | 2.08 / 2.52 | 12.46 / 14.70 |
| Generation p50 / p95 | 1.90 / 2.57 | 1.98 / 2.60 |
| Total p50 / p95 | 4.78 / 5.42 | 15.18 / 16.93 |

## 决策与边界

BGE 未通过预注册的质量门槛（4 题整题回归，最多允许 1 题）和严格同输入 warm rerank latency 门槛（MiniLM p95 的 5.80×，上限 2.0×）。因此，更高的离线汇总覆盖不足以支持更改默认值。新端到端请求的 p95 也明显更高，但独立 rewrite 使其只能作为支持性描述，不能当作 reranker 的因果估计。`PolicySupportAgent.from_project()` 保持 MiniLM + fixed Top5。没有新增 RAG 机制或更改 runtime default。

Validation V1 早期具有 holdout 价值，后来经过 geometry、reranker、架构、失败与机制分析而暴露；此决策仅适用于该 development benchmark 和本次 CPU 环境。Frozen Adjudicated Labels V1 的初评来自两个独立 model agents（314/331 初始一致），另 17 条由项目作者人工裁决。本报告未校准 model judge 的独立性，也未运行新的 fresh validation。

原始输出：[`paired_quality.json`](../results/runtime_reranker_decision_v1/paired_quality.json)、[`minilm_top5_local_runtime.json`](../results/runtime_reranker_decision_v1/minilm_top5_local_runtime.json)、[`bge_top5_local_runtime.json`](../results/runtime_reranker_decision_v1/bge_top5_local_runtime.json)、[`minilm_top5_live_runtime.json`](../results/runtime_reranker_decision_v1/minilm_top5_live_runtime.json)、[`bge_top5_live_runtime.json`](../results/runtime_reranker_decision_v1/bge_top5_live_runtime.json)。

## 验证记录

原决策时 `python -m unittest discover -s tests`：**261 passed，0 failed，0 skipped**；`git diff --check`：clean。当时已有的 README 翻译和研究图片改动得到保留；该决策没有修改产品代码或默认配置。
