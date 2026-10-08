# progression-01 — the first ten minutes, measured

Tool: `tools/gauntlet/curve.py` (two telnet sessions: a genuine level-1 warrior forged through the
creation wizard with its starting kit, plus an admin escort that repops each room, transfers the
newcomer in and restores after a death so the ladder continues). Bar from the plan: **level 5
inside ~15 minutes with no deaths on the newcomer ladder, using only what the screen teaches.**

| run | play style | level reached | deaths | time to L2 | record |
|---|---|---|---|---|---|
| A | auto-attack only (`--dumb`) | 1 | 2 | never (339/800 xp after 5 fights) | `run-a-autoattack/` |
| B | the three buttons: bash to open, brace on the wind-up prompt | 2 | 2 | 9.5 min | `curve.md`, `fights/` |

## What the numbers say
1. **The three buttons are the difference between dying and winning at level 1–2.** On
   auto-attack a level-2 "Even" street urchin kills a fresh warrior in five rounds (19 HP, slash
   for 2–3 vs 48 HP). With bash + brace the same tier is won every time at 8–14 HP left. So the
   Guide / welcome card teaching exactly those two buttons is load-bearing, not decoration.
2. **Level 5 in 15 minutes is not met.** Level 2 arrives at 9.5 minutes. Base 800 xp per level
   against 70–140 xp per newcomer kill means ~6 kills a level with 30–45 s fights and 20–30 s
   rests between; level 5 is on the order of 40 minutes at this pace.
3. **The step from "Even" to "Challenging" is a cliff.** A level-5 mercenary kills the level-1
   warrior in 2.3 s (one exchange) and the pickpocket likewise. `consider` says Challenging, which
   reads as "hard but possible"; at level 1 it means "instant death".
4. Two fights timed out at full HP: the beggar (16 rounds, never hurt him — wimpy/flee loop) and
   the pet-shop wolf (11 bashes, no damage either way). Both are either unhittable or fleeing in
   place; neither is a useful newcomer fight.
5. Deaths cost a real player a corpse run from the temple; here the escort restored them. Real
   first-ten-minutes with two deaths would be ~3 minutes longer and far more discouraging.

## Decisions for the human (not retuned here)
- XP: either lower `BASE_EXP`/`EXP_MULTIPLIER` for levels 1–5 or raise newcomer-kill XP so that
  level 5 lands near 15 minutes (≈ 2–3 kills per level for the first four levels).
- `consider` wording at low level: "Challenging" should not be reachable from "Even" by one
  room; add a "Deadly" tier below level 5 or gate the Dark Alley (3026) behind level 4.
- Make the training-grounds and Main Street animals (fido, rat) sentinel or add a second training
  dummy tier, so the first three fights are always where the Guide sends you.
- Beggar and pet-shop animals: mark no-fight (shop pets) or give them hittable stats.

## Not a gauntlet piece
There is no BrowserQuest reference for progression (it has no levels). This record is the
measurement itself; a future round can re-run `curve.py` after retuning and compare the table.
