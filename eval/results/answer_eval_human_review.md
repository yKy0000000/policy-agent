# Broad Query V3 answer quality review

Raw model judgments remain in the JSON. The decisions below come from offline source inspection; independent human sign-off is still useful. Do not edit the frozen rubric.

## Targeted fact adjudication

- V3-01 / fixed_top5 / V3-01-F01: **evidence_mapping_gap**; selected source chunk_d6d1c627931350dcab91a60d; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-01 / coverage_selector_v2 / V3-01-F01: **evidence_mapping_gap**; selected source chunk_d6d1c627931350dcab91a60d; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-04 / fixed_top5 / V3-04-F02: **evidence_mapping_gap**; selected source chunk_c05a222b5013b1f82b468408; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-10 / fixed_top5 / V3-10-F02: **judge_false_positive**; selected source none; The answer lists access, correction and deletion, but omits restriction of processing.
- V3-10 / fixed_top5 / V3-10-F03: **evidence_mapping_gap**; selected source chunk_153e4163c312de7c055f6c77; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-10 / fixed_top5 / V3-10-F04: **evidence_mapping_gap**; selected source chunk_153e4163c312de7c055f6c77; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-10 / fixed_top5 / V3-10-F05: **evidence_mapping_gap**; selected source chunk_e98271d801fbe9c2d627f885; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-11 / fixed_top5 / V3-11-F03: **evidence_mapping_gap**; selected source chunk_312d5e57a467a74c75e0200c; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-11 / coverage_selector_v2 / V3-11-F03: **evidence_mapping_gap**; selected source chunk_312d5e57a467a74c75e0200c; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-14 / fixed_top5 / V3-14-F04: **evidence_mapping_gap**; selected source chunk_bd4c111b1d64dd00cac67c66; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.
- V3-14 / coverage_selector_v2 / V3-14-F04: **evidence_mapping_gap**; selected source chunk_bd4c111b1d64dd00cac67c66; The cited selected chunk directly supports the full fact; the frozen mapping omits this chunk.

## Targeted claim and citation adjudication

- V3-04 / fixed_top5 / claim 11: **unsupported**; factual status unverified; support unsupported; citation missing. Broad absence claim is not established by the supplied excerpts.
- V3-04 / adaptive_prefix_v1 / claim 13: **unsupported**; factual status unverified; support unsupported; citation missing. Broad absence claim is not established by the supplied excerpts.
- V3-04 / coverage_selector_v2 / claim 6: **unsupported**; factual status unverified; support unsupported; citation missing. Broad absence claim is not established by the supplied excerpts.
- V3-05 / fixed_top5 / claim 10: **citation_misaligned**; factual status supported; support supported; citation missing. The recovery policy explicitly excludes other recovery means, but this concluding sentence lacks a citation.
- V3-05 / adaptive_prefix_v1 / claim 10: **citation_misaligned**; factual status supported; support supported; citation missing. The recovery policy explicitly excludes other recovery means, but this concluding sentence lacks a citation.
- V3-10 / fixed_top5 / claim 12: **unsupported**; factual status unverified; support unsupported; citation missing. Broad absence claim is not established by the supplied excerpts.
- V3-10 / adaptive_prefix_v1 / claim 14: **partial_support**; factual status partially_supported; support partial; citation missing. The cited scope or retention examples support caution, but not the full absence claim.
- V3-10 / coverage_selector_v2 / claim 12: **partial_support**; factual status partially_supported; support partial; citation missing. The cited scope or retention examples support caution, but not the full absence claim.

## Remaining review checklist

- [ ] Independently verify the ten direct-support mapping gap decisions before any future rubric revision.
- [ ] Review any other ambiguous model judgments before external use.

## V3-01 / fixed_top5

- Answer fact coverage: 1/4.
- Missing facts: V3-01-F02, V3-01-F03, V3-01-F04.
- Judge-covered facts absent from frozen evidence mappings: V3-01-F01 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable


## V3-01 / coverage_selector_v2

- Answer fact coverage: 2/4.
- Missing facts: V3-01-F03, V3-01-F04.
- Judge-covered facts absent from frozen evidence mappings: V3-01-F01 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable


## V3-04 / fixed_top5

- Answer fact coverage: 5/5.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: V3-04-F02 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 1 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify any additional criteria (such as specific timelines or thresholds) beyond the above for when GitHub will treat a brand-name account as a trademark problem. — unsupported, citation missing

## V3-04 / adaptive_prefix_v1

- Answer fact coverage: 5/5.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 1 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided policies do not specify any additional criteria (such as a required likelihood-of-confusion legal standard or timelines) beyond the above. — unsupported, citation missing

## V3-04 / coverage_selector_v2

- Answer fact coverage: 5/5.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 1 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify any additional criteria, timelines, or outcomes beyond these. — unsupported, citation missing

## V3-05 / fixed_top5

- Answer fact coverage: 6/6.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided policies do not specify any additional recovery options beyond those above. — supported, citation missing

## V3-05 / adaptive_prefix_v1

- Answer fact coverage: 6/6.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided policies do not specify any additional recovery options beyond those above. — supported, citation missing

## V3-06 / adaptive_prefix_v1

- Answer fact coverage: 4/4.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify a general process for you to request enforcement against a suspected squatter, beyond the name squatting policy itself and the trademark complaint route for claimed usernames. — uncertain, citation supported; The supplied evidence does not explicitly state whether a general enforcement-request process exists or is absent.

## V3-10 / fixed_top5

- Answer fact coverage: 3/6.
- Missing facts: V3-10-F01, V3-10-F02, V3-10-F06.
- Judge-covered facts absent from frozen evidence mappings: V3-10-F03, V3-10-F04, V3-10-F05 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 1 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify any other limits on access, correction, or deletion beyond those described above. — unsupported, citation missing; This is a meta-claim about the provided policies and is not directly supported by a cited policy provision.

## V3-10 / adaptive_prefix_v1

- Answer fact coverage: 6/6.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify a single universal retention period beyond the 90-day profile deletion timeframe noted above and the general retention principles described. — partial, citation missing; This is a meta-claim about the provided policies and is not directly supported by a cited policy provision.

## V3-10 / coverage_selector_v2

- Answer fact coverage: 6/6.
- Missing facts: none.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: The provided published policies do not specify whether these particular limits apply to all users globally. — partial, citation missing; This is a meta-claim about the provided policies and is not directly supported by a cited policy provision.

## V3-11 / fixed_top5

- Answer fact coverage: 3/4.
- Missing facts: V3-11-F01.
- Judge-covered facts absent from frozen evidence mappings: V3-11-F03 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable


## V3-11 / coverage_selector_v2

- Answer fact coverage: 3/4.
- Missing facts: V3-11-F01.
- Judge-covered facts absent from frozen evidence mappings: V3-11-F03 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable


## V3-12 / adaptive_prefix_v1

- Answer fact coverage: 6/7.
- Missing facts: V3-12-F04.
- Judge-covered facts absent from frozen evidence mappings: none (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable

- Claim: GitHub Copilot and GitHub Enterprise Server may not be sold, exported, or re-exported to embargoed destinations or Country Group E:1 destinations, which currently include Cuba, Iran, and the specified regions of Ukraine (Crimea/Sevastopol and the separatist areas of Donetsk and Luhansk). — partial, citation supported; The cited sources support the restriction for GitHub Copilot and GitHub Enterprise Server, but the answer's combined statement omits that the GitHub Enterprise Server restriction is framed as may not be sold to, exported, or re-exported to Country Group E:1 countries or the specified regions of Ukraine, and the Copilot source also lists North Korea, Russia, and Belarus.

## V3-14 / fixed_top5

- Answer fact coverage: 4/8.
- Missing facts: V3-14-F05, V3-14-F06, V3-14-F07a, V3-14-F07b.
- Judge-covered facts absent from frozen evidence mappings: V3-14-F04 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable


## V3-14 / coverage_selector_v2

- Answer fact coverage: 7/8.
- Missing facts: V3-14-F05.
- Judge-covered facts absent from frozen evidence mappings: V3-14-F04 (check evidence support, judge decision and possible rubric disagreement).
- Unsupported / contradicted claims: 0 / 0.
- [ ] Judge fact decisions checked
- [ ] Claim grounding and citations checked
- [ ] Rubric disagreement candidate recorded if applicable
