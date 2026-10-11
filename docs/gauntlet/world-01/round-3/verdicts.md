# world-01 / round 3 — decoded verdict (budget exhausted)

## world — **LOSS** (overall B -> ref; confidence medium)

| label | pick | decoded |
|---|---|---|
| walk | B | ref |
| forest | A | mh |

### Reasons (verbatim)
1. walk A 0.0s->0.5s is a hard cut: the title swaps from 'A Winding Forest Path' to 'Rocky Outcropping', the whole screen goes dim/dark for the 0.5s frame, and the character jumps from screen-centre to a new spot in a different layout. walk B 0.0s->1.8s has no cut at all: the village, road and trees stay put and the character simply advances east from the road edge to the grass.
2. walk A 0.9s->1.4s->2.3s is a visible teleport: the tree clumps are pixel-identical in all three frames (static camera, same room) yet the character is at the right edge at 0.9s, reappears at the left-centre at 1.4s, then walks back to the right edge by 2.3s. Nothing scrolls or reveals; the destination is never visible before arrival. walk B keeps a single consistent position track with the next area (grass, tree line) already on screen before the character reaches it.
3. forest A has real depth cues that B lacks: fog/vignette darkening at the edges, soft drop-shadows under every tree clump, a lit pool on the path around the player, and foliage overlapping the path. forest B is a flat, evenly lit tile grid with no shadows or falloff, so on the still alone A reads as a place and B as a map.

### Fixes (verbatim)
1. Remove the hard cut on room change: keep the camera following the player and scroll/pan the new room into view instead of dimming to a fresh static screen (walk 0.0s->0.5s). (`src/web_isometric/platformer/scene-topdown.js`)
2. Fix the same-room teleport (walk 0.9s->1.4s): when the player crosses the east edge, either spawn them at the matching west edge of the NEXT room with a continuous camera move, or scroll the camera so they never snap back across an unchanged backdrop. (`src/web_isometric/platformer/world-peek.js`)
3. Show the destination before arrival: render the neighbouring room's terrain/path past the current room's edge (a peek strip) so the path visibly continues east rather than ending in a fog wall. (`src/web_isometric/platformer/world-peek.js`)

### Lead's conclusion
Forest (depth, lighting) won all three rounds; walk lost all three. The residual tell is the room rebuild itself: the HUD title swaps and the scene is reconstructed, which a single-map game never does. Camera pan, painted neighbours, hero anchoring and key repeat removed the placeholder, the black band and the invisible hero, but not the cut. Closing the round per budget (3). The fix is architectural: render a whole zone as one stitched tilemap from /atlas with the server's room graph driving only movement/presence (see STATUS.md, Phase B next).
