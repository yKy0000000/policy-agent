"""Render editorial README figures from consolidated frozen results.

This is a presentation script. It performs no evaluation or model calls.
Run from the project root with a Python installation containing Pillow.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "eval" / "reports" / "research_v1"
OUT = FINAL / "figures"
OUT.mkdir(exist_ok=True)

METRICS = json.loads((FINAL / "final_metrics.json").read_text(encoding="utf-8"))
FAILURE = json.loads((FINAL / "failure_analysis.json").read_text(encoding="utf-8"))
CASE = json.loads((FINAL / "a2_case_study.json").read_text(encoding="utf-8"))
PROBE = json.loads((ROOT / "eval" / "results" / "a2_minimal_mechanism_probe_v1.json").read_text(encoding="utf-8"))

INK = "#15283A"
MUTED = "#4A6070"
RULE = "#C9D3D9"
LIGHT = "#F3F6F7"
TEAL = "#087F77"
TEAL_BG = "#E3F3F0"
RED = "#AF483E"
RED_BG = "#FAECE9"
BLUE = "#315F9C"
BLUE_BG = "#EAF0F9"
GRAY = "#677783"
WHITE = "#FFFFFF"


class Figure:
    def __init__(self, name: str, width: int, height: int):
        self.name, self.width, self.height = name, width, height
        self.scale = 3
        self.im = Image.new("RGB", (width * self.scale, height * self.scale), WHITE)
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', f'<rect width="{width}" height="{height}" fill="{WHITE}"/>']

    def font(self, size: int, bold: bool = False):
        candidates = (
            ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/NotoSansSC-VF.ttf"]
            if bold else
            ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/NotoSansSC-VF.ttf"]
        )
        path = next((Path(candidate) for candidate in candidates if Path(candidate).exists()), None)
        if path is None:
            raise FileNotFoundError("A Chinese-capable font is required to render reader figures")
        return ImageFont.truetype(str(path), size * self.scale)

    def rect(self, x, y, w, h, fill, stroke=None, radius=0, sw=1):
        box = tuple(int(v * self.scale) for v in (x, y, x + w, y + h))
        self.draw.rounded_rectangle(box, radius=radius * self.scale, fill=fill, outline=stroke, width=sw * self.scale)
        extra = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"{extra}/>')

    def line(self, x1, y1, x2, y2, color=RULE, sw=1):
        self.draw.line(tuple(int(v * self.scale) for v in (x1, y1, x2, y2)), fill=color, width=sw * self.scale)
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"/>')

    def circle(self, x, y, r, fill, stroke=None, sw=1):
        box = tuple(int(v * self.scale) for v in (x-r, y-r, x+r, y+r))
        self.draw.ellipse(box, fill=fill, outline=stroke, width=sw * self.scale)
        extra = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{extra}/>')

    def text(self, x, y, value, size=20, color=INK, bold=False, anchor="left"):
        value = str(value)
        f = self.font(size, bold)
        bb = self.draw.textbbox((0, 0), value, font=f)
        width = (bb[2] - bb[0]) / self.scale
        px = x if anchor == "left" else x - width if anchor == "right" else x - width / 2
        self.draw.text((int(px * self.scale), int(y * self.scale)), value, font=f, fill=color)
        svg_anchor = {"left": "start", "right": "end", "center": "middle"}[anchor]
        weight = "700" if bold else "400"
        self.svg.append(f'<text x="{x}" y="{y + size * .94:.1f}" fill="{color}" font-family="Microsoft YaHei, Noto Sans SC, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{svg_anchor}">{escape(value)}</text>')

    def save(self):
        self.im.save(OUT / f"{self.name}.png", optimize=True, dpi=(216, 216))
        (OUT / f"{self.name}.svg").write_text("\n".join(self.svg + ["</svg>"]), encoding="utf-8")


def header(f: Figure, eyebrow: str, title: str, subtitle: str):
    f.text(54, 28, eyebrow.upper(), 15, TEAL, True)
    f.text(54, 61, title, 34, INK, True)
    f.text(54, 112, subtitle, 19, MUTED)
    f.line(54, 152, f.width - 54, 152, RULE, 1)


def router_figure():
    f = Figure("router_decision_zh", 1200, 748)
    selector = METRICS["a1"]["coverage_selector_v2"]
    router = METRICS["a1"]["query_router_v1"]
    if not METRICS["a1_strict_dominance"]["coverage_selector_v2_dominates_query_router_v1"]:
        raise ValueError("Frozen A1 result no longer supports the dominance annotation")
    header(f, "A1 / 上下文分配", "为何删除 Router？", "Selector 与 Router 答案质量相同，但前者成本更低、确认回归与 grounding 问题更少。")
    f.text(55, 174, "策略", 15, MUTED, True)
    f.text(383, 174, "每题 Provider tokens", 15, MUTED, True)
    f.text(967, 174, "完整回答", 15, MUTED, True)
    f.text(1117, 174, "定位", 15, MUTED, True, "right")
    arms = [
        ("fixed_top5", "Fixed Top5", GRAY, "成本端点"),
        ("coverage_selector_v2", "coverage_selector_v2", TEAL, "主对比"),
        ("query_router_v1", "query_router_v1", RED, "淘汰"),
        ("no_router_adaptive_v1", "No-router adaptive", BLUE, "质量端点"),
    ]
    x0, x1 = 383, 904
    for i, (key, label, color, role) in enumerate(arms):
        y = 226 + i * 76
        d = METRICS["a1"][key]
        if key in ("coverage_selector_v2", "query_router_v1"):
            f.rect(48, y - 10, 1090, 57, TEAL_BG if key == "coverage_selector_v2" else RED_BG, radius=7)
        f.text(56, y, label, 21 if key == "coverage_selector_v2" else 22, color, True)
        f.rect(x0, y + 5, x1 - x0, 17, LIGHT, radius=8)
        bar = (x1-x0) * d["tokens_per_query"] / 6500
        f.rect(x0, y + 5, bar, 17, color, radius=8)
        f.text(x0 + bar + 10, y - 1, f'{d["tokens_per_query"]:,.0f}', 19, INK, True)
        f.text(978, y, f'{d["complete"]}/{d["cases"]}', 22, INK, True)
        f.text(1131, y + 2, role, 17, color, True, "right")
    f.line(54, 526, 1146, 526, RULE)
    f.text(54, 544, "Selector 严格支配 Router", 22, INK, True)
    f.text(54, 581, "答案质量相同", 16, MUTED, True)
    f.text(54, 608, f'完整回答 {selector["complete"]}/{selector["cases"]} · 必需信息点 {selector["required_covered"]}/{selector["required_total"]}', 18, INK)
    f.text(480, 581, "成本更低", 16, MUTED, True)
    f.text(480, 608, f'{selector["tokens_per_query"]:,.0f} vs {router["tokens_per_query"]:,.0f} tokens/query', 18, INK)
    f.text(846, 581, "风险更少", 16, MUTED, True)
    f.text(846, 608, f'确认回归 {selector["confirmed_regressions"]} vs {router["confirmed_regressions"]}', 18, INK)
    f.text(846, 638, f'正确性/grounding 问题 {selector["correctness_grounding_issues"]} vs {router["correctness_grounding_issues"]}', 16, INK)
    f.line(54, 689, 1146, 689, RULE)
    f.text(54, 702, "严格支配同时依据答案覆盖、完整率、回归与 grounding；成本条形图不是唯一判据。", 16, MUTED)
    f.text(54, 726, "来源：eval/reports/research_v1/final_metrics.json · 冻结 A1 Pareto", 14, MUTED)
    f.save()


def failure_figure():
    f = Figure("failure_roadmap_zh", 1200, 744)
    counts = FAILURE["taxonomy_counts"]
    totals = FAILURE["totals"]
    if "zero fragmentation cases" not in FAILURE["interpretation"]:
        raise ValueError("Frozen failure analysis no longer confirms zero fragmentation cases")
    fragmentation_count = 0
    priority_count = counts["GENERATION_MISS"] + counts["SELECTION_BUDGET"]
    header(f, "A1 / 剩余失败复盘", "剩余问题集中在生成与证据选择", f'{len(totals["per_arm_missing"])} 种保留策略中至少一种漏掉的 {totals["aspects_missing_in_at_least_one_arm"]} 个 QUERY_REQUIRED 信息点；共涉及 {totals["distinct_cases_with_residual_failure"]} 题。')
    f.rect(52, 175, 735, 166, TEAL_BG, radius=9)
    rows = [
        ("GENERATION_MISS", "生成遗漏", TEAL),
        ("SELECTION_BUDGET", "选择 / 预算", TEAL),
        ("RANKING_WEAKNESS", "排序偏弱", GRAY),
        ("REPRESENTATION_CANDIDATE", "Query 表示问题", BLUE),
        (None, "确认的 fragmentation", RED),
    ]
    for i, (key, label, color) in enumerate(rows):
        y = 196 + i * 91
        n = counts[key] if key else fragmentation_count
        f.text(68, y - 4 if key == "REPRESENTATION_CANDIDATE" else y, label, 21, INK, i < 2)
        if key == "REPRESENTATION_CANDIDATE":
            f.text(68, y + 24, "(representation)", 15, MUTED)
        f.rect(355, y + 5, 381, 20, LIGHT, radius=9)
        if n:
            f.rect(355, y + 5, 381*n/6, 20, color, radius=9)
        else:
            f.line(355, y + 16, 736, y + 16, RULE, 2)
        f.text(755, y - 2, str(n), 25, color, True)
    f.rect(827, 193, 313, 118, TEAL_BG, radius=9)
    f.text(846, 206, f'{priority_count} / {totals["aspects_missing_in_at_least_one_arm"]}', 43, TEAL, True)
    f.text(846, 267, "属于生成或选择 / 预算", 17, INK, True)
    f.text(827, 352, "下一步的依据", 16, MUTED, True)
    f.text(827, 389, "优先改进证据使用", 19, INK)
    f.text(827, 419, "与 context allocation。", 19, INK)
    f.text(827, 468, "仅一例明确的表示问题", 18, BLUE, True)
    f.text(827, 496, "支持小规模 A2 机制验证。", 18, INK)
    f.text(827, 550, f'Fragmentation：{fragmentation_count}', 18, RED, True)
    f.text(827, 578, "A3 hierarchical retrieval 不触发。", 16, INK)
    f.line(54, 669, 1146, 669, RULE)
    representation_cases = FAILURE["taxonomy_cases"]["REPRESENTATION_CANDIDATE"]
    f.text(54, 681, f'计数为不同信息点，不是各策略遗漏数之和；{counts["REPRESENTATION_CANDIDATE"]} 个表示问题信息点同属 {representation_cases[0]}。', 16, MUTED)
    f.text(54, 713, "来源：eval/reports/research_v1/failure_analysis.json", 14, MUTED)
    f.save()


def decomposition_figure():
    f = Figure("decomposition_case_zh", 1200, 729)
    strategies = {item["strategy"]: item for item in CASE["strategies"]}
    deeper = strategies["Deeper original"]
    requirement = strategies["Requirement query"]
    select_k = PROBE["environment"]["select_k"]
    if PROBE["environment"]["generation_calls"] != 0:
        raise ValueError("Frozen A2 probe unexpectedly contains answer generation")
    header(f, f'A2 / {CASE["case_id"]}', "Requirement Query 找回原问题遗漏的证据", f'相同的 {select_k} 个 chunk 上下文预算；只验证 retrieval/context 机制，没有生成新答案。')
    f.text(54, 173, "策略", 15, MUTED, True)
    f.text(386, 173, "目标来源在 BGE 排序中的位置（越靠前越好）", 15, MUTED, True)
    f.text(1129, 173, "必需证据", 15, MUTED, True, "right")
    xa, xb = 385, 913
    rankx = lambda rank: xa + (rank - 1) / (deeper["order_size"] - 1) * (xb-xa)
    for rank, label in [(1,"1"),(select_k,str(select_k)),(PROBE["environment"]["deep_k"],str(PROBE["environment"]["deep_k"])),(deeper["order_size"],str(deeper["order_size"]))]:
        x = rankx(rank)
        f.line(x, 225, x, 570, RULE, 1)
        f.text(x, 198, label, 16, MUTED, False, "center")
    for i, item in enumerate(CASE["strategies"]):
        y = 228 + i * 91
        strat = item["strategy"]
        if strat == "Requirement query":
            f.rect(48, y - 8, 1095, 69, TEAL_BG, radius=9)
        labels = {"Original query": "原始问题", "Deeper original": "加深检索", "MMR / diversity": "MMR / diversity", "Requirement query": "Requirement Query"}
        f.text(60, y+7, labels[strat], 21, TEAL if item["selected"] else INK, item["selected"])
        rank = item["bge_rank"]
        if rank is None:
            f.text(385, y+7, "候选池中缺失", 18, RED, True)
        else:
            x = rankx(rank)
            f.circle(x, y+22, 9, TEAL if item["selected"] else RED)
            if strat == "Deeper original":
                f.text(x-15, y+3, f'第 {rank} / {item["order_size"]} 名', 19, RED, True, "right")
            else:
                f.text(x+18, y+3, f'第 {rank} 名 · 进入 Top{select_k}', 19, TEAL, True)
        f.text(1109, y+5, item["coverage"], 26, TEAL if item["selected"] else MUTED, True, "right")
    f.line(54, 609, 1146, 609, RULE)
    f.text(54, 626, "机制得到验证", 19, TEAL, True)
    original = strategies["Original query"]
    f.text(286, 626, f'只有 Requirement Query 将缺失证据拉入 Top{select_k} · 必需证据覆盖 {original["coverage"]} → {requirement["coverage"]}', 19, INK, True)
    f.text(54, 671, "不作为默认策略", 18, RED, True)
    f.text(286, 671, f'明确表示问题仅 {CASE["clear_incidence"]}；尚未测得默认路径的端到端收益。', 18, INK)
    f.text(54, 708, "来源：eval/reports/research_v1/a2_case_study.json", 14, MUTED)
    f.save()


if __name__ == "__main__":
    router_figure()
    decomposition_figure()
    print("Rendered 2 Chinese reader figures as PNG + SVG in", OUT)
