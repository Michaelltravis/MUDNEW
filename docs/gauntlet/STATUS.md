# Gauntlet status

**Run:** graphics-02 — **round 2 of 3 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Pieces:** hud only (labels: city, dungeon). Win rule: majority (overall pick -> mh AND >1/2 labels -> mh).
**Round records:** `docs/gauntlet/graphics-02/round-1/` (records `abca337`, status `f8277de`) and `docs/gauntlet/graphics-02/round-2/` (`verdicts.md`, `builder-hud.md`, `critic-hud.json`; `mh/` and `pairs/` gitignored). Round-2 montage seed `2026-09-03T14:25:00Z:2`. Round-2 code + records committed `d648ea1`.
Previous run graphics-01 is complete (see `docs/gauntlet/graphics-01/`); its hud win was on the overall pick only (1/3 labels, confidence low), which is why graphics-02 re-opened hud under the majority rule.

## History
| Run | Round | hud |
|---|---|---|
| graphics-01 (restart) | 1-3 | WIN in r3 on overall pick only (1/3 labels, confidence low) `4a29fb8` |
| graphics-02 | 1 | LOSS (0/2: city ref, dungeon ref; overall A -> ref; confidence high) — records `abca337`, code left uncommitted |
| **graphics-02** | **2** | **WIN** (2/2: city A -> mh, dungeon B -> mh; overall B -> mh; confidence low) — code + records `d648ea1` |

## Open pieces
- None. hud won round 2 under the majority rule; all pieces in this run have won.

## Blockers / notes for the human brake
- **Overall-pick decode ambiguity.** The round-2 key differs per label (city A=mh, dungeon B=mh), so the critic's single overall letter `B` maps to ref on city and mh on dungeon. The critic's reasons name "city A / dungeon B" as the preferred set (mh on both), and the per-label picks are 2/2 mh, so the clerk decoded overall as mh and ruled WIN. Critic confidence is `low`. If the human wants a strict reading (overall letter must decode identically on every label), this should be treated as a loss and round 3 run; see `round-2/verdicts.md` decode note.
- Critic's three fixes are all aimed at the reference side, so none apply to Misthollow. The one live criticism of our HUD (reason 3): MP/MV sub-bars, the `Lv 30 Warrior ... gold` line and hotbar skill names still read as ~8px grey in the montage despite the builder's 12px floor — same builder/critic size mismatch as round 1. Worth a manual look at `tools/gauntlet/capture.js` output at montage scale before any future hud round.
- `logs/tests.log` is modified in the working tree by builder test runs; not committed.
- Builder self-check: `tests/test_suite.py --smoke` still fails at telnet login (pre-existing account-menu reason, server expects `play Tester`). Not a gauntlet regression.

Next command: human decision: run complete
