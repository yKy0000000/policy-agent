# Reader-facing figure redesign plan

Three figures in the README, each answering one decision question. Source of numerical truth: `eval/final/final_metrics.json`, `eval/final/failure_analysis.json`, and `eval/final/a2_case_study.json`; the frozen underlying sources are named below. All new assets use the same typography, semantic palette, white canvas with dark text, direct labels, a source/scope footnote, and both PNG (high DPI) and SVG. Existing evidence files remain untouched.

## Audit of current figures

| Current asset | Editorial weakness | Decision |
|---|---|---|
| `a1_quality_cost_pareto` | Correct positions, but the tiny labels compete with gridlines. It plots only completeness against tokens while dominance also depends on coverage, regressions, and grounding; the red “dominated” line does not show those dimensions. Five unrelated point colors weaken the hierarchy. | Replace with a paired decision chart: a compact four-arm cost/completeness overview and a prominent selector–router comparison across the other axes. |
| `a1_quality_comparison` | Two percentage panels mostly repeat A1 data, do not show economics or regression, and use a rainbow palette. The main verdict is invisible. | Remove from README; retain the legacy file as evidence. |
| `failure_taxonomy` | Counts are correct, but equal treatment of five bars hides the 12/16 grouping. The bottom caption is small, red, and detached from the bars; representation is an aspect count, not an incidence rate. | Replace with a horizontal breakdown grouped by roadmap consequence, with 12/16 and zero fragmentation called out directly. |
| `a2_representation_case` | Correct data but the large green 4/4 bar and long empty lanes encode coverage only. Rank 2 versus rank 79/91 is relegated to small annotations, and “absent” is hard to compare visually. | Replace with four strategy lanes on a shared rank/visibility scale and a clear 0/4→4/4 outcome callout. |

The old figures have a white raster background and are visible on GitHub dark mode as white cards; the redesign keeps that intentional high-contrast card, improves text size, and avoids transparent text over an unknown page theme. SVG text and shapes remain dark on white as well. No chart relies on color alone.

## Figure 1 — Why the router was removed

- **Question:** did query classification earn its quality, regression, and provider-token cost?
- **Form:** two aligned panels. Left: concise cost-versus-answer-complete positioning of fixed Top5, selector, router, and no-router adaptive. Right: paired selector/router rows for required coverage, completeness, regressions, grounding issues, and provider tokens/query. A visual connector and a one-sentence verdict identify strict dominance.
- **Exact metrics:** fixed **43/50**, **196/208**, **0**, **2,533.1** tokens/query; selector **44/50**, **196/208**, **0**, **1** grounding issue, **3,281.1**; router **44/50**, **196/208**, **1**, **2** grounding issues, **3,667.7**; no-router adaptive **46/50**, **202/208**, **1**, **6,188.9**. Source: `eval/results/a1_final_pareto_v1.json` via `eval/final/final_metrics.json`.
- **Takeaway:** selector equals the router on required quality, costs fewer tokens, and has fewer regressions and grounding issues; fixed is the cost extreme, no-router adaptive the quality extreme. The chart states the full multi-metric dominance rule; 2-D position alone is insufficient to prove dominance.

## Figure 2 — Which failure layer deserves the next mechanism?

- **Question:** what kind of residual miss remained after A1, and what does that imply for A2/A3?
- **Form:** aligned horizontal bars ordered by layer: generation 6, selection/budget 6, ranking 2, representation candidate 2, confirmed fragmentation 0. A bracket visually groups the first two as **12/16**. Right-hand decision notes: improve use/allocation first; one representation case merits a minimal probe; no fragmentation trigger means A3 does not start.
- **Exact metrics/scope:** **16 unique aspects** missing in at least one of four surviving arms, across **10 cases**, from **208 QUERY_REQUIRED** aspects. The two representation aspects share **one** clear case; fragmentation is **zero confirmed**, rather than an assertion that fragmentation is impossible. Source: `eval/results/a1_failure_analysis_v1.json` via `eval/final/failure_analysis.json`.
- **Takeaway:** roadmap follows observed failure layers rather than an attractive menu of RAG techniques.

## Figure 3 — What decomposition actually proved

- **Question:** did requirement queries fix a representation failure that deeper retrieval and MMR could not?
- **Form:** four labeled lanes with source visibility (absent / rank 79 of 91 / absent from pool / rank 2, selected) and required evidence coverage (0/4 / 0/4 / 0/4 / 4/4). Rank 2 and 79 share a deliberately simple rank axis; absence is written, not assigned a fake rank. One bottom line separates “mechanism confirmed” from “default not adopted: 1 clear case/50”.
- **Exact metrics:** `VAL-001-046`; target support chunk absent under original, **79/91** under deeper retrieval, absent under MMR, **2** under requirement query; **0/4 → 4/4**. Source: `eval/results/a2_minimal_mechanism_probe_v1.json` via `eval/final/a2_case_study.json`.
- **Takeaway:** the mechanism genuinely surfaces missing evidence in this case; the figure does not suggest end-to-end answer improvement or enough incidence for default deployment. This probe involved no answer generation.

## Omitted diagrams

- **Decision path:** prose and section transitions already carry the hypothesis → evidence → decision chain. A summary flowchart would mostly duplicate headings.
- **Architecture:** a short text pipeline communicates the final runtime more accurately than a visual with dormant branches beside it. Distinguishing MiniLM production default from BGE research recommendation matters more than decoration.
