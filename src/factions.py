"""
Faction Reputation System
========================
Defines factions, reputation levels, opposing factions, and helpers for
tracking player standing with each faction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger('RealmsMUD.Factions')


REPUTATION_LEVELS = [
    'Hated',
    'Hostile',
    'Unfriendly',
    'Neutral',
    'Friendly',
    'Honored',
    'Exalted',
]

# Thresholds are inclusive (score >= threshold -> that level)
REPUTATION_THRESHOLDS: List[Tuple[str, int]] = [
    ('Hated', -600),
    ('Hostile', -300),
    ('Unfriendly', -1),
    ('Neutral', 0),
    ('Friendly', 300),
    ('Honored', 600),
    ('Exalted', 900),
]

OPPOSING_MULTIPLIER = 0.5

# Price modifiers by reputation level (affects shop prices)
PRICE_MODIFIERS = {
    'Hated': 1.5,
    'Hostile': 1.3,
    'Unfriendly': 1.15,
    'Neutral': 1.0,
    'Friendly': 0.9,
    'Honored': 0.8,
    'Exalted': 0.7,
}


@dataclass
class Faction:
    key: str
    name: str
    description: str
    enemies: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    quest_line: List[str] = field(default_factory=list)
    exalted_rewards: Dict[str, List[str]] = field(default_factory=dict)


FACTIONS: Dict[str, Faction] = {
    'midgaard': Faction(
        key='midgaard',
        name='Midgaard',
        description='The human city-state of Midgaard, bastion of law and order. Reputation gained by helping city NPCs and completing city quests. Lost by attacking citizens or aiding the Thieves Guild.',
        enemies=['thieves_guild', 'orc_horde'],
        allies=['mages_guild', 'holy_order'],
        quest_line=['midgaard_guard_duty', 'midgaard_city_watch', 'midgaard_honor_guard'],
        exalted_rewards={
            'titles': ['the Shield of Midgaard'],
            'mounts': ['warhorse'],
            'items': [9010],
        },
    ),
    'elves': Faction(
        key='elves',
        name='Elven Court',
        description='The Silversong elves, ancient guardians of forest and magic. Reputation gained by helping the forest and completing elven quests. Lost by harming forest creatures needlessly.',
        enemies=['drow_conclave', 'orc_horde'],
        allies=['mages_guild', 'holy_order'],
        quest_line=['elves_forest_wardens', 'elves_sacred_grove', 'elves_starlight_pact'],
        exalted_rewards={
            'titles': ['the Silverleaf'],
            'mounts': ['moonstag'],
            'items': [9011],
        },
    ),
    'dwarves': Faction(
        key='dwarves',
        name='Dwarven Kingdom',
        description='The stout-hearted dwarves of the Moria mountain halls. Reputation gained through Moria quests and trade route defense. Lost by theft or betrayal.',
        enemies=['orc_horde'],
        allies=['midgaard', 'holy_order'],
        quest_line=['dwarves_iron_oath', 'dwarves_deep_delves', 'dwarves_rune_forge'],
        exalted_rewards={
            'titles': ['the Forgefriend'],
            'mounts': ['stoneboar'],
            'items': [9012],
        },
    ),
    'thieves_guild': Faction(
        key='thieves_guild',
        name='Thieves Guild',
        description='A secretive underground guild of rogues, smugglers, and cutpurses. Reputation gained by stealing, sewer quests, and smuggling runs. Lost by cooperating with city guards.',
        enemies=['midgaard', 'holy_order'],
        allies=['drow_conclave'],
        quest_line=['thieves_guild_cutpurse', 'thieves_guild_silent_blade', 'thieves_guild_shadow_king'],
        exalted_rewards={
            'titles': ['the Whisper'],
            'mounts': ['shadowpanther'],
            'items': [9013],
        },
    ),
    'mages_guild': Faction(
        key='mages_guild',
        name='Mages Circle',
        description='The arcane order of the High Tower of Magic. Reputation gained by magical quests, recovering lost scrolls, and arcane research. Neutral to most political conflicts.',
        enemies=[],
        allies=['midgaard', 'elves'],
        quest_line=['mages_guild_apprentice', 'mages_guild_archives', 'mages_guild_ascension'],
        exalted_rewards={
            'titles': ['the Arcanist'],
            'mounts': ['manabound_gryphon'],
            'items': [9014],
        },
    ),
    'drow_conclave': Faction(
        key='drow_conclave',
        name='Drow Conclave',
        description='The dark elves of the underground Drow City. Hostile to surface dwellers by default. Reputation gained by completing drow quests and proving your worth. Lost by killing drow.',
        enemies=['elves', 'holy_order', 'midgaard'],
        allies=['thieves_guild'],
        quest_line=['drow_shadow_errand', 'drow_web_of_lies', 'drow_matrons_favor'],
        exalted_rewards={
            'titles': ['the Spider-Touched'],
            'mounts': ['riding_spider'],
            'items': [9015],
        },
    ),
    'holy_order': Faction(
        key='holy_order',
        name='Holy Order',
        description='The Temple and Paladin faction devoted to purging evil. Reputation gained by destroying undead, healing the sick, and completing temple quests. Lost by necromancy or aiding evil.',
        enemies=['drow_conclave', 'dragon_cult'],
        allies=['midgaard', 'elves', 'dwarves'],
        quest_line=['holy_order_vigil', 'holy_order_purge', 'holy_order_crusade'],
        exalted_rewards={
            'titles': ['the Lightbringer'],
            'mounts': ['celestial_charger'],
            'items': [9016],
        },
    ),
    'dragon_cult': Faction(
        key='dragon_cult',
        name='Dragon Cult',
        description="A mysterious cult dwelling in the Dragon's Domain. Hostile to most. Reputation gained through a secret quest chain and NOT killing dragons. Lost by slaying dragons.",
        enemies=['holy_order', 'midgaard'],
        allies=[],
        quest_line=['dragon_cult_offering', 'dragon_cult_trial', 'dragon_cult_ascendance'],
        exalted_rewards={
            'titles': ['the Dragonsworn'],
            'mounts': ['drake_whelp'],
            'items': [9017],
        },
    ),
    'orc_horde': Faction(
        key='orc_horde',
        name='Orc Horde',
        description='The savage orc tribes of the Orc Enclave. Hostile to all civilized races. Reputation can only be gained through rare special means — defeating their champions in honorable combat or completing brutal trials.',
        enemies=['midgaard', 'elves', 'dwarves'],
        allies=[],
        quest_line=['orc_horde_bloodrite', 'orc_horde_warpath', 'orc_horde_warchief'],
        exalted_rewards={
            'titles': ['the Bloodsworn'],
            'mounts': ['dire_warg'],
            'items': [9018],
        },
    ),
}

# Starting reputation for new players
DEFAULT_STARTING_REPUTATION = {
    'midgaard': 300,        # Friendly
    'elves': 0,             # Neutral
    'dwarves': 0,           # Neutral
    'thieves_guild': -600,  # Hidden (Hated until discovered)
    'mages_guild': 0,       # Neutral
    'drow_conclave': -300,  # Hostile
    'holy_order': 300,      # Friendly
    'dragon_cult': -300,    # Hostile
    'orc_horde': -300,      # Hostile
}

# Actions that grant/lose reputation (referenced by game systems)
FACTION_REP_ACTIONS = {
    'kill_undead': {'holy_order': 5},
    'heal_npc': {'holy_order': 3, 'midgaard': 1},
    'steal_success': {'thieves_guild': 5, 'midgaard': -3},
    'kill_dragon': {'dragon_cult': -50},
    'complete_sewer_quest': {'thieves_guild': 15},
    'kill_city_guard': {'midgaard': -20, 'thieves_guild': 5},
    'kill_orc': {'orc_horde': -5, 'midgaard': 2, 'dwarves': 2},
    'kill_drow': {'drow_conclave': -10, 'elves': 3},
    'kill_elf': {'elves': -15, 'drow_conclave': 3},
    'kill_goblin': {'midgaard': 1, 'dwarves': 1},
}


class FactionManager:
    """Utility methods for faction reputation."""

    @staticmethod
    def normalize_key(name: str) -> Optional[str]:
        if not name:
            return None
        name = name.strip().lower().replace(' ', '_')
        if name in FACTIONS:
            return name
        # Try partial match on faction names
        for key, faction in FACTIONS.items():
            if name == faction.name.lower().replace(' ', '_'):
                return key
            if name in faction.name.lower():
                return key
        return None

    @staticmethod
    def ensure_player_reputation(player):
        if not hasattr(player, 'reputation') or not isinstance(player.reputation, dict):
            player.reputation = {}
        for key in FACTIONS.keys():
            player.reputation.setdefault(key, DEFAULT_STARTING_REPUTATION.get(key, 0))

    @staticmethod
    def get_reputation(player, faction_key: str) -> int:
        FactionManager.ensure_player_reputation(player)
        return player.reputation.get(faction_key, 0)

    @staticmethod
    def set_reputation(player, faction_key: str, value: int):
        FactionManager.ensure_player_reputation(player)
        player.reputation[faction_key] = value

    @staticmethod
    def get_level_for_score(score: int) -> str:
        # Find highest threshold not exceeding score
        current = 'Neutral'
        for level, threshold in REPUTATION_THRESHOLDS:
            if score >= threshold:
                current = level
        return current

    @staticmethod
    def get_threshold_for_level(level_name: str) -> int:
        for level, threshold in REPUTATION_THRESHOLDS:
            if level.lower() == level_name.lower():
                return threshold
        return 0

    @staticmethod
    def get_level(player, faction_key: str) -> str:
        score = FactionManager.get_reputation(player, faction_key)
        return FactionManager.get_level_for_score(score)

    @staticmethod
    def is_hostile(player, faction_key: str) -> bool:
        level = FactionManager.get_level(player, faction_key)
        return level in ('Hated', 'Hostile')

    @staticmethod
    def get_price_modifier(player, faction_key: Optional[str]) -> float:
        if not faction_key or faction_key not in FACTIONS:
            return 1.0
        level = FactionManager.get_level(player, faction_key)
        return PRICE_MODIFIERS.get(level, 1.0)

    @staticmethod
    async def apply_reputation_change(player, faction_key: str, amount: int, reason: str = ""):
        if faction_key not in FACTIONS:
            return

        FactionManager.ensure_player_reputation(player)

        before = FactionManager.get_reputation(player, faction_key)
        after = before + amount
        FactionManager.set_reputation(player, faction_key, after)

        # Apply opposing faction penalties
        faction = FACTIONS[faction_key]
        for enemy_key in faction.enemies:
            if enemy_key in FACTIONS:
                enemy_before = FactionManager.get_reputation(player, enemy_key)
                enemy_after = enemy_before - int(abs(amount) * OPPOSING_MULTIPLIER)
                FactionManager.set_reputation(player, enemy_key, enemy_after)

        # Notify player if possible
        if hasattr(player, 'send'):
            level_before = FactionManager.get_level_for_score(before)
            level_after = FactionManager.get_level_for_score(after)
            sign = '+' if amount >= 0 else ''
            msg = f"Reputation with {faction.name}: {sign}{amount} ({level_after})"
            if reason:
                msg += f" - {reason}"
            await player.send(msg)

            if level_before != level_after:
                await player.send(f"Your standing with {faction.name} is now {level_after}.")

        # Check for exalted rewards
        await FactionManager._check_exalted_rewards(player, faction_key)

    @staticmethod
    async def apply_reputation_changes(player, changes: Dict[str, int], reason: str = ""):
        for key, amount in changes.items():
            await FactionManager.apply_reputation_change(player, key, amount, reason=reason)

    @staticmethod
    async def _check_exalted_rewards(player, faction_key: str):
        if faction_key not in FACTIONS:
            return
        faction = FACTIONS[faction_key]
        level = FactionManager.get_level(player, faction_key)
        if level != 'Exalted':
            return

        # Track rewards granted to avoid duplicates
        if not hasattr(player, 'faction_rewards'):
            player.faction_rewards = {}
        if player.faction_rewards.get(faction_key, False):
            return

        rewards = faction.exalted_rewards or {}
        titles = rewards.get('titles', [])
        mounts = rewards.get('mounts', [])
        items = rewards.get('items', [])

        # Grant title (use first title)
        if titles:
            player.title = titles[0]

        # Grant mounts
        if mounts:
            if not hasattr(player, 'owned_mounts'):
                player.owned_mounts = []
            for mount in mounts:
                if mount not in player.owned_mounts:
                    player.owned_mounts.append(mount)

        # Grant items if possible
        if items:
            try:
                from objects import create_preset_object, create_object
                for item_key in items:
                    item = create_preset_object(item_key) or create_object(item_key, player.world)
                    if item:
                        player.inventory.append(item)
            except Exception:
                pass

        if hasattr(player, 'send'):
            await player.send(f"You have earned Exalted rewards from {faction.name}!")

        player.faction_rewards[faction_key] = True

    @staticmethod
    def format_reputation_summary(player) -> List[str]:
        FactionManager.ensure_player_reputation(player)
        lines = []
        for key, faction in FACTIONS.items():
            score = FactionManager.get_reputation(player, key)
            level = FactionManager.get_level_for_score(score)
            lines.append(f"{faction.name}: {level} ({score})")
        return lines

    @staticmethod
    def format_faction_detail(player, faction_key: str) -> List[str]:
        if faction_key not in FACTIONS:
            return ["Unknown faction."]
        faction = FACTIONS[faction_key]
        score = FactionManager.get_reputation(player, faction_key)
        level = FactionManager.get_level_for_score(score)
        lines = [
            f"{faction.name} - {faction.description}",
            f"Standing: {level} ({score})",
        ]
        if faction.enemies:
            enemies = ', '.join(FACTIONS[e].name for e in faction.enemies if e in FACTIONS)
            lines.append(f"Opposes: {enemies}")
        if faction.allies:
            allies = ', '.join(FACTIONS[a].name for a in faction.allies if a in FACTIONS)
            lines.append(f"Allies: {allies}")
        if faction.quest_line:
            lines.append("Quest line: " + ", ".join(faction.quest_line))
        if faction.exalted_rewards:
            rewards = faction.exalted_rewards
            titles = ', '.join(rewards.get('titles', []))
            mounts = ', '.join(rewards.get('mounts', []))
            items = ', '.join(rewards.get('items', []))
            if titles:
                lines.append(f"Exalted Titles: {titles}")
            if mounts:
                lines.append(f"Exalted Mounts: {mounts}")
            if items:
                lines.append(f"Exalted Gear: {items}")
        return lines
