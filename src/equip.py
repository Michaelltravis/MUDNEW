"""Where a thing can be worn, and finding what you mean (commands.py wear/wield/hold/remove, the
/play inventory's drag and drop: world3d/hud/inventory.js mirrors slots_for).

A ring goes on either finger whatever its data says (many say "finger1"), an amulet on either
neck slot, a bracer on either wrist. A weapon is wielded, or held in the off hand when the
wielder can fight with two and it is light. "2.ring" is the second ring; a slot's name
("finger2") names what is worn there.
"""
import re

from objects import infer_wear_slot

PAIRS = {'finger': ['finger1', 'finger2'], 'neck': ['neck1', 'neck2'], 'wrist': ['wrist1', 'wrist2']}
# words a player may use for a slot
SLOT_WORDS = {'left': 'finger1', 'right': 'finger2', 'lfinger': 'finger1', 'rfinger': 'finger2',
              'offhand': 'dual_wield', 'off-hand': 'dual_wield', 'mainhand': 'wield'}
NOT_WORN = ('weapon', 'food', 'drink', 'potion', 'scroll', 'wand', 'staff', 'pill', 'container',
            'key', 'trash', 'fountain')
OFFHAND_RE = re.compile(r'dagger|knife|stiletto|short ?sword|dirk|kris|tanto', re.I)


def slot_kind(slot) -> str:
    """finger1 -> finger; a slot that is not one of a pair is its own kind."""
    s = str(slot or '')
    base = s.rstrip('12')
    return base if base in PAIRS else s


def all_slots():
    from config import Config
    return list(dict.fromkeys(list(Config.WEAR_SLOTS) + ['wield', 'dual_wield', 'hold', 'light', 'shield']))


def slot_word(word):
    """A word that names a slot ('finger2', 'right', 'offhand'), as the slot, else None."""
    w = str(word or '').lower()
    w = SLOT_WORDS.get(w, w)
    return w if w in all_slots() else None


def can_offhand(player, item) -> bool:
    if 'dual_wield' not in (getattr(player, 'skills', None) or {}):
        return False
    text = f"{getattr(item, 'name', '')} {getattr(item, 'short_desc', '')}"
    return getattr(item, 'weapon_type', '') in ('pierce', 'stab') or bool(OFFHAND_RE.search(text))


def slots_for(player, item) -> list:
    """Every slot `item` may go in, for this player, best first."""
    itype = getattr(item, 'item_type', '') or ''
    if itype == 'weapon':
        return ['wield'] + (['dual_wield'] if can_offhand(player, item) else [])
    named = getattr(item, 'wear_slot', None)
    if itype == 'light' and (not named or named in ('light', 'hold')):
        return ['light']      # a glowing ring that says "finger" is still a ring
    if itype in ('wand', 'staff') and not named:
        return ['hold']
    if itype in NOT_WORN and not named:
        return []
    slot = infer_wear_slot(item)
    if not slot:
        return []
    kind = slot_kind(slot)
    if kind in PAIRS:
        return list(PAIRS[kind])
    return [slot]


def _parse_n(name):
    name = str(name or '').strip().lower()
    if '.' in name and name.split('.', 1)[0].isdigit():
        n, rest = name.split('.', 1)
        return int(n), rest
    return 1, name


def _match(items, name):
    """The nth of `items` by "n.word": a whole word of its keywords first, else part of one."""
    n, word = _parse_n(name)
    words = [it for it in items if word in str(getattr(it, 'name', '') or '').lower().split()]
    found = words or [it for it in items if word in str(getattr(it, 'name', '') or '').lower()]
    return found[n - 1] if 0 < n <= len(found) else None


def find_carried(player, name):
    """What the player carries by `name` ("sword", "2.ring")."""
    return _match(list(getattr(player, 'inventory', None) or []), name)


def find_worn(player, name):
    """(slot, item) the player wears by a slot's name ("finger2") or the item's ("2.ring")."""
    eq = getattr(player, 'equipment', None) or {}
    slot = slot_word(name)
    if slot and eq.get(slot):
        return slot, eq[slot]
    order = {s: i for i, s in enumerate(all_slots())}
    worn = sorted(((s, it) for s, it in eq.items() if it), key=lambda p: order.get(p[0], 99))   # finger1 before finger2
    item = _match([it for _, it in worn], name)
    if item is None:
        return None, None
    return next((s for s, it in worn if it is item), None), item


def free_slot(player, item):
    """The first empty slot `item` may go in, or None."""
    eq = getattr(player, 'equipment', None) or {}
    return next((s for s in slots_for(player, item) if not eq.get(s)), None)
