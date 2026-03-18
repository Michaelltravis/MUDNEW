# Changelog — 2026-03-17

## Phaser 2D Top-Down Web Client

### Overview
A full second web client was built alongside the existing Three.js isometric viewer. The new client is a Phaser 3 single-page application served at `map.frostpine.net/2d`. It provides a top-down 2D view of the world with live WebSocket integration, full MUD terminal emulation, and a polished Frostpine dark theme.

---

### Added — `src/web_isometric/client2d.html`

**Core Architecture**
- Single HTML file, no build step required
- Dual WebSocket connections: MUD telnet bridge (port 4003) + map data stream (port 4001)
- Phaser 3.87.0 via CDN; Google Fonts (Outfit 800, Plus Jakarta Sans 400/500)
- Layout: top stat bar, left map canvas (60%), right text output (40%), bottom command input

**Login Screen**
- Frostpine-themed login overlay with aurora CSS animation
- Supports both existing account login and new account creation flow
- Auto-sequences: name → password (existing) or name → Y → password → confirm (new)
- Subtitle: *"Where shadows breathe and legends are forged"*
- Server online status indicator

**Map Rendering — Phaser Scene**
- LPC terrain atlas tiles (`/sprites/terrain_atlas.png`, 32×32px) replace procedural colored rectangles
- Sector → tile frame mapping:
  - `city` → cobblestone (frame 512)
  - `forest` / `outdoor` / `field` → grass (frame 609)
  - `dungeon` → stone floor (frame 285)
  - `desert` → sand (frame 678)
  - `cave` / `rock` → dark rock (frame 264)
  - `swamp` / `water` → animated water (frames 384–387, 4fps loop)
- **Fog of war**: visited rooms at 100% opacity; unvisited at 35%
- **Current room**: teal 2px border highlight + scale pop animation on arrival (1.0 → 1.15 → 1.0, 200ms)
- **Smooth camera**: `cameras.main.pan()` tween (300ms Sine.easeInOut) on player movement instead of instant scroll
- Exit lines drawn on top of tiles between connected rooms
- Room name tooltip on mouse hover (floating glassmorphism div)
- Player marker: bright teal circle with glow
- Mob icon overlays (24×24px, top-right corner of tile) using existing sprite portraits:
  - Goblin/orc/gnoll/kobold → `mob_goblin.png`
  - Skeleton/zombie/undead/ghoul/lich/vampire → `mob_skeleton.png`
  - Demon/devil → `mob_demon.png`
  - Dragon → `mob_dragon.png`
  - Wolf/bear/lion/animal → `mob_beast.png`
  - Mindflayer/illithid → `mob_mindflayer.png`
  - Humanoid/guard/soldier/bandit → `mob_humanoid.png`
- Click-to-pathfind: click any visited room to auto-walk there
- WASD / arrow key movement (sends n/s/e/w commands)

**Zone Minimap**
- `<canvas id="minimap-canvas">` (160×120px) in top-right of map panel
- All rooms plotted as 3×3 pixel dots colored by sector
- Player position: teal 5×5 dot
- Unvisited rooms: 40% opacity
- Updates on every map_data message

**Stat Bars**
- HP (red), Mana (blue), Move (green) progress bars in top bar
- Updated from player data in each map_data push
- Text labels showing current/max values

**Combat System**
- Combat banner: "⚔️ IN COMBAT" shown when combat text detected
- Output panel color highlighting:
  - 🔴 Red: hits, damage taken/dealt
  - 🟢 Green: heals, regeneration
  - 🟡 Gold: kills, experience gained
  - 🟣 Purple: spells, mana events
  - 🔵 Blue: speech/tells
- Clickable exit directions in room descriptions (sends movement command on click)

**Sound Engine**
- Procedural Web Audio API (no external files)
- Sounds: `move` (soft tone), `combat` (sawtooth thud), `levelup` (rising triangle), `death` (descending saw)
- AudioContext initialized on first user interaction to comply with browser autoplay policy

**Inventory Sidebar**
- Toggle button (⚔️) in top bar
- Slide-in panel (260px) from right side
- Quick-send buttons: `score`, `inventory`, `equipment`
- Shows current HP/Mana/Move stats

**Mobile Layout**
- Media query at ≤768px: stacks panels vertically
- Map panel: 60% of viewport height
- Output panel: 40% of viewport height

**Command Features**
- Command history (Up/Down arrow navigation)
- Enter to send from input field
- Send button

---

### Added — `src/web_isometric/sprites/terrain_atlas.png`
- LPC terrain atlas (1024×1024, CC0 license via OpenGameArt)
- 32×32 tiles, 32×32 grid
- Source: LPC Tile Atlas by OpenGameArt.org contributors

---

### Modified — `src/web_map.py`
- Added `/2d` route handler (serves `client2d.html`)
- Added debug logging for HTTP method/path (request-level visibility)
- Note: server uses raw HTTP/1.1 parsing; Caddy reverse proxy configured with `transport http { versions 1.1 }`

---

### Infrastructure — Caddy Configuration
- `map.frostpine.net/2d` served as static file from landing directory (works around HTTP/2 framing incompatibility with custom asyncio HTTP server)
- All other `map.frostpine.net` routes proxy to `localhost:4001` with `versions 1.1` transport
- Both clients now live:
  - `https://map.frostpine.net/iso` — Three.js isometric (original)
  - `https://map.frostpine.net/2d` — Phaser top-down (new)

---

### LPC Sprites — Future Work
- LiberatedPixelCup GitHub org: `https://github.com/LiberatedPixelCup`
- Universal LPC Spritesheet Character Generator available for animated player/mob sprites
- Next step: integrate walk-cycle animations for the player marker and mob icons

---

## Session Context
- Session date: 2026-03-17 (evening)
- MUD state at commit: 60 zones, 3,008 rooms, 876 mobs, 498 armor, 286 weapons
- Active server: `map.frostpine.net` (port 4001), `mud.frostpine.net` (port 4003), telnet port 4000
