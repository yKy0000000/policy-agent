# Stage 1 human-truth preregistration supplement v1

**State:** human-truth verdicts frozen; A1 generation not started.

## Frozen truth and provenance

- Final artifact: `eval/results/frozen_human_verdicts_v1.json`
- Final artifact SHA-256: `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716`
- Original Stage 0 worksheet SHA-256: `86926d6290a60f5a9b9b1ad2ffa638a6206e028bfa0d97a8581f7aa632f3244b`
- Human truth contract SHA-256: `1b131832cbca8d3529473d65dbb3c48ea80957c88aead225f147ff6870aa6d74`
- Frozen Stage 0 config SHA-256: `744ed411e301aaf28a3751be99c31157b26dcbcf524673f749aa711d2a82e3a6`
- Frozen router SHA-256: `dcc7d4953f3ba9794c35f2168e29f419bbb40eb014775cf8ccb5e0e7ae913bd7`
- Frozen arms SHA-256: `18d7adbfd1ac8a1802dbf29d2c222fb988d0c495ca4f979c24297a406f0112c9`

The final artifact retains the source hashes for both independent model-agent reviews and their disagreement packet. It records the user's explicit final decision and an omission-test resolution reason for each of the 17 disagreements. The 314 initial agreements use their shared candidate verdict. Totals: 331 aspects, 296 `QUERY_REQUIRED`, 35 `RELEVANT_BUT_OPTIONAL`, 0 `AMBIGUOUS`; initial agreement 314/331 (94.864%), and 17/17 disagreements resolved. The eight SIMPLE sentinel case IDs and 41 sentinel aspect rows remain intact.

The original worksheet is unchanged at `pending_human_verdicts`; the new artifact has `status = frozen_human_verdicts` and all `final` fields populated. Any correction after A1 outputs are visible requires a new truth version and a rerun under the contract.

## Pre-generation context rescore

`eval/results/human_aware_context_v1.json` reuses the selected chunk IDs for the exact five frozen arms from `stage0_replay_results.json`. The 50 Validation V1 cases have selected contexts; the 16 Broad Query V3 cases have truth labels but no five-arm selected-context replay and are excluded from this rescore. The result contains all ten paired arm comparisons and defines aggregate context-level dominance. This diagnostic does not decide architecture adoption or answer-level quality.

## Verification and next gate

- 43 unique frozen Stage 0 source/artifact hashes matched their recorded values.
- All five legacy context metrics were reproduced from the frozen selected contexts before applying the query-required truth filter.
- Offline test suite: `python -m unittest discover -s tests -q` using the project virtual environment; 184 tests passed. Tests use their own mocks and fixtures; this preflight made no live LLM API call.
- The human-truth freeze gate is complete. The project has no A1 generation runner yet, and the Stage 0 preconditions call for live latency and rewrite-call instrumentation. Those execution preparations remain before actual A1 generation. A1/A2/A3 generation was not started here.
