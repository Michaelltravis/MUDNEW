"""Swimmers: a body that bends side to side as it swims, fins, a forked tail. Variants:
  fish   fish, trout, carp, piranhas, anglers: a deep body, round eye, small fins
  shark  sharks, barracudas: long and sleek, a tall dorsal fin, a crescent tail, a toothy jaw
Pale with a lighter belly so bestiary tints colour them. Sized by length (index ref).
    tools/art3d/blender/run.sh models/fish.py --preview [--variant shark]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips, gaits

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'fish'
SH = V == 'shark'
pal = Palette(V, {
    'scale': ['#e8eef2', '#b8c6d0', '#f6f8fa'], 'fin': ['#d8e2ea', '#a8b8c6', '#7a8c9c'], 'eye': '#141418',
    'iris': '#f0e8c0', 'tooth': '#f8f4ea', 'gill': '#8a98a6',
})
L = 1.6 if SH else 0.8
g = 0.11 if SH else 0.12

s = Skel(V)
s.node('body', (0, -0.05 * L, 0.2), g * 1.15, sx=0.75)
s.node('head', (0, -0.3 * L, 0.2), g * (0.85 if SH else 1.0), 'body', sx=0.75)
s.node('snout', (0, -0.45 * L, 0.19 if SH else 0.2), g * 0.4, 'head', sx=0.8)
s.node('tail0', (0, 0.15 * L, 0.2), g * 0.8, 'body', sx=0.7)
s.node('tail1', (0, 0.32 * L, 0.2), g * 0.4, 'tail0', sx=0.7)
s.node('tail2', (0, 0.44 * L, 0.2), g * 0.18, 'tail1', sx=0.8)
body = s.hull(subdiv=1, branch_smoothing=0.5)
pal.paint_ramp(body, 'scale')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

ty = 0.44 * L
# the tail: forked for a fish, a tall crescent for a shark
tail = [(0, ty - 0.02, 0.2), (0, ty + 0.12 * L ** 0.5, 0.2 + (0.2 if SH else 0.13)), (0, ty + 0.05, 0.2), (0, ty + 0.1 * L ** 0.5, 0.2 - (0.13 if SH else 0.13))]
add(poly('tailfin', tail, [(0, 1, 2), (0, 2, 3)], 0.012), 'fin', 'tail2')
# the dorsal fin
dz = 0.2 + g * 0.8
dorsal = [(0, -0.12 * L, dz), (0, 0.0 * L, dz + (0.22 if SH else 0.08)), (0, 0.08 * L, dz - 0.01)]
add(poly('dorsal', dorsal, [(0, 1, 2)], 0.012), 'fin', 'body')
for side, x in (('L', 1), ('R', -1)):
    # pectoral fins, eyes, gills
    add(poly(f'pec.{side}', [(0.08 * x, -0.2 * L, 0.15), ((0.2 if SH else 0.13) * x, -0.12 * L, 0.08), (0.08 * x, -0.12 * L, 0.15)], [(0, 1, 2)], 0.01), 'fin', 'body')
    ex = g * 0.62 * x
    add(part('sphere', f'eye.{side}', (ex, -0.36 * L, 0.23), g * (0.18 if SH else 0.3), segments=8), 'iris' if not SH else 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (ex * 1.08, -0.37 * L, 0.23), g * (0.12 if SH else 0.16), segments=6), 'eye', 'head')
    if SH:
        for j in range(3):
            add(part('cube', f'gill{j}.{side}', (g * 0.7 * x, -0.25 * L + 0.04 * j, 0.2), (0.005, 0.008, g * 0.4)), 'gill', 'head')
if SH:
    for j in range(5):
        a = math.radians(-40 + 20 * j)
        add(part('cone', f'tooth{j}', (g * 0.35 * math.sin(a), -0.44 * L + 0.02 * abs(j - 2), 0.15), (0.012, 0.012, 0.03), rot=(math.radians(180), 0, 0), segments=3), 'tooth', 'snout')

body = finish_body(body, arm, parts, budget=2200)

CHAIN = ['tail0', 'tail1', 'tail2']
c = Clips(arm)
with c.clip('Idle', 40, loop=True) as k:
    gaits.slither(k, 40, CHAIN, amp=10)
    k.loc('body', 20, y=0.02).rot('head', 10, z=4).rot('head', 30, z=-4)
with c.clip('Walk', 20, loop=True) as k:
    gaits.slither(k, 20, ['head', 'body'] + CHAIN, amp=18, waves=0.8)
with c.clip('Bite_Front', 16) as k:
    k.rot('head', 5, x=-15).loc('body', 5, z=0.05).rot('head', 9, x=12).loc('body', 9, z=-0.1 * L).rot('head', 16).loc('body', 16)
with c.clip('HitRecieve', 10) as k:
    k.rot('body', 3, z=20).rot('tail1', 3, z=-25)
with c.clip('Death', 30) as k:
    # belly up, drifting down
    k.rot('body', 18, z=150).rot('body', 30, z=178).loc('body', 30, y=-0.05)

mhb.export(arm, body, V, opt['out'], kind='creature', clips=c.names,
           meta={'for': ('sharks, barracudas' if SH else 'fish, piranhas, anglers') + '; tinted by bestiary.js', 'ref': 'length'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 5), ('Walk', 15), ('Bite_Front', 9), ('Death', 999)))
