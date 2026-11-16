"""《青听》角色 rig。

一只蹲坐的小谛听：头大身圆，独角短如石笋，耳朵是两口倒扣的钟，
闭眼听声，额上一枚朱砂点。全部由椭球拼成，三个视图是同一份 rig 的正交投影。
"""

from __future__ import annotations

import math

from .geom import Ellipsoid, Part, Patch, Poly, Tube, euler, rot_z

STONE = "#7B8B84"      # 青灰（岩体）
MOSS = "#4E6455"       # 苔青（耳背、尾巴暗部）
CINNABAR = "#B8402C"   # 朱砂（额头一点）
BRONZE = "#A9803C"     # 铜金（钟箍、颈铃）
CREAM = "#EFE7D8"      # 米白（腹、口鼻）
INK = "#33322E"        # 墨（鼻、口、眼）

PALETTE = [STONE, MOSS, CINNABAR, BRONZE, CREAM, INK]

BASE = dict(
    ear_style="bell",
    eye_open=0.0,        # 0 闭眼弧，1 睁圆
    face_yaw=0.0,        # 面部特征左右位移（度）
    head_tilt=0.0,       # 头左右倾（度）
    hop=0.0,             # 离地高度（世界单位）
    squash=1.0,          # 竖向压缩
    breath=1.0,          # 呼吸缩放
    ear_l=0.0,           # 左耳外转角（度）
    ear_r=0.0,
    tail_wave=0.0,       # 尾尖摆动相位
    bell_swing=0.0,
    ear_scale=1.0,       # 耳朵整体缩放（盲排用）
    ear_pitch=0.0,       # 耳朵与水平面的夹角增量（度）
)


def _lerp(a, b, t):
    return a + (b - a) * t


def _chain(attach, direction, length, r0, r1, n, color, curve=0.0, steps=40):
    """沿一条（可弯的）线堆球，返回 [(点, 半径)]。"""
    dx, dy, dz = direction
    norm = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    dx, dy, dz = dx / norm, dy / norm, dz / norm
    out = []
    for i in range(n):
        t = i / (n - 1)
        px = attach[0] + dx * length * t + curve * math.sin(math.pi * t) * -dy
        py = attach[1] + dy * length * t + curve * math.sin(math.pi * t) * dx
        pz = attach[2] + dz * length * t
        out.append(((px, py, pz), _lerp(r0, r1, t ** 1.25)))
    return out


def _ear_frame(side, params):
    """耳朵的局部坐标系：dir 沿耳长，perp 在耳面内横跨，normal 朝前外。"""
    droop = params.get("ear_l" if side < 0 else "ear_r", 0.0)
    attach = (side * 0.185, 0.930, 0.030)
    pitch = math.radians(61 + droop + params.get('ear_pitch', 0.0))  # 与水平面的夹角
    yaw = math.radians(38)                     # 耳面朝外转
    dx, dy, dz = side * math.cos(pitch), math.sin(pitch), 0.05
    m = math.sqrt(dx * dx + dy * dy + dz * dz)
    d = (dx / m, dy / m, dz / m)
    n = (side * math.sin(yaw), 0.0, math.cos(yaw))
    # perp = n × d
    px = n[1] * d[2] - n[2] * d[1]
    py = n[2] * d[0] - n[0] * d[2]
    pz = n[0] * d[1] - n[1] * d[0]
    mm = math.sqrt(px * px + py * py + pz * pz)
    perp = (px / mm, py / mm, pz / mm)
    if perp[1] < 0:                      # 保证 v=+1 永远朝上，左右耳同构
        perp = (-perp[0], -perp[1], -perp[2])
    return attach, d, perp, n


def _ear_point(attach, d, perp, n, u, v, w_scale=1.0, depth=0.0, scale=1.0):
    L, W = 0.300 * scale, 0.128 * w_scale * scale
    bend = 0.075 * u * u                    # 耳身向外弯一点，别像兔耳那样笔直
    return (
        attach[0] + d[0] * L * u + perp[0] * W * v + n[0] * depth + bend * (1 if attach[0] > 0 else -1),
        attach[1] + d[1] * L * u + perp[1] * W * v + n[1] * depth - 0.022 * u * u,
        attach[2] + d[2] * L * u + perp[2] * W * v + n[2] * depth,
    )


def _ear_width(u):
    """耳宽（相对半宽）：根部略窄，中段最宽，尖端收成圆头（不收成尖）。"""
    taper = max(0.0, 1 - u ** 5.0)
    return (0.74 + 0.40 * math.sin(math.pi * (u ** 0.82))) * (0.26 + 0.74 * math.sqrt(taper))


def _bell_ear(side, params):
    """一片大耳：外壳 + 内耳 + 七道水纹 + 耳缘。side = -1 左，+1 右。"""
    attach, d, perp, n = _ear_frame(side, params)
    es = params.get("ear_scale", 1.0)
    shapes = []

    # 背片（给侧视一点厚度）
    back = []
    for i in range(17):
        u = i / 16
        back.append(_ear_point(attach, d, perp, n, u, _ear_width(u), depth=-0.018, scale=es))
    for i in range(16, -1, -1):
        u = i / 16
        back.append(_ear_point(attach, d, perp, n, u, -_ear_width(u), depth=-0.018, scale=es))
    shapes.append(Patch(back, MOSS))

    # 外壳
    shell = []
    for i in range(19):
        u = i / 18
        shell.append(_ear_point(attach, d, perp, n, u, _ear_width(u), scale=es))
    for i in range(18, -1, -1):
        u = i / 18
        shell.append(_ear_point(attach, d, perp, n, u, -_ear_width(u), scale=es))
    shapes.append(Patch(shell, STONE))

    # 内耳（米白）
    inner = []
    for i in range(17):
        u = 0.08 + 0.82 * i / 16
        inner.append(_ear_point(attach, d, perp, n, u, _ear_width(u) * 0.66, depth=0.004, scale=es))
    for i in range(16, -1, -1):
        u = 0.08 + 0.82 * i / 16
        inner.append(_ear_point(attach, d, perp, n, u, -_ear_width(u) * 0.66, depth=0.004, scale=es))
    shapes.append(Patch(inner, CREAM, outline=False))

    # 七道水纹（七布泉）
    for k in range(7):
        v0 = -0.58 + 1.16 * k / 6
        line = []
        for i in range(12):
            t = i / 11
            u = 0.14 + 0.70 * t
            line.append(
                _ear_point(
                    attach, d, perp, n, u,
                    v0 * (0.55 + 0.45 * t) * _ear_width(u),
                    depth=0.006,
                    scale=es,
                )
            )
        shapes.append(Poly(line, MOSS, 0.0072, opacity=0.62))

    # 耳缘
    rim = []
    for i in range(19):
        u = i / 18
        rim.append(_ear_point(attach, d, perp, n, u, _ear_width(u), depth=0.002))
    for i in range(19):
        u = 1.0 - i / 18
        rim.append(_ear_point(attach, d, perp, n, u, -_ear_width(u), depth=0.002))
    shapes.append(Tube(rim + [rim[0]], [0.0105] * (len(rim) + 1), MOSS))

    return shapes


def build(params=None):
    p = dict(BASE)
    if params:
        p.update(params)

    hop = p["hop"]
    squash = p["squash"]
    breath = p["breath"]
    yaw = math.radians(p["face_yaw"])
    tilt = p["head_tilt"]

    parts = []

    # ---- 尾巴（身后一枚泉水的卷，螺旋朝后）
    tail_pts, tail_rad = [], []
    for i in range(22):
        t = i / 21
        ang = math.radians(-30) + t * math.radians(430) + p["tail_wave"]
        rr = 0.125 * (1 - 0.30 * t)
        tail_pts.append(
            (
                rr * math.sin(ang),
                0.375 + rr * math.cos(ang) * 0.85 + hop,
                -0.215 - 0.115 * t,
            )
        )
        tail_rad.append(0.046 * (1 - 0.50 * t))
    parts.append(
        Part("tail", (0.0, 0.375 + hop, -0.26), [Tube(tail_pts, tail_rad, STONE)])
    )

    # ---- 后腿
    for side in (-1, 1):
        thigh = Ellipsoid(
            center=(side * 0.215, 0.185 + hop, -0.045),
            radii=(0.105, 0.135, 0.115),
            color=STONE,
        )
        paw = Ellipsoid(
            center=(side * 0.235, 0.055 + hop, 0.035),
            radii=(0.095, 0.058, 0.12),
            color=STONE,
        )
        parts.append(Part(f"hind{side}", (side * 0.215, 0.12 + hop, -0.045), [thigh, paw]))

    # ---- 身体
    body = Ellipsoid(
        center=(0.0, 0.38 * squash + hop, -0.02),
        radii=(0.295 / math.sqrt(squash) * breath, 0.29 * squash * breath, 0.255),
        color=STONE,
    )
    parts.append(Part("body", (0.0, 0.38 + hop, -0.02), [body]))

    # ---- 胸腹（米白）
    belly = Ellipsoid(
        center=(0.0, 0.345 * squash + hop, 0.145),
        radii=(0.185 / math.sqrt(squash) * breath, 0.20 * squash * breath, 0.135),
        color=CREAM,
    )
    parts.append(Part("belly", (0.0, 0.345 + hop, 0.145), [belly]))

    # ---- 前腿
    for side in (-1, 1):
        leg = Ellipsoid(
            center=(side * 0.155, 0.20 * squash + hop, 0.165),
            radii=(0.072, 0.16 * squash, 0.075),
            color=STONE,
        )
        paw = Ellipsoid(
            center=(side * 0.165, 0.055 + hop, 0.215),
            radii=(0.085, 0.055, 0.105),
            color=CREAM,
        )
        parts.append(Part(f"fore{side}", (side * 0.155, 0.15 + hop, 0.19), [leg, paw]))

    # ---- 颈铃
    swing = math.radians(p["bell_swing"])
    bx = 0.0 + 0.035 * math.sin(swing)
    bell = Ellipsoid(
        center=(bx, 0.545 * squash + hop, 0.245),
        radii=(0.052, 0.052, 0.045),
        color=BRONZE,
    )
    bell_line = Ellipsoid(
        center=(bx, 0.512 * squash + hop, 0.245),
        radii=(0.050, 0.010, 0.042),
        color=INK,
    )
    parts.append(Part("bell", (bx, 0.545 + hop, 0.245), [bell, bell_line]))

    # ---- 头
    head_y = 0.775 * squash + hop
    head = Ellipsoid(
        center=(0.0, head_y, 0.015),
        radii=(0.285, 0.265, 0.255),
        color=STONE,
        rot=euler(0, 0, tilt * 0.5),
    )
    parts.append(Part("head", (0.0, head_y, 0.015), [head], views=None))

    # ---- 耳朵（画在头之前 → 根部被头盖住），但深度排序会把它放前面；
    #      用 bias 让它落在头之后画
    for side in (-1, 1):
        shapes = _bell_ear(side, p)
        parts.append(
            Part(f"ear{side}", (side * 0.205, 0.965 + hop, -0.02), shapes)
        )

    # ---- 独角（石笋）
    horn_pts, horn_rad = [], []
    for i in range(7):
        t = i / 6
        horn_pts.append((0.0, (0.985 + 0.215 * t) * squash + hop, 0.040 + 0.055 * t))
        horn_rad.append(0.062 * (1 - t) ** 1.30 + 0.008)
    parts.append(
        Part(
            "horn",
            (0.0, 1.05 + hop, 0.045),
            [
                Tube(horn_pts, horn_rad, CREAM),
                Tube(horn_pts[5:], [r + 0.002 for r in horn_rad[5:]], BRONZE),
            ],
        )
    )

    # ---- 口鼻
    muzzle = Ellipsoid(
        center=(math.sin(yaw) * 0.16, 0.705 * squash + hop, 0.215),
        radii=(0.155, 0.105, 0.115),
        color=CREAM,
    )
    parts.append(Part("muzzle", (0.0, 0.705 + hop, 0.215), [muzzle]))

    nose = Ellipsoid(
        center=(math.sin(yaw) * 0.17, 0.742 * squash + hop, 0.318),
        radii=(0.036, 0.026, 0.022),
        color=INK,
        rot=euler(0, 0, 0),
    )
    parts.append(Part("nose", (math.sin(yaw) * 0.17, 0.742 + hop, 0.318), [nose]))

    # ---- 闭眼 / 睁眼（交叉淡入，避免形状跳变）
    eye_w = 0.056
    eye_y = 0.792 * squash + hop
    k = max(0.0, min(1.0, p["eye_open"]))
    for side in (-1, 1):
        cx = side * 0.118 * math.cos(yaw) + math.sin(yaw) * 0.16
        z = 0.268 - abs(math.sin(yaw)) * 0.02
        arc = []
        for i in range(11):
            t = i / 10
            x = cx - eye_w + 2 * eye_w * t
            y = eye_y + 0.024 * math.sin(math.pi * t)
            arc.append((x, y, z))
        shapes = []
        if k < 0.999:
            shapes.append(Poly(arc, INK, 0.015, opacity=1.0 - k))
        if k > 0.001:
            shapes.append(
                Ellipsoid(
                    center=(cx, eye_y + 0.006, z),
                    radii=(eye_w * 0.72, 0.014 + 0.024 * k, 0.012),
                    color=INK,
                    steps=40,
                    outline=False,
                    opacity=k,
                )
            )
            shapes.append(
                Ellipsoid(
                    center=(cx + 0.010, eye_y + 0.026, z + 0.004),
                    radii=(0.0085, 0.0085, 0.006),
                    color="#FFFFFF",
                    steps=28,
                    outline=False,
                    opacity=k,
                )
            )
        parts.append(Part(f"eye{side}", (cx, eye_y, z + 0.01), shapes))

    # ---- 嘴
    mouth = []
    for i in range(9):
        t = i / 8
        x = (-0.030 + 0.060 * t) + math.sin(yaw) * 0.18
        y = 0.672 * squash + hop - 0.012 * math.sin(math.pi * t)
        mouth.append((x, y, 0.305))
    parts.append(Part("mouth", (0.0, 0.672 + hop, 0.305), [Poly(mouth, INK, 0.011)]))

    # ---- 额上朱砂
    dot = Ellipsoid(
        center=(math.sin(yaw) * 0.11, 0.905 * squash + hop, 0.238),
        radii=(0.026, 0.026, 0.012),
        color=CINNABAR,
        steps=40,
        outline=False,
    )
    parts.append(Part("dot", (0.0, 0.905 + hop, 0.238), [dot]))

    # 头部整体随着 tilt 旋转（屏幕空间绕颈根）
    head_names = {"head", "horn", "muzzle", "nose", "mouth", "dot", "ear-1", "ear1",
                  "eye-1", "eye1"}
    for part in parts:
        if part.name in head_names:
            part.rot = p["head_tilt"]
            part.pivot = (0.0, 0.775 * squash + hop)

    return parts


def height_of(parts, view):
    from .render import bounds

    x0, y0, x1, y1 = bounds(parts, view)
    return y1 - y0
