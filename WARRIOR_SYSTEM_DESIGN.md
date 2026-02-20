# Warrior System Design - Misthollow

**Date:** 2026-02-02  
**Goal:** Give warriors tactical depth through Rage and Stance systems

---

## Core Concept: Rage & Stances

Warriors build **Rage** through combat and spend it on powerful abilities. They can also switch between **Stances** that provide different combat trade-offs.

### Rage System

```
┌─────────────────────────────────────────────────┐
│  WARRIOR RAGE SYSTEM                            │
├─────────────────────────────────────────────────┤
│  Rage: 0-100 (starts at 0)                     │
│                                                 │
│  GAIN RAGE:                                     │
│  • +5 per hit you deal                         │
│  • +10 per hit you receive                     │
│  • +2 per combat tick                          │
│                                                 │
│  SPEND RAGE:                                    │
│  • Execute (50 rage) - Powerful finisher       │
│  • Rampage (40 rage) - Multi-target attack     │
│  • War Cry (30 rage) - AoE fear/buff           │
│  • Ignore Pain (20 rage) - Damage absorption   │
│                                                 │
│  DECAY:                                         │
│  • -5 per tick out of combat                   │
│  • Resets to 0 on rest/sleep                   │
└─────────────────────────────────────────────────┘
```

### Stance System

```
┌─────────────────────────────────────────────────────────────────┐
│  WARRIOR STANCES                                                │
├─────────────────────────────────────────────────────────────────┤
│  stance battle   - Balanced (default)                          │
│  stance berserk  - +25% damage, -20 AC, +50% rage gen          │
│  stance defensive - -25% damage, +30 AC, +25% parry            │
│  stance precision - +4 hit, -10% damage, critical strikes      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Rage Abilities (4 Total)

### 1. Execute
- **Command:** `execute`
- **Rage Cost:** 50
- **Effect:** Devastating attack that deals more damage the lower the target's HP
- **Damage:** Base weapon damage × (2 + (100 - target HP%) / 20)
- **At 20% target HP:** 6x weapon damage!
- **Level:** 15

### 2. Rampage  
- **Command:** `rampage`
- **Rage Cost:** 40
- **Effect:** Attack all enemies in the room
- **Damage:** 75% weapon damage to each target
- **Bonus:** +10 rage per target hit
- **Level:** 20

### 3. War Cry
- **Command:** `warcry`
- **Rage Cost:** 30
- **Effect:** Terrifying shout that fears enemies and buffs allies
- **Fear:** Enemies save or flee for 2 ticks
- **Buff:** Allies get +2 hitroll, +1 damroll for 5 ticks
- **Level:** 10

### 4. Ignore Pain
- **Command:** `ignorepain`
- **Rage Cost:** 20
- **Effect:** Absorb the next X damage (based on level)
- **Absorb Amount:** 10 + (level × 2) damage
- **Duration:** 3 ticks or until depleted
- **Level:** 8

---

## Existing Skills (Need Implementation)

### Already Implemented
- ✅ `kick` - Basic damage
- ✅ `bash` - Damage + stun

### Need Implementation
1. **Rescue** - Pull an ally from combat, become the new target
2. **Disarm** - Knock weapon from enemy's hands
3. **Parry** - Passive chance to block attacks (stance-modified)
4. **Shield Block** - Active blocking with shield
5. **Cleave** - Attack carries to a second target on kill

---

## New Skills

### 1. Battle Shout
- **Command:** `battleshout`
- **Effect:** Short-term party buff (+2 str, +1 con)
- **Duration:** 10 ticks
- **Cooldown:** 60 seconds
- **Level:** 5

### 2. Intimidate
- **Command:** `intimidate <target>`
- **Effect:** Reduce target's attack/damage, chance to flee
- **Duration:** 4 ticks
- **Level:** 12

---

## Player Attributes (add to Player class)
```python
self.rage = 0                   # Current rage (0-100)
self.max_rage = 100             # Maximum rage
self.stance = 'battle'          # Current stance
self.ignore_pain_absorb = 0     # Damage absorption remaining
self.last_warcry = 0            # Cooldown tracking
self.last_battleshout = 0       # Cooldown tracking
```

---

## Combat Integration

### Rage Generation (in combat tick)
```python
# Per hit dealt
rage += 5

# Per hit received  
rage += 10

# Per combat tick
rage += 2

# Berserk stance bonus
if stance == 'berserk':
    rage = int(rage * 1.5)
```

### Stance Effects (in damage calculations)
```python
# Damage dealt modifier
if stance == 'berserk':
    damage = int(damage * 1.25)
elif stance == 'defensive':
    damage = int(damage * 0.75)
elif stance == 'precision':
    damage = int(damage * 0.90)
    # But +15% crit chance

# Armor class modifier
if stance == 'berserk':
    ac += 20  # Worse AC
elif stance == 'defensive':
    ac -= 30  # Better AC
```

---

## Implementation Files

1. `src/player.py` - Add rage/stance attributes, rage decay
2. `src/commands.py` - Add stance, execute, rampage, warcry, ignorepain, rescue, disarm commands
3. `src/combat.py` - Integrate rage generation, stance effects, parry checks
4. `src/config.py` - Update warrior skill list

---

## Command Summary

| Command | Type | Description |
|---------|------|-------------|
| `stance <name>` | Utility | Switch combat stance |
| `execute` | Rage (50) | High damage finisher |
| `rampage` | Rage (40) | AoE attack |
| `warcry` | Rage (30) | Fear enemies, buff allies |
| `ignorepain` | Rage (20) | Absorb damage |
| `battleshout` | Skill | Party str/con buff |
| `intimidate` | Skill | Debuff/fear single target |
| `rescue` | Skill | Save ally from combat |
| `disarm` | Skill | Remove enemy weapon |

---

*This design transforms warriors from "hit things" to tactical bruisers with resource management and meaningful choices.*
