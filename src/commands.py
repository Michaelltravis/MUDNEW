"""
RealmsMUD Commands
==================
All player commands and their implementations.
"""

import logging
import random
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

from config import Config

logger = logging.getLogger('RealmsMUD.Commands')


class CommandHandler:
    """Handles all player commands."""
    
    # Command aliases
    ALIASES = {
        'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
        'u': 'up', 'd': 'down',
        'l': 'look', 'ex': 'examine',
        'i': 'inventory', 'inv': 'inventory',
        'eq': 'equipment', 'worn': 'equipment',
        'sc': 'score', 'stat': 'score',
        'k': 'kill', 'att': 'attack',
        "'": 'say', '"': 'say',
        ':': 'emote', 'me': 'emote',
        'gt': 'gtell', 'grouptell': 'gtell',
        'wh': 'who',
        'h': 'help', '?': 'help',
        'q': 'quit', 'exit': 'quit',
        'fl': 'flee',
        'dr': 'drink', 'ea': 'eat',
        'sl': 'sleep', 'wa': 'wake', 're': 'rest', 'st': 'stand',
        'op': 'open', 'cl': 'close',
        'ge': 'get', 'ta': 'take', 'pi': 'pick',
        'pu': 'put', 'dr': 'drop',
        'gi': 'give',
        'we': 'wear', 'wi': 'wield', 'ho': 'hold', 'rem': 'remove',
        'c': 'cast',
        'pr': 'practice',
        'whe': 'where',
        'con': 'consider',
    }
    
    @classmethod
    async def execute(cls, player: 'Player', cmd: str, args: List[str]):
        """Execute a command."""
        # Check aliases
        cmd = cls.ALIASES.get(cmd, cmd)
        
        # Find the command method
        method_name = f'cmd_{cmd}'
        method = getattr(cls, method_name, None)
        
        if method:
            await method(player, args)
        else:
            # Check if it's a direction
            if cmd in Config.DIRECTIONS:
                await cls.cmd_move(player, cmd)
            else:
                await player.send(f"Huh?!? '{cmd}' is not a valid command. Type 'help' for a list.")
    
    # ==================== MOVEMENT ====================
    
    @classmethod
    async def cmd_move(cls, player: 'Player', direction: str):
        """Move in a direction."""
        if not player.room:
            await player.send("You are nowhere!")
            return
            
        if player.position == 'sleeping':
            await player.send("You are sleeping! Wake up first.")
            return
            
        if player.position == 'fighting':
            await player.send("You're fighting! Flee if you want to escape.")
            return
            
        if player.position in ('resting', 'sitting'):
            await player.send("You need to stand up first.")
            return
            
        exit_data = player.room.exits.get(direction)
        if not exit_data:
            await player.send("You can't go that way.")
            return
            
        target_room = exit_data.get('room')
        if not target_room:
            await player.send("That exit seems to lead nowhere...")
            return
            
        # Check movement points
        sector = player.config.SECTOR_TYPES.get(target_room.sector_type, {'move_cost': 1})
        move_cost = sector['move_cost']
        
        if player.move < move_cost:
            await player.send("You are too exhausted to move!")
            return
            
        # Leave message
        await player.room.send_to_room(
            f"{player.name} leaves {direction}.",
            exclude=[player]
        )
        
        # Move player
        player.room.characters.remove(player)
        player.room = target_room
        target_room.characters.append(player)
        player.move -= move_cost
        
        # Arrival message
        opposite = Config.DIRECTIONS.get(direction, {}).get('opposite', 'somewhere')
        await target_room.send_to_room(
            f"{player.name} arrives from the {opposite}.",
            exclude=[player]
        )
        
        # Show new room
        await player.do_look([])
        
    @classmethod
    async def cmd_north(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'north')
        
    @classmethod
    async def cmd_south(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'south')
        
    @classmethod
    async def cmd_east(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'east')
        
    @classmethod
    async def cmd_west(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'west')
        
    @classmethod
    async def cmd_up(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'up')
        
    @classmethod
    async def cmd_down(cls, player: 'Player', args: List[str]):
        await cls.cmd_move(player, 'down')
    
    # ==================== INFORMATION ====================
    
    @classmethod
    async def cmd_look(cls, player: 'Player', args: List[str]):
        """Look at the room or something."""
        await player.do_look(args)
        
    @classmethod
    async def cmd_examine(cls, player: 'Player', args: List[str]):
        """Examine something in detail."""
        await player.do_look(args)

    @classmethod
    async def cmd_weather(cls, player: 'Player', args: List[str]):
        """Check the current weather."""
        c = player.config.COLORS

        if not player.room or not player.room.zone:
            await player.send("You can't sense any weather here.")
            return

        # Get zone weather
        weather = player.room.zone.weather
        game_time = player.world.game_time if hasattr(player, 'world') and player.world else None

        # Display weather information
        await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']} Weather Conditions{c['cyan']}                                            ║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")

        # Weather description
        desc = weather.get_weather_desc()
        await player.send(f"{c['cyan']}║ {c['white']}{desc:<59}{c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")

        # Temperature
        temp_f = weather.temperature
        temp_c = int((temp_f - 32) * 5 / 9)
        await player.send(f"{c['cyan']}║ {c['white']}Temperature: {temp_f}°F ({temp_c}°C){c['cyan']}                                      ║{c['reset']}")

        # Wind
        wind_desc = "calm"
        if weather.wind_speed > 25:
            wind_desc = "strong gale"
        elif weather.wind_speed > 15:
            wind_desc = "steady wind"
        elif weather.wind_speed > 8:
            wind_desc = "light breeze"
        await player.send(f"{c['cyan']}║ {c['white']}Wind: {wind_desc} ({weather.wind_speed} mph){c['cyan']}                                     ║{c['reset']}")

        # Time and season
        if game_time:
            season = game_time.get_season()
            time_str = game_time.get_short_time_string()
            await player.send(f"{c['cyan']}║ {c['white']}Time: {time_str} ({season}){c['cyan']}                                    ║{c['reset']}")

        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

    @classmethod
    async def cmd_score(cls, player: 'Player', args: List[str]):
        """Show player stats."""
        c = player.config.COLORS
        race_info = player.config.RACES.get(player.race, {})
        class_info = player.config.CLASSES.get(player.char_class, {})
        
        await player.send(f"{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']} {player.name} {player.title:<52}{c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}Race: {race_info.get('name', player.race):<12} Class: {class_info.get('name', player.char_class):<12} Level: {player.level:<3}{c['cyan']}    ║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['bright_red']}HP: {player.hp:>4}/{player.max_hp:<4}{c['cyan']}  {c['bright_cyan']}Mana: {player.mana:>4}/{player.max_mana:<4}{c['cyan']}  {c['bright_yellow']}Move: {player.move:>4}/{player.max_move:<4}{c['cyan']}   ║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}Str: {player.str:>2}   Int: {player.int:>2}   Wis: {player.wis:>2}   Dex: {player.dex:>2}   Con: {player.con:>2}   Cha: {player.cha:>2}{c['cyan']} ║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['bright_green']}Experience: {player.exp:<10}{c['cyan']} {c['bright_yellow']}Gold: {player.gold:<10}{c['cyan']} {c['white']}Practices: {player.practices:<3}{c['cyan']}  ║{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}To next level: {player.exp_to_level() - player.exp:<10}{c['cyan']}                              ║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}Armor Class: {player.get_armor_class():<4}  Hitroll: {player.hitroll:>+3}  Damroll: {player.damroll:>+3}{c['cyan']}            ║{c['reset']}")
        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}")
        
    @classmethod
    async def cmd_inventory(cls, player: 'Player', args: List[str]):
        """Show inventory."""
        c = player.config.COLORS
        await player.send(f"{c['cyan']}You are carrying:{c['reset']}")
        
        if not player.inventory:
            await player.send(f"  {c['white']}Nothing.{c['reset']}")
        else:
            for item in player.inventory:
                await player.send(f"  {c['yellow']}{item.short_desc}{c['reset']}")
                
    @classmethod
    async def cmd_equipment(cls, player: 'Player', args: List[str]):
        """Show equipped items."""
        c = player.config.COLORS
        await player.send(f"{c['cyan']}You are using:{c['reset']}")
        
        slot_names = {
            'light': '<used as light>',
            'finger1': '<worn on finger>',
            'finger2': '<worn on finger>',
            'neck1': '<worn around neck>',
            'neck2': '<worn around neck>',
            'body': '<worn on body>',
            'head': '<worn on head>',
            'legs': '<worn on legs>',
            'feet': '<worn on feet>',
            'hands': '<worn on hands>',
            'arms': '<worn on arms>',
            'shield': '<worn as shield>',
            'about': '<worn about body>',
            'waist': '<worn about waist>',
            'wrist1': '<worn on wrist>',
            'wrist2': '<worn on wrist>',
            'wield': '<wielded>',
            'hold': '<held>',
            'dual_wield': '<dual wielded>',
        }
        
        has_equipment = False
        for slot in player.config.WEAR_SLOTS:
            item = player.equipment.get(slot)
            if item:
                has_equipment = True
                slot_desc = slot_names.get(slot, f'<{slot}>')
                await player.send(f"  {c['green']}{slot_desc:20}{c['yellow']}{item.short_desc}{c['reset']}")
                
        if not has_equipment:
            await player.send(f"  {c['white']}Nothing.{c['reset']}")
            
    @classmethod
    async def cmd_who(cls, player: 'Player', args: List[str]):
        """Show online players."""
        c = player.config.COLORS
        players = player.world.players.values()
        
        await player.send(f"{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']}                    Players Online                            {c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        
        for p in players:
            race = player.config.RACES.get(p.race, {}).get('name', p.race)[:8]
            cls_name = player.config.CLASSES.get(p.char_class, {}).get('name', p.char_class)[:8]
            await player.send(f"{c['cyan']}║ {c['white']}[{p.level:>2} {race:<8} {cls_name:<8}] {c['bright_green']}{p.name} {p.title}{c['cyan']}{' ' * (62 - 25 - len(p.name) - len(p.title))}║{c['reset']}")
            
        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}{len(list(players))} player(s) online{' ' * 43}{c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}")
        
    @classmethod
    async def cmd_where(cls, player: 'Player', args: List[str]):
        """Show where players/mobs are."""
        c = player.config.COLORS
        
        if not args:
            # Show all players in zone
            await player.send(f"{c['cyan']}Players in your area:{c['reset']}")
            for p in player.world.players.values():
                if p.room and player.room and p.room.zone == player.room.zone:
                    await player.send(f"  {c['white']}{p.name:20} - {p.room.name}{c['reset']}")
        else:
            # Search for a specific mob/player
            target = ' '.join(args).lower()
            found = False
            
            # Search NPCs in zone
            for npc in player.world.npcs:
                if npc.room and player.room and npc.room.zone == player.room.zone:
                    if target in npc.name.lower():
                        await player.send(f"  {c['white']}{npc.name:20} - {npc.room.name}{c['reset']}")
                        found = True
                        
            # Search players
            for p in player.world.players.values():
                if p.room and player.room and p.room.zone == player.room.zone:
                    if target in p.name.lower():
                        await player.send(f"  {c['white']}{p.name:20} - {p.room.name}{c['reset']}")
                        found = True
                        
            if not found:
                await player.send(f"You don't sense '{target}' nearby.")
                
    @classmethod
    async def cmd_consider(cls, player: 'Player', args: List[str]):
        """Consider how tough a mob is."""
        if not args:
            await player.send("Consider whom?")
            return
            
        target_name = ' '.join(args).lower()
        target = None
        
        # Find target in room
        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break
                
        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return
            
        c = player.config.COLORS
        diff = target.level - player.level
        
        if diff <= -10:
            msg = f"{c['bright_cyan']}Now where did that chicken go?{c['reset']}"
        elif diff <= -5:
            msg = f"{c['cyan']}You could kill {target.name} naked and weaponless.{c['reset']}"
        elif diff <= -2:
            msg = f"{c['bright_green']}{target.name} looks like an easy kill.{c['reset']}"
        elif diff <= 1:
            msg = f"{c['green']}A perfect match!{c['reset']}"
        elif diff <= 4:
            msg = f"{c['yellow']}{target.name} says 'Do you feel lucky, punk?'{c['reset']}"
        elif diff <= 8:
            msg = f"{c['bright_red']}{target.name} laughs at your puny weapons.{c['reset']}"
        else:
            msg = f"{c['red']}Death will thank you for your gift.{c['reset']}"
            
        await player.send(msg)
    
    # ==================== COMBAT ====================
    
    @classmethod
    async def cmd_kill(cls, player: 'Player', args: List[str]):
        """Attack a target."""
        if not args:
            await player.send("Kill whom?")
            return
            
        if player.is_fighting:
            await player.send("You're already fighting!")
            return
            
        target_name = ' '.join(args).lower()
        target = None
        
        # Find target in room
        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break
                
        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return
            
        # Check if it's a player
        if hasattr(target, 'connection'):
            await player.send("You can't attack other players here!")
            return
            
        # Check if room is peaceful
        if 'peaceful' in player.room.flags:
            await player.send("A peaceful feeling overwhelms you. You cannot fight here.")
            return
            
        # Start combat
        from combat import CombatHandler
        await CombatHandler.start_combat(player, target)
        
    @classmethod
    async def cmd_attack(cls, player: 'Player', args: List[str]):
        """Alias for kill."""
        await cls.cmd_kill(player, args)
        
    @classmethod
    async def cmd_flee(cls, player: 'Player', args: List[str]):
        """Flee from combat."""
        if not player.is_fighting:
            await player.send("You're not fighting anyone!")
            return
            
        from combat import CombatHandler
        await CombatHandler.attempt_flee(player)
        
    @classmethod
    async def cmd_kick(cls, player: 'Player', args: List[str]):
        """Kick skill."""
        if 'kick' not in player.skills:
            await player.send("You don't know how to kick!")
            return
            
        if not player.is_fighting:
            await player.send("You're not fighting anyone!")
            return
            
        from combat import CombatHandler
        await CombatHandler.do_kick(player)
        
    @classmethod
    async def cmd_bash(cls, player: 'Player', args: List[str]):
        """Bash skill."""
        if 'bash' not in player.skills:
            await player.send("You don't know how to bash!")
            return
            
        if not player.is_fighting:
            await player.send("You're not fighting anyone!")
            return
            
        from combat import CombatHandler
        await CombatHandler.do_bash(player)
        
    @classmethod
    async def cmd_backstab(cls, player: 'Player', args: List[str]):
        """Backstab skill."""
        if 'backstab' not in player.skills:
            await player.send("You don't know how to backstab!")
            return
            
        if player.is_fighting:
            await player.send("You're too busy fighting!")
            return
            
        if not args:
            await player.send("Backstab whom?")
            return
            
        target_name = ' '.join(args).lower()
        target = None
        
        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break
                
        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return
            
        if target.is_fighting:
            await player.send("You can't backstab someone who's fighting!")
            return
            
        from combat import CombatHandler
        await CombatHandler.do_backstab(player, target)

    @classmethod
    async def cmd_envenom(cls, player: 'Player', args: List[str]):
        """Envenom your weapon with deadly poison."""
        if 'envenom' not in player.skills:
            await player.send("You don't know how to envenom weapons!")
            return

        from combat import CombatHandler
        await CombatHandler.do_envenom(player)

    @classmethod
    async def cmd_assassinate(cls, player: 'Player', args: List[str]):
        """Attempt a deadly assassination on an unsuspecting target."""
        if 'assassinate' not in player.skills:
            await player.send("You don't know how to assassinate!")
            return

        if player.is_fighting:
            await player.send("You're too busy fighting!")
            return

        if not args:
            await player.send("Assassinate whom?")
            return

        target_name = ' '.join(args).lower()
        target = None

        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break

        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return

        from combat import CombatHandler
        await CombatHandler.do_assassinate(player, target)

    @classmethod
    async def cmd_garrote(cls, player: 'Player', args: List[str]):
        """Strangle a target from behind, silencing them."""
        if 'garrote' not in player.skills:
            await player.send("You don't know how to garrote!")
            return

        if player.is_fighting:
            await player.send("You're too busy fighting!")
            return

        if not args:
            await player.send("Garrote whom?")
            return

        target_name = ' '.join(args).lower()
        target = None

        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break

        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return

        from combat import CombatHandler
        await CombatHandler.do_garrote(player, target)

    @classmethod
    async def cmd_shadowstep(cls, player: 'Player', args: List[str]):
        """Dissolve into shadows and appear behind a target."""
        if 'shadow_step' not in player.skills:
            await player.send("You don't know how to shadow step!")
            return

        if player.is_fighting:
            await player.send("You're too busy fighting!")
            return

        if not args:
            await player.send("Shadow step to whom?")
            return

        target_name = ' '.join(args).lower()
        target = None

        # Can shadow step to anyone in the room or nearby rooms
        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break

        # Check adjacent rooms if no target in current room
        if not target:
            for direction, exit_info in player.room.exits.items():
                if exit_info and exit_info.get('room'):
                    adj_room = exit_info['room']
                    for char in adj_room.characters:
                        if target_name in char.name.lower():
                            target = char
                            break
                    if target:
                        break

        if not target:
            await player.send(f"You don't sense '{target_name}' nearby.")
            return

        from combat import CombatHandler
        await CombatHandler.do_shadow_step(player, target)

    @classmethod
    async def cmd_mark(cls, player: 'Player', args: List[str]):
        """Mark a target for death, increasing damage against them."""
        if 'mark_target' not in player.skills:
            await player.send("You don't know how to mark targets!")
            return

        if not args:
            await player.send("Mark whom for death?")
            return

        target_name = ' '.join(args).lower()
        target = None

        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break

        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return

        from combat import CombatHandler
        await CombatHandler.do_mark_target(player, target)

    # ==================== MAGIC ====================
    
    @classmethod
    async def cmd_cast(cls, player: 'Player', args: List[str]):
        """Cast a spell."""
        if not args:
            await player.send("Cast what spell?")
            return
            
        # Parse spell name and target
        spell_name = args[0].lower().replace('_', ' ')
        target_name = ' '.join(args[1:]) if len(args) > 1 else None
        
        # Find matching spell
        matching_spell = None
        for spell in player.spells:
            if spell.replace('_', ' ').startswith(spell_name):
                matching_spell = spell
                break
                
        if not matching_spell:
            await player.send(f"You don't know the spell '{spell_name}'!")
            return
            
        from spells import SpellHandler
        await SpellHandler.cast_spell(player, matching_spell, target_name)
        
    @classmethod
    async def cmd_spells(cls, player: 'Player', args: List[str]):
        """Show known spells."""
        c = player.config.COLORS
        
        if not player.spells:
            await player.send("You don't know any spells.")
            return
            
        await player.send(f"{c['cyan']}╔═══════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']}        Your Known Spells              {c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠═══════════════════════════════════════╣{c['reset']}")
        
        for spell, proficiency in player.spells.items():
            spell_name = spell.replace('_', ' ').title()
            from spells import SPELLS
            spell_info = SPELLS.get(spell, {})
            mana_cost = spell_info.get('mana_cost', 10)
            await player.send(f"{c['cyan']}║ {c['bright_magenta']}{spell_name:<20} {c['white']}Mana: {mana_cost:<3} {proficiency}%{c['cyan']}  ║{c['reset']}")
            
        await player.send(f"{c['cyan']}╚═══════════════════════════════════════╝{c['reset']}")
        
    @classmethod
    async def cmd_skills(cls, player: 'Player', args: List[str]):
        """Show known skills."""
        c = player.config.COLORS
        
        if not player.skills:
            await player.send("You don't know any skills.")
            return
            
        await player.send(f"{c['cyan']}╔═══════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']}        Your Known Skills              {c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠═══════════════════════════════════════╣{c['reset']}")
        
        for skill, proficiency in player.skills.items():
            skill_name = skill.replace('_', ' ').title()
            await player.send(f"{c['cyan']}║ {c['bright_green']}{skill_name:<25} {c['white']}{proficiency}%{c['cyan']}       ║{c['reset']}")
            
        await player.send(f"{c['cyan']}╚═══════════════════════════════════════╝{c['reset']}")
        
    @classmethod
    async def cmd_practice(cls, player: 'Player', args: List[str]):
        """Practice skills/spells."""
        c = player.config.COLORS
        
        if not args:
            # Show what can be practiced
            await player.send(f"{c['cyan']}You have {player.practices} practice sessions.{c['reset']}")
            await player.send(f"{c['cyan']}Skills:{c['reset']}")
            for skill, prof in player.skills.items():
                await player.send(f"  {skill.replace('_', ' ').title()}: {prof}%")
            await player.send(f"{c['cyan']}Spells:{c['reset']}")
            for spell, prof in player.spells.items():
                await player.send(f"  {spell.replace('_', ' ').title()}: {prof}%")
            return
            
        if player.practices <= 0:
            await player.send("You have no practice sessions left!")
            return
            
        target = args[0].lower().replace(' ', '_')
        
        # Check skills
        if target in player.skills:
            if player.skills[target] >= 85:
                await player.send("You've already mastered that skill!")
                return
            player.skills[target] = min(85, player.skills[target] + 10)
            player.practices -= 1
            await player.send(f"You practice {target.replace('_', ' ')}. ({player.skills[target]}%)")
            return
            
        # Check spells
        if target in player.spells:
            if player.spells[target] >= 85:
                await player.send("You've already mastered that spell!")
                return
            player.spells[target] = min(85, player.spells[target] + 10)
            player.practices -= 1
            await player.send(f"You practice {target.replace('_', ' ')}. ({player.spells[target]}%)")
            return
            
        await player.send(f"You don't know '{target}'!")
    
    # ==================== ITEMS ====================
    
    @classmethod
    async def cmd_get(cls, player: 'Player', args: List[str]):
        """Pick up an item."""
        if not args:
            await player.send("Get what?")
            return
            
        item_name = ' '.join(args).lower()

        # Check if getting from container
        if 'from' in args:
            from_idx = args.index('from')
            item_name = ' '.join(args[:from_idx]).lower()
            container_name = ' '.join(args[from_idx+1:]).lower()

            # Find container in inventory or room
            container = None
            for item in player.inventory + player.room.items:
                if container_name in item.name.lower():
                    if hasattr(item, 'item_type') and item.item_type == 'container':
                        container = item
                        break

            if not container:
                await player.send(f"You don't see a '{container_name}' container here.")
                return

            # Check if container is closed
            if hasattr(container, 'is_closed') and container.is_closed:
                await player.send(f"The {container.name} is closed.")
                return

            # Check if getting 'all' from container
            if item_name == 'all':
                if not hasattr(container, 'contents') or not container.contents:
                    await player.send(f"The {container.name} is empty.")
                    return
                for item in list(container.contents):
                    container.contents.remove(item)
                    player.inventory.append(item)
                    await player.send(f"You get {item.short_desc} from {container.short_desc}.")
                return

            # Get specific item from container
            if not hasattr(container, 'contents'):
                await player.send(f"The {container.name} is empty.")
                return

            for item in container.contents:
                if item_name in item.name.lower():
                    container.contents.remove(item)
                    player.inventory.append(item)
                    await player.send(f"You get {item.short_desc} from {container.short_desc}.")
                    await player.room.send_to_room(
                        f"{player.name} gets {item.short_desc} from {container.short_desc}.",
                        exclude=[player]
                    )
                    return

            await player.send(f"There's no '{item_name}' in {container.short_desc}.")
            return
            
        # Check if getting 'all'
        if item_name == 'all':
            if not player.room.items:
                await player.send("There's nothing here to get.")
                return
            for item in list(player.room.items):
                player.room.items.remove(item)
                player.inventory.append(item)
                await player.send(f"You get {item.short_desc}.")
            return
            
        # Find item in room
        for item in player.room.items:
            if item_name in item.name.lower():
                player.room.items.remove(item)
                player.inventory.append(item)
                await player.send(f"You get {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} picks up {item.short_desc}.",
                    exclude=[player]
                )
                return
                
        await player.send(f"You don't see '{item_name}' here.")
        
    @classmethod
    async def cmd_take(cls, player: 'Player', args: List[str]):
        """Alias for get."""
        await cls.cmd_get(player, args)
        
    @classmethod
    async def cmd_drop(cls, player: 'Player', args: List[str]):
        """Drop an item."""
        if not args:
            await player.send("Drop what?")
            return
            
        item_name = ' '.join(args).lower()
        
        # Check if dropping 'all'
        if item_name == 'all':
            if not player.inventory:
                await player.send("You're not carrying anything.")
                return
            for item in list(player.inventory):
                player.inventory.remove(item)
                player.room.items.append(item)
                await player.send(f"You drop {item.short_desc}.")
            return
            
        # Find item in inventory
        for item in player.inventory:
            if item_name in item.name.lower():
                player.inventory.remove(item)
                player.room.items.append(item)
                await player.send(f"You drop {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} drops {item.short_desc}.",
                    exclude=[player]
                )
                return
                
        await player.send(f"You don't have '{item_name}'.")

    @classmethod
    async def cmd_put(cls, player: 'Player', args: List[str]):
        """Put an item into a container. Usage: put <item> <container> or put all <container>"""
        if not args or len(args) < 2:
            await player.send("Usage: put <item> <container> or put all <container>")
            return

        c = player.config.COLORS

        # Check for 'in' or 'into' preposition
        if 'in' in args:
            in_idx = args.index('in')
            item_name = ' '.join(args[:in_idx]).lower()
            container_name = ' '.join(args[in_idx+1:]).lower()
        elif 'into' in args:
            into_idx = args.index('into')
            item_name = ' '.join(args[:into_idx]).lower()
            container_name = ' '.join(args[into_idx+1:]).lower()
        else:
            # Assume last word is container
            container_name = args[-1].lower()
            item_name = ' '.join(args[:-1]).lower()

        # Find container in inventory or room
        container = None
        for item in player.inventory + player.room.items:
            if container_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if not container:
            await player.send(f"{c['red']}You don't see a '{container_name}' container here.{c['reset']}")
            return

        # Check if container is closed
        if hasattr(container, 'is_closed') and container.is_closed:
            await player.send(f"{c['red']}The {container.name} is closed.{c['reset']}")
            return

        # Initialize contents if not present
        if not hasattr(container, 'contents'):
            container.contents = []

        # Check for 'all'
        if item_name == 'all':
            if not player.inventory:
                await player.send(f"{c['yellow']}You're not carrying anything.{c['reset']}")
                return

            put_count = 0
            for item in list(player.inventory):
                # Don't put container into itself
                if item == container:
                    continue

                # Check weight capacity if container has it
                if hasattr(container, 'capacity'):
                    current_weight = sum(getattr(i, 'weight', 1) for i in container.contents)
                    item_weight = getattr(item, 'weight', 1)
                    if current_weight + item_weight > container.capacity:
                        await player.send(f"{c['yellow']}{container.short_desc} is full.{c['reset']}")
                        break

                player.inventory.remove(item)
                container.contents.append(item)
                await player.send(f"You put {item.short_desc} in {container.short_desc}.")
                put_count += 1

            if put_count > 0:
                await player.room.send_to_room(
                    f"{player.name} puts several items in {container.short_desc}.",
                    exclude=[player]
                )
            return

        # Put specific item
        for item in player.inventory:
            if item_name in item.name.lower():
                # Don't put container into itself
                if item == container:
                    await player.send(f"{c['red']}You can't put {item.short_desc} into itself!{c['reset']}")
                    return

                # Check weight capacity
                if hasattr(container, 'capacity'):
                    current_weight = sum(getattr(i, 'weight', 1) for i in container.contents)
                    item_weight = getattr(item, 'weight', 1)
                    if current_weight + item_weight > container.capacity:
                        await player.send(f"{c['red']}{container.short_desc} is full.{c['reset']}")
                        return

                player.inventory.remove(item)
                container.contents.append(item)
                await player.send(f"{c['green']}You put {item.short_desc} in {container.short_desc}.{c['reset']}")
                await player.room.send_to_room(
                    f"{player.name} puts {item.short_desc} in {container.short_desc}.",
                    exclude=[player]
                )
                return

        await player.send(f"{c['red']}You don't have '{item_name}'.{c['reset']}")

    @classmethod
    async def cmd_wear(cls, player: 'Player', args: List[str]):
        """Wear an item."""
        if not args:
            await player.send("Wear what?")
            return
            
        item_name = ' '.join(args).lower()
        
        # Find item in inventory
        for item in player.inventory:
            if item_name in item.name.lower():
                if item.item_type not in ('armor', 'light', 'worn'):
                    await player.send(f"You can't wear {item.short_desc}.")
                    return
                    
                slot = getattr(item, 'wear_slot', None)
                if not slot:
                    await player.send(f"You can't figure out how to wear {item.short_desc}.")
                    return
                    
                # Check if slot is occupied
                if player.equipment.get(slot):
                    await player.send(f"You're already wearing something there.")
                    return
                    
                player.inventory.remove(item)
                player.equipment[slot] = item
                await player.send(f"You wear {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} wears {item.short_desc}.",
                    exclude=[player]
                )
                return
                
        await player.send(f"You don't have '{item_name}'.")
        
    @classmethod
    async def cmd_wield(cls, player: 'Player', args: List[str]):
        """Wield a weapon."""
        if not args:
            await player.send("Wield what?")
            return
            
        item_name = ' '.join(args).lower()
        
        # Find item in inventory
        for item in player.inventory:
            if item_name in item.name.lower():
                if item.item_type != 'weapon':
                    await player.send(f"You can't wield {item.short_desc}.")
                    return
                    
                # Check if already wielding
                if player.equipment.get('wield'):
                    await player.send("You're already wielding something.")
                    return
                    
                player.inventory.remove(item)
                player.equipment['wield'] = item
                await player.send(f"You wield {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} wields {item.short_desc}.",
                    exclude=[player]
                )
                return
                
        await player.send(f"You don't have '{item_name}'.")
        
    @classmethod
    async def cmd_remove(cls, player: 'Player', args: List[str]):
        """Remove worn equipment."""
        if not args:
            await player.send("Remove what?")
            return
            
        item_name = ' '.join(args).lower()
        
        # Find item in equipment
        for slot, item in list(player.equipment.items()):
            if item and item_name in item.name.lower():
                player.equipment[slot] = None
                player.inventory.append(item)
                await player.send(f"You remove {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} removes {item.short_desc}.",
                    exclude=[player]
                )
                return
                
        await player.send(f"You're not wearing '{item_name}'.")
        
    @classmethod
    async def cmd_give(cls, player: 'Player', args: List[str]):
        """Give an item to someone."""
        if len(args) < 2:
            await player.send("Give what to whom?")
            return
            
        item_name = args[0].lower()
        target_name = args[-1].lower()
        
        # Find target
        target = None
        for char in player.room.characters:
            if char != player and target_name in char.name.lower():
                target = char
                break
                
        if not target:
            await player.send(f"You don't see '{target_name}' here.")
            return
            
        # Find item
        for item in player.inventory:
            if item_name in item.name.lower():
                player.inventory.remove(item)
                if hasattr(target, 'inventory'):
                    target.inventory.append(item)
                await player.send(f"You give {item.short_desc} to {target.name}.")
                if hasattr(target, 'send'):
                    await target.send(f"{player.name} gives you {item.short_desc}.")
                await player.room.send_to_room(
                    f"{player.name} gives {item.short_desc} to {target.name}.",
                    exclude=[player, target]
                )
                return
                
        await player.send(f"You don't have '{item_name}'.")
    
    # ==================== COMMUNICATION ====================

    @classmethod
    async def handle_npc_trigger(cls, player: 'Player', npc: 'Mobile', message: str):
        """Handle NPC responses to player speech."""
        c = player.config.COLORS

        # Healer NPCs
        if npc.special == 'healer':
            if 'heal' in message or 'help' in message:
                # Check if player needs healing
                if player.hp < player.max_hp:
                    heal_amount = player.max_hp - player.hp
                    player.hp = player.max_hp
                    await player.send(f"{c['bright_cyan']}{npc.name} says, 'Let me tend to your wounds.'{c['reset']}")
                    await player.room.send_to_room(
                        f"{npc.name} places their hands on {player.name} and heals them.",
                        exclude=[player]
                    )
                    await player.send(f"{c['bright_green']}You are fully healed! [{heal_amount} HP]{c['reset']}")
                else:
                    await player.send(f"{c['bright_cyan']}{npc.name} says, 'You appear to be in perfect health already.'{c['reset']}")

        # Shopkeeper NPCs
        elif npc.special == 'shopkeeper':
            if 'hello' in message or 'hi' in message or 'greet' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'Welcome! Type LIST to see my wares.'{c['reset']}")
            elif 'buy' in message or 'sell' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'Use BUY <item> to purchase or SELL <item> to sell to me.'{c['reset']}")

        # Trainer NPCs
        elif npc.special == 'trainer':
            if 'train' in message or 'teach' in message or 'practice' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'I can train you in the arts of thievery. Type PRACTICE to see what I offer.'{c['reset']}")
            elif 'hello' in message or 'hi' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'Welcome to the guild, shadow walker.'{c['reset']}")

        # Generic helper NPCs
        elif 'helper' in npc.flags:
            if 'hello' in message or 'hi' in message or 'greet' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} nods at you in acknowledgment.{c['reset']}")
            elif 'help' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'I'm here to keep the peace. Stay out of trouble!'{c['reset']}")

    @classmethod
    async def cmd_say(cls, player: 'Player', args: List[str]):
        """Say something to the room."""
        if not args:
            await player.send("Say what?")
            return

        message = ' '.join(args)
        c = player.config.COLORS

        await player.send(f"{c['bright_green']}You say, '{message}'{c['reset']}")
        await player.room.send_to_room(
            f"{c['bright_green']}{player.name} says, '{message}'{c['reset']}",
            exclude=[player]
        )

        # Check for NPC triggers
        from mobs import Mobile
        for char in player.room.characters:
            if isinstance(char, Mobile) and char.special:
                await cls.handle_npc_trigger(player, char, message.lower())
        
    @classmethod
    async def cmd_shout(cls, player: 'Player', args: List[str]):
        """Shout to everyone in the zone."""
        if not args:
            await player.send("Shout what?")
            return
            
        message = ' '.join(args)
        c = player.config.COLORS
        
        await player.send(f"{c['bright_yellow']}You shout, '{message}'{c['reset']}")
        
        # Send to all players in the zone
        for p in player.world.players.values():
            if p != player and p.room and player.room and p.room.zone == player.room.zone:
                await p.send(f"\r\n{c['bright_yellow']}{player.name} shouts, '{message}'{c['reset']}")
                
    @classmethod
    async def cmd_gossip(cls, player: 'Player', args: List[str]):
        """Gossip to all players."""
        if not args:
            await player.send("Gossip what?")
            return
            
        message = ' '.join(args)
        c = player.config.COLORS
        
        await player.send(f"{c['bright_magenta']}You gossip, '{message}'{c['reset']}")
        
        for p in player.world.players.values():
            if p != player:
                await p.send(f"\r\n{c['bright_magenta']}{player.name} gossips, '{message}'{c['reset']}")
                
    @classmethod
    async def cmd_emote(cls, player: 'Player', args: List[str]):
        """Emote an action."""
        if not args:
            await player.send("Emote what?")
            return
            
        message = ' '.join(args)
        c = player.config.COLORS
        
        await player.room.send_to_room(f"{c['yellow']}{player.name} {message}{c['reset']}")
        
    @classmethod
    async def cmd_tell(cls, player: 'Player', args: List[str]):
        """Send a private message."""
        if len(args) < 2:
            await player.send("Tell whom what?")
            return
            
        target_name = args[0].lower()
        message = ' '.join(args[1:])
        c = player.config.COLORS
        
        target = player.world.get_player(target_name)
        if not target:
            await player.send(f"No player named '{target_name}' is online.")
            return
            
        await player.send(f"{c['bright_cyan']}You tell {target.name}, '{message}'{c['reset']}")
        await target.send(f"\r\n{c['bright_cyan']}{player.name} tells you, '{message}'{c['reset']}")
    
    # ==================== POSITIONS ====================
    
    @classmethod
    async def cmd_sit(cls, player: 'Player', args: List[str]):
        """Sit down."""
        if player.is_fighting:
            await player.send("You can't sit while fighting!")
            return
        if player.position == 'sitting':
            await player.send("You're already sitting.")
            return
        player.position = 'sitting'
        await player.send("You sit down.")
        await player.room.send_to_room(f"{player.name} sits down.", exclude=[player])
        
    @classmethod
    async def cmd_rest(cls, player: 'Player', args: List[str]):
        """Rest to regenerate faster."""
        if player.is_fighting:
            await player.send("You can't rest while fighting!")
            return
        if player.position == 'resting':
            await player.send("You're already resting.")
            return
        player.position = 'resting'
        await player.send("You rest and begin to recuperate.")
        await player.room.send_to_room(f"{player.name} rests.", exclude=[player])
        
    @classmethod
    async def cmd_sleep(cls, player: 'Player', args: List[str]):
        """Go to sleep."""
        if player.is_fighting:
            await player.send("You can't sleep while fighting!")
            return
        if player.position == 'sleeping':
            await player.send("You're already asleep.")
            return
        player.position = 'sleeping'
        await player.send("You go to sleep.")
        await player.room.send_to_room(f"{player.name} goes to sleep.", exclude=[player])
        
    @classmethod
    async def cmd_wake(cls, player: 'Player', args: List[str]):
        """Wake up."""
        if player.position != 'sleeping':
            await player.send("You're not sleeping!")
            return
        player.position = 'standing'
        await player.send("You wake and stand up.")
        await player.room.send_to_room(f"{player.name} wakes up.", exclude=[player])
        
    @classmethod
    async def cmd_stand(cls, player: 'Player', args: List[str]):
        """Stand up."""
        if player.position == 'standing':
            await player.send("You're already standing.")
            return
        if player.position == 'sleeping':
            await player.send("You wake and stand up.")
        else:
            await player.send("You stand up.")
        player.position = 'standing'
        await player.room.send_to_room(f"{player.name} stands up.", exclude=[player])
    
    # ==================== CONSUMABLES ====================
    
    @classmethod
    async def cmd_eat(cls, player: 'Player', args: List[str]):
        """Eat food."""
        if not args:
            await player.send("Eat what?")
            return
            
        item_name = ' '.join(args).lower()
        
        for item in player.inventory:
            if item_name in item.name.lower():
                if item.item_type != 'food':
                    await player.send(f"You can't eat {item.short_desc}!")
                    return
                    
                player.inventory.remove(item)
                food_value = getattr(item, 'food_value', 10)
                await player.send(f"You eat {item.short_desc}.")
                
                # Could implement hunger system here
                # For now, just consume the item
                return
                
        await player.send(f"You don't have '{item_name}'.")
        
    @classmethod
    async def cmd_drink(cls, player: 'Player', args: List[str]):
        """Drink from a container or fountain."""
        if not args:
            await player.send("Drink what?")
            return
            
        item_name = ' '.join(args).lower()
        
        for item in player.inventory:
            if item_name in item.name.lower():
                if item.item_type != 'drink':
                    await player.send(f"You can't drink from {item.short_desc}!")
                    return
                    
                await player.send(f"You drink from {item.short_desc}.")
                return
                
        await player.send(f"You don't have '{item_name}'.")
        
    @classmethod
    async def cmd_quaff(cls, player: 'Player', args: List[str]):
        """Drink a potion."""
        if not args:
            await player.send("Quaff what?")
            return
            
        item_name = ' '.join(args).lower()
        
        for item in player.inventory:
            if item_name in item.name.lower():
                if item.item_type != 'potion':
                    await player.send(f"You can't quaff {item.short_desc}!")
                    return
                    
                player.inventory.remove(item)
                await player.send(f"You quaff {item.short_desc}.")
                
                # Apply potion effects
                if hasattr(item, 'spell_effects'):
                    from spells import SpellHandler
                    for spell in item.spell_effects:
                        await SpellHandler.apply_spell_effect(player, player, spell)
                return
                
        await player.send(f"You don't have '{item_name}'.")

    @classmethod
    async def cmd_quest(cls, player: 'Player', args: List[str]):
        """Manage quests."""
        from quests import QuestManager
        from datetime import datetime

        c = player.config.COLORS

        if not args:
            # Show active quests
            if not hasattr(player, 'active_quests') or not player.active_quests:
                await player.send(f"{c['yellow']}You have no active quests.{c['reset']}")
                await player.send(f"{c['white']}Talk to NPCs to find available quests!{c['reset']}")
                return

            await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
            await player.send(f"{c['cyan']}║{c['bright_yellow']} Active Quests{c['cyan']}                                                  ║{c['reset']}")
            await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

            for quest in player.active_quests:
                complete_str = f"{c['bright_green']}COMPLETE{c['reset']}" if quest.is_complete() else f"{c['yellow']}In Progress{c['reset']}"
                await player.send(f"{c['bright_cyan']}{quest.name}{c['reset']} [{complete_str}]")
                await player.send(f"{c['white']}{quest.description}{c['reset']}")
                await player.send(quest.get_progress_string())

                if quest.is_complete():
                    await player.send(f"{c['bright_green']}✓ Return to quest giver to complete!{c['reset']}")

                if quest.time_limit:
                    elapsed = (datetime.now() - quest.started_at).total_seconds() / 60
                    remaining = quest.time_limit - elapsed
                    if remaining > 0:
                        await player.send(f"{c['yellow']}Time remaining: {int(remaining)} minutes{c['reset']}")
                    else:
                        await player.send(f"{c['red']}TIME EXPIRED!{c['reset']}")

                await player.send("")  # Blank line between quests

            return

        subcommand = args[0].lower()

        if subcommand == 'accept':
            if len(args) < 2:
                await player.send("Usage: quest accept <quest_id>")
                return
            await QuestManager.accept_quest(player, args[1])

        elif subcommand == 'abandon':
            if len(args) < 2:
                await player.send("Usage: quest abandon <quest_id>")
                return
            await QuestManager.abandon_quest(player, args[1])

        elif subcommand == 'complete':
            if len(args) < 2:
                await player.send("Usage: quest complete <quest_id>")
                return
            await QuestManager.complete_quest(player, args[1])

        elif subcommand == 'log':
            # Show completed quests
            if not hasattr(player, 'quests_completed') or not player.quests_completed:
                await player.send(f"{c['yellow']}You haven't completed any quests yet.{c['reset']}")
                return

            await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
            await player.send(f"{c['cyan']}║{c['bright_yellow']} Completed Quests{c['cyan']}                                             ║{c['reset']}")
            await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

            for quest_id in player.quests_completed:
                await player.send(f"{c['bright_green']}✓{c['reset']} {quest_id}")

            await player.send(f"\r\n{c['white']}Total: {len(player.quests_completed)} quests completed{c['reset']}\r\n")

        else:
            await player.send(f"Unknown quest command: {subcommand}")
            await player.send("Usage: quest [accept|abandon|complete|log]")

    @classmethod
    async def cmd_questlog(cls, player: 'Player', args: List[str]):
        """Show quest log (alias for quest log)."""
        await cls.cmd_quest(player, ['log'])

    # ==================== PET/COMPANION COMMANDS ====================

    @classmethod
    async def cmd_order(cls, player: 'Player', args: List[str]):
        """Order your pet to do something. Usage: order <command> [target]"""
        from pets import PetManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Usage: order <command> [target]{c['reset']}")
            await player.send(f"Commands: attack, follow, stay, guard, fetch")
            return

        # Get player's pets
        pets = PetManager.get_player_pets(player)
        if not pets:
            await player.send(f"{c['red']}You don't have any pets to command!{c['reset']}")
            return

        command = args[0].lower()
        target = ' '.join(args[1:]) if len(args) > 1 else ''

        # Order all pets
        for pet in pets:
            if pet.room == player.room:
                await pet.execute_command(command, target)

    @classmethod
    async def cmd_dismiss(cls, player: 'Player', args: List[str]):
        """Dismiss your summoned pet. Usage: dismiss"""
        from pets import PetManager, Pet

        c = player.config.COLORS

        # Get player's pets
        pets = PetManager.get_player_pets(player)
        if not pets:
            await player.send(f"{c['red']}You don't have any pets to dismiss!{c['reset']}")
            return

        # Dismiss temporary pets (summons/undead)
        dismissed = False
        for pet in pets:
            if not pet.is_persistent:
                await PetManager.dismiss_pet(pet)
                await player.send(f"{c['green']}You dismiss {pet.name}.{c['reset']}")
                dismissed = True

        if not dismissed:
            await player.send(f"{c['yellow']}You don't have any temporary pets to dismiss.{c['reset']}")
            await player.send(f"(Permanent companions cannot be dismissed)")

    @classmethod
    async def cmd_tame(cls, player: 'Player', args: List[str]):
        """Tame a wild creature. Usage: tame <creature>"""
        from pets import PetManager

        c = player.config.COLORS

        # Check if ranger
        if player.char_class != 'ranger':
            await player.send(f"{c['red']}Only Rangers can tame creatures!{c['reset']}")
            return

        if not args:
            await player.send(f"{c['yellow']}Usage: tame <creature>{c['reset']}")
            return

        target_name = ' '.join(args).lower()

        # Find creature in room
        target = None
        for char in player.room.characters:
            if char != player and hasattr(char, 'name'):
                if char.name.lower().startswith(target_name):
                    target = char
                    break

        if not target:
            await player.send(f"{c['red']}There's no '{target_name}' here to tame.{c['reset']}")
            return

        # Can't tame players or existing pets
        if hasattr(target, 'connection'):
            await player.send(f"{c['red']}You can't tame a player!{c['reset']}")
            return

        if hasattr(target, 'owner'):
            await player.send(f"{c['red']}That creature is already tamed!{c['reset']}")
            return

        # Attempt to tame
        success = await PetManager.tame_companion(player, target)
        if success:
            await player.send(f"{c['bright_green']}You successfully tame {target.name}!{c['reset']}")

    @classmethod
    async def cmd_summon(cls, player: 'Player', args: List[str]):
        """Summon an elemental. Usage: summon <air|fire|water|earth>"""
        from pets import PetManager

        c = player.config.COLORS

        # Check if mage
        if player.char_class != 'mage':
            await player.send(f"{c['red']}Only Mages can summon elementals!{c['reset']}")
            return

        if not args:
            await player.send(f"{c['yellow']}Usage: summon <air|fire|water|earth>{c['reset']}")
            await player.send(f"Elementals: air, fire, water, earth")
            return

        element = args[0].lower()
        valid_elements = ['air', 'fire', 'water', 'earth']

        if element not in valid_elements:
            await player.send(f"{c['red']}Invalid elemental type. Choose: air, fire, water, earth{c['reset']}")
            return

        # Check mana cost
        mana_cost = 50
        if player.mana < mana_cost:
            await player.send(f"{c['red']}You don't have enough mana! (Need {mana_cost}){c['reset']}")
            return

        # Check level requirement
        if player.level < 5:
            await player.send(f"{c['red']}You must be at least level 5 to summon elementals!{c['reset']}")
            return

        # Summon elemental
        template_name = f"{element}_elemental"
        pet = await PetManager.summon_pet(player, template_name, duration_minutes=30)

        if pet:
            player.mana -= mana_cost
            await player.send(f"{c['bright_magenta']}You summon {pet.short_desc}!{c['reset']}")
            await player.send(f"{c['yellow']}Duration: 30 minutes{c['reset']}")

    @classmethod
    async def cmd_animate(cls, player: 'Player', args: List[str]):
        """Animate a corpse as undead. Usage: animate <corpse>"""
        from pets import PetManager

        c = player.config.COLORS

        # Check if necromancer/cleric with evil alignment
        if player.char_class not in ('cleric',) or player.alignment > -200:
            await player.send(f"{c['red']}Only evil Clerics can animate the dead!{c['reset']}")
            return

        # Look for corpse in room
        corpse = None
        for item in player.room.items:
            if hasattr(item, 'item_type') and item.item_type == 'container':
                if 'corpse' in item.name.lower():
                    corpse = item
                    break

        if not corpse:
            await player.send(f"{c['red']}There's no corpse here to animate!{c['reset']}")
            return

        # Check mana cost
        mana_cost = 60
        if player.mana < mana_cost:
            await player.send(f"{c['red']}You don't have enough mana! (Need {mana_cost}){c['reset']}")
            return

        # Check level requirement
        if player.level < 8:
            await player.send(f"{c['red']}You must be at least level 8 to animate the dead!{c['reset']}")
            return

        # Determine type of undead based on level
        if player.level >= 20:
            undead_type = 'wight'
            duration = 30
        elif player.level >= 15:
            undead_type = 'ghoul'
            duration = 45
        elif player.level >= 10:
            undead_type = 'skeleton'
            duration = 60
        else:
            undead_type = 'zombie'
            duration = 60

        # Summon undead
        pet = await PetManager.summon_pet(player, undead_type, duration_minutes=duration)

        if pet:
            player.mana -= mana_cost
            # Remove corpse
            player.room.items.remove(corpse)

            await player.send(f"{c['bright_magenta']}You animate {corpse.name} as {pet.short_desc}!{c['reset']}")
            await player.send(f"{c['yellow']}Duration: {duration} minutes{c['reset']}")

    @classmethod
    async def cmd_companion(cls, player: 'Player', args: List[str]):
        """Show your companion's stats. Usage: companion"""
        from pets import PetManager

        c = player.config.COLORS

        pets = PetManager.get_player_pets(player)

        if not pets:
            await player.send(f"{c['yellow']}You don't have any companions.{c['reset']}")
            return

        await player.send(f"{c['bright_cyan']}╔══════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}                  Your Companions                     {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════╝{c['reset']}")

        for pet in pets:
            hp_bar = cls._make_bar(pet.hp, pet.max_hp, 20)
            loyalty_bar = cls._make_bar(pet.loyalty, 100, 20)

            pet_type = "PERMANENT" if pet.is_persistent else "TEMPORARY"
            time_remaining = ""
            if pet.timer:
                remaining = pet.get_despawn_time()
                if remaining:
                    minutes = remaining // 60
                    seconds = remaining % 60
                    time_remaining = f" (Time left: {minutes}m {seconds}s)"

            await player.send(f"\n{c['bright_white']}{pet.name} [{pet_type}]{c['reset']}{time_remaining}")
            await player.send(f"  Level: {pet.level}  Type: {pet.pet_type}")
            await player.send(f"  HP:      {hp_bar} {pet.hp}/{pet.max_hp}")
            await player.send(f"  Loyalty: {loyalty_bar} {pet.loyalty}/100")

            if pet.room == player.room:
                await player.send(f"  Location: {c['green']}Here{c['reset']}")
            elif pet.room:
                await player.send(f"  Location: {c['yellow']}{pet.room.name}{c['reset']}")
            else:
                await player.send(f"  Location: {c['red']}Unknown{c['reset']}")

    @staticmethod
    def _make_bar(current: int, maximum: int, width: int = 20) -> str:
        """Create a visual bar for stats."""
        if maximum == 0:
            filled = 0
        else:
            filled = int((current / maximum) * width)

        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"

    # ==================== DOOR COMMANDS ====================

    @classmethod
    async def cmd_open(cls, player: 'Player', args: List[str]):
        """Open a door or container. Usage: open <door/container>"""
        if not args:
            await player.send("Open what?")
            return

        c = player.config.COLORS
        target_name = ' '.join(args).lower()

        # Check for container first
        container = None
        for item in player.inventory + player.room.items:
            if target_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if container:
            if not hasattr(container, 'is_closed'):
                await player.send(f"{c['yellow']}The {container.name} doesn't open and close.{c['reset']}")
                return

            if not container.is_closed:
                await player.send(f"{c['yellow']}The {container.name} is already open.{c['reset']}")
                return

            # Check if locked
            if hasattr(container, 'is_locked') and container.is_locked:
                await player.send(f"{c['red']}The {container.name} is locked.{c['reset']}")
                return

            container.is_closed = False
            await player.send(f"{c['green']}You open {container.short_desc}.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} opens {container.short_desc}.",
                exclude=[player]
            )
            return

        # Check for door
        direction = None
        for dir_name in player.config.DIRECTIONS.keys():
            if target_name in dir_name or target_name == dir_name:
                direction = dir_name
                break

        if not direction:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        if direction not in player.room.exits or not player.room.exits[direction]:
            await player.send(f"{c['red']}There's no exit {direction}.{c['reset']}")
            return

        exit_data = player.room.exits[direction]

        if 'door' not in exit_data:
            await player.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
            return

        door = exit_data['door']

        if door.get('state') != 'closed':
            await player.send(f"{c['yellow']}The door is already open.{c['reset']}")
            return

        # Check if locked
        if door.get('locked', False):
            await player.send(f"{c['red']}The door is locked.{c['reset']}")
            return

        # Check if magically blocked
        if door.get('magically_blocked', False):
            await player.send(f"{c['red']}The door is magically sealed!{c['reset']}")
            return

        door['state'] = 'open'
        await player.send(f"{c['green']}You open the {door.get('name', 'door')} {direction}.{c['reset']}")
        await player.room.send_to_room(
            f"{player.name} opens the {door.get('name', 'door')} {direction}.",
            exclude=[player]
        )

    @classmethod
    async def cmd_close(cls, player: 'Player', args: List[str]):
        """Close a door or container. Usage: close <door/container>"""
        if not args:
            await player.send("Close what?")
            return

        c = player.config.COLORS
        target_name = ' '.join(args).lower()

        # Check for container first
        container = None
        for item in player.inventory + player.room.items:
            if target_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if container:
            if not hasattr(container, 'is_closed'):
                await player.send(f"{c['yellow']}The {container.name} doesn't open and close.{c['reset']}")
                return

            if container.is_closed:
                await player.send(f"{c['yellow']}The {container.name} is already closed.{c['reset']}")
                return

            container.is_closed = True
            await player.send(f"{c['green']}You close {container.short_desc}.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} closes {container.short_desc}.",
                exclude=[player]
            )
            return

        # Check for door
        direction = None
        for dir_name in player.config.DIRECTIONS.keys():
            if target_name in dir_name or target_name == dir_name:
                direction = dir_name
                break

        if not direction:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        if direction not in player.room.exits or not player.room.exits[direction]:
            await player.send(f"{c['red']}There's no exit {direction}.{c['reset']}")
            return

        exit_data = player.room.exits[direction]

        if 'door' not in exit_data:
            await player.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
            return

        door = exit_data['door']

        # Check if broken
        if door.get('broken', False):
            await player.send(f"{c['red']}The door is broken and cannot be closed!{c['reset']}")
            return

        if door.get('state') == 'closed':
            await player.send(f"{c['yellow']}The door is already closed.{c['reset']}")
            return

        door['state'] = 'closed'
        await player.send(f"{c['green']}You close the {door.get('name', 'door')} {direction}.{c['reset']}")
        await player.room.send_to_room(
            f"{player.name} closes the {door.get('name', 'door')} {direction}.",
            exclude=[player]
        )

    @classmethod
    async def cmd_lock(cls, player: 'Player', args: List[str]):
        """Lock a door or container. Usage: lock <door/container>"""
        if not args:
            await player.send("Lock what?")
            return

        c = player.config.COLORS
        target_name = ' '.join(args).lower()

        # Check for container first
        container = None
        for item in player.inventory + player.room.items:
            if target_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if container:
            if not hasattr(container, 'is_locked'):
                await player.send(f"{c['yellow']}The {container.name} cannot be locked.{c['reset']}")
                return

            if container.is_locked:
                await player.send(f"{c['yellow']}The {container.name} is already locked.{c['reset']}")
                return

            # Check if closed
            if hasattr(container, 'is_closed') and not container.is_closed:
                await player.send(f"{c['red']}You must close it first.{c['reset']}")
                return

            # Check for key
            key_vnum = getattr(container, 'key_vnum', None)
            has_key = False
            if key_vnum:
                for item in player.inventory:
                    if hasattr(item, 'vnum') and item.vnum == key_vnum:
                        has_key = True
                        break

            if key_vnum and not has_key:
                await player.send(f"{c['red']}You don't have the key.{c['reset']}")
                return

            container.is_locked = True
            await player.send(f"{c['green']}*Click* You lock {container.short_desc}.{c['reset']}")
            return

        # Check for door
        direction = None
        for dir_name in player.config.DIRECTIONS.keys():
            if target_name in dir_name or target_name == dir_name:
                direction = dir_name
                break

        if not direction:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        if direction not in player.room.exits or not player.room.exits[direction]:
            await player.send(f"{c['red']}There's no exit {direction}.{c['reset']}")
            return

        exit_data = player.room.exits[direction]

        if 'door' not in exit_data:
            await player.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
            return

        door = exit_data['door']

        if door.get('locked', False):
            await player.send(f"{c['yellow']}The door is already locked.{c['reset']}")
            return

        # Check if closed
        if door.get('state') != 'closed':
            await player.send(f"{c['red']}You must close it first.{c['reset']}")
            return

        # Check for key
        key_vnum = door.get('key_vnum')
        has_key = False
        if key_vnum:
            for item in player.inventory:
                if hasattr(item, 'vnum') and item.vnum == key_vnum:
                    has_key = True
                    break

        if key_vnum and not has_key:
            await player.send(f"{c['red']}You don't have the key.{c['reset']}")
            return

        door['locked'] = True
        await player.send(f"{c['green']}*Click* You lock the {door.get('name', 'door')} {direction}.{c['reset']}")

    @classmethod
    async def cmd_unlock(cls, player: 'Player', args: List[str]):
        """Unlock a door or container. Usage: unlock <door/container>"""
        if not args:
            await player.send("Unlock what?")
            return

        c = player.config.COLORS
        target_name = ' '.join(args).lower()

        # Check for container first
        container = None
        for item in player.inventory + player.room.items:
            if target_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if container:
            if not hasattr(container, 'is_locked'):
                await player.send(f"{c['yellow']}The {container.name} cannot be locked.{c['reset']}")
                return

            if not container.is_locked:
                await player.send(f"{c['yellow']}The {container.name} is already unlocked.{c['reset']}")
                return

            # Check for key
            key_vnum = getattr(container, 'key_vnum', None)
            has_key = False
            if key_vnum:
                for item in player.inventory:
                    if hasattr(item, 'vnum') and item.vnum == key_vnum:
                        has_key = True
                        break

            if key_vnum and not has_key:
                await player.send(f"{c['red']}You don't have the key.{c['reset']}")
                return

            container.is_locked = False
            await player.send(f"{c['green']}*Click* You unlock {container.short_desc}.{c['reset']}")
            return

        # Check for door
        direction = None
        for dir_name in player.config.DIRECTIONS.keys():
            if target_name in dir_name or target_name == dir_name:
                direction = dir_name
                break

        if not direction:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        if direction not in player.room.exits or not player.room.exits[direction]:
            await player.send(f"{c['red']}There's no exit {direction}.{c['reset']}")
            return

        exit_data = player.room.exits[direction]

        if 'door' not in exit_data:
            await player.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
            return

        door = exit_data['door']

        if not door.get('locked', False):
            await player.send(f"{c['yellow']}The door is already unlocked.{c['reset']}")
            return

        # Check for key
        key_vnum = door.get('key_vnum')
        has_key = False
        if key_vnum:
            for item in player.inventory:
                if hasattr(item, 'vnum') and item.vnum == key_vnum:
                    has_key = True
                    break

        if key_vnum and not has_key:
            await player.send(f"{c['red']}You don't have the key.{c['reset']}")
            return

        door['locked'] = False
        await player.send(f"{c['green']}*Click* You unlock the {door.get('name', 'door')} {direction}.{c['reset']}")

    @classmethod
    async def cmd_pick(cls, player: 'Player', args: List[str]):
        """Pick a lock (Thief skill). Usage: pick <door/container>"""
        if not args:
            await player.send("Pick what lock?")
            return

        c = player.config.COLORS

        # Check if player has pick lock skill
        pick_skill = player.skills.get('pick_lock', 0)
        if pick_skill == 0:
            await player.send(f"{c['red']}You don't know how to pick locks!{c['reset']}")
            return

        target_name = ' '.join(args).lower()

        # Check for container first
        container = None
        for item in player.inventory + player.room.items:
            if target_name in item.name.lower():
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    container = item
                    break

        if container:
            if not hasattr(container, 'is_locked') or not container.is_locked:
                await player.send(f"{c['yellow']}The {container.name} isn't locked.{c['reset']}")
                return

            # Get pick difficulty
            difficulty = getattr(container, 'pick_difficulty', 50)

            # Attempt to pick
            roll = random.randint(1, 100)
            if roll <= pick_skill and roll + pick_skill >= difficulty:
                container.is_locked = False
                await player.send(f"{c['bright_green']}*Click* You successfully pick the lock on {container.short_desc}!{c['reset']}")
                await player.room.send_to_room(
                    f"{player.name} fiddles with {container.short_desc}.",
                    exclude=[player]
                )
            else:
                await player.send(f"{c['yellow']}You fail to pick the lock.{c['reset']}")
            return

        # Check for door
        direction = None
        for dir_name in player.config.DIRECTIONS.keys():
            if target_name in dir_name or target_name == dir_name:
                direction = dir_name
                break

        if not direction:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        if direction not in player.room.exits or not player.room.exits[direction]:
            await player.send(f"{c['red']}There's no exit {direction}.{c['reset']}")
            return

        exit_data = player.room.exits[direction]

        if 'door' not in exit_data:
            await player.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
            return

        door = exit_data['door']

        if not door.get('locked', False):
            await player.send(f"{c['yellow']}The door isn't locked.{c['reset']}")
            return

        # Get pick difficulty
        difficulty = door.get('pick_difficulty', 50)

        # Attempt to pick
        roll = random.randint(1, 100)
        if roll <= pick_skill and roll + pick_skill >= difficulty:
            door['locked'] = False
            await player.send(f"{c['bright_green']}*Click* You successfully pick the lock on the {door.get('name', 'door')}!{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} fiddles with the {door.get('name', 'door')} {direction}.",
                exclude=[player]
            )
        else:
            await player.send(f"{c['yellow']}You fail to pick the lock.{c['reset']}")

    # ==================== SHOP COMMANDS ====================

    @classmethod
    async def cmd_list(cls, player: 'Player', args: List[str]):
        """List items for sale in a shop. Usage: list"""
        from shops import ShopManager

        c = player.config.COLORS

        # Find shopkeeper in room
        shopkeeper = None
        for char in player.room.characters:
            if ShopManager.is_shopkeeper(char):
                shopkeeper = char
                break

        if not shopkeeper:
            await player.send(f"{c['red']}There's no shopkeeper here.{c['reset']}")
            return

        # Get shop
        shop = ShopManager.get_shop(shopkeeper)
        if not shop:
            await player.send(f"{c['red']}This merchant has nothing to sell.{c['reset']}")
            return

        # Check if shop is open
        game_time = player.world.game_time if hasattr(player.world, 'game_time') else None
        if not shop.is_open(game_time):
            await player.send(f"{c['yellow']}{shopkeeper.name} says, 'Sorry, I'm closed right now. Come back during business hours.'{c['reset']}")
            return

        await shop.list_items(player)

    @classmethod
    async def cmd_buy(cls, player: 'Player', args: List[str]):
        """Buy an item from a shop. Usage: buy <item>"""
        from shops import ShopManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Buy what? Use 'list' to see what's available.{c['reset']}")
            return

        # Find shopkeeper in room
        shopkeeper = None
        for char in player.room.characters:
            if ShopManager.is_shopkeeper(char):
                shopkeeper = char
                break

        if not shopkeeper:
            await player.send(f"{c['red']}There's no shopkeeper here.{c['reset']}")
            return

        # Get shop
        shop = ShopManager.get_shop(shopkeeper)
        if not shop:
            await player.send(f"{c['red']}This merchant has nothing to sell.{c['reset']}")
            return

        # Check if shop is open
        game_time = player.world.game_time if hasattr(player.world, 'game_time') else None
        if not shop.is_open(game_time):
            await player.send(f"{c['yellow']}{shopkeeper.name} says, 'Sorry, I'm closed right now.'{c['reset']}")
            return

        item_identifier = ' '.join(args)
        await shop.sell_to_player(player, item_identifier)

    @classmethod
    async def cmd_sell(cls, player: 'Player', args: List[str]):
        """Sell an item to a shop. Usage: sell <item>"""
        from shops import ShopManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Sell what? Use 'value <item>' to check prices.{c['reset']}")
            return

        # Find shopkeeper in room
        shopkeeper = None
        for char in player.room.characters:
            if ShopManager.is_shopkeeper(char):
                shopkeeper = char
                break

        if not shopkeeper:
            await player.send(f"{c['red']}There's no shopkeeper here.{c['reset']}")
            return

        # Get shop
        shop = ShopManager.get_shop(shopkeeper)
        if not shop:
            await player.send(f"{c['red']}This merchant doesn't buy items.{c['reset']}")
            return

        # Check if shop is open
        game_time = player.world.game_time if hasattr(player.world, 'game_time') else None
        if not shop.is_open(game_time):
            await player.send(f"{c['yellow']}{shopkeeper.name} says, 'Sorry, I'm closed right now.'{c['reset']}")
            return

        item_name = ' '.join(args)
        await shop.buy_from_player(player, item_name)

    @classmethod
    async def cmd_value(cls, player: 'Player', args: List[str]):
        """Check how much a shop will pay for an item. Usage: value <item>"""
        from shops import ShopManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Check the value of what?{c['reset']}")
            return

        # Find shopkeeper in room
        shopkeeper = None
        for char in player.room.characters:
            if ShopManager.is_shopkeeper(char):
                shopkeeper = char
                break

        if not shopkeeper:
            await player.send(f"{c['red']}There's no shopkeeper here.{c['reset']}")
            return

        # Get shop
        shop = ShopManager.get_shop(shopkeeper)
        if not shop:
            await player.send(f"{c['red']}This merchant doesn't buy items.{c['reset']}")
            return

        item_name = ' '.join(args)
        await shop.value_item(player, item_name)

    # ==================== GROUP COMMANDS ====================

    @classmethod
    async def cmd_group(cls, player: 'Player', args: List[str]):
        """Manage your group. Usage: group [player] or group leave"""
        from groups import GroupManager

        c = player.config.COLORS

        # No args - show group info
        if not args:
            await GroupManager.show_group(player)
            return

        # Leave group
        if args[0].lower() == 'leave':
            await GroupManager.leave_group(player)
            return

        # Invite player to group
        target_name = ' '.join(args).lower()

        # Find target in room
        target = None
        for char in player.room.characters:
            if char != player and hasattr(char, 'connection'):  # Is a player
                if char.name.lower().startswith(target_name):
                    target = char
                    break

        if not target:
            await player.send(f"{c['red']}Player '{target_name}' not found here.{c['reset']}")
            return

        # Try to add to group
        success = await GroupManager.join_group(player, target)

    @classmethod
    async def cmd_follow(cls, player: 'Player', args: List[str]):
        """Follow another player. Usage: follow <player> or follow self"""
        c = player.config.COLORS

        if not args:
            if hasattr(player, 'following') and player.following:
                await player.send(f"{c['cyan']}You are following {player.following.name}.{c['reset']}")
            else:
                await player.send(f"{c['yellow']}You aren't following anyone.{c['reset']}")
            return

        target_name = ' '.join(args).lower()

        # Stop following
        if target_name in ('self', 'stop', 'none'):
            if hasattr(player, 'following') and player.following:
                old_leader = player.following
                player.following = None
                await player.send(f"{c['yellow']}You stop following {old_leader.name}.{c['reset']}")
                await old_leader.send(f"{c['yellow']}{player.name} stops following you.{c['reset']}")
            else:
                await player.send(f"{c['yellow']}You aren't following anyone.{c['reset']}")
            return

        # Find target in room
        target = None
        for char in player.room.characters:
            if char != player and hasattr(char, 'connection'):  # Is a player
                if char.name.lower().startswith(target_name):
                    target = char
                    break

        if not target:
            await player.send(f"{c['red']}Player '{target_name}' not found here.{c['reset']}")
            return

        # Can't follow yourself
        if target == player:
            await player.send(f"{c['red']}You can't follow yourself!{c['reset']}")
            return

        # Start following
        player.following = target
        await player.send(f"{c['green']}You start following {target.name}.{c['reset']}")
        await target.send(f"{c['green']}{player.name} starts following you.{c['reset']}")

    @classmethod
    async def cmd_gtell(cls, player: 'Player', args: List[str]):
        """Send a message to your group. Usage: gtell <message>"""
        c = player.config.COLORS

        if not hasattr(player, 'group') or not player.group:
            await player.send(f"{c['red']}You're not in a group!{c['reset']}")
            return

        if not args:
            await player.send(f"{c['yellow']}Tell the group what?{c['reset']}")
            return

        message = ' '.join(args)
        await player.group.group_tell(player, message)

    @classmethod
    async def cmd_split(cls, player: 'Player', args: List[str]):
        """Split gold with your group. Usage: split <amount>"""
        c = player.config.COLORS

        if not hasattr(player, 'group') or not player.group:
            await player.send(f"{c['red']}You're not in a group!{c['reset']}")
            return

        if not args:
            await player.send(f"{c['yellow']}Split how much gold?{c['reset']}")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await player.send(f"{c['red']}Invalid amount.{c['reset']}")
            return

        if amount <= 0:
            await player.send(f"{c['red']}You must split a positive amount.{c['reset']}")
            return

        if player.gold < amount:
            await player.send(f"{c['red']}You don't have that much gold! You have {player.gold} gold.{c['reset']}")
            return

        # Take gold from player
        player.gold -= amount

        # Split among group
        await player.group.split_gold(amount)

        # Announce
        await player.send(f"{c['bright_yellow']}You split {amount} gold with your group.{c['reset']}")
        for member in player.group.members:
            if member != player:
                await member.send(f"{c['bright_yellow']}{player.name} splits {amount} gold with the group.{c['reset']}")

    # ==================== SOCIAL COMMANDS ====================

    SOCIALS = {
        'smile': {
            'no_arg_self': 'You smile happily.',
            'no_arg_room': '$n smiles happily.',
            'with_arg_self': 'You smile at $N.',
            'with_arg_target': '$n smiles at you.',
            'with_arg_room': '$n smiles at $N.',
        },
        'laugh': {
            'no_arg_self': 'You laugh out loud.',
            'no_arg_room': '$n laughs out loud.',
            'with_arg_self': 'You laugh at $N.',
            'with_arg_target': '$n laughs at you.',
            'with_arg_room': '$n laughs at $N.',
        },
        'nod': {
            'no_arg_self': 'You nod solemnly.',
            'no_arg_room': '$n nods solemnly.',
            'with_arg_self': 'You nod at $N.',
            'with_arg_target': '$n nods at you.',
            'with_arg_room': '$n nods at $N.',
        },
        'bow': {
            'no_arg_self': 'You bow deeply.',
            'no_arg_room': '$n bows deeply.',
            'with_arg_self': 'You bow before $N.',
            'with_arg_target': '$n bows before you.',
            'with_arg_room': '$n bows before $N.',
        },
        'wave': {
            'no_arg_self': 'You wave.',
            'no_arg_room': '$n waves.',
            'with_arg_self': 'You wave at $N.',
            'with_arg_target': '$n waves at you.',
            'with_arg_room': '$n waves at $N.',
        },
        'hug': {
            'no_arg_self': 'You need a hug!',
            'no_arg_room': '$n looks like $e needs a hug.',
            'with_arg_self': 'You hug $N warmly.',
            'with_arg_target': '$n hugs you warmly.',
            'with_arg_room': '$n hugs $N warmly.',
        },
        'dance': {
            'no_arg_self': 'You dance joyfully!',
            'no_arg_room': '$n dances joyfully!',
            'with_arg_self': 'You dance with $N.',
            'with_arg_target': '$n asks you to dance.',
            'with_arg_room': '$n dances with $N.',
        },
        'comfort': {
            'no_arg_self': 'You console yourself.',
            'no_arg_room': '$n looks like $e needs comfort.',
            'with_arg_self': 'You comfort $N.',
            'with_arg_target': '$n comforts you.',
            'with_arg_room': '$n comforts $N.',
        },
        'ponder': {
            'no_arg_self': 'You ponder the situation.',
            'no_arg_room': '$n ponders the situation.',
            'with_arg_self': 'You ponder $N thoughtfully.',
            'with_arg_target': '$n ponders you thoughtfully.',
            'with_arg_room': '$n ponders $N thoughtfully.',
        },
        'shrug': {
            'no_arg_self': 'You shrug.',
            'no_arg_room': '$n shrugs helplessly.',
            'with_arg_self': 'You shrug at $N.',
            'with_arg_target': '$n shrugs at you.',
            'with_arg_room': '$n shrugs at $N.',
        },
        'giggle': {
            'no_arg_self': 'You giggle.',
            'no_arg_room': '$n giggles.',
            'with_arg_self': 'You giggle at $N.',
            'with_arg_target': '$n giggles at you.',
            'with_arg_room': '$n giggles at $N.',
        },
        'sigh': {
            'no_arg_self': 'You sigh loudly.',
            'no_arg_room': '$n sighs loudly.',
            'with_arg_self': 'You sigh at $N.',
            'with_arg_target': '$n sighs at you.',
            'with_arg_room': '$n sighs at $N.',
        },
        'wink': {
            'no_arg_self': 'You wink suggestively.',
            'no_arg_room': '$n winks suggestively.',
            'with_arg_self': 'You wink at $N.',
            'with_arg_target': '$n winks at you.',
            'with_arg_room': '$n winks at $N.',
        },
        'grin': {
            'no_arg_self': 'You grin evilly.',
            'no_arg_room': '$n grins evilly.',
            'with_arg_self': 'You grin evilly at $N.',
            'with_arg_target': '$n grins evilly at you.',
            'with_arg_room': '$n grins evilly at $N.',
        },
        'cry': {
            'no_arg_self': 'You cry softly.',
            'no_arg_room': '$n cries softly.',
            'with_arg_self': 'You cry on $N\'s shoulder.',
            'with_arg_target': '$n cries on your shoulder.',
            'with_arg_room': '$n cries on $N\'s shoulder.',
        },
        'snicker': {
            'no_arg_self': 'You snicker.',
            'no_arg_room': '$n snickers.',
            'with_arg_self': 'You snicker at $N.',
            'with_arg_target': '$n snickers at you.',
            'with_arg_room': '$n snickers at $N.',
        },
        'pat': {
            'no_arg_self': 'You pat yourself on the back.',
            'no_arg_room': '$n pats $mself on the back.',
            'with_arg_self': 'You pat $N on the head.',
            'with_arg_target': '$n pats you on the head.',
            'with_arg_room': '$n pats $N on the head.',
        },
        'thank': {
            'no_arg_self': 'You thank everyone.',
            'no_arg_room': '$n thanks everyone.',
            'with_arg_self': 'You thank $N heartily.',
            'with_arg_target': '$n thanks you heartily.',
            'with_arg_room': '$n thanks $N heartily.',
        },
        'cheer': {
            'no_arg_self': 'You cheer loudly!',
            'no_arg_room': '$n cheers loudly!',
            'with_arg_self': 'You cheer for $N!',
            'with_arg_target': '$n cheers for you!',
            'with_arg_room': '$n cheers for $N!',
        },
        'glare': {
            'no_arg_self': 'You glare at nothing in particular.',
            'no_arg_room': '$n glares around $mself.',
            'with_arg_self': 'You glare icily at $N.',
            'with_arg_target': '$n glares icily at you.',
            'with_arg_room': '$n glares at $N.',
        },
        'grumble': {
            'no_arg_self': 'You grumble.',
            'no_arg_room': '$n grumbles.',
            'with_arg_self': 'You grumble at $N.',
            'with_arg_target': '$n grumbles at you.',
            'with_arg_room': '$n grumbles at $N.',
        },
        'yawn': {
            'no_arg_self': 'You yawn sleepily.',
            'no_arg_room': '$n yawns sleepily.',
            'with_arg_self': 'You yawn in $N\'s face.',
            'with_arg_target': '$n yawns in your face.',
            'with_arg_room': '$n yawns in $N\'s face.',
        },
        'cackle': {
            'no_arg_self': 'You cackle gleefully!',
            'no_arg_room': '$n cackles gleefully!',
            'with_arg_self': 'You cackle at $N.',
            'with_arg_target': '$n cackles at you.',
            'with_arg_room': '$n cackles at $N.',
        },
        'slap': {
            'no_arg_self': 'You slap yourself. Ouch!',
            'no_arg_room': '$n slaps $mself. Ouch!',
            'with_arg_self': 'You slap $N across the face!',
            'with_arg_target': '$n slaps you across the face!',
            'with_arg_room': '$n slaps $N across the face!',
        },
        'tickle': {
            'no_arg_self': 'You tickle yourself. How silly.',
            'no_arg_room': '$n tickles $mself. How silly.',
            'with_arg_self': 'You tickle $N.',
            'with_arg_target': '$n tickles you. Hee hee!',
            'with_arg_room': '$n tickles $N.',
        },
        'apologize': {
            'no_arg_self': 'You apologize for your behavior.',
            'no_arg_room': '$n apologizes for $s behavior.',
            'with_arg_self': 'You apologize to $N profusely.',
            'with_arg_target': '$n apologizes to you profusely.',
            'with_arg_room': '$n apologizes to $N profusely.',
        },
        'greet': {
            'no_arg_self': 'You greet everyone cheerfully.',
            'no_arg_room': '$n greets everyone cheerfully.',
            'with_arg_self': 'You greet $N cheerfully.',
            'with_arg_target': '$n greets you cheerfully.',
            'with_arg_room': '$n greets $N cheerfully.',
        },
        'poke': {
            'no_arg_self': 'You poke yourself in the ribs.',
            'no_arg_room': '$n pokes $mself in the ribs.',
            'with_arg_self': 'You poke $N in the ribs.',
            'with_arg_target': '$n pokes you in the ribs.',
            'with_arg_room': '$n pokes $N in the ribs.',
        },
        'salute': {
            'no_arg_self': 'You salute smartly.',
            'no_arg_room': '$n salutes smartly.',
            'with_arg_self': 'You salute $N.',
            'with_arg_target': '$n salutes you.',
            'with_arg_room': '$n salutes $N.',
        },
        'cringe': {
            'no_arg_self': 'You cringe in terror.',
            'no_arg_room': '$n cringes in terror.',
            'with_arg_self': 'You cringe away from $N.',
            'with_arg_target': '$n cringes away from you.',
            'with_arg_room': '$n cringes away from $N.',
        },
        'blush': {
            'no_arg_self': 'You blush.',
            'no_arg_room': '$n blushes.',
            'with_arg_self': 'You blush at $N.',
            'with_arg_target': '$n blushes at you.',
            'with_arg_room': '$n blushes at $N.',
        },
    }

    @classmethod
    async def cmd_social(cls, player: 'Player', social_name: str, args: List[str]):
        """Process a social command."""
        if social_name not in cls.SOCIALS:
            return False

        c = player.config.COLORS
        social = cls.SOCIALS[social_name]

        # No target - social to room
        if not args:
            # Message to self
            await player.send(f"{c['cyan']}{social['no_arg_self']}{c['reset']}")

            # Message to room
            msg = social['no_arg_room']
            msg = msg.replace('$n', player.name)
            msg = msg.replace('$e', 'he' if player.sex == 'male' else 'she')
            msg = msg.replace('$s', 'his' if player.sex == 'male' else 'her')
            msg = msg.replace('$m', 'him' if player.sex == 'male' else 'her')
            await player.room.send_to_room(f"{c['cyan']}{msg}{c['reset']}", exclude=[player])

        else:
            # Find target
            target_name = ' '.join(args).lower()
            target = None

            for char in player.room.characters:
                if char != player and char.name.lower().startswith(target_name):
                    target = char
                    break

            if not target:
                await player.send(f"{c['red']}Who do you want to {social_name}?{c['reset']}")
                return True

            # Can't target self with argument
            if target == player:
                await player.send(f"{c['red']}You can't {social_name} yourself!{c['reset']}")
                return True

            # Message to self
            msg_self = social['with_arg_self']
            msg_self = msg_self.replace('$N', target.name)
            await player.send(f"{c['cyan']}{msg_self}{c['reset']}")

            # Message to target
            if hasattr(target, 'send'):
                msg_target = social['with_arg_target']
                msg_target = msg_target.replace('$n', player.name)
                await target.send(f"{c['cyan']}{msg_target}{c['reset']}")

            # Message to room
            msg_room = social['with_arg_room']
            msg_room = msg_room.replace('$n', player.name)
            msg_room = msg_room.replace('$N', target.name)
            await player.room.send_to_room(
                f"{c['cyan']}{msg_room}{c['reset']}",
                exclude=[player, target]
            )

        return True

    # Generate individual social command methods
    @classmethod
    async def cmd_smile(cls, player: 'Player', args: List[str]):
        """Smile at someone."""
        await cls.cmd_social(player, 'smile', args)

    @classmethod
    async def cmd_laugh(cls, player: 'Player', args: List[str]):
        """Laugh."""
        await cls.cmd_social(player, 'laugh', args)

    @classmethod
    async def cmd_nod(cls, player: 'Player', args: List[str]):
        """Nod."""
        await cls.cmd_social(player, 'nod', args)

    @classmethod
    async def cmd_bow(cls, player: 'Player', args: List[str]):
        """Bow."""
        await cls.cmd_social(player, 'bow', args)

    @classmethod
    async def cmd_wave(cls, player: 'Player', args: List[str]):
        """Wave."""
        await cls.cmd_social(player, 'wave', args)

    @classmethod
    async def cmd_hug(cls, player: 'Player', args: List[str]):
        """Hug someone."""
        await cls.cmd_social(player, 'hug', args)

    @classmethod
    async def cmd_dance(cls, player: 'Player', args: List[str]):
        """Dance."""
        await cls.cmd_social(player, 'dance', args)

    @classmethod
    async def cmd_comfort(cls, player: 'Player', args: List[str]):
        """Comfort someone."""
        await cls.cmd_social(player, 'comfort', args)

    @classmethod
    async def cmd_ponder(cls, player: 'Player', args: List[str]):
        """Ponder."""
        await cls.cmd_social(player, 'ponder', args)

    @classmethod
    async def cmd_shrug(cls, player: 'Player', args: List[str]):
        """Shrug."""
        await cls.cmd_social(player, 'shrug', args)

    @classmethod
    async def cmd_giggle(cls, player: 'Player', args: List[str]):
        """Giggle."""
        await cls.cmd_social(player, 'giggle', args)

    @classmethod
    async def cmd_sigh(cls, player: 'Player', args: List[str]):
        """Sigh."""
        await cls.cmd_social(player, 'sigh', args)

    @classmethod
    async def cmd_wink(cls, player: 'Player', args: List[str]):
        """Wink."""
        await cls.cmd_social(player, 'wink', args)

    @classmethod
    async def cmd_grin(cls, player: 'Player', args: List[str]):
        """Grin."""
        await cls.cmd_social(player, 'grin', args)

    @classmethod
    async def cmd_cry(cls, player: 'Player', args: List[str]):
        """Cry."""
        await cls.cmd_social(player, 'cry', args)

    @classmethod
    async def cmd_snicker(cls, player: 'Player', args: List[str]):
        """Snicker."""
        await cls.cmd_social(player, 'snicker', args)

    @classmethod
    async def cmd_pat(cls, player: 'Player', args: List[str]):
        """Pat someone."""
        await cls.cmd_social(player, 'pat', args)

    @classmethod
    async def cmd_thank(cls, player: 'Player', args: List[str]):
        """Thank someone."""
        await cls.cmd_social(player, 'thank', args)

    @classmethod
    async def cmd_cheer(cls, player: 'Player', args: List[str]):
        """Cheer."""
        await cls.cmd_social(player, 'cheer', args)

    @classmethod
    async def cmd_glare(cls, player: 'Player', args: List[str]):
        """Glare at someone."""
        await cls.cmd_social(player, 'glare', args)

    @classmethod
    async def cmd_grumble(cls, player: 'Player', args: List[str]):
        """Grumble."""
        await cls.cmd_social(player, 'grumble', args)

    @classmethod
    async def cmd_yawn(cls, player: 'Player', args: List[str]):
        """Yawn."""
        await cls.cmd_social(player, 'yawn', args)

    @classmethod
    async def cmd_cackle(cls, player: 'Player', args: List[str]):
        """Cackle."""
        await cls.cmd_social(player, 'cackle', args)

    @classmethod
    async def cmd_slap(cls, player: 'Player', args: List[str]):
        """Slap someone."""
        await cls.cmd_social(player, 'slap', args)

    @classmethod
    async def cmd_tickle(cls, player: 'Player', args: List[str]):
        """Tickle someone."""
        await cls.cmd_social(player, 'tickle', args)

    @classmethod
    async def cmd_apologize(cls, player: 'Player', args: List[str]):
        """Apologize."""
        await cls.cmd_social(player, 'apologize', args)

    @classmethod
    async def cmd_greet(cls, player: 'Player', args: List[str]):
        """Greet someone."""
        await cls.cmd_social(player, 'greet', args)

    @classmethod
    async def cmd_poke(cls, player: 'Player', args: List[str]):
        """Poke someone."""
        await cls.cmd_social(player, 'poke', args)

    @classmethod
    async def cmd_salute(cls, player: 'Player', args: List[str]):
        """Salute."""
        await cls.cmd_social(player, 'salute', args)

    @classmethod
    async def cmd_cringe(cls, player: 'Player', args: List[str]):
        """Cringe."""
        await cls.cmd_social(player, 'cringe', args)

    @classmethod
    async def cmd_blush(cls, player: 'Player', args: List[str]):
        """Blush."""
        await cls.cmd_social(player, 'blush', args)

    # ==================== UTILITY ====================
    
    @classmethod
    async def cmd_help(cls, player: 'Player', args: List[str]):
        """Show help information."""
        c = player.config.COLORS
        
        if not args:
            await player.send(f"""
{c['cyan']}╔══════════════════════════════════════════════════════════════════╗
║{c['bright_yellow']}                         RealmsMUD Help                           {c['cyan']}║
╠══════════════════════════════════════════════════════════════════╣
║{c['white']} MOVEMENT:     north south east west up down                      {c['cyan']}║
║{c['white']} INFORMATION:  look score inventory equipment who where           {c['cyan']}║
║{c['white']} COMBAT:       kill flee kick bash backstab cast                  {c['cyan']}║
║{c['white']} ITEMS:        get drop give wear wield remove                    {c['cyan']}║
║{c['white']} COMMUNICATION: say shout gossip tell emote                       {c['cyan']}║
║{c['white']} POSITION:     sit rest sleep wake stand                          {c['cyan']}║
║{c['white']} OTHER:        skills spells practice consider quaff eat drink    {c['cyan']}║
║{c['white']} SYSTEM:       save quit help                                     {c['cyan']}║
╠══════════════════════════════════════════════════════════════════╣
║{c['white']} Type 'help <command>' for more information on a specific command.{c['cyan']}║
╚══════════════════════════════════════════════════════════════════╝{c['reset']}
""")
        else:
            topic = args[0].lower()
            help_topics = {
                'look': "LOOK - Look at your surroundings, a person, or an object.\nUsage: look [target]",
                'score': "SCORE - View your character statistics.\nUsage: score",
                'kill': "KILL - Attack a monster or NPC.\nUsage: kill <target>",
                'cast': "CAST - Cast a spell.\nUsage: cast <spell> [target]",
                'flee': "FLEE - Attempt to escape from combat.\nUsage: flee",
                'skills': "SKILLS - View your known skills.\nUsage: skills",
                'spells': "SPELLS - View your known spells.\nUsage: spells",
            }
            
            if topic in help_topics:
                await player.send(f"{c['cyan']}{help_topics[topic]}{c['reset']}")
            else:
                await player.send(f"No help available for '{topic}'.")
                
    @classmethod
    async def cmd_save(cls, player: 'Player', args: List[str]):
        """Save your character."""
        await player.save()
        await player.send("Character saved.")
        
    @classmethod
    async def cmd_quit(cls, player: 'Player', args: List[str]):
        """Quit the game."""
        if player.is_fighting:
            await player.send("You can't quit while fighting! Try to flee first.")
            return
            
        await player.save()
        await player.send("Farewell, brave adventurer! Your progress has been saved.")
        
        if player.room:
            await player.room.send_to_room(
                f"{player.name} has left the realm.",
                exclude=[player]
            )
            
        # Disconnect
        if player.connection:
            await player.connection.disconnect()
