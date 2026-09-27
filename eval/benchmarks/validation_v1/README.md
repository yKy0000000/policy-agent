# Validation V1 canonical benchmark

`benchmark.json` 是不可变来源的 manifest，不是标签的第二份副本。`eval.core.load_benchmark("validation_v1")` 在加载前校验各来源的 SHA-256，然后组合 50 道冻结问题、239 个早期来源/rubric facts、来自 **Frozen Adjudicated Labels V1** 的 208 个 Validation V1 `QUERY_REQUIRED` aspects，以及冻结 geometry artifact 中的来源支持 chunk IDs。历史文件名 `frozen_human_verdicts_v1.json` 为保持哈希稳定而保留，并不表示存在全面人工标注。V1 与 V3 合计 331 条标签由两个独立 model agents 初评，其中 314/331 初始一致；其余 17 条由项目作者人工裁决。Case IDs、query 文本、fact IDs、支持来源摘录和 reviewer verdicts 均留在原文件中。

原始 239 个 facts 用于 candidate/ranking 诊断；只有 208 个 `QUERY_REQUIRED` aspects 用于 context 与 answer completeness。因此 235/239、224/239、193/208、196/208 不是逐层递进的同一条 accuracy funnel。Loader 不生成新标签，也不修改 verdict；来源哈希不符时会停止加载，不会静默接受漂移。

Validation V1 在首次使用前具有 holdout 价值。后来 geometry analysis、reranker comparison、architecture experiments、failure analysis 和 mechanism investigation 已使其暴露。它现在是 **development / research benchmark**，不能再用作未来架构选择的 fresh holdout。历史冻结比较在各自原协议内仍有参考价值；新的架构主张需要另外的 fresh confirmation。
