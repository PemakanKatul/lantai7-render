"""Clay-miniature locations for "Revisi Terakhir" (an old faculty building, its locked 3rd-floor reading room,
a boarding-house room, the canteen, a lecturer's office, the thesis defence, graduation, and paper close-ups).
Same conventions as sets.py: every builder returns ({cam: (loc, target, lens)}, {mark: (loc, rot_z)}).
Characters face -Y at rot 0 (rot 180 faces +Y, rot 90 faces +X). ~1.45 m tall.
"""
import math, random, os
import bpy
from mathutils import Vector
import lib, clay
from sets import C, cb, cyl, glow, text, door, tube, chair

R = math.radians
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {k: os.path.join(HERE, "fonts", v) for k, v in dict(
    script="DancingScript.ttf", old="PinyonScript.ttf", hand="Caveat.ttf", type="DejaVuSerif.ttf",
    typeb="DejaVuSerif-Bold.ttf", typewriter="SpecialElite.ttf", mono="CourierPrime.ttf").items()}
RED = (0.32, 0.006, 0.006)
INK = (0.012, 0.012, 0.02)
PENCIL = (0.10, 0.10, 0.11)
WOOD = (0.26, 0.14, 0.065)
WOOD_D = (0.16, 0.085, 0.04)


def font(kind):
    p = FONTS[kind]
    return bpy.data.fonts.load(p, check_existing=True)


def ftext(name, body, loc, size, color, kind="type", rot=(0, 0, 0), align="LEFT", shear=0.0, emit=0.0, extrude=0.0):
    bpy.ops.object.text_add(location=loc, rotation=tuple(R(a) for a in rot))
    o = bpy.context.object; o.name = name
    o.data.body = body; o.data.size = size; o.data.extrude = extrude
    o.data.font = font(kind); o.data.shear = shear
    o.data.align_x = align; o.data.align_y = "CENTER"
    m = lib.emit_mat(name + "_m", color, emit) if emit else clay.clay_mat(name + "_m", color, rough=0.7, dents=0.0)
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def shelf_books(prefix, x0, y, z, length, along="x", tidy=False, seed=0, depth=0.22, face=1):
    """a row of clay books standing on a shelf board; tidy = sorted by height, upright, even"""
    rnd = random.Random(seed)
    cols = [(0.35, 0.05, 0.04), (0.06, 0.16, 0.30), (0.10, 0.22, 0.10), (0.45, 0.32, 0.08), (0.20, 0.10, 0.18),
            (0.55, 0.50, 0.40), (0.08, 0.08, 0.09), (0.40, 0.18, 0.05)]
    books, t = [], 0.0
    while t < length - 0.05:
        w = rnd.uniform(0.03, 0.06); h = rnd.uniform(0.20, 0.30)
        books.append([w, h, rnd.choice(cols), rnd.uniform(-14, 14) if rnd.random() < 0.3 else 0.0])
        t += w + (0.004 if tidy else rnd.uniform(0.0, 0.03))
    if tidy:
        books.sort(key=lambda b: -b[1])
        for b in books:
            b[3] = 0.0
    t = 0.0
    for i, (w, h, col, tilt) in enumerate(books):
        c = t + w / 2
        loc = (x0 + c, y, z + h / 2) if along == "x" else (y, x0 + c, z + h / 2)
        size = (w, depth, h) if along == "x" else (depth, w, h)
        rot = (0, tilt, 0) if along == "x" else (tilt, 0, 0)
        cb(f"{prefix}{i}", size, loc, col, rot=rot, bev=0.006, dents=0.8)
        t += w + (0.004 if tidy else (0.012 if abs(tilt) > 0 else 0.004))


def bookcase(prefix, loc, w=1.0, h=2.2, d=0.32, rot_z=0, tidy=False, seed=0, shelves=5):
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = prefix
    before = set(bpy.data.objects)
    cb(prefix + "_back", (w, 0.03, h), (0, d / 2, h / 2), WOOD_D, bev=0.01)
    for s in (-1, 1):
        cb(f"{prefix}_side{s}", (0.04, d, h), (s * w / 2, 0, h / 2), WOOD, bev=0.01)
    for k in range(shelves + 1):
        z = 0.05 + k * (h - 0.1) / shelves
        cb(f"{prefix}_sh{k}", (w, d, 0.03), (0, 0, z), WOOD, bev=0.008)
        if k < shelves:
            shelf_books(f"{prefix}_b{k}_", -w / 2 + 0.03, 0.0, z + 0.015, w - 0.06, tidy=tidy, seed=seed * 10 + k, depth=d * 0.75)
    for o in set(bpy.data.objects) - before:
        if o.parent is None:
            o.parent = root
    return root


def table(prefix, loc, size=(1.6, 0.8), h=0.76, color=WOOD, rot_z=0):
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = prefix
    parts = [cb(prefix + "_top", (size[0], size[1], 0.05), (0, 0, h - 0.025), color, bev=0.012)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cb(f"{prefix}_leg{sx}{sy}", (0.05, 0.05, h - 0.05), (sx * (size[0] / 2 - 0.06), sy * (size[1] / 2 - 0.06), (h - 0.05) / 2),
                            WOOD_D, bev=0.008))
    for o in parts:
        o.parent = root
    return root


def wchair(name, loc, rot_z=0, color=WOOD_D):
    """old wooden chair; seat 0.45; backrest on +Y side before rotation"""
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = name
    ps = [cb(name + "_s", (0.42, 0.40, 0.04), (0, 0, 0.45), color, bev=0.01),
          cb(name + "_b", (0.42, 0.04, 0.45), (0, 0.19, 0.70), color, bev=0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            ps.append(cb(f"{name}_l{sx}{sy}", (0.035, 0.035, 0.45), (sx * 0.18, sy * 0.17, 0.225), color, bev=0.005))
    for o in ps:
        o.parent = root
    return root


def lamp_green(name, loc, power=30, on=True):
    x, y, z = loc
    cyl(name + "_b", 0.07, 0.025, (x, y, z + 0.012), (0.35, 0.27, 0.08))
    cyl(name + "_s", 0.01, 0.30, (x, y + 0.03, z + 0.16), (0.35, 0.27, 0.08))
    cb(name + "_h", (0.30, 0.12, 0.07), (x, y - 0.03, z + 0.33), (0.02, 0.20, 0.08), bev=0.03)
    if on:
        glow(name + "_g", (0.26, 0.09, 0.01), (x, y - 0.03, z + 0.295), (1.0, 0.85, 0.55), 6)
        lib.point_light(name + "_l", (x, y - 0.03, z + 0.26), power, (1.0, 0.80, 0.52), 0.05)


def louver_window(name, x, yc, z0=0.9, w=1.0, h=1.8, sky=(0.9, 0.45, 0.2), sky_str=1.0, along="y", inner=1):
    """tall wooden window with glass louvres (nako) on a wall plane at x (along y) or y (along x)"""
    if along == "y":
        cb(name + "_fr", (0.08, w + 0.1, h + 0.1), (x, yc, z0 + h / 2), (0.42, 0.40, 0.33), bev=0.01)
        glow(name + "_sky", (0.02, w, h), (x + 0.03 * inner * -1, yc, z0 + h / 2), sky, sky_str)
        for k in range(9):
            cb(f"{name}_n{k}", (0.03, w - 0.04, 0.11), (x - 0.06 * inner, yc, z0 + 0.12 + k * (h - 0.2) / 8), (0.30, 0.34, 0.33), rot=(25, 0, 0), bev=0.005)
    else:
        cb(name + "_fr", (w + 0.1, 0.08, h + 0.1), (yc, x, z0 + h / 2), (0.42, 0.40, 0.33), bev=0.01)
        glow(name + "_sky", (w, 0.02, h), (yc, x + 0.03 * inner * -1, z0 + h / 2), sky, sky_str)
        for k in range(9):
            cb(f"{name}_n{k}", (w - 0.04, 0.03, 0.11), (yc, x - 0.06 * inner, z0 + 0.12 + k * (h - 0.2) / 8), (0.30, 0.34, 0.33), rot=(25, 0, 0), bev=0.005)


SKY = {"dusk": ((0.95, 0.42, 0.16), 1.1), "night": ((0.05, 0.08, 0.18), 0.35), "day": ((0.75, 0.82, 0.9), 2.2),
       "dawn": ((0.55, 0.62, 0.78), 1.0)}


# =================================================================== 1. faculty building, outside
def kampus_ext(night=True, rain=False, crowd=False):
    rnd = random.Random(5)
    cb("k_ground", (60, 60, 0.2), (0, 5, -0.1), C((0.07, 0.11, 0.05) if night else (0.16, 0.24, 0.08), 1.8, 0.9), bev=0.02)
    cb("k_path", (3.2, 14, 0.04), (0, 1.0, 0.0), (0.30, 0.29, 0.26), bev=0.01)
    cb("k_road", (60, 5, 0.04), (0, -9.5, 0.0), (0.06, 0.06, 0.065) if night else (0.22, 0.22, 0.22), bev=0.01)
    wall = (0.62, 0.58, 0.48)
    trim = (0.30, 0.27, 0.22)
    W, D, FH = 18.0, 8.0, 3.4
    y0 = 8.0
    cb("k_body", (W, D, 3 * FH), (0, y0 + D / 2, 3 * FH / 2), wall, bev=0.05)
    cb("k_roof", (W + 1.6, D + 1.6, 0.35), (0, y0 + D / 2, 3 * FH + 0.15), (0.30, 0.13, 0.08), bev=0.08)
    cb("k_roof2", (W + 0.6, D * 0.7, 1.4), (0, y0 + D / 2, 3 * FH + 0.9), (0.33, 0.14, 0.09), rot=(0, 0, 0), bev=0.3)
    for f in range(1, 3):
        cb(f"k_ledge{f}", (W + 0.3, 0.35, 0.16), (0, y0 - 0.1, f * FH), trim, bev=0.03)
    ncol = 8
    for f in range(3):
        for i in range(ncol):
            x = -W / 2 + 1.2 + i * (W - 2.4) / (ncol - 1)
            if f == 0 and abs(x) < 1.6:
                continue
            z = f * FH + 0.9
            if f < 2:
                lit = night and rnd.random() < (0.75 if f == 0 else 0.6)
                col, st = ((1.0, 0.78, 0.45), 2.6) if lit else (((0.08, 0.10, 0.14), 0.15) if night else ((0.35, 0.42, 0.5), 0.5))
            else:
                if i == ncol - 1:     # the corner reading-room window: a faint green lamp, always
                    col, st = ((0.45, 0.62, 0.30), 0.55 if night else 0.08)
                else:
                    col, st = ((0.01, 0.012, 0.016), 0.02) if night else ((0.12, 0.13, 0.15), 0.25)
            cb(f"k_wf{f}_{i}", (1.25, 0.14, 1.85), (x, y0 - 0.02, z + 0.9), (0.85, 0.83, 0.76) if not night else (0.45, 0.43, 0.38), bev=0.02)
            glow(f"k_w{f}_{i}", (1.05, 0.04, 1.65), (x, y0 - 0.08, z + 0.9), col, st)
            cb(f"k_wb{f}_{i}", (0.05, 0.05, 1.65), (x, y0 - 0.11, z + 0.9), (0.35, 0.33, 0.28), bev=0.005)
    # entrance, steps, canopy
    cb("k_door", (2.4, 0.1, 2.5), (0, y0 - 0.03, 1.25), (0.05, 0.04, 0.03) if night else (0.12, 0.08, 0.05), bev=0.02)
    glow("k_door_g", (2.2, 0.03, 2.3), (0, y0 - 0.09, 1.2), (1.0, 0.8, 0.5), 1.4 if night else 0.2)
    for k in range(4):
        cb(f"k_step{k}", (4.4 - k * 0.3, 0.45, 0.16), (0, y0 - 1.6 + k * 0.38, 0.08 + k * 0.16), (0.42, 0.40, 0.36), bev=0.01)
    cb("k_canopy", (4.6, 2.2, 0.18), (0, y0 - 1.0, 3.0), trim, bev=0.04)
    for s in (-1, 1):
        cyl(f"k_pillar{s}", 0.13, 3.0, (s * 2.0, y0 - 1.8, 1.5), wall)
    cb("k_sign", (4.0, 0.08, 0.5), (0, y0 - 2.12, 3.0), (0.12, 0.10, 0.08), bev=0.02)
    text("k_sign_t", "GEDUNG C", (0, y0 - 2.18, 3.0), 0.32, (0.80, 0.70, 0.40))
    # big trees (beringin) and lamp posts
    for i, (x, y) in enumerate(((-11, 3.5), (11.5, 4.5), (-15, 12), (16, 13))):
        cyl(f"k_trunk{i}", 0.45, 5.5, (x, y, 2.75), (0.13, 0.09, 0.06))
        for j in range(4):
            clay.blob(f"k_crown{i}_{j}", (x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.2, 1.2), 6.0 + rnd.uniform(0, 1.6)),
                      (2.6, 2.4, 1.8), C((0.03, 0.07, 0.03) if night else (0.08, 0.18, 0.06), 1.6))
        for j in range(5):
            cyl(f"k_root{i}_{j}", 0.03, 4.5, (x + rnd.uniform(-1.6, 1.6), y + rnd.uniform(-1, 1), 3.4), (0.10, 0.07, 0.05))
    for i, x in enumerate((-2.6, 2.6)):
        for j, y in enumerate((-5.5, 1.0)):
            cyl(f"k_post{i}{j}", 0.05, 3.2, (x, y, 1.6), (0.08, 0.08, 0.08))
            cb(f"k_lamp{i}{j}", (0.3, 0.3, 0.3), (x, y, 3.3), (0.08, 0.08, 0.08), bev=0.05)
            glow(f"k_lampg{i}{j}", (0.22, 0.22, 0.06), (x, y, 3.15), (1.0, 0.75, 0.4), 6 if night else 0.3)
            if night:
                lib.point_light(f"k_lampl{i}{j}", (x, y, 3.0), 220, (1.0, 0.72, 0.42), 0.1)
    for i in range(7):      # parked motorbikes along the path
        x = -6 - i * 0.9
        cb(f"k_mtr{i}", (0.25, 1.4, 0.5), (x, 4.5, 0.45), rnd.choice([(0.5, 0.05, 0.05), (0.05, 0.05, 0.06), (0.6, 0.6, 0.6), (0.05, 0.12, 0.35)]),
           rot=(0, 0, rnd.uniform(-8, 8)), bev=0.1)
        for s in (-1, 1):
            cyl(f"k_whl{i}{s}", 0.25, 0.08, (x, 4.5 + s * 0.55, 0.25), (0.02, 0.02, 0.02), rot=(0, 90, 0))
    if crowd:
        cb("k_banner", (8, 0.1, 1.2), (0, y0 - 0.3, 4.6), (0.08, 0.20, 0.45), bev=0.02)
        text("k_banner_t", "SELAMAT & SUKSES WISUDA", (0, y0 - 0.37, 4.6), 0.55, (0.95, 0.85, 0.5))
    if night:
        lib.world((0.004, 0.005, 0.012), 1.0)
        lib.area_light("k_moon", (-14, -10, 16), (0, 8, 4), 2600, 6.0, (0.45, 0.55, 0.9))
        lib.area_light("k_fill", (0, -12, 4), (0, 8, 4), 300, 8.0, (0.25, 0.3, 0.5))
    else:
        lib.world((0.55, 0.62, 0.75), 1.0)
        lib.sun("k_sun", (-0.4, 0.5, -0.6), 3.2, (1.0, 0.93, 0.82), 3.0)
    cams = {"road": ((-7.0, -13.5, 1.3), (1.0, 9.0, 5.2), 24), "wide": ((1.5, -17.0, 3.0), (0, 9.0, 5.0), 28),
            "facade": ((3.0, 2.5, 1.4), (5.0, 8.0, 8.5), 22), "win3": ((5.6, 2.8, 7.4), (7.9, 8.0, 8.4), 40),
            "steps": ((0.6, 3.4, 1.05), (0.0, 6.9, 0.72), 30), "low": ((-3.5, -5.0, 0.35), (2.0, 8.0, 6.5), 22),
            "up3": ((7.6, 3.5, 1.2), (7.9, 8.0, 8.9), 30)}
    marks = {"kating": ((0.05, 6.86, 0.32 - 0.485), R(-8)), "maba1": ((-0.75, 6.86, 0.32 - 0.485), R(-28)), "maba2": ((0.85, 6.86, 0.32 - 0.485), R(30)),
             "path": ((0.0, -2.0, 0), R(180)), "door": ((0.0, 7.6, 0.64), R(180)),
             "ibu": ((-0.45, -0.6, 0), R(-70)), "laras": ((0.35, -0.75, 0), R(105))}
    return cams, marks


# =================================================================== 2. stairwell up to the locked 3rd floor
def tangga_rt(gate="open", light=0.5):
    import sets
    cams, marks = sets.stairs(floor="3", light=light)
    top = 0.165 * 9
    # folding iron gate across the bottom of flight B (the way up to the 3rd floor)
    gx0, gx1, gy = -1.28, -0.04, 1.72
    n = 12
    for k in range(n):
        x = gx0 + (gx1 - gx0) * k / (n - 1) if gate == "closed" else gx0 + 0.015 * k
        cb(f"g_bar{k}", (0.02, 0.02, 2.05), (x, gy, top + 1.03), (0.12, 0.12, 0.12), bev=0.004)
    for z in (0.15, 1.0, 1.95):
        L = (gx1 - gx0) if gate == "closed" else 0.2
        cb(f"g_rail{z}", (L, 0.03, 0.03), (gx0 + L / 2, gy, top + z), (0.12, 0.12, 0.12), bev=0.004)
    if gate == "closed":
        cb("g_lock", (0.07, 0.04, 0.09), (gx1 - 0.08, gy - 0.04, top + 1.05), (0.55, 0.45, 0.15), bev=0.01)
        cyl("g_chain", 0.012, 0.3, (gx1 - 0.08, gy - 0.03, top + 1.13), (0.3, 0.3, 0.3), rot=(0, 90, 0))
    cb("g_sign", (0.02, 0.62, 0.36), (-1.27, 1.2, top + 1.55), (0.80, 0.78, 0.70), bev=0.005)
    ftext("g_sign_t1", "LANTAI 3", (-1.255, 1.2, top + 1.63), 0.075, (0.5, 0.02, 0.02), kind="typeb", rot=(90, 0, 90), align="CENTER")
    ftext("g_sign_t2", "DITUTUP PUKUL 18.00", (-1.255, 1.2, top + 1.50), 0.042, INK, kind="typeb", rot=(90, 0, 90), align="CENTER")
    cams.update({"gate": ((-0.2, 3.0, top + 1.3), (-0.7, 1.4, top + 1.2), 32), "sign": ((-0.6, 1.2, top + 1.55), (-1.27, 1.2, top + 1.55), 40)})
    marks.update({"gate": ((-0.65, 2.25, top), 0.0)})
    return cams, marks


# =================================================================== 3. reading room, 3rd floor
def ruang_baca(light="dusk", lamp=True, stack=True, tubes=0.0, fog=0.02, chair_out=False):
    """long room along +Y (y 0..12, x -3..3). The corner desk is at the far right (2.0, 11.0)."""
    L = 12.0
    cb("rb_floor", (6.2, L + 0.4, 0.06), (0, L / 2, -0.03), lib.tile_floor("rb_tiles", 0.4, (0.40, 0.36, 0.28), (0.30, 0.27, 0.21)), bev=0.005)
    cb("rb_ceil", (6.2, L + 0.4, 0.08), (0, L / 2, 3.3), (0.42, 0.41, 0.37), bev=0.005)
    wallc = lib.grime_wall("rb_wall", (0.52, 0.50, 0.42), (0.22, 0.20, 0.15))
    cb("rb_wL", (0.14, L + 0.4, 3.3), (-3.07, L / 2, 1.65), wallc, bev=0.01)
    cb("rb_wR", (0.14, L + 0.4, 3.3), (3.07, L / 2, 1.65), wallc, bev=0.01)
    cb("rb_wB", (6.3, 0.14, 3.3), (0, L + 0.07, 1.65), wallc, bev=0.01)
    cb("rb_wF", (6.3, 0.14, 3.3), (0, -0.07, 1.65), wallc, bev=0.01)
    cb("rb_skirt", (6.1, L, 0.12), (0, L / 2, 0.06), (0.15, 0.10, 0.06), bev=0.01)
    sky, sky_s = SKY[light]
    for i, y in enumerate((2.0, 5.0, 8.0)):
        louver_window(f"rb_win{i}", 3.0, y, 0.9, 1.1, 1.9, sky, sky_s)
        if light in ("dusk", "day", "dawn"):
            lib.area_light(f"rb_sun{i}", (3.4, y, 2.0), (0.5, y + 0.8, 0.0), {"dusk": 650, "day": 900, "dawn": 300}[light], 1.0,
                           {"dusk": (1.0, 0.55, 0.28), "day": (1.0, 0.95, 0.85), "dawn": (0.7, 0.78, 1.0)}[light])
        else:
            lib.area_light(f"rb_moon{i}", (3.4, y, 2.0), (0.5, y + 0.6, 0.0), 70, 1.0, (0.45, 0.55, 0.95))
    # bookcases on the left wall and the back-left
    for i, y in enumerate((1.4, 2.5, 3.6, 4.7, 5.8, 6.9, 8.0, 9.1, 10.2)):
        bookcase(f"rb_bc{i}", (-2.82, y, 0), w=1.05, h=2.4, d=0.36, rot_z=-90, seed=i + 1)
    for i, x in enumerate((-2.1, -1.0)):
        bookcase(f"rb_bb{i}", (x, 11.80, 0), w=1.05, h=2.4, d=0.36, rot_z=0, seed=20 + i)
    # a free-standing double shelf in the middle-left (the gap where something stands)
    for i, y in enumerate((7.4, 9.4)):
        bookcase(f"rb_mid{i}", (-1.45, y, 0), w=1.6, h=2.1, d=0.34, rot_z=90, seed=40 + i)
    # reading tables
    for i, y in enumerate((2.2, 4.4, 6.6)):
        table(f"rb_t{i}", (0.6, y, 0), size=(1.0, 1.9), h=0.76)
        for s in (-1, 1):
            for k in (-0.5, 0.5):
                wchair(f"rb_c{i}{s}{k}", (0.6 + s * 0.72, y + k, 0), rot_z=90 * s * -1 + (180 if s > 0 else 0) + random.Random(i * 7 + int(k * 4) + s).uniform(-12, 12))
    # THE corner desk
    table("rb_desk", (1.85, 11.15, 0), size=(1.25, 0.72), h=0.78, color=(0.22, 0.12, 0.055))
    wchair("rb_dchair", (1.85, 10.30 if chair_out else 10.58, 0), rot_z=180 + (25 if chair_out else 0))
    if lamp:
        lamp_green("rb_lamp", (2.25, 11.35, 0.78), power=32, on=True)
    else:
        lamp_green("rb_lamp", (2.25, 11.35, 0.78), on=False)
    if stack:
        cb("rb_stack", (0.30, 0.42, 0.06), (1.75, 11.12, 0.81), (0.80, 0.78, 0.72), rot=(0, 0, -6), bev=0.006, dents=0.4)
        cb("rb_stack_top", (0.30, 0.42, 0.004), (1.75, 11.12, 0.842), (0.86, 0.84, 0.78), rot=(0, 0, -6), bev=0.001, dents=0.0)
        for k in range(5):
            cb(f"rb_red{k}", (0.20, 0.006, 0.002), (1.75 - 0.02 * k, 11.22 - 0.06 * k, 0.845), RED, rot=(0, 0, -6 + 3 * k), bev=0.001, dents=0.0)
        cyl("rb_pen", 0.006, 0.15, (2.0, 10.98, 0.79), RED, rot=(0, 90, 30))
    cb("rb_dust", (0.4, 0.3, 0.18), (1.42, 11.38, 0.87), (0.40, 0.36, 0.30), bev=0.03)   # old box of files
    # clock, sign, fans, tubes
    cyl("rb_clock", 0.17, 0.05, (0.0, L - 0.02, 2.55), (0.75, 0.73, 0.66), rot=(90, 0, 0))
    cb("rb_ch1", (0.012, 0.01, 0.11), (0.0, L - 0.06, 2.59), (0.02, 0.02, 0.02)); cb("rb_ch2", (0.09, 0.01, 0.012), (0.04, L - 0.06, 2.55), (0.02, 0.02, 0.02))
    cb("rb_sign", (1.4, 0.04, 0.32), (0.0, 0.03, 2.65), (0.12, 0.09, 0.06), bev=0.01)
    ftext("rb_sign_t", "RUANG BACA", (0.0, 0.06, 2.65), 0.15, (0.78, 0.70, 0.45), kind="typeb", rot=(90, 0, 180), align="CENTER")
    door("rb_door", (-0.9, 0.0, 0), 180, color=(0.20, 0.11, 0.05), w=1.0)
    for i, y in enumerate((3.0, 7.5)):
        cyl(f"rb_fan{i}", 0.08, 0.1, (0.3, y, 3.18), (0.3, 0.3, 0.3))
        for k in range(3):
            cb(f"rb_blade{i}{k}", (0.7, 0.12, 0.012), (0.3 + 0.35 * math.cos(R(120 * k)), y + 0.35 * math.sin(R(120 * k)), 3.12),
               (0.55, 0.52, 0.45), rot=(0, 0, 120 * k), bev=0.004)
    for i, y in enumerate((2.0, 6.0, 10.0)):
        tube(f"rb_tube{i}", (0.6, y, 3.24), on=tubes, power=22)
    lib.world((0.012, 0.012, 0.014) if light in ("dusk", "day") else (0.006, 0.007, 0.010), 1.0)
    lib.area_light("rb_fill", (0.0, 4.0, 3.1), (0.5, 8.0, 0.0), 120 if light in ("dusk", "day") else 30, 3.0,
                   (1.0, 0.85, 0.7) if light in ("dusk", "day") else (0.5, 0.6, 0.9))
    if fog:
        lib.fog_volume((-3, 0, 0), (3, L, 3.3), fog, color=(1.0, 0.92, 0.8) if light in ("dusk", "day") else (0.75, 0.85, 1.0))
    cams = {"long": ((-1.6, 0.6, 1.65), (2.0, 11.0, 0.95), 26), "corner": ((0.5, 11.0, 1.32), (1.85, 10.72, 0.98), 34),
            "desk_top": ((1.72, 10.72, 1.5), (1.75, 11.12, 0.8), 36), "door": ((2.5, 11.5, 1.55), (-0.6, 0.3, 1.0), 26),
            "shelf": ((0.6, 5.9, 1.35), (-2.0, 8.5, 1.15), 30), "gap": ((1.4, 7.0, 1.3), (-1.45, 8.4, 1.2), 34),
            "low": ((0.9, 8.0, 0.35), (2.05, 11.0, 0.95), 24), "window": ((-1.8, 3.2, 1.5), (3.0, 7.0, 1.6), 30),
            "behind": ((0.75, 9.25, 1.8), (2.45, 11.45, 1.1), 30), "front": ((2.05, 11.45, 1.42), (1.85, 10.55, 1.05), 36)}
    marks = {"chair": ((1.85, 10.60, -0.08), R(180)), "desk": ((1.55, 10.35, 0), R(165)), "door": ((-0.4, 0.7, 0), R(180)),
             "aisle": ((1.9, 6.0, 0), R(180)), "gap": ((-1.45, 8.4, 0), R(-90)), "behind": ((2.55, 11.62, 0), R(-30)),
             "corner_far": ((2.68, 11.55, 0), R(-20)), "shelf": ((-2.3, 8.55, 0), R(90))}
    return cams, marks


# =================================================================== 4. paper close-ups (drafts, notes, receipts)
def kertas(lines=(), kind="a4", pen=True, desk="wood", light="lamp", title_page=False, rot=-3.0, pencil=False, extras=()):
    """A sheet on a desk, seen from above. Line codes:
       '#text' bold heading (centred)   'text' typed   '~text' typed + red strike   '!text' red handwriting
       '^text' red margin note           '@text' pencil handwriting   '=text' neat old cursive (black ink)
       '*text' messy own handwriting (blue ink)   '' blank line
    Every object is named kt_l<i> (text), kt_s<i> (strike), so a shot can reveal them with dyn 'hide' keys."""
    dc = {"wood": (0.24, 0.13, 0.06), "dark": (0.10, 0.06, 0.035), "sheet": (0.55, 0.52, 0.48), "table": (0.48, 0.47, 0.45)}[desk]
    cb("kt_desk", (2.2, 1.6, 0.06), (0, 0, 0.73), dc, bev=0.01, dents=1.4)
    paper = {"a4": (0.82, 0.81, 0.76), "tua": (0.66, 0.58, 0.40), "buku": (0.80, 0.78, 0.70), "struk": (0.84, 0.83, 0.80),
             "belanja": (0.80, 0.76, 0.58), "jilid": (0.80, 0.79, 0.74)}[kind]
    pw, ph = {"a4": (0.36, 0.50), "tua": (0.36, 0.50), "buku": (0.38, 0.50), "struk": (0.15, 0.42), "belanja": (0.20, 0.27),
              "jilid": (0.36, 0.50)}[kind]
    z = 0.765
    bpy.ops.object.empty_add(location=(0.0, 0.0, z), rotation=(0, 0, R(rot)))
    root = bpy.context.object; root.name = "kt_root"
    parts = []
    if kind == "jilid":
        parts.append(cb("kt_cover", (0.76, 0.54, 0.02), (0, 0, -0.012), (0.35, 0.02, 0.03), bev=0.006))
        parts.append(cb("kt_left", (0.36, 0.50, 0.01), (-0.185, 0, 0.002), paper, bev=0.004, dents=0.3))
        parts.append(ftext("kt_lt", "KATA PENGANTAR", (-0.185, 0.19, 0.0085), 0.019, INK, kind="typeb", align="CENTER"))
        for k in range(10):
            parts.append(cb(f"kt_lline{k}", (0.27, 0.004, 0.0005), (-0.185, 0.14 - k * 0.03, 0.0075), (0.30, 0.30, 0.30), bev=0.0, dents=0.0))
        cx = 0.185
    else:
        cx = 0.0
    parts.append(cb("kt_paper", (pw, ph, 0.004 if kind != "buku" else 0.02), (cx, 0, 0.0), paper, bev=0.002, dents=0.25))
    if kind in ("a4", "tua") and not title_page:
        parts.append(cb("kt_under", (pw, ph, 0.004), (cx + 0.01, -0.008, -0.004), tuple(v * 0.9 for v in paper), rot=(0, 0, 3), bev=0.002, dents=0.2))
    if kind == "buku":
        for k in range(16):
            parts.append(cb(f"kt_rule{k}", (pw - 0.02, 0.0015, 0.0004), (cx, ph / 2 - 0.06 - k * 0.03 - 0.009, 0.0102), (0.40, 0.50, 0.72), bev=0.0, dents=0.0))
        parts.append(cb("kt_margin", (0.0015, ph - 0.01, 0.0004), (cx - pw / 2 + 0.045, 0, 0.0103), (0.6, 0.2, 0.2), bev=0.0, dents=0.0))
    if kind == "belanja":
        for k in range(7):
            parts.append(cb(f"kt_tear{k}", (0.025, 0.012, 0.004), (cx - pw / 2 + 0.012 + k * 0.023, ph / 2 + 0.003, 0.0), paper, rot=(0, 0, 25 * (k % 2 * 2 - 1)), bev=0.002))
    zt = 0.0035 if kind != "buku" else 0.0118
    top = ph / 2 - (0.06 if kind != "struk" else 0.045)
    step = {"struk": 0.028, "belanja": 0.034}.get(kind, 0.03 if kind == "buku" else 0.033)
    lx = cx - pw / 2 + (0.055 if kind != "struk" else 0.012)
    tsize = {"struk": 0.0125, "belanja": 0.02}.get(kind, 0.0155)
    tkind = "typewriter" if kind == "tua" else ("mono" if kind == "struk" else "type")
    y = top
    for i, ln in enumerate(lines):
        c, body = (ln[0], ln[1:]) if ln and ln[0] in "#~!^@=*" else ("", ln)
        if title_page and c == "#":
            parts.append(ftext(f"kt_l{i}", body, (cx, y, zt), tsize * 1.45, INK, kind="typeb", align="CENTER"))
        elif c == "#":
            parts.append(ftext(f"kt_l{i}", body, (cx, y, zt), tsize * 1.15, INK, kind="typeb" if kind != "tua" else "typewriter", align="CENTER"))
        elif c in ("", "~"):
            if body:
                t = ftext(f"kt_l{i}", body, (lx, y, zt) if not title_page else (cx, y, zt), tsize * (1.12 if title_page else 1.0), INK,
                          kind=("typeb" if title_page else tkind),
                          align="LEFT" if not title_page else "CENTER")
                parts.append(t)
                if c == "~":
                    bpy.context.view_layer.update()
                    wdt = max(0.04, t.dimensions.x)
                    x0 = (lx + wdt / 2) if not title_page else cx
                    st_ = cb(f"kt_s{i}", (wdt + 0.02, 0.0022, 0.0003), (x0, y + 0.001, zt + 0.001), RED, rot=(0, 0, random.Random(i).uniform(-1.5, 1.5)), bev=0.0, dents=0.0)
                    st_.visible_shadow = False
                    parts.append(st_)
        elif c == "!":
            parts.append(ftext(f"kt_l{i}", body, (lx + 0.02, y, zt), tsize * 1.55, RED, kind="script", rot=(0, 0, random.Random(i).uniform(-2.5, 1.5))))
        elif c == "^":
            parts.append(ftext(f"kt_l{i}", body, (cx + pw / 2 - 0.012, y, zt), tsize * 1.4, RED, kind="script", align="RIGHT", rot=(0, 0, -6)))
        elif c == "@":
            parts.append(ftext(f"kt_l{i}", body, (lx + 0.01, y, zt), tsize * 1.7, PENCIL, kind="hand", rot=(0, 0, random.Random(i).uniform(-3, 2))))
        elif c == "=":
            parts.append(ftext(f"kt_l{i}", body, (lx, y, zt), tsize * 1.5, INK, kind="script"))
        elif c == "*":
            parts.append(ftext(f"kt_l{i}", body, (lx + 0.005, y, zt), tsize * 1.75, (0.03, 0.06, 0.30), kind="hand", rot=(0, 0, random.Random(i).uniform(-3, 3))))
        y -= step * (1.3 if c in "!=*@" and kind not in ("buku",) else 1.0)
    for o in parts:
        o.parent = root
    if pen:
        cyl("kt_pen", 0.0065, 0.15, (0.30, -0.16, z + 0.007), RED, rot=(0, 90, 35))
        cyl("kt_pencap", 0.0072, 0.04, (0.356, -0.121, z + 0.007), (0.08, 0.08, 0.09), rot=(0, 90, 35))
    if pencil:
        cyl("kt_pencil", 0.0055, 0.17, (-0.30, -0.18, z + 0.006), (0.75, 0.6, 0.1), rot=(0, 90, -20))
    for e in extras:
        if e == "mug":
            cyl("kt_mug", 0.045, 0.1, (-0.30, 0.18, z + 0.05), (0.62, 0.60, 0.55)); cyl("kt_coffee", 0.04, 0.005, (-0.30, 0.18, z + 0.098), (0.03, 0.015, 0.008))
        if e == "glasses":
            cyl("kt_gl1", 0.03, 0.004, (0.27, 0.15, z + 0.004), (0.05, 0.05, 0.05)); cyl("kt_gl2", 0.03, 0.004, (0.34, 0.15, z + 0.004), (0.05, 0.05, 0.05))
    if light == "lamp":
        lib.point_light("kt_lamp", (0.35, 0.35, 1.35), 30, (1.0, 0.82, 0.58), 0.12)
        lib.world((0.004, 0.004, 0.006), 1.0)
    elif light == "cold":
        lib.point_light("kt_lamp", (-0.3, 0.3, 1.35), 26, (0.72, 0.82, 1.0), 0.15)
        lib.world((0.003, 0.004, 0.007), 1.0)
    else:   # day
        lib.area_light("kt_day", (-0.6, 0.6, 1.6), (0, 0, 0.75), 70, 1.0, (1.0, 0.96, 0.9))
        lib.world((0.10, 0.10, 0.11), 1.0)
    cams = {"top": ((0.02, -0.12, 1.45), (0.0, 0.0, 0.76), 40), "page": ((0.03, -0.13, 1.12), (0.0, 0.03, 0.765), 45),
            "low": ((-0.42, -0.52, 0.98), (0.0, 0.03, 0.77), 34), "topline": ((0.0, 0.08, 1.02), (0.0, 0.14, 0.765), 50),
            "midline": ((0.0, -0.03, 1.0), (0.0, 0.03, 0.765), 50), "botline": ((0.0, -0.16, 1.02), (0.0, -0.10, 0.765), 50),
            "pen": ((0.16, -0.38, 0.95), (0.28, -0.14, 0.77), 45)}
    if kind == "jilid":
        cams.update({"top": ((0.02, -0.14, 1.55), (0.0, 0.0, 0.76), 40), "right": ((0.19, -0.07, 1.06), (0.185, 0.03, 0.765), 45)})
    return cams, {}


# =================================================================== 5. phone close-up (calls and chat)
def hp(mode="chat", bubbles=(), typing="", caller="Ibu"):
    """bubbles: list of (side 'in'|'out', text). Objects hp_b<i> (bubble + text hp_bt<i>) can be revealed with dyn hide.
    typing: text in the input field (object hp_type)."""
    cb("hp_desk", (1.2, 1.0, 0.04), (0, 0, 0.73), (0.55, 0.40, 0.42), bev=0.01, dents=1.6)     # bed sheet
    z = 0.755
    cb("hp_body", (0.085, 0.175, 0.012), (0, 0, z), (0.02, 0.02, 0.025), bev=0.008)
    bg = (0.02, 0.06, 0.05) if mode == "chat" else (0.05, 0.12, 0.10)
    glow("hp_scr", (0.077, 0.165, 0.002), (0, 0, z + 0.0065), bg, 1.2)
    zt = z + 0.0080
    if mode == "call":
        ftext("hp_name", caller, (0, 0.045, zt), 0.010, (0.95, 0.95, 0.95), kind="typeb", align="CENTER", emit=3.0)
        ftext("hp_sub", "Panggilan masuk...", (0, 0.03, zt), 0.0055, (0.75, 0.8, 0.8), kind="type", align="CENTER", emit=2.0)
        cyl("hp_avatar", 0.014, 0.001, (0, 0.065, zt), lib.emit_mat("hp_av", (0.55, 0.6, 0.62), 2.0))
        cyl("hp_acc", 0.009, 0.001, (0.022, -0.06, zt), lib.emit_mat("hp_g", (0.1, 0.8, 0.3), 3.0))
        cyl("hp_dec", 0.009, 0.001, (-0.022, -0.06, zt), lib.emit_mat("hp_r", (0.9, 0.1, 0.1), 3.0))
    else:
        glow("hp_head", (0.077, 0.018, 0.001), (0, 0.0735, zt - 0.0005), (0.03, 0.30, 0.25), 1.8)
        ftext("hp_htxt", caller, (-0.022, 0.0735, zt + 0.0003), 0.0075, (0.95, 0.95, 0.95), kind="typeb", emit=3.0)
        cyl("hp_hav", 0.006, 0.001, (-0.031, 0.0735, zt + 0.0003), lib.emit_mat("hp_av", (0.65, 0.68, 0.7), 2.0))
        y = 0.05
        for i, (side, t) in enumerate(bubbles):
            n = len(t)
            w = min(0.066, 0.012 + n * 0.0031)
            x = -0.036 + w / 2 if side == "in" else 0.036 - w / 2
            col = (0.85, 0.86, 0.86) if side == "in" else (0.62, 0.92, 0.66)
            glow(f"hp_b{i}", (w, 0.017, 0.0008), (x, y, zt), col, 1.6)
            ftext(f"hp_bt{i}", t, (x, y, zt + 0.0008), 0.0062, (0.02, 0.02, 0.02), kind="type", align="CENTER", emit=0.0)
            ftext(f"hp_bk{i}", "21.07" if side == "in" else "21.09", (x + w / 2 - 0.006, y - 0.0048, zt + 0.0008), 0.0024, (0.25, 0.25, 0.25),
                  kind="type", align="RIGHT")
            y -= 0.026
        glow("hp_input", (0.06, 0.012, 0.0008), (-0.006, -0.071, zt), (0.85, 0.86, 0.86), 1.4)
        if typing:
            ftext("hp_type", typing, (-0.034, -0.071, zt + 0.0008), 0.0058, (0.05, 0.05, 0.05), kind="type")
        cyl("hp_send", 0.0055, 0.001, (0.031, -0.071, zt), lib.emit_mat("hp_sendm", (0.05, 0.6, 0.45), 2.0))
    lib.point_light("hp_room", (0.3, 0.4, 1.3), 6, (0.6, 0.65, 0.9), 0.2)
    lib.world((0.003, 0.003, 0.005), 1.0)
    cams = {"top": ((0.0, -0.03, 0.98), (0.0, 0.0, 0.755), 42), "close": ((0.0, 0.0, 0.90), (0.0, 0.022, 0.755), 55),
            "angle": ((-0.18, -0.30, 0.96), (0.0, 0.0, 0.755), 45)}
    return cams, {}


# =================================================================== 6. hand close-up: red stain, pencil case
def tangan(stain=True, case=True):
    cb("tg_desk", (1.4, 1.0, 0.04), (0, 0, 0.73), (0.24, 0.13, 0.06), bev=0.01, dents=1.4)
    z = 0.75
    sk = clay.clay_mat("tg_skin", (0.36, 0.185, 0.10), rough=0.55, sss=0.2, dents=0.3)
    clay.blob("tg_palm", (0.0, -0.01, z + 0.016), (0.048, 0.058, 0.016), sk)
    clay.blob("tg_wrist", (0.0, -0.095, z + 0.02), (0.036, 0.05, 0.02), sk)
    clay.blob("tg_sleeve", (0.0, -0.20, z + 0.035), (0.055, 0.08, 0.04), clay.clay_mat("tg_sl", (0.72, 0.71, 0.66), dents=0.6))
    fing = [(-0.036, 0.035, 0.0105, 0.060, -10), (-0.013, 0.045, 0.0112, 0.072, -3), (0.011, 0.046, 0.0112, 0.078, 2), (0.033, 0.040, 0.010, 0.064, 9)]
    for i, (x, y, r, l, a) in enumerate(fing):
        clay.limb(f"tg_f{i}", (x, y, z + 0.016), (x + math.sin(R(a)) * l, y + math.cos(R(a)) * l, z + 0.011), r, sk)
    clay.limb("tg_thumb", (0.045, -0.025, z + 0.016), (0.085, 0.03, z + 0.012), 0.012, sk)
    if stain:   # the middle finger (index 2): dried red on the tip
        x, y, r, l, a = fing[2]
        tip = (x + math.sin(R(a)) * l, y + math.cos(R(a)) * l, z + 0.013)
        clay.blob("tg_stain", tip, (0.0118, 0.016, 0.0105), clay.clay_mat("tg_red", (0.24, 0.01, 0.01), rough=0.35, dents=0.4))
        clay.blob("tg_stain2", (x + 0.001, y + l * 0.55, z + 0.019), (0.008, 0.011, 0.005), clay.clay_mat("tg_red2", (0.20, 0.012, 0.01), rough=0.4, dents=0.4))
    if case:
        cb("tg_case", (0.26, 0.09, 0.05), (0.22, 0.12, z + 0.025), (0.12, 0.20, 0.35), bev=0.02)
        cb("tg_case_in", (0.24, 0.075, 0.01), (0.22, 0.12, z + 0.047), (0.03, 0.04, 0.07), bev=0.005)
        for k, col in enumerate(((0.05, 0.05, 0.3), (0.05, 0.05, 0.05), (0.75, 0.6, 0.1))):
            cyl(f"tg_p{k}", 0.006, 0.16, (0.21 + 0.004 * k, 0.10 + 0.016 * k, z + 0.06), col, rot=(0, 90, 4 * k))
        cyl("tg_red_pen", 0.0075, 0.16, (0.22, 0.155, z + 0.066), (0.85, 0.83, 0.80), rot=(0, 90, -3))   # clear barrel
        cyl("tg_red_ink", 0.0045, 0.08, (0.18, 0.155, z + 0.066), RED, rot=(0, 90, -3))                # ink only half full
        cyl("tg_red_cap", 0.008, 0.035, (0.29, 0.151, z + 0.066), RED, rot=(0, 90, -3))
    lib.point_light("tg_lamp", (0.3, 0.3, 1.25), 18, (1.0, 0.82, 0.6), 0.1)
    lib.world((0.003, 0.003, 0.005), 1.0)
    cams = {"hand": ((0.02, -0.30, 1.06), (0.02, 0.01, 0.76), 42), "finger": ((0.05, -0.06, 0.90), (0.015, 0.10, 0.765), 55),
            "case": ((0.15, -0.12, 0.98), (0.22, 0.12, 0.78), 45), "pen": ((0.12, 0.02, 0.88), (0.22, 0.155, 0.81), 60)}
    return cams, {}


# =================================================================== 7. Laras's boarding-house room
def kamar_laras(tidy=False, light="night", lamp=True):
    cb("kl_floor", (3.6, 4.0, 0.06), (0, 0, -0.03), lib.tile_floor("kl_tiles", 0.33, (0.55, 0.52, 0.46), (0.48, 0.45, 0.40)), bev=0.005)
    cb("kl_ceil", (3.6, 4.0, 0.06), (0, 0, 2.8), (0.55, 0.55, 0.52), bev=0.005)
    wc = (0.42, 0.47, 0.44)
    cb("kl_back", (3.6, 0.12, 2.8), (0, 2.0, 1.4), wc); cb("kl_left", (0.12, 4.0, 2.8), (-1.8, 0, 1.4), wc)
    cb("kl_right", (0.12, 4.0, 2.8), (1.8, 0, 1.4), wc); cb("kl_front", (3.6, 0.12, 2.8), (0, -2.0, 1.4), wc)
    # bed (left), desk (right, against the back wall), shelf above the desk
    cb("kl_bed", (1.0, 2.0, 0.30), (-1.25, 0.6, 0.18), (0.30, 0.18, 0.09), bev=0.04)
    cb("kl_mat", (0.95, 1.95, 0.16), (-1.25, 0.6, 0.40), (0.68, 0.66, 0.62), bev=0.06)
    cb("kl_pillow", (0.6, 0.35, 0.13), (-1.25, 1.42, 0.53), (0.78, 0.75, 0.68), bev=0.06)
    if tidy:
        cb("kl_blanket", (0.96, 1.1, 0.06), (-1.25, 0.2, 0.50), (0.55, 0.55, 0.52), bev=0.03)
    else:
        cb("kl_blanket", (0.98, 1.2, 0.12), (-1.2, 0.3, 0.52), (0.55, 0.20, 0.25), rot=(0, 4, 8), bev=0.06)
        for k in range(3):
            clay.blob(f"kl_clothes{k}", (-1.4 + k * 0.2, -0.1 + k * 0.25, 0.55), (0.18, 0.14, 0.05), C(((0.1, 0.12, 0.3), (0.5, 0.45, 0.4), (0.05, 0.05, 0.05))[k], 1.0))
    table("kl_desk", (0.85, 1.55, 0), size=(1.4, 0.65), h=0.75, color=(0.45, 0.33, 0.20))
    wchair("kl_chair", (0.85, 0.95, 0), rot_z=0, color=(0.15, 0.15, 0.17))
    cb("kl_laptop", (0.34, 0.24, 0.015), (0.85, 1.5, 0.76), (0.12, 0.12, 0.13), bev=0.005)
    cb("kl_screen", (0.34, 0.015, 0.22), (0.85, 1.62, 0.88), (0.12, 0.12, 0.13), rot=(-12, 0, 0), bev=0.005)
    glow("kl_screen_g", (0.31, 0.004, 0.19), (0.85, 1.61, 0.88), (0.55, 0.62, 0.75), 1.5 if light == "night" else 0.6, rot=(-12, 0, 0))
    cyl("kl_lamp_b", 0.06, 0.02, (1.35, 1.7, 0.76), (0.85, 0.85, 0.82)); cyl("kl_lamp_s", 0.01, 0.42, (1.35, 1.72, 0.97), (0.85, 0.85, 0.82))
    cb("kl_lamp_h", (0.16, 0.16, 0.1), (1.3, 1.62, 1.17), (0.85, 0.85, 0.82), bev=0.04)
    if lamp:
        glow("kl_lamp_g", (0.12, 0.12, 0.01), (1.3, 1.62, 1.12), (1.0, 0.92, 0.75), 5)
        lib.point_light("kl_lamp_l", (1.3, 1.6, 1.08), 34, (1.0, 0.85, 0.62), 0.05)
    # papers on the desk: messy pile or a squared stack
    if tidy:
        cb("kl_papers", (0.22, 0.30, 0.05), (0.32, 1.45, 0.775), (0.80, 0.78, 0.72), bev=0.004, dents=0.3)
        cyl("kl_mug", 0.045, 0.1, (0.4, 1.2, 0.8), (0.12, 0.12, 0.13)); cyl("kl_coffee", 0.04, 0.005, (0.4, 1.2, 0.848), (0.03, 0.015, 0.008))
    else:
        for k in range(6):
            cb(f"kl_paper{k}", (0.22, 0.30, 0.004), (0.3 + 0.05 * k, 1.35 + 0.03 * (k % 3), 0.752 + 0.004 * k), (0.82, 0.80, 0.74),
               rot=(0, 0, random.Random(k).uniform(-30, 30)), bev=0.002, dents=0.2)
        cyl("kl_bottle", 0.035, 0.22, (0.25, 1.75, 0.86), (0.20, 0.45, 0.65))
    # shelf with books above the desk
    cb("kl_shelf", (1.3, 0.25, 0.03), (0.85, 1.85, 1.55), (0.45, 0.33, 0.20), bev=0.01)
    shelf_books("kl_bk", 0.25, 1.85, 1.565, 1.2, tidy=tidy, seed=7, depth=0.18)
    # poster (only in the old, messy room)
    if not tidy:
        cb("kl_poster", (0.6, 0.02, 0.85), (-1.1, 1.93, 1.6), (0.65, 0.25, 0.10), bev=0.005)
        clay.blob("kl_poster_b", (-1.1, 1.915, 1.65), (0.2, 0.01, 0.2), C((0.95, 0.75, 0.15), 0.2))
        ftext("kl_poster_t", "MANIAK", (-1.1, 1.915, 1.3), 0.11, (0.05, 0.05, 0.05), kind="typeb", rot=(90, 0, 0), align="CENTER")
    else:
        cb("kl_poster_mark", (0.6, 0.006, 0.85), (-1.1, 1.935, 1.6), (0.46, 0.51, 0.48), bev=0.002)
    # door, window, clock
    door("kl_door", (1.75, -1.0, 0), 90, color=(0.45, 0.33, 0.20), w=0.85)
    cb("kl_winfr", (0.05, 1.0, 1.0), (-1.76, -0.9, 1.5), (0.6, 0.6, 0.56), bev=0.01)
    sky, ss = SKY["dawn" if light == "dawn" else ("day" if light == "day" else "night")]
    glow("kl_win", (0.02, 0.9, 0.9), (-1.73, -0.9, 1.5), sky, ss * 0.8)
    cb("kl_curtain", (0.05, 0.4, 1.2), (-1.7, -1.25, 1.45), (0.25, 0.30, 0.45), bev=0.03)
    cyl("kl_clock", 0.12, 0.03, (0.0, 1.93, 2.15), (0.85, 0.85, 0.82), rot=(90, 0, 0))
    cb("kl_ch1", (0.01, 0.01, 0.08), (0.0, 1.91, 2.18), (0.02, 0.02, 0.02)); cb("kl_ch2", (0.06, 0.01, 0.01), (0.03, 1.91, 2.15), (0.02, 0.02, 0.02))
    if light == "night":
        lib.world((0.004, 0.005, 0.009), 1.0)
        lib.area_light("kl_moon", (-1.6, -0.9, 1.6), (0.5, 0.5, 0.4), 18, 0.8, (0.45, 0.55, 0.95))
    elif light == "dawn":
        lib.world((0.02, 0.025, 0.035), 1.0)
        lib.area_light("kl_dawn", (-1.6, -0.9, 1.6), (0.5, 0.5, 0.4), 90, 0.8, (0.7, 0.78, 1.0))
    else:
        lib.world((0.05, 0.05, 0.06), 1.0)
        lib.area_light("kl_day", (-1.6, -0.9, 1.6), (0.5, 0.5, 0.4), 160, 0.8, (1.0, 0.95, 0.88))
        tube("kl_tube", (0.0, 0.0, 2.75), on=0.6, power=14)
    cams = {"wide": ((1.25, -1.75, 1.6), (-0.3, 1.2, 0.8), 26), "desk": ((0.1, 0.35, 1.35), (0.85, 1.6, 0.9), 34),
            "shelf": ((0.6, 0.7, 1.45), (0.85, 1.85, 1.62), 34), "door": ((-0.6, 1.2, 1.5), (1.75, -0.6, 1.1), 28),
            "bed": ((0.5, -0.6, 1.2), (-1.25, 0.9, 0.6), 30), "back": ((0.9, 0.2, 1.65), (0.85, 1.55, 0.8), 30)}
    marks = {"chair": ((0.85, 1.02, -0.06), R(180)), "door": ((1.25, -1.0, 0), R(90)), "mid": ((0.2, 0.2, 0), R(160)),
             "bed": ((-1.2, 0.6, 0.12), R(-90))}
    return cams, marks


# =================================================================== 8. the canteen (day)
def kantin(extras_tables=True):
    cb("kn_floor", (12, 10, 0.08), (0, 2, -0.04), lib.tile_floor("kn_tiles", 0.5, (0.50, 0.46, 0.40), (0.42, 0.38, 0.33)), bev=0.005)
    cb("kn_roof", (12, 10, 0.12), (0, 2, 3.2), (0.42, 0.24, 0.12), bev=0.02)
    for x in (-5.5, -1.8, 1.8, 5.5):
        for y in (-2.5, 6.5):
            cyl(f"kn_pil{x}{y}", 0.1, 3.2, (x, y, 1.6), (0.75, 0.73, 0.66))
    # stall counter at the back
    cb("kn_counter", (6.0, 0.7, 1.0), (0, 6.0, 0.5), (0.20, 0.42, 0.40), bev=0.03)
    cb("kn_counter_t", (6.1, 0.8, 0.05), (0, 6.0, 1.02), (0.72, 0.70, 0.64), bev=0.01)
    cb("kn_board", (2.6, 0.06, 0.9), (0, 6.6, 2.1), (0.08, 0.10, 0.08), bev=0.02)
    for i, t in enumerate(("NASI SAYUR   5K", "SOTO          8K", "ES TEH        3K", "KOPI HITAM    4K")):
        ftext(f"kn_menu{i}", t, (-1.1, 6.56, 2.38 - i * 0.18), 0.11, (0.85, 0.85, 0.80), kind="mono", rot=(90, 0, 0))
    for k in range(5):
        cyl(f"kn_jar{k}", 0.09, 0.25, (-2.3 + k * 0.4, 5.85, 1.17), (0.75, 0.70, 0.55))
    # tables and benches (long axis along X)
    for i, (x, y) in enumerate(((0, 1.0), (-3.6, 1.0), (3.6, 1.0), (-3.6, 3.6), (3.6, 3.6), (0, 3.6))):
        cb(f"kn_t{i}", (2.0, 0.8, 0.05), (x, y, 0.74), (0.72, 0.70, 0.64), bev=0.01)
        cb(f"kn_tl{i}", (1.8, 0.1, 0.72), (x, y, 0.36), (0.25, 0.25, 0.27), bev=0.01)
        for s in (-1, 1):
            cb(f"kn_b{i}{s}", (2.0, 0.3, 0.05), (x, y + s * 0.62, 0.44), (0.35, 0.22, 0.10), bev=0.01)
            cb(f"kn_bl{i}{s}", (1.8, 0.08, 0.42), (x, y + s * 0.62, 0.21), (0.25, 0.25, 0.27), bev=0.01)
    # on the main table: two glasses of tea, a plate, Laras's notebook
    cyl("kn_tea1", 0.04, 0.12, (-0.35, 0.82, 0.83), (0.55, 0.25, 0.06)); cyl("kn_tea2", 0.04, 0.12, (0.45, 1.2, 0.83), (0.55, 0.25, 0.06))
    cyl("kn_cup", 0.045, 0.09, (0.2, 0.78, 0.815), (0.85, 0.85, 0.82)); cyl("kn_kopi", 0.04, 0.004, (0.2, 0.78, 0.86), (0.03, 0.015, 0.008))
    cb("kn_book", (0.22, 0.3, 0.015), (0.0, 0.95, 0.775), (0.80, 0.78, 0.70), rot=(0, 0, 8), bev=0.004, dents=0.3)
    for k in range(6):
        cb(f"kn_bookl{k}", (0.15, 0.003, 0.001), (0.0, 1.05 - k * 0.035, 0.784), INK, rot=(0, 0, 8), bev=0.0, dents=0.0)
    for i, x in enumerate((-7, 7)):
        clay.blob(f"kn_tree{i}", (x, 4, 2.5), (1.6, 1.6, 2.2), C((0.10, 0.22, 0.07), 1.6))
        cyl(f"kn_trunk{i}", 0.15, 2.0, (x, 4, 1.0), (0.15, 0.1, 0.06))
    lib.world((0.60, 0.68, 0.80), 1.0)
    lib.sun("kn_sun", (-0.5, 0.4, -0.7), 2.6, (1.0, 0.94, 0.84), 3.0)
    lib.area_light("kn_bounce", (0, -1.5, 2.8), (0, 1.5, 0.8), 260, 4.0, (1.0, 0.95, 0.85))
    cams = {"wide": ((2.6, -2.8, 1.7), (-0.2, 1.4, 0.8), 28), "two": ((1.7, 0.95, 1.25), (-0.5, 0.95, 0.95), 30),
            "book": ((0.12, 0.62, 1.15), (0.0, 0.97, 0.78), 45), "table": ((-1.2, -0.6, 1.2), (0.2, 1.0, 0.85), 30)}
    marks = {"laras": ((-0.1, 0.38, -0.02), R(180)), "dimas": ((0.15, 1.62, -0.02), R(0)),
             "ex1": ((-3.6, 0.38, -0.02), R(180)), "ex2": ((-3.3, 1.62, -0.02), R(0)), "ex3": ((3.4, 3.0, -0.02), R(180)),
             "ex4": ((3.8, 4.22, -0.02), R(0)), "ex5": ((0.4, 3.0, -0.02), R(180)), "ibukos": ((1.6, -1.2, 0), R(150))}
    return cams, marks


# =================================================================== 9. the lecturer's office (day)
def ruang_dosen():
    cb("rd_floor", (4.4, 4.4, 0.06), (0, 0, -0.03), lib.tile_floor("rd_tiles", 0.4, (0.55, 0.52, 0.46), (0.47, 0.44, 0.38)), bev=0.005)
    cb("rd_ceil", (4.4, 4.4, 0.06), (0, 0, 2.9), (0.6, 0.6, 0.57), bev=0.005)
    wc = (0.60, 0.58, 0.50)
    cb("rd_back", (4.4, 0.12, 2.9), (0, 2.2, 1.45), wc); cb("rd_left", (0.12, 4.4, 2.9), (-2.2, 0, 1.45), wc)
    cb("rd_right", (0.12, 4.4, 2.9), (2.2, 0, 1.45), wc); cb("rd_front", (4.4, 0.12, 2.9), (0, -2.2, 1.45), wc)
    table("rd_desk", (0, 1.0, 0), size=(1.6, 0.8), h=0.76, color=(0.30, 0.17, 0.08))
    for k in range(4):
        cb(f"rd_pile{k}", (0.24, 0.32, 0.05 + 0.03 * k), (-0.55 + 0.12 * k, 1.15 + 0.03 * k, 0.78 + 0.025 + 0.015 * k), (0.80, 0.78, 0.72),
           rot=(0, 0, random.Random(k).uniform(-10, 10)), bev=0.004, dents=0.3)
    cb("rd_name", (0.32, 0.06, 0.08), (0.3, 0.68, 0.81), (0.10, 0.08, 0.06), rot=(-20, 0, 0), bev=0.01)
    ftext("rd_name_t", "Dr. Suryo", (0.3, 0.645, 0.815), 0.032, (0.85, 0.75, 0.45), kind="typeb", rot=(70, 0, 0), align="CENTER")
    cb("rd_draft", (0.22, 0.30, 0.012), (0.15, 0.8, 0.79), (0.82, 0.80, 0.75), rot=(0, 0, 175), bev=0.003, dents=0.2)
    for k in range(4):
        cb(f"rd_red{k}", (0.15, 0.004, 0.001), (0.15, 0.88 - k * 0.04, 0.797), RED, rot=(0, 0, 175 + 4 * k), bev=0.0, dents=0.0)
    wchair("rd_chair_d", (0, 1.62, 0), rot_z=0, color=(0.08, 0.08, 0.09))
    wchair("rd_chair_m", (0.0, 0.25, 0), rot_z=180, color=(0.2, 0.12, 0.06))
    for i, x in enumerate((-1.6, 1.6)):
        bookcase(f"rd_bc{i}", (x, 2.0, 0), w=0.9, h=2.1, d=0.3, rot_z=0, tidy=True, seed=60 + i, shelves=5)
    louver_window("rd_win", -2.13, 0.0, 0.9, 1.2, 1.6, SKY["day"][0], 2.0, inner=-1)
    lib.area_light("rd_sun", (-2.5, 0.0, 1.8), (0.5, 0.8, 0.5), 300, 1.2, (1.0, 0.96, 0.88))
    tube("rd_tube", (0.0, 0.5, 2.85), on=0.8, power=16)
    lib.world((0.06, 0.06, 0.065), 1.0)
    cams = {"wide": ((1.6, -1.6, 1.6), (-0.1, 1.1, 0.95), 28), "desk": ((0.6, 0.15, 1.3), (0.0, 1.0, 0.85), 34),
            "over": ((-0.8, -0.6, 1.45), (0.05, 1.6, 1.0), 32)}
    marks = {"dosen": ((0, 1.62, -0.08), R(0)), "laras": ((0.0, 0.25, -0.08), R(180)), "laras_stand": ((0.25, 0.1, 0), R(175))}
    return cams, marks


# =================================================================== 10. corridor, ground floor (where Pak Karto sweeps)
def koridor_k(light="dusk"):
    L = 16.0
    cb("kk_floor", (3.0, L + 1, 0.06), (0, L / 2, -0.03), lib.tile_floor("kk_tiles", 0.4, (0.46, 0.42, 0.34), (0.20, 0.18, 0.15)), bev=0.005)
    cb("kk_ceil", (3.0, L + 1, 0.08), (0, L / 2, 3.1), (0.45, 0.44, 0.40), bev=0.005)
    wc = lib.grime_wall("kk_wall", (0.60, 0.57, 0.48), (0.30, 0.28, 0.22))
    cb("kk_wR", (0.14, L + 1, 3.1), (1.57, L / 2, 1.55), wc, bev=0.01)
    cb("kk_wB", (3.2, 0.14, 3.1), (0, -0.5, 1.55), wc, bev=0.01)
    cb("kk_wE", (3.2, 0.14, 3.1), (0, L + 0.5, 1.55), wc, bev=0.01)
    # open side (left) with low wall and pillars onto the courtyard
    cb("kk_low", (0.2, L + 1, 0.8), (-1.5, L / 2, 0.4), (0.55, 0.52, 0.44), bev=0.02)
    for k in range(6):
        cb(f"kk_pil{k}", (0.25, 0.25, 3.1), (-1.5, k * 3.2, 1.55), (0.60, 0.57, 0.48), bev=0.02)
    sky, ss = SKY[light]
    glow("kk_sky", (0.05, L + 6, 3.0), (-6, L / 2, 2.0), sky, ss * 0.9)
    clay.blob("kk_court", (-4, L / 2, 0.2), (2.0, L / 2, 0.4), C((0.12, 0.2, 0.07), 1.6))
    lib.area_light("kk_sun", (-4.0, 6.0, 2.4), (1.0, 7.0, 0.5), 520 if light == "dusk" else 120, 4.0,
                   (1.0, 0.55, 0.28) if light == "dusk" else (0.45, 0.55, 0.9))
    # classroom doors on the right, notice board
    for i, y in enumerate((2.0, 6.0, 10.0)):
        door(f"kk_d{i}", (1.5, y + 0.45, 0), 90 + 180, color=(0.30, 0.18, 0.08), w=0.9, number=f"C{1}0{i + 1}")
    cb("kk_board", (0.04, 1.6, 0.9), (1.49, 4.0, 1.5), (0.40, 0.28, 0.14), bev=0.01)
    rnd = random.Random(2)
    for k in range(7):
        cb(f"kk_flyer{k}", (0.012, 0.22, 0.3), (1.465, 3.4 + k * 0.18, 1.45 + rnd.uniform(-0.25, 0.25)),
           rnd.choice([(0.8, 0.8, 0.75), (0.85, 0.75, 0.3), (0.7, 0.3, 0.3), (0.4, 0.6, 0.8)]), rot=(rnd.uniform(-6, 6), 0, 0), bev=0.002)
    cb("kk_bench", (0.4, 1.4, 0.05), (1.25, 8.0, 0.45), (0.30, 0.18, 0.08)); cb("kk_bench_l", (0.36, 1.3, 0.42), (1.25, 8.0, 0.21), (0.1, 0.1, 0.1))
    # the stairwell opening at the far end (dark)
    cb("kk_stairhole", (1.4, 0.05, 2.4), (0.3, L + 0.42, 1.2), (0.005, 0.005, 0.006), bev=0.01)
    ftext("kk_up", "TANGGA  >", (0.3, L + 0.4, 2.6), 0.12, (0.85, 0.82, 0.70), kind="typeb", rot=(90, 0, 180), align="CENTER")
    for i, y in enumerate((3.0, 9.0, 14.0)):
        tube(f"kk_tube{i}", (0.3, y, 3.04), on=0.0 if light == "dusk" and i < 2 else 0.6, power=18)
    lib.world((0.01, 0.01, 0.014), 1.0)
    cams = {"long": ((0.6, 0.4, 1.4), (0.1, L, 1.1), 28), "two": ((-1.1, 5.4, 1.4), (0.1, 7.8, 0.95), 28),
            "end": ((0.0, 9.0, 1.45), (0.3, L + 0.4, 1.3), 30), "low": ((0.9, 3.0, 0.3), (0.0, 9.0, 0.9), 24)}
    marks = {"karto": ((0.35, 8.2, 0), R(150)), "laras": ((-0.35, 7.3, 0), R(-30)), "laras_walk0": ((0.2, 1.5, 0), R(180)),
             "laras_walk1": ((0.0, 6.8, 0), R(180))}
    return cams, marks


# =================================================================== 11. thesis defence room
def sidang():
    cb("sd_floor", (6, 5, 0.06), (0, 0.5, -0.03), (0.30, 0.22, 0.16), bev=0.005)
    cb("sd_ceil", (6, 5, 0.06), (0, 0.5, 3.0), (0.6, 0.6, 0.57), bev=0.005)
    wc = (0.62, 0.62, 0.58)
    cb("sd_back", (6, 0.12, 3.0), (0, 3.0, 1.5), wc); cb("sd_left", (0.12, 5, 3.0), (-3.0, 0.5, 1.5), wc)
    cb("sd_right", (0.12, 5, 3.0), (3.0, 0.5, 1.5), wc); cb("sd_front", (6, 0.12, 3.0), (0, -2.0, 1.5), wc)
    # projector screen on the back wall with the title slide
    cb("sd_screen", (2.2, 0.03, 1.3), (0, 2.92, 1.75), (0.85, 0.85, 0.85), bev=0.005)
    glow("sd_slide", (2.0, 0.01, 1.15), (0, 2.90, 1.75), (0.75, 0.78, 0.82), 1.4)
    ftext("sd_s1", "SIDANG SKRIPSI", (0, 2.88, 2.12), 0.13, (0.05, 0.08, 0.30), kind="typeb", rot=(90, 0, 0), align="CENTER")
    ftext("sd_s2", "LARAS PRAMESTI", (0, 2.88, 1.62), 0.09, (0.02, 0.02, 0.02), kind="type", rot=(90, 0, 0), align="CENTER")
    ftext("sd_s3", "Pembimbing: Dr. Suryo", (0, 2.88, 1.42), 0.06, (0.02, 0.02, 0.02), kind="type", rot=(90, 0, 0), align="CENTER")
    # examiners' long table (facing +Y toward the screen side? no: examiners sit at the front, facing the candidate)
    cb("sd_table", (3.0, 0.8, 0.05), (0, -0.6, 0.74), (0.30, 0.17, 0.08), bev=0.01)
    cb("sd_skirt", (3.0, 0.05, 0.65), (0, -0.22, 0.42), (0.10, 0.18, 0.35), bev=0.01)
    for k, x in enumerate((-1.0, 0.0, 1.0)):
        cb(f"sd_doc{k}", (0.22, 0.30, 0.02), (x, -0.5, 0.775), (0.82, 0.80, 0.75), bev=0.003, dents=0.2)
        cyl(f"sd_glass{k}", 0.035, 0.11, (x + 0.25, -0.45, 0.82), (0.75, 0.82, 0.85))
    cb("sd_podium", (0.6, 0.45, 1.05), (0.9, 1.9, 0.525), (0.30, 0.17, 0.08), bev=0.02)
    tube("sd_tube", (0.0, 0.5, 2.95), on=1.0, power=22)
    lib.world((0.06, 0.06, 0.065), 1.0)
    cams = {"wide": ((2.4, -1.7, 1.75), (-0.3, 1.5, 1.0), 26), "panel": ((0.3, 1.4, 1.25), (0.0, -1.0, 0.95), 30),
            "laras": ((-0.2, -0.3, 1.2), (0.3, 1.9, 1.05), 34), "screen": ((0.0, 0.6, 1.6), (0.0, 2.9, 1.75), 40)}
    marks = {"p1": ((-1.0, -1.02, -0.08), R(180)), "p2": ((0.0, -1.02, -0.08), R(180)), "p3": ((1.0, -1.02, -0.08), R(180)),
             "laras": ((0.3, 1.6, 0), R(0)), "p1s": ((-0.8, 0.55, 0), R(160)), "p2s": ((-0.1, 0.65, 0), R(180)),
             "p3s": ((0.7, 0.62, 0), R(200)), "laras_s": ((0.2, 1.35, 0), R(0))}
    return cams, marks


# =================================================================== 12. graduation (day, outside)
def wisuda():
    cb("ws_ground", (40, 40, 0.2), (0, 5, -0.1), C((0.16, 0.26, 0.08), 1.8, 0.9), bev=0.02)
    cb("ws_paving", (8, 10, 0.03), (0, 2, 0.0), (0.45, 0.43, 0.40), bev=0.01)
    cb("ws_back", (7, 0.2, 2.8), (0, 5.5, 1.4), (0.08, 0.20, 0.45), bev=0.03)
    ftext("ws_t1", "WISUDA SARJANA", (0, 5.38, 2.2), 0.42, (0.95, 0.85, 0.5), kind="typeb", rot=(90, 0, 0), align="CENTER")
    ftext("ws_t2", "Selamat & Sukses", (0, 5.38, 1.6), 0.28, (0.95, 0.95, 0.95), kind="script", rot=(90, 0, 0), align="CENTER")
    rnd = random.Random(9)
    for i in range(14):
        x, y = rnd.uniform(-3.4, 3.4), 5.35
        clay.blob(f"ws_bal{i}", (x, y - 0.1, 2.9 + rnd.uniform(0, 0.4)), (0.13, 0.13, 0.16),
                  C(rnd.choice([(0.9, 0.85, 0.85), (0.85, 0.65, 0.1), (0.1, 0.25, 0.6)]), 0.2))
    for i, x in enumerate((-4.2, 4.2)):
        clay.blob(f"ws_bush{i}", (x, 4.5, 0.6), (1.0, 0.8, 0.8), C((0.08, 0.2, 0.06), 1.6))
        cb(f"ws_flower{i}", (0.6, 0.6, 1.0), (x * 0.8, 4.9, 0.5), (0.85, 0.85, 0.82), bev=0.05)
    lib.world((0.62, 0.70, 0.82), 1.0)
    lib.sun("ws_sun", (-0.4, 0.5, -0.65), 3.4, (1.0, 0.93, 0.82), 3.0)
    cams = {"wide": ((0.9, -2.6, 1.5), (0, 2.6, 1.05), 30), "two": ((0.35, 0.65, 1.3), (-0.07, 2.35, 0.95), 36),
            "back": ((-1.6, 4.2, 1.5), (0.3, 1.5, 1.0), 30)}
    marks = {"laras": ((0.10, 2.35, 0), R(-90)), "ibu": ((-0.24, 2.35, 0), R(90)), "g1": ((-2.5, 3.2, 0), R(200)),
             "g2": ((-2.0, 3.7, 0), R(150)), "g3": ((2.6, 3.4, 0), R(160)), "g4": ((3.1, 2.8, 0), R(210))}
    return cams, marks


# =================================================================== 13. memory: the village yard at dusk
def kampung():
    cb("kp_ground", (30, 30, 0.2), (0, 5, -0.1), C((0.30, 0.22, 0.12), 1.8, 0.9), bev=0.02)
    cb("kp_house", (6, 4, 2.8), (0, 6.5, 1.4), (0.62, 0.58, 0.46), bev=0.05)
    cb("kp_roof", (6.8, 4.6, 0.5), (0, 6.5, 3.0), (0.40, 0.14, 0.07), bev=0.1)
    cb("kp_roof2", (6.2, 3.0, 1.0), (0, 6.5, 3.5), (0.42, 0.15, 0.08), bev=0.3)
    cb("kp_door", (1.0, 0.08, 2.1), (0, 4.47, 1.05), (0.20, 0.10, 0.04), bev=0.02)
    glow("kp_doorg", (0.9, 0.03, 2.0), (0, 4.42, 1.0), (1.0, 0.75, 0.42), 4.0)
    lib.point_light("kp_doorl", (0, 4.2, 1.6), 60, (1.0, 0.7, 0.4), 0.2)
    for s in (-1, 1):
        cb(f"kp_win{s}", (0.8, 0.08, 0.8), (s * 1.9, 4.47, 1.6), (0.45, 0.40, 0.30), bev=0.02)
        glow(f"kp_wing{s}", (0.7, 0.03, 0.7), (s * 1.9, 4.42, 1.6), (1.0, 0.72, 0.40), 2.0)
    cb("kp_teras", (6, 1.6, 0.25), (0, 3.7, 0.125), (0.50, 0.46, 0.40), bev=0.02)
    for i, (x, y) in enumerate(((-5, 3), (5.5, 5), (-7, 9))):
        cyl(f"kp_coco{i}", 0.13, 6, (x, y, 3), (0.30, 0.22, 0.14), rot=(0, 6 * (i - 1), 0))
        for k in range(6):
            cb(f"kp_frond{i}{k}", (2.0, 0.3, 0.05), (x + math.cos(R(60 * k)) * 0.9, y + math.sin(R(60 * k)) * 0.9, 6.0), (0.12, 0.22, 0.06),
               rot=(0, -25, 60 * k), bev=0.02)
    glow("kp_sky", (60, 0.1, 30), (0, 30, 8), (1.0, 0.45, 0.15), 1.4)
    lib.world((0.55, 0.30, 0.15), 1.0)
    lib.sun("kp_sun", (0.3, 0.6, -0.25), 2.4, (1.0, 0.55, 0.25), 2.0)
    cams = {"wide": ((1.2, -4.0, 1.3), (0, 4.4, 1.3), 30), "door": ((0.4, 0.6, 1.2), (0, 4.4, 1.15), 40),
            "low": ((-0.8, -1.8, 0.5), (0.0, 4.4, 1.4), 26)}
    marks = {"ibu": ((0.0, 4.25, 0.25), R(0)), "kecil": ((0.4, 1.2, 0), R(170))}
    return cams, marks


# =================================================================== 14. black void with one desk (the ending, the viewer)
def meja_kosong(name_blank=True):
    cb("mk_floor", (12, 12, 0.06), (0, 0, -0.03), (0.02, 0.02, 0.022), bev=0.005)
    table("mk_desk", (0, 0, 0), size=(1.25, 0.72), h=0.78, color=(0.22, 0.12, 0.055))
    wchair("mk_chair", (0.15, -0.75, 0), rot_z=25)
    cb("mk_stack", (0.30, 0.42, 0.04), (-0.05, -0.02, 0.80), (0.82, 0.80, 0.75), rot=(0, 0, -4), bev=0.004, dents=0.3)
    ftext("mk_t1", "SKRIPSI", (-0.05, 0.12, 0.8215), 0.022, INK, kind="typeb", align="CENTER", rot=(0, 0, -4))
    ftext("mk_t2", "Disusun oleh:", (-0.055, -0.02, 0.8215), 0.012, INK, kind="type", align="CENTER", rot=(0, 0, -4))
    ftext("mk_t3", "....................................", (-0.057, -0.05, 0.8215), 0.012, INK, kind="type", align="CENTER", rot=(0, 0, -4))
    cyl("mk_pen", 0.0065, 0.15, (0.22, -0.12, 0.787), RED, rot=(0, 90, 35))
    lamp_green("mk_lamp", (0.4, 0.2, 0.78), power=34, on=True)
    lib.world((0.0, 0.0, 0.0), 1.0)
    cams = {"wide": ((0.0, -3.2, 1.6), (0, 0, 0.75), 30), "chair": ((-0.9, -1.6, 1.0), (0.1, -0.2, 0.75), 30),
            "paper": ((-0.04, -0.2, 1.15), (-0.05, -0.02, 0.8), 45)}
    return cams, {"behind": ((0.0, 0.85, 0), R(0))}
