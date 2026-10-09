"""Structured combat events for the graphical (3D) client.

Every swing, hit, miss, defence, cast, heal, death and wind-up is also emitted as a small
JSON event from the same code that prints its combat-log line, so the client can animate
exactly what the log says. Events emitted during one moment are batched per room and sent
on the map socket as {"type": "combat_events", "room": vnum, "events": [...]} to the web
clients of everyone standing in that room. Telnet players are unaffected.

Event shape (all fields optional except k):
  k       attack | ability | spell | heal | buff | debuff | windup | resolve | death | stun | oor
  src/dst {"p": player name} or {"m": mob uid}
  res     hit | crit | miss | dodge | parry | block | resist | immune
  amt     damage or healing amount
  ability / spell, school (fire, frost, lightning, arcane, holy, shadow, necrotic, nature,
  poison, sound, physical, blood), ranged (bool), area {shape, r, angle, x, z}, ms (wind-up)
"""
import asyncio
import logging

logger = logging.getLogger('Misthollow')

_pending = {}        # room vnum -> (room, [events])
_scheduled = False
_hold = 0            # >0 while an action (a round, a skill) is still producing events


class hold:
    """`with hold():` keeps this moment's events together until the action finishes, so a
    swing and its wounds leave in one message even though the round awaits in between."""
    def __enter__(self):
        global _hold
        _hold += 1

    def __exit__(self, *exc):
        global _hold
        _hold = max(0, _hold - 1)
        return False


def ref(ch):
    """How a combatant is named in an event."""
    if ch is None:
        return None
    if hasattr(ch, 'account_name') or getattr(ch, 'is_player', False):
        return {'p': getattr(ch, 'name', '?')}
    try:
        from map_system import _mob_uid
        return {'m': _mob_uid(ch)}
    except Exception:
        return {'m': id(ch) & 0x7fffffff}


def mark(room):
    """Where the next event for `room` will go: lets a wrapper put an action ahead of the
    wounds it caused (the swing before its damage numbers)."""
    entry = _pending.get(getattr(room, 'vnum', None))
    return len(entry[1]) if entry else 0


def emit_at(room, index, k, src=None, dst=None, **fields):
    """emit(), but inserted at `index` (from mark()) instead of appended."""
    emit(room, k, src, dst, **fields)
    entry = _pending.get(getattr(room, 'vnum', None))
    if entry and index is not None and index < len(entry[1]) - 1:
        entry[1].insert(index, entry[1].pop())


def emit(room, k, src=None, dst=None, **fields):
    """Queue one event for the web clients in `room` (sent at the end of this tick)."""
    global _scheduled
    if room is None:
        return
    ev = {'k': k}
    if src is not None:
        ev['src'] = ref(src)
    if dst is not None:
        ev['dst'] = ref(dst)
    for key, value in fields.items():
        if value is not None:
            ev[key] = value
    vnum = getattr(room, 'vnum', None)
    if vnum is None:
        return
    entry = _pending.get(vnum)
    if entry is None:
        entry = _pending[vnum] = (room, [])
    entry[1].append(ev)
    if not _scheduled:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        _scheduled = True
        loop.call_soon(lambda: asyncio.ensure_future(_flush()))


async def _flush():
    global _scheduled
    for _ in range(150):               # an action is mid-way: wait for the rest of it (<=3 s)
        if _hold <= 0:
            break
        await asyncio.sleep(0.02)
    _scheduled = False
    batch = list(_pending.items())
    _pending.clear()
    for vnum, (room, events) in batch:
        world = None
        for ch in getattr(room, 'characters', []) or []:
            world = getattr(ch, 'world', None)
            if world:
                break
        wm = getattr(world, 'web_map', None) if world else None
        if not wm or not events:
            continue
        try:
            await wm.send_room_event(room, {'type': 'combat_events', 'room': vnum, 'events': events})
        except Exception as e:
            logger.debug(f"combat_events flush failed: {e}")


def result_of(text):
    """Map a combat-log line's outcome word to an event result (for call sites that only
    have the message)."""
    t = (text or '').lower()
    for word, res in (('parr', 'parry'), ('dodge', 'dodge'), ('block', 'block'), ('sidestep', 'dodge'),
                      ('miss', 'miss'), ('resist', 'resist'), ('immune', 'immune')):
        if word in t:
            return res
    return 'hit'
