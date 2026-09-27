# Research snapshot v1 — pre-refactor canonical state

This records the completed research state immediately before the reusable evaluation-framework refactor. The snapshot was committed locally and tagged; no remote push was made.

Current location: `eval/reports/research_v1/research_snapshot_v1.md`. Paths in the checksum table describe the tagged historical tree; the reader-facing files were subsequently moved from `eval/final/` to `eval/reports/research_v1/` without changing the preserved tag.

- Branch at snapshot: `main`
- Commit: `0c3afef3e46d64dda6dd2bd73183a72c86c68358`
- Annotated tag: `research-complete-v1`
- Working tree after snapshot commit/tag: clean
- Restore command: `git checkout research-complete-v1` (detached) or create a branch from this tag.

| Canonical artifact | SHA-256 |
|---|---|
| `eval/validation/broad_queries_validation_v1.json` | `1fb2b03d752343ea19d83283dff92d066febe357178cb93a5cf7c603c1fe4858` |
| `eval/validation/broad_atomic_facts_validation_v1.json` | `451a583f5ce88e0b573e61e5af073e34748b35900fa3ecd3d3f00b001699df50` |
| `eval/results/frozen_human_verdicts_v1.json` | `85199cfa9c0fa486eb467aa04dda108cd121ce775bbf748d053d261e6b42c716` |
| `eval/results/a1_blind_answer_quality_frozen_v1.json` | `96bf5fa61611b31747ca26e5b298d8b96e2b38805bd3d9c4ae2062107c256c35` |
| `eval/results/a1_final_decision_v1.md` | `f3481095ed5045c8fe9f27d17485c4ebfceb638812d72b18b3de1c13f3e1c607` |
| `eval/results/a2_minimal_mechanism_probe_v1.json` | `ceba0ffa54a6e4f6039ebf2cac82284a42349ef8a9a61942c91be70f93c08cde` |
| `eval/final/architecture_decision.md` | `5bbb9202121284bd6201c7b010b7821456fc89302dd6053c3517fa948be74840` |

Benchmark identity: Validation V1 has 50 cases and 239 original rubric facts. Frozen Human Truth marks 208 of those Validation V1 aspects QUERY_REQUIRED. The original fact diagnostic, context coverage, and answer quality use different semantic scopes and must remain separate.

The A1 router verdict is **KILL**; A2 is **mechanism confirmed but not adopted**; A3 was **not triggered**. The repository default at this snapshot is MiniLM + fixed Top5, while the research recommendation is BGE + fixed Top5. Historical runners, results, and archive are preserved by the tag. Subsequent framework files are additive and are not part of this pre-refactor snapshot.
