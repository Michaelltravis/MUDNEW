"""Open ground (the owner: "the world should feel more open world like").

A MUD's rooms join only where an exit was written, so a forest is a set of corridors even
where /play draws the rooms side by side. In a zone opened here, two outdoor rooms that sit
side by side on the zone map (map_system.build_zonemap) are joined both ways, as if by an
exit, so the country runs on: walking, creatures wandering, reaching into the next room and
the 3D client's shared open sides (roomgen.js) all follow the new ways at once.

Never a way the zone did not already have in another form: two rooms are joined only when
one can already walk from one to the other without passing a door (a locked gate, its key
and its keeper keep their meaning) and both ways back again (a one-way drop stays one way).
Water, rooms under a roof, death traps, private and immortal rooms keep their walls.
Applied at world load, after the doors and rites are in place (world.World.load)."""
import logging

logger = logging.getLogger(__name__)

# the zones opened: every zone (owner: "finish all the other zones"), save any listed here as
# kept to their written ways (None in WILD_ZONES: all of them)
WILD_ZONES = None
CLOSED_ZONES = {12}        # the God Rooms
LAND = {'forest', 'darkforest', 'field', 'hills', 'desert', 'snow', 'swamp', 'stones', 'shore'}
WALLED_FLAGS = {'death', 'imm_only', 'private', 'tunnel', 'indoors', 'no_wild', 'godroom'}
STEP = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
BACK = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def _target(ed):
    if not isinstance(ed, dict):
        return None
    t = ed.get('to_room')
    if t is None:
        t = getattr(ed.get('room'), 'vnum', None)
    return t


def open_ground(room):
    """Whether a room is outdoor land that may share its sides."""
    look = getattr(room, 'look', None) or getattr(room, 'sector_type', '') or ''
    flags = set(getattr(room, 'flags', None) or ())
    return look in LAND and not (flags & WALLED_FLAGS)


def _components(rooms):
    """vnum -> component id over the ways that need no door and lead back."""
    comp, n = {}, 0
    for start in rooms:
        if start in comp:
            continue
        n += 1
        comp[start] = n
        stack = [start]
        while stack:
            v = stack.pop()
            for ed in (rooms[v].exits or {}).values():
                t = _target(ed)
                if t not in rooms or t in comp or ed.get('hidden') or ed.get('door'):
                    continue
                if not any(_target(b) == v and not b.get('door') and not b.get('hidden')
                           for b in (rooms[t].exits or {}).values() if isinstance(b, dict)):
                    continue
                comp[t] = n
                stack.append(t)
    return comp


def join_zone(world, zone_num):
    """Join the side-by-side outdoor rooms of one zone. Returns the joins made [(vnum, dir, vnum)]."""
    import map_system
    zm = map_system.build_zonemap(world, zone_num)
    if not zm:
        return []
    rooms = {r['vnum']: world.rooms[r['vnum']] for r in zm['rooms'] if r['vnum'] in world.rooms}
    entry = {r['vnum']: r for r in zm['rooms']}
    at = {(tuple(r['cell']), r.get('level', 0)): r['vnum'] for r in zm['rooms']}
    comp = _components(rooms)
    zm['wild'] = True           # (the client lets the land run on past the zone's edge)
    made = []
    for v, room in rooms.items():
        if not open_ground(room):
            continue
        cx, cy = entry[v]['cell']
        lv = entry[v].get('level', 0)
        for d, (dx, dy) in STEP.items():
            t = at.get(((cx + dx, cy + dy), lv))
            if t is None or t == v or d in (room.exits or {}):
                continue
            other = rooms[t]
            if not open_ground(other) or BACK[d] in (other.exits or {}) or comp.get(v) != comp.get(t):
                continue
            room.exits = room.exits or {}
            other.exits = other.exits or {}
            room.exits[d] = {'to_room': t, 'room': other, 'wild': True, 'description': ''}
            other.exits[BACK[d]] = {'to_room': v, 'room': room, 'wild': True, 'description': ''}
            # the zone map the client draws (cached, laid out already: the cells do not move)
            entry[v].setdefault('exits', {})[d] = {'to': t, 'kind': 'open', 'wild': True}
            entry[t].setdefault('exits', {})[BACK[d]] = {'to': v, 'kind': 'open', 'wild': True}
            made.append((v, d, t))
    return made


def apply(world):
    total = 0
    zones = getattr(world, 'zones', {})
    for z in sorted(zones if WILD_ZONES is None else WILD_ZONES):
        if z in zones and z not in CLOSED_ZONES:
            total += len(join_zone(world, z))
    if total:
        logger.info(f"open ground: {total} ways between side-by-side outdoor rooms")
    return total
