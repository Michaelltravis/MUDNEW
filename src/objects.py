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
        self.weight = 1
        self.cost = 0
        
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
        
        # Consumable properties
        self.food_value = 0
        self.drinks = 0
        self.liquid = "water"
        self.spell_effects = []
        
        # Light properties
        self.light_hours = 0
        
        # Magical properties
        self.affects = []  # [{type, value}, ...]
        self.flags = set()
        
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
            'liquid': self.liquid,
            'spell_effects': self.spell_effects,
            'light_hours': self.light_hours,
            'affects': self.affects,
            'flags': list(self.flags),
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
        obj.weight = data.get('weight', 1)
        obj.cost = data.get('cost', 0)
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
        obj.liquid = data.get('liquid', 'water')
        obj.spell_effects = data.get('spell_effects', [])
        obj.light_hours = data.get('light_hours', 0)
        obj.affects = data.get('affects', [])
        obj.flags = set(data.get('flags', []))
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
        obj.item_type = proto.get('type', 'other')
        obj.wear_slot = proto.get('wear_slot')
        obj.weight = proto.get('weight', 1)
        obj.cost = proto.get('cost', 0)
        obj.damage_dice = proto.get('damage_dice', '1d4')
        obj.weapon_type = proto.get('weapon_type', 'hit')
        obj.armor = proto.get('armor', 0)
        obj.capacity = proto.get('capacity', 0)
        obj.is_closed = proto.get('is_closed', proto.get('closed', False))  # Support both 'is_closed' and 'closed'
        obj.is_locked = proto.get('is_locked', proto.get('locked', False))  # Support both 'is_locked' and 'locked'
        obj.locked = obj.is_locked  # Backward compatibility
        obj.key_vnum = proto.get('key_vnum')
        obj.food_value = proto.get('food_value', 0)
        obj.drinks = proto.get('drinks', 0)
        obj.liquid = proto.get('liquid', 'water')
        obj.spell_effects = proto.get('spell_effects', [])
        obj.light_hours = proto.get('light_hours', 0)
        obj.affects = proto.get('affects', [])
        obj.flags = set(proto.get('flags', []))

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
}


def create_preset_object(vnum: int) -> Optional[Object]:
    """Create an object from preset definitions."""
    if vnum in PRESET_OBJECTS:
        return Object.from_prototype(PRESET_OBJECTS[vnum])
    return None
