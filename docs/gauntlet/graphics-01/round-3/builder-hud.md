# graphics-01 / round 3 / builder: HUD and feed

Files: `src/web_isometric/platformer.html` (CSS block appended last), `src/web_isometric/platformer/ui.js`.

- Letterbox cut from 112px to 64px per side: `#game-root` now runs 48px in from each edge and 6px past the top and bottom, so the scene's quarter-step zoom-fit (which I cannot edit) lands on 3.0 instead of 2.75; the 24x15 room is 1152x720 (90% x 100% of 1280x720; was 1056x660). The bottom wall row sits under the translucent dock, whose gradient was softened so it stays visible.
- The compass, now inside the dock, had to keep the `visibility:hidden`-box / visible-cells trick: the canvas extends under the dock, and a visible compass box there registered as a 175px right inset and dropped the zoom to 2.5 (caught on the first capture).
- Bottom strip collapsed to one cluster: HP bar 26px tall with 15px numerals, MP/MV beside it with 12.5px numerals, the level/xp/gold line under HP at 12.5px, and the three stance chips reduced to the active one (hover the cell to see and switch the others).
- Action bar shows 5 slots (54px, 12.5px labels, gold key numerals) plus a "more" tab that opens all 10 at 46px; keys 1-0 fire every slot in either mode; the choice persists in localStorage (`misthollow_hotbar_open`). The expander is appended last so `els.hotbar.children[i]` still maps to slot i for cooldown painting. Belt shows the Q slot plus one.
- Top edge: room pill 17px with a 12px zone line is the only focal point; the clock chip is dimmed to 55% (full on hover, its ?/gear/sound buttons only appear on hover) and is hidden while `body.in-combat`, where the target frame takes the top.
- Feed: newest pill 14px, the two before it step down to 13px at 78% / 60% opacity so the ticker reads as a rhythm; long prose lines (a wind-up's full flavour text, environment events) are cut at the first clause before entering the ticker (`clogLine`), since the wind-up bar and in-world label already carry that information.
- Not changed: the italic ambient prose that floats mid-scene ("A guard patrol marches by...") is drawn by the scene, not by these files.
- Checks: `node tools/qc_platformer_rooms.js` passes; `tests/test_suite.py --smoke` could not log in against the running server (telnet login flow, unrelated to the client files touched here; see self_check).
