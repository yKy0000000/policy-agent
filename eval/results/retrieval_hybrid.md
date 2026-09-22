# Retrieval hybrid baseline

This report evaluates retrieval only. Multi-turn cases use their standalone references; unsupported cases are displayed but not scored.

## Configuration

- Embedding: `hybrid-rrf/hashing-tfidf-v4 + sentence-transformers/all-MiniLM-L6-v2`
- Index chunks / ranking depth: 655
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Index SHA-256: `672f4231d914272da061524e34b845e0d60711ccb335be531cf0df117f2580a1`
- Source match: exact `source_path`, plus case-insensitive `heading_contains` matching when non-empty.

## Overall supported-case metrics

- Cases: 25
- Hit@1: 0.4000
- Hit@3: 0.6400
- Hit@5: 0.7600
- MRR: 0.5480

## Metrics by category

### direct

- Cases: 5
- Hit@1: 0.2000
- Hit@3: 0.6000
- Hit@5: 0.8000
- MRR: 0.4452

### semantic

- Cases: 7
- Hit@1: 0.2857
- Hit@3: 0.5714
- Hit@5: 0.7143
- MRR: 0.4671

### broad

- Cases: 4
- Hit@1: 0.0000
- Hit@3: 0.2500
- Hit@5: 0.5000
- MRR: 0.1929

### specific

- Cases: 5
- Hit@1: 1.0000
- Hit@3: 1.0000
- Hit@5: 1.0000
- MRR: 1.0000

### multi_turn_oracle

- Cases: 4
- Hit@1: 0.5000
- Hit@3: 0.7500
- Hit@5: 0.7500
- MRR: 0.6083

## Multi-source coverage

- Multi-source cases: 5
- Mean coverage@3: 0.4000
- Mean coverage@5: 0.5000

- `ret_013` (3 expected): coverage@3=0.0000, coverage@5=0.0000
- `ret_015` (2 expected): coverage@3=0.0000, coverage@5=0.0000
- `ret_016` (2 expected): coverage@3=0.5000, coverage@5=0.5000
- `multi_002` (2 expected): coverage@3=1.0000, coverage@5=1.0000
- `multi_004` (2 expected): coverage@3=0.5000, coverage@5=1.0000

## Priority cases for human review

### Supported cases with Hit@5 = 0

`ret_001`, `ret_007`, `ret_008`, `ret_013`, `ret_015`, `multi_003`

### Supported cases with Hit@1 = 0 and Hit@5 = 1

`ret_003`, `ret_004`, `ret_005`, `ret_009`, `ret_011`, `ret_012`, `ret_014`, `ret_016`, `multi_001`

## Unsupported cases (not scored)

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- Top-5:
  - 1. score=0.0325 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=2 | semantic_rank=1
  - 2. score=0.0318 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=1 | semantic_rank=5
  - 3. score=0.0317 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=3
  - 4. score=0.0305 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 6. Enterprise Cloud Service Level Agreement` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=5 | semantic_rank=6
  - 5. score=0.0284 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=12 | semantic_rank=9

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- Top-5:
  - 1. score=0.0291 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=2
  - 2. score=0.0267 | `GitHub Corporate Terms of Service` | heading `D. Content Responsibility; Ownership; License Rights > 5. Contributions Under Repository License` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=18 | semantic_rank=12
  - 3. score=0.0164 | `GitHub Secret Scanning Partner Program Agreement` | heading `4. Purpose Limitation on Match Data > 4.3 Private Repository Data` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=1 | semantic_rank=None
  - 4. score=0.0164 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=1
  - 5. score=0.0161 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=2 | semantic_rank=None

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- Top-5:
  - 1. score=0.0320 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=2 | semantic_rank=3
  - 2. score=0.0318 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=1
  - 3. score=0.0310 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=4 | semantic_rank=5
  - 4. score=0.0299 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=6 | semantic_rank=8
  - 5. score=0.0294 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=3 | semantic_rank=14

## Per-case results

### ret_001

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: How old must someone be to have a GitHub account?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 7
- Reciprocal rank: 0.1429
- Top-5 retrieved chunks:
  - 1. score=0.0318 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=1 | semantic_rank=5
  - 2. score=0.0310 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=6 | semantic_rank=3
  - 3. score=0.0294 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 2. Account Requirements` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=17 | semantic_rank=1
  - 4. score=0.0276 | `GitHub Terms of Service` | heading `B. Account Terms > 2. Required Information` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=15 | semantic_rank=10
  - 5. score=0.0270 | `GitHub Terms of Service` | heading `B. Account Terms > 4. Account Security` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=16 | semantic_rank=12

---

### ret_002

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.0328 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0323 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=2 | semantic_rank=2
  - 3. score=0.0159 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=None | semantic_rank=3
  - 4. score=0.0159 | `GitHub Subprocessors` | heading `Third Party Subprocessors` | `Policies/privacy-policies/github-subprocessors.md` | lexical_rank=3 | semantic_rank=None
  - 5. score=0.0156 | `GitHub Subprocessors` | heading `Third Party Subprocessors` | `Policies/privacy-policies/github-subprocessors.md` | lexical_rank=4 | semantic_rank=None

---

### ret_003

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What is an appeal under GitHub's Appeal and Reinstatement policy?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 1
- First relevant rank: 4
- Reciprocal rank: 0.2500
- Top-5 retrieved chunks:
  - 1. score=0.0323 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=2 | semantic_rank=2
  - 2. score=0.0320 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=4 | semantic_rank=1
  - 3. score=0.0311 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=1 | semantic_rank=8
  - 4. score=0.0310 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=6 | semantic_rank=3
  - 5. score=0.0310 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=3 | semantic_rank=6

---

### ret_004

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What account information does GitHub collect when a user opens an account?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.0328 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0313 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=5 | semantic_rank=3
  - 3. score=0.0306 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=2 | semantic_rank=9
  - 4. score=0.0306 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=9 | semantic_rank=2
  - 5. score=0.0296 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=8 | semantic_rank=7

---

### ret_005

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What contact details must be included in a DMCA counter notice?
- Expected sources:
  - `Guide to Submitting a DMCA Counter Notice` | heading contains `Your Counter Notice Must` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.0328 | `Guide to Submitting a DMCA Counter Notice` | heading `How to Submit Your Counter Notice` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0313 | `Guide to Submitting a DMCA Counter Notice` | heading `Your Counter Notice Must...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=3 | semantic_rank=5
  - 3. score=0.0312 | `DMCA Takedown Policy` | heading `G. Submitting Notices` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=4 | semantic_rank=4
  - 4. score=0.0308 | `DMCA Takedown Policy` | heading `E. Transparency` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=8 | semantic_rank=2
  - 5. score=0.0301 | `Guide to Submitting a DMCA Counter Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` | lexical_rank=5 | semantic_rank=8

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
  - 1. score=0.0325 | `GitHub Hate Speech and Discrimination` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md` | lexical_rank=2 | semantic_rank=1
  - 2. score=0.0290 | `GitHub Event Code of Conduct` | heading `Code of Conduct` | `Policies/github-terms/github-event-code-of-conduct.md` | lexical_rank=4 | semantic_rank=15
  - 3. score=0.0164 | `GitHub Global Data Privacy Notice for Candidates` | heading `Addenda > Canada Addendum` | `Policies/privacy-policies/github-candidate-privacy-policy.md` | lexical_rank=1 | semantic_rank=None
  - 4. score=0.0161 | `GitHub Bullying and Harassment` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-bullying-and-harassment.md` | lexical_rank=None | semantic_rank=2
  - 5. score=0.0159 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md` | lexical_rank=None | semantic_rank=3

---

### ret_007

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: May I publish another person's home address or banking details in a repository?
- Expected sources:
  - `GitHub Doxxing and Invasion of Privacy` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 23
- Reciprocal rank: 0.0435
- Top-5 retrieved chunks:
  - 1. score=0.0320 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=4 | semantic_rank=1
  - 2. score=0.0284 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=7 | semantic_rank=14
  - 3. score=0.0284 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=12 | semantic_rank=9
  - 4. score=0.0279 | `GitHub General Privacy Statement` | heading `Your Privacy Rights` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=16 | semantic_rank=8
  - 5. score=0.0164 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=1 | semantic_rank=None

---

### ret_008

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub report a researcher to law enforcement for an accidental, good-faith violation during authorized vulnerability research?
- Expected sources:
  - `GitHub Bug Bounty Program Legal Safe Harbor` | heading contains `Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 7
- Reciprocal rank: 0.1429
- Top-5 retrieved chunks:
  - 1. score=0.0320 | `GitHub Research Program Terms` | heading `H. Miscellaneous > 1. Governing Law` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=4 | semantic_rank=1
  - 2. score=0.0303 | `Guidelines for Legal Requests of User Data` | heading `Requests from foreign law enforcement` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=5 | semantic_rank=7
  - 3. score=0.0299 | `GitHub Research Program Terms` | heading `G. Limitation of Liability` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=6 | semantic_rank=8
  - 4. score=0.0288 | `GitHub Community Code of Conduct` | heading `Enforcement > _What GitHub Community Participants Can Do_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=16 | semantic_rank=4
  - 5. score=0.0269 | `GitHub Research Program Terms` | heading `H. Miscellaneous > 3. Severability, No Waiver, and Survival` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=13 | semantic_rank=16

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
  - 1. score=0.0309 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=9 | semantic_rank=1
  - 2. score=0.0308 | `GitHub and Trade Controls` | heading `Frequently asked questions > How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=8 | semantic_rank=2
  - 3. score=0.0289 | `GitHub and Trade Controls` | heading `(document introduction)` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=17 | semantic_rank=3
  - 4. score=0.0288 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users’ private repositories be made public?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=11 | semantic_rank=8
  - 5. score=0.0287 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=14 | semantic_rank=6

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
  - 1. score=0.0325 | `GitHub Terms of Service` | heading `D. User-Generated Content > 8. Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=2 | semantic_rank=1
  - 2. score=0.0306 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=4 | semantic_rank=7
  - 3. score=0.0292 | `GitHub Corporate Terms of Service` | heading `I. Affiliates` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=8 | semantic_rank=9
  - 4. score=0.0267 | `GitHub Pre-release License Terms` | heading `14. Confidentiality.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=13 | semantic_rank=17
  - 5. score=0.0164 | `DMCA Takedown Policy` | heading `D. What If I Inadvertently Missed the Window to Make Changes?` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=1 | semantic_rank=None

---

### ret_011

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub warn an account owner before handing their information to investigators?
- Expected sources:
  - `Guidelines for Legal Requests of User Data` | heading contains `notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 1
- First relevant rank: 4
- Reciprocal rank: 0.2500
- Top-5 retrieved chunks:
  - 1. score=0.0318 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=2 | semantic_rank=4
  - 2. score=0.0305 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=11 | semantic_rank=1
  - 3. score=0.0286 | `GitHub Terms of Service` | heading `B. Account Terms > 4. Account Security` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=10 | semantic_rank=10
  - 4. score=0.0164 | `Guidelines for Legal Requests of User Data` | heading `We will notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=1 | semantic_rank=None
  - 5. score=0.0161 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=2

---

### ret_012

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Is code used to study vulnerabilities automatically removed just because it could also be misused?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.0320 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=1 | semantic_rank=4
  - 2. score=0.0283 | `GitHub Bug Bounty Program Legal Safe Harbor` | heading `1. Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` | lexical_rank=15 | semantic_rank=7
  - 3. score=0.0164 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=None | semantic_rank=1
  - 4. score=0.0161 | `Coordinated Disclosure of Security Vulnerabilities` | heading `Bounty Program` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=2 | semantic_rank=None
  - 5. score=0.0161 | `GitHub Secret Scanning Partner Program Agreement` | heading `(document introduction)` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=None | semantic_rank=2

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
  - 1. score=0.0302 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 3. Account Security` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=3 | semantic_rank=10
  - 2. score=0.0296 | `GitHub Terms of Service` | heading `B. Account Terms > 4. Account Security` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=8 | semantic_rank=7
  - 3. score=0.0293 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=2 | semantic_rank=16
  - 4. score=0.0288 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=11 | semantic_rank=8
  - 5. score=0.0278 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 1. Account Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=10 | semantic_rank=14

---

### ret_014

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: What information does GitHub gather about people who use its services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 1
- First relevant rank: 5
- Reciprocal rank: 0.2000
- Top-5 retrieved chunks:
  - 1. score=0.0315 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=3 | semantic_rank=4
  - 2. score=0.0290 | `GitHub General Privacy Statement` | heading `US State Specific Information > Notice of Collection of Personal Information` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=16 | semantic_rank=3
  - 3. score=0.0289 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies?` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=6 | semantic_rank=13
  - 4. score=0.0164 | `GitHub General Privacy Statement` | heading `Information for Minors` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=None
  - 5. score=0.0164 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=None | semantic_rank=1

---

### ret_015

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: What kinds of behavior or material are not allowed on GitHub?
- Expected sources:
  - `GitHub Acceptable Use Policies` | heading contains `User Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - `GitHub Acceptable Use Policies` | heading contains `Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 14
- Reciprocal rank: 0.0714
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=0.0303 | `GitHub Disrupting the Experience of Other Users` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md` | lexical_rank=7 | semantic_rank=5
  - 2. score=0.0282 | `GitHub Community Code of Conduct` | heading `Legal Notices` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=13 | semantic_rank=9
  - 3. score=0.0164 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md` | lexical_rank=1 | semantic_rank=None
  - 4. score=0.0164 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=None | semantic_rank=1
  - 5. score=0.0161 | `GitHub Event Code of Conduct` | heading `Code of Conduct` | `Policies/github-terms/github-event-code-of-conduct.md` | lexical_rank=2 | semantic_rank=None

---

### ret_016

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: How does GitHub respond when a government or law-enforcement body asks it to remove content or disclose user data?
- Expected sources:
  - `GitHub Government Takedown Policy` | heading contains `complete takedown request from a government` | `Policies/other-site-policies/github-government-takedown-policy.md`
  - `Guidelines for Legal Requests of User Data` | heading contains `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Source coverage@3: 0.5000
- Source coverage@5: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.0320 | `GitHub Government Takedown Policy` | heading `What is this?` | `Policies/other-site-policies/github-government-takedown-policy.md` | lexical_rank=2 | semantic_rank=3
  - 2. score=0.0312 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=4 | semantic_rank=4
  - 3. score=0.0286 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=20 | semantic_rank=2
  - 4. score=0.0284 | `GitHub Global Data Privacy Notice for Candidates` | heading `Overview > How and Why We Disclose Personal Data` | `Policies/privacy-policies/github-candidate-privacy-policy.md` | lexical_rank=13 | semantic_rank=8
  - 5. score=0.0273 | `GitHub General Privacy Statement` | heading `US State Specific Information > California > Removal of Content` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=18 | semantic_rank=9

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
  - 1. score=0.0328 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0320 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md` | lexical_rank=3 | semantic_rank=2
  - 3. score=0.0308 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=4 | semantic_rank=6
  - 4. score=0.0303 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=8 | semantic_rank=4
  - 5. score=0.0286 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=2 | semantic_rank=20

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
  - 1. score=0.0328 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > What are your cookie choices and controls?` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0323 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=2 | semantic_rank=2
  - 3. score=0.0315 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies?` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=3 | semantic_rank=4
  - 4. score=0.0313 | `GitHub Cookies` | heading `Cookies` | `Policies/privacy-policies/github-cookies.md` | lexical_rank=5 | semantic_rank=3
  - 5. score=0.0299 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=4 | semantic_rank=10

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
  - 1. score=0.0328 | `GitHub Deceased User Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-deceased-user-policy.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0311 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=7 | semantic_rank=2
  - 3. score=0.0293 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | lexical_rank=13 | semantic_rank=4
  - 4. score=0.0279 | `GitHub Corporate Terms of Service` | heading `C. Compliance with Laws; Acceptable Use; Privacy > 3. Privacy` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=8 | semantic_rank=16
  - 5. score=0.0267 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=11 | semantic_rank=19

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
  - 1. score=0.0328 | `GitHub Account Recovery Policy` | heading `How can I remove a payment method from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0301 | `GitHub Account Recovery Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-account-recovery-policy.md` | lexical_rank=7 | semantic_rank=6
  - 3. score=0.0275 | `GitHub Terms of Service` | heading `L. Payment > 5. Responsibility for Payment` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=9 | semantic_rank=17
  - 4. score=0.0161 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 3. Financial Terms. > 3.4. Payment Method.` | `Policies/github-terms/github-sponsors-additional-terms.md` | lexical_rank=2 | semantic_rank=None
  - 5. score=0.0161 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=None | semantic_rank=2

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
  - 1. score=0.0325 | `GitHub Trademark Policy` | heading `What Information is Required When Reporting Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=2 | semantic_rank=1
  - 2. score=0.0320 | `GitHub Username Policy` | heading `Trademark Policy` | `Policies/other-site-policies/github-username-policy.md` | lexical_rank=1 | semantic_rank=4
  - 3. score=0.0318 | `GitHub Trademark Policy` | heading `How Does GitHub Respond To Reported Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=4 | semantic_rank=2
  - 4. score=0.0310 | `GitHub Trademark Policy` | heading `How Do I Report a Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md` | lexical_rank=6 | semantic_rank=3
  - 5. score=0.0296 | `Submitting content removal requests` | heading `GitHub Trademark Policy` | `Policies/content-removal-policies/submitting-content-removal-requests.md` | lexical_rank=8 | semantic_rank=7

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
  - 1. score=0.0325 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=2 | semantic_rank=1
  - 2. score=0.0318 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md` | lexical_rank=1 | semantic_rank=5
  - 3. score=0.0317 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md` | lexical_rank=3 | semantic_rank=3
  - 4. score=0.0305 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 6. Enterprise Cloud Service Level Agreement` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=5 | semantic_rank=6
  - 5. score=0.0284 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md` | lexical_rank=12 | semantic_rank=9

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
  - 1. score=0.0291 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=17 | semantic_rank=2
  - 2. score=0.0267 | `GitHub Corporate Terms of Service` | heading `D. Content Responsibility; Ownership; License Rights > 5. Contributions Under Repository License` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=18 | semantic_rank=12
  - 3. score=0.0164 | `GitHub Secret Scanning Partner Program Agreement` | heading `4. Purpose Limitation on Match Data > 4.3 Private Repository Data` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md` | lexical_rank=1 | semantic_rank=None
  - 4. score=0.0164 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md` | lexical_rank=None | semantic_rank=1
  - 5. score=0.0161 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=2 | semantic_rank=None

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
  - 1. score=0.0320 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=2 | semantic_rank=3
  - 2. score=0.0318 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=1
  - 3. score=0.0310 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=4 | semantic_rank=5
  - 4. score=0.0299 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=6 | semantic_rank=8
  - 5. score=0.0294 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=3 | semantic_rank=14

---

### multi_001

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?
- Expected sources:
  - `GitHub Private Information Removal Policy` | heading contains `What About Forks?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.0325 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=1 | semantic_rank=2
  - 2. score=0.0315 | `GitHub Private Information Removal Policy` | heading `Disputes` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=2 | semantic_rank=5
  - 3. score=0.0313 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=7 | semantic_rank=1
  - 4. score=0.0305 | `GitHub Private Information Removal Policy` | heading `Sending A Private Information Removal Request` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=5 | semantic_rank=6
  - 5. score=0.0301 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md` | lexical_rank=4 | semantic_rank=9

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
- Source coverage@3: 1.0000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.0325 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=1 | semantic_rank=2
  - 2. score=0.0310 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=4 | semantic_rank=5
  - 3. score=0.0308 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md` | lexical_rank=7 | semantic_rank=3
  - 4. score=0.0307 | `GitHub Acceptable Use Policies` | heading `11. User Protection` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=10 | semantic_rank=1
  - 5. score=0.0305 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | lexical_rank=5 | semantic_rank=6

---

### multi_003

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What personal data does GitHub collect automatically from a user's device or use of the services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 10
- Reciprocal rank: 0.1000
- Top-5 retrieved chunks:
  - 1. score=0.0328 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0317 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=3 | semantic_rank=3
  - 3. score=0.0312 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=4 | semantic_rank=4
  - 4. score=0.0303 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=6 | semantic_rank=6
  - 5. score=0.0288 | `GitHub General Privacy Statement` | heading `Processing Purposes: How We Use Your Personal Data` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=19 | semantic_rank=2

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
- Source coverage@3: 0.5000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.0328 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | lexical_rank=1 | semantic_rank=1
  - 2. score=0.0315 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md` | lexical_rank=5 | semantic_rank=2
  - 3. score=0.0315 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md` | lexical_rank=4 | semantic_rank=3
  - 4. score=0.0303 | `GitHub Research Program Terms` | heading `A. Your Feedback` | `Policies/github-terms/github-research-program-terms.md` | lexical_rank=7 | semantic_rank=5
  - 5. score=0.0291 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | lexical_rank=14 | semantic_rank=4

---
