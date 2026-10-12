#!/usr/bin/env python3
"""The build-out of the connector zones: hand-written rooms, creatures and items, folded into the
world by tools/atlas/build_world.py.

The writing lives in world/buildout/parts/<job>.json (one per job of tools/atlas/briefs.py):
    {"job": "...", "rooms": {vnum: description}, "extras": {vnum: [{keywords, description}]},
     "creatures": [...], "items": [...]}
A room's description replaces its placeholder (wrapped at 72 columns, like the rest of the
world). Creatures and items carry words and facts; their numbers come from their level and kind
(stats(), item_numbers()), fitted to the creatures and gear the world already has, and they are
placed by their terrains and room names, the same way on every build.

    python3 tools/atlas/buildout.py --check world/buildout/parts/<job>.json   # a writer's check
    python3 tools/atlas/buildout.py --merge <job>        # fold parts/<job>.p1.json, .p2.json ... in
    python3 tools/atlas/buildout.py --check-all                                # every part
"""
import collections
import glob
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import briefs  # noqa: E402

ROOT = briefs.ROOT
PARTS = os.path.join(ROOT, 'world', 'buildout', 'parts')
THEMES = os.path.join(ROOT, 'world', 'buildout', 'themes.json')

WORDS = (40, 115)            # a description's words, and its sentences (the brief asks 45-100, 3-5)
SENTENCES = (3, 6)
KINDS = ('animal', 'humanoid', 'monster', 'undead')
ITEM_KINDS = ('weapon', 'armor', 'treasure', 'food', 'potion', 'light')
WEAPON_TYPES = ('slash', 'pierce', 'pound')
SLOTS = {'body': 'body', 'head': 'head', 'legs': 'legs', 'feet': 'feet', 'hands': 'hands', 'arms': 'arms',
         'shield': 'shield', 'about': 'about', 'waist': 'waist', 'wrist': 'wrist1', 'neck': 'neck1',
         'finger': 'finger1', 'hold': 'hold'}
BONUS = {'str': 1, 'dex': 1, 'con': 1, 'int': 1, 'wis': 1, 'cha': 1, 'hitroll': 2, 'damroll': 2, 'hp': 15}
SECTORS = ('inside', 'city', 'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim',
           'water_surface', 'underwater', 'flying', 'desert', 'swamp', 'cave')
WATER = briefs.WATER
COMPASS_RX = re.compile(r'\b(north|south|east|west)(ern|erly|ward|wards|-?east|-?west)?\b', re.I)


def _sentences(text):
    return [s for s in re.split(r'(?<=[.!?])["\')]*\s+', text.strip()) if s.strip()]


def _norm(s):
    return re.sub(r'[^a-z ]+', '', s.lower()).strip()


def _proper_names(zones, rooms):
    """Place names with a compass word in them ("the Great Eastern Desert"), longest first: they
    are names, not directions."""
    names = {z['name'] for z in zones.values()} | {r.get('name', '') for r in rooms.values()}
    out = set()
    for n in names:
        n = (n or '').strip()
        if COMPASS_RX.search(n):
            out.add(n)
            if n.lower().startswith('the '):
                out.add(n[4:])
    return sorted(out, key=len, reverse=True)


def compass_problems(text, room, proper):
    stripped = text
    for n in proper:
        stripped = re.sub(re.escape(n), ' ', stripped, flags=re.I)
    have = {d for d, t, ex in briefs.exits_of(room)}
    bad = []
    for m in COMPASS_RX.finditer(stripped):
        base, tail = m.group(1).lower(), (m.group(2) or '').lower()
        if tail.lstrip('-') in ('east', 'west'):
            bad.append(f'"{m.group(0)}" (no diagonal ways)')
        elif base not in have:
            bad.append(f'"{m.group(0)}" (no way {base} here)')
    return bad


class World:
    def __init__(self):
        self.zones, self.rooms = briefs.load()
        self.proper = _proper_names(self.zones, self.rooms)
        with open(THEMES, encoding='utf-8') as f:
            self.themes = json.load(f)


def check(path, world=None, quiet=False):
    """Problems with one part, as a list of strings (empty when it is good)."""
    w = world or World()
    probs = []
    try:
        with open(path, encoding='utf-8') as f:
            part = json.load(f)
    except (OSError, ValueError) as e:
        return [f'not readable as JSON: {e}']
    job = part.get('job') or os.path.splitext(os.path.basename(path))[0]
    if job not in briefs.JOBS:
        return [f'unknown job {job!r}']
    zs, _, _, design = briefs.JOBS[job]
    want = briefs.job_rooms(job, w.zones, w.rooms)
    rooms = part.get('rooms') or {}
    if not isinstance(rooms, dict):
        return ['"rooms" must map vnum to description']
    missing = [v for v in want if str(v) not in rooms]
    if missing:
        probs.append(f'{len(missing)} of your rooms are missing: {missing[:12]}')
    extra = [k for k in rooms if not k.isdigit() or int(k) not in want]
    if extra:
        probs.append(f'rooms that are not yours: {extra[:12]}')
    seen = collections.defaultdict(list)
    for k, text in rooms.items():
        if not k.isdigit() or int(k) not in w.rooms:
            continue
        v, room = int(k), w.rooms[int(k)]
        if not isinstance(text, str) or not text.strip():
            probs.append(f'{v}: empty')
            continue
        words = len(text.split())
        sents = _sentences(text)
        if not WORDS[0] <= words <= WORDS[1]:
            probs.append(f'{v} {room.get("name")}: {words} words (write 45-100)')
        if not SENTENCES[0] <= len(sents) <= SENTENCES[1]:
            probs.append(f'{v} {room.get("name")}: {len(sents)} sentences (write 3-5)')
        for b in compass_problems(text, room, w.proper):
            probs.append(f'{v} {room.get("name")}: compass word {b}')
        if re.search(r'midgaard|placeholder|\{|\}|&[a-z]|\bvnum\b', text, re.I):
            probs.append(f'{v}: has a forbidden word or code (Midgaard, braces, colour codes, vnum)')
        if ' '.join(text.split()) == ' '.join((room.get('description') or '').split()):
            probs.append(f'{v}: still the placeholder text')
        for s in sents:
            if len(s.split()) >= 5:
                seen[_norm(s)].append(v)
    for s, vs in seen.items():
        if len(vs) > 1:
            probs.append(f'the same sentence in {vs[:6]}: "{s[:70]}..."')
    for k, xs in (part.get('extras') or {}).items():
        if str(k) not in rooms:
            probs.append(f'extras for {k}, which is not one of your rooms')
        for x in xs if isinstance(xs, list) else [xs]:
            if not isinstance(x, dict) or not str(x.get('keywords', '')).strip() or not str(x.get('description', '')).strip():
                probs.append(f'extras for {k}: each needs "keywords" and "description"')
    if design:
        probs += check_design(part, zs, w)
    elif part.get('creatures') or part.get('items'):
        probs.append('this job writes rooms only: leave "creatures" and "items" out')
    if not quiet:
        print(f'{os.path.relpath(path, ROOT)}: {len(rooms)} rooms; ' + ('OK' if not probs else f'{len(probs)} problem(s):'))
        for p in probs[:80]:
            print('  - ' + p)
        if len(probs) > 80:
            print(f'  ... and {len(probs) - 80} more')
    return probs


def check_design(part, zs, w):
    probs = []
    cs, its = part.get('creatures') or [], part.get('items') or []
    if not isinstance(cs, list) or not isinstance(its, list):
        return ['"creatures" and "items" must be lists']
    ids = set()
    item_ids = {i.get('id') for i in its if isinstance(i, dict)}
    dropped = set()
    lo = min(w.themes['zones'][str(z)]['levels'][0] for z in zs)
    hi = max(w.themes['zones'][str(z)]['levels'][1] for z in zs)
    zone_names = {w.rooms[v].get('name') for v in w.rooms if w.rooms[v]['_zone'] in zs}
    for c in cs:
        cid = c.get('id') if isinstance(c, dict) else None
        if not cid or cid in ids:
            probs.append(f'creature without a unique "id": {str(c)[:60]}')
            continue
        ids.add(cid)
        for key in ('keywords', 'short_desc', 'long_desc', 'description', 'kind', 'level', 'count'):
            if c.get(key) in (None, ''):
                probs.append(f'creature {cid}: needs "{key}"')
        if c.get('kind') not in KINDS:
            probs.append(f'creature {cid}: kind must be one of {KINDS}')
        if not isinstance(c.get('level'), int) or not lo - 2 <= c['level'] <= hi + 2:
            probs.append(f'creature {cid}: level {c.get("level")} is outside {lo}-{hi}')
        if not isinstance(c.get('count'), int) or not 1 <= c['count'] <= 60:
            probs.append(f'creature {cid}: count must be 1-60')
        secs, names = c.get('sectors') or [], c.get('rooms') or []
        if not secs and not names:
            probs.append(f'creature {cid}: give "sectors" and/or "rooms"')
        for s in secs:
            if s not in SECTORS:
                probs.append(f'creature {cid}: unknown sector {s!r}')
        for n in names:
            if n not in zone_names:
                probs.append(f'creature {cid}: no room named {n!r} in the zone')
        ld = str(c.get('long_desc') or '')
        if ld and (not ld[0].isupper() or ld.rstrip()[-1:] not in '.!'):
            probs.append(f'creature {cid}: long_desc should be a full sentence')
        for d in c.get('drops') or []:
            if d.get('item') not in item_ids:
                probs.append(f'creature {cid}: drops unknown item {d.get("item")!r}')
            elif not 1 <= int(d.get('chance', 0)) <= 50:
                probs.append(f'creature {cid}: drop chance must be 1-50')
            dropped.add(d.get('item'))
        if not where(c, zs, w, only=set(int(k) for k in (part.get('rooms') or {}) if str(k).isdigit())):
            probs.append(f'creature {cid}: none of your rooms matches its sectors/rooms')
    seen_items = set()
    for i in its:
        iid = i.get('id') if isinstance(i, dict) else None
        if not iid or iid in seen_items:
            probs.append(f'item without a unique "id": {str(i)[:60]}')
            continue
        seen_items.add(iid)
        for key in ('keywords', 'short_desc', 'room_desc', 'description', 'kind', 'level'):
            if i.get(key) in (None, ''):
                probs.append(f'item {iid}: needs "{key}"')
        if i.get('kind') not in ITEM_KINDS:
            probs.append(f'item {iid}: kind must be one of {ITEM_KINDS}')
        if i.get('kind') == 'weapon' and i.get('weapon_type') not in WEAPON_TYPES:
            probs.append(f'item {iid}: a weapon needs weapon_type {WEAPON_TYPES}')
        if i.get('kind') == 'armor' and i.get('wear_slot') not in SLOTS:
            probs.append(f'item {iid}: armor needs wear_slot, one of {tuple(SLOTS)}')
        b = i.get('bonus') or {}
        if len(b) > 1 or any(k not in BONUS or not 0 < int(v) <= BONUS[k] for k, v in b.items()):
            probs.append(f'item {iid}: one small bonus at most ({BONUS})')
        if not isinstance(i.get('level'), int) or not lo - 2 <= i['level'] <= hi + 2:
            probs.append(f'item {iid}: level {i.get("level")} is outside {lo}-{hi}')
        if iid not in dropped:
            probs.append(f'item {iid}: no creature drops it')
    return probs


def where(c, zs, w, only=None):
    """The rooms a creature may stand in: of the rooms its writer wrote (`only`), those of its
    sectors or names, never where creatures may not go."""
    secs, names = set(c.get('sectors') or []), set(c.get('rooms') or [])
    out = []
    for v, r in w.rooms.items():
        if r['_zone'] not in zs or (only is not None and v not in only):
            continue
        flags = set(r.get('flags') or [])
        if flags & {'no_mob', 'imm_only', 'deathtrap', 'death', 'peaceful'}:
            continue
        if (secs and r.get('sector_type', 'inside') in secs) or (names and r.get('name') in names):
            out.append(v)
    return sorted(out)


# ---------------------------------------------------------------- numbers
# Fitted to the creatures the world already has (median by level, bosses and shopkeepers left
# out) so a new wolf hits and lasts like the old ones: health 20 + 14L + 0.15L^2, a blow
# 1.5 + 1.45L, armour 97 - 3L, experience 55L + 20. Weapons and armour follow the world's gear
# below level 50 (a weapon's blow about 4 + 0.15L; armour a few points a piece).
KIND_HP = {'animal': 0.9, 'humanoid': 1.0, 'monster': 1.2, 'undead': 1.1}
SLOT_ARMOR = {'body': (3, 8, 10), 'shield': (3, 12, 6), 'head': (2, 12, 3), 'legs': (2, 12, 3), 'feet': (2, 12, 3),
              'hands': (2, 12, 2), 'arms': (2, 12, 2), 'about': (1, 12, 3), 'waist': (1, 15, 1), 'wrist': (1, 15, 1),
              'neck': (1, 15, 1), 'finger': (1, 15, 1), 'hold': (0, 99, 1)}
MOB_BASE, OBJ_BASE = 600000, 700000          # + zone * 100 + n (world/buildout/vnums.json keeps them)
REGISTRY = os.path.join(ROOT, 'world', 'buildout', 'vnums.json')


def stats(level, kind):
    L = max(1, int(level))
    hp = (20 + 14 * L + 0.15 * L * L) * KIND_HP.get(kind, 1.0)
    dmg = (1.5 + 1.45 * L) * (1.1 if kind == 'monster' else 1.0)
    dn = max(1, L // 4 + 1)
    return {'hp_dice': f'{L}d8+{max(0, round(hp - L * 4.5))}',
            'damage_dice': f'{dn}d6+{max(0, round(dmg - dn * 3.5))}',
            'armor_class': max(-20, 97 - 3 * L - (5 if kind == 'monster' else 0)),
            'exp': 55 * L + 20, 'gold': 12 * L if kind == 'humanoid' else 0}


def item_numbers(i):
    L, kind = max(1, int(i['level'])), i['kind']
    out = {'item_type': kind, 'type': kind, 'min_level': L}
    if kind == 'weapon':
        avg = 4 + 0.15 * L
        n = 1 if L < 10 else 2
        s = max(4, min(12, round(2 * avg - 1))) if n == 1 else max(3, round(avg - 1))
        out.update(damage_dice=f'{n}d{s}', weapon_type=i['weapon_type'], weight=6, value=25 * L + 40)
    elif kind == 'armor':
        base, per, weight = SLOT_ARMOR[i['wear_slot']]
        out.update(wear_slot=SLOTS[i['wear_slot']], armor=base + L // per, weight=weight, value=20 * L + 30)
    elif kind == 'treasure':
        out.update(weight=1, value=30 * L + 25)
    elif kind == 'food':
        out.update(food_value=12 + L // 3, nutrition=12 + L // 3, weight=1, value=5 + L)
    elif kind == 'potion':
        out.update(spell_effects=['cure_light' if L < 12 else 'cure_serious' if L < 25 else 'cure_critical'],
                   weight=1, value=40 + 10 * L)
    elif kind == 'light':
        out.update(light_hours=48, weight=2, value=15 + 2 * L)
    if i.get('bonus'):
        out['affects'] = [{'type': k, 'value': int(v)} for k, v in i['bonus'].items()]
    return out


def _crc(s):
    import zlib
    return zlib.crc32(s.encode('utf-8'))


def _vnum(registry, kind, key, zone, taken):
    book = registry.setdefault(kind, {})
    if key in book:
        return book[key]
    base = (MOB_BASE if kind == 'mobs' else OBJ_BASE) + zone * 100
    v = base
    while v in taken or v in book.values():
        v += 1
    book[key] = v
    return v


class _Rooms:
    """briefs-style access to the world being built ({vnum: room dict with _zone})."""
    def __init__(self, zones, rooms):
        self.zones, self.rooms = zones, rooms


def apply(new_zones, new_rooms, write=False):
    """Fold every part into the world being built (tools/atlas/build_world.py, while rooms still
    carry `_zone`): written descriptions and extras replace the placeholders; creatures and items
    become prototypes in their zone, the creatures placed by their terrains and room names."""
    parts = []
    for path in sorted(glob.glob(os.path.join(PARTS, '*.json'))):
        if re.search(r'\.p\d+\.json$', path):
            continue                                   # a writer's piece, not merged yet
        with open(path, encoding='utf-8') as f:
            parts.append(json.load(f))
    registry = {}
    if os.path.exists(REGISTRY):
        with open(REGISTRY, encoding='utf-8') as f:
            registry = json.load(f)
    taken = set()
    for z in new_zones.values():
        for key in ('mobs', 'objects'):
            ps = z.get(key) or {}
            taken |= {int(v) for v in (ps.keys() if isinstance(ps, dict) else (p['vnum'] for p in ps))}
    w = _Rooms(new_zones, new_rooms)
    summary = collections.Counter()
    # the rooms
    for part in parts:
        for k, text in (part.get('rooms') or {}).items():
            r = new_rooms.get(int(k))
            if r is None:
                continue
            r['description'] = textwrap.fill(' '.join(text.split()), 72)
            r.pop('placeholder', None)
            summary['rooms written'] += 1
        for k, xs in (part.get('extras') or {}).items():
            r = new_rooms.get(int(k))
            if r is None:
                continue
            ex = r.get('extra_descs') if isinstance(r.get('extra_descs'), dict) else {}
            for x in xs if isinstance(xs, list) else [xs]:
                ex[' '.join(str(x['keywords']).split())] = textwrap.fill(' '.join(str(x['description']).split()), 72)
            r['extra_descs'] = ex
            summary['extras'] += len(xs) if isinstance(xs, list) else 1
    # the items, then the creatures that carry them
    for part in parts:
        job = part.get('job')
        if job not in briefs.JOBS or not briefs.JOBS[job][3]:
            continue
        zs = briefs.JOBS[job][0]
        creatures = part.get('creatures') or []
        items = {i['id']: i for i in part.get('items') or []}
        mine = {int(k) for k in (part.get('rooms') or {}) if str(k).isdigit()}
        homes = {}
        for c in creatures:
            homes[c['id']] = where(c, zs, w, only=mine)
        item_zone = {}
        for c in creatures:
            for d in c.get('drops') or []:
                if d['item'] in items and d['item'] not in item_zone:
                    spots = homes[c['id']]
                    item_zone[d['item']] = collections.Counter(new_rooms[v]['_zone'] for v in spots).most_common(1)[0][0] if spots else zs[0]
        item_vnum = {}
        for iid, i in items.items():
            z = item_zone.get(iid, zs[0])
            v = _vnum(registry, 'objects', f'{job}:{iid}', z, taken)
            taken.add(v)
            item_vnum[iid] = v
            proto = {'vnum': v, 'name': ' '.join(str(i['keywords']).split()), 'short_desc': i['short_desc'],
                     'room_desc': i['room_desc'], 'description': i['description'], **item_numbers(i)}
            new_zones[z].setdefault('objects', {})[str(v)] = proto
            summary['items'] += 1
        for c in creatures:
            spots = homes[c['id']]
            if not spots:
                continue
            z = collections.Counter(new_rooms[v]['_zone'] for v in spots).most_common(1)[0][0]
            v = _vnum(registry, 'mobs', f'{job}:{c["id"]}', z, taken)
            taken.add(v)
            kind = c['kind']
            flags = ['stay_zone']
            if c.get('aggressive'):
                flags.append('aggressive')
            elif kind == 'animal':
                flags.append('wimpy')
            if kind == 'undead':
                flags.append('undead')
            align = c.get('alignment')
            if not isinstance(align, int):
                align = {'animal': 0, 'undead': -800, 'monster': -500}.get(kind, 0)
            proto = {'vnum': v, 'name': ' '.join(str(c['keywords']).split()), 'short_desc': c['short_desc'],
                     'long_desc': c['long_desc'], 'description': textwrap.fill(' '.join(str(c['description']).split()), 72),
                     'level': int(c['level']), 'alignment': align, **stats(c['level'], kind), 'flags': flags,
                     'inventory': []}
            drops = [{'vnum': item_vnum[d['item']], 'chance': int(d['chance'])} for d in c.get('drops') or [] if d['item'] in item_vnum]
            if drops:
                tier = 'basic' if c['level'] < 10 else 'intermediate' if c['level'] < 20 else 'advanced' if c['level'] < 35 else 'elite'
                extra = {'basic': [200, 201], 'intermediate': [202, 203, 204, 205],
                         'advanced': [210, 211, 212, 213], 'elite': [214, 215, 216, 217]}[tier]
                proto['loot_table'] = drops + [{'vnum': e, 'chance': 5} for e in extra]
            new_zones[z].setdefault('mobs', {})[str(v)] = proto
            summary['creatures'] += 1
            # placed evenly over its rooms, the same way every build; a room already holding two
            # creatures passes it on to the next of its rooms
            count = min(int(c['count']), len(spots))
            step = len(spots) / count
            start = (_crc(c['id']) % 1000) / 1000 * step
            placed = 0
            for n in range(count):
                at = int(start + n * step) % len(spots)
                for j in range(len(spots)):
                    resets = new_rooms[spots[(at + j) % len(spots)]].setdefault('mob_resets', [])
                    if len(resets) < 2:
                        resets.append({'vnum': v, 'max': 1})
                        placed += 1
                        break
            summary['creatures placed'] += placed
    if write:
        with open(REGISTRY, 'w', encoding='utf-8') as f:
            json.dump({'_about': 'Vnums given to the build-out\'s creatures and items (job:id), kept so a rebuild never renumbers them.',
                       **{k: dict(sorted(v.items())) for k, v in registry.items() if k != '_about'}}, f, indent=1)
            f.write('\n')
    return dict(summary)


def merge(job):
    """Fold a writer's pieces (parts/<job>.p1.json, .p2.json ...) into parts/<job>.json, then
    remove the pieces. Later pieces win for the same room."""
    out_path = os.path.join(PARTS, f'{job}.json')
    merged = {'job': job, 'rooms': {}, 'extras': {}}
    if os.path.exists(out_path):
        with open(out_path, encoding='utf-8') as f:
            old = json.load(f)
        for k in ('rooms', 'extras'):
            merged[k].update(old.get(k) or {})
        for k in ('creatures', 'items'):
            if old.get(k):
                merged[k] = old[k]
    pieces = sorted(glob.glob(os.path.join(PARTS, f'{job}.p*.json')),
                    key=lambda p: int(re.search(r'\.p(\d+)\.json$', p).group(1)) if re.search(r'\.p(\d+)\.json$', p) else 0)
    for p in pieces:
        with open(p, encoding='utf-8') as f:
            piece = json.load(f)
        for k in ('rooms', 'extras'):
            merged[k].update(piece.get(k) or {})
        for k in ('creatures', 'items'):
            if piece.get(k):
                merged[k] = piece[k]
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=1, ensure_ascii=False)
        f.write('\n')
    for p in pieces:
        os.remove(p)
    print(f'{os.path.relpath(out_path, ROOT)}: {len(merged["rooms"])} rooms from {len(pieces)} piece(s)')


def main():
    if '--merge' in sys.argv and len(sys.argv) > sys.argv.index('--merge') + 1:
        merge(sys.argv[sys.argv.index('--merge') + 1])
        return
    if '--check-all' in sys.argv:
        w = World()
        bad = 0
        for path in sorted(glob.glob(os.path.join(PARTS, '*.json'))):
            bad += bool(check(path, w))
        sys.exit(1 if bad else 0)
    if '--check' in sys.argv and len(sys.argv) > sys.argv.index('--check') + 1:
        path = sys.argv[sys.argv.index('--check') + 1]
        sys.exit(1 if check(path) else 0)
    print(__doc__)
    sys.exit(2)


if __name__ == '__main__':
    main()
