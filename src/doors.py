"""Doors: one place that finds them, changes them and tells the web clients.

An exit with a door carries a dict: {'name', 'state': 'open'|'closed', 'locked', 'key_vnum',
and optionally 'broken', 'hp', 'sealed_until', 'barricaded_until', 'magically_blocked',
'pickproof', 'pick_difficulty'}. Each side of a doorway keeps its own dict (the names can
differ: "trapdoor" above, "up door" below); every change goes through apply(), which keeps
both sides in step, stamps a revision and pushes one small event to the web clients of both
zones: {"type": "door", "doors": [{vnum, dir, label, state, locked, broken, rev}]}.

Names are CircleMUD keyword lists ("door wooden", "manhole man hole"); label() turns them
into something to print ("wooden door", "manhole").
"""
import asyncio
import logging
import time

logger = logging.getLogger('Misthollow')

ORDER = ('north', 'east', 'south', 'west', 'up', 'down')
OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}
_DIR_WORDS = {d: d for d in ORDER}
_DIR_WORDS.update({'n': 'north', 'e': 'east', 's': 'south', 'w': 'west', 'u': 'up', 'd': 'down'})
_SKIP = {'the', 'a', 'an'}
# words that name the thing itself (the rest of a keyword list describes it)
_NOUNS = {'door', 'doors', 'gate', 'gates', 'trapdoor', 'grate', 'grating', 'hatch', 'cell', 'curtain',
          'vent', 'cage', 'lid', 'tomb', 'manhole', 'panel', 'bookcase', 'safe', 'cupboard', 'fridge',
          'larder', 'wall', 'block', 'boulder', 'rock', 'stone', 'stones', 'crack', 'altar', 'throne',
          'screen', 'bars', 'head', 'mass', 'coffin', 'floor', 'ceiling', 'square'}
_GENERIC = {'door', 'doors', 'gate', 'gates'}
# what a change may touch on the far side too (barricades and seals stay on their side)
_MIRRORED = ('state', 'locked', 'broken', 'magically_blocked')

WORLD = None                        # set by normalize() at load
_rev_base = int(time.time() * 1000)  # revisions keep rising across server restarts
_rev_n = 0
_pending = {}                       # (vnum, dir) -> (room, dir)
_scheduled = False


# ---------------------------------------------------------------- finding a door
def canon_dir(word):
    """A direction word: full names and n/e/s/w/u/d only ('s' is south, never 'east')."""
    return _DIR_WORDS.get((word or '').lower())


def doors_in(room):
    """[(dir, exit, door)] for every exit of `room` that has a door, in direction order."""
    out = []
    for d in ORDER:
        ex = (getattr(room, 'exits', None) or {}).get(d)
        door = ex.get('door') if ex else None
        if isinstance(door, dict):
            out.append((d, ex, door))
    for d, ex in (getattr(room, 'exits', None) or {}).items():
        if d not in ORDER and ex and isinstance(ex.get('door'), dict):
            out.append((d, ex, ex['door']))
    return out


def has_direction(words):
    return any(canon_dir(w) for w in words or [])


def resolve(room, words, prefer=None):
    """What the player named: (dir, exit, door, err).

    The last direction word wins ("door wooden north" is north). Without one, every word must
    start a word of the door's name or the exit's keywords ("unlock wooden", "pick gate",
    "open door"); ties go to `prefer(door)` (e.g. closed doors for open), then to direction
    order. err is None, 'what', 'noexit', 'nodoor' or 'noname'."""
    words = [w.lower() for w in words or [] if w and w.lower() not in _SKIP]
    if not words:
        return None, None, None, 'what'
    dirs = [canon_dir(w) for w in words if canon_dir(w)]
    if dirs:
        d = dirs[-1]
        ex = (getattr(room, 'exits', None) or {}).get(d)
        if not ex:
            return d, None, None, 'noexit'
        door = ex.get('door')
        if not isinstance(door, dict):
            return d, ex, None, 'nodoor'
        return d, ex, door, None
    found = []
    for d, ex, door in doors_in(room):
        vocab = (str(door.get('name', '')) + ' ' + str(ex.get('keyword') or '')).lower().replace('-', ' ').split()
        vocab.append('door')
        if all(any(v.startswith(w) for v in vocab) for w in words):
            found.append((d, ex, door))
    if not found:
        return None, None, None, 'noname'
    if prefer:
        found.sort(key=lambda f: 0 if prefer(f[2]) else 1)
    d, ex, door = found[0]
    return d, ex, door, None


def label(door):
    """'door wooden' -> 'wooden door', 'door cell' -> 'cell door', 'manhole man hole' ->
    'manhole'; names that already read naturally ('secret door', 'coffin lid') stay."""
    words = str((door or {}).get('name') or 'door').replace('\u2011', '-').split()
    if not words:
        return 'door'
    if len(words) == 1:
        return words[0]
    first, last = words[0].lower(), words[-1].lower()
    if first in last and first != last:
        return words[-1]                              # "book bookcase", "man hole manhole"
    if last in _NOUNS and first not in _GENERIC:
        return ' '.join(words)                        # already reads naturally
    noun, mods = words[0], []
    for w in words[1:]:
        lw = w.lower()
        if lw in noun.lower() or lw in _GENERIC or any(lw in m.lower() or m.lower() in lw for m in mods):
            continue                                  # "trap" in "trapdoor", "gold" beside "golden"
        mods.append(w)
    return ' '.join(mods + [noun])


# ---------------------------------------------------------------- the far side
def other_side(room, d):
    """(room, dir, door) of the same doorway seen from the other room, if it leads back."""
    ex = (getattr(room, 'exits', None) or {}).get(d)
    to = ex.get('room') if ex else None
    od = OPPOSITE.get(d)
    if to is None or not od:
        return None, None, None
    back = (getattr(to, 'exits', None) or {}).get(od)
    if not back:
        return None, None, None
    lead = back.get('room')
    if lead is not None and lead is not room:
        return None, None, None
    if lead is None and back.get('to_room') not in (None, getattr(room, 'vnum', None)):
        return None, None, None
    door = back.get('door')
    return to, od, door if isinstance(door, dict) else None


def _next_rev():
    global _rev_n
    _rev_n += 1
    return _rev_base + _rev_n


def apply(room, d, push=True, mirror=(), **changes):
    """Change a door on this side and the mirrored fields (plus any named in `mirror`) on
    the far side; a value of None removes the field on both sides. Returns the door dict."""
    ex = (getattr(room, 'exits', None) or {}).get(d)
    door = ex.get('door') if ex else None
    if not isinstance(door, dict):
        return None
    rev = _next_rev()
    for key, val in changes.items():
        if val is None:
            door.pop(key, None)
        else:
            door[key] = val
    door['rev'] = rev
    to, od, far = other_side(room, d)
    if far is not None:
        for key, val in changes.items():
            if val is None:
                far.pop(key, None)          # clearing (a burst door, a zone reset) clears both sides
            elif key in _MIRRORED or key in mirror:
                far[key] = val
        far['rev'] = rev
    if push:
        _queue(room, d)
        if far is not None:
            _queue(to, od)
    return door


def _queue(room, d):
    global _scheduled
    vnum = getattr(room, 'vnum', None)
    if vnum is None:
        return
    _pending[(vnum, d)] = (room, d)
    if _scheduled:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    _scheduled = True
    loop.call_soon(lambda: asyncio.ensure_future(_flush()))


async def _flush():
    global _scheduled
    _scheduled = False
    items = list(_pending.values())
    _pending.clear()
    wm = getattr(WORLD, 'web_map', None) if WORLD is not None else None
    if not wm or not items:
        return
    entries, zones = [], set()
    for room, d in items:
        ex = (getattr(room, 'exits', None) or {}).get(d)
        door = ex.get('door') if ex else None
        if not isinstance(door, dict):
            continue
        entries.append(public(room.vnum, d, door))
        zn = getattr(getattr(room, 'zone', None), 'number', None)
        if zn is not None:
            zones.add(zn)
    if not entries:
        return
    try:
        await wm.send_zone_event(zones, {'type': 'door', 'doors': entries})
    except Exception as e:
        logger.debug(f"door push failed: {e}")


def public(vnum, d, door):
    """What every viewer may know about a door."""
    return {'vnum': vnum, 'dir': d, 'label': label(door), 'state': door.get('state', 'open'),
            'locked': bool(door.get('locked')), 'broken': bool(door.get('broken')), 'rev': door.get('rev', 0)}


# ---------------------------------------------------------------- keys and picks
def key_vnum(door):
    k = (door or {}).get('key_vnum', (door or {}).get('key'))
    try:
        k = int(k)
    except (TypeError, ValueError):
        return None
    return k if k > 0 else None


def carried_keys(player):
    """vnums of everything the player carries or wears (a key on a chain counts)."""
    keys = set()
    for item in list(getattr(player, 'inventory', None) or []):
        v = getattr(item, 'vnum', None)
        if v is not None:
            keys.add(v)
    eq = getattr(player, 'equipment', None) or {}
    for item in (eq.values() if isinstance(eq, dict) else []):
        v = getattr(item, 'vnum', None) if item is not None else None
        if v is not None:
            keys.add(v)
    return keys


def has_key(door, keys):
    """A lock without a key can be worked by anyone (the CircleMUD rule this world uses)."""
    k = key_vnum(door)
    return True if k is None else k in (keys or ())


def can_pick(player, door):
    skills = getattr(player, 'skills', None) or {}
    return bool(skills.get('pick_lock', 0)) and not (door or {}).get('pickproof')


def key_name(door):
    k = key_vnum(door)
    proto = (getattr(WORLD, 'obj_prototypes', None) or {}).get(k) if k else None
    if isinstance(proto, dict):
        return proto.get('short_desc') or proto.get('name')
    return None


def view(door, keys, player):
    """The door as one viewer sees it (adds whether they can open the lock)."""
    now = time.time()
    v = {'name': door.get('name', 'door'), 'label': label(door), 'state': door.get('state', 'open'),
         'locked': bool(door.get('locked')), 'broken': bool(door.get('broken')),
         'keyless': key_vnum(door) is None, 'has_key': has_key(door, keys),
         'can_pick': can_pick(player, door), 'rev': door.get('rev', 0)}
    if door.get('sealed_until', 0) > now or door.get('magically_blocked'):
        v['sealed'] = True
    if door.get('barricaded_until', 0) > now:
        v['barricaded'] = True
    if v['locked'] and not v['has_key']:
        kn = key_name(door)
        if kn:
            v['key_name'] = kn
    return v


# ---------------------------------------------------------------- load and reset
def normalize(world):
    """Tidy the converted door data once at load, then remember it as the zone's reset state.

    "open and locked" (102 doors from the CircleMUD import) means lockable, starting open: it
    becomes unlocked. The two sides of a doorway agree (closed wins, locked wins, the key is
    shared)."""
    global WORLD
    WORLD = world
    for room in world.rooms.values():
        for d, ex, door in doors_in(room):
            if 'key' in door and 'key_vnum' not in door:
                door['key_vnum'] = door.pop('key')
            if door.get('state') not in ('open', 'closed'):
                door['state'] = 'open'
            if door['state'] != 'closed' and door.get('locked'):
                door['locked'] = False
    for room in world.rooms.values():
        for d, ex, door in doors_in(room):
            to, od, far = other_side(room, d)
            if far is None:
                continue
            closed = door.get('state') == 'closed' or far.get('state') == 'closed'
            locked = closed and bool(door.get('locked') or far.get('locked'))
            for dd in (door, far):
                dd['state'] = 'closed' if closed else 'open'
                dd['locked'] = locked
            k = key_vnum(door) or key_vnum(far)
            if k:
                for dd in (door, far):
                    if not key_vnum(dd):
                        dd['key_vnum'] = k
    world.door_init = {}
    for room in world.rooms.values():
        for d, ex, door in doors_in(room):
            world.door_init[(room.vnum, d)] = {'state': door.get('state', 'open'), 'locked': bool(door.get('locked'))}


def _occupied(room):
    return any(hasattr(c, 'account_name') for c in (getattr(room, 'characters', None) or []))


def reset_zone(world, zone):
    """Doors go back to how the zone starts (as a CircleMUD zone reset would), except where a
    player stands on either side."""
    init = getattr(world, 'door_init', None) or {}
    for room in list(getattr(zone, 'rooms', {}).values()):
        for d, ex, door in doors_in(room):
            want = init.get((room.vnum, d))
            if not want:
                continue
            same = (door.get('state') == want['state'] and bool(door.get('locked')) == want['locked']
                    and not door.get('broken'))
            if same:
                continue
            to, od, far = other_side(room, d)
            if _occupied(room) or (to is not None and _occupied(to)):
                continue
            apply(room, d, state=want['state'], locked=want['locked'], broken=None, hp=None,
                  sealed_until=None, barricaded_until=None, magically_blocked=None)
