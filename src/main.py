#!/usr/bin/env python3
"""
RealmsMUD - A Fantasy CircleMUD-style Multi-User Dungeon
=========================================================
A complete fantasy MUD with character classes, combat, magic, quests, and more.
"""

import asyncio
import signal
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import MUDServer
from world import World
from config import Config
from web_map import WebMapServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../log/mud.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealmsMUD')

class RealmsMUD:
    """Main MUD application class."""
    
    def __init__(self):
        self.config = Config()
        self.world = None
        self.server = None
        self.web_map = None
        self.web_client = None
        self.admin_dashboard = None
        self.running = False
        self.start_time = None
        
    async def initialize(self):
        """Initialize the MUD world and systems."""
        logger.info("=" * 60)
        logger.info("RealmsMUD - Fantasy Multi-User Dungeon")
        logger.info("=" * 60)
        logger.info("Initializing game systems...")
        
        # Load the world
        self.world = World(self.config)
        await self.world.load()
        
        # Create the server
        self.server = MUDServer(self.world, self.config)

        # Start web map server
        self.web_map = WebMapServer(self.world, self.config)
        await self.web_map.start()
        # Expose for map updates
        self.world.web_map = self.web_map

        # Start admin dashboard
        try:
            from admin_dashboard import AdminDashboard
            self.admin_dashboard = AdminDashboard(self.world, port=4002)
            await self.admin_dashboard.start()
        except Exception as e:
            logger.warning(f"Admin dashboard failed to start: {e}")

        # Start web client
        try:
            from web_client import WebClient
            self.web_client = WebClient(mud_port=self.config.PORT, web_port=4003)
            await self.web_client.start()
        except Exception as e:
            logger.warning(f"Web client failed to start: {e}")

        logger.info("Initialization complete!")
        
    async def run(self):
        """Main game loop."""
        self.running = True
        self.start_time = datetime.now()
        
        logger.info(f"Starting server on port {self.config.PORT}...")
        
        # Start the server
        await self.server.start()
        
        # Main game tick loop
        tick_rate = 1.0 / self.config.TICKS_PER_SECOND
        combat_tick = 0
        regen_tick = 0
        minor_regen_tick = 0
        affect_tick = 0
        poison_tick = 0
        zone_tick = 0
        autosave_tick = 0
        time_tick = 0
        weather_tick = 0
        pet_tick = 0
        ambient_tick = 0

        try:
            while self.running:
                tick_start = asyncio.get_event_loop().time()

                # Process game ticks
                combat_tick += 1
                regen_tick += 1
                minor_regen_tick += 1
                affect_tick += 1
                poison_tick += 1
                zone_tick += 1
                autosave_tick += 1
                time_tick += 1
                weather_tick += 1
                pet_tick += 1
                ambient_tick += 1

                # Time tick (every 1 second - virtual game time)
                if time_tick >= self.config.TICKS_PER_SECOND:
                    await self.world.time_tick()
                    time_tick = 0

                # Weather tick (every 5 minutes)
                if weather_tick >= self.config.TICKS_PER_SECOND * 300:
                    await self.world.weather_tick()
                    weather_tick = 0

                # Pet tick (every 10 seconds)
                if pet_tick >= self.config.TICKS_PER_SECOND * 10:
                    await self.world.pet_tick()
                    pet_tick = 0

                # Combat tick (every 4 seconds - slowed for readability)
                if combat_tick >= self.config.TICKS_PER_SECOND * 4:
                    await self.world.combat_tick()
                    combat_tick = 0

                # Affect tick (DOT/HOT effects)
                if affect_tick >= self.config.TICKS_PER_SECOND * self.config.AFFECT_TICK_SECONDS:
                    await self.world.affect_tick()
                    affect_tick = 0

                # Poison tick (faster feedback)
                if poison_tick >= int(self.config.TICKS_PER_SECOND * self.config.POISON_TICK_SECONDS):
                    await self.world.poison_tick()
                    poison_tick = 0

                # Regen tick every 60 seconds (CircleMUD standard)
                if regen_tick >= self.config.TICKS_PER_SECOND * 60:
                    await self.world.regen_tick()
                    regen_tick = 0

                # Regen tick warning (3 seconds before)
                if regen_tick == self.config.TICKS_PER_SECOND * 57:
                    c = self.config.COLORS
                    for p in self.world.players.values():
                        if getattr(p, 'show_ticks', False):
                            await p.send(f"{c['cyan']}[TICK in 3s]{c['reset']}")

                # Minor regen tick every 5 seconds
                if minor_regen_tick >= self.config.TICKS_PER_SECOND * 5:
                    await self.world.minor_regen_tick()
                    minor_regen_tick = 0
                
                # Ambient message tick (every 10 seconds, 3% chance per player)
                if ambient_tick >= self.config.TICKS_PER_SECOND * 10:
                    from ambient import AmbientManager
                    await AmbientManager.ambient_tick(self.world)
                    ambient_tick = 0
                
                # NPC schedule tick (every game hour change - handled in time_tick)
                # Schedule processing happens when hour changes in world.time_tick()
                
                # Zone reset tick (every 15 minutes)
                if zone_tick >= self.config.TICKS_PER_SECOND * 900:
                    await self.world.zone_reset_tick()
                    zone_tick = 0
                
                # Autosave tick (every 5 minutes)
                if autosave_tick >= self.config.TICKS_PER_SECOND * 300:
                    await self.world.autosave()
                    autosave_tick = 0
                
                # Process player input and NPC AI
                await self.server.process_input()
                await self.world.process_npcs()
                
                # Maintain tick rate
                elapsed = asyncio.get_event_loop().time() - tick_start
                if elapsed < tick_rate:
                    await asyncio.sleep(tick_rate - elapsed)
                    
        except asyncio.CancelledError:
            logger.info("Shutdown requested...")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shut down the MUD."""
        logger.info("Shutting down RealmsMUD...")
        self.running = False
        
        if self.world:
            await self.world.save_all()
            
        if self.server:
            await self.server.shutdown()

        if self.web_map:
            await self.web_map.stop()

        if hasattr(self, 'web_client') and self.web_client:
            await self.web_client.stop()
            
        logger.info("Shutdown complete. Farewell!")

async def main():
    """Entry point."""
    mud = RealmsMUD()
    
    # Handle shutdown signals (Unix only - Windows uses KeyboardInterrupt)
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(mud.shutdown()))
    
    try:
        await mud.initialize()
        await mud.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received...")
        await mud.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    print("""
    ===============================================================

        ____  _____    _    _     __  __ ____    __  __ _   _ ____
       |  _ \\| ____|  / \\  | |   |  \\/  / ___|  |  \\/  | | | |  _ \\
       | |_) |  _|   / _ \\ | |   | |\\/| \\___ \\  | |\\/| | | | | | | |
       |  _ <| |___ / ___ \\| |___| |  | |___) | | |  | | |_| | |_| |
       |_| \\_\\_____/_/   \\_\\_____|_|  |_|____/  |_|  |_|\\___/|____/

           A Fantasy Multi-User Dungeon Adventure

    ===============================================================
    """)
    asyncio.run(main())
