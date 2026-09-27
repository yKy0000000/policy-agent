# Oracle Repair V1 - Blind Human Review Sheet

Score each output with the preregistered checklist. The condition and model labels are hidden; do not infer them from the output style. For each item, first verify the claimed proposition against the frozen evidence and the baseline answer: a correct response refuses when the proposition is already present or unsupported by the evidence.

Checklist per output:
1. assessment correct for the verified finding?
2. confirmed proposition now semantically present/correct (repair cases)?
3. any existing correct fact lost or altered?
4. any unsupported or contradicted claim introduced?
5. repaired claim appropriately cited; prior valid citations preserved?
6. minimal edit (no global rewrite, no verbosity inflation)?
7. note

## Case evidence appendix

### VAL-001-039 (baseline for VAL-001-039-F02)

- question: An application includes open-source components. Where are its licenses documented, and when could an open-source license override GitHub's Application Terms?
- baseline answer: The open-source license for the Software is included in the "Open Source Notices" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].

An open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1].
- anchor span [S1]: To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact
- frozen evidence:

[S1] GitHub Open Source Applications Terms and Conditions :: Open Source Licenses and Notices
## Open Source Licenses and Notices

The open source license for the Software is included in the "Open Source Notices" documentation that is included with the Software. That documentation also includes copies of all applicable open source licenses.

To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact

Unless otherwise agreed to in writing with GitHub, your agreement with GitHub will always include, at a minimum, these Application Terms. Open source software licenses for the Software's source code constitute separate written agreements. To the limited extent that the open source software licenses expressly supersede these Application Terms, the open source licenses govern your agreement with GitHub for the use of the Software or specific included components of the Software.

[S2] GitHub Open Source Applications Terms and Conditions :: Miscellanea
## Miscellanea

1. No Waiver. The failure of GitHub to exercise or enforce any right or provision of these Application Terms shall not constitute a waiver of such right or provision.

1. Entire Agreement. These Application Terms, together with any applicable Privacy Notices, constitutes the entire agreement between you and GitHub and governs your use of the Software, superseding any prior agreements between you and GitHub (including, but not limited to, any prior versions of the Application Terms).

1. Governing Law. You agree that these Application Terms and your use of the Software are governed under California law and any dispute related to the Software must be brought in a tribunal of competent jurisdiction located in or near San Francisco, California.

1. Third-Party Packages. The Software supports third-party "Packages" which may modify, add, remove, or alter the functionality of the Software. These Packages are not covered by these Application Terms and may include their own license which governs your use of that particular package.

1. No Modifications; Complete Agreement. These Application Terms may only be modified by a written amendment signed by an authorized representative of GitHub, or by the posting by GitHub of a revised version. These Application Terms, together with any applicable Open Source Licenses and Notices and GitHub's Privacy Statement, represent the complete and exclusive statement of the agreement between you and us. These Application Terms supersede any proposal or prior agreement oral or written, and any other communications between you and GitHub relating to the subject matter of these terms.

1. License to GitHub Policies. These Application Terms are licensed under this [Creative Commons Zero license](https://creativecommons.org/publicdomain/zero/1.0/). For details, see our [site-policy repository](https://github.com/github/site-policy#license).

1. Contact Us. Questions about the Terms of Service? Contact us through the [GitHub Support portal](https://support.github.com/).

[S3] GitHub Open Source Applications Terms and Conditions :: Document introduction
These GitHub Open Source Applications Terms and Conditions ("Application Terms") are a legal agreement between you (either as an individual or on behalf of an entity) and GitHub, Inc. regarding your use of GitHub's applications, such as GitHub Desktop™ and associated documentation ("Software"). These Application Terms apply to the executable code version of the Software. Source code for the Software is available separately and free of charge under open source software license agreements. If you do not agree to all of the terms in these Application Terms, do not download, install, use, or copy the Software.

[S4] GitHub Open Source Applications Terms and Conditions :: Connecting to GitHub
## Connecting to GitHub

If you configure the Software to work with one or more accounts on the GitHub.com website or with a deployment of GitHub Enterprise Server, your use of the Software will also be governed by your applicable GitHub.com website Terms of Service and/or the license agreement applicable to your deployment of GitHub Enterprise Server ("GitHub Terms").

Any use of the Software that violates your applicable GitHub Terms will also be a violation of these Application Terms.

[S5] GitHub Terms of Service :: D. User-Generated Content > 6. Contributions Under Repository License
### 6. Contributions Under Repository License

Whenever you add Content to a repository containing notice of a license, you license that Content under the same terms, and you agree that you have the right to license that Content under those terms. If you have a separate agreement to license that Content under different terms, such as a contributor license agreement, that agreement will supersede.

Isn't this just how it works already? Yep. This is widely accepted as the norm in the open-source community; it's commonly referred to by the shorthand "inbound=outbound". We're just making it explicit.

### VAL-001-050 (baseline for VAL-001-050-F01)

- question: If a project violates GPLv2 and then fixes the issue, when does GitHub's GPL cooperation commitment provide provisional or permanent reinstatement?
- baseline answer: The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:

- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].
- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].

It also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].

The commitment applies to GPLv2 as a Covered License [S1].
- anchor span [S1]: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend to the person or entity (“you”) accused of violating the Covered License the following provisions regarding cure and reinstatement, taken from GPL version 3. As used here, the term ‘this License’ refers to the specific Covered License being enforced.
- frozen evidence:

[S1] GitHub GPL Cooperation Commitment :: Our Commitment
## Our Commitment

Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend to the person or entity (“you”) accused of violating the Covered License the following provisions regarding cure and reinstatement, taken from GPL version 3. As used here, the term ‘this License’ refers to the specific Covered License being enforced.

However, if you cease all violation of this License, then your license from a particular copyright holder is reinstated (a) provisionally, unless and until the copyright holder explicitly and finally terminates your license, and (b) permanently, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation.

Moreover, your license from a particular copyright holder is reinstated permanently if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of this License (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice.

GitHub intends this Commitment to be irrevocable, and binding and enforceable against GitHub and assignees of or successors to GitHub’s copyrights.

GitHub may modify this Commitment by publishing a new edition on this page or a successor location.

Definitions

‘Covered License’ means the GNU General Public License, version 2 (GPLv2), the GNU Lesser General Public License, version 2.1 (LGPLv2.1), or the GNU Library General Public License, version 2 (LGPLv2), all as published by the Free Software Foundation.

‘Defensive Action’ means a legal proceeding or claim that GitHub brings against you in response to a prior proceeding or claim initiated by you or your affiliate.

‘GitHub’ means GitHub, Inc. and its subsidiaries.

This work is available under a Creative Commons Attribution-ShareAlike 4.0 International license.

[S2] GitHub Copilot Extension Developer Policy :: 1. Services
## 1. Services

By using our Platform, you agree to adhere to this policy and all GitHub terms and policies incorporated by reference. You must also adhere to all technical specifications and requirements published by GitHub. GitHub may update this Agreement and any requirements at any time, and you should periodically review this Agreement and all technical specifications and requirements to ensure compliance with the most recent version. So long as you remain compliant with this Agreement and associated requirements within, we grant you a limited, worldwide, non-exclusive, non-transferable license during the term of the Agreement to access and use the Platform for the purpose of publishing, developing, demonstrating, testing and supporting interoperability and integrations between Your Extension and GitHub Copilot.

GitHub reserves the right at any time to modify or discontinue, temporarily or permanently, Your access to the Platform (or any part of it) with or without notice. It’s your sole responsibility to ensure that your use of the Platform is compatible with the then-current Platform. Other than the rights we expressly give you in this Agreement or the TOS, We don’t grant you any rights or licenses to GitHub Copilot, or to any other GitHub products or services.

Violations of this Agreement may result in removing the Extension from the Platform, token revocation, Account or Extension suspension, User notification, legal action or any other action deemed necessary by Us. If requested, You must provide us with proof of compliance with this Agreement. If You violate this Agreement we may or may not provide notice before taking action. Appeals may be submitted via the GitHub Appeal and Reinstatement Process. Please note that we may periodically audit Extensions and collect information about Users using Your Extension.

[S3] GitHub GPL Cooperation Commitment :: Document introduction
This commitment pertains to GitHub contributions to Git, the Linux kernel, and other programs under covered licenses (scroll to the end for definitions).

We based our statement on the [template](https://github.com/gplcc/gplcc/blob/master/Company/GPL%20Cooperation%20Commitment-Company-Template.md) for companies. See the [GPL Cooperation Commitment site](https://gplcc.github.io/gplcc/) for how other companies, individuals, and projects can adopt this commitment.

[S4] GitHub Community Code of Conduct :: Overview and Purpose
## Overview and Purpose

Millions of developers across the world host millions of projects—both open and closed source—on GitHub. We're fortunate to be able to play a part in enabling collaboration across the developer community every day, which is a responsibility we don’t take lightly. Together, we all have the exciting opportunity to make this a community we can be proud of.

GitHub Community, powered by GitHub Discussions, is intended to be a place for further collaboration, support, and brainstorming. This is a civilized place for connecting with other users, learning new skills, sharing feedback and ideas, and finding all the support you need for your GitHub projects. By participating in GitHub Community, you are agreeing to the same [Terms of Service](/site-policy/github-terms/github-terms-of-service) and [GitHub Acceptable Use Policies](/site-policy/acceptable-use-policies/github-acceptable-use-policies) that apply to GitHub.com, as well as this GitHub Community-specific Code of Conduct.

With this Code of Conduct, we hope to help you understand how best to collaborate in GitHub Community, what you can expect from moderators, and what type of actions or content may result in temporary or permanent suspension from community participation. We will investigate any abuse reports and may moderate public content within GitHub Community that we determine to be in violation of either the GitHub Terms of Service or this Code of Conduct.

Our diverse user base brings different perspectives, ideas, and experiences, and ranges from people who created their first "Hello World" project last week to the most well-known software developers in the world. We are committed to making GitHub an environment that welcomes all the different voices and perspectives our community has to offer, while maintaining a safe place for developers to do their best work.

[S5] GitHub Appeal and Reinstatement :: How this works > Reinstatements
### Reinstatements

Where a user can agree to abide by our Acceptable Use Policies moving forward and has made the changes necessary to address the violation(s), we may choose to reinstate their account or content depending on the circumstances and severity of the initial violation.

All legitimate Reinstatement requests will be reviewed initially by GitHub staff and will be answered with a decision.

## Outputs

## R01 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R02 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "repair_needed", "proposed_patch": "Add an introductory sentence stating that before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.", "revised_answer": "Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator [S1].\n\nThe GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R03 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R04 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R05 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R06 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R07 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R08 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R09 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R10 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R11 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R12 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "repair_needed", "proposed_patch": "Add a sentence after the first paragraph in the baseline answer: 'To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].'", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1]. To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R13 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "repair_needed", "proposed_patch": "Add the following sentence at the beginning of the answer: \"Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator [S1].\"", "revised_answer": "Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator [S1].\n\nThe GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R14 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R15 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R16 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "repair_needed", "proposed_patch": "Add an introductory sentence stating that before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.", "revised_answer": "Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator [S1].\n\nThe GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R17 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R18 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R19 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R20 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R21 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R22 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R23 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R24 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R25 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "repair_needed", "proposed_patch": "Add a sentence after the first paragraph: 'To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].'", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1]. To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R26 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R27 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R28 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "repair_needed", "proposed_patch": "Add a sentence after the first paragraph in the baseline answer: 'To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].'", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1]. To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R29 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R30 (VAL-001-050)

- review finding: Ceasing all violation provisionally reinstates the license unless and until the copyright holder explicitly and finally terminates it.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R31 (VAL-001-039)

- review finding: GitHub offers to provide source code where the licenses applicable to open-source components require such an offer; the offer may be exercised by contacting GitHub.
- output: {"assessment": "repair_needed", "proposed_patch": "Add to the first paragraph: \"To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].\"", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1]. To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R32 (VAL-001-039)

- review finding: GitHub's source-code offer expires one year after the Software release.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R33 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R34 (VAL-001-050)

- review finding: Before filing or continuing to prosecute any legal proceeding or claim (other than a Defensive Action) arising from termination of a Covered License, GitHub commits to extend the cure and reinstatement provisions to the accused violator.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R35 (VAL-001-050)

- review finding: GitHub must reimburse a violator's reasonable legal costs after the violation is cured.
- output: {"assessment": "not_supported", "proposed_patch": "", "revised_answer": "The GitHub GPL Cooperation Commitment states that if you cease all violation of the Covered License, your license from a particular copyright holder is reinstated:\n\n- **Provisionally**, unless and until the copyright holder explicitly and finally terminates your license [S1].\n- **Permanently**, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation [S1].\n\nIt also provides that your license is reinstated **permanently** if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of that license (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice [S1].\n\nThe commitment applies to GPLv2 as a Covered License [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## R36 (VAL-001-039)

- review finding: The Software's open-source license and applicable component licenses appear in the Open Source Notices documentation.
- output: {"assessment": "already_present", "proposed_patch": "", "revised_answer": "The open-source license for the Software is included in the \"Open Source Notices\" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].\n\nAn open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1]."}
- assessment_correct: 
- proposition_present: 
- regression: 
- unsupported_or_contradicted: 
- citation: 
- minimal_edit: 
- note: 

## Mapping status

This sheet is blinded; the condition/model mapping is stored in `eval/results/oracle_repair_v1_results.json` and must only be opened after scoring.
