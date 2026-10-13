"""Garathorm and its districts, offline (world/population/zone_{30,403,418,420,431,517}.json and
the build-out parts that wrote their rooms).

    python3 tests/test_garathorm.py

The city's watch walks its streets and comes when a citizen is attacked (citizens call, the
watch answers; a shopkeeper never leaves the counter to fight). The Wall, the Cathedral, the
School House, Fameland and the Vineyard are lived in, their rooms read like their names, and the
Hollow Bishop and the First Hero fight with their mechanics.
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
    import allies
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    npcs = lambda v: [m for m in world.npcs if getattr(m, 'vnum', None) == v]

    # ---- the districts are lived in
    for z, least in ((403, 8), (431, 20), (517, 12), (420, 12), (418, 3)):
        rooms = [r for r in world.rooms.values() if getattr(r.zone, 'number', None) == z]
        lived = [r for r in rooms if any(not hasattr(c, 'connection') for c in r.characters)]
        check(len(lived) >= least, f'zone {z} is lived in ({len(lived)} of {len(rooms)} rooms)')
        generic = [r.vnum for r in rooms if 'Stone walls close in, cool to the touch' in ' '.join((r.description or '').split())]
        check(not generic, f'zone {z}: no room keeps the placeholder text ({generic[:5]})')
    check('bell' in world.rooms[4452].description.lower(), 'the Belfry reads like a belfry')
    check(world.rooms[4472].look == 'crypt', 'the Ossuary looks like a crypt')

    # ---- bosses
    bishop, hero = npcs(43130), npcs(42030)
    check(len(bishop) == 1 and bishop[0].room.vnum == 4430 and getattr(bishop[0], 'is_boss', False)
          and {m.spec['type'] for m in bishop[0].mechanics} == {'waves', 'plague_pools', 'gloom'},
          'the Hollow Bishop at the Diamond Altar: his risen, his rot, the dying light')
    check(len(hero) == 1 and hero[0].room.vnum == 15222 and [m.spec['type'] for m in hero[0].mechanics] == ['call_guards'],
          'the First Hero on the Way of Heroes calls his champions')
    check(getattr(npcs(43120)[0], 'rank', None) == 'sub-boss' and getattr(npcs(41802)[0], 'rank', None) == 'sub-boss',
          'the Sexton and the wine spider are sub-bosses')
    check(npcs(43130)[0].max_hp > 5 * npcs(43101)[0].max_hp, 'a boss is much tougher than a regular (numbers from level and rank)')

    # ---- the watch walks
    watch = npcs(30500)
    check(len(watch) == 4, f'four watchmen walk the city ({len(watch)})')
    w = next(m for m in watch if m.room.vnum == 3040)
    w._patrol_next = 0
    moved = await w.patrol_ai()
    check(moved and w.room.vnum == 3012, f'a watchman walks Main Street ({w.room.vnum})')
    walls = npcs(40300)
    check(len(walls) == 2 and all(m.patrol_route for m in walls), 'two sentries walk the wall')

    # ---- a citizen attacked: the watch comes, other citizens do not
    crier = npcs(30502)[0]
    check(crier.room.vnum == 3014 and crier.helpers.get('group') == 'garathorm_watch', 'the town crier stands in the Market Square')
    came = allies.nearby_allies(crier, 3, 5)
    check(came and all(getattr(m, 'vnum', None) in (30500, 3059, 3060, 3067) for m, _ in came),
          f'only the watch answers ({[getattr(m, "vnum", None) for m, _ in came]})')
    baker = next(m for m in world.npcs if getattr(m, 'vnum', None) == 3001)
    check(baker.helpers.get('answer') is False and not any(m is baker for m, _ in came), 'the baker calls the watch, but stays at the counter')
    h = Player.create_new(name='Ruffian', password=None, race='human', char_class='warrior',
                          stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    h.connection = tae.Conn()
    h.room = crier.room
    crier.room.characters.append(h)
    joined = await allies.rally(crier, h)
    check(joined and all(m.room is crier.room and m.fighting is h for m in joined), f'the watch rushes in and fights ({len(joined)})')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
