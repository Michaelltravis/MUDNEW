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
    travel: float = 0.3         # how much faster you travel riding it (+30%), at full loyalty

    def loyalty_speed(self) -> float:
        """Speed bonus scaled by loyalty (min 50% effectiveness at 0 loyalty)."""
        scale = 0.5 + 0.5 * (self.loyalty / self.max_loyalty)
        return self.speed_bonus * scale

    def travel_bonus(self) -> float:
        """How much faster it carries you (0.35 = +35%), less when it's neglected (half at 0)."""
        return self.travel * (0.5 + 0.5 * (self.loyalty / self.max_loyalty))

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
        'travel': 0.35,
        'name': 'a sturdy riding horse',
        'cost': 2000,
        'speed_bonus': 0.5,
        'description': 'A reliable riding horse, perfect for long journeys. +35% speed.',
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
        'travel': 0.3,
        'name': 'a powerful war horse',
        'cost': 5000,
        'speed_bonus': 0.5,
        'description': 'A trained war horse. +30% speed; stays mounted during combat and grants +2 damroll.',
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
        'travel': 0.5,
        'name': 'a nightmare steed',
        'cost': 0,
        'speed_bonus': 0.75,
        'description': 'A hellish fire horse wreathed in flame. +50% speed, fire damage aura.',
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
        'travel': 0.6,
        'name': 'a majestic griffin',
        'cost': 0,
        'speed_bonus': 1.0,
        'description': 'A fearsome griffin. +60% speed, and it flies over rough ground.',
        'purchasable': False,
        'drop_zone': 'the Roc Matriarch',
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
        'travel': 0.5,
        'name': 'a clockwork steed',
        'cost': 0,
        'speed_bonus': 0.75,
        'description': 'A mechanical steed of brass and gears. +50% speed, never tires.',
        'purchasable': False,
        'drop_zone': 'the Carillon Engine',
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
        'travel': 0.15,
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
        'travel': 0.2,
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

# the faction mounts an exalted standing gives (factions.py exalted_rewards)
MOUNT_TEMPLATES.update({
    'moonstag': {'key': 'moonstag', 'name': 'a silver moonstag', 'cost': 0, 'speed_bonus': 0.6, 'travel': 0.45,
                 'description': 'A stag of the Elven Court, pale as moonlight. +45% speed.', 'purchasable': False,
                 'faction_required': 'elves', 'tameable': False, 'tame_difficulty': 90, 'combat_ok': False,
                 'damroll_bonus': 0, 'fire_aura': False, 'can_fly': False, 'never_tires': False},
    'stoneboar': {'key': 'stoneboar', 'name': 'an armoured stoneboar', 'cost': 0, 'speed_bonus': 0.5, 'travel': 0.3,
                  'description': 'A dwarven war boar in riveted plate. +30% speed, fights with you (+1 damroll).',
                  'purchasable': False, 'faction_required': 'dwarves', 'tameable': False, 'tame_difficulty': 90,
                  'combat_ok': True, 'damroll_bonus': 1, 'fire_aura': False, 'can_fly': False, 'never_tires': False},
    'armored_warhorse': {'key': 'armored_warhorse', 'name': 'a barded warhorse of the Guard', 'cost': 0,
                         'speed_bonus': 0.5, 'travel': 0.3,
                         'description': 'A Guard destrier in barding. +30% speed, fights with you (+3 damroll).',
                         'purchasable': False, 'faction_required': 'midgaard_guard', 'tameable': False,
                         'tame_difficulty': 90, 'combat_ok': True, 'damroll_bonus': 3, 'fire_aura': False,
                         'can_fly': False, 'never_tires': False},
    'merchant_camel': {'key': 'merchant_camel', 'name': 'a laden merchant camel', 'cost': 0, 'speed_bonus': 0.6,
                       'travel': 0.25, 'description': 'A League caravan camel. +25% speed, never tires.',
                       'purchasable': False, 'faction_required': 'merchant_league', 'tameable': False,
                       'tame_difficulty': 90, 'combat_ok': False, 'damroll_bonus': 0, 'fire_aura': False,
                       'can_fly': False, 'never_tires': True},
})

def _faction_mount(key, name, travel, desc, faction, **kw):
    return {'key': key, 'name': name, 'cost': 0, 'speed_bonus': kw.pop('speed_bonus', 0.55), 'travel': travel,
            'description': desc, 'purchasable': False, 'faction_required': faction, 'tameable': False,
            'tame_difficulty': 90, 'combat_ok': kw.get('combat_ok', False), 'damroll_bonus': kw.get('damroll_bonus', 0),
            'fire_aura': kw.get('fire_aura', False), 'can_fly': kw.get('can_fly', False),
            'never_tires': kw.get('never_tires', False)}


MOUNT_TEMPLATES.update({
    'shadowpanther': _faction_mount('shadowpanther', 'a sleek shadowpanther', 0.45, 'A black panther that pads without a sound. +45% speed.', 'thieves_guild'),
    'shadowcat': _faction_mount('shadowcat', 'a smoke-grey shadowcat', 0.4, 'A great grey cat of the alleys. +40% speed.', 'thieves_guild_faction'),
    'manabound_gryphon': _faction_mount('manabound_gryphon', 'a manabound gryphon', 0.55, 'A gryphon bound by the Mages Circle. +55% speed, flies over rough ground.', 'mages_guild', can_fly=True),
    'mana_wyrm': _faction_mount('mana_wyrm', 'a shimmering mana wyrm', 0.5, 'A serpent of living mana that swims the air. +50% speed, flies.', 'arcane_circle', can_fly=True),
    'riding_spider': _faction_mount('riding_spider', 'a giant riding spider', 0.35, 'A drow riding spider. +35% speed, fights with you (+1 damroll).', 'drow_conclave', combat_ok=True, damroll_bonus=1),
    'celestial_charger': _faction_mount('celestial_charger', 'a celestial charger', 0.5, 'A white charger of the Holy Order. +50% speed, fights with you (+2 damroll).', 'holy_order', combat_ok=True, damroll_bonus=2),
    'drake_whelp': _faction_mount('drake_whelp', 'a young drake', 0.4, 'A drake not yet grown, hot to the touch. +40% speed, fire aura.', 'dragon_cult', fire_aura=True, combat_ok=True),
    'dire_warg': _faction_mount('dire_warg', 'a dire warg', 0.4, 'An orc-bred warg the size of a pony. +40% speed, fights with you (+2 damroll).', 'orc_horde', combat_ok=True, damroll_bonus=2),
    'ancient_treant': _faction_mount('ancient_treant', 'an ancient treant', 0.15, 'A walking oak that lets you ride its shoulder. +15% speed, never tires, fights with you (+2 damroll).', 'natures_wardens', combat_ok=True, damroll_bonus=2, never_tires=True),
})

# the Dark Brotherhood's reward is the nightmare under the name the faction gives it
MOUNT_TEMPLATES['nightmare_steed'] = dict(MOUNT_TEMPLATES['nightmare'], key='nightmare_steed')

TRAVEL_CAP = 0.8        # nothing makes you more than 80% faster
HASTE_TRAVEL = 0.15     # haste (a spell or worn gear) quickens the feet too


def travel_speed(player) -> float:
    """How fast a player travels, as a multiple of walking pace (1.0 .. 1.8): the mount they
    ride (by its loyalty), haste, worn gear that quickens travel (procs.equip_totals), and the
    Pursuit of Justice talent. The 3D client scales the hero's run by it (map payload `speed`)."""
    bonus = 0.0
    mount = getattr(player, 'mount', None)
    if mount is not None and hasattr(mount, 'travel_bonus'):
        bonus += mount.travel_bonus()
    flags = getattr(player, 'affect_flags', None) or set()
    if 'haste' in flags or (hasattr(player, 'gear_hasted') and player.gear_hasted()):
        bonus += HASTE_TRAVEL
    if hasattr(player, 'get_equipment_bonus'):
        bonus += (player.get_equipment_bonus('travel_speed') or 0) / 100.0
    try:
        from talents import TalentManager
        bonus += TalentManager.get_talent_bonus(player, 'stat_bonus', 'move_speed') or 0
    except Exception:
        pass
    return round(1.0 + max(0.0, min(TRAVEL_CAP, bonus)), 3)


# the rare mounts that come from beating a boss: boss vnum -> (mount, percent a kill)
BOSS_MOUNTS = {
    9742: ('griffin', 5),            # the Roc Matriarch's eyrie
    9772: ('clockwork_steed', 5),    # the Carillon Engine
}


async def boss_mount_drop(winner, victim) -> Optional[str]:
    """A boss's mount, won by the player who beat it at its chance (once: owned mounts don't
    drop twice). Returns the mount's key when won."""
    entry = BOSS_MOUNTS.get(getattr(victim, 'vnum', None))
    if not entry or not hasattr(winner, 'owned_mounts'):
        return None
    key, chance = entry
    if MountManager.get_owned_mount_data(winner, key) or random.randint(1, 100) > chance:
        return None
    winner.owned_mounts.append({'key': key, 'loyalty': 100})
    tmpl = MOUNT_TEMPLATES[key]
    c = winner.config.COLORS
    await winner.send(f"{c['bright_yellow']}As {victim.name} falls, {tmpl['name']} is yours to ride! "
                      f"(mount {key}){c['reset']}")
    world = getattr(winner, 'world', None)
    if world and hasattr(world, 'broadcast'):
        await world.broadcast(f"{c['bright_yellow']}{winner.name} has won {tmpl['name']} from {victim.name}!{c['reset']}")
    return key


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
            travel=template.get('travel', 0.3),
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
