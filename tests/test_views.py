import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import character  # noqa: E402
from rig.geom import BACK, FRONT, SIDE  # noqa: E402
from rig.render import bounds  # noqa: E402


class TestTurnaroundConsistency(unittest.TestCase):
    """AC-1：三个视图是同一份 rig 的正交投影，高度必须一模一样。"""

    def setUp(self):
        self.parts = character.build()
        self.boxes = {v.name: bounds(self.parts, v) for v in (FRONT, SIDE, BACK)}

    def test_same_height(self):
        hs = [b[3] - b[1] for b in self.boxes.values()]
        self.assertLess(max(hs) - min(hs), 0.5 / 760.0, f"高度差 {max(hs) - min(hs)}")

    def test_same_ground_line(self):
        """三个视图的最低点必须在同一条线上（都在 y=0 附近）。"""
        for name, b in self.boxes.items():
            self.assertAlmostEqual(b[3], 0.0, delta=0.02, msg=f"{name} 最低点 {b[3]}")

    def test_front_back_same_width(self):
        f = self.boxes["front"]
        b = self.boxes["back"]
        self.assertAlmostEqual(f[2] - f[0], b[2] - b[0], places=6)

    def test_side_narrower_than_front(self):
        f = self.boxes["front"]
        s = self.boxes["side"]
        self.assertLess(s[2] - s[0], f[2] - f[0])


class TestPalette(unittest.TestCase):
    """AC-3：只用登记过的颜色。"""

    def test_only_declared_colors(self):
        allowed = set(character.PALETTE) | {"#FFFFFF"}
        used = set()
        for part in character.build():
            for sh in part.shapes:
                if getattr(sh, "color", None):
                    used.add(sh.color)
        self.assertTrue(used.issubset(allowed), f"未登记的颜色: {used - allowed}")

    def test_palette_size(self):
        self.assertLessEqual(len(character.PALETTE), 6)


class TestEarVariants(unittest.TestCase):
    """耳朵是唯一的记忆点：三种变体必须真的不一样，否则盲排没有意义。"""

    def test_variants_differ(self):
        """耳朵变体改的是宽度与角度，不是总高（最高点一直独角尖）。"""
        sigs = []
        for prm in ({}, {"ear_scale": 0.86, "ear_pitch": -6.0}, {"ear_scale": 1.10, "ear_pitch": 8.0}):
            b = bounds(character.build(prm), FRONT)
            sigs.append((round(b[2] - b[0], 4), round(b[3] - b[1], 4)))
        self.assertEqual(len(set(sigs)), 3, f"三版轮廓太像: {sigs}")
        widths = [s[0] for s in sigs]
        self.assertGreater(max(widths) - min(widths), 0.05, "三版宽度差太小，盲排看不出区别")


if __name__ == "__main__":
    unittest.main(verbosity=2)
