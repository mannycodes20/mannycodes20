"""Shared paths, profile config and terminal-window chrome for every renderer."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data", "contributions.json")
PROFILE = json.load(open(os.path.join(ROOT, "profile.json"), encoding="utf-8"))

BG, BG2, TILE, FRAME = "#0d1117", "#111722", "#161b22", "#30363d"
MUTED, INK, GREEN, BAR = "#7d8590", "#e6edf3", "#39d353", "#26a641"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def window(w, h, title, titlebar=30, pad=20):
    """Opening <svg> plus a dark rounded terminal frame with traffic-light dots."""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{titlebar}" x2="{w}" y2="{titlebar}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{pad + i*16}" cy="{titlebar/2}" r="5" fill="{dot}"/>')
    out.append(f'<text x="{w/2}" y="{titlebar/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
               f'{PROFILE["prompt"]}: ~$ {title}</text>')
    return out


def write(path, svg):
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.relpath(path, ROOT)} ({len(svg)//1024} KB)")
