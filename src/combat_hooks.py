"""Combat v2 wiring: structured events and distance, laid over the existing combat code.

The combat code prints its log from ~120 places; rather than touching each, a few choke
points are wrapped once at startup (install()):

  CombatHandler.one_round   reach check (no blow lands from out of reach; the 3D client is
                            told to close in), then one 'attack' event per swing with its
                            result read from the very lines the log printed
  Player/Mobile.take_damage one 'dmg' event per wound with the amount actually applied (so
                            spells, damage over time and creature specials all show numbers);
                            a ranger shooting point-blank does reduced damage
  CombatHandler.handle_death, Player.die   'death'
  CommandHandler.execute    class abilities: range check first (nothing is spent when out
                            of reach), then an 'ability' event ahead of the wounds it caused
  mob_ai                    wind-ups get a ground area and a 'windup' event; when they land,
                            anyone who has stepped out of the area is spared ('resolve')

Positions and ranges live in combat_range.py; the event transport in combat_events.py.
Telnet players have no position, so for them every range check passes.
"""
import asyncio
import logging
import time

import combat_events as ev
import combat_range as cr

logger = logging.getLogger('Misthollow')
_installed = False


def _is_player(ch):
    return hasattr(ch, 'account_name')


def _capture(ch, lines):
    """Record what `ch` is sent while a wrapped call runs (it is still delivered)."""
    if ch is None or not hasattr(ch, 'send'):
        return lambda: None
    had = 'send' in getattr(ch, '__dict__', {})
    own = ch.__dict__.get('send') if had else None
    real = ch.send

    async def send(msg='', *a, **k):
        lines.append(str(msg))
        return await real(msg, *a, **k)

    try:
        ch.send = send
    except Exception:
        return lambda: None

    def restore():
        try:
            if had:
                ch.send = own
            else:
                del ch.send
        except Exception:
            pass
    return restore


def _plain(lines):
    import re
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', ' '.join(lines)).lower()


def _outcome(text):
    if 'parr' in text:
        return 'parry'
    if 'block' in text and 'with your shield' in text or 'blocks your attack' in text or 'you block' in text:
        return 'block'
    if any(w in text for w in ('dodge', 'evade', 'untouchable', 'sidestep')):
        return 'dodge'
    if 'miss' in text or 'swing blindly' in text or 'swings blindly' in text:
        return 'miss'
    return None


def _weapon_kind(ch):
    eq = getattr(ch, 'equipment', None) or {}
    w = eq.get('wield') if isinstance(eq, dict) else None
    return getattr(w, 'weapon_type', None) if w else None


def _reach_of(ch):
    """(reach in metres, ranged?) of a combatant's ordinary blow."""
    if _is_player(ch):
        return cr.auto_range(ch)
    reach, _prefer = cr.mob_reach(ch)
    return reach, reach > cr.MELEE + 0.5


# ------------------------------------------------------------------ the round
def _wrap_one_round():
    from combat import CombatHandler
    orig = CombatHandler.one_round.__func__

    async def one_round(cls, attacker, defender):
        room = getattr(attacker, 'room', None)
        if room is None or defender is None:
            return await orig(cls, attacker, defender)
        reach, ranged = _reach_of(attacker)
        d = cr.distance(attacker, defender)
        if d is not None and d > reach + 0.4 and getattr(attacker, 'fighting', None) is defender:
            # out of reach: no blow this round. Creatures close in on their own
            # (combat_range.move_tick); a hero is told, and the 3D client walks in.
            if _is_player(attacker):
                now = time.time()
                if now - getattr(attacker, '_oor_said', 0) > 6:
                    attacker._oor_said = now
                    c = attacker.config.COLORS
                    await attacker.send(f"{c['yellow']}{defender.name} is out of reach ({d:.0f} m) — "
                                        f"{'close in' if not ranged else 'get within ' + str(int(reach)) + ' m'}!{c['reset']}")
                ev.emit(room, 'oor', src=attacker, dst=defender, need=round(reach, 1), dist=round(d, 1), auto=True)
            return
        # a bow loosed point-blank lands poorly
        scale = 0.6 if ranged and _is_player(attacker) and d is not None and d < cr.POINT_BLANK else 1
        if scale != 1:
            attacker._dmg_scale = scale
        lines = []
        undo_a, undo_d = _capture(attacker, lines), _capture(defender, lines)
        hp0 = getattr(defender, 'hp', 0)
        mark = ev.mark(room)
        try:
            with ev.hold():
                await orig(cls, attacker, defender)
        finally:
            undo_a(); undo_d()
            if scale != 1:
                attacker._dmg_scale = 1
        text = _plain(lines)
        wounded = getattr(defender, 'hp', 0) < hp0
        res = ('crit' if 'critical hit' in text else 'hit') if wounded or 'damage]' in text else _outcome(text)
        if res:
            ev.emit_at(room, mark, 'attack', src=attacker, dst=defender, res=res, ranged=ranged or None,
                       weapon=_weapon_kind(attacker), perfect=('perfect strike' in text) or None)
        if scale != 1 and wounded and _is_player(attacker):
            c = attacker.config.COLORS
            await attacker.send(f"{c['yellow']}Too close for a clean shot — step back to draw properly.{c['reset']}")

    CombatHandler.one_round = classmethod(one_round)


# ------------------------------------------------------------------ wounds and deaths
def _wrap_take_damage(klass):
    orig = klass.take_damage

    async def take_damage(self, amount, *args, **kwargs):
        attacker = kwargs.get('attacker', args[0] if args else None)
        dtype = kwargs.get('damage_type', args[1] if len(args) > 1 else 'physical')
        scale = getattr(attacker, '_dmg_scale', 1) if attacker is not None else 1
        if scale != 1:
            amount = max(1, int(amount * scale))
        room = getattr(self, 'room', None)
        hp0 = getattr(self, 'hp', 0)
        result = await orig(self, amount, *args, **kwargs)
        dealt = hp0 - getattr(self, 'hp', hp0)
        if dealt > 0 and room is not None:
            ev.emit(room, 'dmg', src=attacker, dst=self, amt=int(dealt),
                    school=None if dtype in (None, 'physical', 'magic') else str(dtype))
        return result

    klass.take_damage = take_damage


def _wrap_deaths():
    from combat import CombatHandler
    from player import Player
    orig = CombatHandler.handle_death.__func__

    async def handle_death(cls, killer, victim, *a, **k):
        if victim is not None and getattr(victim, 'room', None) is not None and not getattr(victim, '_death_evented', False):
            try:
                victim._death_evented = True
            except Exception:
                pass
            ev.emit(victim.room, 'death', src=killer, dst=victim)
        return await orig(cls, killer, victim, *a, **k)

    CombatHandler.handle_death = classmethod(handle_death)
    orig_die = Player.die

    async def die(self, *a, **k):
        if getattr(self, 'room', None) is not None:
            ev.emit(self.room, 'death', dst=self)
        return await orig_die(self, *a, **k)

    Player.die = die


# ------------------------------------------------------------------ class abilities
def _ability_of(cmd, args):
    """(ability key, remaining args) when a command is a ranged-checked class ability."""
    from commands import CommandHandler
    c = CommandHandler.ALIASES.get(cmd, cmd)
    c = CommandHandler.COMMAND_ALIASES.get(c, c)
    if args:
        combo = f"{c}_{args[0]}".lower()
        if combo in cr.ABILITY_RANGE:
            return combo, args[1:]
    if c and c.lower() in cr.ABILITY_RANGE and c.lower() not in ('heal', 'bless', 'sleep'):
        return c.lower(), args
    return None, args


def _wrap_execute():
    from commands import CommandHandler
    orig = CommandHandler.execute.__func__

    async def execute(cls, player, cmd, args):
        name, rest = (None, args)
        try:
            if _is_player(player) and getattr(player, 'room', None) is not None and cmd:
                name, rest = _ability_of(cmd, list(args or []))
        except Exception:
            name = None
        if not name:
            return await orig(cls, player, cmd, args)
        rng, shape = cr.ability_range(name)
        target = None
        if rest:
            try:
                target = player.find_target_in_room(rest[0])
            except Exception:
                target = None
        if target is None:
            target = getattr(player, 'fighting', None)
        room = player.room
        d = cr.distance(player, target) if target is not None and shape not in ('self',) and not shape.startswith('nova') else None
        if d is not None and d > rng + 0.4:
            c = player.config.COLORS
            label = name.replace('_', ' ')
            await player.send(f"{c['yellow']}{target.name} is too far for {label} ({d:.0f} m; it reaches {rng:g} m).{c['reset']}")
            ev.emit(room, 'oor', src=player, dst=target, ability=name, need=rng, dist=round(d, 1))
            return
        lines = []
        undo = _capture(player, lines)
        mark = ev.mark(room)
        try:
            with ev.hold():
                await orig(cls, player, cmd, args)
        finally:
            undo()
        text = _plain(lines)
        if any(w in text for w in ("you don't know", 'huh?', 'not ready', 'cooldown', 'must wait', 'not enough',
                                   'too exhausted', 'you need', "can't", 'cannot', 'who?', 'not here', 'nobody')):
            return   # refused by the ability itself: no animation
        tgt = target if target is not None else getattr(player, 'fighting', None)
        res = _outcome(text)
        if shape == 'dash' and tgt is not None and cr.pos_of(tgt) is not None:
            tx, tz = cr.pos_of(tgt)
            px, pz = cr.pos_of(player) or (tx, tz)
            dx, dz = px - tx, pz - tz
            dd = max(0.01, (dx * dx + dz * dz) ** 0.5)
            cr.set_pos(player, tx + dx / dd * 1.4, tz + dz / dd * 1.4)
        ev.emit_at(room, mark, 'ability', src=player, dst=tgt if shape not in ('self',) else None,
                   ability=name, res=res, shape=shape)

    CommandHandler.execute = classmethod(execute)


# ------------------------------------------------------------------ creature wind-ups
def _area_for(mob, intent):
    """Where a declared special will land, in room metres (None without positions)."""
    target = getattr(mob, 'fighting', None)
    mp, tp = cr.pos_of(mob), cr.pos_of(target) if target is not None else None
    kind = intent.get('kind')
    if kind == 'aoe' and mp:
        return {'shape': 'circle', 'r': 4.0, 'on': 'src', 'x': round(mp[0], 2), 'z': round(mp[1], 2)}
    if kind in ('heavy', 'cast') and tp:
        # the blow (or the bolt) comes down where you stood when it began
        return {'shape': 'circle', 'r': 2.0 if kind == 'heavy' else 1.7, 'x': round(tp[0], 2), 'z': round(tp[1], 2)}
    return None


def _school_of_label(label):
    l = (label or '').lower()
    for word, school in (('fire', 'fire'), ('flame', 'fire'), ('breath', 'fire'), ('ice', 'frost'), ('frost', 'frost'),
                         ('lightning', 'lightning'), ('shadow', 'shadow'), ('venom', 'poison'), ('poison', 'poison'),
                         ('missile', 'arcane'), ('roar', 'sound'), ('summon', 'necrotic')):
        if word in l:
            return school
    return 'physical'


def _wrap_mob_ai():
    import mob_ai
    orig_declare = mob_ai.declare_intents

    async def declare_intents(mob):
        before = getattr(mob, 'pending_intent', None)
        await orig_declare(mob)
        intent = getattr(mob, 'pending_intent', None)
        if intent and intent is not before and getattr(mob, 'room', None) is not None:
            intent['area'] = _area_for(mob, intent)
            ms = int((cr.round_seconds() + cr.NPC_PHASE_DELAY) * 1000)
            ev.emit(mob.room, 'windup', src=mob, dst=getattr(mob, 'fighting', None), label=intent.get('label'),
                    kind=intent.get('kind'), ms=ms, area=intent['area'], school=_school_of_label(intent.get('label')),
                    interruptible=bool(intent.get('interruptible')) or None)

    mob_ai.declare_intents = declare_intents

    orig_resolve = mob_ai._resolve_intent

    async def _resolve_intent(mob):
        intent = getattr(mob, 'pending_intent', None)
        mob._resolving_intent = intent
        room = getattr(mob, 'room', None)
        mark = ev.mark(room) if room is not None else None
        try:
            with ev.hold():
                return await orig_resolve(mob)
        finally:
            mob._resolving_intent = None
            if intent and room is not None:
                dodged = getattr(mob, '_dodged_by_position', None) or []
                mob._dodged_by_position = []
                ev.emit_at(room, mark, 'resolve', src=mob, label=intent.get('label'), kind=intent.get('kind'),
                           area=intent.get('area'), school=_school_of_label(intent.get('label')),
                           dodged=[ev.ref(c) for c in dodged] or None)

    mob_ai._resolve_intent = _resolve_intent

    # stepping out of the marked ground beats the blow (before brace/sidestep rolls)
    orig_mitigate = mob_ai._mitigate_hit

    async def _mitigate_hit(mob, char, damage):
        intent = getattr(mob, '_resolving_intent', None) or {}
        area = intent.get('area')
        if area and _outside(mob, char, area):
            c = mob.config.COLORS
            await mob.room.send_to_room(
                f"{c['bright_cyan']}{getattr(char, 'name', 'Someone')} is clear of {mob.name}'s {intent.get('label', 'blow')} — it hits only ground!{c['reset']}")
            lst = getattr(mob, '_dodged_by_position', None)
            if lst is None:
                mob._dodged_by_position = lst = []
            lst.append(char)
            return None
        return await orig_mitigate(mob, char, damage)

    mob_ai._mitigate_hit = _mitigate_hit

    orig_cast = mob_ai._cast_offensive

    async def _cast_offensive(mob, target, spell):
        intent = getattr(mob, '_resolving_intent', None) or {}
        area = intent.get('area')
        room = getattr(mob, 'room', None)
        name = spell[0] if isinstance(spell, (tuple, list)) else spell
        if room is not None:
            ev.emit(room, 'spell', src=mob, dst=target, spell=str(name), school=_school_of_label(str(name)))
        if area and target is not None and _outside(mob, target, area):
            c = mob.config.COLORS
            await room.send_to_room(f"{c['bright_cyan']}{target.name} slips out of the blast — {mob.name}'s spell scorches empty ground!{c['reset']}")
            return
        return await orig_cast(mob, target, spell)

    mob_ai._cast_offensive = _cast_offensive


def _outside(mob, char, area):
    p = cr.pos_of(char)
    if p is None:
        return False
    if area.get('on') == 'src':
        c = cr.pos_of(mob) or (area['x'], area['z'])
    else:
        c = (area['x'], area['z'])
    return ((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2) ** 0.5 > area.get('r', 2) + 0.35


# ------------------------------------------------------------------ spells and heals
def _wrap_spells():
    from spells import SpellHandler
    orig_apply = SpellHandler.apply_spell.__func__

    async def apply_spell(cls, caster, target, spell, spell_name):
        room = getattr(caster, 'room', None)
        tgt = target if target is not None and target is not caster else None
        if room is not None:
            ev.emit(room, 'spell', src=caster, dst=tgt, spell=spell_name, school=cr.spell_school(spell_name, spell, caster),
                    shape=cr.ability_range(spell_name, True)[1])
        hp0 = getattr(target, 'hp', None) if target is not None else None
        with ev.hold():
            result = await orig_apply(cls, caster, target, spell, spell_name)
        if target is not None and hp0 is not None and getattr(target, 'hp', hp0) > hp0 and room is not None:
            ev.emit(room, 'heal', src=caster, dst=target, amt=int(target.hp - hp0), school=cr.spell_school(spell_name, spell, caster))
        return result

    SpellHandler.apply_spell = classmethod(apply_spell)


def install():
    global _installed
    if _installed:
        return
    _installed = True
    from player import Player
    from mobs import Mobile
    for step in (_wrap_one_round, lambda: _wrap_take_damage(Player), lambda: _wrap_take_damage(Mobile),
                 _wrap_deaths, _wrap_execute, _wrap_mob_ai, _wrap_spells):
        try:
            step()
        except Exception as e:
            logger.error(f"combat_hooks: {getattr(step, '__name__', 'step')} failed: {e}")
    logger.info("combat v2 hooks installed (events + range)")
