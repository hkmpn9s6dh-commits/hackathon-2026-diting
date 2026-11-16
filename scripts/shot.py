"""用本机 chromium 把 SVG/HTML 截成 PNG（无头、固定尺寸）。"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

CHROME = os.environ.get(
    "DITING_CHROME",
    r"C:\Users\张一\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe",
)


def shot(src_path, out_png, width, height, transparent=False, scale=1):
    src = os.path.abspath(src_path)
    out = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    profile = tempfile.mkdtemp(prefix="diting-chrome-")
    args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        f"--user-data-dir={profile}",
        f"--window-size={width},{height}",
        f"--force-device-scale-factor={scale}",
        f"--screenshot={out}",
    ]
    if transparent:
        args.append("--default-background-color=00000000")
    args.append("file:///" + src.replace("\\", "/"))
    res = subprocess.run(args, capture_output=True, timeout=180)
    if not os.path.exists(out):
        sys.stderr.write(res.stderr.decode("utf-8", "ignore")[-2000:])
        raise RuntimeError("chrome screenshot failed")
    return out


if __name__ == "__main__":
    shot(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
