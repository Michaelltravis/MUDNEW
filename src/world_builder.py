"""
RealmsMUD World Builder
=======================
Creates the default fantasy world with zones, rooms, NPCs, and items.
"""

import os
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world import World, Zone, Room

from config import Config

logger = logging.getLogger('RealmsMUD.WorldBuilder')


class WorldBuilder:
    """Builds the default fantasy world."""
    
    def __init__(self, world: 'World'):
        self.world = world
        self.config = Config()
        
    async def build_default_world(self):
        """Build the entire default world."""
        logger.info("Building default fantasy world...")
        
        # Create zones
        await self.create_limbo_zone()
        await self.create_midgaard_zone()
        await self.create_forest_zone()
        await self.create_castle_zone()
        await self.create_goblin_caves_zone()
        await self.create_undead_crypt_zone()
        await self.create_dragon_lair_zone()
        
        # Save all zones
        await self.save_zones()
        
        logger.info("Default world built successfully!")
        
    async def create_limbo_zone(self):
        """Create the Limbo zone (admin area)."""
        from world import Zone, Room
        
        zone = Zone(0)
        zone.name = "Limbo - The Void"
        zone.builders = "Immortals"
        zone.top = 99
        zone.lifespan = 999  # effectively never resets
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Room 1: The Void
        room = Room(1)
        room.name = "The Void"
        room.description = """You float in an endless expanse of nothing. There is no up, no down,
no left, no right. Just infinite darkness stretching in all directions.
This is the place between places, where lost souls drift eternally.
A faint shimmer to the south suggests a way back to reality."""
        room.sector_type = "flying"
        room.zone = zone
        room.exits = {'south': {'to_room': 3001, 'description': 'A shimmer leads to the mortal realm.'}}
        zone.rooms[1] = room
        
        # Immortal lounge
        room = Room(2)
        room.name = "The Immortal Lounge"
        room.description = """Golden light suffuses this magnificent chamber. Plush divans and 
comfortable chairs are arranged around a roaring fireplace. Crystal 
decanters filled with celestial wine line the walls. This is where the
gods rest between their divine duties."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {'down': {'to_room': 1}}
        zone.rooms[2] = room
        
        self.world.zones[0] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
            
    async def create_midgaard_zone(self):
        """Create the main city zone - Midgaard."""
        from world import Zone, Room
        
        zone = Zone(30)
        zone.name = "The City of Midgaard"
        zone.builders = "Realmers"
        zone.top = 3099
        zone.lifespan = 2  # 30 min (2 ticks × 15 min)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Room 3001: Temple of Midgaard (starting room)
        room = Room(3001)
        room.name = "The Temple of Midgaard"
        room.description = """You stand in the grand Temple of Midgaard, a place of healing and
sanctuary for weary adventurers. Towering marble columns rise to a
vaulted ceiling painted with scenes of ancient heroes. Soft candlelight
illuminates the altar at the center, where priests tend to the wounded.
The exit leads south to the main square of the city."""
        room.sector_type = "inside"
        room.zone = zone
        room.flags.add('peaceful')
        room.flags.add('no_mob')
        room.exits = {'south': {'to_room': 3002}}
        room.mob_resets = [{'vnum': 3001, 'max': 1}, {'vnum': 3200, 'max': 1}]  # Temple healer + Sage Aldric
        zone.rooms[3001] = room
        
        # Room 3002: Temple Square
        room = Room(3002)
        room.name = "Temple Square"
        room.description = """The cobblestone square stretches before you, bustling with activity.
Merchants hawk their wares, children play between the market stalls,
and guards patrol the perimeter. The Temple of Midgaard rises to the
north, its white marble gleaming in the sunlight. A magnificent marble
fountain gurgles peacefully in the center, its crystal waters sparkling.
The main road extends east and west, while a narrow alley leads south."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'north': {'to_room': 3001},
            'east': {'to_room': 3003},
            'west': {'to_room': 3005},
            'south': {'to_room': 3010}
        }
        room.mob_resets = [{'vnum': 3002, 'max': 2}]  # City guards
        room.obj_resets = [{'vnum': 3035, 'max': 1}]  # Marble fountain
        zone.rooms[3002] = room
        
        # Room 3003: Main Street East
        room = Room(3003)
        room.name = "Main Street East"
        room.description = """The eastern section of Main Street is lined with prosperous shops and
taverns. The smell of fresh bread wafts from a bakery, mingling with
the sound of a blacksmith's hammer. A large weapons shop stands to the
north, its windows displaying gleaming swords and armor."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'west': {'to_room': 3002},
            'east': {'to_room': 3004},
            'north': {'to_room': 3020},
            'south': {'to_room': 3015}
        }
        zone.rooms[3003] = room
        
        # Room 3004: East Gate
        room = Room(3004)
        room.name = "East Gate of Midgaard"
        room.description = """The massive stone gates of Midgaard loom before you. Two enormous 
towers flank the archway, and guards in chain mail scrutinize all who
pass. Beyond the gates, a dirt road leads east into the wilderness,
toward the Haon Dor forest. The safety of the city lies to the west."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'west': {'to_room': 3003},
            'east': {'to_room': 4001}  # Forest entrance
        }
        room.mob_resets = [{'vnum': 3002, 'max': 2}]  # Gate guards
        zone.rooms[3004] = room
        
        # Room 3005: Main Street West
        room = Room(3005)
        room.name = "Main Street West"
        room.description = """The western stretch of Main Street is home to the city's craftsmen.
A carpenter's shop, a tanner's stall, and a jeweler's boutique line
the street. The sounds of industry fill the air. To the north, a sign
reading 'The Prancing Pony Inn' swings gently in the breeze."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'east': {'to_room': 3002},
            'west': {'to_room': 3006},
            'north': {'to_room': 3030}  # Inn
        }
        zone.rooms[3005] = room
        
        # Room 3006: West Gate
        room = Room(3006)
        room.name = "West Gate of Midgaard"
        room.description = """The western gate of Midgaard opens onto a road leading to distant
mountains. The gate is smaller than its eastern counterpart but no
less fortified. Merchants with loaded wagons queue to enter the city,
their goods bound for the markets. To the west, adventure awaits."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'east': {'to_room': 3005},
            'west': {'to_room': 5001}  # Castle road
        }
        room.mob_resets = [{'vnum': 3002, 'max': 1}]
        zone.rooms[3006] = room
        
        # Room 3010: South Alley
        room = Room(3010)
        room.name = "A Dark Alley"
        room.description = """This narrow alley winds between tall buildings, barely wide enough
for two people to pass. Shadows pool in the corners, and you can't
shake the feeling of being watched. The city's less savory elements
are known to frequent this area after dark."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'north': {'to_room': 3002},
            'south': {'to_room': 3011}
        }
        room.mob_resets = [{'vnum': 3005, 'max': 2}]  # Thieves
        zone.rooms[3010] = room
        
        # Room 3011: Thieves' Den Entrance
        room = Room(3011)
        room.name = "A Dead End"
        room.description = """The alley ends abruptly at a crumbling brick wall. Graffiti marks
the stones, and broken bottles litter the ground. However, keen eyes
might notice that one section of the wall seems different from the
rest - a hidden door, perhaps?"""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'north': {'to_room': 3010},
            'down': {'to_room': 3012}  # Secret passage
        }
        zone.rooms[3011] = room
        
        # Room 3012: Thieves' Guild
        room = Room(3012)
        room.name = "The Thieves' Guild"
        room.description = """You've discovered the legendary Thieves' Guild of Midgaard. The
underground chamber is dimly lit by guttering torches. Hooded figures
converse in hushed tones at tables scattered about the room. A bar
serves drinks of dubious origin, and a guildmaster sits in shadows."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {'up': {'to_room': 3011}}
        room.mob_resets = [
            {'vnum': 3006, 'max': 1},  # Guildmaster
            {'vnum': 3005, 'max': 3}   # Thieves
        ]
        zone.rooms[3012] = room

        # Room 3015: Adventurer's Guild
        room = Room(3015)
        room.name = "The Adventurer's Guild"
        room.description = """A wide hall filled with maps, trophies, and the chatter of seasoned
adventurers. A large bulletin board lists bounties and dungeon notices,
while a guild steward records the names of those brave enough to delve
the unknown. A sturdy door to the north leads back to the city streets."""
        room.sector_type = "inside"
        room.zone = zone
        room.flags.add('peaceful')
        room.flags.add('no_mob')
        room.exits = {'north': {'to_room': 3003}}
        zone.rooms[3015] = room
        
        # Room 3020: Weapons Shop
        room = Room(3020)
        room.name = "Grimtooth's Weapons Emporium"
        room.description = """Weapons of every description line the walls of this shop. Swords,
axes, maces, and more exotic implements of destruction gleam under
magical lighting. A burly dwarf named Grimtooth tends the counter,
his own battleaxe never far from reach. Type 'list' to see his wares."""
        room.sector_type = "inside"
        room.zone = zone
        room.flags.add('no_mob')
        room.exits = {'south': {'to_room': 3003}}
        room.mob_resets = [{'vnum': 3003, 'max': 1}]  # Grimtooth
        zone.rooms[3020] = room
        
        # Room 3030: The Prancing Pony Inn
        room = Room(3030)
        room.name = "The Prancing Pony Inn"
        room.description = """The common room of the Prancing Pony is warm and inviting. A 
cheerful fire crackles in the hearth, and the smell of roasting meat
fills the air. Travelers from far and wide gather here to share tales
of adventure over mugs of ale. Rooms are available upstairs."""
        room.sector_type = "inside"
        room.zone = zone
        room.flags.add('peaceful')
        room.exits = {
            'south': {'to_room': 3005},
            'up': {'to_room': 3031}
        }
        room.mob_resets = [
            {'vnum': 3004, 'max': 1},  # Innkeeper
        ]
        room.obj_resets = [{'vnum': 20, 'max': 1}]  # Bulletin board
        zone.rooms[3030] = room
        
        # Room 3031: Inn Upstairs
        room = Room(3031)
        room.name = "Upstairs Hallway"
        room.description = """A narrow hallway with doors leading to private rooms. The wooden
floor creaks underfoot. A window at the end provides a view of the
city below. This is a peaceful place where adventurers can rest."""
        room.sector_type = "inside"
        room.zone = zone
        room.flags.add('peaceful')
        room.exits = {'down': {'to_room': 3030}}
        zone.rooms[3031] = room
        
        # Add zone mobs
        zone.mobs = {
            3001: {
                'vnum': 3001,
                'name': 'the temple healer',
                'short_desc': 'A kindly temple healer',
                'long_desc': 'A robed priest tends to the altar, ready to heal the wounded.',
                'level': 25,
                'hp_dice': '10d10+100',
                'damage_dice': '1d4+2',
                'gold': 50,
                'exp': 0,
                'alignment': 1000,
                'faction': 'midgaard',
                'flags': ['sentinel', 'helper'],
                'special': 'healer'
            },
            3200: {
                'vnum': 3200,
                'name': 'Sage Aldric',
                'short_desc': 'Sage Aldric, guide of new adventurers',
                'long_desc': 'An elderly sage in deep blue robes stands here, his kind eyes watching for newcomers.',
                'level': 30,
                'hp_dice': '10d10+200',
                'damage_dice': '1d4+1',
                'gold': 0,
                'exp': 0,
                'alignment': 1000,
                'faction': 'midgaard',
                'flags': ['sentinel', 'helper'],
                'special': 'sage_aldric'
            },
            3002: {
                'vnum': 3002,
                'name': 'a city guard',
                'short_desc': 'A vigilant city guard',
                'long_desc': 'A guard in chain mail patrols the area, watching for trouble.',
                'level': 15,
                'hp_dice': '5d10+50',
                'damage_dice': '2d6+3',
                'gold': 20,
                'exp': 500,
                'alignment': 500,
                'faction': 'midgaard',
                'flags': ['sentinel', 'helper'],
                'special': None
            },
            3003: {
                'vnum': 3003,
                'name': 'Grimtooth',
                'short_desc': 'Grimtooth the dwarf weaponsmith',
                'long_desc': 'A gruff dwarf stands behind the counter, appraising his wares.',
                'level': 30,
                'hp_dice': '15d10+150',
                'damage_dice': '3d8+5',
                'gold': 1000,
                'exp': 0,
                'alignment': 0,
                'faction': 'dwarves',
                'flags': ['sentinel', 'shopkeeper'],
                'special': 'shopkeeper'
            },
            3004: {
                'vnum': 3004,
                'name': 'the innkeeper',
                'short_desc': 'A jovial innkeeper',
                'long_desc': 'The innkeeper polishes glasses, ready to serve weary travelers.',
                'level': 10,
                'hp_dice': '3d10+30',
                'damage_dice': '1d4+1',
                'gold': 100,
                'exp': 0,
                'alignment': 200,
                'faction': 'midgaard',
                'flags': ['sentinel'],
                'special': None
            },
            3005: {
                'vnum': 3005,
                'name': 'a shady thief',
                'short_desc': 'A shifty-eyed thief',
                'long_desc': 'A cloaked figure lurks in the shadows, eyeing your purse.',
                'level': 8,
                'hp_dice': '3d10+20',
                'damage_dice': '1d6+2',
                'gold': 30,
                'exp': 400,
                'alignment': -200,
                'faction': 'thieves_guild',
                'faction_rep': {'thieves_guild': -10, 'midgaard': 5},
                'flags': ['thief', 'aggressive'],
                'special': None
            },
            3006: {
                'vnum': 3006,
                'name': 'the Guildmaster',
                'short_desc': 'The mysterious Guildmaster',
                'long_desc': 'A hooded figure sits in shadow, the Guildmaster of Thieves.',
                'level': 40,
                'hp_dice': '20d10+200',
                'damage_dice': '4d6+8',
                'gold': 500,
                'exp': 5000,
                'alignment': -500,
                'faction': 'thieves_guild',
                'min_rep_talk_level': 'Friendly',
                'flags': ['sentinel'],
                'special': 'trainer'
            },
        }
        
        # Add zone objects
        zone.objects = {
            1: {'vnum': 1, 'name': 'a loaf of bread', 'short_desc': 'a loaf of bread',
                'room_desc': 'A loaf of fresh bread lies here.', 'type': 'food',
                'weight': 1, 'cost': 5, 'food_value': 12},
            2: {'vnum': 2, 'name': 'a waterskin', 'short_desc': 'a leather waterskin',
                'room_desc': 'A waterskin lies here.', 'type': 'drink',
                'weight': 2, 'cost': 10, 'drinks': 20, 'liquid': 'water'},
            3: {'vnum': 3, 'name': 'a torch', 'short_desc': 'a burning torch',
                'room_desc': 'A torch flickers here.', 'type': 'light',
                'weight': 1, 'cost': 5, 'light_hours': 24},
            10: {'vnum': 10, 'name': 'a short sword', 'short_desc': 'a short sword',
                 'room_desc': 'A short sword lies here.', 'type': 'weapon',
                 'weight': 5, 'cost': 50, 'damage_dice': '1d6', 'weapon_type': 'slash'},
            11: {'vnum': 11, 'name': 'a dagger', 'short_desc': 'a sharp dagger',
                 'room_desc': 'A dagger glints on the ground.', 'type': 'weapon',
                 'weight': 2, 'cost': 20, 'damage_dice': '1d4', 'weapon_type': 'stab'},
            12: {'vnum': 12, 'name': 'a mace', 'short_desc': 'a heavy mace',
                 'room_desc': 'A mace lies here.', 'type': 'weapon',
                 'weight': 8, 'cost': 40, 'damage_dice': '1d8', 'weapon_type': 'pound'},
            13: {'vnum': 13, 'name': 'a short bow', 'short_desc': 'a short bow',
                 'room_desc': 'A short bow lies here.', 'type': 'weapon',
                 'weight': 3, 'cost': 30, 'damage_dice': '1d6', 'weapon_type': 'pierce'},
            14: {'vnum': 14, 'name': 'a rapier', 'short_desc': 'an elegant rapier',
                 'room_desc': 'A rapier lies here.', 'type': 'weapon',
                 'weight': 3, 'cost': 60, 'damage_dice': '1d6', 'weapon_type': 'pierce'},
            20: {'vnum': 20, 'name': 'a bulletin board', 'short_desc': 'a large bulletin board',
                 'room_desc': 'A bulletin board is mounted on the wall.', 'type': 'other',
                 'weight': 100, 'cost': 0},
            3035: {'vnum': 3035, 'name': 'marble fountain', 'short_desc': 'a marble fountain',
                   'room_desc': 'A magnificent marble fountain gurgles with crystal-clear water.',
                   'type': 'fountain', 'weight': 500, 'cost': 0, 'drink_value': 12,
                   'liquid': 'water'},
        }
        
        self.world.zones[30] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def create_forest_zone(self):
        """Create the Haon Dor forest zone."""
        from world import Zone, Room
        
        zone = Zone(40)
        zone.name = "Haon Dor Forest"
        zone.builders = "Realmers"
        zone.top = 4099
        zone.lifespan = 2  # ~20 min (rounded to 2 ticks)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Forest entrance
        room = Room(4001)
        room.name = "The Forest Road"
        room.description = """The cobblestone road from Midgaard gives way to a dirt path as
you enter the ancient Haon Dor forest. Massive oak trees tower 
overhead, their branches forming a green canopy that filters the 
sunlight. The air is thick with the scent of earth and growing things.
Strange sounds echo from deeper within the woods."""
        room.sector_type = "forest"
        room.zone = zone
        room.exits = {
            'west': {'to_room': 3004},
            'east': {'to_room': 4002},
            'north': {'to_room': 4010}
        }
        room.mob_resets = [{'vnum': 4001, 'max': 2}]
        zone.rooms[4001] = room
        
        # Forest path
        room = Room(4002)
        room.name = "Deep in the Forest"
        room.description = """The forest grows denser here. Ancient trees press close, their
gnarled roots crossing the path. Mushrooms of unusual colors grow
in clusters at their bases. The sounds of civilization have faded,
replaced by bird calls and rustling leaves. Shadows move between
the trees - or is that just your imagination?"""
        room.sector_type = "forest"
        room.zone = zone
        room.exits = {
            'west': {'to_room': 4001},
            'east': {'to_room': 4003},
            'south': {'to_room': 4020}
        }
        room.mob_resets = [
            {'vnum': 4002, 'max': 2},
            {'vnum': 4003, 'max': 1}
        ]
        zone.rooms[4002] = room
        
        # Ancient Grove
        room = Room(4003)
        room.name = "The Ancient Grove"
        room.description = """You've stumbled upon a sacred grove deep within the forest. 
A massive oak, easily a thousand years old, dominates the clearing.
Strange runes are carved into its bark, and offerings of flowers
and berries are piled at its base. This place radiates ancient power."""
        room.sector_type = "forest"
        room.zone = zone
        room.exits = {
            'west': {'to_room': 4002},
        }
        room.mob_resets = [{'vnum': 4004, 'max': 1}]  # Druid
        room.obj_resets = [{'vnum': 40, 'max': 1}]   # Magical item
        zone.rooms[4003] = room
        
        # Northern path - to caves
        room = Room(4010)
        room.name = "Forest Trail North"
        room.description = """The path winds northward through increasingly rocky terrain.
The trees thin out here, and you can see the dark mouth of a cave
in the hillside ahead. Crude totems mark the path - you're entering
goblin territory."""
        room.sector_type = "forest"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 4001},
            'north': {'to_room': 6001}  # Goblin caves
        }
        room.mob_resets = [{'vnum': 4001, 'max': 1}]
        zone.rooms[4010] = room
        
        # Southern path - swamp
        room = Room(4020)
        room.name = "Edge of the Swamp"
        room.description = """The ground becomes soft and waterlogged. The trees here are
twisted and draped with hanging moss. The smell of decay is strong.
Murky water pools between the tree roots, and insects buzz 
annoyingly around your head. The swamp extends to the south."""
        room.sector_type = "swamp"
        room.zone = zone
        room.exits = {
            'north': {'to_room': 4002},
            'south': {'to_room': 4021}
        }
        room.mob_resets = [{'vnum': 4005, 'max': 2}]  # Swamp creatures
        zone.rooms[4020] = room
        
        room = Room(4021)
        room.name = "Deep Swamp"
        room.description = """Brackish water rises to your knees here. Rotting logs provide
the only solid footing. Something large moves beneath the murky
surface. Will-o'-wisps dance in the distance, trying to lure
travelers to their doom."""
        room.sector_type = "swamp"
        room.zone = zone
        room.exits = {
            'north': {'to_room': 4020},
        }
        room.mob_resets = [
            {'vnum': 4006, 'max': 1},  # Swamp troll
            {'vnum': 4005, 'max': 1}
        ]
        zone.rooms[4021] = room
        
        # Zone mobs
        zone.mobs = {
            4001: {
                'vnum': 4001,
                'name': 'a forest wolf',
                'short_desc': 'A grey forest wolf',
                'long_desc': 'A large grey wolf prowls through the undergrowth.',
                'level': 5,
                'hp_dice': '2d10+15',
                'damage_dice': '1d6+1',
                'gold': 0,
                'exp': 200,
                'alignment': 0,
                'flags': ['aggressive'],
                'special': None
            },
            4002: {
                'vnum': 4002,
                'name': 'a giant spider',
                'short_desc': 'A giant forest spider',
                'long_desc': 'A spider the size of a dog lurks in its web.',
                'level': 7,
                'hp_dice': '3d10+20',
                'damage_dice': '1d8+2',
                'gold': 0,
                'exp': 350,
                'alignment': 0,
                'flags': ['aggressive'],
                'special': 'poison'
            },
            4003: {
                'vnum': 4003,
                'name': 'a brown bear',
                'short_desc': 'A large brown bear',
                'long_desc': 'A massive brown bear forages among the trees.',
                'level': 12,
                'hp_dice': '6d10+50',
                'damage_dice': '2d6+4',
                'gold': 0,
                'exp': 800,
                'alignment': 0,
                'flags': [],
                'special': None
            },
            4004: {
                'vnum': 4004,
                'name': 'the Forest Druid',
                'short_desc': 'An ancient druid',
                'long_desc': 'A druid in green robes tends the sacred grove.',
                'level': 25,
                'hp_dice': '10d10+100',
                'damage_dice': '2d8+5',
                'gold': 100,
                'exp': 2000,
                'alignment': 1000,
                'faction': 'elves',
                'flags': ['sentinel'],
                'special': 'druid'
            },
            4005: {
                'vnum': 4005,
                'name': 'a giant frog',
                'short_desc': 'A bloated giant frog',
                'long_desc': 'A frog the size of a pony croaks menacingly.',
                'level': 6,
                'hp_dice': '3d10+15',
                'damage_dice': '1d6+2',
                'gold': 0,
                'exp': 250,
                'alignment': 0,
                'flags': ['aggressive'],
                'special': None
            },
            4006: {
                'vnum': 4006,
                'name': 'a swamp troll',
                'short_desc': 'A hideous swamp troll',
                'long_desc': 'A moss-covered troll rises from the muck, dripping slime.',
                'level': 18,
                'hp_dice': '8d10+80',
                'damage_dice': '2d8+6',
                'gold': 50,
                'exp': 1500,
                'alignment': -500,
                'flags': ['aggressive'],
                'special': 'regenerate'
            },
        }
        
        zone.objects = {
            40: {'vnum': 40, 'name': "the druid's staff", 'short_desc': "a gnarled wooden staff",
                 'room_desc': "A staff carved from ancient oak lies here.", 'type': 'weapon',
                 'weight': 4, 'cost': 500, 'damage_dice': '2d4', 'weapon_type': 'pound',
                 'affects': [{'type': 'mana', 'value': 20}]},
        }
        
        self.world.zones[40] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def create_castle_zone(self):
        """Create the Castle zone."""
        from world import Zone, Room
        
        zone = Zone(50)
        zone.name = "Greystone Castle"
        zone.builders = "Realmers"
        zone.top = 5099
        zone.lifespan = 2  # 30 min (2 ticks × 15 min)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Castle approach
        room = Room(5001)
        room.name = "The Road to Greystone"
        room.description = """A well-maintained road leads toward the imposing silhouette of
Greystone Castle. The fortress sits atop a hill, its grey stone
walls and towers dark against the sky. Pennants snap in the wind
from the battlements. The castle gates lie to the north."""
        room.sector_type = "field"
        room.zone = zone
        room.exits = {
            'east': {'to_room': 3006},
            'north': {'to_room': 5002}
        }
        zone.rooms[5001] = room
        
        # Castle gates
        room = Room(5002)
        room.name = "The Castle Gates"
        room.description = """Massive iron-bound gates stand before you, flanked by towers
bristling with arrow slits. Guards in royal livery challenge all
who approach. Beyond the gates, you can see the cobblestone 
courtyard of Greystone Castle."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 5001},
            'north': {'to_room': 5003}
        }
        room.mob_resets = [{'vnum': 5001, 'max': 2}]  # Castle guards
        zone.rooms[5002] = room
        
        # Courtyard
        room = Room(5003)
        room.name = "Castle Courtyard"
        room.description = """The courtyard of Greystone Castle bustles with activity. Servants
hurry about their duties, soldiers drill in formation, and nobles
converse in small groups. The main keep rises to the north, while
stables and workshops line the walls."""
        room.sector_type = "city"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 5002},
            'north': {'to_room': 5004},
            'east': {'to_room': 5010},
            'west': {'to_room': 5020}
        }
        room.mob_resets = [
            {'vnum': 5002, 'max': 2},  # Servants
            {'vnum': 5001, 'max': 1}
        ]
        zone.rooms[5003] = room
        
        # Great Hall
        room = Room(5004)
        room.name = "The Great Hall"
        room.description = """You stand in the magnificent Great Hall of Greystone Castle.
Tapestries depicting ancient battles hang from the walls. A long
table runs the length of the hall, and at the far end, on a raised
dais, sits the throne of the King. Suits of armor stand at attention."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 5003},
            'up': {'to_room': 5030}
        }
        room.mob_resets = [{'vnum': 5003, 'max': 1}]  # The King
        zone.rooms[5004] = room
        
        # Armory
        room = Room(5010)
        room.name = "The Castle Armory"
        room.description = """Racks of weapons and armor fill this room. Swords, spears, 
shields, and suits of plate mail are arranged in orderly rows.
The royal armorer works at a forge in the corner, maintaining
the kingdom's arsenal."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {'west': {'to_room': 5003}}
        room.mob_resets = [{'vnum': 5004, 'max': 1}]  # Armorer
        room.obj_resets = [
            {'vnum': 50, 'max': 1},  # Royal sword
            {'vnum': 51, 'max': 1}   # Shield
        ]
        zone.rooms[5010] = room
        
        # Stables
        room = Room(5020)
        room.name = "The Royal Stables"
        room.description = """The smell of hay and horses fills the air. Fine warhorses
stamp and snort in their stalls, tended by stable hands. The
royal carriages are housed here as well, gleaming with gilt."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {'east': {'to_room': 5003}}
        zone.rooms[5020] = room
        
        # Tower
        room = Room(5030)
        room.name = "The Tower Chamber"
        room.description = """A spiral staircase has brought you to a chamber high in the
castle tower. Windows provide a commanding view of the kingdom.
A massive iron chest sits against one wall, and ancient tomes
line the shelves. This is where the King keeps his treasures."""
        room.sector_type = "inside"
        room.zone = zone
        room.exits = {'down': {'to_room': 5004}}
        room.obj_resets = [{'vnum': 52, 'max': 1}]  # Treasure chest
        zone.rooms[5030] = room
        
        zone.mobs = {
            5001: {
                'vnum': 5001,
                'name': 'a castle guard',
                'short_desc': 'A royal castle guard',
                'long_desc': 'A guard in royal livery stands at attention.',
                'level': 20,
                'hp_dice': '8d10+80',
                'damage_dice': '2d8+4',
                'gold': 30,
                'exp': 1000,
                'alignment': 500,
                'flags': ['sentinel', 'helper'],
                'special': None
            },
            5002: {
                'vnum': 5002,
                'name': 'a castle servant',
                'short_desc': 'A busy servant',
                'long_desc': 'A servant hurries about their duties.',
                'level': 3,
                'hp_dice': '1d10+10',
                'damage_dice': '1d2',
                'gold': 5,
                'exp': 50,
                'alignment': 0,
                'flags': ['wimpy'],
                'special': None
            },
            5003: {
                'vnum': 5003,
                'name': 'King Valdric',
                'short_desc': 'King Valdric the Just',
                'long_desc': 'King Valdric sits upon his throne, crown gleaming.',
                'level': 50,
                'hp_dice': '30d10+300',
                'damage_dice': '4d8+10',
                'gold': 5000,
                'exp': 20000,
                'alignment': 1000,
                'flags': ['sentinel'],
                'special': None
            },
            5004: {
                'vnum': 5004,
                'name': 'the royal armorer',
                'short_desc': 'The royal armorer',
                'long_desc': 'A muscular smith works the forge, crafting fine weapons.',
                'level': 25,
                'hp_dice': '10d10+100',
                'damage_dice': '2d6+4',
                'gold': 200,
                'exp': 0,
                'alignment': 0,
                'flags': ['sentinel', 'shopkeeper'],
                'special': 'shopkeeper'
            },
        }
        
        zone.objects = {
            50: {'vnum': 50, 'name': 'a royal longsword', 'short_desc': 'a gleaming royal longsword',
                 'room_desc': 'A finely crafted longsword lies here.', 'type': 'weapon',
                 'weight': 6, 'cost': 500, 'damage_dice': '2d6', 'weapon_type': 'slash'},
            51: {'vnum': 51, 'name': 'a kite shield', 'short_desc': 'a sturdy kite shield',
                 'room_desc': 'A shield bearing the royal crest lies here.', 'type': 'armor',
                 'weight': 10, 'cost': 300, 'armor': 15, 'wear_slot': 'shield'},
            52: {'vnum': 52, 'name': 'a treasure chest', 'short_desc': 'an iron treasure chest',
                 'room_desc': 'A heavy iron chest sits here.', 'type': 'container',
                 'weight': 50, 'cost': 0, 'capacity': 100},
        }
        
        self.world.zones[50] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def create_goblin_caves_zone(self):
        """Create the Goblin Caves zone."""
        from world import Zone, Room
        
        zone = Zone(60)
        zone.name = "The Goblin Warrens"
        zone.builders = "Realmers"
        zone.top = 6099
        zone.lifespan = 1  # 15 min (1 tick)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Cave entrance
        room = Room(6001)
        room.name = "Cave Entrance"
        room.description = """The mouth of the cave yawns before you, a dark opening in the
rocky hillside. The stench of goblin is unmistakable - smoke, 
rotting meat, and unwashed bodies. Crude warnings in goblin
pictographs mark the entrance. Torchlight flickers from within."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 4010},
            'north': {'to_room': 6002}
        }
        room.mob_resets = [{'vnum': 6001, 'max': 2}]  # Goblin guards
        zone.rooms[6001] = room
        
        # Guard post
        room = Room(6002)
        room.name = "Goblin Guard Post"
        room.description = """A crude guard post has been established here. Broken furniture
and gnawed bones litter the floor. Tunnels branch off in multiple
directions, leading deeper into the goblin warrens."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 6001},
            'north': {'to_room': 6003},
            'east': {'to_room': 6010},
            'west': {'to_room': 6020}
        }
        room.mob_resets = [{'vnum': 6001, 'max': 3}]
        zone.rooms[6002] = room
        
        # Common area
        room = Room(6003)
        room.name = "Goblin Common Area"
        room.description = """This large cavern serves as the common area for the goblin tribe.
A fire pit smolders in the center, and rough pallets line the walls.
Goblins go about their business - eating, squabbling, and sharpening
weapons. The smell is overwhelming."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 6002},
            'north': {'to_room': 6004}
        }
        room.mob_resets = [
            {'vnum': 6002, 'max': 4},  # Common goblins
            {'vnum': 6003, 'max': 1}   # Goblin shaman
        ]
        zone.rooms[6003] = room
        
        # Chieftain's chamber
        room = Room(6004)
        room.name = "The Chieftain's Chamber"
        room.description = """The goblin chieftain's lair is surprisingly well-appointed by
goblin standards. A throne made of bones dominates one end, and
stolen treasures are piled about. Wolf pelts cover the floor.
The chieftain rules here with an iron fist."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {'south': {'to_room': 6003}}
        room.mob_resets = [
            {'vnum': 6004, 'max': 1},  # Chieftain
            {'vnum': 6005, 'max': 2}   # Bodyguards
        ]
        room.obj_resets = [
            {'vnum': 60, 'max': 1},  # Chieftain's axe
            {'vnum': 61, 'max': 1}   # Treasure pile
        ]
        zone.rooms[6004] = room
        
        # Slave pens
        room = Room(6010)
        room.name = "The Slave Pens"
        room.description = """Iron cages line this damp chamber, holding the goblins' prisoners.
The captives - humans, elves, and halflings - reach out desperately
through the bars. A goblin slaver cracks his whip to keep them quiet."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {'west': {'to_room': 6002}}
        room.mob_resets = [
            {'vnum': 6006, 'max': 1},  # Slaver
            {'vnum': 6007, 'max': 2}   # Prisoners (rescuable)
        ]
        zone.rooms[6010] = room
        
        # Treasure room
        room = Room(6020)
        room.name = "The Goblin Treasury"
        room.description = """The goblins have accumulated quite a hoard of stolen goods over
the years. Coins, gems, weapons, and armor are piled in heaps.
Most of it is junk, but some items of value glint in the torchlight."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {'east': {'to_room': 6002}}
        room.mob_resets = [{'vnum': 6001, 'max': 2}]
        room.obj_resets = [
            {'vnum': 62, 'max': 3},  # Gold piles
            {'vnum': 63, 'max': 1}   # Magic ring
        ]
        zone.rooms[6020] = room
        
        zone.mobs = {
            6001: {
                'vnum': 6001,
                'name': 'a goblin warrior',
                'short_desc': 'A snarling goblin warrior',
                'long_desc': 'A goblin in crude armor snarls at you, weapon ready.',
                'level': 8,
                'hp_dice': '3d10+25',
                'damage_dice': '1d6+2',
                'gold': 15,
                'exp': 350,
                'alignment': -500,
                'flags': ['aggressive'],
                'special': None
            },
            6002: {
                'vnum': 6002,
                'name': 'a goblin',
                'short_desc': 'A mangy goblin',
                'long_desc': 'A small, wretched goblin scurries about.',
                'level': 4,
                'hp_dice': '2d10+10',
                'damage_dice': '1d4+1',
                'gold': 5,
                'exp': 150,
                'alignment': -300,
                'flags': ['aggressive', 'wimpy'],
                'special': None
            },
            6003: {
                'vnum': 6003,
                'name': 'a goblin shaman',
                'short_desc': 'A goblin shaman',
                'long_desc': 'A goblin in feathers and bones chants dark magic.',
                'level': 12,
                'hp_dice': '4d10+40',
                'damage_dice': '1d8+3',
                'gold': 50,
                'exp': 700,
                'alignment': -600,
                'flags': ['caster'],
                'special': 'shaman'
            },
            6004: {
                'vnum': 6004,
                'name': 'the Goblin Chieftain',
                'short_desc': 'Grukthar the Goblin Chieftain',
                'long_desc': 'A massive goblin sits on a throne of bones, glaring at you.',
                'level': 20,
                'hp_dice': '10d10+100',
                'damage_dice': '2d8+5',
                'gold': 500,
                'exp': 2500,
                'alignment': -800,
                'flags': ['sentinel'],
                'special': None
            },
            6005: {
                'vnum': 6005,
                'name': 'a hobgoblin bodyguard',
                'short_desc': 'A hobgoblin bodyguard',
                'long_desc': 'A large hobgoblin stands ready to defend the chieftain.',
                'level': 15,
                'hp_dice': '6d10+60',
                'damage_dice': '2d6+4',
                'gold': 30,
                'exp': 1000,
                'alignment': -600,
                'flags': ['helper'],
                'special': None
            },
            6006: {
                'vnum': 6006,
                'name': 'a goblin slaver',
                'short_desc': 'A cruel goblin slaver',
                'long_desc': 'A goblin cracks a whip, tormenting the prisoners.',
                'level': 10,
                'hp_dice': '4d10+35',
                'damage_dice': '1d8+2',
                'gold': 25,
                'exp': 500,
                'alignment': -700,
                'flags': ['aggressive'],
                'special': None
            },
            6007: {
                'vnum': 6007,
                'name': 'a prisoner',
                'short_desc': 'A pitiful prisoner',
                'long_desc': 'A ragged prisoner cowers in a cage.',
                'level': 1,
                'hp_dice': '1d10+5',
                'damage_dice': '1d2',
                'gold': 0,
                'exp': 0,
                'alignment': 0,
                'flags': ['wimpy'],
                'special': None
            },
        }
        
        zone.objects = {
            60: {'vnum': 60, 'name': "the chieftain's battleaxe", 'short_desc': "a brutal battleaxe",
                 'room_desc': "A massive battleaxe lies here.", 'type': 'weapon',
                 'weight': 12, 'cost': 400, 'damage_dice': '2d8', 'weapon_type': 'cleave'},
            61: {'vnum': 61, 'name': 'a pile of coins', 'short_desc': 'a pile of gold coins',
                 'room_desc': 'A pile of stolen gold coins glitters here.', 'type': 'money',
                 'weight': 5, 'cost': 200},
            62: {'vnum': 62, 'name': 'gold coins', 'short_desc': 'some gold coins',
                 'room_desc': 'Some gold coins are scattered here.', 'type': 'money',
                 'weight': 1, 'cost': 50},
            63: {'vnum': 63, 'name': 'a ring of protection', 'short_desc': 'a silver ring',
                 'room_desc': 'A silver ring glints among the treasure.', 'type': 'armor',
                 'weight': 0, 'cost': 800, 'armor': 5, 'wear_slot': 'finger1',
                 'affects': [{'type': 'ac', 'value': -10}]},
        }
        
        self.world.zones[60] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def create_undead_crypt_zone(self):
        """Create the Undead Crypt zone."""
        from world import Zone, Room
        
        zone = Zone(70)
        zone.name = "The Forgotten Crypt"
        zone.builders = "Realmers"
        zone.top = 7099
        zone.lifespan = 2  # 30 min (2 ticks × 15 min)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Crypt entrance (accessible from city cemetery - we'll link this)
        room = Room(7001)
        room.name = "Crypt Entrance"
        room.description = """Stone steps descend into darkness. The air is cold and still,
carrying the musty scent of ancient death. Cobwebs hang thick
across the entrance, and strange symbols are carved into the 
archway. This is a place of the dead."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {'down': {'to_room': 7002}}
        zone.rooms[7001] = room
        
        # Antechamber
        room = Room(7002)
        room.name = "The Antechamber"
        room.description = """Dusty sarcophagi line the walls of this chamber. Most are sealed,
but a few lie broken open, their occupants long since risen. Faded
paintings on the walls depict a noble family. Corridors lead deeper
into the crypt."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {
            'up': {'to_room': 7001},
            'north': {'to_room': 7003},
            'east': {'to_room': 7010},
            'west': {'to_room': 7020}
        }
        room.mob_resets = [{'vnum': 7001, 'max': 3}]  # Skeletons
        zone.rooms[7002] = room
        
        # Hall of Bones
        room = Room(7003)
        room.name = "The Hall of Bones"
        room.description = """The walls of this corridor are composed entirely of human bones -
skulls, femurs, and ribs arranged in macabre patterns. The floor
crunches underfoot with ancient fragments. An unholy chill permeates
this place."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {
            'south': {'to_room': 7002},
            'north': {'to_room': 7004}
        }
        room.mob_resets = [
            {'vnum': 7002, 'max': 2},  # Zombies
            {'vnum': 7003, 'max': 1}   # Ghoul
        ]
        zone.rooms[7003] = room
        
        # Necromancer's sanctum
        room = Room(7004)
        room.name = "The Necromancer's Sanctum"
        room.description = """You have found the lair of the Necromancer who plagues this land.
Dark altars hold blasphemous offerings, and arcane circles are
etched into the floor. Candles of black wax burn with an eerie 
green flame. The Necromancer himself awaits..."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {'south': {'to_room': 7003}}
        room.mob_resets = [
            {'vnum': 7004, 'max': 1},  # Necromancer boss
            {'vnum': 7005, 'max': 2}   # Skeleton warriors
        ]
        room.obj_resets = [
            {'vnum': 70, 'max': 1},  # Staff of the Dead
            {'vnum': 71, 'max': 1}   # Necronomicon
        ]
        zone.rooms[7004] = room
        
        # Tomb east
        room = Room(7010)
        room.name = "The Noble's Tomb"
        room.description = """An ornate tomb dominates this chamber. Once the resting place
of a noble lord, it has been desecrated by the undead plague.
The ghost of the lord still lingers, trapped between worlds."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {'west': {'to_room': 7002}}
        room.mob_resets = [{'vnum': 7006, 'max': 1}]  # Ghost
        room.obj_resets = [{'vnum': 72, 'max': 1}]   # Noble's sword
        zone.rooms[7010] = room
        
        # Tomb west
        room = Room(7020)
        room.name = "The Mass Grave"
        room.description = """The floor of this chamber is uneven, covered with mounds of
earth beneath which countless bodies were interred during some
ancient plague. Now they rise again, clawing their way free."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.flags.add('dark')
        room.exits = {'east': {'to_room': 7002}}
        room.mob_resets = [
            {'vnum': 7002, 'max': 4},  # Zombies
            {'vnum': 7001, 'max': 2}   # Skeletons
        ]
        zone.rooms[7020] = room
        
        zone.mobs = {
            7001: {
                'vnum': 7001,
                'name': 'a skeleton warrior',
                'short_desc': 'A rattling skeleton',
                'long_desc': 'A skeleton in rusted armor stands guard.',
                'level': 10,
                'hp_dice': '4d10+30',
                'damage_dice': '1d8+2',
                'gold': 10,
                'exp': 400,
                'alignment': -800,
                'flags': ['aggressive', 'undead'],
                'special': None
            },
            7002: {
                'vnum': 7002,
                'name': 'a shambling zombie',
                'short_desc': 'A rotting zombie',
                'long_desc': 'A zombie lurches toward you, arms outstretched.',
                'level': 8,
                'hp_dice': '4d10+40',
                'damage_dice': '1d6+3',
                'gold': 0,
                'exp': 350,
                'alignment': -700,
                'flags': ['aggressive', 'undead'],
                'special': None
            },
            7003: {
                'vnum': 7003,
                'name': 'a ghoul',
                'short_desc': 'A ravenous ghoul',
                'long_desc': 'A ghoul crouches over a corpse, feeding.',
                'level': 14,
                'hp_dice': '5d10+50',
                'damage_dice': '2d4+4',
                'gold': 20,
                'exp': 800,
                'alignment': -900,
                'flags': ['aggressive', 'undead'],
                'special': 'paralyze'
            },
            7004: {
                'vnum': 7004,
                'name': 'Malachar the Necromancer',
                'short_desc': 'Malachar the Necromancer',
                'long_desc': 'A robed figure channels dark energy, eyes glowing with malice.',
                'level': 30,
                'hp_dice': '15d10+150',
                'damage_dice': '3d6+8',
                'gold': 1000,
                'exp': 5000,
                'alignment': -1000,
                'flags': ['sentinel', 'caster'],
                'special': 'necromancer'
            },
            7005: {
                'vnum': 7005,
                'name': 'an undead knight',
                'short_desc': 'An armored undead knight',
                'long_desc': 'A knight in black armor stands motionless, awaiting command.',
                'level': 18,
                'hp_dice': '8d10+80',
                'damage_dice': '2d8+5',
                'gold': 50,
                'exp': 1500,
                'alignment': -800,
                'flags': ['helper', 'undead'],
                'special': None
            },
            7006: {
                'vnum': 7006,
                'name': 'the ghost of Lord Aldric',
                'short_desc': 'The ghost of Lord Aldric',
                'long_desc': 'A spectral figure floats above its tomb, eyes filled with sorrow.',
                'level': 25,
                'hp_dice': '10d10+100',
                'damage_dice': '2d6+6',
                'gold': 0,
                'exp': 3000,
                'alignment': 0,
                'flags': ['sentinel', 'undead'],
                'special': 'ghost'
            },
        }
        
        zone.objects = {
            70: {'vnum': 70, 'name': 'the Staff of the Dead', 'short_desc': 'a bone staff crackling with energy',
                 'room_desc': 'A staff made of fused bones pulses with dark power.', 'type': 'weapon',
                 'weight': 4, 'cost': 2000, 'damage_dice': '2d6', 'weapon_type': 'blast',
                 'affects': [{'type': 'mana', 'value': 30}, {'type': 'int', 'value': 2}]},
            71: {'vnum': 71, 'name': 'the Necronomicon', 'short_desc': 'a book bound in human skin',
                 'room_desc': 'A dark tome lies open, pages covered in forbidden knowledge.', 
                 'type': 'other', 'weight': 3, 'cost': 5000},
            72: {'vnum': 72, 'name': "Lord Aldric's blade", 'short_desc': 'a ghostly longsword',
                 'room_desc': 'A spectral sword hovers in the air.', 'type': 'weapon',
                 'weight': 5, 'cost': 1500, 'damage_dice': '2d6', 'weapon_type': 'slash',
                 'affects': [{'type': 'hitroll', 'value': 3}]},
        }
        
        self.world.zones[70] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def create_dragon_lair_zone(self):
        """Create the Dragon's Lair zone - endgame content."""
        from world import Zone, Room
        
        zone = Zone(80)
        zone.name = "The Dragon's Domain"
        zone.builders = "Realmers"
        zone.top = 8099
        zone.lifespan = 4  # 60 min (4 ticks × 15 min)
        zone.reset_interval_seconds = zone.lifespan * 900
        
        # Mountain pass
        room = Room(8001)
        room.name = "The Mountain Pass"
        room.description = """The path winds ever upward through jagged peaks. The air grows
thin and cold. Far below, the world stretches out like a map.
Ahead, a cave mouth glows with inner fire - the lair of the 
legendary dragon Scorathax."""
        room.sector_type = "mountain"
        room.zone = zone
        room.exits = {'north': {'to_room': 8002}}
        room.mob_resets = [{'vnum': 8001, 'max': 2}]  # Dragon-kin
        zone.rooms[8001] = room
        
        # Dragon's entrance
        room = Room(8002)
        room.name = "The Dragon's Gate"
        room.description = """Massive stone pillars frame the entrance to the dragon's lair.
Ancient draconic runes warn all who approach. The ground is scorched
black, and the bones of previous challengers litter the area. Heat
emanates from within."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {
            'south': {'to_room': 8001},
            'north': {'to_room': 8003}
        }
        room.mob_resets = [{'vnum': 8002, 'max': 2}]  # Fire elementals
        zone.rooms[8002] = room
        
        # Treasure cavern
        room = Room(8003)
        room.name = "The Treasure Cavern"
        room.description = """Mountains of gold, jewels, and magical artifacts fill this vast
cavern - the accumulated hoard of centuries. The wealth here is
beyond imagination. And coiled atop it all, awaiting challengers..."""
        room.sector_type = "dungeon"
        room.zone = zone
        room.exits = {'south': {'to_room': 8002}}
        room.mob_resets = [{'vnum': 8003, 'max': 1}]  # THE DRAGON
        room.obj_resets = [
            {'vnum': 80, 'max': 1},  # Dragonslayer sword
            {'vnum': 81, 'max': 1},  # Dragon armor
            {'vnum': 82, 'max': 1}   # Massive gold pile
        ]
        zone.rooms[8003] = room
        
        zone.mobs = {
            8001: {
                'vnum': 8001,
                'name': 'a dragon-kin warrior',
                'short_desc': 'A scaled dragon-kin warrior',
                'long_desc': 'A humanoid with dragon features guards the path.',
                'level': 35,
                'hp_dice': '15d10+150',
                'damage_dice': '3d6+8',
                'gold': 100,
                'exp': 4000,
                'alignment': -500,
                'flags': ['aggressive'],
                'special': 'firebreath'
            },
            8002: {
                'vnum': 8002,
                'name': 'a fire elemental',
                'short_desc': 'A blazing fire elemental',
                'long_desc': 'A vaguely humanoid shape of living flame crackles here.',
                'level': 30,
                'hp_dice': '12d10+100',
                'damage_dice': '3d8+6',
                'gold': 0,
                'exp': 3000,
                'alignment': 0,
                'flags': ['aggressive'],
                'special': 'fireimmune'
            },
            8003: {
                'vnum': 8003,
                'name': 'Scorathax the Ancient',
                'short_desc': 'Scorathax the Ancient Red Dragon',
                'long_desc': '''A dragon of immense size and terrible majesty coils before you.
Scales like blood-red shields cover its massive form. Eyes like 
molten gold regard you with ancient cunning. Smoke curls from its
nostrils as it speaks in a voice like thunder: "You dare enter my 
domain, mortal? Then face the flames of eternity!"''',
                'level': 50,
                'hp_dice': '50d10+500',
                'damage_dice': '5d10+15',
                'gold': 10000,
                'exp': 50000,
                'alignment': -500,
                'flags': ['sentinel'],
                'special': 'dragon'
            },
        }
        
        zone.objects = {
            80: {'vnum': 80, 'name': 'Dragonsbane', 'short_desc': 'the legendary sword Dragonsbane',
                 'room_desc': 'A sword of legend gleams among the treasure.', 'type': 'weapon',
                 'weight': 8, 'cost': 50000, 'damage_dice': '4d6', 'weapon_type': 'slash',
                 'affects': [{'type': 'hitroll', 'value': 5}, {'type': 'damroll', 'value': 5},
                           {'type': 'str', 'value': 2}]},
            81: {'vnum': 81, 'name': 'dragonscale armor', 'short_desc': 'armor of red dragonscale',
                 'room_desc': 'Armor crafted from dragon scales lies here.', 'type': 'armor',
                 'weight': 30, 'cost': 40000, 'armor': 50, 'wear_slot': 'body',
                 'affects': [{'type': 'ac', 'value': -30}, {'type': 'con', 'value': 2}]},
            82: {'vnum': 82, 'name': "the dragon's hoard", 'short_desc': 'a mountain of gold',
                 'room_desc': 'An immense pile of gold and treasure dominates the cavern.',
                 'type': 'money', 'weight': 1000, 'cost': 100000},
        }
        
        self.world.zones[80] = zone
        for vnum, room in zone.rooms.items():
            self.world.rooms[vnum] = room
        self.world.mob_prototypes.update({int(k): v for k, v in zone.mobs.items()})
        self.world.obj_prototypes.update({int(k): v for k, v in zone.objects.items()})
        
    async def save_zones(self):
        """Save all zones to disk."""
        zones_dir = os.path.join(self.config.WORLD_DIR, 'zones')
        os.makedirs(zones_dir, exist_ok=True)
        
        for zone_num, zone in self.world.zones.items():
            filepath = os.path.join(zones_dir, f"zone_{zone_num:03d}.json")
            with open(filepath, 'w') as f:
                json.dump(zone.to_dict(), f, indent=2)
            logger.info(f"Saved zone {zone_num}: {zone.name}")
