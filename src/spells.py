"""
RealmsMUD Spells
================
Magic system and spell effects.
"""

import random
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Player, Character

from config import Config
from affects import AffectManager

logger = logging.getLogger('RealmsMUD.Spells')

# Spell definitions
SPELLS = {
    # Offensive spells
    'magic_missile': {
        'name': 'Magic Missile',
        'mana_cost': 10,
        'damage_dice': '1d4+1',
        'damage_per_level': 1,
        'target': 'offensive',
        'message_self': 'You fire magic missiles at $N!',
        'message_room': '$n fires magic missiles at $N!',
    },
    'burning_hands': {
        'name': 'Burning Hands',
        'mana_cost': 15,
        'damage_dice': '1d6+2',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'Fire erupts from your hands, burning $N!',
        'message_room': 'Fire erupts from $n\'s hands, burning $N!',
    },
    'chill_touch': {
        'name': 'Chill Touch',
        'mana_cost': 15,
        'damage_dice': '1d8',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'You touch $N with your icy fingers!',
        'message_room': '$n touches $N with icy fingers!',
    },
    'fireball': {
        'name': 'Fireball',
        'mana_cost': 40,
        'damage_dice': '3d6+5',
        'damage_per_level': 3,
        'target': 'offensive',
        'message_self': 'You hurl a fireball at $N!',
        'message_room': '$n hurls a fireball at $N!',
    },
    'lightning_bolt': {
        'name': 'Lightning Bolt',
        'mana_cost': 35,
        'damage_dice': '3d6+3',
        'damage_per_level': 3,
        'target': 'offensive',
        'message_self': 'Lightning crackles from your fingers into $N!',
        'message_room': 'Lightning crackles from $n\'s fingers into $N!',
    },
    'harm': {
        'name': 'Harm',
        'mana_cost': 50,
        'damage_dice': '5d8',
        'damage_per_level': 0,
        'target': 'offensive',
        'message_self': 'You channel divine wrath into $N!',
        'message_room': '$n channels divine wrath into $N!',
    },
    'flamestrike': {
        'name': 'Flamestrike',
        'mana_cost': 60,
        'damage_dice': '4d8+10',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'A column of holy fire descends upon $N!',
        'message_room': 'A column of holy fire descends upon $N!',
    },
    
    # Healing spells
    'cure_light': {
        'name': 'Cure Light Wounds',
        'mana_cost': 10,
        'heal_dice': '1d8+2',
        'heal_per_level': 1,
        'target': 'defensive',
        'message_self': 'You feel a warm glow as minor wounds heal.',
        'message_other': '$N glows briefly as minor wounds heal.',
    },
    'cure_serious': {
        'name': 'Cure Serious Wounds',
        'mana_cost': 20,
        'heal_dice': '2d8+4',
        'heal_per_level': 2,
        'target': 'defensive',
        'message_self': 'You feel warmth spread through your body.',
        'message_other': '$N glows as wounds begin to close.',
    },
    'cure_critical': {
        'name': 'Cure Critical Wounds',
        'mana_cost': 35,
        'heal_dice': '3d8+6',
        'heal_per_level': 2,
        'target': 'defensive',
        'message_self': 'Divine energy courses through you, healing your wounds.',
        'message_other': 'Divine light surrounds $N, healing grievous wounds.',
    },
    'heal': {
        'name': 'Heal',
        'mana_cost': 50,
        'heal_dice': '100',  # Full heal
        'target': 'defensive',
        'message_self': 'A surge of divine power restores you completely!',
        'message_other': '$N is bathed in divine light and fully restored!',
    },
    'group_heal': {
        'name': 'Group Heal',
        'mana_cost': 80,
        'heal_dice': '2d8+10',
        'heal_per_level': 2,
        'target': 'group',
        'message_self': 'You invoke a healing blessing upon your group!',
        'message_room': '$n invokes a healing blessing!',
    },
    
    # Buff spells
    'armor': {
        'name': 'Armor',
        'mana_cost': 15,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'ac', 'value': -20}],
        'message_self': 'You feel protected by magical armor.',
        'message_other': '$N is surrounded by a shimmering shield.',
    },
    'bless': {
        'name': 'Bless',
        'mana_cost': 15,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'hitroll', 'value': 2}, {'type': 'damroll', 'value': 1}],
        'message_self': 'You feel righteous!',
        'message_other': '$N looks more confident.',
    },
    'sanctuary': {
        'name': 'Sanctuary',
        'mana_cost': 75,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'sanctuary', 'value': 1}],
        'message_self': 'A white aura surrounds you.',
        'message_other': 'A white aura surrounds $N.',
    },
    'haste': {
        'name': 'Haste',
        'mana_cost': 50,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'haste', 'value': 1}],
        'message_self': 'You feel yourself moving faster!',
        'message_other': '$N begins moving with supernatural speed.',
    },
    'invisibility': {
        'name': 'Invisibility',
        'mana_cost': 35,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'invisible', 'value': 1}],
        'message_self': 'You fade from view.',
        'message_other': '$N fades from view.',
    },
    'fly': {
        'name': 'Fly',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'fly', 'value': 1}],
        'message_self': 'Your feet lift off the ground!',
        'message_other': '$N rises into the air.',
    },
    
    # Debuff/Utility spells
    'sleep': {
        'name': 'Sleep',
        'mana_cost': 20,
        'target': 'offensive',
        'duration_ticks': 6,
        'affects': [{'type': 'sleep', 'value': 1}],
        'save': True,
        'message_self': '$N falls into a magical slumber!',
        'message_room': '$N falls into a magical slumber!',
    },
    'blindness': {
        'name': 'Blindness',
        'mana_cost': 25,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'blind', 'value': 1}, {'type': 'hitroll', 'value': -4}],
        'save': True,
        'message_self': '$N is struck blind!',
        'message_room': '$N clutches at their eyes, blinded!',
    },
    'poison': {
        'name': 'Poison',
        'mana_cost': 25,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'poison', 'value': 1}, {'type': 'str', 'value': -2}],
        'save': True,
        'message_self': '$N looks very ill.',
        'message_room': '$N looks very ill.',
    },
    'weaken': {
        'name': 'Weaken',
        'mana_cost': 20,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'str', 'value': -4}],
        'save': True,
        'message_self': '$N looks weaker.',
        'message_room': '$N\'s muscles seem to shrink.',
    },
    'fear': {
        'name': 'Fear',
        'mana_cost': 30,
        'target': 'offensive',
        'special': 'fear',
        'save': True,
        'message_self': '$N looks terrified!',
        'message_room': '$N cowers in fear!',
    },
    
    # Necromancy
    'animate_dead': {
        'name': 'Animate Dead',
        'mana_cost': 50,
        'target': 'special',
        'special': 'animate_dead',
        'message_self': 'You raise a corpse to serve you!',
        'message_room': '$n raises a corpse from the dead!',
    },
    'vampiric_touch': {
        'name': 'Vampiric Touch',
        'mana_cost': 30,
        'damage_dice': '2d6+2',
        'damage_per_level': 1,
        'target': 'offensive',
        'special': 'drain_hp',
        'message_self': 'You drain life force from $N!',
        'message_room': '$n drains life force from $N!',
    },
    'energy_drain': {
        'name': 'Energy Drain',
        'mana_cost': 60,
        'damage_dice': '3d8',
        'damage_per_level': 2,
        'target': 'offensive',
        'special': 'drain_exp',
        'message_self': 'You drain $N\'s life essence!',
        'message_room': '$n drains $N\'s life essence!',
    },
    
    # Utility
    'detect_magic': {
        'name': 'Detect Magic',
        'mana_cost': 10,
        'target': 'self',
        'duration_ticks': 24,
        'affects': [{'type': 'detect_magic', 'value': 1}],
        'message_self': 'Your eyes tingle.',
    },
    'identify': {
        'name': 'Identify',
        'mana_cost': 20,
        'target': 'object',
        'message_self': 'You examine the item closely...',
    },
    'teleport': {
        'name': 'Teleport',
        'mana_cost': 50,
        'target': 'self',
        'special': 'teleport',
        'message_self': 'You vanish in a flash of light!',
        'message_room': '$n vanishes in a flash of light!',
    },
    'word_of_recall': {
        'name': 'Word of Recall',
        'mana_cost': 15,
        'target': 'self',
        'special': 'recall',
        'message_self': 'You feel yourself being pulled to safety...',
        'message_room': '$n disappears in a flash of light!',
    },
}


class SpellHandler:
    """Handles spell casting and effects."""
    
    config = Config()
    
    @classmethod
    async def cast_spell(cls, caster: 'Player', spell_name: str, target_name: Optional[str] = None):
        """Cast a spell."""
        c = cls.config.COLORS
        
        # Get spell data
        spell = SPELLS.get(spell_name)
        if not spell:
            await caster.send(f"Unknown spell: {spell_name}")
            return
            
        # Check mana
        mana_cost = spell.get('mana_cost', 10)
        if caster.mana < mana_cost:
            await caster.send(f"{c['red']}You don't have enough mana to cast that spell.{c['reset']}")
            return
            
        # Check proficiency for failure
        proficiency = caster.spells.get(spell_name, 50)
        if random.randint(1, 100) > proficiency:
            caster.mana -= mana_cost // 2
            await caster.send(f"{c['yellow']}You lose your concentration and the spell fizzles.{c['reset']}")
            return
            
        # Get target
        target = await cls.get_target(caster, spell, target_name)
        if target is None and spell['target'] not in ('self', 'special', 'object'):
            await caster.send("Cast the spell on whom?")
            return
            
        # Deduct mana
        caster.mana -= mana_cost
        
        # Apply spell effect
        await cls.apply_spell(caster, target, spell, spell_name)
        
    @classmethod
    async def get_target(cls, caster: 'Player', spell: dict, target_name: Optional[str]) -> Optional['Character']:
        """Get the target for a spell."""
        target_type = spell.get('target', 'offensive')
        
        if target_type == 'self':
            return caster
            
        if target_type == 'defensive':
            # Defensive spells default to self
            if not target_name:
                return caster
            # Or can target others
            for char in caster.room.characters:
                if target_name.lower() in char.name.lower():
                    return char
            return None
            
        if target_type == 'offensive':
            # If already fighting, target opponent
            if caster.is_fighting and not target_name:
                return caster.fighting
                
            # Otherwise need explicit target
            if not target_name:
                return None
                
            for char in caster.room.characters:
                if char != caster and target_name.lower() in char.name.lower():
                    return char
            return None
            
        return caster
        
    @classmethod
    async def apply_spell(cls, caster: 'Player', target: 'Character', spell: dict, spell_name: str):
        """Apply a spell's effects."""
        c = cls.config.COLORS
        
        # Send cast messages
        if target == caster:
            if spell.get('message_self'):
                await caster.send(f"{c['bright_magenta']}{spell['message_self']}{c['reset']}")
        else:
            # Offensive message
            msg_self = spell.get('message_self', f'You cast {spell["name"]} at $N!')
            msg_self = msg_self.replace('$N', target.name).replace('$n', caster.name)
            await caster.send(f"{c['bright_magenta']}{msg_self}{c['reset']}")
            
            if hasattr(target, 'send'):
                msg_target = msg_self.replace('You', caster.name).replace('your', f"{caster.name}'s")
                await target.send(f"\r\n{c['bright_magenta']}{msg_target}{c['reset']}")
                
            msg_room = spell.get('message_room', f'{caster.name} casts {spell["name"]} at {target.name}!')
            msg_room = msg_room.replace('$N', target.name).replace('$n', caster.name)
            await caster.room.send_to_room(
                f"{c['bright_magenta']}{msg_room}{c['reset']}",
                exclude=[caster, target]
            )
            
        # Check for saving throw (for debuffs)
        if spell.get('save') and target != caster:
            save_roll = random.randint(1, 20) + target.wis // 2
            if save_roll > 10 + caster.level // 2:
                await caster.send(f"{c['yellow']}{target.name} resists your spell!{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['cyan']}You resist the spell!{c['reset']}")
                return
                
        # Apply damage spells
        if 'damage_dice' in spell:
            damage = cls.roll_dice(spell['damage_dice'])
            damage += spell.get('damage_per_level', 0) * caster.level

            # Apply weather modifier to damage
            if caster.room and caster.room.zone and hasattr(caster.room.zone, 'weather'):
                weather_mult = caster.room.zone.weather.get_spell_modifier(spell['name'])
                damage = int(damage * weather_mult)

            # Apply spell damage
            killed = await target.take_damage(damage, caster)
            
            await caster.send(f"{c['bright_red']}Your spell does {damage} damage to {target.name}!{c['reset']}")
            
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
            elif not caster.is_fighting and target != caster:
                # Start combat if not already fighting
                from combat import CombatHandler
                await CombatHandler.start_combat(caster, target)
                
            # Handle vampiric drain
            if spell.get('special') == 'drain_hp':
                heal_amount = damage // 2
                caster.hp = min(caster.max_hp, caster.hp + heal_amount)
                await caster.send(f"{c['bright_green']}You absorb {heal_amount} life force!{c['reset']}")
                
        # Apply healing spells
        elif 'heal_dice' in spell:
            heal_str = spell['heal_dice']
            if heal_str.isdigit():
                heal = int(heal_str)  # Fixed amount (like full heal)
                if heal == 100:  # Full heal
                    heal = target.max_hp - target.hp
            else:
                heal = cls.roll_dice(heal_str)
                heal += spell.get('heal_per_level', 0) * caster.level
                
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + heal)
            actual_heal = target.hp - old_hp
            
            if target == caster:
                await caster.send(f"{c['bright_green']}You heal {actual_heal} hit points!{c['reset']}")
            else:
                await caster.send(f"{c['bright_green']}You heal {target.name} for {actual_heal} hit points!{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['bright_green']}{caster.name} heals you for {actual_heal} hit points!{c['reset']}")
                    
        # Apply buff/debuff affects
        if 'affects' in spell:
            duration = spell.get('duration_ticks', 24)
            for affect in spell['affects']:
                await cls.apply_affect(target, affect, duration, spell['name'], caster.level)
                
        # Handle special spells
        if spell.get('special'):
            await cls.handle_special_spell(caster, target, spell)
            
    @classmethod
    async def apply_affect(cls, target: 'Character', affect: dict, duration: int, spell_name: str = 'unknown', caster_level: int = 1):
        """Apply a spell affect to a character using the AffectManager."""
        affect_type = affect['type']
        value = affect['value']

        # Determine if this is a stat modification or a flag
        stat_types = {'hitroll', 'damroll', 'ac', 'str', 'int', 'wis', 'dex', 'con', 'cha',
                     'armor_class', 'max_hp', 'max_mana', 'max_move'}
        flag_types = {'blind', 'invisible', 'sanctuary', 'haste', 'fly', 'detect_magic',
                     'detect_invisible', 'sense_life', 'waterwalk'}

        # Create affect data for AffectManager
        affect_data = {
            'name': spell_name,
            'duration': duration,
            'caster_level': caster_level,
            'applies_to': affect_type,
            'value': value
        }

        if affect_type in stat_types:
            # Convert 'ac' to 'armor_class' for consistency
            if affect_type == 'ac':
                affect_data['applies_to'] = 'armor_class'
            affect_data['type'] = AffectManager.TYPE_MODIFY_STAT
        elif affect_type in flag_types:
            affect_data['type'] = AffectManager.TYPE_FLAG
            affect_data['value'] = 1  # Flags are binary (on/off)
        elif affect_type == 'sleep':
            # Special case: sleep changes position immediately
            target.position = 'sleeping'
            affect_data['type'] = AffectManager.TYPE_FLAG
            affect_data['applies_to'] = 'sleeping'
        else:
            logger.warning(f"Unknown affect type '{affect_type}' for spell {spell_name}")
            return

        # Apply the affect using AffectManager
        AffectManager.apply_affect(target, affect_data)
                
    @classmethod
    async def handle_special_spell(cls, caster: 'Player', target: 'Character', spell: dict):
        """Handle special spell effects."""
        c = cls.config.COLORS
        special = spell.get('special')
        
        if special == 'recall':
            # Teleport to temple
            if caster.room:
                await caster.room.send_to_room(
                    f"{caster.name} disappears!",
                    exclude=[caster]
                )
                caster.room.characters.remove(caster)
                
            temple = caster.world.get_room(caster.config.STARTING_ROOM)
            if temple:
                caster.room = temple
                temple.characters.append(caster)
                await caster.do_look([])
                
        elif special == 'teleport':
            # Random teleport (dangerous!)
            rooms = list(caster.world.rooms.values())
            if rooms:
                new_room = random.choice(rooms)
                if caster.room:
                    caster.room.characters.remove(caster)
                caster.room = new_room
                new_room.characters.append(caster)
                await caster.send(f"{c['bright_cyan']}You materialize in a new location!{c['reset']}")
                await caster.do_look([])
                
        elif special == 'fear':
            # Make target flee
            if hasattr(target, 'flee'):
                await target.flee()
            elif hasattr(target, 'send'):
                await target.send(f"{c['yellow']}You are overcome with fear!{c['reset']}")
                # Player attempts to flee
                from commands import CommandHandler
                await CommandHandler.cmd_flee(target, [])
                
        elif special == 'drain_exp':
            # Drain experience
            if hasattr(target, 'exp'):
                drain = target.level * 100
                target.exp = max(0, target.exp - drain)
                await caster.send(f"{c['bright_red']}You drain {drain} experience from {target.name}!{c['reset']}")
                
    @classmethod
    async def apply_spell_effect(cls, caster: 'Player', target: 'Character', spell_name: str):
        """Apply a spell effect (for potions, scrolls, etc.)."""
        spell = SPELLS.get(spell_name)
        if spell:
            await cls.apply_spell(caster, target, spell, spell_name)
            
    @staticmethod
    def roll_dice(dice_str: str) -> int:
        """Roll dice from a string like '2d6+4'."""
        try:
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
            return max(1, total + bonus)
            
        except Exception:
            return random.randint(1, 8)
