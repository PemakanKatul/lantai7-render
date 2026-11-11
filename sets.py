"""Clay-miniature locations for "Lantai Tujuh Tidak Pernah Kosong".
Every builder creates geometry + motivated lights and returns a dict of named camera
presets {name: (cam_loc, target, lens)} and character marks {name: (loc, rot_z)}.
Characters are ~1.45 m tall; doors 2.1 m.
"""
import math, random
import bpy
from mathutils import Vector
import lib, clay, fig

R = math.radians


def C(color, dents=1.2, rough=0.6):
    return clay.clay_mat("set_" + "_".join(f"{v:.3f}" for v in color) + f"_{dents}", color, rough=rough, dents=dents)


def cb(name, size, loc, color, rot=(0, 0, 0), bev=0.03, dents=1.2):
    o = lib.box(name, size, loc, C(color, dents) if isinstance(color, tuple) else color, rot=tuple(R(a) for a in rot))
    b = o.modifiers.new("round", "BEVEL"); b.width = min(bev, min(size) * 0.45); b.segments = 3
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cyl(name, r, h, loc, color, rot=(0, 0, 0), bev=0.01):
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=r, depth=h, location=loc, rotation=tuple(R(a) for a in rot))
    o = bpy.context.object; o.name = name
    o.data.materials.append(C(color) if isinstance(color, tuple) else color)
    b = o.modifiers.new("round", "BEVEL"); b.width = bev; b.segments = 2; b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth()
    return o


def glow(name, size, loc, color, strength, rot=(0, 0, 0)):
    return lib.box(name, size, loc, lib.emit_mat(name + "_m", color, strength), rot=tuple(R(a) for a in rot))


def text(name, body, loc, size, color, rot=(90, 0, 0), emit=0.0):
    bpy.ops.object.text_add(location=loc, rotation=tuple(R(a) for a in rot))
    o = bpy.context.object; o.name = name
    o.data.body = body; o.data.size = size; o.data.extrude = size * 0.06
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"
    o.data.materials.append(lib.emit_mat(name + "_m", color, emit) if emit else C(color, 0.2))
    return o


def door(name, loc, rot_z, color=(0.16, 0.075, 0.04), w=0.9, h=2.1, number=None, open_deg=0.0, frame=(0.07, 0.06, 0.05)):
    """door slab + frame; loc = hinge-side bottom corner on the wall plane; faces local -Y"""
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = name
    parts = [cb(name + "_fl", (0.08, 0.1, h + 0.08), (-0.04, 0, h / 2 + 0.04), frame),
             cb(name + "_fr", (0.08, 0.1, h + 0.08), (w + 0.04, 0, h / 2 + 0.04), frame),
             cb(name + "_ft", (w + 0.16, 0.1, 0.08), (w / 2, 0, h + 0.04), frame)]
    bpy.ops.object.empty_add(location=(0, 0, 0))
    hinge = bpy.context.object; hinge.name = name + "_hinge"
    leaf = cb(name + "_leaf", (w, 0.05, h), (w / 2, 0, h / 2), color, bev=0.02)
    knob = cb(name + "_knob", (0.07, 0.09, 0.07), (w - 0.1, -0.05, 1.0), (0.35, 0.27, 0.08), bev=0.03)
    for o in (leaf, knob):
        o.parent = hinge
    if number:
        t = text(name + "_no", number, (w / 2, -0.031, 1.62), 0.13, (0.75, 0.68, 0.45)); t.parent = hinge
    hinge.rotation_euler.z = R(-open_deg)
    for o in parts + [hinge]:
        o.parent = root
    return root


def chair(name, loc, rot_z=0, color=(0.05, 0.05, 0.06)):
    bpy.ops.object.empty_add(location=loc, rotation=(0, 0, R(rot_z)))
    root = bpy.context.object; root.name = name
    ps = [cb(name + "s", (0.42, 0.42, 0.07), (0, 0, 0.44), color), cb(name + "b", (0.42, 0.07, 0.42), (0, 0.19, 0.72), color),
          cyl(name + "p", 0.03, 0.40, (0, 0, 0.22), (0.03, 0.03, 0.03)), cyl(name + "f", 0.2, 0.04, (0, 0, 0.03), (0.03, 0.03, 0.03))]
    for o in ps:
        o.parent = root
    return root


def tube(name, loc, length=1.2, on=1.0, color=(0.80, 1.0, 0.84), along="y", power=14):
    sz = (0.14, length + 0.08, 0.05) if along == "y" else (length + 0.08, 0.14, 0.05)
    gz = (0.05, length, 0.02) if along == "y" else (length, 0.05, 0.02)
    cb(name + "_fix", sz, loc, (0.05, 0.05, 0.05), bev=0.01)
    glow(name + "_glow", gz, (loc[0], loc[1], loc[2] - 0.03), color, 5 * on + 0.02)
    if on > 0:
        l = lib.area_light(name, (loc[0], loc[1], loc[2] - 0.06), (loc[0], loc[1], 0), power * on, 0.1, color)
        l.data.shape = "RECTANGLE"; l.data.size = 0.08; l.data.size_y = length
        if along != "y":
            l.rotation_euler.z = R(90)
        return l


# =================================================================== 1. the office unit
def unit(night=True, lights_on=True, bedcover=False, door_open=0.0, fog=False):
    lg = lib.apartment_unit(fog=fog, tube_on=lights_on, moon=night, monitors=True, door_open=door_open)
    clay.clayify_set()
    if not night:
        lib.sun("day", (0.18, -1.0, -0.80), 3.5, (1.0, 0.93, 0.80), 3.0)
        lib.world((0.10, 0.11, 0.12), 1.0)
    # bathroom door (left of the entrance), pantry (right of the entrance)
    door("bath_door", (-2.48, -3.2, 0), -90, color=(0.42, 0.44, 0.40), w=0.75, number=None)
    cb("pantry", (0.55, 1.5, 0.86), (-2.18, 1.1, 0.43), (0.42, 0.36, 0.26))
    cb("pantry_top", (0.6, 1.56, 0.05), (-2.17, 1.1, 0.885), (0.14, 0.13, 0.12))
    cyl("kettle", 0.085, 0.2, (-2.2, 0.75, 1.0), (0.55, 0.08, 0.06)); cyl("mug1", 0.045, 0.09, (-2.1, 1.25, 0.955), (0.75, 0.72, 0.62))
    cyl("mug2", 0.045, 0.09, (-2.25, 1.45, 0.955), (0.12, 0.25, 0.4)); cb("dispenser", (0.3, 0.3, 1.05), (-2.25, 1.75, 0.53), (0.7, 0.72, 0.72))
    cyl("galon", 0.13, 0.36, (-2.25, 1.75, 1.24), (0.25, 0.5, 0.75))
    # Pak Hendra's desk in the back right corner + wardrobe
    cb("hdesk", (1.2, 0.6, 0.05), (1.75, -3.6, 0.74), (0.24, 0.13, 0.06)); cb("hdesk_l", (0.05, 0.55, 0.72), (1.2, -3.6, 0.36), (0.2, 0.11, 0.05))
    cb("hdesk_r", (0.05, 0.55, 0.72), (2.3, -3.6, 0.36), (0.2, 0.11, 0.05)); cb("hlaptop", (0.34, 0.24, 0.02), (1.75, -3.6, 0.78), (0.05, 0.05, 0.055))
    cb("hpapers", (0.24, 0.32, 0.08), (2.15, -3.55, 0.81), (0.72, 0.70, 0.62), rot=(0, 0, 12)); chair("hchair", (1.75, -4.05, 0), 180)
    cb("wardrobe", (1.0, 0.55, 1.9), (-1.6, -4.18, 0.95), (0.22, 0.12, 0.06)); cb("wd_split", (0.02, 0.02, 1.8), (-1.6, -3.9, 0.95), (0.08, 0.04, 0.02))
    for i, yy in enumerate((-0.5, 0.1, 0.7, 1.3)):
        chair(f"chair{i}", (0.75, yy, 0), -90 + (i * 7 - 10))
    cb("rug", (1.9, 1.5, 0.02), (-0.3, -1.3, 0.012), (0.20, 0.05, 0.04), bev=0.01)
    if bedcover:
        cb("bedcover", (0.95, 1.9, 0.09), (-0.9, -1.6, 0.06), (0.50, 0.42, 0.55), rot=(0, 0, 8), bev=0.04)
        cb("blanket", (0.98, 1.1, 0.06), (-0.92, -1.95, 0.13), (0.30, 0.38, 0.55), rot=(0, 0, 8), bev=0.03)
        cb("pillow", (0.6, 0.36, 0.13), (-0.8, -0.85, 0.15), (0.78, 0.76, 0.70), rot=(0, 0, 8), bev=0.06)
    cams = {"wide": ((0.3, -4.25, 1.75), (0.4, 0.6, 0.85), 22), "desk": ((-0.9, -1.9, 1.25), (1.2, 0.4, 0.95), 35),
            "door": ((1.6, -2.4, 1.3), (-2.5, -0.5, 1.0), 35), "floor": ((0.9, -3.4, 0.9), (-0.9, -1.4, 0.2), 35),
            "corner": ((-1.2, -1.2, 1.2), (1.9, -3.9, 0.6), 35)}
    marks = {"center": ((0, -1.0, 0), 0), "desk_a": ((0.75, -0.2, 0), R(90)), "bed": ((-0.86, -1.55, 0.2), R(8)),
             "door_in": ((-1.9, -0.5, 0), R(90)), "corner": ((1.9, -4.0, 0), R(150))}
    return cams, marks


# =================================================================== 2. corridor (lantai 6 / 7)
def corridor(floor="6", length=18.0, dead=(2, 3), fog=True, end_open=0.0):
    """runs along +Y from the lift lobby (y=0) to the corner unit (y=length). x in [-1.1, 1.1]."""
    wall = (0.30, 0.33, 0.27) if floor == "6" else (0.24, 0.27, 0.25)
    cb("c_floor", (2.2, length + 2, 0.06), (0, length / 2 - 1, -0.03), (0.13, 0.11, 0.09), bev=0.005)
    cb("c_carpet", (1.3, length + 1.6, 0.02), (0, length / 2 - 1, 0.012), (0.20, 0.035, 0.035), bev=0.008)
    cb("c_ceil", (2.2, length + 2, 0.06), (0, length / 2 - 1, 2.63), (0.26, 0.26, 0.23), bev=0.005)
    for sx in (-1, 1):
        cb(f"c_wall{sx}", (0.12, length + 2, 2.6), (sx * 1.16, length / 2 - 1, 1.3), wall, bev=0.01)
        cb(f"c_skirt{sx}", (0.04, length + 2, 0.12), (sx * 1.09, length / 2 - 1, 0.06), (0.08, 0.06, 0.05), bev=0.01)
    cb("c_end", (2.4, 0.12, 2.6), (0, length + 0.06, 1.3), wall, bev=0.01)
    cb("c_back", (2.4, 0.12, 2.6), (0, -2.06, 1.3), wall, bev=0.01)
    n = 0
    for y in range(3, int(length) - 1, 3):
        for sx in (-1, 1):
            n += 1
            door(f"cd{n}", (sx * 1.1, y - 0.45 * sx, 0), 90 * sx + 180, number=f"{floor}{n:02d}")
    door("c_unit", (-1.1, length - 1.4 + 0.45, 0), 90, color=(0.16, 0.075, 0.04), number=f"{floor}15", open_deg=end_open)
    # lift on the right near the start
    steel = (0.32, 0.33, 0.34)
    cb("lift_frame", (0.14, 1.5, 2.3), (1.06, -0.6, 1.15), (0.12, 0.12, 0.13), bev=0.02)
    for k in (-1, 1):
        cb(f"lift_door{k}", (0.05, 0.62, 2.1), (1.0, -0.6 + k * 0.315, 1.05), steel, bev=0.01)
    glow("lift_btn", (0.02, 0.05, 0.05), (1.02, 0.3, 1.1), (1.0, 0.45, 0.1), 3.0)
    text("lift_ind", floor, (0.985, -0.6, 2.32), 0.16, (1.0, 0.15, 0.05), rot=(90, 0, -90), emit=4.0)
    text("floor_sign", f"LANTAI {floor}", (-1.09, -0.6, 1.75), 0.2, (0.75, 0.70, 0.5), rot=(90, 0, 90))
    cyl("bin", 0.14, 0.5, (0.8, 1.2, 0.25), (0.10, 0.10, 0.11)); cb("ext", (0.12, 0.12, 0.4), (-1.02, 1.6, 1.1), (0.55, 0.03, 0.03), bev=0.04)
    i = 0
    for y in range(1, int(length), 4):
        i += 1
        on = 0.0 if i in dead else (0.35 if i == max(dead) + 1 else 1.0)
        tube(f"ct{i}", (0, y, 2.58), on=on, power=16)
    lib.world((0.003, 0.004, 0.006), 1.0)
    if fog:
        lib.fog_volume((-1.1, -2, 0), (1.1, length, 2.6), 0.02)
    cams = {"long": ((0.35, -1.5, 1.25), (-0.2, length, 1.0), 28), "lift": ((-0.7, 2.6, 1.2), (1.0, -0.6, 1.1), 35),
            "end": ((0.5, length - 6.5, 1.3), (-1.0, length - 1.0, 1.0), 40), "back": ((0, length - 0.8, 1.5), (0, 0, 0.9), 30)}
    marks = {"lift": ((0.2, 0.4, 0), R(180)), "mid": ((0, 6, 0), R(180)), "unit_door": ((-0.35, length - 0.95, 0), R(90)),
             "behind": ((0.3, length - 5.5, 0), 0)}
    return cams, marks


# =================================================================== 3. emergency stairs
def stairs(floor="3", light=0.5):
    conc = (0.20, 0.20, 0.19)
    W = 1.15
    cb("s_floor", (2.6, 6.2, 0.1), (0, 0, -0.05), conc, bev=0.01)
    for sx in (-1, 1):
        cb(f"s_wall{sx}", (0.15, 6.4, 6.5), (sx * 1.37, 0, 2.6), (0.24, 0.25, 0.23), bev=0.01)
    cb("s_wallN", (2.9, 0.15, 6.5), (0, 3.15, 2.6), (0.24, 0.25, 0.23), bev=0.01)
    cb("s_wallS", (2.9, 0.15, 6.5), (0, -3.15, 2.6), (0.22, 0.23, 0.21), bev=0.01)
    n, rise, run = 9, 0.165, 0.27
    for i in range(n):          # flight A: right side, going up toward +Y
        cb(f"sa{i}", (W, run + 0.03, rise * (i + 1)), (0.65, -1.2 + i * run, rise * (i + 1) / 2), conc, bev=0.012)
    top = rise * n
    cb("s_land", (2.6, 1.5, 0.14), (0, 2.35, top - 0.07), conc, bev=0.01)
    for i in range(n):          # flight B: left side, going up toward -Y
        cb(f"sb{i}", (W, run + 0.03, 0.14), (-0.65, 1.55 - i * run, top + rise * (i + 1) - 0.07), conc, bev=0.012)
        cb(f"sbu{i}", (W, run + 0.03, 0.05), (-0.65, 1.55 - i * run, top + rise * (i + 1) - 0.17), conc, bev=0.005)
    cb("s_land2", (2.6, 1.6, 0.14), (0, -2.3, 2 * top - 0.07), conc, bev=0.01)
    rail = (0.25, 0.05, 0.03)
    for i in range(0, n + 1, 2):
        cyl(f"ra{i}", 0.014, 0.9, (0.06, -1.2 + i * run, rise * i + 0.5), rail)
        cyl(f"rb{i}", 0.014, 0.9, (-0.06, 1.55 - i * run, top + rise * i + 0.5), rail)
    L = math.hypot(n * run, top); ang = math.degrees(math.atan2(top, n * run))
    cyl("ra_top", 0.022, L + 0.2, (0.06, -1.2 + n * run / 2, top / 2 + 0.95), rail, rot=(90 - ang, 0, 0))
    cyl("rb_top", 0.022, L + 0.2, (-0.06, 1.55 - n * run / 2, top * 1.5 + 0.95), rail, rot=(90 + ang, 0, 0))
    text("s_no", floor, (-1.28, 2.4, top + 1.35), 0.55, (0.55, 0.50, 0.35), rot=(90, 0, 90))
    door("s_door", (1.29, 1.9 + 0.45, top), -90, color=(0.30, 0.06, 0.05), number=None)
    glow("s_exit", (0.02, 0.4, 0.14), (1.28, 2.35, top + 2.3), (0.1, 1.0, 0.3), 2.5)
    lib.point_light("s_exitl", (1.1, 2.35, top + 2.2), 6 * light, (0.2, 1.0, 0.4), 0.1)
    lib.area_light("s_slit", (-1.2, 2.6, top + 2.6), (0.3, 0.5, 0.6), 90 * light, 0.5, (0.55, 0.65, 0.9))
    lib.point_light("s_bulb", (0.0, -2.2, 2.9), 14 * light, (1.0, 0.75, 0.45), 0.08)
    lib.world((0.002, 0.003, 0.004), 1.0)
    cams = {"up": ((0.75, -2.7, 1.1), (0.0, 2.2, top + 1.0), 24), "down": ((-0.2, 2.75, top + 1.75), (0.6, -1.0, 0.6), 24),
            "land": ((0.9, 1.0, top + 1.2), (-0.4, 2.5, top + 0.8), 30)}
    marks = {"a": ((0.62, -1.2 + 6 * run, rise * 7), R(180)), "b": ((0.72, -1.2 + 3 * run, rise * 4), R(180)), "c": ((0.55, -1.2, rise), R(180)),
             "low": ((0.65, -1.9, 0), R(180))}
    return cams, marks


# =================================================================== 4. lift (interior, doors open on lantai 7)
def lift(floor="7", doors_open=1.0):
    steel = (0.30, 0.31, 0.32)
    cb("l_floor", (1.7, 1.7, 0.06), (0, 0, -0.03), (0.08, 0.08, 0.085), bev=0.005)
    cb("l_ceil", (1.7, 1.7, 0.06), (0, 0, 2.33), (0.2, 0.2, 0.2), bev=0.005)
    cb("l_back", (1.7, 0.08, 2.3), (0, -0.85, 1.15), steel, bev=0.01)
    for sx in (-1, 1):
        cb(f"l_side{sx}", (0.08, 1.7, 2.3), (sx * 0.85, 0, 1.15), steel, bev=0.01)
        cb(f"l_front{sx}", (0.42, 0.1, 2.3), (sx * 0.64, 0.85, 1.15), steel, bev=0.01)
        cb(f"l_leaf{sx}", (0.44, 0.05, 2.1), (sx * (0.22 + 0.44 * doors_open), 0.93, 1.05), (0.36, 0.37, 0.38), bev=0.01)
        cyl(f"l_rail{sx}", 0.02, 1.4, (sx * 0.78, 0, 0.95), (0.5, 0.5, 0.5), rot=(90, 0, 0))
    cb("l_top", (0.86, 0.1, 0.22), (0, 0.85, 2.19), steel, bev=0.01)
    cb("l_panel", (0.22, 0.03, 0.6), (0.62, 0.79, 1.2), (0.12, 0.12, 0.13), bev=0.01)
    for i in range(8):
        glow(f"l_b{i}", (0.035, 0.01, 0.035), (0.58 + (i % 2) * 0.08, 0.772, 1.0 + (i // 2) * 0.09),
             (1.0, 0.25, 0.05) if i == 6 else (0.6, 0.6, 0.5), 4.0 if i == 6 else 0.25)
    text("l_ind", floor, (0, 0.795, 2.2), 0.15, (1.0, 0.12, 0.04), rot=(90, 0, 180), emit=5.0)
    glow("l_lamp", (0.9, 0.9, 0.02), (0, 0, 2.29), (0.85, 1.0, 0.9), 1.2)
    ll = lib.area_light("l_light", (0, 0, 2.26), (0, 0, 0), 22, 0.9, (0.85, 1.0, 0.9))
    # corridor of lantai 7 beyond the doors
    cb("h_floor", (5, 6, 0.06), (0, 3.9, -0.03), (0.11, 0.09, 0.08), bev=0.005)
    cb("h_carpet", (5, 1.3, 0.02), (0, 2.0, 0.012), (0.18, 0.03, 0.03), bev=0.008)
    cb("h_wall", (5, 0.12, 2.6), (0, 3.2, 1.3), (0.22, 0.25, 0.23), bev=0.01)
    cb("h_ceil", (5, 6, 0.06), (0, 3.9, 2.63), (0.2, 0.2, 0.18), bev=0.005)
    door("h_door", (-0.15, 3.14, 0), 0, number=f"{floor}08")
    tube("h_tube", (1.6, 2.0, 2.58), on=0.25, along="x", power=14)
    lib.point_light("h_red", (-1.8, 2.2, 1.6), 8, (1.0, 0.1, 0.05), 0.2)
    lib.fog_volume((-2.5, 0.95, 0), (2.5, 3.2, 2.6), 0.05)
    lib.world((0.002, 0.002, 0.003), 1.0)
    cams = {"inside": ((0.25, -0.72, 1.3), (-0.05, 2.4, 1.05), 24), "ots": ((0.55, -0.6, 1.5), (0, 2.0, 1.0), 30)}
    marks = {"rider": ((-0.3, 0.05, 0), R(180)), "ghost": ((0.05, 2.05, 0.06), 0)}
    return cams, marks


# =================================================================== 5. lobby
def lobby():
    cb("lb_floor", (10, 8, 0.06), (0, 0, -0.03), (0.22, 0.20, 0.17), bev=0.005)
    for i in range(-4, 5):
        cb(f"lb_tile{i}", (0.02, 8, 0.005), (i * 1.1, 0, 0.002), (0.10, 0.09, 0.08), bev=0.001)
    cb("lb_ceil", (10, 8, 0.06), (0, 0, 3.03), (0.25, 0.25, 0.22), bev=0.005)
    cb("lb_back", (10, 0.15, 3), (0, 4.0, 1.5), (0.27, 0.30, 0.25), bev=0.01)
    cb("lb_left", (0.15, 8, 3), (-5.0, 0, 1.5), (0.27, 0.30, 0.25), bev=0.01)
    cb("lb_right", (0.15, 8, 3), (5.0, 0, 1.5), (0.27, 0.30, 0.25), bev=0.01)
    # reception desk (empty), dusty sofa, dead plant, mailboxes, lift doors
    cb("rc_desk", (2.4, 0.7, 1.05), (-2.4, 2.6, 0.53), (0.20, 0.11, 0.05)); cb("rc_top", (2.5, 0.8, 0.06), (-2.4, 2.6, 1.08), (0.10, 0.09, 0.08))
    text("rc_sign", "RESEPSIONIS", (-2.4, 2.24, 0.62), 0.16, (0.6, 0.52, 0.3))
    cb("sofa_seat", (1.9, 0.75, 0.38), (2.6, 2.9, 0.22), (0.20, 0.10, 0.09), bev=0.08); cb("sofa_back", (1.9, 0.25, 0.75), (2.6, 3.3, 0.5), (0.20, 0.10, 0.09), bev=0.08)
    for k in (-1, 1):
        cb(f"sofa_arm{k}", (0.25, 0.8, 0.55), (2.6 + k * 1.0, 2.9, 0.33), (0.18, 0.09, 0.08), bev=0.08)
    cyl("pot", 0.22, 0.4, (4.3, 3.3, 0.2), (0.32, 0.14, 0.08))
    for k in range(5):
        cyl(f"twig{k}", 0.012, 0.9 + 0.1 * k, (4.3 + 0.05 * math.cos(k * 1.4), 3.3 + 0.05 * math.sin(k * 1.4), 0.8), (0.12, 0.09, 0.05), rot=(8 * math.cos(k * 2), 9 * math.sin(k * 2), 0))
    for r in range(3):
        for c in range(6):
            cb(f"mail{r}{c}", (0.3, 0.06, 0.22), (-4.2 + c * 0.33, 3.9, 1.1 + r * 0.25), (0.34, 0.35, 0.36), bev=0.01)
    for k in (0, 1):
        x = 0.4 + k * 1.5
        cb(f"lf_frame{k}", (1.3, 0.12, 2.35), (x, 3.92, 1.17), (0.10, 0.10, 0.11), bev=0.02)
        for d in (-1, 1):
            cb(f"lf_door{k}{d}", (0.52, 0.05, 2.1), (x + d * 0.265, 3.84, 1.05), (0.33, 0.34, 0.35), bev=0.01)
        text(f"lf_ind{k}", "1" if k == 0 else "7", (x, 3.83, 2.25), 0.13, (1.0, 0.15, 0.05), emit=4.0)
    # glass entrance (front, y=-4) with flood-grey daylight
    for x in (-3.4, -1.2, 1.2, 3.4):
        cb(f"mullion{x}", (0.12, 0.12, 3), (x, -4.0, 1.5), (0.06, 0.06, 0.07), bev=0.02)
    cb("ent_top", (10, 0.15, 0.6), (0, -4.0, 2.7), (0.27, 0.30, 0.25), bev=0.01)
    cb("ent_l", (1.6, 0.15, 3), (-4.2, -4.0, 1.5), (0.27, 0.30, 0.25)); cb("ent_r", (1.6, 0.15, 3), (4.2, -4.0, 1.5), (0.27, 0.30, 0.25))
    day = lib.area_light("lb_day", (0, -5.2, 2.0), (0, 2, 0.6), 220, 5.0, (0.62, 0.72, 0.85)); day.data.shape = "RECTANGLE"; day.data.size_y = 2.4
    tube("lb_t1", (-2.4, 1.6, 2.98), on=0.5, along="x", power=30); tube("lb_t2", (2.2, 1.6, 2.98), on=0.0, along="x")
    lib.area_light("lb_warm", (-2.4, 2.2, 1.6), (-2.4, 3.5, 1.0), 14, 0.6, (1.0, 0.6, 0.3))
    lib.world((0.02, 0.025, 0.03), 1.0)
    cams = {"wide": ((-0.2, -3.4, 1.5), (0.4, 3.0, 1.0), 24), "group": ((-1.2, -1.4, 1.25), (1.3, 1.8, 0.95), 35),
            "whisper": ((0.4, 0.2, 1.2), (1.9, 1.9, 1.1), 50)}
    marks = {"sari": ((2.0, 1.2, 0), R(-55)), "bagas": ((1.25, 1.25, 0), R(55)), "hendra": ((-0.6, 1.8, 0), R(10)),
             "wulan": ((0.2, 2.2, 0), R(-15)), "nadia": ((-1.4, 1.5, 0), R(25)), "fajar": ((3.3, 2.2, 0), R(-20))}
    return cams, marks


# =================================================================== 6. exterior: flood + twin towers
def _tower(name, x, y, w, d, h, wall, lit, warm, seed):
    rnd = random.Random(seed)
    cb(name, (w, d, h), (x, y, h / 2), wall, bev=0.15, dents=2.0)
    cb(name + "_roof", (w + 0.6, d + 0.6, 0.5), (x, y, h + 0.25), tuple(c * 0.7 for c in wall), bev=0.1)
    cols, rows = int(w / 1.7), int(h / 2.9)
    on_m = lib.emit_mat(name + "_on", warm, 2.2); dim_m = lib.emit_mat(name + "_dim", warm, 0.5)
    off_m = C((0.012, 0.014, 0.018), 0.0, 0.15)
    for r in range(1, rows):
        for c in range(cols):
            v = rnd.random()
            m = on_m if v < lit else (dim_m if v < lit * 1.5 else off_m)
            wx = x - w / 2 + (c + 0.5) * w / cols
            lib.box(f"{name}_w{r}_{c}", (w / cols * 0.55, 0.06, 1.3), (wx, y - d / 2 - 0.02, r * 2.9 + 1.2), m)
    return rows


def exterior(twin=False, night=True):
    water = bpy.data.materials.new("water"); water.use_nodes = True
    b = water.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.045, 0.035, 0.02, 1); b.inputs["Roughness"].default_value = 0.08
    nz = water.node_tree.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 4
    bp = water.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    water.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); water.node_tree.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    lib.box("water", (400, 400, 0.02), (0, 0, 0.45), water)
    cb("ground", (400, 400, 0.1), (0, 0, -0.05), (0.06, 0.06, 0.06), bev=0.01)
    _tower("towerA", -9 if twin else 0, 30, 20, 14, 78, (0.20, 0.22, 0.20), 0.035, (0.75, 1.0, 0.8), 3)
    cb("podiumA", (26, 16, 6), (-9 if twin else 0, 27, 3), (0.17, 0.19, 0.17), bev=0.2)
    text("nameA", "APARTEMEN", ((-9 if twin else 0), 18.95, 5.0), 1.4, (0.35, 0.33, 0.25))
    glow("lobbyA", (5, 0.1, 2.4), ((-9 if twin else 0), 18.96, 2.2), (0.6, 0.9, 0.7), 0.6)
    if twin:
        _tower("towerB", 19, 44, 20, 14, 78, (0.42, 0.33, 0.24), 0.5, (1.0, 0.72, 0.38), 8)
        cb("podiumB", (26, 16, 6), (19, 41, 3), (0.38, 0.30, 0.22), bev=0.2)
        glow("lobbyB", (8, 0.1, 2.6), (19, 32.96, 2.3), (1.0, 0.75, 0.4), 4.0)
        lib.area_light("warmB", (19, 30, 5), (19, 20, 0), 6000, 8, (1.0, 0.7, 0.35))
        for i in range(6):
            cb(f"carB{i}", (1.8, 4.0, 1.1), (10 + i * 3.4, 29, 0.85), [(0.5, 0.05, 0.05), (0.7, 0.7, 0.7), (0.05, 0.1, 0.35), (0.6, 0.5, 0.1)][i % 4], bev=0.35)
    # half-drowned street: car, lamp posts, wall, floating debris
    cb("car", (1.9, 4.2, 1.15), (-5.5, 9, 0.75), (0.30, 0.31, 0.33), rot=(0, 3, 24), bev=0.4)
    cb("car_top", (1.6, 2.2, 0.7), (-5.5, 9.2, 1.5), (0.20, 0.21, 0.23), rot=(0, 3, 24), bev=0.3)
    cb("moto", (0.5, 1.7, 0.9), (4.2, 7.5, 0.7), (0.5, 0.06, 0.05), rot=(0, 12, -15), bev=0.2)
    for i, x in enumerate((-12, 0, 12)):
        cyl(f"lamp{i}", 0.09, 7, (x + 3, 14, 3.5), (0.07, 0.07, 0.08)); cb(f"lamp_arm{i}", (1.4, 0.12, 0.12), (x + 2.4, 14, 6.9), (0.07, 0.07, 0.08))
        on = i == 1
        glow(f"lamp_h{i}", (0.5, 0.25, 0.08), (x + 1.8, 14, 6.82), (1.0, 0.75, 0.4), 6.0 if on else 0.05)
        if on:
            lib.point_light("lamp_l", (x + 1.8, 14, 6.6), 2500, (1.0, 0.72, 0.38), 0.3)
    for i in range(7):
        cb(f"fence{i}", (3.9, 0.25, 1.9), (-14 + i * 4, 17.5, 0.95), (0.16, 0.17, 0.16), bev=0.05)
    for i, (x, y, s) in enumerate(((-2, 6, 0.5), (2.5, 11, 0.7), (-9, 12, 0.4), (7, 5, 0.6))):
        cb(f"debris{i}", (s, s * 1.4, 0.12), (x, y, 0.47), (0.25, 0.16, 0.08), rot=(3, 2, 30 * i), bev=0.03)
    lib.world((0.012, 0.018, 0.035) if night else (0.25, 0.28, 0.32), 1.0)
    lib.sun("moon", (-0.35, 0.6, -0.5), 0.35 if night else 2.2, (0.55, 0.68, 1.0) if night else (0.8, 0.85, 0.95), 2.0)
    lib.fog_volume((-60, -20, 0), (60, 60, 90), 0.0012)
    cams = {"wide": ((3.5, -34, 2.0), (0, 30, 20), 24), "low": ((-1, -4, 0.9), (0, 30, 22), 20),
            "twin": ((4, -52, 2.4), (5, 36, 22), 26)}
    return cams, {}


# =================================================================== 7. bedroom (Sari at home / Reza at a friend's)
def bedroom(variant="sari"):
    wallc = (0.34, 0.30, 0.36) if variant == "sari" else (0.26, 0.31, 0.30)
    cb("b_floor", (4, 4, 0.06), (0, 0, -0.03), (0.22, 0.14, 0.08), bev=0.005)
    cb("b_ceil", (4, 4, 0.06), (0, 0, 2.63), (0.3, 0.3, 0.28), bev=0.005)
    cb("b_back", (4, 0.12, 2.6), (0, 2.0, 1.3), wallc); cb("b_left", (0.12, 4, 2.6), (-2.0, 0, 1.3), wallc); cb("b_right", (0.12, 4, 2.6), (2.0, 0, 1.3), wallc)
    cb("bed", (1.3, 2.1, 0.32), (-0.9, 0.85, 0.2), (0.24, 0.13, 0.07), bev=0.05)
    cb("mattress", (1.22, 2.0, 0.2), (-0.9, 0.85, 0.44), (0.72, 0.70, 0.64), bev=0.08)
    cb("blanket", (1.28, 1.25, 0.14), (-0.9, 0.45, 0.56), (0.55, 0.25, 0.30) if variant == "sari" else (0.15, 0.3, 0.2), bev=0.07)
    cb("pillow", (0.75, 0.42, 0.16), (-0.9, 1.6, 0.6), (0.80, 0.78, 0.72), bev=0.08)
    cb("nstand", (0.5, 0.45, 0.55), (0.1, 1.7, 0.275), (0.22, 0.12, 0.06)); cb("phone", (0.08, 0.16, 0.012), (0.1, 1.65, 0.56), (0.02, 0.02, 0.02), bev=0.005)
    glow("phone_scr", (0.07, 0.145, 0.004), (0.1, 1.65, 0.568), (0.75, 0.85, 1.0), 2.5)
    lib.point_light("phone_l", (0.1, 1.6, 0.75), 3.5, (0.7, 0.82, 1.0), 0.05)
    cb("win_frame", (1.3, 0.06, 1.2), (1.0, 1.94, 1.5), (0.6, 0.6, 0.56), bev=0.02); glow("win", (1.15, 0.03, 1.05), (1.0, 1.9, 1.5), (0.25, 0.35, 0.6), 0.5)
    cb("win_bar", (0.05, 0.05, 1.1), (1.0, 1.88, 1.5), (0.6, 0.6, 0.56)); cb("curtain", (0.4, 0.08, 1.5), (1.75, 1.86, 1.45), (0.3, 0.12, 0.14), bev=0.04)
    mo = lib.area_light("b_moon", (1.0, 1.7, 1.6), (-0.6, -0.4, 0.3), 26, 1.0, (0.5, 0.64, 1.0))
    if variant == "reza":
        cb("helmet", (0.32, 0.34, 0.3), (1.5, -0.4, 0.15), (0.6, 0.1, 0.05), bev=0.14); cb("mat2", (0.9, 1.9, 0.1), (1.2, 0.3, 0.06), (0.3, 0.32, 0.4), bev=0.04)
        text("clock", "02:00", (-0.9, 1.93, 1.9), 0.2, (1.0, 0.1, 0.05), emit=3.0)
    else:
        text("clock", "03:00", (-0.9, 1.93, 1.9), 0.2, (1.0, 0.1, 0.05), emit=3.0)
    lib.world((0.003, 0.004, 0.008), 1.0)
    cams = {"wide": ((1.5, -1.7, 1.5), (-0.6, 1.2, 0.7), 28), "bed": ((0.5, -0.4, 1.1), (-0.9, 1.2, 0.7), 40)}
    marks = {"bed_sit": ((-0.9, 0.95, 0.5), R(160)), "floor_sit": ((1.2, 0.2, 0.1), R(200))}
    return cams, marks


# =================================================================== previews
def preview(sc, name, shot):
    put = lambda n, mark, marks, **kw: fig.make(n, loc=marks[mark][0], rot_z=marks[mark][1], **kw)
    sc.view_settings.look = "AgX - Base Contrast"
    sc.cycles.volume_step_rate = 4.0; sc.cycles.volume_bounces = 0
    ex = lambda e: dict(exprs=[e], expr=e)
    if name == "unit_siang":
        cams, mk = unit(night=False)
        put("sari", "center", mk, **ex("netral")); a = put("bagas", "desk_a", mk, **ex("cemas")); a.location = (-0.9, -0.3, 0); a.rotation_euler.z = R(-110)
        sc.view_settings.exposure = 0.3; shot(sc, name, (0.3, -4.25, 1.75), (0.4, 0.6, 0.85), 22, soft=False)
    elif name == "unit_malam":
        cams, mk = unit(night=True, lights_on=False, bedcover=True)
        a = fig.make("sari", **ex("takut")); fig.lie_down(a, (-0.86, -2.35, 0.30))
        sc.view_settings.exposure = 1.6; shot(sc, name, (0.5, -3.3, 1.7), (-0.8, -1.5, 0.25), 32, soft=False)
    elif name == "unit_pintu":
        cams, mk = unit(night=False, door_open=0.9)
        a = fig.make("nadia", loc=(-0.5, -2.5, 0), rot_z=R(-125), **ex("teriak")); fig.pose(a, "scared")
        g = fig.make("hantu", loc=(-3.0, -0.5, 0.05), rot_z=R(90))
        sc.view_settings.exposure = 0.5; shot(sc, name, (1.6, -2.4, 1.3), (-2.5, -0.9, 1.0), 30, soft=False)
    elif name == "lorong6":
        cams, mk = corridor("6")
        a = put("sari", "mid", mk, **ex("cemas")); fig.pose(a, "nervous")
        sc.view_settings.exposure = 1.2; shot(sc, name, *cams["long"], soft=False)
    elif name == "lorong7":
        cams, mk = corridor("7", dead=(1, 3))
        a = put("nadia", "unit_door", mk, **ex("marah")); fig.pose(a, "knock")
        sc.view_settings.exposure = 1.5; shot(sc, name, *cams["end"], soft=False)
    elif name == "tangga":
        cams, mk = stairs("3")
        a = put("sari", "a", mk, **ex("takut")); fig.pose(a, "phone"); put("bagas", "b", mk, **ex("cemas")); put("reza", "c", mk, **ex("netral"))
        lib.point_light("hp", (0.45, 0.2, 2.1), 2.5, (0.75, 0.85, 1.0), 0.03)
        sc.view_settings.exposure = 1.8; shot(sc, name, *cams["down"], soft=False)
    elif name == "lift":
        cams, mk = lift("7")
        a = put("penghuni", "rider", mk, **ex("teriak")); fig.pose(a, "scared"); put("hantu", "ghost", mk)
        sc.view_settings.exposure = 0.8; shot(sc, name, *cams["inside"], soft=False)
    elif name == "lobi":
        cams, mk = lobby()
        for n, e in (("sari", "cemas"), ("bagas", "cemas"), ("hendra", "netral"), ("wulan", "senyum"), ("nadia", "netral"), ("fajar", "senyum")):
            put(n, n, mk, **ex(e))
        sc.view_settings.exposure = 0.6; shot(sc, name, *cams["wide"], soft=False)
    elif name == "eksterior":
        cams, mk = exterior(twin=False)
        sc.view_settings.exposure = 2.0; shot(sc, name, *cams["wide"], soft=False)
    elif name == "kembar":
        cams, mk = exterior(twin=True)
        sc.view_settings.exposure = 2.0; shot(sc, name, *cams["twin"], soft=False)
    elif name == "kamar_sari":
        cams, mk = bedroom("sari")
        a = fig.make("sari", loc=(-0.9, 0.95, 0.12), rot_z=R(40), **ex("capek")); fig.pose(a, "phone")
        sc.view_settings.exposure = 1.8; shot(sc, name, (0.9, -1.0, 1.3), (-0.8, 1.0, 0.95), 35, soft=False)
    elif name == "kamar_reza":
        cams, mk = bedroom("reza")
        a = fig.make("reza", loc=(1.2, 0.35, -0.35), rot_z=R(-20), **ex("takut")); fig.pose(a, "phone")
        sc.view_settings.exposure = 1.8; shot(sc, name, (0.2, -1.6, 1.2), (1.0, 0.8, 0.75), 32, soft=False)


# =================================================================== 8. bathroom (Sari hears the dragging above)
def bathroom():
    tile = (0.42, 0.46, 0.44)
    cb("bt_floor", (2.2, 2.4, 0.06), (0, 0, -0.03), (0.16, 0.17, 0.16), bev=0.005)
    for i in range(-5, 6):
        cb(f"bt_gx{i}", (0.012, 2.4, 0.004), (i * 0.2, 0, 0.002), (0.06, 0.06, 0.06), bev=0.001)
    cb("bt_ceil", (2.2, 2.4, 0.06), (0, 0, 2.43), (0.30, 0.29, 0.26), bev=0.005)
    cb("bt_stain", (0.7, 0.5, 0.01), (0.2, 0.3, 2.395), (0.12, 0.10, 0.07), bev=0.004)
    cb("bt_back", (2.2, 0.1, 2.4), (0, 1.2, 1.2), tile); cb("bt_left", (0.1, 2.4, 2.4), (-1.1, 0, 1.2), tile)
    cb("bt_right", (0.1, 2.4, 2.4), (1.1, 0, 1.2), tile)
    for z in (0.6, 1.0, 1.4, 1.8):
        cb(f"bt_line{z}", (2.2, 0.012, 0.01), (0, 1.145, z), (0.1, 0.1, 0.1), bev=0.003)
    cb("sink", (0.55, 0.42, 0.16), (-0.35, 0.95, 0.85), (0.75, 0.75, 0.72), bev=0.06)
    cyl("sink_leg", 0.07, 0.78, (-0.35, 1.0, 0.39), (0.75, 0.75, 0.72))
    cb("mirror", (0.5, 0.03, 0.65), (-0.35, 1.14, 1.5), (0.55, 0.62, 0.65), rough=0.05) if False else cb("mirror", (0.5, 0.03, 0.65), (-0.35, 1.14, 1.5), (0.55, 0.62, 0.65))
    cb("toilet", (0.4, 0.55, 0.42), (0.6, 0.85, 0.21), (0.78, 0.78, 0.74), bev=0.12)
    cb("tank", (0.42, 0.18, 0.4), (0.6, 1.08, 0.62), (0.78, 0.78, 0.74), bev=0.06)
    cyl("bucket", 0.16, 0.32, (0.75, -0.3, 0.16), (0.15, 0.35, 0.6))
    cyl("bulb", 0.05, 0.08, (0, 0.2, 2.36), (0.9, 0.9, 0.8))
    glow("bulb_g", (0.07, 0.07, 0.04), (0, 0.2, 2.32), (1.0, 0.85, 0.6), 6.0)
    lib.point_light("bt_bulb", (0, 0.2, 2.25), 26, (1.0, 0.80, 0.55), 0.06)
    lib.world((0.003, 0.003, 0.004), 1.0)
    cams = {"door": ((0.05, -1.05, 1.45), (-0.1, 0.8, 1.05), 24), "up": ((0.55, -0.6, 0.55), (-0.1, 0.3, 1.6), 22),
            "ceil": ((0.05, -0.3, 1.25), (0.15, 0.3, 2.4), 24)}
    marks = {"in": ((-0.1, 0.1, 0), R(0)), "door": ((0.0, -1.0, 0), R(0))}
    return cams, marks


# =================================================================== 9. parking (Reza's motorbike starts by itself)
def parking():
    cb("pk_floor", (14, 10, 0.08), (0, 0, -0.04), (0.20, 0.20, 0.19), bev=0.01)
    for i in range(-3, 4):
        cb(f"pk_line{i}", (0.08, 4.0, 0.006), (i * 2.0, 1.0, 0.004), (0.62, 0.58, 0.2), bev=0.002)
    cb("pk_ceil", (14, 10, 0.2), (0, 0, 3.1), (0.24, 0.24, 0.22), bev=0.01)
    for x in (-4.5, 0, 4.5):
        cb(f"pk_col{x}", (0.5, 0.5, 3.0), (x, 3.0, 1.5), (0.30, 0.30, 0.28), bev=0.03)
    cb("pk_back", (14, 0.2, 3.0), (0, 4.8, 1.5), (0.27, 0.29, 0.26), bev=0.01)
    cb("pk_water", (14, 0.6, 0.02), (0, 4.4, 0.01), (0.05, 0.04, 0.03), bev=0.004)
    # motorbike
    red, blk, chrome = (0.45, 0.04, 0.03), (0.02, 0.02, 0.022), (0.5, 0.5, 0.52)
    for y in (-0.65, 0.65):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.27, minor_radius=0.075, location=(0.6, 1.0 + y, 0.32), rotation=(0, R(90), 0))
        t = bpy.context.object; t.name = f"tyre{y}"; t.data.materials.append(C(blk, 0.6)); bpy.ops.object.shade_smooth()
        cyl(f"hub{y}", 0.12, 0.1, (0.6, 1.0 + y, 0.32), chrome, rot=(0, 90, 0))
    cb("mb_body", (0.34, 1.05, 0.34), (0.6, 1.0, 0.62), red, bev=0.12)
    cb("mb_seat", (0.3, 0.7, 0.12), (0.6, 1.2, 0.86), blk, bev=0.05)
    cb("mb_front", (0.3, 0.3, 0.55), (0.6, 0.38, 0.78), red, rot=(-18, 0, 0), bev=0.1)
    cyl("mb_bar", 0.025, 0.75, (0.6, 0.30, 1.1), chrome, rot=(0, 90, 0))
    cyl("mb_lamp", 0.085, 0.06, (0.6, 0.24, 0.98), chrome, rot=(90, 0, 0))
    glow("mb_head", (0.13, 0.02, 0.13), (0.6, 0.2, 0.98), (1.0, 0.93, 0.75), 0.0)
    cb("helmet", (0.3, 0.32, 0.28), (0.6, 1.25, 1.06), (0.6, 0.1, 0.05), bev=0.13)
    for i, x in enumerate((-3.2, 3.6, 5.6)):
        cb(f"pk_car{i}", (1.8, 4.0, 1.15), (x, 1.5, 0.62), [(0.3, 0.32, 0.35), (0.6, 0.6, 0.58), (0.1, 0.12, 0.25)][i], bev=0.35)
        cb(f"pk_cart{i}", (1.55, 2.1, 0.62), (x, 1.7, 1.45), (0.12, 0.13, 0.15), bev=0.25)
    day = lib.area_light("pk_day", (0, -6.0, 2.2), (0, 2, 0.8), 900, 6.0, (0.75, 0.82, 0.95)); day.data.shape = "RECTANGLE"; day.data.size_y = 2.5
    tube("pk_t1", (0.6, 0.5, 3.0), on=0.7, along="x", power=24); tube("pk_t2", (-3.5, 1.5, 3.0), on=0.0, along="x")
    lib.world((0.03, 0.035, 0.04), 1.0)
    cams = {"wide": ((-2.6, -3.0, 1.5), (0.4, 1.0, 0.7), 28), "close": ((1.6, -0.6, 1.25), (0.3, 0.9, 1.05), 40),
            "lamp": ((0.55, -0.9, 0.95), (0.6, 0.3, 0.95), 35)}
    marks = {"reza": ((-0.15, 0.85, 0), R(-80))}
    return cams, marks
