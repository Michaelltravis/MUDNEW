"""Gear that acts by itself, and sets that count (Push 32), offline.

    python3 tests/test_procs.py
"""
import asyncio
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import test_webmove as tw  # noqa: E402

check, failures = tw.check, tw.failures


class Always:
    """random.randint that always rolls the low end: every proc fires, every hit lands low."""
    def __enter__(self):
        self.orig = random.randint
        random.randint = lambda a, b: a
        return self

    def __exit__(self, *a):
        random.randint = self.orig


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    Config.PLAYER_DIR = tempfile.mkdtemp()
    from world import World
    from bosses import create_mob_from_prototype
    from player import Player
    from objects import create_object
    from commands import CommandHandler
    from combat import CombatHandler
    from legendary import create_legendary, LEGENDARY_BOSSES, LEGENDARY_ITEMS
    import combat_events as ev
    import procs
    import sets
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    room = world.rooms[3001]
    if 'peaceful' in (getattr(room, 'flags', None) or ()):
        room = next(r for r in world.rooms.values() if 'peaceful' not in (r.flags or ()) and r.vnum > 3001)

    def hero(name):
        h = Player.create_new(name=name, password=None, race='human', char_class='warrior',
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = room
        room.characters.append(h)
        h.level = 40
        h.max_hp = h.hp = 900
        return h

    def foe(level=20, name=None):
        proto = next(p for p in world.mob_prototypes.values()
                     if not p.get('boss_config') and not p.get('shop_config') and (p.get('level') or 0) >= level)
        m = create_mob_from_prototype(dict(proto), world)
        m.room = room
        room.characters.append(m)
        m.max_hp = m.hp = 5000
        if name:
            m.name = name
        return m

    def fight(a, b):
        a.fighting, b.fighting = b, a
        a.position = b.position = 'fighting'

    events = []
    real_emit = ev.emit
    ev.emit = lambda room, k, src=None, dst=None, **f: events.append((k, src, dst, f)) or real_emit(room, k, src, dst, **f)

    # ---- on hit: a legendary weapon's proc, its school, its event; a chain finds only foes
    h = hero('Proccer')
    h.equipment['wield'] = create_legendary(99002, world)          # echo shatter: chains
    a, b = foe(), foe()
    bystander = foe()
    fight(h, a)
    b.fighting = h
    with Always():
        before = (a.hp, b.hp, bystander.hp)
        await procs.on_hit(h, a, h.equipment['wield'])
    check(a.hp < before[0], f'an on-hit proc wounds the target ({before[0] - a.hp})')
    check(b.hp < before[1], 'a chain leaps to a second foe in the fight')
    check(bystander.hp == before[2], 'a creature not in the fight is never struck')
    check(any(k == 'proc' and f.get('name') == 'Echo Shatter' and f.get('school') == 'sound' for k, s, d, f in events),
          'the 3D client hears of it (a proc event with its name and school)')
    cd_hp = a.hp
    with Always():
        await procs.on_hit(h, a, h.equipment['wield'])
    check(a.hp == cd_hp, 'a proc waits out its cooldown before it fires again')

    # every weapon blow can proc: the main swing, an extra swing, the off-hand
    fired = []
    real_on_hit = procs.on_hit

    async def counting(att, dfn, weapon=None):
        fired.append(weapon)
    procs.on_hit = counting
    try:
        h.hitroll = 500
        h.equipment['dual_wield'] = create_legendary(99017, world)
        h.skills['dual_wield'] = 100
        await CombatHandler.bonus_attack(h, a)
        await CombatHandler.offhand_attack(h, a)
        h.fighting = a
        await CombatHandler.one_round(h, a)
    finally:
        procs.on_hit = real_on_hit
    check(h.equipment['wield'] in fired and h.equipment['dual_wield'] in fired and len(fired) >= 3,
          f'the main swing, an extra swing and the off-hand each roll procs ({len(fired)} blows)')
    del h.equipment['dual_wield']

    # a weapon's own proc fires only on its own blows
    with Always():
        h.__dict__['_proc_cd'] = {}
        hp0 = a.hp
        await procs.on_hit(h, a, weapon=None)
    check(a.hp == hp0, "a weapon's proc doesn't fire on another weapon's blow")

    # a drain heals the wearer
    h.equipment['wield'] = create_legendary(99004, world)          # hunger drain
    h.hp = 100
    with Always():
        h.__dict__['_proc_cd'] = {}
        await procs.on_hit(h, a, h.equipment['wield'])
    check(h.hp > 100, f'a draining proc heals the wearer ({h.hp - 100})')

    # ---- zone items: their spell-named affects and properties are procs now
    ring = create_object(22081, world)
    names = [p['effect'] for p in procs.item_procs(ring)]
    check('vampiric_touch' in names, f'a zone item with vampiric touch drains on hit ({names})')
    bane = next((v for v, p in world.obj_prototypes.items() if 'undead_bane' in (p.get('special_properties') or [])), None)
    if bane:
        it = create_object(bane, world)
        check(any(p['effect'] == 'undead_bane' for p in procs.item_procs(it)), 'an undead-bane item has its proc')
        h.equipment['wield'] = it if it.item_type == 'weapon' else h.equipment['wield']
        h.equipment['hold'] = it
        living = foe(name='a farmer')
        living.race = 'human'
        h.__dict__['_proc_cd'] = {}
        hp0 = living.hp
        with Always():
            await procs.on_hit(h, living, h.equipment.get('wield'))
        check(living.hp == hp0, 'undead bane does nothing to the living')
        h.equipment.pop('hold', None)

    # a proc's level-grown damage
    low, high = {'type': 'on_hit', 'effect': 'flaming'}, {'type': 'on_hit', 'effect': 'flaming'}

    class It:
        pass
    i1, i2 = It(), It()
    i1.vnum = i2.vnum = None
    i1.min_level, i2.min_level = 5, 50
    check(procs.proc_damage(i2, high) > procs.proc_damage(i1, low), 'proc damage grows with the item level')

    # creatures' gear doesn't proc
    a.equipment = {'wield': create_legendary(99002, world)}
    h.hp = h.max_hp
    with Always():
        await procs.on_hit(a, h, a.equipment['wield'])
    check(h.hp == h.max_hp, "a creature's gear doesn't proc")

    # ---- on defend: a blow turned back, the cocoon, dread
    d = hero('Defender')
    d.equipment['shield'] = create_legendary(99014, world)        # damage reflect
    m = foe()
    fight(d, m)
    with Always():
        hp0 = m.hp
        await d.take_damage(100, m, 'physical')
    check(m.hp < hp0, f'a reflecting shield turns part of the blow back ({hp0 - m.hp})')
    d.equipment['neck1'] = create_legendary(99011, world)         # cocoon
    d.hp = 50
    await d.take_damage(500, m, 'magic')
    check(d.hp > 0, f'the cocoon holds them to life once ({d.hp})')
    await d.take_damage(5000, m, 'magic')
    held = sum('cocoon holds you' in x for x in d.connection.sent)
    check(held == 1, f'but only once a day ({held})')

    # ---- on equip: standing bonuses
    e = hero('Equipper')
    cha0 = e.cha
    ring = create_legendary(99010, world)                          # +3 all stats
    ring.affects = []
    e.equipment['finger1'] = ring
    check(e.cha == cha0 + 3, f'an all-stats legendary raises every attribute ({cha0} -> {e.cha})')
    e.equipment['finger1'] = create_legendary(99010, world)
    check(e.cha == cha0 + 3, 'and counts each once when it lists them too')
    dmg0 = CombatHandler.scale_player_weapon_damage(e, 20)
    e.equipment['hands'] = create_legendary(99018, world)         # +5% damage
    check(CombatHandler.scale_player_weapon_damage(e, 20) > dmg0, 'a damage-% legendary hits harder')
    e.equipment['body'] = create_legendary(99007, world)          # fire ward
    check(e.resistance('fire') >= 30, f'the rust carapace wards fire ({e.resistance("fire")}%)')
    e.equipment['feet'] = create_legendary(99008, world)
    check(e.get_equipment_bonus('travel_speed') > 0, 'the threshold walkers quicken travel')

    # ---- sets: armour class, earth, reachable tiers, set procs, the command
    s = hero('Setter')
    ac0 = s.get_armor_class()
    for v in (8001, 8002):
        it = create_object(v, world)
        s.equipment[it.wear_slot or 'body'] = it
    armour_alone = ac0 - sum(getattr(it, 'armor', 0) for it in s.equipment.values() if it)
    check(s.get_armor_class() < armour_alone, f"a set's armour class bonus lowers armour class ({ac0} -> {s.get_armor_class()})")
    m4 = hero('Miner')
    for v in sets.NAMED_SETS['miners_garb']['pieces']:
        it = create_object(v, world)
        slot = it.wear_slot or 'hold'
        m4.equipment[slot if slot not in m4.equipment else slot + '_x'] = it
    check(m4.resistance('earth') >= 15, f"the miner's garb wards earth ({m4.resistance('earth')}%)")
    bad = [(sid, need, cap) for sid, cap in sets.SET_CAPS.items() for need, *_ in sets.set_tiers(sid) if need > cap]
    check(not bad, f'every set tier can be reached by the pieces one hero can wear ({bad[:3]})')
    check(sets.SET_CAPS.get(50) and any(n <= sets.SET_CAPS[50] for n, *_ in sets.set_tiers(50)), 'a five-slot set reaches its top tier')
    n4 = hero('Necro')
    for v in sets.NAMED_SETS['necromancers_regalia']['pieces']:
        it = create_object(v, world)
        n4.equipment[(it.wear_slot or 'hold') + str(v)] = it
    check(any(p['effect'] == 'grave_drain' for _, p in procs.set_procs(n4)), 'four pieces of a named set give its proc')
    await CommandHandler.cmd_sets(n4, [])
    out = ' '.join(n4.connection.sent)
    check("Necromancer's Regalia" in out and 'Grave Drain' in out, '`sets` names the set and its proc')
    lines = procs.item_lines(create_object(14001, world), n4)
    check(any(l.startswith('Set: ') for l in lines) and any('4 pieces' in l for l in lines), 'identify and tooltips list the set and its tiers')

    # ---- legendaries drop from real bosses
    missing = [v for v, (boss, _, _) in LEGENDARY_BOSSES.items() if boss not in world.mob_prototypes]
    check(not missing and len(LEGENDARY_BOSSES) == len(LEGENDARY_ITEMS), f'every legendary drops from a real boss ({missing})')
    from legendary import get_legendary_drop_for_boss
    boss = create_mob_from_prototype(dict(world.mob_prototypes[LEGENDARY_BOSSES[99003][0]]), world)
    boss.is_boss = True
    with Always():
        check(get_legendary_drop_for_boss(boss) == 99003, 'its boss drops it (at its chance)')
    check(create_legendary(99003, world).drop_source.startswith('Kaleidos'), 'and the item says who drops it')

    ev.emit = real_emit
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
