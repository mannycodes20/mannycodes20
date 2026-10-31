#!/usr/bin/env python3
"""
Turn the prepped portrait into a monochrome ASCII-art SVG that "types" itself
in row by row behind a block cursor, then holds. One ink color plus a good
density ramp reads far cleaner than per-character color.

    python scripts/make_ascii_svg.py [source-prepped.png] [ascii.svg]
    STATIC=1 ...   emit the frozen end state (handy for previews)
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

from common import FRAME, MUTED, PROFILE, ROOT, window, write

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "ascii.svg")

COLS = int(os.environ.get("COLS", 180))  # more columns = more detail
ART_W = 800
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8  # monospace glyph aspect
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"   # light -> dense
CONTRAST, GAMMA, WHITE_FLOOR = 1.05, 1.18, 0.80
INK = "#c9d1d9"

PAD, TITLEBAR, STATUS = 20, 30, 30
ART_H = ROWS * CELL_H
W, H = ART_W + PAD * 2, TITLEBAR + ART_H + STATUS + PAD
ROW_DUR = 5.8 / ROWS     # whole portrait prints in ~6 s
STATIC = bool(os.environ.get("STATIC"))

im = ImageEnhance.Contrast(Image.open(SRC).convert("L")).enhance(CONTRAST)
px = im.resize((COLS, ROWS), Image.LANCZOS).load()
rows = []
for y in range(ROWS):
    line = ""
    for x in range(COLS):
        lum = (px[x, y] / 255.0) ** GAMMA
        line += " " if lum >= WHITE_FLOOR else RAMP[round((1 - lum) * (len(RAMP) - 1))]
    rows.append(line)

parts = window(round(W), round(H), "./portrait.sh")
art_top = TITLEBAR + PAD * 0.35
size = CELL_H * 0.86
for r, line in enumerate(rows):
    row_y = art_top + r * CELL_H
    delay = r * ROW_DUR
    text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H*0.74:.1f}" fill="{INK}" font-size="{size:.1f}" '
            f'textLength="{ART_W}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC:
        parts.append(text)
        continue
    parts += [
        f'<clipPath id="r{r}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'</rect></clipPath>',
        f'<g clip-path="url(#r{r})">{text}</g>',
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{INK}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>',
    ]

line_y = TITLEBAR + ART_H + PAD * 0.35
status_y = line_y + 19
prompt = f'{PROFILE["prompt"]}:~$ whoami '
parts += [
    f'<line x1="0" y1="{line_y:.1f}" x2="{W}" y2="{line_y:.1f}" stroke="{FRAME}"/>',
    f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="13">{html.escape(prompt)}'
    f'<tspan fill="{INK}">{html.escape(PROFILE["name"])}</tspan></text>',
    f'<rect x="{PAD + (len(prompt) + len(PROFILE["name"]) + 1) * 13 * 0.6:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
    f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>',
    "</svg>",
]
write(OUT, "".join(parts))
