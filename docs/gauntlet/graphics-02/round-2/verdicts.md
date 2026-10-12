# graphics-02 / round 2 / verdicts

Reference: BrowserQuest. Key seed `2026-09-03T14:25:00Z:2` (`pairs/key.json`, gitignored). Win rule: majority (overall pick must decode to `mh` AND more than half of judged labels decode to `mh`).

## hud — WIN (2/2 labels; overall pick -> mh; confidence low)

| label | pick | decoded winner |
|---|---|---|
| city | A | mh |
| dungeon | B | mh |
| **overall** | **B** | **mh** (see decode note) |

Decode note: the key differs per label this round (city A=mh/B=ref, dungeon A=ref/B=mh), so a single overall letter cannot map cleanly to both labels. The critic's reasons name the preferred set explicitly as "city A / dungeon B", which is `mh` on both labels, and the overall `B` matches the dungeon label whose fight-state evidence the critic leaned on. Decoded as `mh`; the per-label picks are unambiguous at 2/2. Flagged in STATUS.md for the human brake because the critic's confidence is `low`.

### Critic reasons (verbatim)
1. city A / dungeon B: the HP bar carries a big white '207 / 207' readout, a numbered hotbar (1 attack, 2 flee, 3 bash, 4 cleave, 5 kick) and a 'NORMAL' stance chip, so fight state and available actions are readable in one glance; city B / dungeon A has a single unlabeled red bar with no number and the rest of its strip is spent on 'Welcome to BrowserQuest!' and '1 player', which say nothing about the fight.
2. dungeon B shows the enemy 'grave keeper' with a nameplate and a green health sliver above its head next to the player, so threat is visible in-world; dungeon A has no enemy, no target, and no nameplate anywhere on screen, and its HUD strip has nothing that would change during combat.
3. Both strips take roughly the same ~10% bottom band and leave the world untouched, but city A / dungeon B wastes that band: the mana/stamina sub-bars with '169/169' and '254/254' and the 'Lv 30 Warrior 0% xp 2075 gold' line are rendered so small they are unreadable at a glance, and the hotbar skill names sit in ~8px grey text under the numbers, so the secondary tier is noise rather than hierarchy.

### Critic fixes (verbatim)
1. Give the HP bar a numeric readout and a label so vitals are glanceable instead of a bare red sliver; drop the 'Welcome' / player-count text from the strip and replace it with target name + target health when something is engaged. (`src/web_isometric/platformer/ui-arpg.js`)
2. Add a hotbar with keyed, labeled actions so the HUD tells the player what to do, not just that they exist; use one type size for labels (>= 11px) and one for keys, with high-contrast text over a dark backing. (`src/web_isometric/platformer/ui.js`)
3. Attach nameplates with health bars to enemies in-world so threat is visible at the point of action instead of only at the bottom of the screen. (`src/web_isometric/platformer/ui-arpg.js`)

Note: fixes 1-3 are addressed to the *losing* side (the reference), so none of them are actionable on Misthollow. Reason 3 is the one real criticism of our side: MP/MV sub-bars, the level/xp/gold line and the hotbar skill names still read as ~8px in the montage despite the builder's 11-13px floor — the same builder/critic size mismatch seen in round 1.

Code for hud (`platformer.html`, `platformer/ui.js`, `platformer/ui-arpg.js`) committed with this record.
