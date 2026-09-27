"""Prepare a blinded random answer-judge audit and run the frozen cross-family judge."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import subprocess
from pathlib import Path

from eval.core.benchmark import PROJECT_ROOT, load_benchmark


SEED = 20260927
CASE_COUNT = 15
MODEL = "gpt-5.6-sol"
CODEX_FALLBACK = Path.home() / ".codex" / ".sandbox-bin" / "codex.exe"
OUTPUT = PROJECT_ROOT / "eval" / "results" / "judge_calibration_v1"
PACKET = PROJECT_ROOT / "eval" / "judge_calibration_v1_human_review.md"
GENERATION = PROJECT_ROOT / "eval" / "results" / "query_aware_stage1_generation_results.json"
QUALITY = PROJECT_ROOT / "eval" / "results" / "a1_blind_answer_quality_frozen_v1.json"
LABELS = PROJECT_ROOT / "eval" / "results" / "frozen_human_verdicts_v1.json"

PROMPT_RULES = """You are an independent answer-aspect judge. Use only the supplied JSON input.
Do not inspect files, use tools, or use any prior conversation. Judge exactly one required aspect.
Question: Does the candidate ANSWER ITSELF actually express the required information?
COVERED means the answer fully states the required condition, exception, process step, or fact; a complete paraphrase is fine.
MISSING means the answer omits it, weakens a required condition, only vaguely mentions the topic, leaves it only in citations/source text, or requires inference from common knowledge.
AMBIGUOUS is only for a genuinely unstable call under the frozen criterion and source.
The source excerpt explains the criterion but is not part of the candidate answer. Ignore style.
Return only JSON with keys verdict (COVERED, MISSING, or AMBIGUOUS) and brief_reason (at most 25 words).
"""


def codex_executable() -> str:
    candidate = shutil.which("codex") or str(CODEX_FALLBACK)
    if not Path(candidate).is_file():
        raise FileNotFoundError(f"codex CLI not found on PATH or at {CODEX_FALLBACK}")
    return candidate


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_case_ids(case_ids: list[str]) -> list[str]:
    return sorted(random.Random(SEED).sample(sorted(case_ids), CASE_COUNT))


def _citation_map(citations: list[dict]) -> list[dict]:
    return sorted(({
        "citation_id": row["citation_id"],
        "title": row.get("title", ""),
        "section": " > ".join(row.get("heading_path", [])),
        "source_url": row.get("source_url", ""),
    } for row in citations), key=lambda row: row["citation_id"])


def prepare() -> tuple[dict, dict, str]:
    benchmark = load_benchmark("validation_v1")
    if len(benchmark.cases) != 50 or sum(len(c.query_required_aspects) for c in benchmark.cases) != 208:
        raise ValueError("canonical benchmark identity changed")
    chosen = sample_case_ids([case.case_id for case in benchmark.cases])
    generation = _read(GENERATION)
    answers = {row["case_id"]: row for row in generation["cases"] if row["arm"] == "fixed_top5"}
    if len(answers) != 50:
        raise ValueError("expected exactly one fixed Top5 answer per case")
    cases = {case.case_id: case for case in benchmark.cases}
    items: list[dict] = []
    packet_lines = [
        "# Judge calibration v1 — blinded project-author review",
        "",
        "Review the candidate answer against every listed required criterion. Sources clarify the criterion;",
        "a fact appearing only in a source or citation is not covered by the answer. For each review ID,",
        "replace `PENDING` with exactly `COVERED`, `MISSING`, or `AMBIGUOUS`. Optionally add a brief reason.",
        "Do not consult model verdicts while filling this packet. Leave all other text unchanged.",
        "",
    ]
    number = 0
    for case_id in chosen:
        case = cases[case_id]
        row = answers[case_id]
        citation_map = _citation_map(row.get("citations", []))
        packet_lines += [f"## {case_id}", "", "**User query:**", "", case.query, "", "**Candidate answer:**", "", "````text", row["answer"], "````", "", "**Citation map (only citations used in the answer):**", ""]
        if citation_map:
            packet_lines.extend(f"- [{c['citation_id']}] {c['title']} — {c['section']} — {c['source_url']}" for c in citation_map)
        else:
            packet_lines.append("- None cited")
        packet_lines.append("")
        facts = {fact.fact_id: fact for fact in case.original_rubric_facts}
        for aspect_id in case.query_required_aspects:
            number += 1
            fact = facts[aspect_id]
            sources = [{"document": support.get("document", ""), "section": support.get("section", ""),
                        "source_excerpt": support.get("source_excerpt", ""),
                        "context_excerpt": support.get("context_excerpt", "")}
                       for support in fact.support]
            item = {"review_id": f"JC-{number:03d}", "case_id": case_id, "aspect_id": aspect_id,
                    "query": case.query, "required_aspect": fact.statement, "candidate_answer": row["answer"],
                    "supporting_sources": sources, "citation_map": citation_map}
            items.append(item)
            packet_lines += [f"### {item['review_id']} · {aspect_id}", "", f"**Required aspect:** {fact.statement}", "", "**Supporting source excerpt(s):**", ""]
            for source in sources:
                packet_lines += [f"- {source['document']} · {source['section']}", "", "````text", source["source_excerpt"], "````", ""]
                if source["context_excerpt"]:
                    packet_lines += ["Context excerpt:", "", "````text", source["context_excerpt"], "````", ""]
            packet_lines += [f"**{item['review_id']} verdict:** PENDING", f"**{item['review_id']} brief_reason:**", ""]
    if len(items) != 60:
        raise ValueError(f"frozen sample expected 60 aspects, got {len(items)}")
    sample = {"version": "judge-calibration-v1", "random_seed": SEED,
              "sampling": "15 of 50 case IDs, uniform without replacement; all QUERY_REQUIRED aspects",
              "case_ids": chosen, "sampled_cases": 15, "sampled_judgments": len(items),
              "universe_cases": 50, "universe_judgments": 208,
              "source_sha256": {"quality": _sha(QUALITY), "generation": _sha(GENERATION), "labels": _sha(LABELS)},
              "items": [{"review_id": item["review_id"], "case_id": item["case_id"], "aspect_id": item["aspect_id"]} for item in items]}
    judge_inputs = {"version": "judge-calibration-v1-inputs", "items": items}
    packet = "\n".join(packet_lines).rstrip() + "\n"
    forbidden = ("judge_status", "historical score", "cross-family verdict", "fixed_top5", "MiniLM", "BGE")
    if any(token in packet for token in forbidden):
        raise ValueError("review packet contains blinded metadata")
    return sample, judge_inputs, packet


def judge_prompt(item: dict) -> str:
    allowed = {key: item[key] for key in ("query", "required_aspect", "candidate_answer", "supporting_sources", "citation_map")}
    return PROMPT_RULES + "\nINPUT JSON:\n" + json.dumps(allowed, ensure_ascii=False, separators=(",", ":"))


def judge_batch_prompt(items: list[dict]) -> str:
    allowed = [{key: item[key] for key in ("query", "required_aspect", "candidate_answer", "supporting_sources", "citation_map")}
               for item in items]
    rules = (PROMPT_RULES.replace("Judge exactly one required aspect.", "Judge every required aspect separately, in input order.")
             .replace("Return only JSON with keys verdict (COVERED, MISSING, or AMBIGUOUS) and brief_reason (at most 25 words).",
                      "For each item, use verdict COVERED, MISSING, or AMBIGUOUS and brief_reason of at most 25 words."))
    return (rules
            + "\nReturn JSON with a judgments array. Each entry has a 1-based index in this batch, verdict, and brief_reason. "
              "Return exactly one entry per input item; do not omit or merge items.\nINPUT JSON ARRAY:\n"
            + json.dumps(allowed, ensure_ascii=False, separators=(",", ":")))


def run_cross_family() -> None:
    sample = _read(OUTPUT / "sample.json")
    inputs = _read(OUTPUT / "judge_inputs.json")
    if len(sample["items"]) != 60 or len(inputs["items"]) != 60:
        raise ValueError("sample and judge inputs must contain all 60 frozen items")
    schema_path = OUTPUT / "cross_family_schema.json"
    _write(schema_path, {"type": "object", "properties": {"judgments": {"type": "array", "minItems": 20,
        "maxItems": 20, "items": {"type": "object", "properties": {
            "index": {"type": "integer", "minimum": 1, "maximum": 20},
            "verdict": {"type": "string", "enum": ["COVERED", "MISSING", "AMBIGUOUS"]},
            "brief_reason": {"type": "string"}},
            "required": ["index", "verdict", "brief_reason"], "additionalProperties": False}}},
        "required": ["judgments"], "additionalProperties": False})
    output_path = OUTPUT / "cross_family_judgments.json"
    saved = _read(output_path) if output_path.exists() else {"version": "judge-calibration-v1", "model": MODEL,
        "prompt_rules_sha256": hashlib.sha256(PROMPT_RULES.encode("utf-8")).hexdigest(),
        "sample_sha256": _sha(OUTPUT / "sample.json"), "status": "in_progress", "judgments": []}
    completed = {row["review_id"] for row in saved["judgments"]}
    if saved["sample_sha256"] != _sha(OUTPUT / "sample.json"):
        raise ValueError("sample hash changed during cross-family judging")
    for batch_number in range(3):
        batch = inputs["items"][batch_number * 20:(batch_number + 1) * 20]
        if len(batch) != 20:
            raise ValueError("frozen batch size changed")
        if all(item["review_id"] in completed for item in batch):
            continue
        if any(item["review_id"] in completed for item in batch):
            raise ValueError("partially saved batch cannot be silently rerun")
        response_path = OUTPUT / f"batch_{batch_number + 1:02d}_response.json"
        command = [codex_executable(), "exec", "--model", MODEL, "--ephemeral", "--ignore-user-config",
                   "--ignore-rules", "--sandbox", "read-only", "--skip-git-repo-check",
                   "--output-schema", str(schema_path), "--output-last-message", str(response_path), "-"]
        prompt = judge_batch_prompt(batch)
        result = subprocess.run(command, input=prompt, text=True, encoding="utf-8", errors="replace", capture_output=True,
                                cwd=OUTPUT, timeout=420, check=False)
        if result.returncode != 0 or not response_path.exists():
            raise RuntimeError(f"batch {batch_number + 1}: cross-family invocation failed ({result.returncode}): {result.stderr[-1000:]}")
        raw = response_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        judgments = parsed.get("judgments")
        if not isinstance(judgments, list) or len(judgments) != 20 or {row.get("index") for row in judgments} != set(range(1, 21)):
            raise ValueError(f"batch {batch_number + 1}: missing or duplicate output indexes")
        for row in sorted(judgments, key=lambda value: value["index"]):
            item = batch[row["index"] - 1]
            if row.get("verdict") not in {"COVERED", "MISSING", "AMBIGUOUS"} or not isinstance(row.get("brief_reason"), str):
                raise ValueError(f"{item['review_id']}: invalid judge response")
            saved["judgments"].append({"review_id": item["review_id"], "case_id": item["case_id"],
                "aspect_id": item["aspect_id"], "verdict": row["verdict"],
                "brief_reason": row["brief_reason"],
                "batch": batch_number + 1,
                "input_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()})
        completed.update(item["review_id"] for item in batch)
        _write(output_path, saved)
        print(f"batch {batch_number + 1}: 20 judgments complete", flush=True)
    saved["status"] = "complete"
    _write(output_path, saved)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "judge"))
    args = parser.parse_args()
    if args.command == "prepare":
        sample, inputs, packet = prepare()
        if (OUTPUT / "sample.json").exists():
            raise FileExistsError("frozen calibration sample already exists")
        _write(OUTPUT / "sample.json", sample)
        _write(OUTPUT / "judge_inputs.json", inputs)
        PACKET.write_text(packet, encoding="utf-8")
        print(f"prepared {sample['sampled_judgments']} judgments across {sample['sampled_cases']} cases")
    else:
        run_cross_family()


if __name__ == "__main__":
    main()
