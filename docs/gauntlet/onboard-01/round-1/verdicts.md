# onboard-01 / round 1 — decoded verdict (critic only)

Reference: BrowserQuest intro screen + first in-game screen (how-to-play parchment left open). Critic confidence: medium. Seed 8101.
Misthollow side: a brand-new level-1 human warrior forged through the live wizard (`tools/gauntlet/capture-onboard.js`).

## onboarding — **WIN** (overall A -> mh; start A -> mh, first B -> ref)

| label | pick | decoded |
|---|---|---|
| start | A | mh |
| first | B | ref |

### Reasons (verbatim)
1. start: A is a real choice. Nine class cards sit in a 3x3 grid, each with a sprite, a one-line fantasy, starting skills and a prime stat, so you can compare what you will be. B is a name field, one generic avatar and a PLAY button, which is a form with no choice. B's hierarchy is clear (one big red PLAY), but there is nothing to decide. A's weaknesses: the card text is tiny, the sprites are small, there is no visible CTA or confirm button, the selected state is only a faint border on Warrior, and the 'STEP 2 OF 3' header sits in dim grey.
2. first: B teaches three short lines with icons (click to move, Enter to chat, auto-save) over a visible, bright map, and its close hint reads 'click anywhere to close'. That is under ten seconds to read. It never says where to go or what the first objective is, though. A is a wall of text in a centre modal: a paragraph about bash and execute, a keybind table, a quest-giver paragraph and a group command. The world behind it is dimmed and blurred to near black, so nothing is visible, and the text is small at 1280x720. A does name the first objective (talk to Sage Aldric, the gold !), but buried mid-paragraph.
3. Overall: A's start screen is much stronger and closer to modern character creation, which outweighs B's cleaner first-screen tutorial. A's first screen undoes its own promise of 'three buttons, depth later' by dumping depth, keybinds and social commands into the same modal.

### Fixes (verbatim)
1. Cut the welcome modal to three icon-led lines (Move, Attack with F, Talk to the glowing ! sage) and keep the keybind table behind a '?' or 'Controls' link. Mention depth in one hint line, e.g. 'More unlocks at level 6'.
2. Do not dim or blur the world behind the welcome. Use a light scrim or a small corner card, and add a pulsing arrow or ring on Sage Aldric and the '!' marker as the first objective.
3. On the class picker, enlarge the sprites and show the three starting buttons as icons. Add a strong selected state, a large preview of the selected class, a visible 'Choose Warrior' CTA, and bigger body text.
4. Group the nine classes into 3 archetypes or highlight 3 recommended beginner classes, so the choice does not become paralysis. Put a one-word role tag (Tank, Burst, Support) on each card.

### Lead's reading
The piece wins on the strength of the picker; the first screen is the loss and it is our own
welcome card contradicting itself. Fixes 1 and 2 are small and go in now; 3 and 4 are the next
round of the picker if one is wanted.
