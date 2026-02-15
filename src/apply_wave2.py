#!/usr/bin/env python3
"""Apply Wave 2 class rework changes to all files."""
import re, os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# 1. TALENTS.PY - Replace warrior, mage, ranger, bard trees
# ============================================================

with open('talents.py', 'r') as f:
    talents_content = f.read()
    talents_lines = talents_content.split('\n')

# Find section boundaries
def find_line(lines, pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1

# Warrior: from WARRIOR_PROTECTION to before MAGE section comment
warrior_start = find_line(talents_lines, 'WARRIOR_PROTECTION = {')
mage_comment = find_line(talents_lines, '# MAGE TALENT TREES')
mage_sep_start = mage_comment - 1  # The === line before

# Mage: from MAGE section to before RANGER section  
mage_start = find_line(talents_lines, 'MAGE_FIRE = {')
ranger_comment = find_line(talents_lines, '# RANGER TALENT TREES')
ranger_sep_start = ranger_comment - 1

# Ranger: from RANGER section to before BARD section
ranger_start = find_line(talents_lines, 'RANGER_BEASTMASTERY = {')
bard_comment = find_line(talents_lines, '# BARD TALENT TREES')
bard_sep_start = bard_comment - 1

# Bard: from BARD section to before ASSASSIN section
bard_start = find_line(talents_lines, 'BARD_PERFORMANCE = {')
assassin_comment = find_line(talents_lines, '# ASSASSIN TALENT TREES')
assassin_sep_start = assassin_comment - 1

WARRIOR_TREES = '''WARRIOR_PROTECTION = {
    'name': 'Protection',
    'description': 'Master of defense, protecting allies and absorbing damage.',
    'icon': '🛡️',
    'talents': {
        'thick_skin': Talent(
            id='thick_skin', name='Thick Skin',
            description='Physical damage reduction +2% per rank.',
            max_rank=5, tier=1,
            effects={'damage_mod': {'physical_reduction': 0.02}}
        ),
        'shield_mastery': Talent(
            id='shield_mastery', name='Shield Mastery',
            description='Shield block value +5% per rank.',
            max_rank=3, tier=1,
            effects={'stat_bonus': {'shield_block': 0.05}}
        ),
        'shield_bash_talent': Talent(
            id='shield_bash_talent', name='Shield Bash',
            description='Active: Stun target 1 round + interrupt spellcasting. Costs 20 Rage. 15s CD.',
            max_rank=1, tier=2,
            effects={'skill_unlock': 'shield_bash_talent'}
        ),
        'fortified_resolve': Talent(
            id='fortified_resolve', name='Fortified Resolve',
            description='Max HP +3% per rank.',
            max_rank=3, tier=2,
            effects={'stat_bonus': {'max_hp_pct': 0.03}}
        ),
        'shield_wall_mastery': Talent(
            id='shield_wall_mastery', name='Shield Wall Mastery',
            description='Shield Wall cooldown reduced to 90s, lasts 12s.',
            max_rank=1, tier=3,
            effects={'passive': 'shield_wall_mastery'}
        ),
        'reinforced_armor': Talent(
            id='reinforced_armor', name='Reinforced Armor',
            description='Armor value +3% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'armor_pct': 0.03}}
        ),
        'last_stand': Talent(
            id='last_stand', name='Last Stand',
            description='Active: +30% max HP for 15s. Costs 40 Rage. 180s CD.',
            max_rank=1, tier=4,
            effects={'skill_unlock': 'last_stand'}
        ),
        'stalwart_defender': Talent(
            id='stalwart_defender', name='Stalwart Defender',
            description='Damage reduction +1% per rank while in Defensive stance.',
            max_rank=5, tier=4,
            effects={'passive': 'stalwart_defender'}
        ),
        'unbreakable': Talent(
            id='unbreakable', name='Unbreakable',
            description='Passive: Cannot die for 3s after reaching 1 HP (once per 5 min). Grants 50 Rage.',
            max_rank=1, tier=5,
            effects={'passive': 'unbreakable'}
        ),
    }
}

WARRIOR_FURY = {
    'name': 'Fury',
    'description': 'Unleash berserker rage for devastating damage.',
    'icon': '🔥',
    'talents': {
        'blood_frenzy': Talent(
            id='blood_frenzy', name='Blood Frenzy',
            description='Rage generation from damage dealt +1 per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'rage_gen_bonus': 1}}
        ),
        'endless_rage': Talent(
            id='endless_rage', name='Endless Rage',
            description='Rage decay out of combat -2 per rank.',
            max_rank=3, tier=1,
            effects={'passive': 'endless_rage'}
        ),
        'rampage': Talent(
            id='rampage', name='Rampage',
            description='Active: 3 rapid strikes, each dealing weapon damage. Costs 40 Rage. 10s CD.',
            max_rank=1, tier=2,
            effects={'skill_unlock': 'rampage'}
        ),
        'war_cry_talent': Talent(
            id='war_cry_talent', name='War Cry',
            description='Battle Cry damage buff +3% per rank (13/16/19% total).',
            max_rank=3, tier=2,
            effects={'passive': 'war_cry_talent'}
        ),
        'reckless_abandon': Talent(
            id='reckless_abandon', name='Reckless Abandon',
            description='While above 80 Rage, +15% crit chance.',
            max_rank=1, tier=3,
            effects={'passive': 'reckless_abandon'}
        ),
        'enraged_strikes': Talent(
            id='enraged_strikes', name='Enraged Strikes',
            description='Crit damage +3% per rank.',
            max_rank=5, tier=3,
            effects={'stat_bonus': {'crit_damage': 0.03}}
        ),
        'meat_cleaver': Talent(
            id='meat_cleaver', name='Meat Cleaver',
            description='Cleave and Rampage hit +1 additional target.',
            max_rank=1, tier=4,
            effects={'passive': 'meat_cleaver'}
        ),
        'furious_blows': Talent(
            id='furious_blows', name='Furious Blows',
            description='Attack speed +2% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'attack_speed': 0.02}}
        ),
        'avatar_of_war': Talent(
            id='avatar_of_war', name='Avatar of War',
            description='Active: +50% damage, immune to CC for 15s. Costs 80 Rage. 180s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'avatar_of_war'}
        ),
    }
}

WARRIOR_ARMS = {
    'name': 'Arms',
    'description': 'Master weapons and bleed your foes dry.',
    'icon': '⚔️',
    'talents': {
        'weapon_expertise': Talent(
            id='weapon_expertise', name='Weapon Expertise',
            description='Hit chance +1% per rank.',
            max_rank=5, tier=1,
            effects={'stat_bonus': {'hit_chance': 0.01}}
        ),
        'deep_wounds': Talent(
            id='deep_wounds', name='Deep Wounds',
            description='Crits cause bleed for 3/5/8% of damage over 4 ticks.',
            max_rank=3, tier=1,
            effects={'proc': {'chance': 100, 'effect': 'bleed', 'on': 'crit'}}
        ),
        'tactical_mastery': Talent(
            id='tactical_mastery', name='Tactical Mastery',
            description='Retain 30 Rage when switching stances (normally lose all).',
            max_rank=1, tier=2,
            effects={'passive': 'tactical_mastery'}
        ),
        'battle_stance_talent': Talent(
            id='battle_stance_talent', name='Battle Stance Mastery',
            description='Battle Stance damage +3% per rank.',
            max_rank=3, tier=2,
            effects={'passive': 'battle_stance_talent'}
        ),
        'overpower': Talent(
            id='overpower', name='Overpower',
            description='Active: After target dodges, counter for 2x damage. Free (0 Rage). 8s CD.',
            max_rank=1, tier=3,
            effects={'skill_unlock': 'overpower'}
        ),
        'mortal_strike_mastery': Talent(
            id='mortal_strike_mastery', name='Mortal Strike Mastery',
            description='Mortal Strike damage +3% per rank.',
            max_rank=5, tier=3,
            effects={'damage_mod': {'mortal_strike': 0.03}}
        ),
        'sword_specialization': Talent(
            id='sword_specialization', name='Sword Specialization',
            description='10% chance on hit for extra free attack.',
            max_rank=1, tier=4,
            effects={'proc': {'chance': 10, 'effect': 'extra_attack'}}
        ),
        'combat_expertise': Talent(
            id='combat_expertise', name='Combat Expertise',
            description='Crit chance +1% per rank.',
            max_rank=5, tier=4,
            effects={'stat_bonus': {'crit_chance': 0.01}}
        ),
        'bladestorm': Talent(
            id='bladestorm', name='Bladestorm',
            description='Active: AoE spin, hit all enemies for 1.5x weapon damage per round for 3 rounds. Costs 60 Rage. 120s CD.',
            max_rank=1, tier=5,
            effects={'skill_unlock': 'bladestorm'}
        ),
    }
}'''

MAGE_TREES = '''MAGE_FIRE = {
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
}'''

RANGER_TREES = '''RANGER_BEASTMASTERY = {
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
}'''

BARD_TREES = '''BARD_PERFORMANCE = {
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
            description='Active: Identify any item\\'s full stats. Costs 1 Inspiration.',
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
}'''

# Now rebuild talents.py
# Keep lines before warrior start, replace warrior, keep mage comment, replace mage, etc.

new_lines = []
# Lines before warrior trees (includes imports and header)
new_lines.extend(talents_lines[:warrior_start])

# New warrior trees
new_lines.append(WARRIOR_TREES)
new_lines.append('')

# Mage section header
new_lines.append('# =============================================================================')
new_lines.append('# MAGE TALENT TREES')
new_lines.append('# =============================================================================')
new_lines.append('')

# New mage trees
new_lines.append(MAGE_TREES)
new_lines.append('')

# Keep everything between end of mage and start of ranger (cleric, thief, paladin, necro sections)
# Find the line after MAGE_ARCANE closing (which is right before CLERIC or whatever comes next)
# Actually the structure is: warrior, mage, then cleric/thief/paladin/necro, then ranger, bard, assassin
# Let me check what's between mage and ranger

# Lines between mage trees end and ranger section header
# mage goes from mage_start to ranger_sep_start-1
# But there are cleric/thief/paladin/necro sections in between
# Let me find what's at line after mage arcane
mage_arcane_end = find_line(talents_lines, 'MAGE_ARCANE = {', mage_start)
# Find the closing } of MAGE_ARCANE
brace_count = 0
mage_arcane_close = mage_arcane_end
for i in range(mage_arcane_end, len(talents_lines)):
    brace_count += talents_lines[i].count('{') - talents_lines[i].count('}')
    if brace_count == 0 and i > mage_arcane_end:
        mage_arcane_close = i
        break

# Everything between old mage end and ranger start includes cleric, thief, paladin, necro
# We want to keep that. Find the first non-mage content after mage section
# The old mage trees end, then comes cleric section
# Let's find the cleric section
cleric_comment = find_line(talents_lines, '# CLERIC TALENT TREES')
if cleric_comment == -1:
    # Maybe it's right after mage
    # Check what's between mage end and ranger
    print(f"DEBUG: Lines around mage_arcane_close+1 to ranger_sep_start:")
    for i in range(mage_arcane_close+1, min(mage_arcane_close+10, ranger_sep_start)):
        print(f"  {i}: {talents_lines[i]}")

# Find the end of each old section to figure out what to keep between mage and ranger
# Lines from after old mage to before ranger = middle sections (cleric, thief, paladin, necro)
# We need to find where old mage section ends

# Actually let's be more precise. The old structure has:
# Line 43: WARRIOR_PROTECTION
# Line 380: === MAGE TALENT TREES ===
# Line 385: MAGE_FIRE
# Then at some point mage ends, then cleric, thief, paladin, necro sections
# Line 1084: === RANGER TALENT TREES ===
# Line 1088: RANGER_BEASTMASTERY

# So lines from after old mage's last tree to before ranger section header = cleric+thief+paladin+necro
# We need to figure out where mage ends

# Find the end of MAGE_ARCANE (the last mage tree)
# MAGE_ARCANE starts at line 536
old_mage_arcane_start = find_line(talents_lines, 'MAGE_ARCANE = {')
brace_count = 0
old_mage_arcane_end = old_mage_arcane_start
for i in range(old_mage_arcane_start, len(talents_lines)):
    brace_count += talents_lines[i].count('{') - talents_lines[i].count('}')
    if brace_count == 0 and i > old_mage_arcane_start:
        old_mage_arcane_end = i
        break

print(f"Old mage arcane ends at line {old_mage_arcane_end}")
print(f"Content after: {talents_lines[old_mage_arcane_end+1:old_mage_arcane_end+5]}")

# The middle section (cleric, thief, paladin, necro) is from old_mage_arcane_end+1 to ranger_sep_start-1
middle_start = old_mage_arcane_end + 1
middle_end = ranger_sep_start  # exclusive

# Add the middle section (cleric, thief, paladin, necro trees) unchanged
new_lines.extend(talents_lines[middle_start:middle_end])

# Ranger section header
new_lines.append('# =============================================================================')
new_lines.append('# RANGER TALENT TREES')
new_lines.append('# =============================================================================')
new_lines.append('')

# New ranger trees
new_lines.append(RANGER_TREES)
new_lines.append('')

# Bard section header
new_lines.append('# =============================================================================')
new_lines.append('# BARD TALENT TREES')
new_lines.append('# =============================================================================')
new_lines.append('')

# New bard trees
new_lines.append(BARD_TREES)
new_lines.append('')

# Everything from assassin section header onwards (unchanged)
new_lines.extend(talents_lines[assassin_sep_start:])

with open('talents.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ talents.py updated")

# ============================================================
# 2. PLAYER.PY - Add missing attributes
# ============================================================

with open('player.py', 'r') as f:
    player_content = f.read()

# Check what's missing and add
additions = []
if 'self.focus' not in player_content:
    additions.append(('        # Mage Arcane Charges System\n        self.arcane_charges = 0',
                      '        # Mage Arcane Charges System\n        self.arcane_charges = 0         # Arcane charges (0-5)\n        self.max_arcane_charges = 5\n        self.charge_decay_time = 0      # Timestamp for out-of-combat decay'))
if 'self.charge_decay_time' not in player_content:
    # Add charge_decay_time after max_arcane_charges
    player_content = player_content.replace(
        "        self.max_arcane_charges = 5\n",
        "        self.max_arcane_charges = 5\n        self.charge_decay_time = 0      # Timestamp for out-of-combat decay\n"
    )

if 'self.focus' not in player_content:
    # Add focus system after arcane charges section
    player_content = player_content.replace(
        "        # Thief Combo Point System",
        "        # Ranger Focus System\n"
        "        self.focus = 0                  # Current focus (0-100)\n"
        "        self.hunters_mark_target = None  # Marked prey reference\n"
        "\n"
        "        # Bard Inspiration System\n"
        "        self.inspiration = 0            # Current inspiration (0-10)\n"
        "        self.active_song = None          # Current song being played\n"
        "        self.song_targets = []           # Players affected by current song\n"
        "\n"
        "        # Thief Combo Point System"
    )

with open('player.py', 'w') as f:
    f.write(player_content)

print("✅ player.py updated")

# ============================================================
# 3. CONFIG.PY - Update skill lists
# ============================================================

with open('config.py', 'r') as f:
    config_content = f.read()

# Update warrior skills
config_content = re.sub(
    r"('warrior':\s*\{[^}]*'skills':\s*)\[[^\]]*\]",
    r"\1['kick', 'bash', 'rescue', 'disarm', 'second_attack', 'third_attack', 'parry',\n                      'shield_block', 'cleave', 'dodge', 'execute', 'mortal_strike', 'shield_wall',\n                      'battle_cry', 'stance', 'rampage', 'battleshout']",
    config_content,
    count=1
)

# Update mage skills  
config_content = re.sub(
    r"('mage':\s*\{[^}]*'skills':\s*)\[[^\]]*\]",
    r"\1['scribe', 'arcane_barrage', 'evocation', 'arcane_blast', 'dodge']",
    config_content,
    count=1
)

# Update ranger skills
config_content = re.sub(
    r"('ranger':\s*\{[^}]*'skills':\s*)\[[^\]]*\]",
    r"\1['track', 'sneak', 'hide', 'second_attack', 'dual_wield', 'dodge', 'scan',\n                      'aimed_shot', 'kill_command', 'rapid_fire', 'hunters_mark', 'tame']",
    config_content,
    count=1
)

# Update bard skills
config_content = re.sub(
    r"('bard':\s*\{[^}]*'skills':\s*)\[[^\]]*\]",
    r"\1['sneak', 'pick_lock', 'lore', 'countersong', 'fascinate', 'mockery', 'dodge',\n                      'crescendo', 'encore', 'magnum_opus', 'discordant_note']",
    config_content,
    count=1
)

with open('config.py', 'w') as f:
    f.write(config_content)

print("✅ config.py updated")

print("\n✅ Phase 1 complete (talents, player attrs, config skills)")
print("Now need to update: commands.py, combat.py, help_data.py")
