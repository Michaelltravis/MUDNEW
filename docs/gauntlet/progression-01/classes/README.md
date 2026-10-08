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

## Caveats
- One run per class, one route; RNG on a single fight can still kill a level-1 character (run C
  in the parent record shows one such death on a different ladder).
- "Wandered off" steps mean the creature was not in any candidate room when the escort looked;
  they are not losses but they do shorten some classes' ladders (necromancer fought 8 of 12).
