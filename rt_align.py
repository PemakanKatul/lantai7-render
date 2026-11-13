"""Word timings for the 'Revisi Terakhir' VO without speech recognition.
The VO is 29 takes joined with exactly 1 s of silence, so segment starts are exact (DUR below).
Inside a segment: phrases (split at punctuation and [pause] tags) are matched to the silences of the
take by DP, then words inside a phrase are spread over its voiced time by character count.
Writes rt_audio/words.json [{seg, i, w, start, end}] and rt_audio/vo_cuts.json [{seg, start, end}].
"""
import json, re
import numpy as np, soundfile as sf

DUR = [20.271020, 19.226122, 27.402449, 21.629388, 21.890612, 23.170612, 24.346122, 22.204082, 21.786122, 19.879184,
       18.207347, 23.954286, 22.674286, 22.674286, 19.957551, 16.352653, 22.125714, 19.957551, 25.155918, 20.506122,
       22.439184, 21.472653, 20.271020, 20.192653, 20.688980, 24.189388, 22.125714, 22.360816, 21.786122]
SCRIPT = "/home/claude/revisi_terakhir/naskah_vo.md"

x, sr = sf.read("rt_audio/vo16.wav")
HOP = 160                                  # 10 ms
e = np.sqrt(np.convolve(x ** 2, np.ones(400) / 400, "same"))[::HOP]
db = 20 * np.log10(e + 1e-9)


def segments():
    t = open(SCRIPT).read()
    parts = re.split(r"\n## (\d+)\n", t)
    return {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def phrases(txt):
    """-> list of (words, strength of the break AFTER this phrase)"""
    txt = txt.replace("[long pause]", " ⟦L⟧ ").replace("[pause]", " ⟦P⟧ ")
    txt = re.sub(r"\[[^\]]*\]", " ", txt).replace('"', " ").replace("“", " ").replace("”", " ")
    toks = txt.split()
    out, cur = [], []
    for tk in toks:
        if tk in ("⟦L⟧", "⟦P⟧"):
            if cur:
                out.append([cur, 5.0 if tk == "⟦L⟧" else 3.0]); cur = []
            elif out:
                out[-1][1] = max(out[-1][1], 5.0 if tk == "⟦L⟧" else 3.0)
            continue
        cur.append(tk)
        if tk.endswith("..."):
            out.append([cur, 1.6]); cur = []
        elif tk[-1] in ".?!:":
            out.append([cur, 1.5]); cur = []
        elif tk[-1] in ",;":
            out.append([cur, 0.35]); cur = []
    if cur:
        out.append([cur, 0.0])
    return out


def silences(a, b, thr):
    """silent runs inside [a, b) in frames -> list of (start_s, end_s)"""
    seg = db[a:b] < thr
    res, i = [], 0
    while i < len(seg):
        if seg[i]:
            j = i
            while j < len(seg) and seg[j]:
                j += 1
            if j - i >= 9:      # >= 90 ms
                res.append(((a + i) * 0.01, (a + j) * 0.01))
            i = j
        else:
            i += 1
    return res


def wchars(w):
    return len(re.sub(r"[^\wÀ-ɏ]", "", w)) + 1.5


words, cuts = [], []
SEG = segments()
t = 0.0
for k, d in enumerate(DUR):
    seg = k + 1
    a, b = int(t * 100), int((t + d) * 100)
    peak = np.percentile(db[a:b], 95)
    thr = peak - 32
    voiced = np.where(db[a:b] > thr)[0]
    v0, v1 = (a + voiced[0]) * 0.01, (a + voiced[-1]) * 0.01 + 0.01
    sil = [s for s in silences(a, b, thr) if s[0] > v0 + 0.05 and s[1] < v1 - 0.05]
    P = phrases(SEG[seg])
    n = len(P)
    W = np.array([sum(wchars(w) for w in p[0]) for p in P])
    # speech time with silences removed: expected position of each boundary
    speech = (v1 - v0) - sum(s[1] - s[0] for s in sil)

    def sp_before(time):
        return (time - v0) - sum(min(s[1], time) - s[0] for s in sil if s[0] < time)

    exp = np.cumsum(W)[:-1] / W.sum() * speech
    m = len(sil)
    INF = 1e9
    # dp[i][j]: first i boundaries placed, first j silences consumed
    dp = np.full((n, m + 1), INF); bk = {}
    dp[0][0] = 0
    for i in range(n):
        for j in range(m + 1):
            c = dp[i][j]
            if c >= INF:
                continue
            if j < m:   # skip silence j (it falls inside a phrase)
                L = sil[j][1] - sil[j][0]
                cc = c + 6.0 * max(0.0, L - 0.16)
                if cc < dp[i][j + 1]:
                    dp[i][j + 1] = cc; bk[(i, j + 1)] = ("skip", i, j)
            if i < n - 1:
                st = P[i][1]
                # leave boundary i without a silence
                cc = c + {0.0: 0.0, 0.35: 0.15}.get(st, st * 0.9)
                if cc < dp[i + 1][j]:
                    dp[i + 1][j] = cc; bk[(i + 1, j)] = ("none", i, j)
                if j < m:   # boundary i sits in silence j
                    L = sil[j][1] - sil[j][0]
                    dev = (sp_before(sil[j][0]) - exp[i]) / max(1.0, speech) * 10
                    want = {5.0: 0.9, 3.0: 0.55, 1.6: 0.35, 1.5: 0.3, 0.35: 0.12, 0.0: 0.1}[st]
                    cc = c + dev * dev + 2.0 * max(0.0, want - L) + (0.6 if st == 0.0 else 0.0)
                    if cc < dp[i + 1][j + 1]:
                        dp[i + 1][j + 1] = cc; bk[(i + 1, j + 1)] = ("match", i, j)
    # backtrack
    i, j = n - 1, m
    assign = {}
    while (i, j) != (0, 0):
        kind, pi, pj = bk[(i, j)]
        if kind == "match":
            assign[pi] = pj
        i, j = pi, pj
    # phrase spans
    bounds = []
    for bi in range(n - 1):
        if bi in assign:
            s = sil[assign[bi]]; bounds.append((s[0], s[1]))
        else:
            bounds.append(None)
    # fill unmatched boundaries by interpolation of speech time between matched neighbours
    starts = [v0]; ends = []
    for bi in range(n - 1):
        if bounds[bi] is not None:
            ends.append(bounds[bi][0]); starts.append(bounds[bi][1])
        else:
            # find next matched boundary (or segment end)
            nj = next((q for q in range(bi, n - 1) if bounds[q] is not None), None)
            t_end = bounds[nj][0] if nj is not None else v1
            last = nj if nj is not None else n - 1
            wsum = W[bi + 1:last + 1].sum() + W[bi]
            ts = starts[-1] + (t_end - starts[-1]) * W[bi] / wsum
            ends.append(ts); starts.append(ts)
    ends.append(v1)
    for pi, (p, _) in enumerate(P):
        p0, p1 = starts[pi], ends[pi]
        inner = [s for s in sil if s[0] > p0 and s[1] < p1]
        dur = (p1 - p0) - sum(s[1] - s[0] for s in inner)
        ws = np.array([wchars(w) for w in p])
        cum = np.concatenate([[0], np.cumsum(ws)]) / ws.sum() * dur

        def real(sp):    # speech time inside the phrase -> clock time (skipping inner silences)
            tt = p0
            for s in inner:
                if tt + sp <= s[0]:
                    break
                sp -= s[0] - tt; tt = s[1]
            return tt + sp
        for wi, w in enumerate(p):
            words.append(dict(seg=seg, i=0, w=w, start=round(real(cum[wi]), 3), end=round(real(cum[wi + 1]) - 0.01, 3)))
    cuts.append(dict(seg=seg, start=round(t, 3), end=round(t + d, 3), v0=round(v0, 3), v1=round(v1, 3)))
    t += d + 1.0

cnt = {}
for w in words:
    w["i"] = cnt.get(w["seg"], 0); cnt[w["seg"]] = w["i"] + 1
json.dump(words, open("rt_audio/words.json", "w"), ensure_ascii=False, indent=0)
json.dump(cuts, open("rt_audio/vo_cuts.json", "w"), indent=1)
print(len(words), "words; total", round(t - 1, 2))
