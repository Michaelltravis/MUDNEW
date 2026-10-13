"""Things that grow, and the floating eye. Variants:
  treant    treants, ancient trees, dryads, walking trees: a trunk of a body on root feet, branch
            arms with twig fingers, a crown of leaves, a knot-hole face
  myconid   myconids, fungus folk: a stubby body under a broad spotted cap, gills beneath
  beholder  beholders, eye tyrants: a floating orb with one great eye, a fanged mouth and a crown
            of eye stalks
Pale so bestiary tints colour them (the treant's leaves stay green).
    tools/art3d/blender/run.sh models/growth.py --preview --variant treant
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips, gaits
from mhb.forms import humanoid, humanoid_clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'treant'
pal = Palette(V, {
    'bark': ['#8a6c4c', '#5e4630', '#3a2a1a'], 'leaf': ['#9ad06a', '#6aa244', '#3e7028'], 'hole': '#2a1e14', 'glow': '#f0e070',
    'cap': ['#d8704e', '#a8462e', '#6e2a1a'], 'spot': '#f8f4ee', 'stem': ['#f4ecdc', '#dccfb8', '#b8a88e'], 'gill': '#a88a76',
    'orb': ['#ecdcd8', '#c4aaa6', '#94787a'], 'eye': '#f8f4ec', 'iris': '#c84030', 'pupil': '#141010', 'tooth': '#f8f2e0',
})

s = Skel(V)
parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

if V in ('treant', 'myconid'):
    T = V == 'treant'
    H = 3.0 if T else 1.2
    L = humanoid(s, height=H, girth=1.25 if T else 1.3, shoulders=1.05, arms=1.2 if T else 0.8, legs=0.75 if T else 0.6, hunch=0.05,
                 head=0.9 if T else 1.6, belly=1.1)
    hz, hy, r = L['head_z'], L['head_y'], 0.075 * H * (0.9 if T else 1.6)
    body = s.hull(subdiv=1, branch_smoothing=0.4, smooth=not T)
    pal.paint_ramp(body, 'bark' if T else 'stem')
    arm = s.armature()
    if T:
        # the crown of leaves, the knot-hole face, twig fingers and root toes
        for i, (x, y, z, rr) in enumerate(((0, 0.05, 1.35, 1.6), (0.9, 0.2, 1.0, 1.1), (-0.9, 0.2, 1.0, 1.1), (0.4, -0.5, 1.1, 0.9), (-0.4, 0.6, 1.2, 1.0))):
            add(part('ico', f'leaves{i}', (x * r, hy + y * r, hz + z * r), rr * r), 'leaf', 'head')
        for side, x in (('L', 1), ('R', -1)):
            add(part('sphere', f'eye.{side}', (0.35 * r * x, hy - 0.85 * r, hz + 0.1 * r), 0.16 * r, segments=6), 'glow', 'head')
            hand = s.co(f'arm2.{side}')
            for j in range(4):
                a = math.radians(-50 + 33 * j)
                add(part('cone', f'twig{j}.{side}', (hand.x + 0.08 * H * math.sin(a) * x, hand.y - 0.02 * H, hand.z - 0.06 * H), (0.012 * H, 0.012 * H, 0.08 * H),
                         rot=(math.radians(170), math.radians(30 * math.sin(a) * x), 0), segments=4), 'bark', f'arm2.{side}')
            for j in range(3):
                a = math.radians(-40 + 40 * j)
                foot = s.co(f'leg2.{side}')
                add(part('cone', f'root{j}.{side}', (foot.x + 0.06 * H * math.sin(a), foot.y - 0.06 * H * math.cos(a), 0.02 * H), (0.025 * H, 0.025 * H, 0.08 * H),
                         rot=(math.radians(-80), 0, math.radians(math.degrees(a))), segments=4), 'bark', f'leg2.{side}')
            # branches sprouting from the shoulders
            add(part('cone', f'bough.{side}', ((L['sw'] + 0.05 * H) * x, 0, L['chest_z'] + 0.18 * H), (0.03 * H, 0.03 * H, 0.16 * H),
                     rot=(0, math.radians(35 * x), 0), segments=5), 'bark', 'chest')
            add(part('ico', f'boughleaf.{side}', ((L['sw'] + 0.13 * H) * x, 0, L['chest_z'] + 0.3 * H), 0.08 * H), 'leaf', 'chest')
        add(part('sphere', 'mouth', (0, hy - 0.9 * r, hz - 0.4 * r), (0.35 * r, 0.12 * r, 0.15 * r), segments=8), 'hole', 'head')
    else:
        add(part('sphere', 'cap', (0, hy, hz + 0.55 * r), (2.3 * r, 2.3 * r, 1.0 * r), segments=14), 'cap', 'head')
        add(part('cyl', 'gills', (0, hy, hz + 0.25 * r), (2.1 * r, 2.1 * r, 0.06 * r), segments=14), 'gill', 'head')
        for i, (a, rr) in enumerate(((0, 0.9), (1.6, 0.6), (3.0, 1.0), (4.4, 0.7), (5.4, 0.9))):
            add(part('sphere', f'spot{i}', (1.3 * rr * r * math.cos(a), hy + 1.3 * rr * r * math.sin(a), hz + 0.55 * r + 0.85 * r * math.sqrt(max(0, 1 - (1.3 * rr / 2.3) ** 2))), (0.3 * r, 0.3 * r, 0.1 * r), segments=6), 'spot', 'head')
        for side, x in (('L', 1), ('R', -1)):
            add(part('sphere', f'eye.{side}', (0.35 * r * x, hy - 0.85 * r, hz - 0.1 * r), 0.13 * r, segments=6), 'pupil', 'head')
    body = finish_body(body, arm, parts, budget=2900)
    c = Clips(arm)
    humanoid_clips(c, gaits, frames_walk=44 if T else 30, swing=16 if T else 22, arm=14, heavy=1.4 if T else 1.0, height=H)
else:
    # the beholder: an orb floating on nothing (it rests at the ground; the game lifts it)
    s.node('orb', (0, 0, 0.7), 0.3)
    s.node('jaw', (0, -0.38, 0.45), 0.25, 'orb', sx=1.4)
    STALKS = 8
    for i in range(STALKS):
        a = math.radians(-120 + 240 * i / (STALKS - 1))
        bx, by = 0.35 * math.sin(a), 0.35 * math.cos(a) * 0.6 + 0.1
        s.node(f'stalk{i}a', (bx, by, 1.2), 0.05, 'orb')
        s.node(f'stalk{i}b', (bx * 1.6, by * 1.4 + 0.05, 1.55 + 0.08 * math.cos(a)), 0.03, f'stalk{i}a')
    body = s.hull(subdiv=1, branch_smoothing=0.5)
    pal.paint_ramp(body, 'orb')
    arm = s.armature()
    add(part('sphere', 'ball', (0, 0, 0.7), 0.58, segments=16), 'orb', 'orb')         # the orb itself, round
    add(part('sphere', 'eye', (0, -0.5, 0.82), 0.24, segments=12), 'eye', 'orb')
    add(part('sphere', 'iris', (0, -0.7, 0.82), (0.14, 0.06, 0.14), segments=10), 'iris', 'orb')
    add(part('sphere', 'pupil', (0, -0.75, 0.82), (0.07, 0.03, 0.09), segments=8), 'pupil', 'orb')
    for j in range(7):
        a = math.radians(-60 + 20 * j)
        add(part('cone', f'fang{j}', (0.28 * math.sin(a), -0.55 - 0.04 * math.cos(a), 0.4), (0.03, 0.03, 0.07), rot=(math.radians(180), 0, 0), segments=4), 'tooth', 'jaw')
    for i in range(STALKS):
        tip = s.co(f'stalk{i}b')
        add(part('sphere', f'seye{i}', (tip.x, tip.y - 0.03, tip.z + 0.05), 0.07, segments=8), 'eye', f'stalk{i}b')
        add(part('sphere', f'spup{i}', (tip.x, tip.y - 0.09, tip.z + 0.05), 0.03, segments=6), 'pupil', f'stalk{i}b')
    body = finish_body(body, arm, parts, budget=2900)
    c = Clips(arm)
    def wave(k, frames, amp):
        for i in range(STALKS):
            ph = int(frames * i / STALKS)
            k.turn(f'stalk{i}a', ph % frames, (1, 0, 0), amp).turn(f'stalk{i}a', (ph + frames // 2) % frames, (1, 0, 0), -amp)
    with c.clip('Idle', 60, loop=True) as k:
        wave(k, 60, 12)
        k.loc('orb', 30, y=0.06).rot('orb', 15, z=8).rot('orb', 45, z=-8)
    with c.clip('Walk', 40, loop=True) as k:
        wave(k, 40, 18)
        k.rot('orb', 0, x=10).rot('orb', 20, x=10).loc('orb', 20, y=0.05)
    with c.clip('Bite_Front', 20) as k:
        k.rot('jaw', 7, x=-30).rot('orb', 7, x=-10).rot('jaw', 11, x=15).rot('orb', 11, x=15).rot('jaw', 20).rot('orb', 20)
    with c.clip('Bite_InPlace', 30) as k:
        # every eye turns forward: a ray
        for i in range(STALKS):
            k.turn(f'stalk{i}a', 10, (1, 0, 0), 35).turn(f'stalk{i}a', 22, (1, 0, 0), 35).turn(f'stalk{i}a', 30, (1, 0, 0), 0)
        k.rot('orb', 10, x=8).rot('orb', 30)
    with c.clip('HitRecieve', 12) as k:
        k.rot('orb', 3, x=-14, z=12)
    with c.clip('Death', 40) as k:
        k.loc('orb', 25, y=-0.3).rot('orb', 40, x=70).loc('orb', 40, y=-0.35)
        for i in range(STALKS):
            k.turn(f'stalk{i}a', 40, (1, 0, 0), 60 if i % 2 else -60)

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names,
           meta={'for': {'treant': 'treants, ancient trees, dryads', 'myconid': 'myconids, fungus folk',
                         'beholder': 'beholders, eye tyrants'}[V] + '; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 9), ('Bite_Front', 9), ('Bite_InPlace', 12), ('Death', 999)))
