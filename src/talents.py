"""
Talent Tree System for RealmsMUD

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

WARRIOR_PROTECTION = {
    'name': 'Protection',
    'description': 'Master of defense, protecting allies and absorbing damage.',
    'icon': '🛡️',
    'talents': {
        # Tier 1 (0 points required)
        'thick_skin': Talent(
            id='thick_skin',
            name='Thick Skin',
            description='Reduces physical damage taken by 2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_reduction': {'physical': 0.02}}
        ),
        'shield_mastery': Talent(
            id='shield_mastery',
            name='Shield Mastery',
            description='Increases block chance by 3% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'block_chance': 3}}
        ),
        # Tier 2 (5 points required)
        'shield_bash': Talent(
            id='shield_bash',
            name='Shield Bash',
            description='Unlocks Shield Bash: Stun and interrupt with your shield.',
            max_rank=1, tier=2,
            requires=['shield_mastery'],
            effects={'skill_unlock': 'shield_bash'}
        ),
        'improved_taunt': Talent(
            id='improved_taunt',
            name='Improved Taunt',
            description='Taunt now also reduces target damage by 10%.',
            max_rank=1, tier=2,
            requires=['thick_skin'],
            effects={'skill_mod': {'taunt': {'damage_reduction': 0.1}}}
        ),
        'last_stand': Talent(
            id='last_stand',
            name='Last Stand',
            description='When below 20% HP, gain 20% damage reduction.',
            max_rank=1, tier=2,
            effects={'passive': 'last_stand'}
        ),
        # Tier 3 (10 points required)
        'shield_wall': Talent(
            id='shield_wall',
            name='Shield Wall',
            description='Unlocks Shield Wall: Reduce all damage by 50% for 10 seconds.',
            max_rank=1, tier=3,
            requires=['shield_mastery'],
            effects={'skill_unlock': 'shield_wall'}
        ),
        'vigilance': Talent(
            id='vigilance',
            name='Vigilance',
            description='Reduce damage taken by allies within the room by 5%.',
            max_rank=1, tier=3,
            requires=['improved_taunt'],
            effects={'passive': 'vigilance'}
        ),
        'guardian_mark': Talent(
            id='guardian_mark',
            name='Guardian\'s Mark',
            description='Allies in the room take 8% less damage while you are fighting.',
            max_rank=1, tier=3,
            requires=['shield_bash'],
            effects={'passive': 'guardian_mark'}
        ),
        # Tier 4 (15 points required)
        'reflex_block': Talent(
            id='reflex_block',
            name='Reflex Block',
            description='Blocks 8% of incoming spells with a shield per rank.',
            max_rank=3, tier=4,
            requires=['guardian_mark'],
            effects={'stat_bonus': {'spell_block': 8}}
        ),
        'impenetrable': Talent(
            id='impenetrable',
            name='Impenetrable',
            description='Increases armor effectiveness by 15%.',
            max_rank=1, tier=4,
            requires=['shield_wall'],
            effects={'stat_bonus': {'armor_mult': 0.15}}
        ),
        # Tier 5 (20 points required) - Capstone
        'unbreakable': Talent(
            id='unbreakable',
            name='Unbreakable',
            description='Once per hour, survive a killing blow with 1 HP.',
            max_rank=1, tier=5,
            requires=['impenetrable', 'vigilance'],
            effects={'passive': 'unbreakable'}
        ),
    }
}

WARRIOR_FURY = {
    'name': 'Fury',
    'description': 'Unleash devastating attacks in a battle frenzy.',
    'icon': '🔥',
    'talents': {
        # Tier 1
        'blood_frenzy': Talent(
            id='blood_frenzy',
            name='Blood Frenzy',
            description='Increases damage by 2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'all': 0.02}}
        ),
        'endless_rage': Talent(
            id='endless_rage',
            name='Endless Rage',
            description='Rage generation increased by 10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'rage_gen': 0.1}}
        ),
        # Tier 2
        'rampage': Talent(
            id='rampage',
            name='Rampage',
            description='After a killing blow, next attack deals 25% more damage.',
            max_rank=1, tier=2,
            requires=['blood_frenzy'],
            effects={'passive': 'rampage'}
        ),
        'bloodthirst': Talent(
            id='bloodthirst',
            name='Bloodthirst',
            description='Heal for 3% of damage dealt.',
            max_rank=1, tier=2,
            requires=['endless_rage'],
            effects={'passive': 'bloodthirst'}
        ),
        'bloodlust': Talent(
            id='bloodlust',
            name='Bloodlust',
            description='Killing blows grant Bloodlust: +1% damage per stack (max 5).',
            max_rank=1, tier=2,
            requires=['bloodthirst'],
            effects={'passive': 'bloodlust'}
        ),
        # Tier 3
        'rend': Talent(
            id='rend',
            name='Rend',
            description='Unlocks Rend: Bleeding attack that deals damage over time.',
            max_rank=1, tier=3,
            requires=['bloodlust'],
            effects={'skill_unlock': 'rend'}
        ),
        'reckless_abandon': Talent(
            id='reckless_abandon',
            name='Reckless Abandon',
            description='While berserking, ignore 20% of enemy armor.',
            max_rank=1, tier=3,
            requires=['rampage'],
            effects={'passive': 'reckless_abandon'}
        ),
        'execute': Talent(
            id='execute',
            name='Execute',
            description='Unlocks Execute: Massive damage to enemies below 20% HP.',
            max_rank=1, tier=3,
            requires=['bloodthirst'],
            effects={'skill_unlock': 'execute'}
        ),
        # Tier 4
        'meat_cleaver': Talent(
            id='meat_cleaver',
            name='Meat Cleaver',
            description='Cleave now hits all enemies in the room.',
            max_rank=1, tier=4,
            requires=['reckless_abandon'],
            effects={'skill_mod': {'cleave': {'hits_all': True}}}
        ),
        # Tier 5 - Capstone
        'avatar_of_war': Talent(
            id='avatar_of_war',
            name='Avatar of War',
            description='Unlocks Avatar: +50% damage, +50% attack speed for 20 seconds.',
            max_rank=1, tier=5,
            requires=['meat_cleaver', 'execute'],
            effects={'skill_unlock': 'avatar_of_war'}
        ),
    }
}

WARRIOR_ARMS = {
    'name': 'Arms',
    'description': 'Master of weapons with precise, devastating strikes.',
    'icon': '⚔️',
    'talents': {
        # Tier 1
        'weapon_expertise': Talent(
            id='weapon_expertise',
            name='Weapon Expertise',
            description='Increases hit chance by 1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'hit_chance': 1}}
        ),
        'deep_wounds': Talent(
            id='deep_wounds',
            name='Deep Wounds',
            description='Critical hits cause bleeding for 4 seconds.',
            max_rank=3, tier=1,
            effects={'proc': {'on': 'crit', 'effect': 'bleed', 'duration': 4}}
        ),
        # Tier 2
        'tactical_mastery': Talent(
            id='tactical_mastery',
            name='Tactical Mastery',
            description='Retain rage when switching stances.',
            max_rank=1, tier=2,
            requires=['weapon_expertise'],
            effects={'passive': 'tactical_mastery'}
        ),
        'impale': Talent(
            id='impale',
            name='Impale',
            description='Critical hits deal 20% more damage.',
            max_rank=1, tier=2,
            requires=['deep_wounds'],
            effects={'stat_bonus': {'crit_damage': 20}}
        ),
        'sunder_armor': Talent(
            id='sunder_armor',
            name='Sunder Armor',
            description='Unlocks Sunder Armor: Reduce target armor for 3 rounds.',
            max_rank=1, tier=2,
            requires=['weapon_expertise'],
            effects={'skill_unlock': 'sunder_armor'}
        ),
        # Tier 3
        'overpower': Talent(
            id='overpower',
            name='Overpower',
            description='Unlocks Overpower: Quick strike after a miss or dodge.',
            max_rank=1, tier=3,
            requires=['sunder_armor'],
            effects={'skill_unlock': 'overpower'}
        ),
        'mortal_strike': Talent(
            id='mortal_strike',
            name='Mortal Strike',
            description='Unlocks Mortal Strike: Heavy hit that reduces healing received.',
            max_rank=1, tier=3,
            requires=['tactical_mastery'],
            effects={'skill_unlock': 'mortal_strike'}
        ),
        'second_wind': Talent(
            id='second_wind',
            name='Second Wind',
            description='Regenerate 5% HP when stunned or immobilized.',
            max_rank=1, tier=3,
            requires=['impale'],
            effects={'passive': 'second_wind'}
        ),
        # Tier 4
        'sword_specialization': Talent(
            id='sword_specialization',
            name='Sword Specialization',
            description='5% chance for an extra attack on hit.',
            max_rank=1, tier=4,
            requires=['mortal_strike'],
            effects={'proc': {'chance': 5, 'effect': 'extra_attack'}}
        ),
        # Tier 5 - Capstone
        'bladestorm': Talent(
            id='bladestorm',
            name='Bladestorm',
            description='Unlocks Bladestorm: Spin attacking all enemies for 6 seconds.',
            max_rank=1, tier=5,
            requires=['sword_specialization', 'second_wind'],
            effects={'skill_unlock': 'bladestorm'}
        ),
    }
}


# =============================================================================
# MAGE TALENT TREES
# =============================================================================

MAGE_FIRE = {
    'name': 'Fire',
    'description': 'Master of destructive flames and explosive power.',
    'icon': '🔥',
    'talents': {
        'burning_soul': Talent(
            id='burning_soul', name='Burning Soul',
            description='Increases fire damage by 3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'fire': 0.03}}
        ),
        'ignite': Talent(
            id='ignite', name='Ignite',
            description='Fire spells have 10% chance to ignite for extra damage.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 10, 'effect': 'ignite', 'damage': 0.2}}
        ),
        'flame_surge': Talent(
            id='flame_surge', name='Flame Surge',
            description='Fire spell crits reduce your next fire spell cast time.',
            max_rank=1, tier=1,
            effects={'passive': 'flame_surge'}
        ),
        'improved_fireball': Talent(
            id='improved_fireball', name='Improved Fireball',
            description='Fireball cast time reduced by 0.5 seconds.',
            max_rank=1, tier=2, requires=['burning_soul'],
            effects={'skill_mod': {'fireball': {'cast_time': -0.5}}}
        ),
        'pyroblast': Talent(
            id='pyroblast', name='Pyroblast',
            description='Unlocks Pyroblast: Massive fire damage with long cast.',
            max_rank=1, tier=3, requires=['improved_fireball'],
            effects={'skill_unlock': 'pyroblast'}
        ),
        'combustion': Talent(
            id='combustion', name='Combustion',
            description='Unlocks Combustion: +50% fire crit for 15 seconds.',
            max_rank=1, tier=4, requires=['pyroblast'],
            effects={'skill_unlock': 'combustion'}
        ),
        'cinders': Talent(
            id='cinders', name='Cinders',
            description='Enemies you kill with fire explode for minor area damage.',
            max_rank=1, tier=4, requires=['pyroblast'],
            effects={'passive': 'cinders'}
        ),
        'phoenix_flames': Talent(
            id='phoenix_flames', name='Phoenix Flames',
            description='On death, explode dealing fire damage and revive with 20% HP.',
            max_rank=1, tier=5, requires=['combustion', 'cinders'],
            effects={'passive': 'phoenix_flames'}
        ),
    }
}

MAGE_FROST = {
    'name': 'Frost',
    'description': 'Control the battlefield with ice and cold.',
    'icon': '❄️',
    'talents': {
        'frostbite': Talent(
            id='frostbite', name='Frostbite',
            description='Frost spells have 10% chance to freeze enemies.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 10, 'effect': 'freeze', 'duration': 2}}
        ),
        'piercing_cold': Talent(
            id='piercing_cold', name='Piercing Cold',
            description='Increases frost damage by 3% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'frost': 0.03}}
        ),
        'frozen_armor': Talent(
            id='frozen_armor', name='Frozen Armor',
            description='Attackers have a chance to be slowed when hitting you.',
            max_rank=1, tier=2,
            requires=['frostbite'],
            effects={'passive': 'frozen_armor'}
        ),
        'ice_barrier': Talent(
            id='ice_barrier', name='Ice Barrier',
            description='Unlocks Ice Barrier: Absorb damage shield.',
            max_rank=1, tier=2, requires=['frostbite'],
            effects={'skill_unlock': 'ice_barrier'}
        ),
        'shatter': Talent(
            id='shatter', name='Shatter',
            description='Frozen enemies take 50% more crit damage.',
            max_rank=1, tier=3, requires=['ice_barrier'],
            effects={'passive': 'shatter'}
        ),
        'ice_lance': Talent(
            id='ice_lance', name='Ice Lance',
            description='Unlocks Ice Lance: Instant cast, triple damage vs frozen.',
            max_rank=1, tier=4, requires=['shatter'],
            effects={'skill_unlock': 'ice_lance'}
        ),
        'cold_snap': Talent(
            id='cold_snap', name='Cold Snap',
            description='Unlocks Cold Snap: Refresh frost abilities once per fight.',
            max_rank=1, tier=4, requires=['shatter'],
            effects={'skill_unlock': 'cold_snap'}
        ),
        'deep_freeze': Talent(
            id='deep_freeze', name='Deep Freeze',
            description='Unlocks Deep Freeze: Stun frozen target for 5 seconds.',
            max_rank=1, tier=5, requires=['ice_lance', 'cold_snap'],
            effects={'skill_unlock': 'deep_freeze'}
        ),
    }
}

MAGE_ARCANE = {
    'name': 'Arcane',
    'description': 'Pure magical power and mana efficiency.',
    'icon': '✨',
    'talents': {
        'arcane_focus': Talent(
            id='arcane_focus', name='Arcane Focus',
            description='Reduces mana cost of spells by 2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'mana_cost_reduction': 0.02}}
        ),
        'arcane_concentration': Talent(
            id='arcane_concentration', name='Arcane Concentration',
            description='10% chance to make next spell free.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 10, 'effect': 'clearcast'}}
        ),
        'arcane_echo': Talent(
            id='arcane_echo', name='Arcane Echo',
            description='5% chance to echo a spell for 50% effect.',
            max_rank=1, tier=2,
            requires=['arcane_focus'],
            effects={'proc': {'chance': 5, 'effect': 'arcane_echo', 'mult': 0.5}}
        ),
        'arcane_missiles': Talent(
            id='arcane_missiles', name='Arcane Missiles',
            description='Unlocks Arcane Missiles: Channeled arcane damage.',
            max_rank=1, tier=2, requires=['arcane_focus'],
            effects={'skill_unlock': 'arcane_missiles'}
        ),
        'presence_of_mind': Talent(
            id='presence_of_mind', name='Presence of Mind',
            description='Unlocks: Make next spell instant cast.',
            max_rank=1, tier=3, requires=['arcane_missiles'],
            effects={'skill_unlock': 'presence_of_mind'}
        ),
        'arcane_power': Talent(
            id='arcane_power', name='Arcane Power',
            description='Unlocks: +30% damage, +30% mana cost for 15 seconds.',
            max_rank=1, tier=4, requires=['presence_of_mind'],
            effects={'skill_unlock': 'arcane_power'}
        ),
        'mana_rift': Talent(
            id='mana_rift', name='Mana Rift',
            description='Unlocks Mana Rift: Drain mana to deal heavy arcane damage.',
            max_rank=1, tier=4, requires=['arcane_power'],
            effects={'skill_unlock': 'mana_rift'}
        ),
        'arcane_mastery': Talent(
            id='arcane_mastery', name='Arcane Mastery',
            description='All spell damage increased by 10%.',
            max_rank=1, tier=5, requires=['arcane_power'],
            effects={'damage_mod': {'all': 0.1}}
        ),
    }
}


# =============================================================================
# THIEF TALENT TREES
# =============================================================================

THIEF_ASSASSINATION = {
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
    }
}

THIEF_COMBAT = {
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
    }
}

THIEF_SUBTLETY = {
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
    }
}


# =============================================================================
# CLERIC TALENT TREES
# =============================================================================

CLERIC_HOLY = {
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
    }
}

CLERIC_DISCIPLINE = {
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
    }
}

CLERIC_SHADOW = {
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
            description='Pet damage increased by 3% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'pet_damage': 0.03}}
        ),
        'mend_pet': Talent(
            id='mend_pet', name='Mend Pet',
            description='Pet healing effectiveness increased by 5% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'pet_healing': 0.05}}
        ),
        'wild_companion': Talent(
            id='wild_companion', name='Wild Companion',
            description='Your pets gain 10% max HP and damage.',
            max_rank=1, tier=2,
            requires=['animal_bond'],
            effects={'passive': 'wild_companion'}
        ),
        'bestial_wrath': Talent(
            id='bestial_wrath', name='Bestial Wrath',
            description='Unlocks: Pet enters rage, +50% damage for 10s.',
            max_rank=1, tier=3, requires=['animal_bond'],
            effects={'skill_unlock': 'bestial_wrath'}
        ),
        'spirit_bond': Talent(
            id='spirit_bond', name='Spirit Bond',
            description='You and pet regenerate 2% HP every 5 seconds.',
            max_rank=1, tier=4, requires=['bestial_wrath'],
            effects={'passive': 'spirit_bond'}
        ),
        'stampede': Talent(
            id='stampede', name='Stampede',
            description='Unlocks: Summon all your pets to attack.',
            max_rank=1, tier=5, requires=['spirit_bond'],
            effects={'skill_unlock': 'stampede'}
        ),
    }
}

RANGER_MARKSMANSHIP = {
    'name': 'Marksmanship',
    'description': 'Deadly precision with ranged weapons.',
    'icon': '🏹',
    'talents': {
        'lethal_shots': Talent(
            id='lethal_shots', name='Lethal Shots',
            description='Ranged crit chance increased by 1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'ranged_crit': 1}}
        ),
        'hawkeye': Talent(
            id='hawkeye', name='Hawkeye',
            description='Ranged hit chance increased by 2% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'ranged_hit': 2}}
        ),
        'careful_aim': Talent(
            id='careful_aim', name='Careful Aim',
            description='Ranged damage increased by 2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'ranged': 0.02}}
        ),
        'aimed_shot': Talent(
            id='aimed_shot', name='Aimed Shot',
            description='Unlocks: Powerful shot with bonus crit damage.',
            max_rank=1, tier=2, requires=['careful_aim'],
            effects={'skill_unlock': 'aimed_shot'}
        ),
        'predators_mark': Talent(
            id='predators_mark', name='Predator\'s Mark',
            description='Unlocks Predator\'s Mark: Track and deal extra damage to marked target.',
            max_rank=1, tier=3, requires=['aimed_shot'],
            effects={'skill_unlock': 'predators_mark'}
        ),
        'trueshot_aura': Talent(
            id='trueshot_aura', name='Trueshot Aura',
            description='Increases ranged attack power by 10%.',
            max_rank=1, tier=4, requires=['aimed_shot'],
            effects={'passive': 'trueshot_aura'}
        ),
        'sniper_training': Talent(
            id='sniper_training', name='Sniper Training',
            description='Standing still increases damage by 5% per second.',
            max_rank=1, tier=5, requires=['trueshot_aura'],
            effects={'passive': 'sniper_training'}
        ),
    }
}

RANGER_SURVIVAL = {
    'name': 'Survival',
    'description': 'Traps, poisons, and wilderness expertise.',
    'icon': '🪤',
    'talents': {
        'trap_mastery': Talent(
            id='trap_mastery', name='Trap Mastery',
            description='Trap damage and duration increased by 10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'trap_power': 0.1}}
        ),
        'survivalist': Talent(
            id='survivalist', name='Survivalist',
            description='Max HP increased by 2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'max_hp': 0.02}}
        ),
        'explosive_trap': Talent(
            id='explosive_trap', name='Explosive Trap',
            description='Unlocks: Fire trap that damages all enemies.',
            max_rank=1, tier=2, requires=['trap_mastery'],
            effects={'skill_unlock': 'explosive_trap'}
        ),
        'black_arrow': Talent(
            id='black_arrow', name='Black Arrow',
            description='Unlocks: Poisoned arrow with DoT damage.',
            max_rank=1, tier=3, requires=['explosive_trap'],
            effects={'skill_unlock': 'black_arrow'}
        ),
        # Tier 4 (15 points required)
        'camouflage': Talent(
            id='camouflage', name='Camouflage',
            description='Unlocks: Become invisible while stationary.',
            max_rank=1, tier=4, requires=['black_arrow'],
            effects={'skill_unlock': 'camouflage'}
        ),
        'entrapment': Talent(
            id='entrapment', name='Entrapment',
            description='Traps root targets for 3 seconds.',
            max_rank=1, tier=4, requires=['black_arrow'],
            effects={'passive': 'entrapment'}
        ),
        # Tier 5 (20 points required)
        'wyvern_sting': Talent(
            id='wyvern_sting', name='Wyvern Sting',
            description='Unlocks: Puts target to sleep for 8 seconds.',
            max_rank=1, tier=5, requires=['camouflage'],
            effects={'skill_unlock': 'wyvern_sting'}
        ),
    }
}

# =============================================================================
# PALADIN TALENT TREES
# =============================================================================

PALADIN_HOLY = {
    'name': 'Holy',
    'description': 'Channel the Light to heal and protect.',
    'icon': '✨',
    'talents': {
        'divine_strength': Talent(
            id='divine_strength', name='Divine Strength',
            description='Strength increased by 2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'str_mult': 0.02}}
        ),
        'illumination': Talent(
            id='illumination', name='Illumination',
            description='Crit heals restore 30% mana cost.',
            max_rank=1, tier=2, requires=['divine_strength'],
            effects={'passive': 'illumination'}
        ),
        'holy_shock': Talent(
            id='holy_shock', name='Holy Shock',
            description='Unlocks: Instant heal or damage spell.',
            max_rank=1, tier=3, requires=['illumination'],
            effects={'skill_unlock': 'holy_shock'}
        ),
        # Tier 4 (15 points required)
        'divine_favor': Talent(
            id='divine_favor', name='Divine Favor',
            description='Unlocks: Next heal is guaranteed crit.',
            max_rank=1, tier=4, requires=['holy_shock'],
            effects={'skill_unlock': 'divine_favor'}
        ),
        'holy_light_mastery': Talent(
            id='holy_light_mastery', name='Holy Light Mastery',
            description='Holy Light heals for 15% more.',
            max_rank=3, tier=4, requires=['holy_shock'],
            effects={'heal_bonus': {'holy_light': 0.05}}
        ),
        # Tier 5 (20 points required)
        'beacon_of_light': Talent(
            id='beacon_of_light', name='Beacon of Light',
            description='Unlocks: Heals on target also heal beacon.',
            max_rank=1, tier=5, requires=['divine_favor'],
            effects={'skill_unlock': 'beacon_of_light'}
        ),
    }
}

PALADIN_PROTECTION = {
    'name': 'Protection',
    'description': 'Become an unbreakable shield of faith.',
    'icon': '🛡️',
    'talents': {
        'redoubt': Talent(
            id='redoubt', name='Redoubt',
            description='Block chance increased by 2% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'block_chance': 2}}
        ),
        'blessing_of_sanctuary': Talent(
            id='blessing_of_sanctuary', name='Blessing of Sanctuary',
            description='Reduce damage taken by 3%.',
            max_rank=1, tier=2, requires=['redoubt'],
            effects={'damage_reduction': {'all': 0.03}}
        ),
        'holy_shield': Talent(
            id='holy_shield', name='Holy Shield',
            description='Unlocks: Increased block and holy damage.',
            max_rank=1, tier=3, requires=['blessing_of_sanctuary'],
            effects={'skill_unlock': 'holy_shield'}
        ),
        'sacred_shield': Talent(
            id='sacred_shield', name='Sacred Shield',
            description='Unlocks: Shield yourself or ally, reflecting holy damage.',
            max_rank=1, tier=4, requires=['holy_shield'],
            effects={'skill_unlock': 'sacred_shield'}
        ),
        'ardent_defender': Talent(
            id='ardent_defender', name='Ardent Defender',
            description='Below 35% HP, damage reduced by 20%.',
            max_rank=1, tier=4, requires=['holy_shield'],
            effects={'passive': 'ardent_defender'}
        ),
        'divine_guardian': Talent(
            id='divine_guardian', name='Divine Guardian',
            description='Unlocks: Redirect 30% of party damage to you.',
            max_rank=1, tier=5, requires=['ardent_defender'],
            effects={'skill_unlock': 'divine_guardian'}
        ),
    }
}

PALADIN_RETRIBUTION = {
    'name': 'Retribution',
    'description': 'Smite enemies with righteous fury.',
    'icon': '⚔️',
    'talents': {
        'benediction': Talent(
            id='benediction', name='Benediction',
            description='Reduces mana cost of seals by 3% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'seal_cost': -0.03}}
        ),
        'vow_of_courage': Talent(
            id='vow_of_courage', name='Vow of Courage',
            description='Reduces fear effects and increases damage to undead by 10%.',
            max_rank=1, tier=2,
            requires=['benediction'],
            effects={'passive': 'vow_of_courage'}
        ),
        'judgment': Talent(
            id='judgment', name='Judgment',
            description='Unlocks Judgment: Ranged holy strike that debuffs target.',
            max_rank=1, tier=2,
            requires=['benediction'],
            effects={'skill_unlock': 'judgment'}
        ),
        'seal_of_command': Talent(
            id='seal_of_command', name='Seal of Command',
            description='Unlocks: Chance for extra holy damage on hit.',
            max_rank=1, tier=2, requires=['benediction'],
            effects={'skill_unlock': 'seal_of_command'}
        ),
        'crusader_strike': Talent(
            id='crusader_strike', name='Crusader Strike',
            description='Unlocks: Instant weapon strike.',
            max_rank=1, tier=3, requires=['seal_of_command'],
            effects={'skill_unlock': 'crusader_strike'}
        ),
        # Tier 4 (15 points required)
        'sanctified_wrath': Talent(
            id='sanctified_wrath', name='Sanctified Wrath',
            description='Crit chance with holy abilities increased by 5% per rank.',
            max_rank=3, tier=4, requires=['crusader_strike'],
            effects={'stat_bonus': {'holy_crit': 5}}
        ),
        'hammer_of_wrath': Talent(
            id='hammer_of_wrath', name='Hammer of Wrath',
            description='Unlocks: Ranged execute usable below 20% HP.',
            max_rank=1, tier=4, requires=['crusader_strike'],
            effects={'skill_unlock': 'hammer_of_wrath'}
        ),
        # Tier 5 (20 points required)
        'divine_storm': Talent(
            id='divine_storm', name='Divine Storm',
            description='Unlocks: Whirlwind attack with holy damage.',
            max_rank=1, tier=5, requires=['crusader_strike'],
            effects={'skill_unlock': 'divine_storm'}
        ),
    }
}

# =============================================================================
# NECROMANCER TALENT TREES
# =============================================================================

NECRO_UNHOLY = {
    'name': 'Unholy',
    'description': 'Command undead minions and spread disease.',
    'icon': '💀',
    'talents': {
        'master_of_ghouls': Talent(
            id='master_of_ghouls', name='Master of Ghouls',
            description='Ghoul damage increased by 4% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'minion_damage': 0.04}}
        ),
        'grave_pact': Talent(
            id='grave_pact', name='Grave Pact',
            description='Undead pets gain bonus stats from your INT.',
            max_rank=1, tier=2,
            requires=['master_of_ghouls'],
            effects={'passive': 'grave_pact'}
        ),
        'corpse_explosion': Talent(
            id='corpse_explosion', name='Corpse Explosion',
            description='Unlocks: Explode corpses for AoE damage.',
            max_rank=1, tier=2, requires=['master_of_ghouls'],
            effects={'skill_unlock': 'corpse_explosion'}
        ),
        # Tier 3 (10 points required)
        'plague_strike': Talent(
            id='plague_strike', name='Plague Strike',
            description='Unlocks: Strike that spreads disease.',
            max_rank=1, tier=3, requires=['corpse_explosion'],
            effects={'skill_unlock': 'plague_strike'}
        ),
        'virulence': Talent(
            id='virulence', name='Virulence',
            description='Disease damage increased by 5% per rank.',
            max_rank=3, tier=3, requires=['corpse_explosion'],
            effects={'damage_mod': {'disease': 0.05}}
        ),
        # Tier 4 (15 points required)
        'summon_gargoyle': Talent(
            id='summon_gargoyle', name='Summon Gargoyle',
            description='Unlocks: Summon a gargoyle to attack enemies.',
            max_rank=1, tier=4, requires=['plague_strike'],
            effects={'skill_unlock': 'summon_gargoyle'}
        ),
        'dark_transformation': Talent(
            id='dark_transformation', name='Dark Transformation',
            description='Unlocks: Transform your ghoul into a monster.',
            max_rank=1, tier=4, requires=['plague_strike'],
            effects={'skill_unlock': 'dark_transformation'}
        ),
        # Tier 5 (20 points required)
        'army_of_dead': Talent(
            id='army_of_dead', name='Army of the Dead',
            description='Unlocks: Summon army of ghouls.',
            max_rank=1, tier=5, requires=['summon_gargoyle'],
            effects={'skill_unlock': 'army_of_dead'}
        ),
        'raise_abomination': Talent(
            id='raise_abomination', name='Raise Abomination',
            description='Unlocks: Raise a towering abomination from a corpse.',
            max_rank=1, tier=5, requires=['army_of_dead'],
            effects={'skill_unlock': 'raise_abomination'}
        ),
    }
}

NECRO_BLOOD = {
    'name': 'Blood',
    'description': 'Drain life force and empower yourself.',
    'icon': '🩸',
    'talents': {
        'butchery': Talent(
            id='butchery', name='Butchery',
            description='Generate extra essence on kills.',
            max_rank=3, tier=1,
            effects={'passive': 'butchery'}
        ),
        'blood_boil': Talent(
            id='blood_boil', name='Blood Boil',
            description='Unlocks: AoE disease damage.',
            max_rank=1, tier=2, requires=['butchery'],
            effects={'skill_unlock': 'blood_boil'}
        ),
        'bone_armor': Talent(
            id='bone_armor', name='Bone Armor',
            description='Unlocks: Consume a corpse to gain a damage shield.',
            max_rank=1, tier=3, requires=['blood_boil'],
            effects={'skill_unlock': 'bone_armor'}
        ),
        'vampiric_blood': Talent(
            id='vampiric_blood', name='Vampiric Blood',
            description='Unlocks: +15% max HP and healing for 10s.',
            max_rank=1, tier=4, requires=['bone_armor'],
            effects={'skill_unlock': 'vampiric_blood'}
        ),
        # Tier 5 (20 points required)
        'blood_tap': Talent(
            id='blood_tap', name='Blood Tap',
            description='Unlocks: Sacrifice HP to gain essence.',
            max_rank=1, tier=5, requires=['vampiric_blood'],
            effects={'skill_unlock': 'blood_tap'}
        ),
        'dancing_rune_weapon': Talent(
            id='dancing_rune_weapon', name='Dancing Rune Weapon',
            description='Unlocks: Summon weapon that mirrors your attacks.',
            max_rank=1, tier=5, requires=['vampiric_blood'],
            effects={'skill_unlock': 'dancing_rune_weapon'}
        ),
    }
}

NECRO_FROST = {
    'name': 'Frost',
    'description': 'Wield deathly cold and icy runes.',
    'icon': '❄️',
    'talents': {
        'icy_talons': Talent(
            id='icy_talons', name='Icy Talons',
            description='Attack speed increased by 4% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'attack_speed': 0.04}}
        ),
        'howling_blast': Talent(
            id='howling_blast', name='Howling Blast',
            description='Unlocks: Frost AoE that applies chill.',
            max_rank=1, tier=2, requires=['icy_talons'],
            effects={'skill_unlock': 'howling_blast'}
        ),
        # Tier 3 (10 points required)
        'frost_strike': Talent(
            id='frost_strike', name='Frost Strike',
            description='Unlocks: Icy weapon strike.',
            max_rank=1, tier=3, requires=['howling_blast'],
            effects={'skill_unlock': 'frost_strike'}
        ),
        'rime': Talent(
            id='rime', name='Rime',
            description='Obliterate has 15% chance to make Howling Blast free.',
            max_rank=3, tier=3, requires=['howling_blast'],
            effects={'passive': 'rime'}
        ),
        # Tier 4 (15 points required)
        'obliterate': Talent(
            id='obliterate', name='Obliterate',
            description='Unlocks: Massive frost strike.',
            max_rank=1, tier=4, requires=['frost_strike'],
            effects={'skill_unlock': 'obliterate'}
        ),
        # Tier 5 (20 points required)
        'pillar_of_frost': Talent(
            id='pillar_of_frost', name='Pillar of Frost',
            description='Unlocks: +20% strength for 20 seconds.',
            max_rank=1, tier=5, requires=['obliterate'],
            effects={'skill_unlock': 'pillar_of_frost'}
        ),
        'breath_of_sindragosa': Talent(
            id='breath_of_sindragosa', name='Breath of Sindragosa',
            description='Unlocks: Channel frost breath that drains essence.',
            max_rank=1, tier=5, requires=['obliterate'],
            effects={'skill_unlock': 'breath_of_sindragosa'}
        ),
    }
}

# =============================================================================
# BARD TALENT TREES
# =============================================================================

BARD_PERFORMANCE = {
    'name': 'Performance',
    'description': 'Inspire allies with songs and music.',
    'icon': '🎵',
    'talents': {
        'improved_songs': Talent(
            id='improved_songs', name='Improved Songs',
            description='Song effects increased by 3% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'song_power': 0.03}}
        ),
        'inspiring_chorus': Talent(
            id='inspiring_chorus', name='Inspiring Chorus',
            description='While performing, allies regenerate 1% HP per tick.',
            max_rank=1, tier=2,
            requires=['improved_songs'],
            effects={'passive': 'inspiring_chorus'}
        ),
        'song_of_battle': Talent(
            id='song_of_battle', name='Song of Battle',
            description='Unlocks: Increase party damage by 10%.',
            max_rank=1, tier=2, requires=['improved_songs'],
            effects={'skill_unlock': 'song_of_battle'}
        ),
        'anthem_of_defense': Talent(
            id='anthem_of_defense', name='Anthem of Defense',
            description='Unlocks: Reduce party damage taken by 10%.',
            max_rank=1, tier=3, requires=['song_of_battle'],
            effects={'skill_unlock': 'anthem_of_defense'}
        ),
        'encore_mastery': Talent(
            id='encore_mastery', name='Encore Mastery',
            description='Encore duration doubled and costs reduced.',
            max_rank=1, tier=4, requires=['anthem_of_defense'],
            effects={'passive': 'encore_mastery'}
        ),
        'finale': Talent(
            id='finale', name='Finale',
            description='Unlocks: Powerful finisher based on active song.',
            max_rank=1, tier=5, requires=['anthem_of_defense'],
            effects={'skill_unlock': 'finale'}
        ),
    }
}

BARD_LORE = {
    'name': 'Lore',
    'description': 'Ancient knowledge and magical secrets.',
    'icon': '📚',
    'talents': {
        'jack_of_trades': Talent(
            id='jack_of_trades', name='Jack of All Trades',
            description='All skills gain +1% effectiveness per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'skill_power': 0.01}}
        ),
        'identify': Talent(
            id='identify', name='Identify',
            description='Unlocks: Reveal item properties.',
            max_rank=1, tier=2, requires=['jack_of_trades'],
            effects={'skill_unlock': 'identify'}
        ),
        'legend_lore': Talent(
            id='legend_lore', name='Legend Lore',
            description='Unlocks: Learn about creatures and places.',
            max_rank=1, tier=3, requires=['identify'],
            effects={'skill_unlock': 'legend_lore'}
        ),
        # Tier 4 (15 points required)
        'arcane_knowledge': Talent(
            id='arcane_knowledge', name='Arcane Knowledge',
            description='Spell damage increased by 3% per rank.',
            max_rank=3, tier=4, requires=['legend_lore'],
            effects={'stat_bonus': {'spell_damage': 0.03}}
        ),
        'dispel_magic': Talent(
            id='dispel_magic', name='Dispel Magic',
            description='Unlocks: Remove magical effects from target.',
            max_rank=1, tier=4, requires=['legend_lore'],
            effects={'skill_unlock': 'dispel_magic'}
        ),
        # Tier 5 (20 points required)
        'polymorph': Talent(
            id='polymorph', name='Polymorph',
            description='Unlocks: Transform enemy into a harmless critter.',
            max_rank=1, tier=5, requires=['dispel_magic'],
            effects={'skill_unlock': 'polymorph'}
        ),
        'greater_lore': Talent(
            id='greater_lore', name='Greater Lore',
            description='All identify/lore abilities reveal hidden info.',
            max_rank=1, tier=5, requires=['arcane_knowledge'],
            effects={'passive': 'greater_lore'}
        ),
    }
}

BARD_TRICKSTER = {
    'name': 'Trickster',
    'description': 'Illusions, charm, and misdirection.',
    'icon': '🎭',
    'talents': {
        'silver_tongue': Talent(
            id='silver_tongue', name='Silver Tongue',
            description='Charm duration increased by 10% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'charm_duration': 0.1}}
        ),
        'mesmerize': Talent(
            id='mesmerize', name='Mesmerize',
            description='Unlocks: Stun with a captivating performance.',
            max_rank=1, tier=2, requires=['silver_tongue'],
            effects={'skill_unlock': 'mesmerize'}
        ),
        'discordant_chord': Talent(
            id='discordant_chord', name='Discordant Chord',
            description='Unlocks: Silence target for 2 rounds.',
            max_rank=1, tier=3, requires=['mesmerize'],
            effects={'skill_unlock': 'discordant_chord'}
        ),
        'mirror_image': Talent(
            id='mirror_image', name='Mirror Image',
            description='Unlocks: Create illusory copies of yourself.',
            max_rank=1, tier=4, requires=['discordant_chord'],
            effects={'skill_unlock': 'mirror_image'}
        ),
        # Tier 5 (20 points required)
        'mass_charm': Talent(
            id='mass_charm', name='Mass Charm',
            description='Unlocks: Charm all enemies in the room.',
            max_rank=1, tier=5, requires=['mirror_image'],
            effects={'skill_unlock': 'mass_charm'}
        ),
        'grand_illusion': Talent(
            id='grand_illusion', name='Grand Illusion',
            description='Unlocks: Create a powerful illusion that fights.',
            max_rank=1, tier=5, requires=['mirror_image'],
            effects={'skill_unlock': 'grand_illusion'}
        ),
    }
}

# =============================================================================
# ASSASSIN TALENT TREES
# =============================================================================

ASSASSIN_LETHALITY = {
    'name': 'Lethality',
    'description': 'Maximum damage from the shadows.',
    'icon': '☠️',
    'talents': {
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
        'cold_blood': Talent(
            id='cold_blood', name='Cold Blood',
            description='Unlocks: Guarantee next attack crits.',
            max_rank=1, tier=2, requires=['ruthlessness'],
            effects={'skill_unlock': 'cold_blood'}
        ),
        'twist_the_knife': Talent(
            id='twist_the_knife', name='Twist the Knife',
            description='Attacks on bleeding targets deal 8% more damage per rank.',
            max_rank=3, tier=2, requires=['serrated_blades'],
            effects={'damage_mod': {'vs_bleeding': 0.08}}
        ),
        # Tier 3 (10 points required)
        'marked_for_death': Talent(
            id='marked_for_death', name='Marked for Death',
            description='Unlocks: Mark target to take 15% more damage.',
            max_rank=1, tier=3, requires=['cold_blood'],
            effects={'skill_unlock': 'marked_for_death'}
        ),
        'silence_strike': Talent(
            id='silence_strike', name='Silence Strike',
            description='Unlocks: Strike that silences spellcasting.',
            max_rank=1, tier=4, requires=['marked_for_death'],
            effects={'skill_unlock': 'silence_strike'}
        ),
        'death_from_above': Talent(
            id='death_from_above', name='Death from Above',
            description='Unlocks: Leap attack with massive damage.',
            max_rank=1, tier=5, requires=['marked_for_death'],
            effects={'skill_unlock': 'death_from_above'}
        ),
    }
}

ASSASSIN_POISON = {
    'name': 'Poison',
    'description': 'Deadly toxins and debilitating venoms.',
    'icon': '🧪',
    'talents': {
        'venom_coating': Talent(
            id='venom_coating', name='Venom Coating',
            description='Poison chance increased by 5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'poison_chance': 5}}
        ),
        'crippling_poison': Talent(
            id='crippling_poison', name='Crippling Poison',
            description='Unlocks: Poison that slows movement.',
            max_rank=1, tier=2, requires=['venom_coating'],
            effects={'skill_unlock': 'crippling_poison'}
        ),
        'deadly_poison': Talent(
            id='deadly_poison', name='Deadly Poison',
            description='Unlocks: Stacking damage poison.',
            max_rank=1, tier=3, requires=['crippling_poison'],
            effects={'skill_unlock': 'deadly_poison'}
        ),
        # Tier 4 (15 points required)
        'wound_poison': Talent(
            id='wound_poison', name='Wound Poison',
            description='Unlocks: Poison that reduces healing by 50%.',
            max_rank=1, tier=4, requires=['deadly_poison'],
            effects={'skill_unlock': 'wound_poison'}
        ),
        'master_poisoner': Talent(
            id='master_poisoner', name='Master Poisoner',
            description='Poison damage increased by 5% per rank.',
            max_rank=3, tier=4, requires=['deadly_poison'],
            effects={'damage_mod': {'poison': 0.05}}
        ),
        # Tier 5 (20 points required)
        'envenom': Talent(
            id='envenom', name='Envenom',
            description='Unlocks: Consume poisons for burst damage.',
            max_rank=1, tier=5, requires=['wound_poison'],
            effects={'skill_unlock': 'envenom'}
        ),
    }
}

ASSASSIN_SHADOW = {
    'name': 'Shadow',
    'description': 'Become one with darkness.',
    'icon': '🌑',
    'talents': {
        'shadow_mastery': Talent(
            id='shadow_mastery', name='Shadow Mastery',
            description='Stealth cooldown reduced by 5% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'stealth_cd': -0.05}}
        ),
        'cloak_of_shadows': Talent(
            id='cloak_of_shadows', name='Cloak of Shadows',
            description='Unlocks: Remove harmful magic effects.',
            max_rank=1, tier=2, requires=['shadow_mastery'],
            effects={'skill_unlock': 'cloak_of_shadows'}
        ),
        'shadow_blink': Talent(
            id='shadow_blink', name='Shadow Blink',
            description='Unlocks: Blink behind target, entering stealth briefly.',
            max_rank=1, tier=3, requires=['cloak_of_shadows'],
            effects={'skill_unlock': 'shadow_blink'}
        ),
        'vanish': Talent(
            id='vanish', name='Vanish',
            description='Unlocks: Instant stealth, drop threat.',
            max_rank=1, tier=3, requires=['cloak_of_shadows'],
            effects={'skill_unlock': 'vanish'}
        ),
        # Tier 4 (15 points required)
        'shadow_step': Talent(
            id='shadow_step', name='Shadow Step',
            description='Unlocks: Teleport behind any target.',
            max_rank=1, tier=4, requires=['shadow_blink'],
            effects={'skill_unlock': 'shadow_step'}
        ),
        'elusiveness': Talent(
            id='elusiveness', name='Elusiveness',
            description='Dodge chance increased by 3% per rank.',
            max_rank=3, tier=4, requires=['vanish'],
            effects={'stat_bonus': {'dodge': 3}}
        ),
        # Tier 5 (20 points required)
        'shadow_blade': Talent(
            id='shadow_blade', name='Shadow Blade',
            description='Unlocks: +100% damage from stealth for 15s.',
            max_rank=1, tier=5, requires=['shadow_step'],
            effects={'skill_unlock': 'shadow_blade'}
        ),
    }
}

# =============================================================================
# CLASS TALENT TREE MAPPING
# =============================================================================

CLASS_TALENT_TREES = {
    'warrior': [WARRIOR_PROTECTION, WARRIOR_FURY, WARRIOR_ARMS],
    'mage': [MAGE_FIRE, MAGE_FROST, MAGE_ARCANE],
    'thief': [THIEF_ASSASSINATION, THIEF_COMBAT, THIEF_SUBTLETY],
    'cleric': [CLERIC_HOLY, CLERIC_DISCIPLINE, CLERIC_SHADOW],
    'ranger': [RANGER_BEASTMASTERY, RANGER_MARKSMANSHIP, RANGER_SURVIVAL],
    'paladin': [PALADIN_HOLY, PALADIN_PROTECTION, PALADIN_RETRIBUTION],
    'necromancer': [NECRO_UNHOLY, NECRO_BLOOD, NECRO_FROST],
    'bard': [BARD_PERFORMANCE, BARD_LORE, BARD_TRICKSTER],
    'assassin': [ASSASSIN_LETHALITY, ASSASSIN_POISON, ASSASSIN_SHADOW],
}

# Tree identity passives (earned at 25+ points in a single tree)
TREE_IDENTITY_PASSIVES = {
    'warrior': {
        'Protection': 'protection_identity',
        'Fury': 'fury_identity',
        'Arms': 'arms_identity',
    },
    'mage': {
        'Fire': 'fire_identity',
        'Frost': 'frost_identity',
        'Arcane': 'arcane_identity',
    },
    'thief': {
        'Assassination': 'assassination_identity',
        'Combat': 'combat_identity',
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
                
                await player.send(f"\r\n{c['bright_green']}╔══════════════════════════════════════════════╗{c['reset']}")
                await player.send(f"{c['bright_green']}║{c['bright_yellow']}  ★ TALENT LEARNED! ★                         {c['bright_green']}║{c['reset']}")
                await player.send(f"{c['bright_green']}╠══════════════════════════════════════════════╣{c['reset']}")
                await player.send(f"{c['bright_green']}║{c['reset']}  {c['white']}{talent.name:<40}{c['reset']}    {c['bright_green']}║{c['reset']}")
                if talent.max_rank > 1:
                    await player.send(f"{c['bright_green']}║{c['reset']}  {c['cyan']}Rank {new_rank}/{talent.max_rank}{c['reset']}                                 {c['bright_green']}║{c['reset']}")
                await player.send(f"{c['bright_green']}╚══════════════════════════════════════════════╝{c['reset']}\r\n")
                
                # Check for skill unlocks
                if 'skill_unlock' in talent.effects:
                    skill_name = talent.effects['skill_unlock']
                    player.skills[skill_name] = 75  # Start at 75% proficiency
                    await player.send(f"{c['bright_cyan']}New ability unlocked: {skill_name.replace('_', ' ').title()}!{c['reset']}")
                
                break
        
        return True
    
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
