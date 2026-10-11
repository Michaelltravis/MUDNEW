# Gauntlet dry-01 — human brake report

**Run:** dry-01, a single-round dry run on branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest (local clone `.gauntlet-ref/browserquest`; reference shots under `docs/gauntlet/reference/browserquest/`).
**Pieces:** atmosphere fought; actors and hud not run.

## Per piece

### atmosphere
- **Rounds fought:** 1
- **Final result:** LOSS. Overall pick decoded to the reference; 1 of 5 labels won (dungeon). City, forest, cave and water all lost. Critic confidence: low.
- **Most repeated complaint:** the tile grid is exposed and the ground is flat. Three of the four lost labels (forest, cave, water) were called out for identical 1x1 mossy/coral/bush blocks stamped in rows with a hard one-tile border, and city/forest/cave/water were lit at one uniform brightness edge to edge. The one win (dungeon) is precisely the screen where torch pools, fountain glow and an edge vignette actually appear. A secondary, every-label complaint: the opaque room-description panel (`immersion.js`) covers the top third of each shot and hides exits.
- **Commits made:** none for the piece. The builder's edits to `src/web_isometric/platformer/painter.js` and `src/web_isometric/platformer/themes-zones.js` are still **uncommitted** in the working tree. `immersion.js` was not touched.

### actors, hud
Not run this dry run. No rounds, no commits.

## Commits on the branch (`git log --oneline -12`)
```
a6013e4 gauntlet(dry-01): round 1 records
6c40a53 Gauntlet loop: evidence pipeline, skill, and graphics workflow
```
The remaining ten commits (5168a8c through 9c0488d) predate the gauntlet: mob variety, environmental gameplay, Graphics Phases 1-3, rhythm combat. No piece work has been committed.

## Open blocker worth reading before deciding
The builder reports that seamless ring masses, baked vignettes and torch pools were verified in headless captures, yet the critic saw flat fills and stamped blocks in the same mh shots. Either the capture pipeline is not loading the modified painter (cached/fallback tile path) or the builder over-reported. Confirm which before spending another round on the same fixes.

## Options

1. **Continue with the same reference (BrowserQuest).** Start a real multi-round run, e.g. `graphics-01`, keeping the uncommitted painter/themes edits as the round-2 starting point. First step of round 2 should be verifying the capture path exercises the new painter, then addressing the description panel in `immersion.js`.
2. **Change the reference.** BrowserQuest's hand-painted tilesets set a high bar on "terrain vs grid"; a reference closer to Misthollow's procedural style would give more diagnostic verdicts. Rebuild with `node tools/gauntlet/capture-ref.js --setup` against the new target and re-capture reference shots.
3. **Stop.** Revert the uncommitted `painter.js` / `themes-zones.js` edits (or commit them as WIP on a side branch), leave the dry-01 records as-is, and close the loop.
