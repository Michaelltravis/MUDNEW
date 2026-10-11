# onboard-01 / round 2 — decoded verdict (critic only)

Reference: BrowserQuest intro screen + first in-game screen. Critic confidence: medium. Seed 8102.
Misthollow side: fresh level-1 human warrior through the live wizard, after the round-1 first-screen fixes.

## onboarding — **WIN** (overall A -> mh; start A -> mh, first A -> mh)

| label | pick | decoded |
|---|---|---|
| start | A | mh |
| first | A | mh |

### Reasons (verbatim)
1. start: A shows nine classes with sprites, pitches, starting abilities and prime stats, so you can compare what you will be. B is a title screen with one generic avatar, a name field and PLAY.
2. first: A names the first objective (talk to Sage Aldric) in the Guide card, the welcome card and the toast, with a hotbar and an 'unlocks at level 6' hint. B's How to play scroll gives generic controls and no objective.
3. first: A is cluttered. The toast overlaps the zone banner and the NPC nameplate, and several cards compete. B's scroll hides most of a tiny viewport, though its pixel typography is clean.
4. first: A's small body text and footer have low contrast, but its HUD reads as a modern game.

### Fixes (verbatim)
1. Show one teaching surface at a time, merging the Guide card, welcome card and toast, and defer the Daily reward chip.
2. Stop the toast overlapping world labels, and add an arrow or ring pointing at Sage Aldric.
3. Raise small text size and contrast, and make the selected class state clearer.
4. Enlarge class sprites or add a preview pane, and shorten the descriptions.
5. Don't blur or dim the world while the welcome card is open.

### Lead's reading
Round 1 lost `first` on the dimmed wall-of-text modal; round 2 wins both labels. The world is no
longer dimmed (fix 5 was already in; the critic could not see it from a still). Acted on now
without a round: the first-timer hint toast and the Daily-reward chip are deferred while the
welcome card is up (one teaching surface at a time). The ring on the sage exists but pulses to
alpha 0, so a still can miss it. Left for a later picker round: bigger sprites/preview pane,
larger body text, stronger selected state.
