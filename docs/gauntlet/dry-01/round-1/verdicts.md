# dry-01 / round 1 — decoded verdicts

Key: `pairs/key.json` (seed `2026-09-02T23:05:00Z:1`, reference BrowserQuest). A pick decodes to
`mh` = Misthollow (win) or `ref` = reference (loss).

## atmosphere — **LOSS** (overall pick A; 1 of 5 labels decoded to mh)

| label | pick | decoded |
|---|---|---|
| city | A | ref (loss) |
| forest | B | ref (loss) |
| dungeon | A | mh (win) |
| cave | A | ref (loss) |
| water | A | ref (loss) |

Critic confidence: low.

### Reasons (verbatim)
1. Sense of place: city-A is unmistakably a village (timbered houses, tree clumps, a dirt road, a cobbled ramp) while city-B is a flat brown rectangle whose only cue is a paragraph of text; forest-B has real tree canopies and winding dirt paths while forest-A is a uniform green field ringed by identical square bush blocks; water-A shows beach, surf line, dock and sea while water-B is a blue box with a lattice border you can only identify by its title.
2. Light falloff: dungeon-A is the one screen that actually does it - torches at the top wall pool orange, the fountain glows blue on the flagstones and the edges vignette to black - which is why it wins that label; cave-B and water-B only manage a soft radial haze around the player and a purple smudge, and city-B / forest-A are lit at one flat brightness edge to edge.
3. Terrain vs grid: forest-A, cave-B and water-B all expose the tile grid - identical 1x1 mossy/coral blocks stamped in rows and a hard one-tile border around the whole room - whereas forest-B, cave-A and water-A read as painted ground with organic rock rims, path edges and shoreline; the same UI-heavy game also drops an opaque room-description panel over the top third of the map in every label, hiding exits and killing readability.

### Fixes (verbatim)
1. Give each biome a distinct floor treatment instead of one flat fill: painted path/grass/sand/stone variation with soft edge blending, and replace the repeated 1x1 bush/coral/wall blocks with contiguous wall runs that have an outline and a shadow side so the grid disappears (forest, cave, water). — `src/web_isometric/platformer/painter.js`
2. Extend the dungeon torch/fountain falloff to every zone: per-biome ambient tint plus point lights with radial falloff on torches, lanterns, water glow and the player, and a fog/vignette toward room edges so brightness is not uniform (city, forest, cave, water are flat). — `src/web_isometric/platformer/themes-zones.js`
3. Stop covering the map with the opaque room-description panel: fade it out after a few seconds or move it below the viewport, and make exits (stairs, gaps, doors) and NPCs draw with a bright rim so they stand out from the floor. — `src/web_isometric/platformer/immersion.js`

Note: the builder reported that the painter runs and the new textures load in headless captures, yet the critic saw flat fills and 1x1 stamped blocks in the mh shots (city-B, forest-A, cave-B, water-B). Round 2 should first confirm the captured shots actually exercised the new painter path before iterating on the fixes.
