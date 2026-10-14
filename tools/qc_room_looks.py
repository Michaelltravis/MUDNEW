"""Rooms drawn as something their own words say they are not (the owner: Arachnos, a webbed tree
lair, drew as plains with a town). Loads the world as the server does (room_looks.classify runs at
load) and lists rooms whose look disagrees with strong cues in their name and description.

    python3 tools/qc_room_looks.py [--zone N] [--all]
"""
import asyncio
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

CUES = {
    'web': r'\b(webs?|webbed|webby|webbing|cobwebs?|cocoon\w*|egg ?sacs?|spider ?silk)\b',
    'forest': r'\b(trees?|branch(?:es)?|boughs?|limbs?|canopy|foliage|trunks?|undergrowth|forest|woods|leaves)\b',
    'cave': r'\b(caves?|caverns?|tunnels?|stalactites?|rock walls?|underground)\b',
    'indoor': r'\b(walls?|ceiling|rooms?|chambers?|halls?|doors?|floor ?boards?|furniture|tables?|beds?)\b',
    'city': r'\b(streets?|shops?|buildings?|houses?|market|plaza|alley|cobbled|town|city)\b',
    'water': r'\b(water|river|lake|sea|ocean|swim\w*|waves?)\b',
}
CUE_RES = {k: re.compile(v, re.I) for k, v in CUES.items()}
# a look and the cues that contradict it when strong
WEB_OVER = {'inside', 'dungeon', 'cave', 'crypt', 'mine', 'sewer'}
CONFLICT = {
    'city': ('web', 'forest', 'cave'), 'field': ('web', 'forest', 'cave', 'indoor'),
    'hills': ('web', 'cave', 'indoor'), 'inside': ('web', 'forest'), 'forest': ('web', 'cave'),
}


# rooms read and judged right as they are drawn, though their words trip a cue (why)
ACCEPT = {
    2315: 'a walled vegetable garden: walls, open sky',
    8167: "grass behind the inn; the inn's doors and wall are beside it",
    9117: 'a hill pasture crossed by an old field wall',
    201503: "outside Eden's gate, in a wall",
    16200: 'outside a cabin on a hillside',
    8041: 'a town wall road with one tree in its paving',
    13026: "a road between walled gardens in a dwarven hold",
    13038: 'a cobbled yard before a watchtower, its walls rising to the roof of the mountain',
    4507: 'a garden path outside the greenhouse', 4510: 'a garden path round the greenhouse',
    4512: 'a garden path round the greenhouse', 4528: 'inside the glasshouse: a garden under glass',
    4529: 'inside the glasshouse: a garden under glass', 4533: 'an open pavilion in the garden',
    1407: "Elvandar's halls are rooms built in the trees", 1413: "Elvandar's halls are rooms built in the trees",
    1448: "Elvandar's halls are rooms built in the trees", 1456: "Elvandar's halls are rooms built in the trees",
    1458: "Elvandar's halls are rooms built in the trees", 11012: 'a guard room (its text is of the blighted wood outside)',
    11013: 'a guards\' bedroom', 6623: 'a treehouse: a room in the branches',
    20629: 'a cavern town: its streets drawn as streets',
    106284: 'a room inside a hollow tree',
}


def strong(text):
    out = {}
    for k, rx in CUE_RES.items():
        n = len(rx.findall(text))
        if n >= 3 or (k == 'web' and n >= 2):
            out[k] = n
    return out


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    world = World(Config())
    await world.load()
    zone = int(sys.argv[sys.argv.index('--zone') + 1]) if '--zone' in sys.argv else None
    import room_looks
    pinned = room_looks.load_overrides()['rooms']
    per_zone = collections.defaultdict(list)
    for r in world.rooms.values():
        zn = getattr(getattr(r, 'zone', None), 'number', None)
        if zone is not None and zn != zone:
            continue
        if r.vnum in ACCEPT or r.vnum in pinned or getattr(r, 'look_why', None) == 'stated':
            continue
        cues = strong(f'{r.name} {r.description}')
        # (a room whose webs are hung in it by the client: the web dressing over a room's own look)
        bad = [c for c in CONFLICT.get(r.look, ()) if c in cues and not (c == 'web' and r.look in WEB_OVER)]
        if bad:
            per_zone[(zn, getattr(r.zone, 'name', '?'))].append((r.vnum, r.name, r.look, r.look_why, bad))
    total = sum(len(v) for v in per_zone.values())
    for (zn, name), rows in sorted(per_zone.items(), key=lambda kv: -len(kv[1])):
        print(f'== zone {zn} {name}: {len(rows)} rooms')
        for row in rows[:None if '--all' in sys.argv else 4]:
            print('   ', row)
    print(f'{total} rooms whose look disagrees with their words, in {len(per_zone)} zones')


asyncio.run(main())
