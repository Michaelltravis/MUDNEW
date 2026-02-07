"""
NPC Schedule System for RealmsMUD

Makes NPCs feel alive by giving them daily routines:
- Merchants open/close their shops
- Guards change patrol routes
- Innkeepers go to bed
- Farmers work fields during day, sleep at night
"""

import random
import logging
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world import World, Room
    from mobs import Mobile
    from time_system import GameTime

logger = logging.getLogger(__name__)


class NPCSchedule:
    """Defines a daily schedule for an NPC."""
    
    def __init__(self, npc_vnum: int, schedules: List[Dict]):
        """
        Args:
            npc_vnum: The NPC's vnum
            schedules: List of schedule entries like:
                {'hours': (8, 18), 'room': 3050, 'activity': 'working'}
                {'hours': (18, 22), 'room': 3001, 'activity': 'relaxing'}
                {'hours': (22, 8), 'room': 3100, 'activity': 'sleeping'}
        """
        self.npc_vnum = npc_vnum
        self.schedules = schedules
    
    def get_current_activity(self, hour: int) -> Optional[Dict]:
        """Get the schedule entry for the current hour."""
        for entry in self.schedules:
            start, end = entry['hours']
            if start <= end:
                # Normal range (e.g., 8-18)
                if start <= hour < end:
                    return entry
            else:
                # Wrapping range (e.g., 22-8)
                if hour >= start or hour < end:
                    return entry
        return None


# Pre-defined schedules for common NPC types
DEFAULT_SCHEDULES = {
    # Shopkeepers - work during day, go home at night
    'shopkeeper': [
        {'hours': (7, 20), 'activity': 'working', 'message': 'opens the shop'},
        {'hours': (20, 7), 'activity': 'closed', 'message': 'closes the shop for the night'},
    ],
    
    # Guards - patrol during day and evening, rest at night
    'guard': [
        {'hours': (6, 22), 'activity': 'patrolling', 'message': 'begins patrol'},
        {'hours': (22, 6), 'activity': 'resting', 'message': 'goes off duty'},
    ],
    
    # Innkeepers - always working but mention different activities
    'innkeeper': [
        {'hours': (6, 12), 'activity': 'cleaning', 'message': 'starts cleaning the common room'},
        {'hours': (12, 22), 'activity': 'serving', 'message': 'tends to the evening crowd'},
        {'hours': (22, 6), 'activity': 'night_duty', 'message': 'mans the night desk'},
    ],
    
    # Farmers - early risers, work fields, sleep early
    'farmer': [
        {'hours': (5, 12), 'activity': 'field_work', 'message': 'heads out to the fields'},
        {'hours': (12, 14), 'activity': 'lunch', 'message': 'takes a lunch break'},
        {'hours': (14, 19), 'activity': 'field_work', 'message': 'returns to work'},
        {'hours': (19, 5), 'activity': 'sleeping', 'message': 'retires for the night'},
    ],
    
    # Priests - services in morning and evening
    'priest': [
        {'hours': (6, 9), 'activity': 'morning_service', 'message': 'begins morning prayers'},
        {'hours': (9, 17), 'activity': 'duties', 'message': 'attends to temple duties'},
        {'hours': (17, 20), 'activity': 'evening_service', 'message': 'leads evening vespers'},
        {'hours': (20, 6), 'activity': 'meditation', 'message': 'retreats for meditation'},
    ],
}


class NPCScheduleManager:
    """Manages NPC schedules and movements."""
    
    def __init__(self, world: 'World'):
        self.world = world
        # Track NPC states: vnum -> {'current_activity': str, 'home_room': int}
        self._npc_states: Dict[int, Dict] = {}
        # Custom schedules by vnum
        self._custom_schedules: Dict[int, NPCSchedule] = {}
    
    def register_schedule(self, npc_vnum: int, schedule: NPCSchedule):
        """Register a custom schedule for an NPC."""
        self._custom_schedules[npc_vnum] = schedule
    
    def get_schedule_type(self, npc: 'Mobile') -> Optional[str]:
        """Determine what type of schedule an NPC should follow based on their flags/role."""
        if not npc:
            return None
        
        flags = getattr(npc, 'flags', set())
        name_lower = npc.name.lower() if npc.name else ''
        
        # Check for shopkeeper
        if getattr(npc, 'shopkeeper', False) or 'shop' in name_lower:
            return 'shopkeeper'
        
        # Check for guard
        if 'guard' in flags or 'guard' in name_lower or 'soldier' in name_lower:
            return 'guard'
        
        # Check for innkeeper/bartender
        if 'innkeeper' in name_lower or 'bartender' in name_lower or 'barkeep' in name_lower:
            return 'innkeeper'
        
        # Check for farmer
        if 'farmer' in name_lower or 'peasant' in name_lower:
            return 'farmer'
        
        # Check for priest/cleric
        if 'priest' in name_lower or 'cleric' in name_lower or 'monk' in name_lower:
            return 'priest'
        
        return None
    
    async def process_schedules(self, game_time: 'GameTime'):
        """Process NPC schedules based on current game time."""
        if not game_time:
            return
        
        hour = game_time.hour
        
        # Process all mobs in the world
        for zone in self.world.zones.values():
            for room in zone.rooms.values():
                for char in list(room.characters):
                    if hasattr(char, 'vnum') and not hasattr(char, 'connection'):
                        await self._process_npc_schedule(char, hour)
    
    async def _process_npc_schedule(self, npc: 'Mobile', hour: int):
        """Process schedule for a single NPC."""
        vnum = getattr(npc, 'vnum', 0)
        
        # Check for custom schedule
        if vnum in self._custom_schedules:
            schedule = self._custom_schedules[vnum]
            activity = schedule.get_current_activity(hour)
        else:
            # Use default schedule based on NPC type
            schedule_type = self.get_schedule_type(npc)
            if not schedule_type:
                return
            
            schedules = DEFAULT_SCHEDULES.get(schedule_type, [])
            activity = None
            for entry in schedules:
                start, end = entry['hours']
                if start <= end:
                    if start <= hour < end:
                        activity = entry
                        break
                else:
                    if hour >= start or hour < end:
                        activity = entry
                        break
        
        if not activity:
            return
        
        # Check if activity changed
        state = self._npc_states.get(vnum, {})
        current_activity = state.get('current_activity')
        
        if current_activity != activity.get('activity'):
            # Activity changed - announce it
            message = activity.get('message')
            if message and npc.room:
                c = npc.config.COLORS if hasattr(npc, 'config') else {}
                color = c.get('cyan', '') if c else ''
                reset = c.get('reset', '') if c else ''
                await npc.room.send_to_room(
                    f"{color}{npc.name} {message}.{reset}"
                )
            
            # Update state
            self._npc_states[vnum] = {
                'current_activity': activity.get('activity'),
                'home_room': state.get('home_room', npc.room.vnum if npc.room else 0)
            }
            
            # Handle shop closing/opening
            if activity.get('activity') == 'closed':
                npc.shop_closed = True
            elif activity.get('activity') == 'working':
                npc.shop_closed = False


async def schedule_tick(world: 'World'):
    """Called periodically to process NPC schedules."""
    if not hasattr(world, '_schedule_manager'):
        world._schedule_manager = NPCScheduleManager(world)
    
    game_time = getattr(world, 'game_time', None)
    if game_time:
        await world._schedule_manager.process_schedules(game_time)
