"""The restless and the elemental. Variants:
  ghost      a hooded wraith in a ragged shroud that trails away to a wisp, long arms reaching,
             hollow glowing eyes; pale and half see-through, so tints make shades and banshees
  elemental  a hulking torso of living element on a whirling column, great fists, a crown of
             spikes; tinted fire, water, ice, air or earth by bestiary.js, glowing a little
    tools/art3d/blender/run.sh models/ghost.py --preview [--variant elemental]
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'ghost'
E = V == 'elemental'
pal = Palette(V, {
    'shroud': ['#ffffff', '#dfe6f2', '#aab6c8'], 'inner': ['#4a5468', '#2a3040', '#14182a'],
    'eye': '#f4ffff', 'rag': ['#e8eef8', '#c4cede', '#98a6bc'],
    'core': ['#ffffff', '#e8e8e8', '#b0b0b0'], 'rock': ['#d8d8d8', '#a8a8a8', '#787878'],
})

s = Skel(V)
if not E:
    s.node('base', (0, 0.02, 0.62), 0.24)
    s.node('chest', (0, 0, 0.92), 0.27, 'base', sx=1.15)
    s.node('head', (0, -0.03, 1.24), 0.17, 'chest')
    s.node('tail0', (0, 0.08, 0.38), 0.19, 'base')
    s.node('tail1', (0, 0.18, 0.18), 0.11, 'tail0')
    s.node('tail2', (0, 0.3, 0.04), 0.045, 'tail1')
    for side, x in (('L', 1), ('R', -1)):
        s.node(f'arm0.{side}', (0.27 * x, 0, 1.02), 0.09, 'chest')
        s.node(f'arm1.{side}', (0.42 * x, -0.12, 0.8), 0.07, f'arm0.{side}')
        s.node(f'arm2.{side}', (0.46 * x, -0.28, 0.66), 0.045, f'arm1.{side}')
else:
    s.node('base', (0, 0, 0.45), 0.2)
    s.node('chest', (0, 0, 1.05), 0.42, 'base', sx=1.2)
    s.node('head', (0, -0.08, 1.52), 0.2, 'chest')
    s.node('tail0', (0, 0.0, 0.22), 0.14, 'base')
    s.node('tail1', (0, 0.02, 0.04), 0.08, 'tail0')
    for side, x in (('L', 1), ('R', -1)):
        s.node(f'arm0.{side}', (0.48 * x, 0, 1.28), 0.17, 'chest')
        s.node(f'arm1.{side}', (0.68 * x, -0.06, 0.98), 0.1, f'arm0.{side}')
        s.node(f'arm2.{side}', (0.74 * x, -0.18, 0.66), 0.21, f'arm1.{side}')

body = s.hull(subdiv=1, branch_smoothing=0.5, smooth=not E)      # an elemental is faceted, like rough stone or ice
pal.paint_ramp(body, 'core' if E else 'shroud')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

if not E:
    # the hood, its dark hollow, and two cold eyes in it
    add(part('sphere', 'hood', (0, 0.0, 1.27), (0.2, 0.21, 0.22), segments=10), 'shroud', 'head')
    add(part('sphere', 'hollow', (0, -0.14, 1.23), (0.13, 0.08, 0.14), segments=8), 'inner', 'head')
    for side, x in (('L', 1), ('R', -1)):
        add(part('sphere', f'eye.{side}', (0.05 * x, -0.2, 1.25), 0.026, segments=6), 'eye', 'head')
        # ragged sleeves hanging from the forearms
        for j in range(2):
            add(part('cone', f'sleeve{j}.{side}', ((0.4 + 0.05 * j) * x, -0.14 - 0.06 * j, 0.68), (0.05, 0.05, 0.12), rot=(math.radians(180), 0, 0), segments=4), 'rag', f'arm1.{side}')
    # tatters round the hem
    for i in range(7):
        a = 2 * math.pi * i / 7
        add(part('cone', f'tatter{i}', (0.2 * math.sin(a), 0.08 + 0.2 * math.cos(a), 0.36), (0.06, 0.06, 0.16), rot=(math.radians(180 + 18 * math.cos(a)), math.radians(18 * math.sin(a)), 0), segments=4), 'rag', 'tail0')
else:
    for i in range(5):
        a = math.radians(-60 + 30 * i)
        add(part('cone', f'spike{i}', (0.15 * math.sin(a), -0.04, 1.68 - 0.04 * abs(i - 2)), (0.05, 0.05, 0.16 - 0.03 * abs(i - 2)), rot=(0, a * 0.7, 0), segments=4), 'rock', 'head')
    for side, x in (('L', 1), ('R', -1)):
        add(part('sphere', f'eye.{side}', (0.08 * x, -0.25, 1.55), 0.035, segments=6), 'eye', 'head')
        for j in range(3):
            add(part('cone', f'shard{j}.{side}', ((0.5 + 0.06 * j) * x, 0.08 - 0.06 * j, 1.42 + 0.06 * j), (0.07, 0.07, 0.2 - 0.04 * j),
                     rot=(math.radians(-15 + 15 * j), math.radians(35 * x), 0), segments=4), 'rock', f'arm0.{side}')
        add(part('ico', f'knuckle.{side}', (0.76 * x, -0.3, 0.68), 0.09), 'rock', f'arm2.{side}')
    for i, (x, y, z, r) in enumerate(((0.0, 0.32, 1.25, 0.2), (0.18, 0.3, 1.0, 0.15), (-0.18, 0.3, 1.0, 0.15), (0.0, 0.28, 1.45, 0.14))):
        add(part('cone', f'back{i}', (x, y, z), (0.08, 0.08, r), rot=(math.radians(-70), 0, 0), segments=4), 'rock', 'chest')
    for i in range(5):
        a = 2 * math.pi * i / 5
        add(part('ico', f'orbit{i}', (0.32 * math.sin(a), 0.32 * math.cos(a), 0.35 + 0.08 * (i % 2)), 0.08), 'rock', 'base')

body = finish_body(body, arm, parts, budget=2800)

c = Clips(arm)
ARMS = [f'arm1.{s_}' for s_ in ('L', 'R')]
with c.clip('Idle', 56, loop=True) as k:
    gaits.float_(k, 56, 'base', bob=0.05, sway=['tail0', 'tail1'] + (['tail2'] if not E else []), amp=8)
    for side, sgn in (('L', 1), ('R', -1)):
        k.rot(f'arm0.{side}', 14, z=6 * sgn).rot(f'arm0.{side}', 42, z=-4 * sgn)
with c.clip('Walk', 40, loop=True) as k:
    gaits.float_(k, 40, 'base', bob=0.04, sway=['tail0', 'tail1'] + (['tail2'] if not E else []), amp=14)
    k.rot('chest', 20, x=8)
    for side in ('L', 'R'):
        k.rot(f'arm0.{side}', 20, x=-15)
with c.clip('Bite_Front', 22) as k:
    # draw back, then lunge with both arms (a ghost's chill touch, an elemental's double blow)
    k.rot('chest', 7, x=-15).loc('base', 7, z=0.05)
    for side, sgn in (('L', 1), ('R', -1)):
        k.rot(f'arm0.{side}', 7, x=-70, z=10 * sgn).rot(f'arm0.{side}', 12, x=25, z=0)
    k.rot('chest', 12, x=18).loc('base', 12, z=-0.12)
    k.rot('chest', 22).loc('base', 22)
    for side in ('L', 'R'):
        k.rot(f'arm0.{side}', 22)
with c.clip('Bite_InPlace', 30) as k:
    # a wail, arms flung wide
    k.rot('head', 10, x=-25).rot('chest', 10, x=-10)
    for side, sgn in (('L', 1), ('R', -1)):
        k.rot(f'arm0.{side}', 10, y=40 * sgn, x=-30)
    k.rot('head', 22, x=-28).rot('head', 30).rot('chest', 30)
    for side in ('L', 'R'):
        k.rot(f'arm0.{side}', 30)
with c.clip('HitRecieve', 12) as k:
    k.rot('chest', 3, x=-18, z=8).loc('base', 3, z=0.06)
with c.clip('Death', 40) as k:
    # it sinks, folds and collapses into a heap on the ground
    k.rot('chest', 12, x=25).loc('base', 12, y=-0.1)
    k.rot('base', 40, x=-80).loc('base', 40, y=-0.45).rot('chest', 40, x=30).rot('head', 40, x=20)
    for side in ('L', 'R'):
        k.rot(f'arm0.{side}', 40, x=40)

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names,
           meta={'for': 'elementals; tinted by bestiary.js' if E else 'ghosts, wraiths, shades; tinted by bestiary.js',
                 'look': {'opacity': 0.9, 'glow': 0.35} if E else {'opacity': 0.72, 'glow': 0.15}})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 10), ('Bite_Front', 12), ('Bite_InPlace', 14), ('Death', 999)))
