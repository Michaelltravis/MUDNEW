"""
RealmsMUD Ambient Message System
================================
Adds life to the world through periodic flavor text based on location,
time of day, weather, and random events.
"""

import random
import logging
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from player import Player
    from world import World

logger = logging.getLogger('RealmsMUD.Ambient')

# Ambient messages by sector type
SECTOR_AMBIENTS = {
    'city': [
        "A merchant calls out, hawking their wares in the distance.",
        "You hear the clatter of cart wheels on cobblestones.",
        "A dog barks somewhere in the city.",
        "The smell of fresh bread wafts from a nearby bakery.",
        "A guard's patrol passes by in the distance.",
        "Children's laughter echoes from a nearby alley.",
        "A town crier announces the hour.",
        "You hear the rhythmic hammering of a blacksmith at work.",
        "A cat darts across the street and disappears into shadows.",
        "Two merchants argue over prices nearby.",
    ],
    'inside': [
        "Dust motes dance in a shaft of light.",
        "A floorboard creaks somewhere in the building.",
        "You hear muffled voices through the walls.",
        "A candle flickers, casting dancing shadows.",
        "The building settles with a soft groan.",
        "A mouse scurries along the baseboard.",
    ],
    'forest': [
        "Leaves rustle in the breeze above you.",
        "A bird calls out from the treetops.",
        "Something small scurries through the underbrush.",
        "Sunlight filters through the canopy, dappling the forest floor.",
        "You hear the distant sound of running water.",
        "An owl hoots somewhere in the trees.",
        "A squirrel chatters angrily at your presence.",
        "The forest seems to breathe around you.",
        "Branches creak and sway overhead.",
        "You catch a glimpse of a deer through the trees.",
    ],
    'field': [
        "Tall grass sways in the wind.",
        "A hawk circles lazily overhead.",
        "Insects buzz and hum around you.",
        "The wind carries the scent of wildflowers.",
        "A rabbit darts across your path and disappears.",
        "The sun beats down on the open plain.",
        "Clouds drift across the vast sky above.",
    ],
    'hills': [
        "The wind whistles across the rocky terrain.",
        "Small stones clatter down a nearby slope.",
        "You spot a mountain goat perched on a distant ridge.",
        "The air is thin but refreshing up here.",
        "An eagle cries out as it soars above.",
    ],
    'mountain': [
        "The cold wind bites at exposed skin.",
        "Snow crunches underfoot.",
        "An avalanche rumbles in the distance.",
        "The air is thin and each breath comes harder.",
        "Ice crystals glitter on nearby rocks.",
        "You can see for miles from this height.",
    ],
    'swamp': [
        "Something splashes in the murky water nearby.",
        "Mosquitoes buzz around your head incessantly.",
        "A frog croaks from somewhere in the muck.",
        "Bubbles rise from the stagnant water.",
        "The smell of decay hangs heavy in the air.",
        "Your feet squelch in the soft ground.",
        "A snake slithers through the reeds.",
    ],
    'water_swim': [
        "Fish dart away as you move through the water.",
        "Ripples spread across the water's surface.",
        "Water plants sway in the gentle current.",
        "A frog leaps from a nearby lily pad.",
    ],
    'underground': [
        "Water drips from the ceiling somewhere ahead.",
        "Your footsteps echo off the stone walls.",
        "You hear a distant rumble deep in the earth.",
        "A cold draft brushes past you.",
        "Shadows dance at the edge of your torchlight.",
        "Something skitters away in the darkness.",
        "The weight of the earth presses down above you.",
    ],
    'desert': [
        "Heat shimmers off the sand in the distance.",
        "A scorpion scuttles behind a rock.",
        "The wind kicks up a small dust devil.",
        "You lick parched lips as the sun beats down.",
        "A vulture circles lazily overhead.",
        "The sand shifts beneath your feet.",
    ],
}

# Time-of-day specific messages
TIME_AMBIENTS = {
    'dawn': [
        "The first rays of sunlight peek over the horizon.",
        "Dew glistens on everything as the world awakens.",
        "Birds begin their morning chorus.",
        "The air is cool and fresh with the promise of a new day.",
    ],
    'morning': [
        "The morning sun climbs higher in the sky.",
        "The world is bright and full of possibility.",
    ],
    'noon': [
        "The sun hangs directly overhead, casting short shadows.",
        "The heat of midday settles over everything.",
    ],
    'afternoon': [
        "Shadows begin to lengthen as the afternoon wears on.",
        "The heat of the day begins to fade.",
    ],
    'dusk': [
        "The sky blazes with oranges and reds as the sun sets.",
        "Long shadows stretch across the land.",
        "Nocturnal creatures begin to stir.",
    ],
    'night': [
        "Stars twinkle in the vast darkness overhead.",
        "The moon casts silver light across the land.",
        "Night sounds fill the air around you.",
        "The darkness seems to press in around you.",
    ],
}

# Weather-specific messages
WEATHER_AMBIENTS = {
    'raining': [
        "Rain patters steadily on everything around you.",
        "Thunder rumbles in the distance.",
        "You wipe rain from your face.",
        "Puddles are forming on the ground.",
    ],
    'stormy': [
        "Lightning flashes across the sky!",
        "Thunder crashes, making you jump.",
        "The wind howls and rain lashes at you.",
        "The storm rages around you.",
    ],
    'snowing': [
        "Snowflakes drift down from the grey sky.",
        "The world is hushed under a blanket of white.",
        "Your breath fogs in the cold air.",
    ],
    'foggy': [
        "Fog swirls around you, limiting visibility.",
        "Sounds seem muffled in the thick mist.",
        "Shapes loom out of the fog unexpectedly.",
    ],
}

# Combat/danger zone messages
DANGER_AMBIENTS = [
    "You sense something watching you from the shadows.",
    "A chill runs down your spine for no apparent reason.",
    "Your instincts scream that danger is near.",
    "You hear something moving in the darkness ahead.",
    "An uneasy feeling settles in your gut.",
]

# Peaceful zone messages
PEACEFUL_AMBIENTS = [
    "A sense of calm washes over you in this place.",
    "You feel safe here, at least for now.",
    "The tensions of adventure seem far away.",
]


class AmbientManager:
    """Manages ambient messages for the world."""
    
    # Track last ambient time per player to avoid spam
    _last_ambient = {}  # player_name -> timestamp
    
    @classmethod
    def get_ambient_message(cls, player: 'Player', world: 'World') -> Optional[str]:
        """Get an appropriate ambient message for the player's current situation."""
        if not player.room:
            return None
            
        messages = []
        weights = []
        
        # Get sector-based messages
        sector = player.room.sector_type or 'inside'
        
        # Map some sectors to our defined ones
        sector_map = {
            'water_noswim': 'water_swim',
            'flying': 'field',
        }
        mapped_sector = sector_map.get(sector, sector)
        
        if mapped_sector in SECTOR_AMBIENTS:
            messages.extend(SECTOR_AMBIENTS[mapped_sector])
            weights.extend([1.0] * len(SECTOR_AMBIENTS[mapped_sector]))
        
        # Add time-based messages
        if hasattr(world, 'game_time') and world.game_time:
            hour = world.game_time.hour
            if 5 <= hour < 7:
                time_key = 'dawn'
            elif 7 <= hour < 12:
                time_key = 'morning'
            elif 12 <= hour < 14:
                time_key = 'noon'
            elif 14 <= hour < 18:
                time_key = 'afternoon'
            elif 18 <= hour < 21:
                time_key = 'dusk'
            else:
                time_key = 'night'
            
            if time_key in TIME_AMBIENTS:
                messages.extend(TIME_AMBIENTS[time_key])
                weights.extend([0.5] * len(TIME_AMBIENTS[time_key]))  # Lower weight
        
        # Add weather-based messages (outdoor only)
        outdoor_sectors = {'field', 'forest', 'hills', 'mountain', 'water_swim', 
                          'water_noswim', 'flying', 'desert', 'swamp'}
        if sector in outdoor_sectors and player.room.zone:
            weather = player.room.zone.weather
            if weather:
                precip = getattr(weather, 'precipitation', 0)
                if isinstance(precip, str):
                    precip = int(precip) if precip.isdigit() else 0
                if precip > 0:
                    if precip > 2:
                        weather_key = 'stormy'
                    else:
                        weather_key = 'raining'
                    if weather_key in WEATHER_AMBIENTS:
                        messages.extend(WEATHER_AMBIENTS[weather_key])
                        weights.extend([0.8] * len(WEATHER_AMBIENTS[weather_key]))
        
        # Add danger zone messages if aggressive mobs nearby
        has_aggressive = any(
            'aggressive' in getattr(npc, 'flags', set()) 
            for npc in player.room.characters 
            if npc != player and hasattr(npc, 'flags')
        )
        if has_aggressive:
            messages.extend(DANGER_AMBIENTS)
            weights.extend([1.5] * len(DANGER_AMBIENTS))  # Higher weight
        
        # Add peaceful messages if in sanctuary
        if 'peaceful' in player.room.flags or 'sanctuary' in player.room.flags:
            messages.extend(PEACEFUL_AMBIENTS)
            weights.extend([0.8] * len(PEACEFUL_AMBIENTS))
        
        if not messages:
            return None
        
        # Weighted random selection
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for msg, weight in zip(messages, weights):
            cumulative += weight
            if r <= cumulative:
                return msg
        
        return random.choice(messages)
    
    @classmethod
    async def maybe_send_ambient(cls, player: 'Player', world: 'World', 
                                  chance: float = 0.03) -> bool:
        """
        Maybe send an ambient message to a player.
        
        Args:
            player: The player to potentially send a message to
            world: The game world
            chance: Probability of sending a message (default 3%)
            
        Returns:
            True if a message was sent, False otherwise
        """
        import time
        
        # Don't send if player is in combat
        if player.is_fighting:
            return False
        
        # Rate limit: minimum 30 seconds between ambient messages
        now = time.time()
        last = cls._last_ambient.get(player.name, 0)
        if now - last < 30:
            return False
        
        # Random chance check
        if random.random() > chance:
            return False
        
        # Get and send message
        message = cls.get_ambient_message(player, world)
        if message:
            c = player.config.COLORS
            await player.send(f"\r\n{c['white']}{message}{c['reset']}\r\n")
            cls._last_ambient[player.name] = now
            return True
        
        return False
    
    @classmethod
    async def ambient_tick(cls, world: 'World'):
        """
        Process ambient messages for all players.
        Called periodically (e.g., every few seconds).
        """
        for player in world.players.values():
            await cls.maybe_send_ambient(player, world)
