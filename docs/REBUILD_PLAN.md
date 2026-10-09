# Rebuild plan — from first real playtest (2026-10-09)

The first real play on frostpine (not a bot, not a critic) found three things wrong. Root causes
in the code:

| complaint | cause |
|---|---|
| combat is horrible | combat resolves on a **4-second round** (`main.py` fires `combat_tick` every `TICKS_PER_SECOND * 4`; `PULSE_VIOLENCE = 2` in config is ignored). You press, then wait for the round. |
| the UI is too large | the camera zooms to **1.3× "fit one room"** (`scene-topdown.js`), so you see less than one room and a 16-px tile is ~68 px on a wide window; world labels scale with it. The HUD is sized for 1280×720. |
| movement between rooms is clunky | rooms are 24×15 tiles (crossed in ~3.5 s), exits are one-tile gaps in the wall middle, and every crossing waits on the server (pending-move lock up to 2.5 s). |

Decisions (owner): real-time action combat; the web client comes first, telnet may lag behind;
order 1 → 2 → 3 → 4. Every phase ships on its own (auto-deploy to frostpine) and is judged by
playing it, not by screenshots.

## Phase 1 — scale and readability
- Camera: zoom to a fixed world view (~34×19 tiles: the room plus its neighbours), not 1.3× one room.
- HUD ~30% smaller on wide screens; a UI-scale setting (S / M / L) remembered per browser.
- World labels (names, damage numbers, LOOT) sized in screen pixels, not world pixels.
- Underground zones (sewers, caves, crypts, mines) render as stone whatever their old sector tag;
  dark rooms say so ("too dark — hold a light"); neighbours of dark rooms are darkened too.
- Done when: a 1920-wide window shows a room and its neighbours with a HUD under ~15% of the screen.

## Phase 1 — status: shipped
Camera shows ~34×19 tiles (2.5× on a 1920 window instead of 4.25×); HUD scale (auto trims wide
windows; Settings → HUD size); smaller LOOT tag; enclosed zones (sewers, mines, crypts…) render
underground whatever their old sector tags; neighbours of dark rooms are dark; a dark room says
"hold a light". Exposed by the wider view: neighbour paintings arrive slowly (100–160 ms each,
thrown away on every room change) — solved structurally in phase 2.

## Phase 2 — movement (owner, after phase 1: "seamless walking between rooms, no room switching")
The zone is ONE map: rooms laid out on the atlas grid, openings where exits connect, walls where
they don't, one physics world, camera follows. Walking into another room's area sends the move to
the server in the background; nothing on screen rebuilds. Creatures and players stand in their
rooms' areas. Room paintings are made around the player progressively (nearest first, lower detail
far away) and kept in a bounded cache. Only a zone change (or up/down) fades.

- (superseded by the one-map design above; kept for the refusal rule) the server confirms in the
  background and only a refusal snaps you back.
- Wide openings: where two rooms connect, the shared wall is open across a third of its length.
- Faster walk; click-to-move with pathing across rooms (the minimap auto-walk, in the world).
- Done when: holding a direction through five rooms never stops the hero.

### Phase 2 — status, step 1 (shipped)
- Measured first: only 80% of in-zone exits land on the adjacent atlas cell and 7 of 59 zones lay
  out cleanly (MUD loops don't close), so a literal one-map-per-zone would break one exit in five.
  The world is therefore stitched AROUND THE PLAYER: every room is placed next to the one it
  connects to as you go, so every exit you walk through is seamless.
- Entering a room reuses the painting already made for the neighbour view (8 ms instead of
  100–160 ms of repaint at every crossing).
- Creatures seen in a neighbouring room stand on the slot they'll use once you walk in (they
  used to jump).
- Openings are 7 tiles on the long walls and 5 on the short ones (were 3), with clear lanes to
  match; all 3012 rooms pass `tools/qc_platformer_rooms.js`.
- Measured and ruled out: the server answers moves instantly (telnet and the websocket bridge);
  the 9 s crossings seen in headless tests are the test machine's ~1 fps software renderer.
- Owner after step 1: "crossing still feels like switching rooms".

### Phase 2 — status, step 2: optimistic crossing (shipped)
- The move is no longer sent at the doorway. The hero walks on through the opening; the moment
  they leave the room's rectangle into a laid-out neighbour in the same zone, the client switches
  rooms itself (atlas layout + the last payload's creatures, ~5–10 ms when the neighbour is
  already painted) and sends the move in the background.
- Payloads that still place you in the room you just left are ignored while the move is in
  flight; the server's confirmation just clears the flag.
- Only an explicit refusal from the server (or 30 s of silence) puts you back, just inside the
  edge. A short undo timer was tried and removed: on a slow confirmation it undid the switch,
  the hero crossed again and the server moved two rooms.
- Kept on the server path: closed/locked doors (opening them), zone changes, up/down, combat
  (you're held inside the room with "Flee to escape").


## Phase 3 — real-time action combat
- Server: replace round resolution for web players with per-action resolution — an attack is a
  request resolved within ~150 ms with its own swing time and cooldown; abilities keep their
  costs and get cooldowns. Mob AI ticks fast (~250 ms) and uses its existing intents as timed
  attacks with a wind-up you can see and leave.
- Client: every press swings immediately (prediction), hits land on the server's answer; floor
  telegraphs for mob attacks you dodge by moving; brace / stagger / perfect strike / interrupt
  become timing on actions, not rounds.
- Telnet keeps the old round loop until it is ported (owner: web first).
- Done when: a fight is decided by what you press and where you stand, second to second.

## Phase 4 — feel
- Hit-stop, knockback, impact sounds, death and respawn flow, then a playtest by the owner.

## Engine rebuild — a 3D client (owner, 2026-10-09: "still feels bad, rethink the engine")
Owner's verdict after Phase 2: stops at room edges, the screen jumps on crossing, walking feels
poor, the game is choppy. Choice: **new 3D engine + new art**, all-in (no stop-gap patching of
the Phaser client; it stays at `/platformer` until `/play` replaces it).

Why patching could not fix it (research, 2026-10-09): an unconditional clamp
(`scene-topdown.js:5413`) pins the hero inside the room so the seamless crossing almost never
ran; every crossing rebuilds the world at a new origin and evicts neighbour paintings
(`world-peek.js:179`); the server answers moves in text only and sends two full payloads of
every explored room per step.

Design: one continuous 3D world per zone; the client owns the hero's position and tells the
server which room it entered (`webmove <from> <to>`, structured `move_result`); per-zone layout
from the server (`/zonemap`); the DOM HUD (`ui.js`) is kept. Renderer: Three.js 0.185.1
vendored in `src/web_isometric/vendor/three/` (ES modules + import map, no build step); art:
CC0 low-poly (KayKit, Quaternius) — see `docs/art/SOURCES.md`.

| milestone | what | status |
|---|---|---|
| M0 | look and engine spike (now `/play?demo`) — four real room layouts (glade, brook, crypt, hall) stitched into one world, a knight on WASD/click with run/attack animations, skeletons, sun + shadows, torch lights, fog, bloom, see-through walls, F3 perf overlay | shipped; look approved (owner: "wow this looks awesome"; RTX 4070: 144 fps, 6.9 ms) |
| M1 | seamless world on real zones: `/zonemap`, terrain builders per theme, controller with A*, `webmove`, doors, passages, zone changes, login + HUD | **M1a shipped** (see below); M1b next |
| M2 | living world: class heroes, mob models, NPCs, items, other players' positions | |
| M3 | combat in 3D, then Phase 3 real-time combat | |
| M4 | polish, switch-over, retire the Phaser client | |

M0 notes: all URLs under `/v/<commit>/` are immutable (served gzip, `web_map.py`
`static_3d`), so a deploy never needs a hard refresh. Kit models are baked into float
geometry before instancing (the optimiser's quantised positions clamp at 1 m otherwise).
Headless test here: holding S walks the knight from the glade into the crypt at constant speed
across the room boundary (`z = 15`), no stop; ~110 draw calls, ~450k triangles with four rooms
in view. Smoothness and FPS are for the owner's Mac (F3 → "Copy perf report").

### M1a — the real game in 3D at `/play` (2026-10-09)
Owner: "you can redo the HUD to match the new 3d format" — `/play` has its own page and HUD;
the 2D client and its HUD stay at `/platformer`.

- Server: `/zonemap?zone=N|vnum=V` (`map_system.build_zonemap`: per-zone layout, up/down
  levels as islands, every exit `open` / `passage` / `zone`; all 60 zones: no shared cells,
  every `open` exit mutual and adjacent, 80 % of in-zone exits open); `webmove <from> <to>`
  (commands.py) answering a structured `move_result` on the map socket, no echo, name-only
  room output; `mode='near'` payloads add `nearby` rooms (within 3 cells, explored or not)
  with stable mob ids; one payload per move instead of two.
- Client (`src/web_isometric/world3d/`): `zone.js` (one coordinate space per zone, rooms
  streamed within 2 cells, crossings legal only through open exits, passage triggers),
  `sync.js` (moves sent without waiting; refusal → slide back with the server's reason;
  server-made moves relocate the hero, across zones too), `entities.js` (mobs/NPCs/players
  from `nearby`, nameplates, click/Tab targeting; beasts are placeholder wisps until M2),
  `controller.js` (A* click-to-move, minimap travel), doors (E opens), stairs / portals /
  zone-border passages with labels.
- HUD (`world3d/hud/`): login over a drifting 3D backdrop, character creation with the class
  model on a plinth, player frame, health/resource orbs, action bar (3 buttons to start,
  grows at levels 6 and 11, cooldowns), target frame with consider text, room/zone banner,
  toasts, chat log + command line, minimap from the zone map (click a room to walk there),
  menu (character, inventory, equipment, spells, quests), settings (quality, HUD size, F3).
- Verified here: `tests/test_webmove.py` (11 checks incl. closed door and sleeping
  refusals) and Playwright: login → Temple of Midgaard → hold W → server confirms the next
  room two frames after the hero enters it; temple stairs → God Simplex (zone hop); admin
  goto → The Whispering Woods (server-made zone change); Tab targets the nearest creature.
- M1b next: town buildings and interior theming (KayKit Medieval Hexagon, Furniture Bits),
  graveyards (Halloween Bits), monster/animal models (Quaternius), quest tracker and panels
  (inventory, character, spells), polish from the owner's playtest.

### M1b — progress (owner's order: monster models → towns and interiors → inventory → character panels)
- Owner after M1a: walking and the HUD feel good; stairs and lock/unlock doors to fix later;
  no monsters were visible in the sewers (fixed: /state replies wiped them during fights);
  wants to see more of the character's face (camera pitch now follows zoom, 34°–58°).
- Monster models: 38 CC0 Quaternius creatures (OpenGameArt, FBX → glTF in tools/art3d) plus
  procedural rats, spiders, snakes, rabbits and slimes; `world3d/bestiary.js` maps MUD names to
  bodies; creatures fighting you turn and strike each round, the dead fall before they vanish,
  flyers hover. Checked with `/play?demo&gallery=beasts` and in the live sewers and pet shop.
- Towns and interiors: streets get whole houses where they border empty map cells and
  shopfronts (chosen by the shop behind: smithy, tavern, church, market...) where they border
  an indoor room, low stone town walls elsewhere; interiors named as a temple, shop, tavern,
  bank, library, bedroom, guild hall, throne room or house are furnished (wood or stone floor,
  wall shelves, tables with stools, beds, benches and an altar, rugs, lamps); graveyards get
  rows of graves, fences and lanterns (`world3d/terrain-town.js`; KayKit Medieval Hexagon,
  Furniture Bits, Halloween Bits).
- Inventory (I): worn gear in its slots, the bag as a grid with the 2D client's painted item
  icons (`platformer/items.js`), tooltips (type, slot, level, damage, armour, effects, procs,
  weight, value), a menu per item (wear, wield, hold, quaff, eat, drink, recite, zap, brandish,
  read, look inside, examine, drop; remove for worn gear; double-click does the first), gold.
- Character sheet (C; K opens its skills tab): the hero turning in a 3D portrait, vitals,
  attributes (prime stat marked), hit / damage / armour / stance, experience ("max level" at
  the cap), active effects; skills and spells with proficiency, unlearned ones dimmed; talents.
- Still to come from the owner's notes: going up and down stairs, locking and unlocking doors.
