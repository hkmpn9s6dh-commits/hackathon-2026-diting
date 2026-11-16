import json
import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import copy  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCopy(unittest.TestCase):
    """AC-8：介绍 800–1500 汉字；不写夸大话。"""

    def test_length(self):
        han = len(re.findall(r"[\u4e00-\u9fff]", copy.INTRO))
        self.assertGreaterEqual(han, 800, f"只有 {han} 字")
        self.assertLessEqual(han, 1500, f"有 {han} 字")

    def test_no_overclaim(self):
        banned = ["必将获奖", "一定能拿", "保证获奖", "第一名"]
        for w in banned:
            self.assertNotIn(w, copy.INTRO)

    def test_name_is_consistent(self):
        self.assertEqual(copy.NAME, "青听")
        self.assertIn("青听", copy.INTRO)
        self.assertIn("七", copy.MEMORY_TITLE + copy.MEMORY_BODY + copy.INTRO)

    def test_sheet_strings_cover_copy(self):
        joined = copy.sheet_strings()
        for s in (copy.NAME, copy.TAGLINE, copy.MEMORY_TITLE):
            self.assertIn(s, joined)


class TestVideo(unittest.TestCase):
    """AC-5 / AC-6 / AC-7：时长、画幅、白底、有音轨。"""

    path = os.path.join(ROOT, "out", "diting-motion-15s.mp4")

    def _probe(self):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", self.path],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_exists(self):
        self.assertTrue(os.path.exists(self.path), "先跑 scripts/animate.py")

    def test_duration_and_size(self):
        d = self._probe()
        self.assertAlmostEqual(float(d["format"]["duration"]), 15.0, delta=0.05)
        v = [s for s in d["streams"] if s["codec_type"] == "video"][0]
        self.assertEqual((v["width"], v["height"]), (1080, 1080))
        self.assertEqual(v["r_frame_rate"], "30/1")

    def test_has_audio(self):
        d = self._probe()
        a = [s for s in d["streams"] if s["codec_type"] == "audio"]
        self.assertTrue(a, "没有音轨")

    def test_paper_background(self):
        """抽第 0 帧，看四角是不是素色底。"""
        from PIL import Image

        png = os.path.join(ROOT, "out", "_bgcheck.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.2",
                        "-i", self.path, "-frames:v", "1", png], check=True)
        im = Image.open(png).convert("RGB")
        w, h = im.size
        paper = (251, 250, 247)          # #FBFAF7
        for box in ((0, 0, 40, 40), (w - 40, 0, w, 40), (0, h - 40, 40, h), (w - 40, h - 40, w, h)):
            mean = im.crop(box).resize((1, 1), Image.BOX).getpixel((0, 0))
            for c in range(3):
                self.assertLessEqual(
                    abs(mean[c] - paper[c]), 3,
                    f"角落 {box} 不是纸白 {paper}，实测 {mean}",
                )


class TestDeliverables(unittest.TestCase):
    """AC-2 / AC-9：展示页尺寸与三张透明图。"""

    def test_sheet_size(self):
        from PIL import Image

        p = os.path.join(ROOT, "out", "diting-turnaround-A3.png")
        self.assertTrue(os.path.exists(p), "先跑 scripts/sheet.py")
        im = Image.open(p)
        self.assertEqual(im.size, (3508, 2480))

    def test_three_views_transparent(self):
        from PIL import Image

        for name in ("front", "side", "back"):
            p = os.path.join(ROOT, "out", f"diting-{name}.png")
            self.assertTrue(os.path.exists(p), f"缺 {p}")
            im = Image.open(p).convert("RGBA")
            self.assertEqual(im.size, (1500, 1500))
            self.assertEqual(im.getpixel((3, 3))[3], 0, f"{name} 不是透明底")


if __name__ == "__main__":
    unittest.main(verbosity=2)
