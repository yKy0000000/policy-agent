# Answer eval human review

Semantic fields below are intentionally left unchecked for human reviewers.

## ans_001 — direct

- **Source case:** `ret_002`
- **Expected behavior:** `answer`
- **Question:** Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?
- **LLM rewritten query:** Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?

### Retrieved Top5 evidence

- [S1] **GitHub Acceptable Use Policies** — 5. Site Access and Safety — `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- [S2] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- [S3] **GitHub Marketplace Developer Agreement** — 3.	RESTRICTIONS AND RESPONSIBILITIES — `Policies/github-terms/github-marketplace-developer-agreement.md`
- [S4] **GitHub Acceptable Use Policies** — 4. Spam and Inauthentic Activity on GitHub — `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- [S5] **GitHub SIRT description RFC 2350** — 3. Charter > 3.1 Mission Statement — `Policies/security-policies/github-sirt-description-rfc-2350.md`

### Generated answer

No. GitHub does not allow content or activity on its platform that directly supports unlawful active attack or malware campaigns causing technical harms, including using GitHub to deliver malicious executables or as attack infrastructure (for example, organizing denial of service attacks or managing command and control servers), where there is no implicit or explicit dual-use purpose prior to the abuse [S1]. It also prohibits using its servers to disrupt or attempt to disrupt, or to gain or attempt to gain unauthorized access to, any service, device, data, account, or network [S1].

GitHub separately states that it does not allow anyone to use its platform in direct support of unlawful attacks that cause technical harms, such as using GitHub to deliver malicious executables or as attack infrastructure, including organizing denial of service attacks or managing command and control servers [S2]. However, GitHub allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, assuming positive intention and educational/security-community benefit [S2]. In rare cases of very widespread abuse of dual-use content, GitHub may restrict access to that specific instance to disrupt an ongoing unlawful attack or malware campaign leveraging GitHub as an exploit or malware CDN, typically by putting content behind authentication, and as a last resort disabling access or removing it where that is not possible [S2].

For Marketplace, developers may not attempt to distribute any Developer Product that contains or installs active malware or exploits, or uses the platform for exploit delivery (such as part of a command and control system) [S3].

### Inline citations and actual cited sources

- Citation IDs: S1, S2, S3
- [S1] **GitHub Acceptable Use Policies** — 5. Site Access and Safety — `Policies/acceptable-use-policies/github-acceptable-use-policies.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-acceptable-use-policies.md
- [S2] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md
- [S3] **GitHub Marketplace Developer Agreement** — 3.	RESTRICTIONS AND RESPONSIBILITIES — `Policies/github-terms/github-marketplace-developer-agreement.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-marketplace-developer-agreement.md

### Required points

- GitHub prohibits using its platform in direct support of unlawful attacks that cause technical harm, including delivering malicious executables or operating attack infrastructure.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The prohibition should not be broadened into a categorical ban on legitimate dual-use vulnerability, malware, or exploit research.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers.

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

### Forbidden claims

- GitHub prohibits all vulnerability, malware, or exploit research regardless of purpose.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_002 — direct

- **Source case:** `ret_005`
- **Expected behavior:** `answer`
- **Question:** What contact details must be included in a DMCA counter notice?
- **LLM rewritten query:** What contact details must be included in a DMCA counter notice?

### Retrieved Top5 evidence

- [S1] **Guide to Submitting a DMCA Counter Notice** — Your Counter Notice Must... — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- [S2] **Guide to Submitting a DMCA Counter Notice** — How to Submit Your Counter Notice — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- [S3] **Guide to Submitting a DMCA Takedown Notice** — Complaints about Anti-Circumvention Technology — `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
- [S4] **Guide to Submitting a DMCA Takedown Notice** — How to Submit Your Complaint — `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
- [S5] **Guide to Submitting a DMCA Counter Notice** — Before You Start — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`

### Generated answer

A DMCA counter notice must include your contact information: your email address, name, telephone number, and physical address [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **Guide to Submitting a DMCA Counter Notice** — Your Counter Notice Must... — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md

### Required points

- A DMCA counter notice must include the submitter's email address, name, telephone number, and physical address.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> Include your email address, name, telephone number, and physical address.

### Forbidden claims

- None specified.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_003 — specific

- **Source case:** `ret_017`
- **Expected behavior:** `answer`
- **Question:** If a parent repository is disabled for exposing private information, are all of its forks disabled automatically?
- **LLM rewritten query:** If a parent repository is disabled for exposing private information, are all of its forks disabled automatically?

### Retrieved Top5 evidence

- [S1] **GitHub Private Information Removal Policy** — How Does This Actually Work? > What About Forks? (or What's a Fork?) — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S2] **Guide to Submitting a DMCA Takedown Notice** — Your Complaint Must ... — `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
- [S3] **Guide to Submitting a DMCA Takedown Notice** — Your Complaint Must ... — `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
- [S4] **DMCA Takedown Policy** — B. What About Forks? (or What's a Fork?) — `Policies/content-removal-policies/dmca-takedown-policy.md`
- [S5] **GitHub Private Information Removal Policy** — How Does This Actually Work? — `Policies/content-removal-policies/github-private-information-removal-policy.md`

### Generated answer

No. GitHub will not automatically disable forks when disabling a parent repository, because forks belong to different users and may have been altered in significant ways [S1]. GitHub does not conduct any independent investigation into forks; it expects the requester to investigate and expressly include forks in the request if they believe the forks also contain private information [S1].

However, if the requester identified all existing forks of that repository at the time of the notice, GitHub would process a valid claim against all forks in that network when processing the notice [S1]. Also, if the reported network contains more than 100 repositories and would be difficult to review in its entirety, GitHub may consider disabling the entire network if the notice states that, based on the representative number of forks reviewed, the requester believes all or most forks contain the reported content [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **GitHub Private Information Removal Policy** — How Does This Actually Work? > What About Forks? (or What's a Fork?) — `Policies/content-removal-policies/github-private-information-removal-policy.md` — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md

### Required points

- GitHub does not automatically disable forks when it disables a parent repository under the Private Information Removal Policy.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- A requester is expected to investigate forks and expressly include forks believed to contain the private information.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> GitHub will not automatically disable forks when disabling a parent repository. This is because forks belong to different users and may have been altered in significant ways. GitHub does not conduct any independent investigation into forks. We expect those sending private information removal requests to conduct that investigation and, if they believe that the forks also contain private information, expressly include forks in their request.

### Forbidden claims

- All forks are automatically disabled when the parent repository is disabled.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_004 — semantic

- **Source case:** `ret_007`
- **Expected behavior:** `answer`
- **Question:** May I publish another person's home address or banking details in a repository?
- **LLM rewritten query:** May I publish another person's home address or banking details in a repository?

### Retrieved Top5 evidence

- [S1] **GitHub Doxxing and Invasion of Privacy** — Document introduction — `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md`
- [S2] **Guidelines for Legal Requests of User Data** — GitHub terminology — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- [S3] **GitHub Impersonation** — Document introduction — `Policies/acceptable-use-policies/github-impersonation.md`
- [S4] **GitHub Corporate Terms of Service** — A. Definitions — `Policies/github-terms/github-corporate-terms-of-service.md`
- [S5] **GitHub Private Information Removal Policy** — How Does This Actually Work? — `Policies/content-removal-policies/github-private-information-removal-policy.md`

### Generated answer

No. Publishing another person's home address or banking details is prohibited by GitHub's doxxing and invasion of privacy policy, which states you should not post other people's personal information, explicitly including physical addresses or other private location information and bank account information [S1].

GitHub will take context into account, including whether the content is publicly available elsewhere; however, sharing such information with intent to harass or incite abusive behavior may also violate the bullying and harassment prohibition [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **GitHub Doxxing and Invasion of Privacy** — Document introduction — `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md

### Required points

- GitHub's policy says not to post another person's personal information.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- Physical addresses and bank account or credit card information are listed as covered examples.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> Don't post other people's personal information. This includes:
>
> * Personal, private email addresses
> * Phone numbers
> * Physical addresses or other private location information
> * Bank account information or credit card numbers

### Forbidden claims

- None specified.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_005 — semantic

- **Source case:** `ret_011`
- **Expected behavior:** `answer`
- **Question:** Will GitHub warn an account owner before handing their information to investigators?
- **LLM rewritten query:** Will GitHub warn an account owner before handing their information to investigators?

### Retrieved Top5 evidence

- [S1] **Guidelines for Legal Requests of User Data** — Document introduction — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- [S2] **Guidelines for Legal Requests of User Data** — Disclosure of non-public information — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- [S3] **GitHub Private Information Removal Policy** — How Does This Actually Work? — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S4] **GitHub Research Program Terms** — B. Confidentiality — `Policies/github-terms/github-research-program-terms.md`
- [S5] **GitHub Terms of Service** — M. Cancellation and Termination > 2. Upon Cancellation — `Policies/github-terms/github-terms-of-service.md`

### Generated answer

Yes. GitHub states that it will **notify affected users** about any requests for their account information, unless prohibited from doing so by law or court order [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **Guidelines for Legal Requests of User Data** — Document introduction — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md

### Required points

- GitHub's policy is to notify affected users about pending requests concerning their accounts or repositories before disclosure.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- Notification may be withheld when prohibited by law or court order, and may be delayed in rare exigent or ongoing-investigation circumstances.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.

### Forbidden claims

- GitHub always notifies an account owner before every disclosure without exception.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `False`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_006 — semantic

- **Source case:** `ret_012`
- **Expected behavior:** `answer`
- **Question:** Is code used to study vulnerabilities automatically removed just because it could also be misused?
- **LLM rewritten query:** Is code used to study vulnerabilities automatically removed just because it could also be misused?

### Retrieved Top5 evidence

- [S1] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- [S2] **GitHub Bug Bounty Program Legal Safe Harbor** — 1. Safe Harbor Terms — `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`
- [S3] **Guide to Submitting a DMCA Counter Notice** — Before You Start — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md`
- [S4] **Guide to Submitting a DMCA Takedown Notice** — Before You Start — `Policies/content-removal-policies/guide-to-submitting-a-dmca-takedown-notice.md`
- [S5] **GitHub Terrorism and Violent Extremism** — Document introduction — `Policies/acceptable-use-policies/github-terrorism-and-violent-extremism.md`

### Generated answer

No. GitHub’s Active Malware or Exploits policy expressly allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, citing its educational value and net benefit to the security community [S1]. It states that restrictions are not intended to purge or restrict dual-use content in perpetuity, and that any restrictions in rare widespread-abuse cases are temporary where feasible [S1].

That said, the policy does allow restrictions in rare cases of very widespread abuse of dual-use content, potentially including disabling access or full removal as a last resort, to disrupt an ongoing unlawful attack or malware campaign [S1]. So removal is not automatic based on potential misuse; it is tied to actual abuse and is generally temporary [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md

### Required points

- GitHub permits dual-use content used for legitimate vulnerability, malware, or exploit research.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The possibility of misuse alone does not mean the content is automatically removed.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- In rare cases of widespread actual abuse, GitHub may restrict a specific instance to disrupt an ongoing unlawful attack or malware campaign.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

> In rare cases of very widespread abuse of dual-use content, we may restrict access to that specific instance of the content to disrupt an ongoing unlawful attack or malware campaign that is leveraging the GitHub platform as an exploit or malware CDN.

### Forbidden claims

- GitHub automatically removes code solely because it could be misused.
- GitHub never restricts dual-use content even when it is being widely abused in an ongoing attack.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_007 — broad

> **BROAD CASE REVIEW NOTE:** Check whether the answer limits itself to supported major circumstances, avoids claiming an exhaustive list, and gives enough qualification to prevent an exhaustive reading.

- **Source case:** `ret_013`
- **Expected behavior:** `answer`
- **Question:** When can GitHub restrict or shut down an account?
- **LLM rewritten query:** When can GitHub restrict or shut down an account?

### Retrieved Top5 evidence

- [S1] **GitHub Corporate Terms of Service** — K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation — `Policies/github-terms/github-corporate-terms-of-service.md`
- [S2] **GitHub Sponsors Additional Terms** — Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension. — `Policies/github-terms/github-sponsors-additional-terms.md`
- [S3] **GitHub and Trade Controls** — Frequently asked questions > How are organization accounts impacted? — `Policies/other-site-policies/github-and-trade-controls.md`
- [S4] **GitHub Community Code of Conduct** — Standards > _What is not Allowed_ — `Policies/github-terms/github-community-code-of-conduct.md`
- [S5] **GitHub Terms of Service** — M. Cancellation and Termination — `Policies/github-terms/github-terms-of-service.md`

### Generated answer

GitHub can restrict or shut down an account in several circumstances described in the published policies:

- **Violation of terms (Community Code of Conduct context):** If a GitHub.com account is identified as violating the Terms of Service, GitHub will close the account [S4]. Accounts created to inquire about flagged or suspended accounts will also be removed [S4].
- **Underage users:** If GitHub learns or has reason to suspect a user is under 13, it will close the GitHub.com account [S4].
- **Sponsors program violations or sanctions:** GitHub may immediately suspend a Sponsored Developer Account for violating the Sponsors Additional Terms or the Agreement, or if the person is on a restricted trade list or located/resident in a comprehensively sanctioned country; failure to cure may result in termination [S2].
- **Sanctioned organizations:** If an organization is based in, or has sufficient ties to, a sanctioned territory/country for which GitHub lacks a U.S. government license, or otherwise appears subject to U.S. economic sanctions, the organization account and affiliated owner account will be restricted [S3].
- **Termination for convenience (Corporate Terms):** Either party may terminate an Order Form or Agreement without cause with at least 30 days' prior written notice [S1].

Note: The provided evidence does not specify a single comprehensive list of all grounds for account restriction or shutdown beyond these provisions.

### Inline citations and actual cited sources

- Citation IDs: S4, S2, S3, S1
- [S4] **GitHub Community Code of Conduct** — Standards > _What is not Allowed_ — `Policies/github-terms/github-community-code-of-conduct.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-community-code-of-conduct.md
- [S2] **GitHub Sponsors Additional Terms** — Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension. — `Policies/github-terms/github-sponsors-additional-terms.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-sponsors-additional-terms.md
- [S3] **GitHub and Trade Controls** — Frequently asked questions > How are organization accounts impacted? — `Policies/other-site-policies/github-and-trade-controls.md` — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-and-trade-controls.md
- [S1] **GitHub Corporate Terms of Service** — K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation — `Policies/github-terms/github-corporate-terms-of-service.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-corporate-terms-of-service.md

### Required points

- GitHub's Terms of Service reserve a broad right to suspend or terminate access to all or part of the website, with or without cause or notice.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- Policy enforcement may include suspending a user account or organization, and affected users may have an appeal or reinstatement process.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> GitHub has the right to suspend or terminate your access to all or any part of the Website at any time, with or without cause, with or without notice, effective immediately. GitHub reserves the right to refuse service to anyone for any reason at any time.

> GitHub provides an internal complaint-handling process where users can submit requests for reinstatement or provide additional information to appeal a moderation decision.

> Where we have decided that moderation action is warranted, these are some of the ways we may respond:

### Forbidden claims

- The listed examples are an exhaustive statement of every circumstance in which GitHub can restrict or terminate an account.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `abstain`
- Behavior pass: `False`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `False`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_multi_001 — multi_turn

- **Source case:** `multi_001`
- **Expected behavior:** `answer`
- **Question:** What happens to the forks?
- **Original history:**

  - **User:** How does GitHub handle requests to remove private information from a repository?
  - **Assistant:** GitHub's Private Information Removal Policy describes how it reviews reports and may disable qualifying content.
- **LLM rewritten query:** What happens to forks when GitHub removes private information from a repository under its Private Information Removal Policy?

### Retrieved Top5 evidence

- [S1] **GitHub Private Information Removal Policy** — How Does This Actually Work? > What About Forks? (or What's a Fork?) — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S2] **GitHub Private Information Removal Policy** — How Does This Actually Work? — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S3] **GitHub Private Information Removal Policy** — Things to Know — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S4] **GitHub Private Information Removal Policy** — Document introduction — `Policies/content-removal-policies/github-private-information-removal-policy.md`
- [S5] **GitHub Private Information Removal Policy** — What is Private Information? > Private information removal requests are _not_ appropriate for: — `Policies/content-removal-policies/github-private-information-removal-policy.md`

### Generated answer

GitHub will not automatically disable forks when it disables a parent repository, because forks belong to different users and may have been altered significantly; GitHub also does not conduct any independent investigation into forks [S1]. Instead, GitHub expects the requester to investigate forks and expressly include them in the removal request if they believe the forks also contain the private information [S1].

If the requester identified all existing forks of the repository at the time of the notice, GitHub would process a valid claim against all forks in that network when processing the notice, given the likelihood that newly created forks would contain the same content [S1]. Additionally, if the reported network contains more than 100 repositories and would be difficult to review in its entirety, GitHub may consider disabling the entire network if the notice states that, based on a representative number of forks reviewed, the requester believes all or most forks contain the reported content [S1].

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **GitHub Private Information Removal Policy** — How Does This Actually Work? > What About Forks? (or What's a Fork?) — `Policies/content-removal-policies/github-private-information-removal-policy.md` — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md

### Required points

- Forks are not automatically disabled when GitHub disables a parent repository under the Private Information Removal Policy.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The requester is expected to investigate and expressly include forks believed to contain the private information.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> GitHub will not automatically disable forks when disabling a parent repository. This is because forks belong to different users and may have been altered in significant ways. GitHub does not conduct any independent investigation into forks. We expect those sending private information removal requests to conduct that investigation and, if they believe that the forks also contain private information, expressly include forks in their request.

### Forbidden claims

- All forks are automatically disabled together with the parent repository.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `answer`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_multi_002 — multi_turn

- **Source case:** `multi_004`
- **Expected behavior:** `answer`
- **Question:** What if it is for security research?
- **Original history:**

  - **User:** Does GitHub prohibit repositories that support malware or exploit campaigns?
  - **Assistant:** GitHub prohibits using the platform in direct support of unlawful attacks that cause technical harm.
- **LLM rewritten query:** Does GitHub's prohibition on using the platform in direct support of unlawful attacks that cause technical harm apply to security research?

### Retrieved Top5 evidence

- [S1] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- [S2] **GitHub Acceptable Use Policies** — 5. Site Access and Safety — `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- [S3] **GitHub Terrorism and Violent Extremism** — Document introduction — `Policies/acceptable-use-policies/github-terrorism-and-violent-extremism.md`
- [S4] **GitHub Bullying and Harassment** — Document introduction — `Policies/acceptable-use-policies/github-bullying-and-harassment.md`
- [S5] **GitHub Acceptable Use Policies** — 2. User Safety — `Policies/acceptable-use-policies/github-acceptable-use-policies.md`

### Generated answer

GitHub allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, because publication and distribution of such content has educational value and provides a net benefit to the security community; GitHub assumes positive intention and use of these projects to drive ecosystem improvements [S1].

That said, the allowance is not unlimited. In rare cases of very widespread abuse of dual-use content, GitHub may restrict access to that specific instance to disrupt an ongoing unlawful attack or malware campaign leveraging GitHub as an exploit or malware CDN—typically by putting the content behind authentication, and as a last resort by disabling access or full removal where that isn't possible (e.g., gists) [S1]. Such restrictions are temporary where feasible and are not meant to purge or perpetually restrict specific dual-use content or its copies [S1]. GitHub will contact project owners about restrictions where possible, and an appeals process exists if you believe your content was unduly restricted [S1].

GitHub also recommends (but does not require) that repository owners posting potentially harmful security research content clearly identify and describe any potentially harmful content in a disclaimer in the README.md or source code comments, and provide a preferred contact method for third-party abuse inquiries via a SECURITY.md file [S1].

One scope limit to note: GitHub considers the npm registry to be a platform used primarily for installation and run-time use of code, and not for research [S1].

The provided published policies do not specify further conditions, review criteria, or approval processes for security research beyond the above.

### Inline citations and actual cited sources

- Citation IDs: S1
- [S1] **GitHub Active Malware or Exploits** — Document introduction — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md

### Required points

- GitHub allows dual-use vulnerability, malware, or exploit content used for legitimate security research because it can have educational and security-community value.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The allowance does not protect use of GitHub in direct support of unlawful attacks that cause technical harm.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers.

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

### Forbidden claims

- All security research involving malware or exploits is prohibited.
- Labeling content as security research makes active attack infrastructure permissible.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `abstain`
- Behavior pass: `False`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_unsup_001 — unsupported

> **UNSUPPORTED CASE:** Check that related policy context was not converted into an unsupported percentage, physical location, or decision deadline.

- **Source case:** `ret_022`
- **Expected behavior:** `abstain`
- **Question:** What uptime percentage does GitHub guarantee for free personal accounts?
- **LLM rewritten query:** What uptime percentage does GitHub guarantee for free personal accounts?

### Retrieved Top5 evidence

- [S1] **GitHub Pre-release License Terms** — 11. No Uptime Guarantees. — `Policies/github-terms/github-pre-release-license-terms.md`
- [S2] **GitHub Terms of Service** — B. Account Terms > 3. Account Requirements — `Policies/github-terms/github-terms-of-service.md`
- [S3] **GitHub Sponsors Additional Terms** — Terms for Sponsors > 2. Payment. > 2.2. Fees. — `Policies/github-terms/github-sponsors-additional-terms.md`
- [S4] **GitHub and Trade Controls** — Frequently asked questions > What is available and not available? — `Policies/other-site-policies/github-and-trade-controls.md`
- [S5] **GitHub Community Code of Conduct** — Standards > _What is not Allowed_ — `Policies/github-terms/github-community-code-of-conduct.md`

### Generated answer

The provided published policies do not specify any uptime percentage guarantee for free personal accounts. The only uptime-related provision in the supplied evidence states that pre-release software is not subject to an uptime guarantee or similar service level agreement [S1], but that applies to pre-release software, not to free personal accounts generally. None of the other sources address uptime or service level commitments for free personal accounts [S2][S3][S4][S5].

### Inline citations and actual cited sources

- Citation IDs: S1, S2, S3, S4, S5
- [S1] **GitHub Pre-release License Terms** — 11. No Uptime Guarantees. — `Policies/github-terms/github-pre-release-license-terms.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-pre-release-license-terms.md
- [S2] **GitHub Terms of Service** — B. Account Terms > 3. Account Requirements — `Policies/github-terms/github-terms-of-service.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-terms-of-service.md
- [S3] **GitHub Sponsors Additional Terms** — Terms for Sponsors > 2. Payment. > 2.2. Fees. — `Policies/github-terms/github-sponsors-additional-terms.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-sponsors-additional-terms.md
- [S4] **GitHub and Trade Controls** — Frequently asked questions > What is available and not available? — `Policies/other-site-policies/github-and-trade-controls.md` — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-and-trade-controls.md
- [S5] **GitHub Community Code of Conduct** — Standards > _What is not Allowed_ — `Policies/github-terms/github-community-code-of-conduct.md` — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-community-code-of-conduct.md

### Required points

- The provided published policies do not specify an uptime percentage guarantee for free personal accounts.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The no-uptime-guarantee provision in the relevant evidence applies to pre-release software, not free personal accounts generally.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> The pre-release software is not subject to an uptime guarantee or similar service level agreement. The software may be unavailable or stop working entirely at any time for any reason.

### Forbidden claims

- GitHub guarantees 99.9% uptime for free personal accounts.
- GitHub guarantees 99.99% uptime for free personal accounts.
- The pre-release software uptime provision is an uptime SLA for free personal accounts.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `abstain`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_unsup_002 — unsupported

> **UNSUPPORTED CASE:** Check that related policy context was not converted into an unsupported percentage, physical location, or decision deadline.

- **Source case:** `ret_023`
- **Expected behavior:** `abstain`
- **Question:** In which exact physical data center is my specific repository stored?
- **LLM rewritten query:** In which exact physical data center is my specific repository stored?

### Retrieved Top5 evidence

- [S1] **Guidelines for Legal Requests of User Data** — GitHub terminology — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- [S2] **GitHub and Trade Controls** — Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)? — `Policies/other-site-policies/github-and-trade-controls.md`
- [S3] **GitHub Marketplace Developer Agreement** — Addendum 1: Data Protection Addendum — `Policies/github-terms/github-marketplace-developer-agreement.md`
- [S4] **Guidelines for Legal Requests of User Data** — Submitting requests — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- [S5] **GitHub General Privacy Statement** — Private repositories: GitHub Access — `Policies/privacy-policies/github-general-privacy-statement.md`

### Generated answer

The provided published policies do not specify the exact physical data center where a specific repository is stored. The evidence describes repositories generally as project folders containing files and revision history [S1], and addresses legal-process handling for repository data [S4], but it does not identify any physical storage location for an individual repository.

### Inline citations and actual cited sources

- Citation IDs: S1, S4
- [S1] **Guidelines for Legal Requests of User Data** — GitHub terminology — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- [S4] **Guidelines for Legal Requests of User Data** — Submitting requests — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md

### Required points

- The provided published policies do not identify the exact physical data center storing a specific repository.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The privacy statement describes Personal Data being stored and processed across broad regions and countries, not a repository-specific facility.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> GitHub stores and processes Personal Data in a variety of locations, including your local region, the United States, and other countries where GitHub, its affiliates, subsidiaries, or subprocessors have operations.

### Forbidden claims

- The repository is stored in a United States data center.
- The repository is stored in Virginia.
- The repository is stored in Seattle.
- The user's region determines the exact data center containing the repository.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `abstain`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `False`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---

## ans_unsup_003 — unsupported

> **UNSUPPORTED CASE:** Check that related policy context was not converted into an unsupported percentage, physical location, or decision deadline.

- **Source case:** `ret_024`
- **Expected behavior:** `abstain`
- **Question:** What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- **LLM rewritten query:** What is the maximum number of days GitHub will take to decide every account-suspension appeal?

### Retrieved Top5 evidence

- [S1] **GitHub Corporate Terms of Service** — K. Term; Termination; Suspension > 3. Termination for Material Breach — `Policies/github-terms/github-corporate-terms-of-service.md`
- [S2] **GitHub Appeal and Reinstatement** — How this works — `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
- [S3] **GitHub Corporate Terms of Service** — K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation — `Policies/github-terms/github-corporate-terms-of-service.md`
- [S4] **GitHub Secret Scanning Partner Program Agreement** — 16. Term, Termination, and Survival > 16.4 Immediate Suspension — `Policies/github-terms/github-secret-scanning-partner-program-agreement.md`
- [S5] **GitHub Terms of Service** — M. Cancellation and Termination > 2. Upon Cancellation — `Policies/github-terms/github-terms-of-service.md`

### Generated answer

The provided published policies do not specify a maximum number of days for GitHub to decide account-suspension appeals. The appeal policy states only that GitHub staff will review the submitted information to determine whether there is sufficient information to warrant reinstatement or granting of an appeal, and that appeals may be submitted for up to six months following a moderation decision [S2]. No decision deadline is stated.

### Inline citations and actual cited sources

- Citation IDs: S2
- [S2] **GitHub Appeal and Reinstatement** — How this works — `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-appeal-and-reinstatement.md

### Required points

- The published policies do not specify a universal maximum decision time for every account-suspension appeal.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing
- The six-month period is a window for submitting an appeal after a moderation decision, not a guaranteed appeal decision deadline.
  - [ ] covered
  - [ ] partially covered
  - [ ] missing

### Supporting snippets

> You may Appeal a moderation decision for up to six months following the decision. GitHub may, in its discretion, refuse to consider any Appeals submitted more than six months after the decision.

> GitHub staff will review the information provided in the form to determine whether there is sufficient information to warrant Reinstatement or granting of an Appeal.

### Forbidden claims

- GitHub guarantees a decision within 30 days.
- GitHub guarantees a decision within 60 days.
- GitHub guarantees a decision within 90 days.
- GitHub guarantees a decision within six months.
- Six months is the appeal decision deadline.

### Deterministic checks

- Pipeline: `{'status': 'completed', 'rewrite_success': True, 'retrieval_success': True, 'generation_success': True, 'citation_validation_success': True, 'overall_pipeline_success': True, 'error_stage': None, 'error': None}`
- Detected behavior: `abstain`
- Behavior pass: `True`
- Citation validation pass: `True`
- Invalid citations: `[]`
- Missing citations: `False`
- Model-generated URL: `False`
- Acceptable source hit: `True`
- Forbidden claim matches: `[]`

### Human Review

**Claim-level grounding:**
- [ ] pass
- [ ] partial
- [ ] fail

**Citation entailment:**
- [ ] pass
- [ ] partial
- [ ] fail

**Overclaim / unsupported inference:**
- [ ] none
- [ ] present

**Reviewer notes:**


---
