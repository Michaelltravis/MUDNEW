"""Snakes and serpents: a long body laid in an S on the ground, the head raised on its neck, a
forked tongue. Variants:
  snake    every snake, viper and adder; pale scales with darker diamonds, tinted by bestiary.js
  serpent  the great serpents (naga, hydra, sea serpents, lamia): thicker, a flared hood, horns
    tools/art3d/blender/run.sh models/snake.py --preview [--variant serpent]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'snake'
S = V == 'serpent'
pal = Palette(V, {
    'scale': ['#e2dccb', '#b4ab96', '#f0ead8'], 'diamond': '#5a5040', 'eye': '#f0d040', 'pupil': '#141010',
    'tongue': '#c83040', 'hood': ['#d8cfba', '#a49a84', '#6e6656'], 'horn': '#3a3430',
})
g = 1.5 if S else 1.0                      # girth

sk = Skel(V)
N = 9
pts = []
for i in range(N):
    t = i / (N - 1)
    pts.append(((0.16 * math.sin(i * 0.95)) * (1 - 0.3 * t), -0.12 + 0.17 * i, 0.075 * g * (1 - 0.6 * t) + 0.01, (0.08 - 0.06 * t) * g))
sk.node('seg0', pts[0][:3], pts[0][3])
for i in range(1, N):
    sk.node(f'seg{i}', pts[i][:3], pts[i][3], f'seg{i - 1}')
sk.node('neck', (0, -0.3, 0.17 * g), 0.068 * g, 'seg0')
sk.node('head', (0, -0.44, 0.3 * g), 0.075 * g, 'neck', sx=1.25)
sk.node('snout', (0, -0.56, 0.29 * g), 0.04 * g, 'head', sx=1.2)

body = sk.hull(subdiv=1, branch_smoothing=0.6)
pal.paint_ramp(body, 'scale')
arm = sk.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

# a row of dark diamonds down the back
for i in range(1, N - 1):
    x, y, z, r = pts[i]
    add(part('cube', f'diamond{i}', (x, y, z + r * 0.92), (r * 0.45, r * 0.45, 0.012), rot=(0, 0, math.radians(45)), segments=4), 'diamond', f'seg{i}')
for side, x in (('L', 1), ('R', -1)):
    add(part('sphere', f'eye.{side}', (0.055 * g * x, -0.47, 0.33 * g), 0.02 * g, segments=6), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.062 * g * x, -0.48, 0.33 * g), 0.011 * g, segments=6), 'pupil', 'head')
    add(part('cone', f'tongue.{side}', (0.012 * x, -0.64, 0.27 * g), (0.008, 0.035, 0.008), rot=(math.radians(90), 0, math.radians(14 * x)), segments=3), 'tongue', 'snout')
    if S:
        add(part('cone', f'horn.{side}', (0.05 * g * x, -0.4, 0.4 * g), (0.022, 0.022, 0.08), rot=(math.radians(-50), math.radians(15 * x), 0), segments=4), 'horn', 'head')
if S:
    # the hood: a flared fan of skin behind the head
    c = (0, -0.3, 0.27 * g)
    fan = [c] + [(0.2 * g * math.sin(a), -0.3 + 0.05 * math.cos(a), 0.27 * g + 0.14 * g * math.cos(a)) for a in [math.radians(d) for d in range(-100, 101, 25)]]
    add(poly('hood', fan, [(0, i, i + 1) for i in range(1, len(fan) - 1)], 0.02), 'hood', 'neck')

body = finish_body(body, arm, parts, budget=2600)

CHAIN = [f'seg{i}' for i in range(1, N)]
c = Clips(arm)
with c.clip('Idle', 48, loop=True) as k:
    k.rot('neck', 12, z=10).rot('neck', 36, z=-10).rot('head', 24, x=-8)
    gaits.slither(k, 48, CHAIN, amp=4)
with c.clip('Walk', 28, loop=True) as k:
    gaits.slither(k, 28, CHAIN, amp=20)
    k.rot('neck', 7, z=8).rot('neck', 21, z=-8)
with c.clip('Run', 16, loop=True) as k:
    gaits.slither(k, 16, CHAIN, amp=28)
with c.clip('Bite_Front', 18) as k:
    # coil back, then strike
    k.rot('neck', 6, x=-35).rot('head', 6, x=15).rot('neck', 10, x=40).rot('head', 10, x=-10).rot('neck', 18).rot('head', 18)
    k.loc('seg0', 10, z=-0.08)
with c.clip('Bite_InPlace', 28) as k:
    # rear up and hiss, the hood spread
    k.rot('neck', 10, x=-45).rot('head', 10, x=25).rot('neck', 22, x=-48).rot('neck', 28).rot('head', 28)
with c.clip('HitRecieve', 12) as k:
    k.rot('neck', 3, x=-25, z=15).rot('head', 3, x=-10)
with c.clip('Death', 36) as k:
    # the head drops, the body goes limp and rolls over, belly up
    k.rot('neck', 12, x=50).rot('head', 12, x=10)
    k.rot('seg0', 36, y=150).rot('neck', 36, x=55)
    for i, b in enumerate(CHAIN):
        k.turn(b, 36, (0, 0, 1), 8 * math.sin(i))

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names,
           meta={'for': 'serpents, nagas, hydras; tinted by bestiary.js' if S else 'snakes; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 7), ('Bite_Front', 10), ('Bite_InPlace', 14), ('Death', 999)))
