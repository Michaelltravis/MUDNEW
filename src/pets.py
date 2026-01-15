"""
RealmsMUD Pet/Companion System
===============================
Supports temporary summons, persistent companions, and undead servants.
"""

import random
import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from player import Player
    from world import World

from mobs import Mobile
from config import Config

logger = logging.getLogger('RealmsMUD.Pets')


class Pet(Mobile):
    """Pet/companion character controlled by a player."""

    def __init__(self, vnum: int, world: 'World', owner: 'Player', pet_type: str):
        super().__init__(vnum, world)
        self.owner = owner
        self.pet_type = pet_type  # 'summon', 'companion', 'undead'
        self.is_persistent = pet_type == 'companion'
        self.loyalty = 100  # 0-100, affects obedience
        self.experience = 0
        self.timer = None  # Despawn timer for temporary pets
        self.created_at = datetime.now()
        self.pet_level = 1  # Pets can level separately

        # Pet-specific flags
        self.flags.add('pet')

    def get_despawn_time(self) -> Optional[int]:
        """Get remaining time before despawn in seconds."""
        if not self.timer:
            return None
        remaining = (self.created_at + timedelta(seconds=self.timer)) - datetime.now()
        return max(0, int(remaining.total_seconds()))

    def is_expired(self) -> bool:
        """Check if temporary pet has expired."""
        if not self.timer:
            return False
        return datetime.now() >= self.created_at + timedelta(seconds=self.timer)

    async def execute_command(self, command: str, args: str = ''):
        """Execute an order from the owner."""
        if self.loyalty < 20:
            c = self.config.COLORS
            if hasattr(self.owner, 'send'):
                await self.owner.send(
                    f"{c['red']}{self.name} refuses to obey you!{c['reset']}"
                )
            return

        # Handle different commands
        if command == 'attack':
            await self._order_attack(args)
        elif command == 'follow':
            await self._order_follow()
        elif command == 'stay':
            await self._order_stay()
        elif command == 'guard':
            await self._order_guard()
        elif command == 'fetch':
            await self._order_fetch(args)
        else:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"Your pet doesn't understand that command.")

    async def _order_attack(self, target_name: str):
        """Order pet to attack a target."""
        if not self.room or not target_name:
            return

        # Find target in room
        target = None
        for char in self.room.characters:
            if char != self and char.name.lower().startswith(target_name.lower()):
                target = char
                break

        if not target:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"Your pet can't find that target.")
            return

        # Don't attack the owner or other pets
        if target == self.owner or (hasattr(target, 'owner') and target.owner == self.owner):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{self.name} refuses to attack that!")
            return

        # Start combat
        from combat import CombatHandler
        await CombatHandler.start_combat(self, target)

    async def _order_follow(self):
        """Order pet to follow owner."""
        c = self.config.COLORS
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} begins following you.{c['reset']}")
        # Following is default behavior, just confirm

    async def _order_stay(self):
        """Order pet to stay in current room."""
        c = self.config.COLORS
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['yellow']}{self.name} stays here.{c['reset']}")
        # Mark pet as staying (won't follow)
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        self.ai_state['staying'] = True

    async def _order_guard(self):
        """Order pet to guard owner."""
        c = self.config.COLORS
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['cyan']}{self.name} takes a protective stance.{c['reset']}")
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        self.ai_state['guarding'] = True

    async def _order_fetch(self, item_name: str):
        """Order pet to fetch an item."""
        if not self.room or not item_name:
            return

        # Find item in room
        item = None
        for obj in self.room.items:
            if obj.name.lower().startswith(item_name.lower()):
                item = obj
                break

        if not item:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{self.name} can't find that item.")
            return

        # Pick up item and give to owner
        self.room.items.remove(item)
        self.inventory.append(item)

        c = self.config.COLORS
        await self.room.send_to_room(
            f"{self.name} picks up {item.short_desc}."
        )

        # If owner is in room, give it to them
        if self.owner in self.room.characters:
            self.inventory.remove(item)
            self.owner.inventory.append(item)
            if hasattr(self.owner, 'send'):
                await self.owner.send(
                    f"{c['green']}{self.name} brings you {item.short_desc}.{c['reset']}"
                )

    async def process_ai(self):
        """Pet-specific AI behavior."""
        if not self.is_alive:
            return

        # Follow owner if not fighting and not staying
        if not self.is_fighting and not getattr(self, 'ai_state', {}).get('staying', False):
            await self._follow_owner()

        # Guard owner - attack anyone who attacks owner
        if getattr(self, 'ai_state', {}).get('guarding', False):
            await self._guard_owner()

        # Decay loyalty if mistreated
        if self.hp < self.max_hp * 0.3:
            self.loyalty = max(0, self.loyalty - 1)

    async def _follow_owner(self):
        """Follow owner to their room."""
        if not self.owner or not self.owner.room:
            return

        # Already in same room
        if self.room == self.owner.room:
            return

        # Check if we should follow (random chance to prevent spam)
        if random.randint(1, 100) > 30:
            return

        # Move to owner's room
        if self.room:
            self.room.characters.remove(self)

        self.room = self.owner.room
        self.owner.room.characters.append(self)

    async def _guard_owner(self):
        """Automatically defend owner."""
        if not self.owner or not self.owner.room or not self.room:
            return

        if self.room != self.owner.room:
            return

        # If owner is fighting and we're not, join the fight
        if self.owner.is_fighting and not self.is_fighting:
            from combat import CombatHandler
            await CombatHandler.start_combat(self, self.owner.fighting)


# Pet templates
PET_TEMPLATES = {
    # Mage summons (temporary)
    'air_elemental': {
        'name': 'air elemental',
        'short_desc': 'a swirling air elemental',
        'long_desc': 'A swirling mass of air and wind hovers here.',
        'pet_type': 'summon',
        'level_mult': 0.8,
        'duration': 1800,  # 30 minutes
        'hp_dice': '8d8+40',
        'damage_dice': '2d6',
        'special_abilities': ['whirlwind', 'fly'],
        'flags': ['fly'],
    },
    'fire_elemental': {
        'name': 'fire elemental',
        'short_desc': 'a blazing fire elemental',
        'long_desc': 'A blazing column of fire burns here.',
        'pet_type': 'summon',
        'level_mult': 0.8,
        'duration': 1800,
        'hp_dice': '8d8+40',
        'damage_dice': '2d8',
        'special_abilities': ['fire_breath', 'immolate'],
        'flags': ['fire_shield'],
    },
    'water_elemental': {
        'name': 'water elemental',
        'short_desc': 'a flowing water elemental',
        'long_desc': 'A flowing mass of water ripples here.',
        'pet_type': 'summon',
        'level_mult': 0.8,
        'duration': 1800,
        'hp_dice': '10d8+50',
        'damage_dice': '2d4',
        'special_abilities': ['water_jet', 'heal'],
        'flags': ['water_breathing'],
    },
    'earth_elemental': {
        'name': 'earth elemental',
        'short_desc': 'a massive earth elemental',
        'long_desc': 'A massive creature of rock and earth stands here.',
        'pet_type': 'summon',
        'level_mult': 0.9,
        'duration': 1800,
        'hp_dice': '12d8+60',
        'damage_dice': '3d6',
        'special_abilities': ['stone_skin', 'earthquake'],
        'flags': ['armored'],
    },

    # Ranger companions (persistent)
    'wolf': {
        'name': 'wolf',
        'short_desc': 'a gray wolf',
        'long_desc': 'A gray wolf stands here, teeth bared.',
        'pet_type': 'companion',
        'level_mult': 0.7,
        'tame_difficulty': 15,
        'hp_dice': '6d8+20',
        'damage_dice': '1d8',
        'special_abilities': ['track', 'howl', 'pack_tactics'],
        'flags': [],
    },
    'bear': {
        'name': 'bear',
        'short_desc': 'a brown bear',
        'long_desc': 'A massive brown bear growls menacingly.',
        'pet_type': 'companion',
        'level_mult': 0.9,
        'tame_difficulty': 25,
        'hp_dice': '10d8+50',
        'damage_dice': '2d8',
        'special_abilities': ['maul', 'thick_hide'],
        'flags': ['armored'],
    },
    'hawk': {
        'name': 'hawk',
        'short_desc': 'a hunting hawk',
        'long_desc': 'A hawk circles overhead, searching for prey.',
        'pet_type': 'companion',
        'level_mult': 0.5,
        'tame_difficulty': 20,
        'hp_dice': '4d8+10',
        'damage_dice': '1d6',
        'special_abilities': ['scout', 'dive_attack'],
        'flags': ['fly'],
    },
    'panther': {
        'name': 'panther',
        'short_desc': 'a black panther',
        'long_desc': 'A sleek black panther stalks silently here.',
        'pet_type': 'companion',
        'level_mult': 0.75,
        'tame_difficulty': 22,
        'hp_dice': '7d8+25',
        'damage_dice': '2d6',
        'special_abilities': ['stealth', 'pounce'],
        'flags': ['stealth'],
    },
    'boar': {
        'name': 'boar',
        'short_desc': 'a wild boar',
        'long_desc': 'A wild boar snorts and paws at the ground.',
        'pet_type': 'companion',
        'level_mult': 0.8,
        'tame_difficulty': 18,
        'hp_dice': '8d8+40',
        'damage_dice': '2d4',
        'special_abilities': ['charge', 'tusks'],
        'flags': [],
    },

    # Necromancer undead (temporary, requires corpse)
    'skeleton': {
        'name': 'skeleton',
        'short_desc': 'a reanimated skeleton',
        'long_desc': 'A skeleton warrior stands here, bones rattling.',
        'pet_type': 'undead',
        'level_mult': 0.7,
        'duration': 3600,  # 60 minutes
        'hp_dice': '6d8+20',
        'damage_dice': '1d8',
        'special_abilities': ['undead', 'immune_poison'],
        'flags': ['undead'],
    },
    'ghoul': {
        'name': 'ghoul',
        'short_desc': 'a foul ghoul',
        'long_desc': 'A rotting ghoul shambles here, seeking flesh.',
        'pet_type': 'undead',
        'level_mult': 0.9,
        'duration': 2700,  # 45 minutes
        'hp_dice': '8d8+40',
        'damage_dice': '2d6',
        'special_abilities': ['paralyzing_touch', 'disease'],
        'flags': ['undead'],
    },
    'zombie': {
        'name': 'zombie',
        'short_desc': 'a shambling zombie',
        'long_desc': 'A shambling zombie lurches here mindlessly.',
        'pet_type': 'undead',
        'level_mult': 0.6,
        'duration': 3600,
        'hp_dice': '10d8+50',
        'damage_dice': '1d6',
        'special_abilities': ['undead', 'slow'],
        'flags': ['undead'],
    },
    'wight': {
        'name': 'wight',
        'short_desc': 'a terrible wight',
        'long_desc': 'A wight stands here, emanating cold and death.',
        'pet_type': 'undead',
        'level_mult': 1.0,
        'duration': 1800,  # 30 minutes
        'hp_dice': '9d8+45',
        'damage_dice': '2d8',
        'special_abilities': ['energy_drain', 'fear_aura'],
        'flags': ['undead'],
    },
}


class PetManager:
    """Manages pet summoning, taming, and lifecycle."""

    @staticmethod
    async def summon_pet(owner: 'Player', template_name: str, duration_minutes: int = 30) -> Optional[Pet]:
        """
        Summon a temporary pet.

        Args:
            owner: The player summoning the pet
            template_name: Name of pet template from PET_TEMPLATES
            duration_minutes: How long pet lasts

        Returns:
            The summoned pet or None if failed
        """
        if template_name not in PET_TEMPLATES:
            logger.error(f"Unknown pet template: {template_name}")
            return None

        template = PET_TEMPLATES[template_name]

        # Check if player already has too many pets
        current_pets = PetManager.get_player_pets(owner)
        if len(current_pets) >= 3:
            c = Config().COLORS
            if hasattr(owner, 'send'):
                await owner.send(f"{c['red']}You can't control more than 3 pets!{c['reset']}")
            return None

        # Create pet
        pet = Pet(0, owner.world, owner, template['pet_type'])
        pet.name = template['name']
        pet.short_desc = template['short_desc']
        pet.long_desc = template['long_desc']

        # Set level based on owner level
        pet.level = int(owner.level * template['level_mult'])
        pet.level = max(1, pet.level)

        # Set stats
        pet.max_hp = Mobile.roll_dice(template['hp_dice'])
        pet.hp = pet.max_hp
        pet.damage_dice = template['damage_dice']

        # Set duration for temporary pets
        if template['pet_type'] in ('summon', 'undead'):
            pet.timer = duration_minutes * 60

        # Add flags
        for flag in template.get('flags', []):
            pet.flags.add(flag)

        # Add to world
        pet.room = owner.room
        owner.room.characters.append(pet)
        owner.world.npcs.append(pet)

        # Add to owner's companion list if persistent
        if pet.is_persistent:
            if not hasattr(owner, 'companions'):
                owner.companions = []
            owner.companions.append(pet)

        logger.info(f"{owner.name} summoned {pet.name} (level {pet.level})")

        c = Config().COLORS
        await owner.room.send_to_room(
            f"{c['bright_magenta']}{pet.name} appears in a flash of magic!{c['reset']}"
        )

        return pet

    @staticmethod
    async def tame_companion(owner: 'Player', target: Mobile) -> bool:
        """
        Attempt to tame a wild creature as a companion.

        Args:
            owner: The player attempting to tame
            target: The creature to tame

        Returns:
            True if successful
        """
        c = Config().COLORS

        # Check if target is tameable
        template = None
        for template_name, tmpl in PET_TEMPLATES.items():
            if tmpl['pet_type'] == 'companion' and target.name.lower() == tmpl['name']:
                template = tmpl
                break

        if not template:
            if hasattr(owner, 'send'):
                await owner.send(f"{c['red']}That creature cannot be tamed!{c['reset']}")
            return False

        # Check if player already has a companion
        current_companions = [p for p in PetManager.get_player_pets(owner) if p.is_persistent]
        if len(current_companions) >= 1:
            if hasattr(owner, 'send'):
                await owner.send(f"{c['red']}You can only have one permanent companion!{c['reset']}")
            return False

        # Taming check (CHA-based with difficulty)
        tame_skill = 50 + (owner.cha - 10) * 5
        difficulty = template.get('tame_difficulty', 20)
        roll = random.randint(1, 100)

        if roll + tame_skill < difficulty * 5:
            if hasattr(owner, 'send'):
                await owner.send(f"{c['red']}You fail to tame {target.name}!{c['reset']}")
            # Might become aggressive
            if random.randint(1, 100) <= 30:
                await owner.room.send_to_room(
                    f"{c['yellow']}{target.name} becomes enraged!{c['reset']}"
                )
                from combat import CombatHandler
                await CombatHandler.start_combat(target, owner)
            return False

        # Success - convert mob to pet
        pet = Pet(target.vnum, owner.world, owner, 'companion')
        pet.name = target.name
        pet.short_desc = target.short_desc
        pet.long_desc = target.long_desc
        pet.level = target.level
        pet.max_hp = target.max_hp
        pet.hp = target.hp
        pet.damage_dice = target.damage_dice
        pet.is_persistent = True

        # Remove old mob
        if target in target.room.characters:
            target.room.characters.remove(target)
        if target in owner.world.npcs:
            owner.world.npcs.remove(target)

        # Add pet
        pet.room = owner.room
        owner.room.characters.append(pet)
        owner.world.npcs.append(pet)

        if not hasattr(owner, 'companions'):
            owner.companions = []
        owner.companions.append(pet)

        await owner.room.send_to_room(
            f"{c['bright_green']}{owner.name} tames {pet.name}!{c['reset']}"
        )

        logger.info(f"{owner.name} tamed {pet.name}")
        return True

    @staticmethod
    async def dismiss_pet(pet: Pet):
        """Dismiss a pet."""
        if not pet or not pet.owner:
            return

        c = Config().COLORS

        # Remove from world
        if pet.room and pet in pet.room.characters:
            await pet.room.send_to_room(
                f"{c['yellow']}{pet.name} fades away.{c['reset']}"
            )
            pet.room.characters.remove(pet)

        if pet in pet.owner.world.npcs:
            pet.owner.world.npcs.remove(pet)

        # Remove from companions list if persistent
        if pet.is_persistent and hasattr(pet.owner, 'companions'):
            if pet in pet.owner.companions:
                pet.owner.companions.remove(pet)

        logger.info(f"{pet.owner.name} dismissed {pet.name}")

    @staticmethod
    def get_player_pets(owner: 'Player') -> List[Pet]:
        """Get all pets belonging to a player."""
        pets = []
        for npc in owner.world.npcs:
            if isinstance(npc, Pet) and npc.owner == owner:
                pets.append(npc)
        return pets

    @staticmethod
    async def pet_tick(world: 'World'):
        """Process all pet timers and behaviors."""
        pets_to_remove = []

        for npc in world.npcs:
            if not isinstance(npc, Pet):
                continue

            # Check if temporary pet expired
            if npc.timer and npc.is_expired():
                pets_to_remove.append(npc)
                continue

            # Warn owner if pet will expire soon
            if npc.timer:
                remaining = npc.get_despawn_time()
                if remaining and remaining == 300:  # 5 minutes warning
                    c = Config().COLORS
                    if hasattr(npc.owner, 'send'):
                        await npc.owner.send(
                            f"{c['yellow']}{npc.name} will disappear in 5 minutes!{c['reset']}"
                        )

        # Remove expired pets
        for pet in pets_to_remove:
            await PetManager.dismiss_pet(pet)
