"""
RealmsMUD World
===============
World management - zones, rooms, mobs, objects.
"""

import random

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

from config import Config
from time_system import GameTime
from weather import Weather

logger = logging.getLogger('RealmsMUD.World')


class Room:
    """A room in the MUD world."""
    
    def __init__(self, vnum: int):
        self.vnum = vnum
        self.zone = None
        self.name = "An Empty Room"
        self.description = "You see nothing special."
        self.sector_type = "inside"
        self.flags = set()
        self.exits = {}  # direction -> {to_room, description, door, key}
        self.extra_descs = {}  # keyword -> description
        self.hidden_items = []  # [{vnum, search_difficulty, requires_light, requires_detect_magic, reveal_message}, ...]
        self.puzzles = []  # Puzzle definitions for this room
        
        # Contents
        self.characters = []  # Players and NPCs in room
        self.items = []  # Objects in room
        self.gold = 0  # Gold coins on the floor
        
        # Reset data
        self.mob_resets = []  # Mobs that spawn here
        self.obj_resets = []  # Objects that spawn here
        
        self.config = Config()
        
    def is_dark(self, game_time: Optional[GameTime]) -> bool:
        """Determine if the room is currently dark based on time/flags."""
        if 'dark' in self.flags:
            return True

        if not game_time:
            return False

        if not game_time.is_night():
            return False

        # Outdoors sectors are dark at night
        outdoor_sectors = {
            'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim',
            'flying', 'desert', 'swamp'
        }
        return self.sector_type in outdoor_sectors

    def get_visible_exits(self, player: Optional['Player'] = None) -> Dict[str, dict]:
        """Return exits visible to the player (hidden exits require discovery)."""
        visible = {}
        for direction, exit_data in self.exits.items():
            if not exit_data:
                continue
            if exit_data.get('hidden'):
                if player and hasattr(player, 'discovered_exits') and (self.vnum, direction) in player.discovered_exits:
                    visible[direction] = exit_data
            else:
                visible[direction] = exit_data
        return visible

    async def show_to(self, player: 'Player', force_exits: bool = False):
        """Display the room to a player."""
        c = self.config.COLORS

        # Can't see room details while sleeping
        if hasattr(player, 'position') and player.position == 'sleeping':
            await player.send("You can't see anything, you're sleeping!")
            return

        # Day/night visibility check
        game_time = None
        if hasattr(player, 'world') and player.world:
            game_time = player.world.game_time
        is_too_dark = self.is_dark(game_time) and hasattr(player, 'can_see_in_dark') and not player.can_see_in_dark()
        
        if is_too_dark:
            # In darkness: show only that it's dark and available exits (can feel walls)
            await player.send(f"{c['blue']}It is pitch black. You can't see a thing.{c['reset']}")
            # Still show exits - you can feel your way around
            visible_exits = self.get_visible_exits(player)
            exit_strings = []
            for direction, exit_data in visible_exits.items():
                if exit_data and 'door' in exit_data:
                    door = exit_data['door']
                    state = door.get('state', 'open')
                    if state == 'closed':
                        # Can feel a closed door but not see details
                        exit_strings.append(f"{c['yellow']}{direction}[blocked]{c['green']}")
                    else:
                        exit_strings.append(direction)
                else:
                    exit_strings.append(direction)
            if exit_strings:
                await player.send(f"{c['green']}[ Exits: {' '.join(exit_strings)} ]{c['reset']}")
            else:
                await player.send(f"{c['yellow']}[ Exits: None ]{c['reset']}")
            await player.send(f"{c['cyan']}Hint: Equip a light source or cast a light spell.{c['reset']}")
            return

        # Weather visibility effects (outdoors only)
        outdoor_sectors = {
            'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim',
            'flying', 'desert', 'swamp'
        }
        if self.zone and self.sector_type in outdoor_sectors:
            weather = self.zone.weather
            if weather:
                vision_mod = weather.get_vision_modifier()
                if vision_mod < 0.6:
                    await player.send(f"{c['blue']}Visibility is severely reduced by the weather.{c['reset']}")
                    await player.send(f"{c['cyan']}{self.name}{c['reset']}")
                    await player.send(f"{c['white']}You can barely make out your surroundings.{c['reset']}")
                    visible_exits = self.get_visible_exits(player)
                    exit_strings = []
                    for direction, exit_data in visible_exits.items():
                        if exit_data and 'door' in exit_data:
                            door = exit_data['door']
                            state = door.get('state', 'open')
                            door_name = door.get('name', 'door')
                            if state == 'closed':
                                if door.get('locked'):
                                    exit_strings.append(f"{c['red']}{direction}[{door_name}:locked]{c['green']}")
                                elif door.get('picked'):
                                    exit_strings.append(f"{c['yellow']}{direction}[{door_name}:picked]{c['green']}")
                                else:
                                    exit_strings.append(f"{c['yellow']}{direction}[{door_name}:closed]{c['green']}")
                            else:
                                exit_strings.append(direction)
                        else:
                            exit_strings.append(direction)
                    if exit_strings:
                        await player.send(f"{c['green']}[ Exits: {' '.join(exit_strings)} ]{c['reset']}")
                    else:
                        await player.send(f"{c['yellow']}[ Exits: None ]{c['reset']}")
                    return
                elif vision_mod < 1.0:
                    await player.send(f"{c['blue']}Visibility is reduced by the weather.{c['reset']}")

        # Room name
        vnum_str = f" {c['yellow']}[{self.vnum}]{c['reset']}" if getattr(player, 'show_room_vnums', False) else ""
        await player.send(f"{c['cyan']}{self.name}{vnum_str}{c['reset']}")
        
        # Dynamic atmospheric description based on time/weather
        try:
            from atmosphere import AtmosphereManager
            weather = self.zone.weather if self.zone else None
            atmosphere = AtmosphereManager.get_atmosphere(self, game_time, weather)
            if atmosphere:
                await player.send(f"{c['blue']}{atmosphere}{c['reset']}")
        except Exception:
            pass
        
        # Description
        desc = self.description or ""
        if getattr(player, 'brief_mode', False):
            # First sentence or 200 chars
            sentences = desc.split('.')
            if len(sentences) >= 2:
                brief_desc = sentences[0] + '.' + sentences[1] + '.'
            elif sentences and sentences[0]:
                brief_desc = sentences[0] + '.'
            else:
                brief_desc = desc
            if len(brief_desc) > 500:
                brief_desc = brief_desc[:500] + '...'
            await player.send(f"{c['white']}{brief_desc}{c['reset']}")
        else:
            await player.send(f"{c['white']}{desc}{c['reset']}")

        # Puzzle prompts
        try:
            from puzzles import PuzzleManager
            await PuzzleManager.announce_room_puzzles(player)
        except Exception:
            pass
        
        # Exits (only show if autoexit enabled or explicitly requested)
        if force_exits or getattr(player, 'autoexit', False):
            visible_exits = self.get_visible_exits(player)
            exit_strings = []
            for direction, exit_data in visible_exits.items():
                if exit_data and 'door' in exit_data:
                    door = exit_data['door']
                    state = door.get('state', 'open')
                    door_name = door.get('name', 'door')
                    if state == 'closed':
                        if door.get('locked'):
                            # Red for locked
                            exit_strings.append(f"{c['red']}{direction}[{door_name}:locked]{c['green']}")
                        elif door.get('picked'):
                            # Yellow for picked (closed but lock broken)
                            exit_strings.append(f"{c['yellow']}{direction}[{door_name}:picked]{c['green']}")
                        else:
                            # Yellow for closed but unlocked
                            exit_strings.append(f"{c['yellow']}{direction}[{door_name}:closed]{c['green']}")
                    else:
                        # Open door - show in normal color
                        exit_strings.append(direction)
                else:
                    exit_strings.append(direction)
            if exit_strings:
                await player.send(f"{c['green']}[ Exits: {' '.join(exit_strings)} ]{c['reset']}")
            else:
                await player.send(f"{c['yellow']}[ Exits: None ]{c['reset']}")
            
        # Gold in room
        if self.gold > 0:
            if self.gold == 1:
                await player.send(f"{c['yellow']}A single gold coin lies here.{c['reset']}")
            else:
                await player.send(f"{c['yellow']}A pile of {self.gold} gold coins lies here.{c['reset']}")

        # Items in room
        for item in self.items:
            try:
                from legendary import get_rarity_color, RARITY_TIERS
                rarity = getattr(item, 'rarity', 'common') or 'common'
                rcolor = c.get(RARITY_TIERS.get(rarity, {}).get('color_code', 'yellow'), c['yellow'])
                await player.send(f"{rcolor}{item.room_desc}{c['reset']}")
            except Exception:
                await player.send(f"{c['yellow']}{item.room_desc}{c['reset']}")

        # Display case for collections in player housing
        try:
            from housing import HouseManager
            if HouseManager.in_house(player):
                from collection_system import CollectionManager
                case_lines = CollectionManager.get_display_case_lines(player)
                for line in case_lines:
                    await player.send(line)
        except Exception:
            pass
            
        # Characters in room (excluding player)
        for char in self.characters:
            if char != player:
                fighting_msg = ""
                # CircleMUD-style: show who this character is fighting
                if hasattr(char, 'fighting') and char.fighting:
                    if char.fighting == player:
                        fighting_msg = f" {c['red']}[fighting YOU!]{c['reset']}"
                    else:
                        fighting_msg = f" {c['yellow']}[fighting {char.fighting.name}]{c['reset']}"
                # Also note if player is fighting this character
                elif hasattr(player, 'fighting') and player.fighting == char:
                    fighting_msg = f" {c['red']}[your target]{c['reset']}"

                # Check if player has labeled this character
                label_msg = ""
                if hasattr(player, 'target_labels') and player.target_labels:
                    for label_name, labeled_char in player.target_labels.items():
                        if labeled_char == char:
                            label_msg = f" {c['bright_yellow']}({label_name}){c['reset']}"
                            break

                # Color pets/summons differently from regular NPCs
                if hasattr(char, 'owner') and char.owner:
                    # This is a pet/summon - use magenta
                    if char.owner == player:
                        char_color = c['bright_magenta']  # Your pets
                        owner_tag = f" {c['green']}(yours){c['reset']}"
                    else:
                        char_color = c['magenta']  # Other player's pets
                        owner_tag = f" {c['yellow']}({char.owner.name}'s){c['reset']}"
                else:
                    char_color = c['bright_cyan']  # Regular NPCs
                    owner_tag = ""

                # Randomly visible sneaking mobs
                sneak_indicator = ""
                try:
                    flags = getattr(char, 'flags', set())
                    if 'sneaking' in flags and char != player:
                        perc = player.get_perception() if hasattr(player, 'get_perception') else 10
                        # Harder to see sneaking characters
                        if random.randint(1, 100) > min(95, 30 + perc * 2):
                            continue
                        # If we can see them, show they're sneaking
                        sneak_indicator = f" {c['bright_black']}(sneaking){c['reset']}"
                except Exception:
                    pass
                
                # Quest giver indicator (! or ?)
                quest_indicator = ""
                if hasattr(char, 'vnum') and not hasattr(char, 'connection'):
                    try:
                        from quests import QuestManager
                        qi = QuestManager.get_quest_giver_indicator(player, char.vnum)
                        if qi == '!':
                            quest_indicator = f" {c['bright_yellow']}[!]{c['reset']}"
                        elif qi == '?':
                            quest_indicator = f" {c['bright_green']}[?]{c['reset']}"
                    except Exception:
                        pass

                # Build the character description line
                if hasattr(char, 'fighting') and char.fighting:
                    # CircleMUD style: replace desc with fighting message
                    if char.fighting == player:
                        desc = f"{char.name} is here, fighting YOU!"
                        await player.send(f"{c['red']}{desc}{owner_tag}{label_msg}{sneak_indicator}{c['reset']}")
                    else:
                        desc = f"{char.name} is here, fighting {char.fighting.name}."
                        await player.send(f"{char_color}{desc}{owner_tag}{label_msg}{sneak_indicator}{c['reset']}")
                elif hasattr(char, 'long_desc'):
                    # Show mob name hint so players know what keyword to use
                    name_hint = ""
                    if hasattr(char, 'vnum') and not hasattr(char, 'connection'):
                        name_hint = f" {c['bright_black']}({char.name}){c['reset']}"
                    await player.send(f"{char_color}{char.long_desc}{name_hint}{quest_indicator}{owner_tag}{label_msg}{fighting_msg}{sneak_indicator}{c['reset']}")
                elif hasattr(char, 'connection') and char.connection:
                    # Player character - show title and prestige class
                    title_str = getattr(char, 'title', '') or ''
                    prestige = getattr(char, 'prestige_class', None)
                    prestige_str = f" {c['bright_yellow']}[{prestige}]{c['reset']}" if prestige else ""
                    await player.send(f"{c['bright_green']}{char.name} {title_str}{prestige_str} is standing here.{label_msg}{fighting_msg}{sneak_indicator}{c['reset']}")
                else:
                    await player.send(f"{char_color}{char.name} is standing here.{quest_indicator}{owner_tag}{label_msg}{fighting_msg}{sneak_indicator}{c['reset']}")

                # Show active debuffs/buffs on the character (limited, flavorful)
                if hasattr(char, 'affects') and char.affects:
                    debuff_messages = []
                    for affect in char.affects:
                        if affect.type == 'dot' and affect.name == 'poison':
                            debuff_messages.append(f"{c['green']}{char.name} looks sick and pale.{c['reset']}")
                        elif affect.type == 'flag':
                            if affect.applies_to == 'blind':
                                debuff_messages.append(f"{c['yellow']}{char.name} seems blinded.{c['reset']}")
                            elif affect.applies_to == 'silenced':
                                debuff_messages.append(f"{c['magenta']}{char.name} is unnaturally quiet.{c['reset']}")
                            elif affect.applies_to == 'sanctuary':
                                debuff_messages.append(f"{c['white']}{char.name} glows with a holy aura.{c['reset']}")
                            elif affect.applies_to == 'fly':
                                debuff_messages.append(f"{c['cyan']}{char.name} is levitating above the ground.{c['reset']}")
                            elif affect.applies_to == 'stoneskin':
                                debuff_messages.append(f"{c['white']}{char.name}'s skin looks like stone.{c['reset']}")
                            elif affect.applies_to == 'invisible':
                                # Don't show if the viewer can't detect invisible
                                if hasattr(player, 'affect_flags') and 'detect_invisible' in player.affect_flags:
                                    debuff_messages.append(f"{c['cyan']}{char.name} shimmers faintly in the air.{c['reset']}")
                        elif affect.type == 'modify_stat':
                            if affect.name == 'weakened':
                                debuff_messages.append(f"{c['red']}{char.name} looks weakened!{c['reset']}")
                            elif affect.name == 'slowed':
                                debuff_messages.append(f"{c['blue']}{char.name} is moving sluggishly!{c['reset']}")

                    for msg in debuff_messages:
                        await player.send(msg)
                    
    async def send_to_room(self, message: str, exclude: List = None, wake_sleepers: bool = False):
        """Send a message to everyone in the room (sleeping players don't see messages unless wake_sleepers=True)."""
        exclude = exclude or []
        for char in self.characters:
            if char not in exclude and hasattr(char, 'send'):
                # Skip sleeping players unless it's important enough to wake them
                if not wake_sleepers and getattr(char, 'position', 'standing') == 'sleeping':
                    continue
                await char.send(message)
                
    def get_exit(self, direction: str) -> Optional['Room']:
        """Get the room in a given direction."""
        exit_data = self.exits.get(direction)
        if not exit_data:
            return None
        return exit_data.get('room')
        
    def to_dict(self) -> dict:
        """Convert room to dictionary for saving."""
        exits = {}
        for d, e in self.exits.items():
            if not e:
                continue
            ex = dict(e)
            # Remove runtime-only references
            if 'room' in ex:
                ex.pop('room')
            exits[d] = ex
        return {
            'vnum': self.vnum,
            'name': self.name,
            'description': self.description,
            'sector_type': self.sector_type,
            'flags': list(self.flags),
            'exits': exits,
            'extra_descs': self.extra_descs,
            'hidden_items': self.hidden_items,
            'puzzles': self.puzzles,
            'mob_resets': self.mob_resets,
            'obj_resets': self.obj_resets,
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Room':
        """Create a room from dictionary data."""
        room = cls(data['vnum'])
        room.name = data.get('name', 'An Empty Room')
        room.description = data.get('description', '')
        room.sector_type = data.get('sector_type', 'inside')
        room.flags = set(data.get('flags', []))
        
        # Process exits and convert flag-based door format to door objects
        room.exits = {}
        for direction, exit_data in data.get('exits', {}).items():
            if exit_data:
                # Copy the exit data
                processed_exit = dict(exit_data)

                # Normalize legacy exit key
                if 'room_vnum' in processed_exit and 'to_room' not in processed_exit:
                    processed_exit['to_room'] = processed_exit['room_vnum']

                # Check for door flags and convert to door object
                exit_flags = list(exit_data.get('flags', []))  # Make a copy
                if 'door' in exit_flags or exit_data.get('door'):
                    # Has a door - create door object if not exists
                    if 'door' not in processed_exit or not isinstance(processed_exit.get('door'), dict):
                        door_name = exit_data.get('keyword', 'door').split()[0] if exit_data.get('keyword') else 'door'
                        processed_exit['door'] = {
                            'name': door_name,
                            'state': 'closed' if 'closed' in exit_flags else 'open',
                            'locked': 'locked' in exit_flags,
                            'pickproof': 'pickproof' in exit_flags,
                            'key': exit_data.get('key'),
                        }
                    else:
                        # Door object exists, ensure it has proper state from flags
                        door = processed_exit['door']
                        if 'closed' in exit_flags and door.get('state') != 'open':
                            door['state'] = 'closed'
                        if 'locked' in exit_flags:
                            door['locked'] = True
                    
                    # Remove door-related flags since they're now in the door object
                    # This prevents the flags from overriding the door object state
                    for flag in ['door', 'closed', 'locked', 'pickproof']:
                        if flag in exit_flags:
                            exit_flags.remove(flag)
                    processed_exit['flags'] = exit_flags
                
                room.exits[direction] = processed_exit
        
        room.extra_descs = data.get('extra_descs', {})
        room.hidden_items = data.get('hidden_items', [])
        room.puzzles = data.get('puzzles', [])
        room.mob_resets = data.get('mob_resets', [])
        room.obj_resets = data.get('obj_resets', [])
        return room


class Zone:
    """A zone containing rooms, mobs, and objects."""
    
    def __init__(self, number: int):
        self.number = number
        self.name = "Unknown Zone"
        self.builders = ""
        self.lifespan = 2  # Reset ticks (each tick = 15 real minutes; 2 = 30 min)
        self.reset_mode = 2  # 0=never, 1=empty, 2=always
        self.top = 0  # Highest vnum in zone
        self.age = 0  # Ticks since last reset
        self.reset_interval_seconds = self.lifespan * 900
        self.last_reset_at = None
        self.next_reset_at = None

        self.rooms: Dict[int, Room] = {}
        self.mobs: Dict[int, dict] = {}  # mob prototypes
        self.objects: Dict[int, dict] = {}  # object prototypes

        # Initialize weather for this zone
        self.weather = Weather(number)
        
    def to_dict(self) -> dict:
        """Convert zone to dictionary for saving."""
        return {
            'number': self.number,
            'name': self.name,
            'builders': self.builders,
            'reset_time': self.lifespan * 900,  # Save as seconds for from_dict
            'reset_mode': self.reset_mode,
            'top': self.top,
            'rooms': {vnum: room.to_dict() for vnum, room in self.rooms.items()},
            'mobs': self.mobs,
            'objects': self.objects,
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Zone':
        """Create a zone from dictionary data."""
        zone = cls(data['number'])
        zone.name = data.get('name', 'Unknown Zone')
        zone.builders = data.get('builders', '')

        # Handle both old format (lifespan in minutes) and new format (reset_time in seconds)
        # zone_reset_tick is called every 900 seconds (15 minutes), so zone.age increments every 15 minutes
        if 'reset_time' in data:
            # New format: reset_time in seconds, convert to 15-minute units
            reset_time_seconds = data['reset_time']
            zone.lifespan = max(1, round(reset_time_seconds / 900))
        else:
            # Old format: lifespan already in the correct unit (but was probably intended as minutes)
            # Since zone.age increments every 15 minutes, we need to adjust
            lifespan_value = data.get('lifespan', 30)
            # Treat old lifespan values as minutes, convert to 15-minute units
            zone.lifespan = max(1, round(lifespan_value / 15))
        zone.reset_interval_seconds = zone.lifespan * 900

        zone.reset_mode = data.get('reset_mode', 2)
        zone.top = data.get('top', 0)
        
        # Load rooms
        for vnum_str, room_data in data.get('rooms', {}).items():
            room = Room.from_dict(room_data)
            room.zone = zone
            zone.rooms[int(vnum_str)] = room
            
        zone.mobs = data.get('mobs', {})
        zone.objects = data.get('objects', {})
        
        return zone


class World:
    """The game world."""
    
    def __init__(self, config: Config):
        self.config = config
        self.zones: Dict[int, Zone] = {}
        self.rooms: Dict[int, Room] = {}
        self.mob_prototypes: Dict[int, dict] = {}
        self.obj_prototypes: Dict[int, dict] = {}

        self.players: Dict[str, 'Player'] = {}  # Online players
        self.npcs: List = []  # All loaded NPCs

        # Initialize game time system
        self.game_time = GameTime()

        # World events manager (initialized after load)
        self.event_manager = None
        
    async def load(self):
        """Load the world from files."""
        logger.info("Loading world...")
        
        # Load zones
        zones_dir = os.path.join(self.config.WORLD_DIR, 'zones')
        
        if os.path.exists(zones_dir):
            for filename in os.listdir(zones_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(zones_dir, filename)
                    await self.load_zone_file(filepath)
        else:
            logger.warning(f"Zones directory not found: {zones_dir}")
            
        # If no zones loaded, create default world
        if not self.zones:
            logger.info("No zones found, creating default world...")
            await self.create_default_world()
            
        # Link room exits
        self.link_exits()

        # Seed puzzles
        try:
            from puzzles import PuzzleManager
            PuzzleManager.seed_world(self)
        except Exception:
            pass
        
        # Reset zones (spawn mobs and objects)
        await self.reset_all_zones()

        # Spawn faction NPCs
        try:
            from factions import spawn_faction_npcs
            spawn_faction_npcs(self)
        except Exception as e:
            logger.warning(f"Failed to spawn faction NPCs: {e}")
        
        # Initialize world events system
        from world_events import WorldEventManager
        self.event_manager = WorldEventManager(self)

        # Register legendary item prototypes
        try:
            from legendary import LEGENDARY_ITEMS
            for vnum, proto in LEGENDARY_ITEMS.items():
                if vnum not in self.obj_prototypes:
                    self.obj_prototypes[vnum] = proto
        except Exception as e:
            logger.warning(f"Failed to register legendary items: {e}")

        logger.info(f"World loaded: {len(self.zones)} zones, {len(self.rooms)} rooms")
        
    async def load_zone_file(self, filepath: str):
        """Load a zone from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            zone = Zone.from_dict(data)
            self.zones[zone.number] = zone
            
            # Add rooms to global lookup
            for vnum, room in zone.rooms.items():
                self.rooms[vnum] = room
                
            # Add mob/object prototypes
            for vnum_str, mob_data in zone.mobs.items():
                self.mob_prototypes[int(vnum_str)] = mob_data
            for vnum_str, obj_data in zone.objects.items():
                self.obj_prototypes[int(vnum_str)] = obj_data
                
            logger.info(f"Loaded zone {zone.number}: {zone.name} ({len(zone.rooms)} rooms)")
            
        except Exception as e:
            logger.error(f"Error loading zone file {filepath}: {e}")
            
    def link_exits(self):
        """Link room exits to actual room objects and ensure doors exist on both sides."""
        from config import Config
        config = Config()
        
        for room in self.rooms.values():
            for direction, exit_data in room.exits.items():
                if exit_data and 'to_room' in exit_data:
                    target_vnum = exit_data['to_room']
                    if target_vnum in self.rooms:
                        target_room = self.rooms[target_vnum]
                        exit_data['room'] = target_room
                        
                        # If this exit has a door, ensure the other side has it too
                        if 'door' in exit_data and exit_data['door']:
                            opposite = config.DIRECTIONS.get(direction, {}).get('opposite')
                            if opposite and opposite in target_room.exits:
                                other_exit = target_room.exits[opposite]
                                if other_exit and 'door' not in other_exit:
                                    # Copy the door to the other side
                                    other_exit['door'] = dict(exit_data['door'])
                        
    async def create_default_world(self):
        """Create a default fantasy world."""
        from world_builder import WorldBuilder
        builder = WorldBuilder(self)
        await builder.build_default_world()
        
    async def reset_all_zones(self):
        """Reset all zones (spawn mobs/objects)."""
        for zone in self.zones.values():
            await self.reset_zone(zone)
            
    async def reset_zone(self, zone: Zone):
        """Reset a single zone."""
        from bosses import create_mob_from_prototype
        from objects import create_object
        
        for room in zone.rooms.values():
            # Spawn mobs
            for mob_reset in room.mob_resets:
                mob_vnum = mob_reset.get('vnum')
                max_count = mob_reset.get('max', 1)
                max_existing = mob_reset.get('max_existing')
                
                # Count existing mobs for this vnum in the zone (prevents dupes when they wander)
                current = sum(
                    1 for npc in self.npcs
                    if hasattr(npc, 'vnum')
                    and npc.vnum == mob_vnum
                    and (
                        getattr(npc, 'home_zone', None) == zone.number
                        or (npc.room and npc.room.zone == zone)
                    )
                )

                if max_existing is not None:
                    existing_in_zone = sum(
                        1 for npc in self.npcs
                        if hasattr(npc, 'vnum')
                        and npc.vnum == mob_vnum
                        and (
                            getattr(npc, 'home_zone', None) == zone.number
                            or (npc.room and npc.room.zone == zone)
                        )
                    )
                    if existing_in_zone >= max_existing:
                        continue
                
                if current < max_count:
                    proto = self.mob_prototypes.get(mob_vnum)
                    if proto:
                        mob = create_mob_from_prototype(proto, self)
                        mob.room = room
                        mob.home_room = room  # Set home room for AI
                        mob.home_zone = zone.number  # Set home zone for movement restrictions
                        room.characters.append(mob)
                        self.npcs.append(mob)
                        
            # Spawn objects
            for obj_reset in room.obj_resets:
                obj_vnum = obj_reset.get('vnum')
                max_count = obj_reset.get('max', 1)
                
                # Count existing objects of this type
                current = sum(1 for item in room.items 
                            if hasattr(item, 'vnum') and item.vnum == obj_vnum)
                
                if current < max_count:
                    obj = create_object(obj_vnum, self)
                    if obj:
                        room.items.append(obj)
                        
        zone.age = 0
        zone.last_reset_at = time.time()
        zone.next_reset_at = zone.last_reset_at + zone.reset_interval_seconds
        
    def get_room(self, vnum: int) -> Optional[Room]:
        """Get a room by vnum."""
        return self.rooms.get(vnum)
        
    async def add_player(self, player: 'Player'):
        """Add a player to the world."""
        self.players[player.name.lower()] = player

        # Spawn persistent companions
        if hasattr(player, 'companions') and player.companions:
            from pets import Pet
            from companions import Companion
            for companion in player.companions:
                if isinstance(companion, Pet) and companion.is_persistent:
                    # Add companion to world
                    companion.room = player.room
                    player.room.characters.append(companion)
                    self.npcs.append(companion)
                    logger.info(f"Spawned companion: {companion.name} for {player.name}")
                elif isinstance(companion, Companion):
                    companion.room = player.room
                    player.room.characters.append(companion)
                    self.npcs.append(companion)
                    logger.info(f"Spawned companion: {companion.name} for {player.name}")

        logger.info(f"Player entered world: {player.name}")

    async def remove_player(self, player: 'Player'):
        """Remove a player from the world."""
        # Remove persistent companions from world (but keep in player's companion list)
        if hasattr(player, 'companions') and player.companions:
            from pets import Pet
            from companions import Companion
            for companion in player.companions:
                if isinstance(companion, Pet) and companion.is_persistent:
                    if companion.room and companion in companion.room.characters:
                        companion.room.characters.remove(companion)
                    if companion in self.npcs:
                        self.npcs.remove(companion)
                    logger.info(f"Removed companion: {companion.name} for {player.name}")
                elif isinstance(companion, Companion):
                    if companion.room and companion in companion.room.characters:
                        companion.room.characters.remove(companion)
                    if companion in self.npcs:
                        self.npcs.remove(companion)
                    logger.info(f"Removed companion: {companion.name} for {player.name}")

        if player.name.lower() in self.players:
            del self.players[player.name.lower()]

        if player.room and player in player.room.characters:
            player.room.characters.remove(player)

        logger.info(f"Player left world: {player.name}")
        
    def get_player(self, name: str) -> Optional['Player']:
        """Get an online player by name."""
        return self.players.get(name.lower())
        
    async def combat_tick(self):
        """Process combat for all fighting characters."""
        from combat import CombatHandler

        # Process player combat
        for player in list(self.players.values()):
            # If mobs are attacking the player, set fighting target to one of them
            if not player.is_fighting and player.room:
                attackers = [ch for ch in player.room.characters if hasattr(ch, 'fighting') and ch.fighting == player]
                if attackers:
                    player.fighting = attackers[0]
                    player.position = 'fighting'
                elif player.position == 'fighting':
                    # Clear stuck combat state
                    player.position = 'standing'

            # Autoattack if enabled
            if getattr(player, 'autoattack', False) and not player.is_fighting:
                target = getattr(player, 'target', None)
                if target and player.room and target in player.room.characters:
                    if not hasattr(target, 'connection') and 'peaceful' not in player.room.flags:
                        await CombatHandler.start_combat(player, target)

            if player.is_fighting:
                # Check if target is still valid
                if player.fighting is None or player.fighting.hp <= 0 or player.fighting not in player.room.characters:
                    player.fighting = None
                    player.position = 'standing'
                    continue
                await CombatHandler.one_round(player, player.fighting)
                # Send prompt after combat round so player always sees HP
                if hasattr(player, 'connection') and player.connection:
                    await player.connection.send_prompt()

        # Process NPC combat
        from mob_ai import mob_ai_tick
        for npc in list(self.npcs):
            if npc.is_fighting:
                # Check if target is still valid
                if npc.fighting is None or npc.fighting.hp <= 0 or (hasattr(npc.fighting, 'room') and npc.fighting not in npc.room.characters):
                    npc.fighting = None
                    npc.position = 'standing'
                    continue
                # Run intelligent mob AI before the auto-attack round
                try:
                    await mob_ai_tick(npc)
                except Exception as e:
                    logger.debug(f"Mob AI error for {npc.name}: {e}")
                # Re-check fighting state (AI may have caused flee/death)
                if not npc.is_fighting or not npc.fighting:
                    continue
                await CombatHandler.one_round(npc, npc.fighting)
                
    async def affect_tick(self):
        """Process DOT/HOT effects and decrement durations."""
        from affects import AffectManager

        for player in self.players.values():
            await AffectManager.tick_affects(player)

        for npc in self.npcs:
            if hasattr(npc, 'affects'):
                await AffectManager.tick_affects(npc)

    async def poison_tick(self):
        """Process poison damage for all characters (faster tick)."""
        from affects import AffectManager

        for player in self.players.values():
            # Only process poison DOT effects, don't decrement durations
            await AffectManager.tick_affects(player, poison_only=True)

        for npc in self.npcs:
            # Only process poison DOT effects, don't decrement durations
            await AffectManager.tick_affects(npc, poison_only=True)

    async def regen_tick(self):
        """Process regeneration for all characters."""
        c = Config().COLORS
        for player in self.players.values():
            await player.regen_tick()
            # Notify players with tick notifications enabled
            if getattr(player, 'show_ticks', False):
                await player.send(f"{c['cyan']}[TICK - Regen]{c['reset']}")

        for npc in self.npcs:
            if hasattr(npc, 'regen_tick'):
                await npc.regen_tick()

    async def minor_regen_tick(self):
        """Process small between-tick regeneration for all characters."""
        for player in self.players.values():
            if hasattr(player, 'minor_regen_tick'):
                await player.minor_regen_tick()

    async def zone_reset_tick(self):
        """Check and reset zones as needed."""
        for zone in self.zones.values():
            zone.age += 1
            if zone.age >= zone.lifespan:
                if zone.reset_mode == 2:  # Always reset
                    await self.reset_zone(zone)
                elif zone.reset_mode == 1:  # Reset if empty
                    players_in_zone = any(
                        p.room and p.room.zone == zone 
                        for p in self.players.values()
                    )
                    if not players_in_zone:
                        await self.reset_zone(zone)

    async def time_tick(self):
        """Process game time advancement."""
        old_hour = self.game_time.hour
        old_day = (self.game_time.year, self.game_time.month, self.game_time.day)

        # Advance time by 1 second
        self.game_time.advance_tick(1)

        # Check if hour changed
        if self.game_time.hour != old_hour:
            # Get time announcement for significant events
            announcement = self.game_time.get_time_announcement()
            if announcement:
                # Announce to all players
                c = self.config.COLORS
                for player in self.players.values():
                    await player.send(f"\r\n{c['yellow']}{announcement}{c['reset']}\r\n")
                logger.info(f"Time: {self.game_time.get_time_string()}")
            
            # Process hunger/thirst for all players (every game hour)
            c = self.config.COLORS
            for player in self.players.values():
                # Decrement hunger (1 per game hour)
                if hasattr(player, 'hunger') and player.hunger > 0:
                    player.hunger -= 1
                    if player.hunger == 20:
                        await player.send(f"\r\n{c['yellow']}You are getting hungry.{c['reset']}\r\n")
                    elif player.hunger == 10:
                        await player.send(f"\r\n{c['bright_yellow']}You are hungry!{c['reset']}\r\n")
                    elif player.hunger == 5:
                        await player.send(f"\r\n{c['red']}You are very hungry!{c['reset']}\r\n")
                    elif player.hunger == 0:
                        await player.send(f"\r\n{c['bright_red']}You are STARVING! Find food soon!{c['reset']}\r\n")
                
                # Decrement thirst (1 per game hour)
                if hasattr(player, 'thirst') and player.thirst > 0:
                    player.thirst -= 1
                    if player.thirst == 15:
                        await player.send(f"\r\n{c['yellow']}You are getting thirsty.{c['reset']}\r\n")
                    elif player.thirst == 8:
                        await player.send(f"\r\n{c['bright_yellow']}You are thirsty!{c['reset']}\r\n")
                    elif player.thirst == 3:
                        await player.send(f"\r\n{c['red']}You are very thirsty!{c['reset']}\r\n")
                    elif player.thirst == 0:
                        await player.send(f"\r\n{c['bright_red']}You are DYING OF THIRST! Find water!{c['reset']}\r\n")
            
            # Process NPC schedules (shopkeepers open/close, etc.)
            try:
                from npc_schedules import schedule_tick
                await schedule_tick(self)
            except Exception as e:
                logger.debug(f"NPC schedule error: {e}")

        # Daily upkeep for companions
        new_day = (self.game_time.year, self.game_time.month, self.game_time.day)
        if new_day != old_day:
            from companions import CompanionManager
            await CompanionManager.apply_daily_upkeep(self)

    async def weather_tick(self):
        """Process weather updates for all zones."""
        for zone in self.zones.values():
            if zone.number > 0:  # Skip Limbo (zone 0)
                old_weather = zone.weather.sky_condition
                zone.weather.update_weather(self.game_time)

                # Announce significant weather changes to players in the zone
                if zone.weather.sky_condition != old_weather:
                    c = self.config.COLORS
                    weather_desc = zone.weather.get_weather_desc()

                    for player in self.players.values():
                        if player.room and player.room.zone == zone:
                            await player.send(f"\r\n{c['cyan']}{weather_desc}{c['reset']}\r\n")

    async def pet_tick(self):
        """Process pet timers and expiration."""
        from pets import PetManager
        await PetManager.pet_tick(self)

    async def decay_tick(self):
        """Process corpse decay and ground item decay.
        
        Corpses decay after ~5 minutes real time (50 ticks at 6s/tick).
        When a corpse decays, its contents drop to the ground.
        Ground items (non-permanent) decay after 2-3 MUD days (~30 min real time).
        """
        for room in self.rooms.values():
            if not hasattr(room, 'items'):
                continue
            items_to_remove = []
            items_to_add = []
            
            for item in room.items:
                # Initialize decay timer if not set
                if not hasattr(item, 'decay_timer'):
                    if 'corpse' in getattr(item, 'name', '').lower():
                        item.decay_timer = 50  # ~5 min at 6s per tick
                    elif getattr(item, 'item_type', '') in ('key',):
                        item.decay_timer = 300  # Keys last longer (~30 min)
                    elif hasattr(item, '_permanent') and item._permanent:
                        item.decay_timer = -1  # Never decay (zone resets)
                    else:
                        item.decay_timer = -1  # Don't decay zone-spawned items
                
                if item.decay_timer < 0:
                    continue  # Permanent item
                    
                item.decay_timer -= 1
                
                if item.decay_timer <= 0:
                    if 'corpse' in getattr(item, 'name', '').lower():
                        # Corpse decays — drop contents to ground
                        contents = getattr(item, 'contents', [])
                        for contained in contents:
                            contained.decay_timer = 500  # ~50 min for dropped items
                            items_to_add.append(contained)
                        # Notify players in room
                        for char in room.characters:
                            if hasattr(char, 'send'):
                                c = char.config.COLORS
                                await char.send(f"{c['yellow']}{item.short_desc} decays, leaving behind its contents.{c['reset']}")
                    else:
                        # Regular item decays
                        for char in room.characters:
                            if hasattr(char, 'send'):
                                c = char.config.COLORS
                                await char.send(f"{c['yellow']}{item.short_desc} crumbles to dust.{c['reset']}")
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                room.items.remove(item)
            for item in items_to_add:
                room.items.append(item)

    async def process_npcs(self):
        """Process NPC AI."""
        for npc in list(self.npcs):
            if hasattr(npc, 'process_ai'):
                await npc.process_ai()
                
    async def autosave(self):
        """Autosave all players."""
        for player in self.players.values():
            await player.save()
        logger.info(f"Autosaved {len(self.players)} players")
        
    async def save_all(self):
        """Save all players on shutdown."""
        for player in self.players.values():
            await player.save()
        logger.info(f"Saved all {len(self.players)} players")
        
    async def broadcast(self, message: str, exclude: List = None):
        """Broadcast a message to all players."""
        exclude = exclude or []
        for player in self.players.values():
            if player not in exclude:
                await player.send(f"\r\n{message}\r\n")
