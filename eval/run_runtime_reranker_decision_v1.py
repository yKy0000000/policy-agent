"""Paired historical quality and warm local runtime timing for the frozen decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import mean
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
ARMS = {
    "minilm_top5": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "bge_top5": "BAAI/bge-reranker-base",
}
SAMPLE_IDS = tuple(f"VAL-001-{number:03d}" for number in range(1, 40, 2))
OUT = ROOT / "eval" / "results" / "runtime_reranker_decision_v1"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    point = (len(ordered) - 1) * fraction
    low = int(point)
    return ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) * (point - low)


def stats(values: list[float]) -> dict:
    return {"n": len(values), "mean": mean(values), "p50": percentile(values, .5), "p95": percentile(values, .95)} if values else {"n": 0, "mean": None, "p50": None, "p95": None}


def paired_quality() -> dict:
    from eval.core.benchmark import load_benchmark

    source = ROOT / "eval" / "results" / "reranker_transfer_results.json"
    historical = read_json(source)
    benchmark = load_benchmark("validation_v1")
    required = {case.case_id: set(case.query_required_aspects) for case in benchmark.cases}
    if len(required) != 50 or sum(map(len, required.values())) != 208:
        raise ValueError("frozen QUERY_REQUIRED identity changed")
    totals = {arm: {"covered": 0, "complete": 0, "context_covered": 0, "context_complete": 0,
                    "contradicted_claims": 0, "cases": []} for arm in ARMS}
    paired = {"minilm_wins": [], "bge_wins": [], "ties": [], "bge_gained_aspects": [], "bge_lost_aspects": []}
    by_id = {case["case_id"]: case for case in historical["cases"]}
    for case in benchmark.cases:
        case_id = case.case_id
        row = by_id[case_id]
        if row["status"] != "complete":
            raise ValueError(f"incomplete historical row: {case_id}")
        covered_by_arm = {}
        for arm in ARMS:
            archived = row["arms"][arm]
            covered = set(archived["quality"]["covered_fact_ids"]) & required[case_id]
            context = set(archived["available_fact_ids"]) & required[case_id]
            if not covered <= required[case_id] or not context <= required[case_id]:
                raise ValueError(f"invalid aspect IDs: {case_id}/{arm}")
            complete = covered == required[case_id]
            t = totals[arm]
            t["covered"] += len(covered)
            t["complete"] += int(complete)
            t["context_covered"] += len(context)
            t["context_complete"] += int(context == required[case_id])
            t["contradicted_claims"] += archived["quality"]["claims"].get("contradicted", 0)
            t["cases"].append({"case_id": case_id, "covered": sorted(covered), "complete": complete,
                               "context_covered": sorted(context)})
            covered_by_arm[arm] = (covered, complete)
        mini, mc = covered_by_arm["minilm_top5"]
        bge, bc = covered_by_arm["bge_top5"]
        paired["bge_gained_aspects"].extend(sorted(bge - mini))
        paired["bge_lost_aspects"].extend(sorted(mini - bge))
        paired["bge_wins" if bc and not mc else "minilm_wins" if mc and not bc else "ties"].append(case_id)
    return {"source": str(source.relative_to(ROOT)), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "protocol": "historical reranker-transfer judge, both arms filtered to 208 frozen QUERY_REQUIRED IDs",
            "dataset_status": "exposed development/research benchmark", "required_aspects": 208,
            "candidate_availability_original_facts": "235/239 (shared archived candidate union)",
            "arms": totals, "paired": paired}


def measure_arm(arm: str, live_generation: bool) -> dict:
    import torch
    from eval.core.benchmark import load_benchmark
    from src.indexing import load_index
    from src.semantic_indexing import load_semantic_index
    from src.semantic_embeddings import SentenceTransformerEncoder
    from src.retriever import PolicyRetriever
    from src.semantic_retriever import SemanticPolicyRetriever
    from src.reranker import CrossEncoderReranker
    from src.reranked_retriever import RerankedPolicyRetriever, build_reranker_text

    try:
        import psutil
        rss = lambda: psutil.Process(os.getpid()).memory_info().rss
    except ImportError:
        rss = lambda: None

    benchmark = load_benchmark("validation_v1")
    queries = {case.case_id: case.query for case in benchmark.cases}
    lexical_index = load_index(ROOT / "cache" / "policy_index.json")
    semantic_index = load_semantic_index(ROOT / "cache" / "semantic_index.json")
    if [c.to_dict() for c in lexical_index.chunks] != [c.to_dict() for c in semantic_index.chunks]:
        raise ValueError("lexical/semantic snapshots differ")
    encoder = SentenceTransformerEncoder(semantic_index.model_name, cache_folder=ROOT / "cache" / "huggingface", device="cpu", local_files_only=True)
    lexical = PolicyRetriever(lexical_index)
    semantic = SemanticPolicyRetriever(semantic_index, encoder)
    before_load_rss = rss()
    scorer_source = ARMS[arm]
    if arm == "bge_top5":
        cache_root = ROOT / "cache" / "huggingface" / "models--BAAI--bge-reranker-base"
        revision = (cache_root / "refs" / "main").read_text(encoding="utf-8").strip()
        scorer_source = str(cache_root / "snapshots" / revision)
        if not (Path(scorer_source) / "model.safetensors").is_file():
            raise FileNotFoundError("cached BGE model weights are missing")
    start = perf_counter()
    scorer = CrossEncoderReranker(scorer_source, cache_folder=ROOT / "cache" / "huggingface", device="cpu", batch_size=16, local_files_only=True)
    load_seconds = perf_counter() - start
    after_load_rss = rss()
    retriever = RerankedPolicyRetriever(lexical, semantic, scorer)
    warm_candidates = retriever.candidates(queries[SAMPLE_IDS[0]])
    scorer.score(queries[SAMPLE_IDS[0]], [build_reranker_text(warm_candidates[0].result)])

    agent = None
    if live_generation:
        from src.agent import PolicySupportAgent
        from src.llm_client import LLMConfig, OpenAIChatCompletionsClient

        config = LLMConfig.from_env(ROOT / ".env")
        agent = PolicySupportAgent(retriever, OpenAIChatCompletionsClient(config), model=config.model)
    rows = []
    for case_id in SAMPLE_IDS:
        query = queries[case_id]
        if agent is None:
            selected = retriever.search(query, top_k=5)
            timing = retriever.timings[-1]
            row = {"case_id": case_id, "rerank_seconds": timing.reranker_seconds,
                   "retrieval_excluding_rerank_seconds": timing.total_seconds - timing.reranker_seconds,
                   "local_retrieval_total_seconds": timing.total_seconds,
                   "candidate_count": timing.candidate_count,
                   "selected_chunk_ids": [item.chunk_id for item in selected],
                   "rewrite_seconds": 0.0, "generation_seconds": None, "validation_seconds": None,
                   "end_to_end_seconds": None}
        else:
            result = agent.answer(query, history=[])
            trace = result.trace
            assert trace is not None and trace.rerank_seconds is not None
            row = {"case_id": case_id, "rerank_seconds": trace.rerank_seconds,
                   "retrieval_excluding_rerank_seconds": trace.retrieval_seconds - trace.rerank_seconds - (trace.evidence_selection_seconds or 0),
                   "local_retrieval_total_seconds": trace.retrieval_seconds,
                   "candidate_count": retriever.timings[-1].candidate_count,
                   "selected_chunk_ids": list(trace.evidence_chunk_ids),
                   "rewrite_seconds": trace.rewrite_seconds, "generation_seconds": trace.generation_seconds,
                   "validation_seconds": trace.validation_seconds, "end_to_end_seconds": trace.total_seconds}
        rows.append(row)
        print(f"{arm}: {case_id} rerank={row['rerank_seconds']:.3f}s", flush=True)
    metrics = {name: stats([row[name] for row in rows if row[name] is not None])
               for name in ("rerank_seconds", "retrieval_excluding_rerank_seconds", "local_retrieval_total_seconds",
                            "rewrite_seconds", "generation_seconds", "validation_seconds", "end_to_end_seconds")}
    return {"arm": arm, "model": ARMS[arm], "model_source": scorer_source, "device": "cpu", "batch_size": 16,
            "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
            "sample_ids": SAMPLE_IDS, "warmup": "one untimed score before sample", "model_load_seconds": load_seconds,
            "rss_before_model_load_bytes": before_load_rss, "rss_after_model_load_bytes": after_load_rss,
            "cache": "rewrite and generation disabled", "generation": "fresh API calls" if live_generation else "not called",
            "metrics": metrics, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-only", action="store_true")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--live-generation", action="store_true")
    args = parser.parse_args()
    if args.quality_only == bool(args.arm):
        parser.error("choose exactly one of --quality-only or --arm")
    if args.quality_only:
        output = OUT / "paired_quality.json"
        write_json(output, paired_quality())
    else:
        suffix = "live_runtime" if args.live_generation else "local_runtime"
        output = OUT / f"{args.arm}_{suffix}.json"
        write_json(output, measure_arm(args.arm, args.live_generation))
    print(output)


if __name__ == "__main__":
    main()
