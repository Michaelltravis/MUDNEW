# graphics-01 / round 1 — decoded verdicts

Reference: BrowserQuest. Key: `pairs/key.json` (seed `unstamped:1`). A piece wins when the critic's overall pick decodes to `mh` for the piece's labels.

## atmosphere — WIN (overall pick B → mh on 4 of 5 labels; critic confidence low)

| label | pick | decoded |
|---|---|---|
| city | A | ref (loss) |
| forest | B | mh (win) |
| dungeon | B | mh (win) |
| cave | A | mh (win) |
| water | B | mh (win) |

Reasons (verbatim):
1. cave: A has two orange torch pools on the top wall that fade into a near-black rock floor plus a purple glow ring; B's cave is a flat black floor at uniform brightness with no light source anywhere.
2. dungeon: B reads as a necropolis at a glance (grey tombstones, ghost, blue fountain glow, grey haze, wall torches); A reads as a brown desert with dead trees and lava, not a dungeon, and is lit uniformly edge to edge.
3. city: B's Market Square is a small brick-tile box with a visibly repeating cobble grid and no landmarks, while A shows houses, tree canopies and paths that read as a village without any text; in forest and water, B's darker edge vignette and haze give depth where A's grass and sand are flat repeated tiles.

Fixes (verbatim):
- City floor is a bare repeating cobble grid inside a brick box: paint stalls, awnings, a well/fountain, cart ruts and irregular flagstone patches so Market Square reads as a market without the title text. (`src/web_isometric/platformer/themes-zones.js`)
- Add real light sources with radial falloff (lanterns, braziers, windows) to city, forest, water and the flat desert-style dungeon; right now those screens are uniformly bright and only cave shows falloff. (`src/web_isometric/platformer/immersion.js`)
- Break the visible tile grid on sand, grass and cobble with overlaid noise, scatter decals and soft edge blending so ground reads as painted terrain; also bump actor/exit contrast on the blue water floor where the player nearly vanishes. (`src/web_isometric/platformer/painter.js`)

Lead note: the critic's reasons in places describe the reference as "B" (e.g. the dungeon and city praise for "A"/"B" contradicts the key for those labels), so the label-level picks were used as given; the per-label decode is what counts.

## actors — LOSS (overall pick A → ref on city and combat, mh only on cave; critic confidence low)

| label | pick | decoded |
|---|---|---|
| city | B | mh (win) |
| combat | A | ref (loss) |
| cave | A | mh (win) |

Reasons (verbatim):
1. combat: A's player has a visible sword-swing pose and the rat/crab enemies are distinct critters against the grass; B's grave keeper is grey-on-grey among identical grey tombstones and is only identifiable by the 'GRAVE KEEPER - Crushing Blow' text banner, so the wind-up is unreadable without reading.
2. city: B's player sits under a bright halo/ring in the middle of the square and is found instantly; A's player is a small grey knight near a house with only a faint white box nearby and takes scanning to locate.
3. cave: A's bear is unmistakably hostile and huge, but it is drawn at roughly 3x the player's scale and overlaps the top wall so it reads as floating over the room edge; B's lone player is clean but there are no enemies at all to judge.

Fixes (verbatim):
- Give hostiles a silhouette-level hostile cue (red outline/underglow or a distinct palette) so the grave keeper is separable from tombstones and the floor without a text banner. (`src/web_isometric/platformer/scene-topdown.js`)
- Make the wind-up a sprite-level telegraph: enemy rears back (scale/skew/offset tween) plus a ground ring under the target, and a white hit-flash on the struck actor, instead of only a HUD banner. (`src/web_isometric/platformer/fx-abilities.js`)
- Normalize actor scale and anchor: the bear must be the same tile scale as the player and feet-anchored so it does not overlap walls and appear to float. (`src/web_isometric/platformer/dcss.js`)

## hud — LOSS (overall pick A → ref on city and dungeon; critic confidence low)

| label | pick | decoded |
|---|---|---|
| city | A | ref (loss) |
| combat | B | mh (win) |
| dungeon | A | ref (loss) |

Reasons (verbatim):
1. city/dungeon: A gives the world ~90% of the frame with a single bottom strip (health bar + 5 icons); B's playfield is a small window boxed in by Sector Map, Contacts, Quest, Message Feed, hotbar and compass panels, so the world is roughly a third of the screen.
2. all labels: A's text is large and high-contrast (white on dark strip, red health bar with clear fill); B's contacts list, feed timestamps, hotbar labels and the 'Le 38 warrior / 2075 gold' vitals readout are ~6px grey-on-navy and unreadable at a glance, and the tiny stacked HP/MP/XP bars sit buried in the bottom-left corner behind the stance chips.
3. combat: B wins the fight-state question outright: a big target panel names GRAVE KEEPER with a green HP bar and 'DANGEROUS' tag, a red telegraph bar 'Crushing Blow' with 'Q BRACE / E SIDESTEP' prompts, and the feed colors hits (yellow for yours, red for enemy's, 'hit YOU for 16'); A in combat shows only your own health bar and a rat with no threat, target HP or action cue at all.

Fixes (verbatim):
- Reclaim world area: collapse Sector Map and Contacts into small toggleable widgets (or overlay them translucently on the map edge) and shrink the bottom hotbar/vitals cluster so the playfield fills at least two thirds of the width. (`src/web_isometric/platformer.html`)
- Raise the minimum font size to ~12px and use white/near-white on the dark panels for feed lines, contact names, hotbar labels and the vitals readout; drop or dim the 00:00:00 timestamps so the message text is the first thing read. (`src/web_isometric/platformer/ui.js`)
- Make the player HP/MP bars a single large, high-contrast readout (BrowserQuest-style long red bar) placed in a clear corner away from the stance chips and hotbar, so vitals are glanceable even outside combat. (`src/web_isometric/platformer/ui-arpg.js`)
