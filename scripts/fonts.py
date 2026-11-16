"""按用到的字，把两套思源字体切成子集（woff2），随仓库走。"""

from __future__ import annotations

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fontTools import subset  # noqa: E402

from rig import copy  # noqa: E402

SRC = {
    "serif": r"C:\Windows\Fonts\NotoSerifSC-VF.ttf",
    "sans": r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
}
OUT = {
    "serif": "assets/fonts/NotoSerifSC-sub.woff2",
    "sans": "assets/fonts/NotoSansSC-sub.woff2",
}


def build():
    text = copy.all_strings()
    os.makedirs("assets/fonts", exist_ok=True)
    for key, src in SRC.items():
        if not os.path.exists(src):
            if os.path.exists(OUT[key]):
                print(f"[skip] 本机没有 {src}，沿用仓库里的子集 {OUT[key]}")
                continue
            raise SystemExit(f"既没有源字体 {src}，也没有子集 {OUT[key]}")
        args = [
            src,
            f"--text={text}",
            "--flavor=woff2",
            "--layout-features=*",
            "--no-hinting",
            "--desubroutinize",
            f"--output-file={OUT[key]}",
        ]
        subset.main(args)
        size = os.path.getsize(OUT[key])
        print(f"{OUT[key]}  {size/1024:.1f} KB  ({len(text)} chars in)")
    return {k: os.path.abspath(v) for k, v in OUT.items()}


def data_uri(path):
    with open(path, "rb") as f:
        return "data:font/woff2;base64," + base64.b64encode(f.read()).decode("ascii")


if __name__ == "__main__":
    paths = build()
    for k, v in paths.items():
        print(k, len(data_uri(v)) // 1024, "KB base64")
