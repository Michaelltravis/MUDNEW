#!/usr/bin/env python3
"""Aimed area spells (spells.py AIM_RADIUS, commands.py cast @x,z, /play aim.js):

- "cast 'meteor storm' @x,z" strikes only the foes inside the circle round that point;
- without a point (telnet, the command line) a room spell strikes every foe here, as before;
- a point beyond the spell's reach is drawn in toward the caster, and kept inside the room;
- nothing inside the circle: nothing is spent, and the caster is told so;
- Hallowed Ground keeps burning the ground it was cast on;
- the spell event carries the point and the radius (the client draws the blast there);
- the spellbook entry carries the radius and the reach.

    python3 tests/test_aim.py
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
    from bosses import create_mob_from_prototype
    from commands import CommandHandler
    import combat_range as cr
    import combat_events as ev
    import spells
    world = World(Config())
    await world.load()
    import combat_hooks
    combat_hooks.install()                    # the spell event the client reads (as main.py does)
    ROOM = world.rooms[3054] if 3054 in world.rooms else world.rooms[3001]
    ROOM.flags = [f for f in (ROOM.flags or []) if f != 'peaceful']

    def put(ch, room):
        if ch.room is not None and ch in ch.room.characters:
            ch.room.characters.remove(ch)
        ch.room = room
        room.characters.append(ch)

    p = Player.create_new(name='Aimer', password=None, race='human', char_class='mage',
                          stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    p.connection = Conn()
    p.world = world
    world.players['aimer'] = p
    for _ in range(59):
        await p.level_up()
    put(p, ROOM)
    cr.set_pos(p, 2, 7)

    def foe(x, z):
        mob = create_mob_from_prototype(world.mob_prototypes[3062], world)
        mob.max_hp = mob.hp = 99999
        put(mob, ROOM)
        world.npcs.append(mob)
        cr.set_pos(mob, x, z)
        return mob

    def reset():
        p.fighting = None
        p.position = 'standing'
        p.mana = p.max_mana = 5000
        p.spells['meteor_storm'] = 95
        p.spells['hallowed_ground'] = 95
        p.spell_cd = {}                      # the spell's own cooldown
        for m in (near, far):
            m.hp = m.max_hp
            m.fighting = None
            m.position = 'standing'
        p.connection.lines.clear()

    near, far = foe(6, 7), foe(20, 7)
    for ch in list(ROOM.characters):          # only our two foes here
        if ch not in (p, near, far) and not hasattr(ch, 'connection'):
            ROOM.characters.remove(ch)

    # ---- the aim point
    check(CommandHandler._aim_for(p, 'meteor_storm', (6, 7)) == (6.0, 7.0, spells.AIM_RADIUS['meteor_storm']), 'a point within reach is kept')
    far_pt = CommandHandler._aim_for(p, 'meteor_storm', (23.5, 7))
    check(abs(far_pt[0] - (2 + spells.AIM_RANGE)) < 0.01 and far_pt[1] == 7.0, f'a point beyond reach is drawn in toward the caster ({far_pt})')
    out_pt = CommandHandler._aim_for(p, 'meteor_storm', (4, -9))
    check(out_pt[1] >= 0.0, f'a point outside the room is kept inside it ({out_pt})')
    check(CommandHandler._aim_for(p, 'magic_missile', (6, 7)) is None, 'a spell that does not take aim ignores the point')

    # ---- aimed: only the foe inside the circle
    reset()
    ev_seen = []
    real_emit_at = ev.emit_at

    def spy(room, index, k, src=None, dst=None, **fields):
        ev_seen.append(dict(k=k, **fields))
        return real_emit_at(room, index, k, src, dst, **fields)
    ev.emit_at = spy
    await p.execute_command('cast', ["'meteor", "storm'", '@6,7'])
    ev.emit_at = real_emit_at
    check(near.hp < near.max_hp and far.hp == far.max_hp, f'aimed at the near foe: it burns, the far one is untouched ({near.max_hp - near.hp}, {far.max_hp - far.hp})')
    spell_ev = next((e for e in ev_seen if e['k'] == 'spell'), {})
    check(spell_ev.get('at') == [6.0, 7.0] and str(spell_ev.get('shape', '')).startswith('blast:'), f'the spell event carries the point and the blast ({spell_ev.get("at")}, {spell_ev.get("shape")})')
    check(getattr(p, '_aim', None) is None, 'the aim is let go after the cast')

    # ---- not aimed: every foe here, as before (telnet)
    reset()
    await p.execute_command('cast', ["'meteor", "storm'"])
    check(near.hp < near.max_hp and far.hp < far.max_hp, 'not aimed: every foe here burns')

    # ---- nothing inside the circle: nothing spent
    reset()
    mana = p.mana
    await p.execute_command('cast', ["'meteor", "storm'", '@13,2'])
    check(p.mana == mana and near.hp == near.max_hp and p.connection.said('where you aimed'), 'an empty circle: nothing spent, and why')

    # ---- Hallowed Ground keeps burning where it was cast
    reset()
    import marquee_abilities as ma
    effects = []
    real_begin = ma._begin
    ma._begin = lambda e: effects.append(e)
    await p.execute_command('cast', ["'hallowed", "ground'", '@20,7'])
    ma._begin = real_begin
    if effects:
        e = effects[-1]
        e.power = 1
        await e.step(e, 1)
        check(far.hp < far.max_hp and near.hp == near.max_hp, 'Hallowed Ground sears the ground it was cast on, not the caster\'s')
    else:
        check(False, 'Hallowed Ground began its effect')

    # ---- the spellbook entry
    import mastery
    entry = mastery._entry('mage', 'meteor_storm', 'spell', 50)
    check(entry.get('target') == 'area' and entry.get('radius') == spells.AIM_RADIUS['meteor_storm'] and entry.get('range') == spells.AIM_RANGE,
          f"the spellbook entry carries the radius and the reach ({entry.get('radius')}, {entry.get('range')})")

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
