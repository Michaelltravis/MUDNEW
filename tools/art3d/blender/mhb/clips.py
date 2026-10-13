"""Clips keyed bone by bone. Each clip is its own action, named as the game's creature registry
(world3d/assets.js aliasFor) reads them: Idle, Walk, Run, Bite_Front (an attack), Bite_InPlace
(a roar, a breath, a cast), Jump, HitRecieve (sic, the Quaternius name) and Death.

    c = Clips(arm)
    with c.clip('Walk', frames=24, loop=True) as k:
        k.rot('thigh.L', 0, x=25); k.rot('thigh.L', 12, x=-25)
        k.loc('root', 6, z=0.03)

Rotations are in degrees about the bone's own axes (a bone runs along its local Y; X swings it
forward and back). A looping clip's last frame is its first, so it repeats without a hitch.
"""
import math
from contextlib import contextmanager

import bpy

REQUIRED = ('Idle', 'Walk', 'Bite_Front', 'HitRecieve', 'Death')


class _Keys:
    def __init__(self, arm, frames):
        self.arm = arm
        self.frames = frames
        self.keyed = {}          # (bone, path) -> {frame: value}
        self.world = {}          # (frame, bone) -> its aimed rotation (aim)

    def _put(self, bone, path, frame, values):
        d = self.keyed.setdefault((bone, path), {})
        d[frame] = values

    def rot(self, bone, frame, x=0.0, y=0.0, z=0.0):
        self._put(bone, 'rotation_euler', frame, (math.radians(x), math.radians(y), math.radians(z)))
        return self

    def aim(self, bone, frame, to):
        """Point a bone along `to` (a direction in the body's own rest frame: -Y forward, +Z up),
        whatever its own axes are: "the wing laid back along the flank" instead of guessed angles.
        A bone whose parent was aimed in the same frame follows from the parent's new pose."""
        from mathutils import Quaternion, Vector
        b = self.arm.data.bones[bone]
        rest = b.matrix_local.to_quaternion()
        d0 = (b.tail_local - b.head_local).normalized()
        total = d0.rotation_difference(Vector(to).normalized())
        qp = self.world.get((frame, b.parent.name)) if b.parent else None
        qp = qp if qp is not None else Quaternion()
        local = rest.inverted() @ qp.inverted() @ total @ rest
        self.world[(frame, bone)] = total
        self._put(bone, 'rotation_euler', frame, tuple(local.to_euler('XYZ')))
        return self

    def turn(self, bone, frame, axis, deg):
        """Turn a bone `deg` degrees about an axis of the body's rest frame (-Y forward, +Z up),
        on top of any turn already given it (or its parent) in this frame: a spider's leg swung
        about the vertical, then lifted, whichever way the leg itself points."""
        import math as _m
        from mathutils import Quaternion, Vector
        b = self.arm.data.bones[bone]
        rest = b.matrix_local.to_quaternion()
        qp = self.world.get((frame, b.parent.name)) if b.parent else None
        qp = qp if qp is not None else Quaternion()
        prev = self.world.get((frame, bone), qp)
        total = Quaternion(Vector(axis).normalized(), _m.radians(deg)) @ prev
        self.world[(frame, bone)] = total
        local = rest.inverted() @ qp.inverted() @ total @ rest
        self._put(bone, 'rotation_euler', frame, tuple(local.to_euler('XYZ')))
        return self

    def loc(self, bone, frame, x=0.0, y=0.0, z=0.0):
        self._put(bone, 'location', frame, (x, y, z))
        return self

    def scale(self, bone, frame, s=1.0):
        sv = s if isinstance(s, (tuple, list)) else (s, s, s)
        self._put(bone, 'scale', frame, tuple(sv))
        return self


class Clips:
    def __init__(self, arm):
        self.arm = arm
        self.names = []
        if not arm.animation_data:
            arm.animation_data_create()

    @contextmanager
    def clip(self, name, frames=24, loop=False):
        k = _Keys(self.arm, frames)
        yield k
        self._write(name, k, frames, loop)

    def _write(self, name, k, frames, loop):
        arm = self.arm
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        arm.animation_data.action = act
        rest = {'rotation_euler': (0.0, 0.0, 0.0), 'location': (0.0, 0.0, 0.0), 'scale': (1.0, 1.0, 1.0)}
        for (bone, path), keys in k.keyed.items():
            pb = arm.pose.bones.get(bone)
            if pb is None:
                raise KeyError(f'{name}: no bone {bone}')
            keys = dict(keys)
            if 0 not in keys:
                keys[0] = rest[path]
            if loop:
                keys[frames] = keys[0]
            for f in sorted(keys):
                setattr(pb, path, keys[f])
                pb.keyframe_insert(data_path=path, frame=f, group=bone)
            setattr(pb, path, rest[path])
        for fc in act.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'AUTO'
        act.frame_range = (0, frames)
        act.use_frame_range = True
        # each clip on its own muted NLA track, so the exporter writes every one
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 0, act)
        tr.mute = True
        arm.animation_data.action = None
        self.names.append(name)
        return act

    def missing(self):
        return [n for n in REQUIRED if n not in self.names]
