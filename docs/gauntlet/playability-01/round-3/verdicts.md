# playability-01 — round 3 verdicts

Key seed: `2026-09-03T16:05:00Z:3`. Reference: BrowserQuest. Decoded from `pairs/key.json` (gitignored): combat A=mh B=ref; fight A=mh B=ref.

## feel (ab) — LOSS

| label / question | pick | decoded |
|---|---|---|
| fight | B | ref |
| combat | B | ref |
| **overall** | **B** | **ref** |

Result: 0/2 labels -> mh, overall -> ref. **Loss** (confidence: high). Code left uncommitted in the working tree (`scene-topdown.js`, `ui.js`, `ui-arpg.js`; `fx-abilities.js` untouched).

### Critic reasons (verbatim)
- fight: A's eight frames (0.0s-10.5s) are visually near-identical: the knight stands in the same spot with the same blue ring and no visible enemy, no hit flash, no numbers, and the bottom HP bar never visibly changes, so you cannot tell who is winning or even that a fight is happening; B's frames show a rat beside the player, a 'You killed a rat' banner at 1.5s/3.0s/4.5s, and the player relocating toward a second rat by 9.0s, so the arc of the fight reads frame by frame.
- combat: B has a mid-swing sword pose on the player, a rat in contact, floating damage numbers '4' and '6' above the target, and a white target reticle box, i.e. wind-up, contact, and result on one frame; A's combat frame has no enemy on screen at all, only a 'corpse of ...' label and a static knight sprite with no impact flash, recoil, or numbers.
- combat: A's hotbar (1 attack / 2 flee / 3 bash / 4 cleave / 5 kick) is the only next-action cue and it sits in the bottom strip far from the action with no highlight on which key matters now, while B's reticle sits on the target itself and the damage numbers land at the point of impact, telling the player what to hit without covering the scene; A's washed-out grey fog also hides the enemy skulls so the threat is not legible.

### Critic fixes (verbatim)
1. Put the enemy telegraph and result on the sprites: a visible wind-up (enemy lunge/tint) 0.3-0.5 s before the hit, then impact flash, knockback recoil and a floating damage number at the hit point for both player and enemy, so a 1.5 s storyboard shows state change every frame. (`src/web_isometric/platformer/fx-abilities.js`)
2. Draw a target reticle/HP bar directly over the engaged enemy and make the engaged enemy stand out against the fog (higher contrast, outline); currently no enemy is discernible in any fight frame. (`src/web_isometric/platformer/scene-topdown.js`)
3. Highlight the currently-relevant hotbar key (ready/cooldown pulse) and flash the HP bar on damage so the bottom strip changes with the fight instead of staying static across all 8 frames. (`src/web_isometric/platformer/ui-arpg.js`)

### Clerk note
For the third round running the critic describes A as a static knight with no enemy on screen and a "corpse of ..." label — the storyboard was again captured against an already-dead keeper. The builder reproduced this exactly (capture without `zreset`) and showed a live fight appears in frames 0-3 when `zreset` precedes `kill keeper`; `tools/gauntlet/capture.js` was not changed before this round, so the critic never saw the round-2/3 feel code (bracket, ledger numbers, hit flash, reels, reaction prompt). The loss is real under the rules but is not evidence about the code.

## pacing (key) — closed (won round 1, not judged this round)

Fight transcripts this round (`fight/summary.json`): keeper 15 rounds / 57.6 s, 207 -> 126 hp, telegraph 12, reaction prompts 3, staggers 8; grimclaw 13 rounds / 51.8 s, 207 -> 142 hp, telegraph 12, reaction prompts 2, staggers 4. Both ended mob_killed, 0% rounds without a decision. Counter mismatch persists (decision_rounds 20 > rounds 15).
