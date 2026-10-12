# world-01 / round 2 — decoded verdict

## world — **LOSS** (overall B -> ref; confidence low)

| label | pick | decoded |
|---|---|---|
| walk | B | ref |
| forest | A | mh |

### Reasons (verbatim)
1. walk A: between the 0.0s frame (title 'A Winding Forest Path', character on the right of the path) and the 0.5s frame (title 'Rocky Outcropping') the entire screen is replaced by a different map with a dimmed fade-in; the character is not visible at all in the 0.5s frame and then reappears in frames 0.9s-2.3s standing still on the RIGHT side of the new room even though he was walking east, so the move reads as a teleport into a new screen, not a walk into the next area. walk B: the character advances east in every frame (0.0s left of the tree, 0.7s past the tree, 1.1s-1.8s near the right trees) with no cut, no fade, and the destination tile marker is drawn on the grass ahead before he reaches it.
2. walk A: frames 0.9s through 2.3s are effectively the same still; the character's position barely changes and nothing scrolls or reveals, so five of six frames show no travel. walk B: all six frames show the same scene with the player sprite at a new x each time, so the viewer can track the motion through one continuous space.
3. forest A: the still has a painted ground path with soft edges, dark tree-canopy silhouettes at the screen edges, drifting fog/pollen particles, a drop shadow under the player and a vignette, so it reads as a lit place with depth. forest B: flat uniform green tile fill, repeated identical tree sprites, no lighting or shadows, hard-edged dirt paths; it reads as a tile map. That depth is why forest goes to A, but a believable still does not make up for the hard cut in walk, which is the heart of the 'continuous world' question.

### Lead's note
Hero stood still after the crossing because Playwright sends one keydown with no auto-repeat and Phaser loses the key across the rebuild (capture artefact, fixed in capture.js); the 'wrong side' is the hero-anchored camera keeping the hero at its old screen position while easing. Camera ease tightened; round 3 recaptured.
