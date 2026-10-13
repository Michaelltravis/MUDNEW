"""What a room looks like in 3D (Push 33): its *look*, apart from its sector.

A room's sector decides how it plays (moving, water, darkness); its look is only how the 3D client
draws it. The two came apart because most of the world's caves, sewers and deserts were typed
'inside', 'mountain' or 'field' long ago, so a cave drew as a tiled hall. Here each room gets a
look once at load, the first rule that answers:

  1. what is stated: a `look` in the room's zone data (the build-out and new zones write one),
     or world/looks.json (hand overrides by room or by zone, each with its reason);
  2. its name, by the ordered word table LOOK_WORDS; or, for a room typed indoors whose name is
     open country (The Plains, A Mountain Trail), that country (OPEN_COUNTRY);
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

LOOKS = ('cave', 'mine', 'crypt', 'sewer', 'dungeon', 'desert', 'snow', 'shore', 'volcanic', 'swamp', 'web', 'castle')
UNDERGROUND = {'cave', 'mine', 'crypt', 'sewer', 'dungeon'}
OUTDOOR = {'desert', 'snow', 'volcanic', 'swamp', 'web'}   # (a shore is an edge: it doesn't spread)

# first match wins: the specific before the general
LOOK_WORDS = [
    ('sewer', r'\b(sewers?|drains?|cisterns?|culverts?)\b'),
    ('crypt', r'\b(crypts?|tombs?|catacombs?|ossuar(?:y|ies)|sepulch\w*|sarcophag\w*|barrows?|burial chambers?)\b'),
    ('mine', r'\b(mines?|mineshafts?|shafts?|ore|mining|quarry|lode)\b'),
    ('cave', r'\b(caves?|caverns?|cavernous|grottos?|grottoes|stalactites?|stalagmites?|crawlways?|underground|subterranean)\b'),
    ('dungeon', r'\b(dungeons?|oubliettes?|torture chambers?|prison cells?|cell ?blocks?)\b'),
    # a spider's lair: webbed trees and tunnels (Arachnos, the spider queens' dens)
    ('web', r'\b(webs?|webbed|webby|webbing|cobwebs?|cocoon\w*|egg ?sacs?|spider ?silk)\b'),
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
    'web': re.compile(r'\b(coated with (?:cob)?webs?|covered in (?:cob)?webs?|thick (?:cob)?webs?|webbed (?:remains|bodies|corpses)|'
                      r'strands? of (?:web|silk)|spider ?silk)\b', re.I),
}
# a room that reads as a building's never takes an underground look from its neighbours
INTERIOR_RE = re.compile(
    r'\b(temple|church|chapel|cathedral|shrine|taverna?|inn|pub|bar|alehouse|bank|library|study|'
    r'bedroom|bed ?chamber|quarters|dormitory|throne|palace|shop|store|market|merchant|smithy|'
    r'guild|barracks|house|home|cottage|kitchen|parlou?r|dining|living room|stable|great hall|lore-hall|'
    r'belfry|bell ?tower|sacristy|vestry|nave|pews?|organ|choir|rose window|vestments)\b', re.I)

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
    'web': (3, {'field', 'hills', 'forest', 'city', 'mountain'}),
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


FOREST_WORDS = r'\b(forests?|woods|woodlands?|groves?|copse|thickets?|jungle|wildwood|greenwood|glades?|clearing|trees?|treetops?|branch(?:es)?)\b'
FOREST_RE = re.compile(FOREST_WORDS, re.I)
# a description plainly among trees: three or more of these (a field or a road through woods)
TREE_CUES = re.compile(r'\b(trees?|branch(?:es)?|boughs?|limbs?|canopy|foliage|trunks?|undergrowth|forest|woods|leaves|treetops?)\b', re.I)
CITY_CUES = re.compile(r'\b(streets?|shops?|buildings?|houses?|market|plaza|alley|cobble\w*|town|city)\b', re.I)
TUNNEL_RE = re.compile(r'\b(tunnels?|burrows?)\b', re.I)
# a castle's outside (its yard, walls and gate) is drawn as one: curtain walls with merlons, towers
# at the corners, banners; its halls and chambers stay rooms (INTERIOR_RE)
CASTLE_RE = re.compile(r'\b(castle|keep|fortress|citadel|stronghold|bailey|battlements?|ramparts?|gatehouse|'
                       r'portcullis|drawbridge|barbican|parapets?|wall ?walk|outer ward|inner ward|bastion)\b', re.I)
# a courtyard or a turret is a castle's only when the castle is named in its words or its zone's
# (a temple's courtyard, a mage's garden court stay as they are)
CASTLE_WEAK = re.compile(r'\b(courtyard|turrets?)\b', re.I)
CAVERN_RE = re.compile(r'\b(caverns?|caves?|shaft)\b', re.I)
ROCK_CUES = re.compile(r'\b(caves?|caverns?|rock|stone|earth|dark(?:ness)?|damp|underground|walls?)\b', re.I)
MOUNTAIN_WORDS = (r'\b(mountains?|mountainside|peaks?|summit|cliffs?|cliff\'s edge|crags?|ledges?|ravine|gorge|'
                  r'canyon|scree|slopes?|rocky|boulders?|the pass|mountain pass|precipice)\b')
MOUNTAIN_RE = re.compile(MOUNTAIN_WORDS, re.I)
# an indoor-typed room takes only the plain words (a ledge or a slope indoors is likely underground)
MOUNTAIN_STRONG = r'\b(mountains?|mountainside|peaks?|summit|cliffs?|cliff\'s edge)\b'

# a room typed as indoors whose name is open country ("The Plains", "A Mountain Trail"): drawn as
# the country it names, not as a furnished house (sector-named looks: field, forest, hills,
# mountain; a road in a town is a street)
OPEN_COUNTRY = [
    ('mountain', MOUNTAIN_STRONG),
    ('hills', r'\b(hills?|hillside|highlands?|downs|ridges?|foothills)\b'),
    ('forest', FOREST_WORDS),
    ('field', r'\b(plains?|meadows?|fields?|grasslands?|prairie|steppes?|pastures?|farmland|heath|moors?|savannah?)\b'),
    ('road', r'\b(roads?|trails?|paths?|highway|crossroads|track)\b'),
]
OPEN_RES = [(look, re.compile(pat, re.I)) for look, pat in OPEN_COUNTRY]
STREET_RE = re.compile(r'\b(street|avenue|lane|square|alley|plaza|market|wall road|gate)\b', re.I)
INDOOR_SECTORS = {'inside', 'dungeon'}


def open_country(room):
    """The open country an indoor-typed room's name says it is (None: it doesn't, or it reads as a
    building: a tavern on a mountain road is still a tavern). A forest is a forest whatever the
    room was typed (a wood on a hillside, in a town's park), but never under water."""
    sector = getattr(room, 'sector_type', '') or 'inside'
    if sector not in INDOOR_SECTORS:
        name = room.name or ''
        if sector in WATER_SECTORS or INTERIOR_RE.search(name):
            return None
        if sector != 'forest' and FOREST_RE.search(name):
            return 'forest'
        # mountain country typed as field, hills or forest (a mountain road, a ledge above a
        # ravine); a town's mountain wall stays in town
        if sector not in ('mountain', 'city') and MOUNTAIN_RE.search(name):
            return 'mountain'
        return None
    name = room.name or ''
    # an indoor room whose own description is underground (a ledge in a cavern) is underground
    if description_look(room.description) in UNDERGROUND:
        return None
    # a road names where it goes ("The Path By The Cathedral"): still a road (through a forest, a
    # forest); anything else that names a building is that building
    road = dict(OPEN_RES)['road'].search(name)
    if road and not re.search(r'\b(tavern|inn|shop|store)\b', name, re.I):
        return ('forest' if FOREST_RE.search(name) else 'mountain' if re.search(MOUNTAIN_STRONG, name, re.I)
                else 'city' if STREET_RE.search(name) else 'field')
    if INTERIOR_RE.search(name):
        return None
    for look, rx in OPEN_RES:
        if rx.search(name):
            if look == 'road':
                return 'city' if STREET_RE.search(name) else 'field'
            return look
    return None


def _castle(room, sector, name, desc):
    """A castle's yard, walls or gate by its name (not a street toward the keep, not a hall in it,
    not a cavern called a castle's way)."""
    if INTERIOR_RE.search(name) or CAVERN_RE.search(desc) or (sector == 'city' and STREET_RE.search(name)):
        return False
    if CASTLE_RE.search(name):
        return True
    zone = getattr(getattr(room, 'zone', None), 'name', '') or ''
    return bool(CASTLE_WEAK.search(name) and (CASTLE_RE.search(desc) or CASTLE_RE.search(zone)))


def _own_look(room):
    """(look, why) from the room's own words, or (None, None)."""
    sector = getattr(room, 'sector_type', '') or ''
    if sector in WATER_SECTORS:
        return None, None
    name, desc = room.name or '', room.description or ''
    # a tunnel through rock is a cave, whatever it was typed (the Mountain Range's were 'forest')
    if TUNNEL_RE.search(name) and ROCK_CUES.search(desc) and sector != 'city' and not INTERIOR_RE.search(name):
        return 'cave', 'name'
    look = words_look(room.name)
    why = 'name'
    if not look and _castle(room, sector, name, desc):
        return 'castle', 'name'
    if not look:
        look = open_country(room)
        # a forest or a mountain stays one whatever its description says, unless it is snowbound
        if look in ('forest', 'mountain') and description_look(room.description) == 'snow':
            look = 'snow'          # (still read from its name: a snowbound wood)
    if not look and sector == 'forest' and FOREST_RE.search(room.name or ''):
        # a forest typed as one and named as one: no description turns it into a swamp or a shore
        d = description_look(room.description)
        return (d, 'description') if d == 'snow' else ('forest', 'name')
    if not look:
        look, why = description_look(room.description), 'description'
    if not look:
        return None, None
    if sector == 'city' and look not in ('sewer', 'forest', 'web'):
        return None, None
    # an outdoor look found only in a description keeps an enclosed room enclosed
    if look in OUTDOOR | {'shore'} and why == 'description' and sector not in OUTDOOR_FROM_DESC:
        return None, None
    # and an underground one found only in a description, an enclosed room
    if look in UNDERGROUND and why == 'description' and sector not in ENCLOSED_SECTORS:
        return None, None
    return look, why


def _trees(room):
    """Open country (or a 'city' road) that its description plainly puts among trees."""
    sector = getattr(room, 'sector_type', '') or ''
    if sector not in ('field', 'hills', 'city') or INTERIOR_RE.search(room.name or ''):
        return False
    d = room.description or ''
    if sector == 'city' and (STREET_RE.search(room.name or '') or len(CITY_CUES.findall(d)) >= 2):
        return False
    return len(TREE_CUES.findall(d)) >= 3


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
        if not look and _trees(room):
            look, why = 'forest', 'description'
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


# Filler the old description padder added everywhere: an indoor scene's lines (walls, a ceiling,
# stale air, dust). Under open sky or the sea they contradict the room, so they come out of every
# room that is not enclosed (the owner: rooms should match their descriptions).
INDOOR_FILLER = [
    "Dust motes drift in the stale air.", "The walls are rough-hewn and cold to the touch.",
    "The ceiling hangs low overhead.", "The air is still and musty.", "Shadows gather in the corners.",
]
_FILLER_RE = [re.compile(r'\s*' + r'\s+'.join(re.escape(w) for w in f.split())) for f in INDOOR_FILLER]
OPEN_LOOKS = {'field', 'forest', 'hills', 'mountain', 'desert', 'snow', 'shore', 'swamp', 'volcanic',
              'water_swim', 'water_noswim', 'underwater', 'city', 'darkforest'}


def strip_filler(world) -> int:
    """Take the indoor filler out of the descriptions of rooms not enclosed; returns how many."""
    n = 0
    for room in (getattr(world, 'rooms', {}) or {}).values():
        look = getattr(room, 'look', None) or getattr(room, 'sector_type', '')
        flags = set(getattr(room, 'flags', None) or ())
        if look not in OPEN_LOOKS or ('indoors' in flags and look not in ('underwater', 'water_swim', 'water_noswim')):
            continue
        d = getattr(room, 'description', '') or ''
        new = d
        for rx in _FILLER_RE:
            new = rx.sub('', new)
        if new != d:
            room.description = new.strip()
            n += 1
    return n

