import os
import sys
import bpy

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'out'))


def reset():
    """An empty scene in metres, 30 frames a second."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.render.fps = 30
    return s


def args():
    """The script's own options: --preview (render turntable PNGs), --out DIR, --variant NAME."""
    argv = sys.argv[1:]
    out = OUT
    if '--out' in argv:
        out = argv[argv.index('--out') + 1]
    os.makedirs(out, exist_ok=True)
    variant = argv[argv.index('--variant') + 1] if '--variant' in argv else None
    return {'preview': '--preview' in argv, 'out': out, 'variant': variant}


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def select_only(*objs, active=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[-1]
