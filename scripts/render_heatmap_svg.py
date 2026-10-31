#!/usr/bin/env python3
"""
Render data/contributions.json as an animated contribution graph: the classic
53-week x 7-day grid where each box pops in on a diagonal sweep, active days
flash bright as they land, then everything freezes. Pure CSS animation, which
GitHub runs inside <img> SVGs (JS never runs there).
"""
import datetime
import json
import os

from common import DATA, ROOT, write

CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
STEP = CELL + GAP
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
REVEAL, DUR = 3.6, 0.55  # whole sweep length, per-box pop length (seconds)

data = json.load(open(DATA))
days = data["days"]
first = datetime.date.fromisoformat(days[0]["date"])
lead = (first.weekday() + 1) % 7  # GitHub columns start on Sunday
n_weeks = (lead + len(days) + 6) // 7
W = LEFT + n_weeks * STEP + 6
H = TOP + 7 * STEP + 22
last_order = (n_weeks - 1) + 6 * 0.55

labels, rects, last_month, last_wk = [], [], None, -9
for wk in range(n_weeks):
    d = first + datetime.timedelta(days=wk * 7 - lead)
    if d.month != last_month:
        last_month = d.month
        if wk > n_weeks - 3:  # no room at the right edge
            continue
        if wk - last_wk < 3:  # previous month was only a stub column: drop its label
            labels.pop()
        last_wk = wk
        labels.append(f'<text class="l" x="{LEFT + wk*STEP}" y="{TOP-8}">{d:%b}</text>')
for name, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    labels.append(f'<text class="l" x="2" y="{TOP + row*STEP + CELL - 2}">{name}</text>')

for i, d in enumerate(days):
    wk, row = divmod(lead + i, 7)
    lvl = min(d["level"], 4)
    delay = (wk + row * 0.55) / last_order * REVEAL
    s = "" if d["count"] == 1 else "s"
    rects.append(f'<rect class="c{" g" if lvl else ""}" x="{LEFT + wk*STEP}" y="{TOP + row*STEP}" '
                 f'width="{CELL}" height="{CELL}" rx="{RAD}" fill="{COLORS[lvl]}" style="animation-delay:{delay:.3f}s">'
                 f'<title>{d["date"]}: {d["count"]} contribution{s}</title></rect>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
.l{{fill:#7d8590;font-size:13px;font-weight:600}}
.t{{fill:#e6edf3;font-size:15px;font-weight:700}}
.c{{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop {DUR}s ease-out both}}
.g{{animation:pop {DUR}s ease-out both,flash {DUR+0.15}s ease-out both}}
@keyframes pop{{0%{{opacity:0;transform:scale(.2)}}60%{{opacity:1;transform:scale(1.1)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes flash{{0%,45%{{filter:brightness(2.4)}}100%{{filter:brightness(1)}}}}
@media (prefers-reduced-motion:reduce){{.c{{opacity:1!important;animation:none!important}}}}
</style>
{"".join(labels)}
{"".join(rects)}
<text class="t" x="{LEFT}" y="{H-6}">{data["total_contributions"]:,} contributions in the last year</text>
</svg>'''

write(os.path.join(ROOT, "contrib-heatmap.svg"), svg)
