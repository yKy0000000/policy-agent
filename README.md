# GitHub 政策问答 Agent

GitHub 政策问题常常不是单事实问答：一个完整答案可能同时需要一般规则、适用条件、例外和处理流程。这个项目用 [`github/site-policy`](https://github.com/github/site-policy) 语料回答问题，核心问题是：**系统能否找到、选入并真正用上用户需要的每一项证据，同时避免没有收益的复杂度和延迟？** 它会基于来源生成回答，证据不足时明确说明，并校验引用 ID 与来源元数据。

> **真实案例 `VAL-001-046`：**用户问，调查人员索取账户数据时 GitHub 会不会先通知自己，何时可能不通知或延迟通知。完整回答还需要区分法律或法院禁令、披露前提供法律文书副本以便提出异议，以及紧急情况下延迟通知的条件。研究答案提到了**账户数据请求**的通知和法律禁令，却没有说出后两项；其支持段落没有进入原问题的候选证据池。这说明“找到相关文本”和“答全问题”之间还有多道关口。[逐题失败复盘](eval/results/a1_failure_analysis_summary.md) · [冻结答案与评测](eval/results/a1_blind_answer_quality_frozen_summary.md)

## 系统如何回答

```text
用户问题 → 必要时改写多轮对话问题
         → lexical Top20 + semantic Top20 → 合并并按 chunk ID 去重
         → cross-encoder rerank → fixed Top5 证据
         → 基于证据生成回答 → 确定性引用与输出校验
```

仓库当前可执行默认值是 **MiniLM + fixed Top5**。[Agent 入口](src/agent.py) · [Reranker 默认值](src/reranker.py)

## 如何定位一次漏答

以开头的问题为例，评测分别检查四件事，而不把“答案看起来合理”当成唯一信号：

- **Candidate availability：**支持事实的来源是否进入关键词与语义检索的候选并集？Validation V1 中为 **235/239** 个原始 rubric facts；这是检索诊断，不是答案准确率。[候选证据分析](eval/results/evidence_geometry_summary.md)
- **Context coverage：**用户必需信息的证据是否进入生成上下文？研究用 fixed Top5 时为 **193/208** 个 `QUERY_REQUIRED` aspects。
- **Answer coverage：**最终答案是否真的说出这些必需信息？fixed Top5 的冻结评测为 **196/208**。
- **Complete case：**一道题的全部必需信息是否都被回答？fixed Top5 为 **43/50** 题；漏一项也不算完整。[A1 冻结质量](eval/results/a1_blind_answer_quality_frozen_summary.md)

这里有**两种分母**：239 个 *original rubric facts* 用来诊断来源事实能否检索、排序；其中经 **Frozen Adjudicated Labels V1** 判定的 208 个 `QUERY_REQUIRED` 信息点用于上下文和答案评测。候选覆盖、Top5 覆盖、上下文覆盖、答案覆盖并非同一批对象的逐层准确率漏斗；**235/239、224/239、193/208、196/208 不能直接相减**。Context 与 answer 也由独立判定，不能用 193→196 推断生成“增加了三个事实”。[裁决口径](eval/human_truth_contract_v1.md) · [冻结标签](eval/results/frozen_human_verdicts_v1.json)

## 失败案例怎样改变工程决策

### 1. 检索接近饱和后，先看排序与证据选择

50 题中有 **49/50** 题的原始事实支持证据已全部进入候选池；扩大所有问题的检索深度不是优先选项。相同候选池上，BGE 将原始事实的 Top5 覆盖从 MiniLM 的 **211/239 提升至 224/239**。早期答案 rubric 下的迁移检查也得到 answer macro **0.866→0.920**、完整题 **36→38**，因此 BGE 成为后续实验的共同**研究基线**。[Reranker A/B](eval/results/reranker_ab_summary.md) · [答案迁移检查](eval/results/reranker_transfer_summary.md)

**36/38 是早期协议，不能与后来 208-aspect 盲评的 43/50 串成累计提升曲线。** `VAL-001-046` 也提醒我们：整体候选覆盖接近饱和，不代表每一道复合问题都已找到所有来源。

### 2. 更大上下文有时有用，但 query router 没有赢得默认位置

`VAL-001-006` 问部分仓库内容的版权投诉该如何写，包括让 GitHub 定位材料的 URL，以及受影响者如何补救。A1 中，URL 这一必需信息的证据排在 **第 6 名**：fixed Top5 漏掉它，更深的策略选入并答出它。由问题决定证据预算，因此是一个合理的待检验假设。[失败复盘](eval/results/a1_failure_analysis_summary.md)

研究冻结了 SIMPLE/BROAD router，并与无需 query 分类的证据 selector、无 router 的 adaptive 策略及 fixed Top5 配对比较；156 个独立答案先做隐藏策略标签的评测，再合并成本。[Stage 0 冻结记录](eval/query_aware_stage0_freeze.md) · [A1 决策](eval/results/a1_final_decision_v1.md)

![A1 策略：selector 以更低成本和风险达到 router 的答案质量](eval/reports/research_v1/figures/router_decision_zh.png)

Selector 与 router 都覆盖 **196/208** 个必需信息点、完成 **44/50** 题；但 selector 使用 **3,281** 而非 **3,668 tokens/query**，确认的完整题回归为 **0 对 1**，correctness/grounding 问题为 **1 对 2**。按冻结规则，`coverage_selector_v2` 严格支配 `query_router_v1`，所以这条 router 的结论是 **KILL**。这只针对当前规则和开发集，不说明所有 router 都无效。

Selector 相对 fixed Top5 **多答出一项、又漏掉另一项**，多用约 **29.5%** tokens；fixed Top5 保持 **2,533 tokens/query、43/50 完整、0 个确认回归**。无 router 的 adaptive 策略达到 **202/208、46/50**，却需 **6,189 tokens/query**（约 **2.44 倍**）且有一题回归。这些 tokens/query 是各策略独立服务问题的 provider-token 口径，并非实验共享缓存后的实际支出。复杂机制能提高某些结果，但这轮证据不足以让它们取代最简单的默认策略。[最终 Pareto](eval/results/a1_final_pareto_v1.json)

### 3. 离线质量更高，仍不足以成为运行默认值

BGE 是有价值的**质量导向研究候选方案**。但同一历史评价协议下的配对比较虽从 MiniLM 的 **40/50** 完整题升至 **42/50**，也出现 **4 题完整答案回归**；同输入、CPU warm rerank 的 p95 从 **2.55 秒**升至 **14.78 秒**，约 **5.80 倍**。两项均未通过预注册的晋升门槛，故 runtime default 继续是 **MiniLM + fixed Top5**。这组 40→42 也不能与 A1 盲评的 43/50 当作同协议增益。[运行决策与测量边界](eval/reports/runtime_reranker_decision_v1.md)

### 4. 少数真实失败值得研究，不等于要增加默认分支

剩余失败复盘涉及 **10 题、16 个**在至少一种 A1 策略中漏掉的必需信息点：**6 个**证据已在 context 但答案未用，**6 个**是选择或预算问题，**2 个**排序偏弱，另 **2 个**集中在 `VAL-001-046` 的原问题表述失效；确认的 chunk fragmentation 为 **0**。[失败分类](eval/results/a1_failure_analysis_summary.md)

在 `VAL-001-046` 的离线、同为五个 chunk 的机制验证中，单纯加深原问题检索只能把目标来源放在 **91 个候选中的 BGE 第 79 名**；按用户问题拆出的 requirement query 则将它排到**第 2 名**并选入，使*必需信息的证据覆盖*从 **0/4 到 4/4**。这验证了该例的检索机制，**没有重新生成答案，也不是端到端质量提升**。明确的此类失败只有 **1/50** 题，因此 decomposition 保留为研究选项，不进入默认路径；hierarchical/parent expansion 缺少确认的 fragmentation 触发条件，未测试。[A2 机制验证](eval/results/a2_minimal_mechanism_probe_summary.md)

![VAL-001-046：requirement-query 检索使缺失证据进入 Top5](eval/reports/research_v1/figures/decomposition_case_zh.png)

## 测量审计：为什么还要校准答案 judge

初期 331 条标签（Validation V1 与 Broad V3）由两个独立 model agents 初评，**314/331** 初始一致；其余 **17** 条由项目作者人工裁决，形成 **Frozen Adjudicated Labels V1**。这不是全面独立人工标注，也不是人类标注者一致率；历史文件中的 `human_truth` 名称仅为维持冻结哈希与复现路径。[标签来源](eval/human_truth_contract_v1.md)

> **`JC-013`：**必需信息要求说明死者的近亲、指定继承人或其他获授权者可以提出账户请求。候选答案用“authorized individual”概括申请人资格；虽在提交材料中提及是否被指定为继承人，却未明确列出可申请者类别。历史 judge 与跨家族 Sol 都判 `COVERED`，项目作者盲审判 `MISSING`：这是对**部分语义匹配**的高估。[校准报告](eval/reports/judge_calibration_v1.md)

随机样本为 **15 题 / 60 aspects**。历史 judge 与人工、Sol 与人工均 **58/60 一致**；各有 **2 个观察到的 over-credit、0 个 under-credit**。人工参考是 **AI-assisted blinded project-author review**，由**单一项目作者**作最终判定；模型间一致不等于独立真值。这个小样本只做 measurement calibration，**不是 corrected benchmark score**，不改写 196/208 或 43/50，也不能将 58/60 外推成普遍 judge 准确率。[完整审计](eval/reports/judge_calibration_v1.md)

## 最终配置与仍未证明的事

- **KEEP（运行默认）：**混合候选检索、MiniLM rerank、fixed Top5、基于证据的生成、确定性引用与输出校验。
- **RESEARCH-ONLY：**BGE reranker 是离线质量候选方案；decomposition 仅在 `VAL-001-046` 的离线检索机制中得到验证。
- **KILL / DO NOT PROMOTE：**冻结的 `query_router_v1` 被 selector 严格支配；selector 与 adaptive evidence budget 没有成为默认值；decomposition 不作为默认分支；hierarchical retrieval 未达到实验触发条件。[研究架构记录](eval/reports/research_v1/architecture_decision.md) · [runtime 决策](eval/reports/runtime_reranker_decision_v1.md)

Validation V1 在多轮诊断、选择与机制研究中已暴露，现为 **development / research benchmark**，不能再充当新架构的 fresh holdout；16 题 Broad V3 也属开发数据。**尚未执行新的外部 holdout**，也未验证真实用户问题分布、部署监控或在线反馈闭环；小样本、单作者 judge 校准同样限制了结论。确定性引用校验不保证每个论断都获得语义支持。本 Agent 提供来源明确的政策说明，不提供法律意见。[复现清单与哈希](eval/reports/research_v1/reproducibility_manifest.md) · [Evaluation framework](eval/README.md)

## 运行 Agent

需要 Python 3.12+、本地政策语料；首次建立索引会下载模型；回答问题需要兼容 OpenAI Chat Completions 的服务端点。

```powershell
git clone --depth 1 https://github.com/github/site-policy.git data/site-policy
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env  # 设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL
.\.venv\Scripts\python.exe -m src.indexing
.\.venv\Scripts\python.exe -m src.semantic_indexing --device cpu
.\.venv\Scripts\python.exe -m src.cli
```

`src.cli` 即交互 demo：输入政策问题，输入 `exit` 退出。完成设置后，可用 `python -m src.cli --debug` 查看改写后的问题、所选证据与预算。Python 入口为 `PolicySupportAgent.from_project(device="cpu").answer(question, history=[])`。

运行不需要外部模型调用的测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```
