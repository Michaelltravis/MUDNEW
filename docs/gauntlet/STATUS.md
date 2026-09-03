# Gauntlet status

**Run:** playability-01 — **round 1 of 3 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`).
**Pieces:** feel (ab; labels: fight, combat; files `src/web_isometric/platformer/{scene-topdown,fx-abilities,ui,ui-arpg}.js`) and pacing (key; six-question pass/fail; files `src/combat.py`, `src/mob_ai.py`, `src/config.py`).
Win rules: ab = overall pick -> mh AND >1/2 labels -> mh; key = pass === true.
**Round records:** `docs/gauntlet/playability-01/round-1/` (`verdicts.md`, `builder-*.md`, `critic-*.json`, `fight/*.txt|json`; `mh/` and `pairs/` gitignored). Round-1 key seed `2026-09-03T16:05:00Z:1`.
Previous runs graphics-01 and graphics-02 are complete (hud won under the majority rule, `d648ea1`).

## History
| Run | Round | feel | pacing |
|---|---|---|---|
| playability-01 | 1 | LOSS (0/2: fight A -> ref, combat A -> ref; overall A -> ref; confidence high) — code left uncommitted | **WIN** (6/6 pass) — code + records `cf2a4c4` |

## Open pieces
- **feel** — round 2. Critic fixes: (1) draw the mob sprite adjacent to the player with a visible wind-up pose/flash 0.3-0.5 s before the hit and recoil/knockback on impact so storyboard frames differ (`scene-topdown.js`); (2) legible floating damage numbers for both sides, impact flash, brief shake on hits/kills, and a "You killed X" result line (`fx-abilities.js`); (3) reactive skill bar — highlight ready/suggested ability, grey cooldowns, pulse the target frame, small threat cue near the action (`ui-arpg.js`). Round-1 feel code (scene-topdown.js, ui.js, ui-arpg.js) is still in the working tree, uncommitted, for the round-2 builder to build on or discard.
- pacing: closed (won round 1).

## Blockers / notes for the human brake
- **Feel storyboard likely captured the wrong moment.** The critic's B (mh) frames show HP 207/207 in every frame, no enemy sprite and a "corpse of grav..." label — i.e. the capture ran after the grave keeper was already dead or before the fight began, so none of the builder's new tells/damage lanes/duel meter were on camera. Check `tools/gauntlet/` capture timing (spawn + fight start vs. frame window) before round 2, or the feel builder will lose again regardless of the code.
- **Fight stats counter is broken** (critic Q2/Q3 notes): `fight/*.json` reports telegraph=12/8 vs 4/3 lines in the transcript, `decision_rounds` 16 > rounds 11, and `rounds_without_decision_pct` 0. The critic counted from transcripts instead. Fix the counter in the fight harness before it is relied on; not a pacing regression.
- Pacing minor: bear `*** CRITICAL HIT! ***` deals 36, identical to non-crit hits (boss swing cap at 10% max HP flattens crits). Q6 single-low-HP-warning rule was untested (player never fell below 66%).
- Builder caveat: `tools/gauntlet/capture.js` and the smoke suite log in as the same `Gauntlet` character; overlapping logins truncate fight transcripts mid-way. Run fight.py alone on a freshly restarted server.
- `logs/tests.log` and `docs/gauntlet/scratch/` are modified/untracked from builder runs; not committed.

Next command: gauntlet playability-01 round 2 (piece: feel) — after checking the storyboard capture timing above
