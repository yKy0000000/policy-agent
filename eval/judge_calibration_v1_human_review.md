# Judge calibration v1 — AI-assisted blinded project-author review

Provenance: AI-assisted blinded project-author review. The project author made the final verdicts,
with AI translation and filtering used only to surface boundary cases for discussion. The review was
blinded: the reviewer did not see historical judge verdicts, cross-family judge verdicts, arm
identity, or historical score. This is not fully independent human annotation.

Review the candidate answer against every listed required criterion. Sources clarify the criterion;
a fact appearing only in a source or citation is not covered by the answer. Each review ID carries
exactly one verdict: `COVERED`, `MISSING`, or `AMBIGUOUS`. A brief reason is recorded only for
non-`COVERED` items.

## VAL-001-005

**User query:**

If I submit a DMCA counter notice for disabled GitHub content, what must the notice identify and what legal commitments am I making?

**Candidate answer:**

````text
To submit a DMCA counter notice for disabled GitHub content, the notice must:

**Identify the disabled content and its location.** You need to identify the content that was disabled and where it appeared; the disabled content should have been identified by URL in the takedown notice, and you simply copy the URL(s) you want to challenge [S1].

**Provide your contact information.** This includes your email address, name, telephone number, and physical address [S1].

**Include a good-faith belief statement under penalty of perjury.** Specifically: "I swear, under penalty of perjury, that I have a good-faith belief that the material was removed or disabled as a result of a mistake or misidentification of the material to be removed or disabled." You may also explain why you believe there was a mistake or misidentification [S1].

**Include a consent-to-jurisdiction statement.** Specifically: "I consent to the jurisdiction of Federal District Court for the judicial district in which my address is located (if in the United States, otherwise the Northern District of California where GitHub is located), and I will accept service of process from the person who provided the DMCA notification or an agent of such person" [S1].

**Include your physical or electronic signature** [S1].

**Include the acknowledgment statement** (optional in effect): "I have read and understand GitHub's Guide to Filing a DMCA Counter Notice." GitHub won't refuse to process an otherwise complete counter notice if you omit this, but it may ask you to go back and read the guidelines [S1].

**Legal commitments you are making:**

- A counter notice is a legal statement — not just to GitHub, but to the complaining party — which is why all fields must be filled out completely [S2].
- You consent to being sued: if the complaining party wishes to keep the content disabled, they must initiate a legal action seeking a court order to restrain you from engaging in infringing activity, and you consent to that in the counter notice [S2].
- Your statements are made under penalty of perjury [S2].
- Your counter notice will be published: after redacting personal information, GitHub publishes all complete and actionable counter notices, and may provide a complete unredacted copy to any party whose rights would be affected [S2].
- GitHub's role is limited: it exercises little discretion other than determining whether notices meet the minimum requirements of the DMCA; it is up to the parties (and their lawyers) to evaluate the merit of their claims [S2].

Note that if you submit a counter notice, GitHub will wait 10–14 days and then re-enable your content unless the copyright owner initiates a legal action against you before then [S4].
````

**Citation map (only citations used in the answer):**

- [S1] Guide to Submitting a DMCA Counter Notice — Your Counter Notice Must... — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md
- [S2] Guide to Submitting a DMCA Counter Notice — Before You Start — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md
- [S4] Guide to Submitting a DMCA Counter Notice —  — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md

### JC-001 · VAL-001-005-F01

**Required aspect:** A counter notice must identify the disabled content and its prior URL.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · Your Counter Notice Must...

````text
1. ***Identify the content that was disabled and the location where it appeared.*** <!-- markdownlint-disable-line emphasis-style --> The disabled content should have been identified by URL in the takedown notice. You simply need to copy the URL(s) that you want to challenge.
````

**JC-001 verdict:** COVERED
**JC-001 brief_reason:**

### JC-002 · VAL-001-005-F02

**Required aspect:** It must provide the submitter's email, name, phone, and physical address.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · Your Counter Notice Must...

````text
1. **Provide your contact information.** Include your email address, name, telephone number, and physical address.
````

**JC-002 verdict:** COVERED
**JC-002 brief_reason:**

### JC-003 · VAL-001-005-F03

**Required aspect:** It must include a sworn good-faith belief that removal was a mistake or misidentification.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · Your Counter Notice Must...

````text
1. ***Include the following statement: "I swear, under penalty of perjury, that I have a good-faith belief that the material was removed or disabled as a result of a mistake or misidentification of the material to be removed or disabled."*** <!-- markdownlint-disable-line emphasis-style --> You may also choose to communicate the reasons why you believe there was a mistake or misidentification. If you think of your counter notice as a "note" to the complaining party, this is a chance to explain why they should not take the next step and file a lawsuit in response. This is yet another reason to work with a lawyer when submitting a counter notice.
````

**JC-003 verdict:** COVERED
**JC-003 brief_reason:**

### JC-004 · VAL-001-005-F04

**Required aspect:** It must consent to the specified federal court's jurisdiction and accept service of process.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · Your Counter Notice Must...

````text
1. ***Include the following statement: "I consent to the jurisdiction of Federal District Court for the judicial district in which my address is located (if in the United States, otherwise the Northern District of California where GitHub is located), and I will accept service of process from the person who provided the DMCA notification or an agent of such person."*** <!-- markdownlint-disable-line emphasis-style -->
````

**JC-004 verdict:** COVERED
**JC-004 brief_reason:**

### JC-005 · VAL-001-005-F05

**Required aspect:** It must include a physical or electronic signature.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · Your Counter Notice Must...

````text
1. **Include your physical or electronic signature.**
````

**JC-005 verdict:** COVERED
**JC-005 brief_reason:**

## VAL-001-007

**User query:**

Before asking GitHub to remove private information, how should I prepare the request and what may slow its review?

**Candidate answer:**

````text
To prepare a private information removal request:

- **Try contacting the user first.** This is not strictly required but is appreciated; you may find contact info on their profile, README, or Support file, or reach them via an issue or pull request [S1].
- **Have a trained professional evaluate the facts.** Avoid automated bots or bulk complaints; these often lack sufficient explanations, require back-and-forth, and cause delays even when valid [S1].
- **Send the correct type of request.** This process is only for high-risk private information, not for other content such as potentially infringing content, and other removal requests cannot be processed simultaneously [S1]. Send private information requests separately from infringement requests [S1].
- **Investigate and provide required details yourself.** You must conduct your own investigation and provide the details GitHub requires, most importantly an explanation of how the data poses a security risk; GitHub will not search for or make initial determinations about private information on your behalf [S3].
- **Be specific about location.** Complaints must be as specific as possible so GitHub can verify complete removal and know exactly where to look [S5].
- **Submit via the contact form with plain text.** Include a plain-text version of your request in the message body; attachments may cause processing delays [S2].

What may slow review:

- **Volume of requests.** Due to request volume, review may take time [S1].
- **Additional or multiple requests.** Additional requests, or multiple requests from additional points of contact, may result in delays [S1].
- **Attachments.** Sending your request as an attachment may cause processing delays [S2].
- **Insufficient detail.** If the request is not detailed enough to demonstrate the security risk and let GitHub locate the data, GitHub will reply asking for more information [S3].
- **Requests covering entire files or repositories.** You must justify the security risk, and this may increase processing time [S4].
- **Bot-submitted or bulk complaints.** These often lack sufficient explanations, requiring back-and-forth and causing delays [S1].

Note: The provided policies do not specify a maximum or guaranteed review timeframe beyond stating that processing may take time due to volume [S1].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Private Information Removal Policy — Things to Know — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md
- [S2] GitHub Private Information Removal Policy — How to Submit Your Request — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md
- [S3] GitHub Private Information Removal Policy — How Does This Actually Work? — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md
- [S4] GitHub Private Information Removal Policy — What is Private Information? > Private information removal requests are _not_ appropriate for: — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md
- [S5] GitHub Private Information Removal Policy — Sending A Private Information Removal Request — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/github-private-information-removal-policy.md

### JC-006 · VAL-001-007-F01

**Required aspect:** Contacting the user first is encouraged but is not required.

**Supporting source excerpt(s):**

- content-removal-policies/github-private-information-removal-policy.md · Things to Know

````text
**Ask Nicely First.** A great first step before sending us a request to remove data is to try contacting the user directly. They may have listed contact information on their public profile page or in the repository's README or Support file, or you could get in touch by creating an issue or pull request in the repository. This is not strictly required, but it is appreciated.
````

**JC-006 verdict:** COVERED
**JC-006 brief_reason:**

### JC-007 · VAL-001-007-F03

**Required aspect:** The process is an exceptional service for high-risk content and cannot handle unrelated removal requests at the same time.

**Supporting source excerpt(s):**

- content-removal-policies/github-private-information-removal-policy.md · Things to Know

````text
**Send In The Correct Request.** As noted above, we offer this private information removal process as an exceptional service only for high-risk content. We are not able to use this process to remove other kinds of content, such as potentially infringing content, and we are not able to process any other kinds of removal requests simultaneously while processing private information removal requests. We will be able to help you more quickly if you send in your private information removal requests separately from any requests to remove potentially infringing content. If you are unsure whether your request involves only private information or also involves other legal matters, please consult legal counsel.
````

**JC-007 verdict:** COVERED
**JC-007 brief_reason:**

### JC-008 · VAL-001-007-F04

**Required aspect:** Multiple or additional requests can delay review.

**Supporting source excerpt(s):**

- content-removal-policies/github-private-information-removal-policy.md · Things to Know

````text
**Processing Time.** While we do process private information removal requests as quickly as possible, due to the volume of requests we process, it may take some time for your request to be reviewed. Additional requests, or multiple requests from additional points of contact, may result in delays.
````

**JC-008 verdict:** COVERED
**JC-008 brief_reason:**

## VAL-001-008

**User query:**

I have a complete DMCA counter notice. How should I send it, and when does the waiting period begin if I use postal mail?

**Candidate answer:**

````text
You can submit your counter notice through GitHub's DMCA contact form, by email to copyright@github.com, or by physical mail [S1]. The fastest option is the contact form; plain-text email is also much faster than PDF attachments or physical mail [S1].

If you send it by physical mail, the 10–14 day waiting period starts from when GitHub **receives** your counter notice, not when you send it [S1]. The mailing address is GitHub, Inc, Attn: DMCA Agent, 88 Colin P Kelly Jr St, San Francisco, CA. 94107 [S1].
````

**Citation map (only citations used in the answer):**

- [S1] Guide to Submitting a DMCA Counter Notice — How to Submit Your Counter Notice — https://github.com/github/site-policy/blob/main/Policies/content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md

### JC-009 · VAL-001-008-F01

**Required aspect:** The online DMCA form is the fastest way to get a response.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · How to Submit Your Counter Notice

````text
The fastest way to get a response is to enter your information and answer all the questions on our {% data variables.contact.contact_dmca %}.
````

**JC-009 verdict:** COVERED
**JC-009 brief_reason:**

### JC-010 · VAL-001-008-F02

**Required aspect:** Email submissions should include a plain-text version in the email body even if attached.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · How to Submit Your Counter Notice

````text
You can also send an email notification to <copyright@github.com>. You may include an attachment if you like, but please also include a plain-text version of your letter in the body of your message.
````

**JC-010 verdict:** MISSING
**JC-010 brief_reason:** Did not state that a plain-text copy should also appear in the email body when an attachment is used.

### JC-011 · VAL-001-008-F03

**Required aspect:** Physical mail takes substantially longer to receive and process.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · How to Submit Your Counter Notice

````text
If you must send your notice by physical mail, you can do that too, but it will take _substantially_ longer for us to receive and respond to it—and the 10-14 day waiting period starts from when we _receive_ your counter notice. Notices we receive via plain-text email have a much faster turnaround than PDF attachments or physical mail. If you still wish to mail us your notice, our physical address is:
````

**JC-011 verdict:** COVERED
**JC-011 brief_reason:**

### JC-012 · VAL-001-008-F04

**Required aspect:** The 10–14 day waiting period begins when GitHub receives the counter notice.

**Supporting source excerpt(s):**

- content-removal-policies/guide-to-submitting-a-dmca-counter-notice.md · How to Submit Your Counter Notice

````text
If you must send your notice by physical mail, you can do that too, but it will take _substantially_ longer for us to receive and respond to it—and the 10-14 day waiting period starts from when we _receive_ your counter notice. Notices we receive via plain-text email have a much faster turnaround than PDF attachments or physical mail. If you still wish to mail us your notice, our physical address is:
````

**JC-012 verdict:** COVERED
**JC-012 brief_reason:**

## VAL-001-012

**User query:**

A GitHub user I was close to has died. What can an authorized person ask GitHub to do with the account, and what proof might GitHub request?

**Candidate answer:**

````text
An authorized individual can ask GitHub to determine what happens to the deceased user's account content, including actions such as transferring public repositories or canceling billing on the account [S1]. Requests should be made through the GitHub Support portal by clicking **Contact us**, providing: your name; contact information; the deceased account holder's name and GitHub username; your relationship to the deceased (including whether you were designated as account successor on GitHub.com); if designated as successor, your GitHub username; and the action you are seeking [S1].

GitHub may follow up requesting additional information to verify authorization, such as a copy of your photo identification, a copy of the death certificate, and documentation confirming you are authorized to act in relation to the deceased user's account [S1].

The provided published policies do not specify any other particular proof GitHub might request beyond these examples.
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Deceased User Policy —  — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/github-deceased-user-policy.md

### JC-013 · VAL-001-012-F01

**Required aspect:** Next of kin, a designated successor, or another authorized person can request action on a deceased user's account.

**Supporting source excerpt(s):**

- other-site-policies/github-deceased-user-policy.md · document body

````text
If you are next of kin, a [pre-designated successor](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/maintaining-ownership-continuity-of-your-personal-accounts-repositories), or other authorized individual (which could include a collaborator or business partner) of a deceased user and would like to make a request regarding their account, you can reach out to us through the [GitHub Support portal](https://support.github.com/). In the portal, click **Contact us**, and provide the following information in your message:
````

**JC-013 verdict:** MISSING
**JC-013 brief_reason:** "Authorized individual" is too generic and does not clearly identify next of kin / designated successor as eligible requester categories.

### JC-014 · VAL-001-012-F04

**Required aspect:** A request must explain the requester's relationship to the deceased user.

**Supporting source excerpt(s):**

- other-site-policies/github-deceased-user-policy.md · document body

````text
* Your relationship to the deceased account holder (please include whether you have been designated as the account successor on GitHub.com)
````

Context excerpt:

````text
If you are next of kin, a [pre-designated successor](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/maintaining-ownership-continuity-of-your-personal-accounts-repositories), or other authorized individual (which could include a collaborator or business partner) of a deceased user and would like to make a request regarding their account, you can reach out to us through the [GitHub Support portal](https://support.github.com/). In the portal, click **Contact us**, and provide the following information in your message:
````

**JC-014 verdict:** COVERED
**JC-014 brief_reason:**

### JC-015 · VAL-001-012-F05

**Required aspect:** The requester must say what action is sought, such as transferring public repositories or canceling billing.

**Supporting source excerpt(s):**

- other-site-policies/github-deceased-user-policy.md · document body

````text
* What action you are seeking (e.g. transfer public repositories, cancel billing on account)
````

Context excerpt:

````text
If you are next of kin, a [pre-designated successor](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/maintaining-ownership-continuity-of-your-personal-accounts-repositories), or other authorized individual (which could include a collaborator or business partner) of a deceased user and would like to make a request regarding their account, you can reach out to us through the [GitHub Support portal](https://support.github.com/). In the portal, click **Contact us**, and provide the following information in your message:
````

**JC-015 verdict:** COVERED
**JC-015 brief_reason:**

### JC-016 · VAL-001-012-F06

**Required aspect:** GitHub may request identification, a death certificate, or evidence of authority before processing.

**Supporting source excerpt(s):**

- other-site-policies/github-deceased-user-policy.md · document body

````text
Once we have received your request, we may follow up with a request for additional information, such as a copy of your photo identification, copy of the death certificate, and documentation confirming you are authorized to act in relation to the deceased user’s account, to verify that we are properly authorized to process your request.
````

**JC-016 verdict:** COVERED
**JC-016 brief_reason:**

## VAL-001-016

**User query:**

Someone shared personal details and a photo of me on GitHub. How does the privacy rule treat public information, consent, and hostile context?

**Candidate answer:**

````text
Under GitHub's doxxing and invasion-of-privacy policy, posting other people's personal information is prohibited, including private email addresses, phone numbers, physical addresses or other private location information, and other private information that may pose a safety or security risk [S1].

On photos: GitHub may consider photos or videos taken or distributed without the subject's consent to be an invasion of privacy, especially when the material presents a safety risk to the subject, such as intimidation or harassment [S1].

On public availability and context: GitHub will take context into account, as well as whether the reported content is publicly available elsewhere [S1]. Sharing publicly available content may not itself violate the policy, but if the information is shared with the intent to harass or incite other abusive behavior, it may violate GitHub's prohibition against bullying and harassment [S1].

On hostile context specifically: the evidence addresses intent to harass or incite abuse as potentially triggering the bullying and harassment prohibition, and notes that safety risk (e.g., intimidation or harassment) weighs toward treating consent-less photos as an invasion of privacy [S1]. The provided policies do not specify further criteria for evaluating "hostile context" beyond these points.

For reporting or removal options, the policy points to GitHub's Private Information Removal Policy and abuse-reporting instructions [S1].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Doxxing and Invasion of Privacy —  — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md

### JC-017 · VAL-001-016-F01

**Required aspect:** Posting another person's personal information is prohibited.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md · document body

````text
Don't post other people's personal information. This includes:
````

**JC-017 verdict:** COVERED
**JC-017 brief_reason:**

### JC-018 · VAL-001-016-F02

**Required aspect:** Nonconsensual photos or videos may be an invasion of privacy, especially when they pose a safety risk.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md · document body

````text
We may consider other information, such as photos or videos that were taken or distributed without the subject's consent, to be an invasion of privacy, especially when such material presents a safety risk to the subject, such as in the case of intimidation or harassment.
````

**JC-018 verdict:** COVERED
**JC-018 brief_reason:**

### JC-019 · VAL-001-016-F03

**Required aspect:** GitHub considers whether reported information is already publicly available elsewhere.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md · document body

````text
GitHub will take context into account as well as whether the reported content is publicly available elsewhere. Please note, however, that while sharing publicly available content may not be a violation of this policy, if the information is shared with the intent to harass or incite other abusive behavior, it may violate our prohibition against [bullying and harassment](/site-policy/acceptable-use-policies/github-bullying-and-harassment).
````

**JC-019 verdict:** COVERED
**JC-019 brief_reason:**

### JC-020 · VAL-001-016-F04

**Required aspect:** Public information shared with intent to harass may violate the bullying and harassment policy.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-doxxing-and-invasion-of-privacy.md · document body

````text
GitHub will take context into account as well as whether the reported content is publicly available elsewhere. Please note, however, that while sharing publicly available content may not be a violation of this policy, if the information is shared with the intent to harass or incite other abusive behavior, it may violate our prohibition against [bullying and harassment](/site-policy/acceptable-use-policies/github-bullying-and-harassment).
````

**JC-020 verdict:** COVERED
**JC-020 brief_reason:**

## VAL-001-019

**User query:**

I'm building a generative-media project on GitHub. Which harmful uses are barred, and how does GitHub assess what a project is meant to enable?

**Candidate answer:**

````text
**Barred harmful uses (synthetic media/AI tools)**

GitHub does not allow projects designed for, encouraging, promoting, supporting, or suggesting use of large language models or other synthetic/manipulated media tools to create [S1]:

- Sexual material involving minors or other content constituting Child Sexual Abuse Material under GitHub policies [S1]
- Violent extremist propaganda or other content constituting Terrorist or Violent Extremist Content under GitHub policies [S1]
- Sexually explicit media of people without their consent or other content constituting Non-Consensual Intimate Imagery under GitHub policies [S1]

**How GitHub assesses what a project is meant to enable**

GitHub evaluates violations by examining a project in context, which may include factors such as [S1]:

- How the project is configured
- How it is marketed
- Information in its README or other documentation
- External sites or resources it links to
- The nature of support provided by project maintainers
- Any other relevant facts indicating a likelihood of furthering one of the prohibited uses [S1]

The provided published policies do not specify any additional assessment methodology beyond these contextual factors.
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Synthetic Media and AI Tools —  — https://github.com/github/site-policy/blob/main/Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md

### JC-021 · VAL-001-019-F01

**Required aspect:** Projects designed to facilitate synthetic child sexual abuse material are prohibited.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-synthetic-media-and-ai-tools.md · document body

````text
* Sexual material involving minors or any other content that would constitute [Child Sexual Abuse Material](/site-policy/acceptable-use-policies/github-child-sexual-exploitation-or-abuse) under our policies
````

Context excerpt:

````text
GitHub does not allow any projects that are designed for, encourage, promote, support, or suggest in any way the use of large language models or any other synthetic or manipulated media tools for the creation of:
````

**JC-021 verdict:** COVERED
**JC-021 brief_reason:**

### JC-022 · VAL-001-019-F02

**Required aspect:** Projects designed to facilitate violent extremist propaganda are prohibited.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-synthetic-media-and-ai-tools.md · document body

````text
* Violent extremist propaganda or any other content that would constitute [Terrorist or Violent Extremist Content](/site-policy/acceptable-use-policies/github-terrorism-and-violent-extremism) under our policies
````

Context excerpt:

````text
GitHub does not allow any projects that are designed for, encourage, promote, support, or suggest in any way the use of large language models or any other synthetic or manipulated media tools for the creation of:
````

**JC-022 verdict:** COVERED
**JC-022 brief_reason:**

### JC-023 · VAL-001-019-F03

**Required aspect:** Projects designed to facilitate nonconsensual sexually explicit media are prohibited.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-synthetic-media-and-ai-tools.md · document body

````text
* Sexually explicit media of people without their consent or any other content that would constitute [Non-Consensual Intimate Imagery](/site-policy/acceptable-use-policies/github-non-consensual-intimate-imagery) under our policies
````

Context excerpt:

````text
GitHub does not allow any projects that are designed for, encourage, promote, support, or suggest in any way the use of large language models or any other synthetic or manipulated media tools for the creation of:
````

**JC-023 verdict:** COVERED
**JC-023 brief_reason:**

### JC-024 · VAL-001-019-F04

**Required aspect:** GitHub examines project context, including configuration, marketing, and documentation, when assessing violations.

**Supporting source excerpt(s):**

- acceptable-use-policies/github-synthetic-media-and-ai-tools.md · document body

````text
GitHub evaluates violations of this policy by examining a project in context. This could include an evaluation of many factors: how a project is configured; how it is marketed; the information provided in its README or other documentation; the external sites or resources it links to; the nature of support provided by the project maintainers; or any other relevant facts that indicate a likelihood of furthering one of the prohibited uses above.
````

**JC-024 verdict:** COVERED
**JC-024 brief_reason:**

## VAL-001-020

**User query:**

What are GitHub's website cookies used for, and how should I treat the published cookie list over time?

**Candidate answer:**

````text
GitHub uses cookies to provide and secure its websites and to analyze website usage in order to offer a good user experience [S1]. More specifically, GitHub states it uses cookies to provide, secure, and improve the Service or develop new features, such as keeping you logged in, remembering your preferences, identifying your device for security and fraud purposes, compiling statistical reports, and providing information for future development [S5]. Cookies and similar technologies are also used to store preferences and settings, enable sign-in, analyze performance, track interactions with the Services, develop inferences, combat fraud, and fulfill other legitimate purposes [S2]. Some cookies are provided by third parties, including service providers and advertising partners, and may be used for purposes such as targeted advertising [S2]. For Enterprise Marketing Pages, GitHub may use non-essential cookies to gather information about enterprise users' interests and online activities to personalize experiences and to serve and measure targeted advertising and marketing [S5].

As for how to treat the published cookie list over time: GitHub states that since the number and names of cookies may change, the table may be updated from time to time, and it provides instructions for receiving notifications of updates to the list [S1]. The published policies do not specify any other guidance on how users should treat the list over time beyond noting it may change and offering update notifications [S1].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Cookies — Cookies — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-cookies.md
- [S2] GitHub General Privacy Statement — Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies? — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-general-privacy-statement.md
- [S5] GitHub General Privacy Statement — Our use of cookies and tracking technologies > Cookies and tracking technologies — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-general-privacy-statement.md

### JC-025 · VAL-001-020-F01

**Required aspect:** GitHub uses cookies to provide its websites.

**Supporting source excerpt(s):**

- privacy-policies/github-cookies.md · Cookies

````text
GitHub uses cookies to provide and secure our websites, as well as to analyze the usage of our websites, in order to offer you a great user experience. Please take a look at our [Privacy Statement](/github/site-policy/github-privacy-statement#our-use-of-cookies-and-tracking-technologies) if you’d like more information about cookies, and on how and why we use them and cookie-related personal data. You can change your preference about non-essential cookies at any time by following [these instructions](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-personal-account-settings/managing-your-cookie-preferences-for-githubs-enterprise-marketing-pages).
````

**JC-025 verdict:** COVERED
**JC-025 brief_reason:**

### JC-026 · VAL-001-020-F02

**Required aspect:** GitHub uses cookies to secure its websites.

**Supporting source excerpt(s):**

- privacy-policies/github-cookies.md · Cookies

````text
GitHub uses cookies to provide and secure our websites, as well as to analyze the usage of our websites, in order to offer you a great user experience. Please take a look at our [Privacy Statement](/github/site-policy/github-privacy-statement#our-use-of-cookies-and-tracking-technologies) if you’d like more information about cookies, and on how and why we use them and cookie-related personal data. You can change your preference about non-essential cookies at any time by following [these instructions](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-personal-account-settings/managing-your-cookie-preferences-for-githubs-enterprise-marketing-pages).
````

**JC-026 verdict:** COVERED
**JC-026 brief_reason:**

### JC-027 · VAL-001-020-F03

**Required aspect:** GitHub uses cookies to analyze website usage.

**Supporting source excerpt(s):**

- privacy-policies/github-cookies.md · Cookies

````text
GitHub uses cookies to provide and secure our websites, as well as to analyze the usage of our websites, in order to offer you a great user experience. Please take a look at our [Privacy Statement](/github/site-policy/github-privacy-statement#our-use-of-cookies-and-tracking-technologies) if you’d like more information about cookies, and on how and why we use them and cookie-related personal data. You can change your preference about non-essential cookies at any time by following [these instructions](/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-personal-account-settings/managing-your-cookie-preferences-for-githubs-enterprise-marketing-pages).
````

**JC-027 verdict:** COVERED
**JC-027 brief_reason:**

### JC-028 · VAL-001-020-F04

**Required aspect:** The published cookie list may change as cookie names and numbers change.

**Supporting source excerpt(s):**

- privacy-policies/github-cookies.md · Cookies

````text
Since the number and names of cookies may change, the table below may be updated from time to time. To receive notifications of updates to this list, please follow the instructions provided in [About notifications](/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/about-notifications).
````

**JC-028 verdict:** COVERED
**JC-028 brief_reason:**

## VAL-001-021

**User query:**

I explored a GitHub job opening and later became an employee. Can GitHub use the data it collected at the first stage for the next one?

**Candidate answer:**

````text
Yes. GitHub may use candidate data for a compatible employment purpose. Its candidate privacy notice states that personal data will be used only for the purposes for which it was collected unless GitHub reasonably needs it for another compatible purpose with a legal basis, and it gives the example that data provided while researching job openings may later be processed for the purpose of entering into an employment relationship once you apply for and obtain a role [S2]. The notice also describes processing candidate data to on-board you if you accept an offer [S1], and lists recruitment/hiring and payroll, benefits, and related employment purposes [S5].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Global Data Privacy Notice for Candidates — Overview > Personal Data that We Process — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-candidate-privacy-policy.md
- [S2] GitHub Global Data Privacy Notice for Candidates — Overview > Change of Purpose — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-candidate-privacy-policy.md
- [S5] GitHub Global Data Privacy Notice for Candidates — Overview > Why We Process Personal Data — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-candidate-privacy-policy.md

### JC-029 · VAL-001-021-F01

**Required aspect:** Candidate personal data is normally used only for the purpose for which it was collected.

**Supporting source excerpt(s):**

- privacy-policies/github-candidate-privacy-policy.md · Change of Purpose

````text
We will use your personal data only for the purposes for which it was collected, unless we reasonably need it for another compatible purpose and there is a legal basis for further processing. For example, relying upon our legitimate interest in recruiting candidates for roles at GitHub, we may process the personal data you provided while researching job openings. However, once you apply for and are successful in obtaining a role, we may process your personal data for the purpose of entering into an employment relationship with you.
````

**JC-029 verdict:** COVERED
**JC-029 brief_reason:**

### JC-030 · VAL-001-021-F02

**Required aspect:** A different compatible use requires a reasonable need and legal basis for further processing.

**Supporting source excerpt(s):**

- privacy-policies/github-candidate-privacy-policy.md · Change of Purpose

````text
We will use your personal data only for the purposes for which it was collected, unless we reasonably need it for another compatible purpose and there is a legal basis for further processing. For example, relying upon our legitimate interest in recruiting candidates for roles at GitHub, we may process the personal data you provided while researching job openings. However, once you apply for and are successful in obtaining a role, we may process your personal data for the purpose of entering into an employment relationship with you.
````

**JC-030 verdict:** COVERED
**JC-030 brief_reason:**

### JC-031 · VAL-001-021-F03

**Required aspect:** Data from exploring job openings may be processed for recruiting.

**Supporting source excerpt(s):**

- privacy-policies/github-candidate-privacy-policy.md · Change of Purpose

````text
We will use your personal data only for the purposes for which it was collected, unless we reasonably need it for another compatible purpose and there is a legal basis for further processing. For example, relying upon our legitimate interest in recruiting candidates for roles at GitHub, we may process the personal data you provided while researching job openings. However, once you apply for and are successful in obtaining a role, we may process your personal data for the purpose of entering into an employment relationship with you.
````

**JC-031 verdict:** COVERED
**JC-031 brief_reason:**

### JC-032 · VAL-001-021-F04

**Required aspect:** After successful application, candidate data may be processed to enter an employment relationship.

**Supporting source excerpt(s):**

- privacy-policies/github-candidate-privacy-policy.md · Change of Purpose

````text
We will use your personal data only for the purposes for which it was collected, unless we reasonably need it for another compatible purpose and there is a legal basis for further processing. For example, relying upon our legitimate interest in recruiting candidates for roles at GitHub, we may process the personal data you provided while researching job openings. However, once you apply for and are successful in obtaining a role, we may process your personal data for the purpose of entering into an employment relationship with you.
````

**JC-032 verdict:** COVERED
**JC-032 brief_reason:**

## VAL-001-024

**User query:**

What information may GitHub collect automatically when I use its services or visit its site, and how do essential and optional cookies differ?

**Candidate answer:**

````text
GitHub collects the following information automatically when you use its services or visit its site:

- **Service usage information:** IP address, device information, session details, date and time of requests, device type and ID, operating system and application version, information related to your repository contributions, and performance of specific features or services [S1].
- **Website usage data:** referring site, date and time of visit, pages viewed, and links clicked [S1].
- **Geolocation information:** regional geolocation data, depending on the service's functionality [S1].
- **Email marketing interactions:** via web beacons, information on device type, email client, email reception, opens, and link clicks [S1].
- **Data from third-party buttons, tools, and content:** engaging with these may automatically send certain browser information to those companies [S1].

**Essential vs. optional cookies:**

- **Essential cookies and similar tracking technologies** are used to provide essential functionality, such as storing settings and recognizing you while you use the services [S1]. GitHub's "Required Cookies" perform essential website functions—for example, logging you in, saving language preferences, providing a shopping cart experience, improving performance, routing traffic between web servers, detecting screen size, determining page load times, improving user experience, and audience measurement; these are necessary for the websites to work [S5].
- **Non-essential cookies** include online analytics products used to analyze how de-identified users use the services and enhance your experience, as well as third-party cookies for interest-based advertising; in some jurisdictions, these are only used after obtaining your consent [S1]. Non-essential categories include **Analytics** (understanding how you use the websites, and in some cases providing personalized advertising), **Social Media** (showing ads and content based on social media profiles and activity), and **Advertising** (showing new ads based on ads already seen, and tracking ad clicks or purchases after clicking an ad) [S5]. GitHub places non-essential cookies on pages where it markets products and services to enterprise customers, such as resources.github.com [S5].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub General Privacy Statement — Personal Data We Collect > Automatically — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-general-privacy-statement.md
- [S5] GitHub General Privacy Statement — Our use of cookies and tracking technologies > Cookies and tracking technologies > How do we and our partners use cookies and similar technologies? — https://github.com/github/site-policy/blob/main/Policies/privacy-policies/github-general-privacy-statement.md

### JC-033 · VAL-001-024-F01

**Required aspect:** Service usage collection includes IP address, device and session details.

**Supporting source excerpt(s):**

- privacy-policies/github-general-privacy-statement.md · Automatically

````text
* Service Usage Information: We collect data about your interactions with the Services, such as IP address, device information, session details, date and time of requests, device type and ID, operating system and application version, information related to your contributions to repositories, and performance of specific features or Services.
````

**JC-033 verdict:** COVERED
**JC-033 brief_reason:**

### JC-034 · VAL-001-024-F02

**Required aspect:** Website logs include the referring site, pages viewed, and links clicked.

**Supporting source excerpt(s):**

- privacy-policies/github-general-privacy-statement.md · Automatically

````text
* Website Usage Data: We automatically log data about your Website interactions, including the referring site, date and time of visit, pages viewed, and links clicked.
````

**JC-034 verdict:** COVERED
**JC-034 brief_reason:**

### JC-035 · VAL-001-024-F03

**Required aspect:** Essential cookies support functions such as stored settings and recognition.

**Supporting source excerpt(s):**

- privacy-policies/github-general-privacy-statement.md · Automatically

````text
* Essential Cookies and Similar Tracking Technologies: We use cookies and similar technologies to provide essential functionality like storing settings and recognizing you while using our Services.
````

**JC-035 verdict:** COVERED
**JC-035 brief_reason:**

### JC-036 · VAL-001-024-F04

**Required aspect:** Non-essential analytics cookies may depend on jurisdiction and consent.

**Supporting source excerpt(s):**

- privacy-policies/github-general-privacy-statement.md · Automatically

````text
* Non-essential Cookies: Depending on your jurisdiction, we may use online analytics products that use cookies to help us analyze how de-identified users use our Services and to enhance your experience when you use the Services. We may also employ third-party Cookies to gather data for interest-based advertising. In some jurisdictions, we only use non-essential cookies after obtaining your consent. See [this](#what-are-your-cookie-choices-and-controls) section for more details and control options.
````

**JC-036 verdict:** COVERED
**JC-036 brief_reason:**

## VAL-001-026

**User query:**

I publish a GitHub Copilot Extension. What permission do I get to use the platform, what can GitHub do if I violate its policy, and can I appeal?

**Candidate answer:**

````text
**Permission you get:** As long as you remain compliant with the Agreement and associated requirements, GitHub grants you a limited, worldwide, non-exclusive, non-transferable license during the term of the Agreement to access and use the Platform for publishing, developing, demonstrating, testing, and supporting interoperability and integrations between your Extension and GitHub Copilot [S1]. No other rights or licenses to GitHub Copilot or other GitHub products/services are granted beyond those expressly given [S1].

**What GitHub can do if you violate its policy:** Violations may result in removing the Extension from the Platform, token revocation, Account or Extension suspension, User notification, legal action, or any other action deemed necessary by GitHub [S1]. GitHub may or may not provide notice before taking action [S1]. GitHub also reserves the right to modify or discontinue your Platform access temporarily or permanently, with or without notice [S1], and may periodically audit Extensions and collect information about Users using your Extension [S1].

**Appeals:** Yes—appeals may be submitted via the GitHub Appeal and Reinstatement Process [S1].

One note for context: the policy states that GitHub Copilot Extensions are being deprecated on November 10, 2025, in favor of the Model Context Protocol (MCP) [S5].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Copilot Extension Developer Policy — 1. Services — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-copilot-extension-developer-policy.md
- [S5] GitHub Copilot Extension Developer Policy —  — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-copilot-extension-developer-policy.md

### JC-037 · VAL-001-026-F01

**Required aspect:** The platform license is limited to compliant extension development and related interoperability purposes.

**Supporting source excerpt(s):**

- github-terms/github-copilot-extension-developer-policy.md · 1. Services

````text
By using our Platform, you agree to adhere to this policy and all GitHub terms and policies incorporated by reference. You must also adhere to all technical specifications and requirements published by GitHub. GitHub may update this Agreement and any requirements at any time, and you should periodically review this Agreement and all technical specifications and requirements to ensure compliance with the most recent version. So long as you remain compliant with this Agreement and associated requirements within, we grant you a limited, worldwide, non-exclusive, non-transferable license during the term of the Agreement to access and use the Platform for the purpose of publishing, developing, demonstrating, testing and supporting interoperability and integrations between Your Extension and GitHub Copilot.
````

**JC-037 verdict:** COVERED
**JC-037 brief_reason:**

### JC-038 · VAL-001-026-F04

**Required aspect:** Violations may lead to extension removal, token revocation, or account or extension suspension.

**Supporting source excerpt(s):**

- github-terms/github-copilot-extension-developer-policy.md · 1. Services

````text
Violations of this Agreement may result in removing the Extension from the Platform, token revocation, Account or Extension suspension, User notification, legal action or any other action deemed necessary by Us. If requested, You must provide us with proof of compliance with this Agreement. If You violate this Agreement we may or may not provide notice before taking action. Appeals may be submitted via the GitHub Appeal and Reinstatement Process. Please note that we may periodically audit Extensions and collect information about Users using Your Extension.
````

**JC-038 verdict:** COVERED
**JC-038 brief_reason:**

### JC-039 · VAL-001-026-F05

**Required aspect:** Appeals may be submitted through GitHub's appeal and reinstatement process.

**Supporting source excerpt(s):**

- github-terms/github-copilot-extension-developer-policy.md · 1. Services

````text
Violations of this Agreement may result in removing the Extension from the Platform, token revocation, Account or Extension suspension, User notification, legal action or any other action deemed necessary by Us. If requested, You must provide us with proof of compliance with this Agreement. If You violate this Agreement we may or may not provide notice before taking action. Appeals may be submitted via the GitHub Appeal and Reinstatement Process. Please note that we may periodically audit Extensions and collect information about Users using Your Extension.
````

**JC-039 verdict:** COVERED
**JC-039 brief_reason:**

## VAL-001-030

**User query:**

We're considering a GitHub preview for important work. What risks and service commitments should we expect before it becomes generally available?

**Candidate answer:**

````text
Based on the provided policies, here is what you should expect for a GitHub preview:

**Service commitments (or lack thereof)**
- Previews are provided "AS-IS", "WITH ALL FAULTS" and "AS AVAILABLE" [S2].
- GitHub may change or discontinue Previews at any time without notice [S2]. Pre-release software may be changed for the final commercial version, or GitHub may not release a commercial version at all [S5].
- GitHub is not obligated to provide maintenance, technical support, or updates [S5].
- GitHub grants only a limited right to use a non-production instance of the Preview [S2].

**Risks**
- Pre-release software may not operate correctly, may delete or corrupt your data, or have other bugs, and may not work the way a final commercial version will [S5].
- GitHub's maximum liability is limited to direct damages up to US $500 [S2].
- GitHub has no obligation to defend, indemnify, or hold you harmless for third-party claims arising from your use of Previews [S2].

**Confidentiality obligations**
- Non-public information about a private Preview is considered GitHub's confidential information, regardless of whether it is marked as such [S2][S4].
- You may use it only for the express purpose of testing and evaluating the Beta Preview, and must not disclose it to third parties (subject to stated exceptions) [S4]. Similar confidentiality obligations apply under the Research Program terms [S1].
- If you provide comments or suggestions about a Preview, GitHub may use that feedback for any purpose without obligation of any kind [S2].

**Not specified in the provided evidence**
- The published policies do not specify any timeline, notice period, or commitment regarding when a preview will become generally available, nor any service-level commitments (such as uptime or support response times) for previews.
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Research Program Terms — B. Confidentiality — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-research-program-terms.md
- [S2] GitHub Terms for Additional Products and Features — Previews — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-terms-for-additional-products-and-features.md
- [S4] GitHub Terms of Service — K. Beta Previews > 2. Confidentiality — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-terms-of-service.md
- [S5] GitHub Pre-release License Terms — 1. Pre-Release Software. — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-pre-release-license-terms.md

### JC-040 · VAL-001-030-F02

**Required aspect:** Pre-release software may fail or delete or corrupt data.

**Supporting source excerpt(s):**

- github-terms/github-pre-release-license-terms.md · 1. Pre-Release Software.

````text
Pre-release software may not operate correctly. It may delete your data, corrupt your data, or have other bugs. It also may not work the way a final commercial version of the software will.
````

**JC-040 verdict:** COVERED
**JC-040 brief_reason:**

### JC-041 · VAL-001-030-F03

**Required aspect:** GitHub may change or discontinue a pre-release product without notice.

**Supporting source excerpt(s):**

- github-terms/github-pre-release-license-terms.md · 1. Pre-Release Software.

````text
GitHub may change or discontinue pre-release software at any time, for any reason, without notice to you. GitHub may change the software for the final commercial version, or may not release a commercial version at all. GitHub is not obligated to provide to you any maintenance, technical support, or updates for the software.
````

**JC-041 verdict:** COVERED
**JC-041 brief_reason:**

### JC-042 · VAL-001-030-F04

**Required aspect:** GitHub is not obligated to provide maintenance, support, or updates for the pre-release product.

**Supporting source excerpt(s):**

- github-terms/github-pre-release-license-terms.md · 1. Pre-Release Software.

````text
GitHub may change or discontinue pre-release software at any time, for any reason, without notice to you. GitHub may change the software for the final commercial version, or may not release a commercial version at all. GitHub is not obligated to provide to you any maintenance, technical support, or updates for the software.
````

**JC-042 verdict:** COVERED
**JC-042 brief_reason:**

## VAL-001-032

**User query:**

Can I use GitHub Actions as a general compute or delivery service, and what might GitHub do if my workflows misuse it?

**Candidate answer:**

````text
You may not use GitHub Actions as a general compute or delivery service. The Terms state that Actions should not be used for any activity that places a disproportionate burden on GitHub's servers relative to user benefits—explicitly giving the example "don't use Actions as a content delivery network or as part of a serverless application" [S1]. Actions also may not be used for cryptomining, unauthorized access, offering Actions (or its elements) as a stand-alone or integrated commercial product/service, or—when using GitHub-hosted runners—any activity unrelated to producing, testing, deploying, or publishing the software project associated with the repository [S1]. Use is further limited to developing and testing your application(s) [S1].

If you misuse Actions, GitHub may monitor your use to prevent violations and abuse, and misuse may result in termination of jobs, restrictions on your ability to use Actions, disabling of repositories created to run Actions in violation of these Terms, or in some cases suspension or termination of your GitHub account [S1].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Terms for Additional Products and Features — Actions — https://github.com/github/site-policy/blob/main/Policies/github-terms/github-terms-for-additional-products-and-features.md

### JC-043 · VAL-001-032-F02

**Required aspect:** Actions cannot be used for cryptomining.

**Supporting source excerpt(s):**

- github-terms/github-terms-for-additional-products-and-features.md · Actions

````text
* Cryptomining;
````

Context excerpt:

````text
Actions and any elements of the Actions product or service may not be used in violation of the Agreement, the [GitHub Acceptable Use Policies](/site-policy/acceptable-use-policies/github-acceptable-use-policies), or the GitHub Actions service limitations set forth in the [Actions documentation](/actions/learn-github-actions/usage-limits-billing-and-administration). Additionally, regardless of whether an Action is using self-hosted runners, Actions should not be used for:
````

**JC-043 verdict:** COVERED
**JC-043 brief_reason:**

### JC-044 · VAL-001-032-F03

**Required aspect:** Actions cannot be offered as a standalone or integrated commercial Actions service.

**Supporting source excerpt(s):**

- github-terms/github-terms-for-additional-products-and-features.md · Actions

````text
* The provision of a stand-alone or integrated application or service offering the Actions product or service, or any elements of the Actions product or service, for commercial purposes;
````

Context excerpt:

````text
Actions and any elements of the Actions product or service may not be used in violation of the Agreement, the [GitHub Acceptable Use Policies](/site-policy/acceptable-use-policies/github-acceptable-use-policies), or the GitHub Actions service limitations set forth in the [Actions documentation](/actions/learn-github-actions/usage-limits-billing-and-administration). Additionally, regardless of whether an Action is using self-hosted runners, Actions should not be used for:
````

**JC-044 verdict:** COVERED
**JC-044 brief_reason:**

### JC-045 · VAL-001-032-F04

**Required aspect:** Disproportionate server burden, such as using Actions as a CDN or serverless app, is prohibited.

**Supporting source excerpt(s):**

- github-terms/github-terms-for-additional-products-and-features.md · Actions

````text
* Any activity that places a burden on our servers, where that burden is disproportionate to the benefits provided to users (for example, don't use Actions as a content delivery network or as part of a serverless application, but a low benefit Action could be ok if it’s also low burden); or
````

Context excerpt:

````text
Actions and any elements of the Actions product or service may not be used in violation of the Agreement, the [GitHub Acceptable Use Policies](/site-policy/acceptable-use-policies/github-acceptable-use-policies), or the GitHub Actions service limitations set forth in the [Actions documentation](/actions/learn-github-actions/usage-limits-billing-and-administration). Additionally, regardless of whether an Action is using self-hosted runners, Actions should not be used for:
````

**JC-045 verdict:** COVERED
**JC-045 brief_reason:**

### JC-046 · VAL-001-032-F05

**Required aspect:** Misuse can cause job termination, use restrictions, repository disabling, or account suspension.

**Supporting source excerpt(s):**

- github-terms/github-terms-for-additional-products-and-features.md · Actions

````text
In order to prevent violations of these limitations and abuse of GitHub Actions, GitHub may monitor your use of GitHub Actions. Misuse of GitHub Actions may result in termination of jobs, restrictions in your ability to use GitHub Actions, disabling of repositories created to run Actions in a way that violates these Terms, or in some cases, suspension or termination of your GitHub account.
````

**JC-046 verdict:** COVERED
**JC-046 brief_reason:**

## VAL-001-045

**User query:**

For a legal request, what kinds of GitHub account information are public by default, optional for users to reveal, or maintained privately?

**Candidate answer:**

````text
Based on the provided policy evidence:

**Public by default (all public profiles display):**
- Username
- Repositories the user has starred
- Other GitHub users the user follows
- Users who follow them [S1]

**Optional for users to share publicly:**
- Real name
- Avatar
- Affiliated company
- Location
- Public email address
- Personal web page
- Organizations the user is a member of (depending on the organizations' or users' preferences) [S1]

**Maintained privately (private account data):**
- Private email addresses
- Payment details
- Security access logs
- Data about interactions with private repositories [S1]

Note that the private account data list is described as something that "may include" those items, and the public/optional lists are described as non-exhaustive [S1]. The evidence also notes that some information is optional for users to provide, and in other cases GitHub may not have collected or retained it [S2].
````

**Citation map (only citations used in the answer):**

- [S1] Guidelines for Legal Requests of User Data — User data on GitHub.com — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- [S2] Guidelines for Legal Requests of User Data — Disclosure of non-public information — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md

### JC-047 · VAL-001-045-F01

**Required aspect:** Public user profiles display a username.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* Username
````

Context excerpt:

````text
* <a name="public-account-data"></a> **Public account data:** There is a variety of information publicly available on GitHub about users and their repositories. User profiles can be found at a URL such as `https://github.com/username`. User profiles display information about when the user created their account as well their public activity on GitHub.com and social interactions. Public user profiles can also include additional information that a user may have chosen to share publicly. All user public profiles display:
````

**JC-047 verdict:** COVERED
**JC-047 brief_reason:**

### JC-048 · VAL-001-045-F02

**Required aspect:** Public user profiles display starred repositories.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* The repositories that the user has starred
````

Context excerpt:

````text
* <a name="public-account-data"></a> **Public account data:** There is a variety of information publicly available on GitHub about users and their repositories. User profiles can be found at a URL such as `https://github.com/username`. User profiles display information about when the user created their account as well their public activity on GitHub.com and social interactions. Public user profiles can also include additional information that a user may have chosen to share publicly. All user public profiles display:
````

**JC-048 verdict:** COVERED
**JC-048 brief_reason:**

### JC-049 · VAL-001-045-F03

**Required aspect:** Users may optionally publish their real name.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* Their real name
````

Context excerpt:

````text
Optionally, a user may also choose to share the following information publicly:
````

**JC-049 verdict:** COVERED
**JC-049 brief_reason:**

### JC-050 · VAL-001-045-F04

**Required aspect:** GitHub may maintain private email addresses as private account data.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* Private email addresses
````

Context excerpt:

````text
* <a name="private-account-data"></a> **Private account data:** GitHub also collects and maintains certain private information about users as outlined in our [Privacy Policy](/site-policy/privacy-policies/github-privacy-statement). This may include:
````

**JC-050 verdict:** COVERED
**JC-050 brief_reason:**

### JC-051 · VAL-001-045-F05

**Required aspect:** GitHub may maintain payment details as private account data.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* Payment details
````

Context excerpt:

````text
* <a name="private-account-data"></a> **Private account data:** GitHub also collects and maintains certain private information about users as outlined in our [Privacy Policy](/site-policy/privacy-policies/github-privacy-statement). This may include:
````

**JC-051 verdict:** COVERED
**JC-051 brief_reason:**

### JC-052 · VAL-001-045-F06

**Required aspect:** GitHub may maintain security access logs as private account data.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · User data on GitHub.com

````text
* Security access logs
````

Context excerpt:

````text
* <a name="private-account-data"></a> **Private account data:** GitHub also collects and maintains certain private information about users as outlined in our [Privacy Policy](/site-policy/privacy-policies/github-privacy-statement). This may include:
````

**JC-052 verdict:** COVERED
**JC-052 brief_reason:**

## VAL-001-046

**User query:**

If investigators seek my GitHub account data, will GitHub tell me first, and in what situations might that notice be withheld or delayed?

**Candidate answer:**

````text
Based on the provided evidence, GitHub's stated policy is to notify affected users about requests for their account information, unless it is prohibited from doing so by law or court order [S2]. The published guidelines do not enumerate specific situations in which notice might be withheld or delayed beyond that general "prohibited by law or court order" exception [S2].

The evidence also notes that in certain exigent circumstances GitHub may share limited information corresponding to the nature of the circumstances, and would require legal process for anything beyond that [S4]. However, the provided sources do not specify whether or how such exigent circumstances affect user notification timing.
````

**Citation map (only citations used in the answer):**

- [S2] Guidelines for Legal Requests of User Data —  — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md
- [S4] Guidelines for Legal Requests of User Data — Disclosure of non-public information — https://github.com/github/site-policy/blob/main/Policies/other-site-policies/guidelines-for-legal-requests-of-user-data.md

### JC-053 · VAL-001-046-F01

**Required aspect:** GitHub generally notifies users about pending account or repository requests.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · We will notify any affected account owners

````text
It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.
````

**JC-053 verdict:** MISSING
**JC-053 brief_reason:** Answer narrows the notification statement to account-information requests and does not clearly cover repository requests.

### JC-054 · VAL-001-046-F02

**Required aspect:** Notice may be omitted when law or a court order prohibits it.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · We will notify any affected account owners

````text
It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.
````

**JC-054 verdict:** COVERED
**JC-054 brief_reason:**

### JC-055 · VAL-001-046-F03

**Required aspect:** Before disclosure, GitHub makes a reasonable effort to email affected owners a copy of the legal process so they can challenge it.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · We will notify any affected account owners

````text
It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.
````

**JC-055 verdict:** MISSING
**JC-055 brief_reason:** Only states that users are notified; omits the pre-disclosure verified-email notice, copy of legal process, and opportunity to challenge it.

### JC-056 · VAL-001-046-F04

**Required aspect:** In rare urgent circumstances, GitHub may delay notice to prevent death or serious harm or because of an ongoing investigation.

**Supporting source excerpt(s):**

- other-site-policies/guidelines-for-legal-requests-of-user-data.md · We will notify any affected account owners

````text
It is our policy to notify users about any pending requests regarding their accounts or repositories, unless we are prohibited by law or court order from doing so. Before disclosing user information, we will make a reasonable effort to notify any affected account owner(s) by sending a message to their verified email address providing them with a copy of the subpoena, court order, or warrant so that they can have an opportunity to challenge the legal process if they wish. In (rare) exigent circumstances, we may delay notification if we determine delay is necessary to prevent death or serious harm or due to an ongoing investigation.
````

**JC-056 verdict:** MISSING
**JC-056 brief_reason:** Answer says specific delay circumstances are not provided, but the source explicitly lists preventing death/serious harm and an ongoing investigation.

## VAL-001-049

**User query:**

A GitHub employee wants to offer a customer a sports ticket or dinner. How does the gifts policy separate acceptable hospitality from improper influence?

**Candidate answer:**

````text
The policy separates acceptable hospitality from improper influence primarily by **intent** and by **what is given**, not just by dollar value.

**Intent is the key dividing line.** The policy states that "if the intention is to improperly influence, anything, however small, might be considered 'of value'" [S1]. The Code of Ethics prohibits giving "anything else of value" to anyone "in order to obtain or keep business, or secure any other improper advantage for GitHub or Microsoft" [S2][S3]. GitHub's business relationships must not be used "to create a special advantage or influence a deal" [S5].

**Examples of acceptable hospitality for customers/prospective customers** include swag, economy class airfare to GitHub offices for Executive Briefings, bleacher-type tickets to a sporting event, a reasonably priced dinner in town, and a small box of chocolates as an end-of-year thank you [S1].

**Examples of unacceptable gifts** include first class airfare, winery tours, tickets to Disneyland/the World Cup/the Olympics, an autographed futbol, and charity contributions [S1].

**Applying this to the employee's question:** A reasonably priced dinner in town is listed as acceptable, and bleacher-type tickets to a sporting event are acceptable [S1]. However, premium event tickets (e.g., World Cup, Olympics) are listed as not ok [S1]. So a sports ticket or dinner could fall on either side depending on its nature and, critically, the intent behind offering it [S1].

**Special rule for government officials:** No gifts are acceptable for government officials (perhaps stickers), and employees should ask what their policies permit; many U.S. congresspeople will not allow you to take them out for dinner and pay [S1].

**Note on thresholds:** The Anti-Bribery Statement references that the Gifts and Entertainment Policy "includes clear monetary thresholds for gifts along with annual limitations, with limited exceptions for gifts approved by appropriate management" [S3], but the specific threshold amounts are not provided in the supplied evidence. When in doubt, the policy advises running it by Legal [S1].
````

**Citation map (only citations used in the answer):**

- [S1] GitHub Gifts and Entertainment Policy — Examples of acceptable and unacceptable gifts — https://github.com/github/site-policy/blob/main/Policies/github-company-policies/github-gifts-and-entertainment-policy.md
- [S2] GitHub Gifts and Entertainment Policy — Company policies — https://github.com/github/site-policy/blob/main/Policies/github-company-policies/github-gifts-and-entertainment-policy.md
- [S3] GitHub Anti-Bribery Statement — GitHub policies prohibiting bribery — https://github.com/github/site-policy/blob/main/Policies/github-company-policies/github-anti-bribery-statement.md
- [S5] GitHub Gifts and Entertainment Policy —  — https://github.com/github/site-policy/blob/main/Policies/github-company-policies/github-gifts-and-entertainment-policy.md

### JC-057 · VAL-001-049-F02

**Required aspect:** Even a small benefit can be improper when intended to influence someone.

**Supporting source excerpt(s):**

- github-company-policies/github-gifts-and-entertainment-policy.md · Examples of acceptable and unacceptable gifts

````text
As for other customers or prospective customers, certain things might seem trivial but have great value to someone else. For example, although it might not seem like a big deal to you to get your friend’s daughter hired as an intern, it might be of huge value to them. But if she is not qualified and you pull strings to make it happen, then it isn't ok. In addition, if the intention is to improperly influence, anything, however small, might be considered "of value."
````

**JC-057 verdict:** COVERED
**JC-057 brief_reason:**

### JC-058 · VAL-001-049-F03

**Required aspect:** Tickets to major events are examples of unacceptable customer gifts.

**Supporting source excerpt(s):**

- github-company-policies/github-gifts-and-entertainment-policy.md · Examples of acceptable and unacceptable gifts

````text
* Tickets to Disneyland 👸, the World Cup 🥅, the Olympics 🏅
````

Context excerpt:

````text
🙅 _Here are some other things that aren't ok:_
````

**JC-058 verdict:** COVERED
**JC-058 brief_reason:**

### JC-059 · VAL-001-049-F04

**Required aspect:** Low-cost bleacher-type sports tickets are examples of acceptable customer hospitality.

**Supporting source excerpt(s):**

- github-company-policies/github-gifts-and-entertainment-policy.md · Examples of acceptable and unacceptable gifts

````text
* Bleacher-type tickets to a sporting event ⚾️
````

Context excerpt:

````text
🙆 _Here is some stuff that is actually ok for customers or prospective customers:_
````

**JC-059 verdict:** COVERED
**JC-059 brief_reason:**

### JC-060 · VAL-001-049-F05

**Required aspect:** A reasonably priced dinner is an example of acceptable customer hospitality.

**Supporting source excerpt(s):**

- github-company-policies/github-gifts-and-entertainment-policy.md · Examples of acceptable and unacceptable gifts

````text
* A reasonably priced dinner in town 🍽
````

Context excerpt:

````text
🙆 _Here is some stuff that is actually ok for customers or prospective customers:_
````

**JC-060 verdict:** COVERED
**JC-060 brief_reason:**
