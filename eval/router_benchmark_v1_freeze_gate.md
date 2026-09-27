# Router Benchmark V1 — Freeze Gate

**Verdict: PASS_WITH_NOTE.** This is a deterministic surface-feature audit of the 20 unchanged queries, not a retrieval or Router evaluation. The observed sentence-pattern bias is recorded below; substantial overlap remains between the auditor's source-layout groups. The benchmark may be frozen with this limitation.

## 1. Applied audit changes

Source: `eval/router_benchmark_v1_audit_changes.json` (DeepSeek independent audit). Its dispositions are **17 KEEP / 3 RECLASSIFY / 0 EDIT / 0 REMOVE**. Only these three approved case-metadata changes were applied to the freeze candidate:

| id | `benchmark_property` change | `likely_evidence_structure` change |
|---|---|---|
| `router_002` | `multi_document, representation_mismatch, multi_requirement` → `direct_control, rule_exception, hard_looking_control, representation_mismatch, multi_requirement` | `multi_document` → `localized` |
| `router_009` | `multi_document, rule_exception, rule_process, fragmented_evidence, multi_requirement` → `direct_control, rule_exception, rule_process, fragmented_evidence, hard_looking_control, multi_requirement` | `multi_document` → `multi_section` |
| `router_016` | add `broad_coherent_control` between `fragmented_evidence` and `multi_requirement` | unchanged: `multi_section` |

All other case fields, including the original author's explanatory notes, were retained verbatim. Consequently, the inherited `why_it_is_useful` for `router_002` and `router_009`, and collection-level counts in the copied review Markdown, still reflect the draft author's original interpretation. The corrected structural comparison in this gate follows the auditor's approved reclassifications. No additional wording or evidence-outcome judgment was inserted into the candidate.

## 2. Query integrity check

- Draft JSON and Markdown SHA-256 still match the hashes recorded before the independent audit: `2638f308d70b9c6a85d9381cb81aef2bbe593de89528f5b7c4c3976e46514b78` and `fd213c5a89fd6a56b9744f72378b06ad1b7e0b7f3a2197f2df9a6a89a9dc4087`.
- The DeepSeek audit Markdown SHA-256 is `6b688b68f8408ef00e1a90e6977f90d41ccae8696b0a92c46aa0f42bcefb904a`; its change file SHA-256 is `70bc0970b91e787088b1a7673c4fb4bbc11ad7483924799f3669debead859887`. Both remained unchanged during this gate.
- Candidate JSON and Markdown contain exactly `router_001` through `router_020`. Candidate query strings match draft JSON and draft Markdown **20/20, character for character**. No extra or backup query exists.
- Candidate-to-draft case-field differences are confined to the two approved metadata fields for the three IDs above. Candidate top-level lifecycle fields identify version `router_benchmark_v1` and status `freeze_candidate`.
- No routing gold, route decision, oracle label, or expected winner is stored in the benchmark. No LLM, retrieval, decomposition, or Router was run.

## 3. Surface feature table

The reproducible rules and measurements are in `eval/analyze_router_benchmark_surface_features.py`. `length_chars` counts Unicode code points, including spaces and punctuation. `token_or_word_count` uses `[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*`; apostrophe and hyphen words count once. `clause_marker_count` counts case-insensitive whole-word `and`, `also`, `but`, `while`, `or`, `then` occurrences. `question_structure_count` counts `?` plus an explicit `and/or` followed by an interrogative or auxiliary word; it is a syntax proxy, not a semantic count of user needs. `literal topic cues` counts distinct matches in a fixed, conservative named-term lexicon in the script. It is **not** an inferred number of policy documents or semantic topics.

The structural-pattern rule has fixed priority: `but|while|without` → contrastive; else `if|when|unless` → conditional; else an extra question structure or `and|also|or|then` → coordinated; otherwise single. This label describes wording only.

`G1` is the auditor's five likely-localized plus six likely-multi-section single-document queries; `G2` is the auditor's nine likely-multi-document queries. These are **source-layout groups for this audit**, not routing targets. Fragmented evidence and multiple requirements can occur in either group.

| id | group | length_chars | token_or_word_count | clause_marker_count | question_structure_count | literal topic cues | structural pattern |
|---|---|---:|---:|---:|---:|---:|---|
| router_001 | G2 | 229 | 41 | 2 | 2 | 2 | coordinated |
| router_002 | G1 | 207 | 33 | 1 | 1 | 0 | contrastive |
| router_003 | G2 | 211 | 32 | 2 | 2 | 0 | coordinated |
| router_004 | G1 | 214 | 34 | 2 | 1 | 0 | contrastive |
| router_005 | G1 | 228 | 37 | 2 | 1 | 1 | contrastive |
| router_006 | G2 | 233 | 38 | 2 | 2 | 2 | contrastive |
| router_007 | G2 | 181 | 32 | 2 | 2 | 0 | coordinated |
| router_008 | G1 | 196 | 25 | 1 | 1 | 1 | contrastive |
| router_009 | G1 | 222 | 37 | 2 | 2 | 2 | coordinated |
| router_010 | G1 | 186 | 33 | 2 | 2 | 1 | coordinated |
| router_011 | G2 | 196 | 29 | 2 | 2 | 1 | coordinated |
| router_012 | G1 | 190 | 29 | 1 | 2 | 1 | coordinated |
| router_013 | G2 | 200 | 33 | 3 | 2 | 1 | coordinated |
| router_014 | G1 | 190 | 30 | 1 | 2 | 0 | contrastive |
| router_015 | G1 | 207 | 39 | 3 | 2 | 1 | contrastive |
| router_016 | G1 | 187 | 31 | 1 | 2 | 1 | coordinated |
| router_017 | G2 | 202 | 35 | 2 | 1 | 1 | coordinated |
| router_018 | G2 | 181 | 34 | 2 | 2 | 1 | contrastive |
| router_019 | G1 | 214 | 37 | 3 | 2 | 1 | contrastive |
| router_020 | G2 | 228 | 37 | 3 | 3 | 2 | coordinated |

## 4. Distribution comparison

| feature | G1: 11 single-document queries | G2: 9 multi-document queries |
|---|---|---|
| Characters | 186–228; median 207; mean 203.7 | 181–233; median 202; mean 206.8 |
| Words | 25–39; median 33; mean 33.2 | 29–41; median 34; mean 34.6 |
| Clause markers | 1–3; median 2; mean 1.7 | 2–3; median 2; mean 2.2 |
| Question structures | 1–2; median 2; mean 1.6 | 1–3; median 2; mean 2.0 |
| Literal topic cues | 0–2; median 1; mean 0.8 | 0–2; median 1; mean 1.1 |

The length ranges overlap almost completely. For example, single-document `router_015` has 39 words, while multi-document `router_011` has 29. All nine G2 queries have at least two clause markers, but so do six of eleven G1 queries. Seven G1 and two G2 queries have the lexically contrastive pattern. Seven G2 and four G1 queries have the coordinated pattern. Both groups contain single-document or cross-document questions with multiple explicit asks; the auditor also notes that all 20 have at least two effective sub-asks, while only 16 carry the author's `multi_requirement` tag.

## 5. Shallow heuristic checks

The following are illustrative fixed checks, **not fitted thresholds or trained classifiers**. A hit means only that the query has the stated surface form.

| check | G1 hits / 11 | G2 hits / 9 | implication |
|---|---:|---:|---|
| Words ≥ 35 | 4 | 4 | Length does not separate groups. |
| Characters ≥ 200 | 6 | 6 | Same conclusion using character length. |
| Clause markers ≥ 2 | 6 | 9 | Bias toward G2, with many G1 matches. |
| Contains `and` or `also` | 10 | 9 | Nearly universal; non-discriminative. |
| Question structures ≥ 2 | 7 | 8 | Near-uniform overlap. |
| Literal named-topic cues ≥ 2 | 1 | 3 | Weak, low-recall cue; `router_009` is the G1 counterexample. |

The strongest obvious **two-cue** illustration is “at least two clause markers and lexically coordinated”: 7/9 G2 queries and 2/11 G1 queries satisfy it. If one mechanically mapped that pattern to G2 and everything else to G1, it would agree with these *source-layout groups* on 16/20. It would misgroup single-document `router_009` and `router_010`, and multi-document `router_006` and `router_018`. This observed combination was inspected after seeing the distributions; it is **not** a preregistered classifier score and says nothing about which retrieval path wins.

For the “multiple named policy topics” concern, the exact-term proxy fires in `router_001`, `006`, `009`, and `020`; it does not find most multi-document cases and incorrectly treats the single-document `009` as multi-topic. Implicit topics cannot be reliably counted by a literal regex without semantic interpretation, so the report does not claim a complete `explicit_entity_or_topic_count`. This proxy cannot rule out a more semantic topic-count shortcut, but it shows no simple literal-name separation.

## 6. DeepSeek high-risk claim verification

The claim that “complex-looking → decompose” might *appear* strong is **partly supported as a dataset-surface concern**, not verified as a routing result. Clause count and coordinated-versus-contrastive wording correlate with the auditor's source-layout groups. The simple two-cue illustration above agrees on 16/20 structural assignments. However, word and character length overlap heavily; `and/also` and multiple explicit question structures occur in both groups; and the two-cue illustration has four clear counterexamples. Moreover, G1 includes six multi-section cases with fragmented evidence, so a source-document grouping cannot stand in for actual decomposition benefit.

No route was run, and no retrieval outcome is available. This gate therefore cannot infer that decomposition would help G2 or hurt G1. It only bounds the risk that a shallow surface cue could mimic the auditor's structural interpretation on this small collection.

## 7. Final verdict — PASS_WITH_NOTE

Freeze is permitted. There is an observable sentence-pattern and clause-marker bias, including a simple two-cue pattern with 16/20 agreement against the **non-gold** source-layout grouping. The four counterexamples and substantial overlap across length, explicit asks, and literal topic cues keep it from being a near-mechanical separator. Preserve this limitation in future result interpretation; do not treat author/auditor metadata or this grouping as a routing label, and do not update the frozen 20 queries based on Router results.
