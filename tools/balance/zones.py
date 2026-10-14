#!/usr/bin/env python3
"""Zones cleared: a hero (or a party) walks a zone room by room and fights what lives there, with the
game's own combat code on a simulated clock (sim.py: the same heroes, rotation, wind-ups and world
ticks), resting back to full between fights. How dangerous a zone is at its own level.

    python3 tools/balance/zones.py --zones 512,408          # each zone, lone heroes and a party of three
    python3 tools/balance/zones.py --busiest 6              # the zones the build-out cap fix filled most
    python3 tools/balance/zones.py --rooms 13831-13848,13884-13899 --levels 60,64,68   # dead Morkai

Each room's foes are the creatures the world puts there when it loads, made fresh from their
prototypes (ranks and bosses as population.py makes them); --old-cap fights them as the build-out
placed them before its cap fix (each build-out creature once per zone) for comparison. Per party
and level: rooms fought, foes, deaths, the median and the worst share of health a fight took, the
minutes fighting and resting. Findings: docs/balance/zones.md.
"""
import argparse
import asyncio
import collections
import json
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
sys.path.insert(0, sim.SRC)   # (the game's bosses.py before this folder's)

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
_n = [0]


def made_by_buildout():
    with open(os.path.join(ROOT, 'world', 'buildout', 'vnums.json'), encoding='utf-8') as f:
        return set(json.load(f).get('mobs', {}).values())


def layout(world, rooms, old_cap=False):
    """[(room, [vnum...])] of the hostile creatures standing in these rooms at load, in room order;
    old_cap: each build-out creature only in the first room it stands in."""
    made = made_by_buildout() if old_cap else set()
    seen = set()
    out = []
    for v in sorted(rooms):
        room = world.rooms.get(v)
        if room is None:
            continue
        foes = []
        for ch in room.characters:
            vn = getattr(ch, 'vnum', None)
            if vn is None or hasattr(ch, 'connection') or getattr(ch, 'is_player', False):
                continue
            flags = set(getattr(ch, 'flags', None) or [])
            if 'aggressive' not in flags and not getattr(ch, 'aggressive', False):
                continue
            if old_cap and vn in made:
                if vn in seen:
                    continue
                seen.add(vn)
            foes.append(vn)
        if foes:
            out.append((room, foes))
    return out


async def clear(world, plan, classes, level, a, seed):
    """The party clears the plan; returns a dict of what it cost."""
    from bosses import create_mob_from_prototype
    random.seed(seed)
    heroes = []
    for cls in classes:
        _n[0] += 1
        heroes.append(await sim.make_hero(world, cls, max(1, level), f'Zn{cls[:3].title()}{_n[0]}', a.gear))
    costs, deaths, fight_s, rest_m, lost = [], 0, 0.0, 0.0, 0
    for room, vnums in plan:
        foes = [create_mob_from_prototype(dict(world.mob_prototypes[v]), world) for v in vnums if v in world.mob_prototypes]
        for f in foes:
            for m in getattr(f, 'mechanics', ()):
                if m.spec.get('type') == 'call_guards':
                    m.spec = dict(m.spec, rooms=0)
        for h in heroes:
            h._low = h.hp
        sim.DEATHS.clear()
        fight_s += await sim.fight(world, room, heroes, foes, a.mode, a.dodge, {}, max_secs=a.max_minutes * 60)
        d = len(sim.DEATHS)
        deaths += d
        if any(f.hp > 0 for f in foes):
            lost += 1
        for f in foes:
            if f in world.npcs:
                world.npcs.remove(f)
            if f.room is not None and f in f.room.characters:
                f.room.characters.remove(f)
        if d and a.verbose:
            print(f"      died in {room.vnum} {room.name}: " + ', '.join(world.mob_prototypes[v]['short_desc'] for v in vnums), flush=True)
        costs.append(max(1.0 if h.name in sim.DEATHS else 1 - getattr(h, '_low', h.hp) / max(1, h.max_hp) for h in heroes))
        rest_m += sim.rest(heroes)
    leave(world, heroes)
    return {'fights': len(plan), 'foes': sum(len(v) for _, v in plan), 'deaths': deaths, 'lost': lost,
            'median': statistics.median(costs) if costs else 0, 'worst': max(costs) if costs else 0,
            'fight_min': fight_s / 60, 'rest_min': rest_m}


def leave(world, heroes):
    """The heroes and their servants out of the world (bosses.py _leave)."""
    from pets import PetManager
    for h in heroes:
        for pet in PetManager.get_player_pets(h):
            if pet in world.npcs:
                world.npcs.remove(pet)
            if pet.room is not None and pet in pet.room.characters:
                pet.room.characters.remove(pet)
        world.players.pop(h.name.lower(), None)
        if h.room is not None and h in h.room.characters:
            h.room.characters.remove(h)


def zone_rooms(world, zn):
    return [v for v, r in world.rooms.items() if getattr(getattr(r, 'zone', None), 'number', None) == zn]


def zone_level(world, rooms):
    lv = [world.mob_prototypes[getattr(ch, 'vnum')]['level'] for v in rooms for ch in world.rooms[v].characters
          if getattr(ch, 'vnum', None) in world.mob_prototypes]
    return int(statistics.median(lv)) if lv else 1


def parse_rooms(spec):
    out = []
    for part in spec.split(','):
        if '-' in part:
            a, b = part.split('-')
            out += list(range(int(a), int(b) + 1))
        elif part.strip():
            out.append(int(part))
    return out


async def run(world, name, rooms, levels, a):
    rows = []
    for old in ([False, True] if a.compare else [a.old_cap]):
        plan = layout(world, rooms, old_cap=old)
        for level in levels:
            for party in [[c] for c in a.classes.split(',')] + ([a.party.split(',')] if a.party else []):
                res = await clear(world, plan, party, level, a, seed=7000 + level)
                who = '+'.join(c[:4] for c in party)
                tag = 'old cap' if old else 'now'
                rows.append((name, tag, level, who, res))
                print(f"{name[:26]:26} {tag:7} L{level} {who:16} fights {res['fights']:3} foes {res['foes']:3}  "
                      f"deaths {res['deaths']:2} lost {res['lost']:2}  median {100 * res['median']:3.0f}% worst {100 * res['worst']:3.0f}%  "
                      f"fighting {res['fight_min']:5.1f}m resting {res['rest_min']:5.1f}m", flush=True)
    return rows


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--zones', default='', help='zone numbers, e.g. 512,408')
    ap.add_argument('--rooms', default='', help='a room list instead, e.g. 13831-13848,13884-13899')
    ap.add_argument('--name', default='rooms')
    ap.add_argument('--busiest', type=int, default=0, help='the N build-out zones the cap fix filled most')
    ap.add_argument('--levels', default='', help="hero levels (default: the median level of the zone's foes)")
    ap.add_argument('--classes', default='warrior,cleric,mage')
    ap.add_argument('--party', default='warrior,cleric,mage', help='a party too (empty: none)')
    ap.add_argument('--compare', action='store_true', help='also fight the zone as the old cap left it')
    ap.add_argument('--old-cap', action='store_true')
    ap.add_argument('--exclude', default='', help='rooms to leave out, e.g. 13828-13899')
    ap.add_argument('--verbose', action='store_true', help='where each death happened')
    ap.add_argument('--mode', choices=['rounds', 'action'], default='rounds')
    ap.add_argument('--dodge', type=float, default=0.6)
    ap.add_argument('--gear', type=float, default=0.75)
    ap.add_argument('--max-minutes', type=float, default=10)
    a = ap.parse_args()
    world = await sim.load_world()
    sim.patch_deaths(world)
    sim.patch_damage()
    targets = []
    if a.rooms:
        targets.append((a.name, parse_rooms(a.rooms)))
    for zn in [int(z) for z in a.zones.split(',') if z.strip()]:
        rooms = zone_rooms(world, zn)
        zname = getattr(world.rooms[rooms[0]].zone, 'name', str(zn)) if rooms else str(zn)
        targets.append((f'{zn} {zname}', rooms))
    if a.busiest:
        made = made_by_buildout()
        gain = collections.Counter()
        per = collections.defaultdict(collections.Counter)
        for n in world.npcs:
            if getattr(n, 'vnum', None) in made and n.room is not None:
                per[n.room.zone.number][n.vnum] += 1
        for zn, c in per.items():
            gain[zn] = sum(c.values()) - len(c)
        for zn, g in gain.most_common(a.busiest):
            rooms = zone_rooms(world, zn)
            targets.append((f'{zn} {world.rooms[rooms[0]].zone.name} (+{g})', rooms))
    skip = set(parse_rooms(a.exclude)) if a.exclude else set()
    targets = [(n, [r for r in rooms if r not in skip]) for n, rooms in targets]
    for name, rooms in targets:
        levels = [int(x) for x in a.levels.split(',')] if a.levels else [zone_level(world, rooms)]
        await run(world, name, rooms, levels, a)


if __name__ == '__main__':
    asyncio.run(main())
