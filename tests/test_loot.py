"""What creatures carry and drop (Push 32), offline.

A creature spawned from its zone carries what the zone gave it (its `inventory`: keys, coins,
gear) and rolls the drops its zone wrote for it (`loot_table`); a shopkeeper's wares stay its
shop; a creature with neither still gets the generic tier table. And `gearup` kits a character
out for endgame testing.

    python3 tests/test_loot.py
"""
import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import test_webmove as tw  # noqa: E402

check, failures = tw.check, tw.failures


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    Config.PLAYER_DIR = tempfile.mkdtemp()
    from world import World
    from bosses import create_mob_from_prototype
    from player import Player
    from commands import CommandHandler
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    protos = world.mob_prototypes
    carrier = next(p for p in protos.values() if p.get('inventory') and not p.get('shop_config') and not p.get('boss_config'))
    mob = create_mob_from_prototype(dict(carrier), world)
    want = len([e for e in carrier['inventory']])
    check(len(mob.inventory) >= 1 and len(mob.inventory) <= want, f'a creature carries what its zone gave it ({len(mob.inventory)} of {want})')
    keyed = next((p for p in protos.values() if any(
        (world.obj_prototypes.get(e.get('vnum') if isinstance(e, dict) else e) or {}).get('item_type') == 'key'
        for e in p.get('inventory') or [])), None)
    if keyed:
        km = create_mob_from_prototype(dict(keyed), world)
        check(any(getattr(o, 'item_type', '') == 'key' for o in km.inventory), f'a key its zone gave it is in its pockets ({keyed.get("short_desc")})')
    looter = next(p for p in protos.values() if p.get('loot_table') and not p.get('boss_config'))
    lm = create_mob_from_prototype(dict(looter), world)
    want_v = {e.get('vnum') if isinstance(e, dict) else e for e in looter['loot_table']}
    got_v = {e.get('vnum') if isinstance(e, dict) else e for e in lm.loot_table}
    check(want_v <= got_v, 'a creature rolls the drops its zone wrote for it')
    built = [p for v, p in protos.items() if 600000 <= v < 700000 and p.get('loot_table')]
    bm = create_mob_from_prototype(dict(built[0]), world)
    check(any(isinstance(e, dict) and 700000 <= e.get('vnum', 0) < 800000 for e in bm.loot_table), "the build-out's creatures drop its items")
    keeper = next((p for p in protos.values() if p.get('shop_config') and p.get('special') == 'shopkeeper' and p.get('inventory')), None)
    if keeper:
        sk = create_mob_from_prototype(dict(keeper), world)
        check(not any(o for o in sk.inventory if getattr(o, 'vnum', None) in {e.get('vnum') if isinstance(e, dict) else e for e in keeper['inventory']} and o not in getattr(getattr(sk, 'shop', None), 'inventory', [])), "a shopkeeper's wares are its shop, not loot")
    plain = next(p for p in protos.values() if not p.get('loot_table') and not p.get('boss_config'))
    pm = create_mob_from_prototype(dict(plain), world)
    check(bool(pm.loot_table), 'a creature with no drops of its own still has the tier table')

    # ---- gearup
    hero = Player.create_new(name='Kittest', password=None, race='human', char_class='mage',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    hero.connection = tae.Conn()
    hero.room = world.rooms[3001]
    world.players['kittest'] = hero
    real = Player.is_immortal
    Player.is_immortal = property(lambda self: True)
    try:
        await CommandHandler.cmd_gearup(hero, ['kittest'])
    finally:
        Player.is_immortal = real
    from prestige import get_max_level
    from sets import NAMED_SETS
    check(hero.level == get_max_level(hero), f'gearup raises to the highest level ({hero.level})')
    check(len(hero.equipment) >= 15, f'gearup fills the slots ({len(hero.equipment)})')
    worn = {getattr(i, 'vnum', None) for i in hero.equipment.values() if i}
    check(any(len(worn & set(s['pieces'])) == len(s['pieces']) for s in NAMED_SETS.values()), 'gearup puts on a whole named set')
    check(getattr(hero.equipment.get('wield'), 'rarity', '') == 'legendary', 'gearup puts a legendary in the hand')
    check(hero.mount is not None and hero.gold >= 50000, 'gearup gives gold and a mount, ridden')

    # ---- a corpse shows what it holds (the 3D loot window), and each thing can be taken
    from combat import CombatHandler
    from map_system import item_info
    room = hero.room
    victim = create_mob_from_prototype(dict(carrier), world)
    victim.room = room
    room.characters.append(victim)
    victim.hp = 0
    hero.autoloot = hero.autoloot_gold = hero.autogold = False
    await CombatHandler.handle_death(hero, victim)
    corpse = next((o for o in room.items if str(o.name).startswith('corpse of')), None)
    info = item_info(corpse) if corpse else {}
    check(corpse is not None and len(info.get('contents', [])) == len(corpse.contents) > 0,
          f"a corpse sends what it holds to the loot window ({len(info.get('contents', []))} things)")
    first = corpse.contents[0]
    word = next(w for w in str(first.name).lower().split() if len(w) > 1)
    await CommandHandler.cmd_get(hero, [word, 'from', 'corpse'])
    check(first in hero.inventory and first not in corpse.contents, 'the window takes one thing with `get <it> from corpse`')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
