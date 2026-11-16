import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig.geom import (  # noqa: E402
    BACK, FRONT, SIDE, Ellipsoid, Part, cholesky2, euler, mat_mul, mat_vec,
    rot_y, sort_parts,
)


class TestCholesky(unittest.TestCase):
    def test_reconstructs_sigma(self):
        a, b, c = 4.0, 1.2, 0.9
        l11, l21, l22 = cholesky2(a, b, c)[0][0], cholesky2(a, b, c)[1][0], cholesky2(a, b, c)[1][1]
        self.assertAlmostEqual(l11 * l11, a, places=9)
        self.assertAlmostEqual(l21 * l11, b, places=9)
        self.assertAlmostEqual(l21 * l21 + l22 * l22, c, places=9)

    def test_degenerate_is_positive(self):
        l11, l21, l22 = cholesky2(0.0, 0.0, 0.0)[0][0], cholesky2(0.0, 0.0, 0.0)[1][0], cholesky2(0.0, 0.0, 0.0)[1][1]
        self.assertTrue(l11 > 0)
        self.assertTrue(l22 > 0)


class TestProjection(unittest.TestCase):
    def test_sphere_is_circle_in_every_view(self):
        s = Ellipsoid(center=(0, 0, 0), radii=(0.25, 0.25, 0.25), color="#000")
        for view in (FRONT, SIDE, BACK):
            w, h = s.width_height(view)
            self.assertAlmostEqual(w, 0.5, places=6)
            self.assertAlmostEqual(h, 0.5, places=6)

    def test_flat_ellipsoid_axes(self):
        e = Ellipsoid(center=(0, 0, 0), radii=(0.2, 0.1, 0.3), color="#000")
        self.assertAlmostEqual(e.width_height(FRONT)[0], 0.4, places=6)
        self.assertAlmostEqual(e.width_height(FRONT)[1], 0.2, places=6)
        self.assertAlmostEqual(e.width_height(SIDE)[0], 0.6, places=6)
        self.assertAlmostEqual(e.width_height(SIDE)[1], 0.2, places=6)

    def test_rotation_of_sphere_is_invariant(self):
        base = Ellipsoid(center=(0, 0, 0), radii=(0.2, 0.2, 0.2), color="#000")
        rotated = Ellipsoid(
            center=(0, 0, 0), radii=(0.2, 0.2, 0.2), color="#000", rot=euler(37, 21, 11)
        )
        self.assertAlmostEqual(
            base.width_height(FRONT)[0], rotated.width_height(FRONT)[0], places=6
        )

    def test_yaw_90_swaps_front_and_side(self):
        e = Ellipsoid(center=(0, 0, 0), radii=(0.3, 0.1, 0.05), color="#000")
        e90 = Ellipsoid(
            center=(0, 0, 0), radii=(0.3, 0.1, 0.05), color="#000", rot=rot_y(90)
        )
        self.assertAlmostEqual(e90.width_height(FRONT)[0], 0.1, places=6)
        self.assertAlmostEqual(e90.width_height(SIDE)[0], 0.6, places=6)

    def test_symmetry_front_and_back(self):
        e = Ellipsoid(center=(0.1, 0.2, 0.3), radii=(0.12, 0.07, 0.2), color="#000")
        fw, fh = e.width_height(FRONT)
        bw, bh = e.width_height(BACK)
        self.assertAlmostEqual(fw, bw, places=6)
        self.assertAlmostEqual(fh, bh, places=6)

    def test_mat_mul_identity(self):
        i = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        m = euler(20, 30, 40)
        self.assertEqual(mat_mul(i, m), m)
        v = mat_vec(i, (1, 2, 3))
        self.assertEqual(v, (1, 2, 3))


class TestDepthOrder(unittest.TestCase):
    def test_far_first_in_front_view(self):
        near = Part("near", (0, 0, 0.5), [])
        far = Part("far", (0, 0, -0.5), [])
        order = [p.name for p in sort_parts([near, far], FRONT)]
        self.assertEqual(order, ["far", "near"])

    def test_far_first_in_back_view(self):
        near = Part("near", (0, 0, -0.5), [])
        far = Part("far", (0, 0, 0.5), [])
        order = [p.name for p in sort_parts([near, far], BACK)]
        self.assertEqual(order, ["far", "near"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
