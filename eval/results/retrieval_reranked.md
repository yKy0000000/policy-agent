# Retrieval reranked baseline

This report evaluates retrieval only. Multi-turn cases use their standalone references; unsupported cases are displayed but not scored.

- Candidate union: lexical Top-20 + semantic Top-20, deduplicated by `chunk_id`
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Reranker features: query + structured candidate text only; component scores and ranks excluded.

## Configuration

- Embedding: `sentence-transformers-cross-encoder/cross-encoder/ms-marco-MiniLM-L-6-v2`
- Index chunks / ranking depth: 655
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Index SHA-256: `672f4231d914272da061524e34b845e0d60711ccb335be531cf0df117f2580a1`
- Source match: exact `source_path`, plus case-insensitive `heading_contains` matching when non-empty.

## Overall supported-case metrics

- Cases: 25
- Hit@1: 0.6400
- Hit@3: 0.8400
- Hit@5: 0.8800
- MRR: 0.7569

## Metrics by category

### direct

- Cases: 5
- Hit@1: 0.6000
- Hit@3: 0.8000
- Hit@5: 1.0000
- MRR: 0.7400

### semantic

- Cases: 7
- Hit@1: 0.7143
- Hit@3: 0.8571
- Hit@5: 0.8571
- MRR: 0.8016

### broad

- Cases: 4
- Hit@1: 0.0000
- Hit@3: 0.5000
- Hit@5: 0.5000
- MRR: 0.2778

### specific

- Cases: 5
- Hit@1: 1.0000
- Hit@3: 1.0000
- Hit@5: 1.0000
- MRR: 1.0000

### multi_turn_oracle

- Cases: 4
- Hit@1: 0.7500
- Hit@3: 1.0000
- Hit@5: 1.0000
- MRR: 0.8750

## Multi-source coverage

- Multi-source cases: 5
- Mean coverage@3: 0.4000
- Mean coverage@5: 0.6000

- `ret_013` (3 expected): coverage@3=0.0000, coverage@5=0.0000
- `ret_015` (2 expected): coverage@3=0.5000, coverage@5=1.0000
- `ret_016` (2 expected): coverage@3=0.0000, coverage@5=0.0000
- `multi_002` (2 expected): coverage@3=0.5000, coverage@5=1.0000
- `multi_004` (2 expected): coverage@3=1.0000, coverage@5=1.0000

## Candidate recall before reranking

- Supported: 25/25
- Recall: 1.0000

## Reranking performance

- Queries: 28
- Candidate count average/min/max: 33.64 / 26 / 38
- Cross-Encoder total: 58.0686s
- Mean per query: 2.0739s
- p50 / p95: 2.0651s / 2.4261s
- End-to-end retrieval plus reranking total: 58.9106s

## Priority cases for human review

### Supported cases with Hit@5 = 0

`ret_011`, `ret_013`, `ret_016`

### Supported cases with Hit@1 = 0 and Hit@5 = 1

`ret_001`, `ret_002`, `ret_009`, `ret_014`, `ret_015`, `multi_003`

## Unsupported cases (not scored)

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- Top-5:
  - 1. score=0.9254 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=1 | semantic_rank=5 | reranker_score=0.9254
  - 2. score=-0.2835 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=3 | reranker_score=-0.2835
  - 3. score=-0.6392 | `GitHub Sponsors Additional Terms` | heading `Terms for Sponsors > 2. Payment. > 2.2. Fees.` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=None | semantic_rank=17 | reranker_score=-0.6392
  - 4. score=-1.0336 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=12 | semantic_rank=9 | reranker_score=-1.0336
  - 5. score=-1.0845 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=6 | semantic_rank=None | reranker_score=-1.0845

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- Top-5:
  - 1. score=-6.2922 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=5 | semantic_rank=None | reranker_score=-6.2922
  - 2. score=-9.3447 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=6 | semantic_rank=None | reranker_score=-9.3447
  - 3. score=-9.5414 | `GitHub Marketplace Developer Agreement` | heading `Addendum 1: Data Protection Addendum` | `Policies/github-terms/github-marketplace-developer-agreement.md` | lexical_rank=14 | semantic_rank=None | reranker_score=-9.5414
  - 4. score=-10.1946 | `Guidelines for Legal Requests of User Data` | heading `Submitting requests` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=None | semantic_rank=7 | reranker_score=-10.1946
  - 5. score=-10.4178 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=2 | reranker_score=-10.4178

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- Top-5:
  - 1. score=1.8594 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=2 | reranker_score=1.8594
  - 2. score=1.4025 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=1 | reranker_score=1.4025
  - 3. score=1.0154 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=11 | reranker_score=1.0154
  - 4. score=0.0662 | `GitHub Secret Scanning Partner Program Agreement` | heading `16. Term, Termination, and Survival > 16.4 Immediate Suspension` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=None | semantic_rank=9 | reranker_score=0.0662
  - 5. score=-1.1247 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=17 | reranker_score=-1.1247

## Per-case results

### ret_001

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: How old must someone be to have a GitHub account?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 1
- First relevant rank: 5
- Reciprocal rank: 0.2000
- Top-5 retrieved chunks:
  - 1. score=7.4415 | `GitHub Marketplace Terms of Service` | heading `B. Use Requirements` | `Policies/github-terms/github-marketplace-terms-of-service.md` | lexical_rank=None | semantic_rank=7 | reranker_score=7.4415
  - 2. score=6.8931 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 2. Account Requirements` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=17 | semantic_rank=1 | reranker_score=6.8931
  - 3. score=5.7086 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 1. Acceptable Use. > 1.1. GitHub Sponsors Program` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=None | semantic_rank=6 | reranker_score=5.7086
  - 4. score=5.0263 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=1 | semantic_rank=5 | reranker_score=5.0263
  - 5. score=3.8537 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=2 | reranker_score=3.8537

---

### ret_002

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=7.4574 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=2 | semantic_rank=2 | reranker_score=7.4574
  - 2. score=7.2205 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=7.2205
  - 3. score=1.4887 | `GitHub Marketplace Developer Agreement` | heading `3.	RESTRICTIONS AND RESPONSIBILITIES` | `Policies/github-terms/github-marketplace-developer-agreement.md` | lexical_rank=13 | semantic_rank=None | reranker_score=1.4887
  - 4. score=0.6403 | `GitHub Acceptable Use Policies` | heading `4. Spam and Inauthentic Activity on GitHub` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=6 | reranker_score=0.6403
  - 5. score=-0.1044 | `GitHub SIRT description RFC 2350` | heading `3. Charter > 3.1 Mission Statement` | `Policies/security-policies/github-sirt-description-rfc-2350.md` | lexical_rank=5 | semantic_rank=None | reranker_score=-0.1044

---

### ret_003

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What is an appeal under GitHub's Appeal and Reinstatement policy?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=7.8766 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=6 | semantic_rank=3 | reranker_score=7.8766
  - 2. score=7.3685 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=3 | semantic_rank=6 | reranker_score=7.3685
  - 3. score=6.8822 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=5 | reranker_score=6.8822
  - 4. score=6.7701 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=8 | semantic_rank=4 | reranker_score=6.7701
  - 5. score=6.7358 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=2 | semantic_rank=2 | reranker_score=6.7358

---

### ret_004

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What account information does GitHub collect when a user opens an account?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=8.1365 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=2 | semantic_rank=9 | reranker_score=8.1365
  - 2. score=5.6090 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=9 | semantic_rank=2 | reranker_score=5.6090
  - 3. score=4.7204 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=4.7204
  - 4. score=3.7177 | `GitHub Deceased User Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-deceased-user-policy.md` | lexical_rank=14 | semantic_rank=None | reranker_score=3.7177
  - 5. score=3.3821 | `GitHub Open Source Applications Terms and Conditions` | heading `Privacy` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md` | lexical_rank=13 | semantic_rank=10 | reranker_score=3.3821

---

### ret_005

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What contact details must be included in a DMCA counter notice?
- Expected sources:
  - `Guide to Submitting a DMCA Counter Notice` | heading contains `Your Counter Notice Must` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=5.0899 | `Guide to Submitting a DMCA Counter Notice` | heading `Your Counter Notice Must...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=3 | semantic_rank=5 | reranker_score=5.0899
  - 2. score=4.6918 | `Guide to Submitting a DMCA Counter Notice` | heading `How to Submit Your Counter Notice` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=4.6918
  - 3. score=4.1578 | `Guide to Submitting a DMCA Takedown Notice` | heading `Complaints about Anti-Circumvention Technology` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=10 | semantic_rank=13 | reranker_score=4.1578
  - 4. score=2.2131 | `Guide to Submitting a DMCA Takedown Notice` | heading `How to Submit Your Complaint` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=11 | semantic_rank=3 | reranker_score=2.2131
  - 5. score=2.1674 | `Guide to Submitting a DMCA Counter Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=6 | semantic_rank=7 | reranker_score=2.1674

---

### ret_006

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Can someone target a person with degrading language because of their identity or background?
- Expected sources:
  - `GitHub Hate Speech and Discrimination` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=-5.9452 | `GitHub Hate Speech and Discrimination` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md` | lexical_rank=2 | semantic_rank=1 | reranker_score=-5.9452
  - 2. score=-8.7226 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md` | lexical_rank=None | semantic_rank=3 | reranker_score=-8.7226
  - 3. score=-8.9798 | `GitHub Global Data Privacy Notice for Candidates` | heading `Overview > Personal Data that We Process` | `Policies/privacy-policies/github-candidate-privacy-policy.md` | lexical_rank=8 | semantic_rank=None | reranker_score=-8.9798
  - 4. score=-9.2849 | `GitHub Event Code of Conduct` | heading `Code of Conduct` | `Policies/github-terms/github-event-code-of-conduct.md` | lexical_rank=4 | semantic_rank=15 | reranker_score=-9.2849
  - 5. score=-9.5485 | `GitHub Global Data Privacy Notice for Candidates` | heading `Addenda > Canada Addendum` | `Policies/privacy-policies/github-candidate-privacy-policy.md` | lexical_rank=1 | semantic_rank=None | reranker_score=-9.5485

---

### ret_007

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: May I publish another person's home address or banking details in a repository?
- Expected sources:
  - `GitHub Doxxing and Invasion of Privacy` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=-5.0745 | `GitHub Doxxing and Invasion of Privacy` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` | lexical_rank=None | semantic_rank=13 | reranker_score=-5.0745
  - 2. score=-5.5961 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=12 | semantic_rank=9 | reranker_score=-5.5961
  - 3. score=-6.4628 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md` | lexical_rank=3 | semantic_rank=None | reranker_score=-6.4628
  - 4. score=-7.0117 | `GitHub Corporate Terms of Service` | heading `A. Definitions` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=9 | semantic_rank=None | reranker_score=-7.0117
  - 5. score=-7.1188 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=6 | semantic_rank=None | reranker_score=-7.1188

---

### ret_008

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub report a researcher to law enforcement for an accidental, good-faith violation during authorized vulnerability research?
- Expected sources:
  - `GitHub Bug Bounty Program Legal Safe Harbor` | heading contains `Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=5.9634 | `GitHub Bug Bounty Program Legal Safe Harbor` | heading `1. Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` | lexical_rank=1 | semantic_rank=None | reranker_score=5.9634
  - 2. score=-0.8870 | `Coordinated Disclosure of Security Vulnerabilities` | heading `Bounty Program` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=17 | semantic_rank=None | reranker_score=-0.8870
  - 3. score=-1.4362 | `GitHub Research Program Terms` | heading `G. Limitation of Liability` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=6 | semantic_rank=8 | reranker_score=-1.4362
  - 4. score=-1.6345 | `Guidelines for Legal Requests of User Data` | heading `Requests from foreign law enforcement` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=5 | semantic_rank=7 | reranker_score=-1.6345
  - 5. score=-1.9938 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=None | semantic_rank=15 | reranker_score=-1.9938

---

### ret_009

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Can a company connected to a sanctioned region continue using private repositories and paid GitHub features?
- Expected sources:
  - `GitHub and Trade Controls` | heading contains `How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=4.5159 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=9 | semantic_rank=1 | reranker_score=4.5159
  - 2. score=4.1926 | `GitHub and Trade Controls` | heading `Frequently asked questions > How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=8 | semantic_rank=2 | reranker_score=4.1926
  - 3. score=0.5985 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 3. Access` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=7 | semantic_rank=13 | reranker_score=0.5985
  - 4. score=0.0395 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=14 | semantic_rank=6 | reranker_score=0.0395
  - 5. score=0.0203 | `GitHub Terms of Service` | heading `E. Private Repositories > 3. Access` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=10 | semantic_rank=None | reranker_score=0.0203

---

### ret_010

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: If I publish code in an open repository, am I directing GitHub to make it available to everyone online?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=3.6914 | `GitHub Terms of Service` | heading `D. User-Generated Content > 8. Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=2 | semantic_rank=1 | reranker_score=3.6914
  - 2. score=1.2380 | `GitHub Open Source Applications Terms and Conditions` | heading `Open Source Licenses and Notices` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md` | lexical_rank=None | semantic_rank=8 | reranker_score=1.2380
  - 3. score=0.5412 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=4 | semantic_rank=7 | reranker_score=0.5412
  - 4. score=-0.3415 | `GitHub Open Source Applications Terms and Conditions` | heading `(document introduction)` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md` | lexical_rank=5 | semantic_rank=None | reranker_score=-0.3415
  - 5. score=-0.7866 | `GitHub Terms of Service` | heading `D. User-Generated Content > 5. License Grant to Other Users` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=2 | reranker_score=-0.7866

---

### ret_011

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub warn an account owner before handing their information to investigators?
- Expected sources:
  - `Guidelines for Legal Requests of User Data` | heading contains `notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 9
- Reciprocal rank: 0.1111
- Top-5 retrieved chunks:
  - 1. score=3.4396 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=11 | semantic_rank=1 | reranker_score=3.4396
  - 2. score=2.8653 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=2 | semantic_rank=4 | reranker_score=2.8653
  - 3. score=1.6029 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=None | semantic_rank=11 | reranker_score=1.6029
  - 4. score=0.5122 | `GitHub Research Program Terms` | heading `B. Confidentiality` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=18 | semantic_rank=None | reranker_score=0.5122
  - 5. score=-0.0675 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=None | reranker_score=-0.0675

---

### ret_012

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Is code used to study vulnerabilities automatically removed just because it could also be misused?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=-2.5262 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=None | semantic_rank=1 | reranker_score=-2.5262
  - 2. score=-3.7517 | `GitHub Bug Bounty Program Legal Safe Harbor` | heading `1. Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` | lexical_rank=15 | semantic_rank=7 | reranker_score=-3.7517
  - 3. score=-4.9758 | `Guide to Submitting a DMCA Counter Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=3 | semantic_rank=None | reranker_score=-4.9758
  - 4. score=-5.4475 | `Guide to Submitting a DMCA Takedown Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=10 | semantic_rank=None | reranker_score=-5.4475
  - 5. score=-5.9444 | `GitHub Terrorism and Violent Extremism` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-terrorism-and-violent-extremism.md` | lexical_rank=9 | semantic_rank=None | reranker_score=-5.9444

---

### ret_013

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: When can GitHub restrict or shut down an account?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `GitHub May Terminate` | `Policies/github-terms/github-terms-of-service.md`
  - `GitHub Appeal and Reinstatement` | heading contains `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - `GitHub Community Guidelines` | heading contains `What happens if someone violates GitHub's policies?` | `Policies/github-terms/github-community-guidelines.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 6
- Reciprocal rank: 0.1667
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=5.3618 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=4 | reranker_score=5.3618
  - 2. score=5.3513 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension.` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=None | semantic_rank=17 | reranker_score=5.3513
  - 3. score=4.8415 | `GitHub and Trade Controls` | heading `Frequently asked questions > How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=None | semantic_rank=15 | reranker_score=4.8415
  - 4. score=4.4954 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=11 | semantic_rank=8 | reranker_score=4.4954
  - 5. score=4.4207 | `GitHub Terms of Service` | heading `M. Cancellation and Termination` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=5 | reranker_score=4.4207

---

### ret_014

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: What information does GitHub gather about people who use its services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=7.0441 | `GitHub General Privacy Statement` | heading `US State Specific Information > Notice of Collection of Personal Information` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=16 | semantic_rank=3 | reranker_score=7.0441
  - 2. score=6.4819 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=None | semantic_rank=9 | reranker_score=6.4819
  - 3. score=6.4144 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=None | semantic_rank=1 | reranker_score=6.4144
  - 4. score=6.1555 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=3 | semantic_rank=4 | reranker_score=6.1555
  - 5. score=5.6360 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=None | semantic_rank=2 | reranker_score=5.6360

---

### ret_015

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: What kinds of behavior or material are not allowed on GitHub?
- Expected sources:
  - `GitHub Acceptable Use Policies` | heading contains `User Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - `GitHub Acceptable Use Policies` | heading contains `Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Source coverage@3: 0.5000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=4.7562 | `GitHub Acceptable Use Policies` | heading `4. Spam and Inauthentic Activity on GitHub` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=15 | reranker_score=4.7562
  - 2. score=4.4870 | `GitHub Disrupting the Experience of Other Users` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md` | lexical_rank=7 | semantic_rank=5 | reranker_score=4.4870
  - 3. score=4.4485 | `GitHub Acceptable Use Policies` | heading `2. User Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=7 | reranker_score=4.4485
  - 4. score=4.2357 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=8 | reranker_score=4.2357
  - 5. score=3.7462 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=1 | reranker_score=3.7462

---

### ret_016

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: How does GitHub respond when a government or law-enforcement body asks it to remove content or disclose user data?
- Expected sources:
  - `GitHub Government Takedown Policy` | heading contains `complete takedown request from a government` | `Policies/other-site-policies/github-government-takedown-policy.md`
  - `Guidelines for Legal Requests of User Data` | heading contains `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 9
- Reciprocal rank: 0.1111
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=5.7549 | `GitHub Government Takedown Policy` | heading `What is this?` | `Policies/other-site-policies/github-government-takedown-policy.md` | lexical_rank=2 | semantic_rank=3 | reranker_score=5.7549
  - 2. score=4.9420 | `Guidelines for Legal Requests of User Data` | heading `Requests from foreign law enforcement` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=11 | semantic_rank=None | reranker_score=4.9420
  - 3. score=4.3721 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=4 | semantic_rank=4 | reranker_score=4.3721
  - 4. score=3.9676 | `GitHub Global Data Privacy Notice for Candidates` | heading `Overview > How and Why We Disclose Personal Data` | `Policies/privacy-policies/github-candidate-privacy-policy.md` | lexical_rank=13 | semantic_rank=8 | reranker_score=3.9676
  - 5. score=3.5214 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=None | semantic_rank=1 | reranker_score=3.5214

---

### ret_017

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: If a parent repository is disabled for exposing private information, are all of its forks disabled automatically?
- Expected sources:
  - `GitHub Private Information Removal Policy` | heading contains `What About Forks?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=2.4655 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=2.4655
  - 2. score=1.1730 | `Guide to Submitting a DMCA Takedown Notice` | heading `Your Complaint Must ...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=10 | semantic_rank=14 | reranker_score=1.1730
  - 3. score=-0.0571 | `Guide to Submitting a DMCA Takedown Notice` | heading `Your Complaint Must ...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=5 | semantic_rank=None | reranker_score=-0.0571
  - 4. score=-1.1989 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=3 | semantic_rank=2 | reranker_score=-1.1989
  - 5. score=-2.4432 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=15 | semantic_rank=None | reranker_score=-2.4432

---

### ret_018

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: How can a user disable non-essential cookies on GitHub pages?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `cookie choices and controls` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=8.3045 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > What are your cookie choices and controls?` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=8.3045
  - 2. score=4.5331 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=2 | semantic_rank=2 | reranker_score=4.5331
  - 3. score=2.8288 | `GitHub Cookies` | heading `Cookies` | `Policies/privacy-policies/github-cookies.md` | lexical_rank=6 | semantic_rank=15 | reranker_score=2.8288
  - 4. score=2.2653 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=18 | semantic_rank=None | reranker_score=2.2653
  - 5. score=2.2351 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=4 | semantic_rank=10 | reranker_score=2.2351

---

### ret_019

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: What details should an authorized person provide when asking GitHub to handle a deceased user's account?
- Expected sources:
  - `GitHub Deceased User Policy` | heading contains `(path only)` | `Policies/other-site-policies/github-deceased-user-policy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=5.5491 | `GitHub Deceased User Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-deceased-user-policy.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=5.5491
  - 2. score=2.4619 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=13 | semantic_rank=4 | reranker_score=2.4619
  - 3. score=1.5822 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=None | semantic_rank=3 | reranker_score=1.5822
  - 4. score=0.9882 | `GitHub General Privacy Statement` | heading `GitHub Privacy Statement > End User Notice: Organization-Provided GitHub Accounts` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=6 | semantic_rank=None | reranker_score=0.9882
  - 5. score=0.7585 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=3 | semantic_rank=None | reranker_score=0.7585

---

### ret_020

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: How can someone remove a payment method after being locked out of their GitHub account?
- Expected sources:
  - `GitHub Account Recovery Policy` | heading contains `remove a payment method from a locked account` | `Policies/other-site-policies/github-account-recovery-policy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=7.2372 | `GitHub Account Recovery Policy` | heading `How can I remove a payment method from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=7.2372
  - 2. score=0.8628 | `GitHub Account Recovery Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=7 | semantic_rank=6 | reranker_score=0.8628
  - 3. score=-0.0019 | `GitHub Account Recovery Policy` | heading `Can I recover the contents of a user or organization account I lost access to?` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=None | semantic_rank=15 | reranker_score=-0.0019
  - 4. score=-0.4503 | `GitHub Account Recovery Policy` | heading `How can I retrieve my email from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=3 | semantic_rank=None | reranker_score=-0.4503
  - 5. score=-0.4834 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=2 | reranker_score=-0.4834

---

### ret_021

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: Which registration and confusion details are required in a GitHub trademark complaint?
- Expected sources:
  - `GitHub Trademark Policy` | heading contains `Information is Required When Reporting Trademark Policy Violations` | `Policies/content-removal-policies/github-trademark-policy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=4.8539 | `GitHub Trademark Policy` | heading `What Information is Required When Reporting Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=2 | semantic_rank=1 | reranker_score=4.8539
  - 2. score=2.2651 | `GitHub Trademark Policy` | heading `How Does GitHub Respond To Reported Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=4 | semantic_rank=2 | reranker_score=2.2651
  - 3. score=2.1822 | `GitHub Trademark Policy` | heading `How Do I Report a Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=6 | semantic_rank=3 | reranker_score=2.1822
  - 4. score=1.3139 | `GitHub Registered Developer Agreement` | heading `(document introduction)` | `Policies/github-terms/github-registered-developer-agreement.md` | lexical_rank=14 | semantic_rank=5 | reranker_score=1.3139
  - 5. score=1.0394 | `GitHub Marketplace Developer Agreement` | heading `6.	PAID APPLICATIONS OR PRODUCTS` | `Policies/github-terms/github-marketplace-developer-agreement.md` | lexical_rank=9 | semantic_rank=None | reranker_score=1.0394

---

### ret_022

- Category: `unsupported`
- Evaluation group: `unsupported`
- Query source: `question`
- Query actually used: What uptime percentage does GitHub guarantee for free personal accounts?
- Expected sources:
  - `[]` (unsupported; not scored)
- Hit/MRR: not computed
- Top-5 retrieved chunks:
  - 1. score=0.9254 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=1 | semantic_rank=5 | reranker_score=0.9254
  - 2. score=-0.2835 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=3 | reranker_score=-0.2835
  - 3. score=-0.6392 | `GitHub Sponsors Additional Terms` | heading `Terms for Sponsors > 2. Payment. > 2.2. Fees.` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=None | semantic_rank=17 | reranker_score=-0.6392
  - 4. score=-1.0336 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=12 | semantic_rank=9 | reranker_score=-1.0336
  - 5. score=-1.0845 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=6 | semantic_rank=None | reranker_score=-1.0845

---

### ret_023

- Category: `unsupported`
- Evaluation group: `unsupported`
- Query source: `question`
- Query actually used: In which exact physical data center is my specific repository stored?
- Expected sources:
  - `[]` (unsupported; not scored)
- Hit/MRR: not computed
- Top-5 retrieved chunks:
  - 1. score=-6.2922 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=5 | semantic_rank=None | reranker_score=-6.2922
  - 2. score=-9.3447 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=6 | semantic_rank=None | reranker_score=-9.3447
  - 3. score=-9.5414 | `GitHub Marketplace Developer Agreement` | heading `Addendum 1: Data Protection Addendum` | `Policies/github-terms/github-marketplace-developer-agreement.md` | lexical_rank=14 | semantic_rank=None | reranker_score=-9.5414
  - 4. score=-10.1946 | `Guidelines for Legal Requests of User Data` | heading `Submitting requests` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=None | semantic_rank=7 | reranker_score=-10.1946
  - 5. score=-10.4178 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=2 | reranker_score=-10.4178

---

### ret_024

- Category: `unsupported`
- Evaluation group: `unsupported`
- Query source: `question`
- Query actually used: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- Expected sources:
  - `[]` (unsupported; not scored)
- Hit/MRR: not computed
- Top-5 retrieved chunks:
  - 1. score=1.8594 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=2 | reranker_score=1.8594
  - 2. score=1.4025 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=1 | reranker_score=1.4025
  - 3. score=1.0154 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=11 | reranker_score=1.0154
  - 4. score=0.0662 | `GitHub Secret Scanning Partner Program Agreement` | heading `16. Term, Termination, and Survival > 16.4 Immediate Suspension` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=None | semantic_rank=9 | reranker_score=0.0662
  - 5. score=-1.1247 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=17 | reranker_score=-1.1247

---

### multi_001

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?
- Expected sources:
  - `GitHub Private Information Removal Policy` | heading contains `What About Forks?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=5.4535 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=7 | semantic_rank=1 | reranker_score=5.4535
  - 2. score=2.9898 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=11 | semantic_rank=4 | reranker_score=2.9898
  - 3. score=2.7986 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=13 | semantic_rank=3 | reranker_score=2.7986
  - 4. score=1.8093 | `Guide to Submitting a DMCA Takedown Notice` | heading `Your Complaint Must ...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md` | lexical_rank=17 | semantic_rank=None | reranker_score=1.8093
  - 5. score=1.6035 | `GitHub Private Information Removal Policy` | heading `Things to Know` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=12 | semantic_rank=19 | reranker_score=1.6035

---

### multi_002

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: Can a user appeal GitHub's decision to restrict content or disable an account for an alleged policy violation?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - `GitHub Community Guidelines` | heading contains `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Source coverage@3: 0.5000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=6.5339 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=1 | semantic_rank=2 | reranker_score=6.5339
  - 2. score=5.3981 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=4 | semantic_rank=5 | reranker_score=5.3981
  - 3. score=5.3602 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=6 | reranker_score=5.3602
  - 4. score=5.2635 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=7 | semantic_rank=3 | reranker_score=5.2635
  - 5. score=4.6480 | `GitHub Acceptable Use Policies` | heading `11. User Protection` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=10 | semantic_rank=1 | reranker_score=4.6480

---

### multi_003

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What personal data does GitHub collect automatically from a user's device or use of the services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=9.1722 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=9.1722
  - 2. score=7.1441 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=2 | semantic_rank=None | reranker_score=7.1441
  - 3. score=5.5570 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=4 | semantic_rank=4 | reranker_score=5.5570
  - 4. score=5.2340 | `GitHub General Privacy Statement` | heading `US State Specific Information > Notice of Collection of Personal Information` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=None | reranker_score=5.2340
  - 5. score=5.1459 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=6 | semantic_rank=6 | reranker_score=5.1459

---

### multi_004

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: Does GitHub allow dual-use vulnerability, malware, or exploit content when it is posted for security research?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - `GitHub Acceptable Use Policies` | heading contains `Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Source coverage@3: 1.0000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=7.6470 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=1 | semantic_rank=1 | reranker_score=7.6470
  - 2. score=4.9092 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=14 | semantic_rank=4 | reranker_score=4.9092
  - 3. score=1.7023 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=4 | semantic_rank=3 | reranker_score=1.7023
  - 4. score=1.5873 | `Coordinated Disclosure of Security Vulnerabilities` | heading `Bounty Program` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=11 | semantic_rank=None | reranker_score=1.5873
  - 5. score=0.7628 | `GitHub Child Sexual Exploitation or Abuse` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-child-sexual-exploitation-or-abuse.md` | lexical_rank=None | semantic_rank=14 | reranker_score=0.7628

---
