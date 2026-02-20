"""
Misthollow Spells
================
Magic system and spell effects.
"""

import random
import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Player, Character

from config import Config
from affects import AffectManager

logger = logging.getLogger('Misthollow.Spells')

# Spell definitions
SPELLS = {
    # Offensive spells
    'magic_missile': {
        'name': 'Magic Missile',
        'mana_cost': 10,
        'damage_dice': '1d4+1',
        'damage_per_level': 1,
        'target': 'offensive',
        'message_self': 'You fire magic missiles at $N!',
        'message_room': '$n fires magic missiles at $N!',
    },
    'burning_hands': {
        'name': 'Burning Hands',
        'mana_cost': 15,
        'damage_dice': '1d6+2',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'Fire erupts from your hands, burning $N!',
        'message_room': 'Fire erupts from $n\'s hands, burning $N!',
    },
    'chill_touch': {
        'name': 'Chill Touch',
        'mana_cost': 15,
        'damage_dice': '1d8',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'You touch $N with your icy fingers!',
        'message_room': '$n touches $N with icy fingers!',
    },
    'fireball': {
        'name': 'Fireball',
        'mana_cost': 40,
        'damage_dice': '3d6+5',
        'damage_per_level': 3,
        'target': 'offensive',
        'message_self': 'You hurl a fireball at $N!',
        'message_room': '$n hurls a fireball at $N!',
    },
    'lightning_bolt': {
        'name': 'Lightning Bolt',
        'mana_cost': 35,
        'damage_dice': '3d6+3',
        'damage_per_level': 3,
        'target': 'offensive',
        'message_self': 'Lightning crackles from your fingers into $N!',
        'message_room': 'Lightning crackles from $n\'s fingers into $N!',
    },
    'harm': {
        'name': 'Harm',
        'mana_cost': 50,
        'damage_dice': '5d8',
        'damage_per_level': 0,
        'target': 'offensive',
        'message_self': 'You channel divine wrath into $N!',
        'message_room': '$n channels divine wrath into $N!',
    },
    'flamestrike': {
        'name': 'Flamestrike',
        'mana_cost': 60,
        'damage_dice': '4d8+10',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'A column of holy fire descends upon $N!',
        'message_room': 'A column of holy fire descends upon $N!',
    },
    
    # Healing spells
    'cure_light': {
        'name': 'Cure Light Wounds',
        'mana_cost': 10,
        'heal_dice': '1d8+2',
        'heal_per_level': 1,
        'target': 'defensive',
        'message_self': 'You feel a warm glow as minor wounds heal.',
        'message_other': '$N glows briefly as minor wounds heal.',
    },
    'cure_serious': {
        'name': 'Cure Serious Wounds',
        'mana_cost': 20,
        'heal_dice': '2d8+4',
        'heal_per_level': 2,
        'target': 'defensive',
        'message_self': 'You feel warmth spread through your body.',
        'message_other': '$N glows as wounds begin to close.',
    },
    'cure_critical': {
        'name': 'Cure Critical Wounds',
        'mana_cost': 35,
        'heal_dice': '3d8+6',
        'heal_per_level': 2,
        'target': 'defensive',
        'message_self': 'Divine energy courses through you, healing your wounds.',
        'message_other': 'Divine light surrounds $N, healing grievous wounds.',
    },
    'heal': {
        'name': 'Heal',
        'mana_cost': 50,
        'heal_dice': '100',  # Full heal
        'target': 'defensive',
        'message_self': 'A surge of divine power restores you completely!',
        'message_other': '$N is bathed in divine light and fully restored!',
    },
    'group_heal': {
        'name': 'Group Heal',
        'mana_cost': 80,
        'heal_dice': '2d8+10',
        'heal_per_level': 2,
        'target': 'group',
        'message_self': 'You invoke a healing blessing upon your group!',
        'message_room': '$n invokes a healing blessing!',
    },
    
    # Buff spells
    'armor': {
        'name': 'Armor',
        'mana_cost': 15,
        'target': 'defensive',
        'duration_ticks': 100,  # ~10 min base, scales with level
        'scales_duration': True,
        'affects': [{'type': 'ac', 'value': -20}],
        'message_self': 'You feel protected by magical armor.',
        'message_other': '$N is surrounded by a shimmering shield.',
    },
    'bless': {
        'name': 'Bless',
        'mana_cost': 15,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'hitroll', 'value': 2}, {'type': 'damroll', 'value': 1}],
        'message_self': 'You feel righteous!',
        'message_other': '$N looks more confident.',
    },
    'sanctuary': {
        'name': 'Sanctuary',
        'mana_cost': 75,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'sanctuary', 'value': 1}],
        'message_self': 'A white aura surrounds you.',
        'message_other': 'A white aura surrounds $N.',
    },
    'haste': {
        'name': 'Haste',
        'mana_cost': 50,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'haste', 'value': 1}],
        'message_self': 'You feel yourself moving faster!',
        'message_other': '$N begins moving with supernatural speed.',
    },
    'invisibility': {
        'name': 'Invisibility',
        'mana_cost': 35,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'invisible', 'value': 1}],
        'message_self': 'You fade from view.',
        'message_other': '$N fades from view.',
    },
    'fly': {
        'name': 'Fly',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'fly', 'value': 1}],
        'message_self': 'Your feet lift off the ground!',
        'message_other': '$N rises into the air.',
    },
    
    # Debuff/Utility spells
    'sleep': {
        'name': 'Sleep',
        'mana_cost': 20,
        'target': 'offensive',
        'duration_ticks': 6,
        'affects': [{'type': 'sleep', 'value': 1}],
        'save': True,
        'message_self': '$N falls into a magical slumber!',
        'message_room': '$N falls into a magical slumber!',
    },
    'blindness': {
        'name': 'Blindness',
        'mana_cost': 25,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'blind', 'value': 1}, {'type': 'hitroll', 'value': -4}],
        'save': True,
        'message_self': '$N is struck blind!',
        'message_room': '$N clutches at their eyes, blinded!',
    },
    'poison': {
        'name': 'Poison',
        'mana_cost': 25,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'poison', 'value': 1}, {'type': 'str', 'value': -2}],
        'save': True,
        'message_self': '$N looks very ill.',
        'message_room': '$N looks very ill.',
    },
    'weaken': {
        'name': 'Weaken',
        'mana_cost': 20,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'str', 'value': -4}],
        'save': True,
        'message_self': '$N looks weaker.',
        'message_room': '$N\'s muscles seem to shrink.',
    },
    'fear': {
        'name': 'Fear',
        'mana_cost': 30,
        'target': 'offensive',
        'special': 'fear',
        'save': True,
        'message_self': '$N looks terrified!',
        'message_room': '$N cowers in fear!',
    },
    
    # Necromancy
    'animate_dead': {
        'name': 'Animate Dead',
        'mana_cost': 50,
        'target': 'special',
        'special': 'animate_dead',
        'message_self': 'You raise a corpse to serve you!',
        'message_room': '$n raises a corpse from the dead!',
    },
    'vampiric_touch': {
        'name': 'Vampiric Touch',
        'mana_cost': 30,
        'damage_dice': '2d6+2',
        'damage_per_level': 1,
        'target': 'offensive',
        'special': 'drain_hp',
        'message_self': 'You drain life force from $N!',
        'message_room': '$n drains life force from $N!',
    },
    'energy_drain': {
        'name': 'Energy Drain',
        'mana_cost': 60,
        'damage_dice': '3d8',
        'damage_per_level': 2,
        'target': 'offensive',
        'special': 'drain_exp',
        'message_self': 'You drain $N\'s life essence!',
        'message_room': '$n drains $N\'s life essence!',
    },
    'dark_mending': {
        'name': 'Dark Mending',
        'mana_cost': 35,
        'heal_dice': '3d8',
        'heal_per_level': 1,
        'target': 'pet',
        'special': 'heal_undead',
        'message_self': 'You channel necrotic energy into $N, mending its form!',
        'message_other': 'Dark energy flows into $N, knitting bone and shadow.',
    },
    'unholy_might': {
        'name': 'Unholy Might',
        'mana_cost': 50,
        'target': 'pet',
        'duration_ticks': 20,
        'affects': [
            {'type': 'hitroll', 'value': 5},
            {'type': 'damroll', 'value': 8},
            {'type': 'haste', 'value': 1},
            {'type': 'necrotic_damage', 'value': 6}
        ],
        'message_self': 'You infuse $N with overwhelming dark power!',
        'message_other': '$N crackles with unholy energy!',
    },
    'death_pact': {
        'name': 'Death Pact',
        'mana_cost': 40,
        'target': 'pet',
        'duration_ticks': 10,
        'special': 'death_pact',
        'affects': [{'type': 'damroll', 'value': 3}],
        'message_self': 'You forge a dark bond with $N!',
        'message_other': 'Shadowy tendrils connect $n and $N.',
    },
    'siphon_unlife': {
        'name': 'Siphon Unlife',
        'mana_cost': 45,
        'target': 'pet',
        'special': 'siphon_hp',
        'message_self': 'You create a conduit between yourself and $N!',
        'message_other': 'Life force flows between $n and $N!',
    },
    'corpse_explosion': {
        'name': 'Corpse Explosion',
        'mana_cost': 60,
        'damage_dice': '5d8',
        'target': 'room',
        'special': 'explode_corpse',
        'message_self': 'You detonate the corpse in a blast of necrotic energy!',
        'message_room': 'The corpse explodes in a devastating blast!',
    },
    'mass_animate': {
        'name': 'Mass Animate',
        'mana_cost': 100,
        'target': 'special',
        'special': 'mass_animate',
        'level_required': 20,
        'message_self': 'You raise multiple corpses at once!',
        'message_room': '$n raises an army of undead!',
    },
    
    # Utility
    'detect_magic': {
        'name': 'Detect Magic',
        'mana_cost': 10,
        'target': 'self',
        'duration_ticks': 24,
        'affects': [{'type': 'detect_magic', 'value': 1}],
        'message_self': 'Your eyes tingle.',
    },
    'identify': {
        'name': 'Identify',
        'mana_cost': 20,
        'target': 'object',
        'message_self': 'You examine the item closely...',
    },
    'teleport': {
        'name': 'Teleport',
        'mana_cost': 50,
        'target': 'self',
        'special': 'teleport',
        'message_self': 'You vanish in a flash of light!',
        'message_room': '$n vanishes in a flash of light!',
    },
    'word_of_recall': {
        'name': 'Word of Recall',
        'mana_cost': 15,
        'target': 'self',
        'special': 'recall',
        'message_self': 'You feel yourself being pulled to safety...',
        'message_room': '$n disappears in a flash of light!',
    },

    # Door spells
    'break_door': {
        'name': 'Break Door',
        'mana_cost': 40,
        'target': 'door',
        'special': 'break_door',
        'message_self': 'You unleash magical force at the door!',
        'message_room': '$n unleashes magical force at the door!',
        'level_required': 8,
    },
    'block_door': {
        'name': 'Block Door',
        'mana_cost': 50,
        'target': 'door',
        'duration_ticks': 600,  # 10 minutes
        'special': 'block_door',
        'message_self': 'You seal the door with magical energy!',
        'message_room': '$n seals the door with magical energy!',
        'level_required': 10,
    },

    # Additional Mage Spells
    'color_spray': {
        'name': 'Color Spray',
        'mana_cost': 25,
        'damage_dice': '2d6',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'A spray of brilliant colors dazzles $N!',
        'message_room': '$n creates a spray of brilliant colors at $N!',
    },
    'enchant_weapon': {
        'name': 'Enchant Weapon',
        'mana_cost': 100,
        'target': 'object',
        'special': 'enchant_weapon',
        'message_self': 'Your weapon glows with magical energy!',
        'message_room': '$n\'s weapon glows with magical energy!',
    },
    'meteor_swarm': {
        'name': 'Meteor Swarm',
        'mana_cost': 80,
        'damage_dice': '8d6+10',
        'damage_per_level': 4,
        'target': 'offensive',
        'message_self': 'You summon a devastating meteor swarm at $N!',
        'message_room': '$n summons a meteor swarm that crashes into $N!',
    },
    'chain_lightning': {
        'name': 'Chain Lightning',
        'mana_cost': 70,
        'damage_dice': '6d6+8',
        'damage_per_level': 3,
        'target': 'offensive',
        'special': 'chain_lightning',
        'message_self': 'Lightning chains from your fingers through $N!',
        'message_room': 'Lightning chains from $n through $N!',
    },

    # Additional Cleric Spells
    'remove_curse': {
        'name': 'Remove Curse',
        'mana_cost': 35,
        'target': 'defensive',
        'special': 'remove_curse',
        'message_self': 'Divine light purges curses from $N!',
        'message_other': 'You feel purified as curses are lifted!',
    },
    'remove_poison': {
        'name': 'Remove Poison',
        'mana_cost': 30,
        'target': 'defensive',
        'special': 'remove_poison',
        'message_self': 'You draw the poison from $N\'s body!',
        'message_other': 'The poison leaves your body!',
    },
    'create_food': {
        'name': 'Create Food',
        'mana_cost': 10,
        'target': 'self',
        'special': 'create_food',
        'message_self': 'You conjure a nourishing meal!',
        'message_room': '$n conjures food from thin air!',
    },
    'create_water': {
        'name': 'Create Water',
        'mana_cost': 10,
        'target': 'self',
        'special': 'create_water',
        'message_self': 'You create fresh water!',
        'message_room': '$n creates water from thin air!',
    },
    'summon': {
        'name': 'Summon',
        'mana_cost': 75,
        'target': 'special',
        'special': 'summon_player',
        'message_self': 'You call $N to your side!',
        'message_room': '$n summons someone!',
    },
    'resurrect': {
        'name': 'Resurrect',
        'mana_cost': 150,
        'target': 'special',
        'special': 'resurrect',
        'message_self': 'You call upon divine power to restore life!',
        'message_room': '$n channels divine power, restoring life!',
    },
    'dispel_evil': {
        'name': 'Dispel Evil',
        'mana_cost': 40,
        'damage_dice': '4d8',
        'damage_per_level': 3,
        'target': 'offensive',
        'special': 'dispel_evil',
        'message_self': 'Holy power purges evil from $N!',
        'message_room': 'Holy light purges $N!',
    },
    'earthquake': {
        'name': 'Earthquake',
        'mana_cost': 90,
        'damage_dice': '5d8',
        'damage_per_level': 2,
        'target': 'room',
        'special': 'earthquake',
        'message_self': 'You call upon the earth to shake violently!',
        'message_room': 'The ground shakes violently!',
    },
    'curse': {
        'name': 'Curse',
        'mana_cost': 30,
        'target': 'offensive',
        'duration_ticks': 24,
        'affects': [{'type': 'hitroll', 'value': -3}, {'type': 'damroll', 'value': -2}],
        'save': True,
        'message_self': 'You place a curse upon $N!',
        'message_room': '$n curses $N!',
    },
    'dispel_magic': {
        'name': 'Dispel Magic',
        'mana_cost': 50,
        'target': 'defensive',
        'special': 'dispel_magic',
        'message_self': 'You dispel magical effects on $N!',
        'message_other': 'Your magical effects are stripped away!',
    },

    # ========== MAGE DEFENSIVE SPELLS ==========
    'stoneskin': {
        'name': 'Stoneskin',
        'mana_cost': 60,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'stoneskin', 'value': 100}],  # Absorbs 100 damage
        'message_self': 'Your skin turns to stone!',
        'message_other': '$N\'s skin turns gray and hard as stone!',
    },
    'shield': {
        'name': 'Shield',
        'mana_cost': 25,
        'target': 'defensive',
        'duration_ticks': 100,  # ~10 min base, scales with level
        'scales_duration': True,
        'affects': [{'type': 'ac', 'value': -30}],  # Better than armor
        'message_self': 'A shimmering force shield surrounds you!',
        'message_other': 'A shimmering force shield surrounds $N!',
    },
    'mirror_image': {
        'name': 'Mirror Image',
        'mana_cost': 40,
        'target': 'self',
        'duration_ticks': 12,
        'affects': [{'type': 'mirror_image', 'value': 3}],  # 3 images
        'message_self': 'Multiple images of yourself appear around you!',
        'message_room': 'Multiple images of $n suddenly appear!',
    },
    'displacement': {
        'name': 'Displacement',
        'mana_cost': 35,
        'target': 'self',
        'duration_ticks': 18,
        'affects': [{'type': 'displacement', 'value': 1}],  # 25% miss chance
        'message_self': 'You shimmer and appear a few feet from your actual position!',
        'message_room': '$n shimmers and becomes hard to pinpoint!',
    },
    'mana_shield': {
        'name': 'Mana Shield',
        'mana_cost': 50,
        'target': 'self',
        'duration_ticks': 10,
        'affects': [{'type': 'mana_shield', 'value': 1}],  # Converts 50% damage to mana loss
        'message_self': 'A mana barrier forms around you!',
        'message_room': 'A crackling energy barrier surrounds $n!',
    },
    'ice_armor': {
        'name': 'Ice Armor',
        'mana_cost': 45,
        'target': 'defensive',
        'duration_ticks': 18,
        'affects': [{'type': 'ac', 'value': -25}, {'type': 'ice_armor', 'value': 1}],
        'message_self': 'Icy armor forms around your body!',
        'message_other': 'Icy armor forms around $N!',
    },
    'fire_shield': {
        'name': 'Fire Shield',
        'mana_cost': 50,
        'target': 'self',
        'duration_ticks': 15,
        'affects': [{'type': 'ac', 'value': -20}, {'type': 'fire_shield', 'value': 1}],
        'message_self': 'Flames surround you in a protective shield!',
        'message_room': 'Flames erupt around $n in a protective shield!',
    },
    'spell_reflection': {
        'name': 'Spell Reflection',
        'mana_cost': 70,
        'target': 'self',
        'duration_ticks': 8,
        'affects': [{'type': 'spell_reflect', 'value': 1}],  # 50% chance to reflect
        'message_self': 'A reflective aura surrounds you!',
        'message_room': 'A shimmering aura surrounds $n!',
    },
    'blink': {
        'name': 'Blink',
        'mana_cost': 30,
        'target': 'self',
        'duration_ticks': 12,
        'affects': [{'type': 'blink', 'value': 1}],  # 30% miss chance from micro-teleports
        'message_self': 'You begin blinking in and out of phase!',
        'message_room': '$n begins flickering in and out of existence!',
    },
    'protection_from_evil': {
        'name': 'Protection from Evil',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'ac', 'value': -10}, {'type': 'prot_evil', 'value': 1}],
        'message_self': 'You are protected from evil!',
        'message_other': '$N is surrounded by a holy aura!',
    },
    'protection_from_good': {
        'name': 'Protection from Good',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'ac', 'value': -10}, {'type': 'prot_good', 'value': 1}],
        'message_self': 'You are protected from good!',
        'message_other': '$N is surrounded by a dark aura!',
    },

    # ========== CLERIC DEFENSIVE SPELLS ==========
    'shield_of_faith': {
        'name': 'Shield of Faith',
        'mana_cost': 35,
        'target': 'defensive',
        'duration_ticks': 18,
        'affects': [{'type': 'ac', 'value': -25}, {'type': 'saving_throw', 'value': 2}],
        'message_self': 'Divine power shields you from harm!',
        'message_other': 'Divine light surrounds $N protectively!',
    },
    'divine_shield': {
        'name': 'Divine Shield',
        'mana_cost': 75,
        'target': 'self',
        'duration_ticks': 6,
        'affects': [{'type': 'divine_shield', 'value': 150}],  # Absorbs 150 damage
        'message_self': 'A radiant barrier of divine energy protects you!',
        'message_room': 'A radiant barrier forms around $n!',
    },
    'barkskin': {
        'name': 'Barkskin',
        'mana_cost': 40,
        'target': 'defensive',
        'duration_ticks': 24,
        'affects': [{'type': 'ac', 'value': -35}],  # Natural armor, very strong
        'message_self': 'Your skin becomes as tough as bark!',
        'message_other': '$N\'s skin becomes thick and bark-like!',
    },
    'righteous_fury': {
        'name': 'Righteous Fury',
        'mana_cost': 55,
        'target': 'self',
        'duration_ticks': 12,
        'affects': [{'type': 'damage_reduction', 'value': 5}, {'type': 'damroll', 'value': 3}],
        'message_self': 'Holy fury courses through you!',
        'message_room': 'Divine power radiates from $n!',
    },
    'divine_protection': {
        'name': 'Divine Protection',
        'mana_cost': 100,
        'target': 'self',
        'duration_ticks': 3,
        'affects': [{'type': 'invulnerable', 'value': 1}],  # Nearly invulnerable
        'message_self': 'Divine energy makes you nearly invulnerable!',
        'message_room': '$n is surrounded by blinding divine light!',
    },
    'aegis': {
        'name': 'Aegis',
        'mana_cost': 65,
        'target': 'defensive',
        'duration_ticks': 15,
        'affects': [{'type': 'spell_resist', 'value': 30}],  # 30% spell resistance
        'message_self': 'A magical aegis forms around you!',
        'message_other': 'Magical wards surround $N!',
    },
    # Paladin Talent Spells
    'lay_on_hands': {
        'name': 'Lay on Hands',
        'mana_cost': 20,  # Minimum cost, uses all remaining mana
        'target': 'defensive',
        'special': 'lay_on_hands',
        'message_self': 'You channel all your remaining holy power into healing hands!',
        'message_target': '$n places healing hands upon you!',
    },
    'avenging_wrath': {
        'name': 'Avenging Wrath',
        'mana_cost': 100,
        'target': 'self',
        'duration_ticks': 10,
        'affects': [{'type': 'damroll', 'value': 8}, {'type': 'hitroll', 'value': 6}, {'type': 'haste', 'value': 1}],
        'message_self': 'Wings of golden light burst from your back as holy wrath fills you!',
        'message_room': 'Wings of golden light burst from $n as divine power surrounds them!',
    },
    'holy_aura': {
        'name': 'Holy Aura',
        'mana_cost': 80,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [
            {'type': 'ac', 'value': -40},
            {'type': 'saving_throw', 'value': 4},
            {'type': 'spell_resist', 'value': 20}
        ],
        'message_self': 'A powerful holy aura surrounds you!',
        'message_other': 'A brilliant holy aura surrounds $N!',
    },

    # ========== RANGER/DRUID SPELLS ==========
    'entangle': {
        'name': 'Entangle',
        'mana_cost': 25,
        'target': 'offensive',
        'duration_ticks': 6,
        'affects': [{'type': 'entangled', 'value': 1}],  # Reduces movement/attack
        'save': True,
        'message_self': 'Vines shoot up and entangle $N!',
        'message_room': 'Vines erupt from the ground, entangling $N!',
    },
    'call_lightning': {
        'name': 'Call Lightning',
        'mana_cost': 45,
        'damage_dice': '4d6+5',
        'damage_per_level': 2,
        'target': 'offensive',
        'message_self': 'You call down lightning upon $N!',
        'message_room': 'Lightning strikes $N from the sky!',
    },
    'faerie_fire': {
        'name': 'Faerie Fire',
        'mana_cost': 20,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'ac', 'value': 20}],  # Makes target easier to hit
        'message_self': '$N is outlined in glowing light!',
        'message_room': '$N is outlined in faerie fire!',
    },

    # ========== PALADIN SPELLS ==========
    'detect_evil': {
        'name': 'Detect Evil',
        'mana_cost': 10,
        'target': 'self',
        'duration_ticks': 24,
        'affects': [{'type': 'detect_evil', 'value': 1}],
        'message_self': 'You can sense evil auras.',
    },
    'lay_hands': {
        'name': 'Lay Hands',
        'mana_cost': 40,
        'heal_dice': '50',  # Heals 50 HP
        'target': 'defensive',
        'message_self': 'You lay hands on $N, channeling healing energy!',
        'message_other': '$n lays hands on you, and you feel renewed!',
    },

    # ========== NECROMANCER SPELLS ==========
    'enervation': {
        'name': 'Enervation',
        'mana_cost': 35,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'str', 'value': -3}, {'type': 'dex', 'value': -3}],
        'save': True,
        'message_self': 'Dark energy drains $N\'s vitality!',
        'message_room': 'Dark energy surrounds $N, draining their strength!',
    },
    'death_grip': {
        'name': 'Death Grip',
        'mana_cost': 45,
        'damage_dice': '3d8+3',
        'damage_per_level': 2,
        'target': 'offensive',
        'special': 'death_grip',  # Also stuns
        'message_self': 'You grasp $N with the power of death!',
        'message_room': 'Dark energy grips $N!',
    },
    'finger_of_death': {
        'name': 'Finger of Death',
        'mana_cost': 150,
        'damage_dice': '12d10+30',
        'damage_per_level': 8,
        'target': 'offensive',
        'save': True,
        'special': 'finger_of_death',
        'message_self': 'You point your finger at $N, channeling the cold touch of death!',
        'message_room': '$n points at $N with a skeletal finger wreathed in dark energy!',
    },

    # ========== BARD SPELLS ==========
    'charm_person': {
        'name': 'Charm Person',
        'mana_cost': 30,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'charmed', 'value': 1}],
        'save': True,
        'message_self': '$N looks at you adoringly!',
        'message_room': '$N is charmed by $n!',
    },
    'heroism': {
        'name': 'Heroism',
        'mana_cost': 40,
        'target': 'defensive',
        'duration_ticks': 18,
        'affects': [
            {'type': 'hitroll', 'value': 3},
            {'type': 'damroll', 'value': 3},
            {'type': 'max_hp', 'value': 20}
        ],
        'message_self': 'You feel heroic!',
        'message_other': '$N looks more confident and powerful!',
    },
    'mass_charm': {
        'name': 'Mass Charm',
        'mana_cost': 100,
        'target': 'room',
        'special': 'mass_charm',
        'message_self': 'You attempt to charm everyone in the room!',
        'message_room': '$n sings a mesmerizing song!',
    },
    'slow': {
        'name': 'Slow',
        'mana_cost': 35,
        'target': 'offensive',
        'duration_ticks': 12,
        'affects': [{'type': 'slow', 'value': 1}, {'type': 'hitroll', 'value': -2}],
        'save': True,
        'message_self': '$N moves in slow motion!',
        'message_room': '$N begins moving sluggishly!',
    },

    # ========== TALENT SPELLS (NEW) ==========
    'pyroblast': {
        'name': 'Pyroblast',
        'mana_cost': 60,
        'damage_dice': '5d8',
        'damage_per_level': 3,
        'target': 'offensive',
        'element': 'fire',
        'message_self': 'You hurl a massive pyroblast at $N!',
        'message_room': '$n hurls a massive pyroblast at $N!',
    },
    'combustion': {
        'name': 'Combustion',
        'mana_cost': 40,
        'target': 'defensive',
        'duration_ticks': 6,
        'affects': [{'type': 'combustion', 'value': 1}],
        'message_self': 'Your flames burn with terrifying intensity!',
        'message_other': '$N ignites with overwhelming power.',
    },
    'ice_barrier': {
        'name': 'Ice Barrier',
        'mana_cost': 35,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'divine_shield', 'value': 120}, {'type': 'ice_armor', 'value': 1}],
        'message_self': 'Ice crystallizes into a protective barrier.',
        'message_other': 'Ice surrounds $N in a protective barrier.',
    },
    'ice_lance': {
        'name': 'Ice Lance',
        'mana_cost': 20,
        'damage_dice': '2d6+4',
        'damage_per_level': 2,
        'target': 'offensive',
        'element': 'frost',
        'message_self': 'A lance of ice streaks toward $N!',
        'message_room': '$n launches a lance of ice at $N!',
    },
    'deep_freeze': {
        'name': 'Deep Freeze',
        'mana_cost': 45,
        'damage_dice': '3d6+6',
        'damage_per_level': 2,
        'target': 'offensive',
        'element': 'frost',
        'affects': [{'type': 'stunned', 'value': 1}],
        'duration_ticks': 3,
        'message_self': '$N is encased in deep ice!',
        'message_room': '$N is frozen solid by $n!',
    },
    'cold_snap': {
        'name': 'Cold Snap',
        'mana_cost': 25,
        'target': 'defensive',
        'special': 'cold_snap',
        'message_self': 'Your frost power surges anew.',
        'message_other': '$N exhales a blast of winter air.',
    },
    'arcane_missiles': {
        'name': 'Arcane Missiles',
        'mana_cost': 30,
        'damage_dice': '3d5',
        'damage_per_level': 2,
        'target': 'offensive',
        'element': 'arcane',
        'message_self': 'Arcane missiles strike $N!',
        'message_room': 'Arcane missiles strike $N!',
    },
    'presence_of_mind': {
        'name': 'Presence of Mind',
        'mana_cost': 15,
        'target': 'defensive',
        'duration_ticks': 4,
        'affects': [{'type': 'presence_of_mind', 'value': 1}],
        'message_self': 'Your mind sharpens to perfect focus.',
        'message_other': '$N looks intensely focused.',
    },
    'arcane_power': {
        'name': 'Arcane Power',
        'mana_cost': 25,
        'target': 'defensive',
        'duration_ticks': 6,
        'affects': [{'type': 'arcane_power', 'value': 1}],
        'message_self': 'Arcane power floods through you.',
        'message_other': '$N crackles with arcane power.',
    },
    'mana_rift': {
        'name': 'Mana Rift',
        'mana_cost': 20,
        'target': 'offensive',
        'special': 'mana_rift',
        'message_self': 'You tear open a rift of raw mana at $N!',
        'message_room': '$n rips open a rift of raw mana at $N!',
    },
    'guardian_spirit': {
        'name': 'Guardian Spirit',
        'mana_cost': 50,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'guardian_spirit', 'value': 1}],
        'message_self': 'A guardian spirit watches over $N.',
        'message_other': 'A guardian spirit watches over $N.',
    },
    'divine_hymn': {
        'name': 'Divine Hymn',
        'mana_cost': 70,
        'heal_dice': '3d8+6',
        'heal_per_level': 2,
        'target': 'group',
        'message_self': 'You sing a divine hymn of healing!',
        'message_room': '$n sings a divine hymn!',
    },
    'power_word_shield': {
        'name': 'Power Word: Shield',
        'mana_cost': 35,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'divine_shield', 'value': 180}],
        'message_self': 'A radiant shield surrounds $N.',
        'message_other': 'A radiant shield surrounds $N.',
    },
    'aegis_ward': {
        'name': 'Aegis Ward',
        'mana_cost': 40,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'divine_shield', 'value': 140}, {'type': 'aegis_ward', 'value': 1}],
        'message_self': 'A protective aegis settles over $N.',
        'message_other': 'A protective aegis settles over $N.',
    },
    'pain_suppression': {
        'name': 'Pain Suppression',
        'mana_cost': 45,
        'target': 'defensive',
        'duration_ticks': 6,
        'affects': [{'type': 'damage_reduction', 'value': 40}],
        'message_self': '$N feels less pain.',
        'message_other': '$N feels less pain.',
    },
    'shadowform': {
        'name': 'Shadowform',
        'mana_cost': 25,
        'target': 'defensive',
        'duration_ticks': 12,
        'affects': [{'type': 'shadowform', 'value': 1}, {'type': 'damroll', 'value': 3}],
        'message_self': 'You fade into shadow.',
        'message_other': '$N fades into shadow.',
    },
    'mind_flay': {
        'name': 'Mind Flay',
        'mana_cost': 30,
        'damage_dice': '3d6',
        'damage_per_level': 2,
        'target': 'offensive',
        'element': 'shadow',
        'affects': [{'type': 'slow', 'value': 1}],
        'duration_ticks': 3,
        'message_self': "You flay $N's mind!",
        'message_room': "$n flays $N's mind!",
    },
    'shadow_word_pain': {
        'name': 'Shadow Word: Pain',
        'mana_cost': 25,
        'target': 'offensive',
        'special': 'shadow_word_pain',
        'message_self': 'You afflict $N with searing shadow pain.',
        'message_room': '$n afflicts $N with shadowy pain.',
    },
    'holy_shock': {
        'name': 'Holy Shock',
        'mana_cost': 35,
        'target': 'offensive',
        'special': 'holy_shock',
        'message_self': 'You unleash a holy shock at $N!',
        'message_room': '$n unleashes a holy shock at $N!',
    },
    'beacon_of_light': {
        'name': 'Beacon of Light',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 20,
        'affects': [{'type': 'beacon_of_light', 'value': 1}],
        'message_self': '$N is marked with a beacon of light.',
        'message_other': '$N is marked with a beacon of light.',
    },
    'holy_shield': {
        'name': 'Holy Shield',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'holy_shield', 'value': 1}],
        'message_self': 'Holy energy surrounds your shield.',
        'message_other': '$N is protected by a holy shield.',
    },
    'divine_guardian': {
        'name': 'Divine Guardian',
        'mana_cost': 50,
        'target': 'defensive',
        'duration_ticks': 6,
        'affects': [{'type': 'divine_guardian', 'value': 1}],
        'message_self': 'You become a divine guardian.',
        'message_other': '$N becomes a divine guardian.',
    },
    'army_of_dead': {
        'name': 'Army of the Dead',
        'mana_cost': 60,
        'target': 'defensive',
        'special': 'army_of_dead',
        'message_self': 'You summon an army of the dead!',
        'message_other': '$n summons an army of the dead!',
    },
    'blood_boil': {
        'name': 'Blood Boil',
        'mana_cost': 35,
        'target': 'room',
        'special': 'blood_boil',
        'message_self': 'You boil the blood of your enemies!',
        'message_room': '$n boils the blood of the room!',
    },
    'vampiric_blood': {
        'name': 'Vampiric Blood',
        'mana_cost': 30,
        'target': 'defensive',
        'duration_ticks': 6,
        'affects': [{'type': 'max_hp', 'value': 50}],
        'message_self': 'Your blood surges with undead power.',
        'message_other': "$N's blood surges with undead power.",
    },
    'bone_armor': {
        'name': 'Bone Armor',
        'mana_cost': 25,
        'target': 'defensive',
        'duration_ticks': 8,
        'affects': [{'type': 'divine_shield', 'value': 120}],
        'message_self': 'Bones knit into a protective shell.',
        'message_other': 'Bones knit into a protective shell around $N.',
    },
    'howling_blast': {
        'name': 'Howling Blast',
        'mana_cost': 35,
        'target': 'room',
        'damage_dice': '3d6',
        'damage_per_level': 2,
        'element': 'frost',
        'message_self': 'A howl of frost rips through the room!',
        'message_room': 'A howl of frost rips through the room!',
    },
    'obliterate': {
        'name': 'Obliterate',
        'mana_cost': 40,
        'damage_dice': '5d6',
        'damage_per_level': 3,
        'target': 'offensive',
        'element': 'frost',
        'message_self': 'You obliterate $N with a frost strike!',
        'message_room': '$n obliterates $N with a frost strike!',
    },
    # Death Knight - Blood
    'death_strike': {
        'name': 'Death Strike',
        'mana_cost': 35,
        'damage_dice': '4d6',
        'damage_per_level': 2,
        'target': 'offensive',
        'special': 'death_strike',
        'message_self': 'You strike $N, draining their life!',
        'message_room': '$n strikes $N with a deathly blow!',
    },
    'dancing_rune_weapon': {
        'name': 'Dancing Rune Weapon',
        'mana_cost': 60,
        'target': 'self',
        'duration_ticks': 8,
        'affects': [{'type': 'damroll', 'value': 5}, {'type': 'hitroll', 'value': 4}],
        'message_self': 'A spectral rune weapon appears and fights beside you!',
        'message_room': 'A spectral weapon materializes beside $n!',
    },
    # Death Knight - Frost
    'remorseless_winter': {
        'name': 'Remorseless Winter',
        'mana_cost': 45,
        'target': 'room',
        'damage_dice': '2d6',
        'damage_per_level': 2,
        'duration_ticks': 4,
        'element': 'frost',
        'affects': [{'type': 'slow', 'value': 1}],
        'message_self': 'A remorseless winter engulfs the area!',
        'message_room': 'A remorseless winter engulfs the area!',
    },
    'killing_machine': {
        'name': 'Killing Machine',
        'mana_cost': 20,
        'target': 'self',
        'duration_ticks': 3,
        'affects': [{'type': 'killing_machine', 'value': 1}],
        'message_self': 'Your next strike will be devastating!',
        'message_room': '$n readies a killing blow!',
    },
    # Death Knight - Unholy
    'festering_strike': {
        'name': 'Festering Strike',
        'mana_cost': 30,
        'damage_dice': '3d6',
        'damage_per_level': 2,
        'target': 'offensive',
        'special': 'festering_strike',
        'message_self': 'You strike $N with festering wounds!',
        'message_room': '$n strikes $N with a disease-laden blow!',
    },
    'apocalypse': {
        'name': 'Apocalypse',
        'mana_cost': 100,
        'target': 'room',
        'special': 'apocalypse',
        'message_self': 'You unleash the apocalypse!',
        'message_room': '$n unleashes the apocalypse!',
    },
    # Priest - Shadow
    'vampiric_embrace': {
        'name': 'Vampiric Embrace',
        'mana_cost': 40,
        'target': 'self',
        'duration_ticks': 15,
        'affects': [{'type': 'vampiric_embrace', 'value': 25}],  # 25% of shadow damage heals
        'message_self': 'Dark energy surrounds you, ready to leech life.',
        'message_room': 'Dark energy surrounds $n.',
    },
    'void_eruption': {
        'name': 'Void Eruption',
        'mana_cost': 80,
        'damage_dice': '6d6',
        'damage_per_level': 3,
        'target': 'room',
        'element': 'shadow',
        'message_self': 'The void erupts around you!',
        'message_room': 'The void erupts around $n!',
    },
    'song_of_battle': {
        'name': 'Song of Battle',
        'mana_cost': 20,
        'target': 'group',
        'duration_ticks': 8,
        'affects': [{'type': 'damroll', 'value': 2}],
        'message_self': 'Your song inspires battle fury!',
        'message_room': '$n sings a song of battle!',
    },
    'anthem_of_defense': {
        'name': 'Anthem of Defense',
        'mana_cost': 20,
        'target': 'group',
        'duration_ticks': 8,
        'affects': [{'type': 'damage_reduction', 'value': 10}],
        'message_self': 'Your anthem hardens your allies.',
        'message_room': '$n sings an anthem of defense!',
    },
    'finale': {
        'name': 'Finale',
        'mana_cost': 30,
        'target': 'offensive',
        'special': 'finale',
        'message_self': 'You unleash a powerful finale at $N!',
        'message_room': '$n unleashes a powerful finale at $N!',
    },
    'legend_lore': {
        'name': 'Legend Lore',
        'mana_cost': 15,
        'target': 'defensive',
        'special': 'legend_lore',
        'message_self': 'You intone a legend of this place.',
        'message_room': '$n speaks an ancient legend.',
    },
    'mesmerize': {
        'name': 'Mesmerize',
        'mana_cost': 25,
        'target': 'offensive',
        'affects': [{'type': 'stunned', 'value': 1}],
        'duration_ticks': 2,
        'message_self': '$N is mesmerized!',
        'message_room': '$N is mesmerized!',
    },
    'discordant_chord': {
        'name': 'Discordant Chord',
        'mana_cost': 20,
        'target': 'offensive',
        'affects': [{'type': 'silenced', 'value': 1}],
        'duration_ticks': 3,
        'message_self': '$N is silenced by discordant sound!',
        'message_room': '$N is silenced by discordant sound!',
    },
    'raise_abomination': {
        'name': 'Raise Abomination',
        'mana_cost': 80,
        'target': 'defensive',
        'special': 'raise_abomination',
        'message_self': 'You raise a towering abomination!',
        'message_room': '$n raises a towering abomination!',
    },

    # ========== LEVEL 31-60 ABILITIES ==========
    # These powerful abilities unlock at higher levels and define endgame play.

    # ===== MAGE LEVEL 31-60 =====
    'time_warp': {
        'name': 'Time Warp',
        'mana_cost': 120,
        'target': 'group',
        'duration_ticks': 20,
        'level_required': 38,
        'class_required': 'mage',
        'cooldown': 300,  # 5 minutes
        'affects': [
            {'type': 'haste', 'value': 1},
            {'type': 'hitroll', 'value': 4},
            {'type': 'damroll', 'value': 3}
        ],
        'message_self': 'You bend the fabric of time, hastening your allies!',
        'message_room': '$n warps time itself, hastening everyone nearby!',
    },
    'arcane_explosion': {
        'name': 'Arcane Explosion',
        'mana_cost': 80,
        'damage_dice': '8d8+20',
        'damage_per_level': 4,
        'target': 'room',
        'level_required': 44,
        'class_required': 'mage',
        'cooldown': 30,
        'element': 'arcane',
        'message_self': 'You unleash a devastating arcane explosion!',
        'message_room': '$n unleashes a massive arcane explosion that engulfs everything!',
    },
    'icy_veins': {
        'name': 'Icy Veins',
        'mana_cost': 100,
        'target': 'self',
        'duration_ticks': 15,
        'level_required': 50,
        'class_required': 'mage',
        'cooldown': 180,  # 3 minutes
        'affects': [
            {'type': 'crit_chance', 'value': 30},
            {'type': 'haste', 'value': 1},
            {'type': 'spell_power', 'value': 15}
        ],
        'message_self': 'Frost surges through your veins, sharpening your focus!',
        'message_room': '$n\'s eyes glow icy blue as frost power surges through them!',
    },
    'combustion_master': {
        'name': 'Combustion',
        'mana_cost': 80,
        'target': 'self',
        'duration_ticks': 12,
        'level_required': 56,
        'class_required': 'mage',
        'cooldown': 180,
        'affects': [
            {'type': 'fire_crit', 'value': 100},  # Guaranteed fire crits
            {'type': 'damroll', 'value': 8}
        ],
        'message_self': 'Your inner fire ignites - every spell WILL burn!',
        'message_room': '$n erupts in flames, fire magic guaranteed to devastate!',
    },
    'meteor_storm': {
        'name': 'Meteor Storm',
        'mana_cost': 200,
        'damage_dice': '15d10+50',
        'damage_per_level': 6,
        'target': 'room',
        'level_required': 60,
        'class_required': 'mage',
        'cooldown': 600,  # 10 minutes
        'element': 'fire',
        'special': 'meteor_storm',
        'affects': [{'type': 'stunned', 'value': 1}],
        'duration_ticks': 2,
        'dot_damage': '3d6',
        'dot_duration': 5,
        'message_self': 'You call down a CATACLYSMIC METEOR STORM from the heavens!',
        'message_room': 'The sky TEARS OPEN as $n calls down a devastating meteor storm!',
    },

    # ===== CLERIC LEVEL 31-60 =====
    'prayer_of_mending': {
        'name': 'Prayer of Mending',
        'mana_cost': 60,
        'heal_dice': '4d8+10',
        'heal_per_level': 2,
        'target': 'defensive',
        'level_required': 32,
        'class_required': 'cleric',
        'cooldown': 15,
        'special': 'prayer_of_mending',  # Bounces to injured allies
        'bounces': 3,
        'message_self': 'You place a prayer of mending on $N - it will bounce to heal others!',
        'message_other': 'A glowing prayer settles on you, ready to heal and bounce!',
    },
    'spirit_link': {
        'name': 'Spirit Link',
        'mana_cost': 100,
        'target': 'group',
        'duration_ticks': 15,
        'level_required': 38,
        'class_required': 'cleric',
        'cooldown': 120,
        'special': 'spirit_link',
        'affects': [{'type': 'spirit_link', 'value': 1}],
        'message_self': 'You link the spirits of your allies - damage is shared equally!',
        'message_room': 'Glowing spirit chains connect everyone in $n\'s group!',
    },
    'mass_dispel': {
        'name': 'Mass Dispel',
        'mana_cost': 80,
        'target': 'room',
        'level_required': 44,
        'class_required': 'cleric',
        'cooldown': 60,
        'special': 'mass_dispel',
        'message_self': 'You unleash a wave of purifying energy!',
        'message_room': 'A wave of holy light purges magical effects from everyone!',
    },
    'lightwell': {
        'name': 'Lightwell',
        'mana_cost': 100,
        'target': 'room',
        'duration_ticks': 30,
        'level_required': 50,
        'class_required': 'cleric',
        'cooldown': 180,
        'special': 'lightwell',
        'heal_per_tick': '2d8+5',
        'message_self': 'You summon a radiant Lightwell that pulses with healing energy!',
        'message_room': 'A pillar of holy light appears, radiating healing energy!',
    },
    'serenity': {
        'name': 'Serenity',
        'mana_cost': 150,
        'heal_dice': '100',  # Full heal single target
        'target': 'defensive',
        'level_required': 56,
        'class_required': 'cleric',
        'cooldown': 180,
        'special': 'serenity',
        'message_self': 'You channel pure divine serenity into $N, fully restoring them!',
        'message_other': 'Waves of holy serenity wash over you, fully restoring your health!',
    },
    'divine_intervention': {
        'name': 'Divine Intervention',
        'mana_cost': 300,
        'target': 'group',
        'level_required': 60,
        'class_required': 'cleric',
        'cooldown': 600,  # 10 minutes
        'special': 'divine_intervention',
        'message_self': 'You invoke DIVINE INTERVENTION - the gods themselves answer!',
        'message_room': 'The heavens OPEN as $n invokes DIVINE INTERVENTION!',
    },

    # ===== PALADIN LEVEL 31-60 =====
    'hand_of_freedom': {
        'name': 'Hand of Freedom',
        'mana_cost': 40,
        'target': 'defensive',
        'duration_ticks': 8,
        'level_required': 32,
        'class_required': 'paladin',
        'cooldown': 30,
        'special': 'hand_of_freedom',
        'message_self': 'You grant $N freedom from all bonds!',
        'message_other': 'Golden light surrounds you - you are FREE!',
    },
    'consecration': {
        'name': 'Consecration',
        'mana_cost': 60,
        'target': 'room',
        'duration_ticks': 10,
        'level_required': 38,
        'class_required': 'paladin',
        'cooldown': 20,
        'special': 'consecration',
        'damage_per_tick': '2d6+4',
        'message_self': 'You consecrate the ground with holy fire!',
        'message_room': 'Holy flames erupt from the ground around $n!',
    },
    'hammer_of_justice': {
        'name': 'Hammer of Justice',
        'mana_cost': 50,
        'damage_dice': '4d8+10',
        'target': 'offensive',
        'level_required': 44,
        'class_required': 'paladin',
        'cooldown': 45,
        'affects': [{'type': 'stunned', 'value': 1}],
        'duration_ticks': 4,
        'message_self': 'You hurl a hammer of holy justice at $N!',
        'message_room': '$n hurls a blazing hammer at $N, stunning them!',
    },
    'avenging_wrath_master': {
        'name': 'Avenging Wrath',
        'mana_cost': 120,
        'target': 'self',
        'duration_ticks': 20,
        'level_required': 50,
        'class_required': 'paladin',
        'cooldown': 180,
        'affects': [
            {'type': 'damroll', 'value': 12},
            {'type': 'hitroll', 'value': 8},
            {'type': 'heal_power', 'value': 30},
            {'type': 'haste', 'value': 1}
        ],
        'message_self': 'Wings of GOLDEN LIGHT burst from your back!',
        'message_room': 'WINGS OF LIGHT burst from $n as divine wrath fills them!',
    },
    'divine_shield_master': {
        'name': 'Divine Shield',
        'mana_cost': 80,
        'target': 'self',
        'duration_ticks': 8,
        'level_required': 56,
        'class_required': 'paladin',
        'cooldown': 300,
        'affects': [{'type': 'invulnerable', 'value': 1}],
        'message_self': 'You are surrounded by an IMPENETRABLE divine shield!',
        'message_room': '$n is encased in a bubble of PURE DIVINE LIGHT!',
    },
    'crusaders_judgment': {
        'name': "Crusader's Judgment",
        'mana_cost': 250,
        'damage_dice': '12d10+40',
        'target': 'offensive',
        'level_required': 60,
        'class_required': 'paladin',
        'cooldown': 600,
        'special': 'crusaders_judgment',
        'message_self': 'You invoke the ULTIMATE JUDGMENT of the Light!',
        'message_room': 'Divine power EXPLODES as $n calls down CRUSADER\'S JUDGMENT!',
    },

    # ===== NECROMANCER LEVEL 31-60 =====
    'death_coil': {
        'name': 'Death Coil',
        'mana_cost': 45,
        'damage_dice': '3d8+8',
        'heal_dice': '4d8+12',
        'target': 'offensive',
        'level_required': 32,
        'class_required': 'necromancer',
        'cooldown': 12,
        'special': 'death_coil',
        'message_self': 'You hurl a coil of death energy at $N!',
        'message_room': '$n hurls dark death energy at $N!',
    },
    'corpse_shield': {
        'name': 'Corpse Shield',
        'mana_cost': 60,
        'target': 'self',
        'duration_ticks': 15,
        'level_required': 38,
        'class_required': 'necromancer',
        'cooldown': 60,
        'special': 'corpse_shield',
        'affects': [{'type': 'damage_redirect_pet', 'value': 50}],
        'message_self': 'Your undead minion forms a protective barrier around you!',
        'message_room': 'Bones and shadow swirl around $n protectively!',
    },
    'plague_strike': {
        'name': 'Plague Strike',
        'mana_cost': 55,
        'damage_dice': '3d6+5',
        'target': 'offensive',
        'level_required': 44,
        'class_required': 'necromancer',
        'cooldown': 20,
        'special': 'plague_strike',
        'affects': [{'type': 'plague', 'value': 1}],
        'duration_ticks': 10,
        'message_self': 'You strike $N with virulent plague!',
        'message_room': '$n strikes $N with a diseased blow that spreads to nearby foes!',
    },
    'summon_gargoyle': {
        'name': 'Summon Gargoyle',
        'mana_cost': 100,
        'target': 'self',
        'duration_ticks': 30,
        'level_required': 50,
        'class_required': 'necromancer',
        'cooldown': 180,
        'special': 'summon_gargoyle',
        'message_self': 'You summon a fearsome gargoyle from the shadows!',
        'message_room': 'A stone gargoyle materializes beside $n, ready to serve!',
    },
    'soul_harvest': {
        'name': 'Soul Harvest',
        'mana_cost': 80,
        'target': 'self',
        'level_required': 56,
        'class_required': 'necromancer',
        'cooldown': 120,
        'special': 'soul_harvest',
        'message_self': 'You harvest the essence of fallen souls!',
        'message_room': 'Dark tendrils reach out from $n, gathering essence from the fallen!',
    },
    'apocalypse_necro': {
        'name': 'Apocalypse',
        'mana_cost': 250,
        'target': 'room',
        'level_required': 60,
        'class_required': 'necromancer',
        'cooldown': 600,
        'special': 'apocalypse_necro',
        'message_self': 'You unleash the APOCALYPSE - every corpse in the zone RISES!',
        'message_room': 'The ground TEARS OPEN as $n commands an ARMY OF THE DEAD to rise!',
    },

    # ===== BARD LEVEL 31-60 =====
    'hymn_of_hope': {
        'name': 'Hymn of Hope',
        'mana_cost': 50,
        'target': 'group',
        'duration_ticks': 20,
        'level_required': 32,
        'class_required': 'bard',
        'cooldown': 60,
        'affects': [
            {'type': 'mana_regen', 'value': 100},
            {'type': 'max_mana', 'value': 50}
        ],
        'message_self': 'You sing a hymn of hope that restores magical energy!',
        'message_room': '$n\'s hymn fills the air, restoring magical energy to all!',
    },
    'chord_of_disruption': {
        'name': 'Chord of Disruption',
        'mana_cost': 70,
        'target': 'room',
        'level_required': 38,
        'class_required': 'bard',
        'cooldown': 45,
        'affects': [{'type': 'silenced', 'value': 1}],
        'duration_ticks': 4,
        'message_self': 'You strike a discordant chord that silences all foes!',
        'message_room': 'A JARRING chord from $n silences everyone in the room!',
    },
    'epic_tale': {
        'name': 'Epic Tale',
        'mana_cost': 100,
        'target': 'group',
        'duration_ticks': 30,
        'level_required': 44,
        'class_required': 'bard',
        'cooldown': 120,
        'affects': [
            {'type': 'str', 'value': 3},
            {'type': 'int', 'value': 3},
            {'type': 'wis', 'value': 3},
            {'type': 'dex', 'value': 3},
            {'type': 'con', 'value': 3},
            {'type': 'cha', 'value': 3}
        ],
        'message_self': 'You weave an epic tale that empowers your allies!',
        'message_room': '$n tells an EPIC TALE that fills everyone with power!',
    },
    'siren_song': {
        'name': 'Siren Song',
        'mana_cost': 80,
        'target': 'room',
        'level_required': 50,
        'class_required': 'bard',
        'cooldown': 90,
        'special': 'siren_song',
        'affects': [{'type': 'charmed', 'value': 1}],
        'duration_ticks': 8,
        'message_self': 'You sing an irresistible siren song!',
        'message_room': '$n\'s enchanting voice captivates everyone in the room!',
    },
    'requiem': {
        'name': 'Requiem',
        'mana_cost': 100,
        'target': 'room',
        'duration_ticks': 15,
        'level_required': 56,
        'class_required': 'bard',
        'cooldown': 120,
        'special': 'requiem',
        'damage_per_tick': '3d6+5',
        'message_self': 'You begin a haunting requiem that drains the life of enemies!',
        'message_room': 'A mournful requiem fills the air, sapping the life of enemies!',
    },
    'magnum_opus': {
        'name': 'Magnum Opus',
        'mana_cost': 200,
        'target': 'group',
        'duration_ticks': 30,
        'level_required': 60,
        'class_required': 'bard',
        'cooldown': 600,
        'special': 'magnum_opus',
        'affects': [
            {'type': 'all_stats', 'value': 5},
            {'type': 'damroll', 'value': 10},
            {'type': 'hitroll', 'value': 10},
            {'type': 'haste', 'value': 1},
            {'type': 'damage_reduction', 'value': 20}
        ],
        'message_self': 'You perform your MAGNUM OPUS - the ultimate masterpiece!',
        'message_room': '$n performs their MAGNUM OPUS - music of LEGENDARY power fills the air!',
    },

}

# ========== RANGER COMPANION SYSTEM ==========
# Animal companions that rangers can tame and bond with.

RANGER_COMPANIONS = {
    'wolf': {
        'name': 'Wolf',
        'keywords': ['wolf', 'grey wolf', 'timber wolf', 'dire wolf'],
        'level_required': 5,
        'hp_mult': 0.8,      # 80% of ranger HP
        'damage_mult': 1.0,  # 100% damage
        'armor_class': 80,
        'attack_speed': 'fast',
        'special': 'trip',
        'special_chance': 20,
        'description': 'A loyal grey wolf with piercing yellow eyes.',
        'attack_msg': '$n lunges at $N with snapping jaws!',
        'special_msg': '$n trips $N, sending them sprawling!',
    },
    'bear': {
        'name': 'Bear',
        'keywords': ['bear', 'brown bear', 'black bear', 'grizzly'],
        'level_required': 10,
        'hp_mult': 1.5,      # 150% of ranger HP
        'damage_mult': 0.8,  # 80% damage
        'armor_class': 60,
        'attack_speed': 'slow',
        'special': 'maul',
        'special_chance': 25,
        'description': 'A massive brown bear with powerful claws.',
        'attack_msg': '$n swipes at $N with massive claws!',
        'special_msg': '$n mauls $N savagely, leaving deep wounds!',
    },
    'hawk': {
        'name': 'Hawk',
        'keywords': ['hawk', 'falcon', 'eagle', 'bird of prey'],
        'level_required': 8,
        'hp_mult': 0.5,      # 50% of ranger HP
        'damage_mult': 0.6,  # 60% damage
        'armor_class': 120,  # Hard to hit
        'attack_speed': 'very_fast',
        'special': 'flyby',
        'special_chance': 100,  # Always
        'description': 'A keen-eyed hawk with razor-sharp talons.',
        'attack_msg': '$n dives at $N with talons extended!',
        'special_msg': '$n swoops past $N too quickly to counter!',
    },
    'cat': {
        'name': 'Great Cat',
        'keywords': ['cat', 'panther', 'lion', 'tiger', 'leopard', 'cougar'],
        'level_required': 12,
        'hp_mult': 0.7,      # 70% of ranger HP
        'damage_mult': 1.2,  # 120% damage
        'armor_class': 90,
        'attack_speed': 'fast',
        'special': 'pounce',
        'special_chance': 100,  # Always from stealth
        'description': 'A sleek predator with deadly grace.',
        'attack_msg': '$n rakes $N with razor claws!',
        'special_msg': '$n pounces from the shadows, rending $N!',
    },
    'boar': {
        'name': 'Boar',
        'keywords': ['boar', 'wild boar', 'warthog', 'pig'],
        'level_required': 7,
        'hp_mult': 1.2,      # 120% of ranger HP
        'damage_mult': 0.9,  # 90% damage
        'armor_class': 70,
        'attack_speed': 'medium',
        'special': 'charge',
        'special_chance': 100,  # On engage
        'description': 'A fierce wild boar with sharp tusks.',
        'attack_msg': '$n gores $N with sharp tusks!',
        'special_msg': '$n charges $N, stunning them!',
    },
}

# ========== BARD SONG SYSTEM ==========
# Songs are ongoing performances that apply effects each tick while active.
# Unlike spells, songs drain mana per tick and can be interrupted.

BARD_SONGS = {
    # ===== COMBAT SONGS =====
    'courage': {
        'name': 'Song of Courage',
        'level': 1,
        'mana_per_tick': 3,
        'target': 'allies',
        'affects': [
            {'type': 'hitroll', 'value': 2},
            {'type': 'damroll', 'value': 1}
        ],
        'start_self': "You begin singing a stirring song of courage!",
        'start_room': "$n begins singing a stirring, courageous tune!",
        'tick_self': "♪ Your song of courage fills your allies with valor! ♪",
        'tick_room': "♪ $n's courageous melody echoes through the room! ♪",
        'end_self': "Your song of courage fades away.",
        'end_room': "$n stops singing.",
    },
    'battle_hymn': {
        'name': 'Battle Hymn',
        'level': 10,
        'mana_per_tick': 4,
        'target': 'allies',
        'affects': [
            {'type': 'haste', 'value': 1},  # Extra attack chance
            {'type': 'hitroll', 'value': 1}
        ],
        'start_self': "You begin a thunderous battle hymn!",
        'start_room': "$n begins a thunderous battle hymn!",
        'tick_self': "♪ Your battle hymn drives your allies into a fighting frenzy! ♪",
        'tick_room': "♪ $n's battle hymn echoes with martial power! ♪",
        'end_self': "Your battle hymn fades into silence.",
        'end_room': "$n's battle hymn ends.",
    },
    'dirge': {
        'name': 'Dirge of Doom',
        'level': 15,
        'mana_per_tick': 4,
        'target': 'enemies',
        'affects': [
            {'type': 'hitroll', 'value': -2},
            {'type': 'damroll', 'value': -1},
            {'type': 'saving_throw', 'value': -1}
        ],
        'start_self': "You begin a mournful dirge of doom...",
        'start_room': "$n begins a haunting, mournful dirge...",
        'tick_self': "♪ Your dirge saps the will of your enemies! ♪",
        'tick_room': "♪ $n's mournful dirge fills the room with dread! ♪",
        'end_self': "Your dirge of doom fades to silence.",
        'end_room': "$n's dirge fades into silence.",
    },
    'discord': {
        'name': 'Discordant Note',
        'level': 25,
        'mana_per_tick': 5,
        'target': 'enemies',
        'affects': [
            {'type': 'fumble', 'value': 20}  # 20% chance to fumble attacks
        ],
        'special': 'discord',
        'start_self': "You begin playing jarring, discordant notes!",
        'start_room': "$n begins playing horribly discordant music!",
        'tick_self': "♪ Your discordant notes throw enemies off balance! ♪",
        'tick_room': "♪ $n's jarring notes pierce the ears painfully! ♪",
        'end_self': "Your discordant melody ends.",
        'end_room': "$n stops the jarring noise.",
    },
    
    # ===== SUPPORT SONGS =====
    'rest': {
        'name': 'Song of Rest',
        'level': 3,
        'mana_per_tick': 2,
        'target': 'allies',
        'combat_only': False,  # Only works out of combat
        'affects': [
            {'type': 'hp_regen', 'value': 50},   # +50% regen
            {'type': 'mana_regen', 'value': 50},
            {'type': 'move_regen', 'value': 50}
        ],
        'start_self': "You begin a soothing melody of rest and recovery...",
        'start_room': "$n begins playing a gentle, soothing melody...",
        'tick_self': "♪ Your song of rest helps your allies recover... ♪",
        'tick_room': "♪ $n's soothing melody washes over the room... ♪",
        'end_self': "Your song of rest ends.",
        'end_room': "$n's soothing melody fades.",
    },
    'lullaby': {
        'name': 'Lullaby',
        'level': 12,
        'mana_per_tick': 5,
        'target': 'enemies',
        'special': 'sleep',
        'save_penalty_per_tick': 5,  # -5% save per tick (cumulative)
        'start_self': "You begin singing a gentle, drowsy lullaby...",
        'start_room': "$n begins singing a soft, drowsy lullaby...",
        'tick_self': "♪ Your lullaby lulls enemies toward slumber... ♪",
        'tick_room': "♪ $n's lullaby makes it hard to stay awake... ♪",
        'end_self': "Your lullaby fades away.",
        'end_room': "$n stops singing the lullaby.",
    },
    'inspiration': {
        'name': 'Inspiring Ballad',
        'level': 20,
        'mana_per_tick': 4,
        'target': 'allies',
        'affects': [
            {'type': 'all_stats', 'value': 1},  # +1 to all stats
            {'type': 'xp_bonus', 'value': 10}   # +10% XP
        ],
        'start_self': "You begin an inspiring ballad of legendary heroes!",
        'start_room': "$n begins singing an inspiring ballad of heroism!",
        'tick_self': "♪ Your inspiring ballad fills allies with confidence! ♪",
        'tick_room': "♪ $n's inspiring ballad echoes with tales of glory! ♪",
        'end_self': "Your inspiring ballad ends.",
        'end_room': "$n's inspiring ballad comes to an end.",
    },
    
    # ===== ULTIMATE SONG =====
    'destruction': {
        'name': 'Symphony of Destruction',
        'level': 35,
        'mana_per_tick': 8,
        'target': 'enemies',
        'damage_per_tick': '2d6',
        'special': 'sonic_damage',
        'affects': [
            {'type': 'deafen', 'value': 15}  # 15% chance to deafen per tick
        ],
        'start_self': "You begin a devastating symphony of destruction!",
        'start_room': "$n begins playing a terrifying, destructive symphony!",
        'tick_self': "♪ Your symphony tears at your enemies with sonic fury! ♪",
        'tick_room': "♪ $n's devastating symphony shakes the very air! ♪",
        'end_self': "Your symphony of destruction ends.",
        'end_room': "$n's symphony of destruction finally ends.",
    },

}


class SpellHandler:
    """Handles spell casting and effects."""
    
    config = Config()

    @classmethod
    async def cast_spell(cls, caster: 'Player', spell_name: str, target_name: Optional[str] = None):
        """Cast a spell."""
        c = cls.config.COLORS
        
        # Get spell data
        spell = SPELLS.get(spell_name)
        if not spell:
            await caster.send(f"Unknown spell: {spell_name}")
            return
        
        # Check if channeling dark ritual (necromancer)
        if getattr(caster, 'channeling_ritual', False):
            await caster.send(f"{c['red']}You cannot cast spells while channeling the dark ritual!{c['reset']}")
            return
            
        # Check mana - apply soul fragment discount
        mana_cost = spell.get('mana_cost', 10)
        original_cost = mana_cost
        fragment_used = False

        # Clearcast / Presence of Mind
        if getattr(caster, 'clearcast_next', False):
            mana_cost = 0
            caster.clearcast_next = False
        if hasattr(caster, 'affect_flags') and 'presence_of_mind' in caster.affect_flags:
            mana_cost = 0
            try:
                from affects import AffectManager
                # remove presence of mind
                for affect in getattr(caster, 'affects', [])[:]:
                    if getattr(affect, 'applies_to', '') == 'presence_of_mind':
                        AffectManager.remove_affect(caster, affect)
            except Exception:
                pass

        # Arcane Power increases mana cost
        if hasattr(caster, 'affect_flags') and 'arcane_power' in caster.affect_flags:
            mana_cost = int(mana_cost * 1.3)

        # Mage arcane charges increase mana cost by 10% per charge
        if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'mage':
            charges = getattr(caster, 'arcane_charges', 0)
            if charges > 0:
                mana_cost = int(mana_cost * (1 + 0.10 * charges))
        
        # Soul fragments reduce mana cost by 10% per fragment
        if hasattr(caster, 'soul_fragments') and caster.soul_fragments > 0:
            import time
            if time.time() < getattr(caster, 'soul_fragment_expires', 0):
                discount = mana_cost * 0.10 * caster.soul_fragments
                mana_cost = max(1, int(mana_cost - discount))
                fragment_used = True
        
        if caster.mana < mana_cost:
            await caster.send(f"{c['red']}You don't have enough mana to cast that spell.{c['reset']}")
            return
            
        # Check proficiency for failure
        proficiency = caster.spells.get(spell_name, 50)
        if random.randint(1, 100) > proficiency:
            caster.mana -= mana_cost // 2
            await caster.send(f"{c['yellow']}You lose your concentration and the spell fizzles.{c['reset']}")
            return
            
        # Get target
        target = await cls.get_target(caster, spell, target_name)
        if target is None and spell['target'] not in ('self', 'special', 'object', 'door', 'group', 'room'):
            await caster.send("Cast the spell on whom?")
            return
            
        # Deduct mana
        caster.mana -= mana_cost
        
        # Consume a soul fragment if used
        if fragment_used and hasattr(caster, 'soul_fragments'):
            caster.soul_fragments -= 1
            if caster.soul_fragments <= 0:
                caster.soul_fragments = 0
                await caster.send(f"{c['cyan']}Your last soul fragment is consumed! (Cost: {mana_cost}/{original_cost}){c['reset']}")
            else:
                await caster.send(f"{c['cyan']}Soul fragment consumed! Mana cost: {mana_cost}/{original_cost} ({caster.soul_fragments} remaining){c['reset']}")

        # Apply spell effect
        await cls.apply_spell(caster, target, spell, spell_name)

        # Talent procs: clearcast
        try:
            from talents import TalentManager
            proc = TalentManager.get_proc_chance(caster, 'clearcast')
            if proc > 0 and random.randint(1, 100) <= proc:
                caster.clearcast_next = True
                await caster.send(f"{c['cyan']}Arcane Concentration! Your next spell is free.{c['reset']}")
        except Exception:
            pass

        # Attempt to improve spell proficiency through successful casting
        if hasattr(caster, 'improve_spell'):
            await caster.improve_spell(spell_name)
        
    @classmethod
    async def get_target(cls, caster: 'Player', spell: dict, target_name: Optional[str]) -> Optional['Character']:
        """Get the target for a spell."""
        target_type = spell.get('target', 'offensive')

        if target_type == 'self':
            return caster

        if target_type in ('object', 'door'):
            # For object/door-target spells (like identify/break door), return the item name
            # The actual item will be found in handle_special_spell
            return target_name if target_name else None

        if target_type == 'special':
            # Some special spells need a target name (summon, etc.)
            return target_name if target_name else caster

        if target_type in ('group', 'room'):
            return caster

        if target_type == 'pet':
            # Target must be one of the caster's pets
            if not target_name:
                await caster.send("Which pet do you want to target?")
                return None
            
            from pets import PetManager
            pets = PetManager.get_player_pets(caster)
            for pet in pets:
                if target_name.lower() in pet.name.lower():
                    return pet
            
            await caster.send(f"You don't have a pet named '{target_name}'.")
            return None

        if target_type == 'defensive':
            # Defensive spells default to self
            if not target_name:
                return caster
            # Or can target others
            for char in caster.room.characters:
                if target_name.lower() in char.name.lower():
                    return char
            return None

        if target_type == 'offensive':
            # If already fighting, target opponent
            if caster.is_fighting and not target_name:
                return caster.fighting

            # Check for pre-set target (from 'target' command)
            if not target_name and hasattr(caster, 'target') and caster.target:
                # Make sure target is still in the room
                if caster.target in caster.room.characters:
                    return caster.target

            # Otherwise need explicit target
            if not target_name:
                return None

            for char in caster.room.characters:
                if char != caster and target_name.lower() in char.name.lower():
                    return char
            return None

        return caster
        
    @classmethod
    async def apply_spell(cls, caster: 'Player', target: 'Character', spell: dict, spell_name: str):
        """Apply a spell's effects."""
        c = cls.config.COLORS

        # Boss magic immunity check
        if target and not isinstance(target, str) and spell.get('target') == 'offensive':
            if getattr(target, 'is_boss', False):
                immune_until = getattr(target, 'ai_state', {}).get('magic_immune_until', 0)
                if time.time() < immune_until:
                    await caster.send(f"{c['red']}{target.name} shrugs off your magic!{c['reset']}")
                    if caster.room:
                        await caster.room.send_to_room(
                            f"{target.name} is unaffected by the spell.",
                            exclude=[caster]
                        )
                    return
        
        # Send cast messages
        if isinstance(target, str):
            # Object/door/special target strings
            if spell.get('message_self'):
                msg_self = spell['message_self'].replace('$N', target).replace('$n', caster.name)
                await caster.send(f"{c['bright_magenta']}{msg_self}{c['reset']}")
            if spell.get('message_room') and caster.room:
                msg_room = spell['message_room'].replace('$N', target).replace('$n', caster.name)
                await caster.room.send_to_room(
                    f"{c['bright_magenta']}{msg_room}{c['reset']}",
                    exclude=[caster]
                )
        elif target == caster:
            if spell.get('message_self'):
                msg_self = spell['message_self'].replace('$N', caster.name).replace('$n', caster.name)
                await caster.send(f"{c['bright_magenta']}{msg_self}{c['reset']}")
            # Group/room spells should still announce to the room
            if spell.get('message_room') and spell.get('target') in ('group', 'room') and caster.room:
                msg_room = spell['message_room'].replace('$N', caster.name).replace('$n', caster.name)
                await caster.room.send_to_room(
                    f"{c['bright_magenta']}{msg_room}{c['reset']}",
                    exclude=[caster]
                )
        else:
            # Offensive message
            msg_self = spell.get('message_self', f'You cast {spell["name"]} at $N!')
            msg_self = msg_self.replace('$N', target.name).replace('$n', caster.name)
            await caster.send(f"{c['bright_magenta']}{msg_self}{c['reset']}")
            
            if hasattr(target, 'send'):
                msg_target = msg_self.replace('You', caster.name).replace('your', f"{caster.name}'s")
                await target.send(f"\r\n{c['bright_magenta']}{msg_target}{c['reset']}")
                
            msg_room = spell.get('message_room', f'{caster.name} casts {spell["name"]} at {target.name}!')
            msg_room = msg_room.replace('$N', target.name).replace('$n', caster.name)
            await caster.room.send_to_room(
                f"{c['bright_magenta']}{msg_room}{c['reset']}",
                exclude=[caster, target]
            )
            
        # If target is a string (object/door/special), handle special and exit
        if isinstance(target, str):
            if spell.get('special'):
                await cls.handle_special_spell(caster, target, spell)
            return

        # Check for saving throw (for debuffs)
        if spell.get('save') and target != caster:
            save_roll = random.randint(1, 20) + target.wis // 2
            if save_roll > 10 + caster.level // 2:
                await caster.send(f"{c['yellow']}{target.name} resists your spell!{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['cyan']}You resist the spell!{c['reset']}")
                return
                
        # Apply damage spells
        if 'damage_dice' in spell:
            # Room-target spells (like earthquake) handle damage in their special handler
            if spell.get('target') == 'room':
                pass
            # Dispel evil should not harm non-evil targets
            elif spell.get('special') == 'dispel_evil' and (not hasattr(target, 'alignment') or target.alignment >= -100):
                await caster.send(f"{c['yellow']}{target.name} is not evil enough to be affected.{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['cyan']}You resist the holy power!{c['reset']}")
                return
            else:
                damage = cls.roll_dice(spell['damage_dice'])
                damage += spell.get('damage_per_level', 0) * caster.level
                # Affix bonuses: spell_power and per-spell bonus (percentage)
                spell_bonus = caster.get_equipment_bonus('spell_power') + caster.get_equipment_bonus(spell_name)
                if spell_bonus:
                    damage = int(damage * (1 + (spell_bonus / 100)))

                # Apply weather modifier to damage
                if caster.room and caster.room.zone and hasattr(caster.room.zone, 'weather'):
                    weather_mult = caster.room.zone.weather.get_spell_modifier(spell['name'])
                    damage = int(damage * weather_mult)

                # Soulstone bonus (necromancer offhand)
                try:
                    stone = caster.equipment.get('hold') if hasattr(caster, 'equipment') else None
                    if stone and (getattr(stone, 'is_soulstone', False) or ('soulstone' in getattr(stone, 'flags', set()))):
                        damage += getattr(stone, 'soulstone_spell_damage', 2)
                except Exception:
                    pass

                # Mage arcane charges: +8% damage per charge
                if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'mage':
                    charges = getattr(caster, 'arcane_charges', 0)
                    if charges > 0:
                        damage = int(damage * (1 + (0.08 * charges)))
                        await caster.send(f"{c['magenta']}Arcane charges amplify your spell! ({charges} charges, +{charges * 8}% damage){c['reset']}")

                # Spell critical strike chance
                # Base 5% + 1% per 2 INT above 10 + 0.5% per level
                crit_chance = 5
                int_bonus = (getattr(caster, 'int', 10) - 10) // 2
                crit_chance += int_bonus
                crit_chance += caster.level // 2
                # Mage bonus: +5% spell crit
                if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'mage':
                    crit_chance += 5
                # Talent bonuses
                try:
                    from talents import TalentManager
                    crit_chance += int(TalentManager.get_talent_bonus(caster, 'stat_bonus', 'crit_chance'))
                    # Combustion increases crit chance
                    if hasattr(caster, 'affect_flags') and 'combustion' in caster.affect_flags:
                        crit_chance += 30
                except Exception:
                    pass
                crit_chance = min(crit_chance, 60)  # Cap at 60%
                
                is_crit = random.randint(1, 100) <= crit_chance
                if is_crit:
                    crit_mult = 1.5  # 150% damage
                    # Mage gets better crits
                    if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'mage':
                        crit_mult = 2.0  # 200% damage
                    try:
                        from talents import TalentManager
                        crit_mult += TalentManager.get_talent_bonus(caster, 'stat_bonus', 'crit_damage') / 100.0
                    except Exception:
                        pass
                    damage = int(damage * crit_mult)
                    await caster.send(f"{c['bright_yellow']}*** CRITICAL SPELL! ***{c['reset']}")

                # Apply spell damage
                killed = await target.take_damage(damage, caster)
                
                await caster.send(f"{c['bright_red']}Your spell does {damage} damage to {target.name}!{c['reset']}")

                # Build arcane charges on offensive casts
                if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'mage':
                    if hasattr(caster, 'arcane_charges') and hasattr(caster, 'max_arcane_charges'):
                        if caster.arcane_charges < caster.max_arcane_charges:
                            caster.arcane_charges += 1
                            await caster.send(f"{c['cyan']}Arcane charge gained ({caster.arcane_charges}/{caster.max_arcane_charges}).{c['reset']}")
                
                if killed:
                    from combat import CombatHandler
                    await CombatHandler.handle_death(caster, target)
                elif not caster.is_fighting and target != caster:
                    # Start combat if not already fighting
                    from combat import CombatHandler
                    await CombatHandler.start_combat(caster, target)
                    
                # Handle vampiric drain
                if spell.get('special') == 'drain_hp':
                    heal_amount = damage // 2
                    caster.hp = min(caster.max_hp, caster.hp + heal_amount)
                    await caster.send(f"{c['bright_green']}You absorb {heal_amount} life force!{c['reset']}")
                
        # Apply healing spells
        elif 'heal_dice' in spell:
            heal_str = spell['heal_dice']
            if heal_str.isdigit():
                heal = int(heal_str)  # Fixed amount (like full heal)
                if heal == 100:  # Full heal
                    heal = target.max_hp - target.hp
            else:
                heal = cls.roll_dice(heal_str)
                heal += spell.get('heal_per_level', 0) * caster.level

            # Affix bonuses: heal_power and per-spell bonus (percentage)
            heal_bonus = caster.get_equipment_bonus('heal_power') + caster.get_equipment_bonus(spell_name)
            if heal_bonus:
                heal = int(heal * (1 + (heal_bonus / 100)))

            # Group heal affects all group members in the room + their pets
            if spell.get('target') == 'group':
                targets = [caster]
                if hasattr(caster, 'group') and caster.group:
                    targets = [m for m in caster.group.members if m.room == caster.room]
                
                # Add pets belonging to any target in the room
                from pets import PetManager
                all_targets = list(targets)
                for member in targets:
                    member_pets = PetManager.get_player_pets(member)
                    for pet in member_pets:
                        if pet.room == caster.room and pet not in all_targets:
                            all_targets.append(pet)
                targets = all_targets

                for member in targets:
                    old_hp = member.hp
                    member.hp = min(member.max_hp, member.hp + heal)
                    actual_heal = member.hp - old_hp

                    if member == caster:
                        await caster.send(f"{c['bright_green']}You heal {actual_heal} hit points!{c['reset']}")
                    else:
                        await caster.send(f"{c['bright_green']}You heal {member.name} for {actual_heal} hit points!{c['reset']}")
                        if hasattr(member, 'send'):
                            await member.send(f"{c['bright_green']}{caster.name} heals you for {actual_heal} hit points!{c['reset']}")

                    # Cleric divine favor gain on healing
                    if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'cleric':
                        if hasattr(caster, 'divine_favor'):
                            gain = max(2, actual_heal // 5)
                            caster.divine_favor = min(100, caster.divine_favor + gain)

                        # Cleric Faith generation from healing
                        if hasattr(caster, 'faith') and not getattr(caster, 'shadow_form', False):
                            if actual_heal > 0 and caster.faith < 10:
                                caster.faith = min(10, caster.faith + 1)
                                await caster.send(f"{c['bright_yellow']}[Faith: {caster.faith}/10]{c['reset']}")

                    # Bard Inspiration from healing allies
                    if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'bard':
                        if hasattr(caster, 'inspiration') and actual_heal > 0 and member != caster:
                            if caster.inspiration < 10:
                                caster.inspiration = min(10, caster.inspiration + 1)
                                await caster.send(f"{c['bright_yellow']}[Inspiration: {caster.inspiration}/10]{c['reset']}")
            else:
                old_hp = target.hp
                target.hp = min(target.max_hp, target.hp + heal)
                actual_heal = target.hp - old_hp
                
                if target == caster:
                    await caster.send(f"{c['bright_green']}You heal {actual_heal} hit points!{c['reset']}")
                else:
                    await caster.send(f"{c['bright_green']}You heal {target.name} for {actual_heal} hit points!{c['reset']}")
                    if hasattr(target, 'send'):
                        await target.send(f"{c['bright_green']}{caster.name} heals you for {actual_heal} hit points!{c['reset']}")

                # Cleric divine favor gain on healing
                if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'cleric':
                    if hasattr(caster, 'divine_favor'):
                        gain = max(2, actual_heal // 5)
                        caster.divine_favor = min(100, caster.divine_favor + gain)

                    # Cleric Faith generation from healing
                    if hasattr(caster, 'faith') and not getattr(caster, 'shadow_form', False):
                        if actual_heal > 0 and caster.faith < 10:
                            caster.faith = min(10, caster.faith + 1)
                            await caster.send(f"{c['bright_yellow']}[Faith: {caster.faith}/10]{c['reset']}")

                # Bard Inspiration from healing allies
                if hasattr(caster, 'char_class') and str(caster.char_class).lower() == 'bard':
                    if hasattr(caster, 'inspiration') and actual_heal > 0 and target != caster:
                        if caster.inspiration < 10:
                            caster.inspiration = min(10, caster.inspiration + 1)
                            await caster.send(f"{c['bright_yellow']}[Inspiration: {caster.inspiration}/10]{c['reset']}")

        # Apply buff/debuff affects
        if 'affects' in spell:
            duration = spell.get('duration_ticks', 24)
            # Level scaling for certain buffs (armor, shield, etc.)
            if spell.get('scales_duration'):
                # Add 2 ticks per level (at 6 sec/tick: +12 sec per level)
                # Level 1: 100 + 2 = 102 ticks (~10 min)
                # Level 15: 100 + 30 = 130 ticks (~13 min)
                # Level 30: 100 + 60 = 160 ticks (~16 min)
                duration = duration + (caster.level * 2)
            for affect in spell['affects']:
                await cls.apply_affect(target, affect, duration, spell['name'], caster.level)
                
        # Handle special spells
        if spell.get('special'):
            await cls.handle_special_spell(caster, target, spell)
            
    @classmethod
    async def apply_affect(cls, target: 'Character', affect: dict, duration: int, spell_name: str = 'unknown', caster_level: int = 1):
        """Apply a spell affect to a character using the AffectManager."""
        affect_type = affect['type']
        value = affect['value']

        # Determine if this is a stat modification or a flag
        stat_types = {'hitroll', 'damroll', 'ac', 'str', 'int', 'wis', 'dex', 'con', 'cha',
                     'armor_class', 'max_hp', 'max_mana', 'max_move', 'saving_throw',
                     'spell_resist', 'damage_reduction'}
        flag_types = {'blind', 'invisible', 'sanctuary', 'haste', 'fly', 'detect_magic',
                     'detect_invisible', 'sense_life', 'waterwalk', 'stoneskin', 'mirror_image',
                     'displacement', 'mana_shield', 'ice_armor', 'fire_shield', 'spell_reflect',
                     'blink', 'prot_evil', 'prot_good', 'divine_shield', 'invulnerable',
                     'detect_evil', 'charmed', 'entangled', 'sleeping', 'stunned', 'slow',
                     'combustion', 'presence_of_mind', 'arcane_power', 'guardian_spirit',
                     'beacon_of_light', 'holy_shield', 'divine_guardian', 'aegis_ward', 'shadowform'}

        # Create affect data for AffectManager
        affect_data = {
            'name': spell_name,
            'duration': duration,
            'caster_level': caster_level,
            'applies_to': affect_type,
            'value': value
        }

        if affect_type in stat_types:
            # Convert 'ac' to 'armor_class' for consistency
            if affect_type == 'ac':
                affect_data['applies_to'] = 'armor_class'
            affect_data['type'] = AffectManager.TYPE_MODIFY_STAT
        elif affect_type == 'poison':
            # Apply poison DOT and poisoned flag
            dot_data = {
                'name': 'poison',
                'type': AffectManager.TYPE_DOT,
                'applies_to': 'hp',
                'value': max(1, value),
                'duration': duration,
                'caster_level': caster_level
            }
            AffectManager.apply_affect(target, dot_data)

            flag_data = {
                'name': 'poison',
                'type': AffectManager.TYPE_FLAG,
                'applies_to': 'poisoned',
                'value': 1,
                'duration': duration,
                'caster_level': caster_level
            }
            AffectManager.apply_affect(target, flag_data)
            return
        elif affect_type in flag_types:
            affect_data['type'] = AffectManager.TYPE_FLAG
            # Absorption shields keep their value, other flags are binary
            if affect_type not in ('divine_shield', 'stoneskin'):
                affect_data['value'] = 1  # Flags are binary (on/off)
        elif affect_type == 'sleep':
            # Special case: sleep changes position immediately
            target.position = 'sleeping'
            affect_data['type'] = AffectManager.TYPE_FLAG
            affect_data['applies_to'] = 'sleeping'
        else:
            logger.warning(f"Unknown affect type '{affect_type}' for spell {spell_name}")
            return

        # Apply the affect using AffectManager
        AffectManager.apply_affect(target, affect_data)
                
    @classmethod
    async def handle_special_spell(cls, caster: 'Player', target: 'Character', spell: dict):
        """Handle special spell effects."""
        from affects import AffectManager
        c = cls.config.COLORS
        special = spell.get('special')

        if special == 'cold_snap':
            # Refresh frost-related cooldowns/flags
            for attr in ['last_ice_lance', 'last_deep_freeze', 'last_howling_blast']:
                if hasattr(caster, attr):
                    setattr(caster, attr, 0)
            await caster.send(f"{c['cyan']}Your frost power surges anew.{c['reset']}")
            return

        elif special == 'mana_rift':
            # Convert mana into damage
            mana_spent = min(50, caster.mana)
            caster.mana -= mana_spent
            damage = mana_spent * 2 + caster.level
            await caster.send(f"{c['magenta']}Mana Rift tears into {target.name} for {damage} damage!{c['reset']}")
            killed = await target.take_damage(damage, caster)
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
            return

        elif special == 'shadow_word_pain':
            from affects import AffectManager
            AffectManager.apply_affect(target, {
                'name': 'shadow_word_pain',
                'type': AffectManager.TYPE_DOT,
                'applies_to': 'hp',
                'value': 6 + caster.level // 5,
                'duration': 6,
                'caster_level': caster.level
            })
            await caster.send(f"{c['magenta']}Shadow pain wracks {target.name}!{c['reset']}")
            return

        elif special == 'holy_shock':
            # If target is ally (or self), heal; otherwise damage
            if target == caster or hasattr(target, 'connection'):
                heal = cls.roll_dice('3d6') + caster.level
                target.hp = min(target.max_hp, target.hp + heal)
                await caster.send(f"{c['bright_green']}Holy Shock heals {target.name} for {heal}!{c['reset']}")
            else:
                damage = cls.roll_dice('3d6') + caster.level
                await caster.send(f"{c['bright_yellow']}Holy Shock strikes {target.name} for {damage}!{c['reset']}")
                killed = await target.take_damage(damage, caster)
                if killed:
                    from combat import CombatHandler
                    await CombatHandler.handle_death(caster, target)
            return

        elif special == 'lay_on_hands':
            # Massive heal that consumes all remaining mana
            mana_spent = caster.mana
            if mana_spent < 20:
                await caster.send(f"{c['yellow']}You need at least 20 mana to use Lay on Hands.{c['reset']}")
                return
            caster.mana = 0
            heal = mana_spent * 3 + caster.level * 5
            target.hp = min(target.max_hp, target.hp + heal)
            await caster.send(f"{c['bright_yellow']}You channel all your holy power into {target.name}! [+{heal} HP]{c['reset']}")
            if target != caster:
                await target.send(f"{c['bright_yellow']}{caster.name} places healing hands upon you! [+{heal} HP]{c['reset']}")
            return

        elif special == 'army_of_dead':
            from pets import PetManager
            # summon 3 temporary undead
            for _ in range(3):
                await PetManager.summon_pet(caster, 'undead_warrior', duration_minutes=3)
            await caster.send(f"{c['bright_magenta']}The dead rise to fight for you!{c['reset']}")
            return

        elif special == 'blood_boil':
            # AoE disease damage
            if caster.room:
                for char in list(caster.room.characters):
                    if char != caster and hasattr(char, 'hp'):
                        dmg = cls.roll_dice('2d6') + caster.level
                        await char.take_damage(dmg, caster)
                await caster.send(f"{c['red']}Blood boils in your enemies' veins!{c['reset']}")
            return

        elif special == 'death_strike':
            # Damage + heal based on damage dealt
            damage = cls.roll_dice('4d6') + caster.level * 2
            await caster.send(f"{c['red']}Death Strike hits {target.name} for {damage}!{c['reset']}")
            killed = await target.take_damage(damage, caster)
            # Heal for 25% of damage dealt
            heal = damage // 4
            caster.hp = min(caster.max_hp, caster.hp + heal)
            await caster.send(f"{c['bright_green']}You drain {heal} life from the strike!{c['reset']}")
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
            return

        elif special == 'finger_of_death':
            # Finger of Death: massive damage + instant kill chance on low HP targets
            import random
            
            # Calculate damage: 12d10+30 + 8 per level
            damage = cls.roll_dice('12d10+30') + (caster.level * 8)
            
            # Instant kill check: if target is below 25% HP after damage, chance to instantly kill
            # Chance = 50% base + 2% per caster level - 1% per target level
            # Bosses are immune to instant kill
            is_boss = getattr(target, 'is_boss', False)
            projected_hp = target.hp - damage
            
            if not is_boss and projected_hp < (target.max_hp * 0.25):
                kill_chance = 50 + (caster.level * 2) - (getattr(target, 'level', 1) * 1)
                kill_chance = max(10, min(90, kill_chance))  # Cap between 10-90%
                
                if random.randint(1, 100) <= kill_chance:
                    await caster.send(f"{c['bright_red']}*** DEATH CLAIMED! ***{c['reset']}")
                    await caster.send(f"{c['red']}Your finger of death instantly slays {target.name}!{c['reset']}")
                    if caster.room:
                        await caster.room.send_to_room(
                            f"{c['red']}{target.name}'s life is extinguished by {caster.name}'s dark magic!{c['reset']}",
                            exclude=[caster]
                        )
                    # Instant kill - deal remaining HP as damage
                    await target.take_damage(target.hp + 100, caster)
                    from combat import CombatHandler
                    await CombatHandler.handle_death(caster, target)
                    # Grant bonus soul fragment to necromancer
                    if hasattr(caster, 'soul_fragments'):
                        caster.soul_fragments = min(5, caster.soul_fragments + 1)
                        await caster.send(f"{c['magenta']}A soul fragment is torn from the slain!{c['reset']}")
                    return
            
            # Normal damage if instant kill didn't proc
            await caster.send(f"{c['red']}Dark energy tears through {target.name} for {damage} damage!{c['reset']}")
            killed = await target.take_damage(damage, caster)
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
                # Soul fragment on kill
                if hasattr(caster, 'soul_fragments'):
                    caster.soul_fragments = min(5, caster.soul_fragments + 1)
                    await caster.send(f"{c['magenta']}A soul fragment is torn from the slain!{c['reset']}")
            return

        elif special == 'festering_strike':
            # Damage + apply festering wound stacks
            damage = cls.roll_dice('3d6') + caster.level * 2
            await caster.send(f"{c['green']}Festering Strike hits {target.name} for {damage}!{c['reset']}")
            killed = await target.take_damage(damage, caster)
            # Add festering wounds
            from affects import AffectManager
            wounds = getattr(target, 'festering_wounds', 0) + 2
            target.festering_wounds = min(8, wounds)
            await caster.send(f"{c['green']}{target.name} has {target.festering_wounds} festering wounds!{c['reset']}")
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
            return

        elif special == 'apocalypse':
            # Burst all festering wounds on all enemies + summon ghouls
            if caster.room:
                total_burst = 0
                for char in list(caster.room.characters):
                    if char != caster and hasattr(char, 'hp'):
                        wounds = getattr(char, 'festering_wounds', 0)
                        if wounds > 0:
                            burst_damage = wounds * (10 + caster.level)
                            char.festering_wounds = 0
                            await char.take_damage(burst_damage, caster)
                            total_burst += wounds
                        # Base damage even without wounds
                        base_dmg = cls.roll_dice('3d6') + caster.level
                        await char.take_damage(base_dmg, caster)
                await caster.send(f"{c['bright_magenta']}The apocalypse consumes your enemies! ({total_burst} wounds burst){c['reset']}")
                # Summon ghouls based on wounds burst
                if total_burst > 0:
                    from pets import PetManager
                    ghouls = min(4, total_burst // 2)
                    for _ in range(ghouls):
                        await PetManager.summon_pet(caster, 'undead_warrior', duration_minutes=2)
                    await caster.send(f"{c['magenta']}{ghouls} ghouls rise from the carnage!{c['reset']}")
            return

        elif special == 'finale':
            damage = cls.roll_dice('4d6') + caster.level
            await caster.send(f"{c['bright_yellow']}Your finale crashes into {target.name}! [{damage}]{c['reset']}")
            killed = await target.take_damage(damage, caster)
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(caster, target)
            return

        elif special == 'legend_lore':
            await caster.send(f"{c['cyan']}Legends whisper of this place...{c['reset']}")
            # reuse lore command if present
            try:
                await caster.do_look([])
            except Exception:
                pass
            return

        elif special == 'raise_abomination':
            from pets import PetManager
            pet = await PetManager.summon_pet(caster, 'undead_warrior', duration_minutes=5)
            if pet:
                pet.max_hp = int(pet.max_hp * 1.5)
                pet.hp = pet.max_hp
                pet.name = 'Abomination'
                await caster.send(f"{c['bright_magenta']}A hulking abomination rises to serve you!{c['reset']}")
            return

        if special == 'animate_dead':
            # Raise a corpse as a necromancer servant
            if caster.char_class != 'necromancer':
                await caster.send(f"{c['red']}Only necromancers can animate the dead this way!{c['reset']}")
                return

            if not caster.room:
                await caster.send(f"{c['red']}You are nowhere. There is no corpse to animate.{c['reset']}")
                return

            corpse = None
            for item in caster.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpse = item
                        break

            if not corpse:
                await caster.send(f"{c['yellow']}There is no corpse here to animate.{c['reset']}")
                return

            # Determine requested pet role
            choice = None
            if isinstance(target, str):
                choice = target.strip().lower()

            role_map = {
                # Themed names
                'knight': 'undead_warrior',
                'wraith': 'undead_healer',
                'lich': 'undead_caster',
                'stalker': 'undead_rogue',
                # Legacy/alternate names
                'warrior': 'undead_warrior',
                'tank': 'undead_warrior',
                'bone': 'undead_warrior',
                'healer': 'undead_healer',
                'support': 'undead_healer',
                'caster': 'undead_caster',
                'mage': 'undead_caster',
                'rogue': 'undead_rogue',
                'shadow': 'undead_rogue',
            }

            if choice and choice not in role_map:
                await caster.send(f"{c['yellow']}Choose a servant: knight, wraith, lich, stalker.{c['reset']}")
                return

            template_name = role_map.get(choice, 'undead_warrior')

            from pets import PetManager, PET_TEMPLATES
            template = PET_TEMPLATES.get(template_name, {})
            duration_seconds = template.get('duration', 3600)
            duration_minutes = max(1, int(duration_seconds // 60))

            imbue_level = getattr(corpse, 'soul_imbue_level', 0)
            if imbue_level > 0:
                duration_minutes += 5 * imbue_level

            pet = await PetManager.summon_pet(caster, template_name, duration_minutes=duration_minutes)
            if pet:
                if imbue_level > 0:
                    bonus_mult = 1 + (0.10 * imbue_level)
                    pet.level = max(1, int(pet.level * bonus_mult))
                if corpse in caster.room.items:
                    caster.room.items.remove(corpse)
                await caster.send(
                    f"{c['bright_magenta']}You carve a sigil of bone and shadow. The corpse snaps to attention as {pet.short_desc}.{c['reset']}"
                )
                if caster.room:
                    await caster.room.send_to_room(
                        f"{c['magenta']}A chill sweeps the air as {pet.short_desc} rises to serve {caster.name}.{c['reset']}",
                        exclude=[caster]
                    )
                if imbue_level > 0:
                    await caster.send(
                        f"{c['cyan']}Soulstone imbue: +{imbue_level * 10}% level, +{imbue_level * 5} min duration{c['reset']}"
                    )
                await caster.send(f"{c['yellow']}Duration: {duration_minutes} minutes{c['reset']}")
            return

        elif special == 'heal_undead':
            # Dark Mending - heal undead pet
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only mend undead servants!{c['reset']}")
                return
            
            heal_amount = cls.roll_dice(spell.get('heal_dice', '3d8'))
            heal_amount += caster.level * spell.get('heal_per_level', 1)
            
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + heal_amount)
            actual_heal = target.hp - old_hp
            
            await caster.send(f"{c['bright_green']}You channel necrotic energy into {target.name}, healing {actual_heal} HP!{c['reset']}")
            if caster.room:
                await caster.room.send_to_room(
                    f"Dark energy flows into {target.name}, mending its form.",
                    exclude=[caster]
                )
        
        elif special == 'death_pact':
            # Create bond between caster and pet
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only bond with undead servants!{c['reset']}")
                return
            
            # Store the pact relationship
            if not hasattr(caster, 'death_pact_target'):
                caster.death_pact_target = None
            if not hasattr(target, 'death_pact_master'):
                target.death_pact_master = None
            
            caster.death_pact_target = target
            target.death_pact_master = caster
            target.death_pact_duration = spell.get('duration_ticks', 10)
            
            await caster.send(f"{c['bright_magenta']}You forge a dark bond with {target.name}!{c['reset']}")
            await caster.send(f"{c['yellow']}You will now share damage with your servant.{c['reset']}")
            if caster.room:
                await caster.room.send_to_room(
                    f"Shadowy tendrils connect {caster.name} and {target.name}.",
                    exclude=[caster]
                )
        
        elif special == 'siphon_hp':
            # Siphon Unlife - bidirectional HP transfer
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only siphon from undead servants!{c['reset']}")
                return
            
            # Parse direction from target (should be passed as string like "from knight" or "to knight")
            direction = 'from'  # default
            if isinstance(target, str):
                parts = target.lower().split()
                if 'to' in parts:
                    direction = 'to'
                elif 'from' in parts:
                    direction = 'from'
            
            if direction == 'from':
                # Drain from pet to heal caster
                transfer = int(target.hp * 0.5)
                if transfer <= 0:
                    await caster.send(f"{c['red']}{target.name} has no life force to drain!{c['reset']}")
                    return
                target.hp = max(1, target.hp - transfer)  # Don't kill the pet
                caster.hp = min(caster.max_hp, caster.hp + transfer)
                await caster.send(f"{c['bright_green']}You drain {transfer} HP from {target.name}!{c['reset']}")
                await caster.send(f"{c['yellow']}{target.name} now has {target.hp}/{target.max_hp} HP{c['reset']}")
            else:
                # Transfer from caster to heal pet
                transfer = int(caster.hp * 0.4)
                if transfer <= 0 or caster.hp <= transfer:
                    await caster.send(f"{c['red']}You don't have enough life force to transfer!{c['reset']}")
                    return
                caster.hp -= transfer
                target.hp = min(target.max_hp, target.hp + transfer)
                await caster.send(f"{c['yellow']}You transfer {transfer} HP to {target.name}!{c['reset']}")
                await caster.send(f"{c['bright_green']}{target.name} now has {target.hp}/{target.max_hp} HP{c['reset']}")
            
            if caster.room:
                await caster.room.send_to_room(
                    f"Life force flows between {caster.name} and {target.name}!",
                    exclude=[caster]
                )
        
        elif special == 'explode_corpse':
            # Corpse Explosion - AoE damage
            base_damage = cls.roll_dice(spell.get('damage_dice', '5d8'))
            
            # If target is a pet, add its remaining HP/2 to damage and destroy it
            bonus_damage = 0
            sacrificed_pet = None
            if target and hasattr(target, 'pet_type'):
                bonus_damage = int(target.hp / 2)
                sacrificed_pet = target
                await caster.send(f"{c['bright_red']}You sacrifice {target.name} in a massive explosion!{c['reset']}")
            
            total_damage = base_damage + bonus_damage
            
            # Announce explosion
            await caster.room.send_to_room(
                f"{c['bright_red']}**BOOM** A corpse explodes in a devastating blast of necrotic energy!{c['reset']}"
            )
            
            # Hit all enemies in room
            if caster.room:
                hit_count = 0
                for char in list(caster.room.characters):
                    if char != caster and not (hasattr(char, 'owner') and char.owner == caster):
                        if hasattr(char, 'hp') and hasattr(char, 'take_damage'):
                            killed = await char.take_damage(total_damage, caster)
                            await char.send(f"{c['bright_red']}The explosion engulfs you for {total_damage} damage!{c['reset']}")
                            hit_count += 1
                            if killed and hasattr(char, 'send'):
                                from combat import CombatHandler
                                await CombatHandler.handle_death(caster, char)
                
                await caster.send(f"{c['yellow']}Your explosion hits {hit_count} enemies for {total_damage} damage each!{c['reset']}")
            
            # Remove sacrificed pet if any
            if sacrificed_pet:
                if sacrificed_pet.room:
                    sacrificed_pet.room.characters.remove(sacrificed_pet)
                if hasattr(caster, 'world') and hasattr(caster.world, 'npcs'):
                    if sacrificed_pet in caster.world.npcs:
                        caster.world.npcs.remove(sacrificed_pet)
        
        elif special == 'mass_animate':
            # Mass Animate - raise 3 weak zombies
            if caster.level < spell.get('level_required', 20):
                await caster.send(f"{c['red']}You must be level {spell['level_required']} to use this spell!{c['reset']}")
                return
            
            # Find corpses in room
            corpses = []
            for item in caster.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpses.append(item)
            
            if len(corpses) < 3:
                await caster.send(f"{c['yellow']}You need at least 3 corpses to use mass animate!{c['reset']}")
                return
            
            # Raise 3 weak zombies
            from pets import PetManager
            raised = 0
            for i in range(min(3, len(corpses))):
                # Create weak zombie (50% stats of normal)
                zombie = await PetManager.summon_pet(
                    caster,
                    'undead_warrior',
                    duration_minutes=60
                )
                if zombie:
                    # Reduce stats to 50%
                    zombie.max_hp = int(zombie.max_hp * 0.5)
                    zombie.hp = zombie.max_hp
                    zombie.name = f"zombie {i+1}"
                    zombie.short_desc = f"a shambling zombie"
                    zombie.long_desc = f"A shambling zombie stands here, reeking of decay."
                    raised += 1
                    # Remove corpse
                    if corpses[i] in caster.room.items:
                        caster.room.items.remove(corpses[i])
            
            if raised > 0:
                await caster.send(f"{c['bright_magenta']}You raise {raised} zombie servants!{c['reset']}")
                await caster.room.send_to_room(
                    f"{caster.name} raises an army of undead!",
                    exclude=[caster]
                )
            else:
                await caster.send(f"{c['red']}You failed to raise any zombies!{c['reset']}")

        elif special == 'recall':
            # Teleport to temple
            if caster.room:
                await caster.room.send_to_room(
                    f"{caster.name} disappears!",
                    exclude=[caster]
                )
                caster.room.characters.remove(caster)
                
            temple = caster.world.get_room(caster.config.STARTING_ROOM)
            if temple:
                caster.room = temple
                temple.characters.append(caster)
                await caster.do_look([])
                
        elif special == 'teleport':
            # Random teleport (dangerous!)
            rooms = list(caster.world.rooms.values())
            if rooms:
                new_room = random.choice(rooms)
                if caster.room:
                    caster.room.characters.remove(caster)
                caster.room = new_room
                new_room.characters.append(caster)
                await caster.send(f"{c['bright_cyan']}You materialize in a new location!{c['reset']}")
                await caster.do_look([])
                
        elif special == 'fear':
            # Make target flee
            if hasattr(target, 'flee'):
                await target.flee()
            elif hasattr(target, 'send'):
                await target.send(f"{c['yellow']}You are overcome with fear!{c['reset']}")
                # Player attempts to flee
                from commands import CommandHandler
                await CommandHandler.cmd_flee(target, [])
                
        elif special == 'drain_exp':
            # Drain experience
            if hasattr(target, 'exp'):
                drain = target.level * 100
                target.exp = max(0, target.exp - drain)
                await caster.send(f"{c['bright_red']}You drain {drain} experience from {target.name}!{c['reset']}")

        elif special == 'break_door':
            # Break a locked door
            # Need to get direction from target_name in original cast
            direction = None
            for dir_name in caster.config.DIRECTIONS.keys():
                if target and dir_name in str(target).lower():
                    direction = dir_name
                    break

            if not direction or direction not in caster.room.exits:
                await caster.send(f"{c['red']}There's no door in that direction!{c['reset']}")
                return

            exit_data = caster.room.exits[direction]
            if 'door' not in exit_data:
                await caster.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
                return

            door = exit_data['door']

            # Make a loud noise
            await caster.room.send_to_room(
                f"{c['bright_red']}**CRASH** The {door.get('name', 'door')} explodes into splinters!{c['reset']}"
            )

            # Break the door
            door['broken'] = True
            door['state'] = 'open'
            door['locked'] = False

            # Alert nearby mobs (aggressive behavior)
            for npc in caster.room.characters:
                if npc != caster and hasattr(npc, 'flags'):
                    if 'aggressive' in npc.flags and not npc.is_fighting:
                        from combat import CombatHandler
                        await CombatHandler.start_combat(npc, caster)

        elif special == 'block_door':
            # Magically block a door
            direction = None
            for dir_name in caster.config.DIRECTIONS.keys():
                if target and dir_name in str(target).lower():
                    direction = dir_name
                    break

            if not direction or direction not in caster.room.exits:
                await caster.send(f"{c['red']}There's no door in that direction!{c['reset']}")
                return

            exit_data = caster.room.exits[direction]
            if 'door' not in exit_data:
                await caster.send(f"{c['yellow']}There's no door {direction}.{c['reset']}")
                return

            door = exit_data['door']

            # Check if already blocked
            if door.get('magically_blocked', False):
                await caster.send(f"{c['yellow']}The door is already magically sealed!{c['reset']}")
                return

            # Block the door
            door['magically_blocked'] = True
            door['block_expires'] = caster.world.game_time.hour + (spell['duration_ticks'] // 60) if hasattr(caster.world, 'game_time') else 0

            await caster.send(f"{c['bright_blue']}Magical energy surrounds the {door.get('name', 'door')}, sealing it shut!{c['reset']}")

        elif special == 'identify':
            # Identify an item in inventory, equipped, or on the ground
            if not target or not isinstance(target, str):
                await caster.send(f"{c['yellow']}Identify what item?{c['reset']}")
                return

            item_name = target.lower()
            item = None

            # Search inventory for item
            for inv_item in caster.inventory:
                if hasattr(inv_item, 'name') and hasattr(inv_item, 'short_desc'):
                    if item_name in inv_item.name.lower() or item_name in inv_item.short_desc.lower():
                        item = inv_item
                        break

            # Also check equipped items
            if not item:
                for slot, eq_item in caster.equipment.items():
                    if eq_item and hasattr(eq_item, 'name') and hasattr(eq_item, 'short_desc'):
                        if item_name in eq_item.name.lower() or item_name in eq_item.short_desc.lower():
                            item = eq_item
                            break

            # Check items on the ground in current room
            if not item and caster.room:
                for room_item in caster.room.items:
                    if hasattr(room_item, 'name') and hasattr(room_item, 'short_desc'):
                        if item_name in room_item.name.lower() or item_name in room_item.short_desc.lower():
                            item = room_item
                            break

            if not item:
                await caster.send(f"{c['yellow']}You don't see that item here.{c['reset']}")
                return

            # Display item information
            await caster.send(f"{c['bright_cyan']}{'='*60}{c['reset']}")
            await caster.send(f"{c['bright_yellow']}Item: {c['white']}{item.short_desc}{c['reset']}")
            await caster.send(f"{c['bright_cyan']}{'='*60}{c['reset']}")

            # Type
            await caster.send(f"{c['cyan']}Type:   {c['white']}{item.item_type.capitalize()}{c['reset']}")

            # Weight and value
            await caster.send(f"{c['cyan']}Weight: {c['white']}{item.weight} lbs{c['reset']}")
            await caster.send(f"{c['cyan']}Value:  {c['yellow']}{item.cost} gold{c['reset']}")

            # Weapon stats
            if item.item_type == 'weapon':
                damage = getattr(item, 'damage_dice', '1d4')
                weapon_type = getattr(item, 'weapon_type', 'hit')
                await caster.send(f"{c['cyan']}Damage: {c['white']}{damage} ({weapon_type}){c['reset']}")

            # Armor stats
            elif item.item_type == 'armor':
                ac = getattr(item, 'armor_class', 0)
                wear_slot = getattr(item, 'wear_slot', 'body')
                await caster.send(f"{c['cyan']}Armor:  {c['white']}{ac} AC{c['reset']}")
                await caster.send(f"{c['cyan']}Slot:   {c['white']}{wear_slot}{c['reset']}")

            # Container stats
            elif item.item_type == 'container':
                capacity = getattr(item, 'capacity', 0)
                await caster.send(f"{c['cyan']}Capacity: {c['white']}{capacity} lbs{c['reset']}")

            # Food/Drink stats
            elif item.item_type == 'food':
                food_value = getattr(item, 'food_value', 0)
                await caster.send(f"{c['cyan']}Nourishment: {c['white']}{food_value} hours{c['reset']}")
            elif item.item_type == 'drink':
                drinks = getattr(item, 'drinks', 0)
                liquid = getattr(item, 'liquid', 'water')
                await caster.send(f"{c['cyan']}Liquid:  {c['white']}{liquid}{c['reset']}")
                await caster.send(f"{c['cyan']}Servings: {c['white']}{drinks}{c['reset']}")

            # Potion/Scroll/Wand/Staff
            elif item.item_type in ['potion', 'scroll', 'wand', 'staff']:
                spells = getattr(item, 'spells', [])
                spell_level = getattr(item, 'spell_level', 1)
                await caster.send(f"{c['cyan']}Spell Level: {c['white']}{spell_level}{c['reset']}")
                if spells:
                    spell_names = ', '.join([s.replace('_', ' ').title() for s in spells])
                    await caster.send(f"{c['cyan']}Spells: {c['bright_magenta']}{spell_names}{c['reset']}")
                if item.item_type in ['wand', 'staff']:
                    charges = getattr(item, 'charges', 0)
                    await caster.send(f"{c['cyan']}Charges: {c['white']}{charges}{c['reset']}")

            # Affects/bonuses
            affects = getattr(item, 'affects', [])
            if affects:
                await caster.send(f"{c['bright_cyan']}\nMagical Properties:{c['reset']}")
                for affect in affects:
                    affect_type = affect.get('type', 'unknown')
                    value = affect.get('value', 0)
                    sign = '+' if value >= 0 else ''
                    if affect_type == 'ac':
                        await caster.send(f"  {c['green']}{sign}{value} Armor Class{c['reset']}")
                    elif affect_type == 'hitroll':
                        await caster.send(f"  {c['green']}{sign}{value} To Hit{c['reset']}")
                    elif affect_type == 'damroll':
                        await caster.send(f"  {c['green']}{sign}{value} Damage{c['reset']}")
                    elif affect_type in ['str', 'int', 'wis', 'dex', 'con', 'cha']:
                        await caster.send(f"  {c['green']}{sign}{value} {affect_type.upper()}{c['reset']}")
                    else:
                        await caster.send(f"  {c['green']}{affect_type.title()}: {sign}{value}{c['reset']}")

            await caster.send(f"{c['bright_cyan']}{'='*60}{c['reset']}")

        elif special == 'enchant_weapon':
            # Enchant a weapon to be more powerful
            if not target:
                await caster.send(f"{c['yellow']}Enchant which weapon?{c['reset']}")
                return

            item_name = str(target).lower()
            weapon = None

            # Find weapon in inventory
            for inv_item in caster.inventory:
                if item_name in inv_item.name.lower() and inv_item.item_type == 'weapon':
                    weapon = inv_item
                    break

            # Check equipped weapon
            if not weapon and 'wield' in caster.equipment:
                eq_weapon = caster.equipment['wield']
                if eq_weapon and item_name in eq_weapon.name.lower():
                    weapon = eq_weapon

            if not weapon:
                await caster.send(f"{c['yellow']}You don't have that weapon.{c['reset']}")
                return

            # Check if already enchanted
            if hasattr(weapon, 'enchanted') and weapon.enchanted:
                await caster.send(f"{c['yellow']}That weapon is already enchanted!{c['reset']}")
                return

            # Enchant the weapon (+2 hitroll, +2 damroll)
            if not hasattr(weapon, 'affects'):
                weapon.affects = []
            weapon.affects.append({'type': 'hitroll', 'value': 2})
            weapon.affects.append({'type': 'damroll', 'value': 2})
            weapon.enchanted = True

            await caster.send(f"{c['bright_blue']}Your {weapon.short_desc} glows with magical power!{c['reset']}")

        elif special == 'chain_lightning':
            # Lightning chains to multiple targets
            # For now, just hit the main target (full implementation would hit multiple)
            pass  # Damage already handled in apply_spell

        elif special == 'remove_curse':
            # Remove curse effects from target
            if hasattr(target, 'affects'):
                curse_removed = False
                for affect in target.affects[:]:
                    if 'curse' in affect.name.lower():
                        AffectManager.remove_affect(target, affect)
                        curse_removed = True
                if curse_removed:
                    await caster.send(f"{c['bright_yellow']}The curse is lifted from {target.name}!{c['reset']}")
                    if hasattr(target, 'send'):
                        await target.send(f"{c['bright_yellow']}You feel the curse lifted!{c['reset']}")
                else:
                    await caster.send(f"{c['yellow']}{target.name} is not cursed.{c['reset']}")

        elif special == 'remove_poison':
            # Remove poison effects from target
            if hasattr(target, 'affects'):
                poison_removed = False
                for affect in target.affects[:]:
                    if affect.name.lower() == 'poison':
                        AffectManager.remove_affect(target, affect)
                        poison_removed = True
                if poison_removed:
                    await caster.send(f"{c['bright_green']}You draw the poison from {target.name}!{c['reset']}")
                    if hasattr(target, 'send'):
                        await target.send(f"{c['bright_green']}The poison leaves your body!{c['reset']}")
                else:
                    await caster.send(f"{c['yellow']}{target.name} is not poisoned.{c['reset']}")

        elif special == 'create_food':
            # Create food item
            from objects import GameObject
            food = GameObject.create_from_template({
                'vnum': 9999,
                'name': 'conjured bread',
                'short_desc': 'a loaf of conjured bread',
                'description': 'A magically created loaf of bread.',
                'item_type': 'food',
                'weight': 1,
                'cost': 0,
                'food_value': 12,
            })
            caster.inventory.append(food)
            await caster.send(f"{c['bright_yellow']}You conjure a loaf of bread!{c['reset']}")

        elif special == 'create_water':
            # Create water or fill waterskin
            waterskin = None
            for item in caster.inventory:
                if item.item_type == 'drink':
                    waterskin = item
                    break

            if waterskin:
                waterskin.drinks = getattr(waterskin, 'max_drinks', 20)
                waterskin.liquid = 'water'
                await caster.send(f"{c['bright_cyan']}You fill the waterskin with fresh water!{c['reset']}")
            else:
                # Create a waterskin
                from objects import GameObject
                waterskin = GameObject.create_from_template({
                    'vnum': 9998,
                    'name': 'conjured waterskin',
                    'short_desc': 'a conjured waterskin',
                    'description': 'A magically created waterskin filled with water.',
                    'item_type': 'drink',
                    'weight': 2,
                    'cost': 0,
                    'drinks': 20,
                    'liquid': 'water',
                })
                caster.inventory.append(waterskin)
                await caster.send(f"{c['bright_cyan']}You conjure a waterskin full of water!{c['reset']}")

        elif special == 'summon_player':
            # Summon a player to your location
            if not target or not isinstance(target, str):
                await caster.send(f"{c['yellow']}Summon whom?{c['reset']}")
                return

            # Find player by name
            target_player = None
            for player in caster.world.players.values():
                if target.lower() in player.name.lower():
                    target_player = player
                    break

            if not target_player:
                await caster.send(f"{c['red']}That player is not online.{c['reset']}")
                return

            if target_player == caster:
                await caster.send(f"{c['yellow']}You can't summon yourself!{c['reset']}")
                return

            # Check if target can be summoned (no summon protection, not in combat)
            if target_player.is_fighting:
                await caster.send(f"{c['red']}{target_player.name} is fighting and cannot be summoned!{c['reset']}")
                return

            # Move player
            old_room = target_player.room
            if old_room:
                await old_room.send_to_room(
                    f"{target_player.name} disappears in a flash of light!",
                    exclude=[target_player]
                )
                old_room.characters.remove(target_player)

            target_player.room = caster.room
            caster.room.characters.append(target_player)

            await target_player.send(f"{c['bright_yellow']}You are summoned!{c['reset']}")
            await target_player.do_look([])

            await caster.room.send_to_room(
                f"{target_player.name} appears in a flash of light!",
                exclude=[target_player]
            )

        elif special == 'resurrect':
            # Resurrect a dead player (would need corpse system)
            await caster.send(f"{c['yellow']}Resurrection requires a corpse to work on.{c['reset']}")
            # Full implementation would check for player corpse objects

        elif special == 'dispel_evil':
            # Extra damage to evil-aligned targets
            if hasattr(target, 'alignment') and target.alignment < -100:
                # Extra damage already applied via damage_dice
                await caster.send(f"{c['bright_white']}Your holy power devastates the evil creature!{c['reset']}")
            else:
                await caster.send(f"{c['yellow']}{target.name} is not evil enough to be affected.{c['reset']}")

        elif special == 'earthquake':
            # Damage all enemies in the room
            enemies = []
            for char in caster.room.characters[:]:
                if char != caster:
                    if hasattr(char, 'is_player') or hasattr(char, 'flags'):
                        enemies.append(char)

            damage = cls.roll_dice('5d8') + caster.level * 2

            for enemy in enemies:
                killed = await enemy.take_damage(damage // 2, caster)  # Half damage to all enemies
                if hasattr(enemy, 'send'):
                    await enemy.send(f"{c['red']}The earthquake hits you for {damage // 2} damage!{c['reset']}")

        elif special == 'dispel_magic':
            # Remove magical effects from target
            if hasattr(target, 'affects'):
                count = AffectManager.dispel_affects(target, caster.level)
                if count > 0:
                    await caster.send(f"{c['bright_cyan']}You dispel {count} magical effect(s) from {target.name}!{c['reset']}")
                    if hasattr(target, 'send'):
                        await target.send(f"{c['cyan']}Your magical effects are stripped away!{c['reset']}")
                else:
                    await caster.send(f"{c['yellow']}{target.name} has no magical effects to dispel.{c['reset']}")

        elif special == 'death_grip':
            # Stun the target for a short time
            from affects import AffectManager
            if hasattr(target, 'affects'):
                stun_affect = {
                    'name': 'Death Grip Stun',
                    'type': AffectManager.TYPE_FLAG,
                    'applies_to': 'stunned',
                    'value': 1,
                    'duration': 2,  # 2 ticks (10 seconds)
                    'caster_level': caster.level
                }
                AffectManager.apply_affect(target, stun_affect)
                await caster.send(f"{c['bright_red']}{target.name} is stunned by your death grip!{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['red']}You are stunned!{c['reset']}")

        elif special == 'mass_charm':
            # Attempt to charm all enemies in the room
            enemies = []
            for char in caster.room.characters[:]:
                if char != caster and not hasattr(char, 'is_player'):
                    enemies.append(char)

            charmed_count = 0
            for enemy in enemies:
                # Saving throw
                save_roll = random.randint(1, 20) + (enemy.wis // 2 if hasattr(enemy, 'wis') else 0)
                if save_roll <= 10 + caster.level // 2:
                    # Charm successful
                    if hasattr(enemy, 'affects'):
                        charm_affect = {
                            'name': 'Charm',
                            'type': AffectManager.TYPE_FLAG,
                            'applies_to': 'charmed',
                            'value': 1,
                            'duration': 12,
                            'caster_level': caster.level
                        }
                        AffectManager.apply_affect(enemy, charm_affect)
                        charmed_count += 1

            if charmed_count > 0:
                await caster.send(f"{c['bright_magenta']}You charm {charmed_count} creature(s)!{c['reset']}")
            else:
                await caster.send(f"{c['yellow']}Your charm fails to affect anyone.{c['reset']}")

    @classmethod
    async def apply_spell_effect(cls, caster: 'Player', target: 'Character', spell_name: str):
        """Apply a spell effect (for potions, scrolls, etc.)."""
        spell = SPELLS.get(spell_name)
        if spell:
            await cls.apply_spell(caster, target, spell, spell_name)
            
    @staticmethod
    def roll_dice(dice_str: str) -> int:
        """Roll dice from a string like '2d6+4'."""
        try:
            if '+' in dice_str:
                dice_part, bonus = dice_str.split('+')
                bonus = int(bonus)
            elif '-' in dice_str:
                dice_part, penalty = dice_str.split('-')
                bonus = -int(penalty)
            else:
                dice_part = dice_str
                bonus = 0
                
            num_dice, die_size = dice_part.split('d')
            num_dice = int(num_dice)
            die_size = int(die_size)
            
            total = sum(random.randint(1, die_size) for _ in range(num_dice))
            return max(1, total + bonus)
            
        except Exception:
            return random.randint(1, 8)
