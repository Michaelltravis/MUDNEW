"""Things with tentacles. Variants:
  mindflayer  mind flayers, illithids: a tall robed figure whose face is four writhing tentacles,
              a domed head, long-fingered hands
  overmind    the Master Mindflayer (a boss): taller, a high collar, a glowing brow
  horror      krakens, octopi, otyughs, aboleths, aberrations: a bulbous mantle with great eyes on
              eight coiling tentacles
Pale so bestiary tints colour them.
    tools/art3d/blender/run.sh models/tentacle.py --preview --variant mindflayer
"""
import math

import mhb
from mhb import Skel, Palette, part, finish_body, Clips, gaits
from mhb.forms import humanoid, humanoid_clips

mhb.reset()
opt = mhb.args()
V = opt['variant'] or 'mindflayer'
pal = Palette(V, {
    'skin': ['#e4d8e8', '#bcaac4', '#8c7a98'], 'robe': ['#5a4a6a', '#3e3050', '#241a34'], 'trim': ['#e0c070', '#b08a40', '#7a5a20'],
    'eye': '#f4f0ff', 'pupil': '#1a1020', 'glow': '#b080ff', 'sucker': '#f0d8e0', 'mantle': ['#e8dcd0', '#c0aea0', '#8e7c70'],
})

s = Skel(V)
parts = []
def add(p, key, bone):
    pal.paint(p, key)
    parts.append((p, bone))

if V in ('mindflayer', 'overmind'):
    big = V == 'overmind'
    H = 2.4 if big else 2.0
    L = humanoid(s, height=H, girth=0.85, shoulders=0.95, arms=1.15, legs=1.1, hunch=0.05, head=1.15)
    hz, hy, r = L['head_z'], L['head_y'], 0.075 * H * 1.15
    for i, a in enumerate((-50, -15, 15, 50)):
        x = 0.35 * r * math.sin(math.radians(a))
        s.node(f'tent{i}a', (x, hy - 0.75 * r, hz - 0.45 * r), 0.16 * r, 'head')
        s.node(f'tent{i}b', (x * 1.1, hy - 0.85 * r, hz - 1.1 * r), 0.11 * r, f'tent{i}a')
        s.node(f'tent{i}c', (x * 1.2, hy - 0.8 * r, hz - 1.7 * r), 0.06 * r, f'tent{i}b')
    body = s.hull(subdiv=1, branch_smoothing=0.4)
    pal.paint_ramp(body, 'skin')
    arm = s.armature()
    add(part('sphere', 'dome', (0, hy + 0.1 * r, hz + 0.1 * r), (1.0 * r, 1.25 * r, 1.15 * r), segments=12), 'skin', 'head')
    for side, x in (('L', 1), ('R', -1)):
        add(part('sphere', f'eye.{side}', (0.42 * r * x, hy - 0.8 * r, hz + 0.15 * r), 0.2 * r, segments=8), 'eye', 'head')
        add(part('sphere', f'pupil.{side}', (0.45 * r * x, hy - 0.92 * r, hz + 0.15 * r), 0.1 * r, segments=6), 'pupil', 'head')
    # the robe: a long skirt from the waist, and a mantle on the shoulders
    add(part('cone', 'robe', (0, 0, L['hip_z'] * 0.5), (0.16 * H, 0.13 * H, L['hip_z'] * 0.52), segments=12), 'robe', 'hips')
    add(part('sphere', 'mantle', (0, 0, L['chest_z'] + 0.03 * H), (0.2 * H, 0.13 * H, 0.08 * H), segments=10), 'robe', 'chest')
    add(part('cyl', 'belt', (0, 0, L['hip_z'] + 0.02 * H), (0.12 * H, 0.1 * H, 0.015 * H), segments=12), 'trim', 'hips')
    if big:
        for i in range(5):
            a = math.radians(-70 + 35 * i)
            add(part('cone', f'collar{i}', (0.16 * H * math.sin(a), 0.06 * H * math.cos(a) + 0.03 * H, L['chest_z'] + 0.12 * H), (0.025 * H, 0.012 * H, 0.1 * H),
                     rot=(math.radians(-15), math.radians(25 * math.sin(a)), 0), segments=4), 'trim', 'chest')
        add(part('ico', 'brow', (0, hy - 0.85 * r, hz + 0.55 * r), 0.14 * r), 'glow', 'head')
    body = finish_body(body, arm, parts, budget=5000 if big else 2900)

    def more(name, k, frames):
        # the face tentacles never stop writhing
        for i in range(4):
            for j, seg in enumerate('abc'):
                a = 10 + 6 * j
                k.turn(f'tent{i}{seg}', (i * 3 + j * 2) % frames, (1, 0, 0), a).turn(f'tent{i}{seg}', (frames // 2 + i * 3 + j * 2) % frames, (1, 0, 0), -a)
    c = Clips(arm)
    humanoid_clips(c, gaits, frames_walk=34, swing=20, arm=14, heavy=1.0, more=more, height=H)
else:
    # the horror: a mantle on eight tentacles, each a chain that coils
    s.node('mantle', (0, 0.05, 0.72), 0.42, sx=1.05)
    s.node('crown', (0, 0.22, 1.08), 0.38, 'mantle', sx=1.05)
    s.node('face', (0, -0.22, 0.6), 0.22, 'mantle')
    TENTS = 8
    for i in range(TENTS):
        a = 2 * math.pi * (i + 0.5) / TENTS
        cx, cy = math.sin(a), -math.cos(a)
        s.node(f'arm{i}a', (0.3 * cx, 0.3 * cy, 0.45), 0.11, 'mantle')
        s.node(f'arm{i}b', (0.62 * cx, 0.62 * cy, 0.18), 0.075, f'arm{i}a')
        s.node(f'arm{i}c', (0.95 * cx, 0.95 * cy, 0.08), 0.05, f'arm{i}b')
        s.node(f'arm{i}d', (1.2 * cx, 1.2 * cy, 0.2), 0.025, f'arm{i}c')
    body = s.hull(subdiv=1, branch_smoothing=0.5)
    pal.paint_ramp(body, 'mantle')
    arm = s.armature()
    for side, x in (('L', 1), ('R', -1)):
        add(part('sphere', f'eye.{side}', (0.17 * x, -0.38, 0.72), 0.08, segments=8), 'eye', 'face')
        add(part('sphere', f'pupil.{side}', (0.18 * x, -0.44, 0.72), 0.04, segments=6), 'pupil', 'face')
    for i in range(TENTS):
        a = 2 * math.pi * (i + 0.5) / TENTS
        for j, f in enumerate((0.5, 0.8)):
            add(part('sphere', f'sucker{i}{j}', (f * math.sin(a), -f * math.cos(a), 0.06 if j else 0.13), 0.025, segments=5), 'sucker', f'arm{i}b' if j == 0 else f'arm{i}c')
    body = finish_body(body, arm, parts, budget=2900)
    c = Clips(arm)
    def coil(k, frames, amp):
        for i in range(TENTS):
            for j, seg in enumerate('bcd'):
                ph = frames * ((i / TENTS + j * 0.15) % 1)
                k.turn(f'arm{i}{seg}', int(ph) % frames, (0, 0, 1), amp).turn(f'arm{i}{seg}', int(ph + frames / 2) % frames, (0, 0, 1), -amp)
    with c.clip('Idle', 48, loop=True) as k:
        coil(k, 48, 12)
        k.loc('mantle', 24, y=0.04).rot('crown', 24, x=-8)
    with c.clip('Walk', 32, loop=True) as k:
        coil(k, 32, 22)
        k.loc('mantle', 8, y=0.06).loc('mantle', 24, y=0.06)
    with c.clip('Bite_Front', 22) as k:
        # two front tentacles lash out
        for i in (0, TENTS - 1):
            k.turn(f'arm{i}a', 6, (1, 0, 0), 40).turn(f'arm{i}a', 11, (1, 0, 0), -45).turn(f'arm{i}a', 22, (1, 0, 0), 0)
        k.rot('mantle', 6, x=-10).rot('mantle', 11, x=12).rot('mantle', 22)
    with c.clip('Bite_InPlace', 30) as k:
        k.loc('mantle', 10, y=0.25).rot('crown', 10, x=-20).loc('mantle', 30).rot('crown', 30)
        coil(k, 30, 30)
    with c.clip('HitRecieve', 12) as k:
        k.rot('mantle', 3, x=-14, z=10)
    with c.clip('Death', 40) as k:
        # it slumps, the tentacles go limp and spread
        k.loc('mantle', 20, y=-0.3).loc('mantle', 40, y=-0.45).rot('crown', 40, x=40)
        for i in range(TENTS):
            k.turn(f'arm{i}a', 40, (0, 0, 1), 8)

mhb.export(arm, body, V, opt['out'], kind='boss' if V == 'overmind' else 'creature', clips=c.names,
           meta={'for': {'mindflayer': 'mind flayers, illithids', 'overmind': 'the Master Mindflayer',
                         'horror': 'krakens, octopi, otyughs, aboleths, aberrations'}[V] + '; tinted by bestiary.js',
                 **({'look': {'glow': 0.1}} if V == 'overmind' else {})})
if opt['preview']:
    mhb.preview(arm, body, V, opt['out'], poses=(('Idle', 0), ('Walk', 8), ('Bite_Front', 11), ('Bite_InPlace', 12), ('Death', 999)))
