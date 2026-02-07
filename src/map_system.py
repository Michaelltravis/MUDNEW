"""
Map rendering and coordinate utilities for RealmsMUD.
"""

from typing import Dict, Tuple, Set, List, Optional

from config import Config

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
    if 'death' in flags or 'deathtrap' in name:
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
    offset_x = 0

    def bfs(seed_vnum: int, seed_coord: Tuple[int, int, int]):
        queue = [seed_vnum]
        coords[seed_vnum] = seed_coord
        unvisited.discard(seed_vnum)
        while queue:
            vnum = queue.pop(0)
            room = rooms[vnum]
            x, y, z = coords[vnum]
            for direction, exit_data in _iter_visible_exits(room, player):
                if direction not in DIR_OFFSETS:
                    continue
                to_vnum = _get_exit_target_vnum(exit_data)
                if to_vnum not in rooms:
                    continue
                if to_vnum in coords:
                    continue
                dx, dy, dz = DIR_OFFSETS[direction]
                coords[to_vnum] = (x + dx, y + dy, z + dz)
                unvisited.discard(to_vnum)
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


def get_frontier_coords(coords: Dict[int, Tuple[int, int, int]], rooms: Dict[int, object], explored: Set[int], player=None) -> Set[Tuple[int, int, int]]:
    frontier = set()
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
                frontier.add((x + dx, y + dy, z + dz))
    return frontier


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
        points = list(coords.values()) + list(frontier)
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
    for x, y, z in frontier:
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
        
        for direction, exit_data in _iter_visible_exits(room, player):
            if direction not in DIR_OFFSETS:
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
            'flags': list(room.flags) if hasattr(room, 'flags') else [],
        })

    player_coord = coords[start_vnum]

    # Filter frontier to only valid 3-tuples (defensive coding)
    valid_frontier = [f for f in frontier if isinstance(f, tuple) and len(f) == 3]
    
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
    
    return {
        'type': 'map_data',
        'rooms': room_items,
        'frontier': [{'x': x, 'y': y, 'z': z} for (x, y, z) in valid_frontier],
        'zones': zones_list,
        'player': {
            'name': player.name,
            'vnum': start_vnum,
            'x': player_coord[0],
            'y': player_coord[1],
            'z': player_coord[2],
        }
    }
