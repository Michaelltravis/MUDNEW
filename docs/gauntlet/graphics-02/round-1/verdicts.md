# graphics-02 / round 1 / verdicts

Reference: BrowserQuest. Key seed `2026-09-03T14:25:00Z:1` (`pairs/key.json`, gitignored). Win rule: majority (overall pick must decode to `mh` AND more than half of judged labels decode to `mh`).

## hud — LOSS (0/2 labels; overall pick -> ref; confidence high)

| label | pick | decoded winner |
|---|---|---|
| city | A | ref |
| dungeon | A | ref |
| **overall** | **A** | **ref** |

### Critic reasons (verbatim)
1. city: A's HUD is a single bottom strip dominated by one tall red heart-icon HP bar readable from across the room; B's HP/mana/stamina are three ~4px-tall slivers with 7px '207 / 207' numerals, plus 'Lv 30 Warrior 0% xp 2875 gold' in near-illegible micro text, so vitals need a squint, not a glance.
2. dungeon: B paints two lines of ambient prose ('A chill wind blows... in the distance', 'the wall bones ... night') semi-transparently directly over the playfield and enemy, competing with the 'grave keep' nameplate and the top-centre 'Plaza of Bones' banner, so there is no single focal point; A has one focal (the centred player/cursor) and one message strip in the bar.
3. both labels: B stacks a location banner top-centre, a tiny unreadable time/weather readout top-right, a five-slot hotbar with 5px labels, a WASD diagram and a PANELS/Tab hint in one bar, so the eye has to scan six zones; A's bar is HP + message + player count + four icons, and in dungeon A the player is instantly locatable while in dungeon B the washed-out grey scene and grey prose make the party and the target hard to separate from the fog.

### Critic fixes (verbatim)
1. Make HP the one big element: a ~14-16px tall HP bar with large numerals and an icon, mana/stamina as thinner bars beneath; in combat pulse/flash it on damage so fight state reads at a glance. (`src/web_isometric/platformer/ui-arpg.js`)
2. Stop rendering ambient/room prose as floating translucent text over the playfield; route it into a single feed strip with a dark backdrop (or a fading one-line ticker), so the scene stays clean and text has contrast. (`src/web_isometric/platformer/ui.js`)
3. Cut HUD zones from six to three: drop the WASD diagram and tiny top-right readout (or fold into the location banner on hover), enlarge hotbar key/skill labels to >=11px, and give every HUD text a consistent min size and outline/backdrop. (`src/web_isometric/platformer.html`)

Note: the builder reports a 28px HP bar with 16px numerals, yet the critic measured "~4px-tall slivers with 7px numerals" in the montage. Either the montage downscale is shrinking the HUD (BrowserQuest's strip survives the same scale) or the builder's CSS block did not take effect in the capture; round 2's builder should verify the capture output before iterating.

Code for hud (`platformer.html`, `platformer/ui.js`) left uncommitted in the working tree for round 2.
