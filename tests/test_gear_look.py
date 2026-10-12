"""How gear looks to the 3D client (src/gear_look.py), offline: item levels, tiers, how items are
read (kind, hands, armour weight, material, colour), each class's starting look, the look's
signature, and the relay that re-dresses a character for everyone around when their gear
changes. Live, in two browsers: tests/web/probe_play3d.js gear.

    python3 tests/test_gear_look.py
"""
import asyncio
import logging
import os
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


class FakeWebMap:
    def __init__(self):
        self.sent = []

    async def relay_look(self, player, look):
        self.sent.append((player.name, look['sig']))


async def offline():
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    from objects import Object, create_preset_object
    from player import Player
    import gear_look as gl
    world = World(Config())
    await world.load()
    gear = [v for v, p in world.obj_prototypes.items() if isinstance(p, dict)
            and (p.get('item_type') or p.get('type')) in ('weapon', 'armor', 'worn')]
    known = sum(1 for v in gear if v in gl.ITEM_LEVELS)
    check(known >= 0.9 * len(gear), f'item levels for nearly all gear ({known} of {len(gear)})')

    def piece_of(name, slot='wield', **kw):
        o = Object(0, world)
        o.name = o.short_desc = name
        o.item_type = kw.pop('item_type', 'weapon' if slot in ('wield', 'dual_wield') else 'armor')
        o.wear_slot = slot
        for k, v in kw.items():
            setattr(o, k, v)
        return o

    # how items are read
    p = gl.weapon_piece(piece_of('a steel bardiche'))
    check(p['k'] == 'polearm' and p['h'] == 2, f'a bardiche is a two-handed polearm ({p})')
    p = gl.weapon_piece(piece_of('a short bow'))
    check(p['k'] == 'bow' and p['h'] == 2 and p['m'] == 'wood', f'a short bow: two hands, wood ({p})')
    p = gl.weapon_piece(piece_of('the rainbow blade'))
    check(p['k'] == 'sword', f'"rainbow" is not a bow ({p})')
    p = gl.weapon_piece(piece_of('a royal greatblade'))
    check(p['k'] == 'sword' and p['h'] == 2 and p['m'] == 'gold', f'a royal greatblade: a gold two-handed sword ({p})')
    p = gl.weapon_piece(piece_of('tombknife'))
    check(p['k'] == 'dagger', f'a made-up word ending in "knife" is a dagger ({p})')
    p = gl.held_piece(piece_of('a well-crafted lute', 'hold', item_type='other'))
    check(p and p['k'] == 'instrument', f'a lute is an instrument ({p})')
    p = gl.held_piece(piece_of('lockpicks', 'hold', item_type='other'))
    check(p is None, 'lockpicks are not drawn')
    # which instrument, which crown: the client builds each its own shape
    p = gl.held_piece(piece_of('a golden lyre', 'hold', item_type='other'))
    check(p and p['k'] == 'instrument' and p.get('v') == 'lyre', f'a held lyre is drawn as a lyre ({p})')
    p = gl.weapon_piece(piece_of('a war drum'))
    check(p['k'] == 'instrument' and p.get('v') == 'drum', f'a war drum is a drum ({p})')
    p = gl.held_piece(piece_of('a well-crafted lute', 'hold', item_type='other'))
    check(p.get('v') == 'lute', f'a lute stays a lute ({p})')
    p = gl.head_piece(piece_of('a silver circlet', 'head'))
    check(p['k'] == 'crown' and p.get('v') == 'circlet' and p.get('m') == 'silver', f'a silver circlet ({p})')
    p = gl.head_piece(piece_of('the crown of thorns', 'head'))
    check(p['k'] == 'crown' and p.get('v') == 'crown', f'a crown ({p})')
    check(gl.armour_piece(piece_of('a suit of chainmail', 'body'))['w'] == 2, 'chainmail is mail (2)')
    check(gl.armour_piece(piece_of('simple cloth robes', 'body'))['w'] == 0, 'robes are cloth (0)')
    p = gl.armour_piece(piece_of('fitted black leather armor', 'body'))
    check(p['w'] == 1 and p['m'] == 'leather_black', f'black leather armour: leather, black ({p})')
    check(gl.armour_piece(piece_of('leather gauntlets', 'hands'))['w'] == 1, 'leather gauntlets are leather, not plate')
    check(gl.armour_piece(piece_of('some silvery leg plates', 'legs'))['w'] == 3, 'leg plates are plate')
    p = gl.head_piece(piece_of('a dark hooded cowl', 'head'))
    check(p['k'] == 'hood', f'a cowl is a hood ({p})')
    p = gl.cloak_piece(piece_of('a thick bear pelt cloak', 'about'))
    check(p['v'] == 'barbarian', f'a fur cloak hangs like the barbarian\'s ({p})')

    # tiers: a level from where the item is found, one more for magic, a legendary is 5
    low = piece_of('a dagger')
    low.vnum = 11                       # starting gear
    check(gl.item_tier(low) == 0, 'starting gear is tier 0')
    deep = piece_of('a sword')
    deep.vnum = -1
    deep.min_level = 45
    check(gl.item_tier(deep) == 4, 'a level-45 sword is tier 4')
    mid = piece_of('a sword')
    mid.vnum = -2
    mid.min_level = 20
    mid.flags = {'magic'}
    check(gl.item_tier(mid) == 3, 'a level-20 magic sword is tier 3 (2, and one for magic)')
    leg = piece_of('Cataract')
    leg.rarity = 'legendary'
    check(gl.item_tier(leg) == 5, 'a legendary is tier 5')
    fire = piece_of('a sword')
    fire.flags = {'flaming'}
    check(gl.weapon_piece(fire).get('e') == 'fire', 'a flaming sword burns')
    dark = gl.armour_piece(piece_of('shadowy dark robes', 'body'))
    check('e' not in dark and dark.get('c') == 'black', f'dark robes are black, not a shadow weapon ({dark})')

    # what a shop sells is ordinary, however strong the shopkeeper who also carries it
    sword = Object.from_prototype(world.obj_prototypes[3022], world)
    check(gl.item_tier(sword) == 1, f"Midgaard's shop sword is tier 1, not its level-33 sellers' ({gl.item_level(sword)})")

    # creatures: the gear their zone gave them shows, the gear every creature is handed does not;
    # their level is no standing (no renown)
    import map_system
    mobs = [ch for r in world.rooms.values() for ch in getattr(r, 'characters', []) if not hasattr(ch, 'account_name')]
    guard = next((m for m in mobs if getattr(m, 'vnum', None) == 3060), None)
    lk = map_system._npc_look(guard) if guard else None
    check(lk and lk['main']['k'] == 'sword' and lk['rn'] == 0, f'a cityguard wears its sword ({lk})')
    high = next((m for m in mobs if getattr(m, 'own_gear', False) and (m.level or 0) >= 35 and map_system._npc_look(m)), None)
    check(high is not None and map_system._npc_look(high)['rn'] == 0, 'a level-35 creature has no renown')
    handed = [m for m in mobs if not getattr(m, 'own_gear', False) and getattr(m, 'equipment', None)]
    check(handed and all(map_system._npc_look(m) is None for m in handed), f'auto-equipped creatures send no look ({len(handed)})')

    # every class's starting look
    looks = {}
    for cls in ('warrior', 'mage', 'cleric', 'thief', 'ranger', 'paladin', 'necromancer', 'bard', 'assassin'):
        hero = Player.create_new(name=f'Gl{cls[:4].title()}', password=None, race='human', char_class=cls,
                                 stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        hero.connection = Conn()
        looks[cls] = gl.look_of(hero)
    lk = looks['warrior']
    check(lk['main']['k'] == 'sword' and lk['off']['k'] == 'shield' and lk['body']['w'] == 2 and lk['head']['k'] == 'helm',
          f"a warrior starts with a sword, a shield, mail and a helm ({lk})")
    check(looks['ranger']['main']['k'] == 'bow' and looks['ranger'].get('quiver'), 'a ranger starts with a bow and a quiver')
    check(looks['cleric']['main']['k'] == 'mace', 'a cleric starts with a mace')
    check(looks['bard']['off']['k'] == 'instrument', 'a bard holds a lute')
    check(looks['mage']['off']['k'] == 'book' and looks['mage']['body']['w'] == 0, 'a mage holds a book, in robes')
    check(looks['assassin']['back']['k'] == 'cloak' and looks['assassin']['back'].get('c') == 'black', 'an assassin wears a dark cloak')
    check(all(p.get('t', 0) == 0 for lk in looks.values() for p in lk.values() if isinstance(p, dict)),
          'all starting gear is tier 0')
    check(all(len(lk['sig']) == 8 for lk in looks.values()) and len({lk['sig'] for lk in looks.values()}) == 9,
          'each class looks different (a signature each)')

    # the signature, and the relay: once per change, never for nothing
    hero = Player.create_new(name='Glrelay', password=None, race='dwarf', char_class='warrior',
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    hero.connection = Conn()
    hero.room = world.rooms.get(3001)
    wm = FakeWebMap()
    world.web_map = wm
    first = gl.look_of(hero)
    check(first['race'] == 'dwarf' and gl.look_of(hero) is first, "a look is cached until it changes (and knows the race)")
    await gl.after_command(hero)
    check(wm.sent == [], 'nothing changed: nothing relayed')
    hero.equipment['wield'].flags.add('flaming')
    await gl.after_command(hero)
    check(len(wm.sent) == 1 and wm.sent[0][1] != first['sig'], f'the sword caught fire: one relay ({wm.sent})')
    await gl.after_command(hero)
    check(len(wm.sent) == 1, 'and no second one')
    hero.equipment['shield'] = None
    await gl.after_command(hero)
    check(len(wm.sent) == 2 and 'off' not in gl.look_of(hero), 'the shield taken off: relayed, and gone from the look')
    hero.level = 20
    await gl.touch(hero)
    check(len(wm.sent) == 3 and gl.look_of(hero)['rn'] == 2, 'level 20: a new band of renown, relayed')
    world.web_map = None


async def main():
    await offline()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
