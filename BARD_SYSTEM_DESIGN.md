# Bard System Design - RealmsMUD

**Date:** 2026-02-02  
**Goal:** Give bards a unique, engaging song-based identity

---

## Core Concept: Performance System

Bards channel songs as **ongoing performances**. While performing, the song provides effects to allies/enemies in the room. Performances drain mana over time and can be interrupted.

### Performance Mechanics

```
┌─────────────────────────────────────────────────┐
│  BARD PERFORMANCE SYSTEM                        │
├─────────────────────────────────────────────────┤
│  perform <song>     - Start a performance      │
│  stop               - End current performance  │
│  encore             - Boost current song       │
│  songs              - List known songs         │
├─────────────────────────────────────────────────┤
│  While performing:                              │
│  • Song effects apply each tick                 │
│  • Mana drains per tick                         │
│  • Cannot cast spells (mouth busy)             │
│  • Can still fight (instruments/voice)          │
│  • Movement ends performance                    │
│  • Taking damage may interrupt                  │
└─────────────────────────────────────────────────┘
```

---

## Songs (8 Total)

### Combat Songs

#### 1. Song of Courage
- **Effect:** +2 hitroll, +1 damroll to all allies in room
- **Mana Cost:** 3/tick
- **Level:** 1
- **Message:** "♪ Your courageous melody fills your allies with valor! ♪"

#### 2. Battle Hymn  
- **Effect:** +15% attack speed to all allies
- **Mana Cost:** 4/tick
- **Level:** 10
- **Message:** "♪ Your battle hymn drives your allies into a fighting frenzy! ♪"

#### 3. Dirge of Doom
- **Effect:** -2 hitroll, -1 damroll to all enemies in room
- **Mana Cost:** 4/tick
- **Level:** 15
- **Message:** "♪ Your mournful dirge saps the will of your enemies! ♪"

#### 4. Discordant Note
- **Effect:** Enemies have 20% chance to fumble attacks
- **Mana Cost:** 5/tick
- **Level:** 25
- **Message:** "♪ Your jarring notes throw enemies off balance! ♪"

### Support Songs

#### 5. Song of Rest
- **Effect:** +50% HP/mana/move regen to all allies (out of combat only)
- **Mana Cost:** 2/tick
- **Level:** 3
- **Message:** "♪ Your soothing melody helps your allies recover... ♪"

#### 6. Lullaby
- **Effect:** Enemies must save vs sleep each tick (cumulative -5% per tick)
- **Mana Cost:** 5/tick
- **Level:** 12
- **Message:** "♪ Your gentle lullaby lulls enemies into slumber... ♪"

#### 7. Inspiring Ballad
- **Effect:** +10% XP gain to all allies, +1 to all stats
- **Mana Cost:** 4/tick
- **Level:** 20
- **Message:** "♪ Your inspiring ballad fills allies with confidence! ♪"

### Ultimate Song

#### 8. Symphony of Destruction
- **Effect:** 2d6 sonic damage to all enemies per tick, chance to deafen
- **Mana Cost:** 8/tick
- **Level:** 35
- **Message:** "♪ Your devastating symphony tears at your enemies! ♪"

---

## Bard Skills

### Existing (Need Implementation)
- `lore` ✅ - Already implemented (identify items)
- `sneak` ✅ - Already implemented
- `pick_lock` ❌ - Needs implementation

### New Skills

#### 1. Counter-Song
- **Command:** `countersong`
- **Effect:** Attempt to dispel enemy magical effects with your music
- **Mana Cost:** 25
- **Cooldown:** 30 seconds
- **Success:** Remove 1-3 buffs from enemies / debuffs from allies

#### 2. Fascinate
- **Command:** `fascinate <target>`
- **Effect:** Charm a non-hostile enemy, preventing them from attacking
- **Duration:** 3-5 ticks (level-based)
- **Mana Cost:** 20
- **Note:** Breaks on damage

#### 3. Mockery
- **Command:** `mock <target>`
- **Effect:** Taunt enemy, reducing their attack/damage and forcing them to attack you
- **Duration:** 2-4 ticks
- **Mana Cost:** 10
- **Bonus:** Small psychic damage

#### 4. Encore
- **Command:** `encore`
- **Effect:** Temporarily double current song's effects for 3 ticks
- **Mana Cost:** 30
- **Cooldown:** 60 seconds
- **Requirement:** Must be performing

---

## Implementation Details

### Player Attributes (add to Player class)
```python
self.performing = None          # Current song being performed
self.performance_ticks = 0      # How long performing
self.encore_active = False      # Encore boost active
self.encore_ticks = 0           # Encore duration remaining
self.last_countersong = 0       # Cooldown tracking
self.last_encore = 0            # Cooldown tracking
```

### Song Data Structure
```python
BARD_SONGS = {
    'courage': {
        'name': 'Song of Courage',
        'level': 1,
        'mana_per_tick': 3,
        'target': 'allies',
        'affects': [
            {'type': 'hitroll', 'value': 2},
            {'type': 'damroll', 'value': 1}
        ],
        'start_msg': "You begin singing a courageous melody!",
        'tick_msg': "♪ Your song of courage fills your allies with valor! ♪",
        'end_msg': "Your song of courage fades away.",
        'room_start': "$n begins singing a stirring, courageous tune!",
        'room_tick': "♪ $n's courageous melody echoes through the room! ♪",
    },
    # ... etc
}
```

### Performance Tick Logic
```python
async def process_performance_tick(player):
    if not player.performing:
        return
    
    song = BARD_SONGS[player.performing]
    
    # Check mana
    mana_cost = song['mana_per_tick']
    if player.encore_active:
        mana_cost *= 2
    
    if player.mana < mana_cost:
        await end_performance(player, "You run out of energy to continue!")
        return
    
    player.mana -= mana_cost
    player.performance_ticks += 1
    
    # Apply song effects
    await apply_song_effects(player, song)
    
    # Tick message (every 3 ticks)
    if player.performance_ticks % 3 == 0:
        await player.send(song['tick_msg'])
```

---

## Command Summary

| Command | Description |
|---------|-------------|
| `perform <song>` | Start performing a song |
| `songs` | List known songs and status |
| `stop` | Stop current performance |
| `encore` | Boost current song temporarily |
| `countersong` | Dispel magical effects |
| `fascinate <target>` | Charm an enemy |
| `mock <target>` | Taunt and debuff enemy |
| `lore <item>` | Identify an item (existing) |

---

## Integration Points

1. **Combat tick** - Apply song effects each combat round
2. **Movement** - End performance when leaving room
3. **Damage taken** - Chance to interrupt performance
4. **Casting** - Block spell casting while performing
5. **Regen tick** - Song of Rest bonus

---

## Files to Modify

1. `src/commands.py` - Add perform, songs, stop, encore, countersong, fascinate, mock commands
2. `src/combat.py` - Apply song effects in combat, handle interrupts
3. `src/player.py` - Add performance attributes
4. `src/spells.py` - Add BARD_SONGS dict and handlers
5. `src/server.py` - Add performance tick processing

---

*This design makes Bards the ultimate support class with meaningful tactical choices: which song for which situation?*
