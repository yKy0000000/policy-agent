"""Pre-register the Router V2 selection study before any evaluation call.

Writes selection_study_config.json with frozen input hashes, the complete
policy parameterization, the predeclared parameter grids, the dominance rule
for the generation stage, and the decision-matrix thresholds. Must run before
the evidence-judging stage; the evidence driver verifies it.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.router_v2_study_lib import (  # noqa: E402
    BENCH_PATH,
    BANDIT_REPRESENTATIVE_SEED,
    BANDIT_SEEDS,
    BANDIT_TOPK,
    BANDIT_UCB_C,
    CONFIG_PATH,
    EVIDENCE_BUDGET,
    LEXICAL_INDEX_PATH,
    MMR_LAMBDAS,
    RAW_PATH,
    SELECTIONS_PATH,
    SEMANTIC_INDEX_PATH,
    SEMANTIC_VECTORS_PATH,
    TRUTH_PATH,
    EVIDENCE_CACHE_PATH,
    STUDY_DIR,
    sha256_file,
    write_json,
)

CONFIG = {
    "study_version": "router_v2_selection_study_v1",
    "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "study_role": "EXPLORATORY_MECHANISM_STUDY",
    "declaration": (
        "The same frozen 20 queries and 66 required aspects are used to compare multiple evidence "
        "selection policies. This is an exploratory mechanism study, not a new independent "
        "confirmatory test. Any 'best' policy is exploratory only and requires a fresh holdout "
        "benchmark for confirmation. Oracle policies read required-aspect truth and are "
        "ANALYSIS_ONLY_ORACLE; they are never runtime methods."
    ),
    "frozen_inputs": {
        "raw_results_path": "eval/results/router_v1/raw/router_v1_raw_results.json",
        "raw_results_sha256": sha256_file(RAW_PATH),
        "required_aspects_path": "eval/router_v1_required_aspects.json",
        "required_aspects_sha256": sha256_file(TRUTH_PATH),
        "benchmark_path": "eval/router_benchmark_v1.json",
        "benchmark_sha256": sha256_file(BENCH_PATH),
        "lexical_index_path": "cache/policy_index.json",
        "lexical_index_sha256": sha256_file(LEXICAL_INDEX_PATH),
        "semantic_index_path": "cache/semantic_index.json",
        "semantic_index_sha256": sha256_file(SEMANTIC_INDEX_PATH),
        "semantic_vectors_path": "cache/semantic_index.npy",
        "semantic_vectors_sha256": sha256_file(SEMANTIC_VECTORS_PATH),
    },
    "frozen_reuse": {
        "decomposer_recalled": False,
        "subqueries_regenerated": False,
        "router_rerun": False,
        "rewrites": "frozen shared rewrites from router_v1_raw_results.json",
        "retrieval_replay": (
            "frozen per-stream lexical/semantic candidate unions, reranked order and stream top5; "
            "cross-encoder scores recomputed locally with the same frozen model to obtain scores "
            "for every candidate (verified bit-identical to stored top5 scores, delta 0.0)"
        ),
    },
    "evidence_budget": EVIDENCE_BUDGET,
    "candidate_super_pool": {
        "definition": (
            "per-case union over the FIXED_DECOMPOSE streams (base + 3 subqueries) of each stream's "
            "lexical Top20 + semantic Top20 candidate union, deduplicated by chunk_id, base first"
        ),
        "provenance_fields": [
            "in_base_stream_union", "in_base_stream_top5", "stream_sources (stream_id, rank)",
            "global_rerank_score", "stream_rerank_scores",
        ],
    },
    "runtime_policies": {
        "DIRECT_TOP5": {
            "family": "frozen",
            "definition": "frozen FIXED_DIRECT final evidence in frozen order (V1 baseline)",
        },
        "ROUND_ROBIN": {
            "family": "frozen",
            "definition": "frozen FIXED_DECOMPOSE round-robin merge evidence in frozen order (V1 baseline)",
        },
        "GLOBAL_BASE_RERANK": {
            "family": "global",
            "definition": (
                "top5 of the candidate super-pool by the frozen MiniLM cross-encoder "
                "(cross-encoder/ms-marco-MiniLM-L-6-v2) score under the shared rewritten query"
            ),
            "tie_break": "chunk_id ascending",
        },
        "MMR": {
            "family": "mmr",
            "lambda_grid": list(MMR_LAMBDAS),
            "definition": (
                "greedy utility = min-max normalized global cross-encoder relevance "
                "- lambda * max cosine similarity (frozen all-MiniLM-L6-v2 document embeddings) "
                "to already-selected chunks"
            ),
            "relevance_normalization": "min-max over the case candidate super-pool",
            "tie_break": "higher relevance, then chunk_id ascending",
        },
        "EACL_BANDIT": {
            "family": "bandit",
            "algorithm": "Thompson Sampling",
            "prior": "Beta(1,1) per arm",
            "posterior_update": "fractional Bernoulli: alpha += r, beta += 1 - r",
            "arms": "FIXED_DECOMPOSE streams (base + 3 subqueries); base is a regular arm (paper-faithful)",
            "ranked_list": "frozen per-stream reranked list; each pull observes the next unobserved document",
            "reward_relevance": (
                "per-arm min-max normalized frozen MiniLM cross-encoder score "
                "(continuous relevance signal; no required-aspect truth)"
            ),
            "top_k_window": BANDIT_TOPK,
            "variants": {
                "EACL_TS_TOPK": {"diversity": False, "reserve_base_slots": 0, "ucb_c": 0.0},
                "EACL_TS_TOPK_DIV": {
                    "diversity": True,
                    "reserve_base_slots": 0,
                    "ucb_c": BANDIT_UCB_C,
                    "novelty": "1 - (max cosine to observed + 1) / 2 (freeze all-MiniLM-L6-v2 embeddings)",
                    "ucb": "c * sqrt(log2(n + 1) / n), n = 1-based next position, fixed small c (paper drives c->0)",
                },
                "EACL_TS_RESERVE": {
                    "diversity": False,
                    "reserve_base_slots": 2,
                    "ucb_c": 0.0,
                    "base_handling": (
                        "V1-displacement-informed adaptation: base ranks 1-2 are reserved as guaranteed "
                        "exploitation before the bandit allocates the remaining 3 slots across the 4 arms "
                        "(base pointer starts at rank 3); reserved slots are not posterior observations"
                    ),
                },
            },
            "seeds": list(BANDIT_SEEDS),
            "seed_derivation": "sha256('case_id::bandit::seed::variant') mod 2^32, deterministic",
            "seed_aggregation": "mean and spread of per-seed evidence metrics; no seed cherry-picking",
            "generation_representative_seed": BANDIT_REPRESENTATIVE_SEED,
        },
    },
    "oracle": {
        "role": "ANALYSIS_ONLY_ORACLE",
        "ORACLE_TOP5": "max required-aspect coverage over the candidate super-pool with at most 5 chunks",
        "ORACLE_BASE_TOP5": "same objective restricted to the base-stream candidate union",
        "ORACLE_SUPERPOOL_RECALL": "aspects coverable by the entire candidate super-pool (no chunk limit)",
        "coverage_semantics": (
            "frozen required-aspect truth; an aspect is covered when the selection contains one of its "
            "acceptable_supporting_chunk_sets. Truth marks verified examples, not an exhaustive gold set."
        ),
        "tie_break": [
            "maximize covered aspects",
            "minimize chunks covering no required aspect",
            "minimize chunk count",
            "lexicographic chunk_id tie-break",
        ],
    },
    "generation_stage_rules": {
        "always_included": ["DIRECT_TOP5", "ROUND_ROBIN", "GLOBAL_BASE_RERANK", "ORACLE_TOP5"],
        "oracle_marking": "ORACLE_TOP5 generation is ANALYSIS_ONLY_ORACLE and is reported separately",
        "family_dominance_rule": (
            "A family (MMR grid, bandit variants) is dominated and excluded from generation when every "
            "member has pooled evidence required recall <= ROUND_ROBIN, pooled required context precision "
            "<= ROUND_ROBIN, and displacement query count >= ROUND_ROBIN; all three must hold."
        ),
        "family_representative_rule": (
            "highest pooled evidence required recall; ties broken by higher pooled precision, then fewer "
            "displaced queries, then deterministic order (MMR: smaller lambda; bandit: TS_TOPK, "
            "TS_TOPK_DIV, TS_RESERVE). The bandit representative uses its seed "
            f"{BANDIT_REPRESENTATIVE_SEED} case selections for generation."
        ),
    },
    "decision_matrix": {
        "basis": "blind-judged evidence aspects over the 20 frozen cases (66 required aspects)",
        "exploration_upside": "ORACLE_TOP5 supported total - ORACLE_BASE_TOP5 supported total",
        "oracle_upside_vs_direct": "ORACLE_TOP5 supported total - DIRECT_TOP5 supported total",
        "round_robin_oracle_gap": "ORACLE_TOP5 supported total - ROUND_ROBIN supported total",
        "thresholds_in_aspects": {
            "exploration_upside_small": 2,
            "oracle_upside_material": 5,
            "bandit_material_gain": 2,
            "runtime_recovery_weak_fraction": 0.25,
            "runtime_recovery_strong_fraction": 0.75,
            "selection_recovery_fraction": 0.50,
        },
        "rules": {
            "EXPLORATION_LIMITED": "exploration_upside <= 2",
            "UTILITY_ESTIMATION_LIMITED": (
                "exploration_upside > 2 and best runtime policy closes < 25% of the ROUND_ROBIN->oracle gap"
            ),
            "BANDIT_ADDS_VALUE": (
                "best bandit family total >= best simple (GLOBAL or MMR) total + 2 and oracle upside material"
            ),
            "SIMPLE_SELECTOR_SUFFICIENT": (
                "best simple closes >= 75% of the ROUND_ROBIN->oracle gap and bandit gain < 2 aspects"
            ),
            "SELECTION_LIMITED": (
                "oracle upside material and ROUND_ROBIN at least 4 aspects below oracle and best runtime "
                "closes >= 50% of the ROUND_ROBIN->oracle gap"
            ),
            "MIXED": "no single rule dominates",
        },
        "eacl_followup_mapping": {
            "DECOMPOSITION_UPSIDE_TOO_SMALL": "EXPLORATION_LIMITED",
            "IMPROVE_UTILITY_ESTIMATION_FIRST": "UTILITY_ESTIMATION_LIMITED",
            "ADOPT_BANDIT_DIRECTION": "BANDIT_ADDS_VALUE",
            "ADOPT_UTILITY_SELECTION_NOT_BANDIT": "SIMPLE_SELECTOR_SUFFICIENT or SELECTION_LIMITED",
        },
    },
    "cost_accounting_fields": [
        "reranker_local_calls", "reranker_local_pairs", "reranker_local_seconds",
        "evidence_judge_calls", "evidence_judge_input_tokens", "evidence_judge_output_tokens",
        "generation_calls", "generation_input_tokens", "generation_output_tokens",
        "answer_judge_calls", "answer_judge_input_tokens", "answer_judge_output_tokens",
        "wall_clock_seconds",
    ],
    "planned_outputs": [
        "selection_study_config.json",
        "candidate_pool_analysis.json",
        "oracle_upper_bound.json",
        "policy_selections.json",
        "evidence_policy_results.json",
        "generation_results.json",
        "answer_eval.json",
        "selection_study_analysis.json",
        "selection_study_report.md",
        "selection_study_failure_review.md",
    ],
    "output_dir": "eval/results/router_v2_selection_study",
}


def main() -> int:
    if CONFIG_PATH.exists():
        existing = CONFIG_PATH.read_text(encoding="utf-8")
        raise SystemExit(
            "refusing to overwrite pre-registered config; delete it manually to re-register "
            f"({len(existing)} bytes at {CONFIG_PATH})"
        )
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    write_json(CONFIG_PATH, CONFIG)
    print(f"pre-registered at {CONFIG_PATH}")
    print(f"planned outputs in {STUDY_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
