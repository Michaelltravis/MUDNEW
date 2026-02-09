"""
Advanced Mob AI System

Provides sophisticated AI behaviors for NPCs including:
- Patrol routes
- Home/guard behavior
- Pack tactics and coordination
- Smart spell/skill usage
- Flee and heal tactics
- Assist allies
"""

import random
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from mobs import Mobile

logger = logging.getLogger(__name__)


class AIBehavior(ABC):
    """Base class for AI behaviors."""

    def __init__(self, priority: int):
        self.priority = priority

    @abstractmethod
    async def should_execute(self, mob: 'Mobile') -> bool:
        """
        Check if this behavior should execute.

        Args:
            mob: The mob to check

        Returns:
            True if behavior should execute
        """
        pass

    @abstractmethod
    async def execute(self, mob: 'Mobile'):
        """
        Execute the behavior.

        Args:
            mob: The mob to execute behavior on
        """
        pass


class PatrolBehavior(AIBehavior):
    """Follow a predefined patrol route."""

    def __init__(self):
        super().__init__(priority=50)

    async def should_execute(self, mob: 'Mobile') -> bool:
        # Only patrol when not fighting
        if mob.is_fighting:
            return False

        # Check if mob has a patrol route
        if not hasattr(mob, 'ai_config') or not mob.ai_config:
            return False

        patrol_route = mob.ai_config.get('patrol_route', [])
        if len(patrol_route) <= 1:
            return False

        # Cooldown: only move once every 15-30 seconds
        import time
        if not hasattr(mob, 'ai_state'):
            mob.ai_state = {}
        next_patrol_time = mob.ai_state.get('next_patrol_time', 0)
        if time.time() < next_patrol_time:
            return False

        return True

    async def execute(self, mob: 'Mobile'):
        import time
        patrol_route = mob.ai_config.get('patrol_route', [])
        if not patrol_route or not mob.room:
            return

        # Get current patrol index
        if not hasattr(mob, 'ai_state'):
            mob.ai_state = {}

        # Set next patrol time (15-30 seconds)
        import random as rng
        mob.ai_state['next_patrol_time'] = time.time() + rng.randint(15, 30)

        patrol_index = mob.ai_state.get('patrol_index', 0)
        next_room_vnum = patrol_route[patrol_index]

        # Find direction to next room
        for direction, exit_data in mob.room.exits.items():
            if exit_data.get('to_room') == next_room_vnum:
                # Skip closed doors
                if 'door' in exit_data and exit_data['door'].get('state') == 'closed':
                    continue
                # Move to next room
                target_room = mob.world.rooms.get(next_room_vnum)
                if target_room:
                    mob.room.characters.remove(mob)
                    target_room.characters.append(mob)
                    mob.room = target_room

                    # Update patrol index
                    mob.ai_state['patrol_index'] = (patrol_index + 1) % len(patrol_route)
                    logger.debug(f"{mob.name} patrolled to room {next_room_vnum}")
                    return


class GuardBehavior(AIBehavior):
    """Return to home room when too far away."""

    def __init__(self):
        super().__init__(priority=60)

    async def should_execute(self, mob: 'Mobile') -> bool:
        # Only guard when not fighting
        if mob.is_fighting:
            return False

        # Check if mob has a home room
        if not hasattr(mob, 'ai_config') or not mob.ai_config:
            return False

        home_room = mob.ai_config.get('home_room')
        if not home_room or not mob.room:
            return False

        # Check if too far from home
        return mob.room.vnum != home_room

    async def execute(self, mob: 'Mobile'):
        home_room_vnum = mob.ai_config.get('home_room')
        if not home_room_vnum or not mob.room:
            return

        # Simple pathfinding - try to move toward home
        # In a real implementation, you'd use A* or similar
        # For now, just pick a random direction
        if mob.room.exits:
            # Filter out closed doors
            valid_exits = []
            for dir_name, exit_info in mob.room.exits.items():
                if not exit_info:
                    continue
                # Skip closed doors
                if 'door' in exit_info and exit_info['door'].get('state') == 'closed':
                    continue
                valid_exits.append((dir_name, exit_info))
            
            if valid_exits:
                direction, exit_data = random.choice(valid_exits)
                target_vnum = exit_data.get('to_room')
                target_room = mob.world.rooms.get(target_vnum)

                if target_room:
                    mob.room.characters.remove(mob)
                    target_room.characters.append(mob)
                    mob.room = target_room
                    logger.debug(f"{mob.name} moved toward home")


class FleeHealBehavior(AIBehavior):
    """Flee when low on HP and try to heal."""

    def __init__(self):
        super().__init__(priority=100)  # Highest priority - survival

    async def should_execute(self, mob: 'Mobile') -> bool:
        if not mob.is_fighting:
            return False

        hp_percent = mob.hp / mob.max_hp
        return hp_percent < 0.25  # Flee when below 25% HP

    async def execute(self, mob: 'Mobile'):
        # Try to flee
        if mob.room and mob.room.exits:
            # Filter out closed doors
            valid_exits = []
            for dir_name, exit_info in mob.room.exits.items():
                if not exit_info:
                    continue
                # Skip closed doors
                if 'door' in exit_info and exit_info['door'].get('state') == 'closed':
                    continue
                valid_exits.append((dir_name, exit_info))
            
            if not valid_exits:
                return
            
            direction, exit_data = random.choice(valid_exits)
            target_vnum = exit_data.get('to_room')
            target_room = mob.world.rooms.get(target_vnum)

            if target_room:
                # End combat
                if mob.fighting:
                    mob.fighting.fighting = None
                    mob.fighting = None

                # Move to new room
                mob.room.characters.remove(mob)
                target_room.characters.append(mob)
                old_room = mob.room
                mob.room = target_room

                # Announce flee
                c = mob.config.COLORS
                await old_room.send_to_room(f"{c['yellow']}{mob.name} flees {direction}!{c['reset']}")

                # Try to heal if possible
                if mob.mana >= 30 and 'heal' in getattr(mob, 'spells', []):
                    heal_amount = mob.max_hp // 3
                    mob.hp = min(mob.max_hp, mob.hp + heal_amount)
                    logger.debug(f"{mob.name} healed for {heal_amount}")


class SpellCasterBehavior(AIBehavior):
    """Intelligently choose and cast spells."""

    def __init__(self):
        super().__init__(priority=70)

    async def should_execute(self, mob: 'Mobile') -> bool:
        if not mob.is_fighting or mob.mana < 20:
            return False

        # Check if mob has spells
        return bool(getattr(mob, 'spells', []))

    async def execute(self, mob: 'Mobile'):
        spells = getattr(mob, 'spells', [])
        if not spells or not mob.fighting:
            return

        hp_percent = mob.hp / mob.max_hp
        target_hp_percent = mob.fighting.hp / mob.fighting.max_hp

        # Choose spell based on situation
        chosen_spell = None

        # Low health - heal self
        if hp_percent < 0.4 and mob.mana >= 30:
            heal_spells = ['heal', 'cure_critical', 'cure_serious']
            for spell in heal_spells:
                if spell in spells:
                    chosen_spell = spell
                    break

        # Not yet buffed - cast buff
        if not chosen_spell and not getattr(mob, 'ai_state', {}).get('buffed', False):
            buff_spells = ['armor', 'bless', 'haste']
            for spell in buff_spells:
                if spell in spells:
                    chosen_spell = spell
                    if not hasattr(mob, 'ai_state'):
                        mob.ai_state = {}
                    mob.ai_state['buffed'] = True
                    break

        # Enemy at high HP - damage spell
        if not chosen_spell and target_hp_percent > 0.6:
            damage_spells = ['fireball', 'lightning_bolt', 'magic_missile', 'burning_hands']
            for spell in damage_spells:
                if spell in spells:
                    chosen_spell = spell
                    break

        # Enemy at medium HP - debuff or damage
        if not chosen_spell and target_hp_percent > 0.3:
            debuff_spells = ['blindness', 'weaken', 'poison']
            for spell in debuff_spells:
                if spell in spells:
                    chosen_spell = spell
                    break

        # Cast the chosen spell
        if chosen_spell and mob.mana >= 15:
            from spells import SpellHandler
            await SpellHandler.cast_spell(mob, chosen_spell, mob.fighting.name if mob.fighting != mob else None)
            logger.debug(f"{mob.name} cast {chosen_spell}")


class PackBehavior(AIBehavior):
    """Coordinate with pack members."""

    def __init__(self):
        super().__init__(priority=80)

    async def should_execute(self, mob: 'Mobile') -> bool:
        if not mob.is_fighting:
            return False

        # Check if mob has pack tactics enabled
        if not hasattr(mob, 'ai_config') or not mob.ai_config:
            return False

        return mob.ai_config.get('pack_tactics', False)

    async def execute(self, mob: 'Mobile'):
        if not mob.room or not mob.fighting:
            return

        # Find pack members (same species, not fighting)
        pack_members = []
        for char in mob.room.characters:
            if char == mob or not hasattr(char, 'name'):
                continue

            # Same type of mob
            if hasattr(char, 'vnum') and hasattr(mob, 'vnum'):
                if char.vnum == mob.vnum and not char.is_fighting:
                    pack_members.append(char)

        # Call up to 2 pack members to assist
        if pack_members:
            for ally in pack_members[:2]:
                # Start combat with the same target
                ally.fighting = mob.fighting
                mob.fighting.fighting = ally  # Target fights back

                c = mob.config.COLORS
                await mob.room.send_to_room(
                    f"{c['red']}{ally.name} joins the fight!{c['reset']}"
                )
                logger.debug(f"{ally.name} joined pack attack")


class AssistBehavior(AIBehavior):
    """Help specific ally types."""

    def __init__(self):
        super().__init__(priority=75)

    async def should_execute(self, mob: 'Mobile') -> bool:
        if mob.is_fighting:
            return False

        # Check if mob has assist allies configured
        if not hasattr(mob, 'ai_config') or not mob.ai_config:
            return False

        assist_allies = mob.ai_config.get('assist_allies', [])
        if not assist_allies or not mob.room:
            return False

        # Check if any ally is fighting in the room
        for char in mob.room.characters:
            if char.is_fighting and hasattr(char, 'name'):
                for ally_name in assist_allies:
                    if ally_name.lower() in char.name.lower():
                        return True

        return False

    async def execute(self, mob: 'Mobile'):
        if not mob.room:
            return

        assist_allies = mob.ai_config.get('assist_allies', [])

        # Find fighting ally
        for char in mob.room.characters:
            if char.is_fighting and hasattr(char, 'name'):
                for ally_name in assist_allies:
                    if ally_name.lower() in char.name.lower() and char.fighting:
                        # Assist the ally by attacking their enemy
                        mob.fighting = char.fighting
                        char.fighting.fighting = mob

                        c = mob.config.COLORS
                        await mob.room.send_to_room(
                            f"{c['red']}{mob.name} rushes to assist {char.name}!{c['reset']}"
                        )
                        logger.debug(f"{mob.name} assisted {char.name}")
                        return


class AIController:
    """Controls all AI behaviors for a mob."""

    def __init__(self, mob: 'Mobile'):
        self.mob = mob
        self.behaviors: List[AIBehavior] = []
        self.action_rate = 0.05  # 5% chance to take an action per tick (~0.5/sec at 10 tps)

    def add_behavior(self, behavior: AIBehavior):
        """Add a behavior to this AI controller."""
        self.behaviors.append(behavior)
        # Keep sorted by priority (highest first)
        self.behaviors.sort(key=lambda b: b.priority, reverse=True)

    async def process(self):
        """Process AI behaviors."""
        # Random chance to take an action
        if random.random() > self.action_rate:
            return

        # Execute highest priority behavior that should execute
        for behavior in self.behaviors:
            try:
                if await behavior.should_execute(self.mob):
                    await behavior.execute(self.mob)
                    return  # Only execute one behavior per tick
            except Exception as e:
                logger.error(f"Error in AI behavior {behavior.__class__.__name__}: {e}")

    @staticmethod
    def create_from_config(mob: 'Mobile', ai_config: Dict[str, Any]) -> 'AIController':
        """
        Create an AI controller from configuration.

        Args:
            mob: The mob this controller is for
            ai_config: AI configuration dictionary

        Returns:
            Configured AIController
        """
        controller = AIController(mob)

        # Add behaviors based on config
        behaviors_list = ai_config.get('behaviors', [])

        if 'patrol' in behaviors_list:
            controller.add_behavior(PatrolBehavior())

        if 'guard' in behaviors_list:
            controller.add_behavior(GuardBehavior())

        if 'flee_heal' in behaviors_list or 'wimpy' in getattr(mob, 'flags', []):
            controller.add_behavior(FleeHealBehavior())

        if 'spellcaster' in behaviors_list or getattr(mob, 'spells', []):
            controller.add_behavior(SpellCasterBehavior())

        if 'pack_tactics' in behaviors_list or ai_config.get('pack_tactics'):
            controller.add_behavior(PackBehavior())

        if 'assist' in behaviors_list or ai_config.get('assist_allies'):
            controller.add_behavior(AssistBehavior())

        return controller
