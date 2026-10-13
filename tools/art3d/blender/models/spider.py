"""Spiders: eight jointed legs arched high over a low body, a bulbous banded abdomen, a cluster of
eyes and fangs. Variants:
  spider        every spider, tarantula and driders' kin: pale grey-brown so tints colour it
  spider_queen  the Spider Queens (Zyraxxis and the others), a boss: swollen marked abdomen,
                a crown of spines, red eyes
    tools/art3d/blender/run.sh models/spider.py --preview [--variant spider_queen]
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'spider'
Q = V == 'spider_queen'
pal = Palette(V, {
    'body': ['#cfc6b8', '#9c9284', '#6e665a'] if not Q else ['#4a3a5a', '#2c2238', '#181020'],
    'abdomen': ['#d6cdbe', '#a69a88', '#7a6e5e'] if not Q else ['#5a4470', '#382a48', '#1c1428'],
    'band': '#4a4038' if not Q else '#c83a3a',
    'leg': ['#c4baa8', '#8e8472', '#5e5648'] if not Q else ['#3e3048', '#261c30', '#140e1a'],
    'eye': '#1a1412' if not Q else '#ff3a3a', 'fang': '#e8e0cc', 'crown': '#e0c870',
})
ab = 1.35 if Q else 1.0

s = Skel(V)
s.node('thorax', (0, -0.08, 0.36), 0.15)
s.node('waist', (0, 0.1, 0.38), 0.07, 'thorax')
s.node('abdomen', (0, 0.36, 0.45), 0.25 * ab, 'waist', sx=0.95)
s.node('head', (0, -0.27, 0.34), 0.1, 'thorax')
PAIRS = [(-0.2, 0.75), (-0.1, 0.35), (0.0, -0.1), (0.1, -0.55)]      # y on the thorax, how far forward it reaches
for n, (y, fwd) in enumerate(PAIRS):
    for side, x in (('L', 1), ('R', -1)):
        s.node(f'leg{n}0.{side}', (0.11 * x, y - 0.08, 0.36), 0.05, 'thorax')
        s.node(f'leg{n}1.{side}', (0.42 * x, y - 0.08 - fwd * 0.25, 0.62), 0.04, f'leg{n}0.{side}')
        s.node(f'leg{n}2.{side}', (0.72 * x, y - 0.08 - fwd * 0.5, 0.02), 0.022, f'leg{n}1.{side}')

body = s.hull(subdiv=1, branch_smoothing=0.3)
pal.paint_ramp(body, 'body')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

# the abdomen: a shell over the hull, banded across its back
shell = part('sphere', 'shell', (0, 0.4, 0.48), (0.27 * ab, 0.34 * ab, 0.24 * ab), segments=12)
add(shell, 'abdomen', 'abdomen')
for i, (y, w) in enumerate(((0.28, 0.22), (0.42, 0.26), (0.56, 0.2))):
    add(part('sphere', f'band{i}', (0, y * ab + 0.02, 0.6 * (0.9 + 0.1 * ab) + 0.09 * (ab - 1)), (w * ab, 0.035, 0.05), segments=8), 'band', 'abdomen')
# eyes: two big, four small, clustered on the head
for x, z, r in ((0.035, 0.4, 0.028), (-0.035, 0.4, 0.028), (0.07, 0.38, 0.016), (-0.07, 0.38, 0.016), (0.05, 0.42, 0.014), (-0.05, 0.42, 0.014)):
    add(part('sphere', f'eye{x}{z}', (x, -0.355, z), r, segments=6), 'eye', 'head')
for side, x in (('L', 1), ('R', -1)):
    add(part('cone', f'fang.{side}', (0.03 * x, -0.37, 0.27), (0.018, 0.018, 0.05), rot=(math.radians(160), 0, 0), segments=4), 'fang', 'head')
if Q:
    for i in range(5):
        a = math.radians(-50 + 25 * i)
        add(part('cone', f'crown{i}', (0.08 * math.sin(a), -0.25 + 0.02 * abs(i - 2), 0.47), (0.02, 0.02, 0.07), rot=(0, a * 0.6, 0), segments=4), 'crown', 'head')

body = finish_body(body, arm, parts, budget=6000 if Q else 2800)

c = Clips(arm)
with c.clip('Idle', 50, loop=True) as k:
    k.loc('thorax', 25, y=-0.012).rot('abdomen', 25, x=5).rot('head', 12, z=6).rot('head', 37, z=-6)
    for n in (0, 1):
        for side, sgn in (('L', 1), ('R', -1)):
            k.turn(f'leg{n}1.{side}', 25, (0, 0, 1), 4 * sgn)
with c.clip('Walk', 24, loop=True) as k:
    gaits.legs(k, 24, 4, swing=18, lift=14, root='thorax', bob=0.01)
with c.clip('Run', 14, loop=True) as k:
    gaits.legs(k, 14, 4, swing=24, lift=20, root='thorax', bob=0.02)
with c.clip('Bite_Front', 20) as k:
    # rear up on the back legs, front legs raised, then strike down with the fangs
    k.rot('thorax', 7, x=-22).loc('thorax', 7, y=0.08)
    for side, sgn in (('L', 1), ('R', -1)):
        k.turn(f'leg01.{side}', 7, (1, 0, 0), -40).turn(f'leg11.{side}', 7, (1, 0, 0), -25)
    k.rot('thorax', 11, x=14).loc('thorax', 11, y=-0.02).rot('head', 11, x=18)
    k.rot('thorax', 20).loc('thorax', 20).rot('head', 20)
with c.clip('Bite_InPlace', 24) as k:
    # the abdomen lifts and sprays web
    k.rot('abdomen', 10, x=-35).rot('waist', 10, x=-15).rot('abdomen', 18, x=-38).rot('abdomen', 24).rot('waist', 24)
with c.clip('HitRecieve', 12) as k:
    k.rot('thorax', 3, x=-10, z=8).loc('thorax', 3, y=0.03)
with c.clip('Death', 36) as k:
    # flipped onto its back, legs curling in
    k.loc('thorax', 10, y=0.12).rot('thorax', 22, z=150).loc('thorax', 22, y=0.2)
    k.rot('thorax', 36, z=178).loc('thorax', 36, y=0.1)
    for n in range(4):
        for side in ('L', 'R'):
            k.rot(f'leg{n}2.{side}', 36, x=60 if side == 'L' else -60)

mhb.export(arm, body, V, opt['out'], kind='boss' if Q else 'creature', clips=c.names,
           meta={'for': 'the Spider Queens' if Q else 'spiders; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 6), ('Walk', 18), ('Bite_Front', 7), ('Death', 999)))
