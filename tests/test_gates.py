"""Every zone given a population, and the zones just outside Garathorm's gates, offline (world/population/zone_{72,408,50,200,79}.json):
the Sewer's Rat King, the Trade Road's wardens, outlaws, Black Jory and the Barrow King, the
dracolich and the myconids under the mountain, the Forest of Shadows' pack and brood, and
Redferne in his sky-house.

    python3 tests/test_gates.py
"""
import asyncio
import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import test_webmove as tw  # noqa: E402

check, failures = tw.check, tw.failures


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    Config.PLAYER_DIR = tempfile.mkdtemp()
    from world import World
    import allies
    import population
    world = World(Config())
    await world.load()
    npcs = lambda v: [m for m in world.npcs if getattr(m, 'vnum', None) == v]
    count = collections.Counter(getattr(m, 'vnum', None) for m in world.npcs)

    # ---- every population file: each boss in its room, a boss, with its mechanics; each rank
    # given holds (and lifts the creature to the rank's numbers); each patrol walks its own route
    for z, d in sorted(population.load().items()):
        for b in d.get('bosses') or []:
            ms = npcs(int(b['vnum']))
            want = [m['type'] for m in b.get('mechanics') or []]
            check(len(ms) == 1 and ms[0].room.vnum == int(b['room']) and getattr(ms[0], 'is_boss', False)
                  and [m.spec['type'] for m in ms[0].mechanics] == want and getattr(ms[0], 'rank', None) in (None, 'boss'),
                  f'zone {z}: {b["why"]} ({want})')
        for v, c in (d.get('creatures') or {}).items():
            if c.get('rank') and 'name' not in c:
                ms = npcs(int(v))
                floor = population.numbers(ms[0].level, c['rank'])['max_hp'] if ms else 0
                check(ms and all(getattr(m, 'rank', None) == c['rank'] and m.max_hp >= floor for m in ms),
                      f'zone {z}: {v} is {c["rank"]} ({count[int(v)]} of them, {ms[0].max_hp if ms else 0} health)')
        for p in d.get('patrols') or []:
            walkers = [m for m in npcs(int(p['vnum'])) if getattr(m, 'patrol_route', None) == p['route']]
            check(len(walkers) == 1, f'zone {z}: {p["why"]} ({len(p["route"])} rooms)')
    # ---- a patrol walks
    w = next(m for m in npcs(40800) if m.patrol_route[0] == 9768)
    w._patrol_next = 0
    check(await w.patrol_ai() and w.room.vnum == w.patrol_route[1], 'a warden rides on along the Trade Road')
    # ---- helpers
    jory = npcs(40810)[0]
    check(jory.room.vnum == 19742 and jory.rank == 'sub-boss' and jory.helpers['group'] == 'outlaws', 'Black Jory holds the clearing, and whistles for outlaws')
    king = npcs(72000)[0]
    check(king.room.vnum == 7320 and king.max_hp > 5 * npcs(7207)[0].max_hp, 'the Rat King at the Lair End, far tougher than his rats')
    rat = npcs(7002)[0]
    came = allies.nearby_allies(rat, 2, 5)
    check(all(getattr(m, 'helpers', {}).get('group') == 'sewer_rats' for m, _ in came), f'only rats answer a rat ({len(came)})')
    check(npcs(5014)[0].rank == 'sub-boss' and len(npcs(50000)) == 3, 'the myconid shaman and its three sentries')
    check(npcs(79002) and npcs(79003) and npcs(79000)[0].room.vnum == 7911, "Redferne's household, and Redferne in his bedroom")
    # ---- the next ring out
    check(npcs(2537)[0].room.vnum == 2590 and npcs(2537)[0].rank == 'boss', 'the Master Summoner in his Pentagram Chamber')
    crier = next(m for m in world.npcs if getattr(m, 'vnum', None) == 5433)
    came = allies.nearby_allies(crier, 3, 5)
    check(all(getattr(m, 'vnum', None) in (5461, 5462, 5482, 5463) for m, _ in came), f'in New Thalos only the guard answers ({len(came)})')
    check(npcs(40050)[0].room.vnum == 4044, 'Grondar in the Hill Giant Cave')
    grukthar = npcs(3503)[0]
    check(grukthar.rank == 'boss', 'Grukthar the Goblin King a boss')
    check(npcs(120501)[0].room.vnum == 12204 and npcs(120500)[0].room.vnum == 8892, 'the High Priest of Terror in his temple, the Pallid Herald in Lost Carcosa')
    # ---- the World of Chaos and Ghenna, built and opened together (world/atlas/overrides.json)
    chaos, ghenna = world.zones[475], world.zones[481]
    check(not getattr(chaos, 'sealed', False) and not getattr(ghenna, 'sealed', False), 'the World of Chaos and Ghenna are open')
    down = world.rooms[16258].exits.get('down') or {}
    check(down.get('room') is world.rooms[9901] and not down.get('door'), 'from the island in the Lake of Blood a way leads down to Ghenna, unbarred')
    check(npcs(47530)[0].room.vnum == 16252 and npcs(9910)[0].room.vnum == 9937, 'the Lord of Chaos in the Hall of Pillars; the Deep Dragon in its lair')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
