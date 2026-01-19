"""
RealmsMUD Player
================
Player character class with stats, combat, inventory, etc.
"""

import json
import os
import hashlib
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world import World
    from room import Room

from config import Config
from affects import AffectManager
from regeneration import RegenerationCalculator

logger = logging.getLogger('RealmsMUD.Player')

class Character:
    """Base class for all characters (players and NPCs)."""
    
    def __init__(self):
        self.name = "Unknown"
        self.room = None
        self.hp = 100
        self.max_hp = 100
        self.mana = 100
        self.max_mana = 100
        self.move = 100
        self.max_move = 100
        
        # Stats
        self.str = 10
        self.int = 10
        self.wis = 10
        self.dex = 10
        self.con = 10
        self.cha = 10
        
        # Combat
        self.level = 1
        self.exp = 0
        self.gold = 0
        self.alignment = 0
        self.armor_class = 100
        self.hitroll = 0
        self.damroll = 0
        
        # State
        self.position = 'standing'
        self.fighting = None
        
        # Equipment and inventory
        self.inventory = []
        self.equipment = {}

        # Affects
        self.affects = []
        self.affect_flags = set()  # Flags applied by affects (sanctuary, invisible, etc.)
        
    @property
    def is_alive(self):
        return self.hp > 0
        
    @property
    def is_fighting(self):
        return self.fighting is not None
        
    def get_hit_bonus(self):
        """Calculate total hit bonus (to hit / THAC0)."""
        bonus = self.hitroll

        # DEX is primary factor for accuracy (dodging, precision)
        bonus += (self.dex - 10) // 2

        # STR provides minor bonus (raw power helping land blows)
        bonus += (self.str - 10) // 4

        # INT provides bonus for tactical awareness (mainly for casters)
        if hasattr(self, 'char_class'):
            if self.char_class in ['Mage', 'Necromancer', 'Cleric']:
                bonus += (self.int - 10) // 3

        return bonus

    def get_damage_bonus(self):
        """Calculate total damage bonus."""
        bonus = self.damroll

        # STR is primary factor for damage
        bonus += (self.str - 10) // 2

        # DEX provides minor damage bonus (precision strikes for finesse classes)
        if hasattr(self, 'char_class'):
            if self.char_class in ['Thief', 'Assassin', 'Ranger']:
                bonus += (self.dex - 10) // 5

        return bonus
        
    def get_armor_class(self):
        """Calculate effective armor class."""
        ac = self.armor_class
        ac -= (self.dex - 10) // 2 * 10  # Dexterity bonus
        
        # Equipment bonuses
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'armor'):
                ac -= item.armor
                
        return max(ac, -100)  # Cap at -100


class Player(Character):
    """Player character class."""
    
    def __init__(self, world: 'World'):
        super().__init__()
        self.world = world
        self.config = Config()
        self.connection = None
        
        # Player-specific attributes
        self.password_hash = ""
        self.race = "human"
        self.char_class = "warrior"
        self.title = "the Adventurer"
        
        self.room_vnum = self.config.STARTING_ROOM
        
        # Progression
        self.practices = 0
        self.trains = 0
        
        # Skills and spells
        self.skills = {}
        self.spells = {}
        
        # Quest tracking
        self.quests_completed = []
        self.quest_flags = {}
        self.active_quests = []  # List of ActiveQuest objects

        # Group/following
        self.group = None  # Group object if in a group
        self.following = None  # Player being followed

        # Player flags
        self.flags = set()

        # Command system
        self.last_command = ""  # For ! repeat
        self.custom_aliases = {}  # Personal alias system
        self.target = None  # Current combat target for targeting system

        # Autoloot settings
        self.autoloot = False  # Automatically loot items from corpses
        self.autoloot_gold = True  # Automatically loot gold (default on)

        # Recall system
        self.recall_point = 3001  # Default recall point (Temple of Midgaard)
        self.autorecall_hp = None  # HP threshold for automatic recall
        self.autorecall_is_percent = False  # Whether autorecall_hp is a percentage

        # Hunger/Thirst System (game-time based, realistic timescales)
        self.hunger = 168  # Max 168 game hours = 1 week (0 = starving)
        self.thirst = 60  # Max 60 game hours = 2.5 days (0 = dying of thirst)
        self.max_hunger = 168
        self.max_thirst = 60
        self.last_hunger_hour = 0  # Track last game hour for hunger
        self.last_thirst_hour = 0  # Track last game hour for thirst

        # Mount System
        self.mount = None  # Currently mounted creature
        self.owned_mounts = []  # List of owned mount vnums

        # Rent/Storage System
        self.storage = []  # Items in storage (inn locker)
        self.storage_location = None  # Room vnum where storage is located

        # Timestamps
        self.created_at = datetime.now()
        self.last_login = datetime.now()
        self.total_playtime = 0
        
    @classmethod
    def create_new(cls, name: str, password: str, race: str, char_class: str, 
                   stats: Dict[str, int], world: 'World') -> 'Player':
        """Create a new player character."""
        player = cls(world)
        player.name = name
        player.set_password(password)
        player.race = race
        player.char_class = char_class
        
        # Set stats
        player.str = stats['str']
        player.int = stats['int']
        player.wis = stats['wis']
        player.dex = stats['dex']
        player.con = stats['con']
        player.cha = stats['cha']
        
        # Calculate derived stats based on class
        class_data = player.config.CLASSES[char_class]
        # HP: 12-22 range based on class and constitution
        player.max_hp = 12 + class_data['hit_dice'] // 2 + (player.con - 10) // 2
        # Mana: ~100 base, scales with INT + WIS
        player.max_mana = 100 + class_data['mana_dice'] * 5 + (player.int + player.wis - 20) * 2
        # Moves: 100+ base, scales with constitution
        player.max_move = 100 + class_data['move_dice'] * 5 + player.con * 2
        
        player.hp = player.max_hp
        player.mana = player.max_mana
        player.move = player.max_move
        
        # Starting resources
        player.gold = player.config.STARTING_GOLD
        player.exp = player.config.STARTING_EXPERIENCE
        player.practices = 5
        player.trains = 0
        
        # Learn starting skills/spells
        for skill in class_data['skills'][:3]:  # First 3 skills
            player.skills[skill] = 50  # 50% proficiency
        for spell in class_data['spells'][:2]:  # First 2 spells
            player.spells[spell] = 50
            
        # Give starting equipment
        player._give_starting_equipment()
        
        logger.info(f"Created new character: {name} ({race} {char_class})")
        return player
        
    def _give_starting_equipment(self):
        """Give starting equipment based on class."""
        from objects import create_object

        # Everyone gets basic items
        bread = create_object(1)  # Bread
        if bread:
            self.inventory.append(bread)

        waterskin = create_object(2)  # Waterskin
        if waterskin:
            self.inventory.append(waterskin)

        torch = create_object(3)  # Torch
        if torch:
            self.inventory.append(torch)

        # Class-specific equipment sets
        equipment_sets = {
            'warrior': {
                'wield': 10,    # Short sword
                'head': 30,     # Iron helmet
                'body': 31,     # Chainmail
                'legs': 32,     # Iron greaves
                'shield': 33,   # Wooden shield
            },
            'mage': {
                'wield': 34,    # Wooden staff
                'body': 35,     # Cloth robes
                'hold': 36,     # Spellbook
            },
            'cleric': {
                'wield': 12,    # Mace
                'body': 37,     # Leather armor
                'neck1': 38,    # Holy symbol
            },
            'thief': {
                'wield': 11,    # Dagger
                'body': 39,     # Leather jerkin
                'hold': 40,     # Lockpicks
            },
            'ranger': {
                'wield': 13,    # Short bow
                'body': 41,     # Studded leather
                'hold': 42,     # Quiver of arrows
            },
            'paladin': {
                'wield': 10,    # Short sword
                'body': 31,     # Chainmail
                'shield': 33,   # Wooden shield
                'neck1': 38,    # Holy symbol
            },
            'necromancer': {
                'wield': 43,    # Dark staff
                'body': 44,     # Dark robes
                'neck1': 45,    # Unholy symbol
            },
            'bard': {
                'wield': 14,    # Rapier
                'body': 46,     # Leather vest
                'hold': 47,     # Lute
            },
            'assassin': {
                'wield': 48,    # Stiletto
                'body': 49,     # Black leather armor
                'about': 50,    # Dark cloak
                'hold': 51,     # Poison vial
            },
        }

        # Equip class-specific gear
        class_equipment = equipment_sets.get(self.char_class, {})
        for slot, vnum in class_equipment.items():
            item = create_object(vnum)
            if item:
                self.equipment[slot] = item
            
    def set_password(self, password: str):
        """Set the player's password (hashed)."""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        
    def check_password(self, password: str) -> bool:
        """Check if the password matches."""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
        
    async def send(self, message: str, newline: bool = True):
        """Send a message to the player."""
        if self.connection:
            await self.connection.send(message, newline)
            
    def _save_companions(self) -> List[Dict]:
        """Save persistent companions to dict format."""
        if not hasattr(self, 'companions'):
            return []

        companions_data = []
        from pets import Pet

        for companion in self.companions:
            if isinstance(companion, Pet) and companion.is_persistent:
                comp_data = {
                    'name': companion.name,
                    'short_desc': companion.short_desc,
                    'long_desc': companion.long_desc,
                    'level': companion.level,
                    'hp': companion.hp,
                    'max_hp': companion.max_hp,
                    'damage_dice': companion.damage_dice,
                    'loyalty': companion.loyalty,
                    'experience': companion.experience,
                    'pet_level': companion.pet_level,
                }
                companions_data.append(comp_data)

        return companions_data

    async def save(self):
        """Save the player to disk."""
        data = {
            'name': self.name,
            'password_hash': self.password_hash,
            'race': self.race,
            'char_class': self.char_class,
            'title': self.title,
            'level': self.level,
            'exp': self.exp,
            'gold': self.gold,
            'alignment': self.alignment,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'mana': self.mana,
            'max_mana': self.max_mana,
            'move': self.move,
            'max_move': self.max_move,
            'str': self.str,
            'int': self.int,
            'wis': self.wis,
            'dex': self.dex,
            'con': self.con,
            'cha': self.cha,
            'armor_class': self.armor_class,
            'hitroll': self.hitroll,
            'damroll': self.damroll,
            'practices': self.practices,
            'trains': self.trains,
            'room_vnum': self.room.vnum if self.room else self.config.STARTING_ROOM,
            'skills': self.skills,
            'spells': self.spells,
            'quests_completed': self.quests_completed,
            'quest_flags': self.quest_flags,
            'active_quests': [q.to_dict() for q in self.active_quests],
            'flags': list(self.flags),
            'inventory': [item.to_dict() for item in self.inventory],
            'equipment': {slot: item.to_dict() if item else None
                         for slot, item in self.equipment.items()},
            'affects': AffectManager.save_affects(self),
            'companions': self._save_companions(),
            'custom_aliases': self.custom_aliases,
            'autoloot': self.autoloot,
            'autoloot_gold': self.autoloot_gold,
            'recall_point': self.recall_point,
            'autorecall_hp': self.autorecall_hp,
            'autorecall_is_percent': self.autorecall_is_percent,
            'hunger': self.hunger,
            'thirst': self.thirst,
            'max_hunger': self.max_hunger,
            'max_thirst': self.max_thirst,
            'last_hunger_hour': self.last_hunger_hour,
            'last_thirst_hour': self.last_thirst_hour,
            'owned_mounts': self.owned_mounts,
            'storage': [item.to_dict() for item in self.storage],
            'storage_location': self.storage_location,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat(),
            'total_playtime': self.total_playtime,
        }
        
        filepath = os.path.join(self.config.PLAYER_DIR, f"{self.name.lower()}.json")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.debug(f"Saved player: {self.name}")
        
    @classmethod
    def load(cls, name: str, world: 'World') -> Optional['Player']:
        """Load a player from disk."""
        filepath = os.path.join(Config.PLAYER_DIR, f"{name.lower()}.json")
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            player = cls(world)
            
            # Load all attributes
            player.name = data['name']
            player.password_hash = data['password_hash']
            player.race = data['race']
            player.char_class = data['char_class']
            player.title = data.get('title', 'the Adventurer')
            player.level = data['level']
            player.exp = data['exp']
            player.gold = data['gold']
            player.alignment = data.get('alignment', 0)
            player.hp = data['hp']
            player.max_hp = data['max_hp']
            player.mana = data['mana']
            player.max_mana = data['max_mana']
            player.move = data['move']
            player.max_move = data['max_move']
            player.str = data['str']
            player.int = data['int']
            player.wis = data['wis']
            player.dex = data['dex']
            player.con = data['con']
            player.cha = data['cha']
            player.armor_class = data.get('armor_class', 100)
            player.hitroll = data.get('hitroll', 0)
            player.damroll = data.get('damroll', 0)
            player.practices = data.get('practices', 0)
            player.trains = data.get('trains', 0)
            player.room_vnum = data.get('room_vnum', Config.STARTING_ROOM)
            player.skills = data.get('skills', {})
            player.spells = data.get('spells', {})
            player.quests_completed = data.get('quests_completed', [])
            player.quest_flags = data.get('quest_flags', {})

            # Load active quests
            from quests import ActiveQuest
            player.active_quests = [ActiveQuest.from_dict(q) for q in data.get('active_quests', [])]

            player.flags = set(data.get('flags', []))
            player.custom_aliases = data.get('custom_aliases', {})
            player.autoloot = data.get('autoloot', False)
            player.autoloot_gold = data.get('autoloot_gold', True)
            player.recall_point = data.get('recall_point', 3001)
            player.autorecall_hp = data.get('autorecall_hp', None)
            player.autorecall_is_percent = data.get('autorecall_is_percent', False)
            player.hunger = data.get('hunger', 168)
            player.thirst = data.get('thirst', 60)
            player.max_hunger = data.get('max_hunger', 168)
            player.max_thirst = data.get('max_thirst', 60)
            player.last_hunger_hour = data.get('last_hunger_hour', 0)
            player.last_thirst_hour = data.get('last_thirst_hour', 0)
            player.owned_mounts = data.get('owned_mounts', [])

            # Load storage
            player.storage = [Object.from_dict(item_data, world)
                            for item_data in data.get('storage', [])
                            if item_data]
            player.storage_location = data.get('storage_location', None)

            # Load affects using AffectManager
            affects_data = data.get('affects', [])
            if affects_data and isinstance(affects_data[0], dict) if affects_data else False:
                # New format - use AffectManager
                AffectManager.load_affects(player, affects_data)
            else:
                # Old format - clear old broken affects
                player.affects = []
                player.affect_flags = set()

            # Load inventory
            from objects import Object
            player.inventory = [Object.from_dict(item_data, world) 
                               for item_data in data.get('inventory', [])
                               if item_data]
            
            # Load equipment
            player.equipment = {}
            for slot, item_data in data.get('equipment', {}).items():
                if item_data:
                    player.equipment[slot] = Object.from_dict(item_data, world)
                else:
                    player.equipment[slot] = None

            # Load companions (persistent pets)
            player.companions = []
            companions_data = data.get('companions', [])
            if companions_data:
                from pets import Pet
                for comp_data in companions_data:
                    # Create pet from saved data
                    pet = Pet(0, world, player, 'companion')
                    pet.name = comp_data['name']
                    pet.short_desc = comp_data['short_desc']
                    pet.long_desc = comp_data['long_desc']
                    pet.level = comp_data['level']
                    pet.hp = comp_data['hp']
                    pet.max_hp = comp_data['max_hp']
                    pet.damage_dice = comp_data['damage_dice']
                    pet.loyalty = comp_data.get('loyalty', 100)
                    pet.experience = comp_data.get('experience', 0)
                    pet.pet_level = comp_data.get('pet_level', 1)
                    pet.is_persistent = True

                    player.companions.append(pet)
                    # Companions will be added to world when player enters game

            # Parse timestamps
            player.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
            player.last_login = datetime.now()
            player.total_playtime = data.get('total_playtime', 0)
            
            logger.info(f"Loaded player: {player.name}")
            return player
            
        except Exception as e:
            logger.error(f"Error loading player {name}: {e}")
            return None
            
    async def execute_command(self, cmd: str, args: List[str]):
        """Execute a player command."""
        from commands import CommandHandler
        await CommandHandler.execute(self, cmd, args)
        
    async def do_look(self, args: List[str]):
        """Look at the room or an object."""
        if not self.room:
            await self.send("You are floating in the void...")
            return

        # Can't see anything while sleeping
        if self.position == 'sleeping':
            await self.send("You can't see anything, you're sleeping!")
            return

        if not args:
            # Look at room
            await self.room.show_to(self)
        else:
            # Check for "look in <container>" syntax
            args_str = ' '.join(args).lower()
            if args_str.startswith('in ') or ' in ' in args_str:
                # Handle both "in chest" and "item in chest" patterns
                if args_str.startswith('in '):
                    container_name = args_str[3:].strip()  # Remove "in " from start
                else:
                    parts = args_str.split(' in ', 1)
                    container_name = parts[1].strip()

                # Find container in room or inventory
                container = None
                for item in self.inventory + self.room.items:
                    if container_name in item.name.lower():
                        if hasattr(item, 'item_type') and item.item_type == 'container':
                            container = item
                            break

                if not container:
                    await self.send(f"You don't see a '{container_name}' container here.")
                    return

                # Check if container is closed
                if hasattr(container, 'is_closed') and container.is_closed:
                    await self.send(f"The {container.short_desc} is closed.")
                    return

                # Show container contents
                c = self.config.COLORS
                await self.send(f"{c['cyan']}Inside {container.short_desc}:{c['reset']}")

                # Check for gold
                if hasattr(container, 'gold') and container.gold > 0:
                    await self.send(f"  {c['yellow']}{container.gold} gold coins{c['reset']}")

                # Check for items
                if hasattr(container, 'contents') and container.contents:
                    for cont_item in container.contents:
                        await self.send(f"  {cont_item.short_desc}")
                elif not hasattr(container, 'gold') or container.gold == 0:
                    await self.send(f"  {c['white']}Nothing.{c['reset']}")

                return

            # Look at something specific
            target = ' '.join(args)

            # Check directions FIRST - look into adjacent rooms
            if target in self.config.DIRECTIONS:
                exit_data = self.room.exits.get(target)
                if not exit_data:
                    await self.send("There is no exit in that direction.")
                    return

                c = self.config.COLORS

                # Check for closed door
                if 'door' in exit_data:
                    door = exit_data['door']
                    if door.get('state') == 'closed':
                        door_name = door.get('name', 'door')
                        await self.send(f"{c['yellow']}The {door_name} is closed.{c['reset']}")
                        return

                # Look into the next room
                next_room = exit_data.get('room')
                if next_room:
                    await self.send(f"{c['cyan']}You look {target}...{c['reset']}\n")
                    await self.send(f"{c['bright_yellow']}{next_room.name}{c['reset']}")

                    # Show exit description if available
                    exit_desc = exit_data.get('description', '')
                    if exit_desc:
                        await self.send(f"{c['white']}{exit_desc}{c['reset']}")

                    # Show brief room description (first 2 sentences or 200 chars)
                    desc = next_room.description
                    if desc:
                        # Get first two sentences
                        sentences = desc.split('.')
                        if len(sentences) >= 2:
                            brief_desc = sentences[0] + '.' + sentences[1] + '.'
                        else:
                            brief_desc = sentences[0] + '.'
                        if len(brief_desc) > 200:
                            brief_desc = desc[:200] + '...'
                        await self.send(f"{c['white']}{brief_desc}{c['reset']}")
                    elif not exit_desc:
                        # No description at all - generate generic one from room name
                        await self.send(f"{c['white']}You see {next_room.name.lower()}.{c['reset']}")

                    # Show characters in that room
                    if next_room.characters:
                        await self.send(f"\n{c['green']}You see:{c['reset']}")
                        for char in next_room.characters:
                            if hasattr(char, 'short_desc'):
                                await self.send(f"  {char.short_desc}")
                            else:
                                await self.send(f"  {char.name}")

                    # Show obvious items
                    if next_room.items:
                        item_count = len(next_room.items)
                        if item_count > 0:
                            await self.send(f"{c['yellow']}You notice {item_count} item(s) there.{c['reset']}")
                else:
                    # Room not linked - try to fetch by vnum
                    to_room = exit_data.get('to_room')
                    if to_room and hasattr(self, 'world') and self.world:
                        next_room = self.world.rooms.get(to_room)
                        if next_room:
                            await self.send(f"{c['cyan']}You look {target}...{c['reset']}\n")
                            await self.send(f"{c['bright_yellow']}{next_room.name}{c['reset']}")
                            if next_room.description:
                                brief_desc = next_room.description[:200]
                                if len(next_room.description) > 200:
                                    brief_desc += '...'
                                await self.send(f"{c['white']}{brief_desc}{c['reset']}")
                            return
                    # Fallback to exit description
                    desc = exit_data.get('description', '')
                    if desc:
                        await self.send(f"You see {desc}.")
                    else:
                        await self.send(f"You see an exit leading {target}.")
                return

            # Check characters in room
            for char in self.room.characters:
                if char != self and target.lower() in char.name.lower():
                    await self.show_character(char)
                    return

            # Check items in inventory
            for item in self.inventory:
                if target.lower() in item.name.lower():
                    await self.send(item.get_description())
                    # If it's a container, show contents too
                    if hasattr(item, 'item_type') and item.item_type == 'container':
                        await self._show_container_contents(item)
                    return

            # Check items in room
            for item in self.room.items:
                if target.lower() in item.name.lower():
                    await self.send(item.get_description())
                    # If it's a container, show contents too
                    if hasattr(item, 'item_type') and item.item_type == 'container':
                        await self._show_container_contents(item)
                    return

            await self.send(f"You don't see '{target}' here.")

    async def _show_container_contents(self, container):
        """Show what's inside a container."""
        c = self.config.COLORS

        # Check if container is closed
        if hasattr(container, 'is_closed') and container.is_closed:
            await self.send(f"{c['yellow']}The {container.short_desc} is closed.{c['reset']}")
            return

        await self.send(f"\n{c['cyan']}Inside {container.short_desc}:{c['reset']}")

        has_contents = False

        # Check for gold
        if hasattr(container, 'gold') and container.gold > 0:
            await self.send(f"  {c['yellow']}{container.gold} gold coins{c['reset']}")
            has_contents = True

        # Check for items
        if hasattr(container, 'contents') and container.contents:
            for cont_item in container.contents:
                await self.send(f"  {cont_item.short_desc}")
            has_contents = True

        if not has_contents:
            await self.send(f"  {c['white']}Nothing.{c['reset']}")

    async def show_character(self, char: 'Character'):
        """Show details about a character."""
        c = self.config.COLORS
        
        if hasattr(char, 'long_desc'):
            await self.send(char.long_desc)
        else:
            await self.send(f"You see {char.name}.")
            
        # Show condition
        hp_pct = char.hp / char.max_hp if char.max_hp > 0 else 0
        if hp_pct >= 1.0:
            condition = "is in excellent condition"
        elif hp_pct >= 0.9:
            condition = "has a few scratches"
        elif hp_pct >= 0.75:
            condition = "has some small wounds"
        elif hp_pct >= 0.5:
            condition = "has quite a few wounds"
        elif hp_pct >= 0.30:
            condition = "has some big nasty wounds"
        elif hp_pct >= 0.15:
            condition = "looks pretty hurt"
        else:
            condition = "is in awful condition"
            
        await self.send(f"{c['white']}{char.name} {condition}.{c['reset']}")
        
        # Show equipment if player
        if hasattr(char, 'equipment') and char.equipment:
            await self.send(f"{c['cyan']}{char.name} is using:{c['reset']}")
            for slot, item in char.equipment.items():
                if item:
                    await self.send(f"  <{slot}>: {item.short_desc}")

    def find_target_in_room(self, target_name: str):
        """
        Find a target in the room with numbered targeting support.
        Supports: "goblin", "1.goblin", "2.goblin", etc.
        Returns: Character object or None
        """
        if not target_name or not self.room:
            return None

        # Check for numbered target (e.g., "1.goblin", "2.goblin")
        target_number = 1
        if '.' in target_name:
            parts = target_name.split('.', 1)
            if parts[0].isdigit():
                target_number = int(parts[0])
                target_name = parts[1]

        # Find matching characters
        matches = []
        for char in self.room.characters:
            if char != self and self.matches_character(char, target_name):
                matches.append(char)

        # Return the nth match (1-indexed)
        if target_number <= len(matches):
            return matches[target_number - 1]

        return None

    def matches_character(self, char, target_name: str) -> bool:
        """
        Check if a character matches the target name.
        Checks name, short_desc, and keywords.
        """
        target_lower = target_name.lower()

        # Check name
        if target_lower in char.name.lower():
            return True

        # Check short_desc
        if hasattr(char, 'short_desc') and target_lower in char.short_desc.lower():
            return True

        # Check keywords list (for mobs)
        if hasattr(char, 'keywords') and char.keywords:
            if target_lower in char.keywords:
                return True
            # Also check if target is part of any keyword
            for keyword in char.keywords:
                if target_lower in keyword or keyword in target_lower:
                    return True

        return False

    def find_item_in_room(self, item_name: str):
        """
        Find an item in the room with numbered targeting support.
        Supports: "sword", "1.sword", "2.sword", etc.
        Returns: Item object or None
        """
        if not item_name or not self.room:
            return None

        # Check for numbered target (e.g., "1.chest", "2.chest")
        target_number = 1
        if '.' in item_name:
            parts = item_name.split('.', 1)
            if parts[0].isdigit():
                target_number = int(parts[0])
                item_name = parts[1]

        # Find matching items
        matches = []
        for item in self.room.items:
            if item_name.lower() in item.name.lower():
                matches.append(item)

        # Return the nth match (1-indexed)
        if target_number <= len(matches):
            return matches[target_number - 1]

        return None

    async def gain_exp(self, amount: int):
        """Gain experience points."""
        self.exp += amount

        # Check for level up
        while self.exp >= self.exp_to_level():
            await self.level_up()
            
    def exp_to_level(self) -> int:
        """Calculate experience needed for next level."""
        return int(self.config.BASE_EXP * (self.config.EXP_MULTIPLIER ** (self.level - 1)))
        
    async def level_up(self):
        """Level up the player."""
        self.level += 1
        
        class_data = self.config.CLASSES[self.char_class]
        
        # Gain HP
        hp_gain = random.randint(1, class_data['hit_dice']) + (self.con - 10) // 4
        self.max_hp += max(1, hp_gain)
        self.hp = self.max_hp
        
        # Gain mana
        mana_gain = random.randint(1, class_data['mana_dice']) + (self.int - 10) // 4
        self.max_mana += max(0, mana_gain)
        self.mana = self.max_mana
        
        # Gain move
        move_gain = random.randint(1, class_data['move_dice']) + (self.dex - 10) // 4
        self.max_move += max(0, move_gain)
        self.move = self.max_move
        
        # Gain practices
        self.practices += (self.wis - 10) // 2 + 2
        
        c = self.config.COLORS
        await self.send(f"\r\n{c['bright_yellow']}╔══════════════════════════════════════════════════════════╗")
        await self.send(f"║        CONGRATULATIONS! You have reached level {self.level:>2}!       ║")
        await self.send(f"╠══════════════════════════════════════════════════════════╣")
        await self.send(f"║  {c['bright_green']}HP: +{hp_gain:<3}{c['bright_yellow']}  {c['bright_cyan']}Mana: +{mana_gain:<3}{c['bright_yellow']}  {c['white']}Move: +{move_gain:<3}{c['bright_yellow']}               ║")
        await self.send(f"╚══════════════════════════════════════════════════════════╝{c['reset']}\r\n")
        
        # Check for new skills/spells
        await self.check_new_abilities()
        
    async def check_new_abilities(self):
        """Check if player qualifies for new skills/spells."""
        class_data = self.config.CLASSES[self.char_class]
        
        # Skills unlocked at various levels
        skill_levels = {
            1: 0, 2: 1, 3: 1, 5: 2, 7: 2, 10: 3, 15: 4, 20: 5, 25: 6, 30: 7
        }
        
        max_skills = skill_levels.get(self.level, 0)
        available_skills = class_data['skills'][:max_skills + 3]
        
        for skill in available_skills:
            if skill not in self.skills:
                self.skills[skill] = 30
                c = self.config.COLORS
                await self.send(f"{c['bright_green']}You have learned the skill: {skill.replace('_', ' ').title()}!{c['reset']}")
                
        # Same for spells
        available_spells = class_data['spells'][:max_skills + 2]
        for spell in available_spells:
            if spell not in self.spells:
                self.spells[spell] = 30
                c = self.config.COLORS
                await self.send(f"{c['bright_magenta']}You have learned the spell: {spell.replace('_', ' ').title()}!{c['reset']}")
                
    def get_damage_message(self, damage: int) -> str:
        """Get a message describing the damage amount."""
        if damage <= 0:
            return "miss"
        elif damage <= 4:
            return "scratch"
        elif damage <= 8:
            return "graze"
        elif damage <= 12:
            return "hit"
        elif damage <= 16:
            return "wound"
        elif damage <= 20:
            return "maul"
        elif damage <= 28:
            return "decimate"
        elif damage <= 36:
            return "devastate"
        elif damage <= 48:
            return "maim"
        elif damage <= 64:
            return "MUTILATE"
        elif damage <= 80:
            return "MASSACRE"
        elif damage <= 100:
            return "OBLITERATE"
        else:
            return "*** ANNIHILATE ***"
            
    async def take_damage(self, amount: int, attacker: 'Character' = None) -> bool:
        """Take damage, return True if killed."""
        self.hp -= amount

        # Check for autorecall
        if hasattr(self, 'autorecall_hp') and self.autorecall_hp is not None and self.hp > 0:
            threshold = self.autorecall_hp
            if hasattr(self, 'autorecall_is_percent') and self.autorecall_is_percent:
                threshold = int((self.autorecall_hp / 100.0) * self.max_hp)

            if self.hp <= threshold and self.is_fighting:
                # Trigger autorecall
                c = self.config.COLORS
                await self.send(f"\r\n{c['bright_red']}>>> AUTORECALL TRIGGERED <<<{c['reset']}")
                await self.send(f"{c['yellow']}Your HP dropped below {threshold}!{c['reset']}\r\n")

                # Stop fighting
                if self.fighting:
                    self.fighting.fighting = None
                    self.fighting = None
                self.position = 'standing'

                # Recall (same as cmd_recall but without the fighting check)
                recall_vnum = getattr(self, 'recall_point', 3001)
                recall_room = self.world.rooms.get(recall_vnum)
                if not recall_room:
                    recall_room = self.world.rooms.get(3001)

                if recall_room and self.room != recall_room:
                    old_room = self.room
                    if old_room:
                        await old_room.send_to_room(
                            f"{c['bright_cyan']}{self.name} disappears in a flash of light!{c['reset']}",
                            exclude=[self]
                        )
                        old_room.characters.remove(self)

                    self.room = recall_room
                    recall_room.characters.append(self)

                    await self.send(f"{c['bright_cyan']}You recall to safety!{c['reset']}")
                    await self.send("")
                    await recall_room.show_to(self)

                    await recall_room.send_to_room(
                        f"{c['bright_cyan']}{self.name} appears in a flash of light!{c['reset']}",
                        exclude=[self]
                    )

                    # Autorecall succeeded, don't die
                    return False

        if self.hp <= 0:
            await self.die(attacker)
            return True
        return False
        
    async def die(self, killer: 'Character' = None):
        """Handle player death."""
        c = self.config.COLORS
        
        # Stop fighting
        if self.fighting:
            self.fighting.fighting = None
            self.fighting = None
            
        self.position = 'dead'
        
        # Death message
        await self.send(f"\r\n{c['bright_red']}You have been KILLED!{c['reset']}")
        await self.send(f"{c['red']}You feel your soul slipping away...{c['reset']}\r\n")
        
        if self.room:
            await self.room.send_to_room(
                f"{c['red']}{self.name} falls to the ground, dead!{c['reset']}",
                exclude=[self]
            )
            
        # Lose some experience
        exp_loss = int(self.exp * 0.05)  # Lose 5% exp
        self.exp = max(0, self.exp - exp_loss)
        await self.send(f"{c['yellow']}You lose {exp_loss} experience points.{c['reset']}")
        
        # Drop gold
        gold_drop = int(self.gold * 0.10)  # Lose 10% gold
        if gold_drop > 0:
            self.gold -= gold_drop
            # Create gold object in room
            await self.send(f"{c['yellow']}You drop {gold_drop} gold coins.{c['reset']}")
            
        # Restore to starting room
        self.hp = 1
        self.mana = 1
        self.move = 1
        self.position = 'standing'
        
        # Move to temple
        if self.room:
            self.room.characters.remove(self)
            
        temple = self.world.get_room(self.config.STARTING_ROOM)
        if temple:
            self.room = temple
            temple.characters.append(self)
            
        await self.send(f"\r\n{c['white']}You feel yourself being pulled back to the material plane...{c['reset']}\r\n")
        await self.do_look([])
        
    async def regen_tick(self):
        """Regenerate HP/mana/move and process affects."""
        # Process affects (damage over time, healing over time, expiration)
        await AffectManager.tick_affects(self)

        # Position affects regen
        position_mult = {
            'sleeping': 2.0,
            'resting': 1.5,
            'sitting': 1.25,
            'standing': 1.0,
            'fighting': 0.5,
        }
        mult = position_mult.get(self.position, 1.0)

        # Get game time and weather for enhanced regen calculations
        game_time = None
        weather = None
        if hasattr(self, 'world') and self.world:
            game_time = self.world.game_time
            if self.room and self.room.zone and hasattr(self.room.zone, 'weather'):
                weather = self.room.zone.weather

        # Calculate enhanced regeneration
        hp_regen = RegenerationCalculator.calculate_hp_regen(
            self, self.config.HP_REGEN_RATE, mult, game_time, weather
        )
        mana_regen = RegenerationCalculator.calculate_mana_regen(
            self, self.config.MANA_REGEN_RATE, mult, game_time, weather
        )
        move_regen = RegenerationCalculator.calculate_move_regen(
            self, self.config.MOVE_REGEN_RATE, mult, game_time, weather
        )

        # Apply regeneration
        self.hp = min(self.max_hp, self.hp + hp_regen)
        self.mana = min(self.max_mana, self.mana + mana_regen)
        self.move = min(self.max_move, self.move + move_regen)

        # Process hunger and thirst consumption
        await self.hunger_thirst_tick()

    async def hunger_thirst_tick(self):
        """Process hunger and thirst consumption based on game time (1 point per game hour)."""
        c = self.config.COLORS

        # Get current game time
        if not hasattr(self, 'world') or not self.world or not hasattr(self.world, 'game_time'):
            return

        game_time = self.world.game_time
        current_hour = game_time.hour + (game_time.day * 24)  # Total hours elapsed

        # Decrease hunger by 1 per game hour (hungry after 24 hours, starving after 1 week)
        if current_hour != self.last_hunger_hour:
            hours_passed = current_hour - self.last_hunger_hour
            if hours_passed > 0:
                self.hunger = max(0, self.hunger - hours_passed)
                self.last_hunger_hour = current_hour

                # Warnings and penalties based on hunger level
                if self.hunger == 0:
                    await self.send(f"{c['red']}You are starving to death!{c['reset']}")
                    # Starving: lose HP
                    damage = max(1, self.max_hp // 20)  # 5% of max HP
                    await self.take_damage(damage)

                elif self.hunger <= 24:  # Less than 1 day of food
                    if self.hunger == 24:
                        await self.send(f"{c['yellow']}You are extremely hungry!{c['reset']}")

                elif self.hunger <= 48:  # Less than 2 days of food
                    if self.hunger == 48:
                        await self.send(f"{c['yellow']}You are hungry.{c['reset']}")

        # Decrease thirst by 1 per game hour (critical after 2.5 days = 60 hours)
        if current_hour != self.last_thirst_hour:
            hours_passed = current_hour - self.last_thirst_hour
            if hours_passed > 0:
                self.thirst = max(0, self.thirst - hours_passed)
                self.last_thirst_hour = current_hour

                # Warnings and penalties based on thirst level
                if self.thirst == 0:
                    await self.send(f"{c['bright_red']}You are dying of thirst!{c['reset']}")
                    # Dying of thirst: lose HP (more severe than hunger)
                    damage = max(2, self.max_hp // 10)  # 10% of max HP
                    await self.take_damage(damage)

                elif self.thirst <= 12:  # Less than half day of water
                    if self.thirst == 12:
                        await self.send(f"{c['yellow']}You are extremely thirsty!{c['reset']}")

                elif self.thirst <= 24:  # Less than 1 day of water
                    if self.thirst == 24:
                        await self.send(f"{c['yellow']}You are thirsty.{c['reset']}")

    def get_hunger_condition(self) -> str:
        """Get description of hunger condition (max 168 hours = 1 week)."""
        if self.hunger == 0:
            return "Starving"
        elif self.hunger <= 24:  # Less than 1 day
            return "Famished"
        elif self.hunger <= 48:  # 1-2 days
            return "Hungry"
        elif self.hunger <= 84:  # 2-3.5 days
            return "Peckish"
        else:
            return "Satiated"

    def get_thirst_condition(self) -> str:
        """Get description of thirst condition (max 60 hours = 2.5 days)."""
        if self.thirst == 0:
            return "Parched"
        elif self.thirst <= 12:  # Less than half day
            return "Dehydrated"
        elif self.thirst <= 24:  # 12-24 hours
            return "Thirsty"
        elif self.thirst <= 36:  # 1-1.5 days
            return "Dry"
        else:
            return "Quenched"

    async def improve_skill(self, skill_name: str, difficulty: int = 5):
        """Attempt to improve a skill through use.

        Args:
            skill_name: Name of the skill to improve
            difficulty: Base difficulty (1-10, higher = harder to improve)
        """
        c = self.config.COLORS

        # Check if player has the skill
        if skill_name not in self.skills:
            return

        current_prof = self.skills[skill_name]

        # Can't improve past 95% through use (need practice for last 5%)
        if current_prof >= 95:
            return

        # Calculate improvement chance
        # Lower proficiency = easier to improve
        # Higher difficulty = harder to improve
        base_chance = max(1, 15 - difficulty - (current_prof // 10))

        # Roll for improvement
        if random.randint(1, 100) <= base_chance:
            improvement = random.randint(1, 3)
            old_prof = current_prof
            self.skills[skill_name] = min(95, current_prof + improvement)

            await self.send(f"{c['green']}You feel more skilled at {skill_name.replace('_', ' ')}! ({old_prof}% -> {self.skills[skill_name]}%){c['reset']}")

    async def improve_spell(self, spell_name: str):
        """Attempt to improve a spell through casting.

        Args:
            spell_name: Name of the spell to improve
        """
        c = self.config.COLORS

        # Check if player has the spell
        if spell_name not in self.spells:
            return

        current_prof = self.spells[spell_name]

        # Can't improve past 95% through use (need practice for last 5%)
        if current_prof >= 95:
            return

        # Calculate improvement chance (harder to improve spells than skills)
        base_chance = max(1, 10 - (current_prof // 12))

        # Roll for improvement
        if random.randint(1, 100) <= base_chance:
            improvement = random.randint(1, 2)
            old_prof = current_prof
            self.spells[spell_name] = min(95, current_prof + improvement)

            await self.send(f"{c['bright_cyan']}Your knowledge of {spell_name.replace('_', ' ')} deepens! ({old_prof}% -> {self.spells[spell_name]}%){c['reset']}")
