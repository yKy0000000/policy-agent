# MiniLM vs BGE runtime decision v1 — frozen contract

Status: frozen before the new runtime measurement and paired 208-aspect analysis. This is a deployment decision on the exposed Validation V1 **development / research benchmark**, not fresh external confirmation.

## Fixed pipeline and variable

Only the cross-encoder changes: `cross-encoder/ms-marco-MiniLM-L-6-v2` versus `BAAI/bge-reranker-base`. Both use the same local policy and semantic index snapshots, no-history rewrite (identity), lexical Top20, semantic Top20, chunk-ID union, fixed Top5, the existing grounded generation prompt, `deepseek-v4-flash` when live generation is available, and deterministic citation validation. No router, selector, decomposition, threshold, prompt, or TopK tuning is allowed. CPU, batch size 16, model cache `cache/huggingface`.

## Samples and measurements

Quality uses all 50 frozen Validation V1 queries. The directly paired answer comparison reuses the already-generated MiniLM/BGE answers and *the same earlier reranker-transfer judge protocol* in `eval/results/reranker_transfer_results.json`, filtering both arms to the 208 frozen `QUERY_REQUIRED` IDs. This is a comparable paired re-analysis of historical outputs, not the later A1 blind protocol and not new generation. Report aspect coverage, complete cases, case-level wins/ties/losses, gained/lost aspect IDs, and grounding diagnostics. Candidate and context support are evaluated separately and must not be treated as answer accuracy.

Steady-state runtime latency uses the same deterministic 20-case subset: IDs `VAL-001-001`, `-003`, ..., `-039` (every odd ID from 1 through 39). Load each model once and measure its load time separately. Warm up each reranker once before timed queries. Use real local lexical/semantic retrieval, candidate union, cross-encoder scoring and fixed Top5. Record rerank mean/p50/p95 and sample count; the complete request also records rewrite, retrieval, rerank, generation, validation and total latency. Local caches for rewrite and generation are disabled. If the configured generation endpoint cannot be used, report end-to-end and generation latency N/A rather than combining frozen answer replay with live timings. Record model/device/batch/thread configuration and process RSS where available. Model load time is excluded from warm request latency. The arm order is MiniLM then BGE; the possible time-order effect is a limitation.

## Decision rule

Promotion requires all of: at least two net additional QUERY_REQUIRED-complete cases in paired historical quality, no more than one complete-case regression, no increase in contradicted claims, warm rerank p95 no more than 2.0 times MiniLM, and—if live end-to-end latency is obtainable—end-to-end p95 no more than 1.25 times MiniLM. Missing comparable end-to-end latency blocks promotion. If BGE has the quality gain but fails the deployment latency gate, keep MiniLM as runtime default and retain BGE as a quality-oriented option. If the paired quality gate fails, keep MiniLM. These gates are application decision thresholds for this experiment, not universal performance standards.

No runtime default is changed before analyzing the measurements. Frozen historical artifacts and their hashes are not rewritten.

## Execution deviation log (appended after the contract freeze)

Inspection during measurement showed that the executable Agent calls the contextual rewrite model even when history is empty. The contract's "no-history rewrite (identity)" assumption is false for fresh end-to-end calls. The local retrieval/rerank timing uses the original query and remains a strict reranker-only comparison. Fresh end-to-end calls use the same rewrite prompt/model but make independent rewrite requests per arm; their p50/p95 values are descriptive runtime observations, **not an isolated causal reranker latency delta**. The original decision gates above have not been changed. Historical paired answer quality likewise remains tied to its frozen original-query protocol, not to newly rewritten live answers.
