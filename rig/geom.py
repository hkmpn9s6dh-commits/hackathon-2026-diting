"""几何：椭球 rig → 正交投影 → SVG。

坐标：X 向右，Y 向上，Z 朝观察者（角色面朝 +Z）。
世界单位里角色总高约 1.0；输出时再乘像素比例。

一个椭球：中心 c（3 维）、半径 r（3 维）、姿态 R（3×3）。
正交投影到某个视图后，边界是一个精确的椭圆：
    Σ2 = (R · diag(r²) · Rᵀ) 取视图平面两行两列
    p(θ) = c2 + L · (cosθ, sinθ)，L 是 Σ2 的 Cholesky 因子
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

Vec3 = tuple


# ---------------------------------------------------------------- 线性代数

def mat_mul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def mat_vec(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rot_y(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def rot_z(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def euler(yaw=0.0, pitch=0.0, roll=0.0):
    """先滚后俯仰再偏航（对角色来说直觉：roll 绕自身前后轴）。"""
    return mat_mul(rot_y(yaw), mat_mul(rot_x(pitch), rot_z(roll)))


def cholesky2(a, b, c):
    """Σ = [[a, b], [b, c]] → L，使 L·Lᵀ = Σ。"""
    if a <= 0 or a * c - b * b <= 0:
        a = max(a, 1e-12)
        c = max(c, a * 1e-12 + b * b / a)
    l11 = math.sqrt(a)
    l21 = b / l11
    l22 = math.sqrt(max(c - l21 * l21, 1e-12))
    return ((l11, 0.0), (l21, l22))


# ---------------------------------------------------------------- 视图

@dataclass(frozen=True)
class View:
    """正交视图。screen_x/screen_y 是世界轴；depth 是世界轴（越大越靠前）。"""

    name: str
    screen_x: int   # 0=X 1=Y 2=Z
    screen_y: int
    depth: int
    flip_x: bool = False
    flip_y: bool = False   # SVG 的 y 向下，默认翻转
    depth_sign: int = 1    # 从负方向看时为 -1（背面视图）

    def project_point(self, p):
        x = p[self.screen_x] * (-1 if self.flip_x else 1)
        y = p[self.screen_y] * (-1 if self.flip_y else 1)
        return (x, y)

    def depth_of(self, p):
        return p[self.depth] * self.depth_sign


FRONT = View("front", 0, 1, 2, flip_y=True)
SIDE = View("side", 2, 1, 0, flip_y=True)     # 从 +X 看：屏幕横轴是 +Z（脸朝右）
BACK = View("back", 0, 1, 2, flip_x=True, flip_y=True, depth_sign=-1)


# ---------------------------------------------------------------- 图元

@dataclass
class Ellipsoid:
    center: Sequence[float]
    radii: Sequence[float]
    color: str
    rot: Sequence[Sequence[float]] = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    steps: int = 72
    outline: bool = True
    opacity: float = 1.0
    tags: tuple = ()

    def projected(self, view: View):
        c2 = view.project_point(self.center)
        # Σ = R · diag(r²) · Rᵀ
        r2 = [self.radii[0] ** 2, self.radii[1] ** 2, self.radii[2] ** 2]
        sigma = [[0.0] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                sigma[i][j] = sum(
                    self.rot[i][k] * r2[k] * self.rot[j][k] for k in range(3)
                )
        i, j = view.screen_x, view.screen_y
        sx = -1 if view.flip_x else 1
        sy = -1 if view.flip_y else 1
        a = sigma[i][i]
        b = sigma[i][j] * sx * sy
        c = sigma[j][j]
        chol = cholesky2(a, b, c)
        l11, l21, l22 = chol[0][0], chol[1][0], chol[1][1]
        pts = []
        for k in range(self.steps):
            t = 2 * math.pi * k / self.steps
            dx = l11 * math.cos(t)
            dy = l21 * math.cos(t) + l22 * math.sin(t)
            pts.append((c2[0] + sx * dx, c2[1] + sy * dy))
        return pts

    def width_height(self, view: View):
        pts = self.projected(view)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return max(xs) - min(xs), max(ys) - min(ys)


@dataclass
class Poly:
    """屏幕空间折线（已经算好的 2D 点），用来画口鼻线、闭眼、声波等。"""

    points: Sequence[Sequence[float]]
    color: str
    width: float
    closed: bool = False
    opacity: float = 1.0
    cap: str = "round"


@dataclass
class Patch:
    """一块 3D 平面多边形（耳朵这类薄片）。投影就是把点投下来。"""

    points: Sequence[Sequence[float]]
    color: str
    opacity: float = 1.0
    outline: bool = True

    def projected(self, view: View):
        return [view.project_point(p) for p in self.points]


@dataclass
class Tube:
    """沿 3D 折线扫出的变径管（耳、角、尾）。投影后用两侧偏移曲线算轮廓，
    避免"一串球"的棱。"""

    points: Sequence[Sequence[float]]
    radii: Sequence[float]
    color: str
    cap_steps: int = 10
    opacity: float = 1.0

    def outline(self, view: View):
        pts = [view.project_point(p) for p in self.points]
        rs = list(self.radii)
        n = len(pts)
        if n == 0:
            return []
        if n == 1:
            rs = [rs[0], rs[0]]
            pts = [pts[0], pts[0]]
            n = 2

        def sub(a, b):
            return (a[0] - b[0], a[1] - b[1])

        def unit(v):
            m = math.hypot(v[0], v[1]) or 1.0
            return (v[0] / m, v[1] / m)

        left, right, tangents = [], [], []
        for i in range(n):
            if i == 0:
                t = sub(pts[1], pts[0])
            elif i == n - 1:
                t = sub(pts[-1], pts[-2])
            else:
                t = sub(pts[i + 1], pts[i - 1])
            t = unit(t)
            tangents.append(t)
            nx, ny = -t[1], t[0]
            left.append((pts[i][0] + nx * rs[i], pts[i][1] + ny * rs[i]))
            right.append((pts[i][0] - nx * rs[i], pts[i][1] - ny * rs[i]))

        a_end = math.atan2(tangents[-1][1], tangents[-1][0])
        cap_end = []
        for k in range(self.cap_steps + 1):
            ang = a_end + math.pi / 2 - math.pi * k / self.cap_steps
            cap_end.append(
                (pts[-1][0] + math.cos(ang) * rs[-1], pts[-1][1] + math.sin(ang) * rs[-1])
            )
        a_start = math.atan2(tangents[0][1], tangents[0][0])
        cap_start = []
        for k in range(self.cap_steps + 1):
            ang = a_start - math.pi / 2 - math.pi * k / self.cap_steps
            cap_start.append(
                (pts[0][0] + math.cos(ang) * rs[0], pts[0][1] + math.sin(ang) * rs[0])
            )
        return left + cap_end + list(reversed(right)) + cap_start


@dataclass
class Part:
    """一组图元，作为一个整体参与深度排序（耳朵、尾巴这类链）。"""

    name: str
    anchor: Sequence[float]
    shapes: list = field(default_factory=list)
    views: tuple | None = None      # None = 三个视图都画
    rot: float = 0.0                # 屏幕空间绕 pivot 旋转（度）
    pivot: Sequence[float] | None = None   # 世界坐标 (x, y)

    def visible(self, view_name):
        return self.views is None or view_name in self.views


def chain(points_with_radius, color, steps=48):
    """沿折线堆椭球，半径按折线给出的值插值。用于腿、尾巴、钟耳。"""
    out = []
    for (p, r) in points_with_radius:
        out.append(Ellipsoid(center=p, radii=(r, r, r), color=color, steps=steps))
    return out


# ---------------------------------------------------------------- 深度排序

def sort_parts(parts: Iterable[Part], view: View):
    """远的先画：depth 大的靠前，所以按 depth 升序。"""
    return sorted(parts, key=lambda part: view.depth_of(part.anchor))
