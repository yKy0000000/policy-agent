# GitHub Policy Support Agent

一个以 GitHub 官方 [`github/site-policy`](https://github.com/github/site-policy) 为唯一政策语料的问答 Agent。项目支持单轮与多轮提问，通过词法检索、语义检索、Cross-Encoder 重排和受证据约束的生成，返回带可验证来源映射的回答；当现有政策证据不足时，系统会明确说明无法确定，而不是补造事实。

实现是一条固定、可测试的 deterministic workflow：

```text
conversation
→ contextual rewrite
→ lexical + semantic candidate retrieval
→ Cross-Encoder reranking
→ evidence selection
→ grounded answer generation
→ citation validation
→ CLI
```

它不是 autonomous agent loop，没有 planner 或动态工具选择。这里的 “Agent” 指封装多轮上下文和多阶段能力的高层接口，不意味着必须使用 LangChain / LangGraph 或自治循环。

## Key Results

**Untouched Validation V1** —— 50 条 untouched broad queries、239 required atomic facts、38 份 policy documents。strategy 与 rubric 在首次运行前冻结，并按 preregistered quality gates 评估：

| Strategy | Grounded micro fact coverage | Grounded fact-complete | Evidence tokens |
|---|---:|---:|---:|
| Always V1 (`adaptive_prefix_v1`) | 0.891 | 39/50 | 176,464 |
| Frozen adaptive stopping rule | 0.883 | 38/50 | 160,764 |

- Grounded micro regret = 0.008（preregistered limit 0.02）→ PASS
- Grounded fact-complete deficit = 1（preregistered limit 1）→ PASS
- Unsupported + contradicted claims：V1 = 2，frozen adaptive = 2，没有增加 → PASS
- Evidence token saving = **8.9%**（这是 50-case untouched validation 上的正式泛化结果）
- **Validation V1: PASS under preregistered quality gates**

**Candidate required-fact coverage**：在同一 50-case Validation V1 上，候选池覆盖 235/239 required facts（grounded micro ≈ **98.3%**），49/50 cases 的 required facts 全部进入候选池。这是 candidate *required-fact coverage*，不是 retrieval accuracy。

**16-case Broad Query V3 development / diagnostic set**（92 frozen required atomic facts）：Fixed Top5 macro fact coverage 0.749 → V1 macro 0.930，fact-complete 7/16 → 12/16。

**Exploratory extension**：`Marginal-Information Dynamic-K` 在 dev set 上能用 semantic novelty 省 token，但无法可靠保留 answer-required facts，因此**不进入 production**，也没有独立 validation（见下文）。

> 全文的 coverage 指标都是 evidence / required-fact coverage，不是 answer accuracy，也不是 retrieval accuracy。

## Why this project

把一句话 policy question 变成“检索几段最相关的 policy text”是容易的；难的是 broad policy queries。

它们往往同时要求多个 conditions、exceptions、actors 和 process facts，例如“谁在什么条件下、经过哪些步骤、有什么例外”。对这类问题，**高相关 evidence 并不等于 evidence 已经足够完整**：Top5 里可能有非常相关的段落，却缺少回答所需的某个条件或例外。

项目因此从 Fixed Top5 baseline 出发，沿固定链路逐层定位瓶颈：

```text
candidate recall → ranking → evidence selection → answer utilization → grounded answer quality
```

这也是本项目与“普通 Top5 RAG”的区别：主要研究点是 **evidence selection / evidence sufficiency**，而不是把排序分数再调高一点。

## Architecture

```text
conversation history + latest question
                    │
                    ▼
        contextual query rewrite
                    │
                    ▼
       ┌────────────┴────────────┐
       │                         │
 lexical Top20              semantic Top20
 hashing-TFIDF-v4       all-MiniLM-L6-v2
       │                         │
       └──────── candidate union ┘
                    │
                    ▼
     Cross-Encoder relevance reranking
     ms-marco-MiniLM-L-6-v2 → Top5（默认）/ adaptive prefix（可选）
                    │
                    ▼
       grounded answer generation
                    │
                    ▼
     citation validation + metadata mapping
                    │
                    ▼
        answer + structured citations
```

`src/agent.py` 是唯一的高层编排入口，只负责调用顺序、数据传递、错误边界和结果组装；检索、重排、生成及引用校验由各自模块实现。

```python
from src.agent import PolicySupportAgent

agent = PolicySupportAgent.from_project(device="cpu")
result = agent.answer("When can GitHub suspend an account?", history=[])

print(result.answer)
print(result.citations)
```

Evidence selection 有三种模式，默认固定 Top5：

- `fixed_top5`：生产默认，保留重排后的 Top5。
- `adaptive_prefix_v1`：从同一重排列表中选择确定性的连续前缀（不超过 Top20）。
- `coverage_selector_v2`：保留 Top5 后，用已有的 indexed semantic vectors 做确定性互补集合选择。

## Data preparation

语料来自本地克隆的 `github/site-policy/Policies/`：

- loader 只读取政策 Markdown，移除正文前的 YAML front matter，同时保留标题；
- chunker 先按嵌套 Markdown heading 切分，仅对过长 section 做段落感知的二次切分；
- 每个 chunk 保留 `title`、`heading_path`、`source_path`、`source_url`、`chunk_id` 和原始文本；
- 词法与语义索引使用完全相同的 chunks，embedding 输入为“文档标题 + heading path + chunk text”。

这样既保留政策条款的章节边界，也让最终 citation 可以映射回 GitHub 上的原始文件。

## Retrieval pipeline

两路召回各自取 Top20，按 chunk ID 去重合并成候选池，再由 Cross-Encoder 独立打分并排序：

- Lexical：`hashing-TFIDF-v4`
- Semantic：`all-MiniLM-L6-v2`
- Reranker：`cross-encoder/ms-marco-MiniLM-L-6-v2`

### Early 25-case source-level diagnostics

项目早期用固定的 25 个 supported cases 做 source-level retrieval diagnostic。`Hit@K` 表示前 K 条是否至少命中一个可接受来源；`MRR` 衡量第一个正确来源出现得有多靠前：

| Backend | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Lexical (`hashing-tfidf-v4`) | 0.40 | 0.68 | 0.68 | 0.5569 |
| Semantic (`all-MiniLM-L6-v2`) | 0.48 | 0.72 | 0.76 | 0.6163 |
| Candidate union + Cross-Encoder | 0.64 | 0.84 | 0.88 | 0.7569 |

无权重 Reciprocal Rank Fusion 的 hybrid 没有带来稳定提升（Hit@1 0.40 / MRR 0.5480），因此主链没有把 RRF 分数当作最终排序依据。该负实验被保留，用来说明“合并两个召回器”不等于“已经解决排序”。

必须说明：以上是**旧的 source-level retrieval diagnostic**，不是最终 retrieval accuracy，也不是 candidate required-fact coverage。它只用于早期判断主要瓶颈在 ranking，而不是 candidate recall：lexical Top20 + semantic Top20 的候选并集在 25/25 cases 中都至少包含一个可接受来源。

### Candidate retrieval

在更严格的 50-case Validation V1 上，candidate retrieval 覆盖 **235/239** 个 required policy facts（grounded micro ≈ 98.3%），49/50 cases fact-complete。也就是说，剩余失败主要发生在 **ranking / evidence selection**，而不是候选召回本身。V3 development set 上还有少数 candidate ceiling cases（某个 required chunk 未进入 Top20 候选池），这类失败不是扩大 K 能修复的。

### Multi-turn contextual rewrite

第二轮问题常含代词或省略。系统用 LLM 将 latest question 结合最近两轮 history 改写成 self-contained query，history 只用于理解上下文，不作为政策证据。这是一个 **small 4-case diagnostic**，不足以支撑强泛化结论；它仅说明 rewrite 在该小样本上优于直接拼接 history。

## Grounded answer generation & citations

生成器只接收本次选中的 reranked evidence，并要求每个实质性政策结论使用 `[S1]`…`[Sn]` 行内引用。citation ID 由程序按本次 evidence 排名分配，模型不会获得或输出来源 URL。

生成后 validator 会：

- 检查回答是否包含 citation；
- 拒绝不属于当前 evidence 的 citation ID；
- 拒绝模型直接生成的 URL；
- 用程序持有的 evidence metadata 将有效 ID 映射为 `title`、`heading_path`、`source_path`、`source_url` 和 `chunk_id`。

**这是 deterministic 的结构与来源映射校验，不是 claim-level entailment verifier。** 引用 ID 合法不代表对应 claim 已被语义证明。当前语义层面的 claim support 主要来自 model-judge 加 targeted source review，**不是 independent human gold sign-off**，README 与 `eval/results/answer_eval_summary.md` 都保留这一 limitation。

当选中 evidence 不足以回答具体问题时，生成器被要求明确说明所给政策证据没有给出所请求的信息，并引用相关背景。该 abstention 仍是一次成功回答，不会被当作 `AgentPipelineError`；技术/API 异常则按 `rewrite`、`retrieval`、`generation` 或 `citation_validation` stage 明确区分。

## Broad-query evaluation (development / diagnostic)

16-case Broad Query V3 development / diagnostic set，含 92 frozen required atomic facts。所有策略复用同一份 saved Top20 retrieval snapshot：

| Strategy | Macro fact coverage | Micro fact coverage | fact-complete | Evidence tokens |
|---|---:|---:|---:|---:|
| Fixed Top5 | 0.749 | 0.750 | 7/16 | 27,274 |
| Adaptive V1 | 0.930 | 0.935 | 12/16 | 50,530 |
| Coverage selector V2 | 0.873 | 0.880 | 10/16 | 41,134 |
| Offline Oracle | 0.930 | 0.935 | 12/16 | 40,073 |

Offline Oracle 只允许描述为 **offline upper bound using inference-time unavailable evaluation labels**，它使用 gold required-fact labels，**不是 deployable router**。

Answer quality 在同一 16-case controlled generation 上单独评估（temperature 0，统一生产 prompt）：

| Strategy | Answer macro/micro fact coverage | Grounded macro/micro | fact-complete | Grounded evidence utilization |
|---|---:|---:|---:|---:|
| Fixed | 0.800 / 0.804 | 0.800 / 0.804 | 7/16 | 97.4% |
| Adaptive V1 | 0.889 / 0.902 | 0.889 / 0.902 | 10/16 | 96.5% |
| Coverage selector V2 | 0.881 / 0.891 | 0.881 / 0.891 | 9/16 | 97.6% |

所有 citation ID 都解析到本次 evidence，claim 支撑率在 0.98 左右。主要结论是：**当 required evidence 已经进入生成上下文时，generator 的证据利用率约 96.5%，当前主要瓶颈更偏 evidence selection，而不是 generator 无法使用已经提供的 evidence。** 这些指标是 required-fact / grounded coverage，不是 model accuracy。

复现：`eval/results/eval_summary.md`（证据）、`eval/results/answer_eval_summary.md`（回答质量）。

## Untouched Validation V1

Validation V1 是本项目目前最重要的泛化证据，也是 README 最想强调的结果。

构造与冻结：

- 50 条 untouched broad queries，239 required atomic facts，38 份 policy documents；
- 由本地 policy corpus 独立构造，早于任何 validation strategy 运行；
- 16 条 V3 cases 仍属于 development data；
- strategy 与 rubric 在首次运行前冻结，SHA-256 记录在 `eval/validation/validation_v1_metadata.json`，说明见 `eval/validation/VALIDATION.md`。

Pre-registered outcome criteria：grounded micro fact-coverage regret ≤ 0.02；grounded fact-complete cases 至多比 always-V1 少 1；total unsupported/contradicted claims 不超过 V1。只有在全部 quality gates 通过后，才评估 evidence-token saving。

| Metric | Always V1 | Frozen Adaptive | Gate |
|---|---:|---:|---|
| Answer micro fact coverage | 0.912 | 0.908 | diagnostic |
| Grounded micro fact coverage | 0.891 | 0.883 | regret 0.008 ≤ 0.02 · PASS |
| Grounded fact-complete | 39/50 | 38/50 | deficit 1 ≤ 1 · PASS |
| Unsupported + contradicted claims | 2 | 2 | no increase · PASS |
| Evidence tokens | 176,464 | 160,764 | saving **8.9%** |

Stopping behavior：candidate rule 触发 Fixed 11/50、V1 39/50；safe stops = 10，false stops = 1。

**Validation V1 overall: PASS under preregistered quality gates.** 8.9% 是 50-case untouched validation 上的正式泛化结果；不要用 dev set 上的更大 saving 数字作为 headline。

Production 与 eval 的区别：候选路由规则 `minimum Top5 reranker score 2.5 → Fixed; otherwise V1` 目前是 **validated evaluation candidate / conservative stopping policy**，只存在于 `eval/adaptive_strategy_candidate.json` 和 validation 流程中，**不是生产默认 router**。生产默认仍是代码实际支持的 `fixed_top5`；`adaptive_prefix_v1` 与 `coverage_selector_v2` 需要显式启用。

## Exploratory extension: Marginal-Information Dynamic-K

Dynamic-K 是 **exploratory extension**，不是正式 validated method，也不是项目主成果。

它从 Top5 起步，根据 normalized reranker relevance、semantic novelty（1 − 与已选 evidence 的最大 cosine similarity）以及可选的 structural novelty，探索 marginal information gain，K ≤ 20、evidence tokens ≤ 6,000。

| Configuration | Macro | Micro | fact-complete | Avg K | Evidence tokens |
|---|---:|---:|---:|---:|---:|
| Fixed Top5 (baseline) | 0.749 | 0.750 | 7/16 | 5.00 | 27,274 |
| Adaptive V1 (baseline) | 0.930 | 0.935 | 12/16 | 10.25 | 50,530 |
| `additive_p2` | 0.863 | 0.870 | 9/16 | 7.38 | 38,148 |
| `product_p2` | 0.853 | 0.859 | 9/16 | 7.44 | 39,666 |
| `product_p3` | 0.879 | 0.880 | 10/16 | 10.06 | 51,548 |
| `product_section_p3` | 0.939 | 0.946 | 13/16 | 18.06 | 78,458 |

省 token 的 `additive_p2` 相对 V1 减少约 **24.5%** evidence tokens，但 micro coverage 从 0.935 降到 0.870，fact-complete 从 12/16 降到 9/16。反过来，唯一提高 coverage 的 `product_section_p3` 多花约 55% tokens，并在 10/16 cases 直接选到 K=20。

结论：**semantic novelty does not reliably equal answer-required information gain.** 因此 Dynamic-K 未进入 production、未做独立 untouched validation，只作为 exploratory / future direction。一个更 principled 的后续方向是 **requirement-aware evidence saturation**——围绕“回答所需的 requirement 是否已饱和”而不是“向量是否新颖”来决定是否继续选证据。

复现：`eval/analyze_dynamic_k.py --check`。

## Run locally

### Prerequisites

- **Python 3.12+**（依赖 `numpy==2.5.3`、`scipy` 要求 ≥ 3.12；当前测试环境为 Python 3.12.10）
- 能访问 Hugging Face 以完成首次模型下载
- 一个兼容 OpenAI Chat Completions 的 LLM endpoint；当前评估使用 DeepSeek

依赖通过 `requirements.txt` 安装。以下命令在项目根目录（`policy-agent/`）执行，Windows PowerShell 示例：

```powershell
git clone --depth 1 https://github.com/github/site-policy.git data/site-policy

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.example .env
# 在 .env 中填写 LLM_API_KEY、LLM_BASE_URL 和 LLM_MODEL
```

构建词法与语义索引：

```powershell
.\.venv\Scripts\python.exe -m src.indexing
.\.venv\Scripts\python.exe -m src.semantic_indexing --device cpu
```

CLI 以本地文件模式加载 reranker。首次使用前，用现有 reranked eval runner 下载模型并验证索引：

```powershell
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend reranked --allow-reranker-download
```

启动聊天：

```powershell
.\.venv\Scripts\python.exe -m src.cli
```

默认模式输出回答和由 `AgentResult.citations` 提供的结构化来源。调试模式额外显示 rewritten query、选中的 reranked evidence、证据预算，以及 rewrite/generation 的 API 或 cache 来源：

```powershell
.\.venv\Scripts\python.exe -m src.cli --debug
.\.venv\Scripts\python.exe -m src.cli --adaptive-evidence --debug
.\.venv\Scripts\python.exe -m src.cli --evidence-mode coverage_selector_v2 --debug
```

`--adaptive-evidence` 是 `adaptive_prefix_v1` 的别名，不能与冲突的 `--evidence-mode` 同时使用。输入 `exit` 或 `quit` 退出；也可以使用 `Ctrl+C` 或 EOF。对话 history 只保存在当前进程中，只有成功轮次会被追加。

## Tests and evaluation commands

### Tests

项目使用标准库 `unittest`，不是 pytest：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Evaluation runners

```powershell
# 早期 source-level retrieval diagnostics（lexical / semantic / hybrid 负实验 / 最终重排）
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend lexical
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend semantic
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend hybrid
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend reranked

# 端到端回答评估（需要 LLM endpoint 或已有 cache）
.\.venv\Scripts\python.exe -m eval.run_answer_eval

# V3 controlled generation + blinded answer-quality evaluation（需要 LLM，缓存可续跑）
.\.venv\Scripts\python.exe -m eval.run_answer_eval --broad-v3

# 冻结的 Broad Query V3 证据 baseline（纯离线，只读 saved inputs）
.\.venv\Scripts\python.exe -m eval.run_evidence_eval --check

# 离线 dev-set 候选策略信号分析（不触发检索、生成或 API）
.\.venv\Scripts\python.exe -m eval.analyze_strategy --check

# 离线 Marginal-Information Dynamic-K 分析（不读 Validation V1，不调用 LLM）
.\.venv\Scripts\python.exe -m eval.analyze_dynamic_k --check

# Untouched Validation V1：prepare / report 完全离线；generate / judge 需要 LLM
.\.venv\Scripts\python.exe -m eval.run_validation --prepare
.\.venv\Scripts\python.exe -m eval.run_validation --report
```

- `eval.run_evidence_eval --check` 只验证 `eval/results/evidence_eval.json` 与冻结输入一致，不运行 retrieval / reranking / generation。
- `eval.analyze_strategy --check` 与 `eval.analyze_dynamic_k --check` 是纯离线复现，不调用外部 API。
- `run_answer_eval`（默认与 `--broad-v3`）以及 `run_validation --generate` / `--judge` 需要 `.env` 中的 LLM endpoint 或本地 cache；默认结果写入 `eval/results/`。

## Project layout

```text
policy-agent/
├── data/site-policy/            # upstream policy clone（ignored）
├── cache/                       # indexes、model cache、LLM / generation / judge cache（ignored）
├── eval/
│   ├── run_retrieval_eval.py    # early source-level retrieval diagnostics
│   ├── run_answer_eval.py       # end-to-end + Broad Query V3 answer evaluation
│   ├── run_evidence_eval.py     # frozen V3 evidence baseline check
│   ├── run_validation.py        # Untouched Validation V1 pipelines
│   ├── analyze_strategy.py      # offline dev-set signal study
│   ├── analyze_dynamic_k.py     # offline exploratory Dynamic-K study
│   ├── metrics.py               # label-based evidence metrics
│   ├── PROVENANCE.md            # V3 benchmark / rubric provenance and hashes
│   ├── validation/              # untouched validation data, rubric, metadata, results
│   └── results/                 # frozen summaries and machine-readable results
├── src/
│   ├── ingest.py                # policy loader
│   ├── chunking.py              # heading-aware chunking
│   ├── indexing.py              # lexical index
│   ├── semantic_indexing.py     # dense semantic index
│   ├── retriever.py             # lexical retrieval
│   ├── semantic_retriever.py    # semantic retrieval
│   ├── hybrid_retriever.py      # RRF negative experiment
│   ├── reranker.py              # Cross-Encoder scorer
│   ├── reranked_retriever.py    # candidate union + reranking
│   ├── evidence_budget.py       # deterministic adaptive prefix selection
│   ├── evidence_selector.py     # deterministic complementary set selection
│   ├── conversation.py          # contextual query rewrite
│   ├── generator.py             # grounded generation + citation validation
│   ├── agent.py                 # deterministic orchestration
│   └── cli.py                   # in-process multi-turn CLI
└── tests/                       # unit and pipeline-boundary tests
```

## Known limitations

- 回答受本地 `github/site-policy` 快照限制；上游政策更新后需要重新拉取语料并构建索引。
- contextual rewrite 与 answer generation 依赖外部 LLM API；本地 cache 只覆盖已经成功请求过的相同输入。
- semantic encoder 与 Cross-Encoder 首次需要下载模型，CPU 上的初始化与重排存在延迟。
- `citation validation` 只保证 citation ID 合法、无模型生成 URL、metadata 映射来自当前 evidence，**不证明每项 claim 都被语义支持**；semantic claim support 目前依赖 model-judge 加 targeted review，不是 independent human gold sign-off。
- 16-case V3 与 small 4-case multi-turn 都是 development / diagnostic，不是 population estimate；主要泛化证据是 50-case Untouched Validation V1。
- 候选池存在 ceiling：少数 case 的 required chunk 未进入 Top20，任何 evidence-selection 策略都无法修复。
- 默认 Top5 evidence 仍可能漏掉相关 section；adaptive / coverage 选择器也只能从已进入候选池的证据中选择，并增加上下文与生成输入成本。
- deterministic matcher / detector 可能产生 false positive 或 false negative，因此 answer evaluation 仍保留人工 / targeted review 环节。
- CLI history 仅存在于当前进程，没有持久化会话或 Web UI。
- 本项目提供政策语料检索与解释，不构成法律意见。

## Takeaway

在 broad policy queries 上，把正确 chunk 召回进候选池并不难（Validation V1 candidate required-fact coverage ≈ 98.3%）；真正困难的是**判断证据是否已经足够完整**。项目用固定、可复现的 pipeline 与 untouched validation 表明：deterministic 的 evidence selection 可以在不损失 grounded coverage 的前提下减少约 8.9% evidence tokens（Validation V1 PASS），而单靠 semantic novelty 的 Dynamic-K 无法可靠等价于“回答所需信息已饱和”。后者仍是未来的研究方向。
