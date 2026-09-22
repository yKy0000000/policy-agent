# GitHub Policy Support Agent

一个以 GitHub 官方 [`github/site-policy`](https://github.com/github/site-policy) 为唯一政策语料的问答 Agent。项目支持单轮与多轮提问，通过词法检索、语义检索、Cross-Encoder 重排和受证据约束的生成，返回带可验证来源映射的回答；当现有政策证据不足时，系统会安全地说明无法确定，而不是补造事实。

当前实现采用固定、可测试的工作流，不包含 planner、自治循环或动态工具选择。最终验收中的 single-turn、multi-turn、unsupported/abstention 和 citation-heavy 四类真实 E2E 场景均通过；全量单元测试为 59/59 通过。

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
     ms-marco-MiniLM-L-6-v2 → Top5
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

`src/agent.py` 是唯一的高层编排入口。它只负责调用顺序、数据传递、错误边界和结果组装；检索、重排、生成及引用校验仍由各自模块实现。

```python
from src.agent import PolicySupportAgent

agent = PolicySupportAgent.from_project(device="cpu")
result = agent.answer("When can GitHub suspend an account?", history=[])

print(result.answer)
print(result.citations)
```

## Data Preparation

语料来自本地克隆的 `github/site-policy/Policies/`：

- loader 只读取政策 Markdown，移除正文前的 YAML front matter，同时保留标题；
- chunker 先按嵌套 Markdown heading 切分，仅对过长 section 做段落感知的二次切分；
- 当前快照由 57 份政策文档生成 655 个 chunks；
- 每个 chunk 保留 `title`、`heading_path`、`source_path`、`source_url`、`chunk_id` 和原始文本；
- 词法与语义索引使用完全相同的 chunks，embedding 输入为“文档标题 + heading path + chunk text”。

这样既保留了政策条款的章节边界，也让最终 citation 可以映射回 GitHub 上的原始文件。

## Retrieval Experiments

检索评估使用固定的 25 个 supported cases。`Hit@K` 表示前 K 条是否至少命中一个可接受来源；`MRR` 衡量第一个正确来源出现得有多靠前。

### 1. Lexical baseline 与 semantic retrieval

| Backend | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Lexical (`hashing-tfidf-v4`) | 0.40 | 0.68 | 0.68 | 0.5569 |
| Semantic (`all-MiniLM-L6-v2`) | 0.48 | 0.72 | 0.76 | 0.6163 |

语义检索整体优于词法基线，尤其能找回措辞不同但含义接近的政策段落；词法检索仍对精确术语、标题和专有表述有互补价值。

### 2. RRF hybrid：保留的负实验

对词法与语义结果直接做无权重 Reciprocal Rank Fusion，并没有带来稳定提升：

| Backend | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Semantic | 0.48 | 0.72 | 0.76 | 0.6163 |
| RRF hybrid | 0.40 | 0.64 | 0.76 | 0.5480 |

因此最终主链没有把 RRF 分数当作最终排序依据。该实验被保留，用来说明“合并两个召回器”不等于“已经解决排序”。

### 3. Candidate recall：定位真正瓶颈

将 lexical Top20 与 semantic Top20 去重合并后，25/25 supported cases 都至少包含一个正确来源，candidate recall 为 100%。这说明两路检索适合承担高召回候选生成，而此后的核心问题是：如何把已经进入候选集的正确 chunk 排到前五。

### 4. Cross-Encoder reranker

最终系统用 `cross-encoder/ms-marco-MiniLM-L-6-v2` 对候选 query/chunk pair 重新打分，再选择 Top5 evidence：

| Pipeline | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Candidate union + Cross-Encoder | 0.64 | 0.84 | 0.88 | 0.7569 |

相较单一 semantic backend，重排显著改善了正确证据的前排位置，也验证了此前的判断：主要瓶颈在 ranking，而不是 candidate recall。

### 5. Multi-turn contextual rewrite

第二轮问题经常包含代词或省略，例如：

```text
User: Does GitHub allow dual-use malware or exploit content?
User: What if it is for security research?

Rewrite:
Does GitHub's prohibition on using the platform in direct support of unlawful
attacks that cause technical harm apply to security research?
```

所有策略都使用同一套 frozen candidate union 与 Cross-Encoder pipeline：

| Query strategy | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Latest question only | 0.50 | 0.75 | 1.00 | 0.6875 |
| Raw history concat | 0.25 | 0.50 | 0.75 | 0.4688 |
| LLM contextual rewrite | 0.75 | 1.00 | 1.00 | 0.8750 |
| Human oracle rewrite | 0.75 | 1.00 | 1.00 | 0.8750 |

直接拼接历史反而引入噪声；LLM rewrite 在当前四个多轮 case 上与 human oracle 指标一致。历史只用于理解上下文，不作为政策证据。

## Grounded Answer Generation

生成器只接收 reranked Top5 evidence，并要求每个实质性政策结论使用 `[S1]`…`[S5]` 行内引用。ID 按本次请求的 evidence 排名由程序分配，模型不会获得或输出来源 URL。

生成后，validator 会：

- 检查回答是否包含 citation；
- 拒绝不属于当前 evidence 的 citation ID；
- 拒绝模型直接生成 URL；
- 使用程序持有的 evidence metadata，将有效 ID 映射为 `title`、`heading_path`、`source_path`、`source_url` 和 `chunk_id`。

这是结构与来源映射校验，不是 claim-level entailment verifier。引用是否真正充分支撑每条自然语言主张，仍需要人工审查或更强的 claim-level evaluator。

当 Top5 evidence 无法回答具体问题时，生成器被要求明确说明已发布政策没有给出所请求的信息，并引用相关背景。该 abstention 仍是一次成功回答，不会被当作 `AgentPipelineError`；技术/API 异常则按 `rewrite`、`retrieval`、`generation` 或 `citation_validation` stage 明确区分。

## Why a Deterministic Workflow

这个任务的步骤和工具在设计时已经确定：改写查询、两路召回、候选合并、重排、生成、引用校验。固定编排比自治 agent loop 更适合当前范围，因为它：

- 让每次请求都经过相同的 grounding 与 validation 边界；
- 便于对每一层单独评估、缓存和定位失败；
- 避免 planner 或动态工具选择引入不可控路径；
- 保持 CLI、测试与离线 eval 共享同一条生产主链。

这里的 “Agent” 指封装多轮上下文和多阶段能力的高层接口，不意味着必须使用 autonomous loop、LangChain 或 LangGraph。

## Evaluation Summary

### Retrieval

- Lexical baseline：Hit@1 0.40，Hit@3 0.68，Hit@5 0.68，MRR 0.5569。
- Semantic retrieval：Hit@1 0.48，Hit@3 0.72，Hit@5 0.76，MRR 0.6163。
- Lexical Top20 + semantic Top20：candidate recall 25/25（100%）。
- Cross-Encoder reranking：Hit@1 0.64，Hit@3 0.84，Hit@5 0.88，MRR 0.7569。
- LLM multi-turn rewrite：Hit@1 0.75，Hit@3 1.00，Hit@5 1.00，MRR 0.8750。

### Answer eval（12 cases）

| Check | Result |
|---|---:|
| Pipeline success | 12/12 |
| Behavior accuracy | 10/12 |
| Answer-case behavior accuracy | 7/9 |
| Unsupported abstention accuracy | 3/3 |
| Citation validation | 12/12 |
| Acceptable source hit | 9/12 |
| Forbidden claim violations | 0 |

deterministic failures 已保留供人工复核，没有为了追求 100% 修改 matcher、detector 或主链。现有 human review 将其中两项 behavior failure 识别为 detector false positive；其余问题属于 source matcher 边界、回答完整性或 evidence selection 的非阻塞质量问题。

### Acceptance

- Single-turn supported：通过。
- Multi-turn contextual：通过，第二轮使用 history 完成 query rewrite。
- Unsupported / abstention：通过，未被当作技术失败，后续 supported 问题仍可继续。
- Citation-heavy supported：通过，多个 citation ID 均映射到当前 Top5 evidence。
- Unit tests：59/59 通过。

详细结果位于 `eval/results/`。

## Run Locally

### Prerequisites

- Python 3.10+
- 能访问 Hugging Face 以完成首次模型下载
- 一个兼容 OpenAI Chat Completions 的 LLM endpoint；当前评估使用 DeepSeek

以下命令在项目根目录执行。Windows PowerShell 示例：

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

CLI 以本地文件模式加载 reranker。首次使用前，可通过现有 reranked eval runner 下载模型并同时验证索引：

```powershell
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend reranked --allow-reranker-download
```

之后启动聊天：

```powershell
.\.venv\Scripts\python.exe -m src.cli
```

默认模式输出回答和由 `AgentResult.citations` 提供的结构化来源。调试模式额外显示 rewritten query、reranked Top5 evidence，以及 rewrite/generation 的 API 或 cache 来源：

```powershell
.\.venv\Scripts\python.exe -m src.cli --debug
```

输入 `exit` 或 `quit` 退出；也可以使用 `Ctrl+C` 或 EOF。对话 history 只保存在当前进程中，只有成功轮次会被追加。

### Tests

项目使用标准库 `unittest`，不是 pytest：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Existing eval runners

```powershell
# 单后端与负实验
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend lexical
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend semantic
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend hybrid

# 最终重排、候选召回与多轮改写
.\.venv\Scripts\python.exe -m eval.run_retrieval_eval --backend reranked
.\.venv\Scripts\python.exe -m eval.analyze_candidate_recall
.\.venv\Scripts\python.exe -m eval.evaluate_multiturn_strategies

# 端到端回答评估
.\.venv\Scripts\python.exe -m eval.run_answer_eval
```

多轮与回答 eval 会读取 `.env`，并使用各自的本地 cache。默认结果写入 `eval/results/`。

## Project Layout

```text
policy-agent/
├── data/site-policy/         # upstream policy clone（ignored）
├── cache/                    # indexes、model cache、LLM cache（ignored）
├── eval/                     # datasets、runners、reports、human review
├── src/
│   ├── ingest.py             # policy loader
│   ├── chunking.py           # heading-aware chunking
│   ├── indexing.py           # lexical index
│   ├── semantic_indexing.py  # dense semantic index
│   ├── retriever.py          # lexical retrieval
│   ├── semantic_retriever.py # semantic retrieval
│   ├── hybrid_retriever.py   # RRF negative experiment
│   ├── reranker.py           # Cross-Encoder scorer
│   ├── reranked_retriever.py # candidate union + reranking
│   ├── conversation.py       # contextual query rewrite
│   ├── generator.py          # grounded generation + citation validation
│   ├── agent.py              # deterministic orchestration
│   └── cli.py                # in-process multi-turn CLI
└── tests/                    # unit and pipeline-boundary tests
```

## Known Limitations

- 回答受本地 `github/site-policy` 快照限制；上游政策更新后需要重新拉取语料并构建索引。
- contextual rewrite 与 answer generation 依赖外部 LLM API；本地 cache 只覆盖已经成功请求过的相同输入。
- semantic encoder 与 Cross-Encoder 首次需要下载模型，CPU 上的初始化与重排存在延迟。
- Top5 evidence 仍可能漏掉相关 section，尤其是 broad 或 multi-source 问题；Hit@5 不是 100%。
- citation validation 只保证 ID 合法、无模型生成 URL、metadata 映射来自当前 evidence，不自动证明每项 claim 都被语义支持。
- deterministic matcher/detector 可能产生 false positive 或 false negative，因此 answer eval 仍保留人工审查环节。
- CLI history 仅存在于当前进程，没有持久化会话或 Web UI。
- 本项目提供政策语料检索与解释，不构成法律意见。
