"""The Sunken Ruins of Atal'narath (zone 130), offline: its creatures live there (its own old
mobiles block was never loaded), every creature a population file places in N rooms is there N
times, Nerathis fights with whirlpools and his drowned, and open-water rooms lose the indoor
filler ("stale air", "rough-hewn walls") their descriptions were padded with.

    python3 tests/test_sunken.py
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
    import population
    import room_looks
    world = World(Config())
    await world.load()
    count = collections.Counter(getattr(m, 'vnum', None) for m in world.npcs)

    for z, d in population.load().items():
        want = collections.Counter()
        for sp in d.get('spawns') or []:
            want[int(sp['vnum'])] += len(sp.get('rooms') or [])
        for pt in d.get('patrols') or []:
            want[int(pt['vnum'])] += 1
        short = {v: (n, count[v]) for v, n in want.items() if count[v] < n}
        check(not short, f'zone {z}: every creature placed is there as many times as placed ({short})')

    zone_rooms = [r for r in world.rooms.values() if getattr(r.zone, 'number', None) == 130]
    lived = [r for r in zone_rooms if any(not hasattr(c, 'connection') for c in r.characters)]
    check(len(lived) >= 14, f"Atal'narath is lived in ({len(lived)} of {len(zone_rooms)} rooms)")
    king = next(m for m in world.npcs if getattr(m, 'vnum', None) == 13130)
    check(king.room.vnum == 13015 and getattr(king, 'is_boss', False) and {m.spec['type'] for m in king.mechanics} == {'plague_pools', 'waves'},
          'Nerathis on his throne, a boss with whirlpools and his drowned')
    check(world.rooms[13011].look == 'underwater', 'the Flooded Temple looks like what it is: under the sea')
    filler = [r.vnum for r in world.rooms.values() if r.look in room_looks.OPEN_LOOKS and 'indoors' not in (r.flags or ())
              and any(f in (r.description or '').replace('\n', ' ') for f in room_looks.INDOOR_FILLER)]
    check(not filler, f'no open-air or underwater room keeps the indoor filler ({filler[:5]})')
    check('stale air' not in world.rooms[13011].description, 'the Flooded Temple no longer has stale air')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
