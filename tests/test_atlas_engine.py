"""The engine, ready for the world re-laid on the atlas (Push 26), offline.

A room's zone is the zone file that holds it, never its vnum's hundred-block; rooms can store
their place on the map, and the 3D zone map and the world map honour it; a sealed zone's ways in
are barred (no key, pick or bash opens them, creatures keep out, an immortal walks through) and
open again when the mark is lifted, and the bar is never saved; with the water rule on, going out
on the water takes a boat or a raft, coming ashore never does, and creatures keep to land.

    python3 tests/test_atlas_engine.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import test_webmove as tw  # noqa: E402  (check(), failures)

check, failures = tw.check, tw.failures


class Conn:
    def __init__(self):
        self.sent = []

    async def send(self, message='', newline=True):
        self.sent.append(str(message))

    async def send_prompt(self):
        pass


def said(player, n=3):
    return ' '.join(player.connection.sent[-n:])


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    from world import World, zone_of
    from player import Player
    from objects import Object
    from commands import CommandHandler
    import doors
    import map_system as ms
    real_immortal = Player.is_immortal
    world = World(Config())
    await world.load()

    # ---- a room's zone is its zone file
    check(all(zone_of(r) == r.zone.number for r in world.rooms.values()), 'zone_of agrees with the zone files for every room')
    check(world.zone_of_vnum(3001) == 30 and world.zone_of_vnum(9999999) == 99999, 'a vnum not built yet falls back to its hundred-block')
    class Bare:
        vnum = 4012
        zone = None
    check(zone_of(Bare()) == 40 and zone_of(None) is None, 'a room outside any zone falls back too')

    # ---- stored map places
    t, f = world.rooms[3001], world.rooms[3005]
    t.map, f.map = {'x': 4, 'y': 2, 'z': 0}, {'x': 4, 'y': 1, 'z': 0}
    ms._ZONEMAP_CACHE.clear()
    zm = ms.build_zonemap(world, 30)
    cell = {r['vnum']: r['cell'] for r in zm['rooms']}
    check(cell[3005][0] == cell[3001][0] and cell[3005][1] == cell[3001][1] + 1,
          f'stored places are honoured: the fountain one cell south of the temple ({cell[3001]}, {cell[3005]})')
    check(len({tuple(c) for c in cell.values()}) == len(cell), 'every room of the zone still has its own cell')
    check(ms.check_stored_cells(world) == [], 'the stored places agree with the exits')
    f.map = {'x': 4, 'y': 2, 'z': 0}
    probs = ms.check_stored_cells(world)
    check(any('share the cell' in p for p in probs), f'two rooms on one cell are reported ({probs[:1]})')
    f.map = {'x': 4, 'y': 3, 'z': 0}
    probs = ms.check_stored_cells(world)
    check(any('points away' in p for p in probs), f'an exit pointing against the map is reported ({probs[:1]})')
    f.map = {'x': 4, 'y': 1, 'z': 0}
    d = t.to_dict()
    from world import Room
    check(d.get('map') == {'x': 4, 'y': 2, 'z': 0} and Room.from_dict(d).map == d['map'], 'the place is saved and loaded with the room')
    cells = ms.world_cells(world)
    check(cells.get(3001) and cells[3005][1] == cells[3001][1] + 1, 'the world map uses the stored places too')
    t.map = f.map = None
    ms._ZONEMAP_CACHE.clear()

    # ---- sealed zones
    hero = Player.create_new(name='Sealtest', password=None, race='human', char_class='warrior',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    hero.connection = Conn()
    hero.position = 'standing'
    hero.move = hero.max_move = 500
    entry = world.rooms[3120]
    zone = world.zones[79]
    zone.sealed = True
    doors.seal_zones(world)
    door = entry.exits['up'].get('door')
    check(doors.is_seal(door) and door.get('locked') and door.get('pickproof'), 'the way into a sealed zone is barred and locked')
    hero.room = entry
    entry.characters.append(hero)
    await CommandHandler.cmd_move(hero, 'up')
    check(hero.room is entry and 'still being charted' in said(hero), f'a mortal is turned back ({said(hero, 1)[:90]})')
    for verb in ('open', 'unlock', 'pick'):
        await getattr(CommandHandler, 'cmd_' + verb)(hero, ['up'])
    await CommandHandler._bash_door(hero, 'up')
    check(door.get('state') == 'closed' and door.get('locked') and not door.get('broken'),
          'opening, unlocking, picking and bashing do nothing to it')
    check(doors.apply(entry, 'up', state='open').get('state') == 'closed', 'no door change gets through it either')
    saved = entry.to_dict()['exits']['up']
    check('door' not in saved and '_unsealed_door' not in saved, 'the bar is never saved')
    Player.is_immortal = property(lambda self: getattr(self, '_test_imm', False))
    hero._test_imm = True
    try:
        await CommandHandler.cmd_move(hero, 'up')
        check(hero.room is world.rooms[7914], 'an immortal walks through to build it')
    finally:
        hero._test_imm = False
    hero.room.characters.remove(hero)
    hero.room = entry
    entry.characters.append(hero)
    zone.sealed = False
    doors.seal_zones(world)
    check('door' not in entry.exits['up'], 'lifting the mark lifts the bar')
    await CommandHandler.cmd_move(hero, 'up')
    check(hero.room is world.rooms[7914], 'and the way is open')
    hero.room.characters.remove(hero)

    # ---- water takes a boat or a raft (the rule switched on for this)
    Config.WATER_NEEDS_BOAT = True
    try:
        levee, river = world.rooms[3049], world.rooms[3203]
        hero.room = levee
        levee.characters.append(hero)
        hero.inventory = []
        await CommandHandler.cmd_move(hero, 'south')
        check(hero.room is levee and 'boat or a raft' in said(hero), 'no boat: you stay ashore')
        raft = Object.from_prototype(world.obj_prototypes[3060], world)
        hero.inventory.append(raft)
        await CommandHandler.cmd_move(hero, 'south')
        check(hero.room is river, 'with a raft you go out on the river')
        hero.inventory.remove(raft)
        back = next(d for d, ex in river.exits.items() if ex.get('room') is levee)
        await CommandHandler.cmd_move(hero, back)
        check(hero.room is levee, 'coming ashore never needs one')
        hero.affect_flags = set(getattr(hero, 'affect_flags', set())) | {'fly'}
        await CommandHandler.cmd_move(hero, 'south')
        check(hero.room is river, 'flying, you pass over')
        hero.affect_flags.discard('fly')
        hero.room.characters.remove(hero)
        # creatures keep to land unless they live in the water
        from bosses import create_mob_from_prototype
        proto = next(p for p in world.mob_prototypes.values() if not p.get('boss_config') and 'sentinel' not in str(p.get('flags')))
        mob = create_mob_from_prototype(dict(proto), world)
        mob.flags = set(f for f in mob.flags if f != 'sentinel')
        mob.home_zone, mob.home_room = None, levee
        import random as _random
        real_randint, real_choice = _random.randint, _random.choice
        offered = []

        def choice(seq):
            offered.append(sorted(r.vnum for _, r in seq))
            return real_choice(seq)

        async def options():
            offered.clear()
            mob.room = levee
            levee.characters.append(mob)
            _random.randint, _random.choice = (lambda a, b: a), choice
            try:
                await mob.wander_ai()
            finally:
                _random.randint, _random.choice = real_randint, real_choice
            if mob in mob.room.characters:
                mob.room.characters.remove(mob)
            return offered[0] if offered else []
        land_only = await options()
        check(3203 not in land_only and land_only, f'a land creature never wanders onto the river ({land_only})')
        mob.home_room = river
        swimmer = await options()
        check(3203 in swimmer, f'one that lives on it does ({swimmer})')
    finally:
        Config.WATER_NEEDS_BOAT = False
    Player.is_immortal = real_immortal
    check(Config.WATER_NEEDS_BOAT is False, 'the water rule waits for the re-laid world (off for now)')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
