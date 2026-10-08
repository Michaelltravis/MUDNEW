# progression-01 — the first ten minutes, measured

Tool: `tools/gauntlet/curve.py` (two telnet sessions: a genuine level-1 warrior forged through the
creation wizard with its starting kit, plus an admin escort that repops each room, transfers the
newcomer in and restores after a death so the ladder continues). Bar from the plan: **level 5
inside ~15 minutes with no deaths on the newcomer ladder, using only what the screen teaches.**

| run | play style | curve | level reached | deaths | time to L2 / L5 | record |
|---|---|---|---|---|---|---|
| A | auto-attack only (`--dumb`) | 800 xp base | 1 | 2 | never / never | `run-a-autoattack/` |
| B | three buttons: bash to open, brace on the wind-up | 800 xp base | 2 | 2 | 9.5 min / — | `run-b-three-buttons/` |
| C | three buttons, Midgaard bars and alleys | newcomer ramp 250/350/500/650 + DEADLY tier below L6 | 5 | 1 | 3.6 min / 5.1 min | `run-c-ramp-midgaard/` |
| D | three buttons, **the tutorial's own route** (dummy → Newbie Zone) | same ramp | **5** | **0** | 1.3 min / **2.5 min** | `curve.md`, `fights/` |

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

## Run D: the route the Guide actually walks
- Runs A–C fought Midgaard's drunks, urchins and alley thugs because that is what the ladder
  picked; the tutorial chain never sends a newcomer there. Its real route is the training dummy,
  then the Newbie Zone (18600+: crawlers L1, newbies L2–5, keeper and quasits L3, pitbeast L5).
- On that route a fresh warrior wins all twelve fights, never drops below half HP, and reaches
  level 5 in 2.5 minutes with no deaths — the bar is met on both halves. (It is now brisk: if
  the human wants the first five levels to take closer to ten minutes, `NEWCOMER_EXP` of
  300/450/600/800 is the dial, nothing else needs touching.)
- Found on the way, and fixed: the tutorial quest "Into the Unknown" sent level-1 characters out
  the **East** Gate to fight "a rabbit, a fox, or a deer — safe for your level"; the only creatures
  east of that gate are level-4 aggressive goblins. The rabbits and foxes live beyond the **West**
  Gate (6001 and the shaded paths north of it); the quest now routes there (`src/quests.py`).
- Still for the human: the beggar / shop-pet rooms are `godroom` (no fighting — correct, they
  just must not be suggested as fights), and Midgaard's own level 2–4 fights are thin (one drunk
  in a bard-only tavern, a wandering urchin, a wandering patron) — fine as long as the chain
  keeps pointing at the Newbie Zone and the forest.

## Hard to master? The mastery ladder (`mastery-{dumb,three,pro}/`)
The same level-5 warrior (`NewSlzkb`) one tier up — balcony newbie L5, the Light Forest goblin
pack (L4 ×2, aggressive), minotaur L7 / spectre L6 — played three ways:

| play | deaths | notes |
|---|---|---|
| auto-attack | 2 | both deaths to the goblin pack (22/67 then 8/67 HP) |
| three buttons (bash + brace) | 0 | pack beaten at 76/76 and 28/76; levelled to 6 on the first fight |
| "mastery" (defensive stance, sidestep, interrupt, cleave alternated) | 1 | died to the balcony newbie after 21 rounds; pack beaten at 32/76 and 54/76 |

What this says, honestly:
- The pack is the first thing that **punishes** auto-attack: reacting to the wind-up prompt is
  the difference between two deaths and none. That is the "hard to master" edge biting, one tier
  past the newcomer zone.
- The scripted "mastery" layer did **not** outperform the three buttons. Defensive stance stretched
  the balcony fight to 21 rounds and lost it; `sidestep` answered "Nothing is winding up" because
  the player's own blow in the same round staggered the creature and cancelled the wind-up (the
  telegraph and the stagger arrive in one packet). Brace "works" only because it never checks.
  Two design observations for the human: (1) a stagger that cancels a declared wind-up makes the
  reaction prompt moot in the common case — either the prompt should not print when the mob is
  about to be staggered, or the stagger should not cancel; (2) defensive stance's trade at this
  tier is a net loss for a warrior with 67 HP.
- Spectre and minotaur could not be measured: after the first run `zreset` did not bring them
  back inside the ladder's window (tool limitation, same cause as "wandered off" above). Confound:
  the three-button run levelled the character to 6 before the mastery run.

## Not a gauntlet piece
There is no BrowserQuest reference for progression (it has no levels). This record is the
measurement itself; a future round can re-run `curve.py` after retuning and compare the table.
