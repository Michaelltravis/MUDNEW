# world-01 / round 1 — decoded verdict (no builder; the continuous-world steps as shipped)

Reference: BrowserQuest walking east from spawn. Critic confidence: medium

## world — **LOSS** (overall A -> ref)

| label | pick | decoded |
|---|---|---|
| walk | A | ref |
| forest | B | mh |

### Reasons (verbatim)
1. walk B frame 0.5s is a hard cut: the frame goes dim/washed-out with only a floating 'Eastern Trail' label in the middle and no character, then 0.9s pops into a different room titled 'Rocky Outcropping' with the character absent until 1.4s. walk A frames 0.0s-1.8s keep one continuous scene with the same buildings, trees and path while the character walks from the house toward the east road, so the destination is visible before the character reaches it.
2. walk B frames 1.4s, 1.8s, 2.3s show a flat dark-grey/black vertical band covering roughly the right fifth of the viewport (a blank or unpainted area at the room edge), plus a stale '-6' damage number hanging beside the player across the cut; walk A has no blank regions in any frame and the frame edges are all painted terrain.
3. forest B has real depth: a vignetted canopy with blurred dark tree masses over the ground, a soft ground light gradient, a glowing ring under the player and a lit crossroads path; forest A is a flat, uniform green tile plane with hard-edged trees and no lighting at all, reading as a tile map rather than a place.

### Fixes (verbatim)
1. Remove the dim placeholder frame on room change: stop fading to a near-black screen with a lone exit label ('Eastern Trail'); instead keep the current room painted and slide/scroll the camera into the next room, or at minimum cross-fade with the new room already rendered and the player sprite present in the first frame. (`src/web_isometric/platformer/scene-topdown.js`)
2. Never leave an unpainted band at the viewport edge (the dark strip on the right in frames 1.4s-2.3s): paint the neighbouring room's terrain (or at least canopy/ground fill) past the room boundary so the edge the player is heading to reads as more world, not void. (`src/web_isometric/platformer/world-peek.js`)
3. Make the destination visible before arrival: show the adjacent room's path and tree silhouettes beyond the exit so the walk east is a reveal rather than a cut, and clear stale floating damage numbers when the room changes. (`src/web_isometric/platformer/painter.js`)

### Lead's note
Forest (the painted world) won; walk lost on the crossing frame: a dimmed, labelled neighbour with no hero, then a black band where the room has no east exit. Fixed after the round: hero-anchored camera across the rebuild, lighter haze, no placeholder labels, camera bounds follow exits. Round 2 recaptured for a re-judge.
