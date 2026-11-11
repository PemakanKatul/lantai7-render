"""Core Blender helpers for the horror short (headless bpy, CPU Cycles).

Avatars: Microsoft Rocketbox (MIT). Rebuilt PBR materials with SSS skin.
All poses are applied in world space so they do not depend on Biped bone roll.
"""
import bpy, math, os, json
from mathutils import Matrix, Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.environ.get("ROCKETBOX", "/home/claude/rocketbox/Assets/Avatars/Adults")


# ----------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.05
    cy.max_bounces = 3
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 2
    cy.transmission_bounces = 2
    cy.transparent_max_bounces = 8
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
        cy.denoising_prefilter = "FAST"
    except Exception:
        pass
    sc.render.use_persistent_data = True
    sc.render.fps = 24
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.film_transparent = False
    return sc


def set_output(sc, w, h, samples):
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.image_settings.file_format = "PNG"


def world(color=(0.01, 0.012, 0.018), strength=1.0):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def box(name, size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    return o


def area_light(name, loc, target, power, size=1.0, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = power
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    aim(o, target)
    return o


def point_light(name, loc, power, color=(1, 1, 1), radius=0.1):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = power
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o


def aim(o, target):
    v = Vector(target) - o.location
    o.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()


def camera(loc, target, lens=35):
    d = bpy.data.cameras.new("Cam")
    d.lens = lens
    d.sensor_width = 36
    d.clip_start = 0.02
    o = bpy.data.objects.new("Cam", d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    aim(o, target)
    bpy.context.scene.camera = o
    return o


def dof(cam, focus_dist, fstop=2.8):
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = focus_dist
    cam.data.dof.aperture_fstop = fstop


# ----------------------------------------------------------------- avatar
def _img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color:
        im.colorspace_settings.name = "Non-Color"
    return im


SKIN_TONES = {  # target average skin RGB (0-255)
    "sawo": (168, 118, 86),      # sawo matang, Indonesian medium-tan
    "kuning": (196, 150, 116),   # kuning langsat, lighter
    "gelap": (128, 86, 60),
}
CACHE = os.path.join(HERE, "cache")


def tinted(path, tone, ref=None):
    """Return path to a skin-tinted copy of a color texture. Only skin-like
    pixels change (soft chroma mask), clothes/eyes/hair stay as they are."""
    if not tone:
        return path
    import numpy as np
    from PIL import Image
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"{tone}_" + os.path.basename(path).replace(".tga", ".png"))
    if os.path.exists(out):
        return out
    im = Image.open(path)
    has_a = im.mode == "RGBA"
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb = a[..., :3]
    refc = np.array(ref if ref is not None else _skin_ref(path), np.float32)
    tgt = np.array(SKIN_TONES[tone], np.float32)
    # chroma distance to the reference skin colour
    def chroma(c):
        s = c.sum(-1, keepdims=True) + 1e-3
        return c / s
    d = np.linalg.norm(chroma(rgb) - chroma(refc), axis=-1)
    lum = rgb.mean(-1)
    mask = np.clip(1 - (d - 0.025) / 0.05, 0, 1) * np.clip((lum - 35) / 40, 0, 1)
    gain = tgt / refc
    out_rgb = rgb * (1 - mask[..., None]) + np.clip(rgb * gain, 0, 255) * mask[..., None]
    if "_head_" in path:
        out_rgb = _brown_iris(out_rgb)
    a[..., :3] = out_rgb
    Image.fromarray(a.astype(np.uint8), "RGBA" if has_a else "RGBA").save(out)
    return out


def _brown_iris(rgb):
    """Rocketbox head atlases keep the eyeball in the lower-left corner.
    Find the white sclera disk there and turn the iris inside it dark brown."""
    import numpy as np
    H, W = rgb.shape[:2]
    y0, y1, x0, x1 = int(H * 0.83), H, int(W * 0.17), int(W * 0.37)
    reg = rgb[y0:y1, x0:x1]
    lum = reg.mean(-1)
    sat = reg.max(-1) - reg.min(-1)
    white = (lum > 165) & (sat < 45)
    if white.sum() < 200:
        return rgb
    ys, xs = np.nonzero(white)
    # largest white cluster: take the median as the eye centre
    cy, cx = np.median(ys), np.median(xs)
    r_w = np.sqrt(white.sum() / np.pi)
    yy, xx = np.mgrid[:reg.shape[0], :reg.shape[1]]
    dist = np.hypot(yy - cy, xx - cx)
    iris = (dist < r_w * 0.75) & ~white
    soft = np.clip((r_w * 0.75 - dist) / (r_w * 0.08 + 1), 0, 1) * iris
    l = lum[..., None]
    brown = np.concatenate([l * 0.55, l * 0.34, l * 0.20], -1) * 0.75
    reg2 = reg * (1 - soft[..., None]) + brown * soft[..., None]
    rgb = rgb.copy()
    rgb[y0:y1, x0:x1] = reg2
    return rgb


def _skin_ref(path):
    """Average skin colour: centre of the head texture (cheeks/forehead)."""
    import numpy as np
    from PIL import Image
    head = path.replace("_body_", "_head_")
    a = np.asarray(Image.open(head).convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    c = a[int(h * .35):int(h * .65), int(w * .3):int(w * .7)].reshape(-1, 3)
    lum = c.mean(1)
    c = c[(lum > np.percentile(lum, 30)) & (lum < np.percentile(lum, 90))]
    return tuple(np.median(c, 0))


def _build_material(m, texdir, prefix, part, skin_sss, tone=None):
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    col = nt.nodes.new("ShaderNodeTexImage")
    cp = f"{texdir}/{prefix}_{part}_color.tga"
    col.image = _img(tinted(cp, tone) if part in ("head", "body") else cp)
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    if part == "opacity":
        # hair cards / lashes: alpha from the texture
        nt.links.new(col.outputs["Alpha"], b.inputs["Alpha"])
        b.inputs["Roughness"].default_value = 0.45
        m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
        return
    nrm_p = f"{texdir}/{prefix}_{part}_normal.tga"
    if os.path.exists(nrm_p):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = _img(nrm_p, True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.8
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
    sp_p = f"{texdir}/{prefix}_{part}_specular.tga"
    if os.path.exists(sp_p):
        s = nt.nodes.new("ShaderNodeTexImage")
        s.image = _img(sp_p, True)
        inv = nt.nodes.new("ShaderNodeMapRange")
        inv.inputs["To Min"].default_value = 0.85
        inv.inputs["To Max"].default_value = 0.35
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(s.outputs["Color"], bw.inputs[0])
        nt.links.new(bw.outputs[0], inv.inputs["Value"])
        nt.links.new(inv.outputs[0], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = 0.6
    # subsurface: real skin on the head, a little on the body (bare arms/hands)
    b.inputs["Subsurface Weight"].default_value = skin_sss
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.012
    try:
        b.subsurface_method = "RANDOM_WALK_SKIN"
    except Exception:
        pass


BASE_RZ = math.radians(-90)


def load_avatar(avatar, name=None, loc=(0, 0, 0), rot_z=0.0, scale=1.0, tone="sawo"):
    """Import a Rocketbox avatar. Returns (armature, mesh). Faces -Y by default
    after rot_z=0 (verified in preview); rot_z in degrees."""
    d = f"{RB}/{avatar}"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f"{d}/Export/{avatar}.fbx", use_anim=False)
    new = [o for o in bpy.data.objects if o not in before]
    arm = [o for o in new if o.type == "ARMATURE"][0]
    mesh = [o for o in new if o.type == "MESH"][0]
    for o in new:
        if o.type == "EMPTY":
            bpy.data.objects.remove(o)
    arm.animation_data_clear()
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    tag = name or avatar
    arm.name = f"{tag}_rig"
    mesh.name = f"{tag}_body"
    texdir = f"{d}/Textures"
    seen = {}
    for slot in mesh.material_slots:
        m = slot.material
        prefix, part = m.name.split("_")[0], m.name.split("_")[-1]
        key = (avatar, m.name)
        if key in seen:
            continue
        nm = m.copy() if m.users > 1 else m
        nm.name = f"{tag}_{part}"
        _build_material(nm, texdir, prefix, part, 0.18 if part == "head" else 0.06, tone)
        slot.material = nm
        seen[key] = nm
    arm.scale = (arm.scale[0] * scale,) * 3
    arm.location = loc
    arm["user_rz"] = math.radians(rot_z)
    # Rocketbox FBX faces +X; BASE_RZ turns it to face -Y (towards a front camera)
    arm.rotation_euler = (arm.rotation_euler[0], arm.rotation_euler[1], math.radians(rot_z) + BASE_RZ)
    bpy.context.view_layer.update()
    # lift so the feet touch z=loc.z
    zmin = min((mesh.matrix_world @ v.co).z for v in list(mesh.data.vertices)[::25])
    arm.location.z += loc[2] - zmin
    bpy.context.view_layer.update()
    return arm, mesh


# ----------------------------------------------------------------- posing
# World-space rotations: each entry is bone -> list of (axis, degrees) applied
# around the bone head, in the avatar's own frame (x = avatar's left->right as
# seen from the front camera, y = backwards, z = up). Applied parent-first.
ORDER = ["Bip01 Pelvis", "Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2", "Bip01 Neck",
         "Bip01 Head", "Bip01 L Clavicle", "Bip01 R Clavicle",
         "Bip01 L UpperArm", "Bip01 R UpperArm", "Bip01 L Forearm", "Bip01 R Forearm",
         "Bip01 L Hand", "Bip01 R Hand", "Bip01 L Thigh", "Bip01 R Thigh",
         "Bip01 L Calf", "Bip01 R Calf", "Bip01 L Foot", "Bip01 R Foot"]

AX = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}


def rest_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    bpy.context.view_layer.update()


def apply_pose(arm, pose, rest=True):
    """pose: {bone: [("x", deg), ...]} rotations around avatar-frame axes."""
    if rest:
        rest_pose(arm)
    # avatar frame -> armature space rotation
    frame = arm.matrix_world.to_quaternion().inverted() @ Quaternion((0, 0, 1), arm.get("user_rz", 0.0))
    names = [n for n in ORDER if n in pose] + [n for n in pose if n not in ORDER]
    for bn in names:
        pb = arm.pose.bones.get(bn)
        if pb is None:
            continue
        q = Quaternion()
        for axis, deg in pose[bn]:
            a = frame @ AX[axis]
            q = Quaternion(a, math.radians(deg)) @ q
        M = pb.matrix.copy()
        head = M.translation.copy()
        R = q.to_matrix().to_4x4()
        newM = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ M
        pb.matrix = newM
        bpy.context.view_layer.update()


def key_pose(arm, frame):
    for pb in arm.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("location", frame=frame)


def pose_quats(arm, pose):
    """Return {bone: quaternion} for a pose (for blending between poses)."""
    apply_pose(arm, pose)
    return {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones}


def set_quats(arm, qa, qb=None, t=0.0):
    for pb in arm.pose.bones:
        a = qa.get(pb.name, Quaternion())
        pb.rotation_quaternion = a if qb is None else a.slerp(qb.get(pb.name, Quaternion()), t)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# Base pose library (avatar frame). Arms in Rocketbox start in an A-pose.
ARMS_DOWN = {
    "Bip01 L UpperArm": [("y", 47)],
    "Bip01 R UpperArm": [("y", -47)],
    "Bip01 L Forearm": [("x", -12)],
    "Bip01 R Forearm": [("x", -12)],
}

POSES = {
    "idle": dict(ARMS_DOWN),
    "nervous": {   # hunched, hands clasped at chest, head turned to the side
        **ARMS_DOWN,
        "Bip01 Spine1": [("x", 7)],
        "Bip01 Neck": [("x", 8)],
        "Bip01 Head": [("z", 25), ("x", -4)],
        "Bip01 L Clavicle": [("x", -6)],
        "Bip01 R Clavicle": [("x", -6)],
        "Bip01 L UpperArm": [("y", 50), ("x", -22)],
        "Bip01 R UpperArm": [("y", -50), ("x", -22)],
        "Bip01 L Forearm": [("x", -105), ("z", -38)],
        "Bip01 R Forearm": [("x", -105), ("z", 38)],
    },
}


# ================================================================ cinematic set
def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    return nt, nt.nodes["Principled BSDF"]


def grime_wall(name="wall_paint", base=(0.58, 0.56, 0.48), dirt=(0.24, 0.22, 0.17)):
    """old apartment paint: blotchy damp stains + vertical drip streaks + bump"""
    m = bpy.data.materials.new(name)
    nt, b = _nodes(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 1.6
    n1.inputs["Detail"].default_value = 8; n1.inputs["Roughness"].default_value = 0.62
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2.2, 2.2, 0.9)
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 3.0
    n2.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], n2.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
    nt.links.new(n1.outputs["Fac"], mx.inputs[0]); nt.links.new(n2.outputs["Fac"], mx.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22; ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = (*dirt, 1)
    nt.links.new(mx.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
    n3 = nt.nodes.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 40
    nt.links.new(tc.outputs["Object"], n3.inputs["Vector"])
    nt.links.new(n3.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def tile_floor(name="tiles", tile=0.4, c1=(0.50, 0.47, 0.41), c2=(0.44, 0.41, 0.35)):
    """ceramic floor tiles with dark grout and uneven gloss"""
    m = bpy.data.materials.new(name)
    nt, b = _nodes(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0 / tile
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = 1.0
    br.inputs["Row Height"].default_value = 1.0
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (0.08, 0.075, 0.06, 1)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.blend_type = "MULTIPLY"
    mixc.inputs["Factor"].default_value = 0.5
    nt.links.new(br.outputs["Color"], mixc.inputs["A"]); nt.links.new(nz.outputs["Color"], mixc.inputs["B"])
    nt.links.new(mixc.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.12; rr.inputs["To Max"].default_value = 0.45
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    mr = nt.nodes.new("ShaderNodeMath"); mr.operation = "MAXIMUM"
    nt.links.new(rr.outputs[0], mr.inputs[0]); nt.links.new(br.outputs["Fac"], mr.inputs[1])
    nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.3
    bump.invert = True
    nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def screen_mat(name="screen", tint=(0.75, 0.85, 1.0), strength=0.45):
    """monitor with a fake spreadsheet: bright rows/columns grid"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Scale"].default_value = 9
    br.inputs["Brick Width"].default_value = 0.7
    br.inputs["Row Height"].default_value = 0.09
    br.inputs["Mortar Size"].default_value = 0.006
    br.inputs["Color1"].default_value = (*tint, 1)
    br.inputs["Color2"].default_value = tuple(c * 0.9 for c in tint) + (1,)
    br.inputs["Mortar"].default_value = (0.25, 0.3, 0.4, 1)
    nt.links.new(tc.outputs["UV"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], e.inputs[0])
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def fog_volume(bounds_min, bounds_max, density=0.02, aniso=0.45, color=(0.85, 0.9, 1.0)):
    """room-filling haze so light shafts read"""
    c = [(a + b) / 2 for a, b in zip(bounds_min, bounds_max)]
    s = [b - a for a, b in zip(bounds_min, bounds_max)]
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    o = bpy.context.object
    o.name = "fog"
    o.scale = s
    m = bpy.data.materials.new("fog")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = aniso
    v.inputs["Color"].default_value = (*color, 1)
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def sun(name, direction_to, strength, color, angle_deg=0.6):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = strength
    d.color = color
    d.angle = math.radians(angle_deg)
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = Vector(direction_to).to_track_quat("-Z", "Y").to_euler()
    return o


def _night_city(y):
    """dark sky + far tower blocks with a few lit windows (gives depth through the blinds)"""
    box("sky", (30, 0.05, 14), (0, y + 8, 4), emit_mat("sky", (0.035, 0.05, 0.10), 1.0))
    import random
    rnd = random.Random(3)
    bm = mat("tower", (0.02, 0.022, 0.03), 0.8)
    win = emit_mat("citywin", (1.0, 0.72, 0.42), 2.5)
    winc = emit_mat("citywin_c", (0.75, 0.9, 1.0), 1.5)
    for k in range(7):
        x = -9 + k * 2.8 + rnd.uniform(-0.5, 0.5)
        hgt = rnd.uniform(5, 14)
        yy = y + rnd.uniform(0, 4)
        box(f"tower{k}", (2.2, 2, hgt), (x, yy, hgt / 2 - 3), bm)
        for j in range(18):
            if rnd.random() < 0.3:
                wx_ = x + rnd.uniform(-0.9, 0.9)
                wz_ = rnd.uniform(-2.5, hgt - 3.5)
                box(f"cw{k}_{j}", (0.25, 0.02, 0.18), (wx_, yy - 1.02, wz_), win if rnd.random() < 0.7 else winc)


def _no_shadow(prefixes):
    for o in bpy.data.objects:
        if o.name.startswith(prefixes):
            o.visible_shadow = False


def apartment_unit(fog=True, tube_on=True, moon=True, monitors=True, door_open=0.0):
    """One-room unit, 5 x 6.5 x 2.7 m. Character spot at origin facing -Y.
    Back wall (y=+2) has a window with blinds (moonlight shafts).
    Left wall (x=-2.5) has the entrance door; right side has the 4-PC desk."""
    W0, W1, Y0, Y1, HZ = -2.5, 2.5, -4.5, 2.0, 2.7
    wall = grime_wall()
    ceil = grime_wall("ceiling", (0.5, 0.5, 0.46), (0.28, 0.27, 0.23))
    floor = tile_floor()
    dark = mat("dark_metal", (0.05, 0.05, 0.055), 0.4, 0.6)
    wood = mat("door_wood", (0.20, 0.12, 0.07), 0.55)
    plastic = mat("pc_plastic", (0.035, 0.035, 0.04), 0.35)
    desk_m = mat("desk_top", (0.32, 0.26, 0.19), 0.42)
    t = 0.12
    box("floor", (W1 - W0, Y1 - Y0, 0.05), (0, (Y0 + Y1) / 2, -0.025), floor)
    box("ceiling", (W1 - W0, Y1 - Y0, 0.05), (0, (Y0 + Y1) / 2, HZ + 0.025), ceil)
    box("wall_front", (W1 - W0, t, HZ), (0, Y0 - t / 2, HZ / 2), wall)
    box("wall_R", (t, Y1 - Y0, HZ), (W1 + t / 2, (Y0 + Y1) / 2, HZ / 2), wall)
    # back wall with window opening x[-1.6,-0.2] z[0.9,2.2]
    wx0, wx1, wz0, wz1 = -1.6, -0.2, 0.9, 2.2
    box("wallB_l", (wx0 - W0, t, HZ), ((W0 + wx0) / 2, Y1 + t / 2, HZ / 2), wall)
    box("wallB_r", (W1 - wx1, t, HZ), ((wx1 + W1) / 2, Y1 + t / 2, HZ / 2), wall)
    box("wallB_b", (wx1 - wx0, t, wz0), ((wx0 + wx1) / 2, Y1 + t / 2, wz0 / 2), wall)
    box("wallB_t", (wx1 - wx0, t, HZ - wz1), ((wx0 + wx1) / 2, Y1 + t / 2, (wz1 + HZ) / 2), wall)
    # blinds: horizontal slats, slightly tilted, letting stripes through
    for i in range(16):
        z = wz0 + 0.04 + i * (wz1 - wz0) / 16
        box(f"slat{i}", (wx1 - wx0, 0.05, 0.005), ((wx0 + wx1) / 2, Y1 - 0.04, z),
            mat("slat", (0.55, 0.53, 0.48), 0.5) if i == 0 else bpy.data.materials["slat"],
            rot=(math.radians(-25), 0, 0))
    # night city outside: dim blue emissive backdrop far behind the window
    _night_city(Y1 + 6.0)
    _no_shadow(("sky", "tower", "cw"))
    # left wall with entrance door y[-1.0,0.0]
    dy0, dy1, dz = -1.0, 0.0, 2.1
    box("wallL_a", (t, dy0 - Y0, HZ), (W0 - t / 2, (Y0 + dy0) / 2, HZ / 2), wall)
    box("wallL_b", (t, Y1 - dy1, HZ), (W0 - t / 2, (dy1 + Y1) / 2, HZ / 2), wall)
    box("wallL_c", (t, dy1 - dy0, HZ - dz), (W0 - t / 2, (dy0 + dy1) / 2, (dz + HZ) / 2), wall)
    # door leaf hinged at y=dy0, opens outward into the corridor
    bpy.ops.object.empty_add(location=(W0 - t, dy0, 0))
    hinge = bpy.context.object
    hinge.name = "door_hinge"
    leaf = box("door", (0.045, dy1 - dy0 - 0.01, dz - 0.01), (W0 - t, (dy0 + dy1) / 2, dz / 2), wood)
    leaf.parent = hinge
    leaf.matrix_parent_inverse = hinge.matrix_world.inverted()
    hinge.rotation_euler.z = math.radians(-100 * door_open)
    knob = box("knob", (0.06, 0.06, 0.06), (W0 - t + 0.05, dy1 - 0.12, 1.0), dark)
    knob.parent = leaf
    knob.matrix_parent_inverse = leaf.matrix_world.inverted()
    # corridor beyond the door: near-black with a far flickering tube
    box("corr_floor", (3, 8, 0.05), (W0 - 1.6, -0.5, -0.025), floor)
    box("corr_wall", (0.1, 8, HZ), (W0 - 3.1, -0.5, HZ / 2), wall)
    box("corr_ceil", (3, 8, 0.05), (W0 - 1.6, -0.5, HZ + 0.025), ceil)
    corr = area_light("corridor_tube", (W0 - 1.6, 2.4, HZ - 0.05), (W0 - 1.6, 2.4, 0), 18, 0.15, (0.75, 1.0, 0.8))
    corr.data.shape = "RECTANGLE"; corr.data.size_y = 1.2
    # desk with four PCs on the right
    dxc, dyc = 1.45, 0.4
    box("desk", (1.1, 2.4, 0.04), (dxc, dyc, 0.74), desk_m)
    for lx in (-0.5, 0.5):
        for ly in (-1.15, 1.15):
            box("leg", (0.04, 0.04, 0.72), (dxc + lx, dyc + ly, 0.36), dark)
    scr = screen_mat()
    for i, yy in enumerate((-0.75, -0.25, 0.25, 0.75)):
        for side in (-1, 1):
            if side == 1 and i % 2:
                continue
        bx = dxc + 0.22
        mon = box(f"mon{i}", (0.03, 0.5, 0.32), (bx, dyc + yy * 1.2, 1.0), plastic,
                  rot=(0, 0, math.radians(8)))
        if monitors:
            sc_o = box(f"scr{i}", (0.005, 0.47, 0.29), (bx - 0.02, dyc + yy * 1.2, 1.0), scr,
                       rot=(0, 0, math.radians(8)))
        box(f"stand{i}", (0.03, 0.06, 0.12), (bx + 0.01, dyc + yy * 1.2, 0.81), plastic)
        box(f"kb{i}", (0.16, 0.42, 0.02), (dxc - 0.12, dyc + yy * 1.2, 0.77), plastic)
    # paper stacks (tax reports)
    paper = mat("paper", (0.78, 0.76, 0.70), 0.7)
    for k, (px, py, n) in enumerate([(1.2, -0.6, 9), (1.25, 1.4, 14), (1.15, 0.95, 6)]):
        box(f"papers{k}", (0.24, 0.32, 0.006 * n), (px, py, 0.76 + 0.003 * n), paper,
            rot=(0, 0, math.radians(7 * k - 5)))
    # ---------------- lights (all motivated by visible sources)
    lights = {}
    if moon:
        lights["moon"] = sun("moon", (0.18, -1.0, -0.80), 7.0, (0.52, 0.66, 1.0), 0.4)
    if tube_on:
        box("tube_fixture", (0.16, 1.25, 0.05), (0.2, -0.8, HZ - 0.03), dark)
        box("tube_glow", (0.05, 1.18, 0.02), (0.2, -0.8, HZ - 0.06), emit_mat("tube", (0.80, 1.0, 0.82), 4))
        tl = area_light("tube", (0.2, -0.8, HZ - 0.08), (0.2, -0.8, 0), 7, 0.1, (0.80, 1.0, 0.84))
        tl.data.shape = "RECTANGLE"; tl.data.size = 0.08; tl.data.size_y = 1.2
        lights["tube"] = tl
    if monitors:
        ml = area_light("monitor_glow", (dxc + 0.1, dyc - 0.3, 1.05), (0, 0, 1.45), 45, 0.45, (0.70, 0.83, 1.0))
        lights["monitor"] = ml
    # faint warm bounce from the pantry side so blacks are not dead
    lights["pantry"] = area_light("pantry", (-2.2, -2.5, 1.2), (0, 0, 1.0), 3, 1.0, (1.0, 0.62, 0.35))
    if fog:
        fog_volume((W0, Y0, 0), (W1, Y1, HZ), 0.012)
    world((0.004, 0.005, 0.009), 1.0)
    return lights


# ================================================================ hybrid avatars
def _drop_slots(mesh, slots):
    """delete every face that uses one of these material slots (and orphan verts)"""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in slots], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()


def load_hybrid(body, face, name="hero", loc=(0, 0, 0), rot_z=0.0, tone="sawo", neck_cut=None):
    """Body, clothes and skeleton from `body`; head (face + hair + lashes) from `face`.
    Rocketbox avatars share one skeleton and neck position, so the head mesh can be
    re-skinned onto the other avatar's armature. neck_cut: delete body faces whose
    verts are all above this z (hides the old neck inside the new head)."""
    arm, mesh = load_avatar(body, name, loc, rot_z, tone=tone)
    arm_f, mesh_f = load_avatar(face, name + "_f", loc, rot_z, tone=tone)
    arm_f.location = arm.location
    bpy.context.view_layer.update()
    _drop_slots(mesh, {1, 2})          # remove the body avatar's own head + hair
    _drop_slots(mesh_f, {0})           # keep only face head + hair/lashes
    if neck_cut is not None:
        import bmesh
        bm = bmesh.new(); bm.from_mesh(mesh.data); bm.faces.ensure_lookup_table()
        mw = mesh.matrix_world
        dead = [f for f in bm.faces if all((mw @ v.co).z > neck_cut for v in f.verts) and f.material_index == 0]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(mesh.data); bm.free()
    for m in mesh_f.modifiers:
        if m.type == "ARMATURE":
            m.object = arm
    mesh_f.parent = arm
    mesh_f.matrix_parent_inverse = mesh.matrix_parent_inverse.copy()
    bpy.ops.object.select_all(action="DESELECT")
    mesh_f.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    bpy.data.objects.remove(arm_f)
    bpy.context.view_layer.update()
    return arm, mesh
