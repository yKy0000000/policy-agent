# Retrieval Candidate Review Sheet / 检索候选案例审查表

Source / 来源：`eval/retrieval_candidates.json`

## ret_012

### ID

`ret_012`

### Category

`semantic`

### Question

**English**

Is code used to study vulnerabilities automatically removed just because it could also be misused?

**中文**

用于研究漏洞的代码，会仅仅因为也可能被滥用就被自动移除吗？

### Expected sources

1. `title`: `GitHub Active Malware or Exploits`
   - `heading_contains`: `""`
   - `source_path`: `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`

### Supporting snippet

**English**

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

**中文**

> 请注意，GitHub 允许 dual-use content（双重用途内容），并支持发布用于漏洞、malware（恶意软件）或 exploit（漏洞利用）研究的内容，因为此类内容的发布和传播具有教育价值，并能为安全社区带来整体净收益。

### Notes

**English**

Tests the distinction between dual-use research and active abuse.

**中文**

用于测试 dual-use research（双重用途研究）与主动滥用行为之间的区分。

---

## ret_013

### ID

`ret_013`

### Category

`broad`

### Question

**English**

When can GitHub restrict or shut down an account?

**中文**

GitHub 在哪些情况下可以限制或关闭账户？

### Expected sources

1. `title`: `GitHub Terms of Service`
   - `heading_contains`: `GitHub May Terminate`
   - `source_path`: `Policies/github-terms/github-terms-of-service.md`
2. `title`: `GitHub Appeal and Reinstatement`
   - `heading_contains`: `What are Appeals and Reinstatements?`
   - `source_path`: `Policies/acceptable-use-policies/github-appeal-and-reinstatement.md`
3. `title`: `GitHub Community Guidelines`
   - `heading_contains`: `What happens if someone violates GitHub's policies?`
   - `source_path`: `Policies/github-terms/github-community-guidelines.md`

### Supporting snippet

**English**

> GitHub has the right to suspend or terminate your access to all or any part of the Website at any time, with or without cause, with or without notice, effective immediately.

**中文**

> GitHub 有权随时暂停或终止您对本网站全部或任何部分的访问，无论有无理由，也无论是否通知，均立即生效。

### Notes

**English**

Intentionally broad: termination authority, enforcement context, and appealability are all potentially relevant.

**中文**

此问题有意保持宽泛：终止权限、政策执行背景以及是否可以 appeal（申诉）都可能相关。

---

## ret_016

### ID

`ret_016`

### Category

`broad`

### Question

**English**

How does GitHub respond when a government or law-enforcement body asks it to remove content or disclose user data?

**中文**

当政府或执法机构要求 GitHub 移除内容或披露用户数据时，GitHub 会如何响应？

### Expected sources

1. `title`: `GitHub Government Takedown Policy`
   - `heading_contains`: `complete takedown request from a government`
   - `source_path`: `Policies/other-site-policies/github-government-takedown-policy.md`
2. `title`: `Guidelines for Legal Requests of User Data`
   - `heading_contains`: `Disclosure of non-public information`
   - `source_path`: `Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md`

### Supporting snippet

**English**

> limit the geographic scope of the takedown when possible and include that as part of the notification

**中文**

> 在可能的情况下限制下架措施的地理范围，并将这一点纳入通知内容

### Notes

**English**

Combines two distinct legal-request workflows and therefore has multiple valid sources.

**中文**

该问题合并了两种不同的法律请求处理流程，因此存在多个有效来源。

---

## ret_017

### ID

`ret_017`

### Category

`specific`

### Question

**English**

If a parent repository is disabled for exposing private information, are all of its forks disabled automatically?

**中文**

如果父仓库因暴露私人信息而被禁用，它的所有 fork（分叉仓库）是否也会被自动禁用？

### Expected sources

1. `title`: `GitHub Private Information Removal Policy`
   - `heading_contains`: `What About Forks?`
   - `source_path`: `Policies/content-removal-policies/github-private-information-removal-policy.md`

### Supporting snippet

**English**

> GitHub will not automatically disable forks when disabling a parent repository.

**中文**

> GitHub 在禁用父仓库时，不会自动禁用其 fork（分叉仓库）。

### Notes

**English**

Tests subsection precision because a similarly named forks section also exists in the DMCA policy.

**中文**

用于测试子章节检索的精确性，因为 DMCA 政策中也存在一个名称相近的 fork 章节。

---

## ret_022

### ID

`ret_022`

### Category

`unsupported`

### Question

**English**

What uptime percentage does GitHub guarantee for free personal accounts?

**中文**

GitHub 为免费个人账户保证的正常运行时间百分比是多少？

### Expected sources

`[]`

### Supporting snippet

**English**

`""`

**中文**

`""`（空）

### Notes

**English**

The loaded corpus does not clearly provide an uptime SLA for free personal accounts; the corporate terms mention an Enterprise Cloud SLA in a different context.

**中文**

已加载的语料并未明确提供适用于免费个人账户的正常运行时间 SLA（服务级别协议）；公司条款在另一种语境下提到了 Enterprise Cloud SLA。

---

## ret_023

### ID

`ret_023`

### Category

`unsupported`

### Question

**English**

In which exact physical data center is my specific repository stored?

**中文**

我的这个特定仓库具体存储在哪一个物理数据中心？

### Expected sources

`[]`

### Supporting snippet

**English**

`""`

**中文**

`""`（空）

### Notes

**English**

The privacy policies discuss international transfers and processing locations, but do not identify the physical data center for an individual repository.

**中文**

隐私政策讨论了国际数据传输和处理地点，但并未指出单个仓库所在的具体物理数据中心。

---

## ret_024

### ID

`ret_024`

### Category

`unsupported`

### Question

**English**

What is the maximum number of days GitHub will take to decide every account-suspension appeal?

**中文**

对于每一项账户暂停 appeal（申诉），GitHub 作出决定所需的最长天数是多少？

### Expected sources

`[]`

### Supporting snippet

**English**

`""`

**中文**

`""`（空）

### Notes

**English**

The Appeal and Reinstatement policy describes review and final decisions but does not clearly promise a universal maximum response time.

**中文**

Appeal and Reinstatement（申诉与恢复）政策说明了审查和最终决定流程，但并未明确承诺一个普遍适用的最长响应时间。

---

## multi_001

### ID

`multi_001`

### Category

`multi_turn`

### History

#### 1. `user`

**English**

How does GitHub handle requests to remove private information from a repository?

**中文**

GitHub 如何处理从仓库中移除私人信息的请求？

#### 2. `assistant`

**English**

GitHub's Private Information Removal Policy describes how it reviews reports and may disable qualifying content.

**中文**

GitHub 的 Private Information Removal Policy（私人信息移除政策）说明了 GitHub 如何审查报告，以及可能如何禁用符合条件的内容。

### Question

**English**

What happens to the forks?

**中文**

那些 fork（分叉仓库）会怎样？

### Standalone reference

**English**

What happens to forks when a parent repository is disabled under GitHub's Private Information Removal Policy?

**中文**

根据 GitHub 的 Private Information Removal Policy（私人信息移除政策），当父仓库被禁用时，其 fork（分叉仓库）会怎样？

### Expected sources

1. `title`: `GitHub Private Information Removal Policy`
   - `heading_contains`: `What About Forks?`
   - `source_path`: `Policies/content-removal-policies/github-private-information-removal-policy.md`

### Supporting snippet

**English**

> GitHub will not automatically disable forks when disabling a parent repository.

**中文**

> GitHub 在禁用父仓库时，不会自动禁用其 fork（分叉仓库）。

### Notes

**English**

The follow-up is ambiguous without the private-information-removal context; the DMCA policy has a competing forks section.

**中文**

如果缺少私人信息移除这一上下文，后续问题会有歧义；DMCA 政策中存在一个可能形成竞争匹配的 fork 章节。

---

## multi_004

### ID

`multi_004`

### Category

`multi_turn`

### History

#### 1. `user`

**English**

Does GitHub prohibit repositories that support malware or exploit campaigns?

**中文**

GitHub 是否禁止为 malware（恶意软件）或 exploit（漏洞利用）活动提供支持的仓库？

#### 2. `assistant`

**English**

GitHub prohibits using the platform in direct support of unlawful attacks that cause technical harm.

**中文**

GitHub 禁止使用该平台直接支持会造成技术损害的非法攻击。

### Question

**English**

What if it is for security research?

**中文**

如果是用于安全研究呢？

### Standalone reference

**English**

Does GitHub allow dual-use vulnerability, malware, or exploit content when it is posted for security research?

**中文**

如果出于安全研究目的发布，GitHub 是否允许具有 dual-use（双重用途）性质的漏洞、malware（恶意软件）或 exploit（漏洞利用）内容？

### Expected sources

1. `title`: `GitHub Active Malware or Exploits`
   - `heading_contains`: `""`
   - `source_path`: `Policies/acceptable-use-policies/github-active-malware-or-exploits.md`
2. `title`: `GitHub Acceptable Use Policies`
   - `heading_contains`: `Site Access and Safety`
   - `source_path`: `Policies/acceptable-use-policies/github-acceptable-use-policies.md`

### Supporting snippet

**English**

> Note that GitHub allows dual-use content and supports the posting of content that is used for research into vulnerabilities, malware, or exploits, as the publication and distribution of such content has educational value and provides a net benefit to the security community.

**中文**

> 请注意，GitHub 允许 dual-use content（双重用途内容），并支持发布用于漏洞、malware（恶意软件）或 exploit（漏洞利用）研究的内容，因为此类内容的发布和传播具有教育价值，并能为安全社区带来整体净收益。

### Notes

**English**

The follow-up needs the malware-policy context to resolve what 'it' means.

**中文**

这个后续问题需要 malware 政策的上下文，才能确定其中的 “it” 指代什么。
