"""Mounts carry you faster (Push 34), offline.

    python3 tests/test_mounts.py
"""
import asyncio
import os
import random
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
    from commands import CommandHandler
    from mounts import MountManager, MOUNT_TEMPLATES, travel_speed, TRAVEL_CAP, BOSS_MOUNTS, boss_mount_drop
    from factions import FACTIONS
    from map_system import build_map_payload
    from bosses import create_mob_from_prototype
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()

    def hero(name, at=3001):
        h = Player.create_new(name=name, password=None, race='human', char_class='warrior',
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = world.rooms[at]
        world.rooms[at].characters.append(h)
        world.players[name.lower()] = h
        h.max_move = h.move = 500
        return h

    # ---- how fast you go
    h = hero('Rider')
    check(travel_speed(h) == 1.0, 'on foot you go at walking pace')
    h.mount = MountManager.create_mount('horse')
    check(abs(travel_speed(h) - 1.35) < 0.01, f'a horse carries you 35% faster ({travel_speed(h)})')
    h.mount = MountManager.create_mount('griffin')
    check(abs(travel_speed(h) - 1.6) < 0.01, f'a griffin 60% ({travel_speed(h)})')
    h.mount.loyalty = 0
    check(abs(travel_speed(h) - 1.3) < 0.01, f'a neglected mount half as much ({travel_speed(h)})')
    h.mount.loyalty = 100
    h.affect_flags.add('haste')
    h.equipment['feet'] = __import__('legendary').create_legendary(99008, world)      # threshold walkers
    check(travel_speed(h) == round(1 + TRAVEL_CAP, 3), f'never more than +80% ({travel_speed(h)})')
    h.affect_flags.discard('haste')
    del h.equipment['feet']
    h.explored_rooms = {h.room.vnum}
    payload = build_map_payload(h)
    sp = (payload.get('player') or {}).get('speed')
    check(sp and abs(sp - travel_speed(h)) < 1e-6, f'the map payload says how fast the hero goes ({sp})')

    # ---- every mount a faction gives exists, and every template has a speed
    missing = [m for f in FACTIONS.values() for m in (f.exalted_rewards or {}).get('mounts', []) if m not in MOUNT_TEMPLATES]
    check(not missing, f'every faction mount exists ({missing})')
    check(all(MountManager.create_mount(k).travel > 0 for k in MOUNT_TEMPLATES), 'every mount has a travel speed')

    # ---- what moving costs
    h.mount = MountManager.create_mount('horse')
    target = next(world.rooms[ex['to_room']] for ex in h.room.exits.values() if isinstance(ex, dict) and ex.get('to_room') in world.rooms)
    on_foot = Player.create_new(name='Walker', password=None, race='human', char_class='warrior',
                                stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    on_foot.room = h.room
    walk = sum(CommandHandler._calculate_move_cost(on_foot, target) for _ in range(10))
    ride = sum(CommandHandler._calculate_move_cost(h, target) for _ in range(10))
    check(ride <= walk // 2 + 1 and ride < walk, f'riding halves what moving costs, even on easy ground ({walk} on foot, {ride} riding)')

    # ---- loyalty
    h.mount.loyalty = 100
    for _ in range(10):
        await h.regen_tick()
    check(h.mount.loyalty == 95, f'a ridden mount grows hungry, a point every other minute ({h.mount.loyalty})')
    h.gold = 100
    await CommandHandler.cmd_feed(h, [])
    check(h.mount.loyalty == 100, 'feeding restores it')

    # ---- ride: a speedwalk
    check(CommandHandler.ride_steps(['n', 'n', '3e']) == ['north', 'north', 'east', 'east', 'east'], 'ride n n 3e')
    check(CommandHandler.ride_steps(['nnee']) == ['north', 'north', 'east', 'east'], 'ride nnee')
    check(len(CommandHandler.ride_steps(['20n'])) == 10, 'at most ten steps')
    # find a straight line of three open rooms to ride
    def line(v, d, n):
        out = [v]
        for _ in range(n):
            ex = world.rooms[out[-1]].exits.get(d)
            to = ex.get('to_room') if isinstance(ex, dict) else None
            if to not in world.rooms or (isinstance(ex.get('door'), dict)):
                return None
            out.append(to)
        return out
    start = next(((v, d) for v in world.rooms for d in ('north', 'east') if line(v, d, 3)
                  and all(not any('aggressive' in (getattr(m, 'flags', None) or ()) for m in world.rooms[x].characters) for x in line(v, d, 3))
                  and world.rooms[v].sector_type not in ('water_swim', 'water_noswim', 'underwater')
                  and all(world.rooms[x].sector_type not in ('water_swim', 'water_noswim', 'underwater') for x in line(v, d, 3))
                  and world.rooms[v].admits(h)), None)
    if start:
        v, d = start
        path = line(v, d, 3)
        h.room.characters.remove(h)
        h.room = world.rooms[v]
        h.room.characters.append(h)
        h.fighting = None
        h.position = 'standing'
        await CommandHandler.cmd_ride(h, [d[0] * 3])
        check(h.room.vnum == path[-1], f'ride {d[0] * 3} rides three rooms ({v} -> {h.room.vnum}, want {path[-1]})')
    h.mount = None
    await CommandHandler.cmd_ride(h, ['n'])
    check('mounted' in ' '.join(h.connection.sent[-1:]), 'riding needs a mount')

    # ---- a boss's mount
    boss_v, (key, _) = next(iter(BOSS_MOUNTS.items()))
    if boss_v in world.mob_prototypes:
        boss = create_mob_from_prototype(dict(world.mob_prototypes[boss_v]), world)
        real = random.randint
        random.randint = lambda a, b: a
        try:
            won = await boss_mount_drop(h, boss)
        finally:
            random.randint = real
        check(won == key and MountManager.get_owned_mount_data(h, key), f'beating the boss can win its {key}')
        again = await boss_mount_drop(h, boss)
        check(again is None, 'but only once')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
