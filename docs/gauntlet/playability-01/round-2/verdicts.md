# playability-01 / round 2 — verdicts

Key seed `2026-09-03T16:05:00Z:2` — reference BrowserQuest. Decoded from `pairs/key.json` (gitignored): for both labels **A = mh, B = ref**.

## feel (ab) — **LOSS**

| label / overall | critic pick | decoded |
|---|---|---|
| fight | B | ref |
| combat | B | ref |
| **overall** | **B** | **ref** |

Win rule: overall -> mh AND >1/2 labels -> mh. Result: 0/2 labels, overall ref -> **LOSS** (confidence: high). Code left uncommitted in the working tree (`scene-topdown.js`, `ui.js`, `ui-arpg.js`; `fx-abilities.js` untouched).

### Critic reasons (verbatim)
- fight: A's eight frames (0.0s-10.5s) are near-identical - the knight stands in the same blue puddle spotlight, the skull/ghost enemies never close in, the HP bar stays full red and no number or flash changes; nothing on screen says a fight is even happening. B's frames change: the rat is adjacent to the player at 0.0-4.5s, the bottom log strip reads 'You killed a rat' at 1.5s-4.5s, and the red HP bar visibly shrinks in the 7.5s-10.5s row, so you can track the exchange frame by frame.
- combat: B has legible hit feedback - a white '4' and a red '6' floating above the player's head (outgoing vs incoming damage in different colours), a named tag 'Critic', a target reticle square on the rat and a second rat lunging at the player. A shows the knight at HP 207/207 with the nearest enemy a screen-width away, a faded 'corpse of ...' label, and no damage number, impact flash, or recoil anywhere.
- combat/next action: B's target square on the rat plus the rat's contact sprite tells the player what they are fighting and where to click, without covering the action. A's hotbar (attack/flee/bash/cleave/kick) is a static row of labels at the bottom with no marked target, no cooldown state and no cue on the field about which enemy those buttons apply to.

### Critic fixes (verbatim)
1. Spawn floating damage numbers (white for player hits, red for hits taken) and a 2-3 frame white impact flash + small recoil on the struck sprite every time damage resolves; currently the fight leaves the scene pixel-identical for 10 s. — `src/web_isometric/platformer/fx-abilities.js`
2. Give enemies a visible wind-up before their attack (sprite pull-back / red tint for ~0.4 s) and a stagger pose after being hit, and make them actually close to melee range so the exchange reads in the storyboard. — `src/web_isometric/platformer/scene-topdown.js`
3. Draw a target reticle around the currently engaged enemy with its HP bar and name over its head, and highlight the hotbar slot that applies to it, so the player knows who they are fighting and what to press without reading the log. — `src/web_isometric/platformer/ui-arpg.js`

### Lead note
The critic's description of A (HP 207/207 in every frame, nearest enemy a screen-width away, a faded "corpse of ..." label, no damage numbers) is the same picture as round 1: the storyboard was again captured after the keeper was already dead / before a fight was on camera, so none of the round-2 builder's work (wall-clock damage numbers, adjacent mob stance, last-beat tell, SLAIN stamp, reactive action bar) was judged. The builder's own note says `page.screenshot()` takes ~6-7 s here, so "1.5 s" frames are ~8 s apart and the kill lands around frame 5-6 — yet the critic saw no fight at all. The capture harness must be fixed before a round-3 feel verdict means anything.

## pacing (key) — closed, won round 1 (not judged this round). Fight transcripts for this round: `fight/fight_keeper.*` (12 rounds, 207->136 hp, mob killed) and `fight/fight_bear.*` (9 rounds, 207->158 hp, mob killed).
