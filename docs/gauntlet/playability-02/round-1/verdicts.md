# playability-02 / round 1 — verdicts

Reference: BrowserQuest. Key seed `2026-09-03T20:10:00Z:1` (`pairs/key.json`: combat A=ref B=mh; fight A=ref B=mh).
Win rule (ab): overall pick decodes to mh AND more than half of judged labels decode to mh.

## feel (ab) — **WIN** (overall B -> mh; labels 2/2 -> mh; confidence high)

| Label | Pick | Decoded |
|---|---|---|
| fight | B | mh |
| combat | B | mh |
| **overall** | **B** | **mh** |

### Critic reasons (verbatim)
- fight: A's eight frames (0.0s-10.5s) are visually indistinguishable apart from a tiny red digit near the tree and a bottom status line 'You killed a rat'; the player sprite never changes pose and the bottom-left health bar never moves, so who is winning is unreadable without prose. B's frame 0.0s shows an IN COMBAT nameplate with enemy HP bar, frame 1.0s shows a large 'SLAIN' with a damage number over the corpse, and frames 5.0s-7.0s show a '▼ LOOT' prompt above the body, so the state (fighting -> kill -> loot) reads frame by frame without text.
- combat: B's single frame has a '-4' damage number in large red over the grave keeper, a green enemy HP bar under its name, a top panel with 529/766 HP and a 'YOU 90% WINNING 69% KEEPER' comparison bar, and a glowing ring around the player marking the incoming/outgoing swing; A's frame has only pinprick-sized '4 6 6' numerals floating over a static rat and a plain grey target square, with no enemy HP bar and no visible wind-up.
- combat/fight: B's bottom bar puts numbered actions (1 attack, 2 flee, 3 bash, 4 cleave, 5 kick) plus HP 187/207 and a NORMAL stance chip at the screen edge, and the post-kill '▼ LOOT' prompt sits above the corpse, so the next action is told at the moment it matters without covering the fight; A's HUD is a single red bar plus icon buttons with no action prompts, so nothing on screen says what to do next.

### Critic fixes (verbatim; note these describe A = the reference, not Misthollow)
1. Add an enemy nameplate with an HP bar and a large, contrasting floating damage number on every hit; the current '4 6 6' numerals are too small and low-contrast to read at a glance against the grass. (`src/web_isometric/platformer/ui-arpg.js`)
2. Give the attacking enemy a visible wind-up (color flash or scale-up ~300ms before the swing) and a hit result (white impact flash and a short recoil/knockback of the struck sprite) so the fight frames are not identical static sprites. (`src/web_isometric/platformer/fx-abilities.js`)
3. Surface the next action in-world at the moment it matters (e.g. 'LOOT' / 'attack' prompt above the target after a kill) instead of only a status line at the bottom, and drive HP-bar changes on the player during the exchange so the tide of the fight is visible. (`src/web_isometric/platformer/scene-topdown.js`)

### Clerk note
The critic's fixes are addressed to the losing side, which decodes to the reference (BrowserQuest); no action for Misthollow's code. Feel code + records committed.
