#!/usr/bin/env python3
"""Immortals creatures leave alone (mobs.spared): nohassle ("Mobs will ignore you") and wizinvis keep an
aggressive creature from starting a fight; without them it attacks as before.

    python3 tests/test_nohassle.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


class Room:
    def __init__(self):
        self.characters, self.flags, self.sector_type = [], [], 'field'

    async def send_to_room(self, *a, **k):
        pass


class Hero:
    connection = object()

    def __init__(self, **flags):
        self.name, self.level, self.flags, self.is_fighting = 'Gauntlet', 60, [], False
        self.__dict__.update(flags)


async def main():
    import combat
    from mobs import Mobile
    started = []

    async def start_combat(a, b):
        started.append((a, b))
    combat.CombatHandler.start_combat = staticmethod(start_combat)

    async def attacks(hero):
        started.clear()
        room = Room()
        mob = Mobile.__new__(Mobile)
        mob.name, mob.level, mob.room, mob.position, mob.affect_flags = 'an ixitxachitl', 10, room, 'standing', set()
        mob.config = combat.CombatHandler.config
        room.characters = [mob, hero]
        await Mobile.aggressive_ai(mob)
        return bool(started)

    check(await attacks(Hero()), 'an aggressive creature attacks a hero')
    check(not await attacks(Hero(nohassle=True)), 'but not an immortal with nohassle on')
    check(not await attacks(Hero(wizinvis=True)), 'nor one invisible to mortals (wizinvis)')
    check(await attacks(Hero(nohassle=False)), 'nohassle turned off: it attacks again')
    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
