"""Shelled things that scuttle. Variants:
  crab      crabs, lobsters, crayfish: a broad flat shell, eye stalks, six walking legs, two great
            pincers
  clam      giant clams, oysters, mussels: two ribbed valves hinged at the back, a pearl between them
  scorpion  scorpions: a long segmented body, pincers, and a tail arched over the back to a stinger
  turtle    turtles, tortoises, dragon turtles: a domed patterned shell, a beaked head, four
            stumpy legs
Pale so bestiary tints colour them.
    tools/art3d/blender/run.sh models/shell.py --preview --variant crab
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'crab'
pal = Palette(V, {
    'shell': ['#f0e2d4', '#d0b8a4', '#a08876'], 'under': ['#f8f0e6', '#e6d8c8', '#c8b8a4'], 'leg': ['#e8d6c4', '#c4ac96', '#94806c'],
    'eye': '#141010', 'claw': ['#e8d0bc', '#bca088', '#8a705c'], 'sting': '#3a2a24', 'plate': ['#d8ccb0', '#a89a7c', '#7a6e56'],
    'skin': ['#e0d8c0', '#bcb294', '#8e866c'], 'beak': '#5a5040',
    'flesh': ['#f4d8d0', '#d8aca4', '#a8807a'], 'pearl': '#fbf6ee',
})

s = Skel(V)
parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

if V in ('crab', 'scorpion'):
    long_ = V == 'scorpion'
    s.node('body', (0, 0.0, 0.16), 0.13 if long_ else 0.15, sx=1.2 if long_ else 1.55)
    if long_:
        s.node('abdomen', (0, 0.18, 0.15), 0.11, 'body', sx=1.1)
        s.node('tail0', (0, 0.32, 0.22), 0.07, 'abdomen')
        s.node('tail1', (0, 0.42, 0.38), 0.06, 'tail0')
        s.node('tail2', (0, 0.4, 0.55), 0.05, 'tail1')
        s.node('tail3', (0, 0.3, 0.64), 0.045, 'tail2')
    s.node('head', (0, -0.14, 0.17), 0.07, 'body', sx=1.3)
    for n, y in enumerate((-0.05, 0.03, 0.11) if not long_ else (-0.02, 0.06, 0.14)):
        for side, x in (('L', 1), ('R', -1)):
            s.node(f'leg{n}0.{side}', (0.14 * x if not long_ else 0.1 * x, y, 0.16), 0.03, 'body')
            s.node(f'leg{n}1.{side}', (0.3 * x, y + 0.02, 0.24), 0.022, f'leg{n}0.{side}')
            s.node(f'leg{n}2.{side}', (0.42 * x, y + 0.05, 0.015), 0.012, f'leg{n}1.{side}')
    for side, x in (('L', 1), ('R', -1)):
        s.node(f'arm0.{side}', (0.12 * x, -0.15, 0.2), 0.035, 'body')
        s.node(f'arm1.{side}', (0.26 * x, -0.27, 0.22), 0.03, f'arm0.{side}')
        s.node(f'arm2.{side}', (0.28 * x, -0.42, 0.2), 0.055, f'arm1.{side}', sx=1.2)
    body = s.hull(subdiv=1, branch_smoothing=0.3)
    pal.paint_ramp(body, 'shell')
    arm = s.armature()
    if not long_:
        add(part('sphere', 'carapace', (0, 0.0, 0.2), (0.27, 0.19, 0.09), segments=12), 'shell', 'body')
    else:
        for i, y in enumerate((-0.02, 0.1, 0.2)):
            add(part('sphere', f'plate{i}', (0, y, 0.21), (0.14, 0.08, 0.05), segments=8), 'plate', 'body' if i < 1 else 'abdomen')
        add(part('cone', 'sting', (0, 0.22, 0.6), (0.03, 0.03, 0.08), rot=(math.radians(-120), 0, 0), segments=5), 'sting', 'tail3')
        add(part('sphere', 'bulb', (0, 0.27, 0.64), 0.05, segments=8), 'claw', 'tail3')
    for side, x in (('L', 1), ('R', -1)):
        # eye stalks; pincers: two jaws on each claw
        add(part('cyl', f'stalk.{side}', (0.05 * x, -0.17, 0.27), (0.01, 0.01, 0.05), segments=5), 'leg', 'head')
        add(part('sphere', f'eye.{side}', (0.05 * x, -0.17, 0.33), 0.02, segments=6), 'eye', 'head')
        c = s.co(f'arm2.{side}')
        add(part('cone', f'pincerA.{side}', (c.x + 0.02 * x, c.y - 0.08, c.z + 0.02), (0.03, 0.08, 0.02), rot=(math.radians(90), 0, math.radians(-10 * x)), segments=4), 'claw', f'arm2.{side}')
        add(part('cone', f'pincerB.{side}', (c.x - 0.02 * x, c.y - 0.07, c.z - 0.02), (0.022, 0.065, 0.016), rot=(math.radians(90), 0, math.radians(15 * x)), segments=4), 'claw', f'arm2.{side}')
    PAIRS, LEG = 3, 'leg'
elif V == 'clam':
    # two valves: the lower one on the body, the upper one on a hinge at the back that gapes and snaps
    s.node('body', (0, 0.0, 0.12), 0.12, sx=1.45)
    s.node('hinge', (0, 0.17, 0.16), 0.04, 'body')
    s.node('lid', (0, -0.05, 0.2), 0.05, 'hinge', sx=1.4)
    s.node('foot', (0, -0.2, 0.07), 0.04, 'body')
    body = s.hull(subdiv=1, branch_smoothing=0.3)
    pal.paint_ramp(body, 'flesh')
    arm = s.armature()
    add(part('sphere', 'valveL', (0, 0.0, 0.1), (0.34, 0.27, 0.1), segments=14), 'shell', 'body')
    add(part('sphere', 'valveU', (0, 0.0, 0.2), (0.34, 0.27, 0.1), segments=14), 'shell', 'lid')
    for i in range(9):
        # the wavy lips of the valves, where they meet at the front and sides
        a = math.radians(-100 + 25 * i)
        x, y = 0.3 * math.sin(a), -0.24 * math.cos(a)
        add(part('sphere', f'lipU{i}', (x, y, 0.19), (0.08, 0.06, 0.026), rot=(0, 0, -a), segments=6), 'plate', 'lid')
        add(part('sphere', f'lipL{i}', (x, y, 0.11), (0.08, 0.06, 0.026), rot=(0, 0, -a), segments=6), 'plate', 'body')
    add(part('sphere', 'umbo', (0, 0.17, 0.25), (0.08, 0.06, 0.05), segments=8), 'plate', 'lid')
    add(part('sphere', 'mantle', (0, -0.04, 0.15), (0.3, 0.22, 0.045), segments=12), 'flesh', 'body')
    add(part('sphere', 'pearl', (0, -0.1, 0.19), 0.045, segments=10), 'pearl', 'body')
    PAIRS, LEG = 0, None
else:
    # turtle: a dome over four stumpy legs
    s.node('body', (0, 0.0, 0.2), 0.16, sx=1.25)
    s.node('neck', (0, -0.22, 0.2), 0.06, 'body')
    s.node('head', (0, -0.34, 0.24), 0.065, 'neck')
    s.node('tail0', (0, 0.25, 0.14), 0.03, 'body')
    for n, y in enumerate((-0.14, 0.14)):
        for side, x in (('L', 1), ('R', -1)):
            s.node(f'leg{n}0.{side}', (0.16 * x, y, 0.17), 0.05, 'body')
            s.node(f'leg{n}1.{side}', (0.25 * x, y - 0.02, 0.12), 0.045, f'leg{n}0.{side}')
            s.node(f'leg{n}2.{side}', (0.27 * x, y - 0.04, 0.035), 0.04, f'leg{n}1.{side}')
    body = s.hull(subdiv=1, branch_smoothing=0.3)
    pal.paint_ramp(body, 'skin')
    arm = s.armature()
    add(part('sphere', 'dome', (0, 0.0, 0.24), (0.32, 0.36, 0.17), segments=14), 'shell', 'body')
    add(part('sphere', 'rim', (0, 0.0, 0.19), (0.34, 0.38, 0.05), segments=14), 'plate', 'body')
    for i, (x, y) in enumerate(((0, 0), (0.14, -0.1), (-0.14, -0.1), (0.14, 0.12), (-0.14, 0.12), (0, -0.2), (0, 0.22))):
        add(part('cyl', f'scute{i}', (x, y, 0.38 - 0.25 * (x * x + y * y)), (0.07, 0.07, 0.015), segments=6), 'plate', 'body')
    for side, x in (('L', 1), ('R', -1)):
        add(part('sphere', f'eye.{side}', (0.04 * x, -0.39, 0.27), 0.012, segments=6), 'eye', 'head')
    add(part('cone', 'beak', (0, -0.41, 0.22), (0.03, 0.03, 0.035), rot=(math.radians(110), 0, 0), segments=4), 'beak', 'head')
    PAIRS, LEG = 2, 'leg'

body = finish_body(body, arm, parts, budget=2400)

c = Clips(arm)
ARM = V in ('crab', 'scorpion')
CLAM = V == 'clam'
with c.clip('Idle', 50, loop=True) as k:
    k.loc('body', 25, y=0.01)
    if CLAM:
        # it breathes: the lid lifts a crack and settles
        k.turn('hinge', 0, (1, 0, 0), -10).turn('hinge', 25, (1, 0, 0), -24).turn('hinge', 50, (1, 0, 0), -10)
    elif ARM:
        for side, sgn in (('L', 1), ('R', -1)):
            k.turn(f'arm1.{side}', 12, (1, 0, 0), -12).turn(f'arm1.{side}', 37, (1, 0, 0), 6)
    else:
        k.rot('neck', 12, z=12).rot('neck', 37, z=-12)
    if V == 'scorpion':
        k.rot('tail1', 25, x=-8).rot('tail2', 25, x=-6)
with c.clip('Walk', 22 if V != 'turtle' else 40, loop=True) as k:
    if CLAM:
        # it hops along on its foot, the lid clapping as it lands
        for f0 in (0, 11):
            k.loc('body', f0, y=0.0).loc('body', f0 + 5, y=0.07).loc('body', f0 + 11, y=0.0)
            k.turn('hinge', f0, (1, 0, 0), -18).turn('hinge', f0 + 5, (1, 0, 0), -4).turn('hinge', f0 + 11, (1, 0, 0), -18)
            k.turn('foot', f0, (1, 0, 0), 25).turn('foot', f0 + 5, (1, 0, 0), -20).turn('foot', f0 + 11, (1, 0, 0), 25)
    else:
        gaits.legs(k, 22 if V != 'turtle' else 40, PAIRS, swing=16, lift=14, root='body', bob=0.008)
with c.clip('Bite_Front', 20) as k:
    if V == 'scorpion':
        # the tail strikes over the back
        k.rot('tail0', 6, x=-15).rot('tail1', 6, x=-25).rot('tail0', 10, x=35).rot('tail1', 10, x=40).rot('tail2', 10, x=30)
        k.rot('tail0', 20).rot('tail1', 20).rot('tail2', 20)
    elif CLAM:
        # gape wide, lunge and snap shut
        k.turn('hinge', 0, (1, 0, 0), -4).turn('hinge', 7, (1, 0, 0), -50).turn('hinge', 10, (1, 0, 0), 2).turn('hinge', 20, (1, 0, 0), -4)
        k.rot('body', 7, x=-8).rot('body', 10, x=6).rot('body', 20)
    elif V == 'crab':
        for side in ('L', 'R'):
            k.turn(f'arm0.{side}', 6, (1, 0, 0), 35).turn(f'arm0.{side}', 10, (1, 0, 0), -30).turn(f'arm0.{side}', 20, (1, 0, 0), 0)
    else:
        k.rot('neck', 6, x=-10).rot('neck', 10, x=25).rot('neck', 20)
with c.clip('HitRecieve', 12) as k:
    k.rot('body', 3, x=-10, z=8).loc('body', 3, x=0.02)
with c.clip('Death', 36) as k:
    if CLAM:
        # the lid falls open and the clam slumps on its side
        k.turn('hinge', 0, (1, 0, 0), -4).turn('hinge', 20, (1, 0, 0), -70).turn('hinge', 36, (1, 0, 0), -80)
        k.rot('body', 20, z=10).rot('body', 36, z=18).loc('body', 36, y=-0.03)
    else:
        # flipped onto its back, legs in the air
        k.loc('body', 12, y=0.12).rot('body', 22, z=150).loc('body', 22, y=0.15).rot('body', 36, z=178).loc('body', 36, y=0.08)

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names,
           meta={'for': {'crab': 'crabs, lobsters, crayfish', 'clam': 'giant clams, oysters, mussels', 'scorpion': 'scorpions', 'turtle': 'turtles, tortoises, dragon turtles'}[V] + '; tinted by bestiary.js',
                 'ref': 'length'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 5), ('Walk', 16), ('Bite_Front', 7 if V == 'clam' else 10), ('Death', 999)))
