"""Procs: what worn gear does by itself in a fight (Push 32).

Every source speaks one language here, a proc being {type, effect, chance, damage?, value?}:
  - legendaries (legendary.py LEGENDARY_ITEMS) carry theirs as `procs`;
  - zone items name theirs other ways, read once per item (derived_procs): a spell-named affect
    (vampiric_touch, poison_cloud, ice_blast, turn_undead), a life_drain stat, a special
    property (undead_bane, chaos / random_damage_type), a flaming, frost or shocking weapon;
  - a named set gives one at four pieces worn (sets.NAMED_SETS[...]['procs']).

  on_hit     every weapon blow a player lands (combat.py: the main swing, the extra swings and
             haste, the off-hand, a cleave or circle); spells and abilities don't. A weapon's own
             procs fire only on its own blows; the rest of what is worn on any of them.
  on_kill    when the wearer wins a fight (combat.py handle_death)
  on_defend  when a blow lands on the wearer (Player.take_damage), and the killing blow that a
             cocoon turns aside once a day (cheat_death)
  on_equip   a standing bonus counted with the rest of the gear (equip_totals ->
             Player._gear_totals): damage %, all stats, stealth, sight, travel speed, fire ward

Each proc has its chance, damage that grows with the item's level (a legendary names its own),
a school that worn resistances answer to, and a short cooldown per item. A chain or a splash
finds only the wearer's foes (SpellHandler.foes_in_room). The room reads one line; the 3D client
gets a 'proc' event and draws a burst in the school's colour (combat.js). Creatures' gear doesn't
proc: their fights are tuned without it.
"""
import logging
import random
import time

logger = logging.getLogger('Misthollow')

COOLDOWN = 1.0          # seconds before one item's proc can fire again
DERIVED_CHANCE = 10     # a zone item's proc: percent of blows
SET_CHANCE = 8          # a set's four-piece proc
CHAOS_SCHOOLS = ('fire', 'frost', 'lightning', 'arcane', 'shadow', 'holy', 'poison')

# effect -> how it lands. school: what resists it ('physical' is a blow); look: its colour in 3D
# when that differs; kind: hit, drain (heals the wearer), chain (half to one more foe), splash (a
# third to every other foe), cloud (half to every other foe), slow, root, stun; undead: only on
# the undead; chaos: a random school. {t} the target, {n} the amount.
ON_HIT = {
    'phantom_drown': dict(name='Phantom Drowning', school='physical', look='frost', kind='stun',
                          you="🌊 Phantom water fills {t}'s lungs — they choke and stagger! [{n}]",
                          them="🌊 You hear the roar of a drowned ocean — water that isn't there floods your throat! [{n}]"),
    'gravity_crush': dict(name='Gravity Crush', school='arcane', kind='hit',
                          you="◉ Gravity inverts around {t} — their bones groan under impossible weight! [{n}]",
                          them="◉ The world crushes inward — gravity itself rejects you! [{n}]"),
    'memory_wound': dict(name='Memory Wound', school='arcane', kind='hit',
                         you="✧ The blade cuts through {t}'s memories — old wounds reopen! [{n}]",
                         them="✧ Every scar you've ever earned splits open at once! [{n}]"),
    'echo_shatter': dict(name='Echo Shatter', school='sound', kind='chain',
                         you="🔔 A single perfect note shatters the air around {t}! [{n}]",
                         them="🔔 A sound beyond hearing splits your skull from the inside! [{n}]"),
    'rust_devour': dict(name='Rust Devour', school='disease', kind='hit',
                        you="🦠 Rust crawls across {t}'s flesh like a living infection! [{n}]",
                        them="🦠 Your skin oxidizes and flakes — you're rusting alive! [{n}]"),
    'glass_splinter': dict(name='Glass Splinter', school='physical', look='arcane', kind='splash',
                           you="🔷 Glass shards erupt from {t}'s own reflection! [{n}]",
                           them="🔷 Your reflection shatters outward — glass bites into your flesh! [{n}]"),
    'hunger_drain': dict(name='Hunger Drain', school='necrotic', kind='drain',
                         you="👁 The blade feeds — {t}'s vitality pours into you! [{n}]",
                         them="👁 Something hollow and starving reaches through the wound and pulls! [{n}]"),
    'clockwork_unwind': dict(name='Clockwork Unwind', school='arcane', kind='slow',
                             you="⚙ Gears grind — {t}'s movements stutter and unwind! [{n}]",
                             them="⚙ Your joints lock, your muscles seize — time runs backward through your body! [{n}]"),
    'root_pierce': dict(name='Root Pierce', school='nature', kind='root',
                        you="🌿 Barbed roots erupt from the wound and burrow deeper into {t}! [{n}]",
                        them="🌿 Roots burst from the wound and pin you where you stand! [{n}]"),
    'void_cut': dict(name='Void Cut', school='shadow', kind='hit',
                     you="⊘ The blade cuts a seam in reality — {t} bleeds into the void! [{n}]",
                     them="⊘ A wound opens that leads nowhere — your essence leaks into emptiness! [{n}]"),
    'dream_fracture': dict(name='Dream Fracture', school='arcane', kind='hit',
                           you="💤 {t} flickers — caught between waking and dreaming! [{n}]",
                           them="💤 Reality dissolves — are you awake? Were you ever? [{n}]"),
    # zone items
    'vampiric_touch': dict(name='Vampiric Touch', school='necrotic', kind='drain',
                           you="🩸 Your gear drinks from {t}'s wound! [{n}]", them="🩸 Something cold drinks from your wound! [{n}]"),
    'life_drain': dict(name='Life Drain', school='necrotic', kind='drain',
                       you="🩸 {t}'s life bleeds into you! [{n}]", them="🩸 Your life bleeds away into your foe! [{n}]"),
    'poison_cloud': dict(name='Poison Cloud', school='poison', kind='cloud',
                         you="☁ A cloud of venom bursts around {t}! [{n}]", them="☁ Choking venom billows around you! [{n}]"),
    'ice_blast': dict(name='Ice Blast', school='frost', kind='slow',
                      you="❄ Ice blasts across {t}, slowing them! [{n}]", them="❄ Ice blasts across you — your limbs grow sluggish! [{n}]"),
    'turn_undead': dict(name='Turn Undead', school='holy', kind='hit', undead=True,
                        you="✝ Holy light sears the unliving {t}! [{n}]", them="✝ Holy light sears your unliving flesh! [{n}]"),
    'undead_bane': dict(name='Undead Bane', school='holy', kind='hit', undead=True,
                        you="✝ Your weapon blazes against the undead {t}! [{n}]", them="✝ The blade blazes with holy fire against you! [{n}]"),
    'chaos': dict(name='Chaos Surge', school='arcane', kind='hit', chaos=True,
                  you="✺ Raw chaos lashes {t} as {s}! [{n}]", them="✺ Raw chaos lashes you as {s}! [{n}]"),
    'flaming': dict(name='Flame Strike', school='fire', kind='hit',
                    you="🔥 Your weapon bursts into flame against {t}! [{n}]", them="🔥 The blade sears you with flame! [{n}]"),
    'frost': dict(name='Frost Bite', school='frost', kind='hit',
                  you="❄ Frost bites into {t}! [{n}]", them="❄ Frost bites into your wound! [{n}]"),
    'shocking': dict(name='Shock', school='lightning', kind='hit',
                     you="⚡ Lightning arcs from your weapon into {t}! [{n}]", them="⚡ Lightning jolts through you! [{n}]"),
    # named sets at four pieces
    'grave_drain': dict(name='Grave Drain', school='necrotic', kind='drain',
                        you="☠ Your regalia drinks {t}'s life! [{n}]", them="☠ The necromancer's regalia drinks your life! [{n}]"),
    'chaos_bolt': dict(name='Chaos Bolt', school='arcane', kind='hit', chaos=True,
                       you="✺ The chaos weave spits {s} at {t}! [{n}]", them="✺ The chaos weave spits {s} at you! [{n}]"),
    'apocalypse_ruin': dict(name='Ruin', school='shadow', kind='splash',
                            you="☄ Ruin breaks over {t} and all who stand near! [{n}]", them="☄ Ruin breaks over you! [{n}]"),
}

# on_defend effects (the wearer struck): chance, what it does
ON_DEFEND = {
    'fear_aura': dict(name='Dread', school='shadow'),
    'damage_reflect': dict(name='Reflect', school='physical', look='frost'),
    'frost_aura': dict(name='Frost Aura', school='frost'),
}

# a zone item's affect or property that is a proc
DERIVED_AFFECTS = ('vampiric_touch', 'poison_cloud', 'ice_blast', 'turn_undead', 'life_drain')
DERIVED_PROPERTIES = {'undead_bane': 'undead_bane', 'chaos': 'chaos', 'random_damage_type': 'chaos'}
DERIVED_FLAGS = ('flaming', 'frost', 'shocking')

DESCRIBE = {
    'on_hit': 'Chance on hit', 'on_kill': 'On kill', 'on_defend': 'When struck', 'on_equip': 'Equip',
}


def _level(item):
    try:
        from gear_look import item_level
        return item_level(item)
    except Exception:
        return 20


def proc_damage(item, proc, wearer=None):
    """The most a proc does: a legendary's own number, else grown from the item's level (and a
    zone item's affect value, 12 being the usual)."""
    if proc.get('damage'):
        return int(proc['damage'])
    lvl = _level(item) if item is not None else getattr(wearer, 'level', 20)
    base = 6 + lvl * 0.5
    if proc.get('value'):
        base *= max(0.5, min(2.0, proc['value'] / 12.0))
    return max(4, int(base))


def derived_procs(item):
    """The procs a zone item names some other way, read once and kept on the item."""
    cached = item.__dict__.get('_derived_procs')
    if cached is not None:
        return cached
    out = []
    for a in getattr(item, 'affects', None) or ():
        kind = a.get('type') if isinstance(a, dict) else getattr(a, 'type', None)
        value = a.get('value', 0) if isinstance(a, dict) else getattr(a, 'value', 0)
        if kind in DERIVED_AFFECTS:
            out.append({'type': 'on_hit', 'effect': kind, 'chance': DERIVED_CHANCE, 'value': value or 12})
    props = getattr(item, 'special_properties', None) or ()
    for prop in props:
        eff = DERIVED_PROPERTIES.get(str(prop))
        if eff and not any(p['effect'] == eff for p in out):
            out.append({'type': 'on_hit', 'effect': eff, 'chance': 15 if eff == 'undead_bane' else DERIVED_CHANCE})
    if getattr(item, 'item_type', '') == 'weapon':
        for flag in DERIVED_FLAGS:
            if flag in (getattr(item, 'flags', None) or ()):
                out.append({'type': 'on_hit', 'effect': flag, 'chance': 12})
    item.__dict__['_derived_procs'] = out
    return out


def item_procs(item):
    """Every proc an item has: its own list and what it names some other way."""
    own = [p for p in (getattr(item, 'procs', None) or []) if isinstance(p, dict)]
    return own + derived_procs(item)


def set_procs(player):
    """(set name, proc) for each named set worn at four pieces or more."""
    try:
        from sets import NAMED_SETS, tier_need
    except Exception:
        return []
    counts = {}
    for it in (getattr(player, 'equipment', None) or {}).values():
        sid = getattr(it, 'set_id', None) if it else None
        if isinstance(sid, str) and sid in NAMED_SETS:
            counts[sid] = counts.get(sid, 0) + 1
    out = []
    for sid, n in counts.items():
        for need, procs in (NAMED_SETS[sid].get('procs') or {}).items():
            if n >= tier_need(sid, need):
                out.extend((NAMED_SETS[sid], p) for p in procs)
    return out


def describe(proc):
    """A proc as a tooltip line ('Chance on hit: ...')."""
    if proc.get('desc'):
        return proc['desc']
    eff = proc.get('effect', '')
    spec = ON_HIT.get(eff) or ON_DEFEND.get(eff) or {}
    name = spec.get('name') or eff.replace('_', ' ').title()
    head = DESCRIBE.get(proc.get('type'), 'Effect')
    if proc.get('type') == 'on_hit':
        what = {'drain': 'drains life', 'chain': 'chains to a second foe', 'splash': 'splashes every foe',
                'cloud': 'engulfs every foe', 'slow': 'slows', 'root': 'roots', 'stun': 'staggers'}.get(spec.get('kind'))
        school = 'a random school' if spec.get('chaos') else spec.get('school', 'physical')
        vs = ' against the undead' if spec.get('undead') else ''
        return f"{head} ({proc.get('chance', DERIVED_CHANCE)}%): {name} — {school} damage{', ' + what if what else ''}{vs}"
    return f"{head}: {name}"


def is_player(ch):
    return hasattr(ch, 'connection')


def is_undead(ch):
    if 'undead' in (getattr(ch, 'flags', None) or ()) or 'undead' in str(getattr(ch, 'race', '') or '').lower():
        return True
    name = str(getattr(ch, 'name', '') or '').lower()
    return any(w in name for w in ('skeleton', 'zombie', 'ghoul', 'lich', 'wraith', 'ghost', 'spectre',
                                   'specter', 'vampire', 'mummy', 'revenant', 'wight', 'banshee', 'bone'))


def _worn(wearer, weapon):
    """(item, proc) for every proc worn that fires on this blow: the swinging weapon's own and
    every non-weapon's, then the sets'."""
    for it in (getattr(wearer, 'equipment', None) or {}).values():
        if not it:
            continue
        if getattr(it, 'item_type', '') == 'weapon' and it is not weapon:
            continue
        for p in item_procs(it):
            yield it, p
    for cfg, p in set_procs(wearer):
        yield None, p


def _colors():
    from config import Config
    return Config().COLORS


def _emit(room, src, dst, spec, school):
    try:
        import combat_events as ev
        from combat_hooks import fx_school
        ev.emit(room, 'proc', src=src, dst=dst, name=spec['name'], school=fx_school(spec.get('look') or school))
    except Exception:
        logger.exception('proc event')


async def _say(attacker, defender, item, spec, line_you, line_them, color):
    c = _colors()
    if hasattr(attacker, 'send'):
        await attacker.send(f"{c[color]}{line_you}{c['reset']}")
    if hasattr(defender, 'send') and line_them:
        await defender.send(f"{c[color]}{line_them}{c['reset']}")
    room = getattr(attacker, 'room', None)
    if room is not None and hasattr(room, 'send_to_room'):
        whose = getattr(item, 'short_desc', None) if item is not None else None
        src = f"{attacker.name}'s {_plain(whose)}" if whose else attacker.name
        await room.send_to_room(f"{c[color]}{src} unleashes {spec['name']} on {defender.name}!{c['reset']}",
                                exclude=[attacker, defender])


def _plain(text):
    import re
    return re.sub(r'\x1b\[[0-9;]*m', '', str(text or ''))


SCHOOL_COLOR = {'fire': 'bright_red', 'frost': 'bright_cyan', 'lightning': 'bright_white', 'arcane': 'bright_magenta',
                'shadow': 'magenta', 'necrotic': 'bright_red', 'holy': 'bright_yellow', 'poison': 'green',
                'disease': 'yellow', 'nature': 'green', 'sound': 'bright_white', 'physical': 'bright_cyan'}


async def on_hit(attacker, defender, weapon=None):
    """A player's weapon blow landed on `defender`: roll every proc it carries."""
    if not is_player(attacker) or defender is None or getattr(defender, 'hp', 0) <= 0:
        return 0
    now = time.time()
    cds = attacker.__dict__.setdefault('_proc_cd', {})
    dealt = 0
    for item, proc in list(_worn(attacker, weapon)):
        if proc.get('type') != 'on_hit' or getattr(defender, 'hp', 0) <= 0:
            continue
        spec = ON_HIT.get(proc.get('effect'))
        if not spec:
            continue
        if spec.get('undead') and not is_undead(defender):
            continue
        key = (id(item), proc.get('effect'))
        if now < cds.get(key, 0):
            continue
        if random.randint(1, 100) > int(proc.get('chance', DERIVED_CHANCE)):
            continue
        cds[key] = now + COOLDOWN
        try:
            dealt += await _land(attacker, defender, item, proc, spec)
        except Exception:
            logger.exception('proc %s failed', proc.get('effect'))
    return dealt


async def _land(attacker, defender, item, proc, spec):
    top = proc_damage(item, proc, attacker)
    amount = random.randint(max(1, top // 2), top)
    school = random.choice(CHAOS_SCHOOLS) if spec.get('chaos') else spec['school']
    room = getattr(attacker, 'room', None)
    t = getattr(defender, 'name', 'it')
    fill = dict(t=t, n=amount, s=school)
    await _say(attacker, defender, item, spec, spec['you'].format(**fill),
               spec.get('them', '').format(**fill) if spec.get('them') else '',
               SCHOOL_COLOR.get(spec.get('look') or school, 'bright_cyan'))
    _emit(room, attacker, defender, spec, school)
    kind = spec['kind']
    if kind == 'stun':
        from combat import CombatHandler
        CombatHandler.stun(defender, 1)
    elif kind == 'slow':
        defender.slowed_until = max(getattr(defender, 'slowed_until', 0) or 0, time.time() + 4)
    elif kind == 'root':
        defender.rooted_until = max(getattr(defender, 'rooted_until', 0) or 0, time.time() + 2)
    hp0 = getattr(defender, 'hp', 0)
    await defender.take_damage(amount, attacker, school)
    dealt = max(0, hp0 - getattr(defender, 'hp', hp0))
    if kind == 'drain' and dealt > 0 and getattr(attacker, 'hp', 0) > 0:
        attacker.hp = min(attacker.max_hp, attacker.hp + dealt)
    if kind in ('chain', 'splash', 'cloud'):
        share = {'chain': 2, 'splash': 3, 'cloud': 2}[kind]
        others = [o for o in _foes(attacker) if o is not defender and getattr(o, 'hp', 0) > 0]
        if kind == 'chain':
            others = others[:1]
        for other in others:
            part = amount // share
            if part <= 0:
                break
            if hasattr(attacker, 'send'):
                c = _colors()
                await attacker.send(f"{c[SCHOOL_COLOR.get(spec.get('look') or school, 'bright_cyan')]}"
                                    f"{spec['name']} reaches {other.name}! [{part}]{c['reset']}")
            _emit(room, attacker, other, spec, school)
            await other.take_damage(part, attacker, school)
    return dealt


def _foes(attacker):
    try:
        from spells import SpellHandler
        return list(SpellHandler.foes_in_room(attacker))
    except Exception:
        logger.exception('proc foes')
        return []


async def on_kill(killer, victim):
    """The wearer won: on-kill procs restore health and mana."""
    if not is_player(killer):
        return
    c = _colors()
    for it in (getattr(killer, 'equipment', None) or {}).values():
        if not it:
            continue
        for proc in item_procs(it):
            if proc.get('type') != 'on_kill':
                continue
            eff, pct = proc.get('effect', ''), proc.get('percent', 10)
            name = _plain(it.short_desc)
            if eff == 'restore_hp':
                heal = int(killer.max_hp * pct / 100)
                killer.hp = min(killer.max_hp, killer.hp + heal)
                await killer.send(f"{c['bright_green']}💚 {name} restores {heal} HP on the kill!{c['reset']}")
            elif eff == 'restore_mana':
                gain = int(killer.max_mana * pct / 100)
                killer.mana = min(killer.max_mana, killer.mana + gain)
                await killer.send(f"{c['bright_cyan']}💙 {name} restores {gain} mana!{c['reset']}")
            elif eff == 'absorb_echo':
                heal, gain = int(killer.max_hp * pct / 100), int(killer.max_mana * pct / 100)
                killer.hp = min(killer.max_hp, killer.hp + heal)
                killer.mana = min(killer.max_mana, killer.mana + gain)
                await killer.send(f"{c['bright_white']}🌀 {name} absorbs the dying echo — +{heal} HP, +{gain} mana!{c['reset']}")


def _defend_procs(player):
    for it in (getattr(player, 'equipment', None) or {}).values():
        if it:
            for p in item_procs(it):
                if p.get('type') == 'on_defend':
                    yield it, p
    for cfg, p in set_procs(player):
        if p.get('type') == 'on_defend':
            yield None, p


async def on_defend(player, attacker, amount, damage_type):
    """A blow landed on a player: their gear answers (dread, reflection, a frost aura)."""
    if amount <= 0 or attacker is None or attacker is player or getattr(attacker, 'hp', 0) <= 0:
        return
    if str(damage_type or 'physical') != 'physical' or getattr(attacker, 'room', None) is not getattr(player, 'room', None):
        return
    c = _colors()
    now = time.time()
    cds = player.__dict__.setdefault('_proc_cd', {})
    for item, proc in list(_defend_procs(player)):
        eff = proc.get('effect')
        spec = ON_DEFEND.get(eff)
        if not spec or getattr(attacker, 'hp', 0) <= 0:
            continue
        key = (id(item), eff)
        if now < cds.get(key, 0) or random.randint(1, 100) > int(proc.get('chance', 10)):
            continue
        cds[key] = now + COOLDOWN
        try:
            if eff == 'fear_aura':
                attacker.slowed_until = max(getattr(attacker, 'slowed_until', 0) or 0, now + 4)
                await player.send(f"{c['magenta']}Dread pours from your gear — {attacker.name} falters!{c['reset']}")
                if hasattr(attacker, 'send'):
                    await attacker.send(f"{c['magenta']}Terror grips you as you strike {player.name}!{c['reset']}")
            elif eff == 'damage_reflect':
                back = max(1, amount * int(proc.get('percent', 25)) // 100)
                await player.send(f"{c['bright_cyan']}Your gear turns the blow back on {attacker.name}! [{back}]{c['reset']}")
                _emit(player.room, player, attacker, spec, 'physical')
                await attacker.take_damage(back, player, 'thorns')
            elif eff == 'frost_aura':
                cold = random.randint(4, 6 + getattr(player, 'level', 1) // 3)
                attacker.slowed_until = max(getattr(attacker, 'slowed_until', 0) or 0, now + 3)
                await player.send(f"{c['bright_cyan']}Your frost aura bites {attacker.name}! [{cold}]{c['reset']}")
                _emit(player.room, player, attacker, spec, 'frost')
                await attacker.take_damage(cold, player, 'frost')
        except Exception:
            logger.exception('defend proc %s failed', eff)


CHEAT_DEATH_EVERY = 24 * 3600


async def cheat_death(player) -> bool:
    """A killing blow on a player wearing a cocoon (auto_resurrect): once a day, they live on at
    a third of their health instead."""
    if not any(p.get('effect') == 'auto_resurrect' for _, p in _defend_procs(player)):
        return False
    now = time.time()
    if now - (player.__dict__.get('cheat_death_at') or 0) < CHEAT_DEATH_EVERY:
        return False
    player.cheat_death_at = now
    player.hp = max(1, player.max_hp // 3)
    c = _colors()
    await player.send(f"{c['bright_yellow']}Amber light wraps you as you fall — your cocoon holds you to life!{c['reset']}")
    room = getattr(player, 'room', None)
    if room is not None and hasattr(room, 'send_to_room'):
        await room.send_to_room(f"{c['bright_yellow']}Amber light wraps {player.name} and they rise again!{c['reset']}", exclude=[player])
    _emit(room, player, player, {'name': 'Rebirth', 'look': 'holy'}, 'holy')
    return True


STAT_KEYS = ('str', 'dex', 'con', 'int', 'wis', 'cha')


def equip_totals(items) -> dict:
    """What worn gear's on-equip procs add to its totals (Player._gear_totals)."""
    out = {}

    def add(k, v):
        out[k] = out.get(k, 0) + v
    for it in items:
        for p in item_procs(it):
            eff, val = p.get('effect'), p.get('value', 0) or 0
            if p.get('type') == 'on_equip':
                if eff == 'all_stats':
                    # (an item that already lists each attribute among its affects gives it once)
                    listed = {a.get('type') for a in (getattr(it, 'affects', None) or ()) if isinstance(a, dict)}
                    for k in STAT_KEYS:
                        if k not in listed:
                            add(k, val)
                elif eff == 'stealth_bonus':
                    add('sneak', val)
                elif eff == 'double_speed':
                    add('travel_speed', 25)
                elif eff in ('damage_pct', 'detect_all'):
                    add(eff, val)
            elif p.get('type') == 'on_defend' and eff == 'fire_resist':
                add('fire_resist', 30)
    return out


def item_lines(item, wearer=None):
    """What an item does in a fight and the set it belongs to, as plain lines (identify,
    inspect, the 3D tooltip): its procs, then its set's name, how many are worn, and each tier."""
    lines = [describe(p) for p in item_procs(item)]
    sid = getattr(item, 'set_id', None)
    if sid not in (None, ''):
        sid = int(sid) if isinstance(sid, str) and sid.isdigit() else sid
        try:
            import sets
        except Exception:
            return lines
        worn = None
        if wearer is not None:
            worn = sum(1 for it in (getattr(wearer, 'equipment', None) or {}).values()
                       if it and str(getattr(it, 'set_id', '')) == str(sid))
        head = f"Set: {sets.set_name(sid)}"
        cap = sets.SET_CAPS.get(sid)
        if worn is not None:
            head += f" ({worn}{'/' + str(cap) if cap else ''} worn)"
        lines.append(head)
        for need, stats, where, set_proc_list in sets.set_tiers(sid):
            parts = [sets.describe_bonus(stats)] if stats else []
            parts += [describe(p) for p in set_proc_list]
            mark = '' if worn is None else ('✓ ' if worn >= need else '  ')
            zone = ' (in its zone)' if where == 'in_zone' else ''
            lines.append(f"  {mark}{need} pieces{zone}: {'; '.join(parts)}")
    return lines
