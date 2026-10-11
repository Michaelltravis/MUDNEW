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
  the balcony fight to 21 rounds and lost it. `sidestep` worked on 2 of 3 prompts (the wind-up
  survives the player's stagger — checked in `mob_ai.py`: an intent is cleared only by interrupt,
  death or the fight ending); the one miss, on the fight's first telegraph, answered "Nothing is
  winding up" and is unexplained from the transcript. Brace never checks, so it never "misses".
  Design observation for the human: defensive stance's trade (−hit/−dam for +AC/+PB) is a net
  loss for a 67-HP warrior at this tier — the fight it prolongs does more damage than it saves.
- Spectre and minotaur could not be measured: after the first run `zreset` did not bring them
  back inside the ladder's window (tool limitation, same cause as "wandered off" above). Confound:
  the three-button run levelled the character to 6 before the mastery run.

### Mastery v2: perfect strikes (`mastery-three-l6/`, `mastery-pro/`)
Dropping the defensive stance and instead timing `swing` into the last stretch of every round
(the PERFECT STRIKE: +damage, double stagger), with sidestep on the heavy wind-ups:

| play | pitbeast (L5) fight | swings / PERFECT lines |
|---|---|---|
| three buttons, level 6 | won at **48/76 HP**, 15 rounds | — |
| perfect strikes + sidestep, level 7 | won at **83/83 HP** (untouched), 21 rounds | 7 / 12 |

That is the depth biting the way it should — the timed strike and the sidestep turn a fight that
costs a third of your health into one that costs nothing — **but it is one comparable fight**
(the goblins and the minotaur had wandered off or not repopped for the v2 run) and the levels
differ by one. The v1 lesson stands: the losing "mastery" was the defensive stance, not the
reaction systems. To make this a real measurement the ladder needs creatures that stay put
(sentinel copies in a test zone, or a `zreset` that re-seats wanderers); recorded as a tool task.

### Mastery v3: equal footing, guaranteed creatures (`mastery-v3/{dumb,three,pro}/`)
Three freshly forged warriors, each advanced to level 5 by the escort, the same six fights with
the creature loaded if it had wandered (`mload`, fixed on the way — it crashed the caller's
connection). Caveat: `advance` rolls hit dice, so max HP differed (52 / 32 / 38).

| play | max HP | deaths | where |
|---|---|---|---|
| auto-attack | 52 | **4** | spectre, minotaur, both goblin packs |
| three buttons (bash + brace) | 32 | 1 | second goblin pack (9/32) |
| perfect strikes + sidestep + cleave | 38 | 2 | spectre (20/38 → dead), minotaur (3/38) — 10–11 PERFECT strikes each, 16–19 rounds |

What this says:
- **The tier punishes auto-attack hard** (four deaths on 52 HP) and **the two taught buttons
  are enough** (one death on 32 HP). Easy to start holds up one tier past the newcomer zone.
- **The deeper layer, as a bot plays it, still does not beat the buttons.** Perfect strikes land
  (10–11 per fight) but the fights run twice as long: `sidestep` forgoes your own attack and a
  mistimed `swing` (the bot polls once a second against a 1.7 s window) locks you out for the rest
  of the round. With 38 HP against the three-button warrior's 32 it still died twice. Either the
  mechanic rewards human timing the bot cannot reproduce, or its tempo cost is too high at this
  tier — only a human playthrough can tell which. That is the honest state of "hard to master":
  the systems exist and bite, but they have not yet been shown to out-perform the basics.

### Mastery v4: with the riposte (`mastery-v4/{pro,three}/`)
A clean sidestep now makes the next strike perfect (`mob_ai._mitigate_hit`). Two fresh level-5
warriors, same guaranteed six fights:

| play | max HP | deaths | HP left per win |
|---|---|---|---|
| perfect strikes + sidestep + cleave | 48 | 1 (second goblin pack, 10/48) | 28, 43, 27, 33, 45 |
| three buttons (bash + brace) | 35 | 1 (second goblin pack, 14/35) | **35, 35, 35, 35**, 30 |

Same deaths, same fight. The three-button warrior finished four fights **untouched** on 13 fewer
HP; the riposte never fired because the bot sidestepped once in six fights (brace answers most
wind-ups first). Reading across v3 and v4: at this tier **brace + bash is the dominant play and
the perfect-strike/sidestep layer adds nothing a bot can demonstrate**. The riposte stays (it
only ever helps), but "hard to master" is not yet evidenced by numbers; it needs either a human
playthrough or a tier where brace alone is not enough (bosses with interruptible casts, AoE that
must be evaded) — that is the next measurement if the human wants one.

### Boss tier (`boss-v1/{dumb,three,pro}/`)
The two lowest bosses in the world, loaded into their lairs, against three fresh warriors advanced
to level 10 (spider queen L12 "Moderate", alpha wolf L14 "Even/Challenging", each twice):

| play | deaths | results |
|---|---|---|
| auto-attack | **2** | queen killed it (2/62), wolf killed it (11/62) |
| three buttons (bash + brace) | 0 | queen won 14/82; wolf won 61/82; second wolf **timed out** at 73/82 (18 rounds, 150 s) |
| perfect strikes + sidestep + cleave | 0 | queen won 13/78; wolf won 8/78 and 22/78 — 14–20 PERFECT strikes per fight |

- **The boss tier kills auto-attack outright** and both reaction styles survive it. The perfect-
  strike player is the only one to *finish* every boss inside the window: three-button play ran
  out the clock on the second alpha wolf. That is the first number in which the deeper layer
  beats the basics — on kill speed, not on safety.
- Caveat that matters: neither boss declared an interruptible cast or an AoE slam in any run.
  The spider queen fights with a legacy "Venomous Strike" heavy wind-up (brace/sidestep), the
  alpha wolf with its pack's lunges; the boss ability table (Ground Slam, Terrifying Roar, Summon
  Minions) lives on the `Boss` class's own AI and did not fire for these two. So `interrupt` is
  still unmeasured. A boss that actually casts (zone 200's higher bosses, or any `caster` role
  elite) is the next ladder if the human wants the interrupt mechanic proven.

### Caster tier (`caster-v1/{three,pro}/`, `caster-v2/pro/`)
Six mid-level casters (mages L10–13, a wizard L15) loaded into their rooms, fresh level-10
warriors. The casters declare their spells with "(interrupt it!)" — the only ladder where
`interrupt` can be measured.

| play | deaths | what happened |
|---|---|---|
| three buttons (cannot interrupt) | 5 of 6 | fireballs land for 27–42 a hit on 75 HP |
| reaction layer, interrupt at the old 35% | 4 of 5 | prompted interrupts failed **3 of 3**; a L12 mage's fireball hit for **82** on a 73-HP warrior — dead from 60/73 |
| reaction layer, interrupt at 70% + kick/4 (`cmd_interrupt`, changed) | 2 of 5 | 2 interrupts landed, 2 failed; the two deaths were a **90** fireball from 50/82 and the L15 wizard ("Dangerous", expected) |

What this says:
- **Interrupt now matters**: with a reliable answer to the prompt, the warrior wins the L12 and
  L13 mages it died to before. That completes the mastery picture: brace for heavy blows,
  sidestep for the riposte, interrupt for casts, perfect strikes for kill speed — each measured
  in the tier where it bites.
- **The remaining cliff is the mob fireball itself**: 82–90 damage from a "Moderate" level-12
  caster against a level-10 warrior's 73–82 HP is a one-shot from above half health. No
  reaction mechanic should have to carry that; it is a caster-spell scaling dial
  (`_cast_offensive` in `mob_ai.py`) and it is left for the human.
- Interrupt's 8 s cooldown after a failure means a second cast in the same fight cannot be
  answered; at 70% that is now the main way a caster fight is lost.

**Caster v3 — spell capped at 60% of max HP for non-boss casters** (`caster-v3/`): the two
buttons die 3 of 6 (was 5 of 6), the reaction layer 3 of 5 (was 4 of 5, then 2 of 5). No more
one-shots: the biggest spell hit is now exactly the cap (51 on an 85-HP warrior) and deaths come
from accumulated damage against "Challenging"/"Dangerous" targets, which is what those words
should mean. Two things this surfaced for the human:
1. **Hit-dice variance.** Two level-10 warriors forged the same way rolled **53** and **85** max HP.
   A 60% cap is 31 for one and 51 for the other; the same "Moderate" mage is a fair fight for one
   and a coin-flip for the other. Level-up HP rolls (`player.level_up`, `random.randint(1,
   hit_dice)`) are the widest variance in the whole progression record. **Set**: the per-level
   roll now starts at half the hit die; three warriors forged and advanced to level 10 afterwards
   read 93, 95 and 110 max HP (before: 53, 73, 78, 82, 85 across the ladder runs).
2. The L12 "Moderate" mage still killed each warrior once in two tries; "Moderate" for a caster
   two levels up is optimistic. Either the `consider` tiers should weigh caster roles up a step,
   or the cap should be lower for "Moderate" gaps. **Set**: `consider` weighs a caster one level
   step up, so that mage now reads "Challenging" to a level-10 character.

### Second runs of the tiers (`mastery-v4b/`, `boss-v1b/`, `caster-v3b/`)
Fresh warriors, same ladders, same play styles, to put n=2 behind each tier:

| tier | play | run 1 deaths | run 2 deaths | max HP (run 2) |
|---|---|---|---|---|
| mastery (L5) | three buttons | 1 | 1 | 58 |
| mastery (L5) | reaction layer | 1 | 3 | 40 |
| boss (L10) | three buttons | 0 (one timeout) | 0 | 100 |
| boss (L10) | reaction layer | 0 | 1 (alpha wolf, 2/109) | 109 |
| caster (L10) | three buttons | 3 of 6 | 2 of 6 (wizard L15, mage L13) | 116 |
| caster (L10) | reaction layer | 3 of 5 | 2 of 5 (mage L13, wizard L15); interrupts 2 landed, 0 failed | 87 |

Read together with run 1: **at the mastery and boss tiers the two taught buttons are the most
reliable play**; at the caster tier both styles lose to the "Dangerous" level-15 wizard and the
aggressive level-13 mage and beat the level-12 mages, with the reaction layer finishing one fight
untouched on a 29-HP-lighter character and every prompted interrupt landing; and the reaction layer's run-1 edge on the bosses (finishing the wolf that
three-button play timed out on) did not repeat — the second reaction-layer warrior died to the
alpha wolf once and finished it untouched the second time. The reaction layer's *measured* edge
is at the caster tier (interrupt), and the pack is what punishes auto-attack. Max HP still varies
widely at the same level (40 vs 58 at level 5) even with the hit-dice floor: four level-ups at
d10 floored at 5 still span 20 HP, which decides the mastery-tier fights more than the play does.

## Not a gauntlet piece
There is no BrowserQuest reference for progression (it has no levels). This record is the
measurement itself; a future round can re-run `curve.py` after retuning and compare the table.
