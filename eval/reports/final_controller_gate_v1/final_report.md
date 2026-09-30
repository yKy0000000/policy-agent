# Final Report - Final Controller Gate V1

Executed the pre-declared gate sequence against the repository's frozen artifacts. One question was
asked: can a non-oracle runtime sensor, with no gold aspect / target proposition / oracle evidence /
human diagnosis, discover a real query-required gap from `query + actual context + draft` and choose a
bounded action worth executing?

**Result: `STOP`.** Both action branches failed Gate 1; no controller was implemented; production is
unchanged. This is the terminal negative architecture result, produced with 24 new model calls and no
benchmark construction.

---

## A. Artifact audit

Confirmed from frozen artifacts: candidate coverage 235/239 (~98.3%); oracle-complete cases 49/50;
oracle min-K median 1.0; Validation V1 = 50 cases / 239 facts / 208 `QUERY_REQUIRED` aspects; frozen
human truth = 66 cases / 331 aspects / 296 required / 35 optional / 0 ambiguous; residual failure
geometry = GENERATION_MISS 6 + SELECTION_BUDGET 6 + RANKING 2 + REPRESENTATION 2 + FRAGMENTATION 0;
evidence-complete conversion gap is 100% utilization_miss; historical quality point 196/208 and 43/50,
adaptive ceiling 202/208 and 46/50.

Corrected:
1. `VAL-001-039-F02` is `RELEVANT_BUT_OPTIONAL` (both reviewers), **not** a required positive. It is
   therefore an optional-pressure control here, and the preregistered Candidate Discovery V1 (which
   lists it as a natural positive) risks `DESIGN NOT EXECUTABLE` under its own §3 rule.
2. `VAL-001-050-F01` is `QUERY_REQUIRED`. The oracle-repair cohort must not be described as "two
   required failures": one is required, one is optional, and one further case is excluded as
   non-atomic (`VAL-001-008-F02`).
3. Stronger-model oracle repair is 6/6 **semantic** but only 3/6 constraint-compliant; not "6/6".
4. H3 shows the current model executes repairs 6/6 with 0 overrides once a decision is injected, so the
   oracle-repair model gap is decision-formation, not execution. Stronger-model escalation stays out of
   V1.
5. The canonical frozen A1 blind judge (with human resolutions) disagrees with the
   generation-utilization judge on `VAL-001-009-F01` and `VAL-001-022-F02` (A1: COVERED;
   generation-utilization: missing). Both were demoted to secondary, non-denominator cases.

Full detail: `artifact_audit.md`.

## B. Eligibility

From frozen artifacts only, no new questions/labels:

- PATCH natural positives (required fact `NOT_COVERED` in draft, evidence present in context):
  `VAL-001-011-F01`, `VAL-001-050-F01` (**2**).
- REFRESH natural positives (required fact omitted, evidence absent from context, corpus-recoverable):
  `VAL-001-006-F02`, `VAL-001-033-F01..F05`, `VAL-001-046-F03/F04` (**3 cases**).
- Judge-disagreement candidates (secondary): `VAL-001-009-F01`, `VAL-001-022-F02`.
- Complete controls: `VAL-001-029`, `VAL-001-042`, `VAL-001-007`.
- Optional-pressure controls: `VAL-001-026-F02`, `VAL-001-039-F02`.
- Secondary refresh (recorded, not called): `VAL-001-001-F02/F03`.

Both branches reached the minimum of 2 eligible naturals, so the experiment proceeded. Artifacts:
`sample_eligibility.json`, `sample_eligibility.md`. Everything was frozen in `gate_manifest_v1.json`
before any call.

## C. Gate 1 - non-oracle action discovery

24 calls (12 cases x 2 replicates, `deepseek-v4-flash`, temperature 0), 0 failures.

- PATCH: **0/2** confirmed omissions detected; both replicates `RETURN_DRAFT`.
- REFRESH: **0/3** stable discoveries; `VAL-001-033` produced `REFRESH_CONTEXT` once (replicate 1) and
  `RETURN_DRAFT` once (replicate 2).
- Complete controls: 3/3 `RETURN_DRAFT`, 0 harmful false positives.
- Optional pressure: 2/2 `RETURN_DRAFT`, 0 optional-to-required upgrades.

TP/FP: 0 stable TP, 0 harmful FP. Important misses: all 5 primary positives. Stability: the single
positive action was unstable. Sensor action distribution: 23/24 `RETURN_DRAFT`.

**Branch verdict: PATCH FAIL, REFRESH FAIL.** Detail: `gate1_sensor_results.json`,
`gate1_adjudication.json`, `gate1_sensor_summary.md`.

Notable mechanism readout: in `VAL-001-033` (r2), `VAL-001-046`, and `VAL-001-006` the sensor's own
reasons state that the sources are silent/generic about the required obligation, yet it still returned
the draft. The failure is an action/decision-policy failure layered on imperfect perception, matching
the prior H2 finding (task framing moves the decision; the decision is unstable).

## D. Action probes

Not executed. Gate 2A (PATCH) and Gate 2B (REFRESH targeted vs blind) are gated by their Gate 1 branch;
both branches failed, so the conditional authority path is `STOP`. No repair and no retrieval refresh
were run, and no stronger-model diagnostic was triggered.

## E. Economics

- Sensor: 2,775.8 provider tokens/request, p50 latency 0.934 s, p95 1.428 s; estimated
  ~$0.000574/request on the repository's historical blended fixed_top5 rate.
- Reference `fixed_top5`: 2,533.1 tokens/query, $0.00052381/query.
- Executed actions: 0; action cost $0; failed-action cost $0.
- Trigger rate on this cohort: 1/24 calls produced a non-`RETURN_DRAFT` action, 0 stable and correct.

The always-on sensor costs more than the whole current answer pipeline while detecting nothing
confirmed. **The policy is dominated by the simpler baseline.**

## F. Final Decision

`STOP`

(Exactly one value. No `PARTIAL_BUILD`, no `BUILD`. `INCONCLUSIVE` does not apply: the branches did not
partially pass a threshold; they produced zero stable detections while precision stayed clean, which is
a determinate recall failure.)

## G. Implementation

None. No controller was built. No dead branch was kept. The documentation-only rule from the task was
followed: on STOP, go straight to final documentation and do not implement.

## H. E2E

Not run (no implementation).

## I. Production decision

**NO CHANGE.** Production default remains MiniLM + fixed Top5 (Fast) plus Search+; no migration is
performed or proposed by this task. The generation-side coverage-aware prompt already measured by the
project (+2 complete cases at the same evidence) is a separate, non-agentic line of work and is not
part of this architecture decision.

## J. Repository state

New (all under `eval/reports/final_controller_gate_v1/`):
`artifact_audit.md`, `sample_eligibility.json`, `sample_eligibility.md`, `gate_manifest_v1.json`,
`gate1_sensor_results.json`, `gate1_adjudication.json`, `gate1_sensor_summary.md`,
`economics_summary.json`, `economics_summary.md`, `decision.json`, `decision.md`, `final_report.md`.

New runner: `eval/run_final_controller_gate_v1.py`. New cache: `cache/final_controller_gate_v1_cache.json`.

Unmodified: all frozen validation truth, frozen human verdicts, all historical results, `src/` production
code, `src/`/eval tests, and the production Fixed/Fast + Search+ behavior. No existing benchmark was
edited. No test currently covers the new runner; it is a gate-only experiment script.

---

## Required outputs check

- `artifact_audit.md` - yes
- `sample_eligibility.json` / `.md` - yes
- `gate_manifest_v1.json` - yes
- `gate1_sensor_results.json` / `gate1_sensor_summary.md` - yes
- `gate2_patch_results.json` / `gate2_refresh_results.json` - not executed (Gate 1 FAIL; conditional)
- `economics_summary.json` / `.md` - yes
- `decision.json` / `decision.md` - yes
- `implementation_summary.md` / `e2e_*` - not executed (STOP)
- `final_report.md` - this file

## Final project rule

> Current evidence does not justify additional Agent architecture. The remaining failure state is too
> sparse, insufficiently observable without oracle information, and not addressable with a
> cost-effective bounded action.

Policy Agent architecture research ends here. No V3, no new Agent component, no benchmark built to
rescue the controller.
