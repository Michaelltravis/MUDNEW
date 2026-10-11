# world-01 / round 5 — decoded verdict (round 4 unjudged; budget exceeded, closing the run)

## world — **LOSS** (overall B -> ref; confidence medium)

| label | pick | decoded |
|---|---|---|
| walk | B | ref |
| forest | A | mh |

### Reasons (verbatim)
1. walk A, frame 0.0s to 0.5s: the title changes from 'A Winding Forest Path' to 'Rocky Outcropping' and the entire scene is replaced in one hard cut (different path shape, different tree layout, character teleported from mid-screen to the right edge); walk B keeps one scene across all six frames (0.0s-1.8s) and the character simply walks east across it from the village edge toward the trees, with the destination grass and trees visible from frame 0.0s.
2. walk A, frame 0.5s: the top of the screen shows a block of hard-edged black rectangles where frame 0.9s later shows round tree canopies, i.e. a placeholder/unfinished area is visible during the transition, and the tree layout differs again between 0.5s and 0.9s; walk B has no blank, placeholder or re-laid-out area in any frame.
3. walk A, frames 0.9s-2.3s: the character is pinned near the right edge of the frame and the surroundings do not scroll, so the eastward walk never reveals new world; forest A, by contrast, has real depth cues B lacks (canopy shadow over the path, light pooling at the crossroads, rain streaks, soft tree-mass shading) where forest B is a flat, evenly lit tile map with no shadow under any tree.

### Fixes (verbatim)
1. Remove the hard cut between rooms: when the player reaches an edge, keep the current room drawn and slide/scroll the camera into the next room (or cross-fade with both rooms rendered) instead of swapping the whole scene and relocating the sprite. (`scene-topdown.js`)
2. Pre-render the neighbouring room before the crossing so the destination is visible past the edge and no black rectangle/placeholder canopy block appears mid-transition (walk A frame 0.5s). (`world-peek.js`)
3. Make the camera follow the character continuously with the world scrolling under it, rather than parking the sprite at the screen edge while the background stays fixed (walk A frames 0.9s-2.3s). (`scene-topdown.js`)

### Lead's conclusion
Five rounds, five walk losses, forest won five times. Everything the critic could name was fixed (labels, void, hero, hop, dimming, content popping) and the verdict did not move: the remaining tell is the rebuild itself (title swap, re-laid-out scene) plus the camera clamping at an exit-less edge. The black rectangles at frame 0.5s were Graphics objects drawn into the snapshot; excluded after this round. The run is closed; the stitched-zone renderer in STATUS.md is the fix.
