"""Who lives where, zone by zone (world/population/zone_<n>.json), applied when the world loads,
after the zone files and before the first reset, so a rebuild of world/zones keeps it.

    {"zone": 220,
     "bosses": [{"vnum": 22070, "room": 14151, "mechanics": [{"type": "plague_pools"}], "why": "..."}],
                                                    # spawn here, and only here; fight mechanics
     "doors":  [{"room": 14150, "dir": "south", "key": 22051, "name": "inner gate"}]}   # locked to a key

Also "creatures" (prototypes by vnum: rank regular/elite/sub-boss, helpers {group, rooms, count}),
"spawns" [{vnum, rooms, max}] and "patrols" [{vnum, route}] (mobs.patrol_ai; allies.py).

A boss placed here spawns in its room and nowhere else in the world (its other resets go). A door
listed is closed and locked, opened by the key named (doors.py key_vnum).
"""
import glob
import json
import logging
import os

logger = logging.getLogger('Misthollow')
POP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'world', 'population')


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
            p = dict(proto)
            p['vnum'] = int(v)
            p.setdefault('max_hp', p.get('hp', 1000))
            world.mob_prototypes[int(v)] = p
        # where they live: each room named gets one (max per room)
        for sp in d.get('spawns') or []:
            vnum = int(sp['vnum'])
            if vnum not in world.mob_prototypes:
                problems.append(f"zone {z}: no creature {vnum}")
                continue
            for rv in sp.get('rooms') or []:
                room = world.rooms.get(int(rv))
                if room is None:
                    problems.append(f"zone {z}: no room {rv} for {vnum}")
                    continue
                room.mob_resets.append({'vnum': vnum, 'max': int(sp.get('max', 1))})
        # patrols: start at the route's first room and walk it (mobs.patrol_ai)
        for pt in d.get('patrols') or []:
            vnum, route = int(pt['vnum']), [int(r) for r in pt.get('route') or []]
            bad = [r for r in route if r not in world.rooms]
            if vnum not in world.mob_prototypes or not route or bad:
                problems.append(f"zone {z}: patrol {vnum} route {bad or route}")
                continue
            world.mob_prototypes[vnum] = dict(world.mob_prototypes[vnum], patrol_route=route)
            world.rooms[route[0]].mob_resets.append({'vnum': vnum, 'max': 1})
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
