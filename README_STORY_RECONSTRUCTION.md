# README story reconstruction

This is an editorial map, not a new research result. The current README was treated as a fact index; the decisions below were reconstructed from frozen artifacts and the original stage results.

## Project thesis

A GitHub policy Q&A agent should answer the conditions and exceptions a user actually asks for, with traceable evidence. The engineering question is where additional RAG complexity earns its cost. The research ultimately kept a stronger reranker and a small fixed context, rejected a dominated query router, demonstrated one narrow use for requirement decomposition, and declined to start hierarchical retrieval without a confirmed fragmentation failure.

## Initial belief

Broad questions seemed to need broader retrieval and more context. That was plausible from development-set evidence: on 16 Broad V3 cases, fixed Top5 made core evidence complete in 7 cases, an adaptive prefix in 15, and `coverage_selector_v2` in 11 (`eval/results/broad_v3_coverage_selector_eval.json`). This was a context diagnostic on development data, not proof that a router would improve answers.

## Turning point 1 — from retrieval expansion to evidence placement

- **Belief:** missing answer conditions imply the source never entered retrieval.
- **Evidence:** the frozen Validation V1 candidate union contained support for **235/239** original rubric facts; **49/50** cases were candidate complete (`eval/results/evidence_geometry_summary.md`, section B; `eval/validation/VALIDATION.md`). This measures candidate availability, not final answer accuracy. The same diagnostic found substantial headroom between oracle minimum context and the selected context.
- **Decision:** prioritize ranking, context allocation, and answer use over indiscriminate candidate expansion.
- **Next question:** can a better reranker move existing evidence into a short context?

## Turning point 2 — from MiniLM to a research BGE baseline

- **Belief:** a stronger reranker could rescue relevant chunks already in the union.
- **Evidence:** fixed-union evidence A/B moved coverage@5 from **211 to 224** original facts and fact-complete@5 from **43 to 46** (`eval/results/reranker_ab_summary.md`). The end-to-end transfer then moved answer macro **0.866 → 0.920** and answer-complete cases **36 → 38** (`eval/results/reranker_transfer_summary.md`). There were individual regressions, so the improvement was not universal.
- **Decision:** keep BGE as the shared *research* baseline for later arm comparisons. The repository default remains MiniLM + fixed Top5; no production switch is implied.
- **Next question:** with stronger ranking fixed, which policy should allocate context?

## Turning point 3 — from “broad means more” to a testable router

- **Belief:** query structure might identify which questions deserve a larger context. The Broad V3 evidence comparison gave a real reason to ask this, while its development status required a separate frozen test.
- **Evidence and design:** Stage 0 fixed the BGE orders, five context arms, the deterministic SIMPLE/BROAD rule (29 BROAD / 21 SIMPLE on Validation V1), and replay checks before A1 (`eval/query_aware_stage0_freeze.md`, `eval/query_aware_router_v1.json`, `eval/query_aware_arms_v1.json`, `eval/results/stage0_replay_results.json`). The router sent SIMPLE to fixed Top5 and BROAD to adaptive prefix; the evidence-side selector used no query class.
- **Decision:** compare the hypotheses under the same candidate pool, reranker, prompt, and frozen query set.
- **Next question:** do context-level gains become answers to user-required questions?

## Turning point 4 — from rubric completeness to user-required answer quality

- **Belief challenged:** every relevant policy fact in the original rubric was an obligatory answer element.
- **Evidence:** the Human Truth contract asks whether *omitting this fact makes the response incomplete for this query*, rather than whether the fact exists in policy. Of 331 reviewed aspects across V1 and V3, 296 were QUERY_REQUIRED and 35 optional; Validation V1 contributed **208 QUERY_REQUIRED** aspects. Reviewer agreement and adjudication were frozen before A1 answer quality (`eval/human_truth_contract_v1.md`, `eval/results/human_aware_context_v1_summary.md`, `eval/results/frozen_human_verdicts_v1.json`).
- **Decision:** use query-required aspects for primary answer quality, keeping the 239-fact candidate diagnostic separate. Human-aware context replay was diagnostic only: selector and router tied at **195/208** in selected context and **47/50** context-complete, but the router used more evidence tokens (`eval/results/human_aware_context_v1_summary.md`).
- **Next question:** does the answer actually use the selected evidence, and at what provider-token cost?

## Turning point 5 — from context routing to router deletion

- **Belief:** SIMPLE/BROAD routing might produce a superior quality–cost point.
- **Evidence:** A1 generated/reused answers for five frozen arms, evaluated **156 unique answers** blind to arm and cost, resolved the review queue, froze quality, then joined independent per-arm provider-token economics (`eval/results/a1_blind_answer_quality_frozen_summary.md`, `eval/results/query_aware_stage1_generation_summary.md`, `eval/results/a1_final_pareto_v1.json`). Selector and router both covered **196/208** required aspects and completed **44/50** answers. Selector used **3,281.1** versus **3,667.7** provider tokens/query, with **0 versus 1** confirmed regressions and **1 versus 2** grounding issues.
- **Decision:** `coverage_selector_v2` strictly dominates `query_router_v1` under the frozen multi-metric rule; kill this router. Selector remains a reference, not the default: against fixed Top5 it gains one required aspect and loses one, for ~29.5% more tokens. Fixed Top5 is the cheapest non-dominated working research baseline (**2,533.1** tokens/query, **43/50** complete); no-router adaptive is a **46/50** quality extreme at **6,188.9** tokens/query, not a default (`eval/results/a1_final_decision_v1.md`).
- **Next question:** what caused the required aspects that any surviving arm still missed?

## Turning point 6 — from broad mechanism ideas to failure-specific probes

- **Belief:** decomposition or parent retrieval might repair residual misses.
- **Evidence:** the final postmortem classified **16 unique missing QUERY_REQUIRED aspects across 10 cases**: generation miss **6**, selection/budget **6**, ranking weakness **2**, representation candidate **2** (one clear case), and confirmed fragmentation **0** (`eval/results/a1_failure_analysis_v1.json`, `eval/results/a1_failure_analysis_summary.md`). These are aspects missing in at least one of four surviving arms, not 16 failures in each arm. Earlier geometry work flagged three possible fragmentation shapes on an older rubric; the later answer-level, query-required postmortem confirmed none. Those diagnostic flags are not an A3 trigger.
- **Decision:** investigate only the clear representation case with a minimal A2 retrieval probe. Do not start A3 without a confirmed fragmentation case.
- **Next question:** does requirement-specific retrieval uniquely restore the missing evidence, or would depth/diversity suffice?

## Turning point 7 — mechanism works, adoption does not follow

- **Belief:** decomposing the compound question in `VAL-001-046` could reveal a hidden notice-exception source.
- **Evidence:** original-query candidate pool: absent; deeper Lex50 + Sem50: BGE **rank 79/91**, outside Top5; MMR: absent from pool; frozen query-derived requirement queries: **rank 2**, selected, **0/4 → 4/4** required evidence coverage (`eval/results/a2_minimal_mechanism_probe_v1.json`, `eval/results/a2_minimal_mechanism_probe_summary.md`). This was retrieval/context only, with no new answer generation. The clear trigger incidence was **1/50**; one other case remained uncertain due to rerank-order differences.
- **Decision:** confirm the mechanism for that case; do not add decomposition to the default runtime. A3 remains not triggered at zero confirmed fragmentation.
- **Next question:** only future evidence of higher incidence would justify revisiting default adoption.

## Final message

The small architecture was earned by progressively ruling out mechanisms that had no measured advantage at the failure layer they targeted. “Keep” (BGE), “kill” (this router), “proven but dormant” (decomposition), and “not triggered” (hierarchical retrieval) are different outcomes. The current repository default and the research recommendation must remain explicitly separate.

## Proposed README order

1. What the agent does, the counterintuitive decision, and a four-verdict snapshot.
2. The first route change: candidate saturation, then BGE answer transfer.
3. Why context routing was plausible; Human Truth and the blind A1 comparison.
4. The router decision and the retained fixed-context baseline.
5. Failure postmortem as the gate to subsequent mechanisms.
6. The `VAL-001-046` A2 case, incidence, and A3 non-trigger.
7. Actual repository configuration versus research-recommended pipeline.
8. Run it, evaluation credibility, source links, and scoped limitations.
