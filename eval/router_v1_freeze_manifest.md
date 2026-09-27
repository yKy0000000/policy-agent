# Router V1 Freeze Manifest

> Router V1 experimental specification was frozen before observation of any Router V1 benchmark outcome.

- manifest_version: `router_v1_freeze_manifest`
- status: `frozen_before_router_v1_outputs`
- frozen_at_utc: `2026-09-27T14:25:39Z`
- outcome_blind_at_freeze: `true`
- router_implementation_commit: `PENDING_IMPLEMENTATION_FREEZE`
- baseline_preimplementation_head: `1350b54147e8cf17f3235dbe3988d17de370fef1`

## Core frozen artifacts

| path | role | SHA-256 | status |
|---|---|---|---|
| `eval/router_benchmark_v1.json` | frozen_benchmark | `a345ccfd8dabadedd41ac1abc341a079709d3bbc699e4ea7b3696a06f76acf16` | frozen |
| `eval/router_v1_architecture_frozen.md` | frozen_routing_architecture | `fc6ad624d800d1ea946555e3694725361f90bb0d347f3d07979f4770cbbf575b` | frozen |
| `eval/router_v1_contract.json` | frozen_router_decomposer_contract | `fb5484351eae3fcc285ab9ce8e819c33e3367ceea972ffdbca43cde7d18d9549` | frozen |
| `eval/router_v1_preregistration.json` | frozen_pre_registration | `79499cd5a9959c8f4e390fa2d058cf1a70716d6fdd3b35bdb1ef69092bf34123` | frozen |
| `eval/router_v1_required_aspects.json` | frozen_required_aspects_truth | `d22a5a919cd5828258491adeea0af3f7d5d8983a27f1226dc3e0fa71801b9b76` | frozen |
| `eval/router_v1_required_aspects.md` | frozen_required_aspects_truth_human_readable | `8853b5dee8132febe8a10db2abd01f22989b56260668ba908c555baa26202538` | frozen |

## Corpus

- document_count: `57`
- commit: `b9578b546d2506febda1da2cd7431644d58e512c`
- content_manifest_sha256: `7cb3d94d1bc9dde72aac75e807326f157e588f168d61ed1fdd2d817ffd06b06d`
- lexical index: `cache/policy_index.json` (`dc73a4725ff7361ebd0c28d5b9bef93a433ae6f2b6cd9a65723676e666e6ee82`)
- semantic index: `cache/semantic_index.json` (`672f4231d914272da061524e34b845e0d60711ccb335be531cf0df117f2580a1`)

## Experiment identity

- rewrite: `contextual-query-rewrite-v1` / prompt_source_sha256 `72aac5dcf3d72e02f11441f738bc3b47342390473d83061de3c97a7c2c494254`
- router model: `deepseek-v4-flash` (api.deepseek.com), prompt `104b46283ffe2e504ff5dcd43ecce63107fc780461e2e5e7ff1e48e20a4da74b`, schema `651646d655ae5b963815cd168c5a9f023cf2d2d8ad9bddbdeda248e78e309d9b`
- decomposer model: `deepseek-v4-flash` (api.deepseek.com), prompt `6e866974a5a1861da766417b6f5715c7e0b1009b23fbecc66c15a2540946f489`, schema `98d15a9221c38d2a65fd7cef07219e308ff40a49889953395bd2b304917190d4`
- retrieval: lexical Top20 + semantic Top20 per stream; reranker `cross-encoder/ms-marco-MiniLM-L-6-v2`; stream Top5
- merge: `round_robin_highest_ranked_unselected_chunk_per_stream`, total evidence `5`
- generation: `grounded-policy-answer-v1`, citation validation `src/generator.py:validate_citations`
- oracle rule: `eval/router_v1_architecture_frozen.md#l-oracle-comparison-rule`

## Truth statistics

- query count: `20`
- required aspects: `66` (min 2 / median 3.0 / mean 3.3 / max 4)
- optionalized aspects: `4`
- combined support aspects: `4`
- corpus gaps: `0`
- single-document mean: `2.9091`; multi-document mean: `3.7778`
- Pearson r (aspect count vs author multi_document): `0.776194`

## Preregistration binding

- preregistration: `eval/router_v1_preregistration.json` (`79499cd5a9959c8f4e390fa2d058cf1a70716d6fdd3b35bdb1ef69092bf34123`)
- final truth: `eval/router_v1_required_aspects.json` (`d22a5a919cd5828258491adeea0af3f7d5d8983a27f1226dc3e0fa71801b9b76`)
- human-readable truth: `eval/router_v1_required_aspects.md` (`8853b5dee8132febe8a10db2abd01f22989b56260668ba908c555baa26202538`)
- note: frozen preregistration was not rewritten; binding recorded here only.

## Provenance (research trail; not runtime inputs)

| path | role | SHA-256 |
|---|---|---|
| `eval/router_benchmark_v1_draft.json` | benchmark_generation_draft | `2638f308d70b9c6a85d9381cb81aef2bbe593de89528f5b7c4c3976e46514b78` |
| `eval/router_benchmark_v1_deepseek_audit.md` | benchmark_independent_audit | `6b688b68f8408ef00e1a90e6977f90d41ccae8696b0a92c46aa0f42bcefb904a` |
| `eval/router_benchmark_v1_freeze_gate.md` | benchmark_freeze_gate_record | `a2fdb89673159ea5d79b20691af058e381d210a81264034c10071bce66d78c04` |
| `eval/router_v1_required_aspects_draft.json` | required_aspects_generation_draft | `c2f766b0610c37b899990d0eb8d6bbb229aa25add3a7f2a041f66686af07f547` |
| `eval/router_v1_required_aspects_draft.md` | required_aspects_generation_draft_human_readable | `3495e0e143a26e9c38d45e343d028541eb32a605decf4561b36fb6ab42326d80` |
| `eval/router_v1_required_aspects_deepseek_audit.md` | required_aspects_independent_audit | `b815ed0a4a7f8de4c5aa4e3f093032ca9fc827337cb2fa14bd729de9af81ce1f` |
| `eval/router_v1_required_aspects_audit_changes.json` | required_aspects_audit_change_set | `9c4f373ed9dcc030d39d7fffa099dc15afe3008a046a8d5fa67ff2163e0c2792` |

## Post-freeze modification policy

Any modification after this freeze point to: benchmark, required truth, Router semantics, Router prompt, Router schema, Router model, Decomposer prompt, Decomposer schema, Decomposer model, rewrite behavior, retrieval Top-K, reranker, merge rules, evidence budget, fallback rules, oracle comparison rule — constitutes **Router V2** or a separate new experiment version and cannot count as Router V1.
