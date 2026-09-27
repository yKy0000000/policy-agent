## A. Corpus Opportunity Summary

已检查本地 `github/site-policy` 语料：`Policies` 下有 **57 份文档**，对应提交 `b9578b546d2506febda1da2cd7431644d58e512c`。

最适合测试检索覆盖的关系包括：行为规则与专门移除流程、版权与隐私等不同投诉渠道、政府内容下架与索取用户数据、产品条款与隐私责任，以及一般限制与申诉或豁免。这些关系在语料中有明确依据，例如 [可接受使用政策](<D:/gradual-policyagent/policy-agent/data/site-policy/Policies/acceptable-use-policies/github-acceptable-use-policies.md>)、[私人信息移除政策](<D:/gradual-policyagent/policy-agent/data/site-policy/Policies/content-removal-policies/github-private-information-removal-policy.md>)、[政府下架政策](<D:/gradual-policyagent/policy-agent/data/site-policy/Policies/other-site-policies/github-government-takedown-policy.md>) 和 [用户数据法律请求指南](<D:/gradual-policyagent/policy-agent/data/site-policy/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md>)。

题目同时包含简短的跨文档问题，以及条件较多、但答案集中于单份政策的问题。`likely_evidence_structure` 是依据文档章节作出的**预期**，尚不是对实际 chunk 或检索结果的测量。

## B. Final 20 Queries

### router_001

- **query:** Someone copied my home address from a public website into a GitHub issue and urged others to contact me. Can I report this as a privacy violation, and is the private-information removal request the right way to get it taken down?
- **benchmark_property:** `multi_document`, `rule_exception`, `fragmented_evidence`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 公开来源对隐私规则判断的影响；煽动骚扰的上下文；私人信息移除流程的适用门槛。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** “网上已有”与“被用来骚扰”分别牵涉行为规则和移除流程，容易只覆盖其中一侧。
- **evaluation_notes:** 不可把公开可见等同于一律允许，也不可把所有令人不安的信息都归入高风险移除流程。

### router_002

- **query:** A repository contains no intimate images, but it advertises a tool for making realistic sexual images of real people without their consent. Does hosting only the tool put the project outside GitHub's policy?
- **benchmark_property:** `multi_document`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 针对工具用途的政策范围；非自愿合成亲密影像的相关规则；判断项目用途时可考虑的上下文。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 用户以“只托管代码”描述问题，相关证据却分布在合成媒体与影像政策中。
- **evaluation_notes:** 不可仅按仓库是否直接存放影像判断；需覆盖项目设计和宣传所指向的用途。

### router_003

- **query:** A contributor keeps opening empty pull requests and new accounts after I block them, flooding reviewers with notifications. Which GitHub conduct rules apply, and can staff act beyond moderation of my repository?
- **benchmark_property:** `multi_document`, `rule_process`, `fragmented_evidence`, `multi_requirement`
- **information_needs:** 无意义互动和通知轰炸的规则；规避用户或 GitHub 审核措施的规则；维护者措施与 GitHub 员工措施的关系。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 同一行为可能是平台干扰，也可能达到骚扰门槛；答案还需要说明处理主体。
- **evaluation_notes:** 不可把所有空 PR 自动定为骚扰，也不可漏掉持续性、针对性及规避审核的情境。

### router_004

- **query:** Our museum repository explains the history of nude artwork, but its account avatar previews one of the images. Does the educational context mean GitHub must leave both the repository and avatar visible to everyone?
- **benchmark_property:** `direct_control`, `rule_exception`, `hard_looking_control`
- **information_needs:** 艺术和教育情境如何影响判断；头像等社交展示位置的影响；可能采取的可见性限制。
- **likely_evidence_structure:** `localized`
- **why_it_is_useful:** 条件和呈现位置较多，但核心证据集中在一份内容政策。
- **evaluation_notes:** 须区分允许考虑正当情境与保证不受限制。

### router_005

- **query:** I'm posting a satirical graphic about a medical claim. Its README labels it as satire and links to sources, but the image could circulate without that context. How does GitHub assess whether it crosses the misinformation policy?
- **benchmark_property:** `direct_control`, `rule_exception`, `hard_looking_control`
- **information_needs:** 涉及公共健康危害的判断；讽刺与戏仿的空间；免责声明、来源和呈现上下文的作用。
- **likely_evidence_structure:** `localized`
- **why_it_is_useful:** 表面上有多项条件，实际围绕同一政策的判断标准。
- **evaluation_notes:** 不可把“讽刺”标签视为自动豁免，也不可忽略政策要求的危害与上下文判断。

### router_006

- **query:** We published an exploit demo for defensive research, and an active malware campaign now links to its download. Could GitHub limit that release without banning every copy, and how could we challenge a restriction we think is mistaken?
- **benchmark_property:** `multi_document`, `rule_exception`, `rule_process`, `fragmented_evidence`, `multi_requirement`
- **information_needs:** 双重用途安全研究与直接支持攻击的区别；针对广泛滥用的限制方式及范围；通知和申诉途径。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** “被攻击者使用”并不能单独表达政策判断，完整答复还跨到执行及申诉政策。
- **evaluation_notes:** 不可将研究代码一概禁止，也不可把临时限制描述成永久清除所有副本。

### router_007

- **query:** An account uses our registered company name as its handle, copies our logo, and calls itself parody. Is the matching name enough to reclaim the handle, or what would GitHub look at?
- **benchmark_property:** `multi_document`, `rule_exception`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 已占用用户名的处理规则；商标混淆与可能的处置；冒充判断中的上下文及戏仿因素。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 用户把“拿回名字”作为单一目标，证据却涉及用户名、商标和身份冒充的不同标准。
- **evaluation_notes:** 不可仅因名称与注册商标相同就承诺转移用户名。

### router_008

- **query:** Our README, package description, and profile mention another company's product to explain compatibility, without claiming affiliation. When would that use become a GitHub trademark-policy problem?
- **benchmark_property:** `direct_control`, `rule_exception`, `hard_looking_control`, `broad_coherent_control`
- **information_needs:** 商标政策关注的混淆或误导；出现他人商标本身是否充分；用途与产品或服务的关联。
- **likely_evidence_structure:** `localized`
- **why_it_is_useful:** 提及多个页面但只围绕一个商标政策概念，测试表面范围是否造成过度拆解。
- **evaluation_notes:** 不可把任何提及他人商标都判为违规；也不应替政策作出超出语料的法律结论。

### router_009

- **query:** I found a vulnerability in GitHub and reporting it may involve conduct normally restricted by its site policies. Does the bug bounty safe harbor cover that research, and does it let me test a connected third-party service?
- **benchmark_property:** `multi_document`, `rule_exception`, `rule_process`, `fragmented_evidence`, `multi_requirement`
- **information_needs:** 协调披露和善意研究的适用条件；对其他站点限制的有限豁免；第三方系统的边界。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** “安全港”容易被误读成全面授权；问题要求合并一般规则、有限豁免和第三方限制。
- **evaluation_notes:** 须保留豁免的范围限制及第三方不能由 GitHub 代为授权这一点。

### router_010

- **query:** A DMCA notice identifies one file in my repository and one part of a published package. Can I edit both before GitHub disables anything, and what must I tell GitHub after making changes?
- **benchmark_property:** `direct_control`, `rule_exception`, `rule_process`, `fragmented_evidence`, `hard_looking_control`, `multi_requirement`
- **information_needs:** 仓库部分内容的修改机会；不可变 package 的不同处理；完成修改后的通知与核验步骤。
- **likely_evidence_structure:** `multi_section`
- **why_it_is_useful:** 两种载体看似相同，关键差异和后续流程却位于同一 DMCA 政策的不同段落。
- **evaluation_notes:** 不可把仓库的修改窗口直接套用到 package，也不可漏掉用户告知 GitHub 已修改的要求。

### router_011

- **query:** A repository exposes our internal network diagram and republishes our copyrighted manual. Should I put both into one private-information removal request, and what would GitHub need to assess each?
- **benchmark_property:** `multi_document`, `fragmented_evidence`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 网络资料何时符合私人信息移除门槛；版权材料应走的投诉渠道；两类请求为何需要各自的依据和材料。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 用户将两者统称为“我们的内部材料”，但语料为安全风险与版权主张规定了不同流程。
- **evaluation_notes:** 不可用版权归属代替具体安全风险说明，也不可用私人信息流程处理纯版权投诉。

### router_012

- **query:** I found a notice naming my project in GitHub's public government-takedowns repository. Does that mean GitHub decided my project was unlawful, and what does the listing actually tell readers?
- **benchmark_property:** `direct_control`, `broad_coherent_control`
- **information_needs:** 公布通知的目的；仓库记录能够证明的事项；它不能证明的法律或用户行为结论。
- **likely_evidence_structure:** `localized`
- **why_it_is_useful:** 问题范围较宽但始终围绕“公开通知代表什么”这一个概念。
- **evaluation_notes:** 不可把发布政府请求误写成 GitHub 对违法性或用户过错的认定。

### router_013

- **query:** A government office says my public repository is illegal locally and also wants private data from my account. Does its content-takedown request give it that data, and how are the two requests handled?
- **benchmark_property:** `multi_document`, `fragmented_evidence`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 政府内容下架请求的对象和处理；非公开账户数据的披露条件；两类请求的通知及适用范围。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 用户称之为一件“政府请求”，但内容限制与数据披露有不同证据链。
- **evaluation_notes:** 不可把内容下架请求当成取得非公开账户数据的充分依据。

### router_014

- **query:** Police say they need my private repository immediately to prevent serious harm. Could GitHub disclose its contents under the emergency exception without a warrant, and would I be told first?
- **benchmark_property:** `direct_control`, `rule_exception`, `rule_process`, `fragmented_evidence`, `hard_looking_control`, `multi_requirement`
- **information_needs:** 紧急披露例外的范围；私人仓库内容所需的法律程序；用户通知及可能延迟的条件。
- **likely_evidence_structure:** `multi_section`
- **why_it_is_useful:** 紧急性、内容类别和通知时点分散在同一指南的不同部分。
- **evaluation_notes:** 须区分有限的紧急信息披露与私人仓库内容，不能笼统回答“紧急时都可披露”。

### router_015

- **query:** I use a personal account and keep code in a private repository, but paste a snippet into a GitHub AI feature. Does “private” prevent GitHub from using that input to improve AI, and what changes if I opt out?
- **benchmark_property:** `direct_control`, `rule_exception`, `fragmented_evidence`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 私有仓库内容的一般处理；主动提供给 AI 功能的输入如何处理；个人账户退出相关用途后的适用范围和时点。
- **likely_evidence_structure:** `multi_section`
- **why_it_is_useful:** 用户的“私有”一词覆盖了仓库存储与主动提交输入两种不同情形。
- **evaluation_notes:** 不可把退出选择描述成追溯删除，也不可将未提供为输入的整个仓库与该片段混为一谈。

### router_016

- **query:** Our paid Marketplace app was disabled for a policy reason halfway through its annual term. Who should notify us, does payment guarantee continued access, and are we owed a partial refund?
- **benchmark_property:** `direct_control`, `rule_exception`, `rule_process`, `fragmented_evidence`, `multi_requirement`
- **information_needs:** 政策原因导致产品被屏蔽时的通知安排；已付费服务期限与屏蔽的关系；年度购买的退款条款。
- **likely_evidence_structure:** `multi_section`
- **why_it_is_useful:** 同一 Marketplace 条款中，取消订阅、政策屏蔽和退款规则位于不同章节。
- **evaluation_notes:** 不可把正常取消后的剩余付费期规则直接当作政策屏蔽后的可用性保证。

### router_017

- **query:** I want to thank Sponsors by displaying their logos in my README and Sponsor content, then promote their products in other users' issue threads. Where does GitHub draw the line on that kind of promotion?
- **benchmark_property:** `multi_document`, `rule_exception`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 对赞助者的适度展示；赞助内容与一般账户内容的广告限制；在他人账户中推广的限制。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** “感谢赞助者”在不同展示位置会触及 Sponsors 条款与一般可接受使用规则。
- **evaluation_notes:** 不可把展示赞助者标识与在他人 issue 中发布推广内容视为同一许可。

### router_018

- **query:** At a GitHub event, staff are filming the room while another attendee records me after I say no. Do the same consent rules apply to both, and how can I report the attendee's conduct?
- **benchmark_property:** `multi_document`, `rule_process`, `fragmented_evidence`, `multi_requirement`
- **information_needs:** 活动方拍摄的参加条款；参加者拍摄他人的行为规范；事件举报和紧急协助途径。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 两种拍摄行为看似相同，却由活动条款和行为准则分别约束。
- **evaluation_notes:** 不可把参加活动时对主办方拍摄的授权延伸为其他参加者任意拍摄的许可。

### router_019

- **query:** I normally live outside a trade-restricted region, but my account was flagged while I was traveling through one. Have I permanently lost access to my private repositories, and what can I do if the flag is mistaken?
- **benchmark_property:** `direct_control`, `rule_exception`, `rule_process`, `fragmented_evidence`, `hard_looking_control`, `multi_requirement`
- **information_needs:** 旅行对账户状态的潜在影响；受限服务与私人仓库的处理；错误标记的核验和申诉途径。
- **likely_evidence_structure:** `multi_section`
- **why_it_is_useful:** 用户需要把旅行、账户限制和纠错流程合起来理解，但证据集中于贸易管制政策。
- **evaluation_notes:** 不可承诺自动恢复或允许取回受限私人数据；须保留政策中的条件性表述。

### router_020

- **query:** Our enterprise admin sees a vendor on GitHub's subprocessor list and has also installed a Marketplace app. Are both covered by the same GitHub data-processing commitments, and who is responsible for the app's access to our data?
- **benchmark_property:** `multi_document`, `fragmented_evidence`, `representation_mismatch`, `multi_requirement`
- **information_needs:** 子处理者名单的适用范围；用户授权的第三方应用与 GitHub 服务提供商的区别；Marketplace 产品的数据访问和责任。
- **likely_evidence_structure:** `multi_document`
- **why_it_is_useful:** 用户用“供应商”概括两种不同关系，检索需找出各自的隐私与产品条款。
- **evaluation_notes:** 不可因应用出现在 Marketplace 就认定它是 GitHub 的子处理者。

## C. Coverage Audit

- **multi-document：**11 题，覆盖行为规则与移除流程、政府内容与数据请求、活动条款与行为准则、隐私声明与 Marketplace 等关系。
- **rule + exception：**13 题，包括正当情境、有限豁免、紧急情况和不同内容载体的特殊处理。
- **rule + process：**9 题，覆盖申诉、员工干预、投诉处理、披露、通知与纠错。
- **fragmented evidence：**13 题；其中既有跨文档证据，也有单文档内跨章节证据。
- **representation mismatch：**8 题，例如“只托管工具”“网上已有”“我们的内部材料”“供应商”。
- **multi-requirement：**16 题，需求均服务于一个实际判断或行动。
- **hard-looking controls：**`router_004`、`005`、`008`、`010`、`014`、`019`。
- **broad coherent controls：**`router_008`、`012`。

以上是题目属性审计，不是预设的 Router 决策或效果标签。

## D. Self Audit

1. **语义重复：**20 题内部没有同义改写题。相近主题各有不同的判断目标，例如 `001` 与 `011`、`007` 与 `008`、`013` 与 `014`。
2. **长度捷径：**不能仅凭长度判断证据需求。`002`、`013` 较短但跨文档；`004`、`010`、`014`、`019` 条件较多但主要依据单份政策。
3. **人为难度：**未使用生僻替词、无关背景或互不相关的拼接。跨领域题均围绕同一用户事件或决策。
4. **语料边界：**20 题的政策主题均在这 57 份文档内；未把语料外的具体产品操作或法律结论设为必答事实。
5. **最弱覆盖：**`broad_coherent_control` 只有 2 题。可选的 `boundary_control` 本轮未纳入，以免把重点转向拒答能力。
6. **最大系统性偏差：**跨政策事件是作者有意挑选的，可能比真实支持流量更密集；部分主题也与仓库既有开发评测相邻。因此后续应独立测量真实 chunk 支持位置与检索表现，不能把这些属性描述直接当作效果真值。
