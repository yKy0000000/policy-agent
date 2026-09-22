# Answer Eval Deterministic Failure Review

数据来源：

- `eval/results/answer_eval_results.json`
- `eval/answer_eval_candidates.json`
- `cache/policy_index.json`（仅用于按 `chunk_id` 补充原始 chunk text）
- `eval/run_answer_eval.py`（仅用于记录 behavior detector 的现有 regex）

本报告只汇总原始评测证据并提供未勾选的人工审查模板，不对 detector、ground truth、生成答案或检索结果作正确性判断。

## 1. Deterministic failure scope

共 4 个 case：

- `ans_005`：`acceptable_source_hit == false`
- `ans_007`：`behavior_pass == false`；`acceptable_source_hit == false`
- `ans_multi_002`：`behavior_pass == false`
- `ans_unsup_002`：`acceptable_source_hit == false`

这 4 个 case 的 `citation_validation_pass` 均为 `true`，`forbidden_claim_pass` 均为 `true`。

## 2. All 12 cases summary

| case | category | behavior_pass | citation_valid | acceptable_source_hit | forbidden_claim_violation | pipeline_success |
|---|---|---:|---:|---:|---:|---:|
| `ans_001` | direct | true | true | true | false | true |
| `ans_002` | direct | true | true | true | false | true |
| `ans_003` | specific | true | true | true | false | true |
| `ans_004` | semantic | true | true | true | false | true |
| `ans_005` | semantic | true | true | **false** | false | true |
| `ans_006` | semantic | true | true | true | false | true |
| `ans_007` | broad | **false** | true | **false** | false | true |
| `ans_multi_001` | multi_turn | true | true | true | false | true |
| `ans_multi_002` | multi_turn | **false** | true | true | false | true |
| `ans_unsup_001` | unsupported | true | true | true | false | true |
| `ans_unsup_002` | unsupported | true | true | **false** | false | true |
| `ans_unsup_003` | unsupported | true | true | true | false | true |

---

## 3. Failure case: `ans_005`

### Case details

- **case id:** `ans_005`
- **source_case_id:** `ret_011`
- **category:** `semantic`
- **expected_behavior:** `answer`
- **question:** Will GitHub warn an account owner before handing their information to investigators?
- **history:** `[]`
- **rewritten_query:** Will GitHub warn an account owner before handing their information to investigators?

### Generated answer

~~~text
Yes. GitHub states that it will **notify affected users** about any requests for their account information, unless prohibited from doing so by law or court order [S1].
~~~

### Deterministic checks

- `detected_behavior`: `answer`
- `behavior_pass`: `true`
- `citation_validation_pass`: `true`
- `acceptable_source_hit`: `false`
- `forbidden_claim_matches`: `[]`
- `forbidden_claim_pass`: `true`
- `pipeline.overall_pipeline_success`: `true`

### Behavior failure evidence

不适用：`behavior_pass == true`。

### Citation / acceptable source material

#### A. Dataset acceptable_sources

| title | source_path | heading_contains |
|---|---|---|
| Guidelines for Legal Requests of User Data | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | `notify any affected account owners` |

#### B. Model citation_ids

- `S1`

#### C. Actual cited sources

##### `S1`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- **chunk_id:** `chunk_848e7ed07babd1137a0b93ae`
- **chunk text / relevant snippet:**

> Are you a law enforcement officer conducting an investigation that may involve user content hosted on GitHub? Or maybe you're a privacy-conscious person who would like to know what information we share with law enforcement and under what circumstances. Either way, you're on the right page.
>
> In these guidelines, we provide a little background about what GitHub is, the types of data we have, and the conditions under which we will disclose private user information. Before we get into the details, however, here are a few important details you may want to know:
>
> * We will [**notify affected users**](#we-will-notify-any-affected-account-owners) about any requests for their account information, unless prohibited from doing so by law or court order.
> * We will not disclose **location-tracking data**, such as IP address logs, without a valid court order or search warrant.
> * We will not disclose any **private user content**, including the contents of private repositories, without a valid search warrant.

#### D. Why acceptable_source_hit is false

现有 matcher 先比较 `source_path`，路径相同后，再把 cited source 的 `heading_path` 拼接为 heading 并检查是否包含 `heading_contains`。`title` 不参与该 deterministic matcher。

| field | acceptable rule | cited `S1` | raw match result |
|---|---|---|---|
| title | Guidelines for Legal Requests of User Data | Guidelines for Legal Requests of User Data | 相同；但 matcher 不使用此字段 |
| source_path | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | 相同 |
| heading | must contain `notify any affected account owners` | `(empty heading_path)` | 不同；contains 为 false |

因此，这一条已引用 source 的 `source_path` 匹配，但 heading 条件没有匹配，最终 `acceptable_source_hit == false`。

### Retrieval evidence: reranked Top5

#### Rank 1 — `S1`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **reranker score:** `3.4396026134490967`
- **chunk preview:** “Are you a law enforcement officer conducting an investigation that may involve user content hosted on GitHub? ... We will **notify affected users** about any requests for their account information, unless prohibited from doing so by law or court order.”

#### Rank 2 — `S2`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `Disclosure of non-public information`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **reranker score:** `2.8653440475463867`
- **chunk preview:** “It is our policy to disclose non-public user information in connection with a civil or criminal investigation only with user consent or upon receipt of a valid subpoena, civil investigative demand, court order, search warrant, or other similar valid legal process...”

#### Rank 3 — `S3`

- **title:** GitHub Private Information Removal Policy
- **heading:** `How Does This Actually Work?`
- **source_path:** `Policies/content-removal-policies/github-private-information-removal-policy.md`
- **reranker score:** `1.602890133857727`
- **chunk preview:** “GitHub Asks User to Make Changes. In most cases, we will contact the user who created the repository and give them an opportunity to delete or modify the private information specified in the request or to dispute the claim...”

#### Rank 4 — `S4`

- **title:** GitHub Research Program Terms
- **heading:** `B. Confidentiality`
- **source_path:** `Policies/github-terms/github-research-program-terms.md`
- **reranker score:** `0.5122251510620117`
- **chunk preview:** “If you are required by law, regulation or a valid binding order of a court of competent jurisdiction to disclose our Confidential Information, you may do so, but only if you notify us before you do...”

#### Rank 5 — `S5`

- **title:** GitHub Terms of Service
- **heading:** `M. Cancellation and Termination > 2. Upon Cancellation`
- **source_path:** `Policies/github-terms/github-terms-of-service.md`
- **reranker score:** `-0.06750062853097916`
- **chunk preview:** “We will retain and use your information as necessary to comply with our legal obligations, resolve disputes, and enforce our agreements, but barring legal requirements, we will delete your full profile and the Content of your repositories within 90 days...”

### Ground-truth reference

#### required_points

- GitHub's policy is to notify affected users about pending requests concerning their accounts or repositories before disclosure.
- Notification may be withheld when prohibited by law or court order, and may be delayed in rare exigent or ongoing-investigation circumstances.

#### supporting_snippets

- “It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.”

#### forbidden_claims

- GitHub always notifies an account owner before every disclosure without exception.

#### notes

The answer must preserve the legal-prohibition and delayed-notification exceptions.

### Human Diagnosis

Behavior:

- [ ] true model failure
- [ ] detector false positive
- [ ] unclear

Acceptable source:

- [ ] true citation/source failure
- [ ] eval acceptable_sources too narrow
- [ ] retrieval failure
- [ ] unclear

Required points:

- [ ] covered
- [ ] partial
- [ ] missing

Claim-level grounding:

- [ ] pass
- [ ] partial
- [ ] fail

Recommended action:

- [ ] no change
- [ ] adjust detector
- [ ] adjust eval ground truth
- [ ] adjust generator
- [ ] investigate retrieval

Reviewer notes:


---

## 4. Failure case: `ans_007`

### Case details

- **case id:** `ans_007`
- **source_case_id:** `ret_013`
- **category:** `broad`
- **expected_behavior:** `answer`
- **question:** When can GitHub restrict or shut down an account?
- **history:** `[]`
- **rewritten_query:** When can GitHub restrict or shut down an account?

### Generated answer

~~~text
GitHub can restrict or shut down an account in several circumstances described in the published policies:

- **Violation of terms (Community Code of Conduct context):** If a GitHub.com account is identified as violating the Terms of Service, GitHub will close the account [S4]. Accounts created to inquire about flagged or suspended accounts will also be removed [S4].
- **Underage users:** If GitHub learns or has reason to suspect a user is under 13, it will close the GitHub.com account [S4].
- **Sponsors program violations or sanctions:** GitHub may immediately suspend a Sponsored Developer Account for violating the Sponsors Additional Terms or the Agreement, or if the person is on a restricted trade list or located/resident in a comprehensively sanctioned country; failure to cure may result in termination [S2].
- **Sanctioned organizations:** If an organization is based in, or has sufficient ties to, a sanctioned territory/country for which GitHub lacks a U.S. government license, or otherwise appears subject to U.S. economic sanctions, the organization account and affiliated owner account will be restricted [S3].
- **Termination for convenience (Corporate Terms):** Either party may terminate an Order Form or Agreement without cause with at least 30 days' prior written notice [S1].

Note: The provided evidence does not specify a single comprehensive list of all grounds for account restriction or shutdown beyond these provisions.
~~~

### Deterministic checks

- `detected_behavior`: `abstain`
- `behavior_pass`: `false`
- `citation_validation_pass`: `true`
- `acceptable_source_hit`: `false`
- `forbidden_claim_matches`: `[]`
- `forbidden_claim_pass`: `true`
- `pipeline.overall_pipeline_success`: `true`

### Behavior failure evidence

- **expected_behavior:** `answer`
- **detected_behavior:** `abstain`
- **matched abstention regex:**

~~~regex
\b(?:the\s+)?(?:provided\s+)?evidence\s+(?:do|does)\s+not\s+(?:specify|state|provide|identify)\b
~~~

- **exact matched answer segment:** `The provided evidence does not specify`
- **containing answer text:** `Note: The provided evidence does not specify a single comprehensive list of all grounds for account restriction or shutdown beyond these provisions.`

### Citation / acceptable source material

#### A. Dataset acceptable_sources

| title | source_path | heading_contains |
|---|---|---|
| GitHub Terms of Service | `Policies/github-terms/github-terms-of-service.md` | `GitHub May Terminate` |
| GitHub Appeal and Reinstatement | `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` | `What are Appeals and Reinstatements?` |
| GitHub Community Guidelines | `Policies/github-terms/github-community-guidelines.md` | `What happens if someone violates GitHub's policies?` |

#### B. Model citation_ids

- `S4`
- `S2`
- `S3`
- `S1`

#### C. Actual cited sources

##### `S4`

- **title:** GitHub Community Code of Conduct
- **heading:** `Standards > _What is not Allowed_`
- **source_path:** `Policies/github-terms/github-community-code-of-conduct.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/github-terms/github-community-code-of-conduct.md
- **chunk_id:** `chunk_0ce99a6078cf37abe73d8a85`
- **chunk text / relevant snippet:** “If we learn or have reason to suspect that you are a user who is under the age of 13, we will unfortunately have to close your GitHub.com account... Additional free accounts created to inquire about flagged or suspended accounts in GitHub will be removed.”

##### `S2`

- **title:** GitHub Sponsors Additional Terms
- **heading:** `Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension.`
- **source_path:** `Policies/github-terms/github-sponsors-additional-terms.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/github-terms/github-sponsors-additional-terms.md
- **chunk_id:** `chunk_758f53f21830d6df5e81f763`
- **chunk text / relevant snippet:** “GitHub may suspend your Sponsored Developer Account immediately if you violate these Additional Terms or the Agreement in any way, or if you are placed on a restricted trade list or located in or ordinarily resident in a country or territory subject to comprehensive sanctions... Failure to correct or cure the cause for suspension may result in the termination of your Sponsored Developer Account.”

##### `S3`

- **title:** GitHub and Trade Controls
- **heading:** `Frequently asked questions > How are organization accounts impacted?`
- **source_path:** `Policies/other-site-policies/github-and-trade-controls.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-and-trade-controls.md
- **chunk_id:** `chunk_2899720d6a0761800653e2d4`
- **chunk text / relevant snippet:** “If an organization is based out of, or the key individuals or membership of an organization shows sufficient ties to, a sanctioned territory or country for which GitHub does not yet have a license from the U.S. government, or if the organization otherwise appears to be subject to U.S. economic sanctions, then the organization account and the affiliated owner account will be restricted.”

##### `S1`

- **title:** GitHub Corporate Terms of Service
- **heading:** `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation`
- **source_path:** `Policies/github-terms/github-corporate-terms-of-service.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/github-terms/github-corporate-terms-of-service.md
- **chunk_id:** `chunk_430ff1a4ccffd44ef3ea83bf`
- **chunk text / relevant snippet:** “Either Party may terminate an Order Form (if applicable) or this Agreement, without cause, upon at least thirty (30) days' prior written notice.”

#### D. Why acceptable_source_hit is false

对 4 个实际 cited sources 与 3 条 acceptable rules 的原始字段核对如下。`title` 不参与现有 matcher；matcher 要求至少一条 cited source 的 `source_path` 相同，并在规则有 `heading_contains` 时要求 cited heading 包含该文本。

| cited id | cited source_path | cited heading | 与任一 acceptable source_path 相同？ | cited heading 包含任一 heading_contains？ |
|---|---|---|---:|---:|
| `S4` | `Policies/github-terms/github-community-code-of-conduct.md` | `Standards > _What is not Allowed_` | 否 | 否 |
| `S2` | `Policies/github-terms/github-sponsors-additional-terms.md` | `Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension.` | 否 | 否 |
| `S3` | `Policies/other-site-policies/github-and-trade-controls.md` | `Frequently asked questions > How are organization accounts impacted?` | 否 | 否 |
| `S1` | `Policies/github-terms/github-corporate-terms-of-service.md` | `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation` | 否 | 否 |

没有 cited source 的 `source_path` 与任何 acceptable rule 相同，因此 matcher 在 heading 检查之前即跳过；列出的 cited headings 也与三条 `heading_contains` 均不同。最终 `acceptable_source_hit == false`。

### Retrieval evidence: reranked Top5

#### Rank 1 — `S1`

- **title:** GitHub Corporate Terms of Service
- **heading:** `K. Term; Termination; Suspension > 2. Termination for Convenience; Account Cancellation`
- **source_path:** `Policies/github-terms/github-corporate-terms-of-service.md`
- **reranker score:** `5.361840724945068`
- **chunk preview:** “Either Party may terminate an Order Form (if applicable) or this Agreement, without cause, upon at least thirty (30) days' prior written notice...”

#### Rank 2 — `S2`

- **title:** GitHub Sponsors Additional Terms
- **heading:** `Terms For Sponsored Developer > 5. Term and Termination. > 5.2. Suspension.`
- **source_path:** `Policies/github-terms/github-sponsors-additional-terms.md`
- **reranker score:** `5.351320266723633`
- **chunk preview:** “GitHub may suspend your Sponsored Developer Account immediately if you violate these Additional Terms or the Agreement in any way... Failure to correct or cure the cause for suspension may result in the termination...”

#### Rank 3 — `S3`

- **title:** GitHub and Trade Controls
- **heading:** `Frequently asked questions > How are organization accounts impacted?`
- **source_path:** `Policies/other-site-policies/github-and-trade-controls.md`
- **reranker score:** `4.84153938293457`
- **chunk preview:** “If an organization is based out of, or the key individuals or membership of an organization shows sufficient ties to, a sanctioned territory or country... the organization account and the affiliated owner account will be restricted.”

#### Rank 4 — `S4`

- **title:** GitHub Community Code of Conduct
- **heading:** `Standards > _What is not Allowed_`
- **source_path:** `Policies/github-terms/github-community-code-of-conduct.md`
- **reranker score:** `4.495421409606934`
- **chunk preview:** “If we learn or have reason to suspect that you are a user who is under the age of 13, we will unfortunately have to close your GitHub.com account... Additional free accounts created to inquire about flagged or suspended accounts in GitHub will be removed.”

#### Rank 5 — `S5`

- **title:** GitHub Terms of Service
- **heading:** `M. Cancellation and Termination`
- **source_path:** `Policies/github-terms/github-terms-of-service.md`
- **reranker score:** `4.420710563659668`
- **chunk preview:** “Short version: You may close your Account at any time. If you do, we'll treat your information responsibly.”

Top5 中的 `S5` 与第一条 acceptable rule 的 `source_path` 相同，但其 heading 为 `M. Cancellation and Termination`，不包含 `GitHub May Terminate`；并且模型的 `citation_ids` 不包含 `S5`。

### Ground-truth reference

#### required_points

- GitHub's Terms of Service reserve a broad right to suspend or terminate access to all or part of the website, with or without cause or notice.
- Policy enforcement may include suspending a user account or organization, and affected users may have an appeal or reinstatement process.

#### supporting_snippets

- “GitHub has the right to suspend or terminate your access to all or any part of the Website at any time, with or without cause, with or without notice, effective immediately. GitHub reserves the right to refuse service to anyone for any reason at any time.”
- “GitHub provides an internal complaint-handling process where users can submit requests for reinstatement or provide additional information to appeal a moderation decision.”
- “Where we have decided that moderation action is warranted, these are some of the ways we may respond:”

#### forbidden_claims

- The listed examples are an exhaustive statement of every circumstance in which GitHub can restrict or terminate an account.

#### notes

This is intentionally broad. A good answer may summarize supported examples but should not claim that its list is exhaustively complete.

### Human Diagnosis

Behavior:

- [ ] true model failure
- [ ] detector false positive
- [ ] unclear

Acceptable source:

- [ ] true citation/source failure
- [ ] eval acceptable_sources too narrow
- [ ] retrieval failure
- [ ] unclear

Required points:

- [ ] covered
- [ ] partial
- [ ] missing

Claim-level grounding:

- [ ] pass
- [ ] partial
- [ ] fail

Recommended action:

- [ ] no change
- [ ] adjust detector
- [ ] adjust eval ground truth
- [ ] adjust generator
- [ ] investigate retrieval

Reviewer notes:


---

## 5. Failure case: `ans_multi_002`

### Case details

- **case id:** `ans_multi_002`
- **source_case_id:** `multi_004`
- **category:** `multi_turn`
- **expected_behavior:** `answer`
- **question:** What if it is for security research?
- **history:**

~~~json
[
  {
    "role": "user",
    "content": "Does GitHub prohibit repositories that support malware or exploit campaigns?"
  },
  {
    "role": "assistant",
    "content": "GitHub prohibits using the platform in direct support of unlawful attacks that cause technical harm."
  }
]
~~~

- **rewritten_query:** Does GitHub's prohibition on using the platform in direct support of unlawful attacks that cause technical harm apply to security research?

### Generated answer

~~~text
GitHub allows dual-use content and supports posting content used for research into vulnerabilities, malware, or exploits, because publication and distribution of such content has educational value and provides a net benefit to the security community; GitHub assumes positive intention and use of these projects to drive ecosystem improvements [S1].

That said, the allowance is not unlimited. In rare cases of very widespread abuse of dual-use content, GitHub may restrict access to that specific instance to disrupt an ongoing unlawful attack or malware campaign leveraging GitHub as an exploit or malware CDN—typically by putting the content behind authentication, and as a last resort by disabling access or full removal where that isn't possible (e.g., gists) [S1]. Such restrictions are temporary where feasible and are not meant to purge or perpetually restrict specific dual-use content or its copies [S1]. GitHub will contact project owners about restrictions where possible, and an appeals process exists if you believe your content was unduly restricted [S1].

GitHub also recommends (but does not require) that repository owners posting potentially harmful security research content clearly identify and describe any potentially harmful content in a disclaimer in the README.md or source code comments, and provide a preferred contact method for third-party abuse inquiries via a SECURITY.md file [S1].

One scope limit to note: GitHub considers the npm registry to be a platform used primarily for installation and run-time use of code, and not for research [S1].

The provided published policies do not specify further conditions, review criteria, or approval processes for security research beyond the above.
~~~

### Deterministic checks

- `detected_behavior`: `abstain`
- `behavior_pass`: `false`
- `citation_validation_pass`: `true`
- `acceptable_source_hit`: `true`
- `forbidden_claim_matches`: `[]`
- `forbidden_claim_pass`: `true`
- `pipeline.overall_pipeline_success`: `true`

### Behavior failure evidence

- **expected_behavior:** `answer`
- **detected_behavior:** `abstain`
- **matched abstention regex:**

~~~regex
\b(?:the\s+)?provided(?:\s+published|\s+github)?\s+policies\s+(?:do|does)\s+not\s+(?:specify|state|provide|identify)\b
~~~

- **exact matched answer segment:** `The provided published policies do not specify`
- **containing answer text:** `The provided published policies do not specify further conditions, review criteria, or approval processes for security research beyond the above.`

### Citation / acceptable source material

#### A. Dataset acceptable_sources

| title | source_path | heading_contains |
|---|---|---|
| GitHub Active Malware or Exploits | `Policies/acceptable-use-policies/github-active-malware-or-exploits.md` | `(empty)` |
| GitHub Acceptable Use Policies | `Policies/acceptable-use-policies/github-acceptable-use-policies.md` | `Site Access and Safety` |

#### B. Model citation_ids

- `S1`

#### C. Actual cited sources

##### `S1`

- **title:** GitHub Active Malware or Exploits
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-active-malware-or-exploits.md
- **chunk_id:** `chunk_7d54462de0e9154ce55d108b`
- **chunk text / relevant snippet:**

> We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers. Technical harms means overconsumption of resources, physical damage, downtime, denial of service, or data loss, with no implicit or explicit dual-use purpose prior to the abuse occurring.
>
> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community. We assume positive intention and use of these projects to promote and drive improvements across the ecosystem.
>
> In rare cases of very widespread abuse of dual-use content, we may restrict access to that specific instance of the content to disrupt an ongoing unlawful attack or malware campaign that is leveraging the GitHub platform as an exploit or malware CDN.

#### D. acceptable_source_hit result material

`acceptable_source_hit == true`。实际 cited `S1` 的 `source_path` 与第一条 acceptable rule 相同；该规则的 `heading_contains` 为空，因此路径匹配后即返回 true。

### Retrieval evidence: reranked Top5

#### Rank 1 — `S1`

- **title:** GitHub Active Malware or Exploits
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
- **reranker score:** `7.3959150314331055`
- **chunk preview:** “We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms... Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits...”

#### Rank 2 — `S2`

- **title:** GitHub Acceptable Use Policies
- **heading:** `5. Site Access and Safety`
- **source_path:** `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- **reranker score:** `5.671246528625488`
- **chunk preview:** “We do not allow content or activity on GitHub that directly supports unlawful active attack or malware campaigns that are causing technical harms... with no implicit or explicit dual-use purpose prior to the abuse occurring...”

#### Rank 3 — `S3`

- **title:** GitHub Terrorism and Violent Extremism
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/acceptable-use-policies/github-terrorism-and-violent-extremism.md`
- **reranker score:** `1.8634941577911377`
- **chunk preview:** “GitHub does not allow any content or conduct on GitHub that furthers terrorism or violent extremism (TVE). We will remove content and may ban accounts affiliated with TVE groups or individuals...”

#### Rank 4 — `S4`

- **title:** GitHub Bullying and Harassment
- **heading:** `(empty heading_path)`
- **source_path:** `Policies/acceptable-use-policies/github-bullying-and-harassment.md`
- **reranker score:** `1.098008632659912`
- **chunk preview:** “We do not tolerate harassment, bullying, or abuse of any kind, whether directly or by encouraging others to take part in the prohibited conduct...”

#### Rank 5 — `S5`

- **title:** GitHub Acceptable Use Policies
- **heading:** `2. User Safety`
- **source_path:** `Policies/acceptable-use-policies/github-acceptable-use-policies.md`
- **reranker score:** `0.6683125495910645`
- **chunk preview:** “We do not allow content or activity on GitHub that is unlawful or promotes unlawful activities; is sexually obscene or relates to sexual exploitation or abuse...; is libelous, defamatory, or fraudulent...”

### Ground-truth reference

#### required_points

- GitHub allows dual-use vulnerability, malware, or exploit content used for legitimate security research because it can have educational and security-community value.
- The allowance does not protect use of GitHub in direct support of unlawful attacks that cause technical harm.

#### supporting_snippets

- “We do not allow anyone to use our platform in direct support of unlawful attacks that cause technical harms, such as using GitHub as a means to deliver malicious executables or as attack infrastructure, for example by organizing denial of service attacks or managing command and control servers.”
- “Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.”

#### forbidden_claims

- All security research involving malware or exploits is prohibited.
- Labeling content as security research makes active attack infrastructure permissible.

#### notes

The answer eval input must preserve the history because the latest question does not identify what “it” refers to.

### Human Diagnosis

Behavior:

- [ ] true model failure
- [ ] detector false positive
- [ ] unclear

Acceptable source:

- [ ] true citation/source failure
- [ ] eval acceptable_sources too narrow
- [ ] retrieval failure
- [ ] unclear

Required points:

- [ ] covered
- [ ] partial
- [ ] missing

Claim-level grounding:

- [ ] pass
- [ ] partial
- [ ] fail

Recommended action:

- [ ] no change
- [ ] adjust detector
- [ ] adjust eval ground truth
- [ ] adjust generator
- [ ] investigate retrieval

Reviewer notes:


---

## 6. Failure case: `ans_unsup_002`

### Case details

- **case id:** `ans_unsup_002`
- **source_case_id:** `ret_023`
- **category:** `unsupported`
- **expected_behavior:** `abstain`
- **question:** In which exact physical data center is my specific repository stored?
- **history:** `[]`
- **rewritten_query:** In which exact physical data center is my specific repository stored?

### Generated answer

~~~text
The provided published policies do not specify the exact physical data center where a specific repository is stored. The evidence describes repositories generally as project folders containing files and revision history [S1], and addresses legal-process handling for repository data [S4], but it does not identify any physical storage location for an individual repository.
~~~

### Deterministic checks

- `detected_behavior`: `abstain`
- `behavior_pass`: `true`
- `citation_validation_pass`: `true`
- `acceptable_source_hit`: `false`
- `forbidden_claim_matches`: `[]`
- `forbidden_claim_pass`: `true`
- `pipeline.overall_pipeline_success`: `true`

### Behavior failure evidence

不适用：`behavior_pass == true`。

### Citation / acceptable source material

#### A. Dataset acceptable_sources

| title | source_path | heading_contains |
|---|---|---|
| GitHub General Privacy Statement | `Policies/privacy-policies/github-general-privacy-statement.md` | `International data transfers` |

#### B. Model citation_ids

- `S1`
- `S4`

#### C. Actual cited sources

##### `S1`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `GitHub terminology`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- **chunk_id:** `chunk_6bc363aa4e3f40702deda958`
- **chunk text / relevant snippet:** “Repositories on GitHub—which may be public or private—are most commonly used for software development projects, but are also often used to work on content of all kinds... A repository is one of the most basic GitHub elements. They may be easiest to imagine as a project's folder. A repository contains all of the project files (including documentation), and stores each file's revision history.”

##### `S4`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `Submitting requests`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **source_url:** https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- **chunk_id:** `chunk_c24304bfd4023a6fd2b89ca1`
- **chunk text / relevant snippet:** “Please make your requests as specific and narrow as possible, including the following information: Full information about authority issuing the request for information; the name and badge/ID of the responsible agent; an official email address and contact phone number; the user, organization, repository name(s) of interest; the URLs of any pages, gists or files of interest; the description of the types of records you need.”

#### D. Why acceptable_source_hit is false

| cited id | cited source_path | cited heading | acceptable source_path | required heading | raw result |
|---|---|---|---|---|---|
| `S1` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | `GitHub terminology` | `Policies/privacy-policies/github-general-privacy-statement.md` | `International data transfers` | source_path 不同；heading 不同 |
| `S4` | `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` | `Submitting requests` | `Policies/privacy-policies/github-general-privacy-statement.md` | `International data transfers` | source_path 不同；heading 不同 |

两条 cited source 的 `source_path` 均与 acceptable rule 不同，因此 matcher 在 heading 检查之前即跳过；列出的 cited heading 也不包含 `International data transfers`。最终 `acceptable_source_hit == false`。

### Retrieval evidence: reranked Top5

#### Rank 1 — `S1`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `GitHub terminology`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **reranker score:** `-6.292181968688965`
- **chunk preview:** “GitHub hosts millions of data repositories using the Git version control system... A repository contains all of the project files (including documentation), and stores each file's revision history.”

#### Rank 2 — `S2`

- **title:** GitHub and Trade Controls
- **heading:** `Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)?`
- **source_path:** `Policies/other-site-policies/github-and-trade-controls.md`
- **reranker score:** `-9.344661712646484`
- **chunk preview:** “Our understanding of the law does not give us the option to allow downloads or deletion of private repository content, until otherwise authorized by the U.S. government, for specific categories of trade restrictions...”

#### Rank 3 — `S3`

- **title:** GitHub Marketplace Developer Agreement
- **heading:** `Addendum 1: Data Protection Addendum`
- **source_path:** `Policies/github-terms/github-marketplace-developer-agreement.md`
- **reranker score:** `-9.54139518737793`
- **chunk preview:** “Developer's privacy policy must provide End Users all legally required information regarding access, collection, storage, and processing purpose of Personal Data, with whom the Personal Data is shared, and in which country or countries the Personal Data will be stored...”

#### Rank 4 — `S4`

- **title:** Guidelines for Legal Requests of User Data
- **heading:** `Submitting requests`
- **source_path:** `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`
- **reranker score:** `-10.194635391235352`
- **chunk preview:** “Please make your requests as specific and narrow as possible, including... the user, organization, repository name(s) of interest; the URLs of any pages, gists or files of interest; the description of the types of records you need.”

#### Rank 5 — `S5`

- **title:** GitHub General Privacy Statement
- **heading:** `Private repositories: GitHub Access`
- **source_path:** `Policies/privacy-policies/github-general-privacy-statement.md`
- **reranker score:** `-10.417778015136719`
- **chunk preview:** “If your GitHub account has private repositories, our ability and rights to access private repository information is set forth in Section E (Private Repositories) of the GitHub Terms of Service.”

Top5 中的 `S5` 与 acceptable rule 的 `source_path` 相同，但 heading 为 `Private repositories: GitHub Access`，不包含 `International data transfers`；并且模型的 `citation_ids` 不包含 `S5`。

### Ground-truth reference

#### required_points

- The provided published policies do not identify the exact physical data center storing a specific repository.
- The privacy statement describes Personal Data being stored and processed across broad regions and countries, not a repository-specific facility.

#### supporting_snippets

- “GitHub stores and processes Personal Data in a variety of locations, including your local region, the United States, and other countries where GitHub, its affiliates, subsidiaries, or subprocessors have operations.”

#### forbidden_claims

- The repository is stored in a United States data center.
- The repository is stored in Virginia.
- The repository is stored in Seattle.
- The user's region determines the exact data center containing the repository.

#### notes

The snippet discusses broad Personal Data processing locations. It must not be converted into a claim about the exact facility holding a particular repository.

### Human Diagnosis

Behavior:

- [ ] true model failure
- [ ] detector false positive
- [ ] unclear

Acceptable source:

- [ ] true citation/source failure
- [ ] eval acceptable_sources too narrow
- [ ] retrieval failure
- [ ] unclear

Required points:

- [ ] covered
- [ ] partial
- [ ] missing

Claim-level grounding:

- [ ] pass
- [ ] partial
- [ ] fail

Recommended action:

- [ ] no change
- [ ] adjust detector
- [ ] adjust eval ground truth
- [ ] adjust generator
- [ ] investigate retrieval

Reviewer notes:

