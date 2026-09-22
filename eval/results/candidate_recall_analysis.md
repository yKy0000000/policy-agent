# Candidate recall upper-bound analysis

- Supported cases: 25
- Candidate depths per retriever: 1, 3, 5, 10, 20, 40
- Lexical: `hashing-tfidf-v4`
- Semantic: `sentence-transformers/all-MiniLM-L6-v2`
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Multi-turn mode: `standalone_reference_only`

## Overall candidate recall

- @1: 16/25 = 0.6400
- @3: 23/25 = 0.9200
- @5: 23/25 = 0.9200
- @10: 24/25 = 0.9600
- @20: 25/25 = 1.0000
- @40: 25/25 = 1.0000

## Recall by category

- direct: @1=0.2000, @3=1.0000, @5=1.0000, @10=1.0000, @20=1.0000, @40=1.0000
- semantic: @1=0.7143, @3=0.8571, @5=0.8571, @10=0.8571, @20=1.0000, @40=1.0000
- broad: @1=0.5000, @3=0.7500, @5=0.7500, @10=1.0000, @20=1.0000, @40=1.0000
- specific: @1=1.0000, @3=1.0000, @5=1.0000, @10=1.0000, @20=1.0000, @40=1.0000
- multi_turn_oracle: @1=0.7500, @3=1.0000, @5=1.0000, @10=1.0000, @20=1.0000, @40=1.0000

## Multi-source coverage

- Mean: @1=0.2667, @3=0.5333, @5=0.6333, @10=0.8333, @20=0.8333, @40=1.0000
- `ret_013` (3 expected): @1=0.3333, @3=0.6667, @5=0.6667, @10=0.6667, @20=0.6667, @40=1.0000
- `ret_015` (2 expected): @1=0.0000, @3=0.0000, @5=0.0000, @10=1.0000, @20=1.0000, @40=1.0000
- `ret_016` (2 expected): @1=0.0000, @3=0.5000, @5=0.5000, @10=0.5000, @20=0.5000, @40=1.0000
- `multi_002` (2 expected): @1=0.5000, @3=1.0000, @5=1.0000, @10=1.0000, @20=1.0000, @40=1.0000
- `multi_004` (2 expected): @1=0.5000, @3=0.5000, @5=1.0000, @10=1.0000, @20=1.0000, @40=1.0000

## Failures by depth

- @1: `ret_001`, `ret_003`, `ret_004`, `ret_005`, `ret_007`, `ret_009`, `ret_015`, `ret_016`, `multi_003`
- @3: `ret_007`, `ret_015`
- @5: `ret_007`, `ret_015`
- @10: `ret_007`
- @20: None.
- @40: None.

## First relevant ranks

- `ret_001`: lexical=29, semantic=2, best=2
- `ret_002`: lexical=1, semantic=1, best=1
- `ret_003`: lexical=6, semantic=3, best=3
- `ret_004`: lexical=2, semantic=9, best=2
- `ret_005`: lexical=3, semantic=5, best=3
- `ret_006`: lexical=2, semantic=1, best=1
- `ret_007`: lexical=42, semantic=13, best=13
- `ret_008`: lexical=1, semantic=41, best=1
- `ret_009`: lexical=8, semantic=2, best=2
- `ret_010`: lexical=2, semantic=1, best=1
- `ret_011`: lexical=1, semantic=189, best=1
- `ret_012`: lexical=38, semantic=1, best=1
- `ret_013`: lexical=1, semantic=2, best=1
- `ret_014`: lexical=2, semantic=1, best=1
- `ret_015`: lexical=227, semantic=7, best=7
- `ret_016`: lexical=15, semantic=2, best=2
- `ret_017`: lexical=1, semantic=1, best=1
- `ret_018`: lexical=1, semantic=1, best=1
- `ret_019`: lexical=1, semantic=1, best=1
- `ret_020`: lexical=1, semantic=1, best=1
- `ret_021`: lexical=2, semantic=1, best=1
- `multi_001`: lexical=7, semantic=1, best=1
- `multi_002`: lexical=1, semantic=2, best=1
- `multi_003`: lexical=2, semantic=74, best=2
- `multi_004`: lexical=1, semantic=1, best=1

## First candidate depth distribution

- Depth 1: 16 case(s)
- Depth 2: 5 case(s)
- Depth 3: 2 case(s)
- Depth 7: 1 case(s)
- Depth 13: 1 case(s)

## Candidate pool size

- @1: average=1.64, minimum=1, maximum=2
- @3: average=5.20, minimum=4, maximum=6
- @5: average=8.36, minimum=6, maximum=10
- @10: average=16.64, minimum=12, maximum=19
- @20: average=33.48, minimum=26, maximum=38
- @40: average=66.92, minimum=56, maximum=75

## Recall plateau

- Final tested hit rate: 1.0000
- First tested depth at the final rate: 20
- Exact depth that recalls all supported cases: 13
