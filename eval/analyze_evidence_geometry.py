"""Offline evidence-geometry diagnostic for Broad Query Validation V1.

Step -1 audits the Validation V1 rubric-disagreement facts (answer covered a
fact whose mapped evidence was not supplied). Step 0 computes a gold-aware
minimum evidence cover over the frozen ``direct_chunk_ids`` mapping, a fixed
representation counterfactual, and support/dispersion geometry.

This module is read-only over the frozen benchmark: it never edits the frozen
rubric, queries, metadata, historical results, or the production pipeline. It
uses no network, no LLM, no generation, and no judge. The only model touch is
the already-cached local retriever, used once to recover the candidate union
and the current reranked Top20; that output is cached back into the diagnostic
artifact so later runs are model-free.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "eval/validation/validation_v1_metadata.json"
RUBRIC = ROOT / "eval/validation/broad_atomic_facts_validation_v1.json"
QUERIES = ROOT / "eval/validation/broad_queries_validation_v1.json"
PREPARED = ROOT / "cache/validation_v1_prepare.json"
RESULTS = ROOT / "eval/validation/results/validation_v1_results.json"
INDEX = ROOT / "cache/policy_index.json"
OUTPUT = ROOT / "eval/results/evidence_geometry_analysis.json"
SUMMARY = ROOT / "eval/results/evidence_geometry_summary.md"
AUDIT = ROOT / "eval/results/validation_mapping_audit.json"
GAP = ROOT / "eval/results/evidence_complete_answer_gap_analysis.json"

STRATEGY_ROUTE = {"always_v1": "adaptive_prefix_v1"}

# Pre-registered diagnostic thresholds. Written before observing Step 0 data.
CONFIG = {
    "window_size": 3,
    "overlap_merge_max_chars": 800,
    "overlap_group_min_chars": 200,
    "overlap_group_adjacency": 1,
    "fragmentation_k_drop": 0.30,
    "fragmentation_token_rise": 0.10,
    "high_min_cover_k": 6,
    "v1_deep_k": 10,
    "headroom_token_saving": 0.30,
    "audit_lexical_trace": 0.34,
    "util_late_evidence_percentile": 0.50,
    "util_many_selected_chunks_k": 8,
    "util_compression_words_per_1k": 60,
    "notes": "Diagnostic heuristics, not scientific laws. Frozen before Step 0 was run.",
}

_ENUM_MARKER = re.compile(
    r"\b(and|or|as well as|including|such as|following|list|which of|what .+ are)\b|,|;",
    re.IGNORECASE)
_CONDITION_MARKER = re.compile(
    r"\b(if|unless|except|when|before|after|require|required|condition|limit|deadline|"
    r"within|before|after|who|eligible)\b", re.IGNORECASE)

_RANK_BUCKETS = (("rank_1", 1, 1), ("rank_2_5", 2, 5), ("rank_6_8", 6, 8),
                 ("rank_9_10", 9, 10), ("rank_11_20", 11, 20))

AUDIT_CATEGORIES = (
    "judge_false_positive",
    "existing_direct_mapping_sufficient",
    "missing_direct_mapping_candidate",
    "partial_support",
    "unresolved",
)

GAP_CATEGORIES = (
    "utilization_miss",
    "partial_synthesis",
    "citation_grounding_issue",
    "judge_rubric_disagreement",
    "compression_organization_loss",
    "other_or_unclear",
)

_WORDS = re.compile(r"[a-z]{3,}")
_STOP = frozenset(
    "a an the and or to of in on by for with from what how can could should would is are be my "
    "your our this that it its do does if i we you they their them there was were will not no "
    "may must shall any all each such when who which where why".split()
)


# --------------------------------------------------------------------------- #
# Pure geometry helpers (unit-testable, no model, no IO)
# --------------------------------------------------------------------------- #

def approx_tokens(text: str) -> int:
    """Deterministic lexical token proxy, shared by every level and scope."""
    return len(re.findall(r"\w+|[^\w\s]", text))


def _terms(value: str) -> set[str]:
    return {word.rstrip("s") for word in _WORDS.findall(value.casefold()) if word not in _STOP}


def _solve_cover(fact_to_units: dict[str, set[str]], weights: dict[str, int] | None,
                 require_all: bool) -> tuple[int | None, list[str]]:
    """Exact minimum-weight set cover by branch and bound.

    ``weights is None`` minimizes cardinality; otherwise it minimizes the summed
    weight (tokens). Returns ``(cost, units)``; ``cost is None`` marks an
    impossible cover when ``require_all`` is set. Facts with no candidate unit
    are dropped from the objective when ``require_all`` is false.
    """
    mapping = {f: set(u) for f, u in fact_to_units.items()}
    if require_all and any(not u for u in mapping.values()):
        return None, []
    facts = [f for f in sorted(mapping) if mapping[f]]
    if not facts:
        return 0, []
    bit = {f: index for index, f in enumerate(facts)}
    unit_mask: dict[str, int] = {}
    for fact in facts:
        for unit in mapping[fact]:
            unit_mask[unit] = unit_mask.get(unit, 0) | (1 << bit[fact])
    full = (1 << len(facts)) - 1
    best_by_mask: dict[int, tuple[tuple[int, str], str]] = {}
    for unit, mask in unit_mask.items():
        weight = 1 if weights is None else int(weights.get(unit, 0))
        key = (weight, unit)
        if mask not in best_by_mask or key < best_by_mask[mask][0]:
            best_by_mask[mask] = (key, unit)
    masks = sorted(best_by_mask)
    cover_bits: dict[int, list[int]] = defaultdict(list)
    for mask in masks:
        for index in range(len(facts)):
            if mask >> index & 1:
                cover_bits[index].append(mask)
    best: dict[str, object] = {"cost": None, "units": []}

    def dfs(covered: int, cost: int, chosen: list[str]) -> None:
        if covered == full:
            candidate = (cost, tuple(chosen))
            current = best["cost"]
            if current is None or candidate < (current, tuple(best["units"])):  # type: ignore[operator]
                best["cost"], best["units"] = cost, list(chosen)
            return
        if best["cost"] is not None and cost >= best["cost"]:  # type: ignore[operator]
            return
        remaining = [i for i in range(len(facts)) if not covered >> i & 1]
        pivot = min(remaining, key=lambda i: len(cover_bits[i]))
        for mask in cover_bits[pivot]:
            if mask & covered == mask:
                continue
            weight, unit = best_by_mask[mask][0]
            dfs(covered | mask, cost + weight, chosen + [unit])

    dfs(0, 0, [])
    if best["cost"] is None:
        return None, []
    return int(best["cost"]), list(best["units"])  # type: ignore[arg-type]


def min_cardinality_cover(fact_to_units: dict[str, set[str]], *,
                          require_all: bool = True) -> tuple[int | None, list[str]]:
    return _solve_cover(fact_to_units, None, require_all)


def min_token_cover(fact_to_units: dict[str, set[str]], unit_tokens: dict[str, int], *,
                    require_all: bool = True) -> tuple[int | None, list[str]]:
    return _solve_cover(fact_to_units, unit_tokens, require_all)


def _max_overlap(left: str, right: str, cap: int) -> int:
    limit = min(cap, len(left), len(right))
    for size in range(limit, 0, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def overlap_aware_merge(texts: list[str], *, max_overlap: int = 800) -> str:
    """Join texts, removing the duplicated 400-char chunk overlap between parts."""
    merged = ""
    for text in texts:
        if not merged:
            merged = text
            continue
        overlap = _max_overlap(merged, text, max_overlap)
        merged = merged + (text[overlap:] if overlap else "\n" + text)
    return merged


def build_level0_units(chunks: list[dict]) -> list[dict]:
    return [{"unit_id": c["chunk_id"], "source_path": c["source_path"],
             "heading_path": tuple(c.get("heading_path") or ()),
             "chunk_index": c["chunk_index"], "chunk_ids": [c["chunk_id"]],
             "token_count": approx_tokens(c["text"])} for c in chunks]


def build_local_windows(chunks: list[dict], *, size: int = 3) -> list[dict]:
    by_doc: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        by_doc[chunk["source_path"]].append(chunk)
    units: list[dict] = []
    for source, parts in by_doc.items():
        ordered = sorted(parts, key=lambda c: c["chunk_index"])
        half = size // 2
        for index, anchor in enumerate(ordered):
            window = ordered[max(0, index - half): index + half + 1]
            units.append({
                "unit_id": f"W{size}::{source}::{anchor['chunk_index']}",
                "source_path": source,
                "chunk_ids": [item["chunk_id"] for item in window],
                "texts": [item["text"] for item in window],
            })
    for unit in units:
        unit["token_count"] = approx_tokens(overlap_aware_merge(unit["texts"]))
    return units


def build_top1_subtrees(chunks: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for chunk in chunks:
        heading = tuple(chunk.get("heading_path") or ())
        top = heading[0] if heading else "__document_root__"
        groups[(chunk["source_path"], top)].append(chunk)
    units: list[dict] = []
    for (source, top), parts in groups.items():
        ordered = sorted(parts, key=lambda c: c["chunk_index"])
        units.append({
            "unit_id": f"SUB::{source}::{top}",
            "source_path": source,
            "heading_path": (top,),
            "chunk_ids": [item["chunk_id"] for item in ordered],
            "texts": [item["text"] for item in ordered],
        })
    for unit in units:
        unit["token_count"] = approx_tokens(overlap_aware_merge(unit["texts"]))
    return units


def unit_index(units: list[dict]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for unit in units:
        for chunk_id in unit["chunk_ids"]:
            index[chunk_id].add(unit["unit_id"])
    return index


def fact_units(facts: list[dict], units: list[dict]) -> dict[str, set[str]]:
    index = unit_index(units)
    return {fact["fact_id"]: {unit for chunk_id in fact["direct_chunk_ids"]
                              for unit in index.get(chunk_id, ())} for fact in facts}


def support_groups(support_ids: list[str], meta: dict[str, dict], *,
                   adjacency: int = 1, min_overlap_chars: int = 200) -> list[list[str]]:
    """Collapse direct-support chunks that are 400-char overlap duplicates."""
    ids = sorted(set(support_ids))
    parent = {chunk_id: chunk_id for chunk_id in ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            left, right = meta[a], meta[b]
            if left["source_path"] != right["source_path"]:
                continue
            if _norm(left["text"]) == _norm(right["text"]):
                union(a, b)
                continue
            same_heading = tuple(left.get("heading_path") or ()) == tuple(right.get("heading_path") or ())
            near = abs(left["chunk_index"] - right["chunk_index"]) <= adjacency
            if not (same_heading and near):
                continue
            merged = overlap_aware_merge([left["text"], right["text"]])
            collapsed = len(left["text"]) + len(right["text"]) - len(merged)
            if collapsed >= min_overlap_chars:
                union(a, b)
    groups: dict[str, list[str]] = defaultdict(list)
    for chunk_id in ids:
        groups[find(chunk_id)].append(chunk_id)
    return sorted((sorted(v) for v in groups.values()), key=lambda g: g[0])


def fragmentation_signal(min_k_baseline: int | None, min_k_coarse: int | None,
                         tokens_baseline: int | None, tokens_coarse: int | None, *,
                         k_drop: float = 0.30, token_rise: float = 0.10) -> bool:
    if not min_k_baseline or min_k_coarse is None:
        return False
    drop = (min_k_baseline - min_k_coarse) / min_k_baseline
    rise = 0.0 if not tokens_baseline else (tokens_coarse - tokens_baseline) / tokens_baseline
    return drop >= k_drop and rise <= token_rise


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _ratio_gap(baseline: int | None, oracle: int | None) -> float | None:
    if baseline is None or oracle is None:
        return None
    return (baseline - oracle) / baseline if baseline else 0.0


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #

def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _chunk_meta(chunks: list[dict]) -> dict[str, dict]:
    return {c["chunk_id"]: c for c in chunks}


# --------------------------------------------------------------------------- #
# Step -1: disagreement audit
# --------------------------------------------------------------------------- #

def audit_disagreements(results: dict, prepared: dict, support: dict[str, list[str]]) -> dict:
    """Classify each Validation V1 rubric-disagreement candidate fact."""
    prepared_by_id = {row["case_id"]: row for row in prepared["cases"]}
    entries: list[dict] = []
    for row in results["cases"]:
        case_id = row["case_id"]
        for strategy in ("always_v1", "frozen_adaptive"):
            fact_ids = row[strategy]["quality"].get("answered_without_mapped_evidence_fact_ids") or []
            if not fact_ids:
                continue
            route = STRATEGY_ROUTE.get(strategy) or prepared_by_id[case_id]["adaptive_decision"]
            selected = prepared_by_id[case_id]["variants"][route]["chunks"]
            selected_ids = {chunk["chunk_id"] for chunk in selected}
            answer = row[strategy]["generation"]["answer"]
            for fact_id in fact_ids:
                direct = support.get(fact_id, [])
                in_selected = sorted(set(direct) & selected_ids)
                excerpt_hits = [chunk["chunk_id"] for chunk in selected
                                if _excerpt_contained(fact_id, chunk["text"])]
                category, reason = _classify_audit_fact(
                    fact_id, direct, in_selected, excerpt_hits, answer)
                entries.append({"case_id": case_id, "strategy": strategy, "route": route,
                                "fact_id": fact_id, "category": category, "reason": reason,
                                "direct_chunk_ids": direct, "mapped_chunk_selected": in_selected,
                                "unmapped_excerpt_chunks": excerpt_hits})
    counts = Counter(entry["category"] for entry in entries)
    removed = sorted({entry["fact_id"] for entry in entries
                      if entry["category"] == "unresolved" and not entry["direct_chunk_ids"]})
    added: dict[str, list[str]] = {}
    for entry in entries:
        if entry["category"] == "missing_direct_mapping_candidate":
            added.setdefault(entry["fact_id"], [])
            added[entry["fact_id"]] = sorted(set(added[entry["fact_id"]]) |
                                             set(entry["unmapped_excerpt_chunks"]))
    unique_facts = sorted({entry["fact_id"] for entry in entries})
    return {
        "disagreement_events": len(entries),
        "unique_facts": unique_facts,
        "independent_facts": len({(e["case_id"], e["fact_id"]) for e in entries}),
        "category_counts": {name: counts.get(name, 0) for name in AUDIT_CATEGORIES},
        "missing_direct_mapping_candidates": added,
        "facts_removed_from_available": removed,
        "entries": entries,
        "method": "Deterministic frozen-mapping containment audit; no LLM re-judge.",
    }


def _excerpt_contained(fact_id: str, text: str) -> bool:
    fact = _FACT_TEXT.get(fact_id)
    if not fact:
        return False
    excerpt, context = fact
    normalized = _norm(text)
    return excerpt in normalized and (not context or context in normalized)


def _classify_audit_fact(fact_id: str, direct: list[str], in_selected: list[str],
                         excerpt_hits: list[str], answer: str) -> tuple[str, str]:
    if not direct:
        return "unresolved", "no frozen direct mapping found"
    if in_selected:
        return "existing_direct_mapping_sufficient", "mapped support was in supplied evidence"
    if excerpt_hits:
        return "missing_direct_mapping_candidate", "unmapped supplied chunk contains the source span"
    fact = _FACT_TEXT.get(fact_id)
    terms = _terms(fact[0]) if fact else set()
    trace = len(terms & _terms(answer)) / len(terms) if terms else 0.0
    if trace < CONFIG["audit_lexical_trace"]:
        return "judge_false_positive", "no lexical trace of the fact in the answer"
    return "existing_direct_mapping_sufficient", "frozen mapping valid; disagreement is selection/generation"


def _load_fact_text(rubric: dict) -> dict[str, tuple[str, str]]:
    table = {}
    for case in rubric["cases"]:
        for fact in case["facts"]:
            support = fact["support"][0]
            table[fact["fact_id"]] = (_norm(support["source_excerpt"]),
                                      _norm(support.get("context_excerpt", "")))
            _FACT_STATEMENT[fact["fact_id"]] = fact["statement"]
    return table


_FACT_TEXT: dict[str, tuple[str, str]] = {}
_FACT_STATEMENT: dict[str, str] = {}


# --------------------------------------------------------------------------- #
# Step 0: retrieval scopes
# --------------------------------------------------------------------------- #

def build_retrieval_cache(queries: dict) -> dict:
    """Recover the frozen candidate union and reranked Top20 per query (once)."""
    from eval.run_validation import _local_retriever
    from eval.run_validation import _runtime_fingerprints

    retriever, index = _local_retriever()
    tokens = {chunk.chunk_id: approx_tokens(chunk.text) for chunk in index.chunks}
    scopes = {}
    for case in queries["cases"]:
        query = case["query"]
        # One retrieval pass; the reranked order covers the whole candidate union.
        reranked = [item.chunk_id for item in retriever.search(query, top_k=10 ** 9)]
        scopes[case["case_id"]] = {"union": sorted(reranked), "reranked": reranked,
                                   "top20": reranked[:20]}
        print(f"Retrieved {case['case_id']}", flush=True)
    return {"fingerprints": _runtime_fingerprints(), "tokens": tokens, "scopes": scopes}


# --------------------------------------------------------------------------- #
# Step 0: per-case geometry
# --------------------------------------------------------------------------- #

def _cover_block(facts: list[dict], units: list[dict], tokens: dict[str, int]) -> dict:
    mapping = fact_units(facts, units)
    available = sum(1 for ids in mapping.values() if ids)
    min_k, chosen = min_cardinality_cover(mapping, require_all=False)
    min_tokens, _ = min_token_cover({f: u for f, u in mapping.items() if u},
                                    {unit["unit_id"]: unit["token_count"] for unit in units},
                                    require_all=False)
    return {"min_k": min_k, "min_tokens": min_tokens, "available_facts": available,
            "chosen_units": chosen, "unit_support": mapping}


def _prefix_status(prefix: list[str], union: list[str], facts: list[dict],
                   support: dict[str, list[str]], tokens: dict[str, int]) -> dict:
    prefix_set = set(prefix)
    union_set = set(union)
    covers = {fact["fact_id"]: set(support.get(fact["fact_id"], [])) for fact in facts}
    covered: set[str] = set()
    cumulative = 0
    for index, chunk_id in enumerate(prefix, 1):
        covered.update(fact_id for fact_id, support_ids in covers.items() if chunk_id in support_ids)
        cumulative += tokens.get(chunk_id, 0)
        if len(covered) == len(facts):
            return {"k": index, "tokens": cumulative, "complete": True, "reason": None}
    if any(support_ids and not support_ids & union_set for support_ids in covers.values()):
        reason = "candidate_ceiling"
    elif any(support_ids & union_set and not support_ids & prefix_set
             for support_ids in covers.values()):
        reason = "current_top20_truncation"
    else:
        reason = "other"
    return {"k": None, "tokens": None, "complete": False, "reason": reason}


def _dispersion(chosen_units: list[str], units: list[dict], facts: list[dict],
                support: dict[str, list[str]], chunk_meta: dict[str, dict],
                union: set[str]) -> dict:
    by_id = {unit["unit_id"]: unit for unit in units}
    docs, top_headings, exact_headings = set(), set(), set()
    for unit_id in chosen_units:
        unit = by_id.get(unit_id)
        if not unit:
            continue
        meta = chunk_meta.get(unit["chunk_ids"][0], {})
        docs.add(meta.get("source_path", unit.get("source_path", "")))
        heading = tuple(meta.get("heading_path") or ())
        top_headings.add(heading[0] if heading else "__document_root__")
        exact_headings.add(heading)
    fact_documents = {chunk_meta[c]["source_path"] for f in facts
                      for c in support.get(f["fact_id"], []) if c in chunk_meta and c in union}
    return {"documents": sorted(docs), "top_level_headings": sorted(top_headings),
            "exact_headings": len(exact_headings), "fact_documents": len(fact_documents)}


def _diagnose(row: dict) -> dict:
    flags = []
    if row["candidate_missing"] > 0:
        flags.append("candidate_ceiling")
    if row["strong_fragmentation"]:
        flags.append("fragmentation")
    if row["ranking_headroom"]["k"] or row["ranking_headroom"]["tokens"]:
        flags.append("ranking_selection_headroom")
    if row["intrinsic_breadth"]:
        flags.append("intrinsic_breadth")
    precedence = ["candidate_ceiling", "fragmentation", "ranking_selection_headroom",
                  "intrinsic_breadth"]
    primary = next((name for name in precedence if name in flags), "mixed")
    return {"primary": primary, "flags": flags,
            "secondary": [name for name in flags if name != primary]}


def geometry_for_case(case_row: dict, facts: list[dict], support: dict[str, list[str]],
                      tokens: dict[str, int], scope: dict, chunk_meta: dict[str, dict]) -> dict:
    union = [chunk_id for chunk_id in scope["union"] if chunk_id in chunk_meta]
    top20 = [chunk_id for chunk_id in scope["top20"] if chunk_id in chunk_meta]
    union_set = set(union)
    union_chunks = [chunk_meta[chunk_id] for chunk_id in union]
    top20_chunks = [chunk_meta[chunk_id] for chunk_id in top20]

    l0_units = build_level0_units(union_chunks)
    l1_units = build_local_windows(union_chunks, size=CONFIG["window_size"])
    l2_units = build_top1_subtrees(union_chunks)

    full = _cover_block(facts, l0_units, tokens)
    top = _cover_block(facts, build_level0_units(top20_chunks), tokens)
    l1 = _cover_block(facts, l1_units, tokens)
    l2 = _cover_block(facts, l2_units, tokens)

    v1_chunks = [chunk for chunk in case_row["variants"]["adaptive_prefix_v1"]["chunks"]]
    v1_k = len(v1_chunks)
    v1_tokens = sum(approx_tokens(chunk["text"]) for chunk in v1_chunks)
    v1_evidence = case_row["variants"]["adaptive_prefix_v1"]["evidence"]
    prefix = _prefix_status(top20, union, facts, support, tokens)

    reranked = [chunk_id for chunk_id in scope["reranked"] if chunk_id in chunk_meta]
    rank_of = {chunk_id: index for index, chunk_id in enumerate(reranked, 1)}
    v1_selected_ids = {chunk["chunk_id"] for chunk in v1_chunks}
    fact_ranks = []
    for fact in facts:
        gold = [chunk_id for chunk_id in support.get(fact["fact_id"], [])]
        available = [chunk_id for chunk_id in gold if chunk_id in union_set]
        if not available:
            fact_ranks.append({"fact_id": fact["fact_id"], "gold_chunk_ids": gold,
                               "union_rank": None, "top20_rank": None, "in_top5": False,
                               "in_v1_selected": False, "candidate_missing": True})
            continue
        best = min(rank_of[chunk_id] for chunk_id in available if chunk_id in rank_of)
        fact_ranks.append({"fact_id": fact["fact_id"], "gold_chunk_ids": available,
                           "union_rank": best,
                           "top20_rank": best if best <= 20 else None,
                           "in_top5": best <= 5,
                           "in_v1_selected": any(chunk_id in v1_selected_ids
                                                 for chunk_id in available),
                           "candidate_missing": False})
    ranks = [item["union_rank"] for item in fact_ranks if item["union_rank"] is not None]
    deepest_gold_rank = max(ranks) if ranks else None
    facts_outside_top5 = sum(1 for rank in ranks if rank > 5)

    fragmentation = {}
    for name, block in (("window_3", l1), ("top1_subtree", l2)):
        fragmentation[name] = {
            "min_k": block["min_k"],
            "min_tokens": block["min_tokens"],
            "delta_k": None if (full["min_k"] is None or block["min_k"] is None)
            else full["min_k"] - block["min_k"],
            "delta_tokens": None if (full["min_tokens"] is None or block["min_tokens"] is None)
            else block["min_tokens"] - full["min_tokens"],
            "strong": fragmentation_signal(full["min_k"], block["min_k"],
                                           full["min_tokens"], block["min_tokens"],
                                           k_drop=CONFIG["fragmentation_k_drop"],
                                           token_rise=CONFIG["fragmentation_token_rise"]),
        }
    strong_fragmentation = any(item["strong"] for item in fragmentation.values())

    groups = {fact["fact_id"]: support_groups(
                  [chunk_id for chunk_id in support.get(fact["fact_id"], []) if chunk_id in union_set],
                  chunk_meta, adjacency=CONFIG["overlap_group_adjacency"],
                  min_overlap_chars=CONFIG["overlap_group_min_chars"])
              for fact in facts}
    group_counts = {fact_id: len(value) for fact_id, value in groups.items()}
    sparse = sum(1 for count in group_counts.values() if count == 1)
    robust = sum(1 for count in group_counts.values() if count >= 2)
    candidate_missing = sum(1 for count in group_counts.values() if count == 0)

    dispersion = _dispersion(full["chosen_units"], l0_units, facts, support, chunk_meta, union_set)
    span = (len(dispersion["documents"]) >= 2 or len(dispersion["top_level_headings"]) >= 2)
    intrinsic = (full["min_k"] is not None and full["min_k"] >= CONFIG["high_min_cover_k"]
                 and not strong_fragmentation and span)

    k_saving = _ratio_gap(v1_k, full["min_k"])
    token_saving = _ratio_gap(v1_tokens, full["min_tokens"])
    ranking_headroom = {
        "k": bool(full["min_k"] is not None and full["min_k"] <= CONFIG["high_min_cover_k"]
                  and v1_k >= CONFIG["v1_deep_k"]),
        "tokens": bool(token_saving is not None and token_saving >= CONFIG["headroom_token_saving"]),
        "k_saving": k_saving, "token_saving": token_saving,
    }

    row = {
        "case_id": case_row["case_id"],
        "policy_family": case_row.get("policy_family"),
        "query_type": case_row.get("query_type"),
        "available_facts": full["available_facts"],
        "required_facts": len(facts),
        "candidate_missing": candidate_missing,
        "full_pool_min_k": full["min_k"], "full_pool_min_tokens": full["min_tokens"],
        "top20_min_k": top["min_k"], "top20_min_tokens": top["min_tokens"],
        "top20_available_facts": top["available_facts"],
        "v1_k": v1_k, "v1_tokens": v1_tokens,
        "v1_evidence_tokens_production": v1_evidence["evidence_tokens"],
        "v1_complete": bool(v1_evidence["fact_complete"]),
        "prefix_first_complete_k": prefix["k"], "prefix_first_complete_tokens": prefix["tokens"],
        "prefix_incomplete_reason": prefix["reason"],
        "sparse_support": sparse, "robust_support": robust,
        "sparse_support_pct": sparse / len(facts) if facts else 0.0,
        "candidate_ceiling": candidate_missing > 0,
        "deepest_gold_rank": deepest_gold_rank,
        "facts_outside_top5": facts_outside_top5,
        "gold_chunks_outside_top5": facts_outside_top5,
        "tail_facts": sum(1 for rank in ranks if 6 <= rank <= 20),
        "deep_tail_facts": sum(1 for rank in ranks if rank >= 11),
        "v1_expanded": v1_k > 5,
        "v1_expansion_recovered_facts": sum(1 for rank in ranks if 6 <= rank <= v1_k),
        "fact_ranks": fact_ranks,
        "doc_spread": len(dispersion["documents"]),
        "heading_spread": len(dispersion["top_level_headings"]),
        "exact_heading_spread": dispersion["exact_headings"],
        "fragmentation": fragmentation,
        "strong_fragmentation": strong_fragmentation,
        "intrinsic_breadth": intrinsic,
        "ranking_headroom": ranking_headroom,
        "k_saving_vs_v1": k_saving, "token_saving_vs_v1": token_saving,
        "support_groups": group_counts,
    }
    row["diagnosis"] = _diagnose(row)
    return row


# --------------------------------------------------------------------------- #
# Aggregation and reporting
# --------------------------------------------------------------------------- #

def _distribution(values: list) -> dict:
    data = sorted(value for value in values if value is not None)
    if not data:
        return {"n": 0, "median": None, "mean": None, "min": None, "max": None}
    return {"n": len(data), "median": median(data), "mean": mean(data),
            "min": data[0], "max": data[-1]}


def _aggregate(rows: list[dict], audit: dict) -> dict:
    k_gaps = [row["v1_k"] - row["full_pool_min_k"] for row in rows
              if row["full_pool_min_k"] is not None]
    token_gaps = [row["v1_tokens"] - row["full_pool_min_tokens"] for row in rows
                  if row["full_pool_min_tokens"] is not None]
    complete_cases = sum(1 for row in rows if row["full_pool_min_k"] is not None
                         and row["candidate_missing"] == 0)
    diagnoses = Counter(row["diagnosis"]["primary"] for row in rows)
    flag_counts = Counter(flag for row in rows for flag in row["diagnosis"]["flags"])
    sparse = sum(row["sparse_support"] for row in rows)
    robust = sum(row["robust_support"] for row in rows)
    missing = sum(row["candidate_missing"] for row in rows)
    total_facts = sum(row["required_facts"] for row in rows)
    frag_cases = [row["case_id"] for row in rows if row["strong_fragmentation"]]
    rank_cases = [row["case_id"] for row in rows
                  if row["diagnosis"]["flags"].count("ranking_selection_headroom")]
    intrinsic_cases = [row["case_id"] for row in rows if row["intrinsic_breadth"]]
    return {
        "case_count": len(rows),
        "required_fact_count": total_facts,
        "k_gap_v1_minus_oracle": _distribution(k_gaps),
        "token_gap_v1_minus_oracle": _distribution(token_gaps),
        "full_pool_min_k": _distribution([row["full_pool_min_k"] for row in rows]),
        "full_pool_min_tokens": _distribution([row["full_pool_min_tokens"] for row in rows]),
        "v1_k": _distribution([row["v1_k"] for row in rows]),
        "v1_tokens": _distribution([row["v1_tokens"] for row in rows]),
        "oracle_complete_cases": complete_cases,
        "top20_available_facts": sum(row["top20_available_facts"] for row in rows),
        "diagnosis_distribution": dict(diagnoses),
        "flag_counts": dict(flag_counts),
        "support_geometry": {"candidate_missing": missing, "sparse": sparse, "robust": robust},
        "sparse_fact_pct": sparse / total_facts if total_facts else 0.0,
        "strong_fragmentation_cases": frag_cases,
        "ranking_headroom_cases": rank_cases,
        "intrinsic_breadth_cases": intrinsic_cases,
        "oracle_le5_v1_ge10": sum(1 for row in rows if row["full_pool_min_k"] is not None
                                  and row["full_pool_min_k"] <= 5 and row["v1_k"] >= 10),
        "oracle_le6_v1_ge10": sum(1 for row in rows if row["full_pool_min_k"] is not None
                                  and row["full_pool_min_k"] <= 6 and row["v1_k"] >= 10),
        "token_footprint_cases": sum(1 for row in rows if row["token_saving_vs_v1"] is not None
                                     and row["token_saving_vs_v1"] >= CONFIG["headroom_token_saving"]),
        "audit": {name: audit["category_counts"][name] for name in AUDIT_CATEGORIES},
        "tail_baseline": _tail_baseline(rows),
    }


def _tail_baseline(rows: list[dict]) -> dict:
    """Current reranker tail geometry over the single-support gold mapping. Units: facts/cases."""
    available, missing = [], []
    for row in rows:
        for item in row["fact_ranks"]:
            record = {"case_id": row["case_id"], "policy_family": row["policy_family"],
                      "query_type": row["query_type"], "fact_id": item["fact_id"],
                      "rank": item["union_rank"]}
            (missing if item["candidate_missing"] else available).append(record)
    ranks = [record["rank"] for record in available]
    buckets = {name: sum(1 for rank in ranks if low <= rank <= high)
               for name, low, high in _RANK_BUCKETS}
    buckets["rank_gt_20"] = sum(1 for rank in ranks if rank > 20)
    buckets["candidate_missing"] = len(missing)
    deepest = [row["deepest_gold_rank"] for row in rows if row["deepest_gold_rank"] is not None]
    tail = [record for record in available if 6 <= record["rank"] <= 20]
    deep_tail = [record for record in available if record["rank"] >= 11]
    affected = [row["case_id"] for row in rows if row["facts_outside_top5"] > 0]
    return {
        "unit": "facts",
        "fact_count_total": len(available) + len(missing),
        "top1": sum(1 for rank in ranks if rank == 1),
        "top5": sum(1 for rank in ranks if rank <= 5),
        "buckets": buckets,
        "exact_rank_histogram": {str(k): v for k, v in sorted(Counter(ranks).items())},
        "tail_facts_rank_6_20": len(tail),
        "deep_tail_facts_rank_ge_11": len(deep_tail),
        "facts_outside_top5": sum(1 for rank in ranks if rank > 5),
        "affected_cases_outside_top5": affected,
        "affected_case_count_outside_top5": len(affected),
        "case_with_candidate_missing": [row["case_id"] for row in rows if row["candidate_ceiling"]],
        "deepest_gold_rank": _distribution(deepest),
        "cases_deepest_gt_5": sum(1 for value in deepest if value > 5),
        "cases_deepest_gt_8": sum(1 for value in deepest if value > 8),
        "cases_deepest_gt_10": sum(1 for value in deepest if value > 10),
        "v1_expansion_cases": sum(1 for row in rows if row.get("v1_expanded")),
        "v1_expansion_recovered_facts": sum(row.get("v1_expansion_recovered_facts", 0)
                                            for row in rows),
        "tail_policy_families": dict(Counter(record["policy_family"] for record in tail)),
        "tail_query_types": dict(Counter(record["query_type"] for record in tail)),
    }


def _fact_text_trace(fact_id: str, answer: str) -> float:
    """Diagnostic lexical overlap between the fact statement and the saved answer."""
    statement = _FACT_STATEMENT.get(fact_id)
    if not statement:
        return 0.0
    terms = _terms(statement)
    if not terms:
        return 0.0
    return len(terms & _terms(answer)) / len(terms)


def _attribute_gap_fact(fact_id: str, judge_fact: dict, diagnosis: dict | None,
                        answer: str, audit_facts: set[str]) -> tuple[str, str]:
    """Deterministic attribution from existing labels only; never a new adjudication."""
    if fact_id in audit_facts:
        return "judge_rubric_disagreement", "listed in the Step -1 disagreement audit"
    status = judge_fact.get("status")
    citation = judge_fact.get("citation_status")
    cause = (diagnosis or {}).get("cause")
    # Frozen pipeline cause is authoritative; the lexical trace stays diagnostic-only.
    if cause == "synthesis_error":
        return "partial_synthesis", "frozen pipeline cause=synthesis_error"
    if cause == "utilization_miss":
        return "utilization_miss", "frozen pipeline cause=utilization_miss"
    if cause in {"selection_miss", "candidate_miss"}:
        return "other_or_unclear", f"frozen pipeline cause={cause} under evidence-complete"
    if cause == "unresolved":
        return "other_or_unclear", "frozen pipeline cause=unresolved"
    if status == "covered" and citation != "supported":
        return "citation_grounding_issue", f"answer covered but citation_status={citation}"
    if status == "incorrect":
        return "partial_synthesis", "judge status=incorrect"
    if status == "uncertain":
        return "other_or_unclear", "judge reported uncertainty"
    if status == "missing":
        return "utilization_miss", "judge status=missing"
    return "other_or_unclear", "insufficient existing signal"


def _query_tags(query: str, query_type: str | None) -> dict:
    return {"query_type": query_type,
            "enumeration_query": bool(_ENUM_MARKER.search(query)),
            "multi_condition_query": bool(_CONDITION_MARKER.search(query))}


def _intra_chunk_position(fact_id: str, chunk_text: str) -> tuple[str, float | None]:
    fact = _FACT_TEXT.get(fact_id)
    normalized = _norm(chunk_text)
    if not fact or not normalized:
        return "unknown", None
    index = normalized.find(fact[0])
    if index < 0:
        return "unknown", None
    ratio = (index + len(fact[0]) / 2) / len(normalized)
    third = ("front_third" if ratio < 1 / 3 else
             "back_third" if ratio >= 2 / 3 else "middle_third")
    return third, round(ratio, 3)


def _utilization_pattern(row: dict, fact_id: str, support: dict, chunk_meta: dict) -> dict:
    quality = row["always_v1"]["quality"]
    selected = row["always_v1"]["selected_chunk_ids"]
    total = len(selected)
    gold = set(support.get(fact_id, []))
    position = next((index for index, chunk_id in enumerate(selected, 1)
                     if chunk_id in gold), None)
    percentile = ((position - 1) / (total - 1)) if (position and total > 1) else 0.0
    gold_chunk = next((chunk_id for chunk_id in selected if chunk_id in gold), None)
    third, in_chunk_ratio = ("unknown", None)
    if gold_chunk:
        third, in_chunk_ratio = _intra_chunk_position(fact_id, chunk_meta[gold_chunk]["text"])
    evidence_tokens = row["always_v1"].get("evidence_tokens")
    answer = row["always_v1"]["generation"]["answer"]
    answer_words = len(answer.split())
    required = quality["required_fact_count"]
    covered = quality["covered_count"]
    fact_ids = [entry["fact_id"] for entry in row["always_v1"]["judge"]["facts"]]
    tags = _query_tags(row["query"], row.get("query_type"))
    distinct_gold = {next(iter(support.get(f, [])), None) for f in fact_ids}
    single_dense = len(distinct_gold - {None}) == 1
    mapped_selected = {chunk_id for fact in fact_ids for chunk_id in support.get(fact, [])
                       if chunk_id in set(selected)}
    compression = (answer_words / evidence_tokens) if evidence_tokens else None
    flags = []
    if position is not None and percentile >= CONFIG["util_late_evidence_percentile"]:
        flags.append("late_evidence_position")
    if third == "back_third":
        flags.append("late_in_chunk")
    if tags["enumeration_query"] or tags["multi_condition_query"]:
        flags.append("enumeration_query")
    if total >= CONFIG["util_many_selected_chunks_k"]:
        flags.append("many_selected_chunks")
    if single_dense:
        flags.append("single_dense_gold_chunk")
    if compression is not None and compression * 1000 < CONFIG["util_compression_words_per_1k"]:
        flags.append("high_evidence_to_answer_compression")
    if not flags:
        flags.append("no_clear_pattern")
    return {
        "evidence_position": position, "evidence_percentile": round(percentile, 3),
        "evidence_first_half": percentile < CONFIG["util_late_evidence_percentile"],
        "intra_chunk_position": third, "intra_chunk_ratio": in_chunk_ratio,
        "query_tags": tags, "fact_type_source": "not_in_frozen_rubric",
        "answer_words": answer_words, "answer_tokens": approx_tokens(answer),
        "selected_k": total, "evidence_tokens": evidence_tokens,
        "required_facts": required, "answer_covered_facts": covered,
        "compression_words_per_1k": round(compression * 1000, 2) if compression is not None else None,
        "required_facts_per_selected_chunk": round(required / total, 3) if total else None,
        "required_facts_per_1k_evidence_tokens": round(required / (evidence_tokens / 1000), 3)
        if evidence_tokens else None,
        "single_dense_gold_chunk": single_dense,
        "selected_chunks_mapped": len(mapped_selected),
        "selected_chunks_unmapped": total - len(mapped_selected),
        "pattern_flags": flags,
    }


def _case_feature(row: dict, median_k: float, median_words: float) -> dict:
    selected = row["always_v1"]["selected_chunk_ids"]
    words = len(row["always_v1"]["generation"]["answer"].split())
    tags = _query_tags(row["query"], row.get("query_type"))
    return {"high_k": len(selected) >= median_k,
            "enumeration": tags["enumeration_query"],
            "short_answer": words < median_words,
            "selected_k": len(selected), "answer_words": words}


def _utilization_pattern_summary(gap_cases: list[dict], gap_rows: list[dict],
                                 converted_rows: list[dict]) -> dict:
    facts = [fact for case in gap_cases for fact in case["grounded_missing_facts"]]
    flag_counts: Counter = Counter()
    for fact in facts:
        for flag in fact["pattern"]["pattern_flags"]:
            flag_counts[flag] += 1
    total = len(facts)
    back = flag_counts.get("late_evidence_position", 0)
    chunk_back = flag_counts.get("late_in_chunk", 0)

    all_k = [fact["pattern"]["selected_k"] for fact in facts] + \
            [len(row["always_v1"]["selected_chunk_ids"]) for row in converted_rows]
    all_words = [fact["pattern"]["answer_words"] for fact in facts] + \
                [len(row["always_v1"]["generation"]["answer"].split()) for row in converted_rows]
    median_k = median(all_k) if all_k else 0
    median_words = median(all_words) if all_words else 0
    gap_features = [_case_feature(row, median_k, median_words) for row in gap_rows]
    converted_features = [_case_feature(row, median_k, median_words) for row in converted_rows]
    gap_rates = {name: (sum(f[name] for f in gap_features) / len(gap_features)
                        if gap_features else 0.0)
                 for name in ("high_k", "enumeration", "short_answer")}
    converted_rates = {name: (sum(f[name] for f in converted_features) / len(converted_features)
                              if converted_features else 0.0)
                       for name in ("high_k", "enumeration", "short_answer")}
    discriminative = {name: round(gap_rates[name] - converted_rates[name], 3)
                      for name in ("high_k", "enumeration", "short_answer")}
    elevated = [name for name, delta in discriminative.items() if delta >= 0.20]
    if back or chunk_back:
        verdict = "CLEAR GENERATION PATTERN"
    elif elevated:
        verdict = "MIXED GENERATION PATTERN"
    elif flag_counts.get("high_evidence_to_answer_compression", 0) >= max(1, total // 2):
        verdict = "MIXED GENERATION PATTERN"
    else:
        verdict = "NO DOMINANT PATTERN"
    return {
        "unit": "facts",
        "facts_analyzed": total,
        "flag_counts": dict(flag_counts),
        "gap_case_feature_rates": {k: round(v, 3) for k, v in gap_rates.items()},
        "converted_case_feature_rates": {k: round(v, 3) for k, v in converted_rates.items()},
        "feature_rate_delta_gap_minus_converted": discriminative,
        "discriminative_features": elevated,
        "text": {
            "concentrated_in_evidence_back_half": back,
            "concentrated_in_chunk_back_third": chunk_back,
            "list_or_multi_condition_query": flag_counts.get("enumeration_query", 0),
            "high_k_selected_cases": flag_counts.get("many_selected_chunks", 0),
            "single_dense_gold_chunk": flag_counts.get("single_dense_gold_chunk", 0),
            "high_evidence_to_answer_compression": flag_counts.get(
                "high_evidence_to_answer_compression", 0),
        },
        "verdict": verdict,
        "thresholds": {key: CONFIG[key] for key in (
            "util_late_evidence_percentile", "util_many_selected_chunks_k",
            "util_compression_words_per_1k")},
    }


def _answer_conversion_gap(results: dict, support: dict, audit: dict,
                           chunk_meta: dict | None = None) -> dict:
    audit_facts = {entry["fact_id"] for entry in audit["entries"]}
    chunk_meta = chunk_meta or {}
    evidence_complete, gap_cases, gap_rows, converted_rows = [], [], [], []
    fact_total = fact_grounded = 0
    for row in results["cases"]:
        quality = row["always_v1"]["quality"]
        if not row["always_v1_evidence"]["fact_complete"]:
            continue
        evidence_complete.append(row["case_id"])
        fact_total += quality["required_fact_count"]
        fact_grounded += quality["grounded_covered_count"]
        if quality["grounded_fact_complete"]:
            converted_rows.append(row)
        else:
            gap_rows.append(row)
            gap_cases.append(_gap_case(row, audit_facts, support, chunk_meta))
    fact_primaries = Counter(fact["primary"] for case in gap_cases
                             for fact in case["grounded_missing_facts"])
    case_primaries = Counter(case["primary"] for case in gap_cases)
    n_cases = len(evidence_complete)
    return {
        "units": {"case": "one Validation V1 query", "fact": "one required atomic fact",
                  "claim": "one answer sentence clause; used as context only"},
        "evidence_complete_cases": n_cases,
        "grounded_complete_among_evidence_complete": n_cases - len(gap_cases),
        "conversion_rate_cases": (n_cases - len(gap_cases)) / n_cases if n_cases else None,
        "gap_case_count": len(gap_cases),
        "facts_in_evidence_complete_cases": fact_total,
        "grounded_covered_facts_in_evidence_complete": fact_grounded,
        "conversion_rate_facts": fact_grounded / fact_total if fact_total else None,
        "attribution_unit": "facts",
        "attribution_fact_counts": {name: fact_primaries.get(name, 0)
                                    for name in GAP_CATEGORIES},
        "attribution_case_primary_counts": {name: case_primaries.get(name, 0)
                                            for name in GAP_CATEGORIES},
        "claim_level_context": {
            "note": "claim-level grounding/citation diagnoses are a different unit than facts",
            "citation_error_claims": sum(1 for row in results["cases"]
                                         for d in row["always_v1"]["claim_diagnosis"]
                                         if d["cause"] == "citation_error"),
            "grounding_review_claims": sum(1 for row in results["cases"]
                                           for d in row["always_v1"]["claim_diagnosis"]
                                           if d["cause"] == "grounding_review"),
        },
        "method": "Deterministic attribution over existing frozen labels; no re-judge.",
        "utilization_pattern_summary": _utilization_pattern_summary(gap_cases, gap_rows,
                                                                    converted_rows),
        "cases": gap_cases,
    }


def _gap_case(row: dict, audit_facts: set[str], support: dict,
              chunk_meta: dict) -> dict:
    quality = row["always_v1"]["quality"]
    diagnosis = {d["fact_id"]: d for d in row["always_v1"]["pipeline_diagnosis"]}
    judge = {j["fact_id"]: j for j in row["always_v1"]["judge"]["facts"]}
    answer = row["always_v1"]["generation"]["answer"]
    covered = set(quality["covered_fact_ids"])
    facts = []
    for fact_id in quality["grounded_missing_fact_ids"]:
        judge_fact = judge.get(fact_id, {})
        primary, reason = _attribute_gap_fact(fact_id, judge_fact, diagnosis.get(fact_id),
                                              answer, audit_facts)
        facts.append({"fact_id": fact_id, "answer_status": judge_fact.get("status"),
                      "citation_status": judge_fact.get("citation_status"),
                      "pipeline_cause": (diagnosis.get(fact_id) or {}).get("cause"),
                      "answer_covered": fact_id in covered,
                      "primary": primary, "reason": reason,
                      "pattern": _utilization_pattern(row, fact_id, support, chunk_meta),
                      "text_trace_diagnostic": round(_fact_text_trace(fact_id, answer), 3)})
    primaries = [fact["primary"] for fact in facts]
    primary = Counter(primaries).most_common(1)[0][0] if primaries else None
    return {"case_id": row["case_id"], "policy_family": row["policy_family"],
            "query_type": row["query_type"], "required_facts": quality["required_fact_count"],
            "grounded_covered_facts": quality["grounded_covered_count"],
            "grounded_missing_facts": facts, "primary": primary,
            "secondary": sorted(set(primaries) - {primary}),
            "claim_diagnosis_causes": [d["cause"] for d in row["always_v1"]["claim_diagnosis"]]}


def _decide(global_stats: dict) -> dict:
    ranking = len(global_stats["ranking_headroom_cases"])
    fragmentation = len(global_stats["strong_fragmentation_cases"])
    if fragmentation > ranking:
        decision = "INVESTIGATE REPRESENTATION/CHUNKING FIRST"
        reason = (f"{fragmentation} cases show strong fragmentation vs {ranking} with ranking "
                  "headroom; coarser units recover K without token growth on a majority.")
    elif ranking > fragmentation:
        decision = "PROCEED TO STRONGER RERANKER A/B"
        reason = (f"{ranking} cases have small oracle min-cover but deep V1 selection vs "
                  f"{fragmentation} fragmentation cases; the recoverable headroom looks rankable.")
    elif ranking == fragmentation == 0:
        decision = "MIXED — STRATIFY BEFORE RERANKER A/B"
        reason = "No dominant geometry signal; inspect per-case distribution before intervening."
    else:
        decision = "MIXED — STRATIFY BEFORE RERANKER A/B"
        reason = (f"ranking headroom cases = {ranking}, fragmentation cases = {fragmentation}; "
                  "intervene per stratum rather than globally.")
    return {"decision": decision, "reason": reason,
            "ranking_headroom_cases": ranking, "fragmentation_cases": fragmentation,
            "intrinsic_breadth_cases": len(global_stats["intrinsic_breadth_cases"])}


def _representation_rows(result: dict) -> list[str]:
    units = result["representation"]["global_units"]
    rows = ["| level | units | unit tok p50 | unit tok p90 | median min K | median min tokens |",
            "|---|---:|---:|---:|---:|---:|"]
    for key, unit_key, label in (("level0", "level0_current", "L0 current"),
                                 ("window_3", "level1_window3", "L1 3-window"),
                                 ("top1_subtree", "level2_top1_subtree", "L2 top-1 subtree")):
        rows.append(f"| {label} | {units[unit_key]['unit_count']} | {units[unit_key]['token_p50']} | "
                    f"{units[unit_key]['token_p90']} | {result['representation'][key]['median_min_k']} | "
                    f"{result['representation'][key]['median_min_tokens']} |")
    return rows


def _tail_rows(result: dict) -> list[str]:
    tail = result["global"]["tail_baseline"]
    deepest = tail["deepest_gold_rank"]
    return [
        f"- gold-rank histogram (facts): {tail['exact_rank_histogram']}",
        f"- top1: {tail['top1']}; top5: {tail['top5']}; buckets: {tail['buckets']}",
        f"- tail facts (rank 6-20): {tail['tail_facts_rank_6_20']}; "
        f"deep-tail (rank>=11): {tail['deep_tail_facts_rank_ge_11']}; "
        f"outside top5: {tail['facts_outside_top5']}",
        f"- affected cases outside top5: {tail['affected_case_count_outside_top5']} "
        f"({', '.join(tail['affected_cases_outside_top5'])})",
        f"- deepest gold rank: median {deepest['median']}, mean {deepest['mean']}, max {deepest['max']}",
        f"- cases deepest>5: {tail['cases_deepest_gt_5']}; >8: {tail['cases_deepest_gt_8']}; "
        f">10: {tail['cases_deepest_gt_10']}",
        f"- V1 expansion cases: {tail['v1_expansion_cases']}; "
        f"expansion-recovered facts: {tail['v1_expansion_recovered_facts']}",
        f"- tail policy families: {tail['tail_policy_families']}",
        f"- tail query types: {tail['tail_query_types']}",
    ]


def _gap_rows(result: dict) -> list[str]:
    gap = result["answer_conversion_gap"]
    rows = [
        f"- evidence-complete cases: {gap['evidence_complete_cases']}; "
        f"grounded-complete among them: {gap['grounded_complete_among_evidence_complete']}; "
        f"conversion rate (cases): {gap['conversion_rate_cases']:.3f}",
        f"- gap cases: {gap['gap_case_count']}; fact conversion rate: {gap['conversion_rate_facts']:.3f}",
        f"- attribution (facts): {gap['attribution_fact_counts']}",
        f"- attribution (case primary): {gap['attribution_case_primary_counts']}",
        f"- claim-level context: {gap['claim_level_context']}",
        f"- utilization pattern verdict: {gap['utilization_pattern_summary']['verdict']}",
        f"- pattern flags: {gap['utilization_pattern_summary']['flag_counts']}",
    ]
    for case in gap["cases"]:
        rows.append(f"- {case['case_id']} [{case['policy_family']}] primary={case['primary']} "
                    f"secondary={case['secondary']} missing_facts={[f['fact_id'] for f in case['grounded_missing_facts']]}")
        for fact in case["grounded_missing_facts"]:
            pattern = fact["pattern"]
            rows.append(f"    - {fact['fact_id']} pos={pattern['evidence_position']}/{pattern['selected_k']} "
                        f"({pattern['evidence_percentile']}) intra={pattern['intra_chunk_position']} "
                        f"flags={pattern['pattern_flags']} ev_tokens={pattern['evidence_tokens']} "
                        f"ans_words={pattern['answer_words']} comp/1k={pattern['compression_words_per_1k']}")
    return rows


def _render_summary(result: dict) -> str:
    stats = result["global"]
    decision = result["decision"]
    audit = result["audit"]
    lines = ["# Evidence Geometry Diagnostic (Step -1 + Step 0)", "",
             "Offline, gold-aware, read-only over the frozen Validation V1 benchmark.",
             "No generation, no judge, no network.", "",
             "## A. Step -1 Audit",
             f"- disagreement events: {audit['disagreement_events']} "
             f"({len(audit['unique_facts'])} unique facts)",
             f"- categories: {audit['category_counts']}",
             f"- missing mapping candidates: {len(audit['missing_direct_mapping_candidates'])}",
             f"- facts removed from available: {audit['facts_removed_from_available']}", "",
             "## B. Candidate Geometry",
             f"- full-union available coverage: {stats['required_fact_count'] - stats['support_geometry']['candidate_missing']}"
             f"/{stats['required_fact_count']}",
             f"- reranked-Top20 available coverage: {stats['top20_available_facts']}/{stats['required_fact_count']}",
             f"- candidate-missing facts: {stats['support_geometry']['candidate_missing']}",
             f"- oracle-complete cases (full union): {stats['oracle_complete_cases']}/{stats['case_count']}",
             "", "## C. Oracle Minimum (full union)",
             f"- min K: median {stats['full_pool_min_k']['median']}, "
             f"mean {stats['full_pool_min_k']['mean']}, "
             f"min {stats['full_pool_min_k']['min']}, max {stats['full_pool_min_k']['max']}",
             f"- min tokens: median {stats['full_pool_min_tokens']['median']}, "
             f"mean {stats['full_pool_min_tokens']['mean']}",
             "", "## D. V1 Gap",
             f"- median K gap (V1 - oracle): {stats['k_gap_v1_minus_oracle']['median']}",
             f"- median token gap (V1 - oracle): {stats['token_gap_v1_minus_oracle']['median']}",
             f"- oracle <=5 & V1 >=10: {stats['oracle_le5_v1_ge10']} cases",
             f"- oracle <=6 & V1 >=10: {stats['oracle_le6_v1_ge10']} cases",
             "", "## E. Representation Counterfactual",
             *_representation_rows(result),
             f"- strong fragmentation cases: {len(stats['strong_fragmentation_cases'])} "
             f"({', '.join(stats['strong_fragmentation_cases'])})",
             "", "## F. Support Geometry",
             f"- candidate-missing: {stats['support_geometry']['candidate_missing']}",
             f"- sparse (1 group): {stats['support_geometry']['sparse']}",
             f"- robust (>=2 groups): {stats['support_geometry']['robust']}",
             f"- sparse fact share: {stats['sparse_fact_pct']:.1%}",
             "", "## G. Diagnosis",
             f"- distribution: {stats['diagnosis_distribution']}",
             f"- cases carrying ranking headroom flag: {len(stats['ranking_headroom_cases'])}",
             f"- primary ranking/selection headroom cases: {stats['diagnosis_distribution'].get('ranking_selection_headroom', 0)}",
             f"- intrinsic breadth cases: {len(stats['intrinsic_breadth_cases'])}",
             f"- strong fragmentation cases: {len(stats['strong_fragmentation_cases'])}",
             "", "## H. Sensitivity",
             f"- {result['sensitivity']['verdict']}",
             "", "## Tail Ranking Baseline", *_tail_rows(result),
             "", "## Answer Conversion Gap", *_gap_rows(result),
             "", "## I. Decision", f"### {decision['decision']}", f"{decision['reason']}", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def _load_retrieval(queries: dict, refresh: bool) -> dict:
    if OUTPUT.exists() and not refresh:
        try:
            cached = _json(OUTPUT).get("retrieval_cache")
        except (ValueError, KeyError):
            cached = None
        if cached and cached.get("scopes") and all(
                "reranked" in scope for scope in cached["scopes"].values()):
            return cached
    return build_retrieval_cache(queries)


def analyze(*, refresh: bool = False, write: bool = True) -> dict:
    global _FACT_TEXT
    metadata = _json(METADATA)
    rubric = _json(RUBRIC)
    queries = _json(QUERIES)
    prepared = _json(PREPARED)
    results = _json(RESULTS)
    index = _json(INDEX)
    chunks = index["chunks"]
    chunk_meta = _chunk_meta(chunks)
    _FACT_TEXT = _load_fact_text(rubric)

    from eval.run_validation import direct_support_map
    support = direct_support_map(rubric, chunks)
    expected = metadata["dataset"]["required_fact_count"]
    if len(support) != expected:
        raise ValueError(f"support map has {len(support)} facts, expected {expected}")

    retrieval = _load_retrieval(queries, refresh)
    tokens = retrieval["tokens"]
    prepared_by_id = {row["case_id"]: row for row in prepared["cases"]}

    audit = audit_disagreements(results, prepared, support)
    _write_audit(audit, metadata, write)

    for row in prepared["cases"]:
        case_id = row["case_id"]
        if case_id not in retrieval["scopes"]:
            raise ValueError(f"missing retrieval scope for {case_id}")

    rows = [geometry_for_case(prepared_by_id[case["case_id"]], prepared_by_id[case["case_id"]]["facts"],
                              support, tokens, retrieval["scopes"][case["case_id"]], chunk_meta)
            for case in queries["cases"]]

    stats = _aggregate(rows, audit)
    representation = {
        "level0": _representation_summary(rows, "full_pool_min_k", "full_pool_min_tokens"),
        "window_3": _representation_summary(rows, None, None, key="window_3"),
        "top1_subtree": _representation_summary(rows, None, None, key="top1_subtree"),
        "config": {key: CONFIG[key] for key in (
            "window_size", "overlap_merge_max_chars", "overlap_group_min_chars",
            "fragmentation_k_drop", "fragmentation_token_rise")},
        "note": "Representation units are built from each case's frozen candidate union.",
        "global_units": _global_representation(chunks),
    }
    sensitivity = _sensitivity(audit, stats)
    decision = _decide(stats)
    answer_gap = _answer_conversion_gap(results, support, audit, chunk_meta)

    result = {
        "schema_version": 1,
        "name": "Evidence geometry diagnostic (Step -1 + Step 0)",
        "status": "diagnostic",
        "provenance": {
            "rubric_sha256": _sha256(RUBRIC),
            "queries_sha256": _sha256(QUERIES),
            "index_sha256": _sha256(INDEX),
            "post_hoc": "Analysis layer only; frozen benchmark and historical results untouched.",
        },
        "config": CONFIG,
        "audit": audit,
        "global": stats,
        "representation": representation,
        "sensitivity": sensitivity,
        "decision": decision,
        "answer_conversion_gap": answer_gap,
        "cases": rows,
        "retrieval_cache": retrieval,
    }
    if write:
        _write_outputs(result)
        _write_gap(answer_gap)
    return result


def _global_representation(chunks: list[dict]) -> dict:
    levels = {
        "level0_current": build_level0_units(chunks),
        "level1_window3": build_local_windows(chunks, size=CONFIG["window_size"]),
        "level2_top1_subtree": build_top1_subtrees(chunks),
    }
    summary = {}
    for name, units in levels.items():
        tokens = sorted(unit["token_count"] for unit in units)
        count = len(tokens)
        summary[name] = {"unit_count": count,
                         "token_p50": tokens[count // 2] if count else None,
                         "token_p90": tokens[int(count * 0.9)] if count else None,
                         "token_mean": mean(tokens) if count else None}
    return summary


def _representation_summary(rows: list[dict], k_field: str | None, token_field: str | None,
                            *, key: str | None = None) -> dict:
    if key:
        ks = [row["fragmentation"][key]["min_k"] for row in rows]
        ts = [row["fragmentation"][key]["min_tokens"] for row in rows]
    else:
        ks = [row[k_field] for row in rows]
        ts = [row[token_field] for row in rows]
    return {"median_min_k": _distribution(ks)["median"],
            "median_min_tokens": _distribution(ts)["median"]}


def _sensitivity(audit: dict, stats: dict) -> dict:
    changed = bool(audit["facts_removed_from_available"]) or bool(audit["missing_direct_mapping_candidates"])
    if changed:
        return {"verdict": "audit adjustment changes the available fact set; rerun sensitivity",
                "available_fact_delta": audit["facts_removed_from_available"],
                "added_mappings": audit["missing_direct_mapping_candidates"]}
    return {"verdict": "directionally robust to audit adjustment",
            "available_fact_delta": [], "added_mappings": {},
            "note": "No disagreement fact required a mapping change; frozen and adjusted runs coincide."}


def _write_audit(audit: dict, metadata: dict, write: bool) -> None:
    if not write:
        return
    payload = {"schema_version": 1, "name": "Validation V1 rubric-disagreement audit",
               "status": "post-hoc diagnostic",
               "role": "sensitivity analysis layer; does not overwrite the frozen rubric",
               "rubric_sha256": _sha256(RUBRIC), **audit}
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_outputs(result: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMMARY.write_text(_render_summary(result), encoding="utf-8")


def _write_gap(gap: dict) -> None:
    GAP.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "name": "Evidence-complete but answer-incomplete gap",
               "status": "post-hoc diagnostic",
               "role": "offline attribution over existing labels; no re-judge, no generation",
               "rubric_sha256": _sha256(RUBRIC),
               "frozen_results_sha256": _sha256(RESULTS), **gap}
    GAP.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="rebuild the cached retrieval scopes with the local retriever")
    args = parser.parse_args(argv)
    result = analyze(refresh=args.refresh)
    print(json.dumps({"decision": result["decision"]["decision"],
                      "diagnosis": result["global"]["diagnosis_distribution"],
                      "research_summary": result["representation"]["level0"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
