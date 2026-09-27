# A1 剩余失败分析与 A2 触发判断

**状态：COMPLETE。** 仅作诊断：没有重新生成答案、修改 retrieval/reranker/selector/router/generation、调参或实现 decomposition。

## A. 失败清单

- Validation V1 冻结的 `QUERY_REQUIRED` aspects：**208**。
- 四个保留 arms 中至少一个 arm 漏掉的不同 aspects：**16**，涉及 **10** 题。
- 各 arm 漏答数：`fixed_top5` 12、`coverage_selector_v2` 12、`adaptive_prefix_v1` 8、`no_router_adaptive_v1` 6。
- 按 route：**BROAD 7 / SIMPLE 9**。
- 每个漏答 aspect 的证据位置使用两类记录：`a0_bge_rerank_orders.json` 中的 `in_candidate_union` 与 `candidate_best_rank_pipeline`（A1 arms 实际使用的顺序），以及 `human_aware_context_v1.json` 中各 arm 所选 context 的出现情况。

## B. 失败类型

| 类型 | 数量 | 案例 |
|---|---:|---|
| `GENERATION_MISS` | 6 | VAL-001-008、-011、-027、-032、-039、-050 |
| `SELECTION_BUDGET` | 6 | VAL-001-006、-033（×5） |
| `RANKING_WEAKNESS` | 2 | VAL-001-001 |
| `REPRESENTATION_CANDIDATE` | 2 | VAL-001-046 |
| `CANDIDATE_MISS`（非 representation） | 0 | — |
| `FRAGMENTATION_CANDIDATE` | 0 | — |
| `OTHER` | 0 | — |

**Q1：失败在哪一层？** 主要是 **generation**（证据在选定 context 中，但答案漏答：6 项）和 **context selection / budget**（证据排序尚可，但未被选入：6 项）。Ranking 较少（2 项）；representation 仅 1 题（2 项）；没有确认的 fragmentation。

## C. BROAD 特有失败（7 项）

| Aspect | 类型 | 证据状态 |
|---|---|---|
| VAL-001-001-F02 | RANKING_WEAKNESS | 支持 chunk `chunk_dfcbf6c0…` 在 pipeline 中排 **22/30**；所有 arms 均未选择 |
| VAL-001-001-F03 | RANKING_WEAKNESS | 同一 chunk；`fixed_top5` 答案仍覆盖，其他 arms 漏答 |
| VAL-001-006-F02 | SELECTION_BUDGET | 排第 6；`fixed_top5`（k=5）漏选，所有更深的 arms 选入并答出 |
| VAL-001-008-F02 | GENERATION_MISS | 排 **1**、被所有 arms 选中；`fixed_top5`/`selector` 答案漏答，adaptive/no-router 覆盖 |
| VAL-001-039-F03 | GENERATION_MISS | 排 **1**、被所有 arms 选中；仅 `adaptive_prefix_v1` 漏答 |
| VAL-001-046-F03 | REPRESENTATION_CANDIDATE | 支持证据**不在 candidate union**；所有 arms 漏答 |
| VAL-001-046-F04 | REPRESENTATION_CANDIDATE | 同一 chunk；所有 arms 漏答 |

SIMPLE 的 9 项失败均属 generation 或 budget：`VAL-001-011-F01`（第 1 名、已选入、所有 arms 漏答），`VAL-001-027-F01`、`VAL-001-032-F02`、`VAL-001-050-F01`（generation），以及 `VAL-001-033-F01…F05`（同一 chunk 排第 6，fixed/selector 漏选）。

## D. 明确的 representation 候选案例

**`VAL-001-046`（BROAD）：**“If investigators seek my GitHub account data, will GitHub tell me first, and in what situations might that notice be withheld or delayed?”

- 受影响要求：**F03**（披露前给受影响所有者发送法律程序副本）和 **F04**（紧急情况下延迟通知）。
- 支持 chunk：`chunk_35fd87021964946f76efbd5f`，标题 *“We will notify any affected account owners”*；该段同时包含两项事实。
- 原问题：该 chunk **不在 candidate union**（pipeline `a0` 与 runtime 顺序皆然）。所有 arms 都没有选到它，也都漏掉 F03/F04。
- 反事实 probe：使用相同冻结配置的 retriever；requirement queries 仅从原问题人工提取，不使用 generation LLM：
  - `req_withhold` “When may GitHub withhold or delay notifying users about a legal request?” → 支持 chunk **排名 1**（Top5）。
  - `req_urgent` “…urgent circumstances delay notice to prevent death/serious harm or an ongoing investigation?” → **排名 1**。
  - `req_email_process` “Does GitHub email affected owners a copy of the legal process before disclosure?” → **排名 3**（Top5）。
- 这不只是 budget/selection 问题：复合原问题的候选集合中根本没有目标证据，提高 TopK 不能让它进入 context；generator 从未见过它。从问题文本忠实提取的 requirement query 让它排第 1。严格标准 1–7 均满足。
- 范围限制：这只是**一题**（2 个 aspects）。

**不确定的第二候选 `VAL-001-001`（BROAD）：**支持 chunk `chunk_dfcbf6c0…` 在 pipeline 排 **22**，runtime 排 **12**；`req_assert`/`req_legalrisk` 排 **1/2**。按 pipeline 顺序 TopK 无法触及它，类似 representation 问题；按 runtime 顺序，提高 k 则可能触及。因此**不计为**确认的 representation candidate。

## E. 非 representation 失败

- **Generation（6）：**证据已在所选 context，但答案漏掉要求。尤其 `VAL-001-011-F01` 的来源排第 1、被所有 arms 选中，明确列出 organize/promote/threaten/incite 禁令，却无答案说出；`VAL-001-050-F01` 也排第 1，四个 arms 中三个漏答。这是 answer utilization/compression 问题，不是 decomposition。
- **Selection budget（6）：**`VAL-001-033-F01…F05` 来自一个排第 6 的枚举 chunk；`fixed_top5`（k=5）无法触及，`coverage_selector_v2` 也未选入，但 `adaptive_prefix_v1`/`no_router_adaptive_v1` 选入并答出了全部五项。`VAL-001-006-F02` 同样排第 6。它们可由 budget/selection 处理，而非 representation。
- **Ranking（2）：**`VAL-001-001-F02/F03` 的支持证据排序较深。

## F. A2 触发判断

# WEAK_TRIGGER

存在一个真实但孤立的 BROAD 多要求 representation failure（`VAL-001-046`，2 个必需 aspects）：原问题 candidate union 完全缺少明确被问及的要求之证据，忠实的 requirement query 则把证据带到第 1 名。这足以支持**最小离线机制验证**，不足以默认增加 A2 decomposition hot path。主要剩余失败仍在 generation 和 selection/budget，decomposition 不能解决它们。

## G. 最小后续实验（仅因 WEAK_TRIGGER）

保持小范围，不扩展 benchmark：

- **触发案例（1）：**`VAL-001-046`，要求为 (a) 披露前通知/法律程序副本（F03），(b) 紧急情况下延迟通知（F04）。
- **对照案例（2–3）：**
  - `VAL-001-033`：`SELECTION_BUDGET` 对照（同一 chunk 排第 6，不应需要 decomposition）。
  - `VAL-001-011`：`GENERATION_MISS` 对照（证据第 1 名且已在 context，decomposition 无法帮助）。
  - 另取 2–3 道已完整覆盖的 BROAD 问题作负对照。
- **可选不确定案例：**`VAL-001-001`，仅作为次级 probe，不决定采纳结论。
- 机制验证**仅针对 retrieval**（不生成答案、不采纳架构）。若 requirement-query retrieval 未改善受影响要求，则将 A2 关闭为 `NOT_TRIGGERED`。

## H. 产物与完整性

- `eval/results/a1_failure_analysis_v1.json`
- `eval/results/a1_failure_analysis_summary.md`（本文）
- `eval/results/a1_representation_probe_v1.json`
- 原始清单：`eval/results/a1_failure_inventory_raw_v1.json`
- 未修改生产代码、retrieval、reranker、selector、router、generation、index、model 或 Human Truth；没有 LLM generation 调用（仅 retrieval probe）。

### 排序复现限制

`a0_bge_rerank_orders.json`（A1 arms 实际消耗的顺序，由 `fixed_top5` 所选 chunk IDs 验证）与当前 runtime rerank 顺序在 50 题中均未逐位匹配，虽然所有记录的来源 fingerprints 一致。Pipeline 行为排序使用 `a0`；反事实 probe 在原问题和 requirement queries 上使用同一个 retriever，因此**相对变化**才是信号。该限制已明示，也是 `VAL-001-001` 被视为不确定的原因。

## Q2 / Q3 / Q4

- **Q2：**有一个明确的 BROAD 多要求 representation failure（`VAL-001-046`），另有一个不确定案例（`VAL-001-001`）。
- **Q3：**不能；单个案例不足以构成 A2 机制 benchmark，只支持最小 probe。
- **Q4：**此处不适用：因为存在 representation 证据，A2 不是 `NOT_TRIGGERED`，而是 `WEAK_TRIGGER`（仅做最小 probe，不进入默认 hot path）。

至此停止；A2/A3 均未实现。
