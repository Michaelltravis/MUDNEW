"""Insects: six legs, a head, thorax and abdomen. Variants:
  beetle        beetles, scarabs, ants, ticks, roaches: a rounded wing-case shell, mandibles, antennae
  wasp          bees, wasps, hornets, flies, moths: a striped abdomen with a sting, buzzing wings
  stick_mother  the Stick Mother (a boss): a towering stick insect, long jointed limbs, a mantis's
                raking forelegs
Pale so bestiary tints colour them.
    tools/art3d/blender/run.sh models/insect.py --preview --variant beetle
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'beetle'
pal = Palette(V, {
    'shell': ['#ece4d8', '#c4b8a6', '#968a78'], 'leg': ['#d8ccba', '#a89a86', '#786c5a'], 'band': '#3a3028',
    'eye': '#1a1612', 'wing': ['#f4f8ff', '#dce6f2', '#b8c8dc'], 'sting': '#2a2420', 'bark': ['#d4c4a0', '#a8946c', '#7a6844'],
})

s = Skel(V)
parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

if V == 'stick_mother':
    S = 1.6
    s.node('thorax', (0, 0.0, 0.62 * S), 0.05 * S)
    s.node('abdomen', (0, 0.45 * S, 0.58 * S), 0.045 * S, 'thorax')
    s.node('tip', (0, 0.8 * S, 0.5 * S), 0.025 * S, 'abdomen')
    s.node('neck', (0, -0.25 * S, 0.8 * S), 0.04 * S, 'thorax')
    s.node('head', (0, -0.36 * S, 0.92 * S), 0.06 * S, 'neck')
    legs = (-0.08, 0.1, 0.3)
    reach, lift_ = 0.55 * S, 0.85 * S
else:
    S = 1.0
    W = V == 'wasp'
    s.node('thorax', (0, 0.0, 0.2), 0.09 if not W else 0.07)
    s.node('abdomen', (0, 0.2, 0.2 if not W else 0.22), 0.13 if not W else 0.08, 'thorax', sx=1.1 if not W else 0.9)
    s.node('tip', (0, 0.33, 0.19 if not W else 0.18), 0.05 if not W else 0.03, 'abdomen')
    s.node('neck', (0, -0.1, 0.21), 0.05, 'thorax')
    s.node('head', (0, -0.16, 0.21), 0.07 if not W else 0.06, 'neck')
    legs = (-0.06, 0.0, 0.06)
    reach, lift_ = (0.17, 0.15) if V == 'beetle' else (0.2, 0.2)
for n, y in enumerate(legs):
    for side, x in (('L', 1), ('R', -1)):
        top = s.co('thorax').z
        s.node(f'leg{n}0.{side}', (0.05 * S * x, y * S, top - 0.02 * S), 0.022 * S, 'thorax')
        s.node(f'leg{n}1.{side}', ((0.05 * S + reach * 0.55) * x, (y - 0.03 * (1 - n)) * S, max(top, lift_)), 0.016 * S, f'leg{n}0.{side}')
        s.node(f'leg{n}2.{side}', ((0.05 * S + reach) * x, (y - 0.08 * (1 - n)) * S, 0.012), 0.01 * S, f'leg{n}1.{side}')
if V == 'stick_mother':
    for side, x in (('L', 1), ('R', -1)):
        # the raking forelegs, held up and folded like a mantis's
        s.node(f'arm0.{side}', (0.05 * S * x, -0.3 * S, 0.82 * S), 0.025 * S, 'neck')
        s.node(f'arm1.{side}', (0.12 * S * x, -0.45 * S, 1.05 * S), 0.02 * S, f'arm0.{side}')
        s.node(f'arm2.{side}', (0.1 * S * x, -0.55 * S, 0.8 * S), 0.018 * S, f'arm1.{side}')
body = s.hull(subdiv=1, branch_smoothing=0.3)
pal.paint_ramp(body, 'bark' if V == 'stick_mother' else 'shell')
arm = s.armature()

hz = s.co('head').z
for side, x in (('L', 1), ('R', -1)):
    add(part('sphere', f'eye.{side}', (0.045 * S * x, s.co('head').y - 0.035 * S, hz + 0.02 * S), 0.025 * S, segments=6), 'eye', 'head')
    add(part('cone', f'antenna.{side}', (0.03 * S * x, s.co('head').y - 0.02 * S, hz + 0.1 * S), (0.006 * S, 0.006 * S, 0.1 * S),
             rot=(math.radians(-35), math.radians(25 * x), 0), segments=3), 'leg', 'head')
    if V == 'beetle':
        add(part('cone', f'mandible.{side}', (0.03 * x, -0.24, 0.17), (0.012, 0.04, 0.012), rot=(math.radians(90), 0, math.radians(-25 * x)), segments=3), 'band', 'head')
    if V == 'wasp':
        add(poly(f'wing.{side}', [(0.02 * x, -0.02, 0.27), (0.24 * x, 0.06, 0.36), (0.26 * x, 0.14, 0.33), (0.04 * x, 0.08, 0.26)], [(0, 1, 2, 3)], 0.004), 'wing', 'thorax')
if V == 'beetle':
    add(part('sphere', 'elytra', (0, 0.17, 0.25), (0.15, 0.2, 0.12), segments=12), 'shell', 'abdomen')
if V == 'wasp':
    for i, y in enumerate((0.16, 0.22, 0.28)):
        add(part('cyl', f'band{i}', (0, y, 0.21), (0.08 - 0.012 * i, 0.08 - 0.012 * i, 0.012), rot=(math.radians(90), 0, 0), segments=10), 'band', 'abdomen')
    add(part('cone', 'sting', (0, 0.37, 0.17), (0.012, 0.012, 0.04), rot=(math.radians(-100), 0, 0), segments=4), 'sting', 'tip')
if V == 'stick_mother':
    for i in range(4):
        add(part('cone', f'thorn{i}', (0, 0.1 * S * i, 0.65 * S), (0.012 * S, 0.012 * S, 0.05 * S), segments=3), 'band', 'thorax' if i < 2 else 'abdomen')

boss = V == 'stick_mother'
body = finish_body(body, arm, parts, budget=3000 if boss else 2200)

c = Clips(arm)
with c.clip('Idle', 40, loop=True) as k:
    k.loc('thorax', 20, y=0.008 * S).rot('head', 10, z=8).rot('head', 30, z=-8)
    if V == 'wasp':
        k.rot('abdomen', 10, x=8).rot('abdomen', 30, x=-6)       # hovering, the abdomen pumping
    if boss:
        for side in ('L', 'R'):
            k.turn(f'arm1.{side}', 20, (1, 0, 0), -10)
with c.clip('Walk', 18 if not boss else 30, loop=True) as k:
    gaits.legs(k, 18 if not boss else 30, 3, swing=20, lift=18, root='thorax', bob=0.005 * S)
with c.clip('Bite_Front', 18) as k:
    if boss:
        for side in ('L', 'R'):
            k.turn(f'arm0.{side}', 6, (1, 0, 0), -40).turn(f'arm0.{side}', 10, (1, 0, 0), 50).turn(f'arm0.{side}', 18, (1, 0, 0), 0)
    k.rot('thorax', 6, x=-12).rot('thorax', 10, x=12).rot('thorax', 18).rot('head', 10, x=15).rot('head', 18)
    if V == 'wasp':
        k.rot('abdomen', 8, x=-50).rot('abdomen', 18)
with c.clip('HitRecieve', 10) as k:
    k.rot('thorax', 3, x=-10, z=10)
with c.clip('Death', 30) as k:
    k.loc('thorax', 10, y=0.08 * S).rot('thorax', 20, z=150).rot('thorax', 30, z=178).loc('thorax', 30, y=0.02 * S)
    for n in range(3):
        for side, sgn in (('L', 1), ('R', -1)):
            k.turn(f'leg{n}2.{side}', 30, (0, 1, 0), 50 * sgn)

mhb.export(arm, body, V, opt['out'], kind='boss' if boss else 'creature', clips=c.names,
           meta={'for': {'beetle': 'beetles, scarabs, ants, ticks', 'wasp': 'bees, wasps, hornets, flies, moths',
                         'stick_mother': 'the Stick Mother'}[V] + '; tinted by bestiary.js', **({} if boss else {'ref': 'length'})})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 4), ('Walk', 12), ('Bite_Front', 10), ('Death', 999)))
