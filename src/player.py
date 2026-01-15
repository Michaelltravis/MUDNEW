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
        """Calculate total hit bonus."""
        bonus = self.hitroll
        bonus += (self.str - 10) // 2  # Strength bonus
        bonus += (self.dex - 10) // 4  # Dexterity bonus
        return bonus
        
    def get_damage_bonus(self):
        """Calculate total damage bonus."""
        bonus = self.damroll
        bonus += (self.str - 10) // 2  # Strength bonus
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

        # Player flags
        self.flags = set()
        
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
        player.max_hp = class_data['hit_dice'] + (player.con - 10) // 2 * 2
        player.max_mana = class_data['mana_dice'] + (player.int - 10) // 2 * 2
        player.max_move = class_data['move_dice'] + (player.dex - 10) // 2 * 2
        
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
            
        # Class-specific starting weapon
        weapons = {
            'warrior': 10,    # Short sword
            'mage': 11,       # Dagger
            'cleric': 12,     # Mace
            'thief': 11,      # Dagger
            'ranger': 13,     # Short bow
            'paladin': 10,    # Short sword
            'necromancer': 11, # Dagger
            'bard': 14,       # Rapier
        }
        
        weapon_vnum = weapons.get(self.char_class, 10)
        weapon = create_object(weapon_vnum)
        if weapon:
            self.equipment['wield'] = weapon
            
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
            
        if not args:
            # Look at room
            await self.room.show_to(self)
        else:
            # Look at something specific
            target = ' '.join(args)
            
            # Check characters in room
            for char in self.room.characters:
                if char != self and target.lower() in char.name.lower():
                    await self.show_character(char)
                    return
                    
            # Check items in inventory
            for item in self.inventory:
                if target.lower() in item.name.lower():
                    await self.send(item.get_description())
                    return
                    
            # Check items in room
            for item in self.room.items:
                if target.lower() in item.name.lower():
                    await self.send(item.get_description())
                    return
                    
            # Check directions
            if target in self.config.DIRECTIONS:
                exit_data = self.room.exits.get(target)
                if exit_data:
                    await self.send(f"You see {exit_data.get('description', 'nothing special')}.")
                else:
                    await self.send("Nothing special there.")
                return
                    
            await self.send(f"You don't see '{target}' here.")
            
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
                    
    def gain_exp(self, amount: int):
        """Gain experience points."""
        self.exp += amount
        
        # Check for level up
        while self.exp >= self.exp_to_level():
            self.level_up()
            
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
