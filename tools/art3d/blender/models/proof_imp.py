"""The pipeline's proof: a small horned imp, built, rigged, animated and exported by the mhb helpers.
    tools/art3d/blender/run.sh models/proof_imp.py --preview
"""
import mhb
from mhb import Skel, Palette, part, finish_body, Clips

mhb.reset()
opt = mhb.args()
NAME = 'proof_imp'

pal = Palette(NAME, {'skin': '#c8553d', 'belly': '#e8a87c', 'horn': '#f2e6c8', 'eye': '#ffe66d', 'dark': '#3a2420'})

s = Skel(NAME)
s.node('hips', (0, 0, 0.42), 0.13, sx=1.2)
s.node('chest', (0, 0.01, 0.62), 0.15, 'hips', sx=1.15)
s.node('neck', (0, 0, 0.76), 0.07, 'chest')
s.node('head', (0, -0.02, 0.9), 0.15, 'neck')
for side, x in (('L', 1), ('R', -1)):
    s.node(f'arm.{side}', (0.17 * x, 0, 0.68), 0.05, 'chest')
    s.node(f'fore.{side}', (0.24 * x, -0.03, 0.5), 0.045, f'arm.{side}')
    s.node(f'hand.{side}', (0.26 * x, -0.06, 0.38), 0.05, f'fore.{side}')
    s.node(f'thigh.{side}', (0.08 * x, 0, 0.3), 0.07, 'hips')
    s.node(f'shin.{side}', (0.09 * x, 0.02, 0.12), 0.055, f'thigh.{side}')
    s.node(f'foot.{side}', (0.09 * x, -0.06, 0.03), 0.045, f'shin.{side}')
s.node('tail0', (0, 0.14, 0.4), 0.04, 'hips')
s.node('tail1', (0, 0.3, 0.48), 0.025, 'tail0')

body = s.hull(subdiv=1)
pal.paint_ramp(body, 'skin')
arm = s.armature()

parts = []
for side, x in (('L', 1), ('R', -1)):
    h = part('cone', f'horn.{side}', (0.07 * x, 0.0, 1.06), (0.03, 0.03, 0.08), rot=(0.3, 0.35 * x, 0))
    pal.paint(h, 'horn')
    parts.append((h, 'head'))
    e = part('sphere', f'eye.{side}', (0.06 * x, -0.13, 0.93), 0.028)
    pal.paint(e, 'eye')
    parts.append((e, 'head'))
belly = part('sphere', 'belly', (0, -0.1, 0.52), (0.1, 0.06, 0.12))
pal.paint(belly, 'belly')
parts.append((belly, 'chest'))
body = finish_body(body, arm, parts, budget=2500)

c = Clips(arm)
with c.clip('Idle', 40, loop=True) as k:
    k.loc('hips', 20, z=0.015).rot('head', 20, x=6).rot('tail1', 20, z=20)
with c.clip('Walk', 24, loop=True) as k:
    for f, a in ((0, 1), (12, -1)):
        k.rot('thigh.L', f, x=30 * a).rot('thigh.R', f, x=-30 * a)
        k.rot('arm.L', f, x=-25 * a).rot('arm.R', f, x=25 * a)
    k.loc('hips', 6, z=0.03).loc('hips', 18, z=0.03)
with c.clip('Bite_Front', 18) as k:
    k.rot('chest', 6, x=-20).rot('arm.L', 6, x=-70).rot('arm.R', 6, x=-70)
    k.rot('chest', 10, x=25).rot('arm.L', 10, x=40).rot('arm.R', 10, x=40)
with c.clip('HitRecieve', 12) as k:
    k.rot('chest', 4, x=-25).rot('head', 4, x=-15)
with c.clip('Death', 30) as k:
    k.rot('hips', 12, x=-40).loc('hips', 12, z=-0.1)
    k.rot('hips', 30, x=-85).loc('hips', 30, z=-0.3)

mhb.export(arm, body, NAME, opt['out'], kind='creature', clips=c.names)
if opt['preview']:
    mhb.preview(arm, body, NAME, opt['out'])
