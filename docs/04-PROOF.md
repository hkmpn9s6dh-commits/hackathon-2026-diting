# 04 · 举证（闸 C）

日期：2026-11-16｜机器：家用笔记本 2 号（Windows 11）｜Python 3.13.14

## 1. 本机

```
$ bash scripts/verify.sh
== 1/6 单元测试 ==   Ran 27 tests ... OK
== 2/6 交付物 ==     A3 3508×2480 · 三张 1500×1500 · mp4/gif/pdf 齐全
== 3/6 视频 ==       width=1080 height=1080 30/1 nb_frames=450 duration=15.000000
== 4/6 调色板 ==     面积 ≥1% 的颜色 8 个（≤9）
== 5/6 字数 ==       汉字数 906（800–1500）
== 6/6 ==            全部通过
```

## 2. 全新 clone（只照 README）

```
$ git clone https://github.com/hkmpn9s6dh-commits/hackathon-2026-diting _clone-diting
$ cd _clone-diting && bash scripts/verify.sh
... 全部通过
```

这一遍**不重建**，验的是"仓库里的产物本身自洽"。

## 3. 全新 clone 从零重建（AC-9 确定性）

```
$ python scripts/build.py
[build] 字体子集 2.0s → 三视图 PNG 3.0s → 音轨 1.1s → 15 秒动效 135.0s
[build] A3 展示页 2.3s → GIF 1.5s → 介绍 PDF 1.7s
[build] 全部完成        real 2m27s
```

重建前后四张 PNG 的 sha256：

| 文件 | clone 里（提交版） | 重建后 | |
|---|---|---|---|
| `out/diting-turnaround-A3.png` | `1fb20b0929379a65…` | `1fb20b0929379a65…` | ✅ |
| `out/diting-front.png` | `456b460db4a14db1…` | `456b460db4a14db1…` | ✅ |
| `out/diting-side.png` | `693d19bd8c2e605b…` | `693d19bd8c2e605b…` | ✅ |
| `out/diting-back.png` | `5896e6eda40c08dc…` | `5896e6eda40c08dc…` | ✅ |

**结论：这台机器上，同一份代码两次构建逐字节一致。**（不是"看起来一样"，是 sha256 相同。）

## 4. 踩到的坑（写进构建脚本，不写进改单）

- **全新 clone 第一次 `build.py` 就死在 `sheet.py`**：展示页底部要贴 4 张动效关键帧，
  而 `out/_frames/` 是中间产物、不入库。原顺序把 sheet 排在 animate 前面。
  → 已把顺序改成 animate → sheet，并在 `sheet.py` 里加了明确的报错（缺帧时告诉你先跑哪个脚本）。
- 视频四角判据原来写「均值 ≥250」，但纸白 `#FBFAF7` 本身就是 249.3，H.264 再压掉 1 级 → 必然失败。
  → 改成「与纸白每通道差 ≤3」，这才是真正想验的东西（素色底，不是纯白）。

## 5. 未验

- 真机微信/邮件客户端里的预览效果（本轮走邮箱，不经过平台二次压缩）。
- 打印打样（A3 300dpi 的 CMYK 转换未做，主办方若要求 CMYK 需另导）。
