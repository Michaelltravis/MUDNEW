# Changelog - February 4, 2026

## Tutorial Quest System (NEW!)

Comprehensive 8-quest tutorial chain for new players:

### Tutorial Quests
1. **Awakening** - Meet Sage Aldric, learn about the world
2. **Eyes Open** - Visit Temple Square and Temple Altar (movement basics)
3. **Know Thyself** - Use score, equipment, inventory commands
4. **The Way of Your Class** - Learn skills and spells commands
5. **Blood and Steel** - Visit Training Grounds, defeat a training dummy
6. **The Art of Survival** - Rest, stand, eat (recovery basics)
7. **Tools of the Trade** - Visit shop, use list, buy something
8. **Into the Unknown** - Venture outside, defeat a creature, return

### New NPCs
- **Sage Aldric** (vnum 3200) - Tutorial guide in the Temple
- **Training Dummy** (vnum 3201) - Practice combat target
- **Sergeant Bron** (vnum 3202) - Combat instructor

### New Room
- **The Training Grounds** (vnum 3078) - Practice area south of Temple Square
  - Contains 5 training dummies and Sergeant Bron
  - Connected to Temple Square via southwest exit

### Quest System Updates
- Added 'command' objective type for tracking command usage
- Auto-start tutorial for new level 1 players
- Auto-complete tutorial quests (no need to return to quest giver)
- Tutorial progress tracked after every command
- Rewards include XP, gold, practice sessions, and title "the Initiated"

---

## Phase 2: Feedback Loops

### Epic Level-Up Celebrations
- Animated star sparkle effect on level up
- Detailed stat gains display (HP, Mana, Move, Practices)
- Class-specific titles at milestone levels (5, 10, 15, 20, 30, 40)
  - Warrior: Fighter → Veteran → Swordmaster → Champion → Warlord → Battlemaster
  - Mage: Apprentice → Conjurer → Magician → Warlock → Archmage → Grand Magus
  - And all other classes!
- Milestone messages at levels 5, 10, 15, 20, 25, 30, 40, 50
- Room announcement when someone levels up

### Enhanced Achievement System
- **Tiered achievements**: Bronze, Silver, Gold, Platinum, Legendary
- Beautiful framed notification banners with tier-appropriate colors
- Tier icons: ◆ Bronze, ◇ Silver, ★ Gold, ✦ Platinum, ✧ Legendary
- Room announcements for Gold+ achievements
- New achievements added:
  - Kill milestones: Hunter (10) → Slayer (100) → Executioner (500) → Death Incarnate (1000)
  - Exploration: Explorer (10) → Wanderer (100) → World Traveler (500) → Master Cartographer (1000)
  - Levels: Rising Star (10) → Veteran (20) → Elite (30) → Legend (40) → Immortal Aspirant (50)
  - Bosses: Boss Slayer (1) → Boss Hunter (5) → Boss Master (10 unique)
  - Wealth: Pocket Change (100g) → Well Off (1k) → Wealthy (10k) → Tycoon (100k)
  - Quests: Adventurer (1) → Questor (10) → Hero of the Realm (50)
- Title rewards for top-tier achievements

### Discovery Journal System (NEW!)
Complete journal system tracking player discoveries:

**Categories:**
- 📜 Lore & History - Read from books, scrolls, signs
- 🔮 Secrets - Hidden rooms, passages, treasures
- 👤 Notable Figures - Important NPCs you've met
- 🗺️ Explored Regions - Zones you've discovered
- 📖 Bestiary - Creatures you've defeated
- ⚔️ Quest Log - Completed quests
- 🏆 Achievements - Unlocked achievements

**Commands:**
- `journal` - Overview with category counts
- `journal stats` - Detailed exploration statistics
- `journal lore/secrets/npcs/areas/bestiary/quests` - Filter by category
- `journal read <#>` - Read a specific entry
- `journal all` - Show all entries

**Auto-Discovery Hooks:**
- **Zone Entry** - Records first visit to each zone
- **Mob Kills** - Adds creatures to bestiary on first kill
- **NPC Conversations** - Notable NPCs recorded when talked to
- **Quest Completion** - Quests logged when completed
- **Lore Reading** - Books and scrolls added when read

**Features:**
- Beautiful ASCII-framed notifications for discoveries
- Unread entry indicators (*)
- Persistent across sessions
- Pre-defined lore for major world locations
- Entry details include discovery location and date

### Enhanced Ability Notifications (NEW!)
When leveling up and learning new skills/spells:
- Beautiful framed "NEW ABILITIES UNLOCKED!" panel
- Skills shown with ⚔ icon and descriptions
- Spells shown with ✦ icon and descriptions
- 40+ ability descriptions for flavor text
- Groups all new abilities in single notification

### Consider Command Enhanced
- Shows detailed mob assessment with health status
- Displays special abilities (spells, poison, stun, etc.)
- Shows behavior warnings (aggressive, hunts, remembers)
- Provides tactical hints (weaknesses, class-specific tips)
- Boss-specific info including ability names

---

## Phase 3: Living World

### Dynamic Room Descriptions (NEW!)
Room descriptions now vary based on time, weather, and season:

**Time-based atmosphere:**
- Night: "Stars glitter in the dark sky above."
- Dawn: "The eastern sky blushes pink and gold with approaching dawn."
- Morning: "Morning sunlight filters through, warming the air."
- Afternoon: "The afternoon sun beats down warmly."
- Dusk: "The sun sinks low, painting the sky in oranges and purples."
- Evening: "The last light of day fades from the sky."

**Weather effects:**
- Clear, cloudy, rainy, stormy, snowy, foggy conditions
- "Rain patters steadily from the grey sky."
- "Lightning illuminates the sky for a brief moment."

**Season effects:**
- Spring: "New growth pushes up through the thawing earth."
- Summer: "The warmth of summer is in full force."
- Autumn: "Leaves display their autumn colors."
- Winter: "The cold bite of winter is in the air."

**Sector-specific ambiance:**
- Forest: "Leaves rustle in the branches overhead."
- Desert: "Heat shimmers rise from the sandy ground."
- Swamp: "The air is thick with humidity and strange smells."
- Underground: "Water drips somewhere in the distance."

**Transition Messages:**
- Inside→Outside: "Sunlight washes over you as you step outside."
- Outside→Inside: "You enter, leaving the outside behind."
- Surface→Underground: "The air grows cool and damp as you descend."

### Ambient Events (Already Existed!)
The game already had a comprehensive ambient event system:
- City sounds (merchants, guards, children)
- Forest creatures (birds, squirrels, wolves)
- Weather effects (rain, thunder, wind)
- Danger alerts (when aggressive mobs nearby)
- Peaceful sanctuary messages

### NPC Schedules (NEW!)
NPCs now have daily routines based on their type:

**Shopkeepers:**
- 7am-8pm: Working (shop open)
- 8pm-7am: Closed (announces "closes the shop for the night")

**Guards:**
- 6am-10pm: Patrolling (announces "begins patrol")
- 10pm-6am: Off duty (announces "goes off duty")

**Innkeepers:**
- 6am-12pm: Cleaning
- 12pm-10pm: Serving customers
- 10pm-6am: Night desk duty

**Farmers:**
- 5am-12pm: Field work
- 12pm-2pm: Lunch break
- 2pm-7pm: Back to fields
- 7pm-5am: Sleeping

**Priests:**
- 6am-9am: Morning prayers
- 9am-5pm: Temple duties
- 5pm-8pm: Evening vespers
- 8pm-6am: Meditation

NPCs announce their activity changes to players in the room.

---

---

## Help System Coverage (NEW!)
- Added help entries for all remaining player commands (207 total)
- Help text generated from command docstrings for accurate usage and descriptions
- Players can now use `help <command>` for every command in the game

---

## Phase 4: Depth

### Talent Tree System (NEW!)
Complete specialization system for all classes:

### Talent Ability Wiring (Fixes + Additions)
- Added talent command handlers for new class abilities (warrior/thief/ranger/paladin/assassin).
- Added talent spell entries (mage, priest, paladin, death knight, bard, etc.) and special spell effects.
- Fixed special-spell handler placement so new specials execute correctly.
- Added clearcast/Presence of Mind/Arcane Power handling in spell casting.
- Spell crit now includes talent bonuses + Combustion effect.
- Poison talents now route through envenom with preferred poison type.
- Damage absorption + reduction now respect affects (divine_shield/stoneskin + damage_reduction).

**Commands:**
- `talents` - View all your talent trees
- `talents <tree>` - View specific tree (e.g., `talents fury`)
- `talents learn <id>` - Learn or rank up a talent
- `talents reset` - Reset all talents (costs level × 100 gold)

**Mechanics:**
- Earn 1 talent point per level starting at level 5 (46 total by level 50)
- 5 tiers per tree, each requiring 5 more points in tree
- Higher tiers unlock powerful abilities and passives
- Multi-rank talents (1-5 ranks) for scaling bonuses
- Prerequisites enforce learning order

**Warrior Trees:**
- 🛡️ **Protection**: Tank specialization
  - Thick Skin, Shield Mastery, Last Stand, Shield Wall, Vigilance, Impenetrable, Unbreakable
- 🔥 **Fury**: Berserker damage dealer
  - Blood Frenzy, Endless Rage, Rampage, Bloodthirst, Reckless Abandon, Execute, Meat Cleaver, Avatar of War
- ⚔️ **Arms**: Precise weapon master
  - Weapon Expertise, Deep Wounds, Tactical Mastery, Impale, Mortal Strike, Second Wind, Sword Specialization, Bladestorm

**Mage Trees:**
- 🔥 **Fire**: Explosive damage
- ❄️ **Frost**: Control and shatter combos
- ✨ **Arcane**: Mana efficiency and raw power

**Thief Trees:**
- 🗡️ **Assassination**: Poisons and crits
- ⚔️ **Combat**: Sustained dual-wield damage
- 🌑 **Subtlety**: Shadow and stealth mastery

**Cleric Trees:**
- ✝️ **Holy**: Healing and protection
- 🛡️ **Discipline**: Shields and atonement
- 🌑 **Shadow**: Damage and lifesteal

---

### Bug Fixes
- Fixed ActiveQuest.to_dict() being on wrong class (was on DialogueNode)
- Fixed zone discovery using wrong attribute (zone.number not zone.vnum)
- Fixed advance command to trigger proper level-up celebrations
- Fixed 'bright_white' color reference in talents command

---

## Immortal Commands System

Added a complete set of immortal/wizard commands for server administration:

### Loading & Creating
- **`mload <vnum>`** - Load a mob into the current room
- **`oload <vnum> [room]`** - Load an object (to inventory or room)
- **`purge [target]`** - Remove mobs/objects from room (or specific target)
- **`zreset [zone]`** - Reset/repopulate a zone

### Player Management
- **`restore [player]`** - Fully heal HP/mana/move
- **`advance <player> <level>`** - Set player level (1-100)
- **`transfer <player>`** - Summon player to your location
- **`force <player> <command>`** - Force player to execute a command
- **`set <target> <field> <value>`** - Modify stats (level, hp, str, etc.)

### Combat & Control
- **`slay <target>`** - Instantly kill a mob
- **`peace`** - Stop all combat in the current room

### Movement & Visibility
- **`goto <vnum/zone>`** - Teleport to any room (already existed)
- **`wizinvis`** - Toggle invisibility to mortals

### Information
- **`stat <target>`** - View detailed stats on player/mob/object
- **`immlist`** - List all immortal accounts
- **`wizhelp`** - Display immortal command help

### Server Control
- **`shutdown now`** - Immediate server shutdown
- **`shutdown reboot`** - Reboot the server

## Account System

- Created immortal account **deckard** with admin privileges
- `is_immortal` property added to Player class for admin checks
- Immortal status stored in Account (`is_admin` flag)

## Technical Details

### Files Modified
- `src/player.py` - Added `is_immortal` property
- `src/commands.py` - Added 15 immortal commands + `_find_target` helper

### Implementation Notes
- All immortal commands check `player.is_immortal` before execution
- `is_immortal` looks up the player's account and checks `is_admin` flag
- Commands provide helpful usage messages and colored output
- `stat` command shows different details for players vs mobs vs objects
- `set` command supports all major stat fields
- `purge` can remove all mobs/objects or target specific ones

## Server
- Restarted to load new commands
- Running on port 4000, web map on port 4001

---

## Infrastructure Improvements

### 1. Backup System
- Created `scripts/backup.sh` for automated backups
- Keeps last 20 backups, auto-rotates old ones
- Creates compressed tar.gz in `backups/` directory
- Run manually or via cron: `0 */6 * * * /path/to/backup.sh`

### 2. Bug Fixes (TODOs)
- **Poison effect**: Mobs with poison flag now apply DOT to players
- **Quest item rewards**: Quest completion now properly creates and gives items

### 3. Supervisor Script (`scripts/supervisor.py`)
- Auto-restarts MUD on crash
- Max 5 restarts in 5 minutes (prevents crash loops)
- Discord webhook alerts for: start, restart, crash, shutdown
- Set `REALMSMUD_DISCORD_WEBHOOK` env var to enable alerts

Usage:
```bash
export REALMSMUD_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
python3 scripts/supervisor.py
```

### 4. Admin Dashboard (port 4002)
- Web-based admin interface at http://localhost:4002
- Real-time stats: uptime, players, rooms, NPCs, memory
- Online player list with level, class, HP, location
- Quick actions: broadcast message, shutdown
- Live server logs (last 50 lines)
- Auto-refreshes every 10 seconds

---

## Talent System Smoke Test - PASSED ✅

### Warrior Skills (Nyk)
- ✅ Bladestorm - AoE damage working
- ✅ Rend - DOT applied correctly
- ✅ Mortal Strike - Heavy damage + healing reduction
- ✅ Shield Bash - Stun effect, requires shield
- ✅ Overpower - Works after enemy dodge
- ✅ Sunder Armor - Armor reduction applied

### Mage Spells (Tester)
- ✅ Ice Barrier - Absorb shield applied
- ✅ Ice Lance - 41 damage + arcane charge gained
- ✅ Cold Snap - Reset frost cooldowns
- ✅ Arcane Power - Buff applied
- ✅ Presence of Mind - Instant cast buff
- ✅ Pyroblast/Combustion - Cast logic works (fizzle due to 75% proficiency normal)

### Paladin Spells (Paladin)
- ✅ Divine Shield - Absorb barrier (absorbed 8 damage in test)
- ✅ Lay on Hands - Used 53 mana, healed 174 HP (mana×3 + level×5)
- ✅ Avenging Wrath - Spell added (not tested, insufficient mana)

### Thief Skills (Thief)
- ✅ Sneak - "You start moving silently..."
- ✅ Hide - "You blend into the shadows..."
- ✅ Shadowstep - "You blur through shadows behind fido"
- ✅ Backstab - Correctly requires piercing weapon
- ✅ Mutilate - Correctly requires combat

### Bug Fixes During Testing
- Fixed `import random` inside try block causing UnboundLocalError
- Moved talent spells from BARD_SONGS dict to SPELLS dict
- Added missing `damage_reduction` attribute to Character.__init__
- Implemented divine_shield/stoneskin absorb in take_damage()
- Added lay_on_hands + avenging_wrath spells for paladin

### Test Characters
- `tester` - Level 15 Mage with all fire/frost/arcane talent spells
- `thief` - Level 15 Thief with assassination/subtlety skills
- `paladin` - Level 15 Paladin with holy talent spells
- `cleric` - Level 15 Cleric with holy/discipline/shadow spells
- `deathknight` - Level 15 Death Knight with blood/frost/unholy spells

---

## Extended Spell Testing - Session 2

### Cleric Spells
- ✅ Pain Suppression - 40% damage reduction applied
- ✅ Mind Flay - 42 damage + slow effect

### Death Knight Spells (NEW)
Added missing death knight talent spells:
- `death_strike` - Damage + 25% lifesteal heal
- `dancing_rune_weapon` - +5 damroll, +4 hitroll buff
- `remorseless_winter` - AoE frost damage + slow
- `killing_machine` - Guaranteed crit on next strike
- `festering_strike` - Damage + apply festering wounds (max 8)
- `apocalypse` - Burst all festering wounds + summon ghouls

### Death Knight Testing
- ✅ Bone Armor - Protective shell applied
- ✅ Dancing Rune Weapon - "A spectral rune weapon appears!"
- ✅ Killing Machine - "Your next strike will be devastating!"
- ✅ Howling Blast - AoE frost damage
- ✅ Army of the Dead - Summons 2 bone knights (level 13, 3min)

### Priest Shadow Spells (NEW)
- `vampiric_embrace` - 25% of shadow damage heals caster
- `void_eruption` - 6d6+3/level AoE shadow damage

### Stealth Combat Flow
- ✅ Sneak → Hide → Backstab chain working
- ✅ Backstab with dagger: damage = (1d4 × 3) + bonus = ~5-15
- ✅ Cold Blood guarantees next crit
- ✅ Shadowstep working

### Pet/Minion System
- ✅ Army of the Dead summons bone knights correctly
- ✅ Max undead limit enforced (level/10 + 1)
- ✅ Pets appear in room with long descriptions
- ✅ New `minions` command shows summoned pets with HP% and duration

### Balance Notes
Current damage at level 15:
- Mortal Strike: 10-20 + level = avg 30 damage
- Bladestorm: 6-12 + level per target = avg 24 (AoE)
- Backstab: weapon × 3 + bonus = ~15-25 with dagger
- Rend DOT: 8/tick × 4 ticks = 32 total
- Ice Lance: 2d6+4 = avg 11 + level scaling
- Mind Flay: 3d6 + 2/level = ~40 at level 15

All damage values seem appropriate for their mana/skill costs.

---

## Polish Testing - Session 3

### 1. Combo Finishers
- ✅ Mutilate builds combo points (+2 per use)
- ✅ Eviscerate command exists and requires combo points
- ✅ Kidneyshot command exists (needs 4+ combo points for stun)
- Note: Testing limited as enemies die quickly to mutilate damage

### 2. Ranger Talents (NEW)
Added missing ranger abilities:
- ✅ `rapid_shot` - Fire 3 arrows rapidly (9+12+12 = 33 damage)
- ✅ `volley` - AoE arrow rain on all enemies
- ✅ `marked_shot` - Heavy damage (1.5x if target marked)
- ✅ `hunters_mark` - Mark target for bonus damage
- ✅ `camouflage` - Enhanced hide in wilderness

### 3. Bard Songs
- ✅ `songs` command shows repertoire with mana costs
- ✅ `perform song_of_courage` - "You begin singing a stirring song!"
- ✅ Songs list: Courage, Battle Hymn, Dirge of Doom, Rest, Lullaby

### 4. DK Festering + Apocalypse Combo
- ✅ Festering Strike applies festering wounds (stacks to 8)
- ✅ Apocalypse bursts wounds for bonus damage + spawns ghouls
- ✅ "The apocalypse consumes your enemies! (X wounds burst)"

### 5. Talent Learning Integration
- ✅ `talents` shows tree overview with points spent/available
- ✅ `talents fury` shows detailed tier breakdown
- ✅ Tiers properly lock/unlock based on points invested
- ✅ "No talent points available" when trying to learn without points
- ✅ Nyk has 6 points in Fury: blood_frenzy 3/5, endless_rage 2/3, rampage MAX

### Bug Fixes During Polish
- Fixed ambient.py crash: weather.precipitation string vs int comparison

### New Test Characters
- Ranger (Level 15) - Marksmanship/survival skills
- Bard (Level 15) - Performance songs

---

## Web Client (NEW!)

Browser-based terminal client for players who prefer web access over telnet:

### Features
- **WebSocket bridge** - Connects browser to MUD via telnet proxy
- **ANSI color support** - Full color rendering in HTML
- **Command history** - Arrow keys navigate through previous commands
- **Quick buttons** - Look, Inv, Score, Who, and directional movement
- **Mobile-friendly** - Responsive design works on phones/tablets
- **Dark theme** - Easy on the eyes for long sessions
- **Integrated world map** - Split-pane layout with map panel on right
- **Toggle map** - Click 🗺️ Map button or press M key

### Access
- URL: http://localhost:4003
- Connects automatically to MUD on page load
- Map loads from port 4001 automatically
- No installation required - just share the URL

### Technical
- Built with aiohttp + native WebSockets
- Zero dependencies beyond existing MUD stack
- Embedded HTML/CSS/JS (single-file deployment)
- Graceful reconnection handling
- Responsive layout adapts to mobile screens

---

## Project Stats

As of end of day Feb 4, 2026:
- **~50,400 lines of code** total
- **47,171 lines** Python source
- **66 files** across src/, scripts/, lib/
- **38 zones**, **2,040 rooms**
- **8 playable classes** with talent trees
- **230+ commands** implemented
