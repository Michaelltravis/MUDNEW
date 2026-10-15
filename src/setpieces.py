"""Landmark and boss rooms laid out by hand (Phase 5 of docs/world/room_visuals.md).

A room in world/setpieces.json has its things placed where its maker put them (each feature with
an x, y on the room's grid: shared/roomgen.js places them so, facing the room's middle) in place of
what room_features.py reads from its words, and its own light (terrain.js: a point light of that
colour over the room). Read at load (World.load -> annotate), after the features.
"""
import json
import logging
import os

logger = logging.getLogger('Misthollow')
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'world', 'setpieces.json')


def load(path=PATH):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh).get('rooms') or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning(f'setpieces.json unreadable: {e}')
        return {}


def annotate(world, pieces=None):
    """Lay out the set-piece rooms (room.features with positions, room.setpiece); returns how many."""
    pieces = load() if pieces is None else pieces
    n = 0
    for vnum, sp in pieces.items():
        room = world.rooms.get(int(vnum)) if str(vnum).isdigit() else None
        if room is None:
            continue
        room.features = [dict(f, n=1) for f in sp.get('layout') or []]
        room.setpiece = {k: sp[k] for k in ('light',) if sp.get(k)} or None
        n += 1
    return n
