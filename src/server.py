"""
RealmsMUD Server
================
Handles network connections and player sessions.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import hashlib
import os
import json

from config import Config

logger = logging.getLogger('RealmsMUD.Server')

class Connection:
    """Represents a single client connection."""
    
    STATE_GET_NAME = 0
    STATE_CONFIRM_NAME = 1
    STATE_GET_PASSWORD = 2
    STATE_CONFIRM_PASSWORD = 3
    STATE_GET_RACE = 4
    STATE_GET_CLASS = 5
    STATE_ROLLING_STATS = 6
    STATE_PLAYING = 7
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.world = server.world
        self.config = server.config
        
        self.address = writer.get_extra_info('peername')
        self.connected_at = datetime.now()
        self.last_input = datetime.now()
        
        self.state = self.STATE_GET_NAME
        self.player = None
        self.input_buffer = []
        
        # Character creation temps
        self.temp_name = None
        self.temp_password = None
        self.temp_race = None
        self.temp_class = None
        
        logger.info(f"New connection from {self.address}")
        
    async def send(self, message: str, newline: bool = True):
        """Send a message to the client."""
        try:
            # Convert all newlines to \r\n for telnet compatibility
            message = message.replace('\r\n', '\n').replace('\n', '\r\n')
            if newline and not message.endswith('\r\n'):
                message += '\r\n'
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error sending to {self.address}: {e}")
            
    async def send_prompt(self):
        """Send the appropriate prompt based on state."""
        if self.state == self.STATE_PLAYING and self.player:
            c = self.config.COLORS
            hp_color = c['green'] if self.player.hp > self.player.max_hp * 0.5 else c['yellow'] if self.player.hp > self.player.max_hp * 0.25 else c['red']

            # Add enemy health if fighting
            enemy_status = ""
            if self.player.is_fighting and self.player.fighting:
                enemy = self.player.fighting
                enemy_hp_pct = (enemy.hp / enemy.max_hp) * 100
                enemy_color = c['bright_green'] if enemy_hp_pct > 75 else c['green'] if enemy_hp_pct > 50 else c['yellow'] if enemy_hp_pct > 25 else c['red']
                enemy_status = f" {c['white']}[{enemy_color}{enemy.name}: {enemy.hp}/{enemy.max_hp}{c['white']}]{c['reset']}"

            prompt = f"\r\n{hp_color}{self.player.hp}/{self.player.max_hp}hp {c['cyan']}{self.player.mana}/{self.player.max_mana}mp {c['yellow']}{self.player.move}/{self.player.max_move}mv{enemy_status}{c['reset']}> "
            await self.send(prompt, newline=False)
        else:
            await self.send("> ", newline=False)
            
    async def handle_input(self, line: str):
        """Process input based on current state."""
        line = line.strip()
        self.last_input = datetime.now()
        
        if self.state == self.STATE_GET_NAME:
            await self.handle_name(line)
        elif self.state == self.STATE_CONFIRM_NAME:
            await self.handle_confirm_name(line)
        elif self.state == self.STATE_GET_PASSWORD:
            await self.handle_password(line)
        elif self.state == self.STATE_CONFIRM_PASSWORD:
            await self.handle_confirm_password(line)
        elif self.state == self.STATE_GET_RACE:
            await self.handle_race(line)
        elif self.state == self.STATE_GET_CLASS:
            await self.handle_class(line)
        elif self.state == self.STATE_ROLLING_STATS:
            await self.handle_stats(line)
        elif self.state == self.STATE_PLAYING:
            await self.handle_command(line)
            
    async def handle_name(self, name: str):
        """Handle name entry."""
        if not name:
            await self.send("What name shall you be known by? ")
            return
            
        # Validate name
        if len(name) < 3 or len(name) > 12:
            await self.send("Names must be between 3 and 12 characters.")
            await self.send("What name shall you be known by? ")
            return
            
        if not name.isalpha():
            await self.send("Names must contain only letters.")
            await self.send("What name shall you be known by? ")
            return
            
        name = name.capitalize()
        self.temp_name = name
        
        # Check if player exists
        player_file = os.path.join(self.config.PLAYER_DIR, f"{name.lower()}.json")
        if os.path.exists(player_file):
            await self.send(f"Welcome back, {name}! Enter your password: ")
            self.state = self.STATE_GET_PASSWORD
        else:
            await self.send(f"Did I hear that right, {name}? (Y/N) ")
            self.state = self.STATE_CONFIRM_NAME
            
    async def handle_confirm_name(self, response: str):
        """Confirm new character name."""
        if response.lower() in ('y', 'yes'):
            await self.send("Choose a password: ")
            self.state = self.STATE_GET_PASSWORD
        else:
            self.temp_name = None
            await self.send("What name shall you be known by? ")
            self.state = self.STATE_GET_NAME
            
    async def handle_password(self, password: str):
        """Handle password entry."""
        if not password:
            await self.send("Password cannot be empty. Enter password: ")
            return
            
        player_file = os.path.join(self.config.PLAYER_DIR, f"{self.temp_name.lower()}.json")
        
        if os.path.exists(player_file):
            # Existing player - verify password
            from player import Player
            self.player = Player.load(self.temp_name, self.world)
            
            if self.player and self.player.check_password(password):
                await self.enter_game()
            else:
                await self.send("Wrong password!")
                self.player = None
                self.temp_name = None
                await self.send("What name shall you be known by? ")
                self.state = self.STATE_GET_NAME
        else:
            # New player - set password
            if len(password) < 4:
                await self.send("Password must be at least 4 characters. Enter password: ")
                return
            self.temp_password = password
            await self.send("Confirm password: ")
            self.state = self.STATE_CONFIRM_PASSWORD
            
    async def handle_confirm_password(self, password: str):
        """Confirm new character password."""
        if password == self.temp_password:
            await self.show_race_menu()
            self.state = self.STATE_GET_RACE
        else:
            await self.send("Passwords don't match. Enter password: ")
            self.temp_password = None
            self.state = self.STATE_GET_PASSWORD
            
    async def show_race_menu(self):
        """Display race selection menu."""
        c = self.config.COLORS
        await self.send(f"\r\n{c['cyan']}================================================================{c['reset']}")
        await self.send(f"{c['cyan']}                    Choose Your Race                          {c['reset']}")
        await self.send(f"{c['cyan']}================================================================{c['reset']}")

        for race_id, race in self.config.RACES.items():
            mods = ' '.join([f"{stat[:3].upper()}:{mod:+d}" for stat, mod in race['stat_mods'].items() if mod != 0])
            await self.send(f" {c['bright_green']}{race_id:<12}{c['white']}{race['description']}{c['reset']}")
            if mods:
                await self.send(f"              {c['yellow']}({mods}){c['reset']}")

        await self.send(f"{c['cyan']}================================================================{c['reset']}")
        await self.send(f"\r\n{c['white']}Enter race name: {c['reset']}")
        
    async def handle_race(self, race: str):
        """Handle race selection."""
        race = race.lower().replace(' ', '_')
        
        if race not in self.config.RACES:
            await self.send(f"'{race}' is not a valid race. Choose from: {', '.join(self.config.RACES.keys())}")
            await self.send("Enter race name: ")
            return
            
        self.temp_race = race
        await self.show_class_menu()
        self.state = self.STATE_GET_CLASS
        
    async def show_class_menu(self):
        """Display class selection menu."""
        c = self.config.COLORS
        await self.send(f"\r\n{c['cyan']}================================================================{c['reset']}")
        await self.send(f"{c['cyan']}                    Choose Your Class                         {c['reset']}")
        await self.send(f"{c['cyan']}================================================================{c['reset']}")

        for class_id, cls in self.config.CLASSES.items():
            await self.send(f" {c['bright_green']}{class_id:<12}{c['white']}{cls['description']}{c['reset']}")
            await self.send(f"              {c['yellow']}Prime: {cls['prime_stat'].upper():<3} HP:{cls['hit_dice']:>2}  MP:{cls['mana_dice']:>2}{c['reset']}")

        await self.send(f"{c['cyan']}================================================================{c['reset']}")
        await self.send(f"\r\n{c['white']}Enter class name: {c['reset']}")
        
    async def handle_class(self, char_class: str):
        """Handle class selection."""
        char_class = char_class.lower()
        
        if char_class not in self.config.CLASSES:
            await self.send(f"'{char_class}' is not a valid class. Choose from: {', '.join(self.config.CLASSES.keys())}")
            await self.send("Enter class name: ")
            return
            
        self.temp_class = char_class
        await self.show_stats()
        self.state = self.STATE_ROLLING_STATS
        
    async def show_stats(self):
        """Show rolled stats and ask for confirmation."""
        import random
        
        # Roll stats
        self.temp_stats = {}
        for stat in ['str', 'int', 'wis', 'dex', 'con', 'cha']:
            # Roll 4d6, drop lowest
            rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)[:3]
            base = sum(rolls)
            # Apply racial modifiers
            mod = self.config.RACES[self.temp_race]['stat_mods'].get(stat, 0)
            self.temp_stats[stat] = max(self.config.MIN_STAT, min(self.config.MAX_STAT, base + mod))
        
        c = self.config.COLORS
        await self.send(f"\r\n{c['cyan']}═══════════════ Your Statistics ═══════════════{c['reset']}")
        await self.send(f"{c['bright_red']}Strength:     {self.temp_stats['str']:>2}{c['reset']}")
        await self.send(f"{c['bright_blue']}Intelligence: {self.temp_stats['int']:>2}{c['reset']}")
        await self.send(f"{c['bright_cyan']}Wisdom:       {self.temp_stats['wis']:>2}{c['reset']}")
        await self.send(f"{c['bright_green']}Dexterity:    {self.temp_stats['dex']:>2}{c['reset']}")
        await self.send(f"{c['bright_yellow']}Constitution: {self.temp_stats['con']:>2}{c['reset']}")
        await self.send(f"{c['bright_magenta']}Charisma:     {self.temp_stats['cha']:>2}{c['reset']}")
        await self.send(f"{c['cyan']}═════════════════════════════════════════════{c['reset']}")
        await self.send(f"\r\n{c['white']}Accept these stats? (Y)es, (N)o to reroll: {c['reset']}")
        
    async def handle_stats(self, response: str):
        """Handle stat confirmation."""
        if response.lower() in ('y', 'yes'):
            await self.create_character()
        else:
            await self.show_stats()
            
    async def create_character(self):
        """Create the new character."""
        from player import Player
        
        self.player = Player.create_new(
            name=self.temp_name,
            password=self.temp_password,
            race=self.temp_race,
            char_class=self.temp_class,
            stats=self.temp_stats,
            world=self.world
        )
        
        await self.player.save()
        await self.enter_game()
        
    async def enter_game(self):
        """Enter the game world."""
        self.state = self.STATE_PLAYING
        self.player.connection = self
        
        # Add player to world
        await self.world.add_player(self.player)
        
        # Show welcome message
        c = self.config.COLORS
        await self.send(f"\r\n{c['bright_cyan']}══════════════════════════════════════════════════════════════{c['reset']}")
        await self.send(f"{c['bright_yellow']}  Welcome to RealmsMUD, {self.player.name}!{c['reset']}")
        await self.send(f"{c['white']}  Type 'help' for a list of commands.{c['reset']}")
        await self.send(f"{c['bright_cyan']}══════════════════════════════════════════════════════════════{c['reset']}\r\n")
        
        # Move to starting room and look
        room = self.world.get_room(self.player.room_vnum or self.config.STARTING_ROOM)
        if room:
            self.player.room = room
            room.characters.append(self.player)
            
            # Announce arrival
            await room.send_to_room(f"{self.player.name} has entered the realm.", exclude=[self.player])
            
            # Show room
            await self.player.do_look([])
            
        await self.send_prompt()
        
    async def handle_command(self, line: str):
        """Handle a game command."""
        if not line:
            await self.send_prompt()
            return

        # Handle ! to repeat last command
        if line.strip() == '!':
            if self.player.last_command:
                line = self.player.last_command
                await self.send(f"Repeating: {line}\r\n")
            else:
                await self.send("No previous command to repeat.\r\n")
                await self.send_prompt()
                return

        # Store command for ! repeat
        self.player.last_command = line

        # Parse command and arguments
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Check for alias substitution
        if cmd in self.player.custom_aliases:
            aliased_command = self.player.custom_aliases[cmd]
            # Reconstruct line with alias expanded + original args
            expanded_line = aliased_command
            if args:
                expanded_line += ' ' + ' '.join(args)
            # Re-parse with alias expanded
            parts = expanded_line.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

        # Execute command
        await self.player.execute_command(cmd, args)
        await self.send_prompt()
        
    async def disconnect(self):
        """Handle disconnection."""
        logger.info(f"Connection closed: {self.address}")
        
        if self.player:
            # Save and remove from world
            await self.player.save()
            await self.world.remove_player(self.player)
            
            # Announce departure
            if self.player.room:
                await self.player.room.send_to_room(
                    f"{self.player.name} has left the realm.",
                    exclude=[self.player]
                )
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass


class MUDServer:
    """Main MUD server class."""
    
    def __init__(self, world, config: Config):
        self.world = world
        self.config = config
        self.connections: Dict[str, Connection] = {}
        self.server = None
        
    async def start(self):
        """Start the server."""
        self.server = await asyncio.start_server(
            self.handle_connection,
            self.config.HOST,
            self.config.PORT
        )
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"Server listening on {addr[0]}:{addr[1]}")
        
        asyncio.create_task(self.server.serve_forever())
        
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new connection."""
        conn = Connection(reader, writer, self)
        conn_id = f"{conn.address[0]}:{conn.address[1]}"
        self.connections[conn_id] = conn
        
        try:
            # Send welcome screen
            await self.send_welcome(conn)
            
            # Read input loop
            while True:
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=300.0)
                    if not data:
                        break
                    line = data.decode('utf-8', errors='ignore').strip()
                    await conn.handle_input(line)
                except asyncio.TimeoutError:
                    await conn.send("\r\nConnection timed out. Goodbye!\r\n")
                    break
                except Exception as e:
                    logger.error(f"Error handling input: {e}")
                    break
                    
        finally:
            await conn.disconnect()
            if conn_id in self.connections:
                del self.connections[conn_id]
                
    async def send_welcome(self, conn: Connection):
        """Send the welcome screen."""
        c = self.config.COLORS
        welcome = f"""
{c['bright_cyan']}
    ===================================================================

        ____  _____    _    _     __  __ ____    __  __ _   _ ____
       |  _ \\| ____|  / \\  | |   |  \\/  / ___|  |  \\/  | | | |  _ \\
       | |_) |  _|   / _ \\ | |   | |\\/| \\___ \\  | |\\/| | | | | | | |
       |  _ <| |___ / ___ \\| |___| |  | |___) | | |  | | |_| | |_| |
       |_| \\_\\_____/_/   \\_\\_____|_|  |_|____/  |_|  |_|\\___/|____/

    ===================================================================

    {c['white']}Welcome, brave adventurer, to a world of fantasy and magic!
    Explore vast dungeons, battle fearsome creatures, and
    forge your legend in the Realms!

    {c['bright_green']}* 8 unique races with special abilities
    * 8 character classes to master
    * Hundreds of zones to explore
    * Epic quests and legendary items

{c['bright_cyan']}    ===================================================================
{c['reset']}

{c['white']}What name shall you be known by?{c['reset']} """

        await conn.send(welcome, newline=False)
        
    async def process_input(self):
        """Process input from all connections (called each tick)."""
        # Input is handled asynchronously per connection
        pass
        
    async def shutdown(self):
        """Shut down the server."""
        logger.info("Shutting down server...")
        
        # Disconnect all clients
        for conn in list(self.connections.values()):
            await conn.send("\r\n\r\nServer shutting down. Goodbye!\r\n")
            await conn.disconnect()
            
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    async def broadcast(self, message: str, exclude=None):
        """Broadcast a message to all players."""
        for conn in self.connections.values():
            if conn.player and (exclude is None or conn.player not in exclude):
                await conn.send(f"\r\n{message}\r\n")
