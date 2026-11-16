"""把 rig 画成 SVG。每个图元 = 一层"贴纸"：先画加粗外轮廓，再画渐变本体。"""

from __future__ import annotations

import math

from .geom import Ellipsoid, Part, Patch, Poly, Tube, View, sort_parts

PAPER = "#FBFAF7"
INK = "#33322E"


def _hex_rgb(h):
    if isinstance(h, (tuple, list)):
        return tuple(float(c) for c in h)
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(color, target, t):
    a, b = _hex_rgb(color), _hex_rgb(target)
    return _rgb_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def lighten(color, t):
    return mix(color, (255, 255, 255), t)


def darken(color, t):
    return mix(color, (0, 0, 0), t)


def _path(pts, close=True):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    return d + (" Z" if close else "")


class Renderer:
    def __init__(self, scale=800.0, cx=0.0, cy=0.0, outline=0.0075, paper=PAPER):
        self.scale = scale
        self.cx = cx
        self.cy = cy
        self.outline = outline       # 世界单位
        self.paper = paper

    def _map(self, p):
        return (self.cx + p[0] * self.scale, self.cy + p[1] * self.scale)

    def render(self, parts, view: View, defs_out=None, extra_after=""):
        palette = []
        for part in parts:
            if not part.visible(view.name):
                continue
            for sh in part.shapes:
                if isinstance(sh, (Ellipsoid, Tube, Patch)) and sh.color not in palette:
                    palette.append(sh.color)

        defs = [self._gradient(c) for c in palette] + [self._linear(c) for c in palette]
        body = []

        for part in sort_parts([p for p in parts if p.visible(view.name)], view):
            opened = False
            if part.rot and part.pivot:
                px, py = self._map(view.project_point((part.pivot[0], part.pivot[1], 0.0)))
                body.append(f'<g transform="rotate({part.rot:.3f} {px:.2f} {py:.2f})">')
                opened = True
            for sh in part.shapes:
                if isinstance(sh, Ellipsoid):
                    pts = [self._map(p) for p in sh.projected(view)]
                    d = _path(pts)
                    if sh.outline:
                        body.append(
                            f'<path d="{d}" fill="{INK}" stroke="{INK}" '
                            f'stroke-width="{2 * self.outline * self.scale:.2f}" '
                            f'stroke-linejoin="round" opacity="{sh.opacity:.3f}"/>'
                        )
                    body.append(
                        f'<path d="{d}" fill="url(#g{sh.color.lstrip("#")})" '
                        f'opacity="{sh.opacity:.3f}"/>'
                    )
                elif isinstance(sh, Patch):
                    pts = [self._map(p) for p in sh.projected(view)]
                    d = _path(pts)
                    if sh.outline:
                        body.append(
                            f'<path d="{d}" fill="{INK}" stroke="{INK}" '
                            f'stroke-width="{2 * self.outline * self.scale * 0.8:.2f}" '
                            f'stroke-linejoin="round" opacity="{sh.opacity:.3f}"/>'
                        )
                    body.append(
                        f'<path d="{d}" fill="url(#l{sh.color.lstrip("#")})" '
                        f'opacity="{sh.opacity:.3f}"/>'
                    )
                elif isinstance(sh, Tube):
                    pts = [self._map(p) for p in sh.outline(view)]
                    d = _path(pts)
                    body.append(
                        f'<path d="{d}" fill="{INK}" stroke="{INK}" '
                        f'stroke-width="{2 * self.outline * self.scale:.2f}" '
                        f'stroke-linejoin="round" opacity="{sh.opacity:.3f}"/>'
                    )
                    body.append(
                        f'<path d="{d}" fill="url(#l{sh.color.lstrip("#")})" '
                        f'opacity="{sh.opacity:.3f}"/>'
                    )
                elif isinstance(sh, Poly):
                    pts = [self._map(view.project_point(p)) for p in sh.points]
                    d = _path(pts, close=sh.closed)
                    body.append(
                        f'<path d="{d}" fill="none" stroke="{sh.color}" '
                        f'stroke-width="{sh.width * self.scale:.2f}" '
                        f'stroke-linecap="{sh.cap}" stroke-linejoin="round" '
                        f'opacity="{sh.opacity:.3f}"/>'
                    )
            if opened:
                body.append("</g>")

        body.append(extra_after)
        return defs, "\n      ".join(body)

    @staticmethod
    def _linear(color):
        cid = color.lstrip("#")
        return (
            f'<linearGradient id="l{cid}" x1="0.15" y1="0" x2="0.85" y2="1">'
            f'<stop offset="0%" stop-color="{lighten(color, 0.34)}"/>'
            f'<stop offset="42%" stop-color="{color}"/>'
            f'<stop offset="100%" stop-color="{darken(color, 0.24)}"/>'
            f"</linearGradient>"
        )

    @staticmethod
    def _gradient(color):
        cid = color.lstrip("#")
        return (
            f'<radialGradient id="g{cid}" cx="0.42" cy="0.38" r="0.72" fx="0.34" fy="0.30">'
            f'<stop offset="0%" stop-color="{lighten(color, 0.30)}"/>'
            f'<stop offset="46%" stop-color="{color}"/>'
            f'<stop offset="100%" stop-color="{darken(color, 0.22)}"/>'
            f"</radialGradient>"
        )


def svg_document(width, height, defs, body, background=PAPER, bg_rect=True):
    rect = (
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}"/>'
        if bg_rect else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"<defs>{''.join(defs)}</defs>"
        f"{rect}<g>{body}</g></svg>"
    )


def bounds(parts, view):
    xs, ys = [], []
    for part in parts:
        if not part.visible(view.name):
            continue
        for sh in part.shapes:
            if isinstance(sh, Ellipsoid):
                for p in sh.projected(view):
                    xs.append(p[0])
                    ys.append(p[1])
            elif isinstance(sh, Patch):
                for p in sh.projected(view):
                    xs.append(p[0])
                    ys.append(p[1])
            elif isinstance(sh, Tube):
                for p in sh.outline(view):
                    xs.append(p[0])
                    ys.append(p[1])
            elif isinstance(sh, Poly):
                for p in sh.points:
                    q = view.project_point(p)
                    xs.append(q[0])
                    ys.append(q[1])
    return min(xs), min(ys), max(xs), max(ys)


def spiral(center, radius, turns, steps, plane="yz", shrink=0.0, phase=0.0):
    """尾巴用的螺旋线，返回折线上的点。"""
    cx, cy, cz = center
    out = []
    for i in range(steps + 1):
        t = i / steps
        a = phase + t * turns * 2 * math.pi
        r = radius * (1.0 - shrink * t)
        if plane == "yz":
            out.append((cx, cy + r * math.sin(a), cz + r * math.cos(a)))
        else:
            out.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
    return out
