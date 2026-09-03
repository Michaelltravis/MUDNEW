# Gauntlet status

**Run:** playability-02 — **round 1 of 2 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`).
**Pieces:** feel (ab; labels: fight, combat; files `src/web_isometric/platformer/{scene-topdown,fx-abilities,ui,ui-arpg}.js`). Pacing closed in playability-01 (won round 1, `cf2a4c4`).
Win rules: ab = overall pick -> mh AND >1/2 labels -> mh; key = pass === true.
**Round records:** `docs/gauntlet/playability-02/round-<n>/` (`verdicts.md`, `builder-*.md`, `critic-*.json`, `fight/*.txt|json`; `mh/` and `pairs/` gitignored). Key seed round 1 `2026-09-03T20:10:00Z:1`.
Capture fixes since playability-01 (`3c9d92e`, `bc8d845`): zreset before scripted fights, 1 s storyboard frames — the critic now films a live fight.
Previous runs: graphics-01/02 complete (`d648ea1`); playability-01 complete (pacing won; feel lost 3/3 against a dead-keeper capture, code carried forward into this run).

## History
| Run | Round | feel |
|---|---|---|
| playability-02 | 1 | **WIN** (2/2: fight B -> mh, combat B -> mh; overall mh; confidence high) — code + records `cf05cb3` |

## Open pieces
- none. feel won round 1; its round-2 slot is unused. The critic's three fixes describe the reference (A), not Misthollow, so there is nothing to carry into a round 2.

## Blockers / notes for the human brake
- Fight stats: round-1 `fight/summary.json` is consistent this time (keeper 7/7 rounds, bear 11/11 decision rounds; 0% rounds without decision). The earlier decision_rounds > rounds bug did not reproduce.
- Builder caveat still stands: `python3 tests/test_suite.py --smoke` fails at login for account characters (known); `node tools/qc_platformer_rooms.js` passes.
- Pacing minor (carried): boss crits deal the same as non-crit hits under the 10% max-HP swing cap; Q6 single-low-HP-warning rule still untested.
- `logs/tests.log` is modified from builder runs; not committed.

Next command: human decision — close playability-02 (all pieces won; round 2 not needed) or `gauntlet playability-02 round 2 (piece: feel)` only if a new label/bar is wanted.
