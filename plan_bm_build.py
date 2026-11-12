"""Writes plan_bm.json: every shot of "Bangsal Melati", timed to bm_audio/words.json.
Beat = (segment, first word index, spec). A shot runs from its beat to the next beat.
Times inside a spec: seconds from the shot start, "wN" = start of word N of the same segment, "eN" = end of word N.
talk=[[a, b], ...] makes the actor lip-sync between a and b.
"""
import json

WORDS = json.load(open("bm_audio/words.json"))
CUTS = {c["seg"]: c for c in json.load(open("bm_audio/vo_cuts.json"))}
SEGW = {}
for w in WORDS:
    SEGW.setdefault(w["seg"], []).append(w)
END = CUTS[36]["end"] + 4.0

# ------------------------------------------------------------------ sets
EXT_N = dict(name="rs_ext", night=True, exposure=2.4)
EXT_D = dict(name="rs_ext", night=False, car=True, exposure=0.45)
EXT_DAY = dict(name="rs_ext", night=False, exposure=0.45)
LOR = dict(name="lorong", exposure=0.75)
LOR_DARK = dict(name="lorong", dead=[2, 3, 5], lights=0.5, exposure=1.0)
LOR_WET = dict(name="lorong", wet=True, chain_state="broken", lights=0.45, dead=[2, 4], exposure=1.1)
LOR_OPEN = dict(name="lorong", wet=True, chain_state="broken", door_open=14, lights=0.45, dead=[2, 4], exposure=1.1)
LOR_SLAM = dict(name="lorong", wet=True, chain_state="broken", lights=0.6, exposure=1.0)
LOR_WELD = dict(name="lorong", chain_state="welded", night=False, exposure=0.7)
LOR_DAYL = dict(name="lorong", night=False, exposure=0.6)
JAGA = dict(name="jaga", exposure=1.15)
JAGA_D = dict(name="jaga", drawer_open=0.0, exposure=1.15)
HAR = dict(name="kamar_harun", exposure=1.15)
BANG = dict(name="bangsal", exposure=2.0)
K4 = dict(name="kamar4", exposure=1.9)
K4B = dict(name="kamar4", state="bongkar", exposure=1.2)
CAR = dict(name="mobil", exposure=1.0)
MAK = dict(name="makam", exposure=0.3)
KOS = dict(name="kos", clock="02:16", exposure=1.9)
KOS17 = dict(name="kos", clock="02:17", exposure=1.9)
RULES = ["#ATURAN JAGA MALAM - SAYAP TIMUR", "1. Jangan masuk Bangsal Melati.", "   Dengan alasan apa pun.",
         "2. Ketukan setelah pukul 02.00:", "   jangan didatangi.", "3. Ada yang memanggil namamu",
         "   dari lorong timur: jangan dijawab.", "4. Pasien bertanya tentang \"Ibu\":", "   alihkan pembicaraan."]


def BK(lines, style="open", exposure=1.3):
    return dict(name="buku", lines=lines, style=style, exposure=exposure)


def A(who, at, rot=0, expr=None, pose="idle", keys=(), **k):
    d = dict(who=who, at=at if isinstance(at, str) else list(at), rot=rot, pose=pose, keys=[list(x) for x in keys])
    if expr:
        d["expr"] = expr
    d.update(k)
    return d


def on(who, kind="close", **k):
    d = dict(on=who, kind=kind); d.update(k)
    return d


B = []


def beat(seg, w, set_, cam, cast=(), move="push_slow", **k):
    d = dict(seg=seg, w=w, set=set_, cam=cam, cast=list(cast), move=move)
    d.update(k)
    B.append(d)


# frequently used actors
SARI_DESK = A("sari_p", "desk", None, "netral")
WIWIK_DOOR = A("wiwik", "door", None, "netral")
HARUN = A("harun", "harun_bed", None, "capek", pose="sit", breathe=True)
SARI_HDOOR = A("sari_p", "sari_door", None, "netral", prop="papers", pose="papers")
WIW_CAR = A("wiwik", "driver", 0, "cemas", pose="drive", at_z=0.1)
SARI_CAR = A("sari_p", "pass", 0, "cemas", pose="sitlap", at_z=0.1)
RATNA_K4 = A("ratna", (-0.95, 2.6, -0.3), 35, "takut", pose="hug")
SARI_K4 = A("sari_p", (0.35, 1.0, 0), 160, "takut", pose="torch", prop="torch")
SARI_KOS_LIE = A("sari_p", (0, 0, 0), 0, "tidur", lie=[-0.9, 1.45, 0.66, 0])
SARI_KOS_SIT = A("sari_p", "sit", None, "takut", pose="sit")

# ================================================================== 1. opening
beat(1, 0, EXT_N, "road", title=True, sfx=[(0, "rain"), (0, "wind")], music=[(0, "drone_in")])
beat(1, 8, EXT_N, "wide", move="pan_r")
beat(1, 29, EXT_N, "facade", move="push")
beat(1, 39, LOR, "long", move="push_slow", sfx=[(0, "hum_tube")])
# ================================================================== 2. Sari arrives, Bu Wiwik
beat(2, 0, LOR, "long", [A("sari_p", (0, 12, 0), 0, "netral", walk=[[0, 6.0]], keys=[(0, "move", [0, 12, 0, 0]), (6.0, "move", [0, 5, 0, 0])])],
     move="static", sfx=[(0, "steps")])
beat(2, 8, JAGA, "wide", [SARI_DESK], move="push_slow")
beat(2, 18, JAGA, on("sari_p", "close", side=0.25), [SARI_DESK], move="push_slow")
beat(2, 31, JAGA, "wide", [SARI_DESK, A("wiwik", "door", None, "netral", walk=[[0, 3.0]],
                                        keys=[(0, "move", [0.9, -1.6, 0, 180]), (3.0, "move", [0.4, 0.0, 0, 185])])],
     move="static", sfx=[(0, "door_open")])
beat(2, 47, JAGA, on("wiwik", "medium", side=0.4), [A("sari_p", (0.2, 0.75, 0), 10, "netral"),
                                                    A("wiwik", (0.4, 0.0, 0), 185, "netral", pose="give", prop="papers")], sfx=[(0, "keys")])
beat(2, 60, JAGA, on("wiwik", "close", side=0.3), [A("wiwik", (0.4, 0.0, 0), 185, "netral", talk=[["w60", "e61"]])], move="push")
# ================================================================== 3. the rules
beat(3, 0, BK(RULES, "kertas"), "top", move="push_slow", sfx=[(0, "paper")])
beat(3, 10, BK(RULES, "kertas"), "page", move="pan_d")
beat(3, 30, LOR_DARK, "long", move="push_slow", sfx=[(0, "whisper_far")])
beat(3, 42, BK(RULES, "kertas"), "page", move="push")
# ================================================================== 4. "Ini... serius, Bu?"
beat(4, 0, JAGA, on("sari_p", "close", side=0.35), [A("sari_p", (0.2, 0.75, 0), 10, "senyum", talk=[["w3", "e5"]])])
beat(4, 6, JAGA, on("wiwik", "close", side=-0.2), [A("wiwik", (0.4, 0.0, 0), 185, "netral", blink=False)], move="push")
beat(4, 15, JAGA, on("sari_p", "close", side=0.3), [A("sari_p", (0.2, 0.75, 0), 10, "senyum", keys=[("w17", "expr", "cemas")])])
beat(4, 19, JAGA, on("wiwik", "xclose", side=-0.15), [A("wiwik", (0.4, 0.0, 0), 185, "netral", talk=[["w19", "e25"], ["w26", "e30"]])],
     move="push", music=[("w26", "sting_soft")])
# ================================================================== 5. Pak Harun
beat(5, 0, LOR, "side", move="pan_r")
beat(5, 14, HAR, "back", [HARUN], sfx=[(0, "humming")])
beat(5, 28, HAR, on("harun", "close", side=0.5), [HARUN])
beat(5, 42, HAR, "wall", [HARUN], move="push")
beat(5, 53, HAR, "door", [HARUN, A("sari_p", "sari_door", None, "netral", prop="papers", pose="papers", walk=[[0, 2.0]],
                                     keys=[(0, "move", [-1.0, -1.6, 0, 180]), (2.0, "move", [-0.4, -0.6, 0, 200])])],
     move="static", sfx=[("w62", "hum_stop")])
# ================================================================== 6. "Suster baru, ya?"
SARI_H = A("sari_p", (-0.4, -0.6, 0), 120, "senyum", prop="papers", pose="papers")
beat(6, 0, HAR, on("harun", "close", side=0.55), [dict(HARUN, talk=[["w0", "e2"]])])
beat(6, 6, HAR, on("sari_p", "medium", side=0.2), [dict(SARI_H, talk=[["w6", "e9"]]), HARUN])
beat(6, 10, HAR, on("harun", "xclose", side=0.45), [dict(HARUN, talk=[["w10", "e10"], ["w19", "e26"]], expr="cemas")], move="push")
# ================================================================== 7. "Ibu." and the first knocks
beat(7, 0, HAR, on("sari_p", "close", side=0.2), [dict(SARI_H, expr="cemas", talk=[["w0", "e1"]])])
beat(7, 2, HAR, "back", [dict(HARUN, keys=[("w9", "pose", "wallhand")])])
beat(7, 14, HAR, on("harun", "xclose", side=0.4), [dict(HARUN, pose="wallhand", expr="cemas", talk=[["w14", "e14"]])], move="push")
beat(7, 15, LOR_DARK, "clock", move="push", sfx=[("w21", "clock2")])
beat(7, 28, LOR_DARK, "long", move="push_slow", music=[(0, "tension")])
beat(7, 34, LOR_DARK, "chain", move="push_slow")
beat(7, 39, LOR_DARK, "door", move="static", sfx=[("w40", "knock"), ("w41", "knock"), ("w42", "knock")],
     music=[("w40", "sting")])
# ================================================================== 8. Ratna wants the door opened
beat(8, 0, HAR, on("harun", "xclose", side=0.4), [dict(HARUN, expr="tidur", talk=[["w4", "e7"], ["w9", "e14"]])])
beat(8, 15, JAGA, "wide", [A("sari_p", "desk", None, "cemas", keys=[(1.5, "look", [1.0, -2.2, 1.1])])])
beat(8, 20, LOR_DARK, "clock", move="push")
beat(8, 31, LOR_DARK, "door", move="static", sfx=[(0.3, "knock"), (0.8, "knock"), (1.3, "knock"), (3.0, "knock"), (3.5, "knock"), (4.0, "knock")])
beat(8, 40, JAGA, on("sari_p", "close", side=0.3), [A("sari_p", "desk", None, "cemas")])
beat(8, 46, LOR_DARK, "long", [A("sari_p", "start", None, "cemas")], move="push_slow")
# ================================================================== 9. the drawer and the register
beat(9, 0, JAGA, "cab", [A("sari_p", "cab", None, "netral", pose="papers")])
beat(9, 15, JAGA, "cab", [A("sari_p", "cab", None, "cemas", pose="papers", keys=[(0.4, "pose", "give")])],
     dyn=[dict(obj="j_drawer0", prop="locx", keys=[(0.0, 1.27), (0.9, 0.97)])], move="static", sfx=[(0.3, "drawer")])
beat(9, 27, BK([], "closed"), "top", move="push_slow", sfx=[(0, "paper")])
beat(9, 39, BK([], "closed"), "low", move="push")
beat(9, 52, BK(["Sumarni - 12 Jan 1987 - Luminal", "Rukmini - 20 Jan 1987 - CPZ", "Tini - 26 Jan 1987 - Luminal",
                "Wartini - 30 Jan 1987 - Haloperidol"]), "top", move="pan_d", sfx=[(0, "page")])
beat(9, 62, BK(["Sumarni - 12 Jan 1987 - Luminal", "Rukmini - 20 Jan 1987 - CPZ", "Tini - 26 Jan 1987 - Luminal",
                "Wartini - 30 Jan 1987 - Haloperidol"]), "page", move="push", music=[(0, "tension")])
# ================================================================== 10-12. the entries
beat(10, 0, BK(["2 Februari 1987.", "Pasien kamar 2 mengeluh mendengar", "ketukan dari dalam dinding.", "Diberi obat tidur."]), "page", sfx=[(0, "page")])
beat(10, 19, BK(["9 Februari.", "3 pasien mengeluhkan hal yang sama.", "Semua menyebut", "\"ibu-ibu di dalam tembok\"."]), "page", move="push")
beat(10, 33, BK(["3 Maret. Pasien baru.", "Ratna, 19 tahun. Kamar 4."]), "page", move="push")
beat(10, 43, BK(["8 Maret. Ratna menolak tidur.", "\"Ibu\" memanggil namanya tiap malam.", "Kalau dijawab,", "Ibu bisa keluar."]), "page", move="push_slow")
beat(11, 0, BK(["12 Maret. Ratna mengetuk pintu", "sepanjang malam. Minta dipindahkan.", "Ditolak - dr. H."]), "page", sfx=[(0, "page")])
beat(11, 16, BK(["14 Maret. Pukul 02.17.", "Pasien ditemukan di kamar 4.", "Pintu terkunci dari luar.",
                 "Semua kuku patah. Dinding penuh goresan."]), "page", move="push")
beat(11, 38, K4, "wall", move="push", music=[(0, "sting_soft")])
beat(11, 42, BK(["Pasien meninggal."]), "page", move="push_slow")
beat(12, 0, BK(["Pasien meninggal.", "", "!Saya yang mengunci pintunya.", "!Saya dengar dia minta tolong.", "!Saya tidak buka.",
                "!Tertanda,  W."]), "page", move="push_slow")
beat(12, 21, BK(["!Saya tidak buka.", "!Tertanda,  W."]), "page", move="push", music=[("w22", "sting_soft")])
beat(12, 23, JAGA, on("sari_p", "close", side=0.3), [A("sari_p", "desk", None, "takut", blink=False)], move="push_slow")
# ================================================================== 13-16. in Bu Wiwik's car
beat(13, 0, EXT_D, "car", [A("sari_p", "car_side", 150, "cemas", pose="give", prop="papers")], sfx=[(0, "evening")], music=[(0, "drone_low")])
beat(13, 8, EXT_D, on("sari_p", "medium", side=0.5), [A("sari_p", "car_side", 150, "cemas", pose="give", prop="papers"),
                                                    A("wiwik", (2.1, 23.0, 0), -10, "netral")])
beat(13, 16, EXT_D, on("wiwik", "close", side=0.3), [A("wiwik", (2.1, 23.0, 0), -10, "takut", blink=False)], move="push")
beat(13, 20, CAR, "front", [WIW_CAR, SARI_CAR], sfx=[(0, "car_door")])
beat(13, 26, CAR, "wiwik", [WIW_CAR, SARI_CAR], move="push_slow")
beat(13, 31, CAR, "wiwik", [dict(WIW_CAR, talk=[["w31", "e36"]])], move="push_slow")
beat(13, 40, CAR, "two", [dict(WIW_CAR, talk=[["w40", "e55"]]), SARI_CAR])
beat(14, 0, CAR, "wiwik", [dict(WIW_CAR, talk=[["w0", "e13"]])])
beat(14, 5, LOR_DARK, "door", move="static", sfx=[(0.1, "knock"), (0.5, "knock"), (0.9, "knock"), (2.4, "knock"), (2.8, "knock"), (3.2, "knock")],
     fx=[["old", 0, 99]])
beat(14, 11, CAR, "wiwik", [dict(WIW_CAR, expr="nangis", talk=[["w11", "e20"]])], move="push")
beat(14, 21, CAR, "two", [dict(WIW_CAR, expr="nangis"), SARI_CAR])
beat(14, 25, CAR, "wiwik", [dict(WIW_CAR, expr="cemas", talk=[["w25", "e41"]])])
beat(14, 42, K4, "wall", move="push_slow", sfx=[(0.2, "knock_heavy"), (1.0, "knock_heavy")], fx=[["old", 0, 99]], music=[(0, "sting_soft")])
beat(14, 48, CAR, "wiwik", [dict(WIW_CAR, expr="takut", talk=[["w48", "e66"]])], move="push")
beat(15, 0, CAR, "sari", [WIW_CAR, dict(SARI_CAR, talk=[["w0", "e3"]])])
beat(15, 4, CAR, "wiwik", [dict(WIW_CAR, keys=[(0.6, "expr", "takut")])], move="push")
beat(15, 8, CAR, "two", [dict(WIW_CAR, talk=[["w8", "e19"]]), SARI_CAR])
beat(15, 20, BANG, "entry", [A("hantu", (0.0, 9.0, 0), 0)], move="push_slow", fx=[["old", 0, 99]], music=[(0, "sting_soft")])
beat(15, 30, CAR, "wiwik", [dict(WIW_CAR, talk=[["w30", "e48"]])], move="push_slow")
beat(16, 0, CAR, "wiwik", [dict(WIW_CAR, talk=[["w3", "e20"]])])
beat(16, 9, K4, "low", move="push_slow")
beat(16, 21, CAR, "front", [dict(WIW_CAR, expr="takut"), dict(SARI_CAR, expr="takut")], sfx=[(0, "cold_wind")])
beat(16, 28, CAR, "wiwik", [dict(WIW_CAR, expr="takut", talk=[["w28", "e34"], ["w38", "e45"]])], move="push")
beat(16, 46, LOR_DARK, "door", move="push_slow", sfx=[(0.4, "knock"), (0.8, "knock"), (1.2, "knock")])
beat(16, 53, CAR, "sari", [WIW_CAR, dict(SARI_CAR, expr="takut", blink=False)], move="push")
# ================================================================== 17-18. the chain is broken
beat(17, 0, EXT_N, "road", move="push_slow", sfx=[(0, "rain_heavy"), (1.0, "thunder")], music=[(0, "drone_in")])
beat(17, 5, LOR_DARK, "long", move="static", fx=[["dark", "w10", 0.7], ["dark", 3.6, 0.5]], sfx=[("w10", "power_off"), (3.6, "power_off")])
beat(17, 13, JAGA, "door", [A("sari_p", "desk", 0, "cemas"),
                             A("darto", "door", None, "cemas", prop="torch", pose="torch", talk=[["w30", "e35"]])])
beat(17, 36, LOR_WET, "back", [A("sari_p", (0.35, 3.0, 0), 180, "cemas", prop="torch", pose="torch", walk=[[0, 99]],
                                 keys=[(0, "move", [0.35, 3.0, 0, 180]), (6.0, "move", [0.35, 9.0, 0, 180])]),
                               A("darto", (-0.35, 2.6, 0), 180, "cemas", prop="torch", pose="torch", walk=[[0, 99]],
                                 keys=[(0, "move", [-0.35, 2.6, 0, 180]), (6.0, "move", [-0.35, 8.6, 0, 180])])], move="static",
     sfx=[(0, "steps_wet")])
beat(17, 44, LOR_WET, "low", move="push_slow", sfx=[(0, "drip")])
beat(17, 54, LOR_WET, on("sari_p", "close", side=0.3), [A("sari_p", "mid", None, "cemas", prop="torch", pose="torch")], move="push_slow")
beat(17, 63, LOR_WET, "end", [A("sari_p", (0.35, 19.5, 0), 180, "cemas", prop="torch", pose="torch"),
                              A("darto", (-0.35, 19.2, 0), 180, "cemas", prop="torch", pose="torch")], music=[(0, "tension")])
beat(18, 0, LOR_WET, "chain", move="push")
beat(18, 9, LOR_WET, "chain", move="push_slow", music=[("w14", "sting_soft")])
beat(18, 23, LOR_OPEN, "door", move="push_slow", sfx=[(0, "creak")])
beat(18, 28, LOR_OPEN, on("darto", "close", side=0.3), [A("darto", "door_out", 0, "takut", prop="torch", pose="torch", talk=[["w28", "e28"], ["w32", "e36"]])])
beat(18, 37, LOR_OPEN, "end", [A("darto", (-0.5, 21.0, 0), 180, "takut", prop="torch", pose="torch"),
                               A("sari_p", (0.3, 21.4, 0), 180, "netral", prop="torch", pose="torch", walk=[[0.3, 99]],
                                 keys=[(0.3, "move", [0.3, 21.4, 0, 180]), (3.0, "move", [0.3, 23.6, 0, 180])])])
# ================================================================== 19-20. inside the ward
beat(19, 0, LOR_OPEN, on("sari_p", "xclose", side=0.2), [A("sari_p", "near_door", 0, "netral", prop="torch", pose="torch", blink=False)])
beat(19, 16, LOR_OPEN, on("sari_p", "medium", side=-0.3), [A("sari_p", "near_door", 0, "netral", prop="torch", pose="torch")], music=[(0, "drone_low")])
beat(19, 23, BANG, "entry", [A("sari_p", "entry", 180, "cemas", prop="torch", pose="torch", walk=[[0, 99]],
                              keys=[(0, "move", [0.0, 0.8, 0, 180]), (7.0, "move", [0.0, 4.5, 0, 180])])], move="static", sfx=[(0, "steps_slow")])
beat(19, 30, BANG, "beds", move="pan_r")
beat(19, 40, BANG, "cal", move="push")
beat(19, 55, BANG, "wchair", move="push_slow")
beat(20, 0, BANG, "k4", [A("sari_p", (0.0, 8.0, 0), 180, "cemas", prop="torch", pose="torch", walk=[[0, 99]],
                          keys=[(0, "move", [0.0, 8.0, 0, 180]), (4.0, "move", [0.0, 10.8, 0, 180])])], move="static")
beat(20, 5, K4, "side", [dict(SARI_K4, keys=[(0, "move", [0.15, 0.3, 0, 180]), (2.0, "move", [0.15, 0.7, 0, 180])], walk=[[0, 2.0]])], move="static")
beat(20, 13, K4, on("sari_p", "close", side=0.3), [dict(SARI_K4, at=[0.15, 0.7, 0], rot=180, blink=False)], move="push")
beat(20, 16, K4, "wall", move="push_slow", music=[(0, "tension")])
beat(20, 24, K4, "corner", move="pan_l")
beat(20, 36, K4, "text", move="push_slow")
beat(20, 51, K4, "text", move="push", music=[("w51", "sting")], fx=[["flash", "w51", 0.15]])
beat(20, 57, K4, "low", move="push_slow", music=[("w68", "sting_soft")])
# ================================================================== 21-23. Ratna
beat(21, 0, K4, "side", [dict(SARI_K4, at=[0.15, 0.7, 0], rot=180)], move="static", fx=[["flicker", 0.0, 1.6], ["black", 1.6, 99]],
     sfx=[(0.2, "torch_click"), (1.4, "torch_click")])
beat(21, 5, K4, "corner", move="static", fx=[["black", 0, 99]], sfx=[(0, "breath_sob")], music=[(0, "drone_low")])
beat(21, 27, K4, "corner", [RATNA_K4], move="push_slow", fx=[["fadein", 0, 2.5]], set_over=dict(exposure=1.2))
beat(21, 42, K4, on("ratna", "medium", side=0.3), [RATNA_K4], set_over=dict(exposure=1.2))
beat(21, 56, K4, on("ratna", "close", side=0.6, up=-0.25), [RATNA_K4], move="push", set_over=dict(exposure=1.2))
SARI_DARK = A("sari_p", (0.15, 0.7, 0), 210, "takut", pose="nervous")
RATNA_UP = dict(RATNA_K4, pose="sit", look="sari_p")
beat(22, 0, K4, on("sari_p", "close", side=0.25), [dict(SARI_DARK, talk=[["w0", "e0"]])], set_over=dict(exposure=1.2))
beat(22, 3, K4, on("ratna", "close", side=0.3), [dict(RATNA_K4, keys=[("w5", "pose", "sit")])], move="push", set_over=dict(exposure=1.2))
beat(22, 10, K4, on("ratna", "xclose", side=0.25), [dict(RATNA_UP, expr="nangis")], move="push_slow", set_over=dict(exposure=1.2))
beat(22, 19, K4, on("ratna", "close", side=0.3), [dict(RATNA_UP, talk=[["w19", "e36"]])], set_over=dict(exposure=1.2))
beat(22, 37, K4, on("sari_p", "close", side=0.25), [dict(SARI_DARK, talk=[["w37", "e39"]])], set_over=dict(exposure=1.2))
beat(22, 40, K4, on("ratna", "close", side=0.3), [dict(RATNA_UP, expr="teriak", talk=[["w44", "e47"]], jitter=[0, 99])], move="push",
     set_over=dict(exposure=1.2))
beat(23, 0, K4, "wall", move="shake", sfx=[(0, "knock_heavy")], music=[(0, "sting")], fx=[["flash", 0, 0.12]], set_over=dict(exposure=1.2))
beat(23, 10, K4, "low", move="push", set_over=dict(exposure=1.2))
beat(23, 20, K4, "wall", move="shake", sfx=[(0, "knock_heavy"), ("w21", "knock_heavy")], fx=[["flash", 0, 0.1], ["flash", "w21", 0.1]],
     set_over=dict(exposure=1.2))
beat(23, 22, K4, on("ratna", "close", side=0.3), [dict(RATNA_UP, pose="ears", expr="teriak", jitter=[0, 99])], move="shake",
     fx=[["glitch", "w27", 99]], sfx=[(0, "scream_girl")], set_over=dict(exposure=1.2))
beat(23, 38, K4, on("ratna", "xclose", side=0.25), [dict(RATNA_UP, pose="ears", expr="teriak", jitter=[0, 99], talk=[["w38", "e46"]])],
     fx=[["glitch", 0, 99]], set_over=dict(exposure=1.2))
beat(23, 47, K4, "corner", move="static", fx=[["glitch", 0, 0.6]], set_over=dict(exposure=1.2), music=[(0, "chase")])
# ================================================================== 24-29. the run, the voices
RUN = dict(walk_style="run", prop="torch", pose="torch")
beat(24, 0, BANG, "back", [A("sari_p", (0.0, 10.0, 0), 0, "takut", walk=[[0, 99]], keys=[(0, "move", [0.0, 10.0, 0, 0]), (2.2, "move", [0.0, 8.0, 0, 0])], **RUN)],
     move="shake", sfx=[(0, "run")])
beat(24, 2, BANG, "entry", move="dolly_zoom", sfx=[(0, "run")])
beat(24, 12, BANG, on("sari_p", "close", side=0.3), [A("sari_p", "mid", 0, "takut", walk=[[0, 99]], **RUN)], move="shake")
beat(24, 27, BANG, "beds", move="pan_l", sfx=[(0.2, "knock"), (0.6, "knock"), (1.0, "knock")])
beat(24, 45, BANG, "back", [A("sari_p", (0.0, 8.0, 0), 0, "takut", walk=[[0, 99]], keys=[(0, "move", [0.0, 8.0, 0, 0]), (5.0, "move", [0.0, 5.0, 0, 0])], **RUN)],
     move="shake", sfx=[("w45", "knock"), ("w46", "knock"), ("w47", "knock")])
FAKE = A("darto", "door_out", 180, "netral", prop="torch", pose="torch", noshadow=True, blink=False)
beat(25, 0, BANG, "back", [FAKE, A("sari_p", (0.0, 5.0, 0), 0, "takut")], move="push_slow", music=[(0, "drone_low")])
beat(25, 3, BANG, "door", [dict(FAKE, talk=[["w3", "e3"], ["w12", "e16"]])], move="push_slow")
beat(25, 17, BANG, on("sari_p", "close", side=0.3), [A("sari_p", (0.0, 5.0, 0), 0, "takut", talk=[["w20", "e22"]])])
beat(25, 23, BANG, "feet", [FAKE], move="push", music=[("w39", "sting")])
beat(25, 46, BANG, on("sari_p", "close", side=0.3), [A("sari_p", (0.0, 5.0, 0), 0, "takut", pose="mouth")], move="push")
beat(25, 50, BANG, "beds", [A("sari_p", (0.0, 5.0, 0), 90, "takut", walk=[[0, 99]], keys=[(0, "move", [0.0, 5.0, 0, 90]), (2.5, "move", [-1.4, 5.6, 0, 90])])],
     move="static")
beat(26, 0, BANG, "beds", [A("sari_p", (-1.4, 5.6, 0), 60, "takut", pose="mouth")], move="drift", sfx=[(0, "whisper_far")])
beat(26, 15, BANG, on("sari_p", "xclose", side=0.25), [A("sari_p", (-1.4, 5.6, 0), 60, "nangis", pose="mouth")], move="push_slow")
beat(26, 23, BANG, "back", move="push_slow", set_over=dict(exposure=1.4))
beat(26, 30, BANG, "back", move="static", fx=[["black", 0, "w31"]], music=[("w30", "nduk")])
beat(26, 31, BANG, on("sari_p", "xclose", side=0.2), [A("sari_p", (-1.4, 5.6, 0), 60, "nangis", blink=False)], move="push_slow")
beat(27, 0, BANG, "mid_drift" if False else "beds", [A("sari_p", (-1.4, 5.6, 0), 60, "nangis")], move="drift")
beat(27, 16, BANG, on("sari_p", "medium", side=0.3), [A("sari_p", (-1.4, 5.6, 0), 60, "nangis", pose="kneel", keys=[(0, "move", [-1.4, 5.6, 0, 60]), (0.6, "move", [-1.4, 5.6, -0.32, 60])])],
     sfx=[(0.5, "fall")])
beat(27, 27, BANG, on("sari_p", "close", side=0.3), [A("sari_p", (-1.4, 5.6, -0.32), 60, "nangis", pose="kneel")], move="push_slow")
SARI_KN = A("sari_p", (-1.4, 5.6, -0.32), 60, "nangis", pose="kneel", blink=False)
beat(28, 0, BANG, on("sari_p", "close", side=0.45, up=0.05), [SARI_KN, A("hantu", (-1.8, 5.85, -0.15), 60)], move="push_slow",
     sfx=[(0, "breath_close")], music=[("w17", "sting")])
beat(28, 19, BANG, on("sari_p", "xclose", side=0.2), [dict(SARI_KN, expr="marah")], move="push")
beat(28, 24, BANG, on("sari_p", "medium", side=0.5), [SARI_KN, A("ratna", (-1.75, 5.25, 0), 30, "takut", pose="give")], music=[(0, "hope")])
beat(28, 37, BANG, on("ratna", "close", side=0.3), [SARI_KN, A("ratna", (-1.75, 5.25, 0), 30, "takut", pose="give")])
beat(29, 0, BANG, "back", [A("ratna", (-0.3, 5.0, 0), 0, "takut", walk=[[0, 99]], walk_style="run", keys=[(0, "move", [-0.3, 5.0, 0, 0]), (4.0, "move", [-0.3, 1.2, 0, 0])]),
                          A("sari_p", (0.3, 5.4, 0), 0, "takut", walk=[[0, 99]], walk_style="run", keys=[(0, "move", [0.3, 5.4, 0, 0]), (4.0, "move", [0.3, 1.6, 0, 0])])],
     move="shake", sfx=[(0, "run")], music=[(0, "chase")])
beat(29, 16, BANG, "door", [A("darto", "door_out", 180, "takut", prop="torch", pose="torch", jitter=[0, 99])], move="push")
beat(29, 33, LOR_SLAM, "end", [A("sari_p", (0.2, 22.6, -0.32), 0, "nangis", pose="kneel"), A("darto", (-0.6, 23.0, 0), 160, "takut", pose="give")],
     dyn=[dict(obj="l_bmR_hinge", prop="rotz", keys=[(0, -70), ("w42", -70), ("e42", 0)])], move="static", sfx=[("e42", "slam")])
beat(29, 46, LOR_SLAM, "long", move="shake", sfx=[(0, "scream_inhuman")], music=[(0, "sting")])
beat(29, 60, LOR_SLAM, "side", move="shake", sfx=[(0, "screams_many")])
beat(29, 75, LOR_SLAM, "long", move="static", music=[(0, "silence")], fx=[["dark", 0, 0.3]])
# ================================================================== 30-32. morning, the wall, the grave
beat(30, 0, JAGA, "wide", [A("sari_p", (-0.4, 0.2, 0), 58, "capek", talk=[["w5", "e12"]]), A("wiwik", (0.4, -0.3, 0), 238, "cemas")],
     music=[(0, "sad")], set_over=dict(exposure=0.9))
beat(30, 13, JAGA, on("wiwik", "close", side=-0.2), [A("wiwik", (0.4, -0.3, 0), 238, "nangis")], set_over=dict(exposure=0.9))
beat(30, 18, JAGA, on("wiwik", "close", side=-0.25), [A("wiwik", (0.4, -0.3, 0), 238, "nangis", talk=[["w18", "e20"], ["w22", "e34"]])],
     move="push_slow", set_over=dict(exposure=0.9))
beat(30, 35, EXT_DAY, "facade", move="push_slow", sfx=[(0, "birds")])
beat(30, 45, K4, "side", [A("wiwik", "watch_l", None, "cemas"), A("sari_p", "watch_r", None, "cemas")], sfx=[(0, "hammer")],
     set_over=dict(exposure=0.8))
beat(31, 0, K4B, "wall", move="push_slow", sfx=[(0, "rubble")])
beat(31, 12, K4B, "wall", move="push", music=[("w14", "sting_soft")])
beat(31, 21, K4B, [[0.25, 2.35, 1.75], [0.0, 3.05, 1.85], 40], move="push_slow")
beat(31, 32, K4B, on("wiwik", "close", side=0.3), [A("wiwik", "watch_l", None, "nangis"), A("sari_p", "watch_r", None, "cemas")])
beat(31, 44, MAK, "wide", [A("wiwik", "wiwik", None, "nangis"), A("sari_p", "sari", None, "capek"), A("harun", "harun", None, "capek")],
     sfx=[(0, "birds")])
beat(31, 52, MAK, "stone", move="push_slow")
beat(32, 0, LOR_WELD, "door", move="push_slow", sfx=[(0, "weld")])
beat(32, 9, HAR, "back", [dict(HARUN, expr="senyum"), A("sari_p", "sari_bed", None, "senyum")], set_over=dict(exposure=0.9))
beat(32, 13, HAR, on("harun", "close", side=0.5), [dict(HARUN, expr="senyum", talk=[["w21", "e26"]])], move="push_slow", set_over=dict(exposure=0.9))
beat(32, 27, LOR_DAYL, "long", move="push_slow", sfx=[(0, "birds")])
# ================================================================== 33-36. the boarding house
beat(33, 0, EXT_DAY, "road", move="pull", music=[(0, "calm")])
beat(33, 5, KOS, "wide", [A("sari_p", "sit", None, "capek", pose="sitlap")], set_over=dict(exposure=1.1))
beat(33, 18, KOS, "wide", [SARI_KOS_LIE], move="push_slow", sfx=[(0, "night_room")])
beat(33, 26, KOS, "close", [dict(SARI_KOS_LIE, keys=[("w28", "expr", "cemas")])], move="push_slow", music=[(0, "drone_low")])
beat(33, 36, KOS, [[0.1, 1.45, 0.8], [0.1, 1.65, 0.556], 40], extras=[dict(kind="phone_table", at=[0.1, 1.65, 0.556], text=["02:16", "Kamis"])],
     move="push_slow")
beat(33, 47, KOS17, [[0.1, 1.45, 0.8], [0.1, 1.65, 0.556], 40], extras=[dict(kind="phone_table", at=[0.1, 1.65, 0.556], text=["02:17", "Kamis"])],
     move="push", music=[("w54", "sting_soft")])
beat(34, 0, KOS17, "wall", move="push_slow")
beat(34, 15, KOS17, "wall", move="static", sfx=[("w15", "knock")], music=[("w15", "sting")])
beat(34, 16, KOS17, "close", [dict(SARI_KOS_LIE, expr="takut", blink=False)], move="push")
beat(34, 18, KOS17, "wall", move="push_slow", sfx=[("w18", "knock"), ("w19", "knock")])
beat(34, 25, KOS17, "top", [dict(SARI_KOS_LIE, expr="takut")], move="push_slow", sfx=[(0, "whisper_far")])
beat(35, 0, KOS17, "wall", move="push_slow", music=[(0, "nduk")])
beat(35, 13, KOS17, "close", [dict(SARI_KOS_LIE, expr="nangis")], move="push_slow")
beat(35, 23, KOS17, on("sari_p", "close", side=0.3), [dict(SARI_KOS_SIT, pose="mouth", expr="nangis")], move="push", sfx=[(0, "rain")])
beat(35, 35, KOS17, "wide", [dict(SARI_KOS_SIT, pose="hug", expr="takut")], move="static",
     sfx=[(0.3, "knock"), (0.8, "knock"), (1.3, "knock"), (3.5, "knock"), (4.0, "knock"), (4.5, "knock")], fx=[["timelapse", 0, 99]])
beat(35, 41, KOS, "wide", [dict(SARI_KOS_SIT, pose="hug", expr="capek")], move="push_slow",
     sfx=[(0.3, "knock"), (0.8, "knock"), (1.3, "knock")])
beat(36, 0, KOS17, on("sari_p", "xclose", side=0.25), [dict(SARI_KOS_SIT, pose="hug", expr="capek")], move="push_slow")
beat(36, 12, KOS17, "wall", move="push_slow")
beat(36, 24, KOS17, on("sari_p", "xclose", side=0.2), [dict(SARI_KOS_SIT, pose="hug", expr="capek", keys=[("w26", "expr", "tidur")])],
     move="push_slow")
beat(36, 28, KOS17, "wall", move="static", fx=[["black", 0.0, 99]], sfx=[("w28", "knock"), ("w29", "knock"), ("w30", "knock")],
     music=[("w28", "end")], end=True)


# ------------------------------------------------------------------ resolve times
def wtime(seg, w):
    return SEGW[seg][w]["start"]


def wend(seg, w):
    return SEGW[seg][w]["end"]


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
            c["walk"] = [[rel(a), min(rel(z), round(t1 - t0, 3))] for a, z in c["walk"]]
        if c.get("talk"):
            c["talk"] = [[rel(a), rel(z)] for a, z in c["talk"]]
        if c.get("jitter"):
            c["jitter"] = [rel(c["jitter"][0]), min(rel(c["jitter"][1]), round(t1 - t0, 3))]
        if "at_z" in c:
            c["z"] = c.pop("at_z")
        cast.append(c)
    dyn = []
    for d in b.get("dyn", []):
        d = dict(d); d["keys"] = [[rel(k[0]), k[1]] for k in d["keys"]]
        dyn.append(d)
    st = dict(b["set"]); st.update(b.get("set_over", {}))
    cam = b["cam"]
    fx = [[f[0], rel(f[1]), rel(f[2]) if f[0] != "dark" and f[0] != "flash" else f[2]] for f in b.get("fx", [])]
    shots.append(dict(id=i + 1, seg=b["seg"], w=b["w"], t0=t0, t1=round(t1, 3), set=st, cam=cam, cast=cast, dyn=dyn,
                      extras=b.get("extras", []), move=b["move"], sfx=[[rel(t), n] for t, n in b.get("sfx", [])],
                      music=[[rel(t), n] for t, n in b.get("music", [])], fx=fx,
                      title=b.get("title", False), end=b.get("end", False),
                      text=" ".join(w["w"] for w in WORDS if t0 <= w["start"] < t1)))
json.dump(dict(fps=12, size=[960, 540], out_size=[1920, 1080], duration=END, shots=shots), open("plan_bm.json", "w"), indent=1,
          ensure_ascii=False)
print(len(shots), "shots,", sum(round((s["t1"] - s["t0"]) * 12) for s in shots), "frames @12fps")
