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

    # ---- stored map places (the atlas's, on every room of the re-laid world)
    t, f = world.rooms[3001], world.rooms[3005]
    check(bool(t.map) and bool(f.map), 'the temple and its fountain carry their places on the map')
    base = set(ms.check_stored_cells(world))           # what the world itself reports (the atlas's long ways)
    saved = (dict(t.map), dict(f.map))
    ms._ZONEMAP_CACHE.clear()
    zm = ms.build_zonemap(world, zone_of(t))
    cell = {r['vnum']: r['cell'] for r in zm['rooms']}
    dx, dy = f.map['x'] - t.map['x'], -(f.map['y'] - t.map['y'])      # the game draws north as -y
    check(cell[3005][0] - cell[3001][0] == dx and cell[3005][1] - cell[3001][1] == dy,
          f'stored places are honoured: the fountain sits where the atlas draws it from the temple ({cell[3001]}, {cell[3005]})')
    check(len({tuple(c) for c in cell.values()}) == len(cell), 'every room of the zone has its own cell')
    check(not [p for p in base if 'share the cell' in p], 'no two rooms share a cell')
    f.map = dict(t.map)
    probs = [p for p in ms.check_stored_cells(world) if p not in base]
    check(any('share the cell' in p for p in probs), f'two rooms on one cell are reported ({probs[:1]})')
    f.map = {'x': t.map['x'], 'y': t.map['y'] + 1, 'z': t.map.get('z', 0)}
    probs = [p for p in ms.check_stored_cells(world) if p not in base]
    check(any('points away' in p for p in probs), f'an exit pointing against the map is reported ({probs[:1]})')
    t.map, f.map = saved
    d = t.to_dict()
    from world import Room
    check(d.get('map') == t.map and Room.from_dict(d).map == d['map'], 'the place is saved and loaded with the room')
    cells = ms.world_cells(world)
    check(cells.get(3001) and (cells[3005][0] - cells[3001][0], cells[3005][1] - cells[3001][1]) == (dx, dy),
          'the world map uses the stored places too')
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
        Config.WATER_NEEDS_BOAT = True

    # ---- the God Rooms take immortals only (and nobody mortal is put where they may not be)
    import random as _random
    from spells import SpellHandler
    from quests import route_dirs
    temple, god = world.rooms[3001], world.rooms[1200]
    gods = [world.rooms[v] for v in (1200, 1201, 1203, 1204)]
    check(all('imm_only' in r.flags for r in gods), 'the God Rooms are for immortals only')

    def put(ch, room):
        if ch.room is not None and ch in ch.room.characters:
            ch.room.characters.remove(ch)
        ch.room = room
        room.characters.append(ch)
    put(hero, temple)
    await CommandHandler.cmd_move(hero, 'up')
    check(hero.room is temple and 'divine force' in said(hero), f'a mortal is turned back at the stairs ({said(hero, 1)[:80]})')
    lead = Player.create_new(name='Godtest', password=None, race='human', char_class='cleric',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    lead.connection = Conn()
    lead.position = 'standing'
    lead.move = lead.max_move = 500
    lead._test_imm = True
    put(lead, temple)
    hero.following = lead
    await CommandHandler.cmd_move(lead, 'up')
    check(lead.room is god, 'an immortal walks up into the God Rooms')
    check(hero.room is temple and 'keeps you from following' in said(hero), 'a mortal following them stays behind')
    hero.following = None
    # summoning a mortal up there fails; the teleport spell never lands there, nor in a sealed land
    world.players['sealtest'] = hero
    try:
        await SpellHandler.handle_special_spell(lead, 'Sealtest', {'special': 'summon_player'})
        check(hero.room is temple and 'divine force' in said(lead), f'a mortal cannot be summoned into them ({said(lead, 1)[:80]})')
    finally:
        world.players.pop('sealtest', None)
    seen = []
    real_choice = _random.choice

    def pick(seq):
        seen.append(seq)
        return real_choice(seq)
    _random.choice = pick
    try:
        await SpellHandler.handle_special_spell(hero, None, {'special': 'teleport'})
    finally:
        _random.choice = real_choice
    pool = next((s for s in seen if s and hasattr(s[0], 'vnum')), [])
    check(pool and not any('imm_only' in r.flags or getattr(r.zone, 'sealed', False) for r in pool)
          and len(pool) < len(world.rooms), f'the teleport spell never lands in the God Rooms or a sealed land ({len(pool)} rooms)')
    # a mortal saved up there, or with a recall point there, comes back at the temple
    put(hero, world.rooms[3005])
    hero.room_vnum, hero.recall_point = 1204, 1204
    check(world.login_room(hero) is temple and hero.recall_room() is temple, 'logging in or recalling there sends a mortal to the temple')
    await CommandHandler.cmd_recall(hero, [])
    check(hero.room is temple, 'and recall takes them there')
    put(hero, god)
    await CommandHandler.cmd_recall(hero, ['set'])
    check(hero.recall_point == 1204 and 'cannot set your recall point' in said(hero), 'a mortal cannot bind there')
    hero.recall_point = 3001
    lead.room_vnum = 1204
    check(world.login_room(lead) is world.rooms[1204], 'an immortal comes back where they left')
    put(hero, temple)
    # creatures keep out; mortals' directions never go through
    from bosses import create_mob_from_prototype
    proto = next(p for p in world.mob_prototypes.values() if not p.get('boss_config') and 'sentinel' not in str(p.get('flags')))
    mob = create_mob_from_prototype(dict(proto), world)
    mob.flags = set(f for f in mob.flags if f != 'sentinel')
    mob.home_zone, mob.home_room = None, world.rooms[1204]
    offered = []

    def offer(seq):
        offered.append(sorted(r.vnum for _, r in seq))
        return real_choice(seq)
    put(mob, world.rooms[1204])
    real_randint = _random.randint
    _random.randint, _random.choice = (lambda a, b: a), offer
    try:
        await mob.wander_ai()
    finally:
        _random.randint, _random.choice = real_randint, real_choice
    if mob in mob.room.characters:
        mob.room.characters.remove(mob)
    check(offered and not any(v in (1200, 1201, 1203, 1204) for v in offered[0]),
          f'a wandering creature never steps into a God Room ({offered[:1]})')
    way = route_dirs(world, 3001, 1826) or []
    check(way and way[0] != 'up' and len(way) > 4, f'directions never lead mortals through them ({len(way)} steps to the Long Lake)')
    Player.is_immortal = real_immortal
    check(Config().WATER_NEEDS_BOAT is True, 'the water rule is on with the re-laid world')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
