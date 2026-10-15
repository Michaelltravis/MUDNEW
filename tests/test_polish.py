#!/usr/bin/env python3
"""Player-experience polish (the owner: "complete all the suggested fixes"):

- a dark room is dark in /play: the zone map payload says how the player sees it
  (map_system._sight): dark or not, a light carried, able to see at all;
- a caster's mana stays in its orb, its class resource as pips (hud.js CASTERS), and big numbers
  are shortened on the orbs (200000 -> 200k);
- exit signs fade with distance and in a fight (terrain.js LABEL_FADE), and Tab keeps to the
  hero's own room first (main.js);
- combat numbers: where they show, their size and screen shake are settings, with a colour key;
  bursts of small hits add up; the shake grows with the blow.

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

    # ---- batch 2: combat numbers and feel
    html = src('play.html')
    check(all(f'data-set="{k}"' in html for k in ('sct', 'sctsize', 'shake')) and 'id="sct-key"' in html,
          'settings: combat numbers, their size, screen shake, the colour key')
    fx, combat = src('fx.js'), src('combat.js')
    check("this.opts.sct === 'off'" in fx and 'if (!this.opts.shake) return;' in fx and '* this.opts.size' in fx, 'fx obeys the settings')
    check('×${last.n}' in combat, 'a burst of small hits adds up in one number')
    check('bite * 1.6' in combat and 'killing ? 110' in combat, 'the shake and the pause grow with the blow')

    # ---- dying says what it cost and where you wake
    import combat_events as ev
    sent = []
    real = ev.emit_private
    ev.emit_private = lambda ch, k, src=None, dst=None, **f: sent.append(dict(k=k, **f))
    try:
        v = Player.create_new(name='Mortis', password=None, race='human', char_class='warrior',
                              stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        v.world, v.room = world, world.rooms[3001]
        world.rooms[3001].characters.append(v)
        v.exp, v.gold = 10000, 1000
        await v.die(None) if hasattr(v, 'die') else None
    finally:
        ev.emit_private = real
    f = next((e for e in sent if e['k'] == 'fallen'), None)
    check(f is not None and f['exp'] > 0 and f['gold'] == 50 and f['wake'], f'the death card is told the cost and where you wake ({f})')
    check("Slain by ${d.killer}" in src('hud/hud.js'), 'the death card shows them')

    # ---- batch 3: gear and loot
    inv = src('hud/inventory.js')
    check("import { compare } from '../gearcompare.js'" in inv and 'up-badge' in inv and 'tt-cmp' in inv,
          'tooltips compare with what you wear; better pieces carry a green arrow')
    check('tooltip(r.item, MH.state && MH.state.player)' in src('hud/lootwin.js'), "a corpse's loot window compares too")
    loot = src('loot.js')
    check('rarityBeam(' in loot and 'bestRarity(g.item.contents)' in loot, 'drops and rich corpses show a beam of their rarity')

    # ---- batch 4: where to go for an ordinary quest
    import datetime
    import quest_guide
    from quests import ActiveQuest, QuestObjective, QUEST_DEFINITIONS as Q

    def give(qid):
        d = Q[qid]
        return ActiveQuest(quest_id=qid, name=d['name'], description=d['description'], quest_type=d['type'],
                           objectives=[QuestObjective(**o) for o in d['objectives']], rewards=d['rewards'],
                           started_at=datetime.datetime.now())
    g = Player.create_new(name='Wayfarer', password=None, race='human', char_class='warrior',
                          stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    g.world, g.room = world, world.rooms[3001]
    visit = next(k for k, q in Q.items() if q.get('objectives') and q['objectives'][0]['type'] == 'visit' and str(q['objectives'][0]['target']) == '3054')
    g.active_quests = [give(visit)]
    b = map_system._quest_block(g)
    check(b and b['kind'] == 'quest' and b['where']['vnum'] == 3054 and b['where']['dir'], f'a visit quest: the room, and the first step there ({b and b.get("where")})')
    g.active_quests = [give('message_for_mayor')]
    w = map_system._quest_block(g)['where']
    check(w and w['steps'] > 0 and w['dir'], f'a talk quest: the way to the one to speak with ({w})')
    q = give('message_for_mayor')
    for o in q.objectives:
        o.completed = True
    g.active_quests = [q]
    b = map_system._quest_block(g)
    check(b['title'].startswith('Return to ') and b.get('where'), f"done: back to the quest's giver ({b['title']})")
    g.active_quests = []
    check(map_system._quest_block(g) is None, 'no quest, no tracker')
    check('zone.passageWorld(heroRoom, w.dir)' in src('main.js'), 'a gold arrow by the hero points the way out of the room')

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
