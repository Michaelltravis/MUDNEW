# world-03 / round 2 — decoded verdict (critic only)

Reference: BrowserQuest walking east from spawn (re-filmed with real-time stamps). Critic confidence: low. Seed 7302.

## world — **WIN** (overall B -> mh; walk B -> mh, forest B -> mh)

| label | pick | decoded |
|---|---|---|
| walk | B | mh |
| forest | B | mh |

### Reasons (verbatim)
1. walk: B's camera stays fixed on the character while the world slides under it. The path junction drifts from the upper-right at 1.1s to the centre by 2.9s, so it reads as one continuous forest. The path bending north is visible well before the character reaches it. A barely changes across 0.0s to 2.3s. The town layout looks the same in every frame and the character moves a few pixels, so there is no sense of traversal and no destination ever appears.
2. walk: B has visible tile or lighting seams. At 1.7s there is a rectangular lighter block at the upper right. At 4.1s there is a hard vertical edge at the right, around x=1895, where the shading changes. These read as unpainted or stale regions. A has no flashes or blank regions, but it also shows nothing happening.
3. forest: B reads as a lit place with depth. It has a dark vignette, a soft glow around the path, a canopy overhang at the top, and shadowed foreground bushes at the bottom. The path is a wide painted dirt road with soft edges, and its fork and bend are easy to follow. A is bright, flat, saturated green tile with a hard-edged brown strip. It has no lighting or depth falloff and looks like a 2000s tileset.
4. forest: A wins on tree crispness. Its trees have clean outlines, readable trunks and drop shadows. B's trees are blurry dark blobs, smeared and low-contrast, and individual trunks and silhouettes are not readable. B's overall mood is more modern, but its tree rendering is muddy.
5. overall: B is closer to a modern polished game in atmosphere, continuity and path readability. It is held back by blurry trees and visible rectangular seams.

### Fixes (verbatim)
1. Remove the rectangular lighter blocks and hard vertical edges in the forest ground and lighting layer (seen at 1.7s upper right and 4.1s right edge). Blend chunk boundaries or paint the lighting as one continuous overlay.
2. Sharpen the tree canopies with crisp edges and a light/shadow split per tree. Add visible trunks, and stop the blur or smear filter from softening the silhouettes.
3. Reduce the heavy dark vignette and the overall murk. Raise mid-tone contrast between path, grass and canopy so the path and trees pop at gameplay scale.
4. Keep the camera locked while the world scrolls, and pre-render the next area ahead of the character so the destination is always on screen. Keep the transition seamless.

### What changed between round 1 and round 2 (lead)
- **The real cause of seven walk losses was a client bug, not the renderer.** The "wedged" exit
  breaker in `scene-topdown.js` measured only how long a direction key had been held, never
  whether the hero was stuck: holding a key for 1.5 s fired the exit and teleported you a room
  ahead. Every storyboard therefore filmed one or two forced jumps. It now requires no movement
  since the key was pressed.
- The capture tool was also lying: a WebGL screenshot under xvfb takes 3–4 s, so a "2.7 s"
  storyboard filmed ~20 s of play (two crossings and a wolf fight) against a 2.3 s reference.
  World storyboards are now read back in-page from the renderer at true game-time intervals
  (`filmstrip.canvasOnly`, no HUD in those frames); fight storyboards freeze the game loop while
  each frame is read and stamp game time. The reference walk was re-filmed with real stamps.
- Same-zone cardinal crossings no longer swap the room-title card at the seam (quiet settle 1.1 s
  later); a parked "last hit" number is cleared on room change.
- Caveats, stated plainly: confidence is low; the reference storyboard covers ~2.3 s of play and
  ours ~4.1 s, which the critic read against the reference ("barely changes"). The two seams the
  critic found are real: the un-painted flat fill of a not-yet-painted neighbour (upper right at
  1.7 s) and the haze step at the outer ring (right edge at 4.1 s).

### Next (if another round is wanted)
- Paint neighbours before they can be on screen (paint the two rooms ahead first, flat fill only
  beyond that) and feather the outer-ring haze instead of a hard step.
- Canopy crispness again: trunks + a hard light/shadow split per crown.
- Lift the painter's vignette/murk one notch for forest.
