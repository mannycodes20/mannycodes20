#!/usr/bin/env python3
"""
Render the streak / numbers card from data/contributions.json as a terminal
window the same size as the ASCII portrait (840 x 880), so the two line up side
by side. Six tiles slide in and count up to the real value, then a monthly bar
chart grows underneath. The count-up is a stack of pre-rendered frames toggled
with SMIL <set>, since GitHub runs SMIL/CSS in <img> SVGs but never JS.
"""
import datetime
import json
import os

from common import BAR, DATA, FRAME, GREEN, INK, MUTED, ROOT, TILE, window, write

W, H = 840, 880
PAD, TITLEBAR, GAP = 20, 30, 16
COLS, ROWS, TILE_H = 2, 3, 150
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILES_TOP = TITLEBAR + PAD + 4
CHART_TOP = TILES_TOP + ROWS * (TILE_H + GAP)

STAGGER, SLIDE, COUNT, FRAMES = 0.15, 0.45, 1.2, 16
BAR_START, BAR_STAGGER, BAR_DUR = STAGGER * COLS * ROWS + 0.4, 0.06, 0.6


def short(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d:%b} {d.day}"


def span(s):
    return f'{short(s["start"])} – {short(s["end"])}' if s["length"] else "—"


def fmt(v, like):
    return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"


data = json.load(open(DATA))
cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
n_days = len(data["days"])
tiles = [  # label, value, suffix, caption, accent
    ("current streak", cur["length"], " days", span(cur), GREEN),
    ("longest streak", lng["length"], " days", span(lng), INK),
    ("contributions", data["total_contributions"], "", "in the last year", INK),
    ("active days", data["active_days"], f" / {n_days}", f'{data["active_days"] / n_days:.0%} of the year', INK),
    ("best day", best["count"], "", short(best["date"]), INK),
    ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
]

parts = window(W, H, "./stats.sh")
parts.insert(1, '<style>'
             f'.t{{opacity:0;animation:in {SLIDE}s ease-out both}}'
             '@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}'
             f'.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}'
             '@keyframes grow{to{transform:scaleY(1)}}'
             '@media (prefers-reduced-motion:reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}'
             '</style>')

for i, (label, value, suffix, caption, accent) in enumerate(tiles):
    x = PAD + (i % COLS) * (TILE_W + GAP)
    y = TILES_TOP + (i // COLS) * (TILE_H + GAP)
    start = i * STAGGER
    count_start = start + SLIDE * 0.6
    parts += [f'<g class="t" style="animation-delay:{start:.2f}s">',
              f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" fill="{TILE}" stroke="{FRAME}"/>',
              f'<text x="{x+24:.1f}" y="{y+40}" fill="{MUTED}" font-size="22">$ {label}</text>']
    for k in range(1, FRAMES + 1):
        v = value * (1 - (1 - k / FRAMES) ** 3)  # ease-out into the real number
        anim = f'<set attributeName="opacity" to="1" begin="{count_start + COUNT*(k-1)/FRAMES:.3f}s"/>'
        if k < FRAMES:
            anim += f'<set attributeName="opacity" to="0" begin="{count_start + COUNT*k/FRAMES:.3f}s"/>'
        parts.append(f'<text x="{x+24:.1f}" y="{y+100}" opacity="0" font-size="54" font-weight="700" fill="{accent}">'
                     f'{fmt(v, value)}<tspan font-size="24" font-weight="400" fill="{MUTED}">{suffix}</tspan>{anim}</text>')
    parts += [f'<text x="{x+24:.1f}" y="{y+132}" fill="{MUTED}" font-size="20">{caption}</text>', '</g>']

monthly = data["monthly"]
chart_w, chart_h = W - PAD * 2, H - PAD - CHART_TOP
parts += [f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">',
          f'<rect x="{PAD}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" fill="{TILE}" stroke="{FRAME}"/>',
          f'<text x="{PAD+24}" y="{CHART_TOP+40}" fill="{MUTED}" font-size="22">$ contributions / month</text>', '</g>']

plot_top, plot_bot = CHART_TOP + 64, CHART_TOP + chart_h - 40
plot_l, plot_r = PAD + 24, PAD + chart_w - 24
slot = (plot_r - plot_l) / len(monthly)
bar_w = slot * 0.62
peak = max(m["total"] for m in monthly) or 1
for i, m in enumerate(monthly):
    h = max(2, (plot_bot - plot_top) * m["total"] / peak)
    bx = plot_l + i * slot + (slot - bar_w) / 2
    delay = BAR_START + i * BAR_STAGGER
    is_peak = m["total"] == peak
    parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="3" '
                 f'fill="{GREEN if is_peak else BAR}" style="animation-delay:{delay:.2f}s"/>')
    mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 28}" fill="{MUTED}" font-size="18" text-anchor="middle">{mon}</text>')
    if is_peak and m["total"]:
        parts.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w/2:.1f}" '
                     f'y="{plot_bot - h - 10:.1f}" fill="{INK}" font-size="18" text-anchor="middle">{peak:,}</text>')

parts.append('</svg>')
write(os.path.join(ROOT, "stats.svg"), "".join(parts))
