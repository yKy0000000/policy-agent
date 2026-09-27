"""Render editorial README figures from consolidated frozen results.

This is a presentation script. It performs no evaluation or model calls.
Run from the project root with a Python installation containing Pillow.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "eval" / "final"
OUT = FINAL / "figures"
OUT.mkdir(exist_ok=True)

METRICS = json.loads((FINAL / "final_metrics.json").read_text(encoding="utf-8"))
FAILURE = json.loads((FINAL / "failure_analysis.json").read_text(encoding="utf-8"))
CASE = json.loads((FINAL / "a2_case_study.json").read_text(encoding="utf-8"))

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
        path = Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf")
        if not path.exists():
            path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
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
        self.svg.append(f'<text x="{x}" y="{y + size * .94:.1f}" fill="{color}" font-family="Segoe UI, Arial, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{svg_anchor}">{escape(value)}</text>')

    def save(self):
        self.im.save(OUT / f"{self.name}.png", optimize=True, dpi=(216, 216))
        (OUT / f"{self.name}.svg").write_text("\n".join(self.svg + ["</svg>"]), encoding="utf-8")


def header(f: Figure, eyebrow: str, title: str, subtitle: str):
    f.text(54, 28, eyebrow.upper(), 15, TEAL, True)
    f.text(54, 61, title, 34, INK, True)
    f.text(54, 112, subtitle, 19, MUTED)
    f.line(54, 152, f.width - 54, 152, RULE, 1)


def router_figure():
    f = Figure("router_decision", 1200, 748)
    header(f, "A1 / context allocation", "The router did not earn its extra context", "Four reference arms shown; the frozen Pareto decision compares all five arms and all quality axes.")
    f.text(55, 174, "POLICY", 15, MUTED, True)
    f.text(383, 174, "PROVIDER TOKENS / QUERY", 15, MUTED, True)
    f.text(967, 174, "COMPLETE", 15, MUTED, True)
    f.text(1117, 174, "ROLE", 15, MUTED, True, "right")
    arms = [
        ("fixed_top5", "Fixed Top5", GRAY, "cost floor"),
        ("coverage_selector_v2", "Evidence selector", TEAL, "reference"),
        ("query_router_v1", "Query router", RED, "KILL"),
        ("no_router_adaptive_v1", "No-router adaptive", BLUE, "ceiling"),
    ]
    x0, x1 = 383, 904
    for i, (key, label, color, role) in enumerate(arms):
        y = 226 + i * 76
        d = METRICS["a1"][key]
        if key in ("coverage_selector_v2", "query_router_v1"):
            f.rect(48, y - 10, 1090, 57, TEAL_BG if key == "coverage_selector_v2" else RED_BG, radius=7)
        f.text(56, y, label, 22, color, True)
        f.rect(x0, y + 5, x1 - x0, 17, LIGHT, radius=8)
        bar = (x1-x0) * d["tokens_per_query"] / 6500
        f.rect(x0, y + 5, bar, 17, color, radius=8)
        f.text(x0 + bar + 10, y - 1, f'{d["tokens_per_query"]:,.0f}', 19, INK, True)
        f.text(978, y, f'{d["complete"]}/50', 22, INK, True)
        f.text(1131, y + 2, role, 17, color, True, "right")
    f.line(54, 526, 1146, 526, RULE)
    f.text(54, 544, "STRICT DOMINANCE: EVIDENCE SELECTOR  →  QUERY ROUTER", 20, INK, True)
    f.text(54, 581, "Same answer quality", 16, MUTED, True)
    f.text(54, 608, "44/50 complete  ·  196/208 required aspects", 20, INK)
    f.text(461, 581, "Lower cost", 16, MUTED, True)
    f.text(461, 608, "3,281 vs 3,668 tokens/query", 20, INK)
    f.text(823, 581, "Fewer failures", 16, MUTED, True)
    f.text(823, 608, "0 vs 1 regressions", 20, INK)
    f.text(823, 638, "1 vs 2 grounding issues", 18, INK)
    f.line(54, 689, 1146, 689, RULE)
    f.text(54, 702, "Dominance also requires no worse coverage, regressions or grounding; bar position alone is not the test.", 16, MUTED)
    f.text(54, 726, "Source: eval/final/final_metrics.json · frozen A1 Pareto", 14, MUTED)
    f.save()


def failure_figure():
    f = Figure("failure_roadmap", 1200, 744)
    header(f, "A1 / residual postmortem", "Most remaining misses point to use and selection", "16 distinct QUERY_REQUIRED aspects missing in ≥1 of four surviving arms; 10 cases in total.")
    f.rect(52, 175, 735, 166, TEAL_BG, radius=9)
    counts = FAILURE["taxonomy_counts"]
    rows = [
        ("GENERATION_MISS", "Generation miss", TEAL),
        ("SELECTION_BUDGET", "Selection / budget", TEAL),
        ("RANKING_WEAKNESS", "Ranking weakness", GRAY),
        ("REPRESENTATION_CANDIDATE", "Representation candidate", BLUE),
        (None, "Confirmed fragmentation", RED),
    ]
    for i, (key, label, color) in enumerate(rows):
        y = 196 + i * 91
        n = counts[key] if key else 0
        f.text(68, y, label, 21, INK, i < 2)
        f.rect(355, y + 5, 381, 20, LIGHT, radius=9)
        if n:
            f.rect(355, y + 5, 381*n/6, 20, color, radius=9)
        else:
            f.line(355, y + 16, 736, y + 16, RULE, 2)
        f.text(755, y - 2, str(n), 25, color, True)
    f.rect(827, 193, 313, 118, TEAL_BG, radius=9)
    f.text(846, 206, "12 / 16", 43, TEAL, True)
    f.text(846, 267, "generation + selection", 19, INK, True)
    f.text(827, 352, "ROADMAP CONSEQUENCE", 16, MUTED, True)
    f.text(827, 389, "Improve evidence use and", 19, INK)
    f.text(827, 419, "context allocation first.", 19, INK)
    f.text(827, 468, "One clear representation case", 18, BLUE, True)
    f.text(827, 496, "justifies a small A2 probe.", 18, INK)
    f.text(827, 550, "Zero confirmed fragmentation", 18, RED, True)
    f.text(827, 578, "means A3 does not start.", 18, INK)
    f.line(54, 669, 1146, 669, RULE)
    f.text(54, 681, "Counts are unique aspects, not per-arm totals; two representation aspects come from one case (VAL-001-046).", 16, MUTED)
    f.text(54, 713, "Source: eval/final/failure_analysis.json", 14, MUTED)
    f.save()


def decomposition_figure():
    f = Figure("decomposition_case", 1200, 729)
    header(f, "A2 / VAL-001-046", "The missing source surfaced only after query decomposition", "Same five-chunk context budget; retrieval/context probe only, with no answer generation.")
    f.text(54, 173, "STRATEGY", 15, MUTED, True)
    f.text(386, 173, "TARGET SOURCE IN BGE ORDER — LOWER RANK IS BETTER", 15, MUTED, True)
    f.text(1129, 173, "REQUIRED EVIDENCE", 15, MUTED, True, "right")
    xa, xb = 385, 913
    rankx = lambda rank: xa + (rank - 1) / 90 * (xb-xa)
    for rank, label in [(1,"1"),(5,"5"),(50,"50"),(91,"91")]:
        x = rankx(rank)
        f.line(x, 202, x, 570, RULE, 1)
        f.text(x, 188, label, 16, MUTED, False, "center")
    for i, item in enumerate(CASE["strategies"]):
        y = 228 + i * 91
        strat = item["strategy"]
        if strat == "Requirement query":
            f.rect(48, y - 8, 1095, 69, TEAL_BG, radius=9)
        f.text(60, y+7, strat, 21, TEAL if item["selected"] else INK, item["selected"])
        rank = item["bge_rank"]
        if rank is None:
            f.text(385, y+7, "ABSENT FROM POOL", 18, RED, True)
        else:
            x = rankx(rank)
            f.circle(x, y+22, 9, TEAL if item["selected"] else RED)
            if rank == 79:
                f.text(x-15, y+3, "rank 79 / 91", 19, RED, True, "right")
            else:
                f.text(x+18, y+3, "rank 2 · selected", 19, TEAL, True)
        f.text(1109, y+5, item["coverage"], 26, TEAL if item["selected"] else MUTED, True, "right")
    f.line(54, 609, 1146, 609, RULE)
    f.text(54, 626, "MECHANISM CONFIRMED", 19, TEAL, True)
    f.text(337, 626, "0/4  →  4/4 required evidence coverage", 21, INK, True)
    f.text(54, 671, "DEFAULT NOT ADOPTED", 18, RED, True)
    f.text(337, 671, "One clear representation case among 50; no default end-to-end gain measured.", 18, INK)
    f.text(54, 708, "Source: eval/final/a2_case_study.json", 14, MUTED)
    f.save()


if __name__ == "__main__":
    router_figure()
    failure_figure()
    decomposition_figure()
    print("Rendered 3 reader figures as PNG + SVG in", OUT)
