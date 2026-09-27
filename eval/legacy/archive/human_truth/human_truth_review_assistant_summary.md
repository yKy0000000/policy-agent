# Human Truth Review Assistant — Summary (v1)

**Status: assistant recommendations only — NOT human ground truth.** This package is input for Reviewer 1 / Reviewer 2; it must not be hashed or frozen as verdicts. Humans must still complete adjudication and set `status = frozen_human_verdicts`.

Source worksheet: `eval/results/human_truth_stage0_worksheet.json` (sha256 `86926d6290a60f5a9b9b1ad2ffa638a6206e028bfa0d97a8581f7aa632f3244b`, matches Stage 0 freeze).
Contract: `eval/human_truth_contract_v1.md` (sha256 `1b131832cbca8d3529473d65dbb3c48ea80957c88aead225f147ff6870aa6d74`, matches Stage 0 freeze).

## Dataset overview

- Cases: **66** (Validation V1: 50, Broad Query V3: 16); aspects: **331** (V1: 239, V3: 92).
- Routes (metadata only): cases BROAD 38 / SIMPLE 28; aspects BROAD 192 / SIMPLE 139.
- Assistant-suggested verdicts: **QUERY_REQUIRED 309**, RELEVANT_BUT_OPTIONAL 20, AMBIGUOUS 2.
- Confidence hints: HIGH 277, MEDIUM 52, LOW 2 (not gold; low count = items humans should look at first).
- Reviewer-attention flags: background_detail 8, broad_query_overexpansion 4, enumerated_list 6, example_detail 5, implied_requirement 25, related_fact_drift 15, rubric_contamination 2.
- SIMPLE sentinels (frozen, unchanged): VAL-001-002, VAL-001-004, VAL-001-010, VAL-001-013, VAL-001-015, VAL-001-027, VAL-001-030, VAL-001-032.
- Context: both frozen query sets are single-turn (no rewrite applied); there is no conversation context beyond the recorded query.

## SIMPLE sentinels

### VAL-001-002

- Query: I think code in another repository copies my work. What checks should I make before sending GitHub a DMCA takedown notice?
- Expected interpretation boundary: Pre-filing checks for a code-focused DMCA takedown (correct route, investigate, licenses, fair use, claim specificity) - not counter-notice mechanics or the full takedown process.
- Assistant distribution: R 5 / O 0 / A 0.

### VAL-001-004

- Query: Our registered mark is being used in a misleading GitHub account. What information should our report give GitHub so it can investigate and understand the remedy we want?
- Expected interpretation boundary: Itemized information a trademark report must give GitHub (account username, mark details, confusion, requested action, good-faith statement) - not investigation outcome or enforcement menu.
- Assistant distribution: R 6 / O 0 / A 0.

### VAL-001-010

- Query: I'm reporting copied code and an exposed secret across a fork network. If GitHub disables the parent under either removal process, what happens to its forks?
- Expected interpretation boundary: Fork treatment when the parent is disabled under either removal process (no automatic disablement; owner must identify forks; valid all-fork claim can cover the network).
- Assistant distribution: R 5 / O 1 / A 0.

### VAL-001-013

- Query: I want to automate promotion and engagement on GitHub. What behavior would count as spam or inauthentic activity?
- Expected interpretation boundary: Spam/inauthentic activity categories relevant to automated promotion (bulk activity, fake accounts, rank abuse, phishing, unsolicited advertising relay).
- Assistant distribution: R 5 / O 0 / A 0.

### VAL-001-015

- Query: A disagreement in my repository has escalated. What conduct counts as harassment, and is every unwelcome comment treated that way?
- Expected interpretation boundary: Conduct that counts as harassment plus the explicit boundary that disagreement/downvoting alone may not rise to harassment.
- Assistant distribution: R 4 / O 0 / A 0.

### VAL-001-027

- Query: Our school participates in GitHub's Education Partner Program. What are our responsibilities for qualified users and their continued access?
- Expected interpretation boundary: Education Partner responsibilities toward qualified users and continued access (no resale, no charging, liability, enforcement cooperation, ending non-qualified access).
- Assistant distribution: R 5 / O 1 / A 0.

### VAL-001-030

- Query: We're considering a GitHub preview for important work. What risks and service commitments should we expect before it becomes generally available?
- Expected interpretation boundary: Risks and service commitments of a pre-release product before GA (failure/data loss, change/discontinuation, no maintenance/support obligation) - not the GA-status restatement.
- Assistant distribution: R 3 / O 1 / A 0.

### VAL-001-032

- Query: Can I use GitHub Actions as a general compute or delivery service, and what might GitHub do if my workflows misuse it?
- Expected interpretation boundary: Actions limits relevant to general compute/delivery (disproportionate burden/CDN/serverless, cryptomining, commercial resale) and enforcement consequences.
- Assistant distribution: R 4 / O 1 / A 0.

## High-risk adjudications

### AMBIGUOUS (unresolved by query text; contract says never force QUERY_REQUIRED)

| aspect | suggested | confidence | reason | flags |
|---|---|---|---|---|
| `VAL-001-011-F01` | A | LOW | Torn between the policy's threat/incitement prong and the depiction prong the query targets. | related_fact_drift, rubric_contamination |
| `VAL-001-043-F01` | A | LOW | Incoming-request completeness criteria vs the post-completeness steps the query focuses on. | implied_requirement, related_fact_drift |

### LOW confidence

| aspect | suggested | confidence | reason | flags |
|---|---|---|---|---|
| `VAL-001-011-F01` | A | LOW | Torn between the policy's threat/incitement prong and the depiction prong the query targets. | related_fact_drift, rubric_contamination |
| `VAL-001-043-F01` | A | LOW | Incoming-request completeness criteria vs the post-completeness steps the query focuses on. | implied_requirement, related_fact_drift |

### Broad-query boundary items (BROAD-routed, not HIGH-confidence required)

| aspect | suggested | confidence | reason | flags |
|---|---|---|---|---|
| `VAL-001-005-F02` | R | MEDIUM | Contact details are required notice content, but not identification of the content in the narrow sense. | enumerated_list, implied_requirement |
| `VAL-001-005-F05` | R | MEDIUM | Signature is required notice content; whether it counts as 'identify' or a commitment is interpretive. | enumerated_list, implied_requirement |
| `VAL-001-006-F04` | R | MEDIUM | Contact information is a required complaint element, one item in an enumerated list. | enumerated_list |
| `VAL-001-006-F05` | R | MEDIUM | Good-faith statement is a required complaint element, one item in an enumerated list. | enumerated_list |
| `VAL-001-007-F01` | O | MEDIUM | Source explicitly labels contacting the user first as not required; a prep answer can omit it and stay complete. | implied_requirement |
| `VAL-001-007-F02` | R | MEDIUM | Recommended preparation practice (professionals, not bulk bots) that also explains a review delay. | implied_requirement |
| `VAL-001-007-F03` | R | MEDIUM | Explains a delay factor: unrelated removal requests cannot be processed simultaneously. | implied_requirement |
| `VAL-001-008-F03` | R | MEDIUM | Postal mail is the channel asked about; its slower handling frames the timing answer. | implied_requirement |
| `VAL-001-012-F02` | R | MEDIUM | Submission route is part of how a request is made. | implied_requirement |
| `VAL-001-018-F02` | R | MEDIUM | Illustrative example of covered health misinformation; the query names health claims but not examples. | example_detail |
| `VAL-001-022-F05` | O | MEDIUM | Generic restatement of legal limits; adds little beyond the specific limits already covered. | related_fact_drift, broad_query_overexpansion |
| `VAL-001-025-F01` | O | MEDIUM | Background about the Community platform; not a rule and not a moderation outcome. | background_detail, broad_query_overexpansion |
| `VAL-001-026-F02` | R | MEDIUM | A condition of the license grant; part of the permission terms but not itself the permission. | implied_requirement |
| `VAL-001-037-F01` | O | MEDIUM | Scope of the developer agreement; background rather than responsibility or listing rights. | background_detail |
| `VAL-001-039-F02` | O | MEDIUM | Source-code offer is related OSS compliance detail, not where licenses are documented. | related_fact_drift |
| `VAL-001-039-F03` | R | MEDIUM | Default that Application Terms remain in force frames when an OSS license can override. | implied_requirement |
| `VAL-001-042-F02` | R | MEDIUM | Sublicensing limit is part of the rights granted; not singled out by the query. | implied_requirement |
| `VAL-001-042-F04` | R | MEDIUM | No-recall consequence of open-source distribution; supports the distribution right. | implied_requirement |
| `VAL-001-043-F01` | A | LOW | Incoming-request completeness criteria vs the post-completeness steps the query focuses on. | implied_requirement, related_fact_drift |
| `VAL-001-044-F01` | O | MEDIUM | Definitional context on what self-hosted GHES means; the query already assumes self-hosting. | background_detail |
| `VAL-001-044-F04` | O | MEDIUM | ECCN classification detail; informs but is not itself an export limit. | related_fact_drift |
| `VAL-001-047-F03` | O | MEDIUM | Organization-specific subpoena scope detail; not needed for the subpoena-vs-access-logs contrast. | related_fact_drift |
| `VAL-001-048-F04` | R | MEDIUM | Triage activity is part of what SIRT handles, but operational detail beyond the boundary. | implied_requirement |
| `VAL-001-048-F05` | R | MEDIUM | Investigation activity is part of what SIRT handles, but operational detail. | implied_requirement |
| `VAL-001-048-F06` | O | MEDIUM | External third-party coordination detail; not needed for the SIRT/customer boundary. | related_fact_drift, broad_query_overexpansion |
| `V3-10-F04` | R | MEDIUM | A limit on handling requests; responsive to 'are there limits' but procedural detail. | implied_requirement |
| `V3-14-F05` | R | MEDIUM | Timing window is a procedural detail within the asked process. | implied_requirement |
| `V3-14-F06` | R | MEDIUM | Who decides is a procedural detail within the asked process. | implied_requirement |
| `V3-14-F07a` | R | MEDIUM | Possible reversal outcome; implied by the restoration process but nearly tautological. | implied_requirement |
| `V3-14-F07b` | R | MEDIUM | Possible restoration outcome; implied by the restoration process but nearly tautological. | implied_requirement |

### Thematic-only suggestions (RELEVANT_BUT_OPTIONAL, all cases)

| aspect | case | suggested | confidence | reason |
|---|---|---|---|---|
| `VAL-001-007-F01` | VAL-001-007 | O | MEDIUM | Source explicitly labels contacting the user first as not required; a prep answer can omit it and stay complete. |
| `VAL-001-009-F02` | VAL-001-009 | O | MEDIUM | Submission channel is related procedure, not something the complaint must establish. |
| `VAL-001-010-F02` | VAL-001-010 | O | MEDIUM | Rationale for the no-auto-disable rule; supports the outcome but is not the outcome itself. |
| `VAL-001-022-F05` | VAL-001-022 | O | MEDIUM | Generic restatement of legal limits; adds little beyond the specific limits already covered. |
| `VAL-001-025-F01` | VAL-001-025 | O | MEDIUM | Background about the Community platform; not a rule and not a moderation outcome. |
| `VAL-001-027-F06` | VAL-001-027 | O | MEDIUM | Program-administration communication rule; not a responsibility for qualified users' access. |
| `VAL-001-030-F01` | VAL-001-030 | O | MEDIUM | Restates the query's own premise (preview before GA); adds no risk or commitment content. |
| `VAL-001-032-F01` | VAL-001-032 | O | MEDIUM | General terms/AUP compliance boilerplate; the specific misuse rules carry the answer. |
| `VAL-001-033-F01` | VAL-001-033 | O | MEDIUM | Preventive expectation-setting, not a live option for the ongoing abusive discussion. |
| `VAL-001-037-F01` | VAL-001-037 | O | MEDIUM | Scope of the developer agreement; background rather than responsibility or listing rights. |
| `VAL-001-039-F02` | VAL-001-039 | O | MEDIUM | Source-code offer is related OSS compliance detail, not where licenses are documented. |
| `VAL-001-040-F05` | VAL-001-040 | O | MEDIUM | Effective-date detail of DPA coverage; omission does not change the evaluate/production answer. |
| `VAL-001-044-F01` | VAL-001-044 | O | MEDIUM | Definitional context on what self-hosted GHES means; the query already assumes self-hosting. |
| `VAL-001-044-F04` | VAL-001-044 | O | MEDIUM | ECCN classification detail; informs but is not itself an export limit. |
| `VAL-001-047-F03` | VAL-001-047 | O | MEDIUM | Organization-specific subpoena scope detail; not needed for the subpoena-vs-access-logs contrast. |
| `VAL-001-048-F06` | VAL-001-048 | O | MEDIUM | External third-party coordination detail; not needed for the SIRT/customer boundary. |
| `VAL-001-049-F01` | VAL-001-049 | O | MEDIUM | Government-official gifts are a different recipient category than the asked customer scenario. |
| `VAL-001-049-F06` | VAL-001-049 | O | MEDIUM | Receiving-from-vendors rule; the query is about giving to a customer. |
| `VAL-001-050-F01` | VAL-001-050 | O | MEDIUM | Commitment trigger/scope context; the question is about reinstatement timing after cure. |
| `VAL-001-050-F05` | VAL-001-050 | O | MEDIUM | Covered-license list confirms applicability but is not part of the reinstatement timing. |

## Likely rubric contamination

Old rubric likely marked these `required` because the source document contains them, not because the query requires them. Suggested below as `RELEVANT_BUT_OPTIONAL` / `AMBIGUOUS`; reviewers decide. Do not edit gold from this list automatically.

| aspect | case | suggested | flag | reason |
|---|---|---|---|---|
| `VAL-001-009-F02` | VAL-001-009 | O | related_fact_drift | Submission channel is related procedure, not something the complaint must establish. |
| `VAL-001-010-F02` | VAL-001-010 | O | background_detail,related_fact_drift | Rationale for the no-auto-disable rule; supports the outcome but is not the outcome itself. |
| `VAL-001-011-F01` | VAL-001-011 | A | related_fact_drift,rubric_contamination | Torn between the policy's threat/incitement prong and the depiction prong the query targets. |
| `VAL-001-022-F05` | VAL-001-022 | O | related_fact_drift,broad_query_overexpansion | Generic restatement of legal limits; adds little beyond the specific limits already covered. |
| `VAL-001-027-F06` | VAL-001-027 | O | related_fact_drift,broad_query_overexpansion | Program-administration communication rule; not a responsibility for qualified users' access. |
| `VAL-001-032-F01` | VAL-001-032 | O | related_fact_drift,rubric_contamination | General terms/AUP compliance boilerplate; the specific misuse rules carry the answer. |
| `VAL-001-033-F01` | VAL-001-033 | O | related_fact_drift | Preventive expectation-setting, not a live option for the ongoing abusive discussion. |
| `VAL-001-039-F02` | VAL-001-039 | O | related_fact_drift | Source-code offer is related OSS compliance detail, not where licenses are documented. |
| `VAL-001-043-F01` | VAL-001-043 | A | implied_requirement,related_fact_drift | Incoming-request completeness criteria vs the post-completeness steps the query focuses on. |
| `VAL-001-044-F04` | VAL-001-044 | O | related_fact_drift | ECCN classification detail; informs but is not itself an export limit. |
| `VAL-001-047-F03` | VAL-001-047 | O | related_fact_drift | Organization-specific subpoena scope detail; not needed for the subpoena-vs-access-logs contrast. |
| `VAL-001-048-F06` | VAL-001-048 | O | related_fact_drift,broad_query_overexpansion | External third-party coordination detail; not needed for the SIRT/customer boundary. |
| `VAL-001-049-F01` | VAL-001-049 | O | related_fact_drift | Government-official gifts are a different recipient category than the asked customer scenario. |
| `VAL-001-049-F06` | VAL-001-049 | O | related_fact_drift | Receiving-from-vendors rule; the query is about giving to a customer. |
| `VAL-001-050-F01` | VAL-001-050 | O | background_detail,related_fact_drift | Commitment trigger/scope context; the question is about reinstatement timing after cure. |

## Reviewer priority queue

1. **AMBIGUOUS:** `VAL-001-011-F01`, `VAL-001-043-F01`.
2. **LOW confidence:** `VAL-001-011-F01`, `VAL-001-043-F01` (overlaps with 1).
3. **Potentially rubric-contaminated:** `VAL-001-009-F02`, `VAL-001-010-F02`, `VAL-001-011-F01`, `VAL-001-022-F05`, `VAL-001-027-F06`, `VAL-001-032-F01`, `VAL-001-033-F01`, `VAL-001-039-F02`, `VAL-001-043-F01`, `VAL-001-044-F04`, `VAL-001-047-F03`, `VAL-001-048-F06`, `VAL-001-049-F01`, `VAL-001-049-F06`, `VAL-001-050-F01`.
4. **Broad-query boundary:** `VAL-001-005-F02`, `VAL-001-005-F05`, `VAL-001-006-F04`, `VAL-001-006-F05`, `VAL-001-007-F01`, `VAL-001-007-F02`, `VAL-001-007-F03`, `VAL-001-008-F03`, `VAL-001-012-F02`, `VAL-001-018-F02`, `VAL-001-022-F05`, `VAL-001-025-F01`, `VAL-001-026-F02`, `VAL-001-037-F01`, `VAL-001-039-F02`, `VAL-001-039-F03`, `VAL-001-042-F02`, `VAL-001-042-F04`, `VAL-001-043-F01`, `VAL-001-044-F01`, `VAL-001-044-F04`, `VAL-001-047-F03`, `VAL-001-048-F04`, `VAL-001-048-F05`, `VAL-001-048-F06`, `V3-10-F04`, `V3-14-F05`, `V3-14-F06`, `V3-14-F07a`, `V3-14-F07b`.
5. Remaining straightforward items: all other aspect IDs (HIGH confidence), starting with the medium-confidence required items if time allows.

## Integrity notes

- Worksheet, router, arms, Stage 0 config, and contract hashes were re-verified against the Stage 0 freeze report and match.
- No frozen artifact was modified; no A1/A2/A3 code was run; no LLM API was called.
- Source documents were read only to understand aspect meaning (for example, to confirm that "Ask Nicely First" is labeled optional in the source).
- Recommendations are architecture-independent and blind to replay metrics.
