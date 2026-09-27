"""Router V1 frozen-benchmark execution driver.

This driver only orchestrates the frozen implementation; it adds incremental
raw-result persistence and progress logging. It does not change rewrite,
router, decomposer, retrieval, merge, generation, or fallback behavior.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.run_router_v1 import (  # noqa: E402
    FROZEN_BENCHMARK_PATH,
    build_pipeline,
    load_query_cases,
)
from src.router_v1_identity import verify_contract_identity  # noqa: E402
from src.router_v1_pipeline import ARM_NAMES  # noqa: E402

RAW_DIR = PROJECT_ROOT / "eval" / "results" / "router_v1" / "raw"
RAW_PATH = RAW_DIR / "router_v1_raw_results.json"
IMPLEMENTATION_COMMIT = "98cb503ee3a5b5f7f9340a5d5008b6497da5da0f"


def write_atomic(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    identity = verify_contract_identity()
    cases = load_query_cases(FROZEN_BENCHMARK_PATH, allow_frozen_benchmark=True)
    print(f"loaded {len(cases)} frozen benchmark cases", flush=True)
    pipeline = build_pipeline()
    record = {
        "driver_version": "router_v1_experiment_driver",
        "implementation_source_commit": IMPLEMENTATION_COMMIT,
        "benchmark_path": "eval/router_benchmark_v1.json",
        "frozen_benchmark_executed": True,
        "arms": list(ARM_NAMES),
        "execution_order": "per case: FIXED_DIRECT, FIXED_DECOMPOSE, ROUTED",
        "contract_identity": identity.to_dict(),
        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases": [],
    }
    write_atomic(RAW_PATH, record)
    for case in cases:
        started = time.perf_counter()
        run = pipeline.run_case(
            case["query"],
            case.get("history", []),
            arms=ARM_NAMES,
            case_id=case["case_id"],
            history_identifier=case.get("history_id"),
        )
        entry = run.to_dict()
        entry["wall_clock_seconds"] = time.perf_counter() - started
        record["cases"].append(entry)
        write_atomic(RAW_PATH, record)
        arms = entry["arms"]
        summary = ", ".join(
            f"{name}:{info['executed_path']}"
            f"{'/success' if info['execution_success'] else '/fail:' + str(info['error_stage'])}"
            for name, info in arms.items()
        )
        print(
            f"[{len(record['cases']):02d}/{len(cases)}] {case['case_id']} "
            f"({time.perf_counter() - started:.1f}s) {summary}",
            flush=True,
        )
    record["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_atomic(RAW_PATH, record)
    print(f"raw results written to {RAW_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
