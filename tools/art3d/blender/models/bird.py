"""Birds: a round body, a short neck, a beak, feathered wings that beat, a fanned tail. Variants:
  bird   songbirds, crows, ravens, owls, gulls, waterfowl: small, a short straight beak
  eagle  eagles, hawks, vultures, griffons, harpies: a raptor's hooked beak, broad fingered
         wings, strong talons
  roc    the Roc Matriarch (a boss): a vast eagle with a crest of plumes and a golden beak
Pale plumage with darker wing tips, so bestiary tints colour it.
    tools/art3d/blender/run.sh models/bird.py --preview [--variant eagle|roc]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'bird'
RAPTOR = V in ('eagle', 'roc')
k_ = {'bird': 1.0, 'eagle': 1.25, 'roc': 1.5}[V]            # wing reach
pal = Palette(V, {
    'plume': ['#f4f0e8', '#d8d0c2', '#f8f4ee'], 'wing': ['#e6ded0', '#bcb2a0', '#8a8070'], 'tip': ['#6a6258', '#4a443c', '#2e2a26'],
    'beak': '#f0b840' if V != 'roc' else '#ffd860', 'eye': '#f8e040' if RAPTOR else '#141010', 'pupil': '#141010',
    'leg': '#e0a040', 'talon': '#2a2420', 'crest': ['#ffffff', '#e8e0d0', '#c8bca8'],
})

s = Skel(V)
s.node('body', (0, 0.0, 0.3), 0.12, sx=0.95)
s.node('chest', (0, -0.1, 0.35), 0.115, 'body', sx=0.95)
s.node('neck', (0, -0.17, 0.45), 0.065, 'chest')
s.node('head', (0, -0.21, 0.53), 0.075, 'neck')
s.node('tail0', (0, 0.15, 0.3), 0.055, 'body')
s.node('tail1', (0, 0.27, 0.27), 0.025, 'tail0')
for side, x in (('L', 1), ('R', -1)):
    s.node(f'leg0.{side}', (0.05 * x, 0.02, 0.21), 0.035, 'body')
    s.node(f'leg1.{side}', (0.05 * x, 0.02, 0.08), 0.016, f'leg0.{side}')
    s.node(f'leg2.{side}', (0.05 * x, -0.04, 0.016), 0.016, f'leg1.{side}')
    s.node(f'w0.{side}', (0.09 * x, -0.07, 0.41), 0.035, 'chest')
    s.node(f'w1.{side}', (0.3 * k_ * x, -0.02, 0.45), 0.02, f'w0.{side}')
    s.node(f'w2.{side}', (0.56 * k_ * x, 0.06, 0.43), 0.012, f'w1.{side}')
body = s.hull(subdiv=1, branch_smoothing=0.5)
pal.paint_ramp(body, 'plume')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

for side, x in (('L', 1), ('R', -1)):
    sh, el, tip = s.co(f'w0.{side}'), s.co(f'w1.{side}'), s.co(f'w2.{side}')
    in_back, out_back = (0.3 * k_ * x, 0.2, 0.36), (0.52 * k_ * x, 0.24, 0.38)
    add(poly(f'wing0.{side}', [sh, el, in_back, (0.08 * x, 0.12, 0.34)], [(0, 1, 2, 3)], 0.012), 'wing', f'w1.{side}')
    add(poly(f'wing1.{side}', [el, tip, out_back, in_back], [(0, 1, 2, 3)], 0.012), 'tip', f'w2.{side}')
    if RAPTOR:
        # the fingered primaries at the wing's end
        for j in range(3):
            a = 0.3 + 0.25 * j
            add(part('cone', f'primary{j}.{side}', (tip.x + 0.04 * x, tip.y + 0.04 + a * 0.12, tip.z - 0.01), (0.03, 0.012, 0.09),
                     rot=(math.radians(90), 0, math.radians((80 + 12 * j) * x)), segments=4), 'tip', f'w2.{side}')
    add(part('sphere', f'eye.{side}', (0.045 * x, -0.26, 0.56), 0.016, segments=6), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.05 * x, -0.27, 0.56), 0.009, segments=6), 'pupil', 'head')
    c = s.co(f'leg2.{side}')
    for j, a in enumerate((-30, 0, 30)):
        add(part('cone', f'toe{j}.{side}', (c.x + 0.02 * math.sin(math.radians(a)), c.y - 0.03, 0.01), (0.008, 0.035, 0.008),
                 rot=(math.radians(90), 0, math.radians(a)), segments=4), 'talon' if RAPTOR else 'leg', f'leg2.{side}')
# the beak: a raptor's hooked, a songbird's short and straight
if RAPTOR:
    add(part('cone', 'beak', (0, -0.29, 0.53), (0.035, 0.06, 0.03), rot=(math.radians(100), 0, 0), segments=5), 'beak', 'head')
    add(part('cone', 'hook', (0, -0.34, 0.505), (0.015, 0.015, 0.03), rot=(math.radians(160), 0, 0), segments=4), 'beak', 'head')
else:
    add(part('cone', 'beak', (0, -0.29, 0.52), (0.022, 0.045, 0.018), rot=(math.radians(90), 0, 0), segments=4), 'beak', 'head')
# the tail fan
add(poly('tailfan', [(0, 0.22, 0.29), (0.09, 0.4, 0.25), (0, 0.43, 0.26), (-0.09, 0.4, 0.25)], [(0, 1, 2, 3)], 0.012), 'wing', 'tail1')
if V == 'roc':
    for i in range(5):
        add(part('cone', f'crest{i}', (0, -0.18 + 0.03 * i, 0.6 + 0.01 * i), (0.015, 0.02, 0.09 - 0.008 * i), rot=(math.radians(-40 - 8 * i), 0, 0), segments=4), 'crest', 'head')
    add(part('ico', 'ruff', (0, -0.15, 0.44), (0.09, 0.07, 0.08)), 'crest', 'neck')

body = finish_body(body, arm, parts, budget=3500 if V == 'roc' else 2400)

c = Clips(arm)
# they fly in the game (bestiary 'fly'): idle is hovering on beating wings
with c.clip('Idle', 18, loop=True) as k:
    gaits.flap(k, 18, up=45, down=-35)
    k.loc('body', 4, y=0.02).loc('body', 13, y=-0.015).rot('tail1', 9, x=8)
    for side in ('L', 'R'):
        k.turn(f'leg0.{side}', 0, (1, 0, 0), 25)
with c.clip('Walk', 14, loop=True) as k:
    gaits.flap(k, 14, up=55, down=-40)
    k.rot('body', 0, x=12).rot('body', 7, x=12)
    for side in ('L', 'R'):
        k.turn(f'leg0.{side}', 0, (1, 0, 0), 40)
with c.clip('Bite_Front', 18) as k:
    # rear back with wings spread, then strike: beak and talons forward
    gaits.flap(k, 18, up=60, down=-20)
    k.rot('body', 6, x=-25).rot('neck', 6, x=-20).rot('body', 10, x=25).rot('neck', 10, x=30).rot('head', 10, x=10)
    for side in ('L', 'R'):
        k.turn(f'leg0.{side}', 10, (1, 0, 0), -60)
    k.rot('body', 18).rot('neck', 18).rot('head', 18)
with c.clip('Bite_InPlace', 24) as k:
    # a screech: wings flung wide and high, head thrown back
    for side, sgn in (('L', 1), ('R', -1)):
        k.turn(f'w1.{side}', 8, (0, 1, 0), -50 * sgn).turn(f'w1.{side}', 18, (0, 1, 0), -48 * sgn)
    k.rot('neck', 8, x=-30).rot('head', 8, x=-20).rot('neck', 24).rot('head', 24)
with c.clip('HitRecieve', 10) as k:
    k.rot('body', 3, x=-20, z=12).rot('neck', 3, x=-15)
    for side, sgn in (('L', 1), ('R', -1)):
        k.turn(f'w1.{side}', 3, (0, 1, 0), 30 * sgn)
with c.clip('Death', 30) as k:
    # the wings fold and it drops, landing on its side
    for side, sgn in (('L', 1), ('R', -1)):
        for f in (10, 30):
            k.aim(f'w1.{side}', f, (0.3 * sgn, 0.9, -0.2)).aim(f'w2.{side}', f, (0.1 * sgn, 1.0, -0.2))
    k.rot('body', 30, z=85).loc('body', 30, y=-0.12).rot('neck', 30, x=40)

mhb.export(arm, body, V, opt['out'], kind='boss' if V == 'roc' else 'creature', clips=c.names,
           meta={'for': {'bird': 'songbirds, crows, owls, waterfowl', 'eagle': 'eagles, hawks, vultures, griffons, harpies',
                         'roc': 'the Roc Matriarch'}[V] + '; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Idle', 9), ('Bite_Front', 10), ('Bite_InPlace', 12), ('Death', 999)))
