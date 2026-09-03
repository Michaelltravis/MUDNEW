# Gauntlet status

**Run:** graphics-01 (round 2 of 3 complete; the Workflow loop continues into round 3 with the open piece). Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Round records:** `docs/gauntlet/graphics-01/round-1/` and `round-2/` (`verdicts.md`, `builder-*.md`, `critic-*.json`; `mh/` and `pairs/` gitignored). Montage seeds `unstamped:1`, `unstamped:2` (the run was started without a `timestamp` arg).

## History
| Run | Round | atmosphere | actors | hud |
|---|---|---|---|---|
| dry-01 | 1 | LOSS (1/5 labels) | not run | not run |
| graphics-01 | 1 | **WIN** (4/5 labels) — commit `1fc1d4f` | LOSS (2/3 labels: city, cave; combat lost) | LOSS (1/3 labels: combat) |
| graphics-01 | 2 | closed | **WIN** (3/3 labels: city, combat, cave; confidence high) — commit `e85ae11` | LOSS (1/3 labels: combat; city, dungeon lost; confidence low) |

## Open pieces
- **hud** — lost rounds 1 and 2. Edits to `src/web_isometric/platformer.html`, `platformer/ui.js`, `platformer/ui-arpg.js` are left **uncommitted** (build on them in round 3). Round 2 got the room to 67% width and 12.5px feed text; the critic still wants: world at least 75% of the frame (collapse the right column — sector map, contacts, quest, feed — into an overlay or toggleable drawer; bottom bar down to HP/XP plus hotkeys on one row); 12-13px minimum high-contrast text with no grey-on-navy body text; feed capped to the last 4-5 lines with room-name traversal entries hidden; out of combat hide the target frame, telegraph strip and empty feed panel so the world is the single focal point. Combat readout (target frame, telegraph, reaction prompts, hit feed) beats the reference in both rounds — keep it.
- **actors** — won round 2; closed for this run. The critic's round-2 fixes describe the reference (A), not mh, so nothing carries forward.
- **atmosphere** — won round 1; closed for this run. Carried notes in `round-1/verdicts.md`.

## Blockers
- Builder self-check: `tests/test_suite.py --smoke` still fails at login for the pre-existing account-menu reason (server expects `play Tester`, the suite never sends it). QC rooms passes. Not a gauntlet regression.
- Round-1 records `docs/gauntlet/graphics-01/round-1/builder-{actors,hud}.md` and `critic-{actors,hud}.json` are still untracked (round 1 only committed the atmosphere win); commit them with the round-3 records or the REPORT.
- `logs/tests.log` is modified in the working tree by the builders' test runs; not committed.
- hud critic confidence is `low` both rounds; the reason text again mixes A/B across labels (city A vs dungeon B are the same game). Decoded per-label picks were taken as authoritative.

## Next command
Next command: the running Workflow (`docs/gauntlet/workflows/graphics.js`, run `graphics-01`) proceeds to round 3 with piece hud on its own. If it has stopped, resume with `Workflow({scriptPath: "docs/gauntlet/workflows/graphics.js", args: {run: "graphics-01", timestamp: "<now ISO>", pieces: ["hud"], prior: {hud: "docs/gauntlet/graphics-01/round-2/critic-hud.json"}}})` — the uncommitted hud edits are still in the working tree. After round 3 write `docs/gauntlet/graphics-01/REPORT.md` and stop for the human.
