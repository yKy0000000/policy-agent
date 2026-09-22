# Four-way retrieval comparison

- Chunks: 655
- Candidate union: lexical Top-20 + semantic Top-20
- Candidate recall before reranking: 1.0000
- Multi-turn mode: `standalone_reference_only`

## Overall

- Cases: 25
- hit_at_1: lexical=0.4000, semantic=0.4800, hybrid=0.4000, reranked=0.6400
- hit_at_3: lexical=0.6800, semantic=0.7200, hybrid=0.6400, reranked=0.8400
- hit_at_5: lexical=0.6800, semantic=0.7600, hybrid=0.7600, reranked=0.8800
- mrr: lexical=0.5569, semantic=0.6163, hybrid=0.5480, reranked=0.7569

## By category

### direct

- Cases: 5
- hit_at_1: lexical=0.2000, semantic=0.2000, hybrid=0.2000, reranked=0.6000
- hit_at_3: lexical=0.6000, semantic=0.6000, hybrid=0.6000, reranked=0.8000
- hit_at_5: lexical=0.6000, semantic=0.8000, hybrid=0.8000, reranked=1.0000
- mrr: lexical=0.4069, semantic=0.4289, hybrid=0.4452, reranked=0.7400

### semantic

- Cases: 7
- hit_at_1: lexical=0.2857, semantic=0.4286, hybrid=0.2857, reranked=0.7143
- hit_at_3: lexical=0.5714, semantic=0.5714, hybrid=0.5714, reranked=0.8571
- hit_at_5: lexical=0.5714, semantic=0.5714, hybrid=0.7143, reranked=0.8571
- mrr: lexical=0.4536, semantic=0.5152, hybrid=0.4671, reranked=0.8016

### broad

- Cases: 4
- hit_at_1: lexical=0.2500, semantic=0.2500, hybrid=0.0000, reranked=0.0000
- hit_at_3: lexical=0.5000, semantic=0.7500, hybrid=0.2500, reranked=0.5000
- hit_at_5: lexical=0.5000, semantic=0.7500, hybrid=0.5000, reranked=0.5000
- mrr: lexical=0.3928, semantic=0.5357, hybrid=0.1929, reranked=0.2778

### specific

- Cases: 5
- hit_at_1: lexical=0.8000, semantic=1.0000, hybrid=1.0000, reranked=1.0000
- hit_at_3: lexical=1.0000, semantic=1.0000, hybrid=1.0000, reranked=1.0000
- hit_at_5: lexical=1.0000, semantic=1.0000, hybrid=1.0000, reranked=1.0000
- mrr: lexical=0.9000, semantic=1.0000, hybrid=1.0000, reranked=1.0000

### multi_turn_oracle

- Cases: 4
- hit_at_1: lexical=0.5000, semantic=0.5000, hybrid=0.5000, reranked=0.7500
- hit_at_3: lexical=0.7500, semantic=0.7500, hybrid=0.7500, reranked=1.0000
- hit_at_5: lexical=0.7500, semantic=0.7500, hybrid=0.7500, reranked=1.0000
- mrr: lexical=0.6607, semantic=0.6284, hybrid=0.6083, reranked=0.8750

## Multi-source coverage

- lexical: coverage@3=0.2667, coverage@5=0.2667
- semantic: coverage@3=0.4667, coverage@5=0.5667
- hybrid: coverage@3=0.4000, coverage@5=0.5000
- reranked: coverage@3=0.4000, coverage@5=0.6000

- `ret_013`: lexical=0.3333/0.3333, semantic=0.3333/0.3333, hybrid=0.0000/0.0000, reranked=0.0000/0.0000 (@3/@5)
- `ret_015`: lexical=0.0000/0.0000, semantic=0.0000/0.0000, hybrid=0.0000/0.0000, reranked=0.5000/1.0000 (@3/@5)
- `ret_016`: lexical=0.0000/0.0000, semantic=0.5000/0.5000, hybrid=0.5000/0.5000, reranked=0.0000/0.0000 (@3/@5)
- `multi_002`: lexical=0.5000/0.5000, semantic=1.0000/1.0000, hybrid=1.0000/1.0000, reranked=0.5000/1.0000 (@3/@5)
- `multi_004`: lexical=0.5000/0.5000, semantic=0.5000/1.0000, hybrid=0.5000/1.0000, reranked=1.0000/1.0000 (@3/@5)

## Tracked rank movement

- `ret_001`: lexical=29, semantic=2, RRF=7, reranked=5
- `ret_003`: lexical=6, semantic=3, RRF=4, reranked=1
- `ret_004`: lexical=2, semantic=9, RRF=3, reranked=1
- `ret_007`: lexical=42, semantic=13, RRF=23, reranked=1
- `ret_008`: lexical=1, semantic=41, RRF=7, reranked=1
- `ret_009`: lexical=8, semantic=2, RRF=2, reranked=2
- `ret_011`: lexical=1, semantic=189, RRF=4, reranked=9
- `ret_012`: lexical=38, semantic=1, RRF=3, reranked=1
- `ret_013`: lexical=1, semantic=2, RRF=6, reranked=6
- `ret_015`: lexical=227, semantic=7, RRF=14, reranked=3
- `ret_016`: lexical=15, semantic=2, RRF=3, reranked=9
- `multi_001`: lexical=7, semantic=1, RRF=3, reranked=1
- `multi_003`: lexical=2, semantic=74, RRF=10, reranked=2

## Reranked Hit@5 failures

`ret_011`, `ret_013`, `ret_016`

## Unsupported reranked Top-5

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- 1. score=0.9254 | `GitHub Pre-release License Terms` | `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=1 | semantic_rank=5
- 2. score=-0.2835 | `GitHub Terms of Service` | `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=3
- 3. score=-0.6392 | `GitHub Sponsors Additional Terms` | `Terms for Sponsors > 2. Payment. > 2.2. Fees.` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=None | semantic_rank=17
- 4. score=-1.0336 | `GitHub and Trade Controls` | `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=12 | semantic_rank=9
- 5. score=-1.0845 | `GitHub Community Code of Conduct` | `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=6 | semantic_rank=None

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- 1. score=-6.2922 | `Guidelines for Legal Requests of User Data` | `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=5 | semantic_rank=None
- 2. score=-9.3447 | `GitHub and Trade Controls` | `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=6 | semantic_rank=None
- 3. score=-9.5414 | `GitHub Marketplace Developer Agreement` | `Addendum 1: Data Protection Addendum` | `Policies/github-terms/github-marketplace-developer-agreement.md` | lexical_rank=14 | semantic_rank=None
- 4. score=-10.1946 | `Guidelines for Legal Requests of User Data` | `Submitting requests` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=None | semantic_rank=7
- 5. score=-10.4178 | `GitHub General Privacy Statement` | `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=2

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- 1. score=1.8594 | `GitHub Corporate Terms of Service` | `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=2
- 2. score=1.4025 | `GitHub Appeal and Reinstatement` | `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=1
- 3. score=1.0154 | `GitHub Corporate Terms of Service` | `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=11
- 4. score=0.0662 | `GitHub Secret Scanning Partner Program Agreement` | `16. Term, Termination, and Survival > 16.4 Immediate Suspension` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=None | semantic_rank=9
- 5. score=-1.1247 | `GitHub Terms of Service` | `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=17

## Reranking performance

- Queries: 28
- Candidate count average/min/max: 33.64 / 26 / 38
- Cross-Encoder total/mean: 58.0686s / 2.0739s
- p50/p95: 2.0651s / 2.4261s
