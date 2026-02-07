"""
RealmsMUD Combat System
=======================
Handles all combat mechanics.
"""

import random
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Character, Player

from config import Config

logger = logging.getLogger('RealmsMUD.Combat')


class CombatHandler:
    """Handles combat mechanics."""

    config = Config()

    @classmethod
    def _ng_modifier(cls, player) -> float:
        cycle = getattr(player, 'ng_plus_cycle', 0) or 0
        nightmare = getattr(player, 'nightmare_mode', False)
        if cycle <= 0:
            return 1.0
        return 1.0 + (0.15 * cycle) + (0.25 if nightmare else 0.0)

    @classmethod
    def _apply_ng_scaling(cls, npc, player):
        cycle = getattr(player, 'ng_plus_cycle', 0) or 0
        if cycle <= 0:
            return
        nightmare = getattr(player, 'nightmare_mode', False)
        if not hasattr(npc, 'ng_base_stats'):
            npc.ng_base_stats = {
                'max_hp': npc.max_hp,
                'hp': npc.hp,
                'level': npc.level,
                'armor_class': npc.armor_class,
                'hitroll': npc.hitroll,
                'damroll': npc.damroll,
            }
            npc.ng_scaled_cycle = 0
            npc.ng_scaled_nightmare = False

        if npc.ng_scaled_cycle >= cycle and npc.ng_scaled_nightmare == nightmare:
            return

        base = npc.ng_base_stats
        mult = 1.0 + (0.25 * cycle) + (0.25 if nightmare else 0.0)
        npc.max_hp = max(1, int(base['max_hp'] * mult))
        npc.hp = min(npc.max_hp, max(1, int(base['hp'] * mult)))
        npc.level = base['level'] + cycle
        npc.armor_class = base['armor_class'] - (5 * cycle)
        npc.hitroll = base['hitroll'] + (2 * cycle)
        npc.damroll = base['damroll'] + (2 * cycle)
        npc.ng_scaled_cycle = cycle
        npc.ng_scaled_nightmare = nightmare

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
    async def call_guards_for_help(cls, guard: 'Character', attacker: 'Character'):
        """Guard calls for help - nearby guards within 3 rooms come to assist."""
        if not guard.room:
            return

        c = cls.config.COLORS

        # Announce the call for help
        await guard.room.send_to_room(
            f"{c['bright_yellow']}{guard.name} shouts 'GUARDS! HELP!'{c['reset']}"
        )

        # Find guards within 3 rooms using BFS
        from collections import deque
        visited = {guard.room.vnum}
        queue = deque([(guard.room, 0)])  # (room, distance)
        guards_to_summon = []

        while queue:
            current_room, distance = queue.popleft()

            if distance > 3:
                continue

            # Check for guards in this room (but not the original guard)
            for char in current_room.characters:
                if char == guard:
                    continue
                if not hasattr(char, 'flags'):
                    continue
                # Must be a helper guard, not already fighting, and not a player
                if 'helper' in char.flags and not char.is_fighting and not hasattr(char, 'connection'):
                    # Check if it's a guard-type mob (cityguard, guard, etc.)
                    if 'guard' in char.name.lower():
                        guards_to_summon.append((char, current_room, distance))

            # Explore adjacent rooms (only if distance < 3)
            if distance < 3:
                for direction, exit_data in current_room.exits.items():
                    if not exit_data or not exit_data.get('room'):
                        continue
                    # Don't go through closed doors
                    if 'door' in exit_data:
                        door = exit_data['door']
                        if door.get('state') == 'closed':
                            continue
                    target_room = exit_data['room']
                    if target_room.vnum not in visited:
                        visited.add(target_room.vnum)
                        queue.append((target_room, distance + 1))

        # Summon the guards (move them to the fight)
        for summoned_guard, from_room, distance in guards_to_summon:
            # Remove from old room
            if summoned_guard in from_room.characters:
                from_room.characters.remove(summoned_guard)
                await from_room.send_to_room(
                    f"{c['cyan']}{summoned_guard.name} rushes off to answer the call!{c['reset']}"
                )

            # Add to guard's room
            summoned_guard.room = guard.room
            guard.room.characters.append(summoned_guard)
            await guard.room.send_to_room(
                f"{c['bright_cyan']}{summoned_guard.name} arrives to help!{c['reset']}"
            )

            # Start combat with the attacker
            if not summoned_guard.is_fighting:
                summoned_guard.fighting = attacker
                summoned_guard.position = 'fighting'

    @classmethod
    async def start_combat(cls, attacker: 'Character', defender: 'Character'):
        """Initiate combat between two characters."""
        # Safety: don't start combat with dead targets
        if not defender or defender.hp <= 0:
            return
        if not attacker or attacker.hp <= 0:
            return

        attacker.fighting = defender
        defender.fighting = attacker
        attacker.position = 'fighting'
        defender.position = 'fighting'
        # Auto-target when entering combat
        if hasattr(attacker, 'target') and (not attacker.target or attacker.target not in attacker.room.characters):
            attacker.target = defender
        if hasattr(defender, 'target') and (not defender.target or defender.target not in defender.room.characters):
            defender.target = attacker

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

        # Apply NG+ scaling to NPCs facing NG+ players
        if hasattr(attacker, 'connection') and not hasattr(defender, 'connection'):
            cls._apply_ng_scaling(defender, attacker)
        if hasattr(defender, 'connection') and not hasattr(attacker, 'connection'):
            cls._apply_ng_scaling(attacker, defender)

        # Guards call for help when attacked (helper flag)
        if hasattr(defender, 'flags') and 'helper' in defender.flags:
            await cls.call_guards_for_help(defender, attacker)

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

        if not attacker.is_fighting or attacker.fighting != defender:
            return
            
        c = cls.config.COLORS

        # Auto-combat skills/spells
        if hasattr(attacker, 'autocombat') and attacker.autocombat:
            await cls.auto_combat(attacker)

        # Calculate hits
        hit_roll = random.randint(1, 20) + attacker.get_hit_bonus()

        # Defensive skills (dodge/parry/shield block/blur)
        now = time.time()
        # Blur reduces hit chance
        if getattr(defender, 'blur_until', 0) > now:
            hit_roll -= 2
        # Feint debuff on defender
        if getattr(defender, 'ai_state', {}).get('feinted_until', 0) > now and getattr(defender.ai_state, 'feinted_by', None) == attacker:
            hit_roll += 2

        # Weather visibility penalty (outdoors only)
        outdoor_sectors = {
            'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim',
            'flying', 'desert', 'swamp'
        }
        if attacker.room and attacker.room.zone and attacker.room.sector_type in outdoor_sectors:
            weather = attacker.room.zone.weather
            if weather:
                vision_mod = weather.get_vision_modifier()
                if vision_mod < 1.0:
                    hit_roll -= int((1.0 - vision_mod) * 6)

        # Lower AC = better armor = harder to hit (higher defense)
        defense = 10 - (defender.get_armor_class() // 10)

        # Avoidance checks
        if hasattr(defender, 'skills'):
            dodge = defender.skills.get('dodge', 0)
            if dodge and random.randint(1, 100) <= dodge:
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['cyan']}You dodge {attacker.name}'s attack!{c['reset']}")
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['yellow']}{defender.name} dodges your attack!{c['reset']}")
                return
            parry = defender.skills.get('parry', 0)
            if parry and defender.equipment.get('wield') and random.randint(1, 100) <= parry:
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['cyan']}You parry {attacker.name}'s attack!{c['reset']}")
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['yellow']}{defender.name} parries your attack!{c['reset']}")
                return
            sblock = defender.skills.get('shield_block', 0)
            if sblock and defender.equipment.get('shield') and random.randint(1, 100) <= sblock:
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['cyan']}You block the attack with your shield!{c['reset']}")
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['yellow']}{defender.name} blocks your attack!{c['reset']}")
                return
            # Evasion (chance to avoid entirely)
            evasion = defender.skills.get('evasion', 0)
            if evasion and random.randint(1, 100) <= max(5, evasion // 2):
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['cyan']}You evade the attack!{c['reset']}")
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['yellow']}{defender.name} evades your attack!{c['reset']}")
                return

        if hit_roll >= defense:
            # Calculate damage
            weapon = attacker.equipment.get('wield') if hasattr(attacker, 'equipment') else None

            if weapon and hasattr(weapon, 'damage_dice'):
                damage = cls.roll_dice(weapon.damage_dice)
            else:
                # Bare hands
                damage = random.randint(1, 3)

            damage += attacker.get_damage_bonus()

            # Warrior stance damage modifiers
            if hasattr(attacker, 'stance'):
                if attacker.stance == 'berserk':
                    damage = int(damage * 1.25)  # +25% damage
                elif attacker.stance == 'defensive':
                    damage = int(damage * 0.75)  # -25% damage
                elif attacker.stance == 'precision':
                    damage = int(damage * 0.90)  # -10% damage
                    # But +15% crit chance handled separately

            # Apply talent passive bonuses
            if hasattr(attacker, 'talents') and attacker.talents:
                try:
                    from talents import TalentManager
                    talent_dmg_bonus = TalentManager.get_talent_bonus(attacker, 'damage_mod')
                    if talent_dmg_bonus > 0:
                        damage = int(damage * (1 + talent_dmg_bonus / 100))
                except Exception:
                    pass

            # Boss enrage bonus
            if getattr(attacker, 'is_boss', False) and getattr(attacker, 'ai_state', None):
                if attacker.ai_state.get('enraged'):
                    enrage_mult = getattr(attacker, 'enrage_multiplier', 1.5)
                    damage = int(damage * enrage_mult)

            # Boss vulnerability window
            if getattr(defender, 'is_boss', False):
                vulnerable_until = getattr(defender, 'ai_state', {}).get('vulnerable_until', 0)
                if time.time() < vulnerable_until:
                    damage = int(damage * 1.5)

            # NG+ enemy damage scaling
            if not hasattr(attacker, 'connection') and hasattr(defender, 'connection'):
                damage = int(damage * cls._ng_modifier(defender))

            # Sleeping targets take more damage
            if getattr(defender, 'position', '') == 'sleeping':
                damage = int(damage * 1.5)

            damage = max(1, damage)

            # Evasion/tumble mitigation
            if hasattr(defender, 'skills'):
                evasion = defender.skills.get('evasion', 0)
                if evasion and random.randint(1, 100) <= evasion:
                    damage = int(damage * 0.7)
            if getattr(defender, 'tumble_until', 0) > time.time():
                damage = int(damage * 0.8)
            damage = max(1, damage)

            # Critical hit check - percentage based
            # Base 5% + 1% per 2 DEX above 10 + 0.5% per level
            crit_chance = 5
            dex_bonus = (getattr(attacker, 'dex', 10) - 10) // 2
            crit_chance += dex_bonus
            crit_chance += attacker.level // 2 if hasattr(attacker, 'level') else 0

            # Class bonuses
            char_class = str(getattr(attacker, 'char_class', '')).lower()
            if char_class == 'thief':
                crit_chance += 10  # Thieves are crit machines
            elif char_class == 'warrior':
                crit_chance += 5
            elif char_class == 'ranger':
                crit_chance += 5

            # Precision stance: +15% crit chance
            if hasattr(attacker, 'stance') and attacker.stance == 'precision':
                crit_chance += 15

            # Cap at 50%
            crit_chance = min(crit_chance, 50)

            is_crit = random.randint(1, 100) <= crit_chance
            if is_crit:
                crit_mult = 2.0  # 200% damage
                # Thief gets better crits
                if char_class == 'thief':
                    crit_mult = 2.5  # 250% damage
                damage = int(damage * crit_mult)
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_yellow']}*** CRITICAL HIT! ***{c['reset']}")

            damage_word = cls.get_damage_word(damage)
            damage_color = cls.get_damage_color(damage)

            # Get weapon verb
            weapon_type = 'hit'
            if weapon and hasattr(weapon, 'weapon_type'):
                weapon_type = weapon.weapon_type
            you_verb, they_verb = cls.get_weapon_verb(weapon_type)

            # Send messages with enhanced formatting
            if hasattr(attacker, 'send'):
                if getattr(attacker, 'compact_mode', False):
                    await attacker.send(f"{c['green']}You {you_verb} {defender.name}. {damage_color}[{damage}]{c['reset']}")
                else:
                    await attacker.send(f"{c['green']}Your {damage_word} {they_verb} {defender.name}! {damage_color}[{damage} damage]{c['reset']}")
            if hasattr(defender, 'send'):
                if getattr(defender, 'compact_mode', False):
                    await defender.send(f"{c['red']}{attacker.name} {they_verb} you. {damage_color}[{damage}]{c['reset']}")
                else:
                    await defender.send(f"{c['red']}{attacker.name}'s {damage_word} {they_verb} you! {damage_color}[{damage} damage]{c['reset']}")

            # Bystander message
            try:
                if attacker.room:
                    await attacker.room.send_to_room(
                        f"{c['white']}{attacker.name} {they_verb} {defender.name}.{c['reset']}",
                        exclude=[attacker, defender]
                    )
            except Exception:
                pass

            # Apply damage
            killed = await defender.take_damage(damage, attacker)

            # Add grudge for hunting AI (mob remembers who attacked them)
            if hasattr(defender, 'add_grudge') and hasattr(attacker, 'connection'):
                # Defender is a mob, attacker is a player
                defender.add_grudge(attacker, damage)

            # Warrior rage generation on hit
            if hasattr(attacker, 'rage') and hasattr(attacker, 'char_class'):
                if attacker.char_class.lower() == 'warrior':
                    rage_gain = 5
                    if attacker.stance == 'berserk':
                        rage_gain = int(rage_gain * 1.5)  # +50% rage in berserk
                    attacker.rage = min(attacker.max_rage, attacker.rage + rage_gain)

            # Thief combo point generation on hit
            if hasattr(attacker, 'combo_points') and hasattr(attacker, 'char_class'):
                if attacker.char_class.lower() == 'thief':
                    if attacker.combo_target != defender:
                        attacker.combo_points = 0  # Reset if switching targets
                        attacker.combo_target = defender
                    if attacker.combo_points < 5:
                        attacker.combo_points += 1

            # Apply poison effects from envenomed weapon
            if not killed and weapon and hasattr(weapon, 'envenomed') and weapon.envenomed:
                await cls.apply_poison_effect(attacker, defender, weapon)

            # Show defender health to attacker (if attacker is a player)
            if hasattr(attacker, 'send') and not killed and not getattr(attacker, 'compact_mode', False):
                health_pct = (defender.hp / defender.max_hp) * 100
                health_color = cls.get_health_color(health_pct)
                health_bar = cls.get_health_bar(health_pct)
                await attacker.send(f"{c['cyan']}{defender.name} {health_color}{health_bar} [{defender.hp}/{defender.max_hp}]{c['reset']}")

            if killed:
                await cls.handle_death(attacker, defender)
        else:
            # Miss - with variety
            miss_messages_attacker = [
                f"You miss {defender.name}.",
                f"Your attack misses {defender.name}.",
                f"{defender.name} dodges your attack!",
                f"You swing at {defender.name} but miss!",
                f"Your attack goes wide!",
            ]
            miss_messages_defender = [
                f"{attacker.name} misses you.",
                f"You dodge {attacker.name}'s attack!",
                f"{attacker.name}'s attack goes wide!",
                f"You sidestep {attacker.name}'s strike!",
                f"{attacker.name} swings and misses!",
            ]
            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['yellow']}{random.choice(miss_messages_attacker)}{c['reset']}")
            if hasattr(defender, 'send'):
                if getattr(defender, 'compact_mode', False):
                    await defender.send(f"{c['cyan']}{attacker.name} misses.{c['reset']}")
                else:
                    await defender.send(f"{c['cyan']}{random.choice(miss_messages_defender)}{c['reset']}")

            # Bystander miss message
            try:
                if attacker.room:
                    await attacker.room.send_to_room(
                        f"{c['white']}{attacker.name} misses {defender.name}.{c['reset']}",
                        exclude=[attacker, defender]
                    )
            except Exception:
                pass

        # Check for second attack
        if hasattr(attacker, 'skills') and 'second_attack' in attacker.skills:
            if random.randint(1, 100) <= attacker.skills['second_attack']:
                await cls.bonus_attack(attacker, defender)

        # Check for third attack
        if hasattr(attacker, 'skills') and 'third_attack' in attacker.skills:
            if random.randint(1, 100) <= attacker.skills['third_attack'] // 2:
                await cls.bonus_attack(attacker, defender)

        # Dual wield off-hand attack
        if hasattr(attacker, 'skills') and 'dual_wield' in attacker.skills:
            if attacker.equipment.get('dual_wield') and random.randint(1, 100) <= attacker.skills['dual_wield']:
                await cls.offhand_attack(attacker, defender)

        # Ritual duration and channeling check
        if getattr(attacker, 'channeling_ritual', False):
            ritual_duration = getattr(attacker, 'ritual_duration', 0)
            if ritual_duration > 0:
                attacker.ritual_duration -= 1
            else:
                # Ritual ends
                attacker.channeling_ritual = False
                await attacker.send(f"{c['yellow']}Your dark ritual fades.{c['reset']}")

        # Pet attacks (if attacker has pets)
        if hasattr(attacker, 'world'):
            from pets import PetManager
            pets = PetManager.get_player_pets(attacker)
            for pet in pets:
                if pet.room == attacker.room and pet.is_alive:
                    # Decrement death pact duration
                    if hasattr(pet, 'death_pact_duration') and pet.death_pact_duration > 0:
                        pet.death_pact_duration -= 1
                        if pet.death_pact_duration <= 0:
                            # Pact expired
                            if hasattr(pet, 'death_pact_master') and pet.death_pact_master:
                                master = pet.death_pact_master
                                if hasattr(master, 'send'):
                                    await master.send(f"{c['yellow']}Your death pact with {pet.name} fades.{c['reset']}")
                                master.death_pact_target = None
                            pet.death_pact_master = None

                    # Apply ritual buff HP regen (5% per round)
                    if hasattr(pet, 'ritual_buff_duration') and pet.ritual_buff_duration > 0:
                        pet.ritual_buff_duration -= 1
                        regen = int(pet.max_hp * 0.05)
                        if regen > 0 and pet.hp < pet.max_hp:
                            old_hp = pet.hp
                            pet.hp = min(pet.max_hp, pet.hp + regen)
                            if pet.hp > old_hp:
                                await attacker.send(f"{c['bright_green']}{pet.name} regenerates {pet.hp - old_hp} HP from dark ritual!{c['reset']}")

                        if pet.ritual_buff_duration <= 0:
                            pet.ritual_bonuses = {}

                    # Trigger pet special abilities via AI
                    if hasattr(pet, 'ai_combat_tick'):
                        pet.target = defender  # Set target for abilities
                        pet.fighting = defender  # This makes is_fighting return True
                        await pet.ai_combat_tick()

                    # Pet joins combat to help owner
                    if not pet.is_fighting or random.randint(1, 100) <= 50:  # 50% chance per round
                        await cls.pet_attack(pet, defender)

    @classmethod
    async def auto_combat(cls, player: 'Player'):
        """Automatically use skills/spells based on player settings."""
        if not getattr(player, 'autocombat', False) or not player.is_fighting:
            return

        now = time.time()
        if now - getattr(player, 'last_autocombat_time', 0) < 1.8:
            return

        player.last_autocombat_time = now
        settings = getattr(player, 'auto_combat_settings', {})
        if not settings:
            return

        # Heal if below threshold
        try:
            heal_threshold = settings.get('heal_threshold', 35)
            hp_pct = (player.hp / player.max_hp) * 100 if player.max_hp > 0 else 0
            if hp_pct <= heal_threshold and settings.get('use_spells', True):
                heal_spells = settings.get('spell_priority', [])
                for spell in heal_spells:
                    if spell not in player.spells:
                        continue
                    spell_info = None
                    try:
                        from spells import SPELLS
                        spell_info = SPELLS.get(spell)
                    except Exception:
                        pass
                    if spell_info and spell_info.get('target') != 'defensive' and spell_info.get('target') != 'self':
                        continue

                    cooldown_key = f"spell:{spell}"
                    if player.auto_combat_cooldowns.get(cooldown_key, 0) > now:
                        continue

                    from spells import SpellHandler
                    await SpellHandler.cast_spell(player, spell)
                    player.auto_combat_cooldowns[cooldown_key] = now + 8
                    return
        except Exception:
            pass

        target = player.fighting
        if not target:
            return

        # Offensive spells
        if settings.get('use_spells', True):
            for spell in settings.get('spell_priority', []):
                if spell not in player.spells:
                    continue
                try:
                    from spells import SPELLS
                    spell_info = SPELLS.get(spell)
                    if not spell_info or spell_info.get('target') != 'offensive':
                        continue
                except Exception:
                    continue

                cooldown_key = f"spell:{spell}"
                if player.auto_combat_cooldowns.get(cooldown_key, 0) > now:
                    continue

                from spells import SpellHandler
                await SpellHandler.cast_spell(player, spell, target.name)
                player.auto_combat_cooldowns[cooldown_key] = now + 8
                return

        # Skills
        if settings.get('use_skills', True):
            skill_map = {
                'kick': cls.do_kick,
                'bash': cls.do_bash,
            }
            for skill in settings.get('skill_priority', []):
                if skill not in player.skills:
                    continue
                if skill not in skill_map:
                    continue

                cooldown_key = f"skill:{skill}"
                if player.auto_combat_cooldowns.get(cooldown_key, 0) > now:
                    continue

                await skill_map[skill](player)
                player.auto_combat_cooldowns[cooldown_key] = now + 6
                return

    @classmethod
    async def pet_attack(cls, pet: 'Character', defender: 'Character'):
        """Process a pet attack."""
        if not pet.is_alive or not defender.is_alive:
            return

        c = cls.config.COLORS

        # Calculate hit
        hit_roll = random.randint(1, 20) + pet.get_hit_bonus()
        # Lower AC = better armor = harder to hit (higher defense)
        defense = 10 - (defender.get_armor_class() // 10)

        if hit_roll >= defense:
            # Calculate damage
            damage = cls.roll_dice(pet.damage_dice) if hasattr(pet, 'damage_dice') else random.randint(1, 4)
            damage += pet.get_damage_bonus()

            special_attack = None
            if getattr(pet, 'role', None) == 'rogue' and random.randint(1, 100) <= 25:
                bonus = max(1, pet.level // 2) + random.randint(1, 4)
                damage += bonus
                special_attack = 'backstabs'

            damage = max(1, damage)

            damage_word = cls.get_damage_word(damage)
            attack_word = special_attack or damage_word

            # Send messages
            await pet.room.send_to_room(
                f"{c['green']}{pet.name} {attack_word} {defender.name}! [{damage}]{c['reset']}"
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
        # Lower AC = better armor = harder to hit (higher defense)
        defense = 10 - (defender.get_armor_class() // 10)

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
                if getattr(attacker, 'compact_mode', False):
                    await attacker.send(f"{c['green']}You hit {defender.name}. [{damage}]{c['reset']}")
                else:
                    await attacker.send(f"{c['green']}Your {damage_word} {defender.name}. [{damage}]{c['reset']}")
            if hasattr(defender, 'send'):
                if getattr(defender, 'compact_mode', False):
                    await defender.send(f"{c['red']}{attacker.name} hits you. [{damage}]{c['reset']}")
                else:
                    await defender.send(f"{c['red']}{attacker.name}'s {damage_word} you. [{damage}]{c['reset']}")

            killed = await defender.take_damage(damage, attacker)
            if killed:
                await cls.handle_death(attacker, defender)

    @classmethod
    async def offhand_attack(cls, attacker: 'Character', defender: 'Character'):
        """Process an off-hand dual wield attack."""
        if not attacker.is_alive or not defender.is_alive:
            return

        c = cls.config.COLORS
        hit_roll = random.randint(1, 20) + attacker.get_hit_bonus() - 2
        defense = 10 - (defender.get_armor_class() // 10)

        if hit_roll >= defense:
            weapon = attacker.equipment.get('dual_wield') if hasattr(attacker, 'equipment') else None
            if weapon and hasattr(weapon, 'damage_dice'):
                damage = int(cls.roll_dice(weapon.damage_dice) * 0.75)
            else:
                damage = random.randint(1, 2)
            damage += int(attacker.get_damage_bonus() * 0.5)
            damage = max(1, damage)
            damage_word = cls.get_damage_word(damage)

            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['green']}Your off-hand {damage_word} {defender.name}. [{damage}]{c['reset']}")
            if hasattr(defender, 'send'):
                await defender.send(f"{c['red']}{attacker.name}'s off-hand {damage_word} you. [{damage}]{c['reset']}")

            killed = await defender.take_damage(damage, attacker)
            if killed:
                await cls.handle_death(attacker, defender)
        else:
            if hasattr(attacker, 'send'):
                await attacker.send(f"{c['yellow']}Your off-hand misses {defender.name}.{c['reset']}")
            if hasattr(defender, 'send'):
                await defender.send(f"{c['cyan']}{attacker.name}'s off-hand misses you.{c['reset']}")

    @classmethod
    async def handle_death(cls, killer: 'Character', victim: 'Character'):
        """Handle a combat death."""
        c = cls.config.COLORS

        # Ensure equipped items are lootable
        if hasattr(victim, 'equipment') and hasattr(victim, 'inventory'):
            for item in list(victim.equipment.values()):
                if item:
                    victim.inventory.append(item)
            victim.equipment.clear()

        # Chance-based extra loot drops from loot_table
        if not hasattr(victim, 'connection') and hasattr(victim, 'loot_table') and hasattr(victim, 'inventory'):
            loot_table = getattr(victim, 'loot_table', [])
            # Support both old format (list) and new format (list of dicts with chance)
            if loot_table:
                from objects import create_object, create_preset_object
                for entry in loot_table:
                    if isinstance(entry, dict):
                        vnum = entry.get('vnum')
                        chance = entry.get('chance', 100)
                        if random.randint(1, 100) <= chance:
                            loot_obj = create_object(vnum, killer.world if hasattr(killer, 'world') else None) or create_preset_object(vnum)
                            if loot_obj:
                                victim.inventory.append(loot_obj)
                    else:
                        # Old format: just vnum with loot_chance
                        loot_chance = getattr(victim, 'loot_chance', 100)
                        if random.randint(1, 100) <= loot_chance:
                            loot_obj = create_object(entry, killer.world if hasattr(killer, 'world') else None) or create_preset_object(entry)
                            if loot_obj:
                                victim.inventory.append(loot_obj)
                                break  # Old format: one drop only

        # Universal rare drop chance for all mobs (consumables/gold)
        if not hasattr(victim, 'connection') and hasattr(victim, 'inventory'):
            mob_level = getattr(victim, 'level', 1)
            # 5% base + 1% per 5 mob levels (max 15% at level 50)
            rare_chance = 5 + (mob_level // 5)
            if random.randint(1, 100) <= rare_chance:
                from objects import create_object, create_preset_object
                # Common drops: healing potion, mana potion, food, gold bonus
                common_drops = [3134, 3135, 3101, 3130]  # heal pot, mana pot, bread, meat pie
                drop_vnum = random.choice(common_drops)
                drop_obj = create_object(drop_vnum, killer.world if hasattr(killer, 'world') else None) or create_preset_object(drop_vnum)
                if drop_obj:
                    victim.inventory.append(drop_obj)
                else:
                    # Fallback: bonus gold
                    bonus_gold = random.randint(5, 10) * mob_level
                    if hasattr(victim, 'gold'):
                        victim.gold += bonus_gold

        # Award experience to killer (or owner if killer is a pet)
        exp_recipient = killer
        # If killer is a pet, give exp to owner instead
        if hasattr(killer, 'owner') and killer.owner and hasattr(killer.owner, 'gain_exp'):
            exp_recipient = killer.owner
            # Notify owner their pet got the kill
            if hasattr(exp_recipient, 'send'):
                await exp_recipient.send(f"{c['cyan']}{killer.name} slays {victim.name}!{c['reset']}")

        if hasattr(exp_recipient, 'gain_exp') and hasattr(victim, 'exp'):
            exp_base = getattr(victim, 'exp', 100)
            killer_level = getattr(exp_recipient, 'level', 1)
            victim_level = getattr(victim, 'level', 1)
            level_diff = victim_level - killer_level

            # Smooth exp scaling curve:
            # +5 or more levels: +50% bonus (challenging)
            # +3 to +4 levels: +30% bonus
            # +1 to +2 levels: +15% bonus (sweet spot)
            # Same level: 100%
            # -1 to -2 levels: 80%
            # -3 to -4 levels: 50%
            # -5 to -7 levels: 25%
            # -8 or more: 10% (gray)
            if level_diff >= 5:
                exp_mult = 1.5
            elif level_diff >= 3:
                exp_mult = 1.3
            elif level_diff >= 1:
                exp_mult = 1.15
            elif level_diff >= -2:
                exp_mult = 1.0 if level_diff >= 0 else 0.8
            elif level_diff >= -4:
                exp_mult = 0.5
            elif level_diff >= -7:
                exp_mult = 0.25
            else:
                exp_mult = 0.1  # Gray mob

            exp_base = int(exp_base * exp_mult)

            bonuses = {'kill': exp_base}

            # Boss kill bonus
            boss_bonus = 0
            if getattr(victim, 'is_boss', False):
                boss_bonus = int(exp_base * exp_recipient.config.BOSS_XP_BONUS_PERCENT)
                if boss_bonus > 0:
                    bonuses['boss'] = boss_bonus

            # Kill streak bonus
            streak_bonus = 0
            if hasattr(exp_recipient, 'kill_streak'):
                exp_recipient.kill_streak = max(0, exp_recipient.kill_streak) + 1
                if hasattr(exp_recipient, 'best_kill_streak'):
                    exp_recipient.best_kill_streak = max(exp_recipient.best_kill_streak, exp_recipient.kill_streak)
                streak_mult = min(exp_recipient.config.STREAK_XP_BONUS_CAP,
                                  exp_recipient.kill_streak * exp_recipient.config.STREAK_XP_BONUS_PER_KILL)
                streak_bonus = int(exp_base * streak_mult)
                if streak_bonus > 0:
                    bonuses['streak'] = streak_bonus

            # Rested XP bonus
            rested_bonus = 0
            if hasattr(exp_recipient, 'rested_xp') and exp_recipient.rested_xp > 0:
                rested_bonus = min(exp_recipient.rested_xp, exp_base)
                exp_recipient.rested_xp -= rested_bonus
                if rested_bonus > 0:
                    bonuses['rested'] = rested_bonus

            total_gain = sum(bonuses.values())
            await exp_recipient.gain_exp(total_gain, breakdown=bonuses)
            if hasattr(exp_recipient, 'send'):
                await exp_recipient.send(f"{c['bright_yellow']}You gain {total_gain} experience points!{c['reset']}")
                bonus_parts = []
                if boss_bonus:
                    bonus_parts.append(f"Boss +{boss_bonus}")
                if streak_bonus:
                    bonus_parts.append(f"Streak +{streak_bonus}")
                if rested_bonus:
                    bonus_parts.append(f"Rested +{rested_bonus}")
                if bonus_parts:
                    await exp_recipient.send(f"{c['cyan']}Bonuses: {', '.join(bonus_parts)}{c['reset']}")

        # Check quest progress for kills (use exp_recipient for pet kills)
        quest_holder = exp_recipient if 'exp_recipient' in dir() else killer
        if hasattr(quest_holder, 'active_quests') and hasattr(victim, 'name'):
            from quests import QuestManager
            await QuestManager.check_quest_progress(
                quest_holder, 'kill', {'mob_name': victim.name, 'mob_vnum': getattr(victim, 'vnum', 0)}
            )

        # Check kill achievements
        if hasattr(exp_recipient, 'connection'):
            try:
                from achievements import AchievementManager
                await AchievementManager.check_kill(exp_recipient, victim)
            except Exception as e:
                logger.debug(f"Achievement check error: {e}")

        # Faction reputation loss for killing faction mobs
        if hasattr(killer, 'connection'):
            try:
                from factions import FactionManager
                faction_key = FactionManager.normalize_key(getattr(victim, 'faction', None))
                if faction_key:
                    rep_data = getattr(victim, 'faction_rep', None)
                    if isinstance(rep_data, dict):
                        await FactionManager.apply_reputation_changes(killer, rep_data, reason='Slaying a faction member')
                    else:
                        amount = rep_data if isinstance(rep_data, int) else -10
                        await FactionManager.apply_reputation_change(killer, faction_key, amount, reason='Slaying a faction member')
            except Exception:
                pass

        # Bestiary journal entry (first kill of this creature type)
        if hasattr(killer, 'connection'):
            try:
                from journal import JournalManager
                mob_key = f"{getattr(victim, 'vnum', 0)}_{getattr(victim, 'name', 'unknown').lower().replace(' ', '_')}"
                mob_name = getattr(victim, 'name', 'Unknown Creature')
                mob_level = getattr(victim, 'level', 1)
                mob_desc = getattr(victim, 'description', '') or getattr(victim, 'long_desc', '') or f"A level {mob_level} creature."
                location = killer.room.name if killer.room else 'Unknown'

                # Build a more detailed bestiary entry
                bestiary_content = f"{mob_desc}\n\nLevel: {mob_level}"
                if getattr(victim, 'is_boss', False):
                    bestiary_content += " (Boss)"

                await JournalManager.discover_creature(
                    killer, mob_key, mob_name, bestiary_content,
                    location=location,
                    metadata={'level': mob_level, 'vnum': getattr(victim, 'vnum', 0)}
                )
            except Exception:
                pass

            # Boss-specific achievements and titles
            if getattr(victim, 'is_boss', False):
                boss_achievement = getattr(victim, 'boss_achievement', None)
                if boss_achievement:
                    await AchievementManager._award_async(killer, boss_achievement)
                    try:
                        from collection_system import CollectionManager
                        await CollectionManager.record_trophy(killer, boss_achievement)
                    except Exception:
                        pass
                boss_title = getattr(victim, 'boss_title', None)
                if boss_title and hasattr(killer, 'title'):
                    killer.title = boss_title
                    if hasattr(killer, 'send'):
                        await killer.send(f"{c['bright_magenta']}You are now known as {boss_title}!{c['reset']}")

        # Soul Harvest for necromancers
        if hasattr(killer, 'char_class') and killer.char_class == 'necromancer':
            skill_level = getattr(killer, 'skills', {}).get('soul_harvest', 0)
            if skill_level > 0:
                # Calculate chance and max fragments based on skill level
                if skill_level < 26:
                    chance = 25
                    max_frags = 3
                    duration = 600  # 10 minutes
                elif skill_level < 51:
                    chance = 30
                    max_frags = 4
                    duration = 600
                elif skill_level < 76:
                    chance = 35
                    max_frags = 5
                    duration = 600
                else:
                    chance = 40
                    max_frags = 5
                    duration = 900  # 15 minutes

                if random.randint(1, 100) <= chance:
                    if not hasattr(killer, 'soul_fragments'):
                        killer.soul_fragments = 0
                    if not hasattr(killer, 'soul_fragment_expires'):
                        killer.soul_fragment_expires = 0

                    import time
                    now = time.time()

                    if killer.soul_fragments < max_frags:
                        killer.soul_fragments += 1
                        killer.soul_fragment_expires = now + duration

                        if hasattr(killer, 'send'):
                            await killer.send(
                                f"{c['bright_cyan']}You harvest a soul fragment! ({killer.soul_fragments}/{max_frags}){c['reset']}"
                            )
                            if killer.soul_fragments >= max_frags:
                                await killer.send(
                                    f"{c['yellow']}Soul fragments at maximum!{c['reset']}"
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
                    try:
                        from collection_system import CollectionManager
                        await CollectionManager.record_item(killer, item)
                    except Exception:
                        pass
                    if hasattr(killer, 'send'):
                        await killer.send(f"{c['bright_cyan']}You get {item.short_desc} from the corpse.{c['reset']}")
                victim.inventory.clear()

        # NG+ exclusive loot chance
        if hasattr(killer, 'connection') and getattr(killer, 'ng_plus_cycle', 0) > 0:
            chance = 8 + (2 * killer.ng_plus_cycle)
            if getattr(killer, 'nightmare_mode', False):
                chance += 6
            if random.randint(1, 100) <= chance:
                from objects import create_preset_object
                ng_item = create_preset_object(9400)
                if ng_item:
                    if hasattr(killer, 'inventory'):
                        killer.inventory.append(ng_item)
                        if hasattr(killer, 'send'):
                            await killer.send(f"{c['bright_magenta']}You recover {ng_item.short_desc} from the fallen!{c['reset']}")
                        try:
                            from collection_system import CollectionManager
                            await CollectionManager.record_item(killer, ng_item)
                        except Exception:
                            pass

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

        # Procedural dungeon boss completion
        if hasattr(killer, 'connection') and getattr(victim, 'is_dungeon_boss', False):
            from procedural import get_dungeon_manager
            manager = get_dungeon_manager()
            dungeon = manager.active_dungeons.get(killer.name)
            if dungeon and dungeon.get('id') == getattr(victim, 'dungeon_id', None):
                await manager.complete_dungeon(killer, dungeon)

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
            # If mobs are still attacking, set fighting to one of them
            if player.room:
                attackers = [ch for ch in player.room.characters if hasattr(ch, 'fighting') and ch.fighting == player]
                if attackers:
                    player.fighting = attackers[0]
                    player.position = 'fighting'
                else:
                    return
            else:
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
    async def do_kick(cls, player: 'Player', target: 'Character' = None):
        """Execute kick skill."""
        c = cls.config.COLORS

        # Use provided target or current fighting target
        if target is None:
            if not player.is_fighting:
                return
            target = player.fighting

        # Start combat if not already fighting
        if not player.is_fighting:
            await cls.start_combat(player, target)
        skill_level = player.get_skill_level('kick')

        # Check if kick lands
        if random.randint(1, 100) <= skill_level:
            damage = random.randint(1, player.level) + (player.str - 10) // 2
            damage = max(1, damage)
            damage_word = cls.get_damage_word(damage)

            if getattr(player, 'compact_mode', False):
                await player.send(f"{c['bright_green']}You kick {target.name}. [{damage}]{c['reset']}")
            else:
                await player.send(f"{c['bright_green']}Your kick {damage_word} {target.name}! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                if getattr(target, 'compact_mode', False):
                    await target.send(f"{c['bright_red']}{player.name} kicks you. [{damage}]{c['reset']}")
                else:
                    await target.send(f"{c['bright_red']}{player.name}'s kick {damage_word} you! [{damage}]{c['reset']}")

            killed = await target.take_damage(damage, player)
            if killed:
                await cls.handle_death(player, target)
        else:
            await player.send(f"{c['yellow']}Your kick misses {target.name}!{c['reset']}")

    @classmethod
    async def do_bash(cls, player: 'Player', target: 'Character' = None):
        """Execute bash skill."""
        c = cls.config.COLORS

        # Use provided target or current fighting target
        if target is None:
            if not player.is_fighting:
                return
            target = player.fighting

        # Start combat if not already fighting
        if not player.is_fighting:
            await cls.start_combat(player, target)
        skill_level = player.get_skill_level('bash')

        if random.randint(1, 100) <= skill_level:
            bash_die = max(1, player.level // 2)
            damage = random.randint(1, bash_die) + (player.str - 10) // 2
            damage = max(1, damage)
            damage_word = cls.get_damage_word(damage)

            if getattr(player, 'compact_mode', False):
                await player.send(f"{c['bright_green']}You bash {target.name}. [{damage}]{c['reset']}")
            else:
                await player.send(f"{c['bright_green']}You bash {target.name} to the ground! [{damage}]{c['reset']}")
            if hasattr(target, 'send'):
                if getattr(target, 'compact_mode', False):
                    await target.send(f"{c['bright_red']}{player.name} bashes you. [{damage}]{c['reset']}")
                else:
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
    async def do_backstab(cls, player: 'Player', target: 'Character') -> bool:
        """Execute backstab skill."""
        c = cls.config.COLORS
        skill_level = player.get_skill_level('backstab')

        # Must have a piercing weapon
        weapon = player.equipment.get('wield')
        if not weapon or getattr(weapon, 'weapon_type', '') not in ('stab', 'pierce'):
            await player.send(f"{c['red']}You need a piercing weapon to backstab!{c['reset']}")
            return False

        # Stealth/detection rolls
        env_bonus = 0
        try:
            if player.room and hasattr(player.room, 'is_dark') and player.room.is_dark(player.world.game_time):
                env_bonus += 20
            if player.room and player.room.sector_type in ('forest', 'swamp'):
                env_bonus += 10
        except Exception:
            pass
        if hasattr(player, 'has_light_source') and player.has_light_source():
            env_bonus -= 25

        sneak_skill = player.get_skill_level('sneak')
        hide_skill = player.get_skill_level('hide')
        stealth_roll = sneak_skill + (hide_skill // 2) + player.dex + env_bonus + random.randint(1, 20)
        target_wis = getattr(target, 'wis', 10)
        target_dex = getattr(target, 'dex', 10)
        detect_roll = ((target_wis + target_dex) // 2) + getattr(target, 'level', 1) + random.randint(1, 20)
        detected = detect_roll > stealth_roll

        # Success chance
        level_diff = player.level - getattr(target, 'level', player.level)
        chance = skill_level + (player.dex - target_dex) + (level_diff * 2)
        if 'hidden' in getattr(player, 'flags', set()):
            chance += 10
        if 'sneaking' in getattr(player, 'flags', set()):
            chance += 5
        if env_bonus > 0:
            chance += 5
        if detected:
            chance -= 20
        chance = max(5, min(95, chance))

        if random.randint(1, 100) <= chance:
            # Backstab does multiplied damage
            base_damage = cls.roll_dice(weapon.damage_dice) if hasattr(weapon, 'damage_dice') else random.randint(1, 4)
            multiplier = 2 + (player.level // 10)
            if 'hidden' in getattr(player, 'flags', set()):
                multiplier += 0.5
            if 'sneaking' in getattr(player, 'flags', set()):
                multiplier += 0.25
            if env_bonus > 0:
                multiplier += 0.25
            if env_bonus < 0:
                multiplier -= 0.5
            if detected:
                multiplier -= 0.5
            multiplier = max(1.0, multiplier)

            damage = int(base_damage * multiplier) + player.get_damage_bonus()
            # Gear backstab bonus (percentage of base damage)
            bs_bonus = player.get_equipment_bonus('backstab')
            if bs_bonus:
                damage += int(base_damage * (bs_bonus / 100))

            # Sleeping targets take extra damage
            if getattr(target, 'position', '') == 'sleeping':
                damage = int(damage * 1.5)

            # Rare execution (non-boss)
            flags = getattr(target, 'flags', set()) or set()
            is_boss = ('boss' in flags) or getattr(target, 'boss', False) or getattr(target, 'is_boss', False) or getattr(target, 'level', 0) >= 40
            if not is_boss:
                exec_chance = 0.5  # base %
                if level_diff >= 5:
                    exec_chance = min(1.5, exec_chance + 0.5)
                if level_diff < 0:
                    exec_chance = max(0.25, exec_chance * 0.5)
                if random.random() * 100 < exec_chance:
                    await player.send(f"{c['bright_red']}*** EXECUTION! ***{c['reset']}")
                    damage = max(damage, getattr(target, 'hp', 1))

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
            return True
        else:
            await player.send(f"{c['yellow']}You fail to backstab {target.name}!{c['reset']}")
            # Failed backstab starts combat anyway
            await cls.start_combat(player, target)
            return False

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
        skill_level = player.get_skill_level('envenom')

        weapon = player.equipment.get('wield')
        if not weapon:
            await player.send(f"{c['red']}You need to wield a weapon to envenom it!{c['reset']}")
            return

        # Check for existing poison
        if hasattr(weapon, 'envenomed') and weapon.envenomed:
            await player.send(f"{c['yellow']}Your weapon is already envenomed!{c['reset']}")
            return

        # Find poison vial in inventory (respect preferred poison type if set)
        poison_vial = None
        poison_type = None
        preferred = getattr(player, 'preferred_poison_type', None)
        for item in player.inventory:
            if hasattr(item, 'item_type') and item.item_type == 'poison':
                item_type = getattr(item, 'poison_type', 'venom')
                if preferred and item_type != preferred:
                    continue
                poison_vial = item
                poison_type = item_type
                break

        # fallback to any poison vial if preferred not found
        if not poison_vial:
            for item in player.inventory:
                if hasattr(item, 'item_type') and item.item_type == 'poison':
                    poison_vial = item
                    poison_type = getattr(item, 'poison_type', 'venom')
                    break

        if not poison_vial:
            await player.send(f"{c['red']}You need a poison vial to envenom your weapon!{c['reset']}")
            await player.send(f"{c['yellow']}Hint: Buy poison vials from alchemists or rogue trainers.{c['reset']}")
            player.preferred_poison_type = None
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
            player.preferred_poison_type = None
        else:
            await player.send(f"{c['yellow']}You fumble and fail to properly apply the poison!{c['reset']}")
            # Failed envenom - chance to poison yourself
            if random.randint(1, 100) <= 15:
                await player.send(f"{c['red']}The {poison_config['name']} touches your skin! You feel ill!{c['reset']}")
                # Remove poison vial anyway (it was wasted)
                player.inventory.remove(poison_vial)
                # Apply poison effect to self
                from affects import AffectManager
                if poison_config.get('effect') == 'poison':
                    affect_data = {
                        'name': 'poison',
                        'type': AffectManager.TYPE_DOT,
                        'applies_to': 'hp',
                        'value': poison_config.get('damage', 2),
                        'duration': poison_config.get('duration', 5),
                        'caster_level': player.level
                    }
                    AffectManager.apply_affect(player, affect_data)
                elif poison_config.get('effect') == 'blind':
                    affect_data = {
                        'name': 'blindness',
                        'type': AffectManager.TYPE_FLAG,
                        'applies_to': 'blind',
                        'value': 1,
                        'duration': poison_config.get('duration', 5),
                        'caster_level': player.level
                    }
                    AffectManager.apply_affect(player, affect_data)
            player.preferred_poison_type = None

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
        skill_level = player.get_skill_level('assassinate')

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
        skill_level = player.get_skill_level('garrote')

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
        skill_level = player.get_skill_level('shadow_step')

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
        skill_level = player.get_skill_level('mark_target')

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
        """Get a descriptive word for damage amount (CircleMUD style)."""
        if damage <= 0:
            return "miss"
        elif damage <= 2:
            return "tickle"
        elif damage <= 4:
            return "barely scratch"
        elif damage <= 6:
            return "scratch"
        elif damage <= 8:
            return "nick"
        elif damage <= 10:
            return "graze"
        elif damage <= 14:
            return "hit"
        elif damage <= 18:
            return "injure"
        elif damage <= 22:
            return "wound"
        elif damage <= 26:
            return "maul"
        elif damage <= 32:
            return "decimate"
        elif damage <= 40:
            return "devastate"
        elif damage <= 50:
            return "maim"
        elif damage <= 65:
            return "MUTILATE"
        elif damage <= 80:
            return "DISMEMBER"
        elif damage <= 100:
            return "MASSACRE"
        elif damage <= 140:
            return "OBLITERATE"
        else:
            return "*** ANNIHILATE ***"

    @classmethod
    def get_damage_color(cls, damage: int) -> str:
        """Get color code for damage amount."""
        c = Config().COLORS
        if damage <= 4:
            return c['white']
        elif damage <= 12:
            return c['green']
        elif damage <= 24:
            return c['yellow']
        elif damage <= 48:
            return c['bright_yellow']
        elif damage <= 80:
            return c['bright_red']
        else:
            return c['bright_magenta']

    @classmethod
    def get_weapon_verb(cls, weapon_type: str) -> tuple:
        """Get attack verb based on weapon type (CircleMUD style). Returns (you_verb, they_verb)."""
        verbs = {
            # CircleMUD standard weapon types
            'hit': ('hit', 'hits'),
            'sting': ('sting', 'stings'),
            'whip': ('whip', 'whips'),
            'slash': ('slash', 'slashes'),
            'bite': ('bite', 'bites'),
            'bludgeon': ('bludgeon', 'bludgeons'),
            'crush': ('crush', 'crushes'),
            'pound': ('pound', 'pounds'),
            'claw': ('claw', 'claws'),
            'maul': ('maul', 'mauls'),
            'thrash': ('thrash', 'thrashes'),
            'pierce': ('pierce', 'pierces'),
            'blast': ('blast', 'blasts'),
            'punch': ('punch', 'punches'),
            'stab': ('stab', 'stabs'),
            # Additional types
            'slice': ('slice', 'slices'),
            'cleave': ('cleave', 'cleaves'),
            'smash': ('smash', 'smashes'),
        }
        return verbs.get(weapon_type, ('hit', 'hits'))
