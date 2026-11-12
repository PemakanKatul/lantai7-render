"""Clay-miniature locations for "Bangsal Melati" (old Dutch-era psychiatric hospital, Central Java).
Same conventions as sets.py: every builder returns ({cam: (loc, target, lens)}, {mark: (loc, rot_z)}).
Characters face -Y at rot 0. ~1.45 m tall.
"""
import math, random
import bpy
from mathutils import Vector
import lib, clay
from sets import C, cb, cyl, glow, text, door, tube

R = math.radians
WALL_HI = (0.50, 0.50, 0.44)      # off-white plaster
WALL_LO = (0.07, 0.17, 0.12)      # old hospital green
IRON = (0.05, 0.05, 0.055)
RUST = (0.20, 0.08, 0.04)


def spot(name, loc, target, power, angle=40, blend=0.5, color=(1, 1, 1), radius=0.03):
    d = bpy.data.lights.new(name, "SPOT")
    d.energy = power; d.spot_size = R(angle); d.spot_blend = blend; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    lib.aim(o, target)
    return o


def bars(name, x, y0, z0, w, h, along="y", n=6):
    for i in range(n):
        t = (i + 0.5) / n
        p = (x, y0 + t * w, z0 + h / 2) if along == "y" else (y0 + t * w, x, z0 + h / 2)
        cyl(f"{name}_bar{i}", 0.012, h, p, IRON)


def window(name, x, yc, z0=1.0, w=1.0, h=1.7, side=-1, sky=(0.10, 0.16, 0.30), sky_str=0.35, along="y"):
    """tall barred window set into a wall at x (along y) or at y (along x)"""
    if along == "y":
        cb(name + "_sill", (0.22, w + 0.16, 0.06), (x, yc, z0 - 0.03), (0.55, 0.53, 0.47), bev=0.01)
        glow(name + "_sky", (0.03, w, h), (x + side * 0.05, yc, z0 + h / 2), sky, sky_str)
        cb(name + "_fv", (0.06, 0.05, h), (x, yc, z0 + h / 2), (0.30, 0.27, 0.20), bev=0.01)
        cb(name + "_fh", (0.06, w, 0.05), (x, yc, z0 + h * 0.62), (0.30, 0.27, 0.20), bev=0.01)
        bars(name, x - side * 0.04, yc - w / 2, z0, w, h)
    else:
        cb(name + "_sill", (w + 0.16, 0.22, 0.06), (yc, x, z0 - 0.03), (0.55, 0.53, 0.47), bev=0.01)
        glow(name + "_sky", (w, 0.03, h), (yc, x + side * 0.05, z0 + h / 2), sky, sky_str)
        cb(name + "_fv", (0.05, 0.06, h), (yc, x, z0 + h / 2), (0.30, 0.27, 0.20), bev=0.01)
        cb(name + "_fh", (w, 0.06, 0.05), (yc, x, z0 + h * 0.62), (0.30, 0.27, 0.20), bev=0.01)
        bars(name, x - side * 0.04, yc - w / 2, z0, w, h, along="x")


def two_tone_wall(name, size, loc, along="y"):
    """plaster wall, lower 1.1 m painted green (size = full wall box)"""
    sx, sy, sz = size
    cb(name, size, loc, lib.grime_wall(name + "_m", WALL_HI, (0.26, 0.24, 0.18)), bev=0.01)
    lo = (sx + 0.01, sy, 1.1) if along == "y" else (sx, sy + 0.01, 1.1)
    cb(name + "_lo", lo, (loc[0], loc[1], 0.55), lib.grime_wall(name + "_lm", WALL_LO, (0.03, 0.06, 0.04)), bev=0.01)
    stripe = (sx + 0.02, sy, 0.04) if along == "y" else (sx, sy + 0.02, 0.04)
    cb(name + "_st", stripe, (loc[0], loc[1], 1.12), (0.03, 0.08, 0.05), bev=0.005)


def iron_bed(name, loc, rot_z=0, mattress=(0.62, 0.62, 0.56), rusty=False, sheet=None):
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = name
    col = RUST if rusty else (0.40, 0.42, 0.42)
    parts = []
    for sx in (-0.45, 0.45):
        for sy in (-0.95, 0.95):
            parts.append(cyl(f"{name}_leg{sx}{sy}", 0.02, 0.55, (sx, sy, 0.275), col))
    for sy, h in ((-0.95, 0.85), (0.95, 1.05)):
        parts.append(cyl(f"{name}_post{sy}", 0.022, h, (-0.45, sy, h / 2), col)); parts.append(cyl(f"{name}_postb{sy}", 0.022, h, (0.45, sy, h / 2), col))
        parts.append(cyl(f"{name}_rail{sy}", 0.018, 0.9, (0, sy, h - 0.03), col, rot=(0, 90, 0)))
        for k in range(4):
            parts.append(cyl(f"{name}_sp{sy}{k}", 0.01, h - 0.45, (-0.27 + k * 0.18, sy, 0.45 + (h - 0.45) / 2), col))
    parts.append(cb(f"{name}_frame", (0.94, 1.94, 0.05), (0, 0, 0.42), col, bev=0.01))
    parts.append(cb(f"{name}_mat", (0.86, 1.86, 0.14), (0, 0, 0.51), mattress, bev=0.05))
    if sheet:
        parts.append(cb(f"{name}_sheet", (0.88, 1.2, 0.05), (0, -0.3, 0.6), sheet, bev=0.03))
        parts.append(cb(f"{name}_pil", (0.6, 0.32, 0.1), (0, 0.72, 0.62), (0.70, 0.70, 0.66), bev=0.05))
    for o in parts:
        o.parent = root
    return root


def wheelchair(name, loc, rot_z=0):
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = name
    ps = [cb(name + "_seat", (0.46, 0.44, 0.05), (0, 0, 0.5), (0.10, 0.07, 0.06)),
          cb(name + "_back", (0.46, 0.05, 0.45), (0, 0.22, 0.76), (0.10, 0.07, 0.06))]
    for sx in (-0.27, 0.27):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.018, location=(sx, 0.05, 0.3), rotation=(0, R(90), 0))
        t = bpy.context.object; t.name = f"{name}_wh{sx}"; t.data.materials.append(C(RUST, 0.4)); ps.append(t)
        ps.append(cyl(f"{name}_arm{sx}", 0.015, 0.45, (sx * 0.9, 0.0, 0.68), RUST, rot=(90, 0, 0)))
        ps.append(cyl(f"{name}_fr{sx}", 0.06, 0.03, (sx * 0.7, -0.32, 0.06), IRON, rot=(0, 90, 0)))
    for o in ps:
        o.parent = root
    return root


def chain(name, a, b, links=None, broken=False):
    """iron chain from a to b (torus links); broken = a gap in the middle"""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    n = links or max(4, int(L / 0.07))
    d = (b - a).normalized()
    m = C((0.10, 0.09, 0.08), 0.3, 0.35)
    objs = []
    for i in range(n):
        if broken and abs(i - n // 2) < 1:
            continue
        p = a + d * (i + 0.5) * L / n
        bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.009, location=p)
        t = bpy.context.object; t.name = f"{name}{i}"
        t.rotation_euler = d.to_track_quat("X", "Z").to_euler()
        t.rotation_euler.rotate_axis("X", R(90 * (i % 2)))
        t.data.materials.append(m); objs.append(t)
    return objs


def padlock(name, loc):
    cb(name, (0.09, 0.04, 0.10), loc, (0.32, 0.26, 0.08), bev=0.02)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.007, location=(loc[0], loc[1], loc[2] + 0.06), rotation=(R(90), 0, 0))
    t = bpy.context.object; t.name = name + "_sh"; t.data.materials.append(C((0.3, 0.3, 0.3), 0.2, 0.3))


def scratches(name, center, size, normal_axis, count, seed=1, color=(0.06, 0.04, 0.03), zmax=1.25):
    """fingernail scratches on a wall plane. normal_axis 'x' (wall at x) or 'y'."""
    rnd = random.Random(seed)
    m = C(color, 0.2, 0.7)
    m2 = C((0.20, 0.06, 0.04), 0.2, 0.6)
    cx, cy, cz = center
    w, h = size
    meshes = []
    for i in range(count):
        u = rnd.uniform(-w / 2, w / 2)
        z = rnd.uniform(0.05, min(zmax, h))
        ln = rnd.uniform(0.07, 0.30)
        ang = rnd.uniform(-35, 35) + (rnd.random() < 0.3) * rnd.choice((-60, 60))
        for k in range(rnd.choice((1, 3, 4))):          # 4 fingers side by side
            off = (k - 1.5) * 0.018
            if normal_axis == "x":
                loc = (cx, cy + u + off, z)
                o = lib.box(f"{name}{i}_{k}", (0.003, 0.0045, ln), loc, m2 if rnd.random() < 0.12 else m, rot=(R(ang), 0, 0))
            else:
                loc = (cx + u + off, cy, z)
                o = lib.box(f"{name}{i}_{k}", (0.003, 0.0045, ln), loc, m2 if rnd.random() < 0.12 else m, rot=(0, R(ang), 0))
            meshes.append(o)
    # join for speed
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    meshes[0].name = name
    return meshes[0]


def mahogany(name, x, y, h=7.0, seed=0):
    rnd = random.Random(seed)
    cyl(name + "_t", 0.32, h, (x, y, h / 2), (0.10, 0.06, 0.035))
    m = C((0.025, 0.05, 0.025), 1.8, 0.8)
    for k in range(5):
        clay.blob(f"{name}_c{k}", (x + rnd.uniform(-1.4, 1.4), y + rnd.uniform(-1.2, 1.2), h + rnd.uniform(-0.6, 1.4)),
                  (rnd.uniform(1.6, 2.4), rnd.uniform(1.5, 2.2), rnd.uniform(1.1, 1.6)), m, seg=24)


# =================================================================== 1. exterior: hospital on the hillside
def rs_ext(night=True, rain=True, car=False):
    g = C((0.05, 0.07, 0.04) if night else (0.12, 0.17, 0.08), 1.6, 0.9)
    cb("e_ground", (240, 240, 0.2), (0, 40, -0.1), g, bev=0.02)
    cb("e_road", (5.0, 70, 0.04), (0, 0, 0.02), (0.06, 0.06, 0.06) if night else (0.16, 0.16, 0.15), bev=0.01)
    # hill behind
    for i, (x, y, r, h) in enumerate(((-30, 90, 40, 22), (25, 100, 45, 30), (0, 120, 60, 40))):
        clay.blob(f"e_hill{i}", (x, y, 0), (r, r * 0.6, h), C((0.02, 0.035, 0.03) if night else (0.10, 0.16, 0.10), 1.4, 0.9), seg=32)
    # the building: long Dutch block with a porch and red tile roof
    wall = (0.42, 0.41, 0.36) if night else (0.62, 0.60, 0.53)
    cb("e_main", (34, 9, 6.5), (0, 44, 3.25), lib.grime_wall("e_wall", wall, (0.20, 0.19, 0.15)), bev=0.08)
    roof = C((0.20, 0.06, 0.03) if night else (0.42, 0.13, 0.06), 1.2, 0.7)
    for s in (-1, 1):
        cb(f"e_roof{s}", (35, 6.2, 0.3), (0, 44 + s * 2.4, 7.6), roof, rot=(s * -33, 0, 0), bev=0.05)
    cb("e_porch_roof", (9, 3.4, 0.25), (0, 38.6, 4.6), roof, bev=0.05)
    for x in (-4, -1.4, 1.4, 4):
        cyl(f"e_col{x}", 0.22, 4.4, (x, 37.3, 2.2), (0.60, 0.58, 0.52) if not night else (0.40, 0.39, 0.35))
    cb("e_step", (9, 2, 0.3), (0, 38.3, 0.15), (0.35, 0.34, 0.30), bev=0.03)
    door("e_door", (-0.9, 39.45, 0), 0, color=(0.12, 0.06, 0.03), w=1.8, h=3.0)
    text("e_sign", "RUMAH SAKIT JIWA", (0, 37.2, 5.15), 0.55, (0.70, 0.66, 0.50) if not night else (0.35, 0.33, 0.26))
    rnd = random.Random(7)
    for i, x in enumerate([-15, -12, -9, -6, 6, 9, 12, 15]):
        for row, z in enumerate((1.2,)):
            lit = night and rnd.random() < 0.3
            glow(f"e_win{i}", (1.3, 0.05, 2.4), (x, 39.47, z + 1.2), (0.65, 0.95, 0.70) if lit else (0.02, 0.025, 0.03),
                 1.5 if lit else 0.2)
            for k in range(5):
                cyl(f"e_wb{i}{k}", 0.025, 2.4, (x - 0.5 + k * 0.25, 39.42, 2.4), IRON)
    # mahogany avenue
    for i, y in enumerate(range(-20, 34, 7)):
        mahogany(f"e_tree{i}a", -5.5, y, 7.5 + (i % 3), i)
        mahogany(f"e_tree{i}b", 5.5, y + 3, 7.0 + (i % 2), i + 30)
    # lamp at the gate
    cyl("e_lamp", 0.08, 4.2, (2.8, 30, 2.1), IRON)
    glow("e_lamp_h", (0.3, 0.3, 0.25), (2.8, 30, 4.3), (1.0, 0.8, 0.5), 8.0 if night else 0.1)
    if night:
        lib.point_light("e_lamp_l", (2.8, 29.6, 4.1), 900, (1.0, 0.72, 0.42), 0.2)
        glow("e_porch_g", (2.0, 0.1, 0.3), (0, 38.0, 4.4), (1.0, 0.85, 0.6), 3.0)
        lib.point_light("e_porch_l", (0, 37.6, 4.2), 400, (1.0, 0.8, 0.55), 0.2)
    if car:
        cb("e_car", (1.8, 4.2, 1.1), (3.5, 22, 0.75), (0.45, 0.45, 0.43), bev=0.35)
        cb("e_cartop", (1.55, 2.2, 0.62), (3.5, 22.2, 1.55), (0.10, 0.11, 0.13), bev=0.25)
    lib.world((0.010, 0.014, 0.028) if night else (0.45, 0.30, 0.20), 1.0)
    lib.sun("moon", (-0.3, 0.7, -0.45), 0.3 if night else 2.6, (0.55, 0.68, 1.0) if night else (1.0, 0.62, 0.35), 2.0)
    lib.fog_volume((-60, -30, 0), (60, 130, 50), 0.006 if night else 0.002, color=(0.7, 0.8, 1.0) if night else (1.0, 0.8, 0.6))
    cams = {"road": ((0.6, -12, 1.4), (0, 40, 4.5), 30), "wide": ((-14, -8, 6), (0, 44, 3), 26),
            "facade": ((3, 26, 1.6), (0, 44, 4.5), 26), "gate": ((-1.5, 18, 1.3), (1.0, 40, 3.0), 35),
            "car": ((-3.0, 13.0, 1.6), (3.0, 22, 1.0), 30)}
    marks = {"gate": ((0.0, 30, 0), 0), "car_side": ((2.1, 21.5, 0), R(-90))}
    return cams, marks


# =================================================================== 2. east-wing corridor
def lorong(length=24.0, chain_state="ok", door_open=0.0, wet=False, lights=1.0, dead=(), night=True):
    """runs along +Y from the nurse-station end (y=0) to Bangsal Melati's doors (y=length). x in [-1.5, 1.5]"""
    cb("l_floor", (3.0, length + 2, 0.06), (0, length / 2 - 1, -0.03),
       lib.tile_floor("l_tiles", 0.38, (0.36, 0.34, 0.28), (0.12, 0.12, 0.11)), bev=0.005)
    if wet:
        m = bpy.data.materials.new("l_wet"); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
        b.inputs["Roughness"].default_value = 0.05; b.inputs["Alpha"].default_value = 0.55
        for i in range(6):
            lib.box(f"l_puddle{i}", (random.Random(i).uniform(0.4, 1.0), random.Random(i + 9).uniform(0.6, 1.6), 0.004),
                    (random.Random(i + 3).uniform(-0.7, 0.7), 4 + i * 3.4, 0.003), m)
    cb("l_ceil", (3.0, length + 2, 0.08), (0, length / 2 - 1, 3.24), (0.30, 0.30, 0.27), bev=0.005)
    two_tone_wall("l_wallL", (0.14, length + 2, 3.2), (-1.57, length / 2 - 1, 1.6))
    two_tone_wall("l_wallR", (0.14, length + 2, 3.2), (1.57, length / 2 - 1, 1.6))
    two_tone_wall("l_back", (3.2, 0.14, 3.2), (0, -2.07, 1.6), along="x")
    # barred windows on the left (night sky), patient doors on the right
    for i, y in enumerate(range(2, int(length) - 2, 4)):
        window(f"l_win{i}", -1.50, y, 1.0, 1.0, 1.7, side=-1, sky=(0.08, 0.12, 0.25) if night else (0.6, 0.65, 0.7),
               sky_str=0.3 if night else 2.0)
        door(f"l_d{i}", (1.5, y + 1.0 + 0.45, 0), 90 + 180, color=(0.30, 0.32, 0.30), w=0.9, number=f"T{i + 1}")
        glow(f"l_dwin{i}", (0.02, 0.22, 0.3), (1.47, y + 1.0, 1.55), (0.02, 0.025, 0.03), 0.1)
    # end wall with Bangsal Melati's double door
    two_tone_wall("l_end", (3.2, 0.14, 3.2), (0, length + 0.07, 1.6), along="x")
    for s, nm in ((-1, "l_bmL"), (1, "l_bmR")):
        door(nm, (s * 0.95, length - 0.02, 0), 0 if s < 0 else 180, color=(0.16, 0.09, 0.05), w=0.92, h=2.3,
             open_deg=door_open if s > 0 else 0)
    cb("l_bm_board", (1.7, 0.05, 0.3), (0, length - 0.06, 2.62), (0.10, 0.08, 0.05), bev=0.02)
    text("l_bm_text", "BANGSAL MELATI", (0, length - 0.1, 2.62), 0.15, (0.72, 0.66, 0.46))
    if chain_state in ("ok", "broken"):
        objs = chain("l_chain", (-0.45, length - 0.09, 1.15), (0.45, length - 0.09, 1.25), broken=False)
        if chain_state == "broken":
            for o in objs:
                o.location = (o.location.x * 0.9, length - 0.4 - abs(o.location.x) * 0.3, 0.02)
            padlock("l_lock", (0.05, length - 0.5, 0.05))
        else:
            padlock("l_lock", (0.0, length - 0.12, 1.12))
    elif chain_state == "welded":
        cb("l_weld", (0.05, 0.04, 2.2), (0, length - 0.08, 1.15), (0.25, 0.22, 0.2), bev=0.01)
    # props: clock, bench, trolley
    cyl("l_clock", 0.17, 0.05, (1.48, -0.6, 2.4), (0.75, 0.73, 0.66), rot=(0, 90, 0))
    cb("l_clock_h1", (0.01, 0.012, 0.11), (1.45, -0.6, 2.44), (0.02, 0.02, 0.02))
    cb("l_clock_h2", (0.01, 0.1, 0.012), (1.45, -0.55, 2.4), (0.02, 0.02, 0.02))
    cb("l_bench", (0.45, 1.6, 0.06), (-1.2, 6.0, 0.45), (0.20, 0.12, 0.06)); cb("l_bench_l", (0.4, 1.5, 0.42), (-1.2, 6.0, 0.21), (0.08, 0.08, 0.08))
    cb("l_trolley", (0.5, 0.8, 0.05), (1.1, 9.5, 0.85), (0.6, 0.6, 0.6)); cb("l_trolley_b", (0.5, 0.8, 0.04), (1.1, 9.5, 0.3), (0.6, 0.6, 0.6))
    i = 0
    for y in range(0, int(length) + 1, 4):
        i += 1
        on = 0.0 if i in dead else lights
        tube(f"lt{i}", (0, y, 3.18), on=on, power=26)
    lib.world((0.003, 0.004, 0.007) if night else (0.2, 0.2, 0.2), 1.0)
    lib.fog_volume((-1.5, -2, 0), (1.5, length, 3.2), 0.015)
    L = length
    cams = {"long": ((0.5, -1.6, 1.35), (-0.2, L, 1.0), 26), "end": ((0.6, L - 6.5, 1.35), (-0.3, L, 1.2), 32),
            "door": ((0.5, L - 2.6, 1.25), (0.0, L, 1.3), 30), "chain": ((0.2, L - 1.2, 1.0), (0.0, L, 0.6), 35),
            "back": ((-0.3, L - 0.7, 1.6), (0.2, 0, 1.0), 26), "low": ((0.9, 2.0, 0.25), (-0.2, L, 1.1), 22),
            "side": ((-1.1, 5.0, 1.4), (1.4, 9.0, 1.1), 30), "clock": ((0.4, 0.8, 1.9), (1.48, -0.6, 2.4), 45)}
    marks = {"start": ((0.0, 0.8, 0), R(180)), "mid": ((0.0, L / 2, 0), R(180)), "near_door": ((0.1, L - 1.6, 0), R(180)),
             "door_out": ((0.2, L - 2.6, 0), 0), "far": ((0.0, L - 0.6, 0), 0)}
    return cams, marks


# =================================================================== 3. nurse station
def jaga(night=True, drawer_open=0.0):
    cb("j_floor", (4.4, 4.4, 0.06), (0, 0, -0.03), lib.tile_floor("j_tiles", 0.38, (0.36, 0.34, 0.28), (0.14, 0.13, 0.12)), bev=0.005)
    cb("j_ceil", (4.4, 4.4, 0.06), (0, 0, 3.0), (0.30, 0.30, 0.27), bev=0.005)
    two_tone_wall("j_back", (4.4, 0.12, 3.0), (0, 2.2, 1.5), along="x")
    two_tone_wall("j_left", (0.12, 4.4, 3.0), (-2.2, 0, 1.5))
    two_tone_wall("j_right", (0.12, 4.4, 3.0), (2.2, 0, 1.5))
    window("j_win", -2.13, 0.6, 1.0, 1.0, 1.6, side=-1)
    cb("j_desk", (1.6, 0.75, 0.06), (0.2, 1.4, 0.76), (0.28, 0.15, 0.07)); cb("j_desk_b", (1.5, 0.6, 0.7), (0.2, 1.55, 0.37), (0.22, 0.12, 0.06))
    cb("j_book", (0.34, 0.24, 0.04), (0.0, 1.25, 0.81), (0.06, 0.20, 0.10)); cb("j_paper", (0.22, 0.3, 0.01), (0.5, 1.3, 0.795), (0.70, 0.68, 0.60))
    cyl("j_lamp_b", 0.08, 0.03, (0.8, 1.55, 0.805), IRON); cyl("j_lamp_s", 0.012, 0.4, (0.8, 1.55, 1.0), IRON)
    cb("j_lamp_h", (0.18, 0.18, 0.12), (0.72, 1.48, 1.2), (0.12, 0.25, 0.15), bev=0.05)
    lib.point_light("j_lamp_l", (0.72, 1.45, 1.08), 40, (1.0, 0.78, 0.5), 0.05)
    # keys board
    cb("j_keyboard", (0.6, 0.04, 0.45), (-0.9, 2.13, 1.6), (0.25, 0.15, 0.07))
    for k in range(5):
        cyl(f"j_key{k}", 0.012, 0.08, (-1.1 + k * 0.1, 2.09, 1.6), (0.55, 0.45, 0.15))
    # filing cabinet with 4 drawers (the bottom one sticks)
    cb("j_cab", (0.6, 0.65, 1.4), (1.6, 0.5, 0.7), (0.30, 0.33, 0.30), bev=0.02)
    for k in range(4):
        z = 0.2 + k * 0.33
        o = cb(f"j_drawer{k}", (0.54, 0.05, 0.3), (1.6 - 0.0, 0.5 - 0.35 - (drawer_open if k == 0 else 0), z), (0.34, 0.37, 0.34), bev=0.01)
        o.rotation_euler.z = R(90)
        o.location = (1.6 - 0.33 - (drawer_open if k == 0 else 0), 0.5, z)
        hd = cb(f"j_handle{k}", (0.03, 0.12, 0.03), (1.6 - 0.37 - (drawer_open if k == 0 else 0), 0.5, z + 0.06), (0.5, 0.5, 0.48))
        mw = hd.matrix_world.copy(); hd.parent = o; bpy.context.view_layer.update(); hd.matrix_world = mw
    door("j_door", (0.45, -2.2, 0), 180, color=(0.30, 0.32, 0.30))
    cyl("j_clock", 0.15, 0.04, (-0.6, 2.14, 2.2), (0.75, 0.73, 0.66), rot=(90, 0, 0))
    tube("j_tube", (0, 0.5, 2.95), on=0.6 if night else 1.0, power=18)
    lib.world((0.004, 0.005, 0.008), 1.0)
    cams = {"wide": ((-1.5, -1.9, 1.6), (0.6, 1.2, 0.9), 26), "desk": ((0.9, 0.2, 1.35), (0.0, 1.4, 0.85), 35),
            "cab": ((-0.5, -0.9, 1.15), (1.4, 0.5, 0.45), 30), "door": ((0.8, 1.8, 1.4), (0.9, -2.2, 1.1), 30)}
    marks = {"desk": ((0.2, 0.75, 0), R(180)), "cab": ((0.85, 0.5, 0), R(-90)), "door": ((0.9, -1.6, 0), R(180)),
             "mid": ((-0.4, 0.2, 0), R(150))}
    return cams, marks


# =================================================================== 4. Pak Harun's room
def kamar_harun():
    cb("h_floor", (3.6, 4.2, 0.06), (0, 0, -0.03), lib.tile_floor("h_tiles", 0.38, (0.36, 0.34, 0.28), (0.14, 0.13, 0.12)), bev=0.005)
    cb("h_ceil", (3.6, 4.2, 0.06), (0, 0, 3.0), (0.30, 0.30, 0.27), bev=0.005)
    two_tone_wall("h_back", (3.6, 0.12, 3.0), (0, 2.1, 1.5), along="x")      # the wall he faces
    two_tone_wall("h_left", (0.12, 4.2, 3.0), (-1.8, 0, 1.5))
    two_tone_wall("h_right", (0.12, 4.2, 3.0), (1.8, 0, 1.5))
    cb("h_stain", (0.9, 0.02, 1.1), (0.4, 2.03, 1.6), (0.18, 0.17, 0.12), bev=0.01)
    iron_bed("h_bed", (0.4, 0.6, 0), 0, sheet=(0.50, 0.56, 0.60))
    window("h_win", -1.73, 0.4, 1.1, 0.8, 1.4, side=-1)
    cb("h_table", (0.45, 0.4, 0.6), (-1.2, 1.5, 0.3), (0.25, 0.14, 0.07))
    cyl("h_cup", 0.035, 0.07, (-1.1, 1.45, 0.635), (0.8, 0.8, 0.78)); cyl("h_cup2", 0.03, 0.05, (-1.25, 1.55, 0.625), (0.9, 0.3, 0.2))
    door("h_door", (-1.2, -2.1, 0), 180, color=(0.30, 0.32, 0.30), open_deg=60)
    glow("h_bulb_g", (0.08, 0.08, 0.05), (0, 0.4, 2.9), (1.0, 0.85, 0.6), 4.0)
    lib.point_light("h_bulb", (0, 0.4, 2.75), 45, (1.0, 0.78, 0.5), 0.05)
    lib.area_light("h_cor", (-1.0, -2.6, 1.8), (0.4, 0.6, 0.8), 25, 0.8, (0.75, 1.0, 0.8))
    lib.world((0.003, 0.004, 0.006), 1.0)
    cams = {"back": ((1.1, -1.9, 1.55), (0.3, 1.4, 0.85), 26), "door": ((-0.5, -1.85, 1.5), (0.4, 1.0, 0.9), 26),
            "close": ((1.2, 1.2, 1.25), (0.35, 0.5, 1.1), 40), "wall": ((-0.4, 0.4, 1.3), (0.4, 2.1, 1.1), 30)}
    # Pak Harun sits on the bed facing the back wall (legs along the mattress)
    marks = {"harun_bed": ((0.4, -0.15, 0.27), R(180)), "sari_door": ((-1.0, -1.4, 0), R(180)),
             "sari_bed": ((-0.4, 0.4, 0), R(55))}
    return cams, marks


# =================================================================== 5. the abandoned ward
def bangsal(torch_only=True):
    L = 14.0
    cb("b_floor", (6.0, L, 0.06), (0, L / 2, -0.03), lib.tile_floor("b_tiles", 0.38, (0.22, 0.21, 0.17), (0.08, 0.08, 0.07)), bev=0.005)
    cb("b_dust", (5.6, L - 0.4, 0.01), (0, L / 2, 0.006), C((0.10, 0.09, 0.07), 2.0, 0.95), bev=0.003)
    cb("b_ceil", (6.0, L, 0.08), (0, L / 2, 3.2), (0.16, 0.16, 0.14), bev=0.005)
    for s in (-1, 1):
        cb(f"b_wall{s}", (0.14, L, 3.2), (s * 3.07, L / 2, 1.6), lib.grime_wall(f"b_wm{s}", (0.30, 0.30, 0.25), (0.08, 0.07, 0.05)), bev=0.01)
    fm = lib.grime_wall("b_fm", (0.30, 0.30, 0.25), (0.08, 0.07, 0.05))
    cb("b_frontL", (2.6, 0.14, 3.2), (-1.8, -0.07, 1.6), fm, bev=0.01); cb("b_frontR", (2.6, 0.14, 3.2), (1.8, -0.07, 1.6), fm, bev=0.01)
    cb("b_frontT", (1.0, 0.14, 0.9), (0.0, -0.07, 2.75), fm, bev=0.01)
    cb("b_back", (6.2, 0.14, 3.2), (0, L + 0.07, 1.6), lib.grime_wall("b_bm", (0.30, 0.30, 0.25), (0.08, 0.07, 0.05)), bev=0.01)
    for i, y in enumerate((2.0, 5.0, 8.0)):
        for s in (-1, 1):
            iron_bed(f"b_bed{i}{s}", (s * 2.3, y + 0.3, 0), 90 * s, mattress=(0.05, 0.045, 0.035), rusty=True)
    for i, y in enumerate((2.5, 6.5, 10.0)):
        window(f"b_win{i}", -3.0, y, 1.1, 0.9, 1.6, side=-1, sky=(0.05, 0.08, 0.18), sky_str=0.18)
    # calendar 1987, open at March
    cb("b_cal", (0.02, 0.42, 0.58), (3.0, 4.0, 1.75), (0.62, 0.58, 0.48), bev=0.005)
    text("b_cal_m", "MARET", (2.985, 4.0, 1.95), 0.08, (0.45, 0.06, 0.04), rot=(90, 0, -90))
    text("b_cal_y", "1987", (2.985, 4.0, 1.85), 0.07, (0.1, 0.1, 0.1), rot=(90, 0, -90))
    for r in range(4):
        for c in range(5):
            cb(f"b_cal_d{r}{c}", (0.005, 0.04, 0.03), (2.985, 3.85 + c * 0.075, 1.72 - r * 0.07), (0.25, 0.24, 0.2), bev=0.002)
    wheelchair("b_wchair", (2.6, 10.6, 0), 270)
    # kamar empat at the far end
    two_tone_wall("b_k4wall", (6.0, 0.12, 3.2), (0, L - 2.4, 1.6), along="x")
    door("b_k4door", (-0.45, L - 2.47, 0), 0, color=(0.25, 0.25, 0.22), open_deg=95)
    text("b_k4no", "4", (0.0, L - 2.48, 2.25), 0.18, (0.6, 0.55, 0.4))
    cb("b_debris1", (0.4, 0.3, 0.08), (-1.2, 4.2, 0.04), (0.2, 0.18, 0.15), rot=(0, 0, 20)); cb("b_debris2", (0.6, 0.2, 0.05), (1.0, 9.2, 0.03), (0.12, 0.1, 0.08))
    if not torch_only:
        tube("b_t1", (0, 5, 3.15), on=0.4, power=18)
    lib.area_light("b_moon", (-3.6, 6.5, 2.0), (1.0, 6.0, 0.0), 90, 1.5, (0.5, 0.62, 1.0))
    # entrance (doorway to the corridor, greenish tube light beyond)
    cb("b_dframe_l", (0.1, 0.2, 2.3), (-0.55, 0.0, 1.15), (0.2, 0.15, 0.1)); cb("b_dframe_r", (0.1, 0.2, 2.3), (0.55, 0.0, 1.15), (0.2, 0.15, 0.1))
    cb("b_dframe_t", (1.2, 0.2, 0.1), (0.0, 0.0, 2.3), (0.2, 0.15, 0.1))
    glow("b_doorway", (1.0, 0.02, 2.25), (0.0, -0.16, 1.12), (0.45, 0.62, 0.48), 0.9)
    lib.area_light("b_door_l", (0.0, -0.3, 1.6), (0.0, 3.0, 0.3), 60, 1.0, (0.7, 1.0, 0.75))
    lib.world((0.004, 0.005, 0.008), 1.0)
    lib.fog_volume((-3, 0, 0), (3, L, 3.2), 0.03)
    cams = {"entry": ((0.4, 0.5, 1.45), (-0.2, 9.0, 1.0), 24), "beds": ((-1.2, 1.2, 1.2), (2.4, 6.0, 0.5), 28),
            "cal": ((1.9, 3.6, 1.65), (3.0, 4.0, 1.78), 45), "wchair": ((1.4, 8.6, 1.3), (2.6, 10.8, 0.6), 35),
            "k4": ((0.3, 7.0, 1.35), (0.0, L - 2.4, 1.2), 30), "back": ((0.0, L - 3.0, 1.6), (0.0, 0.5, 1.0), 26),
            "door": ((0.6, 3.2, 1.2), (0.0, 0.0, 1.0), 32), "feet": ((0.5, 1.6, 0.35), (0.0, 0.3, 0.1), 32)}
    marks = {"entry": ((0.0, 0.8, 0), R(180)), "mid": ((0.0, 6.0, 0), R(180)), "k4": ((0.0, L - 3.2, 0), R(180)),
             "door_out": ((0.0, 0.6, 0), 0)}
    return cams, marks


# =================================================================== 6. room four
def kamar4(state="scratch"):
    """small cell 2.6 x 3.0; y from 0 (door) to 3; back wall at y=3 is the thick wall"""
    cb("k_floor", (2.8, 3.2, 0.06), (0, 1.5, -0.03), lib.tile_floor("k_tiles", 0.38, (0.22, 0.21, 0.17), (0.08, 0.08, 0.07)), bev=0.005)
    cb("k_ceil", (2.8, 3.2, 0.06), (0, 1.5, 2.9), (0.16, 0.16, 0.14), bev=0.005)
    wm = lib.grime_wall("k_wm", (0.36, 0.35, 0.29), (0.12, 0.10, 0.07))
    for s in (-1, 1):
        cb(f"k_wall{s}", (0.14, 3.2, 2.9), (s * 1.37, 1.5, 1.45), wm, bev=0.01)
    cb("k_front", (2.9, 0.14, 2.9), (0, -0.07, 1.45), wm, bev=0.01)
    if state == "bongkar":
        # back wall broken open: a body-sized hollow, skeleton standing with fists raised toward the room
        for x, w in ((-0.95, 0.9), (0.95, 0.9)):
            cb(f"k_backp{x}", (w, 0.34, 2.9), (x, 3.17, 1.45), wm, bev=0.02)
        cb("k_backtop", (1.1, 0.34, 0.75), (0, 3.17, 2.52), wm, bev=0.02)
        cb("k_cavity", (1.0, 0.04, 2.2), (0, 3.33, 1.1), (0.04, 0.035, 0.03), bev=0.01)
        bone = C((0.30, 0.25, 0.17), 1.2, 0.7)
        clay.blob("k_skull", (0, 3.2, 1.55), (0.075, 0.085, 0.095), bone)
        for s_ in (-1, 1):
            clay.blob(f"k_eye{s_}", (s_ * 0.028, 3.125, 1.565), (0.018, 0.01, 0.02), C((0.02, 0.015, 0.01), 0.2))
        clay.blob("k_jaw", (0, 3.14, 1.48), (0.035, 0.02, 0.02), C((0.02, 0.015, 0.01), 0.2))
        for z in range(10):
            clay.blob(f"k_spine{z}", (0, 3.24, 1.42 - z * 0.06), (0.025, 0.025, 0.025), bone)
        for k in range(5):
            clay.limb(f"k_rib{k}", (0, 3.22, 1.35 - k * 0.055), (0.09, 3.16, 1.30 - k * 0.06), 0.008, bone)
            clay.limb(f"k_ribr{k}", (0, 3.22, 1.35 - k * 0.055), (-0.09, 3.16, 1.30 - k * 0.06), 0.008, bone)
        clay.blob("k_pelvis", (0, 3.2, 0.8), (0.14, 0.06, 0.08), bone)
        for s in (-1, 1):
            clay.limb(f"k_leg{s}", (s * 0.08, 3.2, 0.78), (s * 0.09, 3.2, 0.06), 0.022, bone)
            clay.limb(f"k_uarm{s}", (s * 0.16, 3.2, 1.38), (s * 0.2, 3.12, 1.68), 0.018, bone)
            clay.limb(f"k_farm{s}", (s * 0.2, 3.12, 1.68), (s * 0.16, 3.02, 1.9), 0.015, bone)
            clay.blob(f"k_fist{s}", (s * 0.16, 3.0, 1.95), (0.035, 0.03, 0.04), bone)
        for i in range(8):
            r = random.Random(i)
            cb(f"k_rubble{i}", (r.uniform(0.1, 0.3),) * 3, (r.uniform(-0.9, 0.9), r.uniform(2.3, 2.9), 0.06), (0.35, 0.33, 0.28),
               rot=(r.uniform(0, 40), r.uniform(0, 40), r.uniform(0, 90)), bev=0.03)
        lib.area_light("k_work", (0.9, 1.2, 2.3), (0, 3.1, 1.2), 70, 0.4, (1.0, 0.85, 0.65))
        lib.world((0.02, 0.02, 0.022), 1.0)
    else:
        cb("k_back", (2.9, 0.34, 2.9), (0, 3.17, 1.45), wm, bev=0.01)
        scratches("k_scr_back", (0, 2.995, 0), (2.6, 2.9), "y", 230, seed=1)
        for s in (-1, 1):
            scratches(f"k_scr{s}", (s * 1.295, 1.5, 0), (3.0, 2.9), "x", 170, seed=5 + s)
        red = (0.14, 0.025, 0.02)
        for k, z in enumerate((1.62, 1.38, 1.14)):
            o = text(f"k_jj{k}", "JANGAN JAWAB", (0.04 * (k - 1), 2.99, z), 0.2 - 0.01 * k, red, rot=(90, 0, 2 * (k - 1)))
            o.rotation_euler.y = R(2 * (k - 1))
        text("k_suara", "dia bisa pakai suara siapa aja", (0.05, 2.99, 0.86), 0.075, red, rot=(90, 0, 0))
        lib.area_light("k_moon", (-0.8, 0.3, 2.5), (0.2, 2.6, 0.8), 8, 0.6, (0.5, 0.62, 1.0))
        lib.world((0.002, 0.0025, 0.004), 1.0)
    lib.fog_volume((-1.3, 0, 0), (1.3, 3, 2.9), 0.02)
    cams = {"door": ((0.2, 0.15, 1.45), (0.0, 3.0, 1.1), 22), "wall": ((0.0, 1.4, 1.3), (0.0, 3.0, 1.35), 32),
            "text": ((0.05, 2.1, 1.35), (0.0, 3.0, 1.38), 40), "low": ((0.05, 2.35, 0.9), (0.05, 3.0, 0.86), 40),
            "corner": ((0.5, 0.6, 1.3), (-1.1, 2.6, 0.5), 30), "side": ((-1.0, 1.0, 1.35), (1.2, 2.6, 0.9), 30)}
    marks = {"door": ((0.15, 0.4, 0), R(180)), "center": ((0.1, 1.3, 0), R(180)), "corner": ((-0.95, 2.6, 0), R(35)),
             "watch_l": ((-0.6, 1.4, 0), R(160)), "watch_r": ((0.55, 1.5, 0), R(200))}
    return cams, marks


# =================================================================== 7. inside Bu Wiwik's car (dusk, hospital car park)
def mobil():
    seat = (0.10, 0.08, 0.07)
    cb("m_floor", (1.6, 2.6, 0.05), (0, 0, 0.0), (0.04, 0.04, 0.04))
    for s in (-1, 1):
        cb(f"m_seat{s}", (0.55, 0.55, 0.16), (s * 0.4, 0.15, 0.32), seat, bev=0.06)
        cb(f"m_seatb{s}", (0.55, 0.14, 0.75), (s * 0.4, 0.45, 0.72), seat, rot=(-12, 0, 0), bev=0.06)
        cb(f"m_head{s}", (0.3, 0.12, 0.2), (s * 0.4, 0.55, 1.18), seat, bev=0.05)
    cb("m_dash", (1.6, 0.5, 0.35), (0, -0.85, 0.75), (0.07, 0.06, 0.055), bev=0.08)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.022, location=(0.4, -0.55, 0.92), rotation=(R(60), 0, 0))
    w = bpy.context.object; w.name = "m_wheel"; w.data.materials.append(C((0.03, 0.03, 0.03), 0.3))
    cb("m_roof", (1.6, 2.4, 0.06), (0, 0, 1.42), (0.18, 0.17, 0.15))
    for s in (-1, 1):
        cb(f"m_pillar{s}", (0.06, 0.06, 0.75), (s * 0.78, -0.95, 1.05), (0.1, 0.1, 0.1), rot=(-30, 0, 0))
        cb(f"m_door{s}", (0.06, 1.6, 0.55), (s * 0.82, 0.0, 0.55), (0.30, 0.30, 0.28), bev=0.03)
    glow("m_outside", (6.0, 0.05, 3.0), (0, -5.0, 1.2), (1.0, 0.55, 0.28), 0.8)
    for i in range(4):
        cb(f"m_tree{i}", (0.6, 0.6, 2.5), (-3 + i * 2, -4.5, 1.5), (0.03, 0.04, 0.03))
    lib.area_light("m_sun", (0.0, -3.0, 1.6), (0, 0.3, 0.9), 120, 2.0, (1.0, 0.6, 0.32))
    lib.area_light("m_fill", (0, 0.5, 1.38), (0, 0, 0.5), 8, 0.6, (0.8, 0.8, 1.0))
    lib.world((0.05, 0.03, 0.02), 1.0)
    cams = {"front": ((0.0, -1.15, 1.05), (0.0, 0.3, 0.9), 22), "wiwik": ((-0.15, -0.6, 1.0), (0.4, 0.15, 0.95), 35),
            "sari": ((0.25, -0.6, 1.0), (-0.4, 0.15, 0.95), 35), "two": ((0.0, -1.0, 1.15), (0.0, 0.2, 0.85), 26)}
    marks = {"driver": ((0.4, 0.22, 0.04), R(0)), "pass": ((-0.4, 0.22, 0.04), R(0))}
    return cams, marks


# =================================================================== 8. the register book on a desk (close-up set)
def buku(lines=(), title=False, style="open"):
    cb("bk_desk", (2.0, 1.4, 0.06), (0, 0, 0.74), (0.28, 0.15, 0.07))
    cv = C((0.05, 0.16, 0.08), 1.8, 0.85)
    if style == "closed":
        cb("bk_block", (0.31, 0.43, 0.06), (0.15, 0, 0.80), (0.60, 0.56, 0.44), bev=0.01)
        cb("bk_cov", (0.32, 0.44, 0.012), (0.15, 0, 0.836), cv, bev=0.006)
        clay.blob("bk_mold", (0.08, 0.12, 0.842), (0.07, 0.05, 0.006), C((0.18, 0.22, 0.12), 2.0, 0.9))
        clay.blob("bk_mold2", (0.22, -0.1, 0.842), (0.04, 0.06, 0.006), C((0.30, 0.32, 0.20), 2.0, 0.9))
        cb("bk_label", (0.2, 0.1, 0.004), (0.15, 0.0, 0.843), (0.62, 0.58, 0.45), bev=0.002)
        text("bk_t1", "BANGSAL MELATI", (0.15, 0.015, 0.846), 0.022, (0.1, 0.08, 0.05), rot=(0, 0, 0))
        text("bk_t2", "1979 - 1987", (0.15, -0.02, 0.846), 0.018, (0.1, 0.08, 0.05), rot=(0, 0, 0))
    elif style == "kertas":
        cb("bk_paper", (0.30, 0.42, 0.004), (0.15, 0, 0.775), (0.55, 0.47, 0.28), rot=(0, 0, -4), bev=0.002)
        for i in range(5):
            cyl(f"bk_key{i}", 0.012, 0.09, (-0.25 + i * 0.03, 0.05 + 0.02 * i, 0.78), (0.55, 0.45, 0.15), rot=(0, 90, 30 * i))
    else:
        cb("bk_cov", (0.62, 0.44, 0.02), (0, 0, 0.78), cv, bev=0.01)
        for s in (-1, 1):
            cb(f"bk_page{s}", (0.29, 0.41, 0.02), (s * 0.152, 0, 0.797), (0.60, 0.56, 0.44), bev=0.004)
        clay.blob("bk_mold", (-0.27, 0.15, 0.785), (0.06, 0.05, 0.008), C((0.18, 0.22, 0.12), 2.0, 0.9))
    if title:
        text("bk_spine", "BANGSAL MELATI 1979-1987", (0, -0.0, 0.81), 0.03, (0.75, 0.66, 0.4), rot=(0, 0, 0))
    ink = (0.010, 0.012, 0.035)
    for i, ln in enumerate(lines):
        col = (0.12, 0.012, 0.008) if ln.startswith("!") else ink
        zz = 0.7775 if style == "kertas" else 0.8072
        t = text(f"bk_l{i}", ln.lstrip("!"), (0.025, 0.17 - i * 0.03, zz), 0.0135 if not ln.startswith("#") else 0.015, col, rot=(0, 0, 0))
        t.data.align_x = "LEFT"; t.data.extrude = 0.0
        t.visible_shadow = False
        if ln.startswith("#"):
            t.data.body = ln.lstrip("#")
    lib.point_light("bk_lamp", (0.4, 0.3, 1.25), 25, (1.0, 0.78, 0.5), 0.1)
    lib.world((0.004, 0.004, 0.006), 1.0)
    cams = {"top": ((0.08, -0.32, 1.35), (0.1, 0.0, 0.8), 40), "page": ((0.14, -0.15, 1.05), (0.15, 0.05, 0.8), 45),
            "low": ((-0.4, -0.5, 0.95), (0.05, 0.05, 0.8), 35)}
    return cams, {}


# =================================================================== 9. graveyard (day)
def makam():
    cb("g_ground", (30, 30, 0.2), (0, 5, -0.1), C((0.13, 0.17, 0.07), 1.8, 0.9), bev=0.02)
    rnd = random.Random(3)
    for i in range(14):
        x, y = rnd.uniform(-6, 6), rnd.uniform(2, 12)
        if abs(x) < 1.2 and y < 4:
            continue
        cb(f"g_stone{i}", (0.42, 0.1, 0.6), (x, y, 0.3), (0.42, 0.42, 0.38), rot=(rnd.uniform(-6, 6), 0, rnd.uniform(-10, 10)), bev=0.05)
    cb("g_mound", (0.8, 1.8, 0.22), (0, 1.8, 0.11), C((0.20, 0.12, 0.06), 2.0), bev=0.12)
    cb("g_stone", (0.55, 0.12, 0.75), (0, 2.75, 0.38), (0.55, 0.55, 0.50), bev=0.05)
    text("g_name", "RATNA", (0, 2.68, 0.55), 0.09, (0.12, 0.12, 0.12))
    text("g_year", "1968 - 1987", (0, 2.68, 0.4), 0.05, (0.12, 0.12, 0.12))
    w = C((0.85, 0.85, 0.80), 0.4, 0.5)
    for i in range(18):
        clay.blob(f"g_melati{i}", (rnd.uniform(-0.3, 0.3), rnd.uniform(1.2, 2.4), 0.24), (0.025, 0.025, 0.015), w, seg=12)
    for i, (x, y) in enumerate(((-3.5, 10), (4, 12), (-6, 4))):
        cyl(f"g_tree{i}", 0.2, 4, (x, y, 2), (0.12, 0.08, 0.05)); clay.blob(f"g_crown{i}", (x, y, 4.5), (1.6, 1.6, 1.3), C((0.06, 0.12, 0.05), 1.6))
    lib.world((0.55, 0.62, 0.75), 1.0)
    lib.sun("g_sun", (-0.3, 0.6, -0.6), 3.0, (1.0, 0.92, 0.8), 3.0)
    cams = {"wide": ((2.4, -3.5, 1.6), (0, 2.0, 0.5), 30), "stone": ((0.3, 0.6, 0.8), (0, 2.75, 0.5), 40)}
    marks = {"wiwik": ((-0.9, 0.9, 0), R(135)), "sari": ((0.9, 0.9, 0), R(225)), "harun": ((1.5, 0.4, 0), R(227))}
    return cams, marks


# =================================================================== 10. the boarding-house room (reuses the bedroom shell)
def kos(clock="02:17", lamp=False):
    import sets
    cams, marks = sets.bedroom("sari")
    if "clock" in bpy.data.objects:
        bpy.data.objects["clock"].data.body = clock
    if "phone_scr" in bpy.data.objects and not lamp:
        pass
    cams.update({"wall": ((0.6, -0.1, 1.0), (-1.95, 0.9, 0.9), 30), "top": ((-0.9, 0.3, 2.3), (-0.9, 1.0, 0.5), 30),
                 "close": ((-0.3, 0.1, 0.95), (-0.9, 1.15, 0.75), 40)})
    marks.update({"sit": ((-0.9, 1.35, 0.24), 0)})
    return cams, marks
