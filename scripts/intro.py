"""把 copy.INTRO 排成一份 A4 PDF（浏览器打印，随包带字体）。"""

from __future__ import annotations

import base64
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rig import copy
from scripts import fonts
from scripts.shot import CHROME


def _inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def md_to_html(md):
    html, para, in_list = [], [], False

    def flush_para():
        if para:
            html.append("<p>" + _inline("".join(para)) + "</p>")
            para.clear()

    def close_list():
        nonlocal in_list
        if in_list:
            html.append("</ul>")
            in_list = False

    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            close_list()
            continue
        if line.startswith("## "):
            flush_para()
            close_list()
            html.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_para()
            close_list()
            html.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("- "):
            flush_para()
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{_inline(line[2:])}</li>")
        else:
            if in_list:
                close_list()
            para.append(line)
    flush_para()
    close_list()
    return "\n".join(html)


def build_html():
    serif = fonts.data_uri(fonts.OUT["serif"])
    sans = fonts.data_uri(fonts.OUT["sans"])
    img = ""
    if os.path.exists("out/diting-front.png"):
        with open("out/diting-front.png", "rb") as f:
            img = (
                '<div class="hero"><img src="data:image/png;base64,'
                + base64.b64encode(f.read()).decode("ascii")
                + '" alt="青听 正视"></div>'
            )
    body = md_to_html(copy.INTRO)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{copy.NAME} · 形象介绍</title>
<style>
@font-face {{ font-family: QTSerif; src: url({serif}) format('woff2'); }}
@font-face {{ font-family: QTSans; src: url({sans}) format('woff2'); }}
@page {{ size: A4; margin: 18mm 20mm 16mm 20mm; }}
@media screen {{ body {{ width: 170mm; margin: 0 auto; padding: 10mm 0; }} }}
html {{ -webkit-print-color-adjust: exact; }}
body {{ font-family: QTSerif, serif; color: #2B2A26; font-size: 10.2pt; line-height: 1.82; }}
.kicker {{ font-family: QTSans; font-size: 8.6pt; letter-spacing: .18em; color: #7A756B; text-transform: none; }}
h1 {{ font-size: 23pt; font-weight: 600; margin: 6pt 0 2pt; letter-spacing: .04em; }}
h2 {{ font-family: QTSans; font-size: 11pt; font-weight: 600; margin: 11pt 0 2pt; letter-spacing: .06em; }}
p {{ margin: 0 0 5pt; text-align: justify; }}
ul {{ margin: 2pt 0 8pt; padding-left: 16pt; }}
li {{ margin-bottom: 3pt; }}
strong {{ font-family: QTSans; font-weight: 600; }}
.hero {{ text-align: center; margin: 6pt 0 10pt; }}
.hero img {{ height: 46mm; }}
.rule {{ border-top: .6pt solid #C9C2B4; margin: 8pt 0 10pt; }}
.foot {{ font-family: QTSans; font-size: 8.2pt; color: #7A756B; margin-top: 14pt; border-top: .6pt solid #E2DBCE; padding-top: 6pt; }}
</style></head><body>
<div class="kicker">2026 九子岩 AIGC 文旅短视频创意大赛 · 第一轮 · 谛听 IP 形象</div>
{img}
{body}
<div class="foot">{copy.FOOTER_LEFT}　|　{copy.FOOTER_RIGHT}</div>
</body></html>"""


def main(out="out/diting-intro.pdf"):
    html = build_html()
    os.makedirs("out", exist_ok=True)
    tmp = os.path.abspath("out/_intro.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    profile = tempfile.mkdtemp(prefix="diting-pdf-")
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
        f"--user-data-dir={profile}", "--no-pdf-header-footer",
        f"--print-to-pdf={os.path.abspath(out)}",
        "file:///" + tmp.replace("\\", "/"),
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=180)
    if not os.path.exists(out):
        sys.stderr.write(res.stderr.decode("utf-8", "ignore")[-1500:])
        raise SystemExit("PDF 生成失败")
    print("wrote", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
