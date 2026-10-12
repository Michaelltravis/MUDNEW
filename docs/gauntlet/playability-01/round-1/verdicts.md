# playability-01 / round 1 — verdicts

Key seed `2026-09-03T16:05:00Z:1`, reference BrowserQuest. Key: combat A=ref B=mh; fight A=ref B=mh.
Win rule (ab): overall pick decodes to mh AND more than half of judged labels decode to mh. Win rule (key): pass === true.

## feel (ab) — LOSS

| Label | Pick | Decoded |
|---|---|---|
| overall | A | ref |
| fight | A | ref |
| combat | A | ref |

Labels -> mh: 0/2. Overall -> ref. Confidence: high. **Result: LOSS.** Code left uncommitted in the working tree (`scene-topdown.js`, `ui.js`, `ui-arpg.js`; `fx-abilities.js` untouched).

### Critic reasons (verbatim)
- fight: A's bottom bar changes from a welcome line at 0.0s to 'You killed a rat' from 1.5s onward and the player's red HP bar visibly shortens across frames, so the outcome reads frame by frame; B's 8 frames are near-identical (knight stands beside the fountain, HP bar full in every frame) with no visible enemy, swing, or state change, so nothing tells you a fight is even happening.
- combat: A shows stacked damage numbers '4 / 6 / 6' floating above the player, a raised-sword swing pose, a white target box on the rat, and a second rat lying flat (dead) at the river, i.e. hit, target, and result are all legible; B shows only a 'corpse of grav...' label over a static knight, HP 207/207 untouched, no enemy sprite, no numbers, no flash.
- combat: A's HUD stays out of the play area (thin bottom bar with HP, weapon, armor, player count) while the action sits in open field; B's bottom bar packs a 1-5 skill row (attack/flee/bash/cleave/kick), three HP/mana/stamina bars and a NORMAL badge, but none of it reflects the moment, no cooldown state, no highlighted action, no threat prompt, so it never tells the player what to do next.

### Critic fixes (verbatim)
1. Make the enemy actually appear and telegraph: draw the mob sprite adjacent to the player with a visible wind-up pose or flash 0.3-0.5 s before its hit lands, then a recoil/knockback on impact so successive storyboard frames differ. (`src/web_isometric/platformer/scene-topdown.js`)
2. Add legible floating damage numbers (player and enemy), an impact flash on the target and a brief screen/sprite shake on hits and kills, plus a 'You killed X' style result line so who is winning reads without prose. (`src/web_isometric/platformer/fx-abilities.js`)
3. Make the skill bar reactive: highlight the ready/suggested ability, grey out on cooldown, pulse the target frame and show a small threat cue ('bash incoming') near the action, not over it. (`src/web_isometric/platformer/ui-arpg.js`)

Clerk note: the critic saw B (mh) frames with HP 207/207 untouched, no enemy sprite and a "corpse of grav..." label — i.e. the storyboard capture appears to have run after the grave keeper was already dead (or with the fight not yet started), so the builder's new tells/damage lanes/duel meter never appeared on camera. Worth checking the capture timing in `tools/gauntlet/` before round 2, alongside the critic's fixes.

## pacing (key) — WIN

| Question | Result |
|---|---|
| Q1 | pass |
| Q2 | pass |
| Q3 | pass |
| Q4 | pass |
| Q5 | pass |
| Q6 | pass |

pass = true. **Result: WIN.**

### Critic evidence (verbatim)
- Q1 fight_keeper: duration_s 41.2, ended mob_killed, rounds 11; '[t=  41.2s] grave keeper is DEAD! You killed grave keeper.' fight_bear: duration_s 35.6, ended mob_killed, rounds 9; '[t=  35.6s] Grimclaw the Great Bear is DEAD!'
- Q2 fight_keeper: first telegraph '[t=   0.8s] grave keeper rears back - a crushing blow is coming! (brace or sidestep!)'; 4 telegraph lines in transcript (0.8, 12.9, 25.1, 41.2s) vs rounds/4 = 2.75. fight_bear: first telegraph '[t=   3.3s] Grimclaw the Great Bear drops low and winds up to SWEEP the whole area'; 3 telegraph lines (3.3, 19.4, 35.6s) vs 2.25. NOTE: stats claim telegraph=12 and 8, overcounting the transcript.
- Q3 counted from transcripts: keeper 12 ticks, 5 with telegraph/stagger/press-the-opening (0.8, 12.9, 17.0, 25.1, 41.2) = 58% without decision, under the 60 cap; bear 10 ticks, 5 with (3.3, 11.3, 15.4, 19.4, 35.6) = 50% without. NOTE: stats report rounds_without_decision_pct 0 and decision_rounds 16 > rounds 11 - the stat counter is broken and was not relied on.
- Q4 keeper player_hit 11 / miss 0: '[t=  12.9s] grave keeper reels - STAGGERED! Strike now!' then '[t=  17.0s] You press the opening while grave keeper reels - wide open!'. bear player_hit 10 / miss 0: '[t=  11.3s] ... STAGGERED! Strike now!' then '[t=  15.4s] You press the opening while Grimclaw the Great Bear reels - wide open!'. Only player command in either transcript is 'kill'; no brace/sidestep was ever typed.
- Q5: no 'Your <adjective> <verb>s' forms. Nearest repetition: bear 'Your slash devastates Grimclaw the Great Bear! [36 damage]' at 15.4s and 27.5s; 'Your slash connects - it devastates ...' at 11.3/23.5/35.6s - never 3 consecutive rounds. Minor: bear '*** CRITICAL HIT! ***' at 23.5s and 35.6s deals 36, identical to non-crit hits.
- Q6: player HP never crossed 25% (keeper min 136/207 = 66%, bear min 159/207 = 77%), low_hp_nag 0 both - single-warning rule untested rather than violated. Mob HP bar moved 100% in both fights (802->0 in 41.2s, 364->0 in 35.6s).

### Critic fixes
None.
