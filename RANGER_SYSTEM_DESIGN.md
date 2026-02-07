# Ranger System Design - RealmsMUD

**Date:** 2026-02-02  
**Goal:** Give rangers their core identity: Animal Companions + Tracking

---

## Core Concept: Beast Master + Hunter

Rangers bond with animal companions and track prey across the wilderness.

### Animal Companion System

```
┌─────────────────────────────────────────────────┐
│  RANGER COMPANION SYSTEM                        │
├─────────────────────────────────────────────────┤
│  companion         - View companion status      │
│  tame <animal>     - Tame a wild beast         │
│  dismiss           - Release companion         │
│  command <action>  - Direct companion          │
│                                                 │
│  COMPANION TYPES:                               │
│  • Wolf - Balanced damage + trip attack        │
│  • Bear - High HP tank + maul                  │
│  • Hawk - Fast + flyby attack + scouting       │
│  • Cat - Stealth + pounce + bleed              │
│  • Boar - Charge + stun                        │
└─────────────────────────────────────────────────┘
```

### Tracking System

```
┌─────────────────────────────────────────────────┐
│  TRACKING SYSTEM                                │
├─────────────────────────────────────────────────┤
│  track <target>    - Begin tracking             │
│  scan              - Check for nearby creatures │
│                                                 │
│  While tracking:                                │
│  • Shows direction to target                   │
│  • Reveals hidden paths                        │
│  • Bonus damage vs tracked target              │
└─────────────────────────────────────────────────┘
```

---

## Animal Companions (5 Types)

### 1. Wolf
- **Stats:** HP: 80%, Damage: 100%, Speed: Fast
- **Special:** Trip Attack - Chance to knock down target
- **Personality:** Loyal, pack hunter
- **Level:** 5

### 2. Bear  
- **Stats:** HP: 150%, Damage: 80%, Speed: Slow
- **Special:** Maul - Heavy damage + bleed
- **Personality:** Protective, tank
- **Level:** 10

### 3. Hawk
- **Stats:** HP: 50%, Damage: 60%, Speed: Very Fast
- **Special:** Flyby - Attack without retaliation, Scout ahead
- **Personality:** Alert, evasive
- **Level:** 8

### 4. Cat (Panther/Lion)
- **Stats:** HP: 70%, Damage: 120%, Speed: Fast
- **Special:** Pounce - Bonus damage from stealth, Bleed DOT
- **Personality:** Stealthy predator
- **Level:** 12

### 5. Boar
- **Stats:** HP: 120%, Damage: 90%, Speed: Medium
- **Special:** Charge - Stun on engage
- **Personality:** Aggressive, tough
- **Level:** 7

---

## Ranger Skills

### New Skills (Need Implementation)

#### 1. Tame
- **Command:** `tame <animal>`
- **Effect:** Attempt to tame a wild beast as companion
- **Requires:** Animal must be beast type, non-hostile, alone
- **Success:** Based on skill level and animal difficulty
- **Level:** 5

#### 2. Track  
- **Command:** `track <target>`
- **Effect:** Begin tracking a creature type or specific mob
- **Tracking shows:** Direction hints ("tracks lead north")
- **Bonus:** +15% damage vs tracked target
- **Level:** 3

#### 3. Scan
- **Command:** `scan`
- **Effect:** Detect creatures in adjacent rooms
- **Range:** 1-3 rooms based on skill level
- **Reveals:** Hidden creatures, number of enemies
- **Level:** 1

#### 4. Camouflage
- **Command:** `camouflage`
- **Effect:** Enhanced hide that works better outdoors
- **Bonus:** +30% hide success in wilderness sectors
- **Level:** 8

#### 5. Ambush
- **Command:** `ambush <target>`
- **Effect:** Attack from stealth with bonus damage
- **Requires:** Hidden + target not in combat
- **Damage:** 2.5x weapon damage
- **Level:** 10

### Existing Skills (Shared)
- ✅ `sneak` - Already implemented
- ✅ `hide` - Already implemented
- ❌ `dual_wield` - Not implemented yet

---

## Companion Commands

```
companion              - Show companion status
companion attack       - Order attack on current target
companion defend       - Defend the ranger (taunt)
companion stay         - Stay in current room
companion follow       - Follow ranger (default)
companion heel         - Return to ranger's side
dismiss                - Release companion back to wild
```

---

## Player Attributes
```python
self.animal_companion = None     # Companion Mobile object
self.companion_type = None       # 'wolf', 'bear', etc.
self.tracking_target = None      # Mob type being tracked
self.tracking_direction = None   # Last known direction
self.last_scan = 0               # Cooldown tracking
```

---

## Implementation Plan

1. **Companion data structure** (in pets.py or new companions.py)
2. **Tame command** - Check beast type, skill check, create companion
3. **Companion AI** - Fight alongside ranger, use special abilities
4. **Track command** - Set tracking target, show directional hints
5. **Scan command** - Reveal nearby creatures
6. **Camouflage/Ambush** - Enhanced stealth combat

---

## Companion Special Abilities (Auto-Use)

Each companion has a special ability that triggers automatically:

| Companion | Ability | Trigger | Effect |
|-----------|---------|---------|--------|
| Wolf | Trip | 20% on hit | Target falls, -1 tick of attacks |
| Bear | Maul | 25% on hit | Extra damage + 3-tick bleed |
| Hawk | Flyby | Always | Can't be counter-attacked |
| Cat | Pounce | From stealth | 2x damage first hit |
| Boar | Charge | On engage | Stun for 1 tick |

---

*This design gives Rangers their D&D/WoW beast master fantasy with meaningful companion choice and tracking utility.*
