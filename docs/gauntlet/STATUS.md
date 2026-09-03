# Gauntlet status

**Run:** graphics-01 — **complete** (round 3 of 3 done). Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Round records:** `docs/gauntlet/graphics-01/round-1/`, `round-2/`, `round-3/` (`verdicts.md`, `builder-*.md`, `critic-*.json`; `mh/` and `pairs/` gitignored). Montage seeds `2026-09-02T23:35:00Z:1` / `:2` / `:3` (keys in `round-<n>/pairs/key.json`, gitignored).

Note: this is a restart of graphics-01 with a stamped seed. The branch already carries an earlier graphics-01 pass (`1fc1d4f` atmosphere R1, `e85ae11` actors R2, `eafdbd8` records); the restart's rounds are what count.

## History
| Run | Round | atmosphere | actors | hud |
|---|---|---|---|---|
| dry-01 | 1 | LOSS (1/5 labels) | not run | not run |
| graphics-01 (earlier pass) | 1 | WIN (4/5) `1fc1d4f` | LOSS (2/3) | LOSS (1/3) |
| graphics-01 (earlier pass) | 2 | closed | WIN (3/3) `e85ae11` | LOSS (1/3) |
| graphics-01 (restart) | 1 | WIN (5/5; confidence low) `fead991` | WIN (3/3; confidence high) `d73fac7` | LOSS (1/3: combat won; city, dungeon lost; confidence low) |
| graphics-01 (restart) | 2 | closed | closed | LOSS (1/3: combat won; city, dungeon lost; confidence low) — records committed, code left uncommitted |
| **graphics-01 (restart)** | **3** | closed | closed | **WIN** (overall pick A -> mh; per-label 1/3: combat mh, city/dungeon ref; confidence low) `4a29fb8` |

## Open pieces
None. All three pieces (atmosphere, actors, hud) have won a round in this run.

- **hud** — won round 3 on the overall pick; committed `4a29fb8` with the accumulated round 1-3 edits to `src/web_isometric/platformer.html`, `platformer/ui.js`, `platformer/ui-arpg.js`. City and dungeon per-label picks still went to the reference (chrome count, text size); combat wins every round on the target frame, telegraph prompts and colour-coded feed.
- **atmosphere** — won round 1; closed.
- **actors** — won round 1; closed.

## Blockers
- hud's round-3 win is on the overall pick only; per-label it is 1/3, the same as rounds 1 and 2, and the critic's confidence is `low` for the third round running. Its three "fixes" describe features A already has (see `round-3/verdicts.md` note). A human should decide whether the hud bar is genuinely met or whether the win is a rubric artefact before starting a follow-on run.
- `docs/gauntlet/graphics-01/round-1/builder-hud.md` and `critic-hud.json` are still modified and uncommitted (not in the round-3 file list); commit them with the REPORT.
- `logs/tests.log` is modified in the working tree by the builders' test runs; not committed.
- Builder self-check: `tests/test_suite.py --smoke` still fails at telnet login for the pre-existing account-menu reason (server expects `play Tester`). Not a gauntlet regression.

## Next command
Next command: human decision: run complete
