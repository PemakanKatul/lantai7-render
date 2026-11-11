"""Fused-clay figurines (approved style). Parts of the same clay colour are voxel-merged into
one surface, like plasticine pressed together. Built at unit height 1.0 and scaled by the
armature. Faces -Y, feet at z=0.

person(...)            -> armature (all parts parented / skinned to it)
set_expr(arm, "takut") -> swap the face (brows, lids, pupils, mouth, tears)
pose(arm, "nervous")   -> body pose
"""
import math
import bpy
import bmesh
from mathutils import Vector
import clay
import toon
from clay import blob, limb, bind
from toon import curve, taper, torus, rbox, bake, Head, skin_mesh, surface_hit, M

UP = Vector((0, 0, 1))
BONES = {
    "pelvis": ((0, 0, 0.36), (0, 0, 0.46), None),
    "chest": ((0, 0, 0.46), (0, 0, 0.64), "pelvis"),
    "neck": ((0, 0, 0.64), (0, 0, 0.69), "chest"),
    "head": ((0, 0, 0.69), (0, 0, 1.0), "neck"),
    "upperarm.L": ((0.125, 0, 0.615), (0.185, 0.005, 0.50), "chest"),
    "forearm.L": ((0.185, 0.005, 0.50), (0.20, -0.01, 0.39), "upperarm.L"),
    "hand.L": ((0.20, -0.01, 0.39), (0.203, -0.015, 0.31), "forearm.L"),
    "upperarm.R": ((-0.125, 0, 0.615), (-0.185, 0.005, 0.50), "chest"),
    "forearm.R": ((-0.185, 0.005, 0.50), (-0.20, -0.01, 0.39), "upperarm.R"),
    "hand.R": ((-0.20, -0.01, 0.39), (-0.203, -0.015, 0.31), "forearm.R"),
    "leg.L": ((0.07, 0, 0.36), (0.07, 0, 0.05), "pelvis"),
    "leg.R": ((-0.07, 0, 0.36), (-0.07, 0, 0.05), "pelvis"),
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
        if p:
            e.parent = d.edit_bones[p]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.hide_render = True
    return arm


def skin_to(arm, o, bones, power=5.0):
    segs = {b: (Vector(BONES[b][0]), Vector(BONES[b][1])) for b in bones}
    groups = {b: o.vertex_groups.new(name=b) for b in bones}
    for v in o.data.vertices:
        ds = sorted(((toon._seg_dist(v.co, *segs[b]), b) for b in bones))[:2]
        ws = [1.0 / (d + 1e-3) ** power for d, _ in ds]
        s = sum(ws)
        for (d, b), w in zip(ds, ws):
            groups[b].add([v.index], w / s, "REPLACE")
    md = o.modifiers.new("arm", "ARMATURE")
    md.object = arm
    o.parent = arm


def fuse(name, objs, m, voxel=0.005, smooth=8, factor=0.7):
    """merge overlapping parts into one clay surface"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in objs:
        bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    r = o.modifiers.new("vox", "REMESH"); r.mode = "VOXEL"; r.voxel_size = voxel; r.adaptivity = 0.0
    if smooth:
        s = o.modifiers.new("sm", "SMOOTH"); s.factor = factor; s.iterations = smooth
    bake(o)
    o.data.materials.append(m)
    return o


def hit(o, x, z):
    return surface_hit(o, (x, -2, z), (0, 1, 0))


SKIN = {"sawo": (0.36, 0.185, 0.10), "kuning": (0.50, 0.29, 0.165), "gelap": (0.23, 0.11, 0.058),
        "hantu": (0.42, 0.45, 0.42)}

# ------------------------------------------------------------------ expressions
# lid: how open the upper lid is (None = no lid = wide eyes, "closed" = shut)
# tilt: + droops toward the outer corner (sad), - toward the nose (angry)
# brow: (inner dz, outer dz) relative to neutral; mouth: shape key; iris: pupil/iris scale
EXPR = {
    "netral": dict(lid=0.026, tilt=0.05, brow=(0.0, 0.0), mouth="flat", iris=1.0),
    "cemas":  dict(lid=0.017, tilt=0.30, brow=(0.012, -0.012), mouth="frown", iris=1.0),
    "takut":  dict(lid=None, tilt=0.0, brow=(0.022, 0.004), mouth="o", iris=0.72),
    "teriak": dict(lid=None, tilt=0.0, brow=(0.026, 0.0), mouth="scream", iris=0.62),
    "marah":  dict(lid=0.020, tilt=-0.42, brow=(-0.03, 0.012), mouth="shout", iris=0.9),
    "nangis": dict(lid=0.010, tilt=0.38, brow=(0.018, -0.016), mouth="wail", iris=1.0, tears=True),
    "capek":  dict(lid=0.004, tilt=0.12, brow=(-0.004, -0.008), mouth="flat", iris=1.0),
    "senyum": dict(lid=0.022, tilt=0.0, brow=(0.004, 0.004), mouth="smile", iris=1.0),
    "tidur":  dict(lid="closed", tilt=0.0, brow=(0.0, -0.004), mouth="flat", iris=1.0),
    "hantu":  dict(lid=None, tilt=0.0, brow=None, mouth="scream", iris=0.0),
}


def set_expr(arm, expr):
    """show one face set, hide the others"""
    tag = f"{arm.name}__"
    for o in bpy.data.objects:
        if o.name.startswith(tag):
            on = o.name.split("__")[1] == expr
            o.hide_render = not on
            o.hide_viewport = not on
    arm["expr"] = expr


def key_expr(arm, expr, frame):
    """keyframe an expression switch at a frame (constant interpolation by nature of visibility)"""
    tag = f"{arm.name}__"
    for o in bpy.data.objects:
        if o.name.startswith(tag):
            o.hide_render = o.name.split("__")[1] != expr
            o.keyframe_insert("hide_render", frame=frame)


def person(name="sari", gender="f", skin="sawo", shirt=(0.60, 0.69, 0.80), bottom=(0.04, 0.05, 0.12),
           hair=(0.025, 0.014, 0.01), shoes=(0.10, 0.045, 0.025), lanyard=(0.05, 0.14, 0.5),
           hair_style="bun", skirt=None, long_skirt=False, hijab=None, glasses=False, mustache=False,
           tie=None, cap=None, collar=None, build=1.0, nose=1.0, scale=1.45, ghost=False,
           exprs=None, expr="cemas", loc=(0, 0, 0), rot_z=0.0):
    if skirt is None:
        skirt = gender == "f"
    skc = SKIN[skin]
    sk = M(f"{name}_skin", skc, rough=0.55, sss=0.2, dents=0.18)
    sk_d = M(f"{name}_skin_d", tuple(v * 0.7 for v in skc), dents=0.0)
    blush = M(f"{name}_blush", tuple(c * k for c, k in zip(skc, (1.3, 0.8, 0.8))), rough=0.6, dents=0.0)
    sh = M(f"{name}_shirt", shirt, dents=0.3)
    col_m = M(f"{name}_collar", collar, dents=0.2) if collar else sh
    bt = M(f"{name}_bottom", bottom, dents=0.3)
    hr = M(f"{name}_hair", hair, rough=0.5, dents=0.15)
    so = M(f"{name}_shoe", shoes, rough=0.5, dents=0.2)
    sole = M("sole", (0.025, 0.018, 0.014), rough=0.6, dents=0.1)
    white = M("eye_white" if not ghost else "eye_ghost", (0.82, 0.80, 0.76) if not ghost else (0.004, 0.003, 0.003),
              rough=0.3, dents=0.0)
    iris = M("iris", (0.09, 0.04, 0.018), rough=0.25, dents=0.0)
    pupil = M("pupil", (0.008, 0.006, 0.005), rough=0.2, dents=0.0)
    shine = M("shine", (1, 1, 1), rough=0.1, dents=0.0, emit=(1, 1, 1), emit_str=2.0)
    lip = M(f"{name}_lip", tuple(c * k for c, k in zip(skc, (0.5, 0.3, 0.42))), rough=0.5, dents=0.0)
    inside = M("mouth_in", (0.03, 0.004, 0.006), rough=0.5, dents=0.0)
    tooth = M("tooth", (0.8, 0.78, 0.7), rough=0.3, dents=0.0)
    tongue = M("tongue", (0.45, 0.10, 0.10), rough=0.4, dents=0.0)
    tear = M("tear", (0.55, 0.75, 0.95), rough=0.08, dents=0.0)
    B = lambda n, c, r, m, **k: blob(n, c, r, m, lumps=False, **k)

    arm = make_rig(name)
    rigid = []

    def R(o, bone):
        rigid.append((o, bone))
        return o

    # ================= shirt: torso + sleeves + cuffs + collar + placket fused, deforming
    bw = build
    V = [(0, 0, 0.40), (0, -0.004 * (bw - 1) * 10, 0.50), (0, -0.003, 0.58), (0, 0, 0.628),
         (0.125, 0, 0.612), (-0.125, 0, 0.612), (0.185, 0.005, 0.50), (-0.185, 0.005, 0.50),
         (0.20, -0.01, 0.395), (-0.20, -0.01, 0.395)]
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (4, 6), (5, 7), (6, 8), (7, 9)]
    sw = 1.06 if gender == "m" else 1.0
    Rr = [(0.125 * bw, 0.10 * bw), (0.138 * bw, 0.108 * bw ** 1.3), (0.132 * sw, 0.102), (0.085 * sw, 0.07),
          (0.054, 0.054), (0.054, 0.054), (0.048, 0.048), (0.048, 0.048), (0.046, 0.046), (0.046, 0.046)]
    base = skin_mesh(f"{name}_shirtbase", V, E, Rr, sh)
    extra = []
    for s in (1, -1):
        a, b = Vector(BONES["forearm.L" if s > 0 else "forearm.R"][0]), Vector(BONES["forearm.L" if s > 0 else "forearm.R"][1])
        extra.append(torus(f"cuff{s}", b + (a - b).normalized() * 0.012, a - b, 0.047, 0.014, sh))
    pl = [hit(base, 0, z)[0] + Vector((0, -0.003, 0)) for z in (0.62, 0.56, 0.50, 0.44)]
    extra.append(curve("placket", pl, 0.013, sh, res=3))
    if not ghost and gender == "f" or (gender == "m" and not tie):
        p, n = hit(base, 0.075, 0.565)
        extra.append(rbox("pocket", p + Vector((0, -0.004, 0)), (0.06, 0.014, 0.062), sh, bev=0.3, rot=(0, 0, -16)))
    cparts = []
    for s in (1, -1):
        p, n = hit(base, 0.04 * s, 0.632)
        cparts.append(B(f"collar{s}", p + Vector((0.004 * s, -0.01, -0.004)), (0.052, 0.016, 0.034), col_m, rot=(-50, 0, 36 * s)))
    cparts.append(torus("collarband", (0, 0.004, 0.652), (0, 0.2, 1), 0.058, 0.015, col_m))
    if collar:
        shirt_o = fuse(f"{name}_shirt", [base] + extra, sh, voxel=0.0045, smooth=5, factor=0.6)
        R(fuse(f"{name}_collar", cparts, col_m, voxel=0.004, smooth=3, factor=0.5), "chest")
    else:
        shirt_o = fuse(f"{name}_shirt", [base] + extra + cparts, sh, voxel=0.0045, smooth=5, factor=0.6)
    skin_to(arm, shirt_o, ["pelvis", "chest", "upperarm.L", "upperarm.R", "forearm.L", "forearm.R"])
    if not ghost:
        btn_m = M(f"{name}_button", tuple(c * 0.55 for c in shirt), rough=0.4, dents=0.0)
        for i, z in enumerate((0.60, 0.545, 0.49)):
            if tie and i < 3:
                continue
            p, n = hit(shirt_o, 0, z)
            R(B(f"{name}_btn{i}", p + n * 0.003, (0.014, 0.008, 0.014), btn_m), "chest")
    if tie:
        tm = M(f"{name}_tie", tie, dents=0.2)
        tp = [hit(shirt_o, 0, z)[0] + Vector((0, -0.012, 0)) for z in (0.625, 0.56, 0.50, 0.455)]
        o = R(curve(f"{name}_tie", tp, 0.02, tm, res=3), "chest"); taper(o, 0.55, 0.9)
        o.scale = (1, 0.6, 1)
        R(B(f"{name}_knot", hit(shirt_o, 0, 0.632)[0] + Vector((0, -0.016, 0)), (0.022, 0.014, 0.02), tm), "chest")
    if lanyard and not hijab:
        lan = M(f"{name}_lanyard", lanyard, rough=0.5, dents=0.1)
        card = M("idcard", (0.85, 0.85, 0.82), rough=0.4, dents=0.0)
        cp, cn = hit(shirt_o, -0.055, 0.50)
        lp = [Vector((0.06, 0.025, 0.665)), Vector((0.075, -0.045, 0.635)),
              hit(shirt_o, 0.03, 0.58)[0] + Vector((0, -0.008, 0)), cp + Vector((0.02, -0.01, 0.045)),
              cp + Vector((-0.01, -0.01, 0.045)), hit(shirt_o, -0.07, 0.59)[0] + Vector((0, -0.008, 0)),
              Vector((-0.075, -0.045, 0.635)), Vector((-0.06, 0.025, 0.665))]
        R(curve(f"{name}_lanyard", lp, 0.005, lan, res=2), "chest")
        R(rbox(f"{name}_card", cp + Vector((0.005, -0.012, 0)), (0.05, 0.008, 0.07), card, bev=0.2, rot=(0, 6, 0)), "chest")
        R(rbox(f"{name}_cardtop", cp + Vector((0.005, -0.016, 0.022)), (0.05, 0.004, 0.016), lan, bev=0.3, rot=(0, 6, 0)), "chest")

    # ================= skirt / trousers
    if skirt:
        z0, r0 = (0.085, 0.175) if long_skirt else (0.25, 0.195)
        sk_o = clay.cone_skirt("skirtcone", z0, 0.455, r0, 0.128 * bw, bt, ry=0.82)
        hem = torus("hem", (0, 0, z0 + 0.005), UP, r0 - 0.005, 0.014, bt); hem.scale = (1, 0.82, 1)
        wb = torus("waist", (0, 0, 0.45), UP, 0.126 * bw, 0.016, bt); wb.scale = (1, 0.82, 1)
        fill = B("skirtfill", (0, 0, 0.37), (0.12, 0.095, 0.09), bt)
        R(fuse(f"{name}_skirt", [sk_o, hem, wb, fill], bt, voxel=0.005, smooth=4, factor=0.5), "pelvis")
    else:
        belt = M(f"{name}_belt", (0.02, 0.015, 0.012), dents=0.1)
        R(fuse(f"{name}_hips", [B("hips", (0, 0, 0.405), (0.128 * bw, 0.102 * bw, 0.07), bt)], bt, voxel=0.005, smooth=3), "pelvis")
        o = R(torus(f"{name}_belt", (0, 0, 0.452), UP, 0.124 * bw, 0.013, belt), "pelvis"); o.scale = (1, 0.8, 1)
        for s, lr in ((1, "L"), (-1, "R")):
            R(fuse(f"{name}_trouser{lr}", [limb("tl", (0.068 * s, 0, 0.40), (0.072 * s, 0, 0.11), 0.062, bt),
                                           torus("tc", (0.072 * s, 0, 0.09), UP, 0.058, 0.013, bt)], bt, smooth=3), f"leg.{lr}")
    # ================= legs + shoes
    for s, lr in ((1, "L"), (-1, "R")):
        R(limb(f"{name}_leg{lr}", (0.07 * s, 0, 0.30), (0.072 * s, 0, 0.07), 0.04, sk), f"leg.{lr}")
        if ghost:
            continue
        sp = [B("toe", (0.075 * s, -0.07, 0.048), (0.062, 0.07, 0.044), so), B("heel", (0.073 * s, 0.015, 0.052), (0.055, 0.06, 0.048), so),
              torus("rim", (0.073 * s, 0.012, 0.088), UP, 0.04, 0.012, so)]
        R(fuse(f"{name}_shoe{lr}", sp, so, voxel=0.004, smooth=5), f"leg.{lr}")
        R(rbox(f"{name}_sole{lr}", (0.075 * s, -0.035, 0.012), (0.122, 0.225, 0.026), sole, bev=0.45), f"leg.{lr}")

    # ================= hands
    for s, lr in ((1, "L"), (-1, "R")):
        w = Vector(BONES[f"hand.{lr}"][0])
        d = Vector((0.02 * s, -0.08, -1)).normalized()
        palm = w + d * 0.042
        ps = [B("palm", palm, (0.04, 0.026, 0.045), sk), limb("wr", w + d * -0.01, palm, 0.026, sk)]
        for k, off in enumerate((-0.027, -0.009, 0.009, 0.026)):
            kn = palm + d * 0.03 + Vector((off, 0, 0))
            tip = kn + d * (0.036 - abs(off) * 0.35) + Vector((0, -0.008, 0))
            ps.append(limb(f"f{k}", kn, tip, 0.0125, sk))
        tb = palm + Vector((-0.036 * s, -0.012, 0.012))
        ps.append(limb("th", tb, tb + Vector((-0.012 * s, -0.022, -0.03)), 0.0145, sk))
        R(fuse(f"{name}_hand{lr}", ps, sk, voxel=0.003, smooth=4, factor=0.6), f"hand.{lr}")

    # ================= head
    HC = Vector((0, 0, 0.835))
    jw = 1.08 if gender == "m" else 1.0
    hp = [B("skull", HC, (0.165, 0.158, 0.168), sk, seg=64),
          B("jaw", (0, -0.02, 0.745), (0.125 * jw, 0.115, 0.085), sk),
          B("nose", (0, -0.168, 0.805), (0.034 * nose, 0.036 * nose, 0.036 * nose), sk),
          limb("neck", (0, 0.012, 0.62), (0, 0.012, 0.72), 0.05, sk)]
    for s in (1, -1):
        hp.append(B(f"cheek{s}", (0.082 * s, -0.095, 0.77), (0.062, 0.058, 0.055), sk))
        if not hijab:
            hp.append(B(f"ear{s}", (0.165 * s, 0.005, 0.82), (0.026, 0.03, 0.046), sk, rot=(0, 0, -20 * s)))
    head = fuse(f"{name}_head", hp, sk, voxel=0.0045, smooth=10, factor=0.7)
    R(head, "head")
    eyes = {}
    for s, lr in ((1, "L"), (-1, "R")):
        p, n = hit(head, 0.066 * s, 0.86)
        c = p + Vector((0, 0.024, 0))
        eyes[s] = c
        R(B(f"{name}_eye{lr}", c, (0.043,) * 3, white, seg=40), "head")
        if not hijab:
            R(B(f"{name}_earin{lr}", (0.181 * s, -0.004, 0.82), (0.008, 0.016, 0.026), sk_d), "head")
        if gender == "f" and not ghost:
            p, n = hit(head, 0.108 * s, 0.782)
            R(B(f"{name}_blush{lr}", p + Vector((0, 0.004, 0)), (0.03, 0.01, 0.02), blush), "head")
    if glasses:
        gm = M("glasses", (0.015, 0.012, 0.01), rough=0.3, dents=0.0)
        for s in (1, -1):
            c = eyes[s]
            R(torus(f"{name}_glass{s}", c + Vector((0, -0.05, -0.004)), (0, -1, 0), 0.05, 0.006, gm), "head")
            R(limb(f"{name}_temple{s}", c + Vector((0.05 * s, -0.045, 0)), (0.172 * s, 0.0, 0.835), 0.005, gm), "head")
        R(limb(f"{name}_bridge", eyes[1] + Vector((-0.05, -0.052, 0.004)), eyes[-1] + Vector((0.05, -0.052, 0.004)), 0.005, gm), "head")
    if mustache:
        mp = [hit(head, x, 0.772 + dz)[0] + Vector((0, -0.006, 0)) for x, dz in ((-0.05, -0.012), (-0.022, 0.0), (0.022, 0.0), (0.05, -0.012))]
        o = R(curve(f"{name}_mustache", mp, 0.012, hr, res=3), "head"); taper(o, 0.5, 0.5)

    # ---- swappable face sets
    def X(o, e):
        o.name = f"{name}__{e}__{o.name}"
        return R(o, "head")

    for e in (exprs or [k for k in EXPR if k != "hantu"]) if not ghost else ["hantu"]:
        sp = EXPR[e]
        for s, lr in ((1, "L"), (-1, "R")):
            c = eyes[s]
            look = Vector((-0.10 * s, -1, -0.04)).normalized()
            k = sp["iris"]
            if k > 0 and sp["lid"] != "closed":
                X(B(f"iris{lr}", c + look * 0.030, (0.0225 * k,) * 3, iris, seg=32), e)
                X(B(f"pupil{lr}", c + look * (0.030 + 0.0118 * k), (0.0118 * k,) * 3, pupil, seg=24), e)
                X(B(f"shine{lr}", c + look * 0.0445 + Vector((0.008, 0, 0.009)) * k, (0.0042,) * 3, shine, seg=16), e)
            if sp["lid"] == "closed":
                X(B(f"lid{lr}", c + Vector((0, -0.002, 0)), (0.0465,) * 3, sk, seg=40), e)
                arc = [c + Vector((x * s, -math.sqrt(0.0465 ** 2 - x * x - 0.006 ** 2) - 0.002, -0.006 + 0.004 * (abs(x) / 0.034) ** 2))
                       for x in (-0.034, -0.017, 0, 0.017, 0.034)]
                X(curve(f"lash{lr}", arc, 0.003, pupil, res=2), e)
            elif sp["lid"] is not None:
                lid = B(f"lid{lr}", c, (0.0465,) * 3, sk, seg=48)
                cut = Vector((sp["tilt"] * s, -0.22, 1)).normalized()
                bm = bmesh.new(); bm.from_mesh(lid.data)
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co - c).dot(cut) < sp["lid"]], context="VERTS")
                bm.to_mesh(lid.data); bm.free()
                t = lid.modifiers.new("t", "SOLIDIFY"); t.thickness = 0.005
                bake(lid)
                X(lid, e)
            if sp["brow"] is not None:
                di, do = sp["brow"]
                pts = []
                for x, z in ((0.028, 0.916 + di), (0.068, 0.926 + (di + do) * 0.5), (0.108, 0.914 + do)):
                    p, n = hit(head, x * s, z)
                    pts.append(p + n * 0.004)
                o = X(curve(f"brow{lr}", pts, 0.008 if gender == "f" else 0.0105, hr, res=3), e)
                taper(o, 0.75, 0.45)
            if sp.get("tears"):
                t0 = c + Vector((0.012 * s, -0.04, -0.03))
                p1 = hit(head, t0.x, 0.80)[0]; p2 = hit(head, t0.x + 0.006 * s, 0.765)[0]
                X(limb(f"tear{lr}", p1 + Vector((0, -0.003, 0)), p2 + Vector((0, -0.003, 0)), 0.006, tear), e)
                X(B(f"drop{lr}", p2 + Vector((0, -0.005, -0.008)), (0.0095, 0.008, 0.012), tear), e)
        m = sp["mouth"]
        if m in ("flat", "frown", "smile"):
            dz = {"flat": -0.0015, "frown": -0.007, "smile": 0.008}[m]
            mp = []
            for x, f in ((-0.034, 1), (-0.017, 0.15), (0, 0), (0.017, 0.15), (0.034, 1)):
                p, n = hit(head, x, 0.742 + dz * f - (0.003 if m == "smile" else 0))
                mp.append(p + n * 0.001)
            X(curve("mouth", mp, 0.0055, lip, res=3), e)
        else:
            w, h, cz = {"o": (0.017, 0.02, 0.738), "scream": (0.032, 0.042, 0.728), "shout": (0.04, 0.026, 0.736),
                        "wail": (0.034, 0.02, 0.736)}[m]
            p, n = hit(head, 0, cz)
            X(B("mouth", p + Vector((0, 0.008, 0)), (w, 0.014, h), inside, seg=40), e)
            ring = [p + Vector((w * math.cos(t), -0.001 + 0.004 * abs(math.cos(t)), h * math.sin(t)))
                    for t in [i / 14 * 2 * math.pi for i in range(14)]]
            X(curve("lips", ring, 0.0045, lip, closed=True, res=2), e)
            if m in ("shout", "scream", "wail"):
                X(rbox("teeth", p + Vector((0, -0.002, h * 0.62)), (w * 1.3, 0.008, h * 0.42), tooth, bev=0.3), e)
            if m in ("scream", "wail"):
                X(B("tongue", p + Vector((0, 0.0, -h * 0.55)), (w * 0.6, 0.008, h * 0.4), tongue), e)

    # ================= hair / hijab
    H = Head(HC, (0.167, 0.160, 0.170))
    hl = lambda th: 44 - 40 * min(1.0, abs(th) / 100.0) ** 1.1

    def cap_shell(mult, low, thick=0.014, keep=None):
        cap = B("cap", HC, tuple(H.r * mult), hr, seg=72)
        bm = bmesh.new(); bm.from_mesh(cap.data)
        kill = []
        for v in bm.verts:
            d = v.co - HC
            th = math.degrees(math.atan2(d.x, -d.y)); el = math.degrees(math.asin(max(-1, min(1, d.z / d.length))))
            if (abs(th) < 100 and el < hl(th) - 2) or el < low or (keep and not keep(th, el)):
                kill.append(v)
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(cap.data); bm.free()
        t = cap.modifiers.new("t", "SOLIDIFY"); t.thickness = thick; t.offset = 1.0
        return cap

    def sweep(k0, n, t_from, t_to, el_top, el_end, r=0.022, off=0.022):
        out = []
        for k in range(n):
            t0 = t_from + k * 3
            pts = []
            for i in range(7):
                u = i / 6
                th = t0 + (t_to - t0) * u ** 0.9
                el = (el_top - 2.5 * k) + (el_end - (el_top - 2.5 * k)) * u ** 1.4
                pts.append(H.at(th, el, off + 0.014 * math.sin(math.pi * u))[0])
            o = curve(f"fr{k0}{k}", pts, r, hr, res=3); taper(o, 0.6, 0.7)
            out.append(o)
        return out

    hparts = []
    if hijab:
        hj = M(f"{name}_hijab", hijab, dents=0.3)
        shell = B("hj", HC + Vector((0, 0.008, 0.004)), tuple(H.r * 1.085), hj, seg=72)
        bm = bmesh.new(); bm.from_mesh(shell.data)
        kill = []
        for v in bm.verts:
            d = v.co - HC
            th = math.degrees(math.atan2(d.x, -d.y)); el = math.degrees(math.asin(max(-1, min(1, d.z / d.length))))
            if (th / 50) ** 2 + ((el + 6) / 40) ** 2 < 1 and d.y < 0:
                kill.append(v)
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(shell.data); bm.free()
        t = shell.modifiers.new("t", "SOLIDIFY"); t.thickness = 0.016
        drape = B("drape", (0, 0.0, 0.612), (0.165, 0.135, 0.078), hj)
        chin = torus("chinwrap", (0, -0.02, 0.70), (0, -0.25, 1), 0.105, 0.03, hj)
        fold = [H.at(th, 46 - abs(th) * 0.12, 0.03)[0] for th in (-70, -35, 0, 35, 70)]
        R(fuse(f"{name}_hijab", [shell, drape, chin, curve("fold", fold, 0.016, hj, res=3)], hj, voxel=0.0045, smooth=4, factor=0.6), "head")
    elif hair_style in ("bun", "long", "bob"):
        hparts.append(cap_shell(1.03, -30))
        if hair_style == "bun":
            bun_dir = Vector((0, 1, -0.05)).normalized()
            bun_c = H.pt(bun_dir, 0.05)[0]
            for k in range(-12, 13):
                th = k * 8.2
                d0 = H.dir(th, hl(th) + 1)
                dm = (d0 + bun_dir + Vector((0, 0, 1.0 if abs(th) < 60 else 0.3))).normalized()
                pts = []
                for i in range(8):
                    u = i / 7
                    d = ((1 - u) ** 2) * d0 + 2 * u * (1 - u) * dm + (u ** 2) * bun_dir
                    pts.append(H.pt(d, 0.014 + 0.012 * math.sin(math.pi * u))[0])
                o = curve(f"strand{k}", pts, 0.021, hr, res=3); taper(o, 0.8, 0.6)
                hparts.append(o)
            hparts.append(B("bun", bun_c, (0.07, 0.06, 0.066), hr))
            ax_u = Vector((1, 0, 0)); ax_v = bun_dir.cross(ax_u).normalized()
            spr = []
            for i in range(28):
                a = i / 27 * 4 * math.pi; r = 0.064 * (1 - i / 36)
                spr.append(bun_c + bun_dir * (0.04 - 0.035 * i / 27) + ax_u * math.cos(a) * r + ax_v * math.sin(a) * r)
            hparts.append(curve("swirl", spr, 0.016, hr, res=3))
            hparts += sweep("a", 5, -22, 80, 52, 10)
        else:
            z_end = 0.60 if hair_style == "long" else 0.70
            for sgn in (1, -1):          # curtains falling from a centre part down the sides and back
                for j in range(10):
                    th = 62 + j * 13.2
                    pts = [H.at(sgn * 10, 84, 0.02)[0], H.at(sgn * th, 58, 0.026)[0], H.at(sgn * th, 28, 0.028)[0],
                           H.at(sgn * th, 0, 0.028)[0], H.at(sgn * th, -24, 0.026)[0]]
                    last = pts[-1]
                    pts.append(Vector((last.x, last.y, (last.z + z_end) / 2)))
                    pts.append(Vector((last.x * 0.97, last.y * 0.97, z_end)))
                    o = curve(f"lock{sgn}{j}", pts, 0.024, hr, res=3); taper(o, 0.7, 0.55)
                    hparts.append(o)
            if ghost:
                for k, th in enumerate((-30, -14, 4, 20, 36)):   # wet strands over the face
                    pts = [H.at(th, 70, 0.02)[0], H.at(th, 40, 0.024)[0], H.at(th * 1.05, 5, 0.03)[0],
                           H.at(th * 1.1, -30, 0.03)[0], H.at(th * 1.1, -30, 0.03)[0] + Vector((0, -0.005, -0.10 - 0.02 * (k % 2)))]
                    o = curve(f"wet{k}", pts, 0.013, hr, res=3); taper(o, 0.9, 0.4)
                    hparts.append(o)
            else:
                hparts += sweep("a", 5, -18, 84, 52, 6)
                hparts += [o for o in sweep("b", 3, 14, -80, 50, 14, r=0.02)]
    elif hair_style == "short":
        hparts.append(cap_shell(1.03, -8))
        hparts += sweep("a", 7, -34, 78, 60, 26, r=0.024, off=0.024)
        hparts += sweep("b", 3, -40, -84, 50, 22, r=0.02)
        for k in range(-4, 5):   # back volume
            pts = [H.at(k * 16, 82, 0.02)[0], H.at(180 - k * 14, 45, 0.026)[0], H.at(180 - k * 14, 5, 0.022)[0]]
            o = curve(f"bk{k}", pts, 0.024, hr, res=3); taper(o, 0.7, 0.6)
            hparts.append(o)
    elif hair_style == "crew":
        hparts.append(cap_shell(1.022, -6, thick=0.012))
        hparts += sweep("a", 5, -30, 60, 56, 40, r=0.016, off=0.016)
    elif hair_style == "balding":
        hparts.append(cap_shell(1.025, -6, thick=0.012, keep=lambda th, el: el < 30 and abs(th) > 62))
    if hparts:
        R(fuse(f"{name}_hair", hparts, hr, voxel=0.0035, smooth=2, factor=0.5), "head")
    if cap:
        cm = M(f"{name}_cap", cap, dents=0.25)
        dome = B("dome", HC + Vector((0, 0.005, 0.075)), (0.178, 0.172, 0.115), cm)
        visor = rbox("visor", HC + Vector((0, -0.185, 0.075)), (0.22, 0.17, 0.02), cm, bev=0.45, rot=(-10, 0, 0))
        band = torus("band", HC + Vector((0, 0.004, 0.068)), UP, 0.168, 0.012, cm)
        R(fuse(f"{name}_cap", [dome, visor, band], cm, voxel=0.0045, smooth=4, factor=0.5), "head")
    if ghost:
        blood = M("blood", (0.16, 0.004, 0.004), rough=0.25, dents=0.0)
        black = M("blackblood", (0.004, 0.002, 0.002), rough=0.2, dents=0.0)
        crack = [H.at(th, el, 0.004)[0] for th, el in ((-28, 62), (-20, 50), (-26, 40), (-14, 30), (-18, 20))]
        R(curve(f"{name}_crack", crack, 0.006, black, res=2), "head")
        for i, (x, z0, z1) in enumerate(((-0.05, 0.93, 0.80), (-0.075, 0.90, 0.74), (0.02, 0.80, 0.70), (-0.02, 0.92, 0.86))):
            pts = [hit(head, x + 0.004 * math.sin(j), z0 + (z1 - z0) * j / 4)[0] + Vector((0, -0.004, 0)) for j in range(5)]
            o = R(curve(f"{name}_drip{i}", pts, 0.007, black if i % 2 == 0 else blood, res=2), "head"); taper(o, 1.0, 0.4)
        import random
        rnd = random.Random(4)
        for i, (x, z, r) in enumerate(((0.035, 0.57, 0.035), (-0.06, 0.50, 0.03), (0.06, 0.37, 0.04), (-0.03, 0.27, 0.045))):
            on_shirt = z > 0.46
            flat = lambda xx, zz: Vector((xx, -0.105 - (0.455 - zz) * 0.19, zz))
            surf = (lambda xx, zz: hit(shirt_o, xx, zz)[0] or flat(xx, zz)) if on_shirt else flat
            for j in range(5):      # irregular splatter: overlapping small blobs
                xx, zz = x + rnd.uniform(-r, r) * 0.8, z + rnd.uniform(-r, r) * 0.8
                rr = r * rnd.uniform(0.35, 0.7)
                R(B(f"{name}_stain{i}{j}", surf(xx, zz) + Vector((0, 0.008, 0)), (rr, 0.012, rr * rnd.uniform(0.9, 1.5)), blood if j else black), "chest" if on_shirt else "pelvis")
            pts = [surf(x, z - r * 0.3 - k * 0.035) + Vector((0, -0.003, 0)) for k in range(4)]
            o = R(curve(f"{name}_run{i}", pts, 0.008, blood, res=2), "chest" if on_shirt else "pelvis"); taper(o, 1.0, 0.35)
    for o, bone in rigid:
        bind(arm, o, bone)
    arm.scale = (scale,) * 3
    arm.location = loc
    arm.rotation_euler.z = rot_z
    bpy.context.view_layer.update()
    set_expr(arm, "hantu" if ghost else expr)
    pose(arm, "idle")
    return arm


# ------------------------------------------------------------------ poses
def pose(arm, name):
    clay.rest(arm)
    P = lambda v: arm.matrix_world @ Vector(v)
    pb = clay.point_bone
    if name == "nervous":      # hunched, hands clasped at the chest
        pb(arm, "chest", P((0, -0.03, 0.64)))
        pb(arm, "head", P((0.04, -0.07, 1.0)))
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.17 * s, -0.07, 0.50)))
            pb(arm, f"forearm.{lr}", P((0.03 * s, -0.16, 0.56)))
            pb(arm, f"hand.{lr}", P((0.0, -0.18, 0.63)))
    elif name == "scared":     # leaning back, hands up beside the face
        pb(arm, "chest", P((0, 0.04, 0.64)))
        pb(arm, "head", P((0, 0.05, 1.0)))
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.22 * s, -0.06, 0.56)))
            pb(arm, f"forearm.{lr}", P((0.17 * s, -0.14, 0.70)))
            pb(arm, f"hand.{lr}", P((0.15 * s, -0.15, 0.80)))
    elif name == "phone":      # right hand holds a phone to the ear
        pb(arm, "head", P((-0.03, -0.02, 1.0)))
        pb(arm, "upperarm.R", P((-0.21, -0.05, 0.53)))
        pb(arm, "forearm.R", P((-0.19, -0.08, 0.72)))
        pb(arm, "hand.R", P((-0.17, -0.06, 0.80)))
    elif name == "knock":      # right fist raised to a door
        pb(arm, "upperarm.R", P((-0.17, -0.14, 0.62)))
        pb(arm, "forearm.R", P((-0.15, -0.22, 0.74)))
        pb(arm, "hand.R", P((-0.15, -0.30, 0.78)))
    elif name == "point":
        pb(arm, "upperarm.L", P((0.19, -0.14, 0.60)))
        pb(arm, "forearm.L", P((0.21, -0.28, 0.62)))
        pb(arm, "hand.L", P((0.22, -0.38, 0.63)))
    elif name == "cower":      # bent forward, arms over the head
        pb(arm, "pelvis", P((0, -0.03, 0.46)))
        pb(arm, "chest", P((0, -0.10, 0.62)))
        pb(arm, "head", P((0, -0.22, 0.92)))
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.17 * s, -0.16, 0.66)))
            pb(arm, f"forearm.{lr}", P((0.12 * s, -0.20, 0.80)))
            pb(arm, f"hand.{lr}", P((0.06 * s, -0.20, 0.88)))
    elif name == "walk":
        pb(arm, "leg.L", P((0.07, -0.10, 0.06)))
        pb(arm, "leg.R", P((-0.07, 0.10, 0.07)))
        pb(arm, "upperarm.L", P((0.18, 0.06, 0.50)))
        pb(arm, "upperarm.R", P((-0.18, -0.06, 0.50)))
    arm["pose"] = name
    return arm


def lie_down(arm, loc, rot_z=0.0):
    """sleeping on the floor: on the back, head toward +Y after rot"""
    arm.rotation_euler = (math.radians(-90), 0, rot_z)
    arm.location = loc
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ cast
CAST = {
    "sari":   dict(gender="f", skin="sawo", hair_style="bun", shirt=(0.60, 0.69, 0.80), bottom=(0.04, 0.05, 0.12),
                   lanyard=(0.05, 0.14, 0.5), scale=1.45),
    "nadia":  dict(gender="f", skin="kuning", hair_style="long", hair=(0.06, 0.025, 0.012), shirt=(0.36, 0.03, 0.05),
                   bottom=(0.012, 0.012, 0.014), shoes=(0.30, 0.02, 0.03), lanyard=None, scale=1.50, expr="netral"),
    "wulan":  dict(gender="f", skin="sawo", hijab=(0.55, 0.30, 0.32), shirt=(0.62, 0.55, 0.42), bottom=(0.05, 0.11, 0.08),
                   long_skirt=True, lanyard=None, scale=1.40, expr="senyum"),
    "hendra": dict(gender="m", skin="sawo", hair_style="balding", hair=(0.16, 0.15, 0.14), shirt=(0.07, 0.10, 0.22),
                   bottom=(0.015, 0.015, 0.018), shoes=(0.02, 0.015, 0.012), tie=(0.35, 0.04, 0.04), glasses=True, mustache=True, build=1.28,
                   nose=1.15, lanyard=None, scale=1.52, expr="netral"),
    "bagas":  dict(gender="m", skin="kuning", hair_style="short", shirt=(0.16, 0.30, 0.20), bottom=(0.10, 0.10, 0.11),
                   shoes=(0.03, 0.02, 0.015), glasses=True, lanyard=(0.4, 0.05, 0.05), scale=1.50, expr="cemas"),
    "reza":   dict(gender="m", skin="gelap", hair_style="crew", shirt=(0.70, 0.22, 0.03), collar=(0.02, 0.02, 0.025),
                   bottom=(0.03, 0.04, 0.07), shoes=(0.6, 0.6, 0.58), cap=(0.02, 0.02, 0.025), lanyard=None,
                   scale=1.53, expr="netral"),
    "fajar":  dict(gender="m", skin="sawo", hair_style="crew", shirt=(0.04, 0.28, 0.30), collar=(0.75, 0.75, 0.7),
                   bottom=(0.02, 0.025, 0.035), shoes=(0.03, 0.03, 0.03), build=0.92, lanyard=None, scale=1.38,
                   expr="senyum"),
    "penghuni": dict(gender="m", skin="gelap", hair_style="balding", hair=(0.5, 0.5, 0.48), shirt=(0.72, 0.70, 0.64),
                     bottom=(0.20, 0.07, 0.05), skirt=True, long_skirt=True, mustache=True, build=1.1, lanyard=None,
                     shoes=(0.25, 0.12, 0.05), scale=1.42, expr="capek"),
    "hantu":  dict(gender="f", skin="hantu", hair_style="long", hair=(0.004, 0.004, 0.005), shirt=(0.55, 0.55, 0.52),
                   bottom=(0.55, 0.55, 0.52), long_skirt=True, lanyard=None, ghost=True, scale=1.6),
}


def make(name, **over):
    kw = dict(CAST[name]); kw.update(over)
    return person(name, **kw)
