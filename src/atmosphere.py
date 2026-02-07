"""
Atmosphere System for RealmsMUD

Generates dynamic atmospheric descriptions based on:
- Time of day (dawn, morning, afternoon, dusk, evening, night)
- Weather conditions (rain, fog, storm, snow, clear)
- Season (spring, summer, autumn, winter)
- Room sector type (forest, city, underground, etc.)

This makes the world feel alive and immersive.
"""

import random
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from world import Room
    from time_system import GameTime
    from weather import Weather


class AtmosphereManager:
    """Generates atmospheric text for rooms based on conditions."""
    
    # Time-based descriptions for outdoor areas
    TIME_OUTDOOR = {
        'night': [
            "Stars glitter in the dark sky above.",
            "The night is quiet, broken only by distant sounds.",
            "Shadows pool in every corner under the moonless sky.",
            "A pale moon casts silver light across the land.",
            "The darkness seems to press in around you.",
        ],
        'dawn': [
            "The eastern sky blushes pink and gold with approaching dawn.",
            "Early morning mist clings to the ground.",
            "Birds begin their dawn chorus in the distance.",
            "The first rays of sunlight peek over the horizon.",
            "Dew glistens on every surface as day breaks.",
        ],
        'morning': [
            "Morning sunlight filters through, warming the air.",
            "The day is young and full of possibility.",
            "A gentle morning breeze carries fresh scents.",
            "The sun climbs steadily into a brightening sky.",
        ],
        'afternoon': [
            "The afternoon sun beats down warmly.",
            "Shadows have grown short as the sun reaches its peak.",
            "The day has settled into comfortable warmth.",
            "Afternoon light gives everything a golden hue.",
        ],
        'dusk': [
            "The sun sinks low, painting the sky in oranges and purples.",
            "Long shadows stretch across the ground as dusk approaches.",
            "The air cools as evening draws near.",
            "Twilight colors wash across the western sky.",
            "The day's heat fades with the setting sun.",
        ],
        'evening': [
            "The last light of day fades from the sky.",
            "Early stars begin to appear in the darkening heavens.",
            "A peaceful evening quiet settles over the land.",
            "The transition from day to night brings a calm stillness.",
        ],
    }
    
    # Time-based descriptions for indoor/city areas
    TIME_INDOOR = {
        'night': [
            "Torches flicker in their sconces, casting dancing shadows.",
            "The building is quiet at this late hour.",
            "Lamplight pushes back the darkness within.",
        ],
        'dawn': [
            "Early light seeps through windows and doorways.",
            "The place is just beginning to stir with activity.",
        ],
        'morning': [
            "Morning bustle fills the air with life.",
            "Sunlight streams in through windows.",
        ],
        'afternoon': [
            "The place is alive with afternoon activity.",
            "Warm light fills the interior spaces.",
        ],
        'dusk': [
            "Lamps are being lit as daylight fades.",
            "The pace of activity begins to slow with evening's approach.",
        ],
        'evening': [
            "Candlelight and torches illuminate the interior.",
            "The evening brings a different, quieter energy.",
        ],
    }
    
    # Weather descriptions for outdoor areas
    WEATHER_DESC = {
        'clear': [
            "The sky is clear and bright.",
            "Not a cloud mars the endless blue sky.",
        ],
        'partly_cloudy': [
            "Puffy white clouds drift lazily across the sky.",
            "The sun plays hide and seek behind scattered clouds.",
        ],
        'overcast': [
            "A blanket of grey clouds covers the sky.",
            "The overcast sky threatens rain but holds for now.",
            "Diffuse light filters through the cloud cover.",
        ],
        'rainy': [
            "Rain patters steadily from the grey sky.",
            "Raindrops splash in puddles all around you.",
            "A steady rain soaks everything it touches.",
            "The smell of rain fills the air.",
        ],
        'stormy': [
            "Thunder rumbles ominously in the distance.",
            "Lightning flickers through dark, roiling clouds.",
            "The storm rages with wind and driving rain.",
            "Nature's fury is on full display.",
        ],
        'snowy': [
            "Snowflakes drift down from the white sky.",
            "A blanket of white covers everything.",
            "Snow crunches underfoot with each step.",
        ],
        'foggy': [
            "Thick fog swirls around you, limiting visibility.",
            "The mist muffles sounds and obscures distances.",
            "Ghostly shapes loom in the fog.",
        ],
    }
    
    # Season descriptions
    SEASON_DESC = {
        'Spring': [
            "New growth pushes up through the thawing earth.",
            "The air carries the fresh scent of spring.",
            "Flowers are beginning to bloom.",
        ],
        'Summer': [
            "The warmth of summer is in full force.",
            "Lush green growth surrounds you.",
            "Insects buzz lazily in the summer heat.",
        ],
        'Autumn': [
            "Leaves display their autumn colors.",
            "A crisp autumn breeze carries fallen leaves.",
            "The air has a pleasant autumn chill.",
        ],
        'Winter': [
            "The cold bite of winter is in the air.",
            "Bare branches reach toward the grey sky.",
            "A winter chill seeps into your bones.",
        ],
    }
    
    # Sector-specific ambient descriptions
    SECTOR_AMBIENT = {
        'forest': [
            "Leaves rustle in the branches overhead.",
            "Birds call to each other in the canopy.",
            "The earthy scent of the forest fills your nostrils.",
            "Sunlight dapples through the leaves.",
        ],
        'field': [
            "Tall grass sways gently in the breeze.",
            "The open sky stretches endlessly above.",
            "Wildflowers dot the meadow with color.",
        ],
        'hills': [
            "The rolling terrain offers views of the surrounding land.",
            "Wind whispers across the hilltops.",
        ],
        'mountain': [
            "The thin mountain air is crisp and cold.",
            "Rocky crags jut upward toward the sky.",
            "The view from this height is breathtaking.",
        ],
        'desert': [
            "Heat shimmers rise from the sandy ground.",
            "The relentless sun beats down from above.",
            "Sand stretches endlessly in every direction.",
        ],
        'swamp': [
            "Murky water stretches between tufts of vegetation.",
            "The air is thick with humidity and strange smells.",
            "Insects buzz incessantly in the humid air.",
        ],
        'water_swim': [
            "Water laps gently at the shores.",
            "The surface ripples with unseen movement below.",
        ],
        'underground': [
            "The darkness presses in from all sides.",
            "Water drips somewhere in the distance.",
            "The air is cool and musty.",
        ],
        'city': [
            "The sounds of civilization surround you.",
            "People go about their daily business nearby.",
        ],
        'inside': [
            "The interior offers shelter from the outside.",
        ],
    }
    
    @staticmethod
    def get_time_period(game_time: Optional['GameTime']) -> str:
        """Get the current time period name."""
        if not game_time:
            return 'afternoon'
        
        hour = game_time.hour
        if 0 <= hour < 5:
            return 'night'
        elif 5 <= hour < 7:
            return 'dawn'
        elif 7 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 20:
            return 'dusk'
        else:
            return 'evening'
    
    @staticmethod
    def get_atmosphere(room: 'Room', game_time: Optional['GameTime'] = None,
                       weather: Optional['Weather'] = None) -> Optional[str]:
        """
        Generate atmospheric description for a room.
        
        Returns None if no atmospheric text should be added,
        otherwise returns a short atmospheric string.
        """
        # Skip for indoor non-city rooms most of the time
        outdoor_sectors = {
            'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim',
            'flying', 'desert', 'swamp'
        }
        city_sectors = {'city', 'inside'}
        underground_sectors = {'underground', 'cave'}
        
        sector = getattr(room, 'sector_type', 'inside')
        is_outdoor = sector in outdoor_sectors
        is_city = sector in city_sectors
        is_underground = sector in underground_sectors
        
        # Only generate atmosphere 40% of the time to avoid spam
        if random.random() > 0.4:
            return None
        
        descriptions = []
        
        # Time-based description
        time_period = AtmosphereManager.get_time_period(game_time)
        if is_outdoor:
            time_descs = AtmosphereManager.TIME_OUTDOOR.get(time_period, [])
        elif is_city or is_underground:
            time_descs = AtmosphereManager.TIME_INDOOR.get(time_period, [])
        else:
            time_descs = []
        
        if time_descs and random.random() < 0.5:
            descriptions.append(random.choice(time_descs))
        
        # Weather description (outdoor only)
        if is_outdoor and weather:
            sky = getattr(weather, 'sky_condition', 'clear')
            weather_descs = AtmosphereManager.WEATHER_DESC.get(sky, [])
            if weather_descs and random.random() < 0.4:
                descriptions.append(random.choice(weather_descs))
        
        # Season description (outdoor only, rare)
        if is_outdoor and game_time and random.random() < 0.15:
            season = game_time.get_season() if hasattr(game_time, 'get_season') else 'Summer'
            season_descs = AtmosphereManager.SEASON_DESC.get(season, [])
            if season_descs:
                descriptions.append(random.choice(season_descs))
        
        # Sector ambient description (rare)
        if random.random() < 0.2:
            ambient_descs = AtmosphereManager.SECTOR_AMBIENT.get(sector, [])
            if ambient_descs:
                descriptions.append(random.choice(ambient_descs))
        
        if not descriptions:
            return None
        
        # Return just one description to keep it concise
        return random.choice(descriptions)
    
    @staticmethod
    def get_transition_message(old_room: 'Room', new_room: 'Room',
                               game_time: Optional['GameTime'] = None) -> Optional[str]:
        """
        Generate a message when transitioning between different room types.
        For example, going from inside to outside, or into a cave.
        """
        old_sector = getattr(old_room, 'sector_type', 'inside') if old_room else 'inside'
        new_sector = getattr(new_room, 'sector_type', 'inside')
        
        outdoor = {'field', 'forest', 'hills', 'mountain', 'desert', 'swamp'}
        indoor = {'inside', 'city'}
        underground = {'underground', 'cave'}
        
        # Going from inside to outside
        if old_sector in indoor and new_sector in outdoor:
            time_period = AtmosphereManager.get_time_period(game_time)
            if time_period == 'night':
                return "You step out into the cool night air."
            elif time_period == 'dawn':
                return "You emerge into the soft light of dawn."
            elif time_period in ('morning', 'afternoon'):
                return "Sunlight washes over you as you step outside."
            elif time_period == 'dusk':
                return "The fading daylight greets you outside."
            else:
                return "You step out into the evening air."
        
        # Going from outside to inside
        if old_sector in outdoor and new_sector in indoor:
            return "You enter, leaving the outside behind."
        
        # Going underground
        if old_sector not in underground and new_sector in underground:
            return "The air grows cool and damp as you descend."
        
        # Coming out of underground
        if old_sector in underground and new_sector not in underground:
            return "Fresh air fills your lungs as you emerge."
        
        return None
