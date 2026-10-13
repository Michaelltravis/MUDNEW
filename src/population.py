"""Who lives where, zone by zone (world/population/zone_<n>.json), applied when the world loads,
after the zone files and before the first reset, so a rebuild of world/zones keeps it.

    {"zone": 220,
     "bosses": [{"vnum": 22070, "room": 14151, "mechanics": [{"type": "plague_pools"}], "why": "..."}],
                                                    # spawn here, and only here; fight mechanics
     "doors":  [{"room": 14150, "dir": "south", "key": 22051, "name": "inner gate"}]}   # locked to a key

Also "creatures" (prototypes by vnum: rank regular/elite/sub-boss, helpers {group, rooms, count}),
"spawns" [{vnum, rooms, max}] and "patrols" [{vnum, route}] (mobs.patrol_ai; allies.py).

A creature needs only its words, level and rank: health, blows, armour and experience left out
are worked out from them (numbers()). An entry for a creature the zone files already have, with
no "name", changes only what it gives (a rank, helpers) and keeps the rest.

A boss placed here spawns in its room and nowhere else in the world (its other resets go). A door
listed is closed and locked, opened by the key named (doors.py key_vnum).
"""
import glob
import json
import logging
import os

logger = logging.getLogger('Misthollow')
POP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'world', 'population')


RANK_HP = {'regular': 1.0, 'elite': 3.4, 'sub-boss': 6.5, 'boss': 11.0}
RANK_XP = {'regular': 2, 'elite': 8, 'sub-boss': 20, 'boss': 20}


def numbers(level, rank=None):
    """A creature's numbers from its level and rank, on the same curve as the castle's and
    Atal'narath's (health about 22 a level for a regular, more by rank)."""
    L, rank = max(1, int(level)), rank or 'regular'
    hp = max(8, int(22 * L * RANK_HP.get(rank, 1.0)))
    n = 1 if L < 10 else 2 if rank in ('regular', 'elite') else 3
    size = 4 if L < 6 else 6 if L < 15 else 8 if L < 22 else 10
    bonus = L // 5 + {'elite': 2, 'sub-boss': 4, 'boss': 6}.get(rank, 0)
    return {'hp_dice': f'{max(1, hp // 10)}d10+{hp // 2}', 'max_hp': hp, 'hp': hp,
            'damage_dice': f'{n}d{size}+{bonus}', 'hitroll': L // 2, 'damroll': bonus,
            'ac': -(10 + L), 'armor_class': 5, 'gold': 4 * L, 'exp': 30 * L,
            'xp': 30 * L * RANK_XP.get(rank, 2), 'detect_bonus': 10}


def load(pop_dir=POP_DIR) -> dict:
    out = {}
    for f in sorted(glob.glob(os.path.join(pop_dir, 'zone_*.json'))):
        try:
            with open(f, encoding='utf-8') as fh:
                d = json.load(fh)
            out[int(d.get('zone'))] = d
        except Exception as e:
            logger.warning(f"population: {os.path.basename(f)}: {e}")
    return out


def apply(world, data=None) -> list:
    """Place the bosses and lock the doors; returns what could not be done."""
    problems = []
    for z, d in (data if data is not None else load()).items():
        # the zone's own creatures (prototypes: a rebuild of world/zones keeps them)
        for v, proto in (d.get('creatures') or {}).items():
            v = int(v)
            if 'name' not in proto:
                if v not in world.mob_prototypes:
                    problems.append(f"zone {z}: no creature {v} to give {sorted(proto)}")
                else:       # an old creature given a rank or helpers
                    world.mob_prototypes[v] = dict(world.mob_prototypes[v], **{k: x for k, x in proto.items() if k != 'why'})
                continue
            p = dict(proto)
            p['vnum'] = v
            if 'level' in p:
                for k, x in numbers(p['level'], p.get('rank')).items():
                    p.setdefault(k, x)
            p.setdefault('max_hp', p.get('hp', 1000))
            p.setdefault('hp', p['max_hp'])
            if p.get('rank') == 'boss' and 'boss' not in (p.get('flags') or []):
                p['flags'] = list(p.get('flags') or []) + ['boss']
            world.mob_prototypes[v] = p
        # where they live: each room named gets one (max per room)
        for sp in d.get('spawns') or []:
            vnum = int(sp['vnum'])
            if vnum not in world.mob_prototypes:
                problems.append(f"zone {z}: no creature {vnum}")
                continue
            # a reset's max counts the creature across the whole zone (world.reset_zone): one in
            # each room named means that many in all, plus any patrols of the same kind
            rooms_named = sp.get('rooms') or []
            total = sum(len(x.get('rooms') or []) for x in d.get('spawns') or [] if int(x['vnum']) == vnum) \
                + sum(1 for pt in d.get('patrols') or [] if int(pt['vnum']) == vnum)
            for rv in rooms_named:
                room = world.rooms.get(int(rv))
                if room is None:
                    problems.append(f"zone {z}: no room {rv} for {vnum}")
                    continue
                room.mob_resets.append({'vnum': vnum, 'max': max(int(sp.get('max', 1)), total)})
        # patrols: start at the route's first room and walk it (mobs.patrol_ai)
        for pt in d.get('patrols') or []:
            vnum, route = int(pt['vnum']), [int(r) for r in pt.get('route') or []]
            bad = [r for r in route if r not in world.rooms]
            if vnum not in world.mob_prototypes or not route or bad:
                problems.append(f"zone {z}: patrol {vnum} route {bad or route}")
                continue
            # the route goes with the reset, so two patrols of one kind walk two routes (world.reset_zone)
            world.rooms[route[0]].mob_resets.append({'vnum': vnum, 'max': 1, 'route': route})
        for b in d.get('bosses') or []:
            vnum, room = int(b['vnum']), world.rooms.get(int(b['room']))
            if room is None or vnum not in world.mob_prototypes:
                problems.append(f"zone {z}: boss {vnum} or room {b.get('room')} missing")
                continue
            for r in world.rooms.values():
                if r.mob_resets:
                    r.mob_resets = [m for m in r.mob_resets if int(m.get('vnum', -1)) != vnum]
            room.mob_resets.append({'vnum': vnum, 'max': 1})
            if b.get('mechanics'):
                world.mob_prototypes[vnum]['mechanics'] = b['mechanics']   # boss_mechanics.py
        for dd in d.get('doors') or []:
            room = world.rooms.get(int(dd['room']))
            ex = (room.exits or {}).get(dd['dir']) if room else None
            if not isinstance(ex, dict):
                problems.append(f"zone {z}: no exit {dd.get('dir')} in room {dd.get('room')}")
                continue
            door = ex.get('door') if isinstance(ex.get('door'), dict) else {}
            door.update({'name': dd.get('name') or door.get('name') or 'door', 'state': 'closed', 'locked': True,
                         'key_vnum': int(dd['key'])})
            ex['door'] = door
    for p in problems:
        logger.warning(f"population: {p}")
    return problems
