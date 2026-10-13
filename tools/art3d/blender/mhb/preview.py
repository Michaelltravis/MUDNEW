"""Look at a model before it goes in the game: a turntable (front, side, back, three-quarter) over
a row of poses (a frame from each clip), rendered with Cycles on the CPU into one PNG,
out/<name>_preview.png. The game's own gallery pages are the final word; this is the quick look."""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

from .scene import link

POSES = (('Idle', 0), ('Walk', 6), ('Bite_Front', 8), ('HitRecieve', 4), ('Death', 999))


def _setup(size, samples):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    s.cycles.use_denoising = False
    s.render.resolution_x = s.render.resolution_y = size
    s.render.film_transparent = False
    s.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('preview') if not s.world else s.world
    s.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.42, 0.47, 0.55, 1)
    bg.inputs['Strength'].default_value = 0.9
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 3.2
    so = link(bpy.data.objects.new('sun', sun))
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    floor = bpy.data.meshes.new('floor')
    floor.from_pydata([(-20, -20, 0), (20, -20, 0), (20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
    fo = link(bpy.data.objects.new('floor', floor))
    fm = bpy.data.materials.new('floor')
    fm.use_nodes = True
    fm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0.36, 0.34, 0.3, 1)
    floor.materials.append(fm)
    return s, [so, fo]


def _bounds(body):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def _camera(target, dist, yaw, elev):
    cam = bpy.data.cameras.new('cam')
    cam.lens = 50
    co = link(bpy.data.objects.new('cam', cam))
    a, e = math.radians(yaw), math.radians(elev)
    co.location = target + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    d = target - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = co
    return co


def _rest(arm):
    """No clip playing, every bone at rest (the exporter leaves its last track applied)."""
    ad = arm.animation_data
    if ad:
        ad.action = None
        for t in ad.nla_tracks:
            t.mute = True
            t.is_solo = False
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)


def _pose(arm, clip, frame):
    _rest(arm)
    tr = arm.animation_data.nla_tracks.get(clip) if arm.animation_data else None
    act = tr.strips[0].action if tr and tr.strips else bpy.data.actions.get(clip)
    arm.animation_data.action = act
    end = int(act.frame_range[1]) if act else 0
    bpy.context.scene.frame_set(min(frame, end))


def preview(arm, body, name, out, size=300, samples=12, poses=POSES):
    s, made = _setup(size, samples)
    lo, hi = _bounds(body)
    h = max(0.3, hi.z - lo.z)
    span = max(hi.x - lo.x, hi.y - lo.y, h)
    target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, h * 0.5))
    dist = span * 2.6
    tiles = []
    tmp = os.path.join(out, f'.{name}_tile.png')

    def shot():
        s.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(tmp, check_existing=False)
        a = np.array(img.pixels[:], dtype=np.float32).reshape(size, size, 4)
        bpy.data.images.remove(img)
        tiles.append(a)

    _rest(arm)
    for yaw in (0, 90, 180, 35):
        c = _camera(target, dist, yaw, 14)
        shot()
        bpy.data.objects.remove(c)
    row1, tiles = tiles, []
    for clip, frame in poses:
        if not arm.animation_data or not (arm.animation_data.nla_tracks.get(clip) or bpy.data.actions.get(clip)):
            continue
        _pose(arm, clip, frame)
        c = _camera(target, dist, 35, 14)
        shot()
        bpy.data.objects.remove(c)
    row2 = tiles
    _rest(arm)
    n = max(len(row1), len(row2))
    blank = np.full((size, size, 4), 0.45, dtype=np.float32)
    blank[..., 3] = 1
    rows = [np.concatenate(r + [blank] * (n - len(r)), axis=1) for r in (row2, row1) if r]   # bottom-up
    grid = np.concatenate(rows, axis=0)
    img = bpy.data.images.new(f'{name}_preview', grid.shape[1], grid.shape[0])
    img.pixels = grid.ravel()
    path = os.path.join(out, f'{name}_preview.png')
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    os.remove(tmp) if os.path.exists(tmp) else None
    for o in made:
        bpy.data.objects.remove(o)
    print(f'preview {path}')
    return path
