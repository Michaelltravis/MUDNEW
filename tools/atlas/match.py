"""Match the Bedlam atlas to our world.

Works out which atlas area is which of our zones, which atlas room is which of our rooms, the
vnum each atlas room will carry in the game, where each of our zones that is not on the atlas
joins it (through a connector), and where the creatures and items of our rooms that the atlas
has no place for would go. Changes nothing in the game; writes:

  world/atlas/zones.json   every atlas area and every zone of ours, with its status
  world/atlas/rooms.json   every atlas room's pairing and game vnum; our rooms left over
  world/atlas/vnums.json   {atlas id: game vnum}

    python3 tools/atlas/match.py

Rooms are paired in passes, each only among rooms still unpaired, one to one:
  vnum+name   the same vnum and a like name (Midgaard read as Garathorm)
  vnum+exits  the same vnum and at least two exits agreeing with rooms already paired
  name        the same name, once on each side, in an area and zone already linked
  walk        the same way out of a paired pair leads to like-named rooms
  position    the same way out of a paired pair leads to rooms of any name (ours lends its
              vnum, creatures and items; its description only when the names are alike)
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (ATLAS_DIR, COMPASS, OPPOSITE, likeness, load_atlas, load_overrides,  # noqa: E402
                    load_world, norm, write_json)

NEW_BASE = 200000     # an atlas room whose own id is held by a different room of ours: 200000 + id
CONTENT_KEYS = ('mob_resets', 'obj_resets', 'special', 'puzzles', 'hidden_items', 'gathering_nodes',
                'zone_mechanic', 'room_effects', 'mobs')


def has_content(r):
    return any(r.get(k) for k in CONTENT_KEYS)


class Matcher:
    def __init__(self, atlas, zones, rooms, ov):
        self.A, self.areas, self.zones, self.R, self.ov = atlas['rooms'], atlas['areas'], zones, rooms, ov
        self.pair, self.back, self.how = {}, {}, {}
        self.never = {int(a) for a, o in (ov.get('rooms') or {}).items() if o is None}
        self.internal = set(ov.get('internal', []))
        self.similar_pos = {}      # our room in a similar zone -> the atlas room about where it was
        self.mob_proto = {}
        for z in zones.values():
            for k, mob in (z.get('mobs') or {}).items():
                self.mob_proto[int(mob.get('vnum', k))] = mob

    def take(self, a, o, why):
        if a in self.pair or o in self.back or a in self.never:
            return False
        if self.R[o]['_zone'] in self.internal:
            return False
        self.pair[a], self.back[o], self.how[a] = o, a, why
        return True

    # ---------------------------------------------------------------- passes
    def run(self):
        A, R = self.A, self.R
        for a, o in (self.ov.get('rooms') or {}).items():
            if o is not None and int(o) in R and int(a) in A:
                self.take(int(a), int(o), 'override')
        self.by_vnum(0.75)
        self.by_vnum_exits()
        self.by_vnum(0.6, need_exit=True)
        self.banned = set()
        for _ in range(2):
            self.link()
            self.prune()
            self.by_name()
            self.walk(min_like=0.5, why='walk')
        self.link()
        self.prune()
        self.walk(min_like=0.0, why='position')
        self.link()
        self.prune()

    def by_vnum(self, min_like, need_exit=False):
        A, R = self.A, self.R
        for a in A:
            if a in R and a not in self.pair and a not in self.back and likeness(A[a]['name'], R[a]['_name']) >= min_like:
                if need_exit and not any(R[a]['_exits'].get(d) is not None and self.pair.get(ta) == R[a]['_exits'][d]
                                         for d, ta in A[a]['exits'].items()):
                    continue
                self.take(a, a, 'vnum+name')

    def by_vnum_exits(self):
        A, R = self.A, self.R
        changed = True
        while changed:
            changed = False
            for a in A:
                if a in self.pair or a not in R or a in self.back:
                    continue
                agree = sum(1 for d, ta in A[a]['exits'].items()
                            if R[a]['_exits'].get(d) is not None and self.pair.get(ta) == R[a]['_exits'][d])
                if agree >= 2 or (agree == 1 and len(A[a]['exits']) == 1):
                    changed |= self.take(a, a, 'vnum+exits')

    def drop(self, a):
        o = self.pair.pop(a)
        self.back.pop(o, None)
        self.how.pop(a, None)

    def prune(self):
        """A link with no pair alike in name is a coincidence of numbering: it is dropped with all
        its pairs. Inside a link, a pair of the same vnum whose names are only loosely alike
        stays only when an exit agrees. A pair outside any link stays only when it is the same
        room for certain (the same vnum and name: the Great Field beside the city)."""
        groups = collections.defaultdict(list)
        for a, o in self.pair.items():
            groups[(self.A[a]['area'], self.R[o]['_zone'])].append(a)
        sim = {(int(area), z) for area, zs in (self.ov.get('similar') or {}).items() for z in zs}
        for key, alist in groups.items():
            if key in sim:
                continue
            like = {a: likeness(self.A[a]['name'], self.R[self.pair[a]]['_name']) for a in alist}
            strong = sum(1 for a in alist if self.how[a] in ('vnum+name', 'name', 'override') and like[a] >= 0.8)
            if len(alist) >= 3 and strong < 2:
                self.banned.add(key)
            for a in alist:
                if self.how[a] == 'override':
                    continue
                if key in self.banned:
                    self.drop(a)
                elif key not in self.links:
                    if not (self.how[a] == 'vnum+name' and like[a] >= 0.9):
                        self.drop(a)
        self.links -= self.banned

    def link(self):
        """Atlas areas and our zones that share at least three paired rooms, or many room names,
        (plus the similar pairs the owner named) count as linked; name pairing and walking stay
        inside them."""
        n = collections.Counter((self.A[a]['area'], self.R[o]['_zone']) for a, o in self.pair.items())
        self.links = {k for k, c in n.items() if c >= 3}
        names_a = collections.defaultdict(set)
        names_o = collections.defaultdict(set)
        for a, r in self.A.items():
            names_a[r['area']].add(norm(r['name']))
        for o, r in self.R.items():
            names_o[r['_zone']].add(norm(r['_name']))
        for area, na in names_a.items():
            for z, no in names_o.items():
                shared = len((na & no) - {''})
                if shared >= 5 and shared >= 0.25 * min(len(na), len(no)):
                    self.links.add((area, z))
        for area, zs in (self.ov.get('similar') or {}).items():
            for z in zs:
                self.links.add((int(area), z))
        self.links -= getattr(self, 'banned', set())

    def by_name(self):
        free_a = collections.defaultdict(lambda: collections.defaultdict(list))
        free_o = collections.defaultdict(lambda: collections.defaultdict(list))
        for a, r in self.A.items():
            if a not in self.pair:
                free_a[r['area']][norm(r['name'])].append(a)
        for o, r in self.R.items():
            if o not in self.back:
                free_o[r['_zone']][norm(r['_name'])].append(o)
        for area, z in sorted(self.links):
            for nm, alist in free_a[area].items():
                olist = free_o[z].get(nm)
                if nm and len(alist) == 1 and olist and len(olist) == 1:
                    self.take(alist[0], olist[0], 'name')

    def walk(self, min_like, why):
        A, R = self.A, self.R
        changed = True
        while changed:
            changed = False
            for a, o in list(self.pair.items()):
                for d, ta in A[a]['exits'].items():
                    to = R[o]['_exits'].get(d)
                    if to is None or to not in R or ta in self.pair or to in self.back:
                        continue
                    if (A[ta]['area'], R[to]['_zone']) not in self.links:
                        continue
                    like = likeness(A[ta]['name'], R[to]['_name'])
                    rev = A[ta]['exits'].get(OPPOSITE[d]) == a and R[to]['_exits'].get(OPPOSITE[d]) == o
                    if like >= min_like or (min_like > 0 and like >= 0.3 and rev):
                        changed |= self.take(ta, to, why)


# -------------------------------------------------------------------- statuses
def area_table(m, atlas, ov):
    sim = {int(a): zs for a, zs in (ov.get('similar') or {}).items()}
    conn, open_too = set(ov.get('connectors', [])), set(ov.get('open_too', []))
    by_area = collections.defaultdict(list)
    for v, r in m.A.items():
        by_area[r['area']].append(v)
    out = {}
    for area, vs in sorted(by_area.items()):
        paired = [v for v in vs if v in m.pair]
        zc = collections.Counter(m.R[m.pair[v]]['_zone'] for v in paired)
        zones = [z for z, c in zc.most_common() if c >= 3] or (sim.get(area) or [])
        if area in sim:
            status = 'similar'
            zones = list(dict.fromkeys(list(sim[area]) + zones))
        elif len(paired) >= 3:
            status = 'matched'
        else:
            status = 'atlas-only'
        out[area] = {
            'name': m.areas[area]['name'], 'builder': m.areas[area]['builder'], 'status': status,
            'our_zones': zones, 'rooms': len(vs), 'paired': len(paired), 'connector': area in conn,
            'open': status in ('matched', 'similar') or area in conn or area in open_too,
        }
    return out


def zone_table(m, areas, ov):
    sim_z = {z for zs in (ov.get('similar') or {}).values() for z in zs}
    out = {}
    for z, zone in sorted(m.zones.items()):
        vs = [v for v, r in m.R.items() if r['_zone'] == z]
        paired = [v for v in vs if v in m.back]
        ac = collections.Counter(m.A[m.back[v]]['area'] for v in paired)
        if z in m.internal:
            status = 'internal'
        elif z in sim_z:
            status = 'similar'
        elif paired and len(paired) >= max(3, len(vs) * 0.25):
            status = 'matched'
        else:
            status = 'ours-only'
        out[z] = {'name': zone['name'], 'file': zone['_file'], 'status': status, 'rooms': len(vs),
                  'paired': len(paired), 'atlas_areas': [a for a, _ in ac.most_common()]}
    return out


# -------------------------------------------------------------------- vnums
def plan_vnums(m, areas, zones, similar_moves):
    """matched rooms keep our vnum; a similar zone's room that takes over one of ours keeps that
    one's; the rest use their atlas id when free, else NEW_BASE + id."""
    kept_ours = {v for v, r in m.R.items() if zones[r['_zone']]['status'] in ('ours-only', 'internal')}
    kept_ours |= set(m.back)
    taken = set(kept_ours)
    game = {}
    for a, o in m.pair.items():
        game[a] = o
    for o, a in similar_moves.items():
        if a not in game and o not in taken | set(game.values()):
            game[a] = o
            taken.add(o)
    taken |= set(game.values())
    # our rooms that leave the map (orphans) keep their numbers reserved too
    taken |= set(m.R)
    for a in sorted(m.A):
        if a in game:
            continue
        game[a] = a if a not in taken else NEW_BASE + a
        taken.add(game[a])
    return game


# -------------------------------------------------------------------- similar zones
def bfs_depth(adj, starts):
    depth, q = {}, collections.deque()
    for s in starts:
        depth[s] = 0
        q.append(s)
    while q:
        x = q.popleft()
        for y in adj.get(x, ()):
            if y not in depth:
                depth[y] = depth[x] + 1
                q.append(y)
    return depth


def similar_moves(m, areas, zones, ov):
    """For each similar zone: our rooms that hold creatures, items or puzzles, each set on the
    atlas room at about the same depth from the way in (the deepest ones on the deepest rooms:
    where a boss waits). One atlas room takes one of ours where it can."""
    moves = {}
    sim = {int(a): zs for a, zs in (ov.get('similar') or {}).items()}
    by_zone = collections.defaultdict(list)
    for area, zs in sim.items():
        for z in zs:
            by_zone[z].append(area)
    for z, alist in by_zone.items():
        ours = [v for v, r in m.R.items() if r['_zone'] == z]
        adj_o = {v: [t for t in m.R[v]['_exits'].values() if t in m.R and m.R[t]['_zone'] == z] for v in ours}
        entry_o = [v for v in ours if any(t in m.R and m.R[t]['_zone'] != z for t in list(m.R[v]['_exits'].values()) + list(m.R[v]['_named_exits'].values()))] or [min(ours)]
        atl = [v for v, r in m.A.items() if r['area'] in alist]
        adj_a = {v: [t for t in m.A[v]['exits'].values() if t in m.A and m.A[t]['area'] in alist] for v in atl}
        entry_a = [v for v in atl if any(m.A[t]['area'] not in alist for t in m.A[v]['exits'].values() if t in m.A)] or [min(atl)]
        do = bfs_depth(adj_o, entry_o)
        da = bfs_depth(adj_a, entry_a)
        if not da:
            continue
        maxo = max(do.values()) or 1
        maxa = max(da.values()) or 1
        free = [v for v in atl if v not in m.pair]
        used = set()
        for v in sorted((v for v in ours if v not in m.back and has_content(m.R[v])), key=lambda v: do.get(v, maxo)):
            want = do.get(v, maxo) / maxo * maxa
            pool = [a for a in free if a not in used] or free
            best = min(pool, key=lambda a: (abs(da.get(a, maxa) - want), a))
            moves[v] = best
            used.add(best)
        for v in ours:
            if v not in m.back:
                want = do.get(v, maxo) / maxo * maxa
                m.similar_pos[v] = min(atl, key=lambda a: (abs(da.get(a, maxa) - want), a))
    return moves


# -------------------------------------------------------------------- orphans
SERVICE = {'shopkeeper', 'guildmaster', 'trainer', 'auctioneer', 'stable_master', 'arena_master',
           'real_estate', 'sage_aldric', 'banker', 'innkeeper', 'healer', 'postmaster'}
PATH_WORDS = re.compile(r'\b(trail|path|road|lane|laneway|foothills?|valley|clearing|plains?|forest|woods?|'
                        r'tunnel|street|track|way|bridge|river|field)\b', re.I)
SERVICE_WORDS = re.compile(r'\b(inn|shop|shoppe|store|guild|bank|tavern|bar|temple|sanctum|vault|academy|'
                           r'school|smith|armou?ry|stables?|market|post|order|chapel|library)\b', re.I)


def services(m, r):
    """The service NPCs set in a room (shopkeepers, guildmasters, trainers...)."""
    found = []
    for reset in r.get('mob_resets') or []:
        mob = m.mob_proto.get(reset.get('vnum') if isinstance(reset, dict) else reset)
        sp = mob.get('special') if mob else None
        if isinstance(sp, str) and sp in SERVICE:
            found.append(sp)
    return found


def orphan_clusters(m, zones, game, placer):
    """Our rooms in matched zones that the atlas has no room for, in connected clusters. A cluster
    with a service (a shop, a guild, an inn, a bank) or three rooms of creatures and items is kept
    as an annex: hung off a free side of the atlas room beside it. A smaller one with creatures or
    items gives them to that atlas room. Bare path rooms are dropped: the atlas has its own way
    there."""
    orph = {v for v, r in m.R.items() if v not in m.back and zones[r['_zone']]['status'] == 'matched'}
    seen, out, cid = set(), {}, 0
    for v0 in sorted(orph):
        if v0 in seen:
            continue
        cid += 1
        comp, q = [], collections.deque([v0])
        seen.add(v0)
        while q:
            x = q.popleft()
            comp.append(x)
            for t in list(m.R[x]['_exits'].values()) + list(m.R[x]['_named_exits'].values()):
                if t in orph and t not in seen and m.R[t]['_zone'] == m.R[v0]['_zone']:
                    seen.add(t)
                    q.append(t)
        # the paired room beside it, and the side the cluster lies on
        anchor = None
        for x in comp:
            for d, t in m.R[x]['_exits'].items():
                if t in m.back:
                    anchor = (m.back[t], OPPOSITE[d], x)
                    break
            if anchor:
                break
        if anchor is None:          # joined to the paired world only by a named way or not at all
            for x in comp:
                for d, t in m.R[x]['_named_exits'].items():
                    if t in m.back:
                        anchor = (m.back[t], None, x)
                        break
                if anchor:
                    break
        svc = sorted({sv for x in comp for sv in services(m, m.R[x])})
        content = [x for x in comp if has_content(m.R[x])]
        named = [x for x in comp if SERVICE_WORDS.search(m.R[x]['_name'])]
        pathlike = sum(1 for x in comp if PATH_WORDS.search(m.R[x]['_name'])) * 2 > len(comp)
        if svc or (named and content) or (len(content) >= 3 and not pathlike):
            kind = 'annex'
        elif content:
            kind = 'move'
        else:
            kind = 'drop'
        prop = {'kind': kind, 'rooms': comp, 'services': svc}
        if anchor is None and kind != 'drop':
            prop['kind'] = 'unplaced'
        if anchor:
            a, d, entry = anchor
            prop['beside_atlas'] = a
            prop['beside_game'] = game.get(a)
            if kind == 'annex':
                spot = placer.place(a, d, m.R[entry]['_exits'], from_vnum=None, prefer=placer.near_areas(a))
                if spot:
                    prop.update(attach_atlas=spot[0], attach_game=game.get(spot[0]), dir=spot[1], entry=entry)
                else:
                    prop['kind'] = 'move'
        for x in comp:
            out[x] = {'zone': m.R[x]['_zone'], 'name': m.R[x]['_name'], 'cluster': cid,
                      'content': has_content(m.R[x]), 'services': services(m, m.R[x])}
        out.setdefault('_clusters', {})[cid] = prop
    clusters = out.pop('_clusters', {})
    return out, clusters


# -------------------------------------------------------------------- hookups
class Placer:
    """Finds free sides on the open atlas map for what we add to it (our zones' ways in, our
    annex rooms), so that no side is given twice and the room of ours on the other end has the
    opposite side free."""

    def __init__(self, m, areas):
        self.m = m
        self.open = {a for a, v in areas.items() if v['open']}
        self.conn = {a for a, v in areas.items() if v['connector']}
        self.city = {a for a, v in areas.items() if v['name'].startswith('Garathorm')}
        self.added = collections.defaultdict(set)

    def free(self, a, d):
        return d not in self.m.A[a]['exits'] and d not in self.added[a]

    def near_areas(self, a):
        return {self.m.A[a]['area']}

    def place(self, a0, want, inside_exits, from_vnum=None, prefer=(), radius=None, strict=False):
        """(atlas room, side) nearest a0 over open atlas rooms: a preferred area's room first,
        the wanted side first; the room of ours needs the opposite side free (or already
        pointing back the old way)."""
        sides = ([want] if want in ('north', 'east', 'south', 'west', 'up', 'down') else []) + \
                [d for d in ('north', 'east', 'south', 'west') if d != want]

        def back_ok(d):
            back = inside_exits.get(OPPOSITE[d])
            return back is None or back == from_vnum

        # first a room out of doors with nothing added yet, then any
        for picky in (True, False):
            for pass_prefer in ((True,) if strict else (True, False) if prefer else (False,)):
                hit = self._search(a0, sides, back_ok, prefer if pass_prefer else None, radius, picky)
                if hit:
                    self.added[hit[0]].add(hit[1])
                    return hit
        return None

    def _search(self, a0, sides, back_ok, prefer, radius, picky):
        seen, q = {a0: 0}, collections.deque([a0])
        while q:
            x = q.popleft()
            if radius is not None and seen[x] > radius:
                continue
            area = self.m.A[x]['area']
            if area in self.open and (prefer is None or area in prefer) and \
                    (not picky or (self.m.A[x]['terrain'] != 'inside' and not self.added[x])):
                for d in sides:
                    if self.free(x, d) and back_ok(d):
                        return x, d
            for t in self.m.A[x]['exits'].values():
                if t in self.m.A and t not in seen and self.m.A[t]['area'] in self.open:
                    seen[t] = seen[x] + 1
                    q.append(t)
        return None


def hookups(m, zones, game, ov, placer):
    """Each zone of ours that the atlas lacks joins the atlas world once for each way it is
    entered from a zone that the atlas has. Kept at the same room and side when the atlas leaves
    that side free; otherwise moved to the nearest connector room with a free side (the city's
    own rooms for the zones kept beside it). Zones entered only from other zones of ours hang
    off those as they do now."""
    only = {z for z, v in zones.items() if v['status'] == 'ours-only'}
    annex = set(ov.get('city_annex', []))
    manual = {int(z): h for z, h in (ov.get('hookups') or {}).items()}
    out = {}
    for z in sorted(only):
        if z in manual:
            h = manual[z]
            out[z] = [{'how': 'owner', 'atlas_room': h['atlas_room'], 'game_room': game.get(h['atlas_room']),
                       'dir': h['dir'], 'zone_room': h.get('zone_room')}]
            placer.added[h['atlas_room']].add(h['dir'])
            continue
        props = []
        entries = [(v, d, t) for v, r in m.R.items() if r['_zone'] not in only and r['_zone'] not in m.internal
                   for d, t in list(r['_exits'].items()) + list(r['_named_exits'].items())
                   if t in m.R and m.R[t]['_zone'] == z]
        has_compass = any(d in COMPASS for _, d, _ in entries)
        for v, d, t in entries:
            if True:
                if d not in COMPASS and has_compass:
                    props.append({'how': 'named way dropped', 'from': v, 'dir': d, 'zone_room': t, 'was': f'{v} {d}'})
                    continue
                a = m.back.get(v)
                inside = m.R[t]['_exits']
                if a is not None and d in COMPASS and m.A[a]['area'] in placer.open and placer.free(a, d) \
                        and (inside.get(OPPOSITE[d]) in (None, v)):
                    placer.added[a].add(d)
                    props.append({'how': 'same place', 'from': v, 'atlas_room': a, 'game_room': game[a], 'dir': d,
                                  'zone_room': t, 'was': f'{v} {d}'})
                    continue
                start = a if a is not None else m.similar_pos.get(v)
                if start is None:            # the room of ours it hung off is not on the atlas
                    seen, q = {v}, collections.deque([v])
                    while q and start is None:
                        x = q.popleft()
                        for y in list(m.R[x]['_exits'].values()) + list(m.R[x]['_named_exits'].values()):
                            if y in m.R and y not in seen:
                                if y in m.back:
                                    start = m.back[y]
                                    break
                                seen.add(y)
                                q.append(y)
                spot = None
                if start:
                    # a dungeon's side door stays in its dungeon: near the old neighbour first
                    spot = placer.place(start, d, inside, from_vnum=v, prefer={m.A[start]['area']}, radius=4, strict=True)
                    if not spot:
                        spot = placer.place(start, d, inside, from_vnum=v,
                                            prefer=placer.city if z in annex else placer.conn)
                if not spot:
                    props.append({'how': 'unplaced', 'from': v, 'dir': d, 'zone_room': t, 'was': f'{v} {d}'})
                    continue
                props.append({'how': 'moved' if d in COMPASS else 'replaces a named way', 'from': v,
                              'atlas_room': spot[0], 'game_room': game[spot[0]], 'dir': spot[1], 'zone_room': t,
                              'was': f'{v} {d}'})
        out[z] = props
    return out


def main():
    atlas = load_atlas()
    zones, rooms = load_world()
    ov = load_overrides()
    m = Matcher(atlas, zones, rooms, ov)
    m.run()
    areas = area_table(m, atlas, ov)
    zt = zone_table(m, areas, ov)
    moves = similar_moves(m, areas, zt, ov)
    game = plan_vnums(m, areas, zt, moves)
    placer = Placer(m, areas)
    hooks = hookups(m, zt, game, ov, placer)
    orphans, clusters = orphan_clusters(m, zt, game, placer)

    room_rows = {}
    for a, r in sorted(m.A.items()):
        o = m.pair.get(a)
        row = {'area': r['area'], 'name': r['name'], 'game': game[a]}
        if o is not None:
            row.update(ours=o, how=m.how[a], our_name=m.R[o]['_name'], like=round(likeness(r['name'], m.R[o]['_name']), 2))
        else:
            took = [v for v, t in moves.items() if t == a]
            if took:
                row.update(takes_content_of=took)
        room_rows[a] = row
    write_json(os.path.join(ATLAS_DIR, 'zones.json'),
               {'_about': 'Generated by tools/atlas/match.py from the atlas, our zones and world/atlas/overrides.json. Do not edit: edit the overrides.',
                'areas': areas, 'zones': zt, 'hookups': hooks}, rows=('areas', 'zones', 'hookups'))
    write_json(os.path.join(ATLAS_DIR, 'rooms.json'),
               {'_about': 'Generated by tools/atlas/match.py. atlas: every atlas room, its game vnum and our room it pairs with (how: the pass that paired them). orphans: our rooms in matched zones the atlas has no room for, and where their content would go. similar_moves: rooms of our similar zones with creatures or items, and the atlas room each moves onto.',
                'atlas': room_rows, 'orphans': orphans, 'orphan_clusters': clusters, 'similar_moves': moves},
               rows=('atlas', 'orphans', 'orphan_clusters', 'similar_moves'))
    write_json(os.path.join(ATLAS_DIR, 'vnums.json'), {str(a): v for a, v in sorted(game.items())})

    hows = collections.Counter(m.how.values())
    print(f"paired {len(m.pair)} of {len(m.A)} atlas rooms with {len(rooms)} of ours: " + ', '.join(f'{k} {v}' for k, v in hows.most_common()))
    st = collections.Counter(v['status'] for v in areas.values())
    print('atlas areas: ' + ', '.join(f'{k} {v}' for k, v in st.items()) + f"; open {sum(v['open'] for v in areas.values())}")
    zs = collections.Counter(v['status'] for v in zt.values())
    print('our zones: ' + ', '.join(f'{k} {v}' for k, v in zs.items()))
    kinds = collections.Counter(c['kind'] for c in clusters.values())
    print(f"orphans {len(orphans)} in {len(clusters)} clusters: " + ', '.join(f'{k} {v}' for k, v in kinds.items()) + '; '
          f"{sum(1 for o in orphans.values() if o['content'])} with creatures or items; "
          f"similar-zone rooms moved {len(moves)}; hookups {sum(len(h) for h in hooks.values())} "
          f"({sum(1 for h in hooks.values() for x in h if x['how'] == 'unplaced')} unplaced)")
    renum = sum(1 for a, g in game.items() if g >= NEW_BASE)
    print(f'atlas rooms renumbered past collisions: {renum}')


if __name__ == '__main__':
    main()
