"""
Weather System

Provides dynamic weather conditions that affect gameplay including:
- Spell damage modifiers (lightning stronger in storms, fire weaker in rain)
- Movement costs (rain/snow makes travel harder)
- Vision/perception
- Atmospheric descriptions
"""

import random
import logging
from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from time_system import GameTime

logger = logging.getLogger(__name__)


class Weather:
    """
    Manages weather conditions for a zone.

    Weather changes gradually over time and is influenced by:
    - Time of day
    - Season
    - Random variation
    """

    # Sky condition types
    SKY_CLEAR = 'clear'
    SKY_PARTLY_CLOUDY = 'partly_cloudy'
    SKY_OVERCAST = 'overcast'
    SKY_RAINY = 'rainy'
    SKY_STORMY = 'stormy'
    SKY_SNOWY = 'snowy'
    SKY_FOGGY = 'foggy'

    # Precipitation types
    PRECIP_NONE = 'none'
    PRECIP_DRIZZLE = 'drizzle'
    PRECIP_LIGHT_RAIN = 'light_rain'
    PRECIP_HEAVY_RAIN = 'heavy_rain'
    PRECIP_SNOW = 'snow'
    PRECIP_SLEET = 'sleet'
    PRECIP_HAIL = 'hail'

    def __init__(self, zone_number: int):
        """
        Initialize weather for a zone.

        Args:
            zone_number: The zone this weather belongs to
        """
        self.zone_number = zone_number
        self.sky_condition = self.SKY_CLEAR
        self.precipitation = self.PRECIP_NONE
        self.temperature = 65  # Degrees F (reasonable default)
        self.wind_speed = 5    # MPH
        self.humidity = 50     # Percentage

        # Internal state for weather transitions
        self._weather_change_timer = 0
        self._weather_change_threshold = random.randint(30, 60)  # Minutes

    def update_weather(self, game_time: 'GameTime'):
        """
        Update weather conditions based on passage of time.

        Args:
            game_time: Current game time for seasonal/time-of-day effects
        """
        self._weather_change_timer += 1

        # Check if it's time for a weather change
        if self._weather_change_timer >= self._weather_change_threshold:
            self._weather_change_timer = 0
            self._weather_change_threshold = random.randint(30, 60)

            # Determine new weather based on season and current conditions
            self._transition_weather(game_time)

        # Update temperature based on time of day
        self._update_temperature(game_time)

    def _transition_weather(self, game_time: 'GameTime'):
        """
        Gradually transition weather to a new state.

        Args:
            game_time: Current game time
        """
        season = game_time.get_season()

        # Weather transition probabilities by season
        if season == 'Winter':
            transitions = self._get_winter_transitions()
        elif season == 'Spring':
            transitions = self._get_spring_transitions()
        elif season == 'Summer':
            transitions = self._get_summer_transitions()
        else:  # Autumn
            transitions = self._get_autumn_transitions()

        # Choose new weather based on current conditions
        current_weights = transitions.get(self.sky_condition, {})
        if current_weights:
            conditions = list(current_weights.keys())
            weights = list(current_weights.values())
            self.sky_condition = random.choices(conditions, weights=weights)[0]

        # Update precipitation based on sky condition
        self._update_precipitation()

        # Update wind and humidity
        self._update_wind_and_humidity()

        logger.debug(f"Zone {self.zone_number} weather changed to: {self.sky_condition}")

    def _get_winter_transitions(self) -> Dict[str, Dict[str, int]]:
        """Get weather transition probabilities for winter."""
        return {
            self.SKY_CLEAR: {
                self.SKY_CLEAR: 40,
                self.SKY_PARTLY_CLOUDY: 30,
                self.SKY_OVERCAST: 20,
                self.SKY_SNOWY: 10,
            },
            self.SKY_PARTLY_CLOUDY: {
                self.SKY_CLEAR: 20,
                self.SKY_PARTLY_CLOUDY: 30,
                self.SKY_OVERCAST: 30,
                self.SKY_SNOWY: 20,
            },
            self.SKY_OVERCAST: {
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_OVERCAST: 30,
                self.SKY_SNOWY: 40,
                self.SKY_FOGGY: 10,
            },
            self.SKY_SNOWY: {
                self.SKY_OVERCAST: 30,
                self.SKY_SNOWY: 30,
                self.SKY_CLEAR: 20,
                self.SKY_PARTLY_CLOUDY: 20,
            },
            self.SKY_FOGGY: {
                self.SKY_FOGGY: 30,
                self.SKY_OVERCAST: 30,
                self.SKY_CLEAR: 20,
                self.SKY_PARTLY_CLOUDY: 20,
            },
        }

    def _get_spring_transitions(self) -> Dict[str, Dict[str, int]]:
        """Get weather transition probabilities for spring."""
        return {
            self.SKY_CLEAR: {
                self.SKY_CLEAR: 30,
                self.SKY_PARTLY_CLOUDY: 40,
                self.SKY_OVERCAST: 20,
                self.SKY_RAINY: 10,
            },
            self.SKY_PARTLY_CLOUDY: {
                self.SKY_CLEAR: 25,
                self.SKY_PARTLY_CLOUDY: 30,
                self.SKY_OVERCAST: 25,
                self.SKY_RAINY: 20,
            },
            self.SKY_OVERCAST: {
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_OVERCAST: 25,
                self.SKY_RAINY: 40,
                self.SKY_STORMY: 15,
            },
            self.SKY_RAINY: {
                self.SKY_OVERCAST: 30,
                self.SKY_RAINY: 25,
                self.SKY_STORMY: 20,
                self.SKY_PARTLY_CLOUDY: 25,
            },
            self.SKY_STORMY: {
                self.SKY_RAINY: 40,
                self.SKY_OVERCAST: 30,
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_CLEAR: 10,
            },
        }

    def _get_summer_transitions(self) -> Dict[str, Dict[str, int]]:
        """Get weather transition probabilities for summer."""
        return {
            self.SKY_CLEAR: {
                self.SKY_CLEAR: 50,
                self.SKY_PARTLY_CLOUDY: 35,
                self.SKY_OVERCAST: 10,
                self.SKY_STORMY: 5,
            },
            self.SKY_PARTLY_CLOUDY: {
                self.SKY_CLEAR: 40,
                self.SKY_PARTLY_CLOUDY: 35,
                self.SKY_OVERCAST: 15,
                self.SKY_STORMY: 10,
            },
            self.SKY_OVERCAST: {
                self.SKY_PARTLY_CLOUDY: 25,
                self.SKY_OVERCAST: 25,
                self.SKY_STORMY: 30,
                self.SKY_RAINY: 20,
            },
            self.SKY_RAINY: {
                self.SKY_OVERCAST: 30,
                self.SKY_STORMY: 30,
                self.SKY_PARTLY_CLOUDY: 25,
                self.SKY_CLEAR: 15,
            },
            self.SKY_STORMY: {
                self.SKY_RAINY: 30,
                self.SKY_OVERCAST: 25,
                self.SKY_PARTLY_CLOUDY: 25,
                self.SKY_CLEAR: 20,
            },
        }

    def _get_autumn_transitions(self) -> Dict[str, Dict[str, int]]:
        """Get weather transition probabilities for autumn."""
        return {
            self.SKY_CLEAR: {
                self.SKY_CLEAR: 35,
                self.SKY_PARTLY_CLOUDY: 35,
                self.SKY_OVERCAST: 20,
                self.SKY_FOGGY: 10,
            },
            self.SKY_PARTLY_CLOUDY: {
                self.SKY_CLEAR: 25,
                self.SKY_PARTLY_CLOUDY: 30,
                self.SKY_OVERCAST: 30,
                self.SKY_RAINY: 15,
            },
            self.SKY_OVERCAST: {
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_OVERCAST: 30,
                self.SKY_RAINY: 35,
                self.SKY_FOGGY: 15,
            },
            self.SKY_RAINY: {
                self.SKY_OVERCAST: 35,
                self.SKY_RAINY: 30,
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_CLEAR: 15,
            },
            self.SKY_FOGGY: {
                self.SKY_FOGGY: 35,
                self.SKY_OVERCAST: 30,
                self.SKY_PARTLY_CLOUDY: 20,
                self.SKY_CLEAR: 15,
            },
        }

    def _update_precipitation(self):
        """Update precipitation based on sky condition."""
        precip_map = {
            self.SKY_CLEAR: self.PRECIP_NONE,
            self.SKY_PARTLY_CLOUDY: self.PRECIP_NONE,
            self.SKY_OVERCAST: self.PRECIP_NONE if random.random() > 0.3 else self.PRECIP_DRIZZLE,
            self.SKY_RAINY: self.PRECIP_LIGHT_RAIN if random.random() > 0.3 else self.PRECIP_HEAVY_RAIN,
            self.SKY_STORMY: self.PRECIP_HEAVY_RAIN if random.random() > 0.2 else self.PRECIP_HAIL,
            self.SKY_SNOWY: self.PRECIP_SNOW,
            self.SKY_FOGGY: self.PRECIP_NONE,
        }
        self.precipitation = precip_map.get(self.sky_condition, self.PRECIP_NONE)

    def _update_wind_and_humidity(self):
        """Update wind speed and humidity based on weather."""
        wind_map = {
            self.SKY_CLEAR: (3, 8),
            self.SKY_PARTLY_CLOUDY: (5, 12),
            self.SKY_OVERCAST: (8, 15),
            self.SKY_RAINY: (10, 20),
            self.SKY_STORMY: (20, 40),
            self.SKY_SNOWY: (12, 25),
            self.SKY_FOGGY: (2, 5),
        }
        min_wind, max_wind = wind_map.get(self.sky_condition, (5, 10))
        self.wind_speed = random.randint(min_wind, max_wind)

        humidity_map = {
            self.SKY_CLEAR: (30, 50),
            self.SKY_PARTLY_CLOUDY: (40, 60),
            self.SKY_OVERCAST: (60, 80),
            self.SKY_RAINY: (80, 95),
            self.SKY_STORMY: (85, 100),
            self.SKY_SNOWY: (70, 90),
            self.SKY_FOGGY: (90, 100),
        }
        min_hum, max_hum = humidity_map.get(self.sky_condition, (50, 70))
        self.humidity = random.randint(min_hum, max_hum)

    def _update_temperature(self, game_time: 'GameTime'):
        """Update temperature based on time of day and season."""
        season = game_time.get_season()

        # Base temperatures by season (midday)
        base_temps = {
            'Winter': 35,
            'Spring': 60,
            'Summer': 80,
            'Autumn': 55,
        }
        base_temp = base_temps.get(season, 60)

        # Time of day modifier
        hour = game_time.hour
        if 0 <= hour < 6:
            # Night - coldest
            temp_modifier = -15
        elif 6 <= hour < 12:
            # Morning - warming up
            temp_modifier = -5
        elif 12 <= hour < 18:
            # Afternoon - warmest
            temp_modifier = 5
        else:
            # Evening - cooling down
            temp_modifier = -10

        # Weather modifier
        weather_mod = {
            self.SKY_CLEAR: 0,
            self.SKY_PARTLY_CLOUDY: -2,
            self.SKY_OVERCAST: -5,
            self.SKY_RAINY: -8,
            self.SKY_STORMY: -10,
            self.SKY_SNOWY: -20,
            self.SKY_FOGGY: -5,
        }

        self.temperature = base_temp + temp_modifier + weather_mod.get(self.sky_condition, 0)

    def get_weather_desc(self) -> str:
        """
        Get a descriptive string of current weather.

        Returns:
            Description of weather conditions
        """
        sky_descs = {
            self.SKY_CLEAR: "The sky is clear and bright",
            self.SKY_PARTLY_CLOUDY: "A few clouds drift across the sky",
            self.SKY_OVERCAST: "The sky is overcast with grey clouds",
            self.SKY_RAINY: "Rain falls steadily from the sky",
            self.SKY_STORMY: "A fierce storm rages overhead",
            self.SKY_SNOWY: "Snow falls gently from the clouded sky",
            self.SKY_FOGGY: "A thick fog obscures your vision",
        }

        desc = sky_descs.get(self.sky_condition, "The weather is unremarkable")

        # Add wind description
        if self.wind_speed > 25:
            desc += ", and strong winds blow"
        elif self.wind_speed > 15:
            desc += ", and a steady wind blows"
        elif self.wind_speed > 8:
            desc += ", and a light breeze blows"

        desc += "."
        return desc

    def get_vision_modifier(self) -> float:
        """
        Get vision/perception modifier from weather.

        Returns:
            Multiplier for vision range (1.0 = normal, 0.5 = half vision)
        """
        vision_mods = {
            self.SKY_CLEAR: 1.0,
            self.SKY_PARTLY_CLOUDY: 1.0,
            self.SKY_OVERCAST: 0.9,
            self.SKY_RAINY: 0.7,
            self.SKY_STORMY: 0.5,
            self.SKY_SNOWY: 0.6,
            self.SKY_FOGGY: 0.4,
        }
        return vision_mods.get(self.sky_condition, 1.0)

    def get_movement_modifier(self) -> float:
        """
        Get movement cost modifier from weather.

        Returns:
            Multiplier for movement costs (1.0 = normal, 1.5 = 50% more costly)
        """
        movement_mods = {
            self.SKY_CLEAR: 1.0,
            self.SKY_PARTLY_CLOUDY: 1.0,
            self.SKY_OVERCAST: 1.0,
            self.SKY_RAINY: 1.2,
            self.SKY_STORMY: 1.5,
            self.SKY_SNOWY: 1.4,
            self.SKY_FOGGY: 1.1,
        }
        return movement_mods.get(self.sky_condition, 1.0)

    def get_spell_modifier(self, spell_name: str) -> float:
        """
        Get spell damage/effect modifier based on weather.

        Args:
            spell_name: Name of the spell

        Returns:
            Damage multiplier (1.0 = normal, 1.5 = 50% more damage)
        """
        # Lightning spells
        if 'lightning' in spell_name.lower() or 'shock' in spell_name.lower():
            if self.sky_condition == self.SKY_STORMY:
                return 1.5  # +50% in storms
            elif self.sky_condition == self.SKY_RAINY:
                return 1.2  # +20% in rain

        # Fire spells
        if 'fire' in spell_name.lower() or 'flame' in spell_name.lower() or 'burn' in spell_name.lower():
            if self.sky_condition in [self.SKY_RAINY, self.SKY_STORMY]:
                return 0.8  # -20% in wet conditions
            elif self.sky_condition == self.SKY_SNOWY:
                return 0.7  # -30% in snow

        # Cold/Ice spells
        if 'chill' in spell_name.lower() or 'ice' in spell_name.lower() or 'frost' in spell_name.lower():
            if self.sky_condition == self.SKY_SNOWY:
                return 1.3  # +30% in snow
            elif self.temperature < 40:
                return 1.2  # +20% when cold

        # Call lightning (special case - only works outdoors in storms)
        if spell_name.lower() == 'call_lightning':
            if self.sky_condition in [self.SKY_STORMY, self.SKY_RAINY]:
                return 2.0  # Double damage
            else:
                return 0.0  # Doesn't work without storm

        # Fog/cloud spells
        if 'fog' in spell_name.lower() or 'cloud' in spell_name.lower():
            if self.sky_condition == self.SKY_FOGGY:
                return 1.5  # +50% in fog

        return 1.0  # No modifier

    def to_dict(self) -> Dict:
        """
        Serialize weather to a dictionary.

        Returns:
            Dictionary containing weather state
        """
        return {
            'sky_condition': self.sky_condition,
            'precipitation': self.precipitation,
            'temperature': self.temperature,
            'wind_speed': self.wind_speed,
            'humidity': self.humidity,
            'change_timer': self._weather_change_timer,
            'change_threshold': self._weather_change_threshold,
        }

    @classmethod
    def from_dict(cls, zone_number: int, data: Dict) -> 'Weather':
        """
        Load weather from a dictionary.

        Args:
            zone_number: Zone this weather belongs to
            data: Dictionary containing weather state

        Returns:
            Weather instance
        """
        weather = cls(zone_number)
        weather.sky_condition = data.get('sky_condition', cls.SKY_CLEAR)
        weather.precipitation = data.get('precipitation', cls.PRECIP_NONE)
        weather.temperature = data.get('temperature', 65)
        weather.wind_speed = data.get('wind_speed', 5)
        weather.humidity = data.get('humidity', 50)
        weather._weather_change_timer = data.get('change_timer', 0)
        weather._weather_change_threshold = data.get('change_threshold', 30)
        return weather
