# Validation V1 canonical benchmark

`benchmark.json` is an immutable-source manifest, not a second copy of the labels. `eval.core.load_benchmark("validation_v1")` verifies each source SHA-256, then combines 50 frozen queries, 239 original rubric facts, 208 Validation V1 `QUERY_REQUIRED` aspects from frozen Human Truth, and the source-support chunk IDs in the frozen geometry artifact. Case IDs, query strings, fact IDs, supporting excerpts, and reviewer verdicts remain in their original files.

The original 239 facts determine candidate/ranking diagnostics. Only the 208 QUERY_REQUIRED aspects determine context and answer completeness. No loader path constructs new Human Truth or changes a verdict. A source hash mismatch fails loading rather than silently accepting drift.
