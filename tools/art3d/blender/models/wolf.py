"""The wolf: a lean four-legged hunter, long muzzle, pointed ears, a ruff at the neck and a bushy
tail. Its coat is pale so the game's tints make it a grey wolf, a hellhound or a jackal
(bestiary.js); the belly and muzzle stay lighter, the nose and eyes dark.
    tools/art3d/blender/run.sh models/wolf.py --preview
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips

mhb.reset()
opt = mhb.args()
NAME = 'wolf'

pal = Palette(NAME, {
    'coat': ['#d6d2ca', '#a29e96', '#e8e0d0'],     # light back, mid flanks, pale belly
    'ruff': ['#f0ece2', '#cfc9bc', '#a8a296'],
    'ear': '#8a857c', 'nose': '#1e1b1a', 'eye': '#f0c040', 'pupil': '#141210',
    'claw': '#3a3530', 'tailtip': '#f4f0e8',
})

s = Skel(NAME)
# spine: hips at the back, chest forward (-Y is the wolf's front)
s.node('hips', (0, 0.32, 0.62), 0.19, sx=1.05)
s.node('spine', (0, 0.04, 0.64), 0.21, 'hips', sx=1.05)
s.node('chest', (0, -0.25, 0.66), 0.25, 'spine', sx=0.95)
s.node('neck', (0, -0.46, 0.8), 0.17, 'chest', sx=1.1)
s.node('head', (0, -0.62, 0.88), 0.135, 'neck', sx=1.1)
s.node('muzzle', (0, -0.81, 0.83), 0.07, 'head', sx=0.95)
# legs: shoulder/hip, knee, ankle, paw
for side, x in (('L', 1), ('R', -1)):
    s.node(f'fl0.{side}', (0.13 * x, -0.27, 0.52), 0.11, 'chest')
    s.node(f'fl1.{side}', (0.13 * x, -0.29, 0.3), 0.07, f'fl0.{side}')
    s.node(f'fl2.{side}', (0.13 * x, -0.3, 0.08), 0.05, f'fl1.{side}')
    s.node(f'fl3.{side}', (0.13 * x, -0.37, 0.04), 0.052, f'fl2.{side}')
    s.node(f'hl0.{side}', (0.13 * x, 0.36, 0.5), 0.13, 'hips')
    s.node(f'hl1.{side}', (0.13 * x, 0.45, 0.29), 0.075, f'hl0.{side}')
    s.node(f'hl2.{side}', (0.13 * x, 0.39, 0.09), 0.05, f'hl1.{side}')
    s.node(f'hl3.{side}', (0.13 * x, 0.32, 0.04), 0.052, f'hl2.{side}')
s.node('tail0', (0, 0.52, 0.66), 0.075, 'hips')
s.node('tail1', (0, 0.7, 0.58), 0.105, 'tail0')
s.node('tail2', (0, 0.85, 0.46), 0.09, 'tail1')

body = s.hull(subdiv=1, branch_smoothing=0.4)
pal.paint_ramp(body, 'coat')
arm = s.armature()

parts = []
def add(p, key, bone, flat=True):
    pal.paint(p, key)
    parts.append((p, bone))

for side, x in (('L', 1), ('R', -1)):
    # ears: tall, pointed, a little apart and tipped back
    add(part('cone', f'ear.{side}', (0.075 * x, -0.58, 1.02), (0.05, 0.03, 0.085), rot=(math.radians(-15), math.radians(14 * x), 0), segments=4), 'ear', 'head')
    add(part('sphere', f'eye.{side}', (0.068 * x, -0.71, 0.92), 0.024, segments=8), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.073 * x, -0.726, 0.92), 0.013, segments=6), 'pupil', 'head')
    for leg in ('fl3', 'hl3'):
        y = s.co(f'{leg}.{side}').y - 0.045
        add(part('cone', f'claw.{leg}.{side}', (0.13 * x, y - 0.01, 0.022), (0.014, 0.024, 0.014), rot=(math.radians(90), 0, 0), segments=4), 'claw', f'{leg}.{side}')
add(part('sphere', 'nose', (0, -0.875, 0.85), (0.036, 0.03, 0.028), segments=8), 'nose', 'muzzle')
# the ruff: a shaggy collar round the neck and shoulders, and the pale tail tip
add(part('ico', 'ruff', (0, -0.43, 0.76), (0.23, 0.16, 0.22)), 'ruff', 'neck')
add(part('ico', 'tailtip', (0, 0.93, 0.38), (0.065, 0.08, 0.065)), 'tailtip', 'tail2')

body = finish_body(body, arm, parts, budget=2800)

LEGS = ('fl', 'hl')
c = Clips(arm)

with c.clip('Idle', 60, loop=True) as k:
    k.loc('hips', 30, y=0.008).rot('chest', 30, x=2)
    k.rot('neck', 20, z=8).rot('neck', 45, z=-6).rot('head', 30, x=-4)
    k.rot('tail1', 15, z=10).rot('tail1', 45, z=-10).rot('tail2', 15, z=14).rot('tail2', 45, z=-14)

def gait(k, frames, swing, lift, bob, name_speed=1.0):
    # a trot: the front left and back right step together, then the other pair
    h = frames // 2
    for f, a in ((0, 1), (h, -1)):
        for side, sgn in (('L', 1), ('R', -1)):
            k.rot(f'fl1.{side}', f, x=swing * a * sgn).rot(f'hl1.{side}', f, x=-swing * a * sgn)
    for side, at in (('L', h // 2), ('R', h + h // 2)):
        # the lifted leg folds at the knee mid-swing
        k.rot(f'fl2.{side}', at, x=-lift).rot(f'hl2.{side}', (at + h) % frames, x=lift)
    k.loc('hips', h // 2, y=bob).loc('hips', h + h // 2, y=bob)
    k.rot('head', h // 2, x=3).rot('head', h + h // 2, x=3)
    k.rot('tail1', h // 2, z=8).rot('tail1', h + h // 2, z=-8)

with c.clip('Walk', 28, loop=True) as k:
    gait(k, 28, 24, 35, 0.02)
with c.clip('Run', 16, loop=True) as k:
    gait(k, 16, 40, 55, 0.05)
    k.rot('spine', 4, x=6).rot('spine', 12, x=-6)

with c.clip('Bite_Front', 20) as k:
    # gather back, then lunge: neck and head thrust forward and snap
    k.rot('spine', 6, x=-8).rot('neck', 6, x=-18).rot('head', 6, x=-12).loc('hips', 6, y=-0.04)
    for side in ('L', 'R'):
        k.rot(f'hl1.{side}', 6, x=12).rot(f'fl1.{side}', 6, x=-10)
    k.rot('spine', 10, x=6).rot('neck', 10, x=28).rot('head', 10, x=18).loc('chest', 10, z=-0.06)
    for side in ('L', 'R'):
        k.rot(f'fl1.{side}', 10, x=18)
    k.rot('neck', 13, x=20).rot('head', 13, x=-6)
    k.rot('spine', 20).rot('neck', 20).rot('head', 20).loc('chest', 20).loc('hips', 20)
with c.clip('Bite_InPlace', 30) as k:
    # a howl: head up, then back down
    k.rot('neck', 10, x=-40).rot('head', 10, x=-25).rot('neck', 22, x=-42).rot('head', 22, x=-28)
    k.rot('tail1', 10, x=-10)
with c.clip('HitRecieve', 12) as k:
    k.rot('spine', 3, x=-10, z=6).rot('neck', 3, x=-22).rot('head', 3, x=-14).loc('hips', 3, x=0.03)
with c.clip('Death', 40) as k:
    # legs give way, it slumps and rolls onto its side, head last
    k.loc('hips', 10, y=-0.12).rot('neck', 10, x=12)
    for side in ('L', 'R'):
        k.rot(f'fl1.{side}', 10, x=25).rot(f'hl1.{side}', 10, x=-25)
    k.rot('hips', 24, z=-75).loc('hips', 24, y=-0.38, x=0.05).rot('spine', 24, z=-8)
    k.rot('hips', 40, z=-88).loc('hips', 40, y=-0.45, x=0.06).rot('neck', 40, x=8, z=-14).rot('head', 40, x=10)
    for side in ('L', 'R'):
        k.rot(f'fl1.{side}', 40, x=30).rot(f'fl2.{side}', 40, x=-20).rot(f'hl1.{side}', 40, x=-30).rot(f'hl2.{side}', 40, x=20)
    k.rot('tail1', 40, z=-15)

mhb.export(arm, body, NAME, opt['out'], kind='creature', clips=c.names, meta={'for': 'wolves, wargs, dogs of war; tinted by bestiary.js'})
if opt['preview']:
    mhb.preview(arm, body, NAME, opt['out'], poses=(('Idle', 0), ('Walk', 7), ('Run', 4), ('Bite_Front', 10), ('Death', 999)))
