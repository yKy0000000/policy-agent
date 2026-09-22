# Retrieval lexical baseline

This report evaluates retrieval only. Multi-turn cases use their standalone references; unsupported cases are displayed but not scored.

## Configuration

- Embedding: `local/hashing-tfidf-v4`
- Index chunks / ranking depth: 655
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Index SHA-256: `dc73a4725ff7361ebd0c28d5b9bef93a433ae6f2b6cd9a65723676e666e6ee82`
- Source match: exact `source_path`, plus case-insensitive `heading_contains` matching when non-empty.

## Overall supported-case metrics

- Cases: 25
- Hit@1: 0.4000
- Hit@3: 0.6800
- Hit@5: 0.6800
- MRR: 0.5569

## Metrics by category

### direct

- Cases: 5
- Hit@1: 0.2000
- Hit@3: 0.6000
- Hit@5: 0.6000
- MRR: 0.4069

### semantic

- Cases: 7
- Hit@1: 0.2857
- Hit@3: 0.5714
- Hit@5: 0.5714
- MRR: 0.4536

### broad

- Cases: 4
- Hit@1: 0.2500
- Hit@3: 0.5000
- Hit@5: 0.5000
- MRR: 0.3928

### specific

- Cases: 5
- Hit@1: 0.8000
- Hit@3: 1.0000
- Hit@5: 1.0000
- MRR: 0.9000

### multi_turn_oracle

- Cases: 4
- Hit@1: 0.5000
- Hit@3: 0.7500
- Hit@5: 0.7500
- MRR: 0.6607

## Multi-source coverage

- Multi-source cases: 5
- Mean coverage@3: 0.2667
- Mean coverage@5: 0.2667

- `ret_013` (3 expected): coverage@3=0.3333, coverage@5=0.3333
- `ret_015` (2 expected): coverage@3=0.0000, coverage@5=0.0000
- `ret_016` (2 expected): coverage@3=0.0000, coverage@5=0.0000
- `multi_002` (2 expected): coverage@3=0.5000, coverage@5=0.5000
- `multi_004` (2 expected): coverage@3=0.5000, coverage@5=0.5000

## Priority cases for human review

### Supported cases with Hit@5 = 0

`ret_001`, `ret_003`, `ret_007`, `ret_009`, `ret_012`, `ret_015`, `ret_016`, `multi_001`

### Supported cases with Hit@1 = 0 and Hit@5 = 1

`ret_004`, `ret_005`, `ret_006`, `ret_010`, `ret_014`, `ret_021`, `multi_003`

## Unsupported cases (not scored)

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- Top-5:
  - 1. score=0.2339 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md`
  - 2. score=0.0824 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.0677 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.0579 | `GitHub General Privacy Statement` | heading `Data Privacy Framework (DPF)` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.0570 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 6. Enterprise Cloud Service Level Agreement` | `Policies/github-terms/github-corporate-terms-of-service.md`

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- Top-5:
  - 1. score=0.0702 | `GitHub Secret Scanning Partner Program Agreement` | heading `4. Purpose Limitation on Match Data > 4.3 Private Repository Data` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md`
  - 2. score=0.0580 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 3. score=0.0572 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 4. score=0.0552 | `GitHub Account Recovery Policy` | heading `How can I retrieve my email from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 5. score=0.0522 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- Top-5:
  - 1. score=0.1052 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.0938 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 3. score=0.0845 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 4. score=0.0823 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 5. score=0.0808 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

## Per-case results

### ret_001

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: How old must someone be to have a GitHub account?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 29
- Reciprocal rank: 0.0345
- Top-5 retrieved chunks:
  - 1. score=0.0780 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.0780 | `GitHub Community Guidelines` | heading `What happens if someone violates GitHub's policies?` | `Policies/github-terms/github-community-guidelines.md`
  - 3. score=0.0645 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 1. Acceptable Use. > 1.2. GitHub Sponsors Matching Fund > 1.2.1. Matching Fund Terms.` | `Policies/github-terms/github-sponsors-additional-terms.md`
  - 4. score=0.0640 | `GitHub Community Guidelines` | heading `What if something or someone offends you?` | `Policies/github-terms/github-community-guidelines.md`
  - 5. score=0.0522 | `GitHub Corporate Terms of Service` | heading `J. Payment > 3. Authorization` | `Policies/github-terms/github-corporate-terms-of-service.md`

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
  - 1. score=0.1459 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - 2. score=0.1435 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 3. score=0.0800 | `GitHub Subprocessors` | heading `Third Party Subprocessors` | `Policies/privacy-policies/github-subprocessors.md`
  - 4. score=0.0498 | `GitHub Subprocessors` | heading `Third Party Subprocessors` | `Policies/privacy-policies/github-subprocessors.md`
  - 5. score=0.0477 | `GitHub SIRT description RFC 2350` | heading `3. Charter > 3.1 Mission Statement` | `Policies/security-policies/github-sirt-description-rfc-2350.md`

---

### ret_003

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What is an appeal under GitHub's Appeal and Reinstatement policy?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 6
- Reciprocal rank: 0.1667
- Top-5 retrieved chunks:
  - 1. score=0.4879 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.4265 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 3. score=0.3685 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 4. score=0.3606 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 5. score=0.3570 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

---

### ret_004

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What account information does GitHub collect when a user opens an account?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.1206 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.1147 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.0954 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md`
  - 4. score=0.0922 | `GitHub Terms of Service` | heading `B. Account Terms > 2. Required Information` | `Policies/github-terms/github-terms-of-service.md`
  - 5. score=0.0903 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`

---

### ret_005

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What contact details must be included in a DMCA counter notice?
- Expected sources:
  - `Guide to Submitting a DMCA Counter Notice` | heading contains `Your Counter Notice Must` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.2616 | `Guide to Submitting a DMCA Counter Notice` | heading `How to Submit Your Counter Notice` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
  - 2. score=0.2213 | `Guide to Submitting a DMCA Counter Notice` | heading `(document introduction)` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
  - 3. score=0.2185 | `Guide to Submitting a DMCA Counter Notice` | heading `Your Counter Notice Must...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
  - 4. score=0.2030 | `DMCA Takedown Policy` | heading `G. Submitting Notices` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 5. score=0.1667 | `Guide to Submitting a DMCA Counter Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`

---

### ret_006

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Can someone target a person with degrading language because of their identity or background?
- Expected sources:
  - `GitHub Hate Speech and Discrimination` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.0603 | `GitHub Global Data Privacy Notice for Candidates` | heading `Addenda > Canada Addendum` | `Policies/privacy-policies/github-candidate-privacy-policy.md`
  - 2. score=0.0577 | `GitHub Hate Speech and Discrimination` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md`
  - 3. score=0.0465 | `GitHub Terms of Service` | heading `Q. Release and Indemnification` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.0465 | `GitHub Event Code of Conduct` | heading `Code of Conduct` | `Policies/github-terms/github-event-code-of-conduct.md`
  - 5. score=0.0460 | `GitHub Terms of Service` | heading `(document introduction)` | `Policies/github-terms/github-terms-of-service.md`

---

### ret_007

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: May I publish another person's home address or banking details in a repository?
- Expected sources:
  - `GitHub Doxxing and Invasion of Privacy` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 42
- Reciprocal rank: 0.0238
- Top-5 retrieved chunks:
  - 1. score=0.0793 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 2. score=0.0772 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 3. score=0.0643 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md`
  - 4. score=0.0605 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 5. score=0.0579 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`

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
  - 1. score=0.1331 | `GitHub Bug Bounty Program Legal Safe Harbor` | heading `1. Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
  - 2. score=0.0811 | `GitHub Research Program Terms` | heading `(document introduction)` | `Policies/github-terms/github-research-program-terms.md`
  - 3. score=0.0802 | `GitHub Research Program Terms` | heading `C. Reservation of Rights` | `Policies/github-terms/github-research-program-terms.md`
  - 4. score=0.0788 | `GitHub Research Program Terms` | heading `H. Miscellaneous > 1. Governing Law` | `Policies/github-terms/github-research-program-terms.md`
  - 5. score=0.0780 | `Guidelines for Legal Requests of User Data` | heading `Requests from foreign law enforcement` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

---

### ret_009

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Can a company connected to a sanctioned region continue using private repositories and paid GitHub features?
- Expected sources:
  - `GitHub and Trade Controls` | heading contains `How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 8
- Reciprocal rank: 0.1250
- Top-5 retrieved chunks:
  - 1. score=0.1585 | `GitHub Terms of Service` | heading `E. Private Repositories > 1. Control of Private Repositories` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.1531 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.1331 | `GitHub Terms of Service` | heading `E. Private Repositories` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.1323 | `GitHub Terms of Service` | heading `E. Private Repositories > 2. Confidentiality of Private Repositories` | `Policies/github-terms/github-terms-of-service.md`
  - 5. score=0.1293 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md`

---

### ret_010

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: If I publish code in an open repository, am I directing GitHub to make it available to everyone online?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.0859 | `DMCA Takedown Policy` | heading `D. What If I Inadvertently Missed the Window to Make Changes?` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 2. score=0.0823 | `GitHub Terms of Service` | heading `D. User-Generated Content > 8. Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.0544 | `GitHub Community Code of Conduct` | heading `Pledge` | `Policies/github-terms/github-community-code-of-conduct.md`
  - 4. score=0.0458 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 5. score=0.0416 | `GitHub Open Source Applications Terms and Conditions` | heading `(document introduction)` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md`

---

### ret_011

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub warn an account owner before handing their information to investigators?
- Expected sources:
  - `Guidelines for Legal Requests of User Data` | heading contains `notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.0747 | `Guidelines for Legal Requests of User Data` | heading `We will notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 2. score=0.0630 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 3. score=0.0518 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.0490 | `GitHub Terms of Service` | heading `B. Account Terms > 1. Account Controls` | `Policies/github-terms/github-terms-of-service.md`
  - 5. score=0.0445 | `GitHub Terms of Service` | heading `B. Account Terms > 2. Required Information` | `Policies/github-terms/github-terms-of-service.md`

---

### ret_012

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Is code used to study vulnerabilities automatically removed just because it could also be misused?
- Expected sources:
  - `GitHub Active Malware or Exploits` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 38
- Reciprocal rank: 0.0263
- Top-5 retrieved chunks:
  - 1. score=0.0827 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md`
  - 2. score=0.0594 | `Coordinated Disclosure of Security Vulnerabilities` | heading `Bounty Program` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md`
  - 3. score=0.0530 | `Guide to Submitting a DMCA Counter Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
  - 4. score=0.0525 | `GitHub Pre-release License Terms` | heading `9. No Warranties.` | `Policies/github-terms/github-pre-release-license-terms.md`
  - 5. score=0.0469 | `Guide to Submitting a DMCA Takedown Notice` | heading `Before You Start` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`

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
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Source coverage@3: 0.3333
- Source coverage@5: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.0620 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.0499 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.0450 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 3. Account Security` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 4. score=0.0408 | `GitHub Account Recovery Policy` | heading `How can I retrieve my email from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 5. score=0.0398 | `GitHub Account Recovery Policy` | heading `How can I remove a payment method from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`

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
  - 1. score=0.0906 | `GitHub General Privacy Statement` | heading `Information for Minors` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.0671 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.0581 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 4. score=0.0574 | `GitHub Corporate Terms of Service` | heading `T. Miscellaneous > 7. Publicity` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.0462 | `GitHub Global Data Privacy Notice for Candidates` | heading `Overview > Use of Cookies and Web Beacons` | `Policies/privacy-policies/github-candidate-privacy-policy.md`

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
- First relevant rank: 227
- Reciprocal rank: 0.0044
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=0.1100 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md`
  - 2. score=0.0677 | `GitHub Event Code of Conduct` | heading `Code of Conduct` | `Policies/github-terms/github-event-code-of-conduct.md`
  - 3. score=0.0641 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 4. score=0.0615 | `GitHub Copilot Extension Developer Policy` | heading `10. Export Control` | `Policies/github-terms/github-copilot-extension-developer-policy.md`
  - 5. score=0.0596 | `GitHub Community Code of Conduct` | heading `Enforcement > _What GitHub Community Participants Can Do_` | `Policies/github-terms/github-community-code-of-conduct.md`

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
- First relevant rank: 15
- Reciprocal rank: 0.0667
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=0.1446 | `GitHub Terms of Service` | heading `D. User-Generated Content > 2. GitHub May Remove Content` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.1083 | `GitHub Government Takedown Policy` | heading `What is this?` | `Policies/other-site-policies/github-government-takedown-policy.md`
  - 3. score=0.0886 | `Guidelines for Legal Requests of User Data` | heading `Questions` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 4. score=0.0858 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 5. score=0.0835 | `GitHub Terms of Service` | heading `D. User-Generated Content > 3. Ownership and License Grants` | `Policies/github-terms/github-terms-of-service.md`

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
  - 1. score=0.1713 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 2. score=0.1329 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 3. score=0.1258 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 4. score=0.1230 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 5. score=0.0980 | `Guide to Submitting a DMCA Takedown Notice` | heading `Your Complaint Must ...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`

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
  - 1. score=0.1852 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > What are your cookie choices and controls?` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.1736 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.1255 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies?` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.1178 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.1175 | `GitHub Cookies` | heading `Cookies` | `Policies/privacy-policies/github-cookies.md`

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
  - 1. score=0.1467 | `GitHub Deceased User Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-deceased-user-policy.md`
  - 2. score=0.0704 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 3. score=0.0614 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.0595 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 2. Account Requirements` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.0593 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md`

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
  - 1. score=0.4432 | `GitHub Account Recovery Policy` | heading `How can I remove a payment method from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 2. score=0.1768 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 3. Financial Terms. > 3.4. Payment Method.` | `Policies/github-terms/github-sponsors-additional-terms.md`
  - 3. score=0.1227 | `GitHub Account Recovery Policy` | heading `How can I retrieve my email from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 4. score=0.0828 | `GitHub Terms of Service` | heading `L. Payment > 4. Authorization` | `Policies/github-terms/github-terms-of-service.md`
  - 5. score=0.0801 | `GitHub Corporate Terms of Service` | heading `J. Payment > 3. Authorization` | `Policies/github-terms/github-corporate-terms-of-service.md`

---

### ret_021

- Category: `specific`
- Evaluation group: `specific`
- Query source: `question`
- Query actually used: Which registration and confusion details are required in a GitHub trademark complaint?
- Expected sources:
  - `GitHub Trademark Policy` | heading contains `Information is Required When Reporting Trademark Policy Violations` | `Policies/content-removal-policies/github-trademark-policy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.1420 | `GitHub Username Policy` | heading `Trademark Policy` | `Policies/other-site-policies/github-username-policy.md`
  - 2. score=0.1409 | `GitHub Trademark Policy` | heading `What Information is Required When Reporting Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 3. score=0.1201 | `GitHub Trademark Policy` | heading `What is a GitHub Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 4. score=0.1181 | `GitHub Trademark Policy` | heading `How Does GitHub Respond To Reported Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 5. score=0.1156 | `GitHub Sponsors Additional Terms` | heading `Terms For Sponsored Developer > 2. Sponsored Developer Obligations. > 2.2. Registration.` | `Policies/github-terms/github-sponsors-additional-terms.md`

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
  - 1. score=0.2339 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md`
  - 2. score=0.0824 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.0677 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.0579 | `GitHub General Privacy Statement` | heading `Data Privacy Framework (DPF)` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.0570 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 6. Enterprise Cloud Service Level Agreement` | `Policies/github-terms/github-corporate-terms-of-service.md`

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
  - 1. score=0.0702 | `GitHub Secret Scanning Partner Program Agreement` | heading `4. Purpose Limitation on Match Data > 4.3 Private Repository Data` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md`
  - 2. score=0.0580 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 3. score=0.0572 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 4. score=0.0552 | `GitHub Account Recovery Policy` | heading `How can I retrieve my email from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 5. score=0.0522 | `Guidelines for Legal Requests of User Data` | heading `GitHub terminology` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

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
  - 1. score=0.1052 | `GitHub Appeal and Reinstatement` | heading `Transparency` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.0938 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 3. score=0.0845 | `GitHub Appeal and Reinstatement` | heading `Appeal and Reinstatement` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 4. score=0.0823 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 5. score=0.0808 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

---

### multi_001

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?
- Expected sources:
  - `GitHub Private Information Removal Policy` | heading contains `What About Forks?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 7
- Reciprocal rank: 0.1429
- Top-5 retrieved chunks:
  - 1. score=0.3040 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 2. score=0.2873 | `GitHub Private Information Removal Policy` | heading `Disputes` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 3. score=0.2694 | `Submitting content removal requests` | heading `GitHub Private Information Removal Policy` | `Policies/content-removal-policies/submitting-content-removal-requests.md`
  - 4. score=0.2640 | `GitHub Private Information Removal Policy` | heading `What is Private Information?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 5. score=0.2551 | `GitHub Private Information Removal Policy` | heading `Sending A Private Information Removal Request` | `Policies/content-removal-policies/github-private-information-removal-policy.md`

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
- Source coverage@5: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.1933 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.1510 | `GitHub Trademark Policy` | heading `What is a GitHub Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 3. score=0.1442 | `GitHub Trademark Policy` | heading `What is not a GitHub Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 4. score=0.1379 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 5. score=0.1358 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

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
  - 1. score=0.2411 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.2188 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.1166 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.1109 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.0907 | `GitHub Global Data Privacy Notice for Candidates` | heading `Addenda > Canada Addendum` | `Policies/privacy-policies/github-candidate-privacy-policy.md`

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
- Source coverage@5: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.1677 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - 2. score=0.0952 | `GitHub Terms of Service` | heading `B. Account Terms > 4. Account Security` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.0939 | `GitHub Bug Bounty Program Legal Safe Harbor` | heading `1. Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
  - 4. score=0.0914 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md`
  - 5. score=0.0810 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md`

---
