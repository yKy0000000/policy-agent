# Router V1 Implementation Freeze

**Status:** tests complete; implementation frozen pending commit; frozen benchmark not executed.

- implementation version: `router_v1_implementation`
- implementation timestamp (UTC): `2026-09-27T14:35:02Z`
- source git HEAD before implementation: `1350b54147e8cf17f3235dbe3988d17de370fef1`
- current git HEAD at freeze artifacts creation: `1350b54147e8cf17f3235dbe3988d17de370fef1`
- implementation source commit: `PENDING_COMMIT`
- implementation manifest: `eval/router_v1_implementation_manifest.json`
- implementation manifest SHA-256 (pre-commit working tree): `3506f5d13adf75974ac1fa44b3c982f14e1bdb64fb39197648ffd71e326e2ed7`

## Implementation files

| path | role | SHA-256 |
|---|---|---|
| `src/router_v1_prompts.py` | frozen prompt/schema constants (generated from contract) | `703d5c00add2649809922eaf77fb22f29f5cb7e76372f63af6c2166051265e48` |
| `src/router_v1_identity.py` | runtime identity verification and canonical hashing | `1e1929415b2656496cbee8634858684252d8e2ce9456e99956eba385e81a9913` |
| `src/router_v1.py` | Router stage (one call, decision-only contract) | `0d28a9409e974ba60d9e65f6bb85bfa9e416ef8933c70637404186eb5fbf50b5` |
| `src/decomposer_v1.py` | Decomposer stage (one call, deterministic subquery validation) | `159294cc8bd16413001839e8689df11e32c2afa8be05aa114b260aba2c1d9bf3` |
| `src/router_v1_trace.py` | typed trace/result structures | `269230ed81c6891c2838f3d266f7820126beb86fad2d7eb93be9d8073a72c945` |
| `src/router_v1_pipeline.py` | multi-stream retrieval, merge, attribution, arm execution | `67f965ed76d6fa913555274f5ec7446524412ff39d0044a0d60e5fad876f7fec` |
| `eval/run_router_v1.py` | experiment runner CLI with frozen-benchmark blindness guard | `e57149874e0f462bdd077915056ff1cbc0d0230b3c6994c9036f266acb1084b2` |
| `tests/test_router_v1.py` | Router parsing, Decomposer validation, identity, runner guard tests | `aec9af35b4c62f6399eeaddbd6c7f56e56df4563a0bc5a45a2531a377df52b26` |
| `tests/test_router_v1_pipeline.py` | merge, attribution, stream, arms, failure and integration tests | `772798843d46c8116ea079df54d717c6b08fc08d5e95d7f92d91166c3176d15e` |

## Architecture mapping

- shared contextual rewrite: existing `src/conversation.py:rewrite_or_keep` (unchanged source hash `72aac5dcf3d72e02f11441f738bc3b47342390473d83061de3c97a7c2c494254`).
- Router: `src/router_v1.py`, contract prompt/schema hash-verified; `decision` is the only execution field.
- Decomposer: `src/decomposer_v1.py`, called only on a legal DECOMPOSE decision; frozen normalization and dedup order.
- retrieval: existing `src/reranked_retriever.py:RerankedPolicyRetriever.search` is called once per stream (lexical Top20 + semantic Top20 union -> frozen MiniLM rerank -> stream Top5).
- merge: frozen round-robin in `src/router_v1_pipeline.py:merge_streams`; five unique chunks maximum.
- attribution: `classify_attribution` records representation gain, selection-ranking gain, and zero evidence gain.
- generation and citation validation: existing `src/generator.py` functions, unchanged.

## Tests

- command: `.\.venv\Scripts\python.exe -m unittest discover -s tests`
- new Router V1 tests: `52`
- existing tests: `266`
- total: `318`; failures: `0`; errors: `0`
- environment issues: none, no real model/API calls required by tests (all Router/Decomposer tests use mocks).

## Frozen artifact integrity

- benchmark: `match`
- architecture: `match`
- contract: `match`
- preregistration: `match`
- required_aspects_truth: `match`
- experiment_freeze_manifest: `not-listed`

## Runtime prompt/schema hash integrity

- router prompt: `104b46283ffe2e504ff5dcd43ecce63107fc780461e2e5e7ff1e48e20a4da74b`
- router schema: `651646d655ae5b963815cd168c5a9f023cf2d2d8ad9bddbdeda248e78e309d9b`
- decomposer prompt: `6e866974a5a1861da766417b6f5715c7e0b1009b23fbecc66c15a2540946f489`
- decomposer schema: `98d15a9221c38d2a65fd7cef07219e308ff40a49889953395bd2b304917190d4`
- verified at test time by `tests/test_router_v1.py:IdentityTests`; mismatch fails fast via `src/router_v1_identity.py`.

## Blindness

- frozen benchmark executed: `false`
- Router V1 outcomes generated: `false`
- real benchmark judge run: `false`
- the runner refuses to load `eval/router_benchmark_v1.json` without `--allow-frozen-benchmark`, which was never passed.

## Two-layer implementation identity

The implementation commit cannot contain its own hash. Identity is therefore recorded in two layers:

1. **implementation source commit** - the git commit containing the implementation files.
2. **post-commit manifest working-tree SHA-256** - the hash of `eval/router_v1_implementation_manifest.json` after the commit updates `implementation_source_commit` in the working tree.

## Post-commit identity

- implementation source commit: `PENDING`
- post-commit manifest working-tree SHA-256: `PENDING`

