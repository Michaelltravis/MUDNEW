# onboard-01 / round 4 — decoded verdict (critic only)

Reference: BrowserQuest intro + first screen. Seed 8104. Key: A = ref, B = mh. Critic confidence: **high**.

## onboarding — **WIN** (start B → mh; first B → mh)

### Reasons (verbatim)
1. start: Side B shows nine class portraits in a 3x3 grid with role subtitles and 'first pick' tags. The large right-hand preview panel shows the sprite, a one-line fantasy, the starting hotbar (1 attack, 2 flee, 3 bash) and a Choose Warrior button. You can compare what you will be and how you will fight without reading a paragraph. Side A is a name field, one generic sprite and PLAY, which is a login form with no choice. The 'Step 2 of 3' label and the one green CTA give B a clear next action.
2. first: Side B leaves the world visible and points at the objective. The Guide card at top-left, the gold '!' over Sage Aldric and the ringed NPC all say where to go. The hotbar at the bottom shows the three actions, and the welcome card says 'Three buttons now. More unlock at level 6', which hints at depth. Side A covers most of the screen with a parchment 'How to play' modal and lists generic controls. It names no objective and no destination, and it blocks the map until you click.
3. first: Side B is cluttered. The welcome card (bottom-right), the Guide card (top-left) and the hotbar compete at once. Faint ghost chat/log text ('doubled patrols...', 'slain by mage') sits over the map and muddies it, and the map looks blurred. The welcome card's 11px grey body text is small at 1280x720, and the Guide card text is tiny. A's single big 'How to play' panel has better type size and calm hierarchy, but it hides the game, so B still wins.
4. start: B's class tiles are small and the stat chips are about 9px, so the preview text is tight. The Mage tile has no first-pick badge and gives no obvious reason to choose it, so the comparison is weak beyond the three picks.

### Fixes (verbatim)
1. Show only one overlay on first load. Merge the welcome card and the Guide card into one objective prompt, and show the second teaching step after the first action is done.
2. Remove or hide chat/log ghost text and the heavy blur or vignette behind it on the first screen, so the world reads crisp and inviting.
3. Add a visible arrow or path line from the player to Sage Aldric, and make the objective card text 13-14px with higher contrast.
4. Make the class tiles and preview bigger, with larger stat chips (at least 11-12px). Add a short animated attack idle to the preview sprite. Add a name field and appearance choice so it reads as a character creator.

### Lead's reading
Third critic round on this piece, first at high confidence, with the focus-pane picker and the deferred
toasts in place. Open notes for a later pass: one overlay on first load (merge the welcome card into the
Guide), hide the ambient log ghost text on the first screen, an arrow or path line to the sage, larger
body text in the Guide and welcome, bigger class tiles.
