# world-03 / round 3 — decoded verdict (critic only)

Reference: BrowserQuest walk. Seed 7303. Key: A = ref, B = mh. Critic confidence: low.

## world — **LOSS** (walk B → mh lost; forest B → mh won)

### Reasons (verbatim)
1. Walk: A holds identical framing and scale across all six frames (0.0s to 2.3s) with the plaza, well, house and bushes in fixed relation, so it reads as one space. B cuts between 0.0s and 2.4s. The 0.0s frame is a dense, zoomed forest with a different camera and layout, and 2.4s onward is a different clearing, so the world visibly swaps.
2. Walk: neither side clearly shows the destination ahead of the character. A at least shows the east edge (house, dark opening at the right) from 0.0s. B's 2.4s to 8.3s frames barely scroll. The character slides across a near-static screen to the right edge, and a dark wall and a new creature appear at 8.3s, so content pops in at the border.
3. Walk: B's frames are murky, with a heavy green fog or vignette over everything and blurry tree blobs and labels. A is clean, with no flashes or blank regions. A's weakness is that the world barely moves, so there is little sense of traversal.
4. Forest: B wins on lighting and depth. It has a vignette, darkened canopy edges, light shafts, drifting particles and a wide painted dirt path that curves through the scene, so it reads as a lit place. A is a flat saturated-green tile plane with uniform lighting and thin, tile-like brown paths.
5. Forest: A has the crisper, more readable tree silhouettes (hard outlines, clear trunks and canopies). B's dark trees at the bottom and right are mushy, dithered blocks with blocky square artifacts in the top-left canopy. B is moody but low-fidelity in detail.

### Fixes (verbatim)
1. Remove the layout swap between the first frame and later frames. Keep one camera and scale, and scroll the world under a centered or edge-following character instead of moving the sprite across a static screen.
2. Render the neighbouring area's terrain, path and trees past the screen edge, so the destination is visible before arrival and nothing pops in at the border.
3. Sharpen tree art. Replace blurry or dithered dark canopy blobs with crisp outlined silhouettes, and remove the blocky square artifacts in the top-left canopy.
4. Reduce the global green fog or vignette strength so mid-screen contrast and character and creature readability improve, while keeping the lighting and depth.
5. Add lighting and depth (canopy shadows, a soft path edge, an ambient gradient) to the flat tile ground, without losing crispness.

### Lead's reading
Tooling, mostly: the first in-page snapshot took 2.4 s and swallowed the crossing, and the Whispering
Woods route ran into Rocky Outcropping — a dead end with no east exit, where the camera clamps and
the hero slides to the screen edge. The exit breaker was also found to count wall-clock time
(fixed: game time). Route moved to the Light Forest; snapshot warmed with the key released.
