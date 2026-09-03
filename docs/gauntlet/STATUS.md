# Gauntlet status

**Run:** graphics-02 — **round 1 of 3 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Pieces:** hud only (labels: city, dungeon). Win rule: majority (overall pick -> mh AND >1/2 labels -> mh).
**Round records:** `docs/gauntlet/graphics-02/round-1/` (`verdicts.md`, `builder-hud.md`, `critic-hud.json`; `mh/` and `pairs/` gitignored). Montage seed `2026-09-03T14:25:00Z:1`. Records committed `abca337`.
Previous run graphics-01 is complete (see `docs/gauntlet/graphics-01/`); its hud win was on the overall pick only (1/3 labels, confidence low), which is why graphics-02 re-opens hud under the majority rule.

## History
| Run | Round | hud |
|---|---|---|
| graphics-01 (restart) | 1-3 | WIN in r3 on overall pick only (1/3 labels, confidence low) `4a29fb8` |
| **graphics-02** | **1** | **LOSS** (0/2: city ref, dungeon ref; overall A -> ref; confidence high) — records `abca337`, code left uncommitted |

## Open pieces
- **hud** — lost round 1. Builder enlarged HP to a 28px bar / 16px numerals, demoted MP/MV, ghosted PANELS and the clock, hid unused compass keys, added a frame vignette. Critic nevertheless saw ~4px vital slivers with 7px numerals, six HUD zones, and translucent ambient prose floating over the playfield. Fixes for round 2 (verbatim in `round-1/verdicts.md`): one big HP bar with pulse-on-damage (`ui-arpg.js`); route room/ambient prose into a single backed feed strip instead of over the playfield (`ui.js`); cut HUD zones six -> three, drop WASD diagram and top-right readout, all HUD text >=11px with outline/backdrop (`platformer.html`).
  Uncommitted round-1 edits in `src/web_isometric/platformer.html` and `src/web_isometric/platformer/ui.js` remain in the working tree for the round-2 builder to build on.

## Blockers
- Builder/critic mismatch: builder reports a 28px HP bar, critic measured ~4px slivers. Round-2 builder must check `tools/gauntlet/capture.js` output at montage scale before iterating, in case the appended CSS block is not reaching the capture or the montage downscale is eating it.
- `logs/tests.log` is modified in the working tree by the builder's test run; not committed.
- Builder self-check: `tests/test_suite.py --smoke` still fails at telnet login (pre-existing account-menu reason, server expects `play Tester`). Not a gauntlet regression.

Next command: Workflow resume graphics-02 round 2 (pieces: hud)
