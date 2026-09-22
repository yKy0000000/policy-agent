# Grounded generation manual review

This is a manual inspection artifact. It does not contain automated answer-quality scores.

## Configuration

- Model: `deepseek-v4-flash`
- Generation prompt: `grounded-policy-answer-v1`
- History window: 2 turns
- Retrieval: frozen lexical Top20 + semantic Top20 union + Cross-Encoder reranker Top5

## API/cache usage

- Rewrite API calls: 6
- Rewrite cache hits: 1
- Generation API calls: 7
- Generation cache hits: 0
- Errors: 0

## ret_002 — direct

**Question:** Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?

**Standalone retrieval query:** Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?

### Retrieved Top5 evidence

- [S1] `GitHub Acceptable Use Policies` — 5. Site Access and Safety (`Policies/acceptable-use-policies/github-acceptable-use-policies.md`)
- [S2] `GitHub Active Malware or Exploits` — Document introduction (`Policies/acceptable-use-policies/github-active-malware-or-exploits.md`)
- [S3] `GitHub Marketplace Developer Agreement` — 3.	RESTRICTIONS AND RESPONSIBILITIES (`Policies/github-terms/github-marketplace-developer-agreement.md`)
- [S4] `GitHub Acceptable Use Policies` — 4. Spam and Inauthentic Activity on GitHub (`Policies/acceptable-use-policies/github-acceptable-use-policies.md`)
- [S5] `GitHub SIRT description RFC 2350` — 3. Charter > 3.1 Mission Statement (`Policies/security-policies/github-sirt-description-rfc-2350.md`)

### Generated answer

No. GitHub does not allow content or activity on its platform that directly supports unlawful active attack or malware campaigns causing technical harms, including using GitHub to deliver malicious executables or as attack infrastructure (for example, organizing denial of service attacks or managing command and control servers), where there is no implicit or explicit dual-use purpose prior to the abuse [S1]. It also prohibits using its servers to disrupt or attempt to disrupt, or to gain or attempt to gain unauthorized access to, any service, device, data, account, or network [S1].

GitHub separately states that it does not allow anyone to use its platform in direct support of unlawful attacks that cause technical harms, such as using GitHub to deliver malicious executables or as attack infrastructure, including organizing denial of service attacks or managing command and control servers [S2]. However, GitHub allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, assuming positive intention and educational/security-community benefit [S2]. In rare cases of very widespread abuse of dual-use content, GitHub may restrict access to that specific instance to disrupt an ongoing unlawful attack or malware campaign leveraging GitHub as an exploit or malware CDN, typically by putting content behind authentication, and as a last resort disabling access or removing it where that is not possible [S2].

For Marketplace, developers may not attempt to distribute any Developer Product that contains or installs active malware or exploits, or uses the platform for exploit delivery (such as part of a command and control system) [S3].

**Citation IDs:** S1, S2, S3

### Rendered sources

- [S1] **GitHub Acceptable Use Policies**
  - Section: 5. Site Access and Safety
  - URL: https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-acceptable-use-policies.md
  - Path: `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
  - Chunk: `chunk_d16788b425405e4d8b96f51b`
- [S2] **GitHub Active Malware or Exploits**
  - Section: Document introduction
  - URL: https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md
  - Path: `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - Chunk: `chunk_7d54462de0e9154ce55d108b`
- [S3] **GitHub Marketplace Developer Agreement**
  - Section: 3.	RESTRICTIONS AND RESPONSIBILITIES
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-marketplace-developer-agreement.md
  - Path: `Policies/github-terms/github-marketplace-developer-agreement.md`
  - Chunk: `chunk_76a40eef1f0fee4df26723be`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## ret_012 — semantic

**Question:** Is code used to study vulnerabilities automatically removed just because it could also be misused?

**Standalone retrieval query:** Is code used to study vulnerabilities automatically removed just because it could also be misused?

### Retrieved Top5 evidence

- [S1] `GitHub Active Malware or Exploits` — Document introduction (`Policies/acceptable-use-policies/github-active-malware-or-exploits.md`)
- [S2] `GitHub Bug Bounty Program Legal Safe Harbor` — 1. Safe Harbor Terms (`Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`)
- [S3] `Guide to Submitting a DMCA Counter Notice` — Before You Start (`Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`)
- [S4] `Guide to Submitting a DMCA Takedown Notice` — Before You Start (`Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`)
- [S5] `GitHub Terrorism and Violent Extremism` — Document introduction (`Policies/acceptable-use-policies/github-terrorism-and-violent-extremism.md`)

### Generated answer

No. GitHub’s Active Malware or Exploits policy expressly allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, citing its educational value and net benefit to the security community [S1]. It states that restrictions are not intended to purge or restrict dual-use content in perpetuity, and that any restrictions in rare widespread-abuse cases are temporary where feasible [S1].

That said, the policy does allow restrictions in rare cases of very widespread abuse of dual-use content, potentially including disabling access or full removal as a last resort, to disrupt an ongoing unlawful attack or malware campaign [S1]. So removal is not automatic based on potential misuse; it is tied to actual abuse and is generally temporary [S1].

**Citation IDs:** S1

### Rendered sources

- [S1] **GitHub Active Malware or Exploits**
  - Section: Document introduction
  - URL: https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md
  - Path: `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
  - Chunk: `chunk_7d54462de0e9154ce55d108b`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## ret_013 — broad

**Question:** When can GitHub restrict or shut down an account?

**Standalone retrieval query:** When can GitHub restrict or shut down an account?

### Retrieved Top5 evidence

- [S1] `GitHub Corporate Terms of Service` — K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation (`Policies/github-terms/github-corporate-terms-of-service.md`)
- [S2] `GitHub Sponsors Additional Terms` — Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension. (`Policies/github-terms/github-sponsors-additional-terms.md`)
- [S3] `GitHub and Trade Controls` — Frequently asked questions > How are organization accounts impacted? (`Policies/other-site-policies/github-and-trade-controls.md`)
- [S4] `GitHub Community Code of Conduct` — Standards > _What is not Allowed_ (`Policies/github-terms/github-community-code-of-conduct.md`)
- [S5] `GitHub Terms of Service` — M. Cancellation and Termination (`Policies/github-terms/github-terms-of-service.md`)

### Generated answer

GitHub can restrict or shut down an account in several circumstances described in the published policies:

- **Violation of terms (Community Code of Conduct context):** If a GitHub.com account is identified as violating the Terms of Service, GitHub will close the account [S4]. Accounts created to inquire about flagged or suspended accounts will also be removed [S4].
- **Underage users:** If GitHub learns or has reason to suspect a user is under 13, it will close the GitHub.com account [S4].
- **Sponsors program violations or sanctions:** GitHub may immediately suspend a Sponsored Developer Account for violating the Sponsors Additional Terms or the Agreement, or if the person is on a restricted trade list or located/resident in a comprehensively sanctioned country; failure to cure may result in termination [S2].
- **Sanctioned organizations:** If an organization is based in, or has sufficient ties to, a sanctioned territory/country for which GitHub lacks a U.S. government license, or otherwise appears subject to U.S. economic sanctions, the organization account and affiliated owner account will be restricted [S3].
- **Termination for convenience (Corporate Terms):** Either party may terminate an Order Form or Agreement without cause with at least 30 days' prior written notice [S1].

Note: The provided evidence does not specify a single comprehensive list of all grounds for account restriction or shutdown beyond these provisions.

**Citation IDs:** S4, S2, S3, S1

### Rendered sources

- [S4] **GitHub Community Code of Conduct**
  - Section: Standards > _What is not Allowed_
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-community-code-of-conduct.md
  - Path: `Policies/github-terms/github-community-code-of-conduct.md`
  - Chunk: `chunk_0ce99a6078cf37abe73d8a85`
- [S2] **GitHub Sponsors Additional Terms**
  - Section: Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension.
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-sponsors-additional-terms.md
  - Path: `Policies/github-terms/github-sponsors-additional-terms.md`
  - Chunk: `chunk_758f53f21830d6df5e81f763`
- [S3] **GitHub and Trade Controls**
  - Section: Frequently asked questions > How are organization accounts impacted?
  - URL: https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-and-trade-controls.md
  - Path: `Policies/other-site-policies/github-and-trade-controls.md`
  - Chunk: `chunk_2899720d6a0761800653e2d4`
- [S1] **GitHub Corporate Terms of Service**
  - Section: K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-corporate-terms-of-service.md
  - Path: `Policies/github-terms/github-corporate-terms-of-service.md`
  - Chunk: `chunk_430ff1a4ccffd44ef3ea83bf`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## multi_001 — multi_turn

**Question:** What happens to the forks?

### History

- **User:** How does GitHub handle requests to remove private information from a repository?
- **Assistant:** GitHub's Private Information Removal Policy describes how it reviews reports and may disable qualifying content.

**Standalone retrieval query:** What happens to forks when GitHub removes private information from a repository under its Private Information Removal Policy?

### Retrieved Top5 evidence

- [S1] `GitHub Private Information Removal Policy` — How Does This Actually Work? > What About Forks? (or What's a Fork?) (`Policies/content-removal-policies/github-private-information-removal-policy.md`)
- [S2] `GitHub Private Information Removal Policy` — How Does This Actually Work? (`Policies/content-removal-policies/github-private-information-removal-policy.md`)
- [S3] `GitHub Private Information Removal Policy` — Things to Know (`Policies/content-removal-policies/github-private-information-removal-policy.md`)
- [S4] `GitHub Private Information Removal Policy` — Document introduction (`Policies/content-removal-policies/github-private-information-removal-policy.md`)
- [S5] `GitHub Private Information Removal Policy` — What is Private Information? > Private information removal requests are _not_ appropriate for: (`Policies/content-removal-policies/github-private-information-removal-policy.md`)

### Generated answer

GitHub will not automatically disable forks when it disables a parent repository, because forks belong to different users and may have been altered significantly; GitHub also does not conduct any independent investigation into forks [S1]. Instead, GitHub expects the requester to investigate forks and expressly include them in the removal request if they believe the forks also contain the private information [S1].

If the requester identified all existing forks of the repository at the time of the notice, GitHub would process a valid claim against all forks in that network when processing the notice, given the likelihood that newly created forks would contain the same content [S1]. Additionally, if the reported network contains more than 100 repositories and would be difficult to review in its entirety, GitHub may consider disabling the entire network if the notice states that, based on a representative number of forks reviewed, the requester believes all or most forks contain the reported content [S1].

**Citation IDs:** S1

### Rendered sources

- [S1] **GitHub Private Information Removal Policy**
  - Section: How Does This Actually Work? > What About Forks? (or What's a Fork?)
  - URL: https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md
  - Path: `Policies/content-removal-policies/github-private-information-removal-policy.md`
  - Chunk: `chunk_161463875a51eb1c46ff33f3`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## ret_022 — unsupported

**Question:** What uptime percentage does GitHub guarantee for free personal accounts?

**Standalone retrieval query:** What uptime percentage does GitHub guarantee for free personal accounts?

### Retrieved Top5 evidence

- [S1] `GitHub Pre-release License Terms` — 11. No Uptime Guarantees. (`Policies/github-terms/github-pre-release-license-terms.md`)
- [S2] `GitHub Terms of Service` — B. Account Terms > 3. Account Requirements (`Policies/github-terms/github-terms-of-service.md`)
- [S3] `GitHub Sponsors Additional Terms` — Terms for Sponsors > 2. Payment. > 2.2. Fees. (`Policies/github-terms/github-sponsors-additional-terms.md`)
- [S4] `GitHub and Trade Controls` — Frequently asked questions > What is available and not available? (`Policies/other-site-policies/github-and-trade-controls.md`)
- [S5] `GitHub Community Code of Conduct` — Standards > _What is not Allowed_ (`Policies/github-terms/github-community-code-of-conduct.md`)

### Generated answer

The provided published policies do not specify any uptime percentage guarantee for free personal accounts. The only uptime-related provision in the supplied evidence states that pre-release software is not subject to an uptime guarantee or similar service level agreement [S1], but that applies to pre-release software, not to free personal accounts generally. None of the other sources address uptime or service level commitments for free personal accounts [S2][S3][S4][S5].

**Citation IDs:** S1, S2, S3, S4, S5

### Rendered sources

- [S1] **GitHub Pre-release License Terms**
  - Section: 11. No Uptime Guarantees.
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-pre-release-license-terms.md
  - Path: `Policies/github-terms/github-pre-release-license-terms.md`
  - Chunk: `chunk_87ea91db9ddecefae97629ef`
- [S2] **GitHub Terms of Service**
  - Section: B. Account Terms > 3. Account Requirements
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-terms-of-service.md
  - Path: `Policies/github-terms/github-terms-of-service.md`
  - Chunk: `chunk_85867a0b6a0b9d17cba279d7`
- [S3] **GitHub Sponsors Additional Terms**
  - Section: Terms for Sponsors > 2. Payment. > 2.2. Fees.
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-sponsors-additional-terms.md
  - Path: `Policies/github-terms/github-sponsors-additional-terms.md`
  - Chunk: `chunk_609b597193925f17c0b613ff`
- [S4] **GitHub and Trade Controls**
  - Section: Frequently asked questions > What is available and not available?
  - URL: https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-and-trade-controls.md
  - Path: `Policies/other-site-policies/github-and-trade-controls.md`
  - Chunk: `chunk_672be43c925d3ed6d1adb2c2`
- [S5] **GitHub Community Code of Conduct**
  - Section: Standards > _What is not Allowed_
  - URL: https://github.com/github/site-policy/blob/main/Policies/github-terms/github-community-code-of-conduct.md
  - Path: `Policies/github-terms/github-community-code-of-conduct.md`
  - Chunk: `chunk_0ce99a6078cf37abe73d8a85`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## ret_023 — unsupported

**Question:** In which exact physical data center is my specific repository stored?

**Standalone retrieval query:** In which exact physical data center is my specific repository stored?

### Retrieved Top5 evidence

- [S1] `Guidelines for Legal Requests of User Data` — GitHub terminology (`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`)
- [S2] `GitHub and Trade Controls` — Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)? (`Policies/other-site-policies/github-and-trade-controls.md`)
- [S3] `GitHub Marketplace Developer Agreement` — Addendum 1: Data Protection Addendum (`Policies/github-terms/github-marketplace-developer-agreement.md`)
- [S4] `Guidelines for Legal Requests of User Data` — Submitting requests (`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`)
- [S5] `GitHub General Privacy Statement` — Private repositories: GitHub Access (`Policies/privacy-policies/github-general-privacy-statement.md`)

### Generated answer

The provided published policies do not specify the exact physical data center where a specific repository is stored. The evidence describes repositories generally as project folders containing files and revision history [S1], and addresses legal-process handling for repository data [S4], but it does not identify any physical storage location for an individual repository.

**Citation IDs:** S1, S4

### Rendered sources

- [S1] **Guidelines for Legal Requests of User Data**
  - Section: GitHub terminology
  - URL: https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
  - Path: `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - Chunk: `chunk_6bc363aa4e3f40702deda958`
- [S4] **Guidelines for Legal Requests of User Data**
  - Section: Submitting requests
  - URL: https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
  - Path: `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
  - Chunk: `chunk_c24304bfd4023a6fd2b89ca1`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---

## ret_024 — unsupported

**Question:** What is the maximum number of days GitHub will take to decide every account-suspension appeal?

**Standalone retrieval query:** What is the maximum number of days GitHub will take to decide every account-suspension appeal?

### Retrieved Top5 evidence

- [S1] `GitHub Corporate Terms of Service` — K. Term; Termination; Suspension > 3. Termination for Material Breach (`Policies/github-terms/github-corporate-terms-of-service.md`)
- [S2] `GitHub Appeal and Reinstatement` — How this works (`Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`)
- [S3] `GitHub Corporate Terms of Service` — K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation (`Policies/github-terms/github-corporate-terms-of-service.md`)
- [S4] `GitHub Secret Scanning Partner Program Agreement` — 16. Term, Termination, and Survival > 16.4 Immediate Suspension (`Policies/github-terms/github-secret-scanning-partner-program-agreement.md`)
- [S5] `GitHub Terms of Service` — M. Cancellation and Termination > 2. Upon Cancellation (`Policies/github-terms/github-terms-of-service.md`)

### Generated answer

The provided published policies do not specify a maximum number of days for GitHub to decide account-suspension appeals. The appeal policy states only that GitHub staff will review the submitted information to determine whether there is sufficient information to warrant reinstatement or granting of an appeal, and that appeals may be submitted for up to six months following a moderation decision [S2]. No decision deadline is stated.

**Citation IDs:** S2

### Rendered sources

- [S2] **GitHub Appeal and Reinstatement**
  - Section: How this works
  - URL: https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-appeal-and-reinstatement.md
  - Path: `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
  - Chunk: `chunk_5d1188bc9474b578388e2ddd`

### Citation validation

- Valid: `True`
- Has citations: `True`
- Invalid citations: `[]`
- Model-generated URL: `False`
- Warnings: `[]`

---
