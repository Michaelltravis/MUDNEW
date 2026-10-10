"""The marquee abilities: one per class, earned through its class's quest (marquee.py), never by
level (owner: "Each class should have a final marquee spell/skill/ability ... a quest for each
character").

Each is a command (cmd_<id>) put on the CommandHandler before mastery.install(), so gating
("you earn it through ..."), the action bar and learning by use work as for any ability. They
are strong alone and party-wide in a group; their damage and healing follow how well they are
known (mastery.power); their long cooldowns are kept on the character (`marquee_cd`, saved).

Warrior — Unbroken Banner: the warrior plants a war banner. Foes within 4 m are stunned for a
round (bosses stagger instead); every foe in the room turns on the warrior; for five rounds the
warrior and the allies beside them strike harder, shake off stuns and fear, and regain about
5% of their health a round.
"""
import logging
import time

logger = logging.getLogger('Misthollow')

# seconds
COOLDOWNS = {'unbroken_banner': 480}
NAMES = {'unbroken_banner': 'Unbroken Banner'}
CLASS_OF = {'unbroken_banner': 'warrior'}


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


async def _ready(player, ability):
    """The class and the cooldown allow it now (else the player is told why)."""
    c = _c(player)
    if str(getattr(player, 'char_class', '')).lower() != CLASS_OF[ability]:
        await player.send(f"{c['red']}Only a {CLASS_OF[ability]} can use {NAMES[ability]}.{c['reset']}")
        return False
    left = cooldown_left(player, ability)
    if left:
        await player.send(f"{c['yellow']}{NAMES[ability]} is not ready yet ({left // 60}m {left % 60:02d}s cooldown).{c['reset']}")
        return False
    return True


def _foes(player):
    """Creatures in the room fighting the player or the player's group."""
    room = getattr(player, 'room', None)
    if room is None:
        return []
    group = getattr(player, 'group', None)
    friends = set(getattr(group, 'members', None) or []) | {player}
    out = []
    for ch in list(room.characters):
        if hasattr(ch, 'account_name') or getattr(ch, 'hp', 0) <= 0:
            continue
        if getattr(ch, 'fighting', None) in friends or any(getattr(f, 'fighting', None) is ch for f in friends):
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


async def unbroken_banner(player, args):
    """Plant a war banner: foes beside you reel and every foe turns on you; you and your allies strike harder, shake off stuns and fear and mend for five rounds."""
    if not await _ready(player, 'unbroken_banner'):
        return
    import combat_range as cr
    from affects import AffectManager
    c = _c(player)
    power = getattr(player, '_ability_scale', 1) or 1
    start_cooldown(player, 'unbroken_banner')
    await player.send(f"{c['bright_yellow']}You drive your war banner into the ground — it stands UNBROKEN!{c['reset']}")
    if player.room:
        await player.room.send_to_room(f"{c['bright_yellow']}{player.name} plants a war banner that blazes with defiance!{c['reset']}", exclude=[player])
    # the plant: foes close by reel; every foe turns on the warrior
    stunned = 0
    for foe in _foes(player):
        d = cr.distance(player, foe)
        if d is None or d <= 4.0:
            if getattr(foe, 'is_boss', False):
                foe.staggered_until = time.time() + 1.5
            else:
                foe.stunned_rounds = max(getattr(foe, 'stunned_rounds', 0) or 0, 1)
                stunned += 1
        foe.fighting = player
    # five rounds beside the banner: harder blows, shaken off stuns and fear, health back
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
        AffectManager.apply_affect(ally, {'name': 'unbroken_banner', 'type': AffectManager.TYPE_MODIFY_STAT,
                                          'applies_to': 'damroll', 'value': int((6 + player.level // 4) * power),
                                          'duration': 3, 'caster_level': player.level})
        AffectManager.apply_affect(ally, {'name': 'unbroken_banner_mend', 'type': AffectManager.TYPE_HOT,
                                          'applies_to': 'hp', 'value': max(1, int(getattr(ally, 'max_hp', 100) * 0.08 * power)),
                                          'duration': 3, 'caster_level': player.level})
        if ally is not player and hasattr(ally, 'send'):
            await ally.send(f"{c['bright_yellow']}{player.name}'s banner fills you with unbreakable resolve!{c['reset']}")
    if stunned:
        await player.send(f"{c['yellow']}{stunned} {'foe reels' if stunned == 1 else 'foes reel'} from the impact.{c['reset']}")


ABILITIES = {'unbroken_banner': unbroken_banner}


def install():
    """Put each marquee ability on the CommandHandler (before mastery.install wraps them)."""
    from commands import CommandHandler
    for ability, fn in ABILITIES.items():
        def make(fn):
            async def run(cls, player, args):
                return await fn(player, args)
            run.__doc__ = (fn.__doc__ or f"{NAMES.get(ability, ability)} (marquee).")
            return run
        setattr(CommandHandler, f'cmd_{ability}', classmethod(make(fn)))
    logger.info(f"marquee abilities installed: {', '.join(ABILITIES)}")
