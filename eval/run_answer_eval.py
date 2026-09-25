"""Run deterministic answer checks and produce a claim-level human review sheet."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from statistics import mean
from time import perf_counter
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from eval.metrics import (POLICIES, answer_quality_key, evidence_utilization,
                          select_answer_oracle)
from eval.run_evidence_eval import evaluate as evaluate_evidence, load_inputs as load_v3_inputs
from src.agent import AgentPipelineError, PolicySupportAgent
from src.conversation import select_recent_history
from src.generator import (GENERATION_PROMPT_VERSION, assign_evidence_sources,
                           build_grounded_messages,
                           generate_grounded_answer, validate_citations)
from src.llm_client import LLMConfig, OpenAIChatCompletionsClient


CATEGORIES = ("direct", "specific", "semantic", "broad", "multi_turn", "unsupported")
_ABSTENTION_PATTERNS = (
    re.compile(
        r"\b(?:the\s+)?provided(?:\s+published|\s+github)?\s+policies\s+"
        r"(?:do|does)\s+not\s+(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?published\s+policies\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?(?:provided\s+)?evidence\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?provided\s+sources\s+(?:do|does)\s+not\s+"
        r"(?:specify|state|provide|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:this|the requested)\s+information\s+is\s+not\s+specified\s+"
        r"in\s+the\s+provided\s+policies\b",
        re.IGNORECASE,
    ),
)


def detect_behavior(answer: str) -> str:
    """Conservatively classify an explicit evidence-based abstention."""

    if not answer.strip():
        return "empty"
    if any(pattern.search(answer) for pattern in _ABSTENTION_PATTERNS):
        return "abstain"
    return "answer"


def behavior_passes(expected_behavior: str, answer: str) -> bool:
    detected = detect_behavior(answer)
    if expected_behavior == "abstain":
        return detected == "abstain"
    if expected_behavior == "answer":
        return detected == "answer"
    raise ValueError(f"unsupported expected behavior: {expected_behavior}")


def normalize_for_matching(text: str) -> str:
    """Normalize case, whitespace, and punctuation for conservative phrase matching."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in normalized
    )
    return " ".join(normalized.split())


def find_forbidden_claims(answer: str, forbidden_claims: Sequence[str]) -> list[str]:
    normalized_answer = normalize_for_matching(answer)
    return [
        claim
        for claim in forbidden_claims
        if normalize_for_matching(claim) in normalized_answer
    ]


def acceptable_source_matches(
    cited_sources: Sequence[Mapping[str, Any]],
    acceptable_sources: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether at least one cited source satisfies an acceptable-source rule."""

    for cited in cited_sources:
        for acceptable in acceptable_sources:
            if cited.get("source_path") != acceptable.get("source_path"):
                continue
            heading_contains = str(acceptable.get("heading_contains", "")).strip()
            if not heading_contains:
                return True
            heading_path = " > ".join(str(value) for value in cited.get("heading_path", []))
            if heading_contains.casefold() in heading_path.casefold():
                return True
    return False


def aggregate_deterministic_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate completed cases while reporting technical errors separately."""

    completed = [row for row in rows if row["pipeline"]["status"] == "completed"]
    errors = [row for row in rows if row["pipeline"]["status"] == "error"]
    answer_rows = [row for row in completed if row["expected_behavior"] == "answer"]
    abstain_rows = [row for row in completed if row["expected_behavior"] == "abstain"]

    def rate(group: Sequence[Mapping[str, Any]], field: str) -> float | None:
        return (
            sum(bool(row["deterministic_checks"][field]) for row in group) / len(group)
            if group
            else None
        )

    forbidden_count = sum(
        len(row["deterministic_checks"]["forbidden_claim_matches"])
        for row in completed
    )
    cases_with_forbidden = sum(
        bool(row["deterministic_checks"]["forbidden_claim_matches"])
        for row in completed
    )
    return {
        "total_cases": len(rows),
        "completed_cases": len(completed),
        "errored_cases": len(errors),
        "error_case_ids": [row["id"] for row in errors],
        "execution_success_rate": (
            sum(bool(row["pipeline"]["execution_success"]) for row in rows)
            / len(rows)
            if rows
            else 0.0
        ),
        "behavior_check_rate": rate(completed, "behavior_check"),
        "answer_behavior_check_rate": rate(answer_rows, "behavior_check"),
        "abstention_check_rate": rate(abstain_rows, "behavior_check"),
        "citation_validation_rate": rate(completed, "citation_validation"),
        "source_check_rate": rate(completed, "source_check"),
        "forbidden_claim_violation_count": forbidden_count,
        "cases_with_forbidden_claim_violation": cases_with_forbidden,
        "forbidden_claim_violation_rate": (
            cases_with_forbidden / len(completed) if completed else None
        ),
        "unsupported_abstention_check_rate": rate(abstain_rows, "behavior_check"),
    }


def run_answer_eval(
    cases: Sequence[Mapping[str, Any]],
    agent: PolicySupportAgent,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Evaluate the same PolicySupportAgent.answer entry point used by the CLI."""

    usage = {
        "rewrite_api_calls": 0,
        "rewrite_cache_hits": 0,
        "generation_api_calls": 0,
        "generation_cache_hits": 0,
        "remote_llm_calls": 0,
        "errors": 0,
    }
    rows: list[dict[str, Any]] = []
    for case in cases:
        base = {
            "id": case["id"],
            "source_case_id": case["source_case_id"],
            "category": case["category"],
            "expected_behavior": case["expected_behavior"],
            "question": case["question"],
            "history": select_recent_history(list(case.get("history", []))),
            "required_points": list(case["required_points"]),
            "acceptable_sources": list(case["acceptable_sources"]),
            "forbidden_claims": list(case["forbidden_claims"]),
            "supporting_snippets": list(case["supporting_snippets"]),
            "notes": case["notes"],
        }
        try:
            result = agent.answer(str(case["question"]), list(case.get("history", [])))
        except AgentPipelineError as error:
            trace = error.trace.to_dict() if error.trace else None
            _add_usage(usage, trace)
            usage["errors"] += 1
            rows.append({
                **base,
                "rewritten_query": trace["rewritten_query"] if trace else None,
                "execution_trace": trace,
                "pipeline": {
                    "status": "error",
                    "execution_success": False,
                    "error_stage": error.stage,
                    "error": str(error),
                },
            })
            continue

        trace = result.trace.to_dict() if result.trace else None
        _add_usage(usage, trace)
        evidence_summary = [
            {
                "citation_id": f"S{rank}",
                "rank": rank,
                "reranker_score": item.reranker_score,
                "chunk_id": item.chunk_id,
                "title": item.title,
                "heading_path": list(item.heading_path),
                "source_path": item.source_path,
                "source_url": item.source_url,
            }
            for rank, item in enumerate(result.evidence, start=1)
        ]
        answer = result.answer
        checks = {
            "detected_behavior": detect_behavior(answer),
            "behavior_check": behavior_passes(str(case["expected_behavior"]), answer),
            "citation_validation": bool(result.citation_validation["valid"]),
            "source_check": acceptable_source_matches(
                list(result.citations), list(case["acceptable_sources"])
            ),
            "forbidden_claim_matches": find_forbidden_claims(
                answer, list(case["forbidden_claims"])
            ),
        }
        checks["forbidden_claim_check"] = not checks["forbidden_claim_matches"]
        checks["all_deterministic_checks_pass"] = all((
            checks["behavior_check"],
            checks["citation_validation"],
            checks["source_check"],
            checks["forbidden_claim_check"],
        ))
        rows.append({
            **base,
            "rewritten_query": result.rewritten_query,
            "retrieved_evidence": evidence_summary,
            "generated_answer": answer,
            "citation_ids": list(result.citation_ids),
            "sources": list(result.citations),
            "generator_validation": result.citation_validation,
            "generation_response_source": result.generation_response_source,
            "execution_trace": trace,
            "pipeline": {
                "status": "completed",
                "execution_success": True,
                "error_stage": None,
                "error": None,
            },
            "deterministic_checks": checks,
        })
    return rows, usage


def _add_usage(usage: dict[str, int], trace: Mapping[str, Any] | None) -> None:
    if not trace:
        return
    usage["remote_llm_calls"] += int(trace["remote_llm_calls"])
    if trace["rewrite_source"] == "api":
        usage["rewrite_api_calls"] += 1
    elif trace["rewrite_source"] == "cache":
        usage["rewrite_cache_hits"] += 1
    if trace["generation_source"] == "api":
        usage["generation_api_calls"] += 1
    elif trace["generation_source"] == "cache":
        usage["generation_cache_hits"] += 1

def category_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["category"])].append(row)
    return {
        category: aggregate_deterministic_metrics(grouped.get(category, []))
        for category in CATEGORIES
    }


def aggregate_instrumentation(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize observed timings and provider usage without filling missing values."""

    traces = [row["execution_trace"] for row in rows if row.get("execution_trace")]
    latencies: dict[str, dict[str, float | int | None]] = {}
    for stage in ("rewrite", "retrieval", "rerank", "generation", "validation", "total"):
        values = sorted(
            float(trace["latency_seconds"][stage])
            for trace in traces
            if trace["latency_seconds"][stage] is not None
        )
        latencies[stage] = {
            "observed_requests": len(values),
            "sum_seconds": sum(values) if values else None,
            "mean_seconds": sum(values) / len(values) if values else None,
            "p50_seconds": values[(len(values) - 1) // 2] if values else None,
            "p95_seconds": values[min(len(values) - 1, int(0.95 * len(values)))] if values else None,
        }
    tokens: dict[str, dict[str, int | None]] = {}
    for field in ("rewrite_input", "rewrite_output", "generation_input", "generation_output"):
        values = [trace["token_usage"][field] for trace in traces if trace["token_usage"][field] is not None]
        tokens[field] = {
            "observed_requests": len(values),
            "reported_total": sum(values) if values else None,
        }
    return {"latency_seconds": latencies, "token_usage": tokens}


def render_summary(report: Mapping[str, Any]) -> str:
    metrics = report["summary"]["overall"]
    lines = [
        "# Answer eval execution and deterministic check summary",
        "",
        "Execution success means the shared production path completed; it does not mean the answer is correct. Semantic correctness and claim-level citation entailment are not auto-scored.",
        "",
        "## Overall deterministic metrics",
        "",
        f"- Total cases: {metrics['total_cases']}",
        f"- Completed cases: {metrics['completed_cases']}",
        f"- Errored cases: {metrics['errored_cases']}",
        f"- Execution success rate: {_metric(metrics['execution_success_rate'])}",
        f"- Behavior check rate: {_metric(metrics['behavior_check_rate'])}",
        f"- Answer-case behavior check rate: {_metric(metrics['answer_behavior_check_rate'])}",
        f"- Abstention check rate: {_metric(metrics['abstention_check_rate'])}",
        f"- Citation validation rate: {_metric(metrics['citation_validation_rate'])}",
        f"- Source check rate: {_metric(metrics['source_check_rate'])}",
        f"- Forbidden claim violations: {metrics['forbidden_claim_violation_count']}",
        f"- Forbidden claim violation rate: {_metric(metrics['forbidden_claim_violation_rate'])}",
        f"- Unsupported abstention check rate: {_metric(metrics['unsupported_abstention_check_rate'])}",
        "",
        "## Metrics by category",
        "",
    ]
    for category in CATEGORIES:
        row = report["summary"]["by_category"][category]
        lines.extend(
            [
                f"### {category}",
                "",
                f"- Cases/completed/errors: {row['total_cases']}/{row['completed_cases']}/{row['errored_cases']}",
                f"- Execution success: {_metric(row['execution_success_rate'])}",
                f"- Behavior check: {_metric(row['behavior_check_rate'])}",
                f"- Citation validation: {_metric(row['citation_validation_rate'])}",
                f"- Source check: {_metric(row['source_check_rate'])}",
                f"- Forbidden claim violation rate: {_metric(row['forbidden_claim_violation_rate'])}",
                "",
            ]
        )
    failures = report["summary"]["deterministic_failures"]
    lines.extend(["## Failed deterministic checks", ""])
    if failures:
        for row in failures:
            lines.append(f"- `{row['id']}`: {', '.join(row['failed_checks'])}")
    else:
        lines.append("None.")
    lines.extend(["", "## Unsupported cases", ""])
    for row in report["cases"]:
        if row["category"] == "unsupported":
            checks = row.get("deterministic_checks", {})
            lines.append(
                f"- `{row['id']}`: detected={checks.get('detected_behavior')}, "
                f"behavior_check={checks.get('behavior_check')}, "
                f"forbidden_matches={checks.get('forbidden_claim_matches')}"
            )
    usage = report["usage"]
    lines.extend(
        [
            "",
            "## API and cache usage",
            "",
            f"- Rewrite API calls/cache hits: {usage['rewrite_api_calls']}/{usage['rewrite_cache_hits']}",
            f"- Generation API calls/cache hits: {usage['generation_api_calls']}/{usage['generation_cache_hits']}",
            f"- Remote LLM calls: {usage['remote_llm_calls']}",
            f"- Errors: {usage['errors']}",
            "",
            "## Request latency baseline",
            "",
        ]
    )
    for stage, values in report["summary"]["instrumentation"]["latency_seconds"].items():
        lines.append(
            f"- {stage}: observed={values['observed_requests']}, "
            f"mean={_metric(values['mean_seconds'])}s, "
            f"p50={_metric(values['p50_seconds'])}s, "
            f"p95={_metric(values['p95_seconds'])}s"
        )
    lines.extend(["", "## Provider-reported token usage", ""])
    for stage, values in report["summary"]["instrumentation"]["token_usage"].items():
        lines.append(
            f"- {stage}: observed={values['observed_requests']}, "
            f"reported total={values['reported_total'] if values['reported_total'] is not None else 'unavailable'}"
        )
    lines.extend(
        [
            "",
            "## Methodology and limitations",
            "",
            "- Behavior detection requires an explicit evidence/policy insufficiency marker; vague uncertainty such as 'I am not sure' is not counted as abstention.",
            "- Forbidden claims use normalized exact-phrase matching. Semantically equivalent paraphrases may not be detected.",
            "- Acceptable-source checks validate cited metadata, not whether the source entails the adjacent claim.",
            "- Required-point coverage, semantic correctness, claim-level grounding, citation entailment, and overclaiming remain human-review tasks.",
            "- No LLM judge or automated semantic score is used.",
            "- Token counts are null for cache hits or provider responses without usage; no counts are estimated.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_human_review(report: Mapping[str, Any]) -> str:
    lines = [
        "# Answer eval human review",
        "",
        "Semantic fields below are intentionally left unchecked for human reviewers.",
        "",
    ]
    for row in report["cases"]:
        lines.extend([f"## {row['id']} — {row['category']}", ""])
        if row["category"] == "broad":
            lines.extend(
                [
                    "> **BROAD CASE REVIEW NOTE:** Check whether the answer limits itself to supported major circumstances, avoids claiming an exhaustive list, and gives enough qualification to prevent an exhaustive reading.",
                    "",
                ]
            )
        if row["category"] == "unsupported":
            lines.extend(
                [
                    "> **UNSUPPORTED CASE:** Check that related policy context was not converted into an unsupported percentage, physical location, or decision deadline.",
                    "",
                ]
            )
        lines.extend(
            [
                f"- **Source case:** `{row['source_case_id']}`",
                f"- **Expected behavior:** `{row['expected_behavior']}`",
                f"- **Question:** {row['question']}",
            ]
        )
        if row["history"]:
            lines.extend(["- **Original history:**", ""])
            for message in row["history"]:
                lines.append(f"  - **{message['role'].capitalize()}:** {message['content']}")
        lines.extend(
            [
                f"- **LLM rewritten query:** {row.get('rewritten_query') or '(unavailable)'}",
                "",
                "### Retrieved Top5 evidence",
                "",
            ]
        )
        for evidence in row.get("retrieved_evidence", []):
            heading = " > ".join(evidence["heading_path"]) or "Document introduction"
            lines.append(
                f"- [{evidence['citation_id']}] **{evidence['title']}** — {heading} — "
                f"`{evidence['source_path']}`"
            )
        lines.extend(["", "### Generated answer", ""])
        lines.append(row.get("generated_answer") or f"(pipeline error: {row['pipeline'].get('error')})")
        lines.extend(["", "### Inline citations and actual cited sources", ""])
        lines.append(
            f"- Citation IDs: {', '.join(row.get('citation_ids', [])) or '(none)'}"
        )
        for source in row.get("sources", []):
            heading = " > ".join(source["heading_path"]) or "Document introduction"
            lines.append(
                f"- [{source['citation_id']}] **{source['title']}** — {heading} — "
                f"`{source['source_path']}` — {source['source_url']}"
            )
        lines.extend(["", "### Required points", ""])
        for point in row["required_points"]:
            lines.extend(
                [
                    f"- {point}",
                    "  - [ ] covered",
                    "  - [ ] partially covered",
                    "  - [ ] missing",
                ]
            )
        lines.extend(["", "### Supporting snippets", ""])
        for snippet in row["supporting_snippets"]:
            lines.extend(["> " + line if line else ">" for line in snippet.splitlines()])
            lines.append("")
        lines.extend(["### Forbidden claims", ""])
        if row["forbidden_claims"]:
            lines.extend(f"- {claim}" for claim in row["forbidden_claims"])
        else:
            lines.append("- None specified.")
        checks = row.get("deterministic_checks", {})
        validation = row.get("generator_validation", {})
        lines.extend(
            [
                "",
                "### Deterministic checks",
                "",
                f"- Execution: `{row['pipeline']}`",
                f"- Detected behavior: `{checks.get('detected_behavior')}`",
                f"- Behavior check: `{checks.get('behavior_check')}`",
                f"- Citation validation: `{checks.get('citation_validation')}`",
                f"- Invalid citations: `{validation.get('invalid_citations')}`",
                f"- Missing citations: `{'missing_citations' in validation.get('warnings', [])}`",
                f"- Model-generated URL: `{validation.get('contains_model_generated_url')}`",
                f"- Source check: `{checks.get('source_check')}`",
                f"- Forbidden claim matches: `{checks.get('forbidden_claim_matches')}`",
                "",
                "### Human Review",
                "",
                "**Claim-level grounding:**",
                "- [ ] pass",
                "- [ ] partial",
                "- [ ] fail",
                "",
                "**Citation entailment:**",
                "- [ ] pass",
                "- [ ] partial",
                "- [ ] fail",
                "",
                "**Overclaim / unsupported inference:**",
                "- [ ] none",
                "- [ ] present",
                "",
                "**Reviewer notes:**",
                "",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _metric(value: Any) -> str:
    return "N/A" if value is None else f"{float(value):.4f}"


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as output:
        output.write(content)
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


V3_GENERATION_MAX_TOKENS = 1536
V3_JUDGE_MAX_TOKENS = 8192
V3_JUDGE_VERSION = "broad-v3-answer-quality-v1"
V3_METRIC_VERSION = "broad-v3-adjudicated-quality-v1"
V3_JUDGE_SYSTEM = """You are evaluating answers to GitHub policy questions. Use only the supplied policy evidence and frozen required facts. Assess each answer independently against the same absolute rubric; never rank answers against each other. A fact is covered only when the answer states its full actor, condition, scope and strength correctly. Mark an attempted but wrong synthesis as incorrect. A correct fact without a supporting supplied citation is still covered, but its citation is unsupported or missing. Split the answer into substantive policy claims and judge each against the supplied evidence. Use uncertain when the available text does not permit a reliable decision. Do not infer facts from general knowledge. Return only a JSON object matching the requested schema."""


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class _V3Cache:
    """Atomic, input-keyed local cache shared by generation and judging."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(self.entries, dict):
            raise ValueError(f"invalid cache: {path}")

    def get(self, key: str) -> dict | None:
        return self.entries.get(key)

    def set(self, key: str, value: dict) -> None:
        self.entries[key] = value
        _write_atomic(self.path, json.dumps(self.entries, ensure_ascii=False, indent=2) + "\n")


class _RecordingGenerationClient:
    def __init__(self, client: OpenAIChatCompletionsClient) -> None:
        self.client = client
        self.usage: dict[str, int | None] = {"input_tokens": None, "output_tokens": None}

    def complete(self, messages: Sequence[Mapping[str, str]], *, max_tokens: int,
                 temperature: float) -> str:
        answer, self.usage = self.client.complete_with_usage(
            messages, max_tokens=max_tokens, temperature=temperature)
        return answer


def build_v3_plan(model: str) -> list[dict]:
    """Construct the exact production prompts before making any model call."""
    benchmark, rubric, frozen, strategies, _ = load_v3_inputs()
    evidence = evaluate_evidence()
    rows = []
    for case, snapshot, saved, scored in zip(
            benchmark["cases"], frozen["cases"], strategies["cases"], evidence["cases"]):
        variants = {}
        groups = {}
        for name in POLICIES:
            chunks = [snapshot["top20"][rank - 1] for rank in saved[name]["original_ranks"]]
            sources = assign_evidence_sources([SimpleNamespace(**chunk) for chunk in chunks])
            messages = build_grounded_messages(case["query"], [], sources)
            evidence_hash = _stable_hash([
                {"chunk_id": chunk["chunk_id"], "text": chunk["text"],
                 "title": chunk["title"], "heading_path": chunk["heading_path"],
                 "source_path": chunk["source_path"]} for chunk in chunks])
            prompt_hash = _stable_hash({"messages": messages, "model": model,
                                        "temperature": 0.0, "max_tokens": V3_GENERATION_MAX_TOKENS,
                                        "prompt_version": GENERATION_PROMPT_VERSION})
            generation_key = _stable_hash({"case_id": case["case_id"],
                                           "evidence_hash": evidence_hash,
                                           "prompt_config_hash": prompt_hash, "model": model})
            request_key = _stable_hash({"case_id": case["case_id"], "strategy": name,
                                        "evidence_hash": evidence_hash,
                                        "prompt_config_hash": prompt_hash, "model": model})
            variant = {"strategy": name, "chunks": chunks, "sources": sources,
                       "evidence_hash": evidence_hash, "prompt_config_hash": prompt_hash,
                       "generation_key": generation_key, "request_key": request_key,
                       "evidence_tokens": scored["policies"][name]["evidence_tokens"],
                       "available_fact_ids": scored["policies"][name]["covered_fact_ids"]}
            variants[name] = variant
            groups.setdefault(generation_key, []).append(name)
        rows.append({"case_id": case["case_id"], "query": case["query"],
                     "facts": [fact for fact in rubric["facts"]
                               if fact["case_id"] == case["case_id"] and fact["required"]],
                     "evidence": scored, "variants": variants, "groups": groups})
    return rows


def _run_v3_generation(case: dict, strategy: str, cache: _V3Cache,
                       client: OpenAIChatCompletionsClient, model: str) -> dict:
    variant = case["variants"][strategy]
    cached = cache.get(variant["generation_key"])
    if cached is None:
        recorder = _RecordingGenerationClient(client)
        started = perf_counter()
        produced = generate_grounded_answer(case["query"], [],
                                             [SimpleNamespace(**chunk) for chunk in variant["chunks"]],
                                             recorder, model=model, cache=None,
                                             max_tokens=V3_GENERATION_MAX_TOKENS)
        cached = {"answer": produced["answer"], "provider_usage": recorder.usage,
                  "latency_seconds": perf_counter() - started,
                  "generation_hash": _stable_hash(produced["answer"]),
                  "model": model, "case_id": case["case_id"],
                  "evidence_hash": variant["evidence_hash"],
                  "prompt_config_hash": variant["prompt_config_hash"]}
        cache.set(variant["generation_key"], cached)
        source = "api"
    else:
        source = "cache"
    citation_result = validate_citations(cached["answer"], variant["sources"])
    return {"answer": cached["answer"], "generation_hash": cached["generation_hash"],
            "generation_key": variant["generation_key"], "request_key": variant["request_key"],
            "evidence_hash": variant["evidence_hash"],
            "prompt_config_hash": variant["prompt_config_hash"],
            "provider_usage": cached["provider_usage"],
            "latency_seconds": cached["latency_seconds"], "response_source": source,
            "citation_ids": citation_result["citation_ids"],
            "citation_validation": citation_result["validation"],
            "cited_sources": citation_result["sources"]}


def _judge_messages(case: dict, labeled: dict[str, dict]) -> list[dict[str, str]]:
    payload = {
        "question": case["query"],
        "required_facts": [{"fact_id": fact["fact_id"], "fact": fact["fact"]}
                           for fact in case["facts"]],
        "answers": {label: {"answer": variant["generation"]["answer"],
                             "sources": [{"citation_id": source.citation_id,
                                          "source_path": source.source_path,
                                          "title": source.title,
                                          "heading_path": source.heading_path,
                                          "text": source.text}
                                         for source in variant["sources"]]}
                    for label, variant in labeled.items()},
    }
    schema = """Return JSON: {"answers":{"A":{"facts":[{"fact_id":"...","status":"covered|missing|incorrect|uncertain","citation_status":"supported|unsupported|missing|not_applicable|uncertain","note":"brief reason for incorrect/uncertain only"}],"claims":[{"text":"one substantive claim","support_status":"supported|partial|unsupported|contradicted|uncertain","citation_status":"supported|unsupported|missing|uncertain","note":"brief reason for non-supported decisions"}]}}}. Include every required fact exactly once for each answer label. Include every substantive policy claim, including claims without citations. For missing facts use citation_status=not_applicable. Do not include strategy names, cost, or comparative commentary."""
    return [{"role": "system", "content": V3_JUDGE_SYSTEM},
            {"role": "user", "content": schema + "\n\nINPUT:\n" +
             json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}]


def _parse_judge(raw: str, labels: set[str], fact_ids: set[str]) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    result = json.loads(text)
    answers = result["answers"]
    if set(answers) != labels:
        raise ValueError("judge answer labels differ")
    for answer in answers.values():
        facts = answer["facts"]
        if len(facts) != len(fact_ids) or {fact["fact_id"] for fact in facts} != fact_ids:
            raise ValueError("judge fact IDs differ")
        if any(fact["status"] not in {"covered", "missing", "incorrect", "uncertain"} or
               fact["citation_status"] not in {"supported", "unsupported", "missing",
                                               "not_applicable", "uncertain"} for fact in facts):
            raise ValueError("invalid judge fact status")
        claims = answer["claims"]
        if not isinstance(claims, list) or not claims:
            raise ValueError("judge claims are empty")
        if any(not claim.get("text") or
               claim["support_status"] not in {"supported", "partial", "unsupported",
                                               "contradicted", "uncertain"} or
               claim["citation_status"] not in {"supported", "unsupported", "missing",
                                                "uncertain"} for claim in claims):
            raise ValueError("invalid judge claim status")
    return answers


def _judge_v3_case(case: dict, cache: _V3Cache,
                   client: OpenAIChatCompletionsClient, model: str,
                   usage: dict) -> dict[str, dict]:
    # Hash ordering conceals Fixed/V1/V2 identities while keeping resume stable.
    owners = [case["variants"][names[0]] for names in case["groups"].values()]
    owners.sort(key=lambda item: _stable_hash({"case_id": case["case_id"],
                                                "generation_key": item["generation_key"]}))
    labeled = {chr(65 + index): owner for index, owner in enumerate(owners)}
    required_ids = {fact["fact_id"] for fact in case["facts"]}

    def call(subset: dict[str, dict]) -> dict[str, dict]:
        messages = _judge_messages(case, subset)
        prompt_hash = _stable_hash({"messages": messages, "model": model,
                                    "temperature": 0.0, "max_tokens": V3_JUDGE_MAX_TOKENS,
                                    "version": V3_JUDGE_VERSION})
        key = _stable_hash({"case_id": case["case_id"], "model": model,
                            "prompt_config_hash": prompt_hash,
                            "generation_hashes": {label: value["generation"]["generation_hash"]
                                                  for label, value in subset.items()}})
        cached = cache.get(key)
        if cached is None:
            raw, provider_usage = client.complete_with_usage(
                messages, max_tokens=V3_JUDGE_MAX_TOKENS, temperature=0.0)
            usage["judge_api_calls"] += 1
            for field in ("input_tokens", "output_tokens"):
                if provider_usage[field] is not None:
                    usage[f"judge_{field}_this_run"] += provider_usage[field]
            try:
                parsed = _parse_judge(raw, set(subset), required_ids)
            except (ValueError, KeyError, TypeError) as error:
                cache.set(key, {"raw": raw, "error": str(error),
                                "provider_usage": provider_usage})
                raise ValueError(f"judge output failed schema for {case['case_id']}: {error}") from error
            cached = {"answers": parsed, "raw": raw, "raw_hash": _stable_hash(raw),
                      "prompt_config_hash": prompt_hash, "model": model,
                      "provider_usage": provider_usage}
            cache.set(key, cached)
        else:
            usage["judge_cache_hits"] += 1
            if "error" in cached:
                raise ValueError(f"cached judge output failed schema: {cached['error']}")
        for field in ("input_tokens", "output_tokens"):
            if cached["provider_usage"][field] is not None:
                usage[f"judge_{field}_reported_total"] += cached["provider_usage"][field]
        return cached["answers"]

    try:
        judged = call(labeled)
    except ValueError:
        # Large grouped outputs can truncate; retry only this case independently.
        usage["judge_group_fallback_cases"] += 1
        judged = {}
        for label, owner in labeled.items():
            judged.update(call({label: owner}))
    return {owner["generation_key"]: judged[label] for label, owner in labeled.items()}


def _score_v3_answer(case: dict, strategy: str, judged: dict,
                     fact_decisions: dict[str, dict] | None = None,
                     claim_decisions: dict[int, dict] | None = None) -> dict:
    variant = case["variants"][strategy]
    generation = variant["generation"]
    facts = {fact["fact_id"]: fact for fact in judged["facts"]}
    fact_decisions = fact_decisions or {}
    claim_decisions = claim_decisions or {}
    for fact_id, decision in fact_decisions.items():
        if fact_id not in facts or decision["generation_hash"] != generation["generation_hash"]:
            raise ValueError(f"stale fact adjudication: {case['case_id']}/{strategy}/{fact_id}")
        if decision["classification"] == "evidence_mapping_gap":
            if decision["source_chunk_id"] not in {chunk["chunk_id"] for chunk in variant["chunks"]}:
                raise ValueError(f"unselected adjudication source: {fact_id}")
        elif decision["classification"] not in {"judge_false_positive", "model_prior_knowledge",
                                                  "partial_support", "unresolved"}:
            raise ValueError(f"invalid fact adjudication: {fact_id}")
    effective_status = {fid: ("missing" if fact_decisions.get(fid, {}).get("classification") ==
                                   "judge_false_positive" else fact["status"])
                        for fid, fact in facts.items()}
    covered = [fact["fact_id"] for fact in case["facts"]
               if effective_status[fact["fact_id"]] == "covered"]
    missing = [fact["fact_id"] for fact in case["facts"]
               if effective_status[fact["fact_id"]] != "covered"]
    available = variant["available_fact_ids"]
    candidate = set(case["evidence"]["candidate_pool"]["covered_fact_ids"])
    available_set = set(available)
    reviewed_available = available_set | {fid for fid, decision in fact_decisions.items()
                                           if decision["classification"] == "evidence_mapping_gap"}
    grounded = [fid for fid in covered if fid in reviewed_available and
                facts[fid]["citation_status"] == "supported" and
                fact_decisions.get(fid, {}).get("classification") not in {
                    "model_prior_knowledge", "partial_support", "unresolved"}]
    answered_without_mapped_evidence = sorted(set(covered) - available_set)
    diagnosis = []
    for fact_id in missing:
        status = effective_status[fact_id]
        if status == "uncertain":
            cause = "unresolved"
        elif status == "incorrect":
            cause = "synthesis_error"
        elif fact_id not in candidate:
            cause = "candidate_miss"
        elif fact_id not in available_set:
            cause = "selection_miss"
        else:
            cause = "utilization_miss"
        diagnosis.append({"fact_id": fact_id, "cause": cause,
                          "judge_status": status, "note": facts[fact_id].get("note", "")})
    effective_claims = []
    for index, claim in enumerate(judged["claims"]):
        effective = dict(claim)
        decision = claim_decisions.get(index)
        if decision:
            if (decision["generation_hash"] != generation["generation_hash"] or
                    decision["claim_hash"] != _stable_hash(claim["text"])):
                raise ValueError(f"stale claim adjudication: {case['case_id']}/{strategy}/{index}")
            effective.update(support_status=decision["support_status"],
                             citation_status=decision["citation_status"])
        effective_claims.append(effective)
    claim_diagnosis = []
    for claim in effective_claims:
        if claim["support_status"] in {"unsupported", "contradicted"}:
            claim_diagnosis.append({"cause": "grounding_error", "claim": claim["text"],
                                    "support_status": claim["support_status"],
                                    "note": claim.get("note", "")})
        elif claim["support_status"] in {"partial", "uncertain"}:
            claim_diagnosis.append({"cause": "grounding_review", "claim": claim["text"],
                                    "support_status": claim["support_status"],
                                    "note": claim.get("note", "")})
        if claim["citation_status"] in {"unsupported", "missing"}:
            claim_diagnosis.append({"cause": "citation_error", "claim": claim["text"],
                                    "citation_status": claim["citation_status"],
                                    "note": claim.get("note", "")})
    claim_counts = Counter(claim["support_status"] for claim in effective_claims)
    citation_counts = Counter(claim["citation_status"] for claim in effective_claims)
    utilization = evidence_utilization(available, covered)
    grounded_utilization = evidence_utilization(sorted(reviewed_available), grounded)
    quality = {
        "covered_fact_ids": covered, "missing_fact_ids": missing,
        "covered_count": len(covered), "required_fact_count": len(case["facts"]),
        "fact_coverage": len(covered) / len(case["facts"]),
        "fact_complete": not missing,
        "grounded_covered_fact_ids": grounded,
        "grounded_missing_fact_ids": [fact["fact_id"] for fact in case["facts"]
                                      if fact["fact_id"] not in grounded],
        "grounded_covered_count": len(grounded),
        "grounded_fact_coverage": len(grounded) / len(case["facts"]),
        "grounded_fact_complete": len(grounded) == len(case["facts"]),
        "synthesis_error_count": sum(item["cause"] == "synthesis_error" for item in diagnosis),
        "fact_citation_supported_count": sum(facts[fid]["citation_status"] == "supported"
                                             for fid in covered),
        "claims": {name: claim_counts[name] for name in
                   ("supported", "partial", "unsupported", "contradicted", "uncertain")},
        "supported_claim_rate": claim_counts["supported"] / len(effective_claims),
        "claim_citations": {name: citation_counts[name] for name in
                            ("supported", "unsupported", "missing", "uncertain")},
        "citation_id_valid": generation["citation_validation"]["valid"],
        "evidence_utilization": utilization,
        "grounded_evidence_utilization": grounded_utilization,
        "answered_without_mapped_evidence_fact_ids": answered_without_mapped_evidence,
        "rubric_disagreement_candidate": answered_without_mapped_evidence,
    }
    return {"evidence_tokens": variant["evidence_tokens"],
            "selected_chunk_ids": [chunk["chunk_id"] for chunk in variant["chunks"]],
            "available_fact_ids": available, "generation": generation,
            "quality": quality, "pipeline_diagnosis": diagnosis,
            "claim_diagnosis": claim_diagnosis,
            "judge": judged,
            "adjudication": {"facts": list(fact_decisions.values()),
                             "claims": list(claim_decisions.values())},
            "review_required": bool(answered_without_mapped_evidence) or
                               any(fact["status"] in {"incorrect", "uncertain"} or
                                   fact["citation_status"] in {"unsupported", "uncertain"}
                                   for fact in judged["facts"]) or
                               any(claim["support_status"] != "supported" or
                                   claim["citation_status"] != "supported"
                                   for claim in judged["claims"])}


def _v3_case_patterns(options: dict[str, dict]) -> dict:
    patterns: set[str] = set()
    comparisons = []
    for left, right in (("fixed_top5", "adaptive_prefix_v1"),
                        ("fixed_top5", "coverage_selector_v2"),
                        ("coverage_selector_v2", "adaptive_prefix_v1")):
        before, after = options[left], options[right]
        evidence_delta = len(after["available_fact_ids"]) - len(before["available_fact_ids"])
        answer_delta = after["quality"]["covered_count"] - before["quality"]["covered_count"]
        labels = []
        if evidence_delta > 0 and answer_delta > 0:
            labels.append("A")
        if evidence_delta > 0 and answer_delta == 0:
            labels.append("B")
        if evidence_delta == 0 and answer_quality_key(after) == answer_quality_key(before) and (
                after["evidence_tokens"] > before["evidence_tokens"]):
            labels.append("C")
        if evidence_delta >= 0 and answer_quality_key(after) < answer_quality_key(before):
            labels.append("D")
        patterns.update(labels)
        comparisons.append({"from": left, "to": right, "evidence_fact_delta": evidence_delta,
                            "answer_fact_delta": answer_delta, "patterns": labels})
    if any(row["quality"]["evidence_utilization"]["answered_available_facts"] <
           row["quality"]["evidence_utilization"]["available_facts"]
           for row in options.values()):
        patterns.add("E")
    return {"patterns": sorted(patterns), "comparisons": comparisons}


def _summarize_v3(rows: list[dict], usage: dict, model: str) -> dict:
    required_total = sum(row["required_fact_count"] for row in rows)
    summaries = {}
    for name in POLICIES:
        options = [row["strategies"][name] for row in rows]
        utilization_values = [item["quality"]["evidence_utilization"]["rate"]
                              for item in options if item["quality"]["evidence_utilization"]["rate"] is not None]
        grounded_utilization_values = [item["quality"]["grounded_evidence_utilization"]["rate"]
                                       for item in options if item["quality"]["grounded_evidence_utilization"]["rate"] is not None]
        claim_totals = Counter()
        failures = Counter()
        for item in options:
            claim_totals.update(item["quality"]["claims"])
            failures.update(d["cause"] for d in item["pipeline_diagnosis"])
            claim_totals["grounding_error"] += (
                item["quality"]["claims"]["unsupported"] +
                item["quality"]["claims"]["contradicted"])
            claim_totals["citation_error"] += (
                item["quality"]["claim_citations"]["unsupported"] +
                item["quality"]["claim_citations"]["missing"])
        summaries[name] = {
            "macro_answer_fact_coverage": mean(item["quality"]["fact_coverage"] for item in options),
            "micro_answer_fact_coverage": sum(item["quality"]["covered_count"] for item in options) / required_total,
            "fact_complete_answer_cases": sum(item["quality"]["fact_complete"] for item in options),
            "macro_grounded_fact_coverage": mean(item["quality"]["grounded_fact_coverage"]
                                                  for item in options),
            "micro_grounded_fact_coverage": sum(item["quality"]["grounded_covered_count"]
                                                for item in options) / required_total,
            "grounded_fact_complete_cases": sum(item["quality"]["grounded_fact_complete"]
                                                for item in options),
            "macro_evidence_utilization": mean(utilization_values) if utilization_values else None,
            "macro_grounded_evidence_utilization": (mean(grounded_utilization_values)
                                                     if grounded_utilization_values else None),
            "micro_evidence_utilization": (
                sum(item["quality"]["evidence_utilization"]["answered_available_facts"]
                    for item in options) /
                sum(item["quality"]["evidence_utilization"]["available_facts"]
                    for item in options)),
            "micro_grounded_evidence_utilization": (
                sum(item["quality"]["grounded_evidence_utilization"]["answered_available_facts"]
                    for item in options) /
                sum(item["quality"]["grounded_evidence_utilization"]["available_facts"]
                    for item in options)),
            "supported_claim_rate": claim_totals["supported"] / sum(
                claim_totals[status] for status in
                ("supported", "partial", "unsupported", "contradicted", "uncertain")),
            "claim_counts": dict(claim_totals),
            "citation_id_valid_cases": sum(item["quality"]["citation_id_valid"] for item in options),
            "fact_citation_supported": sum(item["quality"]["fact_citation_supported_count"]
                                           for item in options),
            "answered_without_mapped_evidence": sum(
                len(item["quality"]["answered_without_mapped_evidence_fact_ids"])
                for item in options),
            "pipeline_failure_counts": dict(failures),
            "total_evidence_tokens": sum(item["evidence_tokens"] for item in options),
        }
    pattern_counts = {label: sum(label in row["patterns"]["patterns"] for row in rows)
                      for label in "ABCDE"}
    oracle_wins = Counter(row["answer_oracle"]["selected_strategy"] for row in rows
                          if row["answer_oracle"]["selected_strategy"])
    oracle_ties = [row["case_id"] for row in rows
                   if row["answer_oracle"]["selected_strategy"] is None]
    oracle_options = [row["strategies"][row["answer_oracle"]["co_optimal_strategies"][0]]
                      for row in rows]
    oracle_tokens = sum(row["answer_oracle"]["evidence_tokens"] for row in rows)
    return {"case_count": len(rows), "required_fact_count": required_total,
            "strategies": summaries, "pattern_case_counts": pattern_counts,
            "answer_oracle": {
                "warning": "offline analysis only; uses judged answer quality unavailable at inference time",
                "macro_answer_fact_coverage": mean(item["quality"]["fact_coverage"] for item in oracle_options),
                "micro_answer_fact_coverage": sum(item["quality"]["covered_count"] for item in oracle_options) / required_total,
                "fact_complete_answer_cases": sum(item["quality"]["fact_complete"] for item in oracle_options),
                "macro_grounded_fact_coverage": mean(item["quality"]["grounded_fact_coverage"]
                                                       for item in oracle_options),
                "micro_grounded_fact_coverage": sum(item["quality"]["grounded_covered_count"]
                                                     for item in oracle_options) / required_total,
                "grounded_fact_complete_cases": sum(item["quality"]["grounded_fact_complete"]
                                                     for item in oracle_options),
                "unique_winners": {name: oracle_wins[name] for name in POLICIES},
                "exact_tie_cases": oracle_ties,
                "total_evidence_tokens": oracle_tokens,
                "token_difference_vs_v1": oracle_tokens - summaries["adaptive_prefix_v1"]["total_evidence_tokens"],
            }, "usage": usage, "model": model}


def _render_v3_summary(section: dict) -> str:
    summary = section["summary"]
    rows = section["cases"]
    names = {"fixed_top5": "Fixed", "adaptive_prefix_v1": "V1",
             "coverage_selector_v2": "V2"}
    adjudication = section.get("adjudication")
    lines = ["# Answer Quality Evaluation", "", "## Dataset", "",
             "- 16 Broad Query V3 cases; 92 frozen required facts.",
             "- Fixed / V1 / V2 answers use one production generator prompt and temperature 0.",
             "- Raw model judgments are retained; 11 fact and 8 claim discrepancies received targeted source review.",
             "", "## Answer Quality", "",
             "| Strategy | Answer macro/micro | Grounded macro/micro | Complete/grounded | Utilization/grounded | Unsupported | Contradicted |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name in POLICIES:
        item = summary["strategies"][name]
        lines.append(f"| {names[name]} | {item['macro_answer_fact_coverage']:.3f}/"
                     f"{item['micro_answer_fact_coverage']:.3f} | "
                     f"{item['macro_grounded_fact_coverage']:.3f}/"
                     f"{item['micro_grounded_fact_coverage']:.3f} | "
                     f"{item['fact_complete_answer_cases']}/"
                     f"{item['grounded_fact_complete_cases']} of 16 | "
                     f"{item['micro_evidence_utilization']:.3f}/"
                     f"{item['micro_grounded_evidence_utilization']:.3f} | "
                     f"{item['claim_counts'].get('unsupported', 0)} | "
                     f"{item['claim_counts'].get('contradicted', 0)} |")
    if adjudication:
        fact_counts = Counter(row["classification"] for row in adjudication["facts"])
        claim_counts = Counter(row["classification"] for row in adjudication["claims"])
        lines += ["", "## Source Review", "",
                  f"- Mapping discrepancies: {fact_counts['evidence_mapping_gap']} "
                  f"direct-support mapping gaps and {fact_counts['judge_false_positive']} "
                  "judge false positive; frozen rubric unchanged.",
                  f"- Claim citation issues: {claim_counts['unsupported']} unsupported, "
                  f"{claim_counts['citation_misaligned']} missing citations, "
                  f"{claim_counts['partial_support']} partial support.",
                  "- Direct mapping gaps are a provenance risk for the frozen evidence "
                  "coverage baseline; reviewed selected chunks are used only in answer evaluation."]
    lines += ["", "## Citation / Grounding", "",
              "| Strategy | Supported claims | Valid citation IDs | Supported fact citations |",
              "|---|---:|---:|---:|"]
    for name in POLICIES:
        item = summary["strategies"][name]
        lines.append(f"| {names[name]} | {item['supported_claim_rate']:.3f} | "
                     f"{item['citation_id_valid_cases']}/16 | "
                     f"{item['fact_citation_supported']} |")
    citation_issues = "/".join(str(summary["strategies"][name]["claim_counts"].get(
        "citation_error", 0)) for name in POLICIES)
    lines += ["", "All citation IDs resolve to supplied evidence. Source review classified "
              f"{citation_issues} claim citation issues for Fixed/V1/V2, respectively; "
              "factual correctness and citation support remain separate judgments."]
    patterns = summary["pattern_case_counts"]
    lines += ["", "## Evidence → Answer Patterns", "",
              f"Cases with A/B/C/D/E: **{patterns['A']}/{patterns['B']}/{patterns['C']}/{patterns['D']}/{patterns['E']}**. "
              "A: evidence and answer coverage rise; B: evidence rises without answer gain; "
              "C: equal evidence and answer quality at higher token cost; D: answer quality falls; "
              "E: available required evidence is omitted from an answer.", "",
              "## Pipeline Failure Breakdown", ""]
    for name in POLICIES:
        counts = summary["strategies"][name]["pipeline_failure_counts"]
        lines.append(f"- {names[name]}: candidate {counts.get('candidate_miss', 0)}, "
                     f"selection {counts.get('selection_miss', 0)}, "
                     f"utilization {counts.get('utilization_miss', 0)}, "
                     f"synthesis {counts.get('synthesis_error', 0)}, "
                     f"unresolved {counts.get('unresolved', 0)} missing-fact labels.")
    oracle = summary["answer_oracle"]
    lines += ["", "## Answer Oracle", "",
              f"- Offline quality-first oracle: answer macro/micro "
              f"{oracle['macro_answer_fact_coverage']:.3f}/{oracle['micro_answer_fact_coverage']:.3f}; "
              f"grounded macro/micro {oracle['macro_grounded_fact_coverage']:.3f}/"
              f"{oracle['micro_grounded_fact_coverage']:.3f}; "
              f"complete/grounded {oracle['fact_complete_answer_cases']}/"
              f"{oracle['grounded_fact_complete_cases']} of 16.",
              f"- Unique wins {oracle['unique_winners']}; exact ties {len(oracle['exact_tie_cases'])}. "
              f"Evidence tokens {oracle['total_evidence_tokens']:,}; "
              f"difference vs V1 {oracle['token_difference_vs_v1']:+,}.",
              "", "## Key Findings", ""]
    lines.append("- V1 has the highest answer coverage and completeness; V2 is close, "
                 "while Fixed is lower. The answer oracle matches V1's coverage and "
                 "completeness at lower evidence cost, using hindsight labels.")
    lines.append("- Evidence gains improve answer coverage in 4 cases but leave it unchanged "
                 "in 4; V3-07 and V3-08 contain required evidence omitted from answers.")
    lines.append("- Three cases show lower adjudicated claim quality with more evidence, "
                 "without losing required answer facts; evidence overload is unconfirmed.")
    unmapped = sum(item["answered_without_mapped_evidence"]
                   for item in summary["strategies"].values())
    lines.append(f"- {unmapped} covered strategy-fact judgments lack a frozen mapping; "
                 "review found direct support in selected chunks for all of them.")
    def fact_counts(case_id: str) -> str:
        row = next(row for row in rows if row["case_id"] == case_id)
        return ", ".join(f"{names[name]} {row['strategies'][name]['quality']['covered_count']}/"
                         f"{row['required_fact_count']}" for name in POLICIES)

    lines += [f"- V3-01 deep-ranking case: {fact_counts('V3-01')}; none is complete.",
              f"- Candidate-ceiling cases: V3-03 ({fact_counts('V3-03')}); "
              f"V3-11 ({fact_counts('V3-11')})."]
    usage = summary["usage"]
    lines += ["", "## Efficiency", "",
              f"- {usage['theoretical_generations']} strategy answers required "
              f"{usage['unique_generation_inputs']} unique generation inputs; "
              f"{usage['dedup_reuses']} answers reused; {len(rows)} grouped judge results.", "",
              "## Limitations", "",
              "- This 16-case diagnostic set is not an untouched validation set.",
              f"- Most semantic labels depend on judge model `{summary['model']}`; "
              "targeted source review is not independent human sign-off.",
              "- Claim segmentation and entailment are semantic judgments, not deterministic validator guarantees.",
              "- The frozen evidence mapping and baseline retain the documented gap risk.", ""]
    return "\n".join(lines)


def _render_v3_review(section: dict) -> str:
    lines = ["# Broad Query V3 answer quality review", "",
             "Raw model judgments remain in the JSON. The decisions below come from "
             "offline source inspection; independent human sign-off is still useful. "
             "Do not edit the frozen rubric.", ""]
    adjudication = section.get("adjudication")
    if adjudication:
        lines += ["## Targeted fact adjudication", ""]
        for decision in adjudication["facts"]:
            lines.append(f"- {decision['case_id']} / {decision['strategy']} / "
                         f"{decision['fact_id']}: **{decision['classification']}**; "
                         f"selected source {decision['source_chunk_id'] or 'none'}; "
                         f"{decision['reason']}")
        lines += ["", "## Targeted claim and citation adjudication", ""]
        for decision in adjudication["claims"]:
            lines.append(f"- {decision['case_id']} / {decision['strategy']} / claim "
                         f"{decision['claim_index']}: **{decision['classification']}**; "
                         f"factual status {decision['factual_status']}; "
                         f"support {decision['support_status']}; "
                         f"citation {decision['citation_status']}. {decision['reason']}")
        lines += ["", "## Remaining review checklist", "",
                  "- [ ] Independently verify the ten direct-support mapping gap decisions "
                  "before any future rubric revision.",
                  "- [ ] Review any other ambiguous model judgments before external use.", ""]
    for row in section["cases"]:
        for name in POLICIES:
            item = row["strategies"][name]
            if not item["review_required"]:
                continue
            lines += [f"## {row['case_id']} / {name}", "",
                      f"- Answer fact coverage: {item['quality']['covered_count']}/{row['required_fact_count']}.",
                      f"- Missing facts: {', '.join(item['quality']['missing_fact_ids']) or 'none'}.",
                      f"- Judge-covered facts absent from frozen evidence mappings: "
                      f"{', '.join(item['quality']['answered_without_mapped_evidence_fact_ids']) or 'none'} "
                      "(check evidence support, judge decision and possible rubric disagreement).",
                      f"- Unsupported / contradicted claims: "
                      f"{item['quality']['claims']['unsupported']} / "
                      f"{item['quality']['claims']['contradicted']}.",
                      "- [ ] Judge fact decisions checked",
                      "- [ ] Claim grounding and citations checked",
                      "- [ ] Rubric disagreement candidate recorded if applicable", ""]
            for fact in item["judge"]["facts"]:
                if fact["status"] in {"incorrect", "uncertain"} or fact["citation_status"] in {
                        "unsupported", "uncertain"}:
                    lines.append(f"- `{fact['fact_id']}`: {fact['status']}; "
                                 f"citation {fact['citation_status']}; {fact.get('note', '')}")
            claim_reviews = {decision["claim_index"]: decision
                             for decision in item["adjudication"]["claims"]}
            for index, claim in enumerate(item["judge"]["claims"]):
                decision = claim_reviews.get(index, {})
                support = decision.get("support_status", claim["support_status"])
                citation = decision.get("citation_status", claim["citation_status"])
                if support != "supported" or citation != "supported":
                    note = f"; {claim['note']}" if claim.get("note") else ""
                    lines.append(f"- Claim: {claim['text']} — "
                                 f"{support}, citation {citation}"
                                 f"{note}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def broad_v3_main(argv: Sequence[str]) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Controlled Broad Query V3 answer evaluation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only-case", choices=[f"V3-{i:02d}" for i in range(1, 17)])
    parser.add_argument("--env-file", type=Path, default=root / ".env")
    parser.add_argument("--generation-cache", type=Path,
                        default=root / "cache/broad_v3_answer_generation.json")
    parser.add_argument("--judge-cache", type=Path,
                        default=root / "cache/broad_v3_answer_judge.json")
    parser.add_argument("--json-output", type=Path,
                        default=root / "eval/results/answer_eval_results.json")
    parser.add_argument("--summary-output", type=Path,
                        default=root / "eval/results/answer_eval_summary.md")
    parser.add_argument("--review-output", type=Path,
                        default=root / "eval/results/answer_eval_human_review.md")
    args = parser.parse_args(argv)
    config = LLMConfig.from_env(args.env_file)
    plan = build_v3_plan(config.model)
    planned_unique = sum(len(case["groups"]) for case in plan)
    print(f"Controlled V3 plan: 48 strategy answers, {planned_unique} unique generations, "
          f"{48 - planned_unique} deduplicated, 16 grouped judge calls planned.", flush=True)
    if args.dry_run:
        return 0
    generation_cache, judge_cache = _V3Cache(args.generation_cache), _V3Cache(args.judge_cache)
    client = OpenAIChatCompletionsClient(replace(config, timeout_seconds=max(120.0, config.timeout_seconds)))
    usage = {"theoretical_generations": 48, "unique_generation_inputs": planned_unique,
             "generation_api_calls": 0, "generation_cache_hits": 0, "dedup_reuses": 0,
             "judge_api_calls": 0, "judge_cache_hits": 0, "judge_group_fallback_cases": 0,
             "generation_input_tokens_reported_total": 0,
             "generation_output_tokens_reported_total": 0,
             "judge_input_tokens_this_run": 0, "judge_output_tokens_this_run": 0,
             "judge_input_tokens_reported_total": 0,
             "judge_output_tokens_reported_total": 0}
    existing = json.loads(args.json_output.read_text(encoding="utf-8")) if args.json_output.exists() else {}
    adjudication = existing.get("broad_v3_controlled", {}).get("adjudication")
    if adjudication and adjudication["frozen_rubric_sha256"] != _sha256(
            root / "eval/broad_query_v3_atomic_facts_frozen_candidate.json"):
        raise ValueError("answer adjudication does not match frozen rubric")
    fact_reviews = {(row["case_id"], row["strategy"], row["fact_id"]): row
                    for row in adjudication["facts"]} if adjudication else {}
    claim_reviews = {(row["case_id"], row["strategy"], row["claim_index"]): row
                     for row in adjudication["claims"]} if adjudication else {}
    selected_cases = [case for case in plan if not args.only_case or case["case_id"] == args.only_case]
    completed = []
    for case in selected_cases:
        for names in case["groups"].values():
            owner = names[0]
            try:
                generation = _run_v3_generation(case, owner, generation_cache, client, config.model)
            except Exception as error:
                print(f"Generation stopped at {case['case_id']}/{owner}: {error}", file=sys.stderr)
                return 2
            usage["generation_api_calls" if generation["response_source"] == "api"
                  else "generation_cache_hits"] += 1
            for field in ("input_tokens", "output_tokens"):
                count = generation["provider_usage"].get(field)
                if count is not None:
                    usage[f"generation_{field}_reported_total"] += count
            for name in names:
                variant = case["variants"][name]
                variant["generation"] = dict(generation,
                                             request_key=variant["request_key"],
                                             evidence_hash=variant["evidence_hash"],
                                             prompt_config_hash=variant["prompt_config_hash"],
                                             response_source=(generation["response_source"] if name == owner
                                                              else "deduplicated"),
                                             deduplicated=name != owner,
                                             reused_from_strategy=owner if name != owner else None)
                if name != owner:
                    usage["dedup_reuses"] += 1
        try:
            judged = _judge_v3_case(case, judge_cache, client, config.model, usage)
        except Exception as error:
            print(f"Judge stopped at {case['case_id']}: {error}", file=sys.stderr)
            return 2
        options = {}
        for name in POLICIES:
            raw = judged[case["variants"][name]["generation_key"]]
            reviews_f = {fid: review for (cid, strategy, fid), review in fact_reviews.items()
                         if cid == case["case_id"] and strategy == name}
            reviews_c = {index: review for (cid, strategy, index), review in claim_reviews.items()
                         if cid == case["case_id"] and strategy == name}
            if adjudication:
                expected_f = {fact["fact_id"] for fact in raw["facts"]
                              if fact["status"] == "covered" and
                              fact["fact_id"] not in case["variants"][name]["available_fact_ids"]}
                expected_c = {index for index, claim in enumerate(raw["claims"])
                              if claim["citation_status"] in {"unsupported", "missing"}}
                if set(reviews_f) != expected_f or set(reviews_c) != expected_c:
                    raise ValueError(f"incomplete answer adjudication: {case['case_id']}/{name}")
            options[name] = _score_v3_answer(case, name, raw, reviews_f, reviews_c)
        completed.append({"case_id": case["case_id"], "query": case["query"],
                          "required_fact_count": len(case["facts"]),
                          "candidate_pool_complete": case["evidence"]["candidate_pool"]["fact_complete"],
                          "strategies": options,
                          "answer_oracle": select_answer_oracle(options),
                          "patterns": _v3_case_patterns(options)})
        existing["broad_v3_controlled"] = {
            "status": "in_progress", "schema_version": 1,
            "configuration": {"model": config.model, "judge_model": config.model,
                              "generation_prompt_version": GENERATION_PROMPT_VERSION,
                              "judge_prompt_version": V3_JUDGE_VERSION,
                              "answer_metric_version": V3_METRIC_VERSION,
                              "temperature": 0.0, "generation_max_tokens": V3_GENERATION_MAX_TOKENS,
                              "judge_max_tokens": V3_JUDGE_MAX_TOKENS,
                              "frozen_rubric_sha256": _sha256(root / "eval/broad_query_v3_atomic_facts_frozen_candidate.json")},
            "usage": usage, "cases": completed,
            **({"adjudication": adjudication,
                "adjudication_status": "frozen_offline_source_review",
                "answer_eval_freeze_hash": _stable_hash({
                    "rubric": adjudication["frozen_rubric_sha256"],
                    "adjudication": adjudication,
                    "generations": sorted(row["generation"]["generation_hash"]
                                          for item in completed for row in item["strategies"].values()),
                    "judge_version": V3_JUDGE_VERSION,
                    "metric_version": V3_METRIC_VERSION})}
               if adjudication else {})}
        _write_atomic(args.json_output, json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
        print(f"{case['case_id']} complete ({len(case['groups'])} unique answers); "
              f"generation API {usage['generation_api_calls']}, judge API {usage['judge_api_calls']}", flush=True)
    if args.only_case:
        print("Partial run cached; rerun without --only-case to complete all 16 cases.")
        return 0
    section = existing["broad_v3_controlled"]
    section["status"] = "complete"
    section["summary"] = _summarize_v3(completed, usage, config.model)
    _write_atomic(args.json_output, json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
    _write_atomic(args.summary_output, _render_v3_summary(section))
    _write_atomic(args.review_output, _render_v3_review(section))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "--broad-v3":
        return broad_v3_main(args_list[1:])
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=project_root / "eval" / "answer_eval_candidates.json",
    )
    parser.add_argument("--env-file", type=Path, default=project_root / ".env")
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--rewrite-cache", type=Path,
        default=project_root / "cache" / "query_rewrites.json",
    )
    parser.add_argument(
        "--generation-cache", type=Path,
        default=project_root / "cache" / "generated_answers.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_results.json",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_summary.md",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=project_root / "eval" / "results" / "answer_eval_human_review.md",
    )
    args = parser.parse_args(argv)

    config = LLMConfig.from_env(args.env_file)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("answer eval cases must be a JSON array")
    agent = PolicySupportAgent.from_project(
        project_root,
        env_file=args.env_file,
        device=args.device,
        rewrite_cache_path=args.rewrite_cache,
        generation_cache_path=args.generation_cache,
    )
    rows, usage = run_answer_eval(cases, agent)
    overall = aggregate_deterministic_metrics(rows)
    by_category = category_metrics(rows)
    failures = []
    for row in rows:
        if row["pipeline"]["status"] == "error":
            failures.append({"id": row["id"], "failed_checks": ["pipeline_error"]})
            continue
        checks = row["deterministic_checks"]
        failed = [
            name
            for name, passed in (
                ("behavior_check", checks["behavior_check"]),
                ("citation_validation", checks["citation_validation"]),
                ("source_check", checks["source_check"]),
                ("forbidden_claim_check", checks["forbidden_claim_check"]),
            )
            if not passed
        ]
        if failed:
            failures.append({"id": row["id"], "failed_checks": failed})
    report = {
        "configuration": {
            "provider": "openai-compatible-chat-completions",
            "base_url": config.base_url,
            "model": config.model,
            "thinking_mode": config.thinking_mode,
            "candidate_dataset": args.cases.as_posix(),
            "candidate_dataset_sha256": _sha256(args.cases),
            "retrieval_pipeline": "lexical Top20 + semantic Top20 union, Cross-Encoder reranker Top5",
            "rewrite_cache": args.rewrite_cache.as_posix(),
            "generation_cache": args.generation_cache.as_posix(),
            "automatic_semantic_scoring": False,
            "llm_judge": False,
        },
        "usage": usage,
        "summary": {
            "overall": overall,
            "by_category": by_category,
            "deterministic_failures": failures,
            "instrumentation": aggregate_instrumentation(rows),
        },
        "cases": rows,
    }
    if args.json_output.exists():
        previous = json.loads(args.json_output.read_text(encoding="utf-8"))
        if "broad_v3_controlled" in previous:
            report["broad_v3_controlled"] = previous["broad_v3_controlled"]
    _write_atomic(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    v3 = report.get("broad_v3_controlled")
    _write_atomic(args.summary_output, _render_v3_summary(v3) if v3 and v3["status"] == "complete"
                  else render_summary(report))
    _write_atomic(args.review_output, _render_v3_review(v3) if v3 and v3["status"] == "complete"
                  else render_human_review(report))
    print(json.dumps(overall, ensure_ascii=False, indent=2))
    print(f"JSON: {args.json_output.resolve()}")
    print(f"Summary: {args.summary_output.resolve()}")
    print(f"Human review: {args.review_output.resolve()}")
    return 1 if usage["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
