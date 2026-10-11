#!/usr/bin/env python3
"""How the 3D client will draw every piece of gear in the world (src/gear_look.py): its kind,
hands, armour weight, material, colour, element and tier, for review.

    python3 tools/qc_gear.py              # summary counts, and the pieces it had to guess
    python3 tools/qc_gear.py --all        # every piece, one line each
    python3 tools/qc_gear.py --grep bow   # pieces whose name matches
"""
import asyncio
import collections
import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))


async def main():
    logging.disable(logging.CRITICAL)
    from config import Config
    from world import World
    from objects import Object
    import gear_look as gl
    world = World(Config())
    await world.load()
    levels = gl.build_item_levels(world)
    show_all = '--all' in sys.argv
    pat = re.compile(sys.argv[sys.argv.index('--grep') + 1], re.I) if '--grep' in sys.argv else None
    counts = collections.Counter()
    tiers = collections.Counter()
    guessed = []
    lines = []
    gear = 0
    for vnum, proto in sorted(world.obj_prototypes.items()):
        if not isinstance(proto, dict):
            continue
        try:
            obj = Object.from_prototype(proto, world)
        except Exception:
            continue
        itype = obj.item_type
        slot = str(obj.wear_slot or '')
        if itype not in ('weapon', 'armor', 'worn') and slot not in ('wield', 'hold', 'shield', 'head', 'body', 'about'):
            continue
        gear += 1
        if itype == 'weapon' or slot == 'wield':
            p, group = gl.weapon_piece(obj), 'weapon'
        elif slot == 'shield':
            p, group = gl.shield_piece(obj), 'shield'
        elif slot == 'hold':
            p, group = gl.held_piece(obj), 'held'
        elif slot == 'head':
            p, group = gl.head_piece(obj), 'head'
        elif slot == 'about':
            p, group = gl.cloak_piece(obj), 'cloak'
        elif slot in ('body', 'arms', 'hands', 'legs', 'feet', ''):
            p, group = gl.armour_piece(obj), f'armour:{slot or "?"}'
        else:
            continue                  # rings, amulets, belts: not drawn
        tiers[gl.item_tier(obj)] += 1
        key = f"{group} {p.get('k', 'w' + str(p.get('w'))) if p else 'nothing'}"
        counts[key] += 1
        text = gl._text(obj)
        if p and group == 'weapon' and not gl._first(gl.WEAPONS, text):
            guessed.append(f"  weapon by weapon_type {obj.weapon_type!r}: {vnum} {obj.name!r} -> {p['k']}")
        if p and group.startswith('armour') and gl._first(gl.WEIGHTS, text) is None:
            guessed.append(f"  armour weight by heft ({obj.weight}): {vnum} {obj.name!r} / {obj.short_desc!r} -> w{p['w']}")
        line = f"{vnum:>6} {group:14} L{levels.get(vnum, '?'):>3} {obj.name[:34]:34} {p}"
        if show_all or (pat and pat.search(obj.name + ' ' + (obj.short_desc or ''))):
            lines.append(line)
    print(f"{gear} pieces of gear; item levels known for {sum(1 for v in world.obj_prototypes if v in levels)} prototypes")
    for k, n in sorted(counts.items()):
        print(f"  {k:28} {n}")
    print('tiers:', dict(sorted(tiers.items())))
    if lines:
        print('\n'.join(lines))
    elif guessed:
        print(f"\n{len(guessed)} guessed:")
        print('\n'.join(guessed[:80]))


if __name__ == '__main__':
    asyncio.run(main())
