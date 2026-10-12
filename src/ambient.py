"""
Misthollow Ambient Message System
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

logger = logging.getLogger('Misthollow.Ambient')

from ambient_lines import LINES, WEIGHT, PRESENCE
from ambient_place import place_tags, fits, neighbours

# where a sound comes from, in words (presence lines)
WHERE = {'up': 'above you', 'down': 'below you'}


def where(direction: str) -> str:
    return WHERE.get(direction, f"to the {direction}")


def _kind(mob) -> str:
    """How a creature next door sounds: dead, big, a person, or a beast."""
    try:
        from procs import is_undead
        if is_undead(mob):
            return 'undead'
    except Exception:
        pass
    flags = set(getattr(mob, 'flags', None) or ())
    if 'boss' in flags or getattr(mob, 'is_boss', False) or (getattr(mob, 'level', 0) or 0) >= 40:
        return 'heavy'
    if getattr(mob, 'equipment', None) or str(getattr(mob, 'race', '') or '').lower() in ('human', 'elf', 'dwarf', 'halfling', 'gnome', 'orc', 'half-orc'):
        return 'person'
    return 'beast'


def _mob_id(mob):
    try:
        from map_system import _mob_uid
        return _mob_uid(mob)
    except Exception:
        return None


class AmbientManager:
    """Manages ambient messages for the world: lines that fit the place (ambient_place.py), and
    creatures really next door heard before they are seen. A telnet player reads them; a /play
    player hears them and sees a cue (an `ambient` event on the map socket), with no chat line."""

    # Track last ambient time per player to avoid spam
    _last_ambient = {}  # player_name -> timestamp
    _last_presence = {}  # player_name -> timestamp (patrols passing nearby)

    @classmethod
    def tags_for(cls, player, world) -> set:
        room = player.room
        game_time = getattr(world, 'game_time', None)
        hour = getattr(game_time, 'hour', None) if game_time else None
        weather = getattr(getattr(room, 'zone', None), 'weather', None)
        return place_tags(room, world, hour, weather)

    @classmethod
    def presence_line(cls, player, world) -> Optional[dict]:
        """A hostile creature one room away, heard: {text, sound, key:'presence', dir, room, mob, name}."""
        room = player.room
        heard = []
        for d, r in neighbours(room, world):
            for ch in getattr(r, 'characters', None) or []:
                if hasattr(ch, 'connection') or getattr(ch, 'fighting', None):
                    continue
                if 'aggressive' not in (getattr(ch, 'flags', None) or ()):
                    continue
                heard.append((d, r, ch))
        if not heard:
            return None
        d, r, mob = random.choice(heard)
        text = random.choice(PRESENCE[_kind(mob)]).format(where=where(d))
        return {'text': text, 'sound': 'amb_steps', 'key': 'presence', 'dir': d, 'room': getattr(r, 'vnum', None),
                'mob': _mob_id(mob), 'name': getattr(mob, 'name', '')}

    @classmethod
    def pick(cls, player, world) -> Optional[dict]:
        """A murmur that fits where the player is: {text, sound, key} (or a presence)."""
        if not player.room:
            return None
        heard = cls.presence_line(player, world)
        if heard and random.random() < 0.5:
            return heard
        tags = cls.tags_for(player, world)
        pool, weights = [], []
        for key, lines in LINES.items():
            if not fits(key, tags):
                continue
            w = max(WEIGHT.get(t, 1.0) for t in key.split('+'))
            for text, sound in lines:
                pool.append({'text': text, 'sound': sound, 'key': key})
                weights.append(w)
        if not pool:
            return heard
        return random.choices(pool, weights)[0]

    @classmethod
    def get_ambient_message(cls, player: 'Player', world: 'World') -> Optional[str]:
        """The text of a murmur that fits where the player is (older callers)."""
        m = cls.pick(player, world)
        return m['text'] if m else None

    @classmethod
    async def deliver(cls, player, world, m: dict):
        """To /play: an `ambient` event (a sound from where it comes, a cue on the HUD), no chat
        line. To telnet: the line."""
        web_map = getattr(world, 'web_map', None)
        if web_map is not None and web_map.has_play(player):
            await web_map.notify_event(player, {'type': 'ambient', **m})
            return
        c = player.config.COLORS
        await player.send(f"\r\n{c['white']}{m['text']}{c['reset']}\r\n")

    @classmethod
    async def maybe_send_ambient(cls, player: 'Player', world: 'World',
                                  chance: float = 0.03) -> bool:
        """Maybe send an ambient murmur to a player (never in a fight, at most one each 30 s)."""
        import time
        if player.is_fighting or getattr(player, 'position', '') == 'sleeping':
            return False
        now = time.time()
        if now - cls._last_ambient.get(player.name, 0) < 30:
            return False
        if random.random() > chance:
            return False
        m = cls.pick(player, world)
        if not m:
            return False
        try:
            await cls.deliver(player, world, m)
        except Exception:
            logger.debug('ambient delivery failed', exc_info=True)
            return False
        cls._last_ambient[player.name] = now
        return True

    @classmethod
    async def ambient_tick(cls, world: 'World'):
        """Process ambient messages for all players (every 10 s from the main loop)."""
        for player in list(world.players.values()):
            # frequent enough to feel alive, rate-limited to 30s per player
            await cls.maybe_send_ambient(player, world, chance=0.12)

    @classmethod
    async def creature_moved(cls, world, mob, new_room):
        """A wandering creature came into `new_room`: /play players one room away hear it (a
        patrol passing: a cue on the minimap and at the screen's edge, no chat line). Those in
        the room itself see it arrive."""
        import time
        web_map = getattr(world, 'web_map', None)
        if web_map is None or new_room is None:
            return
        flags = set(getattr(mob, 'flags', None) or ())
        if not ({'aggressive', 'boss'} & flags or getattr(mob, 'is_boss', False)):
            return
        now = time.time()
        for d, r in neighbours(new_room, world):
            for p in list(getattr(r, 'characters', None) or []):
                if not hasattr(p, 'connection') or not web_map.has_play(p):
                    continue
                if now - cls._last_presence.get(p.name, 0) < 8:
                    continue
                back = next((dd for dd, rr in neighbours(r, world) if rr is new_room), None)
                if back is None:
                    continue
                cls._last_presence[p.name] = now
                text = random.choice(PRESENCE[_kind(mob)]).format(where=where(back))
                await web_map.notify_event(p, {'type': 'ambient', 'text': text, 'sound': 'amb_steps', 'key': 'presence',
                                               'dir': back, 'room': getattr(new_room, 'vnum', None),
                                               'mob': _mob_id(mob), 'name': getattr(mob, 'name', ''), 'moving': True})
