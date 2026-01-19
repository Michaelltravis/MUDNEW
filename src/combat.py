"""
RealmsMUD Combat System
=======================
Handles all combat mechanics.
"""

import random
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Character, Player

from config import Config

logger = logging.getLogger('RealmsMUD.Combat')


class CombatHandler:
    """Handles combat mechanics."""

    config = Config()

    @classmethod
    def get_health_color(cls, health_pct: float) -> str:
        """Get color code based on health percentage."""
        c = cls.config.COLORS
        if health_pct > 75:
            return c['bright_green']
        elif health_pct > 50:
            return c['green']
        elif health_pct > 25:
            return c['yellow']
        elif health_pct > 10:
            return c['red']
        else:
            return c['bright_red']

    @classmethod
    def get_health_bar(cls, health_pct: float) -> str:
        """Get a visual health bar based on health percentage."""
        bar_length = 10
        filled = int((health_pct / 100) * bar_length)
        empty = bar_length - filled
        return f"[{'█' * filled}{'░' * empty}]"

    @classmethod
    async def start_combat(cls, attacker: 'Character', defender: 'Character'):
        """Initiate combat between two characters."""
        attacker.fighting = defender
        defender.fighting = attacker
        attacker.position = 'fighting'
        defender.position = 'fighting'

        # Break stealth for both combatants
        if hasattr(attacker, 'flags'):
            attacker.flags.discard('hidden')
            attacker.flags.discard('sneaking')
        if hasattr(defender, 'flags'):
            defender.flags.discard('hidden')
            defender.flags.discard('sneaking')

        c = cls.config.COLORS
        
        if hasattr(attacker, 'send'):
            await attacker.send(f"{c['bright_red']}You attack {defender.name}!{c['reset']}")
        if hasattr(defender, 'send'):
            await defender.send(f"\r\n{c['bright_red']}{attacker.name} attacks you!{c['reset']}")
        if attacker.room:
            await attacker.room.send_to_room(
                f"{c['red']}{attacker.name} attacks {defender.name}!{c['reset']}",
                exclude=[attacker, defender]
            )
            
        # First strike
        await cls.one_round(attacker, defender)
        
    @classmethod
    async def one_round(cls, attacker: 'Character', defender: 'Character'):
        """Process one round of combat."""
        # Safety check: if either is dead, end combat
        if not attacker.is_alive or not defender.is_alive:
            await cls.end_combat(attacker, defender)
            return

        # Safety check: if defender is None or not in world, end combat
        if defender is None:
            attacker.fighting = None
            if attacker.position == 'fighting':
                attacker.position = 'standing'
            return

        # Safety check: if defender has no room (removed from world), end combat
        if not hasattr(defender, 'room') or defender.room is None:
            attacker.fighting = None
            if attacker.position == 'fighting':
                attacker.position = 'standing'
            return

        # Safety check: if not in same room, end combat
        if attacker.room != defender.room:
            await cls.end_combat(attacker, defender)
            return

        if not attacker.is_fighting or not defender.is_fighting:
            return
            
        c = cls.config.COLORS
        
        # Calculate hits
        hit_roll = random.randint(1, 20) + attacker.get_hit_bonus()
        defense = 10 + (defender.get_armor_class() // 10)
        
        if hit_roll >= defense:
            # Calculate damage
            weapon = attacker.equipment.get('wield') if hasattr(attacker, 'equipment') else None
            
            if weapon and hasattr(weapon, 'damage_dice'):
                damage = cls.roll_dice(weapon.damage_dice)
            else:
                # Bare hands
                damage = random.randint(1, 3)
                
            damage += attacker.get_damage_bonus()
            damage = max(1, damage)
            
            # Critical hit on natural 20
            if random.randint(1, 20) == 20:
                damage *= 2
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_yellow']}CRITICAL HIT!{c['reset']}")
                    
            damage_word = cls.get_damage_word(damage)
            
            # Send messages
            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['green']}Your {damage_word} {defender.name}. [{damage}]{c['reset']}")
            if hasattr(defender, 'send'):
                await defender.send(f"{c['red']}{attacker.name}'s {damage_word} you. [{damage}]{c['reset']}")

            # Apply damage
            killed = await defender.take_damage(damage, attacker)

            # Apply poison effects from envenomed weapon
            if not killed and weapon and hasattr(weapon, 'envenomed') and weapon.envenomed:
                await cls.apply_poison_effect(attacker, defender, weapon)

            # Show defender health to attacker (if attacker is a player)
            if hasattr(attacker, 'send') and not killed:
                health_pct = (defender.hp / defender.max_hp) * 100
                health_color = cls.get_health_color(health_pct)
                health_bar = cls.get_health_bar(health_pct)
                await attacker.send(f"{c['cyan']}{defender.name} {health_color}{health_bar} [{defender.hp}/{defender.max_hp}]{c['reset']}")

            if killed:
                await cls.handle_death(attacker, defender)
        else:
            # Miss
            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['yellow']}You miss {defender.name}.{c['reset']}")
            if hasattr(defender, 'send'):
                await defender.send(f"{c['cyan']}{attacker.name} misses you.{c['reset']}")
                
        # Check for second attack
        if hasattr(attacker, 'skills') and 'second_attack' in attacker.skills:
            if random.randint(1, 100) <= attacker.skills['second_attack']:
                await cls.bonus_attack(attacker, defender)
                
        # Check for third attack
        if hasattr(attacker, 'skills') and 'third_attack' in attacker.skills:
            if random.randint(1, 100) <= attacker.skills['third_attack'] // 2:
                await cls.bonus_attack(attacker, defender)

        # Pet attacks (if attacker has pets)
        if hasattr(attacker, 'world'):
            from pets import PetManager
            pets = PetManager.get_player_pets(attacker)
            for pet in pets:
                if pet.room == attacker.room and pet.is_alive and not pet.is_fighting:
                    # Pet joins combat to help owner
                    if random.randint(1, 100) <= 50:  # 50% chance per round
                        await cls.pet_attack(pet, defender)

    @classmethod
    async def pet_attack(cls, pet: 'Character', defender: 'Character'):
        """Process a pet attack."""
        if not pet.is_alive or not defender.is_alive:
            return

        c = cls.config.COLORS

        # Calculate hit
        hit_roll = random.randint(1, 20) + pet.get_hit_bonus()
        defense = 10 + (defender.get_armor_class() // 10)

        if hit_roll >= defense:
            # Calculate damage
            damage = cls.roll_dice(pet.damage_dice) if hasattr(pet, 'damage_dice') else random.randint(1, 4)
            damage += pet.get_damage_bonus()
            damage = max(1, damage)

            damage_word = cls.get_damage_word(damage)

            # Send messages
            await pet.room.send_to_room(
                f"{c['green']}{pet.name}'s {damage_word} {defender.name}! [{damage}]{c['reset']}"
            )

            # Apply damage
            killed = await defender.take_damage(damage, pet)
            if killed:
                await cls.handle_death(pet, defender)
        else:
            # Miss
            await pet.room.send_to_room(
                f"{c['yellow']}{pet.name} misses {defender.name}.{c['reset']}"
            )

    @classmethod
    async def bonus_attack(cls, attacker: 'Character', defender: 'Character'):
        """Process a bonus attack."""
        if not attacker.is_alive or not defender.is_alive:
            return
            
        c = cls.config.COLORS
        hit_roll = random.randint(1, 20) + attacker.get_hit_bonus()
        defense = 10 + (defender.get_armor_class() // 10)
        
        if hit_roll >= defense:
            weapon = attacker.equipment.get('wield') if hasattr(attacker, 'equipment') else None
            
            if weapon and hasattr(weapon, 'damage_dice'):
                damage = cls.roll_dice(weapon.damage_dice)
            else:
                damage = random.randint(1, 3)
                
            damage += attacker.get_damage_bonus()
            damage = max(1, damage)
            damage_word = cls.get_damage_word(damage)
            
            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['green']}Your {damage_word} {defender.name}. [{damage}]{c['reset']}")
            if hasattr(defender, 'send'):
                await defender.send(f"{c['red']}{attacker.name}'s {damage_word} you. [{damage}]{c['reset']}")
                
            killed = await defender.take_damage(damage, attacker)
            if killed:
                await cls.handle_death(attacker, defender)
                
    @classmethod
    async def handle_death(cls, killer: 'Character', victim: 'Character'):
        """Handle a combat death."""
        c = cls.config.COLORS
        
        # Award experience to killer
        if hasattr(killer, 'gain_exp') and hasattr(victim, 'exp'):
            exp_gain = getattr(victim, 'exp', 100)
            # Scale by level difference
            level_diff = getattr(victim, 'level', 1) - getattr(killer, 'level', 1)
            if level_diff > 0:
                exp_gain = int(exp_gain * (1 + level_diff * 0.1))
            elif level_diff < -5:
                exp_gain = int(exp_gain * 0.1)  # Much lower level = almost no exp
                
            await killer.gain_exp(exp_gain)
            if hasattr(killer, 'send'):
                await killer.send(f"{c['bright_yellow']}You gain {exp_gain} experience points!{c['reset']}")

        # Check quest progress for kills
        if hasattr(killer, 'active_quests') and hasattr(victim, 'name'):
            from quests import QuestManager
            await QuestManager.check_quest_progress(
                killer, 'kill', {'mob_name': victim.name, 'mob_vnum': getattr(victim, 'vnum', 0)}
            )

        # Handle gold and autoloot
        gold_looted = False
        items_looted = []

        # Check for autoloot_gold setting
        if hasattr(victim, 'gold') and victim.gold > 0:
            if hasattr(killer, 'gold'):
                # Autoloot gold is on by default for players
                if hasattr(killer, 'autoloot_gold') and killer.autoloot_gold:
                    killer.gold += victim.gold
                    if hasattr(killer, 'send'):
                        await killer.send(f"{c['yellow']}You get {victim.gold} gold coins from the corpse.{c['reset']}")
                    victim.gold = 0  # Remove gold so it doesn't appear in corpse
                    gold_looted = True

        # Check for autoloot items
        if hasattr(killer, 'autoloot') and killer.autoloot and hasattr(victim, 'inventory'):
            if hasattr(killer, 'inventory'):
                for item in list(victim.inventory):
                    killer.inventory.append(item)
                    items_looted.append(item)
                    if hasattr(killer, 'send'):
                        await killer.send(f"{c['bright_cyan']}You get {item.short_desc} from the corpse.{c['reset']}")
                victim.inventory.clear()

        # Create corpse with remaining items (if not autolooted)
        if victim.room and hasattr(victim, 'inventory'):
            from objects import Object
            corpse = Object(0, killer.world if hasattr(killer, 'world') else None)
            corpse.name = f"corpse of {victim.name}"
            corpse.short_desc = f"the corpse of {victim.name}"
            corpse.room_desc = f"The corpse of {victim.name} lies here."
            corpse.item_type = 'container'
            corpse.capacity = 1000  # Large capacity for corpses
            corpse.container_flags = ['closeable']
            corpse.state = 'open'  # Corpses start open

            # Add remaining gold to corpse if not autolooted
            if hasattr(victim, 'gold') and victim.gold > 0 and not gold_looted:
                corpse.gold = victim.gold
            else:
                corpse.gold = 0

            # Add remaining items to corpse if not autolooted
            if not items_looted:
                corpse.contents = list(victim.inventory)
                victim.inventory.clear()
            else:
                corpse.contents = []

            victim.room.items.append(corpse)
            
        # End combat
        await cls.end_combat(killer, victim)
        
        # Remove NPC from world if it's a mob
        if not hasattr(victim, 'connection'):  # It's an NPC
            if victim.room and victim in victim.room.characters:
                victim.room.characters.remove(victim)
            if hasattr(killer, 'world') and victim in killer.world.npcs:
                killer.world.npcs.remove(victim)
                
    @classmethod
    async def end_combat(cls, char1: 'Character', char2: 'Character'):
        """End combat between two characters."""
        if char1.fighting == char2:
            char1.fighting = None
            if char1.position == 'fighting':
                char1.position = 'standing'
                
        if char2.fighting == char1:
            char2.fighting = None
            if char2.position == 'fighting':
                char2.position = 'standing'
                
    @classmethod
    async def attempt_flee(cls, player: 'Player'):
        """Attempt to flee from combat."""
        if not player.is_fighting:
            return
            
        c = cls.config.COLORS
        
        # Check for available exits
        available_exits = [d for d, e in player.room.exits.items() if e and e.get('room')]
        
        if not available_exits:
            await player.send(f"{c['red']}There's nowhere to flee to!{c['reset']}")
            return
            
        # Chance to flee based on dexterity
        flee_chance = 50 + (player.dex - 10) * 2
        
        if random.randint(1, 100) <= flee_chance:
            direction = random.choice(available_exits)
            enemy = player.fighting
            
            await cls.end_combat(player, enemy)
            
            await player.send(f"{c['yellow']}You flee {direction}!{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} flees {direction}!",
                exclude=[player]
            )
            
            # Move player
            from commands import CommandHandler
            await CommandHandler.cmd_move(player, direction)
            
            # Lose some experience
            exp_loss = int(player.exp * 0.01)
            player.exp = max(0, player.exp - exp_loss)
            await player.send(f"{c['yellow']}You lose {exp_loss} experience points.{c['reset']}")
        else:
            await player.send(f"{c['red']}PANIC! You couldn't escape!{c['reset']}")
            
    @classmethod
    async def do_kick(cls, player: 'Player'):
        """Execute kick skill."""
        if not player.is_fighting:
            return
            
        c = cls.config.COLORS
        target = player.fighting
        skill_level = player.skills.get('kick', 0)
        
        # Check if kick lands
        if random.randint(1, 100) <= skill_level:
            damage = random.randint(1, player.level) + (player.str - 10) // 2
            damage_word = cls.get_damage_word(damage)
            
            await player.send(f"{c['bright_green']}Your kick {damage_word} {target.name}! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{player.name}'s kick {damage_word} you! [{damage}]{c['reset']}")
                
            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
        else:
            await player.send(f"{c['yellow']}Your kick misses {target.name}!{c['reset']}")
            
    @classmethod
    async def do_bash(cls, player: 'Player'):
        """Execute bash skill."""
        if not player.is_fighting:
            return
            
        c = cls.config.COLORS
        target = player.fighting
        skill_level = player.skills.get('bash', 0)
        
        if random.randint(1, 100) <= skill_level:
            damage = random.randint(1, player.level // 2) + (player.str - 10) // 2
            damage_word = cls.get_damage_word(damage)
            
            await player.send(f"{c['bright_green']}You bash {target.name} to the ground! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{player.name} bashes you to the ground! [{damage}]{c['reset']}")
                
            # Bash can stun
            if random.randint(1, 100) <= 30:
                if hasattr(target, 'position'):
                    target.position = 'stunned'
                await player.send(f"{c['bright_yellow']}{target.name} is stunned!{c['reset']}")
                
            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
        else:
            await player.send(f"{c['yellow']}You fail to bash {target.name}!{c['reset']}")
            # Failed bash can make you fall
            if random.randint(1, 100) <= 20:
                await player.send(f"{c['red']}You fall to the ground!{c['reset']}")
                player.position = 'sitting'
                
    @classmethod
    async def do_backstab(cls, player: 'Player', target: 'Character'):
        """Execute backstab skill."""
        c = cls.config.COLORS
        skill_level = player.skills.get('backstab', 0)
        
        # Must have a piercing weapon
        weapon = player.equipment.get('wield')
        if not weapon or getattr(weapon, 'weapon_type', '') not in ('stab', 'pierce'):
            await player.send(f"{c['red']}You need a piercing weapon to backstab!{c['reset']}")
            return
            
        if random.randint(1, 100) <= skill_level:
            # Backstab does multiplied damage
            base_damage = cls.roll_dice(weapon.damage_dice) if hasattr(weapon, 'damage_dice') else random.randint(1, 4)
            multiplier = 2 + (player.level // 10)
            damage = base_damage * multiplier + player.get_damage_bonus()
            
            await player.send(f"{c['bright_green']}You backstab {target.name}! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{player.name} backstabs you! [{damage}]{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} backstabs {target.name}!",
                exclude=[player, target]
            )
            
            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
            else:
                # Start combat
                await cls.start_combat(player, target)
        else:
            await player.send(f"{c['yellow']}You fail to backstab {target.name}!{c['reset']}")
            # Failed backstab starts combat anyway
            await cls.start_combat(player, target)
            
    @classmethod
    def roll_dice(cls, dice_str: str) -> int:
        """Roll dice from a string like '2d6+4'."""
        try:
            # Parse dice string
            if '+' in dice_str:
                dice_part, bonus = dice_str.split('+')
                bonus = int(bonus)
            elif '-' in dice_str:
                dice_part, penalty = dice_str.split('-')
                bonus = -int(penalty)
            else:
                dice_part = dice_str
                bonus = 0
                
            num_dice, die_size = dice_part.split('d')
            num_dice = int(num_dice)
            die_size = int(die_size)
            
            total = sum(random.randint(1, die_size) for _ in range(num_dice))
            return total + bonus
            
        except Exception:
            return random.randint(1, 6)
            
    @classmethod
    async def do_envenom(cls, player: 'Player'):
        """Apply poison to weapon for extra damage."""
        c = cls.config.COLORS
        skill_level = player.skills.get('envenom', 0)

        weapon = player.equipment.get('wield')
        if not weapon:
            await player.send(f"{c['red']}You need to wield a weapon to envenom it!{c['reset']}")
            return

        # Check for existing poison
        if hasattr(weapon, 'envenomed') and weapon.envenomed:
            await player.send(f"{c['yellow']}Your weapon is already envenomed!{c['reset']}")
            return

        # Find poison vial in inventory
        poison_vial = None
        poison_type = None
        for item in player.inventory:
            if hasattr(item, 'item_type') and item.item_type == 'poison':
                poison_vial = item
                poison_type = getattr(item, 'poison_type', 'venom')
                break

        if not poison_vial:
            await player.send(f"{c['red']}You need a poison vial to envenom your weapon!{c['reset']}")
            await player.send(f"{c['yellow']}Hint: Buy poison vials from alchemists or rogue trainers.{c['reset']}")
            return

        # Get poison configuration
        poison_config = cls.config.POISON_TYPES.get(poison_type, cls.config.POISON_TYPES['venom'])

        # Cost move points
        if player.move < 10:
            await player.send(f"{c['red']}You are too exhausted to apply poison!{c['reset']}")
            return
        player.move -= 10

        if random.randint(1, 100) <= skill_level:
            # Success! Apply poison to weapon
            weapon.envenomed = True
            weapon.poison_type = poison_type
            weapon.poison_config = poison_config
            weapon.envenom_charges = 5 + (player.level // 3)  # Number of hits

            # Remove poison vial from inventory
            player.inventory.remove(poison_vial)

            # Success messages
            color_code = c.get(poison_config['color'], c['bright_green'])
            await player.send(
                f"{color_code}You carefully coat your {weapon.name} with {poison_config['name']}!{c['reset']}\n"
                f"{c['cyan']}Your weapon gleams with toxic energy. ({weapon.envenom_charges} charges){c['reset']}"
            )
            await player.room.send_to_room(
                f"{player.name} carefully applies a {poison_config['color']} substance to their weapon.",
                exclude=[player]
            )
        else:
            await player.send(f"{c['yellow']}You fumble and fail to properly apply the poison!{c['reset']}")
            # Failed envenom - chance to poison yourself
            if random.randint(1, 100) <= 15:
                await player.send(f"{c['red']}The {poison_config['name']} touches your skin! You feel ill!{c['reset']}")
                # Remove poison vial anyway (it was wasted)
                player.inventory.remove(poison_vial)

                # Apply poison effect to self
                from affects import AffectManager
                if poison_config['effect'] == 'poison':
                    affect_data = {
                        'name': 'poison',
                        'type': AffectManager.TYPE_DOT,
                        'applies_to': 'hp',
                        'value': poison_config.get('damage', 2),
                        'duration': poison_config.get('duration', 5),
                        'caster_level': player.level
                    }
                    AffectManager.apply_affect(player, affect_data)
                elif poison_config['effect'] == 'blind':
                    affect_data = {
                        'name': 'blindness',
                        'type': AffectManager.TYPE_FLAG,
                        'applies_to': 'blind',
                        'value': 1,
                        'duration': poison_config.get('duration', 5),
                        'caster_level': player.level
                    }
                    AffectManager.apply_affect(player, affect_data)
            else:
                # Just failed, keep the poison vial
                pass

    @classmethod
    async def apply_poison_effect(cls, attacker: 'Character', victim: 'Character', weapon):
        """Apply poison effect from envenomed weapon on hit."""
        from affects import AffectManager
        c = cls.config.COLORS

        # Get poison configuration
        poison_type = getattr(weapon, 'poison_type', 'venom')
        poison_config = getattr(weapon, 'poison_config', cls.config.POISON_TYPES['venom'])

        # Decrement charges
        weapon.envenom_charges -= 1

        # Get color for messages
        color_code = c.get(poison_config.get('color', 'green'), c['bright_green'])

        # Send poison hit messages
        if hasattr(attacker, 'send'):
            await attacker.send(f"{color_code}{poison_config['hit_message']}{c['reset']}")
        if hasattr(victim, 'send'):
            await victim.send(f"{color_code}{poison_config['victim_message']}{c['reset']}")

        # Room message
        if hasattr(attacker, 'room') and attacker.room:
            room_msg = poison_config['room_message'].format(
                attacker=attacker.name,
                victim=victim.name
            )
            await attacker.room.send_to_room(f"{color_code}{room_msg}{c['reset']}", exclude=[attacker, victim])

        # Apply poison effect based on type
        effect_type = poison_config.get('effect', 'poison')

        if effect_type == 'poison':
            # Damage over time
            affect_data = {
                'name': 'poison',
                'type': AffectManager.TYPE_DOT,
                'applies_to': 'hp',
                'value': poison_config.get('damage', 3),
                'duration': poison_config.get('duration', 8),
                'caster_level': getattr(attacker, 'level', 1)
            }
            AffectManager.apply_affect(victim, affect_data)

        elif effect_type == 'blind':
            # Blindness effect
            affect_data = {
                'name': 'blindness',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'blind',
                'value': 1,
                'duration': poison_config.get('duration', 6),
                'caster_level': getattr(attacker, 'level', 1)
            }
            AffectManager.apply_affect(victim, affect_data)

        elif effect_type == 'extra_damage':
            # Immediate extra damage
            extra_damage = poison_config.get('damage', 15)
            await victim.take_damage(extra_damage, attacker)
            if hasattr(victim, 'send'):
                await victim.send(f"{color_code}The venom burns! ({extra_damage} additional damage){c['reset']}")

        elif effect_type == 'silence':
            # Silence effect
            affect_data = {
                'name': 'silence',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'silenced',
                'value': 1,
                'duration': poison_config.get('duration', 5),
                'caster_level': getattr(attacker, 'level', 1)
            }
            AffectManager.apply_affect(victim, affect_data)

        elif effect_type == 'slow':
            # Slow effect (reduces dexterity)
            affect_data = {
                'name': 'slowed',
                'type': AffectManager.TYPE_MODIFY_STAT,
                'applies_to': 'dex',
                'value': poison_config.get('penalty', -2),
                'duration': poison_config.get('duration', 7),
                'caster_level': getattr(attacker, 'level', 1)
            }
            AffectManager.apply_affect(victim, affect_data)

        elif effect_type == 'weaken':
            # Weaken effect (reduces strength)
            stat = poison_config.get('stat', 'str')
            affect_data = {
                'name': 'weakened',
                'type': AffectManager.TYPE_MODIFY_STAT,
                'applies_to': stat,
                'value': poison_config.get('penalty', -3),
                'duration': poison_config.get('duration', 6),
                'caster_level': getattr(attacker, 'level', 1)
            }
            AffectManager.apply_affect(victim, affect_data)

        # Check if weapon poison is depleted
        if weapon.envenom_charges <= 0:
            weapon.envenomed = False
            weapon.poison_type = None
            weapon.poison_config = None
            weapon.envenom_charges = 0

            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['yellow']}The poison on your {weapon.name} has been depleted.{c['reset']}")

    @classmethod
    async def do_assassinate(cls, player: 'Player', target: 'Character'):
        """Execute a deadly assassination attack - high damage if undetected."""
        c = cls.config.COLORS
        skill_level = player.skills.get('assassinate', 0)

        # Must not be in combat
        if player.is_fighting:
            await player.send(f"{c['red']}You cannot assassinate while in combat!{c['reset']}")
            return

        # Target must not be fighting
        if target.is_fighting:
            await player.send(f"{c['red']}Your target is too alert to assassinate!{c['reset']}")
            return

        # Must have a piercing weapon
        weapon = player.equipment.get('wield')
        if not weapon or getattr(weapon, 'weapon_type', '') not in ('stab', 'pierce'):
            await player.send(f"{c['red']}You need a piercing weapon to assassinate!{c['reset']}")
            return

        # Check if player is hidden
        is_hidden = hasattr(player, 'affects') and 'hide' in player.affects

        # Check if target is marked (bonus damage)
        is_marked = hasattr(target, 'affects') and 'marked' in target.affects
        mark_bonus = 1.5 if is_marked else 1.0

        # Higher chance if hidden
        bonus = 20 if is_hidden else 0

        if random.randint(1, 100) <= skill_level + bonus:
            # Assassination damage - massive multiplier
            base_damage = cls.roll_dice(weapon.damage_dice) if hasattr(weapon, 'damage_dice') else random.randint(2, 8)
            multiplier = 4 + (player.level // 8)
            if is_hidden:
                multiplier += 2  # Extra damage from stealth

            damage = int(base_damage * multiplier * mark_bonus) + player.get_damage_bonus() * 2

            # Remove hide
            if is_hidden:
                from affects import AffectManager
                AffectManager.remove_affect_by_name(player, 'hide')

            # Clear mark if present
            if is_marked:
                from affects import AffectManager
                AffectManager.remove_affect_by_name(target, 'marked')
                await player.send(f"{c['magenta']}Your mark flares as you strike!{c['reset']}")

            await player.send(f"{c['bright_red']}You strike {target.name} in a vital spot! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{player.name} strikes you from the shadows! [{damage}]{c['reset']}")
            await player.room.send_to_room(
                f"{c['red']}{player.name} emerges from the shadows and strikes {target.name} viciously!{c['reset']}",
                exclude=[player, target]
            )

            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
            else:
                await cls.start_combat(player, target)
        else:
            await player.send(f"{c['yellow']}Your assassination attempt fails!{c['reset']}")
            if is_hidden:
                from affects import AffectManager
                AffectManager.remove_affect_by_name(player, 'hide')
            await cls.start_combat(player, target)

    @classmethod
    async def do_garrote(cls, player: 'Player', target: 'Character'):
        """Strangle a target from behind, silencing and damaging over time."""
        c = cls.config.COLORS
        skill_level = player.skills.get('garrote', 0)

        # Must not be in combat
        if player.is_fighting:
            await player.send(f"{c['red']}You cannot garrote while in combat!{c['reset']}")
            return

        if target.is_fighting:
            await player.send(f"{c['red']}Your target is too alert to garrote!{c['reset']}")
            return

        # Check if player is hidden (better chance)
        is_hidden = hasattr(player, 'affects') and 'hide' in player.affects
        bonus = 15 if is_hidden else 0

        if random.randint(1, 100) <= skill_level + bonus:
            # Remove hide
            if is_hidden:
                from affects import AffectManager
                AffectManager.remove_affect_by_name(player, 'hide')

            # Apply garrote effect
            damage = random.randint(player.level // 2, player.level) + (player.dex - 10) // 2

            await player.send(f"{c['bright_red']}You wrap a garrote around {target.name}'s throat! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{player.name} wraps something around your throat! You can't breathe!{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} garrotes {target.name} from behind!",
                exclude=[player, target]
            )

            # Apply silence effect
            from affects import AffectManager
            affect_data = {
                'name': 'silence',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'silenced',
                'value': 1,
                'duration': 3,
                'caster_level': player.level
            }
            AffectManager.apply_affect(target, affect_data)

            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
            else:
                await cls.start_combat(player, target)
        else:
            await player.send(f"{c['yellow']}Your garrote attempt fails!{c['reset']}")
            if is_hidden:
                from affects import AffectManager
                AffectManager.remove_affect_by_name(player, 'hide')
            await cls.start_combat(player, target)

    @classmethod
    async def do_shadow_step(cls, player: 'Player', target: 'Character'):
        """Teleport behind a target, ending up hidden."""
        c = cls.config.COLORS
        skill_level = player.skills.get('shadow_step', 0)

        if player.is_fighting:
            await player.send(f"{c['red']}You cannot shadow step while in combat!{c['reset']}")
            return

        # Cost move points
        if player.move < 20:
            await player.send(f"{c['red']}You are too exhausted to shadow step!{c['reset']}")
            return
        player.move -= 20

        if random.randint(1, 100) <= skill_level:
            await player.send(f"{c['magenta']}You dissolve into shadow and reappear behind {target.name}!{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} dissolves into shadows...",
                exclude=[player]
            )

            # If target is in different room, move there
            if target.room != player.room:
                # Remove from current room
                if player in player.room.characters:
                    player.room.characters.remove(player)
                # Add to target's room
                target.room.characters.append(player)
                player.room = target.room

                await target.room.send_to_room(
                    f"Shadows coalesce as {player.name} appears from nowhere!",
                    exclude=[player]
                )

            # Apply hide effect
            from affects import AffectManager
            affect_data = {
                'name': 'hide',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'hidden',
                'value': 1,
                'duration': 2,
                'caster_level': player.level
            }
            AffectManager.apply_affect(player, affect_data)

            await player.send(f"{c['cyan']}You are now hidden behind {target.name}.{c['reset']}")
        else:
            await player.send(f"{c['yellow']}You fail to step through the shadows!{c['reset']}")

    @classmethod
    async def do_mark_target(cls, player: 'Player', target: 'Character'):
        """Mark a target for death, increasing damage against them."""
        c = cls.config.COLORS
        skill_level = player.skills.get('mark_target', 0)

        # Check if already marked
        if hasattr(target, 'affects') and 'marked' in target.affects:
            await player.send(f"{c['yellow']}{target.name} is already marked for death!{c['reset']}")
            return

        # Cost mana
        if player.mana < 5:
            await player.send(f"{c['red']}You don't have enough energy to mark a target!{c['reset']}")
            return
        player.mana -= 5

        if random.randint(1, 100) <= skill_level:
            from affects import AffectManager
            duration = 10 + (player.level // 5)
            affect_data = {
                'name': 'marked',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'marked',
                'value': 1,
                'duration': duration,
                'caster_level': player.level
            }
            AffectManager.apply_affect(target, affect_data)

            await player.send(f"{c['magenta']}You mark {target.name} for death. A dark aura surrounds them.{c['reset']}")
            if hasattr(target, 'send'):
                await target.send(f"{c['magenta']}You feel a chill as {player.name} marks you for death!{c['reset']}")
            await player.room.send_to_room(
                f"A dark aura briefly surrounds {target.name}.",
                exclude=[player, target]
            )
        else:
            await player.send(f"{c['yellow']}You fail to mark {target.name}.{c['reset']}")

    @classmethod
    def get_damage_word(cls, damage: int) -> str:
        """Get a descriptive word for damage amount."""
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
