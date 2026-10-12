"""The Castle of the Apocalypse's creatures (world/population/zone_220.json), offline: regulars,
elites and sub-bosses where they belong; patrols that walk their routes; kin that come when one
is attacked; ranks the 3D client shows.

    python3 tests/test_castle_population.py
"""
import asyncio
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
    from player import Player
    from combat import CombatHandler
    from map_system import build_map_payload
    import population
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    d = population.load()[220]
    of = lambda v: [m for m in world.npcs if getattr(m, 'vnum', None) == v]

    for v, c in d['creatures'].items():
        check(of(int(v)), f"{c['short_desc']} is in the castle ({len(of(int(v)))})")
    ranks = {c.get('rank') for c in d['creatures'].values()}
    check({'elite', 'sub-boss'} <= ranks and None in ranks, f'regulars, elites and sub-bosses ({ranks})')
    marshal = of(22220)[0]
    check(marshal.room.vnum == 14139 and marshal.rank == 'sub-boss', 'the Bone Marshal holds the Junction of the Inner Halls')

    # a patrol walks its route
    knight = of(22210)[0]
    route = knight.patrol_route
    check(route and knight.room.vnum == route[0], f'the death knight starts its round at {route and route[0]}')
    seen = [knight.room.vnum]
    for _ in range(10):
        knight._patrol_next = 0
        await knight.patrol_ai()
        seen.append(knight.room.vnum)
    check(all(v in route for v in seen) and len(set(seen)) >= 5, f'and marches it, room to room ({seen})')
    check(all(abs(route.index(a) - route.index(b)) <= 1 for a, b in zip(seen, seen[1:])), 'one step at a time, there and back')

    # kin come when one is attacked
    sentry = next(m for m in of(22200) if m.room and m.room.zone.number == 220)
    h = Player.create_new(name='Intruder', password=None, race='human', char_class='warrior',
                          stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    h.connection = tae.Conn()
    h.room = sentry.room
    sentry.room.characters.append(h)
    h.level, h.max_hp, h.hp = 60, 50000, 50000
    from allies import nearby_allies
    near = nearby_allies(sentry, 2, 2)
    before = len([c for c in sentry.room.characters if not hasattr(c, 'connection')])
    await CombatHandler.start_combat(h, sentry)
    after = [c for c in sentry.room.characters if not hasattr(c, 'connection') and c is not sentry]
    check(len(after) + 1 >= before + len(near) and all(getattr(c, 'fighting', None) is h for c, _ in near),
          f'attacking a sentry brings its kin from nearby ({len(near)} came)')

    # the 3D client is told each creature's rank
    h.room.characters.remove(h)
    h.room = marshal.room
    marshal.room.characters.append(h)
    h.explored_rooms = {marshal.room.vnum}
    pl = build_map_payload(h)
    import json as _j
    blob = _j.dumps(pl)
    check('"rank": "sub-boss"' in blob, 'the payload says the Marshal is a sub-boss')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
