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

Health is sized against what the heroes who embarked really deal a round — dpr(level), the median
hero measured with the game's own combat code (tools/balance/sim.py), times CLASS_K for each one's
class (a lone hero's own; a party's mean) — so any lone hero spends about 66 s on an elite, two
minutes on the stage's warden and three on the trial's boss, and a party a little less. The
creatures rise with the quest's level (foe_level), and what they deal back (their blows and
specials in world/zones/zone_097.json) is scaled by:

  FOE_DAMAGE   their kind (an elite hits twice its file's blows, a ritual's waves 0.7)
  CLASS_D      what the class that embarked can stand (a lone hero's; a party's mean)
  LEVEL_D      1.8% more a level above 45, as heroes grow sturdier
  damage factor for the party's size (above)

set so a lone hero of any class loses up to about half their health to an elite or a warden and two
thirds of it to the trial's boss at the worst moment of the fight, and seldom dies (much of it in
blows they can see coming and step out of). A lone hero who knows the way plays a quest through
in 41-70 minutes. The measurements, how they were taken and what they found:
docs/balance/marquee.md.
"""
import math

ROUND = 3.0          # seconds per combat round (combat_range.round_seconds)

# rounds a lone hero needs for each kind of foe
ROUNDS = {'elite': 22, 'minion': 6, 'warden': 40, 'wave': 6, 'boss': 60, 'add': 3}
# how each class's damage compares with the median hero's, measured with the real combat code
# (tools/balance/sim.py, levels 45-60 alone; docs/balance/marquee.md): a quest's creatures are
# sized to the classes that embarked, so every party's fights last about as long
CLASS_K = {'warrior': 1.47, 'paladin': 1.13, 'cleric': 0.82, 'mage': 0.52, 'necromancer': 1.04, 'thief': 1.05,
           'assassin': 1.47, 'ranger': 0.73, 'bard': 0.85}


# how hard each kind of creature hits, as a share of its own blows and specials (zone_097): health
# follows the measured hero (dpr, CLASS_K), so fights last as long as the quest wants; the blows
# are set so what a fight costs a lone hero stays where it wants too (docs/balance/marquee.md)
FOE_DAMAGE = {'elite': 2.0, 'minion': 1.0, 'warden': 1.0, 'wave': 0.7, 'boss': 1.0, 'add': 1.0}
# and how hard a class's quest creatures hit at level 45: what a lone hero of that class can stand
# (a thief or a mage has half a warrior's health and no heals; a paladin heals and wears plate),
# measured the same way (tools/balance/sim.py --calibrate; docs/balance/marquee.md)
CLASS_D = {'warrior': 1.05, 'paladin': 1.88, 'cleric': 1.4, 'mage': 0.64, 'necromancer': 0.5, 'thief': 0.54,
           'assassin': 0.78, 'ranger': 1.07, 'bard': 0.78}
# ...and a little harder each level above it, as heroes grow sturdier (measured: 0.9% a level since the
# endgame gear's stats count, Push 22; 1.8% before)
LEVEL_D = 1.009


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
    """A level-L hero's damage per round at the gear a quest like this expects: the median of the
    nine classes measured with the real combat code (tools/balance/sim.py). Since the endgame
    gear's stats count (Push 22): about 195 at level 45, 290 at 50, 310 at 55 and 385 at 60, some
    4.5% more a level. Below 45 (the zone bosses) the 3.3% a level measured before, where that
    gear isn't worn."""
    x = level - 45
    return 204 * (1.045 ** x if x >= 0 else 1.033 ** x)


def _mean(table, cls):
    """A class's number, or a party's: the mean over its members' classes (each member deals, and
    is dealt, what their own class does)."""
    if isinstance(cls, (list, tuple)):
        return sum(table.get(str(c).lower(), 1.0) for c in cls) / len(cls) if cls else 1.0
    return table.get(str(cls).lower() if cls else 'warrior', 1.0)


def foe_health(kind, level, n, cls='warrior'):
    """cls: the quest's class, or the classes of everyone who embarked."""
    return int(ROUNDS.get(kind, 6) * dpr(level) * _mean(CLASS_K, cls) * health_factor(n))


def foe_level(proto_level, quest_level):
    """A quest creature's level: its file's, lifted by how far the quest is above level 45."""
    return int(proto_level) + max(0, int(quest_level) - 45)


def foe_damage(base, n):
    return max(1, int(base * damage_factor(n)))


def foe_damage_scale(kind, n, cls='warrior', level=45):
    """What a quest creature's blows are multiplied by: its kind's share, what the quest's class
    can stand at the quest's level, and the party's size."""
    return FOE_DAMAGE.get(kind, 1.0) * _mean(CLASS_D, cls) * LEVEL_D ** max(0, int(level) - 45) * damage_factor(n)


def exp_reward(base, n):
    return int(base * health_factor(n))


def gold_reward(base, n):
    return int(base * (1 + 0.5 * (clamp_n(n) - 1)))


def minutes(kind, level, n, cls='warrior'):
    """How long the party needs for one foe, in minutes (n heroes, each dealing what their class
    does: cls is the quest's class, or the classes of everyone who embarked)."""
    return foe_health(kind, level, n, cls) / (dpr(level) * _mean(CLASS_K, cls) * clamp_n(n)) * ROUND / 60
