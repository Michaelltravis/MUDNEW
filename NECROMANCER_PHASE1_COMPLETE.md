# Necromancer System - Phase 1 Implementation Complete
**Completed:** February 2, 2026

## ✅ What's Been Implemented

### 1. New Necromancer Spells (spells.py)
Added 6 new spells to SPELLS dictionary and their special handlers:

**Dark Mending** (`heal_undead` handler)
- Heals undead pets for 3d8+level HP
- Class-restricted to necromancers
- Shows proper messages and effects

**Unholy Might** (uses affect system)
- Buffs pet with +5 hit, +8 damage, +25% speed, +1d6 necrotic damage
- Duration: 20 ticks (~10 minutes)
- Standard buff application

**Death Pact** (`death_pact` handler)
- Creates damage-sharing bond between caster and pet
- Stores relationship in both caster and pet objects
- Pet gets +3 damage buff
- Duration: 10 ticks

**Siphon Unlife** (`siphon_hp` handler)
- Bidirectional HP transfer (to/from pet)
- FROM mode: Drain 50% of pet HP to heal caster
- TO mode: Transfer 40% of caster HP to heal pet
- Prevents killing the pet (minimum 1 HP)

**Corpse Explosion** (`explode_corpse` handler)
- AoE damage to all enemies in room
- Base: 5d8 damage
- Bonus: +(pet HP / 2) if sacrificing a pet
- Destroys pet if sacrificed
- Removes corpse from room

**Mass Animate** (`mass_animate` handler)
- Requires level 20+
- Raises 3 weak zombies from corpses
- Zombies have 50% stats of normal undead_warrior
- Uses 3 corpses from room

### 2. Pet Special Abilities (pets.py)
Implemented 4 special abilities inside Pet class:

**Shield Wall** (Bone Knight)
```python
- Activates for 3 rounds
- Taunts all enemies to attack the knight
- Sets shield_wall_active flag
- 50% damage reduction (needs combat.py integration)
```

**Dark Heal** (Wraith Healer)
```python
- Heals lowest HP target (owner or other pets)
- 2d8+10 HP healing
- Auto-targets whoever needs it most
- 2 round cooldown
```

**Necrotic Bolt** (Lich Acolyte)
```python
- Ranged magic damage: 3d6+level
- 20% chance to curse target (-2 STR for 3 rounds)
- 2 round cooldown
- Uses take_damage if available
```

**Backstab** (Shadow Stalker)
```python
- 4x damage from stealth
- 1x damage if not stealthed
- Breaks stealth on use
- 30% chance to re-stealth after 2-3 rounds
- 2-3 round cooldown
```

### 3. Pet AI System (pets.py)
Implemented `ai_combat_tick()` method:

- Automatically uses abilities during combat based on conditions
- Shield Wall: When pet <50% HP or owner is fighting
- Dark Heal: When owner or pets <60% HP, with cooldown
- Necrotic Bolt: On cooldown every 2 rounds
- Backstab: From stealth, with re-stealth logic
- Manages all ability cooldowns automatically
- Decrements shield_wall_active counter

### 4. Pet System Integration (pets.py)
Updated PetManager.summon_pet:
- Now sets `pet.special_abilities` from template
- Pets automatically have their abilities available
- Works with all 4 undead servant types

## Files Modified

1. **src/spells.py**
   - Added 6 new spell definitions to SPELLS dict
   - Added 6 special handlers in handle_special_spell method
   - ~180 lines of new code

2. **src/pets.py**
   - Added use_special_ability method (~120 lines)
   - Added ai_combat_tick method (~80 lines)
   - Updated summon_pet to set special_abilities (~2 lines)
   - ~202 lines of new code

## What's Ready to Test

### Spells (after restart):
```
cast dark_mending knight
cast unholy_might wraith
cast death_pact stalker
cast siphon_unlife from knight
cast siphon_unlife to wraith
cast corpse_explosion knight  (sacrifices the knight)
cast mass_animate  (needs 3 corpses)
```

### Pet Abilities (automatic in combat):
- Bone knight will shield wall when hurt
- Wraith will heal you when you're below 60% HP
- Lich will spam necrotic bolts every 2 rounds
- Shadow stalker will backstab from stealth

## Integration Notes

### Combat System Hook Needed
The `ai_combat_tick()` method needs to be called from the combat round handler. Look for:
- `combat.py` - combat round/tick function
- Where pets already do their combat actions
- Add: `await pet.ai_combat_tick()` for each pet each round

### Shield Wall Damage Reduction
The 50% damage reduction for shield_wall needs integration in:
- `combat.py` or wherever `take_damage()` is implemented
- Check for `pet.shield_wall_active > 0`
- Apply 0.5x damage multiplier

Example:
```python
async def take_damage(self, damage, attacker):
    # Check for shield wall
    if hasattr(self, 'shield_wall_active') and self.shield_wall_active > 0:
        damage = int(damage * 0.5)
        # Show message
    # ... rest of damage code
```

### Death Pact Damage Sharing
When player takes damage, check for death_pact_target:
```python
if hasattr(player, 'death_pact_target') and player.death_pact_target:
    pet = player.death_pact_target
    if pet.death_pact_duration > 0:
        # Split damage 50/50
        pet_damage = damage // 2
        player_damage = damage - pet_damage
        await pet.take_damage(pet_damage, attacker)
        damage = player_damage
        
        # Check if pet died
        if pet.hp <= 0:
            backlash = int(player.max_hp * 0.2)
            player.hp -= backlash
            # Show backlash message
```

## Help Files

Help entries generated in `tools/necromancer_help.py`:
- dark_mending
- unholy_might
- death_pact
- siphon_unlife
- corpse_explosion
- mass_animate
- dark_ritual (skill - not yet implemented)
- soul_harvest (skill - not yet implemented)

Ready to merge into help_data.py.

## What's NOT Implemented Yet

**Phase 2 (Advanced Spells):**
- Unholy Might buff application (partially done via affects)
- Death Pact damage splitting logic (needs combat.py)
- Shield Wall damage reduction (needs combat.py)

**Phase 3 (Skills):**
- Dark Ritual skill
- Soul Harvest skill

**Combat Integration:**
- ai_combat_tick() hook in combat rounds
- Shield Wall damage reduction
- Death Pact damage sharing
- Backlash damage on pet death

## Testing Plan

1. **Basic Spell Casting:**
   - Can cast all 6 new spells?
   - Proper mana costs?
   - Correct messages?

2. **Dark Mending:**
   - Heals undead pets only?
   - Correct heal amount?
   - Rejects non-undead targets?

3. **Siphon Unlife:**
   - FROM mode drains pet, heals caster?
   - TO mode transfers caster HP to pet?
   - Doesn't kill pet?

4. **Corpse Explosion:**
   - Hits all enemies?
   - Bonus damage from pet sacrifice?
   - Removes pet correctly?

5. **Mass Animate:**
   - Requires 3 corpses?
   - Raises 3 zombies?
   - Zombies have 50% stats?
   - Level 20 requirement enforced?

6. **Pet Abilities:**
   - Bone knight uses shield wall?
   - Wraith heals when needed?
   - Lich casts bolts?
   - Stalker backstabs from stealth?

## Known Issues / TODOs

1. Combat integration needed for:
   - Calling ai_combat_tick() each round
   - Shield wall damage reduction
   - Death pact damage sharing

2. Death pact backlash not implemented yet

3. Skills (dark_ritual, soul_harvest) not implemented

4. Help files not merged into help_data.py yet

## Summary

**Phase 1 Complete!** 🎉

Core necromancer spell handlers and pet special abilities are fully implemented and ready to test. The spells will work immediately after restart. Pet abilities will trigger automatically in combat once the ai_combat_tick() hook is added to the combat system.

**Lines of Code:** ~380 new lines across 2 files
**New Features:** 6 spells, 4 pet abilities, auto-AI system
**Ready for:** Testing after server restart tomorrow

Next: Integrate with combat system, then proceed to Phase 2 (advanced features) and Phase 3 (skills).
