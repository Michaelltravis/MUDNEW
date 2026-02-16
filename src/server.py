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
    # Account system states
    STATE_ACCOUNT_PASSWORD = 10
    STATE_SELECT_CHAR = 11
    STATE_CREATE_CHAR_NAME = 12
    STATE_MIGRATE_OFFER = 13
    STATE_CHANGE_PASSWORD = 14
    STATE_CONFIRM_NEW_PASSWORD = 15
    STATE_CONFIRM_DELETE = 16
    
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
        
        # Account system temps
        self.account = None
        self.temp_account_name = None
        
        logger.info(f"New connection from {self.address}")
        
    async def send(self, message: str, newline: bool = True):
        """Send a message to the client."""
        try:
            if message is None:
                return
            # Convert all newlines to \r\n for telnet compatibility
            message = message.replace('\r\n', '\n').replace('\n', '\r\n')
            if newline and not message.endswith('\r\n'):
                message += '\r\n'
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            logger.debug(f"Connection lost while sending to {self.address}")
        except Exception as e:
            logger.error(f"Error sending to {self.address}: {e}")
            
    async def send_prompt(self):
        """Send the appropriate prompt based on state."""
        if self.state == self.STATE_PLAYING and self.player:
            # Respect prompt toggle
            if not getattr(self.player, 'prompt_enabled', True):
                return
            
            c = self.config.COLORS
            hp_color = c['green'] if self.player.hp > self.player.max_hp * 0.5 else c['yellow'] if self.player.hp > self.player.max_hp * 0.25 else c['red']

            # Sneaking indicator
            sneak_status = ""
            if hasattr(self.player, 'flags') and 'sneaking' in self.player.flags:
                sneak_status = f" {c['bright_black']}[sneaking]{c['reset']}"
            
            # Add enemy health if fighting
            enemy_status = ""
            if self.player.is_fighting and self.player.fighting:
                enemy = self.player.fighting
                enemy_hp_pct = (enemy.hp / enemy.max_hp) * 100
                enemy_color = c['bright_green'] if enemy_hp_pct > 75 else c['green'] if enemy_hp_pct > 50 else c['yellow'] if enemy_hp_pct > 25 else c['red']
                enemy_status = f" {c['white']}[{enemy_color}{enemy.name}: {enemy.hp}/{enemy.max_hp}{c['white']}]{c['reset']}"

            # Custom prompt support
            custom = getattr(self.player, 'custom_prompt', None)
            if custom:
                hp_pct = int((self.player.hp / self.player.max_hp) * 100) if self.player.max_hp > 0 else 0
                mana_pct = int((self.player.mana / self.player.max_mana) * 100) if self.player.max_mana > 0 else 0
                move_pct = int((self.player.move / self.player.max_move) * 100) if self.player.max_move > 0 else 0
                
                prompt = custom
                prompt = prompt.replace('%h', str(self.player.hp))
                prompt = prompt.replace('%H', str(self.player.max_hp))
                prompt = prompt.replace('%m', str(self.player.mana))
                prompt = prompt.replace('%M', str(self.player.max_mana))
                prompt = prompt.replace('%v', str(self.player.move))
                prompt = prompt.replace('%V', str(self.player.max_move))
                prompt = prompt.replace('%g', str(self.player.gold))
                prompt = prompt.replace('%x', str(self.player.exp))
                prompt = prompt.replace('%p', str(hp_pct))
                prompt = prompt.replace('%q', str(mana_pct))
                prompt = prompt.replace('%r', str(move_pct))
                prompt = prompt.replace('%n', '\r\n')
                
                prompt = f"\r\n{prompt} {enemy_status}{c['reset']}> "
                await self.send(prompt, newline=False)
                return

            # Warrior Momentum display in prompt
            momentum_status = ""
            if getattr(self.player, 'char_class', '').lower() == 'warrior':
                mom = getattr(self.player, 'momentum', 0)
                if mom > 0:
                    filled = '█' * mom
                    empty = '░' * (10 - mom)
                    momentum_status = f" {c['bright_yellow']}[Momentum: {filled}{empty} {mom}/10]{c['reset']}"
                    if getattr(self.player, 'unstoppable_rounds', 0) > 0:
                        momentum_status += f" {c['bright_red']}★UNSTOPPABLE★{c['reset']}"

            prompt = f"\r\n{hp_color}{self.player.hp}/{self.player.max_hp}hp {c['cyan']}{self.player.mana}/{self.player.max_mana}mp {c['yellow']}{self.player.move}/{self.player.max_move}mv{sneak_status}{momentum_status}{enemy_status}{c['reset']}> "
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
            await self.handle_confirm_new_char_password(line)
        elif self.state == self.STATE_GET_RACE:
            await self.handle_race(line)
        elif self.state == self.STATE_GET_CLASS:
            await self.handle_class(line)
        elif self.state == self.STATE_ROLLING_STATS:
            await self.handle_stats(line)
        elif self.state == self.STATE_PLAYING:
            await self.handle_command(line)
        # Account system states
        elif self.state == self.STATE_ACCOUNT_PASSWORD:
            await self.handle_account_password(line)
        elif self.state == self.STATE_SELECT_CHAR:
            await self.handle_select_char(line)
        elif self.state == self.STATE_CREATE_CHAR_NAME:
            await self.handle_create_char_name(line)
        elif self.state == self.STATE_MIGRATE_OFFER:
            await self.handle_migrate_offer(line)
        elif self.state == self.STATE_CHANGE_PASSWORD:
            await self.handle_change_password(line)
        elif self.state == self.STATE_CONFIRM_NEW_PASSWORD:
            await self.handle_confirm_password(line)
        elif self.state == self.STATE_CONFIRM_DELETE:
            await self.handle_confirm_delete(line)
            
    async def handle_name(self, name: str):
        """Handle name/account entry."""
        if not name:
            await self.send("Enter account name (or character name): ")
            return
            
        # Validate name
        if len(name) < 3 or len(name) > 12:
            await self.send("Names must be between 3 and 12 characters.")
            await self.send("Enter account name (or character name): ")
            return
            
        if not name.isalpha():
            await self.send("Names must contain only letters.")
            await self.send("Enter account name (or character name): ")
            return
        
        name_lower = name.lower()
        name_cap = name.capitalize()
        
        # Check for account first
        from accounts import Account
        if Account.exists(name_lower):
            self.temp_account_name = name_lower
            await self.send(f"Account password: ")
            self.state = self.STATE_ACCOUNT_PASSWORD
            return
        
        # Check for legacy player file (not yet migrated to account)
        player_file = os.path.join(self.config.PLAYER_DIR, f"{name_lower}.json")
        if os.path.exists(player_file):
            self.temp_name = name_cap
            await self.send(f"Welcome back, {name_cap}! Enter your password: ")
            self.state = self.STATE_GET_PASSWORD
            return
        
        # New player/account - offer to create account
        self.temp_account_name = name_lower
        self.temp_name = name_cap
        await self.send(f"'{name_cap}' is a new name. Create account? (Y/N) ")
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
                # Check if already has account
                if hasattr(self.player, 'account_name') and self.player.account_name:
                    await self.enter_game()
                else:
                    # Offer migration to account system
                    self.temp_password = password
                    await self.send("\r\n")
                    await self.send("Would you like to create an account for multiple characters? (Y/N)")
                    await self.send("(You can always do this later with 'account create')")
                    self.state = self.STATE_MIGRATE_OFFER
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
            
    async def handle_confirm_new_char_password(self, password: str):
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

        for i, (race_id, race) in enumerate(self.config.RACES.items(), 1):
            mods = ' '.join([f"{stat[:3].upper()}:{mod:+d}" for stat, mod in race['stat_mods'].items() if mod != 0])
            await self.send(f" {c['bright_yellow']}{i}){c['reset']} {c['bright_green']}{race_id:<12}{c['white']}{race['description']}{c['reset']}")
            if mods:
                await self.send(f"              {c['yellow']}({mods}){c['reset']}")

        await self.send(f"{c['cyan']}================================================================{c['reset']}")
        await self.send(f"\r\n{c['white']}Enter race name or number: {c['reset']}")
        
    async def handle_race(self, race: str):
        """Handle race selection."""
        race = race.strip().lower().replace(' ', '_')
        
        # Accept number selection
        if race.isdigit():
            idx = int(race) - 1
            race_list = list(self.config.RACES.keys())
            if 0 <= idx < len(race_list):
                race = race_list[idx]
            else:
                await self.send(f"Invalid selection. Choose 1-{len(race_list)} or enter race name.")
                await self.send("Enter race name or number: ")
                return
        
        if race not in self.config.RACES:
            await self.send(f"'{race}' is not a valid race. Choose from: {', '.join(self.config.RACES.keys())}")
            await self.send("Enter race name or number: ")
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

        for i, (class_id, cls) in enumerate(self.config.CLASSES.items(), 1):
            await self.send(f" {c['bright_yellow']}{i}){c['reset']} {c['bright_green']}{class_id:<12}{c['white']}{cls['description']}{c['reset']}")
            await self.send(f"              {c['yellow']}Prime: {cls['prime_stat'].upper():<3} HP:{cls['hit_dice']:>2}  MP:{cls['mana_dice']:>2}{c['reset']}")

        await self.send(f"{c['cyan']}================================================================{c['reset']}")
        await self.send(f"\r\n{c['white']}Enter class name or number: {c['reset']}")
        
    async def handle_class(self, char_class: str):
        """Handle class selection."""
        char_class = char_class.strip().lower()
        
        # Accept number selection
        if char_class.isdigit():
            idx = int(char_class) - 1
            class_list = list(self.config.CLASSES.keys())
            if 0 <= idx < len(class_list):
                char_class = class_list[idx]
            else:
                await self.send(f"Invalid selection. Choose 1-{len(class_list)} or enter class name.")
                await self.send("Enter class name or number: ")
                return
        
        if char_class not in self.config.CLASSES:
            await self.send(f"'{char_class}' is not a valid class. Choose from: {', '.join(self.config.CLASSES.keys())}")
            await self.send("Enter class name or number: ")
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
        
        # For account-based characters, use a placeholder password
        # (account authentication protects the character)
        password = self.temp_password if self.temp_password else "account_protected"
        
        self.player = Player.create_new(
            name=self.temp_name,
            password=password,
            race=self.temp_race,
            char_class=self.temp_class,
            stats=self.temp_stats,
            world=self.world
        )
        
        # Link to account if creating via account flow
        if self.account:
            self.player.account_name = self.account.account_name
            self.account.add_character(self.player.name)
            self.account.save()
        
        await self.player.save()
        await self.enter_game()
        
    async def enter_game(self):
        """Enter the game world."""
        self.state = self.STATE_PLAYING
        self.player.connection = self
        
        # Track login info for account system
        from datetime import datetime
        self.player.last_login = datetime.now()
        self.player.last_host = self.address[0] if self.address else 'Unknown'
        
        # Move to starting room before adding to world
        room = self.world.get_room(self.player.room_vnum or self.config.STARTING_ROOM)
        if room:
            self.player.room = room

        # Add player to world
        await self.world.add_player(self.player)
        
        # Show welcome message
        c = self.config.COLORS
        await self.send(f"\r\n{c['bright_cyan']}══════════════════════════════════════════════════════════════{c['reset']}")
        await self.send(f"{c['bright_yellow']}  Welcome to RealmsMUD, {self.player.name}!{c['reset']}")
        await self.send(f"{c['white']}  A world of quests, combat, crafting, and adventure awaits.{c['reset']}")
        await self.send(f"{c['white']}  Type {c['bright_green']}help newbie{c['white']} for a new player guide, or {c['bright_green']}hint{c['white']} for tips.{c['reset']}")
        await self.send(f"{c['bright_cyan']}══════════════════════════════════════════════════════════════{c['reset']}\r\n")

        # Process rent charges from previous session
        try:
            rent_data = getattr(self.player, 'rent_data', None)
            if rent_data and rent_data.get('rented'):
                from datetime import datetime
                rent_time = datetime.fromisoformat(rent_data['rent_time'])
                elapsed = (datetime.now() - rent_time).total_seconds()
                days_elapsed = max(1, elapsed / 86400)  # At least 1 day charge
                daily_cost = rent_data.get('daily_cost', 0)
                total_charge = int(daily_cost * days_elapsed)

                if total_charge > 0:
                    if self.player.gold >= total_charge:
                        self.player.gold -= total_charge
                        await self.send(f"{c['bright_yellow']}The innkeeper collected {total_charge} gold for {days_elapsed:.1f} days of storage.{c['reset']}")
                    else:
                        # Player can't afford - drop random items
                        shortfall = total_charge - self.player.gold
                        self.player.gold = 0
                        dropped = 0
                        while shortfall > 0 and self.player.inventory:
                            item = self.player.inventory.pop()
                            item_rent = 10  # base value of dropped item
                            shortfall -= getattr(item, 'value', getattr(item, 'cost', 50))
                            dropped += 1
                        await self.send(f"{c['red']}You couldn't afford {total_charge} gold in rent!{c['reset']}")
                        if dropped:
                            await self.send(f"{c['red']}The innkeeper confiscated {dropped} item(s) to cover the debt.{c['reset']}")
                        await self.send(f"{c['yellow']}You have {self.player.gold} gold remaining.{c['reset']}")

                # Clear rent data
                self.player.rent_data = None
        except Exception as e:
            import logging
            logging.getLogger('RealmsMUD').error(f"Rent processing error: {e}")

        if room:
            room.characters.append(self.player)
            
            # Initialize explored_rooms and add starting room for map
            if not hasattr(self.player, 'explored_rooms'):
                self.player.explored_rooms = set()
            self.player.explored_rooms.add(room.vnum)
            
            # Announce arrival
            await room.send_to_room(f"{self.player.name} has entered the realm.", exclude=[self.player])
            
            # Daily login bonus check
            try:
                from daily import DailyBonusManager
                await DailyBonusManager.check_daily_bonus(self.player)
            except Exception:
                pass
            
            # Mark explored on login
            try:
                from achievements import AchievementManager
                await AchievementManager.check_exploration(self.player, getattr(self.player.room, 'vnum', 0))
            except Exception:
                pass

            # Waypoint discovery
            try:
                from travel import discover_waypoint
                discovered = discover_waypoint(self.player, getattr(self.player.room, 'vnum', 0))
                if discovered:
                    key, info = discovered
                    await self.player.send(f"{c['bright_cyan']}Waypoint discovered: {info['name']}{c['reset']}")
            except Exception:
                pass

            # Show room
            await self.player.do_look([])

            # Room entry triggers (Sage Aldric greeting, etc.)
            try:
                from commands import CommandHandler
                await CommandHandler._room_entry_triggers(self.player)
            except Exception as e:
                import logging
                logging.getLogger('RealmsMUD').error(f"Room entry trigger error: {e}")

            # Web map update
            if hasattr(self.world, 'web_map') and self.world.web_map:
                await self.world.web_map.notify_player(self.player)
            
            # Send map sync signal for web client (hidden control message)
            await self.send(f"\x1b]MAPSYNC:{self.player.name}\x07")
            
            # Start tutorial for new players (level 1, no quests completed)
            if self.player.level == 1 and not getattr(self.player, 'quests_completed', []):
                try:
                    from quests import QuestManager
                    await QuestManager.start_tutorial(self.player)
                except Exception:
                    pass

            # Check for unread mail
            try:
                from mail_system import MailManager
                unread = MailManager.get_unread_count(self.player.name)
                if unread > 0:
                    await self.send(f"{c['bright_yellow']}You have {unread} unread mail message{'s' if unread != 1 else ''}! Type 'mail read' to read.{c['reset']}")
            except Exception:
                pass

            # Show a tip to newer players
            try:
                if self.player.level < 15:
                    from tips import TipManager
                    await TipManager.maybe_show_tip(self.player, chance=0.3)
            except Exception:
                pass

        await self.send_prompt()
    
    # ==================== ACCOUNT SYSTEM HANDLERS ====================
    
    async def handle_account_password(self, password: str):
        """Handle account password entry."""
        if not password:
            await self.send("Password cannot be empty. Account password: ")
            return
        
        # Forgot/reset flow
        if password.lower().startswith('forgot'):
            from accounts import Account, AccountManager
            account = Account.load(self.temp_account_name)
            if not account or not account.settings.get('email'):
                await self.send("No email on file for this account.")
                await self.send("Set one after login with: account email <address>")
                await self.send("Account password: ")
                return
            token = AccountManager.generate_reset_token(account)
            sent = AccountManager.send_reset_email(account, token)
            if sent:
                await self.send("Reset email sent. Check your inbox for the token.")
                await self.send("You can reset here with: reset <token> <newpass>")
            else:
                await self.send("Email not configured. Contact an admin to reset.")
            await self.send("Account password: ")
            return
        
        if password.lower().startswith('reset '):
            parts = password.split()
            if len(parts) < 3:
                await self.send("Usage: reset <token> <newpass>")
                await self.send("Account password: ")
                return
            token = parts[1]
            new_pw = parts[2]
            from accounts import AccountManager
            ok = AccountManager.reset_with_token(self.temp_account_name, token, new_pw)
            if ok:
                await self.send("Password reset! Please log in with your new password.")
            else:
                await self.send("Invalid or expired token.")
            await self.send("Account password: ")
            return
        
        from accounts import AccountManager
        self.account = AccountManager.authenticate(self.temp_account_name, password)
        
        if self.account:
            await self.show_character_menu()
        else:
            await self.send("Invalid password!")
            self.temp_account_name = None
            await self.send("\r\nEnter account name (or character name): ")
            self.state = self.STATE_GET_NAME
    
    async def show_character_menu(self):
        """Display character selection menu."""
        c = self.config.COLORS
        from accounts import AccountManager
        
        await self.send(f"\r\n{c['bright_cyan']}════════════════════════════════════════════════════════════{c['reset']}")
        await self.send(f"{c['bright_yellow']}  Welcome back, {self.account.account_name}!{c['reset']}")
        await self.send(f"{c['bright_cyan']}════════════════════════════════════════════════════════════{c['reset']}")
        
        # Show commands first
        await self.send(f"\r\n{c['white']}Available commands:{c['reset']}")
        await self.send(f"  {c['bright_green']}create{c['reset']}                      - Create a new character")
        await self.send(f"  {c['bright_green']}play <name>{c['reset']}                 - Play the character <name>")
        await self.send(f"  {c['bright_green']}list [level|name]{c['reset']}           - List all your characters")
        await self.send(f"  {c['bright_green']}info <name>{c['reset']}                 - Show character info")
        await self.send(f"  {c['bright_green']}practice <name>{c['reset']}             - Show character skills")
        await self.send(f"  {c['bright_green']}move <name> <up|down> [n]{c['reset']}   - Reorder character list")
        await self.send(f"  {c['bright_green']}password{c['reset']}                    - Change account password")
        await self.send(f"  {c['bright_green']}delete <name>{c['reset']}               - Delete a character")
        await self.send(f"  {c['bright_green']}time{c['reset']}                        - Display game time")
        await self.send(f"  {c['bright_green']}link{c['reset']}                        - Show connection info")
        await self.send(f"  {c['bright_green']}quit{c['reset']}                        - Disconnect")
        
        # Then show characters
        char_info = AccountManager.get_character_info(self.account)
        
        if char_info:
            await self.send(f"\r\n{c['white']}Your Characters:{c['reset']}")
            for i, info in enumerate(char_info, 1):
                await self.send(f"  {c['bright_green']}{i}) {info['name']:<12}{c['white']} Lvl {info['level']:<3} {info['class']:<12}{c['reset']}")
        else:
            await self.send(f"\r\n{c['yellow']}You have no characters yet. Type 'create' to make one!{c['reset']}")
        
        await self.send(f"\r\n{c['bright_cyan']}════════════════════════════════════════════════════════════{c['reset']}")
        self.state = self.STATE_SELECT_CHAR
    
    async def show_account_help(self):
        """Display detailed account menu help."""
        c = self.config.COLORS
        await self.send(f"\r\n{c['bright_yellow']}Account Commands:{c['reset']}")
        await self.send(f"  {c['bright_green']}create{c['reset']}              - Create a new character")
        await self.send(f"  {c['bright_green']}play <name>{c['reset']}         - Play the character <name>")
        await self.send(f"  {c['bright_green']}time{c['reset']}                - Display the game time")
        await self.send(f"  {c['bright_green']}list [<sort>]{c['reset']}       - List all your characters")
        await self.send(f"  {c['bright_green']}move <name> <up|down> [n]{c['reset']} - Move character in list")
        await self.send(f"  {c['bright_green']}password{c['reset']}            - Change your account password")
        await self.send(f"  {c['bright_green']}info <name>{c['reset']}         - Show information about character")
        await self.send(f"  {c['bright_green']}practice <name>{c['reset']}     - Show skills practiced for character")
        await self.send(f"  {c['bright_green']}link{c['reset']}                - Show information about your connection")
        await self.send(f"  {c['bright_green']}lag{c['reset']}                 - Show network latency")
        await self.send(f"  {c['bright_green']}delete <name>{c['reset']}       - Delete a character (permanent!)")
        await self.send(f"  {c['bright_green']}menu{c['reset']}                - Show this menu again")
        await self.send(f"  {c['bright_green']}help{c['reset']}                - Display this help")
        await self.send(f"  {c['bright_green']}quit{c['reset']}                - Leave the account menu")
    
    async def show_character_list(self, sort_by: str = None):
        """Display detailed character list with columns."""
        c = self.config.COLORS
        from player import Player
        from datetime import datetime
        
        await self.send(f"\r\n{c['bright_cyan']}Characters in account \"{self.account.account_name}\"{c['reset']}")
        
        # Header
        await self.send(f"{c['white']}Name         Rce  Cls  Lvl  Last Login       Area            Host{c['reset']}")
        await self.send(f"{c['bright_black']}{'─' * 80}{c['reset']}")
        
        char_list = []
        for char_name in self.account.characters:
            info = Player.get_info(char_name)
            if info:
                # Calculate last login relative time
                last_login = info.get('last_login')
                if last_login:
                    try:
                        login_dt = datetime.fromisoformat(last_login)
                        delta = datetime.now() - login_dt
                        if delta.days > 365:
                            login_str = f"{delta.days // 365} yrs"
                        elif delta.days > 30:
                            login_str = f"{delta.days // 30} mths"
                        elif delta.days > 0:
                            login_str = f"{delta.days} days"
                        elif delta.seconds > 3600:
                            login_str = f"{delta.seconds // 3600} hrs"
                        elif delta.seconds > 60:
                            login_str = f"{delta.seconds // 60} mins"
                        else:
                            login_str = f"{delta.seconds} secs"
                    except:
                        login_str = "Unknown"
                else:
                    login_str = "Never"
                
                # Get area name from last room vnum
                area = "Unknown"
                room_vnum = info.get('room', 3001)
                if room_vnum and self.world:
                    try:
                        zone_vnum = room_vnum // 100
                        if zone_vnum in self.world.zones:
                            area = self.world.zones[zone_vnum].name[:14]
                    except:
                        pass
                
                # Race/class abbreviations
                race_abbr = info.get('race', 'Hum')[:3].lower()
                class_abbr = info.get('char_class', 'war')[:3].lower()
                
                # Last host (truncate if too long)
                last_host = info.get('last_host', 'Unknown')
                if len(last_host) > 20:
                    last_host = last_host[:17] + '...'
                
                char_list.append({
                    'name': info['name'],
                    'race': race_abbr,
                    'class': class_abbr,
                    'level': info['level'],
                    'last_login': login_str,
                    'area': area,
                    'host': last_host
                })
            else:
                char_list.append({
                    'name': char_name,
                    'race': '???',
                    'class': '???',
                    'level': 0,
                    'last_login': 'Unknown',
                    'area': 'Unknown',
                    'host': 'Unknown'
                })
        
        # Sort if requested
        if sort_by == 'level':
            char_list.sort(key=lambda x: x['level'], reverse=True)
        elif sort_by == 'name':
            char_list.sort(key=lambda x: x['name'])
        elif sort_by == 'login':
            pass  # Keep original order for now
        
        for info in char_list:
            await self.send(f"{c['bright_green']}{info['name']:<12} {c['white']}{info['race']:<4} {info['class']:<4} {info['level']:<4} {info['last_login']:<16} {info['area']:<15} {c['bright_black']}{info['host']}{c['reset']}")
    
    async def show_character_info(self, char_name: str):
        """Display detailed info about a character."""
        c = self.config.COLORS
        from player import Player
        
        char_name = char_name.capitalize()
        if char_name not in self.account.characters:
            await self.send(f"Character '{char_name}' not found in your account.")
            return
        
        info = Player.get_info(char_name)
        if not info:
            await self.send(f"Error loading character '{char_name}'.")
            return
        
        await self.send(f"\r\n{c['bright_cyan']}═══════════ Character Info: {info['name']} ═══════════{c['reset']}")
        await self.send(f"  {c['white']}Name:{c['reset']}    {info['name']}")
        await self.send(f"  {c['white']}Race:{c['reset']}    {info['race']}")
        await self.send(f"  {c['white']}Class:{c['reset']}   {info['char_class']}")
        await self.send(f"  {c['white']}Level:{c['reset']}   {info['level']}")
        await self.send(f"  {c['white']}HP:{c['reset']}      {info['hp']}/{info['max_hp']}")
        await self.send(f"  {c['white']}Mana:{c['reset']}    {info['mana']}/{info['max_mana']}")
        await self.send(f"  {c['white']}Gold:{c['reset']}    {info['gold']:,}")
        await self.send(f"  {c['white']}Exp:{c['reset']}     {info['exp']:,}")
        
        # Stats
        stats = info.get('stats', {})
        if stats:
            await self.send(f"\r\n  {c['yellow']}Stats:{c['reset']}")
            await self.send(f"    STR: {stats.get('str', 10)}  INT: {stats.get('int', 10)}  WIS: {stats.get('wis', 10)}")
            await self.send(f"    DEX: {stats.get('dex', 10)}  CON: {stats.get('con', 10)}  CHA: {stats.get('cha', 10)}")
        
        # Combat stats
        await self.send(f"\r\n  {c['yellow']}Combat:{c['reset']}")
        await self.send(f"    Kills: {info.get('kills', 0):,}  Deaths: {info.get('deaths', 0):,}")
        await self.send(f"    Hitroll: {info.get('hitroll', 0)}  Damroll: {info.get('damroll', 0)}")
        
        # Last login info
        await self.send(f"\r\n  {c['yellow']}Login:{c['reset']}")
        await self.send(f"    Last Login: {info.get('last_login', 'Never')[:19] if info.get('last_login') else 'Never'}")
        await self.send(f"    Last Host:  {info.get('last_host', 'Unknown')}")
        
        await self.send(f"{c['bright_cyan']}{'═' * 45}{c['reset']}")
    
    async def show_character_practice(self, char_name: str):
        """Display skills practiced for a character."""
        c = self.config.COLORS
        from player import Player
        
        char_name = char_name.capitalize()
        if char_name not in self.account.characters:
            await self.send(f"Character '{char_name}' not found in your account.")
            return
        
        info = Player.get_info(char_name)
        if not info:
            await self.send(f"Error loading character '{char_name}'.")
            return
        
        skills = info.get('skills', {})
        spells = info.get('spells', {})
        
        await self.send(f"\r\n{c['bright_cyan']}═══════════ Skills for {info['name']} ═══════════{c['reset']}")
        
        if skills:
            await self.send(f"\r\n{c['yellow']}Skills:{c['reset']}")
            for skill, level in sorted(skills.items()):
                bar = '█' * (level // 10) + '░' * (10 - level // 10)
                await self.send(f"  {skill:<20} [{bar}] {level}%")
        
        if spells:
            await self.send(f"\r\n{c['yellow']}Spells:{c['reset']}")
            for spell, level in sorted(spells.items()):
                bar = '█' * (level // 10) + '░' * (10 - level // 10)
                await self.send(f"  {spell:<20} [{bar}] {level}%")
        
        if not skills and not spells:
            await self.send(f"  {c['bright_black']}No skills or spells learned yet.{c['reset']}")
        
        await self.send(f"\r\n{c['bright_cyan']}{'═' * 40}{c['reset']}")
    
    async def show_connection_link(self):
        """Display connection information."""
        c = self.config.COLORS
        from datetime import datetime
        
        addr = self.address[0] if self.address else 'Unknown'
        port = self.address[1] if self.address and len(self.address) > 1 else 'Unknown'
        
        connected_duration = datetime.now() - self.connected_at
        hours = connected_duration.seconds // 3600
        mins = (connected_duration.seconds % 3600) // 60
        secs = connected_duration.seconds % 60
        
        await self.send(f"\r\n{c['bright_cyan']}═══════════ Connection Info ═══════════{c['reset']}")
        await self.send(f"  {c['white']}Your IP:{c['reset']}     {addr}")
        await self.send(f"  {c['white']}Your Port:{c['reset']}   {port}")
        await self.send(f"  {c['white']}Connected:{c['reset']}   {hours}h {mins}m {secs}s")
        await self.send(f"  {c['white']}Server:{c['reset']}      RealmsMUD v1.0")
        await self.send(f"{c['bright_cyan']}{'═' * 40}{c['reset']}")
    
    async def show_lag(self):
        """Display network lag (simple echo test)."""
        c = self.config.COLORS
        import time
        start = time.time()
        await self.send(".")  # Send a byte
        elapsed = (time.time() - start) * 1000
        await self.send(f"\r\n{c['white']}Network latency: {c['bright_green']}{elapsed:.1f}ms{c['reset']}")
    
    async def change_password(self):
        """Start password change flow."""
        c = self.config.COLORS
        await self.send(f"\r\n{c['yellow']}Enter new password: {c['reset']}", newline=False)
        self.state = self.STATE_CHANGE_PASSWORD
    
    async def handle_select_char(self, line: str):
        """Handle character selection commands."""
        if not line:
            await self.send("Account> ", newline=False)
            return
        
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == 'play' or cmd == 'p':
            if not args:
                await self.send("Play which character? ")
                return
            char_name = args[0].capitalize()
            if char_name not in self.account.characters:
                # Try by number
                try:
                    idx = int(args[0]) - 1
                    if 0 <= idx < len(self.account.characters):
                        char_name = self.account.characters[idx]
                    else:
                        await self.send("Character not found. Try: play <name>")
                        return
                except ValueError:
                    await self.send("Character not found. Try: play <name>")
                    return
            
            # Load and enter game
            from player import Player
            self.player = Player.load(char_name, self.world)
            if self.player:
                self.player.account_name = self.account.account_name
                await self.enter_game()
            else:
                await self.send("Error loading character!")
                await self.show_character_menu()
        
        elif cmd == 'create' or cmd == 'c':
            if len(self.account.characters) >= self.account.settings.get('max_chars', 8):
                await self.send("You have reached the maximum number of characters!")
                await self.show_character_menu()
                return
            await self.send("Enter name for new character: ")
            self.state = self.STATE_CREATE_CHAR_NAME
        
        elif cmd == 'delete' or cmd == 'd':
            if not args:
                await self.send("Delete which character? ")
                return
            char_name = args[0].capitalize()
            if char_name not in self.account.characters:
                await self.send("Character not found.")
                return
            c = self.config.COLORS
            self.temp_delete_char = char_name
            await self.send(f"\r\n{c['bright_red']}WARNING: This will PERMANENTLY delete {char_name}!{c['reset']}")
            await self.send(f"{c['yellow']}To confirm, type the character name in ALL CAPS: {c['reset']}", newline=False)
            self.state = self.STATE_CONFIRM_DELETE
        
        elif cmd == 'list' or cmd == 'l':
            sort_by = args[0] if args else None
            await self.show_character_list(sort_by)
        
        elif cmd == 'move' or cmd == 'm':
            if len(args) < 2:
                await self.send("Usage: move <name> <up|down> [n]")
                return
            char_name = args[0].capitalize()
            direction = args[1].lower()
            amount = int(args[2]) if len(args) > 2 else 1
            
            if char_name not in self.account.characters:
                await self.send("Character not found.")
                return
            
            idx = self.account.characters.index(char_name)
            if direction == 'up':
                new_idx = max(0, idx - amount)
            elif direction == 'down':
                new_idx = min(len(self.account.characters) - 1, idx + amount)
            else:
                await self.send("Use 'up' or 'down'.")
                return
            
            self.account.characters.remove(char_name)
            self.account.characters.insert(new_idx, char_name)
            self.account.save()
            await self.send(f"Moved {char_name} to position {new_idx + 1}.")
        
        elif cmd == 'password' or cmd == 'passwd':
            self.temp_new_password = None
            await self.send("Enter new password: ", newline=False)
            self.state = self.STATE_CHANGE_PASSWORD
        
        elif cmd == 'info' or cmd == 'i':
            if not args:
                await self.send("Info for which character? ")
                return
            await self.show_character_info(args[0])
        
        elif cmd == 'practice' or cmd == 'prac':
            if not args:
                await self.send("Practice info for which character? ")
                return
            await self.show_character_practice(args[0])
        
        elif cmd == 'link':
            await self.show_connection_link()
        
        elif cmd == 'lag':
            await self.show_lag()
        
        elif cmd == 'time':
            from datetime import datetime
            c = self.config.COLORS
            now = datetime.now()
            await self.send(f"\r\n{c['white']}Game time: {c['bright_cyan']}{now.strftime('%A, %B %d, %Y at %I:%M %p')}{c['reset']}")
        
        elif cmd == 'menu':
            await self.show_character_menu()
        
        elif cmd == 'help' or cmd == '?':
            await self.show_account_help()
        
        elif cmd == 'quit' or cmd == 'q':
            await self.send("Farewell! Disconnecting...")
            self.writer.close()
            return
        
        elif cmd.isdigit():
            # Quick select by number
            idx = int(cmd) - 1
            if 0 <= idx < len(self.account.characters):
                char_name = self.account.characters[idx]
                from player import Player
                self.player = Player.load(char_name, self.world)
                if self.player:
                    self.player.account_name = self.account.account_name
                    await self.enter_game()
                else:
                    await self.send("Error loading character!")
                    await self.show_character_menu()
            else:
                await self.send("Invalid selection.")
        else:
            await self.send("Unknown command. Type 'help' for available commands.")
    
    async def handle_change_password(self, password: str):
        """Handle new password entry."""
        if not password or len(password) < 4:
            await self.send("Password must be at least 4 characters. Try again: ", newline=False)
            return
        self.temp_new_password = password
        await self.send("Confirm new password: ", newline=False)
        self.state = self.STATE_CONFIRM_NEW_PASSWORD
    
    async def handle_confirm_password(self, password: str):
        """Handle password confirmation."""
        if password != self.temp_new_password:
            await self.send("Passwords don't match. Password not changed.")
            self.temp_new_password = None
            self.state = self.STATE_SELECT_CHAR
            await self.show_character_menu()
            return
        
        self.account.set_password(password)
        self.account.save()
        await self.send("Password changed successfully!")
        self.temp_new_password = None
        self.state = self.STATE_SELECT_CHAR
        await self.show_character_menu()
    
    async def handle_confirm_delete(self, confirmation: str):
        """Handle character deletion confirmation."""
        c = self.config.COLORS
        char_name = getattr(self, 'temp_delete_char', None)
        
        if not char_name:
            await self.send("Error: No character selected for deletion.")
            self.state = self.STATE_SELECT_CHAR
            await self.show_character_menu()
            return
        
        # Must type name in ALL CAPS
        if confirmation != char_name.upper():
            await self.send(f"{c['yellow']}Deletion cancelled. You must type {char_name.upper()} to confirm.{c['reset']}")
            self.temp_delete_char = None
            self.state = self.STATE_SELECT_CHAR
            await self.show_character_menu()
            return
        
        # Confirmed - delete the character
        from accounts import AccountManager
        if AccountManager.delete_character(self.account, char_name):
            await self.send(f"{c['bright_red']}Character '{char_name}' has been permanently deleted.{c['reset']}")
        else:
            await self.send(f"{c['red']}Error deleting character.{c['reset']}")
        
        self.temp_delete_char = None
        self.state = self.STATE_SELECT_CHAR
        await self.show_character_menu()
    
    async def handle_create_char_name(self, name: str):
        """Handle new character name for account."""
        if not name:
            await self.send("Enter name for new character: ")
            return
        
        if len(name) < 3 or len(name) > 12:
            await self.send("Names must be between 3 and 12 characters.")
            await self.send("Enter name for new character: ")
            return
        
        if not name.isalpha():
            await self.send("Names must contain only letters.")
            await self.send("Enter name for new character: ")
            return
        
        name = name.capitalize()
        
        # Check if name is taken
        from player import Player
        if Player.exists(name):
            await self.send("That name is already taken. Choose another: ")
            return
        
        self.temp_name = name
        await self.show_race_menu()
        self.state = self.STATE_GET_RACE
    
    async def handle_migrate_offer(self, response: str):
        """Handle offer to migrate to account system."""
        if response.lower() in ('y', 'yes'):
            from accounts import AccountManager
            account = AccountManager.migrate_legacy_player(self.temp_name, self.temp_password)
            if account:
                self.account = account
                await self.send(f"\r\nAccount '{account.account_name}' created!")
                await self.send(f"Character '{self.temp_name}' linked to account.")
        
        # Enter game regardless
        await self.enter_game()
        
    async def handle_command(self, line: str):
        """Handle a game command."""
        if not line:
            # Allow help pagination to continue on empty input
            if getattr(self.player, 'help_pagination', None):
                from commands import CommandHandler
                await CommandHandler.continue_help_pagination(self.player)
            await self.send_prompt()
            return

        # Echo command back to player so they see what they typed
        c = self.config.COLORS
        await self.send(f"{c['cyan']}> {line}{c['reset']}\r\n")

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
        
        # Occasional tip for newer players after commands
        try:
            if self.player.level < 15:
                from tips import TipManager
                await TipManager.maybe_show_tip(self.player, chance=0.03)
        except Exception:
            pass

        # Track command for tutorial progress
        try:
            from quests import QuestManager
            await QuestManager.check_tutorial_progress(self.player, cmd)
            # Check for auto-completion of tutorial quests
            for quest in list(getattr(self.player, 'active_quests', [])):
                if quest.quest_id.startswith('tutorial_') and quest.is_complete():
                    await QuestManager.auto_complete_tutorial_quest(self.player, quest)
            
            # Periodic auto-hint for tutorial quests (5 min no progress)
            await QuestManager.check_auto_hint(self.player)
            
            # Compass sense hint after movement/look
            if cmd in ('look', 'north', 'south', 'east', 'west', 'up', 'down', 'n', 's', 'e', 'w', 'u', 'd'):
                await QuestManager.show_compass_hint(self.player)
        except Exception:
            pass
        
        await self.send_prompt()
        
    async def disconnect(self):
        """Handle disconnection gracefully — stop combat, save state, clean up."""
        logger.info(f"Connection closed: {self.address}")
        
        if self.player:
            try:
                # Stop combat immediately
                if self.player.fighting:
                    # Clear the opponent's target if they were fighting this player
                    opponent = self.player.fighting
                    if opponent and getattr(opponent, 'fighting', None) == self.player:
                        opponent.fighting = None
                        if opponent.position == 'fighting':
                            opponent.position = 'standing'
                    self.player.fighting = None
                    if self.player.position == 'fighting':
                        self.player.position = 'standing'

                # Update logout timestamp + playtime
                now = datetime.now()
                if hasattr(self.player, 'last_login'):
                    self.player.total_playtime += max(0, int((now - self.player.last_login).total_seconds()))
                self.player.last_logout = now
            except Exception as e:
                logger.error(f"Error updating player state on disconnect: {e}")

            # Save player state
            try:
                await self.player.save()
            except Exception as e:
                logger.error(f"Error saving player {self.player.name} on disconnect: {e}")

            # Remove from world
            try:
                await self.world.remove_player(self.player)
            except Exception as e:
                logger.error(f"Error removing player {self.player.name} from world: {e}")
            
            # Announce departure
            try:
                if self.player.room:
                    await self.player.room.send_to_room(
                        f"{self.player.name} has left the realm.",
                        exclude=[self.player]
                    )
            except Exception:
                pass

            # Clear connection reference
            self.player.connection = None
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
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
            self.config.PORT,
            reuse_address=True
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
                    data = await asyncio.wait_for(reader.readline(), timeout=1800.0)
                    if not data:
                        break
                    line = data.decode('utf-8', errors='ignore').strip()
                    await conn.handle_input(line)
                except asyncio.TimeoutError:
                    # Force-rent at 2x cost on idle timeout
                    if conn.player:
                        try:
                            from commands import CommandHandler
                            rent_cost = CommandHandler.calc_total_rent(conn.player) * 2
                            if conn.player.gold >= rent_cost:
                                conn.player.gold -= rent_cost
                                conn.player.rent_paid = True
                                await conn.send(f"\r\nIdle timeout! You've been force-rented for {rent_cost} gold (2x normal rate).\r\n")
                            else:
                                await conn.send(f"\r\nIdle timeout! You couldn't afford rent ({rent_cost} gold). Some items may be lost!\r\n")
                        except Exception:
                            pass
                    else:
                        await conn.send("\r\nConnection timed out. Goodbye!\r\n")
                    break
                except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError) as e:
                    logger.info(f"Connection lost for {self.address}: {e}")
                    break
                except Exception as e:
                    import traceback
                    logger.error(f"Error handling input: {e}")
                    logger.error(traceback.format_exc())
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
