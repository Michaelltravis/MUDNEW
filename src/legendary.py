"""
RealmsMUD Legendary Item System
================================
Item rarity tiers, procs/effects, legendary items, drop system, and announcements.
"""

import random
import time
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player, Character
    from objects import Object

from config import Config

logger = logging.getLogger('RealmsMUD.Legendary')

# ═══════════════════════════════════════════════════════════════
# RARITY SYSTEM
# ═══════════════════════════════════════════════════════════════

RARITY_TIERS = {
    'common':    {'color_code': 'white',          'label': 'Common',    'order': 0},
    'uncommon':  {'color_code': 'green',          'label': 'Uncommon',  'order': 1},
    'rare':      {'color_code': 'bright_cyan',    'label': 'Rare',      'order': 2},
    'epic':      {'color_code': 'bright_magenta', 'label': 'Epic',      'order': 3},
    'legendary': {'color_code': 'bright_yellow',  'label': 'Legendary', 'order': 4},
}

def get_rarity_color(item) -> str:
    """Get the ANSI color key for an item's rarity."""
    rarity = getattr(item, 'rarity', 'common') or 'common'
    tier = RARITY_TIERS.get(rarity, RARITY_TIERS['common'])
    return tier['color_code']

def colorize_item_name(item, config=None) -> str:
    """Return the item's short_desc wrapped in its rarity color."""
    if config is None:
        config = Config()
    c = config.COLORS
    color_key = get_rarity_color(item)
    color = c.get(color_key, c.get('white', ''))
    reset = c.get('reset', '')
    name = getattr(item, 'short_desc', 'an object')
    rarity = getattr(item, 'rarity', 'common') or 'common'
    if rarity == 'legendary':
        return f"{c.get('bright_yellow', '')}✦ {name} ✦{reset}"
    elif rarity == 'epic':
        return f"{color}★ {name} ★{reset}"
    return f"{color}{name}{reset}"


# ═══════════════════════════════════════════════════════════════
# PROC / EFFECT SYSTEM
# ═══════════════════════════════════════════════════════════════

PROC_TYPES = {
    'on_hit': 'Chance on hit',
    'on_kill': 'On kill',
    'on_use': 'Use',
    'on_equip': 'Equip',
    'on_defend': 'When hit',
}

async def trigger_on_hit_procs(attacker, defender, damage: int, weapon=None):
    """Called from combat when attacker lands a hit. Checks weapon + all equipped items."""
    if not hasattr(attacker, 'equipment'):
        return 0
    
    extra_damage = 0
    c = Config().COLORS
    
    items_to_check = []
    if weapon:
        items_to_check.append(weapon)
    # Also check all equipped items for on_equip damage bonuses handled elsewhere
    for slot, item in attacker.equipment.items():
        if item and item != weapon and hasattr(item, 'procs'):
            items_to_check.append(item)
    
    for item in items_to_check:
        procs = getattr(item, 'procs', [])
        if not procs:
            continue
        for proc in procs:
            if proc.get('type') != 'on_hit':
                continue
            chance = proc.get('chance', 10)
            if random.randint(1, 100) > chance:
                continue
            
            effect = proc.get('effect', '')
            proc_dmg = proc.get('damage', 0)
            
            if effect == 'frost_damage':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_cyan']}❄ Frostmourne chills {defender.name}'s soul for {actual} frost damage!{c['reset']}")
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['bright_cyan']}❄ A deathly cold seeps into your bones! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'chain_lightning':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_yellow']}⚡ Thunderfury crackles — chain lightning arcs through {defender.name} for {actual} damage!{c['reset']}")
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['bright_yellow']}⚡ Lightning courses through you! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
                # Chain to one nearby enemy
                if attacker.room:
                    for char in attacker.room.characters:
                        if char != attacker and char != defender and char.is_alive and not hasattr(char, 'connection'):
                            chain_dmg = actual // 2
                            if chain_dmg > 0:
                                if hasattr(attacker, 'send'):
                                    await attacker.send(f"{c['bright_yellow']}⚡ Lightning chains to {char.name}! [{chain_dmg}]{c['reset']}")
                                await char.take_damage(chain_dmg, attacker)
                            break
            
            elif effect == 'holy_aoe':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_yellow']}☀ The Ashbringer erupts with holy fire! [{actual} to {defender.name}]{c['reset']}")
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['bright_yellow']}☀ Holy fire sears your flesh! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
                # AoE splash
                if attacker.room:
                    for char in attacker.room.characters:
                        if char != attacker and char != defender and char.is_alive and not hasattr(char, 'connection'):
                            splash = actual // 3
                            if splash > 0:
                                await char.take_damage(splash, attacker)
            
            elif effect == 'lifesteal':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                heal = actual
                attacker.hp = min(attacker.max_hp, attacker.hp + heal)
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_red']}💀 Soulreaper drains {actual} life from {defender.name}! (+{heal} HP){c['reset']}")
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['bright_red']}💀 Your life force is ripped away! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'spell_power':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_magenta']}✧ The Staff of the Archmage pulses with arcane energy! [{actual}]{c['reset']}")
                if hasattr(defender, 'send'):
                    await defender.send(f"{c['bright_magenta']}✧ Arcane energy blasts you! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'venom':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['green']}☠ Serpent's Fang injects venom into {defender.name}! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'vorpal':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_red']}⚔ Blade of the Fallen King strikes true! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'lightning_bolt':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_yellow']}⚡ Stormcaller unleashes a lightning bolt! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)
            
            elif effect == 'shadow_strike':
                actual = random.randint(proc_dmg // 2, proc_dmg)
                extra_damage += actual
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['bright_magenta']}🗡 Nightblade's shadow strikes from the void! [{actual}]{c['reset']}")
                await defender.take_damage(actual, attacker)

    return extra_damage


async def trigger_on_kill_procs(killer, victim):
    """Called when killer defeats victim. Check all equipped items."""
    if not hasattr(killer, 'equipment'):
        return
    c = Config().COLORS
    
    for slot, item in killer.equipment.items():
        if not item:
            continue
        procs = getattr(item, 'procs', [])
        for proc in procs:
            if proc.get('type') != 'on_kill':
                continue
            effect = proc.get('effect', '')
            if effect == 'restore_hp':
                pct = proc.get('percent', 10)
                heal = int(killer.max_hp * pct / 100)
                killer.hp = min(killer.max_hp, killer.hp + heal)
                if hasattr(killer, 'send'):
                    await killer.send(f"{c['bright_green']}💚 {item.short_desc} restores {heal} HP on the kill!{c['reset']}")
            elif effect == 'restore_mana':
                pct = proc.get('percent', 5)
                restore = int(killer.max_mana * pct / 100)
                killer.mana = min(killer.max_mana, killer.mana + restore)
                if hasattr(killer, 'send'):
                    await killer.send(f"{c['bright_cyan']}💙 {item.short_desc} restores {restore} mana!{c['reset']}")


def get_equip_bonuses(player) -> dict:
    """Calculate total equip-proc bonuses from all equipped legendary/epic items.
    Returns dict like {'damage_pct': 5, 'all_stats': 3, ...}."""
    bonuses = {}
    if not hasattr(player, 'equipment'):
        return bonuses
    for slot, item in player.equipment.items():
        if not item:
            continue
        procs = getattr(item, 'procs', [])
        for proc in procs:
            if proc.get('type') != 'on_equip':
                continue
            effect = proc.get('effect', '')
            value = proc.get('value', 0)
            bonuses[effect] = bonuses.get(effect, 0) + value
    return bonuses


# ═══════════════════════════════════════════════════════════════
# LEGENDARY ITEM DEFINITIONS (20 items, vnums 99001-99020)
# ═══════════════════════════════════════════════════════════════

LEGENDARY_ITEMS = {
    # ────────── WEAPONS ──────────
    99001: {
        'vnum': 99001, 'name': 'Frostmourne',
        'short_desc': 'Frostmourne, Blade of the Damned',
        'room_desc': 'A blade of black ice radiates a deathly chill here.',
        'description': 'This runeblade pulses with necrotic frost. Ice crystals form along its edge, and the air around it whispers with the voices of the consumed.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 12, 'cost': 50000,
        'damage_dice': '3d8', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'hitroll', 'value': 5}, {'type': 'damroll', 'value': 4}],
        'procs': [{'type': 'on_hit', 'effect': 'frost_damage', 'chance': 15, 'damage': 25,
                   'desc': 'Chance on hit: Chills the target\'s soul for 12-25 frost damage'}],
        'lore_text': 'Forged in the heart of a dying glacier by the Lich King himself, Frostmourne hungers for souls. Each kill feeds the blade, and each swing whispers promises of power to its wielder. Many have taken up this blade. None have put it down willingly.',
        'drop_source': 'The Lich King',
    },
    99002: {
        'vnum': 99002, 'name': 'Thunderfury',
        'short_desc': 'Thunderfury, Blessed Blade of the Windseeker',
        'room_desc': 'A crackling sword of living lightning lies here.',
        'description': 'Arcs of electricity dance along the curved blade. The air smells of ozone, and your hair stands on end just being near it.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 8, 'cost': 55000,
        'damage_dice': '3d7', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 3}, {'type': 'hitroll', 'value': 6}, {'type': 'damroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'chain_lightning', 'chance': 20, 'damage': 20,
                   'desc': 'Chance on hit: Chain lightning arcs for 10-20 damage, chaining to a nearby foe'}],
        'lore_text': 'Born from the essence of Thunderaan, Prince of Air, this blade carries the fury of every storm that has ever raged. The Windseeker himself was imprisoned within its core, and his rage manifests as living lightning that leaps from foe to foe.',
        'drop_source': 'Baron Thunderaan',
    },
    99003: {
        'vnum': 99003, 'name': 'Ashbringer',
        'short_desc': 'the Ashbringer, Sword of Holy Light',
        'room_desc': 'A golden sword blazes with divine radiance.',
        'description': 'This massive two-handed sword radiates a warm, golden light. The undead recoil from its presence, and the righteous feel their spirits lifted.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 14, 'cost': 60000,
        'damage_dice': '3d9', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 2}, {'type': 'wis', 'value': 3}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 5}],
        'procs': [{'type': 'on_hit', 'effect': 'holy_aoe', 'chance': 12, 'damage': 30,
                   'desc': 'Chance on hit: Holy fire erupts for 15-30 damage to target and nearby enemies'}],
        'lore_text': 'Created from a crystal of pure Light found in an ancient naaru\'s remains, the Ashbringer was forged to turn the undead to ash. Its name is both promise and warning — for where it swings, only ashes remain.',
        'drop_source': 'The Corrupted Highlord',
    },
    99004: {
        'vnum': 99004, 'name': 'Soulreaper',
        'short_desc': 'Soulreaper, the Hungering Scythe',
        'room_desc': 'A wicked scythe with a blade of living shadow lies here.',
        'description': 'The curved blade seems to drink the light around it. Faint screaming echoes from within the weapon, and dark tendrils reach out toward the living.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 10, 'cost': 48000,
        'damage_dice': '3d7', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 2}, {'type': 'con', 'value': 2}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 4}],
        'procs': [
            {'type': 'on_hit', 'effect': 'lifesteal', 'chance': 18, 'damage': 20,
             'desc': 'Chance on hit: Drains 10-20 life from target, healing you'},
            {'type': 'on_kill', 'effect': 'restore_hp', 'percent': 10,
             'desc': 'On kill: Restore 10% of max HP'},
        ],
        'lore_text': 'Soulreaper was crafted by a mad necromancer who sought to cheat death itself. The scythe feeds on the essence of those it slays, trapping fragments of their souls within the blade. Its wielder heals with every life taken, but the whispers of the trapped grow louder with each kill.',
        'drop_source': 'Dreadlord Malachar',
    },
    99005: {
        'vnum': 99005, 'name': 'Staff of the Archmage',
        'short_desc': 'the Staff of the Archmage',
        'room_desc': 'An ancient staff of impossible power thrums with arcane energy.',
        'description': 'Runes of every known magical tradition spiral along this staff. The crystal atop it contains a miniature galaxy, swirling with captured starlight.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 6, 'cost': 52000,
        'damage_dice': '2d8', 'weapon_type': 'pound', 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 5}, {'type': 'wis', 'value': 3}, {'type': 'mana', 'value': 50}, {'type': 'hitroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'spell_power', 'chance': 20, 'damage': 22,
                   'desc': 'Chance on hit: Arcane energy blasts target for 11-22 damage'},
                  {'type': 'on_equip', 'effect': 'damage_pct', 'value': 5,
                   'desc': 'Equip: +5% to all spell damage'}],
        'lore_text': 'This staff has been wielded by every Archmage of the Conclave for a thousand years. Each added their own enchantments, layering spell upon spell until the staff itself became a nexus of raw magical power. It is said to be semi-sentient, choosing its wielder rather than being chosen.',
        'drop_source': 'Archlich Vel\'koz',
    },

    # ────────── ARMOR ──────────
    99006: {
        'vnum': 99006, 'name': 'Crown of the Lich King',
        'short_desc': 'the Crown of the Lich King',
        'room_desc': 'A crown of frozen iron radiates dread.',
        'description': 'This jagged crown of dark iron is perpetually rimed with frost. Those who look upon it feel an overwhelming urge to kneel.',
        'item_type': 'armor', 'wear_slot': 'head', 'weight': 5, 'cost': 45000,
        'armor': 12, 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 4}, {'type': 'wis', 'value': 2}, {'type': 'cha', 'value': -3}, {'type': 'armor', 'value': -15}],
        'procs': [{'type': 'on_defend', 'effect': 'fear_aura', 'chance': 10,
                   'desc': 'When hit: 10% chance attackers flee in fear for 1 round'}],
        'lore_text': 'The Crown of the Lich King contains the imprisoned spirit of the orc shaman Ner\'zhul, whose ambition transcended death itself. Whoever dons the crown hears his whispers, promising dominion over the dead — but the crown\'s true master may not be who you think.',
        'drop_source': 'The Lich King',
    },
    99007: {
        'vnum': 99007, 'name': 'Dragonscale Breastplate',
        'short_desc': 'the Dragonscale Breastplate of Onyxia',
        'room_desc': 'A breastplate of iridescent dragon scales gleams here.',
        'description': 'Crafted from the scales of a fallen dragon, this breastplate shimmers between crimson and obsidian. It radiates warmth and seems almost alive.',
        'item_type': 'armor', 'wear_slot': 'body', 'weight': 20, 'cost': 55000,
        'armor': 18, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 4}, {'type': 'str', 'value': 2}, {'type': 'armor', 'value': -25}],
        'procs': [{'type': 'on_defend', 'effect': 'fire_resist', 'chance': 100,
                   'desc': 'Equip: Fire damage reduced by 30%'},
                  {'type': 'on_hit', 'effect': 'fire_breath', 'chance': 8, 'damage': 28,
                   'desc': 'Chance on hit: Breathe dragonfire for 14-28 damage'}],
        'lore_text': 'The scales of Onyxia the Black were said to be impervious to all but the most powerful magic. This breastplate, forged in dragonfire itself, retains a fraction of the great wyrm\'s essence. Wearers report dreams of soaring over burning landscapes.',
        'drop_source': 'Onyxia the Black Dragon',
    },
    99008: {
        'vnum': 99008, 'name': 'Boots of Hermes',
        'short_desc': 'the Boots of Hermes',
        'room_desc': 'Winged boots hover slightly above the ground.',
        'description': 'These gleaming silver boots sport tiny golden wings at the ankles. They seem to defy gravity, hovering a finger\'s width above any surface.',
        'item_type': 'armor', 'wear_slot': 'feet', 'weight': 2, 'cost': 40000,
        'armor': 5, 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'move', 'value': 100}],
        'procs': [{'type': 'on_equip', 'effect': 'double_speed', 'value': 1,
                   'desc': 'Equip: Movement costs halved'}],
        'lore_text': 'Gifted by the god of messengers to a mortal hero who earned his favor, these boots have carried their wearers across continents in a single day. The wings are not merely decorative — they flutter in response to the wearer\'s intent, as if eager to fly.',
        'drop_source': 'The Immortal Herald',
    },
    99009: {
        'vnum': 99009, 'name': 'Cloak of Shadows',
        'short_desc': 'the Cloak of Shadows',
        'room_desc': 'A cloak of living shadow pools on the ground.',
        'description': 'This cloak seems woven from pure darkness. Its edges blur and shift, making it hard to focus on. When worn, the wearer seems to fade from perception.',
        'item_type': 'armor', 'wear_slot': 'about', 'weight': 1, 'cost': 42000,
        'armor': 4, 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 3}, {'type': 'sneak', 'value': 25}, {'type': 'hide', 'value': 25}],
        'procs': [{'type': 'on_equip', 'effect': 'stealth_bonus', 'value': 20,
                   'desc': 'Equip: +20% stealth effectiveness'}],
        'lore_text': 'The Cloak of Shadows was spun from the essence of the Shadowfell by the Night Mother, patron of assassins. It does not merely hide the wearer — it convinces reality that the wearer was never there at all. Even gods have been fooled by its enchantment.',
        'drop_source': 'The Night Mother',
    },

    # ────────── ACCESSORIES ──────────
    99010: {
        'vnum': 99010, 'name': 'Ring of Power',
        'short_desc': 'the Ring of Power',
        'room_desc': 'A plain gold ring glows with inner fire.',
        'description': 'A seemingly simple gold band that radiates warmth. Looking at it too long fills you with visions of conquest and glory.',
        'item_type': 'armor', 'wear_slot': 'finger1', 'weight': 0, 'cost': 65000,
        'armor': 0, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'int', 'value': 3}, {'type': 'wis', 'value': 3},
                    {'type': 'dex', 'value': 3}, {'type': 'con', 'value': 3}, {'type': 'cha', 'value': 3}],
        'procs': [{'type': 'on_equip', 'effect': 'all_stats', 'value': 3,
                   'desc': 'Equip: All stats +3'}],
        'lore_text': 'One ring to rule them all, one ring to find them. Forged in the fires of Mount Doom by the Dark Lord, this ring contains a portion of his will and power. It whispers to its wearer, promising strength — but its loyalty lies only with its creator.',
        'drop_source': 'The Dark Lord Sauron',
    },
    99011: {
        'vnum': 99011, 'name': 'Amulet of the Phoenix',
        'short_desc': 'the Amulet of the Phoenix',
        'room_desc': 'A fiery amulet blazes with the light of rebirth.',
        'description': 'A golden amulet shaped like a phoenix in flight. The ruby at its heart pulses with living flame, and it is warm to the touch even in the coldest dungeon.',
        'item_type': 'armor', 'wear_slot': 'neck1', 'weight': 1, 'cost': 70000,
        'armor': 2, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 3}, {'type': 'hp', 'value': 30}],
        'procs': [{'type': 'on_defend', 'effect': 'auto_resurrect', 'chance': 100,
                   'desc': 'On death: Auto-resurrect at 50% HP (once per hour)'}],
        'lore_text': 'Crafted from a feather freely given by the last phoenix, this amulet carries the essence of rebirth. When its wearer falls, the phoenix within awakens, wrapping them in cleansing flame and restoring them to life. The amulet then slumbers, needing time to recover its power.',
        'drop_source': 'The Phoenix Guardian',
    },
    99012: {
        'vnum': 99012, 'name': 'Eye of the Seer',
        'short_desc': 'the Eye of the Seer',
        'room_desc': 'A crystalline eye on a silver chain stares unblinking.',
        'description': 'A perfect crystal sphere on a delicate silver chain. Within it, an iris of swirling colors watches everything, seeing through all deception.',
        'item_type': 'armor', 'wear_slot': 'neck2', 'weight': 1, 'cost': 38000,
        'armor': 1, 'rarity': 'legendary',
        'affects': [{'type': 'wis', 'value': 4}, {'type': 'int', 'value': 2}],
        'procs': [{'type': 'on_equip', 'effect': 'detect_all', 'value': 1,
                   'desc': 'Equip: Detect hidden, invisible, and alignment'}],
        'lore_text': 'Plucked from the socket of a dying oracle who chose to give her sight to the world rather than take it to the grave, this eye sees what mortal eyes cannot. Hidden doors, invisible foes, the alignment of souls — nothing escapes its crystalline gaze.',
        'drop_source': 'The Blind Oracle',
    },

    # ────────── 8 MORE LEGENDARIES ──────────
    99013: {
        'vnum': 99013, 'name': 'Serpent\'s Fang',
        'short_desc': 'Serpent\'s Fang, Dagger of the Viper',
        'room_desc': 'A curved dagger dripping with emerald venom lies here.',
        'description': 'This sinuous dagger is shaped like a serpent\'s fang. Green venom constantly weeps from its edge, hissing where it touches stone.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 3, 'cost': 44000,
        'damage_dice': '2d8', 'weapon_type': 'stab', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'hitroll', 'value': 6}, {'type': 'damroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'venom', 'chance': 25, 'damage': 15,
                   'desc': 'Chance on hit: Injects venom for 7-15 poison damage'}],
        'lore_text': 'Carved from the fang of the World Serpent by the assassin-queen Vashara, this dagger has ended more lives than any army. Its venom adapts to its victim, always finding a weakness in their constitution.',
        'drop_source': 'Vashara the Serpent Queen',
    },
    99014: {
        'vnum': 99014, 'name': 'Aegis of the Immortal',
        'short_desc': 'the Aegis of the Immortal',
        'room_desc': 'A radiant golden shield thrums with protective magic.',
        'description': 'This tower shield bears the face of a roaring lion wreathed in golden light. Dents and scratches heal themselves before your eyes.',
        'item_type': 'armor', 'wear_slot': 'shield', 'weight': 15, 'cost': 50000,
        'armor': 15, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 3}, {'type': 'armor', 'value': -30}, {'type': 'hp', 'value': 25}],
        'procs': [{'type': 'on_defend', 'effect': 'damage_reflect', 'chance': 15,
                   'desc': 'When hit: 15% chance to reflect 25% damage back to attacker'}],
        'lore_text': 'The Aegis was forged by divine smiths for a champion who stood alone against an army of ten thousand. Though the champion eventually fell, the shield endured — and it remembers. It fights alongside its wielder, punishing those who dare strike against the one it protects.',
        'drop_source': 'The Eternal Champion',
    },
    99015: {
        'vnum': 99015, 'name': 'Blade of the Fallen King',
        'short_desc': 'the Blade of the Fallen King',
        'room_desc': 'A bloodstained greatsword mourns here in silence.',
        'description': 'This massive greatsword is etched with the names of every king who has fallen in battle. The blade weeps crimson tears that vanish before touching the ground.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 16, 'cost': 58000,
        'damage_dice': '4d6', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 5}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 6}],
        'procs': [{'type': 'on_hit', 'effect': 'vorpal', 'chance': 8, 'damage': 40,
                   'desc': 'Chance on hit: Devastating vorpal strike for 20-40 damage'},
                  {'type': 'on_kill', 'effect': 'restore_hp', 'percent': 15,
                   'desc': 'On kill: Restore 15% of max HP'}],
        'lore_text': 'Each name etched into this blade appeared of its own accord at the moment of a king\'s death. The sword mourns royalty and empowers warriors. Those who wield it hear the battle cries of fallen monarchs, driving them to fight with supernatural fury.',
        'drop_source': 'The Revenant King',
    },
    99016: {
        'vnum': 99016, 'name': 'Stormcaller',
        'short_desc': 'Stormcaller, Warhammer of Thunder',
        'room_desc': 'A massive warhammer crackles with dormant storms.',
        'description': 'This enormous warhammer is carved from a single bolt of petrified lightning. Storm clouds seem to gather whenever it is raised.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 18, 'cost': 53000,
        'damage_dice': '3d8', 'weapon_type': 'pound', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 4}, {'type': 'con', 'value': 2}, {'type': 'hitroll', 'value': 5}, {'type': 'damroll', 'value': 5}],
        'procs': [{'type': 'on_hit', 'effect': 'lightning_bolt', 'chance': 15, 'damage': 25,
                   'desc': 'Chance on hit: Call down a lightning bolt for 12-25 damage'}],
        'lore_text': 'Stormcaller was forged in the eye of a hurricane that raged for a hundred years. The storm god himself struck the anvil with lightning to temper the metal. Whoever lifts this hammer commands the storm — thunder answers their rage, and lightning obeys their fury.',
        'drop_source': 'Jarl Stormfist',
    },
    99017: {
        'vnum': 99017, 'name': 'Nightblade',
        'short_desc': 'Nightblade, Shadow\'s Edge',
        'room_desc': 'A sword of absolute darkness absorbs the light around it.',
        'description': 'This sword appears as a void in reality — a blade-shaped absence of light. Even in bright rooms, shadows gather around it hungrily.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 5, 'cost': 46000,
        'damage_dice': '3d6', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'hitroll', 'value': 7}, {'type': 'sneak', 'value': 15}],
        'procs': [{'type': 'on_hit', 'effect': 'shadow_strike', 'chance': 18, 'damage': 18,
                   'desc': 'Chance on hit: Shadow strikes from the void for 9-18 damage'}],
        'lore_text': 'Nightblade was never forged — it was cut from the fabric of the Shadowfell itself by a god of thieves. It exists in two planes simultaneously, striking from angles that should be impossible. Those slain by Nightblade cast no shadow in death.',
        'drop_source': 'Shadow Lord Malakai',
    },
    99018: {
        'vnum': 99018, 'name': 'Gauntlets of the Titan',
        'short_desc': 'the Gauntlets of the Titan',
        'room_desc': 'Massive stone gauntlets pulse with primordial power.',
        'description': 'These gauntlets appear carved from living stone, yet they flex like leather. Runes of the elder titans glow along each finger.',
        'item_type': 'armor', 'wear_slot': 'hands', 'weight': 8, 'cost': 47000,
        'armor': 10, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 5}, {'type': 'damroll', 'value': 4}, {'type': 'armor', 'value': -20}],
        'procs': [{'type': 'on_equip', 'effect': 'damage_pct', 'value': 5,
                   'desc': 'Equip: +5% to all damage'}],
        'lore_text': 'Worn by the titan Kronax when he shaped the mountains with his bare hands, these gauntlets retain a fraction of his world-shaping power. The ground trembles slightly with every step of the one who wears them.',
        'drop_source': 'The Stone Colossus',
    },
    99019: {
        'vnum': 99019, 'name': 'Sash of Infinite Stars',
        'short_desc': 'the Sash of Infinite Stars',
        'room_desc': 'A belt of woven starlight shimmers impossibly here.',
        'description': 'This sash appears to be made of captured starlight. Tiny constellations drift across its surface, mapping a sky that belongs to no known world.',
        'item_type': 'armor', 'wear_slot': 'waist', 'weight': 1, 'cost': 43000,
        'armor': 3, 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 3}, {'type': 'wis', 'value': 3}, {'type': 'mana', 'value': 40}],
        'procs': [{'type': 'on_kill', 'effect': 'restore_mana', 'percent': 8,
                   'desc': 'On kill: Restore 8% of max mana'}],
        'lore_text': 'Woven by the Celestial Weaver from threads of actual starlight, this sash connects its wearer to the cosmos. Each star that drifts across its surface is real — and when one winks out, a star somewhere in the sky dies.',
        'drop_source': 'The Celestial Weaver',
    },
    99020: {
        'vnum': 99020, 'name': 'Vambraces of the Warlord',
        'short_desc': 'the Vambraces of the Warlord',
        'room_desc': 'Battle-scarred vambraces radiate an aura of conquest.',
        'description': 'These wrist guards bear the scars of a thousand battles. Despite their battered appearance, they are harder than any known metal and hum with martial energy.',
        'item_type': 'armor', 'wear_slot': 'wrist1', 'weight': 4, 'cost': 41000,
        'armor': 8, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'dex', 'value': 2}, {'type': 'hitroll', 'value': 3}, {'type': 'armor', 'value': -15}],
        'procs': [{'type': 'on_equip', 'effect': 'damage_pct', 'value': 3,
                   'desc': 'Equip: +3% to all melee damage'}],
        'lore_text': 'Worn by Warlord Kargath through his legendary campaign that conquered seven kingdoms in a single year, these vambraces absorbed the essence of every foe he defeated. They make the wearer\'s arms tireless and their strikes unerring.',
        'drop_source': 'Warlord Kargath\'s Shade',
    },
}


# ═══════════════════════════════════════════════════════════════
# BOSS → LEGENDARY DROP TABLE
# ═══════════════════════════════════════════════════════════════

# Maps boss mob names (lowercase) to (legendary_vnum, drop_chance_percent)
BOSS_LEGENDARY_DROPS = {
    'the lich king': (99001, 3),
    'lich king': (99001, 3),
    'baron thunderaan': (99002, 4),
    'thunderaan': (99002, 4),
    'the corrupted highlord': (99003, 3),
    'highlord': (99003, 3),
    'dreadlord malachar': (99004, 5),
    'malachar': (99004, 5),
    'archlich vel\'koz': (99005, 4),
    'vel\'koz': (99005, 4),
    'onyxia': (99007, 3),
    'onyxia the black dragon': (99007, 3),
    'the immortal herald': (99008, 4),
    'the night mother': (99009, 3),
    'the dark lord sauron': (99010, 2),
    'sauron': (99010, 2),
    'the phoenix guardian': (99011, 3),
    'the blind oracle': (99012, 5),
    'vashara': (99013, 4),
    'vashara the serpent queen': (99013, 4),
    'the eternal champion': (99014, 4),
    'the revenant king': (99015, 3),
    'jarl stormfist': (99016, 4),
    'shadow lord malakai': (99017, 4),
    'malakai': (99017, 4),
    'the stone colossus': (99018, 4),
    'the celestial weaver': (99019, 5),
    'warlord kargath': (99020, 4),
}

# Also map by mob flags/is_boss for generic bosses
def get_legendary_drop_for_boss(mob) -> Optional[int]:
    """Check if a boss mob should drop a legendary. Returns vnum or None."""
    if not getattr(mob, 'is_boss', False):
        return None
    
    name = getattr(mob, 'name', '').lower().strip()
    
    # Check specific boss drops
    if name in BOSS_LEGENDARY_DROPS:
        vnum, chance = BOSS_LEGENDARY_DROPS[name]
        if random.randint(1, 100) <= chance:
            return vnum
    
    # Check short_desc too
    short = getattr(mob, 'short_desc', '').lower().strip()
    if short in BOSS_LEGENDARY_DROPS:
        vnum, chance = BOSS_LEGENDARY_DROPS[short]
        if random.randint(1, 100) <= chance:
            return vnum
    
    # Generic boss: 1% chance for a random legendary
    if random.randint(1, 100) <= 1:
        return random.choice(list(LEGENDARY_ITEMS.keys()))
    
    return None


def create_legendary(vnum: int, world=None):
    """Create a legendary item Object from its definition."""
    from objects import Object
    
    if vnum not in LEGENDARY_ITEMS:
        return None
    
    proto = LEGENDARY_ITEMS[vnum]
    obj = Object.from_prototype(proto, world)
    obj.rarity = 'legendary'
    obj.procs = proto.get('procs', [])
    obj.lore_text = proto.get('lore_text', '')
    obj.drop_source = proto.get('drop_source', 'Unknown')
    return obj


async def announce_legendary_drop(world, player_name: str, item_name: str):
    """Broadcast a server-wide announcement when a legendary drops."""
    c = Config().COLORS
    border = f"{c['bright_yellow']}{'═' * 60}{c['reset']}"
    msg = (
        f"\r\n{border}\r\n"
        f"{c['bright_yellow']}  ✦✦✦ LEGENDARY DROP ✦✦✦{c['reset']}\r\n"
        f"{c['bright_white']}  {player_name} has obtained {c['bright_yellow']}✦ {item_name} ✦{c['bright_white']}!{c['reset']}\r\n"
        f"{border}"
    )
    if world:
        await world.broadcast(msg)


# ═══════════════════════════════════════════════════════════════
# INSPECT COMMAND HELPER
# ═══════════════════════════════════════════════════════════════

def format_inspect(item, config=None) -> list:
    """Return a list of formatted lines for the inspect command."""
    if config is None:
        config = Config()
    c = config.COLORS
    lines = []
    
    rarity = getattr(item, 'rarity', 'common') or 'common'
    tier = RARITY_TIERS.get(rarity, RARITY_TIERS['common'])
    rcolor = c.get(tier['color_code'], c.get('white', ''))
    
    lines.append(f"{c['bright_cyan']}{'═' * 55}{c['reset']}")
    lines.append(f"{rcolor}  {colorize_item_name(item, config)}{c['reset']}")
    lines.append(f"{c['white']}  Rarity: {rcolor}{tier['label']}{c['reset']}")
    lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
    
    # Description
    desc = getattr(item, 'description', '')
    if desc:
        lines.append(f"{c['white']}  {desc}{c['reset']}")
        lines.append("")
    
    # Stats
    if getattr(item, 'item_type', '') == 'weapon':
        lines.append(f"{c['yellow']}  Damage: {item.damage_dice} ({item.weapon_type}){c['reset']}")
    if getattr(item, 'item_type', '') == 'armor' and getattr(item, 'armor', 0):
        lines.append(f"{c['yellow']}  Armor: {item.armor}{c['reset']}")
    if getattr(item, 'wear_slot', None):
        lines.append(f"{c['yellow']}  Slot: {item.wear_slot}{c['reset']}")
    
    # Affects
    affects = getattr(item, 'affects', [])
    if affects:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        for aff in affects:
            if isinstance(aff, dict):
                lines.append(f"{c['bright_magenta']}  Affects {aff.get('type', '?')}: {aff.get('value', 0):+d}{c['reset']}")
    
    # Procs
    procs = getattr(item, 'procs', [])
    if procs:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        for proc in procs:
            desc_text = proc.get('desc', f"{PROC_TYPES.get(proc.get('type', ''), 'Effect')}: {proc.get('effect', 'unknown')}")
            lines.append(f"{c['bright_yellow']}  ⚡ {desc_text}{c['reset']}")
    
    # Lore
    lore = getattr(item, 'lore_text', '')
    if lore:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        lines.append(f"{c['bright_black']}  \"{lore}\"{c['reset']}")
    
    # Drop source
    source = getattr(item, 'drop_source', '')
    if source:
        lines.append(f"{c['white']}  Drops from: {c['bright_red']}{source}{c['reset']}")
    
    lines.append(f"{c['white']}  Weight: {getattr(item, 'weight', 0)}  Value: {getattr(item, 'cost', 0)} gold{c['reset']}")
    lines.append(f"{c['bright_cyan']}{'═' * 55}{c['reset']}")
    
    return lines
