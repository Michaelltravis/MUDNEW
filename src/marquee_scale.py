"""How hard a marquee quest's foes are (owner: "If done solo the difficulty should take a couple
hours of play time. If in a group the difficulty should scale based on how many embark on the
quest when the player accepts").

`n` is how many embarked when the quest was accepted (1-6): it is fixed for good, so someone
leaving or dying later changes nothing. `level` is the party's level at acceptance (the owner's,
or the party's average if higher; 45-60).

  health       x (1 + 0.8 (n - 1))     each extra hero brings most of a hero's damage
  damage       x (1 + 0.1 (n - 1))     a little harder hitting, so a group still has to mind it
  adds a wave  + floor((n - 1) / 2)
  boss tempo   abilities come 6% sooner per extra hero
  rewards      experience x health factor (shared out), gold x (1 + 0.5 (n - 1))

Base numbers are sized against a level-L hero's damage per round (DPR, from the class damage
curves at mastery-level gear) so a lone level-45 warrior spends about 66 s on an elite, two
minutes on the stage's warden and three on the trial's boss; with travel, talk and the gathering
in between the whole quest runs about two hours alone. What the foes deal back (world/zones/
zone_097.json) is sized so a lone level-45 hero takes about half their health from an elite and
one to two times it from a boss, most of that from blows they can see coming and step out of.
"""
import math

ROUND = 3.0          # seconds per combat round (combat_range.round_seconds)

# rounds a lone hero needs for each kind of foe
ROUNDS = {'elite': 22, 'minion': 6, 'warden': 40, 'wave': 6, 'boss': 60, 'add': 3}
# how much each class's damage differs from the average (a caster bursts, a cleric heals)
CLASS_K = {'warrior': 1.0, 'paladin': 0.92, 'cleric': 0.8, 'mage': 1.1, 'necromancer': 1.0, 'thief': 1.05,
           'assassin': 1.12, 'ranger': 1.05, 'bard': 0.85}


def clamp_n(n):
    return max(1, min(6, int(n or 1)))


def health_factor(n):
    return 1 + 0.8 * (clamp_n(n) - 1)


def damage_factor(n):
    return 1 + 0.1 * (clamp_n(n) - 1)


def extra_adds(n):
    return (clamp_n(n) - 1) // 2


def tempo(n):
    """Multiplier on a boss's time between abilities (smaller: sooner)."""
    return 1 / (1 + 0.06 * (clamp_n(n) - 1))


def party_level(owner_level, levels=()):
    lv = [owner_level] + [x for x in levels if x]
    avg = sum(lv) / len(lv)
    return max(45, min(60, int(round(max(owner_level, avg)))))


def dpr(level):
    """A level-L hero's damage per round at the gear a quest like this expects."""
    return 1.2 * (9 * (1 + 0.22 * level) + 0.6 * level)


def foe_health(kind, level, n, cls='warrior'):
    return int(ROUNDS.get(kind, 6) * dpr(level) * CLASS_K.get(cls, 1.0) * health_factor(n))


def foe_damage(base, n):
    return max(1, int(base * damage_factor(n)))


def exp_reward(base, n):
    return int(base * health_factor(n))


def gold_reward(base, n):
    return int(base * (1 + 0.5 * (clamp_n(n) - 1)))


def minutes(kind, level, n, cls='warrior'):
    """How long the party needs for one foe, in minutes (n heroes, each a DPR)."""
    return foe_health(kind, level, n, cls) / (dpr(level) * clamp_n(n)) * ROUND / 60
