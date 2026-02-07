"""
RealmsMUD Pet/Companion System
===============================
Supports temporary summons, persistent companions, and undead servants.
"""

import random
import logging
import time
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
        self.is_persistent = pet_type in ('companion', 'undead')  # Undead pets persist too!
        self.loyalty = 100  # 0-100, affects obedience
        self.experience = 0
        self.timer = None  # Despawn timer for temporary pets
        self.created_at = datetime.now()
        self.pet_level = 1  # Pets can level separately
        self.role = None  # Optional role for specialized behavior (tank/healer/caster/rogue)

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
        elif command == 'protect':
            await self._order_protect(args)
        elif command == 'fetch':
            await self._order_fetch(args)
        elif command == 'sit':
            await self._order_position('sitting')
        elif command == 'stand':
            await self._order_position('standing')
        elif command == 'sleep':
            await self._order_position('sleeping')
        elif command == 'rest':
            await self._order_position('resting')
        elif command == 'assist':
            await self._order_assist()
        elif command == 'report':
            await self._order_report()
        elif command in ('north', 'south', 'east', 'west', 'up', 'down', 'n', 's', 'e', 'w', 'u', 'd'):
            await self._order_move(command)
        # Combat control commands
        elif command in ('disengage', 'stop', 'halt'):
            await self._order_disengage()
        elif command == 'flee':
            await self._order_flee()
        elif command in ('heel', 'come', 'return'):
            await self._order_heel()
        elif command == 'passive':
            await self._order_passive()
        elif command == 'aggressive':
            await self._order_aggressive()
        elif command == 'defensive':
            await self._order_defensive()
        elif command == 'dismiss':
            await self._order_dismiss()
        # Skill commands
        elif command == 'backstab':
            await self._order_skill('backstab', args)
        elif command == 'heal':
            await self._order_skill('dark_heal', args)
        elif command == 'bolt':
            await self._order_skill('necrotic_bolt', args)
        elif command == 'shield':
            await self._order_skill('shield_wall', args)
        elif command in ('pick', 'picklock', 'unlock'):
            await self._order_pick_lock(args)
        elif command == 'sneak':
            await self._order_sneak()
        elif command == 'recall':
            await self._order_recall()
        else:
            if hasattr(self.owner, 'send'):
                c = self.config.COLORS
                await self.owner.send(f"{c['yellow']}Your pet doesn't understand '{command}'.{c['reset']}")
                await self.owner.send(f"{c['cyan']}Movement:{c['reset']} follow, stay, heel, north/s/e/w/up/down")
                await self.owner.send(f"{c['cyan']}Combat:{c['reset']} attack <target>, assist, disengage, flee")
                await self.owner.send(f"{c['cyan']}Modes:{c['reset']} passive, defensive, aggressive, guard, protect <player>")
                await self.owner.send(f"{c['cyan']}Rogue:{c['reset']} sneak, pick <direction> (if known)")
                await self.owner.send(f"{c['cyan']}Other:{c['reset']} report, fetch <item>, dismiss")
                await self.owner.send(f"{c['cyan']}Skills:{c['reset']} backstab, heal, bolt, shield (if known)")

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

    async def _order_assist(self):
        """Order pet to assist owner - attack what owner is fighting."""
        c = self.config.COLORS
        if not self.owner:
            return
            
        # Check if owner is fighting
        if not self.owner.is_fighting or not self.owner.fighting:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} looks around but you're not fighting anyone.{c['reset']}")
            return
            
        target = self.owner.fighting
        
        # Make sure target is in same room
        if target not in self.room.characters:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} can't reach your target.{c['reset']}")
            return
            
        # Already fighting this target?
        if self.is_fighting and self.fighting == target:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} is already fighting {target.name}!{c['reset']}")
            return
            
        # Start combat
        from combat import CombatHandler
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} rushes to assist you against {target.name}!{c['reset']}")
        if self.room:
            await self.room.send_to_room(
                f"{c['cyan']}{self.name} leaps to assist {self.owner.name}!{c['reset']}",
                exclude=[self.owner]
            )
        await CombatHandler.start_combat(self, target)

    async def _order_report(self):
        """Order pet to report its status."""
        c = self.config.COLORS
        if not self.owner or not hasattr(self.owner, 'send'):
            return
            
        hp_pct = int((self.hp / self.max_hp) * 100) if self.max_hp > 0 else 0
        
        # Color based on health
        if hp_pct > 75:
            hp_color = c['bright_green']
        elif hp_pct > 50:
            hp_color = c['green']
        elif hp_pct > 25:
            hp_color = c['yellow']
        else:
            hp_color = c['red']
            
        # Build status bar
        bar_len = 20
        filled = int((hp_pct / 100) * bar_len)
        bar = '█' * filled + '░' * (bar_len - filled)
        
        await self.owner.send(f"{c['cyan']}╔══════════════════════════════════════════╗{c['reset']}")
        await self.owner.send(f"{c['cyan']}║{c['reset']} {c['bright_white']}{self.name:^40}{c['reset']} {c['cyan']}║{c['reset']}")
        await self.owner.send(f"{c['cyan']}╠══════════════════════════════════════════╣{c['reset']}")
        await self.owner.send(f"{c['cyan']}║{c['reset']} HP: {hp_color}[{bar}]{c['reset']} {self.hp:>4}/{self.max_hp:<4} {c['cyan']}║{c['reset']}")
        await self.owner.send(f"{c['cyan']}║{c['reset']} Level: {c['white']}{self.level:<4}{c['reset']} Loyalty: {c['green']}{getattr(self, 'loyalty', 100):<3}{c['reset']}%       {c['cyan']}║{c['reset']}")
        
        # Show fighting status
        if self.is_fighting and self.fighting:
            enemy_hp_pct = int((self.fighting.hp / self.fighting.max_hp) * 100)
            await self.owner.send(f"{c['cyan']}║{c['reset']} Fighting: {c['red']}{self.fighting.name[:25]:<25}{c['reset']} {c['cyan']}║{c['reset']}")
        else:
            await self.owner.send(f"{c['cyan']}║{c['reset']} Status: {c['green']}Ready{c['reset']}                          {c['cyan']}║{c['reset']}")
            
        await self.owner.send(f"{c['cyan']}╚══════════════════════════════════════════╝{c['reset']}")

    async def _order_skill(self, skill_name: str, target_name: str = ''):
        """Order pet to use a specific skill."""
        c = self.config.COLORS
        
        # Check if pet has this ability
        if skill_name not in getattr(self, 'special_abilities', []):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} doesn't know how to do that.{c['reset']}")
                abilities = getattr(self, 'special_abilities', [])
                if abilities:
                    skill_list = [a for a in abilities if a != 'undead']
                    if skill_list:
                        await self.owner.send(f"{c['cyan']}{self.name} knows: {', '.join(skill_list)}{c['reset']}")
            return
        
        # Find target
        target = None
        if target_name:
            # Find target in room
            for char in self.room.characters:
                if char != self and target_name.lower() in char.name.lower():
                    target = char
                    break
        elif self.is_fighting:
            target = self.fighting
        elif self.owner and self.owner.is_fighting:
            target = self.owner.fighting
        elif self.owner and hasattr(self.owner, 'target') and self.owner.target:
            target = self.owner.target
        
        # Skill-specific handling
        if skill_name == 'backstab':
            if not target:
                if hasattr(self.owner, 'send'):
                    await self.owner.send(f"{c['yellow']}Backstab whom?{c['reset']}")
                return
            if target.hp <= 0:
                if hasattr(self.owner, 'send'):
                    await self.owner.send(f"{c['yellow']}That target is already dead.{c['reset']}")
                return
            # Use the backstab ability
            await self.use_special_ability('backstab', target)
            # Start combat if not fighting
            if not self.is_fighting:
                from combat import CombatHandler
                await CombatHandler.start_combat(self, target)
                
        elif skill_name == 'dark_heal':
            # Heal defaults to owner if no target specified
            if not target:
                target = self.owner
            if not target or target.hp <= 0:
                if hasattr(self.owner, 'send'):
                    await self.owner.send(f"{c['yellow']}Heal whom?{c['reset']}")
                return
            await self.use_special_ability('dark_heal', target)
            
        elif skill_name == 'necrotic_bolt':
            if not target:
                if hasattr(self.owner, 'send'):
                    await self.owner.send(f"{c['yellow']}Cast bolt at whom?{c['reset']}")
                return
            if target.hp <= 0:
                if hasattr(self.owner, 'send'):
                    await self.owner.send(f"{c['yellow']}That target is already dead.{c['reset']}")
                return
            await self.use_special_ability('necrotic_bolt', target)
            if not self.is_fighting:
                from combat import CombatHandler
                await CombatHandler.start_combat(self, target)
                
        elif skill_name == 'shield_wall':
            # Shield wall is self-buff
            await self.use_special_ability('shield_wall', self)
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['cyan']}{self.name} raises their shield in a defensive stance!{c['reset']}")

    async def _order_follow(self):
        """Order pet to follow owner."""
        c = self.config.COLORS
        # Clear the staying flag so pet resumes following
        if hasattr(self, 'ai_state'):
            self.ai_state['staying'] = False
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} begins following you.{c['reset']}")

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

    async def _order_protect(self, target_name: str):
        """Order pet to protect a specific player, intercepting attacks."""
        c = self.config.COLORS
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        
        # If no target, show current protection status or clear
        if not target_name:
            current = self.ai_state.get('protecting')
            if current:
                await self.owner.send(f"{c['cyan']}{self.name} is currently protecting {current.name}.{c['reset']}")
                await self.owner.send(f"{c['white']}Use 'order protect <name>' to protect someone else, or 'order guard' to return to guarding you.{c['reset']}")
            else:
                await self.owner.send(f"{c['yellow']}Usage: order protect <player>{c['reset']}")
            return
        
        # Clear protection if requested
        if target_name.lower() in ('none', 'clear', 'off', 'stop'):
            self.ai_state['protecting'] = None
            await self.owner.send(f"{c['cyan']}{self.name} stops protecting and returns to your side.{c['reset']}")
            return
        
        # Find target to protect (owner or other players in room)
        target = None
        
        # Check if targeting owner
        if target_name.lower() in ('me', 'self', self.owner.name.lower()):
            target = self.owner
        else:
            # Search for player in room
            for char in self.room.characters:
                if char != self and hasattr(char, 'char_class'):  # Players have char_class
                    if target_name.lower() in char.name.lower():
                        target = char
                        break
        
        if not target:
            await self.owner.send(f"{c['yellow']}{self.name} doesn't see anyone named '{target_name}' to protect.{c['reset']}")
            return
        
        # Set protection
        self.ai_state['protecting'] = target
        self.ai_state['guarding'] = True  # Also enable guarding
        
        await self.owner.send(f"{c['bright_green']}{self.name} moves to protect {target.name}, shield raised!{c['reset']}")
        if target != self.owner:
            await target.send(f"{c['bright_green']}{self.name} moves to protect you!{c['reset']}")
        
        # Announce to room
        await self.room.send_to_room(
            f"{c['cyan']}{self.name} takes a defensive stance in front of {target.name}.{c['reset']}",
            exclude=[self.owner, target]
        )

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

    async def _order_position(self, position: str):
        """Order pet to sit, stand, sleep, or rest."""
        c = self.config.COLORS
        self.position = position
        
        messages = {
            'sitting': f"{self.name} sits down.",
            'standing': f"{self.name} stands up.",
            'sleeping': f"{self.name} curls up and goes to sleep.",
            'resting': f"{self.name} settles down to rest.",
        }
        
        if self.room:
            await self.room.send_to_room(f"{c['cyan']}{messages.get(position, f'{self.name} changes position.')}{c['reset']}")
        
        # Stop following if sleeping
        if position == 'sleeping':
            if not hasattr(self, 'ai_state'):
                self.ai_state = {}
            self.ai_state['staying'] = True
        elif position == 'standing':
            # Resume following when standing
            if hasattr(self, 'ai_state'):
                self.ai_state['staying'] = False

    async def _order_move(self, direction: str):
        """Order pet to move to another room."""
        c = self.config.COLORS
        
        # Normalize direction
        dir_map = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}
        direction = dir_map.get(direction, direction)
        
        if not self.room or direction not in self.room.exits:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} can't go that way.{c['reset']}")
            return
        
        exit_data = self.room.exits[direction]
        if not exit_data or not exit_data.get('room'):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} can't go that way.{c['reset']}")
            return
        
        target_room = exit_data['room']
        old_room = self.room
        
        # Leave current room
        await old_room.send_to_room(f"{self.name} leaves {direction}.")
        old_room.characters.remove(self)
        
        # Enter new room
        self.room = target_room
        target_room.characters.append(self)
        await target_room.send_to_room(f"{self.name} arrives.")
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} moves {direction}.{c['reset']}")
        
        # Mark as staying so it doesn't immediately follow back
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        self.ai_state['staying'] = True

    async def _order_recall(self):
        """Order pet to recall to owner's current room."""
        c = self.config.COLORS
        if not self.owner or not getattr(self.owner, 'room', None):
            return

        # Leave current room
        if self.room:
            await self.room.send_to_room(f"{c['bright_cyan']}{self.name} vanishes in a flash of light!{c['reset']}")
            if self in self.room.characters:
                self.room.characters.remove(self)

        # Enter owner's room
        self.room = self.owner.room
        self.owner.room.characters.append(self)
        self.fighting = None
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        self.ai_state['staying'] = False

        await self.owner.room.send_to_room(
            f"{c['bright_cyan']}{self.name} appears beside {self.owner.name}.{c['reset']}")
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} recalls to you.{c['reset']}")

    async def _order_disengage(self):
        """Order pet to stop fighting."""
        c = self.config.COLORS
        if not self.is_fighting:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} isn't fighting anyone.{c['reset']}")
            return
        
        enemy = self.fighting
        
        # End combat
        if enemy and hasattr(enemy, 'fighting') and enemy.fighting == self:
            enemy.fighting = None
        self.fighting = None
        self.position = 'standing'
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} disengages from combat.{c['reset']}")
        if self.room:
            await self.room.send_to_room(
                f"{self.name} backs away from the fight.",
                exclude=[self.owner] if self.owner else []
            )

    async def _order_flee(self):
        """Order pet to flee from combat."""
        c = self.config.COLORS
        import random
        
        if not self.is_fighting:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} isn't fighting anyone.{c['reset']}")
            return
        
        if not self.room or not self.room.exits:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['red']}{self.name} has nowhere to flee!{c['reset']}")
            return
        
        # Pick random exit
        available_exits = [d for d, e in self.room.exits.items() if e and e.get('room')]
        if not available_exits:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['red']}{self.name} has nowhere to flee!{c['reset']}")
            return
        
        direction = random.choice(available_exits)
        enemy = self.fighting
        
        # End combat
        if enemy and hasattr(enemy, 'fighting') and enemy.fighting == self:
            enemy.fighting = None
        self.fighting = None
        self.position = 'standing'
        
        # Move to new room
        target_room = self.room.exits[direction]['room']
        old_room = self.room
        
        await old_room.send_to_room(f"{self.name} flees {direction}!")
        old_room.characters.remove(self)
        
        self.room = target_room
        target_room.characters.append(self)
        await target_room.send_to_room(f"{self.name} arrives, panting.")
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['yellow']}{self.name} flees {direction}!{c['reset']}")
        
        # Mark staying so it doesn't immediately follow back
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        self.ai_state['staying'] = True

    async def _order_heel(self):
        """Order pet to return to owner immediately."""
        c = self.config.COLORS
        
        if not self.owner or not self.owner.room:
            return
        
        # Disengage from combat if fighting
        if self.is_fighting:
            enemy = self.fighting
            if enemy and hasattr(enemy, 'fighting') and enemy.fighting == self:
                enemy.fighting = None
            self.fighting = None
            self.position = 'standing'
        
        # Already with owner?
        if self.room == self.owner.room:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['green']}{self.name} is already at your side.{c['reset']}")
            # Clear staying flag
            if hasattr(self, 'ai_state'):
                self.ai_state['staying'] = False
            return
        
        # Move to owner
        if self.room:
            await self.room.send_to_room(f"{self.name} bounds away.")
            self.room.characters.remove(self)
        
        self.room = self.owner.room
        self.owner.room.characters.append(self)
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['green']}{self.name} returns to your side.{c['reset']}")
        await self.owner.room.send_to_room(
            f"{self.name} bounds over to {self.owner.name}.",
            exclude=[self.owner]
        )
        
        # Clear staying flag
        if hasattr(self, 'ai_state'):
            self.ai_state['staying'] = False

    async def _order_passive(self):
        """Set pet to passive mode - won't auto-attack."""
        c = self.config.COLORS
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        
        self.ai_state['mode'] = 'passive'
        self.ai_state['guarding'] = False
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['cyan']}{self.name} enters passive mode. It won't attack unless ordered.{c['reset']}")

    async def _order_defensive(self):
        """Set pet to defensive mode - only attacks if owner is attacked."""
        c = self.config.COLORS
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        
        self.ai_state['mode'] = 'defensive'
        self.ai_state['guarding'] = True
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['cyan']}{self.name} enters defensive mode. It will protect you if attacked.{c['reset']}")

    async def _order_aggressive(self):
        """Set pet to aggressive mode - always assists in combat."""
        c = self.config.COLORS
        if not hasattr(self, 'ai_state'):
            self.ai_state = {}
        
        self.ai_state['mode'] = 'aggressive'
        self.ai_state['guarding'] = True
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['cyan']}{self.name} enters aggressive mode. It will attack alongside you.{c['reset']}")

    async def _order_dismiss(self):
        """Dismiss the pet (release it)."""
        c = self.config.COLORS
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['yellow']}{self.name} looks at you sadly as you dismiss it.{c['reset']}")
        
        if self.room:
            await self.room.send_to_room(
                f"{self.name} wanders off into the distance.",
                exclude=[self.owner] if self.owner else []
            )
            if self in self.room.characters:
                self.room.characters.remove(self)
        
        # Remove from owner's pets
        if self.owner:
            if hasattr(self.owner, 'pets') and self in self.owner.pets:
                self.owner.pets.remove(self)
            if hasattr(self.owner, 'world') and self in self.owner.world.npcs:
                self.owner.world.npcs.remove(self)
        
        self.owner = None
        self.hp = 0  # Mark as dead (is_alive property checks hp > 0)

    async def _order_pick_lock(self, direction: str):
        """Order pet to pick a lock on a door."""
        c = self.config.COLORS
        import random
        
        # Check if pet can pick locks
        skills = getattr(self, 'skills', {})
        pick_skill = skills.get('pick_lock', 0)
        
        if pick_skill <= 0 and 'pick_lock' not in getattr(self, 'special_abilities', []):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} doesn't know how to pick locks.{c['reset']}")
            return
        
        if not direction:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}Usage: order pick <direction>{c['reset']}")
            return
        
        # Normalize direction
        dir_map = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}
        direction = dir_map.get(direction.lower(), direction.lower())
        
        if not self.room or direction not in self.room.exits:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}There's no exit in that direction.{c['reset']}")
            return
        
        exit_data = self.room.exits[direction]
        if not exit_data:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}There's no exit in that direction.{c['reset']}")
            return
        
        # Check if door exists and is locked
        if not exit_data.get('door'):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}There's no door to the {direction}.{c['reset']}")
            return
        
        if not exit_data.get('locked', False):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}The door to the {direction} isn't locked.{c['reset']}")
            return
        
        # Attempt to pick the lock
        difficulty = exit_data.get('pick_difficulty', 50)
        roll = random.randint(1, 100)
        
        if hasattr(self.owner, 'send'):
            await self.owner.send(f"{c['cyan']}{self.name} examines the lock to the {direction}...{c['reset']}")
        
        if roll <= pick_skill - difficulty + 50:
            # Success!
            exit_data['locked'] = False
            
            # Also unlock the other side
            other_room = exit_data.get('room')
            if other_room:
                reverse_dirs = {'north': 'south', 'south': 'north', 'east': 'west', 
                               'west': 'east', 'up': 'down', 'down': 'up'}
                reverse = reverse_dirs.get(direction)
                if reverse and reverse in other_room.exits:
                    other_exit = other_room.exits[reverse]
                    if other_exit:
                        other_exit['locked'] = False
            
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['bright_green']}{self.name} deftly picks the lock! *click*{c['reset']}")
            if self.room:
                await self.room.send_to_room(
                    f"{self.name} picks the lock to the {direction}.",
                    exclude=[self.owner] if self.owner else []
                )
        else:
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} fails to pick the lock.{c['reset']}")

    async def _order_sneak(self):
        """Toggle pet's sneak mode."""
        c = self.config.COLORS
        
        # Check if pet can sneak
        skills = getattr(self, 'skills', {})
        sneak_skill = skills.get('sneak', 0)
        
        if sneak_skill <= 0 and 'sneak' not in getattr(self, 'special_abilities', []):
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['yellow']}{self.name} doesn't know how to sneak.{c['reset']}")
            return
        
        if not hasattr(self, 'flags'):
            self.flags = set()
        
        if 'sneaking' in self.flags:
            self.flags.discard('sneaking')
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['cyan']}{self.name} stops sneaking.{c['reset']}")
        else:
            self.flags.add('sneaking')
            if hasattr(self.owner, 'send'):
                await self.owner.send(f"{c['cyan']}{self.name} melts into the shadows...{c['reset']}")

    async def process_ai(self):
        """Pet-specific AI behavior."""
        if not self.is_alive:
            return

        # Follow owner if not fighting and not staying
        if not self.is_fighting and not getattr(self, 'ai_state', {}).get('staying', False):
            await self._follow_owner()

        # Auto-assist unless in passive mode
        mode = getattr(self, 'ai_state', {}).get('mode', 'aggressive')
        if mode != 'passive':
            await self._guard_owner()

        # Decay loyalty if mistreated
        if self.hp < self.max_hp * 0.3:
            self.loyalty = max(0, self.loyalty - 1)

        # Role-based behavior
        if self.role == 'healer':
            await self._healer_ai()
        elif self.role == 'caster':
            await self._caster_ai()

    async def _follow_owner(self):
        """Follow owner to their room."""
        if not self.owner or not self.owner.room:
            return

        # Already in same room - clear staying flag since owner arrived
        if self.room == self.owner.room:
            if hasattr(self, 'ai_state') and self.ai_state.get('staying'):
                self.ai_state['staying'] = False
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
            # Make sure the target is still alive before joining
            target = self.owner.fighting
            if target and target.hp > 0 and target in self.room.characters:
                from combat import CombatHandler
                await CombatHandler.start_combat(self, target)

    async def _healer_ai(self):
        """Simple healer behavior for supportive pets."""
        if not self.owner or not self.room or self.room != self.owner.room:
            return

        now = time.time()
        cooldown = getattr(self, 'ai_state', {}).get('heal_cooldown', 0)
        if now < cooldown:
            return

        # Heal owner first, then self
        target = None
        if self.owner.hp < self.owner.max_hp * 0.6:
            target = self.owner
        elif self.hp < self.max_hp * 0.6:
            target = self

        if not target:
            return

        # Small chance each tick to heal
        if random.randint(1, 100) > 25:
            return

        heal_amount = max(5, int(self.level * 2))
        old_hp = target.hp
        target.hp = min(target.max_hp, target.hp + heal_amount)
        actual_heal = target.hp - old_hp

        if actual_heal <= 0:
            return

        c = self.config.COLORS
        await self.room.send_to_room(
            f"{c['bright_green']}{self.name} channels dark energy to mend {target.name}! [+{actual_heal}]{c['reset']}"
        )

        if hasattr(self, 'ai_state'):
            self.ai_state['heal_cooldown'] = now + 8

    async def _caster_ai(self):
        """Simple offensive caster behavior for pets."""
        if not self.is_fighting or not self.fighting or not self.room:
            return

        now = time.time()
        cooldown = getattr(self, 'ai_state', {}).get('cast_cooldown', 0)
        if now < cooldown:
            return

        if random.randint(1, 100) > 20:
            return

        target = self.fighting
        damage = Mobile.roll_dice('2d6') + max(1, self.level // 2)
        c = self.config.COLORS

        await self.room.send_to_room(
            f"{c['bright_magenta']}{self.name} unleashes a bolt of necrotic energy at {target.name}! [{damage}]{c['reset']}"
        )

        killed = await target.take_damage(damage, self)
        if killed:
            from combat import CombatHandler
            await CombatHandler.handle_death(self, target)

        if hasattr(self, 'ai_state'):
            self.ai_state['cast_cooldown'] = now + 6

    # ==================== PET SPECIAL ABILITIES ====================
    
    async def use_special_ability(self, ability_name: str, target=None):
        """Execute a pet's special ability during combat."""
        c = self.config.COLORS
        
        if ability_name == 'shield_wall':
            # Bone Knight - Taunt and damage reduction
            if not hasattr(self, 'shield_wall_active'):
                self.shield_wall_active = 0
            
            if self.shield_wall_active > 0:
                return  # Already active
            
            self.shield_wall_active = 3  # 3 rounds
            
            # Taunt all enemies in room to attack this pet
            if self.room:
                for char in self.room.characters:
                    if hasattr(char, 'is_fighting') and char.is_fighting and char != self and char != self.owner:
                        if not hasattr(char, 'owner'):  # Only taunt enemies, not other pets
                            char.target = self
                            char.fighting = self
                
                await self.room.send_to_room(
                    f"{c['bright_cyan']}{self.name} raises its shield and braces for impact!{c['reset']}",
                    exclude=[]
                )
            
            logger.info(f"{self.name} activated shield_wall for 3 rounds")
        
        elif ability_name == 'dark_heal':
            # Wraith Healer - Heal owner or other pet
            if not self.owner or not self.owner.room:
                return
            
            # Find lowest HP target (owner or other pets)
            targets = [self.owner]
            for char in self.owner.room.characters:
                if hasattr(char, 'owner') and char.owner == self.owner and char != self:
                    targets.append(char)
            
            # Find target with lowest HP percentage
            heal_target = min(targets, key=lambda t: t.hp / t.max_hp if t.max_hp > 0 else 1)
            
            # Heal for 2d8+10
            heal_amount = sum(random.randint(1, 8) for _ in range(2)) + 10
            old_hp = heal_target.hp
            heal_target.hp = min(heal_target.max_hp, heal_target.hp + heal_amount)
            actual_heal = heal_target.hp - old_hp
            
            if hasattr(heal_target, 'send'):
                await heal_target.send(f"{c['bright_green']}The wraith's dark magic mends your wounds for {actual_heal} HP!{c['reset']}")
            if heal_target != self and self.room:
                await self.room.send_to_room(
                    f"{c['green']}{self.name} channels healing energy into {heal_target.name}.{c['reset']}",
                    exclude=[heal_target]
                )
            
            logger.info(f"{self.name} dark_heal healed {heal_target.name} for {actual_heal} HP")
        
        elif ability_name == 'necrotic_bolt':
            # Lich Acolyte - Ranged damage attack
            if not target or not hasattr(target, 'hp'):
                return
            
            damage = sum(random.randint(1, 6) for _ in range(3)) + self.level
            
            if self.room:
                await self.room.send_to_room(
                    f"{c['bright_magenta']}{self.name} fires a bolt of death magic at {target.name}!{c['reset']}",
                    exclude=[]
                )
            
            # Apply damage to target
            if hasattr(target, 'take_damage'):
                await target.take_damage(damage, self)
            else:
                target.hp -= damage
            
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}The necrotic bolt hits you for {damage} damage!{c['reset']}")
            
            # 20% chance to apply weakness curse
            if random.randint(1, 100) <= 20:
                if hasattr(target, 'str'):
                    if not hasattr(target, 'curse_of_weakness_rounds'):
                        target.curse_of_weakness_rounds = 0
                    target.curse_of_weakness_rounds = 3
                    target.str = max(3, target.str - 2)
                    if hasattr(target, 'send'):
                        await target.send(f"{c['yellow']}You feel weakened by the curse!{c['reset']}")
            
            logger.info(f"{self.name} necrotic_bolt dealt {damage} damage to {target.name}")
        
        elif ability_name == 'backstab':
            # Shadow Stalker - Backstab from stealth
            if not target or not hasattr(target, 'hp'):
                return
            
            # Check if hidden/sneaking
            is_stealthy = 'hidden' in self.flags or 'sneaking' in self.flags
            
            base_damage = sum(random.randint(1, 4) for _ in range(2))
            
            if is_stealthy:
                # 4x damage from stealth
                damage = base_damage * 4
                self.flags.discard('hidden')  # Break stealth
                if self.room:
                    await self.room.send_to_room(
                        f"{c['bright_red']}{self.name} materializes behind {target.name} and backstabs!{c['reset']}",
                        exclude=[]
                    )
            else:
                damage = base_damage
                if self.room:
                    await self.room.send_to_room(
                        f"{c['red']}{self.name} strikes at {target.name}!{c['reset']}",
                        exclude=[]
                    )
            
            # Apply damage
            if hasattr(target, 'take_damage'):
                await target.take_damage(damage, self)
            else:
                target.hp -= damage
            
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{self.name} backstabs you for {damage} damage!{c['reset']}")
            
            # Set backstab cooldown (2-3 rounds)
            self.backstab_cooldown = random.randint(2, 3)
            
            logger.info(f"{self.name} backstab dealt {damage} damage to {target.name}")
    
    async def ai_combat_tick(self):
        """AI behavior during combat - use special abilities automatically."""
        if not self.is_fighting or not self.target:
            return
        
        # Check if we have special_abilities attribute
        if not hasattr(self, 'special_abilities'):
            return
        
        # Use abilities based on what this pet has
        if 'shield_wall' in self.special_abilities:
            # Bone Knight - use shield wall when low HP or owner under attack
            should_use = False
            if self.hp < self.max_hp * 0.5:
                should_use = True
            elif self.owner and hasattr(self.owner, 'is_fighting') and self.owner.is_fighting:
                should_use = True
            
            if should_use:
                if not hasattr(self, 'shield_wall_active'):
                    self.shield_wall_active = 0
                if self.shield_wall_active == 0:
                    await self.use_special_ability('shield_wall')
        
        elif 'dark_heal' in self.special_abilities:
            # Wraith Healer - heal when owner or pets below 60% HP
            if self.owner:
                needs_heal = self.owner.hp < self.owner.max_hp * 0.6
                
                if not needs_heal:
                    # Check other pets
                    for char in self.room.characters if self.room else []:
                        if hasattr(char, 'owner') and char.owner == self.owner and char != self:
                            if char.hp < char.max_hp * 0.6:
                                needs_heal = True
                                break
                
                if needs_heal:
                    # Cooldown on healing (every 2 rounds)
                    if not hasattr(self, 'heal_cooldown'):
                        self.heal_cooldown = 0
                    
                    if self.heal_cooldown == 0:
                        await self.use_special_ability('dark_heal')
                        self.heal_cooldown = 2
                    else:
                        self.heal_cooldown -= 1
        
        elif 'necrotic_bolt' in self.special_abilities:
            # Lich - cast bolt on cooldown
            if not hasattr(self, 'bolt_cooldown'):
                self.bolt_cooldown = 0
            
            if self.bolt_cooldown == 0 and self.target:
                await self.use_special_ability('necrotic_bolt', self.target)
                self.bolt_cooldown = 2  # 2 round cooldown
            else:
                self.bolt_cooldown = max(0, self.bolt_cooldown - 1)
        
        elif 'backstab' in self.special_abilities:
            # Shadow Stalker - backstab from stealth
            if not hasattr(self, 'backstab_cooldown'):
                self.backstab_cooldown = 0
            
            # Try to backstab if stealthed or cooldown is up
            if self.backstab_cooldown == 0:
                is_stealthy = 'hidden' in self.flags or 'sneaking' in self.flags
                if is_stealthy and self.target:
                    await self.use_special_ability('backstab', self.target)
                elif not is_stealthy and random.randint(1, 100) <= 30:
                    # 30% chance to re-stealth after 2-3 rounds
                    self.flags.add('hidden')
            else:
                self.backstab_cooldown -= 1
        
        # Decrement shield wall counter
        if hasattr(self, 'shield_wall_active') and self.shield_wall_active > 0:
            self.shield_wall_active -= 1


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
        'name': 'bone vanguard',
        'short_desc': 'a bone vanguard',
        'long_desc': 'A bone vanguard stands here, its marrow-white armor rattling.',
        'pet_type': 'undead',
        'level_mult': 0.7,
        'duration': 3600,  # 60 minutes
        'hp_dice': '6d8+20',
        'damage_dice': '1d8',
        'special_abilities': ['undead', 'immune_poison'],
        'flags': ['undead'],
    },
    'ghoul': {
        'name': 'grave ghoul',
        'short_desc': 'a grave ghoul',
        'long_desc': 'A grave ghoul shambles here, hungry for the warmth of flesh.',
        'pet_type': 'undead',
        'level_mult': 0.9,
        'duration': 2700,  # 45 minutes
        'hp_dice': '8d8+40',
        'damage_dice': '2d6',
        'special_abilities': ['paralyzing_touch', 'disease'],
        'flags': ['undead'],
    },
    'zombie': {
        'name': 'rotting thrall',
        'short_desc': 'a rotting thrall',
        'long_desc': 'A rotting thrall lurches here, bound by necromantic will.',
        'pet_type': 'undead',
        'level_mult': 0.6,
        'duration': 3600,
        'hp_dice': '10d8+50',
        'damage_dice': '1d6',
        'special_abilities': ['undead', 'slow'],
        'flags': ['undead'],
    },
    'wight': {
        'name': 'death wraith',
        'short_desc': 'a death wraith',
        'long_desc': 'A death wraith stands here, exuding chilling dread.',
        'pet_type': 'undead',
        'level_mult': 1.0,
        'duration': 1800,  # 30 minutes
        'hp_dice': '9d8+45',
        'damage_dice': '2d8',
        'special_abilities': ['energy_drain', 'fear_aura'],
        'flags': ['undead'],
    },

    # Necromancer servant roles (temporary, requires corpse)
    'undead_warrior': {
        'name': 'bone knight',
        'short_desc': 'a bone knight',
        'long_desc': 'A bone knight stands guard, rusted shield raised in silence.',
        'pet_type': 'undead',
        'role': 'warrior',
        'guard_owner': True,
        'level_mult': 0.9,
        'duration': 3600,
        'hp_dice': '12d8+70',
        'damage_dice': '2d6',
        'special_abilities': ['undead', 'shield_wall'],
        'flags': ['undead'],
    },
    'undead_healer': {
        'name': 'wraith healer',
        'short_desc': 'a wraith healer',
        'long_desc': 'A wraith healer whispers rites that knit flesh with cold light.',
        'pet_type': 'undead',
        'role': 'healer',
        'level_mult': 0.7,
        'duration': 3600,
        'hp_dice': '7d8+30',
        'damage_dice': '1d6',
        'special_abilities': ['undead', 'dark_heal'],
        'flags': ['undead'],
    },
    'undead_caster': {
        'name': 'lich acolyte',
        'short_desc': 'a lich acolyte',
        'long_desc': 'A lich acolyte crackles with foul necromancy.',
        'pet_type': 'undead',
        'role': 'caster',
        'level_mult': 0.8,
        'duration': 3600,
        'hp_dice': '6d8+25',
        'damage_dice': '1d4+1',
        'special_abilities': ['undead', 'necrotic_bolt'],
        'flags': ['undead'],
    },
    'undead_rogue': {
        'name': 'shadow stalker',
        'short_desc': 'a shadow stalker',
        'long_desc': 'A shadow stalker drifts at the edge of sight, poised to strike.',
        'pet_type': 'undead',
        'role': 'rogue',
        'level_mult': 0.85,
        'duration': 3600,
        'hp_dice': '7d8+35',
        'damage_dice': '2d4',
        'special_abilities': ['undead', 'backstab', 'pick_lock', 'sneak'],
        'flags': ['undead', 'stealth', 'sneaking'],
        'skills': {'sneak': 85, 'hide': 80, 'pick_lock': 75, 'backstab': 70},
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
        if template.get('pet_type') == 'undead':
            max_undead = (owner.level // 10) + 1
            current_undead = [p for p in current_pets if p.pet_type == 'undead']
            if len(current_undead) >= max_undead:
                c = Config().COLORS
                if hasattr(owner, 'send'):
                    await owner.send(
                        f"{c['red']}You can't control more than {max_undead} undead servants!{c['reset']}"
                    )
                return None
        else:
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

        # Role-based behaviors
        pet.role = template.get('role')
        if template.get('guard_owner'):
            pet.ai_state['guarding'] = True

        # Set duration for temporary pets
        if template['pet_type'] in ('summon', 'undead'):
            base_duration = duration_minutes * 60
            
            # Soul fragment bonus: +20% duration per fragment
            if hasattr(owner, 'soul_fragments') and owner.soul_fragments > 0:
                import time
                if time.time() < getattr(owner, 'soul_fragment_expires', 0):
                    bonus = base_duration * 0.20 * owner.soul_fragments
                    base_duration = int(base_duration + bonus)
                    
                    # Consume a fragment for the bonus
                    owner.soul_fragments -= 1
                    c = Config().COLORS
                    if hasattr(owner, 'send'):
                        await owner.send(f"{c['cyan']}Soul fragment consumed! Pet duration extended to {base_duration // 60} minutes!{c['reset']}")
            
            pet.timer = base_duration

        # Add flags
        for flag in template.get('flags', []):
            pet.flags.add(flag)

        # Add special abilities
        pet.special_abilities = template.get('special_abilities', [])
        
        # Add skills from template
        if 'skills' in template:
            pet.skills = template['skills'].copy()

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
        owner = pet.owner

        # Remove from group members
        if hasattr(owner, 'group_members') and pet in owner.group_members:
            owner.group_members.remove(pet)
        
        # Remove from world
        if pet.room and pet in pet.room.characters:
            await pet.room.send_to_room(
                f"{c['yellow']}{pet.name} fades away.{c['reset']}"
            )
            pet.room.characters.remove(pet)

        if pet in owner.world.npcs:
            owner.world.npcs.remove(pet)

        # Remove from companions list if persistent
        if pet.is_persistent and hasattr(owner, 'companions'):
            if pet in owner.companions:
                owner.companions.remove(pet)
        
        # Clear the pet's owner reference
        pet.owner = None
        pet.hp = 0

        logger.info(f"{owner.name} dismissed {pet.name}")

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
