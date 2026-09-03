# graphics-01 — round 2 verdicts (decoded)

Key: `docs/gauntlet/graphics-01/round-2/pairs/key.json` (seed `unstamped:2`, reference BrowserQuest). A piece wins when its overall pick decodes to `mh`.

## actors — **WIN** (overall pick B → mh; 3/3 labels)

| label | pick | decoded |
|---|---|---|
| city | B | mh |
| combat | B | mh |
| cave | B | mh |

Confidence: high.

Reasons (verbatim):
1. city: B's player is a shield-bearing knight sitting inside a bright blue ring/aura at screen centre and is found instantly; A's player is a tiny grey sprite on the sand path next to a white selection box that reads identically to the grey guard NPCs on the rooftops, so it takes scanning to find.
2. combat: B shows the grave keeper with a red hostile ring under it, a red 'Crushing Blow' wind-up banner with a timing bar, and a floating '34' damage number, so attack, wind-up and hit are readable with no text; A shows a blonde figure holding a sword sprite next to a rat with no flash, no ring, no telegraph, and the nearby skeleton is not visually flagged as hostile versus the pink-dressed bystander.
3. cave: B's bear is a large dark silhouette lit under a torch with a name label and the player carries the same blue ring; A's cave has only the grey player sprite with a selection box on a dark floor and no visible enemies at all, and the grey sprite plus box reads as a flat cursor rather than a character.

Fixes (verbatim; note these describe A = the reference, so they are already satisfied by mh):
- Draw a persistent coloured ring/aura under the player (and a red one under aggressive mobs) so the player pops from same-palette NPCs; A's grey warrior is indistinguishable from the grey guards. (`src/web_isometric/platformer/scene-topdown.js`)
- Add a visible wind-up telegraph (ground circle or pulsing outline on the attacker) and a white hit-flash/knock on the target when damage lands; A's combat shot shows only a static sword sprite next to the rat. (`src/web_isometric/platformer/fx-abilities.js`)
- Give hostile sprites a distinct tint/outline from friendly bystanders so a skeleton and a villager are not both plain unmarked sprites in the same shot. (`src/web_isometric/platformer/lpc.js`)

## hud — **LOSS** (overall pick A → ref for city and combat; 1/3 labels)

| label | pick | decoded |
|---|---|---|
| city | A | ref |
| combat | B | mh |
| dungeon | B | ref |

Confidence: low.

Reasons (verbatim):
1. city A and dungeon B (the game with a single thin bottom bar) give the world roughly 90% of the frame with one red HP bar readable at a glance; city B and dungeon A (the dark-panel game) lose the right ~30% to a sector map, contacts list and message feed, and another strip to a 10-slot action bar plus prompt line, so the world sits in a ~55% window.
2. In combat B the dark-panel HUD tells the fight state instantly: an enemy frame with a green HP bar '798/798 LV 35 DANGEROUS', an orange telegraph 'Crushing Blow' with Q BRACE / E SIDESTEP / R INTERRUPT prompts, and red feed lines 'grave keeper hit YOU for 15/34'; combat A shows nothing but the player's own HP bar dropping, no enemy health, no feed, no cue for what to do.
3. The dark-panel game's text is tiny and low-contrast: contacts entries ('cityguard LV 18'), the quest line and the dungeon feed ('-> The Temple Of Midgaard', '-> Market Square') are ~8px grey-on-navy and the dungeon feed is just a room-name log with no combat value; the bottom-bar game's 'Welcome to BrowserQuest!' and HP bar are the only text and are legible at a glance.

Fixes (verbatim):
- Give the world at least 75% of the frame: collapse the right column (sector map, contacts, quest, feed) into an overlay or a narrow toggleable drawer, and shrink the bottom bar to HP/XP plus hotkeys on one row. (`src/web_isometric/platformer.html`)
- Raise HUD/feed type to a 12-13px minimum with high-contrast white on dark and drop the grey-on-navy body text; cap the feed to the last 4-5 lines and hide room-name traversal entries so only combat and dialogue lines remain. (`src/web_isometric/platformer/ui.js`)
- Out of combat, hide the enemy target frame, telegraph strip and the empty message feed panel entirely so the screen has one focal point (the world) and the combat elements only appear when IN COMBAT fires. (`src/web_isometric/platformer/ui-arpg.js`)
