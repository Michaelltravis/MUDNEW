"""
Talent Tree System for Misthollow

Each class has 3 specialization trees. Players earn talent points
as they level and can spend them to unlock powerful abilities and
passive bonuses.

Talent Points: 1 per level starting at level 5 (46 total by level 50)
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger(__name__)


@dataclass
class Talent:
    """A single talent in a tree."""
    id: str
    name: str
    description: str
    max_rank: int = 1
    tier: int = 1  # 1-5, determines point requirement
    requires: List[str] = field(default_factory=list)  # Prerequisite talent IDs
    effects: Dict[str, Any] = field(default_factory=dict)
    # Effect types:
    # - stat_bonus: {'str': 2, 'crit_chance': 5}
    # - damage_mod: {'physical': 0.1, 'fire': 0.15}
    # - skill_unlock: 'whirlwind'
    # - passive: 'second_wind' (handled specially in combat)
    # - proc: {'chance': 10, 'effect': 'stun', 'duration': 2}


# =============================================================================
# WARRIOR TALENT TREES
# =============================================================================

WARRIOR_VANGUARD = {
    'name': 'Vanguard',
    'description': 'Stronger openers, chain initiation, and aggressive starts.',
    'icon': '🟢',
    'talents': {
        'opening_strike': Talent(id='opening_strike', name='Opening Strike', description='Opener damage +4% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'opener_damage': 0.04}}),
        'momentum': Talent(id='momentum', name='Momentum', description='Chain decay window +1s per rank (base 8s becomes 13s at rank 5).', max_rank=5, tier=1, effects={'stat_bonus': {'chain_decay': 1}}),
        'heavy_impact': Talent(id='heavy_impact', name='Heavy Impact', description='Openers stun for +1 extra round.', max_rank=1, tier=2, effects={'passive': 'heavy_impact'}),
        'quick_recovery': Talent(id='quick_recovery', name='Quick Recovery', description='Opener cooldowns reduced by 5/10/15%.', max_rank=3, tier=2, effects={'stat_bonus': {'opener_cd_reduction': 0.05}}),
        'chain_starter': Talent(id='chain_starter', name='Chain Starter', description='Openers start chain at 2 instead of 1.', max_rank=1, tier=3, effects={'passive': 'chain_starter'}),
        'relentless_advance': Talent(id='relentless_advance', name='Relentless Advance', description='After opener, next ability within 3s gets +3% damage per rank.', max_rank=5, tier=3, effects={'stat_bonus': {'post_opener_damage': 0.03}}),
        'battering_ram': Talent(id='battering_ram', name='Battering Ram', description='Charge can be used in combat. Cooldown halved.', max_rank=1, tier=4, effects={'passive': 'battering_ram'}),
        'thunderclap': Talent(id='thunderclap', name='Thunderclap', description='Bash hits 1 additional target per 2 ranks.', max_rank=5, tier=4, effects={'stat_bonus': {'bash_aoe': 1}}),
        'warlords_presence': Talent(id='warlords_presence', name="Warlord's Presence", description='Active: For 15s, all openers also count as chains (don\'t reset chain). 120s CD.', max_rank=1, tier=5, effects={'skill_unlock': 'warlords_presence'}),
    }
}

WARRIOR_TACTICIAN = {
    'name': 'Tactician',
    'description': 'Longer chains, defensive bonuses, and adaptive combat.',
    'icon': '🟡',
    'talents': {
        'fluid_combat': Talent(id='fluid_combat', name='Fluid Combat', description='Chain damage bonus +2% per rank (base 15% becomes 17-25%).', max_rank=5, tier=1, effects={'stat_bonus': {'chain_damage_bonus': 0.02}}),
        'endurance': Talent(id='endurance', name='Endurance', description='Max HP +2% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'max_hp_pct': 0.02}}),
        'double_chain': Talent(id='double_chain', name='Double Chain', description='Chain abilities can extend without an opener.', max_rank=1, tier=2, effects={'passive': 'double_chain'}),
        'defensive_flow': Talent(id='defensive_flow', name='Defensive Flow', description='While chain >= 3, take 3/6/10% less damage.', max_rank=3, tier=2, effects={'stat_bonus': {'chain_dr': 0.03}}),
        'counter_rhythm': Talent(id='counter_rhythm', name='Counter Rhythm', description='After dodging or parrying, instantly gain +1 chain.', max_rank=1, tier=3, effects={'passive': 'counter_rhythm'}),
        'adaptive_defense': Talent(id='adaptive_defense', name='Adaptive Defense', description='Damage reduction +1% per chain count per rank.', max_rank=5, tier=3, effects={'stat_bonus': {'chain_adaptive_dr': 0.01}}),
        'chain_mastery': Talent(id='chain_mastery', name='Chain Mastery', description='Chain max increased to 7 instead of 5.', max_rank=1, tier=4, effects={'passive': 'chain_mastery'}),
        'opportunist': Talent(id='opportunist', name='Opportunist', description='3% chance per rank for chain abilities to not trigger cooldown.', max_rank=5, tier=4, effects={'proc': {'chance': 3, 'effect': 'no_cooldown'}}),
        'perfect_form': Talent(id='perfect_form', name='Perfect Form', description='Active: For 12s, ALL abilities count as their chain type AND the next type. 180s CD.', max_rank=1, tier=5, effects={'skill_unlock': 'perfect_form'}),
    }
}

WARRIOR_EXECUTIONER = {
    'name': 'Executioner',
    'description': 'Devastating finishers, combo mastery, and burst damage.',
    'icon': '🔴',
    'talents': {
        'killing_blow': Talent(id='killing_blow', name='Killing Blow', description='Finisher damage +4% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'finisher_damage': 0.04}}),
        'bloodlust_exec': Talent(id='bloodlust_exec', name='Bloodlust', description='Crit chance +1% per rank on finishers.', max_rank=5, tier=1, effects={'stat_bonus': {'finisher_crit': 0.01}}),
        'swift_execution': Talent(id='swift_execution', name='Swift Execution', description='Finisher cooldowns reduced by 25%.', max_rank=1, tier=2, effects={'passive': 'swift_execution'}),
        'chain_burst': Talent(id='chain_burst', name='Chain Burst', description='Finishers at chain 4+ deal +10/20/30% bonus damage.', max_rank=3, tier=2, effects={'stat_bonus': {'chain4_bonus': 0.10}}),
        'combo_mastery': Talent(id='combo_mastery', name='Combo Mastery', description='Named combo bonuses are 50% stronger.', max_rank=1, tier=3, effects={'passive': 'combo_mastery'}),
        'devastating_force': Talent(id='devastating_force', name='Devastating Force', description='Execute HP threshold +2% per rank (base 30% becomes 40% at rank 5).', max_rank=5, tier=3, effects={'stat_bonus': {'exec_threshold': 0.02}}),
        'second_wind': Talent(id='second_wind', name='Second Wind', description='After landing a finisher, heal 10% max HP.', max_rank=1, tier=4, effects={'passive': 'second_wind'}),
        'relentless_finisher': Talent(id='relentless_finisher', name='Relentless Finisher', description='After finisher, next opener within 4s keeps chain at 2, +2% per rank chance to keep at 3.', max_rank=5, tier=4, effects={'stat_bonus': {'post_finish_chain': 0.02}}),
        'avatar_of_war': Talent(id='avatar_of_war', name='Avatar of War', description='Active: For 15s, finishers don\'t reset chain. Every finisher also hits as AoE. 180s CD.', max_rank=1, tier=5, effects={'skill_unlock': 'avatar_of_war'}),
    }
}

# =============================================================================
# MAGE TALENT TREES
# =============================================================================

MAGE_FIRE = {
    'name': 'Fire',
    'description': 'Burn enemies with devastating fire magic.',
    'icon': '🔥',
    'talents': {
        'burning_soul': Talent(
            id='burning_soul', name='Burning Soul',
            description='Fire spell damage +3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'fire': 0.03}}
        ),
        'ignite': Talent(
            id='ignite', name='Ignite',
            description='Fire spells leave a DoT for 3/4/5% of damage per tick.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 100, 'effect': 'ignite_dot', 'on': 'fire_spell'}}
        ),
        'improved_fireball': Talent(
            id='improved_fireball', name='Improved Fireball',
            description='Fireball cast time -30%, damage +15%.',
            max_rank=1, tier=2,
            effects={'passive': 'improved_fireball'}
        ),
        'searing_heat': Talent(
            id='searing_heat', name='Searing Heat',
            description='Fire DoT damage +2% per rank.',
            max_rank=5, tier=2,
            effects={'damage_mod': {'fire_dot': 0.02}}
        ),
        'pyroblast': Talent(
            id='pyroblast', name='Pyroblast',
            description='Active: Massive fire nuke, int*6 damage. Costs 3 charges. 20s CD.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'pyroblast'}
        ),
        'fire_mastery': Talent(
            id='fire_mastery', name='Fire Mastery',
            description='Fire crit chance +1% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'fire_crit': 0.01}}
        ),
        'combustion': Talent(
            id='combustion', name='Combustion',
            description='Active: All fire DoTs tick instantly + 2x. Costs 4 charges. 45s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'combustion'}
        ),
        'living_bomb': Talent(
            id='living_bomb', name='Living Bomb',
            description='Fire DoTs have 5% chance per rank to spread to nearby enemy.',
            max_rank=5, tier=4,
            effects={'proc': {'chance': 5, 'effect': 'spread_dot'}}
        ),
        'phoenix_flames': Talent(
            id='phoenix_flames', name='Phoenix Flames',
            description='Active: AoE fire, int*8 to all enemies. Leaves HoT on mage. Costs 5 charges. 90s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'phoenix_flames'}
        ),
    }
}

MAGE_FROST = {
    'name': 'Frost',
    'description': 'Control and shatter foes with frost magic.',
    'icon': '❄️',
    'talents': {
        'frostbite': Talent(
            id='frostbite', name='Frostbite',
            description='Frost spells 10/20/30% chance to root for 1 round.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 10, 'effect': 'root', 'duration': 1}}
        ),
        'piercing_cold': Talent(
            id='piercing_cold', name='Piercing Cold',
            description='Frost spell damage +2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'frost': 0.02}}
        ),
        'frozen_armor': Talent(
            id='frozen_armor', name='Frozen Armor',
            description='Passive: melee attackers slowed, +10% armor.',
            max_rank=1, tier=2,
            effects={'passive': 'frozen_armor'}
        ),
        'arctic_winds': Talent(
            id='arctic_winds', name='Arctic Winds',
            description='Frost slow duration +5% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'frost_slow_duration': 0.05}}
        ),
        'shatter': Talent(
            id='shatter', name='Shatter',
            description='Frozen/rooted targets take 50% more crit damage.',
            max_rank=1, tier=3,
            effects={'passive': 'shatter'}
        ),
        'brain_freeze': Talent(
            id='brain_freeze', name='Brain Freeze',
            description='Frost spells have 3% per rank chance to make next spell free.',
            max_rank=5, tier=3,
            effects={'proc': {'chance': 3, 'effect': 'free_spell'}}
        ),
        'ice_lance': Talent(
            id='ice_lance', name='Ice Lance',
            description='Active: Instant frost damage, 2x vs frozen targets. Costs 2 charges. 10s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'ice_lance'}
        ),
        'frost_mastery': Talent(
            id='frost_mastery', name='Frost Mastery',
            description='Frost crit damage +3% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'frost_crit_damage': 0.03}}
        ),
        'deep_freeze': Talent(
            id='deep_freeze', name='Deep Freeze',
            description='Active: Stun target 3 rounds + massive frost damage. Costs 5 charges. 120s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'deep_freeze'}
        ),
    }
}

MAGE_ARCANE = {
    'name': 'Arcane',
    'description': 'Master arcane charges for devastating efficiency.',
    'icon': '✨',
    'talents': {
        'arcane_focus': Talent(
            id='arcane_focus', name='Arcane Focus',
            description='Arcane spell damage +2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'arcane': 0.02}}
        ),
        'arcane_concentration': Talent(
            id='arcane_concentration', name='Arcane Concentration',
            description='5/10/15% chance to not consume mana on cast.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 5, 'effect': 'free_cast'}}
        ),
        'arcane_echo': Talent(
            id='arcane_echo', name='Arcane Echo',
            description='Arcane Barrage has 25% chance to refund 2 charges.',
            max_rank=1, tier=2,
            effects={'passive': 'arcane_echo'}
        ),
        'arcane_stability': Talent(
            id='arcane_stability', name='Arcane Stability',
            description='Mana cost increase from charges reduced by 2% per rank.',
            max_rank=5, tier=2,
            effects={'passive': 'arcane_stability'}
        ),
        'presence_of_mind': Talent(
            id='presence_of_mind', name='Presence of Mind',
            description='Active: Next spell is instant cast + costs no mana. 90s CD.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'presence_of_mind'}
        ),
        'arcane_potency': Talent(
            id='arcane_potency', name='Arcane Potency',
            description='Charge damage bonus +1% per rank (base 8% becomes 9-13%).',
            max_rank=5, tier=3,
            effects={'passive': 'arcane_potency'}
        ),
        'arcane_power': Talent(
            id='arcane_power', name='Arcane Power',
            description='Active: +30% spell damage for 15s but charges generate 2x faster. Costs 3 charges. 120s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'arcane_power'}
        ),
        'arcane_brilliance': Talent(
            id='arcane_brilliance', name='Arcane Brilliance',
            description='Max mana +2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'max_mana_pct': 0.02}}
        ),
        'arcane_mastery': Talent(
            id='arcane_mastery', name='Arcane Mastery',
            description='Passive: 6th charge slot unlocked. At 6 charges, Arcane Barrage is guaranteed crit.',
            max_rank=1, tier=5,
            effects={'passive': 'arcane_mastery'}
        ),
    }
}



# =============================================================================
# THIEF TALENT TREES
# =============================================================================

# === LEGACY THIEF TREES (replaced by Wave 1 rework) ===
_THIEF_ASSASSINATION_LEGACY = {
    'name': 'Assassination',
    'description': 'Deadly poisons and lethal strikes from the shadows.',
    'icon': '🗡️',
    'talents': {
        'malice': Talent(
            id='malice', name='Malice',
            description='Increases crit chance by 1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'crit_chance': 1}}
        ),
        'improved_poisons': Talent(
            id='improved_poisons', name='Improved Poisons',
            description='Poison damage increased by 10% per rank.',
            max_rank=3, tier=1,
            effects={'damage_mod': {'poison': 0.1}}
        ),
        'toxic_blades': Talent(
            id='toxic_blades', name='Toxic Blades',
            description='Poison ticks reduce enemy healing by 20%.',
            max_rank=1, tier=2,
            requires=['improved_poisons'],
            effects={'passive': 'toxic_blades'}
        ),
        'ambush': Talent(
            id='ambush', name='Ambush',
            description='Unlocks Ambush: Stun opener from stealth.',
            max_rank=1, tier=2,
            requires=['malice'],
            effects={'skill_unlock': 'ambush'}
        ),
        'cold_blood': Talent(
            id='cold_blood', name='Cold Blood',
            description='Unlocks Cold Blood: Next attack is guaranteed crit.',
            max_rank=1, tier=2, requires=['malice'],
            effects={'skill_unlock': 'cold_blood'}
        ),
        'seal_fate': Talent(
            id='seal_fate', name='Seal Fate',
            description='Crits from backstab grant combo point.',
            max_rank=1, tier=3, requires=['cold_blood'],
            effects={'passive': 'seal_fate'}
        ),
        'mutilate': Talent(
            id='mutilate', name='Mutilate',
            description='Unlocks Mutilate: Dual-wield strike with bonus damage.',
            max_rank=1, tier=4, requires=['seal_fate'],
            effects={'skill_unlock': 'mutilate'}
        ),
        'vendetta': Talent(
            id='vendetta', name='Vendetta',
            description='Mark target to take 20% more damage from you.',
            max_rank=1, tier=5, requires=['mutilate'],
            effects={'skill_unlock': 'vendetta'}
        ),

        'ruthless_precision': Talent(
            id='ruthless_precision', name='Ruthless Precision',
            description='Combo point generation increased by 5% per rank.',
            max_rank=3, tier=2,
            effects={'stat_bonus': {'combo_gen': 0.05}}
        ),
        'lethality': Talent(
            id='lethality', name='Lethality',
            description='Crit damage increased by 3% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'crit_damage': 3}}
        ),
        'assassins_resolve': Talent(
            id='assassins_resolve', name="Assassin's Resolve",
            description='Attack power increased by 2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'attack_power': 0.02}}
        ),
    }
}

_THIEF_COMBAT_LEGACY = {
    'name': 'Combat',
    'description': 'Skilled fighter excelling in sustained combat.',
    'icon': '⚔️',
    'talents': {
        'precision': Talent(
            id='precision', name='Precision',
            description='Increases hit chance by 1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'hit_chance': 1}}
        ),
        'dual_wield_spec': Talent(
            id='dual_wield_spec', name='Dual Wield Specialization',
            description='Off-hand damage increased by 10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'offhand_damage': 0.1}}
        ),
        'riposte': Talent(
            id='riposte', name='Riposte',
            description='After dodging or parrying, counterattack for 50% damage.',
            max_rank=1, tier=2,
            requires=['precision'],
            effects={'passive': 'riposte'}
        ),
        'blade_flurry': Talent(
            id='blade_flurry', name='Blade Flurry',
            description='Attacks hit an additional nearby enemy.',
            max_rank=1, tier=2, requires=['dual_wield_spec'],
            effects={'passive': 'blade_flurry'}
        ),
        'adrenaline_rush': Talent(
            id='adrenaline_rush', name='Adrenaline Rush',
            description='Unlocks: Double attack speed for 15 seconds.',
            max_rank=1, tier=3, requires=['blade_flurry'],
            effects={'skill_unlock': 'adrenaline_rush'}
        ),
        'blade_dance': Talent(
            id='blade_dance', name='Blade Dance',
            description='Unlocks Blade Dance: Spin striking all enemies.',
            max_rank=1, tier=4, requires=['adrenaline_rush'],
            effects={'skill_unlock': 'blade_dance'}
        ),
        'killing_spree': Talent(
            id='killing_spree', name='Killing Spree',
            description='Unlocks: Teleport between enemies attacking each.',
            max_rank=1, tier=5, requires=['adrenaline_rush'],
            effects={'skill_unlock': 'killing_spree'}
        ),

        'improved_sinister': Talent(
            id='improved_sinister', name='Improved Sinister Strike',
            description='Sinister Strike damage increased by 3% per rank.',
            max_rank=3, tier=2,
            effects={'skill_mod': {'sinister_strike': {'damage': 0.03}}}
        ),
        'combat_potency': Talent(
            id='combat_potency', name='Combat Potency',
            description='Off-hand attacks generate extra energy per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'energy_gen': 0.05}}
        ),
        'savage_combat': Talent(
            id='savage_combat', name='Savage Combat',
            description='Physical damage increased by 2% per rank.',
            max_rank=5, tier=4,
            effects={'damage_mod': {'physical': 0.02}}
        ),
        'unfair_advantage': Talent(
            id='unfair_advantage', name='Unfair Advantage',
            description='Dodge grants a counterattack per rank.',
            max_rank=3, tier=4,
            effects={'proc': {'on': 'dodge', 'effect': 'counterattack', 'chance': 33}}
        ),
    }
}

_THIEF_SUBTLETY_LEGACY = {
    'name': 'Subtlety',
    'description': 'Master of shadows and misdirection.',
    'icon': '🌑',
    'talents': {
        'master_of_deception': Talent(
            id='master_of_deception', name='Master of Deception',
            description='Stealth detection range reduced by 10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'stealth': 0.1}}
        ),
        'shadow_veil': Talent(
            id='shadow_veil', name='Shadow Veil',
            description='Killing a target grants brief stealth.',
            max_rank=1, tier=2,
            requires=['master_of_deception'],
            effects={'passive': 'shadow_veil'}
        ),
        'opportunity': Talent(
            id='opportunity', name='Opportunity',
            description='Backstab damage increased by 4% per rank.',
            max_rank=5, tier=1,
            effects={'skill_mod': {'backstab': {'damage': 0.04}}}
        ),
        'preparation': Talent(
            id='preparation', name='Preparation',
            description='Unlocks: Reset cooldown of all abilities.',
            max_rank=1, tier=2, requires=['master_of_deception'],
            effects={'skill_unlock': 'preparation'}
        ),
        'shadowstep': Talent(
            id='shadowstep', name='Shadowstep',
            description='Unlocks: Teleport behind target.',
            max_rank=1, tier=3, requires=['preparation'],
            effects={'skill_unlock': 'shadowstep'}
        ),
        'slip_away': Talent(
            id='slip_away', name='Slip Away',
            description='Unlocks Slip Away: Enter stealth after dodging.',
            max_rank=1, tier=4, requires=['shadowstep'],
            effects={'skill_unlock': 'slip_away'}
        ),
        'shadow_dance': Talent(
            id='shadow_dance', name='Shadow Dance',
            description='Unlocks: Use stealth abilities while in combat.',
            max_rank=1, tier=5, requires=['shadowstep'],
            effects={'skill_unlock': 'shadow_dance'}
        ),

        'elusiveness': Talent(
            id='elusiveness_sub', name='Elusiveness',
            description='Dodge chance increased by 1% per rank.',
            max_rank=3, tier=2,
            effects={'stat_bonus': {'dodge': 1}}
        ),
        'sinister_calling': Talent(
            id='sinister_calling', name='Sinister Calling',
            description='Agility increased by 2% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'agi_mult': 0.02}}
        ),
        'night_stalker': Talent(
            id='night_stalker', name='Night Stalker',
            description='Damage from stealth increased by 3% per rank.',
            max_rank=5, tier=4,
            effects={'damage_mod': {'stealth': 0.03}}
        ),
        'shadow_techniques': Talent(
            id='shadow_techniques', name='Shadow Techniques',
            description='Auto-attacks have 5% chance per rank to gen combo point.',
            max_rank=3, tier=4,
            effects={'proc': {'chance': 5, 'effect': 'combo_point'}}
        ),
    }
}


# =============================================================================
# CLERIC TALENT TREES
# =============================================================================

_CLERIC_HOLY_LEGACY = {
    'name': 'Holy',
    'description': 'Channel divine light to heal and protect.',
    'icon': '✝️',
    'talents': {
        'healing_focus': Talent(
            id='healing_focus', name='Healing Focus',
            description='Healing spells 3% more effective per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'healing_power': 0.03}}
        ),
        'divine_fury': Talent(
            id='divine_fury', name='Divine Fury',
            description='Holy damage increased by 2% per rank.',
            max_rank=3, tier=1,
            effects={'damage_mod': {'holy': 0.02}}
        ),
        'inspiration': Talent(
            id='inspiration', name='Inspiration',
            description='Crit heals increase target armor by 10%.',
            max_rank=1, tier=2, requires=['healing_focus'],
            effects={'passive': 'inspiration'}
        ),
        'renew': Talent(
            id='renew', name='Renew',
            description='Large heals apply a healing-over-time effect.',
            max_rank=1, tier=3, requires=['inspiration'],
            effects={'passive': 'renew'}
        ),
        'guardian_spirit': Talent(
            id='guardian_spirit', name='Guardian Spirit',
            description='Unlocks: Prevent target death, heal to 50%.',
            max_rank=1, tier=4, requires=['inspiration'],
            effects={'skill_unlock': 'guardian_spirit'}
        ),
        'divine_hymn': Talent(
            id='divine_hymn', name='Divine Hymn',
            description='Unlocks: Heal all allies in room.',
            max_rank=1, tier=5, requires=['guardian_spirit'],
            effects={'skill_unlock': 'divine_hymn'}
        ),

        'spiritual_guidance': Talent(
            id='spiritual_guidance', name='Spiritual Guidance',
            description='Spirit increases spell power by 2% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'spirit_to_spell': 0.02}}
        ),
        'holy_specialization': Talent(
            id='holy_specialization', name='Holy Specialization',
            description='Holy spell crit chance increased by 1% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'holy_crit': 1}}
        ),
        'empowered_healing': Talent(
            id='empowered_healing', name='Empowered Healing',
            description='Healing power increased by 2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'healing_power': 0.02}}
        ),
        'serenity': Talent(
            id='serenity', name='Serenity',
            description='Mana regeneration increased by 3% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'mana_regen': 0.03}}
        ),
    }
}

_CLERIC_DISCIPLINE_LEGACY = {
    'name': 'Discipline',
    'description': 'Prevent damage through shields and atonement.',
    'icon': '🛡️',
    'talents': {
        'improved_shields': Talent(
            id='improved_shields', name='Improved Shields',
            description='Shield absorption increased by 5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'shield_power': 0.05}}
        ),
        'atonement': Talent(
            id='atonement', name='Atonement',
            description='Dealing damage heals lowest HP ally.',
            max_rank=1, tier=2, requires=['improved_shields'],
            effects={'passive': 'atonement'}
        ),
        'pain_to_power': Talent(
            id='pain_to_power', name='Pain to Power',
            description='5% of damage taken is converted into mana.',
            max_rank=1, tier=3, requires=['atonement'],
            effects={'passive': 'pain_to_power'}
        ),
        'power_word_shield': Talent(
            id='power_word_shield', name='Power Word: Shield',
            description='Unlocks: Instant cast damage absorption shield.',
            max_rank=1, tier=3, requires=['atonement'],
            effects={'skill_unlock': 'power_word_shield'}
        ),
        'aegis_ward': Talent(
            id='aegis_ward', name='Aegis Ward',
            description='Unlocks: Shield target and reduce their threat.',
            max_rank=1, tier=4, requires=['power_word_shield'],
            effects={'skill_unlock': 'aegis_ward'}
        ),
        'pain_suppression': Talent(
            id='pain_suppression', name='Pain Suppression',
            description='Unlocks: Reduce target damage taken by 40%.',
            max_rank=1, tier=5, requires=['aegis_ward'],
            effects={'skill_unlock': 'pain_suppression'}
        ),

        'mental_agility': Talent(
            id='mental_agility', name='Mental Agility',
            description='Instant cast spells cost 2% less mana per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'instant_cost': -0.02}}
        ),
        'inner_focus': Talent(
            id='inner_focus', name='Inner Focus',
            description='Spell crit chance increased by 1% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'spell_crit': 1}}
        ),
        'focused_will': Talent(
            id='focused_will', name='Focused Will',
            description='Damage taken reduced by 1% per rank after being crit.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'crit_damage_reduction': 0.01}}
        ),
        'borrowed_time': Talent(
            id='borrowed_time', name='Borrowed Time',
            description='After shielding, haste increased by 2% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'shield_haste': 0.02}}
        ),
        'grace': Talent(
            id='grace', name='Grace',
            description='Healing on shielded targets increased by 2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'shield_heal': 0.02}}
        ),
        'rapture': Talent(
            id='rapture', name='Rapture',
            description='When shield breaks, restore 2% mana per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'shield_mana': 0.02}}
        ),
    }
}

_CLERIC_SHADOW_LEGACY = {
    'name': 'Shadow',
    'description': 'Embrace darkness for devastating power.',
    'icon': '🌑',
    'talents': {
        'shadow_focus': Talent(
            id='shadow_focus', name='Shadow Focus',
            description='Shadow damage increased by 3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'shadow': 0.03}}
        ),
        'shadow_word_pain': Talent(
            id='shadow_word_pain', name='Shadow Word: Pain',
            description='Unlocks: Shadow Word: Pain damage over time spell.',
            max_rank=1, tier=2, requires=['shadow_focus'],
            effects={'skill_unlock': 'shadow_word_pain'}
        ),
        'siphon_light': Talent(
            id='siphon_light', name='Siphon Light',
            description='Shadow damage heals you for 10% of damage dealt.',
            max_rank=1, tier=3, requires=['shadow_word_pain'],
            effects={'passive': 'siphon_light'}
        ),
        'vampiric_embrace': Talent(
            id='vampiric_embrace', name='Vampiric Embrace',
            description='Shadow damage heals you for 15%.',
            max_rank=1, tier=3, requires=['shadow_word_pain'],
            effects={'passive': 'vampiric_embrace'}
        ),
        'shadowform': Talent(
            id='shadowform', name='Shadowform',
            description='Unlocks: +15% shadow damage, -15% physical.',
            max_rank=1, tier=4, requires=['vampiric_embrace'],
            effects={'skill_unlock': 'shadowform'}
        ),
        'mind_flay': Talent(
            id='mind_flay', name='Mind Flay',
            description='Unlocks: Channeled shadow damage that slows.',
            max_rank=1, tier=5, requires=['shadowform'],
            effects={'skill_unlock': 'mind_flay'}
        ),

        'darkness': Talent(
            id='darkness', name='Darkness',
            description='Shadow spell crit chance increased by 1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'shadow_crit': 1}}
        ),
        'shadow_weaving': Talent(
            id='shadow_weaving', name='Shadow Weaving',
            description='Shadow damage stacks a debuff increasing damage by 2% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'shadow_stack': 0.02}}
        ),
        'shadow_power': Talent(
            id='shadow_power', name='Shadow Power',
            description='Shadow spell damage increased by 2% per rank.',
            max_rank=5, tier=3,
            effects={'damage_mod': {'shadow': 0.02}}
        ),
        'twisted_faith': Talent(
            id='twisted_faith', name='Twisted Faith',
            description='Spirit converted to spell power by 2% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'spirit_to_shadow': 0.02}}
        ),
        'misery': Talent(
            id='misery', name='Misery',
            description='Shadow DoT targets take 1% more spell damage per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'dot_vuln': 0.01}}
        ),
        'pain_and_suffering': Talent(
            id='pain_and_suffering', name='Pain and Suffering',
            description='Mind Flay refreshes Shadow Word: Pain per rank chance.',
            max_rank=5, tier=4,
            effects={'proc': {'chance': 20, 'effect': 'refresh_sw_pain'}}
        ),
    }
}


# =============================================================================
# RANGER TALENT TREES
# =============================================================================

RANGER_BEASTMASTERY = {
    'name': 'Beast Mastery',
    'description': 'Bond with nature and command animal companions.',
    'icon': '🐺',
    'talents': {
        'animal_bond': Talent(
            id='animal_bond', name='Animal Bond',
            description='Pet damage +4% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'pet_damage': 0.04}}
        ),
        'mend_pet': Talent(
            id='mend_pet', name='Mend Pet',
            description='Pet heals 3/5/8% HP per tick out of combat.',
            max_rank=3, tier=1,
            effects={'passive': 'mend_pet'}
        ),
        'wild_companion': Talent(
            id='wild_companion', name='Wild Companion',
            description='Pet gains +20% HP and damage.',
            max_rank=1, tier=2,
            effects={'passive': 'wild_companion'}
        ),
        'thick_hide': Talent(
            id='thick_hide', name='Thick Hide',
            description='Pet damage reduction +2% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'pet_damage_reduction': 0.02}}
        ),
        'bestial_wrath': Talent(
            id='bestial_wrath', name='Bestial Wrath',
            description='Active: Pet enrages, +50% damage for 15s. Costs 40 Focus. 60s CD.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'bestial_wrath'}
        ),
        'ferocity': Talent(
            id='ferocity', name='Ferocity',
            description='Pet crit chance +2% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'pet_crit': 0.02}}
        ),
        'spirit_bond': Talent(
            id='spirit_bond', name='Spirit Bond',
            description='Passive: you heal 2% HP when pet deals damage.',
            max_rank=1, tier=4,
            effects={'passive': 'spirit_bond'}
        ),
        'frenzy': Talent(
            id='frenzy', name='Frenzy',
            description='Pet attack speed +2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'pet_attack_speed': 0.02}}
        ),
        'stampede': Talent(
            id='stampede', name='Stampede',
            description='Active: Summon 3 spectral beasts for 15s. Costs 75 Focus. 180s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'stampede'}
        ),
    }
}

RANGER_MARKSMANSHIP = {
    'name': 'Marksmanship',
    'description': 'Deadly precision with ranged attacks.',
    'icon': '🏹',
    'talents': {
        'lethal_shots': Talent(
            id='lethal_shots', name='Lethal Shots',
            description='Ranged crit chance +1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'ranged_crit': 0.01}}
        ),
        'careful_aim': Talent(
            id='careful_aim', name='Careful Aim',
            description='Aimed Shot damage +3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'aimed_shot': 0.03}}
        ),
        'hawkeye': Talent(
            id='hawkeye', name='Hawkeye',
            description='+10% hit chance on all ranged attacks.',
            max_rank=1, tier=2,
            effects={'stat_bonus': {'ranged_hit': 0.10}}
        ),
        'barrage': Talent(
            id='barrage', name='Barrage',
            description='Multi-target attacks hit +1 target per 2 ranks.',
            max_rank=5, tier=2,
            effects={'passive': 'barrage'}
        ),
        'predators_mark': Talent(
            id='predators_mark', name="Predator's Mark",
            description="Hunter's Mark also reduces target armor by 15%.",
            max_rank=1, tier=3,
            effects={'passive': 'predators_mark'}
        ),
        'rapid_fire_mastery': Talent(
            id='rapid_fire_mastery', name='Rapid Fire Mastery',
            description='Rapid Fire grants +1 extra attack per 2 ranks (4-5 total).',
            max_rank=5, tier=3,
            effects={'passive': 'rapid_fire_mastery'}
        ),
        'trueshot_aura': Talent(
            id='trueshot_aura', name='Trueshot Aura',
            description='Passive: +10% ranged damage to you and group.',
            max_rank=1, tier=4,
            effects={'passive': 'trueshot_aura'}
        ),
        'master_marksman': Talent(
            id='master_marksman', name='Master Marksman',
            description='Focus generation +2 per rank per hit.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'focus_gen_bonus': 2}}
        ),
        'sniper_training': Talent(
            id='sniper_training', name='Sniper Training',
            description='Passive: attacks from stealth deal 2x damage + generate 30 Focus.',
            max_rank=1, tier=5,
            effects={'passive': 'sniper_training'}
        ),
    }
}

RANGER_SURVIVAL = {
    'name': 'Survival',
    'description': 'Traps, tracking, and wilderness survival.',
    'icon': '🌿',
    'talents': {
        'trap_mastery': Talent(
            id='trap_mastery', name='Trap Mastery',
            description='Trap damage +10% per rank.',
            max_rank=3, tier=1,
            effects={'damage_mod': {'trap': 0.10}}
        ),
        'survivalist': Talent(
            id='survivalist', name='Survivalist',
            description='HP regen +2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'hp_regen_pct': 0.02}}
        ),
        'explosive_trap': Talent(
            id='explosive_trap', name='Explosive Trap',
            description='Active: Place trap, next enemy takes int*4 fire damage. Costs 20 Focus.',
            max_rank=1, tier=2,
            effects={'skill_unlock': 'explosive_trap'}
        ),
        'improved_tracking': Talent(
            id='improved_tracking', name='Improved Tracking',
            description='Track success +5% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'track_bonus': 0.05}}
        ),
        'black_arrow': Talent(
            id='black_arrow', name='Black Arrow',
            description='Active: Shadow-infused shot with shadow DoT. Costs 30 Focus. 20s CD.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'black_arrow'}
        ),
        'resourcefulness': Talent(
            id='resourcefulness', name='Resourcefulness',
            description='Trap cooldowns -5% per rank.',
            max_rank=5, tier=3,
            effects={'passive': 'resourcefulness'}
        ),
        'camouflage_talent': Talent(
            id='camouflage_talent', name='Camouflage',
            description='Active: Stealth usable in combat for 1 round. Costs 35 Focus. 45s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'camouflage_talent'}
        ),
        'survival_instincts': Talent(
            id='survival_instincts', name='Survival Instincts',
            description='Damage reduction +1% per rank when below 40% HP.',
            max_rank=5, tier=4,
            effects={'passive': 'survival_instincts'}
        ),
        'wyvern_sting': Talent(
            id='wyvern_sting', name='Wyvern Sting',
            description='Active: Target sleeps for 3 rounds (breaks on damage). Costs 60 Focus. 120s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'wyvern_sting'}
        ),
    }
}

# =============================================================================
# BARD TALENT TREES
# =============================================================================

BARD_PERFORMANCE = {
    'name': 'Performance',
    'description': 'Inspire allies with powerful songs and music.',
    'icon': '🎵',
    'talents': {
        'improved_songs': Talent(
            id='improved_songs', name='Improved Songs',
            description='Song buff duration +5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'song_duration': 0.05}}
        ),
        'perfect_pitch': Talent(
            id='perfect_pitch', name='Perfect Pitch',
            description='Song buff strength +2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'song_strength': 0.02}}
        ),
        'inspiring_chorus': Talent(
            id='inspiring_chorus', name='Inspiring Chorus',
            description='Songs affect +1 additional target beyond normal range.',
            max_rank=1, tier=2,
            effects={'passive': 'inspiring_chorus'}
        ),
        'harmonics': Talent(
            id='harmonics', name='Harmonics',
            description='Inspiration generation from songs +10% per rank.',
            max_rank=5, tier=2,
            effects={'passive': 'harmonics'}
        ),
        'song_of_battle': Talent(
            id='song_of_battle', name='Song of Battle',
            description='Active: Song that gives +15% damage to group. Costs 3 Inspiration. 30s.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'song_of_battle'}
        ),
        'resonance': Talent(
            id='resonance', name='Resonance',
            description='Song effects linger 2s per rank after stopping.',
            max_rank=5, tier=3,
            effects={'passive': 'resonance'}
        ),
        'encore_mastery': Talent(
            id='encore_mastery', name='Encore Mastery',
            description='Encore costs 2 Inspiration instead of 3.',
            max_rank=1, tier=4,
            effects={'passive': 'encore_mastery'}
        ),
        'rhythm_mastery': Talent(
            id='rhythm_mastery', name='Rhythm Mastery',
            description='Song mana cost -3% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'song_mana_cost': -0.03}}
        ),
        'finale': Talent(
            id='finale', name='Finale',
            description='Active: End song with massive effect (heal/damage/buff). Costs 7 Inspiration. 60s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'finale'}
        ),
    }
}

BARD_LORE = {
    'name': 'Lore',
    'description': 'Knowledge is power - utility and wisdom.',
    'icon': '📚',
    'talents': {
        'jack_of_trades': Talent(
            id='jack_of_trades', name='Jack of All Trades',
            description='All skill checks +1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'skill_bonus': 0.01}}
        ),
        'quick_study': Talent(
            id='quick_study', name='Quick Study',
            description='XP gain +2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'xp_bonus': 0.02}}
        ),
        'identify_talent': Talent(
            id='identify_talent', name='Identify',
            description='Active: Identify any item\'s full stats. Costs 1 Inspiration.',
            max_rank=1, tier=2,
            effects={'skill_unlock': 'identify_talent'}
        ),
        'encyclopedic': Talent(
            id='encyclopedic', name='Encyclopedic',
            description='Lore checks +3% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'lore_bonus': 0.03}}
        ),
        'legend_lore': Talent(
            id='legend_lore', name='Legend Lore',
            description='Active: Reveal mob weaknesses. Costs 2 Inspiration.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'legend_lore'}
        ),
        'magical_insight': Talent(
            id='magical_insight', name='Magical Insight',
            description='Spell resistance +2% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'spell_resistance': 0.02}}
        ),
        'arcane_knowledge': Talent(
            id='arcane_knowledge', name='Arcane Knowledge',
            description='Passive: can use scrolls regardless of class restrictions.',
            max_rank=1, tier=4,
            effects={'passive': 'arcane_knowledge'}
        ),
        'sage_wisdom': Talent(
            id='sage_wisdom', name='Sage Wisdom',
            description='Mana regen +2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'mana_regen_pct': 0.02}}
        ),
        'polymorph': Talent(
            id='polymorph', name='Polymorph',
            description='Active: Transform target into sheep for 3 rounds. Costs 6 Inspiration. 120s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'polymorph'}
        ),
    }
}

BARD_TRICKSTER = {
    'name': 'Trickster',
    'description': 'Misdirection, illusions, and cunning tricks.',
    'icon': '🎭',
    'talents': {
        'silver_tongue': Talent(
            id='silver_tongue', name='Silver Tongue',
            description='Charm/mesmerize success +10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'charm_bonus': 0.10}}
        ),
        'misdirection_bard': Talent(
            id='misdirection_bard', name='Misdirection',
            description='Enemy hit chance vs you -1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'dodge_bonus': 0.01}}
        ),
        'mesmerize_talent': Talent(
            id='mesmerize_talent', name='Mesmerize',
            description='Active: Mesmerize target (skip 1 round). Costs 2 Inspiration. 20s CD.',
            max_rank=1, tier=2,
            effects={'skill_unlock': 'mesmerize_talent'}
        ),
        'sleight_of_hand': Talent(
            id='sleight_of_hand', name='Sleight of Hand',
            description='Steal/pick lock +3% per rank.',
            max_rank=5, tier=2,
            effects={'stat_bonus': {'steal_bonus': 0.03}}
        ),
        'discordant_mastery': Talent(
            id='discordant_mastery', name='Discordant Mastery',
            description='Discordant Note silence duration +1 round.',
            max_rank=1, tier=3,
            effects={'passive': 'discordant_mastery'}
        ),
        'bewilderment': Talent(
            id='bewilderment', name='Bewilderment',
            description='Confused/mesmerized targets take 2% more damage per rank.',
            max_rank=5, tier=3,
            effects={'damage_mod': {'vs_confused': 0.02}}
        ),
        'mirror_image_bard': Talent(
            id='mirror_image_bard', name='Mirror Image',
            description='Active: Create 2 illusions, each absorbs 1 hit. Costs 4 Inspiration. 45s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'mirror_image_bard'}
        ),
        'puppet_master': Talent(
            id='puppet_master', name='Puppet Master',
            description='Charm duration +5% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'charm_duration': 0.05}}
        ),
        'grand_illusion': Talent(
            id='grand_illusion', name='Grand Illusion',
            description='Active: All enemies confused for 2 rounds. Costs 8 Inspiration. 120s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'grand_illusion'}
        ),
    }
}

# =============================================================================
# ASSASSIN TALENT TREES
# =============================================================================

ASSASSIN_LETHALITY = {
    'name': 'Lethality',
    'description': 'Maximum damage. Study your prey, strike with precision.',
    'icon': '🗡️',
    'talents': {
        # Tier 1 (0 points required)
        'ruthlessness': Talent(
            id='ruthlessness', name='Ruthlessness',
            description='Crit damage increased by 4% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'crit_damage': 4}}
        ),
        'serrated_blades': Talent(
            id='serrated_blades', name='Serrated Blades',
            description='Bleeds deal 10% more damage per rank.',
            max_rank=3, tier=1,
            effects={'damage_mod': {'bleed': 0.1}}
        ),
        # Tier 2 (5 points required)
        'adrenaline': Talent(
            id='adrenaline', name='Adrenaline',
            description='Killing a mob restores 20% of your max HP.',
            max_rank=1, tier=2, requires=['ruthlessness'],
            effects={'passive': 'adrenaline'}
        ),
        'intel_backstab': Talent(
            id='intel_backstab', name='Intel Backstab',
            description='Backstab from stealth grants +3 Intel instead of +1.',
            max_rank=1, tier=2, requires=['ruthlessness'],
            effects={'passive': 'intel_backstab'}
        ),
        # Tier 3 (10 points required)
        'improved_backstab': Talent(
            id='improved_backstab', name='Improved Backstab',
            description='Backstab damage increased by 5% per rank.',
            max_rank=5, tier=3,
            effects={'skill_mod': {'backstab': {'damage': 0.05}}}
        ),
        'kill_or_be_killed': Talent(
            id='kill_or_be_killed', name='Kill or Be Killed',
            description='Each Intel point grants +1% dodge chance.',
            max_rank=1, tier=3, requires=['intel_backstab'],
            effects={'passive': 'kill_or_be_killed'}
        ),
        # Tier 4 (15 points required)
        'cold_blood': Talent(
            id='cold_blood', name='Cold Blood',
            description='Unlocks: Next attack is a guaranteed critical hit.',
            max_rank=1, tier=4, requires=['improved_backstab'],
            effects={'skill_unlock': 'cold_blood'}
        ),
        'focused_attacks': Talent(
            id='focused_attacks', name='Focused Attacks',
            description='Crit chance increased by 1% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'crit_chance': 1}}
        ),
        # Tier 5 (20 points required)
        'death_from_above': Talent(
            id='death_from_above', name='Death from Above',
            description='Unlocks: Leap attack with massive damage.',
            max_rank=1, tier=5, requires=['cold_blood'],
            effects={'skill_unlock': 'death_from_above'}
        ),
    }
}

ASSASSIN_POISON = {
    'name': 'Poison',
    'description': 'Deadly toxins and debilitating venoms.',
    'icon': '🧪',
    'talents': {
        # Tier 1 (0 points required)
        'venom_coating': Talent(
            id='venom_coating', name='Venom Coating',
            description='Poison proc chance increased by 5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'poison_chance': 5}}
        ),
        'improved_poisons': Talent(
            id='improved_poisons', name='Improved Poisons',
            description='Poison damage increased by 3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'poison': 0.03}}
        ),
        # Tier 2 (5 points required)
        'numbing_toxin': Talent(
            id='numbing_toxin', name='Numbing Toxin',
            description='Poisoned targets deal 3/6/10% less damage to you.',
            max_rank=3, tier=2, requires=['venom_coating'],
            effects={'passive': 'numbing_toxin'}
        ),
        'quick_venom': Talent(
            id='quick_venom', name='Quick Venom',
            description='Poison application speed increased by 10% per rank.',
            max_rank=3, tier=2, requires=['venom_coating'],
            effects={'stat_bonus': {'poison_speed': 0.10}}
        ),
        # Tier 3 (10 points required)
        'leech_venom': Talent(
            id='leech_venom', name='Leech Venom',
            description='Poison ticks heal you for 15% of tick damage.',
            max_rank=1, tier=3, requires=['numbing_toxin'],
            effects={'passive': 'leech_venom'}
        ),
        'intel_from_poison': Talent(
            id='intel_from_poison', name='Intel from Poison',
            description='Poison ticks on marked target grant +1 Intel every 3 ticks.',
            max_rank=1, tier=3, requires=['numbing_toxin'],
            effects={'passive': 'intel_from_poison'}
        ),
        # Tier 4 (15 points required)
        'wound_poison': Talent(
            id='wound_poison', name='Wound Poison',
            description='Unlocks: Poison that reduces healing by 50%.',
            max_rank=1, tier=4, requires=['leech_venom'],
            effects={'skill_unlock': 'wound_poison'}
        ),
        'toxic_mastery': Talent(
            id='toxic_mastery', name='Toxic Mastery',
            description='All poison effects increased by 2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'poison_power': 0.02}}
        ),
        # Tier 5 (20 points required)
        'envenom': Talent(
            id='envenom', name='Envenom',
            description='Unlocks: Consume poison stacks for burst damage.',
            max_rank=1, tier=5, requires=['wound_poison'],
            effects={'skill_unlock': 'envenom'}
        ),
    }
}

ASSASSIN_SHADOW = {
    'name': 'Shadow',
    'description': 'Become one with darkness. Survive, evade, re-engage.',
    'icon': '🌑',
    'talents': {
        # Tier 1 (0 points required)
        'shadow_mastery': Talent(
            id='shadow_mastery', name='Shadow Mastery',
            description='Stealth cooldown reduced by 5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'stealth_cd': -0.05}}
        ),
        'improved_stealth': Talent(
            id='improved_stealth', name='Improved Stealth',
            description='Stealth detection range reduced by 3% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'stealth_range': -0.03}}
        ),
        # Tier 2 (5 points required)
        'slip_passive': Talent(
            id='slip_passive', name='Slip',
            description='5/10/15% chance to avoid boss special attacks.',
            max_rank=3, tier=2, requires=['shadow_mastery'],
            effects={'passive': 'slip_passive'}
        ),
        'shadow_focus': Talent(
            id='shadow_focus', name='Shadow Focus',
            description='Abilities from stealth cost 5% less energy per rank.',
            max_rank=3, tier=2, requires=['shadow_mastery'],
            effects={'stat_bonus': {'stealth_cost': -0.05}}
        ),
        # Tier 3 (10 points required)
        'ghost': Talent(
            id='ghost', name='Ghost',
            description='After taking a hit > 20% max HP, gain 50% dodge for 1 round.',
            max_rank=1, tier=3, requires=['slip_passive'],
            effects={'passive': 'ghost'}
        ),
        'shadow_mend': Talent(
            id='shadow_mend', name='Shadow Mend',
            description='Damage from stealth heals you for 10% of damage dealt.',
            max_rank=1, tier=3, requires=['slip_passive'],
            effects={'passive': 'shadow_mend'}
        ),
        # Tier 4 (15 points required)
        'deadly_patience': Talent(
            id='deadly_patience', name='Deadly Patience',
            description='While Intel >= 6, take 15% less damage.',
            max_rank=1, tier=4, requires=['ghost'],
            effects={'passive': 'deadly_patience'}
        ),
        'elusiveness': Talent(
            id='elusiveness', name='Elusiveness',
            description='Dodge chance increased by 1% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'dodge': 1}}
        ),
        # Tier 5 (20 points required)
        'shadow_blade': Talent(
            id='shadow_blade', name='Shadow Blade',
            description='Unlocks: +100% damage from stealth for 15s.',
            max_rank=1, tier=5, requires=['deadly_patience'],
            effects={'skill_unlock': 'shadow_blade'}
        ),
    }
}

# =============================================================================
# CLASS TALENT TREE MAPPING
# =============================================================================

# =============================================================================
# THIEF TALENT TREES (Wave 1 Rework - Luck/Scoundrel)
# =============================================================================

THIEF_FORTUNE = {
    'name': 'Fortune',
    'description': 'Master of luck and fortune. Generate and capitalize on Luck points.',
    'icon': '🎲',
    'talents': {
        'lucky_strikes': Talent(id='lucky_strikes', name='Lucky Strikes', description='Luck generation chance +3% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'luck_gen': 3}}),
        'gamblers_instinct': Talent(id='gamblers_instinct', name="Gambler's Instinct", description='Crit chance +1% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'crit_chance': 1}}),
        'loaded_dice': Talent(id='loaded_dice', name='Loaded Dice', description='Crits generate +2 Luck instead of +1.', max_rank=1, tier=2, requires=['lucky_strikes'], effects={'passive': 'loaded_dice'}),
        'fortune_favors': Talent(id='fortune_favors', name='Fortune Favors', description='Luck gain from dodge +1 per rank.', max_rank=3, tier=2, requires=['lucky_strikes'], effects={'stat_bonus': {'dodge_luck': 1}}),
        'lucky_break': Talent(id='lucky_break', name='Lucky Break', description='At Luck 10, next hit is auto-crit.', max_rank=1, tier=3, requires=['loaded_dice'], effects={'passive': 'lucky_break'}),
        'hot_streak': Talent(id='hot_streak', name='Hot Streak', description='Each consecutive Luck gain increases next gain chance by 2% per rank.', max_rank=5, tier=3, requires=['fortune_favors'], effects={'stat_bonus': {'streak_chance': 2}}),
        'second_chance': Talent(id='second_chance', name='Second Chance', description='Once per fight, fatal blow leaves you at 1 HP and grants 5 Luck.', max_rank=1, tier=4, requires=['lucky_break'], effects={'passive': 'second_chance'}),
        'fortune_wheel': Talent(id='fortune_wheel', name='Fortune Wheel', description='All Luck abilities cost 1 less Luck per 2 ranks (max -2).', max_rank=5, tier=4, requires=['hot_streak'], effects={'stat_bonus': {'luck_cost_reduction': 1}}),
        'jackpot_master': Talent(id='jackpot_master', name='Jackpot Master', description='Jackpot also stuns for 1 round and heals 10% HP.', max_rank=1, tier=5, requires=['second_chance', 'fortune_wheel'], effects={'passive': 'jackpot_master'}),
    }
}

THIEF_DIRTY_TRICKS = {
    'name': 'Dirty Tricks',
    'description': 'Control enemies with stuns, blinds, and underhanded tactics.',
    'icon': '💢',
    'talents': {
        'sucker_punch': Talent(id='sucker_punch', name='Sucker Punch', description='Stun duration from abilities +0.5s per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'stun_duration': 0.5}}),
        'street_smarts': Talent(id='street_smarts', name='Street Smarts', description='Resist stun/blind 5% per rank.', max_rank=3, tier=1, effects={'stat_bonus': {'cc_resist': 5}}),
        'cheap_shot': Talent(id='cheap_shot', name='Cheap Shot', description='Opening attack from stealth stuns for 1 round.', max_rank=1, tier=2, requires=['sucker_punch'], effects={'passive': 'cheap_shot'}),
        'dirty_fighting': Talent(id='dirty_fighting', name='Dirty Fighting', description='Pocket Sand blind duration +1 round per rank.', max_rank=3, tier=2, requires=['sucker_punch'], effects={'stat_bonus': {'blind_duration': 1}}),
        'con_artist': Talent(id='con_artist', name='Con Artist', description='Steal success rate +50%.', max_rank=1, tier=3, requires=['cheap_shot'], effects={'passive': 'con_artist'}),
        'slippery': Talent(id='slippery', name='Slippery', description='Dodge chance +1% per rank.', max_rank=5, tier=3, requires=['dirty_fighting'], effects={'stat_bonus': {'dodge': 1}}),
        'marked_man': Talent(id='marked_man', name='Marked Man', description='Low Blow target takes 10% more damage for 10s.', max_rank=1, tier=4, requires=['con_artist'], effects={'passive': 'marked_man'}),
        'escape_artist': Talent(id='escape_artist', name='Escape Artist', description='Chance to break free from stun/root +5% per rank.', max_rank=5, tier=4, requires=['slippery'], effects={'stat_bonus': {'cc_break': 5}}),
        'grand_heist': Talent(id='grand_heist', name='Grand Heist', description='Jackpot steals an item from target.', max_rank=1, tier=5, requires=['marked_man', 'escape_artist'], effects={'passive': 'grand_heist'}),
    }
}

THIEF_SUBTLETY_NEW = {
    'name': 'Subtlety',
    'description': 'Master of stealth, repositioning, and ambush tactics.',
    'icon': '🌑',
    'talents': {
        'shadow_walk': Talent(id='shadow_walk', name='Shadow Walk', description='Stealth movement speed +5% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'stealth_speed': 5}}),
        'light_fingers': Talent(id='light_fingers', name='Light Fingers', description='Pick lock/steal speed +5% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'steal_speed': 5}}),
        'vanishing_act': Talent(id='vanishing_act', name='Vanishing Act', description='After using Pocket Sand, enter stealth for 1 round.', max_rank=1, tier=2, requires=['shadow_walk'], effects={'passive': 'vanishing_act'}),
        'misdirection': Talent(id='misdirection', name='Misdirection', description='After dodge, 10/20/30% chance target attacks a different mob.', max_rank=3, tier=2, requires=['shadow_walk'], effects={'proc': {'chance': 10, 'effect': 'misdirection'}}),
        'shadowstep_thief': Talent(id='shadowstep_thief', name='Shadowstep', description='Teleport behind target.', max_rank=1, tier=3, requires=['vanishing_act'], effects={'skill_unlock': 'shadowstep_thief'}),
        'ambush_mastery': Talent(id='ambush_mastery', name='Ambush Mastery', description='Backstab damage from stealth +4% per rank.', max_rank=5, tier=3, requires=['misdirection'], effects={'skill_mod': {'backstab': {'damage': 0.04}}}),
        'cloak_and_dagger': Talent(id='cloak_and_dagger', name='Cloak and Dagger', description='Stealth attacks generate +2 Luck.', max_rank=1, tier=4, requires=['shadowstep_thief'], effects={'passive': 'cloak_and_dagger'}),
        'ghost_walk': Talent(id='ghost_walk', name='Ghost Walk', description='Detection range while stealthed -3% per rank.', max_rank=5, tier=4, requires=['ambush_mastery'], effects={'stat_bonus': {'stealth_range': -0.03}}),
        'shadow_dance': Talent(id='shadow_dance', name='Shadow Dance', description='For 15s, all attacks count as from stealth.', max_rank=1, tier=5, requires=['cloak_and_dagger', 'ghost_walk'], effects={'skill_unlock': 'shadow_dance'}),
    }
}

# =============================================================================
# NECROMANCER TALENT TREES (Wave 1 Rework - Soul Shards)
# =============================================================================

NECRO_UNHOLY_NEW = {
    'name': 'Unholy',
    'description': 'Command undead minions and spread disease. Soul Shards empower your dark army.',
    'icon': '💀',
    'talents': {
        'master_of_ghouls': Talent(id='master_of_ghouls', name='Master of Ghouls', description='Minion damage +4% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'minion_damage': 0.04}}),
        'unholy_might': Talent(id='unholy_might', name='Unholy Might', description='Shadow spell damage +2% per rank.', max_rank=5, tier=1, effects={'damage_mod': {'shadow': 0.02}}),
        'grave_pact': Talent(id='grave_pact', name='Grave Pact', description='Minion gains 50% of your Soul Shard damage bonus.', max_rank=1, tier=2, requires=['master_of_ghouls'], effects={'passive': 'grave_pact'}),
        'epidemic': Talent(id='epidemic', name='Epidemic', description='Disease spreads to 1/2/3 nearby enemies.', max_rank=3, tier=2, requires=['master_of_ghouls'], effects={'stat_bonus': {'disease_spread': 1}}),
        'ravenous_dead': Talent(id='ravenous_dead', name='Ravenous Dead', description='Minion kills grant you +1 Soul Shard.', max_rank=1, tier=3, requires=['grave_pact'], effects={'passive': 'ravenous_dead'}),
        'plague_mastery': Talent(id='plague_mastery', name='Plague Mastery', description='Disease damage +3% per rank.', max_rank=5, tier=3, requires=['epidemic'], effects={'damage_mod': {'disease': 0.03}}),
        'dark_transformation': Talent(id='dark_transformation', name='Dark Transformation', description='Transform minion: 2x damage, 2x HP for 30s.', max_rank=1, tier=4, requires=['ravenous_dead'], effects={'skill_unlock': 'dark_transformation'}),
        'desolation': Talent(id='desolation', name='Desolation', description='DoT damage +2% per rank.', max_rank=5, tier=4, requires=['plague_mastery'], effects={'damage_mod': {'dot': 0.02}}),
        'army_of_dead': Talent(id='army_of_dead', name='Army of the Dead', description='Summon 4 temporary minions for 20s. Costs 5 Shards.', max_rank=1, tier=5, requires=['dark_transformation', 'desolation'], effects={'skill_unlock': 'army_of_dead'}),
    }
}

NECRO_BLOOD_NEW = {
    'name': 'Blood',
    'description': 'Sustain yourself through life drain and blood magic.',
    'icon': '🩸',
    'talents': {
        'butchery': Talent(id='butchery', name='Butchery', description='Melee damage +2% per rank.', max_rank=5, tier=1, effects={'damage_mod': {'physical': 0.02}}),
        'scent_of_blood': Talent(id='scent_of_blood', name='Scent of Blood', description='Enemies below 25% HP take 5% more damage per rank.', max_rank=3, tier=1, effects={'damage_mod': {'vs_low_hp': 0.05}}),
        'blood_leech': Talent(id='blood_leech', name='Blood Leech', description='All damage heals you for 5% of damage dealt.', max_rank=1, tier=2, requires=['butchery'], effects={'passive': 'blood_leech'}),
        'improved_blood_presence': Talent(id='improved_blood_presence', name='Improved Blood Presence', description='Max HP +2% per rank.', max_rank=5, tier=2, requires=['butchery'], effects={'stat_bonus': {'max_hp': 0.02}}),
        'bone_armor_mastery': Talent(id='bone_armor_mastery', name='Bone Armor Mastery', description='Bone Shield absorbs 750 instead of 500 per hit.', max_rank=1, tier=3, requires=['blood_leech'], effects={'passive': 'bone_armor_mastery'}),
        'blood_gorged': Talent(id='blood_gorged', name='Blood-Gorged', description='Damage +1% per rank while above 80% HP.', max_rank=5, tier=3, requires=['improved_blood_presence'], effects={'damage_mod': {'all': 0.01}}),
        'vampiric_blood': Talent(id='vampiric_blood', name='Vampiric Blood', description='+30% max HP and +100% healing for 15s. 120s CD.', max_rank=1, tier=4, requires=['bone_armor_mastery'], effects={'skill_unlock': 'vampiric_blood'}),
        'will_of_the_necropolis': Talent(id='will_of_the_necropolis', name='Will of the Necropolis', description='Below 35% HP, take 3% less damage per rank.', max_rank=5, tier=4, requires=['blood_gorged'], effects={'stat_bonus': {'low_hp_dr': 0.03}}),
        'dancing_rune_weapon': Talent(id='dancing_rune_weapon', name='Dancing Rune Weapon', description='Shadow clone mirrors attacks for 15s. Costs 6 Shards.', max_rank=1, tier=5, requires=['vampiric_blood', 'will_of_the_necropolis'], effects={'skill_unlock': 'dancing_rune_weapon'}),
    }
}

NECRO_FROST_NEW = {
    'name': 'Frost',
    'description': 'Wield deathly cold for control and burst damage.',
    'icon': '❄️',
    'talents': {
        'icy_talons': Talent(id='icy_talons', name='Icy Talons', description='Attack speed +2% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'attack_speed': 0.02}}),
        'nerves_of_cold_steel': Talent(id='nerves_of_cold_steel', name='Nerves of Cold Steel', description='Frost spell damage +2% per rank.', max_rank=5, tier=1, effects={'damage_mod': {'frost': 0.02}}),
        'rime': Talent(id='rime', name='Rime', description='Frost spells have 15% chance to reset cooldowns.', max_rank=1, tier=2, requires=['icy_talons'], effects={'passive': 'rime'}),
        'improved_icy_touch': Talent(id='improved_icy_touch', name='Improved Icy Touch', description='Frost slow effect duration +10% per rank.', max_rank=5, tier=2, requires=['nerves_of_cold_steel'], effects={'stat_bonus': {'frost_slow': 0.10}}),
        'killing_machine': Talent(id='killing_machine', name='Killing Machine', description='Every 5th attack is a guaranteed crit.', max_rank=1, tier=3, requires=['rime'], effects={'passive': 'killing_machine'}),
        'howling_blast': Talent(id='howling_blast', name='Howling Blast', description='AoE frost damage +3% per rank.', max_rank=5, tier=3, requires=['improved_icy_touch'], effects={'damage_mod': {'frost_aoe': 0.03}}),
        'obliterate_talent': Talent(id='obliterate_talent', name='Obliterate', description='Massive frost strike, 3x weapon damage + frost. Costs 4 Shards. 30s CD.', max_rank=1, tier=4, requires=['killing_machine'], effects={'skill_unlock': 'obliterate'}),
        'merciless_combat': Talent(id='merciless_combat', name='Merciless Combat', description='Damage to targets below 35% HP +3% per rank.', max_rank=5, tier=4, requires=['howling_blast'], effects={'damage_mod': {'vs_low_hp': 0.03}}),
        'breath_of_sindragosa': Talent(id='breath_of_sindragosa', name='Breath of Sindragosa', description='Channel frost AoE, drains 1 Shard per round.', max_rank=1, tier=5, requires=['obliterate_talent', 'merciless_combat'], effects={'skill_unlock': 'breath_of_sindragosa'}),
    }
}

# =============================================================================
# PALADIN TALENT TREES (Wave 1 Rework - Holy Power/Oath)
# =============================================================================

PALADIN_HOLY_NEW = {
    'name': 'Holy',
    'description': 'Channel the Light to heal and support allies.',
    'icon': '✨',
    'talents': {
        'divine_strength': Talent(id='divine_strength', name='Divine Strength', description='Healing power +3% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'healing_power': 0.03}}),
        'divine_intellect': Talent(id='divine_intellect', name='Divine Intellect', description='Max mana +3% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'max_mana': 0.03}}),
        'illumination': Talent(id='illumination', name='Illumination', description='Heals have 15% chance to refund mana cost.', max_rank=1, tier=2, requires=['divine_strength'], effects={'passive': 'illumination'}),
        'healing_light': Talent(id='healing_light', name='Healing Light', description='Word of Glory heals 5% more per rank.', max_rank=3, tier=2, requires=['divine_strength'], effects={'stat_bonus': {'wog_bonus': 0.05}}),
        'holy_shock': Talent(id='holy_shock', name='Holy Shock', description='Instant damage or heal. Costs 2 Holy Power. 15s CD.', max_rank=1, tier=3, requires=['illumination'], effects={'skill_unlock': 'holy_shock'}),
        'sanctified_light': Talent(id='sanctified_light', name='Sanctified Light', description='Holy damage +2% per rank.', max_rank=5, tier=3, requires=['healing_light'], effects={'damage_mod': {'holy': 0.02}}),
        'divine_favor': Talent(id='divine_favor', name='Divine Favor', description='Next heal is guaranteed crit. Costs 1 Holy Power.', max_rank=1, tier=4, requires=['holy_shock'], effects={'skill_unlock': 'divine_favor'}),
        'infusion_of_light': Talent(id='infusion_of_light', name='Infusion of Light', description='Crit heals grant +1 Holy Power per 2 ranks.', max_rank=5, tier=4, requires=['sanctified_light'], effects={'stat_bonus': {'crit_heal_hp': 1}}),
        'beacon_of_light': Talent(id='beacon_of_light', name='Beacon of Light', description='Link to ally, they receive 30% of all healing you do for 60s.', max_rank=1, tier=5, requires=['divine_favor', 'infusion_of_light'], effects={'skill_unlock': 'beacon_of_light'}),
    }
}

PALADIN_PROTECTION_NEW = {
    'name': 'Protection',
    'description': 'Become an unbreakable shield of faith.',
    'icon': '🛡️',
    'talents': {
        'redoubt': Talent(id='redoubt', name='Redoubt', description='Block chance +2% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'block_chance': 2}}),
        'toughness': Talent(id='prot_toughness', name='Toughness', description='Max HP +2% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'max_hp': 0.02}}),
        'blessing_of_sanctuary': Talent(id='blessing_of_sanctuary', name='Blessing of Sanctuary', description='Reduce all damage taken by 5%.', max_rank=1, tier=2, requires=['redoubt'], effects={'damage_reduction': {'all': 0.05}}),
        'improved_devotion': Talent(id='improved_devotion', name='Improved Devotion', description='Devotion Oath damage reduction +3% per rank.', max_rank=3, tier=2, requires=['redoubt'], effects={'stat_bonus': {'devotion_dr': 0.03}}),
        'holy_shield': Talent(id='holy_shield', name='Holy Shield', description='Block all attacks for 6s. Costs 3 Holy Power. 60s CD.', max_rank=1, tier=3, requires=['blessing_of_sanctuary'], effects={'skill_unlock': 'holy_shield'}),
        'divine_resilience': Talent(id='divine_resilience', name='Divine Resilience', description='Damage reduction +1% per rank.', max_rank=5, tier=3, requires=['improved_devotion'], effects={'damage_reduction': {'all': 0.01}}),
        'ardent_defender': Talent(id='ardent_defender', name='Ardent Defender', description='Fatal blow heals to 20% HP (once per 5 min).', max_rank=1, tier=4, requires=['holy_shield'], effects={'passive': 'ardent_defender'}),
        'guarded_by_light': Talent(id='guarded_by_light', name='Guarded by the Light', description='Word of Glory also shields for 3% of heal per rank.', max_rank=5, tier=4, requires=['divine_resilience'], effects={'stat_bonus': {'wog_shield': 0.03}}),
        'divine_guardian': Talent(id='divine_guardian', name='Divine Guardian', description='Redirect 30% of group damage to you for 10s. Costs 5 Holy Power.', max_rank=1, tier=5, requires=['ardent_defender', 'guarded_by_light'], effects={'skill_unlock': 'divine_guardian'}),
    }
}

PALADIN_RETRIBUTION_NEW = {
    'name': 'Retribution',
    'description': 'Smite enemies with righteous fury and Holy Power.',
    'icon': '⚔️',
    'talents': {
        'benediction': Talent(id='benediction', name='Benediction', description='Holy Power generation chance +3% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'hp_gen': 3}}),
        'conviction': Talent(id='conviction', name='Conviction', description='Crit chance +1% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'crit_chance': 1}}),
        'vow_of_courage': Talent(id='vow_of_courage', name='Vow of Courage', description='Vengeance Oath damage bonus +5% extra.', max_rank=1, tier=2, requires=['benediction'], effects={'passive': 'vow_of_courage'}),
        'pursuit_of_justice': Talent(id='pursuit_of_justice', name='Pursuit of Justice', description='Movement speed +5% per rank.', max_rank=3, tier=2, requires=['benediction'], effects={'stat_bonus': {'move_speed': 0.05}}),
        'crusader_strike': Talent(id='crusader_strike', name='Crusader Strike', description='Melee attack that always generates +1 Holy Power.', max_rank=1, tier=3, requires=['vow_of_courage'], effects={'skill_unlock': 'crusader_strike'}),
        'sanctity_of_battle': Talent(id='sanctity_of_battle', name='Sanctity of Battle', description="Templar's Verdict damage +3% per rank.", max_rank=5, tier=3, requires=['pursuit_of_justice'], effects={'stat_bonus': {'tv_bonus': 0.03}}),
        'sanctified_wrath': Talent(id='sanctified_wrath', name='Sanctified Wrath', description="Templar's Verdict at 5 Holy Power deals 3x instead of 2x.", max_rank=1, tier=4, requires=['crusader_strike'], effects={'passive': 'sanctified_wrath'}),
        'fanaticism': Talent(id='fanaticism', name='Fanaticism', description='Holy damage +2% per rank.', max_rank=5, tier=4, requires=['sanctity_of_battle'], effects={'damage_mod': {'holy': 0.02}}),
        'avenging_wrath': Talent(id='avenging_wrath', name='Avenging Wrath', description='+30% damage and +30% crit for 20s. Costs 5 Holy Power. 180s CD.', max_rank=1, tier=5, requires=['sanctified_wrath', 'fanaticism'], effects={'skill_unlock': 'avenging_wrath'}),
    }
}

# =============================================================================
# CLERIC TALENT TREES (Wave 1 Rework - Faith System)
# =============================================================================

CLERIC_HOLY_NEW = {
    'name': 'Holy',
    'description': 'Channel divine light to heal and protect through Faith.',
    'icon': '✝️',
    'talents': {
        'healing_focus': Talent(id='healing_focus', name='Healing Focus', description='Healing power +3% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'healing_power': 0.03}}),
        'divine_fury': Talent(id='divine_fury', name='Divine Fury', description='Smite damage +5% per rank.', max_rank=3, tier=1, effects={'damage_mod': {'holy': 0.05}}),
        'inspiration': Talent(id='inspiration', name='Inspiration', description='Crit heals grant target 10% damage reduction for 6s.', max_rank=1, tier=2, requires=['healing_focus'], effects={'passive': 'inspiration'}),
        'spiritual_guidance': Talent(id='spiritual_guidance', name='Spiritual Guidance', description='Mana regen +3% per rank.', max_rank=5, tier=2, requires=['healing_focus'], effects={'stat_bonus': {'mana_regen': 0.03}}),
        'renew': Talent(id='renew', name='Renew', description='HoT: heals 5% max HP per tick for 4 ticks. Costs 2 Faith.', max_rank=1, tier=3, requires=['inspiration'], effects={'skill_unlock': 'renew'}),
        'holy_specialization': Talent(id='holy_specialization', name='Holy Specialization', description='Holy spell crit +1% per rank.', max_rank=5, tier=3, requires=['spiritual_guidance'], effects={'stat_bonus': {'holy_crit': 1}}),
        'guardian_spirit': Talent(id='guardian_spirit', name='Guardian Spirit', description='Target saved from death, heals to 40%. Costs 5 Faith. 120s CD.', max_rank=1, tier=4, requires=['renew'], effects={'skill_unlock': 'guardian_spirit'}),
        'empowered_healing': Talent(id='empowered_healing', name='Empowered Healing', description='All heals +2% per rank.', max_rank=5, tier=4, requires=['holy_specialization'], effects={'stat_bonus': {'healing_power': 0.02}}),
        'divine_hymn': Talent(id='divine_hymn', name='Divine Hymn', description='Channel AoE heal, 20% HP per round for 3 rounds. Costs 7 Faith.', max_rank=1, tier=5, requires=['guardian_spirit', 'empowered_healing'], effects={'skill_unlock': 'divine_hymn'}),
    }
}

CLERIC_DISCIPLINE_NEW = {
    'name': 'Discipline',
    'description': 'Prevent damage through shields and atonement.',
    'icon': '🛡️',
    'talents': {
        'improved_shields': Talent(id='improved_shields', name='Improved Shields', description='Shield absorb +4% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'shield_power': 0.04}}),
        'mental_agility': Talent(id='mental_agility', name='Mental Agility', description='Instant spell cost -2% per rank.', max_rank=5, tier=1, effects={'stat_bonus': {'instant_cost': -0.02}}),
        'atonement': Talent(id='atonement', name='Atonement', description='Dealing damage heals lowest HP ally for 50%.', max_rank=1, tier=2, requires=['improved_shields'], effects={'passive': 'atonement'}),
        'inner_focus': Talent(id='inner_focus', name='Inner Focus', description='Next spell costs no mana. 3/2/1 min CD per rank.', max_rank=3, tier=2, requires=['mental_agility'], effects={'skill_unlock': 'inner_focus'}),
        'power_word_shield': Talent(id='power_word_shield', name='Power Word: Shield', description='Shield = 30% of target max HP. Costs 3 Faith. 15s CD.', max_rank=1, tier=3, requires=['atonement'], effects={'skill_unlock': 'power_word_shield'}),
        'focused_will': Talent(id='focused_will', name='Focused Will', description='Taking damage grants +1% DR per rank (stacks 5x).', max_rank=5, tier=3, requires=['inner_focus'], effects={'stat_bonus': {'hit_dr': 0.01}}),
        'aegis_ward': Talent(id='aegis_ward', name='Aegis Ward', description='Party shield absorbing 15% of each HP. Costs 6 Faith. 60s CD.', max_rank=1, tier=4, requires=['power_word_shield'], effects={'skill_unlock': 'aegis_ward'}),
        'grace': Talent(id='grace', name='Grace', description='Consecutive heals on same target +2% per rank (stacks 3x).', max_rank=5, tier=4, requires=['focused_will'], effects={'stat_bonus': {'grace_heal': 0.02}}),
        'pain_suppression': Talent(id='pain_suppression', name='Pain Suppression', description='Target takes 40% less damage for 8s. Costs 8 Faith. 180s CD.', max_rank=1, tier=5, requires=['aegis_ward', 'grace'], effects={'skill_unlock': 'pain_suppression'}),
    }
}

CLERIC_SHADOW_NEW = {
    'name': 'Shadow',
    'description': 'Embrace darkness for devastating power. Damage builds Faith.',
    'icon': '🌑',
    'talents': {
        'shadow_focus_cleric': Talent(id='shadow_focus_cleric', name='Shadow Focus', description='Shadow damage +2% per rank.', max_rank=5, tier=1, effects={'damage_mod': {'shadow': 0.02}}),
        'darkness': Talent(id='darkness', name='Darkness', description='Shadow DoT damage +2% per rank.', max_rank=5, tier=1, effects={'damage_mod': {'shadow_dot': 0.02}}),
        'shadow_word_pain': Talent(id='shadow_word_pain', name='Shadow Word: Pain', description='Shadow DoT: int*2 per tick for 5 ticks. Costs 2 Faith.', max_rank=1, tier=2, requires=['shadow_focus_cleric'], effects={'skill_unlock': 'shadow_word_pain'}),
        'shadow_weaving': Talent(id='shadow_weaving', name='Shadow Weaving', description='Shadow spells reduce target shadow resist -5% per rank.', max_rank=3, tier=2, requires=['shadow_focus_cleric'], effects={'stat_bonus': {'shadow_pen': 5}}),
        'siphon_light': Talent(id='siphon_light', name='Siphon Light', description='Shadow damage heals you for 10%.', max_rank=1, tier=3, requires=['shadow_word_pain'], effects={'passive': 'siphon_light'}),
        'shadow_power': Talent(id='shadow_power', name='Shadow Power', description='Shadow spell damage +3% per rank (shadow form only).', max_rank=5, tier=3, requires=['shadow_weaving'], effects={'damage_mod': {'shadow': 0.03}}),
        'shadowform': Talent(id='shadowform', name='Shadowform', description='Toggle: +25% shadow damage, -30% healing, damage builds Faith.', max_rank=1, tier=4, requires=['siphon_light'], effects={'skill_unlock': 'shadowform'}),
        'misery': Talent(id='misery', name='Misery', description='Shadow DoTs increase all damage target takes by 1% per rank.', max_rank=5, tier=4, requires=['shadow_power'], effects={'stat_bonus': {'dot_vuln': 0.01}}),
        'mind_flay': Talent(id='mind_flay', name='Mind Flay', description='Channel: 3 ticks of int*4 damage, slows target. Costs 5 Faith.', max_rank=1, tier=5, requires=['shadowform', 'misery'], effects={'skill_unlock': 'mind_flay'}),
    }
}

CLASS_TALENT_TREES = {
    # Warrior uses Martial Doctrines + Ability Evolution instead of talent trees
    'mage': [MAGE_FIRE, MAGE_FROST, MAGE_ARCANE],
    'thief': [THIEF_FORTUNE, THIEF_DIRTY_TRICKS, THIEF_SUBTLETY_NEW],
    'cleric': [CLERIC_HOLY_NEW, CLERIC_DISCIPLINE_NEW, CLERIC_SHADOW_NEW],
    'ranger': [RANGER_BEASTMASTERY, RANGER_MARKSMANSHIP, RANGER_SURVIVAL],
    'paladin': [PALADIN_HOLY_NEW, PALADIN_PROTECTION_NEW, PALADIN_RETRIBUTION_NEW],
    'necromancer': [NECRO_UNHOLY_NEW, NECRO_BLOOD_NEW, NECRO_FROST_NEW],
    'bard': [BARD_PERFORMANCE, BARD_LORE, BARD_TRICKSTER],
    'assassin': [ASSASSIN_LETHALITY, ASSASSIN_POISON, ASSASSIN_SHADOW],
}

# Tree identity passives (earned at 25+ points in a single tree)
TREE_IDENTITY_PASSIVES = {
    # Warrior uses Martial Doctrines instead of talent trees
    'mage': {
        'Fire': 'fire_identity',
        'Frost': 'frost_identity',
        'Arcane': 'arcane_identity',
    },
    'thief': {
        'Fortune': 'fortune_identity',
        'Dirty Tricks': 'dirty_tricks_identity',
        'Subtlety': 'subtlety_identity',
    },
    'cleric': {
        'Holy': 'holy_identity',
        'Discipline': 'discipline_identity',
        'Shadow': 'shadow_identity',
    },
    'ranger': {
        'Beast Mastery': 'beast_identity',
        'Marksmanship': 'marks_identity',
        'Survival': 'survival_identity',
    },
    'paladin': {
        'Holy': 'paladin_holy_identity',
        'Protection': 'paladin_protection_identity',
        'Retribution': 'retribution_identity',
    },
    'necromancer': {
        'Unholy': 'unholy_identity',
        'Blood': 'blood_identity',
        'Frost': 'necromancer_frost_identity',
    },
    'bard': {
        'Performance': 'performance_identity',
        'Lore': 'lore_identity',
        'Trickster': 'trickster_identity',
    },
    'assassin': {
        'Lethality': 'lethality_identity',
        'Poison': 'poison_identity',
        'Shadow': 'assassin_shadow_identity',
    },
}


# =============================================================================
# TALENT MANAGER
# =============================================================================

class TalentManager:
    """Manages player talent trees."""
    
    @staticmethod
    def get_talent_points(player: 'Player') -> int:
        """Calculate total available talent points for a player."""
        # 1 point per level starting at level 5
        level = getattr(player, 'level', 1)
        return max(0, level - 4)
    
    @staticmethod
    def get_spent_points(player: 'Player') -> int:
        """Calculate total spent talent points."""
        talents = getattr(player, 'talents', {})
        return sum(talents.values())
    
    @staticmethod
    def get_available_points(player: 'Player') -> int:
        """Calculate unspent talent points."""
        return TalentManager.get_talent_points(player) - TalentManager.get_spent_points(player)
    
    @staticmethod
    def get_tree_points(player: 'Player', tree_name: str) -> int:
        """Get points spent in a specific tree."""
        talents = getattr(player, 'talents', {})
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        
        total = 0
        for tree in trees:
            if tree['name'].lower() == tree_name.lower():
                for talent_id, talent in tree['talents'].items():
                    total += talents.get(talent_id, 0)
                break
        return total

    @staticmethod
    def get_tree_identity(player: 'Player') -> Optional[str]:
        """Return the identity passive if player has 25+ points in a single tree."""
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        identity_map = TREE_IDENTITY_PASSIVES.get(char_class, {})
        for tree in trees:
            if TalentManager.get_tree_points(player, tree['name']) >= 25:
                return identity_map.get(tree['name'])
        return None

    @staticmethod
    def has_tree_identity(player: 'Player', identity_name: str) -> bool:
        """Check if player has a specific tree identity passive."""
        return TalentManager.get_tree_identity(player) == identity_name
    
    @staticmethod
    def can_learn_talent(player: 'Player', talent_id: str) -> tuple:
        """
        Check if player can learn a talent.
        Returns (can_learn: bool, reason: str)
        """
        # Get player's class trees
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        
        # Find the talent
        talent = None
        tree_name = None
        for tree in trees:
            if talent_id in tree['talents']:
                talent = tree['talents'][talent_id]
                tree_name = tree['name']
                break
        
        if not talent:
            return False, "Talent not found for your class."
        
        # Check available points
        if TalentManager.get_available_points(player) < 1:
            return False, "No talent points available."
        
        # Check current rank
        current_rank = getattr(player, 'talents', {}).get(talent_id, 0)
        if current_rank >= talent.max_rank:
            return False, "Already at maximum rank."
        
        # Check tier requirement (points in tree)
        tree_points = TalentManager.get_tree_points(player, tree_name)
        required_points = (talent.tier - 1) * 5  # Tier 1: 0, Tier 2: 5, etc.
        if tree_points < required_points:
            return False, f"Need {required_points} points in {tree_name} tree first."
        
        # Check prerequisites
        player_talents = getattr(player, 'talents', {})
        for prereq in talent.requires:
            if prereq not in player_talents or player_talents[prereq] < 1:
                # Find prereq name
                for tree in trees:
                    if prereq in tree['talents']:
                        prereq_name = tree['talents'][prereq].name
                        return False, f"Requires {prereq_name} first."
                return False, f"Missing prerequisite talent."
        
        return True, "OK"
    
    @staticmethod
    async def learn_talent(player: 'Player', talent_id: str) -> bool:
        """Learn or rank up a talent. Returns success."""
        can_learn, reason = TalentManager.can_learn_talent(player, talent_id)
        if not can_learn:
            c = player.config.COLORS
            await player.send(f"{c['red']}{reason}{c['reset']}")
            return False
        
        # Initialize talents dict if needed
        if not hasattr(player, 'talents'):
            player.talents = {}
        
        # Learn the talent
        current = player.talents.get(talent_id, 0)
        player.talents[talent_id] = current + 1
        
        # Find talent info for message
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        
        for tree in trees:
            if talent_id in tree['talents']:
                talent = tree['talents'][talent_id]
                c = player.config.COLORS
                new_rank = player.talents[talent_id]
                
                await player.send(f"\r\n{c['bright_green']}╔══════════════════════════════════════════════{c['reset']}")
                await player.send(f"{c['bright_green']}║{c['bright_yellow']}  ★ TALENT LEARNED! ★{c['reset']}")
                await player.send(f"{c['bright_green']}╠══════════════════════════════════════════════{c['reset']}")
                await player.send(f"{c['bright_green']}║{c['reset']}  {c['white']}{talent.name}{c['reset']}")
                if talent.max_rank > 1:
                    await player.send(f"{c['bright_green']}║{c['reset']}  {c['cyan']}Rank {new_rank}/{talent.max_rank}{c['reset']}")
                await player.send(f"{c['bright_green']}╚══════════════════════════════════════════════{c['reset']}\r\n")
                
                # Check for skill unlocks
                if 'skill_unlock' in talent.effects:
                    skill_name = talent.effects['skill_unlock']
                    player.skills[skill_name] = 75  # Start at 75% proficiency
                    await player.send(f"{c['bright_cyan']}New ability unlocked: {skill_name.replace('_', ' ').title()}!{c['reset']}")
                
                break

        # Achievement: talent tree mastery
        try:
            from achievements import AchievementManager
            await AchievementManager.check_talent_mastery(player)
        except Exception:
            pass

        return True
    
    @staticmethod
    def get_talent_rank(player: 'Player', talent_id: str) -> int:
        """Get the rank a player has in a specific talent."""
        return getattr(player, 'talents', {}).get(talent_id, 0)

    @staticmethod
    def has_talent(player: 'Player', talent_id: str) -> bool:
        """Check if player has at least 1 rank in a talent."""
        return TalentManager.get_talent_rank(player, talent_id) > 0

    @staticmethod
    def get_talent_bonus(player: 'Player', bonus_type: str, subtype: str = None) -> float:
        """
        Get cumulative bonus from talents.
        
        Examples:
            get_talent_bonus(player, 'damage_mod', 'fire') -> 0.15 (15% fire damage)
            get_talent_bonus(player, 'stat_bonus', 'crit_chance') -> 5
        """
        if not hasattr(player, 'talents'):
            return 0
        
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        total = 0
        
        for tree in trees:
            for talent_id, talent in tree['talents'].items():
                ranks = player.talents.get(talent_id, 0)
                if ranks <= 0:
                    continue
                
                effects = talent.effects
                if bonus_type in effects:
                    bonus_data = effects[bonus_type]
                    if isinstance(bonus_data, dict):
                        if subtype and subtype in bonus_data:
                            total += bonus_data[subtype] * ranks
                        elif 'all' in bonus_data:
                            total += bonus_data['all'] * ranks
                    else:
                        total += bonus_data * ranks
        
        return total
    
    @staticmethod
    def has_passive(player: 'Player', passive_name: str) -> bool:
        """Check if player has a specific passive talent."""
        if not hasattr(player, 'talents'):
            return False
        
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        
        for tree in trees:
            for talent_id, talent in tree['talents'].items():
                if player.talents.get(talent_id, 0) > 0:
                    if talent.effects.get('passive') == passive_name:
                        return True
        
        return False

    @staticmethod
    def has_maxed_tree(player: 'Player') -> bool:
        """Check if the player has maxed out all talents in any single tree."""
        if not hasattr(player, 'talents') or not player.talents:
            return False
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        for tree in trees:
            all_maxed = True
            if not tree['talents']:
                continue
            for talent_id, talent in tree['talents'].items():
                rank = player.talents.get(talent_id, 0)
                if rank < talent.max_rank:
                    all_maxed = False
                    break
            if all_maxed:
                return True
        return False

    @staticmethod
    def get_proc_chance(player: 'Player', effect_name: str) -> int:
        """Get total proc chance for a given effect name."""
        if not hasattr(player, 'talents'):
            return 0
        char_class = getattr(player, 'char_class', 'warrior').lower()
        trees = CLASS_TALENT_TREES.get(char_class, [])
        total = 0
        for tree in trees:
            for talent_id, talent in tree['talents'].items():
                ranks = player.talents.get(talent_id, 0)
                if ranks <= 0:
                    continue
                proc = talent.effects.get('proc')
                if isinstance(proc, dict) and proc.get('effect') == effect_name:
                    chance = proc.get('chance', 0)
                    total += chance
        return total
