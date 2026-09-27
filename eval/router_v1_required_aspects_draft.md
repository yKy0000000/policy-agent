# Router V1 required-aspects truth draft

**Status:** `draft_pending_independent_corpus_audit`。仅用于完整答案评测；不是路由真值。

## A. Method

- 在任何 Router V1 答案或判分产生前，逐题从冻结问题与本地 `github/site-policy` 57 篇语料建立必需陈述。语料 commit：`b9578b546d2506febda1da2cd7431644d58e512c`。
- 用当前 `cache/policy_index.json` 的稳定 chunk ID 定位证据，同时核查每段锚点在实际 Markdown 语料中存在。`information_needs`、`evaluation_notes` 等作者字段仅在最后的泄漏审计中读取，不作为政策证据。
- 每条 statement 按“省略会使此题答案实质不完整”判断必要性；相关但非必要内容列为 optional。证据清单是已验证的可接受支持位置，不声称穷尽所有语义等价来源。
- `acceptable_supporting_chunk_sets` 中，每个内层列表表示可联合支持该 aspect 的 chunk 组合；未来若发现等价支持组合，可在独立审计阶段核实后增列。答案 covered/missing/incorrect 仍需按 statement 的语义判断，不能仅凭指定 chunk 是否被召回判定。
- `support_type=combined` 表示该陈述的当前证据映射需多个不同 chunk 联合支持。此文件是草案，必须经过独立 corpus audit 和冻结后才能用于两臂答案评价。
- `truth_created_before_router_v1_outputs: true`；本轮未读取或生成 Router V1 两臂结果、答案 judge 或 oracle。

## B. Per-query Contract

### router_001

> Someone copied my home address from a public website into a GitHub issue and urged others to contact me. Can I report this as a privacy violation, and is the private-information removal request the right way to get it taken down?

- **router_001_a1** — GitHub’s privacy rule covers posting another person’s physical address or other private location information.
  - 必要性：用户问住址是否可报告。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_36c8fa4bcb4dccbdc3bbb72c`。
  - 证据：`Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` / (document introduction) / `chunk_36c8fa4bcb4dccbdc3bbb72c` — “l, private email addresses * Phone numbers * Physical addresses or other private location information * Bank account information or credit card numbers * Soci”
- **router_001_a2** — GitHub considers context and whether the information is publicly available elsewhere; public availability does not by itself settle the policy question.
  - 必要性：须处理地址原先公开这一条件。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_36c8fa4bcb4dccbdc3bbb72c`。
  - 证据：`Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` / (document introduction) / `chunk_36c8fa4bcb4dccbdc3bbb72c` — “t as well as whether the reported content is publicly available elsewhere. Please note, however, that while sharing publicly available content may not be a violation of”
- **router_001_a3** — Sharing publicly available information with intent to harass or incite abuse may violate GitHub’s harassment rule.
  - 必要性：须处理号召他人联系的行为。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_36c8fa4bcb4dccbdc3bbb72c`。
  - 证据：`Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md` / (document introduction) / `chunk_36c8fa4bcb4dccbdc3bbb72c` — “olicy, if the information is shared with the intent to harass or incite other abusive behavior, it may violate our prohibition against [bullying and harassment](/site”
- **router_001_a4** — The private-information removal process requires content that should have remained confidential and whose disclosure poses a specific or targeted security risk.
  - 必要性：须判断高风险移除流程是否适用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_fd1a8855ee650c1195777567`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / What is Private Information? / `chunk_fd1a8855ee650c1195777567` — “vate information” refers to content that (i) should have been kept confidential, _and_ (ii) whose public availability poses a specific or targeted security risk to you or you”
- **Optional context：** 移除投诉还需指出具体文件、行号与风险。
- **Corpus gap：** 未发现。

### router_002

> A repository contains no intimate images, but it advertises a tool for making realistic sexual images of real people without their consent. Does hosting only the tool put the project outside GitHub's policy?

- **router_002_a1** — GitHub prohibits projects designed to encourage or support synthetic-media tools for making sexually explicit media of people without consent.
  - 必要性：回答只托管工具是否豁免。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_e921fe7a8e1eeb16ec85d0b4`。
  - 证据：`Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md` / (document introduction) / `chunk_e921fe7a8e1eeb16ec85d0b4` — “GitHub does not allow any projects that are designed for, encourage, promote, support, or suggest in any way the use of large lan”
- **router_002_a2** — The non-consensual intimate imagery rule includes realistic digitally altered or synthetic sexual depictions made without the person’s consent.
  - 必要性：解释所述用途的政策类别。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_eebcff7d8379f37aaf1bf06f`。
  - 证据：`Policies/acceptable-use-policies/github-non-consensual-intimate-imagery.md` / (document introduction) / `chunk_eebcff7d8379f37aaf1bf06f` — “idden cameras, or other forms of voyeurism * Digitally altered or synthetic media that depicts a realistic-looking individual in a sexually explicit manner without their consen”
- **router_002_a3** — GitHub assesses such projects in context, including configuration, marketing, README or other documentation, external links, and maintainer support.
  - 必要性：说明如何判断所述工具项目。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_e921fe7a8e1eeb16ec85d0b4`。
  - 证据：`Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md` / (document introduction) / `chunk_e921fe7a8e1eeb16ec85d0b4` — “f many factors: how a project is configured; how it is marketed; the information provided in its README or other documentation; the external sites or resource”
- **Optional context：** 已发布影像在罕见公共利益情境下可能逐案审查；本题未描述此情境。
- **Corpus gap：** 未发现。

### router_003

> A contributor keeps opening empty pull requests and new accounts after I block them, flooding reviewers with notifications. Which GitHub conduct rules apply, and can staff act beyond moderation of my repository?

- **router_003_a1** — Empty or meaningless pull requests and excessive notifications are examples of prohibited significant or continual disruption.
  - 必要性：对应空 PR 与通知轰炸。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_65ff616040be6ec5bdfe0770`。
  - 证据：`Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md` / (document introduction) / `chunk_65ff616040be6ec5bdfe0770` — “is includes: * Posting off-topic comments * Opening empty or meaningless issues or pull requests * Starring and/or following accounts or repositories in large volume i”
- **router_003_a2** — Creating alternative accounts specifically to evade moderation by GitHub staff or users is identified as harassment-related conduct.
  - 必要性：对应被屏蔽后开新号。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_23acf65f48bfbc0fd2b142a9`。
  - 证据：`Policies/acceptable-use-policies/github-bullying-and-harassment.md` / (document introduction) / `chunk_23acf65f48bfbc0fd2b142a9` — “conflict or undermines sincere discussion * Creating alternative accounts specifically to evade moderation action taken by GitHub staff or users Please note, not all unwelcome cond”
- **router_003_a3** — Disruptive conduct may also be bullying or harassment depending on its nature and severity; it is not automatically harassment.
  - 必要性：说明两类规则的关系。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_65ff616040be6ec5bdfe0770`。
  - 证据：`Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md` / (document introduction) / `chunk_65ff616040be6ec5bdfe0770` — “use-policies). For example, depending on the nature and severity of the activity, it may rise to the level of [bullying and harassment](/site-policy/acceptable”
- **router_003_a4** — Maintainers may moderate their projects, and GitHub staff may take further restrictive action against disruptive accounts.
  - 必要性：回答平台措施是否超出仓库管理。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_65ff616040be6ec5bdfe0770`。
  - 证据：`Policies/acceptable-use-policies/github-disrupting-the-experience-of-other-users.md` / (document introduction) / `chunk_65ff616040be6ec5bdfe0770` — “e their own projects on an individual basis, GitHub staff may take further restrictive action against accounts that are engaging in these types of behaviors. Please note that the above co”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_004

> Our museum repository explains the history of nude artwork, but its account avatar previews one of the images. Does the educational context mean GitHub must leave both the repository and avatar visible to everyone?

- **router_004_a1** — GitHub may allow nudity in artistic, educational, historical, or journalistic contexts.
  - 必要性：回答博物馆教育背景的作用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f25af672289856012d211dad`。
  - 证据：`Policies/acceptable-use-policies/github-sexually-obscene-content.md` / (document introduction) / `chunk_f25af672289856012d211dad` — “ay allow visual and/or textual depictions in artistic, educational, historical or journalistic contexts, or as it relates to victim advocacy. In some cases a disclaimer can”
- **router_004_a2** — Sexually suggestive content in profiles or other social contexts receives particular scrutiny when it mainly solicits an erotic or shocking response.
  - 必要性：回答头像展示位置的作用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f25af672289856012d211dad`。
  - 证据：`Policies/acceptable-use-policies/github-sexually-obscene-content.md` / (document introduction) / `chunk_f25af672289856012d211dad` — “larly where that content is amplified by its placement in profiles or other social contexts. This includes: * Pornographic content * Non-consensual intimate ima”
- **router_004_a3** — Even when context supports allowing material, GitHub may limit viewing by requiring users to opt in.
  - 必要性：回答是否必须对所有人可见。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f25af672289856012d211dad`。
  - 证据：`Policies/acceptable-use-policies/github-sexually-obscene-content.md` / (document introduction) / `chunk_f25af672289856012d211dad` — “ose to limit the content by giving users the option to opt in before viewing.”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_005

> I'm posting a satirical graphic about a medical claim. Its README labels it as satire and links to sources, but the image could circulate without that context. How does GitHub assess whether it crosses the misinformation policy?

- **router_005_a1** — The misinformation rule reaches inaccurate or unsupported medical claims likely to endanger public health or safety.
  - 必要性：说明医疗图像的危害门槛。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f9ddd26bbbc61c34bb71774a`。
  - 证据：`Policies/acceptable-use-policies/github-misinformation-and-disinformation.md` / (document introduction) / `chunk_f9ddd26bbbc61c34bb71774a` — “: * Inaccurate or scientifically unsupported medical claims that endanger public health or safety * Manipulated media, whether audio or visual, likely to mislead or deceive in a way”
- **router_005_a2** — GitHub generally allows parody and satire consistent with its Acceptable Use Policies, rather than automatically exempting anything labeled satire.
  - 必要性：回答讽刺标签的作用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f9ddd26bbbc61c34bb71774a`。
  - 证据：`Policies/acceptable-use-policies/github-misinformation-and-disinformation.md` / (document introduction) / `chunk_f9ddd26bbbc61c34bb71774a` — “ispute personal accounts or observations. We generally allow parody and satire that is in line with our [Acceptable Use Policies](/site-policy/acceptable-use-policies/github”
- **router_005_a3** — GitHub considers how context orients viewers, including clear disclaimers, credible citations, and details clarifying accuracy.
  - 必要性：回答 README 说明与来源的作用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f9ddd26bbbc61c34bb71774a`。
  - 证据：`Policies/acceptable-use-policies/github-misinformation-and-disinformation.md` / (document introduction) / `chunk_f9ddd26bbbc61c34bb71774a` — “s whether the content has been provided with clear disclaimers, citations to credible sources, or includes other details that clarify the accuracy of the information be”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_006

> We published an exploit demo for defensive research, and an active malware campaign now links to its download. Could GitHub limit that release without banning every copy, and how could we challenge a restriction we think is mistaken?

- **router_006_a1** — GitHub generally allows dual-use exploit and malware research content for its educational and security value.
  - 必要性：说明防御研究内容的政策起点。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_7d54462de0e9154ce55d108b`。
  - 证据：`Policies/acceptable-use-policies/github-active-malware-or-exploits.md` / (document introduction) / `chunk_7d54462de0e9154ce55d108b` — “e prior to the abuse occurring. Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, o”
- **router_006_a2** — In rare widespread abuse during an active attack or malware campaign, GitHub may restrict the specific abused instance.
  - 必要性：回答能否针对 release 或实例采取限制。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_7d54462de0e9154ce55d108b`。
  - 证据：`Policies/acceptable-use-policies/github-active-malware-or-exploits.md` / (document introduction) / `chunk_7d54462de0e9154ce55d108b` — “widespread abuse of dual-use content, we may restrict access to that specific instance of the content to disrupt an ongoing unlawful attack or malware campaign that is leveraging th”
- **router_006_a3** — Such a restriction is temporary where feasible and is not meant to purge all copies of the dual-use content permanently.
  - 必要性：回答是否会禁止所有副本。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_7d54462de0e9154ce55d108b`。
  - 证据：`Policies/acceptable-use-policies/github-active-malware-or-exploits.md` / (document introduction) / `chunk_7d54462de0e9154ce55d108b` — “strictions are temporary where feasible, and do not serve the purpose of purging or restricting any specific dual-use content, or copies of that content, from the platform in”
- **router_006_a4** — A restriction usually puts content behind authentication; disabling or removal is a last resort when that is not possible.
  - 必要性：回答限制的具体方式。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_7d54462de0e9154ce55d108b`。
  - 证据：`Policies/acceptable-use-policies/github-active-malware-or-exploits.md` / (document introduction) / `chunk_7d54462de0e9154ce55d108b` — “ese instances, restriction takes the form of putting the content behind authentication, but may, as an option of last resort, involve disabling access or full removal where this is”
- **router_006_a5** — A user who believes content was unduly restricted may appeal and provide grounds for a different decision.
  - 必要性：回答异议途径。
  - 支持类型：`combined`；可接受 chunk 组合：`chunk_5d1188bc9474b578388e2ddd` + `chunk_56264636771e77075a782b6d`。
  - 证据：`Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` / How this works / `chunk_5d1188bc9474b578388e2ddd` — “an enforcement action, please fill out our [Appeal and Reinstatement form](https://support.github.com/contact/reinstatement). You may Appeal a moderation decision for u”
  - 证据：`Policies/acceptable-use-policies/github-appeal-and-reinstatement.md` / How this works > Appeals / `chunk_56264636771e77075a782b6d` — “sion, they can use the form to explain their basis for disputing the decision and to provide any additional information regarding the alleged violation that th”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_007

> An account uses our registered company name as its handle, copies our logo, and calls itself parody. Is the matching name enough to reclaim the handle, or what would GitHub look at?

- **router_007_a1** — A username matching a registered trademark is not by itself a policy violation or automatic right to reclaim it.
  - 必要性：回答同名是否足够。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_19600b091f62ca0ede3450a2`。
  - 证据：`Policies/content-removal-policies/github-trademark-policy.md` / What is not a GitHub Trademark Policy Violation? / `chunk_19600b091f62ca0ede3450a2` — “ount with a user name that happens to be the same as a registered trademark is not, by itself, necessarily a violation of our trademark policy.”
- **router_007_a2** — Use of a company name or logo may violate trademark policy when it may confuse others about brand or business affiliation.
  - 必要性：回答复制标识的商标判断。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_e21d5efa444988a6ee52dc30`。
  - 证据：`Policies/content-removal-policies/github-trademark-policy.md` / What is a GitHub Trademark Policy Violation? / `chunk_e21d5efa444988a6ee52dc30` — “ark-protected materials in a manner that may mislead or confuse others with regard to its brand or business affiliation may be considered a trademark policy violatio”
- **router_007_a3** — Impersonation depends on misleading context; a similar name alone is not necessarily impersonation, and parody may be allowed.
  - 必要性：回答戏仿抗辩的作用。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_0d2d5abd2784cfcf630269b4`。
  - 证据：`Policies/acceptable-use-policies/github-impersonation.md` / (document introduction) / `chunk_0d2d5abd2784cfcf630269b4` — “oss of access to your account. Please note, having a username similar to another is not necessarily impersonation. GitHub will take context into account. For exampl”
- **router_007_a4** — After reviewing a registered-mark complaint, GitHub may release a username for the trademark holder’s active use; release is discretionary.
  - 必要性：说明可能转让而非保证转让。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f7c393d8c6398f15f8c9a7d1`。
  - 证据：`Policies/content-removal-policies/github-trademark-policy.md` / How Does GitHub Respond To Reported Trademark Policy Violations? / `chunk_f7c393d8c6398f15f8c9a7d1` — “nity to clear up any potential confusion. We may also release a username for the trademark holder's active use.”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_008

> Our README, package description, and profile mention another company's product to explain compatibility, without claiming affiliation. When would that use become a GitHub trademark-policy problem?

- **router_008_a1** — Trademark use becomes a GitHub policy issue when it may mislead or confuse others about brand or business affiliation.
  - 必要性：回答违规门槛。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_e21d5efa444988a6ee52dc30`。
  - 证据：`Policies/content-removal-policies/github-trademark-policy.md` / What is a GitHub Trademark Policy Violation? / `chunk_e21d5efa444988a6ee52dc30` — “ark-protected materials in a manner that may mislead or confuse others with regard to its brand or business affiliation may be considered a trademark policy violatio”
- **router_008_a2** — Mentioning another’s mark is not automatically a violation; the policy distinguishes use unrelated to the registered product or service from confusing use.
  - 必要性：回答兼容性说明中的商标提及。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_19600b091f62ca0ede3450a2`。
  - 证据：`Policies/content-removal-policies/github-trademark-policy.md` / What is not a GitHub Trademark Policy Violation? / `chunk_19600b091f62ca0ede3450a2` — “Using another's trademark in a way that has nothing to do with the product or service for which the trademark was granted is not a trademark policy violation. GitHub user names are”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_009

> I found a vulnerability in GitHub and reporting it may involve conduct normally restricted by its site policies. Does the bug bounty safe harbor cover that research, and does it let me test a connected third-party service?

- **router_009_a1** — Good-faith research within GitHub’s bug bounty policy receives the stated legal safe-harbor protection, subject to the program’s scope.
  - 必要性：回答安全港适用条件。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_e0d354aeaa7beb50005833bb`。
  - 证据：`Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` / 1. Safe Harbor Terms / `chunk_e0d354aeaa7beb50005833bb` — “ction, or send notice to law enforcement for accidental or good faith violations of this policy. We consider security research and vulnerability disclosure activities conducte”
- **router_009_a2** — GitHub waives otherwise inconsistent site-policy restrictions only for research consistent with the bug bounty program and for that limited purpose.
  - 必要性：回答站点规则的有限豁免。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_d5357e5db301e01f2d4c408f`。
  - 证据：`Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` / 3. Limited Waiver of Other Site Policies / `chunk_d5357e5db301e01f2d4c408f` — “program, we waive those restrictions for the sole and limited purpose of permitting your security research under this bug bounty program. Just like above, if in dou”
- **router_009_a3** — GitHub cannot authorize testing of a connected third-party service or bind that third party with its own safe harbor.
  - 必要性：回答第三方系统测试边界。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_943f62cca2ec5fdcf5f38e8c`。
  - 证据：`Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md` / 2. Third Party Safe Harbor / `chunk_943f62cca2ec5fdcf5f38e8c` — “en permission to do so. Please note that we cannot authorize out-of-scope testing in the name of third parties, and such testing is beyond the scope of our policy. Refer to tha”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_010

> A DMCA notice identifies one file in my repository and one part of a published package. Can I edit both before GitHub disables anything, and what must I tell GitHub after making changes?

- **router_010_a1** — For a notice targeting only part of a repository, GitHub generally gives its creator approximately one business day to delete or modify the identified content before disabling the repository.
  - 必要性：回答仓库文件的修改窗口。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_80d71a13ddfac8eb977f9541`。
  - 证据：`Policies/content-removal-policies/dmca-takedown-policy.md` / A. How Does This Actually Work? / `chunk_80d71a13ddfac8eb977f9541` — “ser who created the repository and give them approximately 1 business day to delete or modify the content specified in the notice. We'll notify the copyright owner if a”
- **router_010_a2** — Because packages are immutable, an allegedly infringing part can require disabling the whole package, with possible reinstatement after removal of that part.
  - 必要性：回答 package 的不同处理。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_80d71a13ddfac8eb977f9541`。
  - 证据：`Policies/content-removal-policies/dmca-takedown-policy.md` / A. How Does This Actually Work? / `chunk_80d71a13ddfac8eb977f9541` — “n we give the user a chance to make changes. Because packages are immutable, if only part of a package is infringing, GitHub would need to disable the entire package, but”
- **router_010_a3** — A repository user who makes the specified changes must tell GitHub within the approximately one-business-day window; GitHub verifies them and notifies the rightsholder.
  - 必要性：回答修改后的告知步骤。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_80d71a13ddfac8eb977f9541`。
  - 证据：`Policies/content-removal-policies/dmca-takedown-policy.md` / A. How Does This Actually Work? / `chunk_80d71a13ddfac8eb977f9541` — “s to make the specified changes, they _must_ tell us so within the window of approximately 1 business day. If they don't, we will disable the repository (as described i”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_011

> A repository exposes our internal network diagram and republishes our copyrighted manual. Should I put both into one private-information removal request, and what would GitHub need to assess each?

- **router_011_a1** — An internal network diagram fits private-information removal only if its exposure poses a specific organizational security risk.
  - 必要性：回答网络图的适用门槛。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_503d0f8451cd132a55e45b74`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / What is Private Information? > Private information removal requests are appropriate for: / `chunk_503d0f8451cd132a55e45b74` — “does belong to you. * Documentation (such as network diagrams or architecture) that poses a specific security risk for an organization. * [Information](/site-policy/accepta”
- **router_011_a2** — A private-information request must identify a working link to each file and the specific lines containing the information.
  - 必要性：回答网络图投诉的定位材料。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_0cc6709199187f11f4436f08`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / Sending A Private Information Removal Request > Your Request Must Include: / `chunk_0cc6709199187f11f4436f08` — “### Your Request Must Include: 1. A working, clickable link to each file containing private information. (Note that we're not able to work from search res”
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / Sending A Private Information Removal Request > Your Request Must Include: / `chunk_0cc6709199187f11f4436f08` — “earch results, examples, or screenshots.) 1. Specific line numbers within each file containing the private information. 1. A brief description of how each item y”
- **router_011_a3** — A private-information request must explain how each identified item poses a concrete security risk, beyond simply asserting risk.
  - 必要性：回答网络图投诉的风险材料。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_0cc6709199187f11f4436f08`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / Sending A Private Information Removal Request > Your Request Must Include: / `chunk_0cc6709199187f11f4436f08` — “ivate information. 1. A brief description of how each item you've identified poses a security risk to you or your organization. ***It is important that y”
- **router_011_a4** — A complaint about a copyrighted manual belongs under the DMCA process, not private-information removal.
  - 必要性：回答手册版权部分的渠道。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_d6d1c627931350dcab91a60d`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / What is Private Information? > Private information removal requests are _not_ appropriate for: / `chunk_d6d1c627931350dcab91a60d` — “hat may infringe your or your organization's copyright rights. If you have questions about how GitHub handles copyright-related matters or would like to rep”
- **router_011_a5** — GitHub asks for private-information and potentially infringing-content requests separately because it cannot process them simultaneously.
  - 必要性：回答能否合并请求。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_a761f910df2bb1e22f5a4020`。
  - 证据：`Policies/content-removal-policies/github-private-information-removal-policy.md` / Things to Know / `chunk_a761f910df2bb1e22f5a4020` — “in your private information removal requests separately from any requests to remove potentially infringing content. If you are unsure whether your request involves only”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_012

> I found a notice naming my project in GitHub's public government-takedowns repository. Does that mean GitHub decided my project was unlawful, and what does the listing actually tell readers?

- **router_012_a1** — A public government-takedowns notice establishes that GitHub received it on the indicated date.
  - 必要性：回答列表能证明什么。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_b5d910ef2bfc9d7ef2df4802`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / What does it mean if we post a notice in our gov-takedowns repository? / `chunk_b5d910ef2bfc9d7ef2df4802` — “gov-takedowns repository? It means that we received the notice on the indicated date. It does _not_ mean that the content was unlawful or wrong. It does _not_ mean that the user i”
- **router_012_a2** — Publishing the notice does not mean the content was unlawful, the user did wrong, or GitHub endorses the claim’s merits.
  - 必要性：回答是否认定项目违法。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_b5d910ef2bfc9d7ef2df4802`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / What does it mean if we post a notice in our gov-takedowns repository? / `chunk_b5d910ef2bfc9d7ef2df4802` — “indicated date. It does _not_ mean that the content was unlawful or wrong. It does _not_ mean that the user identified in the notice has done anything wrong. We don't m”
- **router_012_a3** — GitHub posts government takedown notices for transparency about what is withheld and why.
  - 必要性：回答公开列表的用途。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_cd467ee375fec67040db1e33`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / Why do we publicly post takedown notices? / `chunk_cd467ee375fec67040db1e33` — “tices, we can better inform the public about what content is being withheld from GitHub, and why. We post takedown notices to document their potential to chill speech.”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_013

> A government office says my public repository is illegal locally and also wants private data from my account. Does its content-takedown request give it that data, and how are the two requests handled?

- **router_013_a1** — A complete government content-takedown request must come from a relevant official agency, identify illegal content, and specify the local legal basis.
  - 必要性：说明内容请求的条件。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_a57209acbc132cc6e16c7234`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / How to submit a government takedown request / `chunk_a57209acbc132cc6e16c7234` — “rt.github.com/contact/government-takedown). To count as complete, a request must * come from a relevant, official government agency * identify illegal content”
- **router_013_a2** — For a complete government takedown request, GitHub notifies affected users of the allegation and permits appeal.
  - 必要性：说明受影响用户的程序。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_ef6899bc1eb9e4fe063bec90`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / What happens when we receive a complete takedown request from a government? / `chunk_ef6899bc1eb9e4fe063bec90` — “specifies the source of the illegality, we * notify the affected users of the specific content that allegedly violates the law, and that this is a legal takedown req”
- **router_013_a3** — For a complete government takedown request, GitHub limits geographic scope when possible and posts the official request publicly.
  - 必要性：说明内容限制范围与透明度。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_ef6899bc1eb9e4fe063bec90`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / What happens when we receive a complete takedown request from a government? / `chunk_ef6899bc1eb9e4fe063bec90` — “the decision as part of that notification * limit the geographic scope of the takedown when possible and include that as part of the notification * post the official”
- **router_013_a4** — A content-takedown request does not itself authorize disclosure of non-public account data; that requires consent or valid legal process, subject to limited emergency disclosure.
  - 必要性：回答内容请求是否附带私人数据。
  - 支持类型：`combined`；可接受 chunk 组合：`chunk_a57209acbc132cc6e16c7234` + `chunk_e38e8b117bf75ca2426fb8a0`。
  - 证据：`Policies/other-site-policies/github-government-takedown-policy.md` / How to submit a government takedown request / `chunk_a57209acbc132cc6e16c7234` — “government official and wish to request the removal of content under this policy, you can submit your request using our [Government Takedown Requests Form](https://support.git”
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / Disclosure of non-public information / `chunk_e38e8b117bf75ca2426fb8a0` — “ction with a civil or criminal investigation only with user consent or upon receipt of a valid subpoena, civil investigative demand, court order, search warrant,”
- **router_013_a5** — Private repository contents require a search warrant under the user-data guidelines.
  - 必要性：说明私人内容的更高门槛。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_30ab6464817b7b0946abaad0`。
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / Disclosure of non-public information / `chunk_30ab6464817b7b0946abaad0` — “a search warrant:** We will not disclose the private contents of any account unless compelled to do so under a search warrant issued under the procedures described in the”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_014

> Police say they need my private repository immediately to prevent serious harm. Could GitHub disclose its contents under the emergency exception without a warrant, and would I be told first?

- **router_014_a1** — In a qualifying emergency involving danger of death or serious physical injury, GitHub may disclose only limited necessary information after verifying the law-enforcement request.
  - 必要性：回答紧急例外范围。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_30ab6464817b7b0946abaad0`。
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / Disclosure of non-public information / `chunk_30ab6464817b7b0946abaad0` — “* <a name="in-exigent-circumstances"></a> **Under exigent circumstances:** If we receive a request for information under certain exigent circumstances (where we belie”
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / Disclosure of non-public information / `chunk_30ab6464817b7b0946abaad0` — “ivate repositories without a search warrant. Before disclosing information, we confirm that the request came from a law enforcement agency, an authority sent an official notice summ”
- **router_014_a2** — Even in that emergency, GitHub says it will not disclose private repository contents without a search warrant.
  - 必要性：回答私人仓库是否免搜查令。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_30ab6464817b7b0946abaad0`。
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / Disclosure of non-public information / `chunk_30ab6464817b7b0946abaad0` — “t order, as described above. For example, we will not disclose contents of private repositories without a search warrant. Before disclosing information, we confirm that the request came from”
- **router_014_a3** — GitHub generally gives affected owners notice before disclosure, but may delay it in rare exigent circumstances to prevent death or serious harm or due to an ongoing investigation.
  - 必要性：回答是否一定事先通知。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_35fd87021964946f76efbd5f`。
  - 证据：`Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md` / We will notify any affected account owners / `chunk_35fd87021964946f76efbd5f` — “ey wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing inves”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_015

> I use a personal account and keep code in a private repository, but paste a snippet into a GitHub AI feature. Does “private” prevent GitHub from using that input to improve AI, and what changes if I opt out?

- **router_015_a1** — GitHub treats private repository contents as confidential and says it will not otherwise use them to develop or improve the Service unless provided as AI Feature Input.
  - 必要性：区分仓库存储与主动提交。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_82b71e1d710271179f8b4bdd`。
  - 证据：`Policies/github-terms/github-terms-of-service.md` / E. Private Repositories > 3. Access / `chunk_82b71e1d710271179f8b4bdd` — “s to this use of private repository content. We will not otherwise use your private repository contents to develop or improve the Service. Additionally, we may be [compelled by law](/site-policy/pr”
- **router_015_a2** — For an individual license, AI Inputs and Outputs may be used to improve AI unless the user opts out through account settings.
  - 必要性：回答粘贴片段可否用于 AI 改进。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_5bd8f67a21c277adbd0e92cd`。
  - 证据：`Policies/github-terms/github-terms-of-service.md` / J. AI Features, Training, and Your Data > 3. Development and Improvement Using Your Input and Output / `chunk_5bd8f67a21c277adbd0e92cd` — “gies including those that power AI Features, unless (a) you opt out through your account settings, or (b) your use of the Service is governed by a GitHub Customer”
- **router_015_a3** — The opt-out stops the specified collection or use of Inputs and Outputs from its effective date forward, not retroactively.
  - 必要性：回答退出后的时点。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_5bd8f67a21c277adbd0e92cd`。
  - 证据：`Policies/github-terms/github-terms-of-service.md` / J. AI Features, Training, and Your Data > 3. Development and Improvement Using Your Input and Output / `chunk_5bd8f67a21c277adbd0e92cd` — “for the purposes described in this paragraph from the effective date of your opt-out going forward. Unless you opt out, GitHub's Affiliates may use your Inputs an”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_016

> Our paid Marketplace app was disabled for a policy reason halfway through its annual term. Who should notify us, does payment guarantee continued access, and are we owed a partial refund?

- **router_016_a1** — GitHub may block or disable a Marketplace developer product for policy reasons and will work with its Product Provider to notify affected users.
  - 必要性：回答政策禁用与通知安排。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_53cfaee79a6c3b7ee9eed1d1`。
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / H. Developer Product Blocking / `chunk_53cfaee79a6c3b7ee9eed1d1` — “lock or disable a Developer Product, we will work with the Product Provider to notify affected users.”
- **router_016_a2** — Monthly or yearly Marketplace purchases are billed in advance and non-refundable, with no refunds or credits for partial or unused months under the terms.
  - 必要性：回答部分退款。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_1c0bd6feab4c1cdf6411559c`。
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / D. Payment, Billing Schedule, and Cancellation / `chunk_1c0bd6feab4c1cdf6411559c` — “monthly or yearly basis respectively and are non-refundable. There will be no refunds or credits for partial months of service, downgrade refunds, or refu”
- **router_016_a3** — The ordinary paid-period continuation term does not override GitHub’s separate authority to block a product for policy reasons.
  - 必要性：回答付款是否保证继续访问。
  - 支持类型：`combined`；可接受 chunk 组合：`chunk_1c0bd6feab4c1cdf6411559c` + `chunk_53cfaee79a6c3b7ee9eed1d1`。
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / D. Payment, Billing Schedule, and Cancellation / `chunk_1c0bd6feab4c1cdf6411559c` — “for months unused; however, the service will remain active for the length of the paid billing period. If you would like to cancel the Developer Product services, you ca”
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / H. Developer Product Blocking / `chunk_53cfaee79a6c3b7ee9eed1d1` — “## H. Developer Product Blocking GitHub may block a Developer Product from our servers, or disable its functionality, for legal or policy reasons. In the event that”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_017

> I want to thank Sponsors by displaying their logos in my README and Sponsor content, then promote their products in other users' issue threads. Where does GitHub draw the line on that kind of promotion?

- **router_017_a1** — Sponsored developers may display Sponsors’ names or logos, but Sponsored Developer Content must not primarily be advertising.
  - 必要性：回答展示感谢的限度。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_612778d80d7c5c0b6e3e95ae`。
  - 证据：`Policies/github-terms/github-sponsors-additional-terms.md` / Terms For Sponsored Developer > 2. Sponsored Developer Obligations. > 2.3. Content Monetization. > 2.3.3. Advertising. / `chunk_612778d80d7c5c0b6e3e95ae` — “understand that you may want to promote your Sponsors by posting their names or logos in your account, the primary focus of your Sponsored Developer Content should not be advertisi”
- **router_017_a2** — Project-related static images, links, and promotional text may appear in an account README or project description, provided advertising is not its primary focus.
  - 必要性：回答 README 展示条件。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_98cf35fb3afbd05cb943b94b`。
  - 证据：`Policies/acceptable-use-policies/github-acceptable-use-policies.md` / 10. Advertising on GitHub / `chunk_98cf35fb3afbd05cb943b94b` — “other parts of the Service. You may include static images, links, and promotional text in the README documents or project description sections associated with your Account, but they”
- **router_017_a3** — GitHub prohibits advertising in other users’ accounts, including monetized or excessive bulk content in their issues.
  - 必要性：回答在他人 issue 推广的界限。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_98cf35fb3afbd05cb943b94b`。
  - 证据：`Policies/acceptable-use-policies/github-acceptable-use-policies.md` / 10. Advertising on GitHub / `chunk_98cf35fb3afbd05cb943b94b` — “o the project you are hosting on GitHub. You may not advertise in other Users' Accounts, such as by posting monetized or excessive bulk content in issues. You may not prom”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_018

> At a GitHub event, staff are filming the room while another attendee records me after I say no. Do the same consent rules apply to both, and how can I report the attendee's conduct?

- **router_018_a1** — Event participation authorizes GitHub’s use of event photos or videos taken by GitHub and its partners, agents, or contractors.
  - 必要性：回答工作人员拍摄的条款。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_f4e90716332b9d36c12106b4`。
  - 证据：`Policies/github-terms/github-event-terms.md` / 2. Pictures and videos / `chunk_f4e90716332b9d36c12106b4` — “metimes take photos and videos at the Event. By participating or attending the Event, you agree that you may appear in some of these photos and videos, and you authorize”
- **router_018_a2** — The Event Code of Conduct lists photographing or recording participants without consent as unacceptable conduct.
  - 必要性：回答其他参加者被拒绝后的拍摄。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_6603d8df9b666afe3f73439e`。
  - 证据：`Policies/github-terms/github-event-code-of-conduct.md` / Code of Conduct / `chunk_6603d8df9b666afe3f73439e` — “lowing, or harassing of Event Participants * Photography or recording of Event Participants without their consent * Harassment of any kind, even in a joking or ironic manner * Conduct wh”
- **router_018_a3** — An attendee may seek urgent help from venue security or a GitHub employee, or email events@github.com for non-urgent concerns.
  - 必要性：回答举报途径。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_9092956baf424fb221444e70`。
  - 证据：`Policies/github-terms/github-event-code-of-conduct.md` / Reporting an incident / `chunk_9092956baf424fb221444e70` — “ode of Conduct, please speak directly with a venue security officer or GitHub employee for urgent help, or email us at [events@github.com](mailto:events@github.co”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_019

> I normally live outside a trade-restricted region, but my account was flagged while I was traveling through one. Have I permanently lost access to my private repositories, and what can I do if the flag is mistaken?

- **router_019_a1** — Travel in a sanctioned region may affect account status, but availability may be reinstated after leaving.
  - 必要性：回答旅行是否造成永久失去访问。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_c11cc08e2ae10c0e3bb3806b`。
  - 证据：`Policies/other-site-policies/github-and-trade-controls.md` / Frequently asked questions > Will traveling in these regions be impacted? / `chunk_c11cc08e2ae10c0e3bb3806b` — “regions may impact your account status, but availability may be reinstated once you are outside of the sanctioned region.”
- **router_019_a2** — A user who believes a sanctions flag is mistaken may appeal with verification information to GitHub Support; the flag may be removed upon sufficient verification.
  - 必要性：回答误标时的处理。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_88854c0d88a888f9e14ed636`。
  - 证据：`Policies/other-site-policies/github-and-trade-controls.md` / Frequently asked questions > How is GitHub ensuring that folks not living in and/or having professional links to the sanctioned countries and territories still have access or ability to appeal? / `chunk_88854c0d88a888f9e14ed636` — “error, then that user has the opportunity to appeal the flag by providing verification information to GitHub. If GitHub receives sufficient information to verify that the user or or”
- **router_019_a3** — For specified trade restrictions, GitHub says it cannot allow download or deletion of private repository content until authorized.
  - 必要性：回答私人仓库访问限制。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_11b0f878e227d23915728926`。
  - 证据：`Policies/other-site-policies/github-and-trade-controls.md` / Frequently asked questions > Can trade-restricted users access private repository data (e.g. downloading or deletion of repository data)? / `chunk_11b0f878e227d23915728926` — “nderstanding of the law does not give us the option to allow downloads or deletion of private repository content, until otherwise authorized by the U.S. government, for specific”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

### router_020

> Our enterprise admin sees a vendor on GitHub's subprocessor list and has also installed a Marketplace app. Are both covered by the same GitHub data-processing commitments, and who is responsible for the app's access to our data?

- **router_020_a1** — The Subprocessor List covers processors acting for GitHub to serve Enterprise customers under GitHub services governed by its Data Protection Agreement.
  - 必要性：回答清单及承诺范围。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_1cb42138938eed82045675df`。
  - 证据：`Policies/privacy-policies/github-subprocessors.md` / (document introduction) / `chunk_1cb42138938eed82045675df` — “es to our Enterprise customers. This list is applicable for all GitHub services governed by the [GitHub Data Protection Agreement](https://github.com/customer-terms/github-data-protec”
- **router_020_a2** — A customer-authorized Marketplace third-party application is a distinct data-sharing relationship from a vendor processing data on GitHub’s behalf under the Subprocessor List.
  - 必要性：回答两类供应商是否相同。
  - 支持类型：`combined`；可接受 chunk 组合：`chunk_a523e9aa5d9d9ddd9c764fba` + `chunk_1cb42138938eed82045675df`。
  - 证据：`Policies/privacy-policies/github-general-privacy-statement.md` / Sharing of Personal Data / `chunk_a523e9aa5d9d9ddd9c764fba` — “sions in GitHub Codespaces and github.dev. * Other Third-party Applications: Upon your instruction, we may share Personal Data with third-party applications available on”
  - 证据：`Policies/privacy-policies/github-subprocessors.md` / (document introduction) / `chunk_1cb42138938eed82045675df` — “PR. The GitHub Subprocessor List identifies subprocessors authorized to subprocess customer or personal data on behalf of GitHub to provide services to our Enterpr”
- **router_020_a3** — The customer is responsible for data it instructs GitHub to share with Marketplace third-party applications.
  - 必要性：回答客户对应用共享数据的责任。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_a523e9aa5d9d9ddd9c764fba`。
  - 证据：`Policies/privacy-policies/github-general-privacy-statement.md` / Sharing of Personal Data / `chunk_a523e9aa5d9d9ddd9c764fba` — “y applications available on our Marketplace. You are responsible for the data you instruct us to share with these applications. * Other Users and the Public: Depending on y”
- **router_020_a4** — Marketplace users can review the requested permission scope and accept or deny it at authorization.
  - 必要性：回答应用如何获得访问权限。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_65d9607208f5f96afca0d68c`。
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / E. Your Data and GitHub's Privacy Policy / `chunk_65d9607208f5f96afca0d68c` — “r private data. You will be able to view the scope of the permissions the Developer Product is requesting, and accept or deny them, when you grant it authorization”
- **router_020_a5** — The Marketplace Product Provider is responsible for its product’s security and custody of the data it receives.
  - 必要性：回答产品提供方的数据责任。
  - 支持类型：`direct`；可接受 chunk 组合：`chunk_65d9607208f5f96afca0d68c`。
  - 证据：`Policies/github-terms/github-marketplace-terms-of-service.md` / E. Your Data and GitHub's Privacy Policy / `chunk_65d9607208f5f96afca0d68c` — “he security of the Developer Product and the custodianship of your data, including your Personal Information (if any), is the responsibility of the Product Provider.”
- **Optional context：** 无。
- **Corpus gap：** 未发现。

## C. Dataset Summary

- 题目：20；required aspects：70。
- 每题数量：mean 3.50，median 3.0，min 2，max 5。
- 单 chunk 支持：66；combined support：4；跨文档联合支持：2。
- Corpus gaps：0。

| Query | Required aspects |
|---|---:|
| `router_001` | 4 |
| `router_002` | 3 |
| `router_003` | 4 |
| `router_004` | 3 |
| `router_005` | 3 |
| `router_006` | 5 |
| `router_007` | 4 |
| `router_008` | 2 |
| `router_009` | 3 |
| `router_010` | 3 |
| `router_011` | 5 |
| `router_012` | 3 |
| `router_013` | 5 |
| `router_014` | 3 |
| `router_015` | 3 |
| `router_016` | 3 |
| `router_017` | 3 |
| `router_018` | 3 |
| `router_019` | 3 |
| `router_020` | 5 |

## D. Self Audit

1. **过度拆分：** 文件链接/行号合并为一个定位单元，具体安全风险单列；政府请求中的用户通知与地理限制分开。独立审计仍应检查复合程序陈述。
2. **重复：** 逐题检查没有完全同义的 required aspects；相邻条目分别评测门槛、例外、程序或结果。
3. **作者 metadata：** 政策依据均由实际 corpus 段落和 chunk ID 验证，未将 benchmark 作者的解释字段直接当作 truth。
4. **Corpus 外结论：** 未使用线上政策、法律常识或外部资料。对“内容下架请求与私人数据披露不同”“已付费期不覆盖政策禁用”“Marketplace 应用与子处理者不同”等跨条款推论标为 combined；独立审计须重点核验措辞。
5. **数量异常：** 范围为 2–5；`router_006`、`router_011`、`router_013`、`router_020` 各有 5 条，分别对应明确询问的副本/申诉、投诉材料、两类政府程序、两类数据责任；未为了平衡删项。
6. **结构泄漏：** aspect 数量由答案必要性决定，可能与作者的语料结构字段相关；运行时 Router 不读取本文件。以下相关性仅用于解释评测，不是路由标签。

### Metadata correlation check

- `multi_document`：有该作者字段的 9 题平均 4.22 个；其余 11 题平均 2.91 个；点二列相关 r=0.754。该小样本相关性不用于增删 required aspects。
- `fragmented_evidence`：有该作者字段的 13 题平均 3.77 个；其余 7 题平均 3.00 个；点二列相关 r=0.424。该小样本相关性不用于增删 required aspects。
