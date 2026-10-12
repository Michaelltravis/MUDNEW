"""Wearing gear, offline: rings on both fingers, a slot named, a swap, "2.ring", hold, remove.

    python3 tests/test_wear.py

The owner: "enable drag and drop gear swapping from inventory to wear positions. Ensure rings can
be worn on both fingers too." Many rings say "finger1" in their data; they go on either finger.
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
    from player import Player
    from objects import Object
    from commands import CommandHandler as C
    from equip import slots_for
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()

    def thing(name, short, itype='worn', slot=None, **kw):
        o = Object(0, world)
        o.name, o.short_desc, o.item_type = name, short, itype
        if slot:
            o.wear_slot = slot
        for k, v in kw.items():
            setattr(o, k, v)
        return o

    def hero(name):
        h = Player.create_new(name=name, password=None, race='human', char_class='warrior',
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = world.rooms[3001]
        world.rooms[3001].characters.append(h)
        for s in list(h.equipment):
            h.equipment[s] = None
        h.inventory.clear()
        return h

    said = lambda h: ' '.join(h.connection.sent[-3:])

    # ---- two rings that both say finger1 go on both fingers
    h = hero('Ringer')
    gold, ruby, jade = (thing('ring gold', 'a gold ring', slot='finger1'), thing('ring ruby', 'a ruby ring', slot='finger1'),
                        thing('ring jade', 'a jade ring', slot='finger1'))
    h.inventory += [gold, ruby, jade]
    check(slots_for(h, gold) == ['finger1', 'finger2'], 'a ring that says finger1 fits either finger')
    await C.execute(h, 'wear', ['ring'])
    await C.execute(h, 'wear', ['ring'])
    check(h.equipment.get('finger1') is gold and h.equipment.get('finger2') is ruby, f'two rings: one on each finger ({said(h)})')
    await C.execute(h, 'wear', ['ring'])
    check(jade in h.inventory and 'both finger slots' in said(h) and 'finger2' in said(h),
          f'a third: both are taken, and it says how to swap ({said(h)})')
    # ---- a slot named: a swap
    await C.execute(h, 'wear', ['jade', 'finger1'])
    check(h.equipment['finger1'] is jade and gold in h.inventory and 'You remove a gold ring' in ' '.join(h.connection.sent[-4:]),
          'wear jade finger1: the gold ring comes off, the jade goes on')
    await C.execute(h, 'wear', ['gold', 'neck1'])
    check(gold in h.inventory and "doesn't go there" in said(h), f'a ring does not go on the neck ({said(h)})')
    # ---- 2.ring, the second of two alike
    h2 = hero('Twins')
    a, b = thing('ring silver', 'a silver ring', slot='finger1'), thing('ring silver', 'a silver ring', slot='finger1')
    h2.inventory += [a, b]
    await C.execute(h2, 'wear', ['2.ring', 'finger2'])
    check(h2.equipment.get('finger2') is b and a in h2.inventory, '"wear 2.ring finger2" puts the second ring on the right finger')
    await C.execute(h2, 'wear', ['ring'])
    check(h2.equipment.get('finger1') is a, 'and the first on the left')
    # ---- remove by slot or by 2.name
    await C.execute(h2, 'remove', ['finger2'])
    check(h2.equipment.get('finger2') is None and b in h2.inventory, 'remove finger2 takes off what is there')
    await C.execute(h2, 'wear', ['ring', 'right'])
    await C.execute(h2, 'remove', ['2.ring'])
    check(h2.equipment.get('finger2') is None and h2.equipment.get('finger1') is a, 'remove 2.ring takes off the second ring worn')
    # ---- necks and wrists pair the same way
    h3 = hero('Necks')
    h3.inventory += [thing('amulet bone', 'a bone amulet', slot='neck1'), thing('amulet jade', 'a jade amulet', slot='neck1'),
                     thing('bracer iron', 'an iron bracer', slot='wrist1'), thing('bracer bronze', 'a bronze bracer', slot='wrist')]
    await C.execute(h3, 'wear', ['all'])
    check(all(h3.equipment.get(s) for s in ('neck1', 'neck2', 'wrist1', 'wrist2')), 'wear all: both necks and both wrists')
    # ---- weapons: a swap, the off hand
    h4 = hero('Blades')
    sword, axe = thing('sword long', 'a long sword', 'weapon', weapon_type='slash'), thing('axe battle', 'a battle axe', 'weapon', weapon_type='slash')
    dagger = thing('dagger', 'a dagger', 'weapon', weapon_type='pierce')
    h4.inventory += [sword, axe, dagger]
    await C.execute(h4, 'wield', ['sword'])
    await C.execute(h4, 'wield', ['axe'])
    check(h4.equipment['wield'] is sword and 'already wielding' in said(h4), 'a second weapon unasked: refused, with the way to swap')
    await C.execute(h4, 'wield', ['axe', 'wield'])
    check(h4.equipment['wield'] is axe and sword in h4.inventory, 'wield axe wield: swapped')
    await C.execute(h4, 'wield', ['dagger', 'offhand'])
    check(not h4.equipment.get('dual_wield'), 'the off hand needs dual wield')
    h4.skills['dual_wield'] = 50
    await C.execute(h4, 'wield', ['sword', 'offhand'])
    check(not h4.equipment.get('dual_wield'), 'and only a light weapon')
    await C.execute(h4, 'wield', ['dagger', 'offhand'])
    check(h4.equipment.get('dual_wield') is dagger, 'a dagger in the off hand')
    # ---- hold
    h5 = hero('Holder')
    torch = thing('torch', 'a torch', 'light')
    wand = thing('wand oak', 'an oak wand', 'wand')
    h5.inventory += [torch, wand]
    await C.execute(h5, 'hold', ['torch'])
    await C.execute(h5, 'hold', ['wand'])
    check(h5.equipment.get('light') is torch and h5.equipment.get('hold') is wand, 'hold: a torch as the light, a wand in hand')
    # ---- "a ring of light" is an item's name, not "ring of" in the light slot
    h6 = hero('Lighter')
    rol = thing('ring light', 'a ring of light', slot='finger')
    h6.inventory.append(rol)
    await C.execute(h6, 'wear', ['ring', 'light'])
    check(h6.equipment.get('finger1') is rol, 'wear ring light: the ring of light goes on a finger')
    # a glowing ring (item_type light, wear_slot finger: the platinum ring) goes on a finger
    h7 = hero('Glow')
    glow = thing('ring', 'a platinum ring', 'light', slot='finger')
    h7.inventory.append(glow)
    await C.execute(h7, 'wear', ['ring', 'finger2'])
    check(h7.equipment.get('finger2') is glow, 'a glowing ring goes on a finger, not in the light slot')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
