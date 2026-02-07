# RealmsMUD Changelog - February 5, 2026

## Guard Call-for-Help Mechanic - COMPLETE ✅

### Implementation
- Guards with `helper` flag now shout "GUARDS! HELP!" when attacked
- Nearby guards (within 3 rooms) rush to assist via BFS pathfinding
- Guards respect closed doors (won't path through them)
- Arriving guards immediately engage the attacker

### Code Changes
- `combat.py`: Added `call_guards_for_help()` classmethod
- `combat.py`: Modified `start_combat()` to trigger call-for-help when defender has `helper` flag
- Guards set `fighting = attacker` and `position = 'fighting'` on arrival
- Combat tick in `world.py` processes NPC combat, so arriving guards attack on next tick

### Mob Flags Verified
- **Cityguard (3060)**: `['special', 'stay_zone', 'memory', 'helper', 'sentinel']`
- **Fido (3062)**: `['special', 'aggressive', 'stay_zone', 'wimpy', 'no_bash', 'slow_wander']`

### Testing Results
```
cityguard shouts 'GUARDS! HELP!'
cityguard rushes off to answer the call!
cityguard arrives to help!
```
- Multiple guards (4) arrived from nearby rooms
- Guards properly removed from origin rooms and added to fight room

### Previous Work (from summary)
- `sentinel` flag prevents wandering (guards stay in place)
- `slow_wander` flag = 1% chance vs 3% normal (fidos wander slower)
- `wander_ai()` updated to check both flags

## Additional Updates (later today)

### Combat/UX
- Combat slowed to **4s** per round
- **HP prompt** shown after every combat round
- Command **echo** added (web + telnet)

### Practice command
- `practice` now shows the full class list even when **not at a trainer**
- Unlearned skills/spells show **0%**

### Affects and movement flavor
- Room look now shows select affect flavor lines:
  - Fly, Sanctuary, Stoneskin, Poison, Invisible (detect-only)
- Movement flavor for Fly/Sanctuary

### Stealth / Detection / Tracking
- Perception stat added (`PER=(WIS+DEX)/2 + level/5`)
- Sneak/Hide checks now include environment bonuses:
  - Dark +20, Forest/Swamp +10, Active light −25
- **Exposed** debuff on detection (10–30s) prevents re‑sneak/hide
- NPCs enter **searching** state when detecting a sneaker (+15 detect)
- Hide can break tracking (50% chance)
- **Sneaking movement cost** increased by terrain
- **Light control commands**: `cover light`, `uncover light`, `snuff light`, `relight light`
- **Sneaking mobs** can be **randomly visible** (perception‑based)
- `detect_bonus` added for mobs, boosts detection rolls

### DOT / Regen
- Regen tick 60s; base regen boosted (HP 12%, Mana 15%, Move 20%)
- DOT tick system separated (`AFFECT_TICK_SECONDS` / `POISON_TICK_SECONDS`)

### Pets / Group / Targeting
- Pet command upgrades (assist/report/skill orders) + `pets` manager
- Pets announce room entry, colored in look
- Grouping enhancements (group all/disband/kick, followers auto‑move)
- Target system: spells/skills use `player.target` if unspecified; multi‑word spells supported

### Bosses / Dragons / Gear Progression
- Endgame dragons added (Red/Green/Bronze/Prismatic) + Beholder boss
- Boss loot tables + equipment rolls
- Set bonuses system (always‑on + in‑zone) with `sets` command
- Mid/endgame gear tinted by zone + class accents
- Zone gear progression added with themed loot

### Affix System (new)
- Equipment affects now boost **skills** and **spells**:
  - Skills use `get_skill_level()` (skill + gear bonus)
  - Spells scale with `spell_power` + per‑spell affix
  - Heals scale with `heal_power` + per‑spell affix
  - Smite scales with `smite/holy_smite`

### Endgame stealth gear
- Boss stealth gear (sneak + no_track)
- Backstab gloves added, backstab % bonus from gear

### New Zone: Tunnel of Sticks (zone_210)
- **20x20 maze** (400 rooms), dark/indoors
- Entrance from **zone_040 room 4016** via **down** (two‑way)
- Secret descent to Castle Apocalypse (search_difficulty 60)
- **Mosquitoes**: sneaking + slow_wander, high detect_bonus, low hp/dmg
- **Stick Stalkers**: tougher roaming mob, aggressive
- **Portable Hole** rare drop (capacity 200) from stalkers

### Castle Apocalypse (zone_220)
**Outer Area**
- Wall perimeter paths (east + west)
- Locked **main gate** with two **boss** guardians (one holds gate key)
- West wall patrols: undead guardians (2–3 per room)
- **Deathtrap trail** (~15 rooms) with instant‑death trap rooms
- **Kirgan the Destroyer** (lvl 60) at trail end, drops inner gate key + themed loot

**Interior Wing (Four Horsemen)**
- Inner gate 4 rooms south of main gate
- Entry room: **Pestilence** (boss)
- **Pestilence key** opens the south gate (locked)
- **War key** opens the door to **Death**
- East L‑path → **War** boss
- West L‑path → **Famine** boss
- South door → **Death** boss

### Horsemen Loot (themed)
- **Pestilence**: Plaguewrap, Pestilent Ring, Plaguebearer’s Censer
- **War**: Warbrand, Pauldron of War, Banner of War
- **Famine**: Hunger Chain, Gauntlets of Famine, Girdle of Hunger
- **Death**: Scythe of Endings, Veil of the End, Mantle of the End, Death’s Ring

### Rare Class Gear (colored)
- Necromancer: Gravebind Locket
- Cleric: Radiant Rosary
- Warrior: Warlord’s Vambrace
- Paladin: Halo of Judgment
- Ranger: Wildpath Bandolier
- Thief: Shadowgrip Wraps
- Mage: Stormcall Ring
- Bard: Dirgeflute
- Assassin: Eclipse Band

## OLC Implementation (MVP)

### Commands
- `redit` — Room editor (immortal only)
  - Edit name, description, sector, flags
  - Edit exits (destination, description, doors, hidden/secret, search difficulty)
  - Edit extra descriptions
- `save <zone>` — Write zone to disk

### OLC Menu Flow
- Menu-driven interface matching OasisOLC style
- Multi-line description input (end with `@`)
- Flag toggling (add/remove on repeat)
- Exit editor with full door support (name, locked, key vnum, hidden)

### Technical
- OLC state stored on player (`player.olc_state`)
- Input intercepted in `CommandHandler.execute()` when in OLC mode
- Room `to_dict()` now preserves full exit data (doors, hidden flags, etc.)

## Castle Apocalypse Best Practice Fixes

### Room Descriptions (OasisOLC Guidelines)
- All room descriptions expanded to **3+ lines**
- Removed directional phrasing ("to your right", "behind you")
- Lines wrapped at **65-75 characters**
- Proper grammar and punctuation throughout

### Extra Descriptions Added
- **Outer Gate**: gate, wall, runes
- **Main Gate**: guardians, runes
- **Courtyard**: battlements, beams, courtyard
- **Chamber of Death**: frost, void
- **War's Arena**: throne, blood
- **Famine's Vault**: vault, braziers
- **Kirgan's Lair**: throne, armor

### Mob Descriptions Normalized
- Removed all gear references from mob long_desc
- Added proper `description` field with lore (no equipment mentions)
- All 8 mobs updated: guardians, Kirgan, Four Horsemen

### Object Descriptions Added
- Ruinblade, Warbrand, Scythe of Endings (weapons)
- Apocalypse Plate, Veil of the End (armor)
- Death's Ring (accessory)

### Gear Tradeoffs (per handbook)
- Ruinblade: +6 damroll, +3 hitroll, **-25 HP**
- Warbrand: +7 damroll, +4 hitroll, **-20 HP**
- Scythe of Endings: +8 damroll, +5 hitroll, **-30 HP**
- Veil of the End: +10 spell_power, +6 heal_power, **-20 HP**

### Balance Pass (Level 59-60)
**Class-themed drops boosted for parity:**
- Hunger Chain: sneak +8, track +10
- Gauntlets of Famine: damroll +5, spell_power +8
- Gravebind Locket: vampiric_touch +15, spell_power +8
- Radiant Rosary: heal +15, turn_undead +12
- Warlord's Vambrace: bash +10, damroll +4
- Halo of Judgment: holy_smite +15, heal_power +8
- Wildpath Bandolier: track +12, ambush +10
- Shadowgrip Wraps: sneak +10, backstab +10
- Stormcall Ring: lightning_bolt +15, spell_power +8
- Eclipse Band: backstab +15, no_track +1

**Mob stat tuning:**
- Gate Guardians: 55d10+800 HP, 14d8+22 dmg
- Undead Guardians: 16d10+180 HP, 5d6+8 dmg
- Kirgan: 60d10+950 HP, 16d8+26 dmg
- Pestilence: 55d10+850 HP, 14d8+20 dmg
- War: 58d10+900 HP, 16d8+24 dmg
- Famine: 56d10+870 HP, 15d8+22 dmg
- Death: 65d10+1000 HP, 18d8+28 dmg (hardest)

## Full World Audit (OasisOLC Guidelines)

### Scope
- **40 zones** audited
- **2494 rooms** processed
- **670 mobs** checked
- **1101 objects** balanced

### Room Description Fixes
- Expanded ALL short descriptions to **3+ lines**
- Added sector-appropriate flavor text:
  - Inside/dungeon: cold walls, shadows, dust
  - City: cobblestones, urban bustle
  - Forest: canopy, fallen leaves, bird calls
  - Field/hills: open sky, grass, wind
  - Mountain: thin air, rocky terrain
  - Swamp: murky water, decay
  - Desert: endless sand, heat
  - Water: ripples, currents

### Directional Phrasing Removed
- Converted all "You are standing/walking" to third-person
- Fixed "to your left/right" → "nearby"
- Fixed "to your north/south/east/west" → "to the north/south/etc"
- Fixed "north/south/etc of you" → "to the north/south/etc"
- Fixed "You can see" → "Visible is"
- Fixed "around you" → "around"

### Mob Description Normalization
- Removed gear references from mob long_desc
- Fixed patterns: "wielding X", "wearing X", "clad in X", "carrying X"

### Gear Balance Pass
- Added HP tradeoffs to all high-power items (+6 damroll/hitroll/spell_power)
- Weapons: -15 HP penalty
- Armor/accessories: -10 HP penalty

### Zones Fixed
All 40 zones now pass OasisOLC guidelines:
- Zone 000-009: Limbo, River Island
- Zone 012-015: God Simplex, Straight Path
- Zone 025: High Tower of Magic
- Zone 030-036: Midgaard (North/South), Three of Swords, Miden'Nir, Chessboard
- Zone 040: Mines of Moria
- Zone 050-054: Desert, Drow, Thalos, Pyramid, New Thalos
- Zone 060-065: Haon-Dor, Orc Enclave, Arachnos, Rand's Tower, Dwarven Kingdom
- Zone 070-079: Sewers (all levels), Redferne's
- Zone 080-090: Dragon's Lair, Haunted Swamp
- Zone 100-160: Khaz-Durum, Silversong, Rome, Sunken Ruins, Necropolis, Welmar's Castle, Chaos Plane
- Zone 186: Newbie Zone
- Zone 200-220: Forest of Shadows, Tunnel of Sticks, Castle Apocalypse

## OLC Complete (medit/oedit)

### medit - Mob Editor
Menu-driven mob editing:
- Keywords, short/long/description
- Level, HP dice, damage dice, AC
- Gold, experience, alignment
- Flags (aggressive, sentinel, helper, boss, etc.)
- Boss setup with loot chance

### oedit - Object Editor
Menu-driven object editing:
- Keywords, short/room/description
- Item type, wear slot, weight, value
- Flags (magic, glow, hum, nodrop, etc.)
- Affects (stats, spell bonuses)
- Type-specific: damage dice (weapons), armor bonus (armor), capacity (containers)

## Newbie Experience Improvements

### Tutorial Quest Extension
- Added **tutorial_9_newbie_zone** quest
- Directs players to the Great Field and Newbie Zone
- Requires killing 3 creatures in Newbie Zone
- Rewards 500 XP and 200 gold
- Completes the tutorial flow: Temple → Training → City → Newbie Zone

### Newbie Zone Audit (Zone 186)
- 41 rooms with proper 3+ line descriptions
- 15 mobs spanning levels 1-7
- 24 objects with appropriate stats
- Connected to Midgaard via Great Field (room 3061)

## Web Client Complete Redesign

### Visual Overhaul
- **Welcome splash screen** with animated logo while connecting
- **Modern typography**: JetBrains Mono (terminal) + Inter (UI)
- **Refined color palette** with subtle gradients and accent glows
- **Custom scrollbar** styling
- **Smooth animations** on all interactive elements

### New UI Components
- **Vitals bar** with gradient fills and glow effects:
  - HP: Red gradient with pulse on damage
  - Mana: Blue gradient
  - Move: Green gradient
- **Room info bar** showing current location + clickable exit buttons
- **Exit buttons** highlight green when that exit is available
- **Combat flash effect** when taking damage
- **Send button** for mobile/touch users
- **Status badge** with pulsing connected indicator

### Quick Commands
Organized into logical groups:
- Info row: Look, Inv, Gear, Stats, Quest, Who, Help
- Combat: Flee (styled red)
- All buttons have emoji icons

### Mobile Responsive
- Touch-friendly button sizes
- Map slides in as full-screen overlay on mobile
- Adjusted spacing and font sizes for small screens

### Keyboard Shortcuts
- `M` - Toggle map
- `/` - Focus command input
- Arrow Up/Down - Command history

## Help System Overhaul

### Comprehensive Index
- `help` now shows **ALL 500+ topics** organized by category:
  - Basic Commands
  - Movement
  - Communication
  - Combat
  - Skills
  - Spells
  - Bard Songs
  - Equipment & Items
  - Groups & Social
  - Information
  - Classes
  - Miscellaneous

### Pagination
- Shows 20 lines at a time
- **Press ENTER** to see next page
- Any other input cancels and runs that command
- Topics displayed in 4-column format for easy scanning

### New Help Entries Added
- `sets` - Equipment set bonuses
- `pets` - Pet management
- `updates` / `changelog` - Game updates
- `cover` / `uncover` / `snuff` / `relight` - Light control
- `ungroup` - Leave/kick from group
- `tick` / `notick` - Tick timer display

## Bug Fixes
- Fixed syntax error in practice command (stray else block)
- Fixed MAP_URL_PLACEHOLDER showing in web client iframe

## Backup System Implementation

### Backup Script (scripts/backup.py)
Full-featured backup system with:
- **Full backup**: Players + world + config
- **Selective backup**: `--players` or `--world` only
- **List backups**: `--list` shows all available backups with size/date
- **Restore**: `--restore <file>` with `--dry-run` option
- **Prune**: `--prune <days>` deletes old backups
- **Compression**: ~85% compression (2.9MB → 450KB)

### In-Game Backup Command (Immortal)
- `backup` - Full backup
- `backup players` - Player data only
- `backup world` - Zone data only
- `backup list` - Show available backups
- `backup restore <file>` - Restore from backup

### Automated Daily Backup
- `scripts/daily_backup.sh` for cron jobs
- Runs full backup + prunes backups older than 14 days
- Example cron: `0 4 * * * /path/to/daily_backup.sh`

### Backup Contents
- Player save files (data/players/*.json)
- Zone files (world/zones/*.json)
- Config (updates.json, motd.txt, config.py)
- Manifest with metadata

## Server Status
- Ports: 4000 (telnet), 4001 (web map), 4002 (admin), 4003 (web client)
- 40 zones, 2494 rooms loaded
- 345 commands, 496 help topics
- All systems operational
