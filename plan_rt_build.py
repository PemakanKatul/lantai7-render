"""Writes plan_rt.json: every shot of "Revisi Terakhir", timed to rt_audio/words.json.
Beat = (segment, first word index, spec). A shot runs from its beat to the next beat.
Times inside a spec: seconds from the shot start, "wN" = start of word N of the same segment, "eN" = end of word N.
talk=[[a, b], ...] makes the actor talk between a and b; with aud=True (default) the mouth follows the VO loudness.
"""
import json
import numpy as np, soundfile as sf

WORDS = json.load(open("rt_audio/words.json"))
CUTS = {c["seg"]: c for c in json.load(open("rt_audio/vo_cuts.json"))}
SEGW = {}
for w in WORDS:
    SEGW.setdefault(w["seg"], []).append(w)
END = CUTS[29]["end"] + 5.0
FPS = 12
_x, _sr = sf.read("rt_audio/vo16.wav")
_env = np.sqrt(np.convolve(_x ** 2, np.ones(320) / 320, "same"))[::160]     # 100 Hz loudness

# ------------------------------------------------------------------ sets
EXT_N = dict(name="kampus_ext", night=True, exposure=0.95)
EXT_D = dict(name="kampus_ext", night=False, exposure=0.45)
TG_C = dict(name="tangga_rt", gate="closed", light=0.5, exposure=2.0)
TG_O = dict(name="tangga_rt", gate="open", light=0.9, exposure=1.6)
RB_DUSK = dict(name="ruang_baca", light="dusk", exposure=1.3)
RB_NIGHT = dict(name="ruang_baca", light="night", exposure=1.8)
RB_DAWN = dict(name="ruang_baca", light="dawn", exposure=1.5)
RB_NIGHT_C = dict(name="ruang_baca", light="night", chair_out=True, exposure=1.8)
KL_M = dict(name="kamar_laras", tidy=False, light="night", exposure=1.4)
KL_T = dict(name="kamar_laras", tidy=True, light="night", exposure=1.4)
KL_TD = dict(name="kamar_laras", tidy=True, light="day", exposure=0.8)
KL_DAWN = dict(name="kamar_laras", tidy=True, light="dawn", exposure=1.2, lamp=True)
KN = dict(name="kantin", exposure=0.5)
RD = dict(name="ruang_dosen", exposure=0.7)
KK = dict(name="koridor_k", light="dusk", exposure=1.0)
SD = dict(name="sidang", exposure=0.8)
WS = dict(name="wisuda", exposure=0.45)
KP = dict(name="kampung", exposure=0.7)
MK = dict(name="meja_kosong", exposure=1.4)
TGN = dict(name="tangan", exposure=1.2)


def KT(lines, kind="a4", exposure=1.2, **k):
    d = dict(name="kertas", lines=lines, kind=kind, exposure=exposure); d.update(k)
    return d


def HP(mode="chat", bubbles=(), typing="", exposure=1.0):
    return dict(name="hp", mode=mode, bubbles=[list(b) for b in bubbles], typing=typing, exposure=exposure)


def A(who, at, rot=None, expr=None, pose="idle", keys=(), **k):
    d = dict(who=who, at=at if isinstance(at, str) else list(at), rot=rot, pose=pose, keys=[list(x) for x in keys])
    if expr:
        d["expr"] = expr
    d.update(k)
    return d


def on(who, kind="close", **k):
    d = dict(on=who, kind=kind); d.update(k)
    return d


def hide(obj, t_show, t_hide=None):
    """object hidden until t_show (then visible); optional hide again at t_hide"""
    keys = [(0.0, 1), (t_show, 0)] + ([(t_hide, 1)] if t_hide is not None else [])
    return dict(obj=obj, prop="hide", keys=keys)


B = []


def beat(seg, w, set_, cam, cast=(), move="push_slow", **k):
    d = dict(seg=seg, w=w, set=set_, cam=cam, cast=list(cast), move=move)
    d.update(k)
    B.append(d)


# ------------------------------------------------------------------ cast in three stages of Laras
L1 = dict(who="laras")                                                                     # maroon hoodie, hair down
L2 = dict(who="laras", over=dict(hair_style="bun", shirt=[0.52, 0.50, 0.48], bottom=[0.12, 0.12, 0.14]))   # greyer, hair up
L3 = dict(who="laras", **{"as": "laras2"})                                                  # white blouse, bun: like her


def LA(stage, at, rot=None, expr="capek", pose="idle", keys=(), **k):
    d = A("laras", at, rot, expr, pose, keys, **k)
    d.update({kk: vv for kk, vv in stage.items() if kk != "who"})
    return d


MBAK90 = dict(over=dict(hair_style="long", shirt=[0.70, 0.68, 0.60], bottom=[0.08, 0.08, 0.10], long_skirt=True, collar=[0.80, 0.78, 0.70]))


def M90(at, rot=None, expr="capek", pose="idle", keys=(), **k):
    d = A("mbak", at, rot, expr, pose, keys, **k)
    d["as"] = "laras2"; d.update(MBAK90)
    return d


GHOST = lambda at, rot=None, **k: A("tigabelas", at, rot, None, **k)
OLD = [["old", 0, 999]]
TITLE90 = ["#SKRIPSI", "", "TINJAUAN PENGARUH MEDIA CETAK", "TERHADAP PERSEPSI MAHASISWA", "", "", "Disusun oleh:", "~RETNO WULANDARI",
           "~NIM 91/0417/SP", "", "~FAKULTAS ILMU SOSIAL", "~1994"]
TITLE_L = ["#SKRIPSI", "", "ANALISIS PENGARUH LITERASI DIGITAL", "TERHADAP MINAT BACA MAHASISWA", "", "", "Disusun oleh:", "LARAS PRAMESTI",
           "NIM 1518301142", "", "PROGRAM STUDI SARJANA", "2026"]
BAB4 = ["#BAB IV  HASIL DAN PEMBAHASAN", "", "Hasil penelitian menunjukkan bahwa", "responden yang memiliki kebiasaan",
        "membaca cenderung lebih kritis", "dalam menilai sebuah informasi.", "Hal ini sejalan dengan temuan", "penelitian sebelumnya, yaitu",
        "bahwa literasi digital berperan", "penting terhadap minat baca."]

# ================================================================== 1. the building, the rule
beat(1, 0, EXT_N, "road", title=True, sfx=[(0, "crickets"), (0, "wind")], music=[(0, "drone_in")])
beat(1, 2, EXT_N, "wide", move="pan_r")
beat(1, 11, EXT_N, "facade", move="push", sfx=[(0, "chatter_far")])
beat(1, 18, EXT_N, "win3", move="push_slow", music=[("w22", "sting_soft")])
beat(1, 25, TG_C, "gate", move="push_slow", sfx=[(0, "hum")])
beat(1, 31, EXT_N, "steps", [A("kating", "kating", pose="sitlap", expr="senyum", look="maba1"),
                             A("maba1", "maba1", pose="sitlap", expr="cemas", look="kating"),
                             A("maba2", "maba2", pose="sitlap", expr="cemas", look="kating")], move="push_slow")
# ================================================================== 2. "Jangan pernah tinggalkan skripsimu..."
beat(2, 0, EXT_N, on("kating", "close", side=0.35), [A("kating", "kating", pose="sitlap", expr="netral", look="maba1", talk=[["w0", "e13"]]),
                                                    A("maba1", "maba1", pose="sitlap", expr="cemas")], move="push_slow",
     music=[(0, "whisper_bed")])
beat(2, 9, EXT_N, on("maba1", "close", side=-0.3), [A("maba1", "maba1", pose="sitlap", expr="takut", blink=False, look="kating"),
                                                   A("kating", "kating", pose="sitlap", expr="netral")], move="push")
beat(2, 14, RD, "wide", [A("dosen", "dosen", pose="sitdesk", expr="marah"), M90("laras_stand", pose="headdown", expr="cemas")],
     fx=OLD, music=[(0, "drone_low")], sfx=[(0, "clock")])
beat(2, 21, RD, on("mbak", "close", side=0.3), [A("dosen", "dosen", pose="sitdesk", expr="marah"), M90("laras_stand", pose="headdown", expr="nangis")],
     fx=OLD, move="push_slow")
beat(2, 28, KT(BAB4[:1] + ["~" + x for x in BAB4[1:]], "tua"), "page", fx=OLD, move="push",
     dyn=[hide(f"kt_s{i}", round(0.25 + 0.32 * k, 2)) for k, i in enumerate((2, 3, 4, 5, 6, 7, 8, 9))], sfx=[(0.2, "pen_strikes")])
# ================================================================== 3. the night of the 14th submission
beat(3, 0, TG_O, "up", [M90((0.62, -1.75, 0), 180, expr="capek", pose="papers", prop="papers", walk=[[0.3, 99]],
                              keys=[(0, "move", [0.62, -1.75, 0, 180]), (0.3, "move", [0.62, -1.75, 0, 180]),
                                    (7.0, "move", [0.62, 0.42, 1.0, 180])])],
     fx=OLD, move="static", sfx=[(0.3, "steps_stairs")], set_over=dict(light=0.4, exposure=2.2))
beat(3, 15, TG_C, "down", move="push_slow", fx=OLD, music=[(0, "sting_soft")], sfx=[(0, "hum")])
beat(3, 20, dict(RB_DAWN, chair_out=True), "long", move="push_slow", fx=OLD, sfx=[(0, "birds_far")])
beat(3, 26, dict(RB_DAWN, chair_out=True), "corner", move="push", fx=OLD)
beat(3, 32, KT(["~" + x for x in BAB4], "tua"), "page", fx=OLD, move="pan_d", sfx=[(0, "page")])
beat(3, 37, KT(TITLE90, "tua", title_page=True), "top", fx=OLD, move="push_slow",
     dyn=[hide("kt_s7", "w44")], sfx=[("w44", "pen_strike")])
beat(3, 46, RB_NIGHT, "gap", [GHOST("gap")], move="push_slow", music=[("w50", "sting")], sfx=[(0, "whisper")])
# ================================================================== 4. the rumour: leave your draft overnight
beat(4, 0, EXT_N, "steps", [A("kating", "kating", pose="sitlap", expr="senyum", look="maba1"),
                            A("maba1", "maba1", pose="sitlap", expr="cemas", look="kating"),
                            A("maba2", "maba2", pose="sitlap", expr="cemas", look="kating")], move="push_slow", music=[(0, "drone_low")])
beat(4, 7, EXT_N, on("kating", "xclose", side=0.25), [A("kating", "kating", pose="sitlap", expr="senyum", look="maba1", talk=[["w15", "e24"]])],
     move="push_slow")
beat(4, 25, RB_DUSK, "desk_top", move="push_slow", sfx=[(0, "clock")])
beat(4, 27, KT(BAB4[:6] + ["!Lebih tepat: cenderung kritis."], "a4"), "page", move="push",
     dyn=[hide("kt_l6", "w31")], sfx=[("w31", "pen_write")])
beat(4, 34, EXT_N, on("kating", "xclose", side=0.25), [A("kating", "kating", pose="sitlap", expr="senyum", look="maba1", talk=[["w34", "e37"]])],
     move="push", music=[("w36", "sting_soft")])
# ================================================================== 5. Laras
beat(5, 0, KL_M, "wide", [LA(L1, "chair", expr="capek", pose="sitwrite")], move="push_slow", sfx=[(0, "night_room"), (0, "typing")],
     music=[(0, "sad")])
beat(5, 5, KT(["#SURAT PERINGATAN", "", "Kepada: Laras Pramesti", "NIM 1518301142", "", "Batas masa studi: Semester 14",
               "Status: TERANCAM DIKELUARKAN"], "a4", light="cold"), "page", move="push")
beat(5, 13, RD, "over", [A("dosen", "dosen", pose="sitdesk", expr="netral"), LA(L1, "laras", expr="capek", pose="sitlap")],
     sfx=[(0, "paper_slide")])
beat(5, 21, KT(["~" + x for x in BAB4[:9] if x], "a4", light="day"), "page", move="push_slow",
     dyn=[hide(f"kt_s{i}", round(0.2 + 0.18 * k, 2)) for k, i in enumerate(range(8))], sfx=[(0.1, "pen_strikes")])
beat(5, 27, HP("call"), "top", move="push_slow", sfx=[(0, "phone_vibe")])
beat(5, 35, KL_M, on("laras", "close", side=0.3), [LA(L1, "mid", -20, expr="capek", pose="phone", prop="phone")], move="push_slow")
# ================================================================== 6. the stairs, Dimas
beat(6, 0, TG_O, "up", [LA(L1, (0.62, -1.75, 0), 180, expr="capek", pose="papers", prop="papers", walk=[[0.2, 99]],
                              keys=[(0, "move", [0.62, -1.75, 0, 180]), (0.2, "move", [0.62, -1.75, 0, 180]), (5.0, "move", [0.62, -0.2, 0.55, 180])])],
     move="static", sfx=[(0.2, "steps_stairs")])
beat(6, 8, TG_O, [[0.25, -3.0, 1.55], [0.7, -0.4, 1.3], 30], [LA(L1, "b", expr="capek", pose="papers", prop="papers", keys=[("w17", "move", [0.72, -0.39, 0.66, 180]),
                                                                                         ("w19", "move", [0.72, -0.39, 0.66, 0])]),
                          A("dimas", (0.65, -2.9, 0), 180, expr="cemas", walk=[[0, 1.6]],
                            keys=[(0, "move", [0.65, -2.9, 0, 180]), (1.6, "move", [0.65, -2.4, 0, 180])])],
     move="push_slow", sfx=[(0, "steps")])
beat(6, 21, TG_O, [[0.3, -0.85, 1.65], [0.65, -2.4, 1.15], 42], [LA(L1, (0.72, -0.39, 0.66), 0, expr="capek", pose="papers", prop="papers"),
                                                               A("dimas", (0.65, -2.4, 0), 180, expr="cemas", look="laras", talk=[["w21", "e33"]])])
beat(6, 34, TG_O, [[0.95, -2.25, 1.15], [0.72, -0.39, 1.55], 40], [LA(L1, (0.72, -0.39, 0.66), 0, expr="cemas", pose="papers", prop="papers",
                                                                   look="dimas"), A("dimas", (0.65, -2.4, 0), 180, expr="cemas")])
beat(6, 36, KT(TITLE_L, "a4", title_page=True, light="day"), "top", move="pull", sfx=[(0, "paper_tear"), (1.5, "zipper")])
beat(6, 44, RB_DUSK, "long", [LA(L1, "desk", expr="capek", pose="give", prop="papers", walk=[[0, 2.0]],
                                   keys=[(0, "move", [1.9, 7.5, 0, 180]), (2.0, "move", [1.75, 10.35, 0, 165]), (2.4, "pose", "papers")]),
                              GHOST("shelf")], move="static", sfx=[(0, "steps"), (2.4, "paper_drop")], music=[(0, "tension")])
# ================================================================== 7. the first correction
beat(7, 0, RB_DAWN, "desk_top", move="push_slow", sfx=[(0, "birds_far")])
beat(7, 9, KT(BAB4[:2] + ["~" + BAB4[2], "!Hasil penelitian menunjukkan,", "~" + BAB4[3], "!responden yang terbiasa membaca", BAB4[4], BAB4[5]], "a4"),
     "page", move="push", dyn=[hide("kt_s2", 0.3), hide("kt_l3", 0.6), hide("kt_s4", 1.0), hide("kt_l5", 1.3)], sfx=[(0.3, "pen_write")])
beat(7, 15, KT(["", "!Hasil penelitian menunjukkan,", "!responden yang terbiasa membaca", "!lebih kritis menilai informasi."], "a4"),
     "midline", move="push_slow", music=[(0, "musicbox")])
beat(7, 25, KT(["#Persamaan regresi", "", "~Y = a + bX", "!Y = a + b1X1 + b2X2 + e", "", "~yang mana dimana hal tersebut", "!yang"], "a4"),
     "page", move="pan_d")
beat(7, 33, RD, "desk", [A("dosen", "dosen", pose="sitdesk", expr="netral", keys=[("w41", "expr", "senyum")]),
                         LA(L1, "laras", expr="cemas", pose="sitlap")], sfx=[(0, "page")])
beat(7, 43, RD, on("dosen", "close", side=0.25), [A("dosen", "dosen", pose="sitdesk", expr="senyum", talk=[["w43", "e46"]])], move="push_slow")
# ================================================================== 8. "Bagus. Sedikit lagi. Kamu bisa."
beat(8, 0, TG_O, "up", [LA(L1, (0.62, -1.75, 0), 180, expr="netral", pose="papers", prop="papers", walk=[[0.0, 99]],
                              keys=[(0, "move", [0.62, -1.75, 0, 180]), (4.5, "move", [0.62, 0.0, 0.66, 180])])],
     move="static", sfx=[(0, "steps_stairs")])
beat(8, 8, RB_DAWN, "desk_top", move="push_slow")
beat(8, 13, KT(BAB4[2:8] + ["", "^Bagus.", "^Sedikit lagi.", "^Kamu bisa."], "a4"), "page", move="push_slow",
     dyn=[hide("kt_l7", "w21"), hide("kt_l8", "w22"), hide("kt_l9", "w24")], sfx=[("w21", "pen_write")], music=[(0, "musicbox")])
beat(8, 26, RB_DAWN, "front", [LA(L1, "chair", expr="nangis", pose="sitdesk")], move="push_slow", sfx=[(0, "sob")])
beat(8, 29, RB_DAWN, on("laras", "xclose", side=0.3, up=0.05), [LA(L1, "chair", expr="nangis", pose="sitdesk")], move="push_slow")
# ================================================================== 9. the thank-you page
UCAP = ["#UCAPAN TERIMA KASIH", "", "Puji syukur penulis panjatkan atas", "selesainya skripsi ini. Penulis", "mengucapkan terima kasih kepada:",
        "", "1. Dr. Suryo, selaku pembimbing.", "~2. Ibu, yang selalu sabar menunggu.", "3. Teman-teman seangkatan.", "",
        "!Tidak jujur.", "!Kamu membencinya, setiap kali ia bertanya."]
beat(9, 0, RB_DAWN, "corner", [LA(L1, "desk", expr="netral", pose="papers")], move="push_slow")
beat(9, 11, KT(UCAP, "a4"), "page", move="push_slow", dyn=[hide("kt_s7", "w26"), hide("kt_l10", "w34"), hide("kt_l11", "w36")],
     sfx=[("w26", "pen_strike"), ("w34", "pen_write")], music=[("w34", "sting_soft")])
beat(9, 27, KT(UCAP, "a4"), "botline", move="push", dyn=[hide("kt_l10", "w34"), hide("kt_l11", "w36")])
# ================================================================== 10. relief
beat(10, 0, RB_DUSK, "long", [LA(L1, "chair", expr="capek", pose="sitdesk")], move="push_slow", music=[(0, "drone_low")])
beat(10, 8, RB_DUSK, on("laras", "close", side=0.35, dist=0.85, lens=40), [LA(L1, "chair", expr="cemas", pose="sitdesk")], move="push_slow")
beat(10, 14, RB_DUSK, on("laras", "xclose", side=0.2), [LA(L1, "chair", expr="cemas", pose="sitdesk", keys=[("w19", "expr", "senyum")])],
     move="push_slow")
beat(10, 20, RB_DUSK, "behind", [LA(L1, "chair", expr="senyum", pose="sitdesk"), GHOST("corner_far")], move="push_slow",
     music=[(0, "tension")], sfx=[(0, "breath")])
beat(10, 32, RB_NIGHT, "door", [LA(L1, "desk", 0, expr="netral", walk=[[0.3, 4.0]],
                                   keys=[(0, "move", [1.75, 10.35, 0, 0]), (0.3, "move", [1.75, 10.35, 0, 20]), (4.0, "move", [-0.2, 2.0, 0, 10])])],
     move="static", sfx=[(0.3, "steps"), (3.8, "door_close")])
# ================================================================== 11. the red ink spreads
beat(11, 0, KL_M, "desk", [LA(L1, "chair", expr="capek", pose="sitwrite")], move="push_slow", sfx=[(0, "night_room")])
beat(11, 9, KT(["*Senin - metpen", "*- revisi bab 5 !!!", "*- fotokopi kuesioner", "*- telp ibu", "", "!Urutkan menurut prioritas."], "buku"),
     "page", move="push", dyn=[hide("kt_l5", 0.6)])
beat(11, 15, KT(["*indomie 2", "*telur 1/4", "*sabun", "*kopi sachet", "~", "!kopi hitam, tanpa gula"], "belanja"), "page", move="push",
     dyn=[hide("kt_l5", 0.5)])
beat(11, 18, KT(["FOTOKOPI SINAR JAYA", "Jl. Kaliurang", "------------------", "Fotokopi 120 x 200", "Jilid 1 x 5000", "TOTAL   29.000",
                 "", "!Belum tepat."], "struk"), "page", move="push", dyn=[hide("kt_l7", 0.4)])
beat(11, 22, KT(["", "!Belum tepat.", "!Urutkan menurut prioritas.", "!Kamu bisa."], "a4", light="cold"), "midline", move="push_slow",
     music=[(0, "tension")])
beat(11, 31, KL_M, "wide", [LA(L1, "mid", expr="takut", pose="scared", look="desk")], move="push", music=[("w39", "sting_soft")])
# ================================================================== 12. the phone
beat(12, 0, HP("chat", [("in", "Kapan wisuda, Ras?")]), "top", move="push_slow", sfx=[(0, "msg_recv")])
beat(12, 10, KL_M, on("laras", "close", side=0.3), [LA(L1, "mid", -20, expr="cemas", pose="phone", prop="phone")], move="push_slow",
     sfx=[("w14", "typing_phone")])
beat(12, 15, HP("chat", [("in", "Kapan wisuda, Ras?")], typing="iya Bu, sebentar lagi"), "close", move="push_slow")
beat(12, 19, HP("chat", [("in", "Kapan wisuda, Ras?"), ("out", "Jangan tanya-tanya lagi."), ("in", "maaf ya, Nak.")]), "close",
     dyn=[hide("hp_b1", "w27"), hide("hp_bt1", "w27"), hide("hp_bk1", "w27"), hide("hp_b2", "w33"), hide("hp_bt2", "w33"), hide("hp_bk2", "w33")],
     move="push_slow", sfx=[("w27", "msg_send"), ("w33", "msg_recv")], music=[("w27", "sting_soft")])
beat(12, 36, KL_M, on("laras", "xclose", side=0.25), [LA(L1, "mid", -20, expr="takut", pose="phone", prop="phone", blink=False)],
     move="push_slow", music=[(0, "sad")])
# ================================================================== 13. Dimas notices
KANTIN_EX = [A("teman1", "ex1", pose="sitdesk", expr="senyum", gest=False), A("teman2", "ex2", pose="sitdesk", expr="senyum", gest=False),
             A("maba1", "ex3", pose="sitdesk", expr="netral", gest=False), A("kating", "ex4", pose="sitdesk", expr="senyum", gest=False)]
beat(13, 0, KN, "wide", [LA(L2, "laras", expr="netral", pose="sitdesk"), A("dimas", "dimas", expr="netral", pose="sitdesk")] + KANTIN_EX,
     move="push_slow", sfx=[(0, "canteen")], music=[(0, "drone_low")])
beat(13, 9, KN, "book", move="push")
beat(13, 15, KN, on("dimas", "close", side=0.55, dist=1.0, up=0.05), [A("dimas", "dimas", expr="cemas", pose="sitdesk", look="laras", talk=[["w15", "e20"]]),
                                                         LA(L2, "laras", expr="netral", pose="sitdesk")])
beat(13, 21, KN, on("laras", "close", side=-0.3, up=0.05), [LA(L2, "laras", expr="netral", pose="sitdesk", keys=[(0.3, "pose", "headdown")]),
                                                          A("dimas", "dimas", expr="cemas", pose="sitdesk")], hold=0.6)
beat(13, 23, KT(["=Senin, kuliah metode penelitian.", "=Dosen menjelaskan tentang", "=validitas dan reliabilitas.", "=Catatan: baca ulang bab 3."],
                "buku", light="day", desk="table"), "page", move="push_slow", music=[(0, "musicbox")])
beat(13, 35, KN, on("laras", "xclose", side=-0.2), [LA(L2, "laras", expr="netral", pose="sitdesk", blink=False)], move="push_slow")
# ================================================================== 14. small things
beat(14, 0, KL_TD, "wide", [LA(L2, "mid", expr="cemas", pose="idle", keys=[(1.2, "look", "shelf"), (3.0, "look", "door")])], move="push_slow",
     sfx=[(0, "day_room")])
beat(14, 7, KL_TD, "desk", [LA(L2, "chair", expr="netral", pose="sitdesk")], move="push", sfx=[(0, "cup")])
beat(14, 21, KN, "wide", [A("teman1", "ex1", pose="sitdesk", expr="senyum", talk=[[0.2, 3.0]]), A("teman2", "ex2", pose="sitdesk", expr="senyum"),
                          LA(L2, (-3.3, 0.38, -0.02), 180, expr="senyum", pose="sitdesk")], cam_over=None, move="push_slow", sfx=[(0, "laugh")])
beat(14, 24, KN, on("laras", "close", side=0.55, dist=1.0), [LA(L2, (-3.3, 0.38, -0.02), 180, expr="senyum", pose="sitdesk", blink=False),
                                                 A("teman2", "ex2", pose="sitdesk", expr="senyum")], move="push_slow")
beat(14, 28, KL_TD, "shelf", move="pan_r")
beat(14, 37, KL_TD, on("laras", "close", side=0.3), [LA(L2, "mid", expr="cemas", pose="idle", look="shelf")], move="push_slow")
# ================================================================== 15. everyone prefers her
beat(15, 0, KN, "wide", [LA(L2, "laras", expr="senyum", pose="sitdesk"), A("teman1", "dimas", expr="senyum", pose="sitdesk")] + KANTIN_EX[1:],
     move="push_slow", music=[(0, "drone_low")])
beat(15, 7, KN, on("teman1", "close", side=0.55, dist=1.0), [A("teman1", "dimas", expr="senyum", pose="sitdesk", look="laras", talk=[["w9", "e13"]]),
                                                 LA(L2, "laras", expr="senyum", pose="sitdesk")])
beat(15, 14, KL_TD, on("ibukos", "close", side=0.3), [A("ibukos", (1.2, -0.6, 0), -124, expr="senyum", look="laras", talk=[["w17", "e21"]]),
                                                     LA(L2, (0.6, -0.2, 0), 56, expr="senyum")])
beat(15, 22, RD, on("dosen", "close", side=0.25), [A("dosen", "dosen", pose="sitdesk", expr="senyum", talk=[["w24", "e26"]])])
beat(15, 27, KL_TD, on("laras", "xclose", side=0.15, dist=0.9), [LA(L2, (0.6, -0.2, 0), 56, expr="senyum", blink=False)], move="push_slow",
     music=[("w31", "sting_soft")])
# ================================================================== 16-18. Pak Karto
beat(16, 0, KK, "long", [LA(L2, "laras_walk0", expr="netral", walk=[[0.2, 6.0]],
                            keys=[(0, "move", [0.2, 1.5, 0, 180]), (6.0, "move", [-0.35, 7.3, 0, 160])]),
                         A("karto", "karto", expr="capek", pose="sweep", prop="broom")], move="static", sfx=[(0, "broom"), (0.2, "steps")],
     music=[(0, "drone_low")])
beat(16, 15, KK, "two", [LA(L2, "laras", expr="netral"), A("karto", "karto", expr="capek", pose="sweep", prop="broom",
                                                           keys=[("w21", "pose", "idle"), ("w21", "look", "laras")])], sfx=[(0, "broom")])
beat(16, 24, KK, on("karto", "close", side=0.3), [A("karto", "karto", expr="cemas", prop="broom", look="laras", talk=[["w24", "e29"]],
                                                  keys=[("w31", "look", [-1.2, 7.0, 1.2]), ("e31", "look", [1.0, 7.6, 1.2]),
                                                        ("w32", "look", [-1.0, 7.0, 1.2]), ("e32", "look", "laras")]),
                                                LA(L2, "laras", expr="netral")], hold=0.25)
beat(17, 0, KK, on("karto", "close", side=0.25), [A("karto", "karto", expr="cemas", prop="broom", look="laras", talk=[["w0", "e13"]])])
beat(17, 14, RD, on("dosen", "close", side=0.3), [A("dosen", "dosen", pose="sitdesk", expr="marah", talk=[["w14", "e21"]])], fx=OLD,
     music=[(0, "sting_soft")])
beat(17, 22, KK, "end", [A("karto", (0.0, 11.0, 0), 160, expr="capek", prop="broom", keys=[(0.4, "move", [0.0, 11.0, 0, 160]),
                                                                                         (1.6, "move", [0.0, 11.0, 0, 175])],
                           look=[0.3, 16.4, 1.6])], move="push_slow")
beat(17, 28, KK, on("karto", "xclose", side=0.25), [A("karto", "karto", expr="cemas", prop="broom", look="laras", talk=[["w28", "e43"]])],
     move="push_slow")
beat(18, 0, KK, on("laras", "close", side=-0.3), [LA(L2, "laras", expr="cemas", look="karto", talk=[["w0", "e3"]]),
                                                 A("karto", "karto", expr="capek", prop="broom")])
beat(18, 4, KK, on("karto", "close", side=0.3), [A("karto", "karto", expr="capek", prop="broom", look="laras", talk=[["w4", "e11"]])])
GRAD = dict(prop="toga", over=dict(shirt=[0.02, 0.02, 0.025], bottom=[0.02, 0.02, 0.025], long_skirt=True))
beat(18, 12, WS, "wide", [A("g1", "g1", **{"as": "teman1"}, expr="senyum", **GRAD), A("g2", "g2", **{"as": "teman2"}, expr="netral", **GRAD),
                          A("o1", "g3", **{"as": "ibukos"}, expr="cemas"), A("g3", "g4", **{"as": "maba2"}, expr="netral", **GRAD)],
     fx=[["desat", 0, 999]], move="push_slow", sfx=[(0, "crowd")], music=[(0, "musicbox")])
beat(18, 23, WS, "two", [A("o1", "ibu", **{"as": "ibukos"}, expr="cemas", talk=[["w23", "e35"]], look="g2"),
                         A("g2", "laras", **{"as": "teman2"}, expr="senyum", blink=False, **GRAD)], fx=[["desat", 0, 999]], move="push_slow")
# ================================================================== 19-21. she stops; the name; the stain; "Siapa kamu?"
beat(19, 0, KL_T, "door", [LA(L3, "door", expr="cemas", pose="papers", prop="papers", walk=[[0.4, 3.2]],
                              keys=[(0, "move", [1.25, -1.0, 0, 90]), (0.4, "move", [1.25, -1.0, 0, 90]), (3.2, "move", [0.3, 0.1, 0, 160]),
                                    (4.2, "move", [0.3, 0.1, 0, 60]), (4.6, "pose", "knock")])],
     move="static", sfx=[(0.2, "door_open"), (3.4, "door_close"), (4.8, "lock")], music=[(0, "drone_low")])
beat(19, 15, KL_T, on("laras", "close", side=0.3), [LA(L3, (0.3, 0.1, 0), 160, expr="cemas", keys=[("w18", "expr", "takut")])], move="push_slow")
beat(19, 29, KL_T, "desk", [LA(L3, "chair", expr="takut", pose="sitdesk")], move="push", sfx=[(0, "zipper")])
beat(19, 34, KT(TITLE_L[:7] + ["~LARAS PRAMESTI", "NIM 1518301142", "", "", "^Belum tepat."], "a4", title_page=True), "top", move="push_slow",
     dyn=[hide("kt_s7", "w36"), hide("kt_l11", "w44")], sfx=[("w36", "pen_strike")], music=[("w44", "sting")])
beat(20, 0, KL_T, "wide", [LA(L3, "mid", expr="takut", pose="nervous", keys=[(0.8, "look", "shelf"), (2.2, "look", "bed"), (3.4, "look", "desk")])],
     move="push_slow", sfx=[(0, "rummage")], hold=0.3)
beat(20, 12, TGN, "case", move="push", sfx=[(0, "zipper")])
beat(20, 21, TGN, "pen", move="push_slow")
beat(20, 24, TGN, "finger", move="push_slow", music=[("w31", "sting_soft"), (0, "heartbeat")])
beat(21, 0, KT(["", "", "@Siapa kamu?"], "a4", light="cold", pencil=True, pen=False), "topline", move="push_slow",
     dyn=[hide("kt_l2", "w12")], sfx=[("w9", "pencil_write")], music=[(0, "drone_low")])
beat(21, 14, KL_T, on("laras", "xclose", side=0.2, dist=0.72, lens=38), [LA(L3, "chair", expr="takut", pose="sitdesk", blink=False)], move="push_slow",
     sfx=[(0, "clock")])
beat(21, 22, KL_T, on("laras", "xclose", side=0.2, dist=0.72, lens=38), [LA(L3, "chair", expr="takut", pose="sitdesk", blink=False,
                                                     keys=[("w24", "expr", "tidur"), ("e24", "expr", "takut")])], move="static",
     fx=[["black", "w24", "e24"]])
beat(21, 25, KL_DAWN, "wide", [LA(L3, "chair", expr="takut", pose="sitdesk"),
                               GHOST((0.25, 0.55, 0), 200, keys=[(0.0, "show", 1), (0.35, "show", 0)])],
     move="static", sfx=[(0, "birds_far")], music=[(0, "sting")])
beat(21, 35, KT(["", "", "@Siapa kamu?", "!Pertanyaan kurang tepat."], "a4", light="day", pencil=True), "topline", move="push",
     dyn=[hide("kt_l3", "w39")])
# ================================================================== 22-23. who were you before me
beat(22, 0, KT(["", "", "@Siapa kamu?", "!Pertanyaan kurang tepat.", "!Yang benar...", "!siapa kamu, sebelum aku?"], "a4", light="day", pencil=True),
     "page", move="push_slow", dyn=[hide("kt_l4", "w3"), hide("kt_l5", "w5")], music=[("w5", "sting")])
beat(22, 9, KL_DAWN, on("laras", "xclose", side=0.25, dist=0.72, lens=38), [LA(L3, "chair", expr="cemas", pose="sitdesk")], move="push_slow")
beat(22, 12, KT(["=Makanan kesukaan: mie ayam Pak No.", "=Lagu: yang selalu kuputar waktu SMA.", "=Masuk jurusan ini karena ingin", "=jadi penulis.",
                 "", "=- Laras, 2019"], "buku", light="day"), "page", move="pan_d", music=[(0, "musicbox")])
beat(22, 28, KL_DAWN, on("laras", "close", side=-0.3, dist=0.8, lens=35), [LA(L3, "chair", expr="netral", pose="sitdesk", blink=False)], move="push_slow")
beat(23, 0, KP, "wide", [A("ibu", "ibu", expr="senyum"), A("kecil", "kecil", expr="senyum", walk=[[0.5, 3.0]],
                                                         keys=[(0, "move", [0.4, 1.2, 0, 170]), (3.0, "move", [0.3, 2.3, 0, 180])])],
     fx=[["dream", 0, 999]], move="push_slow", sfx=[(0, "evening_village")], music=[(0, "memory")])
beat(23, 10, KP, "door", [A("ibu", "ibu", expr="senyum", talk=[[0.2, 1.4]], aud=False)], fx=[["dream", 0, 999]], move="push_slow")
beat(23, 17, KP, "low", [A("kecil", (0.3, 2.3, 0), 180, expr="senyum")], fx=[["dream", 0, 999]], move="pan_r")
beat(23, 21, KP, "door", [A("ibu", "ibu", expr="senyum", talk=[["w24", "e26"]], aud=False)], move="push",
     fx=[["dream", 0, 999], ["redline", "w29", 1.0]], music=[("w27", "cut"), ("w30", "sting")])
# ================================================================== 24-26. the defence, graduation, the one line
PANEL = [A("penguji1", "p1", pose="sitdesk"), A("penguji2", "p2", pose="sitdesk"), A("penguji3", "p3", pose="sitdesk")]
beat(24, 0, SD, "wide", [LA(L3, "laras", expr="senyum", talk=[[1.5, 99]], aud=False)] + PANEL, move="push_slow", sfx=[(0, "room_tone")],
     music=[(0, "drone_low")])
beat(24, 5, SD, on("laras", "close", side=0.3), [LA(L3, "laras", expr="senyum", talk=[[0.1, 99]], aud=False, blink=False)], move="push_slow")
beat(24, 16, SD, "wide", [LA(L3, "laras_s", expr="senyum"), A("penguji1", "p1s", expr="senyum", pose="give"),
                           A("penguji2", "p2s", expr="senyum", pose="give"), A("penguji3", "p3s", expr="senyum")], sfx=[(0, "applause_small")])
beat(24, 21, SD, on("laras", "xclose", side=0.2), [LA(L3, "laras_s", expr="senyum", blink=False)], move="push_slow")
beat(24, 24, KT(["#BERITA ACARA SIDANG SKRIPSI", "", "Nama        : ~Laras Pramesti", "!Seseorang", "Predikat    : Dengan Pujian", "",
                 "Penguji I   : ................", "Penguji II  : ................"], "a4", light="day"), "page", move="push",
     dyn=[hide("kt_l3", "w25")], music=[("w24", "sting")])
WS_L = LA(L3, "laras", expr="senyum", pose="hugstand", **GRAD)
beat(25, 0, WS, "wide", [dict(WS_L, pose="idle"), A("ibu", (-1.5, 1.2, 0), -60, expr="senyum", walk=[[0.0, 2.6]],
                                                    keys=[(0, "move", [-1.5, 1.2, 0, -60]), (2.6, "move", [-0.32, 2.35, 0, -90])]),
                         A("g1", "g1", **{"as": "teman1"}, expr="senyum", **GRAD), A("g2", "g2", **{"as": "teman2"}, expr="senyum", **GRAD)],
     move="push_slow", sfx=[(0, "crowd")], music=[(0, "sad")])
beat(25, 4, WS, "two", [WS_L, A("ibu", "ibu", expr="nangis", pose="hugstand")], move="push_slow")
beat(25, 9, WS, [[0.55, 1.55, 1.3], [-0.24, 2.35, 1.12], 40], [A("ibu", "ibu", expr="nangis", pose="hugstand", talk=[["w9", "e13"]]), WS_L])
beat(25, 14, WS, on("laras", "xclose", side=0.2), [dict(WS_L, blink=False)], move="push", fx=[["red", "w21", 1.4], ["flicker", "w21", 1.4]],
     music=[("w21", "sting")], sfx=[("w21", "scream_muffled")])
beat(25, 25, WS, on("laras", "close", side=0.3), [dict(WS_L, talk=[["w34", "e36"]], blink=False)], move="push_slow")
beat(26, 0, WS, on("laras", "xclose", side=0.15), [dict(WS_L, blink=False)], move="push_slow", fx=[["vignette", 0, 999]], music=[(0, "drone_low")])
STRIKE = ["Aku suka mie ayam Pak No.", "Aku suka tertawa keras.", "Aku benci kopi hitam.", "Aku ingin jadi penulis.", "Aku Laras."]
beat(26, 9, KT(["~" + x for x in STRIKE], "buku", light="cold"), "top", move="push_slow",
     dyn=[hide(f"kt_s{i}", round(0.3 + 0.55 * i, 2)) for i in range(5)], sfx=[(0.3, "pen_strikes")])
beat(26, 16, RB_NIGHT, "long", move="push_slow", sfx=[(0, "hum")])
beat(26, 24, KT([], "jilid"), "top", move="push_slow", sfx=[(0, "page")])
beat(26, 36, KT(["#UCAPAN TERIMA KASIH", "", "", "", "=Untuk Laras.", "=Yang sudah saya perbaiki."], "jilid"), "right", move="push_slow",
     dyn=[hide("kt_l4", "w40"), hide("kt_l5", "w42")], music=[("w40", "sting")])
# ================================================================== 27-29. the building still stands; you
beat(27, 0, EXT_N, "road", move="push_slow", sfx=[(0, "crickets"), (0, "wind")], music=[(0, "drone_in")])
beat(27, 6, EXT_N, "up3", move="push_slow")
beat(27, 12, TG_C, "gate", [A("maba2", (0.3, 2.55, 1.485), 20, expr="cemas", prop="papers", pose="papers", walk=[[0.2, 3.0]],
                             keys=[(0, "move", [0.3, 2.55, 1.485, 20]), (3.0, "move", [-0.6, 2.05, 1.485, 0])])], move="static",
     sfx=[(0.2, "steps")])
beat(27, 23, RB_NIGHT, "corner", move="push_slow", sfx=[(0, "clock")])
beat(27, 31, RB_NIGHT, "behind", [GHOST("corner_far")], move="push_slow", music=[(0, "tension")])
beat(28, 0, MK, "wide", move="push_slow", music=[(0, "drone_low")], sfx=[(0, "room_tone")])
beat(28, 9, MK, "chair", move="push_slow")
beat(28, 20, MK, "wide", move="push_slow")
beat(28, 31, MK, "paper", move="push_slow", music=[(0, "tension")])
beat(29, 0, KT(["*NAMA: LARAS", "*KELAS: 4B", "*Cita-citaku: jadi penulis!"], "buku", light="lamp"), "top", move="push_slow",
     music=[(0, "musicbox")])
beat(29, 16, KT(["=Nama: Laras Pramesti", "=Kelas: -", "=Cita-cita: -"], "buku", light="cold"), "top", move="push",
     music=[("w22", "sting_soft")])
beat(29, 24, RB_NIGHT, "front", [LA(L3, "chair", expr="senyum", pose="sitstill", blink=False)], move="push_slow")
beat(29, 29, MK, "paper", move="push_slow", music=[("w29", "sting")])
beat(29, 30, KT(["#SKRIPSI", "", "", "", "", "Disusun oleh:", "...................................", "!kamu"], "a4", title_page=True,
                light="lamp"), "top", move="push", dyn=[hide("kt_l7", "w33")], music=[("w33", "end")], end=True)


# ------------------------------------------------------------------ resolve times
def wtime(seg, w):
    return SEGW[seg][w]["start"]


def wend(seg, w):
    return SEGW[seg][w]["end"]


def mouth_frames(t0, spans, nfr):
    """frames (1-based, relative to the shot) where the mouth is open, from the VO loudness"""
    out = []
    for a, b in spans:
        A_, B_ = t0 + a, t0 + b
        seg_env = _env[int(A_ * 100):int(B_ * 100) + 1]
        if len(seg_env) < 3:
            continue
        thr = 0.35 * np.percentile(seg_env, 90)
        prev = 0.0
        for f in range(max(1, int(a * FPS) + 1), min(nfr, int(b * FPS) + 1) + 1):
            tt = t0 + (f - 1) / FPS
            v = _env[int(tt * 100):int(tt * 100) + 8].mean() if int(tt * 100) + 8 < len(_env) else 0
            if v > thr and not (prev > v * 1.6):     # a sharp dip closes the mouth (syllable gaps)
                out.append(f)
            prev = v
    return out


starts = []
for i, b in enumerate(B):
    if b["w"] == 0:
        t = 0.0 if i == 0 else max(starts[-1] + 0.5, wtime(b["seg"], 0) - 0.45)
    else:
        t = wtime(b["seg"], b["w"]) - 0.12
    starts.append(round(t, 3))
shots = []
for i, b in enumerate(B):
    t0 = starts[i]
    t1 = starts[i + 1] if i + 1 < len(B) else END
    assert t1 - t0 > 0.3, (b["seg"], b["w"], t0, t1)
    dur = round(t1 - t0, 3)
    nfr = round(dur * FPS)

    def rel(v):
        if isinstance(v, str) and v[0] in "we" and v[1:].isdigit():
            f = wtime if v[0] == "w" else wend
            return round(max(0.0, f(b["seg"], int(v[1:])) - t0), 3)
        return v

    cast = []
    for c in b["cast"]:
        c = json.loads(json.dumps(c))
        c["keys"] = [[rel(k[0])] + k[1:] for k in c.get("keys", [])]
        if c.get("walk"):
            c["walk"] = [[rel(a), min(rel(z), dur)] for a, z in c["walk"]]
        if c.get("talk"):
            c["talk"] = [[rel(a), min(rel(z), dur)] for a, z in c["talk"]]
            if c.pop("aud", True):
                c["mouth"] = mouth_frames(t0, c["talk"], nfr)
        c.pop("aud", None)
        if c.get("rot") is None:
            c.pop("rot")
        cast.append(c)
    dyn = []
    for d in b.get("dyn", []):
        d = dict(d); d["keys"] = [[rel(k[0]), k[1]] for k in d["keys"]]
        dyn.append(d)
    st = dict(b["set"]); st.update(b.get("set_over", {}))
    fx = [[f[0], rel(f[1]), rel(f[2]) if f[0] in ("old", "black", "desat", "dream", "vignette") else f[2]] for f in b.get("fx", [])]
    shot = dict(id=i + 1, seg=b["seg"], w=b["w"], t0=t0, t1=round(t1, 3), set=st, cam=b["cam"], cast=cast, dyn=dyn,
                extras=b.get("extras", []), move=b["move"], sfx=[[rel(t), n] for t, n in b.get("sfx", [])],
                music=[[rel(t), n] for t, n in b.get("music", [])], fx=fx,
                title=b.get("title", False), end=b.get("end", False),
                text=" ".join(w["w"] for w in WORDS if t0 <= w["start"] < t1))
    if b.get("hold"):
        for c in shot["cast"]:
            c.setdefault("hold", b["hold"])
    shots.append(shot)
json.dump(dict(fps=FPS, size=[960, 540], out_size=[1920, 1080], duration=END, shots=shots), open("plan_rt.json", "w"), indent=1,
          ensure_ascii=False)
print(len(shots), "shots,", sum(round((s["t1"] - s["t0"]) * FPS) for s in shots), "frames @12fps, END", round(END, 2))
