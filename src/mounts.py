"""
Misthollow Mount System
======================
Handles buyable and tameable mounts that boost travel speed.
"""

import random
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger('Misthollow.Mounts')


@dataclass
class Mount:
    name: str
    key: str
    speed_bonus: float
    description: str
    loyalty: int = 100          # 0-100, drops over time without feeding
    combat_ok: bool = False     # Can stay mounted in combat
    damroll_bonus: int = 0      # Passive damroll while mounted in combat
    fire_aura: bool = False     # Deals fire damage to attackers
    can_fly: bool = False       # Can traverse impassable/flying terrain
    never_tires: bool = False   # Doesn't consume extra move when hungry
    max_loyalty: int = 100

    def loyalty_speed(self) -> float:
        """Speed bonus scaled by loyalty (min 50% effectiveness at 0 loyalty)."""
        scale = 0.5 + 0.5 * (self.loyalty / self.max_loyalty)
        return self.speed_bonus * scale

    def feed(self) -> str:
        """Feed the mount, restoring loyalty."""
        old = self.loyalty
        self.loyalty = min(self.max_loyalty, self.loyalty + 25)
        gained = self.loyalty - old
        if gained > 0:
            return f"You feed your {self.name}. It nuzzles you gratefully. (+{gained} loyalty)"
        return f"Your {self.name} isn't hungry right now."

    def tick_loyalty(self):
        """Called periodically to decay loyalty."""
        if not self.never_tires:
            self.loyalty = max(0, self.loyalty - 1)

    def to_dict(self) -> dict:
        return {
            'key': self.key,
            'name': self.name,
            'loyalty': self.loyalty,
        }


# ─── Mount Templates ─────────────────────────────────────────────

MOUNT_TEMPLATES: Dict[str, Dict] = {
    'horse': {
        'key': 'horse',
        'name': 'a sturdy riding horse',
        'cost': 2000,
        'speed_bonus': 0.5,
        'description': 'A reliable riding horse, perfect for long journeys.',
        'purchasable': True,
        'tameable': True,
        'tame_difficulty': 30,
        'combat_ok': False,
        'damroll_bonus': 0,
        'fire_aura': False,
        'can_fly': False,
        'never_tires': False,
    },
    'warhorse': {
        'key': 'warhorse',
        'name': 'a powerful war horse',
        'cost': 5000,
        'speed_bonus': 0.5,
        'description': 'A trained war horse. Stays mounted during combat and grants +2 damroll.',
        'purchasable': True,
        'tameable': False,
        'tame_difficulty': 50,
        'combat_ok': True,
        'damroll_bonus': 2,
        'fire_aura': False,
        'can_fly': False,
        'never_tires': False,
    },
    'nightmare': {
        'key': 'nightmare',
        'name': 'a nightmare steed',
        'cost': 0,
        'speed_bonus': 0.75,
        'description': 'A hellish fire horse wreathed in flame. +75% speed, fire damage aura.',
        'purchasable': False,
        'faction_required': 'dark_brotherhood',
        'faction_level': 'revered',
        'tameable': False,
        'tame_difficulty': 80,
        'combat_ok': True,
        'damroll_bonus': 0,
        'fire_aura': True,
        'can_fly': False,
        'never_tires': False,
    },
    'griffin': {
        'key': 'griffin',
        'name': 'a majestic griffin',
        'cost': 0,
        'speed_bonus': 1.0,
        'description': 'A fearsome griffin. +100% speed and can fly over impassable terrain.',
        'purchasable': False,
        'drop_zone': 'Shadowspire',
        'tameable': False,
        'tame_difficulty': 90,
        'combat_ok': False,
        'damroll_bonus': 0,
        'fire_aura': False,
        'can_fly': True,
        'never_tires': False,
    },
    'clockwork_steed': {
        'key': 'clockwork_steed',
        'name': 'a clockwork steed',
        'cost': 0,
        'speed_bonus': 0.75,
        'description': 'A mechanical steed of brass and gears. +75% speed, never tires.',
        'purchasable': False,
        'drop_zone': 'Clockwork Foundry',
        'tameable': False,
        'tame_difficulty': 85,
        'combat_ok': False,
        'damroll_bonus': 0,
        'fire_aura': False,
        'can_fly': False,
        'never_tires': True,
    },
    # Legacy mounts kept for compatibility
    'donkey': {
        'key': 'donkey',
        'name': 'a reliable donkey',
        'cost': 600,
        'speed_bonus': 0.35,
        'description': 'A reliable donkey.',
        'purchasable': True,
        'tameable': True,
        'tame_difficulty': 20,
        'combat_ok': False,
        'damroll_bonus': 0,
        'fire_aura': False,
        'can_fly': False,
        'never_tires': False,
    },
    'pony': {
        'key': 'pony',
        'name': 'a small pony',
        'cost': 900,
        'speed_bonus': 0.4,
        'description': 'A small but spirited pony.',
        'purchasable': True,
        'tameable': True,
        'tame_difficulty': 25,
        'combat_ok': False,
        'damroll_bonus': 0,
        'fire_aura': False,
        'can_fly': False,
        'never_tires': False,
    },
}


class MountManager:
    """Manages player mounts."""

    @staticmethod
    def get_mount_template(name: str) -> Optional[Dict]:
        return MOUNT_TEMPLATES.get(name.lower())

    @staticmethod
    def list_purchasable_mounts() -> Dict[str, Dict]:
        return {k: v for k, v in MOUNT_TEMPLATES.items() if v.get('purchasable')}

    @staticmethod
    def list_mounts() -> Dict[str, Dict]:
        return MOUNT_TEMPLATES

    @staticmethod
    def create_mount(template_name: str, loyalty: int = 100) -> Optional[Mount]:
        template = MountManager.get_mount_template(template_name)
        if not template:
            return None
        return Mount(
            name=template['name'],
            key=template['key'],
            speed_bonus=template['speed_bonus'],
            description=template['description'],
            loyalty=loyalty,
            combat_ok=template.get('combat_ok', False),
            damroll_bonus=template.get('damroll_bonus', 0),
            fire_aura=template.get('fire_aura', False),
            can_fly=template.get('can_fly', False),
            never_tires=template.get('never_tires', False),
        )

    @staticmethod
    def load_mount(data: dict) -> Optional[Mount]:
        """Load a mount from saved dict."""
        if not data:
            return None
        key = data.get('key', '')
        mount = MountManager.create_mount(key, loyalty=data.get('loyalty', 100))
        return mount

    @staticmethod
    async def buy_mount(player, template_name: str) -> bool:
        """Buy a mount from a stable."""
        template = MountManager.get_mount_template(template_name)
        if not template:
            return False

        if not template.get('purchasable'):
            c = player.config.COLORS
            await player.send(f"{c['red']}That mount cannot be purchased.{c['reset']}")
            return False

        cost = template['cost']
        if player.gold < cost:
            c = player.config.COLORS
            await player.send(f"{c['red']}You need {cost} gold to buy a {template['name']}. You have {player.gold}.{c['reset']}")
            return False

        # Check if already owned
        for m in player.owned_mounts:
            mkey = m if isinstance(m, str) else m.get('key', '')
            if mkey == template_name:
                c = player.config.COLORS
                await player.send(f"{c['yellow']}You already own {template['name']}.{c['reset']}")
                return False

        player.gold -= cost
        player.owned_mounts.append({'key': template_name, 'loyalty': 100})
        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You purchase {template['name']} for {cost} gold!{c['reset']}")
        logger.info(f"{player.name} bought mount {template_name}")
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

        for m in player.owned_mounts:
            mkey = m if isinstance(m, str) else m.get('key', '')
            if mkey == template['key']:
                c = player.config.COLORS
                await player.send(f"{c['yellow']}You already own {template['name']}.{c['reset']}")
                return False

        tame_skill = 50 + (player.cha - 10) * 5
        difficulty = template.get('tame_difficulty', 25)
        roll = random.randint(1, 100)

        if roll + tame_skill < difficulty * 4:
            c = player.config.COLORS
            await player.send(f"{c['red']}You fail to tame the {template['name']}!{c['reset']}")
            return False

        player.owned_mounts.append({'key': template['key'], 'loyalty': 100})
        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You tame {template['name']}!{c['reset']}")

        if target.room and target in target.room.characters:
            target.room.characters.remove(target)
        if hasattr(player, 'world') and hasattr(player.world, 'npcs') and target in player.world.npcs:
            player.world.npcs.remove(target)

        logger.info(f"{player.name} tamed mount {template['key']}")
        return True

    @staticmethod
    def get_owned_mount_data(player, key: str) -> Optional[dict]:
        """Find owned mount data by key."""
        for m in player.owned_mounts:
            if isinstance(m, str):
                if m == key:
                    return {'key': m, 'loyalty': 100}
            elif isinstance(m, dict) and m.get('key') == key:
                return m
        return None

    @staticmethod
    def should_auto_dismount(player) -> bool:
        """Check if player should be auto-dismounted when entering combat."""
        if not player.mount:
            return False
        return not player.mount.combat_ok
