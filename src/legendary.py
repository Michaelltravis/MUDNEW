"""
Misthollow Legendary Item System
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

logger = logging.getLogger('Misthollow.Legendary')

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

# The procs themselves live in procs.py (one engine for legendaries, zone items and sets);
# these names stay for older callers.


async def trigger_on_hit_procs(attacker, defender, damage: int = 0, weapon=None):
    import procs
    return await procs.on_hit(attacker, defender, weapon)


async def trigger_on_kill_procs(killer, victim):
    import procs
    await procs.on_kill(killer, victim)


def get_equip_bonuses(player) -> dict:
    import procs
    return procs.equip_totals([it for it in (getattr(player, 'equipment', None) or {}).values() if it])


# ═══════════════════════════════════════════════════════════════
# LEGENDARY ITEM DEFINITIONS (20 items, vnums 99001-99020)
# ═══════════════════════════════════════════════════════════════

LEGENDARY_ITEMS = {
    # ────────── WEAPONS ──────────
    99001: {
        'vnum': 99001, 'name': 'Whisper of the Drowned God',
        'short_desc': 'Whisper of the Drowned God',
        'room_desc': 'A trident of black coral weeps salt water onto the stone.',
        'description': 'Three tines of ancient coral, dark as the abyssal trench. Barnacles cling to the haft in patterns that resemble screaming faces. The air around it tastes of brine and something older than the sea.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 12, 'cost': 50000,
        'damage_dice': '3d8', 'weapon_type': 'stab', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'hitroll', 'value': 5}, {'type': 'damroll', 'value': 4}],
        'procs': [{'type': 'on_hit', 'effect': 'phantom_drown', 'chance': 15, 'damage': 25,
                   'desc': 'Chance on hit: Phantom water fills the target\'s lungs, stunning them for 12-25 damage'}],
        'lore_text': 'Pulled from the throat of a leviathan that had swallowed an entire harbor town. The townspeople were never found, but their voices still echo from inside the coral — whispering tide tables, lullabies, and the coordinates of a city that sank before the first sunrise.',
        'drop_source': 'The Drowned Apostle',
    },
    99002: {
        'vnum': 99002, 'name': 'Requiem of Fractured Harmonics',
        'short_desc': 'Requiem of Fractured Harmonics',
        'room_desc': 'A crystalline blade hums with a sound just beyond hearing.',
        'description': 'A longsword forged from a single resonant crystal, its edge vibrating at a frequency that makes your teeth ache. Hairline fractures run through it like frozen lightning — each one a different note waiting to shatter free.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 8, 'cost': 55000,
        'damage_dice': '3d7', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 3}, {'type': 'hitroll', 'value': 6}, {'type': 'damroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'echo_shatter', 'chance': 20, 'damage': 20,
                   'desc': 'Chance on hit: A shattering harmonic erupts for 10-20 damage, echoing to a nearby foe'}],
        'lore_text': 'A deaf composer spent forty years carving this blade from a singing crystal found in a collapsed cathedral. She could feel the vibrations through her fingertips — every frequency mapped to a different way to die. She finished it, played it once, and was found smiling in a room where every window had melted.',
        'drop_source': 'The Shattered Cantor',
    },
    99003: {
        'vnum': 99003, 'name': 'Cataract, the Mirror-Eater',
        'short_desc': 'Cataract, the Mirror-Eater',
        'room_desc': 'A greatsword of liquid mercury holds its shape against all reason.',
        'description': 'This massive blade appears to be made of living mercury — it reflects everything around it, but wrong. Your reflection in its surface moves a half-second too late, and sometimes it smiles when you don\'t.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 14, 'cost': 60000,
        'damage_dice': '3d9', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 2}, {'type': 'wis', 'value': 3}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 5}],
        'procs': [{'type': 'on_hit', 'effect': 'glass_splinter', 'chance': 12, 'damage': 30,
                   'desc': 'Chance on hit: The target\'s reflection shatters outward for 15-30 damage, splashing nearby enemies'}],
        'lore_text': 'Every mirror in the palace shattered the night it was forged. The royal alchemist had discovered that reflections are not copies — they are prisoners. Cataract frees them violently. Those struck by it see their own face rushing toward them from impossible angles, and the shards are very, very real.',
        'drop_source': 'The Mercurial Alchemist',
    },
    99004: {
        'vnum': 99004, 'name': 'Famine\'s Needle',
        'short_desc': 'Famine\'s Needle, the Hollow Fang',
        'room_desc': 'A bone-white scythe radiates a desperate, gnawing hunger.',
        'description': 'Carved from the rib of something that starved to death over geological time. The blade is hollow — a needle that drinks rather than cuts. The air near it feels thin, as if even oxygen is being consumed.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 10, 'cost': 48000,
        'damage_dice': '3d7', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 2}, {'type': 'con', 'value': 2}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 4}],
        'procs': [
            {'type': 'on_hit', 'effect': 'hunger_drain', 'chance': 18, 'damage': 20,
             'desc': 'Chance on hit: Devours 10-20 vitality from target, feeding the wielder'},
            {'type': 'on_kill', 'effect': 'restore_hp', 'percent': 10,
             'desc': 'On kill: Restore 10% of max HP'},
        ],
        'lore_text': 'It was not crafted — it grew. In a desert where nothing had eaten for a thousand years, hunger itself calcified into bone. The first person to touch it felt full for the first time in their life. The second person to touch it was the first person\'s dinner.',
        'drop_source': 'The Hollow Matriarch',
    },
    99005: {
        'vnum': 99005, 'name': 'Synapse of the Last Astronomer',
        'short_desc': 'Synapse of the Last Astronomer',
        'room_desc': 'A staff of petrified nerve tissue crackles with captured starlight.',
        'description': 'This staff is a single petrified neuron, enlarged to impossible scale. Dendrites branch at its crown, each tip holding a tiny imprisoned star. When you hold it, you can feel it thinking.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 6, 'cost': 52000,
        'damage_dice': '2d8', 'weapon_type': 'pound', 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 5}, {'type': 'wis', 'value': 3}, {'type': 'mana', 'value': 50}, {'type': 'hitroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'dream_fracture', 'chance': 20, 'damage': 22,
                   'desc': 'Chance on hit: Fractures the boundary between dreaming and waking for 11-22 damage'},
                  {'type': 'on_equip', 'effect': 'damage_pct', 'value': 5,
                   'desc': 'Equip: +5% to all spell damage'}],
        'lore_text': 'The Last Astronomer mapped every star in the sky and found they formed a neural network. The universe, she realized, was a brain — and it was dreaming us. She extracted one of its thoughts and made it into a staff. The universe has not stopped looking for it.',
        'drop_source': 'The Paradox Archivist',
    },

    # ────────── ARMOR ──────────
    99006: {
        'vnum': 99006, 'name': 'Hollowbone Crown',
        'short_desc': 'the Hollowbone Crown',
        'room_desc': 'A crown of pale bone from something that was never alive sits here.',
        'description': 'Interlocking bones from no known creature form this circlet. They are hollow — peer through them and you glimpse rooms you have never visited, corridors that may not exist yet. It weighs almost nothing, as if it exists only partially.',
        'item_type': 'armor', 'wear_slot': 'head', 'weight': 5, 'cost': 45000,
        'armor': 12, 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 4}, {'type': 'wis', 'value': 2}, {'type': 'cha', 'value': -3}, {'type': 'armor', 'value': -15}],
        'procs': [{'type': 'on_defend', 'effect': 'fear_aura', 'chance': 10,
                   'desc': 'When hit: 10% chance attackers flee in terror, seeing visions of their own skeleton'}],
        'lore_text': 'The bones belong to something that was imagined but never born — a creature from an abandoned draft of creation. It remembers being almost-real, and it hates. Wearers report seeing through walls, but also being seen by things on the other side that press their faces against the stone and whisper.',
        'drop_source': 'The Unborn Architect',
    },
    99007: {
        'vnum': 99007, 'name': 'Carapace of the Rust Sovereign',
        'short_desc': 'the Carapace of the Rust Sovereign',
        'room_desc': 'A breastplate of living rust breathes flakes of corroded iron.',
        'description': 'This armor is made of rust — not rusted metal, but rust itself, compressed into plates that flex like chitin. Orange-red spores drift from its surface. Any metal that touches it begins to oxidize.',
        'item_type': 'armor', 'wear_slot': 'body', 'weight': 20, 'cost': 55000,
        'armor': 18, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 4}, {'type': 'str', 'value': 2}, {'type': 'armor', 'value': -25}],
        'procs': [{'type': 'on_defend', 'effect': 'fire_resist', 'chance': 100,
                   'desc': 'Equip: Corrosion absorbs fire — fire damage reduced by 30%'},
                  {'type': 'on_hit', 'effect': 'rust_devour', 'chance': 8, 'damage': 28,
                   'desc': 'Chance on hit: Living rust crawls across the target for 14-28 damage'}],
        'lore_text': 'In the deepest iron mines, miners found a vein that was already corroded. The rust moved. It consumed their tools, their lanterns, their belt buckles. One miner let it consume his skin and became something new — an apostle of entropy, preaching that all things must return to dust. This is his sermon, worn as armor.',
        'drop_source': 'The Rust Sovereign',
    },
    99008: {
        'vnum': 99008, 'name': 'Threshold Walkers',
        'short_desc': 'the Threshold Walkers',
        'room_desc': 'A pair of boots made from compressed doorways hovers slightly above the floor.',
        'description': 'These boots are stitched from the leather of doors — thresholds, specifically, the worn strips where thousands of feet have crossed between rooms. They hover a finger\'s width above any surface, refusing to fully commit to being anywhere.',
        'item_type': 'armor', 'wear_slot': 'feet', 'weight': 2, 'cost': 40000,
        'armor': 5, 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'move', 'value': 100}],
        'procs': [{'type': 'on_equip', 'effect': 'double_speed', 'value': 1,
                   'desc': 'Equip: Movement costs halved — you exist between steps'}],
        'lore_text': 'A carpenter who had built ten thousand doors realized that thresholds are the thinnest places in reality — the spots where one room becomes another. She harvested that thinness and stitched it into boots. The wearer doesn\'t walk so much as continuously arrive.',
        'drop_source': 'The Liminal Cartographer',
    },
    99009: {
        'vnum': 99009, 'name': 'Penumbra of Forgotten Names',
        'short_desc': 'the Penumbra of Forgotten Names',
        'room_desc': 'A cloak woven from condensed silence pools on the ground.',
        'description': 'This cloak is made from silence — actual silence, harvested from libraries, deathbeds, and the moment before a scream. Names are stitched into its hem in thread that becomes invisible when read.',
        'item_type': 'armor', 'wear_slot': 'about', 'weight': 1, 'cost': 42000,
        'armor': 4, 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 3}, {'type': 'sneak', 'value': 25}, {'type': 'hide', 'value': 25}],
        'procs': [{'type': 'on_equip', 'effect': 'stealth_bonus', 'value': 20,
                   'desc': 'Equip: +20% stealth — you become a name no one remembers'}],
        'lore_text': 'Every person whose name has been completely forgotten contributed one syllable to this cloak. It does not make you invisible — it makes you forgettable. Guards who see you immediately lose the memory. Friends must concentrate to recall your face. The price is that, slowly, you begin to forget your own name too.',
        'drop_source': 'The Nameless Registrar',
    },

    # ────────── ACCESSORIES ──────────
    99010: {
        'vnum': 99010, 'name': 'Ouroboros Circuit',
        'short_desc': 'the Ouroboros Circuit',
        'room_desc': 'A ring of tarnished silver eats its own tail endlessly.',
        'description': 'A serpent swallowing itself, rendered in silver so old it has forgotten what it was before it was a ring. Wearing it creates a faint closed-loop hum in your bones, as if your bloodstream has become circular in a way it wasn\'t before.',
        'item_type': 'armor', 'wear_slot': 'finger1', 'weight': 0, 'cost': 65000,
        'armor': 0, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'int', 'value': 3}, {'type': 'wis', 'value': 3},
                    {'type': 'dex', 'value': 3}, {'type': 'con', 'value': 3}, {'type': 'cha', 'value': 3}],
        'procs': [{'type': 'on_equip', 'effect': 'all_stats', 'value': 3,
                   'desc': 'Equip: All stats +3 — your potential loops back on itself, amplifying'}],
        'lore_text': 'The ring has no beginning and no maker. Attempts to determine its origin reveal only that it has always existed and has always been found, never made. Scholars theorize it is a closed causal loop — an effect that is its own cause. Wearing it feels like completing a circuit you didn\'t know was open.',
        'drop_source': 'The Paradox Engine',
    },
    99011: {
        'vnum': 99011, 'name': 'Cocoon of Arrested Decay',
        'short_desc': 'the Cocoon of Arrested Decay',
        'room_desc': 'An amber amulet pulses with suspended time.',
        'description': 'A pendant of dark amber containing a single frozen moment — a moth caught mid-metamorphosis, neither caterpillar nor winged thing. The amber is warm and smells faintly of autumn and formaldehyde.',
        'item_type': 'armor', 'wear_slot': 'neck1', 'weight': 1, 'cost': 70000,
        'armor': 2, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 3}, {'type': 'hp', 'value': 30}],
        'procs': [{'type': 'on_defend', 'effect': 'auto_resurrect', 'chance': 100,
                   'desc': 'On death: Suspends your death in amber — auto-resurrect at 50% HP (once per hour)'}],
        'lore_text': 'A dying alchemist poured her last experiment over her own heart — a tincture that could arrest any process, even death. She didn\'t survive, but the moment of her dying was captured in amber, and that moment contains enough life to lend. The moth inside has been becoming a butterfly for three hundred years.',
        'drop_source': 'The Amber Chrysalis',
    },
    99012: {
        'vnum': 99012, 'name': 'Pupil of the Severed Witness',
        'short_desc': 'the Pupil of the Severed Witness',
        'room_desc': 'A crystalline eye on a copper chain watches everything with cold fascination.',
        'description': 'An eye carved from smoky quartz, its iris a spiral of copper wire that contracts and dilates in response to light. It sees through deception the way a surgeon sees through skin — clinically, completely, without mercy.',
        'item_type': 'armor', 'wear_slot': 'neck2', 'weight': 1, 'cost': 38000,
        'armor': 1, 'rarity': 'legendary',
        'affects': [{'type': 'wis', 'value': 4}, {'type': 'int', 'value': 2}],
        'procs': [{'type': 'on_equip', 'effect': 'detect_all', 'value': 1,
                   'desc': 'Equip: Detect hidden, invisible, and alignment — the Witness sees all'}],
        'lore_text': 'The Witness was an entity that existed only to observe — it had no body, no desires, only sight. When the gods decided some things should remain unseen, they severed its eye and buried it. The eye kept watching from underground. It has opinions about what it has seen, and it shares them as cold impressions behind your own eyelids.',
        'drop_source': 'The Severed Witness',
    },

    # ────────── 8 MORE LEGENDARIES ──────────
    99013: {
        'vnum': 99013, 'name': 'The Unraveling',
        'short_desc': 'the Unraveling, Dagger of Loose Threads',
        'room_desc': 'A dagger made of twisted thread and spite lies here, twitching.',
        'description': 'Not a blade at all — a dense weave of metallic threads compressed into the shape of a dagger. When it cuts, it doesn\'t sever — it pulls. Threads of reality come loose at its touch, and things begin to come undone.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 3, 'cost': 44000,
        'damage_dice': '2d8', 'weapon_type': 'stab', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'hitroll', 'value': 6}, {'type': 'damroll', 'value': 3}],
        'procs': [{'type': 'on_hit', 'effect': 'root_pierce', 'chance': 25, 'damage': 15,
                   'desc': 'Chance on hit: Unravels the target\'s defenses for 7-15 damage as their armor loosens'}],
        'lore_text': 'A weaver who could see the threads of fate grew tired of the pattern. She pulled one thread free and twisted it into a blade. Everything the blade touches begins to fray — armor loosens, wounds reopen, certainties dissolve. The weaver herself unraveled shortly after, leaving only this and a spool of something that screams when unwound.',
        'drop_source': 'The Frayed Weaver',
    },
    99014: {
        'vnum': 99014, 'name': 'Tidal Asylum',
        'short_desc': 'Tidal Asylum, Bulwark of the Drowned',
        'room_desc': 'A shield of compressed ocean water holds its shape through sheer pressure.',
        'description': 'This tower shield is a disc of ocean — actual ocean, compressed to the density of steel. Fish swim in its depths. Sometimes a face presses against the surface from inside, mouth open in a silent scream, before sinking back into the blue.',
        'item_type': 'armor', 'wear_slot': 'shield', 'weight': 15, 'cost': 50000,
        'armor': 15, 'rarity': 'legendary',
        'affects': [{'type': 'con', 'value': 3}, {'type': 'armor', 'value': -30}, {'type': 'hp', 'value': 25}],
        'procs': [{'type': 'on_defend', 'effect': 'damage_reflect', 'chance': 15,
                   'desc': 'When hit: 15% chance the ocean inside erupts, reflecting 25% damage as crushing pressure'}],
        'lore_text': 'A coastal fortress was swallowed by the sea during a siege. The ocean compressed everything inside it — stones, soldiers, screams — into a single flat disc. It serves as a shield now, but the soldiers inside are still fighting. When struck hard enough, their battle spills outward briefly, and the attacker finds themselves caught in a war that ended centuries ago.',
        'drop_source': 'The Sunken Castellan',
    },
    99015: {
        'vnum': 99015, 'name': 'Amnesia, Blade of Shed Histories',
        'short_desc': 'Amnesia, Blade of Shed Histories',
        'room_desc': 'A greatsword covered in fading inscriptions mourns here in silence.',
        'description': 'Names, dates, and histories are etched into every surface of this massive blade — but they\'re fading. As you watch, words blur and vanish, replaced by new ones that immediately begin to dissolve. The sword remembers everything, but only for a moment.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 16, 'cost': 58000,
        'damage_dice': '4d6', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 5}, {'type': 'hitroll', 'value': 4}, {'type': 'damroll', 'value': 6}],
        'procs': [{'type': 'on_hit', 'effect': 'memory_wound', 'chance': 8, 'damage': 40,
                   'desc': 'Chance on hit: Cuts through the target\'s history — old wounds reopen for 20-40 damage'},
                  {'type': 'on_kill', 'effect': 'restore_hp', 'percent': 15,
                   'desc': 'On kill: Absorbs the victim\'s final memory, restoring 15% max HP'}],
        'lore_text': 'Every kingdom that has ever fallen is recorded on this blade — and then forgotten. It is a chronicle that erases itself, a history book with dissolving ink. Those struck by it don\'t just take wounds — they remember wounds. Every injury they have ever suffered reopens simultaneously, and for one terrible moment, they experience a lifetime of pain at once.',
        'drop_source': 'The Amnesiac King',
    },
    99016: {
        'vnum': 99016, 'name': 'Pendulum of the Stopped Clock',
        'short_desc': 'Pendulum of the Stopped Clock',
        'room_desc': 'A massive clockwork warhammer ticks with irregular, broken time.',
        'description': 'The head of this warhammer is a clock face — but the numbers are wrong, the hands move backward, and it strikes thirteen. Gears grind inside it with the sound of time being chewed.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 18, 'cost': 53000,
        'damage_dice': '3d8', 'weapon_type': 'pound', 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 4}, {'type': 'con', 'value': 2}, {'type': 'hitroll', 'value': 5}, {'type': 'damroll', 'value': 5}],
        'procs': [{'type': 'on_hit', 'effect': 'clockwork_unwind', 'chance': 15, 'damage': 25,
                   'desc': 'Chance on hit: Unwinds the target\'s personal timeline for 12-25 damage'}],
        'lore_text': 'A clockmaker built a clock that kept perfect time — so perfect that time itself became jealous and stopped. The moment of stopping was captured in the pendulum. When it strikes, the target experiences temporal rejection — their body tries to exist in two moments at once, and neither moment wants them.',
        'drop_source': 'The Horologist\'s Remnant',
    },
    99017: {
        'vnum': 99017, 'name': 'Lacuna, the Absent Edge',
        'short_desc': 'Lacuna, the Absent Edge',
        'room_desc': 'A gap in the shape of a sword hangs in the air where a blade should be.',
        'description': 'There is no sword here. There is an absence of sword — a blade-shaped hole in reality where matter refuses to exist. The hilt is real enough, wrapped in leather from an animal that was never catalogued, but the blade is pure nothing.',
        'item_type': 'weapon', 'wear_slot': 'wield', 'weight': 5, 'cost': 46000,
        'damage_dice': '3d6', 'weapon_type': 'slash', 'rarity': 'legendary',
        'affects': [{'type': 'dex', 'value': 4}, {'type': 'hitroll', 'value': 7}, {'type': 'sneak', 'value': 15}],
        'procs': [{'type': 'on_hit', 'effect': 'void_cut', 'chance': 18, 'damage': 18,
                   'desc': 'Chance on hit: Cuts a hole in the target\'s existence for 9-18 void damage'}],
        'lore_text': 'A blacksmith attempted to forge a blade from nothing and succeeded. The result is a weapon that does not exist — it has no weight, no reflection, no sound. It cuts by removing, not by striking. Those wounded by Lacuna don\'t bleed — they simply have less. Less blood, less breath, less self.',
        'drop_source': 'The Voidsmiths\' Absence',
    },
    99018: {
        'vnum': 99018, 'name': 'Palms of the Root Network',
        'short_desc': 'the Palms of the Root Network',
        'room_desc': 'Gauntlets of living wood and tangled roots pulse with green veins.',
        'description': 'These gauntlets are grown, not forged — a lattice of living roots compressed into the shape of armored gloves. They pulse with a vegetative heartbeat, and tiny white flowers bloom and die in seconds along the knuckles.',
        'item_type': 'armor', 'wear_slot': 'hands', 'weight': 8, 'cost': 47000,
        'armor': 10, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 5}, {'type': 'damroll', 'value': 4}, {'type': 'armor', 'value': -20}],
        'procs': [{'type': 'on_equip', 'effect': 'damage_pct', 'value': 5,
                   'desc': 'Equip: +5% to all damage — your strikes carry the weight of ancient growth'}],
        'lore_text': 'Beneath every forest is a network — roots speaking to roots in a language older than sound. A druid who learned to listen heard the network scream: it was angry. It had been carrying the weight of every tree for millennia, and it wanted to hit something. She gave it hands.',
        'drop_source': 'The Mycorrhizal Titan',
    },
    99019: {
        'vnum': 99019, 'name': 'Girdle of Collapsed Frequencies',
        'short_desc': 'the Girdle of Collapsed Frequencies',
        'room_desc': 'A belt of woven radio static shimmers between states of matter.',
        'description': 'This sash is made from something between light and sound — collapsed frequencies that exist as a shimmering, humming fabric. Constellations of static drift across its surface, mapping signals from sources that may not exist in this reality.',
        'item_type': 'armor', 'wear_slot': 'waist', 'weight': 1, 'cost': 43000,
        'armor': 3, 'rarity': 'legendary',
        'affects': [{'type': 'int', 'value': 3}, {'type': 'wis', 'value': 3}, {'type': 'mana', 'value': 40}],
        'procs': [{'type': 'on_kill', 'effect': 'absorb_echo', 'percent': 8,
                   'desc': 'On kill: Absorbs the dying frequency — restore 8% max HP and mana'}],
        'lore_text': 'A mathematician proved that every living thing emits a unique frequency and that death is simply that frequency collapsing. She wove the collapsed frequencies of a thousand extinctions into a belt. It hums with the last songs of species no one remembers — each one a tiny, perfect requiem that restores the wearer\'s strength.',
        'drop_source': 'The Frequency Collector',
    },
    99020: {
        'vnum': 99020, 'name': 'Sutures of the Wound Between',
        'short_desc': 'the Sutures of the Wound Between',
        'room_desc': 'Vambraces of stitched reality hold the air together where it was torn.',
        'description': 'These wrist guards appear to be made of surgical sutures — but they\'re stitching together a wound in space itself. The air around them has visible seams, neatly closed with thread that exists in a color your eyes can\'t quite process.',
        'item_type': 'armor', 'wear_slot': 'wrist1', 'weight': 4, 'cost': 41000,
        'armor': 8, 'rarity': 'legendary',
        'affects': [{'type': 'str', 'value': 3}, {'type': 'dex', 'value': 2}, {'type': 'hitroll', 'value': 3}, {'type': 'armor', 'value': -15}],
        'procs': [{'type': 'on_equip', 'effect': 'damage_pct', 'value': 3,
                   'desc': 'Equip: +3% to all melee damage — your strikes tear at the seams of things'}],
        'lore_text': 'Reality tore once — a wound from horizon to horizon, bleeding light and wrong geometry. A surgeon who had stitched a thousand human wounds looked up and said, "I can fix that." She did. The leftover sutures became these vambraces. They remember how to hold things together, and more importantly, how to pull them apart.',
        'drop_source': 'The Cosmo-Surgeon',
    },
}


# ═══════════════════════════════════════════════════════════════
# BOSS → LEGENDARY DROP TABLE
# ═══════════════════════════════════════════════════════════════

# Each legendary drops from one real boss of fitting level (its vnum), at its chance per kill.
# Any other boss of level 40 or more has a 1% chance at a random one.
LEGENDARY_BOSSES = {
    99001: (5200, 'the mighty beholder', 4),
    99002: (9772, 'the Carillon Engine', 4),
    99003: (16025, 'Kaleidos the Prismatic Dragon', 3),
    99004: (22072, 'Famine', 4),
    99005: (9716, 'Vaelith the Star-Eater', 4),
    99006: (9786, 'the Faceless One', 4),
    99007: (9702, 'the Cinder Smith', 4),
    99008: (9742, 'the Roc Matriarch', 4),
    99009: (9756, 'Morvane the Eclipsed', 4),
    99010: (9712, 'the Echo of the Archmage', 3),
    99011: (9766, "Xal'thar the First Lich", 3),
    99012: (9736, 'Auditor Mordessa', 5),
    99013: (14030, 'Verdraxx the Green Dragon', 4),
    99014: (9706, 'Gorrund the Siegebreaker', 4),
    99015: (9776, 'the Mute King', 3),
    99016: (9732, 'the Keeper of Keys', 4),
    99017: (9762, 'the Soulbinder', 4),
    99018: (27010, 'the Oakfather', 5),
    99019: (9722, 'the Gilded Hierophant', 5),
    99020: (9726, 'Serathiel the Fallen', 4),
}
BOSS_LEGENDARY_DROPS = {boss: (vnum, chance) for vnum, (boss, _, chance) in LEGENDARY_BOSSES.items()}
for _v, (_boss, _name, _chance) in LEGENDARY_BOSSES.items():
    LEGENDARY_ITEMS[_v]['drop_source'] = _name[0].upper() + _name[1:]


def get_legendary_drop_for_boss(mob) -> Optional[int]:
    """A legendary a boss drops this time (its own at its chance), or None."""
    if not (getattr(mob, 'is_boss', False) or 'boss' in (getattr(mob, 'flags', None) or ())):
        return None
    own = BOSS_LEGENDARY_DROPS.get(getattr(mob, 'vnum', None))
    if own:
        vnum, chance = own
        return vnum if random.randint(1, 100) <= chance else None
    if (getattr(mob, 'level', 0) or 0) >= 40 and random.randint(1, 100) <= 1:
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
    
    desc = getattr(item, 'description', '')
    if desc:
        lines.append(f"{c['white']}  {desc}{c['reset']}")
        lines.append("")
    
    if getattr(item, 'item_type', '') == 'weapon':
        lines.append(f"{c['yellow']}  Damage: {item.damage_dice} ({item.weapon_type}){c['reset']}")
    if getattr(item, 'item_type', '') == 'armor' and getattr(item, 'armor', 0):
        lines.append(f"{c['yellow']}  Armor: {item.armor}{c['reset']}")
    if getattr(item, 'wear_slot', None):
        lines.append(f"{c['yellow']}  Slot: {item.wear_slot}{c['reset']}")
    
    affects = getattr(item, 'affects', [])
    if affects:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        for aff in affects:
            if isinstance(aff, dict):
                lines.append(f"{c['bright_magenta']}  Affects {aff.get('type', '?')}: {aff.get('value', 0):+d}{c['reset']}")
    
    import procs
    extra = procs.item_lines(item)
    if extra:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        for text in extra:
            lines.append(f"{c['bright_yellow']}  {'⚡ ' if not text.startswith(('Set:', '  ')) else ''}{text}{c['reset']}")
    
    lore = getattr(item, 'lore_text', '')
    if lore:
        lines.append(f"{c['bright_cyan']}{'─' * 55}{c['reset']}")
        lines.append(f"{c['bright_black']}  \"{lore}\"{c['reset']}")
    
    source = getattr(item, 'drop_source', '')
    if source:
        lines.append(f"{c['white']}  Drops from: {c['bright_red']}{source}{c['reset']}")
    
    lines.append(f"{c['white']}  Weight: {getattr(item, 'weight', 0)}  Value: {getattr(item, 'cost', 0)} gold{c['reset']}")
    lines.append(f"{c['bright_cyan']}{'═' * 55}{c['reset']}")
    
    return lines
