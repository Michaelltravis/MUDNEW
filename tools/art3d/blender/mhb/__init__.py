"""mhb: Misthollow's Blender helpers. Model scripts (../models/*.py) build one model each, headless:
a skeleton graph with radii becomes a skin-modifier body, an armature is built from the same graph,
the body is weighted to it, extra parts are pinned to bones, colours come from one small palette
texture, clips are keyed by bone, and the whole is exported as one skinned .glb (glTF Y-up, facing
+Z in the game; model it facing -Y in Blender). See docs/art/STYLE3D.md for the rules it must keep.
"""
from .scene import reset, args, OUT
from .palette import Palette
from .body import Skel, part, poly, finish_body, tris
from .clips import Clips
from .export import export
from .preview import preview
