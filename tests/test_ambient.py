"""The world murmurs what fits the place, offline (ambient.py, ambient_place.py, ambient_lines.py).

    python3 tests/test_ambient.py

The owner: town lines ("Merchants haggle loudly", "a blacksmith at work") came in the Castle of the
Apocalypse, as chat. Now a line fits only where its place tags hold, a creature next door is
heard from where it really is, and a /play player gets a sound and a cue instead of a chat line.
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
TOWN = {'smithy', 'market', 'bakery', 'tavern', 'street', 'street+day', 'building'}


class FakeMap:
    def __init__(self, play):
        self.play, self.events = play, []

    def has_play(self, p):
        return self.play

    async def notify_event(self, p, ev):
        self.events.append(ev)


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    Config.PLAYER_DIR = tempfile.mkdtemp()
    from world import World
    from player import Player
    from ambient import AmbientManager
    from ambient_lines import LINES
    from ambient_place import place_tags, SMITH_RE, neighbours
    from bosses import create_mob_from_prototype
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    random.seed(7)

    def hero(name, at):
        h = Player.create_new(name=name, password=None, race='human', char_class='warrior',
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = world.rooms[at]
        world.rooms[at].characters.append(h)
        world.players[name.lower()] = h
        return h

    def keys_at(h, n=300):
        out = set()
        for _ in range(n):
            m = AmbientManager.pick(h, world)
            if m:
                out.add(m['key'])
        return out

    # ---- the castle: no town in it
    for v in (22001, 22007, 14102):
        h = hero(f'Castle{v}', v)
        tags = AmbientManager.tags_for(h, world)
        got = keys_at(h)
        check('castle' in tags and not (got & TOWN), f'{world.rooms[v].name} ({v}) is a castle: no town murmurs ({sorted(got)})')
        h.room.characters.remove(h)

    # ---- beside a smith: the hammer
    smith = next((m for m in world.npcs if getattr(m, 'special', None) == 'shopkeeper' and m.room
                  and SMITH_RE.search(f"{m.name} {getattr(m, 'short_desc', '')}")), None)
    check(smith is not None, f'the world has a smith ({smith and smith.name})')
    if smith:
        h = hero('Smithy', smith.room.vnum)
        check('smithy' in AmbientManager.tags_for(h, world), f"at {smith.name}'s shop: the place is a smithy")
        sounds = {AmbientManager.pick(h, world).get('sound') for _ in range(300)}
        check('amb_anvil' in sounds, 'and the hammer rings there')
        next_door = next((r for _, r in neighbours(smith.room, world) if not any(getattr(c, 'special', None) == 'shopkeeper' for c in r.characters)), None)
        if next_door:
            far = [r for r in world.rooms.values() if r.zone is next_door.zone and 'smithy' not in place_tags(r, world)]
            check(far, 'and a room of the same town away from any smith hears no hammer')
        h.room.characters.remove(h)

    # ---- under the earth, in the wilds
    crypt = next((r for r in world.rooms.values() if getattr(r, 'look', '') == 'crypt' and 'castle' not in place_tags(r, world)), None)
    if crypt:
        h = hero('Cryptwalker', crypt.vnum)
        got = keys_at(h)
        check('crypt' in got and not (got & TOWN), f'a crypt murmurs as a crypt ({sorted(got)})')
        h.room.characters.remove(h)
    forest = next(r for r in world.rooms.values() if getattr(r, 'look', '') == 'forest' and 'castle' not in place_tags(r, world))
    h = hero('Woodsman', forest.vnum)
    got = keys_at(h)
    check('forest' in got and not (got & TOWN), f'a forest murmurs as a forest ({sorted(got)})')
    h.room.characters.remove(h)

    # ---- a creature next door is heard from where it is
    room = world.rooms[3001]
    d, nxt = neighbours(room, world)[0]
    proto = next(p for p in world.mob_prototypes.values() if 'aggressive' in (p.get('flags') or []) and not p.get('shop_config'))
    beast = create_mob_from_prototype(dict(proto), world)
    beast.room = nxt
    nxt.characters.append(beast)
    h = hero('Listener', 3001)
    m = AmbientManager.presence_line(h, world)
    check(m and m['dir'] == d and m['room'] == nxt.vnum and m['mob'] is not None,
          f"a creature one room {d} is heard from the {d} ({m and m['text']})")
    nxt.characters.remove(beast)
    check(AmbientManager.presence_line(h, world) is None, 'and with nothing there, nothing is heard')

    # ---- telnet reads it; /play hears it
    h.connection.sent.clear()
    world.web_map = FakeMap(False)
    await AmbientManager.deliver(h, world, {'text': 'Wind moans through an arrow slit.', 'sound': 'amb_wind', 'key': 'castle'})
    check(any('arrow slit' in s for s in h.connection.sent), 'a telnet player reads the line')
    h.connection.sent.clear()
    world.web_map = fm = FakeMap(True)
    await AmbientManager.deliver(h, world, {'text': 'Wind moans through an arrow slit.', 'sound': 'amb_wind', 'key': 'castle'})
    check(not any('arrow slit' in s for s in h.connection.sent) and fm.events and fm.events[0]['type'] == 'ambient'
          and fm.events[0]['sound'] == 'amb_wind', 'a /play player gets a sound and a cue, no chat line')

    # ---- a patrol passing next door
    fm.events.clear()
    beast.room = nxt
    nxt.characters.append(beast)
    await AmbientManager.creature_moved(world, beast, nxt)
    ev = fm.events[0] if fm.events else {}
    check(ev.get('key') == 'presence' and ev.get('moving') and ev.get('dir') == d, f'a creature walking in next door is a cue for /play ({ev.get("text")})')

    # ---- one system, and every line's sound is one the client knows
    src = open(os.path.join(HERE, '..', 'src', 'main.py'), encoding='utf-8').read()
    check('ambient_events' not in src, 'the old second ambient system no longer fires')
    table = open(os.path.join(HERE, '..', 'src', 'web_isometric', 'world3d', 'soundtable.js'), encoding='utf-8').read()
    sounds = {s for lines in LINES.values() for _, s in lines if s} | {'amb_steps'}
    missing = [s for s in sounds if f'{s}:' not in table]
    check(not missing, f'every ambient sound is in the client sound table ({missing})')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
