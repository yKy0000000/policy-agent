# Query-Necessity Review — Blinded Packet

You are asked to make one independent judgment. Read the material below, then record your verdict in the
separate blank response form. Do not discuss this item with the other reviewer before both forms are
submitted.

This packet contains only:

- the user query;
- the baseline answer;
- the frozen evidence that the answer writer saw (sources S1..S5);
- one atomic proposition.

Do not consult any other project material, prior results, labels, or external sources.

## Item: VAL-001-039-F02

### User query

An application includes open-source components. Where are its licenses documented, and when could an open-source license override GitHub's Application Terms?

### Baseline answer

The open-source license for the Software is included in the "Open Source Notices" documentation that ships with the Software, which also includes copies of all applicable open-source licenses [S1].

An open-source license can override GitHub's Application Terms only to the limited extent that the open-source license expressly supersedes those Application Terms; in that case, the open-source license governs your agreement with GitHub for the use of the Software or its specific included components [S1]. Otherwise, your agreement with GitHub always includes, at a minimum, the Application Terms, and open-source licenses for the Software's source code constitute separate written agreements [S1].

### Frozen evidence (sources S1..S5)

[S1]
Title: GitHub Open Source Applications Terms and Conditions
Section: Open Source Licenses and Notices
Content:
## Open Source Licenses and Notices

The open source license for the Software is included in the "Open Source Notices" documentation that is included with the Software. That documentation also includes copies of all applicable open source licenses.

To the extent the terms of the licenses applicable to open source components require GitHub to make an offer to provide source code in connection with the Software, such offer is hereby made, and you may exercise it by contacting GitHub: https://github.com/contact

Unless otherwise agreed to in writing with GitHub, your agreement with GitHub will always include, at a minimum, these Application Terms. Open source software licenses for the Software's source code constitute separate written agreements. To the limited extent that the open source software licenses expressly supersede these Application Terms, the open source licenses govern your agreement with GitHub for the use of the Software or specific included components of the Software.

---

[S2]
Title: GitHub Open Source Applications Terms and Conditions
Section: Miscellanea
Content:
## Miscellanea

1. No Waiver. The failure of GitHub to exercise or enforce any right or provision of these Application Terms shall not constitute a waiver of such right or provision.

1. Entire Agreement. These Application Terms, together with any applicable Privacy Notices, constitutes the entire agreement between you and GitHub and governs your use of the Software, superseding any prior agreements between you and GitHub (including, but not limited to, any prior versions of the Application Terms).

1. Governing Law. You agree that these Application Terms and your use of the Software are governed under California law and any dispute related to the Software must be brought in a tribunal of competent jurisdiction located in or near San Francisco, California.

1. Third-Party Packages. The Software supports third-party "Packages" which may modify, add, remove, or alter the functionality of the Software. These Packages are not covered by these Application Terms and may include their own license which governs your use of that particular package.

1. No Modifications; Complete Agreement. These Application Terms may only be modified by a written amendment signed by an authorized representative of GitHub, or by the posting by GitHub of a revised version. These Application Terms, together with any applicable Open Source Licenses and Notices and GitHub's Privacy Statement, represent the complete and exclusive statement of the agreement between you and us. These Application Terms supersede any proposal or prior agreement oral or written, and any other communications between you and GitHub relating to the subject matter of these terms.

1. License to GitHub Policies. These Application Terms are licensed under this [Creative Commons Zero license](https://creativecommons.org/publicdomain/zero/1.0/). For details, see our [site-policy repository](https://github.com/github/site-policy#license).

1. Contact Us. Questions about the Terms of Service? Contact us through the [GitHub Support portal](https://support.github.com/).

---

[S3]
Title: GitHub Open Source Applications Terms and Conditions
Section: Document introduction
Content:
These GitHub Open Source Applications Terms and Conditions ("Application Terms") are a legal agreement between you (either as an individual or on behalf of an entity) and GitHub, Inc. regarding your use of GitHub's applications, such as GitHub Desktop™ and associated documentation ("Software"). These Application Terms apply to the executable code version of the Software. Source code for the Software is available separately and free of charge under open source software license agreements. If you do not agree to all of the terms in these Application Terms, do not download, install, use, or copy the Software.

---

[S4]
Title: GitHub Open Source Applications Terms and Conditions
Section: Connecting to GitHub
Content:
## Connecting to GitHub

If you configure the Software to work with one or more accounts on the GitHub.com website or with a deployment of GitHub Enterprise Server, your use of the Software will also be governed by your applicable GitHub.com website Terms of Service and/or the license agreement applicable to your deployment of GitHub Enterprise Server ("GitHub Terms").

Any use of the Software that violates your applicable GitHub Terms will also be a violation of these Application Terms.

---

[S5]
Title: GitHub Terms of Service
Section: D. User-Generated Content > 6. Contributions Under Repository License
Content:
### 6. Contributions Under Repository License

Whenever you add Content to a repository containing notice of a license, you license that Content under the same terms, and you agree that you have the right to license that Content under those terms. If you have a separate agreement to license that Content under different terms, such as a contributor license agreement, that agreement will supersede.

Isn't this just how it works already? Yep. This is widely accepted as the norm in the open-source community; it's commonly referred to by the shorthand "inbound=outbound". We're just making it explicit.

### Atomic proposition

GitHub offers source code where component licenses require such an offer.

### Question to answer (record in the response form)

> If the current baseline answer lacks this proposition, would the answer to the current query be
> substantively incomplete?

Allowed verdicts: `QUERY_REQUIRED` / `RELEVANT_BUT_OPTIONAL` / `AMBIGUOUS`.
