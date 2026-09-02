# Gauntlet status

**Run:** none started yet (Phase 0 evidence pipeline and Phase 1 skill are in place).
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`). Reference shots committed under `docs/gauntlet/reference/browserquest/`.
**Smoke evidence:** `docs/gauntlet/smoke/round-0/` (Misthollow shots + blind pairs, gitignored images).

## History
| Run | Round | atmosphere | actors | hud |
|---|---|---|---|---|
| – | – | – | – | – |

## Blockers
None.

## Next command
Start the first graphics run with the Workflow tool:
`Workflow({scriptPath: "docs/gauntlet/workflows/graphics.js", args: {run: "graphics-01", timestamp: "<now ISO>"}})`
Preconditions: MUD running (`./run.sh`), reference servers up (`node tools/gauntlet/capture-ref.js --serve`) only if reference shots need re-capturing.
