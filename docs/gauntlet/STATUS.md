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
- Decision: cross-room physics stays client-side as a camera pan (the server owns rooms and
  movement; exit gaps already send the move). A gauntlet "world" round is the remaining check.
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
- Next: first-10-minutes scripted prompts on the tutorial chain; class picker with ability preview.

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
