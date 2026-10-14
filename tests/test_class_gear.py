#!/usr/bin/env python3
"""Each class wears its own kind of gear (src/class_gear.py), D&D style:

- the rules: a mage wears cloth and carries a staff, a wand or a dagger; a thief wears leather and
  no greatsword; a warrior anything but a wand; leather boots and gloves are anyone's;
- wear, wield, hold and 'wear all' refuse the rest with the reason; nothing moves;
- logging in, an older character puts away what its class can't use;
- every class's starting kit is its own; gearup dresses each class in its own kind (a mage in robes,
  a hat and a staff; no two-handed weapon with a shield) and a set made for it where there is one;
- the new class sets and the ranger's longbow exist, and bosses drop them;
- the /play payload carries the rules and each item's key; the gear gallery's ENDGAME is current.

    python3 tests/test_class_gear.py
"""
import asyncio
import json
import logging
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


class Conn:
    def __init__(self):
        self.lines = []

    async def send(self, message='', newline=True):
        self.lines.append(str(message))

    async def send_prompt(self):
        pass

    def said(self, text):
        return any(text.lower() in l.lower() for l in self.lines)


async def main():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from player import Player
    from objects import create_object, create_preset_object
    from commands import CommandHandler
    import class_gear
    import gear_look
    from sets import NAMED_SETS
    from legendary import LEGENDARY_ITEMS, LEGENDARY_BOSSES
    world = World(Config())
    await world.load()

    def make(cls):
        p = Player.create_new(name='Cg' + cls, password=None, race='human', char_class=cls,
                              stats={s: 15 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        p.connection = Conn()
        p.save = lambda: asyncio.sleep(0)
        p.room = world.rooms[world.config.STARTING_ROOM] if hasattr(world, 'config') else next(iter(world.rooms.values()))
        return p

    async def do(p, line):
        p.connection.lines.clear()
        words = line.split()
        await p.execute_command(words[0], words[1:])
        return p.connection

    def obj(**kw):
        o = create_preset_object(10)          # a short sword (the starting kit's), reshaped
        for k, v in kw.items():
            setattr(o, k, v)
        return o

    # ---- the rules
    mage, thief, warrior = make('mage'), make('thief'), make('warrior')
    plate = obj(name='plate armor', short_desc='a suit of plate armor', item_type='armor', wear_slot='body', weight=30)
    robe = obj(name='robe silk', short_desc='a silk robe', item_type='armor', wear_slot='body', weight=2)
    boots = obj(name='boots leather', short_desc='a pair of leather boots', item_type='armor', wear_slot='feet', weight=2)
    sabatons = obj(name='sabatons steel', short_desc='a pair of steel sabatons', item_type='armor', wear_slot='feet', weight=6)
    helm = obj(name='helm iron', short_desc='an iron helm', item_type='armor', wear_slot='head', weight=4)
    hat = obj(name='hat wizard pointed', short_desc="a pointed wizard's hat", item_type='armor', wear_slot='head', weight=1)
    sword = create_preset_object(10)
    staff = create_preset_object(34)
    claymore = obj(name='claymore', short_desc='a claymore', weapon_type='slash')
    wand = obj(name='wand', short_desc='a wand of sparks', weapon_type='pound')
    check(not class_gear.allows(mage, plate) and class_gear.allows(mage, robe), 'a mage: robes, not plate')
    check(class_gear.allows(mage, boots) and not class_gear.allows(mage, sabatons), "leather boots are anyone's; steel sabatons are armour")
    check(class_gear.allows(mage, hat) and not class_gear.allows(mage, helm), "a mage: a wizard's hat, not an iron helm")
    check(class_gear.allows(mage, staff, 'wield') and not class_gear.allows(mage, sword, 'wield'), 'a mage: a staff, not a sword')
    check(class_gear.allows(thief, sword, 'wield') and not class_gear.allows(thief, claymore, 'wield'), 'a thief: a short sword, not a claymore')
    check(class_gear.allows(warrior, claymore, 'wield') and class_gear.allows(warrior, plate)
          and not class_gear.allows(warrior, wand, 'wield'), 'a warrior: plate and a claymore, not a wand')
    check(class_gear.client_key(plate, 'body') == 'a:3' and class_gear.client_key(claymore) == 'w:sword:2', 'the payload keys')

    # ---- the commands refuse, with the reason, and nothing moves
    mage.inventory = [plate, sword, robe]
    mage.equipment = {}
    out = await do(mage, 'wear plate')
    check(mage.equipment.get('body') is None and plate in mage.inventory and out.said('cloth at most'), 'wear plate: refused, the reason given')
    out = await do(mage, 'wield sword')
    check(mage.equipment.get('wield') is None and out.said('not for you'), 'wield sword: refused')
    out = await do(mage, 'wear all')
    check(mage.equipment.get('body') is robe and plate in mage.inventory, "wear all: the robe goes on, the plate stays in the pack")

    # ---- logging in: an older character puts away what its class can't use
    old = make('mage')
    old.equipment = {'body': plate, 'wield': sword, 'head': hat}
    old.inventory = []
    shed = await class_gear.shed(old)
    check(set(shed) == {plate, sword} and old.equipment.get('head') is hat and old.connection.said('training'),
          'login: the plate and the sword go to the pack, the hat stays, and why')

    # ---- every class's starting kit, and gearup
    looks = {}
    for cls in class_gear.RULES:
        p = make(cls)
        bad = [i.short_desc for s, i in p.equipment.items() if i and not class_gear.allows(p, i, s)]
        check(not bad, f'{cls}: the starting kit is its own ({bad})')
        await CommandHandler.gear_up(p)
        bad = [(s, i.short_desc) for s, i in p.equipment.items() if i and not class_gear.allows(p, i, s)]
        check(not bad, f'{cls}: gearup gives only what it can use ({bad})')
        w = p.equipment.get('wield')
        k = gear_look.weapon_piece(w) if w else {}
        two = k.get('h') == 2 or k.get('k') in ('bow', 'staff', 'polearm', 'spear', 'scythe')
        check(not (two and p.equipment.get('shield')), f'{cls}: no two-handed weapon with a shield')
        looks[cls] = gear_look.look_of(p)
        sets = {getattr(i, 'set_id', None) for i in p.equipment.values() if i}
        want = {'mage': 'archmage_vestments', 'necromancer': 'lichlord_shroud', 'thief': 'nightblade_leathers',
                'assassin': 'nightblade_leathers', 'bard': 'nightblade_leathers'}.get(cls)
        if want:
            check(want in sets, f'{cls}: wears its own set ({want})')
    check(looks['mage']['main']['k'] == 'staff' and looks['mage']['body']['w'] == 0 and looks['mage']['head']['k'] == 'hat',
          'a mage at the top: a staff, robes and a hat')
    check(looks['necromancer']['main']['k'] in ('scythe', 'staff') and looks['necromancer']['head']['k'] == 'hood', 'a necromancer: a scythe or a staff, a cowl')
    check(looks['ranger']['main']['k'] == 'bow', 'a ranger: a bow (Skyrend)')
    check(looks['warrior']['body']['w'] >= 2, 'a warrior: mail or plate')

    # ---- the new gear exists and drops
    for key in ('archmage_vestments', 'lichlord_shroud', 'nightblade_leathers'):
        pieces = [int(v) for v in NAMED_SETS[key]['pieces']]
        missing = [v for v in pieces if v not in world.obj_prototypes]
        dropped = {int(e['vnum'] if isinstance(e, dict) else e) for p in world.mob_prototypes.values() for e in (p.get('boss_loot_table') or [])}
        check(not missing and set(pieces) <= dropped, f'{NAMED_SETS[key]["name"]}: every piece exists and a boss drops it')
    check(NAMED_SETS['necromancers_regalia']['pieces'][14001] == 'bone-stitched robes'
          and gear_look.armour_piece(create_object(14001, world))['w'] == 0, "the Necromancer's Regalia is robes now, not plate")
    check(99021 in LEGENDARY_ITEMS and LEGENDARY_BOSSES[99021][0] in world.mob_prototypes, "Skyrend drops from a real boss")
    check(gear_look.head_piece(create_object(29061, world)).get('v') == 'wizard',
          "the Archmage's hat is drawn as a wizard's hat")

    # ---- the /play payload
    import map_system
    info = map_system.item_info(plate)
    check(info.get('gk') == 'a:3', 'item_info carries the class key')
    check(map_system._gear_rules(mage) == {'armour': 0, 'shield': False, 'weapons': ['dagger', 'staff', 'thrown', 'wand']},
          'the rules go to the client')

    # ---- the gear gallery's ENDGAME is what gearup gives
    src = open(os.path.join(HERE, '..', 'src', 'web_isometric', 'world3d', 'gallery.js'), encoding='utf-8').read()
    m = re.search(r'export const ENDGAME = (\{.*?\});\n', src, re.S)
    endgame = json.loads(m.group(1)) if m else {}
    stale = [c for c, lk in looks.items() if c not in endgame or any(
        (endgame[c].get(k) or {}).get(f) != (lk.get(k) or {}).get(f) for k in ('main', 'head', 'body') for f in ('k', 'w', 's'))]
    check(not stale, f'gallery.js ENDGAME matches gearup ({stale})')

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
