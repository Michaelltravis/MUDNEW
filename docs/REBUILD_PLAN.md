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
| M1 | seamless world on real zones: `/zonemap`, terrain builders per theme, controller with A*, `webmove`, doors, passages, zone changes, login + HUD | **M1a shipped**; M1b shipped (monsters, towns and interiors, inventory, character sheet) |
| M2 | living world: class heroes, mob models, NPCs, items, other players' positions | |
| M3 | combat in 3D, then Phase 3 real-time combat | **combat v2 ready for the owner's test** (see below): events, reach, timing, wind-ups |
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

### M3 — combat on the new engine (owner, 2026-10-09: "I need to see some combat actions… distance from NPCs can and should matter")
Combat v2 keeps the server's rules (rounds, skills, spells, proficiency, poise, brace and
sidestep, creature wind-ups) and adds positions, reach and a structured event for every line
the combat log prints, so the 3D client animates exactly what the log says.
- **Events** (`src/combat_events.py`, `src/combat_hooks.py`): swing, skill, spell, wound,
  heal, death, fizzle, wind-up, resolve, cancel, out-of-reach and creature moves, batched per
  room in the order the log prints them, sent to the web clients standing in the room
  (`combat_events` on the map socket). Telnet output is unchanged.
- **Timing**: a round is 3 s; creatures act 1.3 s after the heroes, so blows alternate instead
  of landing in one heap. A number rises when its blow lands (a sword 0.3 s into the swing, an
  arrow or bolt when it arrives); a creature's second and third blows follow 0.42 s apart; the
  dead fall after the killing number. Pressing a skill starts its own animation at once; the
  server's answer adds what flies and lands. A creature's wind-up marks the ground for the 4.3 s
  until it lands.
- **Positions** (`src/combat_range.py`): metres inside a room (24 × 15). The client reports
  the hero's spot (5×/s in a fight) and where it placed the creatures; the server moves
  creatures in a fight (5×/s): melee ones close to reach, archers and casters keep their
  preferred distance, everyone keeps 1.1 m apart. Telnet players have no position and are
  always in reach.
- **Reach**: an ordinary blow needs its class's reach (out of it: no blow, a message; melee
  heroes walk in by themselves, archers and casters keep their spot). Skills and spells check
  their range before they cost anything; the client walks just far enough (an archer stops at
  bow range). A skill aimed at a creature you are not fighting yet opens the fight.
- **Dodging**: a heavy blow comes down where you stood when it began (2 m), a spell where you
  stood (1.7 m), a sweep around the creature (4 m). Step out before it lands and it "hits only
  ground"; brace and sidestep still work, and staggering or kicking the creature breaks it.

| Class | Ordinary blow | Skills and spells (metres) | How it plays |
|---|---|---|---|
| Warrior | melee 2.5 | bash, kick, execute 2.5 · cleave cone 3 · charge dash from 15 · rally aura 8 · rescue 6 | charge in, hold the front |
| Paladin | melee 2.5 | censure, order verdict 2.5 · holy smite 14 · absolution heal 12 · halo aura 5 · turn undead cone 8 | front line with a ranged smite |
| Cleric | melee 2.5 | holy smite 14 · cure light, heal, bless 12 · flamestrike blast 3 at 14 · turn undead cone 8 | mid-range healer |
| Ranger | bow 16 (under 3 m: 60 % damage) | truesight shot 18 · loosing storm blast 3.5 at 16 · quarry mark 20 · call lightning 16 · wildbond strike 2.5 | keep your distance |
| Thief | melee 2.5 | backstab, circle, trip, low blow, jackpot 2.5 · pocket sand 5 | in close |
| Assassin | melee 2.5 | backstab, expose, vital, feint, execute contract 2.5 · mark 15 · fade | mark from afar, strike close |
| Mage | arcane bolt 10 (weak point-blank) | magic missile 18 · fireball blast 3 at 16 · lightning bolt 18 · towerbolt 20 · sleep 12 · chill touch 2.5 | back line, blasts |
| Necromancer | shadow bolt 10 | soul bolt 16 · soul siphon 10 · soul reap blast 4 at 14 · chill touch 2.5 · animate dead | back line, drains |
| Bard | melee 2.5 | mockery 14 · fascinate 12 · discordant note cone 7 · crescendo aura 6 | mid-range support |
| Creatures | melee 2.2 | archers 15 (prefer 9) · casters 13 (prefer 8) · healers and support 12 (prefer 8) | |

Areas (cone, blast, aura) are drawn on the ground; who they hit is still decided by each
skill's own server code.
- Fixed on the way: `cast 'lightning bolt' orc` (any two-word spell with a target) looked for
  a target called "bolt orc"; spells now fizzle only after the target and range checks, and a
  fizzle shows on screen; an archer's or caster's ordinary blow reads as an arrow or bolt in the
  log; Tab prefers enemies over shopkeepers, trainers and quest-givers; overlapping hit flashes
  could leave a model stuck red.
- Verified here: `tests/test_combat_v2.py` (3 runs green: out of reach → no blow + `oor`, the
  creature walks in, swings and wounds as events, a skill opens a fight, a wind-up lands
  4.32 s after its 4.3 s mark, stepping out of it makes it miss, a stagger cancels it) and
  `tests/test_webmove.py`; Playwright with a level-15 mage (magic missile, fireball, lightning
  bolt, sleep, towerbolt as an opener, fizzles, the bear's sweep, the kill; no page errors),
  ranger and cleric. This container renders WebGL at ~1 fps, so the feel (timing of swings,
  bolts and numbers) is for the owner to judge on a real GPU.
- Next, from the owner's test: tune numbers (round length, reach, wind-up time) and the look
  of each skill; then Phase 3 (per-action resolution) if rounds still feel slow.

### Stairs and doors (owner, 2026-10-10: "the stairs and lock/unlock doors next")
- **Stairs** (`world3d/passages.js`, `zone.js`, `main.js`): a hop stays in flight until the
  arrival is applied, so a zone hop is sent once (the zone map download used to race the next
  frame: a second move, "You can't go that way.", a double flash). You land 1.6 m beside the
  stairs that lead back (up/down exits are named by direction of travel; the client used the
  wrong side). A gate keeps the stairs you arrived beside quiet until you walk away, stand still
  a moment or click them, plus a 1.2 s cooldown: holding a key into them no longer bounces you
  back. Stairs fire only when you move onto them (or a click sends you there); paths and the
  combat chase walk around them; they are blocked in a fight like doorways. `webmove` takes the
  exit the client names (`webmove 3001 3005 down`: 86 room pairs have stairs and a doorway to
  the same room). The step onto and off the stairs is animated under the fade; creatures and
  followers changing level snap there in a puff of dust. ▼ Down is a stairwell now (a dark
  opening, rim and steps), ▲ Up a staircase climbing away from where you arrive; labels say
  where they lead; furniture keeps off them; the minimap shows ▲/▼ and minimap travel crosses
  stairs (re-planned after each hop).
- **Doors** (`src/doors.py`, door commands, `cmd_webdoor`, `world3d/doorlogic.js`, `hud/prompt.js`,
  `hud/castbar.js`, `hud/contextmenu.js`): one module finds doors (`s` is south and `u` up — they
  used to resolve to east and south; names work: `unlock wooden`, `open door wooden north`),
  changes both sides together, stamps a revision and pushes a `door` event to every web client
  in both zones. Keys count when carried or worn; a lock without a key is anyone's (the world's
  rule); pickproof locks refuse picks. Payload doors carry `label` ("wooden door"),
  `has_key`, `can_pick`, `key_name`. At load, "open and locked" (102 imported doors) becomes
  unlocked and the two sides agree; doors return to their starting state with a zone reset
  (not while a player stands by). In /play: a prompt floats over the nearest door ("E Open
  the oak door", "E Unlock", "E Pick the lock", "Locked — needs a golden key", "E Close"); E
  does it (`webdoor <room> <dir> <action>`, unlock-and-open in one press); walking into a
  closed, unlocked door opens it; a right-click by a door gives the full menu (open, close,
  lock, unlock, pick, knock, bash); lock-picking shows a cast bar and moving abandons it.
  Doors appear on passage doorways too, trapdoors are hatches over stairs, locked doors show
  iron bands and a padlock.
- Verified here: `tests/test_doors.py` (offline: parsing, both sides, keys, picks, push,
  `webdoor`, load, reset; live: the oak door at 921 with and without its golden key, the push
  carrying both sides), `tests/test_webmove.py` (stairs direction), `node --test
  tests/web/*.test.mjs` (every stairs/portal room's landing, the gate, door prompts/menus) and
  `tests/web/probe_play3d.js stairs|doors` in a browser with the zone map delayed 3 s.

### Camera, right-click and auto-target (owner: "let the camera pan around the player with a right click"; "right click should give other context menus"; "if something attacks the player ensure the target is automatically selected")
- **Camera** (`world3d/orbit.js`, `input.js`, `engine.js`): right-drag turns the view around the
  hero (0.0065 rad/px) and tilts it (up = a higher view, −12°…+10° on top of the zoom's pitch,
  26°–66° overall); it stays where you leave it (owner's choice); Home, the minimap's compass
  or Settings → Camera snap back to north up. WASD follow the camera (W = away from it). The
  minimap stays north up with a wedge for where the camera looks and a compass needle. The
  wheel zooms in proportion to the scroll (trackpads glide; a sideways scroll does nothing).
  Overlays (nameplates, floating numbers, the see-through circle, prompts, the minimap) run
  after the camera each frame, so nothing lags while turning; numbers fan along the screen's
  left-right; doors and wall furniture turn see-through when they stand in the way.
- **Right-click** (press and release without dragging; Ctrl+click on a Mac): a menu for what is
  under the cursor (`hud/verbs.js`): a creature (Attack, its bar skills, Target, Consider,
  Look), a shopkeeper/trainer/quest-giver (Talk, Shop, Train, Rent, Look...), another player
  (Look, Whisper, Invite to group, Follow, Assist, Trade), a door (its actions), yourself
  (Character, Inventory, Score, Rest/Sleep/Stand, Recall, or Flee in a fight), the ground
  (Walk here).
- **Exact targets**: the client names a creature by its id (`kill #12`); the server turns that
  into the keyword each command understands (`wolf`, or `2.wolf` when another wolf comes first),
  and spells accept numbered and exact targets too. The action bar sends skills by their id
  (`holy_smite`, `order_verdict`, `execute_contract` used to reach the wrong commands) and
  renamed abilities show their cooldowns.
- **Auto-target** (`world3d/targeting.js`): the first blow, spell or wind-up aimed at you makes
  the attacker your target, unless you are busy with a live foe or picked a hostile by hand a
  moment ago; when your target dies, the creature that hit you last takes its place. Its
  nameplate turns red. Server: map payloads say which creatures fight you; a second attacker no
  longer steals your swings (CircleMUD's rule); an attacked player hears about the fight at
  once; hunting creatures show their moves.
- Verified here: `node --test tests/web/*.test.mjs` (orbit maths, W at any angle, click vs drag,
  targeting rules, menus), `tests/test_combat_v2.py` (`kill #id` hits the second of two
  spectres, the payload's `fighting`, cooldown names, the `#id` rewrite) and
  `tests/web/probe_play3d.js camera|menu|autotarget`.

### Creature models (owner: "some of the npcs have weird character models. Like a blob looks like a humanoid")
- **Why it went wrong**: the client matched the keyword list (`name`: "green") instead of what a
  creature is (`short`: "the green gelatinous blob"), and anything it couldn't place became a
  person or a glowing wisp. 78% of the world's 876 creatures were drawn as people.
- **How a body is chosen** (`world3d/looks.js`, pure, run over every creature by
  `tools/qc_bestiary.mjs`): the server now sends `short`, the start of the room line (`long`)
  and the type number (`pv`). What the short description ends with decides: a two-word creature
  ("the fire elemental", "the giant lizard"); a trade or role word makes a person ("the goat
  herder", "the vampire hunter") unless a race stands beside it ("a goblin mushroom farmer",
  "King of the Goblins") or a creature rules ("the Spider Queen"); otherwise the creature it names
  ("the giant hornet" is a hornet, not a giant); then the undead; then any creature word; then a
  person dressed for the job. A person whose room line says otherwise takes that ("the Sewer King":
  "A massive rat-man standing here."; "the Ancient Guardian": "A towering stone golem...").
- **Sizes and colours**: adjectives in front size the body (small creatures grow more and big
  ones less, so a giant rat is dog-sized and a massive minotaur still fits through a door; a baby
  dragon is not a full dragon) and colour it ("the red dragon", "a black bear", "a frost wolf");
  undead beasts are rotten or bare bone; rulers ("the queen wasp", "the alpha wolf") are bigger.
- **New bodies**: kit props come to life (`proc.js` `makeProp`: a mimic is a chest, a living
  book and a dancing sword fly, a magic carpet floats); a four-legged lizard for crocodiles,
  lizards and basilisks; golems, statues, animated armour and chess pieces are one colour all over
  (stone, bronze, iron, black or white — `flat`) and statues stand still until they fight;
  elementals, djinn and efreet are tinted spirits; pixies and sprites are tiny and hover; hags
  wear witch hats; lizard folk, merfolk, orcs, drow and sahuagin keep their trade's gear with their
  own skin.
- **People by trade**: guards and knights carry sword and shield, casters a staff or spellbook,
  innkeepers a mug, smiths an axe, thieves knives, rangers a crossbow; shopkeepers, townsfolk and
  children carry nothing (no more baker with a two-handed axe); guildmasters dress for their guild.
  The skeleton models follow what the dead were (a skeletal warrior, a lich, an ossuary archer).
  A creature type always looks the same (hashed by type, not by its id).
- **Data**: seven creatures shared their numbers with others (3100–3102, 3120–3122, 3200), so one
  of each pair never appeared; they were renumbered (3011–3016, 3203) with their resets, and the
  Pet Shop, the sewers and Stable Road get their dog, bear, wolf, Sewer King, assassin, Ancient
  Guardian and stable master back.
- Verified here: `node --test tests/web/*.test.mjs` (cases, and every creature in the world gets a
  model, weapon and prop that exist in the art, with no creature word drawn as a person),
  `node tools/qc_bestiary.mjs` (the whole list, grouped by body), `/play?demo&gallery=beasts`
  (labelled samples) and `tests/web/probe_play3d.js creatures` (live: a blob, a mimic, a statue,
  a rook, a golem, a goblin farmer, a brownie, a living book and the Sewer King in the temple).

### Skills: learn by doing, a spellbook and your own bar (owner's choices: "learn by doing"; "spellbook + your own bar")
- **Learning** (`src/mastery.py`): every class ability unlocks at a level (`UNLOCK`, from each
  roster's order, spells keeping their `level_required`, spread to 50; prestige spells 56–60).
  Reaching it grants the ability at 50%, on a level-up, at creation and at login (characters made
  before catch up: "Your training catches up with your level..."). Abilities above your level are
  refused ("You don't know execute yet — it comes at level 14"); before, most button skills only
  checked the class. Practice sessions are no longer handed out.
- **Improving**: using an ability may improve it, up to 85% (Mastered): max(2, 20 − %/5)% on a
  success (10% at 50%), half on a miss, +1–2 points; "Your kick improves! (63%)" and a "+N%"
  on its bar slot. Passives (dodge, parry, shield block, evasion, extra attacks) improve when they
  work, at a quarter of that. Crafting and gathering skills keep their own rules.
- **Proficiency matters**: a spell fizzles (100 − %)/4 % of casts (50% → 12.5%, was 50%; 85% →
  3.75%); ability damage and spell healing ×(0.85 + 0.3·%/100). Passives now work a share of
  their proficiency (dodge and parry ×0.25, shield block ×0.3, evasion ×0.2, second attack and
  dual wield ×0.6, third attack ×0.3): at 50% a dodge used to mean dodging half of all blows.
  These are balance changes to tune after playing.
- **Trainers**: past 85%, your guild's trainer teaches 5% at a time to 100%, for (% − 80) × 250
  gold (1,250 at 85%) or a leftover practice session; below 85% they send you off to use it; a
  trainer of another class (Sergeant Bron) says where your guild is. `practice` lists your
  abilities and when the rest arrive; `skills` shows "[level 14]" for those to come. The minimap
  marks your guild's trainer with a gold star. Immortals: `set <who> skill <ability> <percent>`.
- **Spellbook (K)** and **your own bar**: the spellbook lists every ability of the class (and the
  ones a talent can teach) from `/abilitybook` (fetched once per class): what it costs and
  reaches, how well you know it, "Level 14" for the ones to come. Drag an ability onto one of 16
  slots (1–8, Shift+1–8), between slots to swap, off the bar to remove it; right-click a slot for
  Use / Take off the bar. The bar is kept with the character (`webbar`, saved in the player file,
  sent back as `bar`). New abilities glow into a free slot without moving the others. Heals and
  blessings go to the player you target, else to yourself. Right-click a trainer → Master your
  abilities opens the trainer window.
- Verified here: `tests/test_mastery.py` (offline rules and maths; live: `skills`, the level
  refusal, a trainer step for 1,250 gold, Bron's directions, `/abilitybook`, the saved bar),
  `node --test tests/web/*.test.mjs` (bar logic), `tests/web/probe_play3d.js spellbook|trainer`,
  and the stairs/doors/combat suites unchanged.

### Other players and groups (owner: "can multiple players join the game? Can I see other players and group with them?")
- **Sessions are secret now.** Before, the map server trusted a name: anyone could subscribe to
  another player's live updates, read their state and mail, or move them; a `say` containing a
  hidden MAPSYNC sequence switched every listener's client to another identity. Now every login
  gets a token (`server._issue_web_token`), sent only down that player's own connection inside
  MAPSYNC; the map socket's `subscribe` and the 15 per-player endpoints answer only to it
  (`web_map._player_by_token`, `_authed`); `net.js` adds it to every `?player=` request; control
  characters are stripped from everything typed; the client's parser ignores game words inside
  someone's speech. WebSocket frames over 1 MB are refused.
- **One copy of a character.** Logging in again takes the character over in memory: the old
  session is told and closed without saving a stale copy, its web clients are revoked (they go
  back to the login screen), the world keeps one body. Leaving removes only that very object;
  a command that crashes no longer drops the connection; `goto` is for immortals.
- **Seeing each other.** Payloads carry other players' positions; each web player's position is
  relayed (≤ 5 a second) to the 3D clients that can see them, and room changes of any kind
  (walking, recall, portals, following) reach everyone in view (`web_map.relay_presence`,
  `note_room`). Other heroes run to keep up instead of sliding. Followers are no longer dragged
  out of fights, their explored rooms and maps update, and a sneaking leader's followers get
  their view too.
- **Groups.** Invites arrive as a popup (Join / Decline, 60 s), `group invite <name>` works,
  party frames sit under your own (health, mana, leader's crown, where an absent member is;
  click to target them — heals go to your target — right-click for Whisper, Follow, Make leader,
  Remove, Leave), every change is pushed to the members at once, members leave the group when
  they quit, kicking someone from a group of two no longer drops the leader, the last member is
  told when a group disbands, round-robin hands out loot in turn among those present, gold is
  split among the members present, and autoloot leaves worthwhile drops for the need/greed roll.
  A loot roll now holds its item while it runs (it used to be duplicable by looting the corpse).
- **Chat.** Tabs (All / Group / Say / Tells) and a mode chip on the input (Cmd → Say → Group →
  Tell), `reply` answers the last tell; right-click a player: invite/follow/trade say "walk
  closer" when they're in another room.
- Verified here: `tests/test_multiplayer.py` (tokens, takeover, control characters, presence
  relay, invite/accept/kick/quit events, loot-roll custody, round-robin), the existing suites with
  the token, and `tests/web/probe_play3d.js party` (two browsers: each sees the other walk, invite
  → popup → Join → party frames with the leader's crown on both).

### Every ability looks like its class (owner: "ensure animations for skills, spells, and abilities are unique and themed for every class")
- **Every ability has an event now.** Only the ~50 abilities with a range entry used to reach the
  3D client; the rest showed nothing. Every class ability (renamed commands too: `aimed_shot` is
  the truesight shot) and the extras outside the books (combo finishers, lay on hands, raising
  the dead, songs, summoned elementals) now send an `ability` event, aimed by what its book says
  (`combat_hooks._class_ability`, `event_shape`, `EXTRA_ABILITIES`); a heal with nobody named is
  for yourself; sneaking and hiding are shown only to the one doing it (`emit_private`). The
  warrior, thief, ranger and assassin level 31–60 abilities joined their class books, so they
  show in the spellbook and grow with use; self buffs such as Warpath no longer need a target,
  and bow skills (serpent sting, volley...) no longer walk you up to melee range first.
- **A recipe for every ability** (`world3d/abilityfx-table.js`, 302 lines: 285 book abilities
  and 17 extras): `'body | cast | travel | land | aura | flags'` — the clip and a body motion
  (leap, dash, blink behind the target, spin, hover, rise and slam, backstep, sidestep), what
  gathers while it winds up, what flies, how it lands and what lingers. Each class has its
  theme (`abilityfx.js THEMES`): warrior steel and ember (war crest, sparks, cracked ground),
  paladin gold and azure (sun wheel, pillars, wings, halos), cleric pearl and rose (rose window,
  feathers, petals), mage violet and cyan (rune circles, orbs, the elements), necromancer bile
  and bone (skull circles, flying skulls, drains, bones out of the ground), thief coin and smoke
  (coin rings and fountains, dice, smoke), assassin crimson and nightshade (crosshair, blinks,
  afterimages), ranger leaf and amber (leaf wreaths, arrow rain, paw prints, vines), bard magenta
  and teal (the musical staff, notes, rings of sound). Creatures' spells look like their school.
  Passive defences carry the class too (an assassin's dodge leaves an afterimage, a paladin's
  block a flash of gold); auto-attack arcs are the class's colour.
- **New effects** (`fx.js`, pictures drawn in code in `glyphs.js`): glyph particles (notes,
  skulls, coins, leaves, runes, feathers, daggers...), ground sigils and cracks, chains, rays,
  tethers, arrow and glyph rains, meteors, ground waves, cones, geysers, growths (vines, bones,
  ice, stones, bars, thorns), shields and domes, wings, halos, orbiting glyphs, afterimages,
  glows, stealth fades, screen flashes. Everything runs on the frame clock (`fx.after/every`, so
  a hit-stop slows a whole sequence alike), each quality tier has a budget, effects far from
  the view draw only their core, and particle sizes follow the screen's resolution.
- **Timing.** The key press starts the hero's clip, motion and cast at once
  (`fxdirector.prelude`); the server's event then plays what flies and lands from where the key
  press left off. Each ability's wounds and heals in the same batch rise when it reaches them
  (areas included), not when the event arrives.
- **Checks.** `tools/dump_abilitybook.py` writes every class's book to
  `tests/web/fixtures/abilitybook.json` (`test_mastery --offline` fails when it is stale);
  `tests/web/abilityfx.test.mjs`: every ability has its own line, no two in a class share a
  shape, a spell several classes know looks different in each, only real clips and effects;
  `/play?demo&gallery=abilities&cls=<class>[&only=…][&speed=0.5][&manual]` plays a class's
  whole book on training dummies, labelled; `probe_play3d.js abilityfx` uses a character's own
  abilities on a spectre in the real game. All 302 played in the gallery without an error.

### The look of Misthollow (owner: "ensure the UI is amazing… make it easy for players to fight mobs… immersive… menus visually stunning and easy to read… everything needs a theme")
- **A theme: lanterns in the mist.** The hollow is a fog-bound valley; the HUD is a traveller's
  kit carried through it (`hud/theme.css`): panels of dark mistglass bound in brass filigree
  (gilded corner pieces, a grain in the glass), window heads engraved between gilded rules,
  lacquered brass buttons, bookmark tabs, keycaps, tooltip cards on dark vellum. Fonts are part
  of the repo (`src/web_isometric/fonts`, SIL OFL): Cinzel for titles, Cinzel Decorative for the
  name, Alegreya for lore and descriptions, Alegreya Sans for everything you read at a glance.
- **Every ability has a painted icon** (`hud/icons.js`, drawn in code from the ability's own
  recipe): a gem in its element's colour or its class's two tones (blows in the main colour,
  wards and help in the second), the class's sigil faint behind, a pictogram of what it does
  (the weapon, what it throws, how it lands, what it leaves on you), a badge for how the body
  moves, a frame in the class's metal. `/play?demo&gallery=icons` shows all 315.
- **Frames with faces** (`hud/portrait.js`: one small offscreen renderer photographs a bust):
  your own frame (your class model's portrait, a wax-seal level, health and resource bars with
  numbers and a pale ghost that drains behind a wound, buffs as icons whose ring empties as they
  wear off), the target's (its portrait, name in the colour of how dangerous it is — trivial,
  easy, even, hard, deadly — level, health, distance, and its wind-up as a cast bar: "Crushing
  Blow", "Interrupted!").
- **The action bar**: painted icons, cooldowns as a sweep with the seconds, a glint when ready,
  red when out of reach, blue when you lack the mana, rich tooltip cards (rank, progress,
  description, cost, cooldown, reach, key); lantern orbs for health and the class's resource;
  a menu of brass-rimmed buttons (C I K L M O).
- **Easier fights** (`combatcues.js`): a ring under your target (red for a foe), your reach drawn
  around you while you hover an ability (green when the target is inside it), STEP OUT over
  your head with an arrow to the safe side when a foe's marked blow is about to land where you
  stand, STRIKE NOW when a foe is staggered (the bar's heaviest ready attacks glow), "press F to
  attack" when a foe is in reach, nameplates with level badges in danger colours and gold
  chevrons around your target, bosses crowned. (Fixed on the way: a creature's marked ground was
  drawn at room-local coordinates, i.e. in the wrong place outside the zone's first room.)
- **Immersion**: a title screen (drifting mist over the hollow, the lantern crest, MISTHOLLOW
  engraved in gold, "Where the mist remembers every name.", a line of the hollow's lore turning
  below), a loading ring, chapter cards when you enter a zone, the mist reddening and closing in
  when your health runs low, a "Level Up!" moment with a column of light, "You have fallen" when
  you die, speech over the heads of those who talk, passage signs in the same style, character
  creation with each class's emblem.
- **New windows**: a quest journal (L) — your quests, the chosen one's story, objectives and
  reward, Complete/Abandon, the quests offered by whoever stands beside you with Accept; a big
  map of the zone (M) — explored rooms, your guild, your quest, click a room to walk there.
- Verified here: the probe suite (spellbook, trainer, menu, autotarget, abilityfx, camera, doors,
  stairs, creatures) with the new markup; screenshots of the title screen, the HUD exploring and
  in a fight, the cues, the windows.

### Marquee class quests — the warrior's first (owner: "Each class should have a final marquee spell/skill/ability. This should be a quest for each character. It should be achievable solo or with a group. If done solo the difficulty should take a couple hours of play time. If in a group the difficulty should scale based on how many embark on the quest when the player accepts")
Owner's choices: all-new abilities (the level-60 prestige capstones stay), offered at level 45,
the endgame world plus a private trial. Shipped in two parts: the systems with the warrior's
quest end to end (this push), then the other eight classes on the same engine.
- **The ability: Unbroken Banner** (`marquee_abilities.py`): the warrior plants a war banner;
  foes within 4 m reel (bosses stagger), every foe turns on the warrior, and for five rounds the
  warrior and the allies beside them strike harder, shake off stuns and fear and mend. Its
  damage and healing follow how well it is known (it is learned at 50% and grows with use like
  any ability); its 8-minute cooldown is kept on the character. It is in the warrior's book
  from level 45, marked "earned through The Unbroken Banner"; reaching a level never teaches it.
- **The quest** (`marquee_quests.py`; the engine is `marquee.py`): `talk guildmaster` in the
  warriors' yard from level 45 offers it (a card in the 3D client, Accept / Not now; `marquee
  accept` in text). Seven stages, about two hours alone:
  1. *The Fallen Standard* — find the dying crusader on Castle Apocalypse's West Wall Path.
  2. *The Banner-Reavers* — three war-chiefs carry the banner's pieces: the Hall of War, the
     Inner Gate, the Castle Courtyard.
  3. *Embers for the Cloth* — ember shades in the Ashlands (Steam Vent Valley, the Magma
     Flows, the Scorched Wasteland); about half give an ember core; five are needed.
  4. *The Cinder Smith* — a boss on the Burning Bridge (Hammerfall, Slag Wave, adds at half health).
  5. *The Dragon's Gate* — plant the banner (`marquee plant`, or the tracker's button) and
     hold it for 30 seconds against three flights of drakelings; leaving breaks it.
  6. *The Last Bastion* — `trial enter` (or the button) at the gate: a private copy of the
     besieged bastion for the party. Three waves behind locked gates (the Outer Wall, the
     Breach twice), then Gorrund the Siegebreaker in the keep (Rampart Crush around him, Siege
     Charge at one hero, hounds on call, enraged after 8 minutes). `trial leave` steps out; left
     empty for ten minutes it closes and starts over. Logging out inside comes back at the gate.
  7. *The Last Lesson* — back to the guildmaster, who teaches Unbroken Banner.
- **Alone or together**: accepting asks the group members beside you to embark (a popup with
  Join / Decline, 30 seconds; `marquee join|decline`, `marquee go` to set out at once). Who
  joined is the party for good (`marquee_scale.py`): every foe of the quest has ×(1 + 0.8(n−1))
  health and ×(1 + 0.1(n−1)) damage, waves bring one more foe for every two extra heroes, the
  bosses act sooner; the quest's level is the owner's or the party's average if higher. Leaving
  later changes nothing. Any member's kill counts. Helpers are paid (experience, gold) when the
  trial falls; the owner learns the ability.
- **The quest's own foes** (`world/zones/zone_097.json`, vnums 9700–9707): placed when a party
  member comes near, made for the party, attacking after a breath; someone outside the party
  cannot hurt them ("belongs to Gauntlet's quest"); they go home if the party is away ten
  minutes and come back when it returns. Sized so an elite costs a lone level-45 hero about half
  their health and a boss one to two times it, most of it from blows that are telegraphed (the
  3D client marks the ground; stepping out of it now really spares you).
- **On screen**: the tracker under the minimap (stage, objectives with progress bars, ◆ where
  to go — also on the minimap and the big map — the party, and a button for the next action:
  Speak with…, Plant the banner, Enter the trial, Leave the trial), a draining bar while
  holding the gate, the stage's chapter line, the journal (L) lists it first with what it
  teaches, and `marquee` in text says the same. A `!` over the guildmaster when it is offered,
  a `?` over whoever the quest wants you to speak with.
- **Fixed on the way**: a boss's wind-up now sends the 3D client its marked ground and its
  outcome (`windup` / `resolve` / `cancel` with who stepped clear); bosses' summons, heals and
  wards no longer also hit for level × 2 damage; the kill's beneficiary was read before it was
  set in `handle_death` (legendary drops and on-kill effects); a login whose saved room is gone
  lands at the recall point; rooms can be `lit` (never dark at night).
- **Tests**: `tests/test_marquee.py` — offline: the scaling, the quest data pointing at real
  rooms and creatures, and the whole quest driven on the real world with stand-in players (each
  stage, a party of three, outsiders, the trial opened, won and closed); live: the quest on the
  server from the offer to the learned ability with the trial fought through, and two players
  embarking together (a war-chief with ×1.8 health). Admin: `marquee stage <n>` jumps a quest,
  `marquee forget` clears it and the ability.

### Marquee quests: the mage, the cleric, the paladin and the necromancer
Four more classes on the same engine (the last four — thief, ranger, bard, assassin — come next).
- **The abilities** (`marquee_abilities.py`), each sized off a hero's round of damage
  (`marquee_scale.dpr`) and how well it is known:
  - **Singularity** (mage, 8 min): every foe is dragged to one point (in 3D they slide there),
    held and crushed for two rounds, then it implodes and leaves them slowed.
  - **Seraph's Vigil** (cleric, 10 min): a seraph of light hovers over the cleric for six rounds,
    healing whoever is most wounded each round; while it stands each ally survives one killing
    blow (at 1 HP).
  - **Wings of Dawn** (paladin, 8 min): rise on wings of light and crash down — radiant damage
    within 6 m, every ally healed a quarter of their health and shielded for 15%.
  - **Lich Ascension** (necromancer, 10 min): six rounds as a lich — spells cost half, soul bolts
    split to a second foe, a quarter of what you deal drains back, death turned away once (30%).
  - Unbroken Banner's bonus is now "+25% damage to creatures" instead of a damroll affect.
  - Bosses are never pulled, held, slowed or stunned — they stagger. None of them touches players
    or pets, and none works in a duel or the arena.
- **What it rests on**: lingering parts run on combat rounds (`EFFECTS`, stepped after every
  `World.combat_tick`, only while the caster is online, alive and in the room); creatures can now
  be held (`rooted_until`: they don't move) and slowed (`slowed_until`: half the steps, about half
  the swings, a round longer to wind up); damage-taken and damage-dealt bonuses keyed by source
  so they refresh instead of stacking; a death ward that turns a killing blow aside from any
  creature, trap or hazard (never another player) without announcing a death or making a corpse.
- **The quests** (`marquee_quests.py`, creatures 9710-19, 9720-29, 9750-59, 9760-69 in
  `zone_097.json`, trials in `world/marquee/trials/`):
  - *The Heart of the Void* (mage): the planar traveller in the Plane of Chaos; three
    rift-wardens there; star-glass from arcane wraiths in the High Tower of Magic; the Echo of the
    Archmage; attune the shards in the Pentagram Chamber; the trial *The Collapsing Star* and
    Vaelith the Star-Eater.
  - *The Lost Choir* (cleric): a drowned priestess in the Sunken Temple of Nereus; three drowned
    zealots; seraph feathers from gilded harpies at the Great Pyramid; the Gilded Hierophant;
    consecrate the Pyramid's apex; *The Silent Choir* and Serathiel the Fallen.
  - *The Dawnless Chapel* (paladin): the restless ghost in the Necropolis; three eclipse knights;
    dawn embers from ember wisps in the Ashlands; the Ashen Templar; a dawn vigil in the Mountain
    Pass; *The Dawnless Chapel* and Morvane the Eclipsed.
  - *The First Phylactery* (necromancer): the grave keeper in the Necropolis; three bone colossi;
    soul shards from wailing shades in the Shadowspire; the Soulbinder; bind the soul in the
    Phylactery Chamber; *The Phylactery Vault* and Xal'thar the First Lich.
- **In 3D**: three new effects (`fx.js`) — `implode` (sparks falling in, a black core with a
  burning rim swelling over the target, then a flash), `seraph` (a larger figure of the caster
  made of light, with great wings and a halo, feathers drifting down), `lich` (grave-green glow,
  a crown of grave-fire, skulls circling, a ring of bones underfoot); icons for them (an
  imploding core, a winged seraph, a crowned skull; the banner now shows on its own icon).
- **Fixed on the way**: 104 rooms in five zones (the Plane of Chaos, Silversong, the Haunted
  Swamp, the Dwarven Mines, the Sunken Ruins) showed as "An Empty Room" — the loader now reads
  their `title`/`terrain`; "song of the ages"-style names typed with spaces run the right command
  (3- and 4-word joins) and typed abilities animate in 3D; marquee cooldowns show on the bar and in
  the spellbook; a stat buff saved during a relog came back doubled and stuck (stats are now saved
  without their buffs); hazards killed players twice (two death penalties); and only a
  session's first death made a corpse — now every death leaves a corpse with your gold and what
  you carry, and you keep what you wear (owner's call).
- **Tests**: `tests/test_marquee_abilities.py` (the four abilities and the banner by the numbers,
  the boss rule, root and slow, the ward's paths, effects ending on logout, refusal wording, the
  stat save, the corpse rule, the room names); `tests/test_marquee.py` checks every quest's data and
  plays each new quest through all seven stages offline, and live: each class's test character
  takes its quest, enters and leaves its trial, learns and uses its ability (the mage fights its
  trial through).

### Marquee quests: the thief, the ranger, the bard and the assassin — every class has one
- **The abilities**:
  - **The Heist of Ages** (thief, `heist`, 8 min; the owner chose the name because "Grand Heist"
    is already a thief talent): gone in smoke and behind every foe at once — each struck (3×DPR)
    and relieved of half the gold it carries (gold is only ever moved, never made), then the
    next three swings are certain criticals. In 3D the thief blinks from foe to foe.
  - **Heartseeker** (ranger, 6 min): a round's draw (the bow drawn in 3D, the quarry marked),
    then one arrow through every foe on its line (6×DPR the first, 4×DPR the rest; without
    positions the target and up to two others) — marked to take 20% more for four rounds and
    held two (a boss on the line only staggers). In 3D the arrow streaks through and out.
  - **Song of the Ages** (bard, 8 min): five rounds in which the allies beside the bard get one
    extra round off each of their own ability timers a round (never travel, flight, reactions,
    hunger or the marquee cooldowns; two songs don't stack), deal 20% more to creatures and heal
    20% more, while foes slow; the last note stuns them (bosses stagger).
  - **Thousand Shadows** (assassin, 8 min): for three rounds shadows strike every foe (1.2×DPR);
    the last of them finishes the weakest under 30% (capped at 8×DPR, so the huge only take a
    deep wound; a boss takes a 30% heavier last blow instead). In 3D shadow copies step out of
    the dark around each foe and cut in.
- **A new kind of stage, `visit`**: places to reach, in order or any order — the thief cases
  Thalos (City Hall, the Guild House, the north-west watchtower), the ranger follows Gloomfang's
  trail through the Great Northern Forest, the bard hears the four lost verses (a tavern in
  Thalos, the Cliff Tavern, the Refugee Sanctuary in the Plane of Chaos, Silversong's Ancient
  Grove). Each place tells its part of the story and the tracker marks the next one.
- **The quests** (creatures 9731-36, 9740-47, 9771-76, 9780-88; trials `thief`, `ranger`, `bard`,
  `assassin`):
  - *The Last Score* (thief): the fence in Thalos; case the job; tomb keys from the Great
    Pyramid's tomb wardens; rob the Keeper of Keys; crack the treasure vault of the Sunken Temple;
    *The Vault of Ages* and Auditor Mordessa.
  - *The Last Wyvern* (ranger, eight stages): the old trapper; the trail; three dire alphas;
    storm feathers from the cliff rocs of the Sunken Coast; the Roc Matriarch; wait in a blind at
    the Edge of Chaos; *The Hunting Grounds* and Gloomfang, the Last Wyvern.
  - *The Unsung Verse* (bard): the elven bard of Silversong; the four lost verses; resonant gears
    from the Clockwork Foundry's chime automatons; the Carillon Engine; play the Song at the
    Elemental Nexus; *The Hall of Unsung Kings* and the Mute King.
  - *The Contract of Mirrors* (assassin, from the same guildmaster as the thief — the class
    decides): a veiled informant in the Shadowspire; the three mirror-blades; black lotus from the
    Sunken Coast's cutthroats; the Poisoner; an ambush in the Sanctum of Light; *The Hall of a
    Thousand Mirrors* and the Faceless One.
- **In 3D**: `pierce` (an arrow and a streak of light through the line and on out), `blinks`
  (a hop behind each foe it reached, with a slash and a glint of coin), `clones` (shadow copies of
  the striker around the foe, cutting in); icons for them (an arrow through two rings, three
  hooded shapes, a double blink badge).
- **Tests**: `test_marquee_abilities.py` covers the four (gold conserved, the line pick, the mark,
  the shave and its exclusions, two songs shaving once, the execute and its boss rule);
  `test_marquee.py` plays all eight quests through offline and, live, each class's test character
  takes, enters, learns and uses (the ranger fights its trial through).
