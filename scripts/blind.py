"""闸 D 的盲排材料：同题三版（round1）与外部参考混排（round2）。

答案表写到 proof/gate-d/key.json，不进任何给评委看的图。
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from rig import character
from rig.geom import FRONT
from rig.render import PAPER, Renderer, bounds, svg_document
from scripts.shot import shot

OUT = "proof/gate-d"
VARIANTS = {
    "A": dict(ear_scale=1.00, ear_pitch=0.0),
    "B": dict(ear_scale=0.86, ear_pitch=-6.0),
    "C": dict(ear_scale=1.10, ear_pitch=8.0),
}
PW, PH = 760, 940


def _font(size):
    for p in (
        r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render_variant(prm, out_png):
    parts = character.build(prm)
    x0, y0, x1, y1 = bounds(parts, FRONT)
    scale = min((PW - 120) / (x1 - x0), (PH - 140) / (y1 - y0))
    cx = PW / 2 - (x0 + x1) / 2 * scale
    cy = PH - 70 - y1 * scale
    rend = Renderer(scale=scale, cx=cx, cy=cy)
    defs, body = rend.render(parts, FRONT)
    svg = svg_document(PW, PH, defs, body, background=PAPER)
    tmp = os.path.abspath(f"{OUT}/_v.svg")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(svg)
    shot(tmp, out_png, PW, PH)


def build_round1():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for key, prm in VARIANTS.items():
        p = f"{OUT}/var-{key}.png"
        render_variant(prm, p)
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        d.text((34, 26), key, font=_font(64), fill="#2B2A26")
        tiles.append(im)
    sheet = Image.new("RGB", (PW * 3 + 40, PH), "#FFFFFF")
    for i, im in enumerate(tiles):
        sheet.paste(im, (i * (PW + 20), 0))
    sheet.save(f"{OUT}/round1.png")
    json.dump({"variants": VARIANTS}, open(f"{OUT}/key-r1.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("wrote", f"{OUT}/round1.png")


def build_round2(ours=f"{OUT}/var-A.png"):
    refs = ["bingdundun", "xuewang", "linabell", "molly", "kumamon"]
    items = [("ours", ours)] + [(k, f"_ref/{k}.png") for k in refs]
    letters = list("ABCDEF")
    rnd = random.Random(20261130)
    rnd.shuffle(items)
    cw, ch = 620, 780
    sheet = Image.new("RGB", (cw * 3 + 40, ch * 2 + 20), "#FFFFFF")
    key = {}
    for i, (who, path) in enumerate(items):
        im = Image.open(path).convert("RGB")
        im.thumbnail((cw - 40, ch - 60), Image.LANCZOS)
        cell = Image.new("RGB", (cw, ch), "#FFFFFF")
        cell.paste(im, ((cw - im.width) // 2, (ch - im.height) // 2 + 20))
        d = ImageDraw.Draw(cell)
        d.text((24, 16), letters[i], font=_font(52), fill="#2B2A26")
        x, y = (i % 3) * (cw + 20), (i // 3) * (ch + 10)
        sheet.paste(cell, (x, y))
        key[letters[i]] = who
    sheet.save(f"{OUT}/round2.png")
    json.dump(key, open(f"{OUT}/key-r2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("wrote", f"{OUT}/round2.png", key)


def build_round1_r2():
    """第 2 轮的同题盲排：v1 原版、v1 里评委偏好的那版、改法后的 v2。"""
    from rig import character

    os.makedirs(OUT, exist_ok=True)
    panels = {
        "P": dict(ear_scale=1.00, ear_pitch=0.0),                        # v1 原版
        "Q": dict(ear_scale=1.10, ear_pitch=8.0),                        # v1 里更竖的那版
        "R": dict(character.POSE, ear_scale=1.00, ear_pitch=0.0),        # v2 改法版
    }
    tiles = []
    for key, prm in panels.items():
        p = f"{OUT}/v2-{key}.png"
        render_variant(prm, p)
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        d.text((34, 26), key, font=_font(64), fill="#2B2A26")
        tiles.append(im)
    sheet = Image.new("RGB", (PW * 3 + 40, PH), "#FFFFFF")
    for i, im in enumerate(tiles):
        sheet.paste(im, (i * (PW + 20), 0))
    sheet.save(f"{OUT}/round1-r2.png")
    json.dump({"panels": {k: {kk: vv for kk, vv in v.items()} for k, v in panels.items()}},
              open(f"{OUT}/key-r1r2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("wrote", f"{OUT}/round1-r2.png")


if __name__ == "__main__":
    build_round1()
    build_round1_r2()
    build_round2(ours=f"{OUT}/v2-R.png")
