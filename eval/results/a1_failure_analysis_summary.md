# A1 Residual-Failure Analysis & A2 Trigger

**Status: COMPLETE.** Diagnostic only: no answers regenerated, no retrieval/reranker/selector/router/generation change, no parameter tuning, no decomposition implemented.

## A. Failure inventory

- Frozen QUERY_REQUIRED aspects (Validation V1): **208**.
- Aspects missing in at least one of the four surviving arms: **16**, across **10** cases.
- Per-arm missing: `fixed_top5` 12, `coverage_selector_v2` 12, `adaptive_prefix_v1` 8, `no_router_adaptive_v1` 6.
- By route: **BROAD 7 / SIMPLE 9**.
- A missing aspect's evidence was located two ways: `in_candidate_union` + `candidate_best_rank_pipeline` (from `a0_bge_rerank_orders.json`, the order the A1 arms consumed) and selected-context presence per arm (from `human_aware_context_v1.json`).

## B. Failure taxonomy

| Type | Count | Cases |
|---|---:|---|
| `GENERATION_MISS` | 6 | VAL-001-008, -011, -027, -032, -039, -050 |
| `SELECTION_BUDGET` | 6 | VAL-001-006, -033 (×5) |
| `RANKING_WEAKNESS` | 2 | VAL-001-001 |
| `REPRESENTATION_CANDIDATE` | 2 | VAL-001-046 |
| `CANDIDATE_MISS` (non-representation) | 0 | — |
| `FRAGMENTATION_CANDIDATE` | 0 | — |
| `OTHER` | 0 | — |

**Q1 — which layer?** The residual failures are dominated by **generation** (evidence is in the selected context but the answer omits the aspect: 6) and **context selection / budget** (evidence ranked acceptably but not selected: 6). Ranking is minor (2), representation only 1 case (2 aspects), fragmentation none.

## C. BROAD-specific failures (7 aspects)

| aspect | type | evidence status |
|---|---|---|
| VAL-001-001-F02 | RANKING_WEAKNESS | support `chunk_dfcbf6c0…` at pipeline rank **22** (out of union 30); not selected by any arm |
| VAL-001-001-F03 | RANKING_WEAKNESS | same chunk; answer-covered by `fixed_top5` anyway, missing elsewhere |
| VAL-001-006-F02 | SELECTION_BUDGET | rank 6; `fixed_top5` (k=5) misses, all deeper arms select and cover |
| VAL-001-008-F02 | GENERATION_MISS | rank **1**, selected by every arm; `fixed_top5`/`selector` answers omit it, adaptive/no-router cover |
| VAL-001-039-F03 | GENERATION_MISS | rank **1**, selected by every arm; only `adaptive_prefix_v1` omits it |
| VAL-001-046-F03 | REPRESENTATION_CANDIDATE | support **absent from the candidate union**; all arms miss |
| VAL-001-046-F04 | REPRESENTATION_CANDIDATE | same chunk; all arms miss |

SIMPLE failures (9) are all generation or budget: `VAL-001-011-F01` (rank 1, selected, all arms miss), `VAL-001-027-F01`, `VAL-001-032-F02`, `VAL-001-050-F01` (generation), and `VAL-001-033-F01…F05` (rank 6 single chunk, fixed/selector miss).

## D. Strong representation candidate

**VAL-001-046 (BROAD)** — "If investigators seek my GitHub account data, will GitHub tell me first, and in what situations might that notice be withheld or delayed?"

- Affected requirements: **F03** (email affected owners a copy of the legal process before disclosure) and **F04** (urgent-circumstances delay of notice).
- Support chunk: `chunk_35fd87021964946f76efbd5f`, heading *"We will notify any affected account owners"* — the exact section containing both facts.
- Original query: chunk is **absent from the candidate union** (same under the pipeline `a0` order and the runtime order). No arm selects it; all four miss both aspects.
- Counterfactual probe (same frozen-config retriever, requirement queries hand-extracted from the original query, no generation LLM):
  - `req_withhold` "When may GitHub withhold or delay notifying users about a legal request?" → support chunk **rank 1** (top5).
  - `req_urgent` "…urgent circumstances delay notice to prevent death/serious harm or an ongoing investigation?" → **rank 1**.
  - `req_email_process` "Does GitHub email affected owners a copy of the legal process before disclosure?" → **rank 3** (top5).
- Why this is not merely budget/selection: the evidence never enters the candidate set for the compound query, so increasing TopK does not surface it; it is not in any selected context; the generator never had it. A faithful requirement query derived only from the query text makes it rank-1. Strict standards 1–7 are met.
- Scope caveat: this is a **single** case (2 aspects).

**Uncertain second candidate — VAL-001-001 (BROAD):** support chunk `chunk_dfcbf6c0…` (perjury / legal-risk section). Pipeline rank **22**; runtime rank **12**; requirement queries `req_assert`/`req_legalrisk` → **rank 1/2**. Under the pipeline order TopK could not reach it, which is representation-like; under the runtime order a raised k would. Because of this inconsistency it is **not** counted as a representation candidate.

## E. Non-representation failures

- **Generation (6):** evidence is present in the selected context but the answer omits the requirement — notably `VAL-001-011-F01` (rank-1 source stating the organize/promote/threaten/incite prohibition, selected by all arms, yet no answer states it) and `VAL-001-050-F01` (rank 1, 3 of 4 arms miss). This is an answer-utilization/compression issue, not decomposition.
- **Selection budget (6):** `VAL-001-033-F01…F05` come from one enumeration chunk at rank 6; `fixed_top5` (k=5) cannot reach it and `coverage_selector_v2` declines it, while `adaptive_prefix_v1`/`no_router_adaptive_v1` select it and cover all five. Also `VAL-001-006-F02` (rank 6). Fixable by budget/selection, not representation.
- **Ranking (2):** `VAL-001-001-F02/F03` (deep-ranked support).

## F. A2 trigger decision

# WEAK_TRIGGER

There is a **real but isolated** BROAD multi-requirement representation failure (`VAL-001-046`, 2 required aspects) where an explicitly-asked requirement's evidence is entirely absent from the original-query candidate union and a faithful requirement query surfaces it at rank 1. That is enough for a **minimal offline mechanism probe**, but **not** enough to introduce an A2 decomposition hot path by default. The dominant residual failure modes remain generation and selection/budget, which decomposition does not address.

## G. Minimal next experiment (only because WEAK_TRIGGER)

Keep it tiny; do not expand the benchmark:

- **Trigger case (1):** `VAL-001-046` — requirements (a) pre-disclosure notice/copy of legal process (F03), (b) urgent-circumstances delay (F04).
- **Control cases (2–3):**
  - `VAL-001-033` — SELECTION_BUDGET control (evidence at rank 6 in a single chunk; decomposition should not be required).
  - `VAL-001-011` — GENERATION_MISS control (evidence rank-1 and already in context; decomposition cannot help).
  - 2–3 fully-covered BROAD cases as negative controls.
- Optional uncertain add-on: `VAL-001-001` (flagged uncertain; include only as a secondary probe, do not let it drive adoption).
- Mechanism probe is **retrieval-side only** (no generation, no architecture adoption). If the requirement-query retrieval does not measurably improve the affected requirements, close A2 as `NOT_TRIGGERED`.

## H. Artifacts / integrity

- `eval/results/a1_failure_analysis_v1.json`
- `eval/results/a1_failure_analysis_summary.md` (this file)
- `eval/results/a1_representation_probe_v1.json`
- Raw inventory: `eval/results/a1_failure_inventory_raw_v1.json`
- No production code, retrieval, reranker, selector, router, generation, index, model, or Human Truth was modified; no LLM generation call was made (retrieval probe only).

### Caveat (rank reproducibility)
`a0_bge_rerank_orders.json` — the order the A1 arms actually consumed (verified via `fixed_top5` selected chunk IDs) — does **not** bit-match the current-runtime reranked order in any of the 50 cases, although all recorded source fingerprints match. Pipeline-behaviour ranks use `a0`; the counterfactual probe uses one consistent retriever for both original and requirement queries, so its *relative* delta is the signal. This limitation is reported, not hidden; it is also the reason `VAL-001-001` is treated as uncertain.

## Q2 / Q3 / Q4

- **Q2:** Yes, one clear BROAD multi-requirement representation failure (`VAL-001-046`), plus one uncertain (`VAL-001-001`).
- **Q3:** No — one case is too few to form an A2 mechanism benchmark; it supports only a minimal probe.
- **Q4:** Not applicable here: because representation evidence exists, A2 is not `NOT_TRIGGERED`; it is `WEAK_TRIGGER` (minimal probe only, no default hot path).

Stopping. A2/A3 not implemented.
