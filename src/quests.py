"""
Quest System

Provides a simple quest system for kill/fetch quests with:
- Quest definitions (JSON format)
- Progress tracking
- Rewards (XP, gold, items)
- Quest giver NPCs
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING, Any
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from player import Player
    from mobs import Mobile

logger = logging.getLogger(__name__)


@dataclass
class QuestObjective:
    """A single quest objective (kill X, collect Y, etc.)."""
    type: str  # 'kill', 'collect', 'talk', 'explore', 'escort'
    description: str
    target: str  # Mob name, item vnum, npc vnum, or room vnum
    current: int = 0
    required: int = 1
    completed: bool = False

    def check_progress(self) -> bool:
        """Check if objective is complete."""
        if self.current >= self.required:
            self.completed = True
        return self.completed

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'type': self.type,
            'description': self.description,
            'target': self.target,
            'current': self.current,
            'required': self.required,
            'completed': self.completed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestObjective':
        """Load from dictionary."""
        return cls(
            type=data['type'],
            description=data['description'],
            target=data['target'],
            current=data.get('current', 0),
            required=data.get('required', 1),
            completed=data.get('completed', False)
        )


@dataclass
class ActiveQuest:
    """An active quest that a player is working on."""
    quest_id: str
    name: str
    description: str
    quest_type: str
    objectives: List[QuestObjective]
    rewards: Dict[str, Any]
    started_at: datetime
    time_limit: Optional[int] = None  # Minutes

    def is_complete(self) -> bool:
        """Check if all objectives are complete."""
        return all(obj.completed for obj in self.objectives)

    def is_expired(self) -> bool:
        """Check if quest has expired (time limit)."""
        if not self.time_limit:
            return False
        elapsed = (datetime.now() - self.started_at).total_seconds() / 60
        return elapsed >= self.time_limit

    def get_progress_string(self) -> str:
        """Get a string representation of quest progress."""
        lines = []
        for i, obj in enumerate(self.objectives, 1):
            status = "✓" if obj.completed else " "
            lines.append(f"  [{status}] {obj.description} ({obj.current}/{obj.required})")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'quest_id': self.quest_id,
            'name': self.name,
            'description': self.description,
            'quest_type': self.quest_type,
            'objectives': [obj.to_dict() for obj in self.objectives],
            'rewards': self.rewards,
            'started_at': self.started_at.isoformat(),
            'time_limit': self.time_limit
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ActiveQuest':
        """Load from dictionary."""
        return cls(
            quest_id=data['quest_id'],
            name=data['name'],
            description=data['description'],
            quest_type=data['quest_type'],
            objectives=[QuestObjective.from_dict(obj) for obj in data['objectives']],
            rewards=data['rewards'],
            started_at=datetime.fromisoformat(data['started_at']),
            time_limit=data.get('time_limit')
        )


# Quest definitions (could be loaded from JSON files)
QUEST_DEFINITIONS = {
    'quest_001': {
        'name': 'Goblin Extermination',
        'description': 'The goblins have been raiding nearby farms. Slay 10 goblins to protect the villagers.',
        'type': 'kill',
        'level_min': 3,
        'level_max': 10,
        'quest_giver': 3005,  # NPC vnum in Midgaard
        'objectives': [
            {
                'type': 'kill',
                'description': 'Slay goblins',
                'target': 'goblin',
                'required': 10
            }
        ],
        'rewards': {
            'exp': 500,
            'gold': 100,
            'items': []
        },
        'repeatable': False
    },
    'quest_002': {
        'name': 'Herb Collection',
        'description': 'The healer needs healing herbs from the forest. Collect 5 herbs.',
        'type': 'fetch',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3001,
        'objectives': [
            {
                'type': 'collect',
                'description': 'Collect healing herbs',
                'target': '4100',  # Item vnum
                'required': 5
            }
        ],
        'rewards': {
            'exp': 200,
            'gold': 50,
            'items': []
        },
        'repeatable': True
    },
    'quest_003': {
        'name': 'The Lost Sword',
        'description': 'A warrior lost his sword in the Goblin Warrens. Retrieve it and return it to him.',
        'type': 'fetch',
        'level_min': 5,
        'level_max': 15,
        'quest_giver': 3006,
        'objectives': [
            {
                'type': 'collect',
                'description': 'Find the lost sword',
                'target': '6050',  # Sword vnum in Goblin Warrens
                'required': 1
            }
        ],
        'rewards': {
            'exp': 800,
            'gold': 200,
            'items': []
        },
        'repeatable': False
    },
}


class QuestManager:
    """Manages quest state and progression."""

    @staticmethod
    async def offer_quest(player: 'Player', quest_id: str):
        """
        Offer a quest to the player.

        Args:
            player: The player to offer the quest to
            quest_id: ID of the quest to offer
        """
        quest_def = QUEST_DEFINITIONS.get(quest_id)
        if not quest_def:
            logger.warning(f"Quest {quest_id} not found")
            return

        # Check if player already has this quest
        if QuestManager.has_active_quest(player, quest_id):
            await player.send("You are already working on this quest.")
            return

        # Check if player has completed this quest (and it's not repeatable)
        if not quest_def.get('repeatable', False) and quest_id in player.quests_completed:
            await player.send("You have already completed this quest.")
            return

        # Check level requirements
        if player.level < quest_def.get('level_min', 1):
            await player.send("You are not experienced enough for this quest.")
            return
        if player.level > quest_def.get('level_max', 50):
            await player.send("This quest is beneath your abilities.")
            return

        # Display quest offer
        c = player.config.COLORS
        await player.send(f"\r\n{c['bright_yellow']}Quest Available: {quest_def['name']}{c['reset']}")
        await player.send(f"{c['white']}{quest_def['description']}{c['reset']}\r\n")

        await player.send(f"{c['cyan']}Objectives:{c['reset']}")
        for obj in quest_def['objectives']:
            await player.send(f"  - {obj['description']} (0/{obj['required']})")

        await player.send(f"\r\n{c['green']}Rewards:{c['reset']}")
        if quest_def['rewards'].get('exp'):
            await player.send(f"  - {quest_def['rewards']['exp']} experience")
        if quest_def['rewards'].get('gold'):
            await player.send(f"  - {quest_def['rewards']['gold']} gold")
        if quest_def['rewards'].get('items'):
            await player.send(f"  - Special items")

        await player.send(f"\r\n{c['yellow']}Type 'quest accept {quest_id}' to accept this quest.{c['reset']}\r\n")

    @staticmethod
    async def accept_quest(player: 'Player', quest_id: str):
        """
        Accept a quest.

        Args:
            player: The player accepting the quest
            quest_id: ID of the quest to accept
        """
        quest_def = QUEST_DEFINITIONS.get(quest_id)
        if not quest_def:
            await player.send("Unknown quest.")
            return

        # Create active quest
        objectives = [
            QuestObjective(
                type=obj['type'],
                description=obj['description'],
                target=str(obj['target']),
                required=obj['required']
            )
            for obj in quest_def['objectives']
        ]

        active_quest = ActiveQuest(
            quest_id=quest_id,
            name=quest_def['name'],
            description=quest_def['description'],
            quest_type=quest_def['type'],
            objectives=objectives,
            rewards=quest_def['rewards'],
            started_at=datetime.now(),
            time_limit=quest_def.get('time_limit')
        )

        if not hasattr(player, 'active_quests'):
            player.active_quests = []
        player.active_quests.append(active_quest)

        c = player.config.COLORS
        await player.send(f"{c['bright_green']}Quest accepted: {quest_def['name']}{c['reset']}")
        logger.info(f"{player.name} accepted quest {quest_id}")

    @staticmethod
    async def check_quest_progress(player: 'Player', event_type: str, event_data: Dict):
        """
        Check and update quest progress based on an event.

        Args:
            player: The player whose quests to check
            event_type: Type of event ('kill', 'collect', 'talk', 'explore')
            event_data: Data about the event
        """
        if not hasattr(player, 'active_quests'):
            return

        for quest in player.active_quests:
            for obj in quest.objectives:
                if obj.completed:
                    continue

                if obj.type == 'kill' and event_type == 'kill':
                    # Check if killed mob matches target
                    mob_name = event_data.get('mob_name', '').lower()
                    if obj.target.lower() in mob_name:
                        obj.current += 1
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

                elif obj.type == 'collect' and event_type == 'collect':
                    # Check if collected item matches target
                    item_vnum = str(event_data.get('item_vnum', ''))
                    if obj.target == item_vnum:
                        obj.current += 1
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

            # Check if quest is complete
            if quest.is_complete():
                await QuestManager._notify_quest_complete(player, quest)

    @staticmethod
    async def _notify_quest_complete(player: 'Player', quest: ActiveQuest):
        """Notify player that quest is complete."""
        c = player.config.COLORS
        await player.send(f"\r\n{c['bright_yellow']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_yellow']}║{c['bright_green']} QUEST COMPLETE: {quest.name:<45}{c['bright_yellow']}║{c['reset']}")
        await player.send(f"{c['bright_yellow']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")
        await player.send(f"{c['white']}Return to the quest giver to claim your reward!{c['reset']}\r\n")

    @staticmethod
    async def complete_quest(player: 'Player', quest_id: str):
        """
        Complete a quest and grant rewards.

        Args:
            player: The player completing the quest
            quest_id: ID of the quest to complete
        """
        if not hasattr(player, 'active_quests'):
            await player.send("You have no active quests.")
            return

        # Find the quest
        quest = next((q for q in player.active_quests if q.quest_id == quest_id), None)
        if not quest:
            await player.send("You don't have that quest.")
            return

        if not quest.is_complete():
            await player.send("You haven't completed all objectives yet!")
            return

        # Grant rewards
        c = player.config.COLORS
        await player.send(f"\r\n{c['bright_green']}Quest Completed: {quest.name}{c['reset']}\r\n")

        if quest.rewards.get('exp'):
            player.exp += quest.rewards['exp']
            await player.send(f"{c['bright_yellow']}You gain {quest.rewards['exp']} experience!{c['reset']}")

        if quest.rewards.get('gold'):
            player.gold += quest.rewards['gold']
            await player.send(f"{c['yellow']}You receive {quest.rewards['gold']} gold!{c['reset']}")

        if quest.rewards.get('items'):
            await player.send(f"{c['bright_cyan']}You receive special items!{c['reset']}")
            # TODO: Create and give items to player

        # Move quest to completed
        if not hasattr(player, 'quests_completed'):
            player.quests_completed = []
        player.quests_completed.append(quest_id)
        player.active_quests.remove(quest)

        await player.send(f"\r\n{c['green']}Quest reward claimed!{c['reset']}\r\n")
        logger.info(f"{player.name} completed quest {quest_id}")

    @staticmethod
    async def abandon_quest(player: 'Player', quest_id: str):
        """
        Abandon a quest.

        Args:
            player: The player abandoning the quest
            quest_id: ID of the quest to abandon
        """
        if not hasattr(player, 'active_quests'):
            await player.send("You have no active quests.")
            return

        quest = next((q for q in player.active_quests if q.quest_id == quest_id), None)
        if not quest:
            await player.send("You don't have that quest.")
            return

        player.active_quests.remove(quest)

        c = player.config.COLORS
        await player.send(f"{c['red']}Quest abandoned: {quest.name}{c['reset']}")
        logger.info(f"{player.name} abandoned quest {quest_id}")

    @staticmethod
    def has_active_quest(player: 'Player', quest_id: str) -> bool:
        """Check if player has an active quest."""
        if not hasattr(player, 'active_quests'):
            return False
        return any(q.quest_id == quest_id for q in player.active_quests)

    @staticmethod
    def get_available_quests(player: 'Player', quest_giver_vnum: int) -> List[str]:
        """
        Get list of available quests from a quest giver.

        Args:
            player: The player checking for quests
            quest_giver_vnum: VNum of the quest giver NPC

        Returns:
            List of quest IDs
        """
        available = []
        for quest_id, quest_def in QUEST_DEFINITIONS.items():
            if quest_def.get('quest_giver') != quest_giver_vnum:
                continue

            # Check if already active
            if QuestManager.has_active_quest(player, quest_id):
                continue

            # Check if completed (and not repeatable)
            if not quest_def.get('repeatable', False) and quest_id in getattr(player, 'quests_completed', []):
                continue

            # Check level requirements
            if player.level < quest_def.get('level_min', 1):
                continue
            if player.level > quest_def.get('level_max', 50):
                continue

            available.append(quest_id)

        return available
