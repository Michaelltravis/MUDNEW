"""Read the Bedlam world atlas (world/atlas/bedlam-atlas.html) into world/atlas/bedlam.json.

The atlas page carries its whole world in one `const DATA = {...}` line: 91 areas, 8,038 rooms
with their map position, terrain, name and exits, the doors, the map's labels and the bends of
drawn exit lines. This keeps all of it in a form the other atlas tools read, with exits named as
the game names them (north, east, south, west, up, down).

    python3 tools/atlas/extract.py [path/to/bedlam-atlas.html]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SRC = os.path.join(ROOT, 'world', 'atlas', 'bedlam-atlas.html')
OUT = os.path.join(os.environ.get('ATLAS_OUT') or os.path.join(ROOT, 'world', 'atlas'), 'bedlam.json')

# the atlas's exit slots, in its order (it fills only the compass and up/down)
SLOTS = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', 'up', 'down', 'in', 'out']
NAMES = {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west', 'up': 'up', 'down': 'down',
         'u': 'up', 'd': 'down', 'ne': 'northeast', 'se': 'southeast', 'sw': 'southwest',
         'nw': 'northwest', 'in': 'in', 'out': 'out'}
# the atlas's terrain codes (CircleMUD sectors as Bedlam coded them)
TERRAIN = {100: 'inside', 110: 'city', 120: 'forest', 130: 'field', 150: 'shallow water',
           160: 'deep water', 170: 'hills', 180: 'mountain'}
# its door codes
DOORS = {2: 'door', 3: 'locked door'}


def read_data(path):
    """The atlas's DATA object."""
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.lstrip().startswith('const DATA'):
                body = line[line.index('{'):].rstrip().rstrip(';')
                return json.loads(body)
    raise SystemExit(f'no `const DATA` line in {path}')


def convert(data):
    areas = {a: {'name': v[0], 'builder': v[1]} for a, v in data['areas'].items()}
    doors = data.get('doors', {})
    rooms = {}
    for vnum, area, x, y, z, terrain, name, slots in data['rooms']:
        exits = {}
        for i, to in enumerate(slots):
            if to and to > 0:
                exits[NAMES[SLOTS[i]]] = to
        room = {'area': area, 'name': name or '', 'x': x, 'y': y, 'z': z,
                'terrain': TERRAIN.get(terrain, 'unknown'), 'exits': exits}
        d = doors.get(str(vnum))
        if d:
            room['doors'] = {NAMES[k]: DOORS.get(v, f'code {v}') for k, v in d.items()}
        rooms[str(vnum)] = room
    labels = [{'area': a, 'x': x, 'y': y, 'z': z, 'w': w, 'h': h, 'text': t}
              for a, x, y, z, w, h, t in data.get('labels', [])]
    # (a few are drawn for a spoken or acted way on: kneel, bow, say elvandar)
    lines = {v: {NAMES.get(k, k): pts for k, pts in d.items()} for v, d in data.get('cl', {}).items()}
    return {'source': 'bedlam-atlas.html', 'y_axis': 'north is +y (the game draws north as -y)',
            'areas': areas, 'rooms': rooms, 'labels': labels, 'lines': lines}


def write(atlas, path):
    """One room per line: big, but diffs stay readable when the atlas is re-imported."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{\n')
        for key in ('source', 'y_axis'):
            f.write(f'"{key}": {json.dumps(atlas[key])},\n')
        f.write('"areas": {\n' + ',\n'.join(f'{json.dumps(a)}: {json.dumps(v, ensure_ascii=False)}'
                                             for a, v in sorted(atlas['areas'].items(), key=lambda kv: int(kv[0]))) + '\n},\n')
        f.write('"rooms": {\n' + ',\n'.join(f'{json.dumps(v)}: {json.dumps(r, ensure_ascii=False)}'
                                             for v, r in sorted(atlas['rooms'].items(), key=lambda kv: int(kv[0]))) + '\n},\n')
        f.write('"labels": [\n' + ',\n'.join(json.dumps(l, ensure_ascii=False) for l in atlas['labels']) + '\n],\n')
        f.write('"lines": {\n' + ',\n'.join(f'{json.dumps(v)}: {json.dumps(d)}'
                                             for v, d in sorted(atlas['lines'].items(), key=lambda kv: int(kv[0]))) + '\n}\n')
        f.write('}\n')


def load(path=OUT):
    """The extracted atlas, for the other tools and the tests."""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    atlas = convert(read_data(src))
    write(atlas, OUT)
    exits = sum(len(r['exits']) for r in atlas['rooms'].values())
    print(f"{len(atlas['areas'])} areas, {len(atlas['rooms'])} rooms, {exits} exits, "
          f"{sum(len(r.get('doors', {})) for r in atlas['rooms'].values())} doors, {len(atlas['labels'])} labels -> {os.path.relpath(OUT, ROOT)}")


if __name__ == '__main__':
    main()
