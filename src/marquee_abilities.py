"""The marquee abilities: one per class, earned through its class's quest (marquee.py), never by
level (owner: "Each class should have a final marquee spell/skill/ability ... a quest for each
character").

Each is a command (cmd_<id>) put on the CommandHandler before mastery.install(), so gating
("you earn it through ..."), the action bar and learning by use work as for any ability. They
are strong alone and party-wide in a group; their damage and healing follow how well they are
known (mastery.power) and the hero's level (marquee_scale.dpr: about what a hero deals in a
round); their long cooldowns are kept on the character (`marquee_cd`, saved).

  Warrior — Unbroken Banner: foes beside you reel and every foe turns on you; for five rounds
            you and your allies deal 25% more, shake off stuns and fear and mend.
  Mage — Singularity: every foe is pulled to one point and held while it crushes them for two
            rounds, then it implodes and leaves them slowed.
  Cleric — Seraph's Vigil: a seraph heals the most wounded ally each round for six rounds; while
            it stands each ally survives one killing blow.
  Paladin — Wings of Dawn: you rise on wings of light and crash down: radiant damage around you,
            and every ally healed and shielded.
  Necromancer — Lich Ascension: six rounds as a lich: spells cost half, soul bolts split to a
            second foe, what you deal drains back to you, and death is turned away once.

What lasts beyond the command runs on combat rounds (`EFFECTS`, stepped by `on_round` after
every World.combat_tick), only while its caster is online, in the room it began in and alive.
Bosses are never pulled, rooted, slowed or stunned: they stagger instead. Nothing here touches
players as foes: `_foes` are creatures fighting you or your group that you may harm.
"""
import logging
import math
import time

import combat_events as ev
import combat_range as cr
import marquee_scale as ms

logger = logging.getLogger('Misthollow')

# seconds
COOLDOWNS = {'unbroken_banner': 480, 'singularity': 480, 'seraphs_vigil': 600, 'wings_of_dawn': 480,
             'lich_ascension': 600}
NAMES = {'unbroken_banner': 'Unbroken Banner', 'singularity': 'Singularity', 'seraphs_vigil': "Seraph's Vigil",
         'wings_of_dawn': 'Wings of Dawn', 'lich_ascension': 'Lich Ascension'}
CLASS_OF = {'unbroken_banner': 'warrior', 'singularity': 'mage', 'seraphs_vigil': 'cleric',
            'wings_of_dawn': 'paladin', 'lich_ascension': 'necromancer'}
# the follow-up moments the 3D client plays as abilities of their own (combat_hooks.EXTRA_ABILITIES)
BEATS = {'singularity_implode': ('area', 'mage')}


def _c(player):
    return player.config.COLORS


def cooldown_left(player, ability):
    cd = getattr(player, 'marquee_cd', None) or {}
    return max(0, int(cd.get(ability, 0) - time.time()))


def start_cooldown(player, ability):
    cd = getattr(player, 'marquee_cd', None)
    if not isinstance(cd, dict):
        cd = player.marquee_cd = {}
    cd[ability] = time.time() + COOLDOWNS.get(ability, 300)


def _rounds(n):
    return n * cr.round_seconds()


def _power(player):
    """How well the ability is known, as the mastery wrapper set it for this command."""
    return getattr(player, '_ability_scale', 1) or 1


def _is_player(ch):
    return hasattr(ch, 'account_name')


def _hero_of(ch):
    """The player behind a blow: the player, or the master of a pet or charmed follower."""
    if ch is None:
        return None
    if _is_player(ch):
        return ch
    for attr in ('owner', 'master'):
        o = getattr(ch, attr, None)
        if o is not None and _is_player(o):
            return o
    return None


def _is_boss(ch):
    from combat import CombatHandler
    return CombatHandler.is_boss_mob(ch) or getattr(ch, 'boss_config', None) is not None


def _in_pvp(player):
    if getattr(player, 'dueling', None):
        return True
    try:
        from arena import ArenaManager
        return ArenaManager.is_in_arena_match(player)
    except Exception:
        return False


async def _ready(player, ability, foes=False):
    """The class, the cooldown and the place allow it now (else the player is told why: every
    refusal says "cannot", "not ready" or "must be fighting", which keeps the 3D client from
    animating it and the use from counting toward mastery)."""
    c = _c(player)
    name, cls = NAMES[ability], CLASS_OF[ability]
    if str(getattr(player, 'char_class', '')).lower() != cls:
        await player.send(f"{c['red']}You cannot use {name} — only a {cls} can.{c['reset']}")
        return False
    left = cooldown_left(player, ability)
    if left:
        await player.send(f"{c['yellow']}{name} is not ready yet ({left // 60}m {left % 60:02d}s cooldown).{c['reset']}")
        return False
    if _in_pvp(player):
        await player.send(f"{c['yellow']}Not here — {name} cannot be called on in a duel or the arena.{c['reset']}")
        return False
    if foes and not _foes(player):
        await player.send(f"{c['yellow']}You must be fighting to call on {name} — it cannot answer without a foe.{c['reset']}")
        return False
    return True


def _friends(player):
    group = getattr(player, 'group', None)
    return set(getattr(group, 'members', None) or []) | {player}


def _foes(player):
    """Creatures in the room fighting the player, the group or their pets — that the player may
    harm (never players or pets, never someone else's quest creatures)."""
    room = getattr(player, 'room', None)
    if room is None:
        return []
    import marquee
    friends = _friends(player)
    out = []
    for ch in list(room.characters):
        if _is_player(ch) or getattr(ch, 'hp', 0) <= 0 or _hero_of(ch) is not None:
            continue
        if not marquee.can_touch(player, ch):
            continue
        if _hero_of(getattr(ch, 'fighting', None)) in friends or any(getattr(f, 'fighting', None) is ch for f in friends):
            out.append(ch)
    return out


def _allies(player):
    """The player and the group members standing beside them."""
    room = getattr(player, 'room', None)
    group = getattr(player, 'group', None)
    out = [player]
    for m in (getattr(group, 'members', None) or []):
        if m is not player and getattr(m, 'room', None) is room and getattr(m, 'hp', 0) > 0:
            out.append(m)
    return out


async def _deal(caster, foe, amount, school):
    """Exactly `amount` damage to a creature from the caster, whatever scaling the damage
    wrapper applies right now (inside the command it scales by mastery, in a round step it
    doesn't). Returns what was dealt."""
    scale = (getattr(caster, '_dmg_scale', 1) or 1) * (getattr(caster, '_ability_scale', 1) or 1)
    hp0 = getattr(foe, 'hp', 0)
    killed = await foe.take_damage(max(1, int(round(amount / scale))), caster, school)
    if killed:
        from combat import CombatHandler
        await CombatHandler.handle_death(caster, foe)
    return hp0 - max(getattr(foe, 'hp', 0), 0)


def _heal(healer, ally, amount, school='holy'):
    """Heal (with the healer's healing bonus), clamped; the 3D client shows the number."""
    amount *= 1 + (getattr(healer, 'heal_power', 0) or 0) / 100
    hp0 = getattr(ally, 'hp', 0)
    ally.hp = min(getattr(ally, 'max_hp', hp0), hp0 + int(amount))
    gained = ally.hp - hp0
    if gained > 0 and getattr(ally, 'room', None) is not None:
        ev.emit(ally.room, 'heal', src=healer, dst=ally, amt=int(gained), school=school)
    return gained


def _control(caster, foe, kind, rounds=1):
    """Root, slow or stun a creature — a boss only staggers. Returns what happened."""
    now = time.time()
    room = getattr(foe, 'room', None)
    if _is_boss(foe):
        foe.staggered_until = max(getattr(foe, 'staggered_until', 0) or 0, now + 1.5)
        if room is not None:
            ev.emit(room, 'debuff', src=caster, dst=foe, name='Staggered')
        return 'stagger'
    if kind == 'stun':
        foe.stunned_rounds = max(getattr(foe, 'stunned_rounds', 0) or 0, rounds)
        foe.pending_intent = None
        return 'stun'
    attr, label = {'root': ('rooted_until', 'Held'), 'slow': ('slowed_until', 'Slowed')}[kind]
    setattr(foe, attr, max(getattr(foe, attr, 0) or 0, now + _rounds(rounds)))
    if room is not None:
        ev.emit(room, 'debuff', src=caster, dst=foe, name=label)
    return kind


def _ward(player, until, pct, by, label):
    """Turn away one killing blow before `until` (back at pct of max health; 0 means 1 HP)."""
    player._mq_ward = {'until': until, 'pct': pct, 'by': by, 'label': label}


# ---------------------------------------------------------------- what lasts: combat rounds
class Effect:
    """A marquee ability's lingering part, stepped once a combat round."""

    def __init__(self, caster, ability, rounds, step=None, end=None):
        self.caster = caster
        self.name = caster.name.lower()
        self.ability = ability
        self.room = caster.room
        self.rounds = rounds
        self.i = 0
        self.power = _power(caster)
        self.dpr = ms.dpr(getattr(caster, 'level', 45) or 45)
        self.step = step
        self.end = end
        self.data = {}


EFFECTS = {}         # (caster name, ability) -> Effect


def _begin(effect):
    old = EFFECTS.get((effect.name, effect.ability))
    EFFECTS[(effect.name, effect.ability)] = effect
    return old


def _alive_here(world, e):
    caster = (getattr(world, 'players', None) or {}).get(e.name)
    return (caster is e.caster and getattr(caster, 'room', None) is e.room and caster in e.room.characters
            and getattr(caster, 'hp', 0) > 0)


async def on_round(world):
    """Step every lingering effect (after each combat round)."""
    for key, e in list(EFFECTS.items()):
        if EFFECTS.get(key) is not e:
            continue
        if not _alive_here(world, e):
            EFFECTS.pop(key, None)
            await _finish(e, broken=True)
            continue
        e.i += 1
        if e.step is not None:
            try:
                with ev.hold():
                    await e.step(e, e.i)
            except Exception:
                logger.exception(f"marquee effect {e.ability} failed")
        if e.i >= e.rounds and EFFECTS.get(key) is e:
            EFFECTS.pop(key, None)
            await _finish(e, broken=False)


async def _finish(e, broken):
    if e.end is None:
        return
    try:
        with ev.hold():
            await e.end(e, broken)
    except Exception:
        logger.exception(f"marquee effect {e.ability} failed to end")


# ---------------------------------------------------------------- Unbroken Banner (warrior)
async def unbroken_banner(player, args):
    """Plant a war banner: foes beside you reel and every foe turns on you; you and your allies strike harder, shake off stuns and fear and mend for five rounds."""
    if not await _ready(player, 'unbroken_banner'):
        return
    from affects import AffectManager
    c = _c(player)
    power = _power(player)
    start_cooldown(player, 'unbroken_banner')
    await player.send(f"{c['bright_yellow']}You drive your war banner into the ground — it stands UNBROKEN!{c['reset']}")
    if player.room:
        await player.room.send_to_room(f"{c['bright_yellow']}{player.name} plants a war banner that blazes with defiance!{c['reset']}", exclude=[player])
    # the plant: foes close by reel; every foe turns on the warrior
    reeled = 0
    for foe in _foes(player):
        d = cr.distance(player, foe)
        if d is None or d <= 4.0:
            if _control(player, foe, 'stun', 1) == 'stun':
                reeled += 1
        foe.fighting = player
    # five rounds beside the banner: harder blows (on creatures), shaken off stuns and fear, health back
    until = time.time() + _rounds(5)
    for ally in _allies(player):
        if getattr(ally, 'stunned_rounds', 0):
            ally.stunned_rounds = 0
        for name in ('feared', 'fear'):
            try:
                AffectManager.remove_affect_by_name(ally, name)
            except Exception:
                pass
        if hasattr(ally, 'affect_flags'):
            ally.affect_flags.discard('feared')
        for old in [a for a in getattr(ally, 'affects', []) if a.name.startswith('unbroken_banner')]:
            AffectManager.remove_affect(ally, old)
        out = getattr(ally, '_mq_out', None)
        if not isinstance(out, dict):
            out = ally._mq_out = {}
        out['banner'] = (until, 0.25 * power)
        AffectManager.apply_affect(ally, {'name': 'unbroken_banner_mend', 'type': AffectManager.TYPE_HOT,
                                          'applies_to': 'hp', 'value': max(1, int(getattr(ally, 'max_hp', 100) * 0.08 * power)),
                                          'duration': 3, 'caster_level': player.level})
        if ally.room is not None:
            ev.emit(ally.room, 'buff', src=player, dst=ally, name='Unbroken')
        if ally is not player and hasattr(ally, 'send'):
            await ally.send(f"{c['bright_yellow']}{player.name}'s banner fills you with unbreakable resolve!{c['reset']}")
    if reeled:
        await player.send(f"{c['yellow']}{reeled} {'foe reels' if reeled == 1 else 'foes reel'} from the impact.{c['reset']}")


# ---------------------------------------------------------------- Singularity (mage)
async def singularity(player, args):
    """Tear a hole in the world: every foe is dragged to one point and crushed there for two rounds, then it implodes, leaving them slowed."""
    if not await _ready(player, 'singularity', foes=True):
        return
    c = _c(player)
    foes = _foes(player)
    target = player.fighting if getattr(player, 'fighting', None) in foes else foes[0]
    point = cr.pos_of(target)
    if point is None:
        known = [p for p in (cr.pos_of(f) for f in foes) if p is not None]
        point = (sum(p[0] for p in known) / len(known), sum(p[1] for p in known) / len(known)) if known else None
    start_cooldown(player, 'singularity')
    await player.send(f"{c['bright_magenta']}You close your fist on nothing — and the nothing CLOSES. A singularity opens!{c['reset']}")
    await player.room.send_to_room(f"{c['bright_magenta']}{player.name} tears a hole in the world; everything is dragged toward it!{c['reset']}", exclude=[player])
    held = [f for f in foes if not _is_boss(f)]
    for i, f in enumerate(held):
        if point is not None and cr.pos_of(f) is not None:
            a = 2 * math.pi * i / max(1, len(held))
            x, z = point[0] + 1.2 * math.cos(a), point[1] + 1.2 * math.sin(a)
            cr.set_pos(f, x, z)
            p = cr.pos_of(f)
            ev.emit(player.room, 'move', src=f, x=round(p[0], 2), z=round(p[1], 2))
        f.pending_intent = None            # whatever it was winding up is torn away
        _control(player, f, 'root', 2)
    for f in foes:
        if f not in held:
            _control(player, f, 'root', 2)   # a boss staggers
    e = Effect(player, 'singularity', 2, step=_singularity_step)
    e.data.update(point=point, foes=list(foes), target=target)
    for f in foes:
        await _deal(player, f, 1.0 * e.dpr * e.power, 'arcane')
    _begin(e)


async def _singularity_step(e, i):
    room = e.room
    c = _c(e.caster)
    foes = [f for f in e.data['foes'] if getattr(f, 'room', None) is room and getattr(f, 'hp', 0) > 0]
    if i == 1:
        await room.send_to_room(f"{c['magenta']}The singularity grinds everything caught in it.{c['reset']}")
        for f in foes:
            await _deal(e.caster, f, 1.0 * e.dpr * e.power, 'arcane')
        return
    point = e.data['point']
    caught = cr.within(point, foes, 6.0) if point is not None else foes
    tgt = e.data['target'] if e.data['target'] in caught else (caught[0] if caught else None)
    ev.emit(room, 'ability', src=e.caster, dst=tgt, ability='singularity_implode', shape='blast:6')
    await room.send_to_room(f"{c['bright_magenta']}The singularity IMPLODES!{c['reset']}")
    for f in caught:
        await _deal(e.caster, f, 4.0 * e.dpr * e.power, 'arcane')
        if getattr(f, 'hp', 0) > 0:
            _control(e.caster, f, 'slow', 3)


# ---------------------------------------------------------------- Seraph's Vigil (cleric)
async def seraphs_vigil(player, args):
    """Call down a seraph: for six rounds it heals whoever is most wounded beside you, and while it stands each of you will survive one killing blow."""
    if not await _ready(player, 'seraphs_vigil'):
        return
    c = _c(player)
    start_cooldown(player, 'seraphs_vigil')
    await player.send(f"{c['bright_white']}You sing the oldest words, and a SERAPH unfolds above you in a storm of light!{c['reset']}")
    await player.room.send_to_room(f"{c['bright_white']}A seraph unfolds above {player.name}, wings of light spread over you all!{c['reset']}", exclude=[player])
    e = Effect(player, 'seraphs_vigil', 5, step=_vigil_step, end=_vigil_end)
    e.data['warded'] = set()
    e.data['until'] = time.time() + _rounds(6)
    _vigil_ward(e)
    await _vigil_heal(e)
    _begin(e)


def _vigil_ward(e):
    for ally in _allies(e.caster):
        if ally.name not in e.data['warded']:
            e.data['warded'].add(ally.name)
            _ward(ally, e.data['until'], 0.0, 'The seraph', "Seraph's Vigil")
            ev.emit(ally.room, 'buff', src=e.caster, dst=ally, name='Seraph-warded')


async def _vigil_heal(e):
    allies = [a for a in _allies(e.caster) if getattr(a, 'hp', 0) > 0]
    if not allies:
        return
    ally = min(allies, key=lambda a: a.hp / max(1, a.max_hp))
    gained = _heal(e.caster, ally, 0.15 * ally.max_hp * e.power)
    if gained > 0:
        c = _c(e.caster)
        await e.room.send_to_room(f"{c['bright_white']}The seraph's light pours over {ally.name}. (+{gained}){c['reset']}")


async def _vigil_step(e, i):
    _vigil_ward(e)
    await _vigil_heal(e)


async def _vigil_end(e, broken):
    for ally in list(e.room.characters):
        w = getattr(ally, '_mq_ward', None)
        if _is_player(ally) and w and w.get('label') == "Seraph's Vigil":
            ally._mq_ward = None
    if not broken:
        c = _c(e.caster)
        await e.room.send_to_room(f"{c['white']}The seraph folds its wings and is gone.{c['reset']}")


# ---------------------------------------------------------------- Wings of Dawn (paladin)
async def wings_of_dawn(player, args):
    """Rise on wings of light and crash down like the dawn: radiant damage to every foe around you, and every ally beside you healed and shielded."""
    if not await _ready(player, 'wings_of_dawn'):
        return
    from affects import AffectManager
    c = _c(player)
    power = _power(player)
    dpr = ms.dpr(getattr(player, 'level', 45) or 45)
    start_cooldown(player, 'wings_of_dawn')
    await player.send(f"{c['bright_yellow']}Wings of light unfold from your shoulders — you rise, and come down like the DAWN!{c['reset']}")
    await player.room.send_to_room(f"{c['bright_yellow']}{player.name} rises on wings of light and crashes down in a blaze of dawn!{c['reset']}", exclude=[player])
    centre = cr.pos_of(player)
    foes = _foes(player)
    for f in (cr.within(centre, foes, 6.0) if centre is not None else foes):
        await _deal(player, f, 4.0 * dpr * power, 'holy')
    for ally in _allies(player):
        _heal(player, ally, 0.25 * ally.max_hp * power)
        for old in [a for a in getattr(ally, 'affects', []) if a.name == 'wings_of_dawn']:
            AffectManager.remove_affect(ally, old)
        AffectManager.apply_affect(ally, {'name': 'wings_of_dawn', 'type': AffectManager.TYPE_FLAG,
                                          'applies_to': 'armour_ward', 'value': max(1, int(ally.max_hp * 0.15 * power)),
                                          'duration': 3, 'caster_level': player.level})
        ev.emit(ally.room, 'buff', src=player, dst=ally, name="Dawn's Shield")
        if ally is not player and hasattr(ally, 'send'):
            await ally.send(f"{c['bright_yellow']}{player.name}'s dawn washes over you, and its light settles on you like armour.{c['reset']}")


# ---------------------------------------------------------------- Lich Ascension (necromancer)
async def lich_ascension(player, args):
    """Ascend as a lich for six rounds: your spells cost half, your soul bolts split to a second foe, what you deal drains back to you, and death is turned away once."""
    if not await _ready(player, 'lich_ascension'):
        return
    c = _c(player)
    start_cooldown(player, 'lich_ascension')
    until = time.time() + _rounds(6)
    player.lich_until = until
    _ward(player, until, 0.30, 'Your phylactery', 'Lich Ascension')
    await player.send(f"{c['bright_green']}Your flesh withers and your eyes kindle with grave-fire — you ASCEND as a lich!{c['reset']}")
    await player.room.send_to_room(f"{c['bright_green']}{player.name}'s flesh withers away; a lich stands in their place, crowned in grave-fire!{c['reset']}", exclude=[player])
    ev.emit(player.room, 'buff', src=player, dst=player, name='Lich')
    _begin(Effect(player, 'lich_ascension', 6, end=_lich_end))


async def _lich_end(e, broken):
    p = e.caster
    p.lich_until = 0
    w = getattr(p, '_mq_ward', None)
    if w and w.get('label') == 'Lich Ascension':
        p._mq_ward = None
    if not broken and hasattr(p, 'send'):
        c = _c(p)
        await p.send(f"{c['green']}The grave-fire gutters out; your flesh returns, and you are mortal again.{c['reset']}")


ABILITIES = {'unbroken_banner': unbroken_banner, 'singularity': singularity, 'seraphs_vigil': seraphs_vigil,
             'wings_of_dawn': wings_of_dawn, 'lich_ascension': lich_ascension}


# ---------------------------------------------------------------- hooks
def _wrap_world(world_cls):
    orig = world_cls.combat_tick

    async def combat_tick(self, *a, **k):
        result = await orig(self, *a, **k)
        try:
            await on_round(self)
        except Exception:
            logger.exception('marquee rounds failed')
        return result
    world_cls.combat_tick = combat_tick


def _wrap_mob_damage():
    """Damage-taken marks (`_mq_marks` on the creature), the hero's own bonuses (`_mq_out`:
    the banner, a song) and the lich's drain. Each is {source: (until, pct)}, so casting again
    refreshes it instead of stacking."""
    from mobs import Mobile
    orig = Mobile.take_damage

    async def take_damage(self, amount, *args, **kwargs):
        attacker = kwargs.get('attacker', args[0] if args else None)
        now = time.time()
        hero = _hero_of(attacker)
        if amount and amount > 0:
            mult = 1.0
            for until, pct in (getattr(self, '_mq_marks', None) or {}).values():
                if now < until:
                    mult += pct
            if hero is not None:
                for until, pct in (getattr(hero, '_mq_out', None) or {}).values():
                    if now < until:
                        mult += pct
            if mult != 1.0:
                amount = max(1, int(round(amount * mult)))
        hp0 = getattr(self, 'hp', 0)
        result = await orig(self, amount, *args, **kwargs)
        if attacker is not None and _is_player(attacker) and now < (getattr(attacker, 'lich_until', 0) or 0):
            dealt = hp0 - max(getattr(self, 'hp', 0), 0)
            if dealt > 0 and attacker.hp > 0:
                _heal(attacker, attacker, dealt * 0.25, school='necrotic')
        return result
    Mobile.take_damage = take_damage


def _wrap_player_death():
    """A ward (Seraph's Vigil, Lich Ascension) turns one killing blow away — from any creature,
    a hazard or a trap, never from another player. The outermost Player.die layer, so the death
    is never announced; and take_damage then answers "not killed", so no corpse is made."""
    from player import Player
    orig_die = Player.die

    async def die(self, killer=None, *a, **k):
        w = getattr(self, '_mq_ward', None)
        if w and time.time() < w.get('until', 0) and _hero_of(killer) is None and not _in_pvp(self):
            self._mq_ward = None                  # spent before anything else can run
            self.hp = max(1, int(getattr(self, 'max_hp', 1) * w.get('pct', 0)))
            self._mq_ward_saves = getattr(self, '_mq_ward_saves', 0) + 1
            if getattr(self, 'position', '') == 'dead':
                self.position = 'standing'
            room = getattr(self, 'room', None)
            c = _c(self)
            if hasattr(self, 'send'):
                await self.send(f"{c['bright_white']}{w['by']} turns death aside — you stand again! ({self.hp} HP){c['reset']}")
            if room is not None:
                await room.send_to_room(f"{c['bright_white']}{self.name} should have fallen — and stands again!{c['reset']}", exclude=[self])
                ev.emit(room, 'buff', src=self, dst=self, name='Death turned aside')
            return
        return await orig_die(self, killer, *a, **k)
    Player.die = die

    orig_td = Player.take_damage

    async def take_damage(self, amount, *a, **k):
        saves = getattr(self, '_mq_ward_saves', 0)
        result = await orig_td(self, amount, *a, **k)
        if result and getattr(self, '_mq_ward_saves', 0) != saves:
            return False
        return result
    Player.take_damage = take_damage


def _wrap_lich_casting():
    """As a lich, spells cost half (half the mana a cast really took comes back) and a soul
    bolt that flies splits to a second foe for 60% of what it dealt."""
    from spells import SpellHandler
    orig_cast = SpellHandler.cast_spell.__func__

    async def cast_spell(cls, caster, spell_name, target_name=None, *a, **k):
        lich = time.time() < (getattr(caster, 'lich_until', 0) or 0)
        m0 = getattr(caster, 'mana', 0)
        result = await orig_cast(cls, caster, spell_name, target_name, *a, **k)
        if lich:
            spent = m0 - getattr(caster, 'mana', 0)
            if spent > 1:
                caster.mana = min(getattr(caster, 'max_mana', caster.mana), caster.mana + spent // 2)
        return result
    SpellHandler.cast_spell = classmethod(cast_spell)

    from commands import CommandHandler
    orig_bolt = getattr(CommandHandler, 'cmd_soul_bolt', None)
    if orig_bolt is None:
        return
    orig_bolt = orig_bolt.__func__

    async def cmd_soul_bolt(cls, player, args):
        cd0 = getattr(player, 'soul_bolt_cooldown', 0)
        target = getattr(player, 'fighting', None)
        hp0 = getattr(target, 'hp', 0) if target is not None else 0
        result = await orig_bolt(cls, player, args)
        if (time.time() < (getattr(player, 'lich_until', 0) or 0) and target is not None
                and getattr(player, 'soul_bolt_cooldown', 0) != cd0):
            dealt = hp0 - max(getattr(target, 'hp', 0), 0)
            others = [f for f in _foes(player) if f is not target]
            if dealt > 0 and others:
                second = min(others, key=lambda f: cr.distance(target, f) or 0)
                c = _c(player)
                await player.send(f"{c['bright_green']}Your soul bolt splits and arcs into {second.name}!{c['reset']}")
                await _deal(player, second, dealt * 0.6, 'necrotic')
        return result
    cmd_soul_bolt.__doc__ = orig_bolt.__doc__
    CommandHandler.cmd_soul_bolt = classmethod(cmd_soul_bolt)


_installed = False


def install():
    """Put each marquee ability on the CommandHandler (before mastery.install wraps them) and
    the hooks their lingering parts need."""
    global _installed
    from commands import CommandHandler
    for ability, fn in ABILITIES.items():
        def make(fn):
            async def run(cls, player, args):
                return await fn(player, args)
            run.__doc__ = (fn.__doc__ or f"{NAMES.get(ability, ability)} (marquee).")
            return run
        setattr(CommandHandler, f'cmd_{ability}', classmethod(make(fn)))
    if not _installed:
        _installed = True
        from world import World
        _wrap_world(World)
        _wrap_mob_damage()
        _wrap_player_death()
        _wrap_lich_casting()
    logger.info(f"marquee abilities installed: {', '.join(ABILITIES)}")
