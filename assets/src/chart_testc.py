"""TEST-C charts: the optimizer's own program (grey) and the same program with TRIBES (red), accuracy in %; the gain
in percentage points is printed at the end of the red bar.
  chart-testc-*      per benchmark, mean over GEPA, MIPROv2 and SIMBA
  chart-testc-opt-*  per optimizer (GEPA vs GEPA + TRIBES, ...), mean over the seven benchmarks
Source: research/results/testc_result.json. Usage: python chart_testc.py OUT_DIR"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager, patheffects  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

OUT = Path(sys.argv[1])
SRC = Path(__file__).resolve().parents[2] / "research/results/testc_result.json"
font_manager.fontManager.addfont("C:/Windows/Fonts/bahnschrift.ttf")
plt.rcParams["font.family"] = "Bahnschrift"


def heavy(color, w=0.9):
    """Bahnschrift is a variable font matplotlib reads at one weight: thicken the strokes instead."""
    return [patheffects.withStroke(linewidth=w, foreground=color)]


NAMES = {"aime": "AIME 2026", "hover": "HoVer", "natplan": "NATURAL PLAN", "gpqa": "GPQA-extended",
         "toolhop": "ToolHop", "bird": "BIRD", "ifbench": "IFBench"}
OPTS = {"gepa": "GEPA", "mipro": "MIPROv2", "simba": "SIMBA"}
res = json.load(open(SRC))
cells = [c for c in res["cells"] if c["ok"]]
P = res["primary"]

# per benchmark: (label, grey label, red label, program, tribes, gain, significant)
bench = []
for ds, e in res["per_benchmark_holm"].items():
    cs = [c["info"] for c in cells if c["ds"] == ds]
    prog = sum(c["prog"] for c in cs) / len(cs)
    bench.append((NAMES[ds].upper(), None, None, prog, prog + e["mean_pp"], e["mean_pp"], e["holm_claim"]))
bench.sort(key=lambda r: -r[5])
prog_all = sum(r[3] for r in bench) / len(bench)  # every benchmark has three cells: the cell mean equals this
bench.append((f"ALL {P['cells']} CELLS", None, None, prog_all, prog_all + P["mean_pp"], P["mean_pp"], P["claim"]))

# per optimizer: mean over its seven cells (descriptive)
opt = []
for o, lab in OPTS.items():
    cs = [c["info"] for c in cells if c["opt"] == o]
    pr, tr = sum(c["prog"] for c in cs) / len(cs), sum(c["v12"] for c in cs) / len(cs)
    opt.append((lab, lab, f"{lab} + TRIBES", pr, tr, tr - pr, True))

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


def gtxt(g):
    return f"+{g:.1f}" if g >= 0.05 else ("0.0" if g > -0.05 else f"−{-g:.1f}")


def draw(rows, fname, title, subtitle, legend, xlabel, size, left, per_bar, ns_note=True):
    for name, t in THEMES.items():
        fig, ax = plt.subplots(figsize=size, dpi=200)
        fig.patch.set_facecolor(t["bg"])
        ax.set_facecolor(t["bg"])
        h, gap = 0.34, 0.04
        ys, y = [], 0.0
        for i, r in enumerate(rows):
            if r[0].startswith("ALL"):
                y += 0.35  # a gap before the overall row
            ys.append(y)
            y += 1.0
        ys = [max(ys) - v for v in ys]
        ticks, labels, colors = [], [], []
        for (lab, gl, rl, prog, tri, gain, sig), yc in zip(rows, ys):
            last = lab.startswith("ALL")
            hh = h * (1.12 if last else 1.0)
            yp, yt = yc + hh / 2 + gap / 2, yc - hh / 2 - gap / 2
            bar(ax, yp, prog, t["grey"], hh)
            bar(ax, yt, tri, t["red"] if sig else t["ns"], hh)
            ax.text(prog + 0.9, yp, f"{prog:.1f}", va="center", ha="left", fontsize=10, color=t["muted"])
            ax.text(tri + 0.9, yt, f"{tri:.1f}", va="center", ha="left", fontsize=10.5, color=t["ink"])
            c = t["red"] if sig else t["muted"]
            ax.text(tri + 7.2, yt, f"{gtxt(gain)} pp", va="center", ha="left", fontsize=15 if last else 13.5, color=c,
                    path_effects=heavy(c, 0.5))
            if not sig and ns_note:
                ax.text(tri + 21.5, yt, "not significant", va="center", ha="left", fontsize=9, color=t["muted"])
            if per_bar:
                ticks += [yp, yt]
                labels += [gl, rl]
                colors += [t["muted"], t["red"]]
            else:
                ticks.append(yc)
                labels.append(lab)
                colors.append(t["ink"])
        ax.set_xlim(0, 128)
        ax.set_ylim(min(ys) - 0.62, max(ys) + 0.62)
        ax.set_yticks(ticks, labels)
        for lbl, col in zip(ax.get_yticklabels(), colors):
            lbl.set_color(col)
            lbl.set_fontsize(12.5 if per_bar else 11.5)
            if per_bar and col == t["red"] or lbl.get_text().startswith("ALL"):
                lbl.set_path_effects(heavy(col, 0.5))
        ax.tick_params(axis="y", length=0, pad=10)
        ax.set_xticks(range(0, 101, 20))
        ax.tick_params(axis="x", colors=t["muted"], labelsize=10, length=0)
        ax.grid(axis="x", color=t["grid"], lw=0.8, zorder=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.axvline(0, color=t["ink"], lw=1.2, zorder=4)
        ax.set_xlabel(xlabel, color=t["muted"], fontsize=10, labelpad=8)
        H = size[1]
        top = 1 - 0.33 / H
        fig.text(0.015, top, title, fontsize=16, color=t["ink"], va="top", path_effects=heavy(t["ink"], 0.6))
        fig.text(0.015, top - 0.32 / H, subtitle, fontsize=10.5, color=t["muted"], va="top")
        yb = 1 - 0.22 / H
        fig.add_artist(Polygon([(0.015, yb), (0.075, yb), (0.071, yb + 0.06 / H), (0.015, yb + 0.06 / H)], closed=True,
                               transform=fig.transFigure, facecolor=t["red"], edgecolor="none"))
        if legend:
            yl = top - 0.72 / H
            for x0, col, txt in ((0.015, t["grey"], legend[0]), (0.36 if len(legend[0]) > 20 else 0.2, t["red"], legend[1])):
                fig.add_artist(Polygon([(x0, yl - 0.06 / H), (x0 + 0.024, yl - 0.06 / H), (x0 + 0.024, yl + 0.015 / H),
                                        (x0 + 0.019, yl + 0.06 / H), (x0, yl + 0.06 / H)],
                                       closed=True, transform=fig.transFigure, facecolor=col, edgecolor="none"))
                fig.text(x0 + 0.032, yl, txt, fontsize=10, color=t["ink"], va="center", path_effects=heavy(t["ink"], 0.5))
        fig.subplots_adjust(left=left, right=0.985, top=1 - (1.22 if legend else 0.95) / H, bottom=0.62 / H)
        fig.savefig(OUT / f"{fname}-{name}.png", facecolor=t["bg"])
        plt.close(fig)


draw(bench, "chart-testc", "TRIBES  ·  FRESH TEST (TEST-C)",
     "1,323 new items  ·  21 cells  ·  pre-registered, opened once  ·  GLM 5.3 Flash",
     ("PROGRAM  (GEPA · MIPROv2 · SIMBA)", "PROGRAM + TRIBES"),
     "accuracy, %  ·  mean over GEPA, MIPROv2 and SIMBA  ·  gain in percentage points", (10, 7.4), 0.165, False)
draw(opt, "chart-testc-opt", "EVERY OPTIMIZER, PLUS TRIBES  ·  TEST-C",
     "accuracy, %, mean over the seven benchmarks of each optimizer  ·  1,323 new items  ·  GLM 5.3 Flash", None,
     "accuracy, %  ·  gain in percentage points", (10, 4.1), 0.2, True)
order = [r[0] for r in bench[:-1]]
key = {NAMES[k].upper(): k for k in NAMES}
for o, lab in OPTS.items():
    by = {c["ds"]: c["info"] for c in cells if c["opt"] == o}
    rows = [(b, None, None, by[key[b]]["prog"], by[key[b]]["v12"], by[key[b]]["v12"] - by[key[b]]["prog"],
             by[key[b]]["v12"] - by[key[b]]["prog"] >= 0.05) for b in order]
    rows.sort(key=lambda r: -r[5])  # each chart: largest gain first
    pr, tr = sum(r[3] for r in rows) / len(rows), sum(r[4] for r in rows) / len(rows)
    rows.append(("ALL 7 BENCHMARKS", None, None, pr, tr, tr - pr, True))
    n = sum(c["info"]["n"] for c in cells if c["opt"] == o)
    draw(rows, f"chart-testc-{o}", f"{lab}  vs  {lab} + TRIBES  ·  TEST-C",
         f"{n} new items  ·  7 benchmarks  ·  pre-registered, opened once  ·  GLM 5.3 Flash",
         (lab, f"{lab} + TRIBES"), "accuracy, %  ·  gain in percentage points  ·  per-benchmark gains of one optimizer are descriptive",
         (10, 7.4), 0.19, False, ns_note=False)
    print(lab, [(r[0], round(r[3], 1), round(r[4], 1), round(r[5], 1)) for r in rows])
