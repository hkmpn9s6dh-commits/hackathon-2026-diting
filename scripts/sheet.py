"""A3 三视图展示页（3508×2480 @300dpi）。"""

from __future__ import annotations

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import character, copy
from rig.geom import BACK, FRONT, SIDE
from rig.render import PAPER, Renderer, bounds, svg_document
from scripts import fonts
from scripts.shot import shot

W, H = 3508, 2480
M = 120
INK = "#33322E"
GREY = "#7A756B"
LINE = "#D9D2C5"
LEFT_R = 2210
RIGHT_X = 2340
VIEW_TOP, BASELINE = 620, 1620
GAP = 64
KEY_T = [0.5, 4.9, 6.4, 9.2]


def _text(x, y, s, size, family="QTSans", color=INK, weight=400, spacing=0, anchor="start", opacity=1.0):
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" letter-spacing="{spacing}" text-anchor="{anchor}" '
        f'opacity="{opacity}">{s}</text>'
    )


def _wrap_cjk(s, limit):
    """按字数折行；不让标点落在行首，也不让末行只剩一两个字。"""
    no_head = "，。、；：？！）」』】…—"
    lines, cur = [], ""
    for ch in s:
        if len(cur) >= limit and ch not in no_head:
            lines.append(cur)
            cur = ""
        cur += ch
    if cur:
        lines.append(cur)
    if len(lines) >= 2 and len(lines[-1]) <= 3:
        tail = lines[-1]
        take = 4 - len(tail)
        moved = lines[-2][-take:]
        lines[-2] = lines[-2][:-take]
        lines[-1] = moved + tail
    return lines


def _frame_png(t, size=214):
    """裁到角色附近，缩成缩略图，返回 base64（省体积，也让角色在缩略图里够大）。"""
    from io import BytesIO

    from PIL import Image

    idx = max(0, min(449, int(round(t * 30))))
    path = f"out/_frames/f{idx:04d}.png"
    if not os.path.exists(path):
        raise SystemExit(f"缺关键帧 {path}：先跑 scripts/animate.py（或 scripts/build.py），"
                         f"展示页底部要贴四张帧。")
    im = Image.open(path)
    im = im.crop((196, 86, 884, 1016))
    im.thumbnail((size * 2, size * 2), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_svg():
    serif = fonts.data_uri(fonts.OUT["serif"])
    sans = fonts.data_uri(fonts.OUT["sans"])
    style = (
        "<style>"
        f"@font-face {{ font-family: QTSerif; src: url({serif}) format('woff2'); }}"
        f"@font-face {{ font-family: QTSans; src: url({sans}) format('woff2'); }}"
        "</style>"
    )

    parts = character.build()
    views = [FRONT, SIDE, BACK]
    boxes = [bounds(parts, v) for v in views]
    max_w = max(b[2] - b[0] for b in boxes)
    max_h = max(b[3] - b[1] for b in boxes)

    avail_w = LEFT_R - M
    scale = min((avail_w - GAP * 2) / (max_w * 3), (BASELINE - VIEW_TOP) / max_h)
    scale = round(scale, 2)

    center_x = M + avail_w / 2
    slot = max_w * scale + GAP
    start = center_x - slot * 1.5 + GAP / 2

    defs, bodies = [], []
    markers = []
    bodies.append(f'<line x1="{M}" y1="{BASELINE + 2}" x2="{LEFT_R}" y2="{BASELINE + 2}" stroke="#E6DFD2" stroke-width="2"/>')

    for i, (view, box) in enumerate(zip(views, boxes)):
        cx = start + slot * i + max_w * scale / 2 - (box[0] + box[2]) / 2 * scale
        cy = BASELINE - box[3] * scale
        rend = Renderer(scale=scale, cx=cx, cy=cy)
        d, b = rend.render(parts, view)
        defs.extend(d)
        bodies.append(f"<g>{b}</g>")
        zh, en = copy.VIEW_LABELS[i]
        bodies.append(_text(cx, BASELINE + 76, zh, 34, "QTSans", INK, 500, 7, "middle"))
        bodies.append(_text(cx, BASELINE + 120, en, 21, "QTSans", GREY, 400, 9, "middle"))

        if view is FRONT:
            for num, world in (
                ("01", (0.055, 1.155, 0.10)),
                ("02", (-0.300, 1.055, 0.06)),
                ("03", (0.075, 0.975, 0.26)),
                ("04", (0.085, 0.500, 0.30)),
            ):
                px = cx + world[0] * scale
                py = cy + (-world[1]) * scale
                markers.append((num, px, py))

    for num, px, py in markers:
        bodies.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="26" fill="{INK}" opacity="0.92"/>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="29" fill="none" stroke="{PAPER}" stroke-width="3"/>'
        )
        bodies.append(_text(px, py + 9, num, 23, "QTSans", PAPER, 500, 1, "middle"))

    # ---- 标题区
    bodies.append(_text(M, 350, copy.NAME, 164, "QTSerif", INK, 600, 12))
    bodies.append(_text(M + 8, 416, copy.NAME_ROMAN, 38, "QTSans", GREY, 400, 13))
    bodies.append(_text(M, 500, copy.TAGLINE, 44, "QTSans", INK, 400, 2))
    bodies.append(_text(M, 548, copy.TAGLINE_EN, 22, "QTSans", GREY, 400, 1))
    bodies.append(_text(LEFT_R, 350, "谛听 IP 形象", 26, "QTSans", GREY, 500, 8, "end"))
    bodies.append(_text(LEFT_R, 392, "DITING · CHARACTER SHEET", 20, "QTSans", GREY, 400, 5, "end"))

    # ---- 记忆点
    y = 700
    bodies.append(_text(RIGHT_X, y, copy.MEMORY_LABEL, 21, "QTSans", GREY, 500, 6))
    bodies.append(_text(RIGHT_X, y + 86, copy.MEMORY_TITLE, 66, "QTSerif", INK, 600, 2))
    for i, line in enumerate(copy.MEMORY_BODY.split("\n")):
        bodies.append(_text(RIGHT_X, y + 146 + i * 42, line, 26, "QTSans", "#4A4740", 400, 0.5))

    # ---- 四条注释
    ny = 1020
    for num, title, desc in copy.NOTES:
        bodies.append(_text(RIGHT_X, ny + 26, num, 25, "QTSans", "#A9803C", 600, 2))
        bodies.append(_text(RIGHT_X + 66, ny + 28, title, 33, "QTSans", INK, 600, 5))
        lines = _wrap_cjk(desc, 21)
        for k, line in enumerate(lines):
            bodies.append(_text(RIGHT_X + 66, ny + 76 + k * 38, line, 24, "QTSans", "#55514A", 400, 0.3))
        ny += 108 + 34 * (len(lines) - 1)

    # ---- 做法（为什么是 AIGC 做的）
    py = ny + 40
    bodies.append(_text(RIGHT_X, py, "做法 · PROCESS", 21, "QTSans", GREY, 500, 6))
    process = [
        "同一组三维体块，分别做正交投影：",
        "正视、侧视、背视——量的是同一只兽。",
        "改一次参数，三视图与 15 秒动效同时变。",
    ]
    for i, line in enumerate(process):
        bodies.append(_text(RIGHT_X, py + 48 + i * 38, line, 24, "QTSans", "#55514A", 400, 0.3))

    # ---- 关键帧条
    kx, ky, ks = M, 1852, 214
    bodies.append(_text(kx, ky - 22, "动作关键帧 · 15 秒白底动效", 24, "QTSans", GREY, 500, 4))
    for i, t in enumerate(KEY_T):
        x = kx + i * (ks + 34)
        bodies.append(
            f'<image x="{x}" y="{ky}" width="{ks}" height="{ks}" href="{_frame_png(t)}"/>'
        )
        bodies.append(
            f'<rect x="{x}" y="{ky}" width="{ks}" height="{ks}" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
        )
        bodies.append(_text(x, ky + ks + 30, f"{t:.1f}s", 19, "QTSans", GREY, 400, 1))

    # ---- 色卡
    cx0 = 1400
    bodies.append(_text(cx0, ky - 22, "色彩 · PALETTE", 24, "QTSans", GREY, 500, 4))
    for i, (zh, hexv, note) in enumerate(copy.COLORS):
        x = cx0 + i * 392
        bodies.append(
            f'<rect x="{x}" y="{ky}" width="80" height="80" rx="4" fill="{hexv}" '
            f'stroke="{LINE}" stroke-width="1.5"/>'
        )
        bodies.append(_text(x + 98, ky + 32, zh, 25, "QTSans", INK, 500, 3))
        bodies.append(_text(x + 98, ky + 64, hexv.upper(), 18, "QTSans", GREY, 400, 1))
        bodies.append(_text(x + 98, ky + 96, note, 18, "QTSans", GREY, 400, 1))

    # ---- 页脚
    bodies.append(f'<line x1="{M}" y1="2296" x2="{W - M}" y2="2296" stroke="{LINE}" stroke-width="2"/>')
    bodies.append(_text(M, 2346, copy.FOOTER_LEFT, 23, "QTSans", GREY, 400, 0.5))
    bodies.append(_text(W - M, 2346, copy.FOOTER_RIGHT, 23, "QTSans", GREY, 400, 0.5, "end"))

    svg = svg_document(W, H, defs, "".join(bodies), background=PAPER)
    return svg.replace("</svg>", style + "</svg>"), scale


def main(out="out/diting-turnaround-A3.png"):
    svg, scale = build_svg()
    tmp = os.path.abspath("out/_sheet.svg")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(svg)
    shot(tmp, out, W, H)
    print("scale", scale, "->", out)


if __name__ == "__main__":
    main()
