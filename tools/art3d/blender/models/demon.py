"""Fiends and their lesser kin, on the humanoid frame with wings, horns and a tail. Variants:
  demon   devils, demons, succubi, gargoyles: lean and horned, bat wings, a barbed tail, clawed;
          pale so bestiary tints make red devils or stone gargoyles
  fiend   the balor, pit fiend, demon lords and the Cinder Tyrant (bosses): huge, great sweeping
          wings, a crown of horns, burning eyes, a glowing chest
  imp     imps, quasits, gremlins: small, big-headed, pointed ears, little wings
  kobold  kobolds: small, a lizard-dog snout, a tail, no wings
    tools/art3d/blender/run.sh models/demon.py --preview [--variant fiend|imp|kobold]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits
from mhb.forms import humanoid, humanoid_clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'demon'
P = {
    'demon': dict(height=2.0, girth=0.95, shoulders=1.1, arms=1.1, legs=1.05, hunch=0.12, head=0.95),
    'fiend': dict(height=3.0, girth=1.25, shoulders=1.35, arms=1.1, legs=1.0, hunch=0.15, head=0.95, belly=1.05),
    'imp': dict(height=0.9, girth=0.95, shoulders=0.9, arms=1.0, legs=0.85, hunch=0.1, head=1.6),
    'kobold': dict(height=1.1, girth=0.9, shoulders=0.9, arms=1.0, legs=0.9, hunch=0.2, head=1.35),
}[V]
WINGS = {'demon': 1.0, 'fiend': 1.5, 'imp': 0.7, 'kobold': 0}[V]
pal = Palette(V, {
    'skin': ['#ecdcd2', '#c8aea0', '#9a7e70'], 'wing': ['#d8c4b8', '#a88e80', '#6e5a50'],
    'horn': ['#3a3230', '#262020', '#141010'], 'claw': '#1e1a18', 'eye': '#ffe060' if V != 'fiend' else '#ffb040',
    'pupil': '#1a0a08', 'glow': '#ffa040', 'belly': ['#f4e4d4', '#d8c0aa', '#b09a86'],
})

s = Skel(V)
L = humanoid(s, **P)
H = P['height']
cz, hz, hy = L['chest_z'], L['head_z'], L['head_y']
if WINGS:
    for side, x in (('L', 1), ('R', -1)):
        s.node(f'w0.{side}', (0.09 * H * x, 0.08 * H, cz + 0.04 * H), 0.035 * H, 'chest')
        s.node(f'w1.{side}', (0.42 * H * WINGS * x, 0.22 * H, cz + 0.3 * H * WINGS), 0.022 * H, f'w0.{side}')
        s.node(f'w2.{side}', (0.78 * H * WINGS * x, 0.3 * H, cz + 0.12 * H * WINGS), 0.012 * H, f'w1.{side}')
s.node('tail0', (0, 0.12 * H, L['hip_z'] - 0.02 * H), 0.03 * H, 'hips')
s.node('tail1', (0, 0.3 * H, L['hip_z'] * 0.55), 0.022 * H, 'tail0')
s.node('tail2', (0, 0.45 * H, 0.06 * H), 0.014 * H, 'tail1')
if V == 'kobold':
    s.node('snout', (0, hy - 0.1 * H, hz - 0.02 * H), 0.04 * H, 'head')
body = s.hull(subdiv=1, branch_smoothing=0.4)
pal.paint_ramp(body, 'skin')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

r = 0.075 * H * P['head']
add(part('sphere', 'skull', (0, hy, hz), (1.05 * r, 1.1 * r, 1.05 * r), segments=12), 'skin', 'head')
for side, x in (('L', 1), ('R', -1)):
    add(part('sphere', f'eye.{side}', (0.38 * r * x, hy - 0.9 * r, hz + 0.12 * r), 0.16 * r, segments=6), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.4 * r * x, hy - 1.0 * r, hz + 0.12 * r), 0.08 * r, segments=6), 'pupil', 'head')
    if V in ('demon', 'fiend'):
        n = 2 if V == 'demon' else 3
        for i in range(n):
            add(part('cone', f'horn{i}.{side}', ((0.45 + 0.2 * i) * r * x, hy + 0.1 * r * i, hz + (0.8 - 0.15 * i) * r),
                     ((0.22 - 0.04 * i) * r, (0.22 - 0.04 * i) * r, (1.0 - 0.2 * i) * r),
                     rot=(math.radians(-35 - 10 * i), math.radians((25 + 20 * i) * x), 0), segments=6), 'horn', 'head')
    if V == 'imp':
        add(part('cone', f'ear.{side}', (1.0 * r * x, hy, hz + 0.25 * r), (0.15 * r, 0.06 * r, 0.6 * r), rot=(0, math.radians(70 * x), 0), segments=4), 'skin', 'head')
        add(part('cone', f'horn.{side}', (0.35 * r * x, hy - 0.2 * r, hz + 0.85 * r), (0.1 * r, 0.1 * r, 0.3 * r), segments=5), 'horn', 'head')
    if V == 'kobold':
        add(part('cone', f'ear.{side}', (0.6 * r * x, hy + 0.2 * r, hz + 0.6 * r), (0.15 * r, 0.08 * r, 0.45 * r), rot=(math.radians(-30), math.radians(25 * x), 0), segments=4), 'skin', 'head')
    hand = s.co(f'arm2.{side}')
    for j in range(3):
        add(part('cone', f'claw{j}.{side}', (hand.x + (j - 1) * 0.02 * H, hand.y - 0.03 * H, hand.z - 0.04 * H), (0.007 * H, 0.007 * H, 0.03 * H),
                 rot=(math.radians(180), 0, 0), segments=4), 'claw', f'arm2.{side}')
    if WINGS:
        sh, el, tip = s.co(f'w0.{side}'), s.co(f'w1.{side}'), s.co(f'w2.{side}')
        low_mid = (0.38 * H * WINGS * x, 0.3 * H, cz - 0.15 * H * WINGS)
        low_out = (0.7 * H * WINGS * x, 0.36 * H, cz - 0.08 * H * WINGS)
        add(poly(f'web0.{side}', [sh, el, low_mid, (0.08 * H * x, 0.12 * H, cz - 0.12 * H)], [(0, 1, 2, 3)], 0.008 * H), 'wing', f'w1.{side}')
        add(poly(f'web1.{side}', [el, tip, low_out, low_mid], [(0, 1, 2, 3)], 0.008 * H), 'wing', f'w2.{side}')
# the tail's barb, the belly, and the fiend's burning heart
add(part('cone', 'barb', (0, 0.5 * H, 0.05 * H), (0.035 * H, 0.05 * H, 0.012 * H), rot=(math.radians(-90), 0, 0), segments=3), 'horn', 'tail2')
add(part('sphere', 'belly', (0, -0.11 * H * P['girth'], L['hip_z'] + (cz - L['hip_z']) * 0.45), (0.1 * H * P['girth'], 0.04 * H, 0.14 * H), segments=8), 'belly', 'spine')
if V == 'kobold':
    add(part('sphere', 'muzzle', (0, hy - 0.13 * H, hz - 0.03 * H), (0.5 * r, 0.7 * r, 0.42 * r), segments=8), 'skin', 'snout')
if V == 'fiend':
    add(part('ico', 'heart', (0, -0.15 * H, cz + 0.02 * H), 0.05 * H), 'glow', 'chest')

body = finish_body(body, arm, parts, budget=6000 if V == 'fiend' else 2900)

def more(name, k, frames):
    # wings beat slowly at rest, faster on the move, flare in a roar; the tail sways
    if WINGS and name in ('Idle', 'Walk', 'Run', 'Bite_InPlace'):
        up, down = {'Idle': (12, -10), 'Walk': (20, -16), 'Run': (30, -24), 'Bite_InPlace': (45, -5)}[name]
        gaits.flap(k, frames, wings=('w1', 'w2'), up=up, down=down)
    if name in ('Idle', 'Walk', 'Run'):
        k.rot('tail1', frames // 4, z=15).rot('tail1', 3 * frames // 4, z=-15).rot('tail2', frames // 4 + 2, z=20).rot('tail2', 3 * frames // 4 + 2, z=-20)


c = Clips(arm)
humanoid_clips(c, gaits, frames_walk=28 if V in ('imp', 'kobold') else 32, swing=26, arm=24, heavy=1.3 if V == 'fiend' else 1.0, more=more, height=H)

mhb.export(arm, body, V, opt['out'], kind='boss' if V == 'fiend' else 'creature', clips=c.names,
           meta={'for': {'demon': 'demons, devils, succubi, gargoyles', 'fiend': 'the balor, pit fiend, demon lords, the Cinder Tyrant',
                         'imp': 'imps, quasits, gremlins', 'kobold': 'kobolds'}[V] + '; tinted by bestiary.js',
                 **({'look': {'glow': 0.12}} if V == 'fiend' else {})})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 8), ('Bite_Front', 8), ('Bite_InPlace', 12), ('Death', 999)))
