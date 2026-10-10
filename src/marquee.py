"""The marquee quests (owner: "Each class should have a final marquee spell/skill/ability. This
should be a quest for each character. It should be achievable solo or with a group. If done solo
the difficulty should take a couple hours of play time. If in a group the difficulty should
scale based on how many embark on the quest when the player accepts.")

This is the engine; what each quest asks is in marquee_quests.py, how hard its foes are in
marquee_scale.py and the abilities they teach in marquee_abilities.py.

  offer    `talk` to your class's guildmaster from level 45: the quest is offered (a card in
           the 3D client); `marquee accept` beside them takes it.
  embark   group members beside you are asked to join (30 s: `marquee join` / `decline`).
           Who joined is the party for good: its size fixes how hard every foe of the quest
           is, even if someone leaves later.
  stages   talk / kill / collect / ritual / trial / return, through the endgame zones. The
           quest's foes are its own: placed when the party comes near, made for the party's
           size, and out of reach of anyone outside it. Any member's kill counts.
  trial    a private copy of a small place (world/marquee/trials/<class>.json) for the party:
           waves behind locked gates, then a boss. `trial leave` leaves it; left empty for
           ten minutes it closes (and starts over from the first wave).
  return   the guildmaster teaches the marquee ability. Helpers are paid when the trial falls.

State: the owner's `marquee` dict (saved) holds the class, the stage, its progress, the party,
its size and level; a helper's `marquee_help` names whose quest they share. What exists only
while the server runs (the foes placed, a ritual, the trial) is rebuilt when needed.
"""
import asyncio
import copy
import json
import logging
import os
import random
import time

import marquee_quests as mq
import marquee_scale as ms

logger = logging.getLogger('Misthollow')

OFFER_LEVEL = 45
EMBARK_SECONDS = 30
ENGAGE_DELAY = 2.5       # a foe placed by the quest gives you this long to see it before it attacks
AWAY_SECONDS = 600       # the party away this long: the stage's foes go home (back when you return)
RESPAWN_SECONDS = 20     # a gathering stage's creature comes back this long after it falls
TRIAL_EMPTY = 600        # an empty trial closes after this long
TRIAL_WON = 180          # a won trial closes this long after the win (or once empty)
ZONE_BASE = 7000         # trial zones: 7000 and up, rooms zone * 100 + i
TRIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'world', 'marquee', 'trials')
LENGTH = 'About two hours alone'

WORLD = None
RUNS = {}                # owner (lower-case name) -> Run
VOTES = {}               # owner (lower-case name) -> Vote
_zone_seq = 0


def _c(p):
    return p.config.COLORS


def _online(name):
    if not name or WORLD is None:
        return None
    return (getattr(WORLD, 'players', None) or {}).get(str(name).lower())


def _is_player(ch):
    return hasattr(ch, 'account_name')


def _hero_of(ch):
    """The player behind a blow: the player, or the master of a pet or a charmed follower."""
    if ch is None:
        return None
    if _is_player(ch):
        return ch
    for attr in ('owner', 'master'):
        o = getattr(ch, attr, None)
        if o is not None and _is_player(o):
            return o
    return None


def _alive(ch):
    return ch is not None and getattr(ch, 'hp', 0) > 0 and getattr(ch, 'position', '') != 'dead'


def can_touch(hero, mob):
    """May this hero harm this creature? Anyone may, unless it belongs to someone else's
    marquee quest (then only those who embarked on it; with its owner away, whoever embarked
    can still fight what is already out)."""
    tag = getattr(mob, 'marquee_tag', None)
    if not tag:
        return True
    owner = _online(tag.get('owner'))
    m = getattr(owner, 'marquee', None) if owner else None
    if _in_party(m, hero):
        return True
    run = RUNS.get(tag.get('owner'))
    return m is None and run is not None and getattr(hero, 'name', None) in run.party


async def _event(player, event):
    wm = getattr(WORLD, 'web_map', None)
    if wm is None or not getattr(player, 'connection', None):
        return
    try:
        await wm.notify_event(player, event)
    except Exception:
        pass


async def _push(player):
    wm = getattr(WORLD, 'web_map', None)
    if wm is None or not getattr(player, 'connection', None):
        return
    try:
        await wm.notify_player(player)
    except Exception:
        pass


# ---------------------------------------------------------------- whose quest, which stage
def quest_of(player):
    """(owner name, the owner's marquee dict or None when the owner is away, role) — or
    (None, None, None) for someone in no marquee quest."""
    m = getattr(player, 'marquee', None)
    if isinstance(m, dict) and m.get('cls'):
        return player.name, m, 'owner'
    h = getattr(player, 'marquee_help', None)
    if isinstance(h, dict) and h.get('owner'):
        o = _online(h['owner'])
        if o is None:
            return h['owner'], None, 'helper'
        om = getattr(o, 'marquee', None)
        if isinstance(om, dict) and player.name in (om.get('party') or []):
            return o.name, om, 'helper'
        player.marquee_help = None        # that quest ended (or let them go) while they were away
    return None, None, None


def _stage(m):
    q = mq.quest_for(m.get('cls')) if m else None
    i = (m or {}).get('stage', 0)
    return q, (q['stages'][i] if q and 0 <= i < len(q['stages']) else None)


def _party(m):
    """The embarked members online now."""
    return [p for p in (_online(n) for n in (m.get('party') or [])) if p is not None]


def _in_party(m, player):
    return player is not None and m is not None and player.name in (m.get('party') or [])


def _need(m, st):
    return st.get('need', 1) + ms.extra_adds(m.get('n', 1))


def _room(vnum):
    return (getattr(WORLD, 'rooms', None) or {}).get(vnum)


def _where_name(room):
    if room is None:
        return ''
    zone = getattr(getattr(room, 'zone', None), 'name', '') or ''
    return f"{room.name}{f' ({zone})' if zone and zone not in room.name else ''}"


def _npc_name(vnum):
    p = ((getattr(WORLD, 'mob_prototypes', None) or {}).get(vnum) or {})
    return p.get('short_desc') or p.get('name') or 'them'


def _npc_word(vnum):
    """A word that finds this figure with `talk`."""
    p = ((getattr(WORLD, 'mob_prototypes', None) or {}).get(vnum) or {})
    words = (p.get('name') or 'them').split()
    return words[-1] if words else 'them'


class Run:
    """What a quest has out in the world right now."""

    def __init__(self, owner):
        self.owner = owner          # the owner's name
        self.mobs = []              # the stage's foes (and figures) placed now
        self.seen = time.time()     # when a member was last near them
        self.ritual = None          # {'start', 'waves': set of the waves placed}
        self.trial = None           # a Trial
        self.respawn = {}           # room vnum -> earliest time a gathering creature may come back
        self.party = set()          # who embarked (kept for when the owner is away)


def _run(owner_name):
    key = str(owner_name).lower()
    run = RUNS.get(key)
    if run is None:
        run = RUNS[key] = Run(owner_name)
    return run


# ---------------------------------------------------------------- the quest's own foes
def _proto(vnum):
    return (getattr(WORLD, 'mob_prototypes', None) or {}).get(int(vnum))


_HOSTILE = ('aggressive', 'aggr_good', 'aggr_evil', 'aggr_neutral', 'wimpy', 'scavenger', 'helper')


async def _place(run, m, vnum, room, kind, **tag):
    """Place one of the quest's creatures, made for the party (kind: marquee_scale.ROUNDS, or
    'npc' for a figure to speak with)."""
    proto = _proto(vnum)
    if not proto or room is None:
        return None
    from bosses import create_mob_from_prototype
    n = m.get('n', 1)
    p = dict(proto)
    p['flags'] = [f for f in proto.get('flags', []) if f not in _HOSTILE]
    if kind != 'npc':
        p['max_hp'] = ms.foe_health(kind, m.get('level', OFFER_LEVEL), n, m.get('cls'))
        p['exp'] = ms.exp_reward(int(proto.get('exp', 1000)), n)
    if proto.get('boss_config'):
        cfg = copy.deepcopy(proto['boss_config'])
        cfg['ability_interval'] = round(cfg.get('ability_interval', 4.0) * ms.tempo(n), 2)
        extra = ms.extra_adds(n)
        if extra:
            for ph in cfg.get('phases', []):
                if ph.get('spawn_adds'):
                    ph['spawn_adds'] = {k: v + extra for k, v in ph['spawn_adds'].items()}
            for ab in cfg.get('abilities', []):
                if ab.get('summon'):
                    ab['summon'] = {k: v + extra for k, v in ab['summon'].items()}
        p['boss_config'] = cfg
    mob = create_mob_from_prototype(p, WORLD)
    if kind != 'npc':
        mob._dmg_scale = ms.damage_factor(n)
    mob.marquee_tag = dict(tag, owner=run.owner.lower(), stage=m.get('stage', 0), kind=kind)
    mob._marquee_engage_at = time.time() + ENGAGE_DELAY
    mob.room = room
    mob.home_room = room
    mob.home_zone = room.zone.number if getattr(room, 'zone', None) else None
    room.characters.append(mob)
    WORLD.npcs.append(mob)
    if getattr(mob, 'boss_config', None) is not None:
        mob.on_adds = lambda adds, run=run, m=m: _adopt(run, m, adds)
    run.mobs.append(mob)
    return mob


def _adopt(run, m, adds):
    """A quest boss called for help: the newcomers belong to the quest too (lighter than its own)."""
    for a in adds:
        a.max_hp = a.hp = ms.foe_health('add', m.get('level', OFFER_LEVEL), m.get('n', 1), m.get('cls'))
        a._dmg_scale = ms.damage_factor(m.get('n', 1))
        a.marquee_tag = {'owner': run.owner.lower(), 'stage': m.get('stage', 0), 'kind': 'add', 'add': True}
        run.mobs.append(a)


def _remove(mob):
    room = getattr(mob, 'room', None)
    if room is not None and mob in room.characters:
        room.characters.remove(mob)
    if WORLD is not None and mob in WORLD.npcs:
        WORLD.npcs.remove(mob)
    for ch in list(getattr(room, 'characters', None) or []):
        if getattr(ch, 'fighting', None) is mob:
            ch.fighting = None
            if getattr(ch, 'position', '') == 'fighting':
                ch.position = 'standing'
    mob.fighting = None
    mob.room = None


def _clear_mobs(run, keep=None):
    """The stage's foes go home (all of them, or all but those `keep` says to keep)."""
    for mob in list(run.mobs):
        if keep and keep(mob):
            continue
        if _alive(mob):
            _remove(mob)
        run.mobs.remove(mob)


async def fallen(mob, killer=None):
    """One of the quest's creatures fell (counted once, however it died)."""
    if getattr(mob, '_marquee_counted', False):
        return
    mob._marquee_counted = True
    tag = getattr(mob, 'marquee_tag', None) or {}
    run = RUNS.get(tag.get('owner'))
    if run is not None and mob in run.mobs:
        run.mobs.remove(mob)
    owner = _online(tag.get('owner'))
    m = getattr(owner, 'marquee', None) if owner else None
    if run is None or not isinstance(m, dict) or m.get('stage') != tag.get('stage') or tag.get('add') or tag.get('kind') == 'npc':
        return
    q, st = _stage(m)
    if not st:
        return
    pr = m.setdefault('progress', {})
    if st['kind'] == 'kill' and tag.get('slot') is not None:
        dead = pr.setdefault('dead', [False] * len(st['spawns']))
        if tag['slot'] < len(dead):
            dead[tag['slot']] = True
        if all(dead):
            await _advance(run, owner, m)
        else:
            left = len(dead) - sum(dead)
            await _tell(m, 'yellow', f"{mob.short_desc[:1].upper()}{mob.short_desc[1:]} falls. {left} more to go.")
            await _push_party(m)
    elif st['kind'] == 'collect':
        room = getattr(mob, '_marquee_room', None)
        if room is not None:
            run.respawn[room] = time.time() + RESPAWN_SECONDS
        if random.randint(1, 100) <= st.get('chance', 50):
            pr['got'] = pr.get('got', 0) + 1
            need = _need(m, st)
            hero = _hero_of(killer)
            who = f"{hero.name} pulls" if hero is not None else 'You pull'
            await _tell(m, 'bright_yellow', f"{who} {('an' if st['item'][:1] in 'aeiou' else 'a')} {st['item']} from the ashes ({min(pr['got'], need)}/{need}).")
            if pr['got'] >= need:
                await _advance(run, owner, m)
            else:
                await _push_party(m)
        else:
            await _tell(m, 'yellow', f"The {st['item']} gutters out as it falls — nothing to take.")


def _sweep(run):
    """Foes that left the world without a death we saw: gone home, to be placed again."""
    dead = []
    for mob in list(run.mobs):
        if not _alive(mob):
            dead.append(mob)
        elif mob.room is None or mob not in mob.room.characters:
            run.mobs.remove(mob)
    return dead


async def _engage(run, m, party, now):
    """A placed foe turns on a member of the party in its room."""
    from combat import CombatHandler
    for mob in list(run.mobs):
        tag = getattr(mob, 'marquee_tag', {})
        if tag.get('kind') == 'npc' or not _alive(mob) or getattr(mob, 'fighting', None) is not None:
            continue
        if getattr(mob, '_marquee_engage_at', 0) > now:
            continue
        here = [p for p in party if p.room is mob.room and _alive(p)]
        if here:
            try:
                await CombatHandler.start_combat(mob, random.choice(here))
            except Exception as e:
                logger.debug(f"marquee engage: {e}")


# ---------------------------------------------------------------- telling the party
async def _tell(m, colour, text, only=None):
    for p in (only or _party(m)):
        c = _c(p)
        await p.send(f"{c.get(colour, '')}{text}{c['reset']}")


async def _push_party(m):
    for p in _party(m):
        await _push(p)


def _hint(m, st):
    k = st['kind']
    if k == 'talk':
        return f"Speak with {_npc_name(st['npc'])} — {_where_name(_room(st['room']))}."
    if k == 'kill':
        return '  '.join(f"• {sp['label']}" for sp in st['spawns'])
    if k == 'collect':
        return f"{st.get('objective', 'Gather')} — {_need(m, st)} {st['item']}s, about one from every two kills."
    if k == 'ritual':
        return f"At {_where_name(_room(st['room']))}: type 'marquee {st['verb']}'."
    if k == 'trial':
        return f"At {_where_name(_room(st['room']))}: type 'trial enter'."
    if k == 'return':
        q = mq.quest_for(m['cls'])
        return f"Speak with {q['giver_name']} — {_where_name(_room(q['giver_room']))}."
    return ''


async def _announce(m, only=None):
    q, st = _stage(m)
    if not st:
        return
    for p in (only or _party(m)):
        c = _c(p)
        await p.send('')
        await p.send(f"{c['bright_yellow']}★ {q['name']} — {st['title']} ({m['stage'] + 1}/{len(q['stages'])}){c['reset']}")
        await p.send(f"{c['white']}{st['text']}{c['reset']}")
        hint = _hint(m, st)
        if hint:
            await p.send(f"{c['cyan']}{hint}{c['reset']}")
        await _event(p, {'type': 'quest_stage', 'title': st['title'], 'text': st['text'],
                         'stage': m['stage'] + 1, 'of': len(q['stages'])})


async def _advance(run, owner, m):
    q, st = _stage(m)
    if st and st.get('done'):
        await _tell(m, 'bright_green', st['done'])
        for p in _party(m):
            await _event(p, {'type': 'quest_stage', 'title': st['title'], 'text': st['done'], 'done': True})
    _clear_mobs(run, keep=lambda mob: run.trial is not None and getattr(mob, 'room', None) is not None
                and getattr(mob.room, 'zone', None) is run.trial.zone)
    run.ritual = None
    run.respawn = {}
    m['stage'] = m.get('stage', 0) + 1
    m['progress'] = {}
    await _announce(m)
    await _push_party(m)
    try:
        await owner.save()
    except Exception:
        pass


# ---------------------------------------------------------------- offer, embark, begin
def eligible(player, cls=None):
    """Why this player may not take their class's marquee quest now ('' when they may)."""
    mine = str(getattr(player, 'char_class', '')).lower()
    cls = (cls or mine).lower()
    q = mq.quest_for(cls)
    if not q or cls != mine:
        return 'no quest'
    if (getattr(player, 'level', 1) or 1) < OFFER_LEVEL:
        return 'level'
    import mastery
    if mastery.pct_of(player, q['ability']) > 0:
        return 'learned'
    owner, m, role = quest_of(player)
    if owner:
        return 'busy'
    return ''


def _giver_here(player, q):
    room = getattr(player, 'room', None)
    if room is None:
        return False
    return room.vnum == q['giver_room'] or any(getattr(ch, 'vnum', None) == q['giver'] and not _is_player(ch)
                                               for ch in room.characters)


def _free_members_here(player):
    """Group members beside the player who could embark with them."""
    group = getattr(player, 'group', None)
    out = []
    for p in (getattr(group, 'members', None) or []):
        if p is player or getattr(p, 'room', None) is not player.room or not getattr(p, 'connection', None):
            continue
        if quest_of(p)[0]:
            continue
        out.append(p)
    return out


async def offer(player, q):
    c = _c(player)
    import marquee_abilities as ma
    name = ma.NAMES.get(q['ability'], q['ability'])
    here = _free_members_here(player)
    await player.send('')
    await player.send(f"{c['bright_yellow']}★ A marquee quest: {q['name']}{c['reset']}")
    await player.send(f"{c['white']}{q['offer']}{c['reset']}")
    await player.send(f"{c['bright_cyan']}It teaches: {q['teaches']}{c['reset']}")
    await player.send(f"{c['cyan']}{LENGTH}. Group members beside you will be asked to join when you accept — "
                      f"each who joins makes it harder, and shares the glory.{c['reset']}")
    await player.send(f"{c['bright_green']}Type 'marquee accept' to take it on.{c['reset']}")
    desc = q['teaches'].split(' — ', 1)[-1]
    await _event(player, {'type': 'quest_offer', 'quest': {
        'id': q['id'], 'name': q['name'], 'giver': q['giver_name'][:1].upper() + q['giver_name'][1:],
        'text': q['offer'], 'reward': {'name': name, 'desc': desc}, 'length': LENGTH,
        'party': [player.name] + [p.name for p in here]}})


class Vote:
    def __init__(self, owner, cls, invited):
        self.owner = owner
        self.cls = cls
        self.answers = {p.name: None for p in invited}
        self.expires = time.time() + EMBARK_SECONDS


async def accept(player):
    c = _c(player)
    cls = str(getattr(player, 'char_class', '')).lower()
    q = mq.quest_for(cls)
    why = eligible(player, cls) if q else 'no quest'
    if why:
        msg = {'no quest': "There is no marquee quest for you yet.",
               'level': f"Your guildmaster has one last lesson for you — from level {OFFER_LEVEL}.",
               'learned': "You have already earned your marquee ability.",
               'busy': "You are already on a marquee quest ('marquee' shows where you are)."}[why]
        await player.send(f"{c['yellow']}{msg}{c['reset']}")
        return
    if not _giver_here(player, q):
        await player.send(f"{c['yellow']}Only {q['giver_name']} can set you on this road — find them at "
                          f"{_where_name(_room(q['giver_room']))}.{c['reset']}")
        return
    if player.name.lower() in VOTES:
        await player.send(f"{c['yellow']}You are still waiting for your group to answer ('marquee go' sets out now).{c['reset']}")
        return
    invited = _free_members_here(player)
    if not invited:
        await begin(player, [player])
        return
    VOTES[player.name.lower()] = Vote(player, cls, invited)
    for p in invited:
        pc = _c(p)
        await p.send(f"{pc['bright_yellow']}{player.name} embarks on {q['name']}, their {cls} trial. Will you join them? "
                     f"Every member who joins makes it harder — and shares the glory.{pc['reset']}")
        await p.send(f"{pc['bright_green']}Type 'marquee join' or 'marquee decline' ({EMBARK_SECONDS} s).{pc['reset']}")
        await _event(p, {'type': 'quest_embark', 'from': player.name, 'quest': q['name'], 'cls': cls, 'expires': EMBARK_SECONDS})
    names = ', '.join(p.name for p in invited)
    await player.send(f"{c['cyan']}You ask {names} to embark with you ({EMBARK_SECONDS} s). "
                      f"Type 'marquee go' to set out without waiting.{c['reset']}")


async def answer(player, yes):
    c = _c(player)
    for key, v in list(VOTES.items()):
        if player.name in v.answers:
            v.answers[player.name] = bool(yes)
            await player.send(f"{c['cyan']}{'You will embark with' if yes else 'You let'} {v.owner.name}"
                              f"{'.' if yes else ' go on without you.'}{c['reset']}")
            await v.owner.send(f"{_c(v.owner)['cyan']}{player.name} {'joins you' if yes else 'declines'}.{_c(v.owner)['reset']}")
            if all(a is not None for a in v.answers.values()):
                await _close_vote(key)
            return
    await player.send(f"{c['yellow']}Nobody has asked you to embark on a quest.{c['reset']}")


async def _close_vote(key):
    v = VOTES.pop(key, None)
    if v is None:
        return
    owner = v.owner
    if _online(owner.name) is not owner or eligible(owner, v.cls):
        return
    joined = [owner]
    for name, yes in v.answers.items():
        p = _online(name)
        if yes and p is not None and not quest_of(p)[0]:
            joined.append(p)
    await begin(owner, joined[:6])


async def _votes(now):
    for key, v in list(VOTES.items()):
        if now >= v.expires:
            await _close_vote(key)


async def begin(owner, members):
    """The quest is accepted: the party (and so how hard it is) is fixed from here on."""
    cls = str(owner.char_class).lower()
    q = mq.quest_for(cls)
    n = len(members)
    m = {'id': q['id'], 'cls': cls, 'stage': 0, 'progress': {}, 'party': [p.name for p in members], 'n': n,
         'level': ms.party_level(owner.level, [p.level for p in members if p is not owner]), 'accepted': int(time.time())}
    owner.marquee = m
    for p in members:
        if p is not owner:
            p.marquee_help = {'owner': owner.name, 'id': q['id'], 'cls': cls}
    RUNS[owner.name.lower()] = Run(owner.name)
    RUNS[owner.name.lower()].party = set(m['party'])
    for p in members:
        c = _c(p)
        if n == 1:
            await p.send(f"{c['bright_yellow']}You set out alone on {q['name']}.{c['reset']}")
        else:
            others = ', '.join(x.name for x in members if x is not p)
            await p.send(f"{c['bright_yellow']}{'You set' if p is owner else owner.name + ' sets'} out on {q['name']} with "
                         f"{others}. ({n} embarked: its foes are made for {n}.){c['reset']}")
    await _announce(m)
    await _push_party(m)
    for p in members:
        try:
            await p.save()
        except Exception:
            pass


async def abandon(player, confirm=False):
    c = _c(player)
    owner_name, m, role = quest_of(player)
    if not owner_name:
        await player.send(f"{c['yellow']}You are on no marquee quest.{c['reset']}")
        return
    if role == 'helper':
        if m is not None and player.name in m.get('party', []):
            m['party'].remove(player.name)
            await _tell(m, 'yellow', f"{player.name} leaves {owner_name}'s quest. (It stays as hard as when you embarked.)")
            await _push_party(m)
        player.marquee_help = None
        await player.send(f"{c['yellow']}You stop helping {owner_name}.{c['reset']}")
        await _push(player)
        return
    if not confirm:
        await player.send(f"{c['yellow']}Give up {mq.quest_for(m['cls'])['name']}? Everything done so far is lost. "
                          f"Type 'marquee abandon confirm'.{c['reset']}")
        return
    await end(player, m, quiet=False)


async def end(owner, m, quiet=True):
    """Clear a quest away: its foes, its trial, its helpers."""
    run = RUNS.pop(owner.name.lower(), None)
    party = _party(m)
    if run is not None:
        if run.trial is not None:
            await _close_trial(run, 'abandoned')
        _clear_mobs(run)
    owner.marquee = None
    for p in party:
        if p is not owner:
            p.marquee_help = None
            if not quiet:
                await p.send(f"{_c(p)['yellow']}{owner.name} gives up the quest.{_c(p)['reset']}")
    if not quiet:
        await owner.send(f"{_c(owner)['yellow']}You give up the quest.{_c(owner)['reset']}")
    for p in party:
        await _push(p)


# ---------------------------------------------------------------- talking
def _target_of(player, args):
    """The figure `talk <args>` speaks to (as cmd_talk finds it)."""
    from mobs import Mobile
    words = list(args or [])
    if words and words[-1].isdigit():
        words = words[:-1]
    text = ' '.join(words).lower()
    if not text:
        f = getattr(player, 'fighting', None)
        return f if isinstance(f, Mobile) else None
    for ch in (getattr(getattr(player, 'room', None), 'characters', None) or []):
        if isinstance(ch, Mobile) and text in ch.name.lower():
            return ch
    return None


async def on_talk(player, target):
    if target is None:
        return
    vnum = getattr(target, 'vnum', None)
    owner_name, m, role = quest_of(player)
    if m is not None:
        q, st = _stage(m)
        if st and st['kind'] == 'talk' and vnum == st['npc']:
            c = _c(player)
            await player.room.send_to_room(f"{c['bright_white']}{st['say']}{c['reset']}")
            await _advance(_run(owner_name), _online(owner_name), m)
            return
        if st and st['kind'] == 'return' and vnum == q['giver']:
            if role == 'owner':
                await finish(player, m)
            else:
                await player.send(f"{_c(player)['yellow']}{q['giver_name'][:1].upper() + q['giver_name'][1:]} waits for "
                                  f"{owner_name} to bring the banner home.{_c(player)['reset']}")
            return
    if vnum in mq.GIVERS:
        cls = str(getattr(player, 'char_class', '')).lower()
        q = mq.quest_for(cls)
        if not q or q['giver'] != vnum:
            return
        why = eligible(player, cls)
        if not why:
            await offer(player, q)
        elif why == 'level':
            c = _c(player)
            await player.send(f"{c['cyan']}{target.short_desc[:1].upper()}{target.short_desc[1:]} looks you over. "
                              f"'Come back when you have seen level {OFFER_LEVEL}. I will have one last lesson for you.'{c['reset']}")


async def finish(owner, m):
    """The return: the guildmaster teaches the marquee ability."""
    import mastery
    import marquee_abilities as ma
    q, st = _stage(m)
    c = _c(owner)
    if st and st.get('say'):
        await owner.room.send_to_room(f"{c['bright_white']}{st['say']}{c['reset']}")
    ability = q['ability']
    store = mastery.store_of(owner, ability)
    store[ability] = max(store.get(ability, 0), mastery.LEARN_AT)
    exp, gold = owner.level * 3000, 2500
    try:
        await owner.gain_exp(exp, source='quest')
    except TypeError:
        await owner.gain_exp(exp)
    owner.gold = getattr(owner, 'gold', 0) + gold
    name = ma.NAMES.get(ability, ability)
    await owner.send('')
    await owner.send(f"{c['bright_yellow']}★★★ {q['name']} is complete! ★★★{c['reset']}")
    await owner.send(f"{c['bright_yellow']}You learned {name}!{c['reset']} {c['white']}{mastery.describe(ability)}{c['reset']}")
    await owner.send(f"{c['cyan']}You gain {exp} experience and {gold} gold. Type '{ability.replace('_', ' ')}' "
                     f"(or put it on your bar) to use it; it grows as you do.{c['reset']}")
    await _event(owner, {'type': 'quest_done', 'quest': q['name'], 'reward': name, 'ability': ability})
    run = RUNS.pop(owner.name.lower(), None)
    if run is not None:
        _clear_mobs(run)
        if run.trial is not None:
            await _close_trial(run, 'done')
    for p in _party(m):
        if p is not owner:
            p.marquee_help = None
            await p.send(f"{_c(p)['bright_yellow']}{owner.name} has earned {name}. Your part in {q['name']} is told.{_c(p)['reset']}")
            await _push(p)
    owner.marquee = None
    await _push(owner)
    try:
        await owner.save()
    except Exception:
        pass


# ---------------------------------------------------------------- the stages, each second
async def _talk_tick(run, m, st, party, now):
    room = _room(st['room'])
    if room is None or not any(p.room is room for p in party):
        return
    if any(getattr(ch, 'vnum', None) == st['npc'] and _alive(ch) for ch in room.characters):
        return
    await _place(run, m, st['npc'], room, 'npc')


async def _kill_tick(run, m, st, party, now):
    dead = m.setdefault('progress', {}).setdefault('dead', [False] * len(st['spawns']))
    out = {getattr(x, 'marquee_tag', {}).get('slot') for x in run.mobs}
    for i, sp in enumerate(st['spawns']):
        if i < len(dead) and dead[i] or i in out:
            continue
        room = _room(sp['room'])
        if room is None or not any(p.room is room for p in party):
            continue
        mob = await _place(run, m, sp['vnum'], room, sp['kind'], slot=i)
        if mob is None:
            continue
        for _ in range(ms.extra_adds(m.get('n', 1)) if st.get('adds') else 0):
            await _place(run, m, st['adds'], room, 'minion', escort=i)
        line = (f"{mob.short_desc[:1].upper()}{mob.short_desc[1:]} turns from the forge to face you!" if sp['kind'] == 'warden'
                else f"{mob.short_desc[:1].upper()}{mob.short_desc[1:]} strides out to meet you!")
        await room.send_to_room(f"{_c(party[0])['bright_red']}{line}{_c(party[0])['reset']}")


async def _collect_tick(run, m, st, party, now):
    for v in st['rooms']:
        room = _room(v)
        if room is None or not any(p.room is room for p in party):
            continue
        live = [x for x in run.mobs if x.room is room and _alive(x)]
        if len(live) >= st.get('per_room', 2) or now < run.respawn.get(v, 0):
            continue
        mob = await _place(run, m, st['mob'], room, 'minion')
        if mob is not None:
            mob._marquee_room = v
            run.respawn[v] = now + 3
            await room.send_to_room(f"{_c(party[0])['red']}{mob.short_desc[:1].upper()}{mob.short_desc[1:]} rises out of the ash.{_c(party[0])['reset']}")


async def plant(player):
    """The ritual's verb: begin holding the place."""
    c = _c(player)
    owner_name, m, role = quest_of(player)
    q, st = _stage(m) if m else (None, None)
    if not st or st['kind'] != 'ritual':
        await player.send(f"{c['yellow']}There is nothing to {('plant' if not st else st.get('verb', 'plant'))} here.{c['reset']}")
        return
    if role != 'owner':
        await player.send(f"{c['yellow']}It is {owner_name}'s to do — stand with them while they do it.{c['reset']}")
        return
    room = _room(st['room'])
    if player.room is not room:
        await player.send(f"{c['yellow']}Not here — at {_where_name(room)}.{c['reset']}")
        return
    run = _run(owner_name)
    if run.ritual is not None:
        await player.send(f"{c['yellow']}It is already done — hold it!{c['reset']}")
        return
    run.ritual = {'start': time.time(), 'waves': set()}
    await room.send_to_room(f"{c['bright_yellow']}{st['start']}{c['reset']}")
    for p in _party(m):
        await _event(p, {'type': 'quest_stage', 'title': st['title'], 'text': f"Hold for {st['seconds']} seconds!"})
    await _push_party(m)


async def _ritual_tick(run, m, st, party, now):
    r = run.ritual
    if r is None:
        return
    room = _room(st['room'])
    owner = _online(run.owner)
    held = now - r['start']
    if owner is None or owner.room is not room or not _alive(owner):
        _clear_mobs(run)
        run.ritual = None
        await _tell(m, 'bright_red', f"The banner topples — {st['title']} is lost for now. Plant it again ('marquee {st['verb']}').")
        await _push_party(m)
        return
    for i, w in enumerate(st['waves']):
        if i in r['waves'] or held < w['at']:
            continue
        r['waves'].add(i)
        for _ in range(w['count'] + ms.extra_adds(m.get('n', 1))):
            mob = await _place(run, m, w['vnum'], room, 'wave', wave=i)
            if mob is not None:
                mob._marquee_engage_at = now + 1
        await room.send_to_room(f"{_c(owner)['bright_red']}{w['text']}{_c(owner)['reset']}")
    m.setdefault('progress', {})['held'] = min(st['seconds'], int(held))
    if held >= st['seconds'] and len(r['waves']) == len(st['waves']) and not any(_alive(x) for x in run.mobs):
        await _advance(run, owner, m)


# ---------------------------------------------------------------- the private trial
class Trial:
    def __init__(self, owner, tpl, zone, rooms, gate):
        self.owner = owner
        self.tpl = tpl
        self.zone = zone
        self.rooms = rooms          # key -> Room
        self.gate = gate            # the room it is entered from (and left to)
        self.wave = 0
        self.placed = False         # this wave's foes are out
        self.boss = None
        self.won = None
        self.empty_since = None
        self.party = set()


_TEMPLATES = {}


def _template(key):
    if key not in _TEMPLATES:
        with open(os.path.join(TRIALS_DIR, f'{key}.json')) as f:
            _TEMPLATES[key] = json.load(f)
    return _TEMPLATES[key]


def _next_zone():
    global _zone_seq
    while True:
        _zone_seq += 1
        zn = ZONE_BASE + _zone_seq
        if zn not in WORLD.zones and zn * 100 not in WORLD.rooms:
            return zn


def _build_trial(run, m, st):
    from world import Room, Zone
    tpl = _template(st['trial'])
    gate = _room(st['room'])
    zn = _next_zone()
    zone = Zone(zn)
    zone.name = tpl['name']
    zone.builders = 'Marquee'
    zone.reset_mode = 0
    zone.lifespan = 9999
    zone.top = zn * 100 + 99
    rooms = {}
    for i, rd in enumerate(tpl['rooms']):
        room = Room(zn * 100 + i)
        room.zone = zone
        room.name = rd['name']
        room.description = rd['description']
        room.sector_type = rd.get('sector', 'inside')
        room.flags = {'no_recall', 'no_summon', 'no_teleport', 'lit'} | ({'indoors'} if room.sector_type in ('inside', 'dungeon') else set())
        room.instance_exit = gate.vnum
        rooms[rd['key']] = room
        zone.rooms[room.vnum] = room
    for rd in tpl['rooms']:
        room = rooms[rd['key']]
        for d, ex in rd.get('exits', {}).items():
            to = rooms[ex['to']]
            e = {'to_room': to.vnum, 'room': to}
            if ex.get('door'):
                # locked to a key that does not exist and sealed: only the wave's fall opens it
                e['door'] = {'name': ex['door'], 'state': 'closed', 'locked': True, 'pickproof': True,
                             'magically_blocked': True, 'key_vnum': 9799}
            room.exits[d] = e
    WORLD.zones[zn] = zone
    for room in rooms.values():
        WORLD.rooms[room.vnum] = room
    run.trial = Trial(run.owner, tpl, zone, rooms, gate)
    run.trial.party = set(m.get('party') or [])
    logger.info(f"marquee: trial '{tpl['name']}' opened for {run.owner} as zone {zn}")
    return run.trial


async def _move(player, room):
    """Take a player to a room at once (into or out of a trial)."""
    from combat import CombatHandler
    old = getattr(player, 'room', None)
    if old is room:
        return
    foe = getattr(player, 'fighting', None)
    if foe is not None:
        try:
            await CombatHandler.end_combat(player, foe)
        except Exception:
            player.fighting = None
    if old is not None and player in old.characters:
        old.characters.remove(player)
    player.room = room
    room.characters.append(player)
    await room.show_to(player)
    await _push(player)


def _in_trial(player, run):
    return run is not None and run.trial is not None and getattr(getattr(player, 'room', None), 'zone', None) is run.trial.zone


async def enter_trial(player):
    c = _c(player)
    owner_name, m, role = quest_of(player)
    q, st = _stage(m) if m else (None, None)
    if not st or st['kind'] != 'trial':
        await player.send(f"{c['yellow']}Your road has not brought you to a trial{' yet' if st else ''}.{c['reset']}")
        return
    run = _run(owner_name)
    if _in_trial(player, run):
        await player.send(f"{c['yellow']}You are already inside.{c['reset']}")
        return
    gate = _room(st['room'])
    if player.room is not gate:
        await player.send(f"{c['yellow']}The way in opens at {_where_name(gate)}.{c['reset']}")
        return
    if run.trial is None:
        _build_trial(run, m, st)
    t = run.trial
    entrance = t.rooms[t.tpl['entrance']]
    going = [player] + [p for p in _party(m) if p is not player and p.room is gate and _alive(p)]
    for p in going:
        pc = _c(p)
        await p.send(f"{pc['bright_magenta']}{t.tpl['intro']}{pc['reset']}")
        await _move(p, entrance)
    await gate.send_to_room(f"{c['magenta']}{', '.join(p.name for p in going)} {'vanishes' if len(going) == 1 else 'vanish'} "
                            f"into the banner's light.{c['reset']}")


async def leave_trial(player, quiet=False):
    c = _c(player)
    for run in RUNS.values():
        if _in_trial(player, run):
            if not quiet:
                await player.send(f"{c['magenta']}The vision thins, and you stand at {run.trial.gate.name} again.{c['reset']}")
            await _move(player, run.trial.gate)
            return True
    room = getattr(player, 'room', None)
    out = _room(getattr(room, 'instance_exit', None)) if room is not None else None
    if out is not None:
        await _move(player, out)
        return True
    if not quiet:
        await player.send(f"{c['yellow']}You are not in a trial.{c['reset']}")
    return False


async def _open_gate(t, g):
    import doors
    room = t.rooms[g['room']]
    try:
        doors.apply(room, g['dir'], state='open', locked=False, magically_blocked=None, key_vnum=None)
    except Exception as e:
        logger.debug(f"marquee gate: {e}")
    for r in t.rooms.values():
        await r.send_to_room(g['text'])


async def _close_trial(run, why):
    """The trial ends: everyone in it back at the gate; its rooms leave the world."""
    t = run.trial
    if t is None:
        return
    run.trial = None
    gate = t.gate or _room(3001)
    for room in t.rooms.values():
        for ch in list(room.characters):
            if _is_player(ch):
                await ch.send(f"{_c(ch)['magenta']}The vision of {t.tpl['name']} fades around you.{_c(ch)['reset']}")
                await _move(ch, gate)
            else:
                _remove(ch)
        for obj in list(getattr(room, 'items', None) or []):
            # a fallen hero's corpse (and all it carries) comes out with them
            name = str(getattr(obj, 'name', ''))
            if name.startswith('corpse of ') and name[10:] in t.party:
                gate.items.append(obj)
        room.items = []
    for mob in list(run.mobs):
        if getattr(getattr(mob, 'room', None), 'zone', None) is t.zone or mob.room is None:
            if mob in run.mobs:
                run.mobs.remove(mob)
    for room in t.rooms.values():
        WORLD.rooms.pop(room.vnum, None)
    WORLD.zones.pop(t.zone.number, None)
    try:
        import map_system
        map_system._ZONEMAP_CACHE.pop(t.zone.number, None)
        map_system._ZONECELL_INDEX.pop(t.zone.number, None)
        import web_map
        web_map._zonemap_bytes.pop(t.zone.number, None)
    except Exception:
        pass
    logger.info(f"marquee: trial zone {t.zone.number} closed ({why})")


async def _trial_tick(run, m, now):
    t = run.trial
    inside = [p for p in list(WORLD.players.values()) if getattr(getattr(p, 'room', None), 'zone', None) is t.zone]
    if not inside:
        t.empty_since = t.empty_since or now
        if now - t.empty_since > (5 if t.won else TRIAL_EMPTY):
            await _close_trial(run, 'empty')
        return
    t.empty_since = None
    if t.won:
        if now - t.won > TRIAL_WON:
            await _close_trial(run, 'won')
        return
    if m is None:
        return                      # the owner is away: the trial waits for them
    here = [p for p in inside if _in_party(m, p)]
    waves = t.tpl.get('waves', [])
    n = m.get('n', 1)
    if t.wave < len(waves):
        w = waves[t.wave]
        room = t.rooms[w['room']]
        if not t.placed:
            if any(p.room is room for p in here):
                t.placed = True
                for j, (vnum, count) in enumerate(w['mobs']):
                    for _ in range(count + (ms.extra_adds(n) if j == 0 else 0)):
                        await _place(run, m, vnum, room, 'wave', wave=t.wave)
                await room.send_to_room(f"{_c(here[0])['bright_red']}{w['text']}{_c(here[0])['reset']}")
                await _push_party(m)
        elif not any(_alive(x) and getattr(x, 'marquee_tag', {}).get('wave') == t.wave for x in run.mobs):
            for g in t.tpl.get('gates', []):
                if g.get('after') == t.wave:
                    await _open_gate(t, g)
            t.wave += 1
            t.placed = False
            await _push_party(m)
        return
    b = t.tpl['boss']
    room = t.rooms[b['room']]
    if t.boss is None:
        if any(p.room is room for p in here):
            t.boss = await _place(run, m, b['vnum'], room, 'boss', boss=True)
            if t.boss is not None:
                t.boss._marquee_engage_at = now + 4
            await room.send_to_room(f"{_c(here[0])['bright_red']}{b['text']}{_c(here[0])['reset']}")
            await _push_party(m)
    elif not _alive(t.boss):
        t.won = now
        _clear_mobs(run)
        await _trial_won(run, m)


async def _trial_won(run, m):
    """The boss is down: the helpers are paid now; the owner carries the banner home."""
    q, st = _stage(m)
    owner = _online(run.owner)
    for p in _party(m):
        if p is owner:
            continue
        exp, gold = p.level * 2000, 1500
        try:
            await p.gain_exp(exp, source='quest')
        except TypeError:
            await p.gain_exp(exp)
        p.gold = getattr(p, 'gold', 0) + gold
        await p.send(f"{_c(p)['bright_yellow']}For standing with {run.owner} in {run.trial.tpl['name']} you gain {exp} "
                     f"experience and {gold} gold.{_c(p)['reset']}")
        await _event(p, {'type': 'quest_done', 'quest': q['name'], 'helper': True, 'owner': run.owner})
    if owner is not None:
        await _advance(run, owner, m)
    await _tell(m, 'magenta', "The vision will fade soon — type 'trial leave' to step out now.")


# ---------------------------------------------------------------- the loop
async def _step():
    now = time.time()
    await _votes(now)
    for p in list(WORLD.players.values()):
        m = getattr(p, 'marquee', None)
        if isinstance(m, dict) and m.get('cls') and p.name.lower() not in RUNS:
            RUNS[p.name.lower()] = Run(p.name)
    for key, run in list(RUNS.items()):
        owner = _online(run.owner)
        m = getattr(owner, 'marquee', None) if owner else None
        if not isinstance(m, dict) or not m.get('cls'):
            for mob in _sweep(run):
                await fallen(mob)
            if run.mobs and now - run.seen > AWAY_SECONDS:
                _clear_mobs(run)
            if run.trial is not None:
                await _trial_tick(run, None, now)
            if not run.mobs and run.trial is None:
                RUNS.pop(key, None)
            continue
        q, st = _stage(m)
        if not st:
            continue
        run.party = set(m.get('party') or [])
        party = _party(m)
        for mob in _sweep(run):
            await fallen(mob)
        kind = st['kind']
        if kind == 'talk':
            await _talk_tick(run, m, st, party, now)
        elif kind == 'kill':
            await _kill_tick(run, m, st, party, now)
        elif kind == 'collect':
            await _collect_tick(run, m, st, party, now)
        elif kind == 'ritual':
            await _ritual_tick(run, m, st, party, now)
        if run.trial is not None:
            await _trial_tick(run, m, now)
        if RUNS.get(key) is not run:
            continue
        await _engage(run, m, party, now)
        rooms = {getattr(x, 'room', None) for x in run.mobs}
        if any(p.room in rooms for p in party):
            run.seen = now
        elif run.mobs and now - run.seen > AWAY_SECONDS and run.trial is None:
            _clear_mobs(run)
            run.ritual = None


async def _loop():
    while True:
        await asyncio.sleep(1.0)
        try:
            await _step()
        except Exception:
            logger.exception('marquee tick failed')


# ---------------------------------------------------------------- what the clients see
def _objectives(m, st, run, player=None):
    k = st['kind']
    pr = m.get('progress') or {}
    if k == 'kill':
        dead = pr.get('dead') or [False] * len(st['spawns'])
        return [{'text': sp['label'], 'done': bool(dead[i]) if i < len(dead) else False} for i, sp in enumerate(st['spawns'])]
    if k == 'collect':
        need = _need(m, st)
        return [{'text': f"{st.get('objective', 'Gather')} ({st['item']}s)", 'have': min(pr.get('got', 0), need), 'need': need,
                 'done': pr.get('got', 0) >= need}]
    if k == 'ritual':
        holding = run is not None and run.ritual is not None
        return [{'text': st['objective'], 'have': pr.get('held', 0) if holding else 0, 'need': st['seconds'], 'done': False},
                {'text': 'Slay what comes for it', 'done': False}] if holding else [{'text': st['objective'], 'done': False}]
    if k == 'trial':
        t = run.trial if run is not None else None
        waves = len(_template(st['trial']).get('waves', [])) if t is None else len(t.tpl.get('waves', []))
        boss_name = _npc_name(t.tpl['boss']['vnum']) if t is not None else 'its master'
        got = t.wave if t is not None else 0
        return [{'text': 'Break the siege', 'have': got, 'need': waves, 'done': got >= waves},
                {'text': f"Defeat {boss_name}", 'done': bool(t is not None and t.won)}]
    return [{'text': st.get('objective') or st['title'], 'done': False}]


def _where(m, st, run, player):
    k = st['kind']
    t = run.trial if run is not None else None
    vnum = None
    if t is not None and _in_trial(player, run):
        waves = t.tpl.get('waves', [])
        key = waves[t.wave]['room'] if t.wave < len(waves) else t.tpl['boss']['room']
        vnum = t.rooms[key].vnum
    elif k in ('talk', 'ritual', 'trial'):
        vnum = st['room']
    elif k == 'kill':
        dead = (m.get('progress') or {}).get('dead') or []
        for i, sp in enumerate(st['spawns']):
            if not (i < len(dead) and dead[i]):
                vnum = sp['room']
                break
    elif k == 'collect':
        here = getattr(getattr(player, 'room', None), 'vnum', None)
        vnum = here if here in st['rooms'] else st['rooms'][0]
    elif k == 'return':
        vnum = mq.quest_for(m['cls'])['giver_room']
    room = _room(vnum)
    return {'vnum': vnum, 'name': _where_name(room)} if room is not None else None


def _action(player, m, st, run, role):
    k = st['kind']
    room = getattr(player, 'room', None)
    if run is not None and _in_trial(player, run):
        return {'label': 'Leave the trial', 'cmd': 'trial leave'}
    if k == 'talk' and room is not None and room.vnum == st['room']:
        return {'label': f"Speak with {_npc_name(st['npc'])}", 'cmd': f"talk {_npc_word(st['npc'])}"}
    if k == 'ritual' and role == 'owner' and room is not None and room.vnum == st['room'] and (run is None or run.ritual is None):
        return {'label': st.get('action', 'Begin'), 'cmd': f"marquee {st['verb']}"}
    if k == 'trial' and room is not None and room.vnum == st['room']:
        return {'label': st.get('action', 'Enter the trial'), 'cmd': 'trial enter'}
    if k == 'return' and role == 'owner' and room is not None and room.vnum == mq.quest_for(m['cls'])['giver_room']:
        q = mq.quest_for(m['cls'])
        return {'label': f"Speak with {q['giver_name']}", 'cmd': f"talk {_npc_word(q['giver'])}"}
    return None


def quest_block(player):
    """The marquee quest as the 3D client's tracker shows it (None: no quest)."""
    try:
        owner_name, m, role = quest_of(player)
    except Exception:
        return None
    if not owner_name:
        return None
    if m is None:
        h = getattr(player, 'marquee_help', None) or {}
        cls, q = mq.by_id(h.get('id'))
        return {'id': h.get('id'), 'name': q['name'] if q else 'A marquee quest', 'role': 'helper', 'owner': owner_name,
                'stage': 0, 'of': 0, 'title': f"Waiting for {owner_name}", 'text': f"{owner_name} is away; the quest waits for them.",
                'objectives': [], 'party': []}
    q, st = _stage(m)
    if not st:
        return None
    run = RUNS.get(owner_name.lower())
    b = {'id': q['id'], 'name': q['name'], 'role': role, 'owner': owner_name, 'stage': m['stage'] + 1, 'of': len(q['stages']),
         'title': st['title'], 'text': st['text'], 'objectives': _objectives(m, st, run, player),
         'party': list(m.get('party') or []), 'n': m.get('n', 1), 'kind': st['kind']}
    where = _where(m, st, run, player)
    if where:
        b['where'] = where
    act = _action(player, m, st, run, role)
    if act:
        b['action'] = act
    if st['kind'] == 'trial':
        t = run.trial if run is not None else None
        if _in_trial(player, run):
            b['trial'] = {'state': 'inside', 'wave': min(t.wave + 1, len(t.tpl.get('waves', []))), 'of': len(t.tpl.get('waves', [])),
                          'boss': t.wave >= len(t.tpl.get('waves', []))}
        elif getattr(getattr(player, 'room', None), 'vnum', None) == st['room']:
            b['trial'] = {'state': 'ready'}
    if st['kind'] == 'ritual' and run is not None and run.ritual is not None:
        b['ritual'] = {'seconds': st['seconds'], 'left': max(0, int(st['seconds'] - (time.time() - run.ritual['start'])))}
    return b


def journal_entry(player):
    """The marquee quest as the journal (/quests) lists it."""
    b = quest_block(player)
    if not b:
        return None
    import marquee_abilities as ma
    cls, q = mq.by_id(b['id'])
    return {'id': b['id'], 'name': b['name'], 'marquee': True, 'role': b['role'], 'owner': b['owner'],
            'description': f"{b['title']} — {b['text']}",
            'objectives': [{'description': o['text'], 'current': o.get('have', 1 if o.get('done') else 0),
                            'required': o.get('need', 1), 'completed': bool(o.get('done'))} for o in b.get('objectives', [])],
            'rewards': {}, 'teaches': ma.NAMES.get(q['ability']) if q and b['role'] == 'owner' else None,
            'stage': b['stage'], 'of': b['of'], 'complete': False, 'remaining_min': None}


def indicator(player, npc_vnum):
    """'!' over a guildmaster with a marquee quest for you; '?' over whoever your quest wants
    you to speak with now."""
    owner_name, m, role = quest_of(player)
    if m is not None:
        q, st = _stage(m)
        if st and ((st['kind'] == 'talk' and st['npc'] == npc_vnum) or (st['kind'] == 'return' and role == 'owner' and q['giver'] == npc_vnum)):
            return '?'
        return ''
    if npc_vnum in mq.GIVERS and not owner_name:
        cls = str(getattr(player, 'char_class', '')).lower()
        q = mq.quest_for(cls)
        if q and q['giver'] == npc_vnum and not eligible(player, cls):
            return '!'
    return ''


# ---------------------------------------------------------------- commands
async def cmd_marquee(player, args):
    """Your marquee quest: the last lesson of your class's guildmaster (from level 45).

    marquee              where you are in it
    marquee accept       take it on (beside your guildmaster)
    marquee join|decline answer a group member who embarks on theirs
    marquee go           set out without waiting for your group's answers
    marquee plant        (the warrior's ritual) plant the banner where the quest asks
    marquee abandon      give it up (a helper: stop helping)
    """
    c = _c(player)
    sub = (args[0].lower() if args else 'status')
    rest = [a.lower() for a in args[1:]]
    if sub in ('accept', 'take'):
        return await accept(player)
    if sub in ('join', 'yes'):
        return await answer(player, True)
    if sub in ('decline', 'no'):
        return await answer(player, False)
    if sub == 'go':
        if player.name.lower() in VOTES:
            return await _close_vote(player.name.lower())
        return await player.send(f"{c['yellow']}You are not waiting for anyone.{c['reset']}")
    if sub in ('abandon', 'leave', 'quit'):
        return await abandon(player, confirm='confirm' in rest or 'yes' in rest)
    if sub in ('stage', 'forget') and getattr(player, 'is_immortal', False):
        return await _admin(player, sub, rest)
    owner_name, m, role = quest_of(player)
    q, st = _stage(m) if m else (None, None)
    if st and st['kind'] == 'ritual' and sub == st.get('verb'):
        return await plant(player)
    if sub in ('plant',):
        return await plant(player)
    if not owner_name:
        cls = str(getattr(player, 'char_class', '')).lower()
        q = mq.quest_for(cls)
        if q and not eligible(player, cls):
            return await player.send(f"{c['cyan']}{q['giver_name'][:1].upper() + q['giver_name'][1:]} has one last lesson for you: "
                                     f"{q['name']}. Speak with them at {_where_name(_room(q['giver_room']))}.{c['reset']}")
        return await player.send(f"{c['yellow']}You are on no marquee quest.{c['reset']}")
    if m is None:
        return await player.send(f"{c['yellow']}You share {owner_name}'s quest; it waits until they return.{c['reset']}")
    b = quest_block(player)
    await player.send(f"{c['bright_yellow']}★ {b['name']} — {b['title']} ({b['stage']}/{b['of']}){c['reset']}")
    await player.send(f"{c['white']}{b['text']}{c['reset']}")
    for o in b['objectives']:
        mark = '✔' if o.get('done') else '•'
        count = f" ({o.get('have', 0)}/{o['need']})" if o.get('need', 1) > 1 else ''
        await player.send(f"  {c['green'] if o.get('done') else c['white']}{mark} {o['text']}{count}{c['reset']}")
    if b.get('where'):
        await player.send(f"{c['cyan']}Where: {b['where']['name']}{c['reset']}")
    hint = _hint(m, st)
    if _in_trial(player, RUNS.get(owner_name.lower())):
        hint = "Type 'trial leave' to step out (the trial waits ten minutes for you)."
    if hint and st['kind'] in ('ritual', 'trial', 'return', 'talk'):
        await player.send(f"{c['cyan']}{hint}{c['reset']}")
    others = [x for x in m.get('party', []) if x != player.name]
    await player.send(f"{c['cyan']}{'Alone' if m.get('n', 1) == 1 else str(m['n']) + ' embarked'}"
                      f"{(' — with ' + ', '.join(others)) if others else ''}.{c['reset']}")


async def _admin(player, sub, rest):
    """Testing: `marquee stage <n>` jumps your quest to stage n; `marquee forget` unlearns the
    marquee ability and clears the quest and its cooldown."""
    c = _c(player)
    m = getattr(player, 'marquee', None)
    if sub == 'forget':
        if isinstance(m, dict):
            await end(player, m)
        cls = str(player.char_class).lower()
        q = mq.quest_for(cls)
        if q:
            player.skills.pop(q['ability'], None)
            player.spells.pop(q['ability'], None)
            (getattr(player, 'marquee_cd', None) or {}).pop(q['ability'], None)
        await player.send(f"{c['cyan']}Your marquee quest and ability are forgotten.{c['reset']}")
        return await _push(player)
    if not isinstance(m, dict) or not rest or not rest[0].isdigit():
        return await player.send(f"{c['yellow']}Usage: marquee stage <n> (on a marquee quest).{c['reset']}")
    q, st = _stage(m)
    i = max(1, min(len(q['stages']), int(rest[0]))) - 1
    run = _run(player.name)
    _clear_mobs(run)
    run.ritual = None
    if run.trial is not None and q['stages'][i]['kind'] != 'trial':
        await _close_trial(run, 'admin')
    m['stage'] = i
    m['progress'] = {}
    await player.send(f"{c['cyan']}Your quest jumps to stage {i + 1}.{c['reset']}")
    await _announce(m)
    await _push_party(m)


async def cmd_trial(player, args):
    """The marquee quest's private trial.

    trial enter   step into it (at the place your quest names; your party beside you comes too)
    trial leave   step out of it, back where you came in
    """
    sub = (args[0].lower() if args else 'enter')
    if sub in ('leave', 'exit', 'out'):
        return await leave_trial(player)
    return await enter_trial(player)


# ---------------------------------------------------------------- install
def install(world):
    """Wire the marquee quests into the game: talk, deaths, damage, the commands, the loop."""
    global WORLD
    WORLD = world
    from commands import CommandHandler
    from combat import CombatHandler
    from mobs import Mobile

    orig_talk = CommandHandler.cmd_talk.__func__

    async def cmd_talk(cls, player, args):
        result = await orig_talk(cls, player, args)
        try:
            await on_talk(player, _target_of(player, args))
        except Exception:
            logger.exception('marquee talk failed')
        return result
    cmd_talk.__doc__ = orig_talk.__doc__
    CommandHandler.cmd_talk = classmethod(cmd_talk)

    orig_death = CombatHandler.handle_death.__func__

    async def handle_death(cls, killer, victim, *a, **k):
        tagged = getattr(victim, 'marquee_tag', None) is not None and not getattr(victim, '_marquee_counted', False)
        result = await orig_death(cls, killer, victim, *a, **k)
        if tagged and not _alive(victim):
            try:
                await fallen(victim, killer)
            except Exception:
                logger.exception('marquee kill credit failed')
        return result
    CombatHandler.handle_death = classmethod(handle_death)

    orig_td = Mobile.take_damage

    async def take_damage(self, amount, *args, **kwargs):
        tag = getattr(self, 'marquee_tag', None)
        if tag and amount and amount > 0:
            attacker = kwargs.get('attacker', args[0] if args else None)
            hero = _hero_of(attacker)
            if hero is not None:
                if not can_touch(hero, self):
                    if getattr(self, 'fighting', None) in (hero, attacker):
                        self.fighting = None
                    for ch in (hero, attacker):
                        if getattr(ch, 'fighting', None) is self:
                            ch.fighting = None
                    if time.time() - getattr(hero, '_marquee_said', 0) > 8:
                        hero._marquee_said = time.time()
                        c = _c(hero)
                        await hero.send(f"{c['yellow']}{self.short_desc[:1].upper()}{self.short_desc[1:]} belongs to "
                                        f"{tag.get('owner', 'another').capitalize()}'s quest — your blows pass through it.{c['reset']}")
                    return False
        return await orig_td(self, amount, *args, **kwargs)
    Mobile.take_damage = take_damage

    from quests import QuestManager
    orig_ind = QuestManager.get_quest_giver_indicator

    def get_quest_giver_indicator(player, npc_vnum):
        r = orig_ind(player, npc_vnum)
        if r:
            return r
        try:
            return indicator(player, npc_vnum)
        except Exception:
            return ''
    QuestManager.get_quest_giver_indicator = staticmethod(get_quest_giver_indicator)

    for name, fn in (('marquee', cmd_marquee), ('trial', cmd_trial)):
        def make(fn):
            async def run(cls, player, args):
                return await fn(player, args)
            run.__doc__ = fn.__doc__
            return run
        setattr(CommandHandler, f'cmd_{name}', classmethod(make(fn)))
    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        logger.warning('marquee: no running loop; the quest tick is not running')
    logger.info(f"marquee quests installed: {', '.join(q['name'] for q in mq.QUESTS.values())}")
