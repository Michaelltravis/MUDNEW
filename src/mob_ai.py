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

    # Explicit flags take priority
    if 'mob_caster' in flags or 'caster' in flags:
        roles.add('caster')
    if 'mob_boss' in flags or 'boss' in flags:
        roles.add('boss')
    if 'mob_pack' in flags or 'pack' in flags:
        roles.add('pack')
    if 'mob_healer' in flags or 'healer_ai' in flags:
        roles.add('healer')
    if 'mob_coward' in flags:
        roles.add('coward')

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

    # Boss by HP threshold
    if not roles & {'boss'}:
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

    # 35% chance to cast offensive spell
    if random.randint(1, 100) > 35:
        return False

    # Debuff (20% of casts, if target not already debuffed)
    if random.randint(1, 100) <= 20 and CASTER_DEBUFFS:
        spell_name, msg, attr, val = random.choice(CASTER_DEBUFFS)
        if attr and getattr(target, attr, 0) <= 0:
            mob.mana -= 15
            mob.ai_state['spell_cd'] = now + 5
            if attr:
                setattr(target, attr, val)
            await mob.room.send_to_room(
                f"{c['bright_magenta']}{mob.name} {msg} {target.name}!{c['reset']}"
            )
            if hasattr(target, 'send'):
                await target.send(f"{c['yellow']}You feel the effects of {spell_name.replace('_',' ')}!{c['reset']}")
            return True

    # Offensive spell
    for spell_name, msg, mult, mana_cost in CASTER_OFFENSIVE:
        if mob.mana >= mana_cost:
            base_dmg = random.randint(mob.level, mob.level * 3)
            damage = int(base_dmg * mult)
            mob.mana -= mana_cost
            mob.ai_state['spell_cd'] = now + 4
            await mob.room.send_to_room(
                f"{c['bright_magenta']}{mob.name} {msg} {target.name}! [{damage}]{c['reset']}"
            )
            if hasattr(target, 'send'):
                await target.send(f"{c['bright_red']}{mob.name}'s spell hits you for {damage} damage!{c['reset']}")
            killed = await target.take_damage(damage, mob)
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(mob, target)
            return True

    return False


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
    """Boss mob AI: rotate through special abilities on cooldown."""
    now = time.time()
    cooldowns = mob.ai_state.setdefault('boss_cooldowns', {})
    hp_pct = mob.hp / max(1, mob.max_hp)

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
# Main entry point — called each combat round per fighting mob
# ---------------------------------------------------------------------------

async def mob_ai_tick(mob):
    """
    Run intelligent combat AI for a fighting mob.
    Called once per combat round from world.combat_tick().
    Returns True if the mob took a special action this round.
    """
    if not mob.is_fighting or not mob.fighting or not mob.room:
        return False

    target = mob.fighting
    if not target.is_alive:
        return False

    # Ensure ai_state dict exists
    if not hasattr(mob, 'ai_state') or mob.ai_state is None:
        mob.ai_state = {}

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

    return False
