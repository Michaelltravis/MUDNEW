"""
Mob Combat AI System
====================
Intelligent combat behaviors for mobs based on type, flags, and keywords.
Runs once per combat round for each fighting mob via mob_ai_tick().

AI Types (checked via flags or inferred from name/keywords):
- MOB_CASTER: Periodically casts offensive spells, heals self, buffs
- MOB_BOSS: Special ability rotation with cooldowns (AoE, enrage, summon, fear)
- MOB_PACK: Calls nearby same-type mobs for help when attacked
- MOB_HEALER: Prioritizes healing wounded allies in the room
- MOB_COWARD: Flees at low HP
"""

import random
import time
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mobs import Mobile

logger = logging.getLogger('Misthollow.MobAI')

# ---------------------------------------------------------------------------
# Flag / keyword classification
# ---------------------------------------------------------------------------

CASTER_KEYWORDS = {'mage', 'wizard', 'sorcerer', 'warlock', 'shaman', 'necromancer',
                   'witch', 'conjurer', 'enchanter', 'magus', 'druid'}
HEALER_KEYWORDS = {'priest', 'priestess', 'cleric', 'healer', 'acolyte', 'monk',
                   'bishop', 'chaplain', 'medic'}
PACK_KEYWORDS = {'wolf', 'wolves', 'rat', 'rats', 'goblin', 'kobold', 'gnoll',
                 'orc', 'hyena', 'jackal', 'bandit', 'brigand', 'pirate'}
COWARD_KEYWORDS = {'rabbit', 'deer', 'squirrel', 'chicken', 'fox', 'cat',
                   'mouse', 'fawn', 'sparrow', 'villager', 'peasant', 'beggar'}
GUARDED_KEYWORDS = {'guard', 'cityguard', 'knight', 'soldier', 'sentinel', 'sentry',
                    'legionnaire', 'defender', 'golem', 'turtle', 'crab', 'warden'}
BIG_KEYWORDS = {'ogre', 'troll', 'giant', 'bear', 'golem', 'minotaur', 'yeti',
                'cyclops', 'behemoth', 'ettin', 'juggernaut'}


def _has_flag(mob, flag: str) -> bool:
    return flag in getattr(mob, 'flags', set())


def _name_lower(mob) -> str:
    return getattr(mob, 'name', '').lower()


def _keywords_set(mob) -> set:
    return set(getattr(mob, 'keywords', []))


def classify_mob(mob) -> set:
    """Return a set of AI role strings for the mob. Cached on ai_state."""
    ai_state = getattr(mob, 'ai_state', None)
    if ai_state is None:
        mob.ai_state = {}
        ai_state = mob.ai_state

    cached = ai_state.get('_ai_roles')
    if cached is not None:
        return cached

    roles = set()
    flags = getattr(mob, 'flags', set())
    name = _name_lower(mob)
    kws = _keywords_set(mob)
    name_words = set(name.split())
    all_words = kws | name_words

    # bosses.py Boss instances run their own telegraph/cast rotation via
    # Boss.process_ai — giving them the mob_ai 'boss' role too made two boss
    # ability systems fire on one mob
    try:
        from bosses import Boss
        is_boss_class = isinstance(mob, Boss)
    except Exception:
        is_boss_class = False

    # Explicit flags take priority
    if 'mob_caster' in flags or 'caster' in flags:
        roles.add('caster')
    if ('mob_boss' in flags or 'boss' in flags) and not is_boss_class:
        roles.add('boss')
    if 'mob_pack' in flags or 'pack' in flags:
        roles.add('pack')
    if 'mob_healer' in flags or 'healer_ai' in flags:
        roles.add('healer')
    if 'mob_coward' in flags:
        roles.add('coward')

    # Legacy special-attack mobs (poison bite, fire breath, paralyzing touch,
    # troll regen) — these fired from the old per-tick combat_ai; now owned here
    special = getattr(mob, 'special', None)
    if special in ('poison', 'firebreath', 'paralyze', 'regenerate') \
            or 'poison' in flags \
            or any(w in name for w in ('dragon', 'troll', 'spider', 'snake')):
        roles.add('legacy_special')

    # Disciplined/armored fighters periodically raise a GUARD that turns
    # blades aside — broken by a bash or kick (guarded-mob counterplay)
    if any(w in all_words for w in GUARDED_KEYWORDS) or 'shield' in name:
        roles.add('guarded')

    # Infer from keywords / name
    if not roles & {'caster'}:
        if all_words & CASTER_KEYWORDS:
            roles.add('caster')
        elif getattr(mob, 'special', None) in ('necromancer', 'shaman', 'druid'):
            roles.add('caster')
    if not roles & {'healer'}:
        if all_words & HEALER_KEYWORDS:
            roles.add('healer')
    if not roles & {'pack'}:
        if all_words & PACK_KEYWORDS:
            roles.add('pack')
    if not roles & {'coward'}:
        if all_words & COWARD_KEYWORDS:
            roles.add('coward')
        elif 'wimpy' in flags and getattr(mob, 'level', 99) <= 8:
            roles.add('coward')

    # Boss by HP threshold (never for bosses.py Boss instances — see above)
    if not roles & {'boss'} and not is_boss_class:
        if getattr(mob, 'max_hp', 0) > 5000:
            roles.add('boss')
        elif getattr(mob, 'is_boss', False):
            roles.add('boss')

    ai_state['_ai_roles'] = roles
    return roles


# ---------------------------------------------------------------------------
# Caster AI
# ---------------------------------------------------------------------------

CASTER_OFFENSIVE = [
    ('fireball',       'hurls a crackling fireball at',      2.5, 30),
    ('lightning_bolt',  'calls down lightning upon',          2.0, 25),
    ('ice_storm',      'conjures a storm of ice shards at',  1.8, 20),
    ('shadow_bolt',    'fires a bolt of shadow at',          1.5, 15),
    ('magic_missile',  'launches magic missiles at',         1.2, 10),
]

CASTER_DEBUFFS = [
    ('blindness', 'gestures and a blinding flash engulfs', 'blinded_rounds', 2),
    ('weaken',    'whispers a curse of weakness upon',     None, 0),
    ('slow',      'weaves a spell of lethargy around',     'stunned_rounds', 1),
]


async def _caster_tick(mob, target):
    """Caster mob AI: heal self, buff, or offensive spell."""
    if mob.mana < 10:
        return False

    c = mob.config.COLORS
    now = time.time()
    cd = mob.ai_state.setdefault('spell_cd', 0)
    if now < cd:
        return False

    hp_pct = mob.hp / max(1, mob.max_hp)

    # Self-heal at <40% HP
    if hp_pct < 0.4 and mob.mana >= 25:
        heal = random.randint(mob.level * 2, mob.level * 5)
        mob.hp = min(mob.max_hp, mob.hp + heal)
        mob.mana -= 25
        mob.ai_state['spell_cd'] = now + 6
        await mob.room.send_to_room(
            f"{c['bright_cyan']}{mob.name} chants a healing incantation and wounds close! [+{heal} HP]{c['reset']}"
        )
        return True

    # Buff self once per fight
    if not mob.ai_state.get('buffed') and mob.mana >= 15:
        mob.ai_state['buffed'] = True
        mob.ai_state['spell_cd'] = now + 4
        mob.mana -= 15
        # Give a minor buff
        mob.armor_class -= 10
        mob.damroll += 2
        await mob.room.send_to_room(
            f"{c['bright_magenta']}{mob.name} murmurs arcane words and a shimmering aura surrounds them!{c['reset']}"
        )
        return True

    # Offensive/debuff casts are DECLARED an round ahead (declare_intents) so
    # players can react; this direct path only runs for trivial fights that
    # bypass the intent system entirely.
    if not _intent_exempt(mob, target):
        return False

    # 60% chance to cast offensive spell (was 35% at 10Hz via the old
    # combat_ai path — this runs once per 4s round now)
    if random.randint(1, 100) > 60:
        return False

    # Debuff (20% of casts, if target not already debuffed)
    if random.randint(1, 100) <= 20 and CASTER_DEBUFFS:
        deb = random.choice(CASTER_DEBUFFS)
        if deb[2] and getattr(target, deb[2], 0) <= 0:
            mob.ai_state['spell_cd'] = now + 5
            await _cast_debuff(mob, target, deb)
            return True

    # Offensive spell
    for spell in CASTER_OFFENSIVE:
        if mob.mana >= spell[3]:
            mob.ai_state['spell_cd'] = now + 4
            await _cast_offensive(mob, target, spell)
            return True

    return False


async def _cast_debuff(mob, target, deb):
    """Execute a caster debuff (shared by the instant path and intent resolve)."""
    spell_name, msg, attr, val = deb
    c = mob.config.COLORS
    mob.mana = max(0, mob.mana - 15)
    if attr and getattr(target, attr, 0) <= 0:
        # brace = standing firm: resists the stun/blind family
        if attr in ('stunned_rounds', 'blinded_rounds') and _braced(target):
            await mob.room.send_to_room(
                f"{c['cyan']}{getattr(target, 'name', 'Someone')} stands braced — "
                f"the {spell_name.replace('_', ' ')} washes over them harmlessly!{c['reset']}"
            )
            return
        setattr(target, attr, val)
    await mob.room.send_to_room(
        f"{c['bright_magenta']}{mob.name} {msg} {target.name}!{c['reset']}"
    )
    if hasattr(target, 'send'):
        await target.send(f"{c['yellow']}You feel the effects of {spell_name.replace('_', ' ')}!{c['reset']}")


async def _cast_offensive(mob, target, spell):
    """Execute a caster attack spell (shared by the instant path and intent resolve)."""
    spell_name, msg, mult, mana_cost = spell
    c = mob.config.COLORS
    base_dmg = random.randint(mob.level, mob.level * 3)
    damage = int(base_dmg * mult)
    mob.mana = max(0, mob.mana - mana_cost)
    await mob.room.send_to_room(
        f"{c['bright_magenta']}{mob.name} {msg} {target.name}! [{damage}]{c['reset']}"
    )
    if hasattr(target, 'send'):
        await target.send(f"{c['bright_red']}{mob.name}'s spell hits you for {damage} damage!{c['reset']}")
    killed = await target.take_damage(damage, mob)
    if killed:
        from combat import CombatHandler
        await CombatHandler.handle_death(mob, target)


# ---------------------------------------------------------------------------
# Boss AI
# ---------------------------------------------------------------------------

BOSS_ABILITIES = [
    # (name, cooldown_secs, hp_threshold_max, handler_name)
    ('aoe_slam',     8,  1.0, '_boss_aoe_slam'),
    ('fear',         15, 1.0, '_boss_fear'),
    ('summon_adds',  25, 0.6, '_boss_summon_adds'),
    ('enrage',       0,  0.25, '_boss_enrage'),  # One-time at 25% HP
]


async def _boss_aoe_slam(mob, target):
    """AoE slam hitting all players in room."""
    c = mob.config.COLORS
    damage = random.randint(mob.level * 2, mob.level * 5)
    await mob.room.send_to_room(
        f"\n{c['bright_red']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c['reset']}\n"
        f"{c['bright_red']}  💥 {mob.name} SLAMS the ground!{c['reset']}\n"
        f"{c['bright_red']}  The earth trembles beneath your feet!{c['reset']}\n"
        f"{c['bright_red']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c['reset']}"
    )
    for char in list(mob.room.characters):
        if char == mob or not hasattr(char, 'connection'):
            continue
        actual_dmg = random.randint(int(damage * 0.7), damage)
        # declared-intent counterplay: sidestep avoids, brace halves
        actual_dmg = await _mitigate_hit(mob, char, actual_dmg)
        if actual_dmg is None:
            continue
        if hasattr(char, 'send'):
            await char.send(f"{c['bright_red']}The shockwave hits you for {actual_dmg} damage!{c['reset']}")
        killed = await char.take_damage(actual_dmg, mob)
        if killed:
            from combat import CombatHandler
            await CombatHandler.handle_death(mob, char)
    return True


async def _boss_fear(mob, target):
    """Fear: stun target for 1-2 rounds."""
    c = mob.config.COLORS
    await mob.room.send_to_room(
        f"\n{c['bright_yellow']}  😱 {mob.name} lets out a TERRIFYING roar!{c['reset']}\n"
        f"{c['bright_yellow']}  A wave of primal fear washes over the room!{c['reset']}"
    )
    for char in list(mob.room.characters):
        if char == mob or not hasattr(char, 'connection'):
            continue
        if _braced(char):
            # standing braced = steeled nerves; the fear breaks against you
            if hasattr(char, 'send'):
                await char.send(f"{c['cyan']}Braced and unshakable, you stare the terror down!{c['reset']}")
            continue
        if random.randint(1, 100) <= 60:  # 60% chance to be feared
            rounds = random.randint(1, 2)
            char.stunned_rounds = getattr(char, 'stunned_rounds', 0) + rounds
            if hasattr(char, 'send'):
                await char.send(f"{c['bright_yellow']}You are frozen with fear for {rounds} round(s)!{c['reset']}")
        else:
            if hasattr(char, 'send'):
                await char.send(f"{c['cyan']}You steel your nerves against the fear!{c['reset']}")
    return True


async def _boss_summon_adds(mob, target):
    """Summon 1-2 adds (temporary mobs) to fight."""
    c = mob.config.COLORS
    await mob.room.send_to_room(
        f"\n{c['bright_red']}  🔥 {mob.name} raises a hand and dark energy surges forth!{c['reset']}\n"
        f"{c['bright_red']}  \"Come, my minions! Destroy them!\"{c['reset']}"
    )
    num_adds = random.randint(1, 2)
    from mobs import Mobile
    for i in range(num_adds):
        add = Mobile(0, mob.world)
        add.name = f"summoned minion"
        add.short_desc = "a summoned minion"
        add.long_desc = "A dark minion writhes with malevolent energy."
        add.keywords = ['minion', 'summoned']
        add.level = max(1, mob.level - 5)
        add.max_hp = mob.max_hp // 6
        add.hp = add.max_hp
        add.damage_dice = f"{max(1, add.level // 3)}d6+{add.level}"
        add.hitroll = add.level
        add.damroll = add.level // 2
        add.armor_class = 100 - add.level * 2
        add.flags = {'summoned'}
        add.str = 10 + add.level // 5
        add.dex = 10 + add.level // 5
        add.con = 10 + add.level // 5
        add.room = mob.room
        mob.room.characters.append(add)
        if mob.world and hasattr(mob.world, 'npcs'):
            mob.world.npcs.append(add)
        # Start fighting the target
        add.fighting = target
        add.position = 'fighting'
        await mob.room.send_to_room(
            f"{c['red']}A {add.name} materializes and attacks {target.name}!{c['reset']}"
        )
    return True


async def _boss_enrage(mob, target):
    """Enrage at low HP — permanent damage boost."""
    if mob.ai_state.get('enraged'):
        return False
    c = mob.config.COLORS
    mob.ai_state['enraged'] = True
    mob.enrage_multiplier = 1.5
    # Also boost hitroll
    mob.hitroll += 5
    mob.damroll += 5
    await mob.room.send_to_room(
        f"\n{c['bright_red']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c['reset']}\n"
        f"{c['bright_red']}  🔥🔥🔥 {mob.name} ENRAGES! 🔥🔥🔥{c['reset']}\n"
        f"{c['bright_red']}  Eyes blazing with fury, attacks grow savage!{c['reset']}\n"
        f"{c['bright_red']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c['reset']}"
    )
    return True

_BOSS_HANDLERS = {
    '_boss_aoe_slam': _boss_aoe_slam,
    '_boss_fear': _boss_fear,
    '_boss_summon_adds': _boss_summon_adds,
    '_boss_enrage': _boss_enrage,
}


async def _boss_tick(mob, target):
    """Boss mob AI: rotate through special abilities on cooldown.

    In real fights the damaging abilities are DECLARED a round ahead
    (declare_intents) so players can react; this direct path executes them
    only for trivial fights. Enrage (a self-buff with no counterplay) always
    fires instantly.
    """
    now = time.time()
    cooldowns = mob.ai_state.setdefault('boss_cooldowns', {})
    hp_pct = mob.hp / max(1, mob.max_hp)
    exempt = _intent_exempt(mob, target)

    for ability_name, cd_secs, hp_max, handler_name in BOSS_ABILITIES:
        # Check HP threshold
        if hp_pct > hp_max:
            continue
        # Check cooldown
        if now < cooldowns.get(ability_name, 0):
            continue
        # Enrage is one-time
        if ability_name == 'enrage' and mob.ai_state.get('enraged'):
            continue
        # Non-enrage abilities go through the intent system in real fights
        if ability_name != 'enrage' and not exempt:
            continue

        handler = _BOSS_HANDLERS.get(handler_name)
        if handler:
            result = await handler(mob, target)
            if result:
                cooldowns[ability_name] = now + cd_secs
                return True

    return False


# ---------------------------------------------------------------------------
# Pack AI
# ---------------------------------------------------------------------------

async def _pack_tick(mob, target):
    """Pack mob: call for help from nearby same-type mobs (once per fight)."""
    if mob.ai_state.get('pack_called'):
        return False
    mob.ai_state['pack_called'] = True

    if not mob.room:
        return False

    c = mob.config.COLORS
    called = 0
    mob_vnum = getattr(mob, 'vnum', None)
    mob_name_base = _name_lower(mob).split()[0] if _name_lower(mob) else ''

    # Check current room and adjacent rooms
    rooms_to_check = [mob.room]
    for direction, exit_data in mob.room.exits.items():
        if exit_data and exit_data.get('room'):
            rooms_to_check.append(exit_data['room'])

    for room in rooms_to_check:
        for char in list(room.characters):
            if char == mob or char.is_fighting:
                continue
            if not hasattr(char, 'vnum'):
                continue
            # Same vnum or same name base
            is_same = (mob_vnum and char.vnum == mob_vnum) or \
                      (mob_name_base and _name_lower(char).startswith(mob_name_base))
            if not is_same:
                continue

            # Move to room if in adjacent room
            if char.room != mob.room:
                if char in char.room.characters:
                    char.room.characters.remove(char)
                char.room = mob.room
                mob.room.characters.append(char)
                await mob.room.send_to_room(
                    f"{c['red']}{char.name} rushes in to help!{c['reset']}"
                )

            # Join the fight
            char.fighting = target
            char.position = 'fighting'
            called += 1
            if called >= 3:
                break
        if called >= 3:
            break

    if called > 0:
        await mob.room.send_to_room(
            f"{c['bright_red']}{mob.name} howls for help and {called} ally{'s' if called != 1 else ''} join the fight!{c['reset']}"
        )
        return True
    return False


# ---------------------------------------------------------------------------
# Healer AI
# ---------------------------------------------------------------------------

async def _healer_tick(mob, target):
    """Healer mob: prioritize healing wounded allies in the room."""
    if mob.mana < 15:
        return False

    now = time.time()
    cd = mob.ai_state.setdefault('heal_cd', 0)
    if now < cd:
        return False

    c = mob.config.COLORS

    # Find the most wounded ally (non-player NPC in same room, fighting)
    best_ally = None
    best_pct = 1.0
    for char in mob.room.characters:
        if char == mob or hasattr(char, 'connection'):
            continue
        if not char.is_alive:
            continue
        pct = char.hp / max(1, char.max_hp)
        if pct < best_pct and pct < 0.7:
            best_pct = pct
            best_ally = char

    # Also consider healing self
    self_pct = mob.hp / max(1, mob.max_hp)
    if self_pct < best_pct and self_pct < 0.6:
        best_ally = mob

    if best_ally is None:
        return False

    heal = random.randint(mob.level * 2, mob.level * 5)
    best_ally.hp = min(best_ally.max_hp, best_ally.hp + heal)
    mob.mana -= 15
    mob.ai_state['heal_cd'] = now + 5

    if best_ally == mob:
        await mob.room.send_to_room(
            f"{c['bright_cyan']}{mob.name} chants a prayer and heals themselves! [+{heal} HP]{c['reset']}"
        )
    else:
        await mob.room.send_to_room(
            f"{c['bright_cyan']}{mob.name} lays hands on {best_ally.name} and heals their wounds! [+{heal} HP]{c['reset']}"
        )
    return True


# ---------------------------------------------------------------------------
# Coward AI
# ---------------------------------------------------------------------------

async def _coward_tick(mob, target):
    """Cowardly mob: flee when HP drops below 30%."""
    hp_pct = mob.hp / max(1, mob.max_hp)
    if hp_pct > 0.3:
        return False

    c = mob.config.COLORS
    await mob.room.send_to_room(
        f"{c['yellow']}{mob.name} panics and tries to flee!{c['reset']}"
    )

    # End combat
    if mob.fighting:
        if mob.fighting.fighting == mob:
            mob.fighting.fighting = None
    mob.fighting = None
    mob.position = 'standing'
    await mob.flee()
    return True


# ---------------------------------------------------------------------------
# Declared intents — a mob telegraphs its next special ONE ROUND AHEAD and the
# players get a real window to react (brace / sidestep / interrupt, see
# commands.py). declare_intents() runs in a pre-pass at the top of
# world.combat_tick — BEFORE the player phase — so the same tick's web push
# carries the intent with a full round left on the clock. mob_ai_tick()
# resolves a ripe intent the following round.
# ---------------------------------------------------------------------------

INTENT_WINDUP = 3.0        # min seconds between declaration and resolution
INTENT_ROOM_CAP = 2        # max simultaneous wind-ups per room (readability)


def _intent_exempt(mob, target) -> bool:
    """Trivial fights skip the declare/react loop so grinding stays fast."""
    return getattr(mob, 'level', 1) <= getattr(target, 'level', 1) - 8


def _braced(char) -> bool:
    return time.time() < getattr(char, 'brace_until', 0)


def _sidestep_roll(char) -> bool:
    """One evasion roll for a character in the sidestep window (dodge formula)."""
    if time.time() >= getattr(char, 'sidestep_until', 0):
        return False
    skill = char.skills.get('dodge', 0) if hasattr(char, 'skills') else 0
    bonus = (getattr(char, 'dex', 10) - 10) * 2
    return random.randint(1, 100) <= min(95, max(25, skill + bonus))


async def _mitigate_hit(mob, char, damage):
    """Apply brace/sidestep to a resolving heavy/aoe hit.
    Returns the final damage, or None when fully avoided."""
    c = mob.config.COLORS
    name = getattr(char, 'name', 'Someone')
    if _sidestep_roll(char):
        await mob.room.send_to_room(
            f"{c['bright_cyan']}{name} sidesteps at the last instant — the blow finds only air!{c['reset']}"
        )
        return None
    if _braced(char):
        if hasattr(char, 'send'):
            await char.send(f"{c['cyan']}You brace against the impact — it glances off you! (halved){c['reset']}")
        return max(1, damage // 2)
    return damage


def _choose_boss_intent(mob, target):
    """Pick the boss's next declared ability (enrage stays instant)."""
    now = time.time()
    cooldowns = mob.ai_state.setdefault('boss_cooldowns', {})
    hp_pct = mob.hp / max(1, mob.max_hp)
    META = {
        'aoe_slam':    ('aoe', 'Ground Slam', False,
                        '{name} coils low and raises both fists — the very air trembles!'),
        'fear':        ('debuff', 'Terrifying Roar', True,
                        "{name}'s chest swells as it draws in a deep, rumbling breath..."),
        'summon_adds': ('cast', 'Summon Minions', True,
                        '{name} begins chanting, dark energy gathering at its fingertips!'),
    }
    for ability_name, cd_secs, hp_max, handler_name in BOSS_ABILITIES:
        if ability_name == 'enrage' or ability_name not in META:
            continue
        if hp_pct > hp_max or now < cooldowns.get(ability_name, 0):
            continue
        kind, label, interruptible, telegraph = META[ability_name]
        cooldowns[ability_name] = now + cd_secs   # cooldown commits at declaration
        return {'kind': kind, 'label': label, 'interruptible': interruptible,
                'ability': ('boss', handler_name),
                'telegraph': telegraph.format(name=mob.name)}
    return None


def _choose_caster_intent(mob, target):
    """Pick the caster's next declared offensive/debuff spell (heal/buff stay instant)."""
    now = time.time()
    if mob.mana < 10 or now < mob.ai_state.get('spell_cd', 0):
        return None
    hp_pct = mob.hp / max(1, mob.max_hp)
    # leave the round free for the instant self-heal / first-buff paths
    if (hp_pct < 0.4 and mob.mana >= 25) or not mob.ai_state.get('buffed'):
        return None
    if random.randint(1, 100) > 60:
        return None
    if random.randint(1, 100) <= 20:
        deb = random.choice(CASTER_DEBUFFS)
        if deb[2] and getattr(target, deb[2], 0) <= 0:
            mob.ai_state['spell_cd'] = now + 5
            return {'kind': 'debuff', 'label': deb[0].replace('_', ' ').title(),
                    'interruptible': True, 'ability': ('caster_debuff', deb),
                    'telegraph': f'{mob.name} begins weaving a hex, fingers tracing sickly glowing sigils!'}
    for spell in CASTER_OFFENSIVE:
        if mob.mana >= spell[3]:
            mob.ai_state['spell_cd'] = now + 4
            return {'kind': 'cast', 'label': spell[0].replace('_', ' ').title(),
                    'interruptible': True, 'ability': ('caster_offensive', spell),
                    'telegraph': f'{mob.name} begins an incantation — arcane power crackles around it!'}
    return None


def _legacy_kind(mob):
    """Which legacy special this mob declares (None = instant-only, e.g. troll regen)."""
    special = getattr(mob, 'special', None)
    name = _name_lower(mob)
    flags = getattr(mob, 'flags', set())
    if special == 'firebreath' or 'dragon' in name:
        return 'firebreath'
    if special == 'paralyze':
        return 'paralyze'
    if special == 'poison' or 'poison' in flags or 'spider' in name or 'snake' in name:
        return 'poison'
    return None


def _choose_legacy_intent(mob, target):
    which = _legacy_kind(mob)
    if not which:
        return None
    now = time.time()
    if now < mob.ai_state.get('legacy_cd', 0):
        return None
    if random.randint(1, 100) > 35:
        return None
    mob.ai_state['legacy_cd'] = now + 8   # ~2 rounds
    if which == 'firebreath':
        return {'kind': 'heavy', 'label': 'Fire Breath', 'interruptible': False,
                'ability': ('legacy', 'firebreath'),
                'telegraph': f'{mob.name} rears back, flames licking between its jaws!'}
    if which == 'paralyze':
        return {'kind': 'debuff', 'label': 'Paralyzing Touch', 'interruptible': True,
                'ability': ('legacy', 'paralyze'),
                'telegraph': f'{mob.name} reaches out, numbing energy trailing from its touch...'}
    return {'kind': 'heavy', 'label': 'Venomous Strike', 'interruptible': False,
            'ability': ('legacy', 'poison'),
            'telegraph': f'{mob.name} bares dripping fangs, venom beading at their tips!'}


def _choose_bruiser_intent(mob, target):
    """Role-less mobs wind up a crushing blow every few rounds; hulking brutes
    sweep the whole area instead — the client paints a danger zone you can
    physically walk out of (cmd_evade)."""
    now = time.time()
    if now < mob.ai_state.get('heavy_cd', 0):
        return None
    if random.randint(1, 100) > 40:
        return None
    mob.ai_state['heavy_cd'] = now + random.randint(12, 16)   # every 3-4 rounds
    big = bool(set(_name_lower(mob).split()) & BIG_KEYWORDS)
    if big and random.randint(1, 100) <= 60:
        return {'kind': 'aoe', 'label': 'Sweeping Blow', 'interruptible': False,
                'ability': ('bruiser', 'sweep'),
                'telegraph': f'{mob.name} winds up a great SWEEPING blow — get clear!'}
    return {'kind': 'heavy', 'label': 'Crushing Blow', 'interruptible': False,
            'ability': ('bruiser', None),
            'telegraph': f'{mob.name} plants its feet and rears back for a crushing blow!'}


async def declare_intents(mob):
    """Pre-pass (top of world.combat_tick): a fighting mob with no pending
    wind-up may choose and DECLARE its next special. It resolves next round."""
    if getattr(mob, 'pending_intent', None):
        return
    if not mob.is_fighting or not mob.fighting or not mob.room:
        return
    target = mob.fighting
    if not getattr(target, 'is_alive', False):
        return
    if not hasattr(mob, 'ai_state') or mob.ai_state is None:
        mob.ai_state = {}
    if _intent_exempt(mob, target):
        return
    if time.time() < getattr(mob, 'staggered_until', 0):
        return   # reeling — in no state to wind anything up
    # keep pack fights readable: at most a couple of wind-ups at once
    pending = sum(1 for ch in mob.room.characters if getattr(ch, 'pending_intent', None))
    if pending >= INTENT_ROOM_CAP:
        return

    roles = classify_mob(mob)

    # A disciplined foe READS your rhythm: arming a perfect strike (cmd_swing)
    # can invite a counter — the guard snaps up before your blow lands. This
    # runs in the pre-pass, i.e. BEFORE the player phase resolves the strike,
    # so the duel actually plays out: telegraph → counter → breaker.
    if 'guarded' in roles and getattr(target, 'perfect_next', False):
        now = time.time()
        if now >= mob.ai_state.get('guard_cd', 0) and now >= getattr(mob, 'staggered_until', 0) \
                and random.randint(1, 100) <= 60:
            mob.guard_until = now + 8.0
            mob.ai_state['guard_cd'] = now + 20
            c = mob.config.COLORS
            await mob.room.send_to_room(
                f"{c['bright_cyan']}🛡 {mob.name} reads your rhythm and snaps into a guard!{c['reset']}"
            )
            return

    intent = None
    if 'boss' in roles:
        intent = _choose_boss_intent(mob, target)
    if intent is None and 'caster' in roles:
        intent = _choose_caster_intent(mob, target)
    if intent is None and 'legacy_special' in roles:
        intent = _choose_legacy_intent(mob, target)
    if intent is None and not roles & {'boss', 'caster', 'legacy_special'}:
        intent = _choose_bruiser_intent(mob, target)
    if intent is None:
        return

    intent['declared_at'] = time.time()
    mob.pending_intent = intent
    c = mob.config.COLORS
    if intent['kind'] in ('heavy', 'aoe'):
        tip = ' (brace or sidestep!)'
    elif intent.get('interruptible'):
        tip = ' (interrupt it!)'
    else:
        tip = ''
    await mob.room.send_to_room(
        f"{c['bright_yellow']}⚠ {intent['telegraph']}{c['yellow']}{tip}{c['reset']}"
    )


async def _resolve_legacy(mob, target, which):
    c = mob.config.COLORS
    from combat import CombatHandler
    if which == 'firebreath':
        damage = int(mob.roll_dice(mob.damage_dice) * 2.0)
        dmg = await _mitigate_hit(mob, target, damage)
        if dmg is None:
            return
        await mob.room.send_to_room(
            f"{c['bright_red']}{mob.name} breathes a torrent of fire over {target.name}! [{dmg}]{c['reset']}"
        )
        if await target.take_damage(dmg, mob):
            await CombatHandler.handle_death(mob, target)
    elif which == 'poison':
        damage = max(1, int(mob.roll_dice(mob.damage_dice) * 0.5))
        dmg = await _mitigate_hit(mob, target, damage)
        if dmg is None:
            return
        await mob.room.send_to_room(
            f"{c['bright_red']}{mob.name} sinks venomous fangs into {target.name}! [{dmg}]{c['reset']}"
        )
        try:
            from affects import AffectManager
            already = any((a.get('name') if isinstance(a, dict) else getattr(a, 'name', '')) == 'poison'
                          for a in getattr(target, 'affects', []))
            if not already:
                AffectManager.apply_affect(target, {
                    'name': 'poison', 'type': AffectManager.TYPE_DOT, 'applies_to': 'hp',
                    'value': 3 + mob.level // 5, 'duration': 4, 'caster_level': mob.level,
                })
                if hasattr(target, 'send'):
                    await target.send(f"{c['green']}You feel poison coursing through your veins!{c['reset']}")
        except Exception:
            pass
        if await target.take_damage(dmg, mob):
            await CombatHandler.handle_death(mob, target)
    else:   # paralyze
        if _braced(target) or _sidestep_roll(target):
            await mob.room.send_to_room(
                f"{c['cyan']}{target.name} shrugs off {mob.name}'s numbing touch!{c['reset']}"
            )
            return
        if random.randint(1, 100) <= 35:
            if hasattr(target, 'position'):
                target.position = 'stunned'
            await mob.room.send_to_room(f"{c['yellow']}{target.name} is paralyzed!{c['reset']}")
        else:
            await mob.room.send_to_room(
                f"{c['yellow']}{target.name} twists away from the paralyzing touch!{c['reset']}"
            )


async def _resolve_bruiser(mob, target, variant=None):
    c = mob.config.COLORS
    from combat import CombatHandler
    try:
        base = mob.roll_dice(mob.damage_dice)
    except Exception:
        base = random.randint(mob.level, max(mob.level, mob.level * 3))
    if variant == 'sweep':
        # area sweep: hits every player in the room; sidestep/brace/evade all
        # mitigate (the web client auto-evades when you're physically clear)
        damage = int(base * 1.4) + getattr(mob, 'damroll', 0)
        await mob.room.send_to_room(
            f"{c['bright_red']}{mob.name}'s SWEEPING blow scythes across the area!{c['reset']}"
        )
        for char in list(mob.room.characters):
            if char is mob or not hasattr(char, 'connection'):
                continue
            dmg = await _mitigate_hit(mob, char, damage)
            if dmg is None:
                continue
            if hasattr(char, 'send'):
                await char.send(f"{c['bright_red']}The sweep smashes into you! [{dmg}]{c['reset']}")
            if await char.take_damage(dmg, mob):
                await CombatHandler.handle_death(mob, char)
        return
    damage = int(base * 1.8) + getattr(mob, 'damroll', 0)
    dmg = await _mitigate_hit(mob, target, damage)
    if dmg is None:
        return
    await mob.room.send_to_room(
        f"{c['bright_red']}{mob.name}'s crushing blow slams into {target.name}! [{dmg}]{c['reset']}"
    )
    if not _braced(target) and random.randint(1, 100) <= 25:
        target.stunned_rounds = getattr(target, 'stunned_rounds', 0) + 1
        if hasattr(target, 'send'):
            await target.send(f"{c['yellow']}The impact leaves you reeling — stunned!{c['reset']}")
    if await target.take_damage(dmg, mob):
        await CombatHandler.handle_death(mob, target)


async def _resolve_intent(mob):
    """Execute (or fizzle) the mob's declared intent. Called from mob_ai_tick
    one round after declaration; an interrupt clears pending_intent before we
    ever get here."""
    intent = getattr(mob, 'pending_intent', None)
    mob.pending_intent = None
    if not intent:
        return False
    c = mob.config.COLORS
    target = mob.fighting
    if not target or not getattr(target, 'is_alive', False) or not mob.room:
        if mob.room:
            await mob.room.send_to_room(
                f"{c['yellow']}{mob.name}'s {intent['label']} finds no target and fizzles.{c['reset']}"
            )
        return True

    if intent['kind'] in ('heavy', 'aoe'):
        mob._skip_autoattack = True   # the special IS this round's attack

    what, arg = intent['ability']
    if what == 'boss':
        handler = _BOSS_HANDLERS.get(arg)
        if handler:
            await handler(mob, target)
    elif what == 'caster_offensive':
        await _cast_offensive(mob, target, arg)
    elif what == 'caster_debuff':
        await _cast_debuff(mob, target, arg)
    elif what == 'legacy':
        await _resolve_legacy(mob, target, arg)
    elif what == 'bruiser':
        await _resolve_bruiser(mob, target, arg)
    return True


# ---------------------------------------------------------------------------
# Main entry point — called each combat round per fighting mob
# ---------------------------------------------------------------------------

async def mob_ai_tick(mob):
    """
    Run intelligent combat AI for a fighting mob.
    Called once per combat round from world.combat_tick().
    Returns True if the mob took a special action this round.
    """
    if not mob.is_fighting or not mob.fighting or not mob.room:
        mob.pending_intent = None   # never leave a wind-up dangling
        return False

    target = mob.fighting
    if not target.is_alive:
        return False

    # Ensure ai_state dict exists
    if not hasattr(mob, 'ai_state') or mob.ai_state is None:
        mob.ai_state = {}

    # A declared intent owns this mob's special action: resolve it once ripe
    # (it was declared in a previous round's pre-pass); otherwise it is still
    # winding up and the mob takes no other special action this round.
    intent = getattr(mob, 'pending_intent', None)
    if intent:
        if time.time() - intent.get('declared_at', 0) >= INTENT_WINDUP:
            await _resolve_intent(mob)
        return True

    roles = classify_mob(mob)
    if not roles:
        return False

    # Priority order: coward > healer > boss > pack > caster
    # Coward check first (survival)
    if 'coward' in roles:
        if await _coward_tick(mob, target):
            return True

    # Healer checks allies
    if 'healer' in roles:
        if await _healer_tick(mob, target):
            return True

    # Boss abilities
    if 'boss' in roles:
        if await _boss_tick(mob, target):
            return True

    # Pack call for help (one-time)
    if 'pack' in roles:
        if await _pack_tick(mob, target):
            return True

    # Caster spells
    if 'caster' in roles:
        if await _caster_tick(mob, target):
            return True

    # Troll-style regeneration (instant — its counter is poison, not a reaction).
    # Declared legacy specials (fire breath etc.) go through declare_intents.
    if 'legacy_special' in roles and _legacy_kind(mob) is None:
        if random.randint(1, 100) <= 30:
            await mob.special_attack()
            return True

    # Disciplined fighters raise a GUARD: physical damage mostly turned aside
    # for two rounds. The taught counter is a bash/kick (break_guard).
    if 'guarded' in roles:
        now = time.time()
        if now >= mob.ai_state.get('guard_cd', 0) \
                and now >= getattr(mob, 'staggered_until', 0) \
                and random.randint(1, 100) <= 45:
            mob.guard_until = now + 8.0          # ~2 rounds
            mob.ai_state['guard_cd'] = now + 20  # ~5 rounds between guards
            c = mob.config.COLORS
            await mob.room.send_to_room(
                f"{c['bright_cyan']}🛡 {mob.name} locks into a defensive guard! "
                f"{c['yellow']}(a heavy bash or kick can break it){c['reset']}"
            )
            return True

    return False
