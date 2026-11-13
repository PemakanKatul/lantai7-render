"""Music + sound effects for "Revisi Terakhir", all synthesised here (no samples), mixed under the VO.
Reads plan_rt.json (sfx/music cues per shot, relative to the shot start) and rt_audio/vo_all.mp3.
Writes rt_audio/mix.wav (stereo 48 kHz, about -14 LUFS) and rt_audio/stems/{music,sfx,vo}.wav
"""
import json, os, subprocess
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
rng = np.random.default_rng(13)
os.makedirs("rt_audio/stems", exist_ok=True)


# ------------------------------------------------------------------ building blocks
def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d, kind="white"):
    n = rng.standard_normal(int(d * SR))
    if kind == "pink":
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        n = signal.lfilter(b, a, n) * 4
    elif kind == "brown":
        n = np.cumsum(n); n = signal.lfilter([1, -1], [1, -0.995], n) * 0.05
    return n


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.3):
    e = np.ones(n) * s
    A, D, Rr = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n); e[:A] = np.linspace(0, 1, A)
    D = min(D, n - A); e[A:A + D] = np.linspace(1, s, D)
    Rr = min(Rr, n); e[n - Rr:] *= np.linspace(1, 0, Rr)
    return e


def fade(x, fi=0.05, fo=0.3):
    n = len(x); a, b = min(int(fi * SR), n), min(int(fo * SR), n)
    x = x.copy(); x[:a] *= np.linspace(0, 1, a); x[n - b:] *= np.linspace(1, 0, b)
    return x


_IR = {}


def reverb(x, size=2.0, wet=0.35, bright=4000):
    key = (size, bright)
    if key not in _IR:
        n = int(size * SR)
        ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * (6.9 / size))
        ir = lp(ir, bright); ir /= np.sqrt(np.sum(ir ** 2))
        _IR[key] = ir
    y = signal.fftconvolve(x, _IR[key])[:len(x) + int(size * SR)]
    out = np.zeros(len(y)); out[:len(x)] = x * (1 - wet)
    return out + y * wet


def tone(f, d, kind="sine", detune=0.0):
    t = t_(d)
    ph = 2 * np.pi * f * t * (1 + detune)
    if kind == "sine":
        return np.sin(ph)
    if kind == "saw":
        return 2 * ((f * (1 + detune) * t) % 1) - 1
    if kind == "tri":
        return 2 * np.abs(2 * ((f * t) % 1) - 1) - 1


def bell(f, d=3.0, bright=1.0):
    """music-box tine: inharmonic partials, fast decay"""
    t = t_(d)
    y = np.zeros(len(t))
    for k, (m, a, dec) in enumerate(((1, 1.0, 2.2), (2.76, 0.4 * bright, 4), (5.4, 0.2 * bright, 7), (8.9, 0.08 * bright, 10))):
        y += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * dec)
    return y * 0.4


def piano(f, d=4.0):
    t = t_(d)
    y = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.2 + 0.8 * k)) for k, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.1)))
    return y * env_adsr(len(t), 0.005, 0.1, 1.0, 0.8) * 0.35


def note(n):        # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)


def add(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


# ------------------------------------------------------------------ music cues (mono, return array)
def m_drone(d=40.0, base=55.0, dark=1.0):
    t = t_(d)
    y = np.zeros(len(t))
    for k, (m, a) in enumerate(((1, 1.0), (1.498, 0.35), (2.01, 0.25), (2.997, 0.12), (0.5, 0.5))):
        lfo = 1 + 0.004 * np.sin(2 * np.pi * (0.05 + 0.03 * k) * t + k)
        y += a * np.sin(2 * np.pi * base * m * np.cumsum(lfo) / SR)
    y += lp(noise(d, "brown"), 220) * 2.0 * dark
    y += bp(noise(d), 900, 1400) * 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
    return fade(norm(y, 0.5), 6.0, 6.0)


def m_sting(d=5.0, soft=False):
    t = t_(d)
    y = np.zeros(len(t))
    root = 110 if not soft else 220
    for m in (1, 1.059, 1.414, 1.5, 2.12, 2.83, 3.0):          # dissonant cluster
        y += tone(root * m, d, "saw", rng.uniform(-0.004, 0.004)) * 0.3
    y = lp(y, 2200 if not soft else 1400) * np.exp(-t * (0.9 if not soft else 1.4))
    if not soft:
        boom = np.sin(2 * np.pi * 42 * t * np.exp(-t * 0.6)) * np.exp(-t * 2.2) * 1.4
        y += boom
        hit = hp(noise(d), 3000) * np.exp(-t * 9) * 0.6
        y += hit
    att = env_adsr(len(t), 0.004 if not soft else 0.35, 0.3, 0.8, 2.5)
    y = reverb(y * att, 3.0, 0.45)
    pre = int(0.0 * SR)
    return norm(y, 0.95 if not soft else 0.55)


def m_reverse_swell(d=2.0):
    t = t_(d)
    y = hp(noise(d), 2000) * (t / d) ** 3 + sum(tone(220 * m, d, "saw") for m in (1, 1.06, 1.5)) * 0.1 * (t / d) ** 2
    return norm(lp(y, 6000), 0.6)


def m_tension(d=12.0):
    t = t_(d)
    y = np.zeros(len(t))
    for m, a in ((1, 1), (1.059, 0.8), (1.122, 0.6), (2.0, 0.4)):
        f = 196 * m * (1 + 0.06 * t / d)                       # slowly bending up
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
        y += a * np.sin(2 * np.pi * np.cumsum(f * vib) / SR)
    y += bp(noise(d), 3000, 6000) * 0.05
    y *= (t / d) ** 1.4
    return fade(norm(reverb(y, 2.5, 0.4), 0.5), 0.5, 1.0)


def m_musicbox(d=16.0, detune=0.012):
    """slightly broken lullaby in A minor; every note a little flat"""
    mel = [69, 72, 76, 74, 72, 71, 69, None, 67, 69, 71, 72, 71, 69, 68, 69]
    y = np.zeros(int(d * SR))
    step = 0.62
    for i, n in enumerate(mel):
        if n is None:
            continue
        st = int(i * step * SR)
        if st >= len(y):
            break
        b = bell(note(n) * (1 - detune * rng.uniform(0.3, 1.0)), 3.0)
        y[st:st + len(b)] += b[:len(y) - st]
        if i % 4 == 0:
            b2 = bell(note(n - 24) * (1 - detune), 3.0, 0.5) * 0.6
            y[st:st + len(b2)] += b2[:len(y) - st]
    wob = 1 + 0.03 * np.sin(2 * np.pi * 0.3 * t_(d))
    return fade(norm(reverb(y * wob, 2.8, 0.5), 0.45), 0.2, 3.0)


def m_sad(d=18.0):
    chords = [(57, 60, 64), (53, 57, 60), (55, 59, 62), (52, 56, 59)]
    y = np.zeros(int(d * SR))
    for i, ch in enumerate(chords * 2):
        st = int(i * 2.4 * SR)
        if st >= len(y):
            break
        for k, n in enumerate(ch):
            p = piano(note(n) * (1 - 0.003 * k), 4.5)
            y[st + int(k * 0.05 * SR):st + int(k * 0.05 * SR) + len(p)] += p[:max(0, len(y) - st - int(k * 0.05 * SR))]
    return fade(norm(reverb(y, 3.2, 0.5), 0.45), 0.1, 3.0)


def m_memory(d=22.0):
    t = t_(d)
    pad = sum(np.sin(2 * np.pi * note(n) * t * (1 + 0.002 * k)) for k, n in enumerate((57, 64, 69, 72))) * 0.18
    pad *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * t)
    pad = lp(pad, 1800)
    mb = m_musicbox(d, 0.02)
    y = np.pad(pad, (0, max(0, len(mb) - len(pad)))) + np.pad(mb, (0, max(0, len(pad) - len(mb)))) * 0.8
    tape = 1 + 0.006 * np.sin(2 * np.pi * 0.7 * t)                  # warbly old tape
    idx = np.clip(np.cumsum(tape) - 1, 0, len(y) - 1).astype(int)
    return fade(norm(y[idx], 0.45), 2.0, 3.0)


def m_whisper_bed(d=10.0):
    y = np.zeros(int(d * SR))
    for k in range(9):
        st = int(rng.uniform(0, d - 1.2) * SR)
        w = s_whisper(rng.uniform(0.5, 1.1))
        y[st:st + len(w)] += w * rng.uniform(0.3, 0.7)
    return fade(norm(reverb(y, 2.5, 0.6), 0.35), 1.0, 2.0)


def m_heartbeat(d=12.0, bpm=62):
    y = np.zeros(int(d * SR))
    beat = 60 / bpm
    for i in range(int(d / beat)):
        for off, a in ((0, 1.0), (0.28, 0.6)):
            st = int((i * beat + off) * SR)
            tt = t_(0.25)
            th = np.sin(2 * np.pi * 48 * tt * np.exp(-tt * 3)) * np.exp(-tt * 18) * a
            y[st:st + len(th)] += th[:len(y) - st]
    return fade(norm(lp(y, 180), 0.8), 0.5, 1.5)


def m_end(d=10.0):
    t = t_(d)
    sw = m_reverse_swell(1.2)
    boom = np.sin(2 * np.pi * 36 * t * np.exp(-t * 0.3)) * np.exp(-t * 0.7)
    ring = sum(tone(220 * m, d, "sine") for m in (1, 1.06, 1.5, 2.12)) * np.exp(-t * 0.4) * 0.15
    y = np.concatenate([sw, reverb(boom + ring + hp(noise(d), 2500) * np.exp(-t * 6) * 0.4, 4.0, 0.5)])
    return norm(y, 0.95)


MUSIC = {"drone_in": lambda: m_drone(30, 55), "drone_low": lambda: m_drone(22, 41.2, 1.4), "sting": m_sting,
         "sting_soft": lambda: m_sting(4.5, soft=True), "tension": m_tension, "musicbox": m_musicbox, "sad": m_sad,
         "memory": m_memory, "whisper_bed": m_whisper_bed, "heartbeat": m_heartbeat, "end": m_end}
MUSIC_GAIN = {"drone_in": 0.4, "drone_low": 0.4, "sting": 0.8, "sting_soft": 0.55, "tension": 0.4, "musicbox": 0.4, "sad": 0.4,
              "memory": 0.45, "whisper_bed": 0.4, "heartbeat": 0.55, "end": 0.9}
PRE = {"sting": 0.0, "end": 1.2}     # seconds of pre-roll (reverse swell) before the hit time


# ------------------------------------------------------------------ sound effects (mono)
def s_crickets(d=30.0):
    y = np.zeros(int(d * SR))
    for c in range(6):
        f = rng.uniform(4200, 5600); rate = rng.uniform(2.5, 4.5); ph = rng.uniform(0, 1)
        t = t_(d)
        chirp = np.sin(2 * np.pi * f * t) * (np.sin(2 * np.pi * 38 * t) > 0.2) * ((np.sin(2 * np.pi * rate * t + ph * 6) > 0.6))
        y += lp(chirp.astype(float), 7000) * rng.uniform(0.1, 0.3)
    return fade(y, 2.0, 2.0) * 0.6


def s_wind(d=30.0):
    t = t_(d)
    y = bp(noise(d, "pink"), 150, 900) * (0.4 + 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t + 1)))
    return fade(norm(y, 0.5), 3.0, 3.0)


def s_murmur(d=8.0, voices=8, room=1.2):
    y = np.zeros(int(d * SR))
    t = t_(d)
    for v in range(voices):
        f0 = rng.uniform(140, 260)
        syl = (np.sin(2 * np.pi * rng.uniform(3, 5.5) * t + rng.uniform(0, 6)) > rng.uniform(-0.2, 0.4)).astype(float)
        syl = lp(syl, 12)
        voice = bp(tone(f0, d, "saw") + noise(d) * 0.3, 300, 2500) * syl * rng.uniform(0.3, 1.0)
        y += voice
    return fade(norm(reverb(lp(y, 2600), room, 0.5), 0.5), 1.0, 1.0)


def s_hum(d=12.0):
    t = t_(d)
    y = sum(a * np.sin(2 * np.pi * 100 * k * t) for k, a in ((1, 1), (2, 0.4), (3, 0.3), (5, 0.12)))
    y *= 1 + 0.15 * (rng.standard_normal(len(t)) > 2.8)
    return fade(y * 0.08, 1.0, 1.0)


def s_scratch(d=0.35, bright=1.0):
    """pen nib dragging across paper"""
    t = t_(d)
    grain = (rng.random(len(t)) < 0.3).astype(float) * rng.standard_normal(len(t))
    y = bp(grain + noise(d) * 0.4, 1800, 7500 * bright) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(18, 30) * t))
    return fade(y * env_adsr(len(t), 0.01, 0.05, 0.9, 0.06), 0.005, 0.05) * 0.8


def s_pen_strike():
    return reverb(np.concatenate([s_scratch(0.45, 1.1), np.zeros(int(0.05 * SR))]), 0.4, 0.15)


def s_pen_strikes(n=6):
    y = np.zeros(int((n * 0.42 + 0.6) * SR))
    for k in range(n):
        s = s_scratch(rng.uniform(0.25, 0.4)); st = int(k * 0.42 * SR)
        y[st:st + len(s)] += s
    return reverb(y, 0.4, 0.15)


def s_pen_write(d=2.4, pencil=False):
    y = np.zeros(int(d * SR)); tt = 0.0
    while tt < d - 0.2:
        s = s_scratch(rng.uniform(0.06, 0.2), 0.6 if pencil else 1.0) * rng.uniform(0.5, 1.0)
        st = int(tt * SR); y[st:st + len(s)] += s[:len(y) - st]
        tt += rng.uniform(0.08, 0.22)
    return reverb(y, 0.4, 0.15) * (0.7 if pencil else 1.0)


def s_paper(d=0.8, crisp=1.0):
    t = t_(d)
    y = hp(noise(d), 1500) * lp(np.abs(rng.standard_normal(len(t))) > 2.2, 60) * 3
    return fade(reverb(y * crisp, 0.5, 0.2), 0.01, 0.2)


def s_page():
    t = t_(0.6)
    y = bp(noise(0.6), 800, 6000) * np.exp(-((t - 0.25) / 0.12) ** 2) * 1.2
    return reverb(y, 0.5, 0.2)


def s_tear():
    t = t_(0.9)
    y = hp(noise(0.9), 1200) * ((rng.random(len(t)) < 0.2) * 1.0) * (0.5 + t)
    return fade(lp(y, 9000), 0.01, 0.1)


def s_thud(f=70, d=0.4, a=1.0):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t * np.exp(-t * 4)) * np.exp(-t * 14) + lp(noise(d), 400) * np.exp(-t * 30) * 0.5) * a


def s_click(f=2500, d=0.05):
    t = t_(d)
    return bp(noise(d), f * 0.6, min(f * 1.6, 20000)) * np.exp(-t * 120)


def s_step(hard=True):
    y = add(s_thud(110 if hard else 80, 0.25, 0.6), s_click(1800, 0.06) * (0.5 if hard else 0.2))
    return y


def s_steps(d=5.0, rate=1.9, hard=True, room=1.4):
    y = np.zeros(int(d * SR))
    for k in range(int(d * rate)):
        s = s_step(hard) * rng.uniform(0.6, 1.0); st = int((k / rate + rng.uniform(-0.02, 0.02)) * SR)
        if st >= 0:
            y[st:st + len(s)] += s[:len(y) - st]
    return reverb(y, room, 0.35)


def s_creak(d=1.4):
    t = t_(d)
    f = 180 + 120 * np.sin(2 * np.pi * 0.6 * t) + 40 * rng.standard_normal(len(t)).cumsum() / SR * 30
    y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (0.4 + 0.6 * (rng.random(len(t)) < 0.5))
    return fade(bp(y, 400, 3000) * 0.4, 0.05, 0.3)


def s_door_open():
    return reverb(np.concatenate([s_click(1200, 0.08), s_creak(1.2)]), 1.0, 0.3)


def s_door_close():
    return reverb(add(s_thud(65, 0.5, 1.2), s_click(1500, 0.05)), 1.2, 0.35)


def s_lock():
    a = s_click(3200, 0.04); b = s_click(2200, 0.06)
    return reverb(np.concatenate([a, np.zeros(int(0.12 * SR)), b]) * 1.4, 0.6, 0.25)


def s_clock(d=12.0):
    y = np.zeros(int(d * SR))
    for k in range(int(d)):
        c = s_click(3800 if k % 2 else 2900, 0.04) * 0.6
        st = int(k * SR); y[st:st + len(c)] += c
    return reverb(y, 1.0, 0.3)


def s_birds(d=10.0):
    y = np.zeros(int(d * SR))
    for k in range(int(d * 1.2)):
        dd = rng.uniform(0.08, 0.2); t = t_(dd)
        f0 = rng.uniform(2500, 4500)
        ch = np.sin(2 * np.pi * np.cumsum(f0 + 1500 * np.sin(np.pi * t / dd)) / SR) * np.sin(np.pi * t / dd)
        st = int(rng.uniform(0, d - 0.3) * SR); y[st:st + len(ch)] += ch * rng.uniform(0.1, 0.35)
    return fade(reverb(y, 1.5, 0.4), 1.0, 1.0) * 0.5


def s_room(d=20.0, warm=True):
    y = lp(noise(d, "brown"), 300) * 0.6 + bp(noise(d), 200, 1200) * 0.02
    return fade(norm(y, 0.12), 2.0, 2.0)


def s_typing(d=3.0, soft=False):
    y = np.zeros(int(d * SR)); tt = 0.0
    while tt < d - 0.1:
        c = s_click(2000 if not soft else 1400, 0.03) * rng.uniform(0.4, 1.0) * (0.5 if soft else 1)
        st = int(tt * SR); y[st:st + len(c)] += c
        tt += rng.uniform(0.07, 0.2) if not soft else rng.uniform(0.15, 0.3)
    return reverb(y, 0.5, 0.2)


def s_vibe(d=3.0):
    t = t_(d)
    y = np.sin(2 * np.pi * 160 * t) * (((t % 1.0) < 0.4) & ((t % 0.2) < 0.17)) + bp(noise(d), 200, 500) * 0.2 * ((t % 1.0) < 0.4)
    return y * 0.5


def s_ding(up=True):
    a, b = (880, 1320) if up else (1320, 990)
    t = t_(0.5)
    y = np.concatenate([np.sin(2 * np.pi * a * t[:SR // 8]) * np.exp(-t[:SR // 8] * 20),
                        np.sin(2 * np.pi * b * t) * np.exp(-t * 9)])
    return y * 0.35


def s_whoosh(d=0.5):
    t = t_(d)
    return bp(noise(d), 500, 4000) * np.sin(np.pi * t / d) ** 2 * 0.5


def s_whisper(d=1.0):
    t = t_(d)
    y = np.zeros(len(t))
    nz = noise(d)
    for f in (rng.uniform(500, 800), rng.uniform(1200, 1800), rng.uniform(2400, 3000)):
        y += bp(nz, f * 0.85, f * 1.15)
    syl = lp((np.sin(2 * np.pi * rng.uniform(4, 7) * t) > 0).astype(float), 20)
    return fade(y * syl * np.sin(np.pi * t / d), 0.05, 0.1) * 0.6


def s_breath(d=3.0):
    t = t_(d)
    y = bp(noise(d), 300, 2500) * (np.sin(2 * np.pi * 0.45 * t) ** 2)
    return fade(y * 0.35, 0.3, 0.5)


def s_canteen(d=20.0):
    y = s_murmur(d, 12, 1.0)
    for k in range(int(d * 0.8)):
        c = s_click(rng.uniform(3000, 5000), 0.15) * rng.uniform(0.2, 0.6)   # spoon/glass clinks
        st = int(rng.uniform(0, d - 0.2) * SR); y[st:st + len(c)] += c
    return y


def s_cup():
    t = t_(0.8)
    return reverb(add(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 12) for f in (2100, 3300, 5100)) * 0.2, s_thud(180, 0.2, 0.4)), 0.5, 0.2)


def s_broom(d=8.0):
    y = np.zeros(int(d * SR))
    for k in range(int(d / 0.9)):
        t = t_(0.5)
        s = bp(noise(0.5), 900, 6000) * np.sin(np.pi * t / 0.5) ** 2 * 0.5
        st = int(k * 0.9 * SR); y[st:st + len(s)] += s[:len(y) - st]
    return reverb(y, 1.4, 0.35)


def s_applause(d=3.0, n=30):
    y = np.zeros(int(d * SR))
    for k in range(int(n * d)):
        c = bp(noise(0.03), 900, 5000) * np.exp(-t_(0.03) * 120)
        st = int(rng.uniform(0, d - 0.05) * SR); y[st:st + len(c)] += c * rng.uniform(0.3, 1.0)
    return fade(reverb(y, 1.0, 0.3), 0.1, 0.8) * 0.6


def s_zipper():
    t = t_(0.7)
    y = bp(noise(0.7), 1500, 7000) * (np.sin(2 * np.pi * (60 + 80 * t) * t) > 0.3)
    return fade(y * 0.6, 0.02, 0.05)


def s_rummage(d=4.0):
    y = s_paper(d, 0.8)[:int(d * SR)] * 0.8
    for k in range(6):
        th = s_thud(rng.uniform(150, 300), 0.15, 0.4); st = int(rng.uniform(0, d - 0.2) * SR); y[st:st + len(th)] += th
    return y


def s_scream_muffled(d=1.6):
    t = t_(d)
    f = 520 + 90 * np.sin(2 * np.pi * 6 * t)
    y = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) + bp(noise(d), 600, 2000) * 0.5
    y = lp(y, 700) * np.sin(np.pi * t / d) ** 0.5
    return reverb(y * 0.5, 0.8, 0.5)


def s_sob(d=3.0):
    t = t_(d)
    y = bp(noise(d), 400, 1800) * ((np.sin(2 * np.pi * 1.6 * t) > 0.5) * np.sin(2 * np.pi * 0.35 * t) ** 2)
    return fade(lp(y, 2200) * 0.35, 0.2, 0.5)


def s_laugh(d=2.5):
    y = np.zeros(int(d * SR))
    for v in range(4):
        t = t_(d)
        f0 = rng.uniform(180, 320)
        ha = (np.sin(2 * np.pi * rng.uniform(5, 6.5) * t) > 0.1) * np.exp(-t * rng.uniform(0.4, 0.8))
        y += bp(tone(f0, d, "saw") + noise(d) * 0.8, 300, 3000) * lp(ha.astype(float), 25)
    return fade(reverb(y, 1.0, 0.35) * 0.3, 0.05, 0.6)


def s_village(d=20.0):
    return add(s_crickets(d) * 0.6, s_birds(d) * 0.4, s_wind(d) * 0.5)


SFX = {"crickets": (lambda: s_crickets(30), 0.35), "wind": (lambda: s_wind(30), 0.4), "chatter_far": (lambda: s_murmur(8, 8, 2.5) * 0.6, 0.25),
       "hum": (s_hum, 0.35), "pen_strike": (s_pen_strike, 0.7), "pen_strikes": (s_pen_strikes, 0.6), "pen_write": (s_pen_write, 0.6),
       "pencil_write": (lambda: s_pen_write(2.4, True), 0.6), "paper": (s_paper, 0.5), "page": (s_page, 0.55),
       "paper_slide": (lambda: s_paper(0.6, 0.6), 0.5), "paper_tear": (s_tear, 0.6), "paper_drop": (lambda: s_paper(0.4, 1.0), 0.5),
       "steps": (lambda: s_steps(4.0), 0.5), "steps_stairs": (lambda: s_steps(7.0, 1.5, True, 2.2), 0.5), "door_open": (s_door_open, 0.55),
       "door_close": (s_door_close, 0.6), "lock": (s_lock, 0.7), "clock": (s_clock, 0.35), "birds_far": (s_birds, 0.35),
       "night_room": (lambda: s_room(20), 0.5), "day_room": (lambda: add(s_room(15), s_birds(15) * 0.5), 0.45), "room_tone": (lambda: s_room(15), 0.5),
       "typing": (s_typing, 0.4), "typing_phone": (lambda: s_typing(2.5, True), 0.45), "phone_vibe": (s_vibe, 0.5),
       "msg_send": (lambda: np.concatenate([s_whoosh(0.3), s_ding(False)]), 0.45), "msg_recv": (s_ding, 0.45),
       "whisper": (lambda: m_whisper_bed(6), 0.45), "breath": (s_breath, 0.5), "canteen": (s_canteen, 0.35), "cup": (s_cup, 0.5),
       "broom": (s_broom, 0.4), "crowd": (lambda: s_murmur(15, 14, 2.0), 0.35), "applause_small": (s_applause, 0.45),
       "zipper": (s_zipper, 0.45), "rummage": (s_rummage, 0.45), "scream_muffled": (s_scream_muffled, 0.55), "sob": (s_sob, 0.45),
       "laugh": (s_laugh, 0.4), "evening_village": (s_village, 0.4), "heartbeat": (m_heartbeat, 0.5)}


# ------------------------------------------------------------------ timeline
def place(buf, x, t, gain=1.0, pan=0.0):
    st = int(t * SR)
    if st < 0:
        x = x[-st:]; st = 0
    n = min(len(x), buf.shape[0] - st)
    if n <= 0:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[st:st + n, 0] += x[:n] * gain * l * 1.41
    buf[st:st + n, 1] += x[:n] * gain * r * 1.41


def stereo_wide(x, ms=0.012):
    d = int(ms * SR)
    return np.stack([x, np.concatenate([np.zeros(d), x[:-d]])], 1)


if __name__ == "__main__":
    plan = json.load(open("plan_rt.json"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "rt_audio/vo_all.mp3", "-ac", "1", "-ar", str(SR), "rt_audio/vo48.wav"], check=True)
    vo, _ = sf.read("rt_audio/vo48.wav")
    T = plan["duration"] + 2.0
    N = int(T * SR)
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    music = np.zeros((N, 2)); sfx = np.zeros((N, 2))
    cache = {}
    events_m, events_s = [], []
    for s in plan["shots"]:
        for t, nm in s["music"]:
            events_m.append((s["t0"] + t, nm))
        for t, nm in s["sfx"]:
            events_s.append((s["t0"] + t, nm))
    cut_times = [t for t, nm in events_m if nm == "cut"]
    for t, nm in sorted(events_m):
        if nm in ("cut", "silence"):
            continue
        x = MUSIC[nm]()
        g = MUSIC_GAIN[nm]
        if nm in ("sting", "end"):
            pre = m_reverse_swell(1.0) * 0.7
            place(music, pre, t - 1.0, g * 0.8)
        # a bed stops softly where the next bed of the same kind starts
        place(music, x, t, g, rng.uniform(-0.15, 0.15))
        print("music", round(t, 2), nm)
    for t, nm in sorted(events_s):
        if nm not in SFX:
            print("!! missing sfx", nm); continue
        fn, g = SFX[nm]
        x = fn()
        place(sfx, x, t, g, rng.uniform(-0.3, 0.3))
    # continuous low bed under the whole film so it never goes fully silent
    bed = m_drone(T, 49.0, 0.8) * 0.18
    music[:, 0] += bed[:N]; music[:, 1] += np.roll(bed[:N], 400)
    # "cut": the memory is erased -> everything drops out for 1.6 s
    for ct in cut_times:
        a, b = int(ct * SR), int((ct + 1.6) * SR)
        ramp = np.ones(N); ramp[a:b] = 0.0
        ramp[a - int(0.05 * SR):a] = np.linspace(1, 0, int(0.05 * SR)); ramp[b:b + int(0.8 * SR)] = np.linspace(0, 1, int(0.8 * SR))
        music *= ramp[:, None]; sfx *= ramp[:, None]
    # duck music/sfx under the voice
    venv = np.sqrt(np.maximum(signal.sosfilt(signal.butter(2, 6, "lowpass", fs=SR, output="sos"), vo ** 2), 0))
    duck = 1.0 - 0.6 * np.clip(venv / (np.percentile(venv, 90) + 1e-9), 0, 1)
    duck = signal.sosfilt(signal.butter(1, 3, "lowpass", fs=SR, output="sos"), duck)
    music *= duck[:, None]; sfx *= (0.5 + 0.5 * duck)[:, None]
    vo_st = np.stack([vo, vo], 1)
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lv = meter.integrated_loudness(vo_st)
    vo_st = pyln.normalize.loudness(vo_st, lv, -16.0)
    lm = meter.integrated_loudness(music + 1e-7); music = pyln.normalize.loudness(music, lm, -28.5)
    ls = meter.integrated_loudness(sfx + 1e-7); sfx = pyln.normalize.loudness(sfx, ls, -26.0)
    mix = vo_st + music + sfx
    for _ in range(3):            # loudness to -14 LUFS with a soft limiter keeping peaks under -0.5 dBFS
        mix = pyln.normalize.loudness(mix, meter.integrated_loudness(mix), -14.0)
        mix = 0.94 * np.tanh(mix / 0.94)
    sf.write("rt_audio/mix.wav", mix.astype(np.float32), SR)
    for nm, x in (("music", music), ("sfx", sfx), ("vo", vo_st)):
        sf.write(f"rt_audio/stems/{nm}.wav", x.astype(np.float32), SR)
    print("mix", round(meter.integrated_loudness(mix), 2), "LUFS, peak", round(float(np.max(np.abs(mix))), 3))
