"""Every class's abilities and the rig's animation clips, for the 3D client's tests.

tests/web/abilityfx.test.mjs reads the file this writes to check, without a running server,
that every ability a class can use has a look of its own (world3d/abilityfx-table.js) built
from clips the rig really has; tests/test_mastery.py --offline checks the file is current.
    python3 tools/dump_abilitybook.py           # write tests/web/fixtures/abilitybook.json
    python3 tools/dump_abilitybook.py --check   # exit 1 when it is out of date
"""
import json
import logging
import os
import struct
import sys
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
OUT = os.path.join(ROOT, 'tests', 'web', 'fixtures', 'abilitybook.json')
RIG = os.path.join(ROOT, 'src', 'web_isometric', 'art3d', 'chars', 'rig_anims.glb')


def clips():
    """The animation names in the rig's glTF (its JSON chunk)."""
    with open(RIG, 'rb') as f:
        data = f.read()
    size, _kind = struct.unpack('<II', data[12:20])
    return sorted(a['name'] for a in json.loads(data[20:20 + size]).get('animations', []))


def build():
    logging.disable(logging.CRITICAL)
    import combat_hooks
    import combat_range as cr
    import mastery
    from config import Config
    from spells import SPELLS
    out = {'clips': clips(), 'classes': {}, 'extras': {}}
    for cls in sorted(Config.CLASSES):
        who = types.SimpleNamespace(char_class=cls)
        rows = []
        for e in mastery.book(cls):
            a = e['id']
            row = {'id': a, 'type': e['type'], 'level': e.get('level')}
            if e.get('talent'):
                row['talent'] = e['talent']
            if e.get('passive'):
                row['passive'] = True
            else:
                spell = e['type'] == 'spell'
                row['target'] = e.get('target', 'enemy')
                row['shape'] = cr.ability_range(a, True)[1] if spell else combat_hooks.event_shape(a, cls)
                if spell:       # what its 'spell' event says (skills' looks choose their own)
                    row['school'] = cr.spell_school(a, SPELLS.get(a), who)
            rows.append(row)
        out['classes'][cls] = rows
        have = {r['id'] for r in rows}
        extras = [{'id': a, 'target': aim, 'shape': combat_hooks.event_shape(a, cls)}
                  for a, (aim, users) in sorted(combat_hooks.EXTRA_ABILITIES.items())
                  if cls in users.split() and a not in have]
        if extras:
            out['extras'][cls] = extras
    return out


def text():
    return json.dumps(build(), indent=1, sort_keys=True) + '\n'


def main():
    new = text()
    old = open(OUT).read() if os.path.exists(OUT) else ''
    if '--check' in sys.argv:
        print('abilitybook.json is current' if new == old else 'abilitybook.json is out of date: run tools/dump_abilitybook.py')
        sys.exit(0 if new == old else 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write(new)
    book = json.loads(new)
    n = sum(1 for rows in book['classes'].values() for r in rows if not r.get('passive'))
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {n} active abilities over {len(book['classes'])} classes, "
          f"{sum(len(v) for v in book['extras'].values())} extras, {len(book['clips'])} clips")


if __name__ == '__main__':
    main()
