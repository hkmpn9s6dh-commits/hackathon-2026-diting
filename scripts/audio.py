"""15 秒音轨：风、一声铜铃、一下闷响、再一声远铃。全部用标准库合成。"""

from __future__ import annotations

import array
import math
import os
import random
import struct
import wave

SR = 44100
DUR = 15.0
N = int(SR * DUR)


def env(t, start, attack, decay, curve=3.0):
    if t < start:
        return 0.0
    dt = t - start
    if dt < attack:
        return dt / attack
    return math.exp(-max(0.0, dt - attack) / decay * curve)


def bell(t, start, freq, amp, decay):
    e = env(t, start, 0.004, decay)
    if e <= 0:
        return 0.0
    # 非谐分音，越小越"铜"
    return amp * e * (
        1.00 * math.sin(2 * math.pi * freq * t)
        + 0.45 * math.sin(2 * math.pi * freq * 2.41 * (t - start) + 1.1) * math.exp(-(t - start) / (decay * 0.55))
        + 0.22 * math.sin(2 * math.pi * freq * 3.83 * (t - start) + 2.3) * math.exp(-(t - start) / (decay * 0.35))
    )


def main(out="out/_audio.wav"):
    rnd = random.Random(20261130)
    samples = []
    lp = 0.0
    lp2 = 0.0
    for i in range(N):
        t = i / SR
        # 风：两级低通的白噪，慢速起伏
        x = rnd.uniform(-1, 1)
        lp += 0.02 * (x - lp)
        lp2 += 0.06 * (lp - lp2)
        wind = lp2 * (0.55 + 0.45 * math.sin(2 * math.pi * t / 7.5)) * 0.050

        v = wind
        # 耳朵转过来：一点细碎的"沙"
        if 3.3 < t < 4.4:
            v += lp * 0.05 * math.exp(-((t - 3.55) ** 2) / 0.02)
        # 睁眼：一声近铃
        v += bell(t, 4.62, 784.0, 0.36, 0.55)
        # 落地：一记闷响
        v += 0.30 * env(t, 6.34, 0.002, 0.10) * math.sin(2 * math.pi * 92 * (t - 6.34))
        v += 0.10 * lp * env(t, 6.34, 0.001, 0.04)
        # 收势：一声远铃
        v += bell(t, 11.24, 587.0, 0.16, 0.85)

        # 总线软限幅
        v = math.tanh(v * 1.4) * 0.92
        samples.append(v)

    peak = max(abs(s) for s in samples) or 1.0
    gain = 0.69 / peak
    pcm = array.array("h")
    for s in samples:
        pcm.append(int(max(-1.0, min(1.0, s * gain)) * 32767))
    stereo = array.array("h")
    for s in pcm:
        stereo.append(s)
        stereo.append(s)

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())
    print("wrote", out, len(stereo) // 2, "frames")


if __name__ == "__main__":
    main()
