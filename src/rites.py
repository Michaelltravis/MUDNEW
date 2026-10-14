"""Rites of passage (world/rites.json): the ways a place makes you earn the way on.

- **gates**: a door locked by a key that its gatekeeper carries. Kill the keeper, take the key, and
  the key opens that one door and crumbles in the lock. The door is warded: no pick, no bash, no
  spell breaks it. The zone's reset locks it again and the keeper comes back with a fresh key.
- **tolls**: a ferryman, a bridge-keeper or a gate-warden who takes you across for a fare. You talk
  to them (`talk charon`, or the Talk window), pay (`pay charon`, `give 1 gold charon`, `give coin
  charon`) and they carry you: the crossing room for a few moments, then the far side. They will
  not fight and cannot be fought.
- **keys**: the keys the gates use, made here so a zone needs no item file of its own.

Applied at world load after population.py and before doors.normalize (so a gate's locked state is
the state its zone resets to).

    {"keys":  {"bone-key": {"vnum": 790001, "keywords": "...", "short_desc": "...", "description": "..."}},
     "gates": [{"room": 3741, "dir": "north", "key": "bone-key", "keeper": 649510}],
     "tolls": [{"id": "styx", "npc": 649505, "room": 3772, "fare": 1, "via": 3773, "to": 3774, "secs": 6, ...}]}
"""
import asyncio
import json
import logging
import os

logger = logging.getLogger('Misthollow.Rites')

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FILE = os.path.join(ROOT, 'world', 'rites.json')

DATA = {'keys': {}, 'gates': [], 'tolls': []}
TOLLS = {}            # npc vnum -> toll
KEY_VNUMS = set()     # every gate key (they crumble when used)
CROSSING = set()      # players mid-crossing


def load(path=FILE):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def key_proto(kid, k):
    return {'vnum': int(k['vnum']), 'name': ' '.join(str(k.get('keywords') or kid).split()),
            'short_desc': k['short_desc'], 'description': k.get('room_desc') or f"{k['short_desc'][0].upper()}{k['short_desc'][1:]} lies here.",
            'long_desc': k.get('description', ''), 'action_desc': '', 'item_type': 'key', 'type': 'key',
            'extra_flags': ['crumbles'], 'wear_flags': ['take'], 'weight': 1, 'value': 1, 'cost': 1,
            'level': int(k.get('level', 1)), 'gate_key': True}


def apply(world, data=None):
    """Make the keys, lock the gates (and hand each keeper its key), seat the toll-keepers."""
    global DATA
    data = data if data is not None else load()
    DATA = {'keys': data.get('keys') or {}, 'gates': data.get('gates') or [], 'tolls': data.get('tolls') or []}
    problems = []
    vnum_of = {}
    for kid, k in DATA['keys'].items():
        proto = key_proto(kid, k)
        world.obj_prototypes[proto['vnum']] = proto
        vnum_of[kid] = proto['vnum']
        KEY_VNUMS.add(proto['vnum'])
    for g in DATA['gates']:
        room = world.rooms.get(int(g['room']))
        ex = (getattr(room, 'exits', None) or {}).get(g['dir']) if room else None
        if not isinstance(ex, dict) or not ex.get('door'):
            problems.append(f"gate {g['room']} {g['dir']}: no door there")
            continue
        kv = vnum_of.get(g.get('key'))
        if kv is None:
            problems.append(f"gate {g['room']} {g['dir']}: no key {g.get('key')!r}")
            continue
        door = ex['door']
        door.update(state='closed', locked=True, key_vnum=kv, pickproof=True, warded=True)
        if g.get('name'):
            door['name'] = g['name']
        to = world.rooms.get(ex.get('to_room'))
        back = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}.get(g['dir'])
        far = ((getattr(to, 'exits', None) or {}).get(back) or {}) if to else {}
        if isinstance(far, dict) and far.get('door'):
            far['door'].update(state='closed', locked=True, key_vnum=kv, pickproof=True, warded=True)
            if g.get('name'):
                far['door']['name'] = g['name']
        spec = g.get('keeper')
        if isinstance(spec, dict):
            keeper = make_keeper(world, spec, problems)
        else:
            keeper = world.mob_prototypes.get(int(spec)) if spec is not None else None
        if keeper is None:
            problems.append(f"gate {g['room']} {g['dir']}: no keeper {spec}")
            continue
        inv = keeper.setdefault('inventory', [])
        if kv not in [i['vnum'] if isinstance(i, dict) else i for i in inv]:
            inv.append(kv)
        keeper.setdefault('gate_keys', []).append(kv)
    for t in DATA['tolls']:
        if isinstance(t.get('make'), dict):
            # a toll-keeper made here (a bargeman at a quay): a plain proto, standing in its room
            m = t['make']
            world.mob_prototypes[int(t['npc'])] = {
                'vnum': int(t['npc']), 'name': ' '.join(str(m['keywords']).split()), 'short_desc': m['short_desc'],
                'long_desc': m['long_desc'], 'description': m.get('description', ''), 'level': int(m.get('level', 10)),
                'alignment': 0, 'flags': ['sentinel', 'no_attack'], 'hp_dice': '10d10+100', 'damage_dice': '1d4',
                'armor_class': 50, 'exp': 0, 'gold': 0, 'inventory': []}
            room = world.rooms.get(int(t['room']))
            if room is not None:
                room.mob_resets = list(room.mob_resets or []) + [{'vnum': int(t['npc']), 'max': 1}]
        # the way a body cannot walk (the Styx): barred, the ferryman's words on the bar
        for bar in t.get('bars') or []:
            room = world.rooms.get(int(bar['room']))
            ex = (getattr(room, 'exits', None) or {}).get(bar['dir']) if room else None
            if not isinstance(ex, dict):
                problems.append(f"toll {t.get('id')}: no way {bar['room']} {bar['dir']} to bar")
                continue
            ex['_unsealed_door'] = ex.get('door')        # never saved: the bar is made at load
            ex['door'] = {'name': bar.get('name', 'crossing'), 'state': 'closed', 'locked': True, 'pickproof': True,
                          'crossing': bar.get('say') or 'There is no way across but the ferry.'}
        npc = world.mob_prototypes.get(int(t['npc']))
        if npc is None:
            problems.append(f"toll {t.get('id')}: no npc {t['npc']}")
            continue
        flags = [f for f in (npc.get('flags') or []) if f not in ('aggressive', 'wimpy')]
        for f in ('sentinel', 'no_attack'):
            if f not in flags:
                flags.append(f)
        npc['flags'] = flags
        npc['aggressive'] = False
        npc.pop('rank', None)
        npc.pop('helpers', None)
        TOLLS[int(t['npc'])] = t
        _dialogue(t)
    for p in problems:
        logger.warning(f'rites: {p}')
    return problems


def make_keeper(world, spec, problems):
    """A gatekeeper made for its door: a named, sub-boss copy of one of the zone's own creatures
    ({"from": vnum, "vnum": new, "keywords", "short_desc", "long_desc", "description"?, "level"?,
    "room": where it stands}), standing in that room and nowhere else."""
    import copy
    import population
    src = world.mob_prototypes.get(int(spec['from']))
    room = world.rooms.get(int(spec['room']))
    if src is None or room is None:
        problems.append(f"keeper {spec.get('vnum')}: no creature {spec.get('from')} or room {spec.get('room')}")
        return None
    p = copy.deepcopy(src)
    if spec.get('level'):
        p['level'] = int(spec['level'])
    p.update(population.ranked(p, 'sub-boss'))
    p.update(vnum=int(spec['vnum']), name=' '.join(str(spec['keywords']).split()), short_desc=spec['short_desc'],
             long_desc=spec['long_desc'], rank='sub-boss', inventory=[])
    if spec.get('description'):
        p['description'] = spec['description']
    p['flags'] = [f for f in (p.get('flags') or []) if f not in ('boss', 'wimpy', 'helper')] + \
        [f for f in ('aggressive', 'sentinel') if f not in (p.get('flags') or [])]
    p.pop('special', None)
    world.mob_prototypes[p['vnum']] = p
    room.mob_resets = list(room.mob_resets or []) + [{'vnum': p['vnum'], 'max': 1}]
    return p


# ---------------------------------------------------------------- tolls

def _dialogue(t):
    """The toll-keeper's words as a dialogue tree (quests.DIALOGUE_TREES): greet, the fare, a
    refusal for those who cannot pay."""
    try:
        from quests import DIALOGUE_TREES, DialogueNode, DialogueChoice
    except Exception:
        return
    fare = int(t.get('fare', 1))
    coin = 'coin' if fare == 1 else 'coins'
    say = t.get('say') or {}
    DIALOGUE_TREES[int(t['npc'])] = {
        'start': DialogueNode(text=say.get('greet', f"'The fare is {fare} gold {coin}.'"), choices=[
            DialogueChoice(text=say.get('pay', f"Pay the fare ({fare} gold {coin})."), next_node='start',
                           effects=[{'type': 'toll', 'npc': int(t['npc'])}]),
            DialogueChoice(text=say.get('ask', 'What lies on the other side?'), next_node='lore'),
            DialogueChoice(text=say.get('leave', 'Not today.'), next_node='bye'),
        ]),
        'lore': DialogueNode(text=say.get('lore', "'Only what you go to find.'"), choices=[
            DialogueChoice(text=say.get('pay', f"Pay the fare ({fare} gold {coin})."), next_node='start',
                           effects=[{'type': 'toll', 'npc': int(t['npc'])}]),
            DialogueChoice(text=say.get('leave', 'Not today.'), next_node='bye'),
        ]),
        'bye': DialogueNode(text=say.get('bye', "'Then wait.'"), end=True),
    }


def toll_for(npc):
    return TOLLS.get(getattr(npc, 'vnum', None))


def fare_of(t):
    return int(t.get('fare', 1))


async def pay(player, npc, gold=None, item=None):
    """`pay <npc>`, `give <n> gold <npc>`, `give coin <npc>`, or the dialogue's fare choice. True
    when the toll-keeper took the fare (the player is then carried across)."""
    t = toll_for(npc)
    if not t:
        return False
    c = player.config.COLORS
    say = t.get('say') or {}
    fare = fare_of(t)
    if player in CROSSING:
        await player.send(f"{c['yellow']}You are already on your way.{c['reset']}")
        return True
    if getattr(player, 'room', None) is None or player.room.vnum != int(t['room']):
        await player.send(f"{c['yellow']}{_cap(npc.name)} only carries passengers from {t.get('from_name', 'his landing')}.{c['reset']}")
        return True
    if gold is None and item is None:
        gold = fare
    if gold is not None:
        if gold < fare:
            await player.send(f"{c['cyan']}{say.get('short', f'{_cap(npc.name)} looks at the coin and does not take it.')}{c['reset']}")
            return True
        if (player.gold or 0) < gold:
            await player.send(f"{c['cyan']}{say.get('broke', f'{_cap(npc.name)} holds out a hand and waits. You have not the fare.')}{c['reset']}")
            return True
        player.gold -= gold
    await player.send(f"{c['bright_cyan']}{say.get('paid', f'{_cap(npc.name)} takes your coin without a word.')}{c['reset']}")
    if player.room:
        await player.room.send_to_room(f"{c['cyan']}{player.name} pays {npc.name} and steps aboard.{c['reset']}", exclude=[player])
    asyncio.ensure_future(_carry(player, npc, t))
    return True


async def _carry(player, npc, t):
    """The crossing: the via room for a few moments (the lines of the journey), then the far side."""
    world = player.world
    via, to = world.rooms.get(t.get('via')), world.rooms.get(int(t['to']))
    if to is None:
        return
    c = player.config.COLORS
    CROSSING.add(player)
    try:
        if via is not None:
            await _move(player, via)
            lines = list(t.get('journey') or [])
            secs = float(t.get('secs', 6))
            step = secs / max(1, len(lines) + 1)
            for line in lines:
                await asyncio.sleep(step)
                if player.room is not via:
                    return
                await player.send(f"{c['cyan']}{line}{c['reset']}")
            await asyncio.sleep(step)
            if player.room is not via:
                return
        await _move(player, to)
        arrive = (t.get('say') or {}).get('arrive')
        if arrive:
            await player.send(f"{c['bright_cyan']}{arrive}{c['reset']}")
    finally:
        CROSSING.discard(player)


async def _move(player, room):
    old = player.room
    if old is not None and player in old.characters:
        old.characters.remove(player)
    player.room = room
    room.characters.append(player)
    try:
        await room.show_to(player)
    except Exception:
        logger.debug('show_to failed', exc_info=True)
    try:
        await player.sync_room()
    except Exception:
        logger.debug('sync_room failed', exc_info=True)


def _cap(s):
    s = str(s or '')
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------- gates

def is_warded(door):
    return bool((door or {}).get('warded'))


def ward_message(door):
    import doors
    return f"The {doors.label(door)} is warded. Only its own key will open it."


def crumble_key(player, door):
    """The key that opened a gate crumbles in the lock: the gate needs its keeper again after the
    zone resets. Returns the key's name, or None when no gate key was used."""
    import doors
    kv = doors.key_vnum(door)
    if kv is None or kv not in KEY_VNUMS:
        return None
    for item in list(getattr(player, 'inventory', None) or []):
        if getattr(item, 'vnum', None) == kv:
            player.inventory.remove(item)
            return getattr(item, 'short_desc', 'the key')
    eq = getattr(player, 'equipment', None) or {}
    for slot, item in list(eq.items()) if isinstance(eq, dict) else []:
        if item is not None and getattr(item, 'vnum', None) == kv:
            eq[slot] = None
            return getattr(item, 'short_desc', 'the key')
    return None
