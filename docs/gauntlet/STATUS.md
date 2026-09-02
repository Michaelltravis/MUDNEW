# Gauntlet status

**Run:** dry-01 (round 1 of 1 — dry run, single round). Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Round record:** `docs/gauntlet/dry-01/round-1/` (`verdicts.md`, `builder-atmosphere.md`, `critic-atmosphere.json`; `mh/` and `pairs/` gitignored).

## History
| Run | Round | atmosphere | actors | hud |
|---|---|---|---|---|
| dry-01 | 1 | LOSS (1/5 labels: dungeon won; city, forest, cave, water lost; critic confidence low) | not run | not run |

## Open pieces
- **atmosphere** — lost round 1. Its edits to `src/web_isometric/platformer/painter.js` and `src/web_isometric/platformer/themes-zones.js` are left **uncommitted** in the working tree (rework next round or revert at the end). `immersion.js` untouched.

## Blockers
- Builder/critic mismatch: the builder claims seamless ring masses, baked vignettes and torch pools were verified in headless captures, but the critic still saw flat fills, 1x1 stamped blocks and uniform brightness in the mh shots. Confirm the capture pipeline is loading the modified painter (not a cached/fallback tile path) before spending another round on the same fixes.
- Critic flagged the opaque room-description panel covering the top third of every mh shot (`immersion.js`) — not addressed this round.

## Next command
human decision: run complete (dry-01 was a single-round dry run; atmosphere lost and its files remain uncommitted — decide whether to revert them or start a real run, e.g. `Workflow({scriptPath: "docs/gauntlet/workflows/graphics.js", args: {run: "graphics-01", timestamp: "<now ISO>"}})`).
