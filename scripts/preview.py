"""快速预览：三个视图并排出一张 PNG，供肉眼检查。"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import character
from rig.geom import BACK, FRONT, SIDE
from rig.render import PAPER, Renderer, bounds, svg_document
from scripts.shot import shot

W, H = 420, 560
SCALE = 330
GAP = 24
PAD = 30


def main(out="out/preview.png", params=None, variants=None):
    views = [FRONT, SIDE, BACK]
    variants = variants or [("", params or {})]
    rows = len(variants)
    total_w = (W * 3 + GAP * 2) * 1 + PAD * 2
    total_h = (H) * rows + PAD * 2

    defs, bodies = [], []
    for r, (label, prm) in enumerate(variants):
        parts = character.build(prm)
        for c, view in enumerate(views):
            x0, y0, x1, y1 = bounds(parts, view)
            scale = min(SCALE, SCALE)
            cx = PAD + c * (W + GAP) + W / 2 - (x0 + x1) / 2 * scale
            cy = PAD + r * H + H * 0.56 - (y0 + y1) / 2 * scale
            rend = Renderer(scale=scale, cx=cx, cy=cy)
            d, b = rend.render(parts, view)
            defs.extend(d)
            bodies.append(
                f'<g>{b}</g>'
                f'<text x="{PAD + c * (W + GAP) + W / 2}" y="{PAD + r * H + H - 12}" '
                f'font-family="sans-serif" font-size="14" fill="#888" text-anchor="middle">'
                f'{label} {view.name}</text>'
            )
    svg = svg_document(total_w, total_h, defs, "".join(bodies), background=PAPER)
    os.makedirs("out", exist_ok=True)
    tmp = os.path.abspath("out/_preview.svg")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(svg)
    shot(tmp, out, total_w, total_h)
    print("wrote", out)


if __name__ == "__main__":
    main()
