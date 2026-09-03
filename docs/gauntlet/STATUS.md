# Gauntlet status

**Run:** playability-01 — **round 2 of 3 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`).
**Pieces:** feel (ab; labels: fight, combat; files `src/web_isometric/platformer/{scene-topdown,fx-abilities,ui,ui-arpg}.js`) and pacing (key; six-question pass/fail; files `src/combat.py`, `src/mob_ai.py`, `src/config.py`).
Win rules: ab = overall pick -> mh AND >1/2 labels -> mh; key = pass === true.
**Round records:** `docs/gauntlet/playability-01/round-<n>/` (`verdicts.md`, `builder-*.md`, `critic-*.json`, `fight/*.txt|json`; `mh/` and `pairs/` gitignored). Key seeds: round 1 `2026-09-03T16:05:00Z:1`, round 2 `2026-09-03T16:05:00Z:2`.
Previous runs graphics-01 and graphics-02 are complete (hud won under the majority rule, `d648ea1`).

## History
| Run | Round | feel | pacing |
|---|---|---|---|
| playability-01 | 1 | LOSS (0/2: fight A -> ref, combat A -> ref; overall ref; confidence high) — code left uncommitted | **WIN** (6/6 pass) — code + records `cf2a4c4` |
| playability-01 | 2 | LOSS (0/2: fight B -> ref, combat B -> ref; overall ref; confidence high) — code left uncommitted; records committed | closed (not judged) |

## Open pieces
- **feel** — round 3 (last round of the budget). Critic fixes: (1) floating damage numbers (white out / red in) + 2-3 frame white impact flash + recoil on every damage resolve (`fx-abilities.js`); (2) enemy wind-up (pull-back / red tint ~0.4 s), stagger pose after being hit, and enemies actually closing to melee range (`scene-topdown.js`); (3) target reticle around the engaged enemy with HP bar + name over its head, and highlight the applicable hotbar slot (`ui-arpg.js`). Round-2 feel code (scene-topdown.js, ui.js, ui-arpg.js: wall-clock damage numbers, adjacent mob stance, last-beat tell, SLAIN stamp, kill result plate, reactive action bar) is still in the working tree, uncommitted, for the round-3 builder to build on or discard. Most of fixes 1-3 already exist in that uncommitted code; the critic never saw them (see blocker below).
- pacing: closed (won round 1).

## Blockers / notes for the human brake
- **STOP: the feel storyboard has now captured the wrong moment two rounds running.** Round 2's critic again describes A as HP 207/207 in every frame, no enemy within a screen-width, a faded "corpse of ..." label, no damage numbers — i.e. the capture ran against an already-dead keeper. The round-2 builder verified its work on a live keeper fight with a scratch copy of the capture flow and reported that `page.screenshot()` takes ~6-7 s here (frames ~8 s apart, kill around frame 5-6), and that headless Phaser ran tweens 20-50x slow (fixed in `create()`/`update()`). Before round 3: fix `tools/gauntlet/capture.js` so it (a) `zreset`s / respawns the keeper, (b) starts frames only after the first round payload arrives, and (c) uses short-interval frames (JPEG/lower res) so 8 frames cover ~10 s of fight. Spending the last round on feel without this fix wastes it.
- **Fight stats counter is broken** (from round 1): `fight/*.json` telegraph/decision_rounds counts do not match the transcripts (round 2: keeper telegraph=9, decision_rounds 13 > rounds 12). Count from transcripts. Not a pacing regression.
- Pacing minor: boss `*** CRITICAL HIT! ***` deals the same as non-crit hits (10% max-HP swing cap flattens crits). Q6 single-low-HP-warning rule still untested.
- Builder caveat: `tools/gauntlet/capture.js` and the smoke suite log in as the same `Gauntlet` character; overlapping logins truncate fight transcripts. Run fight.py alone on a freshly restarted server.
- `logs/tests.log` and `docs/gauntlet/scratch/` are modified/untracked from builder runs; not committed.

Next command: fix the feel storyboard capture timing in tools/gauntlet/capture.js (verify a frame shows a damage number before proceeding), then: gauntlet playability-01 round 3 (piece: feel)
