# graphics-01 — round 2 verdicts (decoded)

Key: `docs/gauntlet/graphics-01/round-2/pairs/key.json` (seed `2026-09-02T23:35:00Z:2`, reference BrowserQuest). A piece wins when its overall pick decodes to `mh`. Only hud ran this round (atmosphere and actors closed in round 1).

## hud — **LOSS** (overall pick B → ref on city and dungeon; 1/3 labels)

| label | pick | decoded |
|---|---|---|
| city | B | ref |
| combat | B | mh |
| dungeon | B | ref |

Overall pick B decodes to `ref` for city and dungeon and to `mh` for combat; the critic itself notes B-in-combat is a different game from B-in-city/dungeon and that the overall winner is the bright full-viewport game (the reference). Confidence: low.

Reasons (verbatim):
1. city/dungeon: A's world is letterboxed with black margins on both sides and a two-row bottom strip of ~13 action buttons (attack/flee/bash/cleave/kick/exec...) at roughly 7px text plus three color-coded HP/MP/MV bars; B's world fills the full viewport with a single red HP bar bottom-left and one readable line of text ('Welcome to BrowserQuest!', '1 player').
2. city/dungeon: A has four competing chrome elements (room banner top-center, clock/date pill top-right, compass bottom-right, PANELS/Tab button) around a tiny 'Lv 30 Warrior - 0% xp - 2075 gold' status line; B has one focal point, the player with the highlighted target square, and nothing else to read.
3. combat: B (the dark HUD) shows a target frame 'GRAVE KEEPER Lv 35 DANGEROUS 758/768' with an 'IN COMBAT' badge, floating '34' damage numbers and a three-line pill feed ('grave keeper hit YOU for 34', 'grave keeper dodges'); A (the bright game) shows no enemy health at all, a barely visible '6' over a rat, and only the player HP bar as fight-state signal. NOTE: B in combat is a different game from B in city/dungeon; the overall winner is the bright full-viewport game (B in city/dungeon, A in combat), fixes target the dark letterboxed game.

Fixes (verbatim):
- Kill the black letterbox margins: scale the game canvas to fill the viewport width so the world, not empty black, owns the screen as in the bright game's city/dungeon. (`src/web_isometric/platformer.html`)
- Collapse the two-row bottom strip: merge HP/MP/MV into one compact cluster with >=12px numerals and hide the 13 tiny action buttons behind hotkeys or a single expandable bar so the bottom edge reads at a glance. (`src/web_isometric/platformer/ui.js`)
- Reduce competing top chrome: fold the clock/date pill and PANELS button into the room banner or fade them after a few seconds so the room name and (in combat) the target frame are the only focal points; keep the target frame and pill feed, which already win combat. (`src/web_isometric/platformer/ui-arpg.js`)
