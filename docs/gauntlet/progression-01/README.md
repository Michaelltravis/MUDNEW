# progression-01 — the first ten minutes, measured

Tool: `tools/gauntlet/curve.py` (two telnet sessions: a genuine level-1 warrior forged through the
creation wizard with its starting kit, plus an admin escort that repops each room, transfers the
newcomer in and restores after a death so the ladder continues). Bar from the plan: **level 5
inside ~15 minutes with no deaths on the newcomer ladder, using only what the screen teaches.**

| run | play style | curve | level reached | deaths | time to L2 / L5 | record |
|---|---|---|---|---|---|---|
| A | auto-attack only (`--dumb`) | 800 xp base | 1 | 2 | never / never | `run-a-autoattack/` |
| B | three buttons: bash to open, brace on the wind-up | 800 xp base | 2 | 2 | 9.5 min / — | `run-b-three-buttons/` |
| C | three buttons | **newcomer ramp 250/350/500/650** + DEADLY tier below L6 | **5** | 1 | 3.6 min / **5.1 min** | `curve.md`, `fights/` |

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

## After the retune (run C)
- `NEWCOMER_EXP = (250, 350, 500, 650)` (config-overridable, `player.exp_to_level`) and a DEADLY
  `consider` verdict below level 6 for any target three or more levels up (`cmd_consider`).
- Level 5 at 5.1 minutes — inside the 15-minute bar with room to spare; the Dark Alley pair that
  one-shot the level-1 character reads "Even" by level 4–5 and is won at 17–29 HP left.
- One death remains: the level-2 drunk at level 1 (RNG — the same fight was won at 11/19 in run
  B). The "no deaths" half of the bar is not guaranteed; the honest statement is "a newcomer who
  presses the two taught buttons usually survives the first ten minutes and reaches level 5 in
  about five". A one-kill double level (1 → 3 on the urchin) shows the ramp is now generous at
  the very bottom; 300/400/500/650 would smooth it if the human prefers a slower first level.
- Still open for the human: sentinel first targets (fido wandered again — a 90 s timeout at full
  HP), and the beggar / shop pets that cannot be hurt.

## Not a gauntlet piece
There is no BrowserQuest reference for progression (it has no levels). This record is the
measurement itself; a future round can re-run `curve.py` after retuning and compare the table.
