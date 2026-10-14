#!/usr/bin/env python3
"""How full each zone is, and whether its locked doors can be opened. Loads the world as the game
does (build-out, population, rites) and counts what stands in it at load.

    python3 tools/audit/density.py                 # the table, sparsest adventuring zones first
    python3 tools/audit/density.py --md docs/world/density.md
    python3 tools/audit/density.py --zone 495      # one zone, room by room

Per zone: rooms a body can walk (no god rooms, no deep water), creatures at load (all, and the
hostile ones), creatures per walkable room, the level band of its foes, doors, locked doors, and
locked doors whose key nothing in the world provides (no room, no creature carries or drops it) --
a door nobody can open but a thief. A zone counts as a town when most of its creatures are
peaceful or its rooms are mostly city; towns are not held to the hostile density.
"""
import argparse
import asyncio
import collections
import logging
import os
import statistics
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

DEEP = {'water_noswim', 'underwater', 'air'}
GODLY = {'imm_only', 'godroom', 'god_room', 'gods_only'}
SPARSE = 0.35          # hostile creatures per walkable room below which an adventuring zone is thin


def key_sources(world):
    """Every object vnum the world hands out: room resets, what creatures carry or drop."""
    out = set()
    for r in world.rooms.values():
        for o in getattr(r, 'obj_resets', None) or []:
            v = o.get('vnum') if isinstance(o, dict) else o
            if v is not None:
                out.add(int(v))
        for it in getattr(r, 'items', None) or []:
            if getattr(it, 'vnum', None) is not None:
                out.add(int(it.vnum))
    for p in world.mob_prototypes.values():
        for v in p.get('inventory') or []:
            out.add(int(v['vnum'] if isinstance(v, dict) else v))
        for v in p.get('loot_table') or []:
            out.add(int(v['vnum'] if isinstance(v, dict) else v))
        for v in (p.get('equipment') or {}).values() if isinstance(p.get('equipment'), dict) else []:
            out.add(int(v['vnum'] if isinstance(v, dict) else v))
    return out


def survey(world):
    import doors
    sources = key_sources(world)
    zones = collections.OrderedDict()
    for v, r in sorted(world.rooms.items()):
        z = getattr(getattr(r, 'zone', None), 'number', None)
        if z is None:
            continue
        s = zones.setdefault(z, {'zone': z, 'name': getattr(r.zone, 'name', str(z)), 'rooms': 0, 'walk': 0, 'city': 0,
                                 'mobs': 0, 'hostile': 0, 'levels': [], 'doors': 0, 'locked': 0, 'nokey': [],
                                 'bosses': 0, 'empty_walk': 0})
        s['rooms'] += 1
        flags = set(getattr(r, 'flags', None) or [])
        walk = getattr(r, 'sector_type', '') not in DEEP and not (flags & GODLY)
        s['walk'] += walk
        s['city'] += getattr(r, 'sector_type', '') == 'city'
        here = [c for c in r.characters if getattr(c, 'vnum', None) is not None and not hasattr(c, 'connection')]
        if walk and not here:
            s['empty_walk'] += 1
        for c in here:
            s['mobs'] += 1
            fl = set(getattr(c, 'flags', None) or [])
            if 'aggressive' in fl or getattr(c, 'aggressive', False) or getattr(c, 'rank', None) in ('elite', 'sub-boss', 'boss'):
                s['hostile'] += 1
                s['levels'].append(getattr(c, 'level', 1))
            if 'boss' in fl or getattr(c, 'is_boss', False):
                s['bosses'] += 1
        for d, ex in (getattr(r, 'exits', None) or {}).items():
            door = ex.get('door') if isinstance(ex, dict) else None
            if not door:
                continue
            s['doors'] += 1
            if door.get('locked') or door.get('state') == 'locked':
                s['locked'] += 1
                k = doors.key_vnum(door)
                if k is not None and k not in sources:
                    s['nokey'].append((v, d, k))
    for s in zones.values():
        s['per_room'] = s['hostile'] / max(1, s['walk'])
        s['town'] = (s['mobs'] and s['hostile'] < 0.4 * s['mobs']) or s['city'] > 0.5 * s['rooms']
        s['band'] = (min(s['levels']), int(statistics.median(s['levels'])), max(s['levels'])) if s['levels'] else None
        s['sparse'] = (not s['town']) and s['walk'] >= 8 and s['per_room'] < SPARSE
    return zones


def table(zones, md=False):
    rows = sorted(zones.values(), key=lambda s: (not s['sparse'], s['town'], s['per_room']))
    head = ['zone', 'name', 'walk rooms', 'creatures', 'hostile', 'hostile/room', 'empty rooms', 'levels', 'doors', 'locked', 'no key', 'note']
    out = []
    if md:
        out.append('| ' + ' | '.join(head) + ' |')
        out.append('|' + '---|' * len(head))
    for s in rows:
        band = f"{s['band'][0]}-{s['band'][2]} (med {s['band'][1]})" if s['band'] else '-'
        note = 'SPARSE' if s['sparse'] else ('town' if s['town'] else '')
        cells = [s['zone'], s['name'][:28], s['walk'], s['mobs'], s['hostile'], f"{s['per_room']:.2f}", s['empty_walk'],
                 band, s['doors'], s['locked'], len(s['nokey']), note]
        out.append(('| ' + ' | '.join(map(str, cells)) + ' |') if md else
                   f"{cells[0]:>4} {cells[1]:28} {cells[2]:>4} {cells[3]:>4} {cells[4]:>4} {cells[5]:>5} {cells[6]:>4} {band:16} {cells[8]:>3} {cells[9]:>3} {cells[10]:>2} {note}")
    return '\n'.join(out)


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--md', default='')
    ap.add_argument('--zone', type=int, default=0)
    a = ap.parse_args()
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    world = World(Config())
    await world.load()
    zones = survey(world)
    if a.zone:
        s = zones[a.zone]
        print({k: v for k, v in s.items() if k != 'levels'})
        for v, r in sorted(world.rooms.items()):
            if getattr(r.zone, 'number', None) == a.zone:
                who = [c.short_desc for c in r.characters if getattr(c, 'vnum', None) is not None and not hasattr(c, 'connection')]
                print(v, r.name[:36].ljust(36), ', '.join(who))
        return
    sparse = [s for s in zones.values() if s['sparse']]
    nokey = [(s['zone'], x) for s in zones.values() for x in s['nokey']]
    print(f"{len(zones)} zones; {len(sparse)} sparse adventuring zones (< {SPARSE} hostile per walkable room); "
          f"{len(nokey)} locked doors with no key in the world")
    print(table(zones, md=bool(a.md)) if not a.md else '')
    if a.md:
        with open(os.path.join(ROOT, a.md), 'w', encoding='utf-8') as f:
            f.write(table(zones, md=True) + '\n')
        print('wrote', a.md)


if __name__ == '__main__':
    asyncio.run(main())
