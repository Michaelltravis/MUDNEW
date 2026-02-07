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


def get_set_bonus(set_id: int, pieces: int, in_zone: bool):
    category = ZONE_CATEGORIES.get(set_id)
    if not category:
        return {}
    config = CATEGORY_BONUSES.get(category, {})
    table = config.get('in_zone' if in_zone else 'always', {})
    bonuses = {}
    for threshold in (2,4,6):
        if pieces >= threshold and threshold in table:
            for stat, val in table[threshold].items():
                bonuses[stat] = bonuses.get(stat, 0) + val
    return bonuses
