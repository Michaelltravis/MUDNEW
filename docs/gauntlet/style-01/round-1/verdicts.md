# style-01 / round 1 — decoded verdict (no builder; judging the Lucifer art as shipped)

Reference: BrowserQuest. One A/B order for the whole round. Critic confidence: medium

## style — **WIN** (overall B -> mh; 6/7 labels -> mh)

| label | pick | decoded |
|---|---|---|
| city | A | ref |
| forest | B | mh |
| dungeon | B | mh |
| cave | B | mh |
| water | B | mh |
| combat | B | mh |
| fight | B | mh |

### Reasons (verbatim)
1. Lighting and mood: B has per-biome light falloff and depth in forest (canopy shadow and vignette over the path), dungeon (cold fog with a bright pool under the hero), cave (near-black edges with a purple glow) and water (dark reef masses sinking into the blue). A is the same flat, evenly lit tile sheet in every label; the cave in A is a flat black void and the water is a single flat blue sheet.
2. Combat readability: in combat and fight, B shows a named enemy frame with HP, an 'INCOMING CRUSHING BLOW 0.3s' timer, a red telegraph ring on the floor, a '! CRUSHING BLOW' banner, a red screen flash at 1.0s/4.0s, floating -4/-14 numbers and a final 'STAGGERED!' result, all without reading prose. A's fight storyboard is 8 nearly identical frames of a tiny hero next to a rat with only a small '6' and a 'You killed a rat' bar text.
3. Where A wins (city): A's houses, trees, cobble and UI are one consistent pixel style and the blonde sword hero and NPCs read at a glance; B's city is a smeared, upscaled cobble texture, the hero is a dark grey smudge with no face, the two NPCs are unreadable silhouettes, and the dungeon gravestones are flat cubes with smiley faces that break the painted look. B wins on atmosphere and combat, not on character or prop craft.

### Fixes (verbatim; addressed to the losing side = reference)
1. Add a lighting pass: ambient tint per biome plus radial light falloff around the hero, torches and lamps, and a dark vignette at screen edges; the cave should be lit by a point light, not a flat black fill. (`src/web_isometric/platformer/painter.js`)
2. Give each biome a distinct palette and ground treatment (cold blue-grey dungeon fog, deep teal water with drifting highlights, dappled forest shadow) instead of the one saturated green grass and flat blue water everywhere. (`src/web_isometric/platformer/themes-zones.js`)
3. Add on-screen combat feedback: an enemy frame with HP and name, a floor telegraph ring plus wind-up timer before a big hit, a screen flash on damage taken, large floating damage numbers and an outcome banner (stagger/kill) so the fight reads without the log text. (`src/web_isometric/platformer/ui.js`)

### Lead's note
The critic's observed weaknesses of OUR side (city label): hero reads as a faceless dark silhouette at this zoom, townsfolk silhouettes unreadable, cobble ground reads blurred, dungeon obstacle 'skull blocks' clash with the painted fog. These are the next art targets (lucifer.js contour/brightness, lucifer-tiles.js obstacles).
