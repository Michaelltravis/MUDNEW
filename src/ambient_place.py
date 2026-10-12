"""Where a room is, as the ambient murmurs need it (ambient.py, ambient_lines.py): tags read off
the world itself rather than the room's sector alone (a castle hall is sector 'city' too, and it
got merchants and blacksmiths).

    place_tags(room, world) -> {'castle', 'indoors', 'dark', ...}

  smithy    an armourer, weaponsmith or blacksmith keeps shop here or next door, or the room is a forge
  market    any shopkeeper here or next door
  bakery    a baker or grocer here or next door
  tavern    an innkeeper or barkeep here or next door, or the room is an inn, tavern or bar
  castle    the room or its zone is a castle, keep, fortress, its walls or walks
  street    a town street under the sky (sector city, not indoors, not a castle)
  building  indoors, not a castle, not under the earth
  indoors / outdoors, dark, peaceful
  the room's look (room_looks.py): cave, mine, crypt, sewer, dungeon, forest, field, hills,
            mountain, snow, swamp, shore, desert, volcanic; water for the water sectors
  dawn / day / dusk / night, rain / storm (the sky: outdoors lines only take them with 'outdoors')
"""
import re

CASTLE_RE = re.compile(r"\b(castle|keep|fortress|citadel|battlements?|ramparts?|walkway atop|inner wall|throne|gatehouse|barbican|bailey)\b", re.I)
SMITH_RE = re.compile(r"\b(black)?smith(y)?\b|\bweaponsmith\b|\barmou?rer\b|\bforge\b", re.I)
BAKER_RE = re.compile(r"\b(baker|bakery|grocer|bread)\b", re.I)
TAVERN_RE = re.compile(r"\b(inn|tavern|taverna|alehouse|bar|pub|bartender|barkeep|barmaid|innkeeper|waiter|waitress)\b", re.I)
UNDER = {'cave', 'mine', 'sewer', 'crypt'}
LOOK_TAGS = {'cave', 'mine', 'crypt', 'sewer', 'dungeon', 'forest', 'field', 'hills', 'mountain', 'snow',
             'swamp', 'shore', 'desert', 'volcanic'}
WATER = {'water_swim', 'water_noswim', 'underwater'}


def neighbours(room, world):
    """The rooms one step away, by direction: [(dir, room)]."""
    out = []
    for d, ex in (getattr(room, 'exits', None) or {}).items():
        to = ex.get('to_room') if isinstance(ex, dict) else None
        r = world.rooms.get(to) if world is not None and to is not None else None
        if r is not None and r is not room:
            out.append((d, r))
    return out


def _keepers(rooms):
    for r in rooms:
        for ch in getattr(r, 'characters', None) or []:
            if getattr(ch, 'special', None) == 'shopkeeper' or getattr(ch, 'shop', None):
                yield ch


def _people(rooms):
    for r in rooms:
        for ch in getattr(r, 'characters', None) or []:
            if not hasattr(ch, 'connection'):
                yield ch


def place_tags(room, world, hour=None, weather=None) -> set:
    tags = set()
    if room is None:
        return tags
    flags = set(getattr(room, 'flags', None) or ())
    sector = getattr(room, 'sector_type', '') or 'inside'
    look = getattr(room, 'look', None) or sector
    name = getattr(room, 'name', '') or ''
    zone_name = getattr(getattr(room, 'zone', None), 'name', '') or ''
    here_and_next = [room] + [r for _, r in neighbours(room, world)]

    if look in LOOK_TAGS:
        tags.add(look)
    if sector in WATER or look in WATER:
        tags.add('water')
    indoors = 'indoors' in flags or sector == 'inside' or look in UNDER
    tags.add('indoors' if indoors else 'outdoors')
    if 'dark' in flags:
        tags.add('dark')
    if 'peaceful' in flags or 'sanctuary' in flags:
        tags.add('peaceful')
    castle = bool(CASTLE_RE.search(name) or CASTLE_RE.search(zone_name))
    if castle:
        tags.add('castle')
    elif look not in UNDER and look != 'dungeon':
        if sector == 'city' and not indoors:
            tags.add('street')
        if indoors:
            tags.add('building')

    keepers = list(_keepers(here_and_next))
    if keepers and not castle:
        tags.add('market')
    for k in keepers:
        nm = f"{getattr(k, 'name', '')} {getattr(k, 'short_desc', '')}"
        if SMITH_RE.search(nm):
            tags.add('smithy')
        if BAKER_RE.search(nm):
            tags.add('bakery')
    if SMITH_RE.search(name):
        tags.add('smithy')
    if TAVERN_RE.search(name) or any(TAVERN_RE.search(f"{getattr(p, 'name', '')} {getattr(p, 'short_desc', '')}")
                                     for p in _people(here_and_next) if getattr(p, 'special', None) in ('shopkeeper', 'innkeeper', 'receptionist')):
        tags.add('tavern')

    if hour is not None:
        tags.add('dawn' if 5 <= hour < 7 else 'day' if 7 <= hour < 18 else 'dusk' if 18 <= hour < 21 else 'night')
    if weather is not None:
        precip = getattr(weather, 'precipitation', 0)
        try:
            precip = int(precip)
        except (TypeError, ValueError):
            precip = 0
        if precip > 2 or getattr(weather, 'sky_condition', '') == 'stormy':
            tags.add('storm')
        elif precip > 0:
            tags.add('rain')
    return tags


def fits(key: str, tags: set) -> bool:
    """Does a line's key ('street', 'outdoors+night') hold here?"""
    return all(t in tags for t in key.split('+'))
