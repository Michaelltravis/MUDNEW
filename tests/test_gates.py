"""The zones just outside Garathorm's gates, offline (world/population/zone_{72,408,50,200,79}.json):
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

    # ---- every boss in its room, a boss, with its mechanics
    for z in (72, 408, 50, 200, 79):
        d = population.load()[z]
        for b in d.get('bosses') or []:
            ms = npcs(int(b['vnum']))
            want = [m['type'] for m in b.get('mechanics') or []]
            check(len(ms) == 1 and ms[0].room.vnum == int(b['room']) and getattr(ms[0], 'is_boss', False)
                  and [m.spec['type'] for m in ms[0].mechanics] == want and getattr(ms[0], 'rank', None) == 'boss',
                  f'zone {z}: {b["why"]} ({want})')
        for v, c in (d.get('creatures') or {}).items():
            if c.get('rank') and 'name' not in c:
                check(all(getattr(m, 'rank', None) == c['rank'] for m in npcs(int(v))) and npcs(int(v)),
                      f'zone {z}: {v} is {c["rank"]} ({count[int(v)]} of them)')
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
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
