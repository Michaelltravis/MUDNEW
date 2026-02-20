# Misthollow Changelog - February 6, 2026

## UX / QoL
- **Autoexit** now persists and defaults **ON** (exits show on room entry).
- **Drink containers**: `look` / `look in` shows liquid + fullness.
- **Fill** now correctly refills drink containers (drinks/max_drinks/liquid).
- **Drink behavior**: if a fountain is present, `drink` uses it by default; `drink <container>` forces container.

## Stealth / Backstab System
- **Backstab wind‑up**: 1–4s prep with spinner indicator.
- **Backstab cooldown**: 6s.
- **Sneak/Hide/Environment** now factor into **backstab success + damage**.
- **Detection roll** vs target perception can reduce success/damage.
- **Rare execution proc** (non‑boss) can one‑shot on successful backstab.

## Sneak Detection / Tracking
- **Room‑entry detection** uses Sneak + ½ Hide + environment + light penalty.
- **Exposed** debuff now triggers on detection (10–30s).
- **NPC searching/tracking**: detected NPCs follow for 10–20s (adjacent rooms).
- **Tracking clears** when timer expires.

## Pets
- **Recall pulls pets with you**; pets resume following on arrival.
- **Order recall** added for pets.

## Class Trainers / Rooms
- **Trainer rooms are class‑locked** (auto‑applied to all trainer rooms).
- **Thieves’ guildmaster** trains **thief + assassin**.

## Help / Documentation
- Rebuilt **all** help topics (commands/skills/spells/classes).
- Added comprehensive skill/spell lists to every class help.
- Generated **docs/HELP.md** to preserve full help content.

---

## 🎮 LEVEL 60 EXPANSION - Major Content Update

### Level Cap Increased to 60
- **MAX_MORTAL_LEVEL** increased from 50 to 60
- **XP Curve Changes:**
  - Levels 1-30: Standard progression (1.4x multiplier)
  - Levels 31-60: Slower progression (1.6x multiplier) for extended endgame

### New Abilities: 54 Total (6 per class)
Every class gains 5 new abilities at levels 32, 38, 44, 50, and 56, plus a **CAPSTONE ability at level 60**.

#### 🗡️ Warrior (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Rallying Cry** | Party buff: +Max HP, 2min CD |
| 38 | **Shattering Blow** | Armor penetration strike, 15s CD |
| 44 | **Commanding Shout** | AoE taunt, 30s CD |
| 50 | **Heroic Leap** | Gap closer + stun, 45s CD |
| 56 | **Warpath** | Sustained damage mode (+15 dam, haste), 3min CD |
| 60 | **Titan's Wrath** | 💀 CAPSTONE: 10s invuln + 2x damage + AoE cleave, 10min CD |

#### 🔥 Mage (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Mana Shield** | Absorb damage with mana |
| 38 | **Time Warp** | Haste party, 5min CD |
| 44 | **Arcane Explosion** | Massive AoE, 30s CD |
| 50 | **Icy Veins** | +30% crit + haste, 3min CD |
| 56 | **Combustion** | Guaranteed fire crits, 3min CD |
| 60 | **Meteor Storm** | 💀 CAPSTONE: Massive AoE + stun + ground burn, 10min CD |

#### ✝️ Cleric (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Prayer of Mending** | Bouncing heal (3 jumps), 15s CD |
| 38 | **Spirit Link** | Share HP with party, 2min CD |
| 44 | **Mass Dispel** | Remove all debuffs from allies, 1min CD |
| 50 | **Lightwell** | Sustained area heal, 3min CD |
| 56 | **Serenity** | Full single-target heal, 3min CD |
| 60 | **Divine Intervention** | 💀 CAPSTONE: Full party heal + rez + immunity, 10min CD |

#### 🗡️ Thief (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Nerve Strike** | Paralyze target, 30s CD |
| 38 | **Shadow Dance** | Use stealth abilities in combat |
| 44 | **Garrote** | Silence + bleed from stealth, 20s CD |
| 50 | **Evasion** | 100% dodge for 10s, 3min CD |
| 56 | **Marked for Death** | +50% damage to target, 1min CD |
| 60 | **Perfect Crime** | 💀 CAPSTONE: 30s perma-stealth + guaranteed crits, 10min CD |

#### 🏹 Ranger (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Volley** | AoE arrow rain, 20s CD |
| 38 | **Camouflage** | Superior stealth, 30s CD |
| 44 | **Serpent Sting** | Strong poison DoT, 15s CD |
| 50 | **Rapid Fire** | 5-7 rapid arrows, 1min CD |
| 56 | **Kill Command** | Pet execute (2x if <35% HP), 45s CD |
| 60 | **Alpha Pack** | 💀 CAPSTONE: Summon ALL 5 pets in frenzy, 10min CD |

#### ⚔️ Paladin (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Hand of Freedom** | Remove CC, 30s CD |
| 38 | **Consecration** | Holy ground damage, 20s CD |
| 44 | **Hammer of Justice** | Ranged stun, 45s CD |
| 50 | **Avenging Wrath** | +damage/healing + wings, 3min CD |
| 56 | **Divine Shield** | Complete immunity, 5min CD |
| 60 | **Crusader's Judgment** | 💀 CAPSTONE: Holy nuke + party invuln + mass rez, 10min CD |

#### 💀 Necromancer (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Death Coil** | Damage OR heal undead, 12s CD |
| 38 | **Corpse Shield** | Pet absorbs 50% damage, 1min CD |
| 44 | **Plague Strike** | Spreading disease, 20s CD |
| 50 | **Summon Gargoyle** | Flying pet, 3min CD |
| 56 | **Soul Harvest** | Massive essence gain, 2min CD |
| 60 | **Apocalypse** | 💀 CAPSTONE: Raise EVERY corpse in zone, 10min CD |

#### 🎵 Bard (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Hymn of Hope** | Mana regen aura, 1min CD |
| 38 | **Chord of Disruption** | AoE silence, 45s CD |
| 44 | **Epic Tale** | +3 ALL stats for party, 2min CD |
| 50 | **Siren Song** | Mass charm, 90s CD |
| 56 | **Requiem** | Damage over time aura, 2min CD |
| 60 | **Magnum Opus** | 💀 CAPSTONE: All songs active + massive buffs, 10min CD |

#### 🔪 Assassin (Level 31-60)
| Level | Ability | Description |
|-------|---------|-------------|
| 32 | **Shadowstrike** | Teleport + backstab, 20s CD |
| 38 | **Fan of Knives** | AoE poison, 15s CD |
| 44 | **Rupture** | Massive bleed, 20s CD |
| 50 | **Shadow Blades** | +20 damage dual shadow weapons, 2min CD |
| 56 | **Vendetta** | 2x damage to marked target, 2min CD |
| 60 | **Death Mark** | 💀 CAPSTONE: Instant kill if <25% HP, 10min CD |

### Technical Changes
- Modified `src/config.py`: Added HIGH_LEVEL_EXP_MULTIPLIER (1.6) and HIGH_LEVEL_THRESHOLD (30)
- Modified `src/player.py`: Updated exp_to_level() with tiered progression
- Modified `src/spells.py`: Added 30+ new spells for levels 31-60
- Modified `src/commands.py`: Added 20+ new skill commands for levels 31-60
- Modified `src/help_data.py`: Added comprehensive help entries for all new abilities
- Updated class definitions in config.py to include new abilities in skill/spell lists

### Balance Notes
- Level 60 capstone abilities have 10-minute cooldowns
- These are designed to be **powerful but rare** - one use per major fight
- Mid-tier abilities (32-56) have 15s-3min cooldowns for regular use
- High-level abilities scale with player level for continued relevance

---

## 🗺️ WEB MAP POLISH - Visual Overhaul

### Quick Wins
- **Rounded room corners** with drop shadows for depth
- **Pulsing player indicator** with animated glow effect
- **Hover tooltips** showing room name, sector type, and available exits
- **Smooth zoom/pan** with lerp easing transitions
- **Enhanced color palette** per sector type (forest=green, water=blue, etc.)
- **HiDPI/Retina support** for crisp rendering on high-DPI displays
- **Viewport indicator** on minimap showing current view area

### Major Features
- **Emoji Room Icons**: Visual indicators for room types
  - 🏛️ City/Temple | 🌲 Forest | 🌊 Water | ⛰️ Mountain
  - 🛒 Shop | 👹 Boss | 💀 Danger | 🏠 Inn
  - 🚰 Sewer | 🦇 Cave | ⛏️ Mine | ⚰️ Crypt | 🕳️ Tunnel
- **Animated Fog of War**: Unexplored rooms dimmed, radial reveal animation
- **Path Highlighting**: Right-click destination → green path shown with distance
- **Zone Boundaries**: Colored dashed outlines per zone, zone labels in sidebar
- **One-Way Exits**: Orange arrows indicating direction, two-way = purple gradient
- **Up/Down Indicators**: Cyan ↑ (top-right) and Red ↓ (bottom-right) badges

### Toggle Controls
- Icons on/off
- Fog of war on/off  
- Zone boundaries on/off
- Minimap on/off

### Bug Fixes
- **Fixed disconnected map components**: `offset_x` now calculated after player BFS
- **Fixed up/down exit badges**: Were showing on wrong rooms due to coordinate bug

---

## 🎮 LEVELS COMMAND UPDATE

### Changes
- Now displays all 60 levels (was showing only 50)
- Uses correct tiered XP formula:
  - Levels 1-30: `BASE_EXP × 1.4^(level-1)`
  - Levels 31-60: `level_30_xp × 1.6^(level-30)`
- Color-coded by tier:
  - White: 1-10 | Green: 11-20 | Cyan: 21-30
  - Yellow: 31-40 | Magenta: 41-50 | Red: 51-60
- Shows `<-- YOU` marker at current level

---

## 🧪 TEST CHARACTER: Avikan

### Level 60 Assassin (Account: sorin)
Created for testing endgame content.

**Stats:**
- Level 60 | 650 HP | 200 Mana | 400 Move
- STR 18 | INT 14 | WIS 12 | DEX 25 | CON 18 | CHA 14
- AC -100 | Hitroll +35 | Damroll +40
- 5,000,000 XP | 500,000 Gold

**Equipment: Shadowdancer Set (set_id 600)**
- Fang of the Void (4d8+10 pierce) - main hand
- Soul Reaver (4d6+8 pierce) - off hand
- Full 14-piece armor set with +DEX, +hitroll, +damroll bonuses

**Skills:** All assassin skills at 100%
**Talents:** 51 points spent across all 3 trees (maxed)

---

## 🔧 BUG FIXES

### Player Loading
- **Fixed**: `fromisoformat` crash when `last_logout` was null
- Player files now require valid datetime strings for all date fields

### Map System
- **Fixed**: Disconnected map components overlapping at (0,0,0)
- **Fixed**: Up/down exit indicators showing on wrong rooms

---

## 📊 COMBAT GAP ANALYSIS

### What's Implemented ✅
- Basic attack loop with hit/miss/damage
- Armor Class (AC) affecting hit chance
- Avoidance (dodge, parry, block, riposte)
- Multi-attack (second, third attack based on skill)
- Critical hits with multiplier
- Pet/companion combat with assist
- All 9 class resource systems:
  - Warrior: Rage + Stances
  - Thief: Combo Points
  - Cleric: Divine Favor
  - Paladin: Holy Power + Auras
  - Necromancer: Soul Essence + Undead pets
  - Ranger: Focus + Animal companions
  - Bard: Rhythm + Songs
  - Mage: Mana + Arcane Charges
  - Assassin: Combo Points + Poisons

### Gaps Identified 🔴

**Priority 1 - Core Mechanics:**
- Damage types (physical, fire, cold, etc.)
- Resistances/vulnerabilities per damage type
- Threat/aggro table for tank mechanics
- Interrupt/counterspell system
- Crowd control diminishing returns

**Priority 2 - Quality of Life:**
- `cooldowns` command to show active CDs
- Combat log with damage breakdown
- Target lock system
- Improved assist command

**Priority 3 - Class Abilities:**
- Warrior: Charge, Shield Wall, Execute
- Mage: Polymorph, Counterspell, Blink
- Thief: Traps, Blind, Distract
- Ranger: Freezing Trap, Misdirection
- Various missing utility spells

**Priority 4 - Boss Mechanics:**
- Phase transitions
- Telegraphed attacks
- Add spawning
- Positioning requirements
- Enrage timers

---

## 📈 WORLD STATISTICS

| Metric | Count |
|--------|-------|
| Zones | 40 |
| Rooms | 2,498 |
| Mobs | 670 |
| Objects | 1,101 |
| Spells | 156 |
| Help Topics | 500+ |
| Max Level | 60 |

### Server Access
- **Telnet**: `nc 72.35.132.11 4000`
- **Web Map**: `http://72.35.132.11:4001?player=Name`
- **Web Client**: `http://72.35.132.11:4003`
- **Admin Login**: deckard / `gnrl dyks gpnv kmbz`

### Restart Command
```bash
pkill -9 -f "main.py"; sleep 2; nohup python3 src/main.py > server.log 2>&1 &
```
