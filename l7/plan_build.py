"""Writes plan.json: every shot of "Lantai Tujuh Tidak Pernah Kosong", timed to audio/words.json.
Beat = (segment, first word index, spec). A shot runs from its beat to the next beat.
Times inside a spec: seconds from the shot start, or "wN" = word N of the same segment.
"""
import json
import re

WORDS = json.load(open("audio/words.json"))
CUTS = {c["seg"]: c for c in json.load(open("audio/vo_cuts.json"))}
SEGW = {}
for w in WORDS:
    SEGW.setdefault(w["seg"], []).append(w)
END = 721.55 + 2.0

# ------------------------------------------------------------------ sets (with exposure)
U_DAY = dict(name="unit", night=False, lights_on=True, exposure=0.9)
U_NIGHT = dict(name="unit", night=True, lights_on=False, exposure=1.6)
U_BED = dict(name="unit", night=True, lights_on=False, bedcover=True, exposure=1.6)
U_NADIA = dict(name="unit", night=False, lights_on=True, exposure=0.9)
C6 = dict(name="corridor", floor="6", exposure=1.2)
C7 = dict(name="corridor", floor="7", dead=[1, 3], exposure=1.5)
STAIRS = dict(name="stairs", floor="4", exposure=1.8)
STAIRS7 = dict(name="stairs", floor="7", exposure=1.8)
LIFT = dict(name="lift", floor="7", exposure=0.8)
LOBBY = dict(name="lobby", exposure=0.6)
EXT = dict(name="exterior", twin=False, night=True, lit=0, exposure=2.0)
EXT_DAY = dict(name="exterior", twin=False, night=False, lit=0, exposure=0.35)
TWIN = dict(name="exterior", twin=True, night=True, lit=0, exposure=2.0)
BED = dict(name="bedroom", variant="sari", clock="03:00", nophone=True, exposure=1.8)
BATH = dict(name="bathroom", exposure=1.0)
PARK = dict(name="parking", exposure=0.6)

# ------------------------------------------------------------------ cameras
CAM = {
    "unit_wide": ((0.3, -4.25, 1.75), (0.4, 0.6, 0.85), 22),
    "unit_desk": ((-0.9, -1.9, 1.25), (1.2, 0.4, 0.95), 35),
    "unit_ceil": ((0.0, -1.3, 1.0), (0.05, -0.7, 2.7), 20),
    "unit_door": ((1.6, -2.4, 1.3), (-2.5, -0.9, 1.0), 30),
    "unit_corner": ((-1.2, -1.2, 1.2), (1.9, -3.9, 0.6), 32),
    "unit_floor": ((0.5, -3.3, 1.7), (-0.8, -1.5, 0.25), 32),
    "unit_bedtop": ((-0.6, -2.3, 2.25), (-0.86, -1.4, 0.3), 30),
    "unit_doorout": ((-3.6, -2.3, 1.3), (-2.4, -0.4, 1.1), 26),
    "c_long": ((0.35, -1.5, 1.25), (-0.2, 18.0, 1.0), 28),
    "c_lift": ((-0.7, 2.6, 1.2), (1.0, -0.6, 1.1), 35),
    "c_end": ((0.5, 11.5, 1.3), (-1.0, 17.0, 1.0), 40),
    "c_back": ((0.0, 17.3, 1.5), (0.0, 0.0, 0.9), 30),
    "c_door": ((0.7, 14.2, 1.2), (-1.1, 16.5, 1.1), 35),
    "c_tube": ((0.3, 11.2, 1.9), (0.0, 13.0, 2.58), 30),
    "s_up": ((0.75, -2.7, 1.1), (0.0, 2.2, 2.5), 24),
    "s_down": ((-0.2, 2.75, 3.23), (0.6, -1.0, 0.6), 24),
    "s_land": ((0.9, 1.0, 2.7), (-0.4, 2.5, 2.3), 30),
    "s_meet": ((0.35, 0.15, 3.03), (-0.15, 2.3, 2.2), 26),
    "lift_in": ((0.25, -0.72, 1.3), (-0.05, 2.4, 1.05), 24),
    "lift_ghost": ((0.1, 0.3, 1.45), (0.05, 2.05, 1.3), 40),
    "lobby_wide": ((-0.2, -3.4, 1.5), (0.4, 3.0, 1.0), 24),
    "lobby_group": ((-1.2, -1.4, 1.25), (1.3, 1.8, 0.95), 35),
    "lobby_two": ((0.6, -0.6, 1.25), (1.6, 1.3, 1.05), 40),
    "ext_wide": ((3.5, -34, 2.0), (0, 30, 20), 24),
    "ext_low": ((-1, -4, 0.9), (0, 30, 22), 20),
    "ext_street": ((-1.5, 1.5, 1.0), (-5.5, 9.0, 0.9), 30),
    "ext_facade": ((2.5, 6.0, 1.6), (0, 22, 14), 24),
    "ext_top": ((2, -18, 1.5), (0, 30, 70), 28),
    "twin": ((4, -52, 2.4), (5, 36, 22), 26),
    "twin_b": ((10, -10, 2.0), (19, 33, 10), 30),
    "twin_a": ((-4, -10, 2.0), (-9, 23, 12), 30),
    "bed": ((0.5, -0.4, 1.1), (-0.9, 1.2, 0.7), 40),
    "bed_sit": ((0.9, -1.0, 1.3), (-0.8, 1.0, 0.95), 35),
    "bed_phone": ((0.12, 1.35, 0.8), (0.1, 1.65, 0.56), 40),
    "bath_door": ((0.05, -1.05, 1.45), (-0.1, 0.8, 1.05), 24),
    "bath_up": ((0.55, -0.6, 0.55), (-0.1, 0.3, 1.6), 22),
    "bath_ceil": ((0.05, -0.3, 1.25), (0.15, 0.3, 2.4), 24),
    "park_wide": ((-2.6, -3.0, 1.5), (0.4, 1.0, 0.7), 28),
    "park_close": ((1.6, -0.6, 1.25), (0.3, 0.9, 1.05), 40),
    "park_lamp": ((0.55, -0.9, 0.95), (0.6, 0.3, 0.95), 35),
}


def on(who, kind="close", **k):
    d = dict(on=who, kind=kind); d.update(k)
    return d


def A(who, at, rot=0, expr=None, pose="idle", keys=(), **k):
    d = dict(who=who, at=list(at), rot=rot, pose=pose, keys=[list(x) for x in keys])
    if expr:
        d["expr"] = expr
    d.update(k)
    return d


# stairs step helper: flight A (right side, x=0.65) goes up toward +Y
def stepA(i, x=0.65):
    return [x, -1.2 + i * 0.27, 0.165 * (i + 1) if i >= 0 else 0.0]


TOP = 0.165 * 9
UNIT7 = [-0.35, 17.05 - 0.6, 0]      # standing in front of the unit door at the corridor end

# lobby group (7 people)
LOBBY_CAST = [A("sari", (2.0, 1.2, 0), -30, "cemas"), A("bagas", (1.35, 1.35, 0), 10, "cemas"),
              A("hendra", (-0.6, 1.8, 0), 10, "netral"), A("wulan", (0.2, 2.2, 0), -10, "netral"),
              A("nadia", (-1.4, 1.5, 0), 20, "netral"), A("fajar", (3.0, 2.2, 0), -20, "netral"),
              A("reza", (0.9, 2.5, 0), 0, "netral")]
UNIT_CAST = [A("hendra", (1.4, -2.7, 0), 20, "senyum", pose="point"), A("sari", (-0.6, -1.6, 0), -10, "netral"),
             A("bagas", (0.6, -0.3, 0), -30, "netral"), A("nadia", (-1.3, -0.4, 0), 10, "netral"),
             A("wulan", (-0.2, 0.4, 0), 0, "senyum"), A("fajar", (-1.9, 0.9, 0), 20, "senyum"),
             A("reza", (0.4, 1.2, 0), -10, "netral")]

B = []


def beat(seg, w, set_, cam, cast=(), move="push", **k):
    d = dict(seg=seg, w=w, set=set_, cam=cam if not isinstance(cam, str) else cam, cast=list(cast), move=move)
    d.update(k)
    B.append(d)


S = "sfx"
# ================================================================== 1-4: arrival
beat(1, 0, EXT, "ext_low", move="push_slow", title=True, sfx=[(0, "drone"), (0, "rain")])
beat(2, 0, EXT_DAY, "ext_street", move="pan_r", sfx=[(0, "rain")])
beat(2, 4, EXT_DAY, "ext_street", move="push")
beat(2, 13, LOBBY, "lobby_wide", LOBBY_CAST, move="push_slow")
beat(2, 23, C6, "c_long", move="push_slow", sfx=[(0, "drone")])
beat(2, 30, U_DAY, "unit_wide", UNIT_CAST, move="push_slow", focus="hendra")
# 3: the seven, one by one
beat(3, 0, LOBBY, "lobby_group", LOBBY_CAST, move="push_slow")
for i, n in enumerate(["hendra", "bagas", "reza", "fajar", "nadia", "wulan", "sari"]):
    beat(3, 3 + i, LOBBY, on(n, "close", side=0.15), LOBBY_CAST, move="push_slow" if n != "sari" else "push")
beat(4, 0, EXT, "ext_wide", move="push_slow", sfx=[(0, "drone")])
beat(4, 6, EXT, "ext_low", move="push")
beat(4, 9, EXT, "ext_facade", move="pan_u")
beat(4, 18, EXT, "ext_top", move="pan_u")
beat(4, 27, EXT, "ext_wide", move="pull", sfx=[("w30", "riser")])
# ================================================================== 5-10: lobby, the whisper
beat(5, 0, LOBBY, "lobby_wide",
     [A(n["who"], n["at"], n["rot"], "cemas", keys=[(0, "move", [n["at"][0], n["at"][1] - 2.5, 0, n["rot"]]),
                                                       ("w5", "move", [n["at"][0], n["at"][1], 0, n["rot"]])],
        walk=[[0, "w5"]], hold=0.2) for n in LOBBY_CAST], move="push_slow", sfx=[(0, "steps")])
SB = [A("sari", (2.0, 1.2, 0), 60, "cemas"), A("bagas", (1.35, 1.25, 0), -20, "cemas", nolook=True)]
beat(6, 0, LOBBY, "lobby_two", SB + LOBBY_CAST[2:], move="push_slow")
beat(7, 0, LOBBY, on("sari", "close", side=-0.2), [dict(SB[0], talk=[(7, 0, None)]), SB[1]], move="push")
beat(8, 0, LOBBY, on("bagas", "close", side=0.2), SB, move="push_slow")
beat(9, 0, LOBBY, on("bagas", "xclose", side=0.1), [SB[0], A("bagas", (1.35, 1.25, 0), -20, "takut", nolook=True, talk=[(9, 0, None)])], move="push",
     sfx=[(0, "drone")])
beat(10, 0, LOBBY, "lobby_two", [SB[0], A("bagas", (1.35, 1.25, 0), -20, "cemas", pose="shush")], move="push_slow")
beat(10, 7, LOBBY, on("sari", "close", side=-0.2), [A("sari", (2.0, 1.2, 0), 60, "takut")], move="push")
beat(10, 10, LOBBY, on("sari", "xclose", side=-0.15), [A("sari", (2.0, 1.2, 0), 60, "capek")], move="push_slow")
# ================================================================== 11: the office on six
beat(11, 0, C6, "c_long", [A(n, (x, 3.0 + dy, 0), 180, "netral", keys=[(0, "move", [x, 3.0 + dy, 0, 180]), (6.5, "move", [x, 9.0 + dy, 0, 180])],
                             walk=[[0, 6.5]]) for n, x, dy in (("sari", -0.35, 0), ("bagas", 0.35, 0), ("nadia", 0.0, -0.8))], move="push_slow",
     sfx=[(0, "steps")])
beat(11, 9, U_DAY, "unit_wide", move="pan_r")
beat(11, 19, U_DAY, "unit_desk", move="push_slow")
beat(11, 27, C6, "c_back", move="push_slow", sfx=[(0, "drone")])
beat(11, 34, C6, "c_long", [A("hantu", (0.0, 15.5, 0), 0)], move="push", sfx=[("w39", "whoosh")])
# ================================================================== 12-16: night one
beat(12, 0, U_NIGHT, "unit_desk", [A("sari", (0.75, -0.2, 0), -90, "capek", pose="papers")], move="push_slow",
     sfx=[(0, "drone"), (0, "rain")])
beat(12, 4, U_NIGHT, on("sari", "close", side=0.25), [A("sari", (0.75, -0.2, 0), -90, "capek", pose="phone", prop="phone")],
     move="push_slow")
beat(12, 11, U_NIGHT, "unit_wide", [A("sari", (0.75, -0.2, 0), -90, "capek", keys=[(0.3, "pose", "stretch"), (2.6, "pose", "idle")])],
     move="push_slow")
beat(13, 0, U_BED, "unit_floor", [A("sari", (-0.5, -1.6, 0), 60, "capek", keys=[(1.0, "pose", "nervous")])], move="push_slow")
beat(13, 6, U_BED, "unit_bedtop", [A("sari", (0, 0, 0), 0, "tidur", lie=[-0.86, -2.35, 0.30, 0], keys=[("w10", "expr", "takut")])],
     move="push", sfx=[("w9", "heartbeat")])
LIE = [A("sari", (0, 0, 0), 0, "takut", lie=[-0.86, -2.35, 0.30, 0])]
beat(14, 0, U_BED, on("sari", "xclose", side=0.0, up=0.3), LIE, move="push_slow")
beat(14, 5, U_BED, "unit_ceil", move="push_slow", sfx=[("w15", "drag")])
beat(14, 17, U_BED, "unit_ceil", move="shake", sfx=[(0, "drag")])
beat(14, 18, U_BED, on("sari", "xclose", side=0.0, up=0.3), LIE, move="shake", sfx=[(0, "drag")])
beat(14, 19, U_BED, "unit_ceil", move="shake", sfx=[(0, "drag")])
beat(14, 20, U_BED, on("sari", "xclose", side=0.0, up=0.3), LIE, move="push_slow")
beat(14, 21, U_BED, "unit_ceil", move="push_slow", sfx=[("w22", "drag")])
beat(15, 0, BATH, "bath_door", [A("sari", (0.0, -1.0, 0), 180, "cemas", keys=[(0, "move", [0.0, -1.0, 0, 180]),
                                                                              (1.6, "move", [-0.1, 0.1, 0, 180]), (2.2, "move", [-0.1, 0.1, 0, 0])],
                                  walk=[[0, 1.6]])], move="push_slow", sfx=[(0, "drag")])
beat(15, 10, BATH, "bath_up", [A("sari", (-0.1, 0.1, 0), 0, "takut", pose="lookup")], move="push", sfx=[(0, "drag")])
beat(15, 14, BATH, on("sari", "close", side=0.2), [A("sari", (-0.1, 0.1, 0), 0, "cemas", keys=[("w18", "expr", "senyum")])],
     move="push_slow")
beat(16, 0, C7, "c_long", move="push_slow", sfx=[(0, "riser")])
# ================================================================== 17: morning, Bagas looks away
SB2 = [A("sari", (0.75, -0.6, 0), -60, "senyum", talk=[(17, 3, 14)]), A("bagas", (0.75, 0.3, 0), -15, "netral")]
beat(17, 0, U_DAY, "unit_desk", SB2, move="push_slow")
beat(17, 9, U_DAY, on("sari", "close", side=-0.2), SB2, move="push_slow")
beat(17, 15, U_DAY, on("bagas", "close", side=0.2),
     [A("sari", (0.75, -0.6, 0), -60, "senyum"),
      A("bagas", (0.75, 0.3, 0), -15, "cemas", nolook=True, keep_rot=True,
        keys=[("w20", "move", [0.75, 0.3, 0, -15]), ("w21", "move", [0.75, 0.3, 0, 100])])],
     move="push_slow")
beat(17, 22, U_DAY, "unit_desk", [A("sari", (0.75, -0.6, 0), -60, "netral"), A("bagas", (0.75, 0.3, 0), 100, "cemas", nolook=True, keep_rot=True)],
     move="push_slow")
# ================================================================== 18-25: night two (Sari at home, Reza stuck in the unit)
SARI_BED = A("sari", (0, 0, 0), 0, "tidur", lie=[-0.9, -0.15, 0.71, 0])
beat(18, 0, BED, "bed", [SARI_BED], move="push_slow",
     extras=[dict(kind="phone_table", at=[0.1, 1.65, 0.556], text=["8 panggilan", "tak terjawab", "Reza"])], sfx=[(0, "buzz")])
beat(18, 8, BED, "bed_phone", [], move="push",
     extras=[dict(kind="phone_table", at=[0.1, 1.65, 0.556], text=["8 panggilan", "tak terjawab", "Reza"])], sfx=[(0, "buzz")])
REZA_N = dict(at=(-0.4, -1.6, 0), rot=10)
beat(19, 0, U_NIGHT, on("reza", "close", side=0.2), [A("reza", REZA_N["at"], REZA_N["rot"], "takut", pose="phone", prop="phone", talk=[(19, 0, None)])],
     move="push", sfx=[(0, "heartbeat")])
SARI_SIT = A("sari", (-0.9, 0.95, 0.12), 40, "cemas", pose="phone", prop="phone")
beat(20, 0, BED, "bed_sit", [SARI_SIT], move="push_slow")
beat(20, 10, U_NIGHT, "unit_wide", [A("reza", REZA_N["at"], REZA_N["rot"], "takut", pose="phone", prop="phone", talk=[(20, 10, None)])], move="push_slow")
beat(21, 0, U_NIGHT, on("reza", "close", side=-0.2), [A("reza", REZA_N["at"], REZA_N["rot"], "takut", pose="phone", prop="phone",
                                                         look=[-0.4, -1.4, 2.7], talk=[(21, 0, None)])], move="push")
beat(22, 0, BED, on("sari", "close", side=-0.25), [dict(SARI_SIT, expr="takut")], move="push")
beat(22, 3, C7, "c_long", move="push_slow", sfx=[(0, "drone")])
beat(22, 16, BED, on("sari", "xclose", side=-0.2), [SARI_SIT], move="push_slow")
beat(23, 0, BED, on("sari", "close", side=-0.25), [dict(SARI_SIT, talk=[(23, 0, None)])], move="push_slow")
beat(24, 0, U_NIGHT, on("reza", "close", side=0.25), [A("reza", REZA_N["at"], REZA_N["rot"], "takut", pose="phone", prop="phone",
                                                        look=[-0.4, -1.4, 2.7], talk=[(24, 0, None)])], move="push_slow", sfx=[(0, "drag")])
beat(24, 9, U_NIGHT, "unit_corner", [A("reza", (1.6, -3.1, -0.33), 200, "takut", pose="sitphone", prop="phone", talk=[(24, 0, None)])],
     move="push_slow")
beat(25, 0, BED, "bed_sit", [dict(SARI_SIT, expr="capek", talk=[(25, 0, 6)])], move="push_slow", set_over=dict(clock="03:30"))
beat(25, 7, U_NIGHT, on("reza", "close", side=0.2), [A("reza", REZA_N["at"], REZA_N["rot"], "capek", pose="phone", prop="phone",
                                                       talk=[(25, 7, None)])],
     move="push_slow")
# ================================================================== 26-29: day three
beat(26, 0, PARK, "park_wide", [A("reza", (-0.15, 0.85, 0), -80, "netral")], move="push_slow",
     dyn=[dict(obj="mb_head", prop="emit", keys=[(0, 0.0), ("w4", 6.0)])], sfx=[("w4", "engine")])
beat(26, 6, PARK, on("reza", "close", side=0.2), [A("reza", (-0.15, 0.85, 0), -80, "takut", pose="pocket")], move="push")
beat(26, 10, PARK, "park_lamp", [A("reza", (-0.15, 0.85, 0), -80, "takut", keys=[("w15", "move", [-0.15, 0.85, 0, -80]),
                                                                                ("w18", "move", [-0.55, 0.6, 0, -80])], walk=[["w15", "w18"]])],
     move="push", dyn=[dict(obj="mb_head", prop="emit", keys=[(0, 6.0)])], sfx=[(0, "engine")])
beat(27, 0, C7, "c_long", [A("reza", (-0.3, 4.0, 0), 180, "netral", keys=[(0, "move", [-0.3, 4.0, 0, 180]), (4.5, "move", [-0.3, 9.0, 0, 180])],
                             walk=[[0, 4.5]]),
                           A("bagas", (0.3, 3.6, 0), 180, "cemas", keys=[(0, "move", [0.3, 3.6, 0, 180]), (4.5, "move", [0.3, 8.6, 0, 180])],
                             walk=[[0, 4.5]])], move="push_slow", sfx=[(0, "steps")])
beat(27, 11, C7, "c_end", move="push_slow", sfx=[(0, "drone")])
beat(27, 21, U_DAY, "unit_wide", [A("bagas", (-1.9, -0.5, 0), 90, "capek", keys=[(0, "move", [-1.9, -0.5, 0, 90]), (2.5, "move", [-0.6, -1.2, 0, 20])],
                                    walk=[[0, 2.5]]), A("sari", (0.4, -2.3, 0), -40, "cemas")], move="push_slow")
beat(27, 33, U_DAY, on("sari", "close", side=-0.2), [A("sari", (0.4, -2.3, 0), 60, "cemas", talk=[(27, 33, 34)]), A("bagas", (-0.6, -1.2, 0), -110, "capek")],
     move="push_slow")
beat(28, 0, U_DAY, on("bagas", "xclose", side=0.15), [A("sari", (0.4, -2.3, 0), 60, "cemas"), A("bagas", (-0.6, -1.2, 0), -110, "takut", talk=[(28, 0, None)])],
     move="push", sfx=[(0, "stinger_soft")])
beat(29, 0, U_DAY, "unit_desk", [A("reza", (0.75, 0.6, 0), -90, "capek", nolook=True), A("bagas", (0.75, -0.3, 0), -90, "capek", nolook=True)],
     move="push_slow")
# ================================================================== 30-36: the lift dies, the stairs, the resident
beat(30, 0, C6, "c_lift", move="shake",
     dyn=[dict(obj="lift_ind", prop="emit", keys=[(0, 4.0), (1.1, 0.0)]), dict(obj="lift_btn", prop="emit", keys=[(0, 3.0), (1.1, 0.0)])],
     sfx=[(1.1, "thud")])
T3 = [("sari", 0.0), ("bagas", 0.35), ("reza", 0.7)]


def down_walk(name, delay, i0=8, i1=2, t=6.0):
    a, b = stepA(i0), stepA(i1)
    return A(name, a, 0, "cemas", keys=[(delay, "move", a + [0]), (delay + t, "move", b + [0])], walk=[[delay, delay + t]])


beat(31, 0, STAIRS, "s_down", [down_walk(n, 0.0, i0, i0 - 4) for n, i0 in (("sari", 4), ("bagas", 6), ("reza", 8))], move="push_slow",
     sfx=[(0, "steps")])
beat(31, 9, STAIRS, "s_up", [A(n, stepA(i), 0, "cemas") for (n, _), i in zip(T3, (3, 5, 7))], move="push_slow")
beat(31, 15, STAIRS, on("sari", "medium", side=0.2), [A(n, stepA(i), 0, "cemas") for (n, _), i in zip(T3, (3, 5, 7))],
     move="push_slow", sfx=[(0, "heartbeat")])
RES = A("penghuni", [-0.65, 1.55 - 0.27, TOP + 0.165 - 0.3], 0, "capek", pose="sit")
T3L = [A("sari", [0.2, 2.9, TOP], -30, "cemas"), A("bagas", [1.0, 2.35, TOP], -55, "cemas"), A("reza", [0.75, 2.85, TOP], -45, "netral")]
beat(32, 0, STAIRS, "s_meet", [RES] + T3L, move="push_slow", focus="penghuni")
beat(32, 7, STAIRS, on("penghuni", "close", side=0.2), [dict(RES, talk=[(32, 20, None)])], move="push_slow")
beat(33, 0, STAIRS, on("penghuni", "close", side=0.25), [dict(RES, talk=[(33, 0, None)])], move="push_slow")
beat(33, 7, C7, "c_door", move="push_slow", sfx=[(0.3, "knock"), (2.0, "knock")])
beat(33, 19, LIFT, "lift_in", move="push_slow", sfx=[(0, "ding")])
KID = dict(who="anak", over=dict(scale=1.0))
beat(33, 30, LIFT, "lift_in", [A("anak", (-0.3, 0.05, 0), 180, "netral", **{"as": "fajar", "over": {"scale": 1.0}})],
     set_over=dict(doors_open=0.0), move="push_slow", sfx=[("w38", "ding")])
beat(33, 42, LIFT, "lift_in", [A("anak", (-0.3, 0.05, 0), 180, "takut", **{"as": "fajar", "over": {"scale": 1.0}})],
     dyn=[dict(obj="l_leaf-1", prop="locx", keys=[(0, -0.22), (1.3, -0.66)]), dict(obj="l_leaf1", prop="locx", keys=[(0, 0.22), (1.3, 0.66)])],
     set_over=dict(doors_open=0.0), move="push_slow", sfx=[(0, "ding")])
beat(33, 44, LIFT, "lift_in", [A("anak", (-0.3, 0.05, 0), 180, "takut", **{"as": "fajar", "over": {"scale": 1.0}}),
                               A("hantu", (0.05, 2.05, 0.06), 0)], move="push", sfx=[(0, "stinger")])
beat(33, 48, LIFT, "lift_ghost", [A("hantu", (0.05, 2.05, 0.06), 0)], move="push")
beat(34, 0, STAIRS, on("penghuni", "xclose", side=0.15), [dict(RES, expr="netral")], move="push")
beat(35, 0, LIFT, "lift_in", [A("anak", (-0.3, 0.05, 0), 180, "nangis", pose="cower", **{"as": "fajar", "over": {"scale": 1.0}})],
     move="push_slow", sfx=[(0, "sob")])
beat(35, 7, STAIRS, on("penghuni", "close", side=0.25), [dict(RES, talk=[(35, 0, None)])], move="push_slow")
beat(35, 18, STAIRS, on("penghuni", "xclose", side=0.1), [dict(RES, look="sari", talk=[(35, 0, None)])] + T3L, move="push", focus="penghuni")


def up_walk(name, delay, i0=1, i1=8, t=3.2):
    a, b = stepA(i0), stepA(i1)
    return A(name, a, 180, "cemas", keys=[(delay, "move", a + [180]), (delay + t, "move", b + [180])], walk=[[delay, delay + t]])


beat(36, 0, STAIRS7, "s_up", [up_walk(n, 0.0, i0, i0 + 4) for n, i0 in (("sari", 4), ("bagas", 2), ("reza", 0))], move="push_slow",
     sfx=[(0, "steps")])
# ================================================================== 37-55: Nadia alone
NADIA_DESK = A("nadia", (0.75, -0.3, 0), -90, "netral", pose="papers", prop="papers")
beat(37, 0, U_NADIA, "unit_wide", [NADIA_DESK], move="push_slow")
beat(38, 0, U_NADIA, on("nadia", "close", side=0.25), [NADIA_DESK], move="push_slow")
beat(38, 14, U_NADIA, "unit_ceil", move="shake", sfx=[("w14", "bang"), ("w15", "bang"), ("w16", "bang")])
beat(38, 17, U_NADIA, on("nadia", "medium", side=0.3), [A("nadia", (0.75, -0.3, 0), -90, "takut", keys=[(k * 0.17, "pose", "shake" if k % 2 else "shake2") for k in range(24)], hold=0.05)],
     move="push_slow", sfx=[(0, "bang"), (1.2, "bang")])
BROOM = A("nadia", (-0.3, -1.4, 0), -10, "marah", prop="broom", hold=0.12,
          keys=[(0.4 + k * 0.42, "pose", "poke2" if k % 2 else "poke") for k in range(8)])
beat(39, 0, U_NADIA, "unit_wide", [dict(BROOM, pose="idle")], move="push_slow", sfx=[(1.0 + k * 0.84, "thud") for k in range(4)])
beat(40, 0, U_NADIA, on("nadia", "close", side=0.2, up=-0.15), [dict(BROOM, keys=[], pose="poke", talk=[(40, 0, None)])], move="shake")
beat(41, 0, U_NADIA, "unit_ceil", move="shake", sfx=[(0, "bang"), (0.6, "bang")])
beat(41, 3, STAIRS7, "s_up", [up_walk("nadia", 0, 1, 8, 3.0)], move="push_slow", sfx=[(0, "heels")])
NADIA_DOOR = A("nadia", UNIT7, 180, "marah")
beat(41, 8, C7, "c_end", [NADIA_DOOR], move="push_slow")
beat(41, 19, C7, "c_door", [dict(NADIA_DOOR, pose="knock", keys=[(k * 0.4, "pose", "knock" if k % 2 == 0 else "idle") for k in range(6)], hold=0.12)],
     move="push_slow", sfx=[("w21", "knock")])
beat(42, 0, C7, "c_long", [dict(NADIA_DOOR, expr="cemas")], move="push_slow", sfx=[(0, "silence")])
beat(42, 5, C7, "c_tube", move="push_slow", sfx=[(0, "flicker")])
beat(42, 15, C7, on("nadia", "close", side=-0.25), [dict(NADIA_DOOR, expr="cemas", rot=200)], move="push_slow")
beat(42, 25, C7, "c_door", move="push_slow", sfx=[(0, "drone")])
beat(43, 0, C7, "c_door", [dict(NADIA_DOOR, keys=[(0.2 + k * 0.35, "pose", "knock" if k % 2 == 0 else "idle") for k in range(8)], hold=0.1)],
     move="shake", sfx=[(0.4, "knock"), (1.6, "knock")])
beat(44, 0, C7, on("nadia", "close", side=0.25), [dict(NADIA_DOOR, rot=200, expr="teriak", talk=[(44, 0, None)])], move="shake")
beat(45, 0, C7, "c_door", [dict(NADIA_DOOR, keys=[("w3", "pose", "kick"), (2.0, "pose", "idle")])], move="shake", sfx=[("w3", "bang")])
beat(45, 6, C7, "c_long", [A("nadia", UNIT7, 0, "marah", keys=[(0, "move", UNIT7 + [0]), (3.5, "move", [0.0, 11.0, 0, 0])], walk=[[0, 3.5]])],
     move="push_slow", sfx=[(0, "heels")])
NADIA_STEP = A("nadia", stepA(7), 0, "cemas")
beat(46, 0, STAIRS7, "s_down", [down_walk("nadia", 0.0, 8, 7, 0.8)], move="push_slow", sfx=[("w8", "creak"), ("w9", "bang_soft")])
beat(46, 10, STAIRS7, on("nadia", "close", side=0.25), [dict(NADIA_STEP, expr="takut")], move="push", sfx=[("w16", "heels")])
beat(47, 0, STAIRS7, on("nadia", "feet", side=0.2), [down_walk("nadia", 0.0, 7, 4, 9.0)], move="push_slow",
     sfx=[("w8", "heel1"), ("w9", "heel1"), ("w10", "heel1")])
beat(47, 11, STAIRS7, on("nadia", "close", side=0.25), [dict(NADIA_STEP, expr="takut", at=stepA(4), pose="walk")], move="push_slow")
beat(48, 0, STAIRS7, "s_down", [A("nadia", stepA(3), 0, "takut", pose="walk"), A("hantu", [0.2, 2.5, TOP], 0)], move="push",
     sfx=[(0, "heels")])
beat(49, 0, STAIRS7, on("nadia", "close", side=0.2), [A("nadia", stepA(2), 0, "takut")], move="push")
beat(49, 6, U_NADIA, "unit_door", [A("nadia", (-2.4, -0.5, 0), 90, "takut", keys=[(0, "move", [-3.0, -0.5, 0, 90]), (1.2, "move", [-1.3, -0.8, 0, 90])],
                                     walk=[[0, 1.2]], walk_style="run")],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80), ("w11", -80), ("w12", 0)])], move="shake", sfx=[("w12", "bang")])
NADIA_SIT = A("nadia", (0.85, -1.2, -0.3), -90, "capek", pose="sit")
beat(50, 0, U_NADIA, "unit_desk", [NADIA_SIT], move="push_slow", sfx=[(0, "breath")])
beat(51, 0, U_NADIA, "unit_door", [], dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, 0), ("w8", -45)])], move="push_slow",
     sfx=[(0, "creak")])
beat(51, 9, U_NADIA, "unit_door", [A("hantu", (-2.2, -0.6, 0), 120, keys=[("w14", "move", [-2.2, -0.6, 0, 120]), ("w19", "move", [1.8, -3.6, 0, 120]),
                                                                          ("w19", "show", 0)])],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -45)])], move="push", sfx=[("w14", "whoosh")])
beat(52, 0, U_NADIA, "unit_corner", move="push_slow", sfx=[(0, "drone")])
beat(53, 0, U_NADIA, on("nadia", "close", side=0.2), [dict(NADIA_SIT, pose="idle", at=(0.85, -1.2, 0), keys=[(0.5, "move", [0.85, -1.2, 0, -90]),
                                                                                                       (1.6, "move", [0.85, -1.2, 0, 30])])],
     move="push_slow")
GHOST_DOOR = A("hantu", (-3.0, -0.5, 0.05), 90)
beat(53, 5, U_NADIA, "unit_door", [A("nadia", (-0.5, -2.5, 0), -125, "teriak", pose="scared"), GHOST_DOOR],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80)])], move="push", sfx=[("w9", "stinger")])
beat(54, 0, U_NADIA, on("hantu", "medium", side=0.1), [GHOST_DOOR], dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80)])], move="push_slow")
beat(54, 3, U_NADIA, on("hantu", "close", side=0.05), [GHOST_DOOR], dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80)])], move="push_slow")
beat(54, 12, U_NADIA, on("hantu", "xclose", side=0.0), [GHOST_DOOR], dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80)])], move="push")
beat(55, 0, U_NADIA, "unit_door", [A("nadia", (-1.9, -0.9, 0), 90, "teriak", keys=[(0, "move", [-1.9, -0.9, 0, 90]), (0.4, "move", [-1.9, -0.9, 0, -60]),
                                                                                  ("w5", "move", [1.6, -3.3, 0, -60])], walk=[[0.4, "w5"]], walk_style="run")],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -80), ("w1", -80), ("w2", 0)])], move="shake", sfx=[("w2", "bang")])
NADIA_CORNER = A("nadia", (1.75, -3.6, -0.33), 200, "nangis", pose="sitphone", prop="phone")
beat(55, 6, U_NADIA, "unit_corner", [NADIA_CORNER], move="push")
# ================================================================== 56-62: they come back up
beat(56, 0, STAIRS7, on("sari", "close", side=0.25), [A("sari", stepA(4), 180, "cemas", pose="phone", prop="phone"),
                                                      A("bagas", stepA(2), 180, "cemas"), A("reza", stepA(0), 180, "netral")], move="push_slow")
beat(56, 10, STAIRS7, on("sari", "xclose", side=0.2), [A("sari", stepA(4), 180, "takut", pose="phone", prop="phone")], move="push_slow",
     sfx=[(0, "static")])
beat(56, 23, U_NADIA, on("nadia", "close", side=-0.2), [dict(NADIA_CORNER, expr="teriak", talk=[(56, 23, None)])], move="shake")
RUN3 = [A(n, (x, 8.0 + d, 0), 180, "takut", keys=[(0, "move", [x, 8.0 + d, 0, 180]), (3.2, "move", [x, 15.4 + d, 0, 180])], walk=[[0, 3.2]],
          walk_style="run") for n, x, d in (("sari", -0.3, 0), ("reza", 0.3, -0.6), ("bagas", 0.0, -1.2))]
beat(57, 0, C6, "c_long", RUN3, move="shake", sfx=[(0, "steps"), ("w8", "sob")],
     dyn=[dict(obj="c_unit_hinge", prop="rotz", keys=[(0, -80)])])
beat(57, 9, U_NADIA, "unit_doorout", dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -95)])], move="push_slow")
NADIA_COWER = A("nadia", (1.75, -3.6, -0.33), 200, "nangis", pose="sitcower")
beat(57, 13, U_NADIA, "unit_corner", [NADIA_COWER], move="push_slow", sfx=[(0, "sob")])
beat(57, 25, U_NADIA, on("nadia", "close", side=0.2), [dict(NADIA_COWER, pose="sitphone", look=(-2.4, -0.5, 1.4))], move="push_slow")
REZA_GUARD = A("reza", (1.1, -2.9, 0), 160, "takut", look=(-2.4, -0.5, 1.4))
beat(57, 32, U_NADIA, "unit_corner", [REZA_GUARD, A("nadia", (1.5, -3.4, 0), 160, "nangis", pose="hide", nolook=True,
                                                    keys=[(0, "move", [1.75, -3.6, -0.2, 200]), (1.2, "move", [1.5, -3.4, 0, 160])])],
     move="push_slow")
beat(58, 0, U_NADIA, on("nadia", "close", side=-0.25), [REZA_GUARD, A("nadia", (1.5, -3.4, 0), 160, "nangis", pose="hide", nolook=True,
                                                                      talk=[(58, 0, None)])], move="push")
SARI_IN = A("sari", (-0.9, -1.6, 0), 60, "takut")
beat(59, 0, U_NADIA, on("sari", "close", side=0.2), [dict(SARI_IN, keys=[(0, "move", [-0.9, -1.6, 0, -40]), (1.2, "move", [-0.9, -1.6, 0, 60])])],
     move="push_slow")
beat(59, 4, U_NADIA, "unit_door", dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -95)])], move="push_slow", sfx=[(0, "silence")])
SARI_OUT = [-2.9, -0.5, 0]
beat(60, 0, U_NADIA, "unit_doorout", [A("sari", (-1.9, -0.5, 0), 90, "takut", keys=[(0, "move", [-1.9, -0.5, 0, 90]), (1.5, "move", SARI_OUT + [90]),
                                                                                    ("w4", "look", [-3.2, -3.5, 1.4]), ("w6", "look", [-3.2, 3.0, 1.4]),
                                                                                    ("w8", "look", None)], walk=[[0, 1.5]])],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -95)])], move="push_slow")
beat(60, 8, C6, "c_long", move="push_slow", dyn=[dict(obj="ct5_glow", prop="emit", keys=[(0, 5.0), ("w17", 0.0), ("w18", 5.0)])],
     sfx=[("w17", "flicker")])
beat(60, 19, U_NADIA, on("sari", "close", side=0.2), [A("sari", (-1.9, -0.6, 0), -90, "takut", keys=[("w22", "expr", "tidur")])],
     dyn=[dict(obj="door_hinge", prop="rotz", keys=[(0, -95), ("w20", -95), ("w21", 0)])], move="push_slow", sfx=[("w21", "bang_soft")])
beat(61, 0, U_NADIA, on("sari", "xclose", side=0.1), [A("sari", (-1.9, -0.6, 0), -90, "tidur")], move="push_slow", sfx=[(0, "drone")])
beat(62, 0, U_NADIA, on("sari", "close", side=0.2), [A("sari", (-1.9, -0.6, 0), -90, "cemas")], move="push_slow")
beat(62, 16, C6, "c_door", [A("hantu", (-0.45, 16.05, 0.05), 90)], dyn=[dict(obj="c_unit_hinge", prop="rotz", keys=[(0, 0)])],
     move="push", sfx=[(0, "stinger_soft")])
# ================================================================== 63-69: the twin, the truth
beat(63, 0, U_DAY, "unit_wide", [dict(c, expr="cemas") for c in UNIT_CAST if c["who"] != "hendra"] +
     [A("hendra", (1.4, -2.7, 0), 20, "cemas")], move="push_slow", focus="hendra")
beat(63, 13, TWIN, "twin", move="push_slow", sfx=[(0, "drone")])
beat(63, 20, TWIN, "twin_a", move="pan_r")
beat(63, 32, TWIN, "twin", move="push")
beat(64, 0, TWIN, "twin_b", move="push_slow", sfx=[(0, "city")])
beat(64, 11, TWIN, "twin_a", move="push_slow", sfx=[(0, "drone")])
beat(64, 14, C7, "c_long", [A("hantu", (-1.0, 12.0, 0.05), -90, keys=[(0, "move", [-1.0, 12.0, 0.05, -90]), (1.6, "move", [1.0, 12.0, 0.05, -90])])],
     move="push_slow", sfx=[(0, "steps")])
beat(64, 29, C7, "c_long", move="push_slow", sfx=[(0, "sob")])
beat(64, 32, C7, "c_door", move="push", sfx=[(0, "knock")])
beat(64, 37, LIFT, "lift_in", move="push_slow", sfx=[("w41", "ding")])
beat(65, 0, U_DAY, "unit_wide", [dict(c, expr="cemas") for c in UNIT_CAST if c["who"] != "hendra"] +
     [A("hendra", (1.4, -2.7, 0), 20, "cemas")], move="push_slow", focus="hendra")
beat(65, 7, C7, "c_long", [A("hantu", (0.0, 9.0, 0.05), 0)], move="push_slow", sfx=[(0, "drone")])
beat(65, 27, C7, on("hantu", "medium", side=0.0), [A("hantu", (0.0, 9.0, 0.05), 0)], move="push_slow")
beat(65, 34, C7, on("hantu", "close", side=0.0), [A("hantu", (0.0, 9.0, 0.05), 0)], move="push")
beat(65, 38, LOBBY, "lobby_wide", LOBBY_CAST, move="push_slow")
beat(65, 46, U_DAY, "unit_wide", [dict(c, expr="senyum") for c in UNIT_CAST], move="push_slow")
beat(65, 49, C7, on("nadia", "close", side=0.25), [dict(NADIA_DOOR, rot=200, expr="teriak")], move="push")
beat(66, 0, EXT, "ext_wide", move="pull", sfx=[(0, "rain"), (0, "drone")])
beat(67, 0, EXT, "ext_low", move="push_slow")
beat(68, 0, BED, "bed_sit", [dict(SARI_SIT, expr="takut")], move="push_slow")
beat(68, 5, BED, "bed_phone", [], extras=[dict(kind="phone_table", at=[0.1, 1.65, 0.556], text=["BERITA", "Apartemen", "Kemayoran"])],
     move="push")
beat(69, 0, EXT, "ext_top", move="pan_u", sfx=[("w3", "stinger")], end=True)


# ------------------------------------------------------------------ resolve times
def wtime(seg, w):
    return SEGW[seg][w]["start"]


starts = []
for i, b in enumerate(B):
    if b["w"] == 0:
        t = CUTS[b["seg"]]["start"] if i else 0.0
        # first beat of a segment starts in the gap before it so the cut leads the line
        if i:
            t = max(starts[-1] + 0.5, wtime(b["seg"], 0) - 0.55)
    else:
        t = wtime(b["seg"], b["w"]) - 0.12
    starts.append(round(t, 3))
shots = []
for i, b in enumerate(B):
    t0 = starts[i]
    t1 = starts[i + 1] if i + 1 < len(B) else END
    assert t1 - t0 > 0.3, (b["seg"], b["w"], t0, t1)

    def rel(v):
        if isinstance(v, str) and v.startswith("w"):
            return round(max(0.0, wtime(b["seg"], int(v[1:])) - t0), 3)
        return v

    cast = []
    for c in b["cast"]:
        c = json.loads(json.dumps(c))
        c["keys"] = [[rel(k[0])] + k[1:] for k in c.get("keys", [])]
        if c.get("walk"):
            c["walk"] = [[rel(a), rel(z)] for a, z in c["walk"]]
        if c.get("talk"):
            mouth, wiv = [], []
            for sg, wa, wb in c.pop("talk"):
                for w in SEGW[sg][wa:(wb + 1 if wb is not None else None)]:
                    s0, e0 = w["start"] - t0, w["end"] - t0
                    if e0 <= 0.02 or s0 >= t1 - t0 - 0.02:
                        continue
                    s0, e0 = max(0.0, s0), min(t1 - t0, e0)
                    wiv.append([round(s0, 3), round(e0, 3)])
                    n = max(1, len(re.findall(r"[aiueoAIUEO]+", w["w"])))
                    slot = (e0 - s0) / n
                    for j in range(n):
                        mouth.append([round(s0 + j * slot, 3), round(s0 + (j + 0.62) * slot, 3)])
            wins = []
            for a, z in wiv:
                if wins and a - wins[-1][1] < 0.5:
                    wins[-1][1] = z
                else:
                    wins.append([a, z])
            if mouth:
                c["mouth"], c["words"], c["talkwin"] = mouth, wiv, wins
        cast.append(c)
    dyn = []
    for d in b.get("dyn", []):
        d = dict(d); d["keys"] = [[rel(k[0]), k[1]] for k in d["keys"]]
        dyn.append(d)
    st = dict(b["set"]); st.update(b.get("set_over", {}))
    cam = b["cam"]
    if isinstance(cam, str):
        cam = cam if cam not in CAM else [list(CAM[cam][0]), list(CAM[cam][1]), CAM[cam][2]]
    shots.append(dict(id=i + 1, seg=b["seg"], w=b["w"], t0=t0, t1=round(t1, 3), set=st, cam=cam, cast=cast, dyn=dyn,
                      extras=b.get("extras", []), move=b["move"], sfx=[[rel(t), n] for t, n in b.get("sfx", [])],
                      title=b.get("title", False), end=b.get("end", False), focus=b.get("focus"),
                      text=" ".join(w["w"] for w in WORDS if t0 <= w["start"] < t1)))
json.dump(dict(fps=12, size=[960, 540], out_size=[1920, 1080], duration=END, shots=shots), open("plan.json", "w"), indent=1,
          ensure_ascii=False)
print(len(shots), "shots,", sum(round((s["t1"] - s["t0"]) * 12) for s in shots), "frames @12fps")
