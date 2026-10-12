"""What a room looks like in 3D (Push 33): its *look*, apart from its sector.

A room's sector decides how it plays (moving, water, darkness); its look is only how the 3D client
draws it. The two came apart because most of the world's caves, sewers and deserts were typed
'inside', 'mountain' or 'field' long ago, so a cave drew as a tiled hall. Here each room gets a
look once at load, the first rule that answers:

  1. what is stated: a `look` in the room's zone data (the build-out and new zones write one),
     or world/looks.json (hand overrides by room or by zone, each with its reason);
  2. its name, by the ordered word table LOOK_WORDS;
  3. its description, by the same table (two mentions, or one telling phrase);
  4. its zone's default in world/looks.json;
  5. its neighbours: a room with no word of its own takes the look most of its looked
     neighbours in the same zone share, a few steps out (SPREAD: how far, and through which
     sectors). Underground looks spread only through enclosed rooms that don't read as a
     building's (a tavern, a kitchen...); outdoor looks only through open country;
  6. its zone, when the zone is plainly underground: a third of its enclosed rooms have
     underground looks by now (the most common at least ZONE_MIN), and the rest take that one.

Anything left keeps its sector as its look. Never saved but a stated one (Room.to_dict).
"""
import json
import logging
import os
import re
from collections import Counter

logger = logging.getLogger('Misthollow')

LOOKS = ('cave', 'mine', 'crypt', 'sewer', 'dungeon', 'desert', 'snow', 'shore', 'volcanic', 'swamp')
UNDERGROUND = {'cave', 'mine', 'crypt', 'sewer', 'dungeon'}
OUTDOOR = {'desert', 'snow', 'volcanic', 'swamp'}          # (a shore is an edge: it doesn't spread)

# first match wins: the specific before the general
LOOK_WORDS = [
    ('sewer', r'\b(sewers?|drains?|cisterns?|culverts?)\b'),
    ('crypt', r'\b(crypts?|tombs?|catacombs?|ossuar(?:y|ies)|sepulch\w*|sarcophag\w*|barrows?|burial chambers?)\b'),
    ('mine', r'\b(mines?|mineshafts?|shafts?|ore|mining|quarry|lode)\b'),
    ('cave', r'\b(caves?|caverns?|cavernous|grottos?|grottoes|stalactites?|stalagmites?|crawlways?|underground|subterranean)\b'),
    ('dungeon', r'\b(dungeons?|oubliettes?|torture chambers?|prison cells?|cell ?blocks?)\b'),
    ('volcanic', r'\b(lava|magma|volcan\w*|molten|caldera|ashen|ashlands?|cinders?|obsidian)\b'),
    ('desert', r'\b(deserts?|dunes?|sands|oasis|wastes of sand)\b'),
    ('snow', r'\b(snow\w*|frozen|glaciers?|glacial|tundra|icy|ice|frost\w*|winterlands?|blizzard)\b'),
    ('swamp', r'\b(swamps?|bogs?|marsh\w*|mires?|fens?|quagmire|bayou)\b'),
    ('shore', r'\b(beach(?:es)?|shores?|shoreline|coasts?|coastline|strand)\b'),
]
LOOK_RES = [(look, re.compile(pat, re.I)) for look, pat in LOOK_WORDS]
# one of these in a description is enough
TELLING = {
    'cave': re.compile(r'\b(in(?:side)? (?:a|the|this) (?:cave|cavern|grotto)|cave walls?|cavern walls?|'
                       r'stalactites|rough[- ]hewn rock|natural tunnel)\b', re.I),
    'sewer': re.compile(r'\b(sewage|sewer water|in the sewers?)\b', re.I),
    'mine': re.compile(r'\b(mine cart|ore cart|mining tunnel|support beams|pick ?axes? marks)\b', re.I),
    'crypt': re.compile(r'\b(burial niches?|coffins? line|stone coffins?|sarcophagi)\b', re.I),
}
# a room that reads as a building's never takes an underground look from its neighbours
INTERIOR_RE = re.compile(
    r'\b(temple|church|chapel|cathedral|shrine|taverna?|inn|pub|bar|alehouse|bank|library|study|'
    r'bedroom|bed ?chamber|quarters|dormitory|throne|palace|shop|store|market|merchant|smithy|'
    r'guild|barracks|house|home|cottage|kitchen|parlou?r|dining|living room|stable|great hall|lore-hall)\b', re.I)

ENCLOSED_SECTORS = {'inside', 'cave', 'dungeon', 'underground'}
WATER_SECTORS = {'water_swim', 'water_noswim', 'underwater'}
# outdoor looks found only in a description need an outdoor room
OUTDOOR_FROM_DESC = {'field', 'hills', 'mountain', 'forest', 'desert', 'swamp', 'road'}
# how far each look spreads to rooms with no word of their own, and through which sectors
SPREAD = {
    'cave': (3, ENCLOSED_SECTORS), 'mine': (3, ENCLOSED_SECTORS),
    'sewer': (3, ENCLOSED_SECTORS | {'forest', 'mountain', 'hills', 'field'}),   # the old sewer was typed anyhow
    'dungeon': (2, ENCLOSED_SECTORS), 'crypt': (1, ENCLOSED_SECTORS),
    'desert': (3, {'field', 'hills', 'mountain', 'desert'}), 'volcanic': (3, {'field', 'hills', 'mountain'}),
    'snow': (3, {'field', 'hills', 'mountain', 'forest'}), 'swamp': (2, {'field', 'swamp'}),
}

ZONE_MIN = 5

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OVERRIDES = os.path.join(ROOT, 'world', 'looks.json')


def words_look(text):
    """The first look a piece of text names, or None."""
    for look, rx in LOOK_RES:
        if rx.search(text or ''):
            return look
    return None


def description_look(text):
    """A look a description gives: two mentions of its words, or one telling phrase."""
    text = text or ''
    for look, rx in TELLING.items():
        if rx.search(text):
            return look
    for look, rx in LOOK_RES:
        if len(rx.findall(text)) >= 2:
            return look
    return None


def load_overrides(path=OVERRIDES):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {'rooms': {}, 'zones': {}}
    return {'rooms': {int(k): v for k, v in (data.get('rooms') or {}).items()},
            'zones': {int(k): v for k, v in (data.get('zones') or {}).items()}}


def _zone(room):
    return getattr(getattr(room, 'zone', None), 'number', None)


def _neighbours(room, rooms):
    for ex in (getattr(room, 'exits', None) or {}).values():
        to = ex.get('to_room') if isinstance(ex, dict) else ex
        try:
            other = rooms.get(int(to))
        except (TypeError, ValueError):
            other = None
        if other is not None and other is not room:
            yield other


def _own_look(room):
    """(look, why) from the room's own words, or (None, None)."""
    sector = getattr(room, 'sector_type', '') or ''
    if sector in WATER_SECTORS:
        return None, None
    look = words_look(room.name)
    why = 'name'
    if not look:
        look, why = description_look(room.description), 'description'
    if not look:
        return None, None
    if sector == 'city' and look != 'sewer':
        return None, None
    # an outdoor look found only in a description keeps an enclosed room enclosed
    if look in OUTDOOR | {'shore'} and why == 'description' and sector not in OUTDOOR_FROM_DESC:
        return None, None
    # and an underground one found only in a description, an enclosed room
    if look in UNDERGROUND and why == 'description' and sector not in ENCLOSED_SECTORS:
        return None, None
    return look, why


def _fits(room, look):
    """Whether a look that isn't the room's own (a zone's) suits it: an underground one an
    enclosed room that doesn't read as a building's, an outdoor one open country."""
    sector = getattr(room, 'sector_type', '') or 'inside'
    if look in UNDERGROUND:
        return sector in ENCLOSED_SECTORS and not INTERIOR_RE.search(f'{room.name} {room.description}')
    return sector in OUTDOOR_FROM_DESC


def classify(world, overrides=None):
    """Give every room its `look` (and `look_why`). Returns the counts per look."""
    rooms = getattr(world, 'rooms', {}) or {}
    ov = overrides if overrides is not None else load_overrides()
    for room in rooms.values():
        sector = getattr(room, 'sector_type', '') or 'inside'
        stated = getattr(room, 'stated_look', None) or ov['rooms'].get(room.vnum)
        if stated:
            room.look, room.look_why = stated, 'stated'
            continue
        look, why = _own_look(room)
        if not look and _zone(room) in ov['zones'] and _fits(room, ov['zones'][_zone(room)]):
            look, why = ov['zones'][_zone(room)], 'zone'
        room.look, room.look_why = (look, why) if look else (sector, None)
    # neighbours: waves out from the rooms with a look of their own
    for wave in range(max(n for n, _ in SPREAD.values())):
        taken = {}
        for room in rooms.values():
            if room.look_why is not None:
                continue
            sector = getattr(room, 'sector_type', '') or 'inside'
            near = Counter(n.look for n in _neighbours(room, rooms)
                           if n.look_why is not None and _zone(n) == _zone(room) and n.look in SPREAD)
            if not near:
                continue
            look = near.most_common(1)[0][0]
            steps, through = SPREAD[look]
            if wave >= steps or sector not in through:
                continue
            if look in UNDERGROUND and look != 'sewer' and INTERIOR_RE.search(f'{room.name} {room.description}'):
                continue
            taken[room] = look
        for room, look in taken.items():
            room.look, room.look_why = look, 'neighbours'
    # a zone that is plainly underground (a third or more of its enclosed rooms have underground
    # looks by now, the most common at least ZONE_MIN): its other enclosed rooms take that look
    zones = {}
    for room in rooms.values():
        zones.setdefault(_zone(room), []).append(room)
    for zn, members in zones.items():
        enclosed = [r for r in members if (getattr(r, 'sector_type', '') or 'inside') in ENCLOSED_SECTORS]
        named = Counter(r.look for r in enclosed if r.look_why is not None and r.look in UNDERGROUND)
        if not named:
            continue
        look, n = named.most_common(1)[0]
        if n < ZONE_MIN or sum(named.values()) * 3 < len(enclosed):
            continue
        for r in enclosed:
            if r.look_why is None and not INTERIOR_RE.search(f'{r.name} {r.description}'):
                r.look, r.look_why = look, 'zone'
    return Counter(r.look for r in rooms.values())


def summary(world):
    """Counts per look and per reason, for the world check and the docs."""
    rooms = (getattr(world, 'rooms', {}) or {}).values()
    return {'looks': Counter(r.look for r in rooms), 'why': Counter(r.look_why for r in rooms)}
