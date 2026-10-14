#!/usr/bin/env python3
"""Rites of passage (src/rites.py, world/rites.json) on the Island of the Dead, end to end:

- the Styx cannot be walked; Charon talks, takes one gold coin (talk, pay or give) and carries you
  across; the hollow oarsman rows you back; neither can be fought;
- each gate is locked and warded (no pick, no bash); its keeper carries the key; the key opens
  that gate and crumbles; the zone reset locks it again.

    python3 tests/test_rites.py
"""
import asyncio
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


class Conn:
    def __init__(self):
        self.lines = []

    async def send(self, message='', newline=True):
        self.lines.append(str(message))

    async def send_prompt(self):
        pass

    def said(self, text):
        return any(text.lower() in l.lower() for l in self.lines)


async def main():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from player import Player
    import doors
    import rites
    world = World(Config())
    await world.load()
    rites.CROSSING.clear()

    p = Player.create_new(name='Ritetest', password=None, race='human', char_class='warrior',
                          stats={s: 15 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    p.connection = Conn()
    world.players['ritetest'] = p
    for _ in range(24):
        await p.level_up()

    def put(vnum):
        if p.room is not None and p in p.room.characters:
            p.room.characters.remove(p)
        p.room = world.rooms[vnum]
        p.room.characters.append(p)

    async def do(line):
        p.connection.lines.clear()
        words = line.split()
        await p.execute_command(words[0], words[1:])
        return p.connection

    # ---- the Styx
    put(3772)
    charon = next((c for c in p.room.characters if getattr(c, 'vnum', None) == 649505), None)
    check(charon is not None, 'Charon waits at the wharf before the Styx (3772)')
    out = await do('north')
    check(p.room.vnum == 3772 and out.said('Charon'), 'the Styx cannot be walked: the bar names Charon')
    out = await do('kill charon')
    check(not p.fighting and charon.hp > 0, 'Charon cannot be fought')
    out = await do('talk charon')
    check(out.said('One coin') and out.said('Pay the ferryman'), "talking to Charon: his words and the fare as a choice")
    p.gold = 0
    out = await do('talk charon 1')
    check(p.room.vnum == 3772 and out.said('No coin'), 'no gold: no crossing')
    p.gold = 5
    out = await do('give 1 gold charon')
    check(p.gold == 4 and out.said('closes his fingers on the coin'), 'give 1 gold charon: the fare taken')
    await asyncio.sleep(0.2)
    check(p.room.vnum == 3773, 'aboard: the crossing (3773)')
    await asyncio.sleep(9.5)
    check(p.room.vnum == 3774, 'and across to the far landing (3774)')
    out = await do('south')
    check(p.room.vnum == 3774 and out.said('oarsman'), 'the way back is barred too: the oarsman waits')
    out = await do('pay oarsman')
    check(p.gold == 3, 'pay oarsman: one coin')
    await asyncio.sleep(7.8)
    check(p.room.vnum == 3772, 'rowed back to the wharf')
    p.gold = 10
    out = await do('give coin charon')
    check(p.gold == 9, "give coin charon: one gold piece")
    await asyncio.sleep(9.8)

    # ---- a gate and its keeper
    put(3775)
    door = p.room.exits['north']['door']
    check(door.get('locked') and door.get('warded') and doors.key_vnum(door) == 799903, 'the gates of Hades are locked, warded, keyed')
    cerberus = next((c for c in p.room.characters if getattr(c, 'vnum', None) == 649515), None)
    check(cerberus is not None and any(getattr(i, 'vnum', None) == 799903 for i in cerberus.inventory),
          'Cerberus stands at the gates with their key')
    p.skills['pick_lock'] = 95
    out = await do('pick north')
    check(door.get('locked') and out.said('beyond any pick'), 'the gate cannot be picked')
    out = await do('bash north')
    check(door.get('locked') and out.said('warded'), 'nor bashed')
    out = await do('unlock north')
    check(door.get('locked') and out.said("don't have the key"), 'nor unlocked without its key')
    from objects import create_object
    p.inventory.append(create_object(799903, world))
    out = await do('unlock north')
    check(not door.get('locked') and out.said('crumbles'), 'the key opens the gate and crumbles')
    check(not any(getattr(i, 'vnum', None) == 799903 for i in p.inventory), 'and is gone')
    # the reset locks it again
    if p in p.room.characters:
        p.room.characters.remove(p)
    p.room = world.rooms[3700]
    world.rooms[3700].characters.append(p)
    doors.reset_zone(world, world.rooms[3775].zone)
    check(door.get('locked') and door.get('state') == 'closed', "the zone's reset locks the gate again")

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
