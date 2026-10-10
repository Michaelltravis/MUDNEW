"""The marquee abilities and the rules they rest on, offline on the real world with real Player
objects (no server): each ability's numbers in multiples of a hero's round of damage
(marquee_scale.dpr), the boss rule, root and slow, the death ward's paths, the round engine's
clean-up, and the fixes made with them (stats saved without buffs, a death's corpse, rooms
written with `title`, multi-word commands).

    python3 tests/test_marquee_abilities.py
"""
import asyncio
import json
import logging
import os
import random
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import test_webmove as tw  # noqa: E402  (check(), failures)

check, failures = tw.check, tw.failures


class Conn:
    def __init__(self):
        self.lines = []

    async def send(self, message='', newline=True):
        self.lines.append(str(message))

    def said(self, text):
        return any(text in s for s in self.lines)


def put(ch, room):
    if getattr(ch, 'room', None) is not None and ch in ch.room.characters:
        ch.room.characters.remove(ch)
    ch.room = room
    room.characters.append(ch)


async def main():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from player import Player
    import combat_hooks
    import combat_range as cr
    import marquee_abilities as ma
    import marquee_scale as ms
    import mastery
    import marquee
    from commands import CommandHandler
    from combat import CombatHandler
    from bosses import create_mob_from_prototype
    from affects import AffectManager

    world = World(Config())
    await world.load()
    world.web_map = None
    combat_hooks.install()
    ma.install()
    mastery.install()

    async def no_loop():
        return None
    marquee._loop = no_loop
    marquee.install(world)
    random.seed(7)
    ROOM = world.rooms[3054] if 3054 in world.rooms else world.rooms[3001]

    def hero(name, cls, level=50, room=ROOM):
        p = Player(world)
        p.name, p.char_class, p.level = name, cls, level
        p.max_hp = p.hp = 600
        p.max_mana = p.mana = 600
        p.connection = Conn()
        world.players[name.lower()] = p
        put(p, room)
        cr.set_pos(p, 12, 7)
        return p

    def foe(vnum, x, z, against, room=ROOM):
        mob = create_mob_from_prototype(world.mob_prototypes[vnum], world)
        mob.max_hp = mob.hp = 20000
        put(mob, room)
        world.npcs.append(mob)
        cr.set_pos(mob, x, z)
        mob.fighting = against
        against.fighting = mob
        return mob

    def clear():
        for ch in list(ROOM.characters):
            if not hasattr(ch, 'account_name') and getattr(ch, 'vnum', 0) >= 9700:
                ROOM.characters.remove(ch)
        ma.EFFECTS.clear()

    dpr = ms.dpr(50)

    # ---------------- Singularity: pull, hold, crush, implode, slow; a boss only staggers
    mage = hero('Mira', 'mage')
    mage.skills['singularity'] = 50
    a, b, c = foe(9704, 4, 3, mage), foe(9704, 20, 12, mage), foe(9704, 9, 11, mage)
    boss = foe(9706, 18, 3, mage)
    mage.fighting = a
    bpos = cr.pos_of(boss)
    await CommandHandler.execute(mage, 'singularity', [])
    point = cr.pos_of(a)
    near = all(cr.distance(m, a) is not None and cr.distance(m, a) < 2.6 for m in (b, c))
    check(near, f"the foes are dragged to one point ({[cr.pos_of(m) for m in (a, b, c)]})")
    check(cr.pos_of(boss) == bpos and time.time() < boss.staggered_until and not getattr(boss, 'rooted_until', 0),
          'a boss is not moved or held: it staggers')
    first = 20000 - b.hp
    check(0.7 * dpr < first < 1.4 * dpr, f'the first crush is about a round of damage ({first} vs {dpr:.0f})')
    check(time.time() < b.rooted_until, 'they are held')
    cr.move_tick(world, 1.0)
    check(cr.distance(b, a) < 2.6, 'a held foe does not move')
    check(getattr(mage, '_ability_scale', 1) == 1, 'no damage scale is left on the caster after the command')
    await ma.on_round(world)
    second = 20000 - b.hp - first
    check(0.7 * dpr < second < 1.4 * dpr, f'it crushes again next round ({second})')
    await ma.on_round(world)
    implode = 20000 - b.hp - first - second
    check(3.0 * dpr < implode < 5.5 * dpr, f'then it implodes ({implode} vs {4 * dpr:.0f})')
    check(time.time() < b.slowed_until and not getattr(boss, 'slowed_until', 0), 'leaving them slowed (not the boss)')
    check(('mira', 'singularity') not in ma.EFFECTS, 'the effect is over')
    check(mage.marquee_cd.get('singularity', 0) > time.time() + 400, 'its cooldown is kept on the character')
    mage.connection.lines.clear()
    await CommandHandler.execute(mage, 'singularity', [])
    check(mage.connection.said('not ready'), 'used again at once: not ready yet')
    # slowed creatures swing about half as often
    b.fighting, mage.fighting = mage, b
    cr.set_pos(b, 13, 7)
    b.max_hp = b.hp = 20000

    async def landed(slowed):
        n = 0
        for _ in range(150):
            b.slowed_until = time.time() + 30 if slowed else 0
            b.stunned_rounds, b.staggered_until, b.rooted_until = 0, 0, 0
            b.fighting, mage.fighting = mage, b
            mage.hp = mage.max_hp
            await CombatHandler.one_round(b, mage)
            n += mage.hp < mage.max_hp
        return n
    quick, slowed = await landed(False), await landed(True)
    check(quick > 30 and slowed < 0.75 * quick, f'a slowed creature lands about half as many blows ({slowed} vs {quick})')
    clear()

    # ---------------- Seraph's Vigil: the most wounded healed each round; a killing blow turned aside once
    cleric = hero('Celes', 'cleric')
    cleric.skills['seraphs_vigil'] = 50
    tank = hero('Tor', 'warrior')
    from groups import Group
    g = Group(cleric)
    g.add_member(tank)
    cleric.group = tank.group = g
    brute = foe(9704, 13, 7, tank)
    tank.hp = 120
    await CommandHandler.execute(cleric, 'seraphs_vigil', [])
    check(tank.hp >= 120 + int(0.15 * 600) - 1, f'the seraph heals the most wounded ({tank.hp})')
    check(tank._mq_ward and cleric._mq_ward, 'each ally beside the cleric is warded')
    tank.hp = 10
    killed = await tank.take_damage(5000, brute)
    check(killed is False and tank.hp == 1 and tank.room is ROOM, 'a killing blow is turned aside: 1 HP, still standing here')
    killed = await tank.take_damage(5000, brute)
    check(killed is True and tank.room is not ROOM, 'the ward holds once: the next killing blow kills')
    put(tank, ROOM)
    tank.hp = tank.max_hp
    # a hazard (die() with no killer) is turned aside too; another player is not
    ma._ward(tank, time.time() + 30, 0.0, 'The seraph', "Seraph's Vigil")
    await tank.die(None)
    check(tank.room is ROOM and tank.hp == 1, 'a hazard is turned aside too')
    ma._ward(tank, time.time() + 30, 0.0, 'The seraph', "Seraph's Vigil")
    rival = hero('Rex', 'warrior')
    tank.hp = 5
    killed = await tank.take_damage(5000, rival)
    check(killed is True, 'never against another player')
    put(tank, ROOM)
    tank.hp = tank.max_hp
    # the vigil ends with its caster gone; its wards go with it
    tank._mq_ward = None
    cleric.marquee_cd = {}
    await CommandHandler.execute(cleric, 'seraphs_vigil', [])
    check(('celes', 'seraphs_vigil') in ma.EFFECTS, 'a new vigil runs')
    world.players.pop('celes')
    await ma.on_round(world)
    check(('celes', 'seraphs_vigil') not in ma.EFFECTS and not getattr(tank, '_mq_ward', None),
          'logging out ends the vigil and its wards')
    world.players['celes'] = cleric
    clear()

    # ---------------- Wings of Dawn: radiant damage within 6 m, heals and a shield that does not stack
    pal = hero('Paz', 'paladin')
    pal.skills['wings_of_dawn'] = 50
    close, far = foe(9704, 14, 7, pal), foe(9704, 22, 13, pal)
    pal.hp = 300
    await CommandHandler.execute(pal, 'wings_of_dawn', [])
    hit = 20000 - close.hp
    check(3.0 * dpr < hit < 5.5 * dpr and far.hp == 20000, f'radiant damage within 6 m ({hit}), none beyond')
    check(pal.hp >= 300 + 150 - 1, f'healed a quarter of their health ({pal.hp})')
    wards = [a for a in pal.affects if a.name == 'wings_of_dawn']
    check(len(wards) == 1 and wards[0].value == 90, f"shielded for 15% ({[w.value for w in wards]})")
    pal.marquee_cd = {}
    await CommandHandler.execute(pal, 'wings', ['of', 'dawn'])
    check(len([a for a in pal.affects if a.name == 'wings_of_dawn']) == 1, 'typed "wings of dawn" works, and the shield refreshes instead of stacking')
    clear()

    # ---------------- Lich Ascension: half-cost spells, drain, a split bolt, death turned away at 30%
    necro = hero('Nyx', 'necromancer')
    necro.skills['lich_ascension'] = 50
    necro.skills['soul_bolt'] = 60
    m1, m2 = foe(9704, 14, 7, necro), foe(9704, 15, 9, necro)
    necro.fighting = m1
    m2.fighting = necro
    await CommandHandler.execute(necro, 'lich_ascension', [])
    check(time.time() < necro.lich_until, 'the lich form begins')
    necro.hp = 300
    await m1.take_damage(400, necro)
    check(necro.hp >= 300 + 90, f'a quarter of what the lich deals drains back ({necro.hp})')
    from spells import SpellHandler, SPELLS
    necro.spells['chill_touch'] = 80
    necro.mana = 500
    await SpellHandler.cast_spell(necro, 'chill_touch', m1.name.split()[0])
    spent = 500 - necro.mana
    cost = (SPELLS.get('chill_touch') or {}).get('mana_cost', 0)
    check(0 < spent <= max(1, cost // 2 + 1) or cost <= 1, f'spells cost half ({spent} of {cost})')
    necro.soul_shards = 10
    necro.soul_bolt_cooldown = 0
    hp2 = m2.hp
    await CommandHandler.execute(necro, 'soul_bolt', [])
    check(m2.hp < hp2, f'a soul bolt splits to a second foe ({hp2 - m2.hp})')
    necro.hp = 5
    killed = await necro.take_damage(5000, m1)
    check(killed is False and necro.hp == int(600 * 0.30), f'death is turned away once, back at 30% ({necro.hp})')
    clear()

    # ---------------- Unbroken Banner: allies deal a quarter more (to creatures), no stat affect
    war = hero('Ward', 'warrior')
    war.skills['unbroken_banner'] = 50
    dummy = foe(9704, 13, 7, war)
    base_hp = dummy.hp
    await dummy.take_damage(200, war)
    plain = base_hp - dummy.hp
    dmg0 = war.damroll
    await CommandHandler.execute(war, 'unbroken', ['banner'])
    check(war.damroll == dmg0 and 'banner' in war._mq_out, 'the banner gives a damage bonus, not a stat affect')
    hp0 = dummy.hp
    await dummy.take_damage(200, war)
    check(abs((hp0 - dummy.hp) - plain * 1.25) <= 3, f'+25% to creatures under the banner ({plain} -> {hp0 - dummy.hp})')
    clear()

    # ---------------- refusals say "cannot" (no animation, no mastery gain)
    duelist = hero('Dee', 'mage')
    duelist.skills['singularity'] = 50
    duelist.dueling = war
    foe(9704, 13, 7, duelist)
    await CommandHandler.execute(duelist, 'singularity', [])
    check(duelist.connection.said('cannot') and not duelist.marquee_cd, 'not in a duel or the arena')
    duelist.dueling = None
    wrong = hero('Wren', 'thief')
    await ma.singularity(wrong, [])
    check(wrong.connection.said('cannot use Singularity'), 'another class cannot use it')
    clear()

    # ---------------- stats are saved without the buffs on them
    saver = hero('Zzmarqtest', 'warrior')
    base = saver.damroll
    AffectManager.apply_affect(saver, {'name': 'test_rage', 'type': AffectManager.TYPE_MODIFY_STAT, 'applies_to': 'damroll',
                                       'value': 10, 'duration': 5, 'caster_level': 50})
    await saver.save()
    path = os.path.join(saver.config.PLAYER_DIR, 'zzmarqtest.json')
    data = json.load(open(path))
    check(data['damroll'] == base, f'a buffed stat is saved without the buff ({data["damroll"]} vs {base})')
    again = Player.load('Zzmarqtest', world)
    rage = next((a for a in again.affects if a.name == 'test_rage'), None) if again else None
    check(again is not None and again.damroll == base + 10 and rage is not None, f'reloaded: the buff is back on once ({again and again.damroll})')
    if rage is not None:
        AffectManager.remove_affect(again, rage)
        check(again.damroll == base, f'and when it ends the stat is where it began ({again.damroll})')

    # ---------------- a death leaves a corpse with what you carry; you keep what you wear, every time
    from objects import Object
    victim = hero('Zzmarqtest', 'warrior')
    killer = foe(9704, 13, 7, victim)
    for n in range(2):
        put(victim, ROOM)
        victim.hp = victim.max_hp
        blade, pouch = Object(0, world), Object(0, world)
        blade.name, blade.short_desc = f'test blade {n}', 'a test blade'
        pouch.name, pouch.short_desc = f'test pouch {n}', 'a test pouch'
        victim.equipment['wield'] = blade
        victim.inventory = [pouch]
        if await victim.take_damage(99999, killer):
            await CombatHandler.handle_death(killer, victim)
        corpses = [o for o in getattr(victim.room, 'items', []) if getattr(o, 'name', '') == 'corpse of Zzmarqtest'
                   and any(getattr(x, 'name', '') == f'test pouch {n}' for x in getattr(o, 'contents', []))]
        check(corpses and victim.equipment.get('wield') is blade,
              f'death {n + 1}: a corpse holds what was carried; the worn blade stays on')
    try:
        os.remove(path)
    except OSError:
        pass
    world.players.pop('zzmarqtest', None)

    # ---------------- rooms written with `title` load with their names
    empty = [v for v, r in world.rooms.items() if r.zone and r.zone.number in (90, 100, 110, 130, 160) and r.name == 'An Empty Room']
    check(not empty and world.rooms[16010].sector_type == 'mountain',
          f"the Plane of Chaos and four more zones have their room names ({world.rooms[16010].name})")

    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
