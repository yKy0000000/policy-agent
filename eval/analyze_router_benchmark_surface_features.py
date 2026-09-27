"""Deterministic, query-only surface analysis for Router Benchmark V1.

This script does not run retrieval, a model, decomposition, or a Router. The
auditor's source-layout groups are used only to compare feature distributions.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORD = re.compile(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*")
CLAUSE = re.compile(r"\b(?:and|also|but|while|or|then)\b", re.I)
COORDINATED_QUESTION = re.compile(
    r"\b(?:and|or)\s+(?:what|which|who|where|when|why|how|can|could|"
    r"should|would|will|do|does|did|is|are|was|were|have|has)\b",
    re.I,
)

# Conservative, literal cues only. These are not an inferred number of policy
# domains: ordinary synonyms, implicit topics, and document relationships are
# deliberately not inferred.
NAMED_TOPIC_CUES = {
    "private-information": re.compile(r"\bprivate-information removal\b", re.I),
    "privacy": re.compile(r"\bprivacy\b", re.I),
    "misinformation": re.compile(r"\bmisinformation\b", re.I),
    "DMCA": re.compile(r"\bDMCA\b", re.I),
    "trademark": re.compile(r"\btrademark(?:-policy)?\b", re.I),
    "bug-bounty": re.compile(r"\bbug bounty\b", re.I),
    "site-policies": re.compile(r"\bsite policies\b", re.I),
    "government-takedown": re.compile(r"\b(?:government-takedowns|content-takedown)\b", re.I),
    "Marketplace": re.compile(r"\bMarketplace\b", re.I),
    "Sponsors": re.compile(r"\bSponsors?\b", re.I),
    "event": re.compile(r"\bGitHub event\b", re.I),
    "AI-feature": re.compile(r"\bAI feature\b", re.I),
    "trade-restricted": re.compile(r"\btrade-restricted\b", re.I),
    "subprocessor": re.compile(r"\bsubprocessor\b", re.I),
    "malware": re.compile(r"\bmalware\b", re.I),
    "exploit": re.compile(r"\bexploit\b", re.I),
}


def surface_pattern(query: str, question_count: int) -> str:
    """Return a lexical pattern, with fixed priority and no semantic reading."""
    if re.search(r"\b(?:but|while|without)\b", query, re.I):
        return "contrastive condition"
    if re.search(r"\b(?:if|when|unless)\b", query, re.I):
        return "conditional request"
    if question_count > 1 or re.search(r"\b(?:and|also|or|then)\b", query, re.I):
        return "coordinated request"
    return "single request"


def features(case: dict[str, object]) -> dict[str, object]:
    query = str(case["query"])
    question_count = query.count("?") + len(COORDINATED_QUESTION.findall(query))
    cues = [name for name, pattern in NAMED_TOPIC_CUES.items() if pattern.search(query)]
    return {
        "id": case["id"],
        "length_chars": len(query),
        "token_or_word_count": len(WORD.findall(query)),
        "clause_marker_count": len(CLAUSE.findall(query)),
        "question_structure_count": question_count,
        "explicit_topic_cue_count": len(cues),
        "explicit_topic_cues": cues,
        "query_structural_pattern": surface_pattern(query, question_count),
        "has_and_or_also": bool(re.search(r"\b(?:and|also)\b", query, re.I)),
    }


def describe(rows: list[dict[str, object]], key: str) -> str:
    values = [int(row[key]) for row in rows]
    return (
        f"{min(values)}–{max(values)}; median {statistics.median(values):g}; "
        f"mean {statistics.mean(values):.1f}"
    )


def main() -> None:
    benchmark = json.loads((HERE / "router_benchmark_v1_freeze_candidate.json").read_text(encoding="utf-8"))
    audit = json.loads((HERE / "router_benchmark_v1_audit_changes.json").read_text(encoding="utf-8"))
    coverage = audit["corrected_coverage_after_changes"]
    group_one = set(coverage["likely_localized"]) | set(coverage["likely_multi_section_single_document"])
    group_two = set(coverage["likely_multi_document"])
    rows = [features(case) for case in benchmark["cases"]]
    ids = {row["id"] for row in rows}
    if len(rows) != 20 or group_one & group_two or group_one | group_two != ids:
        raise ValueError("Auditor source-layout groups must partition exactly 20 queries")

    print("## Fixed measurement rules")
    print("- `length_chars`: Python Unicode code points in `query`, including spaces and punctuation.")
    print("- `token_or_word_count`: matches `[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*`; hyphenated/apostrophe words count once.")
    print("- `clause_marker_count`: whole-word, case-insensitive occurrences of `and`, `also`, `but`, `while`, `or`, `then`.")
    print("- `question_structure_count`: number of `?` plus explicit `and/or` followed by an interrogative/auxiliary word (what/which/who/where/when/why/how/can/could/should/would/will/do/does/did/is/are/was/were/have/has). This is a syntax proxy, not a semantic sub-ask count.")
    print("- `explicit_topic_cue_count`: distinct literal cue families matched by the fixed lexicon in the script; a conservative proxy, not a policy-document or semantic-topic count.")
    print("- `query_structural_pattern`: priority `but|while|without` → contrastive condition; else `if|when|unless` → conditional request; else `question_structure_count > 1` or `and|also|or|then` → coordinated request; else single request.")
    print("- Group 1: auditor's 5 likely-localized plus 6 likely-multi-section single-document queries. Group 2: auditor's 9 likely-multi-document queries. These are source-layout groups for analysis, not routing labels. `fragmented_evidence` and `multi_requirement` can occur in either group.")

    print("\n## Per-query surface features")
    print("| id | source-layout group | chars | words | clause markers | question structures | literal topic cues | structural pattern |")
    print("|---|---|---:|---:|---:|---:|---:|---|")
    for row in rows:
        group = "G1" if row["id"] in group_one else "G2"
        print(
            f"| {row['id']} | {group} | {row['length_chars']} | "
            f"{row['token_or_word_count']} | {row['clause_marker_count']} | "
            f"{row['question_structure_count']} | {row['explicit_topic_cue_count']} | "
            f"{row['query_structural_pattern']} |"
        )

    print("\n## Distribution by source-layout group")
    print("| feature | Group 1 (n=11) min–max; median; mean | Group 2 (n=9) min–max; median; mean |")
    print("|---|---|---|")
    for key, label in [
        ("length_chars", "characters"),
        ("token_or_word_count", "words"),
        ("clause_marker_count", "clause markers"),
        ("question_structure_count", "question structures"),
        ("explicit_topic_cue_count", "literal topic cues"),
    ]:
        first = [row for row in rows if row["id"] in group_one]
        second = [row for row in rows if row["id"] in group_two]
        print(f"| {label} | {describe(first, key)} | {describe(second, key)} |")

    checks = [
        ("words ≥ 35", lambda row: int(row["token_or_word_count"]) >= 35),
        ("characters ≥ 200", lambda row: int(row["length_chars"]) >= 200),
        ("clause markers ≥ 2", lambda row: int(row["clause_marker_count"]) >= 2),
        ("contains `and` or `also`", lambda row: bool(row["has_and_or_also"])),
        ("question structures ≥ 2", lambda row: int(row["question_structure_count"]) >= 2),
        ("literal topic cues ≥ 2", lambda row: int(row["explicit_topic_cue_count"]) >= 2),
    ]
    print("\n## Illustrative shallow checks (fixed thresholds, not fitted)")
    print("| surface check | Group 1 hits / 11 | Group 2 hits / 9 | Group 1 matching IDs | Group 2 matching IDs |")
    print("|---|---:|---:|---|---|")
    for label, predicate in checks:
        hits_one = [str(row["id"]) for row in rows if row["id"] in group_one and predicate(row)]
        hits_two = [str(row["id"]) for row in rows if row["id"] in group_two and predicate(row)]
        print(f"| {label} | {len(hits_one)} | {len(hits_two)} | {', '.join(hits_one) or '—'} | {', '.join(hits_two) or '—'} |")

    print("\n## Pattern counts")
    for group_name, group_ids in [("Group 1", group_one), ("Group 2", group_two)]:
        counts = Counter(str(row["query_structural_pattern"]) for row in rows if row["id"] in group_ids)
        print(f"- {group_name}: " + "; ".join(f"{name} {counts[name]}" for name in ["single request", "coordinated request", "conditional request", "contrastive condition"]))

    print("\n## Literal cue matches")
    for row in rows:
        print(f"- {row['id']}: {', '.join(row['explicit_topic_cues']) or 'none'}")


if __name__ == "__main__":
    main()
