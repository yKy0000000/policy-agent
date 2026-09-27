# Router Benchmark v1 — Independent Deep Audit

- **Auditor role:** independent auditor (DeepSeek), separate from benchmark author (Sol).
- **Inputs read (unmodified):** `eval/router_benchmark_v1_draft.json`, `eval/router_benchmark_v1_draft.md`.
- **Corpus audited:** local `github/site-policy` at `data/site-policy/Policies`, **57 markdown documents**, commit `b9578b546d2506febda1da2cd7431644d58e512c` (verified with `git rev-parse HEAD`).
- **Method:** every query was checked against the **actual policy text**, not against the author metadata. Author fields (`benchmark_property`, `information_needs`, `likely_evidence_structure`, `why_it_is_useful`, `evaluation_notes`) are treated as **design hypotheses only**.
- **No routing gold:** this audit does **not** assign DIRECT / DECOMPOSE, does not predict a winning route or pipeline, and does not begin Router architecture. Statements such as "decomposition opportunity" describe dataset structure, not a decision.

### Scope limits stated up front

1. The production Router can read **only `query`**. All metadata used here is for offline dataset analysis.
2. "Evidence structure" below is inferred from **document/section layout**, not from a measured top-K retrieval run. Where a claim depends on chunking, it is flagged as such.
3. One corpus-level fact drives much of the audit: the set contains several **very large single documents** (`github-terms-of-service.md` 48.5 KB, `github-corporate-terms-of-service.md` 44.8 KB, `github-general-privacy-statement.md` 41.9 KB, `github-sponsors-additional-terms.md` 36.1 KB, `dmca-takedown-policy.md` 20.5 KB, `guidelines-for-legal-requests-of-user-data.md` 17.5 KB, `github-and-trade-controls.md` 14.2 KB, `github-marketplace-terms-of-service.md` 13.4 KB). A single-document question is therefore **not** the same as a non-fragmented question.

---

## router_001

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural single incident (address taken from a public site, reposted with an incitement to contact). The privacy-rule question and the removal-process question are two legitimate aspects of one real event.

### claimed_properties_audit
- `multi_document`: genuine. Answer needs `github-doxxing-and-invasion-of-privacy.md` (context, publicly-available-elsewhere, intent to harass → cross-link to bullying) plus `github-private-information-removal-policy.md` (exceptional high-risk service, "privacy complaints" routed to the privacy contact form).
- `rule_exception`: genuine (public availability is not a blanket allowance; intent to harass changes the analysis).
- `fragmented_evidence`: genuine, across two documents.
- `representation_mismatch`: **weak / over-claimed.** The user's wording ("privacy violation", "private-information removal request") already matches policy vocabulary almost exactly.
- `multi_requirement`: genuine (two explicit sub-asks).

### decomposition_bias_risk
medium — a genuine multi-document, multi-need case, but the inflated `representation_mismatch` shows property padding.

### routing_value
Tests whether a router realizes that one colloquial "privacy" framing actually spans a **conduct rule** and a **separate high-risk removal process**.

### issues
`representation_mismatch` is not well supported. Not severe enough to force a metadata rewrite on its own.

### revised_query
—

### revised_metadata
—

---

## router_002

### disposition
RECLASSIFY

### corpus_support
supported

### naturalness
Natural. A single scenario ("host only the tool, no images") that is a realistic policy question.

### claimed_properties_audit
- `multi_document`: **not required.** `github-synthetic-media-and-ai-tools.md` alone answers the question: it forbids projects "designed for, encourage, promote, support, or suggest in any way" synthetic-media use for NCII, and it supplies the exact context factors (configuration, marketing, README/documentation, external links, maintainer support). `github-non-consensual-intimate-imagery.md` contributes only a definition that the synthetic-media policy already names and links.
- `representation_mismatch`: genuine ("only the tool" vs prohibited purpose).
- `multi_requirement`: genuine but only two clauses.
- Author's `why_it_is_useful` ("evidence distributed across synthetic media and imagery policies") overstates the split.

### decomposition_bias_risk
high **as labeled** (looks cross-topic and therefore decomposition-favoring) — but as a **control** it is valuable.

### routing_value
Excellent hard-looking localized control: cross-topic surface (synthetic media + NCII) that is answerable from **one** policy. Attaches representation mismatch to a localized case.

### issues
Mislabeled `multi_document` and `likely_evidence_structure: multi_document`; inflates the multi-document count.

### revised_query
—

### revised_metadata
- `benchmark_property`: `["direct_control", "rule_exception", "hard_looking_control", "representation_mismatch", "multi_requirement"]`
- `likely_evidence_structure`: `localized`
- `benchmark_role`: hard-looking localized control
- core evidence doc: `Policies/acceptable-use-policies/github-synthetic-media-and-ai-tools.md`

---

## router_003

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural. Empty PRs, ban evasion, and notification flooding are one coherent abuse episode.

### claimed_properties_audit
- `multi_document`: genuine. `github-disrupting-the-experience-of-other-users.md` covers empty/meaningless PRs, excessive notifications, and staff action beyond maintainers; `github-bullying-and-harassment.md` covers alt accounts to evade moderation.
- `rule_process`: genuine (maintainer moderation vs GitHub staff action).
- `fragmented_evidence`: genuine across two documents.
- `multi_requirement`: genuine.
- `representation_mismatch` not claimed (correct).

### decomposition_bias_risk
medium — genuine two-document, two-conduct case.

### routing_value
Tests whether a router separates "disruptive platform use" from "harassment/evasion" and recognizes the different acting parties.

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_004

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural. Museum/educational framing with an avatar being the social-context surface.

### claimed_properties_audit
- `direct_control` + `localized`: genuine. Core evidence in `github-sexually-obscene-content.md` (artistic/educational/historical/journalistic allowance; "amplified by its placement in profiles or other social contexts"; opt-in limiting).
- `rule_exception`: genuine.
- `hard_looking_control`: genuine (context + placement + possible visibility limitation, one policy).
- The literal word "avatar" does not appear; it is covered by "profiles or other social contexts". Acceptable.

### decomposition_bias_risk
low — a clean hard-looking localized control.

### routing_value
Hard-looking localized control against "many conditions → multiple evidence locations".

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_005

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (satire labelled in README, sources linked, concern about context-free circulation).

### claimed_properties_audit
- `direct_control` + `localized`: genuine. `github-misinformation-and-disinformation.md` covers public-health harm, parody/satire allowance, and disclaimers/citations/context.
- `rule_exception`: genuine.
- `hard_looking_control`: genuine (multiple conditions, single policy).

### decomposition_bias_risk
low.

### routing_value
Hard-looking localized control; also tests that a router is not misled by the words "medical claim" + "satire" into assuming two evidence sources.

### issues
Names the policy noun ("misinformation policy"), which is natural user language but slightly eases the localized recognition.

### revised_query
—

### revised_metadata
—

---

## router_006

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (defensive-research exploit reused by a live campaign).

### claimed_properties_audit
- `multi_document`: genuine. `github-active-malware-or-exploits.md` (dual-use, authentication-gating as the usual restriction, temporary, owner contact) + `github-appeal-and-reinstatement.md` (appeal path).
- `rule_exception`: genuine (dual-use vs direct support of attack).
- `rule_process`: genuine (notify/challenge).
- `fragmented_evidence`: genuine.
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium.

### routing_value
Tests combining a substantive content rule with a procedural remedy from a different document.

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_007

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural ("get my name back" framed as one goal).

### claimed_properties_audit
- `multi_document`: genuine. `github-username-policy.md` (no release/transfer/reclaim unless trademark complaint), `github-trademark-policy.md` (confusion, may release a username), and `github-impersonation.md` (context/parody).
- `rule_exception`: genuine (parody).
- `representation_mismatch`: genuine (one "handle" goal vs three distinct standards).
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium.

### routing_value
Tests that a single user goal maps to distinct policy standards.

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_008

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (mentions another product for compatibility; asks where the line is).

### claimed_properties_audit
- `direct_control` + `localized`: genuine. `github-trademark-policy.md` (confusion/misleading; same mark alone is not necessarily a violation).
- `rule_exception`: genuine.
- `hard_looking_control`: genuine (multiple surfaces: README, package description, profile).
- `broad_coherent_control`: genuine.

### decomposition_bias_risk
low.

### routing_value
Control against multi-surface → multi-document. **Weakest control by surface** (25 words, shortest in the set, and it names "trademark-policy" directly), so it does little to defeat length/clause heuristics.

### issues
Shortest query; names its own policy. Still valid, but under-strong as a hard control.

### revised_query
—

### revised_metadata
—

---

## router_009

### disposition
RECLASSIFY

### corpus_support
supported

### naturalness
Natural (security researcher worried about legal exposure and third-party scope).

### claimed_properties_audit
- `multi_document`: **not required.** `github-bug-bounty-program-legal-safe-harbor.md` alone covers all three needs: §1 safe-harbor coverage, §2 third-party limits, §3 limited waiver of other site policies. `coordinated-disclosure-of-security-vulnerabilities.md` is only a landing page that links to the bounty site and to the safe-harbor policy.
- `rule_exception`: genuine.
- `rule_process`: genuine.
- `fragmented_evidence`: genuine **within a single document** (§1/§2/§3) → multi-section, not multi-document.
- `multi_requirement`: genuine.

### decomposition_bias_risk
high **as labeled** (three concepts that look cross-document) — valuable as a control.

### routing_value
Strong control: multiple distinct legal concepts that nonetheless live in one document's sections. Attacks a "concept count → decompose" heuristic.

### issues
Mislabeled `multi_document`; `why_it_is_useful` claims it "requires merging general rules, a limited exemption, and third-party limits" across sources, but these are sections of one policy.

### revised_query
—

### revised_metadata
- `benchmark_property`: `["direct_control", "rule_exception", "rule_process", "fragmented_evidence", "hard_looking_control", "multi_requirement"]`
- `likely_evidence_structure`: `multi_section`
- `benchmark_role`: intra-document control (single document, several sections)
- core evidence doc: `Policies/security-policies/github-bug-bounty-program-legal-safe-harbor.md`

---

## router_010

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (a single notice covering one repo file and one package release).

### claimed_properties_audit
- `direct_control`: genuine **only under a single-source-document notion.** `dmca-takedown-policy.md` Step 3 (repo partial vs package: packages are immutable → disable entire package, reinstate after removal), Step 4 (user must notify GitHub of changes; GitHub verifies), and section D (one additional window).
- `multi_section`: genuine.
- `rule_exception` / `rule_process`: genuine.
- `fragmented_evidence`: genuine within the document.
- `hard_looking_control`: genuine (two carriers, two questions).
- `multi_requirement`: genuine.

### decomposition_bias_risk
low **as a doc-count control**, but see issue: the answer genuinely spans Step 3 + Step 4 + section D of a 20.5 KB document, so the item is itself an intra-document fragmentation case.

### routing_value
Control against "two carriers / two questions → decompose". Also silently tests intra-document section coverage.

### issues
`direct_control` here means "one source document", not "no decomposition opportunity". The label conflates source-document count with evidence structure. This caveat applies to 010, 014, 015, 016, 019.

### revised_query
—

### revised_metadata
—

---

## router_011

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (one repository leaking two different kinds of internal material; user asks whether one request fits).

### claimed_properties_audit
- `multi_document`: genuine. `github-private-information-removal-policy.md` (network diagrams may qualify only with a shown security risk; copyright is explicitly *not* appropriate; requests must be sent separately) + `dmca-takedown-policy.md`.
- `fragmented_evidence`: genuine.
- `representation_mismatch`: genuine ("our internal material" vs security-risk removal vs copyright channel).
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium.

### routing_value
Tests mapping one colloquial "internal material" description onto two removal channels with different requirements.

### issues
Structurally close to router_001 (private-info process eligibility + a second channel). Differentiated by the copyright channel and the security-risk-vs-copyright distinction; not a duplicate.

### revised_query
—

### revised_metadata
—

---

## router_012

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (user finds their project named in the public gov-takedowns repo).

### claimed_properties_audit
- `direct_control` + `localized`: genuine. `github-government-takedown-policy.md` ("What does it mean if we post a notice…" explicitly says it does **not** mean the content was unlawful or the user did wrong).
- `broad_coherent_control`: genuine (wide framing, one concept).

### decomposition_bias_risk
low. Best coherent control in the set.

### routing_value
Control for "broad framing → decompose": the whole question collapses to one informational concept.

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_013

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (a single government request that mixes a content demand with a data demand).

### claimed_properties_audit
- `multi_document`: genuine. `github-government-takedown-policy.md` (content declared unlawful locally; notification; geographic limiting) + `guidelines-for-legal-requests-of-user-data.md` (non-public data needs valid legal process; foreign requests go via DOJ/MLAT; GitHub not required to give foreign governments data).
- `fragmented_evidence`: genuine.
- `representation_mismatch`: genuine ("a government request" conflates two evidence chains).
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium. Note mild route leakage: "how are the **two** requests handled" enumerates the split.

### routing_value
Tests separating a content takedown from an account-data disclosure that a user lumps together.

### issues
The phrase "the two requests" telegraphs the answer structure.

### revised_query
—

### revised_metadata
—

---

## router_014

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (police exigency claim over a private repository).

### claimed_properties_audit
- `direct_control`: genuine under a single-document notion. `guidelines-for-legal-requests-of-user-data.md` covers exigent circumstances (limited disclosure; private repo contents still require a warrant), "only with a search warrant", and notification/delay.
- `multi_section`: genuine.
- `rule_exception` / `rule_process`: genuine.
- `fragmented_evidence`: genuine within the document.
- `hard_looking_control`: genuine (exigency + content type + notification timing).
- `multi_requirement`: genuine.

### decomposition_bias_risk
low as a doc-count control; same caveat as router_010 (large document, answer split across sections).

### routing_value
Control against "urgency + private data + notification → decompose".

### issues
Same document-count vs evidence-structure caveat as router_010.

### revised_query
—

### revised_metadata
—

---

## router_015

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (personal account, private repo, pasted snippet, opt-out question).

### claimed_properties_audit
- `direct_control`: genuine under a single-document notion. `github-terms-of-service.md` §J.3 (opt-out; individual licenses), the private-repository clause (line 189), §J.1 applicability.
- `multi_section`: genuine (widely separated within a 48.5 KB document).
- `rule_exception`: genuine.
- `fragmented_evidence`: genuine within the document.
- `representation_mismatch`: genuine ("private" covers storage vs submitted input).
- `multi_requirement`: genuine.
- Longest query in the set (39 words) while still a single-document case.

### decomposition_bias_risk
low as a doc-count control; the "private" ambiguity is a real surface cue but the answer stays in one agreement.

### routing_value
**Best control against a length heuristic**: longest query, multiple conditions, single operative document.

### issues
Same document-count vs evidence-structure caveat. Optionally could also carry `broad_coherent_control`.

### revised_query
—

### revised_metadata
—

---

## router_016

### disposition
RECLASSIFY

### corpus_support
supported

### naturalness
Natural (paid Marketplace app disabled mid-term; notification/payment/refund questions).

### claimed_properties_audit
- `direct_control`: genuine under a single-document notion. `github-marketplace-terms-of-service.md` §D (billing, no refunds, service active for the paid period), §E (privacy/data responsibility), §H (blocking for legal or policy reasons; GitHub works with the Product Provider to notify users).
- `multi_section`: genuine.
- `rule_exception` / `rule_process`: genuine.
- `fragmented_evidence`: genuine within the document.
- `multi_requirement`: genuine.
- `broad_coherent_control`: **missing but applicable** (notification + paid-term/access + refund are broad aspects of one agreement).

### decomposition_bias_risk
low.

### routing_value
Control against "three explicit sub-questions → decompose". Also an under-used broad-coherent control.

### issues
"Does payment guarantee continued access" is answered only by **combining** §D (service remains active for the paid period) with §H (GitHub may block for policy reasons) — a synthesis, not a single sentence. It is defensible but worth flagging.

### revised_query
—

### revised_metadata
- `benchmark_property`: add `broad_coherent_control` → `["direct_control", "rule_exception", "rule_process", "fragmented_evidence", "broad_coherent_control", "multi_requirement"]`
- `likely_evidence_structure`: `multi_section` (unchanged)
- `benchmark_role`: hard-looking intra-document control / broad-coherent control

---

## router_017

### disposition
KEEP

### corpus_support
supported

### naturalness
Acceptable but **borderline**. Two behaviours (displaying sponsor logos in your own README/Sponsor content; promoting sponsor products in other users' issue threads) are joined by "then". They share the subject of sponsor promotion, so it reads as one plan, but the second half is what pulls in the general advertising rule.

### claimed_properties_audit
- `multi_document`: genuine. `github-sponsors-additional-terms.md` (sponsor name/logo display, promotional focus limit) + `github-acceptable-use-policies.md` §10 ("You may not advertise in other Users' Accounts, such as by posting monetized or excessive bulk content in issues").
- `rule_exception`: genuine.
- `representation_mismatch`: mild but genuine ("thanking sponsors" vs advertising restrictions).
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium–high — the second clause looks appended to force cross-document retrieval.

### routing_value
Tests whether a router treats "thanking sponsors" and "promoting in others' threads" as one permission or two.

### issues
Weakest naturalness among the multi-document cases; the two halves serve the same broad goal, so it is not clearly artificial, but the stitching is visible. No edit applied (wording is still plausible user language).

### revised_query
—

### revised_metadata
—

---

## router_018

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (one event, two recording contexts, consent already refused).

### claimed_properties_audit
- `multi_document`: genuine. `github-event-terms.md` §2 (GitHub's own photo/video use and attendee-provided media) + `github-event-code-of-conduct.md` ("Photography or recording of Event Participants without their consent" is unacceptable; reporting channel).
- `rule_process`: genuine (reporting/urgent help).
- `fragmented_evidence`: genuine.
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium.

### routing_value
Tests separating organizer media authorization from attendee conduct rules.

### issues
none

### revised_query
—

### revised_metadata
—

---

## router_019

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural (account flagged while travelling through a restricted region).

### claimed_properties_audit
- `direct_control`: genuine under a single-document notion. `github-and-trade-controls.md` (travel impact and reinstatement; private-repo restriction; mistaken-flag appeal through Support).
- `multi_section`: genuine.
- `rule_exception` / `rule_process`: genuine.
- `fragmented_evidence`: genuine within the document.
- `hard_looking_control`: genuine (travel + account restriction + correction path).
- `multi_requirement`: genuine.

### decomposition_bias_risk
low as a doc-count control; same caveat as router_010.

### routing_value
Control against "travel + access loss + appeal → decompose".

### issues
Same document-count vs evidence-structure caveat.

### revised_query
—

### revised_metadata
—

---

## router_020

### disposition
KEEP

### corpus_support
supported

### naturalness
Natural enough for an enterprise admin reviewing vendors (subprocessor-list vendor + installed Marketplace app), though the two are somewhat independently motivated.

### claimed_properties_audit
- `multi_document`: genuine. `github-subprocessors.md` (list applies to subprocessors acting on GitHub's behalf for Enterprise customers under the DPA) + `github-general-privacy-statement.md` ("Other Third-party Applications … You are responsible for the data you instruct us to share") + `github-marketplace-terms-of-service.md` §C/§E (Product Provider responsibility; OAuth scope).
- `fragmented_evidence`: genuine.
- `representation_mismatch`: genuine ("vendor" covers two different relationships).
- `multi_requirement`: genuine.

### decomposition_bias_risk
medium. Does not name policy documents, so honest-framing leakage is low.

### routing_value
Tests distinguishing a GitHub subprocessor from a user-authorized Marketplace app and assigning responsibility.

### issues
The two halves are loosely coupled (a compliance review is a plausible but not airtight single event).

### revised_query
—

### revised_metadata
—

---

# Collection-Level Audit

## A. Benchmark Balance (independent recount)

Structural counts, **before** the recommended reclassifications (author's labels):

| property | author count | independent count | notes |
|---|---|---|---|
| multi_document | 11 | **9** (after removing 002, 009) | 002 and 009 answerable from one document |
| single-document (localized + multi_section) | 9 | **11** | includes large-document multi-section cases |
| localized | 4 | **5** after reclassify (002); 4 before | 004, 005, 008, 012 |
| multi_requirement | 16 | **20** | every query has ≥2 explicit sub-asks |
| fragmented_evidence | 13 | ≈13 | 009 becomes intra-document |
| representation_mismatch | 8 | 8, but 001 weak | property padding risk |
| rule_exception | 13 | 13 | consistent |
| rule_process | author md says 9 / JSON has 8 | **8** | minor doc discrepancy |
| hard-looking controls | 6 | **10** after reclassify (add 002, 009; plus 015, 016) | author under-counts |
| broad-coherent controls | 2 | 2 (008, 012); **3** if 016 added | under-populated |

Independent structural classification (after recommended reclassification):

- **likely localized:** 002, 004, 005, 008, 012 → 5
- **likely multi-section (single document):** 009, 010, 014, 015, 016, 019 → 6
- **likely multi-document:** 001, 003, 006, 007, 011, 013, 017, 018, 020 → 9

This is dataset structure, **not** a route label.

## B. Shallow-Heuristic Audit

Measured over the draft (word/symbol counts):

| heuristic | controls (avg) | multi-document (avg) | verdict |
|---|---|---|---|
| query length (words) | 32.8 | 34.6 | **no separation** — full overlap (015 control = 39 words; 011 multi-doc = 29) |
| question marks | 1.0 | 1.0 | uniform |
| clause/sub-ask count | ~2 | ~2 | uniform |
| `and` count | 1.22 | 1.55 | weak; controls 004/005/015/019 also contain `but`/`and` |
| requested outputs | 2 | 2 | uniform — no `multi_requirement` discrimination |
| technical vocabulary | — | — | no separation |

**One heuristic does separate the set (as originally labeled): policy-domain / topic count.** Multi-document cases name two or more concrete subject domains (privacy + removal; malware + appeal; username + trademark + impersonation; sponsors + advertising; event + code of conduct; government content + account data; subprocessor + Marketplace app), whereas the original controls each name one. A router that counts named domains could therefore match author expectation without any real reasoning.

Specific items where this shallow cue fires: 001, 003, 006, 007, 011, 013, 017, 018, 020.

**Mitigation already present but uncounted:** 002 (synthetic media + NCII → one doc), 009 (bug bounty + site policies + third party → one doc), and 016 (notification + payment + refund → one agreement) are multi-topic yet single-document. Promoting these to controls directly neutralizes the topic-count shortcut; this is the single highest-value balance fix available without new items.

## C. Decomposition-Favoring Bias

**Yes.** As originally labeled, a trivial "complex query → decompose" strategy would be *consistent with the author's stated expectations* on 16/20 cases (`multi_requirement`) and 13/20 (`fragmented_evidence`), while only 4 cases are cleanly localized. Evidence:

- `multi_requirement` is attached to 16/20, but in fact **all 20 queries contain two explicit sub-asks**, so the property is near-uniform and does not discriminate.
- Every query is a single sentence with exactly one "?" and a two-clause structure — so the set offers no structural variety that could penalize an always-split strategy.
- Only 6 items are marked `hard_looking_control` and only 2 `broad_coherent_control`.
- Several nominal controls (010, 014, 015, 016, 019) are themselves fragmented + multi-requirement; they are "controls" only because the sections happen to sit in one file.

After the recommended reclassification (5 localized, 6 multi-section, 9 multi-document) the picture improves: at least 5 localized items and 3 multi-topic/single-document items (002, 009, 016) now actively penalize both "topic count → decompose" and "always decompose". The residual risk is that the benchmark still cannot tell a good router from a complexity heuristic on the remaining 9 multi-document items, because they are all genuinely multi-need.

## D. Control Quality

- **Quantity:** adequate after reclassification: 5 localized + 6 intra-document controls = 11 single-document items vs 9 multi-document items.
- **Difficulty matching:** the intra-document controls 010, 014, 015, 016, 019 carry surface complexity equal to or greater than several multi-document items (34–39 words, multiple conditions, 2–3 sub-asks). They can break length and clause-count heuristics. **router_008 is the weakest** (25 words, names its own policy) and barely qualifies as "hard-looking".
- **Breaking shallow heuristics:** they defeat length/clause/output-count heuristics well. They do **not** defeat a semantic topic-count heuristic unless 002, 009, and 016 are treated as controls.
- **Reclassification is preferable to adding items:** promote 002 and 009 from multi-document to single-document hard-looking controls; add `broad_coherent_control` to 016. This raises controls from 9 to 11 and lowers multi-document from 11 to 9 **without touching any query**.

## E. Dataset Validity Risks (highest first)

1. **Document-count is conflated with evidence structure.** `direct_control` currently means "the answer is in one file", but the benchmark studies representation/evidence structure. Because several single files are very large, items 010, 014, 015, 016, 019 are labeled controls while their answers genuinely span multiple distant sections — i.e. plausible intra-document decomposition opportunities sitting inside the control bucket. This both overstates control purity and hides decomposition opportunity. *(severity: high)*
2. **Decomposition-favoring imbalance / weak negative controls.** Only 4–5 items have localized evidence; 16/20 are tagged multi-requirement and all 20 are structurally two-clause. A trivial complexity router can appear to agree with author expectation. There is also no item where decomposition would plausibly *hurt* (over-narrowing), so the set has no true anti-decomposition trap. *(severity: high)*
3. **Fake multi-document labels (002, 009).** Both are answerable from a single document; they inflate the multi-document count (11 vs 9) and overstate cross-document fragmentation coverage. *(severity: medium)*
4. **`multi_requirement` near-uniformity.** Tagged 16/20 but effectively 20/20; the property carries no discriminative information as defined. *(severity: medium)*
5. **Weak / padded `representation_mismatch`.** 001 is only marginally a mismatch; combined with the multi-topic/single-doc items this makes the "representation mismatch" bucket look larger than it is. *(severity: low–medium)*

## F. Final Count

```
KEEP:        17
EDIT:         0
RECLASSIFY:   3   (002, 009 → single-document hard-looking controls; 016 → add broad_coherent_control)
REMOVE:       0
usable total: 20
```

No new items were generated. `usable total == 20`, so no "缺 X 题" statement applies. Note: the set is usable, but its **discriminative power** depends on applying the reclassifications; without them the effective balance is weaker than it needs to be.

## G. Freeze Decision

1. **Not yet freeze-ready as-is.** The 20 queries are corpus-valid, natural, and free of route-gold leakage; the blocker is metadata/balance, not wording.
2. **Before freeze, resolve:**
   - Reclassify **002** and **009** from `multi_document` to single-document (`localized` / `multi_section`) hard-looking controls, and drop the `multi_document` property. — *metadata + balance*
   - Add `broad_coherent_control` to **016**. — *metadata*
   - Publish a corrected coverage audit: multi-document is **9**, not 11; controls are **11**, not 9; `multi_requirement` is effectively **20/20** and should be redefined or dropped as a discriminator. — *metadata + balance*
   - Add an explicit dataset-level definition: `direct_control` = "single source document", **not** "no decomposition opportunity", and list 010/014/015/016/019 as intra-document-fragmented. — *metadata*
3. **Categories:**
   - wording: none required.
   - metadata: reclassify 002/009/016, correct counts, fix `multi_requirement` definition.
   - balance: caused by the metadata corrections above; no new items strictly required for freeze. If later retrieval experiments show the topic-count heuristic still dominates, add targeted localized/intra-document controls then.
   - corpus validity: none — all 20 queries are supported by the frozen 57-document corpus at commit `b9578b5`.

No Router architecture discussion is started here.

---

## Verification checklist

- Original drafts not modified (see `router_benchmark_v1_audit_changes.json` hashes).
- All 20 cases audited; no 21st case created.
- No routing gold produced.
- No Router implementation touched.
