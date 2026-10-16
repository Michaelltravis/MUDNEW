# An open world (/play)

The owner: "I feel like the world should feel more open world like. Is this possible?"

The world underneath is a MUD's: rooms joined where an exit was written, each room a 24 x 15 m
cell on its zone's map. /play already draws a zone as one place; what still felt like boxes:

1. outdoor rooms side by side on the map joined only where an exit was written (corridors through a
   forest);
2. the land ending half a cell past a zone's edge rooms (darkness beyond);
3. draw distance (rooms past 3 cells hidden, for speed);
4. zone borders crossed with a fade and a load;
5. creatures living in rooms (they notice you, and wander, room by room).

| Phase | What | State |
|---|---|---|
| 1 | Open ground: side-by-side outdoor rooms join up; the land runs on past the edge | the Plains (zone 60) |
| 2 | See further: far rooms drawn cheaply, a horizon | |
| 3 | Seamless zone borders: the next zone streamed in as you near it | |
| 4 | A living world: creatures notice by distance and sight, wander real paths | |

## Phase 1: open ground (`src/wilds.py`)

In an opened zone (`wilds.WILD_ZONES`), two rooms side by side on the zone map
(`map_system.build_zonemap`) are joined both ways when both are open country (a land look:
forest, field, hills, desert, snow, swamp, stones, shore) and neither is flagged as walled
(death trap, private, immortal, tunnel, indoors). The joins are real exits (`'wild': True`), so
walking, followers, wandering creatures, reaching into the next room and pulls all follow them,
for telnet players too; the zone map gives them as `open`, and the 3D client draws the two rooms'
shared side as open country (roomgen.js).

Never a way the zone did not already have in another form: two rooms are joined only when one can
already walk from one to the other without passing a door (so a locked gate, its key and its
keeper keep their meaning: rites.py), and back again (a one-way drop stays one way). Water keeps
its banks (it needs a boat). Applied at world load after the room looks, before the tutorials'
routes.

The client (terrain.js `fillerLand`): in an opened zone the land skirt past an edge room reaches a
cell and a half out instead of half a cell, thinning into the fog.

The Plains: 19 new joins (most of its forest already opened onto itself). To open another zone,
add it to `WILD_ZONES`.

Checks: `python3 tests/test_polish.py` (the open ground section).
