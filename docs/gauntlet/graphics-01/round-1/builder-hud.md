# graphics-01 / round 1 — builder: HUD and feed

Files: `src/web_isometric/platformer.html` (one appended CSS block, last in the cascade), `src/web_isometric/platformer/ui.js` (feed writer only). `ui-arpg.js` untouched.

- Room prose card moved out of the play area: it was a 560px italic block over the top half of the room; it now sits in the empty left band (top 64px, 300px wide, scrollable, non-italic, cyan left rule) so the world is never covered on arrival. BrowserQuest's biggest edge is that nothing persistent overlaps the map.
- Vitals made glanceable: HP bar is now 20px with a 12px bold mono readout, MP/MV drop to 13px as secondary; the readouts were previously clipped (absolute `<b>` with top/bottom auto sat under the 100%-tall fill), so "207 / 207" is visible for the first time. The duplicated name line in the HUD is hidden because the crest already carries name / class / level.
- Combat stack under the target frame: "IN COMBAT" chip -> target frame (16px HP bar, bigger name) -> enemy wind-up bar -> Q/E/X reaction strip, all stacked at top-center where the eye already is. The wind-up and reaction strip previously floated over the message feed and covered its lines.
- Feed rhythm in `clogLine`: each server combat round opens a "beat" (hairline + gap) so an exchange reads as a group; identical consecutive lines fold into one line with a xN counter instead of stacking; combat state resets the fold.
- Feed typography: 12px lines, 2px colour rule on the left edge per kind (jade = you, ember = them, cyan = defence/chat, dim = miss), damage numbers in mono and larger, incoming hits get a faint red wash, timestamps at 45% opacity until the feed is hovered. Sticky header made opaque; the first scrolled-off line used to bleed through it.
- Legibility at 720p: action-bar labels 8px -> 10px, zone line 10 -> 10.5px and brighter, room name 20px; the class sigil shrinks from 104 to 92px so it competes less with the HP bar.
- Transient overlays moved off the room centre: the "draws near" caption and cast bar now sit just above the feed instead of under the target frame.
- Not changed: contacts, sector map, quest tracker, hotbar layout, world rendering. Verified with scratch captures (city, combat, dungeon at 1280x720) that no panel overlaps the room canvas except the combat stack at its top edge.
