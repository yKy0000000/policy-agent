# Candidate Discovery V1 — Preregistration

**Status: PRE-FREEZE canonical draft (materialized from the agreed design; no model call has been made).**

This document materializes the agreed Candidate Discovery V1 design into an executable, red-teamable,
hash-freezable preregistration. No architecture, model, verifier, agent, or experiment branch is added
beyond what is written here. Pre-flight appendices (A, C) must be completed and the external freeze manifest
(`eval/candidate_discovery_v1_freeze_manifest.json`, §14) recorded before the first model call.

Research-chain position: `Validate ✅ → Repairability ✅ → Mechanism H1 ✅ → Mechanism H2 ✅ → Mechanism H3 ✅
→ Routing design → Candidate Discovery V1`.

## 1. Purpose / scope

Candidate Discovery V1 answers exactly one question:

> Given `query + frozen BGE Top5 evidence + frozen baseline answer`, and **without** any gold proposition or
> rubric, can a model discover a missing proposition that is:
>
> - evidence-supported;
> - not yet expressed by the baseline answer;
> - substantively required by the current query;
> - sufficiently atomic;
> - directly usable as a downstream minimal-repair target?

This experiment:

- does **not** execute repair;
- does **not** train a router;
- does **not** estimate production prevalence;
- is **not** deployment evidence;
- is a low-cost falsification / feasibility screen only.

### 1.1 Canonical terms

| term | meaning in this document |
|---|---|
| natural positive | a candidate target that passed the §3 two-reviewer `QUERY_REQUIRED` pre-flight |
| complete control | a case whose full query-conditioned answer completeness was human-audited per §4.2 |
| stress case | a fixed case/target pair used only to measure false proposals on a designated already-present proposition |
| synthetic input | a complete control whose baseline was minimally edited to remove one justified fact, per §4.4 |
| call | one model API request; 3 identical-setting calls per model per input |
| planned call | one of the 3 pre-registered identical-setting calls per model per input; all denominators are 3 planned calls and are never redefined by completion counts |
| replicate | one of the 3 identical-setting calls; measures API behavioral stability, not stochastic diversity |
| input | one frozen (query, evidence, baseline) triple assigned to a group |
| sufficient match | a candidate satisfying all §9 criteria, judged by the §9.1 human annotation protocol |

## 2. Value vs Reachability positioning

- Oracle analysis (existing frozen artifacts) tests the **Value** condition: if the correct missing
  proposition were known, would repair be worth it?
- Candidate Discovery V1 tests the **Reachability** condition: can the missing proposition be found at all,
  without oracle information?
- Both are **necessary but not sufficient** conditions for semantic routing.
- This experiment tests Reachability only.
- Existing frozen artifacts may support a separate partial oracle analysis with **zero new API calls**, but
  that analysis is **not part of this experiment's primary result**.

## 3. Pre-flight eligibility

Natural-positive candidates are fixed as:

- `VAL-001-039` / `F02`
- `VAL-001-050` / `F01`

Before **any** model call, two human reviewers independently label each item:

- `QUERY_REQUIRED`
- `RELEVANT_BUT_OPTIONAL`
- `AMBIGUOUS`

Reviewers are blind to each other and to all model outputs; both labels are recorded verbatim. Reviewers see
the query, the frozen baseline answer, the frozen evidence, and the frozen candidate proposition text
(Appendix B), and answer:

> If the current baseline answer lacks this proposition, would the answer to the current query be
> substantively incomplete?

Reviewer history and vision scope:

- where available, reviewers must be fresh reviewers who did not participate in the earlier 039/050
  measurement-validity review, Oracle Repair V1, or Mechanism H1/H2/H3;
- each reviewer's visible-information scope is recorded in Appendix A1;
- reviewers must not see:
  - the prior ABSENT / PRESENT human labels for these items;
  - H1 / H2 / H3 results;
  - Oracle Repair results;
  - the historical reasons these cases were selected;
- if prior knowledge cannot be fully eliminated, it must be recorded as an explicit limitation, and the
  review must not be described as fully blinded.

Rules:

- only when **both** reviewers label `QUERY_REQUIRED` does the item enter the primary natural-positive set;
- reviewer disagreement must **not** be resolved by discussion into `QUERY_REQUIRED`;
- disagreement, `RELEVANT_BUT_OPTIONAL`, and `AMBIGUOUS` all mean the item does not have primary-positive
  eligibility;
- if fewer than two natural positives remain eligible:

  **`Candidate Discovery V1 = DESIGN NOT EXECUTABLE`**

  Stop; make no model call. This is a pre-execution design status, **not** a discovery failure and not an
  `INCONCLUSIVE` result (see §12); it must never be written as a model failure. Natural positives must not be
  replaced after the fact.

The original human ABSENT / PRESENT labels are retained; no old experiment is rewritten.

## 4. Frozen case groups

### 4.1 Natural positives

Only `VAL-001-039-F02` and `VAL-001-050-F01`, and only if both pass §3.

### 4.2 Complete controls

Pool: the original candidate complete pool =

- cases whose baseline arm is grounded-fact-complete
  (`eval/results/generation_utilization_results.json`, `arms.baseline.quality.grounded_fact_complete == true`);
- excluding natural-positive cases;
- excluding the four stress cases (§4.3).

`grounded_fact_complete == true` is used **only** to construct the deterministic candidate pool.

Ordering: ascending `SHA-256(UTF-8("candidate-discovery-v1" + case_id))` hex digest.

A human reviewer must audit the **entire query-conditioned answer completeness** for each case in that
order. Final control eligibility requires this new query-conditioned human completeness audit; the old
evaluator label is not the eligibility criterion.

The audit uses **only** `query + frozen evidence + baseline answer`. The reviewer independently derives the
query's requirements and must **not** use the old evaluator's fact list as the audit checklist. A case passes
the audit only when the reviewer finds no executable, query-required content that is absent. The audit
records, per requirement:

- the query requirement;
- its evidence support;
- whether the baseline expresses it (present / absent);
- the decision reason.

Take the first four cases that pass. All excluded cases and the reasons for exclusion must be written to
Appendix A **before the first model call**. Once four controls are frozen they must not be replaced.

Control results are a screening signal conditional on this frozen pool; they must not be reported as a
production precision estimate.

### 4.3 Precision stress cases

Fixed:

| case | designated target |
|---|---|
| `VAL-001-009` | `F02` |
| `VAL-001-022` | `F02` |
| `VAL-001-026` | `F02` |
| `VAL-001-037` | `F01` |

These targets were previously human-present and were over-strictly flagged by a model. Stress cases are used
only to measure false proposals on the designated target proposition.

Unless the entire case has separately completed a full query-conditioned completeness audit, other
candidates proposed on a stress case must **not** automatically count as false positives; they are recorded
verbatim for descriptive reporting only.

`VAL-001-008` does not enter the main analysis.

### 4.4 Synthetic deletion

Two of the four human-confirmed complete controls are pre-selected as synthetic sources: the first two
controls in the frozen §4.2 hash order. The mapping is recorded in Appendix A before any model call.

For each source, exactly one piece of answer content carrying a **single, query-required, atomic,
evidence-supported** fact is deleted. The chosen fact and the deleted text are recorded in Appendix A before
any model call. After deletion:

- the query is unchanged;
- the evidence is unchanged;
- all other facts remain;
- the answer's grammar and discourse must read naturally;
- citation / reference structure must not show a visible break;
- no obvious deletion scar may remain.

Minimal surface edits are allowed only to remove mechanical deletion traces and must not change semantic
content.

The scar reviewer must not know the deletion target and must not be the reviewer who performed the deletion.
The following are saved in the frozen input manifest artifact and Appendix A4:

- the before baseline;
- the after synthetic baseline;
- the exact diff;
- the deleted target;
- the surface-only edits.

A reviewer independent of the deletion editor confirms that the surface edits introduced or removed no extra
semantics. This semantic-diff check may know the diff and the deleted target; it is a separate role from the
target-blind scar check. The scar reviewer labels each synthetic input:

`OBVIOUS_DELETION_SCAR = YES / NO`

Only `NO` admits the synthetic input into synthetic calibration. A synthetic input that fails is dropped; if
both fail, synthetic calibration is reported as not constructed.

Synthetic inputs are used for **calibration only**:

- they do not enter the primary positive denominator;
- they do not enter the primary pass condition;
- synthetic success cannot offset a natural-positive failure;
- synthetic construction failure is a calibration caveat only and never triggers `INCONCLUSIVE` or blocks
  the primary experiment.

## 5. Models / calls

Models are fixed:

- `deepseek-v4-flash`
- `deepseek-v4-pro`

For each frozen input: 3 identical-setting calls; `temperature = 0`; all other decoding parameters frozen.

If natural positives = 2, complete controls = 4, stress = 4, synthetic = 2:

`12 inputs × 2 models × 3 replicates = 72 calls.`

Replicate interpretation is frozen:

> Replicates measure API-level behavioral stability under identical decoding settings, not stochastic
> sampling diversity.

Statistical wording is frozen:

- the 3 replicates are correlated identical-setting behavioral checks;
- no iid Bernoulli inference is made from them;
- no production precision / recall confidence intervals are computed;
- the `≤ 1/12` control threshold is a preregistered screening threshold, not a precision estimator.

Prohibited:

- treating replicates as independent Bernoulli observations for production-grade confidence intervals;
- selecting the best replicate;
- rerunning because the content is unsatisfying.

Transport / format failures must be recorded per call, without replacement calls, and are handled by §12.

## 6. Frozen prompt task

The only task: find atomic propositions that are evidence-supported, not yet expressed by the baseline
answer, and substantively required to answer the current query.

Requirements:

- at most 5 candidates;
- ordered by importance;
- an empty array is allowed;
- no repair;
- no confidence output;
- no access to gold fact IDs, gold propositions, or the matching rubric.

The literal model-visible prompt string must exist in a defined frozen artifact; its path and SHA-256 are
recorded in the external freeze manifest (§14) before any call. It must be a direct rendering of the
contract above and of the §7 schema, and must not change after the first call.

Model-visible inputs are constructed **only** from the frozen input manifest (Appendix C) and this literal
prompt. Appendix B (gold propositions and qualifiers), stress targets, and any preregistration content must
never enter model-visible input assembly.

## 7. Output schema

Fixed JSON:

```json
{"candidates":[{"proposition":"...","source_id":"S1","evidence_span":"...","reason":"..."}]}
```

Rules:

- `proposition` is the only downstream repair target;
- `source_id` must correspond to a frozen evidence source;
- `evidence_span` must be a short span locatable verbatim in that source;
- if the proposition requires two spans jointly, exactly one optional second pair of fields,
  `source_id_2` and `evidence_span_2`, may be added; no other fields are permitted;
- `reason` is for explanation and debug only.

Frozen:

> `SUFFICIENT MATCH` must be satisfied by the `proposition` field itself. The `reason` field must not supply
> any actor, condition, time, scope, exception, or other key qualifier that the proposition omits.

## 8. Deduplication

Only **within-case exact-context deduplication** is allowed.

The frozen dedup key is:

`case_id + whitespace-normalized proposition + ordered support tuple(s)`

where a support tuple is `(source_id, exact evidence_span)`, and, when present, the second tuple is
`(source_id_2, exact evidence_span_2)`.

Rules:

- candidates share a single human verdict only when the full key is identical;
- different evidence spans do not share a verdict and are scored separately;
- cross-case deduplication is prohibited;
- semantic-approximate deduplication is prohibited;
- the same proposition appearing in different cases must be re-scored, because query relevance, baseline
  presence, and evidence support may differ;
- within a case, a shared verdict is backfilled only to replicate positions with the identical key;
- the number of deduplicated candidates must not be treated as a count of statistically independent samples.

## 9. Human evaluation rubric

Human-primary evaluation. No new LLM judge may decide a primary endpoint. Reviewers score with **model
identity and replicate identity hidden**.

### 9.1 Human-primary annotation protocol (frozen)

1. Deduplicate within-case by the §8 exact key, then build the anonymous candidate list.
2. Hide model identity and replicate identity.
3. Two reviewers independently annotate every candidate that could affect a primary endpoint.
4. Initial labels are retained.
5. Disagreements must be adjudicated before unblinding, using the frozen rubric.
6. If adjudication still cannot decide:
   - a natural-positive candidate does not count as `SUFFICIENT MATCH`;
   - a control candidate is marked `annotation-uncertain`, which makes the corresponding primary control
     component non-evaluable;
   - disagreement is never automatically counted as a model error.
7. All final labels are frozen and hashed before unblinding; the label table hash is recorded in the results
   artifact before unblinding.

### 9.2 SUFFICIENT MATCH

The candidate `proposition` itself:

1. hits the frozen target core;
2. is substantively required by the query;
3. is not yet expressed by the baseline answer;
4. is supported by valid evidence / a valid locatable span;
5. retains all frozen key qualifiers (Appendix B);
6. is atomic;
7. shows no scope drift;
8. is repair-ready as written.

Semantically equivalent paraphrase is allowed.

### 9.3 PARTIAL MATCH

- hits the target core;
- has valid evidence support;
- but has a qualifier / scope / atomicity problem;
- and therefore cannot be used directly as a repair target.

Partial does not count as a primary hit.

### 9.4 MISS

- target core not hit;
- not required by the query;
- already expressed by the baseline;
- not supported by the evidence;
- evidence span not locatable;
- structurally invalid output.

### 9.5 Classification precedence

The classes are mutually exclusive, with frozen precedence `SUFFICIENT MATCH > PARTIAL MATCH > MISS`.
`reason` can never supplement missing proposition qualifiers.

### 9.6 VALID_NON_GOLD_FINDING

A `VALID_NON_GOLD_FINDING` (VNGF) is a candidate that independently satisfies the same criteria as
`SUFFICIENT MATCH`:

- query-required;
- baseline missing;
- evidence entailed;
- atomic;
- qualifier-complete;
- no scope drift;
- repair-ready;

but corresponds to no frozen target P. It must pass the same §9.1 human-primary blinded annotation protocol.

If a complete control has a confirmed VNGF:

- that control is no longer eligible for the primary complete-control PASS component;
- consequently PASS cannot be established;
- the other candidates on that control are still annotated one by one and reported;
- false proposals must not be hidden because of the VNGF;
- the VNGF must not be added to the primary gold set after the fact.

### 9.7 EXECUTABLE_BUT_UNNECESSARY_OR_INCORRECT_CANDIDATE

Used for complete-control scoring. A candidate that is executable (atomic, span-grounded, repair-ready per
this section) but is:

- unnecessary (already expressed by the baseline, or not query-required); or
- incorrect (not entailed by the cited evidence, or with wrong key qualifiers).

Non-executable candidates (non-atomic, unlocatable span, schema-invalid, compound) are reported separately
under §11 and do not count toward the primary control-error count.

## 10. Primary endpoints

### Natural positives

Per model, per case, across the 3 planned calls report:

`SUFFICIENT MATCH count = 0–3`

At most one hit per target per call: a call records 1 hit if it contains at least one `SUFFICIENT MATCH` for
the target, otherwise 0; this is not satisfied by `PARTIAL MATCH`. Missing replicates are handled by §12 and
never redefine the denominator.

The two natural positives are **not** aggregated into a production recall estimate.

### Complete controls

Per model, across the 4 complete controls × 3 calls (= 12 planned calls), report the number of calls
containing at least one `EXECUTABLE_BUT_UNNECESSARY_OR_INCORRECT_CANDIDATE`.

Also report:

- candidate-level error types;
- empty-array rate;
- repeated same-error behavior (same deduplicated erroneous candidate on the same control in ≥ 2/3 of the
  3 planned calls).

The `≤ 1/12` control condition is a preregistered screening threshold over correlated identical-setting
calls, not a precision estimator; no confidence intervals are computed.

Synthetic and stress inputs must not fill a primary denominator.

## 11. Secondary endpoints

- top-1 / top-3 / top-5 natural-positive hit;
- PARTIAL matches;
- stress-target false proposals;
- synthetic hits;
- source / span validity;
- atomicity;
- candidates per call;
- tokens;
- latency;
- output-format failures;
- API behavioral stability (label agreement across the 3 identical-setting calls per input; no iid
  inference).

## 12. Screening decision

There is no priority ordering. The outcome is determined by the following decision tree.

### Preflight

If fewer than two eligible natural positives remain after §3: `DESIGN NOT EXECUTABLE`. This status occurs
before the first model call.

### After execution

Transport / format failures are recorded and never replaced. All `2/3` and `3/3` refer to the 3 planned
calls, never to a redefined completed-call denominator.

**STOP CURRENT TESTED DISCOVERY TRACK**

Stop if, for any eligible natural positive:

- both models have all 3 planned replicates completed (6 completed calls total); and
- none of the 6 completed calls contains a `SUFFICIENT MATCH`.

This STOP can be established independently of control-component evaluability.

Scope of the stop:

> the current semantic-discovery routing research track under the tested model family, one-shot prompt,
> frozen evidence representation, and K = 5 architecture.

It must not be generalized to:

> semantic routing is impossible in principle.

**PASS TO LARGER VALIDATION**

Only when at least one model simultaneously satisfies:

- both natural-positive cells for that model have all 3 planned calls completed;
- both natural positives show `SUFFICIENT MATCH` in ≥ 2/3 planned calls (at least 2 of 3);
- all four complete controls remain valid complete controls after model-output review;
- all 12 planned complete-control calls are completed;
- the preregistered control-error conditions hold (at most 1 call containing an
  `EXECUTABLE_BUT_UNNECESSARY_OR_INCORRECT_CANDIDATE`, and no single erroneous candidate repeating stably
  ≥ 2/3 on the same control).

Meaning is limited to: `eligible for larger validation`.

This must not be written as: deployable; high recall; high precision; production-ready.

**INCONCLUSIVE**

If there is no STOP and no PASS, and any of the following holds:

- necessary replicates are missing;
- a control is no longer a valid complete control because of a VNGF;
- annotation cannot adjudicate;
- any other primary component is non-evaluable;

then the result is `INCONCLUSIVE`.

`INCONCLUSIVE` must not be rewritten as `PASS` after the fact.

## 13. Prohibited post-hoc changes

After the first model call, it is prohibited to modify:

- natural positives;
- controls;
- stress cases;
- synthetic grouping;
- query;
- evidence;
- baseline;
- source IDs;
- evidence ordering;
- the literal prompt artifact and its recorded path / SHA-256;
- K;
- model;
- decoding / request config;
- replicate count;
- matching rubric;
- the Appendix B gold qualifier table;
- annotation labels, adjudication outcomes, and the pre-unblinding label-table hash;
- the frozen input manifest and the external freeze manifest;
- thresholds;
- STOP / PASS / INCONCLUSIVE rules;
- failure accounting.

Prohibited:

- adding gold after seeing outputs;
- selecting a favorable replicate;
- redefining PARTIAL;
- offsetting a natural-positive failure with synthetic success;
- folding a `VALID_NON_GOLD_FINDING` into the primary gold set;
- using replicates or deduplicated candidates as independent iid samples for production statistical
  inference.

## 14. Freeze record

There is no self-referential hash inside this document. The preregistration SHA-256 is computed directly
from the final prereg file bytes at freeze time and is not written back into the preregistration.

At preflight freeze, an external manifest is recorded at:

`eval/candidate_discovery_v1_freeze_manifest.json`

containing at least:

| field | content |
|---|---|
| prereg path + SHA-256 | path to this file; SHA-256 of its final bytes |
| literal prompt path + SHA-256 | path to the frozen prompt artifact; its SHA-256 |
| frozen input manifest path + SHA-256 | path to the input manifest (Appendix C); its SHA-256 |
| complete model / decoding config | model identifiers, temperature, max output tokens, timeout, reasoning / thinking setting (if applicable), JSON / schema mode (if applicable), retry policy, and any per-model override |
| freeze timestamp | UTC |

The git freeze commit SHA is not written back into the same committed artifact; after the commit is made it
is recorded externally and reported.

This section specifies the process only; no final freeze hash is created at the time of this draft. No model
call may be made until the external freeze manifest is recorded.

---

## Appendix A — Case-group pre-flight record (completed before the first model call)

### A1. Natural-positive eligibility

| item | reviewer 1 | reviewer 2 | consensus | eligible |
|---|---|---|---|---|
| `VAL-001-039-F02` | TBD | TBD | TBD | TBD |
| `VAL-001-050-F01` | TBD | TBD | TBD | TBD |

Also recorded per reviewer: the visible-information scope, participation history in prior 039/050
measurement / Oracle Repair / H1–H3 work, and any residual prior knowledge (explicit limitation).

### A2. Complete-control pool, hash order, and audit

Ordering rule: ascending `SHA-256(UTF-8("candidate-discovery-v1" + case_id))`.

| order | case_id | hash | audit result | exclusion reason (if any) |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

Frozen complete controls (first four passes): TBD.

#### A2b. Per-requirement audit record

The audit is based only on `query + frozen evidence + baseline answer`; the old evaluator fact list is not
used as the checklist.

| case_id | query requirement | evidence support | baseline present / absent | decision reason |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

### A3. Stress cases

Frozen per §4.3; no record needed beyond the fixed table.

### A4. Synthetic mapping, saved artifacts, and scar checks

| synthetic input | source control | deleted target fact | before baseline | after synthetic baseline | exact diff | surface-only edits | semantic-diff reviewer | scar reviewer verdict | admitted |
|---|---|---|---|---|---|---|---|---|---|
| S1 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| S2 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Pre-flight freeze gate: no model call may be made until A1, A2 (including A2b), A4 and Appendix C are
complete and the external freeze manifest (§14) is recorded.

## Appendix B — Frozen gold propositions and matching reference

Natural-positive target propositions (frozen atomic statements from
`eval/validation/broad_atomic_facts_validation_v1.json`):

| case | fact | frozen proposition |
|---|---|---|
| `VAL-001-039` | `F02` | GitHub offers source code where component licenses require such an offer. |
| `VAL-001-050` | `F01` | The commitment applies before GitHub brings a non-defensive claim arising from termination of a Covered License. |

Stress designated targets (same source; used only for false-proposal measurement):

| case | fact | frozen proposition |
|---|---|---|
| `VAL-001-009` | `F02` | A complainant can send this kind of report through GitHub's DMCA contact form. |
| `VAL-001-022` | `F02` | Disclosed data must be used consistently with the candidate privacy statement. |
| `VAL-001-026` | `F02` | The developer must follow GitHub's technical specifications and requirements. |
| `VAL-001-037` | `F01` | The developer agreement covers Marketplace products offered free or for a fee. |

### B1. Frozen key qualifiers (frozen before the first model call)

Qualifiers are drawn only from the frozen proposition itself; no detail that appears only in the evidence and
is not required by the gold proposition may be added. "None specified" means the frozen proposition does not
express that qualifier and reviewers must not require it.

| target | target core | subject | action | condition | timing | scope | exception |
|---|---|---|---|---|---|---|---|
| `VAL-001-039-F02` | GitHub makes an offer to provide source code | GitHub | offers to provide source code | the applicable component licenses require such an offer | none specified | source code of components whose licenses require the offer | none specified |
| `VAL-001-050-F01` | the commitment applies before GitHub brings a claim | the commitment / GitHub | applies before GitHub brings the claim | the claim is non-defensive and arises from termination of a Covered License | before GitHub brings the claim | claims arising from termination of a Covered License | defensive claims fall outside the "non-defensive" condition |
| `VAL-001-009-F02` | a complainant can send this kind of report through the DMCA contact form | a complainant | can send this kind of report | through GitHub's DMCA contact form | none specified | "this kind of report" as the case's report type | none specified |
| `VAL-001-022-F02` | disclosed data must be used consistently with the candidate privacy statement | disclosed data | must be used consistently with | none specified | none specified | the candidate privacy statement | none specified |
| `VAL-001-026-F02` | the developer must follow GitHub's technical specifications and requirements | the developer | must follow | none specified | none specified | GitHub's technical specifications and requirements | none specified |
| `VAL-001-037-F01` | the developer agreement covers Marketplace products | the developer agreement | covers | none specified | none specified | Marketplace products offered free or for a fee | none specified |

Matching is judged by §9 through the §9.1 protocol against these frozen propositions and qualifiers; `reason`
cannot supplement the proposition's qualifiers.

## Appendix C — Input manifest (completed before the first model call)

Frozen input manifest:

- file path: `eval/results/candidate_discovery_v1_input_manifest.json`;
- canonical JSON serialization: UTF-8 bytes of `json.dumps(obj, ensure_ascii=False, sort_keys=True,
  separators=(",", ":"))` plus a single trailing `\n`; its SHA-256 is recorded in the external freeze
  manifest;
- evidence ordering: the frozen BGE Top5 order as stored, `S1..S5`;
- query: verbatim from `eval/validation/broad_queries_validation_v1.json`;
- baseline: verbatim from `eval/results/generation_utilization_results.json` (baseline arm), except
  synthetic inputs, whose baseline is the recorded §4.4 after-edit text;
- source IDs: `S1..S5` in the frozen evidence order;
- exact evidence text: chunk text verbatim from
  `eval/results/reranker_transfer_results.json`, `preparation.arms.bge_top5`.

| input_id | group | case_id | query SHA-256 | evidence SHA-256 | baseline SHA-256 | synthetic source | calls planned |
|---|---|---|---|---|---|---|---|
| TBD | natural_positive / complete_control / stress / synthetic | TBD | TBD | TBD | TBD | TBD | 2 models × 3 replicates |

Model-visible inputs are assembled only from this manifest and the literal prompt. Appendix B content (gold
propositions, qualifiers, stress targets) must never enter model-visible input assembly.
