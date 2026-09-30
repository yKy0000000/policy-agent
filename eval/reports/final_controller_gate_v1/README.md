# Final Controller Gate V1：STOP / Release 归档

这是 Policy Agent architecture research 的终点。**PATCH FAIL + REFRESH FAIL → STOP**；没有执行后续 action probes、E2E、Controller 实现或 production migration。产品继续提供 MiniLM + fixed Top5 的 Fast，以及用户选择的 Adaptive/Search+。

本文件是 release 导航与澄清，原始 12 个 gate artifacts 和实验脚本按原字节保留。它不改写冻结结果、truth、sensor、样本或阈值。[归档校验和](archive_checksums.json)保存这些文件的 SHA-256；[release validation](release_validation.md)记录收尾检查。

## 阅读顺序

1. [最终报告](final_report.md)与[机器决策](decision.json)：为什么停止，以及哪些后续步骤没有执行。
2. [样本资格](sample_eligibility.json)与[事前 manifest](gate_manifest_v1.json)：正例、controls、optional-pressure 和 secondary 的边界。
3. [原始 sensor 输出](gate1_sensor_results.json)、[adjudication](gate1_adjudication.json)与[摘要](gate1_sensor_summary.md)：逐调用行为及稳定性裁决。
4. [成本原始摘要](economics_summary.json)与[来源审计](artifact_audit.md)：token/latency、历史参考和事实修正。

## 最终结果及范围

- 实际执行 12 个输入 × 2 replicates = **24 calls**，0 transport/parse failures。
- **23/24 RETURN_DRAFT，1/24 REFRESH_CONTEXT**；没有 PATCH_CONTEXT 输出。
- PATCH 正例 `011-F01`、`050-F01`：**0/2** 发现，两次均返回草稿。
- REFRESH 正例 `006-F02`、`033-F01..F05`、`046-F03/F04`：**0/3** 稳定发现。`033` 第一次提出刷新、第二次返回草稿，不能算稳定命中。
- 完整 controls `029`、`042`、`007` 没有有害动作提议；optional-pressure `026-F02`、`039-F02` 没有升级。
- `009-F01`、`022-F02` 的 canonical A1 judge 为 COVERED、generation-utilization judge 为 missing；分歧保持为 secondary，不能合并成已确认遗漏。
- `001` 只记录为 secondary refresh，没有进入调用集。

Sensor 在该样本上高度不愿采取动作，未能可靠把可观察的缺口转成部署信息可得的动作。这足以否定**本项目冻结样本与本次 sensor**的 Controller 投入，不证明所有 LLM 无法发现缺口，也不证明 Agent architecture 普遍无效。没有 E2E，不能声称测得 Controller 的端到端质量、线上触发率或 production Pareto frontier。

## 成本与统计口径

Provider-reported totals：input **64,454**、output **2,165**、total **66,619 tokens**；24 次平均 total **2,775.8 tokens/request**。记录的 latency p50/p95 为 **0.934/1.428 s**，mean 为 **0.946 s**。原摘要使用排序后零基索引 `floor(n × p)` 的经验取值（上界截到 `n-1`）；p50 是偶数样本的上中位值，不是两中位值平均，p95 不做线性插值。保留原值，不重新生成结果。

历史 BGE research fixed Top5 参考为 **2,533.12 tokens/query**、**$0.00052381/query**。Sensor 的 **$0.00057399/request** 来自该历史 baseline 的 blended USD/token rate；它是数量级估算，不是本轮账单，也不是独立核实的当前模型价目。基线与 12-case sensor sample 不是当前 MiniLM 上的新配对 E2E 对照。Sensor 平均开销相当于历史 baseline token 均值的 1.096 倍；假设叠加在该参考均值上，才会得到约 2.096 倍的估计总量，不能把 1.096 倍误写成叠加后的总成本。

没有执行修复或检索刷新，因此 action cost 为 0。始终执行的观察已增加成本，却未展示稳定动作收益；停止结论同时依据 Gate 1 FAIL，不依赖泛化的经济优势声明。

## 保留的计数与历史澄清

- Eligibility 的 `replicate_calls: 26` 和原 Markdown 的 planned 26 包含只记录、不调用的 `001` secondary case。Manifest 排除该 case，实际执行始终是 24；不能称为两次缺失或失败调用。
- Manifest 的 sample 列表保留代表性 target ID；完整 `033-F01..F05`、secondary `001-F02/F03` 以被 manifest 哈希锁定的 eligibility 文件为准。没有增加样本或主分母。
- `039-F02` 在最终 truth 中为 **RELEVANT_BUT_OPTIONAL**，`050-F01` 为 **QUERY_REQUIRED**。Oracle repair 的两项语义错误不能称为“两项 required failures”。
- Stronger-model oracle repair 是 **6/6 semantic、3/6 constraint-compliant**。H3 中 current 在注入明确决策后实际执行修复 6/6、0 overrides；这是 decision formation 的机制线索，不足以证明 executor 语义与输出约束全面可靠。
- 原 `artifact_audit.md` 与历史 H1 stage summary 写 current modal accuracy 为 26/27（96.3%）；[冻结 H1 原始结果](../../results/semantic_gap_discrimination_v1_results.json)的 confusion matrix 和 `overall_accuracy_modal` 实际为 **25/27（92.59%）**。此为历史摘要勘误，原文件不改写，且不影响本次 24-call gate 或 STOP。
- 原报告中的“无法通过调参修好”等措辞超出本轮实验可证范围。Release 结论是**不继续调参**，不是已经证明调参不可能有效。
- 原决策提及的可选 generation-side investigation 不是本 release 的后续计划。架构研究已封板，不追加研究来挽救 Controller。

## 无网络归档检查

从 repository 根目录运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_final_controller_gate_v1.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

归档测试读取已保存的输出、样本和校验和，不执行模型、不重建结果，不需要 `.env` 或 local cache。`eval/run_final_controller_gate_v1.py` 保留为原实验 provenance；其实际 parser 只有 eligibility/gate1/check，docstring 提到的 gate2/economics 并未实现。不要按该 docstring 运行不存在的模式，也不要为复现归档重新调用 gate1。

`cache/final_controller_gate_v1_cache.json` 属于本地运行缓存，不提交；逐调用输出与 provider usage 已在归档中。原始 artifacts 经 `.gitattributes` 禁用文本换行转换，以保留 hash 身份。
