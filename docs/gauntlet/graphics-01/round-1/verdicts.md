# graphics-01 / round 1 — decoded verdicts

Reference: BrowserQuest. Key: `pairs/key.json` (seed `2026-09-02T23:35:00Z:1`; this restarted run regenerated the round-1 records that an earlier graphics-01 pass had committed in `eafdbd8`). A piece wins when the critic's overall pick decodes to `mh` for the piece's labels.

Key: cave A=mh, city A=mh, combat A=mh, dungeon A=ref/B=mh, forest A=mh, water A=mh.

## atmosphere — WIN (overall pick A → mh on 4 of 5 labels; critic confidence low)

| label | pick | decoded |
|---|---|---|
| city | A | mh (win) |
| forest | A | mh (win) |
| dungeon | B | mh (win) |
| cave | A | mh (win) |
| water | A | mh (win) |

Per-label picks decode to mh on all five labels; the overall pick A decodes to mh on every label except dungeon (where the critic's per-label pick B is also mh).

Reasons (verbatim):
1. cave: A's two wall torches throw warm pools that fade into darkness across the rock floor, plus a purple glow on the floor; B's cave is one flat brown wash with identical brightness in every corner and a hard repeating rock-wall tile border.
2. dungeon: A shows a sunlit tan desert with a lava stairway and a visible tile grid, nothing reads as a dungeon; B's grey fog, tombstone rows, torch sconces on the top wall and the brighter pool around the player read as a necropolis at night without the title text.
3. forest/water: A's lighting falls off toward the screen edges but the palette collapses: A forest player and mobs are green-on-green smudges and A water rocks nearly vanish in the blue tint, while B's forest trees/rocks/paths and B's beach-river-dock pop cleanly even though B's ground is a uniformly lit, obviously tiled grid.

Fixes (verbatim):
- Add per-source light falloff (torches, lava, windows) with a radial gradient into darkness instead of a single uniform brightness across the whole room; the dungeon and cave screens on the losing side have zero light sources that affect the floor. (`src/web_isometric/platformer/immersion.js`)
- Break the visible tile grid: paint the ground with soft edge blends, noise and terrain-edge feathering so grass/sand/rock read as painted terrain instead of repeating square tiles. (`src/web_isometric/platformer/painter.js`)
- Keep the biome tint from flattening readability: the murky forest and blue-washed water screens need actors, exits and rocks to keep a separate value/hue from the floor (rim light or outline) so the vignette does not swallow them. (`src/web_isometric/platformer/themes-zones.js`)

Lead note: fixes 1 and 2 describe the reference (the losing side on cave/dungeon/water), not mh; only fix 3 (forest/water readability of actors, exits and rocks under the biome tint) applies to mh.

## actors — WIN (overall pick A → mh on 3 of 3 labels; critic confidence high)

| label | pick | decoded |
|---|---|---|
| city | A | mh (win) |
| combat | A | mh (win) |
| cave | A | mh (win) |

Reasons (verbatim):
1. City and cave: A's player is a knight with a raised shield sitting inside a bright ground highlight ring, found instantly; B's player is a tiny grey rat-sized sprite on a busy floor, locatable only by the white cursor box next to it (cave B is a grey speck on dark brown floor).
2. Combat: A shows a wind-up state without text: red concentric rings on the ground under the grave keeper, a '!' warning marker above it, and floating '4' / '-16' damage numbers; B's rats and blonde player show no hit flash, no wind-up pose, no ground telegraph, so you cannot tell who is attacking whom.
3. Cave: A's bear 'Grimclaw' is a large dark silhouette that reads as a threat at a glance with a name plate, while A's city NPCs (stray dog, citiguards) all carry identical green bars so hostile vs bystander is not distinguished; B has no visible hostile actor at all in city or cave, only a rat that could be the player.

Fixes (verbatim):
- Make the player sprite larger and higher-contrast against floor tiles and add a persistent ground highlight ring so it is findable in one second (cave B is a grey speck). (`src/web_isometric/platformer/lpc.js`)
- Give hostile actors a red aggro tint/outline and bar colour distinct from neutral NPCs; neutral bystanders should not share the enemy treatment. (`src/web_isometric/platformer/scene-topdown.js`)
- Add a visible wind-up telegraph (ground ring plus pose/scale pulse) and a white hit-flash on damage so attack state reads without the log. (`src/web_isometric/platformer/fx-abilities.js`)

Lead note: fixes 1 and 3 describe the reference; fix 2 (neutral city NPCs sharing the green bar with hostiles) is the one that applies to mh.

## hud — LOSS (overall pick B → ref on city; per-label mh only on combat; critic confidence low)

| label | pick | decoded |
|---|---|---|
| city | B | ref (loss) |
| combat | A | mh (win) |
| dungeon | A | ref (loss) |

Reasons (verbatim):
1. city: A's dark-chrome HUD boxes the world into roughly 60% of the frame (right sidebar with a near-empty SECTOR MAP of dots, a CONTACTS list repeating 'cityguard' twice, a quest panel, plus top and bottom bars); B keeps a single bottom strip with one big red HP bar and gives the world ~90% of the screen while HP is still glanceable.
2. combat: A's HUD reads the fight in one glance: a centered GRAVE KEEPER plate with 756/768 HP and a DANGEROUS tag, an orange 'Crushing Blow' wind-up bar, and Q BRACE / E SIDESTEP / F INTERRUPT prompts under it; B shows nothing about the enemy at all, only the player's HP bar, so you cannot tell threat or what to do.
3. dungeon (and repeated in city/combat): the dark-HUD game's secondary text is too small at a glance: the 'ok · Lv 30' subtitle, hotbar labels ('attack','flee','bash'...), 'Lv 30 warrior 0% xp' and the sidebar body copy are ~6-8px on a 1300px-wide montage, and in combat the faint 'You swing at grave keeper... Miss!' prose floats over the scene; the single-bar game's text ('1 player', 'Welcome to BrowserQuest!') is large, high-contrast and never sits on top of the action. Overall winner is the single-bottom-bar game (B in city, A in dungeon); it loses only the combat label.

Fixes (verbatim):
- Collapse the permanent right sidebar (SECTOR MAP, CONTACTS, QUEST) into auto-hiding overlays or a toggled drawer so the world canvas gets ~85-90% of the width; in city and dungeon the sector map is a handful of dots and contacts duplicates entries, none of it worth a quarter of the screen. (`src/web_isometric/platformer.html`)
- Raise the minimum HUD font size: hotbar labels, the 'ok · Lv 30' subtitle, the xp/gold line and sidebar body copy must be at least ~12px with higher contrast against the dark chrome; drop or merge microcopy that cannot meet that size. (`src/web_isometric/platformer/ui.js`)
- Keep the boss plate / wind-up bar / Q-E-F prompts (they are the strongest thing on screen) but move the combat feed to a translucent 3-line ticker at the bottom edge of the world with a short lifetime, and remove the faint mid-scene 'You swing at ... Miss!' prose so nothing textual sits over the fight. (`src/web_isometric/platformer/ui-arpg.js`)
