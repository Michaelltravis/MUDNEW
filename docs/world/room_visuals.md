# Room visuals that match the room's text

The owner's example, A Sharp Bend In The Stone Circle [24641]:

> The circle makes a sharp turn at a stone wrapped in a collar of red-dyed wool. A narrow track leads east to the Third Altar Of The Stones, and the ring runs back north. The ground is pocked with the holes of old stakes, and an iron smell lingers in the air.

It was drawn as a market street: cobbles, shop fronts, crates of apples. The zone is typed `city`, so its rooms took the town look. The text talks of standing stones on open ground, but nothing in the room was read from the text beyond its look. It also got the ambient line "Warm light fills the interior spaces", an indoor line.

Two things decide what a room looks like in /play:
- **its look** (`room_looks.py`): what kind of place it is (cave, crypt, desert, town, forest...);
- **its features** (`room_features.py`, new): what the words say stands in it.

The audit (`tools/audit/room_text.py`, report in [room_text_audit.md](room_text_audit.md)) reads all 124 zones and 9,251 rooms:
- half of all rooms (4,656) name something standing in them, but none of it was drawn;
- 361 rooms were drawn against their text before Phase 2, and 184 after it:
  - 211 had the town look and nothing of a town in the words (no streets, houses, shops, paving, windows or doors); 34 are left;
  - 95 are roofed (inside, cave, crypt) though the words speak only of sky, open air, grass or wind;
  - 55 are open-air though the words speak only of a ceiling, a chamber or a hall.

  A room's own name settles which it is: a tunnel stays roofed whatever wind blows through it, and a forest path stays open.

## Phase 1 (done): features, and the Stone Circle

**Features from the text** (`src/room_features.py`). At load, each room's name and description are read for about 40 kinds of thing:
- standing stones, altars, statues, obelisks, pillars;
- wells, fountains, braziers and fire pits;
- tents, cages and gibbets, stakes, skull poles, banners, cairns;
- skulls, bones, graves, coffins, candles, torches, lanterns, drums;
- thrones, tables, benches, shelves, beds, chests, barrels, crates, weapon racks;
- rubble, dead trees, mushrooms, flowers, fences, rugs, chains, crystals;
- blood, ash and scorch marks, stake holes.

How the text is read:
- **How many:** more than one when the text names it more than once or in the plural ("braziers smoulder at every corner").
- **Colour:** a colour said beside the noun goes with it ("a collar of red-dyed wool" puts a red band on the stone).
- **Centrepiece:** a feature in the room's own name ("At The Slaughter Stone", "The First Altar") is drawn larger and nearest the middle.
- **Not here:** a place named as where a way leads ("a track leads east to the Third Altar") belongs to the next room.
- **Not what it seems:**
  - "the stone floor" and "a stone bridge" are not standing stones;
  - an altar "like a low table" is not also a table;
  - "the holes of old stakes" are holes, not a stake.

The zone map sends each room's `features`.

**Placement** (`shared/roomgen.js`):
- Features stand on open floor, off the ways through and away from stairs and portals.
- Edge things go by the walls, centre things out in the open, and small things are scattered.
- Big features are solid to the walker. One is kept only while every way out can still be reached, so no feature ever shuts an exit.

**Drawing** (`world3d/terrain-features.js`):
- Built from the art kits where a piece exists: graves, coffins, skulls, banners, tents, beds, shelves, weapon racks.
- Otherwise made in code, in the same chunky style: menhirs with dyed bands, stone altars with candles and stains, statues, obelisks, cairns, cages, drums, braziers (lit), fountains, thrones, crystals, chains, and decals for blood, ash and stake holes.

**The Stone Circle of the Raven Clans** (zone 476) has its own look, `stones`, used by 70 of its 94 rooms:
- open moor turf with a worn grey track;
- standing stones and grey boulders round the edge, and a lone pine;
- grass tufts and pebbles;
- the meadow's wind for sound;
- outdoor ambient lines.

The classifier gives `stones` to any open room whose words say standing stones, a stone circle or monoliths, unless it is in a town.

Screenshots: `/play?demo&gallery=rooms&only=stones,slaughter,gathering,temple` shows four real rooms as their words read.

## Phase 2 (done): town-look rooms that are no town

Before this phase, 211 rooms had the town look with nothing of a town in their words. 34 are left, and they are real streets that never say so: Garathorm's Park Road and Concourse, New Thalos's drives, Mishrak's wall roads.

**Buildings typed as their town's street** are now drawn as rooms. An old import gave many buildings their town's sector, `city`, so they were drawn as market streets: the Orcus priests' quarters, the School House classrooms, Morvoct's huts, Brethrenmere's washrooms and newsroom. A city-typed room is now drawn as a room when:
- its name is a building's (quarters, hut, classroom, office, kitchen, workshop, sanctum, stable...);
- and its text reads indoors.

A den hacked out of the living rock (the Cyclops's in Morvoct) is drawn as a cave. These rooms also get indoor ambient lines now, not street ones.

**City-typed rooms whose words describe another place** take that place's look (`room_looks.py`, the `TOWNLESS` table). First match wins:

| Look | Words | Where |
|---|---|---|
| `necropolis` | a road, path or walkway of bones or skulls | World Of Chaos's Path Of Bones, the City of Ancients' Walkway of Bones |
| `ruins` (new) | ruins, ruined, crumbling, collapsed, broken columns, a deserted city | Thalos, the City of Ancients, a burnt-out inn on the Caravan Road |
| `garden` (new) | gardens, flower beds, lawns, hedges, orchards, beehives, a park | Eden, Ghenna's twisting hedges, Garathorm's park, Salem's Lot's town garden |
| `camp` (new) | camps, tents, fire pits, palisades | the ogres' Gathering Place and fire pit |
| `village` (new) | a village, huts, hovels, thatch, wattle, byres, a farmhouse, palms | Morvoct's sandy paths among the huts, the ogre village, Hommlet's lanes |
| `desert` | the desert, dunes, sands | outside New Thalos's southern gate |
| `field` | fields, countryside, meadows, pastures | the Great Field of Garathorm, the Old Road |

**Guards against real towns:**
- A ruin or a road of bones may stand in a town that names its houses.
- Every other look needs a text that says nothing of a town: no shops or houses, and no cobbles, paving, quays or town walls.
- A garden is never read from a road's name. Park Road is a street past the park.
- A look found only in the description must be named twice; a look in the room's own name is enough once.
- Villages, camps and ruins spread one room to neighbours with no words of their own, never onto a town street.

**Pins in `world/looks.json`**, about 100 rooms, each with its reason:
- Morvoct's cliffs and harpy nests are `mountain`, and its cyclops's den is `cave`;
- the Shortcut through the Mountain Range is `cave`;
- Ocam's Reach in the Castle of the Apocalypse is `dungeon`;
- the Trade Road's country roads (the Dusty Road over the heath, the Caravan Road, the King's Road) are `field`;
- Elvandar's common platform among the trees is `forest`;
- the Orcus Temple courtyard of black walls is `castle`;
- the Ocean Pier is `shore`;
- Mount Olympus's Gods' Table and thrones are a new look, `terrace`: white marble paving and whole marble columns under the sky.

**How they are drawn** (`world3d/terrain-places.js`, new; every piece is built in code):
- **village:** beaten-earth ground; round huts of wattle or mud under thatch, set just behind the open ground with their doors facing in; bushes, fence lengths and woodpiles along the edge; sacks, crates and barrels on the ground.
- **camp:** trampled mud; A-frame hide tents facing the middle; sharpened palisade stakes along the edge; logs, bones and sacks on the ground.
- **garden:** lawn with a pale gravel path; clipped hedges along the edge, trees behind them; flower groups and flowering bushes.
- **ruins:** grass over old paving; broken walls and broken columns of pale stone; rubble and fallen column drums.
- **terrace:** pale marble paving; whole white columns; nothing growing.

Each look has its ground colours, minimap colour, footsteps, ambient sound and the country drawn beyond the room's edge. The text reader also stopped misreading gardens: "beds of roses" are not beds, "petals carpet the paths" lays no rug, and "rain strikes the stone" raises no standing stone.

Screenshots: `/play?demo&gallery=rooms&only=village,camp,garden,ruins,olympus`.

## Phase 3 (done): roofed and open, the wrong way round

Each mismatch needed a look by eye, because the words can mislead: "Skyless Court" in the Black Observatory names the sky to say there is none. Fixed:
- **Underground rooms drawn under open sky.** Two new underground looks, `ice_cave` and `lava_cave` (`room_looks.py` UNDERGROUND): cave walls and roof with a frozen floor (ice sheets, icicles, pale blue crystals, a cold mood) or a burning one (black rock, glowing cracks in the floor, fire crystals, a red mood). Below Moria's Freezer, Labyrinth, Fire Guardian's Chamber and Tunnel To Hell, the Cold Tunnels, the Room Of Fire and the Natural Lava-Chamber take them. A room pinned in `looks.json` now wins over the look its zone states for all its rooms (those rooms were stated `snow` and `volcanic`).
- **A room inside a stone in the Stone Circle.** Inside The Great Stone [24671] is a `cave`.
- **Leper Island (zone 449):** the village footpaths, pens and yards are `village`, its garden a `garden`, the encampment a `camp`, the ponds and gullies open ground and hills.
- **Pins elsewhere:** caves in Durmandel and the Orc Tunnels drawn open, halls drawn as fields, gardens, ruins.

`tools/audit/room_text.py` counts the new looks (roofed: the caves; open: garden, ruins, terrace, camp). After this pass it counts 138 rooms drawn against their text; what is left is mostly words that mislead the reader (a "sky" painted on a ceiling, a "roof" of leaves).

## Phase 4 (done): each zone's colours and light from its text

`src/zone_tone.py` reads each zone's rooms for the colour of their stone ("black stone", "red sandstone", marble, obsidian) and of their light (ghost-fire, moonlight, torchlight). A zone gets a tone only where the words agree: mentions in proportion to its size (one room in eight, at least four) and most of the colours named. 20 zones have one, among them Olympus and the White Gold Cathedral (white), the Orcus Temple (black) and the Necromancer Mines (ghost light). Each room carries it in the zone map (`tone`); `/play` tints the paving and walls by the stone (`terrain.js` TONE_STONE) and blends the light into the room's mood (`main.js` TONE_LIGHT).

## Phase 5 (done): landmark and boss rooms

`world/setpieces.json` lays out twelve rooms by hand, among them the Throne of Shadows [24527], the Throne Room of Hades [3797], Moloch's Repose [13859], the Bone Throne [14027], the Slaughter Stone [24614], the Sharp Bend in the Stone Circle [24641], the Satanic Chamber [20597], the White Gold Altar [3409] and The Temple [13685]. Each says what stands where (a feature with an `x`, `y` on the room's 24 x 15 grid, a colour, which one is the centrepiece) and the room's light. `src/setpieces.py` puts them in place of the features read from the words; `shared/roomgen.js` places them where they were put, turns thrones, altars and statues to face the middle, and drops any piece that would sit on a way in or out, the stairs, a portal or the middle, or shut a way out. `terrain.js` hangs a light of the set piece's colour over the room.

Screenshots: `/play?demo&gallery=rooms&only=throneshadows`.

## Checks

- `python3 tests/test_room_features.py` checks:
  - the reader: 24641, places named as destinations, colours, plurals, stake holes, an altar and not a table;
  - that every feature the reader names, the client places and draws;
  - the world at load: features read, the zone map sends them, the Stone Circle draws as stones, its ambient lines are outdoor ones.
- `python3 tests/test_room_places.py` checks Phase 2:
  - buildings typed as streets are rooms, and a den is a cave;
  - bones, ruins, gardens, villages, camps and the terrace are each read right;
  - real streets stay streets;
  - the town-look count stays low;
  - a classroom gets no street ambient lines;
  - the reader's garden fixes.
- `tests/web/roomlooks.test.mjs` walks every look, the new ones included.
- `python3 tests/test_polish.py` checks the cave looks, zone tones and set pieces at load and in the zone map.
- `node --test tests/web/roomfeatures.test.mjs` checks placement (a set piece where it was put, facing the middle, never shutting a way out):
  - no way out is ever shut;
  - solid features are walls to the walker;
  - most of what the words name is drawn;
  - the centrepiece stands nearest the middle;
  - colours are kept.
- `python3 tools/audit/room_text.py --md docs/world/room_text_audit.md` rewrites the audit after each phase. The wrongly drawn count should fall phase by phase.
