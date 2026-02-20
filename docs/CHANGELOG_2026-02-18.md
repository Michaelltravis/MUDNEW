# Misthollow Changelog — Wednesday, February 18, 2026

## Summary
Major isometric client day. Comprehensive work on the web-based 3D iso client (`/iso`),
player restoration, world map improvements, and infrastructure fixes.

---

## 🗺️ Isometric Client — Sprite System Overhaul

### Problem
Every mob with a name not in the tiny 40-entry map fell back to `wolf.png`. Sewer bat
and wererat were visually identical. Sprite coverage was ~10% of actual mob types.

### Fix
- Downloaded **66 new DCSS sprites** (CC0 license) from the Dungeon Crawl Stone Soup repo
  - Total: **130 sprites** across 17 subdirectories
  - New categories: bats, rats, snakes, scorpions, crocs, hounds, hogs, ravens, wargs,
    manticores, hippogriffs, minotaurs, harpies, sphinxes, tengu, aquatics (kraken/eel/
    jellyfish/octopus), amorphous (slime/jelly), wraith variants, golems, constructs
- Expanded **DCSS_NAME_MAP from ~40 → 330 entries** covering every mob type in the game
  - `sewer bat` → `animals/bat.png` ✅
  - `wererat` → `animals/rat.png` ✅
  - All beast/undead/demon/elemental/humanoid/aquatic types mapped correctly

---

## 💀 Dead Mob State

When a mob is killed, the combat portrait now reflects it:
- Portrait goes **grayscale** with **💀 skull overlay**
- HP bar collapses to 0, label changes to "DEAD"
- Panel **auto-hides after 3 seconds**
- Detection: parses "The [name] is dead!" from combat text via regex → `markMobDead()`
- Also triggers if server sends `hp: 0` in map data
- Dead set **clears on room change** so stale state doesn't carry over

---

## 👥 Multi-Mob Dynamic Sizing

Multiple mobs in the same room now display sensibly:
- 1–5 mobs: individual dots in a circle, radius **shrinks as count increases**
  - 1–2 mobs: 14px dots
  - 3–4: 12px
  - 5–6: 10px
  - 7+: 8px
- **6+ mobs**: shows 5 dots + red **"+N" count badge** (canvas sprite)
- Circle radius tightens proportionally so dots don't overlap tile edges

---

## 📋 Character Sheet Panel

New toggleable floating panel showing full character info.

**Open:** Click 📋 button (zoom controls area) or press **C**

**4 tabs:**
- **Stats** — Player class portrait, HP/Mana/Move bars, full stat grid (STR/DEX/CON/INT/
  WIS/CHA), hitroll/damroll/AC/gold/exp/level, title
- **Equipment** — Each worn slot with item name and affect values
- **Inventory** — Item list with types
- **Skills** — Skills (% mastery) and Talents (★ rank) in compact two-column grid

**UI:**
- Draggable by header bar (same system as text panel)
- 320px wide, up to 600px tall, scrollable content
- Font size 12–16px (readable)
- Dark themed matching existing UI
- Updates live on every map tick

**Server changes (`map_system.py`):**
Extended `build_map_payload()` player object to include:
`hp, max_hp, mana, max_mana, move, max_move, level, char_class, race, title,
str, int, wis, dex, con, cha, hitroll, damroll, armor_class, gold, exp,
equipment {slot→{name,affects}}, inventory [{name,item_type}], skills {}, talents {}`

---

## 🗺️ Map View System

### Zone / Full / World Toggle Bar
New button bar at top-center (appears after login):

| Button | Behavior |
|--------|----------|
| **Zone** (default) | 3D iso shows only current zone — clean, readable |
| **Full** | All explored rooms (old behavior) |
| **World** (M key) | Opens 2D world map overlay |

Zone filter is client-side — `visibleRooms = data.rooms.filter(r => r.zone === currentPlayerZone)`.
Minimap also respects the filter. Moving to a new room auto-updates the zone view.

---

## 🌍 2D World Map

Canvas overlay (900×620px) showing all 53 zones.

**Access:** Click "World" button or press **M**. Press **Esc** to close.

### First attempt (force-directed) — failed
Force simulation resulted in nodes piling up in corners, long crossing lines, unreadable
labels. Scrapped entirely.

### Replacement: Hand-crafted geographical layout
Fixed `ZONE_POS` coordinates reflecting actual MUD world geography:
- **Center**: Midgaard + immediate areas (Newbie Zone, Housing District, God Simplex)
- **South**: South Midgaard → Redferne's → River Island chain
- **SW**: Miden'Nir cluster (Three of Swords, Welmar's Castle, Dwarven Kingdom/Mines)
- **West**: Haon-Dor forests → Orc Enclave / Arachnos → Silversong Village
- **North**: Northern Forest → Frostspire (far), Northern Wilderness → Goblin Warrens
- **NE chain**: E.Highlands → Haunted Monastery → Shadowspire → Sunken Coast →
  Sunken Temple → Ashlands → Clockwork Foundry
- **Center-north**: High Tower → Mines of Moria → Rand's Tower (Haunted Swamp beside)
- **East spine**: Tunnel of Sticks → Castle Apocalypse (rightmost, clearly endgame)
- **East hub**: New Thalos → Eastern Desert → Drow City/Thalos/Pyramid/Rome
- **Underground** (below Midgaard): Sewers L1→L2→Maze→Mindflayer's Lair, Necropolis

**Visual features:**
- Color-coded by level range: 🟢 1-10 · 🔵 11-20 · 🟡 21-35 · 🟠 36-50 · 🔴 51-60
- Node size scales with room count (bigger = more rooms)
- **Current zone glows gold**
- Hover → tooltip (name, zone ID, room count, level range)
- **Click any zone** → closes world map, filters 3D view to that zone
- Labels: text shadow for legibility; labels near bottom edge flip above the node
- **Blood Pit Arena** shown with dashed border + "Teleport access only" tooltip

### Zone Connectivity Check
- **52 of 53 zones** fully reachable from Midgaard (undirected graph)
- **Zone 250 (Blood Pit Arena)**: intentionally isolated — confirmed no exits in zone file,
  accessed via in-game teleport command only
- Fixed several one-way connection asymmetries in map display data (Midgaard now correctly
  lists Northern Forest, Sunken Ruins, High Tower as neighbors)

---

## ➡️ Exit Arrow Indicators

### Problem
Room connectors were dark blue-gray lines (`0x444466`, 60% opacity) — invisible against
the dark tile grid. Players couldn't see available exits.

### Fix
- **Connector lines**: now bright cyan (`0x55eeff`, 75% opacity) — clearly visible
- **Directional arrow sprites** on every tile edge pointing toward exits:
  - 🟡 **Gold triangles** (42% scale) on **current room's** exits — instant readability
  - 🔵 **Cyan triangles** (30% scale) on all other explored room exits
  - ⬜ **Grey triangles** (45% opacity) on frontier/unexplored exits — "something's there"
- **Up/Down exits**: colored circle badges — green **U** (up) / orange **D** (down)
  - Unicode ▲▼ didn't render on HTML canvas → replaced with letter badges in circles
  - Placed floating above tile at correct Y height with `depthTest: false, renderOrder: 999`
- Frontier exits (leading to unexplored/different-zone rooms) still show arrows so players
  know exits exist even without having explored them

---

## ⚔️ Avikan — Player Restoration

### What happened
Avikan died in-game and lost all equipment.

### Initial restore failure
Edited the JSON player file while Avikan was still logged in. Server auto-saves player
state periodically — overwrote the file with empty equipment. **Lesson: always wait for
player to be fully logged out before editing their file.**

### Final gear (17 slots)
Assassin-optimized kit. Both weapons are pierce/dagger type (backstab eligible):

| Slot | Item | Key Bonuses |
|------|------|-------------|
| wield | shadow dagger | hitroll+4, damroll+3, dex+1 |
| hold | grave-edge stiletto | dex+4, hitroll+2 |
| head | hood of the unblinking | sneak+5, no_track+1 |
| body | death's black armor | str+3, con+3 |
| about | prismatic veil | sneak+6, no_track+1 |
| hands | shadowgrip wraps | sneak+10, backstab+10 |
| waist | girdle of hunger | damroll+4, sneak+6 |
| feet | boots of the bronze whisper | sneak+7 |
| neck1 | hunger chain | sneak+8, track+10 |
| neck2 | apocalyptic crest | hitroll+4, damroll+4 |
| finger1 | wraith-hunter band | dex+3, hitroll+1 |
| finger2 | death's ring | backstab+12, no_track+1 |
| wrist1 | eclipse band | backstab+15, no_track+1 |
| wrist2 | tunnel-guard bracer | dex+2 |
| arms | warlord's vambrace | damroll+4, bash+10 |
| back | verdant shroud | sneak+7 |
| shoulders | pauldron of war | str+2, bash+8 |

**Total gear bonuses**: +49 sneak, +37 backstab, +20 damroll, +14 hitroll, +6 dex, +4 no_track

### Food loadout (inventory)
- 3× Ambrosia (food value 100 — best in game)
- 3× Phoenix Egg Omelette (food value 50)
- 3× Giant's Stew (food value 60)
- 5× Battle Ration (food value 40)
- 1× Canteen (10 drinks of water)

---

## 🗑️ Deprecated Skills Purged — Avikan

18 deprecated skills removed from Avikan's skill list:

**Removed (old system):** `assassinate`, `blur`, `garrote`, `mark_target`, `slip`,
`shadowstrike`, `fan_of_knives`, `rupture`, `shadow_blades_master`, `vendetta_assassin`,
`death_mark`, `cold_blood`, `marked_for_death`, `silence_strike`, `death_from_above`,
`cloak_of_shadows`, `shadow_blink`, `shadow_blade`

**Valid assassin skills (15):** `backstab`, `mark`, `expose`, `vital`, `execute_contract`,
`feint`, `evasion`, `vanish`, `shadow_step`, `sneak`, `hide`, `dual_wield`,
`second_attack`, `dodge`, `poison`

**Valid talents (21):** All correct per `ASSASSIN_LETHALITY`, `ASSASSIN_POISON`,
`ASSASSIN_SHADOW` trees in `talents.py`

---

## 🔧 Infrastructure Fixes

### Cron Jobs (earlier today)
All daily cron jobs were broken due to `anthropic/claude-sonnet-4-6` being specified
as model — that model is unavailable on current token.
- Removed model override from: morning briefing, research report, crypto prices
- Fixed delivery target for bug-check: `user:642117186193981456` (was missing `user:` prefix)
- Deleted: "Check Sonnet 4.6 availability" cron (was failing 5+ times daily)
- Sent: Manual Wednesday morning briefing (8 AM cron had missed it)

### Diagonal Exits Purged (earlier today)
- Found 12 illegal diagonal exits (NE/NW/SE/SW) across zones 066, 067, 068, 069, 180
- All converted to nearest cardinal direction
- Scanned all 54 zones / 2,809 rooms / 6,174 exits — confirmed clean

### OpenClaw Updated
`2026.2.15` → `2026.2.17`

---

## 📁 Files Modified Today

| File | Changes |
|------|---------|
| `src/web_isometric/index.html` | Sprites, dead state, multi-mob, char sheet, map views, world map, exit arrows |
| `src/map_system.py` | Player data in map payload (stats/equip/inventory/skills/talents) |
| `src/web_isometric/sprites/dcss/` | 66 new sprites added across 17 subdirs |
| `lib/players/Avikan.json` | Equipment, inventory, skills, explored_rooms restored |
| `world/zones/zone_066.json` | Diagonal exits fixed |
| `world/zones/zone_067.json` | Diagonal exits fixed |
| `world/zones/zone_068.json` | Diagonal exits fixed |
| `world/zones/zone_069.json` | Diagonal exits fixed |
| `world/zones/zone_180.json` | Diagonal exits fixed |

---

## 🚀 Server Status
Running on `72.35.132.11` ports 4000 (telnet) / 4001 (web+map) / 4003 (web client)
Web client: `http://72.35.132.11:4001/iso`

---

*Changelog written by Ram 🐏 — Feb 18, 2026 @ 2:52 PM PST*

---
---

# Evening Session — Feb 18, 2026 (5 PM – 10 PM PST)

## Summary
Comprehensive NPC/player artwork overhaul + three major isometric UX improvements.

---

## 🎨 NPC Sprite System — Phase 2

### DCSS Sprite Gap Fill (+23 sprites, 149 → 172 total)

Audited all 536 unique mob names from zone files against the DCSS name map.
Identified and downloaded missing sprite categories from the DCSS GitHub repo (CC0):

| New Sprite | Maps To |
|---|---|
| `dragons/hydra.png` | cryohydra, lernaean hydra, hydra |
| `fungi_plants/treant.png` | ancient treant, treant, tree creatures |
| `fungi_plants/wandering_mushroom.png` | myconoid, mushroom, fungus |
| `fungi_plants/toadstool.png` | toadstool |
| `eyes/great_orb_of_eyes.png` | beholder (upgraded from tentacled_monstrosity) |
| `eyes/eye_of_devastation.png` | eye creature variants |
| `animals/broodmother.png` | broodmother, web spinner |
| `animals/quokka.png` | rabbit, squirrel, chipmunk, mongoose (later replaced by custom) |
| `animals/inugami.png` | fox (later replaced by custom) |
| `animals/elephant.png` | elephant |
| `animals/hell_hound.png` | hell hound |
| `animals/bullfrog.png` | frog, toad, duck, duckling (later replaced by custom) |
| `animals/butterfly.png` | butterfly, swan (later replaced by custom) |
| `animals/dream_sheep.png` | sheep/goat backup |
| `aberrations/ugly_thing.png` | otyugh, mutants, grotesque |
| `aberrations/abomination_large.png` | abomination, grotesque |
| `demihumanoids/jorogumo.png` | drider, yochlol (spider-woman hybrid) |
| `demihumanoids/entropy_weaver.png` | spider-hybrid backup |
| `demihumanoids/satyr.png` | satyr |
| `boss/arachne.png` | Spider Queen, the Spider Queen (boss) |
| `boss/ignacio.png` | initial Kirgan placeholder (later replaced) |
| `boss/khufu.png` | pharaoh, Ramses, mummy pharaoh boss |

### Code Improvements

**`DCSS_EXACT_NAME_MAP`** — New exact-name lookup added *before* partial keyword matching.
Prevents single-word boss names bleeding into unrelated mobs:
- `death` → horseman portrait (not contaminating "death knight")
- `war` → horseman portrait (not contaminating "warg")
- Named dragons (`Aurexus`, `Scorathax`, etc.) all individually mapped

**Boss type fallback fixed** — Was referencing `golden_dragon_boss.png` (didn't exist).
Now correctly falls back to `dragon_boss.png`.

**Beholder upgraded** — `beholder` now maps to `eyes/great_orb_of_eyes.png` instead of
`tentacled_monstrosity.png`.

---

## 🖼️ Custom AI-Generated Boss Portraits (7 sprites)

All generated via Nano Banana Pro (Gemini 3 Pro Image), saved to `sprites/dcss/boss/`.
Dark fantasy portrait style, no text/labels, single figure centered.

| File | Character | Description |
|---|---|---|
| `horseman_death.png` | Death | Skeletal grim reaper, silver scythe, violet flame eyes |
| `horseman_war.png` | War | Blood-red spiked demon knight, flaming sword |
| `horseman_famine.png` | Famine | Skeletal withered figure with balance scales |
| `horseman_pestilence.png` | Pestilence | Moss-covered plague lord, skull staff, toxic miasma |
| `kirgan.png` | Kirgan the Destroyer | Colossal demon warlord, obsidian plate, lava-vein cracks |
| `shadow_lord.png` | Shadow Lord Malachar | Living-shadow nobleman, void orb, obsidian crown |
| `goblin_king.png` | Goblin King Grizznak | Scarred goblin king on throne, iron crown, spiked club |

Several required multiple regenerations to eliminate baked-in text labels (Gemini
tendency). Final versions confirmed text-free.

### Wiring
All 7 mapped in `DCSS_EXACT_NAME_MAP` so exact mob names hit the right portrait:
- `'death'` → `horseman_death.png`
- `'war'` → `horseman_war.png`
- `'famine'` → `horseman_famine.png`
- `'pestilence'` → `horseman_pestilence.png`
- `'kirgan the destroyer'` → `kirgan.png`
- `'shadow lord malachar'` → `shadow_lord.png`
- `'goblin king grizznak'` → `goblin_king.png`
- `'grizznak'` → `goblin_king.png`

---

## 🐾 Custom AI-Generated Animal Sprites (12 sprites)

Replaced wrong DCSS fallbacks (catoblepas for lions, warg for wolverines, etc.)
with proper custom portraits. All saved to `sprites/dcss/animals/`.

| File | Replaces | Covers |
|---|---|---|
| `lion.png` | catoblepas | lion, bobcat, mountain lion, cat, kitten |
| `tiger.png` | catoblepas | tiger, panther |
| `wolverine.png` | warg | wolverine |
| `badger.png` | warg | badger, honey badger |
| `fox.png` | inugami | fox, inugami |
| `rabbit.png` | quokka | rabbit, quokka, ferret, otter |
| `squirrel.png` | quokka | squirrel, chipmunk, mongoose |
| `deer.png` | catoblepas | deer, stag, fawn |
| `swan.png` | butterfly | swan |
| `duck.png` | bullfrog | duck, duckling |
| `horse.png` | catoblepas | horse, pegasus |
| `chimera.png` | catoblepas | chimera |

Fox required two regenerations — first attempt had runic text on a harness.

---

## 🧝 Player Portrait System — Gear Tier Portraits (36 sprites)

New system: character sheet portrait changes based on equipped body armor.

### Tier Detection Logic (`getGearTier()`)
Reads `p.equipment.body.name` and keyword-matches to determine visual tier:

| Tier | Keywords | Visual |
|---|---|---|
| `naked` | no body slot equipped | Starting gear, class identity clear |
| `leather` | leather, hide, studded, robe, vestment, shirt, tunic, jacket... | Light armor |
| `chain` | chain, chainmail, ring mail, scale, hauberk, brigandine... | Medium armor |
| `plate` | plate, platemail, breastplate, mithril, dragonscale, adamant... | Heavy/epic armor |

Fallback: if keywords don't match, uses `body.armor` value (≥3 = chain, else leather).

### Portrait Files
36 custom AI portraits saved to `sprites/players/{class}_{tier}.png`:

**Classes:** warrior, mage, cleric, thief, assassin, ranger, bard, necromancer, paladin

Each class has a distinct visual progression — e.g. warrior:
- `warrior_naked.png` — torn shirt, fists raised, no armor
- `warrior_leather.png` — studded leather vest, sword
- `warrior_chain.png` — chain hauberk, battle-worn, scarred vet
- `warrior_plate.png` — blackened full plate, enormous sword, lava-crack trim

Caster classes show robe/regalia progression rather than armor. Thief/assassin stay
in dark leather aesthetics even at plate tier (class-appropriate).

### Integration
`renderCharacterSheet()` now calls `getPlayerPortrait(p)` which returns
`/sprites/players/${cls}_${tier}.png`. Falls back to old `/${cls}.png` sprite
if the tier portrait fails to load. Sprite server already handles subdirectory
paths via `path.replace('/sprites/', '')`.

---

## 🗺️ Isometric Map UX — Three Major Improvements

### 1. Tile Theming by Sector Type

**Before:** All tiles used `MeshLambertMaterial` with flat solid colors. Every dungeon
tile, sewer tile, and city tile looked nearly identical — monotonous purple/grey blobs.

**After:** Switched to `MeshStandardMaterial` with per-sector `roughness`, `metalness`,
and `emissive` glow. Each sector now has a distinct visual fingerprint:

| Sector | Top Color | Emissive | Roughness | Metalness | Character |
|---|---|---|---|---|---|
| dungeon | deep purple `#4a2255` | violet `#110022` | 0.80 | 0.15 | Glowing purple stone |
| forest | rich green `#2a9940` | life `#051408` | 1.00 | 0.00 | Organic, matte |
| city | cool grey `#9aabb8` | none | 0.90 | 0.05 | Stone cobblestone |
| sewer | murky green `#3a5538` | `#041008` | 0.85 | 0.10 | Damp stone |
| water | bright blue `#2288ee` | `#001133` | 0.10 | 0.30 | Reflective surface |
| cave | brown `#5a4030` | dim `#080200` | 0.95 | 0.05 | Raw rock |
| desert | sandy `#e0c878` | warm `#100800` | 1.00 | 0.00 | Dry, matte |
| swamp | dark green `#4a6638` | `#050a02` | 1.00 | 0.00 | Overgrown |

**Edge outlines** also sector-tinted: each tile now has a faint colored outline matching
its sector's accent color, not just a generic grey. Current room keeps gold outline.

**Lighting upgraded** to support PBR materials:
- Ambient: `0.4 → 0.55` intensity
- Directional: `0.8 → 1.1`, warm white `#fff5e0`
- Fill: `0.3 → 0.45`, cool blue `#8899cc`
- Added rim light from below (`0x220033`, 0.3) for emissive sector pop

### 2. Low HP Alert System

**Before:** No visual warning when near death beyond the static HP bar.

**After:** Two-layer danger system triggers at ≤25% HP:

**HP bar** — Switches from normal red gradient to pulsing deep crimson (`#7f0000 → #cc0000`)
with 0.8s alternate animation and a red glow border (`box-shadow: 0 0 6px rgba(200,0,0,0.6)`).

**Danger vignette** (`#danger-vignette`) — Full-screen radial gradient overlay:
- Transparent center → red at edges
- Pulses between 60% and 100% opacity on 1.1s cycle
- Added as a fixed overlay with `pointer-events: none` (doesn't block input)
- Snaps off immediately when HP returns above 25%

### 3. Combat Log Hierarchy

**Before:** All combat lines were the same 12px monospace text, same size, same 3s
fade. CRITICAL HIT and "is dead!" looked identical to "you hit the goblin."

**After:** Four distinct visual tiers:

| Type | Size | Color | Linger | Effect |
|---|---|---|---|---|
| `critical` | 14px bold | Orange `#ff6622` | 4s | Glow, scale-bounce entrance, screen flash |
| `kill` | 14px bold | Gold `#ffd700` | 5s | Glow, slide-in entrance |
| `attack` | 12px | Gold `#ffd700` | 3s | Normal |
| `damage` | 12px | Red `#ffaaaa` | 3s | Normal |
| `heal` | 12px | Green `#88ffbb` | 3s | Normal |
| `death` | 12px | Grey `#999999` | 3s | Normal |

**Triggers for `critical`:** CRITICAL HIT, ANNIHILATE, OBLITERATE, MASSACRE, DEMOLISH,
DEVASTAT — also triggers a screen flash (`rgba(255,100,0,0.3)`, 300ms)

**Triggers for `kill`:** "[mob] is dead!" / "has been killed" / "is slain!" — separated
from player death which stays grey. Kill also calls `markMobDead()` for portrait update.

Player combat verbs expanded: now includes annihilate, obliterate, massacre, demolish,
feint, backstab, disembowel, dismember, eviscerate.

### 4. Exit Indicators (Upgraded)

**Before:** Exit arrows existed but were tiny (0.42 scale), low contrast, no labels.
Effectively invisible in practice.

**After:** Complete visual overhaul of `createExitArrow()`:

**Current room exits:**
- Scale `0.42 → 0.70` (67% larger)
- Gold arrow body with **N/S/E/W direction letter** centered
- `renderOrder: 10` ensures visibility above tiles
- **Pulsing** — gentle opacity (0.72–1.0) + scale (±6%) pulse at 3.5Hz in render loop
- `_baseScale` stored on userData so pulse math stays stable across frames

**Explored room exits:**
- Scale `0.30 → 0.36`
- Cyan chevrons, 75% opacity

**Unexplored/frontier exits:**
- Grey chevrons, 50% opacity
- Still shown so players know exits exist

**Up/Down exits:**
- Circle badges with ▲/▼ symbols
- Current room: 0.65 scale with pulse
- Other rooms: 0.42 scale, static

---

## 📁 Files Modified (Evening Session)

| File | Changes |
|---|---|
| `src/web_isometric/index.html` | Tile theming, low HP vignette, combat log hierarchy, exit indicators, player portraits, exact name map, boss fallback fix |
| `src/web_isometric/sprites/dcss/` | +23 DCSS sprites (new subdirs: dragons, fungi_plants, eyes, aberrations) |
| `src/web_isometric/sprites/dcss/boss/` | +7 custom AI boss portraits |
| `src/web_isometric/sprites/dcss/animals/` | +12 custom AI animal portraits |
| `src/web_isometric/sprites/players/` | +36 custom AI player tier portraits (new directory) |

**Total sprites:** 149 (morning) → 227 (evening) — +78 sprites added in one session.

---

## 🔮 Known Pending / Next Steps

- Screenshots needed to verify tile theming, exit arrows, vignette in-game
- Wolverine/badger portraits use custom art — verify they look right vs. warg fallback
- Tier 3 player portraits (weapon-type variants on top of armor tier) — future work
- Four Horsemen zone (220) bosses now have custom portraits — test in combat
- Low HP vignette threshold (25%) may need tuning based on gameplay feel

---

*Evening session documented by Ram 🐏 — Feb 18, 2026 @ ~10 PM PST*
