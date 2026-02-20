"""
Ambient Events System for Misthollow

Generates random atmospheric events that make the world feel alive:
- Traveling merchants passing through
- NPC conversations overheard  
- Animal behaviors
- Weather effects
- Environmental sounds
"""

import random
import asyncio
from typing import Optional, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from world import Room, World
    from player import Player

logger = logging.getLogger(__name__)


class AmbientEventManager:
    """Manages random ambient events in the game world."""
    
    # Events that can happen in city/town areas
    CITY_EVENTS = [
        "A merchant pushes a cart down the street, calling out his wares.",
        "Two citizens argue loudly nearby about the price of bread.",
        "A child runs past, laughing and chasing a stray cat.",
        "A guard patrol marches by, their armor clanking.",
        "The smell of fresh bread wafts from a nearby bakery.",
        "A bard somewhere nearby plays a lively tune.",
        "You hear the distant clang of a blacksmith's hammer.",
        "A dog barks somewhere in the distance.",
        "A town crier announces the hour.",
        "Merchants haggle loudly in a nearby stall.",
        "A group of adventurers discusses their latest quest.",
        "The clatter of wagon wheels echoes on cobblestones.",
    ]
    
    # Events for forest/wilderness areas
    FOREST_EVENTS = [
        "A bird takes flight from a nearby tree, startled by something.",
        "Leaves rustle in the underbrush as a small creature scurries away.",
        "A distant wolf howl echoes through the trees.",
        "Sunlight shifts through the canopy as clouds pass overhead.",
        "A woodpecker drums rhythmically on a distant tree.",
        "The wind carries the scent of wildflowers.",
        "A deer appears at the edge of your vision, then bounds away.",
        "Squirrels chatter angrily at each other in the branches.",
        "A hawk circles lazily overhead, hunting.",
        "The forest seems to sigh as a breeze passes through.",
    ]
    
    # Events for underground/dungeon areas
    UNDERGROUND_EVENTS = [
        "Water drips steadily somewhere in the darkness.",
        "A cold draft whispers past, carrying strange smells.",
        "You hear distant scratching sounds.",
        "Echoes of your own movements return from far away.",
        "A bat flutters past in the darkness.",
        "The rock groans as if under great pressure.",
        "Phosphorescent fungi pulse with a faint glow.",
        "The air feels thicker here, harder to breathe.",
        "You hear what might be whispers, or just the wind.",
        "Dust falls from the ceiling as something moves above.",
    ]
    
    # Events for swamp/marsh areas
    SWAMP_EVENTS = [
        "Bubbles rise from the murky water with a soft plop.",
        "A frog croaks loudly nearby, then falls silent.",
        "The buzz of insects intensifies momentarily.",
        "Something large moves beneath the water's surface.",
        "A bird calls out with an eerie, wailing cry.",
        "The stench of decay wafts on the humid air.",
        "Fireflies blink in the distance like tiny stars.",
        "A snake slithers away through the vegetation.",
    ]
    
    # Events for desert areas
    DESERT_EVENTS = [
        "A dust devil spins across the sand in the distance.",
        "The distant cry of a vulture echoes overhead.",
        "Heat shimmers distort the horizon.",
        "A scorpion scuttles across your path.",
        "The sand shifts as something moves beneath the surface.",
        "A cool breeze brings momentary relief from the heat.",
        "You hear the rattle of a snake's warning.",
    ]
    
    # Events for mountain/hill areas
    MOUNTAIN_EVENTS = [
        "A hawk soars past on the mountain updrafts.",
        "Loose rocks clatter down a nearby slope.",
        "The wind whistles through the crags above.",
        "An eagle's cry echoes off the rocky walls.",
        "Mountain goats scramble across distant ledges.",
        "The thin air makes you slightly dizzy.",
    ]
    
    # Events for water/coastal areas
    WATER_EVENTS = [
        "A fish jumps, splashing back into the water.",
        "Waves lap gently at the shore.",
        "A seabird calls out as it glides overhead.",
        "The smell of salt and seaweed fills the air.",
        "Distant whitecaps hint at deeper currents.",
        "A crab scuttles into hiding among the rocks.",
    ]
    
    # Night-specific events (can happen in addition to sector events)
    NIGHT_EVENTS = [
        "An owl hoots somewhere in the darkness.",
        "A shooting star streaks across the sky.",
        "The moon emerges from behind a cloud.",
        "Nocturnal creatures stir in the shadows.",
        "The stars seem to pulse with ancient light.",
        "A distant wolf pack howls at the moon.",
    ]
    
    # Storm-specific events
    STORM_EVENTS = [
        "Lightning illuminates the sky for a brief moment.",
        "Thunder rumbles ominously in the distance.",
        "The wind picks up, howling around you.",
        "Rain lashes down with renewed fury.",
        "A tree branch cracks somewhere nearby.",
    ]
    
    @staticmethod
    def get_event_for_room(room: 'Room', game_time=None, weather=None) -> Optional[str]:
        """Get a random ambient event appropriate for the room."""
        sector = getattr(room, 'sector_type', 'inside')
        
        # Map sectors to event lists
        sector_events = {
            'city': AmbientEventManager.CITY_EVENTS,
            'inside': AmbientEventManager.CITY_EVENTS,  # Use city events for indoors
            'forest': AmbientEventManager.FOREST_EVENTS,
            'field': AmbientEventManager.FOREST_EVENTS,  # Fields can use forest events
            'underground': AmbientEventManager.UNDERGROUND_EVENTS,
            'cave': AmbientEventManager.UNDERGROUND_EVENTS,
            'swamp': AmbientEventManager.SWAMP_EVENTS,
            'desert': AmbientEventManager.DESERT_EVENTS,
            'mountain': AmbientEventManager.MOUNTAIN_EVENTS,
            'hills': AmbientEventManager.MOUNTAIN_EVENTS,
            'water_swim': AmbientEventManager.WATER_EVENTS,
            'water_noswim': AmbientEventManager.WATER_EVENTS,
        }
        
        events = sector_events.get(sector, AmbientEventManager.FOREST_EVENTS)
        
        # Add night events if it's nighttime
        if game_time and hasattr(game_time, 'is_night') and game_time.is_night():
            if sector not in ('underground', 'cave', 'inside'):
                events = events + AmbientEventManager.NIGHT_EVENTS
        
        # Add storm events if stormy
        if weather:
            sky = getattr(weather, 'sky_condition', 'clear')
            if sky == 'stormy':
                events = events + AmbientEventManager.STORM_EVENTS
        
        return random.choice(events) if events else None


class AmbientEventScheduler:
    """Schedules and delivers ambient events to players."""
    
    def __init__(self, world: 'World'):
        self.world = world
        self.running = False
        self.task = None
        # Track last event time per player to avoid spam
        self._last_event = {}  # player_name -> tick
        self._current_tick = 0
        # Minimum ticks between events per player (30 = about 1 minute at 2-sec ticks)
        self.min_event_interval = 30
        # Chance of event per check (when interval has passed)
        self.event_chance = 0.15  # 15% chance
    
    async def start(self):
        """Start the ambient event scheduler."""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._event_loop())
        logger.info("Ambient event scheduler started")
    
    async def stop(self):
        """Stop the ambient event scheduler."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Ambient event scheduler stopped")
    
    async def _event_loop(self):
        """Main event loop - checks for events every few seconds."""
        while self.running:
            try:
                await asyncio.sleep(2)  # Check every 2 seconds
                self._current_tick += 1
                await self._process_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ambient event loop: {e}")
    
    async def _process_events(self):
        """Check if any players should receive ambient events."""
        if not self.world.players:
            return
        
        game_time = self.world.game_time if hasattr(self.world, 'game_time') else None
        
        for player in list(self.world.players.values()):
            try:
                # Skip if no room, sleeping, or in combat
                if not player.room:
                    continue
                if getattr(player, 'position', 'standing') in ('sleeping', 'fighting'):
                    continue
                if getattr(player, 'fighting', None):
                    continue
                
                # Check cooldown
                last_event = self._last_event.get(player.name, 0)
                if self._current_tick - last_event < self.min_event_interval:
                    continue
                
                # Random chance for event
                if random.random() > self.event_chance:
                    continue
                
                # Get weather for the zone
                weather = player.room.zone.weather if hasattr(player.room, 'zone') and player.room.zone else None
                
                # Generate and send event
                event = AmbientEventManager.get_event_for_room(player.room, game_time, weather)
                if event:
                    c = player.config.COLORS
                    await player.send(f"\r\n{c['cyan']}{event}{c['reset']}")
                    self._last_event[player.name] = self._current_tick
                    
            except Exception as e:
                logger.debug(f"Error sending ambient event to {player.name}: {e}")
