# Validate Stage Summary — Measurement Validity Audit

**Status: Validate = COMPLETE** (2026-09-26)

Research chain: `Validate → Repairability → Mechanism → Routing`. This document closes Validate and formally
retracts the earlier over-strong interpretation. It introduces no new experiment and changes no frozen
artifact (selection, benchmark, rubric, V1/V2 audits, historical results are untouched).

## Formal retraction

The earlier working conclusion

> generation utilization is the binding constraint

is **withdrawn**. It was based on a nominal omission count that the Measurement Validity Audit showed to be
substantially inflated by evaluation measurement artifacts. The corrected statement is narrower:

> The original answer-evaluation pipeline substantially overestimated generation incompleteness. Most nominal
> omissions were semantically present paraphrases rather than genuine omissions. Narrow-span adjudication
> introduced additional false errors through insufficient evidence context, while full-Top5 adjudication
> corrected that problem but showed mild over-leniency and anchor drift. Human review of the pre-registered
> subset confirmed two genuine answer-level errors and one ambiguous/non-atomic target among the nominal cases.

中文：

> 原 evaluation pipeline 明显高估了 generation incompleteness。大量 nominal omission 实际是语义等价表达；
> V1 narrow-span 又制造了 packet-scope 假错误；V2 full-Top5 修复了证据不足，但又表现出轻度过宽匹配和
> anchor drift。最终人工复核确认了 2 个 genuine answer-level errors 和 1 个 target-ambiguous item。

真正结论：**原来估计的 generation-error magnitude 被明显夸大，但仍存在少量真实 answer-level errors。**

Keep the following out of scope — none of these is licensed by the data:

- generator 完全没有问题；
- evaluator 完全不可靠；
- V2 完全失败；
- genuine error = 0；
- generation utilization 已被彻底否定。

## Final evidence chain

| Layer | Scope | Result |
|---|---|---|
| Original judge (deepseek-v4-flash) | 10 nominal problematic facts | 9 missing + 1 incorrect |
| V1 adjudication (deepseek-v4-pro, narrow span) | 10 nominal | 7 present, 3 `ABSENT_OR_INCORRECT`; 6 `unclear_source` tags |
| V2 adjudication (deepseek-v4-pro, full frozen BGE Top5) | 10 nominal | 10 present; `unclear_source` 0 |
| Human review (pre-registered subset) | 10 nominal + 10 covered-side | 7 present, 2 `ABSENT_OR_INCORRECT`, 1 `AMBIGUOUS` |

- Human-vs-V2 exact agreement on the pre-registered 20-item subset: **17/20 = 85%**; disagreement **3/20 = 15%**.
- Disagreement set: `VAL-001-039-F02` (anchor drift / false PRESENT), `VAL-001-050-F01` (over-lenient incomplete
  proposition coverage), `VAL-001-008-F02` (human cannot determine the atomic target; non-atomic anchor — not a
  model error).
- Cleaned nominal cohort: 2 confirmed errors + 1 ambiguous + 7 human-confirmed present.
- Covered side: the V2 model judged 40/40 covered sample PRESENT, but **only 10 of 40 were human reviewed**
  (all 10 human-confirmed present). 40/40 must be described as model-adjudication evidence, never as
  human-confirmed ground truth.

Frozen artifacts: `eval/results/measurement_validity_cleaned_cohort.json` / `.md` (three-layer writeback and
cohort), `eval/results/measurement_validity_audit.json`, `eval/results/measurement_validity_audit_v2.json`.

## Evaluator failure taxonomy (observed so far)

1. **Semantic paraphrase false negative / over-strict matching.** The answer conveys the required information,
   but the evaluator labels it missing because wording, compression, or merge order differs. This is the main
   source of the original nominal omissions (e.g., the seven nominal facts human-confirmed present in
   `VAL-001-009`, `011`, `022`, `026`, `037`, `050-F05`).
2. **Packet-scope artifact.** The V1 adjudicator received only one narrow mapped source span while the generator
   saw the full frozen BGE Top5; this produced `unclear_source` and false `ABSENT_OR_INCORRECT` labels
   (V1: 6 `unclear_source` tags; V2 full-Top5: 0).
3. **Anchor drift / over-lenient semantic matching.** With full context, the adjudicator finds topically related
   evidence and accepts it without aligning to the atomic proposition. Representative case:
   `VAL-001-039-F02`. Core principle: **topical relevance ≠ proposition equivalence**.
4. **Target ambiguity / non-atomic anchor.** The anchor contains several semantic propositions and the fact ID
   does not state which one is the scoring target, so even a human reviewer cannot give a reliable binary
   verdict. Representative case: `VAL-001-008-F02`. This is a case-representation problem, not a model error;
   the item is excluded from the repair cohort.

## Scope and limitation statement

- Human review is a pre-registered but **single-reviewer** review of **20/50** Validation V1 cases' facts
  (10 nominal + 10 of 40 covered-side). It is the current human gold for those items only.
- The V1/V2 adjudicator is same-provider/same-family as the generator (`deepseek-v4-pro` vs
  `deepseek-v4-flash`), not family-independent.
- Validation V1 remains development/diagnostic data, not an untouched test set for this audit.
- No production prompt, model, router, or rubric was changed by the audit or by this writeback.

## Next stage

Repairability only, starting from the two confirmed errors (`VAL-001-039-F02`, `VAL-001-050-F01`) and excluding
the ambiguous item. Design is preregistered in `eval/oracle_repair_v1_preregistration.md`; no repair API calls
have been executed.
