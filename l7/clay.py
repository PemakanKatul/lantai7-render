"""Claymation look: plasticine material, clay-ified apartment set, procedural clay people.
Characters are rigid clay parts parented to a simple armature (like a stop-motion puppet).
Every character faces -Y with feet at z=0.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler
import lib


# ------------------------------------------------------------------ material
def _set(b, names, v):
    for n in names if isinstance(names, (list, tuple)) else [names]:
        if n in b.inputs:
            b.inputs[n].default_value = v
            return


def clay_mat(name, color, rough=0.58, sss=0.0, dents=1.0, emit=None, emit_str=0.0, grooves=0.0):
    """Plasticine: matte with a faint sheen, thumb dents + fine grain bump, slight colour mottling."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    _set(b, "Roughness", rough)
    _set(b, ["Specular IOR Level", "Specular"], 0.32)
    _set(b, ["Sheen Weight", "Sheen"], 0.25)
    _set(b, "Sheen Roughness", 0.6)
    if sss:
        _set(b, ["Subsurface Weight", "Subsurface"], sss)
        _set(b, "Subsurface Radius", (1.0, 0.45, 0.25))
        _set(b, "Subsurface Scale", 0.02)
    if emit:
        _set(b, ["Emission Color", "Emission"], (*emit, 1))
        _set(b, "Emission Strength", emit_str)
    tc = N.new("ShaderNodeTexCoord")
    # colour mottling
    mott = N.new("ShaderNodeTexNoise"); mott.inputs["Scale"].default_value = 6.0
    mott.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], mott.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.88; mr.inputs["To Max"].default_value = 1.10
    L.new(mott.outputs["Fac"], mr.inputs["Value"])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    mul.inputs[6].default_value = (*color, 1)
    L.new(mr.outputs["Result"], mul.inputs[7])
    L.new(mul.outputs[2], b.inputs["Base Color"])
    # thumb dents (smooth voronoi) + fine grain
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 7.0
    try:
        vor.feature = "SMOOTH_F1"
    except Exception:
        pass
    L.new(tc.outputs["Object"], vor.inputs["Vector"])
    grain = N.new("ShaderNodeTexNoise"); grain.inputs["Scale"].default_value = 180.0
    grain.inputs["Detail"].default_value = 2.0
    L.new(tc.outputs["Object"], grain.inputs["Vector"])
    b1 = N.new("ShaderNodeBump"); b1.inputs["Strength"].default_value = min(1.0, 0.55 * dents)
    b1.inputs["Distance"].default_value = 0.006
    L.new(vor.outputs["Distance"], b1.inputs["Height"])
    b2 = N.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.10
    b2.inputs["Distance"].default_value = 0.0008
    L.new(grain.outputs["Fac"], b2.inputs["Height"])
    L.new(b1.outputs["Normal"], b2.inputs["Normal"])
    last = b2
    if grooves:   # sculpted hair strands (tool grooves)
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
        wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 6.0
        wv.inputs["Detail"].default_value = 1.0
        L.new(tc.outputs["Object"], wv.inputs["Vector"])
        b3 = N.new("ShaderNodeBump"); b3.inputs["Strength"].default_value = grooves
        b3.inputs["Distance"].default_value = 0.004
        L.new(wv.outputs["Fac"], b3.inputs["Height"])
        L.new(b2.outputs["Normal"], b3.inputs["Normal"])
        last = b3
    L.new(last.outputs["Normal"], b.inputs["Normal"])
    return m


def _lumpy(o, strength=0.006, scale=0.15):
    """subtle hand-made unevenness"""
    tex = bpy.data.textures.get("clay_lumps") or bpy.data.textures.new("clay_lumps", "CLOUDS")
    tex.noise_scale = scale
    d = o.modifiers.new("lumps", "DISPLACE")
    d.texture = tex
    d.texture_coords = "GLOBAL"
    d.strength = strength
    d.mid_level = 0.5


# ------------------------------------------------------------------ set
SET_COLORS = [  # name prefix -> clay colour (linear)
    ("floor", (0.20, 0.15, 0.11)), ("corr_floor", (0.16, 0.12, 0.09)),
    ("ceiling", (0.30, 0.30, 0.27)), ("corr_ceil", (0.20, 0.20, 0.18)),
    ("wall", (0.30, 0.32, 0.27)), ("corr_wall", (0.18, 0.20, 0.17)),
    ("slat", (0.48, 0.46, 0.40)), ("door", (0.16, 0.07, 0.035)), ("knob", (0.35, 0.28, 0.10)),
    ("desk", (0.30, 0.18, 0.09)), ("leg", (0.04, 0.04, 0.045)), ("mon", (0.03, 0.03, 0.035)),
    ("stand", (0.03, 0.03, 0.035)), ("kb", (0.05, 0.05, 0.06)), ("papers", (0.70, 0.68, 0.60)),
    ("tube_fixture", (0.05, 0.05, 0.05)),
]
KEEP = ("scr", "tube_glow", "sky", "tower", "cw")


def clayify_set(bevel=0.025):
    """swap every set material for clay and round every edge"""
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o.name.startswith(KEEP):
            continue
        col = None
        for p, c in SET_COLORS:
            if o.name.startswith(p):
                col = c
        if col is None:
            continue
        o.data.materials.clear()
        o.data.materials.append(clay_mat("clay_set_" + "_".join(f"{v:.2f}" for v in col), col, dents=1.4))
        thin = min(o.dimensions)
        bv = o.modifiers.new("round", "BEVEL")
        bv.width = min(bevel, thin * 0.45)
        bv.segments = 3
        bv.limit_method = "ANGLE"
        for p in o.data.polygons:
            p.use_smooth = True
        try:
            bv.harden_normals = True
        except Exception:
            pass


def set_scene(fog=True):
    lights = lib.apartment_unit(fog=fog)
    clayify_set()
    # clay rug under the hero so the floor reads as a miniature, not a void
    rug = blob("rug", (0, -0.4, 0.006), (0.85, 0.6, 0.012), clay_mat("rug", (0.16, 0.035, 0.03), dents=1.6))
    return lights


# ------------------------------------------------------------------ primitives
def blob(name, loc, radii, m, rot=(0, 0, 0), seg=40, lumps=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc,
                                         rotation=[math.radians(a) for a in rot])
    o = bpy.context.object
    o.name = name
    o.scale = radii
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    if lumps:
        _lumpy(o)
    return o


def limb(name, a, b, r, m, r2=None):
    """ellipsoid stretched from point a to point b (rounded capsule)"""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    o = blob(name, (0, 0, 0), (r, r2 or r, L / 2 + r * 0.6), m, lumps=True)
    q = Vector((0, 0, 1)).rotation_difference((b - a).normalized())
    o.data.transform(q.to_matrix().to_4x4())
    o.location = (a + b) / 2
    return o


def cone_skirt(name, z0, z1, r0, r1, m, ry=0.78, seg=32, rings=8):
    """A-line skirt: lathe of rings from hem (z0, radius r0) to waist (z1, radius r1)"""
    bm = bmesh.new()
    loops = []
    for k in range(rings + 1):
        t = k / rings
        z = z0 + (z1 - z0) * t
        r = r0 + (r1 - r0) * (t ** 0.8)
        loops.append([bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * ry * math.sin(2 * math.pi * i / seg), z))
                      for i in range(seg)])
    for k in range(rings):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((loops[k][i], loops[k][j], loops[k + 1][j], loops[k + 1][i]))
    bm.faces.new(loops[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    sol = o.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.012
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    _lumpy(o)
    return o


# ------------------------------------------------------------------ rig
BONES = {  # name: (head, tail, parent)
    "pelvis": ((0, 0, 0.55), (0, 0, 0.75), None),
    "chest": ((0, 0, 0.75), (0, 0, 1.10), "pelvis"),
    "neck": ((0, 0, 1.10), (0, 0, 1.20), "chest"),
    "head": ((0, 0, 1.20), (0, 0, 1.55), "neck"),
    "upperarm.L": ((0.20, 0, 1.06), (0.24, 0, 0.82), "chest"),
    "forearm.L": ((0.24, 0, 0.82), (0.25, 0, 0.62), "upperarm.L"),
    "hand.L": ((0.25, 0, 0.62), (0.25, 0, 0.52), "forearm.L"),
    "upperarm.R": ((-0.20, 0, 1.06), (-0.24, 0, 0.82), "chest"),
    "forearm.R": ((-0.24, 0, 0.82), (-0.25, 0, 0.62), "upperarm.R"),
    "hand.R": ((-0.25, 0, 0.62), (-0.25, 0, 0.52), "forearm.R"),
    "thigh.L": ((0.085, 0, 0.55), (0.085, 0, 0.30), "pelvis"),
    "shin.L": ((0.085, 0, 0.30), (0.085, 0, 0.04), "thigh.L"),
    "thigh.R": ((-0.085, 0, 0.55), (-0.085, 0, 0.30), "pelvis"),
    "shin.R": ((-0.085, 0, 0.30), (-0.085, 0, 0.04), "thigh.R"),
}


def make_rig(name):
    d = bpy.data.armatures.new(name + "_rig")
    arm = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, (h, t, p) in BONES.items():
        e = d.edit_bones.new(bn)
        e.head, e.tail = h, t
        e.roll = 0
        if p:
            e.parent = d.edit_bones[p]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.show_in_front = False
    arm.hide_render = True
    return arm


def bind(arm, o, bone):
    mw = o.matrix_world.copy()
    o.parent = arm
    o.parent_type = "BONE"
    o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = mw


def rest(arm):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def point_bone(arm, bone, target, twist=0.0):
    """rotate bone (minimal rotation) so its tail points at a world-space target"""
    pb = arm.pose.bones[bone]
    inv = arm.matrix_world.inverted()
    head = pb.head.copy()                       # armature space (posed)
    d = (inv @ Vector(target)) - head
    cur = pb.matrix.to_3x3()
    y = cur.col[1].normalized()
    q = y.rotation_difference(d.normalized())
    if twist:
        q = Matrix.Rotation(math.radians(twist), 3, d.normalized()).to_quaternion() @ q
    M = (q.to_matrix() @ cur).to_4x4()
    M.translation = head
    pb.matrix = M
    bpy.context.view_layer.update()


def world_pt(arm, local):
    """rest-space point relative to the character origin -> world (follows arm loc/rot)"""
    return arm.matrix_world @ Vector(local)


def pose(arm, name):
    rest(arm)
    P = lambda v: world_pt(arm, v)
    if name == "idle":
        point_bone(arm, "upperarm.L", P((0.235, 0.0, 0.82)))
        point_bone(arm, "upperarm.R", P((-0.235, 0.0, 0.82)))
        point_bone(arm, "forearm.L", P((0.235, -0.04, 0.62)))
        point_bone(arm, "forearm.R", P((-0.235, -0.04, 0.62)))
    elif name == "nervous":   # hunched, hands clasped under the chin, head tilted, eyes up
        point_bone(arm, "chest", P((0, -0.05, 1.10)))
        point_bone(arm, "head", P((0.07, -0.10, 1.53)))
        point_bone(arm, "upperarm.L", P((0.215, -0.15, 0.87)))
        point_bone(arm, "upperarm.R", P((-0.215, -0.15, 0.87)))
        point_bone(arm, "forearm.L", P((0.03, -0.29, 0.99)))
        point_bone(arm, "forearm.R", P((-0.03, -0.29, 0.99)))
        point_bone(arm, "hand.L", P((0.0, -0.31, 1.09)))
        point_bone(arm, "hand.R", P((0.0, -0.31, 1.09)))
    elif name == "scared":    # recoiling, hands up near the face
        point_bone(arm, "chest", P((0, 0.06, 1.10)))
        point_bone(arm, "head", P((-0.04, 0.05, 1.55)))
        point_bone(arm, "upperarm.L", P((0.26, -0.08, 0.90)))
        point_bone(arm, "upperarm.R", P((-0.26, -0.08, 0.90)))
        point_bone(arm, "forearm.L", P((0.13, -0.20, 1.20)))
        point_bone(arm, "forearm.R", P((-0.13, -0.20, 1.20)))
    return arm


# ------------------------------------------------------------------ people
SKIN = {"sawo": (0.40, 0.20, 0.105), "kuning": (0.52, 0.30, 0.17), "gelap": (0.24, 0.11, 0.055)}


def clay_person(name="sari", loc=(0, 0, 0), rot_z=0.0, skin="sawo",
                shirt=(0.70, 0.74, 0.80), bottom=(0.02, 0.03, 0.08), hair=(0.012, 0.008, 0.006),
                shoes=(0.02, 0.018, 0.018), hairstyle="bun", skirt=True):
    """Build a clay office worker. Returns the armature (parts are bone-parented to it)."""
    sk = clay_mat(f"{name}_skin", SKIN[skin], rough=0.5, sss=0.25, dents=0.6)
    sh = clay_mat(f"{name}_shirt", shirt, dents=1.0)
    bt = clay_mat(f"{name}_bottom", bottom, dents=1.0)
    hr = clay_mat(f"{name}_hair", hair, rough=0.45, dents=1.2, grooves=0.45)
    so = clay_mat(f"{name}_shoes", shoes, rough=0.35)
    white = clay_mat("eye_white", (0.80, 0.78, 0.72), rough=0.25, dents=0.0)
    iris = clay_mat("iris", (0.045, 0.020, 0.010), rough=0.2, dents=0.0)
    shine = clay_mat("eye_shine", (1, 1, 1), rough=0.1, dents=0.0, emit=(1, 1, 1), emit_str=1.5)
    dark = clay_mat(f"{name}_brow", tuple(c * 1.2 for c in hair), dents=0.5)
    lip = clay_mat(f"{name}_mouth", (0.22, 0.05, 0.05), rough=0.4, dents=0.0)
    blush = clay_mat(f"{name}_blush", tuple(c * k for c, k in zip(SKIN[skin], (1.25, 0.85, 0.85))), rough=0.5, dents=0.3)
    btn = clay_mat("button", (0.06, 0.06, 0.07), rough=0.3, dents=0.0)

    arm = make_rig(name)
    parts = []

    def add(o, bone):
        parts.append((o, bone))
        return o

    def lim(n, a, b, r, m, bone):
        return add(limb(n, a, b, r, m), bone)

    # legs + shoes
    for s, lr in ((1, "L"), (-1, "R")):
        x = 0.085 * s
        lim(f"{name}_thigh{lr}", (x, 0, 0.52), (x, 0, 0.30), 0.055, sk, f"thigh.{lr}")
        lim(f"{name}_shin{lr}", (x, 0, 0.30), (x, 0, 0.07), 0.048, sk, f"shin.{lr}")
        add(blob(f"{name}_shoe{lr}", (x, -0.035, 0.035), (0.058, 0.095, 0.038), so), f"shin.{lr}")
    # skirt or trousers
    if skirt:
        add(cone_skirt(f"{name}_skirt", 0.36, 0.74, 0.24, 0.17, bt), "pelvis")
    else:
        for s, lr in ((1, "L"), (-1, "R")):
            x = 0.085 * s
            lim(f"{name}_trouserT{lr}", (x, 0, 0.62), (x, 0, 0.30), 0.068, bt, f"thigh.{lr}")
            lim(f"{name}_trouserS{lr}", (x, 0, 0.30), (x, 0, 0.09), 0.06, bt, f"shin.{lr}")
        add(blob(f"{name}_hips", (0, 0, 0.66), (0.17, 0.12, 0.11), bt), "pelvis")
    # torso (shirt), buttons, collar
    add(blob(f"{name}_torso", (0, 0, 0.92), (0.175, 0.13, 0.25), sh), "chest")
    for z in (1.02, 0.94, 0.86, 0.78):
        y = -0.13 * math.sqrt(max(0, 1 - ((z - 0.92) / 0.25) ** 2)) - 0.004
        add(blob(f"{name}_btn{z}", (0, y, z), (0.011, 0.006, 0.011), btn, lumps=False), "chest")
    for s in (1, -1):
        add(blob(f"{name}_collar{s}", (0.045 * s, -0.075, 1.125), (0.06, 0.02, 0.035),
                 clay_mat(f"{name}_collar", tuple(min(1, c * 1.12) for c in shirt)), rot=(-25, 0, 32 * s)), "chest")
    # neck + head
    add(blob(f"{name}_neck", (0, 0.0, 1.16), (0.048, 0.048, 0.07), sk), "neck")
    hx, hy, hz, HC = 0.20, 0.185, 0.215, 1.36
    add(blob(f"{name}_head", (0, 0, HC), (hx, hy, hz), sk, seg=56), "head")

    def surf_y(x, z):
        return -hy * math.sqrt(max(0.0, 1 - (x / hx) ** 2 - ((z - HC) / hz) ** 2))

    for s, lr in ((1, "L"), (-1, "R")):
        ex, ez = 0.072 * s, 1.385
        ey = surf_y(ex, ez)
        add(blob(f"{name}_eye{lr}", (ex, ey + 0.01, ez), (0.043, 0.024, 0.05), white, lumps=False), "head")
        add(blob(f"{name}_iris{lr}", (ex * 0.97, ey - 0.012, ez - 0.006), (0.025, 0.008, 0.029), iris, lumps=False), "head")
        add(blob(f"{name}_shine{lr}", (ex * 0.97 + 0.009, ey - 0.019, ez + 0.008), (0.0065, 0.003, 0.0065), shine, lumps=False), "head")
        # worried brows: inner ends raised
        bx, bz = 0.075 * s, 1.47
        add(blob(f"{name}_brow{lr}", (bx, surf_y(bx, bz) - 0.006, bz), (0.036, 0.011, 0.009), dark,
                 rot=(0, 16 * s, 0), lumps=False), "head")
        # lashes at the outer upper corner + cheek blush
        add(blob(f"{name}_lash{lr}", (ex * 1.42, ey + 0.004, ez + 0.03), (0.022, 0.008, 0.007), dark,
                 rot=(0, -28 * s, 0), lumps=False), "head")
        cx, cz = 0.118 * s, 1.315
        add(blob(f"{name}_blush{lr}", (cx, surf_y(cx, cz) + 0.004, cz), (0.034, 0.008, 0.022), blush, lumps=False), "head")
        # ears
        add(blob(f"{name}_ear{lr}", (0.197 * s, 0.005, 1.36), (0.022, 0.034, 0.046), sk), "head")
    add(blob(f"{name}_nose", (0, surf_y(0, 1.33) - 0.004, 1.33), (0.018, 0.017, 0.018), sk), "head")
    add(blob(f"{name}_mouth", (0, surf_y(0, 1.265) + 0.002, 1.265), (0.021, 0.008, 0.011), lip, lumps=False), "head")
    # hair: shell with the face cut out, side fringe, bun
    cap = blob(f"{name}_hair", (0, 0.012, HC + 0.02), (hx + 0.022, hy + 0.024, hz + 0.02), hr, seg=64, lumps=False)
    bm = bmesh.new(); bm.from_mesh(cap.data)
    kill = [v for v in bm.verts if (v.co.y < -0.05 and v.co.z < 1.505 - 1.6 * v.co.x ** 2) or v.co.z < 1.235 or
            (v.co.y < 0.03 and v.co.z < 1.325)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(cap.data); bm.free()
    so_ = cap.modifiers.new("thick", "SOLIDIFY"); so_.thickness = 0.016; so_.offset = 1.0
    sub = cap.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    _lumpy(cap, 0.006)
    add(cap, "head")
    for s, lr in ((1, "L"), (-1, "R")):
        # curtain bangs swept from a centre part
        add(blob(f"{name}_bang{lr}", (0.075 * s, -0.152, 1.488), (0.085, 0.036, 0.04), hr, rot=(18, 0, -22 * s)), "head")
        # loose strands framing the face
        add(limb(f"{name}_strand{lr}", (0.168 * s, -0.095, 1.45), (0.178 * s, -0.11, 1.28), 0.016, hr), "head")
    if hairstyle == "bun":
        add(blob(f"{name}_bun", (0, 0.205, 1.30), (0.085, 0.07, 0.075), hr), "head")
        add(blob(f"{name}_tie", (0, 0.16, 1.32), (0.04, 0.02, 0.035), clay_mat("hair_tie", (0.25, 0.03, 0.03))), "head")
    # arms (long sleeves) + mitten hands
    for s, lr in ((1, "L"), (-1, "R")):
        lim(f"{name}_upper{lr}", (0.20 * s, 0, 1.05), (0.24 * s, 0, 0.83), 0.05, sh, f"upperarm.{lr}")
        lim(f"{name}_fore{lr}", (0.24 * s, 0, 0.83), (0.25 * s, 0, 0.64), 0.045, sh, f"forearm.{lr}")
        add(blob(f"{name}_hand{lr}", (0.25 * s, -0.005, 0.585), (0.04, 0.03, 0.058), sk), f"hand.{lr}")
        add(blob(f"{name}_thumb{lr}", (0.235 * s, -0.035, 0.6), (0.015, 0.015, 0.03), sk, rot=(0, -20 * s, 0)), f"hand.{lr}")
        add(blob(f"{name}_shoulder{lr}", (0.175 * s, 0, 1.055), (0.05, 0.062, 0.045), sh), "chest")

    for o, bone in parts:
        bind(arm, o, bone)
    arm.location = loc
    arm.rotation_euler.z = rot_z
    bpy.context.view_layer.update()
    return arm
