"""一条命令从零重建全部交付物。

顺序：字体子集（或核对）→ 三视图 PNG → A3 展示页 → 音轨 → 15 秒动效 → GIF → 介绍 PDF。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)


def run(name, fn):
    t = time.time()
    print(f"[build] {name} ...", flush=True)
    fn()
    print(f"[build] {name} 完成 {time.time() - t:.1f}s", flush=True)


def main():
    from scripts import audio, fonts, intro, views

    run("字体子集", fonts.build)
    run("三视图 PNG", views.main)
    run("A3 展示页 / 音轨", lambda: None)
    import scripts.sheet as sheet

    run("A3 展示页", sheet.main)
    run("音轨", audio.main)
    import scripts.animate as animate

    run("15 秒动效", animate.main)
    run("GIF", lambda: subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", "out/diting-motion-15s.mp4",
         "-vf", "fps=20,scale=720:720:flags=lanczos", "-loop", "0",
         "out/diting-motion-15s.gif"], check=True))
    run("介绍 PDF", intro.main)
    print("[build] 全部完成")


if __name__ == "__main__":
    main()
