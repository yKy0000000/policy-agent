# Query-Aware Retrieval V1 — Stage 0 Freeze (A0-BGE Baseline & Measurement Contract)

**Status: STAGE 0 COMPLETE; technical gates PASS.** No A1/A2/A3 code is implemented; no LLM/model call was
made for this freeze. Replay command: `python -m eval.run_stage0_replay --check` (offline).

## 1. Config identification

| | Repository default | Research A0-BGE (shared Stage 1 baseline) |
|---|---|---|
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (`src/reranker.py`) | `BAAI/bge-reranker-base` |
| Evidence policy | `fixed_top5`, k=5 (`src/agent.py`) | `fixed_top5`, k=5 |
| Candidate stage | Lexical Top20 + Semantic Top20 → union → chunk-ID dedup | same, frozen union hash `0b217aea…` |
| Generation | `.env` model, `grounded-policy-answer-v1` | same |
| Role | production default; not comparable to A0-BGE | Stage 1/2/3 common baseline |

Separation note: the two configurations must never be compared as one baseline; all Stage 1 arms share
the A0-BGE retrieval stack and differ only in context allocation policy.

The frozen reranked orders were recomputed locally from the frozen unions and reproduce the transfer
artifact exactly: **0/50 Top5 mismatches**, union hash matches, evidence tokens match.

## 2. Frozen artifacts and hashes

| Artifact | SHA-256 |
|---|---|
| `eval/query_aware_stage0_config.json` | `744ed411e301aaf28a3751be99c31157b26dcbcf524673f749aa711d2a82e3a6` |
| `eval/query_aware_router_v1.json` | `dcc7d4953f3ba9794c35f2168e29f419bbb40eb014775cf8ccb5e0e7ae913bd7` |
| `eval/query_aware_arms_v1.json` | `18d7adbfd1ac8a1802dbf29d2c222fb988d0c495ca4f979c24297a406f0112c9` |
| `eval/results/a0_bge_rerank_orders.json` | `fb15b316c4b5170514e6f1c5140689ba0e77869dd516b7c7e170593c4db5b2e2` |
| `eval/results/human_truth_stage0_worksheet.json` | `86926d6290a60f5a9b9b1ad2ffa638a6206e028bfa0d97a8581f7aa632f3244b` |
| `eval/results/stage0_replay_results.json` | `5e7d665bdae13803dd00d39756881f55e5a6792eb01ca37d0e2f63a4e1563703` |
| `eval/human_truth_contract_v1.md` | `1b131832cbca8d3529473d65dbb3c48ea80957c88aead225f147ff6870aa6d74` |
| `eval/economics_contract_v1.md` | `8ec4f46dc10e9fc36fdee9dd17b34915ae6cd2eef8b7c969a6504208e5c77540` |

Derived freeze values: router rule hash `04bb954e…`, `adaptive_prefix_v1` config hash `b2754711…`,
`coverage_selector_v2` config hash `c8e42bb7…`, A2 shared-rerank rule hash `103cbeb6…`,
mechanism-vs-adoption rule hash `b83c49e4…`. The config artifact records 36 input/source hashes verified by
the harness.

## 3. Stage 0 deliverables

1. **Five arms frozen** (`eval/query_aware_arms_v1.json`): `fixed_top5`, `adaptive_prefix_v1`,
   `coverage_selector_v2`, `no_router_adaptive_v1` (evidence-side score-gap prefix; query text prohibited),
   `query_router_v1` (SIMPLE → fixed Top5; BROAD → adaptive). Policy IDs, signals, params, cache-key schema
   (`stage1_generation_key` includes `context_policy_id` + `context_policy_hash`), and reuse rule are frozen.
2. **Router rule frozen** (`eval/query_aware_router_v1.json`, `query-structure-router-v1`): 5 deterministic
   signals; conservative default to BROAD; no LLM; frozen distribution V1 = 29 BROAD / 21 SIMPLE,
   V3 = 9 BROAD / 7 SIMPLE. Note: the rule detects multi-ask structure, not topical breadth.
3. **Human truth rules frozen** (`eval/human_truth_contract_v1.md`); worksheet materialized for 239 V1
   aspects + 92 V3 required aspects (331 rows, verdicts pending); 8 SIMPLE sentinels frozen:
   `VAL-001-002, -004, -010, -013, -015, -027, -030, -032`.
4. **Economics contract frozen** (`eval/economics_contract_v1.md`): provider tokens authoritative; evidence
   tokens diagnostic; latency p50/p95 via live trace; preregistered material-benefit / material-regression /
   complexity-deletion rules; mandatory reporting table.
5. **A2 shared-rerank rule frozen** (in arms JSON): per-query BGE ordering only; merged pool ordered by
   min within-query rank with tie-break; **raw scores from different queries must never be compared**.
6. **Mechanism proof vs architecture adoption frozen**: mechanism proof on failure-type-selected cases;
   adoption must be evaluated on the pre-frozen, unfiltered V1 50 set with trigger frequency, net quality,
   total cost; no failure-type filtering may support adoption.

## 4. A0-BGE baseline replay (Validation V1, 50 cases; context layer)

| Policy | mean CoreCoverage | FULL | evidence tokens total | per case | mean chunks | changed vs A0 |
|---|---:|---:|---:|---:|---:|---:|
| `fixed_top5` (A0) | 0.9372 | 46/50 | 91,699 | 1,834 | 5.0 | 0 |
| `adaptive_prefix_v1` | 0.9665 | 48/50 | 176,934 | 3,539 | 11.1 | 45 |
| `coverage_selector_v2` | 0.9456 | 47/50 | 125,648 | 2,513 | 7.0 | 25 |
| `no_router_adaptive_v1` | 0.9665 | 48/50 | 256,422 | 5,128 | 17.3 | 50 |
| `query_router_v1` | 0.9456 | 47/50 | 143,319 | 2,866 | 8.7 | 27 |

Observations for Stage 1 (diagnostic, not conclusions): at the context layer the router arm is dominated by
`coverage_selector_v2` (same coverage/FULL at fewer tokens), and `no_router_adaptive_v1` is far too
expensive at its frozen parameters; `adaptive_prefix_v1` buys +2 FULL for ~2× tokens. The frozen diagnostic
budget sweeps give reference budgets 3,500 (SIMPLE) / 3,750 (BROAD) for a prefix policy; these are recorded
in the replay artifact and are **not** used by any arm. Note also that availability (candidate union) caps
context FULL below 100%: the union itself misses 4/239 facts.

**A0 reproduction**: selected chunk IDs, evidence tokens, available facts, and utilization baseline IDs all
match stored artifacts with 0 mismatches; context FULL = 46/50 matches the frozen BGE-vs-MiniLM challenger
`fact_complete@5 = 46`; the stored answer-level `grounded_complete = 38` is judge-based and is not the
context metric.

**Provider accounting** (verified against `cache/validation_v1_llm_cache.json`; 0 mismatches):
A0-BGE 50 cases = 110,674 input / 15,982 output tokens (50 calls); utilization baseline 46 cases =
98,824 / 14,299. Rewrite calls in the frozen replay = 0 (noted; production rewrite cost to be added in
Stage 1). Per-call latency is not present in frozen artifacts and must be instrumented live in Stage 1.

## 5. Stage 0 gate checklist

| Gate | Status |
|---|---|
| A0-BGE config explicit | PASS |
| Frozen artifacts replayable (0 mismatches) | PASS |
| Hash / selected context / metrics reproducible | PASS |
| Token accounting reliable | PASS |
| Human adjudication **rules** frozen | PASS |
| Economics contract frozen | PASS |
| Router / arms frozen | PASS |
| Human **verdicts** complete and hashed | PENDING (Stage 1 precondition, not a Stage 0 gate) |

## 6. Stage 1 preconditions (before any Stage 1 answer-level conclusion)

1. Complete the worksheet verdicts, set `status = frozen_human_verdicts`, and record its hash (human work,
   not performed here).
2. Instrument live latency (p50/p95) and rewrite calls into the Stage 1 result artifact.
3. Run Stage 1 only through the frozen arms/router; no parameter changes after the first Stage 1 call.

## 7. Changed files (Stage 0)

- Added: `eval/query_aware_stage0_config.json`, `eval/query_aware_router_v1.json`,
  `eval/query_aware_arms_v1.json`, `eval/human_truth_contract_v1.md`, `eval/economics_contract_v1.md`,
  `eval/run_stage0_replay.py`, `eval/query_aware_stage0_freeze.md`,
  `eval/results/a0_bge_rerank_orders.json`, `eval/results/human_truth_stage0_worksheet.json`,
  `eval/results/stage0_replay_results.json`, `tests/test_eval.py` (Stage 0 test class).
- No production file, no A1/A2/A3 code, no model call, no new evaluator.

**Status: READY FOR A1** (subject to the Stage 1 preconditions above; A1 is not started here).
