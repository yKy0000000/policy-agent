# Answer judge calibration v1：测量审计报告

**范围。** 在冻结随机样本上，将历史 DeepSeek-family answer judge 与 GPT-5.6 Sol cross-family judge、项目作者人工复核进行确定性比较。没有重新生成或修改答案、aspect、样本、rubric 或 verdict。这是测量审计，**不是 corrected benchmark score**。

审计总体：50 道 fixed-Top5 研究答案及其 208 个 `QUERY_REQUIRED` answer–aspect judgments（`a1_blind_answer_quality_frozen_v1.json` 中支撑已发布 `196/208`、`43/50` 的标签）。主样本：seed `20260927`，15 题、60 aspects（`JC-001`–`JC-060`，28.8%）。

人工参考为 **AI-assisted blinded project-author review**：项目作者作最终判定，AI 仅用于翻译和提示边界案例。复核者未看到历史或 cross-family verdict、arm identity 或历史分数。这不是完全独立的人工标注。

## 完整性

分析前所有检查均通过；若不匹配，分析将停止。

- seed `20260927`；15 题 / 60 aspects；`JC-001`–`JC-060` 各出现一次。
- sample SHA-256 `222ba9eb…` 未变；cross-family SHA-256 `041f8955…` 与冻结值一致。
- 来源哈希与预注册一致：quality `96bf5fa6…`、generation `1a0c2f0d…`、labels `85199cfa…`。
- 人工复核 packet：60/60 已完成，0 个 `PENDING`；正文与生成 packet 按字节一致，答案、criterion、source 和 ID 均无漂移。
- 历史 verdict 经 fixed-Top5 blind mapping 确定性映射至全部 60 个 IDs。
- Cross-family：60/60 完成，0 个未解决技术失败，0 个 `AMBIGUOUS`。

## A. 历史 DeepSeek-family judge 与人工复核

以人工复核为参考。`False positive` 指历史 judge 判 `COVERED`、人工判 `MISSING`；`False negative` 指历史 judge 判 `MISSING`、人工判 `COVERED`。

| 人工 \ 历史 judge | COVERED | MISSING |
|---|---:|---:|
| COVERED | 55 | 0 |
| MISSING | 2 | 3 |

| 指标 | 数值 |
|---|---:|
| 比较项数 | 60 |
| 一致项数 | 58 |
| 一致比例 | 96.67% |
| 95% Wilson CI | [88.64%, 99.08%] |
| False positives | 2（`JC-013`、`JC-053`） |
| False negatives | 0 |

样本中观察到的不一致率为 **2/60 = 3.33%**，95% Wilson CI [0.92%, 11.36%]。这是*示意性的敏感性分析，不是 corrected benchmark score*。

## B. GPT-5.6 Sol cross-family judge 与人工复核

| 人工 \ Sol | COVERED | MISSING | AMBIGUOUS |
|---|---:|---:|---:|
| COVERED | 55 | 0 | 0 |
| MISSING | 2 | 3 | 0 |

| 指标 | 数值 |
|---|---:|
| 比较项数 | 60 |
| 一致项数 | 58 |
| 一致比例 | 96.67% |
| 95% Wilson CI | [88.64%, 99.08%] |
| False positives | 2（`JC-013`、`JC-053`） |
| False negatives | 0 |
| AMBIGUOUS | 0 |

Sol 没有输出 `AMBIGUOUS`；全部 60 项都可与人工结果比较，未强行映射 verdict。

## C. 历史 judge 与 Sol（二级模型间比较）

| 指标 | 数值 |
|---|---:|
| 可比较项数 | 60 |
| 一致 | 60（100%） |
| 不一致 | 0 |
| 历史 `COVERED` → Sol `MISSING` | 0 |
| 历史 `MISSING` → Sol `COVERED` | 0 |
| 涉及 AMBIGUOUS | 0 |

**模型间一致不等于准确率。** 两个 judge 可能共享盲点；本次它们都高估了相同两个 aspects，不能用模型间一致替代人工校准。

## D. 人工判为 MISSING 的边界案例

| JC ID | 人工 | 历史 | Sol | 必需信息 | 模式 |
|---|---|---|---|---|---|
| JC-010 | MISSING | MISSING | MISSING | 邮件提交即使附有附件，也应在邮件正文提供纯文本版本。 | 三方均判 MISSING |
| JC-013 | MISSING | COVERED | COVERED | 死者的近亲、指定继承人或其他获授权者可请求处理账户。 | 部分语义匹配 |
| JC-053 | MISSING | COVERED | COVERED | GitHub 通常会就待处理的账户或仓库请求通知用户。 | 适用范围不匹配 |
| JC-055 | MISSING | MISSING | MISSING | 披露前，GitHub 会合理努力通过邮件向受影响账户所有者提供法律程序副本，使其能够提出异议。 | 三方均判 MISSING |
| JC-056 | MISSING | MISSING | MISSING | 在罕见紧急情况下，为防止死亡、严重伤害或因调查仍在进行，GitHub 可能延迟通知。 | 三方均判 MISSING |

只有 `JC-013` 和 `JC-053` 是模型与人工的分歧。`JC-010`、`JC-055`、`JC-056` 虽由人工判 `MISSING`，历史 judge 也已如此判断，不是历史 judge 错误。

## E. 整题完成状态的敏感性

一题的所有抽样 `QUERY_REQUIRED` aspects 都为 `COVERED` 才算 complete；若有 `AMBIGUOUS`，该题为 indeterminate。

| 指标 | 历史 | Sol | 人工 |
|---|---:|---:|---:|
| Complete | 13 | 13 | 12 |
| Incomplete | 2 | 2 | 3 |
| Indeterminate | 0 | 0 | 0 |

- 历史与人工的 complete-status 分歧：`VAL-001-012`（历史/Sol 因 `JC-013` 判 Complete，人工判 Incomplete）。
- Sol 与人工的 complete-status 分歧：`VAL-001-012`。

Aspect 层面的 58/60 一致略高估整题可靠性：15 题中有 1 题的 complete 状态翻转，因为一个被高估的 aspect 就足以改变 AND-complete 判定。

## F. 误差方向与分类

审计样本中的历史 judge 呈现**观察到的 over-credit 倾向**：2 个 false positives、0 个 false negatives，Sol 方向相同。这只是样本观察，不证明确定的普遍偏差。

| 模式 | 数量 |
|---|---:|
| partial semantic match | 1（`JC-013`） |
| scope mismatch | 1（`JC-053`） |

两项误判的候选答案与 criterion 在主题上相邻，但表达范围更窄或更泛：`JC-013` 用笼统的“authorized individual”代替明确的申请人类别；`JC-053` 将通知限制到账户信息请求，没有清楚覆盖仓库请求。另 3 项遗漏型人工 `MISSING`（流程、条件、例外）均已被两个模型 judge 识别。因此，观察到的宽松判断集中在覆盖范围，而不是漏掉步骤。

## G. 架构结论的稳定性

没有重新运行任何架构实验。审计对象是 fixed-Top5 研究 arm；router/selector 和 MiniLM runtime arms 未直接经过人工校准。

| 结论 | 状态 | 理由 |
|---|---|---|
| MiniLM + fixed Top5 runtime default | STABLE | 部署决策有不依赖 judge 的 latency 门槛：warm rerank p95 约为 MiniLM 2.55s、BGE 14.78s，5.80× 超过 2.0× 上限。审计仅见少量 over-credit，未发现反转；judge 分歧本身无法推翻受 latency 门槛约束的 runtime 选择。 |
| Router KILL | STABLE | `query_router_v1` 的 KILL 还依据不依赖 judge 的成本与回归计数及质量持平。审计未见 under-credit，历史/Sol 100% 一致，因此没有证据表明方向性误差造成持平；但 router/selector arms 的持平质量部分尚未经人工校准。 |
| BGE research-quality candidate | MEASUREMENT-SENSITIVE | 审计对象是 BGE 研究 arm，历史 judge 高估了其中 2/60 个 aspects。“质量导向研究选项”的判断依赖这个 judge 测得的质量优势，因此对测量敏感。部署状态不变：不依赖 judge 的 latency 原因仍使 BGE 不是 runtime default。 |

没有更改默认值、reranker、router、selector、prompt 或 retrieval 设置。

## H. 结论的证据等级

**直接观察到：**

- 历史 vs 人工：58/60 一致、2 个 false positives、0 个 false negatives。
- Sol vs 人工：58/60 一致、2 个 false positives、0 个 false negatives、0 个 `AMBIGUOUS`。
- 历史 vs Sol：60/60 一致、0 个方向性分歧。
- 人工 `MISSING` 共 5 项，其中 3 项三方一致。
- 整题状态：历史/Sol 13 题 complete，人工 12 题；分歧为 `VAL-001-012`。
- 一致比例的 Wilson 95% CI 为 [88.64%, 99.08%]；不一致比例为 [0.92%, 11.36%]。

**推断：**

- 观察到的分歧提示，模型对部分覆盖或缩窄范围的语义匹配较宽松。
- Aspect 一致率可能略高估整题可靠性。

**尚未确立：**

- 整个 benchmark 的人工准确率、真实用户准确率，或修正后的 `196/208` / `43/50`。
- 超出 Validation V1 和该 CPU 环境的外部有效性。
- Router、selector 或 MiniLM runtime arms 的 judge 表现（未审计）。
- 基于此样本的任何架构因果主张。

## 限制因素

- 15 题的 60 个 aspects；Wilson 区间较宽。
- 人工参考有 AI 辅助，且来自单一项目作者；不是独立多人标注。
- Cross-family judge 与历史 judge 在全部 60 项上都一致，因此本审计不能确立两个 model judges 的独立性。
- 仅审计 fixed-Top5 研究 arm。

## 产物

- `eval/results/judge_calibration_v1/calibration_summary.json`
- `eval/results/judge_calibration_v1/disagreements.json`
- 分析器：`eval/run_judge_calibration_analysis.py`
