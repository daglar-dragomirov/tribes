# Generates the TRIBES identity (needs shapely, pillow; font: Windows Bahnschrift).
"""TRIBES identity: black, white, blood red; hard 45-degree cuts. Geometry -> SVG + supersampled PNG.
Usage: python brand.py OUT_DIR"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

INK = "#0A0A0B"     # black
COAL = "#141416"
GRAPH = "#232327"
ASH = "#8C8C92"
WHITE = "#F4F4F2"
RED = "#A0000C"     # blood red on white
RED_D = "#C4001A"   # the same red, lifted to stay blood-red on black
FONT = "C:/Windows/Fonts/bahnschrift.ttf"

CUT, R = 14, 3.5      # signature cut (top-right, bottom-left) and the small chamfer on every other corner


def chamfer(g, r=R):
    return g.buffer(-r, join_style="mitre", mitre_limit=10).buffer(r, join_style="bevel")


def cut_corners(g, c=CUT):
    x0, y0, x1, y1 = g.bounds
    tr = Polygon([(x1 - c, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y0 + c)])
    bl = Polygon([(x0 - 1, y1 - c), (x0 - 1, y1 + 1), (x0 + c, y1 + 1)])
    return g.difference(tr).difference(bl)


def U(*gs):
    return unary_union(gs)


# ---------- letters: cap height 100, stroke 20 ----------
def T():
    return U(box(0, 0, 72, 20), box(26, 0, 46, 100))


def Rr():
    bowl = box(0, 0, 72, 60).difference(box(20, 20, 52, 40))
    leg = Polygon([(30, 50), (52, 50), (72, 100), (50, 100)])
    return U(bowl, box(0, 0, 20, 100), leg)


def I():
    return box(0, 0, 20, 100)


def B():
    outer = U(box(0, 0, 66, 60), box(0, 40, 72, 100))
    return outer.difference(box(20, 20, 46, 40)).difference(box(20, 60, 52, 80))


def E():
    return U(box(0, 0, 20, 100), box(0, 0, 72, 20), box(0, 40, 60, 60), box(0, 80, 72, 100))


def S():
    return U(box(0, 0, 72, 20), box(0, 0, 20, 60), box(0, 40, 72, 60), box(52, 40, 72, 100), box(0, 80, 72, 100),
             box(52, 0, 72, 32), box(0, 68, 20, 100))


def wordmark(gap=16):
    parts, x = [], 0
    for f in (T, Rr, I, B, E, S):
        g = chamfer(cut_corners(f()))
        parts.append(affinity.translate(g, x, 0))
        x += g.bounds[2] - g.bounds[0] + gap
    return unary_union(parts)


# ---------- the mark: three forms, one chosen (red), on one base, in a cut frame ----------
def mark():
    big, small = 24, 8
    outer = Polygon([(small, 0), (100 - big, 0), (100, big), (100, 100 - small), (100 - small, 100), (big, 100),
                     (0, 100 - big), (0, small)])
    ring = outer.difference(outer.buffer(-7, join_style="mitre"))
    ring = ring.difference(box(-1, 44, 8, 56)).difference(box(92, 44, 101, 56))   # HUD gaps
    left = Polygon([(23, 46), (36, 34), (36, 72), (23, 72)])
    right = Polygon([(64, 34), (77, 46), (77, 72), (64, 72)])
    base = Polygon([(23, 72), (77, 72), (77, 76), (73, 80), (23, 80)])
    mono = unary_union([ring, chamfer(unary_union([left, right, base]), 1.2)])
    red = Polygon([(43, 31), (50, 19), (57, 31), (57, 66), (43, 66)])
    return mono, red


# ---------- output ----------
def polys(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def svg_path(g, dx=0, dy=0, s=1.0):
    d = []
    for p in polys(g):
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            d.append("M" + " L".join(f"{(x + dx) * s:.2f} {(y + dy) * s:.2f}" for x, y in pts) + " Z")
    return " ".join(d)


def draw_geom(img, g, color, dx, dy, s):
    m = Image.new("L", img.size, 0)
    dr = ImageDraw.Draw(m)
    for p in polys(g):
        dr.polygon([((x + dx) * s, (y + dy) * s) for x, y in p.exterior.coords], fill=255)
        for hole in p.interiors:
            dr.polygon([((x + dx) * s, (y + dy) * s) for x, y in hole.coords], fill=0)
    img.paste(Image.new("RGBA", img.size, color), (0, 0), m)


def render(layers, w, h, s, bg=(0, 0, 0, 0), ss=4):
    """layers: (geom, color, dx, dy) in units; s = px per unit at final size."""
    img = Image.new("RGBA", (w * ss, h * ss), bg)
    for g, c, dx, dy in layers:
        draw_geom(img, g, c, dx, dy, s * ss)
    return img.resize((w, h), Image.LANCZOS)


def write_svg(path, layers, vw, vh, bg=None):
    body = "".join(f'<path fill="{c}" fill-rule="evenodd" d="{svg_path(g, dx, dy)}"/>' for g, c, dx, dy in layers)
    rect = f'<rect width="{vw}" height="{vh}" fill="{bg}"/>' if bg else ""
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}">{rect}{body}</svg>\n')


def font(size, weight="Bold"):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


MONO, REDP = mark()
WORD = wordmark()
WW = WORD.bounds[2]


def mark_layers(mono, red, dx=0, dy=0):
    return [(MONO, mono, dx, dy), (REDP, red, dx, dy)]


# mark: transparent, light and dark
for name, mono, red in (("light", INK, RED), ("dark", WHITE, RED_D)):
    suffix = "" if name == "light" else "-dark"
    render(mark_layers(mono, red, 4, 4), 512, 512, 512 / 108).save(OUT / f"mark{suffix}-512.png")
    write_svg(OUT / f"tribes-mark{suffix}.svg", mark_layers(mono, red), 100, 100)

# tile icons (black tile, white + red): favicon, apple touch, header
tile = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
for px, fname in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icon-512.png")):
    pad = 10 if px >= 64 else 4
    u = 100 + 2 * pad
    render([(affinity.scale(tile, u / 100, u / 100, origin=(0, 0)), INK, 0, 0)] + mark_layers(WHITE, RED_D, pad, pad),
           px, px, px / u).save(OUT / fname)
render(mark_layers(WHITE, RED_D, 2, 2), 208, 208, 208 / 104).save(OUT / "logo-header.png")
write_svg(OUT / "tribes-mark-small.svg", [(tile, INK, 0, 0)] + mark_layers(WHITE, RED_D), 100, 100)

# lockup: mark (110 units tall) + wordmark (cap 62 units), red rule under the word
WS = 0.62
word = affinity.scale(WORD, WS, WS, origin=(0, 0))
rule = Polygon([(0, 0), (WW * WS * 0.30, 0), (WW * WS * 0.30 - 4, 4), (0, 4)])
LW, LH = 110 + 26 + WW * WS + 6, 106


def lockup_layers(mono, red):
    return (mark_layers(mono, red, 3, 3) + [(word, mono, 139, 3 + (110 - 62) / 2 - 4)]
            + [(rule, red, 139, 3 + (110 - 62) / 2 + 62 + 6)])


for name, mono, red in (("light", INK, RED), ("dark", WHITE, RED_D)):
    s = 8
    render(lockup_layers(mono, red), int(LW * s), int(LH * s), s).save(OUT / f"lockup-{name}.png")
    write_svg(OUT / f"tribes-lockup-{name}.svg", lockup_layers(mono, red), round(LW, 1), LH)

# social preview 1280 x 640
W, H = 1280, 640
img = Image.new("RGBA", (W, H), INK)
d = ImageDraw.Draw(img)
for x in range(0, W, 40):
    d.line([(x, 0), (x, H)], fill=COAL)
for y in range(0, H, 40):
    d.line([(0, y), (W, y)], fill=COAL)
d.polygon([(W - 150, 0), (W - 70, 0), (W - 390, H), (W - 470, H)], fill="#1B0003")
d.polygon([(W - 56, 0), (W - 40, 0), (W - 360, H), (W - 376, H)], fill=RED_D)
for (x, y, sx, sy) in ((40, 40, 1, 1), (W - 40, 40, -1, 1), (40, H - 40, 1, -1), (W - 40, H - 40, -1, -1)):
    d.line([(x, y), (x + 46 * sx, y)], fill=ASH, width=3)
    d.line([(x, y), (x, y + 46 * sy)], fill=ASH, width=3)
lk = render(lockup_layers(WHITE, RED_D), int(LW * 1.85), int(LH * 1.85), 1.85)
img.alpha_composite(lk, (96, 104))
d.text((100, 104 + lk.size[1] + 22), "INFERENCE-TIME ANSWER SELECTION", font=font(30, "SemiBold"), fill=WHITE)
d.text((100, 104 + lk.size[1] + 62), "FOR OPTIMIZED DSPY PROGRAMS  ·  GEPA  ·  MIPROv2  ·  SIMBA", font=font(22, "SemiBold"), fill=ASH)
stats = (("+4.7 pp", "FRESH TEST  ·  1,010 ITEMS"), ("+7.1 pp", "SEALED TEST  ·  15 CELLS"))
for i, (big, small) in enumerate(stats):
    x, y = 100 + 330 * i, 450
    d.polygon([(x, y), (x + 6, y), (x + 6, y + 96), (x, y + 96)], fill=RED_D)
    d.text((x + 24, y - 6), big, font=font(58), fill=WHITE)
    d.text((x + 24, y + 72), small, font=font(19, "SemiBold"), fill=ASH)
d.text((W - 100, H - 62), "pip install tribes", font=font(24, "SemiBold"), fill=WHITE, anchor="rs")
img.convert("RGB").save(OUT / "social-preview.png", optimize=True)
print("ok", sorted(p.name for p in OUT.iterdir()))
