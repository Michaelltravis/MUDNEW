"""
RealmsMUD Configuration
=======================
Game settings and constants.
"""

import os

class Config:
    """Game configuration settings."""
    
    # Server Settings
    PORT = 4000
    HOST = '0.0.0.0'
    MAX_PLAYERS = 100
    TICKS_PER_SECOND = 10
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORLD_DIR = os.path.join(BASE_DIR, 'world')
    PLAYER_DIR = os.path.join(BASE_DIR, 'lib', 'players')
    LOG_DIR = os.path.join(BASE_DIR, 'log')
    
    # Game Settings
    STARTING_ROOM = 3001  # Temple of Midgaard equivalent
    VOID_ROOM = 1  # Limbo
    MORTAL_START_ROOM = 3001
    IMMORTAL_START_ROOM = 1200
    
    # Level Settings
    MAX_MORTAL_LEVEL = 50
    MAX_IMMORTAL_LEVEL = 60
    IMMORTAL_LEVEL = 51
    
    # Combat Settings
    PULSE_VIOLENCE = 2  # seconds between combat rounds
    PULSE_MOBILE = 10  # seconds between mob actions
    
    # Character Creation
    STARTING_GOLD = 100
    STARTING_EXPERIENCE = 0
    
    # Stat Limits
    MAX_STAT = 25
    MIN_STAT = 3
    
    # Experience multipliers by level
    EXP_MULTIPLIER = 1.5
    BASE_EXP = 1000
    
    # Regeneration rates (per tick)
    HP_REGEN_RATE = 0.05
    MANA_REGEN_RATE = 0.08
    MOVE_REGEN_RATE = 0.10
    
    # Colors (ANSI)
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
    }
    
    # Race definitions
    RACES = {
        'human': {
            'name': 'Human',
            'description': 'Versatile and adaptable, humans excel in all professions.',
            'stat_mods': {'str': 0, 'int': 0, 'wis': 0, 'dex': 0, 'con': 0, 'cha': 1},
            'size': 'medium',
            'abilities': ['quick_learner'],
        },
        'elf': {
            'name': 'Elf',
            'description': 'Graceful and wise, elves are masters of magic and archery.',
            'stat_mods': {'str': -1, 'int': 2, 'wis': 1, 'dex': 2, 'con': -2, 'cha': 1},
            'size': 'medium',
            'abilities': ['infravision', 'resist_charm'],
        },
        'dwarf': {
            'name': 'Dwarf',
            'description': 'Stout and hardy, dwarves are renowned warriors and craftsmen.',
            'stat_mods': {'str': 1, 'int': -1, 'wis': 1, 'dex': -1, 'con': 3, 'cha': -1},
            'size': 'small',
            'abilities': ['infravision', 'resist_poison', 'resist_magic'],
        },
        'halfling': {
            'name': 'Halfling',
            'description': 'Small and nimble, halflings are excellent thieves and scouts.',
            'stat_mods': {'str': -2, 'int': 0, 'wis': 0, 'dex': 3, 'con': 0, 'cha': 1},
            'size': 'small',
            'abilities': ['sneak_bonus', 'resist_fear'],
        },
        'half_orc': {
            'name': 'Half-Orc',
            'description': 'Strong and fierce, half-orcs are formidable warriors.',
            'stat_mods': {'str': 3, 'int': -2, 'wis': -1, 'dex': 0, 'con': 2, 'cha': -2},
            'size': 'medium',
            'abilities': ['infravision', 'berserk'],
        },
        'gnome': {
            'name': 'Gnome',
            'description': 'Clever and curious, gnomes have an affinity for illusion magic.',
            'stat_mods': {'str': -2, 'int': 2, 'wis': 0, 'dex': 1, 'con': 0, 'cha': 0},
            'size': 'small',
            'abilities': ['infravision', 'illusion_bonus'],
        },
        'dark_elf': {
            'name': 'Dark Elf',
            'description': 'Mysterious and deadly, dark elves wield shadow magic.',
            'stat_mods': {'str': 0, 'int': 2, 'wis': 0, 'dex': 2, 'con': -1, 'cha': -1},
            'size': 'medium',
            'abilities': ['infravision', 'faerie_fire', 'light_sensitivity'],
        },
    }
    
    # Class definitions
    CLASSES = {
        'warrior': {
            'name': 'Warrior',
            'description': 'Masters of combat, warriors excel in melee and defense.',
            'prime_stat': 'str',
            'hit_dice': 12,
            'mana_dice': 2,
            'move_dice': 6,
            'thac0_progression': 'fast',
            'save_progression': 'warrior',
            'skills': ['kick', 'bash', 'rescue', 'disarm', 'second_attack', 'third_attack', 'parry'],
            'spells': [],
        },
        'mage': {
            'name': 'Mage',
            'description': 'Wielders of arcane power, mages command devastating spells.',
            'prime_stat': 'int',
            'hit_dice': 4,
            'mana_dice': 12,
            'move_dice': 4,
            'thac0_progression': 'slow',
            'save_progression': 'mage',
            'skills': ['scribe'],
            'spells': ['magic_missile', 'burning_hands', 'chill_touch', 'fireball', 'lightning_bolt',
                      'sleep', 'color_spray', 'teleport', 'fly', 'invisibility', 'detect_magic',
                      'identify', 'enchant_weapon', 'meteor_swarm', 'chain_lightning'],
        },
        'cleric': {
            'name': 'Cleric',
            'description': 'Divine servants who heal allies and smite the undead.',
            'prime_stat': 'wis',
            'hit_dice': 8,
            'mana_dice': 8,
            'move_dice': 4,
            'thac0_progression': 'medium',
            'save_progression': 'cleric',
            'skills': ['turn_undead'],
            'spells': ['cure_light', 'cure_serious', 'cure_critical', 'heal', 'group_heal',
                      'bless', 'armor', 'sanctuary', 'remove_curse', 'remove_poison',
                      'create_food', 'create_water', 'summon', 'word_of_recall', 'resurrect',
                      'harm', 'dispel_evil', 'earthquake', 'flamestrike'],
        },
        'thief': {
            'name': 'Thief',
            'description': 'Cunning rogues who strike from the shadows.',
            'prime_stat': 'dex',
            'hit_dice': 6,
            'mana_dice': 2,
            'move_dice': 8,
            'thac0_progression': 'medium',
            'save_progression': 'thief',
            'skills': ['backstab', 'sneak', 'hide', 'steal', 'pick_lock', 'detect_traps',
                      'second_attack', 'trip', 'circle'],
            'spells': [],
        },
        'ranger': {
            'name': 'Ranger',
            'description': 'Wilderness warriors who blend combat prowess with nature magic.',
            'prime_stat': 'dex',
            'hit_dice': 10,
            'mana_dice': 4,
            'move_dice': 8,
            'thac0_progression': 'fast',
            'save_progression': 'warrior',
            'skills': ['track', 'sneak', 'hide', 'second_attack', 'dual_wield'],
            'spells': ['cure_light', 'detect_magic', 'faerie_fire', 'call_lightning',
                      'barkskin', 'entangle'],
        },
        'paladin': {
            'name': 'Paladin',
            'description': 'Holy warriors who combine martial skill with divine power.',
            'prime_stat': 'str',
            'hit_dice': 10,
            'mana_dice': 4,
            'move_dice': 4,
            'thac0_progression': 'fast',
            'save_progression': 'warrior',
            'skills': ['rescue', 'bash', 'lay_hands', 'turn_undead', 'second_attack'],
            'spells': ['cure_light', 'cure_serious', 'bless', 'detect_evil', 'protection_from_evil'],
        },
        'necromancer': {
            'name': 'Necromancer',
            'description': 'Dark mages who command the forces of death and undeath.',
            'prime_stat': 'int',
            'hit_dice': 4,
            'mana_dice': 10,
            'move_dice': 4,
            'thac0_progression': 'slow',
            'save_progression': 'mage',
            'skills': [],
            'spells': ['chill_touch', 'animate_dead', 'vampiric_touch', 'enervation',
                      'death_grip', 'summon_undead', 'finger_of_death', 'energy_drain',
                      'poison', 'weaken', 'blindness', 'fear'],
        },
        'bard': {
            'name': 'Bard',
            'description': 'Charismatic performers who inspire allies with magical songs.',
            'prime_stat': 'cha',
            'hit_dice': 6,
            'mana_dice': 6,
            'move_dice': 6,
            'thac0_progression': 'medium',
            'save_progression': 'thief',
            'skills': ['sneak', 'pick_lock', 'lore'],
            'spells': ['charm_person', 'sleep', 'invisibility', 'haste', 'slow',
                      'cure_light', 'detect_magic', 'heroism', 'fear', 'mass_charm'],
        },
        'assassin': {
            'name': 'Assassin',
            'description': 'Deadly killers who specialize in eliminating targets with lethal precision.',
            'prime_stat': 'dex',
            'hit_dice': 8,
            'mana_dice': 2,
            'move_dice': 10,
            'thac0_progression': 'fast',
            'save_progression': 'thief',
            'skills': ['backstab', 'sneak', 'hide', 'envenom', 'assassinate',
                      'second_attack', 'dual_wield', 'garrote', 'shadow_step', 'mark_target'],
            'spells': [],
        },
    }
    
    # Equipment slots
    WEAR_SLOTS = [
        'light',      # Light source
        'finger1',    # First ring
        'finger2',    # Second ring  
        'neck1',      # First neck slot
        'neck2',      # Second neck slot
        'body',       # Body armor
        'head',       # Helmet
        'legs',       # Leg armor
        'feet',       # Boots
        'hands',      # Gloves
        'arms',       # Arm guards
        'shield',     # Shield
        'about',      # Cloak/cape
        'waist',      # Belt
        'wrist1',     # First wrist
        'wrist2',     # Second wrist
        'wield',      # Main weapon
        'hold',       # Held item
        'dual_wield', # Off-hand weapon
    ]
    
    # Item types
    ITEM_TYPES = [
        'light', 'scroll', 'wand', 'staff', 'weapon', 'treasure', 'armor',
        'potion', 'worn', 'other', 'trash', 'container', 'note', 'drink',
        'key', 'food', 'money', 'boat', 'fountain', 'portal'
    ]
    
    # Weapon types
    WEAPON_TYPES = [
        'hit', 'sting', 'whip', 'slash', 'bite', 'bludgeon', 'crush',
        'pound', 'claw', 'maul', 'thrash', 'pierce', 'blast', 'punch',
        'stab', 'slice', 'cleave', 'smash'
    ]
    
    # Sector types (terrain)
    SECTOR_TYPES = {
        'inside': {'move_cost': 1, 'description': 'Indoors'},
        'city': {'move_cost': 1, 'description': 'City streets'},
        'field': {'move_cost': 2, 'description': 'Open field'},
        'forest': {'move_cost': 3, 'description': 'Dense forest'},
        'hills': {'move_cost': 4, 'description': 'Rolling hills'},
        'mountain': {'move_cost': 6, 'description': 'Steep mountains'},
        'water_swim': {'move_cost': 4, 'description': 'Shallow water'},
        'water_noswim': {'move_cost': 100, 'description': 'Deep water'},
        'underwater': {'move_cost': 5, 'description': 'Underwater'},
        'flying': {'move_cost': 1, 'description': 'Flying'},
        'desert': {'move_cost': 4, 'description': 'Arid desert'},
        'swamp': {'move_cost': 5, 'description': 'Murky swamp'},
        'dungeon': {'move_cost': 2, 'description': 'Dungeon corridor'},
    }
    
    # Position states
    POSITIONS = ['dead', 'mortally_wounded', 'incapacitated', 'stunned',
                 'sleeping', 'resting', 'sitting', 'fighting', 'standing']
    
    # Directions
    DIRECTIONS = {
        'north': {'opposite': 'south', 'abbrev': 'n'},
        'east': {'opposite': 'west', 'abbrev': 'e'},
        'south': {'opposite': 'north', 'abbrev': 's'},
        'west': {'opposite': 'east', 'abbrev': 'w'},
        'up': {'opposite': 'down', 'abbrev': 'u'},
        'down': {'opposite': 'up', 'abbrev': 'd'},
    }
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        for directory in [cls.PLAYER_DIR, cls.LOG_DIR]:
            os.makedirs(directory, exist_ok=True)

# Create directories on import
Config.ensure_directories()
