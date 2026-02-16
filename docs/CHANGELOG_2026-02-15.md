# Changelog — 2026-02-15 (Overnight Build)

## New Systems Added

### PvP Arena (`arena.py`)
- Full opt-in PvP arena in zone 250 (The Blood Pit Arena)
- ELO-style rating system (start 1000, K=32)
- Commands: `challenge`, `arena join/leave/stats/top`
- No death on loss — loser teleported to lobby at 1 HP
- Spectator gallery, gold/point rewards
- Arena stats saved per player (wins, losses, rating, points)

### Player Housing (`housing.py`)
- Housing district (zone 260) with 20 purchasable plots
- Three sizes: Small Cottage (5k), Medium Townhouse (15k), Grand Estate (50k)
- Commands: `house buy/sell/list/info/enter/lock/unlock/invite/name/decorate/furnish/storage`
- `home` teleport command (30min cooldown)
- Persistent storage chest (max 50 items), guest lists, furniture with bonuses
- Furniture: bed (+50% HP regen), trophy case, weapon rack, bookshelf

### World Events (`world_events.py`)
- Dynamic periodic world events ticking every 30 seconds
- Event types: Invasion, World Boss, Treasure Hunt, Double XP, Dense Fog
- Double XP integrates with combat XP calculations
- Fog reduces combat accuracy
- `events` command to view active events

### Achievement System (`achievements.py`)
- Categories: combat, exploration, progression, class, social, wealth, collection
- Progress tracking with bars, unlockable titles, gold/XP/stat bonus rewards
- Integrated hooks: kill tracking, exploration, gold earned, boss kills, deathtraps
- `achievements [category]` and `title` commands

### Faction Reputation (`factions.py`)
- 8-tier reputation system (Hated → Exalted), 1000 points per tier
- Opposing faction mechanics (killing one faction hurts standing with allies)
- Shop price modifiers by reputation level
- Faction NPCs spawned on world load
- Automatic rep gain/loss on mob kills
- `faction` and `reputation` commands

### Group/Party System (`groups.py`)
- Parties up to 6 players, XP sharing (bonus for group size)
- Loot modes: free-for-all, round-robin
- Auto-follow, group chat (`gtell`), group effects
- `group` command with invite/kick/leave/list/loot subcommands

### Mob AI (`mob_ai.py`)
- Intelligent combat AI running per combat tick for fighting NPCs
- AI types: Caster, Boss, Pack, Healer, Coward
- Keyword-based classification (e.g., "wolf" → pack behavior)
- Boss ability rotations with cooldowns (AoE, enrage, summon, fear)

### Crafting System (`crafting.py`)
- Gathering skills: mining, herbalism, skinning
- Crafting skills: blacksmithing, alchemy, leatherworking
- Recipe-based crafting with material requirements
- `craft` and `gather` commands

### Collection System (`collection_system.py`)
- Track collected items and trophies
- Display cases in player housing
- `collections` command

## Integration Points Verified

### Player Save/Load
All new attributes properly included in both `save()` and `load()`:
- ✅ Arena stats (wins, losses, rating, highest_rating, points)
- ✅ Faction reputation + rewards
- ✅ Achievements + progress + available titles
- ✅ Housing (house_vnum, house_storage)
- ✅ Collections (collection_progress, collections_completed)
- ✅ Explored rooms, discovered exits, secret rooms
- ✅ Journal + lore catalog
- ✅ Warrior doctrine system (doctrine, momentum, ability_usage, evolutions)

### Combat Death Hook Order (combat.py `handle_death`)
1. Arena death intercept (no real death in arena)
2. Duel intercept (1 HP, not death)
3. Equipment → inventory for looting
4. Loot table drops
5. Double XP world event check
6. Group XP sharing (with level scaling)
7. Solo XP (with streak/rested/boss bonuses)
8. Quest progress check
9. Achievement kill tracking
10. Faction reputation changes
11. Journal bestiary entry
12. Boss achievement/title awards
13. Class-specific resource generation (soul shards, faith, luck)
14. Gold/item autoloot
15. Corpse creation
16. NPC removal from world

### Main Game Loop (main.py)
- ✅ World event tick (every 30s) properly integrated
- ✅ Mob AI called during combat tick
- ✅ All tick systems operational

### World Load (world.py)
- ✅ Faction NPCs spawned on load
- ✅ World event manager initialized after zone load
- ✅ Puzzle seeding on load

## Issues Found & Fixed

### 1. Alias Conflicts (commands.py)
**Problem:** Two alias keys collided between `ALIASES` and `COMMAND_ALIASES`:
- `bs` → `battleshout` (ALIASES) vs `backstab` (COMMAND_ALIASES)
- `mm` → `minimap` (ALIASES) vs `magic_missile` (COMMAND_ALIASES)

Since `ALIASES` is checked first, `COMMAND_ALIASES` values were unreachable.

**Fix:**
- Changed `bs` → `bsh` for battleshout in ALIASES
- Changed `mm` → `mmap` for minimap in ALIASES
- `bs` now correctly resolves to backstab, `mm` to magic_missile

### 2. Missing Help Entries (help_data.py)
**Problem:** Several new commands lacked help entries:
- `housing` (alias for house)
- `events` (world events viewer)
- `furnish` (alias for house furnish)

**Fix:** Added help entries for all three.

## No Issues Found (Verified Clean)

- ✅ All 60 `.py` files compile without syntax errors
- ✅ No circular imports detected (all cross-module imports are inside functions)
- ✅ No duplicate `cmd_` method names in commands.py
- ✅ All module imports in world.py/main.py use try/except or lazy imports
- ✅ Player `__init__` initializes all new attributes with safe defaults
- ✅ Arena, housing, factions, achievements all use lazy imports (no startup crash risk)
- ✅ Mob AI properly guarded with try/except in combat tick
- ✅ World event manager null-checked before tick calls

## Wave 5-6: Auction House, Prestige, Social, Dungeons, Overworld, Emotes, Legendaries

### New Systems
- **Auction House** — player-to-player trading with fixed-price and auction bidding
- **Prestige Classes** — level 30+ specializations with unique abilities
- **Social System** — friends list, ignore, player notes, chat channels (global/newbie/trade/lfg)
- **Mid-Level Dungeons** — new dungeon content for levels 10-25
- **Overworld Travel** — waypoint discovery and fast-travel system
- **Emotes** — social emotes and expressions
- **Legendary Items** — rare endgame drops with set bonuses

### Tutorial Update
- Auto-completion of tutorial quests on objective fulfillment
- Compass sense hints after movement commands
- Auto-hint system for stuck players (5 min no progress)

### QA Pass (Wave 5-6)
- ✅ All 58 .py files compile clean (`py_compile`)
- ✅ `main.py` imports all modules without errors
- ✅ Fixed duplicate aliases: `tr` (track→tra), `fi` (fish→fis)
- ✅ Fixed broken alias targets: `hold`→wield, `fb`/`mm`→cast, removed stale `shadow_step` alias
- ✅ Player save/load covers all new attributes (prestige, arena, crafting, social, warrior doctrine)
- ✅ Added 17 missing help entries (accept, decline, duel, lfg, mail, newbie, prestige, respec, specialize, slip, trade, unignore, use, vnums, wevent, whois, shadowstep_talent skipped—internal)
