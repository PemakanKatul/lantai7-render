"""Sculpted clay-figurine characters (stop-motion puppet look, smooth plasticine).
Body/clothes are skin-modifier meshes with smooth armature weights; face details and
accessories are rigid parts on the head/chest bones. Faces -Y, feet at z=0.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
import clay
from clay import blob, bind

UP = Vector((0, 0, 1))


def M(name, color, rough=0.62, sss=0.0, dents=0.22, grooves=0.0, emit=None, emit_str=0.0):
    return clay.clay_mat(name, color, rough=rough, sss=sss, dents=dents, grooves=grooves,
                         emit=emit, emit_str=emit_str)


# ------------------------------------------------------------------ mesh helpers
def skin_mesh(name, verts, edges, radii, m, sub=2):
    """skin-modifier tube network, baked to a real smooth mesh"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], edges, [])
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    sk = o.modifiers.new("skin", "SKIN")
    sk.branch_smoothing = 0.6
    for i, r in enumerate(radii):
        r = r if isinstance(r, (tuple, list)) else (r, r)
        me.skin_vertices[0].data[i].radius = r
    me.skin_vertices[0].data[0].use_root = True
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = sub; sd.render_levels = sub
    bake(o)
    o.data.materials.append(m)
    return o


def bake(o):
    dg = bpy.context.evaluated_depsgraph_get()
    nm = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    old = o.data
    o.modifiers.clear()
    o.data = nm
    bpy.data.meshes.remove(old)
    for p in o.data.polygons:
        p.use_smooth = True


def curve(name, pts, bevel, m, closed=False, res=4):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    cu.materials.append(m)
    return o


def taper(o, start=0.5, end=1.0):
    """thin the ends of a bevelled curve (clay worms are fatter in the middle)"""
    for bp in o.data.splines[0].bezier_points:
        bp.radius = 1.0
    pts = o.data.splines[0].bezier_points
    pts[0].radius = start
    pts[-1].radius = end


def torus(name, center, axis, R, r, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=40, minor_segments=14,
                                     location=center)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = UP.rotation_difference(Vector(axis).normalized())
    bpy.ops.object.transform_apply(rotation=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o


def rbox(name, center, size, m, bev=0.4, rot=(0, 0, 0)):
    """rounded slab (pockets, ID card, soles)"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=[math.radians(a) for a in rot])
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    b = o.modifiers.new("bev", "BEVEL"); b.width = min(size) * bev; b.segments = 4
    s = o.modifiers.new("sub", "SUBSURF"); s.levels = 1; s.render_levels = 2
    bake(o)
    o.data.materials.append(m)
    return o


def surface_hit(o, origin, direction):
    ok, loc, nrm, _ = o.ray_cast(Vector(origin), Vector(direction).normalized())
    return (loc, nrm) if ok else (None, None)


# ------------------------------------------------------------------ rig + weights
BONES = {
    "pelvis": ((0, 0, 0.66), (0, 0, 0.80), None),
    "chest": ((0, 0, 0.80), (0, 0, 1.10), "pelvis"),
    "neck": ((0, 0, 1.10), (0, 0, 1.20), "chest"),
    "head": ((0, 0, 1.20), (0, 0, 1.58), "neck"),
    "upperarm.L": ((0.165, 0, 1.065), (0.215, 0.01, 0.86), "chest"),
    "forearm.L": ((0.215, 0.01, 0.86), (0.232, -0.005, 0.69), "upperarm.L"),
    "hand.L": ((0.232, -0.005, 0.69), (0.234, -0.01, 0.58), "forearm.L"),
    "upperarm.R": ((-0.165, 0, 1.065), (-0.215, 0.01, 0.86), "chest"),
    "forearm.R": ((-0.215, 0.01, 0.86), (-0.232, -0.005, 0.69), "upperarm.R"),
    "hand.R": ((-0.232, -0.005, 0.69), (-0.234, -0.01, 0.58), "forearm.R"),
    "thigh.L": ((0.085, 0, 0.70), (0.085, -0.008, 0.40), "pelvis"),
    "shin.L": ((0.085, -0.008, 0.40), (0.08, 0, 0.09), "thigh.L"),
    "thigh.R": ((-0.085, 0, 0.70), (-0.085, -0.008, 0.40), "pelvis"),
    "shin.R": ((-0.085, -0.008, 0.40), (-0.08, 0, 0.09), "thigh.R"),
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
            e.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.hide_render = True
    return arm


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def skin_to(arm, o, bones, power=6.0):
    """smooth envelope weights from distance to bone segments (top-2 blend)"""
    segs = {b: (Vector(BONES[b][0]), Vector(BONES[b][1])) for b in bones}
    groups = {b: o.vertex_groups.new(name=b) for b in bones}
    for v in o.data.vertices:
        ds = sorted(((_seg_dist(v.co, *segs[b]), b) for b in bones))[:2]
        ws = [1.0 / (d + 1e-3) ** power for d, _ in ds]
        s = sum(ws)
        for (d, b), w in zip(ds, ws):
            groups[b].add([v.index], w / s, "REPLACE")
    md = o.modifiers.new("arm", "ARMATURE")
    md.object = arm
    o.parent = arm
    o.matrix_parent_inverse = arm.matrix_world.inverted()


# ------------------------------------------------------------------ head geometry
class Head:
    def __init__(self, c, r):
        self.c, self.r = Vector(c), Vector(r)

    def dir(self, theta, el):
        """theta: degrees around Z from the front (+ = character's left, +X); el: elevation"""
        t, e = math.radians(theta), math.radians(el)
        return Vector((math.sin(t) * math.cos(e), -math.cos(t) * math.cos(e), math.sin(e)))

    def pt(self, d, off=0.0):
        d = Vector(d).normalized()
        s = 1.0 / math.sqrt((d.x / self.r.x) ** 2 + (d.y / self.r.y) ** 2 + (d.z / self.r.z) ** 2)
        n = Vector((d.x / self.r.x ** 2, d.y / self.r.y ** 2, d.z / self.r.z ** 2)).normalized()
        return self.c + d * s + n * off, n

    def at(self, theta, el, off=0.0):
        return self.pt(self.dir(theta, el), off)


def hairline_el(theta):
    a = min(1.0, abs(theta) / 100.0)
    return 47 - 41 * a ** 1.1


# ------------------------------------------------------------------ character
SKIN = {"sawo": (0.33, 0.165, 0.085), "kuning": (0.55, 0.32, 0.18), "gelap": (0.25, 0.115, 0.06)}


def person(name="sari", skin="sawo", shirt=(0.66, 0.72, 0.80), bottom=(0.035, 0.045, 0.10),
           hair=(0.022, 0.012, 0.008), shoes=(0.05, 0.025, 0.015), lanyard=(0.05, 0.12, 0.45),
           skirt=True, hair_style="bun", loc=(0, 0, 0), rot_z=0.0):
    sk = M(f"{name}_skin", SKIN[skin], rough=0.55, sss=0.2, dents=0.12)
    sk_dark = M(f"{name}_skin_d", tuple(c * 0.7 for c in SKIN[skin]), rough=0.6, sss=0.1, dents=0.1)
    blush = M(f"{name}_blush", tuple(c * k for c, k in zip(SKIN[skin], (1.22, 0.86, 0.84))), rough=0.6, dents=0.0)
    sh = M(f"{name}_shirt", shirt, dents=0.25)
    sh_d = M(f"{name}_shirt_d", tuple(c * 0.86 for c in shirt), dents=0.2)
    bt = M(f"{name}_bottom", bottom, dents=0.25)
    hr = M(f"{name}_hair", hair, rough=0.5, dents=0.1, grooves=0.25)
    so = M(f"{name}_shoe", shoes, rough=0.45, dents=0.15)
    sole = M("sole", (0.02, 0.015, 0.012), rough=0.6, dents=0.05)
    white = M("eye_white", (0.80, 0.78, 0.74), rough=0.3, dents=0.0)
    iris = M("iris", (0.10, 0.045, 0.02), rough=0.25, dents=0.0)
    pupil = M("pupil", (0.008, 0.006, 0.005), rough=0.2, dents=0.0)
    shine = M("shine", (1, 1, 1), rough=0.1, dents=0.0, emit=(1, 1, 1), emit_str=2.0)
    lip = M(f"{name}_lip", (0.16, 0.045, 0.04), rough=0.5, dents=0.0)
    btn = M("button", tuple(c * 0.75 for c in shirt), rough=0.4, dents=0.0)
    lan = M("lanyard", lanyard, rough=0.5, dents=0.1)
    card = M("idcard", (0.85, 0.85, 0.82), rough=0.4, dents=0.0)

    arm = make_rig(name)
    rigid = []

    def R(o, bone):
        rigid.append((o, bone))
        return o

    # ---------------- shirt (torso + sleeves), deforming
    V = [(0, 0.0, 0.66), (0, 0, 0.80), (0, -0.005, 0.96), (0, 0.0, 1.085),
         (0.165, 0, 1.06), (-0.165, 0, 1.06), (0.215, 0.01, 0.86), (-0.215, 0.01, 0.86),
         (0.232, -0.005, 0.70), (-0.232, -0.005, 0.70)]
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (4, 6), (5, 7), (6, 8), (7, 9)]
    Rr = [(0.16, 0.12), (0.148, 0.112), (0.18, 0.13), (0.105, 0.085), (0.066, 0.066), (0.066, 0.066),
          (0.056, 0.056), (0.056, 0.056), (0.05, 0.05), (0.05, 0.05)]
    shirt_o = skin_mesh(f"{name}_shirt", V, E, Rr, sh)
    skin_to(arm, shirt_o, ["pelvis", "chest", "upperarm.L", "upperarm.R", "forearm.L", "forearm.R"])

    # ---------------- legs (deforming) + shoes
    for s, lr in ((1, "L"), (-1, "R")):
        lg = skin_mesh(f"{name}_leg{lr}", [(0.085 * s, 0, 0.72), (0.085 * s, -0.008, 0.40), (0.08 * s, 0, 0.09)],
                       [(0, 1), (1, 2)], [0.07, 0.058, 0.048], sk)
        skin_to(arm, lg, [f"thigh.{lr}", f"shin.{lr}"])
        R(blob(f"{name}_shoe{lr}", (0.08 * s, -0.04, 0.058), (0.064, 0.12, 0.052), so, lumps=False), f"shin.{lr}")
        R(rbox(f"{name}_sole{lr}", (0.08 * s, -0.04, 0.014), (0.132, 0.245, 0.03), sole, bev=0.45), f"shin.{lr}")

    # ---------------- skirt / trousers
    if skirt:
        R(clay.cone_skirt(f"{name}_skirt", 0.47, 0.83, 0.235, 0.148, bt), "pelvis")
        R(torus(f"{name}_waistband", (0, 0, 0.815), UP, 0.142, 0.016, bt), "pelvis")
        R(torus(f"{name}_hem", (0, 0, 0.475), UP, 0.226, 0.013, bt), "pelvis")
    else:
        for s, lr in ((1, "L"), (-1, "R")):
            tr = skin_mesh(f"{name}_trouser{lr}", [(0.088 * s, 0, 0.80), (0.088 * s, -0.008, 0.40), (0.082 * s, 0, 0.11)],
                           [(0, 1), (1, 2)], [0.085, 0.066, 0.06], bt)
            skin_to(arm, tr, [f"thigh.{lr}", f"shin.{lr}"])
        hips = skin_mesh(f"{name}_hips", [(0, 0, 0.84), (0, 0, 0.70)], [(0, 1)], [(0.15, 0.115), (0.16, 0.12)], bt)
        skin_to(arm, hips, ["pelvis", "thigh.L", "thigh.R"])

    # ---------------- shirt details: placket, buttons, pocket, collar, cuffs, lanyard + ID card
    def front(z, x=0.0):
        loc, n = surface_hit(shirt_o, (x, -1, z), (0, 1, 0))
        return loc, n

    for i, z in enumerate((1.035, 0.965, 0.895, 0.83)):
        p, n = front(z)
        R(blob(f"{name}_btn{i}", p + n * 0.004, (0.0155, 0.0155, 0.0155), btn, lumps=False), "chest")
    pts = [front(z)[0] + front(z)[1] * 0.002 for z in (1.07, 0.98, 0.90, 0.82)]
    R(curve(f"{name}_placket", pts, 0.012, sh_d, res=2), "chest").scale = (1, 1, 1)
    p, n = front(0.985, 0.085)
    R(rbox(f"{name}_pocket", p + n * 0.006, (0.075, 0.014, 0.08), sh_d, bev=0.35, rot=(0, 0, -14)), "chest")
    for s in (1, -1):
        p, n = front(1.085, 0.05 * s)
        R(blob(f"{name}_collar{s}", p + n * 0.012 + Vector((0, 0, -0.012)), (0.062, 0.016, 0.042), sh,
               rot=(-58, 0, 34 * s), lumps=False), "chest")
    R(torus(f"{name}_collarband", (0, 0.004, 1.115), (0, 0.25, 1), 0.066, 0.017, sh), "chest")
    for s, lr in ((1, "L"), (-1, "R")):
        a, b = Vector(BONES[f"forearm.{lr}"][0]), Vector(BONES[f"forearm.{lr}"][1])
        R(torus(f"{name}_cuff{lr}", b + (a - b).normalized() * 0.012, a - b, 0.05, 0.012, sh_d), f"forearm.{lr}")
    # lanyard + ID card
    cz = 0.90
    cp, cn = front(cz, 0.0)
    lp = [Vector((0.075, 0.03, 1.13)), Vector((0.10, -0.05, 1.07)), front(1.0, 0.055)[0] + Vector((0, -0.012, 0)),
          cp + Vector((0.012, -0.016, 0.045)), cp + Vector((-0.012, -0.016, 0.045)),
          front(1.0, -0.055)[0] + Vector((0, -0.012, 0)), Vector((-0.10, -0.05, 1.07)), Vector((-0.075, 0.03, 1.13))]
    R(curve(f"{name}_lanyard", lp, 0.0055, lan, res=2), "chest")
    R(rbox(f"{name}_card", cp + cn * 0.02, (0.058, 0.008, 0.08), card, bev=0.2), "chest")
    R(rbox(f"{name}_cardstrip", cp + cn * 0.025 + Vector((0, 0, 0.025)), (0.058, 0.004, 0.018), lan, bev=0.3), "chest")

    # ---------------- hands (rigid on hand bones): palm + 4 fingers + thumb
    for s, lr in ((1, "L"), (-1, "R")):
        w = Vector(BONES[f"hand.{lr}"][0])
        d = Vector((0, 0, -1))
        palm = w + d * 0.045
        verts = [w + d * 0.008, palm]
        edges = [(0, 1)]
        radii = [(0.03, 0.022), (0.038, 0.02)]
        for k, off in enumerate((-0.022, -0.007, 0.008, 0.022)):
            side = Vector((off * s * -1, 0, 0))
            kn = palm + d * 0.028 + side
            tip = kn + d * (0.04 - abs(off) * 0.4) + Vector((0, -0.012, 0))
            verts += [kn, tip]
            edges += [(1, len(verts) - 2), (len(verts) - 2, len(verts) - 1)]
            radii += [0.0115, 0.0105]
        tb = w + d * 0.025 + Vector((-0.028 * s, -0.018, 0))
        tt = tb + Vector((-0.012 * s, -0.022, -0.028))
        verts += [tb, tt]
        edges += [(0, len(verts) - 2), (len(verts) - 2, len(verts) - 1)]
        radii += [0.014, 0.012]
        R(skin_mesh(f"{name}_hand{lr}", verts, edges, radii, sk, sub=2), f"hand.{lr}")

    # ---------------- neck + head
    R(clay.limb(f"{name}_neck", (0, 0.01, 1.09), (0, 0.01, 1.235), 0.05, sk), "neck")
    H = Head((0, -0.005, 1.39), (0.172, 0.165, 0.176))
    head = blob(f"{name}_head", tuple(H.c), tuple(H.r), sk, seg=64, lumps=False)
    for v in head.data.vertices:   # jaw: narrower towards the chin, slight chin forward
        f = max(0.0, (H.c.z - v.co.z) / H.r.z)
        v.co.x = H.c.x + (v.co.x - H.c.x) * (1 - 0.12 * f ** 1.5)
        if v.co.y < H.c.y:
            v.co.y -= 0.006 * f ** 2
    R(head, "head")
    for s, lr in ((1, "L"), (-1, "R")):
        # eyes
        p, n = H.at(21 * s, 4, -0.014)
        R(blob(f"{name}_eye{lr}", p, (0.04, 0.04, 0.04), white, lumps=False, seg=32), "head")
        look = (n + Vector((0, -0.25, 0.05))).normalized()
        R(blob(f"{name}_iris{lr}", p + look * 0.029, (0.0235, 0.0235, 0.0235), iris, lumps=False, seg=32), "head")
        R(blob(f"{name}_pupil{lr}", p + look * 0.0405, (0.012, 0.012, 0.012), pupil, lumps=False, seg=24), "head")
        R(blob(f"{name}_shine{lr}", p + look * 0.046 + Vector((0.008, 0, 0.009)), (0.0045,) * 3, shine, lumps=False, seg=16), "head")
        # sleepy/worried upper lid: skin shell over the top of the eye, inner end raised
        lid = blob(f"{name}_lid{lr}", p, (0.0445, 0.0445, 0.0445), sk, lumps=False, seg=40)
        cut = Vector((0.18 * s * -1, -0.32, 1)).normalized()
        bm = bmesh.new(); bm.from_mesh(lid.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co - p).dot(cut) < 0.009], context="VERTS")
        bm.to_mesh(lid.data); bm.free()
        so_ = lid.modifiers.new("t", "SOLIDIFY"); so_.thickness = 0.004
        bake(lid)
        R(lid, "head")
        # lower lid rim
        lo = [H.at(21 * s + 12 * k, -3.2 + 1.5 * abs(k) ** 2, 0.006)[0] for k in (-1, -0.5, 0, 0.5, 1)]
        o = R(curve(f"{name}_lowlid{lr}", lo, 0.0035, sk_dark, res=2), "head")
        # brows: worried (inner end raised)
        bw = [H.at(s * t, e, 0.004)[0] for t, e in ((9, 22), (19, 21.5), (30, 18))]
        o = R(curve(f"{name}_brow{lr}", bw, 0.0085, hr, res=3), "head")
        taper(o, 0.7, 0.45)
        # ears with inner dent
        p, n = H.at(92 * s, 0, 0.004)
        R(blob(f"{name}_ear{lr}", p, (0.022, 0.04, 0.052), sk, lumps=False), "head")
        R(blob(f"{name}_earin{lr}", p + n * 0.012, (0.01, 0.024, 0.032), sk_dark, lumps=False), "head")
        # cheeks
        p, n = H.at(33 * s, -12, -0.002)
        R(blob(f"{name}_cheek{lr}", p, (0.034, 0.012, 0.024), blush, lumps=False), "head")
    # nose: big, round, slightly drooping
    p, n = H.at(0, -9, 0.012)
    R(blob(f"{name}_nose", p + Vector((0, 0, -0.006)), (0.032, 0.033, 0.036), sk, lumps=False), "head")
    for s in (1, -1):
        pp, _ = H.at(0, -14, 0.02)
        R(blob(f"{name}_nostril{s}", pp + Vector((0.016 * s, -0.012, 0.0)), (0.012, 0.012, 0.01), sk, lumps=False), "head")
    # mouth: small worried line + lower lip
    mpts = [H.at(t, e, 0.001)[0] for t, e in ((-16, -25.0), (-8, -23.3), (0, -23.0), (8, -23.3), (16, -25.0))]
    R(curve(f"{name}_mouth", mpts, 0.0055, lip, res=3), "head")
    p, n = H.at(0, -27.5, -0.003)
    R(blob(f"{name}_lowerlip", p, (0.03, 0.011, 0.01), sk, lumps=False), "head")

    # ---------------- hair: cap + sculpted strands pulled back to a bun
    cap = blob(f"{name}_haircap", tuple(H.c), tuple(H.r * 1.035), hr, seg=72, lumps=False)
    bm = bmesh.new(); bm.from_mesh(cap.data)
    kill = []
    for v in bm.verts:
        d = (v.co - H.c)
        th = math.degrees(math.atan2(d.x, -d.y))
        el = math.degrees(math.asin(max(-1, min(1, d.z / d.length))))
        if (abs(th) < 102 and el < hairline_el(th) - 1.5) or el < -22:
            kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(cap.data); bm.free()
    so_ = cap.modifiers.new("t", "SOLIDIFY"); so_.thickness = 0.01
    bake(cap)
    R(cap, "head")
    bun_dir = Vector((0, 1, 0.42)).normalized()
    bun_c = H.pt(bun_dir, 0.055)[0]
    for k in range(-13, 14):
        th = k * 7.6
        el0 = hairline_el(th)
        d0 = H.dir(th, el0 + 1.0)
        dm = (d0 + bun_dir + Vector((0, 0, 0.9 if abs(th) < 60 else 0.35))).normalized()
        pts = []
        for i in range(8):
            t = i / 7
            d = ((1 - t) ** 2) * d0 + 2 * t * (1 - t) * dm + (t ** 2) * bun_dir
            off = 0.016 + 0.01 * math.sin(math.pi * t)
            pts.append(H.pt(d, off)[0])
        o = R(curve(f"{name}_strand{k}", pts, 0.019, hr, res=3), "head")
        taper(o, 0.75, 0.6)
    for s in (1, -1):   # volume over the temples so it reads as hair, not a cap
        p, n = H.at(70 * s, 22, 0.012)
        R(blob(f"{name}_temple{s}", p, (0.045, 0.075, 0.06), hr, rot=(0, 0, -25 * s), lumps=False), "head")
    for k in range(6):
        t0 = -6 + k * 2.5
        pts = []
        for i in range(7):
            t = i / 6
            th = t0 + (78 - t0) * t ** 0.9
            el = (58 - 3 * k) + (14 - (58 - 3 * k)) * t ** 1.3
            pts.append(H.at(th, el, 0.03 + 0.012 * math.sin(math.pi * t))[0])
        pts.append(H.pt(H.dir(112, 4) + bun_dir * 0.6, 0.03)[0])
        o = R(curve(f"{name}_fringe{k}", pts, 0.021, hr, res=3), "head")
        taper(o, 0.6, 0.7)
    if hair_style == "bun":
        R(blob(f"{name}_bun", bun_c, (0.075, 0.065, 0.07), hr, lumps=False), "head")
        sp = []
        ax_u = Vector((1, 0, 0)); ax_v = bun_dir.cross(ax_u).normalized()
        for i in range(30):
            a = i / 29 * 4.2 * math.pi
            r = 0.07 * (1 - i / 40)
            sp.append(bun_c + bun_dir * (0.035 - 0.03 * i / 29) + ax_u * math.cos(a) * r + ax_v * math.sin(a) * r * 0.95)
        R(curve(f"{name}_bunswirl", sp, 0.017, hr, res=3), "head")

    for o, bone in rigid:
        bind(arm, o, bone)
    arm.location = loc
    arm.rotation_euler.z = rot_z
    bpy.context.view_layer.update()
    return arm


# ------------------------------------------------------------------ poses
def pose(arm, name):
    clay.rest(arm)
    P = lambda v: arm.matrix_world @ Vector(v)
    pb = clay.point_bone
    if name == "idle":
        pb(arm, "upperarm.L", P((0.23, 0.0, 0.86)))
        pb(arm, "upperarm.R", P((-0.23, 0.0, 0.86)))
        pb(arm, "forearm.L", P((0.235, -0.05, 0.67)))
        pb(arm, "forearm.R", P((-0.235, -0.05, 0.67)))
    elif name == "nervous":   # hunched, hands clasped at the chest, head tilted down
        pb(arm, "chest", P((0, -0.05, 1.10)))
        pb(arm, "head", P((0.06, -0.12, 1.57)))
        pb(arm, "upperarm.L", P((0.20, -0.13, 0.88)))
        pb(arm, "upperarm.R", P((-0.20, -0.13, 0.88)))
        pb(arm, "forearm.L", P((0.035, -0.27, 0.99)))
        pb(arm, "forearm.R", P((-0.035, -0.27, 0.99)))
        pb(arm, "hand.L", P((0.0, -0.30, 1.08)))
        pb(arm, "hand.R", P((0.0, -0.30, 1.08)))
    return arm
