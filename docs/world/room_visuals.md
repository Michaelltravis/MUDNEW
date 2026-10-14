# Room visuals that match the room's text

The owner's example, A Sharp Bend In The Stone Circle [24641]:

> The circle makes a sharp turn at a stone wrapped in a collar of red-dyed wool. A narrow track leads east to the Third Altar Of The Stones, and the ring runs back north. The ground is pocked with the holes of old stakes, and an iron smell lingers in the air.

It was drawn as a market street: cobbles, shop fronts, crates of apples. The zone is typed `city`, so its rooms took the town look. The text talks of standing stones on open ground, but nothing in the room was read from the text beyond its look. It also got the ambient line "Warm light fills the interior spaces", an indoor line.

Two things decide what a room looks like in /play:
- **its look** (`room_looks.py`): what kind of place it is (cave, crypt, desert, town, forest...);
- **its features** (`room_features.py`, new): what the words say stands in it.

The audit (`tools/audit/room_text.py`, report in [room_text_audit.md](room_text_audit.md)) reads all 124 zones and 9,251 rooms:
- half of all rooms (4,656) name something standing in them, but none of it was drawn;
- 361 rooms are drawn against their text:
  - 211 have the town look and nothing of a town in the words (no streets, houses, shops, paving, windows or doors);
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

## Phase 2: the 211 town-look rooms with no town

These are rooms in zones typed `city` whose words describe something else. Worst first, with what their text actually says:

| Zone | Rooms | What the text says | Fix |
|---|---|---|---|
| 491 Morvoct | 34 | a fishing village: driftwood huts hung with nets, sandy paths | a `village` look: huts on sand |
| 408 Trade Road | 22 | the Dusty Road between low stone walls and fields | `field` |
| 475 World Of Chaos | 10 | a road laid of skulls | `necropolis`, or a bone-field look |
| 515 Orcus Temple | 10 | temple courtyards of black stone | `castle` yard in black stone |
| 30 Garathorm Inner City | 10 | quays, a riverside path, a Japanese garden | `shore` for the quay, a `garden` look |
| 54 New Thalos | 10 | the desert outside the gates | `desert` for the rooms outside the walls |
| 220 Castle Of The Apocalypse II | 10 | paths toward Ocam's Reach | read them; `castle` yard or `field` |
| 494 Eden | 9 | gravel paths between beds of lavender and sage | a `garden` look |
| 52 Thalos | 8 | the deserted temple grounds and gate of a ruined city | a `ruins` look |
| 439 Mount Olympus | 8 | | read them |

The work, per zone:
1. Read the rooms (`python3 tools/audit/room_text.py --zone N`).
2. Pick the look, with a reason in `world/looks.json`.
3. Check in the gallery.

**New looks to add here:**
- **camp**: tents, fire pits, palisade stakes on trampled earth. The ogres' Gathering Place [2245] is the clearest case: its text has log benches round a trampled square, but it is drawn now as a market square.
- **village**: huts of wood, wattle or driftwood on dirt or sand, nets and drying racks.
- **ruins**: broken walls, fallen columns and rubble under the sky.
- **garden**: hedges, flower beds, paths.

## Phase 3: roofed and open, the wrong way round

Each mismatch needs a look by eye, because the words can mislead: "Skyless Court" in the Black Observatory names the sky to say there is none. Cases that are wrong as drawn:
- **Underground rooms drawn under open sky.** In Below Moria (zone 465) the Freezer and the Labyrinth have the `snow` look, and the Fire Guardian's Chamber and the Tunnel To Hell have the `volcanic` look. All of them should be a cave, with ice or with lava. That needs underground forms of `snow` and `volcanic`: cave walls with a frozen or a burning floor.
- **A room inside a stone in the Stone Circle.** Inside The Great Stone [24671] is drawn as open turf. It should be `cave`.
- **Gullies and weed-grown ways on Leper Island (zone 449)** are drawn `inside`. They should be open.

The audit names each room. Most are fixed with a pin in `looks.json`. Rules in `room_looks.py` are added only where a word decides it for every zone; for example, "courtyard" or "clearing" in a room's name overrules a roofed zone default.

## Phase 4: each zone's colours and mood from its text

Zone text names its stone and light: black stone in Morkai, white marble on Olympus, red sandstone, green ghost-fire.
- Read them per zone: wall and floor tint, light colour, fog.
- Use them in place of one palette per look.

Features already read colours this way.

## Phase 5: landmark and boss rooms

The places players remember: boss lairs, the altars of the Stone Circle, throne rooms, The Temple [13685] with its great altar and painted red eye. A list of them, drawn up zone by zone, gets hand-placed set pieces in `world/setpieces.json`: what stands where, the light and any special effect. Each set piece takes over from the generated layout.

## Checks

- `python3 tests/test_room_features.py` checks:
  - the reader: 24641, places named as destinations, colours, plurals, stake holes, an altar and not a table;
  - that every feature the reader names, the client places and draws;
  - the world at load: features read, the zone map sends them, the Stone Circle draws as stones, its ambient lines are outdoor ones.
- `node --test tests/web/roomfeatures.test.mjs` checks placement:
  - no way out is ever shut;
  - solid features are walls to the walker;
  - most of what the words name is drawn;
  - the centrepiece stands nearest the middle;
  - colours are kept.
- `python3 tools/audit/room_text.py --md docs/world/room_text_audit.md` rewrites the audit after each phase. The wrongly drawn count should fall phase by phase.
