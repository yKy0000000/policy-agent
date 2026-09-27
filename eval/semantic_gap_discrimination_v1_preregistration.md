# Semantic Gap Discrimination V1 — Preregistration (Mechanism / H1)

**Status: FROZEN for execution (2026-09-26).** Frozen before the first classification call; the document
SHA-256 is recorded in `eval/results/semantic_gap_discrimination_v1_results.json`. No repair generation, no
rewriting, no routing, no production change.

Parent chain: `Validate = COMPLETE → Repairability = COMPLETE → Mechanism (H1) → Routing`. Repairability
established that the current generator frequently misclassified human-confirmed genuine gaps as
`already_present` or `not_supported` under oracle guidance, while the stronger generator did not. This
experiment isolates **proposition-level semantic state classification** from repair generation, editing,
citation handling, URL constraints, and output rewriting.

## 1. Research question

When a model sees the query, the frozen baseline answer, the frozen evidence, and one human-confirmed atomic
proposition, can it correctly classify the proposition as:

- `MISSING`
- `ALREADY_PRESENT`
- `UNSUPPORTED`

No repair answer is generated in this experiment.

## 2. Label definitions (verbatim contract, shared by all models)

- `MISSING`: (1) the frozen evidence supports the proposition; (2) the proposition is relevant to the query;
  (3) the baseline answer does not semantically express it, or expresses it incompletely/incorrectly.
- `ALREADY_PRESENT`: (1) the frozen evidence supports the proposition; (2) the baseline answer already
  expresses it semantically; paraphrase / compression / merged expression count, literal wording is not
  required.
- `UNSUPPORTED`: (1) the frozen evidence does not support the proposition; (2) plausibility, topical
  relevance, or prior knowledge must not be accepted as support.

## 3. Dataset composition (frozen)

Total: 27 probe items = 2 `MISSING` + 19 `ALREADY_PRESENT` + 6 `UNSUPPORTED`.

### A. MISSING (n = 2)

Only the two human-confirmed genuine answer-level errors from the frozen cleaned cohort:

- `VAL-001-039-F02` — proposition = frozen rubric statement.
- `VAL-001-050-F01` — proposition = frozen rubric statement.

Explicitly excluded: `VAL-001-008-F02` (confirmed non-atomic target / ambiguity). No synthetic missing items
are created to balance the dataset. MISSING n = 2 is reported honestly and no population inference is made.

### B. ALREADY_PRESENT (n = 19)

All human-confirmed present facts, atomic and evidence-clear:

- 17 items from the Measurement Validity human-review writeback with `human_adjudication =
  SEMANTICALLY_PRESENT` (7 nominal facts + 10 covered-side facts); proposition = frozen rubric statement;
- 2 items from the frozen Oracle Repair V1 already-present controls (`VAL-001-039-F01`, `VAL-001-050-F02`);
  proposition = the frozen control proposition text.

The 17 MVA items are paraphrase / compression cases (the V2 adjudicator tagged all as `paraphrase`), not
literal copies. No re-adjudication is performed.

Preregistered gold caveat: `VAL-001-050-F05` — the baseline names GPLv2 as a Covered License while the fact
statement also includes LGPLv2/LGPLv2.1; the frozen human review nonetheless recorded
`SEMANTICALLY_PRESENT`. The primary analysis keeps the frozen gold; a preregistered sensitivity analysis
excluding this single item is also reported.

### C. UNSUPPORTED (n = 6)

Each proposition is validated against the **full** frozen BGE Top5 evidence (not only an anchor span): no
sentence entails it and none contradicts it; plausibility alone is insufficient.

| id | case | proposition | validation |
|---|---|---|---|
| U-039-01 | VAL-001-039 | GitHub's source-code offer expires one year after the Software release. | frozen Oracle Repair V1 sham (non-entailment/non-contradiction review recorded) |
| U-039-02 | VAL-001-039 | GitHub must deliver the complete source code of open-source components within 30 days of a written request. | preregistered alternate sham; no timeline sentence in any chunk |
| U-039-03 | VAL-001-039 | GitHub provides a written warranty for the Software's open-source components. | no warranty sentence in the full Top5 (including Miscellanea) |
| U-039-04 | VAL-001-039 | The Software's open-source components are licensed under the MIT license. | no license is named; only "open source software license agreements" |
| U-050-01 | VAL-001-050 | GitHub must reimburse a violator's reasonable legal costs after the violation is cured. | frozen Oracle Repair V1 sham (non-entailment/non-contradiction review recorded) |
| U-050-02 | VAL-001-050 | GitHub must publish an annual compliance report for this Commitment. | no reporting duty; the only publication is new editions of the commitment |

Marker-absence scans over the full evidence text are recorded per item in the results artifact.

## 4. Input format and leakage rules

Each probe item exposes only: (1) query, (2) frozen baseline answer, (3) frozen evidence (full BGE Top5 in
production `[S1]..[S5]` format), (4) the atomic proposition.

Never exposed in the prompt: gold label, original evaluator label, human review verdict, item class/source,
repairability result, model history, anchor span, or any phrase indicating whether the item is missing,
already present, or unsupported. The three label tokens appear only in the shared system schema.

## 5. Prompt contract (identical for both models)

System: classifier role; the three label definitions above; evidence-only judgement; no repair, no revised
answer, no rewriting; brief justification only.

User template:

```text
Question:
{query}

Baseline answer:
{baseline_answer}

Frozen evidence:
{formatted S1..S5 evidence}

Atomic proposition:
{proposition}

Return only the JSON object.
```

Output schema:

```json
{"label": "MISSING | ALREADY_PRESENT | UNSUPPORTED",
 "evidence_source_ids": ["S1"],
 "answer_support": "brief semantic justification (<= 40 words)"}
```

`label` is the primary metric; `evidence_source_ids` and `answer_support` are auxiliary only.

## 6. Models, budget, replicates

- current model: `deepseek-v4-flash` (the Repairability current generator);
- stronger model: `deepseek-v4-pro` (the Repairability stronger generator).

Identical probe set, prompt, evidence, schema, temperature `0.0`, `max_tokens = 200`, timeout 120 s.
3 replicates per item x model (27 x 2 x 3 = 162 calls). Replicates are pre-declared; no selective rerun
after seeing results. Technical failures are reported, not silently retried into success.

## 7. Primary endpoints

1. Confusion matrix per model: gold (rows) x modal predicted label (columns). Modal label = majority of the
   3 replicates; if all three differ, the item x model is `INCONSISTENT` and excluded from the matrix
   (reported separately, never imputed).
2. Per-class recall for `MISSING`, `ALREADY_PRESENT`, `UNSUPPORTED`.
3. `MISSING → ALREADY_PRESENT` and `MISSING → UNSUPPORTED` counts (the Repairability-linked errors).
4. Consistency per item x model: 3/3 same, 2/3 majority, 0/3 (all different).

Secondary: overall accuracy (never a substitute for per-class metrics); strict 3/3-agreement confusion matrix
as sensitivity; auxiliary evidence-ID validity; the 050-F05 exclusion sensitivity; item-level readout for
`VAL-001-039-F02` and `VAL-001-050-F01`.

## 8. Interpretation rules (fixed before execution)

Operational mapping for this n = 2 MISSING design (fixed now, before any call):

- **Outcome A**: the current model's modal label is not `MISSING` for at least one of the two MISSING items,
  and the stronger model's modal label is `MISSING` for both → **H1 supported**, limited to: "the current
  model shows weaker proposition-level semantic gap discrimination under the frozen-evidence condition".
  Next: prioritize H3 (proposition-level entailment / evidence load).
- **Outcome B**: the current model's modal label is `MISSING` for both MISSING items (regardless of the
  stronger model) → **H1 weakened; H2 rises** (instruction / repair-task framing / conservative action
  policy); test task framing next.
- **Outcome C**: current and stronger produce identical modal labels on every item → the Repairability
  difference cannot be attributed mainly to semantic gap discrimination; **prioritize H2**.
- **Mixed/unresolved**: anything else; reported descriptively without a stage switch, with the per-class and
  consistency tables carrying the evidence.
- **Outcome D**: if current is correct under this full-Top5 condition, no short-span claim may be made. This
  experiment does not vary evidence length, so only "H3 remains plausible" may be recorded; an
  evidence-length / entailment experiment would be needed later.

## 9. Limitations (declared)

- `MISSING` n = 2: mechanism-diagnostic evidence only; no statistical generalization about the models.
- Items cluster by case/evidence/query; effective sample size is lower than item count.
- Human gold is a single-reviewer frozen review; no re-adjudication is performed.
- Full BGE Top5 only; no short-span or evidence-ordering conditions.
- No prompt-framing variation; no repair generation; H2 and H3 are untouched by design.

## 10. Artifacts and integrity

- runner: `eval/run_semantic_gap_discrimination_v1.py` (offline dataset build + classification);
- cache: `cache/semantic_gap_discrimination_v1_cache.json`;
- results: `eval/results/semantic_gap_discrimination_v1_results.json` and
  `eval/results/semantic_gap_discrimination_v1_summary.md`;
- frozen inputs (Validate and Repairability artifacts, rubric, queries, benchmark) are hash-verified; no
  production/rubric/benchmark change.

## 11. Stop condition

Report dataset composition, both confusion matrices, per-class recall, MISSING→ALREADY_PRESENT,
MISSING→UNSUPPORTED, consistency, whether 039/050 reproduce the Repairability failure pattern, whether H1 is
supported/weakened/unresolved, and whether H2 or H3 should be prioritized next. Then stop. Do not execute
any follow-up experiment.
