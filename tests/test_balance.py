"""The marquee balance pass, offline: the stat fixes it found and the simulator it is built on.

    python3 tests/test_balance.py            # the fixes, the scale, and one quest simulated
    python3 tests/test_balance.py --quick    # without the simulated quest

- creatures wear the armour their zone files give them (`armor_class`, not only `ac`);
- the INT bonus to hit and the DEX bonus to damage apply (class names are lower case);
- a warrior's skills grow with level as their swings do;
- a creature that can't be charmed (or a boss) shrugs off Charm Person;
- a shield spell cast again renews itself instead of stacking (stoneskin twice was two shields);
- a boss whose blow lands on a pet goes on fighting (it froze mid-cast);
- a quest creature with a party's health doesn't take the boss kit meant for big world creatures;
- marquee_scale: dpr() follows the measured median hero; a quest's creatures are made for the
  classes that embarked (their damage, and what they can stand), a little harder each level;
- tools/balance/sim.py plays a quest through with sane numbers.
"""
import asyncio
import logging
import os
import random
import sys

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


async def main():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from player import Player
    import combat_hooks
    import marquee_scale as ms
    from bosses import create_mob_from_prototype
    from combat import CombatHandler

    # ---- the scale
    check(abs(ms.dpr(45) - 204) < 1 and abs(ms.dpr(60) - 332) < 2, f'dpr() follows the measured median hero ({ms.dpr(45):.0f} at 45, {ms.dpr(60):.0f} at 60)')
    check(all(abs(ms.minutes('elite', 46, 1, c) - 1.1) < 0.01 for c in ms.CLASS_K),
          "an elite takes ~66 s alone whatever the quest's class (its creatures are sized to the class)")
    check(ms.CLASS_K['warrior'] > 1.2 and ms.CLASS_K['mage'] < 0.8, 'a warrior hits harder than the median, a mage softer (measured)')
    check(ms.foe_damage_scale('boss', 1, 'thief') < ms.foe_damage_scale('boss', 1, 'warrior') < ms.foe_damage_scale('boss', 1, 'paladin'),
          "a thief's creatures hit softer than a warrior's, a paladin's harder (what each can stand, measured)")
    check(ms.foe_damage_scale('boss', 1, 'warrior', 60) > ms.foe_damage_scale('boss', 1, 'warrior', 45),
          'and a little harder at a higher quest level (heroes grow sturdier)')
    party = ['warrior', 'mage', 'cleric']
    k = sum(ms.CLASS_K[c] for c in party) / 3
    check(ms.foe_health('elite', 50, 3, party) == int(ms.ROUNDS['elite'] * ms.dpr(50) * k * ms.health_factor(3))
          and ms.foe_health('elite', 50, 1, ['thief']) == ms.foe_health('elite', 50, 1, 'thief'),
          "a party's creatures are made for everyone who embarked (their mean), a lone hero's for their class")
    check(abs(ms.minutes('elite', 50, 3, party) - ms.minutes('elite', 50, 3, 'warrior')) < 0.01,
          '…so a mixed party takes as long over a foe as a party of the quest\'s class would')

    world = World(Config())
    await world.load()
    world.web_map = None
    combat_hooks.install()
    room = world.rooms[3054] if 3054 in world.rooms else world.rooms[3001]
    left_as_found = list(room.characters)

    # ---- creatures wear their zone's armour
    proto = dict(world.mob_prototypes[9700])
    proto['armor_class'] = 17
    mob = create_mob_from_prototype(proto, world)
    check(mob.armor_class == 17, f"a creature wears the armour its zone file gives it (armor_class 17 -> {mob.armor_class})")
    old = {k: v for k, v in proto.items() if k != 'armor_class'}
    old['ac'] = 33
    check(create_mob_from_prototype(old, world).armor_class == 33, '…an older file\'s `ac` still works')

    # ---- class bonuses
    def hero(cls, level=45, **stats):
        p = Player(world)
        p.name, p.char_class, p.level = f'Bal{cls[:4].title()}', cls, level
        for k, v in stats.items():
            setattr(p, k, v)
        p.connection = Conn()
        return p
    smart, dull = hero('mage', int=22), hero('mage', int=10)
    check(smart.get_hit_bonus() > dull.get_hit_bonus(), f"a mage's INT helps them hit ({smart.get_hit_bonus()} vs {dull.get_hit_bonus()})")
    quick, slow = hero('thief', dex=22), hero('thief', dex=10)
    check(quick.get_damage_bonus() > slow.get_damage_bonus(), f"a thief's DEX adds to their damage ({quick.get_damage_bonus()} vs {slow.get_damage_bonus()})")

    # ---- warrior skills grow with level
    import warrior_abilities as wa
    random.seed(5)
    lo = sum(wa.get_weapon_damage(hero('warrior', level=10)) for _ in range(400)) / 400
    random.seed(5)
    hi = sum(wa.get_weapon_damage(hero('warrior', level=50)) for _ in range(400)) / 400
    check(hi > lo * 2, f"a level-50 warrior's skills hit far harder than a level-10's ({hi:.0f} vs {lo:.0f})")

    # ---- charm: not on a creature that can't be, nor a boss
    from spells import SpellHandler, SPELLS
    bard = hero('bard', level=50)
    bard.room = room
    room.characters.append(bard)
    elite = create_mob_from_prototype(dict(world.mob_prototypes[9710]), world)
    elite.room = room
    room.characters.append(elite)
    await SpellHandler.apply_spell(bard, elite, SPELLS['charm_person'], 'charm_person')
    flags = getattr(elite, 'affect_flags', set()) or set()
    check('charmed' not in flags and any('unaffected' in l for l in bard.connection.lines),
          'a no_charm quest creature shrugs off Charm Person')
    plain = create_mob_from_prototype(dict(world.mob_prototypes[3062]), world)
    plain.room = room
    room.characters.append(plain)
    check(not CombatHandler.is_boss_mob(plain) and 'no_charm' not in set(getattr(plain, 'flags', ()) or ()),
          '(an ordinary creature can still be charmed: the rule only spares the immune)')

    # ---- a shield cast again renews itself
    from spells import SpellHandler as SH
    mage = hero('mage', level=50)
    mage.room = room
    room.characters.append(mage)
    mage.spells.update(stoneskin=80, armor=80)
    ac0 = mage.get_armor_class()
    for _ in range(3):
        await SH.apply_spell(mage, mage, SPELLS['stoneskin'], 'stoneskin')
        await SH.apply_spell(mage, mage, SPELLS['armor'], 'armor')
    skins = [a for a in mage.affects if a.applies_to == 'stoneskin']
    check(len(skins) == 1 and mage.get_armor_class() == ac0 - 20,
          f'stoneskin and armor cast three times: one shield, -20 AC ({len(skins)} shields, AC {ac0} -> {mage.get_armor_class()})')

    # ---- a boss whose blow lands on a pet goes on fighting
    import time as _t
    from pets import Pet
    from bosses import Boss
    boss = create_mob_from_prototype(dict(world.mob_prototypes[9706]), world)
    check(isinstance(boss, Boss), '(Gorrund is a scripted boss)')
    boss.room = room
    room.characters.append(boss)
    pet = Pet(0, world, bard, 'undead')
    pet.name = pet.short_desc = 'a bone knight'
    pet.max_hp = pet.hp = 500
    pet.room = room
    room.characters.append(pet)
    boss.fighting = pet
    boss.position = 'fighting'
    charge = next(a for a in boss.abilities if a.get('name') == 'Siege Charge')
    await boss._start_ability(charge)
    first = boss.ai_state['cast']
    first['resolve_at'] = _t.time() - 1
    err = None
    try:
        await boss.process_ai()
    except Exception as e:
        err = e
    check(err is None and boss.ai_state.get('cast') is not first and pet.hp < 500,
          f"a boss's blow lands on the pet holding it, and the boss goes on ({err!r}, pet {pet.hp}/500)")

    # ---- a quest creature with a party's health keeps its own kit
    import mob_ai
    big = create_mob_from_prototype(dict(world.mob_prototypes[9700]), world)
    big.max_hp = big.hp = 9000
    plain_big = create_mob_from_prototype(dict(world.mob_prototypes[9700]), world)
    plain_big.max_hp = plain_big.hp = 9000
    big.marquee_tag = {'kind': 'elite'}
    check('boss' not in mob_ai.classify_mob(big) and 'boss' in mob_ai.classify_mob(plain_big),
          "a quest creature made for a party isn't handed the boss kit (a room-wide slam every 8 s); a big world creature still is")

    # ---- the simulator plays a quest through (in the room the checks above used: empty it again)
    room.characters[:] = left_as_found
    if '--quick' not in sys.argv:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'balance'))
        import importlib
        sim = importlib.import_module('sim')
        sim.patch_deaths(world)
        sim.patch_damage()
        res = await sim.run_quest(world, 'warrior', 45, 1, 'rounds', 0.6, 1.0, 0.75, seed=1000)
        total = sum(s['fight'] + s['rest'] + s['travel'] for s in res['stages'])
        fight = sum(s['fight'] for s in res['stages'])
        check(len(res['stages']) == 7 and 40 < total < 240, f'sim: a lone level-45 warrior plays The Unbroken Banner through ({total:.0f} min)')
        check(5 < fight < 60 and len(res['deaths']) <= 2, f'sim: …about {fight:.0f} min of fighting, {len(res["deaths"])} deaths')
        check(0.8 * ms.dpr(45) < res['owner_dpr'] < 2.2 * ms.dpr(45), f"sim: a warrior's damage per round is near dpr() x their class ({res['owner_dpr']:.0f})")

    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
