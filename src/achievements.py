"""
Achievement System for RealmsMUD

Tracks player accomplishments and awards titles/bonuses.
Achievements are checked on relevant events (kills, levels, exploration, etc.)
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger(__name__)


@dataclass
class Achievement:
    """Definition of an achievement."""
    id: str
    name: str
    description: str
    category: str  # combat, exploration, social, progression, collection
    icon: str  # emoji
    points: int  # achievement points
    reward_title: Optional[str] = None  # title player can display
    reward_gold: int = 0
    reward_xp: int = 0
    hidden: bool = False  # hidden until unlocked


# Achievement definitions
ACHIEVEMENTS: Dict[str, Achievement] = {
    # === PROGRESSION ===
    'first_blood': Achievement(
        id='first_blood',
        name='First Blood',
        description='Defeat your first enemy',
        category='combat',
        icon='⚔️',
        points=5,
        reward_xp=50,
    ),
    'level_5': Achievement(
        id='level_5',
        name='Apprentice Adventurer',
        description='Reach level 5',
        category='progression',
        icon='📈',
        points=10,
        reward_gold=100,
    ),
    'level_10': Achievement(
        id='level_10',
        name='Journeyman',
        description='Reach level 10',
        category='progression',
        icon='📈',
        points=20,
        reward_gold=250,
        reward_title='the Journeyman',
    ),
    'level_20': Achievement(
        id='level_20',
        name='Veteran',
        description='Reach level 20',
        category='progression',
        icon='📈',
        points=30,
        reward_gold=500,
        reward_title='the Veteran',
    ),
    'level_30': Achievement(
        id='level_30',
        name='Elite',
        description='Reach level 30',
        category='progression',
        icon='📈',
        points=50,
        reward_gold=1000,
        reward_title='the Elite',
    ),
    'level_40': Achievement(
        id='level_40',
        name='Champion',
        description='Reach level 40',
        category='progression',
        icon='🏆',
        points=75,
        reward_gold=2000,
        reward_title='the Champion',
    ),
    'level_50': Achievement(
        id='level_50',
        name='Hero of the Realm',
        description='Reach level 50',
        category='progression',
        icon='👑',
        points=100,
        reward_gold=5000,
        reward_title='Hero of the Realm',
    ),
    
    # === COMBAT ===
    'slayer_10': Achievement(
        id='slayer_10',
        name='Monster Slayer',
        description='Defeat 10 enemies',
        category='combat',
        icon='💀',
        points=10,
    ),
    'slayer_100': Achievement(
        id='slayer_100',
        name='Veteran Slayer',
        description='Defeat 100 enemies',
        category='combat',
        icon='💀',
        points=25,
        reward_title='the Slayer',
    ),
    'slayer_1000': Achievement(
        id='slayer_1000',
        name='Death Incarnate',
        description='Defeat 1000 enemies',
        category='combat',
        icon='☠️',
        points=50,
        reward_title='Death Incarnate',
    ),
    'boss_slayer': Achievement(
        id='boss_slayer',
        name='Boss Slayer',
        description='Defeat your first boss',
        category='combat',
        icon='🐉',
        points=25,
        reward_xp=500,
    ),
    'dragon_slayer': Achievement(
        id='dragon_slayer',
        name='Dragon Slayer',
        description='Defeat a dragon',
        category='combat',
        icon='🐲',
        points=50,
        reward_title='the Dragon Slayer',
    ),
    'horseman_slayer': Achievement(
        id='horseman_slayer',
        name='Apocalypse Averted',
        description='Defeat all Four Horsemen',
        category='combat',
        icon='🏇',
        points=100,
        reward_title='Apocalypse Survivor',
        hidden=True,
    ),
    'survivor': Achievement(
        id='survivor',
        name='Survivor',
        description='Die and return from the dead',
        category='combat',
        icon='💫',
        points=5,
    ),
    'death_10': Achievement(
        id='death_10',
        name='Familiar with Death',
        description='Die 10 times',
        category='combat',
        icon='👻',
        points=10,
        hidden=True,
    ),
    
    # === EXPLORATION ===
    'explorer_10': Achievement(
        id='explorer_10',
        name='Explorer',
        description='Visit 10 different rooms',
        category='exploration',
        icon='🗺️',
        points=5,
    ),
    'explorer_100': Achievement(
        id='explorer_100',
        name='Wanderer',
        description='Visit 100 different rooms',
        category='exploration',
        icon='🗺️',
        points=15,
        reward_title='the Wanderer',
    ),
    'explorer_500': Achievement(
        id='explorer_500',
        name='Cartographer',
        description='Visit 500 different rooms',
        category='exploration',
        icon='🗺️',
        points=30,
        reward_title='the Cartographer',
    ),
    'zone_complete': Achievement(
        id='zone_complete',
        name='Zone Master',
        description='Visit every room in a zone',
        category='exploration',
        icon='✅',
        points=20,
    ),
    'midgaard_native': Achievement(
        id='midgaard_native',
        name='Midgaard Native',
        description='Visit every room in Midgaard',
        category='exploration',
        icon='🏰',
        points=25,
        reward_title='of Midgaard',
    ),
    
    # === COLLECTION ===
    'first_gold': Achievement(
        id='first_gold',
        name='First Fortune',
        description='Earn your first 100 gold',
        category='collection',
        icon='💰',
        points=5,
    ),
    'wealthy': Achievement(
        id='wealthy',
        name='Wealthy',
        description='Have 10,000 gold at once',
        category='collection',
        icon='💎',
        points=25,
        reward_title='the Wealthy',
    ),
    'rich': Achievement(
        id='rich',
        name='Filthy Rich',
        description='Have 100,000 gold at once',
        category='collection',
        icon='👑',
        points=50,
        reward_title='the Rich',
        hidden=True,
    ),
    'hoarder': Achievement(
        id='hoarder',
        name='Hoarder',
        description='Have 50 items in your inventory',
        category='collection',
        icon='🎒',
        points=10,
        hidden=True,
    ),
    'fully_equipped': Achievement(
        id='fully_equipped',
        name='Fully Equipped',
        description='Have equipment in every slot',
        category='collection',
        icon='🛡️',
        points=15,
    ),
    'set_collector': Achievement(
        id='set_collector',
        name='Set Collector',
        description='Complete an equipment set',
        category='collection',
        icon='👔',
        points=30,
        reward_title='the Collector',
    ),
    'bookworm': Achievement(
        id='bookworm',
        name='Bookworm',
        description='Read your first lore item',
        category='collection',
        icon='📖',
        points=5,
    ),
    'scholar': Achievement(
        id='scholar',
        name='Scholar',
        description='Read 10 different lore items',
        category='collection',
        icon='📚',
        points=20,
        reward_title='the Scholar',
    ),
    'loremaster': Achievement(
        id='loremaster',
        name='Loremaster',
        description='Read 50 different lore items',
        category='collection',
        icon='🏛️',
        points=50,
        reward_title='Loremaster',
    ),
    
    # === SOCIAL ===
    'tutorial_complete': Achievement(
        id='tutorial_complete',
        name='Graduate',
        description='Complete the tutorial',
        category='social',
        icon='🎓',
        points=10,
        reward_xp=100,
    ),
    'quest_5': Achievement(
        id='quest_5',
        name='Helpful Citizen',
        description='Complete 5 quests',
        category='social',
        icon='📜',
        points=15,
    ),
    'quest_25': Achievement(
        id='quest_25',
        name='Quest Master',
        description='Complete 25 quests',
        category='social',
        icon='📜',
        points=35,
        reward_title='the Quest Master',
    ),
    'group_victory': Achievement(
        id='group_victory',
        name='Team Player',
        description='Defeat an enemy while in a group',
        category='social',
        icon='👥',
        points=10,
    ),
    
    # === SECRET ===
    'secret_room': Achievement(
        id='secret_room',
        name='Secret Seeker',
        description='Discover a hidden room',
        category='exploration',
        icon='🔍',
        points=15,
        hidden=True,
    ),
    'deathtrap_survivor': Achievement(
        id='deathtrap_survivor',
        name='Cheating Death',
        description='Enter a deathtrap and... well, die',
        category='exploration',
        icon='💀',
        points=5,
        hidden=True,
    ),
}


class AchievementManager:
    """Manages achievement tracking and unlocking."""
    
    @classmethod
    async def check_kill(cls, player: 'Player', victim) -> None:
        """Check kill-related achievements."""
        # Track kill count
        if not hasattr(player, 'stats'):
            player.stats = {}
        player.stats['kills'] = player.stats.get('kills', 0) + 1
        kills = player.stats['kills']
        
        # First kill
        if kills == 1:
            await cls.unlock(player, 'first_blood')
        
        # Kill milestones
        if kills >= 10:
            await cls.unlock(player, 'slayer_10')
        if kills >= 100:
            await cls.unlock(player, 'slayer_100')
        if kills >= 1000:
            await cls.unlock(player, 'slayer_1000')
        
        # Boss kill
        if hasattr(victim, 'flags') and 'boss' in victim.flags:
            await cls.unlock(player, 'boss_slayer')
            
            # Dragon check
            victim_name = getattr(victim, 'name', '').lower()
            if 'dragon' in victim_name:
                await cls.unlock(player, 'dragon_slayer')
            
            # Track horsemen kills
            horsemen = ['pestilence', 'war', 'famine', 'death']
            for horseman in horsemen:
                if horseman in victim_name:
                    if not hasattr(player, 'horsemen_killed'):
                        player.horsemen_killed = set()
                    player.horsemen_killed.add(horseman)
                    if len(player.horsemen_killed) >= 4:
                        await cls.unlock(player, 'horseman_slayer')
                    break
        
        # Group kill
        if player.group_leader or player.group_members:
            await cls.unlock(player, 'group_victory')
    
    @classmethod
    async def check_level(cls, player: 'Player') -> None:
        """Check level-related achievements."""
        level = player.level
        
        if level >= 5:
            await cls.unlock(player, 'level_5')
        if level >= 10:
            await cls.unlock(player, 'level_10')
        if level >= 20:
            await cls.unlock(player, 'level_20')
        if level >= 30:
            await cls.unlock(player, 'level_30')
        if level >= 40:
            await cls.unlock(player, 'level_40')
        if level >= 50:
            await cls.unlock(player, 'level_50')
    
    @classmethod
    async def check_death(cls, player: 'Player') -> None:
        """Check death-related achievements."""
        if not hasattr(player, 'stats'):
            player.stats = {}
        player.stats['deaths'] = player.stats.get('deaths', 0) + 1
        deaths = player.stats['deaths']
        
        if deaths >= 1:
            await cls.unlock(player, 'survivor')
        if deaths >= 10:
            await cls.unlock(player, 'death_10')
    
    @classmethod
    async def check_exploration(cls, player: 'Player', room_vnum: int) -> None:
        """Check exploration-related achievements."""
        if not hasattr(player, 'visited_rooms'):
            player.visited_rooms = set()
        
        player.visited_rooms.add(room_vnum)
        visited = len(player.visited_rooms)
        
        if visited >= 10:
            await cls.unlock(player, 'explorer_10')
        if visited >= 100:
            await cls.unlock(player, 'explorer_100')
        if visited >= 500:
            await cls.unlock(player, 'explorer_500')
    
    @classmethod
    async def check_gold(cls, player: 'Player') -> None:
        """Check gold-related achievements."""
        gold = player.gold
        
        if gold >= 100:
            await cls.unlock(player, 'first_gold')
        if gold >= 10000:
            await cls.unlock(player, 'wealthy')
        if gold >= 100000:
            await cls.unlock(player, 'rich')
    
    @classmethod
    async def check_quest_complete(cls, player: 'Player', quest_id: str) -> None:
        """Check quest-related achievements."""
        if not hasattr(player, 'stats'):
            player.stats = {}
        player.stats['quests_completed'] = player.stats.get('quests_completed', 0) + 1
        quests = player.stats['quests_completed']
        
        # Tutorial completion
        if quest_id.startswith('tutorial_9'):
            await cls.unlock(player, 'tutorial_complete')
        
        if quests >= 5:
            await cls.unlock(player, 'quest_5')
        if quests >= 25:
            await cls.unlock(player, 'quest_25')
    
    @classmethod
    async def check_equipment(cls, player: 'Player') -> None:
        """Check equipment-related achievements."""
        # Check if all slots filled
        slots = ['head', 'neck', 'body', 'arms', 'hands', 'waist', 'legs', 
                 'feet', 'wield', 'shield', 'held', 'about', 'wrist', 'finger']
        
        filled = sum(1 for slot in slots if player.equipment.get(slot))
        if filled >= 10:  # Most slots filled
            await cls.unlock(player, 'fully_equipped')
        
        # Check inventory size
        if len(player.inventory) >= 50:
            await cls.unlock(player, 'hoarder')
    
    @classmethod
    async def check_secret_room(cls, player: 'Player') -> None:
        """Called when player finds a secret room."""
        await cls.unlock(player, 'secret_room')
    
    @classmethod
    async def check_deathtrap(cls, player: 'Player') -> None:
        """Called when player enters a deathtrap."""
        await cls.unlock(player, 'deathtrap_survivor')
    
    @classmethod
    async def record_lore_found(cls, player: 'Player', item) -> None:
        """Called when player reads a lore item (book, scroll, etc.)."""
        # Track lore items read for potential achievement
        if not hasattr(player, 'lore_read'):
            player.lore_read = set()
        
        item_vnum = getattr(item, 'vnum', None)
        if item_vnum and item_vnum not in player.lore_read:
            player.lore_read.add(item_vnum)
            
            # Check milestones
            count = len(player.lore_read)
            if count >= 1:
                await cls.unlock(player, 'bookworm')  # First lore read
            if count >= 10:
                await cls.unlock(player, 'scholar')   # 10 lore items
            if count >= 50:
                await cls.unlock(player, 'loremaster') # 50 lore items
    
    @classmethod
    async def unlock(cls, player: 'Player', achievement_id: str) -> bool:
        """Unlock an achievement for a player."""
        if achievement_id not in ACHIEVEMENTS:
            return False
        
        # Initialize achievements dict if needed
        if not hasattr(player, 'achievements'):
            player.achievements = {}
        
        # Already unlocked?
        if achievement_id in player.achievements:
            return False
        
        achievement = ACHIEVEMENTS[achievement_id]
        
        # Unlock it
        player.achievements[achievement_id] = {
            'unlocked_at': datetime.now().isoformat(),
            'points': achievement.points,
        }
        
        # Get colors
        c = player.config.COLORS
        
        # Announcement
        await player.send(f"\n{c['bright_yellow']}★ ACHIEVEMENT UNLOCKED ★{c['reset']}")
        await player.send(f"{c['bright_cyan']}{achievement.icon} {achievement.name}{c['reset']}")
        await player.send(f"{c['white']}{achievement.description}{c['reset']}")
        await player.send(f"{c['yellow']}+{achievement.points} achievement points{c['reset']}")
        
        # Grant rewards
        if achievement.reward_xp > 0:
            player.experience += achievement.reward_xp
            await player.send(f"{c['bright_green']}+{achievement.reward_xp} XP{c['reset']}")
        
        if achievement.reward_gold > 0:
            player.gold += achievement.reward_gold
            await player.send(f"{c['bright_yellow']}+{achievement.reward_gold} gold{c['reset']}")
        
        if achievement.reward_title:
            if not hasattr(player, 'available_titles'):
                player.available_titles = []
            if achievement.reward_title not in player.available_titles:
                player.available_titles.append(achievement.reward_title)
                await player.send(f"{c['bright_magenta']}New title unlocked: '{achievement.reward_title}'{c['reset']}")
        
        await player.send("")  # Blank line
        
        # Save player
        player.save()
        
        logger.info(f"Player {player.name} unlocked achievement: {achievement.name}")
        return True
    
    @classmethod
    def get_player_points(cls, player: 'Player') -> int:
        """Get total achievement points for a player."""
        if not hasattr(player, 'achievements'):
            return 0
        return sum(a.get('points', 0) for a in player.achievements.values())
    
    @classmethod
    def get_player_achievements(cls, player: 'Player') -> List[str]:
        """Get list of unlocked achievement IDs."""
        if not hasattr(player, 'achievements'):
            return []
        return list(player.achievements.keys())
    
    @classmethod
    async def show_achievements(cls, player: 'Player', category: Optional[str] = None) -> None:
        """Show achievements to player."""
        c = player.config.COLORS
        
        unlocked = cls.get_player_achievements(player)
        total_points = cls.get_player_points(player)
        max_points = sum(a.points for a in ACHIEVEMENTS.values())
        
        await player.send(f"\n{c['bright_cyan']}═══════════════════════════════════════{c['reset']}")
        await player.send(f"{c['bright_cyan']}         ★ ACHIEVEMENTS ★{c['reset']}")
        await player.send(f"{c['bright_cyan']}═══════════════════════════════════════{c['reset']}")
        await player.send(f"{c['yellow']}Points: {total_points}/{max_points}{c['reset']}")
        await player.send(f"{c['white']}Unlocked: {len(unlocked)}/{len(ACHIEVEMENTS)}{c['reset']}")
        await player.send("")
        
        # Group by category
        categories = {}
        for ach_id, ach in ACHIEVEMENTS.items():
            if category and ach.category != category:
                continue
            if ach.category not in categories:
                categories[ach.category] = []
            categories[ach.category].append((ach_id, ach))
        
        category_names = {
            'progression': '📈 Progression',
            'combat': '⚔️ Combat',
            'exploration': '🗺️ Exploration',
            'collection': '💎 Collection',
            'social': '👥 Social',
        }
        
        for cat, achievements in sorted(categories.items()):
            cat_name = category_names.get(cat, cat.title())
            await player.send(f"{c['bright_white']}{cat_name}{c['reset']}")
            
            for ach_id, ach in achievements:
                is_unlocked = ach_id in unlocked
                
                # Hidden achievements only show if unlocked
                if ach.hidden and not is_unlocked:
                    await player.send(f"  {c['bright_black']}??? - Hidden achievement{c['reset']}")
                    continue
                
                if is_unlocked:
                    status = f"{c['bright_green']}✓{c['reset']}"
                    name_color = c['bright_white']
                else:
                    status = f"{c['bright_black']}○{c['reset']}"
                    name_color = c['white']
                
                points_str = f"{c['yellow']}[{ach.points}]{c['reset']}"
                await player.send(f"  {status} {ach.icon} {name_color}{ach.name}{c['reset']} {points_str}")
                await player.send(f"      {c['bright_black']}{ach.description}{c['reset']}")
            
            await player.send("")
        
        await player.send(f"{c['bright_cyan']}═══════════════════════════════════════{c['reset']}")
