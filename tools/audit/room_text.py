#!/usr/bin/env python3
"""Do the rooms look like what their text says? For every zone: how its rooms are drawn (their
looks, room_looks.py), what their descriptions name standing in them (room_features.py), and the
rooms whose look the text contradicts:

  town look, no town      drawn as streets and houses (city), but the text names no street,
                          house, shop, market, inn... and reads open country or a sacred place
  roofed look, open text  drawn with walls and a ceiling, but the text speaks of sky, sun,
                          grass, turf or trees and never of a ceiling or roof
  open look, roofed text  drawn as open country, but the text speaks of a ceiling, a hall, a
                          chamber or corridors and never of the sky

    python3 tools/audit/room_text.py                         # the table, worst zones first
    python3 tools/audit/room_text.py --zone 476              # one zone, room by room
    python3 tools/audit/room_text.py --md docs/world/room_text_audit.md
"""
import argparse
import asyncio
import collections
import logging
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

TOWN = re.compile(r'\b(streets?|houses?|homes?|cottages?|shops?|stores?|markets?|inns?|taverns?|alleys?|guilds?|'
                  r'bakery|smithy|blacksmiths?|merchants?|stalls?|square|townsfolk|citizens?|city walls?|gates? of the (?:city|town)|'
                  r'boulevard|plaza|avenue|lanes?|wharf|docks?|warehouses?|shopkeepers?|bank|'
                  # a town's streets say so in their stones and doors, not always in the word town
                  r'windows?|doorways?|flagstones?|paving|paved|cobbles(?:tones)?|quays?|portcullis|gatehouse|post office)\b', re.I)
SKY = re.compile(r'\b(sky|skies|sunlight|sun\b|moonlight|starlight|stars|clouds?|open air|grass|turf|meadows?|trees?|'
                 r'breeze|wind|rain|overhead the|heavens)\b', re.I)
ROOF = re.compile(r'\b(ceiling|roof(?:ed)?|vault(?:ed)?|walls? of (?:the )?(?:room|hall|chamber)|chambers?|halls?|corridors?|'
                  r'rooms?\b|indoors|inside the)\b', re.I)
# a room's own name settles it: a tunnel is roofed whatever wind blows through it, a forest open
NAMED_ROOFED = re.compile(r'\b(tunnels?|caves?|caverns?|sewers?|pipes?|mines?|shafts?|ladder|cellars?|crypts?|tombs?|vaults?|'
                          r'chambers?|halls?|rooms?|corridors?|passages?|labyrinth|freezer|quarters|stacks|huts?|houses?|inn|tavern|shop)\b', re.I)
NAMED_OPEN = re.compile(r'\b(forest|woods?|clearing|field|meadow|plains?|hills?|road|path|trail|garden|yard|court(?:yard)?|'
                        r'beach|shore|desert|dunes?|mountain|peak|pass|cliffs?|valley|glade|grove|swamp|marsh|moor)\b', re.I)
ROOFED_LOOKS = {'inside', 'dungeon', 'crypt', 'cave', 'mine', 'sewer', 'ice_cave', 'lava_cave'}
OPEN_LOOKS = {'field', 'forest', 'hills', 'mountain', 'desert', 'snow', 'swamp', 'shore', 'volcanic', 'web', 'stones', 'garden', 'ruins', 'terrace', 'camp'}


def judge(room):
    """What is wrong with how a room is drawn, by its text (None: nothing)."""
    look = getattr(room, 'look', None) or getattr(room, 'sector_type', '')
    text = f"{room.name}. {room.description or ''}"
    if look == 'city' and not TOWN.search(text):
        return 'town look, no town'
    name = room.name or ''
    if look in ROOFED_LOOKS and SKY.search(text) and not ROOF.search(text) and not NAMED_ROOFED.search(name):
        return 'roofed look, open text'
    if look in OPEN_LOOKS and ROOF.search(text) and not SKY.search(text) and look not in ('mountain',) and not NAMED_OPEN.search(name):
        return 'open look, roofed text'
    return None


def survey(world):
    zones = collections.OrderedDict()
    for v, r in sorted(world.rooms.items()):
        z = getattr(getattr(r, 'zone', None), 'number', None)
        if z is None:
            continue
        s = zones.setdefault(z, {'zone': z, 'name': getattr(r.zone, 'name', str(z)), 'rooms': 0, 'looks': collections.Counter(),
                                 'featured': 0, 'features': collections.Counter(), 'wrong': collections.Counter(), 'examples': []})
        s['rooms'] += 1
        s['looks'][getattr(r, 'look', None) or r.sector_type] += 1
        feats = getattr(r, 'features', None) or []
        s['featured'] += bool(feats)
        for f in feats:
            s['features'][f['k']] += 1
        w = judge(r)
        if w:
            s['wrong'][w] += 1
            if len(s['examples']) < 3:
                s['examples'].append((v, r.name, w))
    for s in zones.values():
        s['wrong_n'] = sum(s['wrong'].values())
    return zones


def table(zones, md=False):
    rows = sorted(zones.values(), key=lambda s: (-s['wrong_n'], s['zone']))
    out = []
    if md:
        out += ['| zone | name | rooms | looks | wrongly drawn | rooms naming features | most named |', '|---|---|---|---|---|---|---|']
    for s in rows:
        looks = ', '.join(f'{k} {n}' for k, n in s['looks'].most_common(3))
        wrong = ', '.join(f'{k}: {n}' for k, n in s['wrong'].most_common()) or '-'
        feats = ', '.join(f'{k} {n}' for k, n in s['features'].most_common(4)) or '-'
        pct = f"{100 * s['featured'] // max(1, s['rooms'])}%"
        cells = [s['zone'], s['name'][:30], s['rooms'], looks, wrong, pct, feats]
        out.append(('| ' + ' | '.join(map(str, cells)) + ' |') if md else
                   f"{s['zone']:>4} {s['name'][:28]:28} {s['rooms']:>4}  {wrong[:40]:40} {pct:>4}  {feats[:60]}")
    return '\n'.join(out)


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--md', default='')
    ap.add_argument('--zone', type=int, default=0)
    a = ap.parse_args()
    logging.disable(logging.WARNING)
    from config import Config
    from world import World
    import room_features
    world = World(Config())
    await world.load()
    if not any(getattr(r, 'features', None) is not None for r in world.rooms.values()):
        room_features.annotate(world)
    zones = survey(world)
    if a.zone:
        for v, r in sorted(world.rooms.items()):
            if getattr(r.zone, 'number', None) == a.zone:
                fs = ' '.join(f"{f['k']}{'x' + str(f['n']) if f['n'] > 1 else ''}{'*' if f.get('main') else ''}{'(' + f['c'] + ')' if f.get('c') else ''}"
                              for f in r.features)
                print(v, (getattr(r, 'look', '') or '')[:8].ljust(8), r.name[:36].ljust(36), (judge(r) or '').ljust(22), fs)
        return
    total = sum(s['rooms'] for s in zones.values())
    featured = sum(s['featured'] for s in zones.values())
    wrong = collections.Counter()
    feats = collections.Counter()
    for s in zones.values():
        wrong.update(s['wrong'])
        feats.update(s['features'])
    head = (f"{len(zones)} zones, {total} rooms; {featured} rooms ({100 * featured // total}%) name something standing in them; "
            f"{sum(wrong.values())} rooms drawn against their text ({', '.join(f'{k} {n}' for k, n in wrong.most_common())})")
    print(head)
    print('most named:', ', '.join(f'{k} {n}' for k, n in feats.most_common(30)))
    if a.md:
        with open(os.path.join(ROOT, a.md), 'w', encoding='utf-8') as f:
            f.write('# Room text audit (generated)\n\n'
                    f'`python3 tools/audit/room_text.py --md {a.md}` writes this from the world as it loads. {head}.\n\n'
                    f"Most named: {', '.join(f'{k} {n}' for k, n in feats.most_common(40))}.\n\n"
                    'See [room_visuals.md](room_visuals.md) for the plan.\n\n')
            f.write(table(zones, md=True) + '\n')
        print('wrote', a.md)
    else:
        print(table(zones))


if __name__ == '__main__':
    asyncio.run(main())
