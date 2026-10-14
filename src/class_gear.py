"""What each class may wear and wield, D&D style: the heaviest armour it is trained in, whether it
takes a shield, and the kinds of weapon it knows (commands.py wear/wield/hold, gearup, login).

Armour weight is gear_look's: 0 cloth, 1 leather, 2 mail, 3 plate. A head piece weighs what it
looks like: a helm is mail, a horned or fur helm leather, a hat, hood, circlet or mask cloth.
Gloves, boots and bracers count only when metal (gauntlets, sabatons, vambraces): anyone may
wear leather ones.
Weapon kinds are gear_look's too; "sword1" is a one-handed sword only (a rapier, not a
greatsword). Every player is held to it, immortals too (their characters should look the part);
creatures are not.

    mage, necromancer   cloth; staff, wand, dagger, darts (a necromancer a scythe too)
    thief, assassin     leather; daggers, one-handed swords, clubs, whips, bows and crossbows
    bard                leather; rapiers, daggers, staves, whips, crossbows, instruments
    ranger              up to mail and a shield; any martial weapon but a scythe
    cleric              up to mail and a shield; maces, hammers, staves and wands
    warrior, paladin    any armour and a shield; any weapon but a wand
"""
import re

import gear_look

ARMOUR_NAMES = ['cloth', 'leather', 'mail', 'plate']
# the slots whose weight counts
ARMOUR_SLOTS = ('body', 'arms', 'legs', 'hands', 'feet', 'head')
LIGHT_SLOTS = ('arms', 'hands', 'feet')       # only metal counts here

ALL_WEAPONS = {'sword', 'axe', 'dagger', 'mace', 'hammer', 'spear', 'polearm', 'scythe', 'pick',
               'claw', 'whip', 'staff', 'wand', 'crossbow', 'bow', 'thrown', 'instrument'}
_ROGUE = {'dagger', 'sword1', 'mace', 'whip', 'claw', 'thrown', 'bow', 'crossbow'}

RULES = {
    'mage': {'armour': 0, 'shield': False, 'weapons': {'staff', 'wand', 'dagger', 'thrown'}},
    'necromancer': {'armour': 0, 'shield': False, 'weapons': {'staff', 'wand', 'dagger', 'thrown', 'scythe'}},
    'thief': {'armour': 1, 'shield': False, 'weapons': set(_ROGUE)},
    'assassin': {'armour': 1, 'shield': False, 'weapons': set(_ROGUE)},
    'bard': {'armour': 1, 'shield': False, 'weapons': {'sword1', 'dagger', 'staff', 'whip', 'thrown', 'crossbow', 'instrument', 'mace'}},
    'ranger': {'armour': 2, 'shield': True, 'weapons': ALL_WEAPONS - {'wand', 'instrument', 'scythe'}},
    'cleric': {'armour': 2, 'shield': True, 'weapons': {'mace', 'hammer', 'staff', 'wand'}},
    'warrior': {'armour': 3, 'shield': True, 'weapons': ALL_WEAPONS - {'wand', 'instrument'}},
    'paladin': {'armour': 3, 'shield': True, 'weapons': ALL_WEAPONS - {'wand', 'instrument'}},
}
# the weapon each class is drawn with, first choice first (gearup, a legendary for the class)
PREFERRED = {'mage': ['staff', 'wand'], 'necromancer': ['scythe', 'staff', 'wand'], 'thief': ['dagger', 'sword1'],
             'assassin': ['dagger', 'sword1'], 'bard': ['sword1', 'instrument'], 'ranger': ['bow', 'crossbow', 'sword'],
             'cleric': ['mace', 'hammer'], 'warrior': ['sword', 'axe'], 'paladin': ['sword', 'hammer', 'mace']}
WEAPON_WORDS = {'sword': 'swords', 'sword1': 'one-handed swords', 'axe': 'axes', 'dagger': 'daggers', 'mace': 'maces and clubs',
                'hammer': 'hammers', 'spear': 'spears', 'polearm': 'polearms', 'scythe': 'scythes', 'pick': 'picks',
                'claw': 'claws', 'whip': 'whips', 'staff': 'staves', 'wand': 'wands', 'crossbow': 'crossbows',
                'bow': 'bows', 'thrown': 'darts and throwing weapons', 'instrument': 'instruments'}
HEAD_WEIGHT = {'helm': 2, 'horned': 1, 'crown': 0, 'hat': 0, 'hood': 0, 'mask': 0}


def rules_for(ch):
    return RULES.get(str(getattr(ch, 'char_class', '') or '').lower())


def gear_key(item, slot=None):
    """What the rules look at: ('weapon', kind, hands), ('shield',), ('armour', weight), or None."""
    itype = getattr(item, 'item_type', '') or ''
    if itype == 'weapon':
        p = gear_look.weapon_piece(item)
        return ('weapon', p['k'], p.get('h', 1))
    if slot is None:
        from objects import infer_wear_slot
        slot = getattr(item, 'wear_slot', None) or infer_wear_slot(item)
    if slot == 'shield':
        return ('shield',)
    if slot == 'head':
        kind = gear_look.head_piece(item)['k']
        w = HEAD_WEIGHT.get(kind, 0)
        if w >= 2 and re.search(r'\b(?:leather|hide|fur|cloth|silk)\b', gear_look._text(item)):
            w = 1
        return ('armour', w)
    if slot in ARMOUR_SLOTS and itype in ('armor', 'worn', 'treasure'):
        w = gear_look.armour_piece(item)['w']
        # gloves, boots and bracers are not armour in D&D unless they are metal (gauntlets, sabatons)
        if slot in LIGHT_SLOTS and w == 1:
            w = 0
        return ('armour', w)
    return None


def preference(ch, item):
    """How well a weapon suits the class's look: higher is better (0 when it is none of its favourites)."""
    if getattr(item, 'item_type', '') != 'weapon':
        return 0
    p = gear_look.weapon_piece(item)
    prefs = PREFERRED.get(str(getattr(ch, 'char_class', '') or '').lower(), [])
    for i, k in enumerate(prefs):
        if p['k'] == k or (k == 'sword1' and p['k'] == 'sword' and p.get('h', 1) == 1):
            return len(prefs) - i
    return 0


def set_for_others(ch, item) -> bool:
    """A piece of a named set made for other classes (sets.py "classes")."""
    sid = getattr(item, 'set_id', None)
    if not sid:
        return False
    try:
        from sets import NAMED_SETS
    except Exception:
        return False
    classes = (NAMED_SETS.get(sid) or {}).get('classes')
    return bool(classes) and str(getattr(ch, 'char_class', '')).lower() not in classes


def suits(ch, item, slot=None) -> int:
    """How well a piece suits the class's look, for choosing gear (gearup): its favourite weapons,
    armour of the weight it is trained in (a warrior's plate, a mage's robes), and not another
    class's set. Higher is better."""
    if set_for_others(ch, item):
        return -10
    rules = rules_for(ch)
    key = gear_key(item, slot)
    if not rules or not key:
        return 0
    if key[0] == 'weapon':
        return preference(ch, item)
    if key[0] == 'armour':
        if (slot or getattr(item, 'wear_slot', None)) == 'head' and gear_look.head_piece(item)['k'] == 'crown':
            return 0                      # a crown or circlet suits anyone
        return -abs(rules['armour'] - key[1])
    return 0


def weapon_ok(rules, kind, hands):
    ws = rules['weapons']
    return kind in ws or (kind == 'sword' and hands == 1 and 'sword1' in ws)


def refusal(ch, item, slot=None):
    """Why `ch` may not wear or wield `item` (a sentence), or None when they may."""
    if getattr(ch, 'is_npc', False) or not hasattr(ch, 'char_class'):
        return None
    rules = rules_for(ch)
    if not rules:
        return None
    key = gear_key(item, slot)
    if not key:
        return None
    cls = str(ch.char_class).lower()
    what = getattr(item, 'short_desc', None) or 'that'
    if key[0] == 'weapon':
        if weapon_ok(rules, key[1], key[2]):
            return None
        kind = 'two-handed sword' if key[1] == 'sword' and key[2] == 2 else key[1]
        return f"A {cls} isn't trained with a {kind}: {what} is not for you. ({allowed_text(ch)})"
    if key[0] == 'shield':
        return None if rules['shield'] else f"A {cls} doesn't fight behind a shield. ({allowed_text(ch)})"
    if key[1] > rules['armour']:
        return (f"{what[0].upper() + what[1:]} is {ARMOUR_NAMES[key[1]]}; a {cls} is trained in "
                f"{ARMOUR_NAMES[rules['armour']]} at most. ({allowed_text(ch)})")
    return None


def allows(ch, item, slot=None) -> bool:
    return refusal(ch, item, slot) is None


def allowed_text(ch):
    rules = rules_for(ch)
    if not rules:
        return 'anything'
    words = [WEAPON_WORDS[w] for w in sorted(rules['weapons'])]
    armour = ' armour' if rules['armour'] else ''
    return (f"{ARMOUR_NAMES[rules['armour']]}{armour}{' and a shield' if rules['shield'] else ''}; "
            f"{', '.join(words)}")


def for_client(ch):
    """The rules, for the /play inventory to grey out what the class can't use."""
    rules = rules_for(ch)
    if not rules:
        return None
    return {'armour': rules['armour'], 'shield': rules['shield'], 'weapons': sorted(rules['weapons'])}


def client_key(item, slot=None):
    """gear_key, compact for the item payload: 'w:sword:2', 's', 'a:3'."""
    try:
        key = gear_key(item, slot)
    except Exception:
        return None
    if not key:
        return None
    return 'w:%s:%d' % (key[1], key[2]) if key[0] == 'weapon' else 's' if key[0] == 'shield' else 'a:%d' % key[1]


async def shed(ch):
    """Take off what the class can't use (an older character, a rule that changed); returns the items."""
    out = []
    eq = getattr(ch, 'equipment', None) or {}
    for slot, item in list(eq.items()):
        if item is None or slot in ('light', 'hold') and getattr(item, 'item_type', '') != 'weapon':
            continue
        why = refusal(ch, item, slot)
        if why:
            eq[slot] = None
            ch.inventory.append(item)
            out.append(item)
    if out and hasattr(ch, 'send'):
        names = ', '.join(i.short_desc for i in out)
        await ch.send(f"You put away what your training doesn't cover: {names}. "
                      f"A {ch.char_class} wears {allowed_text(ch)}.")
    return out
