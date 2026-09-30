# 最终架构决策（A1–A3）

研究阶段已经冻结。以下是该阶段最终使用、推荐的**研究配置**：

```text
Query
→ multi-turn rewrite when applicable
→ Lexical Top20 + Semantic Top20
→ union / chunk-ID dedup
→ BGE reranker
→ fixed Top5 context
→ grounded generation
→ deterministic citation/output validation
```

| 机制 | 是否测试 | 证据 | 决策 | Runtime 状态 |
|---|---|---|---|---|
| Hybrid retrieval | 是 | candidate recall 较高（required-fact coverage ≈ 98.3%） | **KEEP** | 运行中（production） |
| BGE reranker | 是 | 测得 answer macro 0.866 → 0.920、完整题 36 → 38 | **KEEP** | 研究推荐 |
| SIMPLE/BROAD router | 是 | 被 `coverage_selector_v2` 严格支配 | **KILL** | 已移除 |
| Evidence selector（`coverage_selector_v2`） | 是 | 非支配方案，但相对最简单 baseline 没有足够的采纳收益 | **REFERENCE** | 未启用（需显式选择） |
| Requirement decomposition | 最小机制验证 | 仅修复一个 representation failure（1/50） | **CONFIRMED / NOT ADOPTED** | 保留为未启用的研究选项 |
| Parent / hierarchical expansion | 否 | 0 个确认的 fragmentation failure | **NOT TRIGGERED** | 不在运行路径中 |

## 配置区别

仓库的 runtime default 是 **MiniLM cross-encoder + fixed Top5**。在已暴露的研究 benchmark 上，**BGE reranker + fixed Top5** 的离线汇总质量更高；但后续[配对质量与 latency 决策](../runtime_reranker_decision_v1.md)没有支持晋升：4 题配对完整答案回归，加上 warm CPU rerank p95 为 MiniLM 的 5.80 倍，均未通过冻结的晋升门槛。早期 239-fact/rubric 结果（包括完整题 36 → 38）不能与后来的 208-aspect blind evaluation 串成累计提升曲线。Validation V1 早期有 holdout 价值，经过 geometry、reranker、架构、失败与机制分析后，现为 development / research benchmark。

## 运行规则

- `query_router_v1` 不在最终架构中。
- Decomposition 是**研究发现**，不是 runtime 功能；未增加 fallback 分支。
- Hierarchical/parent expansion 未实现，因为没有观察到足以支持它的失败模式。

详见 `research_summary.md`、`final_metrics.json`、`failure_analysis.json`、`a2_case_study.json`。

## 最终 release 补记：Controller Gate = STOP

上述 A1–A3 是原研究阶段的冻结配置记录。后续产品保留 MiniLM + fixed Top5 的 Fast，以及用户选择的 Adaptive/Search+，不采用 BGE production migration。

最后的 [Final Controller Gate V1](../final_controller_gate_v1/README.md)检查了观察 `query + actual context + draft` 后能否提出可执行动作。24 次调用中，PATCH 0/2、REFRESH 0/3 稳定发现；两分支均 FAIL，因此 **STOP**。没有 action probes、E2E、Controller 实现或 production 变更。始终执行的 sensor 平均增加 2,775.8 provider tokens/request，尚未证明动作收益。

结论只适用于冻结 BGE 研究场景及被测试的 non-oracle sensor，不推广为所有 LLM 或 Agent 架构的结论。保留原始结果、canonical judge 分歧和 optional/required 区别；不修改 A1–A3 决策或 frozen truth。Policy Agent architecture research 在此封板，不进入 V2/V3 tuning。
