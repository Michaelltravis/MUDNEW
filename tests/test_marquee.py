"""The marquee quests (push 7): one per class, offered at level 45 by the class's trainer, ending
in a private trial; solo about two hours, harder for each member who embarks.

Offline: the scaling (health, damage, adds, tempo, rewards) by the number who embarked; a solo
quest's foes add up to about two hours with travel; Unbroken Banner is earned, never learned by
level, and its command refuses another class and a running cooldown.
Live (needs ./run.sh and the gauntlet accounts) — see live() below.
    python3 tests/test_marquee.py [--offline]
"""
import asyncio
import json
import os
import re
import sys
import time
import types

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import test_webmove as tw  # noqa: E402  (Telnet helper, check(), failures)

check, failures = tw.check, tw.failures


def fake_player(**kw):
    sent = []

    async def send(msg='', *a, **k):
        sent.append(str(msg))
    from config import Config
    p = types.SimpleNamespace(level=46, char_class='warrior', skills={}, spells={}, send=send, sent=sent, affects=[],
                              config=types.SimpleNamespace(COLORS=Config.COLORS), world=None, room=None, group=None,
                              name='Ann', hp=500, max_hp=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


async def offline():
    import marquee_scale as ms
    check(ms.health_factor(1) == 1 and abs(ms.health_factor(3) - 2.6) < 1e-9 and abs(ms.health_factor(6) - 5.0) < 1e-9,
          'health x1 alone, x2.6 for three, x5 for six')
    check(abs(ms.damage_factor(6) - 1.5) < 1e-9 and ms.extra_adds(1) == 0 and ms.extra_adds(3) == 1 and ms.extra_adds(6) == 2,
          'damage +10% a hero, one extra add a wave for every two more')
    check(ms.tempo(1) == 1 and ms.tempo(6) < 0.8, 'a boss acts sooner for a bigger party')
    check(ms.party_level(45, [52, 50]) == 49 and ms.party_level(58, [45]) == 58 and ms.party_level(40) == 45,
          "the quest's level: the owner's, or the party's average if higher, 45-60")
    solo = ms.minutes('elite', 46, 1)
    six = ms.minutes('elite', 46, 6)
    check(0.9 < solo < 1.4 and six < solo, f'an elite takes ~1 min alone ({solo:.2f}), a little less for six ({six:.2f})')
    boss = ms.minutes('boss', 47, 1)
    check(2.5 < boss < 3.5, f'the trial boss takes ~3 minutes alone ({boss:.1f})')
    check(ms.gold_reward(1000, 3) == 2000 and ms.exp_reward(1000, 3) == 2600, 'rewards grow with the party')

    import mastery
    from config import Config
    check('unbroken_banner' in [a for a, _k in mastery.roster('warrior')] and mastery.unlock_level('warrior', 'unbroken_banner') == 45,
          "Unbroken Banner is in the warrior's book at level 45")
    p = fake_player(level=60)
    mastery.grant_now(p)
    check('unbroken_banner' not in p.skills, 'reaching level 60 does not teach it: it is earned through the quest')
    e = next(x for x in mastery.book('warrior') if x['id'] == 'unbroken_banner')
    check(e.get('quest') == 'The Unbroken Banner' and e.get('marquee') and e.get('target') == 'self',
          f"the book says how it is earned ({e.get('quest')}) and it needs no target")

    import marquee_abilities as ma
    mage = fake_player(char_class='mage')
    await ma.unbroken_banner(mage, [])
    check(any('Only a warrior' in s for s in mage.sent), 'another class is refused')
    w = fake_player(marquee_cd={'unbroken_banner': __import__('time').time() + 200})
    await ma.unbroken_banner(w, [])
    check(any('not ready yet' in s for s in w.sent), 'a running cooldown is refused (and the cooldown is saved on the character)')


def _world_player(world, name, room, **kw):
    """A stand-in for a Player in a real loaded world (enough for marquee.py)."""
    sent = []

    async def send(msg='', *a, **k):
        sent.append(str(msg))

    async def save():
        pass

    async def gain_exp(amount, source='other', breakdown=None):
        p.exp += amount
    from config import Config
    p = types.SimpleNamespace(name=name, account_name=name.lower(), level=46, char_class='warrior', skills={}, spells={},
                              send=send, sent=sent, save=save, gain_exp=gain_exp, exp=0, gold=0, affects=[], position='standing',
                              config=types.SimpleNamespace(COLORS=Config.COLORS), world=world, room=None, group=None,
                              hp=600, max_hp=600, marquee=None, marquee_help=None, marquee_cd={}, fighting=None,
                              connection=None, is_immortal=False)
    for k, v in kw.items():
        setattr(p, k, v)
    world.players[name.lower()] = p
    put(p, world.rooms[room])
    return p


def put(ch, room):
    if getattr(ch, 'room', None) is not None and ch in ch.room.characters:
        ch.room.characters.remove(ch)
    ch.room = room
    room.characters.append(ch)


def said(p, text):
    return any(text in s for s in p.sent)


async def engine():
    """The quest engine on the real world, with stand-in players: offer, accept, every stage of
    the warrior's quest, the party's size in every foe, credit for any member's kill, outsiders
    kept out, the private trial opened, won and closed."""
    import logging
    logging.disable(logging.INFO)
    import json as _json
    from config import Config
    from world import World
    import marquee
    import marquee_quests as mq
    import marquee_scale as ms
    world = World(Config())
    await world.load()
    world.web_map = None

    async def no_loop():
        return None
    marquee._loop = no_loop                 # the test drives the ticks itself
    marquee.install(world)
    q = mq.QUESTS['warrior']

    # the quest's data points at things that exist
    for st in q['stages']:
        for v in [st.get('room'), *[sp['room'] for sp in st.get('spawns', [])], *st.get('rooms', [])]:
            check(v is None or v in world.rooms, f"{st['title']}: room {v} exists")
        for v in [st.get('npc'), st.get('mob'), st.get('adds'), *[sp['vnum'] for sp in st.get('spawns', [])],
                  *[w['vnum'] for w in st.get('waves', [])]]:
            check(v is None or v in world.mob_prototypes, f"{st['title']}: creature {v} exists")
    tpl = marquee._template('warrior')
    keys = {r['key'] for r in tpl['rooms']}
    check(tpl['entrance'] in keys and all(w['room'] in keys for w in tpl['waves']) and tpl['boss']['room'] in keys
          and all(ex['to'] in keys for r in tpl['rooms'] for ex in r['exits'].values()), 'the trial template hangs together')
    check(tpl['boss']['vnum'] in world.mob_prototypes and world.mob_prototypes[tpl['boss']['vnum']].get('boss_config'),
          'the trial boss has a boss config (phases, telegraphed abilities)')

    # too young: a hint; at 45: the offer
    gm = next(ch for ch in world.rooms[q['giver_room']].characters if getattr(ch, 'vnum', None) == q['giver'])
    kid = _world_player(world, 'Kid', q['giver_room'], level=30)
    await marquee.on_talk(kid, gm)
    check(said(kid, 'level 45') and not said(kid, 'marquee accept'), 'below level 45 the guildmaster says to come back')
    ann = _world_player(world, 'Ann', q['giver_room'], level=46)
    await marquee.on_talk(ann, gm)
    check(said(ann, 'A marquee quest: The Unbroken Banner') and said(ann, "marquee accept"), 'at 46 the guildmaster offers the quest')
    check(marquee.indicator(ann, q['giver']) == '!', "a '!' over the guildmaster")
    mage = _world_player(world, 'Mia', q['giver_room'], level=50, char_class='mage')
    await marquee.accept(mage)
    check(mage.marquee is None, 'another class cannot take the warrior quest')

    await marquee.accept(ann)
    m = ann.marquee
    check(m and m['n'] == 1 and m['party'] == ['Ann'] and m['stage'] == 0, 'accepted alone: a party of one')
    b = marquee.quest_block(ann)
    check(b['title'] == 'The Fallen Standard' and b['where']['vnum'] == 22005 and b['stage'] == 1 and b['of'] == 7,
          f"the tracker block: stage 1 of 7, marked at the West Wall Path ({b['where']})")
    j = marquee.journal_entry(ann)
    check(j['marquee'] and j['teaches'] == 'Unbroken Banner', 'the journal lists it, with what it teaches')

    # 1 talk: the figure is there (placed if need be) and speaking to it moves the quest on
    put(ann, world.rooms[22005])
    await marquee._step()
    crusader = next(ch for ch in world.rooms[22005].characters if getattr(ch, 'vnum', None) == 22098)
    await marquee.on_talk(ann, crusader)
    check(m['stage'] == 1, 'speaking with the dying crusader ends stage 1')

    # 2 kill: each war-chief appears when you come near, made for the party
    run = marquee.RUNS['ann']
    for i, sp in enumerate(q['stages'][1]['spawns']):
        put(ann, world.rooms[sp['room']])
        await marquee._step()
        chief = next(x for x in run.mobs if x.marquee_tag.get('slot') == i)
        if i == 0:
            check(chief.max_hp == ms.foe_health('elite', m['level'], 1, 'warrior') and chief.hp == chief.max_hp,
                  f"a war-chief's health is made for one ({chief.max_hp})")
            check(not any(x.marquee_tag.get('escort') is not None for x in run.mobs), 'alone: no thralls with it')
            stranger = _world_player(world, 'Sam', sp['room'], level=50)
            hit = await chief.take_damage(500, stranger)
            check(chief.hp == chief.max_hp and not hit and said(stranger, "belongs to Ann's quest"),
                  "someone outside the party cannot hurt it")
            put(stranger, world.rooms[3001])
        chief.hp = 0
        await marquee.fallen(chief, ann)
    check(m['stage'] == 2, 'three war-chiefs down: stage 2 done')

    # 3 collect: shades in the ash; about half give a core
    st = q['stages'][2]
    put(ann, world.rooms[st['rooms'][0]])
    import random as _r
    _r.seed(4)
    for _ in range(40):
        if m['stage'] != 2:
            break
        await marquee._step()
        run.respawn = {}
        shade = next((x for x in run.mobs if marquee._alive(x)), None)
        if shade is not None:
            shade.hp = 0
            await marquee.fallen(shade, ann)
    check(m['stage'] == 3, 'enough ember cores: stage 3 done')

    # 4 the warden: a boss, faster for a bigger party
    put(ann, world.rooms[6908])
    await marquee._step()
    smith = next(x for x in run.mobs if x.marquee_tag.get('slot') == 0)
    check(getattr(smith, 'boss_config', None) is not None and smith.max_hp == ms.foe_health('warden', m['level'], 1, 'warrior'),
          'the Cinder Smith is a boss made for one')
    smith.hp = 0
    await marquee.fallen(smith, ann)
    check(m['stage'] == 4, 'the Cinder Smith down: stage 4 done')

    # 5 the ritual: plant, hold, slay what comes; leaving breaks it
    put(ann, world.rooms[8002])
    await marquee.plant(ann)
    check(run.ritual is not None, 'the banner is planted')
    put(ann, world.rooms[8001])
    await marquee._step()
    check(run.ritual is None and said(ann, 'The banner topples'), 'walking away breaks the ritual')
    put(ann, world.rooms[8002])
    await marquee.plant(ann)
    run.ritual['start'] -= 40           # thirty seconds held
    await marquee._step()
    waves = [x for x in run.mobs if x.marquee_tag.get('wave') is not None]
    check(len(waves) == 7, f'three waves of drakelings came (7: {len(waves)})')
    for x in waves:
        x.hp = 0
    await marquee._step()
    check(m['stage'] == 5, 'held and cleared: stage 5 done')

    # 6 the trial: a private copy; gates open as the waves fall; the boss; it closes behind you
    await marquee.enter_trial(ann)
    t = run.trial
    check(t is not None and ann.room is t.rooms['wall'] and ann.room.vnum // 100 == t.zone.number and t.zone.number >= 7000,
          f'inside the trial (zone {t and t.zone.number})')
    check(getattr(ann.room, 'instance_exit', None) == 8002, 'its rooms name the way back (a save there comes back at the gate)')
    gate = ann.room.exits['north']['door']
    check(gate['state'] == 'closed' and gate['locked'], 'the portcullis is locked until the wave falls')
    for wave in range(3):
        room = t.rooms[tpl['waves'][wave]['room']]
        put(ann, room)
        await marquee._step()
        foes = [x for x in run.mobs if x.marquee_tag.get('wave') == wave]
        check(len(foes) == sum(c for _v, c in tpl['waves'][wave]['mobs']), f'wave {wave + 1}: {len(foes)} foes')
        for x in foes:
            x.hp = 0
        await marquee._step()
    check(t.rooms['wall'].exits['north']['door']['state'] == 'open' and t.rooms['breach'].exits['north']['door']['state'] == 'open',
          'both gates opened')
    put(ann, t.rooms['keep'])
    await marquee._step()
    check(t.boss is not None and t.boss.max_hp == ms.foe_health('boss', m['level'], 1, 'warrior'), "Gorrund waits in the keep")
    t.boss.hp = 0
    await marquee._step()
    check(m['stage'] == 6 and t.won, 'Gorrund down: the trial is won')
    vnums = [r.vnum for r in t.rooms.values()]
    await marquee.leave_trial(ann)
    check(ann.room.vnum == 8002, 'trial leave: back at the gate')
    for _ in range(2):
        t.empty_since = (t.empty_since or 0) - 10
        await marquee._step()
    check(run.trial is None and not any(v in world.rooms for v in vnums), 'the empty trial closed and its rooms left the world')

    # 7 home: the guildmaster teaches it
    put(ann, world.rooms[q['giver_room']])
    check(marquee.indicator(ann, q['giver']) == '?', "a '?' over the guildmaster when you come home")
    await marquee.on_talk(ann, gm)
    check(ann.skills.get('unbroken_banner') == 50 and ann.marquee is None and 'ann' not in marquee.RUNS,
          'the guildmaster teaches Unbroken Banner (50%); the quest is done')
    ann.sent.clear()
    await marquee.on_talk(ann, gm)
    check(not said(ann, 'A marquee quest') and marquee.eligible(ann) == 'learned', 'it is not offered again once learned')

    # a party of three: embarking fixes the size; every foe is made for it; any member's kill counts
    bo = _world_player(world, 'Bo', q['giver_room'], level=52, connection=True)
    cy = _world_player(world, 'Cy', q['giver_room'], level=50, connection=True)
    lea = _world_player(world, 'Lea', q['giver_room'], level=46, connection=True)
    grp = types.SimpleNamespace(members=[lea, bo, cy], leader=lea)
    for p in (lea, bo, cy):
        p.group = grp
    await marquee.accept(lea)
    check('lea' in marquee.VOTES and said(bo, "marquee join"), 'the group beside her is asked to embark')
    await marquee.answer(bo, True)
    await marquee.answer(cy, True)
    m3 = lea.marquee
    check(m3 and m3['n'] == 3 and m3['party'] == ['Lea', 'Bo', 'Cy'] and bo.marquee_help['owner'] == 'Lea',
          'three embarked: the party is fixed at three')
    check(m3['level'] == 49, f"the quest's level is the party's average when higher ({m3['level']})")
    m3['stage'] = 1
    run3 = marquee.RUNS['lea']
    put(bo, world.rooms[22030])
    await marquee._step()
    chief = next(x for x in run3.mobs if x.marquee_tag.get('slot') == 0)
    check(chief.max_hp == ms.foe_health('elite', 49, 3, 'warrior') and abs(chief._dmg_scale - 1.2) < 1e-9,
          f'made for three: x2.6 health, +20% damage ({chief.max_hp})')
    check(sum(1 for x in run3.mobs if x.marquee_tag.get('escort') == 0) == 1, 'and one thrall at its side')
    chief.hp = 0
    await marquee.fallen(chief, bo)
    check(m3['progress']['dead'][0], "a helper's kill counts for the quest")
    put(bo, world.rooms[22024])
    await marquee._step()
    chief2 = next(x for x in run3.mobs if x.marquee_tag.get('slot') == 1)
    del world.players['lea']                # the owner drops out mid-fight
    await chief2.take_damage(300, bo)
    check(chief2.hp < chief2.max_hp, 'with the owner away, a helper can still fight what is already out')
    world.players['lea'] = lea
    await marquee.abandon(cy)
    check(cy.marquee_help is None and m3['n'] == 3 and 'Cy' not in m3['party'], 'a helper may leave; the quest stays as hard')
    await marquee.abandon(lea, confirm=True)
    check(lea.marquee is None and bo.marquee_help is None and not run3.mobs, 'abandoned: foes gone, helpers released')
    logging.disable(logging.NOTSET)


# the quest's foes as a room shows them (their long line, or "<name> is here, fighting YOU!")
FOES = (('siegeman', 'siegeman'), ('siege hound', 'hound'), ('gorrund', 'gorrund'), ('drakeling', 'drakeling'))


def foe_in(look):
    for line in look.splitlines():
        low = line.lower()
        if low.startswith('the corpse') or ' is here' not in low and ' looms here' not in low and ' strains forward' not in low \
                and ' crouches here' not in low:
            continue
        for key, word in FOES:
            if key in low:
                return word
    return None


async def fight_here(tn, limit=240):
    """Fight every quest foe standing here (by its room line), restoring when low."""
    t0 = time.time()
    log = ''
    while time.time() - t0 < limit:
        look = await tn.cmd('look', 0.8)
        word = foe_in(look)
        if not word:
            return log
        out = await tn.cmd(f'kill {word}', 1.0)
        for _ in range(40):
            if 'is DEAD' in out:
                break
            chunk = await tn.read(1.5)
            out += chunk
            hp = re.findall(r'(\d+)/(\d+)hp', chunk)
            if hp and int(hp[-1][0]) < int(hp[-1][1]) // 2:
                await tn.cmd('restore', 0.3)
        log += out
    return log


async def live():
    """The warrior's quest on the running server with the test warrior (level 60, an immortal for
    the jumps): offer, accept, the first stage, the tracker in the map payload and the journal,
    a jump to the trial, the trial fought through (waves, gates, Gorrund), the return, the ability."""
    tn = tw.Telnet()
    await tn.open()
    for line in ('wake', 'stand', 'restore', 'marquee forget'):
        await tn.cmd(line, 0.5)
    await tn.cmd('goto 3023', 0.8)
    text = await tn.cmd('talk guildmaster', 1.2)
    check('A marquee quest: The Unbroken Banner' in text, 'the guildmaster offers the quest')
    text = await tn.cmd('marquee accept', 1.2)
    check('You set out alone' in text and 'The Fallen Standard (1/7)' in text, 'accepted alone: stage 1 of 7')

    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(f'ws://{tw.HOST}:{tw.MAP}/') as ws:
            await ws.send_str(tw.subscribe(tw.CHAR))
            block = None
            for _ in range(40):
                msg = await asyncio.wait_for(ws.receive(), timeout=10)
                d = json.loads(msg.data) if msg.type == aiohttp.WSMsgType.TEXT else {}
                if d.get('type') == 'map_data':
                    block = d['player'].get('quest')
                    break
    check(block and block['title'] == 'The Fallen Standard' and block['where']['vnum'] == 22005,
          f"the map payload carries the tracker ({block and block['title']}, marked {block and block['where']})")
    journal = tw.get_json(f'/quests?player={tw.CHAR}&t={tw.TOKEN}')
    mq_entry = next((q for q in journal.get('active', []) if q.get('marquee')), None)
    check(mq_entry and mq_entry['teaches'] == 'Unbroken Banner', 'the journal lists the marquee quest first')

    await tn.cmd('goto 22005', 2.5)
    text = await tn.cmd('talk crusader', 1.5)
    check('The Banner-Reavers (2/7)' in text, 'speaking with the dying crusader: stage 2')

    await tn.cmd('marquee stage 6', 0.8)
    await tn.cmd('goto 8002', 1.0)
    text = await tn.cmd('trial enter', 2.0)
    check('The Last Bastion - The Outer Wall' in text, 'trial enter: inside the Last Bastion')
    for step, (way, into) in enumerate((('north', 'The Breach'), ('north', 'The Keep'), (None, None))):
        await tn.read(3.5)
        log = await fight_here(tn)
        if step == 1:                       # the breach has a second wave
            await tn.read(3.0)
            log += await fight_here(tn)
        if way:
            await tn.read(1.6)              # the gate opens on the quest's next tick
            text = await tn.cmd(way, 1.5)
            ok = f'The Last Bastion - {into}' in text
            check(ok, f'the gate opened after the wave: {way} into {into}' + ('' if ok else f'\n{text[-900:]}'))
    await tn.read(1.6)
    text = await tn.cmd('marquee', 1.0)
    check('The Last Lesson (7/7)' in text, 'Gorrund down: the last stage')
    text = await tn.cmd('trial leave', 1.5)
    check("Dragon's Gate" in text, 'trial leave: back at the gate')
    await tn.cmd('goto 3023', 1.0)
    text = await tn.cmd('talk guildmaster', 2.0)
    check('You learned Unbroken Banner' in text, 'home: the guildmaster teaches Unbroken Banner')
    text = await tn.cmd('unbroken banner', 1.2)
    check('UNBROKEN' in text, 'and it works')
    text = await tn.cmd('unbroken banner', 1.0)
    check('not ready yet' in text, 'with its long cooldown')
    for line in ('marquee forget', 'recall', 'save'):
        await tn.cmd(line, 0.6)
    tn.w.close()


async def live_group():
    """Two players: the group beside the warrior is asked to embark; who joins makes every foe
    harder (x1.8 health for two); giving the quest up releases the helper."""
    import marquee_scale as ms
    import test_multiplayer as tmu
    g = await tmu.Raw('gauntlet', 'Gauntlet').open()
    b = await tmu.Raw('gauntletb', 'Gauntletb').open()
    for line in ('wake', 'stand', 'restore', 'marquee forget', 'group leave', 'goto 3023'):
        await g.cmd(line, 0.5)
    for line in ('wake', 'stand', 'marquee leave', 'group leave', 'goto 3023'):
        await b.cmd(line, 0.5)
    await g.cmd('group invite gauntletb', 0.8)
    await b.cmd('group accept', 0.8)
    text = await g.cmd('marquee accept', 1.0)
    check('You ask Gauntletb to embark' in text, 'accepting asks the group member beside you to embark')
    text = tmu.ANSI.sub('', await b.read(0.8))
    check('marquee join' in text, 'the member is asked to join')
    await b.cmd('marquee join', 1.0)
    text = await g.read(1.0)
    check('2 embarked' in text, f"both set out: two embarked ({text.strip().splitlines()[-2:] if text.strip() else ''})")
    text = await b.cmd('marquee', 0.8)
    check('The Fallen Standard' in text and 'with Gauntlet' in text, "the helper sees the quest they share")
    await g.cmd('marquee stage 2', 0.8)
    await g.cmd('goto 22030', 1.0)
    await g.read(3.5)
    text = await g.cmd('kill warchief', 1.5)
    hp = re.findall(r'Banner-Reaver war-chief: \d+/(\d+)', text)
    want = ms.foe_health('elite', 60, 2, 'warrior')
    check(hp and int(hp[-1]) == want, f'a war-chief made for two: {hp[-1] if hp else "?"} health (x1.8 = {want})')
    await g.cmd('restore', 0.4)
    await g.cmd('marquee abandon confirm', 1.0)
    text = await b.read(1.0)
    check('gives up the quest' in text, 'giving it up tells the helper')
    text = await b.cmd('marquee', 0.8)
    check('no marquee quest' in text, 'and releases them')
    for line in ('group leave', 'recall', 'save'):
        await b.cmd(line, 0.5)
        await g.cmd(line, 0.5)
    g.w.close()
    b.w.close()


async def main():
    await offline()
    await engine()
    if '--offline' not in sys.argv:
        await live()
        await live_group()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
