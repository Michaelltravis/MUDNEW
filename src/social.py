"""
RealmsMUD Social & Communication System
========================================
Chat channels, friends, ignore, player notes, finger/whois.
"""

import time
import logging
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger('RealmsMUD.Social')

# ==================== CHAT CHANNELS ====================

CHANNELS = {
    'global': {
        'name': 'Global',
        'color': 'bright_yellow',
        'prefix': '[Global]',
        'description': 'Global chat for all players',
        'min_level': 1,
        'max_level': None,
        'helper_access': False,
    },
    'newbie': {
        'name': 'Newbie',
        'color': 'bright_green',
        'prefix': '[Newbie]',
        'description': 'New player help channel (levels 1-15 + helpers)',
        'min_level': 1,
        'max_level': 15,
        'helper_access': True,
    },
    'trade': {
        'name': 'Trade',
        'color': 'bright_cyan',
        'prefix': '[Trade]',
        'description': 'Trading and economy chat',
        'min_level': 1,
        'max_level': None,
        'helper_access': False,
    },
    'lfg': {
        'name': 'LFG',
        'color': 'bright_magenta',
        'prefix': '[LFG]',
        'description': 'Looking for group',
        'min_level': 1,
        'max_level': None,
        'helper_access': False,
    },
}

# Rate limiting: max messages per channel per player
RATE_LIMIT_WINDOW = 10  # seconds
RATE_LIMIT_MAX = 3      # max messages per window


def _check_rate_limit(player: 'Player', channel: str) -> bool:
    """Return True if message is allowed, False if rate-limited."""
    now = time.time()
    if not hasattr(player, '_channel_timestamps'):
        player._channel_timestamps = {}
    
    timestamps = player._channel_timestamps.get(channel, [])
    # Prune old timestamps
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    
    if len(timestamps) >= RATE_LIMIT_MAX:
        return False
    
    timestamps.append(now)
    player._channel_timestamps[channel] = timestamps
    return True


def can_access_channel(player: 'Player', channel_key: str) -> bool:
    """Check if a player can access a channel."""
    ch = CHANNELS.get(channel_key)
    if not ch:
        return False
    if ch['max_level'] and player.level > ch['max_level']:
        # Check helper access
        if ch['helper_access'] and 'helper' in getattr(player, 'flags', set()):
            return True
        if getattr(player, 'is_immortal', False):
            return True
        return False
    if player.level < ch['min_level']:
        return False
    return True


def is_channel_on(player: 'Player', channel_key: str) -> bool:
    """Check if a player has a channel enabled."""
    disabled = getattr(player, 'disabled_channels', set())
    return channel_key not in disabled


def is_ignored(player: 'Player', sender_name: str) -> bool:
    """Check if player is ignoring sender."""
    ignored = getattr(player, 'ignore_list', [])
    return sender_name.lower() in [n.lower() for n in ignored]


async def send_channel_message(player: 'Player', channel_key: str, message: str):
    """Send a message on a chat channel."""
    ch = CHANNELS.get(channel_key)
    if not ch:
        await player.send(f"Unknown channel '{channel_key}'.")
        return

    if not can_access_channel(player, channel_key):
        await player.send(f"You cannot access the {ch['name']} channel.")
        return

    if not is_channel_on(player, channel_key):
        await player.send(f"You have the {ch['name']} channel turned off. Use 'channel on {channel_key}' first.")
        return

    if not _check_rate_limit(player, channel_key):
        c = player.config.COLORS
        await player.send(f"{c['red']}You are sending messages too fast. Please wait a moment.{c['reset']}")
        return

    c = player.config.COLORS
    color = c.get(ch['color'], c['white'])

    # Send to self
    await player.send(f"{color}{ch['prefix']} You: {message}{c['reset']}")

    # Send to all other online players
    for p in player.world.players.values():
        if p == player:
            continue
        if not can_access_channel(p, channel_key):
            continue
        if not is_channel_on(p, channel_key):
            continue
        if is_ignored(p, player.name):
            continue
        await p.send(f"\r\n{color}{ch['prefix']} {player.name}: {message}{c['reset']}")


# ==================== FRIENDS ====================

def get_friends(player: 'Player') -> list:
    """Get player's friends list."""
    return getattr(player, 'friends_list', [])


async def add_friend(player: 'Player', target_name: str):
    """Add a friend."""
    c = player.config.COLORS
    if not hasattr(player, 'friends_list'):
        player.friends_list = []

    target_lower = target_name.lower()
    if target_lower == player.name.lower():
        await player.send(f"{c['yellow']}You can't add yourself as a friend.{c['reset']}")
        return

    if any(f.lower() == target_lower for f in player.friends_list):
        await player.send(f"{c['yellow']}{target_name} is already on your friends list.{c['reset']}")
        return

    # Verify player exists
    from player import Player as PlayerClass
    if not PlayerClass.exists(target_name):
        await player.send(f"{c['red']}No player named '{target_name}' exists.{c['reset']}")
        return

    player.friends_list.append(target_name.capitalize())
    await player.send(f"{c['bright_green']}{target_name.capitalize()} added to your friends list.{c['reset']}")


async def remove_friend(player: 'Player', target_name: str):
    """Remove a friend."""
    c = player.config.COLORS
    if not hasattr(player, 'friends_list'):
        player.friends_list = []
        await player.send(f"{c['yellow']}Your friends list is empty.{c['reset']}")
        return

    target_lower = target_name.lower()
    for i, f in enumerate(player.friends_list):
        if f.lower() == target_lower:
            player.friends_list.pop(i)
            await player.send(f"{c['yellow']}{f} removed from your friends list.{c['reset']}")
            return

    await player.send(f"{c['yellow']}{target_name} is not on your friends list.{c['reset']}")


async def show_friends(player: 'Player'):
    """Show friends list with online status."""
    c = player.config.COLORS
    friends = get_friends(player)

    if not friends:
        await player.send(f"{c['yellow']}Your friends list is empty. Use 'friend add <player>' to add friends.{c['reset']}")
        return

    await player.send(f"\r\n{c['cyan']}═══ Friends List ═══{c['reset']}")
    for name in sorted(friends):
        online_player = player.world.get_player(name.lower()) if player.world else None
        if online_player:
            zone_name = ''
            if online_player.room and online_player.room.zone:
                zone_name = f" - {online_player.room.zone.name}"
            await player.send(f"  {c['bright_green']}● {name}{zone_name}{c['reset']}")
        else:
            await player.send(f"  {c['bright_black']}○ {name} (offline){c['reset']}")
    await player.send(f"{c['cyan']}Total: {len(friends)} friend(s){c['reset']}")


# ==================== IGNORE ====================

async def ignore_player(player: 'Player', target_name: str):
    """Add player to ignore list."""
    c = player.config.COLORS
    if not hasattr(player, 'ignore_list'):
        player.ignore_list = []

    target_lower = target_name.lower()
    if target_lower == player.name.lower():
        await player.send(f"{c['yellow']}You can't ignore yourself.{c['reset']}")
        return

    if any(n.lower() == target_lower for n in player.ignore_list):
        await player.send(f"{c['yellow']}{target_name} is already on your ignore list.{c['reset']}")
        return

    player.ignore_list.append(target_name.capitalize())
    await player.send(f"{c['yellow']}You are now ignoring {target_name.capitalize()}.{c['reset']}")


async def unignore_player(player: 'Player', target_name: str):
    """Remove player from ignore list."""
    c = player.config.COLORS
    if not hasattr(player, 'ignore_list'):
        player.ignore_list = []

    target_lower = target_name.lower()
    for i, n in enumerate(player.ignore_list):
        if n.lower() == target_lower:
            player.ignore_list.pop(i)
            await player.send(f"{c['green']}You are no longer ignoring {n}.{c['reset']}")
            return

    await player.send(f"{c['yellow']}{target_name} is not on your ignore list.{c['reset']}")


# ==================== PLAYER NOTES ====================

async def add_note(player: 'Player', target_name: str, text: str):
    """Add a private note about another player."""
    c = player.config.COLORS
    if not hasattr(player, 'player_notes'):
        player.player_notes = {}

    key = target_name.lower()
    if key not in player.player_notes:
        player.player_notes[key] = []

    player.player_notes[key].append({
        'time': time.time(),
        'text': text,
    })
    # Keep max 20 notes per player
    player.player_notes[key] = player.player_notes[key][-20:]
    await player.send(f"{c['green']}Note added for {target_name.capitalize()}.{c['reset']}")


async def show_notes(player: 'Player', target_name: str = None):
    """Show player notes."""
    c = player.config.COLORS
    if not hasattr(player, 'player_notes'):
        player.player_notes = {}

    if target_name:
        key = target_name.lower()
        notes = player.player_notes.get(key, [])
        if not notes:
            await player.send(f"{c['yellow']}No notes for {target_name.capitalize()}.{c['reset']}")
            return
        await player.send(f"\r\n{c['cyan']}═══ Notes: {target_name.capitalize()} ═══{c['reset']}")
        for note in notes:
            import datetime
            ts = datetime.datetime.fromtimestamp(note['time']).strftime('%m/%d %H:%M')
            await player.send(f"  {c['white']}[{ts}] {note['text']}{c['reset']}")
    else:
        if not player.player_notes:
            await player.send(f"{c['yellow']}You have no notes. Use 'note <player> <text>' to add one.{c['reset']}")
            return
        await player.send(f"\r\n{c['cyan']}═══ Player Notes ═══{c['reset']}")
        for key, notes in sorted(player.player_notes.items()):
            await player.send(f"  {c['bright_white']}{key.capitalize()}{c['white']} ({len(notes)} note{'s' if len(notes) != 1 else ''}){c['reset']}")


# ==================== FINGER / WHOIS ====================

async def show_finger(player: 'Player', target_name: str):
    """Show detailed info about a player."""
    c = player.config.COLORS

    # Try online first
    target = player.world.get_player(target_name.lower()) if player.world else None

    if not target:
        # Load from file
        from player import Player as PlayerClass
        target = PlayerClass.load(target_name)
        if not target:
            await player.send(f"{c['red']}No player named '{target_name}' found.{c['reset']}")
            return

    online = player.world.get_player(target.name.lower()) is not None if player.world else False

    await player.send(f"\r\n{c['cyan']}═══════════════════════════════════════════{c['reset']}")
    await player.send(f"{c['bright_white']}  {target.name} {getattr(target, 'title', 'the Adventurer')}{c['reset']}")
    await player.send(f"{c['cyan']}═══════════════════════════════════════════{c['reset']}")

    race_name = target.config.RACES.get(target.race, {}).get('name', target.race)
    class_name = target.config.CLASSES.get(target.char_class, {}).get('name', target.char_class)
    await player.send(f"  {c['white']}Race:{c['reset']}    {race_name}")
    await player.send(f"  {c['white']}Class:{c['reset']}   {class_name}")
    await player.send(f"  {c['white']}Level:{c['reset']}   {target.level}")

    # Prestige class (if any)
    prestige = getattr(target, 'prestige_class', None)
    if prestige:
        await player.send(f"  {c['white']}Prestige:{c['reset']} {prestige}")

    # Guild
    guild = getattr(target, 'guild', None)
    if guild:
        await player.send(f"  {c['white']}Guild:{c['reset']}   {guild}")

    # Status
    status = f"{c['bright_green']}Online" if online else f"{c['bright_black']}Offline"
    await player.send(f"  {c['white']}Status:{c['reset']}  {status}{c['reset']}")

    # Last login
    last = getattr(target, 'last_login', None)
    if last:
        await player.send(f"  {c['white']}Last on:{c['reset']} {last.strftime('%Y-%m-%d %H:%M') if hasattr(last, 'strftime') else str(last)}")

    # Playtime
    playtime = getattr(target, 'total_playtime', 0)
    hours = int(playtime // 3600)
    mins = int((playtime % 3600) // 60)
    await player.send(f"  {c['white']}Played:{c['reset']}  {hours}h {mins}m")

    # Created
    created = getattr(target, 'created_at', None)
    if created:
        await player.send(f"  {c['white']}Created:{c['reset']} {created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created)}")

    # PvP stats
    arena_wins = getattr(target, 'arena_wins', 0)
    arena_losses = getattr(target, 'arena_losses', 0)
    arena_rating = getattr(target, 'arena_rating', 1000)
    if arena_wins or arena_losses:
        await player.send(f"  {c['white']}PvP:{c['reset']}     {arena_wins}W / {arena_losses}L (Rating: {arena_rating})")

    # Achievements
    achievements = getattr(target, 'achievements', {})
    if achievements:
        await player.send(f"  {c['white']}Achievements:{c['reset']} {len(achievements)} earned")

    # Faction standings (top 3)
    rep = getattr(target, 'reputation', {})
    if rep:
        sorted_rep = sorted(rep.items(), key=lambda x: x[1], reverse=True)[:3]
        if sorted_rep:
            await player.send(f"  {c['white']}Top Factions:{c['reset']}")
            for faction, value in sorted_rep:
                await player.send(f"    {faction}: {value}")

    await player.send(f"{c['cyan']}═══════════════════════════════════════════{c['reset']}")


# ==================== FRIEND NOTIFICATIONS ====================

async def notify_login(player: 'Player'):
    """Notify friends that player logged in."""
    if not getattr(player, 'friend_notify', True):
        return
    c = player.config.COLORS
    for p in player.world.players.values():
        if p == player:
            continue
        if not getattr(p, 'friend_notify', True):
            continue
        friends = getattr(p, 'friends_list', [])
        if any(f.lower() == player.name.lower() for f in friends):
            await p.send(f"\r\n{c['bright_green']}[Friend] {player.name} has logged in.{c['reset']}")


async def notify_logout(player: 'Player'):
    """Notify friends that player logged out."""
    if not getattr(player, 'friend_notify', True):
        return
    c = player.config.COLORS
    for p in player.world.players.values():
        if p == player:
            continue
        if not getattr(p, 'friend_notify', True):
            continue
        friends = getattr(p, 'friends_list', [])
        if any(f.lower() == player.name.lower() for f in friends):
            await p.send(f"\r\n{c['bright_yellow']}[Friend] {player.name} has logged out.{c['reset']}")
