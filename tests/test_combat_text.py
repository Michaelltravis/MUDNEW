#!/usr/bin/env python3
"""Fights shown, not told (combat phases 1 and 2, the owner: "focus less on the text portion and
more on the graphics"):

- every line sent to /play is marked by kind (msgkind.py): the blow-by-blow 'combat' (printed while
  a swing, skill or spell resolves, or a line of the fight's own outside one), a kill's 'reward';
  refusals, speech and a room's description never; telnet never sees a mark;
- the bridge turns the mark into an empty <i data-k> the page reads (web_client.py);
- a wound over time ticks as an event with its name (the number rises in its school's colour),
  a mending over time too, and an effect wearing off tells the player's page;
- a mage's arcane charges: one cap for every place they are gained (six with Arcane Mastery, the
  spell's "(2/5)" and Arcane Blast's "[5/6]" no longer disagree), in the payload, and every change
  tells the page at once;
- a creature's target frame lists what lingers on it (map_system._ailments);
- a kill's rewards tell the page (phase 3): experience with its bonuses and where the bar stands,
  the gold, a change in standing with a faction.

    python3 tests/test_combat_text.py
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


class Writer:
    def __init__(self):
        self.data = b''

    def write(self, b):
        self.data += b

    async def drain(self):
        pass


async def main():
    logging.disable(logging.WARNING)
    import msgkind
    import combat_events as ev
    k = msgkind.kind_of
    # ---- the kinds
    check(k('You gain 209 experience points!') == 'reward' and k('Bonuses: Streak +27, Rested +91') == 'reward'
          and k('Reputation with Garathorm Guard: +16 (Unfriendly) - Slaying a skeletal sentry') == 'reward'
          and k('You get 330 gold coins from the corpse.') == 'reward', "a kill's reward is a reward")
    check(all(k(l) == 'combat' for l in ('a skeletal sentry [█████░░░░░] [2490/4200]', 'a skeletal sentry looks ill from Meteor Burn.',
                                         'The effect of Mana Shield wears off.', 'Arcane charge gained (3/5).',
                                         '💤 a skeletal sentry flickers — caught between waking and dreaming! [17]',
                                         'Your arcane bolt *** ANNIHILATES *** a skeletal sentry! [294 damage]')),
          "the fight's own lines are combat outside an action too")
    check(k('A skeletal sentry swings at you.', True) == 'combat' and k('A skeletal sentry swings at you.') is None,
          'any line printed while an action resolves is combat; the same line outside one is not')
    check(k("You don't have enough mana.", True) is None and k('You must be fighting!', True) is None,
          'a refusal is never hidden, even mid-action')
    check(k("The Lich King says, 'You will die here.'", True) is None, 'speech is never hidden')
    with ev.hold():
        marked = msgkind.mark('You hurl a massive pyroblast!\nYour spell does 456 damage!')
        look = msgkind.mark('The Bone Hall\nA cold hall.\nObvious exits: north south')
    check(marked.count('\x1b]K:combat\x07') == 2, 'inside an action every line is marked combat')
    check('\x1b]K:' not in look, "a room described mid-action (a charge, a flee) stays in the log")

    # ---- the connection marks for the web, never for telnet
    import server
    for web in (True, False):
        conn = server.Connection.__new__(server.Connection)
        conn.is_web, conn.state, conn.writer, conn.address = web, server.Connection.STATE_PLAYING, Writer(), 'test'
        await conn.send('You gain 209 experience points!')
        has = b'\x1b]K:reward\x07' in conn.writer.data
        check(has == web, f"{'a web page' if web else 'telnet'} {'gets' if web else 'never gets'} the mark")

    # ---- the bridge
    import web_client
    html = web_client.KIND_PATTERN.sub(r'<i data-k="\1"></i>', web_client.ansi_to_html('\x1b]K:combat\x07\x1b[33mYou hurl a pyroblast!\x1b[0m'))
    check(html.startswith('<i data-k="combat"></i>') and 'You hurl a pyroblast!' in html, f'the bridge hands the page the mark ({html[:40]})')

    # ---- the world: ticks, fading, charges, ailments
    from config import Config
    from world import World
    from player import Player
    from bosses import create_mob_from_prototype
    from affects import AffectManager
    import combat_hooks
    import map_system
    import spells
    combat_hooks.install()
    world = World(Config())
    await world.load()
    room = world.rooms.get(3054) or world.rooms[3001]
    seen, private = [], []
    real_emit, real_private = ev.emit, ev.emit_private
    ev.emit = lambda r, kk, src=None, dst=None, **f: seen.append(dict(k=kk, dst=dst, **f))
    ev.emit_private = lambda ch, kk, src=None, dst=None, **f: private.append(dict(k=kk, ch=ch, **f))
    try:
        mob = create_mob_from_prototype(world.mob_prototypes[3062], world)
        mob.max_hp = mob.hp = 5000
        mob.room = room
        room.characters.append(mob)
        AffectManager.apply_affect(mob, {'name': 'Meteor Burn', 'type': 'dot', 'applies_to': 'hp', 'value': 40, 'duration': 3})
        await AffectManager.tick_affects(mob)
        tick = next((e for e in seen if e['k'] == 'dmg' and e.get('dot') == 'Meteor Burn'), None)
        check(tick is not None and tick['amt'] > 0 and tick.get('school') == 'fire', f'a burn ticks as an event, fire-coloured ({tick})')
        ails = map_system._ailments(mob)
        check(any(a['n'] == 'Meteor Burn' and a['dot'] and a['s'] == 'fire' for a in ails), f"the creature's frame lists the burn ({ails})")

        p = Player.create_new(name='Pyra', password=None, race='human', char_class='mage',
                              stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        p.world, p.room = world, room
        room.characters.append(p)
        private.clear()
        p.arcane_charges = 2
        res = [e for e in private if e['k'] == 'res']
        check(res and res[-1]['v'] == 2 and res[-1]['max'] == spells.arcane_max(p) and not res[-1]['spent'], f'a charge gained tells the page ({res})')
        p.arcane_charges = 0
        check(private[-1]['k'] == 'res' and private[-1]['spent'], 'charges spent tell the page too')
        ch = map_system._charges(p)
        check(ch == {'name': 'arcane', 'label': 'Arcane Charges', 'value': 0, 'max': spells.arcane_max(p)}, f'the payload carries the charges ({ch})')
        import inspect, commands
        check('arcane_max(player)' in inspect.getsource(commands) and spells.arcane_max(p) == 5, 'one cap for every place a charge is gained')

        AffectManager.apply_affect(p, {'name': 'Mana Shield', 'type': 'flag', 'applies_to': 'mana_shield', 'value': 1, 'duration': 1})
        private.clear()
        await AffectManager.tick_affects(p)
        check(any(e['k'] == 'fade' and e['name'] == 'Mana Shield' for e in private), 'an effect wearing off tells the page')

        # ---- rewards (phase 3)
        private.clear()
        p.exp = 0
        await p.gain_exp(209, breakdown={'kill': 91, 'streak': 27, 'rested': 91})
        xp = next((e for e in private if e['k'] == 'xp'), None)
        check(xp is not None and xp['amt'] == 209 and xp['src_kind'] == 'kill' and xp['bonus'] == {'streak': 27, 'rested': 91}
              and xp['exp'] == p.exp and xp['next'] > xp['floor'] >= 0, f'experience tells the page, bonuses and the bar ({xp})')
        private.clear()
        await p.gain_exp(50, source='quest')
        check(private and private[-1]['k'] == 'xp' and private[-1]['src_kind'] == 'quest' and private[-1]['bonus'] is None, 'a quest\'s experience too, without kill bonuses')
        private.clear()
        from factions import FactionManager, FACTIONS
        key = next(iter(FACTIONS))
        await FactionManager.apply_reputation_change(p, key, 16, 'Slaying a test')
        r = next((e for e in private if e['k'] == 'rep'), None)
        check(r is not None and r['amt'] == 16 and r['faction'] == FACTIONS[key].name and r['standing'], f'a change in standing tells the page ({r})')
        private.clear()
        combat_hooks.reward_event(p, 'gold', amt=330, total=1330)
        import combat as combat_mod
        check(private and private[-1]['k'] == 'gold' and private[-1]['amt'] == 330
              and "reward_event(killer, 'gold'" in inspect.getsource(combat_mod), "a kill's gold tells the page")
    finally:
        ev.emit, ev.emit_private = real_emit, real_private

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
