"""Build, animate and render one shot of plan.json.

Render strategy (keeps 960x540 but makes full animation affordable):
  * the camera is static in 3D (pushes/pans are done in 2D in the edit),
  * the set is rendered once as a plate with every animated object excluded,
  * each frame (12 fps) renders only the screen region covering the animated objects,
  * region and plate are blended with a feathered mask and encoded to out/shot_XXX.mp4.
python3 -I shots.py <shot_id> [samples=16] [frames=a-b] [out=out]
"""
import sys, os, math, json, shutil, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler
from bpy_extras.object_utils import world_to_camera_view
import lib, clay, fig, sets
from toon import rbox

FPS = 12
W, H = 960, 540
R = math.radians
UP = Vector((0, 0, 1))


# ------------------------------------------------------------------ extra poses
def pose(arm, name):
    P = lambda v: arm.matrix_world @ Vector(v)
    pb = clay.point_bone
    if name in ("idle", "nervous", "scared", "phone", "knock", "point", "cower", "walk"):
        return fig.pose(arm, name)
    clay.rest(arm)
    if name == "walk2":
        pb(arm, "leg.L", P((0.07, 0.10, 0.07)))
        pb(arm, "leg.R", P((-0.07, -0.10, 0.06)))
        pb(arm, "upperarm.L", P((0.18, -0.06, 0.50)))
        pb(arm, "upperarm.R", P((-0.18, 0.06, 0.50)))
    elif name == "run":
        pb(arm, "chest", P((0, -0.06, 0.64)))
        pb(arm, "leg.L", P((0.07, -0.16, 0.10)))
        pb(arm, "leg.R", P((-0.07, 0.14, 0.12)))
        pb(arm, "upperarm.L", P((0.17, 0.10, 0.52)))
        pb(arm, "forearm.L", P((0.17, 0.02, 0.46)))
        pb(arm, "upperarm.R", P((-0.17, -0.10, 0.52)))
        pb(arm, "forearm.R", P((-0.17, -0.18, 0.58)))
    elif name == "run2":
        pb(arm, "chest", P((0, -0.06, 0.64)))
        pb(arm, "leg.L", P((0.07, 0.14, 0.12)))
        pb(arm, "leg.R", P((-0.07, -0.16, 0.10)))
        pb(arm, "upperarm.L", P((0.17, -0.10, 0.52)))
        pb(arm, "forearm.L", P((0.17, -0.18, 0.58)))
        pb(arm, "upperarm.R", P((-0.17, 0.10, 0.52)))
        pb(arm, "forearm.R", P((-0.17, 0.02, 0.46)))
    elif name == "shush":          # finger to the lips
        pb(arm, "upperarm.R", P((-0.15, -0.10, 0.52)))
        pb(arm, "forearm.R", P((-0.05, -0.17, 0.70)))
        pb(arm, "hand.R", P((-0.02, -0.18, 0.80)))
    elif name == "lookup":
        pb(arm, "chest", P((0, 0.03, 0.64)))
        pb(arm, "head", P((0, 0.16, 0.98)))
    elif name == "poke":           # both hands up holding a broom over the head
        pb(arm, "chest", P((0, 0.03, 0.64)))
        pb(arm, "head", P((0, 0.12, 0.99)))
        pb(arm, "upperarm.R", P((-0.16, -0.06, 0.74)))
        pb(arm, "forearm.R", P((-0.10, -0.10, 0.86)))
        pb(arm, "hand.R", P((-0.08, -0.10, 0.96)))
        pb(arm, "upperarm.L", P((0.16, -0.06, 0.70)))
        pb(arm, "forearm.L", P((0.04, -0.12, 0.78)))
        pb(arm, "hand.L", P((0.0, -0.12, 0.86)))
    elif name == "poke2":
        pb(arm, "chest", P((0, 0.04, 0.64)))
        pb(arm, "head", P((0, 0.14, 0.99)))
        pb(arm, "upperarm.R", P((-0.15, -0.04, 0.80)))
        pb(arm, "forearm.R", P((-0.09, -0.06, 0.95)))
        pb(arm, "hand.R", P((-0.07, -0.06, 1.05)))
        pb(arm, "upperarm.L", P((0.15, -0.04, 0.76)))
        pb(arm, "forearm.L", P((0.04, -0.08, 0.86)))
        pb(arm, "hand.L", P((0.0, -0.08, 0.95)))
    elif name == "kick":
        pb(arm, "chest", P((0, 0.05, 0.64)))
        pb(arm, "leg.R", P((-0.06, -0.30, 0.16)))
        pb(arm, "upperarm.L", P((0.22, 0.04, 0.52)))
        pb(arm, "upperarm.R", P((-0.22, 0.04, 0.52)))
    elif name == "sit":            # sitting on the floor, legs forward
        pb(arm, "leg.L", P((0.08, -0.32, 0.36)))
        pb(arm, "leg.R", P((-0.08, -0.32, 0.36)))
        pb(arm, "upperarm.L", P((0.17, -0.06, 0.50)))
        pb(arm, "upperarm.R", P((-0.17, -0.06, 0.50)))
        pb(arm, "forearm.L", P((0.13, -0.18, 0.44)))
        pb(arm, "forearm.R", P((-0.13, -0.18, 0.44)))
    elif name == "sitcower":       # knees up, arms over the head
        pb(arm, "leg.L", P((0.08, -0.25, 0.62)))
        pb(arm, "leg.R", P((-0.08, -0.25, 0.62)))
        pb(arm, "chest", P((0, -0.08, 0.63)))
        pb(arm, "head", P((0, -0.17, 0.94)))
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.16 * s, -0.14, 0.68)))
            pb(arm, f"forearm.{lr}", P((0.10 * s, -0.17, 0.82)))
            pb(arm, f"hand.{lr}", P((0.04 * s, -0.16, 0.90)))
    elif name == "sitphone":
        pb(arm, "leg.L", P((0.08, -0.25, 0.62)))
        pb(arm, "leg.R", P((-0.08, -0.25, 0.62)))
        pb(arm, "head", P((-0.03, -0.03, 1.0)))
        pb(arm, "upperarm.R", P((-0.21, -0.05, 0.53)))
        pb(arm, "forearm.R", P((-0.19, -0.08, 0.72)))
        pb(arm, "hand.R", P((-0.17, -0.06, 0.80)))
        pb(arm, "upperarm.L", P((0.15, -0.12, 0.50)))
        pb(arm, "forearm.L", P((0.10, -0.2, 0.60)))
    elif name == "hide":           # crouched behind someone, hands on his arm
        pb(arm, "chest", P((0, -0.06, 0.62)))
        pb(arm, "head", P((0.02, -0.10, 0.96)))
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.14 * s, -0.12, 0.52)))
            pb(arm, f"forearm.{lr}", P((0.06 * s, -0.24, 0.58)))
    elif name == "stretch":
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.16 * s, 0.0, 0.76)))
            pb(arm, f"forearm.{lr}", P((0.10 * s, 0.0, 0.90)))
            pb(arm, f"hand.{lr}", P((0.06 * s, 0.0, 0.98)))
        pb(arm, "head", P((0, 0.06, 1.0)))
    elif name == "shake":          # trembling hands in front (alternate with shake2)
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.17 * s, -0.08, 0.50)))
            pb(arm, f"forearm.{lr}", P((0.10 * s, -0.20, 0.56)))
    elif name == "shake2":
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.175 * s, -0.085, 0.505)))
            pb(arm, f"forearm.{lr}", P((0.112 * s, -0.205, 0.575)))
    elif name == "papers":         # hands on the desk
        for s, lr in ((1, "L"), (-1, "R")):
            pb(arm, f"upperarm.{lr}", P((0.17 * s, -0.10, 0.50)))
            pb(arm, f"forearm.{lr}", P((0.10 * s, -0.24, 0.50)))
        pb(arm, "head", P((0, -0.10, 0.99)))
    elif name == "pocket":
        pb(arm, "upperarm.R", P((-0.21, 0.02, 0.50)))
        pb(arm, "forearm.R", P((-0.17, -0.05, 0.40)))
        pb(arm, "head", P((-0.04, -0.08, 0.99)))
    else:
        raise ValueError(f"unknown pose {name}")
    return arm


def look(arm, target, amount=0.75):
    """turn the head so the face points at a world target"""
    pbh = arm.pose.bones["head"]
    h = arm.matrix_world @ pbh.head
    tail = arm.matrix_world @ pbh.tail
    f = (arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    d = (Vector(target) - h).normalized()
    q = Quaternion().slerp(f.rotation_difference(d), amount)
    clay.point_bone(arm, "head", h + q @ (tail - h))


# ------------------------------------------------------------------ props
def _mat(name, col, emit=0.0):
    return lib.emit_mat(name, col, emit) if emit else clay.clay_mat(name, col, rough=0.4, dents=0.1)


def prop(arm, kind, text=None):
    clay.rest(arm)
    bpy.context.view_layer.update()
    s = arm.scale.x
    M = arm.matrix_world
    objs = []
    if kind == "phone":
        c = M @ Vector((-0.205, -0.06, 0.335))
        o = lib.box("phone", (0.035 * s, 0.016 * s, 0.075 * s), c, _mat("phone_body", (0.02, 0.02, 0.025)))
        scr = lib.box("phone_scr", (0.031 * s, 0.003 * s, 0.066 * s), c + M.to_3x3() @ Vector((0, -0.009, 0)),
                      _mat("phone_glow", (0.7, 0.82, 1.0), 2.5))
        objs = [o, scr]
        bone = "hand.R"
    elif kind == "broom":
        c = M @ Vector((-0.205, -0.045, 0.33))
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.012 * s, depth=0.75 * s, location=c + M.to_3x3() @ Vector((0, 0, 0.12)))
        st = bpy.context.object; st.name = "broom_stick"; st.data.materials.append(_mat("broom_m", (0.35, 0.16, 0.05)))
        br = lib.box("broom_head", (0.20 * s, 0.05 * s, 0.10 * s), c + M.to_3x3() @ Vector((0, 0, 0.52)), _mat("broom_h", (0.55, 0.45, 0.2)))
        objs = [st, br]
        bone = "hand.R"
    elif kind == "papers":
        c = M @ Vector((0.0, -0.20, 0.36))
        objs = [lib.box("paper_stack", (0.16 * s, 0.11 * s, 0.03 * s), c, _mat("paper_m", (0.75, 0.73, 0.66)))]
        bone = "hand.L"
    for o in objs:
        fig.bind(arm, o, bone)
    return objs


def phone_on_table(loc, text_lines, rot_z=0.0, glow=2.5):
    """phone lying on a surface with readable text (for close-ups)"""
    body = lib.box("tphone", (0.08, 0.16, 0.012), loc, _mat("phone_body", (0.02, 0.02, 0.025)), rot=(0, 0, rot_z))
    scr = lib.box("tphone_scr", (0.072, 0.148, 0.003), (loc[0], loc[1], loc[2] + 0.0075), _mat("phone_glow2", (0.55, 0.65, 0.9), glow), rot=(0, 0, rot_z))
    objs = [body, scr]
    for i, t in enumerate(text_lines):
        o = sets.text(f"tphone_t{i}", t, (loc[0], loc[1] + 0.045 - i * 0.03, loc[2] + 0.0095), 0.011 if i else 0.013,
                      (0.02, 0.02, 0.03) if i else (0.6, 0.05, 0.05), rot=(0, 0, math.degrees(rot_z)))
        objs.append(o)
    return objs


# ------------------------------------------------------------------ sets
def build_set(spec):
    n = spec["name"]
    p = {k: v for k, v in spec.items() if k not in ("name", "exposure")}
    if n == "unit":
        return sets.unit(**p)
    if n == "corridor":
        return sets.corridor(**p)
    if n == "stairs":
        return sets.stairs(**p)
    if n == "lift":
        return sets.lift(**p)
    if n == "lobby":
        return sets.lobby()
    if n == "exterior":
        cams, mk = sets.exterior(**{k: v for k, v in p.items() if k in ("twin", "night")})
        if "lit" in p:   # override window lighting of tower A (story: none lit)
            for o in bpy.data.objects:
                if o.name.startswith("towerA_w"):
                    o.data.materials.clear()
                    o.data.materials.append(sets.C((0.012, 0.014, 0.018), 0.0, 0.15))
        return cams, mk
    if n == "bedroom":
        cams, mk = sets.bedroom(p.get("variant", "sari"))
        if p.get("nophone"):
            for nm in ("phone", "phone_scr", "phone_l"):
                if nm in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects[nm])
        if "clock" in p and "clock" in bpy.data.objects:
            bpy.data.objects["clock"].data.body = p["clock"]
        return cams, mk
    if n == "bathroom":
        return sets.bathroom()
    if n == "parking":
        return sets.parking()
    raise ValueError(n)


# ------------------------------------------------------------------ camera helpers
def head_point(arm):
    return arm.matrix_world @ Vector((0, -0.03, 0.83))


def cam_on(arm, kind="close", side=0.3, up=0.0, dist=None, lens=None):
    f = (arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    sv = f.cross(UP).normalized()
    s = arm.scale.x
    hp = head_point(arm)
    if kind == "close":
        d, ln, tgt = dist or 0.95, lens or 50, hp + Vector((0, 0, -0.02 * s))
    elif kind == "xclose":
        d, ln, tgt = dist or 0.62, lens or 60, hp + Vector((0, 0, -0.01 * s))
    elif kind == "medium":
        d, ln, tgt = dist or 1.9, lens or 40, arm.matrix_world @ Vector((0, 0, 0.62))
    elif kind == "full":
        d, ln, tgt = dist or 3.2, lens or 35, arm.matrix_world @ Vector((0, 0, 0.5))
    elif kind == "feet":
        d, ln, tgt = dist or 0.9, lens or 40, arm.matrix_world @ Vector((0, -0.05, 0.05))
        return (tuple(tgt + f * d + sv * side + Vector((0, 0, 0.12))), tuple(tgt), ln)
    elif kind == "low":
        d, ln, tgt = dist or 1.3, lens or 30, hp
        return (tuple(hp + f * d + sv * side + Vector((0, 0, -0.75 * s))), tuple(tgt), ln)
    loc = tgt + f * d + sv * side + Vector((0, 0, up))
    return (tuple(loc), tuple(tgt), ln)


# ------------------------------------------------------------------ scene assembly
def collect(arm):
    out = []
    stack = list(arm.children)
    while stack:
        o = stack.pop()
        out.append(o)
        stack += list(o.children)
    return out


def build(shot):
    sc = lib.reset()
    lib.set_output(sc, W, H, SAMPLES)
    sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 1
    sc.cycles.transmission_bounces = 1; sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = shot["set"].get("exposure", 0.6)
    sc.render.fps = FPS
    nfr = max(1, round((shot["t1"] - shot["t0"]) * FPS))
    sc.frame_start, sc.frame_end = 1, nfr
    cams, marks = build_set(shot["set"])
    dyn = bpy.data.collections.new("DYN")
    sc.collection.children.link(dyn)
    before = set(bpy.data.objects)
    actors = {}
    for c in shot.get("cast", []):
        who = c["who"]
        base = c.get("as", who)
        exprs = sorted({c.get("expr", fig.CAST[base].get("expr", "cemas"))} |
                       {k[2] for k in c.get("keys", []) if k[1] == "expr"}) if base != "hantu" else None
        loc, rot = c.get("at"), c.get("rot")
        if isinstance(loc, str):
            loc, r0 = marks[loc]
            rot = rot if rot is not None else math.degrees(r0)
        over = dict(c.get("over", {}))
        arm = fig.make(base, loc=tuple(loc), rot_z=R(rot or 0), exprs=exprs,
                       expr=c.get("expr", fig.CAST[base].get("expr", "cemas")) if base != "hantu" else "hantu", **over)
        arm.name = who if who not in bpy.data.objects or bpy.data.objects[who] == arm else arm.name
        if c.get("prop"):
            prop(arm, c["prop"])
        if c.get("lie"):
            fig.lie_down(arm, tuple(c["lie"][:3]), R(c["lie"][3] if len(c["lie"]) > 3 else 0))
        actors[who] = (arm, c)
    for o in bpy.data.objects:
        if o not in before or o.name.startswith(("tphone",)):
            pass
    # extra props / screens that belong to the animated layer
    for e in shot.get("extras", []):
        if e["kind"] == "phone_table":
            for o in phone_on_table(tuple(e["at"]), e["text"], R(e.get("rot", 0)), e.get("glow", 2.5)):
                before.discard(o)
    # clear furniture standing where an actor stands (office chairs)
    for arm, c in actors.values():
        p0 = arm.location
        for o in [o for o in bpy.data.objects if o.name.startswith("chair") and o.parent is None]:
            if (Vector((o.location.x, o.location.y)) - Vector((p0.x, p0.y))).length < 0.5:
                for ch in dyn_targets(o.name):
                    bpy.data.objects.remove(ch)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for col in list(o.users_collection):
            col.objects.unlink(o)
        dyn.objects.link(o)
    # set objects that animate
    for d in shot.get("dyn", []):
        for o in dyn_targets(d["obj"]):
            for col in list(o.users_collection):
                col.objects.unlink(o)
            dyn.objects.link(o)
    # camera
    cs = shot["cam"]
    if isinstance(cs, str):
        cam_spec = cams[cs]
    elif isinstance(cs, dict) and "on" in cs:
        arm = actors[cs["on"]][0]
        cam_spec = cam_on(arm, cs.get("kind", "close"), cs.get("side", 0.3), cs.get("up", 0.0), cs.get("dist"), cs.get("lens"))
    else:
        cam_spec = cs
    cam = lib.camera(*cam_spec)
    if shot.get("dof"):
        lib.dof(cam, shot["dof"][0], shot["dof"][1])
    animate(sc, shot, actors, cams, marks)
    return sc, cam, dyn, actors


def dyn_targets(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return []
    out = [o]
    stack = list(o.children)
    while stack:
        c = stack.pop(); out.append(c); stack += list(c.children)
    return out


def fr(shot, t):
    """time inside the shot (s) -> frame number; strings 'w12' were resolved in plan.json already"""
    return max(1, min(round(t * FPS) + 1, round((shot["t1"] - shot["t0"]) * FPS)))


def key_bones(arm, f):
    for pb in arm.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=f)


def animate(sc, shot, actors, cams, marks):
    nfr = sc.frame_end
    for who, (arm, c) in actors.items():
        keys = sorted(c.get("keys", []), key=lambda k: k[0])
        moves = [k for k in keys if k[1] == "move"]
        arm.rotation_mode = "XYZ"
        if moves:
            arm.keyframe_insert("location", frame=1); arm.keyframe_insert("rotation_euler", frame=1)
            for t, _, v in moves:
                f = fr(shot, t)
                if v[0] is not None:
                    arm.location = Vector(v[:3]) if len(v) >= 3 else arm.location
                if len(v) > 3 and v[3] is not None:
                    arm.rotation_euler.z = R(v[3])
                arm.keyframe_insert("location", frame=f); arm.keyframe_insert("rotation_euler", frame=f)
        # pose track
        state = {"pose": c.get("pose", "idle"), "look": c.get("look")}
        track = [(0.0, dict(state))]
        for t, kind, v in keys:
            if kind == "pose":
                state["pose"] = v; track.append((t, dict(state)))
            elif kind == "look":
                state["look"] = v; track.append((t, dict(state)))
        hold = c.get("hold", 0.25)   # seconds to blend into a new pose
        for i, (t, st) in enumerate(track):
            for ff in ([fr(shot, t)] if i == 0 else [fr(shot, max(0, t - hold)), fr(shot, t)]):
                prev = track[i - 1][1] if (i > 0 and ff == fr(shot, max(0, t - hold))) else st
                sc.frame_set(ff)
                pose(arm, prev["pose"])
                if prev.get("look") is not None:
                    tgt = prev["look"]
                    if isinstance(tgt, str):
                        tgt = tuple(head_point(actors[tgt][0])) if tgt in actors else cams[tgt][0]
                    look(arm, tgt)
                key_bones(arm, ff)
        # walking: alternate legs while moving
        if c.get("walk"):
            for a, b in c["walk"]:
                fa, fb = fr(shot, a), fr(shot, b)
                step = 3 if c.get("walk_style") != "run" else 2
                names = ("walk", "walk2") if c.get("walk_style") != "run" else ("run", "run2")
                for k, ff in enumerate(range(fa, fb, step)):
                    sc.frame_set(ff)
                    pose(arm, names[k % 2])
                    key_bones(arm, ff)
                sc.frame_set(fb); pose(arm, track[-1][1]["pose"]); key_bones(arm, fb)
        # expressions
        for t, kind, v in keys:
            if kind == "expr":
                fig.key_expr(arm, v, fr(shot, t))
        if any(k[1] == "expr" for k in keys):
            fig.key_expr(arm, c.get("expr", fig.CAST[c.get("as", who)].get("expr", "cemas")), 1)
            for t, kind, v in keys:
                if kind == "expr":
                    fig.key_expr(arm, v, fr(shot, t))
        # visibility
        vis = [k for k in keys if k[1] == "show"]
        if vis or c.get("hidden"):
            parts = collect(arm)
            states = [(1, not c.get("hidden", False))] + [(fr(shot, t), bool(v)) for t, _, v in vis]
            for o in parts:
                base_hidden = o.hide_render
                for ff, on in states:
                    o.hide_render = base_hidden or not on
                    o.keyframe_insert("hide_render", frame=ff)
        # breathing (delta channels so they never fight the main keys)
        if c.get("breathe", c.get("as", who) != "hantu"):
            ph = (hash(who) % 100) / 100 * 6.28
            # stepped like stop-motion "boil": the pose only changes every 4th frame, so held
            # frames in between are identical and are not rendered again
            for ff in range(1, nfr + 1, 4):
                tt = (ff - 1) / FPS
                arm.delta_scale = (1, 1, 1 + 0.008 * math.sin(tt * 2 * math.pi / 3.2 + ph))
                arm.delta_rotation_euler = (0, 0, R(0.7 * math.sin(tt * 2 * math.pi / 5.1 + ph)))
                arm.keyframe_insert("delta_scale", frame=ff); arm.keyframe_insert("delta_rotation_euler", frame=ff)
            if arm.animation_data and arm.animation_data.action:
                for fc in arm.animation_data.action.fcurves:
                    if fc.data_path.startswith("delta_"):
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
        if c.get("jitter"):        # trembling
            a, b = c["jitter"]
            for ff in range(fr(shot, a), fr(shot, b)):
                arm.delta_location = (0.004 * math.sin(ff * 2.7), 0.003 * math.cos(ff * 3.3), 0)
                arm.keyframe_insert("delta_location", frame=ff)
    # set animation
    for d in shot.get("dyn", []):
        o = bpy.data.objects[d["obj"]]
        for t, v in d["keys"]:
            f = fr(shot, t)
            if d["prop"] == "rotz":
                o.rotation_euler.z = R(v); o.keyframe_insert("rotation_euler", index=2, frame=f)
            elif d["prop"] == "locx":
                o.location.x = v; o.keyframe_insert("location", index=0, frame=f)
            elif d["prop"] == "emit":
                for m in o.data.materials:
                    nd = m.node_tree.nodes.get("Emission") or next((n for n in m.node_tree.nodes if n.type == "EMISSION"), None)
                    if nd:
                        nd.inputs["Strength"].default_value = v
                        nd.inputs["Strength"].keyframe_insert("default_value", frame=f)
            elif d["prop"] == "hide":
                o.hide_render = bool(v); o.keyframe_insert("hide_render", frame=f)
        if d["prop"] in ("emit", "hide"):
            for fc in (o.animation_data.action.fcurves if o.animation_data and o.animation_data.action else []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    sc.frame_set(1)


# ------------------------------------------------------------------ rendering
def region(sc, cam, dyn):
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys = [], []
    for o in dyn.all_objects:
        if o.type not in ("MESH", "CURVE", "FONT") or o.hide_render:
            continue
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            p = world_to_camera_view(sc, cam, oe.matrix_world @ Vector(c))
            if p.z > 0:
                xs.append(p.x); ys.append(p.y)
    if not xs:
        return None
    x0, x1 = max(0.0, min(xs) - 0.05), min(1.0, max(xs) + 0.05)
    y0, y1 = max(0.0, min(ys) - 0.10), min(1.0, max(ys) + 0.05)
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, x1, y0, y1)


def signature(dyn):
    sig = []
    for o in sorted(dyn.all_objects, key=lambda o: o.name):
        if o.hide_render:
            sig.append((o.name, 0)); continue
        m = o.matrix_world
        sig.append((o.name, tuple(round(v, 4) for row in m for v in row)))
        if o.type == "ARMATURE":
            sig.append(tuple(round(v, 4) for pb in o.pose.bones for v in pb.rotation_quaternion))
    return hash(tuple(sig))


def feather(alpha, px=10):
    from PIL import Image, ImageFilter
    a = Image.fromarray(alpha)
    a = a.filter(ImageFilter.MinFilter(px * 2 + 1)).filter(ImageFilter.GaussianBlur(px * 0.7))
    return np.asarray(a).astype(np.float32)[..., None] / 255.0


def render_shot(shot, out, frames=None):
    from PIL import Image
    t_start = time.time()
    sc, cam, dyn, actors = build(shot)
    sid = shot["id"]
    work = os.path.join(out, f"work_{sid:03d}")
    os.makedirs(work, exist_ok=True)
    plate_p = os.path.join(work, "plate.png")
    lc = bpy.context.view_layer.layer_collection.children["DYN"]
    if not os.path.exists(plate_p):
        lc.exclude = True
        sc.render.use_border = False
        sc.frame_set(1)
        sc.render.filepath = plate_p
        bpy.ops.render.render(write_still=True)
        lc.exclude = False
    plate = np.asarray(Image.open(plate_p).convert("RGB")).astype(np.float32)
    nfr = sc.frame_end
    fa, fb = frames or (1, nfr)
    sc.render.use_border = True
    sc.render.use_crop_to_border = False
    last_sig, last_img = None, None
    for f in range(fa, fb + 1):
        fp = os.path.join(work, f"f_{f:04d}.png")
        if os.path.exists(fp):
            continue
        sc.frame_set(f)
        sig = signature(dyn)
        if sig == last_sig and last_img is not None:
            shutil.copyfile(last_img, fp); continue
        reg = region(sc, cam, dyn)
        if reg is None:
            Image.fromarray(plate.astype(np.uint8)).save(fp)
        else:
            sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = reg
            tmp = os.path.join(work, "_r.png")
            sc.render.filepath = tmp
            bpy.ops.render.render(write_still=True)
            rgba = np.asarray(Image.open(tmp).convert("RGBA"))
            m = feather(rgba[..., 3])
            comp = plate * (1 - m) + rgba[..., :3].astype(np.float32) * m
            Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).save(fp)
        last_sig, last_img = sig, fp
        print(f"shot {sid} frame {f}/{nfr} {time.time() - t_start:.0f}s", flush=True)
    return work, nfr


def encode(work, nfr, out_mp4):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(work, "f_%04d.png"),
                    "-frames:v", str(nfr), "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv444p", out_mp4],
                   check=True)


SAMPLES = 16
if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    SAMPLES = int(args.get("samples", 16))
    plan = json.load(open(os.path.join(HERE, "plan.json")))
    shot = next(s for s in plan["shots"] if s["id"] == int(sys.argv[1]))
    out = args.get("out", os.path.join(HERE, "out"))
    frames = tuple(int(x) for x in args["frames"].split("-")) if "frames" in args else None
    work, nfr = render_shot(shot, out, frames)
    if not frames or frames[1] >= nfr:
        if all(os.path.exists(os.path.join(work, f"f_{f:04d}.png")) for f in range(1, nfr + 1)):
            encode(work, nfr, os.path.join(out, f"shot_{shot['id']:03d}.mp4"))
            print("ENCODED", shot["id"], flush=True)
