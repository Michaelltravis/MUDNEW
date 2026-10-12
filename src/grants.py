"""One-time gifts to named characters (world/grants.json), given on their next login.

    {"xtc": {"mounts": ["griffin", "horse"], "ride": "griffin", "explore_all": true,
             "waypoints_all": true, "room": 14804, "gearup": true, "gold": 0, "why": "..."}}

Each gift is given once: the save records it in `grants_received` (by the gift's own key,
"<name>:<sorted contents>"), so editing a character's entry gives the new gift once more.
Mounts already owned aren't given twice; unknown mounts are skipped.
"""
import json
import logging
import os

logger = logging.getLogger('Misthollow')
GRANTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'world', 'grants.json')


def load_grants(path=GRANTS) -> dict:
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    return {k.lower(): v for k, v in data.items() if not k.startswith('_') and isinstance(v, dict)}


def grant_key(name, gift) -> str:
    body = {k: v for k, v in gift.items() if k != 'why'}
    return f"{name.lower()}:{json.dumps(body, sort_keys=True)}"


def apply_grants(player, grants=None) -> list:
    """Give this player their gift if they haven't had it; returns lines to tell them."""
    gift = (grants if grants is not None else load_grants()).get(str(getattr(player, 'name', '')).lower())
    if not gift:
        return []
    key = grant_key(player.name, gift)
    got = getattr(player, 'grants_received', None)
    if got is None:
        player.grants_received = got = []
    if key in got:
        return []
    from mounts import MountManager, MOUNT_TEMPLATES
    lines = []
    for m in gift.get('mounts') or []:
        if m not in MOUNT_TEMPLATES:
            logger.warning(f"grants: {player.name}: no mount {m!r}")
            continue
        if not MountManager.get_owned_mount_data(player, m):
            player.owned_mounts.append({'key': m, 'loyalty': 100})
            lines.append(f"You are given {MOUNT_TEMPLATES[m]['name']} ({m}).")
    ride = gift.get('ride')
    if ride in MOUNT_TEMPLATES and MountManager.get_owned_mount_data(player, ride):
        player.mount = MountManager.create_mount(ride)
        lines.append(f"You are riding {player.mount.name}. (dismount / mount <name>; ride n n 3e to speedwalk)")
    world = getattr(player, 'world', None)
    if gift.get('explore_all') and world is not None:
        # every room on the map, but the God Rooms and lands sealed until built
        rooms = [r.vnum for r in world.rooms.values()
                 if 'imm_only' not in (r.flags or ()) and not getattr(getattr(r, 'zone', None), 'sealed', False)]
        before = len(player.explored_rooms)
        player.explored_rooms.update(rooms)
        lines.append(f"Your map is unveiled: {len(player.explored_rooms) - before:,} more rooms charted.")
    if gift.get('waypoints_all'):
        from travel import WAYPOINTS
        before = len(player.discovered_waypoints)
        player.discovered_waypoints.update(WAYPOINTS.keys())
        lines.append(f"Every travel waypoint is known to you ({len(player.discovered_waypoints) - before} new).")
    if gift.get('room') and world is not None:
        # put them somewhere (an owner testing a place): where they wake on this login
        v = int(gift['room'])
        if v in world.rooms:
            player.room_vnum = v
            lines.append(f"You find yourself at {world.rooms[v].name}.")
        else:
            logger.warning(f"grants: {player.name}: no room {v}")
    if gift.get('gearup'):
        # the endgame kit (CommandHandler.gear_up): given once they are in the world (it levels
        # them through the game's own level-up, which talks to them)
        player._grant_gearup = True
    if gift.get('gold'):
        player.gold = (getattr(player, 'gold', 0) or 0) + int(gift['gold'])
        lines.append(f"You are given {int(gift['gold']):,} gold.")
    got.append(key)
    logger.info(f"grants: gave {player.name} {gift}")
    return lines
