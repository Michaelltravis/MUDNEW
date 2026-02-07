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
    type: str  # 'kill', 'collect', 'talk', 'visit', 'explore', 'escort'
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


@dataclass
class DialogueChoice:
    """A dialogue choice with optional effects."""
    text: str
    next_node: Optional[str] = None
    effects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DialogueNode:
    """Dialogue node for NPC conversations."""
    text: str
    choices: List[DialogueChoice] = field(default_factory=list)
    end: bool = False


# Quest definitions (could be loaded from JSON files)
QUEST_DEFINITIONS = {
    # ========== BEGINNER QUESTS (Level 1-10) ==========
    'rat_problem': {
        'name': 'Rat Problem',
        'description': 'The sewers are overrun with rats! Help clear them out before they spread disease.',
        'type': 'kill',
        'level_min': 1,
        'level_max': 8,
        'quest_giver': 3105,  # Mayor in Midgaard
        'objectives': [
            {'type': 'kill', 'description': 'Slay sewer rats', 'target': 'rat', 'required': 8}
        ],
        'rewards': {'exp': 300, 'gold': 75, 'items': []},
        'repeatable': True
    },
    'goblin_menace': {
        'name': 'The Goblin Menace',
        'description': "Goblins from Miden'Nir have been raiding the roads. Put an end to their threat!",
        'type': 'kill',
        'level_min': 3,
        'level_max': 12,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'kill', 'description': 'Slay goblins', 'target': 'goblin', 'required': 10}
        ],
        'rewards': {'exp': 600, 'gold': 150, 'items': []},
        'repeatable': False
    },


    'herbal_remedy': {
        'name': 'Herbal Remedy',
        'description': 'The healers need fresh herbs for their remedies. Gather them from the wilds.',
        'type': 'collect',
        'level_min': 1,
        'level_max': 10,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'collect', 'description': 'Gather healing herbs', 'target': '9004', 'required': 3}
        ],
        'rewards': {'exp': 200, 'gold': 60, 'items': []},
        'repeatable': True
    },
    'scout_temple': {
        'name': 'Scout the Temple',
        'description': 'Make sure the Temple of Midgaard is safe. Report once you have visited.',
        'type': 'visit',
        'level_min': 1,
        'level_max': 12,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'visit', 'description': 'Visit the Temple of Midgaard', 'target': '3001', 'required': 1}
        ],
        'rewards': {'exp': 250, 'gold': 80, 'items': []},
        'repeatable': True
    },
    'message_for_mayor': {
        'name': 'Message for the Mayor',
        'description': 'Captain Stolar needs you to deliver a message to the Mayor of Midgaard.',
        'type': 'talk',
        'level_min': 2,
        'level_max': 15,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'talk', 'description': 'Speak with the Mayor', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 300, 'gold': 100, 'items': []},
        'repeatable': False
    },

    # ========== INTERMEDIATE QUESTS (Level 8-20) ==========
    'orc_invasion': {
        'name': 'Orc Invasion',
        'description': 'Orcs from the Enclave are preparing to attack! Strike first and thin their numbers.',
        'type': 'kill',
        'level_min': 8,
        'level_max': 18,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay orcs', 'target': 'orc', 'required': 15}
        ],
        'rewards': {'exp': 1200, 'gold': 300, 'items': []},
        'repeatable': False
    },
    'spider_infestation': {
        'name': 'Spider Infestation',
        'description': 'Giant spiders have infested Arachnos! Clear them before they spread to the roads.',
        'type': 'kill',
        'level_min': 10,
        'level_max': 20,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay giant spiders', 'target': 'spider', 'required': 12}
        ],
        'rewards': {'exp': 1500, 'gold': 350, 'items': []},
        'repeatable': False
    },
    'moria_depths': {
        'name': 'Depths of Moria',
        'description': 'The orcs in Moria grow bold. Venture into the mines and reduce their numbers.',
        'type': 'kill',
        'level_min': 12,
        'level_max': 22,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay Moria orcs', 'target': 'orc', 'required': 20}
        ],
        'rewards': {'exp': 2000, 'gold': 500, 'items': []},
        'repeatable': False
    },

    # ========== ADVANCED QUESTS (Level 15-30) ==========
    'drow_threat': {
        'name': 'The Drow Threat',
        'description': 'Dark elves stir in the underground city. Investigate and eliminate their scouts.',
        'type': 'kill',
        'level_min': 15,
        'level_max': 28,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay drow', 'target': 'drow', 'required': 10}
        ],
        'rewards': {'exp': 2500, 'gold': 600, 'items': []},
        'repeatable': False
    },
    'undead_purge': {
        'name': 'Undead Purge',
        'description': 'The Necropolis teems with undead abominations. Destroy them before they march on the living!',
        'type': 'kill',
        'level_min': 20,
        'level_max': 35,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'kill', 'description': 'Destroy zombies', 'target': 'zombie', 'required': 10},
            {'type': 'kill', 'description': 'Destroy skeletons', 'target': 'skeleton', 'required': 10}
        ],
        'rewards': {'exp': 4000, 'gold': 1000, 'items': []},
        'repeatable': False
    },
    'desert_raiders': {
        'name': 'Desert Raiders',
        'description': 'Nomad raiders are attacking caravans in the Great Desert. End their reign of terror.',
        'type': 'kill',
        'level_min': 18,
        'level_max': 30,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay nomad raiders', 'target': 'nomad', 'required': 15}
        ],
        'rewards': {'exp': 3000, 'gold': 800, 'items': []},
        'repeatable': False
    },

    # ========== ELITE QUESTS (Level 25-45) ==========
    'demon_hunter': {
        'name': 'Demon Hunter',
        'description': 'Demons have begun emerging from portals. Hunt them down before they grow too numerous!',
        'type': 'kill',
        'level_min': 25,
        'level_max': 45,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'kill', 'description': 'Slay demons', 'target': 'demon', 'required': 8}
        ],
        'rewards': {'exp': 6000, 'gold': 2000, 'items': []},
        'repeatable': False
    },
    'dragon_slayer': {
        'name': 'Dragon Slayer',
        'description': 'A dragon terrorizes the land! Only the bravest heroes dare face such a creature.',
        'type': 'kill',
        'level_min': 30,
        'level_max': 50,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay a dragon', 'target': 'dragon', 'required': 1}
        ],
        'rewards': {'exp': 10000, 'gold': 5000, 'items': []},
        'repeatable': False
    },
    'elemental_mastery': {
        'name': 'Elemental Mastery',
        'description': 'Rogue elementals threaten the balance of nature. Destroy them to restore order.',
        'type': 'kill',
        'level_min': 28,
        'level_max': 45,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'kill', 'description': 'Slay elementals', 'target': 'elemental', 'required': 6}
        ],
        'rewards': {'exp': 5000, 'gold': 1500, 'items': []},
        'repeatable': False
    },

    # ========== REPEATABLE DAILY QUESTS ==========
    'bounty_hunter': {
        'name': 'Bounty Hunter',
        'description': 'The city needs dangerous creatures culled. Hunt them for a reward.',
        'type': 'kill',
        'level_min': 5,
        'level_max': 50,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay dangerous creatures', 'target': 'any', 'required': 25}
        ],
        'rewards': {'exp': 1000, 'gold': 250, 'items': []},
        'repeatable': True
    },
    'sewer_cleanup': {
        'name': 'Sewer Cleanup',
        'description': 'The sewers always need cleaning. Help keep them clear of vermin.',
        'type': 'kill',
        'level_min': 1,
        'level_max': 15,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'kill', 'description': 'Clear sewer creatures', 'target': 'any', 'required': 15}
        ],
        'rewards': {'exp': 400, 'gold': 100, 'items': []},
        'repeatable': True
    },

    # ========== HIDDEN DUNGEON QUEST CHAIN ==========
    'forgotten_passage': {
        'name': 'The Forgotten Passage',
        'description': 'Rumors speak of a hidden entrance near the Common Square. Investigate and report back.',
        'type': 'visit',
        'level_min': 10,
        'level_max': 30,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'visit', 'description': 'Find the hidden passage', 'target': '3074', 'required': 1}
        ],
        'rewards': {'exp': 500, 'gold': 150, 'items': []},
        'repeatable': False,
        'next_quest': 'sewer_king'
    },
    'sewer_king': {
        'name': 'The Sewer King',
        'description': 'A monstrous rat-man called the Sewer King rules the depths. End his reign of terror!',
        'type': 'kill',
        'level_min': 12,
        'level_max': 25,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay the Sewer King', 'target': 'sewer king', 'required': 1}
        ],
        'rewards': {'exp': 2000, 'gold': 500, 'items': []},
        'repeatable': False,
        'next_quest': 'shadow_assassin'
    },
    'shadow_assassin': {
        'name': 'The Shadow Assassin',
        'description': 'Something darker lurks beyond the Sewer King\'s domain. Hunt the shadow assassin!',
        'type': 'kill',
        'level_min': 18,
        'level_max': 30,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay the Shadow Assassin', 'target': 'shadow assassin', 'required': 1}
        ],
        'rewards': {'exp': 3500, 'gold': 800, 'items': []},
        'repeatable': False,
        'next_quest': 'ancient_guardian'
    },
    'ancient_guardian': {
        'name': 'The Ancient Guardian',
        'description': 'An ancient golem guards something precious in the deepest vault. Defeat it and claim the treasure!',
        'type': 'kill',
        'level_min': 22,
        'level_max': 35,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Defeat the Ancient Guardian', 'target': 'ancient guardian', 'required': 1}
        ],
        'rewards': {'exp': 5000, 'gold': 1500, 'items': [3128]},
        'repeatable': False
    },

    # ========== CITY PATROL QUESTS ==========
    'street_patrol': {
        'name': 'Street Patrol',
        'description': 'Pickpockets and urchins are causing trouble in the alleys. Help restore order.',
        'type': 'kill',
        'level_min': 3,
        'level_max': 12,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Deal with troublemakers', 'target': 'pickpocket', 'required': 3},
            {'type': 'kill', 'description': 'Chase off street urchins', 'target': 'street urchin', 'required': 5}
        ],
        'rewards': {'exp': 400, 'gold': 120, 'items': []},
        'repeatable': True
    },
    'tavern_trouble': {
        'name': 'Tavern Trouble',
        'description': 'The Grubby Inn is getting rowdy. Help calm things down before someone gets hurt.',
        'type': 'kill',
        'level_min': 2,
        'level_max': 10,
        'quest_giver': 3046,  # Bartender
        'objectives': [
            {'type': 'kill', 'description': 'Subdue drunk patrons', 'target': 'drunk patron', 'required': 3}
        ],
        'rewards': {'exp': 250, 'gold': 75, 'items': []},
        'repeatable': True
    },
    'rat_exterminator': {
        'name': 'Rat Exterminator',
        'description': 'Rats are infesting the lower passages. Clear them out!',
        'type': 'kill',
        'level_min': 1,
        'level_max': 8,
        'quest_giver': 3110,  # Temple Guide
        'objectives': [
            {'type': 'kill', 'description': 'Kill rats', 'target': 'rat', 'required': 10}
        ],
        'rewards': {'exp': 150, 'gold': 40, 'items': []},
        'repeatable': True
    },
    'bank_tour': {
        'name': 'Visit the Bank',
        'description': 'Learn about banking! Visit the First National Bank of Midgaard and check your balance.',
        'type': 'visit',
        'level_min': 1,
        'level_max': 10,
        'quest_giver': 3110,  # Temple Guide
        'objectives': [
            {'type': 'visit', 'description': 'Visit the bank', 'target': '3069', 'required': 1}
        ],
        'rewards': {'exp': 100, 'gold': 50, 'items': []},
        'repeatable': False
    },

    # ========== FOREST OF SHADOWS QUESTS ==========
    'forest_exploration': {
        'name': 'Into the Forest',
        'description': 'Explore the Forest of Shadows south of the west gate. Report back on what you find.',
        'type': 'visit',
        'level_min': 5,
        'level_max': 20,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'visit', 'description': 'Explore the forest edge', 'target': '20001', 'required': 1},
            {'type': 'visit', 'description': 'Find the hidden glade', 'target': '20010', 'required': 1}
        ],
        'rewards': {'exp': 400, 'gold': 100, 'items': []},
        'repeatable': False,
        'next_quest': 'wolf_hunt'
    },
    'wolf_hunt': {
        'name': 'Wolf Hunt',
        'description': 'The forest wolves are growing bold. Thin their numbers before they threaten travelers.',
        'type': 'kill',
        'level_min': 5,
        'level_max': 15,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay forest wolves', 'target': 'forest wolf', 'required': 8},
            {'type': 'kill', 'description': 'Slay dire wolves', 'target': 'dire wolf', 'required': 3}
        ],
        'rewards': {'exp': 600, 'gold': 200, 'items': []},
        'repeatable': True
    },
    'spider_infestation': {
        'name': 'Spider Infestation',
        'description': 'Giant spiders have taken over part of the forest. Clear them out!',
        'type': 'kill',
        'level_min': 6,
        'level_max': 18,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Kill giant spiders', 'target': 'giant spider', 'required': 10},
            {'type': 'kill', 'description': 'Kill venomous spiders', 'target': 'venomous spider', 'required': 5}
        ],
        'rewards': {'exp': 800, 'gold': 250, 'items': []},
        'repeatable': True,
        'next_quest': 'spider_queen'
    },
    'spider_queen': {
        'name': 'The Spider Queen',
        'description': 'The spiders are led by an ancient queen. Slay her to end the infestation for good!',
        'type': 'kill',
        'level_min': 10,
        'level_max': 20,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Slay the Spider Queen', 'target': 'spider queen', 'required': 1}
        ],
        'rewards': {'exp': 1500, 'gold': 400, 'items': [20003]},
        'repeatable': False
    },
    'alpha_challenge': {
        'name': 'Alpha Challenge',
        'description': 'The Alpha Wolf must be defeated to break the pack\'s grip on the forest.',
        'type': 'kill',
        'level_min': 12,
        'level_max': 22,
        'quest_giver': 3006,  # Captain Stolar
        'objectives': [
            {'type': 'kill', 'description': 'Defeat the Alpha Wolf', 'target': 'alpha wolf', 'required': 1}
        ],
        'rewards': {'exp': 2000, 'gold': 500, 'items': [20005]},
        'repeatable': False
    },

    # ========== MAIN STORY QUEST CHAIN ==========
    'awakening_echoes': {
        'name': 'Awakening Echoes',
        'description': 'You awaken with no memory. Find Captain Stolar, the city mentor, and seek answers.',
        'type': 'talk',
        'level_min': 1,
        'level_max': 10,
        'quest_giver': 3006,  # Captain Stolar (mentor)
        'objectives': [
            {'type': 'talk', 'description': 'Speak with Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 200, 'gold': 50, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a1_awakening'
    },
    'first_steps': {
        'name': 'First Steps',
        'description': 'Prove you can stand on your own. Visit the Temple and swear the oath of service.',
        'type': 'visit',
        'level_min': 1,
        'level_max': 10,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'visit', 'description': 'Visit the Temple of Midgaard', 'target': '3001', 'required': 1}
        ],
        'rewards': {'exp': 250, 'gold': 75, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a1_first_steps'
    },
    'shadow_in_sewers': {
        'name': 'Shadow in the Sewers',
        'description': 'Something twisted is spreading beneath the city. Clear the sewers of tainted vermin.',
        'type': 'kill',
        'level_min': 2,
        'level_max': 10,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay sewer rats', 'target': 'rat', 'required': 6}
        ],
        'rewards': {'exp': 300, 'gold': 90, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a1_shadow'
    },
    'corrupted_heart': {
        'name': 'Corrupted Heart',
        'description': 'A corrupted goblin champion stalks the tunnels. End it and bring back proof.',
        'type': 'kill',
        'level_min': 4,
        'level_max': 12,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay the corrupted goblin', 'target': 'goblin', 'required': 1}
        ],
        'rewards': {'exp': 500, 'gold': 120, 'items': ['Tainted Sigil']},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a1_boss'
    },
    'whispers_of_dark': {
        'name': 'Whispers of Dark',
        'description': 'Report the sigil to the Mayor and learn of the growing darkness.',
        'type': 'talk',
        'level_min': 5,
        'level_max': 12,
        'quest_giver': 3105,  # Mayor
        'objectives': [
            {'type': 'talk', 'description': 'Speak with the Mayor', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 650, 'gold': 150, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a1_reveal'
    },
    'journey_outward': {
        'name': 'Journey Outward',
        'description': 'Travel beyond the walls and gather allies by thinning the orc ranks.',
        'type': 'kill',
        'level_min': 10,
        'level_max': 20,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay orc raiders', 'target': 'orc', 'required': 8}
        ],
        'rewards': {'exp': 1200, 'gold': 300, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a2_journey'
    },
    'forked_path': {
        'name': 'A Forked Path',
        'description': 'The realm demands a choice: aid the villages or chase forbidden power. Speak with the Mayor.',
        'type': 'talk',
        'level_min': 12,
        'level_max': 22,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Consult the Mayor about your path', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 1400, 'gold': 350, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a2_choice'
    },
    'aid_ashgrove': {
        'name': 'Ashgrove Under Siege',
        'description': 'Aid the village of Ashgrove. Destroy the spider brood threatening the people.',
        'type': 'kill',
        'level_min': 13,
        'level_max': 22,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay giant spiders', 'target': 'spider', 'required': 8}
        ],
        'rewards': {'exp': 1600, 'gold': 400, 'items': ['Ashgrove Token']},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a2_aid'
    },
    'seize_relic': {
        'name': 'Relic of the Deep',
        'description': 'Seek the power hidden below. Drive back the drow scouts guarding the relic.',
        'type': 'kill',
        'level_min': 13,
        'level_max': 22,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'kill', 'description': 'Slay drow scouts', 'target': 'drow', 'required': 6}
        ],
        'rewards': {'exp': 1700, 'gold': 450, 'items': ['Obsidian Relic']},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a2_relic'
    },
    'unmask_villain': {
        'name': 'Unmask the Villain',
        'description': 'Evidence points to a traitor within the realm. Return to Captain Stolar.',
        'type': 'talk',
        'level_min': 15,
        'level_max': 24,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Report your findings to Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 2000, 'gold': 600, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a2_reveal'
    },
    'siege_prep': {
        'name': 'Gather the Siege',
        'description': 'The assault nears. Cut off desert raiders threatening supply lines.',
        'type': 'kill',
        'level_min': 20,
        'level_max': 30,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay nomad raiders', 'target': 'nomad', 'required': 10}
        ],
        'rewards': {'exp': 2600, 'gold': 800, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a3_prep'
    },
    'assault_stronghold': {
        'name': 'Assault the Stronghold',
        'description': 'Strike at the villain’s outer defenses and break the demon wardens.',
        'type': 'kill',
        'level_min': 22,
        'level_max': 30,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay demonic wardens', 'target': 'demon', 'required': 6}
        ],
        'rewards': {'exp': 3200, 'gold': 1000, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a3_assault'
    },
    'final_choice': {
        'name': 'The Final Choice',
        'description': 'Before the last battle, decide the fate of the realm. Speak with Captain Stolar.',
        'type': 'talk',
        'level_min': 24,
        'level_max': 30,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Make your final vow to Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 3500, 'gold': 1200, 'items': []},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a3_choice'
    },
    'endgame': {
        'name': 'End of the Dark',
        'description': 'Confront the corrupted tyrant in their lair and end the darkness forever.',
        'type': 'kill',
        'level_min': 26,
        'level_max': 35,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Defeat the dark tyrant', 'target': 'dragon', 'required': 1}
        ],
        'rewards': {'exp': 6000, 'gold': 2500, 'items': ['Champion’s Sigil']},
        'repeatable': False,
        'chain_id': 'main_story',
        'chain_stage': 'a3_final'
    },

    # ========== SIDE QUEST CHAINS ==========
    'forest_whispers': {
        'name': 'Forest Whispers',
        'description': 'The forest spirits stir. Speak with the druidic envoy to learn more.',
        'type': 'talk',
        'level_min': 5,
        'level_max': 20,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Speak with the druidic envoy', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 400, 'gold': 120, 'items': []},
        'repeatable': False,
        'chain_id': 'forest_spirits',
        'chain_stage': 'fs_intro'
    },
    'spirit_bloom': {
        'name': 'Spirit Bloom',
        'description': 'Purge the blighted growths threatening the forest spirits.',
        'type': 'kill',
        'level_min': 6,
        'level_max': 22,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'kill', 'description': 'Destroy blighted creatures', 'target': 'any', 'required': 6}
        ],
        'rewards': {'exp': 700, 'gold': 200, 'items': ['Spirit Bloom']},
        'repeatable': False,
        'chain_id': 'forest_spirits',
        'chain_stage': 'fs_bloom'
    },
    'heart_of_the_wood': {
        'name': 'Heart of the Wood',
        'description': 'Return the Spirit Bloom and receive the forest’s blessing.',
        'type': 'talk',
        'level_min': 8,
        'level_max': 24,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Return to the druidic envoy', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 900, 'gold': 280, 'items': ['Oakbound Charm']},
        'repeatable': False,
        'chain_id': 'forest_spirits',
        'chain_stage': 'fs_final'
    },
    'dwarven_lineage': {
        'name': 'Dwarven Lineage',
        'description': 'A dwarf elder seeks a lost family crest. Speak with Captain Stolar for leads.',
        'type': 'talk',
        'level_min': 8,
        'level_max': 24,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Speak with Captain Stolar about the crest', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 500, 'gold': 150, 'items': []},
        'repeatable': False,
        'chain_id': 'dwarven_heritage',
        'chain_stage': 'dh_intro'
    },
    'mine_echoes': {
        'name': 'Echoes in the Mine',
        'description': 'Search the mines for the missing crest by driving back orcs.',
        'type': 'kill',
        'level_min': 10,
        'level_max': 26,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay Moria orcs', 'target': 'orc', 'required': 12}
        ],
        'rewards': {'exp': 900, 'gold': 240, 'items': ['Dwarven Crest']},
        'repeatable': False,
        'chain_id': 'dwarven_heritage',
        'chain_stage': 'dh_mine'
    },
    'oath_of_stone': {
        'name': 'Oath of Stone',
        'description': 'Return the crest and swear the dwarven oath.',
        'type': 'talk',
        'level_min': 12,
        'level_max': 28,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Return to Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 1200, 'gold': 300, 'items': ['Stonebound Ring']},
        'repeatable': False,
        'chain_id': 'dwarven_heritage',
        'chain_stage': 'dh_final'
    },
    'shadows_inquiry': {
        'name': 'Shadows Inquiry',
        'description': 'Investigate a string of disappearances in the city.',
        'type': 'talk',
        'level_min': 6,
        'level_max': 22,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Speak with the Mayor about the disappearances', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 450, 'gold': 140, 'items': []},
        'repeatable': False,
        'chain_id': 'city_mystery',
        'chain_stage': 'cm_intro'
    },
    'trail_of_ashes': {
        'name': 'Trail of Ashes',
        'description': 'Follow the trail to the smugglers by clearing out goblin thugs.',
        'type': 'kill',
        'level_min': 7,
        'level_max': 22,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'kill', 'description': 'Slay goblin thugs', 'target': 'goblin', 'required': 8}
        ],
        'rewards': {'exp': 800, 'gold': 220, 'items': []},
        'repeatable': False,
        'chain_id': 'city_mystery',
        'chain_stage': 'cm_trail'
    },
    'the_last_witness': {
        'name': 'The Last Witness',
        'description': 'Confront the smuggler ringleader and learn the truth.',
        'type': 'talk',
        'level_min': 9,
        'level_max': 24,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Return with the witness report', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 1100, 'gold': 300, 'items': ['Watcher’s Badge']},
        'repeatable': False,
        'chain_id': 'city_mystery',
        'chain_stage': 'cm_final'
    },
    'lost_lineage': {
        'name': 'Lost Lineage',
        'description': 'A traveler seeks their missing family. Offer your help.',
        'type': 'talk',
        'level_min': 8,
        'level_max': 25,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Speak with Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 500, 'gold': 160, 'items': []},
        'repeatable': False,
        'chain_id': 'lost_lineage',
        'chain_stage': 'll_intro'
    },
    'blood_and_bond': {
        'name': 'Blood and Bond',
        'description': 'Retrieve proof of kinship by defeating the bandit captains.',
        'type': 'kill',
        'level_min': 10,
        'level_max': 26,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'kill', 'description': 'Slay bandit captains', 'target': 'nomad', 'required': 6}
        ],
        'rewards': {'exp': 900, 'gold': 260, 'items': ['Family Locket']},
        'repeatable': False,
        'chain_id': 'lost_lineage',
        'chain_stage': 'll_bond'
    },
    'homecoming': {
        'name': 'Homecoming',
        'description': 'Bring the proof to the traveler and decide their future.',
        'type': 'talk',
        'level_min': 12,
        'level_max': 28,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'talk', 'description': 'Return to Captain Stolar', 'target': '3006', 'required': 1}
        ],
        'rewards': {'exp': 1200, 'gold': 340, 'items': ['Traveler’s Cloak']},
        'repeatable': False,
        'chain_id': 'lost_lineage',
        'chain_stage': 'll_final'
    },
    'mercy_or_wrath': {
        'name': 'Mercy or Wrath',
        'description': 'A captured raider begs for mercy. Decide their fate.',
        'type': 'talk',
        'level_min': 14,
        'level_max': 30,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'talk', 'description': 'Deliver your judgment', 'target': '3105', 'required': 1}
        ],
        'rewards': {'exp': 900, 'gold': 240, 'items': []},
        'repeatable': False,
        'chain_id': 'moral_dilemma',
        'chain_stage': 'md_choice'
    },
    'aftermath': {
        'name': 'Aftermath',
        'description': 'Deal with the consequences of your decision.',
        'type': 'kill',
        'level_min': 16,
        'level_max': 32,
        'quest_giver': 3105,
        'objectives': [
            {'type': 'kill', 'description': 'Face the raider’s allies', 'target': 'orc', 'required': 6}
        ],
        'rewards': {'exp': 1300, 'gold': 380, 'items': ['Judicator’s Token']},
        'repeatable': False,
        'chain_id': 'moral_dilemma',
        'chain_stage': 'md_final'
    },

    # ========== FACTION QUEST LINES ==========
    'midgaard_guard_duty': {
        'name': 'Guard Duty',
        'description': 'Midgaard needs watchful eyes. Patrol and drive off goblin raiders.',
        'type': 'kill',
        'level_min': 5,
        'level_max': 18,
        'quest_giver': 3002,
        'objectives': [
            {'type': 'kill', 'description': 'Slay goblin raiders', 'target': 'goblin', 'required': 6}
        ],
        'rewards': {'exp': 500, 'gold': 120, 'items': [], 'reputation': {'midgaard': 120}},
        'repeatable': False
    },
    'midgaard_city_watch': {
        'name': 'City Watch',
        'description': 'Help the City Watch root out thieves within Midgaard’s walls.',
        'type': 'kill',
        'level_min': 10,
        'level_max': 25,
        'quest_giver': 3002,
        'min_reputation': {'midgaard': 300},
        'objectives': [
            {'type': 'kill', 'description': 'Deal with thieves', 'target': 'thief', 'required': 6}
        ],
        'rewards': {'exp': 900, 'gold': 220, 'items': [], 'reputation': {'midgaard': 180}},
        'repeatable': False
    },
    'midgaard_honor_guard': {
        'name': 'Honor Guard',
        'description': 'Prove your loyalty by breaking an orcish warband outside the city.',
        'type': 'kill',
        'level_min': 16,
        'level_max': 35,
        'quest_giver': 3105,
        'min_reputation': {'midgaard': 600},
        'objectives': [
            {'type': 'kill', 'description': 'Slay orc warband members', 'target': 'orc', 'required': 10}
        ],
        'rewards': {'exp': 1400, 'gold': 400, 'items': [], 'reputation': {'midgaard': 240}},
        'repeatable': False
    },

    'elves_forest_wardens': {
        'name': 'Forest Wardens',
        'description': 'Protect the sacred forest from encroaching beasts.',
        'type': 'kill',
        'level_min': 6,
        'level_max': 20,
        'quest_giver': 4004,
        'objectives': [
            {'type': 'kill', 'description': 'Cull forest predators', 'target': 'wolf', 'required': 6}
        ],
        'rewards': {'exp': 600, 'gold': 140, 'items': [], 'reputation': {'elves': 120}},
        'repeatable': False
    },
    'elves_sacred_grove': {
        'name': 'Sacred Grove',
        'description': 'Purge corrupt creatures from the sacred grove.',
        'type': 'kill',
        'level_min': 12,
        'level_max': 26,
        'quest_giver': 4004,
        'min_reputation': {'elves': 300},
        'objectives': [
            {'type': 'kill', 'description': 'Destroy corrupted beasts', 'target': 'spider', 'required': 6}
        ],
        'rewards': {'exp': 950, 'gold': 260, 'items': [], 'reputation': {'elves': 200}},
        'repeatable': False
    },
    'elves_starlight_pact': {
        'name': 'Starlight Pact',
        'description': 'Complete the ancient rite under the stars for the Elven elders.',
        'type': 'talk',
        'level_min': 18,
        'level_max': 40,
        'quest_giver': 4004,
        'min_reputation': {'elves': 600},
        'objectives': [
            {'type': 'talk', 'description': 'Swear the Starlight Pact', 'target': '4004', 'required': 1}
        ],
        'rewards': {'exp': 1700, 'gold': 420, 'items': [], 'reputation': {'elves': 260}},
        'repeatable': False
    },

    'dwarves_iron_oath': {
        'name': 'The Iron Oath',
        'description': 'Aid the dwarves in keeping the trade routes safe.',
        'type': 'kill',
        'level_min': 6,
        'level_max': 22,
        'quest_giver': 3003,
        'objectives': [
            {'type': 'kill', 'description': 'Drive off cave raiders', 'target': 'goblin', 'required': 6}
        ],
        'rewards': {'exp': 620, 'gold': 160, 'items': [], 'reputation': {'dwarves': 120}},
        'repeatable': False
    },
    'dwarves_deep_delves': {
        'name': 'Deep Delves',
        'description': 'Clear the deep tunnels of lurking threats.',
        'type': 'kill',
        'level_min': 12,
        'level_max': 28,
        'quest_giver': 3003,
        'min_reputation': {'dwarves': 300},
        'objectives': [
            {'type': 'kill', 'description': 'Slay tunnel beasts', 'target': 'troll', 'required': 4}
        ],
        'rewards': {'exp': 980, 'gold': 280, 'items': [], 'reputation': {'dwarves': 200}},
        'repeatable': False
    },
    'dwarves_rune_forge': {
        'name': 'Rune Forge',
        'description': 'Assist in the forging of a rune-etched masterwork.',
        'type': 'talk',
        'level_min': 18,
        'level_max': 40,
        'quest_giver': 3003,
        'min_reputation': {'dwarves': 600},
        'objectives': [
            {'type': 'talk', 'description': 'Complete the forging ritual', 'target': '3003', 'required': 1}
        ],
        'rewards': {'exp': 1750, 'gold': 440, 'items': [], 'reputation': {'dwarves': 260}},
        'repeatable': False
    },

    'thieves_guild_cutpurse': {
        'name': 'Cutpurse Initiation',
        'description': 'Prove your worth by slipping past the city watch.',
        'type': 'visit',
        'level_min': 6,
        'level_max': 20,
        'quest_giver': 3006,
        'objectives': [
            {'type': 'visit', 'description': 'Slip through Midgaard unnoticed', 'target': '3002', 'required': 1}
        ],
        'rewards': {'exp': 600, 'gold': 180, 'items': [], 'reputation': {'thieves_guild': 120}},
        'repeatable': False
    },
    'thieves_guild_silent_blade': {
        'name': 'Silent Blade',
        'description': 'Eliminate a dangerous informant without raising alarms.',
        'type': 'kill',
        'level_min': 12,
        'level_max': 28,
        'quest_giver': 3006,
        'min_reputation': {'thieves_guild': 300},
        'objectives': [
            {'type': 'kill', 'description': 'Deal with the informer', 'target': 'guard', 'required': 4}
        ],
        'rewards': {'exp': 980, 'gold': 320, 'items': [], 'reputation': {'thieves_guild': 200}},
        'repeatable': False
    },
    'thieves_guild_shadow_king': {
        'name': 'Shadow King',
        'description': 'Establish dominance over rival thieves in the undercity.',
        'type': 'kill',
        'level_min': 18,
        'level_max': 40,
        'quest_giver': 3006,
        'min_reputation': {'thieves_guild': 600},
        'objectives': [
            {'type': 'kill', 'description': 'Defeat rival cutthroats', 'target': 'thief', 'required': 8}
        ],
        'rewards': {'exp': 1750, 'gold': 480, 'items': [], 'reputation': {'thieves_guild': 260}},
        'repeatable': False
    },

    'mages_guild_apprentice': {
        'name': 'Apprentice Trials',
        'description': 'Complete the arcane trials set by the Mages Guild.',
        'type': 'collect',
        'level_min': 6,
        'level_max': 20,
        'quest_giver': 3001,
        'objectives': [
            {'type': 'collect', 'description': 'Gather arcane reagents', 'target': '9004', 'required': 3}
        ],
        'rewards': {'exp': 620, 'gold': 160, 'items': [], 'reputation': {'mages_guild': 120}},
        'repeatable': False
    },
    'mages_guild_archives': {
        'name': 'Arcane Archives',
        'description': 'Recover lost scrolls for the Mages Guild.',
        'type': 'collect',
        'level_min': 12,
        'level_max': 28,
        'quest_giver': 3001,
        'min_reputation': {'mages_guild': 300},
        'objectives': [
            {'type': 'collect', 'description': 'Recover ancient scrolls', 'target': '9005', 'required': 2}
        ],
        'rewards': {'exp': 980, 'gold': 280, 'items': [], 'reputation': {'mages_guild': 200}},
        'repeatable': False
    },
    'mages_guild_ascension': {
        'name': 'Arcane Ascension',
        'description': 'Pass the final trial to join the Conclave.',
        'type': 'talk',
        'level_min': 18,
        'level_max': 40,
        'quest_giver': 3001,
        'min_reputation': {'mages_guild': 600},
        'objectives': [
            {'type': 'talk', 'description': 'Complete the ascension rite', 'target': '3001', 'required': 1}
        ],
        'rewards': {'exp': 1750, 'gold': 460, 'items': [], 'reputation': {'mages_guild': 260}},
        'repeatable': False
    },

    # ========== TUTORIAL QUESTS ==========
    'tutorial_1_awakening': {
        'name': 'Awakening',
        'description': 'Speak with Sage Aldric at the Temple to begin your training.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'auto_start': True,
        'objectives': [
            {'type': 'talk', 'description': 'Speak with Sage Aldric', 'target': '3200', 'required': 1}
        ],
        'rewards': {'exp': 50, 'gold': 10},
        'next_quest': 'tutorial_2_look_around',
        'repeatable': False
    },
    'tutorial_2_look_around': {
        'name': 'Eyes Open',
        'description': 'Learn to observe your surroundings by exploring the Temple area.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'visit', 'description': 'Visit the Temple Square', 'target': '3005', 'required': 1},
            {'type': 'visit', 'description': 'Visit the Temple Altar', 'target': '3054', 'required': 1}
        ],
        'rewards': {'exp': 75, 'gold': 15},
        'next_quest': 'tutorial_3_know_thyself',
        'repeatable': False
    },
    'tutorial_3_know_thyself': {
        'name': 'Know Thyself',
        'description': 'Learn about your character using score, equipment, and inventory.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'command', 'description': 'Check your score', 'target': 'score', 'required': 1},
            {'type': 'command', 'description': 'View your equipment', 'target': 'equipment', 'required': 1},
            {'type': 'command', 'description': 'Check your inventory', 'target': 'inventory', 'required': 1}
        ],
        'rewards': {'exp': 100, 'gold': 20},
        'next_quest': 'tutorial_4_skills',
        'repeatable': False
    },
    'tutorial_4_skills': {
        'name': 'The Way of Your Class',
        'description': 'Learn about your class abilities using skills and spells commands.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'command', 'description': 'View your skills', 'target': 'skills', 'required': 1},
            {'type': 'command', 'description': 'View your spells', 'target': 'spells', 'required': 1}
        ],
        'rewards': {'exp': 100, 'gold': 25, 'practices': 2},
        'next_quest': 'tutorial_5_combat',
        'repeatable': False
    },
    'tutorial_5_combat': {
        'name': 'Blood and Steel',
        'description': 'Learn combat by defeating a training dummy at the Training Grounds.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'visit', 'description': 'Go to the Training Grounds', 'target': '3078', 'required': 1},
            {'type': 'kill', 'description': 'Defeat a training dummy', 'target': 'dummy', 'required': 1}
        ],
        'rewards': {'exp': 150, 'gold': 30},
        'next_quest': 'tutorial_6_healing',
        'repeatable': False
    },
    'tutorial_6_healing': {
        'name': 'The Art of Survival',
        'description': 'Learn to recover from injuries using rest, stand, and eating.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'command', 'description': 'Rest to recover', 'target': 'rest', 'required': 1},
            {'type': 'command', 'description': 'Stand back up', 'target': 'stand', 'required': 1},
            {'type': 'command', 'description': 'Eat some food', 'target': 'eat', 'required': 1}
        ],
        'rewards': {'exp': 100, 'gold': 25},
        'next_quest': 'tutorial_7_shopping',
        'repeatable': False
    },
    'tutorial_7_shopping': {
        'name': 'Tools of the Trade',
        'description': 'Learn to buy and sell at shops.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'visit', 'description': 'Visit the Weapon Shop', 'target': '3031', 'required': 1},
            {'type': 'command', 'description': 'View shop inventory', 'target': 'list', 'required': 1},
            {'type': 'command', 'description': 'Buy any item', 'target': 'buy', 'required': 1}
        ],
        'rewards': {'exp': 125, 'gold': 100},
        'next_quest': 'tutorial_8_exploration',
        'repeatable': False
    },
    'tutorial_8_exploration': {
        'name': 'Into the Unknown',
        'description': 'Venture beyond the city and prove yourself ready for adventure.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 5,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'visit', 'description': 'Visit the South Gate', 'target': '3053', 'required': 1},
            {'type': 'kill', 'description': 'Defeat a creature outside the city', 'target': 'any', 'required': 1},
            {'type': 'visit', 'description': 'Return to the Temple', 'target': '3001', 'required': 1}
        ],
        'rewards': {'exp': 300, 'gold': 150, 'title': 'the Initiated'},
        'next_quest': 'tutorial_9_newbie_zone',
        'repeatable': False
    },
    'tutorial_9_newbie_zone': {
        'name': 'Proving Grounds',
        'description': 'Sage Aldric recommends testing your skills in the Newbie Zone east of the Great Field.',
        'type': 'tutorial',
        'level_min': 1,
        'level_max': 7,
        'quest_giver': 3200,
        'objectives': [
            {'type': 'visit', 'description': 'Find the Great Field', 'target': '3061', 'required': 1},
            {'type': 'visit', 'description': 'Enter the Newbie Zone', 'target': '18600', 'required': 1},
            {'type': 'kill', 'description': 'Defeat creatures in the Newbie Zone', 'target': 'any', 'required': 3},
            {'type': 'visit', 'description': 'Return to Sage Aldric', 'target': '3001', 'required': 1}
        ],
        'rewards': {'exp': 500, 'gold': 200},
        'repeatable': False
    },
}

# Quest chains with branching paths and stages
QUEST_CHAINS = {
    'main_story': {
        'name': 'The Shattered Crown',
        'start_stage': 'a1_awakening',
        'stages': {
            'a1_awakening': {'quest_id': 'awakening_echoes', 'next': 'a1_first_steps', 'act': 'Act I: The Awakening'},
            'a1_first_steps': {'quest_id': 'first_steps', 'next': 'a1_shadow', 'act': 'Act I: The Awakening'},
            'a1_shadow': {'quest_id': 'shadow_in_sewers', 'next': 'a1_boss', 'act': 'Act I: The Awakening'},
            'a1_boss': {'quest_id': 'corrupted_heart', 'next': 'a1_reveal', 'act': 'Act I: The Awakening'},
            'a1_reveal': {'quest_id': 'whispers_of_dark', 'next': 'a2_journey', 'act': 'Act I: The Awakening'},
            'a2_journey': {'quest_id': 'journey_outward', 'next': 'a2_choice', 'act': 'Act II: The Journey'},
            'a2_choice': {
                'quest_id': 'forked_path',
                'act': 'Act II: The Journey',
                'branches': {
                    'path': {
                        'aid': 'a2_aid',
                        'power': 'a2_relic'
                    }
                },
                'next': 'a2_aid'
            },
            'a2_aid': {'quest_id': 'aid_ashgrove', 'next': 'a2_reveal', 'act': 'Act II: The Journey'},
            'a2_relic': {'quest_id': 'seize_relic', 'next': 'a2_reveal', 'act': 'Act II: The Journey'},
            'a2_reveal': {'quest_id': 'unmask_villain', 'next': 'a3_prep', 'act': 'Act II: The Journey'},
            'a3_prep': {'quest_id': 'siege_prep', 'next': 'a3_assault', 'act': 'Act III: The Confrontation'},
            'a3_assault': {'quest_id': 'assault_stronghold', 'next': 'a3_choice', 'act': 'Act III: The Confrontation'},
            'a3_choice': {
                'quest_id': 'final_choice',
                'act': 'Act III: The Confrontation',
                'branches': {
                    'final_vow': {
                        'mercy': 'a3_final',
                        'wrath': 'a3_final'
                    }
                },
                'next': 'a3_final'
            },
            'a3_final': {'quest_id': 'endgame', 'next': None, 'act': 'Act III: The Confrontation'}
        }
    },
    'forest_spirits': {
        'name': 'Whispers of the Grove',
        'start_stage': 'fs_intro',
        'stages': {
            'fs_intro': {'quest_id': 'forest_whispers', 'next': 'fs_bloom'},
            'fs_bloom': {'quest_id': 'spirit_bloom', 'next': 'fs_final'},
            'fs_final': {'quest_id': 'heart_of_the_wood', 'next': None}
        }
    },
    'dwarven_heritage': {
        'name': 'Legacy of Stone',
        'start_stage': 'dh_intro',
        'stages': {
            'dh_intro': {'quest_id': 'dwarven_lineage', 'next': 'dh_mine'},
            'dh_mine': {'quest_id': 'mine_echoes', 'next': 'dh_final'},
            'dh_final': {'quest_id': 'oath_of_stone', 'next': None}
        }
    },
    'city_mystery': {
        'name': 'The Vanishing',
        'start_stage': 'cm_intro',
        'stages': {
            'cm_intro': {'quest_id': 'shadows_inquiry', 'next': 'cm_trail'},
            'cm_trail': {'quest_id': 'trail_of_ashes', 'next': 'cm_final'},
            'cm_final': {'quest_id': 'the_last_witness', 'next': None}
        }
    },
    'lost_lineage': {
        'name': 'Bloodlines',
        'start_stage': 'll_intro',
        'stages': {
            'll_intro': {'quest_id': 'lost_lineage', 'next': 'll_bond'},
            'll_bond': {'quest_id': 'blood_and_bond', 'next': 'll_final'},
            'll_final': {'quest_id': 'homecoming', 'next': None}
        }
    },
    'moral_dilemma': {
        'name': 'Judgment of Ashes',
        'start_stage': 'md_choice',
        'stages': {
            'md_choice': {'quest_id': 'mercy_or_wrath', 'next': 'md_final'},
            'md_final': {'quest_id': 'aftermath', 'next': None}
        }
    }
}

# Dialogue trees keyed by NPC vnum
DIALOGUE_TREES = {
    3006: {
        'start': DialogueNode(
            text=(
                "The captain studies you with a steady gaze. 'You look like you've seen a ghost.'"
            ),
            choices=[
                DialogueChoice(
                    text="Who am I?",
                    next_node='memory',
                    effects=[{'type': 'set_flag', 'key': 'memory', 'value': 'fractured'}]
                ),
                DialogueChoice(
                    text="I'm ready to help.",
                    next_node='oath',
                    effects=[{'type': 'start_quest', 'quest_id': 'awakening_echoes'}]
                ),
                DialogueChoice(
                    text="Power is all that matters.",
                    next_node='power',
                    effects=[{'type': 'set_flag', 'key': 'path', 'value': 'power'}]
                )
            ]
        ),
        'memory': DialogueNode(
            text="'Your past is a storm. But your future is still yours to claim.'",
            choices=[
                DialogueChoice(
                    text="I'll help the realm.",
                    next_node='oath',
                    effects=[{'type': 'start_quest', 'quest_id': 'awakening_echoes'}]
                )
            ]
        ),
        'oath': DialogueNode(
            text="'Then take your first steps. The realm needs you.'",
            end=True
        ),
        'power': DialogueNode(
            text="'Power without purpose destroys. Choose carefully.'",
            end=True
        ),
        'final_vow': DialogueNode(
            text="'The tyrant falls tonight. Will you show mercy or wrath?'",
            choices=[
                DialogueChoice(
                    text="Mercy. The cycle must end.",
                    next_node='vow_mercy',
                    effects=[{'type': 'set_flag', 'key': 'final_vow', 'value': 'mercy'}]
                ),
                DialogueChoice(
                    text="Wrath. The realm needs fear.",
                    next_node='vow_wrath',
                    effects=[{'type': 'set_flag', 'key': 'final_vow', 'value': 'wrath'}]
                )
            ]
        ),
        'vow_mercy': DialogueNode(
            text="'Then strike true, and spare those who can change.'",
            end=True
        ),
        'vow_wrath': DialogueNode(
            text="'Then let them remember your fury.'",
            end=True
        )
    },
    3105: {
        'start': DialogueNode(
            text="The Mayor leans forward. 'The realm trembles, and we need champions.'",
            choices=[
                DialogueChoice(
                    text="I will aid the villages.",
                    next_node='aid',
                    effects=[{'type': 'set_flag', 'key': 'path', 'value': 'aid'}]
                ),
                DialogueChoice(
                    text="I seek the relics of power.",
                    next_node='power',
                    effects=[{'type': 'set_flag', 'key': 'path', 'value': 'power'}]
                )
            ]
        ),
        'aid': DialogueNode(
            text="'Then go. The people will sing your name.'",
            end=True
        ),
        'power': DialogueNode(
            text="'Dangerous, but the realm may need every edge.'",
            end=True
        )
    }
}


class QuestManager:
    """Manages quest state and progression."""

    @staticmethod
    def _get_chain_state(player: 'Player', chain_id: str, auto_init: bool = False) -> Dict[str, Any]:
        if not hasattr(player, 'quest_chains'):
            player.quest_chains = {}
        state = player.quest_chains.get(chain_id)
        if not state and auto_init:
            chain_def = QUEST_CHAINS.get(chain_id, {})
            state = {
                'stage': chain_def.get('start_stage'),
                'completed': False,
                'choices': {},
                'history': []
            }
            player.quest_chains[chain_id] = state
        return state

    @staticmethod
    def is_chain_quest_available(player: 'Player', quest_def: Dict[str, Any]) -> bool:
        chain_id = quest_def.get('chain_id')
        if not chain_id:
            return True
        chain_def = QUEST_CHAINS.get(chain_id)
        if not chain_def:
            return False
        stage = quest_def.get('chain_stage')
        state = QuestManager._get_chain_state(player, chain_id)
        if not state:
            return stage == chain_def.get('start_stage')
        if state.get('completed'):
            return False
        return state.get('stage') == stage

    @staticmethod
    def record_choice(player: 'Player', key: str, value: str):
        if not hasattr(player, 'quest_flags'):
            player.quest_flags = {}
        player.quest_flags[key] = value

    @staticmethod
    def advance_chain_from_quest(player: 'Player', quest_id: str):
        quest_def = QUEST_DEFINITIONS.get(quest_id)
        if not quest_def:
            return
        chain_id = quest_def.get('chain_id')
        if not chain_id:
            return
        chain_def = QUEST_CHAINS.get(chain_id, {})
        stage = quest_def.get('chain_stage')
        if not stage:
            return
        state = QuestManager._get_chain_state(player, chain_id, auto_init=True)
        stage_def = chain_def.get('stages', {}).get(stage, {})
        next_stage = stage_def.get('next')
        branches = stage_def.get('branches', {})
        for flag_key, branch_map in branches.items():
            choice = player.quest_flags.get(flag_key)
            if choice in branch_map:
                next_stage = branch_map[choice]
                break
        if next_stage:
            state['history'].append(stage)
            state['stage'] = next_stage
        else:
            state['history'].append(stage)
            state['stage'] = None
            state['completed'] = True

    @staticmethod
    async def handle_dialogue(player: 'Player', npc_vnum: int, choice_index: Optional[int] = None) -> bool:
        tree = DIALOGUE_TREES.get(npc_vnum)
        if not tree:
            return False

        if not hasattr(player, 'dialogue_state'):
            player.dialogue_state = {}

        node_id = player.dialogue_state.get(str(npc_vnum), 'start')
        node = tree.get(node_id) or tree.get('start')
        if not node:
            return False

        if choice_index is not None:
            if not node.choices:
                await player.send("There is nothing more to say.")
                return True
            if choice_index < 1 or choice_index > len(node.choices):
                await player.send("That is not a valid response.")
                return True
            choice = node.choices[choice_index - 1]
            for effect in choice.effects:
                effect_type = effect.get('type')
                if effect_type == 'set_flag':
                    QuestManager.record_choice(player, effect.get('key'), effect.get('value'))
                elif effect_type == 'start_quest':
                    await QuestManager.accept_quest(player, effect.get('quest_id'))
                elif effect_type == 'advance_chain':
                    chain_id = effect.get('chain_id')
                    stage = effect.get('stage')
                    if chain_id:
                        state = QuestManager._get_chain_state(player, chain_id, auto_init=True)
                        if stage:
                            state['stage'] = stage
                elif effect_type == 'grant_reward':
                    exp = effect.get('exp', 0)
                    gold = effect.get('gold', 0)
                    if exp:
                        player.exp += exp
                    if gold:
                        player.gold += gold

            node_id = choice.next_node or 'start'
            player.dialogue_state[str(npc_vnum)] = node_id
            node = tree.get(node_id) or node

        c = player.config.COLORS
        await player.send(f"{c['bright_cyan']}{node.text}{c['reset']}")
        if node.choices and not node.end:
            await player.send(f"{c['yellow']}Responses:{c['reset']}")
            for idx, choice in enumerate(node.choices, 1):
                await player.send(f"  {idx}. {choice.text}")
            await player.send(f"{c['white']}Use 'talk <npc> <number>' to respond.{c['reset']}")
        if node.end:
            player.dialogue_state.pop(str(npc_vnum), None)
        return True

    @staticmethod
    def get_story_progress(player: 'Player') -> str:
        chain_def = QUEST_CHAINS.get('main_story')
        if not chain_def:
            return "No main story configured."
        state = QuestManager._get_chain_state(player, 'main_story')
        if not state:
            return "Main Story: Not started"
        stage = state.get('stage')
        if state.get('completed'):
            return "Main Story: Completed"
        if not stage:
            return "Main Story: Not started"
        stage_def = chain_def['stages'].get(stage, {})
        quest_id = stage_def.get('quest_id')
        quest_name = QUEST_DEFINITIONS.get(quest_id, {}).get('name', 'Unknown')
        act = stage_def.get('act', 'Main Story')
        return f"{act} - Current: {quest_name}"

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

        if not QuestManager.is_chain_quest_available(player, quest_def):
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
        if quest_def['rewards'].get('reputation'):
            rep_lines = []
            for key, amount in quest_def['rewards']['reputation'].items():
                rep_lines.append(f"{key} {amount:+d}")
            await player.send(f"  - Reputation: {', '.join(rep_lines)}")

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

        if not QuestManager.is_chain_quest_available(player, quest_def):
            await player.send("That quest is not available right now.")
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

        if quest_def.get('chain_id'):
            state = QuestManager._get_chain_state(player, quest_def['chain_id'], auto_init=True)
            state['stage'] = quest_def.get('chain_stage', state.get('stage'))

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
            event_type: Type of event ('kill', 'collect', 'talk', 'visit', 'explore')
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
                    # 'any' target matches any mob kill
                    if obj.target.lower() == 'any' or obj.target.lower() in mob_name:
                        obj.current += 1
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

                elif obj.type == 'collect' and event_type == 'collect':
                    # Check if collected item matches target
                    item_vnum = str(event_data.get('item_vnum', ''))
                    item_name = event_data.get('item_name', '').lower()
                    target_name = obj.target.lower()
                    if obj.target == item_vnum or (item_name and target_name in item_name):
                        obj.current += 1
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

                elif obj.type == 'talk' and event_type == 'talk':
                    npc_vnum = str(event_data.get('npc_vnum', ''))
                    npc_name = event_data.get('npc_name', '').lower()
                    target_name = obj.target.lower()
                    if obj.target == npc_vnum or (npc_name and target_name in npc_name):
                        obj.current += 1
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

                elif obj.type in ('visit', 'explore') and event_type in ('visit', 'explore'):
                    room_vnum = str(event_data.get('room_vnum', ''))
                    if obj.target == room_vnum:
                        obj.current = max(obj.current, 1)
                        obj.check_progress()

                        c = player.config.COLORS
                        await player.send(f"{c['yellow']}Quest Progress: {obj.description} ({obj.current}/{obj.required}){c['reset']}")

                        if obj.completed:
                            await player.send(f"{c['bright_green']}Objective complete!{c['reset']}")

                elif obj.type == 'command' and event_type == 'command':
                    # Check if command matches target
                    cmd = event_data.get('command', '').lower()
                    target = obj.target.lower()
                    # Match if command starts with target (e.g., 'score' matches 'score', 'eat' matches 'eat bread')
                    if cmd == target or cmd.startswith(target):
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
            await player.gain_exp(quest.rewards['exp'], source='quest')
            await player.send(f"{c['bright_yellow']}You gain {quest.rewards['exp']} experience!{c['reset']}")

        if quest.rewards.get('gold'):
            player.gold += quest.rewards['gold']
            await player.send(f"{c['yellow']}You receive {quest.rewards['gold']} gold!{c['reset']}")

        if quest.rewards.get('items'):
            await player.send(f"{c['bright_cyan']}You receive special items!{c['reset']}")
            # Create and give items to player
            for item_vnum in quest.rewards['items']:
                try:
                    item = player.world.create_object(item_vnum)
                    if item:
                        if not hasattr(player, 'inventory'):
                            player.inventory = []
                        player.inventory.append(item)
                        await player.send(f"{c['cyan']}  → {item.short_desc}{c['reset']}")
                except Exception as e:
                    import logging
                    logging.getLogger('RealmsMUD.Quests').warning(f"Failed to give quest item {item_vnum}: {e}")

        # Quest completion bonus XP
        try:
            bonus = int(player.exp_to_level() * player.config.QUEST_XP_BONUS_PERCENT)
            if bonus > 0:
                await player.gain_exp(bonus, source='quest')
                await player.send(f"{c['bright_green']}Quest bonus: {bonus} XP!{c['reset']}")
        except Exception:
            pass

        # Reputation rewards
        if quest.rewards.get('reputation'):
            try:
                from factions import FactionManager
                await FactionManager.apply_reputation_changes(player, quest.rewards['reputation'], reason='Quest completion')
            except Exception:
                pass

        # Move quest to completed
        if not hasattr(player, 'quests_completed'):
            player.quests_completed = []
        player.quests_completed.append(quest_id)
        player.active_quests.remove(quest)

        QuestManager.advance_chain_from_quest(player, quest_id)

        try:
            from achievements import AchievementManager
            await AchievementManager.check_quest_complete(player, quest_id)
        except Exception:
            pass
        
        # Journal entry for completed quest
        try:
            from journal import JournalManager
            quest_desc = quest.description or f"Completed the quest: {quest.name}"
            await JournalManager.record_quest(
                player, quest_id, quest.name, quest_desc
            )
        except Exception:
            pass

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

            # Check chain availability
            if not QuestManager.is_chain_quest_available(player, quest_def):
                continue

            # Check level requirements
            if player.level < quest_def.get('level_min', 1):
                continue
            if player.level > quest_def.get('level_max', 50):
                continue

            # Check faction reputation requirements
            min_rep = quest_def.get('min_reputation')
            if min_rep:
                try:
                    from factions import FactionManager
                    ok = True
                    for faction_key, required in min_rep.items():
                        key = FactionManager.normalize_key(faction_key)
                        if not key:
                            continue
                        if FactionManager.get_reputation(player, key) < required:
                            ok = False
                            break
                    if not ok:
                        continue
                except Exception:
                    pass

            available.append(quest_id)

        return available

    @staticmethod
    async def start_tutorial(player: 'Player'):
        """
        Start the tutorial quest chain for a new player.
        Called automatically when a new character enters the game.
        """
        # Check if player has already started or completed the tutorial
        if hasattr(player, 'quests_completed') and 'tutorial_1_awakening' in player.quests_completed:
            return  # Already completed first tutorial
        
        if QuestManager.has_active_quest(player, 'tutorial_1_awakening'):
            return  # Already has tutorial active
        
        # Check if any tutorial quest is active
        tutorial_quests = [q for q in getattr(player, 'active_quests', []) if q.quest_id.startswith('tutorial_')]
        if tutorial_quests:
            return  # Already on a tutorial quest
        
        # Start the first tutorial quest
        c = player.config.COLORS
        await player.send(f"\r\n{c['bright_cyan']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}           WELCOME, NEW ADVENTURER!                           {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════════╝{c['reset']}")
        await player.send(f"\r\n{c['white']}Sage Aldric at the Temple can teach you the ways of the Realms.")
        await player.send(f"He is waiting for you in the Temple to the north.{c['reset']}\r\n")
        
        # Auto-accept the first tutorial quest
        await QuestManager.accept_quest(player, 'tutorial_1_awakening')

    @staticmethod
    async def check_tutorial_progress(player: 'Player', command: str):
        """
        Track command usage for tutorial quest objectives.
        Called from command handler after each command.
        """
        if not hasattr(player, 'active_quests'):
            return
        
        # Check for command-type objectives
        await QuestManager.check_quest_progress(player, 'command', {'command': command.lower()})

    @staticmethod
    async def auto_complete_tutorial_quest(player: 'Player', quest: ActiveQuest):
        """
        Auto-complete a tutorial quest when all objectives are done.
        Tutorial quests don't require returning to the quest giver.
        """
        if not quest.quest_id.startswith('tutorial_'):
            return False
        
        if not quest.is_complete():
            return False
        
        # Auto-complete
        c = player.config.COLORS
        await player.send(f"\r\n{c['bright_green']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_green']}║ TUTORIAL COMPLETE: {quest.name:<41}║{c['reset']}")
        await player.send(f"{c['bright_green']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")
        
        # Grant rewards
        if quest.rewards.get('exp'):
            await player.gain_exp(quest.rewards['exp'], source='tutorial')
            await player.send(f"{c['bright_yellow']}You gain {quest.rewards['exp']} experience!{c['reset']}")
        
        if quest.rewards.get('gold'):
            player.gold += quest.rewards['gold']
            await player.send(f"{c['yellow']}You receive {quest.rewards['gold']} gold!{c['reset']}")
        
        if quest.rewards.get('practices'):
            player.practices += quest.rewards['practices']
            await player.send(f"{c['bright_cyan']}You receive {quest.rewards['practices']} practice sessions!{c['reset']}")
        
        if quest.rewards.get('title'):
            player.title = quest.rewards['title']
            await player.send(f"{c['bright_magenta']}You have earned the title: {quest.rewards['title']}!{c['reset']}")
        
        # Move to completed
        if not hasattr(player, 'quests_completed'):
            player.quests_completed = []
        player.quests_completed.append(quest.quest_id)
        player.active_quests.remove(quest)
        
        # Start next tutorial quest if exists
        quest_def = QUEST_DEFINITIONS.get(quest.quest_id, {})
        next_quest = quest_def.get('next_quest')
        if next_quest and next_quest in QUEST_DEFINITIONS:
            await player.send(f"\r\n{c['cyan']}New objective available...{c['reset']}\r\n")
            await QuestManager.accept_quest(player, next_quest)
        else:
            # Tutorial complete!
            await player.send(f"\r\n{c['bright_yellow']}╔══════════════════════════════════════════════════════════════╗{c['reset']}")
            await player.send(f"{c['bright_yellow']}║     CONGRATULATIONS! You have completed the tutorial!        ║{c['reset']}")
            await player.send(f"{c['bright_yellow']}║                                                              ║{c['reset']}")
            await player.send(f"{c['bright_yellow']}║  You are now ready to explore the world on your own.        ║{c['reset']}")
            await player.send(f"{c['bright_yellow']}║  Type 'help' for commands, 'quests' for more adventures!    ║{c['reset']}")
            await player.send(f"{c['bright_yellow']}╚══════════════════════════════════════════════════════════════╝{c['reset']}\r\n")
        
        return True
