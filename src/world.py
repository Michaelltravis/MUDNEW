"""
RealmsMUD World
===============
World management - zones, rooms, mobs, objects.
"""

import os
import json
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
        
        # Contents
        self.characters = []  # Players and NPCs in room
        self.items = []  # Objects in room
        self.gold = 0  # Gold coins on the floor
        
        # Reset data
        self.mob_resets = []  # Mobs that spawn here
        self.obj_resets = []  # Objects that spawn here
        
        self.config = Config()
        
    async def show_to(self, player: 'Player'):
        """Display the room to a player."""
        c = self.config.COLORS

        # Can't see room details while sleeping
        if hasattr(player, 'position') and player.position == 'sleeping':
            await player.send("You can't see anything, you're sleeping!")
            return

        # Room name
        await player.send(f"{c['cyan']}{self.name}{c['reset']}")
        
        # Description
        await player.send(f"{c['white']}{self.description}{c['reset']}")
        
        # Exits
        exits = [d for d, e in self.exits.items() if e]
        if exits:
            await player.send(f"{c['green']}[ Exits: {' '.join(exits)} ]{c['reset']}")
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
            await player.send(f"{c['yellow']}{item.room_desc}{c['reset']}")
            
        # Characters in room (excluding player)
        for char in self.characters:
            if char != player:
                fighting_msg = ""
                # Check if this character is fighting the player
                if hasattr(char, 'fighting') and char.fighting == player:
                    fighting_msg = f" {c['red']}(Fighting YOU!){c['reset']}"
                # Check if player is fighting this character
                elif hasattr(player, 'fighting') and player.fighting == char:
                    fighting_msg = f" {c['yellow']}(You are fighting this!){c['reset']}"

                if hasattr(char, 'long_desc'):
                    await player.send(f"{c['bright_cyan']}{char.long_desc}{fighting_msg}{c['reset']}")
                else:
                    await player.send(f"{c['bright_cyan']}{char.name} is standing here.{fighting_msg}{c['reset']}")

                # Show active debuffs/buffs on the character
                if hasattr(char, 'affects') and char.affects:
                    debuff_messages = []
                    for affect in char.affects:
                        if affect.type == 'dot' and affect.name == 'poison':
                            debuff_messages.append(f"{c['green']}{char.name} is poisoned!{c['reset']}")
                        elif affect.type == 'flag':
                            if affect.applies_to == 'blind':
                                debuff_messages.append(f"{c['yellow']}{char.name} is blinded!{c['reset']}")
                            elif affect.applies_to == 'silenced':
                                debuff_messages.append(f"{c['magenta']}{char.name} is silenced!{c['reset']}")
                            elif affect.applies_to == 'sanctuary':
                                debuff_messages.append(f"{c['white']}{char.name} is protected by sanctuary!{c['reset']}")
                            elif affect.applies_to == 'invisible':
                                # Don't show if the viewer can't detect invisible
                                if hasattr(player, 'affect_flags') and 'detect_invisible' in player.affect_flags:
                                    debuff_messages.append(f"{c['cyan']}{char.name} is invisible!{c['reset']}")
                        elif affect.type == 'modify_stat':
                            if affect.name == 'weakened':
                                debuff_messages.append(f"{c['red']}{char.name} looks weakened!{c['reset']}")
                            elif affect.name == 'slowed':
                                debuff_messages.append(f"{c['blue']}{char.name} is moving sluggishly!{c['reset']}")

                    for msg in debuff_messages:
                        await player.send(msg)
                    
    async def send_to_room(self, message: str, exclude: List = None):
        """Send a message to everyone in the room."""
        exclude = exclude or []
        for char in self.characters:
            if char not in exclude and hasattr(char, 'send'):
                await char.send(message)
                
    def get_exit(self, direction: str) -> Optional['Room']:
        """Get the room in a given direction."""
        exit_data = self.exits.get(direction)
        if not exit_data:
            return None
        return exit_data.get('room')
        
    def to_dict(self) -> dict:
        """Convert room to dictionary for saving."""
        return {
            'vnum': self.vnum,
            'name': self.name,
            'description': self.description,
            'sector_type': self.sector_type,
            'flags': list(self.flags),
            'exits': {d: {'to_room': e.get('to_room'), 'description': e.get('description')}
                     for d, e in self.exits.items()},
            'extra_descs': self.extra_descs,
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
        room.exits = {d: e for d, e in data.get('exits', {}).items()}
        room.extra_descs = data.get('extra_descs', {})
        room.mob_resets = data.get('mob_resets', [])
        room.obj_resets = data.get('obj_resets', [])
        return room


class Zone:
    """A zone containing rooms, mobs, and objects."""
    
    def __init__(self, number: int):
        self.number = number
        self.name = "Unknown Zone"
        self.builders = ""
        self.lifespan = 30  # Minutes between resets
        self.reset_mode = 2  # 0=never, 1=empty, 2=always
        self.top = 0  # Highest vnum in zone
        self.age = 0  # Minutes since last reset

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
            'lifespan': self.lifespan,
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
        
        # Reset zones (spawn mobs and objects)
        await self.reset_all_zones()
        
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
        """Link room exits to actual room objects."""
        for room in self.rooms.values():
            for direction, exit_data in room.exits.items():
                if exit_data and 'to_room' in exit_data:
                    target_vnum = exit_data['to_room']
                    if target_vnum in self.rooms:
                        exit_data['room'] = self.rooms[target_vnum]
                        
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
        from mobs import Mobile
        from objects import create_object
        
        for room in zone.rooms.values():
            # Spawn mobs
            for mob_reset in room.mob_resets:
                mob_vnum = mob_reset.get('vnum')
                max_count = mob_reset.get('max', 1)
                
                # Count existing mobs of this type
                current = sum(1 for npc in self.npcs 
                            if hasattr(npc, 'vnum') and npc.vnum == mob_vnum 
                            and npc.room == room)
                
                if current < max_count:
                    proto = self.mob_prototypes.get(mob_vnum)
                    if proto:
                        mob = Mobile.from_prototype(proto, self)
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
        
    def get_room(self, vnum: int) -> Optional[Room]:
        """Get a room by vnum."""
        return self.rooms.get(vnum)
        
    async def add_player(self, player: 'Player'):
        """Add a player to the world."""
        self.players[player.name.lower()] = player

        # Spawn persistent companions
        if hasattr(player, 'companions') and player.companions:
            from pets import Pet
            for companion in player.companions:
                if isinstance(companion, Pet) and companion.is_persistent:
                    # Add companion to world
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
            for companion in player.companions:
                if isinstance(companion, Pet) and companion.is_persistent:
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
            if player.is_fighting:
                # Check if target is still valid
                if player.fighting is None or player.fighting.hp <= 0 or player.fighting not in player.room.characters:
                    player.fighting = None
                    player.position = 'standing'
                    continue
                await CombatHandler.one_round(player, player.fighting)

        # Process NPC combat
        for npc in list(self.npcs):
            if npc.is_fighting:
                # Check if target is still valid
                if npc.fighting is None or npc.fighting.hp <= 0 or (hasattr(npc.fighting, 'room') and npc.fighting not in npc.room.characters):
                    npc.fighting = None
                    npc.position = 'standing'
                    continue
                await CombatHandler.one_round(npc, npc.fighting)
                
    async def poison_tick(self):
        """Process poison damage for all characters (runs every 2.5 seconds)."""
        from affects import AffectManager

        for player in self.players.values():
            # Only process poison DOT effects, don't decrement durations
            await AffectManager.tick_affects(player, poison_only=True)

        for npc in self.npcs:
            # Only process poison DOT effects, don't decrement durations
            await AffectManager.tick_affects(npc, poison_only=True)

    async def regen_tick(self):
        """Process regeneration for all characters."""
        for player in self.players.values():
            await player.regen_tick()

        for npc in self.npcs:
            if hasattr(npc, 'regen_tick'):
                await npc.regen_tick()
                
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
