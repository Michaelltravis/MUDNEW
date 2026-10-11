# graphics-02 / round 2 / builder: HUD and feed

Files: `src/web_isometric/platformer.html` (CSS only), `src/web_isometric/platformer/ui.js`, `src/web_isometric/platformer/ui-arpg.js`.

- HP is now the one big element of the dock: a 32px-tall, full-width (400px) bar with a heart glyph label at 14px and 18px numerals, red glow border; MP and MV became 12px bars beneath it with 11px numerals, the level/xp/gold line sits under those at 12.5px. The dock grew from 66px to 78px so the bar could get taller without stacking over the world; the remaining 642px of the 720px frame is playfield.
- On any HP drop `ui-arpg.js` toggles `hp-hit` on `#hud` for 420ms, which drives a white-flash keyframe on the bar and a brighter glow, so a hit registers on the loud element without reading the feed; the existing amber (hurt) and pulsing (low) states stay.
- Ambient prose no longer floats over the playfield: the `ambient.candidate` intercept in `ui.js` only forwards lines that name a mob present in the room (those still become speech bubbles over the mob) and routes atmosphere lines ("A chill wind...", "In the distance...") into the feed strip as an italic `.ambient` line on a dark backdrop, rate-limited to one per 9s so it is a beat, not a wall.
- HUD zones cut from six to three (title, dock, feed strip): the WASD compass cross is hidden unless the Tab drawer is open; the top-right time/weather chip is invisible until the room banner or the chip itself is hovered (or the drawer is open); PANELS/Tab is the only thing on the dock's right.
- Every HUD text now has a floor of 12px with a black text-shadow or dark pill: hotbar key numerals 13px gold bold, hotbar labels 13px white, stance chip 12px, level line 12.5px, PANELS 12px.
- Feed strip: 15px newest line on an 86%-opaque backdrop, older two lines settle to 13.5/12.5px and fade, strip lifted to sit above the taller dock; enemy hits keep the red pill. Floating chat lines got the same 13px dark-pill treatment and are capped at three.
- The Dragon-Warrior encounter caption now anchors above the feed strip (bottom: 150px) instead of at a fixed top offset over the sprites.
- Not changed: side drawer contents, target frame, wind-up/reaction strip (owned by other pieces).
