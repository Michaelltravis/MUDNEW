# Necromancer System - Phase 2 Implementation Complete
**Completed:** February 2, 2026

## ✅ Phase 2: Combat Integration

### 1. Death Pact Damage Sharing (player.py)
Added to `take_damage()` method:
- Checks for active death pact with a pet
- Splits incoming damage 50/50 with bonded pet
- If pet dies from shared damage:
  - Player takes 20% max HP backlash damage
  - Pact is automatically cleared
  - Pet is removed from world
- Shows appropriate messages for damage sharing and backlash

### 2. Shield Wall Damage Reduction (mobs.py)
Added to `take_damage()` method:
- Checks for `shield_wall_active > 0` on the target
- Reduces damage by 50% while active
- Shows message indicating damage absorbed
- Works for all mobs/pets, not just bone knights

### 3. Pet AI Combat Hook (combat.py)
Added to `one_round()` method:
- Calls `pet.ai_combat_tick()` for each pet each combat round
- Sets pet's target and fighting state before AI tick
- Triggers automatic use of special abilities:
  - Bone Knight: Shield Wall when low HP or owner attacked
  - Wraith Healer: Dark Heal when anyone <60% HP
  - Lich Acolyte: Necrotic Bolt every 2 rounds
  - Shadow Stalker: Backstab from stealth

### 4. Death Pact Duration Tracking (combat.py)
Added to `one_round()` method:
- Decrements `death_pact_duration` each combat round
- When duration reaches 0:
  - Notifies player that pact has faded
  - Clears pact references on both player and pet

### 5. Pet Targeting for Spells (spells.py)
Added to `get_target()` method:
- New 'pet' target type support
- Searches player's pets by name
- Returns matching pet or error message
- Used by: dark_mending, unholy_might, death_pact, siphon_unlife

## Files Modified

1. **src/player.py** - `take_damage()` (~40 lines)
   - Death pact damage sharing
   - Backlash damage on pet death
   - Pact cleanup

2. **src/mobs.py** - `take_damage()` (~10 lines)
   - Shield wall 50% damage reduction
   - Damage absorbed message

3. **src/combat.py** - `one_round()` (~20 lines)
   - Pet AI combat tick hook
   - Death pact duration decrement
   - Pact expiration handling

4. **src/spells.py** - `get_target()` (~15 lines)
   - Pet targeting support

## How It Works Together

### Combat Flow:
```
1. Player enters combat
2. one_round() processes player attack
3. For each pet in room:
   a. Decrement death_pact_duration if active
   b. Call pet.ai_combat_tick()
      - Uses special abilities based on conditions
      - Manages ability cooldowns
   c. Pet attacks target (50% chance)
4. If player takes damage:
   a. Check for death pact
   b. Split damage with pet
   c. Apply backlash if pet dies
```

### Shield Wall Flow:
```
1. Bone Knight hp < 50% or owner is fighting
2. ai_combat_tick() triggers shield_wall ability
3. shield_wall_active = 3 (rounds)
4. All enemies in room are taunted (target the knight)
5. When knight takes damage:
   - Check shield_wall_active > 0
   - Reduce damage by 50%
   - Show absorption message
6. shield_wall_active decrements each round
```

### Death Pact Flow:
```
1. Player casts death_pact on bone knight
2. death_pact_target = pet, death_pact_duration = 10
3. Each combat round: duration decrements
4. When player takes 100 damage:
   - Pet takes 50 damage
   - Player takes 50 damage
5. If pet dies:
   - Player takes 20% max HP backlash
   - Pact clears automatically
6. If duration reaches 0:
   - Pact fades, clears references
```

## Testing Plan

### Death Pact:
```
1. Summon bone knight
2. Cast death_pact on knight
3. Get hit by enemy
4. Verify damage is split 50/50
5. Let knight take enough damage to die
6. Verify backlash damage occurs
```

### Shield Wall:
```
1. Summon bone knight
2. Enter combat
3. Knight should use shield wall when <50% HP
4. Verify knight takes 50% less damage
5. Verify enemies are taunted to attack knight
```

### Pet AI:
```
1. Summon wraith healer
2. Take damage to get below 60% HP
3. Verify wraith automatically heals you
4. Summon lich acolyte
5. Enter combat
6. Verify lich casts necrotic bolt every 2 rounds
```

## Summary

**Phase 2 Complete!** 🎉

Combat integration is fully implemented:
- Death pact damage sharing ✅
- Death pact backlash on pet death ✅
- Death pact duration tracking ✅
- Shield wall damage reduction ✅
- Pet AI combat hook ✅
- Pet spell targeting ✅

All necromancer pet abilities will now work automatically in combat!

**Total New Code:** ~85 lines across 4 files

## What's Next: Phase 3

**Skills to implement:**
1. Dark Ritual (active channeled skill)
   - Buffs all pets at once
   - 30 mana + 15% HP cost
   - 2 minute duration
   - Cannot cast while channeling

2. Soul Harvest (passive skill)
   - Proc on enemy death
   - Gain soul fragments
   - Reduce spell costs / extend pet duration

**Commands to add:**
- `ritual` / `dark ritual` - activate dark ritual
- Update `score` to show soul fragments
