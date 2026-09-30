# Final Controller Gate V1 - Sample Eligibility (Phase 0)

> Frozen selection derived from existing frozen artifacts only. No new questions, no new
> labels, no benchmark construction. `039-F02` is `RELEVANT_BUT_OPTIONAL` and is therefore
> an optional-pressure control, never a required positive.

- counts: {'patch_positive': 2, 'patch_judge_disagreement': 2, 'refresh_positive': 3, 'complete_control': 3, 'optional_pressure': 2, 'secondary_refresh': 1}
- planned sensor calls: 26 (2 replicates)

| case | role | expected action | route | draft omits (A1) | in-context | A1 label | target facts |
|---|---|---|---|---|---|---|---|
| VAL-001-011 | patch_positive | PATCH_CONTEXT | SIMPLE | True | True | VAL-001-011-F01:NOT_COVERED | VAL-001-011-F01 |
| VAL-001-050 | patch_positive | PATCH_CONTEXT | SIMPLE | True | True | VAL-001-050-F01:NOT_COVERED | VAL-001-050-F01 |
| VAL-001-009 | patch_judge_disagreement | PATCH_CONTEXT | SIMPLE | False | True | VAL-001-009-F01:COVERED | VAL-001-009-F01 |
| VAL-001-022 | patch_judge_disagreement | PATCH_CONTEXT | BROAD | False | True | VAL-001-022-F02:COVERED | VAL-001-022-F02 |
| VAL-001-006 | refresh_positive | REFRESH_CONTEXT | BROAD | True | False | VAL-001-006-F02:NOT_COVERED | VAL-001-006-F02 |
| VAL-001-033 | refresh_positive | REFRESH_CONTEXT | SIMPLE | True | False | VAL-001-033-F01:NOT_COVERED, VAL-001-033-F02:NOT_COVERED, VAL-001-033-F03:NOT_COVERED, VAL-001-033-F04:NOT_COVERED, VAL-001-033-F05:NOT_COVERED | VAL-001-033-F01, VAL-001-033-F02, VAL-001-033-F03, VAL-001-033-F04, VAL-001-033-F05 |
| VAL-001-046 | refresh_positive | REFRESH_CONTEXT | BROAD | True | False | VAL-001-046-F03:NOT_COVERED, VAL-001-046-F04:NOT_COVERED | VAL-001-046-F03, VAL-001-046-F04 |
| VAL-001-029 | complete_control | RETURN_DRAFT | BROAD | False | None | - | - |
| VAL-001-042 | complete_control | RETURN_DRAFT | BROAD | False | None | - | - |
| VAL-001-007 | complete_control | RETURN_DRAFT | BROAD | False | None | - | - |
| VAL-001-026 | optional_pressure | RETURN_DRAFT | BROAD | False | True | VAL-001-026-F02:None | VAL-001-026-F02 |
| VAL-001-039 | optional_pressure | RETURN_DRAFT | BROAD | False | True | VAL-001-039-F02:None | VAL-001-039-F02 |
| VAL-001-001 | secondary_refresh | REFRESH_CONTEXT | BROAD | False | False | VAL-001-001-F02:NOT_COVERED, VAL-001-001-F03:COVERED | VAL-001-001-F02, VAL-001-001-F03 |

## Truth rows

- VAL-001-011-F01 (QUERY_REQUIRED, in_context=True): GitHub prohibits using the platform to organize, promote, threaten, or incite violence.
- VAL-001-050-F01 (QUERY_REQUIRED, in_context=True): The commitment applies before GitHub brings a non-defensive claim arising from termination of a Covered License.
- VAL-001-009-F01 (QUERY_REQUIRED, in_context=True): The claim concerns a technological measure that effectively controls access to a copyright-protected work.
- VAL-001-022-F02 (QUERY_REQUIRED, in_context=True): Disclosed data must be used consistently with the candidate privacy statement.
- VAL-001-006-F02 (QUERY_REQUIRED, in_context=False): It must identify allegedly infringing material specifically enough for GitHub to locate it, including a URL at minimum.
- VAL-001-033-F01 (QUERY_REQUIRED, in_context=False): Maintainers can publish community-specific expectations for project interaction.
- VAL-001-033-F02 (QUERY_REQUIRED, in_context=False): People with repository write access can edit, delete, or hide comments.
- VAL-001-033-F03 (QUERY_REQUIRED, in_context=False): Authorized repository members can lock disruptive conversations.
- VAL-001-033-F04 (QUERY_REQUIRED, in_context=False): An account or organization can block a user.
- VAL-001-033-F05 (QUERY_REQUIRED, in_context=False): A public project can set temporary interaction limits when facing unwanted attention.
- VAL-001-046-F03 (QUERY_REQUIRED, in_context=False): Before disclosure, GitHub makes a reasonable effort to email affected owners a copy of the legal process so they can challenge it.
- VAL-001-046-F04 (QUERY_REQUIRED, in_context=False): In rare urgent circumstances, GitHub may delay notice to prevent death or serious harm or because of an ongoing investigation.
- VAL-001-026-F02 (RELEVANT_BUT_OPTIONAL, in_context=True): The developer must follow GitHub's technical specifications and requirements.
- VAL-001-039-F02 (RELEVANT_BUT_OPTIONAL, in_context=True): GitHub offers source code where component licenses require such an offer.
- VAL-001-001-F02 (QUERY_REQUIRED, in_context=False): The counter notice is sworn under penalty of perjury.
- VAL-001-001-F03 (QUERY_REQUIRED, in_context=False): Intentionally false sworn information can cause criminal and civil consequences.