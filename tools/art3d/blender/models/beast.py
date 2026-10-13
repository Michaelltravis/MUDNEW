"""Four-legged beasts on the shared quadruped frame (mhb.forms.quadruped). Variants:
  cat        cats great and small (lynx, panther, tiger...): long low body, round head, small round
             ears, long tail
  lion       lions, sphinxes, manticores: a cat with a great mane and a tufted tail
  bear       bears: heavy, humped shoulders, short legs, round ears, a stub tail
  rat        rats, mice, weasels and small vermin: low, pointed snout, big round ears, a long bare tail
  rat_king   the Sewer King (a boss): a huge rat with a crown and scars
  deer       deer, stags, elk: long legs and neck, antlers, a white tail flash
  horse      horses, ponies, steeds, nightmares: long head, mane and tail tuft, hooves
  unicorn    unicorns, pegasi, ki-rin: a horse with a spiral horn and a silver mane
  lizard     lizards, salamanders: sprawled legs, flat head, long tapering tail
  crocodile  crocodiles, giant lizards, basilisks: a long armoured lizard with a toothy snout
Each is pale enough that bestiary tints colour it (a tiger orange, a panther black, a bear brown).
    tools/art3d/blender/run.sh models/beast.py --preview --variant cat
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits
from mhb.forms import quadruped, quadruped_clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'cat'
P = {
    'cat': dict(length=1.05, height=0.55, girth=0.17, leg=0.9, neck=0.22, neck_up=0.5, head=0.12, muzzle=0.05, tail=0.75, tail_r=0.035, tail_droop=0.3),
    'lion': dict(length=1.1, height=0.62, girth=0.2, leg=0.95, neck=0.24, neck_up=0.55, head=0.14, muzzle=0.06, tail=0.7, tail_r=0.035, tail_droop=0.6),
    'bear': dict(length=1.05, height=0.62, girth=0.3, leg=0.8, neck=0.18, neck_up=0.3, head=0.15, muzzle=0.08, tail=0.1, tail_r=0.05, tail_droop=0.4, hump=0.6, width=1.1),
    'rat': dict(length=0.9, height=0.3, girth=0.15, leg=0.6, neck=0.12, neck_up=0.3, head=0.1, muzzle=0.1, tail=0.9, tail_r=0.025, tail_droop=0.9),
    'rat_king': dict(length=1.0, height=0.45, girth=0.24, leg=0.65, neck=0.15, neck_up=0.4, head=0.14, muzzle=0.12, tail=1.1, tail_r=0.035, tail_droop=0.9, hump=0.5),
    'deer': dict(length=1.0, height=0.95, girth=0.21, leg=1.4, neck=0.45, neck_up=0.85, head=0.1, muzzle=0.1, tail=0.1, tail_r=0.04, tail_droop=0.2),
    'horse': dict(length=1.4, height=1.1, girth=0.32, leg=1.6, neck=0.6, neck_up=0.95, head=0.15, muzzle=0.34, tail=0.5, tail_r=0.06, tail_droop=0.85),
    'unicorn': dict(length=1.35, height=1.08, girth=0.29, leg=1.6, neck=0.6, neck_up=0.95, head=0.14, muzzle=0.3, tail=0.5, tail_r=0.06, tail_droop=0.8),
    'lizard': dict(length=0.8, height=0.2, girth=0.12, leg=0.5, neck=0.12, neck_up=0.2, head=0.09, muzzle=0.08, tail=0.8, tail_r=0.06, tail_droop=0.95, sprawl=0.8),
    'rabbit': dict(length=0.6, height=0.28, girth=0.15, leg=0.7, neck=0.08, neck_up=0.5, head=0.1, muzzle=0.035, tail=0.06, tail_r=0.05, tail_droop=0.0),
    'pig': dict(length=1.0, height=0.5, girth=0.26, leg=0.55, neck=0.1, neck_up=0.2, head=0.14, muzzle=0.09, tail=0.15, tail_r=0.025, tail_droop=0.2, width=1.05),
    'sheep': dict(length=0.95, height=0.62, girth=0.26, leg=0.85, neck=0.2, neck_up=0.55, head=0.1, muzzle=0.07, tail=0.12, tail_r=0.05, tail_droop=0.7),
    'cow': dict(length=1.3, height=0.95, girth=0.32, leg=1.05, neck=0.3, neck_up=0.35, head=0.15, muzzle=0.13, tail=0.55, tail_r=0.03, tail_droop=0.9, width=1.05),
    'crocodile': dict(length=1.4, height=0.24, girth=0.19, leg=0.5, neck=0.14, neck_up=0.1, head=0.12, muzzle=0.32, tail=1.3, tail_r=0.11, tail_droop=0.95, sprawl=0.9, width=1.1),
}[V]
H = P['height']
pal = Palette(V, {
    'coat': ['#ece4d4', '#c8bca6', '#f2ecdf'], 'belly': ['#f8f4ec', '#e6ded0', '#cfc6b6'],
    'dark': ['#5a4a3a', '#3e3228', '#241c16'], 'nose': '#2a2020', 'eye': '#e8c040', 'pupil': '#141010',
    'claw': '#2e2824', 'mane': ['#d8b884', '#a8844e', '#7a5a30'], 'horn': ['#fff8e0', '#f0d890', '#c8a858'],
    'antler': ['#e8dcc4', '#bca98a', '#8e7a5e'], 'hoof': '#3a3028', 'tooth': '#f4f0e0', 'gold': ['#ffe890', '#e0b440', '#a07820'],
    'scale': ['#e0dcc8', '#b4ae94', '#efe8d4'], 'pink': '#e8a8a0', 'scar': '#9a6a6a',
})

s = Skel(V)
Q = quadruped(s, **P)
body = s.hull(subdiv=1, branch_smoothing=0.45, smooth=V not in ('crocodile',))
pal.paint_ramp(body, 'scale' if V in ('lizard', 'crocodile') else 'coat')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

hx, hy, hz = Q['head']
hr = Q['head_r']
mx, my, mz = Q['muzzle']
add(part('sphere', 'skull', (0, hy, hz), (1.05 * hr, 1.1 * hr, 0.95 * hr), segments=10), 'scale' if V in ('lizard', 'crocodile') else 'coat', 'head')
for side, x in (('L', 1), ('R', -1)):
    ex = (0.55 if V not in ('horse', 'unicorn', 'deer') else 0.7) * hr * x
    add(part('sphere', f'eye.{side}', (ex, hy - 0.75 * hr, hz + 0.2 * hr), 0.16 * hr, segments=6), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (ex * 1.05, hy - 0.85 * hr, hz + 0.2 * hr), 0.09 * hr, segments=6), 'pupil', 'head')
    if V == 'rabbit':
        add(part('cone', f'ear.{side}', (0.3 * hr * x, hy + 0.15 * hr, hz + 1.6 * hr), (0.2 * hr, 0.08 * hr, 1.0 * hr), rot=(math.radians(-15), math.radians(10 * x), 0), segments=5), 'coat', 'head')
    if V in ('pig', 'sheep', 'cow'):
        add(part('sphere', f'ear.{side}', (0.85 * hr * x, hy + 0.1 * hr, hz + 0.45 * hr), (0.35 * hr, 0.12 * hr, 0.2 * hr), rot=(0, math.radians(-25 * x), 0), segments=6), 'pink' if V == 'pig' else 'coat', 'head')
    if V == 'cow':
        add(part('cone', f'horn.{side}', (0.65 * hr * x, hy + 0.1 * hr, hz + 0.75 * hr), (0.1 * hr, 0.1 * hr, 0.45 * hr), rot=(0, math.radians(60 * x), 0), segments=5), 'horn', 'head')
    if V in ('cat', 'lion', 'bear', 'rat', 'rat_king'):
        er = {'cat': 0.38, 'lion': 0.3, 'bear': 0.32, 'rat': 0.5, 'rat_king': 0.45}[V] * hr
        add(part('sphere', f'ear.{side}', (0.62 * hr * x, hy + 0.1 * hr, hz + 0.85 * hr), (er, er * 0.35, er), segments=8), 'pink' if V.startswith('rat') else 'coat', 'head')
    if V in ('deer', 'horse', 'unicorn'):
        add(part('cone', f'ear.{side}', (0.45 * hr * x, hy + 0.2 * hr, hz + 0.95 * hr), (0.18 * hr, 0.1 * hr, 0.45 * hr), rot=(math.radians(-15), math.radians(15 * x), 0), segments=4), 'coat', 'head')
    if V == 'deer':
        # antlers: a beam swept back and up, with tines
        base = (0.35 * hr * x, hy + 0.1 * hr, hz + 0.9 * hr)
        add(part('cone', f'antler.{side}', (base[0] + 0.18 * hr * x, base[1] + 0.25 * hr, base[2] + 0.6 * hr), (0.08 * hr, 0.08 * hr, 0.85 * hr),
                 rot=(math.radians(-25), math.radians(28 * x), 0), segments=5), 'antler', 'head')
        for j in range(3):
            add(part('cone', f'tine{j}.{side}', (base[0] + (0.25 + 0.15 * j) * hr * x, base[1] + (0.05 + 0.18 * j) * hr, base[2] + (0.5 + 0.35 * j) * hr), (0.05 * hr, 0.05 * hr, 0.35 * hr),
                     rot=(math.radians(-5), math.radians(10 * x), 0), segments=4), 'antler', 'head')
    # paws, claws and hooves
    for leg in ('fl3', 'hl3'):
        c = s.co(f'{leg}.{side}')
        if V in ('deer', 'horse', 'unicorn'):
            add(part('cyl', f'hoof.{leg}.{side}', (c.x, c.y, 0.045 * H), (0.065 * H * P['girth'] / 0.2, 0.065 * H * P['girth'] / 0.2, 0.045 * H), segments=6), 'hoof', f'{leg}.{side}')
        elif V in ('pig', 'sheep', 'cow'):
            lr = 0.24 * P['girth'] * P['leg'] ** 0.3
            add(part('cyl', f'hoof.{leg}.{side}', (c.x, c.y - 0.2 * lr, lr * 0.45), (lr * 1.05, lr * 1.05, lr * 0.45), segments=6), 'hoof', f'{leg}.{side}')
        else:
            lr = 0.24 * P['girth'] * P['leg'] ** 0.3          # the paw's radius (forms.quadruped)
            for j, dx in enumerate((-0.45, 0, 0.45)):
                add(part('cone', f'claw{j}.{leg}.{side}', (c.x + dx * lr, c.y - lr * 0.95, lr * 0.35), (lr * 0.22, lr * 0.45, lr * 0.22),
                         rot=(math.radians(90), 0, 0), segments=4), 'claw', f'{leg}.{side}')
# the nose, and each kind's own marks
add(part('sphere', 'nose', (0, my - 0.45 * hr, mz + 0.1 * hr), (0.3 * hr, 0.18 * hr, 0.2 * hr), segments=6), 'nose', 'muzzle')
if V == 'lion':
    add(part('ico', 'mane', (0, hy + 0.35 * hr, hz - 0.1 * hr), (2.1 * hr, 1.5 * hr, 2.0 * hr)), 'mane', 'neck')
    add(part('sphere', 'tuft', Q['tail'], 0.06, segments=6), 'mane', 'tail2')
if V in ('horse', 'unicorn'):
    nx, ny_, nz = Q['neck']
    for i in range(6):
        t = i / 5
        add(part('cone', f'mane{i}', (0, ny_ + (hy - ny_) * t + 0.06, nz + (hz - nz) * t + P['girth'] * 0.55), (0.04, 0.09, 0.12),
                 rot=(math.radians(-150), 0, 0), segments=4), 'mane' if V == 'horse' else 'belly', 'neck' if t < 0.7 else 'head')
    add(part('cone', 'tailhair', (Q['tail'][0], Q['tail'][1] + 0.05, Q['tail'][2] - 0.15), (0.07, 0.07, 0.3), segments=6), 'mane' if V == 'horse' else 'belly', 'tail2')
if V == 'unicorn':
    add(part('cone', 'horn', (0, hy - 0.35 * hr, hz + 1.4 * hr), (0.14 * hr, 0.14 * hr, 1.6 * hr), rot=(math.radians(-25), 0, 0), segments=8), 'horn', 'head')
if V == 'deer':
    add(part('sphere', 'flash', Q['tail'], (0.06, 0.04, 0.07), segments=6), 'belly', 'tail2')
if V in ('rat', 'rat_king'):
    for side, x in (('L', 1), ('R', -1)):
        add(part('cone', f'whisker.{side}', (0.3 * hr * x, my, mz), (0.006, 0.006, 0.25 * hr), rot=(0, math.radians(80 * x), 0), segments=3), 'dark', 'muzzle')
    add(part('cone', 'tooth', (0, my - 0.35 * hr, mz - 0.4 * hr), (0.08 * hr, 0.04 * hr, 0.2 * hr), rot=(math.radians(180), 0, 0), segments=4), 'tooth', 'muzzle')
if V == 'rat_king':
    for i in range(5):
        a = 2 * math.pi * i / 5
        add(part('cone', f'crown{i}', (0.45 * hr * math.cos(a), hy + 0.45 * hr * math.sin(a), hz + 1.1 * hr), (0.08 * hr, 0.08 * hr, 0.35 * hr), segments=4), 'gold', 'head')
    add(part('cyl', 'crownband', (0, hy, hz + 0.95 * hr), (0.55 * hr, 0.55 * hr, 0.12 * hr), segments=10), 'gold', 'head')
    add(part('cube', 'scar', (0.4 * hr, hy - 0.5 * hr, hz + 0.6 * hr), (0.05 * hr, 0.4 * hr, 0.04 * hr), rot=(0, 0, math.radians(30))), 'scar', 'head')
if V == 'crocodile':
    for side, x in (('L', 1), ('R', -1)):
        for j in range(4):
            add(part('cone', f'tooth{j}.{side}', (0.3 * hr * x, my + (0.1 + 0.4 * j) * hr * 0.8, mz - 0.35 * hr), (0.05 * hr, 0.05 * hr, 0.16 * hr),
                     rot=(math.radians(180), 0, 0), segments=4), 'tooth', 'muzzle' if j < 2 else 'head')
    for i in range(6):
        y = -0.3 + 0.28 * i
        add(part('cone', f'scute{i}', (0, y, H + P['girth'] * (0.75 - 0.08 * max(0, i - 3))), (0.05, 0.08, 0.06), segments=4), 'dark', 'chest' if i < 2 else ('spine' if i < 3 else ('hips' if i < 4 else 'tail0' if i < 5 else 'tail1')))
if V == 'pig':
    add(part('cyl', 'snout', (0, my - 0.35 * hr, mz), (0.32 * hr, 0.32 * hr, 0.1 * hr), rot=(math.radians(90), 0, 0), segments=8), 'pink', 'muzzle')
if V == 'sheep':
    # a fleece of woolly puffs over the back
    for i, (x, y, z) in enumerate(((0, -0.2, 0.28), (0.14, -0.05, 0.24), (-0.14, -0.05, 0.24), (0, 0.1, 0.3), (0.14, 0.22, 0.24), (-0.14, 0.22, 0.24), (0, 0.32, 0.26), (0, -0.32, 0.22))):
        add(part('sphere', f'wool{i}', (x * 1.15, y * 1.1, H + z * 0.12), 0.2, segments=8), 'belly', 'spine' if -0.1 < y < 0.2 else ('chest' if y <= -0.1 else 'hips'))
    add(part('ico', 'topknot', (0, hy + 0.2 * hr, hz + 0.75 * hr), 0.08), 'belly', 'head')
if V == 'rabbit':
    add(part('ico', 'puff', Q['tail'], 0.06), 'belly', 'tail2')
if V == 'cow':
    for i, (x, y) in enumerate(((0.2, -0.1), (-0.18, 0.15), (0.15, 0.3), (-0.2, -0.25))):
        add(part('sphere', f'patch{i}', (x * 1.2, y, H + 0.15), (0.12, 0.14, 0.12), segments=8), 'dark', 'spine' if -0.1 < y < 0.2 else ('chest' if y <= -0.1 else 'hips'))
if V == 'bear':
    add(part('sphere', 'snoutpale', (0, my + 0.2 * hr, mz - 0.05 * hr), (0.45 * hr, 0.6 * hr, 0.4 * hr), segments=8), 'belly', 'muzzle')

boss = V == 'rat_king'
body = finish_body(body, arm, parts, budget=4000 if boss else 2900)

c = Clips(arm)
walk = {'rabbit': 16, 'pig': 24, 'sheep': 26, 'cow': 34, 'cat': 26, 'lion': 30, 'bear': 34, 'rat': 18, 'rat_king': 22, 'deer': 28, 'horse': 30, 'unicorn': 30, 'lizard': 20, 'crocodile': 30}[V]
quadruped_clips(c, gaits, walk=walk, swing=18 if P.get('sprawl') else 24, lift=25 if P.get('sprawl') else 35, height=H)

mhb.export(arm, body, V, opt['out'], kind='boss' if boss else 'creature', clips=c.names,
           meta={'for': V + '; tinted by bestiary.js', **({'ref': 'length'} if V in ('lizard', 'crocodile') else {})})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', walk // 4), ('Run', 3), ('Bite_Front', 10), ('Death', 999)))
