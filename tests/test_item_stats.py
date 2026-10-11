"""What gear does, offline: the endgame items' stats (zones that give them as an `effects` dict)
load as the affects the game reads, gear that speeds regeneration does, the balance simulator
scores armour the right way round, and the weapon in hand decides the reach of an ordinary
blow (a bow shoots whoever holds it; a caster's bolt whatever they hold). A player's health,
mana, moves and six attributes count what they wear, everywhere: saved as their own, levelled
and spelled as their own, falling back when the gear comes off; a creature's stay its own.

    python3 tests/test_item_stats.py
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import test_webmove as tw  # noqa: E402  (check(), failures)

check, failures = tw.check, tw.failures


class Conn:
    async def send(self, message='', newline=True):
        pass

    async def send_prompt(self):
        pass


async def offline():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from objects import Object, effects_as_affects
    from player import Player
    from regeneration import RegenerationCalculator as Regen
    import combat_range as cr
    world = World(Config())
    await world.load()

    def obj(vnum):
        return Object.from_prototype(world.obj_prototypes[vnum], world)

    def affect(o, kind):
        return sum(a.get('value', 0) for a in o.affects if a.get('type') == kind)

    # every endgame item's stats load, under the names the game reads
    with_effects = [v for v, p in world.obj_prototypes.items() if isinstance(p, dict) and isinstance(p.get('effects'), dict)]
    check(len(with_effects) >= 60, f'{len(with_effects)} items give their stats as effects')
    loaded = [v for v in with_effects if obj(v).affects or obj(v).flags & {'water_breathing', 'haste', 'corruption_immunity'}]
    check(len(loaded) == len(with_effects), f'all of them load ({len(loaded)})')
    blade = obj(28050)
    check(affect(blade, 'hitroll') == 10 and affect(blade, 'damroll') == 12 and affect(blade, 'str') == 4,
          f'the Cinderbrand Greatsword: +10 to hit, +12 damage, +4 strength ({blade.affects})')
    coral = obj(24002)
    check(affect(coral, 'armor') == -35 and 'water_breathing' in coral.flags, f'Coral Plate: armour -35, water breathing ({coral.affects}, {coral.flags})')
    check(affect(obj(24501), 'sneak') == 25, 'stealth is sneaking')
    check(effects_as_affects({'strength': 2, 'haste': True, 'odd': 'x'}) == ([{'type': 'str', 'value': 2}], {'haste'}), 'the conversion')

    # a copy saved before the effects were read takes them from its prototype
    saved = blade.to_dict()
    saved['affects'] = []
    healed = Object.from_dict(saved, world)
    check(affect(healed, 'damroll') == 12, 'an old saved copy gets its stats back')

    # worn, they count: to hit, damage, armour; regeneration is faster
    hero = Player.create_new(name='Gearstat', password=None, race='human', char_class='warrior',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    hero.connection = Conn()
    hero.equipment = {}
    hit0, dam0, ac0 = hero.get_hit_bonus(), hero.get_damage_bonus(), hero.get_armor_class()
    hero.equipment['wield'] = blade
    hero.equipment['body'] = coral
    check(hero.get_hit_bonus() >= hit0 + 10 and hero.get_damage_bonus() >= dam0 + 12, f'the blade hits harder ({hit0}->{hero.get_hit_bonus()}, {dam0}->{hero.get_damage_bonus()})')
    check(hero.get_armor_class() <= ac0 - 35, f'the plate turns blows ({ac0}->{hero.get_armor_class()})')
    hero.max_hp = 1000
    hero.position = 'resting'
    base = Regen.calculate_hp_regen(hero, 0.05, 1.0)
    hero.equipment['neck1'] = obj(28059)            # Heartstone of the Expanse: +25% health, +15% mana and moves
    faster = Regen.calculate_hp_regen(hero, 0.05, 1.0)
    check(faster >= int(base * 1.2), f'a regeneration stone heals faster ({base} -> {faster} a tick)')
    check(Regen._gear(hero, 'mana_regen') == 1.15 and Regen._gear(hero, 'move_regen') == 1.15, 'and restores mana and moves faster')

    # the simulator chooses gear as a player would: lower armour class is better
    from tools.balance.sim import _score
    check(_score({'item_type': 'armor', 'affects': [{'type': 'armor', 'value': -35}]}) > _score({'item_type': 'armor', 'affects': [{'type': 'armor', 'value': -10}]}),
          'the simulator prefers -35 armour to -10')
    check(_score(world.obj_prototypes[28050]) > _score({'item_type': 'weapon', 'damage_dice': '10d6+24'}), "and counts an item's effects")

    # the weapon in hand decides the reach of an ordinary blow
    def armed(cls, vnum):
        p = Player.create_new(name=f'Reach{cls[:3]}', password=None, race='human', char_class=cls,
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        p.equipment = {'wield': obj(vnum)} if vnum else {}
        return cr.auto_range(p)
    bow = next(v for v, p in world.obj_prototypes.items() if isinstance(p, dict) and p.get('item_type') == 'weapon'
               and cr.WEAPON_RANGE.get(__import__('gear_look').weapon_piece(obj(v)).get('k'), (0,))[0] == 16.0)
    check(armed('warrior', bow) == (16.0, True), f'a warrior with a bow shoots ({obj(bow).name})')
    check(armed('ranger', 3022) == (cr.MELEE, False), 'a ranger with a sword swings')
    check(armed('mage', 3022) == (10.0, True), 'a mage throws a bolt whatever is in hand')
    check(armed('mage', bow) == (16.0, True), 'a mage with a bow shoots it')
    check(armed('thief', None) == (cr.MELEE, False), 'bare hands: arm\'s length')
    ranger = Player.create_new(name='Reachranger', password=None, race='human', char_class='ranger',
                               stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    check(cr.auto_range(ranger)[1], f'a ranger starts with a bow, and shoots ({getattr(ranger.equipment.get("wield"), "name", None)})')


async def gear_stats():
    """Health, mana, moves and attributes from gear, for players."""
    import json
    import tempfile
    from config import Config
    from world import World
    from objects import Object
    from player import Player
    from affects import AffectManager
    from regeneration import RegenerationCalculator as Regen
    world = World(Config())
    await world.load()

    def obj(vnum):
        return Object.from_prototype(world.obj_prototypes[vnum], world)

    hero = Player.create_new(name='Gearvital', password=None, race='human', char_class='mage',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    hero.connection = Conn()
    hero.equipment = {}
    hp0, mana0, con0 = hero.max_hp, hero.max_mana, hero.con
    hero.equipment['body'] = obj(24002)                 # Coral Plate: +200 health
    hero.equipment['hold'] = obj(30065)                 # +2 to all six attributes
    check(hero.max_hp == hp0 + 200, f'Coral Plate raises the real maximum: {hp0} -> {hero.max_hp}')
    check(all(getattr(hero, s) == 15 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')), 'the shard adds 2 to each attribute')
    check(hero.base_stat('con') == con0 == 13 and hero.gear_bonus('con') == 2, "the attribute's own value stays 13")
    hero.hp = 1
    hero.position = 'resting'
    check(Regen.calculate_hp_regen(hero, 0.05, 1.0) > 0 and hero.hp < hero.max_hp, 'it can be healed up to the new maximum')
    hero.hp = hero.max_hp
    # legacy names count too ('max_mana', 'constitution')
    ring = Object(0, world)
    ring.name = ring.short_desc = 'a test ring'
    ring.item_type, ring.wear_slot = 'armor', 'finger'
    ring.affects = [{'type': 'max_mana', 'value': 30}, {'type': 'constitution', 'value': 1}]
    hero.equipment['finger1'] = ring
    check(hero.max_mana == mana0 + 30 and hero.con == 16, f"'max_mana' and 'constitution' count ({hero.max_mana}, {hero.con})")
    # attributes count wherever they are read: armour class from dexterity, mana regeneration
    # from intelligence and wisdom
    ac_with = hero.get_armor_class()
    del hero.equipment['hold']
    check(hero.get_armor_class() > ac_with, 'two points of dexterity from gear improve armour class')
    hero.equipment['hold'] = obj(30065)

    # saved as their own, so nothing grows with each save
    saved_dir = Config.PLAYER_DIR
    with tempfile.TemporaryDirectory() as tmp:
        Config.PLAYER_DIR = tmp
        try:
            await hero.save()
            data = json.load(open(os.path.join(tmp, 'gearvital.json')))
            check(data['max_hp'] == hp0 and data['con'] == 13 and data['hp'] == hero.max_hp,
                  f"the save keeps their own maximum and attributes ({data['max_hp']}, {data['con']}), and the health they had")
            back = Player.load('Gearvital', world)
            check(back.max_hp == hero.max_hp and back.base_stat('max_hp') == hp0 and back.con == hero.con,
                  f'loaded, the gear adds again ({back.max_hp})')
            await back.save()
            again = json.load(open(os.path.join(tmp, 'gearvital.json')))
            check(again['max_hp'] == data['max_hp'] and again['str'] == data['str'], 'saved again: unchanged')
        finally:
            Config.PLAYER_DIR = saved_dir

    # a level and a spell move their own value only
    base = hero.base_stat('max_hp')
    await hero.level_up()
    check(hero.base_stat('max_hp') > base and hero.max_hp == hero.base_stat('max_hp') + 200, 'a level adds to their own maximum')
    s0 = hero.base_stat('str')
    a = AffectManager.apply_affect(hero, {'name': 'giant strength', 'type': 'modify_stat', 'applies_to': 'str', 'value': 2, 'duration': 5})
    check(hero.str == s0 + 2 + 2, "a spell's +2 on top of the gear's")
    AffectManager.remove_affect(hero, a)
    check(hero.base_stat('str') == s0, 'and it ends cleanly')

    # taken off, the maximum falls and health with it
    hero.hp = hero.max_hp
    del hero.equipment['body']
    hero.clamp_vitals()
    check(hero.max_hp == hero.base_stat('max_hp') and hero.hp == hero.max_hp, f'the plate taken off: health back to {hero.max_hp}')
    # hit counts the gear's dexterity once: 13 -> 15 is +1 to hit (counted twice, 17, it would be +2)
    gloves = Object(0, world)
    gloves.name = gloves.short_desc = 'test gloves'
    gloves.item_type, gloves.wear_slot = 'armor', 'hands'
    gloves.affects = [{'type': 'dex', 'value': 2}]
    hero.equipment = {}
    bare = hero.get_hit_bonus()
    hero.equipment = {'hands': gloves}
    check(hero.dex == 15 and hero.get_hit_bonus() - bare == 1, f'+2 dexterity from gloves is +1 to hit ({bare} -> {hero.get_hit_bonus()})')

    # a creature's attributes are its own; its gear counts only in its blows, as before
    mob = next(ch for r in world.rooms.values() for ch in getattr(r, 'characters', []) if not hasattr(ch, 'account_name'))
    con = mob.con
    mob.equipment['hold'] = obj(30065)
    check(mob.con == con and mob.gear_stat('con') == con + 2, "a creature's constitution stays its own")


async def main():
    await offline()
    await gear_stats()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
