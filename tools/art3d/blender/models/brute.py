"""The big two-legged brutes. Variants:
  ogre      ogres, giants, ettins, cyclopes, titans: huge, pot-bellied, a heavy brow, tusks, a
            loincloth and a club-sized fist; pale hide so bestiary tints colour it
  troll     hunched and long-armed, a long nose, a ragged mane, clawed hands
  yeti      yetis, sasquatches, flesh golems, umber hulks: broad and shaggy, a pale fur coat
  minotaur  minotaurs and King Minos: a bull's head with great horns on a warrior's body
    tools/art3d/blender/run.sh models/brute.py --preview [--variant troll|yeti|minotaur]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits
from mhb.forms import humanoid, humanoid_clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'ogre'
P = {
    'ogre': dict(height=2.6, girth=1.25, shoulders=1.15, arms=1.05, legs=0.9, hunch=0.15, head=1.25, belly=1.3),
    'troll': dict(height=2.7, girth=0.95, shoulders=1.0, arms=1.35, legs=1.0, hunch=0.45, head=0.95, belly=0.9),
    'yeti': dict(height=2.3, girth=1.4, shoulders=1.2, arms=1.15, legs=0.85, hunch=0.2, head=1.0, belly=1.15),
    'minotaur': dict(height=2.7, girth=1.2, shoulders=1.3, arms=1.05, legs=1.0, hunch=0.1, head=1.25, belly=1.0),
}[V]
pal = Palette(V, {
    'hide': ['#e6dccc', '#c2b49e', '#9a8a74'], 'fur': ['#f4f2ec', '#dad6cc', '#b0aa9e'],
    'cloth': ['#9a7a54', '#7a5c3c', '#5a4028'], 'tusk': '#f2ead6', 'eye': '#f0d040', 'pupil': '#1a1410',
    'horn': ['#f2e8d0', '#c8b898', '#8a7a60'], 'nail': '#4a3e34', 'hair': ['#6a5a48', '#4a3c2e', '#2e2418'],
    'nose': '#3a2a24', 'metal': ['#c8ccd0', '#8a9096', '#5a6066'], 'wood': ['#9a7048', '#76522e', '#52381c'],
})

s = Skel(V)
L = humanoid(s, **P)
H = P['height']
if V == 'minotaur':
    # a bull's long head: push the muzzle forward
    s.node('muzzle', (0, L['head_y'] - 0.14 * H * 0.5, L['head_z'] - 0.04 * H), 0.06 * H, 'head', sx=1.1)
if V == 'troll':
    s.node('nose', (0, L['head_y'] - 0.11 * H * 0.5, L['head_z'] - 0.01 * H), 0.025 * H, 'head')
body = s.hull(subdiv=1, branch_smoothing=0.4, smooth=True)
pal.paint_ramp(body, 'fur' if V == 'yeti' else 'hide')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

hz, hy = L['head_z'], L['head_y']
r_head = 0.075 * H * P['head']
for side, x in (('L', 1), ('R', -1)):
    ey = hy - r_head * 0.85
    add(part('sphere', f'eye.{side}', (0.32 * r_head * x, ey, hz + 0.1 * r_head), 0.13 * r_head, segments=6), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.34 * r_head * x, ey - 0.08 * r_head, hz + 0.1 * r_head), 0.07 * r_head, segments=6), 'pupil', 'head')
    hand = s.co(f'arm2.{side}')
    for j in range(3):
        add(part('cone', f'nail{j}.{side}', (hand.x + (j - 1) * 0.025 * H, hand.y - 0.04 * H, hand.z - 0.045 * H), (0.008 * H, 0.008 * H, 0.025 * H),
                 rot=(math.radians(180), 0, 0), segments=4), 'nail', f'arm2.{side}')
    if V == 'ogre':
        add(part('cone', f'tusk.{side}', (0.35 * r_head * x, hy - r_head * 0.9, hz - 0.45 * r_head), (0.05 * r_head, 0.05 * r_head, 0.22 * r_head), segments=4), 'tusk', 'head')
    if V == 'minotaur':
        add(part('cone', f'horn.{side}', (1.25 * r_head * x, hy, hz + 0.75 * r_head), (0.2 * r_head, 0.2 * r_head, 0.9 * r_head),
                 rot=(math.radians(-15), math.radians(48 * x), 0), segments=6), 'horn', 'head')
        add(part('cone', f'hornbase.{side}', (0.8 * r_head * x, hy, hz + 0.45 * r_head), (0.28 * r_head, 0.28 * r_head, 0.4 * r_head),
                 rot=(0, math.radians(75 * x), 0), segments=6), 'horn', 'head')
        add(part('cone', f'ear.{side}', (0.95 * r_head * x, hy + 0.1 * r_head, hz + 0.1 * r_head), (0.1 * r_head, 0.05 * r_head, 0.25 * r_head),
                 rot=(0, math.radians(-100 * x), 0), segments=4), 'hide', 'head')
    if V == 'troll':
        add(part('cone', f'ear.{side}', (0.95 * r_head * x, hy + 0.05 * r_head, hz + 0.2 * r_head), (0.08 * r_head, 0.04 * r_head, 0.4 * r_head),
                 rot=(0, math.radians(-75 * x), 0), segments=4), 'hide', 'head')
# the head itself: a skull with some weight to it (the hull alone tapers to a point)
add(part('sphere', 'skull', (0, hy, hz), (1.15 * r_head, 1.2 * r_head, 1.1 * r_head), segments=12), 'fur' if V == 'yeti' else 'hide', 'head')
# brow ridge, and what each wears
add(part('sphere', 'brow', (0, hy - r_head * 0.7, hz + 0.32 * r_head), (0.75 * r_head, 0.25 * r_head, 0.18 * r_head), segments=8),
    'fur' if V == 'yeti' else 'hide', 'head')
if V in ('ogre', 'troll', 'minotaur'):
    add(part('cyl', 'loincloth', (0, 0, L['hip_z'] - 0.02 * H), (0.13 * H * P['girth'] * 1.2, 0.11 * H * P['girth'], 0.06 * H), segments=10), 'cloth', 'hips')
if V == 'ogre':
    add(part('sphere', 'belt', (0, -0.1 * H * P['girth'] * 0.9, L['hip_z'] + 0.02 * H), (0.04 * H, 0.02 * H, 0.03 * H), segments=6), 'metal', 'hips')
if V == 'troll':
    for i in range(5):
        add(part('cone', f'mane{i}', (0, hy + 0.2 * r_head + 0.04 * H * i, hz + 0.2 * r_head - 0.05 * H * i), (0.03 * H, 0.03 * H, 0.09 * H),
                 rot=(math.radians(-140), 0, 0), segments=4), 'hair', 'chest' if i > 1 else 'head')
if V == 'yeti':
    for i, (x, y, z) in enumerate(((0.16, 0.0, 0.62), (-0.16, 0.0, 0.62), (0.0, 0.12, 0.66), (0.2, 0.05, 0.45), (-0.2, 0.05, 0.45))):
        add(part('ico', f'tuft{i}', (x * H, y * H, z * H), 0.06 * H), 'fur', 'chest' if z > 0.55 else 'spine')
if V == 'minotaur':
    add(part('sphere', 'snout', (0, hy - r_head * 1.3, hz - 0.3 * r_head), (0.75 * r_head, 0.8 * r_head, 0.6 * r_head), segments=10), 'hide', 'muzzle')
    add(part('sphere', 'nose', (0, hy - r_head * 2.0, hz - 0.35 * r_head), (0.45 * r_head, 0.2 * r_head, 0.3 * r_head), segments=8), 'nose', 'muzzle')
    add(part('cyl', 'ring', (0, hy - r_head * 2.0, hz - 0.55 * r_head), (0.18 * r_head, 0.18 * r_head, 0.03 * r_head), rot=(math.radians(90), 0, 0), segments=8), 'metal', 'muzzle')

# what it carries in its right hand: an ogre or giant a great club, a minotaur a two-headed axe
hand = s.co('arm2.R')
if V == 'ogre':
    # the club held out in front, angled down: shaft from the fist, a studded head at the end
    d = (0.0, -0.94, -0.34)
    th = math.radians(110)
    at = lambda f: (hand.x + d[0] * f * H, hand.y + d[1] * f * H, hand.z + d[2] * f * H)
    add(part('cyl', 'club', at(0.17), (0.022 * H, 0.022 * H, 0.17 * H), rot=(th, 0, 0), segments=6), 'wood', 'arm2.R')
    add(part('sphere', 'clubhead', at(0.38), (0.065 * H, 0.065 * H, 0.09 * H), rot=(th, 0, 0), segments=7), 'wood', 'arm2.R')
    hx, hy_, hz_ = at(0.4)
    for i in range(4):
        a = math.pi / 2 * i
        add(part('cone', f'stud{i}', (hx + 0.065 * H * math.cos(a), hy_, hz_ + 0.065 * H * math.sin(a)), (0.012 * H, 0.012 * H, 0.025 * H),
                 rot=(0, math.radians(90) * math.cos(a), 0), segments=4), 'metal', 'arm2.R')
if V == 'minotaur':
    # a great two-headed axe held upright beside it
    add(part('cyl', 'haft', (hand.x, hand.y - 0.02 * H, hand.z + 0.12 * H), (0.016 * H, 0.016 * H, 0.3 * H), segments=6), 'wood', 'arm2.R')
    for side, sx in (('a', 1), ('b', -1)):
        y0, z0 = hand.y - 0.02 * H, hand.z + 0.34 * H
        blade = [(hand.x, y0, z0 + 0.06 * H), (hand.x, y0 + sx * 0.16 * H, z0 + 0.11 * H), (hand.x, y0 + sx * 0.19 * H, z0),
                 (hand.x, y0 + sx * 0.16 * H, z0 - 0.11 * H), (hand.x, y0, z0 - 0.06 * H)]
        add(poly(f'blade{side}', blade, [(0, 1, 2, 3, 4)], 0.015 * H), 'metal', 'arm2.R')

body = finish_body(body, arm, parts, budget=2900)

c = Clips(arm)
humanoid_clips(c, gaits, frames_walk=36 if V != 'troll' else 32, swing=22, arm=20 if V != 'troll' else 30, heavy=1.25 if V in ('ogre', 'yeti') else 1.1, height=H)

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names, meta={'for': {
    'ogre': 'ogres, giants, ettins, cyclopes, titans', 'troll': 'trolls', 'yeti': 'yetis, sasquatches, flesh golems, umber hulks',
    'minotaur': 'minotaurs and King Minos'}[V] + '; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 9), ('Bite_Front', 9), ('Bite_InPlace', 14), ('Death', 999)))
