#!/usr/bin/env python3
"""Generate the caterpillar/butterfly contribution animation (SMIL, no JS).

usage: gen_caterpillar.py weeks.json outdir

weeks.json is the `weeks` array of GitHub's contributionCalendar (GraphQL).
Writes caterpillar.svg (light) and caterpillar-dark.svg.
"""
import json
import sys
from pathlib import Path

CELL, GAP, PAD = 10, 3, 26
STEP = CELL + GAP
BODY = 4           # squares behind the head
SEGMENT = ("#ffd33d", "#ffffff")  # head first, then alternating
T_EAT = 18.0       # caterpillar reaches the last cell
T_FLY0 = T_EAT + 1.2   # butterfly takes off
T_ZOOM = T_FLY0 + 8.2  # one wing fills the frame
T_BLACK = T_ZOOM + 0.8 # black hold ends; blocks come back
T = T_BLACK + 1.8      # loop length, seconds
EPS = 0.02

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
PALETTES = {
    "caterpillar.svg": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    "caterpillar-dark.svg": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
}


def kf(attr, points, tag="animate", extra=""):
    """<animate> over the loop from (time, value) points; steps use a tiny gap."""
    pts = sorted(points)
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    keys = ";".join(f"{t / T:.4f}" for t, _ in pts)
    vals = ";".join(str(v) for _, v in pts)
    return (f'<{tag} attributeName="{attr}" dur="{T}s" repeatCount="indefinite" '
            f'keyTimes="{keys}" values="{vals}"{extra}/>')


def slide(a, xa, b, xb):
    return kf("transform", [(a, xa), (b, xb)], "animateTransform", ' type="translate"')


def fade(show, hide):
    """opacity: 1 between show and hide (seconds), 0 elsewhere."""
    return kf("opacity", [(0, 0), (show, 0), (show + 0.3, 1), (hide, 1), (hide + 0.3, 0)])


def build(weeks, palette):
    ncols = len(weeks)
    gw = ncols * STEP - GAP
    w, h = gw + 2 * PAD, 7 * STEP - GAP + 2 * 18
    top = 18
    mid = top + 3 * STEP + CELL / 2

    # head only goes for coloured cells, in column order; greys stay untouched.
    grid = {(c, d["weekday"]): d["contributionLevel"] for c, wk in enumerate(weeks) for d in wk["contributionDays"]}
    pos = lambda c, r: (PAD + c * STEP + CELL / 2, top + r * STEP + CELL / 2)
    steps = [(0, min(r for (c, r) in grid if c == 0))]
    for c in range(ncols):
        rows = sorted(r for (cc, r) in grid if cc == c and grid[(cc, r)] != "NONE")
        if c % 2:
            rows.reverse()
        for r in rows:
            cx, cr = steps[-1]
            while cr != r:
                cr += 1 if r > cr else -1
                steps.append((cx, cr))
            while cx != c:
                cx += 1 if c > cx else -1
                steps.append((cx, cr))
    path = [pos(*st) for st in steps]
    first = {}
    for k, st in enumerate(steps):
        first.setdefault(st, k)
    cells = [(pos(c, r), lvl, first.get((c, r), 0)) for (c, r), lvl in sorted(grid.items())]
    dt = T_EAT / (len(path) - 1)
    xl, yl = path[-1]

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
         '<defs><path id="p" d="' + " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(path)) + '"/></defs>']

    empty = palette[0]
    for (cx, cy), level, k in cells:
        col = palette[LEVELS.index(level)]
        r = f'<rect x="{cx - CELL / 2}" y="{cy - CELL / 2}" width="{CELL}" height="{CELL}" rx="2" fill="{col}"'
        if level == "NONE":
            o.append(r + "/>")
            continue
        eat = k * dt
        o.append(r + ">" + kf("fill", [(0, col), (eat, col), (eat + EPS, empty), (T_BLACK, empty), (T_BLACK + 0.4, col)]) + "</rect>")

    # caterpillar: squares trailing the head along the same path
    end = T_EAT + BODY * dt
    o.append(f'<g>{kf("opacity", [(0, 1), (end + 0.1, 1), (end + 0.4, 0), (T_BLACK, 0), (T_BLACK + 0.3, 1)])}')
    for i in range(BODY, -1, -1):
        d0 = i * dt
        keys = ";".join(f"{t / T:.4f}" for t in (0, d0, T_EAT + d0, T_BLACK, T_BLACK + 0.01, T))
        o.append(f'<rect x="{-CELL / 2}" y="{-CELL / 2}" width="{CELL}" height="{CELL}" rx="2" fill="{SEGMENT[i % 2]}" stroke="#6e7681" stroke-width="0.5">'
                 f'<animateMotion dur="{T}s" repeatCount="indefinite" calcMode="linear" '
                 f'keyPoints="0;0;1;1;0;0" keyTimes="{keys}"><mpath xlink:href="#p"/></animateMotion></rect>')
    o.append("</g>")

    # butterfly: top view; flies left while zooming about its upper wing's centre
    o.append(f'<g>{fade(T_FLY0, T_ZOOM)}')
    o.append('<g>' + kf("transform", [(T_FLY0, f"{xl:.1f},{yl:.1f}"), (T_ZOOM, f"{w / 2},{mid}")],
                        "animateTransform", ' type="translate"'))
    o.append('<g>' + kf("transform", [(T_FLY0, 0.8), (T_FLY0 + 4.8, 1.3), (T_ZOOM - 1.4, 6), (T_ZOOM, 60)],
                        "animateTransform", ' type="scale"'))
    o.append('<g transform="translate(-2,8)">')
    o.append('<g><animateTransform attributeName="transform" type="translate" values="0,-7;0,7;0,-7" dur="2.2s" repeatCount="indefinite"/>')
    o.append('<g><animateTransform attributeName="transform" type="scale" values="1 1;1 0.2;1 1" dur="0.45s" repeatCount="indefinite"/>'
             '<ellipse cx="2" cy="-8" rx="8" ry="8.5" fill="#f0883e" stroke="#9e5a1c"/>'
             '<ellipse cx="2" cy="8" rx="8" ry="8.5" fill="#f0883e" stroke="#9e5a1c"/>'
             '<ellipse cx="-6" cy="-5" rx="5" ry="5" fill="#d29922"/>'
             '<ellipse cx="-6" cy="5" rx="5" ry="5" fill="#d29922"/>'
             '<circle cx="3" cy="-9" r="2.6" fill="#ffd33d" stroke="#000" stroke-width="0.7"/>'
             '<circle cx="3" cy="9" r="2.6" fill="#ffd33d" stroke="#000" stroke-width="0.7"/></g>')
    o.append('<ellipse rx="9" ry="2" fill="#6e7681"/><circle cx="-9" r="2.2" fill="#6e7681"/>'
             '<path d="M-10,-1 q-4,-4 -7,-3 M-10,1 q-4,4 -7,3" stroke="#6e7681" fill="none"/>')
    o.append("</g></g></g></g></g>")

    # black screen between the zoom and the next loop
    o.append(f'<rect width="{w}" height="{h}" fill="#000">'
             f'{kf("opacity", [(0, 0), (T_ZOOM - 0.6, 0), (T_ZOOM, 1), (T_BLACK, 1), (T_BLACK + 0.6, 0)])}</rect>')

    o.append("</svg>")
    return "\n".join(o)


def main(src: Path, outdir: Path) -> None:
    weeks = json.loads(src.read_text())
    outdir.mkdir(parents=True, exist_ok=True)
    for name, palette in PALETTES.items():
        (outdir / name).write_text(build(weeks, palette))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
