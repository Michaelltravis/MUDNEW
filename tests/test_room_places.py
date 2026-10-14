#!/usr/bin/env python3
"""Rooms an old import typed 'city' that are no town (Phase 2 of docs/world/room_visuals.md):

- a building typed as its town's street is drawn as a room (quarters, a classroom, a hut), a den
  hacked out of the rock as a cave;
- a road of bones is the necropolis, a ruined city ruins, a garden a garden, a village of huts a
  village, a camp round a fire pit a camp, the Gods' Table a marble terrace;
- a real town stays a town: Park Road is a street past a park, River Avenue an avenue, Mishrak's
  wall roads its streets;
- the audit finds few town-look rooms with no town left (the rest are streets that never say so);
- their ambient lines are their own (a classroom isn't a street, a village is under the sky);
- the text reader: "beds of roses" are not beds, "petals carpet the paths" no rug, "rain strikes
  the stone" no standing stone.

    python3 tests/test_room_places.py
"""
import asyncio
import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, os.path.join(HERE, '..', 'tools', 'audit'))

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


async def main():
    logging.disable(logging.WARNING)
    import room_features as rf
    keys = lambda name, desc: {f['k'] for f in rf.features(name, desc)}
    check('bed' not in keys('The Flower Garden', 'Beds of roses, lilies and anemones spill across this corner.'), '"beds of roses" are not beds')
    check('bed' in keys('The Barracks', 'Rows of beds line the walls.'), 'a barracks still has its beds')
    check('rug' not in keys('The Flower Garden', 'Petals carpet the paths.'), '"petals carpet the paths" lays no rug')
    check('standing_stone' not in keys('The Gods\' Table', 'A few fat drops of rain strike the stone.'), '"rain strikes the stone" raises no standing stone')

    from config import Config
    from world import World
    import atmosphere
    import room_text
    world = World(Config())
    await world.load()
    R = world.rooms
    want = {
        13917: 'inside',      # Priests Quarters (Orcus Temple)
        2805: 'inside',       # a classroom of the Garathorm School House
        15102: 'inside',      # Hut Of Kigrint (Morvoct)
        15158: 'cave',        # The Cyclop's Den, hacked out of the living rock
        16216: 'necropolis',  # On A Path Of Bones (World Of Chaos)
        1619: 'necropolis',   # The Walkway of Bones (City of Ancients)
        5201: 'ruins',        # Main Street of ruined Thalos
        201517: 'garden',     # The Flower Garden (Eden)
        9905: 'garden',       # The Twisting Hedges (Ghenna)
        15136: 'village',     # The Palm Covered Path (Morvoct)
        2242: 'village',      # Among the Crude Huts (the ogres)
        2246: 'camp',         # The Firepit Before the Lodge
        1031: 'terrace',      # Crossing The Gods' Table (Olympus)
        3118: 'city',         # Park Road: a street past the park
        12026: 'city',        # River Avenue
        8032: 'city',         # Mishrak's Northern Wall Road
    }
    for v, look in want.items():
        r = R.get(v)
        check(r is not None and r.look == look, f'{v} {getattr(r, "name", "?")}: {look} ({getattr(r, "look", None)})')

    left = sum(1 for r in R.values() if (room_text.judge(r) or '').startswith('town'))
    check(left <= 40, f'few town-look rooms with no town left ({left}; were 211)')

    lines = {atmosphere.AtmosphereManager.get_atmosphere(R[2805]) for _ in range(60)} - {None}
    check(not any(w in l.lower() for l in lines for w in ('street', 'vendor', 'cobble')), f'a classroom has no street lines ({sorted(lines)[:2]})')

    print(f"\n{'ALL OK' if not FAILED else f'{len(FAILED)} FAILED'}")
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    asyncio.run(main())
