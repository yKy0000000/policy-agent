# Retrieval semantic baseline

This report evaluates retrieval only. Multi-turn cases use their standalone references; unsupported cases are displayed but not scored.

## Configuration

- Embedding: `sentence-transformers/sentence-transformers/all-MiniLM-L6-v2`
- Index chunks / ranking depth: 655
- Candidate SHA-256: `25b5fdb561d3d2a338f450099dc4980eb9ba0bbb8e8fc0ae58c1d2b9844942cc`
- Index SHA-256: `672f4231d914272da061524e34b845e0d60711ccb335be531cf0df117f2580a1`
- Source match: exact `source_path`, plus case-insensitive `heading_contains` matching when non-empty.

## Overall supported-case metrics

- Cases: 25
- Hit@1: 0.4800
- Hit@3: 0.7200
- Hit@5: 0.7600
- MRR: 0.6163

## Metrics by category

### direct

- Cases: 5
- Hit@1: 0.2000
- Hit@3: 0.6000
- Hit@5: 0.8000
- MRR: 0.4289

### semantic

- Cases: 7
- Hit@1: 0.4286
- Hit@3: 0.5714
- Hit@5: 0.5714
- MRR: 0.5152

### broad

- Cases: 4
- Hit@1: 0.2500
- Hit@3: 0.7500
- Hit@5: 0.7500
- MRR: 0.5357

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
- MRR: 0.6284

## Multi-source coverage

- Multi-source cases: 5
- Mean coverage@3: 0.4667
- Mean coverage@5: 0.5667

- `ret_013` (3 expected): coverage@3=0.3333, coverage@5=0.3333
- `ret_015` (2 expected): coverage@3=0.0000, coverage@5=0.0000
- `ret_016` (2 expected): coverage@3=0.5000, coverage@5=0.5000
- `multi_002` (2 expected): coverage@3=1.0000, coverage@5=1.0000
- `multi_004` (2 expected): coverage@3=0.5000, coverage@5=1.0000

## Priority cases for human review

### Supported cases with Hit@5 = 0

`ret_004`, `ret_007`, `ret_008`, `ret_011`, `ret_015`, `multi_003`

### Supported cases with Hit@1 = 0 and Hit@5 = 1

`ret_001`, `ret_003`, `ret_005`, `ret_009`, `ret_013`, `ret_016`, `multi_002`

## Unsupported cases (not scored)

### ret_022

- Query: What uptime percentage does GitHub guarantee for free personal accounts?
- Top-5:
  - 1. score=0.6583 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.6298 | `GitHub Terms of Service` | heading `L. Payment > 2. Upgrades, Downgrades, and Changes` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.6271 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.6232 | `GitHub Corporate Terms of Service` | heading `S. Support` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.6195 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md`

### ret_023

- Query: In which exact physical data center is my specific repository stored?
- Top-5:
  - 1. score=0.3478 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 2. score=0.3249 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.3206 | `GitHub Subprocessors` | heading `(document introduction)` | `Policies/privacy-policies/github-subprocessors.md`
  - 4. score=0.3164 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 2. Confidentiality` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.3112 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`

### ret_024

- Query: What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- Top-5:
  - 1. score=0.6706 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.6658 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 3. score=0.6303 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 4. score=0.6287 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 5. Suspension` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.6228 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

## Per-case results

### ret_001

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: How old must someone be to have a GitHub account?
- Expected sources:
  - `GitHub Terms of Service` | heading contains `Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.7435 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 2. Account Requirements` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 2. score=0.6996 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.6991 | `GitHub Community Code of Conduct` | heading `Standards > _What is not Allowed_` | `Policies/github-terms/github-community-code-of-conduct.md`
  - 4. score=0.6944 | `GitHub General Privacy Statement` | heading `Information for Minors` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.6597 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`

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
  - 1. score=0.7105 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - 2. score=0.6852 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 3. score=0.6495 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.5962 | `GitHub Corporate Terms of Service` | heading `T. Miscellaneous > 8. Force Majeure` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.5951 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`

---

### ret_003

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What is an appeal under GitHub's Appeal and Reinstatement policy?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 3
- Reciprocal rank: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.8191 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.8175 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 3. score=0.8074 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 4. score=0.8034 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 5. score=0.7868 | `GitHub Appeal and Reinstatement` | heading `How this works > Reinstatements` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

---

### ret_004

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What account information does GitHub collect when a user opens an account?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 9
- Reciprocal rank: 0.1111
- Top-5 retrieved chunks:
  - 1. score=0.7018 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.6916 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 3. score=0.6894 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.6825 | `GitHub General Privacy Statement` | heading `Security and Retention` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.6806 | `GitHub Terms of Service` | heading `B. Account Terms > 1. Account Controls` | `Policies/github-terms/github-terms-of-service.md`

---

### ret_005

- Category: `direct`
- Evaluation group: `direct`
- Query source: `question`
- Query actually used: What contact details must be included in a DMCA counter notice?
- Expected sources:
  - `Guide to Submitting a DMCA Counter Notice` | heading contains `Your Counter Notice Must` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 1
- First relevant rank: 5
- Reciprocal rank: 0.2000
- Top-5 retrieved chunks:
  - 1. score=0.6514 | `Guide to Submitting a DMCA Counter Notice` | heading `How to Submit Your Counter Notice` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
  - 2. score=0.6218 | `DMCA Takedown Policy` | heading `E. Transparency` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 3. score=0.5804 | `Guide to Submitting a DMCA Takedown Notice` | heading `How to Submit Your Complaint` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
  - 4. score=0.5498 | `DMCA Takedown Policy` | heading `G. Submitting Notices` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 5. score=0.5323 | `Guide to Submitting a DMCA Counter Notice` | heading `Your Counter Notice Must...` | `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`

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
  - 1. score=0.3375 | `GitHub Hate Speech and Discrimination` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-hate-speech-and-discrimination.md`
  - 2. score=0.2589 | `GitHub Bullying and Harassment` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-bullying-and-harassment.md`
  - 3. score=0.2422 | `GitHub Impersonation` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-impersonation.md`
  - 4. score=0.2177 | `GitHub Acceptable Use Policies` | heading `2. User Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 5. score=0.2165 | `GitHub Threats of Violence and Gratuitously Violent Content` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-threats-of-violence-and-gratuitously-violent-content.md`

---

### ret_007

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: May I publish another person's home address or banking details in a repository?
- Expected sources:
  - `GitHub Doxxing and Invasion of Privacy` | heading contains `(path only)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 13
- Reciprocal rank: 0.0769
- Top-5 retrieved chunks:
  - 1. score=0.5173 | `Guidelines for Legal Requests of User Data` | heading `User data on GitHub.com` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 2. score=0.4884 | `GitHub Global Data Privacy Notice for Candidates` | heading `Addenda > California Addendum` | `Policies/privacy-policies/github-candidate-privacy-policy.md`
  - 3. score=0.4859 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 4. score=0.4616 | `GitHub General Privacy Statement` | heading `US State Specific Information` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.4611 | `Guidelines for Legal Requests of User Data` | heading `Submitting requests` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

---

### ret_008

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub report a researcher to law enforcement for an accidental, good-faith violation during authorized vulnerability research?
- Expected sources:
  - `GitHub Bug Bounty Program Legal Safe Harbor` | heading contains `Safe Harbor Terms` | `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 41
- Reciprocal rank: 0.0244
- Top-5 retrieved chunks:
  - 1. score=0.6568 | `GitHub Research Program Terms` | heading `H. Miscellaneous > 1. Governing Law` | `Policies/github-terms/github-research-program-terms.md`
  - 2. score=0.6404 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 3. score=0.6365 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 4. score=0.6330 | `GitHub Community Code of Conduct` | heading `Enforcement > _What GitHub Community Participants Can Do_` | `Policies/github-terms/github-community-code-of-conduct.md`
  - 5. score=0.6325 | `Guidelines for Legal Requests of User Data` | heading `About these guidelines` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

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
  - 1. score=0.6782 | `GitHub and Trade Controls` | heading `Frequently asked questions > What is available and not available?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 2. score=0.6763 | `GitHub and Trade Controls` | heading `Frequently asked questions > How are organization accounts impacted?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 3. score=0.6743 | `GitHub and Trade Controls` | heading `(document introduction)` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 4. score=0.6330 | `GitHub and Trade Controls` | heading `Frequently asked questions > On which countries and territories are U.S. government sanctions applied?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 5. score=0.6273 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can you clarify availability of GitHub to Cuban developers?` | `Policies/other-site-policies/github-and-trade-controls.md`

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
  - 1. score=0.6489 | `GitHub Terms of Service` | heading `D. User-Generated Content > 8. Public Repositories and Lawful Access` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.6412 | `GitHub Terms of Service` | heading `D. User-Generated Content > 5. License Grant to Other Users` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.6266 | `GitHub Marketplace Terms of Service` | heading `G. Updates to Developer Products` | `Policies/github-terms/github-marketplace-terms-of-service.md`
  - 4. score=0.6183 | `GitHub Open Source Applications Terms and Conditions` | heading `Privacy` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md`
  - 5. score=0.6098 | `GitHub General Privacy Statement` | heading `US State Specific Information > Exercising your Privacy Rights` | `Policies/privacy-policies/github-general-privacy-statement.md`

---

### ret_011

- Category: `semantic`
- Evaluation group: `semantic`
- Query source: `question`
- Query actually used: Will GitHub warn an account owner before handing their information to investigators?
- Expected sources:
  - `Guidelines for Legal Requests of User Data` | heading contains `notify any affected account owners` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 189
- Reciprocal rank: 0.0053
- Top-5 retrieved chunks:
  - 1. score=0.7420 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 2. score=0.7340 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 3. score=0.7295 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 3. Account Security` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 4. score=0.7126 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 5. score=0.7059 | `GitHub Open Source Applications Terms and Conditions` | heading `Privacy` | `Policies/github-terms/github-open-source-applications-terms-and-conditions.md`

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
  - 1. score=0.4032 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - 2. score=0.3536 | `GitHub Secret Scanning Partner Program Agreement` | heading `(document introduction)` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md`
  - 3. score=0.3471 | `GitHub Educational Use Agreement` | heading `8. Miscellaneous. > 8.2 Severability.` | `Policies/github-terms/github-educational-use-agreement.md`
  - 4. score=0.3420 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md`
  - 5. score=0.3364 | `GitHub Secret Scanning Partner Program Agreement` | heading `12. Modifications > 12.3 Program Changes` | `Policies/github-terms/github-secret-scanning-partner-program-agreement.md`

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
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Source coverage@3: 0.3333
- Source coverage@5: 0.3333
- Top-5 retrieved chunks:
  - 1. score=0.7277 | `GitHub Acceptable Use Policies` | heading `11. User Protection` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 2. score=0.7210 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 3. GitHub May Terminate` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.7003 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 5. Suspension` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 4. score=0.6987 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.6889 | `GitHub Terms of Service` | heading `M. Cancellation and Termination` | `Policies/github-terms/github-terms-of-service.md`

---

### ret_014

- Category: `broad`
- Evaluation group: `broad`
- Query source: `question`
- Query actually used: What information does GitHub gather about people who use its services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 1 / 1 / 1
- First relevant rank: 1
- Reciprocal rank: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.7612 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.7316 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.7044 | `GitHub General Privacy Statement` | heading `US State Specific Information > Notice of Collection of Personal Information` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.6867 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 5. score=0.6854 | `GitHub Corporate Terms of Service` | heading `T. Miscellaneous > 2. Feedback` | `Policies/github-terms/github-corporate-terms-of-service.md`

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
- First relevant rank: 7
- Reciprocal rank: 0.1429
- Source coverage@3: 0.0000
- Source coverage@5: 0.0000
- Top-5 retrieved chunks:
  - 1. score=0.7320 | `GitHub Acceptable Use Policies` | heading `3. Intellectual Property, Authenticity, and Private Information` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 2. score=0.7250 | `GitHub Corporate Terms of Service` | heading `C. Compliance with Laws; Acceptable Use; Privacy > 1. Compliance with Laws and Regulations` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 3. score=0.7223 | `GitHub Community Guidelines` | heading `Legal Notices` | `Policies/github-terms/github-community-guidelines.md`
  - 4. score=0.7021 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.6949 | `GitHub Disrupting the Experience of Other Users` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md`

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
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Source coverage@3: 0.5000
- Source coverage@5: 0.5000
- Top-5 retrieved chunks:
  - 1. score=0.7875 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 2. score=0.7762 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 3. score=0.7627 | `GitHub Government Takedown Policy` | heading `What is this?` | `Policies/other-site-policies/github-government-takedown-policy.md`
  - 4. score=0.7608 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 5. score=0.7576 | `GitHub Doxxing and Invasion of Privacy` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`

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
  - 1. score=0.6347 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 2. score=0.5354 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 3. score=0.4610 | `GitHub and Trade Controls` | heading `Frequently asked questions > Can trade-restricted users’ private repositories be made public?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 4. score=0.4603 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.4543 | `GitHub Terms of Service` | heading `E. Private Repositories > 1. Control of Private Repositories` | `Policies/github-terms/github-terms-of-service.md`

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
  - 1. score=0.8500 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > What are your cookie choices and controls?` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.7227 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.7012 | `GitHub Cookies` | heading `Cookies` | `Policies/privacy-policies/github-cookies.md`
  - 4. score=0.6347 | `GitHub General Privacy Statement` | heading `Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies?` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.6291 | `GitHub Cookies` | heading `Cookies` | `Policies/privacy-policies/github-cookies.md`

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
  - 1. score=0.8471 | `GitHub Deceased User Policy` | heading `(document introduction)` | `Policies/other-site-policies/github-deceased-user-policy.md`
  - 2. score=0.7071 | `GitHub Acceptable Use Policies` | heading `8. Privacy` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 3. score=0.6787 | `Guidelines for Legal Requests of User Data` | heading `Disclosure of non-public information` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 4. score=0.6756 | `Guidelines for Legal Requests of User Data` | heading `(document introduction)` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - 5. score=0.6560 | `GitHub Corporate Terms of Service` | heading `B. Account Terms > 3. Account Security` | `Policies/github-terms/github-corporate-terms-of-service.md`

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
  - 1. score=0.8616 | `GitHub Account Recovery Policy` | heading `How can I remove a payment method from a locked account?` | `Policies/other-site-policies/github-account-recovery-policy.md`
  - 2. score=0.6336 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 2. Upon Cancellation` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.6287 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 4. score=0.6268 | `GitHub Terms of Service` | heading `M. Cancellation and Termination > 1. Account Cancellation` | `Policies/github-terms/github-terms-of-service.md`
  - 5. score=0.6047 | `GitHub Terms of Service` | heading `M. Cancellation and Termination` | `Policies/github-terms/github-terms-of-service.md`

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
  - 1. score=0.7594 | `GitHub Trademark Policy` | heading `What Information is Required When Reporting Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 2. score=0.7327 | `GitHub Trademark Policy` | heading `How Does GitHub Respond To Reported Trademark Policy Violations?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 3. score=0.7131 | `GitHub Trademark Policy` | heading `How Do I Report a Trademark Policy Violation?` | `Policies/content-removal-policies/github-trademark-policy.md`
  - 4. score=0.6989 | `GitHub Username Policy` | heading `Trademark Policy` | `Policies/other-site-policies/github-username-policy.md`
  - 5. score=0.6972 | `GitHub Registered Developer Agreement` | heading `(document introduction)` | `Policies/github-terms/github-registered-developer-agreement.md`

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
  - 1. score=0.6583 | `GitHub Terms of Service` | heading `B. Account Terms` | `Policies/github-terms/github-terms-of-service.md`
  - 2. score=0.6298 | `GitHub Terms of Service` | heading `L. Payment > 2. Upgrades, Downgrades, and Changes` | `Policies/github-terms/github-terms-of-service.md`
  - 3. score=0.6271 | `GitHub Terms of Service` | heading `B. Account Terms > 3. Account Requirements` | `Policies/github-terms/github-terms-of-service.md`
  - 4. score=0.6232 | `GitHub Corporate Terms of Service` | heading `S. Support` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.6195 | `GitHub Pre-release License Terms` | heading `11. No Uptime Guarantees.` | `Policies/github-terms/github-pre-release-license-terms.md`

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
  - 1. score=0.3478 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 1. Control` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 2. score=0.3249 | `GitHub General Privacy Statement` | heading `Private repositories: GitHub Access` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.3206 | `GitHub Subprocessors` | heading `(document introduction)` | `Policies/privacy-policies/github-subprocessors.md`
  - 4. score=0.3164 | `GitHub Corporate Terms of Service` | heading `E. Private Repositories > 2. Confidentiality` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.3112 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`

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
  - 1. score=0.6706 | `GitHub Appeal and Reinstatement` | heading `How this works` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 2. score=0.6658 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 3. Termination for Material Breach` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 3. score=0.6303 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 4. score=0.6287 | `GitHub Corporate Terms of Service` | heading `K. Term; Termination; Suspension > 5. Suspension` | `Policies/github-terms/github-corporate-terms-of-service.md`
  - 5. score=0.6228 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

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
  - 1. score=0.8119 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work? > What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 2. score=0.6730 | `GitHub Private Information Removal Policy` | heading `(document introduction)` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 3. score=0.6573 | `DMCA Takedown Policy` | heading `B. What About Forks? (or What's a Fork?)` | `Policies/content-removal-policies/dmca-takedown-policy.md`
  - 4. score=0.6169 | `GitHub Private Information Removal Policy` | heading `How Does This Actually Work?` | `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - 5. score=0.6147 | `GitHub Private Information Removal Policy` | heading `Disputes` | `Policies/content-removal-policies/github-private-information-removal-policy.md`

---

### multi_002

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: Can a user appeal GitHub's decision to restrict content or disable an account for an alleged policy violation?
- Expected sources:
  - `GitHub Appeal and Reinstatement` | heading contains `Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - `GitHub Community Guidelines` | heading contains `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 1 / 1
- First relevant rank: 2
- Reciprocal rank: 0.5000
- Source coverage@3: 1.0000
- Source coverage@5: 1.0000
- Top-5 retrieved chunks:
  - 1. score=0.7928 | `GitHub Acceptable Use Policies` | heading `11. User Protection` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 2. score=0.7415 | `GitHub Appeal and Reinstatement` | heading `What are Appeals and Reinstatements?` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - 3. score=0.7317 | `GitHub Community Guidelines` | heading `Appeal and Reinstatement` | `Policies/github-terms/github-community-guidelines.md`
  - 4. score=0.7138 | `GitHub and Trade Controls` | heading `Frequently asked questions > How is GitHub ensuring that folks not living in and/or having professional links to the sanctioned countries and territories still have access or ability to appeal?` | `Policies/other-site-policies/github-and-trade-controls.md`
  - 5. score=0.7135 | `GitHub Appeal and Reinstatement` | heading `How this works > Appeals` | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`

---

### multi_003

- Category: `multi_turn`
- Evaluation group: `multi_turn_oracle`
- Query source: `standalone_reference`
- Query actually used: What personal data does GitHub collect automatically from a user's device or use of the services?
- Expected sources:
  - `GitHub General Privacy Statement` | heading contains `Automatically` | `Policies/privacy-policies/github-general-privacy-statement.md`
- Hit@1 / Hit@3 / Hit@5: 0 / 0 / 0
- First relevant rank: 74
- Reciprocal rank: 0.0135
- Top-5 retrieved chunks:
  - 1. score=0.8788 | `GitHub General Privacy Statement` | heading `Personal Data We Collect` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 2. score=0.7783 | `GitHub General Privacy Statement` | heading `Processing Purposes: How We Use Your Personal Data` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.7724 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From Third Parties` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 4. score=0.7662 | `GitHub General Privacy Statement` | heading `Personal Data We Collect > From You` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 5. score=0.7345 | `GitHub General Privacy Statement` | heading `Security and Retention` | `Policies/privacy-policies/github-general-privacy-statement.md`

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
  - 1. score=0.7614 | `GitHub Active Malware or Exploits` | heading `(document introduction)` | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - 2. score=0.6916 | `GitHub General Privacy Statement` | heading `Security` | `Policies/privacy-policies/github-general-privacy-statement.md`
  - 3. score=0.6701 | `Coordinated Disclosure of Security Vulnerabilities` | heading `(document introduction)` | `Policies/security-policies/coordinated-disclosure-of-security-vulnerabilities.md`
  - 4. score=0.6656 | `GitHub Acceptable Use Policies` | heading `5. Site Access and Safety` | `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - 5. score=0.6651 | `GitHub Research Program Terms` | heading `A. Your Feedback` | `Policies/github-terms/github-research-program-terms.md`

---
