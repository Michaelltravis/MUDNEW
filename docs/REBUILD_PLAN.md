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

## Phase 2 — movement
- Crossing a room edge is instant on the client (optimistic move, no lock); the server confirms
  in the background and only a refusal snaps you back.
- Wide openings: where two rooms connect, the shared wall is open across a third of its length.
- Faster walk; click-to-move with pathing across rooms (the minimap auto-walk, in the world).
- Done when: holding a direction through five rooms never stops the hero.

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
