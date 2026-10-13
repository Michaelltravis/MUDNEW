"""Motion shared by the creature scripts: gaits, breathing, wing beats and deaths, keyed onto a
clip (`with c.clip('Walk', 28, loop=True) as k: gaits.quad(k, 28, ...)`). Bones are named by the
scripts' conventions: limbs as <prefix><segment>.<L|R> (fl1.L is the front left upper leg),
chains as <prefix><index> (tail1, neck0)."""
import math

SIDES = (('L', 1), ('R', -1))


def quad(k, frames, swing=24, lift=35, bob=0.02, root='hips', front='fl', hind='hl', tail=None, head=None):
    """A trot: the front left and back right step together, then the other pair; a lifted leg
    folds at the knee mid-swing, the body bobs twice a cycle, the tail sways."""
    h = frames // 2
    for f, a in ((0, 1), (h, -1)):
        for side, sgn in SIDES:
            k.rot(f'{front}1.{side}', f, x=swing * a * sgn).rot(f'{hind}1.{side}', f, x=-swing * a * sgn)
    for side, at in (('L', h // 2), ('R', h + h // 2)):
        k.rot(f'{front}2.{side}', at, x=-lift).rot(f'{hind}2.{side}', (at + h) % frames, x=lift)
    k.loc(root, h // 2, y=bob).loc(root, h + h // 2, y=bob)
    if head:
        k.rot(head, h // 2, x=3).rot(head, h + h // 2, x=3)
    for i, b in enumerate(tail or ()):
        k.rot(b, h // 2, z=6 + 3 * i).rot(b, h + h // 2, z=-6 - 3 * i)


def biped(k, frames, swing=28, lift=30, arm=24, bob=0.03, root='hips', leg='leg', arm_bone='arm', torso=None):
    """A walk on two legs, arms swinging against them. Turned about the body's own side-to-side
    axis (turn()), so it works whichever way the limb bones happen to point."""
    h = frames // 2
    X = (1, 0, 0)
    for f, a in ((0, 1), (h, -1)):
        for side, sgn in SIDES:
            k.turn(f'{leg}1.{side}', f, X, -swing * a * sgn)           # forward is -Y: a negative turn
            if arm_bone:
                k.turn(f'{arm_bone}1.{side}', f, X, arm * a * sgn)
    for side, at in (('L', h // 2), ('R', h + h // 2)):
        k.turn(f'{leg}2.{side}', at, X, lift)                        # the shin folds back
    k.loc(root, h // 2, y=bob).loc(root, h + h // 2, y=bob)
    if torso:
        k.rot(torso, h // 2, z=4).rot(torso, h + h // 2, z=-4)


def legs(k, frames, pairs, swing=22, lift=18, prefix='leg', root=None, bob=0.0):
    """A wave gait for many legs (a spider's eight, an insect's six): alternate legs on each side
    step together, the two sides out of step. Leg n's upper segment is <prefix>n1.<side>; it
    swings about the vertical and lifts as it comes forward (turn(): whichever way it points)."""
    h = frames // 2
    for n in range(pairs):
        for side, sgn in SIDES:
            bone = f'{prefix}{n}1.{side}'
            b = k.arm.data.bones[bone]
            d = (b.tail_local - b.head_local)
            out = (d.x, d.y, 0.0)
            ax = (-out[1], out[0], 0.0)                    # horizontal, across the leg: lifts it
            a = 1 if (n + (0 if side == 'L' else 1)) % 2 == 0 else -1
            k.turn(bone, 0, (0, 0, 1), swing * a)
            k.turn(bone, h, (0, 0, 1), -swing * a)
            up = h // 2 if a > 0 else h + h // 2
            k.turn(bone, up, ax, -lift)
    if root and bob:
        k.loc(root, h // 2, y=bob).loc(root, h + h // 2, y=bob)


def slither(k, frames, chain, amp=22, waves=1.0, root=None, lift=0.0):
    """A travelling wave down a chain of bones: each later bone lags, the whole body undulates."""
    n = len(chain)
    steps = 4
    for s in range(steps):
        f = int(frames * s / steps)
        for i, b in enumerate(chain):
            ph = 2 * math.pi * (s / steps - waves * i / max(1, n))
            k.turn(b, f, (0, 0, 1), amp * math.sin(ph))
    if root and lift:
        k.loc(root, frames // 4, y=lift).loc(root, 3 * frames // 4, y=lift)


def float_(k, frames, root, bob=0.06, sway=None, amp=6):
    """Hovering: rise and fall, and a slow sway down the given bones (a ghost's tail, its arms)."""
    k.loc(root, frames // 4, y=bob).loc(root, 3 * frames // 4, y=-bob * 0.5)
    for i, b in enumerate(sway or ()):
        a = amp + 3 * i
        k.rot(b, frames // 4 + i, z=a).rot(b, 3 * frames // 4 + i, z=-a)


def flap(k, frames, wings=('w1', 'w2'), up=40, down=-30):
    """Wing beats: the inner bone of each wing raised and lowered about the body's front-to-back
    axis, the outer following a little behind."""
    h = frames // 2
    inner, outer = wings
    Y = (0, 1, 0)
    for side, sgn in SIDES:
        k.turn(f'{inner}.{side}', 0, Y, -up * sgn).turn(f'{inner}.{side}', h, Y, -down * sgn)
        k.turn(f'{outer}.{side}', min(frames - 1, 2), Y, -up * 0.5 * sgn).turn(f'{outer}.{side}', min(frames - 1, h + 2), Y, -down * 0.5 * sgn)


def roll_over(k, frames, root='hips', drop=0.4, side=-1, limbs=(), neck=None):
    """Death on four legs: the legs give way, it slumps and rolls onto its side."""
    a = frames // 4
    k.loc(root, a, y=-drop * 0.3)
    k.rot(root, frames * 2 // 3, z=80 * side).loc(root, frames * 2 // 3, y=-drop * 0.9, x=0.05)
    k.rot(root, frames, z=88 * side).loc(root, frames, y=-drop, x=0.06)
    for b, deg in limbs:
        k.rot(b, frames, x=deg)
    if neck:
        k.rot(neck, frames, x=10, z=-14)


def crumple(k, frames, root='hips', drop=0.5, fall=-85, limbs=(), torso=None):
    """Death on two legs: knees buckle, then it falls forward (fall<0) or back (fall>0) flat."""
    a = frames // 3
    k.loc(root, a, y=-drop * 0.35).rot(root, a, x=fall * 0.15)
    if torso:
        k.rot(torso, a, x=fall * 0.2)
    k.rot(root, frames, x=fall).loc(root, frames, y=-drop)
    for b, deg in limbs:
        k.rot(b, frames, x=deg)
