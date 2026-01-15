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
        zone_tick = 0
        autosave_tick = 0
        time_tick = 0
        weather_tick = 0
        pet_tick = 0

        try:
            while self.running:
                tick_start = asyncio.get_event_loop().time()

                # Process game ticks
                combat_tick += 1
                regen_tick += 1
                zone_tick += 1
                autosave_tick += 1
                time_tick += 1
                weather_tick += 1
                pet_tick += 1

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

                # Combat tick (every 2 seconds)
                if combat_tick >= self.config.TICKS_PER_SECOND * 2:
                    await self.world.combat_tick()
                    combat_tick = 0

                # Regeneration tick (every 5 seconds)
                if regen_tick >= self.config.TICKS_PER_SECOND * 5:
                    await self.world.regen_tick()
                    regen_tick = 0
                
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
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ███████╗ █████╗ ██╗     ███╗   ███╗███████╗         ║
    ║   ██╔══██╗██╔════╝██╔══██╗██║     ████╗ ████║██╔════╝         ║
    ║   ██████╔╝█████╗  ███████║██║     ██╔████╔██║███████╗         ║
    ║   ██╔══██╗██╔══╝  ██╔══██║██║     ██║╚██╔╝██║╚════██║         ║
    ║   ██║  ██║███████╗██║  ██║███████╗██║ ╚═╝ ██║███████║         ║
    ║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝         ║
    ║                       MUD                                     ║
    ║                                                               ║
    ║           A Fantasy Multi-User Dungeon Adventure              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
