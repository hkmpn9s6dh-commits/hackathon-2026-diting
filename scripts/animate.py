"""15 秒白底动效：逐帧算 SVG → chromium 批量截图 → ffmpeg 合成。"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from rig import character
from rig.geom import FRONT
from rig.render import PAPER, Renderer, bounds, svg_document
from scripts.shot import shot

W = H = 1080
FPS = 30
DURATION = 15.0
FRAMES = int(FPS * DURATION)
GRID = 3
CELL = W * GRID


def _ss(x):
    return x * x * (3 - 2 * x)


def key(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return v0 + (v1 - v0) * _ss(max(0.0, min(1.0, u)))
    return keys[-1][1]


def params_at(t):
    p = character.POSE
    return dict(
        ear_l=p["ear_l"] + key(t, [(0, 0), (2.6, 0), (3.7, 11), (6.0, 7), (8.2, 4), (10.9, 0), (15, 0)]),
        ear_r=p["ear_r"] + key(t, [(0, 0), (3.0, 0), (4.1, 4), (6.5, 2), (10.9, 0), (15, 0)]),
        head_tilt=p["head_tilt"] + key(t, [(0, 0), (2.9, 0), (4.1, -6.0), (6.3, -9.0), (8.2, -6.0), (10.9, 0), (15, 0)]),
        face_yaw=p["face_yaw"] + key(t, [(0, 0), (3.1, 0), (4.5, -6), (7.0, -9.5), (9.6, -4), (11.0, 0), (15, 0)]),
        eye_open=key(t, [(0, 0), (4.3, 0), (4.9, 1), (10.6, 1), (11.3, 0), (15, 0)]),
        hop=key(t, [(0, 0), (5.80, 0), (6.10, 0.050), (6.40, 0.055), (6.72, 0), (15, 0)]),
        squash=key(t, [(0, 1), (5.80, 1), (6.02, 0.955), (6.30, 1.020), (6.80, 1.0), (15, 1)]),
        bell_swing=key(t, [(0, 0), (5.9, 0), (6.3, 16), (6.8, -10), (7.3, 4), (7.9, 0), (15, 0)]),
        tail_wave=0.22 * math.sin(2 * 3.141592653589793 * t / 5.0),
        breath=1 + 0.012 * math.sin(2 * 3.141592653589793 * t / 3.75),
    )


def ring_overlay(t, cx, cy, scale):
    """两道极淡的声波，从左边钟口扩散。8.0–11.0 s。"""
    out = []
    for k, offset in enumerate((0.0, 0.6)):
        tt = t - 8.0 - offset
        if 0 <= tt <= 2.4:
            u = tt / 2.4
            r = (0.12 + 0.55 * u) * scale
            a = 0.10 * (1 - u) ** 1.6
            out.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" '
                f'stroke="#6E7F79" stroke-width="3" opacity="{a:.3f}"/>'
            )
    return "".join(out)


def frame_body(t):
    parts = character.build(params_at(t))
    x0, y0, x1, y1 = bounds(parts, FRONT)
    scale = 760.0
    cx = W / 2 - (x0 + x1) / 2 * scale
    cy = 1005 - y1 * scale
    rend = Renderer(scale=scale, cx=cx, cy=cy)
    defs, body = rend.render(parts, FRONT)
    # 钟口位置（左耳）
    ear_x = cx - 0.33 * scale
    ear_y = cy - 0.92 * scale
    body += ring_overlay(t, ear_x, ear_y, scale)
    return defs, body


def build_grid(indices):
    defs, bodies = [], []
    for n, idx in enumerate(indices):
        t = idx / FPS
        d, b = frame_body(t)
        defs.extend(d)
        col, row = n % GRID, n // GRID
        bodies.append(
            f'<svg x="{col * W}" y="{row * H}" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>{b}</svg>'
        )
    return svg_document(CELL, CELL, defs, "".join(bodies), background=PAPER)


def main(out_mp4="out/diting-motion-15s.mp4"):
    tmp = os.path.abspath("out/_frames")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    for start in range(0, FRAMES, GRID * GRID):
        indices = list(range(start, min(start + GRID * GRID, FRAMES)))
        svg = build_grid(indices)
        path = os.path.abspath("out/_grid.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        png = os.path.abspath("out/_grid.png")
        shot(path, png, CELL, CELL)
        im = Image.open(png)
        for n, frame_idx in enumerate(indices):
            col, row = n % GRID, n // GRID
            tile = im.crop((col * W, row * H, (col + 1) * W, (row + 1) * H))
            tile.save(os.path.join(tmp, f"f{frame_idx:04d}.png"))
        print(f"batch {start // (GRID * GRID) + 1}: {min(start + GRID * GRID, FRAMES)}/{FRAMES}", flush=True)

    audio = os.path.abspath("out/_audio.wav")
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"),
        "-i", audio,
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
        out_mp4,
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print("wrote", out_mp4)


if __name__ == "__main__":
    main()
