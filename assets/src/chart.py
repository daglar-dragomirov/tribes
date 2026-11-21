"""TEST-B chart: TRIBES 1.1 minus the program per benchmark, 95 % CI. Usage: python chart.py OUT_DIR"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

OUT = Path(sys.argv[1])
font_manager.fontManager.addfont("C:/Windows/Fonts/bahnschrift.ttf")
plt.rcParams["font.family"] = "Bahnschrift"

# (label, mean, lo, hi, significant)   source: research/results/testb_result.json
ROWS = [("HoVer", 12.44, 8.89, 16.44, True), ("HotpotQA", 4.17, 1.83, 6.83, True), ("BIRD", 3.22, 0.89, 5.67, True),
        ("ToolHop", 2.17, -0.50, 5.00, False), ("GPQA", 1.67, -1.46, 4.79, False)]
MEAN = ("All 15 cells", 4.73, 3.43, 6.07, True)

THEMES = {
    "light": dict(bg="#FFFFFF", ink="#0A0A0B", muted="#5C5C62", grid="#E4E4E6", red="#A0000C", ns="#9A9AA0"),
    "dark": dict(bg="#0A0A0B", ink="#F4F4F2", muted="#A0A0A6", grid="#232327", red="#C4001A", ns="#5E5E64"),
}


def bar(ax, y, v, color, h=0.56, cut=0.12):
    """A bar from 0 to v with the brand's 45-degree cut on its outer top corner."""
    pts = [(0, y - h / 2), (v, y - h / 2), (v, y + h / 2 - cut * 2), (v - cut * 4, y + h / 2), (0, y + h / 2)] \
        if v > 0.6 else [(0, y - h / 2), (v, y - h / 2), (v, y + h / 2), (0, y + h / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor="none", zorder=3))


for name, t in THEMES.items():
    fig, ax = plt.subplots(figsize=(9.6, 4.6), dpi=200)
    fig.patch.set_facecolor(t["bg"])
    ax.set_facecolor(t["bg"])
    rows = ROWS + [MEAN]
    ys = list(range(len(rows) + 1))[::-1]
    ys = [y for y in ys if y != 1]  # gap before the mean row
    for (lab, m, lo, hi, sig), y in zip(rows, ys):
        is_mean = lab == MEAN[0]
        color = t["ink"] if is_mean else (t["red"] if sig else t["ns"])
        bar(ax, y, m, color, h=0.62 if is_mean else 0.56)
        wc = t["red"] if is_mean else t["ink"]
        ax.plot([lo, hi], [y, y], color=wc, lw=1.8, zorder=4, solid_capstyle="butt")
        for x in (lo, hi):
            ax.plot([x, x], [y - 0.16, y + 0.16], color=wc, lw=1.8, zorder=4)
        ax.text(hi + 0.35, y, f"{m:+.1f}", va="center", ha="left", fontsize=13, color=t["ink"], fontweight="bold")
        ax.text(hi + 1.85, y, "" if sig else "not significant", va="center", ha="left", fontsize=10,
                color=t["muted"])
        ax.text(-2.4, y, lab.upper(), va="center", ha="right", fontsize=11.5, color=t["ink"],
                fontweight="bold" if is_mean else "normal")
    ax.axvline(0, color=t["ink"], lw=1.2, zorder=2)
    ax.set_xlim(-2.2, 19.5)
    ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
    ax.set_yticks([])
    ax.set_xticks(range(0, 19, 3))
    ax.tick_params(axis="x", colors=t["muted"], labelsize=10, length=0)
    ax.grid(axis="x", color=t["grid"], lw=0.8, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("percentage points over the optimizer's own program  ·  95 % CI", color=t["muted"], fontsize=10,
                  labelpad=8)
    fig.text(0.015, 0.95, "TRIBES 1.1  ·  FRESH TEST (TEST-B)", fontsize=15, fontweight="bold", color=t["ink"],
             va="top")
    fig.text(0.015, 0.885, "1,010 new items  ·  GEPA, MIPROv2, SIMBA  ·  pre-registered  ·  red: significant after Holm",
             fontsize=10.5, color=t["muted"], va="top")
    fig.add_artist(Polygon([(0.015, 0.975), (0.075, 0.975), (0.07, 0.985), (0.015, 0.985)], closed=True,
                           transform=fig.transFigure, facecolor=t["red"], edgecolor="none"))
    fig.subplots_adjust(left=0.17, right=0.985, top=0.80, bottom=0.14)
    fig.savefig(OUT / f"chart-testb-{name}.png", facecolor=t["bg"])
    plt.close(fig)
print("ok")
