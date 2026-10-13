"""Dragons: a four-legged, winged great beast with a long neck and tail, horns swept back and a
ridge of spines. Variants:
  dragon      the common dragon: pale scales so the game's tints colour it (red, black, green...)
  frost_wyrm  Vyrkothas the Frost Wyrm (a boss): icy blue, white belly, more horns and spines
    tools/art3d/blender/run.sh models/dragon.py --preview [--variant frost_wyrm]
"""
import math

import mhb
from mhb import Skel, Palette, part, poly, finish_body, Clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'dragon'
VARIANTS = {
    'dragon': dict(kind='creature', budget=3000, horns=2, spines=7, colours={
        'scale': ['#d8cfc4', '#b4a99c', '#e8dcc4'], 'belly': ['#f0e4c8', '#dccaa4', '#b8a37c'],
        'wing': ['#c9b8a8', '#a89584', '#8a7666'], 'bone': '#efe6d2', 'horn': '#3a332e',
        'spine': '#5a4e44', 'eye': '#ffd04a', 'pupil': '#1a1410', 'claw': '#2a2420'}),
    'frost_wyrm': dict(kind='boss', budget=6000, horns=4, spines=11, colours={
        'scale': ['#cfe6f4', '#7fa8c8', '#4a6f92'], 'belly': ['#f4fbff', '#dcecf6', '#b0c8dc'],
        'wing': ['#d8ecf8', '#9cc0dc', '#6a90b4'], 'bone': '#e8f4fc', 'horn': '#eaf6ff',
        'spine': '#bfe4fa', 'eye': '#7af0ff', 'pupil': '#0a1a2a', 'claw': '#d0e4f0'}),
}
cfg = VARIANTS[V]
pal = Palette(V, cfg['colours'])

s = Skel(V)
s.node('hips', (0, 0.5, 1.0), 0.46, sx=1.05)
s.node('belly', (0, 0.0, 1.06), 0.56, 'hips', sx=1.08)
s.node('chest', (0, -0.5, 1.18), 0.5, 'belly', sx=1.02)
s.node('neck0', (0, -0.86, 1.52), 0.31, 'chest')
s.node('neck1', (0, -1.06, 1.86), 0.24, 'neck0')
s.node('neck2', (0, -1.16, 2.14), 0.21, 'neck1')
s.node('head', (0, -1.34, 2.3), 0.25, 'neck2', sx=1.15)
s.node('snout', (0, -1.78, 2.2), 0.14, 'head', sx=1.15)
s.node('tail0', (0, 0.98, 0.98), 0.32, 'hips')
s.node('tail1', (0, 1.45, 0.84), 0.21, 'tail0')
s.node('tail2', (0, 1.95, 0.62), 0.12, 'tail1')
s.node('tail3', (0, 2.4, 0.42), 0.075, 'tail2')
s.node('tail4', (0, 2.78, 0.3), 0.045, 'tail3')
WING = {}
for side, x in (('L', 1), ('R', -1)):
    s.node(f'fl0.{side}', (0.42 * x, -0.55, 0.9), 0.23, 'chest')
    s.node(f'fl1.{side}', (0.5 * x, -0.6, 0.5), 0.17, f'fl0.{side}')
    s.node(f'fl2.{side}', (0.5 * x, -0.62, 0.12), 0.13, f'fl1.{side}')
    s.node(f'fl3.{side}', (0.5 * x, -0.84, 0.09), 0.13, f'fl2.{side}')
    s.node(f'hl0.{side}', (0.46 * x, 0.55, 0.86), 0.32, 'hips')
    s.node(f'hl1.{side}', (0.54 * x, 0.8, 0.48), 0.2, f'hl0.{side}')
    s.node(f'hl2.{side}', (0.54 * x, 0.62, 0.13), 0.13, f'hl1.{side}')
    s.node(f'hl3.{side}', (0.54 * x, 0.42, 0.09), 0.14, f'hl2.{side}')
    # the wing's arm: shoulder, elbow, finger tip
    s.node(f'w0.{side}', (0.38 * x, -0.36, 1.6), 0.14, 'chest')
    s.node(f'w1.{side}', (1.15 * x, -0.2, 2.15), 0.09, f'w0.{side}')
    s.node(f'w2.{side}', (2.2 * x, 0.15, 2.45), 0.05, f'w1.{side}')

body = s.hull(subdiv=1, branch_smoothing=0.5)
pal.paint_ramp(body, 'scale')
arm = s.armature()

parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

for side, x in (('L', 1), ('R', -1)):
    # the membrane: inner (shoulder to elbow, down to the flank) and outer (elbow to tip, swept
    # back), each riding its own bone of the wing so it folds and beats with it
    sh, el, tip = s.co(f'w0.{side}'), s.co(f'w1.{side}'), s.co(f'w2.{side}')
    back_mid, back_out, flank = (1.05 * x, 0.85, 1.38), (1.95 * x, 0.75, 1.72), (0.4 * x, 0.5, 1.35)
    add(poly(f'web0.{side}', [sh, el, back_mid, flank], [(0, 1, 2, 3)], 0.025), 'wing', f'w1.{side}')
    add(poly(f'web1.{side}', [el, tip, back_out, back_mid], [(0, 1, 2, 3)], 0.025), 'wing', f'w2.{side}')
    add(part('cone', f'wclaw.{side}', (el.x, el.y, el.z + 0.1), (0.035, 0.035, 0.09), segments=4), 'bone', f'w1.{side}')
    # horns: swept back from the brow (a frost wyrm has a second, smaller pair)
    for i in range(cfg['horns'] // 2):
        add(part('cone', f'horn{i}.{side}', ((0.13 + 0.07 * i) * x, -1.2 + 0.13 * i, 2.5 - 0.07 * i), (0.065 - 0.015 * i, 0.065 - 0.015 * i, 0.26 - 0.06 * i),
                 rot=(math.radians(-62), math.radians(16 * x), 0), segments=5), 'horn', 'head')
    add(part('sphere', f'eye.{side}', (0.16 * x, -1.47, 2.37), 0.05, segments=8), 'eye', 'head')
    add(part('sphere', f'pupil.{side}', (0.18 * x, -1.5, 2.37), 0.027, segments=6), 'pupil', 'head')
    for leg in ('fl3', 'hl3'):
        c = s.co(f'{leg}.{side}')
        for j, dx in enumerate((-0.05, 0.0, 0.05)):
            add(part('cone', f'claw{j}.{leg}.{side}', (c.x + dx * 1.3, c.y - 0.15, 0.04), (0.028, 0.06, 0.028), rot=(math.radians(90), 0, 0), segments=4), 'claw', f'{leg}.{side}')
# belly plates and the ridge of spines down the back and tail
add(part('sphere', 'belly', (0, -0.15, 0.8), (0.38, 0.72, 0.2), segments=10), 'belly', 'belly')
ridge = [('neck1', -1.04, 2.07), ('neck0', -0.8, 1.8), ('chest', -0.45, 1.68), ('belly', 0.0, 1.62), ('hips', 0.45, 1.46),
         ('tail0', 0.98, 1.3), ('tail1', 1.45, 1.06), ('tail2', 1.95, 0.76), ('tail3', 2.4, 0.5), ('neck2', -1.16, 2.33), ('tail4', 2.7, 0.37)]
for i, (bone, y, z) in enumerate(ridge[:cfg['spines']]):
    h = 0.16 if bone in ('chest', 'belly', 'hips') else 0.11
    add(part('cone', f'spine{i}', (0, y, z), (0.05, 0.08, h), rot=(math.radians(-20), 0, 0), segments=4), 'spine', bone)
add(part('cone', 'tailblade', (0, 2.92, 0.28), (0.12, 0.16, 0.03), rot=(math.radians(-80), 0, 0), segments=3), 'spine', 'tail4')

body = finish_body(body, arm, parts, budget=cfg['budget'])

c = Clips(arm)
def wings(k, f, up, fold=0.0):
    for side, sgn in (('L', 1), ('R', -1)):
        k.rot(f'w1.{side}', f, y=up * sgn, x=fold).rot(f'w2.{side}', f, y=up * 0.6 * sgn)

with c.clip('Idle', 48, loop=True) as k:
    # a slow beat holding it aloft, the tail swaying, the head turning
    wings(k, 0, 22); wings(k, 24, -28)
    k.loc('belly', 12, y=0.03).loc('belly', 36, y=-0.02)
    k.rot('neck1', 24, z=8).rot('head', 24, x=-6)
    for i, a in enumerate((6, 9, 12, 14)):
        k.rot(f'tail{i + 1}', 12, z=a).rot(f'tail{i + 1}', 36, z=-a)

def gait(k, frames, swing, beat):
    h = frames // 2
    for f, a in ((0, 1), (h, -1)):
        for side, sgn in (('L', 1), ('R', -1)):
            k.rot(f'fl1.{side}', f, x=swing * a * sgn).rot(f'hl1.{side}', f, x=-swing * a * sgn)
        wings(k, f, beat * a)
    k.loc('belly', h // 2, y=0.04).loc('belly', h + h // 2, y=0.04)
    for i in range(1, 5):
        k.rot(f'tail{i}', h // 2, z=6 + i * 2).rot(f'tail{i}', h + h // 2, z=-6 - i * 2)

with c.clip('Walk', 36, loop=True) as k:
    gait(k, 36, 18, 16)
with c.clip('Run', 20, loop=True) as k:
    gait(k, 20, 28, 34)

with c.clip('Bite_Front', 26) as k:
    # rear back, then strike down with the jaws, wings flared
    k.rot('neck0', 8, x=-20).rot('neck1', 8, x=-20).rot('head', 8, x=-15); wings(k, 8, 40)
    k.rot('neck0', 13, x=28).rot('neck1', 13, x=22).rot('head', 13, x=12).loc('chest', 13, z=-0.15)
    k.rot('neck0', 26).rot('neck1', 26).rot('head', 26).loc('chest', 26); wings(k, 26, 0)
with c.clip('Bite_InPlace', 36) as k:
    # rear up and breathe: head raised, chest out, then the breath forward
    k.rot('belly', 10, x=-14).rot('neck0', 10, x=-25).rot('head', 10, x=-20); wings(k, 10, 50)
    k.rot('neck0', 18, x=10).rot('neck1', 18, x=10).rot('head', 18, x=6)
    k.rot('neck0', 30, x=12).rot('neck1', 30, x=10).rot('head', 30, x=8)
    k.rot('belly', 36).rot('neck0', 36).rot('neck1', 36).rot('head', 36); wings(k, 36, 0)
with c.clip('HitRecieve', 14) as k:
    k.rot('neck0', 4, x=-18, z=10).rot('head', 4, x=-14).rot('belly', 4, z=-6); wings(k, 4, 30)
with c.clip('Death', 54) as k:
    # wings fold, the legs give, and it rolls onto its side, neck and tail falling last
    wings(k, 12, -60, fold=30)
    k.loc('hips', 16, y=-0.25).rot('neck0', 16, x=15)
    k.rot('hips', 34, z=-80).loc('hips', 34, y=-0.62, x=0.1)
    k.rot('hips', 54, z=-88).loc('hips', 54, y=-0.7, x=0.12)
    # wings swept back and laid along the flanks, not left standing up
    for side, sgn in (('L', 1), ('R', -1)):
        for f in (30, 54):
            k.aim(f'w1.{side}', f, (0.45 * sgn, 0.85, -0.25)).aim(f'w2.{side}', f, (0.2 * sgn, 1.0, -0.35))
    k.rot('neck0', 54, x=20, z=-18).rot('neck1', 54, x=18, z=-10).rot('head', 54, x=12)
    for side in ('L', 'R'):
        k.rot(f'fl1.{side}', 54, x=30).rot(f'fl2.{side}', 54, x=-25).rot(f'hl1.{side}', 54, x=-25).rot(f'hl2.{side}', 54, x=25)
    for i in range(1, 5):
        k.rot(f'tail{i}', 54, z=-8)

mhb.export(arm, body, V, opt['out'], kind=cfg['kind'], clips=c.names,
           meta={'for': 'dragons; tinted by bestiary.js' if V == 'dragon' else 'Vyrkothas the Frost Wyrm'})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Idle', 24), ('Bite_Front', 13), ('Bite_InPlace', 18), ('Death', 999)))
