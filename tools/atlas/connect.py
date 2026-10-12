"""The connection pass: every open room must be reachable from the temple, and you must be able to
walk back from it. Works on the world being built (tools/atlas/build_world.py): {vnum: room dict}
with game vnums, and which zones are sealed.

Excepted: rooms flagged deathtrap/death and the rooms beyond a one-way exit into them (they are
meant to kill). Each round works out what the temple reaches and what reaches the temple over
open rooms, then joins what is cut off, in this order of preference:
  1. our own old way (from the world before the re-lay) between rooms that both still exist,
     when the side is free; when it isn't, the atlas's own way out of that land walked back,
     and failing that another free side;
  2. the way back along a one-way exit, when its opposite side is free;
  3. water: a river whose current runs one way flows both ways (you're in a boat anyway);
  4. a room one cell away on the atlas map (same zone, same level), both sides free.
Whatever is still cut off is reported. Every exit added is recorded with its reason.
"""
import collections

OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}
COMPASS = ('north', 'east', 'south', 'west', 'up', 'down')
STEP = {'north': (0, 1), 'south': (0, -1), 'east': (1, 0), 'west': (-1, 0)}     # atlas axes: north is +y
WATER = ('water_swim', 'water_noswim', 'water_surface')
DEATH = ('deathtrap', 'death')


def _to(ex):
    return ex.get('to_room') if isinstance(ex, dict) else None


def graph(rooms, open_vnums):
    fwd, rev = collections.defaultdict(set), collections.defaultdict(set)
    for v in open_vnums:
        for d, ex in (rooms[v].get('exits') or {}).items():
            t = _to(ex)
            if t in open_vnums:
                fwd[v].add(t)
                rev[t].add(v)
    return fwd, rev


def bfs(start, g):
    seen, q = {start}, collections.deque([start])
    while q:
        x = q.popleft()
        for y in g.get(x, ()):
            if y not in seen:
                seen.add(y)
                q.append(y)
    return seen


def death_region(rooms, open_vnums):
    """Death-trap rooms, and the rooms you can reach only by going through one."""
    deadly = {v for v in open_vnums if any(f in DEATH for f in (rooms[v].get('flags') or []))}
    return deadly


def _way_out(rooms, u, unreach, reach, fwd, free):
    """The atlas's own way out of the land cut off around u: the nearest room on foot from u (over
    rooms the temple doesn't reach) with a compass exit into a room it does reach, whose opposite
    side there is free. Returns (that room, the way out, the reached room), or None."""
    seen, q = {u}, collections.deque([u])
    while q:
        y = q.popleft()
        for d in COMPASS:
            t = _to((rooms[y].get('exits') or {}).get(d))
            if t in reach and free(t, OPP[d]):
                return y, d, t
        for t in sorted(fwd.get(y, ())):
            if t in unreach and t not in seen:
                seen.add(t)
                q.append(t)
    return None


def add_exit(rooms, a, d, b, why, log, name=None):
    rooms[a].setdefault('exits', {})[d] = {'to_room': b, 'description': f"To the {d} lies {name or rooms[b].get('name', 'somewhere')}."}
    log.append({'from': a, 'dir': d, 'to': b, 'why': why})


def connect(rooms, open_vnums, old_rooms, renumber=None, temple=3001, max_rounds=60):
    """Join what is cut off; returns (added, still_cut_off). `renumber` names the room standing in
    for each old room that is gone (a similar zone's room for ours it replaced)."""
    log = []
    renumber = renumber or {}

    def stand(t):
        return t if t in rooms else renumber.get(t)
    deadly = death_region(rooms, open_vnums)
    for _ in range(max_rounds):
        fwd, rev = graph(rooms, open_vnums)
        reach = bfs(temple, fwd)
        back = bfs(temple, rev)
        unreach = {v for v in open_vnums - reach if v not in deadly}
        trapped = {v for v in reach - back if v not in deadly}
        if not unreach and not trapped:
            return log, set()
        before = len(log)

        def free(v, d):
            return d not in (rooms[v].get('exits') or {})

        # 1. our own old ways (a room that was replaced counts as the one standing in for it). One
        #    that can't keep its own direction gives way to the atlas's own way out of that land,
        #    walked back (the gods' rooms lie up from the temple because the atlas goes down from
        #    them to it); failing that, it takes a free side, up and down first (an old named way,
        #    the arena's or a portal's, always does)
        for u in sorted(unreach):
            done = False
            for x, r in old_rooms.items():
                xs = stand(x)
                if xs is None or xs not in reach or xs not in rooms:
                    continue
                for d, ex in (r.get('exits') or {}).items():
                    if stand(_to(ex)) != u:
                        continue
                    if d in COMPASS and free(xs, d) and free(u, OPP[d]):
                        add_exit(rooms, xs, d, u, 'our old way in', log)
                        add_exit(rooms, u, OPP[d], xs, 'our old way in (back)', log)
                        done = True
                    elif d in COMPASS:
                        out = _way_out(rooms, u, unreach, reach, fwd, free)
                        if out:
                            y, dy, xo = out
                            add_exit(rooms, xo, OPP[dy], y, 'the atlas way out, walked back', log)
                            done = True
                    if not done:
                        for dd in [k for k in ('up', 'down', 'north', 'east', 'south', 'west') if k != d]:
                            if free(xs, dd) and free(u, OPP[dd]):
                                add_exit(rooms, xs, dd, u, 'our old way in', log)
                                add_exit(rooms, u, OPP[dd], xs, 'our old way in (back)', log)
                                done = True
                                break
                    if done:
                        break
                if done:
                    break
        for y in sorted(trapped):
            r = old_rooms.get(y)
            if not r:
                continue
            for d, ex in (r.get('exits') or {}).items():
                t = _to(ex)
                if d in COMPASS and t in back and t in rooms and free(y, d):
                    add_exit(rooms, y, d, t, 'our old way out', log)
                    break
        if len(log) > before:
            continue
        # 2. back along a one-way way in
        for y in sorted(trapped | unreach):
            for x in sorted(rev.get(y, ())):
                if x in back:
                    for d, ex in (rooms[x].get('exits') or {}).items():
                        if _to(ex) == y and d in COMPASS and free(y, OPP[d]):
                            add_exit(rooms, y, OPP[d], x, 'the way back', log)
                            break
                    else:
                        continue
                    break
        if len(log) > before:
            continue
        # 3. a river flows both ways
        for y in sorted(trapped):
            if rooms[y].get('sector_type') not in WATER:
                continue
            for x in sorted(rev.get(y, ())):
                if rooms[x].get('sector_type') in WATER:
                    for d, ex in (rooms[x].get('exits') or {}).items():
                        if _to(ex) == y and d in COMPASS and free(y, OPP[d]):
                            add_exit(rooms, y, OPP[d], x, 'upstream', log)
        if len(log) > before:
            continue
        # 4. a room nearby on the map: one cell away, or up to three along a straight line with
        #    nothing between (the atlas draws some rooms spaced out: the pits of Minos)
        cells = {}
        for v in open_vnums:
            m = rooms[v].get('map')
            if m:
                cells[(rooms[v].get('_zone'), m['x'], m['y'], m.get('z', 0))] = v
        for y in sorted(trapped | unreach):
            m = rooms[y].get('map')
            if not m:
                continue
            want = back if y in trapped else reach
            done = False
            for dist in (1, 2, 3):
                for d, (dx, dy) in STEP.items():
                    key = (rooms[y].get('_zone'), m['x'] + dx * dist, m['y'] + dy * dist, m.get('z', 0))
                    n = cells.get(key)
                    between = any(cells.get((key[0], m['x'] + dx * k, m['y'] + dy * k, key[3])) for k in range(1, dist))
                    if n is not None and not between and n in want and free(y, d) and free(n, OPP[d]):
                        add_exit(rooms, y, d, n, 'map neighbour', log)
                        add_exit(rooms, n, OPP[d], y, 'map neighbour', log)
                        done = True
                        break
                if done:
                    break
        if len(log) > before:
            continue
        # 5. a trap with its natural way back taken: back to where you came in, on any free side
        for y in sorted(trapped):
            for x in sorted(rev.get(y, ())):
                if x not in back:
                    continue
                d_in = next((d for d, ex in (rooms[x].get('exits') or {}).items() if _to(ex) == y), None)
                sides = ([OPP[d_in]] if d_in in OPP else []) + ['up', 'down', 'north', 'east', 'south', 'west']
                dd = next((k for k in sides if free(y, k)), None)
                if dd:
                    add_exit(rooms, y, dd, x, 'a way back out', log)
                    break
            if len(log) > before:
                break
        if len(log) == before:
            return log, unreach | trapped
    fwd, rev = graph(rooms, open_vnums)
    reach, back = bfs(temple, fwd), bfs(temple, rev)
    return log, {v for v in (open_vnums - reach) | (reach - back) if v not in deadly}
