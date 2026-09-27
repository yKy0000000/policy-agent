# A2 Minimal Mechanism Probe — VAL-001-046

**Status: COMPLETE.** Offline, retrieval/context only. No generation LLM, no automatic decomposition, no production pipeline change, no retriever/reranker/model/index change, no parameter sweep, no A3.

Environment: the frozen-config retriever (`RerankedPolicyRetriever`, Lex20 + Sem20 → union → BGE `BAAI/bge-reranker-base`). Requirements are hand-frozen and strictly query-derived (`eval/a2_minimal_probe_requirements_v1.json`). All arms select the same **5-chunk** context budget; deeper arm uses a pre-fixed Lex50 + Sem50 depth.

## A. Cases

- **Clear trigger:** `VAL-001-046` (BROAD), affected F03/F04.
- **Controls:** `VAL-001-033` (budget), `VAL-001-011` (generation), and fully-covered BROAD controls `VAL-001-005`, `VAL-001-045`, `VAL-001-047`.
- **Optional uncertain:** `VAL-001-001` (BROAD), reported separately, not used as primary trigger proof.

## B. Requirements (frozen, query-derived)

- `VAL-001-046-R1` — "Will GitHub notify me first (and how) before disclosing my account data to investigators?" (source phrase *"will GitHub tell me first"*; aspects F01/F03)
- `VAL-001-046-R2` — "In what situations might that notice be withheld or delayed?" (source phrase *"in what situations might that notice be withheld or delayed"*; aspects F02/F04)
- Analogous single/double requirement splits were frozen for the control cases; no requirement is drawn from policy evidence.

## C. Retrieval results (target supporting chunk visibility)

| Case | Arm | target in union | BGE rank | selected (top-5) | required covered | evidence tokens |
|---|---|---|---:|---|---:|---:|
| **VAL-001-046** | A2-0 original | no | — | no | 0/4 | 1865 |
| | A2-1 deeper original | yes | **79 / 91** | no | 0/4 | 1865 |
| | A2-2 diversity (MMR λ=0.7) | no | — | no | 0/4 | 1981 |
| | A2-3 requirement-query | yes | **2** | **yes** | **4/4** | 1286 |
| VAL-001-033 | A2-0 / A2-1 / A2-2 / A2-3 | yes | 3 / 3 / 3 / 1 | yes | 5/5 | 2799 / 2799 / 2799 / 2289 |
| VAL-001-011 | A2-0 / A2-1 / A2-2 / A2-3 | yes | 1 / 1 / 1 / 1 | yes | 4/4 | 1744 / 1744 / 1759 / 1574 |
| VAL-001-005 | all arms | yes | 1 | yes | 5/5 | 2890 / 2890 / 2540 / 2708 |
| VAL-001-045 | all arms | yes | 1 | yes | 6/6 | 2429 / 2720 / 2639 / 2805 |
| VAL-001-047 | all arms | yes | 1 | yes | 3/3 | 1772 / 1772 / 1772 / 2063 |
| VAL-001-001 | A2-0 / A2-1 / A2-2 | yes | 12 / 12 / 12 | no | 0/4 | 3430 / 3430 / 3528 |
| | A2-3 | yes | 1 | yes | 4/4 | 3353 |

(Candidate layer for `VAL-001-046`: the support chunk is in neither Lexical-Top20 nor Semantic-Top20 for the original query.)

## D. VAL-001-046 result

- **original:** support chunk absent from the candidate union → coverage 0/4.
- **deeper original (Lex50 + Sem50):** chunk finally appears but at **BGE rank 79 of 91** — unreachable at any reasonable context budget → coverage 0/4. Decomposition is not "just searching more".
- **diversity (MMR):** chunk is not even in the pool, so diversity selection cannot recover it → coverage 0/4.
- **requirement-query:** chunk at BGE rank 2, selected, **all four** required aspects covered (4/4) at **fewer** evidence tokens (1286 vs 1865).

Only the requirement-query (decomposition mechanism) arm recovers the evidence, and it does so at a lower or comparable context cost. Success criteria 1–4 are met.

## E. Controls (diagnoses preserved)

- `VAL-001-033` — the enumeration chunk ranks 3 in every arm and is selected everywhere; decomposition yields **no unique gain** → `SELECTION_BUDGET` diagnosis preserved (under the pipeline `a0` order it is rank 6, still a budget issue, not representation).
- `VAL-001-011` — the source ranks 1 and is selected in **all** arms including the original; decomposition adds nothing → `GENERATION_MISS` diagnosis preserved. Requirement retrieval finding the same chunk is **not** counted as an A2 fix.
- Fully-covered BROAD controls (`005/045/047`) — required coverage stays 5/5, 6/6, 3/3 with no retrieval drift or regression.

## F. Mechanism verdict

# A2_MECHANISM_CONFIRMED_BUT_NOT_ADOPTED

- Mechanism proof: **YES** — requirement decomposition uniquely (vs deeper retrieval and diversity selection) restores F03/F04 visibility for the single clear trigger case.
- Default adoption evidence: **INSUFFICIENT** — incidence is **1 clear case / 50 V1 cases** (plus 1 uncertain). Not enough to justify a decomposition hot path. Benchmark was not expanded.

## G. Architecture implication (≤3 sentences)

Requirement decomposition is a proven mechanism for the isolated `VAL-001-046` failure but too rare to adopt by default. Keep `fixed_top5` as the working baseline; treat decomposition as a dormant, evidence-gated option, not a hot path. Do not implement it now.

## H. Artifacts / tests

- `eval/a2_minimal_probe_requirements_v1.json` (frozen query-derived requirements)
- `eval/results/a2_minimal_mechanism_probe_v1.json`
- `eval/results/a2_minimal_mechanism_probe_summary.md` (this file)
- No production code changed; retrieval probe only (0 generation calls).

### Caveat
`a0_bge_rerank_orders.json` (the order the A1 arms consumed) does not bit-match the current-runtime reranked order. This does not affect the trigger result: for `VAL-001-046` the support chunk is absent from the original-query union under **both** orders. The caveat only affects `VAL-001-033` (rank 3 runtime vs rank 6 pipeline) and the uncertain `VAL-001-001`.

Stopping. A3 not started.
