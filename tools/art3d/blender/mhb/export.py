"""Export one model: its armature and skinned mesh as a .glb (Y-up, every clip), and a sidecar
.json the build reads (kind, the clips, triangles, height)."""
import json
import os

import bpy

from .body import tris
from .clips import REQUIRED
from .scene import select_only


# triangles a model may have (docs/art/STYLE3D.md); tools/art3d/qc_models.mjs holds the same
BUDGET = {'creature': 3000, 'boss': 8000, 'prop': 1500, 'steed': 3000}


def export(arm, body, name, out, kind='creature', clips=(), meta=None):
    missing = [c for c in REQUIRED if c not in clips]
    if missing:
        raise SystemExit(f'{name}: missing clips {missing}')
    if tris(body) > BUDGET.get(kind, 3000):
        raise SystemExit(f'{name}: {tris(body)} triangles, over the {kind} budget of {BUDGET.get(kind, 3000)}')
    pts = [arm.matrix_world @ v.co for v in body.data.vertices]
    lo_z = min(p.z for p in pts)
    if abs(lo_z) > 0.005:
        # something hangs below the feet (a drooping tail, a claw), or it floats (a fish): set the
        # whole rig down on the ground
        arm.location.z -= lo_z
        bpy.context.view_layer.update()
        print(f'{name}: moved {-lo_z:+.3f} so it rests on the ground')
        pts = [arm.matrix_world @ v.co for v in body.data.vertices]
        lo_z = min(p.z for p in pts)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    span = max(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts))
    if abs(lo_z) > 0.03:
        raise SystemExit(f'{name}: its feet are at {lo_z:.3f}, not on the ground (0)')
    if abs(cx) > span * 0.25 or abs(cy) > span * 0.35:
        raise SystemExit(f'{name}: not centred on its origin ({cx:.2f}, {cy:.2f})')
    path = os.path.join(out, f'{name}.glb')
    for o in bpy.context.view_layer.objects:
        o.hide_set(False)
    select_only(body, arm, active=arm)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True, export_yup=True,
        export_apply=False, export_texcoords=True, export_normals=True, export_materials='EXPORT',
        export_skins=True, export_def_bones=False, export_animations=True,
        export_animation_mode='NLA_TRACKS', export_nla_strips=True, export_force_sampling=True,
        export_frame_step=1, export_optimize_animation_size=True, export_anim_single_armature=True,
        export_reset_pose_bones=True, export_image_format='AUTO', export_lights=False, export_cameras=False)
    h = max((arm.matrix_world @ v.co).z for v in body.data.vertices) if body.data.vertices else 0
    meta = dict(meta or {})
    if meta.get('ref') == 'length':
        # a long, low creature (a crocodile) is sized by the game by its length, not its height
        meta['ref'] = round(max(p.y for p in pts) - min(p.y for p in pts), 3)
    side = {'name': name, 'kind': kind, 'clips': list(clips), 'tris': tris(body), 'height': round(h, 3), **meta}
    with open(os.path.join(out, f'{name}.json'), 'w') as f:
        json.dump(side, f, indent=1)
    print(f'exported {path}: {side["tris"]} tris, clips {", ".join(clips)}')
    return path
