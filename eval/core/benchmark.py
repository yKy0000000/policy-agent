"""Load the frozen Validation V1 questions, original facts, and Human Truth.

The manifest points to the original artifacts. We never rewrite or relabel them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_DIR = PROJECT_ROOT / "eval" / "benchmarks"


@dataclass(frozen=True, slots=True)
class OriginalFact:
    fact_id: str
    statement: str
    support: tuple[dict[str, Any], ...]
    supporting_chunk_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    query: str
    history: tuple[dict[str, str], ...]
    original_rubric_facts: tuple[OriginalFact, ...]
    query_required_aspects: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def original_fact_ids(self) -> tuple[str, ...]:
        return tuple(f.fact_id for f in self.original_rubric_facts)

    def supporting_chunks(self, aspect_id: str) -> tuple[str, ...]:
        return next(f.supporting_chunk_ids for f in self.original_rubric_facts if f.fact_id == aspect_id)

    def required_statements(self) -> tuple[dict[str, str], ...]:
        required = set(self.query_required_aspects)
        return tuple({"fact_id": f.fact_id, "fact": f.statement} for f in self.original_rubric_facts if f.fact_id in required)


@dataclass(frozen=True, slots=True)
class Benchmark:
    name: str
    version: str
    cases: tuple[BenchmarkCase, ...]
    source_hashes: dict[str, str]

    @property
    def original_fact_count(self) -> int:
        return sum(len(case.original_rubric_facts) for case in self.cases)

    @property
    def query_required_count(self) -> int:
        return sum(len(case.query_required_aspects) for case in self.cases)

    def by_id(self) -> dict[str, BenchmarkCase]:
        return {case.case_id: case for case in self.cases}


def _read_verified(source: dict[str, str]) -> dict[str, Any]:
    path = PROJECT_ROOT / source["path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != source["sha256"]:
        raise ValueError(f"frozen benchmark source hash mismatch: {source['path']}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_benchmark(name: str = "validation_v1") -> Benchmark:
    manifest = json.loads((BENCHMARK_DIR / name / "benchmark.json").read_text(encoding="utf-8"))
    sources = manifest["sources"]
    questions = _read_verified(sources["questions"])
    rubric = _read_verified(sources["original_rubric"])
    truth = _read_verified(sources["human_truth"])
    geometry = _read_verified(sources["support_chunk_mapping"])

    question_rows = questions["cases"]
    rubric_by_id = {row["case_id"]: row for row in rubric["cases"]}
    geo_by_id = {row["case_id"]: row for row in geometry["cases"]}
    truth_by_id: dict[str, set[str]] = {}
    for item in truth["items"]:
        if item["case_id"] in rubric_by_id and item["final"] == "QUERY_REQUIRED":
            truth_by_id.setdefault(item["case_id"], set()).add(item["aspect_id"])

    cases = []
    for row in question_rows:
        case_id = row["case_id"]
        facts = rubric_by_id[case_id]["facts"]
        chunk_map = {fact["fact_id"]: tuple(fact["gold_chunk_ids"]) for fact in geo_by_id[case_id]["fact_ranks"]}
        original = tuple(
            OriginalFact(fact["fact_id"], fact["statement"], tuple(fact["support"]), chunk_map[fact["fact_id"]])
            for fact in facts
        )
        if set(chunk_map) != {fact.fact_id for fact in original}:
            raise ValueError(f"support mapping drift: {case_id}")
        required = tuple(fact.fact_id for fact in original if fact.fact_id in truth_by_id.get(case_id, set()))
        if set(required) != truth_by_id.get(case_id, set()):
            raise ValueError(f"Human Truth ID drift: {case_id}")
        metadata = {key: value for key, value in row.items() if key not in {"case_id", "query", "history"}}
        cases.append(BenchmarkCase(case_id, row["query"], tuple(row.get("history", [])), original, required, metadata))

    result = Benchmark(manifest["name"], manifest["version"], tuple(cases), {key: source["sha256"] for key, source in sources.items()})
    expected = manifest["identity"]
    if len(result.cases) != expected["cases"] or result.original_fact_count != expected["original_facts"] or result.query_required_count != expected["query_required_aspects"]:
        raise ValueError("benchmark count drift")
    if len(result.by_id()) != len(result.cases) or len({f.fact_id for c in result.cases for f in c.original_rubric_facts}) != result.original_fact_count:
        raise ValueError("benchmark ID drift")
    return result
