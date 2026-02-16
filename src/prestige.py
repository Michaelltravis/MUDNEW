"""
RealmsMUD Prestige Class System
===============================
At level 50, players can specialize into an advanced prestige class.
Each base class has two prestige options with 3 unique abilities each.
Prestige classes can reach level 60 (non-prestige caps at 50).
"""

import time
import random
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger('RealmsMUD.Prestige')

RESPEC_COST = 50000  # 50K gold

# ─────────────────────────────────────────────────────────────────────
# Prestige Class Definitions
# ─────────────────────────────────────────────────────────────────────

PRESTIGE_CLASSES = {
    # ── Warrior ──
    'champion': {
        'name': 'Champion',
        'base_class': 'warrior',
        'theme': 'offense',
        'description': 'A master of devastating offense, the Champion channels fury into overwhelming strikes that shatter armor and crush opposition.',
        'abilities': {
            'titans_fury': {
                'name': "Titan's Fury",
                'description': 'Unleash a massive overhead strike dealing 250% weapon damage. If target is below 40% HP, deals 350% instead.',
                'cooldown': 45,
                'mana_cost': 0,
                'type': 'attack',
            },
            'warpath': {
                'name': 'Warpath',
                'description': 'Enter a warpath for 20 seconds. All attacks deal +25% damage and have +10% crit chance.',
                'cooldown': 120,
                'mana_cost': 0,
                'type': 'buff',
            },
            'earthquake_slam': {
                'name': 'Earthquake Slam',
                'description': 'Slam the ground, dealing 150% weapon damage to all enemies in the room and stunning them for 1 round.',
                'cooldown': 90,
                'mana_cost': 0,
                'type': 'aoe',
            },
        },
    },
    'vanguard': {
        'name': 'Vanguard',
        'base_class': 'warrior',
        'theme': 'defense',
        'description': 'An immovable bulwark, the Vanguard absorbs punishment that would fell lesser warriors and protects allies with unbreakable resolve.',
        'abilities': {
            'iron_bastion': {
                'name': 'Iron Bastion',
                'description': 'Raise an impenetrable defense for 15 seconds. Take 50% reduced damage and reflect 20% back to attackers.',
                'cooldown': 120,
                'mana_cost': 0,
                'type': 'buff',
            },
            'guardian_wall': {
                'name': 'Guardian Wall',
                'description': 'Intercept all attacks aimed at group members for 10 seconds. You take 30% reduced damage during this.',
                'cooldown': 90,
                'mana_cost': 0,
                'type': 'buff',
            },
            'unbreakable': {
                'name': 'Unbreakable',
                'description': 'For 8 seconds, you cannot drop below 1 HP. Afterward, heal 25% of max HP.',
                'cooldown': 180,
                'mana_cost': 0,
                'type': 'buff',
            },
        },
    },

    # ── Assassin ──
    'shadowblade': {
        'name': 'Shadowblade',
        'base_class': 'assassin',
        'theme': 'burst damage',
        'description': 'The Shadowblade strikes with lethal precision, delivering devastating burst damage from the shadows that can eliminate targets before they react.',
        'abilities': {
            'death_blossom': {
                'name': 'Death Blossom',
                'description': 'A flurry of 5 rapid strikes, each dealing 80% weapon damage. Crits grant an additional strike (max 8 total).',
                'cooldown': 60,
                'mana_cost': 0,
                'type': 'attack',
            },
            'umbral_strike': {
                'name': 'Umbral Strike',
                'description': 'Teleport behind target and strike for 300% weapon damage. If used from stealth, ignore all armor.',
                'cooldown': 45,
                'mana_cost': 0,
                'type': 'attack',
            },
            'shadow_execution': {
                'name': 'Shadow Execution',
                'description': 'Mark target for death. After 3 rounds, deal damage equal to 40% of HP they lost during the mark period.',
                'cooldown': 120,
                'mana_cost': 0,
                'type': 'debuff',
            },
        },
    },
    'phantom': {
        'name': 'Phantom',
        'base_class': 'assassin',
        'theme': 'stealth/utility',
        'description': 'The Phantom exists between worlds, a ghost that strikes from nowhere and vanishes without a trace, controlling the battlefield through fear and misdirection.',
        'abilities': {
            'veil_of_shadows': {
                'name': 'Veil of Shadows',
                'description': 'Become invisible for 30 seconds. First attack from veil deals 200% damage and applies a 5-second silence.',
                'cooldown': 90,
                'mana_cost': 0,
                'type': 'buff',
            },
            'phantom_step': {
                'name': 'Phantom Step',
                'description': 'Dodge the next 3 attacks completely. Each dodge creates a shadow clone that strikes for 50% weapon damage.',
                'cooldown': 60,
                'mana_cost': 0,
                'type': 'buff',
            },
            'terror': {
                'name': 'Terror',
                'description': 'Emit an aura of dread. All enemies lose 20% hit chance and deal 15% less damage for 20 seconds.',
                'cooldown': 120,
                'mana_cost': 0,
                'type': 'debuff',
            },
        },
    },

    # ── Mage ──
    'archmage': {
        'name': 'Archmage',
        'base_class': 'mage',
        'theme': 'raw power',
        'description': 'The Archmage has transcended ordinary magic, wielding arcane forces of terrifying magnitude that reshape reality itself.',
        'abilities': {
            'arcane_annihilation': {
                'name': 'Arcane Annihilation',
                'description': 'Channel pure arcane energy for 400% spell damage. Consumes all arcane charges for +20% damage per charge.',
                'cooldown': 60,
                'mana_cost': 80,
                'type': 'attack',
            },
            'temporal_shift': {
                'name': 'Temporal Shift',
                'description': 'Bend time: reset all spell cooldowns and gain 50% mana back. For 10 seconds, spells cost no mana.',
                'cooldown': 180,
                'mana_cost': 0,
                'type': 'buff',
            },
            'meteor_cataclysm': {
                'name': 'Meteor Cataclysm',
                'description': 'Rain meteors on all enemies for 300% spell damage. Leaves burning ground dealing 5% spell damage per tick for 4 ticks.',
                'cooldown': 120,
                'mana_cost': 120,
                'type': 'aoe',
            },
        },
    },
    'battlemage': {
        'name': 'Battlemage',
        'base_class': 'mage',
        'theme': 'hybrid melee/magic',
        'description': 'The Battlemage weaves spell and steel together, an armored caster who fights on the front lines with magic-enhanced weapons.',
        'abilities': {
            'spellblade': {
                'name': 'Spellblade',
                'description': 'Enchant your weapon for 30 seconds. Melee attacks deal bonus magic damage equal to 50% of your INT and restore 3% mana per hit.',
                'cooldown': 60,
                'mana_cost': 40,
                'type': 'buff',
            },
            'arcane_barrier': {
                'name': 'Arcane Barrier',
                'description': 'Create a barrier absorbing damage equal to 40% of your max mana. While active, melee attacks deal 30% bonus magic damage.',
                'cooldown': 90,
                'mana_cost': 60,
                'type': 'buff',
            },
            'elemental_surge': {
                'name': 'Elemental Surge',
                'description': 'Strike with fire, frost, and lightning simultaneously for 250% combined damage. Each element applies its debuff (burn, slow, stun 1 round).',
                'cooldown': 75,
                'mana_cost': 70,
                'type': 'attack',
            },
        },
    },

    # ── Cleric ──
    'high_priest': {
        'name': 'High Priest',
        'base_class': 'cleric',
        'theme': 'healing master',
        'description': 'The High Priest channels divine radiance with unmatched purity, their healing miracles capable of restoring life from the very brink of death.',
        'abilities': {
            'divine_resurrection': {
                'name': 'Divine Resurrection',
                'description': 'Resurrect a fallen group member at 50% HP/mana, or fully heal a living ally and remove all debuffs.',
                'cooldown': 180,
                'mana_cost': 100,
                'type': 'heal',
            },
            'sanctuary_of_light': {
                'name': 'Sanctuary of Light',
                'description': 'Create a holy zone for 20 seconds. All group members regenerate 8% max HP per tick and take 20% less damage.',
                'cooldown': 120,
                'mana_cost': 80,
                'type': 'buff',
            },
            'grace_of_the_divine': {
                'name': 'Grace of the Divine',
                'description': 'For 15 seconds, all your heals are doubled and cost 50% less mana. Overhealing creates a damage shield.',
                'cooldown': 150,
                'mana_cost': 60,
                'type': 'buff',
            },
        },
    },
    'inquisitor': {
        'name': 'Inquisitor',
        'base_class': 'cleric',
        'theme': 'damage/debuff',
        'description': 'The Inquisitor wields divine wrath as a weapon, punishing the wicked with holy fire and curses that weaken body and soul.',
        'abilities': {
            'judgment_of_light': {
                'name': 'Judgment of Light',
                'description': 'Pass divine judgment dealing 250% holy damage. Target takes 25% more damage from all sources for 15 seconds.',
                'cooldown': 60,
                'mana_cost': 50,
                'type': 'attack',
            },
            'chains_of_penance': {
                'name': 'Chains of Penance',
                'description': 'Bind target in holy chains for 3 rounds. They cannot move or attack, and take 50% holy damage per round.',
                'cooldown': 90,
                'mana_cost': 60,
                'type': 'debuff',
            },
            'holy_inquisition': {
                'name': 'Holy Inquisition',
                'description': 'For 20 seconds, your damaging spells heal you for 30% of damage dealt and reduce target healing received by 50%.',
                'cooldown': 120,
                'mana_cost': 70,
                'type': 'buff',
            },
        },
    },

    # ── Ranger ──
    'warden': {
        'name': 'Warden',
        'base_class': 'ranger',
        'theme': 'nature magic',
        'description': 'The Warden has bonded deeply with the natural world, commanding the elements and beasts with primal authority.',
        'abilities': {
            'natures_wrath': {
                'name': "Nature's Wrath",
                'description': 'Call lightning and thorns on all enemies: 200% nature damage plus a root for 2 rounds.',
                'cooldown': 75,
                'mana_cost': 50,
                'type': 'aoe',
            },
            'primal_bond': {
                'name': 'Primal Bond',
                'description': 'Your animal companion gains +50% damage and HP for 30 seconds. You heal 5% HP when your companion hits.',
                'cooldown': 90,
                'mana_cost': 30,
                'type': 'buff',
            },
            'overgrowth': {
                'name': 'Overgrowth',
                'description': 'Surround yourself in living vines. Absorb damage equal to 30% max HP, and enemies that strike you are slowed 30% for 3 rounds.',
                'cooldown': 120,
                'mana_cost': 40,
                'type': 'buff',
            },
        },
    },
    'sharpshooter': {
        'name': 'Sharpshooter',
        'base_class': 'ranger',
        'theme': 'ranged DPS',
        'description': 'The Sharpshooter has perfected the art of ranged combat, delivering devastating precision shots that strike with surgical accuracy.',
        'abilities': {
            'killshot': {
                'name': 'Killshot',
                'description': 'A perfect aimed shot dealing 350% weapon damage. If target is below 30% HP, guaranteed critical hit.',
                'cooldown': 45,
                'mana_cost': 0,
                'type': 'attack',
            },
            'volley_of_arrows': {
                'name': 'Volley of Arrows',
                'description': 'Fire a rain of arrows hitting all enemies for 150% weapon damage each. Each arrow has a 20% chance to apply a bleed.',
                'cooldown': 60,
                'mana_cost': 0,
                'type': 'aoe',
            },
            'eagle_eye': {
                'name': 'Eagle Eye',
                'description': 'Enter a focused state for 20 seconds. +30% ranged damage, +15% crit chance, and attacks cannot miss.',
                'cooldown': 120,
                'mana_cost': 0,
                'type': 'buff',
            },
        },
    },

    # ── Paladin ──
    'crusader': {
        'name': 'Crusader',
        'base_class': 'paladin',
        'theme': 'offensive holy',
        'description': 'The Crusader is a holy avenger, smiting evil with blinding radiance and righteous fury that grows stronger with every blow landed.',
        'abilities': {
            'radiant_judgment': {
                'name': 'Radiant Judgment',
                'description': 'Smite target with holy fire for 300% holy damage. Undead and demons take 450% instead.',
                'cooldown': 45,
                'mana_cost': 40,
                'type': 'attack',
            },
            'zealots_fury': {
                'name': "Zealot's Fury",
                'description': 'Enter a righteous frenzy for 20 seconds. +30% holy damage, attacks build holy power 2x faster.',
                'cooldown': 120,
                'mana_cost': 30,
                'type': 'buff',
            },
            'divine_reckoning': {
                'name': 'Divine Reckoning',
                'description': 'Spend all Holy Power (min 3) for a devastating strike: 100% holy damage per point spent, healing you for 50% of damage dealt.',
                'cooldown': 60,
                'mana_cost': 50,
                'type': 'attack',
            },
        },
    },
    'templar': {
        'name': 'Templar',
        'base_class': 'paladin',
        'theme': 'defensive auras',
        'description': 'The Templar radiates divine protection, their auras shielding allies from harm and their faith turning aside the mightiest blows.',
        'abilities': {
            'aura_of_invincibility': {
                'name': 'Aura of Invincibility',
                'description': 'All group members take 30% less damage for 15 seconds. You take an additional 15% less.',
                'cooldown': 120,
                'mana_cost': 60,
                'type': 'buff',
            },
            'holy_aegis': {
                'name': 'Holy Aegis',
                'description': 'Shield target for 25% of your max HP. Shield explodes when broken, healing nearby allies for the remaining amount.',
                'cooldown': 45,
                'mana_cost': 40,
                'type': 'heal',
            },
            'martyrdom': {
                'name': 'Martyrdom',
                'description': 'Absorb all damage dealt to group members for 8 seconds. You take 40% reduced damage during this. Cannot die during martyrdom.',
                'cooldown': 180,
                'mana_cost': 80,
                'type': 'buff',
            },
        },
    },

    # ── Necromancer ──
    'lich': {
        'name': 'Lich',
        'base_class': 'necromancer',
        'theme': 'self-power',
        'description': 'The Lich has bound their soul to dark phylacteries, transcending mortal limits to wield death magic of terrifying potency.',
        'abilities': {
            'soul_cage': {
                'name': 'Soul Cage',
                'description': 'Store your soul in a phylactery. If you die within 60 seconds, resurrect at 40% HP and gain 5 soul shards.',
                'cooldown': 300,
                'mana_cost': 50,
                'type': 'buff',
            },
            'necrotic_nova': {
                'name': 'Necrotic Nova',
                'description': 'Explode necrotic energy outward: 250% shadow damage to all enemies. Heals you for 30% of total damage dealt.',
                'cooldown': 75,
                'mana_cost': 70,
                'type': 'aoe',
            },
            'dark_ascension': {
                'name': 'Dark Ascension',
                'description': 'Transform into a lich form for 25 seconds. +40% spell damage, immune to fear/stun, and all kills generate 2 soul shards.',
                'cooldown': 180,
                'mana_cost': 80,
                'type': 'buff',
            },
        },
    },
    'reaper': {
        'name': 'Reaper',
        'base_class': 'necromancer',
        'theme': 'summons',
        'description': 'The Reaper commands an army of the dead, raising ever more powerful minions and empowering them with dark rituals.',
        'abilities': {
            'army_of_the_dead': {
                'name': 'Army of the Dead',
                'description': 'Raise 3 skeletal warriors for 30 seconds. Each fights independently, dealing 60% of your spell damage per round.',
                'cooldown': 120,
                'mana_cost': 80,
                'type': 'summon',
            },
            'soul_link': {
                'name': 'Soul Link',
                'description': 'Link your minions\' souls to yours. 30% of damage you take is split among minions. Minions heal you 10% when they deal damage.',
                'cooldown': 90,
                'mana_cost': 40,
                'type': 'buff',
            },
            'harbinger_of_doom': {
                'name': 'Harbinger of Doom',
                'description': 'Sacrifice a minion to deal 400% shadow damage to target and reduce their healing by 75% for 10 seconds.',
                'cooldown': 60,
                'mana_cost': 50,
                'type': 'attack',
            },
        },
    },

    # ── Thief ──
    'mastermind': {
        'name': 'Mastermind',
        'base_class': 'thief',
        'theme': 'control',
        'description': 'The Mastermind plays the long game, manipulating enemies like chess pieces and turning every situation to their advantage.',
        'abilities': {
            'grand_scheme': {
                'name': 'Grand Scheme',
                'description': 'For 20 seconds, every successful hit reveals an opening: next ability cooldown reduced by 3 seconds. Luck generation doubled.',
                'cooldown': 90,
                'mana_cost': 0,
                'type': 'buff',
            },
            'puppeteer': {
                'name': 'Puppeteer',
                'description': 'Confuse target for 3 rounds. They attack random targets (including allies) and cannot use abilities.',
                'cooldown': 75,
                'mana_cost': 0,
                'type': 'debuff',
            },
            'ace_in_the_hole': {
                'name': 'Ace in the Hole',
                'description': 'Consume all Luck points. Deal 30% weapon damage per Luck point consumed (300% at max). Guaranteed crit if 8+ Luck consumed.',
                'cooldown': 60,
                'mana_cost': 0,
                'type': 'attack',
            },
        },
    },
    'swashbuckler': {
        'name': 'Swashbuckler',
        'base_class': 'thief',
        'theme': 'combat',
        'description': 'The Swashbuckler is a dashing duelist, combining speed, style, and deadly precision into an unstoppable whirlwind of blades.',
        'abilities': {
            'blade_storm': {
                'name': 'Blade Storm',
                'description': 'Whirl your blades hitting all enemies for 180% weapon damage. Each enemy hit grants +1 combo point.',
                'cooldown': 45,
                'mana_cost': 0,
                'type': 'aoe',
            },
            'riposte_mastery': {
                'name': 'Riposte Mastery',
                'description': 'For 15 seconds, automatically counter every incoming attack for 100% weapon damage. +25% dodge chance.',
                'cooldown': 90,
                'mana_cost': 0,
                'type': 'buff',
            },
            'coup_de_grace': {
                'name': 'Coup de Grace',
                'description': 'A devastating finishing blow consuming all combo points. Deals 80% weapon damage per point (400% at 5). Target bleeds for 50% over 4 rounds.',
                'cooldown': 45,
                'mana_cost': 0,
                'type': 'attack',
            },
        },
    },

    # ── Bard ──
    'virtuoso': {
        'name': 'Virtuoso',
        'base_class': 'bard',
        'theme': 'songs',
        'description': 'The Virtuoso has mastered every form of music, their performances so powerful they reshape reality and move the very gods to action.',
        'abilities': {
            'symphony_of_war': {
                'name': 'Symphony of War',
                'description': 'Perform an epic symphony for 25 seconds. Group gains +20% damage, +15% crit chance, and 5% HP regen per tick.',
                'cooldown': 120,
                'mana_cost': 60,
                'type': 'buff',
            },
            'requiem_of_sorrow': {
                'name': 'Requiem of Sorrow',
                'description': 'Play a mournful dirge. All enemies take 150% sonic damage and are slowed 40% for 4 rounds. Undead are feared.',
                'cooldown': 75,
                'mana_cost': 50,
                'type': 'aoe',
            },
            'standing_ovation': {
                'name': 'Standing Ovation',
                'description': 'End your current song with a masterful finale. Heal all group members for 30% max HP and grant 10 seconds of +30% all stats.',
                'cooldown': 150,
                'mana_cost': 80,
                'type': 'heal',
            },
        },
    },
    'war_chanter': {
        'name': 'War Chanter',
        'base_class': 'bard',
        'theme': 'combat buffs',
        'description': 'The War Chanter drives allies to impossible feats of valor, their battle hymns turning ordinary warriors into legends.',
        'abilities': {
            'battle_anthem': {
                'name': 'Battle Anthem',
                'description': 'Chant a battle anthem for 20 seconds. Group attacks have +20% chance to strike twice. Your own attacks deal +30% damage.',
                'cooldown': 90,
                'mana_cost': 50,
                'type': 'buff',
            },
            'war_drums': {
                'name': 'War Drums',
                'description': 'Beat war drums that energize the group. Restore 20% max mana/move to all group members and grant immunity to fear for 15 seconds.',
                'cooldown': 120,
                'mana_cost': 40,
                'type': 'buff',
            },
            'heroic_ballad': {
                'name': 'Heroic Ballad',
                'description': 'Sing of the group\'s heroic deeds. For 15 seconds, all group members that drop below 20% HP are instantly healed to 40% HP (once each).',
                'cooldown': 150,
                'mana_cost': 70,
                'type': 'buff',
            },
        },
    },
}

# Map base class -> list of prestige class keys
BASE_CLASS_PRESTIGES = {}
for key, data in PRESTIGE_CLASSES.items():
    base = data['base_class']
    if base not in BASE_CLASS_PRESTIGES:
        BASE_CLASS_PRESTIGES[base] = []
    BASE_CLASS_PRESTIGES[base].append(key)


def get_prestige_display_name(player) -> str:
    """Get the prestige class display name, or empty string if none."""
    prestige = getattr(player, 'prestige_class', None)
    if prestige and prestige in PRESTIGE_CLASSES:
        return PRESTIGE_CLASSES[prestige]['name']
    return ''


def get_class_display(player) -> str:
    """Get class name with prestige indicator for display (who list, score)."""
    from config import Config
    base_name = Config.CLASSES.get(player.char_class, {}).get('name', player.char_class)
    prestige = getattr(player, 'prestige_class', None)
    if prestige and prestige in PRESTIGE_CLASSES:
        return PRESTIGE_CLASSES[prestige]['name']
    return base_name


def get_max_level(player) -> int:
    """Return max mortal level: 60 for prestige, 50 for non-prestige."""
    if getattr(player, 'prestige_class', None):
        return 60
    return 50


def has_prestige_ability(player, ability_key: str) -> bool:
    """Check if player has a specific prestige ability."""
    prestige = getattr(player, 'prestige_class', None)
    if not prestige or prestige not in PRESTIGE_CLASSES:
        return False
    return ability_key in PRESTIGE_CLASSES[prestige]['abilities']


def get_prestige_abilities(player) -> dict:
    """Get dict of prestige abilities for this player."""
    prestige = getattr(player, 'prestige_class', None)
    if not prestige or prestige not in PRESTIGE_CLASSES:
        return {}
    return PRESTIGE_CLASSES[prestige]['abilities']


# ─────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────

async def cmd_specialize(player, args):
    """Choose your prestige class specialization at level 50."""
    from config import Config
    c = Config.COLORS

    prestige = getattr(player, 'prestige_class', None)
    if prestige:
        pname = PRESTIGE_CLASSES[prestige]['name']
        await player.send(f"{c['yellow']}You are already specialized as a {c['bright_yellow']}{pname}{c['yellow']}. Use 'respec' to reset (costs {RESPEC_COST:,} gold).{c['reset']}")
        return

    if player.level < 50:
        await player.send(f"{c['red']}You must be at least level 50 to specialize. You are level {player.level}.{c['reset']}")
        return

    base = player.char_class.lower()
    options = BASE_CLASS_PRESTIGES.get(base, [])
    if not options:
        await player.send(f"{c['red']}No prestige classes available for your class.{c['reset']}")
        return

    if not args:
        # Show options
        base_name = Config.CLASSES.get(base, {}).get('name', base)
        await player.send(f"\n{c['bright_cyan']}═══ Prestige Specializations for {base_name} ═══{c['reset']}\n")
        for key in options:
            pdata = PRESTIGE_CLASSES[key]
            await player.send(f"  {c['bright_yellow']}{pdata['name']}{c['white']} — {pdata['theme'].title()}{c['reset']}")
            await player.send(f"  {c['cyan']}{pdata['description']}{c['reset']}")
            await player.send(f"  {c['white']}Abilities:{c['reset']}")
            for akey, adata in pdata['abilities'].items():
                await player.send(f"    {c['bright_green']}{adata['name']}{c['white']}: {adata['description']}{c['reset']}")
            await player.send("")
        await player.send(f"{c['yellow']}Usage: specialize <class name>{c['reset']}")
        await player.send(f"{c['red']}WARNING: This is a permanent choice (respec costs {RESPEC_COST:,} gold)!{c['reset']}")
        return

    # Match choice
    choice = '_'.join(args).lower().replace(' ', '_')
    # Also try matching by name
    matched = None
    for key in options:
        if key == choice or PRESTIGE_CLASSES[key]['name'].lower() == choice.replace('_', ' '):
            matched = key
            break

    if not matched:
        names = ', '.join(PRESTIGE_CLASSES[k]['name'] for k in options)
        await player.send(f"{c['red']}Invalid choice. Options: {names}{c['reset']}")
        return

    # Confirm
    if not getattr(player, '_specialize_confirm', None) == matched:
        player._specialize_confirm = matched
        pname = PRESTIGE_CLASSES[matched]['name']
        await player.send(f"{c['bright_yellow']}You are about to specialize as a {c['bright_white']}{pname}{c['bright_yellow']}!{c['reset']}")
        await player.send(f"{c['yellow']}Type 'specialize {' '.join(args)}' again to confirm.{c['reset']}")
        return

    # Apply specialization
    player._specialize_confirm = None
    player.prestige_class = matched
    player.prestige_cooldowns = {}
    pdata = PRESTIGE_CLASSES[matched]
    pname = pdata['name']

    await player.send(f"\n{c['bright_yellow']}{'*' * 60}{c['reset']}")
    await player.send(f"{c['bright_yellow']}  You have become a {c['bright_white']}{pname}{c['bright_yellow']}!{c['reset']}")
    await player.send(f"{c['bright_yellow']}{'*' * 60}{c['reset']}")
    await player.send(f"{c['cyan']}{pdata['description']}{c['reset']}\n")
    await player.send(f"{c['bright_green']}New abilities unlocked:{c['reset']}")
    for akey, adata in pdata['abilities'].items():
        await player.send(f"  {c['bright_yellow']}{adata['name']}{c['white']}: {adata['description']}{c['reset']}")
    await player.send(f"\n{c['bright_green']}Your level cap has been raised to 60!{c['reset']}")

    # Announce to room
    if player.room:
        await player.room.send_to_room(
            f"{c['bright_yellow']}{player.name} has specialized as a {pname}!{c['reset']}",
            exclude=[player]
        )

    await player.save()


async def cmd_respec(player, args):
    """Reset your prestige specialization for gold."""
    from config import Config
    c = Config.COLORS

    prestige = getattr(player, 'prestige_class', None)
    if not prestige:
        await player.send(f"{c['yellow']}You don't have a prestige specialization to reset.{c['reset']}")
        return

    pname = PRESTIGE_CLASSES.get(prestige, {}).get('name', prestige)

    if player.gold < RESPEC_COST:
        await player.send(f"{c['red']}Respecialization costs {RESPEC_COST:,} gold. You only have {player.gold:,}.{c['reset']}")
        return

    # Stop combat
    if player.fighting:
        await player.send(f"{c['red']}You can't respec while fighting!{c['reset']}")
        return

    # Confirm
    if not getattr(player, '_respec_confirm', False):
        player._respec_confirm = True
        await player.send(f"{c['bright_yellow']}Reset your {pname} specialization for {RESPEC_COST:,} gold?{c['reset']}")
        await player.send(f"{c['yellow']}Type 'respec' again to confirm. You will lose all prestige abilities.{c['reset']}")
        return

    player._respec_confirm = False
    player.gold -= RESPEC_COST
    old_prestige = player.prestige_class
    player.prestige_class = None
    player.prestige_cooldowns = {}

    await player.send(f"{c['bright_yellow']}Your {pname} specialization has been reset.{c['reset']}")
    await player.send(f"{c['yellow']}{RESPEC_COST:,} gold deducted. You may now choose a new specialization with 'specialize'.{c['reset']}")

    # If over level 50, cap at 50
    if player.level > 50:
        await player.send(f"{c['red']}Your level has been reduced from {player.level} to 50 (non-prestige cap).{c['reset']}")
        player.level = 50

    await player.save()


async def cmd_prestige(player, args):
    """View your prestige class info and abilities."""
    from config import Config
    c = Config.COLORS

    prestige = getattr(player, 'prestige_class', None)
    if not prestige:
        if player.level >= 50:
            await player.send(f"{c['yellow']}You haven't specialized yet. Type 'specialize' to view options.{c['reset']}")
        else:
            await player.send(f"{c['yellow']}Prestige classes unlock at level 50. You are level {player.level}.{c['reset']}")
        return

    pdata = PRESTIGE_CLASSES[prestige]
    await player.send(f"\n{c['bright_cyan']}═══ {pdata['name']} ═══{c['reset']}")
    await player.send(f"{c['cyan']}{pdata['description']}{c['reset']}\n")
    await player.send(f"{c['white']}Theme: {pdata['theme'].title()}{c['reset']}")
    await player.send(f"{c['white']}Base Class: {Config.CLASSES.get(pdata['base_class'], {}).get('name', pdata['base_class'])}{c['reset']}\n")
    await player.send(f"{c['bright_green']}Abilities:{c['reset']}")

    now = time.time()
    cooldowns = getattr(player, 'prestige_cooldowns', {})
    for akey, adata in pdata['abilities'].items():
        cd_remaining = max(0, cooldowns.get(akey, 0) - now)
        cd_str = f" {c['red']}[CD: {int(cd_remaining)}s]{c['reset']}" if cd_remaining > 0 else f" {c['green']}[Ready]{c['reset']}"
        mana_str = f" (Mana: {adata['mana_cost']})" if adata.get('mana_cost') else ""
        await player.send(f"  {c['bright_yellow']}{adata['name']}{c['white']}: {adata['description']}{mana_str}{cd_str}{c['reset']}")


# ─────────────────────────────────────────────────────────────────────
# Help entries for help_data
# ─────────────────────────────────────────────────────────────────────

PRESTIGE_HELP_ENTRIES = {
    'prestige': {
        'category': 'system',
        'title': 'Prestige Classes',
        'syntax': 'specialize | respec | prestige',
        'description': (
            'At level 50, players can choose a prestige specialization — an advanced\n'
            'version of their base class. Each class has two options:\n\n'
            '  Warrior   → Champion (offense) or Vanguard (defense)\n'
            '  Assassin  → Shadowblade (burst) or Phantom (stealth/utility)\n'
            '  Mage      → Archmage (raw power) or Battlemage (hybrid melee/magic)\n'
            '  Cleric    → High Priest (healing) or Inquisitor (damage/debuff)\n'
            '  Ranger    → Warden (nature magic) or Sharpshooter (ranged DPS)\n'
            '  Paladin   → Crusader (offensive holy) or Templar (defensive auras)\n'
            '  Necromancer → Lich (self-power) or Reaper (summons)\n'
            '  Thief     → Mastermind (control) or Swashbuckler (combat)\n'
            '  Bard      → Virtuoso (songs) or War Chanter (combat buffs)\n\n'
            'BENEFITS:\n'
            '  - Level cap raised from 50 to 60\n'
            '  - 3 unique powerful abilities per specialization\n'
            '  - Prestige title shown in who list and score\n\n'
            'COMMANDS:\n'
            '  specialize          — View available prestige classes\n'
            '  specialize <class>  — Choose your specialization (permanent)\n'
            '  respec              — Reset specialization (costs 50,000 gold)\n'
            '  prestige            — View your prestige abilities and cooldowns\n\n'
            'This is a MEANINGFUL choice — choose carefully!'
        ),
    },
    'specialize': {
        'category': 'command',
        'title': 'Specialize',
        'syntax': 'specialize [class name]',
        'description': (
            'Choose your prestige class at level 50.\n\n'
            'Type "specialize" alone to see your options.\n'
            'Type "specialize <name>" to choose (requires confirmation).\n\n'
            'See "help prestige" for the full list of prestige classes.'
        ),
    },
    'respec': {
        'category': 'command',
        'title': 'Respec',
        'syntax': 'respec',
        'description': (
            'Reset your prestige specialization.\n\n'
            'Costs 50,000 gold. You lose all prestige abilities.\n'
            'If you are above level 50, your level is reduced to 50.\n'
            'You can then choose a new specialization with "specialize".'
        ),
    },
}

# Generate help entries for each prestige class
for _key, _pdata in PRESTIGE_CLASSES.items():
    _abilities_text = '\n'.join(
        f"  {a['name']}: {a['description']}"
        for a in _pdata['abilities'].values()
    )
    PRESTIGE_HELP_ENTRIES[_key] = {
        'category': 'prestige',
        'title': _pdata['name'],
        'description': (
            f"{_pdata['description']}\n\n"
            f"Base Class: {_pdata['base_class'].title()}\n"
            f"Theme: {_pdata['theme'].title()}\n\n"
            f"ABILITIES:\n{_abilities_text}"
        ),
    }
    # Also add by display name (lowercase)
    _name_key = _pdata['name'].lower().replace(' ', '_')
    if _name_key != _key:
        PRESTIGE_HELP_ENTRIES[_name_key] = PRESTIGE_HELP_ENTRIES[_key]
