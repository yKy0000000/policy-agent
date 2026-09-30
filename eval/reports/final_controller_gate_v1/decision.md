# Final Decision - Final Controller Gate V1

## Decision: `STOP`

| gate | result |
|---|---|
| PATCH_CONTEXT action discovery | **FAIL** - 0/2 confirmed required omissions detected, both replicates `RETURN_DRAFT` |
| REFRESH_CONTEXT action discovery | **FAIL** - 0/3 stable discoveries; 1 unstable `REFRESH_CONTEXT` (replicate 1 only) |
| Complete controls | CLEAN - 0 harmful actionable false positives |
| Optional pressure | CLEAN - 0 optional-to-required upgrades |
| Economics | **DOMINATED** - sensor ~2,775.8 tokens/request vs fixed_top5 2,533.1 tokens/query, for 0 confirmed detections |

Decision-matrix path: `PATCH FAIL + REFRESH FAIL -> STOP`.

## What was and was not done

- Implemented: nothing. No controller, no repair/refresh action, no production change.
- Not done (forbidden): no sensor-prompt retune, no sample replacement, no threshold change, no second
  round, no verifier/planner/multi-agent, no new benchmark.

## Reason (frozen evidence)

1. A non-oracle sensor, given only query + actual context + draft, did not discover a single confirmed
   query-required gap. The two PATCH positives are human/canonical-judge-confirmed omissions; both were
   returned as `RETURN_DRAFT`.
2. The one actionable output (`VAL-001-033`, replicate 1) did not survive replicate 2.
3. Precision was clean, so this is a recall/policy failure, not an over-triggering problem.
4. In several cases the sensor recognized that the sources were silent on a required obligation and
   still chose not to refresh. This reproduces the H2 decision-instability finding in a deployable,
   non-oracle setting.
5. The sensor is economically dominated even before any action cost.

See `gate1_sensor_summary.md`, `gate1_adjudication.json`, `economics_summary.md`, `final_report.md`.
