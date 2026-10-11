# world-03 / round 1 — decoded verdict (critic only, after stitched-zone steps 3+4)

Reference: BrowserQuest walking east from spawn. Critic confidence: medium. Seed 7301.

## world — **LOSS** (overall A -> ref)

| label | pick | decoded |
|---|---|---|
| walk | A | ref |
| forest | B | mh |

### Reasons (verbatim)
1. walk: A holds identical framing and scale across all six frames (0.0s-1.8s): house, trees, rocks and path stay locked while the character moves east, with no cut, flash or overlay. B changes layout between 0.0s (Winding Forest Path, wide path) and 0.5s (Rocky Outcropping, different trees and path), which is a cut with a title card swap. Neither side shows a clear destination before arrival, but A at least never swaps the world.
2. walk: B has combat HUD, enemy plates, damage numbers and a STAGGERED banner stacked over the scene from 1.4s-2.3s, and the dark vignette plus haze hides the terrain, so the walk stops reading as traversal. A shows only a clean bottom bar and no stale overlays.
3. forest: B reads as a lit place with depth. It has a soft light pool, a canopy vignette, particles and a path with edge shading that you can follow from the centre to the lower right. Its trees are dark blobs with weak silhouettes, though. A has crisp trees, but the ground is a flat saturated green tile plane with no lighting, and the thin brown paths at the left and right edges are hard to follow as terrain.

### Fixes (verbatim)
1. walk (B): keep one continuous scrolling world across area boundaries with locked camera framing and scale. Render the next area's trees, path and creatures beyond the edge before the character reaches it, and use no layout swap at the transition.
2. walk (B): drop the combat HUD, target plates, damage numbers and banners from the traversal. Lighten the vignette and haze so the terrain stays readable while moving.
3. forest (A): add lighting and depth with a canopy vignette, light pools, tinted ground variation and drifting particles. Widen and shade the path with edges so it reads as painted terrain you can follow.

### Lead's reading
The red wash, the pop-in and the blank band are gone (none cited). What the critic now reads as the
"cut" is (a) the camera racing to re-centre within one storyboard interval, so 0.0s and 0.5s share
little screen space, and (b) the room-title card swapping at the seam. The combat overlays are the
walk route itself: the room east of 27001 holds dire wolves that aggro on entry, so the storyboard
always films an ambush. Round 2 targets exactly those three: slow camera pan, no title card on a
same-zone crossing, and a traversal route that is not an ambush.
