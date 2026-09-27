# 70 题多策略对照：中文阅读版

> 本文件为中文阅读版；[原始冻结实验记录](../../results/multiarm_70/multiarm_70_summary.md)是 source-of-truth。中文版本不作为实验 source-of-truth，也不参与原 frozen identity。

## 研究问题与方法

项目想知道：固定 Direct、固定 Decompose、扩大证据预算的 Adaptive，以及自动 Router，各自用多少计算换到多少完整答案？这是一份**探索性 comparative snapshot**。它并列 Validation V1 的 50 题（208 个必需信息点）与 Router V1 的 20 题（66 个必需信息点），总计 70 题、274 个信息点。两个 cohort 原本为不同目的构造，合并只是报告视图，不是新的确认性实验或独立 holdout。

四个历史对照臂称为 FAST、SEARCH+、ADAPTIVE、AUTO_ROUTER_AVAILABLE。其中原报告的 `SEARCH+` 指**当时的固定 Decompose 实验臂**；当前产品的 Search+ 已改用 Adaptive，不能把两个名字视作同一实现。50 题中复用的 A1 单元使用 BGE 研究栈，20 题及部分补齐单元使用 MiniLM；两个 cohort 的 Router 也不是同一套算法。280 个 arm-case 单元中，210 个复用冻结历史结果，70 个补齐单元来自此前按冻结语义执行的缓存；生成与 judge 使用冻结协议。详细单元来源、逐题表和 latency 可用性见原始记录。

## 核心数据

| 历史策略 | 70 题完整回答 | 必需信息覆盖 | 平均 provider tokens/题 |
|---|---:|---:|---:|
| FAST / Fixed Direct | 55/70 | 250/274（91.2%） | 2,452.6 |
| SEARCH+ / Fixed Decompose | 51/70 | 241/274（88.0%） | 2,470.7 |
| ADAPTIVE | 62/70 | 262/274（95.6%） | 5,322.1 |
| AUTO_ROUTER_AVAILABLE | 57/70 | 251/274（91.6%） | 3,371.9 |

分 cohort 看，Adaptive 在 Validation 50 题完成 **46/50**，在 Router 20 题完成 **16/20**；FAST 分别为 **43/50**、**12/20**。固定 Decompose 分别为 **42/50**、**9/20**。固定 Decompose 的 provider tokens 与 FAST 相近，却有更多检索流和 rerank 工作；平均 token 数本身不表示总运行成本相同。历史 latency 只覆盖部分臂和 cohort，不能把表中的缺失值当作零或做统一端到端比较。

## 结论与限制

在这份快照中，Adaptive 的总体答案完整性最高，同时平均 provider tokens 约为 FAST 的 **2.17 倍**；Auto Router 未展示足以支持进入普通产品路径的稳定收益。事后逐题挑选四臂中最好的答案可达 **64/70**、**265/274**，这是经验上界，不是实际 Router 或产品成绩。当前产品因此提供默认 Fast 和用户主动选择的 Search+（Adaptive）；这个产品映射是在历史实验之后形成的。

这些数值不能解释为未来问题的泛化准确率。两组问题的来源、truth 审查方式、历史 reranker 与 Router lineage 不完全相同；Validation V1 已是开发数据。逐题变化、成本与有效性限制均以[原始冻结摘要](../../results/multiarm_70/multiarm_70_summary.md)为准。
