# world-03 / round 4 — decoded verdict (critic only)

Reference: BrowserQuest walk. Seed 7304. Key: A = ref, B = mh. Critic confidence: medium.

## world — **LOSS** (walk B → mh lost; forest B → mh won)

### Reasons (verbatim)
1. walk: A holds identical framing and scale across all six frames (0.0s-2.3s). The town square, well, houses and the tree at bottom-right stay put with no flashes or blank regions, and the destination (house, trees, cave edge on the right) is visible the whole time. Weakness: the walk is short, and the character barely crosses the screen, so it shows little real traversal.
2. walk: B has visible rectangular seams. At 0.0s there is a hard vertical brightness edge near the character, at 3.0s a lighter slab on the left, and at 3.7s and 4.4s another vertical boundary that looks like a stale overlay or unblended chunk. The path layout also shifts between 0.0s and 2.1s and again at 6.4s. Creatures (fox, rabbit, grey) appear and disappear between frames, and a tree sprite pops in at the top at 6.4s. The reading is chunks being swapped, not a world sliding under a fixed camera.
3. forest: B reads as a lit place. It has a vignette, dark canopy masses at top and bottom, a soft glow on the path and a warm-to-cool gradient, so it has depth. A is a flat, uniformly lit, saturated green tile plane with no light or atmosphere.
4. forest: A's trees are crisp, with readable silhouettes, trunks and cast shadows. B's trees are blurry dark blobs, and the bottom canopy is mush with no individual trees. B's path is a readable painted dirt crossroads with texture, while A's path is crisp but flat and tile-like.
5. Overall: the piece is continuity of place. B is more atmospheric and modern in a still, but its walk is the one that fails (seams, pop-in, layout changes), so A is closer on the stated goal. B would win if the seams were fixed.

### Fixes (verbatim)
1. Remove the visible rectangular seams or brightness steps between world chunks, such as the vertical edges at 0.0s, 3.0s and 3.7s. Blend the lighting and tint pass across chunk boundaries, and draw it as one full-viewport pass in world space rather than per-tile or per-chunk.
2. Stop the layout and creature pop-in during the walk. Pre-render the adjacent area and keep the camera scale fixed, so the world scrolls continuously with creatures and trees spawning off-screen.
3. Sharpen the tree rendering in the forest. Use crisp canopy sprites with a rim light and a hard-edged shadow instead of blurred dark blobs, and reduce the heavy blur or darkness at the bottom edge so individual trees read.
4. Keep B's lighting and depth, which beat A's flat scene, but pair it with clearer silhouettes. Add contrast between the path and the surrounding grass, and add path edge detail.

### Lead's reading
The critic's seams were real and measurable: a luminance probe read 70 vs 82 across the room border
with every overlay hidden — the two paintings differ because the rooms are different SECTORS (field
beside forest). Fixed by cross-fading the two floor colours over four tiles at every shared edge
(probe after: 85.5 vs 85); outdoor rooms also stopped carrying their own vignette (one screen-space
pass instead) and the grade/tint/flash/mood plates now cover the whole drawn world.
