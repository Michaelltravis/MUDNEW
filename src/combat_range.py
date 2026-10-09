"""Distance in combat (combat v2, 3D client).

Positions are metres inside a room (x 0..24 east, z 0..15 south, the 3D client's layout).
The web client reports where its hero stands; the server moves the creatures in a fight
(melee closes in, archers and casters keep their distance) and every blow, skill and spell
checks range. Telnet players have no position and are always treated as in reach, so
nothing changes for them.

Design (owner: "think about the classes and what ranges make sense"):
  melee classes (warrior, paladin, cleric, thief, assassin, bard) swing at 2.5 m and close
  gaps with charges, trips and throws; the ranger shoots from up to 16 m and fights poorly
  point-blank; mages and necromancers throw a weak bolt from 10 m and cast from 14-20 m,
  but their touch spells need 2.5 m; heals, blessings and songs reach allies at 12-15 m;
  shouts and novas hit everything around the user, area spells everything around a point.
"""
import math

MELEE = 2.5          # a sword's reach, edge to edge, generous for a top-down view
POINT_BLANK = 3.0    # too close to draw a bow well

# the ordinary blow, by class: (reach in metres, ranged?)
AUTO_RANGE = {
    'warrior': (MELEE, False), 'paladin': (MELEE, False), 'cleric': (MELEE, False),
    'thief': (MELEE, False), 'assassin': (MELEE, False), 'bard': (MELEE, False),
    'ranger': (16.0, True), 'mage': (10.0, True), 'necromancer': (10.0, True),
}

# per ability: (range in metres, shape)
#   'melee' / 'ranged' — hits the target if within range
#   'self'             — no target needed
#   'nova:R'           — everything within R of the user
#   'blast:R'          — everything within R of the target (target within range)
#   'cone:R'           — everything within R in front of the user (90 degrees)
#   'dash'             — closes from up to range to melee (charge)
ABILITY_RANGE = {
    # warrior
    'bash': (MELEE, 'melee'), 'cleave': (MELEE + 0.5, 'cone:3'), 'kick': (MELEE, 'melee'),
    'execute': (MELEE, 'melee'), 'rally': (0, 'nova:8'), 'rescue': (6.0, 'ranged'),
    'charge': (15.0, 'dash'),
    # paladin
    'censure': (MELEE, 'melee'), 'order_verdict': (MELEE, 'melee'), 'holy_smite': (14.0, 'ranged'),
    'absolution': (12.0, 'ranged'), 'halo_of_reckoning': (0, 'nova:5'), 'turn_undead': (8.0, 'cone:8'),
    # ranger
    'truesight_shot': (18.0, 'ranged'), 'wildbond_strike': (MELEE, 'melee'), 'loosing_storm': (16.0, 'blast:3.5'),
    'quarry_mark': (20.0, 'ranged'), 'call_lightning': (16.0, 'ranged'),
    # thief / assassin
    'backstab': (MELEE, 'melee'), 'circle': (MELEE, 'melee'), 'trip': (MELEE, 'melee'), 'low_blow': (MELEE, 'melee'),
    'pocket_sand': (5.0, 'ranged'), 'jackpot': (MELEE, 'melee'), 'mark': (15.0, 'ranged'), 'expose': (MELEE, 'melee'),
    'vital': (MELEE, 'melee'), 'feint': (MELEE, 'melee'), 'execute_contract': (MELEE, 'melee'), 'fade': (0, 'self'),
    # mage
    'magic_missile': (18.0, 'ranged'), 'fireball': (16.0, 'blast:3'), 'lightning_bolt': (18.0, 'ranged'),
    'chill_touch': (MELEE, 'melee'), 'sleep': (12.0, 'ranged'), 'towerbolt': (20.0, 'ranged'),
    # necromancer
    'soul_bolt': (16.0, 'ranged'), 'soul_siphon': (10.0, 'ranged'), 'animate_dead': (0, 'self'),
    'soul_reap': (14.0, 'blast:4'),
    # cleric
    'cure_light': (12.0, 'ranged'), 'heal': (12.0, 'ranged'), 'bless': (12.0, 'ranged'),
    'flamestrike': (14.0, 'blast:3'),
    # bard
    'mockery': (14.0, 'ranged'), 'fascinate': (12.0, 'ranged'), 'crescendo': (0, 'nova:6'),
    'discordant_note': (7.0, 'cone:7'),
}
DEFAULT_SPELL = (14.0, 'ranged')
DEFAULT_SKILL = (MELEE, 'melee')

# creatures: reach by role (mob_ai roles), and the distance they like to keep
ROLE_RANGE = {
    'archer': (15.0, 9.0), 'caster': (13.0, 8.0), 'healer': (12.0, 8.0), 'support': (12.0, 8.0),
}
MOB_MELEE = 2.2
MOB_SPEED = 3.4      # m/s closing in
ROOM_W, ROOM_H = 24.0, 15.0


def key(name):
    return str(name or '').strip().lower().replace(' ', '_').replace("'", '')


def ability_range(name, is_spell=False):
    return ABILITY_RANGE.get(key(name)) or (DEFAULT_SPELL if is_spell else DEFAULT_SKILL)


def auto_range(ch):
    return AUTO_RANGE.get(str(getattr(ch, 'char_class', '') or '').lower(), (MELEE, False))


def mob_reach(mob):
    """(reach, preferred distance) for a creature."""
    try:
        from map_system import _mob_roles
        roles = set(_mob_roles(mob))
    except Exception:
        roles = set()
    for role, rng in ROLE_RANGE.items():
        if role in roles:
            return rng
    return (MOB_MELEE, MOB_MELEE * 0.8)


# ---- positions ----
def pos_of(ch):
    """(x, z) in the combatant's current room, or None if unknown (telnet players)."""
    p = getattr(ch, 'web_pos', None)
    room = getattr(ch, 'room', None)
    if not p or not room or p[0] != getattr(room, 'vnum', None):
        return None
    return (p[1], p[2])


def set_pos(ch, x, z):
    room = getattr(ch, 'room', None)
    if room is None:
        return
    x = max(1.0, min(ROOM_W - 1.0, float(x)))
    z = max(1.0, min(ROOM_H - 1.0, float(z)))
    ch.web_pos = (room.vnum, x, z)


def distance(a, b):
    """Metres between two combatants, or None when either has no position."""
    pa, pb = pos_of(a), pos_of(b)
    if pa is None or pb is None:
        return None
    return math.hypot(pa[0] - pb[0], pa[1] - pb[1])


def in_reach(a, b, reach):
    d = distance(a, b)
    return True if d is None else d <= reach


def within(center, others, radius):
    """Combatants within radius of a point (x, z); unknown positions count as inside."""
    out = []
    for o in others:
        p = pos_of(o)
        if p is None or math.hypot(p[0] - center[0], p[1] - center[1]) <= radius:
            out.append(o)
    return out


def mob_seed(room, mobs):
    """Adopt the client's placement of creatures that have no position yet (both clients
    compute the same spots from the room layout, so the first report is as good as any)."""
    by_id = {}
    try:
        from map_system import _mob_uid
        for ch in getattr(room, 'characters', []) or []:
            if not hasattr(ch, 'account_name'):
                by_id[_mob_uid(ch)] = ch
    except Exception:
        return
    for m in mobs[:40]:
        try:
            mob = by_id.get(int(m.get('id')))
            if mob is not None and pos_of(mob) is None:
                set_pos(mob, float(m.get('x')), float(m.get('z')))
        except (TypeError, ValueError, AttributeError):
            continue
