# 青听 · 谛听 IP 形象

2026 九子岩 AIGC 文旅短视频创意大赛（第一轮 · 谛听 IP 形象）参赛作品。

**一只把耳朵长成七道泉的小谛听。** 名字叫青听——青是青阳，听是谛听，连读就是「倾听」。

| 交付物 | 文件 |
| --- | --- |
| 三视图展示页（A3 3508×2480 @300dpi） | `out/diting-turnaround-A3.png` |
| 正 / 侧 / 背 三个透明视图（1500×1500） | `out/diting-front.png` · `diting-side.png` · `diting-back.png` |
| 15 秒白底动效（1080×1080 · 30fps · 带音轨） | `out/diting-motion-15s.mp4` |
| 同上一版 GIF（720×720） | `out/diting-motion-15s.gif` |
| 形象介绍（800–1500 字，A4） | `out/diting-intro.pdf` |

## 一句话说清它怎么来的

角色不是画三遍画出来的，是**一组可以计算的三维体块**（头、身、四肢、耳、角、尾）：
正视、侧视、背视是同一份 rig 的**正交投影**，15 秒动效是同一份 rig 的逐帧投影。
所以三个角度是同一只兽，不是三只长得很像的兽。改一次参数，三视图与动效同时变。

## 从零重建

```bash
python scripts/build.py      # 字体子集 → 三视图 → A3 页 → 音轨 → 15s 动效 → GIF → PDF
bash scripts/verify.sh       # 全部断言 + 产物检查（全新 clone 里也能跑）
```

依赖：Python 3.13（标准库 + Pillow + fontTools）、本机 chromium（截图）、ffmpeg（编码）。
字体子集已随仓库携带（`assets/fonts/`），没有系统思源字体也能重建。

## 目录

```
rig/          角色 rig：geom（几何/投影）· character（造型参数）· render（SVG）· copy（全部文案）
scripts/      build · verify · sheet · views · animate · audio · intro · blind · fonts
docs/         00-SPEC · 01-RULERS · 02-DESIGN · 03-VERIFY · 04-PROOF · 05-SUBMISSION · 06-GATE-D · 07-UI
proof/        闸 D 的盲排材料与答案表、UI 量测报告
tests/        视图一致性、调色板、文案长度、视频参数、交付物尺寸
```

## 四道闸

| 闸 | 状态 | 证据 |
| --- | --- | --- |
| A 共识 | ✅ | `docs/00-SPEC.md`（官方评分表 + 黄金路径 + AC-1~AC-10）、`docs/07-UI.md`（风格、6 件尺子、记忆点、版式） |
| B 流程 | ✅ | 先写断言再实现：`tests/` 28 条；`scripts/verify.sh` 一条命令复验 |
| C 能用 | ✅ | 本机全绿 + 全新 clone 全绿（见 `docs/04-PROOF.md`） |
| D 第一眼 | 见 `docs/06-GATE-D.md` | 三位不同家族评委盲排（同题三版 + 5 个成名 IP 混排） |

## 授权

本仓库为参赛作品存档。角色形象（青听）版权归作者；引用的外部参考图仅用于内部盲排，
放在 `_ref/` 且不入库。
