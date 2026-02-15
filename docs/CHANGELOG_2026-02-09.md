# Changelog — 2026-02-09

## Major Session: Bug Fixes, New Zones, QoL Improvements

### Critical Bugs Fixed
- **Zone reset timing**: world_builder set lifespan in minutes but zone_reset_tick treated as 15-min ticks. Fresh zones reset every 7.5 hours instead of 30 min. Fixed all lifespan values to tick units.
- **Slay command**: handle_death args swapped — created corpse of immortal instead of victim.
- **Mob respawn**: Codex added home_room counting + max_existing zone-wide cap (wandering mobs no longer cause duplicate spawns).
- **Fountain missing**: vnum 3035 referenced but never defined. Players couldn't drink in Temple Square.
- **Starter equipment**: 19 of 22 equipment objects (vnums 30-51) didn't exist. _give_starting_equipment silently failed. All items now in PRESET_OBJECTS with fallback.
- **Fido aggressive**: Fido (vnum 3062) was aggressive + max 15 per room. Changed to scavenger, max 1.
- **Broken exits**: Fixed all 21 broken exits across the world, created 15 missing rooms with proper names.
- **Brief mode truncation**: 200 char limit cut room descriptions mid-sentence. Raised to 500.

### New Content
- **Sage Aldric** (vnum 3200): NPC in Temple, greets players under level 5 who haven't done tutorial_1_awakening.
- **Immortal character "Deckard"**: Created for Michael on account deckard (is_admin=true).
- **Paladin Guild**: Rooms 3085-3086, west of Training Grounds. Moved paladin trainer from Temple Altar.
- **The Great Northern Forest** (zone 180): 26 rooms, levels 8-15. Buffer zone north of Midgaard.
- **The Frostspire** (zone 190): 27 rooms, levels 15-30. Frozen mountain with 2 bosses (Frozen Dwarven King lv28, Vyrkothas the Frost Wyrm lv30).

### QoL
- Patrol AI: 15-30 sec cooldown between moves (was every tick = 10x/sec)
- AI action rates reduced (30%→5% controller, 10%→2% fallback)
- Immortal zones locked (imm_only flag)
- City aggro: mobs won't attack players 5+ levels below them
- drink command auto-targets fountains when no args given
- Port reuse_address on all servers for clean restarts
- Save format uses reset_time (seconds) for unambiguous zone timing

### Evening Session: Combat Balance, Shops, Pets & Rent

#### Mob Rebalance (369 mobs across 39 zones)
- **Castle Apocalypse (zone 220)**: Massive buffs — Death HP ~1,350→~15,000 (AC -50, 50K EXP), Kirgan ~1,280→~12,000, War/Pestilence/Famine scaled similarly, Gate Guardians to ~8,000 HP
- **Plane of Eternal Chaos (zone 160)**: All 11 mobs ~2x HP. Kaleidos: ~925→~8,000 HP
- **Necropolis (zone 140)**: 11 mobs buffed. Verdraxx→~6,000 HP
- **Dragon's Domain (zone 80)**: Scorathax→~8,000 HP
- **Great Pyramid (zone 53)**: Aurexus→~5,000, Sphinx→~4,000, Ramses→~3,000
- **Thalos (zone 52)**: Beholder ~767→~5,000 HP
- **Tunnel of Sticks (zone 210)**: Scaled appropriately
- Newbie zones (186) and Light Forest (60) left untouched
- Shopkeepers and unkillable NPCs preserved

#### Vendetta Skill Fix (3 bugs)
- `cmd_vendetta` now routes assassins with `vendetta_assassin` skill to `cmd_vendetta_assassin`
- Added `vendetta_target`/`vendetta_bonus` damage check in combat damage calculation
- Added `vendetta_ticks` decrement with expiration message

#### NPC Keyword Expansion
- `apply_prototype` generates keywords from name, short_desc, AND long_desc (stop-word filtered)
- Supports explicit `keywords` array from zone JSON
- Room display shows `(mob_name)` hint after long_desc for targeting

#### Invalid Exit Directions Fixed
- Converted 11 non-standard exits (out, gate, portal, inside, outside, northwest, southeast) to valid 6-direction exits across zones 030, 160, 180, 190

#### Boss Combat Crash Fix
- `AchievementManager._award_async` → `AchievementManager.unlock` in combat.py

#### Zone 190 Equipment Overhaul
- 7 new objects (vnums 19040-19046), mob equipment dicts, obj_resets in 9 rooms
- Light sources, readable text, wear_flags → wear_slot mapping fix

#### Watercraft System
- 3 tiers: wooden raft (50%, vnum 60), birch canoe (70%, vnum 61), elven skiff (90%, vnum 62)
- Inventory-based — no equip needed. No sneaking on water sectors.

#### Castle Apocalypse Death Trail
- Rebuilt 14-room path (22100→22114) with bidirectional exits
- 5 deathtraps preserved as clearly-warned side exits

#### Exit Descriptions (All Zones)
- 3,559 exit descriptions generated across 37 zone files
- 39 deathtrap warning descriptions added

#### Look Numbered Targeting
- `do_look` supports `look 2.guardian` syntax

#### Web Map Enhancements
- Zone filter sidebar, portal markers (🌀), mini-overview canvas, cross-zone connection lines

#### Shops, Pets & Rent System
- 77 new items stocked across all shops (weapons by tier, armor sets, potions/scrolls, food, supplies)
- 7 new pets in pet store (tabby cat through dire wolf)
- Rent system at innkeeper: pricing by item rarity (Common 10g → Legendary 5,000g/day)
- Baker mob_reset fixed (wasn't spawning)
- All shopkeepers given 100K-500K gold

#### Comprehensive World Polish Pass

**Containers + Locks + Keys:**
- 72 containers created across 21 zones (locked treasure chests, weapon racks, caches)
- ~50 keys created, placed in boss/elite mob inventories
- 96 items moved from bare ground into thematic containers
- 12 locked doors on boss rooms (Dragon's Lair, Pyramid, Frostspire, Necropolis, Apocalypse, Moria)
- Container themes match zones (frost-rimed strongboxes, sandstone coffers, etc.)

**Zone Quest Givers:**
- 15 thematic quest NPCs placed across all major zones
- 27 quests reassigned from Captain/Mayor to zone-appropriate NPCs
- Quest Board added in Temple Square with breadcrumbs to all zone givers
- `talk` command shows flavorful NPC dialogue instead of raw quest IDs

**Object Type Audit:**
- 1,091 objects fixed from unknown type to proper types
- Correct wear_slots, damage_dice, ac_apply, and capacities set

**Zone Flavor NPCs:**
- 30 atmospheric NPCs across 18 zones (miners, ghosts, hermits, crusaders, demons, etc.)
- All with lore dialogue containing zone-appropriate hints and atmosphere
- `flavor_npc` special type with talk_responses support

**Progression Hooks:**
- 17 NPCs hint at next zones when players ask about progression
- 8 signposts at major crossroads with level recommendations
- Quest Board reorganized by difficulty tier (Beginner → Legendary)
- Sage Aldric gives level-appropriate guidance post-tutorial

#### Orphaned Rooms Fixed
- 13 unreachable rooms connected (Pet Shop Store, Odin's Store, Coliseum Gates, Mercenaries Guild, rooms in Thalos/Pyramid/High Tower/Sewers)

#### Equipment Sets (10 sets)
- Low: Miner's Garb, Forest Stalker
- Mid: Drow Shadow, Pharaoh's Legacy, Sewer Rat
- High: Dragonscale, Necromancer's Regalia, Chaos Weave
- Endgame: Apocalypse Raiment, Frostlord's Mantle
- All pieces added to zone JSONs and boss loot tables

#### Boss Phase Mechanics (11 bosses)
- Death (3 phases: death touch → undead summons → AoE death wave)
- Kirgan (2 phases: cleave → berserk shockwave)
- War, Pestilence, Famine (2 phases each)
- Scorathax (3 phases: fire breath → flight → desperate fury)
- Verdraxx (2 phases: poison → undead summons)
- Kaleidos (3 phases cycling elements)
- Master Mindflayer (2 phases: mind blast → mind control)
- Frozen Dwarven King, Vyrkothas (2 phases each)

#### Systems Wired Up
- Ambient events: sector/weather/time-aware atmospheric messages
- Tips system: contextual hints for players under level 15
- 9 factions defined with starting rep, cross-faction relationships, and rewards
- Mail system: send/read/list/delete between players (online or offline)
- Player trading: offer items, both sides accept
- Dueling: PvP to 1 HP, no death penalty, optional gold wagers

#### Playtest Bug Fixes
- **Account creation crash**: `handle_confirm_password` method collision — new char creation hit account password change handler. Renamed to `handle_confirm_new_char_password`.
- **Wielding bread**: Zone 000 objects (vnum 1=wings, 10=waybread) collided with starter equipment presets. Fixed: preset objects checked first, world objects as fallback.
- **Race/class number selection**: Menus showed numbered items but only accepted text. Now accepts both `1` and `human`.
- **Tutorial quest dump**: Talking to Aldric listed all 7 future tutorial quests. Filtered to only show current/next step.
- **Double completion banner**: Tutorial quests showed both "QUEST COMPLETE" and "TUTORIAL COMPLETE". Suppressed generic banner for tutorials.

### World Stats
- 42 zones, 2,568 rooms, 0 orphaned rooms
- 369 mobs rebalanced across 39 zones
- 10 equipment sets, 11 phased bosses, 9 factions
- 77 shop items, 7 pets, rent system
- 72 containers, 50 keys, 12 locked doors
- 15 zone quest givers, 30 flavor NPCs, 8 signposts
- 9 factions, mail/trade/duel systems
- 1,091 object types fixed
