# Gauntlet status

**Run:** playability-01 — **round 3 of 3 done (budget exhausted)**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`).
**Pieces:** feel (ab; labels: fight, combat; files `src/web_isometric/platformer/{scene-topdown,fx-abilities,ui,ui-arpg}.js`) and pacing (key; six-question pass/fail; files `src/combat.py`, `src/mob_ai.py`, `src/config.py`).
Win rules: ab = overall pick -> mh AND >1/2 labels -> mh; key = pass === true.
**Round records:** `docs/gauntlet/playability-01/round-<n>/` (`verdicts.md`, `builder-*.md`, `critic-*.json`, `fight/*.txt|json`; `mh/` and `pairs/` gitignored). Key seeds: round 1 `2026-09-03T16:05:00Z:1`, round 2 `...:2`, round 3 `...:3`.
Previous runs graphics-01 and graphics-02 are complete (hud won under the majority rule, `d648ea1`).

## History
| Run | Round | feel | pacing |
|---|---|---|---|
| playability-01 | 1 | LOSS (0/2: fight A -> ref, combat A -> ref; overall ref; confidence high) — code left uncommitted | **WIN** (6/6 pass) — code + records `cf2a4c4` |
| playability-01 | 2 | LOSS (0/2: fight B -> ref, combat B -> ref; overall ref; confidence high) — code left uncommitted; records `724eb2e` | closed (not judged) |
| playability-01 | 3 | LOSS (0/2: fight B -> ref, combat B -> ref; overall ref; confidence high) — code left uncommitted; records committed | closed (not judged) |

## Open pieces
- **feel** — lost all three rounds; round budget exhausted. Round-3 critic fixes: (1) enemy wind-up 0.3-0.5 s before the hit, impact flash, knockback recoil, floating damage number for both sides (`fx-abilities.js`); (2) reticle/HP bar over the engaged enemy, enemy contrast/outline against the fog (`scene-topdown.js`); (3) pulse the relevant hotbar key and flash the HP bar on damage (`ui-arpg.js`). The round-2+3 feel code (scene-topdown.js +388, ui.js +257, ui-arpg.js +31: gold target bracket + wide HP bar, parked damage ledger, wall-clock hit flash + red wash + reel, 40 px melee stance, reaction prompt above the hotbar, reactive action bar) is still in the working tree, uncommitted, and already implements most of fixes 1-3. Human decision needed: extend the run by one round after fixing the capture, or drop the code.
- pacing: closed (won round 1).

## Blockers / notes for the human brake
- **STOP: the feel storyboard captured a dead keeper three rounds running.** Every critic verdict describes A as a static knight with no enemy on screen and a "corpse of ..." label. The round-3 builder reproduced this exactly: the lead's fight transcripts kill the keeper minutes before `tools/gauntlet/capture.js` runs and capture.js does not `zreset`. With `zreset` first, a live fight appears in frames 0-3. `capture.js` was not fixed before round 3 (the round-2 STATUS asked for it), so the critic has never seen the feel code. Required before any further feel round: (a) `zreset`/respawn the target in capture.js, (b) start frames only after the first round payload arrives, (c) short-interval frames (JPEG/lower res; `page.screenshot()` takes ~6-7 s here) or a tankier target / lower `advance` so 8 frames cover the exchange, (d) verify a frame shows a damage number before running the critic.
- **Fight stats counter is broken** (since round 1): `fight/*.json` decision_rounds > rounds (round 3: keeper 20 > 15, grimclaw 16 > 13). Count from transcripts. Not a pacing regression.
- Pacing minor: boss `*** CRITICAL HIT! ***` deals the same as non-crit hits (10% max-HP swing cap flattens crits). Q6 single-low-HP-warning rule still untested.
- Builder caveat: `capture.js` and the smoke suite log in as the same `Gauntlet` character; overlapping logins truncate fight transcripts. Run fight.py alone on a freshly restarted server.
- `logs/tests.log` and `docs/gauntlet/scratch/` are modified/untracked from builder runs; not committed.

Next command: human decision — fix tools/gauntlet/capture.js (zreset before kill, frames after first round payload, verify a damage number is on film), then either `gauntlet playability-01 round 4 (piece: feel, budget extension)` or `git checkout -- src/web_isometric/platformer/` to drop the uncommitted feel code and close the run.
