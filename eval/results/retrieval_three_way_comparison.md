# Lexical vs semantic vs hybrid retrieval

- Chunks: 655
- Lexical: `hashing-tfidf-v4`
- Semantic: `sentence-transformers/all-MiniLM-L6-v2`
- Hybrid: unweighted RRF, k=60, candidate depth=20
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Multi-turn mode: `standalone_reference_only`

## Overall

- Cases: 25
- hit_at_1: lexical=0.4000, semantic=0.4800, hybrid=0.4000
- hit_at_3: lexical=0.6800, semantic=0.7200, hybrid=0.6400
- hit_at_5: lexical=0.6800, semantic=0.7600, hybrid=0.7600
- mrr: lexical=0.5569, semantic=0.6163, hybrid=0.5480

## By category

### direct

- Cases: 5
- hit_at_1: lexical=0.2000, semantic=0.2000, hybrid=0.2000
- hit_at_3: lexical=0.6000, semantic=0.6000, hybrid=0.6000
- hit_at_5: lexical=0.6000, semantic=0.8000, hybrid=0.8000
- mrr: lexical=0.4069, semantic=0.4289, hybrid=0.4452

### semantic

- Cases: 7
- hit_at_1: lexical=0.2857, semantic=0.4286, hybrid=0.2857
- hit_at_3: lexical=0.5714, semantic=0.5714, hybrid=0.5714
- hit_at_5: lexical=0.5714, semantic=0.5714, hybrid=0.7143
- mrr: lexical=0.4536, semantic=0.5152, hybrid=0.4671

### broad

- Cases: 4
- hit_at_1: lexical=0.2500, semantic=0.2500, hybrid=0.0000
- hit_at_3: lexical=0.5000, semantic=0.7500, hybrid=0.2500
- hit_at_5: lexical=0.5000, semantic=0.7500, hybrid=0.5000
- mrr: lexical=0.3928, semantic=0.5357, hybrid=0.1929

### specific

- Cases: 5
- hit_at_1: lexical=0.8000, semantic=1.0000, hybrid=1.0000
- hit_at_3: lexical=1.0000, semantic=1.0000, hybrid=1.0000
- hit_at_5: lexical=1.0000, semantic=1.0000, hybrid=1.0000
- mrr: lexical=0.9000, semantic=1.0000, hybrid=1.0000

### multi_turn_oracle

- Cases: 4
- hit_at_1: lexical=0.5000, semantic=0.5000, hybrid=0.5000
- hit_at_3: lexical=0.7500, semantic=0.7500, hybrid=0.7500
- hit_at_5: lexical=0.7500, semantic=0.7500, hybrid=0.7500
- mrr: lexical=0.6607, semantic=0.6284, hybrid=0.6083

## Multi-source coverage

- lexical: coverage@3=0.2667, coverage@5=0.2667
- semantic: coverage@3=0.4667, coverage@5=0.5667
- hybrid: coverage@3=0.4000, coverage@5=0.5000

- `ret_013`: lexical=0.3333/0.3333, semantic=0.3333/0.3333, hybrid=0.0000/0.0000 (@3/@5)
- `ret_015`: lexical=0.0000/0.0000, semantic=0.0000/0.0000, hybrid=0.0000/0.0000 (@3/@5)
- `ret_016`: lexical=0.0000/0.0000, semantic=0.5000/0.5000, hybrid=0.5000/0.5000 (@3/@5)
- `multi_002`: lexical=0.5000/0.5000, semantic=1.0000/1.0000, hybrid=1.0000/1.0000 (@3/@5)
- `multi_004`: lexical=0.5000/0.5000, semantic=0.5000/1.0000, hybrid=0.5000/1.0000 (@3/@5)

## Oracle union upper bound

- Hit@1: 0.6400
- Hit@3: 0.9200
- Hit@5: 0.9200

## Tracked rank movement

- `ret_001`: 29 -> 2 -> 7
- `ret_003`: 6 -> 3 -> 4
- `ret_004`: 2 -> 9 -> 3
- `ret_007`: 42 -> 13 -> 23
- `ret_008`: 1 -> 41 -> 7
- `ret_009`: 8 -> 2 -> 2
- `ret_011`: 1 -> 189 -> 4
- `ret_012`: 38 -> 1 -> 3
- `ret_015`: 227 -> 7 -> 14
- `ret_016`: 15 -> 2 -> 3
- `multi_001`: 7 -> 1 -> 3
- `multi_003`: 2 -> 74 -> 10

## Hybrid Hit@5 failures

`ret_001`, `ret_007`, `ret_008`, `ret_013`, `ret_015`, `multi_003`

## Unsupported hybrid top-5

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- 1. RRF=0.032522 | `GitHub Terms of Service` | `B. Account Terms` | lexical_rank=2 | semantic_rank=1
- 2. RRF=0.031778 | `GitHub Pre-release License Terms` | `11. No Uptime Guarantees.` | lexical_rank=1 | semantic_rank=5
- 3. RRF=0.031746 | `GitHub Terms of Service` | `B. Account Terms > 3. Account Requirements` | lexical_rank=3 | semantic_rank=3
- 4. RRF=0.030536 | `GitHub Corporate Terms of Service` | `B. Account Terms > 6. Enterprise Cloud Service Level Agreement` | lexical_rank=5 | semantic_rank=6
- 5. RRF=0.028382 | `GitHub and Trade Controls` | `Frequently asked questions > What is available and not available?` | lexical_rank=12 | semantic_rank=9

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- 1. RRF=0.029116 | `GitHub General Privacy Statement` | `Private repositories: GitHub Access` | lexical_rank=17 | semantic_rank=2
- 2. RRF=0.026709 | `GitHub Corporate Terms of Service` | `D. Content Responsibility; Ownership; License Rights > 5. Contributions Under Repository License` | lexical_rank=18 | semantic_rank=12
- 3. RRF=0.016393 | `GitHub Secret Scanning Partner Program Agreement` | `4. Purpose Limitation on Match Data > 4.3 Private Repository Data` | lexical_rank=1 | semantic_rank=None
- 4. RRF=0.016393 | `GitHub Corporate Terms of Service` | `E. Private Repositories > 1. Control` | lexical_rank=None | semantic_rank=1
- 5. RRF=0.016129 | `GitHub Appeal and Reinstatement` | `Transparency` | lexical_rank=2 | semantic_rank=None

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- 1. RRF=0.032002 | `GitHub Community Guidelines` | `Appeal and Reinstatement` | lexical_rank=2 | semantic_rank=3
- 2. RRF=0.031778 | `GitHub Appeal and Reinstatement` | `How this works` | lexical_rank=5 | semantic_rank=1
- 3. RRF=0.031010 | `GitHub Appeal and Reinstatement` | `What are Appeals and Reinstatements?` | lexical_rank=4 | semantic_rank=5
- 4. RRF=0.029857 | `GitHub Appeal and Reinstatement` | `How this works > Reinstatements` | lexical_rank=6 | semantic_rank=8
- 5. RRF=0.029387 | `GitHub Appeal and Reinstatement` | `Appeal and Reinstatement` | lexical_rank=3 | semantic_rank=14
