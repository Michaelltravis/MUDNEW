#!/usr/bin/env python3
"""Player-experience polish (the owner: "complete all the suggested fixes"):

- a dark room is dark in /play: the zone map payload says how the player sees it
  (map_system._sight): dark or not, a light carried, able to see at all;
- a caster's mana stays in its orb, its class resource as pips (hud.js CASTERS), and big numbers
  are shortened on the orbs (200000 -> 200k);
- exit signs fade with distance and in a fight (terrain.js LABEL_FADE), and Tab keeps to the
  hero's own room first (main.js);
- combat numbers: where they show, their size and screen shake are settings, with a colour key;
  bursts of small hits add up; the shake grows with the blow;
- rooms: ice and lava caves, a zone's own stone and light (zone_tone.py), set pieces laid out by
  hand (setpieces.py, world/setpieces.json).

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
                           objectives=[QuestObjective(**{k: v for k, v in o.items() if not k.startswith('_')}) for o in d['objectives']], rewards=d['rewards'],
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

    # ---- batch 5: rooms drawn as their words say: ice and fire caves, a zone's own stone and
    # light, set pieces laid out by hand
    import room_looks
    import zone_tone
    import setpieces
    check({'ice_cave', 'lava_cave'} <= room_looks.UNDERGROUND, 'ice and lava caves are roofed, underground looks')
    check(world.rooms[20572].look == 'ice_cave' and world.rooms[20597].look == 'lava_cave', 'an ice cave and a lava cave drawn so')
    check(zone_tone.read(['A hall of black stone.'] * 8) == {'stone': 'black'}, 'a zone of black stone is black')
    check(zone_tone.read(['A dark room.'] * 8 + ['White marble.']) is None, 'a stray mention is no tone')
    check(zone_tone.read(['Green ghost-fire burns.'] * 6) == {'light': 'ghost'}, 'ghost-fire is a ghost light')
    toned = [r for r in world.rooms.values() if getattr(r, 'tone', None)]
    check(0 < len(toned) < len(world.rooms) / 4, f'some zones have a tone, most none ({len(toned)} rooms)')
    sp = setpieces.load()
    throne = world.rooms[24527]
    check(throne.setpiece == {'light': sp['24527']['light']} and throne.features[0]['x'] == 12, 'the Throne of Shadows is laid out by hand, with its light')
    zm = map_system.build_zonemap(world, throne.zone.number)
    room = next((r for r in zm['rooms'] if r.get('vnum') == 24527), None)
    check(room and room.get('setpiece') and room.get('features') and 'tone' in room, 'the zone map carries set pieces and tones')
    check('TONE_STONE[layout.tone.stone]' in src('terrain.js') and 'TONE_LIGHT[L.tone.light]' in src('main.js'), "/play tints a zone's stone and light")

    # ---- batch 6: the tutorial in /play (found playing it as a newcomer)
    check(quest_guide.web_text('Check your score (type "score")') == 'Check your score: open your Character sheet (C)',
          'a "type score" step says which window to open')
    g.room = world.rooms[3001]
    g.active_quests = [give('tutorial_3_know_thyself')]
    b = map_system._quest_block(g)
    check('(C)' in b['title'] and 'where' not in b, f"a step done where you stand: how, and no arrow ({b['title']})")
    from commands import CommandHandler
    sent = []
    g.send = lambda *a, **k: asyncio.sleep(0, sent.append(a))
    await CommandHandler.cmd_uiseen(g, ['character'])
    q = g.active_quests[0]
    check(all(o.completed for o in q.objectives if o.target in ('score', 'equipment')), 'opening the Character sheet counts as score and equipment')
    await CommandHandler.cmd_uiseen(g, ['spellbook'])
    check(all(o.completed for o in q.objectives if o.target in ('skills', 'spells')), 'opening the Spellbook counts as skills and spells')
    g.active_quests = [give('tutorial_9_newbie_zone')]
    for o in g.active_quests[0].objectives[:2]:
        o.completed = True
    g.room = world.rooms[18600]
    b = map_system._quest_block(g)
    check(b.get('where') and b['where']['steps'] >= 0, f'"defeat any 3 creatures": the way to the nearest fair fight ({b.get("where")})')
    hud = src('hud/hud.js')
    check('uiseen ${name}' in hud, 'the HUD tells the server when a window opens')
    net = open(os.path.join(WEB, '..', 'shared', 'net.js'), encoding='utf-8').read()
    check("MH.bus.emit('connection.lost')" in net and 'MH.awaitServer' in net and 'connection.lost' in src('main.js') and "classList.contains('done') ? $('#resume-btn').click()" in src('hud/login.js'),
          'a dropped connection waits for the server and signs back in')

    zm = map_system.build_zonemap(world, world.rooms[3001].zone.number)
    temple = next(r for r in zm['rooms'] if r['vnum'] == 3001)
    up = temple['exits'].get('up') or {}
    check(up.get('imm') is True and 'if (e.imm) delete r.exits[d]' in src('zone.js'),
          "the Temple's stairs to the God Rooms are not drawn for players who can't take them")
    check('.xbar.unused' in src('hud/hud.css') and "classList.toggle('unused'" in src('hud/hud.js'),
          'an extra action bar with nothing on it stays faded until used')
    msgs = []
    class Conn:
        is_web = True
    g.connection = Conn()
    check(quest_guide.for_player(g, 'Rest to recover (type "rest")') == 'Rest to recover: right-click yourself, then Rest',
          'the chat log words tutorial steps for /play too')
    g.connection = None

    # a quest that moves on where you stand (a talk, a window, a kill) refreshes the tracker now
    pushed = []

    class WM:
        def has_play(self, pl):
            return True

        async def notify_player(self, pl):
            pushed.append(pl.name)
    real_wm = getattr(world, 'web_map', None)
    world.web_map = WM()
    try:
        g.active_quests = [give('tutorial_3_know_thyself')]
        await CommandHandler.cmd_uiseen(g, ['inventory'])
        await asyncio.sleep(0)
        check(pushed, f'a step done in place sends the tracker at once ({pushed})')
    finally:
        world.web_map = real_wm

    # the training dummy falls: the tutorial step completes there and then, the next one begins
    from quests import QuestManager
    g.active_quests = [give('tutorial_5_combat')]
    g.active_quests[0].objectives[0].completed = True
    g.active_quests[0].objectives[0].current = 1
    await QuestManager.check_quest_progress(g, 'kill', {'mob_vnum': 3078, 'mob_name': 'a training dummy', 'mob_keywords': 'dummy training'})
    ids = [q.quest_id for q in g.active_quests]
    check('tutorial_5_combat' not in ids and 'tutorial_6_healing' in ids, f'a tutorial kill completes the step at once ({ids})')

    # lighter dark rooms and dim moods (the owner: "too dark in some of the rooms"), and a
    # Brightness setting on top
    eng = src('engine.js')
    check("lit ? 0.35 : eyes ? 0.35 : 0.6" in src('main.js') and '(1 - 0.75 * darkNow)' in eng,
          'a dark room keeps most of its light with a lantern, and some without')
    check("data-set=\"bright\"" in open(os.path.join(WEB, 'play.html'), encoding='utf-8').read()
          and "settings.brightness" in src('main.js') and '(api.brightness || 1)' in eng,
          'Settings -> Brightness lightens the whole picture')

    # the server on a laptop (the owner: "super laggy"): creatures where no player is think one
    # tick in ten, and a zone reset counts the world's creatures once, not once per reset line
    near = next(n for n in world.npcs if n.room and n.room.zone is world.rooms[3001].zone)
    far = next(n for n in world.npcs if n.room and n.room.zone is not world.rooms[3001].zone
               and all(getattr(getattr(e.get('room') if isinstance(e, dict) else None, 'zone', None), 'number', None)
                       != world.rooms[3001].zone.number for e in (n.room.exits or {}).values()))
    calls = {'near': 0, 'far': 0}

    async def count_near():
        calls['near'] += 1

    async def count_far():
        calls['far'] += 1
    near.process_ai, far.process_ai = count_near, count_far
    world.players['wayfarer'] = g
    g.room = world.rooms[3001]
    try:
        for _ in range(world.NPC_SLEEP_EVERY):
            await world.process_npcs()
    finally:
        world.players.pop('wayfarer', None)
        del near.process_ai, far.process_ai
    check(calls == {'near': world.NPC_SLEEP_EVERY, 'far': 1}, f'creatures by a player think every tick, the rest one in ten ({calls})')
    import time as _t
    for z in world.zones.values():
        z.age = z.lifespan
    t0 = _t.perf_counter()
    await world.zone_reset_tick()
    took = _t.perf_counter() - t0
    check(took < 3, f'a reset of every zone takes a moment, not seconds of a frozen server ({took:.2f}s; was ~8s)')

    # the owner's machine drew in software ("Microsoft Basic Render Driver", 3 fps): /play notices,
    # drops to Low and says why; far rooms are kept but not drawn; exit signs no longer overlap
    main_js = src('main.js')
    check('basic render driver|swiftshader|llvmpipe' in main_js and "engine.setQuality('low')" in main_js,
          'a browser drawing without a graphics card gets Low quality and a word on why')
    check('r.built.group.visible = far <= 3' in src('zone.js'), 'rooms kept for the way back are not drawn past the fog')
    check('x + inward * 4' in src('terrain.js'), "an exit's sign stands inside its own room, clear of the one across the edge")

    # combat numbers stay longer (the owner: "fades pretty fast"), weighted, with a setting and a cap
    fxs = src('fx.js')
    check('TEXT_LIFE = 1.45' in fxs and 'LANE_MAX = 7' in fxs and 'data-set="sctlife"' in open(os.path.join(WEB, 'play.html'), encoding='utf-8').read(),
          'combat numbers stay up longer, crits longest, with a Number duration setting and a cap on the crowd')

    # reaching into the next room (reach.py): a shot or a bolt across an open way pulls the
    # creature in; never melee, a sentinel, a closed door, a peaceful room, nor for telnet
    import reach
    import combat_range as cr
    from bosses import create_mob_from_prototype
    here, there = world.rooms[3002], world.rooms[3003]
    check(reach.joined(world, here, there) == 'east', 'the Temple Square and the market street are joined by an open way')
    mage = Player.create_new(name='Reacher', password=None, race='human', char_class='mage',
                             stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    mage.world, mage.room, mage.connection = world, here, object()
    here.characters.append(mage)
    told = []

    async def note(m, *a, **k):
        told.append(m)
    mage.send = note
    beast = create_mob_from_prototype(next(iter(world.mob_prototypes.values())), world)
    beast.flags = set(f for f in (beast.flags or ()) if f not in ('sentinel', 'boss'))
    beast.special, beast._web_uid, beast.owner = None, 990001, None

    def put(x):
        if beast.room is not None and beast in beast.room.characters:
            beast.room.characters.remove(beast)
        beast.room = there
        there.characters.append(beast)
        cr.set_pos(beast, x, 7.5)
    world.npcs.append(beast)
    put(2.0)
    mage.web_pos = (here.vnum, 22.0, 7.5)
    check(abs(reach.distance(world, mage, beast) - 4.0) < 0.01, 'distance is measured across the edge (4 m)')
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is here and cr.pos_of(beast) == (23.0, 7.5), f"a mage's bolt pulls it in to the nearest point ({cr.pos_of(beast)})")
    put(20.0)
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is there and 'out of reach' in told[-1], "beyond the bolt's 10 m it stays")
    put(2.0)
    await reach.webpull(mage, ['#990001', 'bash'])
    check(beast.room is there, 'a melee skill pulls nothing (the hero walks in)')
    beast.flags.add('sentinel')
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is there and 'post' in told[-1], 'a creature that keeps its post is not pulled')
    beast.flags.discard('sentinel')
    ex = here.exits['east']
    had = ex.get('door')
    ex['door'] = {'name': 'door', 'state': 'closed'}
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is there, 'not through a closed door')
    if had is None:
        ex.pop('door')
    else:
        ex['door'] = had
    there.flags.add('peaceful')
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is there, 'not into a peaceful room')
    there.flags.discard('peaceful')
    came = reach.pull_area(mage, (23.5, 7.5), 4.0)
    check(beast in came and beast.room is here, 'an aimed circle across the edge catches it')
    put(2.0)
    check(reach.pull_area(beast, (2.0, 7.5), 30.0) == [], "a creature's own spell pulls no one")
    mage.web_pos = None
    await reach.webpull(mage, ['#990001', 'attack'])
    check(beast.room is there, 'a player with no position (telnet) keeps the old rules')
    # only what is aimed at a foe pulls, as the hero's own class book says
    import mastery
    for cls in ('warrior', 'paladin', 'cleric', 'ranger', 'mage', 'necromancer', 'thief', 'assassin', 'bard'):
        hero = Player.create_new(name='Probe' + cls[:3].title(), password=None, race='human', char_class=cls,
                                 stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        wrong = [e['id'] for e in mastery.book(cls) if reach.action_range(hero, e['id'])[1] and e.get('target') not in (None, 'enemy')]
        check(not wrong, f'{cls}: no heal, blessing or self ability pulls ({wrong})')
    sin = Player.create_new(name='Probesin', password=None, race='human', char_class='assassin',
                            stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    check(not reach.action_range(sin, 'poison')[1] and reach.action_range(mage, 'magic_missile')[1],
          "an assassin's weapon poison pulls nothing; a mage's magic missile does")
    # a leap or a charge carries the hero over instead (the client sends the room move first,
    # then the ability: commands from one connection run in order)
    from commands import CommandHandler
    war = Player.create_new(name='Leaper', password=None, race='human', char_class='warrior',
                            stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    war.world, war.room, war.connection, war.level = world, here, object(), 50
    war.send = note
    here.characters.append(war)
    war.web_pos = (here.vnum, 22.0, 7.5)
    if beast.room is not there:
        put(2.0)
    hp0 = beast.hp
    await CommandHandler.execute(war, 'webmove', ['3002', '3003', 'east'])
    await CommandHandler.execute(war, 'heroic_leap', ['#990001'])
    check(war.room is there and beast.room is there and beast.hp < hp0,
          f'Heroic Leap from the next room lands on it ({war.room.vnum}, {hp0} -> {beast.hp})')
    check(all(cr.ABILITY_RANGE[k][1] == 'dash' for k in ('heroic_leap', 'charge', 'shadowstrike', 'death_from_above')),
          'the leaps and charges are dashes (the client carries the hero over for them)')
    for ch in (war, beast):
        ch.fighting = None
    # warriors and thieves throw: Heroic Throw and Knife Toss reach the next room and pull
    for who, ab in (('warrior', 'heroic_throw'), ('thief', 'knife_toss')):
        hero = Player.create_new(name='Thrower' + who[:3].title(), password=None, race='human', char_class=who,
                                 stats={s: 16 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        hero.level = 3
        mastery.grant_now(hero)
        check(ab in hero.skills and reach.action_range(hero, ab)[1] and reach.action_range(hero, ab)[0] >= 14,
              f'a {who} has {ab} at level 3, and it reaches the next room')
    war.fighting = None
    if beast.room is not there:
        put(2.0)
    war.room.characters.remove(war)
    war.room, war.web_pos = here, (here.vnum, 22.0, 7.5)
    here.characters.append(war)
    war.skills['heroic_throw'] = 50
    war.heroic_throw_cooldown = 0
    hp0 = beast.hp
    await reach.webpull(war, ['#990001', 'heroic_throw'])
    await CommandHandler.execute(war, 'heroic_throw', ['#990001'])
    check(beast.room is here and beast.hp < hp0, f'Heroic Throw pulls it in and wounds it ({hp0} -> {beast.hp})')
    for ch in (war, beast):
        ch.fighting = None
    # an aimed circle may land deep in the next room (no need to step in first)
    put(10.0)
    mage.web_pos = (here.vnum, 22.0, 7.5)
    aim = CommandHandler._aim_for(mage, 'meteor_storm', (34.0, 7.5))
    check(aim and aim[0] == 34.0, f'a meteor aimed 12 m away, 10 m into the next room, lands there ({aim})')
    from spells import SpellHandler
    caught = SpellHandler.foes_in_room(mage, aim)
    check(beast in caught and beast.room is here, 'what it catches there charges in and is struck')
    mage.web_pos = None
    check(CommandHandler._aim_for(mage, 'meteor_storm', (34.0, 7.5))[0] == 24.0, 'without a position the circle stays in the room')
    mage.web_pos = (here.vnum, 22.0, 7.5)
    war.room.characters.remove(war)
    beast.room.characters.remove(beast)
    world.npcs.remove(beast)
    here.characters.remove(mage)
    check('reachAcross(t, range, pulls)' in src('main.js') and 'webpull ${refFor(t)}' in src('main.js') and 'strikesFrom(' in src('hud/hud.js'),
          '/play strikes across an open way from where the hero stands, and shows what reaches')
    ents_src = src('entities.js')
    check('moveTo(e, vnum, at = null)' in ents_src and 'this.moveTo(e, w.vnum, w.data)' in ents_src
          and 'this.moveTo(e, payload.vnum, m)' in ents_src and 'e.rush' in ents_src,
          '/play: a creature pulled in from next door runs across to where the server put it (no snap to a spawn spot)')
    check('leapAcross(t, then)' in src('main.js') and "ab.shape === 'dash'" in src('hud/hud.js'),
          '/play leaps across an open way, and lights the leaps that reach')

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
