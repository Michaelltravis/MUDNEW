#!/usr/bin/env python3
"""Player-experience polish (the owner: "complete all the suggested fixes"):

- a dark room is dark in /play: the zone map payload says how the player sees it
  (map_system._sight): dark or not, a light carried, able to see at all;
- a caster's mana stays in its orb, its class resource as pips (hud.js CASTERS), and big numbers
  are shortened on the orbs (200000 -> 200k);
- exit signs fade with distance and in a fight (terrain.js LABEL_FADE), and Tab keeps to the
  hero's own room first (main.js).

    python3 tests/test_polish.py
"""
import asyncio
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
WEB = os.path.join(HERE, '..', 'src', 'web_isometric', 'world3d')

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


def src(name):
    return open(os.path.join(WEB, name), encoding='utf-8').read()


async def main():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from player import Player
    import map_system
    world = World(Config())
    await world.load()
    p = Player.create_new(name='Lumen', password=None, race='human', char_class='cleric',
                          stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    p.world = world
    dark = next(r for r in world.rooms.values() if 'dark' in (r.flags or []))
    p.room = dark
    s = map_system._sight(p)
    check(s == {'dark': True, 'light': False, 'see': False}, f'a dark room, no light: dark and unseen ({s})')
    p.room = world.rooms[3001]
    check(map_system._sight(p) == {'dark': False}, 'a lit room is not dark')
    p.room = dark
    real = Player.has_light_source
    Player.has_light_source = lambda self: True
    try:
        s = map_system._sight(p)
        check(s['dark'] and s['light'] and s['see'], f'carrying a light: dark, lit, seen ({s})')
    finally:
        Player.has_light_source = real
    payload = map_system.build_zonemap  # (the payloads carry it)
    ms = open(map_system.__file__, encoding='utf-8').read()
    check(ms.count("'sight': _sight(player)") == 2, 'both player payloads carry the sight')

    hud = src('hud/hud.js')
    check("const CASTERS = new Set(['mage', 'necromancer', 'cleric', 'paladin', 'bard'])" in hud and 'classRes && !caster' in hud,
          "a caster's orb is its mana, a fighter's its resource")
    check('compact(p.hp)' in hud, 'orbs shorten big numbers')
    check('LABEL_FADE.combat' in src('main.js') and 'export const LABEL_FADE' in src('terrain.js'), 'exit signs fade with distance and in a fight')
    check('e.vnum === heroRoom.vnum' in src('main.js'), "Tab keeps to the hero's own room first")
    check('engine.darkness' in src('main.js') and 'darkness: 0' in src('engine.js'), 'the engine darkens a dark room')

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
