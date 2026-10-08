# Gauntlet status

**Current direction (user goal, 2026-10-07):** a modern multiplayer ARPG face on the MUD. Plan in
`/root/.claude/plans/take-a-look-at-twinkly-grove.md` (Phases A-E). Handoff for a fresh context:
read this file, `docs/art/SOURCES.md`, then the plan.

## Phase A: art pipeline and style lock (DONE, commits 53dcf5e..HEAD)
- CC0 Foozle Lucifer collection adopted (`src/web_isometric/art/`, `docs/art/SOURCES.md`).
- `lucifer.js`: players and humanoid mobs render from Lucifer sheets; every class has its own
  recoloured model (`docs/art/class-lineup.png`); LPC/DCSS remain fallbacks for animals.
- `lucifer-tiles.js`: 16 painter props replaced by Lucifer crops under the same texture keys.
- Art is served by the aiohttp bridge (:4003 `/art/`); web_map's HTTP truncated large bodies.
- Gauntlet style-01 (no builder, one blind critic vs BrowserQuest): WIN 6/7 labels; city lost
  (dark hero silhouette, unreadable townsfolk, skull-cube obstacles). Fixed after the round:
  no baked contour on Lucifer actors, +12% brightness, a warm readable townsfolk variant, and
  necropolis border/obstacle blocks replaced by Lucifer stone brick (`lucifer-tiles.js`).
  Record: `docs/gauntlet/style-01/round-1/verdicts.md`.
- Stone border/obstacle blocks also applied to castle, darkcastle, sewer, dwarvenhall, sandstone
  and drow themes; midgaard keeps its painted rooftop border (decision: the Lucifer exterior atlas
  only has a thin stone fence frame, and the painted rooftops won the atmosphere round). Decision: the Lucifer RPG UI chrome (flat 14-48px pixel frames) is NOT adopted;
  the glass HUD that won graphics-02 stays. Lucifer icons/boss bars remain available for later.

## Phase B: continuous world (IN PROGRESS)
- Step 1 done (`world-peek.js`): the camera follows the player at a notch more zoom, and the
  rooms behind each exit are pre-rendered at their offsets as dimmed flat ground (deterministic
  `generateRoomTopDown` layouts, colours from the zone theme) using the static `/atlas`, so an
  exit reveals the next space instead of black.
- Step 2 done: neighbours are painted with the real painter, deferred one per tick after the
  current room renders (flat fill shows first), tinted as distance haze; canvases are freed when
  you move on. Evidence: `docs/gauntlet/artlock/peek_forest_edge.png`.
- Step 3 done: cardinal room changes are a camera pan, not a screen slide. The camera keeps the
  old composition (the room you left is now the neighbour behind you) and eases onto the player.
  Up/down/portal travel keeps the wipe.
- Gauntlet world-01 (critic only, 3 rounds): forest still WON every round on depth/lighting; the
  walk storyboard LOST every round because a room rebuild (title swap, scene reconstruction) is
  still a visible cut next to BrowserQuest's single map. Fixed on the way: placeholder labels,
  the black band past exit-less edges, the invisible hero, the flat flash, key auto-repeat in
  captures. Records: `docs/gauntlet/world-01/round-*/verdicts.md`.
- After round 3 (unjudged): the player's world position now carries across the rebuild (no
  4-tile hop) and the room just left stays at full brightness before fading to haze; see
  `docs/gauntlet/artlock/walk_crossing_round4.png`. The remaining tell is the camera settle.
- Stitched-zone step 1 done (`world-peek.js`): every room of the zone within a 2-cell radius
  of the current one is drawn at its atlas offset (same z), nearest first, and the camera may
  roam the whole drawn extent; the room you leave stays as a fading rendered snapshot.
- world-02 round 2 (after tight follow + title crossfade): still LOSS on walk, WIN on forest.
  Two new notes: the full-screen red ambush wash reads as a cut (use an edge flash); painted
  canopies read as mush at storyboard scale (sharpen silhouettes). World runs closed (6 rounds).
- Both notes fixed (no new round): `#hit-flash` was the red wash — every hit taken fired a
  full-viewport radial at 45%; it is now edge-only (transparent to 72%, 0.32 s, `heavy` variant
  for hits ≥20). Painter canopy crowns get a lit sunward rim + dark underside arc, like rocks.
- Stitched zone step 3 (built, no round spent): neighbours are now pre-rendered at FULL fidelity,
  not just ground. `scene.prerenderStatic(layout)` runs the wall/decoration/furniture passes into
  throwaway layers and bakes one RenderTexture per room (`_staticRTs`); `world-peek` parks each
  at its atlas offset in the deferred queue (after that room's ground paint) and prunes the ones
  out of range. The room you leave is snapshotted into the same cache (walls, props AND its mobs)
  instead of a fading ghost, so nothing vanishes behind you. `/atlas` now carries `description`
  + `flags`, and the peek passes `zone`, so the peeked layout is byte-identical to the live one
  (before, zone-less layouts drew different props and the crossing swapped them). Adjacent rooms
  are untinted (haze only on the outer ring): the brightness seam at the border is gone.
  Evidence: `docs/gauntlet/scratch/round-3/mh/walk.png` (local only) — trees visible beyond the
  gap before crossing, the old room fully furnished beside the new one, no flash.
- Stitched zone step 4: creatures in neighbouring rooms. `map_data.rooms[]` already carries every
  explored room's mobs/players, so `scene.syncFarEntities()` stands them on that room's spawn
  slots at the offset world-peek parked it at (Lucifer actor idling in a hashed facing, DCSS
  fallback, contact shadow; display-only — no physics/labels/targeting). Re-synced on every
  payload and on every peek render; the old-room snapshot no longer bakes mobs (they are live).
  Evidence: `scratch/round-4/mh/{walk,city}.png` (local) — a creature beyond the gap before the
  crossing; two guards in the next street of Midgaard.
  Still not stitched: physics (one physics world per room; a crossing is a camera pan + rebuild
  under a continuous camera). That is the remaining item of the NEXT below.
- **world-03 (critic only): round 1 LOSS on walk (title-card swap, combat overlays), round 2 WIN on
  walk AND forest** (`docs/gauntlet/world-03/round-2/verdicts.md`). The seven-round walk loss
  turned out to be a client bug: the "wedged" exit breaker fired on any key held 1.5 s and
  teleported the hero a room ahead (fixed: requires no movement). The capture tool compounded
  it (a 3–4 s WebGL screenshot made a "2.7 s" storyboard film ~20 s of play; world storyboards
  are now in-page renderer snapshots at true game time, fight storyboards freeze the loop per
  frame; reference re-filmed with real stamps). Open notes from the win: un-painted neighbour
  flat fill can reach the screen (paint ahead first), haze step at the outer ring (feather),
  canopy crispness, vignette one notch lighter. Confidence low; see the caveats in the record.
  All four notes acted on without a round: peek queue pumps at 40 ms (nearest first), outer-ring
  haze is 0xe2e5ec / 0.10 instead of 0xc4c8d4 / 0.22, crowns get trunks on their open south side
  and stronger rims, outdoor vignette 0.28 → 0.22 (`scratch/round-5` local evidence).
- NEXT (architectural, the biggest remaining item): the full stitched-zone renderer. Build the whole
  zone as one tilemap from `/atlas` coordinates (each room = its deterministic layout placed at
  x*W, y*H; corridors drawn for non-adjacent exits), paint per room into one big canvas on idle,
  keep one physics world with openings between rooms, and derive the room change from the
  player's world position (send the move when they cross; the HUD title follows the server).
  No rebuild, no cut. Estimated at several sessions; everything built here (peek, painter reuse,
  atlas, roles, actors) carries over.
## Phase D: multiplayer presence (BASELINE VERIFIED)
- Two live clients (`tools/gauntlet/duo.js`, characters Gauntlet/Gauntletb) share a room, follow,
  group, and fight together; party frames (top centre) show both members' live HP. Evidence:
  `docs/gauntlet/multiplayer/duo_A_party_fight.png`.
- Step 2 done: combat rounds are pushed to everyone in the room (each from their own side), so
  a party member's mob wind-ups and staggers show for allies; other players carry
  `in_combat` / `fighting` / `fighting_you` and get a gold crossed-swords badge while fighting
  (red stays reserved for "attacking you"); allies animate their attacks.
  Evidence: `docs/gauntlet/multiplayer/duo_A_ally_badge.png`.
- Step 3 done: presence chip under the zone caption ("N with you · M nearby · K online"); player
  arrivals, departures, teleports, logins and logouts now refresh every graphical client in the
  affected rooms at once (`player_move` events), with an "X arrives/leaves" feed line.
- World-event banners already exist (`ui.js` eventAlert detects boss/invasion/treasure/double-XP lines).
- Step 4 done: need/greed/pass loot rolls. New groups default to `loot_mode = roll`; worthwhile drops
  (uncommon+ rarity, weapons/armor worth 50+, anything 200+) from a group kill go to a 20 s roll
  among members in the room; `roll need|greed|pass` or the client popup; winner takes the item
  from the corpse. Verified end to end with two clients (`tools/gauntlet/duo.js` with POLL).
- Art decisions (no CC0 beast or extra-hero sheets exist): DCSS creature art stays for animals;
  recoloured heroes stay until a commissioned sheet. See docs/art/SOURCES.md.
- Next: loot history panel; ally telegraph rings when a mob fights a party member beside you.

## Phase C: ARPG controls and readability (BASELINE EXISTS)
- Click-to-move, hit-stop, screen shake, floor telegraphs, reaction prompts and damage numbers
  already exist from the gauntlet runs; the playability gauntlet judged them above the bar.
- Reaction prompt now floats above the hero (ui.js listens to `player.screen`); perfect strikes already hit-stop (`freezeFrame`).
- Next: a gauntlet feel round with the new art, radial layout for the prompt chips.

## Phase E: onboarding (STEP 1 DONE)
- Progressive hotbar: 3 slots (attack, flee, first class ability) through level 5, 5 slots to
  level 10, full bar after; unlock flash on tier change (`ui.js` autofillBar).
- Class-specific welcome card: class fantasy line, the three starting buttons, and how to group.
  Evidence: `docs/gauntlet/multiplayer/newbie_welcome.png`.
- The Guide (built): a WoW-style objective tracker (`#guide`, top-left) for the quest you are on —
  tutorial quests first, then any active quest. It turns the current objective into one hint and
  one button from the same `/quests` data the journal uses: visit → "Head north ↑ · 3 rooms" +
  Walk there (minimap auto-walk); command → the command as a button; talk → "Talk to X" when
  X is in the room, else the room X is in with a Walk there if a path is known; kill → the F
  hint. Refreshes on room change, on quest lines in the feed (`quest.update` from the parser),
  on combat end, level-up, and a 15 s poll. Verified end to end with the tutorial chain
  (`scratch/guide/*.png`, local). Found and fixed on the way: `prerenderStatic` leaked root-level
  glows/washes over the live room (now sweeps every display-list newcomer).
- Next: class picker with ability preview.

Credit discipline: one piece, one round.

**Run:** playability-02 — **round 1 of 2 done**. Working branch `claude/nice-johnson-slpinu`.
**Reference:** BrowserQuest, local clone `.gauntlet-ref/browserquest` (gitignored; rebuild with `node tools/gauntlet/capture-ref.js --setup`).
**Pieces:** feel (ab; labels: fight, combat; files `src/web_isometric/platformer/{scene-topdown,fx-abilities,ui,ui-arpg}.js`). Pacing closed in playability-01 (won round 1, `cf2a4c4`).
Win rules: ab = overall pick -> mh AND >1/2 labels -> mh; key = pass === true.
**Round records:** `docs/gauntlet/playability-02/round-<n>/` (`verdicts.md`, `builder-*.md`, `critic-*.json`, `fight/*.txt|json`; `mh/` and `pairs/` gitignored). Key seed round 1 `2026-09-03T20:10:00Z:1`.
Capture fixes since playability-01 (`3c9d92e`, `bc8d845`): zreset before scripted fights, 1 s storyboard frames — the critic now films a live fight.
Previous runs: graphics-01/02 complete (`d648ea1`); playability-01 complete (pacing won; feel lost 3/3 against a dead-keeper capture, code carried forward into this run).

## History
| Run | Round | feel |
|---|---|---|
| playability-02 | 1 | **WIN** (2/2: fight B -> mh, combat B -> mh; overall mh; confidence high) — code + records `cf05cb3` |

## Open pieces
- none. feel won round 1; its round-2 slot is unused. The critic's three fixes describe the reference (A), not Misthollow, so there is nothing to carry into a round 2.

## Blockers / notes for the human brake
- Fight stats: round-1 `fight/summary.json` is consistent this time (keeper 7/7 rounds, bear 11/11 decision rounds; 0% rounds without decision). The earlier decision_rounds > rounds bug did not reproduce.
- Builder caveat still stands: `python3 tests/test_suite.py --smoke` fails at login for account characters (known); `node tools/qc_platformer_rooms.js` passes.
- Pacing minor (carried): boss crits deal the same as non-crit hits under the 10% max-HP swing cap; Q6 single-low-HP-warning rule still untested.
- `logs/tests.log` is modified from builder runs; not committed.

Next command: human decision — close playability-02 (all pieces won; round 2 not needed) or `gauntlet playability-02 round 2 (piece: feel)` only if a new label/bar is wanted.
