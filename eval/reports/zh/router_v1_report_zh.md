# Router V1：中文阅读版

> 本文件为中文阅读版；[原始冻结实验记录](../../results/router_v1/router_v1_report.md)是 source-of-truth。中文版本不作为实验 source-of-truth，也不参与原 frozen identity。

## 研究问题与方法

Router V1 只看 query，尝试判断何时需要将一条检索表示拆成多个可独立检索的目标。20 道冻结题目有 66 个必需信息点；每题共享一次 rewrite，再分别运行固定 Direct、固定 Decompose 和 Router 选路。三臂使用同一语料、索引、MiniLM reranker、生成与 citation validation。事后 oracle 比较实际结果，仅用于分析，不进入 Router prompt。

## 核心数据

| Arm | 完整回答 | 覆盖信息点 | 有效回答 |
|---|---:|---:|---:|
| 固定 Direct | 12/20 | 54/66 | 14/20 |
| 固定 Decompose | 9/20 | 51/66 | 11/20 |
| Router 选路 | 13/20 | 55/66 | 15/20 |

Router 选择并执行 Decompose **3/20** 次，其余 17 次走 Direct；没有 fallback。事后 oracle 给出固定 Direct 优先 6 题、固定 Decompose 优先 2 题、持平 8 题、两者都不满足有效性条件 4 题。Router 在 8 道有明确偏好的题上选对 **7 道**，漏掉 `router_001`；另外两道持平题 `router_009`、`router_020` 花了拆分成本。

## 结论与限制

Router 总分比固定 Direct 多 1 道完整题，但在 17 道实际走 Direct 的题里，两臂证据相同；其中 `router_016` 的 judge 覆盖不同，来自生成结果差异。因此总分领先**不能归因于选路**。固定 Decompose 得分低于固定 Direct，也说明多流检索并不自动带来更完整答案。Router V1 的结论是 mixed：这 20 题没有显示清楚的 routing-attributable 质量收益。

样本仅 20 题、语料为 57 篇 GitHub 政策文档；Router 依据 query 预测覆盖风险，看不到检索结果。Decompose 使用更多检索流和候选，temperature 0 也不保证服务端完全确定。原始逐题、费用与证据归因请读[冻结报告](../../results/router_v1/router_v1_report.md)；证据层后续诊断见[V1.1 中文阅读版](router_v1_1_report_zh.md)。
