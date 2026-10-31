#!/usr/bin/env python3
"""
Render the hero banner in two themes (readmefile/dark.svg, readmefile/light.svg)
for the README's <picture> element, which picks one by the viewer's GitHub theme.

Name and tagline come from profile.json; the pixel dino is sampled from
source-photo.png. Run once locally after changing either:

    python scripts/make_banner.py
"""
import html
import os
import random

from PIL import Image

from common import PROFILE, ROOT

W, H = 1200, 320
FONT_SANS = "-apple-system, Segoe UI, Helvetica, Arial, sans-serif"
FONT_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FOCUS = ["AI Agents", "Desktop Tools", "Full-Stack", "VFX"]

THEMES = {
    "dark": dict(bg="#0d1117", bg2="#111722", ink="#e6edf3", muted="#7d8590", accent="#39d353",
                 frame="#30363d", cells=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]),
    "light": dict(bg="#ffffff", bg2="#f6f8fa", ink="#1f2328", muted="#59636e", accent="#1a7f37",
                  frame="#d0d7de", cells=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]),
}


def dino_cells(cols=34):
    """The avatar's white dino as a list of (col, row) pixels on a cols-wide grid."""
    im = Image.open(os.path.join(ROOT, "source-photo.png")).convert("L")
    im = im.crop(Image.eval(im, lambda v: 255 if v > 128 else 0).getbbox())
    rows = round(cols * im.height / im.width)
    px = im.resize((cols, rows), Image.BOX).load()
    return [(x, y) for y in range(rows) for x in range(cols) if px[x, y] > 128], rows


def runs(cells):
    """Merge (col, row) pixels into (row, start_col, length) horizontal runs."""
    out = []
    for c, r in sorted(cells, key=lambda p: (p[1], p[0])):
        if out and out[-1][0] == r and out[-1][1] + out[-1][2] == c:
            out[-1][2] += 1
        else:
            out.append([r, c, 1])
    return out


def render(t, dino, dino_rows):
    rnd = random.Random(20)  # same backdrop every run
    p = PROFILE
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<style>'
        '.c{opacity:0;animation:in .5s ease-out both}'
        '@keyframes in{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}'
        '.k{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}'
        '.d{animation:bob 2.4s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-6px)}}'
        '@media (prefers-reduced-motion:reduce){.c,.k,.d{animation:none!important;opacity:1!important}}'
        '</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg2"]}"/>'
        f'<stop offset="1" stop-color="{t["bg"]}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{t["frame"]}"/>',
    ]

    # contribution-graph backdrop: absent behind the text, ramping up towards the right
    step, cell = 18, 14
    for col in range(W // step):
        x = col * step + 6
        ramp = min(1, max(0, (x - 560) / 420)) * 0.75
        if ramp == 0:
            continue
        for row in range(H // step):
            lvl = rnd.choices(range(5), weights=[10, 3, 2, 1.5, 1])[0]
            delay = (col - 31) * 0.03 + row * 0.04
            out.append(f'<rect class="c" x="{x}" y="{row*step + 7}" width="{cell}" height="{cell}" rx="3" '
                       f'fill="{t["cells"][lvl]}" fill-opacity="{ramp:.2f}" style="animation-delay:{delay:.2f}s"/>')

    # text block
    x0 = 64
    prompt = f'{p["prompt"]} ~ $ whoami'
    out += [
        f'<text x="{x0}" y="92" font-family="{FONT_MONO}" font-size="20" fill="{t["muted"]}">{html.escape(prompt)}</text>',
        f'<rect class="k" x="{x0 + len(prompt) * 12.1 + 6:.0f}" y="76" width="11" height="20" fill="{t["accent"]}"/>',
        f'<text x="{x0 - 3}" y="170" font-family="{FONT_SANS}" font-size="68" font-weight="800" fill="{t["ink"]}" '
        f'letter-spacing="-1.5">{html.escape(p["name"])}</text>',
        f'<text x="{x0}" y="212" font-family="{FONT_SANS}" font-size="24" fill="{t["muted"]}">{html.escape(p["tagline"])}</text>',
        f'<text x="{x0}" y="262" font-family="{FONT_MONO}" font-size="18" fill="{t["accent"]}">'
        + html.escape("  ·  ".join(FOCUS)) + '</text>',
    ]

    # the dino, standing on a dashed ground line, with a backing plate so the grid doesn't show through
    px = 6
    dw, dh = 34 * px, dino_rows * px
    dx, dy = W - dw - 90, H - dh - 52
    out.append(f'<rect x="{dx - 24}" y="{dy - 20}" width="{dw + 48}" height="{dh + 40}" rx="14" fill="{t["bg"]}" opacity=".85"/>')
    out.append(f'<g class="d" fill="{t["ink"]}" shape-rendering="crispEdges">')
    for r, c0, n in runs(dino):  # one rect per horizontal run: no seams between pixels
        out.append(f'<rect x="{dx + c0*px}" y="{dy + r*px}" width="{n*px}" height="{px}"/>')
    out.append('</g>')
    out.append(f'<line x1="{dx - 12}" y1="{dy + dh + 4}" x2="{dx + dw + 12}" y2="{dy + dh + 4}" '
               f'stroke="{t["muted"]}" stroke-width="2" stroke-dasharray="10 6"/>')
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    dino, rows = dino_cells()
    os.makedirs(os.path.join(ROOT, "readmefile"), exist_ok=True)
    for name, theme in THEMES.items():
        path = os.path.join(ROOT, "readmefile", f"{name}.svg")
        svg = render(theme, dino, rows)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote readmefile/{name}.svg ({len(svg)//1024} KB)")
