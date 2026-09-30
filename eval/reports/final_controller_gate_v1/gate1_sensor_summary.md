# Gate 1 - Non-Oracle Action Discovery Summary

Status: COMPLETE. Sensor = `deepseek-v4-flash`, temperature 0, `max_tokens` 700, 2 replicates,
24 calls (12 cases), **0 transport/parse failures**. No prompt, threshold or sample change was made
after the first call. The run was on the frozen BGE research-stack context + draft; production remains
MiniLM/fixed Top5 and no quality baseline is drawn here.

## Frozen sample

| role | cases |
|---|---|
| patch_positive | VAL-001-011, VAL-001-050 |
| patch_judge_disagreement (secondary) | VAL-001-009, VAL-001-022 |
| refresh_positive | VAL-001-006, VAL-001-033, VAL-001-046 |
| complete_control | VAL-001-029, VAL-001-042, VAL-001-007 |
| optional_pressure | VAL-001-026, VAL-001-039 |

## Result

| branch | primary positives | stable hits | partial/unstable | verdict |
|---|---:|---:|---:|---|
| PATCH_CONTEXT | 2 | 0 | 0 | **FAIL** |
| REFRESH_CONTEXT | 3 | 0 | 1 | **FAIL** |
| complete controls (harmful FP) | 3 | 0 FP | 0 | CLEAN |
| optional pressure (optional->required) | 2 | 0 | 0 | CLEAN |

- Sensor action distribution: 23/24 `RETURN_DRAFT`, 1/24 `REFRESH_CONTEXT`.
- PATCH: both confirmed required omissions (`011-F01`, `050-F01`) received `RETURN_DRAFT` in both
  replicates. The sensor's own reasons asserted the drafts already covered the obligations.
- REFRESH: `006-F02` and `046-F03/F04` were not detected; `033` produced one correct-class
  `REFRESH_CONTEXT` (replicate 1) with a target matching the omitted maintainer moderation options and
  a valid refresh query, then `RETURN_DRAFT` (replicate 2). No stable discovery.

## Key observation (action policy, not only detection)

In several refresh cases the sensor's own reasoning **recognized** the acquisition gap but still chose
`RETURN_DRAFT`:

- `VAL-001-033` r2: "the sources only reference 'moderation tools' generically".
- `VAL-001-046` both: "the sources do not enumerate [the delay exceptions]".
- `VAL-001-006`: draft summary omits the specific identification requirement.

So the failure is not purely a perception failure: when the sensor sees that evidence is absent, it
still declines to escalate. This reproduces the H2 finding (the action decision is framing/policy
dependent and unstable) in a new, deployable, non-oracle setting. It cannot be fixed by tuning the
sample or the threshold; it is the sensor's decision policy.

## Interpretation

- Precision side is clean: no harmful action on complete controls, no optional->required upgrade.
- Recall side is empty: the sensor discovered **0** of the confirmed required omissions (2 PATCH + 3
  REFRESH), and its single positive action was not replicate-stable.
- Per the frozen Gate 1 rule (">=2 distinct natural positives reachable and stable"), both branches
  FAIL. Per the decision matrix, `PATCH FAIL + REFRESH FAIL -> STOP`.

No sensor-prompt retune, no replacement sample, no second round was attempted.
