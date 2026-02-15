"""
RealmsMUD Objects
=================
Items, equipment, and containers.
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world import World

from config import Config

logger = logging.getLogger('RealmsMUD.Objects')


class Object:
    """A game object (item)."""
    
    def __init__(self, vnum: int, world: 'World' = None):
        self.vnum = vnum
        self.world = world
        self.config = Config()
        
        # Basic properties
        self.name = "an object"
        self.short_desc = "an object"
        self.room_desc = "An object lies here."
        self.description = "You see nothing special."
        
        # Item properties
        self.item_type = "other"  # weapon, armor, potion, etc.
        self.wear_slot = None  # Where it can be worn
        self.set_id = None      # Zone set id
        self.weight = 1
        self.cost = 0
        self.value = 0  # Alias for shop system compatibility
        
        # Weapon properties
        self.damage_dice = "1d4"
        self.weapon_type = "hit"
        
        # Armor properties
        self.armor = 0
        
        # Container properties
        self.contents = []
        self.capacity = 0
        self.is_closed = False  # Containers start open by default
        self.is_locked = False
        self.locked = False  # Backward compatibility
        self.key_vnum = None
        self.lock_difficulty = 0
        
        # Consumable properties
        self.food_value = 0
        self.drinks = 0
        self.max_drinks = 0  # Maximum drink capacity
        self.liquid = "water"
        self.spell_effects = []
        
        # Light properties
        self.light_hours = 0
        
        # Magical properties
        self.affects = []  # [{type, value}, ...]
        self.flags = set()

        # Lore/Readable text
        self.lore_id = None
        self.lore_title = None
        self.lore_text = None
        self.lore_zone = None
        self.readable_text = None
        
        # Timer (for decay, etc.)
        self.timer = -1
        
    def get_description(self) -> str:
        """Get the full description of the object."""
        c = self.config.COLORS
        lines = [f"{c['cyan']}{self.short_desc}{c['reset']}"]
        lines.append(f"{c['white']}{self.description}{c['reset']}")
        
        if self.item_type == 'weapon':
            lines.append(f"{c['yellow']}Damage: {self.damage_dice} ({self.weapon_type}){c['reset']}")
        elif self.item_type == 'armor':
            lines.append(f"{c['yellow']}Armor: {self.armor}{c['reset']}")
            if self.wear_slot:
                lines.append(f"{c['yellow']}Worn on: {self.wear_slot}{c['reset']}")
                
        if self.affects:
            for affect in self.affects:
                lines.append(f"{c['bright_magenta']}Affects {affect['type']}: {affect['value']:+d}{c['reset']}")
                
        lines.append(f"{c['white']}Weight: {self.weight}  Value: {self.cost} gold{c['reset']}")
        
        return '\n'.join(lines)
        
    def to_dict(self) -> dict:
        """Convert object to dictionary for saving."""
        return {
            'vnum': self.vnum,
            'name': self.name,
            'short_desc': self.short_desc,
            'room_desc': self.room_desc,
            'description': self.description,
            'item_type': self.item_type,
            'wear_slot': self.wear_slot,
            'set_id': self.set_id,
            'weight': self.weight,
            'cost': self.cost,
            'damage_dice': self.damage_dice,
            'weapon_type': self.weapon_type,
            'armor': self.armor,
            'contents': [item.to_dict() for item in self.contents],
            'capacity': self.capacity,
            'is_closed': getattr(self, 'is_closed', False),
            'is_locked': getattr(self, 'is_locked', False),
            'key_vnum': getattr(self, 'key_vnum', None),
            'food_value': self.food_value,
            'drinks': self.drinks,
            'max_drinks': self.max_drinks,
            'liquid': self.liquid,
            'spell_effects': self.spell_effects,
            'light_hours': self.light_hours,
            'affects': self.affects,
            'flags': list(self.flags),
            'lore_id': self.lore_id,
            'lore_title': self.lore_title,
            'lore_text': self.lore_text,
            'lore_zone': self.lore_zone,
            'readable_text': self.readable_text,
            'timer': self.timer,
        }
        
    @classmethod
    def from_dict(cls, data: dict, world: 'World' = None) -> 'Object':
        """Create an object from dictionary data."""
        obj = cls(data.get('vnum', 0), world)
        
        obj.name = data.get('name', 'an object')
        obj.short_desc = data.get('short_desc', obj.name)
        obj.room_desc = data.get('room_desc', f"{obj.short_desc} lies here.")
        obj.description = data.get('description', '')
        obj.item_type = data.get('item_type', 'other')
        obj.wear_slot = data.get('wear_slot')
        obj.set_id = data.get('set_id')
        obj.weight = data.get('weight', 1)
        obj.cost = data.get('cost', data.get('value', 0))
        obj.value = obj.cost  # Alias for shop system compatibility
        obj.damage_dice = data.get('damage_dice', '1d4')
        obj.weapon_type = data.get('weapon_type', 'hit')
        obj.armor = data.get('armor', 0)
        obj.capacity = data.get('capacity', 0)
        obj.is_closed = data.get('is_closed', False)
        obj.is_locked = data.get('is_locked', False)
        obj.locked = data.get('locked', False)  # Backward compatibility
        obj.key_vnum = data.get('key_vnum')
        obj.food_value = data.get('food_value', 0)
        obj.drinks = data.get('drinks', 0)
        obj.max_drinks = data.get('max_drinks', obj.drinks)  # Default to current drinks if not specified
        obj.liquid = data.get('liquid', 'water')
        obj.spell_effects = data.get('spell_effects', [])
        obj.light_hours = data.get('light_hours', 0)
        obj.affects = data.get('affects', [])
        obj.flags = set(data.get('flags', []))
        obj.lore_id = data.get('lore_id')
        obj.lore_title = data.get('lore_title')
        obj.lore_text = data.get('lore_text')
        obj.lore_zone = data.get('lore_zone')
        obj.readable_text = data.get('readable_text')
        obj.timer = data.get('timer', -1)

        # Load contents recursively
        obj.contents = [cls.from_dict(item_data, world) 
                       for item_data in data.get('contents', [])]
        
        return obj
        
    @classmethod
    def from_prototype(cls, proto: dict, world: 'World' = None) -> 'Object':
        """Create an object from a prototype dictionary."""
        obj = cls(proto.get('vnum', 0), world)
        
        obj.name = proto.get('name', 'an object')
        obj.short_desc = proto.get('short_desc', obj.name)
        obj.room_desc = proto.get('room_desc', f"{obj.short_desc} lies here.")
        obj.description = proto.get('description', 'You see nothing special.')
        obj.item_type = proto.get('item_type', proto.get('type', 'other'))
        obj.wear_slot = proto.get('wear_slot')
        # Support wear_flags list (CircleMUD-style) as fallback for wear_slot
        if not obj.wear_slot and proto.get('wear_flags'):
            flags = proto['wear_flags']
            if isinstance(flags, list) and flags:
                obj.wear_slot = flags[0]  # Use first wear flag as slot
        obj.set_id = proto.get('set_id')
        obj.weight = proto.get('weight', 1)
        obj.cost = proto.get('cost', proto.get('value', 0))
        obj.value = obj.cost  # Alias for shop system compatibility
        obj.damage_dice = proto.get('damage_dice', '1d4')
        obj.weapon_type = proto.get('weapon_type', 'hit')
        obj.armor = proto.get('armor', 0)
        obj.capacity = proto.get('capacity', 0)
        obj.is_closed = proto.get('is_closed', proto.get('closed', False))  # Support both 'is_closed' and 'closed'
        obj.is_locked = proto.get('is_locked', proto.get('locked', False))  # Support both 'is_locked' and 'locked'
        obj.locked = obj.is_locked  # Backward compatibility
        obj.key_vnum = proto.get('key_vnum')
        obj.food_value = proto.get('food_value', 0)
        obj.food_bonus = proto.get('food_bonus')  # Rare food stat bonuses
        obj.food_message = proto.get('food_message')  # Custom message when eaten
        obj.drinks = proto.get('drinks', 0)
        obj.max_drinks = proto.get('max_drinks', obj.drinks)  # Default max to initial drinks
        obj.liquid = proto.get('liquid', 'water')
        obj.spell_effects = proto.get('spell_effects', [])
        obj.light_hours = proto.get('light_hours', 0)
        obj.affects = proto.get('affects', [])
        obj.flags = set(proto.get('flags', []))
        obj.lore_id = proto.get('lore_id')
        obj.lore_title = proto.get('lore_title')
        obj.lore_text = proto.get('lore_text')
        obj.lore_zone = proto.get('lore_zone')
        obj.readable_text = proto.get('readable_text')
        obj.water_speed = proto.get('water_speed', 0)
        obj.lock_difficulty = proto.get('lock_difficulty', 0)
        obj.pick_difficulty = proto.get('lock_difficulty', proto.get('pick_difficulty', 50))

        # Populate contents from 'contains' vnum list
        contains_vnums = proto.get('contains', [])
        if contains_vnums and world:
            for cvnum in contains_vnums:
                child = create_object(cvnum, world)
                if child:
                    obj.contents.append(child)

        return obj


def create_object(vnum: int, world: 'World' = None) -> Optional[Object]:
    """Create an object instance from the world's object prototypes."""
    if world and vnum in world.obj_prototypes:
        proto = world.obj_prototypes[vnum]
        return Object.from_prototype(proto, world)
    return None


# Preset item definitions for starting equipment
PRESET_OBJECTS = {
    1: {
        'vnum': 1,
        'name': 'a loaf of bread',
        'short_desc': 'a loaf of fresh bread',
        'room_desc': 'A loaf of bread lies here.',
        'description': 'A crusty loaf of fresh bread. It looks delicious.',
        'type': 'food',
        'weight': 1,
        'cost': 5,
        'food_value': 12,
    },
    2: {
        'vnum': 2,
        'name': 'a waterskin',
        'short_desc': 'a leather waterskin',
        'room_desc': 'A waterskin lies here.',
        'description': 'A leather waterskin, useful for carrying water.',
        'type': 'drink',
        'weight': 2,
        'cost': 10,
        'drinks': 20,
        'max_drinks': 20,
        'liquid': 'water',
    },
    3: {
        'vnum': 3,
        'name': 'a torch',
        'short_desc': 'a burning torch',
        'room_desc': 'A torch flickers on the ground.',
        'description': 'A wooden torch soaked in oil. It provides light in dark places.',
        'type': 'light',
        'weight': 1,
        'cost': 5,
        'light_hours': 24,
        'wear_slot': 'light',
    },
    10: {
        'vnum': 10,
        'name': 'a short sword',
        'short_desc': 'a short sword',
        'room_desc': 'A short sword lies here.',
        'description': 'A well-balanced short sword, good for beginners.',
        'type': 'weapon',
        'weight': 5,
        'cost': 50,
        'damage_dice': '1d6',
        'weapon_type': 'slash',
    },
    11: {
        'vnum': 11,
        'name': 'a dagger',
        'short_desc': 'a sharp dagger',
        'room_desc': 'A dagger glints on the ground.',
        'description': 'A keen-edged dagger, perfect for quick strikes.',
        'type': 'weapon',
        'weight': 2,
        'cost': 20,
        'damage_dice': '1d4',
        'weapon_type': 'stab',
    },
    12: {
        'vnum': 12,
        'name': 'a mace',
        'short_desc': 'a heavy mace',
        'room_desc': 'A mace lies here.',
        'description': 'A heavy mace with a flanged head.',
        'type': 'weapon',
        'weight': 8,
        'cost': 40,
        'damage_dice': '1d8',
        'weapon_type': 'pound',
    },
    13: {
        'vnum': 13,
        'name': 'a short bow',
        'short_desc': 'a short bow',
        'room_desc': 'A short bow lies here.',
        'description': 'A compact bow suitable for hunting.',
        'type': 'weapon',
        'weight': 3,
        'cost': 30,
        'damage_dice': '1d6',
        'weapon_type': 'pierce',
    },
    14: {
        'vnum': 14,
        'name': 'a rapier',
        'short_desc': 'an elegant rapier',
        'room_desc': 'A rapier lies here.',
        'description': 'A slender, elegant rapier designed for precise thrusts.',
        'type': 'weapon',
        'weight': 3,
        'cost': 60,
        'damage_dice': '1d6',
        'weapon_type': 'pierce',
    },
    # === STARTER EQUIPMENT (vnums 30-51) ===
    30: {'vnum': 30, 'name': 'an iron helmet', 'short_desc': 'an iron helmet',
         'room_desc': 'An iron helmet sits here.', 'type': 'armor', 'weight': 4, 'cost': 30,
         'armor': 3, 'wear_pos': 'head'},
    31: {'vnum': 31, 'name': 'a suit of chainmail', 'short_desc': 'a suit of chainmail',
         'room_desc': 'A suit of chainmail lies here.', 'type': 'armor', 'weight': 15, 'cost': 75,
         'armor': 5, 'wear_pos': 'body'},
    32: {'vnum': 32, 'name': 'iron greaves', 'short_desc': 'a pair of iron greaves',
         'room_desc': 'Iron greaves lie here.', 'type': 'armor', 'weight': 5, 'cost': 25,
         'armor': 2, 'wear_pos': 'legs'},
    33: {'vnum': 33, 'name': 'a wooden shield', 'short_desc': 'a wooden shield',
         'room_desc': 'A wooden shield lies here.', 'type': 'armor', 'weight': 6, 'cost': 20,
         'armor': 2, 'wear_pos': 'shield'},
    34: {'vnum': 34, 'name': 'a wooden staff', 'short_desc': 'a gnarled wooden staff',
         'room_desc': 'A wooden staff lies here.', 'type': 'weapon', 'weight': 4, 'cost': 15,
         'damage_dice': '1d6', 'weapon_type': 'pound'},
    35: {'vnum': 35, 'name': 'cloth robes', 'short_desc': 'simple cloth robes',
         'room_desc': 'Cloth robes lie here.', 'type': 'armor', 'weight': 3, 'cost': 10,
         'armor': 1, 'wear_pos': 'body'},
    36: {'vnum': 36, 'name': 'a spellbook', 'short_desc': 'a worn spellbook',
         'room_desc': 'A spellbook lies here.', 'type': 'other', 'weight': 2, 'cost': 25},
    37: {'vnum': 37, 'name': 'leather armor', 'short_desc': 'a suit of leather armor',
         'room_desc': 'Leather armor lies here.', 'type': 'armor', 'weight': 8, 'cost': 40,
         'armor': 3, 'wear_pos': 'body'},
    38: {'vnum': 38, 'name': 'a holy symbol', 'short_desc': 'a silver holy symbol',
         'room_desc': 'A holy symbol glints here.', 'type': 'other', 'weight': 1, 'cost': 15},
    39: {'vnum': 39, 'name': 'a leather jerkin', 'short_desc': 'a supple leather jerkin',
         'room_desc': 'A leather jerkin lies here.', 'type': 'armor', 'weight': 5, 'cost': 30,
         'armor': 2, 'wear_pos': 'body'},
    40: {'vnum': 40, 'name': 'lockpicks', 'short_desc': 'a set of lockpicks',
         'room_desc': 'A set of lockpicks lies here.', 'type': 'other', 'weight': 1, 'cost': 20},
    41: {'vnum': 41, 'name': 'studded leather', 'short_desc': 'a suit of studded leather',
         'room_desc': 'Studded leather armor lies here.', 'type': 'armor', 'weight': 10, 'cost': 50,
         'armor': 4, 'wear_pos': 'body'},
    42: {'vnum': 42, 'name': 'a quiver of arrows', 'short_desc': 'a quiver of arrows',
         'room_desc': 'A quiver of arrows lies here.', 'type': 'other', 'weight': 3, 'cost': 15},
    43: {'vnum': 43, 'name': 'a dark staff', 'short_desc': 'a staff of dark wood',
         'room_desc': 'A dark staff lies here.', 'type': 'weapon', 'weight': 5, 'cost': 20,
         'damage_dice': '1d6', 'weapon_type': 'pound'},
    44: {'vnum': 44, 'name': 'dark robes', 'short_desc': 'shadowy dark robes',
         'room_desc': 'Dark robes lie here.', 'type': 'armor', 'weight': 3, 'cost': 15,
         'armor': 1, 'wear_pos': 'body'},
    45: {'vnum': 45, 'name': 'an unholy symbol', 'short_desc': 'a tarnished unholy symbol',
         'room_desc': 'An unholy symbol lies here.', 'type': 'other', 'weight': 1, 'cost': 15},
    46: {'vnum': 46, 'name': 'a leather vest', 'short_desc': 'a stylish leather vest',
         'room_desc': 'A leather vest lies here.', 'type': 'armor', 'weight': 4, 'cost': 25,
         'armor': 2, 'wear_pos': 'body'},
    47: {'vnum': 47, 'name': 'a lute', 'short_desc': 'a well-crafted lute',
         'room_desc': 'A lute lies here.', 'type': 'other', 'weight': 3, 'cost': 30},
    48: {'vnum': 48, 'name': 'a stiletto', 'short_desc': 'a razor-sharp stiletto',
         'room_desc': 'A stiletto lies here.', 'type': 'weapon', 'weight': 1, 'cost': 40,
         'damage_dice': '1d4+1', 'weapon_type': 'stab'},
    49: {'vnum': 49, 'name': 'black leather armor', 'short_desc': 'fitted black leather armor',
         'room_desc': 'Black leather armor lies here.', 'type': 'armor', 'weight': 7, 'cost': 45,
         'armor': 3, 'wear_pos': 'body'},
    50: {'vnum': 50, 'name': 'a dark cloak', 'short_desc': 'a dark hooded cloak',
         'room_desc': 'A dark cloak lies here.', 'type': 'armor', 'weight': 2, 'cost': 20,
         'armor': 1, 'wear_pos': 'about'},
    51: {'vnum': 51, 'name': 'a poison vial', 'short_desc': 'a small vial of poison',
         'room_desc': 'A vial of poison sits here.', 'type': 'other', 'weight': 1, 'cost': 25},
    # === TUTORIAL REWARD ITEMS ===
    100: {
        'vnum': 100,
        'name': 'a minor healing potion',
        'short_desc': 'a small vial of red liquid',
        'room_desc': 'A small vial of red liquid sits here.',
        'description': 'A small glass vial filled with a glowing red liquid. It will restore a modest amount of health when quaffed.',
        'type': 'potion',
        'weight': 1,
        'cost': 15,
        'spell': 'cure light',
        'spell_level': 5,
    },
    101: {
        'vnum': 101,
        'name': 'a ration of travel bread',
        'short_desc': 'a ration of travel bread',
        'room_desc': 'A wrapped ration of bread lies here.',
        'description': 'A hearty ration of travel bread, wrapped in cloth to keep it fresh.',
        'type': 'food',
        'weight': 1,
        'cost': 8,
        'food_value': 18,
    },
    9010: {
        'vnum': 9010,
        'name': 'the Midgaard guard blade',
        'short_desc': 'the Midgaard guard blade',
        'room_desc': 'A polished guard blade rests here.',
        'description': 'A masterwork blade awarded to the most trusted defenders of Midgaard.',
        'type': 'weapon',
        'weight': 5,
        'cost': 2000,
        'damage_dice': '2d6',
        'weapon_type': 'slash',
    },
    9011: {
        'vnum': 9011,
        'name': 'the elven silverbow',
        'short_desc': 'the elven silverbow',
        'room_desc': 'A silver-threaded bow gleams here.',
        'description': 'An elegant bow of ancient elven make, humming with forest magic.',
        'type': 'weapon',
        'weight': 3,
        'cost': 2200,
        'damage_dice': '2d6',
        'weapon_type': 'pierce',
    },
    9012: {
        'vnum': 9012,
        'name': 'the dwarven warhammer',
        'short_desc': 'the dwarven warhammer',
        'room_desc': 'A rune-etched warhammer rests here.',
        'description': 'A heavy hammer forged in the deep halls, etched with protective runes.',
        'type': 'weapon',
        'weight': 8,
        'cost': 2300,
        'damage_dice': '2d7',
        'weapon_type': 'pound',
    },
    9013: {
        'vnum': 9013,
        'name': 'the dagger of silence',
        'short_desc': 'the dagger of silence',
        'room_desc': 'A matte-black dagger lies here.',
        'description': 'A blade that drinks the light around it, favored by the Thieves Guild.',
        'type': 'weapon',
        'weight': 2,
        'cost': 2100,
        'damage_dice': '2d5',
        'weapon_type': 'stab',
    },
    9014: {
        'vnum': 9014,
        'name': 'the staff of the Conclave',
        'short_desc': 'the staff of the Conclave',
        'room_desc': 'An arcane staff radiates power here.',
        'description': 'A staff bound with glowing sigils, gift of the Mages Guild.',
        'type': 'weapon',
        'weight': 4,
        'cost': 2400,
        'damage_dice': '2d4',
        'weapon_type': 'pound',
        'affects': [{'type': 'mana', 'value': 30}]
    },
    9200: {
        'vnum': 9200,
        'name': 'an ancient sun idol',
        'short_desc': 'an ancient sun idol',
        'room_desc': 'A gilded sun idol glows faintly here.',
        'description': 'An artifact of the old empire, warm to the touch and etched with solar runes.',
        'type': 'treasure',
        'weight': 2,
        'cost': 1200,
    },
    9201: {
        'vnum': 9201,
        'name': 'a shattered crown fragment',
        'short_desc': 'a shattered crown fragment',
        'room_desc': 'A shard of a regal crown lies here.',
        'description': 'A jagged piece of a once-mighty crown, still humming with forgotten power.',
        'type': 'treasure',
        'weight': 1,
        'cost': 1400,
    },
    9202: {
        'vnum': 9202,
        'name': 'a rune-etched obelisk chip',
        'short_desc': 'a rune-etched obelisk chip',
        'room_desc': 'A rune-etched stone chip rests here.',
        'description': 'A fragment of an ancient obelisk covered in warding glyphs.',
        'type': 'treasure',
        'weight': 3,
        'cost': 1100,
    },
    9203: {
        'vnum': 9203,
        'name': 'a relic of the deep forge',
        'short_desc': 'a relic of the deep forge',
        'room_desc': 'A darkened relic from a lost forge lies here.',
        'description': 'A heavy relic forged in the deep places, still radiating heat.',
        'type': 'treasure',
        'weight': 4,
        'cost': 1300,
    },
    9300: {
        'vnum': 9300,
        'name': 'a prismarine gem',
        'short_desc': 'a prismarine gem',
        'room_desc': 'A prismarine gem sparkles here.',
        'description': 'A multifaceted gem that catches light in impossible angles.',
        'type': 'treasure',
        'weight': 1,
        'cost': 900,
    },
    9301: {
        'vnum': 9301,
        'name': 'a storm opal',
        'short_desc': 'a storm opal',
        'room_desc': 'A storm opal swirls with inner lightning.',
        'description': 'A rare opal with a rolling, electric sheen.',
        'type': 'treasure',
        'weight': 1,
        'cost': 950,
    },
    9302: {
        'vnum': 9302,
        'name': 'a blood ruby',
        'short_desc': 'a blood ruby',
        'room_desc': 'A blood ruby gleams here.',
        'description': 'A rich ruby that seems to pulse with crimson light.',
        'type': 'treasure',
        'weight': 1,
        'cost': 980,
    },
    9303: {
        'vnum': 9303,
        'name': 'a star sapphire',
        'short_desc': 'a star sapphire',
        'room_desc': 'A star sapphire twinkles here.',
        'description': 'A deep sapphire with a luminous star at its core.',
        'type': 'treasure',
        'weight': 1,
        'cost': 1000,
    },
    9400: {
        'vnum': 9400,
        'name': 'a nightmare sigil',
        'short_desc': 'a nightmare sigil',
        'room_desc': 'A shadowy sigil pulses with dread.',
        'description': 'A token of your trials in New Game+, humming with dark power.',
        'type': 'treasure',
        'weight': 1,
        'cost': 1500,
    },
    # Watercraft - reduce water movement costs
    60: {
        'vnum': 60, 'name': 'a wooden raft',
        'short_desc': 'a crude wooden raft',
        'room_desc': 'A crude wooden raft is propped up here.',
        'description': 'A simple raft lashed together from logs and rope. It floats, barely. Better than swimming.',
        'item_type': 'boat', 'weight': 30, 'cost': 100,
        'water_speed': 0.5,  # 50% reduction
    },
    61: {
        'vnum': 61, 'name': 'a birch canoe',
        'short_desc': 'a lightweight birch canoe',
        'room_desc': 'A sleek birch canoe rests here.',
        'description': 'A well-crafted canoe carved from birch wood. Light enough to carry, fast enough to outrun most river currents.',
        'item_type': 'boat', 'weight': 20, 'cost': 500,
        'water_speed': 0.7,  # 70% reduction
    },
    62: {
        'vnum': 62, 'name': 'an elven skiff',
        'short_desc': 'an elegant elven skiff',
        'room_desc': 'An elegant elven skiff of pale wood sits here, barely touching the ground.',
        'description': 'This masterwork vessel was crafted by elven shipwrights. Its hull is impossibly thin yet strong, and faint enchantments make it glide through water with almost no effort. Even deep ocean crossings become trivial.',
        'item_type': 'boat', 'weight': 15, 'cost': 5000,
        'water_speed': 0.9,  # 90% reduction
        'flags': ['glow'],
    },
}


def create_preset_object(vnum: int) -> Optional[Object]:
    """Create an object from preset definitions."""
    if vnum in PRESET_OBJECTS:
        return Object.from_prototype(PRESET_OBJECTS[vnum])
    return None
