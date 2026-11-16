#!/usr/bin/env bash
# 一条命令复验。全新 clone 里也能跑：不依赖本机任何未入库文件。
set -u
cd "$(dirname "$0")/.."
fail=0

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

say "1/6 单元测试（几何 / 视图 / 调色板 / 文案 / 视频 / 产物）"
python -m unittest discover -s tests -v 2>&1 | tail -25 || fail=1

say "2/6 交付物存在性与尺寸"
python - <<'PY' || fail=1
import os, sys
from PIL import Image
need = {
    "out/diting-turnaround-A3.png": (3508, 2480),
    "out/diting-front.png": (1500, 1500),
    "out/diting-side.png": (1500, 1500),
    "out/diting-back.png": (1500, 1500),
}
for p, size in need.items():
    if not os.path.exists(p):
        print("MISSING", p); sys.exit(1)
    im = Image.open(p)
    if im.size != size:
        print("SIZE", p, im.size, "!=", size); sys.exit(1)
    print("ok", p, im.size)
for p in ("out/diting-motion-15s.mp4", "out/diting-motion-15s.gif", "out/diting-intro.pdf"):
    if not os.path.exists(p):
        print("MISSING", p); sys.exit(1)
    print("ok", p, os.path.getsize(p) // 1024, "KB")
PY

say "3/6 视频参数（ffprobe）"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames \
  -show_entries format=duration -of default=nw=1 out/diting-motion-15s.mp4 || fail=1

say "4/6 调色板（展示页里面积 >=1% 的颜色）"
python - <<'PY' || fail=1
from PIL import Image
from collections import Counter
im = Image.open("out/diting-turnaround-A3.png").convert("RGB").resize((878, 620))
q = im.quantize(colors=12, method=Image.MEDIANCUT).convert("RGB")
c = Counter(q.getdata())
total = sum(c.values())
big = [(col, n / total) for col, n in c.items() if n / total >= 0.01]
print("面积 >=1% 的颜色数：", len(big))
for col, share in sorted(big, key=lambda x: -x[1]):
    print("  #%02X%02X%02X %.1f%%" % (col[0], col[1], col[2], share * 100))
raise SystemExit(0 if len(big) <= 9 else 1)
PY

say "5/6 介绍字数（800–1500 汉字）"
python - <<'PY' || fail=1
import re, sys
sys.path.insert(0, ".")
from rig import copy
han = len(re.findall(r"[\u4e00-\u9fff]", copy.INTRO))
print("汉字数：", han)
raise SystemExit(0 if 800 <= han <= 1500 else 1)
PY

say "6/6 结论"
if [ "$fail" -eq 0 ]; then
  echo "全部通过。"
else
  echo "有失败项，见上。"
fi
exit "$fail"
