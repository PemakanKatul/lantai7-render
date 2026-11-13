"""Final edit of "Revisi Terakhir": shots (960x540 @12fps) -> 1920x1080 @24fps with 2D camera moves, horror FX,
title + end card, the mixed audio, and an .srt.
python3 rt_edit.py [renders_dir=out_rt] [out=final_rt.mp4] [from=0] [to=9999] [preview=1]
"""
import json, os, sys, subprocess, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ARGS = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
RD = ARGS.get("renders", "out_rt")
OUT = ARGS.get("out", "final_rt.mp4")
W, H, FPS = 1920, 1080, 24
PREVIEW = ARGS.get("preview") == "1"
if PREVIEW:
    W, H = 960, 540
plan = json.load(open("plan_rt.json"))
shots = plan["shots"]
T_FROM, T_TO = float(ARGS.get("from", 0)), float(ARGS.get("to", 1e9))
rng = np.random.default_rng(3)
FONT = lambda f, s: ImageFont.truetype(os.path.join("fonts", f), s)


def smooth(p):
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def move_params(move, p, t, sid):
    """-> zoom, dx, dy (fractions of the frame), rot (deg)"""
    e = smooth(p)
    z, dx, dy, rot = 1.0, 0.0, 0.0, 0.0
    if move == "push_slow":
        z = 1.0 + 0.07 * e
    elif move == "push":
        z = 1.0 + 0.15 * e
    elif move == "pull":
        z = 1.14 - 0.14 * e
    elif move == "pan_r":
        z, dx = 1.12, -0.045 + 0.09 * e
    elif move == "pan_l":
        z, dx = 1.12, 0.045 - 0.09 * e
    elif move == "pan_d":
        z, dy = 1.14, -0.05 + 0.10 * e
    elif move == "shake":
        z = 1.07; dx = 0.006 * math.sin(t * 37 + sid); dy = 0.006 * math.cos(t * 29 + sid)
    elif move == "static":
        z = 1.0
    # tiny hand-held drift on everything, so no frame is dead still
    dx += 0.0025 * math.sin(t * 0.7 + sid * 1.3)
    dy += 0.0020 * math.sin(t * 0.53 + sid * 0.7)
    rot += 0.12 * math.sin(t * 0.4 + sid)
    return max(z, 1.012), dx, dy, rot


def transform(src, z, dx, dy, rot):
    h, w = src.shape[:2]
    s = W / w * z
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += W / 2 - w / 2 + dx * W
    M[1, 2] += H / 2 - h / 2 + dy * H
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


_grain = [((rng.standard_normal((H // 2, W // 2)) * 9).astype(np.float32)) for _ in range(8)]
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIG = np.clip(1.0 - 0.32 * _r ** 2.2, 0.35, 1.0)[..., None]
VIG_STRONG = np.clip(1.0 - 0.75 * _r ** 1.8, 0.05, 1.0)[..., None]


def grain(img, k, amt=1.0):
    g = cv2.resize(_grain[k % 8], (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + g * amt


def sepia(img, amt=1.0):
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    sep = np.stack([lum * 1.07, lum * 0.92, lum * 0.72], -1)
    return img * (1 - amt) + sep * amt


def redline_layer(p, seed):
    """a hand-drawn red pen stroke crossing the frame, drawn left->right"""
    lay = np.zeros((H, W, 4), np.float32)
    r = np.random.default_rng(seed)
    x0, x1 = int(W * 0.04), int(W * 0.04 + W * 0.92 * smooth(p))
    y0 = H * 0.52
    pts = [(x, int(y0 + (x - W / 2) * -0.03 + 3 * math.sin(x * 0.01))) for x in range(x0, max(x0 + 2, x1), 6)]
    if len(pts) > 1:
        img = np.zeros((H, W), np.uint8)
        cv2.polylines(img, [np.array(pts, np.int32)], False, 255, thickness=max(2, int(H * 0.022)), lineType=cv2.LINE_AA)
        img = cv2.GaussianBlur(img, (0, 0), 1.2).astype(np.float32) / 255
        lay[..., 0] = 0.55 * 255; lay[..., 1] = 0.02 * 255; lay[..., 2] = 0.02 * 255; lay[..., 3] = img * 0.95
    return lay


def text_layer(lines, alpha):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (txt, font, size, col, y, strike) in lines:
        f = FONT(font, int(size * H / 1080))
        bb = d.textbbox((0, 0), txt, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x = (W - tw) / 2
        d.text((x, y * H - th / 2), txt, font=f, fill=col + (int(255 * alpha),))
        if strike is not None and strike > 0:
            sx1 = x + tw * min(1.0, strike)
            d.line([(x - 10 * W / 1920, y * H + th * 0.05), (sx1, y * H - th * 0.08)], fill=(150, 4, 4, int(255 * alpha)), width=int(9 * H / 1080))
    return np.asarray(im).astype(np.float32)


def over(img, lay):
    a = lay[..., 3:4] / 255.0
    return img * (1 - a) + lay[..., :3] * a


def read_shot(sid):
    p = os.path.join(RD, f"shot_{sid:03d}.mp4")
    if not os.path.exists(p):
        return None
    cmd = ["ffmpeg", "-v", "error", "-i", p, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 540, 960, 3)
    return fr


def fx_at(shot, t):
    """active effects for time t inside the shot"""
    out = {}
    for f in shot["fx"]:
        kind, a, b = f[0], float(f[1]), float(f[2])
        if kind in ("old", "black", "desat", "dream", "vignette"):
            if a <= t < b:
                out[kind] = 1.0
        else:                         # [kind, start, duration]
            if a <= t < a + b:
                out[kind] = (t - a) / b
            if kind == "redline" and t >= a:
                out[kind] = min(1.0, (t - a) / b)
    return out


def main():
    os.makedirs("edit_tmp", exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium" if not PREVIEW else "veryfast", "-crf", "18" if not PREVIEW else "26",
                            "-pix_fmt", "yuv420p", "edit_tmp/video.mp4"], stdin=subprocess.PIPE)
    total_end = plan["duration"]
    missing = []
    k = 0
    for s in shots:
        t0, t1 = s["t0"], s["t1"]
        if t1 <= T_FROM or t0 >= T_TO:
            continue
        frames = read_shot(s["id"])
        if frames is None:
            missing.append(s["id"])
        n_out = int(round(t1 * FPS)) - int(round(t0 * FPS))
        dur = t1 - t0
        for j in range(n_out):
            t = j / FPS
            if frames is None:
                src = np.full((540, 960, 3), 20, np.uint8)
                cv2.putText(src, f"SHOT {s['id']} BELUM ADA", (250, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)
            else:
                src = frames[min(int(t * 12), len(frames) - 1)]
            z, dx, dy, rot = move_params(s["move"], t / dur, t, s["id"])
            fxs = fx_at(s, t)
            if "flicker" in fxs:
                dx += rng.uniform(-0.01, 0.01); dy += rng.uniform(-0.01, 0.01)
            img = transform(src, z, dx, dy, rot).astype(np.float32)
            # ---------------------------------------------------------- effects
            if "old" in fxs:
                img = sepia(img, 0.85)
                img = cv2.GaussianBlur(img, (0, 0), 1.1)
                img *= 0.92 + 0.08 * rng.random()
                img = grain(img, k, 2.2)
                if rng.random() < 0.08:                         # dust / scratches
                    x = rng.integers(0, W); img[:, x:x + 2] = img[:, x:x + 2] * 0.5 + 90
            if "desat" in fxs:
                img = sepia(img, 0.25)
                lum = img.mean(-1, keepdims=True); img = img * 0.35 + lum * 0.65
            if "dream" in fxs:
                blur = cv2.GaussianBlur(img, (0, 0), 9)
                img = img * 0.62 + blur * 0.55
                img = img * np.array([1.08, 0.98, 0.85], np.float32)
                img = img * (0.75 + 0.25 * VIG)
            if "red" in fxs:
                p = fxs["red"]; a = math.sin(math.pi * p) * 0.75
                lum = img.mean(-1, keepdims=True)
                img = img * (1 - a) + np.concatenate([lum * 1.35, lum * 0.15, lum * 0.12], -1) * a
            if "flicker" in fxs:
                img *= 0.55 + 0.75 * rng.random()
            if "vignette" in fxs:
                img *= VIG_STRONG
            if "redline" in fxs:
                img = over(img, redline_layer(fxs["redline"], s["id"]))
            if "dark" in fxs:
                img *= 1 - 0.85 * math.sin(math.pi * fxs["dark"])
            if "black" in fxs:
                img *= 0.0
            # ---------------------------------------------------------- global look: cool shadows, grain, vignette
            img = img * VIG
            lum = img.mean(-1, keepdims=True) / 255
            img = img + (1 - lum) * np.array([-4, 0, 6], np.float32) * (1 - lum)
            img = grain(img, k, 0.6)
            # ---------------------------------------------------------- titles
            tg = t0 + t
            if s.get("title") and t < dur:
                a = smooth((t - 0.4) / 0.8) * (1 - smooth((t - (dur - 0.9)) / 0.8))
                if a > 0:
                    strike = smooth((t - 1.6) / 0.5)
                    lay = text_layer([("REVISI", "SpecialElite.ttf", 120, (225, 220, 205), 0.42, None),
                                      ("TERAKHIR", "SpecialElite.ttf", 120, (225, 220, 205), 0.56, strike)], a)
                    img = img * (1 - 0.45 * a) ; img = over(img, lay)
            if s.get("end"):
                fade_t = total_end - 3.6
                if tg > fade_t:
                    a = smooth((tg - fade_t) / 0.8)
                    img *= 1 - a
                    b = smooth((tg - fade_t - 0.9) / 0.7) * (1 - smooth((tg - (total_end - 0.6)) / 0.5))
                    if b > 0:
                        img = over(img, text_layer([("KELAS MALAM", "SpecialElite.ttf", 54, (200, 196, 185), 0.5, None)], b))
            enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
            k += 1
        print(f"shot {s['id']} done ({k} frames)", flush=True)
    enc.stdin.close(); enc.wait()
    a0, a1 = max(T_FROM, 0), min(T_TO, total_end)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "edit_tmp/video.mp4", "-ss", str(a0), "-t", str(a1 - a0), "-i", "rt_audio/mix.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", OUT], check=True)
    print("WROTE", OUT, "missing:", missing)


def srt():
    words = json.load(open("rt_audio/words.json"))
    out, cur = [], []
    for w in words:
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        if (w["w"][-1] in ".?!" and len(cur) >= 3) or len(txt) > 52 or (w["w"].endswith("...") and len(cur) >= 3):
            out.append(cur); cur = []
    if cur:
        out.append(cur)

    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    lines = []
    for i, g in enumerate(out):
        a, b = g[0]["start"], min(g[-1]["end"] + 0.35, out[i + 1][0]["start"] - 0.05 if i + 1 < len(out) else g[-1]["end"] + 1)
        lines.append(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{' '.join(x['w'] for x in g)}\n")
    open("Revisi_Terakhir.srt", "w").write("\n".join(lines))
    print("srt", len(lines))


if __name__ == "__main__":
    if ARGS.get("srt") == "1":
        srt()
    else:
        main()
