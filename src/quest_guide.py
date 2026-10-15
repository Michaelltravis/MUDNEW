"""Where to go next for an ordinary quest, for /play's tracker, minimap mark and ground arrow.

A marquee quest has its own tracker block (marquee.quest_block); every other quest (kill, talk,
visit, collect, the tutorial) had none, so the 3D client showed nothing and pointed nowhere. This
builds the same block for the player's first unfinished quest:

  {'id', 'name', 'stage', 'of', 'title', 'objectives': [{text, have, need, done}],
   'where': {'vnum', 'name', 'steps', 'dir'}, 'kind': 'quest'}

`where` is the nearest room (by walking, from where the player stands) that holds what the current
objective wants: a creature of that name to kill, the person to talk to, the room to visit, the
thing to collect lying there or carried by someone there. When every objective is done it is the
quest's giver, to turn it in. `dir` is the first step of the way there (None when already there).
"""
from collections import deque

MAX_ROOMS = 600          # how far the search walks (a zone or two around the player)


def _words(s):
    return set(str(s or '').lower().replace(',', ' ').split())


def _mob_matches(ch, target):
    """A creature that answers to `target`: its vnum, or a word of its name."""
    if getattr(ch, 'is_player', False) or hasattr(ch, 'account_name'):
        return False
    if getattr(ch, 'hp', 1) <= 0:
        return False
    t = str(target or '').strip().lower()
    if not t:
        return False
    if t.isdigit():
        return str(getattr(ch, 'vnum', '')) == t
    names = _words(getattr(ch, 'name', '')) | _words(getattr(ch, 'short_desc', '')) | _words(getattr(ch, 'keywords', ''))
    return t in names or any(w.rstrip('s') == t.rstrip('s') for w in names)


def _item_here(room, vnum):
    for it in getattr(room, 'items', None) or getattr(room, 'objects', None) or []:
        if str(getattr(it, 'vnum', '')) == vnum:
            return True
    for ch in getattr(room, 'characters', None) or []:
        if getattr(ch, 'is_player', False):
            continue
        for it in getattr(ch, 'inventory', None) or []:
            if str(getattr(it, 'vnum', '')) == vnum:
                return True
    return False


def _wanted(room, kind, target):
    """Whether `room` holds what an objective of `kind` wants."""
    t = str(target or '').strip()
    if kind in ('visit', 'explore'):
        return t.isdigit() and getattr(room, 'vnum', None) == int(t)
    if kind in ('kill', 'talk', 'escort'):
        return any(_mob_matches(ch, t) for ch in getattr(room, 'characters', None) or [])
    if kind == 'collect':
        return t.isdigit() and _item_here(room, t)
    return False


def _exits(room):
    for d, e in (getattr(room, 'exits', None) or {}).items():
        if not e:
            continue
        nxt = e.get('room') if isinstance(e, dict) else None
        if nxt is not None:
            yield d, nxt


def find(player, test):
    """The nearest room (walking from the player's) for which test(room) holds: (room, steps,
    first direction), or None."""
    start = getattr(player, 'room', None)
    if start is None:
        return None
    if test(start):
        return start, 0, None
    seen = {id(start)}
    q = deque([(start, 0, None)])
    n = 0
    while q and n < MAX_ROOMS:
        room, steps, first = q.popleft()
        n += 1
        for d, nxt in _exits(room):
            if id(nxt) in seen:
                continue
            seen.add(id(nxt))
            try:
                if not nxt.admits(player):
                    continue
            except Exception:
                pass
            f = first or d
            if test(nxt):
                return nxt, steps + 1, f
            q.append((nxt, steps + 1, f))
    return None


def _giver(quest_id):
    try:
        from quests import QUEST_DEFINITIONS
        return (QUEST_DEFINITIONS.get(quest_id) or {}).get('quest_giver')
    except Exception:
        return None


def _giver_name(player, vnum):
    try:
        proto = player.world.mob_prototypes.get(int(vnum))
    except Exception:
        proto = None
    if not proto:
        return None
    name = proto.get('short_desc') if isinstance(proto, dict) else getattr(proto, 'short_desc', None)
    return name or (proto.get('name') if isinstance(proto, dict) else getattr(proto, 'name', None))


def guide_block(player):
    """The tracker block for the player's first unfinished ordinary quest (None: none)."""
    quests = [q for q in getattr(player, 'active_quests', None) or [] if q.objectives]
    if not quests:
        return None
    q = next((q for q in quests if not q.is_complete()), quests[0])
    objs = q.objectives
    current = next((o for o in objs if not o.completed), None)
    b = {'id': q.quest_id, 'name': q.name, 'kind': 'quest',
         'stage': (objs.index(current) + 1) if current else len(objs), 'of': len(objs),
         'title': current.description if current else 'Return to the one who gave you this quest',
         'objectives': [{'text': o.description, 'have': o.current, 'need': o.required, 'done': bool(o.completed)} for o in objs],
         'party': []}
    if current is not None:
        hit = find(player, lambda r: _wanted(r, current.type, current.target))
    else:
        giver = _giver(q.quest_id)
        hit = find(player, lambda r: _wanted(r, 'talk', giver)) if giver else None
        name = _giver_name(player, giver)
        if name:
            b['title'] = f'Return to {name}'
    if hit:
        room, steps, first = hit
        b['where'] = {'vnum': room.vnum, 'name': room.name, 'steps': steps, 'dir': first}
    return b
