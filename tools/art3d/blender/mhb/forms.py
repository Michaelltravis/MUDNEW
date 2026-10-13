"""Body plans shared by several creature scripts. humanoid() lays out a two-legged, two-armed
skeleton from a few proportions; the bone names are the ones gaits.biped and the deaths expect:
hips (root), spine, chest, neck, head; arm0/arm1/arm2 (shoulder, elbow, hand) and leg0/leg1/
leg2/leg3 (hip, knee, ankle, toe) on each side (.L at +x)."""


def humanoid(s, height=2.0, girth=1.0, shoulders=1.0, arms=1.0, legs=1.0, hunch=0.0, head=1.0, neck=1.0, belly=1.0):
    """Proportions are multipliers of an ordinary build ~`height` metres tall; hunch (0..1) bends
    the back forward and pushes the head out in front of the chest, as a troll stands."""
    H = height
    hip_z = 0.48 * H * legs / (0.48 * legs + 0.52)
    top = H - 0.12 * H * head
    chest_z = hip_z + (top - hip_z) * 0.62
    g = girth
    s.node('hips', (0, 0, hip_z), 0.11 * H * g * belly, sx=1.15)
    s.node('spine', (0, -0.05 * H * hunch, hip_z + (chest_z - hip_z) * 0.5), 0.125 * H * g * belly, 'hips', sx=1.1)
    s.node('chest', (0, -0.14 * H * hunch, chest_z), 0.14 * H * g, 'spine', sx=1.25 * shoulders)
    nz = chest_z + 0.11 * H * neck - 0.04 * H * hunch
    s.node('neck', (0, -0.22 * H * hunch, nz), 0.05 * H * g * neck, 'chest')
    s.node('head', (0, -0.27 * H * hunch - 0.01 * H, nz + 0.08 * H * head), 0.075 * H * head, 'neck')
    sw = 0.17 * H * shoulders * g
    for side, x in (('L', 1), ('R', -1)):
        al = 0.36 * H * arms
        s.node(f'arm0.{side}', (sw * x, -0.14 * H * hunch, chest_z + 0.04 * H), 0.06 * H * g, 'chest')
        s.node(f'arm1.{side}', ((sw + 0.04 * H) * x, -0.14 * H * hunch - 0.02 * H, chest_z + 0.04 * H - al * 0.5), 0.045 * H * g, f'arm0.{side}')
        s.node(f'arm2.{side}', ((sw + 0.05 * H) * x, -0.14 * H * hunch - 0.06 * H, chest_z + 0.04 * H - al), 0.05 * H * g, f'arm1.{side}')
        lx = 0.07 * H * g
        s.node(f'leg0.{side}', (lx * x, 0, hip_z - 0.02 * H), 0.07 * H * g, 'hips')
        s.node(f'leg1.{side}', (lx * x, -0.01 * H, hip_z * 0.52), 0.05 * H * g, f'leg0.{side}')
        # ankle and toe sit on the ground whatever the build: their centres at their own radius
        s.node(f'leg2.{side}', (lx * x, 0.01 * H, max(0.05 * H, 0.042 * H * g)), 0.04 * H * g, f'leg1.{side}')
        s.node(f'leg3.{side}', (lx * x, -0.07 * H, 0.035 * H * g), 0.035 * H * g, f'leg2.{side}')
    return {'hip_z': hip_z, 'chest_z': chest_z, 'head_z': nz + 0.08 * H * head, 'head_y': -0.27 * H * hunch - 0.01 * H,
            'sw': sw, 'hand_z': chest_z + 0.04 * H - 0.36 * H * arms}


def humanoid_clips(c, gaits, frames_walk=32, swing=26, arm=22, heavy=1.0, fall=85, more=None, height=2.0):
    """The usual clips for a two-legged body: idle breathing, walk and run, a two-handed
    overhead smash, a roar, a flinch, and a fall onto its face. `heavy` slows and deepens it.
    more(name, k, frames), if given, adds keys inside each clip (a demon's wings, a tail)."""
    with c.clip('Idle', 60, loop=True) as k:
        k.rot('chest', 30, x=3).rot('head', 15, z=8).rot('head', 45, z=-6)
        for side, sgn in (('L', 1), ('R', -1)):
            k.rot(f'arm0.{side}', 30, z=-3 * sgn)
        if more:
            more('Idle', k, 60)
    with c.clip('Walk', frames_walk, loop=True) as k:
        gaits.biped(k, frames_walk, swing=swing, lift=30, arm=arm, bob=0.015 * height * heavy, torso='chest')
        if more:
            more('Walk', k, frames_walk)
    with c.clip('Run', max(12, frames_walk // 2), loop=True) as k:
        gaits.biped(k, max(12, frames_walk // 2), swing=swing * 1.4, lift=45, arm=arm * 1.5, bob=0.025 * height * heavy, torso='chest')
        k.rot('spine', 4, x=10)
        if more:
            more('Run', k, max(12, frames_walk // 2))
    with c.clip('Bite_Front', int(24 * heavy)) as k:
        t = int(24 * heavy)
        X = (1, 0, 0)
        # both arms raised overhead, then brought down in a smash
        for side in ('L', 'R'):
            k.turn(f'arm0.{side}', t // 3, X, -150).turn(f'arm1.{side}', t // 3, X, -25)
            k.turn(f'arm0.{side}', t // 2, X, -35).turn(f'arm1.{side}', t // 2, X, -10)
        k.rot('chest', t // 3, x=-12).rot('chest', t // 2, x=22).rot('spine', t // 2, x=10)
        k.rot('chest', t).rot('spine', t)
        for side in ('L', 'R'):
            k.rot(f'arm0.{side}', t).rot(f'arm1.{side}', t)
        if more:
            more('Bite_Front', k, int(24 * heavy))
    with c.clip('Bite_InPlace', 36) as k:
        # a roar: chest out, arms flung wide, head back
        k.rot('chest', 12, x=-14).rot('head', 12, x=-22)
        for side, sgn in (('L', 1), ('R', -1)):
            k.turn(f'arm0.{side}', 12, (0, 1, 0), -60 * sgn).turn(f'arm0.{side}', 12, (1, 0, 0), -30)
        k.rot('chest', 26, x=-16).rot('head', 26, x=-24)
        k.rot('chest', 36).rot('head', 36)
        for side in ('L', 'R'):
            k.rot(f'arm0.{side}', 36)
        if more:
            more('Bite_InPlace', k, 36)
    with c.clip('HitRecieve', 14) as k:
        k.rot('chest', 4, x=-16, z=10).rot('head', 4, x=-12).loc('hips', 4, z=0.025 * height)
        if more:
            more('HitRecieve', k, 14)
    with c.clip('Death', 44) as k:
        gaits.crumple(k, 44, root='hips', drop=0.25 * height, fall=fall, torso='chest',
                      limbs=[(f'leg1.{s_}', 20) for s_ in ('L', 'R')])
        for s_ in ('L', 'R'):
            k.turn(f'arm0.{s_}', 44, (1, 0, 0), -25)
        if more:
            more('Death', k, 44)


def quadruped(s, length=1.0, height=0.6, girth=0.2, leg=1.0, neck=0.35, neck_up=0.6, head=0.12, muzzle=0.12,
              tail=0.45, tail_r=0.05, tail_droop=0.5, sprawl=0.0, hump=0.0, width=1.0):
    """A four-legged body: `height` at the shoulder, `length` nose-to-rump-ish, `girth` the chest's
    radius. Bones: hips (root), spine, chest, neck, head, muzzle; fl0-3/hl0-3 per side; tail0-2.
    `sprawl` (0..1) turns the legs out to the sides (lizards, crocodiles); `hump` raises the
    shoulders (bears)."""
    L, Hs, g = length, height, girth
    w = (0.55 * g + 0.5 * sprawl * g) * width
    s.node('hips', (0, 0.32 * L, Hs - 0.02), 0.8 * g, sx=1.05 * width)
    s.node('spine', (0, 0.04 * L, Hs + 0.02 + 0.3 * hump * g), 0.92 * g, 'hips', sx=1.05 * width)
    s.node('chest', (0, -0.24 * L, Hs + 0.03 + 0.6 * hump * g), g, 'spine', sx=1.0 * width)
    ny, nz = -0.24 * L - neck * 0.5, Hs + 0.03 + neck * neck_up * 0.7 + 0.3 * hump * g
    s.node('neck', (0, ny, nz), 0.62 * g, 'chest', sx=1.05)
    hy_, hz_ = ny - neck * 0.45 - head * 0.3, nz + neck * neck_up * 0.35 + head * 0.2
    s.node('head', (0, hy_, hz_), head, 'neck', sx=1.05)
    s.node('muzzle', (0, hy_ - head * 0.8 - muzzle, hz_ - head * 0.35), head * 0.48, 'head', sx=1.0)
    lr = 0.24 * g * leg ** 0.3
    for side, x in (('L', 1), ('R', -1)):
        fy, hy2 = -0.24 * L, 0.32 * L
        out = sprawl * 0.9 * Hs
        s.node(f'fl0.{side}', (w * x, fy, Hs - 0.35 * g), 0.5 * g, 'chest')
        s.node(f'fl1.{side}', ((w + out) * x, fy - 0.01, Hs * 0.5 * (1 - 0.5 * sprawl)), lr, f'fl0.{side}')
        s.node(f'fl2.{side}', ((w + out) * x, fy - 0.02, 0.06 * Hs + lr * 0.4), lr * 0.72, f'fl1.{side}')
        s.node(f'fl3.{side}', ((w + out) * x, fy - 0.07 * Hs - lr, lr * 0.8), lr * 0.8, f'fl2.{side}')
        s.node(f'hl0.{side}', (w * x, hy2, Hs - 0.3 * g), 0.58 * g, 'hips')
        s.node(f'hl1.{side}', ((w + out) * x, hy2 + 0.12 * Hs * (1 - sprawl), Hs * 0.48 * (1 - 0.5 * sprawl)), lr * 1.1, f'hl0.{side}')
        s.node(f'hl2.{side}', ((w + out) * x, hy2 + 0.03, 0.08 * Hs + lr * 0.4), lr * 0.72, f'hl1.{side}')
        s.node(f'hl3.{side}', ((w + out) * x, hy2 - 0.05 * Hs - lr, lr * 0.8), lr * 0.8, f'hl2.{side}')
    ty = 0.32 * L + 0.7 * g
    s.node('tail0', (0, ty, Hs - 0.02), tail_r * 1.1, 'hips')
    s.node('tail1', (0, ty + tail * 0.5, max(tail_r * 1.05, Hs - 0.02 - tail * 0.45 * tail_droop)), tail_r, 'tail0')
    s.node('tail2', (0, ty + tail, max(tail_r * 0.75, Hs - 0.02 - tail * 0.9 * tail_droop)), tail_r * 0.7, 'tail1')
    return {'head': (0, hy_, hz_), 'head_r': head, 'muzzle': (0, hy_ - head * 0.8 - muzzle, hz_ - head * 0.35),
            'neck': (0, ny, nz), 'chest': (0, -0.24 * L, Hs), 'tail': (0, ty + tail, max(tail_r * 0.75, Hs - 0.02 - tail * 0.9 * tail_droop))}


def quadruped_clips(c, gaits, walk=28, swing=24, lift=35, height=0.6, more=None, run=True):
    """The usual clips for a four-legged body: idle, trot, gallop, a lunge and bite, a rear-up
    roar, a flinch, and a roll onto its side."""
    H = height
    TAIL = ['tail1', 'tail2']
    def m(name, k, f):
        if more:
            more(name, k, f)
    with c.clip('Idle', 60, loop=True) as k:
        k.loc('hips', 30, y=0.012 * H).rot('chest', 30, x=2)
        k.rot('neck', 20, z=8).rot('neck', 45, z=-6).rot('head', 30, x=-4)
        for i, b in enumerate(TAIL):
            k.turn(b, 15, (0, 0, 1), 8 + 4 * i).turn(b, 45, (0, 0, 1), -8 - 4 * i)
        m('Idle', k, 60)
    with c.clip('Walk', walk, loop=True) as k:
        gaits.quad(k, walk, swing=swing, lift=lift, bob=0.03 * H, tail=TAIL, head='head')
        m('Walk', k, walk)
    if run:
        with c.clip('Run', max(12, walk * 4 // 7), loop=True) as k:
            f = max(12, walk * 4 // 7)
            gaits.quad(k, f, swing=swing * 1.6, lift=lift * 1.5, bob=0.07 * H, tail=TAIL, head='head')
            k.rot('spine', f // 4, x=6).rot('spine', 3 * f // 4, x=-6)
            m('Run', k, f)
    with c.clip('Bite_Front', 20) as k:
        k.rot('spine', 6, x=-8).rot('neck', 6, x=-18).rot('head', 6, x=-12).loc('hips', 6, y=-0.06 * H)
        k.rot('spine', 10, x=6).rot('neck', 10, x=28).rot('head', 10, x=18).loc('chest', 10, z=-0.1 * H)
        k.rot('neck', 13, x=20).rot('head', 13, x=-6)
        k.rot('spine', 20).rot('neck', 20).rot('head', 20).loc('chest', 20).loc('hips', 20)
        m('Bite_Front', k, 20)
    with c.clip('Bite_InPlace', 32) as k:
        # rear up and roar (a horse rears, a bear stands, a cat snarls)
        k.rot('hips', 10, x=-14).loc('hips', 10, z=0.1 * H).rot('neck', 10, x=-30).rot('head', 10, x=-20)
        k.rot('hips', 22, x=-16).loc('hips', 22, z=0.1 * H).rot('neck', 22, x=-32)
        k.rot('hips', 32).loc('hips', 32).rot('neck', 32).rot('head', 32)
        m('Bite_InPlace', k, 32)
    with c.clip('HitRecieve', 12) as k:
        k.rot('spine', 3, x=-10, z=6).rot('neck', 3, x=-22).rot('head', 3, x=-14).loc('hips', 3, x=0.04 * H)
        m('HitRecieve', k, 12)
    with c.clip('Death', 40) as k:
        gaits.roll_over(k, 40, root='hips', drop=0.75 * H, side=-1, neck='neck',
                        limbs=[(f'fl1.{s_}', 30) for s_ in ('L', 'R')] + [(f'hl1.{s_}', -30) for s_ in ('L', 'R')])
        m('Death', k, 40)
