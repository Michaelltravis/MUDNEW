"""A body from a skeleton graph. Each node is a point with a radius; each node but the root hangs
from a parent. The Skin modifier wraps the graph in a hull (smoothed by a subdivision), and the same
graph becomes the armature: one bone per node, from its parent's point to its own, named after the
node. The hull is weighted to the bones automatically; small parts (eyes, horns, claws, a crest)
are made separately and pinned rigidly to one bone, then joined, so the model is one skinned mesh.

Blender is Z-up; model facing -Y (the exporter turns that into the game's +Z forward, Y up).
"""
import bmesh
import bpy
from mathutils import Vector

from .scene import link, select_only


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


class Skel:
    def __init__(self, name):
        self.name = name
        self.nodes = []          # {name, co, r, parent, sx}

    def node(self, name, co, r, parent=None, sx=1.0):
        """A point of the body, `r` its radius (sx widens it sideways: a chest broader than deep)."""
        if any(n['name'] == name for n in self.nodes):
            raise ValueError(f'node {name} twice')
        p = None if parent is None else self.index(parent)
        self.nodes.append({'name': name, 'co': Vector(co), 'r': r, 'parent': p, 'sx': sx})
        return name

    def chain(self, prefix, parent, points):
        """Nodes one after another: [(co, r), ...] named prefix0, prefix1, ..."""
        last = parent
        for i, (co, r) in enumerate(points):
            last = self.node(f'{prefix}{i}', co, r, last)
        return last

    def mirror(self, name, co, r, parent, sx=1.0):
        """A node and its mirror across X: name.L at +x, name.R at -x (parents mirrored too)."""
        x, y, z = co
        pl = parent if parent is None or not parent.endswith(('.L', '.R')) else parent[:-2] + '.L'
        pr = parent if parent is None or not parent.endswith(('.L', '.R')) else parent[:-2] + '.R'
        self.node(f'{name}.L', (abs(x), y, z), r, pl, sx)
        self.node(f'{name}.R', (-abs(x), y, z), r, pr, sx)
        return f'{name}.L', f'{name}.R'

    def index(self, name):
        for i, n in enumerate(self.nodes):
            if n['name'] == name:
                return i
        raise KeyError(name)

    def co(self, name):
        return self.nodes[self.index(name)]['co']

    # ---- the hull ----
    def hull(self, subdiv=1, smooth=True, branch_smoothing=0.25):
        # the skin modifier ends a limb flat at its last point: carry each tip on past it, narrowing,
        # so heads, paws and tails end round (these points are hull only, not bones)
        pts = [(tuple(n['co']), n['r'], n['sx']) for n in self.nodes]
        edges = [(n['parent'], i) for i, n in enumerate(self.nodes) if n['parent'] is not None]
        has_child = {n['parent'] for n in self.nodes if n['parent'] is not None}
        for i, n in enumerate(self.nodes):
            if i in has_child or n['parent'] is None:
                continue
            d = n['co'] - self.nodes[n['parent']]['co']
            if d.length < 1e-6:
                continue
            d.normalize()
            for k, (f, rr) in enumerate(((0.55, 0.8), (0.9, 0.45))):
                pts.append((tuple(n['co'] + d * n['r'] * f), n['r'] * rr, n['sx']))
                edges.append((i if k == 0 else len(pts) - 2, len(pts) - 1))
        me = bpy.data.meshes.new(f'{self.name}_body')
        me.from_pydata([p[0] for p in pts], edges, [])
        obj = link(bpy.data.objects.new(f'{self.name}', me))
        sk = obj.modifiers.new('Skin', 'SKIN')
        sk.branch_smoothing = branch_smoothing
        sk.use_smooth_shade = smooth
        for i, (co, r, sx) in enumerate(pts):
            sv = me.skin_vertices[0].data[i]
            sv.radius = (r * sx, r)
            sv.use_root = i < len(self.nodes) and self.nodes[i]['parent'] is None
        if subdiv:
            ss = obj.modifiers.new('Subsurf', 'SUBSURF')
            ss.levels = subdiv
            ss.render_levels = subdiv
        select_only(obj)
        for m in list(obj.modifiers):
            with bpy.context.temp_override(object=obj, active_object=obj):
                bpy.ops.object.modifier_apply(modifier=m.name)
        if smooth:
            for p in obj.data.polygons:
                p.use_smooth = True
        return obj

    # ---- the armature ----
    def armature(self):
        ad = bpy.data.armatures.new(f'{self.name}_rig')
        arm = link(bpy.data.objects.new(f'{self.name}_rig', ad))
        select_only(arm)
        bpy.ops.object.mode_set(mode='EDIT')
        eb = ad.edit_bones
        made = {}
        for n in self.nodes:
            b = eb.new(n['name'])
            if n['parent'] is None:
                b.head = n['co'] - Vector((0, 0.0, 0.12))       # the root bone: a short stub under it
                b.tail = n['co']
            else:
                b.head = self.nodes[n['parent']]['co']
                b.tail = n['co']
                if (b.tail - b.head).length < 1e-4:
                    b.tail = b.head + Vector((0, 0, 0.02))
            made[n['name']] = b
        for n in self.nodes:
            if n['parent'] is not None:
                made[n['name']].parent = made[self.nodes[n['parent']]['name']]
                made[n['name']].use_connect = False
        bpy.ops.object.mode_set(mode='OBJECT')
        for pb in arm.pose.bones:
            pb.rotation_mode = 'XYZ'
        return arm


def part(kind, name, at, size, rot=(0, 0, 0), segments=8):
    """A small rigid part: 'sphere', 'cone', 'cube', 'cyl' or 'ico' at `at`, scaled by `size`
    (a number or (x, y, z)), rotated by `rot` (radians)."""
    sz = size if isinstance(size, (tuple, list)) else (size, size, size)
    if kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(4, segments // 2), radius=1, location=at, rotation=rot)
    elif kind == 'ico':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=at, rotation=rot)
    elif kind == 'cone':
        bpy.ops.mesh.primitive_cone_add(vertices=segments, radius1=1, radius2=0, depth=2, location=at, rotation=rot)
    elif kind == 'cyl':
        bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=1, depth=2, location=at, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2, location=at, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = sz
    select_only(o)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return o


def poly(name, verts, faces, thickness=0.0):
    """A part from its own points and faces (a wing's membrane, a fin, a frill), given a little
    thickness so it shows from both sides."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    o = link(bpy.data.objects.new(name, me))
    if thickness:
        m = o.modifiers.new('Solidify', 'SOLIDIFY')
        m.thickness = thickness
        m.offset = 0
        select_only(o)
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_apply(modifier=m.name)
    return o


def _pin(obj, bone):
    vg = obj.vertex_groups.new(name=bone)
    vg.add([v.index for v in obj.data.vertices], 1.0, 'REPLACE')


def finish_body(body, arm, parts=(), budget=3000, flat_parts=True):
    """Weight the hull to the armature, pin each (part, bone, palette-painted) to its bone, join
    them into one skinned mesh parented to the armature, decimating the hull to stay in budget."""
    part_tris = sum(tris(p) for p, _ in parts)
    room = max(400, budget - part_tris)
    if tris(body) > room:
        d = body.modifiers.new('Decimate', 'DECIMATE')
        d.ratio = room / tris(body)
        select_only(body)
        with bpy.context.temp_override(object=body, active_object=body):
            bpy.ops.object.modifier_apply(modifier=d.name)
    # weights: bone heat, falling back to envelopes if it cannot solve
    select_only(body, arm, active=arm)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    weighted = set()
    for v in body.data.vertices:
        if any(g.weight > 0.01 for g in v.groups):
            weighted.add(v.index)
    if len(weighted) < len(body.data.vertices) * 0.98:
        body.vertex_groups.clear()
        select_only(body, arm, active=arm)
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
    for p, bone in parts:
        if flat_parts:
            for f in p.data.polygons:
                f.use_smooth = False
        _pin(p, bone)
    if parts:
        select_only(body, *[p for p, _ in parts], active=body)
        bpy.ops.object.join()
    # one modifier, the armature's
    mods = [m for m in body.modifiers if m.type == 'ARMATURE']
    for m in body.modifiers:
        if m.type != 'ARMATURE':
            body.modifiers.remove(m)
    if not mods:
        m = body.modifiers.new('Armature', 'ARMATURE')
        m.object = arm
    body.parent = arm
    _clean(body)
    return body


def _clean(obj):
    """Merge doubles left by joining, keep normals pointing out."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
