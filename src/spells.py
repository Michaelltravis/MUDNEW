"""
RealmsMUD Spells
================
Magic system and spell effects.
"""

import random
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Player, Character

from config import Config
from affects import AffectManager

logger = logging.getLogger('RealmsMUD.Spells')

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
        'duration_ticks': 24,
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
        'duration_ticks': 24,
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
        'damage_dice': '10d8+20',
        'damage_per_level': 5,
        'target': 'offensive',
        'save': True,
        'message_self': 'You point your finger at $N, invoking instant death!',
        'message_room': '$n points at $N with deadly intent!',
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
            
        # Check mana
        mana_cost = spell.get('mana_cost', 10)
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
        if target is None and spell['target'] not in ('self', 'special', 'object'):
            await caster.send("Cast the spell on whom?")
            return
            
        # Deduct mana
        caster.mana -= mana_cost

        # Apply spell effect
        await cls.apply_spell(caster, target, spell, spell_name)

        # Attempt to improve spell proficiency through successful casting
        if hasattr(caster, 'improve_spell'):
            await caster.improve_spell(spell_name)
        
    @classmethod
    async def get_target(cls, caster: 'Player', spell: dict, target_name: Optional[str]) -> Optional['Character']:
        """Get the target for a spell."""
        target_type = spell.get('target', 'offensive')

        if target_type == 'self':
            return caster

        if target_type == 'object':
            # For object-target spells (like identify), return the item name
            # The actual item will be found in handle_special_spell
            return target_name if target_name else None

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
        
        # Send cast messages
        if target == caster:
            if spell.get('message_self'):
                await caster.send(f"{c['bright_magenta']}{spell['message_self']}{c['reset']}")
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
            damage = cls.roll_dice(spell['damage_dice'])
            damage += spell.get('damage_per_level', 0) * caster.level

            # Apply weather modifier to damage
            if caster.room and caster.room.zone and hasattr(caster.room.zone, 'weather'):
                weather_mult = caster.room.zone.weather.get_spell_modifier(spell['name'])
                damage = int(damage * weather_mult)

            # Apply spell damage
            killed = await target.take_damage(damage, caster)
            
            await caster.send(f"{c['bright_red']}Your spell does {damage} damage to {target.name}!{c['reset']}")
            
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
                
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + heal)
            actual_heal = target.hp - old_hp
            
            if target == caster:
                await caster.send(f"{c['bright_green']}You heal {actual_heal} hit points!{c['reset']}")
            else:
                await caster.send(f"{c['bright_green']}You heal {target.name} for {actual_heal} hit points!{c['reset']}")
                if hasattr(target, 'send'):
                    await target.send(f"{c['bright_green']}{caster.name} heals you for {actual_heal} hit points!{c['reset']}")
                    
        # Apply buff/debuff affects
        if 'affects' in spell:
            duration = spell.get('duration_ticks', 24)
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
                     'detect_evil', 'charmed', 'entangled', 'sleeping', 'stunned'}

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
        elif affect_type in flag_types:
            affect_data['type'] = AffectManager.TYPE_FLAG
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
        c = cls.config.COLORS
        special = spell.get('special')
        
        if special == 'recall':
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
                if target and hasattr(target, 'name') and dir_name in str(target).lower():
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
                if target and hasattr(target, 'name') and dir_name in str(target).lower():
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
                if char != caster and char not in [caster.fighting] if hasattr(caster, 'fighting') else True:
                    if hasattr(char, 'is_player') or hasattr(char, 'flags'):
                        enemies.append(char)

            damage = cls.roll_dice('5d8') + caster.level * 2

            for enemy in enemies:
                killed = await enemy.take_damage(damage // 2, caster)  # Half damage to others
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
