"""
Zone Set Bonuses
=================
Each zone has a set_id (zone number). Wearing 2/4/6 pieces grants bonuses.
Both always-on and in-zone bonuses apply.
"""

# Zone categories
ZONE_CATEGORIES = {
    186: 'newbie',
    60: 'forest',
    70: 'sewer', 71: 'sewer', 72: 'sewer',
    62: 'orc',
    200: 'shadow_forest',
    40: 'dwarf_mines',
    90: 'swamp',
    100: 'dwarf_kingdom',
    64: 'arcane',
    50: 'desert',
    110: 'elf',
    52: 'city',
    54: 'city',
    51: 'shadow',
    65: 'dwarf_kingdom',
    63: 'venom',
    120: 'city',
    53: 'pyramid',
    130: 'sea',
    150: 'royal',
    33: 'duel',
    25: 'arcane',
    140: 'death',
    160: 'chaos',
}

CATEGORY_BONUSES = {
    'newbie': {
        'always': {2:{'armor_class':1},4:{'hitroll':1},6:{'max_hp':20}},
        'in_zone': {2:{'max_hp':10},4:{'hitroll':1},6:{'damroll':1}}
    },
    'forest': {
        'always': {2:{'dex':1},4:{'wis':1},6:{'max_move':20}},
        'in_zone': {2:{'hitroll':1},4:{'dex':1},6:{'max_move':30}}
    },
    'shadow_forest': {
        'always': {2:{'dex':1},4:{'shadow_resist':5},6:{'hitroll':1}},
        'in_zone': {2:{'shadow_resist':10},4:{'dex':1},6:{'damroll':1}}
    },
    'sewer': {
        'always': {2:{'poison_resist':5},4:{'con':1},6:{'max_hp':30}},
        'in_zone': {2:{'poison_resist':10},4:{'con':1},6:{'max_hp':40}}
    },
    'orc': {
        'always': {2:{'str':1},4:{'damroll':1},6:{'max_hp':30}},
        'in_zone': {2:{'damroll':1},4:{'str':1},6:{'hitroll':1}}
    },
    'dwarf_mines': {
        'always': {2:{'con':1},4:{'armor_class':2},6:{'max_hp':40}},
        'in_zone': {2:{'armor_class':2},4:{'con':1},6:{'damroll':1}}
    },
    'dwarf_kingdom': {
        'always': {2:{'con':1},4:{'str':1},6:{'armor_class':2}},
        'in_zone': {2:{'armor_class':2},4:{'str':1},6:{'damroll':1}}
    },
    'swamp': {
        'always': {2:{'disease_resist':5},4:{'con':1},6:{'max_hp':30}},
        'in_zone': {2:{'disease_resist':10},4:{'con':1},6:{'damroll':1}}
    },
    'desert': {
        'always': {2:{'con':1},4:{'max_move':20},6:{'hitroll':1}},
        'in_zone': {2:{'max_move':30},4:{'hitroll':1},6:{'damroll':1}}
    },
    'elf': {
        'always': {2:{'dex':1},4:{'wis':1},6:{'hitroll':1}},
        'in_zone': {2:{'dex':1},4:{'hitroll':1},6:{'max_mana':30}}
    },
    'city': {
        'always': {2:{'cha':1},4:{'armor_class':1},6:{'max_hp':30}},
        'in_zone': {2:{'armor_class':1},4:{'cha':1},6:{'hitroll':1}}
    },
    'shadow': {
        'always': {2:{'shadow_resist':5},4:{'dex':1},6:{'hitroll':1}},
        'in_zone': {2:{'shadow_resist':10},4:{'dex':1},6:{'damroll':1}}
    },
    'venom': {
        'always': {2:{'poison_resist':5},4:{'dex':1},6:{'hitroll':1}},
        'in_zone': {2:{'poison_resist':10},4:{'dex':1},6:{'damroll':1}}
    },
    'pyramid': {
        'always': {2:{'curse_resist':5},4:{'wis':1},6:{'max_mana':30}},
        'in_zone': {2:{'curse_resist':10},4:{'wis':1},6:{'hitroll':1}}
    },
    'sea': {
        'always': {2:{'cold_resist':5},4:{'dex':1},6:{'max_move':20}},
        'in_zone': {2:{'cold_resist':10},4:{'dex':1},6:{'hitroll':1}}
    },
    'royal': {
        'always': {2:{'cha':1},4:{'armor_class':2},6:{'max_hp':40}},
        'in_zone': {2:{'armor_class':2},4:{'cha':1},6:{'damroll':1}}
    },
    'duel': {
        'always': {2:{'hitroll':1},4:{'dex':1},6:{'damroll':1}},
        'in_zone': {2:{'hitroll':2},4:{'dex':1},6:{'damroll':2}}
    },
    'arcane': {
        'always': {2:{'int':1},4:{'max_mana':40},6:{'spell_resist':5}},
        'in_zone': {2:{'max_mana':40},4:{'int':1},6:{'spell_resist':10}}
    },
    'death': {
        'always': {2:{'shadow_resist':5},4:{'damroll':1},6:{'max_hp':40}},
        'in_zone': {2:{'shadow_resist':10},4:{'damroll':1},6:{'hitroll':1}}
    },
    'chaos': {
        'always': {2:{'spell_resist':5},4:{'damroll':1},6:{'max_mana':50}},
        'in_zone': {2:{'spell_resist':10},4:{'damroll':1},6:{'hitroll':1}}
    },
}


"""
Named Equipment Sets
====================
Item-specific sets with 2pc/4pc bonuses. Items reference a set by string set_id.
"""

NAMED_SETS = {
    # ── Low-level sets (10-20) ──────────────────────────────────────────
    "miners_garb": {
        "name": "Miner's Garb",
        "level_range": (10, 20),
        "zone": 40,  # Moria / Dwarf Mines
        "pieces": {
            4001: "miner's pickaxe",
            4002: "miner's iron helmet",
            4003: "miner's heavy boots",
            4004: "miner's thick gloves",
        },
        "bonuses": {
            2: {"damroll": 2, "str": 1},         # +mining damage
            4: {"earth_resist": 15, "con": 2},   # +resist earth
        },
    },
    "forest_stalker": {
        "name": "Forest Stalker",
        "level_range": (10, 20),
        "zone": 60,  # Forest
        "pieces": {
            6001: "forest stalker's leather armor",
            6002: "forest stalker's cloak",
            6003: "forest stalker's boots",
            6004: "forest stalker's longbow",
        },
        "bonuses": {
            2: {"dex": 2, "hitroll": 1},          # +sneak
            4: {"nature_resist": 15, "max_move": 30},  # +nature resist
        },
    },

    # ── Mid-level sets (20-35) ──────────────────────────────────────────
    "drow_shadow": {
        "name": "Drow Shadow",
        "level_range": (20, 35),
        "zone": 51,  # Drow City
        "pieces": {
            5151: "drow shadow armor",
            5152: "drow shadow cloak",
            5153: "drow shadow blade",
            5154: "drow shadow ring",
        },
        "bonuses": {
            2: {"dex": 2, "hitroll": 2},           # +stealth
            4: {"poison_resist": 20, "shadow_resist": 10},  # +poison resist
        },
    },
    "pharaohs_legacy": {
        "name": "Pharaoh's Legacy",
        "level_range": (20, 35),
        "zone": 53,  # Great Pyramid
        "pieces": {
            5320: "golden armor of the pharaoh",
            5321: "pharaoh's crown",
            5322: "pharaoh's scepter",
            5323: "pharaoh's sandals",
        },
        "bonuses": {
            2: {"wis": 3, "max_mana": 30},         # +wisdom
            4: {"curse_resist": 20, "int": 2},      # +curse resist
        },
    },
    "sewer_rat": {
        "name": "Sewer Rat",
        "level_range": (20, 35),
        "zone": 70,  # Sewers
        "pieces": {
            7001: "ratty leather vest",
            7002: "sewer rat's ring",
            7003: "sewer rat's boots",
            7004: "sewer rat's dagger",
        },
        "bonuses": {
            2: {"disease_resist": 15, "con": 1},    # +disease resist
            4: {"dex": 3, "armor_class": 3},         # +dodge
        },
    },

    # ── High-level sets (35-50) ─────────────────────────────────────────
    "dragonscale": {
        "name": "Dragonscale",
        "level_range": (35, 50),
        "zone": 80,  # Dragon's Domain
        "pieces": {
            8001: "dragonscale breastplate",
            8002: "dragonscale helm",
            8003: "dragonscale gauntlets",
            8004: "dragonscale shield",
        },
        "bonuses": {
            2: {"fire_resist": 20, "armor_class": 3},  # +fire resist
            4: {"max_hp": 100, "con": 3},              # +massive HP
        },
    },
    "necromancers_regalia": {
        "name": "Necromancer's Regalia",
        "level_range": (35, 50),
        "classes": ("necromancer",),
        "zone": 140,  # Necropolis
        "pieces": {
            14001: "bone-stitched robes",
            14002: "skull-topped staff",
            14003: "death shroud cloak",
            14004: "ring of the lich",
        },
        "bonuses": {
            2: {"int": 3, "damroll": 2},                # +spell power
            4: {"shadow_resist": 20, "max_hp": 50},     # +drain life
        },
        "procs": {4: [{"type": "on_hit", "effect": "grave_drain", "chance": 8}]},
    },
    "chaos_weave": {
        "name": "Chaos Weave",
        "level_range": (35, 50),
        "zone": 160,  # Plane of Chaos
        "pieces": {
            16001: "shifting chaos armor",
            16002: "prismatic ring of chaos",
            16003: "chaos blade",
            16004: "boots of planar shift",
        },
        "bonuses": {
            2: {"spell_resist": 10, "fire_resist": 10, "cold_resist": 10},  # +all resist
            4: {"damroll": 4, "hitroll": 4},             # +random proc
        },
        "procs": {4: [{"type": "on_hit", "effect": "chaos_bolt", "chance": 10}]},
    },

    # ── Endgame sets (50-60) ────────────────────────────────────────────
    "apocalypse_raiment": {
        "name": "Apocalypse Raiment",
        "level_range": (50, 60),
        "zone": 220,  # Castle Apocalypse
        "pieces": {
            22001: "death's black armor",
            22002: "war helm of the apocalypse",
            22003: "pestilence cloak",
            22004: "famine ring",
        },
        "bonuses": {
            2: {"str": 3, "dex": 3, "con": 3, "int": 3, "wis": 3},  # +all stats
            4: {"damroll": 8, "hitroll": 8, "max_hp": 80},           # +devastating
        },
        "procs": {4: [{"type": "on_hit", "effect": "apocalypse_ruin", "chance": 8}]},
    },
    "frostlords_mantle": {
        "name": "Frostlord's Mantle",
        "level_range": (50, 60),
        "zone": 190,  # Frostspire
        "pieces": {
            19001: "frostlord's plate armor",
            19002: "ice crown of the frostlord",
            19003: "frozen gauntlets",
            19004: "boots of permafrost",
        },
        "bonuses": {
            2: {"cold_resist": 25, "damroll": 3},       # +cold power
            4: {"max_hp": 80, "armor_class": 5, "cold_resist": 15},  # +frost aura
        },
        "procs": {4: [{"type": "on_defend", "effect": "frost_aura", "chance": 20}]},
    },

    # ── Class sets (55-66): what a caster or a rogue wears at the top (class_gear.py) ──
    "archmage_vestments": {
        "name": "Archmage's Vestments",
        "level_range": (60, 66),
        "zone": 290,  # the Black Observatory: the Eclipse Regent
        "classes": ("mage",),
        "pieces": {
            29060: "archmage starwoven robe",
            29061: "archmage pointed wizard hat",
            29062: "archmage silk gloves",
            29063: "archmage star-silk slippers",
        },
        "bonuses": {
            2: {"int": 3, "max_mana": 60},
            4: {"damroll": 6, "spell_resist": 15, "max_hp": 60},
        },
    },
    "lichlord_shroud": {
        "name": "Lich-Lord's Shroud",
        "level_range": (60, 68),
        "zone": 285,  # the Thalassine Lich and the Bone-Crowned Sovereign
        "classes": ("necromancer",),
        "pieces": {
            28560: "lich-lord grave-silk robe",
            28561: "lich-lord cowl",
            29560: "lich-lord bone-knuckled wraps",
            29561: "lich-lord grave-walker shoes",
        },
        "bonuses": {
            2: {"int": 3, "shadow_resist": 15},
            4: {"damroll": 6, "max_mana": 60, "max_hp": 60},
        },
    },
    "nightblade_leathers": {
        "name": "Nightblade's Leathers",
        "level_range": (55, 60),
        "zone": 245,  # Shadowspire Citadel: Shadow Lord Malachar
        "classes": ("thief", "assassin", "bard"),
        "pieces": {
            24510: "nightblade leather jerkin",
            24511: "nightblade hood",
            24512: "nightblade leather gloves",
            24513: "nightblade leather breeches",
        },
        "bonuses": {
            2: {"dex": 3, "hitroll": 4},
            4: {"damroll": 7, "max_hp": 70},
        },
    },
}


def get_named_set_bonus(set_id: str, pieces: int) -> dict:
    """Get bonuses from a named equipment set."""
    config = NAMED_SETS.get(set_id)
    if not config:
        return {}
    bonuses = {}
    for threshold in (2, 4):
        if pieces >= threshold and threshold in config.get('bonuses', {}):
            for stat, val in config['bonuses'][threshold].items():
                bonuses[stat] = bonuses.get(stat, 0) + val
    return bonuses


# How many pieces of each set one hero can wear at once (its pieces' slots: two rings, two
# necklaces, two bracers, one of everything else), filled at world load. A tier that asks for
# more than that unlocks at that many instead, so every tier can be reached.
SET_CAPS = {}
PAIRED_SLOTS = {'finger', 'neck', 'wrist'}


def _slot_kind(slot):
    slot = str(slot or '')
    return slot.rstrip('12') if slot.rstrip('12') in PAIRED_SLOTS else slot


def build_set_caps(world):
    """set id -> the most of its pieces one hero can wear (SET_CAPS)."""
    from objects import infer_wear_slot
    slots = {}
    for vnum, proto in (getattr(world, 'obj_prototypes', {}) or {}).items():
        if not isinstance(proto, dict) or proto.get('set_id') in (None, ''):
            continue
        sid = proto['set_id']
        sid = int(sid) if isinstance(sid, str) and sid.isdigit() else sid
        slot = proto.get('wear_slot') or (proto.get('wear_flags') if isinstance(proto.get('wear_flags'), str) else None)
        if not slot:
            class _P:
                pass
            probe = _P()
            probe.wear_slot, probe.item_type = None, proto.get('item_type', '')
            probe.name, probe.short_desc = proto.get('name', ''), proto.get('short_desc', '')
            slot = infer_wear_slot(probe) or ('wield' if proto.get('item_type') == 'weapon' else None)
        if slot:
            kind = _slot_kind(slot)
            slots.setdefault(sid, {})[kind] = slots.setdefault(sid, {}).get(kind, 0) + 1
    caps = {sid: sum(min(n, 2 if kind in PAIRED_SLOTS else 1) for kind, n in by.items()) for sid, by in slots.items()}
    SET_CAPS.clear()
    SET_CAPS.update(caps)
    return caps


def tier_need(set_id, threshold):
    """Pieces a tier really asks for: its number, or every piece one hero can wear."""
    cap = SET_CAPS.get(set_id)
    return min(threshold, cap) if cap else threshold


def set_name(set_id):
    if isinstance(set_id, str) and set_id in NAMED_SETS:
        return NAMED_SETS[set_id]['name']
    cat = ZONE_CATEGORIES.get(set_id)
    return f"{cat.replace('_', ' ').title()} Set (zone {set_id})" if cat else f"Set {set_id}"


def set_tiers(set_id):
    """[(pieces needed, {stat: value}, 'always' | 'in_zone', [procs])] for a set, lowest first."""
    out = []
    if isinstance(set_id, str) and set_id in NAMED_SETS:
        cfg = NAMED_SETS[set_id]
        for thr in sorted(set(cfg.get('bonuses', {})) | set(cfg.get('procs', {}))):
            out.append((tier_need(set_id, thr), cfg.get('bonuses', {}).get(thr, {}), 'always', cfg.get('procs', {}).get(thr, [])))
        return out
    table = CATEGORY_BONUSES.get(ZONE_CATEGORIES.get(set_id), {})
    for where in ('always', 'in_zone'):
        for thr in sorted(table.get(where, {})):
            out.append((tier_need(set_id, thr), table[where][thr], where, []))
    return out


def describe_bonus(stats):
    """'+2 dex, armour +10' for a tier's stats."""
    parts = []
    for stat, val in stats.items():
        if stat == 'armor_class':
            parts.append(f"armour +{val * 5}")
        else:
            parts.append(f"+{val} {stat.replace('_', ' ')}")
    return ', '.join(parts)


def get_set_bonus(set_id, pieces: int, in_zone: bool):
    # Handle named sets (string IDs)
    if isinstance(set_id, str) and not set_id.isdigit():
        config = NAMED_SETS.get(set_id)
        if not config:
            return {}
        bonuses = {}
        for threshold, table in config.get('bonuses', {}).items():
            if pieces >= tier_need(set_id, threshold):
                for stat, val in table.items():
                    bonuses[stat] = bonuses.get(stat, 0) + val
        return bonuses

    set_id = int(set_id) if isinstance(set_id, str) else set_id
    category = ZONE_CATEGORIES.get(set_id)
    if not category:
        return {}
    config = CATEGORY_BONUSES.get(category, {})
    table = config.get('in_zone' if in_zone else 'always', {})
    bonuses = {}
    for threshold in (2,4,6):
        if threshold in table and pieces >= tier_need(set_id, threshold):
            for stat, val in table[threshold].items():
                bonuses[stat] = bonuses.get(stat, 0) + val
    return bonuses
