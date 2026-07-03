"""
Room-environment gameplay
=========================
The world itself becomes part of a fight:

- ENV TAGS: each room derives once from its prose/sector what it contains —
  water, fire, webs. These power everything below.
- FLOOR TRAPS: dangerous areas seed hidden traps (spike / snare / gas).
  search / detect traps reveals them, disarm removes them (thief bonus),
  walking in blind risks springing them. Deadly variants only where the room
  is already flagged hostile. Thieves lay caltrops, rangers lay snares that
  catch the next hostile that blunders in.
- HAZARD SHOVES: heavy blows (bash, charge, a mob's Crushing Blow) can knock
  the victim into the room's water / fire / an armed trap. Fully symmetric.
- ELEMENTAL TERRAIN: fire spells ignite webbed rooms (burning field), frost
  freezes water (the client renders walkable ice), lightning cast in a water
  room splashes everyone standing in the fight.

Server owns hazard LOGIC; the web client owns hazard GEOMETRY (it renders
markers/ice/embers from the payload). Telnet players get the same game via
messages and the same commands.
"""

import random
import re
import time
import logging

logger = logging.getLogger('Misthollow.Environment')

WATER_RE = re.compile(r'\b(stream|river|brook|creek|pond|pool|lake|spring|fountain|waterfall)\b', re.I)
FIRE_RE = re.compile(r'\b(brazier|campfire|forge|hearth|furnace|bonfire|firepit|flames?)\b', re.I)
WEB_RE = re.compile(r'\b(cobwebs?|webs?|webbing)\b', re.I)
BRAMBLE_RE = re.compile(r'\b(brambles?|thorns?|briars?|nettles?)\b', re.I)
LEDGE_RE = re.compile(r'\b(cliff|ledge|chasm|precipice|ravine|drop-?off)\b', re.I)
TRAPPY_RE = re.compile(r'dungeon|crypt|mine|sewer|tomb|lair|cave|catacomb|ruin|warren', re.I)

# rooms burning right now (fire spread), ticked from world.combat_tick
_burning_rooms = set()


def _seed(vnum: int) -> int:
    return ((vnum * 2654435761) ^ 0x5eed) & 0xffffffff


def get_env(room) -> dict:
    """Derive (and cache) the room's environmental tags."""
    env = getattr(room, '_env', None)
    if env is not None:
        return env
    text = f"{getattr(room, 'name', '')} {getattr(room, 'description', '')}"
    sector = getattr(room, 'sector_type', '')
    env = {
        'water': bool(WATER_RE.search(text)) or sector in ('water_swim', 'water_noswim', 'underwater'),
        'fire': bool(FIRE_RE.search(text)),
        'webbed': bool(WEB_RE.search(text)),
        'brambles': bool(BRAMBLE_RE.search(text)),
        'ledge': bool(LEDGE_RE.search(text)) or sector == 'mountain' and 'cliff' in text.lower(),
    }
    room._env = env
    return env


# ---------------------------------------------------------------------------
# World traps
# ---------------------------------------------------------------------------

TRAP_KINDS = ('spike', 'snare', 'gas')
TRAP_NAMES = {'spike': 'a spike trap', 'snare': 'a snare', 'gas': 'a gas vent'}


def get_trap(room):
    """The room's world trap dict, or None. Seeded by vnum: dangerous-sounding
    zones grow traps deterministically. Lazily created and cached."""
    if hasattr(room, 'trap'):
        return room.trap
    trap = None
    vnum = getattr(room, 'vnum', 0)
    zone_name = str(getattr(getattr(room, 'zone', None), 'name', '') or '')
    text = f"{zone_name} {getattr(room, 'name', '')}"
    flags = getattr(room, 'flags', set()) or set()
    trappy = 'trapped' in flags or TRAPPY_RE.search(text)
    if trappy and 'peaceful' not in flags:
        s = _seed(vnum)
        if s % 100 < 16:   # ~1 in 6 dangerous rooms carries a trap
            kind = TRAP_KINDS[(s >> 8) % len(TRAP_KINDS)]
            deadly = 'trapped' in flags or (s >> 16) % 100 < 8   # rare, where it fits
            trap = {'kind': kind, 'deadly': deadly, 'disarmed': False, 'sprung_until': 0}
    room.trap = trap
    return trap


def trap_detected(player, room) -> bool:
    return (getattr(room, 'vnum', 0)) in getattr(player, 'detected_traps', set())


def _mark_detected(player, room):
    if not hasattr(player, 'detected_traps'):
        player.detected_traps = set()
    player.detected_traps.add(getattr(room, 'vnum', 0))


async def spring_trap(room, victim, trap=None, forced=False):
    """The trap goes off on the victim. Used by walk-ins and hazard shoves."""
    trap = trap or get_trap(room)
    if not trap or trap['disarmed']:
        return False
    now = time.time()
    if not forced and now < trap['sprung_until']:
        return False
    trap['sprung_until'] = now + 30   # doesn't shred corpse runs
    from config import Config
    c = Config.COLORS
    name = getattr(victim, 'name', 'Someone')
    max_hp = max(1, getattr(victim, 'max_hp', 1))
    killed = False
    if trap['kind'] == 'spike':
        frac = (0.45 + random.random() * 0.2) if trap['deadly'] else (0.10 + random.random() * 0.08)
        dmg = max(3, int(max_hp * frac))
        await room.send_to_room(
            f"{c['bright_red']}⚠ SHUNK! Iron spikes burst from the ground beneath {name}! [{dmg}]{c['reset']}"
        )
        killed = await victim.take_damage(dmg, None)
    elif trap['kind'] == 'snare':
        victim.stunned_rounds = getattr(victim, 'stunned_rounds', 0) + 2
        await room.send_to_room(
            f"{c['bright_yellow']}⚠ A hidden snare whips tight around {name}'s legs — held fast!{c['reset']}"
        )
    else:   # gas
        dmg = max(2, int(max_hp * (0.20 if trap['deadly'] else 0.06)))
        try:
            from affects import AffectManager
            AffectManager.apply_affect(victim, {
                'name': 'poison', 'type': AffectManager.TYPE_DOT, 'applies_to': 'hp',
                'value': max(2, dmg // 3), 'duration': 4, 'caster_level': 10,
            })
        except Exception:
            pass
        await room.send_to_room(
            f"{c['green']}⚠ A vent hisses — {name} is engulfed in noxious gas! [{dmg}]{c['reset']}"
        )
        killed = await victim.take_damage(dmg, None)
    if killed and hasattr(victim, 'die'):
        try:
            await victim.die(None)
        except Exception:
            pass
    return True


async def on_player_enter(player, room):
    """Walk-in trap logic: passive spotting, careful steps, or a sprung trap."""
    # a trapsmith's rig checks first — it was made for exactly this moment
    try:
        await check_mob_traps(player, room)
    except Exception:
        pass
    trap = get_trap(room)
    if not trap or trap['disarmed']:
        return
    c = player.config.COLORS
    if trap_detected(player, room):
        await player.send(f"{c['cyan']}You step carefully around {TRAP_NAMES[trap['kind']]}.{c['reset']}")
        return
    # rogues' eyes: passive chance to spot on entry
    spot = getattr(player, 'skills', {}).get('detect_traps', 0) // 2
    if spot and random.randint(1, 100) <= spot:
        _mark_detected(player, room)
        await player.send(
            f"{c['bright_cyan']}Your trained eye catches {TRAP_NAMES[trap['kind']]} hidden here! "
            f"(step around it, or DISARM it){c['reset']}"
        )
        return
    if random.randint(1, 100) <= 55:
        await spring_trap(room, player, trap)


async def search_reveal(player, room) -> str:
    """Called from search / detect traps: reveal the room's trap if present."""
    trap = get_trap(room)
    mob_rigs = [t for t in getattr(room, 'mob_traps', []) or [] if t['until'] > time.time()]
    if (not trap or trap['disarmed'] or trap_detected(player, room)) and not mob_rigs:
        return None
    if mob_rigs and not trap_detected(player, room):
        _mark_detected(player, room)
        return f"{mob_rigs[0]['owner']}'s crude {mob_rigs[0]['kind']} rig (DISARM it, or step around it)"
    if not trap or trap['disarmed'] or trap_detected(player, room):
        return None
    _mark_detected(player, room)
    return f"{TRAP_NAMES[trap['kind']]}{' — it looks LETHAL' if trap['deadly'] else ''} (DISARM it, or lure a foe onto it)"


async def disarm_trap(player, room):
    """Disarm the room's detected trap (a trapsmith's rig first, then the
    world trap). Thieves shine at this."""
    from config import Config
    c = Config.COLORS
    # a spotted mob rig comes apart easily — it's crude work
    mob_rigs = [t for t in getattr(room, 'mob_traps', []) or [] if t['until'] > time.time()]
    if mob_rigs and trap_detected(player, room):
        room.mob_traps = []
        player.trap_parts = getattr(player, 'trap_parts', 0) + 1
        await player.send(
            f"{c['bright_green']}You pull apart {mob_rigs[0]['owner']}'s crude rig and pocket a trap part "
            f"({player.trap_parts} carried).{c['reset']}"
        )
        return
    trap = get_trap(room)
    if not trap or trap['disarmed']:
        await player.send(f"{c['yellow']}There's no armed trap here.{c['reset']}")
        return
    if not trap_detected(player, room):
        await player.send(f"{c['yellow']}You don't see a trap here... yet. Try SEARCH.{c['reset']}")
        return
    skill = getattr(player, 'skills', {}).get('detect_traps', 0)
    chance = min(95, 35 + skill + (getattr(player, 'dex', 10) - 10) * 2)
    if random.randint(1, 100) <= chance:
        trap['disarmed'] = True
        parts = 2 if trap['deadly'] else 1
        player.trap_parts = getattr(player, 'trap_parts', 0) + parts
        await player.send(
            f"{c['bright_green']}Click. You carefully disarm {TRAP_NAMES[trap['kind']]} "
            f"and salvage {parts} trap part{'s' if parts > 1 else ''} ({player.trap_parts} carried) — "
            f"your own traps grow nastier.{c['reset']}"
        )
        if room:
            await room.send_to_room(f"{player.name} disarms a hidden trap.", exclude=[player])
        if skill and hasattr(player, 'improve_skill'):
            await player.improve_skill('detect_traps', difficulty=2)
        if hasattr(player, 'gain_exp'):
            try:
                await player.gain_exp(15 + (10 if trap['deadly'] else 0))
            except Exception:
                pass
    else:
        await player.send(f"{c['yellow']}Your hand slips —{c['reset']}")
        await spring_trap(room, player, trap, forced=True)


# ---------------------------------------------------------------------------
# Mob-laid traps: trapsmiths (kobolds, trappers...) rig their lairs while
# idle — and the trap they rigged is a trap YOU can spot, disarm, or shove
# them onto. Fair's fair.
# ---------------------------------------------------------------------------

async def mob_rig_trap(mob, room):
    """A trapsmith rigs a snare/spike in its room (one per room)."""
    traps = getattr(room, 'mob_traps', None)
    if traps is None:
        traps = room.mob_traps = []
    if traps:
        return False
    kind = random.choice(('snare', 'spike'))
    traps.append({'owner': getattr(mob, 'name', 'something'), 'kind': kind, 'until': time.time() + 900})
    from config import Config
    c = Config.COLORS
    if any(hasattr(ch, 'connection') for ch in getattr(room, 'characters', [])):
        await room.send_to_room(f"{c['yellow']}{mob.name} fiddles with something low to the ground...{c['reset']}")
    return True


async def check_mob_traps(player, room):
    """A player blunders into a trapsmith's rig on entry (DEX helps)."""
    traps = getattr(room, 'mob_traps', None)
    if not traps:
        return False
    now = time.time()
    room.mob_traps = [t for t in traps if t['until'] > now]
    if not room.mob_traps:
        return False
    if room.vnum in getattr(player, 'detected_traps', set()):
        return False   # spotted rigs get stepped around (search covers both)
    dodge = min(60, (getattr(player, 'dex', 10) - 10) * 3 + getattr(player, 'skills', {}).get('detect_traps', 0) // 3)
    if random.randint(1, 100) <= dodge:
        return False
    t = room.mob_traps.pop(0)
    from config import Config
    c = Config.COLORS
    if t['kind'] == 'snare':
        player.stunned_rounds = getattr(player, 'stunned_rounds', 0) + 1
        await room.send_to_room(
            f"{c['bright_yellow']}⚠ {t['owner']}'s hidden snare snaps around {player.name}'s ankle!{c['reset']}"
        )
    else:
        dmg = max(2, int(getattr(player, 'max_hp', 10) * 0.08))
        await room.send_to_room(
            f"{c['bright_red']}⚠ SHUNK! {t['owner']}'s spike rig bites into {player.name}! [{dmg}]{c['reset']}"
        )
        if await player.take_damage(dmg, None) and hasattr(player, 'die'):
            try:
                await player.die(None)
            except Exception:
                pass
    return True


# ---------------------------------------------------------------------------
# Player-laid traps (thief caltrops / ranger snares)
# ---------------------------------------------------------------------------

async def lay_trap(player, kind):
    from config import Config
    c = Config.COLORS
    room = player.room
    if not room:
        return
    traps = getattr(room, 'player_traps', None)
    if traps is None:
        traps = room.player_traps = []
    if any(t['owner'] == player.name for t in traps):
        await player.send(f"{c['yellow']}You've already prepared a trap here.{c['reset']}")
        return
    # salvaged trap parts make your traps meaner (up to 2 consumed per trap)
    spend = min(2, getattr(player, 'trap_parts', 0))
    if spend:
        player.trap_parts -= spend
    potency = 1 + spend
    traps.append({'owner': player.name, 'kind': kind, 'until': time.time() + 300, 'potency': potency})
    verb = 'scatter a handful of caltrops across the ground' if kind == 'caltrops' \
        else 'rig a spring-snare across the approach'
    extra = f" (reinforced with {spend} salvaged part{'s' if spend > 1 else ''})" if spend else ''
    await player.send(f"{c['bright_green']}You {verb}{extra}. The next hostile through here is in for a surprise.{c['reset']}")
    await room.send_to_room(f"{player.name} rigs something low to the ground...", exclude=[player])


async def check_player_traps(mob, room):
    """A hostile mob blunders into a player-laid trap (on aggro/each round)."""
    traps = getattr(room, 'player_traps', None)
    if not traps:
        return False
    now = time.time()
    room.player_traps = [t for t in traps if t['until'] > now]
    if not room.player_traps:
        return False
    t = room.player_traps.pop(0)   # consumed
    from config import Config
    c = Config.COLORS
    potency = t.get('potency', 1)
    if t['kind'] == 'caltrops':
        dmg = max(2, int(getattr(mob, 'max_hp', 10) * (0.03 + 0.04 * potency)))
        mob.stunned_rounds = getattr(mob, 'stunned_rounds', 0) + 1
        await room.send_to_room(
            f"{c['bright_yellow']}⚠ {mob.name} stamps onto {t['owner']}'s caltrops — hobbled! [{dmg}]{c['reset']}"
        )
        if await mob.take_damage(dmg, None):
            return True
    else:   # snare
        mob.stunned_rounds = getattr(mob, 'stunned_rounds', 0) + 1 + potency
        mob.pending_intent = None
        await room.send_to_room(
            f"{c['bright_yellow']}⚠ {t['owner']}'s snare snaps shut — {mob.name} is yanked off its feet!{c['reset']}"
        )
    return True


# ---------------------------------------------------------------------------
# Hazard shoves — heavy blows use the room, both directions
# ---------------------------------------------------------------------------

async def try_shove(attacker, victim, room):
    """A heavy hit may knock the victim into the room's hazard (35%)."""
    if not room or random.random() > 0.35:
        return False
    env = get_env(room)
    from config import Config
    c = Config.COLORS
    name = getattr(victim, 'name', 'Someone')
    options = []
    if env['water']:
        options.append('water')
    if env['fire'] or getattr(room, 'burning_until', 0) > time.time():
        options.append('fire')
    if env['ledge']:
        options.append('ledge')
    trap = get_trap(room)
    if trap and not trap['disarmed'] and time.time() >= trap['sprung_until']:
        options.append('trap')
    # a trapsmith's own rig makes a fine landing spot too
    if [t for t in getattr(room, 'mob_traps', []) or [] if t['until'] > time.time()]:
        options.append('mobtrap')
    if not options:
        return False
    what = random.choice(options)
    if what == 'water':
        if getattr(room, 'frozen_until', 0) > time.time():
            return False   # the water is ice right now
        dmg = max(2, int(getattr(victim, 'max_hp', 10) * 0.04))
        await room.send_to_room(
            f"{c['bright_cyan']}💦 The blow sends {name} sprawling into the water! [{dmg}]{c['reset']}"
        )
        if hasattr(victim, 'fire_aura'):
            victim.fire_aura = False
        if await victim.take_damage(dmg, attacker):
            from combat import CombatHandler
            await CombatHandler.handle_death(attacker, victim)
    elif what == 'fire':
        dmg = max(3, int(getattr(victim, 'max_hp', 10) * 0.07))
        await room.send_to_room(
            f"{c['bright_red']}🔥 The blow knocks {name} into the flames! [{dmg}]{c['reset']}"
        )
        try:
            from affects import AffectManager
            AffectManager.apply_affect(victim, {
                'name': 'burning', 'type': AffectManager.TYPE_DOT, 'applies_to': 'hp',
                'value': max(2, dmg // 3), 'duration': 3, 'caster_level': 10,
            })
        except Exception:
            pass
        if await victim.take_damage(dmg, attacker):
            from combat import CombatHandler
            await CombatHandler.handle_death(attacker, victim)
    elif what == 'ledge':
        # over the edge: the big one — scraped down the rocks and left reeling
        dmg = max(4, int(getattr(victim, 'max_hp', 10) * 0.12))
        victim.stunned_rounds = getattr(victim, 'stunned_rounds', 0) + 1
        await room.send_to_room(
            f"{c['bright_red']}🪨 The blow sends {name} over the ledge — a sickening scrape down the rocks! [{dmg}]{c['reset']}"
        )
        if await victim.take_damage(dmg, attacker):
            from combat import CombatHandler
            await CombatHandler.handle_death(attacker, victim)
    elif what == 'mobtrap':
        t = room.mob_traps.pop(0)
        dmg = max(2, int(getattr(victim, 'max_hp', 10) * 0.08))
        await room.send_to_room(
            f"{c['bright_yellow']}The blow drives {name} straight onto {t['owner']}'s own rig! [{dmg}]{c['reset']}"
        )
        if t['kind'] == 'snare':
            victim.stunned_rounds = getattr(victim, 'stunned_rounds', 0) + 1
        if await victim.take_damage(dmg, attacker):
            from combat import CombatHandler
            await CombatHandler.handle_death(attacker, victim)
    else:
        await room.send_to_room(
            f"{c['bright_yellow']}The blow drives {name} straight onto the hidden trap!{c['reset']}"
        )
        await spring_trap(room, victim, trap, forced=True)
    return True


# ---------------------------------------------------------------------------
# Elemental terrain interplay
# ---------------------------------------------------------------------------

FIRE_SPELL = re.compile(r'fire|burn|flame|meteor|combust|immolat|pyro', re.I)
FROST_SPELL = re.compile(r'frost|\bice\b|chill|rime|blizzard|freez', re.I)
BOLT_SPELL = re.compile(r'lightning|shock|storm|thunder|chain', re.I)


async def elemental_cast(caster, target, spell_name, room=None):
    """Spells interact with what the room is made of."""
    room = room or getattr(caster, 'room', None)
    if not room:
        return
    env = get_env(room)
    now = time.time()
    from config import Config
    c = Config.COLORS
    sp = str(spell_name or '')
    if FIRE_SPELL.search(sp) and env['webbed'] and getattr(room, 'burning_until', 0) <= now:
        room.burning_until = now + 16   # ~4 rounds of burning webs
        _burning_rooms.add(room)
        await room.send_to_room(
            f"{c['bright_red']}🔥 The webs catch — in a heartbeat the whole chamber is BURNING!{c['reset']}"
        )
    elif FROST_SPELL.search(sp) and env['water'] and getattr(room, 'frozen_until', 0) <= now:
        room.frozen_until = now + 120
        await room.send_to_room(
            f"{c['bright_cyan']}❄ The water crackles and stills — frozen into a sheet of ice!{c['reset']}"
        )
    elif BOLT_SPELL.search(sp) and env['water'] and getattr(room, 'frozen_until', 0) <= now:
        # everyone standing in the fight takes the splash — allies included
        splash = max(3, int(getattr(caster, 'level', 5) * 1.5))
        await room.send_to_room(
            f"{c['bright_cyan']}⚡ The bolt arcs through the water — the whole pool LIGHTS UP!{c['reset']}"
        )
        for ch in list(getattr(room, 'characters', [])):
            if ch is caster or ch is target:
                continue
            if not getattr(ch, 'fighting', None):
                continue
            if hasattr(ch, 'send'):
                await ch.send(f"{c['bright_cyan']}Electricity surges up through the water! [{splash}]{c['reset']}")
            try:
                if await ch.take_damage(splash, caster):
                    from combat import CombatHandler
                    await CombatHandler.handle_death(caster, ch)
            except Exception:
                pass


async def heavy_impact(room):
    """A heavy/area blow landed in this room: frozen ice can SHATTER under
    the fight, dumping everyone standing on it back into freezing water."""
    now = time.time()
    if getattr(room, 'frozen_until', 0) <= now or random.random() > 0.30:
        return False
    room.frozen_until = 0
    from config import Config
    c = Config.COLORS
    await room.send_to_room(
        f"{c['bright_cyan']}❄💥 The ice SHATTERS under the impact — freezing water swallows the footing!{c['reset']}"
    )
    for ch in list(getattr(room, 'characters', [])):
        if not getattr(ch, 'fighting', None):
            continue
        dmg = max(2, int(getattr(ch, 'max_hp', 10) * 0.06))
        try:
            if hasattr(ch, 'send'):
                await ch.send(f"{c['bright_cyan']}You crash through into the freezing water! [{dmg}]{c['reset']}")
            if await ch.take_damage(dmg, None) and hasattr(ch, 'die'):
                await ch.die(None)
        except Exception:
            pass
    return True


async def tick(world):
    """Per-combat-round upkeep: burning rooms cook everyone inside, brambles
    bleed whoever fights among them, rain douses open flames."""
    now = time.time()
    from config import Config
    c = Config.COLORS
    # brambles: fighting in a thorn patch costs blood — everyone's blood
    for p in list(getattr(world, 'players', {}).values()):
        room = getattr(p, 'room', None)
        if not room or not getattr(p, 'fighting', None):
            continue
        if not get_env(room)['brambles']:
            continue
        if getattr(room, '_bramble_tick', 0) > now - 3.5:
            continue   # once per round per room
        room._bramble_tick = now
        for ch in list(getattr(room, 'characters', [])):
            if not getattr(ch, 'fighting', None):
                continue
            dmg = max(1, int(getattr(ch, 'max_hp', 10) * 0.02))
            try:
                if hasattr(ch, 'send'):
                    await ch.send(f"{c['green']}🌿 The thorns rake you as you fight! [{dmg}]{c['reset']}")
                if await ch.take_damage(dmg, None) and hasattr(ch, 'die'):
                    await ch.die(None)
            except Exception:
                pass
    for room in list(_burning_rooms):
        # rain douses open flames outdoors
        try:
            weather = getattr(getattr(room, 'zone', None), 'weather', None)
            precip = getattr(weather, 'precipitation', 'none') if weather else 'none'
            if precip and precip != 'none' and random.random() < 0.4:
                room.burning_until = 0
                _burning_rooms.discard(room)
                await room.send_to_room(f"{c['cyan']}The rain hisses down — the flames are doused.{c['reset']}")
                continue
        except Exception:
            pass
        if getattr(room, 'burning_until', 0) <= now:
            _burning_rooms.discard(room)
            try:
                await room.send_to_room(f"{c['yellow']}The flames gutter out, leaving scorched strands.{c['reset']}")
            except Exception:
                pass
            continue
        for ch in list(getattr(room, 'characters', [])):
            dmg = max(2, int(getattr(ch, 'max_hp', 10) * 0.05))
            try:
                if hasattr(ch, 'send'):
                    await ch.send(f"{c['bright_red']}The burning room sears you! [{dmg}]{c['reset']}")
                if await ch.take_damage(dmg, None) and hasattr(ch, 'die'):
                    await ch.die(None)
            except Exception:
                pass


def env_public(room, player=None) -> dict:
    """Environment block for the web payload."""
    env = get_env(room)
    now = time.time()
    trap = get_trap(room)
    out = {
        'water': env['water'], 'fire': env['fire'], 'webbed': env['webbed'],
        'brambles': env['brambles'], 'ledge': env['ledge'],
        'burning': getattr(room, 'burning_until', 0) > now,
        'frozen': getattr(room, 'frozen_until', 0) > now,
        'ptraps': len([t for t in getattr(room, 'player_traps', []) or [] if t['until'] > now]),
    }
    if trap and not trap['disarmed']:
        out['trap'] = {
            'kind': trap['kind'], 'deadly': trap['deadly'],
            'detected': bool(player and trap_detected(player, room)),
        }
    elif [t for t in getattr(room, 'mob_traps', []) or [] if t['until'] > now]:
        out['trap'] = {
            'kind': 'rig', 'deadly': False,
            'detected': bool(player and trap_detected(player, room)),
        }
    return out
