# world-02 / round 2 — decoded verdict (world runs closed)

## world — **LOSS** (overall A -> ref; confidence medium)

| label | pick | decoded |
|---|---|---|
| walk | A | ref |
| forest | B | mh |

### Reasons (verbatim)
1. walk A frames 0.0s-1.8s: the same village, path and tree cluster stay put while the character (with name label) visibly crosses from the house to the east sand path; the tree it ends beside at 1.8s is on screen from 0.0s, so the walk reads as traversal of one persistent space. walk B: the framing changes between 0.0s (wide, dim, 'A Winding Forest Path' header) and 0.5s (closer, different tree layout), then by 0.9s the header reads 'Rocky Outcropping' with an entirely different tree arrangement - a hard cut to a new area, nothing of the next place was visible before arrival.
2. walk B 1.4s: the whole viewport turns red with a full-screen combat flash and a dark bar across the middle - a visual discontinuity that breaks the sense of place for a frame; A has no cut, flash or placeholder across all six frames, just the same map with the character in a new spot.
3. forest B has what A lacks as a place: a curving dirt path with soft edges, dark canopy blobs around a vignetted edge, fog, light falloff and a shadow ring under the character, so it reads as a lit clearing with depth; forest A is a bright flat tile map with identical trees and a hard-edged path, no lighting at all - but B's trees are blurry low-contrast blobs and A's are at least crisp and readable.

### Fixes (verbatim)
1. Kill the hard cut between rooms: when the character reaches an exit, keep the current room on screen and scroll/pan the camera into the neighbor instead of swapping to a new tree layout and a new header. The walk should look like B 0.0s -> B 0.5s does NOT: same framing, same scale, world sliding under a centered character. (`src/web_isometric/platformer/scene-topdown.js`)
2. Show the destination before you get there: render the adjacent room's strip (path continuation, its trees) at the edge the player is walking toward so the 'Rocky Outcropping' is visible at 0.5s, not revealed at 0.9s. Adjacent rooms must share edge geometry so the path lines up across the seam. (`src/web_isometric/platformer/world-peek.js`)
3. Raise readability of the forest so it stays a place at walking speed: sharpen tree silhouettes and lift path/grass contrast (B's canopies are mush at storyboard scale, A's trees are instantly readable), and drop the full-screen red combat wash to a small edge flash so the world does not vanish when a wolf shows up. (`src/web_isometric/platformer/painter.js`)

### Lead's conclusion (six rounds across world-01 and world-02)
Forest won 6/6 on depth and lighting; walk lost 6/6. Every nameable defect was removed; what remains is that our storyboard crosses a room seam (two genuinely different places) while the reference walks inside one map screen, and the scene swap at the seam is inherent to a per-room renderer. Two useful new notes from this round: the full-screen red ambush wash reads as a discontinuity (consider an edge flash), and painted canopies are mush at storyboard scale (sharpen silhouettes). The architectural fix is the stitched-zone renderer in STATUS.md; the world runs are closed.
