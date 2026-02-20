"""
Faction Reputation System
========================
Defines factions, reputation levels, opposing factions, and helpers for
tracking player standing with each faction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger('Misthollow.Factions')


REPUTATION_LEVELS = [
    'Hated',
    'Hostile',
    'Unfriendly',
    'Neutral',
    'Friendly',
    'Honored',
    'Revered',
    'Exalted',
]

# Each level spans 1000 points. Thresholds are inclusive (score >= threshold -> that level)
REPUTATION_THRESHOLDS: List[Tuple[str, int]] = [
    ('Hated', -3000),
    ('Hostile', -2000),
    ('Unfriendly', -1000),
    ('Neutral', 0),
    ('Friendly', 1000),
    ('Honored', 2000),
    ('Revered', 3000),
    ('Exalted', 4000),
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
    'Revered': 0.75,
    'Exalted': 0.7,
}

# Tier reward descriptions (for display)
TIER_REWARDS = {
    'Friendly': 'Discount at faction shops',
    'Honored': 'Access to faction-specific quests',
    'Revered': 'Faction title, special equipment',
    'Exalted': 'Unique mount/pet, powerful item',
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

    # ─── NEW FACTIONS (Reputation/Faction System) ───

    'midgaard_guard': Faction(
        key='midgaard_guard',
        name='Midgaard Guard',
        description='The sworn protectors of Midgaard. Gain reputation by killing bandits and undead near the city, and completing guard quests.',
        enemies=['thieves_guild', 'dark_brotherhood'],
        allies=['merchant_league'],
        quest_line=['guard_patrol', 'guard_bandit_hunt', 'guard_captain_trial'],
        exalted_rewards={
            'titles': ['the Sentinel of Midgaard'],
            'mounts': ['armored_warhorse'],
            'items': [9020],
        },
    ),
    'thieves_guild_faction': Faction(
        key='thieves_guild_faction',
        name='Thieves Guild',
        description='An underground syndicate of rogues and thieves. Gain reputation by pickpocketing, stealing, and completing shady quests.',
        enemies=['midgaard_guard'],
        allies=['dark_brotherhood'],
        quest_line=['guild_initiation', 'guild_heist', 'guild_shadowmaster'],
        exalted_rewards={
            'titles': ['the Shadow'],
            'mounts': ['shadowcat'],
            'items': [9021],
        },
    ),
    'arcane_circle': Faction(
        key='arcane_circle',
        name='Arcane Circle',
        description='Scholarly mages devoted to arcane research. Gain reputation by identifying items, killing magical creatures, and pursuing research.',
        enemies=[],
        allies=['natures_wardens'],
        quest_line=['circle_apprentice', 'circle_research', 'circle_archmage'],
        exalted_rewards={
            'titles': ['the Archmage'],
            'mounts': ['mana_wyrm'],
            'items': [9022],
        },
    ),
    'natures_wardens': Faction(
        key='natures_wardens',
        name="Nature's Wardens",
        description='Druids and rangers who protect the natural world. Gain reputation by killing undead, protecting animals, and foraging.',
        enemies=['dark_brotherhood'],
        allies=['arcane_circle'],
        quest_line=['warden_initiate', 'warden_grove_defense', 'warden_archdruid'],
        exalted_rewards={
            'titles': ['the Archdruid'],
            'mounts': ['ancient_treant'],
            'items': [9023],
        },
    ),
    'dark_brotherhood': Faction(
        key='dark_brotherhood',
        name='Dark Brotherhood',
        description='A sinister faction of assassins and dark practitioners. Gain reputation by killing guards, assassinating NPCs, and performing dark rituals.',
        enemies=['natures_wardens', 'midgaard_guard'],
        allies=['thieves_guild_faction'],
        quest_line=['brotherhood_blood_oath', 'brotherhood_contract', 'brotherhood_grandmaster'],
        exalted_rewards={
            'titles': ['the Deathbringer'],
            'mounts': ['nightmare_steed'],
            'items': [9024],
        },
    ),
    'merchant_league': Faction(
        key='merchant_league',
        name='Merchant League',
        description='A powerful guild of traders and merchants. Gain reputation by buying and selling in large amounts, and completing trade quests.',
        enemies=[],
        allies=['midgaard_guard'],
        quest_line=['league_apprentice', 'league_caravan', 'league_guildmaster'],
        exalted_rewards={
            'titles': ['the Magnate'],
            'mounts': ['merchant_camel'],
            'items': [9025],
        },
    ),
}

# Starting reputation for new players
DEFAULT_STARTING_REPUTATION = {
    'midgaard': 300,        # Friendly-ish (legacy)
    'elves': 0,             # Neutral
    'dwarves': 0,           # Neutral
    'thieves_guild': -600,  # Hidden (Hated until discovered)
    'mages_guild': 0,       # Neutral
    'drow_conclave': -300,  # Hostile
    'holy_order': 300,      # Friendly-ish (legacy)
    'dragon_cult': -300,    # Hostile
    'orc_horde': -300,      # Hostile
    # New factions — everyone starts Neutral
    'midgaard_guard': 0,
    'thieves_guild_faction': 0,
    'arcane_circle': 0,
    'natures_wardens': 0,
    'dark_brotherhood': 0,
    'merchant_league': 0,
}

# Actions that grant/lose reputation (referenced by game systems)
FACTION_REP_ACTIONS = {
    'kill_undead': {'holy_order': 5, 'midgaard_guard': 10, 'natures_wardens': 10},
    'heal_npc': {'holy_order': 3, 'midgaard': 1},
    'steal_success': {'thieves_guild': 5, 'midgaard': -3, 'thieves_guild_faction': 15, 'midgaard_guard': -8},
    'kill_dragon': {'dragon_cult': -50},
    'complete_sewer_quest': {'thieves_guild': 15, 'thieves_guild_faction': 20},
    'kill_city_guard': {'midgaard': -20, 'thieves_guild': 5, 'midgaard_guard': -25, 'dark_brotherhood': 15, 'thieves_guild_faction': 10},
    'kill_orc': {'orc_horde': -5, 'midgaard': 2, 'dwarves': 2},
    'kill_drow': {'drow_conclave': -10, 'elves': 3},
    'kill_elf': {'elves': -15, 'drow_conclave': 3},
    'kill_goblin': {'midgaard': 1, 'dwarves': 1, 'midgaard_guard': 5},
    # New faction actions
    'kill_bandit': {'midgaard_guard': 15},
    'kill_magical_creature': {'arcane_circle': 10},
    'kill_guard_npc': {'dark_brotherhood': 10, 'midgaard_guard': -15},
    'pickpocket': {'thieves_guild_faction': 10, 'midgaard_guard': -5},
    'identify_item': {'arcane_circle': 5},
    'forage': {'natures_wardens': 5},
    'shop_buy': {'merchant_league': 1},
    'shop_sell': {'merchant_league': 2},
    'shop_large_transaction': {'merchant_league': 10},
}

# Mob keyword -> faction rep mapping for auto-gain on kills
# Maps keywords found in mob name/keywords to faction reputation changes
MOB_KILL_FACTION_MAP = {
    # Killing bandits/thieves = +Guard rep
    'bandit': {'midgaard_guard': 15, 'thieves_guild_faction': -5},
    'brigand': {'midgaard_guard': 12},
    'highwayman': {'midgaard_guard': 15},
    'mugger': {'midgaard_guard': 10},
    'outlaw': {'midgaard_guard': 12},
    # Killing undead = +Guard & +Wardens rep
    'skeleton': {'midgaard_guard': 8, 'natures_wardens': 10},
    'zombie': {'midgaard_guard': 8, 'natures_wardens': 10},
    'ghost': {'natures_wardens': 12},
    'ghoul': {'natures_wardens': 12, 'midgaard_guard': 5},
    'wraith': {'natures_wardens': 15, 'midgaard_guard': 8},
    'vampire': {'natures_wardens': 20, 'midgaard_guard': 10},
    'lich': {'natures_wardens': 25, 'midgaard_guard': 15, 'arcane_circle': 10},
    'undead': {'natures_wardens': 10, 'midgaard_guard': 8},
    'wight': {'natures_wardens': 12},
    'spectre': {'natures_wardens': 15},
    # Killing magical creatures = +Arcane rep
    'elemental': {'arcane_circle': 15},
    'golem': {'arcane_circle': 12},
    'imp': {'arcane_circle': 8},
    'demon': {'arcane_circle': 20},
    'djinn': {'arcane_circle': 18},
    'familiar': {'arcane_circle': 5},
    # Killing guards = +Dark Brotherhood (opposing factions auto-handled)
    'guard': {'dark_brotherhood': 10, 'midgaard_guard': -20},
    'cityguard': {'dark_brotherhood': 10, 'midgaard_guard': -20},
    'watchman': {'dark_brotherhood': 8, 'midgaard_guard': -15},
    'soldier': {'dark_brotherhood': 8, 'midgaard_guard': -12},
    # Killing animals = -Wardens
    'deer': {'natures_wardens': -10},
    'rabbit': {'natures_wardens': -5},
    'fox': {'natures_wardens': -8},
    'stag': {'natures_wardens': -12},
    # Killing wolves/bears (threats) = slight +Wardens
    'wolf': {'natures_wardens': 5},
    'bear': {'natures_wardens': 5},
    'spider': {'natures_wardens': 5},
    # Orcs and goblins
    'goblin': {'midgaard_guard': 5, 'merchant_league': 3},
    'orc': {'midgaard_guard': 8},
    # Merchants/traders killed = -Merchant League
    'merchant': {'merchant_league': -20},
    'trader': {'merchant_league': -15},
    'shopkeeper': {'merchant_league': -25},
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
    def get_progress_in_level(score: int) -> tuple:
        """Return (current_level, progress_within_level 0-1000, level_name)."""
        level_name = FactionManager.get_level_for_score(score)
        # Find threshold for current level
        current_threshold = 0
        next_threshold = None
        for i, (name, threshold) in enumerate(REPUTATION_THRESHOLDS):
            if name == level_name:
                current_threshold = threshold
                if i + 1 < len(REPUTATION_THRESHOLDS):
                    next_threshold = REPUTATION_THRESHOLDS[i + 1][1]
                break
        if next_threshold is None:
            # At max level
            return (level_name, 1000, level_name)
        progress = score - current_threshold
        return (level_name, min(1000, max(0, progress)), level_name)

    @staticmethod
    def make_progress_bar(score: int, bar_length: int = 20) -> str:
        """Create a visual progress bar for reputation within current level."""
        level_name, progress, _ = FactionManager.get_progress_in_level(score)
        if level_name == 'Exalted':
            filled = bar_length
        else:
            filled = int((progress / 1000) * bar_length)
        empty = bar_length - filled
        return f"[{'█' * filled}{'░' * empty}] {progress}/1000"

    @staticmethod
    def get_level_color(level_name: str) -> str:
        """Return ANSI color code for a reputation level."""
        colors = {
            'Hated': '\033[1;31m',      # bright red
            'Hostile': '\033[31m',       # red
            'Unfriendly': '\033[33m',    # yellow
            'Neutral': '\033[37m',       # white
            'Friendly': '\033[32m',      # green
            'Honored': '\033[1;32m',     # bright green
            'Revered': '\033[1;36m',     # bright cyan
            'Exalted': '\033[1;33m',     # bright yellow
        }
        return colors.get(level_name, '\033[37m')

    @staticmethod
    async def on_mob_kill(player, victim):
        """Auto-gain faction reputation when killing a mob.
        Called from combat.handle_death after a player kills an NPC."""
        if not hasattr(player, 'connection') or hasattr(victim, 'connection'):
            return  # Only player-kills-NPC

        victim_name = getattr(victim, 'name', '').lower()
        victim_keywords = getattr(victim, 'keywords', [])

        # Collect all matching rep changes
        changes: Dict[str, int] = {}
        checked = set()
        for keyword, rep_map in MOB_KILL_FACTION_MAP.items():
            if keyword in checked:
                continue
            # Check if keyword appears in mob name or keywords
            if keyword in victim_name or keyword in victim_keywords:
                checked.add(keyword)
                for faction_key, amount in rep_map.items():
                    if faction_key in FACTIONS:
                        changes[faction_key] = changes.get(faction_key, 0) + amount

        # Also check mob's explicit faction tag
        mob_faction = getattr(victim, 'faction', None)
        if mob_faction:
            fk = FactionManager.normalize_key(mob_faction)
            if fk and fk not in changes:
                # Killing a faction member = lose rep with that faction
                changes[fk] = changes.get(fk, 0) - 10

        if changes:
            await FactionManager.apply_reputation_changes(player, changes, reason=f"Slaying {victim.name}")

    @staticmethod
    async def on_shop_transaction(player, amount: int, is_buy: bool = True):
        """Grant Merchant League rep for shop transactions."""
        if amount >= 500:
            rep = 10
        elif amount >= 100:
            rep = 5
        else:
            rep = 1 if is_buy else 2
        await FactionManager.apply_reputation_change(
            player, 'merchant_league', rep, reason='Trade transaction'
        )

    @staticmethod
    def format_reputation_summary(player) -> List[str]:
        FactionManager.ensure_player_reputation(player)
        lines = []
        # Show new factions first, then legacy
        new_factions = ['midgaard_guard', 'thieves_guild_faction', 'arcane_circle',
                        'natures_wardens', 'dark_brotherhood', 'merchant_league']
        other_factions = [k for k in FACTIONS if k not in new_factions]

        for key in new_factions + other_factions:
            if key not in FACTIONS:
                continue
            faction = FACTIONS[key]
            score = FactionManager.get_reputation(player, key)
            level = FactionManager.get_level_for_score(score)
            bar = FactionManager.make_progress_bar(score)
            level_col = FactionManager.get_level_color(level)
            reset = '\033[0m'
            lines.append(f"  {faction.name:<20s} {level_col}{level:<12s}{reset} {bar}")
        return lines

    @staticmethod
    def format_faction_detail(player, faction_key: str) -> List[str]:
        if faction_key not in FACTIONS:
            return ["Unknown faction."]
        faction = FACTIONS[faction_key]
        score = FactionManager.get_reputation(player, faction_key)
        level = FactionManager.get_level_for_score(score)
        bar = FactionManager.make_progress_bar(score)
        lines = [
            f"{faction.name} - {faction.description}",
            f"Standing: {level} ({score})  {bar}",
        ]
        if faction.enemies:
            enemies = ', '.join(FACTIONS[e].name for e in faction.enemies if e in FACTIONS)
            lines.append(f"Opposes: {enemies}")
        if faction.allies:
            allies = ', '.join(FACTIONS[a].name for a in faction.allies if a in FACTIONS)
            lines.append(f"Allies: {allies}")
        # Tier rewards
        lines.append("Rewards:")
        for tier, desc in TIER_REWARDS.items():
            marker = '✓' if REPUTATION_THRESHOLDS and FactionManager.get_threshold_for_level(tier) <= score else '○'
            lines.append(f"  {marker} {tier}: {desc}")
        if faction.exalted_rewards:
            rewards = faction.exalted_rewards
            titles = ', '.join(str(t) for t in rewards.get('titles', []))
            mounts = ', '.join(str(m) for m in rewards.get('mounts', []))
            if titles:
                lines.append(f"  Exalted Title: {titles}")
            if mounts:
                lines.append(f"  Exalted Mount: {mounts}")
        return lines


# ─────────────────────────────────────────────────────────────────────
# Faction NPC Prototypes — spawned via code, not zone JSON edits
# ─────────────────────────────────────────────────────────────────────

FACTION_NPC_PROTOTYPES = {
    # Midgaard Guard quartermaster — city area (zone 30, room 3005)
    'guard_quartermaster': {
        'vnum': 9501,
        'name': 'Captain Aldren',
        'short_desc': 'Captain Aldren, the Guard Quartermaster',
        'long_desc': 'Captain Aldren stands here in polished plate armor, inspecting his ledger.',
        'description': 'A grizzled veteran of the Midgaard Guard with a scar across his left cheek.',
        'keywords': ['captain', 'aldren', 'guard', 'quartermaster'],
        'level': 25,
        'flags': ['sentinel', 'helper'],
        'special': 'faction_npc',
        'faction': 'midgaard_guard',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "Captain Aldren says, 'The Guard watches over Midgaard. Prove your loyalty and I'll see you equipped.'",
            'hostile': "Captain Aldren scowls. 'I have nothing to say to the likes of you.'",
        },
        'spawn_room': 3005,
    },
    # Thieves Guild fence — sewer area (zone 30, room 3044 or similar)
    'guild_fence': {
        'vnum': 9502,
        'name': 'Whisper',
        'short_desc': 'Whisper, the Guild Fence',
        'long_desc': 'A cloaked figure lurks in the shadows, eyes glinting.',
        'description': 'You can barely make out the face beneath the hood. This is Whisper, fence for the Thieves Guild.',
        'keywords': ['whisper', 'fence', 'thief', 'guild'],
        'level': 20,
        'flags': ['sentinel'],
        'special': 'faction_npc',
        'faction': 'thieves_guild_faction',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "Whisper hisses, 'Looking to move some goods? Prove you're one of us first.'",
        },
        'spawn_room': 3044,
    },
    # Arcane Circle scholar — near mage guild (zone 30, room 3017)
    'circle_scholar': {
        'vnum': 9503,
        'name': 'Archmage Thessaly',
        'short_desc': 'Archmage Thessaly of the Arcane Circle',
        'long_desc': 'An elderly mage with a long silver beard pores over a glowing tome.',
        'description': 'Archmage Thessaly radiates an aura of arcane power. Her robes shimmer with protective wards.',
        'keywords': ['archmage', 'thessaly', 'mage', 'scholar', 'circle'],
        'level': 30,
        'flags': ['sentinel'],
        'special': 'faction_npc',
        'faction': 'arcane_circle',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "Archmage Thessaly says, 'The Arcane Circle seeks those who pursue knowledge. Show us your dedication.'",
        },
        'spawn_room': 3017,
    },
    # Nature's Wardens — forest area (zone 36 or light forest)
    'warden_druid': {
        'vnum': 9504,
        'name': 'Elder Oakhart',
        'short_desc': 'Elder Oakhart of the Wardens',
        'long_desc': 'A weathered druid wrapped in living vines stands here communing with nature.',
        'description': 'Elder Oakhart is ancient and gnarled like the trees he protects.',
        'keywords': ['elder', 'oakhart', 'druid', 'warden'],
        'level': 28,
        'flags': ['sentinel'],
        'special': 'faction_npc',
        'faction': 'natures_wardens',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "Elder Oakhart rumbles, 'The forest remembers those who protect it. Prove your worth, young one.'",
        },
        'spawn_room': 3600,
    },
    # Dark Brotherhood — hidden area (zone 31 graveyard or similar)
    'brotherhood_agent': {
        'vnum': 9505,
        'name': 'the Shrouded Figure',
        'short_desc': 'a shrouded figure from the Dark Brotherhood',
        'long_desc': 'A figure cloaked in darkness watches you with cold, calculating eyes.',
        'description': 'This is an agent of the Dark Brotherhood. Their identity is hidden behind layers of shadow.',
        'keywords': ['shrouded', 'figure', 'brotherhood', 'dark'],
        'level': 25,
        'flags': ['sentinel'],
        'special': 'faction_npc',
        'faction': 'dark_brotherhood',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "The Shrouded Figure whispers, 'We are always watching. Prove your darkness and we may have use for you.'",
        },
        'spawn_room': 3100,
    },
    # Merchant League — market/shop area (zone 30)
    'league_guildmaster': {
        'vnum': 9506,
        'name': 'Guildmaster Brennan',
        'short_desc': 'Guildmaster Brennan of the Merchant League',
        'long_desc': 'A portly man in fine silk robes examines a set of golden scales.',
        'description': 'Guildmaster Brennan is the local representative of the Merchant League, always looking for profitable ventures.',
        'keywords': ['guildmaster', 'brennan', 'merchant', 'league'],
        'level': 20,
        'flags': ['sentinel'],
        'special': 'faction_npc',
        'faction': 'merchant_league',
        'min_rep_talk_level': 'Friendly',
        'talk_responses': {
            'default': "Guildmaster Brennan says, 'Commerce makes the world go round! Trade with us and reap the rewards.'",
        },
        'spawn_room': 3014,
    },
}


def spawn_faction_npcs(world):
    """Spawn faction NPCs into the world. Called once during world startup.
    Does NOT modify zone JSON files — creates mobs via code only."""
    from mobs import Mobile

    spawned = 0
    for npc_key, proto in FACTION_NPC_PROTOTYPES.items():
        room_vnum = proto.get('spawn_room')
        if not room_vnum:
            continue

        room = world.get_room(room_vnum)
        if not room:
            logger.warning(f"Faction NPC {npc_key}: room {room_vnum} not found, skipping")
            continue

        # Don't double-spawn if already present
        already = any(getattr(m, 'vnum', 0) == proto['vnum'] for m in room.characters)
        if already:
            continue

        mob = Mobile.from_prototype(proto, world)
        mob.room = room
        mob.home_room = room
        mob.home_zone = room_vnum // 100
        room.characters.append(mob)
        spawned += 1
        logger.info(f"Spawned faction NPC: {mob.name} in room {room_vnum}")

    if spawned:
        logger.info(f"Spawned {spawned} faction NPCs")
