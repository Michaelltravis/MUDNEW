"""
RealmsMUD Collection System
===========================
Tracks collectible sets and rewards.
"""

import logging
from typing import Dict, List

logger = logging.getLogger('RealmsMUD.Collections')


COLLECTION_SETS: Dict[str, Dict] = {
    'Ancient Artifacts': {
        'type': 'items',
        'items': [9200, 9201, 9202, 9203],
        'reward': {'gold': 800, 'exp': 300, 'title': 'the Relic-Bearer'},
        'description': 'Recovered relics of the old empires.'
    },
    'Rare Gems': {
        'type': 'items',
        'items': [9300, 9301, 9302, 9303],
        'reward': {'gold': 600, 'exp': 250},
        'description': 'A curated collection of rare gemstones.'
    },
    'Monster Trophies': {
        'type': 'trophies',
        'trophies': ['boss_goblin_king', 'boss_necromancer', 'boss_spider_queen', 'boss_ancient_dragon'],
        'reward': {'gold': 900, 'exp': 350, 'title': 'the Vanquisher'},
        'description': 'Proof of victory over the realm’s greatest threats.'
    },
    'Zone Completion Badges': {
        'type': 'badges',
        'badges': ['cartographer_midgaard', 'cartographer_haondor', 'cartographer_sewers', 'cartographer_desert'],
        'reward': {'gold': 700, 'exp': 300},
        'description': 'Badges earned for fully exploring key regions.'
    }
}


class CollectionManager:
    """Utility helpers for collection tracking."""

    @staticmethod
    def _ensure_player_fields(player):
        if not hasattr(player, 'collection_progress') or player.collection_progress is None:
            player.collection_progress = {name: [] for name in COLLECTION_SETS}
        else:
            for name in COLLECTION_SETS:
                player.collection_progress.setdefault(name, [])
        if not hasattr(player, 'collections_completed') or player.collections_completed is None:
            player.collections_completed = []

    @staticmethod
    async def record_item(player, item):
        """Record an item towards collection sets."""
        CollectionManager._ensure_player_fields(player)
        if not hasattr(item, 'vnum'):
            return

        for set_name, data in COLLECTION_SETS.items():
            if data.get('type') != 'items':
                continue
            if item.vnum in data.get('items', []):
                await CollectionManager._mark_progress(player, set_name, str(item.vnum))

    @staticmethod
    async def record_trophy(player, trophy_id: str):
        CollectionManager._ensure_player_fields(player)
        for set_name, data in COLLECTION_SETS.items():
            if data.get('type') != 'trophies':
                continue
            if trophy_id in data.get('trophies', []):
                await CollectionManager._mark_progress(player, set_name, trophy_id)

    @staticmethod
    async def record_badge(player, badge_id: str):
        CollectionManager._ensure_player_fields(player)
        for set_name, data in COLLECTION_SETS.items():
            if data.get('type') != 'badges':
                continue
            if badge_id in data.get('badges', []):
                await CollectionManager._mark_progress(player, set_name, badge_id)

    @staticmethod
    async def _mark_progress(player, set_name: str, token: str):
        progress = player.collection_progress.get(set_name, [])
        if token in progress:
            return
        progress.append(token)
        player.collection_progress[set_name] = progress
        await CollectionManager._check_complete(player, set_name)

    @staticmethod
    async def _check_complete(player, set_name: str):
        data = COLLECTION_SETS.get(set_name)
        if not data:
            return

        completed = set(player.collections_completed)
        if set_name in completed:
            return

        required = []
        if data.get('type') == 'items':
            required = [str(v) for v in data.get('items', [])]
        elif data.get('type') == 'trophies':
            required = list(data.get('trophies', []))
        elif data.get('type') == 'badges':
            required = list(data.get('badges', []))

        if set(required).issubset(set(player.collection_progress.get(set_name, []))):
            completed.add(set_name)
            player.collections_completed = list(completed)
            await CollectionManager._grant_reward(player, set_name, data.get('reward', {}))

    @staticmethod
    async def _grant_reward(player, set_name: str, reward: dict):
        if not reward:
            return
        c = player.config.COLORS
        await player.send(f"{c['bright_green']}Collection complete: {set_name}!{c['reset']}")

        exp = reward.get('exp', 0)
        gold = reward.get('gold', 0)
        title = reward.get('title')

        if exp:
            player.exp += exp
        if gold:
            player.gold += gold
        if title:
            player.title = title

        parts = []
        if exp:
            parts.append(f"{exp} exp")
        if gold:
            parts.append(f"{gold} gold")
        if title:
            parts.append(f"title: {title}")

        if parts:
            await player.send(f"{c['bright_cyan']}Reward:{c['reset']} {' and '.join(parts)}")

    @staticmethod
    def get_display_case_lines(player) -> List[str]:
        CollectionManager._ensure_player_fields(player)
        c = player.config.COLORS
        lines = [f"{c['bright_magenta']}A polished display case showcases your collections:{c['reset']}"]
        completed = set(player.collections_completed)
        if not completed:
            lines.append(f"{c['yellow']}  (It is currently empty.){c['reset']}")
            return lines
        for set_name in COLLECTION_SETS:
            if set_name in completed:
                lines.append(f"{c['bright_green']}  ✔ {set_name}{c['reset']}")
        return lines

    @staticmethod
    def render_collections(player) -> List[str]:
        CollectionManager._ensure_player_fields(player)
        c = player.config.COLORS
        lines = [f"{c['bright_yellow']}Collections:{c['reset']}"]
        for set_name, data in COLLECTION_SETS.items():
            required = []
            if data.get('type') == 'items':
                required = [str(v) for v in data.get('items', [])]
            elif data.get('type') == 'trophies':
                required = list(data.get('trophies', []))
            elif data.get('type') == 'badges':
                required = list(data.get('badges', []))

            progress = set(player.collection_progress.get(set_name, []))
            count = len(progress.intersection(set(required)))
            total = len(required)
            status = 'Complete' if set_name in player.collections_completed else f"{count}/{total}"
            lines.append(f"{c['cyan']}- {set_name}:{c['reset']} {status}")
            desc = data.get('description')
            if desc:
                lines.append(f"  {c['white']}{desc}{c['reset']}")
        return lines
