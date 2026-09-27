# Router V1 Required-Aspects Truth — Independent DeepSeek Audit

- **Auditor role:** independent evaluation-truth auditor (DeepSeek), separate from the truth author.
- **Status of this document:** pre-outcome audit. No Router V1 output was read.
- **audit_blind_to_router_v1_outputs: true**
  - Verified before reading any truth file: no Router V1 DIRECT / DECOMPOSE / routed answers, no answer-judge outputs, and no oracle results exist for Router V1. The only `eval/experiments` directories are `historical_fixed_top5_v1` and `historical_selector_v2_v1`; the only result files matching `*oracle*/judge/answer*` are prior legacy experiments (`oracle_repair_v1`, `judge_calibration_v1`, `a1_blind_answer_eval_v1`), not Router V1. Nothing from those was read for this audit.
- **Inputs audited (read-only, not modified):**
  - `eval/router_benchmark_v1.json` (frozen; SHA-256 `a345ccfd…acf16`)
  - `eval/router_v1_required_aspects_draft.json` (SHA-256 `c2f766b0…7f547`)
  - `eval/router_v1_required_aspects_draft.md` (SHA-256 `3495e0e1…26d80`)
  - `eval/router_v1_preregistration.json`, `eval/human_truth_contract_v1.md`
- **Corpus checked directly:** `data/site-policy/Policies`, **57 documents**, commit `b9578b546d2506febda1da2cd7431644d58e512c`.
- **No routing truth:** this file contains no DIRECT/DECOMPOSE gold, no expected route, no expected winner, and no claim that decomposition should help. Route-structure labels are referenced only as **author benchmark metadata** for the correlation analysis.

### Audit method

Every one of the 70 required aspects was re-derived from **query intent + corpus text**, not from the author's `information_needs`. No `information_needs → required_aspects` mapping was assumed. Each aspect was scored on five dimensions (necessity, atomicity, corpus support, evaluation clarity, granularity symmetry). The 4 `combined` aspects received the stricter §6 review.

### Headline

The draft is **substantively accurate and corpus-grounded**: 0 unsupported aspects, 0 corpus gaps, 0 route-gold leakage. The one real defect is a **localized granularity asymmetry**: the four 5-aspect queries are all cross-document, and each carries exactly one secondary aspect that is not required for answer completeness. This is a *constructive* over-decomposition driven by the shape of the underlying evidence (bulleted policy lists), not by the user's information needs. It is fixable with 4 `OPTIONALIZE` actions plus one wording-only `EDIT`; no structural redesign is needed.

Two initially suspected support-mapping edges (`router_015_a1`'s confidentiality clause and `router_013_a4`'s emergency-disclosure qualifier) were traced to the **full corpus chunks** in `cache/policy_index.json` and are in fact fully supported; the truncated `supporting_text_span` excerpts had hidden the relevant sentences. They are therefore recorded as KEEP.

---

## A. Audit Summary

**Overall verdict: READY (after mechanical change set).** The required-aspect contract is fit to freeze once the change set in §G is applied.

**Strongest parts**
1. Statements are phrased at the level of *policy judgment*, not document summary, and consistently avoid restating evidence verbatim.
2. Corpus support is almost entirely `direct`; the draft resists the "two documents → two aspects" trap except in the one place it is genuinely warranted (`router_013_a4`).
3. The four `combined` aspects are all valid cross-clause/cross-document inferences, and three of the four are directly demanded by an explicit user question.
4. Hard-looking localized queries (`router_004`, `005`, `008`, `012`) are scored at the same 2–3 aspect granularity as multi-document cases, so the contract does **not** uniformly inflate cross-document queries.
5. The draft's own method note already states that `acceptable_supporting_chunk_sets` is verified-but-not-exhaustive; the intent is correct although the JSON needs one machine-readable assertion.

**Major risks**
1. **Localized secondary-aspect inflation** (`router_006_a4`, `011_a2`, `013_a1`, `020_a4`): one extra required aspect in each of the four 5-count cases. These are the aspects most likely to be incidentally surfaced by any higher-recall retrieval and thus the ones that add the most scoring volatility (§F).
2. **One statement asserts a rule the corpus does not state**: `router_016_a3`'s "does not override" is a precedence claim; it must be reworded to the grounded conclusion (wording-only `EDIT`).
3. **Residual granularity ceiling**: no single-document query exceeds 3 aspects while four cross-document queries reach 4–5, so the top of the scale is reachable only by cross-document cases. After the change set the cross-document ceiling is 4.
4. **Metadata hygiene (non-substantive)**: duplicate chunk entries in `router_011_a2` and `router_014_a1`, and the JSON has no machine-readable statement that supporting chunks are verified-not-exhaustive (the draft Markdown says so in prose only).

---

## B. Query-by-Query Audit

Legend — necessity: `req` required / `opt` optional / `unsup` unsupported. atomicity: `atomic` / `overcomb` / `oversplit`. support: `direct` / `comb_valid` / `comb_question` / `unsup`. clarity: `clear` / `ambig`.

### router_001 — query disposition: KEEP
Localized? No. Genuine two-question case with a real public-availability nuance.

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | address is enumerated in the doxxing list; needed for "privacy violation?" |
| a2 | KEEP | req | atomic | direct | clear | "publicly available elsewhere" is the crux of the scenario |
| a3 | KEEP | req | atomic | direct | clear | incitement to contact defeats a public-source defense |
| a4 | KEEP | req | atomic | direct | clear | definitional threshold for the removal process (part 2) |

### router_002 — query disposition: KEEP
Note: `a2` comes from a second document, but it is definitional grounding for the same single question, not a second user need.

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | core prohibition on tool-purpose projects |
| a2 | KEEP | req | atomic | direct | clear | establishes that synthetic NCII counts; grounds the prohibited target |
| a3 | KEEP | req | atomic | direct | clear | context factors answer "hosting only the tool" |

### router_003 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | empty PRs + notifications |
| a2 | KEEP | req | atomic | direct | clear | alt accounts to evade moderation |
| a3 | KEEP | req | atomic | direct | clear | not-automatic-harassment nuance |
| a4 | KEEP | req | atomic | direct | clear | maintainer vs staff action (second question) |

### router_004 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | artistic/educational allowance |
| a2 | KEEP | req | atomic | direct | clear | profile placement scrutiny |
| a3 | KEEP | req | atomic | direct | clear | opt-in limiting answers "must leave visible?" |

### router_005 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | medical-claim reach |
| a2 | KEEP | req | atomic | direct | clear | parody allowed, not auto-exempt |
| a3 | KEEP | req | atomic | direct | clear | disclaimers/citations/context |

### router_006 — query disposition: OPTIONALIZE (1 aspect)

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | dual-use allowed |
| a2 | KEEP | req | atomic | direct | clear | restrict the specific abused instance |
| a3 | KEEP | req | atomic | direct | clear | temporary, not a permanent purge (answers "without banning every copy") |
| a4 | **OPTIONALIZE** | opt | atomic | direct | clear | auth-gating is the *mechanism*; an answer that omits it still fully answers "can it limit without banning every copy" |
| a5 | KEEP | req | atomic | comb_valid | clear | appeal path answers "how could we challenge" (two chunks, same document) |

### router_007 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | same-name ≠ violation or automatic reclaim |
| a2 | KEEP | req | atomic | direct | clear | confusion standard |
| a3 | KEEP | req | atomic | direct | clear | impersonation context + parody |
| a4 | KEEP | req | atomic | direct | clear | discretionary username release |

### router_008 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | confusion/misleading standard |
| a2 | KEEP | req | atomic | direct | clear | unrelated use is not a violation |

### router_009 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | safe-harbor coverage |
| a2 | KEEP | req | atomic | direct | clear | limited waiver of other site policies |
| a3 | KEEP | req | atomic | direct | clear | cannot authorize third-party testing |

### router_010 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | repo partial-edit window |
| a2 | KEEP | req | atomic | direct | clear | immutable package handling |
| a3 | KEEP | req | atomic | direct | clear | must notify GitHub within window |

### router_011 — query disposition: OPTIONALIZE (1 aspect)

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | network diagram needs a specific security risk |
| a2 | **OPTIONALIZE** | opt | overcomb | direct | clear | link + line numbers are *submission* mechanics; the question asks what GitHub needs to **assess**; also two bundled facts |
| a3 | KEEP | req | atomic | direct | clear | must explain the concrete risk |
| a4 | KEEP | req | atomic | direct | clear | copyright manual → DMCA channel |
| a5 | KEEP | req | atomic | direct | clear | the two request types must be sent separately |

### router_012 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | notice = receipt on date |
| a2 | KEEP | req | atomic | direct | clear | not unlawful / no wrongdoing / no endorsement |
| a3 | KEEP | req | atomic | direct | clear | transparency purpose answers "what it tells readers" |

### router_013 — query disposition: OPTIONALIZE (1 aspect)

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | **OPTIONALIZE** | opt | overcomb | direct | clear | request-completeness criteria are background; query asks whether it yields data and how handled; also bundles 3 conditions |
| a2 | KEEP | req | atomic | direct | clear | notify + appeal on a complete request |
| a3 | KEEP | req | atomic | direct | clear | geographic limiting + public posting |
| a4 | KEEP | req | atomic | comb_valid | clear | combined inference valid; the "limited emergency disclosure" qualifier is verified in the full `chunk_e38e8b117` |
| a5 | KEEP | req | atomic | direct | clear | private contents require a search warrant |

### router_014 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | limited emergency disclosure after verification |
| a2 | KEEP | req | atomic | direct | clear | private contents still need a warrant |
| a3 | KEEP | req | atomic | direct | clear | notice + allowed delay |

### router_015 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | the full cited chunk (E.3, `chunk_82b71e1d…`) contains both the ToS E.2 confidentiality sentence and the "will not otherwise use … unless provided as AI Input" sentence; the truncated span hid the former |
| a2 | KEEP | req | atomic | direct | clear | individual-license AI use unless opt-out |
| a3 | KEEP | req | atomic | direct | clear | opt-out is forward-looking, not retroactive |

### router_016 — query disposition: EDIT

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | block + notify via Product Provider |
| a2 | KEEP | req | atomic | direct | clear | advance-billed, non-refundable |
| a3 | **EDIT** | req | atomic | comb_valid | ambig | "does not override" asserts a precedence rule the corpus never states; reword to the grounded conclusion |

### router_017 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | sponsor logo display, not primarily advertising |
| a2 | KEEP | req | atomic | direct | clear | README/project-description promotional text |
| a3 | KEEP | req | atomic | direct | clear | no advertising in others' accounts/issues |

### router_018 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | event participation authorizes GitHub filming |
| a2 | KEEP | req | atomic | direct | clear | consentless recording is unacceptable |
| a3 | KEEP | req | atomic | direct | clear | reporting channel |

### router_019 — query disposition: KEEP

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | travel effect + reinstatement |
| a2 | KEEP | req | atomic | direct | clear | mistaken-flag appeal |
| a3 | KEEP | req | atomic | direct | clear | no download/deletion of restricted private content |

### router_020 — query disposition: OPTIONALIZE (1 aspect)

| aspect | verdict | necessity | atomicity | support | clarity | note |
|---|---|---|---|---|---|---|
| a1 | KEEP | req | atomic | direct | clear | Subprocessor List scope (on GitHub's behalf, Enterprise/DPA) |
| a2 | KEEP | req | atomic | comb_valid | clear | distinct data relationships — directly answers "same commitments?" |
| a3 | KEEP | req | atomic | direct | clear | customer responsible for instructed sharing |
| a4 | **OPTIONALIZE** | opt | atomic | direct | clear | permission-scope review is a control detail; not asked by "who is responsible" |
| a5 | KEEP | req | atomic | direct | clear | Product Provider responsible for security/custody |

---

## C. Combined-Support Audit (the 4 `combined` aspects)

| aspect | inference valid? | should it be split? | over-reach? | stronger than text? | must a normal answer state it? | verdict |
|---|---|---|---|---|---|---|
| `router_006_a5` | Yes — two spans of *the same* document jointly describe the appeal form and the appeal grounds | No (one procedural fact) | No | No | Yes (query asks how to challenge) | KEEP |
| `router_013_a4` | Yes — separation of content-removal from data disclosure is a sound cross-policy inference | No (one judgment: takedown ≠ data access) | No | No (the "limited emergency disclosure" qualifier is verified in the full `chunk_e38e8b117`) | Yes (query asks "does takedown give it data?") | KEEP |
| `router_016_a3` | Partly — §D and §H coexist, but the corpus never states which prevails | No | Yes: "does not override" is a precedence claim | Yes | Yes (query asks "does payment guarantee access?") | **EDIT** (reword) |
| `router_020_a2` | Yes — "on your instruction" app vs "on GitHub's behalf" subprocessor is a clean contrast | No | No | No | Yes (query asks "are both covered?") | KEEP |

No combined aspect needs `SPLIT`; one needs wording tightening (`router_016_a3`).

---

## D. Granularity Symmetry Audit

Aspect counts by author evidence structure (author metadata; **not** a route label):

- localized: 002=3, 004=3, 005=3, 008=2, 012=3
- multi_section single-document: 009=3, 010=3, 014=3, 015=3, 016=3, 019=3
- multi_document: 001=4, 003=4, 006=5, 007=4, 011=5, 013=5, 017=3, 018=3, 020=5

**Qualitative comparisons**

1. **Four cross-document cases share a 2-part structure but split 5 ways.** `011` (one request? / what needed each?), `013` (does it yield data? / how handled?), `006` (limit without banning? / how challenge?), `020` (same commitments? / who responsible?) each received 5 aspects. Comparable single-document 2-part cases (`014`, `015`, `019`) received 3. The extra aspects are not extra *user needs*; they are enumerated *corpus bullets* (`011_a2`, `013_a1`, `013_a3`, `006_a2/a3/a4`, `020_a4`). This is the construction-bias signature.
2. **But inflation is not automatic for cross-document cases.** `017` and `018` are cross-document and stay at 3, matching every single-document case. The differentiator is not "multi-document" per se; it is whether the underlying policy text is a **bulleted list** that invites one-aspect-per-bullet scoring.
3. **Single-document cases are not artificially coarse.** `010`, `014`, `019` split rule / variant / process into 3 distinct aspects; `012` splits positive meaning / negative meaning / purpose. So at the 3-aspect level, granularity is symmetric.
4. **The asymmetry is confined to the top of the scale.** No single-document query exceeds 3; four cross-document queries reach 4–5. After the proposed `OPTIONALIZE` actions the ceiling drops to 4 for cross-document cases, but the ceiling gap does not fully close.
5. **No genuine over-splitting of one judgment into interchangeable wordings** was found; `011_a4`/`011_a5`, `013_a2`/`013_a3`, `012_a1`/`012_a2`, `017_a1`/`017_a2` are closely related but each encodes a distinct fact, so `MERGE` was not applied.

---

## E. Correlation Analysis (r = 0.754)

Reproduced from the frozen benchmark's author `multi_document` flag (9 cases) against the draft aspect counts:

- multi_document mean = **4.22**; single-document mean = **2.91**; overall mean = 3.50; r = **0.754** (verified by hand: 6.50 / √(4.95 × 15.0) = 0.754).

**Interpretation: MIXED, predominantly legitimate, with a bounded construction-bias component.**

Evidence for *legitimate correlation*
- Two cross-document cases (`017`, `018`) sit at 3 aspects — identical to every single-document case — so the author did not mechanically give cross-document queries more aspects.
- The single-document cases are not coarse: they split rule / exception / process into 3 separate aspects, the same granularity used inside the 4-aspect cross-document cases.
- The highest-count queries genuinely contain two distinct regulatory processes with distinct user-facing questions (content takedown vs account data; privacy removal vs copyright; Sponsors terms vs advertising rules), so more independent required facts are justified.

Evidence for *construction bias*
- The four 5-aspect queries each carry exactly one aspect that fails the necessity test (`006_a4`, `011_a2`, `013_a1`, `020_a4`). All four are cross-document. Their removal reduces the cross-document mean from 4.22 to 3.78; no single-document aspect failed the same test.
- Those four secondary aspects were derived by transcribing list items from the evidence rather than by asking "does the user need this?", i.e. the aspect author's granularity was influenced by seeing multiple separated evidence spans.

**After the proposed changes r ≈ 0.78** (recomputed below). The correlation staying high is expected and does **not** by itself indicate a problem: the residual contrast reflects genuine structural difference between two-process and one-process queries. The defect is not the coefficient; it is the four non-required secondary aspects it was inflating.

---

## F. Oracle-Bias Audit (scoring-contract structure only; no route prediction)

The question is whether the *scoring contract* systematically advantages the arm that retrieves more, independent of decomposition quality. It does so through four channels; the change set narrows three.

**A. More required scoring opportunities for cross-document queries.** Cross-document mean (4.22 pre / 3.78 post) vs single-document (2.91). More required aspects = more units on which a higher-coverage arm can gain and a lower-coverage arm can fail. Partly legitimate (more real user needs), partly the four secondary aspects (pre-fix).

**B. Secondary facts required-ized.** Confirmed: `006_a4` (restriction mechanism), `011_a2` (submission mechanics), `013_a1` (request-completeness background), `020_a4` (permission-scope review). These are precisely the facts most likely to appear incidentally when more retrieval streams are drawn.

**C. Disproportionate score from one extra minor fact.** The primary metric is all-or-nothing per query (`query_required_complete`), tie-broken by the covered fraction. With fine granularity, one extra retrieved chunk can flip one aspect and, under the all-or-nothing primary, decide a whole query. This magnifies the advantage of the higher-coverage arm. Removing the four secondary aspects reduces the number of "cheap flip" opportunities.

**D. Single-document coarser at the top end.** Single-document queries are not coarse at the 3-aspect level, but none exceed 3, so only cross-document queries can accumulate more scoring units. This residual asymmetry is **not** repaired by the change set (forcing single-document queries to 4–5 would require adding non-required aspects, which is prohibited). It should be documented as a known, bounded property of the contract rather than "fixed."

**Conclusion.** The contract is not *intentionally* biased, but before the change set it gave the higher-coverage arm a modest structural advantage via four secondary cross-document aspects. The `OPTIONALIZE` actions remove that specific channel; the residual ceiling asymmetry remains and is legitimate.

---

## G. Change Set Summary (aspect-level)

| action | count | aspects |
|---|---|---|
| KEEP | 65 | all others |
| EDIT | 1 | `router_016_a3` |
| MERGE | 0 | — |
| SPLIT | 0 | — |
| OPTIONALIZE | 4 | `router_006_a4`, `router_011_a2`, `router_013_a1`, `router_020_a4` |
| REMOVE | 0 | — |
| **total** | **70** | |

Dataset-level metadata change (no fact change): add a machine-readable assertion that supporting evidence is verified-but-not-exhaustive.

---

## H. Final Truth Statistics After Proposed Changes

- required aspect total: **70 → 66**
- min / median / mean / max (required): **2 / 3 / 3.30 / 4**
  - distribution: 2 → 1 query (`008`); 3 → 12 queries; 4 → 7 queries
- optional context total: **2 → 6**
- combined-support count: **4** (unchanged)
- corpus gap count: **0** (unchanged)
- single-document mean: **2.91** (unchanged — all four optionalized aspects were cross-document)
- multi-document mean: **4.22 → 3.78**
- Pearson r (aspect_count vs author `multi_document`): **0.754 → ≈0.776**

Recomputation (post-change): Σ(x−x̄)(y−ȳ)=4.30, Σ(x−x̄)²=4.95, Σ(y−ȳ)²=6.20 → r = 4.30/√(4.95·6.20) = **0.776**.

---

## I. Freeze Readiness

**READY.**

There is no structural problem that requires regenerating the truth. The contract is corpus-grounded and internally consistent; every proposed change is a local, deterministic operation on a named aspect or a support entry:

1. Apply the 4 `OPTIONALIZE` actions (move the listed aspects to `optional_context`, remove from `required_aspects`).
2. Apply the 3 `EDIT` actions (reword `router_016_a3`; fix support mapping for `router_015_a1` and `router_013_a4`).
3. Apply the dataset-level metadata assertion for non-exhaustive support; de-duplicate the repeated chunk entries in `router_011_a2` and `router_014_a1` (either removed or resolved by action 1).
4. Recompute the statistics in §H and hash-freeze the final file as `eval/router_v1_required_aspects.json`.

No aspect statement was found unsupported, so no query needs removal, and no routing label is introduced anywhere.

---

## Verification

1. `audit_blind_to_router_v1_outputs: true` — confirmed before reading any truth file.
2. Benchmark unchanged (SHA-256 `a345ccfd…acf16`).
3. Architecture unchanged (SHA-256 `fc6ad624…f575b`).
4. Preregistration unchanged (SHA-256 `79499cd5…34123`).
5. Contract unchanged (SHA-256 `fb548435…d9549`).
6. All 20/20 queries audited.
7. All 70/70 required aspects individually checked.
8. No routing labels created.
9. Router not run; Decomposer not run; DIRECT/DECOMPOSE not run; answer judge not run.
10. Draft truth not overwritten.
