# RealmsMUD Development Changelog
## Session: February 3, 2026

### Overview
Major feature expansion bringing RealmsMUD up to CircleMUD standards and beyond, with modern enhancements including AI-powered NPC dialogue.

---

## 🎮 CLASS SYSTEMS (Completed Previously)

All 7 classes now have unique mechanics:

### Mage - Arcane Charges
- Gain charges on offensive spell casts
- +5% spell damage per charge (max 5)
- Charges decay out of combat

### Paladin - Auras
- `aura devotion` - +15 AC to nearby allies
- `aura protection` - 10% damage reduction
- `aura retribution` - Thorns damage to attackers

### Cleric - Divine Favor
- Gain favor when casting healing spells
- Empowers healing and holy abilities

### Necromancer - Themed Servants
- `raise` creates themed undead: Bone Knight, Wraith Healer, Lich Acolyte, Shadow Stalker
- **Soulstone System**: `soulstone` command creates offhand item from corpses
  - +3 INT, +10% mana regen, +2 spell damage
  - `imbue` to level up soulstone (max 5 levels)

### Warrior, Ranger, Thief, Bard
- All previously implemented with full skill trees

---

## ⚔️ COMBAT SYSTEM ENHANCEMENTS

### Critical Strikes (New)
**Melee Crits:**
- Base 5% + 1% per 2 DEX above 10 + 0.5% per level
- Thief: +10% crit chance, 250% damage
- Warrior/Ranger: +5% crit chance
- Precision stance: +15% crit chance
- Cap: 50%

**Spell Crits:**
- Base 5% + 1% per 2 INT above 10 + 0.5% per level
- Mage: +5% crit chance, 200% damage (others 150%)
- Cap: 40%

### CircleMUD Combat Messages
**Damage Words (Progressive):**
```
tickle → barely scratch → scratch → nick → graze → hit → injure → 
wound → maul → decimate → devastate → maim → MUTILATE → DISMEMBER → 
MASSACRE → OBLITERATE → *** ANNIHILATE ***
```

**Weapon Verbs (15 types):**
hit, sting, whip, slash, bite, bludgeon, crush, pound, claw, maul, thrash, pierce, blast, punch, stab

**Color-Coded Damage:**
- White (1-4) → Green (5-12) → Yellow (13-24) → Bright Yellow (25-48) → Bright Red (49-80) → Magenta (81+)

**Varied Miss Messages:**
- "You miss...", "Your attack goes wide!", "They dodge your attack!", etc.

### Affect Descriptions (Look at NPCs)
When looking at affected NPCs, see flavorful descriptions:
- **Blind**: "stumbles around blindly, arms outstretched..."
- **Poisoned**: "looks sickly, with a greenish pallor..."
- **Stunned**: "sways unsteadily, looking dazed..."
- **Paralyzed**: "stands frozen in place..."
- **Feared**: "cowers in terror..."
- **Sanctuary**: "surrounded by a shimmering white aura"
- Plus: charmed, entangled, slow, haste, fly, stoneskin, fire_shield, ice_armor

---

## 🐾 PET SYSTEM ENHANCEMENTS

### New Pet Orders
- `order sit` - Pet sits down
- `order stand` - Pet stands up
- `order sleep` - Pet goes to sleep (stops following)
- `order rest` - Pet rests
- `order <direction>` - Send pet to another room

### Improved Order Command
- Works with just `order <action>` if you have one pet
- Or `order <petname> <action>` for specific pets

---

## 💬 COMMUNICATION COMMANDS (New)

| Command | Description |
|---------|-------------|
| `gossip <msg>` | Global chat channel (magenta) |
| `auction <msg>` | Auction channel (bright yellow) |
| `grats [msg]` | Congratulations channel (green) |
| `holler <msg>` | Shout to everyone (costs 20 movement) |
| `qsay <msg>` | Quest channel for quest parties |

---

## ℹ️ INFO COMMANDS (New)

| Command | Description |
|---------|-------------|
| `time` | Game clock with time-of-day descriptions |
| `commands` | Lists all 230+ commands in columns |
| `diagnose [target]` | Detailed health check with % and affects |
| `levels` | Shows XP required for levels 1-50 |
| `news` | Server updates and features |
| `motd` | Message of the Day |
| `policy` | Server rules |
| `info` | New player guide |

---

## ⚙️ SETTINGS & TOGGLES (New)

| Command | Description |
|---------|-------------|
| `toggle` | Shows ALL settings at once (15 options) |
| `color off\|sparse\|normal\|complete` | Color preference level |
| `prompt <format>` | Custom prompt (%h=HP %m=Mana %v=Move %g=Gold) |
| `display` | Alias for prompt |
| `autoexit` | Toggle auto-show exits on room entry |
| `norepeat` | Don't echo your own says/tells |
| `notell` | Block incoming tells |
| `noshout` | Block shouts/hollers |
| `wimpy <hp>` | Auto-flee when HP drops below threshold |

---

## 🗡️ COMBAT UTILITY COMMANDS (New)

| Command | Description |
|---------|-------------|
| `assist <player>` | Jump into their fight |
| `report` | Announce HP/Mana/Move to group |

---

## 📦 ITEM COMMANDS (New)

| Command | Description |
|---------|-------------|
| `junk <item>` | Destroy item, salvage 10% gold value |
| `donate <item>` | Send to donation room (75%) or junk (25%) |
| `pour <from> <to>` | Transfer liquids between containers |
| `pour <item> out` | Empty a container |
| `quaff <potion>` | Drink potion (alias for use) |
| `recite <scroll>` | Use scroll (alias for use) |

---

## 🍖 HUNGER & THIRST SYSTEM (New)

### Mechanics
- **Hunger**: Max 168 game hours (1 week), decrements each game hour
- **Thirst**: Max 60 game hours (2.5 days), decrements each game hour
- Warnings at low levels: "getting hungry" → "hungry!" → "STARVING!"

### Commands
| Command | Description |
|---------|-------------|
| `eat [food]` | Eat food or check hunger status |
| `drink [from] <source>` | Drink from fountain or container |
| `fill <container> [fountain]` | Fill waterskin from fountain |
| `taste <item>` | Sample food/drink |

### New Items
- **Marble Fountain** (Temple Square) - Infinite water source
- **Loaf of Bread** - +24 hours hunger
- **Leather Waterskin** - Holds 10 drinks

---

## 🏦 BANKING SYSTEM (New)

### Location
**First National Bank of Midgaard** - Northwest from Market Square (room 3069)

### Commands
| Command | Description |
|---------|-------------|
| `deposit <amount>` | Store gold in bank |
| `withdraw <amount>` | Get gold from bank |
| `balance` | Check bank balance |

---

## 📝 PLAYER FEEDBACK (New)

| Command | Description |
|---------|-------------|
| `bug <description>` | Report bugs → logs/bugs.log |
| `idea <suggestion>` | Submit ideas → logs/ideas.log |
| `typo <description>` | Report typos → logs/typos.log |

---

## 🚪 MISC COMMANDS (New)

| Command | Description |
|---------|-------------|
| `knock <direction>` | Knock on doors (notifies other side) |
| `enter [target]` | Enter buildings/portals |
| `leave` | Exit buildings to outdoors |
| `socials` | List all 30+ social commands |
| `title <new title>` | Set custom player title |

---

## 🤖 AI INTEGRATION (New)

### AI Service (`ai_service.py`)
Connects to LM Studio on `localhost:1234` for local LLM inference.

**Features:**
- Response caching (5 min TTL)
- Rate limiting (0.5s between requests)
- Graceful fallback when offline

**Available Methods:**
- `npc_dialogue()` - Dynamic NPC conversations
- `generate_quest()` - Procedural quest generation
- `combat_narration()` - Dramatic combat descriptions
- `room_ambiance()` - Atmospheric flavor text
- `item_lore()` - Item backstory generation

### Commands

#### `chat <npc> <message>`
Free-form AI conversation with NPCs:
```
> chat guard Hello, any trouble around here?
You say to the city guard, "Hello, any trouble around here?"
The city guard says, "Hail, citizen. The roads have been quiet, 
though I'd advise caution near the forest after dark."
```

Auto-generated NPC personalities:
- Guards: Formal, dutiful
- Merchants: Friendly, business-minded
- Wizards: Wise, cryptic
- Bartenders: Gossipy, knows rumors
- And more...

#### `aistatus`
Check LM Studio connection status.

### Setup
1. Open LM Studio
2. Load model (Qwen 2.5 7B recommended)
3. Start local server (port 1234)
4. AI features activate automatically

---

## 📊 HELP SYSTEM (New)

Added 112+ help entries covering:
- All new commands
- All spells (82 entries)
- All skills (30 entries)
- Game mechanics

---

## 🐛 BUG FIXES

- **Combat crash fix**: Removed `pet.is_fighting = True` (read-only property)
- **Help crash fix**: `get_help_text()` handles missing fields
- **ASCII UI toggle**: For terminals without UTF-8 box drawing

---

## 🗺️ WORLD ADDITIONS

### New Rooms
- **First National Bank of Midgaard** (3069) - Banking services
- Total rooms: 2026

### New Items
- Marble fountain (3100)
- Loaf of bread (3101)
- Leather waterskin (3102)

### Room Updates
- Temple Square now has fountain
- Market Square has bank exit (northwest)

---

## 📁 FILES MODIFIED

### Core Files
- `commands.py` - 230+ commands now
- `player.py` - Bank gold, hunger/thirst attributes
- `combat.py` - Crits, damage words, weapon verbs
- `spells.py` - Spell crits
- `world.py` - Hunger/thirst tick processing
- `pets.py` - New order commands
- `help_data.py` - 112+ new entries

### New Files
- `ai_service.py` - LM Studio integration

### Zone Files
- `zone_030.json` - Fountain, bank, new items

### Documentation
- `docs/CIRCLEMUD_GAP_ANALYSIS.md` - Feature comparison
- `docs/CHANGELOG_2026-02-03.md` - This file

---

## 📈 STATISTICS

| Metric | Before | After |
|--------|--------|-------|
| Commands | ~180 | 230+ |
| Help entries | ~100 | 212+ |
| Rooms | 2025 | 2026 |
| Objects | ~100 | 103 |

---

---

## 🧪 TESTING TOOLING (Enhanced)

### Test Coverage Expanded
| Category | Tests |
|----------|-------|
| Basic | look, score, inventory, equipment, who, help |
| Movement | south, north, exits |
| Info | time, weather, commands, levels, diagnose |
| Communication | say, gossip, emote |
| Inventory | get, drop |
| Settings | toggle, brief, color |
| **Shops** | list, value |
| **Banking** | balance, deposit, withdraw |
| **Combat Prep** | consider, wimpy, skills, spells |
| **Food/Drink** | eat, drink fountain |
| **Pets** | pet, order, group |
| **Hidden Dungeon** | search, open trapdoor, enter |

### Login Flow Fixed
- Handles character creation prompts
- Race/class selection
- Password confirmation
- MOTD skip

---

## 🧪 TESTING TOOLING (New)

### Automated Test Suite
- `tests/test_suite.py` connects via socket and validates core commands
- Checks: look, score, inventory, equipment, who, help, movement, time, weather, commands, levels, diagnose, say, gossip, emote, toggle, brief, color

### AI Player Agent
- `tests/ai_player.py` uses local LLM (LM Studio) to explore and test
- Safety filters prevent destructive commands
- Keeps command history for context

### Test Instructions
- `tests/README.md` with usage for automated tests, AI player, and manual `nc` testing

### Status
- Automated tests not run yet (awaiting command approval)

---

## 🌲 FOREST OF SHADOWS (New Zone)

### Zone Overview
- **Location:** Southwest from Midgaard's West Gate (room 3052)
- **Level Range:** 5-15
- **Rooms:** 10 new rooms
- **Theme:** Dark forest with wolves, spiders, and ancient ruins

### Rooms
| Room | Name | Features |
|------|------|----------|
| 20001 | Forest Edge | Entry point |
| 20002 | Shadowy Path | Forest wolves |
| 20003 | Dark Grove | Spiders + wolves |
| 20004 | Spider's Hollow | Venomous spiders |
| 20005 | Mossy Trail | Ancient stones |
| 20006 | Ruined Shrine | Spectral guardian, treasure |
| 20007 | Wolf Den Entrance | Dire wolves |
| 20008 | Spider Queen's Lair | **BOSS: Spider Queen** |
| 20009 | Wolf Den | **BOSS: Alpha Wolf** |
| 20010 | Hidden Glade | Peaceful, spring water |

### Bosses & Loot
| Boss | Level | Drops |
|------|-------|-------|
| Spider Queen | 12 | Spider Fang Dagger, Cloak of Webbing |
| Alpha Wolf | 14 | Wolf Fang Necklace, Alpha Wolf's Pelt |

### New Quests (6)
- Into the Forest (exploration)
- Wolf Hunt (repeatable)
- Spider Infestation (repeatable)
- The Spider Queen (boss)
- Alpha Challenge (boss)

---

## 📊 LEVEL SCALING IMPROVEMENTS

### EXP Curve (Smooth Scaling)
| Level Diff | EXP Multiplier |
|------------|----------------|
| +5 or more | 150% (challenging) |
| +3 to +4 | 130% |
| +1 to +2 | 115% (sweet spot) |
| Same level | 100% |
| -1 to -2 | 80% |
| -3 to -4 | 50% |
| -5 to -7 | 25% |
| -8 or more | 10% (gray) |

### Consider Command Enhanced
- Now shows mob level
- Shows exp category (gray/green/yellow/etc)
- Shows special flags (BOSS, Aggressive, Hunts)

---

## 📜 NEW QUESTS (15 total added)

### Hidden Dungeon Chain
- The Forgotten Passage → The Sewer King → Shadow Assassin → Ancient Guardian

### City Patrol
- Street Patrol (pickpockets/urchins)
- Tavern Trouble (drunk patrons)
- Rat Exterminator
- Bank Tour (tutorial)

### Forest of Shadows
- Into the Forest → Wolf Hunt
- Spider Infestation → Spider Queen
- Alpha Challenge

---

## ⚡ QUICK WINS (Late Night Pass)

### Death/Respawn Polish
- Varied death messages (5 random options)
- Level-scaled exp loss: 2% (lv1-10) → 3% (11-20) → 4% (21-30) → 5% (31+)
- Gold loss reduced: 10% → 5%
- Respawn with 25% HP/mana, 50% move (not just 1)
- Clear negative affects on death (poison, blind, stun, etc.)
- Death counter tracking (player.deaths)
- Respawn at recall point (not always temple)

### Universal Rare Drops
- All mobs now have 5-15% chance to drop consumables
- Drops scale with mob level: healing pots, mana pots, food
- Stacks with existing loot tables

### Tutorial NPC AI
- Added "guide" personality for temple guide
- Explains basics: look, score, inventory, combat, bank location
- Encourages exploration, warns about dangers

### More Mob Variety (5 new mobs)
| Mob | Level | Location |
|-----|-------|----------|
| Street Urchin | 2 | Poor Alley |
| Stray Dog | 1 | Poor Alley |
| Drunk Patron | 3 | Grubby Inn |
| Pickpocket | 5 | Dark Alley |
| Large Rat | 1 | Hidden Passage |

---

## 🏰 HIDDEN DUNGEON + BOSS ENCOUNTERS

### The Forgotten Passage (Hidden Area)
Access: `search` in Common Square → find trapdoor → `open trapdoor` → `down`

**Rooms:**
- The Forgotten Passage (3074) - Entry
- The Sewer King's Domain (3075) - Boss #1
- The Shadow Crossing (3076) - Boss #2  
- The Guardian's Vault (3077) - Final Boss + Treasure

### Boss Mobs
| Boss | Level | HP | Loot |
|------|-------|-----|------|
| Sewer King | 15 | ~200 | Bone Scepter, Rat Crown, Plague Ring |
| Shadow Assassin | 20 | ~160 | Shadow Dagger, Shadow Cloak, Silent Boots |
| Ancient Guardian | 25 | ~300 | Runic Hammer, Stone Shield, Ancient Amulet |

### Boss Loot (9 new items)
- **Sewer King's Scepter** (3d5+4 mace, +3 dam, +2 hit)
- **Crown of the Rat King** (+2 CHA, -10 AC)
- **Ring of Pestilence** (+2 CON, -5 saves)
- **Shadowsteel Dagger** (2d6+5, +4 hit, +3 dam, +1 DEX)
- **Cloak of Shadows** (-15 AC, +2 DEX)
- **Boots of Silent Step** (+2 DEX, +25 move)
- **Guardian's Runic Hammer** (4d5+6, +5 dam, +3 hit, +2 STR)
- **Runic Stone Shield** (-20 AC, +2 CON, -8 saves)
- **Amulet of the Ancients** (+3 INT, +3 WIS, +50 mana, -10 saves) ⭐ RARE

---

## 🛒 EXPANDED SHOP INVENTORIES

### New Consumables (9 items)
| Item | Type | Effect |
|------|------|--------|
| Meat Pie | Food | +12 hunger |
| Cheese Wheel | Food | +18 hunger |
| Apple | Food | +6 hunger |
| Fine Wine | Drink | Wine, 6 drinks |
| Healing Potion | Potion | Cure Light |
| Mana Potion | Potion | Restore Mana |
| Torch | Light | 24 hours |
| Rope | Tool | Utility item |
| Bandages | Tool | Wound care |

### Shop Updates
- **Wizard** now sells: Healing potions, Mana potions, Torches
- **Baker** now sells: Bread, Meat pies, Cheese, Apples
- **Grocer** now sells: Waterskins, Wine bottles

---

## 🐾 PET SYSTEM ENHANCEMENTS

### Pet Grouping
- Pets now display in `group` command under their owner
- Solo players with pets see a "Your Party" display
- Group heals (`group heal` spell) now heal pets in the room too

### Pet Orders (already in code, now documented)
- **Positions:** sit, stand, sleep, rest
- **Movement:** order north/south/east/west/up/down
- Standing up resumes following; sleeping stops following

### Pet Command Enhanced
- `pet` now shows detailed status: HP, level, loyalty, position, time left
- Shows pet location if not in your room
- Status shows guarding/fighting/staying state

### Help Entries
- Added comprehensive `help order` with all actions
- Updated `help pet` with detailed info

---

## ✨ POLISH PASS (Combat + AI + QoL)

### Combat Polish
- Added **bystander combat messages** for hits and misses
- Hunting AI now displays **"gives up"** when grudges expire
- Door chase feedback (rattles locked doors / pushes closed doors)

### AI Polish
- `ai on|off` toggle per player
- `chathistory <npc>` command
- `chat <npc> reset` clears conversation
- AI toggle shown in `settings` and `toggle`

### Prompt & UI
- Prompt can be toggled `prompt on|off`
- Added percent codes: `%p` HP% / `%q` Mana% / `%r` Move%
- Autoexit only shows exits on room entry when enabled
- `look` always shows exits (forced)

### Communication QoL
- `norepeat` now applies to say/shout/tell/gossip/auction/grats/holler
- `noshout` blocks shout/gossip/auction/grats/holler
- `notell` blocks tells cleanly

### Hunger/Thirst Penalties
- Regen penalties at low hunger/thirst (HP/Mana/Move)

### World Polish
- Added **stone fountain** in Market Square
- Added **Temple Guide** NPC in Temple (new player help)
- Added **Bank Teller** NPC in bank
- Grocer sells waterskins; Baker sells bread

### Testing Polish
- Test suite supports `--smoke`
- Test results logged to `logs/tests.log`

---

## 🎯 NPC HUNTING SYSTEM (New)

### Overview
NPCs can now hunt players who attack them, tracking them through rooms within their zone.

### Mob Flags
| Flag | Behavior |
|------|----------|
| `hunter` | Tracks attackers up to 5 rooms |
| `tracker` | Tracks attackers up to 10 rooms |
| `boss` | Tracks up to 15 rooms, can bash through closed doors |
| `sentinel` | Never moves (existing) |

### Mechanics

**Grudge System:**
- Mobs remember who attacked them and how much damage
- Grudges last 5 minutes
- Highest-damage attacker becomes primary target

**Hunting Behavior:**
- Mobs use BFS pathfinding to track targets
- Respects zone boundaries (bosses can cross)
- Respects closed doors (bosses can smash through)
- Won't enter `no_mob` flagged rooms
- 2-tick cooldown between moves

**Door Strategy:**
- Closed doors block regular hunters
- Locked doors block all mobs
- Bosses can smash through closed (unlocked) doors
- Players can use doors tactically to escape

**Messages:**
```
"The orc warrior stalks north, hunting for prey."
"The orc warrior arrives from the south, eyes searching!"
"The orc warrior snarls and attacks Sorin!"
"The dragon smashes through the wooden door!"
```

### Zone Containment
- Regular mobs stay in their home zone
- Bosses can pursue across zone boundaries
- Mobs won't chase into safe rooms

---

## 🔮 FUTURE CONSIDERATIONS

### Not Yet Built (Intentionally Deferred)
- Mail system
- Crafting system
- Fishing
- Reputation/Faction system
- Leaderboards

### AI Expansion Possibilities
- Dynamic quest generation
- Combat narration mode
- Procedural dungeon descriptions
- NPC memory persistence

---

---

## ⚖️ COMBAT BALANCE AUDIT & FIXES (Evening Pass)

### Critical Bug: Defense Formula Inverted
**Problem:** The defense formula was `10 + (AC // 10)`, which made lower AC (better armor) EASIER to hit.

**Fix:** Changed to `10 - (AC // 10)` in all three locations:
- `one_round()` main combat
- `pet_attack()` pet combat
- `bonus_attack()` multi-attack combat

### Critical Bug: Mob Damage Values (CircleMUD Conversion Error)
**Problem:** Damage dice from CircleMUD conversion were completely broken:
- Wolf (L4): `1d12+47` → 48-59 avg damage (instant kill!)
- Cityguard (L10): `1d12+123` → ~130 avg damage
- Mercenary (L5): `2d6+60` → ~67 avg damage
- Green Blob (L20): `1d11+325` → ~331 avg damage

**Fixed Mobs (Zone 030):**
| Mob | Level | Old Damage | New Damage |
|-----|-------|------------|------------|
| Wolf | 4 | 1d12+47 | 1d4+2 |
| Janitor | 1 | 2d6+10 | 1d3 |
| Fido | 1 | 1d6+4 | 1d2 |
| Mercenary | 5 | 2d6+60 | 1d6+3 |
| Drunk | 2 | 2d6+22 | 1d4+1 |
| Beggar | 1 | 2d6+10 | 1d3 |
| Odif | 1 | 1d6+4 | 1d2 |
| Cityguard (x2) | 10 | 1d12+123 | 1d8+5 |
| Peacekeeper | 17 | 5d6+225 | 2d6+10 |
| Green Blob | 20 | 1d11+325 | 2d6+12 |
| Waiter | 5 | 6d10+390 | 1d4+2 |

### EXP Values Fixed
Mobs now give level-appropriate EXP instead of flat 8 EXP:
| Level | Old EXP | New EXP |
|-------|---------|---------|
| 1 | 8 | 10-15 |
| 5 | 8 | 50 |
| 10 | 8 | 150 |
| 17 | 8 | 300 |
| 20 | 8 | 450 |

### Balance Fix Script Created
`scripts/fix_mob_balance.py` - Analyzes and fixes mob damage/exp across all zones:
- Detects broken damage dice patterns
- Applies level-appropriate formulas
- Preserves shopkeeper godmode (30000 damage)
- Dry-run mode for safety

**Expected Damage Formula:**
- L1-5: 1d4 + level/2
- L6-10: 1d6 + level*0.8
- L11-15: 1d8 + level
- L16-20: 2d6 + level*1.2
- L21-25: 2d8 + level*1.5
- L26-30: 3d6 + level*1.8

### Documentation
- Created `docs/COMBAT_BALANCE_AUDIT.md` with full analysis
- Documented shopkeeper godmode as intentional (30000 damage)
- Testing checklist for post-fix verification

---

## 🌌 NIGHT IMPROVEMENTS (Late Session)

### Ambient Message System (NEW)
- Added `src/ambient.py` with 50+ flavor messages by:
  - Sector type (city, forest, desert, etc.)
  - Time of day (dawn, noon, dusk, night)
  - Weather (rain/storm)
  - Danger/peaceful states
- Integrated into main tick loop (every 10s, 3% chance per player)

### Tips System (NEW)
- Added `src/tips.py` with 60+ helpful tips
- Hooks:
  - On level-up
  - On first few deaths

### Achievements Command Upgrade
- `achievements` now shows:
  - Total points + earned count
  - Progress stats (kills / rooms / secrets)
- `achievements progress` shows next milestones
- `achievements all` lists unearned achievements

### Combat Balance Script (GLOBAL FIX)
- Ran `scripts/fix_mob_balance.py --apply`
- **384 / 606 mobs fixed** across all zones
- Damage/HP/EXP now scale reasonably by level

---

## 🎯 SERVER INFO

- **Connect**: `nc 72.35.132.11 4000`
- **Web Map**: `http://72.35.132.11:4001`
- **Starting Room**: Temple of Midgaard (3001)
