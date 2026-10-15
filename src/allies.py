"""Creatures that come to each other's aid (a zone's population: world/population, a creature's
`helpers`: {"group": "castle", "rooms": 2, "count": 3}). When a player attacks one, others of
its group within `rooms` steps who are free rush in and join the fight (a boss's call_guards
works the same way: boss_mechanics.py). One whose helpers say "answer": false calls for help
but never comes (a shopkeeper calls the watch; the watch comes).
"""


def _group(mob):
    h = getattr(mob, 'helpers', None) or {}
    return h.get('group') if isinstance(h, dict) else None


def nearby_allies(mob, rooms=2, want=3):
    """Free creatures of mob's group, nearest first: [(creature, room it is in)]."""
    group, room = _group(mob), mob.room
    if not group or room is None:
        return []
    out, seen, frontier = [], {room.vnum}, [room]
    for _ in range(rooms):
        nxt = []
        for r in frontier:
            for ex in (r.exits or {}).values():
                to = ex.get('room') if isinstance(ex, dict) else None
                if to is None or to.vnum in seen or to.zone is not room.zone:
                    continue
                door = ex.get('door')
                if isinstance(door, dict) and door.get('state') == 'closed':
                    continue               # a shut door keeps help out
                seen.add(to.vnum)
                nxt.append(to)
                for m in to.characters:
                    if len(out) >= want:
                        return out
                    if m is mob or hasattr(m, 'connection') or getattr(m, 'fighting', None) or getattr(m, 'hp', 0) <= 0:
                        continue
                    if _group(m) == group and (m.helpers or {}).get('answer', True):
                        out.append((m, to))
        frontier = nxt
    return out


async def rally(mob, attacker):
    import reach
    if reach.pulled(mob):
        return []          # struck from the next room (reach.py): only the one aimed at comes
    h = getattr(mob, 'helpers', None) or {}
    came = nearby_allies(mob, int(h.get('rooms', 2)), int(h.get('count', 2)))
    if not came:
        return []
    room = mob.room
    await room.send_to_room(h.get('shout') or f"{mob.name} cries out for help!")
    for m, frm in came:
        frm.characters.remove(m)
        m.room = room
        room.characters.append(m)
        await room.send_to_room(f"{m.name} rushes in to help {mob.name}!")
        m.fighting, m.position = attacker, 'fighting'
        try:
            await m._notify_move(frm, room, 'somewhere', 'somewhere')
        except Exception:
            pass
    return [m for m, _ in came]
