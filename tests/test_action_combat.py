"""Real-time combat (action_combat.py) and the plumbing under it, offline: a real world, real
characters, the 3D client stood in for by a fake map server.

    python3 tests/test_action_combat.py

- combat events: each action holds only its own events (overlapping actions never wait for
  each other), a mark taken in the hold puts the action ahead of its wounds, a task an action
  started goes on alone once the action ends;
- the round says what became of each swing (hit, crit, miss, dodge, block, a lost turn);
- action mode: who is in it (a live /play client that asked), the creatures on its clock, the
  3-s round leaving their swings alone, webattack (first blow at once, then the clock), the
  global cooldown and its refusal wording, perfect strike by press timing;
- bosses never take the bruiser's blows on top of their own rotation.
"""
import asyncio
import logging
import os
import random
import sys
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import test_webmove as tw  # noqa: E402  (check(), failures)

check, failures = tw.check, tw.failures


class Conn:
    def __init__(self):
        self.lines = []

    async def send(self, message='', newline=True):
        self.lines.append(str(message))

    async def send_prompt(self):
        pass

    def said(self, text):
        return any(text.lower() in s.lower() for s in self.lines)


class FakeMap:
    """The map server as action_combat and combat_events see it."""
    def __init__(self):
        self.clients = []
        self.room_events = []
        self.private = []

    def opt_in(self, name, combat='action'):
        self.clients.append(types.SimpleNamespace(player_name=name, combat=combat, mode='near'))

    async def send_room_event(self, room, msg):
        self.room_events.append((getattr(room, 'vnum', None), [e['k'] for e in msg['events']]))
        self.full = getattr(self, 'full', []) + list(msg['events'])

    async def notify_event(self, ch, msg):
        self.private.extend(msg['events'])

    async def notify_combat(self, ch):
        pass

    async def notify_room(self, *a, **k):
        pass

    async def notify_player(self, *a, **k):
        pass


def put(ch, room):
    if getattr(ch, 'room', None) is not None and ch in ch.room.characters:
        ch.room.characters.remove(ch)
    ch.room = room
    room.characters.append(ch)


async def events():
    import combat_events as ev
    wm = FakeMap()
    room = types.SimpleNamespace(vnum=1, characters=[types.SimpleNamespace(world=types.SimpleNamespace(web_map=wm))])
    ev.emit(room, 'loose')
    await asyncio.sleep(0.01)
    check(wm.room_events == [(1, ['loose'])], f'an event outside any action goes out at once ({wm.room_events})')
    wm.room_events.clear()

    async def action(tag, delay):
        with ev.hold():
            m = ev.mark(room)
            ev.emit(room, f'{tag}-wound')
            await asyncio.sleep(delay)
            with ev.hold():
                ev.emit(room, f'{tag}-more')
            ev.emit_at(room, m, f'{tag}-swing')

    slow = asyncio.create_task(action('slow', 0.08))
    await asyncio.sleep(0.005)
    fast = asyncio.create_task(action('fast', 0.01))
    await fast
    await asyncio.sleep(0.02)
    check(wm.room_events == [(1, ['fast-swing', 'fast-wound', 'fast-more'])],
          f'a short action goes out while a long one is still running ({wm.room_events})')
    await slow
    await asyncio.sleep(0.02)
    check(wm.room_events[-1] == (1, ['slow-swing', 'slow-wound', 'slow-more']),
          "…and the long one in one piece when it ends, the swing ahead of its wounds")
    wm.room_events.clear()

    async def later():
        await asyncio.sleep(0.03)
        ev.emit(room, 'echo')
    with ev.hold():
        ev.emit(room, 'cast')
        child = asyncio.create_task(later())
    await asyncio.sleep(0.01)
    check(wm.room_events == [(1, ['cast'])], 'an action does not wait for a task it started')
    await child
    await asyncio.sleep(0.01)
    check(wm.room_events[-1] == (1, ['echo']), '…which sends on its own once the action is over')


async def main():
    logging.disable(logging.WARNING)
    await events()

    from config import Config
    from world import World
    from player import Player
    import combat_hooks
    import combat_range as cr
    import mastery
    import mob_ai
    import action_combat as ac
    from commands import CommandHandler
    from combat import CombatHandler
    from bosses import create_mob_from_prototype, Boss

    world = World(Config())
    await world.load()
    wm = FakeMap()
    world.web_map = wm
    combat_hooks.install()
    mastery.install()
    random.seed(11)
    ROOM = world.rooms[3054] if 3054 in world.rooms else world.rooms[3001]

    def hero(name, cls='warrior', level=30):
        p = Player(world)
        p.name, p.char_class, p.level = name, cls, level
        p.max_hp = p.hp = 900
        p.connection = Conn()
        p.world = world
        world.players[name.lower()] = p
        put(p, ROOM)
        cr.set_pos(p, 12, 7)
        return p

    def foe(vnum=3062, hp=5000):
        mob = create_mob_from_prototype(world.mob_prototypes[vnum], world)
        mob.max_hp = mob.hp = hp
        put(mob, ROOM)
        world.npcs.append(mob)
        cr.set_pos(mob, 13, 7)
        return mob

    def fight(a, b):
        a.fighting, b.fighting = b, a
        a.position = b.position = 'fighting'

    # ---------------- what the round says became of a swing
    real_randint = random.randint
    ace, mob = hero('Ace'), foe()
    fight(ace, mob)

    async def swing_with(prepare, low=False):
        ace.next_swing_at = 0
        prepare()
        random.randint = (lambda a, b: a) if low else (lambda a, b: b)
        try:
            return await CombatHandler.one_round(ace, mob)
        finally:
            random.randint = real_randint

    r = await swing_with(lambda: None)
    check(r and r['res'] == 'hit' and r['amt'] > 0, f'a landed blow: hit with its damage ({r})')
    r = await swing_with(lambda: setattr(ace, 'rigged_dice_hits', 1))
    check(r and r['res'] == 'crit', f'a certain critical: crit ({r})')
    r = await swing_with(lambda: setattr(ace, 'blinded_rounds', 2), low=True)
    check(r and r['res'] == 'miss', f'swinging blind: miss ({r})')
    ace.blinded_rounds = 0
    r = await swing_with(lambda: setattr(mob, 'evasion_until', time.time() + 5))
    check(r and r['res'] == 'dodge', f'an evading foe: dodge ({r})')
    mob.evasion_until = 0
    r = await swing_with(lambda: [setattr(mob, 'bone_shield_charges', 1), setattr(mob, 'bone_shield_until', time.time() + 5),
                                  setattr(mob, 'bone_shield_absorb', 10 ** 6)])
    check(r and r['res'] == 'block', f'a blow a bone shield swallows: block ({r})')
    r = await swing_with(lambda: setattr(ace, 'stunned_rounds', 1))
    check(r and r['res'] == 'skip', f'a stunned turn: skip ({r})')
    check(time.time() + 2.5 < ace.next_swing_at <= time.time() + 3.01, 'every turn taken restarts the swing clock')

    # ---------------- who fights in action mode
    check(not ac.wants(ace), 'no /play client asking: rounds')
    wm.opt_in('Ace', combat=None)
    check(not ac.wants(ace), 'a /play client with the setting off: rounds')
    wm.clients.clear()
    wm.opt_in('Ace')
    check(ac.wants(ace) and ac.on_clock(mob) and ac.round_skips(mob) and ac.round_skips(ace),
          'a /play client in action mode: the player and the creature fighting them are on the clock')
    Config.ACTION_COMBAT = False
    check(not ac.wants(ace) and not ac.on_clock(mob), 'the kill switch puts everyone back on rounds')
    Config.ACTION_COMBAT = True

    # the 3-s round leaves their swings alone, and brings the rest of the round
    extras = []
    real_extras = CombatHandler.round_extras.__func__

    async def counting(cls, a, d):
        extras.append(a.name)
        return await real_extras(cls, a, d)
    CombatHandler.round_extras = classmethod(counting)
    hp0, ace.next_swing_at = mob.hp, 0
    world.combat_tick.__func__  # (bound method exists)
    await world.combat_tick()
    await asyncio.sleep(0.05)
    check(mob.hp == hp0 and 'Ace' in extras, 'the 3-s round: no swing for an action-mode player, but its pets and rituals')
    CombatHandler.round_extras = classmethod(real_extras)

    # a swing on the clock leaves the rest of the round to the round
    extras.clear()
    CombatHandler.round_extras = classmethod(counting)
    ace.next_swing_at = 0
    r = await ac.swing(ace, mob)
    check(r is not None and 'Ace' not in extras, 'a swing on the clock leaves pets and rituals to the 3-s round')
    r2 = await ac.swing(ace, mob)
    check(r2 is None, 'a second swing before the clock comes round is refused')
    CombatHandler.round_extras = classmethod(real_extras)

    # ---------------- webattack: the first blow at once, then the clock
    bea, rat = hero('Bea'), foe()
    wm.opt_in('Bea')
    hp0 = rat.hp
    wm.private.clear()
    await CommandHandler.execute(bea, 'webattack', [f'#{__import__("map_system")._mob_uid(rat)}'])
    await asyncio.sleep(0.01)
    check(bea.fighting is rat and rat.hp < hp0 or bea.fighting is rat and getattr(bea, '_swing_res', None) in ('miss', 'dodge', 'parry', 'block'),
          f'webattack on a creature: the fight starts with a blow at once ({hp0 - rat.hp} damage, {getattr(bea, "_swing_res", None)})')
    swings = [e for e in wm.private if e.get('k') == 'swing']
    check(swings and 2500 <= swings[-1]['next_ms'] <= 3000, f'…and the client is told when the next one comes ({swings[-1:]})')
    hp1 = rat.hp
    await CommandHandler.execute(bea, 'webattack', [])
    await asyncio.sleep(0.01)
    check(rat.hp == hp1 and wm.private[-1].get('res') in ('not_ready', 'perfect'), 'pressed again at once: not ready, no blow')

    # perfect strike by press timing
    bea.perfect_next, bea.swing_lockout_until = False, 0
    bea.next_swing_at = time.time() + 0.4
    check(ac.perfect_press(bea) and bea.perfect_next, 'a press in the last 0.6 s before the swing: perfect')
    bea.perfect_next = False
    bea.next_swing_at = time.time() + 2.0
    check(not ac.perfect_press(bea) and bea.swing_lockout_until > time.time() + 1.9, 'a press too early: not perfect…')
    bea.next_swing_at = time.time() + 0.3
    bea.swing_lockout_until = bea.next_swing_at + 0.15
    check(not ac.perfect_press(bea), '…and that swing cannot be perfect any more (holding the key never pays)')

    # ---------------- the global cooldown
    bea.connection.lines.clear()
    bea.gcd_until = 0
    for a in ('kick', 'bash', 'rescue'):
        bea.skills[a] = 75
    bea.skills.setdefault('kick', 75)
    await CommandHandler.execute(bea, 'kick', [])
    first_gcd = getattr(bea, 'gcd_until', 0)
    bea.connection.lines.clear()
    await CommandHandler.execute(bea, 'bash', [])
    check(first_gcd > time.time() and bea.connection.said('Not ready yet'), 'a second skill within a second: "Not ready yet."')
    import mastery as m2
    check(any(w in 'not ready yet.' for w in m2._REFUSED) and any(w in 'not ready yet.' for w in combat_hooks._REFUSALS),
          '…worded as a refusal (no animation, no learning from it)')
    bea.gcd_until = 0
    bea.connection.lines.clear()
    await CommandHandler.execute(bea, 'nosuchskill', [])
    check(getattr(bea, 'gcd_until', 0) <= time.time(), 'something that is not a skill never starts the cooldown')
    bea.gcd_until = 0
    for e in ('brace', 'sidestep', 'flee'):
        check(not ac.gcd_applies(bea, e, e), f'{e} never waits for the cooldown')
    cid = hero('Cid')
    cid.skills['kick'] = cid.skills['bash'] = 75
    check(not ac.gcd_applies(cid, 'kick', 'kick'), 'a player in rounds (telnet, the 2D client) has no global cooldown')

    # ---------------- creatures on the clock
    ivy, wolf = hero('Ivy'), foe()
    wm.opt_in('Ivy')
    fight(ivy, wolf)
    now = time.time()
    await ac.mob_turn(wolf, now)
    check(now + 0.79 <= wolf._turn_at <= now + 1.21, 'a creature that turns on an action-mode player: first turn 0.8-1.2 s later')
    hp0 = ivy.hp
    wolf.next_swing_at = 0
    await ac.mob_turn(wolf, wolf._turn_at + 0.01)
    check(wolf._turn_at > now + 3.4 and getattr(wolf, 'next_swing_at', 0) > time.time() + 2, 'its turn: a swing, then the next turn ~3 s later')
    wm.clients = [c for c in wm.clients if c.player_name != 'Ivy']
    check(not ac.on_clock(wolf), 'its foe closes /play: back on the round')

    # a creature's wind-up on the action clock: 2 s, marked as 2 s, landed on its turn
    ivo, brute = hero('Ivo'), foe()
    wm.opt_in('Ivo')
    fight(ivo, brute)
    brute.ai_state = {}                  # a fresh foe: its opening wind-up is certain
    brute.level = ivo.level + 2          # (a far weaker one never winds up: trivial fights stay quick)
    brute.pending_intent = None
    wm.full = []
    await mob_ai.declare_intents(brute)
    await asyncio.sleep(0.02)
    wind = [e for e in wm.full if e.get('k') == 'windup']
    check(brute.pending_intent is not None and wind and wind[-1].get('ms') == 2000,
          f"its wind-up is marked as 2 s long ({wind[-1:] or brute.pending_intent})")
    if brute.pending_intent:
        brute.pending_intent['declared_at'] = time.time() - 2.05
        await ac.mob_turn(brute, time.time())
        await asyncio.sleep(0.02)
        check(brute.pending_intent is None and any(e.get('k') == 'resolve' for e in wm.full),
              'two seconds on, it lands (resolve)')

    # ---------------- bosses: their own rotation, never the bruiser's blows on top
    boss = None
    for vnum, proto in world.mob_prototypes.items():
        if 'boss' in set(proto.get('flags', []) if isinstance(proto, dict) else []):
            cand = create_mob_from_prototype(proto, world)
            if isinstance(cand, Boss):
                boss = cand
                break
    if boss is None:
        check(False, 'found a Boss to test')
    else:
        put(boss, ROOM)
        world.npcs.append(boss)
        cr.set_pos(boss, 12.5, 7)
        fight(boss, cid)
        check('scripted' in mob_ai.classify_mob(boss), f'a bosses.py boss ({boss.name}) is marked as scripted')
        called = []
        real_bruiser = mob_ai._choose_bruiser_intent
        mob_ai._choose_bruiser_intent = lambda m, t: called.append(m) or None
        for _ in range(20):
            boss.pending_intent = None
            await mob_ai.declare_intents(boss)
        mob_ai._choose_bruiser_intent = real_bruiser
        check(not called, "…and never takes the bruiser's crushing blows")
        import map_system
        check('scripted' not in map_system._mob_roles(boss), '…which the clients never see')

    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
