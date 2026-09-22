# Lexical vs semantic retrieval

- Chunks: 655
- Lexical: `hashing-tfidf-v4`
- Semantic: `sentence-transformers/all-MiniLM-L6-v2`
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Multi-turn mode: `standalone_reference_only`

## Overall

- Cases: 25
- hit_at_1: lexical=0.4000, semantic=0.4800, delta=+0.0800
- hit_at_3: lexical=0.6800, semantic=0.7200, delta=+0.0400
- hit_at_5: lexical=0.6800, semantic=0.7600, delta=+0.0800
- mrr: lexical=0.5569, semantic=0.6163, delta=+0.0594

## By category

### direct

- Cases: 5
- hit_at_1: lexical=0.2000, semantic=0.2000, delta=+0.0000
- hit_at_3: lexical=0.6000, semantic=0.6000, delta=+0.0000
- hit_at_5: lexical=0.6000, semantic=0.8000, delta=+0.2000
- mrr: lexical=0.4069, semantic=0.4289, delta=+0.0220

### semantic

- Cases: 7
- hit_at_1: lexical=0.2857, semantic=0.4286, delta=+0.1429
- hit_at_3: lexical=0.5714, semantic=0.5714, delta=+0.0000
- hit_at_5: lexical=0.5714, semantic=0.5714, delta=+0.0000
- mrr: lexical=0.4536, semantic=0.5152, delta=+0.0616

### broad

- Cases: 4
- hit_at_1: lexical=0.2500, semantic=0.2500, delta=+0.0000
- hit_at_3: lexical=0.5000, semantic=0.7500, delta=+0.2500
- hit_at_5: lexical=0.5000, semantic=0.7500, delta=+0.2500
- mrr: lexical=0.3928, semantic=0.5357, delta=+0.1429

### specific

- Cases: 5
- hit_at_1: lexical=0.8000, semantic=1.0000, delta=+0.2000
- hit_at_3: lexical=1.0000, semantic=1.0000, delta=+0.0000
- hit_at_5: lexical=1.0000, semantic=1.0000, delta=+0.0000
- mrr: lexical=0.9000, semantic=1.0000, delta=+0.1000

### multi_turn_oracle

- Cases: 4
- hit_at_1: lexical=0.5000, semantic=0.5000, delta=+0.0000
- hit_at_3: lexical=0.7500, semantic=0.7500, delta=+0.0000
- hit_at_5: lexical=0.7500, semantic=0.7500, delta=+0.0000
- mrr: lexical=0.6607, semantic=0.6284, delta=-0.0323

## Multi-source coverage

- coverage@3: lexical=0.2667, semantic=0.4667, delta=+0.2000
- coverage@5: lexical=0.2667, semantic=0.5667, delta=+0.3000

- `ret_013`: @3 0.3333 -> 0.3333; @5 0.3333 -> 0.3333
- `ret_015`: @3 0.0000 -> 0.0000; @5 0.0000 -> 0.0000
- `ret_016`: @3 0.0000 -> 0.5000; @5 0.0000 -> 0.5000
- `multi_002`: @3 0.5000 -> 1.0000; @5 0.5000 -> 1.0000
- `multi_004`: @3 0.5000 -> 0.5000; @5 0.5000 -> 1.0000

## Tracked failure rank movement

- `ret_001`: 29 -> 2
- `ret_003`: 6 -> 3
- `ret_007`: 42 -> 13
- `ret_009`: 8 -> 2
- `ret_012`: 38 -> 1
- `ret_015`: 227 -> 7
- `ret_016`: 15 -> 2
- `multi_001`: 7 -> 1

## Semantic Hit@5 failures

`ret_004`, `ret_007`, `ret_008`, `ret_011`, `ret_015`, `multi_003`

## Unsupported semantic top-5

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- 1. 0.6583 | `GitHub Terms of Service` | `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
- 2. 0.6298 | `GitHub Terms of Service` | `L. Payment > 2. Upgrades, Downgrades, and Changes` | `Policies/github-terms/github-terms-of-service.md`
- 3. 0.6271 | `GitHub Terms of Service` | `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
- 4. 0.6232 | `GitHub Corporate Terms of Service` | `S. Support` | `Policies/github-terms/github-corporate-terms-of-service.md`
- 5. 0.6195 | `GitHub Pre-release License Terms` | `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md`

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- 1. 0.3478 | `GitHub Corporate Terms of Service` | `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md`
- 2. 0.3249 | `GitHub General Privacy Statement` | `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md`
- 3. 0.3206 | `GitHub Subprocessors` | `(document introduction)` | `Policies/privacy-policies/github-subprocessors.md`
- 4. 0.3164 | `GitHub Corporate Terms of Service` | `E. Private Repositories > 2. Confidentiality` | `Policies/github-terms/github-corporate-terms-of-service.md`
- 5. 0.3112 | `GitHub General Privacy Statement` | `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- 1. 0.6706 | `GitHub Appeal and Reinstatement` | `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- 2. 0.6658 | `GitHub Corporate Terms of Service` | `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md`
- 3. 0.6303 | `GitHub Community Guidelines` | `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
- 4. 0.6287 | `GitHub Corporate Terms of Service` | `K. Term; Termination; Suspension > 5. Suspension` | `Policies/github-terms/github-corporate-terms-of-service.md`
- 5. 0.6228 | `GitHub Appeal and Reinstatement` | `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
