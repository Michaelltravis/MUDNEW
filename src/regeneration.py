"""
Enhanced Regeneration System

Provides sophisticated regeneration calculations based on multiple factors:
- Character position (sleeping, resting, standing, fighting)
- Character stats (CON for HP, INT/WIS for mana, DEX for move)
- Time of day (night bonus for sleeping, day bonus for movement)
- Weather conditions
- Terrain type
- Class bonuses
- Race bonuses
- Active affects
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Character
    from time_system import GameTime
    from weather import Weather

logger = logging.getLogger(__name__)


class RegenerationCalculator:
    """
    Calculates regeneration rates for HP, mana, and movement points
    based on multiple modifiers.
    """

    @staticmethod
    def calculate_hp_regen(character: 'Character', base_rate: float,
                          position_mult: float, game_time: Optional['GameTime'] = None,
                          weather: Optional['Weather'] = None) -> int:
        """
        Calculate HP regeneration for a character.

        Args:
            character: The character regenerating
            base_rate: Base regeneration rate (percentage of max HP)
            position_mult: Multiplier from position (sleeping 2x, resting 1.5x, etc.)
            game_time: Optional game time for time-of-day bonuses
            weather: Optional weather for weather bonuses

        Returns:
            HP to regenerate this tick
        """
        # Start with base regen
        regen = character.max_hp * base_rate * position_mult

        # Stat bonus: Constitution
        con_modifier = (character.con - 10) * 0.01  # +1% per point above 10
        regen *= (1.0 + con_modifier)

        # Time of day bonus
        if game_time and character.position in ['sleeping', 'resting']:
            # Night time bonus for sleeping/resting (midnight to 6am)
            if game_time.is_night() and game_time.hour < 6:
                regen *= 1.25  # +25% regen at night

        # Weather effects
        if weather:
            weather_mult = RegenerationCalculator._get_weather_hp_modifier(weather)
            regen *= weather_mult

        # Terrain effects
        if hasattr(character, 'room') and character.room:
            terrain_mult = RegenerationCalculator._get_terrain_hp_modifier(
                character.room.sector_type, character
            )
            regen *= terrain_mult

        # Class bonuses
        if hasattr(character, 'char_class'):
            class_mult = RegenerationCalculator._get_class_hp_modifier(
                character.char_class, character.room.sector_type if hasattr(character, 'room') and character.room else 'inside'
            )
            regen *= class_mult

        # Race bonuses
        if hasattr(character, 'race'):
            race_mult = RegenerationCalculator._get_race_hp_modifier(character.race)
            regen *= race_mult

        # Affect bonuses/penalties
        if hasattr(character, 'affect_flags'):
            if 'regenerating' in character.affect_flags:
                regen *= 2.0  # Regeneration spell doubles HP regen
            if 'poisoned' in character.affect_flags:
                regen *= 0.5  # Poison halves HP regen
            if 'diseased' in character.affect_flags:
                regen *= 0.25  # Disease severely reduces HP regen

        # Hunger/Thirst penalties (players only)
        if hasattr(character, 'hunger'):
            if character.hunger <= 5:
                regen *= 0.4
            elif character.hunger <= 10:
                regen *= 0.7
        if hasattr(character, 'thirst'):
            if character.thirst <= 3:
                regen *= 0.4
            elif character.thirst <= 8:
                regen *= 0.7

        return max(1, int(regen))

    @staticmethod
    def calculate_mana_regen(character: 'Character', base_rate: float,
                            position_mult: float, game_time: Optional['GameTime'] = None,
                            weather: Optional['Weather'] = None) -> int:
        """
        Calculate mana regeneration for a character.

        Args:
            character: The character regenerating
            base_rate: Base regeneration rate (percentage of max mana)
            position_mult: Multiplier from position
            game_time: Optional game time for time-of-day bonuses
            weather: Optional weather for weather bonuses

        Returns:
            Mana to regenerate this tick
        """
        # Start with base regen
        regen = character.max_mana * base_rate * position_mult

        # Stat bonus: Intelligence and Wisdom
        int_modifier = (character.int - 10) * 0.01  # +1% per point above 10
        wis_modifier = (character.wis - 10) * 0.01  # +1% per point above 10
        regen *= (1.0 + int_modifier + wis_modifier)

        # Time of day bonus
        if game_time and character.position in ['sleeping', 'resting']:
            # Night time bonus for sleeping/resting (midnight to 6am)
            if game_time.is_night() and game_time.hour < 6:
                regen *= 1.25  # +25% mana regen at night

        # Weather effects
        if weather:
            weather_mult = RegenerationCalculator._get_weather_mana_modifier(weather)
            regen *= weather_mult

        # Terrain effects (some places are more magically attuned)
        if hasattr(character, 'room') and character.room:
            terrain_mult = RegenerationCalculator._get_terrain_mana_modifier(
                character.room.sector_type
            )
            regen *= terrain_mult

        # Class bonuses
        if hasattr(character, 'char_class'):
            class_mult = RegenerationCalculator._get_class_mana_modifier(character.char_class)
            regen *= class_mult

        # Race bonuses
        if hasattr(character, 'race'):
            race_mult = RegenerationCalculator._get_race_mana_modifier(character.race)
            regen *= race_mult

        # Soulstone bonus (necromancer offhand)
        try:
            stone = character.equipment.get('hold') if hasattr(character, 'equipment') else None
            if stone and (getattr(stone, 'is_soulstone', False) or ('soulstone' in getattr(stone, 'flags', set()))):
                regen *= (1.0 + getattr(stone, 'soulstone_mana_regen', 0.10))
        except Exception:
            pass

        # Affect bonuses/penalties
        if hasattr(character, 'affect_flags'):
            if 'silenced' in character.affect_flags:
                regen *= 0.5  # Silence halves mana regen

        # Hunger/Thirst penalties (players only)
        if hasattr(character, 'hunger'):
            if character.hunger <= 5:
                regen *= 0.5
            elif character.hunger <= 10:
                regen *= 0.8
        if hasattr(character, 'thirst'):
            if character.thirst <= 3:
                regen *= 0.4
            elif character.thirst <= 8:
                regen *= 0.7

        return max(1, int(regen))

    @staticmethod
    def calculate_move_regen(character: 'Character', base_rate: float,
                            position_mult: float, game_time: Optional['GameTime'] = None,
                            weather: Optional['Weather'] = None) -> int:
        """
        Calculate movement point regeneration for a character.

        Args:
            character: The character regenerating
            base_rate: Base regeneration rate (percentage of max move)
            position_mult: Multiplier from position
            game_time: Optional game time for time-of-day bonuses
            weather: Optional weather for weather bonuses

        Returns:
            Movement points to regenerate this tick
        """
        # Start with base regen
        regen = character.max_move * base_rate * position_mult

        # Stat bonus: Dexterity
        dex_modifier = (character.dex - 10) * 0.01  # +1% per point above 10
        regen *= (1.0 + dex_modifier)

        # Time of day bonus
        if game_time:
            # Day time bonus for movement (6am to 8pm)
            if game_time.is_day():
                regen *= 1.25  # +25% move regen during day

        # Weather effects
        if weather:
            weather_mult = RegenerationCalculator._get_weather_move_modifier(weather)
            regen *= weather_mult

        # Terrain effects
        if hasattr(character, 'room') and character.room:
            terrain_mult = RegenerationCalculator._get_terrain_move_modifier(
                character.room.sector_type, character
            )
            regen *= terrain_mult

        # Class bonuses
        if hasattr(character, 'char_class'):
            class_mult = RegenerationCalculator._get_class_move_modifier(
                character.char_class, character.room.sector_type if hasattr(character, 'room') and character.room else 'inside'
            )
            regen *= class_mult

        # Race bonuses (some races are naturally more agile)
        if hasattr(character, 'race'):
            race_mult = RegenerationCalculator._get_race_move_modifier(character.race)
            regen *= race_mult

        # Hunger/Thirst penalties (players only)
        if hasattr(character, 'hunger'):
            if character.hunger <= 5:
                regen *= 0.5
            elif character.hunger <= 10:
                regen *= 0.8
        if hasattr(character, 'thirst'):
            if character.thirst <= 3:
                regen *= 0.4
            elif character.thirst <= 8:
                regen *= 0.7

        return max(1, int(regen))

    # Helper methods for modifiers

    @staticmethod
    def _get_weather_hp_modifier(weather: 'Weather') -> float:
        """Get HP regen modifier from weather."""
        # Most weather has minimal effect on HP regen
        if weather.sky_condition == 'stormy':
            return 0.9  # Storms are stressful, -10% HP regen
        return 1.0

    @staticmethod
    def _get_weather_mana_modifier(weather: 'Weather') -> float:
        """Get mana regen modifier from weather."""
        # Stormy weather can disrupt magical concentration
        if weather.sky_condition == 'stormy':
            return 0.9  # -10% mana regen in storms
        return 1.0

    @staticmethod
    def _get_weather_move_modifier(weather: 'Weather') -> float:
        """Get move regen modifier from weather."""
        weather_mods = {
            'clear': 1.1,           # Nice weather, +10% move regen
            'partly_cloudy': 1.0,
            'overcast': 1.0,
            'rainy': 0.9,           # Rain tiring, -10%
            'stormy': 0.8,          # Storms exhausting, -20%
            'snowy': 0.85,          # Snow tiring, -15%
            'foggy': 0.95,          # Fog slightly tiring, -5%
        }
        return weather_mods.get(weather.sky_condition, 1.0)

    @staticmethod
    def _get_terrain_hp_modifier(sector_type: str, character: 'Character') -> float:
        """Get HP regen modifier from terrain."""
        terrain_mods = {
            'inside': 1.0,
            'city': 0.9,            # Urban stress, -10%
            'field': 1.05,          # Open air, +5%
            'forest': 1.1,          # Natural environment, +10%
            'hills': 1.0,
            'mountains': 0.85,      # Altitude, -15%
            'water_swim': 0.9,      # Tiring, -10%
            'water_noswim': 0.5,    # Drowning risk, -50%
            'underwater': 0.7,      # Difficult to rest, -30%
            'swamp': 0.75,          # Disease risk, -25%
            'desert': 0.9,          # Harsh conditions, -10%
            'flying': 0.95,         # Exposure, -5%
            'dungeon': 0.95,        # Underground, -5%
        }
        return terrain_mods.get(sector_type, 1.0)

    @staticmethod
    def _get_terrain_mana_modifier(sector_type: str) -> float:
        """Get mana regen modifier from terrain."""
        terrain_mods = {
            'inside': 1.0,
            'city': 0.95,           # Urban noise, -5%
            'field': 1.0,
            'forest': 1.05,         # Natural magic, +5%
            'hills': 1.0,
            'mountains': 1.05,      # High altitude clarity, +5%
            'water_swim': 1.0,
            'water_noswim': 1.0,
            'underwater': 1.1,      # Water magic, +10%
            'swamp': 0.9,           # Corrupted magic, -10%
            'desert': 0.95,         # Dry, less mana, -5%
            'flying': 1.05,         # Open to sky, +5%
            'dungeon': 1.0,
        }
        return terrain_mods.get(sector_type, 1.0)

    @staticmethod
    def _get_terrain_move_modifier(sector_type: str, character: 'Character') -> float:
        """Get move regen modifier from terrain."""
        terrain_mods = {
            'inside': 1.0,
            'city': 0.95,           # Hard surfaces, -5%
            'field': 1.0,
            'forest': 0.9,          # Rough terrain, -10%
            'hills': 0.9,           # Uphill, -10%
            'mountains': 0.8,       # Steep, -20%
            'water_swim': 0.7,      # Swimming exhausting, -30%
            'water_noswim': 0.5,    # Can't rest well, -50%
            'underwater': 0.6,      # Very exhausting, -40%
            'swamp': 0.7,           # Muddy, -30%
            'desert': 0.85,         # Hot and dry, -15%
            'flying': 1.0,
            'dungeon': 0.95,        # Dark, -5%
        }
        return terrain_mods.get(sector_type, 1.0)

    @staticmethod
    def _get_class_hp_modifier(char_class: str, sector_type: str) -> float:
        """Get HP regen modifier from class."""
        base_mods = {
            'warrior': 1.15,        # Tough, +15%
            'mage': 1.0,
            'cleric': 1.15,         # Divine healing, +15%
            'thief': 1.0,
            'ranger': 1.1,          # Hardy, +10%
            'paladin': 1.1,         # Divine protection, +10%
            'necromancer': 0.95,    # Undead affinity, -5%
            'bard': 1.0,
        }

        base = base_mods.get(char_class, 1.0)

        # Rangers get extra bonus in natural environments
        if char_class == 'ranger' and sector_type in ['forest', 'field', 'hills']:
            base *= 1.25  # Rangers excel in nature

        return base

    @staticmethod
    def _get_class_mana_modifier(char_class: str) -> float:
        """Get mana regen modifier from class."""
        class_mods = {
            'warrior': 0.8,         # Not magically attuned, -20%
            'mage': 1.2,            # Magical focus, +20%
            'cleric': 1.15,         # Divine connection, +15%
            'thief': 0.9,           # Some training, -10%
            'ranger': 1.0,
            'paladin': 1.05,        # Divine spark, +5%
            'necromancer': 1.15,    # Dark magic, +15%
            'bard': 1.1,            # Magical music, +10%
        }
        return class_mods.get(char_class, 1.0)

    @staticmethod
    def _get_class_move_modifier(char_class: str, sector_type: str) -> float:
        """Get move regen modifier from class."""
        base_mods = {
            'warrior': 1.0,
            'mage': 0.9,            # Bookish, -10%
            'cleric': 1.0,
            'thief': 1.1,           # Nimble, +10%
            'ranger': 1.15,         # Wilderness expert, +15%
            'paladin': 1.0,
            'necromancer': 0.95,    # Unhealthy, -5%
            'bard': 1.05,           # Performer stamina, +5%
        }

        base = base_mods.get(char_class, 1.0)

        # Rangers get massive bonus in natural environments
        if char_class == 'ranger' and sector_type in ['forest', 'field', 'hills']:
            base *= 1.25  # Rangers never tire in nature

        return base

    @staticmethod
    def _get_race_hp_modifier(race: str) -> float:
        """Get HP regen modifier from race."""
        race_mods = {
            'human': 1.0,
            'elf': 1.0,
            'dwarf': 1.15,          # Sturdy, +15%
            'halfling': 1.05,       # Resilient, +5%
            'half-orc': 1.1,        # Tough, +10%
            'gnome': 1.0,
            'dark elf': 0.95,       # Surface weakness, -5%
        }
        return race_mods.get(race.lower(), 1.0)

    @staticmethod
    def _get_race_mana_modifier(race: str) -> float:
        """Get mana regen modifier from race."""
        race_mods = {
            'human': 1.0,
            'elf': 1.1,             # Magical heritage, +10%
            'dwarf': 0.9,           # Earth-bound, -10%
            'halfling': 0.95,       # Some resistance, -5%
            'half-orc': 0.85,       # Not magically gifted, -15%
            'gnome': 1.05,          # Tinkerers, +5%
            'dark elf': 1.15,       # Innate magic, +15%
        }
        return race_mods.get(race.lower(), 1.0)

    @staticmethod
    def _get_race_move_modifier(race: str) -> float:
        """Get move regen modifier from race."""
        race_mods = {
            'human': 1.0,
            'elf': 1.05,            # Graceful, +5%
            'dwarf': 0.95,          # Short legs, -5%
            'halfling': 1.1,        # Surprisingly spry, +10%
            'half-orc': 1.0,
            'gnome': 0.9,           # Very short, -10%
            'dark elf': 1.05,       # Agile, +5%
        }
        return race_mods.get(race.lower(), 1.0)
