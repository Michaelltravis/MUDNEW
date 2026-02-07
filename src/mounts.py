"""
RealmsMUD Mount System
======================
Handles buyable and tameable mounts that boost travel speed.
"""

import random
import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger('RealmsMUD.Mounts')


@dataclass
class Mount:
    name: str
    speed_bonus: float
    description: str


MOUNT_TEMPLATES: Dict[str, Dict] = {
    'horse': {
        'name': 'horse',
        'cost': 1200,
        'speed_bonus': 0.5,  # 50% less move cost
        'description': 'A sturdy riding horse.',
        'tameable': True,
        'tame_difficulty': 30,
    },
    'donkey': {
        'name': 'donkey',
        'cost': 600,
        'speed_bonus': 0.35,
        'description': 'A reliable donkey.',
        'tameable': True,
        'tame_difficulty': 20,
    },
    'pony': {
        'name': 'pony',
        'cost': 900,
        'speed_bonus': 0.4,
        'description': 'A small but spirited pony.',
        'tameable': True,
        'tame_difficulty': 25,
    },
    'warhorse': {
        'name': 'warhorse',
        'cost': 2500,
        'speed_bonus': 0.6,
        'description': 'A trained warhorse with powerful build.',
        'tameable': False,
        'tame_difficulty': 50,
    },
    'moonstag': {
        'name': 'moonstag',
        'cost': 0,
        'speed_bonus': 0.65,
        'description': 'A luminous stag blessed by the Elven groves.',
        'tameable': False,
        'tame_difficulty': 60,
    },
    'stoneboar': {
        'name': 'stoneboar',
        'cost': 0,
        'speed_bonus': 0.55,
        'description': 'A hardy dwarven boar bred in the mountain halls.',
        'tameable': False,
        'tame_difficulty': 55,
    },
    'shadowpanther': {
        'name': 'shadowpanther',
        'cost': 0,
        'speed_bonus': 0.7,
        'description': 'A sleek panther that moves like living shadow.',
        'tameable': False,
        'tame_difficulty': 65,
    },
    'manabound_gryphon': {
        'name': 'manabound_gryphon',
        'cost': 0,
        'speed_bonus': 0.75,
        'description': 'A gryphon bound to arcane sigils, swift as thought.',
        'tameable': False,
        'tame_difficulty': 70,
    },
}


class MountManager:
    """Manages player mounts."""

    @staticmethod
    def get_mount_template(name: str) -> Optional[Dict]:
        return MOUNT_TEMPLATES.get(name.lower())

    @staticmethod
    def list_mounts() -> Dict[str, Dict]:
        return MOUNT_TEMPLATES

    @staticmethod
    def create_mount(template_name: str) -> Optional[Mount]:
        template = MountManager.get_mount_template(template_name)
        if not template:
            return None
        return Mount(
            name=template['name'],
            speed_bonus=template['speed_bonus'],
            description=template['description']
        )

    @staticmethod
    async def buy_mount(player, template_name: str) -> bool:
        """Buy a mount from a stable."""
        template = MountManager.get_mount_template(template_name)
        if not template:
            return False

        cost = template['cost']
        if player.gold < cost:
            c = player.config.COLORS
            await player.send(f"{c['red']}You need {cost} gold to buy a {template['name']}.{c['reset']}")
            return False

        if template['name'] in player.owned_mounts:
            c = player.config.COLORS
            await player.send(f"{c['yellow']}You already own a {template['name']}.{c['reset']}")
            return False

        player.gold -= cost
        player.owned_mounts.append(template['name'])
        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You purchase a {template['name']}!{c['reset']}")
        logger.info(f"{player.name} bought mount {template['name']}")
        return True

    @staticmethod
    async def tame_mount(player, target) -> bool:
        """Attempt to tame a mount from a wild creature in the room."""
        if not target or not hasattr(target, 'name'):
            return False

        template = MountManager.get_mount_template(target.name.lower())
        if not template or not template.get('tameable', False):
            c = player.config.COLORS
            await player.send(f"{c['red']}That creature cannot be tamed as a mount.{c['reset']}")
            return False

        if template['name'] in player.owned_mounts:
            c = player.config.COLORS
            await player.send(f"{c['yellow']}You already own a {template['name']}.{c['reset']}")
            return False

        # Simple CHA-based tame roll
        tame_skill = 50 + (player.cha - 10) * 5
        difficulty = template.get('tame_difficulty', 25)
        roll = random.randint(1, 100)

        if roll + tame_skill < difficulty * 4:
            c = player.config.COLORS
            await player.send(f"{c['red']}You fail to tame the {template['name']}!{c['reset']}")
            return False

        player.owned_mounts.append(template['name'])
        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You tame a {template['name']}!{c['reset']}")

        # Remove the creature from the room (it becomes your mount)
        if target.room and target in target.room.characters:
            target.room.characters.remove(target)
        if hasattr(player.world, 'npcs') and target in player.world.npcs:
            player.world.npcs.remove(target)

        logger.info(f"{player.name} tamed mount {template['name']}")
        return True
