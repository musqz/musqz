#!/usr/bin/env python3
"""Generate assets/globe.svg: words on a rotating Fibonacci sphere (SMIL, no JS)."""
import math
import random
import sys
from pathlib import Path

WORDS = [
    "archcanary", "mabox", "eBPF", "X11", "Wayland", "Qt", "GTK", "systemd",
    "quickbox", "forum-scout", "tabdock", "fittsmon", "skippy-wl", "volbar",
    "Bash", "Python", "C", "Arch", "Linux", "AUR", "PKGBUILD", "AppImage",
    "quickemu", "supply-chain", "snapshot", "persistence", "kmod", "DKMS",
    "polkit", "labwc", "noctalia", "icons", "dock", "TUI", "scanner",
    "hot-edges", "VM", "KDE", "XFCE", "pacman",
]
W, H = 560, 360
CX, CY, R = W / 2, H / 2, 135
FRAMES, DUR = 36, 24
FG, DIM = "#7ee787", "#8b949e"


def main(out: Path) -> None:
    rnd = random.Random(7)
    n = len(WORDS)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="ui-monospace,Menlo,Consolas,monospace">',
        f'<rect width="{W}" height="{H}" rx="8" fill="#0d1117"/>',
    ]
    for i, word in enumerate(WORDS):
        y0 = 1 - 2 * (i + 0.5) / n
        rad = math.sqrt(1 - y0 * y0)
        a0 = i * math.pi * (3 - math.sqrt(5))
        cycles = rnd.choice([1, 2, 3])
        phase = rnd.random() * 2 * math.pi
        xs, ys, os_, ss = [], [], [], []
        for f in range(FRAMES + 1):
            a = a0 + 2 * math.pi * f / FRAMES
            x, z = rad * math.cos(a), rad * math.sin(a)
            depth = (z + 1) / 2
            fade = 0.5 + 0.5 * math.cos(2 * math.pi * cycles * f / FRAMES + phase)
            fade = min(1.0, fade * 1.6)
            xs.append(f"{CX + R * x:.1f}")
            ys.append(f"{CY + R * y0:.1f}")
            os_.append(f"{(0.12 + 0.88 * depth ** 1.5) * fade:.2f}")
            ss.append(f"{9 + 8 * depth:.1f}")
        fill = FG if i % 3 == 0 else DIM
        parts.append(f'<text text-anchor="middle" fill="{fill}" x="{xs[0]}" y="{ys[0]}">{word}')
        for attr, vals in (("x", xs), ("opacity", os_), ("font-size", ss)):
            parts.append(
                f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" '
                f'values="{";".join(vals)}"/>'
            )
        parts.append("</text>")
    parts.append("</svg>")
    out.write_text("\n".join(parts))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "assets" / "globe.svg")
