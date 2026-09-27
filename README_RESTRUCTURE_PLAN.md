# README Restructure Plan (v1)

**Do not overwrite `README.md` in this round.** This is a proposed structure only. Theme:

> **Add complexity only when a measured failure mode justifies it.**

## Proposed section order

1. **Project overview** — one-paragraph description: GitHub policy Q&A over `github/site-policy`; deterministic pipeline; abstains when evidence is insufficient. Keep the current concise intro; drop the long architecture figure block down to section 2.
2. **Final architecture** — the decided production/working path: multi-turn rewrite → Lexical Top20 + Semantic Top20 → union/dedup → BGE reranker → fixed Top5 → grounded generation → deterministic citation validation. State the excluded mechanisms (router, default decomposition, hierarchical expansion) and the Stage 0 two-configuration note.
3. **Why retrieval was not the main bottleneck** — candidate required-fact coverage ≈ 98.3%; the binding constraint is allocation/utilization. This becomes the framing for everything after.
4. **Evaluation benchmark** — Validation V1: 50 untouched broad queries, 239 required atomic facts, frozen Human Truth, preregistered gates; distinguish candidate coverage vs answer quality; note the 16-case V3 dev set.
5. **A1 — Query routing experiment** — hypothesis, blind evaluation, strict dominance of `query_router_v1` by `coverage_selector_v2`, and the KILL decision. Include the quality–cost table (no composite score).
6. **A2 — Requirement decomposition mechanism probe** — hypothesis, the `VAL-001-046` showcase table (original / deeper / MMR / requirement query), the 1/50 incidence, and `A2_MECHANISM_CONFIRMED_BUT_NOT_ADOPTED`.
7. **A3 — Why hierarchical retrieval was not tested** — fragmentation trigger definition, 0 confirmed cases, `A3_NOT_TRIGGERED`.
8. **Final architecture decisions** — one table (mechanism / hypothesis / evidence / decision) covering KEEP / KILL / REFERENCE / CONFIRMED-NOT-ADOPTED / NOT-TRIGGERED.
9. **Quality–cost results** — the A1 headline table plus the existing Validation V1 token-saving result; keep separate, no merged score.
10. **Demo** — minimal `PolicySupportAgent` snippet and CLI usage (`--debug`, evidence modes), matching the surviving architecture.
11. **Reproducibility** — test command, offline `--check` runners, generation/judge runners that need an endpoint, and the frozen artifact/decision records. Keep the UNKNOWN-reconciliation, journal state-machine, hash, and executor-audit details **here and only here** (appendix).
12. **Limitations** — carry over existing limitations (snapshot-bound corpus, model download, citation validation is structural not entailment, dev sets are diagnostic, candidate ceiling, decomposition dormant).
13. **Key lessons** — the closing theme: measure the bottleneck first; a real mechanism can still be non-adoptable if incidence is low; remove dominated components; keep negative results.

## Editing rules

- Preserve all existing numbers and their exact scopes (validation vs diagnostic).
- Do not introduce a composite score.
- Keep the research/evaluation layer clearly separated from the production path.
- Move execution/audit minutiae (reconciliation states, journal, hashes) into the Reproducibility appendix.
- Do not present `query_router_v1` or default decomposition as available features.

## Suggested deletions / demotions from the current README

- Demote the early source-level Hit@K / MRR table and RRF negative experiment into a short "retrieval diagnostics" subsection under section 3.
- Demote the Dynamic-K exploratory extension into a brief future-work note.
- Move the long CLI/pipeline prose into sections 10–11.
