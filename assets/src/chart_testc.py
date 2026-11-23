"""TEST-C chart: per benchmark, the optimizer's own program (grey) and the same program with TRIBES 1.2 (red),
accuracy in %, mean over GEPA, MIPROv2 and SIMBA; the gain is printed at the end of the red bar.
Source: research/results/testc_result.json. Usage: python chart_testc.py OUT_DIR"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

OUT = Path(sys.argv[1])
SRC = Path(__file__).resolve().parents[2] / "research/results/testc_result.json"
font_manager.fontManager.addfont("C:/Windows/Fonts/bahnschrift.ttf")
plt.rcParams["font.family"] = "Bahnschrift"

NAMES = {"aime": "AIME 2026", "hover": "HoVer", "natplan": "NATURAL PLAN", "gpqa": "GPQA-extended",
         "toolhop": "ToolHop", "bird": "BIRD", "ifbench": "IFBench"}
res = json.load(open(SRC))
cells = [c for c in res["cells"] if c["ok"]]
rows = []
for ds, e in res["per_benchmark_holm"].items():
    cs = [c["info"] for c in cells if c["ds"] == ds]
    prog = sum(c["prog"] for c in cs) / len(cs)
    rows.append((NAMES[ds], prog, prog + e["mean_pp"], e["mean_pp"], e["holm_claim"]))
rows.sort(key=lambda r: -r[3])
P = res["primary"]
prog_all = sum(r[1] for r in rows) / len(rows)  # every benchmark has three cells: the cell mean equals this
rows.append((f"ALL {P['cells']} CELLS", prog_all, prog_all + P["mean_pp"], P["mean_pp"], P["claim"]))

THEMES = {
    "light": dict(bg="#FFFFFF", ink="#0A0A0B", muted="#5C5C62", grid="#E9E9EB", red="#A0000C", grey="#B9B9BE",
                  ns="#D86A72"),
    "dark": dict(bg="#0A0A0B", ink="#F4F4F2", muted="#A0A0A6", grid="#1E1E22", red="#C4001A", grey="#4A4A50",
                 ns="#7A2A31"),
}


def bar(ax, y, v, color, h, cut=0.11):
    """A bar from 0 to v with the brand's 45-degree cut on its outer top corner."""
    pts = [(0, y - h / 2), (v, y - h / 2), (v, y + h / 2 - cut), (v - cut * 9, y + h / 2), (0, y + h / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor="none", zorder=3))


for name, t in THEMES.items():
    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=200)
    fig.patch.set_facecolor(t["bg"])
    ax.set_facecolor(t["bg"])
    step, h, gap = 1.0, 0.34, 0.04
    ys, y = [], 0.0
    for i, r in enumerate(rows):
        if i == len(rows) - 1:
            y += 0.35  # a gap before the overall row
        ys.append(y)
        y += step
    ys = [max(ys) - v for v in ys]
    for (lab, prog, tri, gain, sig), yc in zip(rows, ys):
        last = lab.startswith("ALL")
        hh = h * (1.12 if last else 1.0)
        yp, yt = yc + hh / 2 + gap / 2, yc - hh / 2 - gap / 2
        bar(ax, yp, prog, t["grey"], hh)
        bar(ax, yt, tri, t["red"] if sig else t["ns"], hh)
        ax.text(prog + 0.9, yp, f"{prog:.1f}", va="center", ha="left", fontsize=10, color=t["muted"])
        ax.text(tri + 0.9, yt, f"{tri:.1f}", va="center", ha="left", fontsize=10.5, color=t["ink"])
        ax.text(tri + 7.2, yt, f"+{gain:.1f}", va="center", ha="left", fontsize=15 if last else 13.5,
                color=t["red"] if sig else t["muted"], fontweight="bold")
        if not sig:
            ax.text(tri + 16.2, yt, "not significant", va="center", ha="left", fontsize=9, color=t["muted"])
    ax.set_xlim(0, 124)
    ax.set_ylim(min(ys) - 0.62, max(ys) + 0.62)
    ax.set_yticks(ys, [r[0].upper() for r in rows])
    for lbl, r in zip(ax.get_yticklabels(), rows):
        lbl.set_color(t["ink"])
        lbl.set_fontsize(12.5 if r[0].startswith("ALL") else 11.5)
        lbl.set_fontweight("bold" if r[0].startswith("ALL") else "normal")
    ax.tick_params(axis="y", length=0, pad=10)
    ax.set_xticks(range(0, 101, 20))
    ax.tick_params(axis="x", colors=t["muted"], labelsize=10, length=0)
    ax.grid(axis="x", color=t["grid"], lw=0.8, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.axvline(0, color=t["ink"], lw=1.2, zorder=4)
    ax.set_xlabel("accuracy, %  ·  mean over GEPA, MIPROv2 and SIMBA  ·  gain in percentage points",
                  color=t["muted"], fontsize=10, labelpad=8)
    fig.text(0.015, 0.955, "TRIBES 1.2  ·  FRESH TEST (TEST-C)", fontsize=16, fontweight="bold", color=t["ink"],
             va="top")
    fig.text(0.015, 0.912, "1,323 new items  ·  21 cells  ·  pre-registered, opened once  ·  GLM 5.3 Flash",
             fontsize=10.5, color=t["muted"], va="top")
    fig.add_artist(Polygon([(0.015, 0.977), (0.075, 0.977), (0.071, 0.985), (0.015, 0.985)], closed=True,
                           transform=fig.transFigure, facecolor=t["red"], edgecolor="none"))
    for x0, col, txt in ((0.015, t["grey"], "OPTIMIZED PROGRAM"), (0.235, t["red"], "PROGRAM + TRIBES 1.2")):
        fig.add_artist(Polygon([(x0, 0.862), (x0 + 0.024, 0.862), (x0 + 0.024, 0.872), (x0 + 0.019, 0.879), (x0, 0.879)],
                               closed=True, transform=fig.transFigure, facecolor=col, edgecolor="none"))
        fig.text(x0 + 0.032, 0.8705, txt, fontsize=10, color=t["ink"], va="center", fontweight="bold")
    fig.subplots_adjust(left=0.165, right=0.985, top=0.835, bottom=0.085)
    fig.savefig(OUT / f"chart-testc-{name}.png", facecolor=t["bg"])
    plt.close(fig)
print("ok", [(r[0], round(r[1], 1), round(r[2], 1), r[3]) for r in rows])
