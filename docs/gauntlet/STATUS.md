# Gauntlet status

**Run:** graphics-01 (round 2 of 3 complete; one round left). Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Round records:** `docs/gauntlet/graphics-01/round-1/` and `round-2/` (`verdicts.md`, `builder-*.md`, `critic-*.json`; `mh/` and `pairs/` gitignored). Montage seeds `2026-09-02T23:35:00Z:1` / `:2` (keys in `round-<n>/pairs/key.json`, gitignored).

Note: this is a restart of graphics-01 with a stamped seed. The branch already carries an earlier graphics-01 pass (`1fc1d4f` atmosphere R1, `e85ae11` actors R2, `eafdbd8` records); the restart's rounds are what count.

## History
| Run | Round | atmosphere | actors | hud |
|---|---|---|---|---|
| dry-01 | 1 | LOSS (1/5 labels) | not run | not run |
| graphics-01 (earlier pass) | 1 | WIN (4/5) `1fc1d4f` | LOSS (2/3) | LOSS (1/3) |
| graphics-01 (earlier pass) | 2 | closed | WIN (3/3) `e85ae11` | LOSS (1/3) |
| graphics-01 (restart) | 1 | WIN (5/5; confidence low) `fead991` | WIN (3/3; confidence high) `d73fac7` | LOSS (1/3: combat won; city, dungeon lost; confidence low) |
| **graphics-01 (restart)** | **2** | closed | closed | **LOSS** (1/3: combat won; city, dungeon lost; confidence low) — records committed, code left uncommitted |

## Open pieces
- **hud** — lost rounds 1 and 2; one round left. Edits to `src/web_isometric/platformer.html`, `platformer/ui.js`, `platformer/ui-arpg.js` remain **uncommitted** (build on them in round 3). Round 2 removed the right column (Tab drawer), got the room to 1056x660 of 1280x720 (82% width) with a 48px dock and a 3-line bottom ticker; combat (target frame, damage numbers, pill feed) beats the reference again. The critic still sees, in city/dungeon: black letterbox margins either side of the world (fix: scale the canvas to fill the viewport width), a two-row bottom strip of ~13 tiny action buttons plus three bars (fix: one compact HP/MP/MV cluster at >=12px, action buttons behind hotkeys or one expandable bar), and four competing top/corner chrome elements (room banner, clock/date pill, compass, PANELS/Tab button) (fix: fold the clock pill and PANELS button into the banner or fade them). Keep the target frame and pill feed.
- **atmosphere** — won round 1; closed for this run.
- **actors** — won round 1; closed for this run.

## Blockers
- hud critic confidence is `low` for the second round; its overall pick B maps to ref on city/dungeon and mh on combat (the critic flagged the ambiguity itself). Decoded per-label picks were taken as authoritative: loss.
- Builder self-check: `tests/test_suite.py --smoke` still fails at telnet login for the pre-existing account-menu reason (server expects `play Tester`). Not a gauntlet regression.
- Round-1 `docs/gauntlet/graphics-01/round-1/builder-hud.md` and `critic-hud.json` are modified but uncommitted; commit them with the round that closes hud or with the REPORT.
- `logs/tests.log` is modified in the working tree by the builders' test runs; not committed.
- If hud loses round 3 the run ends with hud open; the human decides whether to commit or drop the uncommitted hud edits.

## Next command
Next command: the running Workflow (`docs/gauntlet/workflows/graphics.js`, run `graphics-01`) proceeds to round 3 with piece hud on its own. If it has stopped, resume with `Workflow({scriptPath: "docs/gauntlet/workflows/graphics.js", args: {run: "graphics-01", timestamp: "2026-09-02T23:35:00Z", pieces: ["hud"], prior: {hud: "docs/gauntlet/graphics-01/round-2/critic-hud.json"}}})` — the uncommitted hud edits are still in the working tree.
