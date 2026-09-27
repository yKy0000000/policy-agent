# A2 最小机制验证：VAL-001-046

**状态：COMPLETE。** 仅做离线 retrieval/context 验证；没有 generation LLM、自动 decomposition、生产 pipeline 改动、retriever/reranker/model/index 改动、参数扫描或 A3。

环境：冻结配置的 retriever（`RerankedPolicyRetriever`，Lex20 + Sem20 → union → BGE `BAAI/bge-reranker-base`）。Requirements 从原问题人工提取并冻结（`eval/a2_minimal_probe_requirements_v1.json`），严格不使用政策答案。所有 arms 都选用相同的 **5-chunk** context budget；加深检索 arm 使用预先固定的 Lex50 + Sem50 深度。

## A. 案例

- **明确触发案例：**`VAL-001-046`（BROAD），受影响的是 F03/F04。
- **对照案例：**`VAL-001-033`（budget）、`VAL-001-011`（generation），以及已完整覆盖的 BROAD 对照 `VAL-001-005`、`VAL-001-045`、`VAL-001-047`。
- **可选的不确定案例：**`VAL-001-001`（BROAD），单独报告，不作为主要触发证据。

## B. 冻结的 query-derived requirements

- `VAL-001-046-R1` — “Will GitHub notify me first (and how) before disclosing my account data to investigators?”（来自原问题 *“will GitHub tell me first”*；对应 F01/F03）。
- `VAL-001-046-R2` — “In what situations might that notice be withheld or delayed?”（来自原问题同名短语；对应 F02/F04）。
- 对照案例也冻结了类似的单项/双项要求拆分；没有任何 requirement 从政策证据中抽取。

## C. 检索结果：目标支持 chunk 的可见性

| 案例 | Arm | 目标在 union 中 | BGE rank | 被 Top5 选中 | 必需信息覆盖 | Evidence tokens |
|---|---|---|---:|---|---:|---:|
| **VAL-001-046** | A2-0 original | 否 | — | 否 | 0/4 | 1865 |
| | A2-1 deeper original | 是 | **79 / 91** | 否 | 0/4 | 1865 |
| | A2-2 diversity（MMR λ=0.7） | 不在候选池 | — | 否 | 0/4 | 1981 |
| | A2-3 requirement-query | 是 | **2** | **是** | **4/4** | 1286 |
| VAL-001-033 | A2-0 / A2-1 / A2-2 / A2-3 | 是 | 3 / 3 / 3 / 1 | 是 | 5/5 | 2799 / 2799 / 2799 / 2289 |
| VAL-001-011 | A2-0 / A2-1 / A2-2 / A2-3 | 是 | 1 / 1 / 1 / 1 | 是 | 4/4 | 1744 / 1744 / 1759 / 1574 |
| VAL-001-005 | all arms | 是 | 1 | 是 | 5/5 | 2890 / 2890 / 2540 / 2708 |
| VAL-001-045 | all arms | 是 | 1 | 是 | 6/6 | 2429 / 2720 / 2639 / 2805 |
| VAL-001-047 | all arms | 是 | 1 | 是 | 3/3 | 1772 / 1772 / 1772 / 2063 |
| VAL-001-001 | A2-0 / A2-1 / A2-2 | 是 | 12 / 12 / 12 | 否 | 0/4 | 3430 / 3430 / 3528 |
| | A2-3 | 是 | 1 | 是 | 4/4 | 3353 |

`VAL-001-046` 的 candidate 层结果：原问题的目标支持 chunk 既不在 Lexical-Top20，也不在 Semantic-Top20。

## D. VAL-001-046 的结果

- **原问题：**目标支持 chunk 不在 candidate union → 证据覆盖 0/4。
- **加深原问题检索（Lex50 + Sem50）：**chunk 最终出现，但 BGE 排在 **91 个候选中的第 79 名**；合理的 context budget 仍无法选到 → 0/4。Decomposition 的作用不是“搜得更深”。
- **Diversity（MMR）：**目标不在候选池，无法通过重排选择 → 0/4。
- **Requirement-query：**目标排到 **第 2 名**并被选中，**四项**必需信息都有证据（4/4），evidence tokens **1286 vs 1865**，反而更少。

只有 requirement-query（decomposition 机制）arm 恢复了证据，且 context 成本更低或相近。成功标准 1–4 均满足。

## E. 对照案例保持原诊断

- **`VAL-001-033`：**枚举 chunk 在所有 arm 中都排第 3 且都被选中；decomposition 没有独有收益 → `SELECTION_BUDGET` 诊断保留（pipeline `a0` 排序中它是第 6 名，仍属 budget 而非 representation 问题）。
- **`VAL-001-011`：**来源在包括原问题在内的所有 arm 中都排第 1、均被选中；decomposition 没有增益 → `GENERATION_MISS` 诊断保留。再次找到相同 chunk **不算** A2 修复。
- **已完整覆盖的 BROAD 对照（`005/045/047`）：**必需信息覆盖仍为 5/5、6/6、3/3，没有 retrieval 漂移或 regression。

## F. 机制结论

# A2_MECHANISM_CONFIRMED_BUT_NOT_ADOPTED

- **机制证据：YES。** 与加深检索和 diversity selection 相比，requirement decomposition 独有地恢复了该明确案例中 F03/F04 的证据可见性。
- **默认采纳证据：INSUFFICIENT。** 明确触发案例仅 **1/50** 题（另有 1 题不确定）；不足以支持默认 decomposition hot path。Benchmark 没有扩展。

## G. 架构含义（≤3 句）

Requirement decomposition 在孤立的 `VAL-001-046` 失败上有机制证据，但发生率不足以支持默认启用。保持 `fixed_top5` 为工作 baseline，decomposition 仅作为未启用、由证据触发的研究选项。当前不实现该默认分支。

## H. 产物与测试

- `eval/a2_minimal_probe_requirements_v1.json`（冻结的 query-derived requirements）
- `eval/results/a2_minimal_mechanism_probe_v1.json`
- `eval/results/a2_minimal_mechanism_probe_summary.md`（本文）
- 未改生产代码；仅 retrieval probe（0 次 generation 调用）。

### 排序复现限制

`a0_bge_rerank_orders.json`（A1 arms 实际使用的顺序）与当前 runtime rerank 顺序在字节级不一致。它不影响触发结论：对 `VAL-001-046`，目标 chunk 在**两种**顺序下都不在原问题 candidate union。该限制只影响 `VAL-001-033`（runtime 第 3 名、pipeline 第 6 名）和不确定的 `VAL-001-001`。

至此停止；未启动 A3。
