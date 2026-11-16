"""三个视图的透明 PNG（1500×1500），单独交件用。"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import character
from rig.geom import BACK, FRONT, SIDE
from rig.render import PAPER, Renderer, bounds, svg_document
from scripts.shot import shot

S = 1500


def one(view, out):
    parts = character.build(character.POSE)
    x0, y0, x1, y1 = bounds(parts, view)
    scale = (S * 0.80) / max(x1 - x0, y1 - y0)
    cx = S / 2 - (x0 + x1) / 2 * scale
    cy = S / 2 - (y0 + y1) / 2 * scale
    rend = Renderer(scale=scale, cx=cx, cy=cy)
    defs, body = rend.render(parts, view)
    svg = svg_document(S, S, defs, body, background=PAPER, bg_rect=False)
    tmp = os.path.abspath(f"out/_{view.name}.svg")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(svg)
    shot(tmp, out, S, S, transparent=True)
    print("wrote", out)


def main():
    for view, name in ((FRONT, "front"), (SIDE, "side"), (BACK, "back")):
        one(view, f"out/diting-{name}.png")


if __name__ == "__main__":
    main()
