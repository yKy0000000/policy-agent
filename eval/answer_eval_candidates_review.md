# Answer eval candidate review

Candidate data only. No answer generation or automatic scoring was run.

## ans_001

- **Source case:** `ret_002`
- **Category:** `direct`
- **Question:** Does GitHub allow its platform to be used to deliver malware or run attack infrastructure?
- **Expected behavior:** `answer`

### Required points

- GitHub prohibits using its platform in direct support of unlawful attacks that cause technical harm, including delivering malicious executables or operating attack infrastructure.
- The prohibition should not be broadened into a categorical ban on legitimate dual-use vulnerability, malware, or exploit research.

### Acceptable sources

- **GitHub Active Malware or Exploits** — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — heading contains `(path only)`
- **GitHub Acceptable Use Policies** — `Policies/acceptable-use-policies/github-acceptable-use-policies.md` — heading contains `Site Access and Safety`

### Forbidden claims

- GitHub prohibits all vulnerability, malware, or exploit research regardless of purpose.

### Supporting snippets

> We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers.

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

### Notes

The answer should distinguish active harmful use from legitimate dual-use security research rather than state a blanket malware-related ban.

---

## ans_002

- **Source case:** `ret_005`
- **Category:** `direct`
- **Question:** What contact details must be included in a DMCA counter notice?
- **Expected behavior:** `answer`

### Required points

- A DMCA counter notice must include the submitter's email address, name, telephone number, and physical address.

### Acceptable sources

- **Guide to Submitting a DMCA Counter Notice** — `Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md` — heading contains `Your Counter Notice Must`

### Forbidden claims

- None specified.

### Supporting snippets

> Include your email address, name, telephone number, and physical address.

### Notes

A precise procedural case. Equivalent wording is acceptable, but all four contact details should be present.

---

## ans_003

- **Source case:** `ret_017`
- **Category:** `specific`
- **Question:** If a parent repository is disabled for exposing private information, are all of its forks disabled automatically?
- **Expected behavior:** `answer`

### Required points

- GitHub does not automatically disable forks when it disables a parent repository under the Private Information Removal Policy.
- A requester is expected to investigate forks and expressly include forks believed to contain the private information.

### Acceptable sources

- **GitHub Private Information Removal Policy** — `Policies/content-removal-policies/github-private-information-removal-policy.md` — heading contains `What About Forks?`

### Forbidden claims

- All forks are automatically disabled when the parent repository is disabled.

### Supporting snippets

> GitHub will not automatically disable forks when disabling a parent repository. This is because forks belong to different users and may have been altered in significant ways. GitHub does not conduct any independent investigation into forks. We expect those sending private information removal requests to conduct that investigation and, if they believe that the forks also contain private information, expressly include forks in their request.

### Notes

Section precision matters because GitHub's DMCA materials also discuss forks under a different removal process.

---

## ans_004

- **Source case:** `ret_007`
- **Category:** `semantic`
- **Question:** May I publish another person's home address or banking details in a repository?
- **Expected behavior:** `answer`

### Required points

- GitHub's policy says not to post another person's personal information.
- Physical addresses and bank account or credit card information are listed as covered examples.

### Acceptable sources

- **GitHub Doxxing and Invasion of Privacy** — `Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` — heading contains `(path only)`
- **GitHub Acceptable Use Policies** — `Policies/acceptable-use-policies/github-acceptable-use-policies.md` — heading contains `Intellectual Property, Authenticity, and Private Information`

### Forbidden claims

- None specified.

### Supporting snippets

> Don't post other people's personal information. This includes:
>
> * Personal, private email addresses
> * Phone numbers
> * Physical addresses or other private location information
> * Bank account information or credit card numbers

### Notes

The question uses concrete examples rather than the policy labels doxxing or invasion of privacy.

---

## ans_005

- **Source case:** `ret_011`
- **Category:** `semantic`
- **Question:** Will GitHub warn an account owner before handing their information to investigators?
- **Expected behavior:** `answer`

### Required points

- GitHub's policy is to notify affected users about pending requests concerning their accounts or repositories before disclosure.
- Notification may be withheld when prohibited by law or court order, and may be delayed in rare exigent or ongoing-investigation circumstances.

### Acceptable sources

- **Guidelines for Legal Requests of User Data** — `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` — heading contains `notify any affected account owners`

### Forbidden claims

- GitHub always notifies an account owner before every disclosure without exception.

### Supporting snippets

> It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.

### Notes

The answer must preserve the legal-prohibition and delayed-notification exceptions.

---

## ans_006

- **Source case:** `ret_012`
- **Category:** `semantic`
- **Question:** Is code used to study vulnerabilities automatically removed just because it could also be misused?
- **Expected behavior:** `answer`

### Required points

- GitHub permits dual-use content used for legitimate vulnerability, malware, or exploit research.
- The possibility of misuse alone does not mean the content is automatically removed.
- In rare cases of widespread actual abuse, GitHub may restrict a specific instance to disrupt an ongoing unlawful attack or malware campaign.

### Acceptable sources

- **GitHub Active Malware or Exploits** — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — heading contains `(path only)`
- **GitHub Acceptable Use Policies** — `Policies/acceptable-use-policies/github-acceptable-use-policies.md` — heading contains `Site Access and Safety`

### Forbidden claims

- GitHub automatically removes code solely because it could be misused.
- GitHub never restricts dual-use content even when it is being widely abused in an ongoing attack.

### Supporting snippets

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

> In rare cases of very widespread abuse of dual-use content, we may restrict access to that specific instance of the content to disrupt an ongoing unlawful attack or malware campaign that is leveraging the GitHub platform as an exploit or malware CDN.

### Notes

This case tests the distinction between legitimate dual-use research, mere potential misuse, and actual widespread abuse.

---

## ans_007

- **Source case:** `ret_013`
- **Category:** `broad`
- **Question:** When can GitHub restrict or shut down an account?
- **Expected behavior:** `answer`

### Required points

- GitHub's Terms of Service reserve a broad right to suspend or terminate access to all or part of the website, with or without cause or notice.
- Policy enforcement may include suspending a user account or organization, and affected users may have an appeal or reinstatement process.

### Acceptable sources

- **GitHub Terms of Service** — `Policies/github-terms/github-terms-of-service.md` — heading contains `GitHub May Terminate`
- **GitHub Appeal and Reinstatement** — `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` — heading contains `What are Appeals and Reinstatements?`
- **GitHub Community Guidelines** — `Policies/github-terms/github-community-guidelines.md` — heading contains `What happens if someone violates GitHub's policies?`

### Forbidden claims

- The listed examples are an exhaustive statement of every circumstance in which GitHub can restrict or terminate an account.

### Supporting snippets

> GitHub has the right to suspend or terminate your access to all or any part of the Website at any time, with or without cause, with or without notice, effective immediately. GitHub reserves the right to refuse service to anyone for any reason at any time.

> GitHub provides an internal complaint-handling process where users can submit requests for reinstatement or provide additional information to appeal a moderation decision.

> Where we have decided that moderation action is warranted, these are some of the ways we may respond:

### Notes

This is intentionally broad. A good answer may summarize supported examples but should not claim that its list is exhaustively complete.

---

## ans_multi_001

- **Source case:** `multi_001`
- **Category:** `multi_turn`
- **Question:** What happens to the forks?
- **History:**

  - **User:** How does GitHub handle requests to remove private information from a repository?
  - **Assistant:** GitHub's Private Information Removal Policy describes how it reviews reports and may disable qualifying content.
- **Reference query (not user input):** What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?
- **Expected behavior:** `answer`

### Required points

- Forks are not automatically disabled when GitHub disables a parent repository under the Private Information Removal Policy.
- The requester is expected to investigate and expressly include forks believed to contain the private information.

### Acceptable sources

- **GitHub Private Information Removal Policy** — `Policies/content-removal-policies/github-private-information-removal-policy.md` — heading contains `What About Forks?`

### Forbidden claims

- All forks are automatically disabled together with the parent repository.

### Supporting snippets

> GitHub will not automatically disable forks when disabling a parent repository. This is because forks belong to different users and may have been altered in significant ways. GitHub does not conduct any independent investigation into forks. We expect those sending private information removal requests to conduct that investigation and, if they believe that the forks also contain private information, expressly include forks in their request.

### Notes

The answer eval input must use this history plus the latest question. reference_query is inspection-only and must not replace the real multi-turn input.

---

## ans_multi_002

- **Source case:** `multi_004`
- **Category:** `multi_turn`
- **Question:** What if it is for security research?
- **History:**

  - **User:** Does GitHub prohibit repositories that support malware or exploit campaigns?
  - **Assistant:** GitHub prohibits using the platform in direct support of unlawful attacks that cause technical harm.
- **Reference query (not user input):** Does GitHub allow dual-use vulnerability, malware, or exploit content when it is posted for security research?
- **Expected behavior:** `answer`

### Required points

- GitHub allows dual-use vulnerability, malware, or exploit content used for legitimate security research because it can have educational and security-community value.
- The allowance does not protect use of GitHub in direct support of unlawful attacks that cause technical harm.

### Acceptable sources

- **GitHub Active Malware or Exploits** — `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` — heading contains `(path only)`
- **GitHub Acceptable Use Policies** — `Policies/acceptable-use-policies/github-acceptable-use-policies.md` — heading contains `Site Access and Safety`

### Forbidden claims

- All security research involving malware or exploits is prohibited.
- Labeling content as security research makes active attack infrastructure permissible.

### Supporting snippets

> We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers.

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

### Notes

The answer eval input must preserve the history because the latest question does not identify what 'it' refers to.

---

## ans_unsup_001

- **Source case:** `ret_022`
- **Category:** `unsupported`
- **Question:** What uptime percentage does GitHub guarantee for free personal accounts?
- **Expected behavior:** `abstain`

### Required points

- The provided published policies do not specify an uptime percentage guarantee for free personal accounts.
- The no-uptime-guarantee provision in the relevant evidence applies to pre-release software, not free personal accounts generally.

### Acceptable sources

- **GitHub Pre-release License Terms** — `Policies/github-terms/github-pre-release-license-terms.md` — heading contains `No Uptime Guarantees`

### Forbidden claims

- GitHub guarantees 99.9% uptime for free personal accounts.
- GitHub guarantees 99.99% uptime for free personal accounts.
- The pre-release software uptime provision is an uptime SLA for free personal accounts.

### Supporting snippets

> The pre-release software is not subject to an uptime guarantee or similar service level agreement. The software may be unavailable or stop working entirely at any time for any reason.

### Notes

The snippet supplies nearby uptime context but does not establish an SLA for free personal accounts. The answer must not invent a percentage.

---

## ans_unsup_002

- **Source case:** `ret_023`
- **Category:** `unsupported`
- **Question:** In which exact physical data center is my specific repository stored?
- **Expected behavior:** `abstain`

### Required points

- The provided published policies do not identify the exact physical data center storing a specific repository.
- The privacy statement describes Personal Data being stored and processed across broad regions and countries, not a repository-specific facility.

### Acceptable sources

- **GitHub General Privacy Statement** — `Policies/privacy-policies/github-general-privacy-statement.md` — heading contains `International data transfers`

### Forbidden claims

- The repository is stored in a United States data center.
- The repository is stored in Virginia.
- The repository is stored in Seattle.
- The user's region determines the exact data center containing the repository.

### Supporting snippets

> GitHub stores and processes Personal Data in a variety of locations, including your local region, the United States, and other countries where GitHub, its affiliates, subsidiaries, or subprocessors have operations.

### Notes

The snippet discusses broad Personal Data processing locations. It must not be converted into a claim about the exact facility holding a particular repository.

---

## ans_unsup_003

- **Source case:** `ret_024`
- **Category:** `unsupported`
- **Question:** What is the maximum number of days GitHub will take to decide every account-suspension appeal?
- **Expected behavior:** `abstain`

### Required points

- The published policies do not specify a universal maximum decision time for every account-suspension appeal.
- The six-month period is a window for submitting an appeal after a moderation decision, not a guaranteed appeal decision deadline.

### Acceptable sources

- **GitHub Appeal and Reinstatement** — `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` — heading contains `How this works`

### Forbidden claims

- GitHub guarantees a decision within 30 days.
- GitHub guarantees a decision within 60 days.
- GitHub guarantees a decision within 90 days.
- GitHub guarantees a decision within six months.
- Six months is the appeal decision deadline.

### Supporting snippets

> You may Appeal a moderation decision for up to six months following the decision. GitHub may, in its discretion, refuse to consider any Appeals submitted more than six months after the decision.

> GitHub staff will review the information provided in the form to determine whether there is sufficient information to warrant Reinstatement or granting of an Appeal.

### Notes

This case specifically guards against confusing the six-month submission window with a decision-time guarantee.

---
