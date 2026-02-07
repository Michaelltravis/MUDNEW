"""
Procedural Dungeons
===================
Replayable procedural dungeon generation and management.
"""

import random
import time
from datetime import date
from typing import Dict, List, Optional

from config import Config
from world import Zone, Room
from mobs import Mobile
from objects import Object, create_object, create_preset_object


DUNGEON_TYPES = {
    'cave': {
        'name': 'Cave System',
        'theme': 'cave',
        'sector': 'dungeon',
        'room_names': [
            'A Damp Cavern', 'A Narrow Tunnel', 'A Crystal Grotto', 'A Low Passage',
            'A Stalagmite Field', 'A Shimmering Cavern', 'A Dark Chasm', 'A Rocky Hollow'
        ],
        'room_descs': [
            'Water drips from jagged stone overhead, echoing through the cave.',
            'The air is cold and damp, and the tunnel narrows to a crawlspace.',
            'Crystals glitter faintly along the walls, casting ghostly light.',
            'The cave floor is uneven and slick with moss.',
            'Stalagmites rise like teeth from the cavern floor.',
            'A faint rumble of underground water reverberates nearby.',
            'Loose stones crunch underfoot as the tunnel curves onward.'
        ],
        'mobs': [
            {'name': 'a cave bat', 'short': 'a cave bat', 'desc': 'A bat flutters here, eyes gleaming.'},
            {'name': 'a cavern lizard', 'short': 'a cavern lizard', 'desc': 'A pale lizard skitters along the wall.'},
            {'name': 'a rock beetle', 'short': 'a rock beetle', 'desc': 'A beetle with a granite shell clacks its mandibles.'},
            {'name': 'a cave wolf', 'short': 'a cave wolf', 'desc': 'A lean wolf snarls from the shadows.'}
        ],
        'boss': {
            'name': 'the cave behemoth',
            'short': 'the cave behemoth',
            'desc': 'A hulking behemoth blocks the way, dripping with slime.'
        },
    },
    'ruins': {
        'name': 'Ancient Ruins',
        'theme': 'ruins',
        'sector': 'dungeon',
        'room_names': [
            'A Crumbling Hall', 'A Dusty Shrine', 'A Fallen Library', 'A Broken Gallery',
            'A Pillared Chamber', 'A Forgotten Vault', 'A Silent Corridor'
        ],
        'room_descs': [
            'Carved stone reliefs line the walls, worn by centuries.',
            'Ancient incense clings to the air, though no flame burns.',
            'Collapsed shelves litter the floor with shattered tablets.',
            'Mosaics of forgotten heroes crack beneath your boots.',
            'The ceiling arches overhead, pitted by time and decay.',
            'A faint chill creeps along the stones, as if watched.'
        ],
        'mobs': [
            {'name': 'a restless skeleton', 'short': 'a restless skeleton', 'desc': 'A skeleton rattles here, grasping at the air.'},
            {'name': 'a dusty wight', 'short': 'a dusty wight', 'desc': 'A wight drifts here, its eyes hollow.'},
            {'name': 'an ancient guardian', 'short': 'an ancient guardian', 'desc': 'A stone guardian stirs, cracks glowing with light.'}
        ],
        'boss': {
            'name': 'the tomb warden',
            'short': 'the tomb warden',
            'desc': 'The tomb warden rises, cloaked in necrotic power.'
        },
    },
    'bandit': {
        'name': 'Bandit Hideout',
        'theme': 'bandit',
        'sector': 'dungeon',
        'room_names': [
            'A Smoky Den', 'A Guard Post', 'A Loot Stash', 'A Hidden Bunkroom',
            'A Rough Tavern', 'A Training Pit'
        ],
        'room_descs': [
            'Smoke and sweat hang in the air, mixed with cheap ale.',
            'Crude barricades guard the passage, pocked with arrows.',
            'Scattered crates and sacks reek of stolen goods.',
            'Rough cots line the wall, blankets strewn across them.',
            'A card table sits abandoned, cups half full.'
        ],
        'mobs': [
            {'name': 'a bandit scout', 'short': 'a bandit scout', 'desc': 'A bandit scout watches you warily.'},
            {'name': 'a bandit bruiser', 'short': 'a bandit bruiser', 'desc': 'A burly bandit cracks his knuckles.'},
            {'name': 'a bandit archer', 'short': 'a bandit archer', 'desc': 'A bandit archer strings a bow.'}
        ],
        'boss': {
            'name': 'the bandit kingpin',
            'short': 'the bandit kingpin',
            'desc': 'The bandit kingpin stands over a pile of treasure.'
        },
    },
    'demon': {
        'name': 'Demon Rift',
        'theme': 'demon',
        'sector': 'dungeon',
        'room_names': [
            'A Fiery Rift', 'A Searing Corridor', 'A Lava Scar', 'A Charred Chamber',
            'A Rift Altar', 'A Smoldering Vault'
        ],
        'room_descs': [
            'Heat rolls from the walls, and flames lick the cracked stone.',
            'The air shimmers with heat haze and sulfur.',
            'Charred bones crunch beneath your steps.',
            'Burning runes glow along the floor, pulsing with power.',
            'A low chant echoes from unseen mouths.'
        ],
        'mobs': [
            {'name': 'an ember imp', 'short': 'an ember imp', 'desc': 'An imp crackles with flame.'},
            {'name': 'a rift demon', 'short': 'a rift demon', 'desc': 'A demon snarls, flames curling from its claws.'},
            {'name': 'a flame thrall', 'short': 'a flame thrall', 'desc': 'A thrall lurches, its skin blistered by fire.'}
        ],
        'boss': {
            'name': 'the rift overlord',
            'short': 'the rift overlord',
            'desc': 'The rift overlord towers here, wreathed in fire.'
        },
    },
}

LOOT_TIERS = {
    'basic': [1, 2, 3, 4, 10, 11, 12, 13],
    'intermediate': [14, 30, 35, 37, 39],
    'advanced': [41, 44, 48, 49, 80, 83, 81],
    'elite': [84, 85, 87, 88, 89, 90, 91],
}


class ProceduralDungeonManager:
    """Manage procedural dungeons and their state."""

    def __init__(self):
        self.config = Config()
        self.active_dungeons: Dict[str, dict] = {}
        self.leaderboards: Dict[str, List[dict]] = {}
        self._counter = 1
        self._daily_date: Optional[date] = None
        self._daily_type: Optional[str] = None
        self.daily_completions: Dict[str, date] = {}

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    def get_daily_type(self) -> str:
        today = date.today()
        if self._daily_date != today or not self._daily_type:
            self._daily_date = today
            self._daily_type = random.choice(list(DUNGEON_TYPES.keys()))
        return self._daily_type

    def list_dungeons(self) -> List[dict]:
        daily_type = self.get_daily_type()
        result = []
        for key, data in DUNGEON_TYPES.items():
            entry = {
                'key': key,
                'name': data['name'],
                'theme': data['theme'],
                'daily': key == daily_type,
            }
            result.append(entry)
        return result

    def _difficulty_to_level(self, player_level: int, difficulty: Optional[int]) -> int:
        if difficulty is None:
            return max(1, player_level)
        return max(1, difficulty)

    def _level_tier(self, level: int) -> str:
        if level <= 10:
            return 'basic'
        if level <= 20:
            return 'intermediate'
        if level <= 30:
            return 'advanced'
        return 'elite'

    def _create_room(self, zone: Zone, vnum: int, name: str, desc: str, sector: str) -> Room:
        room = Room(vnum)
        room.zone = zone
        room.name = name
        room.description = desc
        room.sector_type = sector
        return room

    def _build_layout(self, zone: Zone, start_vnum: int, dungeon_type: dict, level: int) -> dict:
        room_count = max(6, 6 + random.randint(0, 4) + level // 8)
        positions = {(0, 0): 0}
        coords = [(0, 0)]
        for _ in range(1, room_count):
            placed = False
            attempts = 0
            while not placed and attempts < 30:
                attempts += 1
                base = random.choice(coords)
                dx, dy = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
                new_pos = (base[0] + dx, base[1] + dy)
                if new_pos not in positions:
                    positions[new_pos] = len(coords)
                    coords.append(new_pos)
                    placed = True
            if not placed:
                # Fallback: add in a line
                new_pos = (coords[-1][0] + 1, coords[-1][1])
                positions[new_pos] = len(coords)
                coords.append(new_pos)

        rooms: List[Room] = []
        for idx in range(room_count):
            name = random.choice(dungeon_type['room_names'])
            desc = random.choice(dungeon_type['room_descs'])
            room = self._create_room(zone, start_vnum + idx, name, desc, dungeon_type['sector'])
            rooms.append(room)
            zone.rooms[room.vnum] = room

        # Create entrance and boss rooms
        entrance = rooms[0]
        entrance.name = f"Entrance to the {dungeon_type['name']}"
        entrance.description = f"A rough archway opens into the {dungeon_type['name'].lower()}. Torches flicker along the walls."
        boss_room = rooms[-1]
        boss_room.name = f"Lair of {dungeon_type['boss']['name']}"
        boss_room.description = f"The air grows heavy as you enter. {dungeon_type['boss']['desc']}"

        # Link rooms based on coordinates
        coord_to_room = {coords[i]: rooms[i] for i in range(room_count)}
        for pos, room in coord_to_room.items():
            x, y = pos
            for (dx, dy, direction, opposite) in [
                (0, 1, 'north', 'south'),
                (1, 0, 'east', 'west'),
                (0, -1, 'south', 'north'),
                (-1, 0, 'west', 'east'),
            ]:
                neighbor = (x + dx, y + dy)
                if neighbor in coord_to_room:
                    target = coord_to_room[neighbor]
                    room.exits[direction] = {'to_room': target.vnum, 'room': target}
                    if opposite not in target.exits:
                        target.exits[opposite] = {'to_room': room.vnum, 'room': room}

        return {'rooms': rooms, 'entrance': entrance, 'boss_room': boss_room}

    def _create_mob(self, world, dungeon_type: dict, level: int, is_boss: bool, dungeon_id: int) -> Mobile:
        if is_boss:
            mob_data = dungeon_type['boss']
            mob_level = level + 3
        else:
            mob_data = random.choice(dungeon_type['mobs'])
            mob_level = max(1, level + random.randint(-1, 2))

        proto = {
            'vnum': 800000 + random.randint(1, 9999),
            'name': mob_data['name'],
            'short_desc': mob_data['short'],
            'long_desc': mob_data['desc'],
            'level': mob_level,
            'alignment': -100 if dungeon_type['theme'] in {'demon', 'ruins'} else 0,
            'hp_dice': f"{mob_level}d10+{mob_level * 6}",
            'damage_dice': f"{max(1, mob_level // 2)}d6+{mob_level // 3}",
            'gold': mob_level * 10,
            'exp': mob_level * 150,
            'auto_equip': False,
        }
        mob = Mobile.from_prototype(proto, world)
        tier = self._level_tier(mob_level)
        mob.loot_table = LOOT_TIERS.get(tier, LOOT_TIERS['basic'])
        mob.loot_chance = 30 if is_boss else 15
        mob.is_dungeon_boss = is_boss
        mob.dungeon_id = dungeon_id
        return mob

    def _place_loot(self, world, room: Room, level: int, rare: bool = False):
        tier = self._level_tier(level + (5 if rare else 0))
        loot_choices = LOOT_TIERS.get(tier, LOOT_TIERS['basic'])
        loot_vnum = random.choice(loot_choices)
        loot_obj = create_object(loot_vnum, world) or create_preset_object(loot_vnum)
        if not loot_obj:
            loot_obj = Object(900000 + random.randint(1, 9999), world)
            loot_obj.name = 'a mysterious relic'
            loot_obj.short_desc = 'a mysterious relic'
            loot_obj.room_desc = 'A mysterious relic glows faintly here.'
            loot_obj.description = 'A relic of unknown origin. It hums with dormant power.'
            loot_obj.cost = 50 + level * 5
        room.items.append(loot_obj)

    def _create_token(self, world) -> Object:
        token = Object(950000 + random.randint(1, 9999), world)
        token.name = 'a dungeon token'
        token.short_desc = 'a dungeon token'
        token.room_desc = 'A dungeon token glints here.'
        token.description = 'A token stamped with the seal of the Adventurer\'s Guild.'
        token.cost = 0
        return token

    async def enter_dungeon(self, player, dungeon_key: str, difficulty: Optional[int] = None,
                            permadeath: bool = False, daily: bool = False):
        if player.name in self.active_dungeons:
            await player.send("You are already in a dungeon. Use 'dungeon leave' to abandon it.")
            return

        dungeon_data = DUNGEON_TYPES.get(dungeon_key)
        if not dungeon_data:
            await player.send("Unknown dungeon type. Use 'dungeon list' to see options.")
            return

        level = self._difficulty_to_level(player.level, difficulty)

        zone_number = 900 + self._next_id()
        zone = Zone(zone_number)
        zone.name = f"Procedural: {dungeon_data['name']}"
        zone.builders = 'Procedural'
        zone.lifespan = 999
        zone.reset_mode = 0
        zone.top = zone_number * 1000 + 999

        start_vnum = zone_number * 1000
        layout = self._build_layout(zone, start_vnum, dungeon_data, level)

        # Attach zone/rooms to world
        world = player.world
        world.zones[zone.number] = zone
        for vnum, room in zone.rooms.items():
            world.rooms[vnum] = room

        dungeon_id = self._next_id()
        # Spawn mobs
        mobs = []
        for room in layout['rooms']:
            if room == layout['entrance']:
                continue
            if room == layout['boss_room']:
                boss = self._create_mob(world, dungeon_data, level + 2, True, dungeon_id)
                boss.room = room
                room.characters.append(boss)
                world.npcs.append(boss)
                mobs.append(boss)
                continue
            mob_count = random.randint(0, 2)
            for _ in range(mob_count):
                mob = self._create_mob(world, dungeon_data, level, False, dungeon_id)
                mob.room = room
                room.characters.append(mob)
                world.npcs.append(mob)
                mobs.append(mob)

        # Place loot
        for room in layout['rooms']:
            if room == layout['entrance']:
                continue
            if random.randint(1, 100) <= 35:
                self._place_loot(world, room, level)
        self._place_loot(world, layout['boss_room'], level, rare=True)

        dungeon = {
            'id': dungeon_id,
            'key': dungeon_key,
            'name': dungeon_data['name'],
            'level': level,
            'difficulty': difficulty or level,
            'zone': zone,
            'rooms': layout['rooms'],
            'entrance': layout['entrance'],
            'boss_room': layout['boss_room'],
            'mobs': mobs,
            'return_vnum': player.room.vnum if player.room else 3001,
            'start_time': time.time(),
            'permadeath': permadeath,
            'daily': daily,
        }
        self.active_dungeons[player.name] = dungeon
        player.active_dungeon = dungeon

        # Move player into dungeon entrance
        await self._move_player(player, layout['entrance'])

        c = player.config.COLORS
        await player.send(f"{c['bright_cyan']}You enter the {dungeon_data['name']} (Level {level}).{c['reset']}")
        if permadeath:
            await player.send(f"{c['red']}Permadeath is enabled for this run!{c['reset']}")
        if daily:
            await player.send(f"{c['bright_yellow']}Daily dungeon bonus active!{c['reset']}")

        await layout['entrance'].show_to(player)

    async def leave_dungeon(self, player, reason: str = 'abandon'):
        dungeon = self.active_dungeons.get(player.name)
        if not dungeon:
            await player.send("You are not in a dungeon.")
            return

        c = player.config.COLORS
        await player.send(f"{c['yellow']}You leave the dungeon.{c['reset']}")
        await self._return_player(player, dungeon)
        await self._cleanup_dungeon(player, dungeon, reason)

    async def complete_dungeon(self, player, dungeon: dict):
        c = player.config.COLORS
        duration = max(1, int(time.time() - dungeon['start_time']))

        xp_bonus = dungeon['level'] * 200
        token_count = 1 + dungeon['level'] // 10
        if dungeon['permadeath']:
            xp_bonus = int(xp_bonus * 1.4)
            token_count += 1
        if dungeon['daily'] and self.daily_completions.get(player.name) != date.today():
            xp_bonus = int(xp_bonus * 1.5)
            token_count += 2
            self.daily_completions[player.name] = date.today()

        await player.gain_exp(xp_bonus)
        await player.send(f"{c['bright_yellow']}Dungeon complete! Bonus XP: {xp_bonus}.{c['reset']}")

        for _ in range(token_count):
            player.inventory.append(self._create_token(player.world))
        await player.send(f"{c['bright_cyan']}You receive {token_count} dungeon tokens.{c['reset']}")

        # Rare loot drop
        if random.randint(1, 100) <= 30:
            rare_obj = Object(960000 + random.randint(1, 9999), player.world)
            rare_obj.name = 'a relic of conquest'
            rare_obj.short_desc = 'a relic of conquest'
            rare_obj.room_desc = 'A relic of conquest gleams here.'
            rare_obj.description = 'A rare relic awarded for dungeon mastery.'
            rare_obj.cost = 250 + dungeon['level'] * 10
            player.inventory.append(rare_obj)
            await player.send(f"{c['bright_magenta']}You receive a rare relic!{c['reset']}")

        # Leaderboard tracking
        board_key = f"{dungeon['key']}:{dungeon['level']}"
        entry = {
            'player': player.name,
            'duration': duration,
            'timestamp': time.time(),
        }
        board = self.leaderboards.setdefault(board_key, [])
        board.append(entry)
        board.sort(key=lambda e: e['duration'])
        self.leaderboards[board_key] = board[:5]

        await player.send(f"{c['green']}Clear time: {duration} seconds.{c['reset']}")

        await self._return_player(player, dungeon)
        await self._cleanup_dungeon(player, dungeon, reason='complete')

    async def on_player_death(self, player):
        dungeon = self.active_dungeons.get(player.name)
        if not dungeon:
            return
        if dungeon.get('permadeath'):
            await player.send("Your permadeath run has failed. The dungeon collapses behind you.")
            await self._cleanup_dungeon(player, dungeon, reason='death')
        else:
            await self._cleanup_dungeon(player, dungeon, reason='death')

    async def _return_player(self, player, dungeon: dict):
        target_room = player.world.get_room(dungeon['return_vnum'])
        if not target_room:
            target_room = player.world.get_room(self.config.STARTING_ROOM)
        if target_room:
            await self._move_player(player, target_room)
            await target_room.show_to(player)

    async def _move_player(self, player, target_room: Room):
        if player.room and player in player.room.characters:
            player.room.characters.remove(player)
        player.room = target_room
        target_room.characters.append(player)

    async def _cleanup_dungeon(self, player, dungeon: dict, reason: str):
        # Remove mobs
        world = player.world
        for mob in list(dungeon.get('mobs', [])):
            if mob in world.npcs:
                world.npcs.remove(mob)
            if mob.room and mob in mob.room.characters:
                mob.room.characters.remove(mob)

        # Remove rooms from world
        for room in dungeon.get('rooms', []):
            if room.vnum in world.rooms:
                del world.rooms[room.vnum]

        zone = dungeon.get('zone')
        if zone and zone.number in world.zones:
            del world.zones[zone.number]

        if player.name in self.active_dungeons:
            del self.active_dungeons[player.name]
        player.active_dungeon = None

    def is_boss_kill(self, victim) -> bool:
        return getattr(victim, 'is_dungeon_boss', False)

    def get_leaderboards(self) -> Dict[str, List[dict]]:
        return self.leaderboards


DUNGEON_MANAGER = ProceduralDungeonManager()


def get_dungeon_manager() -> ProceduralDungeonManager:
    return DUNGEON_MANAGER
