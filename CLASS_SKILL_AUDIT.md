# Class Skills & Spells Audit - RealmsMUD

**Date:** 2026-02-02  
**Purpose:** Audit all classes to ensure unique, engaging abilities comparable to the Necromancer system

---

## Executive Summary

The **Assassin** class has excellent implementation with 5 unique, synergistic skills. The **Necromancer** now has a complete pet system with 6 spells and pet abilities. Other classes need significant work.

### Implementation Status by Class

| Class | Skills Defined | Skills Implemented | Spells | Unique Factor | Grade |
|-------|---------------|-------------------|--------|---------------|-------|
| **Assassin** | 14 | 6 ✅ | 0 | Shadow/Poison synergy | A |
| **Necromancer** | 0 | 0 | 13+ | Pet system, death magic | A |
| **Warrior** | 11 | 2 ❌ | 0 | Generic melee | D |
| **Thief** | 12 | 3 ❌ | 0 | Stealth basics only | C |
| **Mage** | 1 | 0 ❌ | 22+ | Lots of spells, no skills | C+ |
| **Cleric** | 1 | 0 ❌ | 16+ | Healing focus, no mechanics | C |
| **Ranger** | 8 | 2 ❌ | 6 | Pet-less, no tracking | D |
| **Paladin** | 4 | 1 ❌ | 8 | Hybrid potential unused | D |
| **Bard** | 3 | 1 ❌ | 11 | No songs, no performance | F |

---

## Detailed Class Audits

### 1. WARRIOR ⚔️

**Config Skills:** kick, bash, rescue, disarm, second_attack, third_attack, parry, shield_block, defensive_stance, berserk, cleave

**Implemented:**
- ✅ `kick` - Basic damage
- ✅ `bash` - Damage + stun chance

**Missing (Need Implementation):**
- ❌ `rescue` - Pull ally from combat
- ❌ `disarm` - Knock weapon from enemy
- ❌ `parry` - Passive damage reduction
- ❌ `shield_block` - Active blocking
- ❌ `defensive_stance` - Trade damage for defense
- ❌ `berserk` - Rage mode (more damage, less defense)
- ❌ `cleave` - AoE melee attack
- ❌ `second_attack` / `third_attack` - Extra attacks per round

**Uniqueness Problem:** Warriors are just "guy who hits things." No tactical depth, no class fantasy.

**Proposed Unique Mechanics:**
1. **Rage System** - Build rage through combat, spend on powerful abilities
2. **Stance System** - Aggressive/Defensive/Balanced stances with trade-offs
3. **Weapon Mastery** - Different bonuses based on weapon type equipped
4. **Battle Shouts** - Short-term party buffs (courage, intimidate, rally)

---

### 2. THIEF 🗡️

**Config Skills:** backstab, sneak, hide, steal, pick_lock, detect_traps, second_attack, trip, circle, dodge, evasion, tumble

**Implemented:**
- ✅ `backstab` - Multiplied damage from stealth
- ✅ `sneak` - Move without detection
- ✅ `hide` - Become hidden

**Missing (Need Implementation):**
- ❌ `steal` - Take items from enemies
- ❌ `pick_lock` - Open locked doors/containers
- ❌ `detect_traps` - Find and disarm traps
- ❌ `trip` - Knock down enemy
- ❌ `circle` - Reposition behind target in combat
- ❌ `dodge` - Passive evasion (partially exists)
- ❌ `evasion` - Reduce AoE damage
- ❌ `tumble` - Escape combat safely

**Uniqueness Problem:** Thief is just "weaker assassin without cool abilities."

**Proposed Unique Mechanics:**
1. **Combo Point System** - Build combo points, spend on finishers
2. **Sleight of Hand** - Pickpocket gold/items during combat
3. **Trap Crafting** - Create and place traps
4. **Quick Fingers** - Steal beneficial buffs from enemies

---

### 3. MAGE 🔮

**Config Skills:** scribe  
**Config Spells:** magic_missile, burning_hands, chill_touch, fireball, lightning_bolt, sleep, color_spray, teleport, fly, invisibility, detect_magic, identify, enchant_weapon, meteor_swarm, chain_lightning, armor, shield, stoneskin, mirror_image, displacement, mana_shield, ice_armor, fire_shield, spell_reflection, blink, protection_from_evil, protection_from_good

**Implemented:**
- ✅ Many offensive spells
- ✅ Many defensive spells
- ❌ `scribe` - Not implemented

**Missing (Need Implementation):**
- ❌ `scribe` - Create scrolls
- ❌ Spell combos / metamagic
- ❌ Elemental specialization

**Uniqueness Problem:** Mages have lots of spells but no *mechanical depth*. Just "cast fireball, cast fireball, cast fireball."

**Proposed Unique Mechanics:**
1. **Arcane Charges** - Build charges, empower next spell
2. **Elemental Attunement** - Specialize in Fire/Ice/Lightning for bonuses
3. **Spell Weaving** - Combine spells for unique effects
4. **Metamagic** - Quicken, Empower, Maximize spell modifiers
5. **Familiar** - Summonable companion with utility abilities

---

### 4. CLERIC ⛪

**Config Skills:** turn_undead  
**Config Spells:** cure_light, cure_serious, cure_critical, heal, group_heal, bless, armor, sanctuary, remove_curse, remove_poison, create_food, create_water, summon, word_of_recall, resurrect, harm, dispel_evil, earthquake, flamestrike, shield_of_faith, divine_shield, barkskin, righteous_fury, divine_protection, aegis, holy_aura, protection_from_evil

**Implemented:**
- ✅ Healing spells
- ✅ Buff spells
- ❌ `turn_undead` - Not implemented

**Missing (Need Implementation):**
- ❌ `turn_undead` - Fear/destroy undead
- ❌ Divine channeling system
- ❌ Holy/unholy alignment mechanics

**Uniqueness Problem:** Clerics are just "healbots." No tactical depth, no interesting decisions.

**Proposed Unique Mechanics:**
1. **Divine Favor** - Resource that builds through healing, spend on smites
2. **Domain System** - Choose War/Life/Death domain for different abilities
3. **Turn Undead** - AoE fear/damage to undead
4. **Martyrdom** - Take damage to heal allies more
5. **Prayer** - Channel abilities that scale with time spent

---

### 5. RANGER 🏹

**Config Skills:** track, sneak, hide, second_attack, dual_wield, camouflage, ambush, dodge  
**Config Spells:** cure_light, detect_magic, faerie_fire, call_lightning, barkskin, entangle

**Implemented:**
- ✅ `sneak`, `hide` (shared with thief)
- ❌ Everything else

**Missing (Need Implementation):**
- ❌ `track` - Hunt down specific mobs
- ❌ `camouflage` - Enhanced outdoor hiding
- ❌ `ambush` - Opening attack from stealth
- ❌ `dual_wield` - Two-weapon fighting
- ❌ Animal companion system

**Uniqueness Problem:** Rangers are supposed to be wilderness warriors with animal companions. Currently they're just "thief with nature spells."

**Proposed Unique Mechanics:**
1. **Animal Companion** - Loyal pet that fights alongside (wolf, bear, hawk)
2. **Tracking System** - Hunt specific creatures, find hidden paths
3. **Terrain Mastery** - Bonuses in specific terrains (forest, mountain, etc.)
4. **Hunter's Mark** - Similar to assassin mark, but grants tracking
5. **Favored Enemy** - Bonus damage vs specific creature types

---

### 6. PALADIN 🛡️

**Config Skills:** rescue, bash, turn_undead, second_attack  
**Config Spells:** cure_light, cure_serious, bless, detect_evil, protection_from_evil, lay_hands, shield_of_faith, divine_shield

**Implemented:**
- ✅ `bash` (shared with warrior)
- ❌ Everything else

**Missing (Need Implementation):**
- ❌ `rescue` - Pull ally from combat
- ❌ `turn_undead` - Fear/destroy undead
- ❌ `lay_hands` - Emergency heal (should be skill, not spell)
- ❌ Aura system

**Uniqueness Problem:** Paladins should be holy tanks with protective abilities. Currently just "warrior with bad heals."

**Proposed Unique Mechanics:**
1. **Aura System** - Passive area buffs (Protection, Devotion, Retribution)
2. **Smite Evil** - Massive bonus damage vs evil creatures
3. **Lay on Hands** - Powerful self/ally heal on cooldown
4. **Divine Shield** - Brief invulnerability
5. **Righteous Fury** - More damage taken = more damage dealt

---

### 7. BARD 🎵

**Config Skills:** sneak, pick_lock, lore  
**Config Spells:** charm_person, sleep, invisibility, haste, slow, cure_light, detect_magic, heroism, fear, mass_charm, bless, armor

**Implemented:**
- ✅ `lore` - Identify items
- ❌ Everything else unique

**Missing (Need Implementation):**
- ❌ Song system (the whole class identity!)
- ❌ Performance mechanics
- ❌ Inspiration buffs

**Uniqueness Problem:** **THE WORST.** Bards are defined by their music. Without songs, they're just "bad mage/thief hybrid."

**Proposed Unique Mechanics:**
1. **Song System** - Ongoing performances that buff/debuff
   - Song of Courage (+hit/damage to party)
   - Song of Rest (out-of-combat regen)
   - Lullaby (AoE sleep)
   - Dirge (debuff enemies)
   - Battle Hymn (+party attack speed)
2. **Performance** - Channel songs that scale with duration
3. **Bardic Inspiration** - Give allies bonus dice
4. **Counter-Song** - Disrupt enemy magic/songs
5. **Fascinate** - Charm/distract enemies

---

## Priority Implementation Order

### Phase 1: Critical (Class-Defining)
1. **Bard Songs** - Without songs, bards have no identity
2. **Ranger Animal Companion** - Core class fantasy
3. **Warrior Stance System** - Tactical depth

### Phase 2: High Priority
4. **Cleric Turn Undead** - Listed but not implemented
5. **Paladin Auras** - Core paladin identity
6. **Thief Combo Points** - Differentiate from assassin

### Phase 3: Polish
7. **Mage Arcane Charges** - Add depth to spellcasting
8. **Warrior Rage** - Resource system
9. **All missing passive skills** (parry, dodge, evasion, etc.)

---

## Implementation Estimates

| Feature | Complexity | Lines of Code | Time |
|---------|------------|---------------|------|
| Bard Song System | High | ~400-500 | 2-3 hours |
| Ranger Companion | High | ~350-400 | 2 hours |
| Warrior Stances | Medium | ~200-250 | 1 hour |
| Paladin Auras | Medium | ~200-250 | 1 hour |
| Turn Undead | Low | ~80-100 | 30 min |
| Thief Combos | Medium | ~250-300 | 1.5 hours |
| Mage Charges | Medium | ~150-200 | 1 hour |

---

## Comparison: Assassin vs Other Classes

The Assassin shows what a well-designed class looks like:

**Assassin Synergies:**
- `sneak` → `hide` → `shadowstep` → `assassinate` (stealth chain)
- `mark_target` → `assassinate` (mark bonus)
- `envenom` → auto-applies on hits (poison system)
- `garrote` → silence casters (tactical utility)

**Other Classes Lack:**
- Skill synergies
- Resource management
- Meaningful choices
- Class fantasy fulfillment

---

## Recommendations

1. **Start with Bard** - Most broken, fastest to notice improvement
2. **Use Assassin as template** - 5-6 interconnected skills per class
3. **Add resource systems** - Rage, Combo Points, Divine Favor, Song Duration
4. **Create skill chains** - Skills that enable other skills
5. **Write help files simultaneously** - Don't repeat the help audit problem

---

*This audit identifies RealmsMUD's class balance issues. The goal is to make every class feel as unique and engaging as Assassin and Necromancer.*
