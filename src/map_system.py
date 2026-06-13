"""
Map rendering and coordinate utilities for Misthollow.
"""

from typing import Dict, Tuple, Set, List, Optional

from config import Config
from affects import AffectManager

DIR_OFFSETS = {
    'north': (0, -1, 0),
    'south': (0, 1, 0),
    'east': (1, 0, 0),
    'west': (-1, 0, 0),
    'up': (0, 0, 1),
    'down': (0, 0, -1),
}

REVERSE_DIR = {
    'north': 'south',
    'south': 'north',
    'east': 'west',
    'west': 'east',
    'up': 'down',
    'down': 'up',
}


def get_room_symbol(room) -> str:
    """Return symbol for a room based on type/flags."""
    if not room:
        return '·'

    flags = set(room.flags) if hasattr(room, 'flags') else set()
    name = room.name.lower() if hasattr(room, 'name') and room.name else ''
    sector = getattr(room, 'sector_type', 'inside')

    # Special overrides
    if 'shop' in flags or 'store' in name or 'shop' in name or 'merchant' in name:
        return '$'
    if 'important' in flags or 'quest' in flags or 'boss' in flags or 'temple' in name or 'castle' in name:
        return '!'

    # Terrain-based
    if sector in ('city', 'inside') or 'indoors' in flags:
        return '□'
    if sector == 'forest':
        return '♣'
    if sector in ('water_swim', 'water_noswim', 'underwater'):
        return '≈'
    if sector in ('mountain', 'hills'):
        return '▲'
    if sector in ('dungeon',) or 'underground' in flags:
        return '▼'

    return '·'


def get_room_icon(room) -> str:
    """Return emoji icon for a room based on type/flags (for web map)."""
    if not room:
        return '❓'

    flags = set(room.flags) if hasattr(room, 'flags') else set()
    name = room.name.lower() if hasattr(room, 'name') and room.name else ''
    sector = getattr(room, 'sector_type', 'inside')

    # Special locations
    if 'deathtrap' in flags:
        return '💀'
    if 'boss' in flags or 'boss' in name:
        return '👹'
    if 'shop' in flags or 'store' in name or 'shop' in name or 'merchant' in name:
        return '🛒'
    if 'bank' in name:
        return '🏦'
    if 'inn' in name or 'tavern' in name:
        return '🍺'
    if 'temple' in name or 'church' in name or 'altar' in name:
        return '⛪'
    if 'castle' in name or 'throne' in name or 'palace' in name:
        return '🏰'
    if 'guild' in name or 'trainer' in name:
        return '📚'
    if 'gate' in name or 'entrance' in name:
        return '🚪'
    if 'important' in flags or 'quest' in flags:
        return '⭐'
    
    # Underground / tunnels (check name before sector)
    if 'sewer' in name or 'drain' in name or 'pipe' in name:
        return '🚰'
    if 'tunnel' in name or 'passage' in name or 'corridor' in name:
        return '🕳️'
    if 'cave' in name or 'cavern' in name or 'grotto' in name:
        return '🦇'
    if 'crypt' in name or 'tomb' in name or 'catacomb' in name:
        return '⚰️'
    if 'mine' in name or 'shaft' in name:
        return '⛏️'

    # Terrain-based
    if sector == 'city':
        return '🏛️'
    if sector == 'inside':
        return '🏠'
    if sector == 'forest':
        return '🌲'
    if sector == 'field':
        return '🌾'
    if sector in ('water_swim', 'water_noswim'):
        return '🌊'
    if sector == 'underwater':
        return '🐠'
    if sector == 'mountain':
        return '⛰️'
    if sector == 'hills':
        return '🏔️'
    if sector == 'dungeon':
        return '🕯️'
    if sector == 'desert':
        return '🏜️'
    if sector == 'swamp':
        return '🐊'
    if sector == 'road':
        return '🛤️'
    if sector == 'sewer':
        return '🚰'
    if sector == 'cave':
        return '🦇'
    if sector == 'tunnel':
        return '🕳️'
    if 'underground' in flags:
        return '🕳️'

    return '📍'


def find_path(rooms: Dict[int, object], start_vnum: int, end_vnum: int, player=None) -> List[int]:
    """Find shortest path between two rooms using BFS. Returns list of vnums."""
    if start_vnum == end_vnum:
        return [start_vnum]
    if start_vnum not in rooms or end_vnum not in rooms:
        return []

    visited = {start_vnum}
    queue = [(start_vnum, [start_vnum])]

    while queue:
        current, path = queue.pop(0)
        room = rooms.get(current)
        if not room:
            continue

        for direction, exit_data in _iter_visible_exits(room, player):
            to_vnum = _get_exit_target_vnum(exit_data)
            if to_vnum is None or to_vnum in visited:
                continue
            if to_vnum not in rooms:
                continue

            new_path = path + [to_vnum]
            if to_vnum == end_vnum:
                return new_path

            visited.add(to_vnum)
            queue.append((to_vnum, new_path))

    return []  # No path found


def _iter_visible_exits(room, player=None):
    if not room:
        return []
    if hasattr(room, 'get_visible_exits'):
        return room.get_visible_exits(player).items()
    return room.exits.items() if hasattr(room, 'exits') else []


def _get_exit_target_vnum(exit_data) -> Optional[int]:
    if not exit_data:
        return None
    if isinstance(exit_data, dict):
        if 'to_room' in exit_data:
            return exit_data.get('to_room')
        to_room = exit_data.get('room')
        return getattr(to_room, 'vnum', None) if to_room else None
    return None


def compute_room_coords(rooms: Dict[int, object], start_vnum: Optional[int], player=None) -> Dict[int, Tuple[int, int, int]]:
    """Assign coordinates to rooms using BFS based on exits.

    Handles multiple components by offsetting each component on the X axis.
    """
    coords: Dict[int, Tuple[int, int, int]] = {}
    if not rooms:
        return coords

    unvisited = set(rooms.keys())
    occupied = set()
    offset_x = 0

    def _zone_num(vnum):
        z = getattr(rooms[vnum], 'zone', None)
        return getattr(z, 'number', None)

    def _place(vnum, coord, dxyz):
        """Claim a grid cell; on collision slide further along the travel
        direction so distinct rooms never stack on one map square."""
        if coord not in occupied:
            coords[vnum] = coord
            occupied.add(coord)
            return coord
        dx, dy, dz = dxyz if dxyz != (0, 0, 0) else (1, 0, 0)
        x, y, z = coord
        for step in range(1, 8):
            cand = (x + dx * step, y + dy * step, z + dz * step)
            if cand not in occupied:
                coords[vnum] = cand
                occupied.add(cand)
                return cand
        coords[vnum] = coord    # give up: overlap beats omission
        return coord

    def bfs(seed_vnum: int, seed_coord: Tuple[int, int, int]):
        from collections import deque
        _place(seed_vnum, seed_coord, (0, 0, 0))
        unvisited.discard(seed_vnum)
        queue = deque([seed_vnum])
        while queue:
            vnum = queue.popleft()
            room = rooms[vnum]
            x, y, z = coords[vnum]
            zone_here = _zone_num(vnum)
            # lay out the local zone before chasing cross-zone links, so a
            # town stays one coherent block on the map instead of being
            # scattered by whichever detour the BFS found first
            same, cross = [], []
            for direction, exit_data in _iter_visible_exits(room, player):
                if direction not in DIR_OFFSETS:
                    continue
                to_vnum = _get_exit_target_vnum(exit_data)
                if to_vnum not in rooms or to_vnum in coords:
                    continue
                (same if _zone_num(to_vnum) == zone_here else cross).append((direction, to_vnum))
            for direction, to_vnum in same + cross:
                if to_vnum in coords:
                    continue
                dx, dy, dz = DIR_OFFSETS[direction]
                _place(to_vnum, (x + dx, y + dy, z + dz), (dx, dy, dz))
                unvisited.discard(to_vnum)
                if _zone_num(to_vnum) == zone_here:
                    queue.appendleft(to_vnum)
                else:
                    queue.append(to_vnum)

    # Start with player's component if available
    if start_vnum in unvisited:
        bfs(start_vnum, (0, 0, 0))
        # Update offset AFTER player's BFS so disconnected components don't overlap
        xs = [c[0] for v, c in coords.items() if v in rooms]
        if xs:
            offset_x = max(xs) + 3

    # Layout remaining components
    while unvisited:
        seed = next(iter(unvisited))
        # Place new component to the right of previous components
        component_offset = (offset_x, 0, 0)
        bfs(seed, component_offset)
        # Update offset based on component bounds
        xs = [c[0] for v, c in coords.items() if v in rooms]
        if xs:
            offset_x = max(xs) + 3

    return coords


def get_frontier_coords(coords: Dict[int, Tuple[int, int, int]], rooms: Dict[int, object], explored: Set[int], player=None) -> list:
    """Returns list of dicts with x, y, z and optional deathtrap flag."""
    frontier_map = {}  # (x,y,z) -> {info}
    occupied_coords = set(coords.values())
    world = player.world if player and hasattr(player, 'world') else None
    for vnum, (x, y, z) in coords.items():
        if vnum not in explored:
            continue
        room = rooms.get(vnum)
        for direction, exit_data in _iter_visible_exits(room, player):
            if direction not in DIR_OFFSETS:
                continue
            to_vnum = _get_exit_target_vnum(exit_data)
            dx, dy, dz = DIR_OFFSETS[direction]
            if not to_vnum or to_vnum not in explored:
                coord = (x + dx, y + dy, z + dz)
                # Skip if an explored room already occupies this coordinate
                if coord in occupied_coords:
                    continue
                # Also skip if coord is already a frontier entry
                if coord not in frontier_map:
                    # Check if the destination is a deathtrap
                    is_deathtrap = False
                    dest_name = None
                    if to_vnum and world:
                        dest_room = world.rooms.get(to_vnum)
                        if dest_room:
                            dest_flags = set(dest_room.flags) if hasattr(dest_room, 'flags') else set()
                            is_deathtrap = 'deathtrap' in dest_flags
                            dest_name = dest_room.name if hasattr(dest_room, 'name') else None
                    # Also check exit description for danger warnings
                    if not is_deathtrap and isinstance(exit_data, dict):
                        desc = exit_data.get('description', '')
                        if 'DANGER' in desc or 'deathtrap' in desc.lower():
                            is_deathtrap = True
                    frontier_map[coord] = {
                        'x': coord[0], 'y': coord[1], 'z': coord[2],
                        'deathtrap': is_deathtrap,
                        'name': dest_name,
                    }
    return list(frontier_map.values())


def render_ascii_map(player, mode: str = 'local', size: int = 11) -> str:
    """Render ASCII map for a player."""
    c = player.config.COLORS
    explored = set(getattr(player, 'explored_rooms', set()))

    # Filter rooms by mode
    rooms: Dict[int, object] = {}
    if mode == 'zone' and player.room and player.room.zone:
        zone_rooms = set(player.room.zone.rooms.keys())
        for vnum in explored:
            if vnum in zone_rooms:
                room = player.world.rooms.get(vnum)
                if room:
                    rooms[vnum] = room
    else:
        for vnum in explored:
            room = player.world.rooms.get(vnum)
            if room:
                rooms[vnum] = room

    if not rooms:
        return f"{c['yellow']}You haven't explored any rooms yet.{c['reset']}"

    start_vnum = player.room.vnum if player.room else None
    coords = compute_room_coords(rooms, start_vnum, player)
    if start_vnum not in coords:
        return f"{c['yellow']}Your current location is unknown to the map.{c['reset']}"

    player_x, player_y, player_z = coords[start_vnum]
    frontier = get_frontier_coords(coords, rooms, explored, player)

    # Determine bounds
    if mode == 'full':
        frontier_pts = [(f['x'], f['y'], f['z']) for f in frontier]
        points = list(coords.values()) + frontier_pts
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
    else:
        radius = size // 2
        min_x = player_x - radius
        max_x = player_x + radius
        min_y = player_y - radius
        max_y = player_y + radius

    # Build grid (rooms at even coordinates, exits in between)
    width = (max_x - min_x) * 2 + 1
    height = (max_y - min_y) * 2 + 1
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    def to_grid(x, y):
        gx = (x - min_x) * 2
        gy = (y - min_y) * 2
        return gx, gy

    # Draw exits and rooms
    for vnum, (x, y, z) in coords.items():
        if z != player_z:
            continue
        if x < min_x or x > max_x or y < min_y or y > max_y:
            continue
        room = rooms.get(vnum)
        gx, gy = to_grid(x, y)
        symbol = get_room_symbol(room)
        if vnum == start_vnum:
            symbol = f"{c['bright_yellow']}@{c['reset']}"
        grid[gy][gx] = symbol

        # Draw exits
        for direction, exit_data in _iter_visible_exits(room, player):
            if direction not in DIR_OFFSETS:
                continue
            to_vnum = _get_exit_target_vnum(exit_data)
            dx, dy, dz = DIR_OFFSETS[direction]
            ex = x + dx
            ey = y + dy
            ez = z + dz
            if ez != player_z:
                # indicate up/down diagonals for explored destinations
                if to_vnum in explored:
                    if direction == 'up':
                        ex_g, ey_g = gx + 1, gy - 1
                        if 0 <= ey_g < height and 0 <= ex_g < width:
                            grid[ey_g][ex_g] = '/'
                    elif direction == 'down':
                        ex_g, ey_g = gx + 1, gy + 1
                        if 0 <= ey_g < height and 0 <= ex_g < width:
                            grid[ey_g][ex_g] = '\\'
                continue

            if ex < min_x or ex > max_x or ey < min_y or ey > max_y:
                continue

            # only draw if explored
            if to_vnum in explored:
                ex_g, ey_g = to_grid(ex, ey)
                mid_x = (gx + ex_g) // 2
                mid_y = (gy + ey_g) // 2
                grid[mid_y][mid_x] = '─' if direction in ('east', 'west') else '│'

    # Draw frontier
    for f in frontier:
        x, y, z = f['x'], f['y'], f['z']
        if z != player_z:
            continue
        if x < min_x or x > max_x or y < min_y or y > max_y:
            continue
        gx, gy = to_grid(x, y)
        if grid[gy][gx] == ' ':
            grid[gy][gx] = '?'

    # Build output
    title = "Explored Map"
    if mode == 'zone' and player.room and player.room.zone:
        title = f"{player.room.zone.name}"

    lines = [f"{c['cyan']}[{title}] (Z={player_z}){c['reset']}"]
    for row in grid:
        lines.append(''.join(row))
    return '\n'.join(lines)


def _exp_thresholds(player):
    """Return (exp floor of current level, exp needed for next level).

    exp is cumulative, so within-level progress is
    (exp - floor) / (next - floor). Mirrors Player.exp_to_level().
    """
    try:
        nxt = player.exp_to_level()
    except Exception:
        return 0, 0
    lvl = getattr(player, 'level', 1)
    if lvl <= 1:
        return 0, nxt
    cfg = player.config
    thr = getattr(cfg, 'HIGH_LEVEL_THRESHOLD', 30)
    prev = lvl - 1
    if prev <= thr:
        floor = int(cfg.BASE_EXP * (cfg.EXP_MULTIPLIER ** (prev - 1)))
    else:
        level_30 = int(cfg.BASE_EXP * (cfg.EXP_MULTIPLIER ** (thr - 1)))
        floor = int(level_30 * (getattr(cfg, 'HIGH_LEVEL_EXP_MULTIPLIER', 1.6) ** (prev - thr)))
    return floor, nxt


def _build_set_by_vnum():
    """vnum -> named-set key, so the client can theme each set piece uniquely."""
    out = {}
    try:
        from sets import NAMED_SETS
        for sid, cfg in NAMED_SETS.items():
            for vnum in cfg.get('pieces', {}):
                out[vnum] = sid
    except Exception:
        pass
    return out


_SET_BY_VNUM = _build_set_by_vnum()


def item_info(item):
    """Compact item payload used for ground items, inventory and equipment:
    enough for the client to draw a real icon and rarity border."""
    vnum = getattr(item, 'vnum', None)
    return {
        'name': getattr(item, 'name', 'something'),
        'short': getattr(item, 'short_desc', '') or getattr(item, 'name', 'something'),
        'type': getattr(item, 'item_type', 'other'),
        'slot': getattr(item, 'wear_slot', None),
        'rarity': getattr(item, 'rarity', 'common'),
        'set_id': getattr(item, 'set_id', None),
        'set_key': _SET_BY_VNUM.get(vnum),
        'level': getattr(item, 'level', 0),
        'affects': getattr(item, 'affects', []) or [],
    }


CLASS_RESOURCE = {
    # class -> (attribute, display name, maximum)
    'warrior': ('momentum', 'Momentum', 10),
    'thief': ('luck_points', 'Luck', 10),
    'assassin': ('intel_points', 'Intel', 10),
    'cleric': ('faith', 'Faith', 10),
    'paladin': ('holy_power', 'Holy Power', 5),
    'ranger': ('focus', 'Focus', 100),
    'necromancer': ('soul_shards', 'Soul Shards', 10),
    'bard': ('inspiration', 'Inspiration', 10),
}


def _class_resource(player):
    """The class's signature combat resource, for the client resource chip."""
    spec = CLASS_RESOURCE.get(str(getattr(player, 'char_class', '')).lower())
    if not spec:
        return None
    attr, label, cap = spec
    return {'name': label, 'value': int(getattr(player, attr, 0) or 0), 'max': cap}


def _worn_aura(player):
    """'legendary' when any legendary piece is worn; 'set' at 4+ pieces of
    one named set - drives the class-colored aura on the world sprite."""
    worn = [it for it in getattr(player, 'equipment', {}).values() if it]
    if any(getattr(it, 'rarity', '') == 'legendary' for it in worn):
        return 'legendary'
    counts = {}
    for it in worn:
        sid = getattr(it, 'set_id', None)
        if sid:
            counts[str(sid)] = counts.get(str(sid), 0) + 1
    if any(c >= 4 for c in counts.values()):
        return 'set'
    return None


def _in_combat(player) -> bool:
    """True only for a LIVE fight: target alive and in the same room.
    Stale fighting references must never wedge graphical clients."""
    f = getattr(player, 'fighting', None)
    if not f:
        return False
    if getattr(f, 'hp', 0) <= 0:
        return False
    room = getattr(player, 'room', None)
    if not room or f not in getattr(room, 'characters', []):
        return False
    return True


def _path_active(player):
    try:
        from paths import PathManager
        if PathManager.lone_wolf_active(player):
            return 'lone_wolf'
        if PathManager.fellowship_active(player):
            return 'fellowship'
    except Exception:
        pass
    return None


# party-frame roles, inferred from class
_GROUP_ROLES = {
    'warrior': 'tank', 'paladin': 'tank',
    'cleric': 'healer', 'bard': 'healer',
    'mage': 'dps', 'necromancer': 'dps', 'thief': 'dps',
    'assassin': 'dps', 'ranger': 'dps',
}
# strongest heal a class can cast on an ally, best first (underscore cast keys)
_HEAL_PRIORITY = ['heal', 'cure_critical', 'cure_serious', 'cure_light', 'lay_on_hands']


def _best_heal_spell(player):
    """The strongest single-target heal the viewer can cast on an ally, or None."""
    known = getattr(player, 'spells', None) or {}
    for key in _HEAL_PRIORITY:
        if key in known:
            return key
    return None


def _fighting_name(entity):
    f = getattr(entity, 'fighting', None)
    if not f or getattr(f, 'hp', 0) <= 0:
        return None
    return getattr(f, 'name', None)


def build_group_block(player) -> Optional[dict]:
    """Roster + live vitals for the player's party, for the UI party frames.

    Included in both map_data and the per-round combat_update so allied
    health/mana/target stay live during a fight. Returns None when solo.
    """
    group = getattr(player, 'group', None)
    roster = list(getattr(group, 'members', [])) if group else [player]
    # gather the player's pets + companions so they ride along in the bar
    minions = []
    try:
        from pets import PetManager
        minions += [(p, 'pet') for p in (PetManager.get_player_pets(player) or [])]
    except Exception:
        pass
    try:
        from companions import CompanionManager
        minions += [(c, 'companion') for c in (CompanionManager.get_player_companions(player) or [])]
    except Exception:
        pass
    # solo with no minions => no party bar
    if len(roster) < 2 and not minions:
        return None

    proom = getattr(player, 'room', None)
    pvnum = getattr(proom, 'vnum', None)
    # map adjacent room vnum -> direction, so split members get a heading
    dir_by_vnum = {}
    for direction, exit_data in _iter_visible_exits(proom, player):
        tv = _get_exit_target_vnum(exit_data)
        if tv is not None and tv not in dir_by_vnum:
            dir_by_vnum[tv] = direction

    members = []
    for m in roster:
        mroom = getattr(m, 'room', None)
        mvnum = getattr(mroom, 'vnum', None)
        same_room = mroom is proom and proom is not None
        cls = str(getattr(m, 'char_class', '') or '').lower()
        max_hp = getattr(m, 'max_hp', 1) or 1
        max_mana = getattr(m, 'max_mana', 1) or 1
        members.append({
            'name': getattr(m, 'name', 'Unknown'),
            'char_class': cls,
            'role': _GROUP_ROLES.get(cls, 'dps'),
            'level': getattr(m, 'level', 1),
            'hp': getattr(m, 'hp', 0),
            'maxHp': max_hp,
            'mana': getattr(m, 'mana', 0),
            'maxMana': max_mana,
            'move': getattr(m, 'move', 0),
            'maxMove': getattr(m, 'max_move', 1) or 1,
            'is_leader': bool(group) and m is group.leader,
            'is_self': m is player,
            'sameRoom': same_room,
            'roomName': getattr(mroom, 'name', '???') if mroom else '???',
            'roomVnum': mvnum,
            'dir': None if same_room else dir_by_vnum.get(mvnum),
            'fighting': _fighting_name(m),
            'online': getattr(m, 'connection', None) is not None or m is player,
            'dead': getattr(m, 'hp', 1) <= 0,
        })

    # pets & companions as compact sub-frames after their owner (you)
    for minion, kind in minions:
        mhp = getattr(minion, 'max_hp', 1) or 1
        members.append({
            'name': getattr(minion, 'name', kind), 'char_class': kind,
            'role': 'pet', 'level': getattr(minion, 'level', 1),
            'hp': getattr(minion, 'hp', 0), 'maxHp': mhp,
            'mana': 0, 'maxMana': 0, 'move': 0, 'maxMove': 1,
            'is_leader': False, 'is_self': False, 'is_minion': True, 'minion_kind': kind,
            'sameRoom': getattr(minion, 'room', None) is proom,
            'roomName': '', 'roomVnum': None, 'dir': None,
            'fighting': _fighting_name(minion),
            'online': True, 'dead': getattr(minion, 'hp', 1) <= 0,
        })

    return {
        'leader': getattr(group.leader, 'name', '') if group else getattr(player, 'name', ''),
        'loot_mode': getattr(group, 'loot_mode', 'freeforall') if group else 'freeforall',
        'auto_follow': bool(getattr(group, 'auto_follow', True)) if group else True,
        'exp_bonus': int((group.get_exp_bonus() - 1.0) * 100) if group else 0,
        'size': len(members),
        'is_leader': (player is group.leader) if group else True,
        'heal_spell': _best_heal_spell(player),
        'members': members,
    }


def build_combat_payload(player) -> dict:
    """Lightweight push for live combat: vitals + current-room entities only.

    Sent every violence round, so it must stay cheap — no BFS, no room list.
    """
    room = player.room
    mobs = []
    others = []
    if room and hasattr(room, 'characters'):
        for entity in room.characters:
            if hasattr(entity, 'account_name'):
                if entity is not player:
                    others.append({
                        'name': getattr(entity, 'name', 'Unknown'),
                        'level': getattr(entity, 'level', 1),
                        'char_class': getattr(entity, 'char_class', ''),
                        'hp': getattr(entity, 'hp', 0),
                        'maxHp': getattr(entity, 'max_hp', 1),
                    })
                continue
            quest_mark = ''
            if hasattr(entity, 'vnum'):
                try:
                    from quests import QuestManager
                    quest_mark = QuestManager.get_quest_giver_indicator(player, entity.vnum)
                except Exception:
                    quest_mark = ''
            mob = {
                'name': getattr(entity, 'name', 'Unknown'),
                'level': getattr(entity, 'level', 1),
                'hostile': getattr(entity, 'aggressive', False) or getattr(entity, 'hostile', False),
                'boss': 'boss' in (getattr(entity, 'flags', None) or []) or getattr(entity, 'is_boss', False),
                'shopkeeper': getattr(entity, 'special', '') == 'shopkeeper',
                'trainer': getattr(entity, 'special', '') in ('trainer', 'guildmaster'),
                'quest': quest_mark,
                'fighting': bool(getattr(entity, 'fighting', None) is player),
            }
            hp = getattr(entity, 'hp', None)
            max_hp = getattr(entity, 'max_hp', None)
            if hp is not None and max_hp:
                mob['hp'] = hp
                mob['maxHp'] = max_hp
            mobs.append(mob)
    return {
        'type': 'combat_update',
        'vnum': room.vnum if room else None,
        'in_combat': _in_combat(player),
        'player': {
            'name': player.name,
            'momentum': getattr(player, 'momentum', 0),
            'resource': _class_resource(player),
            'path': getattr(player, 'path', None),
            'path_active': _path_active(player),
            'stance': getattr(player, 'combat_stance', getattr(player, 'mood', '')),
            'hp': getattr(player, 'hp', 0),
            'max_hp': getattr(player, 'max_hp', 1),
            'mana': getattr(player, 'mana', 0),
            'max_mana': getattr(player, 'max_mana', 1),
            'move': getattr(player, 'move', 0),
            'max_move': getattr(player, 'max_move', 1),
            'level': getattr(player, 'level', 1),
            'exp': getattr(player, 'exp', 0),
            'exp_floor': _exp_thresholds(player)[0],
            'exp_to_level': _exp_thresholds(player)[1],
            'gold': getattr(player, 'gold', 0),
        },
        'mobs': mobs,
        'players': others,
        'group': build_group_block(player),
    }


_ATLAS_CACHE = None


def build_atlas(world) -> dict:
    """The complete world atlas: every room with coordinates and exit links,
    plus zone metadata and zone-to-zone connections. The world is static, so
    this is computed once and cached - it powers the full game map (M)."""
    global _ATLAS_CACHE
    if _ATLAS_CACHE is not None:
        return _ATLAS_CACHE

    coords = compute_room_coords(world.rooms, 3001)
    zone_colors = [
        '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
        '#f43f5e', '#ef4444', '#f97316', '#f59e0b', '#eab308',
        '#84cc16', '#22c55e', '#10b981', '#14b8a6', '#06b6d4',
        '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7',
    ]
    zones = {}
    rooms = []
    links = set()          # (zone_a, zone_b) pairs that touch
    for vnum, room in world.rooms.items():
        if vnum not in coords:
            continue
        x, y, z = coords[vnum]
        znum = room.zone.number if room.zone else -1
        if znum not in zones:
            zones[znum] = {
                'id': znum,
                'name': room.zone.name if room.zone else 'Unknown',
                'color': zone_colors[len(zones) % len(zone_colors)],
            }
        exits = {}
        for direction, exit_data in _iter_visible_exits(room, None):
            tv = _get_exit_target_vnum(exit_data)
            if tv and tv in world.rooms:
                exits[direction] = tv
                tz = world.rooms[tv].zone.number if world.rooms[tv].zone else -1
                if tz != znum:
                    links.add((min(znum, tz), max(znum, tz)))
        rooms.append({
            'vnum': vnum, 'name': room.name, 'zone': znum,
            'x': x, 'y': y, 'z': z,
            'sector': getattr(room, 'sector_type', '') or '',
            'exits': exits,
        })
    _ATLAS_CACHE = {
        'type': 'atlas',
        'rooms': rooms,
        'zones': list(zones.values()),
        'links': sorted(links),
    }
    return _ATLAS_CACHE


def build_map_payload(player, mode: str = 'full') -> dict:
    """Build map data payload for the web map UI."""
    explored = set(getattr(player, 'explored_rooms', set()))
    rooms: Dict[int, object] = {}

    if mode == 'zone' and player.room and player.room.zone:
        zone_rooms = set(player.room.zone.rooms.keys())
        for vnum in explored:
            if vnum in zone_rooms:
                room = player.world.rooms.get(vnum)
                if room:
                    rooms[vnum] = room
    else:
        for vnum in explored:
            room = player.world.rooms.get(vnum)
            if room:
                rooms[vnum] = room

    if not rooms:
        return {
            'type': 'map_data',
            'rooms': [],
            'frontier': [],
            'player': None,
        }

    start_vnum = player.room.vnum if player.room else None
    coords = compute_room_coords(rooms, start_vnum, player)
    if start_vnum not in coords:
        return {
            'type': 'map_data',
            'rooms': [],
            'frontier': [],
            'player': None,
        }

    frontier = get_frontier_coords(coords, rooms, explored, player)

    room_items = []
    zones_seen = {}
    for vnum, (x, y, z) in coords.items():
        room = rooms.get(vnum)
        exits = []
        one_way_exits = []
        
        portal_exits = []
        for direction, exit_data in _iter_visible_exits(room, player):
            if direction not in DIR_OFFSETS:
                # named passages (gate/arch/portal/...) — kept for pathfinding
                pt = _get_exit_target_vnum(exit_data)
                if pt:
                    portal_exits.append({'name': direction, 'to_room': pt})
                continue
            exits.append(direction)
            
            # Check if this is a one-way exit
            to_vnum = _get_exit_target_vnum(exit_data)
            if to_vnum:
                dest_room = rooms.get(to_vnum) or (player.world.rooms.get(to_vnum) if hasattr(player, 'world') else None)
                if dest_room:
                    reverse_dir = REVERSE_DIR.get(direction)
                    has_return = False
                    if reverse_dir:
                        for dest_dir, dest_exit in _iter_visible_exits(dest_room, player):
                            if dest_dir == reverse_dir:
                                dest_target = _get_exit_target_vnum(dest_exit)
                                if dest_target == vnum:
                                    has_return = True
                                    break
                    if not has_return:
                        one_way_exits.append(direction)
        
        zone_num = room.zone.number if room.zone else 0
        zone_name = room.zone.name if room.zone else 'Unknown'
        if zone_num not in zones_seen:
            zones_seen[zone_num] = zone_name
        
        # Build mob list for this room
        mob_list = []
        if hasattr(room, 'characters'):
            for entity in room.characters:
                if hasattr(entity, 'account_name'):
                    continue  # skip players (handled below)
                quest_mark = ''
                # quest scan is per-mob, per-room, per-push: only the CURRENT
                # room renders markers, so only compute it there (a veteran
                # character's full explored set made every step crawl)
                if hasattr(entity, 'vnum') and player.room and vnum == player.room.vnum:
                    try:
                        from quests import QuestManager
                        quest_mark = QuestManager.get_quest_giver_indicator(player, entity.vnum)
                    except Exception:
                        quest_mark = ''
                mob_info = {
                    'name': getattr(entity, 'name', 'Unknown'),
                    'level': getattr(entity, 'level', 1),
                    'hostile': getattr(entity, 'aggressive', False) or getattr(entity, 'hostile', False),
                    'boss': 'boss' in (getattr(entity, 'flags', None) or []) or getattr(entity, 'is_boss', False),
                    'shopkeeper': getattr(entity, 'special', '') == 'shopkeeper',
                'trainer': getattr(entity, 'special', '') in ('trainer', 'guildmaster'),
                    'quest': quest_mark,
                    'flags': list(getattr(entity, 'flags', []) or []),
                }
                # Include HP if available
                hp = getattr(entity, 'hp', None)
                max_hp = getattr(entity, 'max_hp', None)
                if hp is not None and max_hp:
                    mob_info['hp'] = hp
                    mob_info['maxHp'] = max_hp
                mob_list.append(mob_info)

        # Build other-players list for this room
        player_list = []
        if hasattr(room, 'characters'):
            for entity in room.characters:
                if hasattr(entity, 'account_name') and entity is not player:
                    player_list.append({
                        'name': getattr(entity, 'name', 'Unknown'),
                        'level': getattr(entity, 'level', 1),
                        'char_class': getattr(entity, 'char_class', ''),
                        'hp': getattr(entity, 'hp', 0),
                        'maxHp': getattr(entity, 'max_hp', 1),
                    })

        # Build door info for exits
        doors = {}
        if hasattr(room, 'exits'):
            raw_exits = room.exits if isinstance(room.exits, dict) else {}
            for direction, exit_data in raw_exits.items():
                if isinstance(exit_data, dict) and 'door' in exit_data:
                    door = exit_data['door']
                    doors[direction] = {
                        'name': door.get('name', 'door'),
                        'state': door.get('state', 'open'),
                        'locked': bool(door.get('locked', False)),
                    }

        # Items on ground
        item_list = []
        for item in (getattr(room, 'items', None) or getattr(room, 'contents', []))[:12]:
            item_list.append(item_info(item))

        room_items.append({
            'vnum': vnum,
            'name': room.name,
            'sector': room.sector_type,
            'zone': zone_num,
            'zoneName': zone_name,
            'x': x,
            'y': y,
            'z': z,
            'symbol': get_room_symbol(room),
            'icon': get_room_icon(room),
            'exits': exits,
            'oneWayExits': one_way_exits,
            'portals': portal_exits,
            'flags': list(room.flags) if hasattr(room, 'flags') else [],
            'mobs': mob_list,
            'players': player_list,
            'doors': doors,
            'items': item_list,
        })

    player_coord = coords[start_vnum]

    # Frontier is now a list of dicts
    valid_frontier = [f for f in frontier if isinstance(f, dict) and 'x' in f]
    
    # Build zones list with colors
    zone_colors = [
        '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
        '#f43f5e', '#ef4444', '#f97316', '#f59e0b', '#eab308',
        '#84cc16', '#22c55e', '#10b981', '#14b8a6', '#06b6d4',
        '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7',
    ]
    zones_list = []
    for i, (zone_num, zone_name) in enumerate(zones_seen.items()):
        zones_list.append({
            'id': zone_num,
            'name': zone_name,
            'color': zone_colors[i % len(zone_colors)],
        })
    
    # Game time info
    time_info = {}
    world = getattr(player, 'world', None)
    if world and hasattr(world, 'game_time'):
        gt = world.game_time
        time_info = {
            'hour': getattr(gt, 'hour', 12),
            'period': gt.get_period() if hasattr(gt, 'get_period') else 'afternoon',
            'day': getattr(gt, 'day', 1),
            'month': getattr(gt, 'month', 6),
            'year': getattr(gt, 'year', 1000),
        }

    # Weather info for current zone
    weather_info = {}
    if player.room and player.room.zone and hasattr(player.room.zone, 'weather'):
        w = player.room.zone.weather
        weather_info = {
            'sky': getattr(w, 'sky_condition', 'clear'),
            'temperature': getattr(w, 'temperature', 70),
            'wind': getattr(w, 'wind_speed', 0),
            'precipitation': getattr(w, 'precipitation', 'none'),
        }

    # Detailed info for the player's current room (used by the platformer client)
    current_room = None
    if player.room:
        cur = player.room
        cur_exits = {}
        raw_exits = cur.exits if isinstance(getattr(cur, 'exits', None), dict) else {}
        for direction, exit_data in _iter_visible_exits(cur, player):
            door = None
            raw = raw_exits.get(direction)
            if isinstance(raw, dict) and 'door' in raw:
                d = raw['door']
                door = {
                    'name': d.get('name', 'door'),
                    'state': d.get('state', 'open'),
                    'locked': bool(d.get('locked', False)),
                }
            to_vnum = _get_exit_target_vnum(exit_data)
            # signpost data: name the zone when this exit crosses a border
            to_zone = None
            if to_vnum and hasattr(player, 'world'):
                dest = player.world.rooms.get(to_vnum)
                if dest and dest.zone and cur.zone and dest.zone.number != cur.zone.number:
                    to_zone = dest.zone.name
            cur_exits[direction] = {
                'to_room': to_vnum,
                'door': door,
                'to_zone': to_zone,
            }
        try:
            from gravestones import GravestoneRegistry
            stones = GravestoneRegistry.for_room(cur.vnum)
        except Exception:
            stones = []
        # keywords the player can "look at" - first word of each extra_desc key
        details = []
        for keys in (getattr(cur, 'extra_descs', None) or {}):
            first = (keys.split() or [''])[0]
            if first:
                details.append(first.lower())
        current_room = {
            'vnum': cur.vnum,
            'name': cur.name,
            'description': getattr(cur, 'description', '') or '',
            'sector': getattr(cur, 'sector_type', '') or '',
            'flags': list(cur.flags) if hasattr(cur, 'flags') else [],
            'exits': cur_exits,
            'gravestones': stones,
            'details': details,
        }

    return {
        'type': 'map_data',
        'rooms': room_items,
        'frontier': valid_frontier,
        'current_room': current_room,
        'zones': zones_list,
        'time': time_info,
        'weather': weather_info,
        'player': {
            'name': player.name,
            'vnum': start_vnum,
            'x': player_coord[0],
            'y': player_coord[1],
            'z': player_coord[2],
            'hp': getattr(player, 'hp', 0),
            'max_hp': getattr(player, 'max_hp', 1),
            'mana': getattr(player, 'mana', 0),
            'max_mana': getattr(player, 'max_mana', 1),
            'move': getattr(player, 'move', 0),
            'max_move': getattr(player, 'max_move', 1),
            'level': getattr(player, 'level', 1),
            'char_class': getattr(player, 'char_class', ''),
            'race': getattr(player, 'race', ''),
            'class_skills': Config().CLASSES.get(getattr(player,'char_class','').lower(), {}).get('skills', []),
            'class_spells': Config().CLASSES.get(getattr(player,'char_class','').lower(), {}).get('spells', []),
            'title': getattr(player, 'title', ''),
            'str': getattr(player, 'str', 0),
            'int': getattr(player, 'int', 0),
            'wis': getattr(player, 'wis', 0),
            'dex': getattr(player, 'dex', 0),
            'con': getattr(player, 'con', 0),
            'cha': getattr(player, 'cha', 0),
            'hitroll': getattr(player, 'hitroll', 0),
            'damroll': getattr(player, 'damroll', 0),
            'armor_class': getattr(player, 'armor_class', 0),
            'gold': getattr(player, 'gold', 0),
            'exp': getattr(player, 'exp', 0),
            'exp_floor': _exp_thresholds(player)[0],
            'exp_to_level': _exp_thresholds(player)[1],
            'in_combat': _in_combat(player),
            'path': getattr(player, 'path', None),
            'path_active': _path_active(player),
            'equipment': {
                slot: dict(item_info(item), affects=getattr(item, 'affects', []))
                for slot, item in getattr(player, 'equipment', {}).items()
                if item is not None
            },
            'inventory': [
                dict(item_info(item), item_type=getattr(item, 'item_type', 'other'))
                for item in getattr(player, 'inventory', [])
            ],
            'aura': _worn_aura(player),
            'resource': _class_resource(player),
            'skills': dict(getattr(player, 'skills', {})),
            'talents': dict(getattr(player, 'talents', {})),
            'affects': AffectManager.save_affects(player),
        },
        'group': build_group_block(player),
    }
