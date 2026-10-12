"""Shops buy and sell at sane prices, offline.

    python3 tests/test_shops.py

The old shop import read many shops a field off (product vnums as markup and markdown, the buy
profit as a buy type): a raft listed at 1,224,400 gold and those shops would buy nothing.
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
    from shops import ShopManager, repair_config
    from objects import create_object
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    shops = list(ShopManager.shops.values())
    check(len(shops) > 30, f'the world has its shops ({len(shops)})')

    # ---- the misaligned import, undone
    fixed = repair_config({'sells': [3060], 'buys': ['1.2'], 'markup': 3061.0, 'markdown': -1.0})
    check(fixed['sells'] == [3060, 3061] and fixed['markup'] == 1.2 and fixed['markdown'] == 0.4 and fixed['buys'] == [],
          f'a shop read a field off gets its products, profit and a sane markdown back ({fixed})')
    fixed = repair_config({'sells': [3040], 'buys': ['3043'], 'markup': 3041.0, 'markdown': 3042.0})
    check(fixed['sells'] == [3040, 3041, 3042, 3043] and fixed['markup'] == 1.5, f'and every product ({fixed["sells"]})')
    good = {'sells': [3020], 'buys': ['weapon'], 'markup': 1.15, 'markdown': 0.2}
    check(repair_config(good) == good, 'a sound shop is left as it is')

    bad = [(s.mob.name, s.markup, s.markdown) for s in shops if not (1.0 <= s.markup <= 3.0 and 0 < s.markdown <= 1.0)]
    check(not bad, f'every shop prices sanely ({bad[:4]})')
    nobuy = [(s.mob.name, s.buy_types) for s in shops if not s.buy_types or not all(str(b).isalpha() for b in s.buy_types)]
    check(not nobuy, f'every shop buys some kinds of thing ({nobuy[:4]})')

    # ---- a raft is affordable, where boats are sold
    boats = [(s, it) for s in shops for it in s.get_sellable_items() if getattr(it, 'item_type', '') == 'boat']
    check(boats and all(s.get_sell_price(it) <= 1500 for s, it in boats if 'raft' in it.name),
          f'a raft costs about a thousand gold, not a million ({[(s.mob.name, s.get_sell_price(it)) for s, it in boats][:4]})')

    # ---- selling: what a shop deals in, even when its till is empty; "2.<word>" sells the second
    def hero(at):
        h = Player.create_new(name='Seller', password=None, race='human', char_class='warrior',
                              stats={k: 13 for k in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = at
        at.characters.append(h)
        return h
    smith = next(s for s in shops if 'weapon' in s.buy_types and s.mob.room)
    h = hero(smith.mob.room)
    proto = next(v for v, p in world.obj_prototypes.items() if str(p.get('item_type')) == 'weapon' and (p.get('value') or 0) > 50)
    a, b = create_object(proto, world), create_object(proto, world)
    h.inventory += [a, b]
    smith.gold = 0
    gold0 = h.gold
    ok = await smith.buy_from_player(h, 'zz_nothing')
    check(not ok, 'selling what you lack fails')
    word = a.name.split()[0]
    ok = await smith.buy_from_player(h, f'2.{word}')
    check(ok and b not in h.inventory and a in h.inventory and h.gold > gold0,
          f"an empty till doesn't stop a sale, and 2.{word} sells the second ({h.gold - gold0} gold)")
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
