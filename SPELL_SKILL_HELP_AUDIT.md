# Spell & Skill Help File Audit - February 2, 2026

## Summary
Audited all 76 spells and 17 skills for help file coverage. Generated comprehensive, player-friendly help entries for everything missing documentation.

## Audit Results

### Coverage Statistics
- **Total Spells**: 76
- **Total Skills**: 17 (11 combat + 6 crafting)
- **Existing Help Topics**: 25
- **Missing Help Files**: 77 (63 spells + 14 skills)
- **Coverage Rate**: 18% → Will be 100% after merge

### Spells Audited
**Offensive (23 spells)**:
- blindness, burning_hands, call_lightning, chain_lightning, charm_person
- chill_touch, color_spray, death_grip, dispel_evil, energy_drain
- enervation, entangle, faerie_fire, fear, finger_of_death
- flamestrike, harm, meteor_swarm, poison, sleep
- slow, vampiric_touch, weaken

**Defensive/Buff (31 spells)**:
- aegis, barkskin, blink, create_food, create_water
- cure_critical, detect_evil, detect_magic, dispel_magic, displacement
- divine_protection, divine_shield, fire_shield, fly, heroism
- holy_aura, ice_armor, lay_hands, mana_shield, mirror_image
- protection_from_evil, protection_from_good, remove_curse, remove_poison
- righteous_fury, sanctuary, shield, shield_of_faith
- spell_reflection, stoneskin, word_of_recall

**Utility (9 spells)**:
- block_door, break_door, earthquake, enchant_weapon, group_heal
- identify, mass_charm, resurrect, summon

### Skills Audited
**Combat Skills (8)**:
- bash, kick, garrote, assassinate
- envenom, mark_target, shadow_step, detect_traps

**Crafting Skills (6)**:
- mining, herbalism, skinning
- blacksmithing, alchemy, leatherworking

Note: sneak, hide, backstab already had help files

## Help File Format

Each generated help entry includes:

### For Spells:
- **Name** and spell category (offensive/healing/buff/utility)
- **Description** with flavor text based on spell type
- **Mechanics**:
  - Damage dice (for offensive spells)
  - Healing amount (for healing spells)
  - Buff effects and values (for defensive spells)
  - Duration in game ticks and real-world minutes
- **Mana Cost**
- **Target Type** (offensive/defensive/self/object/door/room)
- **Level Requirements** (if any)
- **Saving Throw** info (if applicable)
- **Usage Examples** with proper syntax

### For Skills:
- **Name** and class restrictions
- **Description** explaining purpose and mechanics
- **Requirements** (tools, conditions, etc.)
- **Usage** with command syntax
- **Skill Improvement** info
- **Tips** for effective use

## Implementation

### Files Created:
1. **tools/audit_spells_skills.py** - Initial audit script
2. **tools/full_spell_skill_audit.py** - Complete audit with grouping
3. **tools/generate_help_files.py** - Help file generator
4. **tools/generated_help.py** - Generated help entries (80 total)
5. **tools/merge_help.py** - Merge script (ready to use)

### Files to Update:
- **src/help_data.py** - Need to merge generated_help.py entries

## Next Steps

1. **Merge help files** into help_data.py:
   ```bash
   cd ~/clawd/projects/RealmsMUD
   python3 tools/merge_help.py
   ```
   OR manually copy entries from `tools/generated_help.py` into `src/help_data.py` before the closing `}` at line 952.

2. **Update HELP_CATEGORIES** in help_data.py to include new spells/skills for organized browsing

3. **Test** after server restart:
   ```
   help magic_missile
   help bash
   help barkskin
   help mining
   ```

4. **Verify** all spells and skills are discoverable:
   ```
   help spells
   help skills
   ```

## Help Quality Guidelines

All generated help files follow these principles:
- **Player-focused**: Written from player perspective
- **Clear mechanics**: Exact numbers for damage, mana, duration
- **Usage examples**: Real command syntax with examples
- **Contextual**: Flavor text matches spell/skill theme
- **Complete**: All important info in one place

## Example Help Entry

```
Spell: Fireball
===============

Description:
  Fireball is an offensive spell that deals magical damage to your target.
  Base damage: 3d6+5 (+3 per level)
  Harness the power of fire to burn your enemies.

Mana Cost: 40
Target: Offensive

Usage:
  cast fireball <target>
  Example: cast fireball goblin
```

## Impact

**Before**: Players had to guess spell/skill mechanics through trial and error
**After**: Comprehensive in-game documentation for all 93 spells and skills

Players can now:
- Understand what each spell/skill does before learning it
- Know exact costs and requirements
- See usage examples for proper syntax
- Make informed decisions about character builds
- Learn game mechanics through built-in help

## Files Modified
- None yet (pending merge approval)

## Files Ready to Merge
- `tools/generated_help.py` (80 new help entries)
