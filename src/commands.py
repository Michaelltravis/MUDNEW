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
        'q': 'quit',
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
        'rec': 'recall',
        'zones': 'map',
        'worldmap': 'map',
    }
    
    @classmethod
    async def execute(cls, player: 'Player', cmd: str, args: List[str]):
        """Execute a command."""
        original_cmd = cmd

        # Check custom player aliases first
        if cmd in player.custom_aliases:
            cmd = player.custom_aliases[cmd]

        # Check built-in aliases
        cmd = cls.ALIASES.get(cmd, cmd)

        # Try exact match first
        method_name = f'cmd_{cmd}'
        method = getattr(cls, method_name, None)

        # If no exact match, try partial matching
        if not method:
            matches = []
            for attr_name in dir(cls):
                if attr_name.startswith('cmd_'):
                    command_name = attr_name[4:]  # Remove 'cmd_' prefix
                    if command_name.startswith(cmd):
                        matches.append((command_name, getattr(cls, attr_name)))

            if len(matches) == 1:
                # Single match found
                method = matches[0][1]
                # Show what command was matched
                c = player.config.COLORS
                if original_cmd != matches[0][0]:
                    await player.send(f"{c['cyan']}[{matches[0][0]}]{c['reset']}")
            elif len(matches) > 1:
                # Multiple matches - show suggestions
                c = player.config.COLORS
                match_names = f"{c['bright_yellow']}, {c['bright_green']}".join([m[0] for m in matches[:8]])  # Limit to 8 suggestions
                await player.send(f"{c['yellow']}Did you mean: {c['bright_green']}{match_names}{c['reset']}")
                if len(matches) > 8:
                    await player.send(f"{c['cyan']}...and {len(matches) - 8} more.{c['reset']}")
                return

        if method:
            await method(player, args)
        else:
            # Check if it's a direction
            if cmd in Config.DIRECTIONS:
                await cls.cmd_move(player, cmd)
            else:
                # Check partial direction matching
                dir_matches = [d for d in Config.DIRECTIONS if d.startswith(cmd)]
                if len(dir_matches) == 1:
                    # Show matched direction
                    c = player.config.COLORS
                    if original_cmd != dir_matches[0]:
                        await player.send(f"{c['cyan']}[{dir_matches[0]}]{c['reset']}")
                    await cls.cmd_move(player, dir_matches[0])
                elif len(dir_matches) > 1:
                    c = player.config.COLORS
                    dir_list = f"{c['bright_yellow']}, {c['bright_green']}".join(dir_matches)
                    await player.send(f"{c['yellow']}Did you mean: {c['bright_green']}{dir_list}{c['reset']}")
                else:
                    await player.send(f"Huh?!? '{original_cmd}' is not a valid command. Type 'help' for a list.")
    
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

        # Clear stale fighting state
        if player.position == 'fighting':
            # Check if actually fighting someone valid
            if not player.fighting or player.fighting.hp <= 0 or player.fighting not in player.room.characters:
                player.fighting = None
                player.position = 'standing'
            else:
                await player.send("You're fighting! Flee if you want to escape.")
                return
            
        if player.position in ('resting', 'sitting'):
            await player.send("You need to stand up first.")
            return
            
        exit_data = player.room.exits.get(direction)
        if not exit_data:
            await player.send("You can't go that way.")
            return

        # Check for closed door
        if 'door' in exit_data:
            door = exit_data['door']
            if door.get('state') == 'closed':
                c = player.config.COLORS
                await player.send(f"{c['red']}The {door.get('name', 'door')} is closed.{c['reset']}")
                return

        target_room = exit_data.get('room')
        if not target_room:
            await player.send("That exit seems to lead nowhere...")
            return
            
        # Check movement points
        sector = player.config.SECTOR_TYPES.get(target_room.sector_type, {'move_cost': 1})
        move_cost = sector['move_cost']

        # Mounted movement bonus (50% less movement cost)
        if player.mount:
            move_cost = max(1, move_cost // 2)

        if player.move < move_cost:
            await player.send("You are too exhausted to move!")
            return
            
        # Check if sneaking and make skill check
        sneak_success = False
        if 'sneaking' in player.flags and not player.mount:
            import random
            sneak_skill = player.skills.get('sneak', 0)
            # Skill check to move silently - easier than initial sneak
            if random.randint(1, 100) <= sneak_skill + 10:
                sneak_success = True
                # Small chance to improve skill
                if random.randint(1, 100) <= 5:
                    await player.improve_skill('sneak', difficulty=2)
            else:
                # Failed sneak check - break stealth
                player.flags.discard('sneaking')
                c = player.config.COLORS
                await player.send(f"{c['yellow']}You make a noise and break your stealth!{c['reset']}")

        # Leave message (only if not sneaking successfully)
        if not sneak_success:
            if player.mount:
                await player.room.send_to_room(
                    f"{player.name} rides {player.mount.name} {direction}.",
                    exclude=[player]
                )
            else:
                await player.room.send_to_room(
                    f"{player.name} leaves {direction}.",
                    exclude=[player]
                )

        # Move player (and mount if present)
        player.room.characters.remove(player)
        if player.mount and player.mount in player.room.characters:
            player.room.characters.remove(player.mount)

        player.room = target_room
        target_room.characters.append(player)
        if player.mount:
            target_room.characters.append(player.mount)

        player.move -= move_cost

        # Arrival message (only if not sneaking successfully)
        if not sneak_success:
            opposite = Config.DIRECTIONS.get(direction, {}).get('opposite', 'somewhere')
            if player.mount:
                await target_room.send_to_room(
                    f"{player.name} arrives from the {opposite}, riding {player.mount.name}.",
                    exclude=[player]
                )
            else:
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
    async def cmd_exits(cls, player: 'Player', args: List[str]):
        """Show available exits from the current room with descriptions."""
        c = player.config.COLORS

        if not player.room:
            await player.send("You are nowhere!")
            return

        if not player.room.exits:
            await player.send(f"{c['yellow']}There are no obvious exits.{c['reset']}")
            return

        await player.send(f"\n{c['cyan']}Obvious exits:{c['reset']}")

        has_exits = False
        for direction, exit_data in player.room.exits.items():
            if exit_data:
                has_exits = True
                # Get description if available
                desc = exit_data.get('description', '')

                # Check for door
                door_info = ""
                if 'door' in exit_data:
                    door = exit_data['door']
                    door_name = door.get('name', 'door')
                    state = door.get('state', 'open')
                    locked = door.get('locked', False)
                    if state == 'closed':
                        if locked:
                            door_info = f" {c['red']}[{door_name}, closed, locked]{c['reset']}"
                        else:
                            door_info = f" {c['yellow']}[{door_name}, closed]{c['reset']}"
                    else:
                        door_info = f" {c['green']}[{door_name}]{c['reset']}"

                # Format exit line
                if desc:
                    await player.send(f"  {c['bright_green']}{direction:8}{c['white']} - {desc}{door_info}{c['reset']}")
                else:
                    await player.send(f"  {c['bright_green']}{direction:8}{door_info}{c['reset']}")

        if not has_exits:
            await player.send(f"{c['yellow']}There are no obvious exits.{c['reset']}")

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

        # Show hunger and thirst status
        hunger_cond = player.get_hunger_condition()
        thirst_cond = player.get_thirst_condition()
        hunger_color = c['red'] if player.hunger <= 3 else c['yellow'] if player.hunger <= 6 else c['green']
        thirst_color = c['red'] if player.thirst <= 3 else c['yellow'] if player.thirst <= 6 else c['green']

        await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['cyan']}║ {c['white']}Hunger: {hunger_color}{hunger_cond:<12}{c['white']}  Thirst: {thirst_color}{thirst_cond:<12}{c['cyan']}              ║{c['reset']}")

        # Show active affects/buffs/debuffs
        if player.affects:
            await player.send(f"{c['cyan']}╠══════════════════════════════════════════════════════════════╣{c['reset']}")
            await player.send(f"{c['cyan']}║ {c['bright_cyan']}Active Effects:{c['reset']}                                            {c['cyan']}║{c['reset']}")

            for affect in player.affects:
                # Determine if it's a buff (positive) or debuff (negative)
                is_debuff = affect.name.lower() in ['poison', 'blindness', 'weaken', 'sleep', 'fear', 'curse']
                affect_color = c['red'] if is_debuff else c['bright_green']

                # Format the affect display
                duration_str = f"{affect.remaining}t"  # 't' for ticks
                affect_desc = f"{affect.name}"

                # Add effect details based on type
                if affect.type == 'modify_stat':
                    if affect.value > 0:
                        effect_str = f"+{affect.value} {affect.applies_to}"
                    else:
                        effect_str = f"{affect.value} {affect.applies_to}"
                    affect_desc = f"{affect.name} ({effect_str})"
                elif affect.type == 'flag':
                    affect_desc = f"{affect.name}"
                elif affect.type == 'dot':
                    affect_desc = f"{affect.name} ({affect.value} dmg/tick)"
                elif affect.type == 'hot':
                    affect_desc = f"{affect.name} ({affect.value} hp/tick)"

                # Truncate if too long
                if len(affect_desc) > 45:
                    affect_desc = affect_desc[:42] + "..."

                await player.send(f"{c['cyan']}║  {affect_color}• {affect_desc:<43}{c['white']}[{duration_str:>5}]{c['cyan']} ║{c['reset']}")

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
    async def cmd_map(cls, player: 'Player', args: List[str]):
        """Display map - world overview or local ASCII map.

        Usage:
            map        - Show world zone overview
            map world  - Show world zone overview
            map local  - Show local ASCII map (if available)
        """
        c = player.config.COLORS

        # Check if local map requested
        if args and args[0].lower() == 'local':
            await cls._show_local_map(player)
            return

        # Show world map (default)
        await player.send(f"{c['bright_cyan']}╔═══════════════════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}                        REALMSMUD WORLD MAP                                  {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╚═══════════════════════════════════════════════════════════════════════════╝{c['reset']}")
        await player.send("")

        # Current location indicator
        current_zone = player.room.vnum // 100 if player.room else 0
        zone = player.world.zones.get(current_zone)
        zone_name = zone.name if zone else 'Unknown'
        await player.send(f"{c['white']}You are currently in: {c['bright_green']}{zone_name}{c['reset']}")
        await player.send("")

        # Zone map organized by region and level
        await player.send(f"{c['bright_yellow']}═══ NEWBIE ZONES (Level 1-10) ═══{c['reset']}")
        zones_newbie = [
            (15, "The Straight Path", "Easy tutorial area"),
            (186, "Newbie Zone", "Beginner training grounds"),
            (30, "Midgaard City", "Central hub, shops & quests"),
        ]
        for vnum, name, desc in zones_newbie:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['cyan']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['yellow']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['bright_yellow']}═══ LOW LEVEL ZONES (Level 5-15) ═══{c['reset']}")
        zones_low = [
            (31, "South Midgaard", "City streets & alleys"),
            (33, "Three Of Swords", "Wilderness adventure"),
            (60, "Haon-Dor Light Forest", "Peaceful woods"),
            (9, "River Island Of Minos", "Minotaur labyrinth"),
            (90, "Haunted Swamp", "Undead bog"),
        ]
        for vnum, name, desc in zones_low:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['cyan']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['yellow']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['bright_yellow']}═══ MID LEVEL ZONES (Level 10-25) ═══{c['reset']}")
        zones_mid = [
            (35, "Miden'Nir", "Elven stronghold"),
            (36, "Chessboard", "Strategic combat"),
            (40, "Mines of Moria", "Deep dwarven mines"),
            (50, "Great Eastern Desert", "Vast wasteland"),
            (52, "The City of Thalos", "Ancient metropolis"),
            (61, "Haon-Dor Dark Forest", "Dangerous woods"),
            (62, "The Orc Enclave", "Orcish camp"),
            (63, "Arachnos", "Spider caverns"),
            (64, "Rand's Tower", "Wizard's tower"),
            (65, "Dwarven Kingdom", "Mountain halls"),
            (100, "Dwarven Mines", "Rich ore deposits"),
            (110, "Elven Village", "Silversong settlement"),
        ]
        for vnum, name, desc in zones_mid:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['cyan']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['yellow']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['bright_yellow']}═══ HIGH LEVEL ZONES (Level 20-35) ═══{c['reset']}")
        zones_high = [
            (51, "Drow City", "Dark elf metropolis"),
            (53, "The Great Pyramid", "Ancient tombs"),
            (54, "New Thalos", "Massive city (285 rooms!)"),
            (70, "Sewers Level 1", "Underground tunnels"),
            (71, "Sewers Level 2", "Deeper sewers"),
            (72, "Sewer Maze", "Complex labyrinth"),
            (120, "Rome", "Ancient city"),
            (130, "Sunken Ruins", "Underwater temple"),
            (140, "Necropolis", "City of the dead"),
        ]
        for vnum, name, desc in zones_high:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['cyan']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['yellow']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['bright_red']}═══ EPIC ZONES (Level 30-50) ═══{c['reset']}")
        zones_epic = [
            (25, "High Tower Of Magic", "Arcane challenges"),
            (79, "Redferne's Residence", "Wizard's home"),
            (80, "Dragon's Domain", "Ancient dragon lair"),
            (150, "King Welmar's Castle", "Royal fortress"),
            (160, "Plane of Eternal Chaos", "Planar battleground"),
        ]
        for vnum, name, desc in zones_epic:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['bright_red']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['bright_red']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['bright_yellow']}═══ SPECIAL ZONES ═══{c['reset']}")
        zones_special = [
            (0, "Limbo", "Admin zone"),
            (12, "God Simplex", "Immortal area"),
        ]
        for vnum, name, desc in zones_special:
            marker = f"{c['bright_green']}[YOU]" if vnum == current_zone else "     "
            await player.send(f"  {marker} {c['magenta']}{vnum:3d}{c['reset']} - {c['white']}{name:<30}{c['magenta']} {desc}{c['reset']}")

        await player.send("")
        await player.send(f"{c['cyan']}═══ MAP LEGEND ═══{c['reset']}")
        await player.send(f"  {c['bright_green']}[YOU]{c['reset']} - Your current zone")
        await player.send(f"  {c['cyan']}###{c['reset']}  - Zone number (use 'goto' to travel)")
        await player.send(f"  {c['yellow']}Recall{c['reset']} to return to Temple of Midgaard (zone 30)")
        await player.send("")
        await player.send(f"{c['white']}Total: {c['bright_green']}37 zones{c['white']}, {c['bright_green']}2,002 rooms{c['white']}, {c['bright_green']}48 shops{c['reset']}")
        await player.send(f"{c['cyan']}═════════════════════════════════════════════════════════════════════════{c['reset']}")

    @classmethod
    async def _show_local_map(cls, player: 'Player'):
        """Display an ASCII map of the current zone with player position."""
        c = player.config.COLORS

        if not player.room:
            await player.send("You are nowhere!")
            return

        # Zone-specific ASCII maps
        zone_maps = {
            30: """
{cyan}╔════════════════════════════════════════════════════════════╗
║{bright_yellow}              The City of Midgaard - Map                    {cyan}║
╠════════════════════════════════════════════════════════════╣
║{white}                                                            {cyan}║
║{white}                         [Temple]                          {cyan}║
║{white}                            |                              {cyan}║
║{white}              [Dark]---[Square]---[East St]---[E.Gate]    {cyan}║
║{white}               Alley       |         |                     {cyan}║
║{white}                 |      [W.St]---[Weapon]                 {cyan}║
║{white}              [Dead]       |         |                     {cyan}║
║{white}                 |       [Inn]---[Magic]                   {cyan}║
║{white}              [Guild]                                      {cyan}║
║{white}                 |                                         {cyan}║
║{white}              [Sewers]                                     {cyan}║
║{white}                                                            {cyan}║
╚════════════════════════════════════════════════════════════╝{reset}
""",
            35: """
{cyan}╔════════════════════════════════════════════════════════════╗
║{bright_yellow}           The Sewers of Midgaard - Map                    {cyan}║
╠════════════════════════════════════════════════════════════╣
║{white}                                                            {cyan}║
║{white}              [City Exit]                                  {cyan}║
║{white}                   |                                       {cyan}║
║{white}          [Flooded]---[Side]                              {cyan}║
║{white}               |         |                                 {cyan}║
║{white}     [Entrance]---[Junction]---[Storage]                  {cyan}║
║{white}               |         |                                 {cyan}║
║{white}           [Rat King] [Pool]---[Collector]                {cyan}║
║{white}                                                            {cyan}║
╚════════════════════════════════════════════════════════════╝{reset}
""",
            40: """
{cyan}╔════════════════════════════════════════════════════════════╗
║{bright_yellow}             Haon Dor Forest - Map                         {cyan}║
╠════════════════════════════════════════════════════════════╣
║{white}                                                            {cyan}║
║{white}                      [Clearing]                           {cyan}║
║{white}                           |                               {cyan}║
║{white}         [Midgaard]---[Entrance]---[Dark Path]            {cyan}║
║{white}                           |                               {cyan}║
║{white}                      [Oak Grove]                          {cyan}║
║{white}                           |                               {cyan}║
║{white}                    [Goblin Warrens]                       {cyan}║
║{white}                                                            {cyan}║
╚════════════════════════════════════════════════════════════╝{reset}
"""
        }

        # Get the appropriate map for this zone
        zone_num = player.room.vnum // 100
        map_template = zone_maps.get(zone_num)

        if not map_template:
            # Generic map for zones without specific maps
            await player.send(f"{c['cyan']}Local map not available for this zone.{c['reset']}")
            await player.send(f"{c['yellow']}Try 'map' or 'map world' to see the world overview.{c['reset']}")
            await player.send(f"{c['white']}Current location: {player.room.name}{c['reset']}")
            return

        # Replace room names with highlighted version if player is there
        room_markers = {
            # Zone 30 - Midgaard
            3001: "Temple",
            3002: "Square",
            3003: "East St",
            3004: "E.Gate",
            3005: "W.St",
            3010: "Dark",
            3011: "Dead",
            3012: "Guild",
            3020: "Weapon",
            3021: "Magic",
            3030: "Inn",
            3031: "Inn",
            # Zone 35 - Sewers
            3500: "Entrance",
            3501: "Flooded",
            3502: "Junction",
            3503: "Rat King",
            3504: "City Exit",
            3505: "Flooded",
            3506: "Pool",
            3507: "Side",
            3508: "Storage",
            3509: "Collector",
            # Zone 40 - Forest
            4001: "Entrance",
            4002: "Clearing",
            4003: "Dark Path",
            4004: "Oak Grove",
        }

        marker = room_markers.get(player.room.vnum)
        if marker:
            # Highlight player's current position
            map_output = map_template.replace(f"[{marker}]", f"{{bright_green}}[@{marker}@]{{white}}")
        else:
            map_output = map_template

        # Format with colors
        map_output = map_output.format(**c)

        await player.send(map_output)
        await player.send(f"{c['bright_yellow']}You are here: {c['bright_green']}{player.room.name}{c['reset']}")

    @classmethod
    async def cmd_help(cls, player: 'Player', args: List[str]):
        """Show help information for commands, skills, and spells."""
        from help_data import get_help_text, get_help_index

        c = player.config.COLORS

        if not args:
            # Show help index
            help_text = get_help_index()
            await player.send(f"{c['white']}{help_text}{c['reset']}")
            return

        # Look up specific topic
        topic = ' '.join(args).lower()
        help_text = get_help_text(topic)

        if help_text:
            await player.send(f"{c['white']}{help_text}{c['reset']}")
        else:
            await player.send(f"{c['red']}No help available for '{topic}'.{c['reset']}")
            await player.send(f"{c['yellow']}Type 'help' for a list of topics.{c['reset']}")

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

    # ==================== SKILLS ====================

    @classmethod
    async def cmd_sneak(cls, player: 'Player', args: List[str]):
        """Toggle sneak mode."""
        c = player.config.COLORS

        # Check if player has the skill
        if 'sneak' not in player.skills:
            await player.send(f"{c['red']}You don't know how to sneak!{c['reset']}")
            return

        # Toggle sneak
        if 'sneaking' in player.flags:
            player.flags.remove('sneaking')
            await player.send(f"{c['yellow']}You stop sneaking.{c['reset']}")
        else:
            # Skill check
            import random
            skill_level = player.skills['sneak']
            if random.randint(1, 100) <= skill_level:
                player.flags.add('sneaking')
                await player.send(f"{c['green']}You start moving silently...{c['reset']}")
                # Improve skill
                await player.improve_skill('sneak', difficulty=3)
            else:
                await player.send(f"{c['yellow']}You try to move quietly but fail.{c['reset']}")

    @classmethod
    async def cmd_hide(cls, player: 'Player', args: List[str]):
        """Attempt to hide in shadows."""
        c = player.config.COLORS

        # Check if player has the skill
        if 'hide' not in player.skills:
            await player.send(f"{c['red']}You don't know how to hide!{c['reset']}")
            return

        # Can't hide while fighting
        if player.is_fighting:
            await player.send(f"{c['red']}You can't hide while fighting!{c['reset']}")
            return

        # Skill check
        import random
        skill_level = player.skills['hide']
        if random.randint(1, 100) <= skill_level:
            player.flags.add('hidden')
            await player.send(f"{c['green']}You blend into the shadows...{c['reset']}")
            # Improve skill
            await player.improve_skill('hide', difficulty=4)
        else:
            await player.send(f"{c['yellow']}You fail to conceal yourself.{c['reset']}")

    @classmethod
    async def cmd_visible(cls, player: 'Player', args: List[str]):
        """Come out of hiding or stop sneaking."""
        c = player.config.COLORS

        made_visible = False
        if 'hidden' in player.flags:
            player.flags.remove('hidden')
            made_visible = True
        if 'sneaking' in player.flags:
            player.flags.remove('sneaking')
            made_visible = True

        if made_visible:
            await player.send(f"{c['yellow']}You step out of the shadows.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} emerges from the shadows.",
                exclude=[player]
            )
        else:
            await player.send(f"{c['yellow']}You are already visible.{c['reset']}")

    @classmethod
    async def cmd_backstab(cls, player: 'Player', args: List[str]):
        """Attempt to backstab a target (thief/assassin skill)."""
        c = player.config.COLORS

        if 'backstab' not in player.skills:
            await player.send(f"{c['red']}You don't know how to backstab!{c['reset']}")
            return

        if player.is_fighting:
            await player.send(f"{c['red']}You can't backstab while already fighting!{c['reset']}")
            return

        # If no args, use current target
        if not args:
            if player.target and player.target in player.room.characters:
                target = player.target
            else:
                await player.send("Backstab whom?")
                if player.target:
                    await player.send(f"{c['yellow']}(Your target is not here. Use 'target <name>' to set a new target){c['reset']}")
                return
        else:
            # Find target with numbered targeting support
            target_name = ' '.join(args).lower()
            target = player.find_target_in_room(target_name)

            if not target:
                await player.send(f"{c['red']}They aren't here.{c['reset']}")
                return

        # Skill check
        import random
        skill_level = player.skills['backstab']

        if random.randint(1, 100) > skill_level:
            await player.send(f"{c['yellow']}You try to backstab {target.name} but fumble!{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} tries to backstab {target.name} but fails!",
                exclude=[player]
            )
            # Start combat anyway
            from combat import CombatHandler
            await CombatHandler.start_combat(player, target)
            return

        # Successful backstab - calculate massive damage
        base_damage = random.randint(player.level, player.level * 3)
        backstab_multiplier = 3 + (skill_level // 25)  # 3x to 6x damage
        damage = base_damage * backstab_multiplier

        await player.send(f"{c['bright_red']}You slip behind {target.name} and STAB them in the back!{c['reset']}")
        await player.room.send_to_room(
            f"{player.name} sneaks behind {target.name} and delivers a devastating backstab!",
            exclude=[player, target]
        )

        if hasattr(target, 'send'):
            await target.send(f"{c['bright_red']}{player.name} backstabs you!{c['reset']}")

        # Apply damage
        await target.take_damage(damage, player)

        # Improve skill
        await player.improve_skill('backstab', difficulty=6)

        # Start combat if target survived
        if target.hp > 0:
            from combat import CombatHandler
            await CombatHandler.start_combat(player, target)

    # ==================== COMBAT ====================

    @classmethod
    async def cmd_target(cls, player: 'Player', args: List[str]):
        """Set your combat target."""
        c = player.config.COLORS

        if not args:
            # Show current target
            if player.target:
                await player.send(f"{c['yellow']}Your current target: {c['red']}{player.target.name}{c['reset']}")
            else:
                await player.send(f"{c['yellow']}You have no target set.{c['reset']}")
                await player.send(f"{c['white']}Usage: target <name> - Set combat target{c['reset']}")
                await player.send(f"{c['white']}       target clear - Clear target{c['reset']}")
            return

        if args[0].lower() in ['clear', 'none', 'off']:
            player.target = None
            await player.send(f"{c['yellow']}Combat target cleared.{c['reset']}")
            return

        target_name = ' '.join(args).lower()
        target = player.find_target_in_room(target_name)

        if not target:
            await player.send(f"{c['red']}You don't see '{target_name}' here.{c['reset']}")
            return

        # Check if it's a player
        if hasattr(target, 'connection'):
            await player.send(f"{c['red']}You can't target other players!{c['reset']}")
            return

        player.target = target
        await player.send(f"{c['green']}Target set: {c['red']}{target.name}{c['reset']}")

    @classmethod
    async def cmd_kill(cls, player: 'Player', args: List[str]):
        """Attack a target."""
        c = player.config.COLORS

        # If no args, use current target
        if not args:
            if player.target and player.target in player.room.characters:
                target = player.target
            else:
                await player.send("Kill whom?")
                if player.target:
                    await player.send(f"{c['yellow']}(Your target is not here. Use 'target <name>' to set a new target){c['reset']}")
                return
        else:
            # Find target with numbered targeting support
            target_name = ' '.join(args).lower()
            target = player.find_target_in_room(target_name)

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
        c = player.config.COLORS

        if not args:
            await player.send("Cast what spell?")
            return

        # Join all args to handle quoted spell names
        full_args = ' '.join(args)

        # Remove quotes if present
        full_args = full_args.replace("'", "").replace('"', '')

        # Split into spell name and target
        parts = full_args.split(' ', 1)
        spell_input = parts[0].lower()
        target_name = parts[1] if len(parts) > 1 else None

        # Check if player has any spells
        if not player.spells:
            await player.send(f"{c['red']}You don't know any spells!{c['reset']}")
            return

        # Find matching spell - convert spaces to underscores for matching
        spell_search = spell_input.replace(' ', '_')
        matching_spell = None

        for spell_key in player.spells:
            # Match by exact name or prefix
            if spell_key == spell_search or spell_key.startswith(spell_search):
                matching_spell = spell_key
                break
            # Also try matching the display name
            if spell_key.replace('_', ' ') == spell_input or spell_key.replace('_', ' ').startswith(spell_input):
                matching_spell = spell_key
                break

        if not matching_spell:
            await player.send(f"{c['red']}You don't know the spell '{spell_input}'!{c['reset']}")
            await player.send(f"{c['cyan']}Type 'spells' to see your known spells.{c['reset']}")
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
        """Practice skills/spells - must be at a guild master or trainer."""
        c = player.config.COLORS

        # Check for trainer/guildmaster in room
        has_trainer = False
        from mobs import Mobile
        if player.room:
            for char in player.room.characters:
                if isinstance(char, Mobile) and char.special in ('trainer', 'guildmaster'):
                    has_trainer = True
                    break

        if not has_trainer:
            await player.send(f"{c['red']}You must find a guild master or trainer to practice!{c['reset']}")
            await player.send(f"{c['yellow']}Trainers can be found in the guilds around town.{c['reset']}")
            return

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
        """Pick up an item.

        Usage:
            get <item>              - Get item from room
            get all                 - Get all items from room
            get <item> <container>  - Get item from container
            get all <container>     - Get all items from container
            get <item> from <container> - Alternative syntax
            get all from <container>    - Alternative syntax
        """
        if not args:
            await player.send("Get what?")
            return

        c = player.config.COLORS

        # Support both "get item container" and "get item from container" syntax
        # Check if last argument is a container (and no "from" keyword)
        from_container = False
        container_name = None

        if len(args) >= 2 and 'from' not in args:
            # Check if last argument might be a container
            potential_container = args[-1].lower()
            for item in player.inventory + player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if potential_container in item.name.lower() or potential_container in item.short_desc.lower():
                        from_container = True
                        container_name = potential_container
                        # Rebuild item_name without container
                        item_name = ' '.join(args[:-1]).lower()
                        break

        if not from_container:
            item_name = ' '.join(args).lower()

        # Check if getting gold from room (not from container)
        if not from_container and 'from' not in args and (item_name in ['gold', 'coins', 'coin', 'gold coins']):
            if player.room.gold <= 0:
                await player.send(f"{c['yellow']}There's no gold here.{c['reset']}")
                return

            gold_amount = player.room.gold
            player.gold += gold_amount
            player.room.gold = 0

            await player.send(f"{c['yellow']}You get {gold_amount} gold coins. You now have {player.gold} gold.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} picks up some gold coins.",
                exclude=[player]
            )
            return

        # Check if getting from container (either "get item container" or "get item from container")
        if from_container or 'from' in args:
            # If using "from" syntax, extract container name
            if 'from' in args:
                from_idx = args.index('from')
                item_name = ' '.join(args[:from_idx]).lower()
                container_name = ' '.join(args[from_idx+1:]).lower()

            # Find container in inventory or room
            container = None
            for item in player.inventory + player.room.items:
                if container_name in item.name.lower() or container_name in item.short_desc.lower():
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

            # Check if getting gold from container
            if item_name in ['gold', 'coins', 'coin', 'gold coins']:
                if not hasattr(container, 'gold') or container.gold <= 0:
                    await player.send(f"{c['yellow']}There's no gold in {container.short_desc}.{c['reset']}")
                    return

                gold_amount = container.gold
                player.gold += gold_amount
                container.gold = 0

                await player.send(f"{c['yellow']}You get {gold_amount} gold coins from {container.short_desc}. You now have {player.gold} gold.{c['reset']}")
                await player.room.send_to_room(
                    f"{player.name} gets gold coins from {container.short_desc}.",
                    exclude=[player]
                )
                return

            # Check if getting 'all' from container
            if item_name == 'all':
                # Get gold first if any
                if hasattr(container, 'gold') and container.gold > 0:
                    gold_amount = container.gold
                    player.gold += gold_amount
                    container.gold = 0
                    await player.send(f"{c['yellow']}You get {gold_amount} gold coins from {container.short_desc}.{c['reset']}")

                if not hasattr(container, 'contents') or not container.contents:
                    if not hasattr(container, 'gold') or container.gold == 0:
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

        # Check for 'all.corpse' or 'all.chest' - get all items from all matching containers
        if '.' in item_name and item_name.startswith('all.'):
            container_type = item_name.split('.', 1)[1]
            containers = []

            # Find all matching containers
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if container_type in item.name.lower():
                        containers.append(item)

            if not containers:
                await player.send(f"{c['yellow']}You don't see any {container_type}s here.{c['reset']}")
                return

            total_gold = 0
            total_items = 0

            for container in containers:
                # Check if container is closed
                if hasattr(container, 'is_closed') and container.is_closed:
                    await player.send(f"{c['yellow']}The {container.short_desc} is closed.{c['reset']}")
                    continue

                # Get gold from this container
                if hasattr(container, 'gold') and container.gold > 0:
                    total_gold += container.gold
                    container.gold = 0

                # Get items from this container
                if hasattr(container, 'contents') and container.contents:
                    for item in list(container.contents):
                        container.contents.remove(item)
                        player.inventory.append(item)
                        await player.send(f"You get {item.short_desc} from {container.short_desc}.")
                        total_items += 1

            if total_gold > 0:
                player.gold += total_gold
                await player.send(f"{c['yellow']}You get {total_gold} gold coins. You now have {player.gold} gold.{c['reset']}")

            if total_items == 0 and total_gold == 0:
                await player.send(f"{c['white']}All {container_type}s are empty.{c['reset']}")

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
    async def cmd_loot(cls, player: 'Player', args: List[str]):
        """Loot items from a corpse."""
        c = player.config.COLORS

        # Find corpse - default to first corpse if no args
        corpse = None
        if args:
            corpse_name = ' '.join(args).lower()
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower() and corpse_name in item.name.lower():
                        corpse = item
                        break
        else:
            # No args - find first corpse
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpse = item
                        break

        if not corpse:
            await player.send(f"{c['yellow']}You don't see any corpses to loot here.{c['reset']}")
            return

        # Loot gold from corpse if any
        gold_looted = 0
        if hasattr(corpse, 'gold') and corpse.gold > 0:
            player.gold += corpse.gold
            gold_looted = corpse.gold
            corpse.gold = 0

        # Loot items from corpse
        items_looted = 0
        if hasattr(corpse, 'contents') and corpse.contents:
            for item in list(corpse.contents):
                corpse.contents.remove(item)
                player.inventory.append(item)
                await player.send(f"{c['bright_cyan']}You get {item.short_desc} from {corpse.short_desc}.{c['reset']}")
                items_looted += 1

        # Report what was looted
        if gold_looted > 0:
            await player.send(f"{c['yellow']}You get {gold_looted} gold coins from {corpse.short_desc}.{c['reset']}")

        if items_looted == 0 and gold_looted == 0:
            await player.send(f"{c['white']}The {corpse.short_desc} is empty.{c['reset']}")
        else:
            await player.room.send_to_room(
                f"{player.name} loots {corpse.short_desc}.",
                exclude=[player]
            )

    @classmethod
    async def cmd_sacrifice(cls, player: 'Player', args: List[str]):
        """Sacrifice a corpse to the gods for gold."""
        c = player.config.COLORS

        # Check for .all, all, or all.corpse to sacrifice all corpses
        if args and (args[0] == '.all' or args[0] == 'all' or args[0].startswith('all.')):
            corpses = []
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpses.append(item)

            if not corpses:
                await player.send(f"{c['yellow']}You don't see any corpses to sacrifice here.{c['reset']}")
                return

            total_gold = 0
            corpse_count = 0

            for corpse in list(corpses):
                # Drop all items from corpse onto the floor
                if hasattr(corpse, 'contents') and corpse.contents:
                    for item in list(corpse.contents):
                        corpse.contents.remove(item)
                        player.room.items.append(item)

                # Drop any gold from corpse onto the floor
                if hasattr(corpse, 'gold') and corpse.gold > 0:
                    player.room.gold += corpse.gold

                # Remove corpse from room
                player.room.items.remove(corpse)

                # Give player 1 gold per corpse
                player.gold += 1
                total_gold += 1
                corpse_count += 1

            await player.send(f"{c['bright_yellow']}You sacrifice {corpse_count} corpses to the gods!{c['reset']}")
            await player.send(f"{c['yellow']}The gods give you {total_gold} gold coins for your offerings.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} sacrifices multiple corpses in brilliant flashes of light!",
                exclude=[player]
            )
            return

        # Find corpse - default to first corpse if no args
        corpse = None
        if args:
            corpse_name = ' '.join(args).lower()
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower() and corpse_name in item.name.lower():
                        corpse = item
                        break
        else:
            # No args - find first corpse
            for item in player.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpse = item
                        break

        if not corpse:
            await player.send(f"{c['yellow']}You don't see any corpses to sacrifice here.{c['reset']}")
            return

        # Drop all items from corpse onto the floor
        items_dropped = 0
        if hasattr(corpse, 'contents') and corpse.contents:
            for item in list(corpse.contents):
                corpse.contents.remove(item)
                player.room.items.append(item)
                items_dropped += 1

        # Drop any gold from corpse onto the floor
        if hasattr(corpse, 'gold') and corpse.gold > 0:
            player.room.gold += corpse.gold

        # Remove corpse from room
        player.room.items.remove(corpse)

        # Give player 1 gold for the sacrifice
        player.gold += 1

        # Messages
        await player.send(f"{c['bright_yellow']}You sacrifice {corpse.short_desc} to the gods!{c['reset']}")
        await player.send(f"{c['yellow']}The gods give you 1 gold coin for your offering.{c['reset']}")

        if items_dropped > 0:
            await player.send(f"{c['white']}The contents of the corpse scatter on the ground.{c['reset']}")

        await player.room.send_to_room(
            f"{player.name} sacrifices {corpse.short_desc} in a brilliant flash of light!",
            exclude=[player]
        )

    @classmethod
    async def cmd_drop(cls, player: 'Player', args: List[str]):
        """Drop an item or gold."""
        if not args:
            await player.send("Drop what?")
            return

        c = player.config.COLORS
        item_name = ' '.join(args).lower()

        # Check if dropping gold
        if 'gold' in item_name or 'coins' in item_name or 'coin' in item_name:
            # Extract amount if specified (e.g., "drop 100 gold")
            amount = None
            words = item_name.split()
            for word in words:
                if word.isdigit():
                    amount = int(word)
                    break

            if amount is None:
                amount = player.gold

            if amount <= 0:
                await player.send(f"{c['yellow']}Drop how much gold?{c['reset']}")
                return

            if player.gold < amount:
                await player.send(f"{c['red']}You don't have that much gold. You have {player.gold} gold.{c['reset']}")
                return

            player.gold -= amount
            player.room.gold += amount

            await player.send(f"{c['yellow']}You drop {amount} gold coins. You have {player.gold} gold remaining.{c['reset']}")
            await player.room.send_to_room(
                f"{player.name} drops some gold coins.",
                exclude=[player]
            )
            return

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
        """Wear an item or 'wear all' to wear everything you can."""
        if not args:
            await player.send("Wear what?")
            return

        item_name = ' '.join(args).lower()

        # Handle "wear all"
        if item_name == 'all':
            worn_count = 0
            items_to_wear = [item for item in player.inventory
                           if item.item_type in ('armor', 'light', 'worn') and hasattr(item, 'wear_slot')]

            for item in items_to_wear:
                slot = item.wear_slot
                # Only wear if slot is empty
                if not player.equipment.get(slot):
                    player.inventory.remove(item)
                    player.equipment[slot] = item
                    await player.send(f"You wear {item.short_desc}.")
                    worn_count += 1

            if worn_count > 0:
                await player.room.send_to_room(
                    f"{player.name} puts on several items.",
                    exclude=[player]
                )
            else:
                await player.send("You don't have anything to wear.")
            return

        # Find specific item in inventory
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
        """Remove worn equipment or 'remove all' to remove everything."""
        if not args:
            await player.send("Remove what?")
            return

        item_name = ' '.join(args).lower()

        # Handle "remove all"
        if item_name == 'all':
            removed_count = 0
            for slot, item in list(player.equipment.items()):
                if item:
                    player.equipment[slot] = None
                    player.inventory.append(item)
                    await player.send(f"You remove {item.short_desc}.")
                    removed_count += 1

            if removed_count > 0:
                await player.room.send_to_room(
                    f"{player.name} removes several items.",
                    exclude=[player]
                )
            else:
                await player.send("You're not wearing anything to remove.")
            return

        # Find specific item in equipment
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

        # Innkeeper NPCs
        elif npc.special == 'innkeeper':
            if 'rent' in message or 'room' in message or 'stay' in message:
                rent_cost = max(20, player.level * 10)
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'A room costs {rent_cost} gold per night. Type RENT to secure a room and rest.'{c['reset']}")
            elif 'hello' in message or 'hi' in message or 'greet' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'Welcome to The Prancing Pony! Looking for a room to rest? Just ask about rent.'{c['reset']}")
            elif 'help' in message:
                await player.send(f"{c['bright_cyan']}{npc.name} says, 'We offer safe rooms where you can rest and save your progress. Type RENT when you're ready.'{c['reset']}")

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
                    
                c = player.config.COLORS
                player.inventory.remove(item)
                food_value = getattr(item, 'food_value', 10)

                # Restore hunger based on food value
                old_hunger = player.hunger
                player.hunger = min(player.max_hunger, player.hunger + food_value)
                hunger_restored = player.hunger - old_hunger

                await player.send(f"You eat {item.short_desc}.")
                if hunger_restored > 0:
                    await player.send(f"{c['green']}You feel less hungry. (+{hunger_restored} hunger){c['reset']}")
                else:
                    await player.send(f"{c['yellow']}You are already full!{c['reset']}")

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

                c = player.config.COLORS
                # Get drink value (drinks attribute indicates how many servings remain)
                drinks_remaining = getattr(item, 'drinks', 20)
                drink_value = 3  # Each drink restores 3 hours of thirst

                if drinks_remaining > 0:
                    # Consume one serving
                    item.drinks = drinks_remaining - 1

                    # Restore thirst
                    old_thirst = player.thirst
                    player.thirst = min(player.max_thirst, player.thirst + drink_value)
                    thirst_restored = player.thirst - old_thirst

                    liquid = getattr(item, 'liquid', 'water')
                    await player.send(f"You drink {liquid} from {item.short_desc}.")
                    if thirst_restored > 0:
                        await player.send(f"{c['cyan']}You feel less thirsty. (+{thirst_restored} thirst){c['reset']}")
                    else:
                        await player.send(f"{c['yellow']}You can't drink any more!{c['reset']}")

                    # Remove empty container
                    if item.drinks <= 0:
                        await player.send(f"{c['white']}{item.short_desc} is now empty.{c['reset']}")
                        player.inventory.remove(item)
                else:
                    await player.send(f"{item.short_desc} is empty!")

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
                c = player.config.COLORS
                await player.send(f"You quaff {item.short_desc}.")

                # Apply potion effects
                if hasattr(item, 'spell_effects'):
                    from spells import SpellHandler
                    for spell in item.spell_effects:
                        await SpellHandler.apply_spell_effect(player, player, spell)
                elif hasattr(item, 'potion_spell'):
                    # Handle cure potions
                    from affects import AffectManager
                    spell_name = item.potion_spell

                    if spell_name == 'cure_poison':
                        # Remove poison effect
                        if AffectManager.remove_affect_by_name(player, 'poison'):
                            await player.send(f"{c['green']}The antidote neutralizes the poison in your blood!{c['reset']}")
                        else:
                            await player.send(f"{c['yellow']}You feel refreshed, but you weren't poisoned.{c['reset']}")

                    elif spell_name == 'cure_blindness':
                        # Remove blindness
                        if AffectManager.remove_affect_by_name(player, 'blindness'):
                            await player.send(f"{c['white']}Your vision clears!{c['reset']}")
                        else:
                            await player.send(f"{c['yellow']}You feel refreshed, but your vision was fine.{c['reset']}")

                    elif spell_name == 'cure_silence':
                        # Remove silence
                        if AffectManager.remove_affect_by_name(player, 'silence'):
                            await player.send(f"{c['magenta']}You can speak again!{c['reset']}")
                        else:
                            await player.send(f"{c['yellow']}You feel refreshed, but you weren't silenced.{c['reset']}")

                    elif spell_name == 'restoration':
                        # Remove stat debuffs
                        removed_any = False
                        if AffectManager.remove_affect_by_name(player, 'weakened'):
                            await player.send(f"{c['red']}Your strength returns!{c['reset']}")
                            removed_any = True
                        if AffectManager.remove_affect_by_name(player, 'slowed'):
                            await player.send(f"{c['blue']}Your movements quicken!{c['reset']}")
                            removed_any = True
                        if not removed_any:
                            await player.send(f"{c['yellow']}You feel refreshed, but had no debuffs.{c['reset']}")

                    elif spell_name == 'panacea':
                        # Remove all debuffs
                        removed = []
                        if AffectManager.remove_affect_by_name(player, 'poison'):
                            removed.append('poison')
                        if AffectManager.remove_affect_by_name(player, 'blindness'):
                            removed.append('blindness')
                        if AffectManager.remove_affect_by_name(player, 'silence'):
                            removed.append('silence')
                        if AffectManager.remove_affect_by_name(player, 'weakened'):
                            removed.append('weakness')
                        if AffectManager.remove_affect_by_name(player, 'slowed'):
                            removed.append('slowness')

                        if removed:
                            await player.send(f"{c['bright_yellow']}The panacea purges all ailments from your body!{c['reset']}")
                            await player.send(f"{c['cyan']}Cured: {', '.join(removed)}{c['reset']}")
                        else:
                            await player.send(f"{c['yellow']}You feel incredibly refreshed!{c['reset']}")

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

        elif subcommand == 'list' or subcommand == 'available':
            # Show available quests from NPCs in the current room
            from quests import QuestManager, QUEST_DEFINITIONS

            if not player.room:
                await player.send("You need to be somewhere to find quests!")
                return

            found_quests = False
            for npc in player.room.npcs:
                vnum = getattr(npc, 'vnum', 0)
                available = QuestManager.get_available_quests(player, vnum)
                if available:
                    if not found_quests:
                        await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
                        await player.send(f"{c['cyan']}║{c['bright_yellow']} Available Quests{c['cyan']}                                             ║{c['reset']}")
                        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")
                        found_quests = True

                    await player.send(f"{c['bright_cyan']}From {npc.name}:{c['reset']}")
                    for quest_id in available:
                        quest_def = QUEST_DEFINITIONS[quest_id]
                        lvl_range = f"[L{quest_def['level_min']}-{quest_def['level_max']}]"
                        repeatable = " (Repeatable)" if quest_def.get('repeatable') else ""
                        await player.send(f"  {c['yellow']}{quest_id}{c['reset']}: {quest_def['name']} {lvl_range}{repeatable}")
                    await player.send("")

            if not found_quests:
                await player.send(f"{c['yellow']}No quests available from NPCs in this room.{c['reset']}")
                await player.send(f"{c['white']}Try visiting the Mayor in Midgaard or Captain Stolar at the docks.{c['reset']}")
            else:
                await player.send(f"{c['white']}Use 'quest accept <quest_id>' to accept a quest.{c['reset']}\r\n")

        elif subcommand == 'info':
            # Show details about a specific quest
            from quests import QUEST_DEFINITIONS

            if len(args) < 2:
                await player.send("Usage: quest info <quest_id>")
                return

            quest_id = args[1]
            if quest_id not in QUEST_DEFINITIONS:
                await player.send(f"Unknown quest: {quest_id}")
                return

            quest_def = QUEST_DEFINITIONS[quest_id]
            await player.send(f"\r\n{c['bright_yellow']}Quest: {quest_def['name']}{c['reset']}")
            await player.send(f"{c['white']}{quest_def['description']}{c['reset']}\r\n")
            await player.send(f"{c['cyan']}Level Range:{c['reset']} {quest_def['level_min']}-{quest_def['level_max']}")
            await player.send(f"{c['cyan']}Type:{c['reset']} {quest_def['type'].title()}")
            await player.send(f"{c['cyan']}Repeatable:{c['reset']} {'Yes' if quest_def.get('repeatable') else 'No'}\r\n")

            await player.send(f"{c['cyan']}Objectives:{c['reset']}")
            for obj in quest_def['objectives']:
                await player.send(f"  - {obj['description']} (x{obj['required']})")

            await player.send(f"\r\n{c['green']}Rewards:{c['reset']}")
            if quest_def['rewards'].get('exp'):
                await player.send(f"  - {quest_def['rewards']['exp']} experience")
            if quest_def['rewards'].get('gold'):
                await player.send(f"  - {quest_def['rewards']['gold']} gold")
            await player.send("")

        else:
            await player.send(f"Unknown quest command: {subcommand}")
            await player.send("Usage: quest [list|accept|abandon|complete|log|info]")

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

        # Check for door - handle "door north", "door n", or just "north"
        direction = None

        # Remove "door" from the target name if present
        if target_name.startswith('door '):
            target_name = target_name[5:].strip()

        for dir_name in player.config.DIRECTIONS.keys():
            if target_name == dir_name or target_name in dir_name:
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

        # Update the other side of the door
        next_room = exit_data.get('room')
        if next_room:
            opposite_dir = player.config.DIRECTIONS[direction]['opposite']
            if opposite_dir in next_room.exits and 'door' in next_room.exits[opposite_dir]:
                next_room.exits[opposite_dir]['door']['state'] = 'open'

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

        # Check for door - handle "door north", "door n", or just "north"
        direction = None

        # Remove "door" from the target name if present
        if target_name.startswith('door '):
            target_name = target_name[5:].strip()

        for dir_name in player.config.DIRECTIONS.keys():
            if target_name == dir_name or target_name in dir_name:
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

        # Update the other side of the door
        next_room = exit_data.get('room')
        if next_room:
            opposite_dir = player.config.DIRECTIONS[direction]['opposite']
            if opposite_dir in next_room.exits and 'door' in next_room.exits[opposite_dir]:
                next_room.exits[opposite_dir]['door']['state'] = 'closed'

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

        # Check for door - handle "door north", "door n", or just "north"
        direction = None

        # Remove "door" from the target name if present
        if target_name.startswith('door '):
            target_name = target_name[5:].strip()

        for dir_name in player.config.DIRECTIONS.keys():
            if target_name == dir_name or target_name in dir_name:
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

        # Update the other side of the door
        next_room = exit_data.get('room')
        if next_room:
            opposite_dir = player.config.DIRECTIONS[direction]['opposite']
            if opposite_dir in next_room.exits and 'door' in next_room.exits[opposite_dir]:
                next_room.exits[opposite_dir]['door']['locked'] = True

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

        # Check for door - handle "door north", "door n", or just "north"
        direction = None

        # Remove "door" from the target name if present
        if target_name.startswith('door '):
            target_name = target_name[5:].strip()

        for dir_name in player.config.DIRECTIONS.keys():
            if target_name == dir_name or target_name in dir_name:
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

        # Update the other side of the door
        next_room = exit_data.get('room')
        if next_room:
            opposite_dir = player.config.DIRECTIONS[direction]['opposite']
            if opposite_dir in next_room.exits and 'door' in next_room.exits[opposite_dir]:
                next_room.exits[opposite_dir]['door']['locked'] = False

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

        # Check for door - handle "door north", "door n", or just "north"
        direction = None

        # Remove "door" from the target name if present
        if target_name.startswith('door '):
            target_name = target_name[5:].strip()

        for dir_name in player.config.DIRECTIONS.keys():
            if target_name == dir_name or target_name in dir_name:
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

    @classmethod
    async def cmd_show(cls, player: 'Player', args: List[str]):
        """Show detailed stats of an item in the shop. Usage: show <item>"""
        from shops import ShopManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Show what? Use 'list' to see available items.{c['reset']}")
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

        item_name = ' '.join(args).lower()

        # Find the item in shop inventory
        item = None
        for shop_item in shop.inventory:
            if item_name in shop_item.name.lower() or item_name in shop_item.short_desc.lower():
                item = shop_item
                break

        if not item:
            await player.send(f"{c['red']}The shopkeeper doesn't have '{item_name}' for sale.{c['reset']}")
            return

        # Calculate price
        price = int(item.cost * shop.markup)

        # Show detailed item information
        await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']} {shopkeeper.name} shows you:{c['cyan']}{'':>36}║{c['reset']}")
        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

        await player.send(f"{c['bright_white']}{item.short_desc.capitalize()}{c['reset']}")
        await player.send(f"{c['white']}{item.description}{c['reset']}\r\n")

        # Item type
        await player.send(f"{c['yellow']}Type: {item.item_type.capitalize()}{c['reset']}")

        # Weapon stats
        if item.item_type == 'weapon':
            await player.send(f"{c['red']}Damage: {item.damage_dice} ({item.weapon_type}){c['reset']}")
            if hasattr(item, 'weapon_class'):
                await player.send(f"{c['yellow']}Weapon Class: {item.weapon_class}{c['reset']}")

        # Armor stats
        elif item.item_type == 'armor':
            await player.send(f"{c['blue']}Armor: {item.armor} AC{c['reset']}")
            if item.wear_slot:
                await player.send(f"{c['cyan']}Worn on: {item.wear_slot}{c['reset']}")

        # Poison stats
        elif item.item_type == 'poison':
            if hasattr(item, 'poison_type'):
                poison_config = player.config.POISON_TYPES.get(item.poison_type, {})
                await player.send(f"{c['green']}Effect: {poison_config.get('effect', 'unknown').capitalize()}{c['reset']}")
                if 'duration' in poison_config:
                    await player.send(f"{c['green']}Duration: {poison_config['duration']} ticks{c['reset']}")
                if 'damage' in poison_config:
                    await player.send(f"{c['red']}Damage: {poison_config['damage']} per tick{c['reset']}")

        # Potion stats
        elif item.item_type == 'potion':
            if hasattr(item, 'potion_spell'):
                await player.send(f"{c['magenta']}Effect: {item.potion_spell.replace('_', ' ').title()}{c['reset']}")

        # Magical affects
        if hasattr(item, 'affects') and item.affects:
            await player.send(f"\r\n{c['bright_magenta']}Magical Properties:{c['reset']}")
            for affect in item.affects:
                sign = '+' if affect['value'] > 0 else ''
                await player.send(f"  {c['magenta']}{affect['type'].capitalize()}: {sign}{affect['value']}{c['reset']}")

        # Weight and value
        await player.send(f"\r\n{c['white']}Weight: {item.weight} lbs{c['reset']}")
        await player.send(f"{c['yellow']}Price: {price} gold{c['reset']}")

    @classmethod
    async def cmd_compare(cls, player: 'Player', args: List[str]):
        """Compare a shop item to your equipped item. Usage: compare <item>"""
        from shops import ShopManager

        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Compare what? Use 'list' to see available items.{c['reset']}")
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

        item_name = ' '.join(args).lower()

        # Find the item in shop inventory
        shop_item = None
        for item in shop.inventory:
            if item_name in item.name.lower() or item_name in item.short_desc.lower():
                shop_item = item
                break

        if not shop_item:
            await player.send(f"{c['red']}The shopkeeper doesn't have '{item_name}' for sale.{c['reset']}")
            return

        # Determine what slot this item uses
        equipped_item = None
        if shop_item.item_type == 'weapon':
            equipped_item = player.equipment.get('wield')
        elif shop_item.item_type == 'armor' and shop_item.wear_slot:
            equipped_item = player.equipment.get(shop_item.wear_slot)

        # Show comparison
        await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']} Comparing Items:{c['cyan']}{'':>45}║{c['reset']}")
        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

        if not equipped_item:
            await player.send(f"{c['yellow']}You have nothing equipped in that slot.{c['reset']}\r\n")
            await player.send(f"{c['white']}Shop Item:{c['reset']} {shop_item.short_desc}")
            if shop_item.item_type == 'weapon':
                await player.send(f"  {c['red']}Damage: {shop_item.damage_dice}{c['reset']}")
            elif shop_item.item_type == 'armor':
                await player.send(f"  {c['blue']}Armor: {shop_item.armor} AC{c['reset']}")
            return

        # Compare equipped vs shop item
        await player.send(f"{c['bright_cyan']}Currently Equipped:{c['reset']} {equipped_item.short_desc}")
        await player.send(f"{c['bright_yellow']}Shop Item:{c['reset']} {shop_item.short_desc}\r\n")

        if shop_item.item_type == 'weapon':
            # Parse damage dice to compare
            def parse_damage(dice_str):
                # Parse "2d6" -> avg = 2 * 3.5 = 7
                try:
                    num, sides = dice_str.lower().split('d')
                    return int(num) * (int(sides) + 1) / 2
                except:
                    return 0

            equipped_dmg = parse_damage(equipped_item.damage_dice if hasattr(equipped_item, 'damage_dice') else '1d4')
            shop_dmg = parse_damage(shop_item.damage_dice)

            diff = shop_dmg - equipped_dmg
            if diff > 0:
                await player.send(f"{c['red']}Damage: {equipped_item.damage_dice} → {shop_item.damage_dice} {c['green']}(+{diff:.1f} avg){c['reset']}")
            elif diff < 0:
                await player.send(f"{c['red']}Damage: {equipped_item.damage_dice} → {shop_item.damage_dice} {c['red']}({diff:.1f} avg){c['reset']}")
            else:
                await player.send(f"{c['red']}Damage: {equipped_item.damage_dice} → {shop_item.damage_dice} {c['yellow']}(same){c['reset']}")

        elif shop_item.item_type == 'armor':
            equipped_ac = equipped_item.armor if hasattr(equipped_item, 'armor') else 0
            shop_ac = shop_item.armor

            diff = shop_ac - equipped_ac
            if diff > 0:
                await player.send(f"{c['blue']}Armor: {equipped_ac} AC → {shop_ac} AC {c['green']}(+{diff}){c['reset']}")
            elif diff < 0:
                await player.send(f"{c['blue']}Armor: {equipped_ac} AC → {shop_ac} AC {c['red']}({diff}){c['reset']}")
            else:
                await player.send(f"{c['blue']}Armor: {equipped_ac} AC → {shop_ac} AC {c['yellow']}(same){c['reset']}")

        # Compare magical affects
        if hasattr(shop_item, 'affects') and shop_item.affects:
            await player.send(f"\r\n{c['bright_magenta']}Shop Item Magical Properties:{c['reset']}")
            for affect in shop_item.affects:
                sign = '+' if affect['value'] > 0 else ''
                await player.send(f"  {c['magenta']}{affect['type'].capitalize()}: {sign}{affect['value']}{c['reset']}")

        if hasattr(equipped_item, 'affects') and equipped_item.affects:
            await player.send(f"\r\n{c['bright_cyan']}Current Item Magical Properties:{c['reset']}")
            for affect in equipped_item.affects:
                sign = '+' if affect['value'] > 0 else ''
                await player.send(f"  {c['cyan']}{affect['type'].capitalize()}: {sign}{affect['value']}{c['reset']}")

    @classmethod
    async def cmd_examine(cls, player: 'Player', args: List[str]):
        """Examine an item in your inventory or equipment. Usage: examine <item>"""
        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Examine what? Specify an item in your inventory or equipment.{c['reset']}")
            return

        item_name = ' '.join(args).lower()

        # Search in equipment first
        item = None
        item_location = None

        for slot, equipped in player.equipment.items():
            if equipped and (item_name in equipped.name.lower() or item_name in equipped.short_desc.lower()):
                item = equipped
                item_location = f"worn on {slot}"
                break

        # Search in inventory if not found
        if not item:
            for inv_item in player.inventory:
                if item_name in inv_item.name.lower() or item_name in inv_item.short_desc.lower():
                    item = inv_item
                    item_location = "in inventory"
                    break

        if not item:
            await player.send(f"{c['red']}You don't have '{item_name}'.{c['reset']}")
            return

        # Display item details
        await player.send(f"\r\n{c['cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']} Examining: {item.short_desc:<46}{c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")

        await player.send(f"{c['white']}{item.description}{c['reset']}\r\n")

        await player.send(f"{c['yellow']}Type: {item.item_type.capitalize()}{c['reset']}")
        await player.send(f"{c['cyan']}Location: {item_location.capitalize()}{c['reset']}")

        # Weapon stats
        if item.item_type == 'weapon':
            await player.send(f"{c['red']}Damage: {item.damage_dice} ({item.weapon_type}){c['reset']}")
            if hasattr(item, 'envenomed') and item.envenomed:
                poison_type = getattr(item, 'poison_type', 'venom')
                charges = getattr(item, 'envenom_charges', 0)
                await player.send(f"{c['green']}Envenomed with {poison_type} ({charges} charges remaining){c['reset']}")

        # Armor stats
        elif item.item_type == 'armor':
            await player.send(f"{c['blue']}Armor: {item.armor} AC{c['reset']}")
            if item.wear_slot:
                await player.send(f"{c['cyan']}Slot: {item.wear_slot}{c['reset']}")

        # Poison stats
        elif item.item_type == 'poison':
            if hasattr(item, 'poison_type'):
                poison_config = player.config.POISON_TYPES.get(item.poison_type, {})
                await player.send(f"{c['green']}Poison Type: {poison_config.get('name', 'Unknown')}{c['reset']}")
                await player.send(f"{c['green']}Effect: {poison_config.get('effect', 'unknown').capitalize()}{c['reset']}")

        # Potion stats
        elif item.item_type == 'potion':
            if hasattr(item, 'potion_spell'):
                await player.send(f"{c['magenta']}Effect: {item.potion_spell.replace('_', ' ').title()}{c['reset']}")

        # Container stats
        elif item.item_type == 'container':
            status = 'closed' if item.is_closed else 'open'
            locked = ' (locked)' if item.is_locked else ''
            await player.send(f"{c['yellow']}Container: {status}{locked}{c['reset']}")
            if item.contents:
                await player.send(f"{c['yellow']}Contains: {len(item.contents)} item(s){c['reset']}")

        # Magical affects
        if hasattr(item, 'affects') and item.affects:
            await player.send(f"\r\n{c['bright_magenta']}Magical Properties:{c['reset']}")
            for affect in item.affects:
                sign = '+' if affect['value'] > 0 else ''
                await player.send(f"  {c['magenta']}{affect['type'].capitalize()}: {sign}{affect['value']}{c['reset']}")

        # Weight and value
        await player.send(f"\r\n{c['white']}Weight: {item.weight} lbs{c['reset']}")
        if hasattr(item, 'cost'):
            await player.send(f"{c['yellow']}Value: {item.cost} gold{c['reset']}")

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
    async def cmd_save(cls, player: 'Player', args: List[str]):
        """Save your character."""
        await player.save()
        await player.send("Character saved.")
        
    @classmethod
    async def cmd_rent(cls, player: 'Player', args: List[str]):
        """Rent a room at the Inn to save your character and quit safely."""
        c = player.config.COLORS

        # Check if player is in combat
        if player.is_fighting:
            await player.send(f"{c['red']}You can't rent while fighting! Try to flee first.{c['reset']}")
            return

        # Check if player is at the Inn
        inn_rooms = [3030, 3031, 3032, 3033, 3034]  # Inn common room and rental rooms
        if not player.room or player.room.vnum not in inn_rooms:
            await player.send(f"{c['yellow']}You must be at The Prancing Pony Inn to rent a room.{c['reset']}")
            return

        # Calculate rent cost (level * 10 gold per day, minimum 20 gold)
        rent_cost = max(20, player.level * 10)

        # Check if player can afford it
        if player.gold < rent_cost:
            await player.send(f"{c['red']}You need {rent_cost} gold to rent a room, but you only have {player.gold} gold.{c['reset']}")
            await player.send(f"{c['yellow']}The innkeeper says, 'Come back when you have enough coin, friend.'{c['reset']}")
            return

        # Deduct rent cost
        player.gold -= rent_cost

        # Save the player
        await player.save()

        # Send messages
        await player.send(f"{c['bright_yellow']}You pay {rent_cost} gold to the innkeeper.{c['reset']}")
        await player.send(f"{c['bright_cyan']}The innkeeper says, 'Rest well, {player.name}. Your room will be ready when you return.'{c['reset']}")
        await player.send(f"{c['bright_green']}You settle into your room and drift off to sleep...{c['reset']}")
        await player.send(f"{c['white']}Your character has been saved.{c['reset']}")

        if player.room:
            await player.room.send_to_room(
                f"{player.name} rents a room and retires for the evening.",
                exclude=[player]
            )

        # Disconnect
        if player.connection:
            await player.connection.disconnect()

    # ==================== MOUNTS ====================

    @classmethod
    async def cmd_mount(cls, player: 'Player', args: List[str]):
        """Mount a creature."""
        c = player.config.COLORS

        if player.mount:
            await player.send(f"{c['yellow']}You are already mounted!{c['reset']}")
            return

        if not args:
            await player.send("Mount what?")
            return

        mount_name = ' '.join(args).lower()

        # Find mount in room (must be your own mount or a tame creature)
        mount = None
        from mobs import Mobile
        for char in player.room.characters:
            if isinstance(char, Mobile) and mount_name in char.name.lower():
                # Check if it's a mountable creature
                if hasattr(char, 'is_mount') and char.is_mount:
                    mount = char
                    break

        if not mount:
            await player.send(f"{c['yellow']}There's no mount here by that name.{c['reset']}")
            return

        # Mount the creature
        player.mount = mount
        await player.send(f"{c['green']}You mount {mount.name}.{c['reset']}")
        await player.room.send_to_room(
            f"{player.name} mounts {mount.name}.",
            exclude=[player]
        )

    @classmethod
    async def cmd_dismount(cls, player: 'Player', args: List[str]):
        """Dismount from your current mount."""
        c = player.config.COLORS

        if not player.mount:
            await player.send(f"{c['yellow']}You are not mounted.{c['reset']}")
            return

        mount_name = player.mount.name
        player.mount = None

        await player.send(f"{c['green']}You dismount from {mount_name}.{c['reset']}")
        await player.room.send_to_room(
            f"{player.name} dismounts from {mount_name}.",
            exclude=[player]
        )

    @classmethod
    async def cmd_mounts(cls, player: 'Player', args: List[str]):
        """List your owned mounts."""
        c = player.config.COLORS

        if not player.owned_mounts:
            await player.send(f"{c['yellow']}You don't own any mounts.{c['reset']}")
            await player.send(f"{c['cyan']}Visit the stables to purchase a mount!{c['reset']}")
            return

        await player.send(f"{c['cyan']}╔════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']}         Your Mounts                  {c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠════════════════════════════════════════╣{c['reset']}")

        for mount_vnum in player.owned_mounts:
            # In a real implementation, you'd load mount data from vnums
            await player.send(f"{c['cyan']}║ {c['yellow']}Mount #{mount_vnum:<30}{c['cyan']}║{c['reset']}")

        await player.send(f"{c['cyan']}╚════════════════════════════════════════╝{c['reset']}")

    # ==================== RENT/STORAGE ====================

    @classmethod
    async def cmd_storage(cls, player: 'Player', args: List[str]):
        """View items in your storage locker."""
        c = player.config.COLORS

        if not player.storage:
            await player.send(f"{c['yellow']}Your storage is empty.{c['reset']}")
            return

        storage_room = player.world.get_room(player.storage_location) if player.storage_location else None
        location_name = storage_room.name if storage_room else "Unknown Location"

        await player.send(f"{c['cyan']}╔════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['cyan']}║{c['bright_yellow']}     Your Storage at {location_name:<20}{c['cyan']}║{c['reset']}")
        await player.send(f"{c['cyan']}╠════════════════════════════════════════════════╣{c['reset']}")

        for item in player.storage:
            await player.send(f"{c['cyan']}║ {c['yellow']}{item.short_desc:<44}{c['cyan']}║{c['reset']}")

        await player.send(f"{c['cyan']}╚════════════════════════════════════════════════╝{c['reset']}")
        await player.send(f"{c['white']}Total: {len(player.storage)} items{c['reset']}")

    @classmethod
    async def cmd_store(cls, player: 'Player', args: List[str]):
        """Store an item in your inn locker."""
        c = player.config.COLORS

        # Check if at an inn
        if not player.room:
            await player.send(f"{c['red']}You need to be at an inn to use storage!{c['reset']}")
            return

        # Check for innkeeper in room
        has_innkeeper = False
        from mobs import Mobile
        for char in player.room.characters:
            if isinstance(char, Mobile) and char.special == 'innkeeper':
                has_innkeeper = True
                break

        if not has_innkeeper:
            await player.send(f"{c['red']}You must be at an inn with an innkeeper to access storage!{c['reset']}")
            return

        if not args:
            await player.send(f"Store what item?")
            return

        item_name = ' '.join(args).lower()

        # Find item in inventory
        item = None
        for inv_item in player.inventory:
            if item_name in inv_item.name.lower():
                item = inv_item
                break

        if not item:
            await player.send(f"{c['yellow']}You don't have that item.{c['reset']}")
            return

        # Store the item
        player.inventory.remove(item)
        player.storage.append(item)

        # Set storage location if first time
        if not player.storage_location:
            player.storage_location = player.room.vnum

        await player.send(f"{c['green']}You store {item.short_desc} in your locker.{c['reset']}")

    @classmethod
    async def cmd_retrieve(cls, player: 'Player', args: List[str]):
        """Retrieve an item from your inn locker."""
        c = player.config.COLORS

        # Check if at correct inn
        if not player.room:
            await player.send(f"{c['red']}You need to be at an inn to access storage!{c['reset']}")
            return

        # Check for innkeeper in room
        has_innkeeper = False
        from mobs import Mobile
        for char in player.room.characters:
            if isinstance(char, Mobile) and char.special == 'innkeeper':
                has_innkeeper = True
                break

        if not has_innkeeper:
            await player.send(f"{c['red']}You must be at an inn with an innkeeper to access storage!{c['reset']}")
            return

        if not player.storage:
            await player.send(f"{c['yellow']}Your storage is empty.{c['reset']}")
            return

        # Check if at the right inn
        if player.storage_location and player.room.vnum != player.storage_location:
            storage_room = player.world.get_room(player.storage_location)
            location_name = storage_room.name if storage_room else f"room {player.storage_location}"
            await player.send(f"{c['yellow']}Your storage is located at {location_name}.{c['reset']}")
            await player.send(f"{c['yellow']}You must return there to access it.{c['reset']}")
            return

        if not args:
            await player.send(f"Retrieve what item?")
            return

        item_name = ' '.join(args).lower()

        # Find item in storage
        item = None
        for storage_item in player.storage:
            if item_name in storage_item.name.lower():
                item = storage_item
                break

        if not item:
            await player.send(f"{c['yellow']}That item is not in your storage.{c['reset']}")
            return

        # Retrieve the item
        player.storage.remove(item)
        player.inventory.append(item)

        await player.send(f"{c['green']}You retrieve {item.short_desc} from your locker.{c['reset']}")

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

    @classmethod
    async def cmd_alias(cls, player: 'Player', args: List[str]):
        """Create, view, or remove personal command aliases.

        Usage:
            alias              - List all your aliases
            alias <word>       - Show what <word> is aliased to
            alias <word> <cmd> - Create alias <word> for <cmd>
            unalias <word>     - Remove an alias
        """
        c = player.config.COLORS

        if not args:
            # List all aliases
            if not player.custom_aliases:
                await player.send("You have no aliases defined.")
            else:
                await player.send(f"{c['cyan']}Your Aliases:{c['reset']}")
                for alias, command in sorted(player.custom_aliases.items()):
                    await player.send(f"  {c['bright_green']}{alias}{c['white']} -> {c['bright_yellow']}{command}{c['reset']}")
        elif len(args) == 1:
            # Show specific alias
            alias_word = args[0].lower()
            if alias_word in player.custom_aliases:
                await player.send(f"{c['bright_green']}{alias_word}{c['white']} is aliased to: {c['bright_yellow']}{player.custom_aliases[alias_word]}{c['reset']}")
            else:
                await player.send(f"You have no alias for '{alias_word}'.")
        else:
            # Create new alias
            alias_word = args[0].lower()
            command = ' '.join(args[1:])
            player.custom_aliases[alias_word] = command
            await player.send(f"{c['bright_green']}Alias created:{c['white']} {alias_word} -> {command}{c['reset']}")

    @classmethod
    async def cmd_unalias(cls, player: 'Player', args: List[str]):
        """Remove a personal alias."""
        c = player.config.COLORS

        if not args:
            await player.send("Usage: unalias <word>")
            return

        alias_word = args[0].lower()
        if alias_word in player.custom_aliases:
            del player.custom_aliases[alias_word]
            await player.send(f"{c['bright_green']}Alias '{alias_word}' removed.{c['reset']}")
        else:
            await player.send(f"You have no alias for '{alias_word}'.")

    @classmethod
    async def cmd_autoloot(cls, player: 'Player', args: List[str]):
        """Toggle automatic looting of items from corpses.

        Usage:
            autoloot          - Toggle autoloot on/off
            autoloot on       - Turn autoloot on
            autoloot off      - Turn autoloot off
            autoloot gold     - Toggle gold autoloot on/off
            autoloot gold on  - Turn gold autoloot on
            autoloot gold off - Turn gold autoloot off
        """
        c = player.config.COLORS

        # Handle autoloot gold
        if args and args[0].lower() == 'gold':
            if len(args) > 1:
                setting = args[1].lower()
                if setting == 'on':
                    player.autoloot_gold = True
                    await player.send(f"{c['bright_green']}Autoloot gold is now ON. You will automatically loot gold from corpses.{c['reset']}")
                elif setting == 'off':
                    player.autoloot_gold = False
                    await player.send(f"{c['yellow']}Autoloot gold is now OFF. You must manually loot gold from corpses.{c['reset']}")
                else:
                    await player.send(f"{c['red']}Usage: autoloot gold [on|off]{c['reset']}")
            else:
                # Toggle
                player.autoloot_gold = not player.autoloot_gold
                status = f"{c['bright_green']}ON{c['reset']}" if player.autoloot_gold else f"{c['red']}OFF{c['reset']}"
                await player.send(f"Autoloot gold is now {status}.")
        # Handle regular autoloot
        elif args:
            setting = args[0].lower()
            if setting == 'on':
                player.autoloot = True
                await player.send(f"{c['bright_green']}Autoloot is now ON. You will automatically loot all items from corpses.{c['reset']}")
            elif setting == 'off':
                player.autoloot = False
                await player.send(f"{c['yellow']}Autoloot is now OFF. You must manually loot items from corpses.{c['reset']}")
            else:
                await player.send(f"{c['red']}Usage: autoloot [on|off] or autoloot gold [on|off]{c['reset']}")
        else:
            # Toggle
            player.autoloot = not player.autoloot
            status = f"{c['bright_green']}ON{c['reset']}" if player.autoloot else f"{c['red']}OFF{c['reset']}"
            await player.send(f"Autoloot is now {status}.")

        # Show current status
        gold_status = f"{c['bright_green']}ON{c['reset']}" if player.autoloot_gold else f"{c['red']}OFF{c['reset']}"
        item_status = f"{c['bright_green']}ON{c['reset']}" if player.autoloot else f"{c['red']}OFF{c['reset']}"
        await player.send(f"{c['cyan']}Current settings: Autoloot Items: {item_status}, Autoloot Gold: {gold_status}{c['reset']}")

    @classmethod
    async def cmd_recall(cls, player: 'Player', args: List[str]):
        """Recall to your recall point (temple).

        Usage:
            recall     - Teleport to your recall point
            recall set - Set current location as recall point
        """
        c = player.config.COLORS

        # Check if setting recall point
        if args and args[0].lower() == 'set':
            if not player.room:
                await player.send(f"{c['red']}You are nowhere!{c['reset']}")
                return

            # Can't set recall in certain rooms
            if 'no_recall' in player.room.flags:
                await player.send(f"{c['red']}You cannot set your recall point here!{c['reset']}")
                return

            player.recall_point = player.room.vnum
            await player.send(f"{c['bright_cyan']}Recall point set to: {player.room.name}{c['reset']}")
            await player.send(f"{c['yellow']}You can now use 'recall' to return here from anywhere.{c['reset']}")
            return

        # Can't recall while fighting
        if player.is_fighting:
            await player.send(f"{c['red']}You can't recall while fighting!{c['reset']}")
            return

        # Can't recall from no_recall rooms
        if player.room and 'no_recall' in player.room.flags:
            await player.send(f"{c['red']}Powerful magic prevents you from recalling!{c['reset']}")
            return

        # Get recall point (default to temple at 3001)
        recall_vnum = getattr(player, 'recall_point', 3001)

        # Find recall room
        recall_room = player.world.rooms.get(recall_vnum)
        if not recall_room:
            # Fallback to temple if custom recall point doesn't exist
            recall_room = player.world.rooms.get(3001)
            if not recall_room:
                await player.send(f"{c['red']}Your recall point no longer exists!{c['reset']}")
                return

        # Already at recall point?
        if player.room == recall_room:
            await player.send(f"{c['yellow']}You are already at your recall point!{c['reset']}")
            return

        # Recall!
        old_room = player.room

        # Leave old room
        if old_room:
            await old_room.send_to_room(
                f"{c['bright_cyan']}{player.name} disappears in a flash of light!{c['reset']}",
                exclude=[player]
            )
            old_room.characters.remove(player)

        # Enter recall room
        player.room = recall_room
        recall_room.characters.append(player)

        await player.send(f"{c['bright_cyan']}You recall to safety!{c['reset']}")
        await player.send("")

        # Show room
        await recall_room.show_to(player)

        # Announce arrival
        await recall_room.send_to_room(
            f"{c['bright_cyan']}{player.name} appears in a flash of light!{c['reset']}",
            exclude=[player]
        )

    @classmethod
    async def cmd_goto(cls, player: 'Player', args: List[str]):
        """Teleport to a room or zone (testing command).

        Usage:
            goto <vnum>     - Go to room vnum (e.g. goto 3001)
            goto <zone>     - Go to zone entrance (e.g. goto 30)
        """
        c = player.config.COLORS

        if not args:
            await player.send(f"{c['yellow']}Usage: goto <room_vnum> or goto <zone_number>{c['reset']}")
            await player.send(f"{c['cyan']}Examples:{c['reset']}")
            await player.send(f"{c['white']}  goto 3001    {c['yellow']}# Go to Temple of Midgaard{c['reset']}")
            await player.send(f"{c['white']}  goto 30      {c['yellow']}# Go to zone 30 entrance{c['reset']}")
            await player.send(f"{c['white']}  goto 80      {c['yellow']}# Go to Dragon's Domain{c['reset']}")
            return

        try:
            target_vnum = int(args[0])
        except ValueError:
            await player.send(f"{c['red']}Invalid room/zone number. Must be a number.{c['reset']}")
            return

        # Check if it's a zone number (under 100) and convert to first room in zone
        if target_vnum < 100:
            # It's a zone number - find first room in that zone
            zone_num = target_vnum
            zone = player.world.zones.get(zone_num)
            if not zone:
                await player.send(f"{c['red']}Zone {zone_num} does not exist.{c['reset']}")
                return

            # Get first room in zone
            if not zone.rooms:
                await player.send(f"{c['red']}Zone {zone_num} has no rooms!{c['reset']}")
                return

            # Find the lowest vnum room in the zone
            target_vnum = min(zone.rooms.keys())
            await player.send(f"{c['cyan']}Teleporting to {zone.name} (room {target_vnum})...{c['reset']}")

        # Find the target room
        target_room = player.world.rooms.get(target_vnum)
        if not target_room:
            await player.send(f"{c['red']}Room {target_vnum} does not exist.{c['reset']}")
            await player.send(f"{c['yellow']}Tip: Use 'map' to see available zones.{c['reset']}")
            return

        # Already there?
        if player.room == target_room:
            await player.send(f"{c['yellow']}You are already in that room!{c['reset']}")
            return

        # Teleport!
        old_room = player.room

        # Leave old room
        if old_room:
            await old_room.send_to_room(
                f"{c['bright_magenta']}{player.name} vanishes in a puff of smoke!{c['reset']}",
                exclude=[player]
            )
            old_room.characters.remove(player)

        # Enter target room
        player.room = target_room
        target_room.characters.append(player)

        await player.send(f"{c['bright_magenta']}You teleport through space!{c['reset']}")
        await player.send("")

        # Show room
        await target_room.show_to(player)

        # Announce arrival
        await target_room.send_to_room(
            f"{c['bright_magenta']}{player.name} appears in a puff of smoke!{c['reset']}",
            exclude=[player]
        )

    @classmethod
    async def cmd_autorecall(cls, player: 'Player', args: List[str]):
        """Set automatic recall when HP drops below a threshold.

        Usage:
            autorecall             - Show current autorecall settings
            autorecall <hp>        - Set HP threshold (number or percentage)
            autorecall 50          - Recall when HP drops below 50
            autorecall 25%         - Recall when HP drops below 25%
            autorecall off         - Disable autorecall
        """
        c = player.config.COLORS

        if not args:
            # Show current settings
            if not hasattr(player, 'autorecall_hp') or player.autorecall_hp is None:
                await player.send(f"{c['yellow']}Autorecall is currently {c['red']}OFF{c['reset']}")
                await player.send(f"{c['cyan']}Usage: autorecall <hp> or autorecall <percentage>%{c['reset']}")
                await player.send(f"{c['cyan']}Example: autorecall 50 or autorecall 25%{c['reset']}")
            else:
                threshold = player.autorecall_hp
                if player.autorecall_is_percent:
                    percent_val = int(threshold)
                    actual_hp = int((percent_val / 100.0) * player.max_hp)
                    await player.send(f"{c['bright_green']}Autorecall is {c['bright_green']}ON{c['reset']}")
                    await player.send(f"{c['cyan']}Threshold: {percent_val}% ({actual_hp} HP){c['reset']}")
                else:
                    await player.send(f"{c['bright_green']}Autorecall is {c['bright_green']}ON{c['reset']}")
                    await player.send(f"{c['cyan']}Threshold: {int(threshold)} HP{c['reset']}")
            return

        setting = args[0].lower()

        # Turn off autorecall
        if setting in ['off', 'disable', 'no']:
            player.autorecall_hp = None
            player.autorecall_is_percent = False
            await player.send(f"{c['yellow']}Autorecall disabled.{c['reset']}")
            return

        # Parse HP threshold
        try:
            if '%' in setting:
                # Percentage
                percent = int(setting.rstrip('%'))
                if percent < 1 or percent > 99:
                    await player.send(f"{c['red']}Percentage must be between 1% and 99%.{c['reset']}")
                    return

                player.autorecall_hp = percent
                player.autorecall_is_percent = True
                actual_hp = int((percent / 100.0) * player.max_hp)
                await player.send(f"{c['bright_green']}Autorecall enabled at {percent}% HP ({actual_hp} HP).{c['reset']}")
                await player.send(f"{c['yellow']}You will automatically recall when your HP drops below this threshold.{c['reset']}")
            else:
                # Absolute HP value
                hp_value = int(setting)
                if hp_value < 1:
                    await player.send(f"{c['red']}HP threshold must be at least 1.{c['reset']}")
                    return

                if hp_value >= player.max_hp:
                    await player.send(f"{c['red']}HP threshold must be less than your maximum HP ({player.max_hp}).{c['reset']}")
                    return

                player.autorecall_hp = hp_value
                player.autorecall_is_percent = False
                await player.send(f"{c['bright_green']}Autorecall enabled at {hp_value} HP.{c['reset']}")
                await player.send(f"{c['yellow']}You will automatically recall when your HP drops below this threshold.{c['reset']}")
        except ValueError:
            await player.send(f"{c['red']}Invalid HP value. Use a number or percentage (e.g., 50 or 25%).{c['reset']}")
            return
