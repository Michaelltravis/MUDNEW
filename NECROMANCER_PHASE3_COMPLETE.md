# Necromancer System - Phase 3 Implementation Complete
**Completed:** February 2, 2026

## ✅ Phase 3: Skills Implementation

### 1. Dark Ritual Command (commands.py)
New `ritual` command for necromancers:

**Mechanics:**
- Costs: 30 mana + 15% max HP (10% at skill level 76+)
- 5 minute cooldown
- Cannot cast other spells while channeling
- Duration scales with skill level:
  - Level 1-25: ~1 minute (20 rounds)
  - Level 26-50: ~1.5 minutes (30 rounds)
  - Level 51-75: ~2 minutes (40 rounds)
  - Level 76+: ~2.5 minutes (50 rounds)

**Effects on all undead pets:**
- +3 to STR, DEX, CON
- 5% HP regeneration per combat round

**Integration:**
- Ritual duration decrements each combat round
- HP regen applied to pets each round
- Blocks spellcasting while active
- Shows status in score command

### 2. Soul Harvest Passive (combat.py)
Automatic proc on enemy kills:

**Mechanics:**
- Triggers when necromancer kills any enemy
- Proc chance scales with skill level:
  - Level 1-25: 25% chance, max 3 fragments
  - Level 26-50: 30% chance, max 4 fragments  
  - Level 51-75: 35% chance, max 5 fragments
  - Level 76+: 40% chance, max 5 fragments, 15 min duration

**Fragment Benefits:**
- Reduces spell mana cost by 10% per fragment
- Extends pet summon duration by 20% per fragment
- Fragments are consumed when used
- Expire after 10-15 minutes (skill dependent)

### 3. Spell Channeling Block (spells.py)
- Checks for `channeling_ritual` flag before any spell
- Prevents casting while ritual is active
- Shows appropriate error message

### 4. Soul Fragment Mana Discount (spells.py)
- Applied before mana check
- 10% discount per fragment
- Fragment consumed on successful cast
- Shows discount in cast message

### 5. Soul Fragment Pet Duration (pets.py)
- Applied when summoning pets
- +20% duration per fragment
- Fragment consumed when bonus applied
- Shows extended duration message

### 6. Score Display Updates (commands.py)
Necromancer section shows:
- Soul fragment count (X/5)
- Fragment effects reminder
- Fragment expiration timer
- Dark Ritual active status and duration
- Dark Ritual cooldown remaining

## Files Modified

1. **src/commands.py**
   - Added `cmd_ritual()` method (~90 lines)
   - Updated `cmd_score()` for necromancer info (~35 lines)

2. **src/combat.py**  
   - Added soul harvest proc in `handle_death()` (~40 lines)
   - Added ritual duration decrement in `one_round()` (~8 lines)
   - Added pet ritual HP regen in `one_round()` (~12 lines)

3. **src/spells.py**
   - Added ritual channeling check (~4 lines)
   - Added soul fragment mana discount (~15 lines)
   - Added fragment consumption on cast (~10 lines)

4. **src/pets.py**
   - Added soul fragment duration bonus (~15 lines)

## Usage Examples

### Dark Ritual:
```
> ritual
You begin the dark ritual, sacrificing 45 HP and 30 mana!
All 3 undead servants are empowered for 40 rounds!
Effects: +3 to all stats, 5% HP regen per round
```

### Soul Harvest:
```
(kill enemy)
You harvest a soul fragment! (2/5)

> cast fireball goblin
Soul fragment consumed! Mana cost: 32/40 (1 remaining)
```

### Pet Summon with Fragments:
```
> cast animate_dead warrior
Soul fragment consumed! Pet duration extended to 72 minutes!
You bind the corpse into service as a bone knight!
```

### Score Display:
```
╠══════════════════════════════════════════════════════════════╣
║ Necromancer:                                               ║
║  Soul Fragments: 3/5  (-10% mana cost, +20% pet duration) ║
║  Expires in: 542s                                          ║
║  Dark Ritual ACTIVE - 35 rounds remaining              ║
```

## Combat Flow with Skills

```
1. Necromancer kills enemy
   → 25-40% chance to gain soul fragment
   → Message: "You harvest a soul fragment! (X/5)"

2. Necromancer uses 'ritual'
   → Pays 30 mana + 15% HP
   → All undead pets get buff for 20-50 rounds
   → Cannot cast spells while active

3. Each combat round while ritual active:
   → Ritual duration decrements
   → Pets regenerate 5% max HP
   → When ritual ends: "Your dark ritual fades."

4. Necromancer casts spell with fragments:
   → Mana cost reduced by 10% per fragment
   → One fragment consumed
   → Shows: "Soul fragment consumed! Mana cost: X/Y"

5. Necromancer summons pet with fragments:
   → Duration extended by 20% per fragment
   → One fragment consumed
   → Shows: "Pet duration extended to X minutes!"
```

## Testing Checklist

### Dark Ritual:
- [ ] Only necromancers can use
- [ ] Costs 30 mana + 15% HP
- [ ] Cannot cast spells while active
- [ ] All undead pets get buffed
- [ ] Duration scales with skill level
- [ ] 5 minute cooldown enforced
- [ ] Shows in score command

### Soul Harvest:
- [ ] Procs on enemy kills
- [ ] Chance increases with skill
- [ ] Max fragments scales with skill
- [ ] Fragments expire after 10-15 minutes
- [ ] Shows harvest message

### Fragment Effects:
- [ ] Mana cost reduced per fragment
- [ ] Fragments consumed on cast
- [ ] Pet duration extended
- [ ] Fragments consumed on summon
- [ ] Expiration tracked and displayed

## Summary

**Phase 3 Complete!** 🎉

The necromancer skill system is fully implemented:
- Dark Ritual active skill ✅
- Soul Harvest passive ✅
- Fragment mana discount ✅
- Fragment pet duration bonus ✅
- Score display updates ✅
- Combat integration ✅

**Total New Code:** ~230 lines across 4 files

## Complete Necromancer System Summary

### Phases Completed:
1. **Phase 1** - 6 spells, 4 pet abilities, AI system
2. **Phase 2** - Combat integration (damage sharing, shields, AI hook)
3. **Phase 3** - Dark Ritual skill, Soul Harvest passive

### Total Implementation:
- **Spells:** 6 new (dark_mending, unholy_might, death_pact, siphon_unlife, corpse_explosion, mass_animate)
- **Pet Abilities:** 4 (shield_wall, dark_heal, necrotic_bolt, backstab)
- **Skills:** 2 (dark_ritual, soul_harvest)
- **Combat Features:** Death pact damage sharing, shield wall reduction, pet AI
- **Resource System:** Soul fragments with mana/duration bonuses

### Files Modified:
- src/spells.py (~210 lines)
- src/pets.py (~235 lines)
- src/commands.py (~125 lines)
- src/player.py (~40 lines)
- src/mobs.py (~10 lines)
- src/combat.py (~100 lines)

**Total New Code:** ~720 lines

### Ready for Testing:
All features are coded and ready for testing after server restart!
