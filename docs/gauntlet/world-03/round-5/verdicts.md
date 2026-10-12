# world-03 / round 5 — decoded verdict (critic only)

Reference: BrowserQuest walk. Seed 7305. Key: A = mh, B = ref. Critic confidence: medium.

## world — **WIN** (walk A → mh; forest A → mh)

### Reasons (verbatim)
1. Walk: A holds one framing and scale across 0.0s to 7.5s while the world slides under the character. The side-path junction appears at 2.4s, the grey and rabbit creatures drift past, and a pine enters at the top left by 7.5s, so the destination shows up ahead of the character. B covers 2.3s in one town square, and the character barely moves between 0.0s and 2.3s. It shows no traversal and no destination, so it proves little about continuity.
2. Forest: A reads as a lit place. It has a bright clearing around the path, a dark canopy vignette on the edges and bottom, and soft light falloff, and the path is painted and branches. B is a flat, evenly lit green tile plane with no light direction and no depth beyond the drop shadows.
3. Weakness of A: the trees are dark blurry blobs with no crisp silhouettes. The bottom and edge canopy is muddy and low contrast, and the whole frame looks soft and over-vignetted. B's trees and rocks are far crisper and more readable, and B wins on silhouette clarity. That is not enough to outweigh A's depth and continuity.
4. Neither side shows blank regions or full-screen flashes. A has a dark band at the right edge in the 7.5s frame and a faint seam in the canopy, which look like tile or chunk boundaries.

### Fixes (verbatim)
1. Sharpen the tree canopies. Give them a light rim and a clear outline against the dark ground, and reduce the blur and fog overlay so individual trees read at game scale.
2. Lighten the edge and bottom vignette and raise the mid-tone contrast, so the forest floor and the path edges stay legible and the scene stops looking muddy.
3. Remove the visible seam at the right edge of the 7.5s walk frame and the chunk boundaries in the canopy, so the world looks seamless.
4. Add crisp ground detail such as grass tufts, path edge stones and shadows to the path texture, to match the readability of the reference sprites.

### Lead's reading
First walk win at medium confidence, and with the sides swapped by the seed (ours was A this time).
The critic names what is still weak: blurry canopies at game scale, a heavy vignette, a dark band at
the right edge of the last frame (the two rooms' tree borders meeting), and chunk boundaries in the
canopy. Those are the next notes if a further round is wanted.
