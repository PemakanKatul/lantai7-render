"""Vertical 1080x1920 Shorts cut from Revisi_Terakhir.mp4.
python3 rt_shorts.py part1|teaser
Cuts are (segment, first word, last word). Paper/phone close-ups are shown whole over a blurred copy (text stays readable);
everything else is a centre crop. Subtitles are burned in; an end card closes the video.
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

KIND = sys.argv[1]
SRC = "Revisi_Terakhir.mp4"
W = json.load(open("rt_audio/words.json"))
PLAN = json.load(open("plan_rt.json"))
SEGW = {}
for w in W:
    SEGW.setdefault(w["seg"], []).append(w)
CUTS = {
    "part1": [(1, 2, 38), (2, 0, 999), (3, 0, 999), (4, 0, 999), (5, 0, 12), (6, 0, 7), (7, 0, 999), (9, 0, 999), (12, 0, 999)],
    "teaser": [(4, 15, 37), (9, 24, 41), (13, 15, 20), (13, 35, 40), (15, 27, 34), (19, 34, 45), (25, 14, 24), (28, 31, 42)],
}[KIND]
CARD = {"part1": ("BERSAMBUNG", "bagian 2 & versi lengkap", "ada di channel ini"),
        "teaser": ("REVISI TERAKHIR", "versi lengkap", "ada di channel ini")}[KIND]
LABEL = {"part1": "REVISI TERAKHIR · PART 1", "teaser": "REVISI TERAKHIR"}[KIND]
FIT_SETS = ("kertas", "hp", "tangan")
TMP = f"shorts_tmp/{KIND}"
os.makedirs(TMP, exist_ok=True)
OUT = {"part1": "Revisi_Terakhir_Shorts_Part1.mp4", "teaser": "Revisi_Terakhir_Shorts_Teaser.mp4"}[KIND]
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_T = "fonts/SpecialElite.ttf"


def cut_range(seg, a, b):
    ws = SEGW[seg]
    b = min(b, len(ws) - 1)
    t0 = ws[a]["start"] - (0.25 if a > 0 else 0.45)
    if a > 0:
        t0 = max(t0, ws[a - 1]["end"] + 0.03)
    t1 = ws[b]["end"] + (0.3 if b < len(ws) - 1 else 0.75)
    if b < len(ws) - 1:
        t1 = min(t1, ws[b + 1]["start"] - 0.04)
    return t0, t1, ws[a:b + 1]


def shot_at(t):
    for s in PLAN["shots"]:
        if s["t0"] <= t < s["t1"]:
            return s
    return PLAN["shots"][-1]


pieces, subs, tl = [], [], 0.0
for k, (seg, a, b) in enumerate(CUTS):
    t0, t1, ws = cut_range(seg, a, b)
    # split at shot boundaries so each part gets its own framing
    bounds = sorted({t0, t1} | {s["t0"] for s in PLAN["shots"] if t0 < s["t0"] < t1})
    for i in range(len(bounds) - 1):
        u0, u1 = bounds[i], bounds[i + 1]
        if u1 - u0 < 0.05:
            continue
        sh = shot_at((u0 + u1) / 2)
        fit = sh["set"]["name"] in FIT_SETS
        p = f"{TMP}/p{len(pieces):03d}.mp4"
        cam = sh["cam"]
        semi = (isinstance(cam, dict) and cam.get("kind") in ("close", "xclose")) or isinstance(cam, list)
        if semi and not fit:
            vf = ("[0:v]split[a][b];[a]crop=608:1080:(iw-608)/2:0,scale=1080:1920,boxblur=30:2,eq=brightness=-0.22[bg];"
                  "[b]crop=810:1080:(iw-810)/2:0,scale=1080:1440:flags=lanczos[fg];[bg][fg]overlay=0:(H-h)/2-80,setsar=1[v]")
        elif fit:
            vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:2,eq=brightness=-0.18[bg];"
                  "[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=0:(H-h)/2-80,setsar=1[v]")
        else:
            vf = "[0:v]crop=608:1080:(iw-608)/2:0,scale=1080:1920:flags=lanczos,setsar=1[v]"
        fi = 0.03 if i == 0 else 0.0
        fo = 0.04 if i == len(bounds) - 2 else 0.0
        af = f"afade=t=in:d={fi}," if fi else ""
        af += f"afade=t=out:st={max(0, u1 - u0 - fo)}:d={fo}," if fo else ""
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{u0:.3f}", "-t", f"{u1 - u0:.3f}", "-i", SRC, "-filter_complex", vf + ";[0:a]" +
                        af + "aformat=sample_rates=48000:channel_layouts=stereo[a]", "-map", "[v]", "-map", "[a]", "-r", "24",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", p.replace(".mp4", ".mkv")],
                       check=True)
        pieces.append(p.replace(".mp4", ".mkv"))
    for w in ws:
        subs.append((tl + w["start"] - t0, tl + w["end"] - t0, w["w"]))
    tl += t1 - t0
    print("cut", k, seg, a, b, round(t1 - t0, 2), "total", round(tl, 2), flush=True)

# ---------------------------------------------------------------- end card (black, title, line; heartbeat + drone)
D = 6.5
im = Image.new("RGB", (1080, 1920), (0, 0, 0)); d = ImageDraw.Draw(im)
for txt, f, y, c in ((CARD[0], ImageFont.truetype(FONT_T, 92), 820, (200, 20, 20)), (CARD[1], ImageFont.truetype(FONT_B, 48), 960, (220, 215, 205)),
                     (CARD[2], ImageFont.truetype(FONT_B, 48), 1030, (220, 215, 205)), ("KELAS MALAM", ImageFont.truetype(FONT_T, 54), 1250, (150, 146, 140))):
    x = (1080 - d.textlength(txt, font=f)) / 2
    d.text((x, y), txt, font=f, fill=c)
im.save(f"{TMP}/card.png")
sys.path.insert(0, "."); import rt_audio as A
SR = 48000
au = np.zeros(int(D * SR))
hb = A.m_heartbeat(D, 70) * 0.7; au[:len(hb)] += hb[:len(au)]
dr = A.m_drone(D + 2, 41.2, 1.2)[:len(au)] * 0.45; au[:len(dr)] += dr
st = A.m_sting(4.0, soft=True) * 0.6; au[:len(st)] += st[:len(au)]
au *= np.minimum(1, np.linspace(D, 0, len(au)) / 1.2)
sf.write(f"{TMP}/card.wav", np.stack([au, au], 1).astype(np.float32) * 0.5, SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{D}", "-i", f"{TMP}/card.png", "-i", f"{TMP}/card.wav",
                "-vf", "fade=t=in:d=0.6,fade=t=out:st=%.2f:d=0.6,setsar=1" % (D - 0.7), "-r", "24", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-t", f"{D}", f"{TMP}/card.mkv"], check=True)
pieces.append(f"{TMP}/card.mkv")

# ---------------------------------------------------------------- subtitles (3-4 words a line) + label
groups, cur = [], []
for s in subs:
    cur.append(s)
    if len(cur) >= 4 or s[2][-1] in ".?!," or s[2].endswith("..."):
        groups.append(cur); cur = []
if cur:
    groups.append(cur)


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,DejaVu Sans,74,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,70,70,520,1",
       "Style: Lab,DejaVu Sans,34,&H00C8D2DC,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,8,40,40,150,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for i, g in enumerate(groups):
    a = g[0][0]; b = min(g[-1][1] + 0.25, groups[i + 1][0][0] - 0.02) if i + 1 < len(groups) else g[-1][1] + 0.6
    txt = " ".join(x[2] for x in g)
    if any(x[2].lower().strip(".,!?") in ("merah", "dicoret", "jujur.", "jujur", "direvisi", "berubah", "tepat") for x in g):
        txt = txt.replace("merah", "{\\c&H2020E0&}merah{\\c&HFFFFFF&}")
    ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{txt}")
ass.append(f"Dialogue: 0,{ts(0)},{ts(tl)},Lab,,0,0,0,,{LABEL}")
open(f"{TMP}/subs.ass", "w").write("\n".join(ass) + "\n")

open(f"{TMP}/list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in pieces))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{TMP}/list.txt", "-vf", f"ass={TMP}/subs.ass",
                "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", OUT], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout)
print("WROTE", OUT, round(dur, 2), "s")
