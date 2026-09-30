# Final Controller Gate V1 — Artifact Audit

Status: audit complete, produced **before any new model call**.
Scope: verify the facts the task prompt relies on against the repository's frozen artifacts.
Rule applied: where the prompt and a frozen artifact disagree, the frozen artifact wins and the
correction is recorded below.

## 1. Files inspected

| File | SHA-256 (16) |
|---|---|
| eval/results/final_results_table_v1.json | 7af09fddaff35262 |
| eval/results/final_architecture_decision_v1.md | d3aa604ad216e17c |
| eval/validation/broad_queries_validation_v1.json | 1fb2b03d752343ea |
| eval/validation/broad_atomic_facts_validation_v1.json | 451a583f5ce88e0b |
| eval/results/frozen_human_verdicts_v1.json | 85199cfa9c0fa486 |
| eval/results/generation_utilization_results.json | 01be9f9c3a3c26b8 |
| eval/results/reranker_transfer_results.json | bbce7fa512bfbf9d |
| eval/results/a1_failure_analysis_v1.json | c0baf21496e86916 |
| eval/results/measurement_validity_cleaned_cohort.json | 9bb81f81a7b2d770 |
| eval/results/oracle_repair_v1_human_summary.md | 6a391d8c05e9a2a0 |
| eval/results/decision_execution_coupling_v1_summary.md | f3d4821f06ff90e7 |
| eval/results/semantic_gap_discrimination_v1_results.json | 0d9efb364ffa1620 |
| eval/candidate_discovery_v1_preregistration.md | a25c2465448d079c |
| eval/results/eval_summary.md | 531eb67242f3937f |
| eval/results/evidence_geometry_summary.md | f38fd0cfa2dd61d5 |
| src/generator.py | 42a7880c6a5e0bf4 |
| src/llm_client.py | c4040fc7c25a5a0b |

## 2. Confirmed facts

- Corpus: 57 documents / ~655 chunks / heading-aware chunking; hybrid lexical+semantic retrieval;
  cross-encoder reranking; fixed Top5 context; grounded generation; deterministic citation validation.
- Candidate availability is near-saturated: `evidence_geometry_summary.md` full-union available
  coverage **235/239**; reranked-Top20 also 235/239; oracle-complete cases (full union) **49/50**;
  oracle minimum K median **1.0**.
- Validation V1: 50 cases; **239** original rubric facts; **208** frozen `QUERY_REQUIRED` aspects.
- Frozen human truth (V1+V3): **66 cases**, **331** aspects, **296** `QUERY_REQUIRED`,
  **35** `RELEVANT_BUT_OPTIONAL`, **0** `AMBIGUOUS`; 314/331 initial model-agent agreement, 17/17
  disagreements adjudicated.
- Frozen quality point (BGE research stack, fixed_top5): **196/208** required aspects covered,
  **43/50** complete cases, 0 confirmed regressions, 2,533 tokens/query.
- Adaptive ceiling (`no_router_adaptive_v1`): **202/208**, **46/50**, 1 confirmed regression,
  6,189 tokens/query.
- Residual failure geometry (16 aspects / 10 cases across arms): `GENERATION_MISS` 6,
  `SELECTION_BUDGET` 6, `RANKING_WEAKNESS` 2, `REPRESENTATION_CANDIDATE` 2, `FRAGMENTATION` 0.
  By route: BROAD 7 / SIMPLE 9.
- Answer-conversion gap among evidence-complete cases: attribution is **100% `utilization_miss`**
  (8 facts / 7 cases); case conversion 0.848, fact conversion 0.964.
- Oracle Repair V1 (human-primary): current `deepseek-v4-flash` semantic repair success **1/6**;
  stronger `deepseek-v4-pro` **6/6** semantic, **3/6** full-constraint (no-URL failures); sham refusal
  12/12; already-present no-op 12/12.
- H1 semantic gap discrimination: current overall modal accuracy 26/27 (96.3%), stronger 21/27
  (77.8%); `MISSING` recall 1/2 for both; the 050 item is misclassified as `ALREADY_PRESENT` by both.
- H2 task-conditioned action: frame changes decisions; frame B `REPAIR` recall **0/2** for both;
  frame consistency current 24/27, stronger 20/27; overall H2 supported (A).
- H3 decision-execution coupling: injected decisions obeyed **6/6**, overrides **0/6** for current;
  overall A (strong decision→execution coupling); conclusion: any downstream design is only as safe as
  the upstream decision and must add decision verification rather than trust one classifier.
- Dynamic-K selection probe: no recommended configuration; token-saving variants lose 6–7 facts and
  ~3 complete cases versus adaptive; section-bonus +1 fact at +55% tokens.
- Candidate Discovery V1 is preregistered (`eval/candidate_discovery_v1_preregistration.md`), designed
  as a Value/Reachability split; it is a feasibility screen, not a deployable mechanism.

## 3. Corrected / clarified facts (prompt vs frozen artifacts)

1. **`VAL-001-039-F02` is `RELEVANT_BUT_OPTIONAL`, not `QUERY_REQUIRED`.** Confirmed in
   `frozen_human_verdicts_v1.json` (final = `RELEVANT_BUT_OPTIONAL`, both reviewers agree).
   Consequence: it is **not** a valid required-omission natural positive. The preregistered Candidate
   Discovery V1 lists it as a natural positive; under its own §3 rule (both reviewers must label
   `QUERY_REQUIRED`) that design loses one of its two naturals and risks `DESIGN NOT EXECUTABLE`.
2. **`VAL-001-050-F01` is `QUERY_REQUIRED`** (confirmed). The oracle-repair cohort may therefore not be
   described as "two required failures"; after measurement-validity cleaning the confirmed genuine
   required errors reduce to effectively one clean required positive plus one optional case, and one
   excluded non-atomic case (`VAL-001-008-F02`).
3. **Stronger-model oracle repair is not 6/6 full success.** 6/6 semantic, but only **3/6**
   constraint-compliant (raw-URL output constraint violated); this must not be summarized as 6/6.
4. **H3 shows the current model executes repairs 6/6 once a decision is injected** with 0 overrides.
   The oracle-repair current-vs-stronger gap is therefore a *decision-formation* gap, not a repair
   execution gap. Stronger-model escalation is excluded from the V1 runtime.
5. **`VAL-001-008-F02` is `QUERY_REQUIRED` in frozen truth but was excluded from the oracle-repair /
   H1 cohort as non-atomic/ambiguous.** It is not used as a natural positive here.
6. **"Coverage selector V2 11/16 / adaptive prefix 15/16" (prompt) does not match the frozen
   `eval_summary.md`**, which reports evidence-fact macro/completeness: Fixed 7/16, Adaptive V1 12/16,
   Coverage V2 10/16, Oracle 12/16. The prompt's numbers use a different metric/version; the frozen
   artifact governs. This does not change the controller decision (acquisition already near-saturated).
7. **BGE is `KEEP` in the research stack (MiniLM→BGE answer macro 0.866→0.920) but failed the paired
   promotion gate** (BGE gained 18 / lost 8 aspects, +2 complete but 4 complete-case regressions,
   above the allowed ≤1), so the **production default remains MiniLM**. Research results are
   BGE-based and must not be reported as MiniLM production baselines.

## 4. Configuration compatibility

| Item | Value | Note |
|---|---|---|
| Production default | MiniLM cross-encoder + fixed Top5 | unchanged by this task |
| Research stack used by frozen context/draft artifacts | BGE reranker + fixed Top5 | `reranker_transfer_results.json`, `generation_utilization_results.json` |
| Generator | `deepseek-v4-flash`, temperature 0 | same as all recent mechanism experiments |
| API | `https://api.deepseek.com`, Chat Completions | live connectivity verified with an 8-token dry call |

The frozen context+draft pair (`bge_top5` chunks + `bge_top5` answers) is internally consistent and is
used here **only as the sensor input scenario**, not as a production quality baseline. No MiniLM-vs-BGE
quality comparison is drawn in this report.

## 5. Legitimate reuse vs not directly comparable

Legitimately reusable:
- `reranker_transfer_results.json` `preparation.arms.bge_top5[case].chunks` as the actual generation
  context, and `cases[case].arms.bge_top5.answer` as the actual draft (same object as the
  `generation_utilization_results.json` baseline answer).
- `frozen_human_verdicts_v1.json` verdicts and `generation_utilization_results.json`
  `cohort.missing_facts` / `arms.baseline.quality.missing_fact_ids` as hidden truth.
- `a1_failure_analysis_summary.md` classification for the refresh-context candidate set.

Not directly comparable / excluded:
- Any production-quality claim from BGE artifacts.
- The two excluded ambiguous facts (`VAL-001-008-F02`, `VAL-001-039-F02`) as required positives.
- Historical judge (`deepseek-v4-pro`) outputs as primary endpoints; human/frozen truth is primary.
