# progression-01 — every class on the newcomer ladder

Fresh level-1 character of each class, forged through the live creation wizard, playing attack +
its own button 3 + brace on the wind-up prompt. Ladder: training dummy, then the Newbie Zone (the
tutorial's own route). Newcomer XP ramp 250/350/500/650. "wins" counts kills out of 12 steps; the
rest are steps whose creature had wandered off (not losses). Driver: `tools/gauntlet/curve_all.py`.

| class | opener (button 3) | level reached | deaths | time to L5 | wins /12 |
|---|---|---|---|---|---|
| warrior | `bash` | 5 | 0 | 2.5 min | 12 |
| paladin | `censure` | 5 | 0 | 2.4 min | 12 |
| cleric | `cast 'holy smite'` | 5 | 0 | 2.8 min | 11 |
| mage | `cast 'magic missile'` | 5 | 0 | 2.9 min | 11 |
| bard | `mockery` | 5 | 0 | 2.8 min | 10 |
| thief | `backstab` | 5 | 0 | 3.6 min | 10 |
| ranger | `cast 'truesight shot'` | 5 | 0 | 2.9 min | 9 |
| assassin | `backstab` | 5 | 0 | 2.9 min | 9 |
| necromancer | `cast 'soul bolt'` | 5 | 0 | 2.9 min | 8 |

**Nine of nine classes reach level 5 with no deaths in 2.4–3.6 minutes.** (Warrior is run D in
the parent record; the other eight are the per-class folders here.)

## What the first pass found (records in `../classes-before-roster-fix/`)
Before the roster fix the **bard reached level 1 with ten deaths** ("You haven't learned mockery
yet!"), and paladin and ranger fought with auto-attack only. A new character learns its first
three roster skills and two spells; for bard (sneak, pick_lock, lore), paladin (censure was fifth)
and ranger (track, sneak, hide) the attack that the welcome card, hotbar and class picker promised
was not among them. Fixes: rosters reordered so button 3 is learned at creation (`src/config.py`),
the payload carries learned spells (`src/map_system.py`), and the hotbar kit and welcome card only
name abilities the character actually has (`ui.js`). Bard after the fix: 0 deaths, level 5 at 2.8 min.

## Run 2 (`../classes-run2/`): the same ladder, nine new characters — and a world hazard
| class | run 1 (deaths, L5 at) | run 2 (deaths, L5 at) |
|---|---|---|
| warrior | 0, 2.5 min | 1, 5.4 min |
| paladin | 0, 2.4 min | 0, 2.0 min |
| cleric | 0, 2.8 min | 0, 1.5 min |
| mage | 0, 2.9 min | 0, 2.9 min |
| ranger | 0, 2.9 min | 0, 2.3 min |
| assassin | 0, 2.9 min | 0, 5.0 min |
| necromancer | 0, 2.9 min | 1, 2.4 min |
| thief | 0, 3.6 min | 4, never (wrong-level "newbie" fights) → **1, 3.3 min** on the pinned ladder (`../classes-run2c/`) |
| bard | 0, 2.8 min | 7, never (wrong-level "newbie" fights) → **0, 2.0 min**, 12/12 on the pinned ladder (`../classes-run2c/`) |

Run 2 is not a tuning regression; it found a **world hazard**. "newbie" is the keyword of six
different creatures (levels 1 to 5) that wander the same Newbie Zone corridors, and the ladder
(like a real player typing `kill newbie`) got whichever was standing there: the bard at level 2
fought "newbie" creatures that `consider` correctly called DEADLY, and died seven times. The
thief (14 HP at level 1 — a low CON roll) died to the first fights outright. Two things follow:
1. The tool now pins every step to the creature's vnum and the escort loads it when the newcomer
   cannot see one (`curve.py`; a first attempt counted the word "newbie" in the room's own name and
   kept reading "absent" — `../classes-run2b/`). On the pinned ladder (`../classes-run2c/`) the bard
   wins 12 of 12 with no deaths and the thief 11 of 12 with one — **two runs per class now, nine of
   nine reaching level 5 in 1.5–5.4 minutes, with the only deaths being the keyword trap, one
   level-1 crawler fight on a 14-HP thief, and single late-ladder losses.**
2. For the human: the Newbie Zone's shared keyword is a trap the tutorial walks newcomers into
   ("Defeat 3 creatures in the Newbie Zone"). Distinct names (e.g. "newbie wanderer" L1-2,
   "newbie brute" L4-5), or keeping the L4-5 ones out of the entrance corridors, would remove
   it. Also: a level-1 thief or bard can start with 14 HP; a starting-HP floor is the same
   dial as the hit-dice floor, one level earlier.

## Caveats
- One run per class, one route; RNG on a single fight can still kill a level-1 character (run C
  in the parent record shows one such death on a different ladder).
- "Wandered off" steps mean the creature was not in any candidate room when the escort looked;
  they are not losses but they do shorten some classes' ladders (necromancer fought 8 of 12).
