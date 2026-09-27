# Answer judge calibration v1 — frozen protocol

**Status: frozen before new cross-family judge calls.** This is a measurement audit. It does not change retrieval, reranking, generation, prompts, TopK, Frozen Adjudicated Labels V1, the MiniLM runtime default, or any architecture decision.

## Primary questions

1. Agreement between the historical DeepSeek answer judge and a cross-family judge.
2. Agreement of each model judge with a blinded project-author review.
3. Direction of current-judge errors: `COVERED` when human says `MISSING` (false positive), versus `MISSING` when human says `COVERED` (false negative).
4. Sensitivity of aspect coverage and strict complete-case rates to judge choice, without replacing the 50-case headline score from a sample.

Secondary: concentration of disagreements by existing failure type or the small categories exception omitted, condition weakened, procedural step omitted, partial semantic match, citation-only support, paraphrase accepted/rejected, scope mismatch, other; whether disagreements cluster on exceptions, conditions, or procedures; and whether they make the *qualitative* fixed Top5, router, or BGE runtime conclusions measurement-sensitive. No architecture search or parameter tuning is permitted.

## Frozen universe and primary sample

Universe: the **50 fixed-Top5 BGE research answers**, one per Validation V1 case, with their **208 `QUERY_REQUIRED` answer–aspect judgments** from `a1_blind_answer_quality_frozen_v1.json`. This is the universe behind the published research `196/208` and `43/50`, not the MiniLM executable default and not the full 156-answer multi-arm set. Answer text and citation metadata come from `query_aware_stage1_generation_results.json`; criterion and support excerpts come from the canonical Validation V1 loader. Keep these roles separate.

Sample **15 cases uniformly without replacement** from the 50 lexicographically sorted case IDs using Python `random.Random(20260927).sample(ids, 15)`, then review **all** `QUERY_REQUIRED` aspects in those cases. The frozen IDs, sorted for presentation, are:

`VAL-001-005`, `-007`, `-008`, `-012`, `-016`, `-019`, `-020`, `-021`, `-024`, `-026`, `-030`, `-032`, `-045`, `-046`, `-049`.

They contain **60/208 aspects (28.8%)** across 15 cases. The sample was chosen without reading per-item judge verdicts. There is no verdict-stratified primary sampling or diagnostic oversample in v1. `sample.json` must preserve the exact IDs, source hashes, opaque review IDs, and sample algorithm. Do not change the sample after seeing model or human labels.

Frozen input SHA-256: A1 quality `96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35`; stage-1 generation `1a0c2f0d873c93dcd58b1ff362e56001b99bf610c188671607aec3c6d81d2f11`; adjudicated aspect labels `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716`.

## Cross-family judge

Historical A1 generation and primary answer judge both used `deepseek-v4-flash`. Use **`gpt-5.6-sol`** through a separate ephemeral, read-only Codex invocation, with no repository inspection and no prior conversation history. The model gets only the case query, one frozen `QUERY_REQUIRED` aspect, that case's candidate answer (including its citation markers), the relevant source excerpt(s), and a citation-ID-to-source map. It must not receive arm identity, historical verdict/score, deployment decision, dispute status, or model rationale. Judge each of the 60 aspect IDs once. Save raw parsed verdicts and model provenance in `cross_family_judgments.json`; keep prompt/response data separate from the human packet. If this model is unavailable, record the failure and do not silently substitute a related family.

For each aspect, the fixed task is: **Does the candidate answer actually express the required information?** Return exactly `COVERED`, `MISSING`, or `AMBIGUOUS`, plus at most one short reason for audit. Do not reward a vague mention, a merely similar topic, a fact present only in citations/source text, common-sense inference, or an unstated condition/exception/procedural step. A complete paraphrase in another language counts as `COVERED`. Use `AMBIGUOUS` only when the frozen criterion and source do not permit a stable call. Do not grade writing style or overall answer quality. The source explains the criterion; the answer itself must say it.

Execution note before any successful sample judgment: a one-item Codex CLI attempt timed out during model transport without returning a verdict. A simple availability probe confirmed `gpt-5.6-sol` can respond, but connection setup is slow. To keep the frozen sample feasible, submit the 60 items in **three fixed contiguous batches of 20 in review-ID order**. Each batch contains only the allowed per-item fields, no prior verdicts or arm identity. Require exactly one indexed verdict per item; reject missing, duplicate, or malformed indexes. Batching is not based on verdict or difficulty. The judging rule and model remain unchanged.

## Blinded human review

Generate `eval/judge_calibration_v1_human_review.md` containing the 15 case queries and candidate answers, and for each of 60 opaque review IDs the required criterion, supporting source excerpts and citation map, with blank `verdict` (`COVERED` / `MISSING` / `AMBIGUOUS`) and optional `brief_reason`. It must show **no historical or cross-family verdict, arm/model name, historical score, or model rationale**. The project author, not code or this agent, fills it. Do not modify evaluator, rubric, prompt, sample or historical artifacts in response to the human labels.

## Analysis after human review only

For the random primary sample, report current-vs-human and cross-family-vs-human agreement, false positives, false negatives, and ambiguous counts. Exclude human/model `AMBIGUOUS` from binary FP/FN denominators and report exclusions explicitly. Also report current-vs-cross-family agreement and directional disagreements; this does not replace human calibration. For current-judge `COVERED` and `MISSING` subsets, report observed human reversals with Wilson intervals when denominators are large enough. Any projection to 208 is illustrative sensitivity, **not a corrected benchmark score**.

Because complete-case is an AND across aspects, compare complete status only for the **15 fully audited cases** under each of the three judges. A case with any `AMBIGUOUS` human aspect has unresolved human complete status, rather than being forced complete or incomplete. Report changed complete-case statuses separately from aspect agreement. Assess architecture conclusions qualitatively as `Stable` or `Measurement-sensitive`; never select a new default from this audit. Stop after delivering the blinded packet if project-author verdicts have not been supplied.
