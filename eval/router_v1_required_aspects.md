# Router V1 Required-Aspects Truth (Frozen)

> Required aspects define minimum answer content.  
> Optional context does not affect completeness or oracle winner.  
> Listed supporting evidence is verified but not exhaustive.

- version: `router_v1_required_aspects`
- status: `frozen`
- benchmark: `eval/router_benchmark_v1.json` (`a345ccfd8dabadedd41ac1abc341a079709d3bbc699e4ea7b3696a06f76acf16`)
- corpus commit: `b9578b546d2506febda1da2cd7431644d58e512c`
- source draft: `eval/router_v1_required_aspects_draft.json` (`c2f766b0610c37b899990d0eb8d6bbb229aa25add3a7f2a041f66686af07f547`)
- independent audit: `eval/router_v1_required_aspects_deepseek_audit.md` (`b815ed0a4a7f8de4c5aa4e3f093032ca9fc827337cb2fa14bd729de9af81ce1f`)
- change set: `eval/router_v1_required_aspects_audit_changes.json` (`9c4f373ed9dcc030d39d7fffa099dc15afe3008a046a8d5fa67ff2163e0c2792`)
- truth_frozen_timestamp: `2026-09-27T14:25:39Z`
- truth_created_before_router_v1_outputs: `true`
- outcome_blind_at_freeze: `true`
- required aspects: `66`
- optionalized aspects: `4`
- corpus gaps: `0`
- supporting evidence semantics: `verified_examples_not_exhaustive` (semantic answer requirements, not unique chunk gold)

## Coverage

| query | required | optional | corpus gap |
|---|---|---|---|
| router_001 | 4 | 1 | 0 |
| router_002 | 3 | 1 | 0 |
| router_003 | 4 | 0 | 0 |
| router_004 | 3 | 0 | 0 |
| router_005 | 3 | 0 | 0 |
| router_006 | 4 | 1 | 0 |
| router_007 | 4 | 0 | 0 |
| router_008 | 2 | 0 | 0 |
| router_009 | 3 | 0 | 0 |
| router_010 | 3 | 0 | 0 |
| router_011 | 4 | 1 | 0 |
| router_012 | 3 | 0 | 0 |
| router_013 | 4 | 1 | 0 |
| router_014 | 3 | 0 | 0 |
| router_015 | 3 | 0 | 0 |
| router_016 | 3 | 0 | 0 |
| router_017 | 3 | 0 | 0 |
| router_018 | 3 | 0 | 0 |
| router_019 | 3 | 0 | 0 |
| router_020 | 4 | 1 | 0 |

## Per-query contract

### router_001

**Query:** Someone copied my home address from a public website into a GitHub issue and urged others to contact me. Can I report this as a privacy violation, and is the private-information removal request the right way to get it taken down?

**Required aspects (4):**

- `router_001_a1` — GitHub’s privacy rule covers posting another person’s physical address or other private location information.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md | (document introduction) | `chunk_36c8fa4bcb4dccbdc3bbb72c`
- `router_001_a2` — GitHub considers context and whether the information is publicly available elsewhere; public availability does not by itself settle the policy question.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md | (document introduction) | `chunk_36c8fa4bcb4dccbdc3bbb72c`
- `router_001_a3` — Sharing publicly available information with intent to harass or incite abuse may violate GitHub’s harassment rule.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md | (document introduction) | `chunk_36c8fa4bcb4dccbdc3bbb72c`
- `router_001_a4` — The private-information removal process requires content that should have remained confidential and whose disclosure poses a specific or targeted security risk.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | What is Private Information? | `chunk_fd1a8855ee650c1195777567`

**Optional context (1):**

- (draft optional) — 移除投诉还需指出具体文件、行号与风险。  [origin: `pre_existing_draft_optional_context`]

**Corpus gap:** none

### router_002

**Query:** A repository contains no intimate images, but it advertises a tool for making realistic sexual images of real people without their consent. Does hosting only the tool put the project outside GitHub's policy?

**Required aspects (3):**

- `router_002_a1` — GitHub prohibits projects designed to encourage or support synthetic-media tools for making sexually explicit media of people without consent.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md | (document introduction) | `chunk_e921fe7a8e1eeb16ec85d0b4`
- `router_002_a2` — The non-consensual intimate imagery rule includes realistic digitally altered or synthetic sexual depictions made without the person’s consent.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-non-consensual-intimate-imagery.md | (document introduction) | `chunk_eebcff7d8379f37aaf1bf06f`
- `router_002_a3` — GitHub assesses such projects in context, including configuration, marketing, README or other documentation, external links, and maintainer support.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md | (document introduction) | `chunk_e921fe7a8e1eeb16ec85d0b4`

**Optional context (1):**

- (draft optional) — 已发布影像在罕见公共利益情境下可能逐案审查；本题未描述此情境。  [origin: `pre_existing_draft_optional_context`]

**Corpus gap:** none

### router_003

**Query:** A contributor keeps opening empty pull requests and new accounts after I block them, flooding reviewers with notifications. Which GitHub conduct rules apply, and can staff act beyond moderation of my repository?

**Required aspects (4):**

- `router_003_a1` — Empty or meaningless pull requests and excessive notifications are examples of prohibited significant or continual disruption.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md | (document introduction) | `chunk_65ff616040be6ec5bdfe0770`
- `router_003_a2` — Creating alternative accounts specifically to evade moderation by GitHub staff or users is identified as harassment-related conduct.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-bullying-and-harassment.md | (document introduction) | `chunk_23acf65f48bfbc0fd2b142a9`
- `router_003_a3` — Disruptive conduct may also be bullying or harassment depending on its nature and severity; it is not automatically harassment.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md | (document introduction) | `chunk_65ff616040be6ec5bdfe0770`
- `router_003_a4` — Maintainers may moderate their projects, and GitHub staff may take further restrictive action against disruptive accounts.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md | (document introduction) | `chunk_65ff616040be6ec5bdfe0770`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_004

**Query:** Our museum repository explains the history of nude artwork, but its account avatar previews one of the images. Does the educational context mean GitHub must leave both the repository and avatar visible to everyone?

**Required aspects (3):**

- `router_004_a1` — GitHub may allow nudity in artistic, educational, historical, or journalistic contexts.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-sexually-obscene-content.md | (document introduction) | `chunk_f25af672289856012d211dad`
- `router_004_a2` — Sexually suggestive content in profiles or other social contexts receives particular scrutiny when it mainly solicits an erotic or shocking response.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-sexually-obscene-content.md | (document introduction) | `chunk_f25af672289856012d211dad`
- `router_004_a3` — Even when context supports allowing material, GitHub may limit viewing by requiring users to opt in.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-sexually-obscene-content.md | (document introduction) | `chunk_f25af672289856012d211dad`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_005

**Query:** I'm posting a satirical graphic about a medical claim. Its README labels it as satire and links to sources, but the image could circulate without that context. How does GitHub assess whether it crosses the misinformation policy?

**Required aspects (3):**

- `router_005_a1` — The misinformation rule reaches inaccurate or unsupported medical claims likely to endanger public health or safety.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-misinformation-and-disinformation.md | (document introduction) | `chunk_f9ddd26bbbc61c34bb71774a`
- `router_005_a2` — GitHub generally allows parody and satire consistent with its Acceptable Use Policies, rather than automatically exempting anything labeled satire.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-misinformation-and-disinformation.md | (document introduction) | `chunk_f9ddd26bbbc61c34bb71774a`
- `router_005_a3` — GitHub considers how context orients viewers, including clear disclaimers, credible citations, and details clarifying accuracy.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-misinformation-and-disinformation.md | (document introduction) | `chunk_f9ddd26bbbc61c34bb71774a`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_006

**Query:** We published an exploit demo for defensive research, and an active malware campaign now links to its download. Could GitHub limit that release without banning every copy, and how could we challenge a restriction we think is mistaken?

**Required aspects (4):**

- `router_006_a1` — GitHub generally allows dual-use exploit and malware research content for its educational and security value.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-active-malware-or-exploits.md | (document introduction) | `chunk_7d54462de0e9154ce55d108b`
- `router_006_a2` — In rare widespread abuse during an active attack or malware campaign, GitHub may restrict the specific abused instance.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-active-malware-or-exploits.md | (document introduction) | `chunk_7d54462de0e9154ce55d108b`
- `router_006_a3` — Such a restriction is temporary where feasible and is not meant to purge all copies of the dual-use content permanently.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-active-malware-or-exploits.md | (document introduction) | `chunk_7d54462de0e9154ce55d108b`
- `router_006_a5` — A user who believes content was unduly restricted may appeal and provide grounds for a different decision.
  - support_type: `combined`
  - evidence: Policies/acceptable-use-policies/github-appeal-and-reinstatement.md | How this works | `chunk_5d1188bc9474b578388e2ddd`
  - evidence: Policies/acceptable-use-policies/github-appeal-and-reinstatement.md | How this works/Appeals | `chunk_56264636771e77075a782b6d`

**Optional context (1):**

- `router_006_a4` — A restriction usually puts content behind authentication; disabling or removal is a last resort when that is not possible.  [origin: `optionalized_from_required`]
  - evidence: Policies/acceptable-use-policies/github-active-malware-or-exploits.md | (document introduction) | `chunk_7d54462de0e9154ce55d108b`

**Corpus gap:** none

### router_007

**Query:** An account uses our registered company name as its handle, copies our logo, and calls itself parody. Is the matching name enough to reclaim the handle, or what would GitHub look at?

**Required aspects (4):**

- `router_007_a1` — A username matching a registered trademark is not by itself a policy violation or automatic right to reclaim it.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-trademark-policy.md | What is not a GitHub Trademark Policy Violation? | `chunk_19600b091f62ca0ede3450a2`
- `router_007_a2` — Use of a company name or logo may violate trademark policy when it may confuse others about brand or business affiliation.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-trademark-policy.md | What is a GitHub Trademark Policy Violation? | `chunk_e21d5efa444988a6ee52dc30`
- `router_007_a3` — Impersonation depends on misleading context; a similar name alone is not necessarily impersonation, and parody may be allowed.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-impersonation.md | (document introduction) | `chunk_0d2d5abd2784cfcf630269b4`
- `router_007_a4` — After reviewing a registered-mark complaint, GitHub may release a username for the trademark holder’s active use; release is discretionary.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-trademark-policy.md | How Does GitHub Respond To Reported Trademark Policy Violations? | `chunk_f7c393d8c6398f15f8c9a7d1`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_008

**Query:** Our README, package description, and profile mention another company's product to explain compatibility, without claiming affiliation. When would that use become a GitHub trademark-policy problem?

**Required aspects (2):**

- `router_008_a1` — Trademark use becomes a GitHub policy issue when it may mislead or confuse others about brand or business affiliation.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-trademark-policy.md | What is a GitHub Trademark Policy Violation? | `chunk_e21d5efa444988a6ee52dc30`
- `router_008_a2` — Mentioning another’s mark is not automatically a violation; the policy distinguishes use unrelated to the registered product or service from confusing use.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-trademark-policy.md | What is not a GitHub Trademark Policy Violation? | `chunk_19600b091f62ca0ede3450a2`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_009

**Query:** I found a vulnerability in GitHub and reporting it may involve conduct normally restricted by its site policies. Does the bug bounty safe harbor cover that research, and does it let me test a connected third-party service?

**Required aspects (3):**

- `router_009_a1` — Good-faith research within GitHub’s bug bounty policy receives the stated legal safe-harbor protection, subject to the program’s scope.
  - support_type: `direct`
  - evidence: Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md | 1. Safe Harbor Terms | `chunk_e0d354aeaa7beb50005833bb`
- `router_009_a2` — GitHub waives otherwise inconsistent site-policy restrictions only for research consistent with the bug bounty program and for that limited purpose.
  - support_type: `direct`
  - evidence: Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md | 3. Limited Waiver of Other Site Policies | `chunk_d5357e5db301e01f2d4c408f`
- `router_009_a3` — GitHub cannot authorize testing of a connected third-party service or bind that third party with its own safe harbor.
  - support_type: `direct`
  - evidence: Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md | 2. Third Party Safe Harbor | `chunk_943f62cca2ec5fdcf5f38e8c`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_010

**Query:** A DMCA notice identifies one file in my repository and one part of a published package. Can I edit both before GitHub disables anything, and what must I tell GitHub after making changes?

**Required aspects (3):**

- `router_010_a1` — For a notice targeting only part of a repository, GitHub generally gives its creator approximately one business day to delete or modify the identified content before disabling the repository.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/dmca-takedown-policy.md | A. How Does This Actually Work? | `chunk_80d71a13ddfac8eb977f9541`
- `router_010_a2` — Because packages are immutable, an allegedly infringing part can require disabling the whole package, with possible reinstatement after removal of that part.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/dmca-takedown-policy.md | A. How Does This Actually Work? | `chunk_80d71a13ddfac8eb977f9541`
- `router_010_a3` — A repository user who makes the specified changes must tell GitHub within the approximately one-business-day window; GitHub verifies them and notifies the rightsholder.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/dmca-takedown-policy.md | A. How Does This Actually Work? | `chunk_80d71a13ddfac8eb977f9541`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_011

**Query:** A repository exposes our internal network diagram and republishes our copyrighted manual. Should I put both into one private-information removal request, and what would GitHub need to assess each?

**Required aspects (4):**

- `router_011_a1` — An internal network diagram fits private-information removal only if its exposure poses a specific organizational security risk.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | What is Private Information?/Private information removal requests are appropriate for: | `chunk_503d0f8451cd132a55e45b74`
- `router_011_a3` — A private-information request must explain how each identified item poses a concrete security risk, beyond simply asserting risk.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | Sending A Private Information Removal Request/Your Request Must Include: | `chunk_0cc6709199187f11f4436f08`
- `router_011_a4` — A complaint about a copyrighted manual belongs under the DMCA process, not private-information removal.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | What is Private Information?/Private information removal requests are _not_ appropriate for: | `chunk_d6d1c627931350dcab91a60d`
- `router_011_a5` — GitHub asks for private-information and potentially infringing-content requests separately because it cannot process them simultaneously.
  - support_type: `direct`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | Things to Know | `chunk_a761f910df2bb1e22f5a4020`

**Optional context (1):**

- `router_011_a2` — A private-information request must identify a working link to each file and the specific lines containing the information.  [origin: `optionalized_from_required`]
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | Sending A Private Information Removal Request/Your Request Must Include: | `chunk_0cc6709199187f11f4436f08`
  - evidence: Policies/content-removal-policies/github-private-information-removal-policy.md | Sending A Private Information Removal Request/Your Request Must Include: | `chunk_0cc6709199187f11f4436f08`

**Corpus gap:** none

### router_012

**Query:** I found a notice naming my project in GitHub's public government-takedowns repository. Does that mean GitHub decided my project was unlawful, and what does the listing actually tell readers?

**Required aspects (3):**

- `router_012_a1` — A public government-takedowns notice establishes that GitHub received it on the indicated date.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | What does it mean if we post a notice in our gov-takedowns repository? | `chunk_b5d910ef2bfc9d7ef2df4802`
- `router_012_a2` — Publishing the notice does not mean the content was unlawful, the user did wrong, or GitHub endorses the claim’s merits.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | What does it mean if we post a notice in our gov-takedowns repository? | `chunk_b5d910ef2bfc9d7ef2df4802`
- `router_012_a3` — GitHub posts government takedown notices for transparency about what is withheld and why.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | Why do we publicly post takedown notices? | `chunk_cd467ee375fec67040db1e33`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_013

**Query:** A government office says my public repository is illegal locally and also wants private data from my account. Does its content-takedown request give it that data, and how are the two requests handled?

**Required aspects (4):**

- `router_013_a2` — For a complete government takedown request, GitHub notifies affected users of the allegation and permits appeal.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | What happens when we receive a complete takedown request from a government? | `chunk_ef6899bc1eb9e4fe063bec90`
- `router_013_a3` — For a complete government takedown request, GitHub limits geographic scope when possible and posts the official request publicly.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | What happens when we receive a complete takedown request from a government? | `chunk_ef6899bc1eb9e4fe063bec90`
- `router_013_a4` — A content-takedown request does not itself authorize disclosure of non-public account data; that requires consent or valid legal process, subject to limited emergency disclosure.
  - support_type: `combined`
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | How to submit a government takedown request | `chunk_a57209acbc132cc6e16c7234`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | Disclosure of non-public information | `chunk_e38e8b117bf75ca2426fb8a0`
- `router_013_a5` — Private repository contents require a search warrant under the user-data guidelines.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | Disclosure of non-public information | `chunk_30ab6464817b7b0946abaad0`

**Optional context (1):**

- `router_013_a1` — A complete government content-takedown request must come from a relevant official agency, identify illegal content, and specify the local legal basis.  [origin: `optionalized_from_required`]
  - evidence: Policies/other-site-policies/github-government-takedown-policy.md | How to submit a government takedown request | `chunk_a57209acbc132cc6e16c7234`

**Corpus gap:** none

### router_014

**Query:** Police say they need my private repository immediately to prevent serious harm. Could GitHub disclose its contents under the emergency exception without a warrant, and would I be told first?

**Required aspects (3):**

- `router_014_a1` — In a qualifying emergency involving danger of death or serious physical injury, GitHub may disclose only limited necessary information after verifying the law-enforcement request.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | Disclosure of non-public information | `chunk_30ab6464817b7b0946abaad0`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | Disclosure of non-public information | `chunk_30ab6464817b7b0946abaad0`
- `router_014_a2` — Even in that emergency, GitHub says it will not disclose private repository contents without a search warrant.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | Disclosure of non-public information | `chunk_30ab6464817b7b0946abaad0`
- `router_014_a3` — GitHub generally gives affected owners notice before disclosure, but may delay it in rare exigent circumstances to prevent death or serious harm or due to an ongoing investigation.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md | We will notify any affected account owners | `chunk_35fd87021964946f76efbd5f`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_015

**Query:** I use a personal account and keep code in a private repository, but paste a snippet into a GitHub AI feature. Does “private” prevent GitHub from using that input to improve AI, and what changes if I opt out?

**Required aspects (3):**

- `router_015_a1` — GitHub treats private repository contents as confidential and says it will not otherwise use them to develop or improve the Service unless provided as AI Feature Input.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-terms-of-service.md | E. Private Repositories/3. Access | `chunk_82b71e1d710271179f8b4bdd`
- `router_015_a2` — For an individual license, AI Inputs and Outputs may be used to improve AI unless the user opts out through account settings.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-terms-of-service.md | J. AI Features, Training, and Your Data/3. Development and Improvement Using Your Input and Output | `chunk_5bd8f67a21c277adbd0e92cd`
- `router_015_a3` — The opt-out stops the specified collection or use of Inputs and Outputs from its effective date forward, not retroactively.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-terms-of-service.md | J. AI Features, Training, and Your Data/3. Development and Improvement Using Your Input and Output | `chunk_5bd8f67a21c277adbd0e92cd`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_016

**Query:** Our paid Marketplace app was disabled for a policy reason halfway through its annual term. Who should notify us, does payment guarantee continued access, and are we owed a partial refund?

**Required aspects (3):**

- `router_016_a1` — GitHub may block or disable a Marketplace developer product for policy reasons and will work with its Product Provider to notify affected users.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | H. Developer Product Blocking | `chunk_53cfaee79a6c3b7ee9eed1d1`
- `router_016_a2` — Monthly or yearly Marketplace purchases are billed in advance and non-refundable, with no refunds or credits for partial or unused months under the terms.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | D. Payment, Billing Schedule, and Cancellation | `chunk_1c0bd6feab4c1cdf6411559c`
- `router_016_a3` — Because GitHub may block or disable a Developer Product for legal or policy reasons, paying for a paid Marketplace term does not guarantee continued access.
  - support_type: `combined`
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | D. Payment, Billing Schedule, and Cancellation | `chunk_1c0bd6feab4c1cdf6411559c`
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | H. Developer Product Blocking | `chunk_53cfaee79a6c3b7ee9eed1d1`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_017

**Query:** I want to thank Sponsors by displaying their logos in my README and Sponsor content, then promote their products in other users' issue threads. Where does GitHub draw the line on that kind of promotion?

**Required aspects (3):**

- `router_017_a1` — Sponsored developers may display Sponsors’ names or logos, but Sponsored Developer Content must not primarily be advertising.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-sponsors-additional-terms.md | Terms For Sponsored Developer/2. Sponsored Developer Obligations./2.3. Content Monetization./2.3.3. Advertising. | `chunk_612778d80d7c5c0b6e3e95ae`
- `router_017_a2` — Project-related static images, links, and promotional text may appear in an account README or project description, provided advertising is not its primary focus.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-acceptable-use-policies.md | 10. Advertising on GitHub | `chunk_98cf35fb3afbd05cb943b94b`
- `router_017_a3` — GitHub prohibits advertising in other users’ accounts, including monetized or excessive bulk content in their issues.
  - support_type: `direct`
  - evidence: Policies/acceptable-use-policies/github-acceptable-use-policies.md | 10. Advertising on GitHub | `chunk_98cf35fb3afbd05cb943b94b`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_018

**Query:** At a GitHub event, staff are filming the room while another attendee records me after I say no. Do the same consent rules apply to both, and how can I report the attendee's conduct?

**Required aspects (3):**

- `router_018_a1` — Event participation authorizes GitHub’s use of event photos or videos taken by GitHub and its partners, agents, or contractors.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-event-terms.md | 2. Pictures and videos | `chunk_f4e90716332b9d36c12106b4`
- `router_018_a2` — The Event Code of Conduct lists photographing or recording participants without consent as unacceptable conduct.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-event-code-of-conduct.md | Code of Conduct | `chunk_6603d8df9b666afe3f73439e`
- `router_018_a3` — An attendee may seek urgent help from venue security or a GitHub employee, or email events@github.com for non-urgent concerns.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-event-code-of-conduct.md | Reporting an incident | `chunk_9092956baf424fb221444e70`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_019

**Query:** I normally live outside a trade-restricted region, but my account was flagged while I was traveling through one. Have I permanently lost access to my private repositories, and what can I do if the flag is mistaken?

**Required aspects (3):**

- `router_019_a1` — Travel in a sanctioned region may affect account status, but availability may be reinstated after leaving.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-and-trade-controls.md | Frequently asked questions/Will traveling in these regions be impacted? | `chunk_c11cc08e2ae10c0e3bb3806b`
- `router_019_a2` — A user who believes a sanctions flag is mistaken may appeal with verification information to GitHub Support; the flag may be removed upon sufficient verification.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-and-trade-controls.md | Frequently asked questions/How is GitHub ensuring that folks not living in and/or having professional links to the sanctioned countries and territories still have access or ability to appeal? | `chunk_88854c0d88a888f9e14ed636`
- `router_019_a3` — For specified trade restrictions, GitHub says it cannot allow download or deletion of private repository content until authorized.
  - support_type: `direct`
  - evidence: Policies/other-site-policies/github-and-trade-controls.md | Frequently asked questions/Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)? | `chunk_11b0f878e227d23915728926`

**Optional context (0):**

- (none)

**Corpus gap:** none

### router_020

**Query:** Our enterprise admin sees a vendor on GitHub's subprocessor list and has also installed a Marketplace app. Are both covered by the same GitHub data-processing commitments, and who is responsible for the app's access to our data?

**Required aspects (4):**

- `router_020_a1` — The Subprocessor List covers processors acting for GitHub to serve Enterprise customers under GitHub services governed by its Data Protection Agreement.
  - support_type: `direct`
  - evidence: Policies/privacy-policies/github-subprocessors.md | (document introduction) | `chunk_1cb42138938eed82045675df`
- `router_020_a2` — A customer-authorized Marketplace third-party application is a distinct data-sharing relationship from a vendor processing data on GitHub’s behalf under the Subprocessor List.
  - support_type: `combined`
  - evidence: Policies/privacy-policies/github-general-privacy-statement.md | Sharing of Personal Data | `chunk_a523e9aa5d9d9ddd9c764fba`
  - evidence: Policies/privacy-policies/github-subprocessors.md | (document introduction) | `chunk_1cb42138938eed82045675df`
- `router_020_a3` — The customer is responsible for data it instructs GitHub to share with Marketplace third-party applications.
  - support_type: `direct`
  - evidence: Policies/privacy-policies/github-general-privacy-statement.md | Sharing of Personal Data | `chunk_a523e9aa5d9d9ddd9c764fba`
- `router_020_a5` — The Marketplace Product Provider is responsible for its product’s security and custody of the data it receives.
  - support_type: `direct`
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | E. Your Data and GitHub's Privacy Policy | `chunk_65d9607208f5f96afca0d68c`

**Optional context (1):**

- `router_020_a4` — Marketplace users can review the requested permission scope and accept or deny it at authorization.  [origin: `optionalized_from_required`]
  - evidence: Policies/github-terms/github-marketplace-terms-of-service.md | E. Your Data and GitHub's Privacy Policy | `chunk_65d9607208f5f96afca0d68c`

**Corpus gap:** none
