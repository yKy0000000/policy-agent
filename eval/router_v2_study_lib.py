"""Router V2 evidence-selection study library.

EXPLORATORY MECHANISM STUDY. This module reuses the frozen Router V1 artifacts
(raw candidate pools, shared rewrites, subqueries, per-stream reranked lists),
plus frozen local stacks (MiniLM cross-encoder, MiniLM sentence embeddings), to
compare evidence-selection policies under a fixed Top-5 budget.

Runtime-legal policies never read required-aspect truth. Oracle functions do,
are analysis-only, and must never be presented as runtime methods.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STUDY_DIR = PROJECT_ROOT / "eval" / "results" / "router_v2_selection_study"

RAW_PATH = PROJECT_ROOT / "eval" / "results" / "router_v1" / "raw" / "router_v1_raw_results.json"
TRUTH_PATH = PROJECT_ROOT / "eval" / "router_v1_required_aspects.json"
BENCH_PATH = PROJECT_ROOT / "eval" / "router_benchmark_v1.json"
LEXICAL_INDEX_PATH = PROJECT_ROOT / "cache" / "policy_index.json"
SEMANTIC_INDEX_PATH = PROJECT_ROOT / "cache" / "semantic_index.json"
SEMANTIC_VECTORS_PATH = PROJECT_ROOT / "cache" / "semantic_index.npy"
RERANKER_CACHE = PROJECT_ROOT / "cache" / "huggingface"
V1_1_EVIDENCE_CACHE = PROJECT_ROOT / "eval" / "results" / "router_v1_1" / "evidence_judge_cache.json"

CONFIG_PATH = STUDY_DIR / "selection_study_config.json"
LOCAL_SCORES_PATH = STUDY_DIR / "local_retrieval_scores.json"
SELECTIONS_PATH = STUDY_DIR / "policy_selections.json"
EVIDENCE_CACHE_PATH = STUDY_DIR / "evidence_judge_cache.json"

EVIDENCE_BUDGET = 5
BANDIT_TOPK = 4
BANDIT_UCB_C = 0.1
BANDIT_SEEDS = (20260927, 20260928, 20260929)
BANDIT_REPRESENTATIVE_SEED = 20260927
MMR_LAMBDAS = (0.10, 0.25, 0.50, 0.75)
FROZEN_POLICIES = ("DIRECT_TOP5", "ROUND_ROBIN")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path | str, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)


def rng_for(*parts: str) -> random.Random:
    seed = int(sha256_text("::".join(parts))[:8], 16)
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Frozen inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AspectSpec:
    aspect_id: str
    statement: str
    acceptable_sets: tuple[tuple[str, ...], ...]

    def covered_by(self, selected: frozenset[str]) -> bool:
        return any(set(option) <= selected for option in self.acceptable_sets)


@dataclass(frozen=True, slots=True)
class StreamData:
    stream_id: str
    stream_type: str
    query_text: str
    union_ids: tuple[str, ...]
    reranked_ids: tuple[str, ...]
    stream_top5_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaseContext:
    case_id: str
    raw_query: str
    shared_rewrite: str
    streams: tuple[StreamData, ...]
    frozen_direct_ids: tuple[str, ...]
    frozen_decompose_ids: tuple[str, ...]
    superpool_ids: tuple[str, ...]
    aspects: tuple[AspectSpec, ...]
    chunks: Mapping[str, Mapping[str, Any]]
    embeddings: Mapping[str, Sequence[float]]
    global_scores: Mapping[str, float]
    stream_scores: Mapping[str, Mapping[str, float]]

    @property
    def required_total(self) -> int:
        return len(self.aspects)


def load_frozen_inputs() -> dict[str, Any]:
    raw = load_json(RAW_PATH)
    truth = load_json(TRUTH_PATH)
    benchmark = load_json(BENCH_PATH)
    return {"raw": raw, "truth": truth, "benchmark": benchmark}


def aspect_specs_for(truth_case: Mapping[str, Any]) -> tuple[AspectSpec, ...]:
    specs: list[AspectSpec] = []
    for aspect in truth_case["required_aspects"]:
        options = aspect.get("acceptable_supporting_chunk_sets") or []
        acceptable = tuple(tuple(str(chunk) for chunk in option) for option in options)
        if not acceptable:
            acceptable = tuple(
                (str(entry["chunk_id"]),) for entry in aspect.get("supporting_evidence") or []
            )
        specs.append(
            AspectSpec(
                aspect_id=str(aspect["aspect_id"]),
                statement=str(aspect["statement"]),
                acceptable_sets=acceptable,
            )
        )
    return tuple(specs)


def superpool_ids_for(streams: Sequence[StreamData]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for stream in streams:
        for chunk_id in stream.union_ids:
            if chunk_id not in seen:
                seen.add(chunk_id)
                ordered.append(chunk_id)
    return tuple(ordered)


def load_chunk_records() -> dict[str, dict[str, Any]]:
    from src.indexing import load_index

    index = load_index(LEXICAL_INDEX_PATH)
    return {chunk.chunk_id: chunk.to_dict() for chunk in index.chunks}


def load_semantic_vectors() -> tuple[dict[str, Any], dict[str, Sequence[float]]]:
    from src.semantic_indexing import load_semantic_index

    index = load_semantic_index(SEMANTIC_INDEX_PATH)
    lookup = {chunk.chunk_id: position for position, chunk in enumerate(index.chunks)}
    vectors: dict[str, Sequence[float]] = {}
    for chunk_id, position in lookup.items():
        vectors[chunk_id] = index.vectors[position]
    return lookup, vectors


def compute_or_load_local_scores(
    contexts: Sequence[dict[str, Any]],
    *,
    refresh: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Cross-encode super-pool candidates with the frozen reranker.

    Global scores use the shared rewrite; per-stream scores replay each frozen
    stream query locally. Returns (payload, meter).
    """

    if LOCAL_SCORES_PATH.exists() and not refresh:
        payload = load_json(LOCAL_SCORES_PATH)
        if {entry["case_id"] for entry in payload["cases"]} == {
            context["case_id"] for context in contexts
        }:
            return payload, payload.get("meter", {})

    from src.reranked_retriever import build_reranker_text
    from src.reranker import CrossEncoderReranker
    from src.retriever import RetrievalResult

    reranker = CrossEncoderReranker(
        cache_folder=RERANKER_CACHE, device="cpu", local_files_only=True
    )
    meter = {"calls": 0, "pairs": 0, "seconds": 0.0}
    from time import perf_counter

    cases_out: list[dict[str, Any]] = []
    for context in contexts:
        chunk_ids = list(context["chunk_ids"])
        texts = [
            build_reranker_text(
                RetrievalResult(
                    score=0.0,
                    chunk_id=chunk_id,
                    text=context["chunks"][chunk_id]["text"],
                    source_path=context["chunks"][chunk_id]["source_path"],
                    source_url=context["chunks"][chunk_id]["source_url"],
                    title=context["chunks"][chunk_id]["title"],
                    heading_path=tuple(context["chunks"][chunk_id]["heading_path"]),
                    chunk_index=int(context["chunks"][chunk_id]["chunk_index"]),
                )
            )
            for chunk_id in chunk_ids
        ]
        started = perf_counter()
        global_scores = reranker.score(context["shared_rewrite"], texts)
        elapsed = perf_counter() - started
        meter["calls"] += 1
        meter["pairs"] += len(texts)
        meter["seconds"] += elapsed
        stream_scores: dict[str, dict[str, float]] = {}
        for stream in context["streams"]:
            stream_ids = list(stream["union_ids"])
            stream_texts = [texts[chunk_ids.index(chunk_id)] for chunk_id in stream_ids]
            if stream["stream_id"] == "base":
                stream_scores["base"] = {
                    chunk_id: float(global_scores[chunk_ids.index(chunk_id)])
                    for chunk_id in stream_ids
                }
                continue
            started = perf_counter()
            scores = reranker.score(stream["query_text"], stream_texts)
            elapsed = perf_counter() - started
            meter["calls"] += 1
            meter["pairs"] += len(stream_texts)
            meter["seconds"] += elapsed
            stream_scores[stream["stream_id"]] = {
                chunk_id: float(score) for chunk_id, score in zip(stream_ids, scores)
            }
        cases_out.append(
            {
                "case_id": context["case_id"],
                "global_scores": {
                    chunk_id: float(score) for chunk_id, score in zip(chunk_ids, global_scores)
                },
                "stream_scores": stream_scores,
            }
        )
        print(f"[local-rerank] {context['case_id']} scored {len(chunk_ids)} candidates", flush=True)
    payload = {
        "version": "router_v2_local_retrieval_scores",
        "reranker_model": reranker.model_name,
        "note": "deterministic local replay; no LLM calls; used to build policy inputs",
        "meter": meter,
        "cases": cases_out,
    }
    write_json(LOCAL_SCORES_PATH, payload)
    return payload, meter


def build_contexts(*, local_scores: Mapping[str, Any]) -> list[CaseContext]:
    inputs = load_frozen_inputs()
    raw, truth = inputs["raw"], inputs["truth"]
    truth_cases = {case["id"]: case for case in truth["cases"]}
    chunks = load_chunk_records()
    _, embeddings = load_semantic_vectors()
    scores_by_case = {entry["case_id"]: entry for entry in local_scores["cases"]}

    contexts: list[CaseContext] = []
    for case_entry in raw["cases"]:
        case_id = case_entry["case_id"]
        decompose = case_entry["arms"]["FIXED_DECOMPOSE"]
        if decompose["executed_path"] != "DECOMPOSE":
            raise ValueError(f"{case_id}: FIXED_DECOMPOSE did not execute the decompose path")
        trace = decompose["trace"]
        streams: list[StreamData] = []
        for stream in trace["streams"]:
            streams.append(
                StreamData(
                    stream_id=stream["stream_id"],
                    stream_type=stream["stream_type"],
                    query_text=stream["query_text"],
                    union_ids=tuple(stream["union_ids"]),
                    reranked_ids=tuple(stream["reranked_ids"]),
                    stream_top5_ids=tuple(stream["stream_top5_ids"]),
                )
            )
        case_scores = scores_by_case[case_id]
        contexts.append(
            CaseContext(
                case_id=case_id,
                raw_query=case_entry["raw_query"],
                shared_rewrite=case_entry["shared_rewrite"],
                streams=tuple(streams),
                frozen_direct_ids=tuple(case_entry["arms"]["FIXED_DIRECT"]["evidence_chunk_ids"]),
                frozen_decompose_ids=tuple(decompose["evidence_chunk_ids"]),
                superpool_ids=superpool_ids_for(streams),
                aspects=aspect_specs_for(truth_cases[case_id]),
                chunks=chunks,
                embeddings=embeddings,
                global_scores={
                    chunk_id: float(value)
                    for chunk_id, value in case_scores["global_scores"].items()
                },
                stream_scores={
                    stream_id: {chunk_id: float(value) for chunk_id, value in mapping.items()}
                    for stream_id, mapping in case_scores["stream_scores"].items()
                },
            )
        )
    return contexts


def context_to_dict(context: CaseContext) -> dict[str, Any]:
    return {
        "case_id": context.case_id,
        "shared_rewrite": context.shared_rewrite,
        "chunk_ids": list(context.superpool_ids),
        "streams": [
            {
                "stream_id": stream.stream_id,
                "stream_type": stream.stream_type,
                "query_text": stream.query_text,
                "union_ids": list(stream.union_ids),
                "reranked_ids": list(stream.reranked_ids),
                "stream_top5_ids": list(stream.stream_top5_ids),
            }
            for stream in context.streams
        ],
    }


# ---------------------------------------------------------------------------
# Runtime-legal selection policies
# ---------------------------------------------------------------------------


def _minmax_normalize(values: Mapping[str, float]) -> dict[str, float]:
    if not values:
        return {}
    low = min(values.values())
    high = max(values.values())
    if high - low <= 1e-12:
        return {key: 1.0 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def global_rerank_top(context: CaseContext, budget: int = EVIDENCE_BUDGET) -> list[str]:
    ordered = sorted(
        context.superpool_ids,
        key=lambda chunk_id: (-context.global_scores.get(chunk_id, 0.0), chunk_id),
    )
    return ordered[:budget]


def mmr_top(context: CaseContext, lam: float, budget: int = EVIDENCE_BUDGET) -> list[str]:
    relevance = _minmax_normalize(context.global_scores)
    selected: list[str] = []
    remaining = set(context.superpool_ids)
    while len(selected) < budget and remaining:
        best_id: str | None = None
        best_utility = -math.inf
        for chunk_id in sorted(remaining):
            rel = relevance.get(chunk_id, 0.0)
            novelty_penalty = 0.0
            if selected:
                max_similarity = max(
                    float(_dot(context.embeddings[chunk_id], context.embeddings[chosen]))
                    for chosen in selected
                )
                novelty_penalty = lam * max_similarity
            utility = rel - novelty_penalty
            if utility > best_utility + 1e-12 or (
                abs(utility - best_utility) <= 1e-12
                and best_id is not None
                and (rel, chunk_id) > (relevance.get(best_id, 0.0), best_id)
            ):
                best_utility = utility
                best_id = chunk_id
        if best_id is None:
            break
        selected.append(best_id)
        remaining.discard(best_id)
    return selected


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right)))


def _novelty(
    chunk_id: str,
    observed: Sequence[str],
    context: CaseContext,
) -> float:
    if not observed:
        return 1.0
    max_similarity = max(
        _dot(context.embeddings[chunk_id], context.embeddings[other]) for other in observed
    )
    return 1.0 - (max_similarity + 1.0) / 2.0


def _ranked_lists(context: CaseContext) -> dict[str, list[str]]:
    return {stream.stream_id: list(stream.reranked_ids) for stream in context.streams}


def _arm_relevance(context: CaseContext) -> dict[str, dict[str, float]]:
    return {
        stream.stream_id: _minmax_normalize(context.stream_scores.get(stream.stream_id, {}))
        for stream in context.streams
    }


def bandit_select(
    context: CaseContext,
    *,
    seed: int,
    diversity: bool,
    reserve_base_slots: int = 0,
    budget: int = EVIDENCE_BUDGET,
) -> dict[str, Any]:
    """Thompson Sampling over frozen streams with a runtime-legal reward.

    Arms are the FIXED_DECOMPOSE streams (base + subqueries). A pull observes
    the next unranked document down the arm's frozen reranked list. The reward
    is a fractional-Bernoulli proxy: the mean of min-max normalized cross-encoder
    relevance over a top-k window of that list, optionally multiplied by the
    paper's cosine novelty term and shifted by the paper's small UCB bonus.
    """

    ranked = _ranked_lists(context)
    relevance = _arm_relevance(context)
    arm_order = {stream.stream_id: index for index, stream in enumerate(context.streams)}
    rng = rng_for(context.case_id, "bandit", str(seed), "div" if diversity else "plain",
                  f"reserve{reserve_base_slots}")
    alpha = {arm: 1.0 for arm in ranked}
    beta = {arm: 1.0 for arm in ranked}
    pointers = {arm: 0 for arm in ranked}
    selected: list[str] = []
    pulls: list[dict[str, Any]] = []
    observed: list[str] = []

    if reserve_base_slots > 0 and "base" in ranked:
        for position in range(min(reserve_base_slots, len(ranked["base"]))):
            chunk_id = ranked["base"][position]
            selected.append(chunk_id)
            observed.append(chunk_id)
            pointers["base"] = position + 1
            pulls.append(
                {
                    "stream_id": "base",
                    "rank": position + 1,
                    "chunk_id": chunk_id,
                    "reward": None,
                    "reserved_exploitation": True,
                }
            )

    while len(selected) < budget:
        # Advance each arm past chunks already selected through any other arm.
        # The paper pulls (arm, rank) observations without an overlap rule; with
        # a fixed 5-slot evidence budget, duplicate chunks would waste slots, so
        # we suppress cross-stream duplicates exactly like the frozen V1 merge.
        available: dict[str, int] = {}
        for arm in ranked:
            pointer = pointers[arm]
            while pointer < len(ranked[arm]) and ranked[arm][pointer] in selected:
                pointer += 1
            pointers[arm] = pointer
            if pointer < len(ranked[arm]):
                available[arm] = pointer
        if not available:
            break
        samples = {arm: rng.betavariate(alpha[arm], beta[arm]) for arm in available}
        arm = max(available, key=lambda name: (samples[name], -arm_order[name]))
        position = available[arm]
        chunk_id = ranked[arm][position]
        window = [
            relevance[arm].get(ranked[arm][index], 0.0)
            for index in range(position, min(position + BANDIT_TOPK, len(ranked[arm])))
        ]
        reward = statistics.mean(window) if window else 0.0
        if diversity:
            reward *= _novelty(chunk_id, observed, context)
            reward += BANDIT_UCB_C * math.sqrt(math.log2(position + 2) / (position + 1))
        reward = max(0.0, min(1.0, reward))
        alpha[arm] += reward
        beta[arm] += 1.0 - reward
        pointers[arm] += 1
        selected.append(chunk_id)
        observed.append(chunk_id)
        pulls.append(
            {
                "stream_id": arm,
                "rank": position + 1,
                "chunk_id": chunk_id,
                "reward": reward,
                "reserved_exploitation": False,
            }
        )
    return {"ids": selected, "pulls": pulls}


def provenance_for(context: CaseContext, chunk_ids: Sequence[str]) -> list[dict[str, Any]]:
    provenance: list[dict[str, Any]] = []
    for chunk_id in chunk_ids:
        sources = []
        for stream in context.streams:
            if chunk_id in stream.stream_top5_ids:
                sources.append({"stream_id": stream.stream_id, "rank": stream.stream_top5_ids.index(chunk_id) + 1})
            elif chunk_id in stream.union_ids:
                sources.append({"stream_id": stream.stream_id, "rank": None})
        provenance.append(
            {
                "chunk_id": chunk_id,
                "in_base_stream_union": chunk_id in context.streams[0].union_ids,
                "in_base_stream_top5": chunk_id in context.streams[0].stream_top5_ids,
                "stream_sources": sources,
                "global_rerank_score": context.global_scores.get(chunk_id),
                "stream_rerank_scores": {
                    stream.stream_id: context.stream_scores.get(stream.stream_id, {}).get(chunk_id)
                    for stream in context.streams
                },
            }
        )
    return provenance


def build_policy_selections(
    contexts: Sequence[CaseContext],
    *,
    mmr_lambdas: Sequence[float] = MMR_LAMBDAS,
    bandit_seeds: Sequence[int] = BANDIT_SEEDS,
) -> dict[str, Any]:
    """Predeclared runtime-legal policies, one entry per policy instance."""

    policies: dict[str, Any] = {}

    def put(policy_id: str, family: str, case_id: str, ids: Sequence[str], extra: Mapping[str, Any] | None = None) -> None:
        entry = policies.setdefault(
            policy_id,
            {"policy_id": policy_id, "family": family, "role": "runtime", "cases": {}},
        )
        record: dict[str, Any] = {"ids": list(ids)}
        if extra:
            record.update(extra)
        entry["cases"][case_id] = record

    for context in contexts:
        put("DIRECT_TOP5", "frozen", context.case_id, context.frozen_direct_ids,
            {"source": "FIXED_DIRECT frozen final evidence order"})
        put("ROUND_ROBIN", "frozen", context.case_id, context.frozen_decompose_ids,
            {"source": "FIXED_DECOMPOSE frozen round-robin merge order"})
        global_ids = global_rerank_top(context)
        put(
            "GLOBAL_BASE_RERANK",
            "global",
            context.case_id,
            global_ids,
            {"source": "top5 by frozen MiniLM cross-encoder score under the shared rewrite"},
        )
        for lam in mmr_lambdas:
            put(
                f"MMR_{lam:.2f}",
                "mmr",
                context.case_id,
                mmr_top(context, lam),
                {"lambda": lam},
            )
        for variant, kwargs in (
            ("EACL_TS_TOPK", {"diversity": False, "reserve_base_slots": 0}),
            ("EACL_TS_TOPK_DIV", {"diversity": True, "reserve_base_slots": 0}),
            ("EACL_TS_RESERVE", {"diversity": False, "reserve_base_slots": 2}),
        ):
            for seed in bandit_seeds:
                result = bandit_select(context, seed=seed, **kwargs)
                put(
                    f"{variant}::seed{seed}",
                    "bandit",
                    context.case_id,
                    result["ids"],
                    {"seed": seed, "variant": variant, "pulls": result["pulls"],
                     "diversity": kwargs["diversity"],
                     "reserve_base_slots": kwargs["reserve_base_slots"]},
                )
    return policies


# ---------------------------------------------------------------------------
# Analysis-only oracle bounds (uses required-aspect truth)
# ---------------------------------------------------------------------------


def coverage_ids(context: CaseContext, selected: frozenset[str]) -> list[str]:
    return [aspect.aspect_id for aspect in context.aspects if aspect.covered_by(selected)]


def _oracle_search(
    context: CaseContext,
    candidate_ids: Sequence[str],
    budget: int = EVIDENCE_BUDGET,
) -> dict[str, Any]:
    """Exact max required-aspect coverage selection (<= budget chunks).

    Objective order: maximize covered aspects, then minimize chunks that cover
    no required aspect, then minimize chunk count, then lexicographic chunk-id
    tie-break. A chunk outside every acceptable support set can never improve
    this objective, so the search space is restricted to support-capable chunks.
    """

    capable = [
        chunk_id
        for chunk_id in dict.fromkeys(candidate_ids)
        if any(chunk_id in option for aspect in context.aspects for option in aspect.acceptable_sets)
    ]
    best: dict[str, Any] | None = None
    capable_sorted = sorted(capable)

    def score(selection: Sequence[str]) -> tuple:
        selected = frozenset(selection)
        covered = sum(1 for aspect in context.aspects if aspect.covered_by(selected))
        non_required = sum(
            1 for chunk_id in selection
            if not any(chunk_id in option for aspect in context.aspects for option in aspect.acceptable_sets)
        )
        return (covered, -non_required, -len(selection), tuple(sorted(selection)))

    if len(capable_sorted) > 32:  # pragma: no cover - pools here stay far below this bound
        raise RuntimeError(f"{context.case_id}: oracle search space too large ({len(capable_sorted)})")
    from itertools import combinations

    for size in range(1, budget + 1):
        for selection in combinations(capable_sorted, size):
            current = score(selection)
            if best is None or current > best["score"]:
                best = {"ids": list(selection), "score": current}

    if best is None:
        best = {"ids": [], "score": (0, 0, 0, ())}
    covered_ids = coverage_ids(context, frozenset(best["ids"]))
    return {
        "ids": best["ids"],
        "covered_aspect_ids": covered_ids,
        "covered_count": len(covered_ids),
    }


def compute_oracle_bounds(contexts: Sequence[CaseContext]) -> dict[str, Any]:
    oracle_cases: dict[str, Any] = {}
    totals = {
        "direct_truth_covered": 0,
        "round_robin_truth_covered": 0,
        "base_union_recall": 0,
        "superpool_recall": 0,
        "oracle_base_top5": 0,
        "oracle_top5": 0,
        "required_total": 0,
    }
    for context in contexts:
        base_union = frozenset(context.streams[0].union_ids)
        superpool = frozenset(context.superpool_ids)
        direct_truth = coverage_ids(context, frozenset(context.frozen_direct_ids))
        round_robin_truth = coverage_ids(context, frozenset(context.frozen_decompose_ids))
        base_recall = coverage_ids(context, base_union)
        superpool_recall = coverage_ids(context, superpool)
        oracle_base = _oracle_search(context, context.streams[0].union_ids)
        oracle_super = _oracle_search(context, context.superpool_ids)
        novel_chunk_ids = [chunk_id for chunk_id in context.superpool_ids if chunk_id not in base_union]
        novel_supporting = [
            chunk_id for chunk_id in novel_chunk_ids
            if any(chunk_id in option for aspect in context.aspects for option in aspect.acceptable_sets)
        ]
        only_novel_aspects = sorted(set(superpool_recall) - set(base_recall))
        oracle_cases[context.case_id] = {
            "required_total": context.required_total,
            "direct_truth_covered": len(direct_truth),
            "round_robin_truth_covered": len(round_robin_truth),
            "base_union_recall": len(base_recall),
            "superpool_recall": len(superpool_recall),
            "oracle_base_top5": {
                "ids": oracle_base["ids"],
                "covered_count": oracle_base["covered_count"],
                "covered_aspect_ids": oracle_base["covered_aspect_ids"],
            },
            "oracle_top5": {
                "ids": oracle_super["ids"],
                "covered_count": oracle_super["covered_count"],
                "covered_aspect_ids": oracle_super["covered_aspect_ids"],
            },
            "novel_chunk_count": len(novel_chunk_ids),
            "novel_supporting_chunk_count": len(novel_supporting),
            "aspects_only_coverable_by_novel_chunks": only_novel_aspects,
            "candidate_pool": {
                "superpool_size": len(context.superpool_ids),
                "base_union_size": len(base_union),
                "stream_union_sizes": {
                    stream.stream_id: len(stream.union_ids) for stream in context.streams
                },
            },
        }
        totals["direct_truth_covered"] += len(direct_truth)
        totals["round_robin_truth_covered"] += len(round_robin_truth)
        totals["base_union_recall"] += len(base_recall)
        totals["superpool_recall"] += len(superpool_recall)
        totals["oracle_base_top5"] += oracle_base["covered_count"]
        totals["oracle_top5"] += oracle_super["covered_count"]
        totals["required_total"] += context.required_total
    totals["exploration_upside_oracle_top5_minus_base_top5"] = (
        totals["oracle_top5"] - totals["oracle_base_top5"]
    )
    totals["decomposition_pool_recall_minus_base_union_recall"] = (
        totals["superpool_recall"] - totals["base_union_recall"]
    )
    return {
        "version": "router_v2_oracle_upper_bound",
        "role": "ANALYSIS_ONLY_ORACLE",
        "truth_semantics": (
            "an aspect is covered when the selected set contains one acceptable supporting chunk set; "
            "frozen truth marks verified examples, not an exhaustive gold set, so oracle numbers are "
            "pool-level lower bounds and are never runtime-legal"
        ),
        "selection_rule": {
            "objective_order": [
                "maximize required aspects covered",
                "minimize chunks covering no required aspect",
                "minimize chunk count",
                "lexicographic chunk-id tie-break",
            ],
            "candidate_restriction": "chunks appearing in at least one acceptable support set",
        },
        "totals": totals,
        "cases": oracle_cases,
    }


# ---------------------------------------------------------------------------
# Blind evidence judging (reuses the frozen Router V1.1 judge protocol)
# ---------------------------------------------------------------------------


def judge_evidence_selection(
    *,
    case_id: str,
    query: str,
    aspects: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
    client: Any,
    model: str,
    new_cache: dict[str, Any],
    v1_1_cache: Mapping[str, Any],
    usage: dict[str, float],
) -> dict[str, Any]:
    from eval.run_router_v1_1_evidence_diagnostic import (
        EVIDENCE_LABELS,
        JUDGE_MAX_TOKENS,
        JUDGE_VERSION,
        build_judge_messages,
        parse_judge,
        sha256_text as judge_sha256,
    )

    messages = build_judge_messages(query, list(aspects), list(evidence))
    key = judge_sha256(
        json.dumps(
            {
                "case_id": case_id,
                "messages": messages,
                "model": model,
                "judge_version": JUDGE_VERSION,
                "max_tokens": JUDGE_MAX_TOKENS,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    entry = None
    cache_source = None
    if key in new_cache:
        entry = new_cache[key]
        cache_source = "study_cache"
    elif key in v1_1_cache:
        entry = v1_1_cache[key]
        cache_source = "v1_1_cache"
    if entry is not None and "parsed" not in entry:
        entry = None
        cache_source = None
    if entry is None:
        from time import perf_counter

        started = perf_counter()
        raw, provider_usage = client.complete_with_usage(
            messages, max_tokens=JUDGE_MAX_TOKENS, temperature=0.0
        )
        latency = perf_counter() - started
        try:
            parsed = parse_judge(
                raw,
                {aspect["aspect_id"] for aspect in aspects},
                set(EVIDENCE_LABELS[: len(evidence)]),
            )
        except Exception as error:  # pragma: no cover - surfaced as judge_error
            return {
                "status": "judge_error",
                "error": str(error),
                "raw_response": raw,
                "judge_key": key,
            }
        entry = {
            "parsed": parsed,
            "usage": {
                "input_tokens": provider_usage.get("input_tokens"),
                "output_tokens": provider_usage.get("output_tokens"),
            },
            "latency_seconds": latency,
            "raw_response": raw,
        }
        new_cache[key] = entry
        usage["new_calls"] += 1
        usage["input_tokens"] += provider_usage.get("input_tokens") or 0
        usage["output_tokens"] += provider_usage.get("output_tokens") or 0
        usage["latency_seconds"] += latency
        write_json(EVIDENCE_CACHE_PATH, new_cache)
        cache_source = "new_call"
    else:
        usage["cache_hits"] += 1
    return {"status": "judged", "judge_key": key, "cache_source": cache_source, **entry["parsed"]}


def shape_evidence_judgment(
    evidence_ids: Sequence[str],
    parsed: Mapping[str, Any],
    required_total: int,
) -> dict[str, Any]:
    from eval.run_router_v1_1_evidence_diagnostic import EVIDENCE_LABELS

    labels = list(EVIDENCE_LABELS[: len(evidence_ids)])
    chunk_map = {label: chunk_id for label, chunk_id in zip(labels, evidence_ids)}
    supported = [aspect_id for aspect_id, item in parsed.items() if item["status"] == "SUPPORTED"]
    uncertain = [aspect_id for aspect_id, item in parsed.items() if item["status"] == "UNCERTAIN"]
    not_supported = [aspect_id for aspect_id, item in parsed.items() if item["status"] == "NOT_SUPPORTED"]
    useful_labels = sorted(
        {
            label
            for item in parsed.values()
            if item["status"] == "SUPPORTED"
            for label in item["supporting_evidence_ids"]
        }
    )
    useful_chunks = [chunk_map[label] for label in useful_labels]
    non_required = [chunk_id for chunk_id in evidence_ids if chunk_id not in useful_chunks]
    return {
        "evidence_ids": list(evidence_ids),
        "aspects": dict(parsed),
        "supported_aspect_ids": supported,
        "uncertain_aspect_ids": uncertain,
        "not_supported_aspect_ids": not_supported,
        "supported_count": len(supported),
        "required_total": required_total,
        "evidence_required_recall": (len(supported) / required_total) if required_total else None,
        "evidence_required_complete": len(supported) == required_total,
        "useful_chunk_ids": useful_chunks,
        "non_required_chunk_ids": non_required,
        "required_context_precision": (len(useful_chunks) / len(evidence_ids)) if evidence_ids else None,
        "non_required_chunk_count": len(non_required),
    }
