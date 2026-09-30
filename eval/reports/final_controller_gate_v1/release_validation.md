# Final Controller Gate V1 — Release Validation

Validation date: **2026-09-30** (Asia/Shanghai). This is a release record, not a new experiment or
regenerated gate result. Terminal architecture decision remains **STOP**.

## Scope and identity

- Included the 12 original final-gate artifacts and original `eval/run_final_controller_gate_v1.py`.
  Their exact bytes are identified by `archive_checksums.json`; no sensor, prompt, result, sample,
  threshold, frozen truth or production source was edited.
- Updated the existing Chinese README narrative, evaluation navigation, reader-facing architecture
  decision, research summary and reproducibility manifest. Original A1/A2/H1/H2/H3 results stay intact.
- Added eight offline archive regression checks. They consume recorded cells instead of local cache
  or a provider, reconstruct input identities, check non-oracle message assembly, preserve secondary
  judge disagreements, validate usage/empirical quantiles and assert terminal no-action status.
- Added `.gitattributes` protection against newline conversion for the final archive.

## Completed checks

- Targeted archive suite: **8 tests passed**.
- Full repository suite: **333 tests passed**, 56.495 seconds. `socket.connect`, `connect_ex` and
  `create_connection` were blocked; Hugging Face/Transformers offline mode was enabled. Tests that
  print API counters use mocked clients, not external calls.
- Python compilation: `compileall -q src eval tests` passed.
- Dependency consistency: `pip check` passed, no broken requirements.
- Frozen/source identity comparison: **236 pre-release files unchanged**, including all tracked
  production sources, frozen truth/results/benchmark/provenance inputs and the original gate package.
- Recorded usage was checked against all 24 cells: input 64,454, output 2,165, total 66,619 tokens.
  The original p50/p95 convention and price-estimate basis are documented without rewriting results.
- Credential-pattern scan of the release source/docs/archive found no credential-like tokens.

Markdown links, staged whitespace, tracked runtime-artifact exclusions and exact staged archive bytes
are checked before commit. Git remote synchronization and clean working tree are checked after push.
No new model calls, benchmark, action probes, E2E, controller implementation or production migration
were performed during release validation.

## Cleanup and publication boundary

The gate runtime cache and generated source/test bytecode are local, disposable artifacts; they are
excluded from the release. Credentials, existing model/index caches and the separately fetched upstream
corpus remain local and ignored. Raw sensor output and provider usage remain available in the tracked
archive, so its integrity tests do not require the removed gate runtime cache.

Known original-report discrepancies (planned 26 versus executed 24, representative target lists,
H1 summary accuracy, historical-cost scope and unsupported tuning generalizations) are explicitly
preserved and clarified in `README.md`; they do not change the gate outcome.
