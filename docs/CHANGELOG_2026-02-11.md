# Changelog — February 11, 2026

## Assassin Class Rework — Intel System

### Core Mechanic: Intel
The assassin class has been completely redesigned around a new **Intel** system that replaces the old grab-bag of standalone abilities. Assassins now study their prey during combat, building Intel points that unlock increasingly powerful threshold abilities.

**How Intel works:**
- `mark <target>` — designate a target for Intel tracking
- Each successful melee hit on a marked target grants +1 Intel (max 10)
- Backstab from stealth grants +3 Intel (with talent)
- Shadow Step grants +1 Intel
- Poison ticks can grant Intel (with talent)
- Intel persists through Vanish (key for re-engage cycles)
- Intel resets on: target death, re-marking, player death

**Intel Threshold Abilities:**
| Intel | Command | Effect |
|-------|---------|--------|
| 3 | `expose` | Target takes 15% more damage from you for 30s |
| 6 | `vital` | 3x weapon damage, guaranteed crit, ignores 50% AC |
| 10 | `execute_contract` | Instant kill below 20% HP (bosses: 5x weapon damage) |

### Defensive Skills Rework
- **Feint** — Now reduces target's damage to you by 30% for 3 combat rounds (20s cooldown)
- **Evasion** — 100% dodge for 10 seconds (180s cooldown)
- **Vanish** — Drops combat, re-enters stealth, preserves Intel (60s cooldown)
- **Shadow Step** — Teleport behind target, auto-dodge next attack, +1 Intel (30s cooldown)

### Talent Tree Rebuild
All three assassin talent trees redesigned with meaningful passives:

**Lethality** (burst damage):
- Ruthlessness, Serrated Blades, Adrenaline, Intel Backstab
- Improved Backstab, Kill or Be Killed, Cold Blood, Focused Attacks, Death from Above

**Poison** (DoTs/sustain):
- Venom Coating, Improved Poisons, Numbing Toxin, Quick Venom
- Leech Venom, Intel from Poison, Wound Poison, Toxic Mastery, Envenom

**Shadow** (evasion/survivability):
- Shadow Mastery, Improved Stealth, Slip, Shadow Focus
- Ghost, Shadow Mend, Deadly Patience, Elusiveness, Shadow Blade

### Key Talent Passives (wired into combat):
- **Ghost** — Big hit (>20% max HP) triggers 50% dodge for 1 round
- **Shadow Mend** — Backstab from stealth heals 10% of damage dealt
- **Deadly Patience** — Intel >= 6 grants 15% damage reduction
- **Kill or Be Killed** — Each Intel point = +1% dodge
- **Numbing Toxin** — Poisoned targets deal 3/6/10% less damage to you
- **Adrenaline** — Killing a mob restores 20% max HP
- **Leech Venom** — Poison ticks heal 15% of tick damage
- **Intel from Poison** — Poison ticks on marked target build Intel

### Skill Cleanup
Assassin skills trimmed from 28 to 14 core abilities:
- **Kept**: backstab, sneak, hide, dual_wield, second_attack, dodge, feint, evasion, vanish, shadow_step, poison
- **New**: mark, expose, vital, execute_contract
- **Removed from class**: assassinate, fan_of_knives, rupture, garrote, shadowstrike, shadow_blades_master, vendetta_assassin, death_mark, blur, mark_target, slip, cold_blood (talent), shadow_blade (talent), shadow_blink, cloak_of_shadows, silence_strike, death_from_above (talent), marked_for_death

### Combat Flow
```
Stealth → Mark → Backstab (+3 Intel) → Build Intel →
Feint (damage reduction) → Expose at Intel 3 →
Continue building → Vital at Intel 6 →
Evasion if needed → Build to Intel 10 →
Execute Contract → Kill
```

Emergency: Vanish → heal → re-engage with Backstab (Intel preserved!)

---

## Other Changes

### Castle Apocalypse Difficulty Overhaul
- **Mob stats now loaded from zone data**: AC, hitroll, damroll, max_hp all read from zone JSON
- All zone 220 mobs massively buffed:
  - Gate Guardians: 8,000 HP, AC -60
  - Undead Guardians: 5,000 HP, AC -50
  - Bound Demons: 6,000 HP, AC -55
  - Pestilence: 60,000 HP, AC -90
  - War: 65,000 HP, AC -85
  - Famine: 55,000 HP, AC -85
  - Death: 80,000 HP, AC -100
  - Kirgan: 100,000 HP, AC -110
- Boss regen capped at 500 HP/tick (was 5% = 5,000 for Kirgan)

### Poison vs Regeneration
- Poison now halves mob out-of-combat regen
- Disease quarters mob regen
- Troll/regenerator in-combat regen completely blocked by poison
- All effects apply to both mobs and players

### Mob Combat Stats
- `mobs.py` now reads `ac`, `hitroll`, `damroll`, `max_hp` from zone JSON
- `get_hit_bonus()` uses mob's hitroll attribute
- `get_damage_bonus()` uses mob's damroll attribute
- Explicit `max_hp` takes priority over dice rolls

### Talent Tree Display
- Two-column layout for talent trees (fits on screen)
- Open-right box design (no right border for emoji compatibility)

### Help System Updates
- Complete help entries for: assassin, intel, mark, expose, vital, execute_contract, vanish, feint, evasion, shadow_step, backstab
- Legacy entries for removed skills (assassinate, garrote, blur, fan_of_knives, rupture, shadow_blades, vendetta, death_mark)
- Updated category indices

---

## Full Class Rework — All 9 Classes

Every class now has a unique resource mechanic and redesigned talent trees.

### Summary Table

| Class | Resource | Max | Generation | Key Abilities |
|-------|----------|-----|------------|---------------|
| Assassin | Intel | 10 | Hits on marked target, backstab | Expose, Vital Strike, Execute Contract |
| Thief | Luck | 10 | 15% per hit, crits, dodge/parry | Pocket Sand, Low Blow, Rigged Dice, Jackpot |
| Necromancer | Soul Shards | 10 | Killing enemies | Soul Bolt, Drain Soul, Bone Shield, Soul Reap |
| Paladin | Holy Power | 5 | 25% per hit, smite/bash, healing | Templar's Verdict, Word of Glory, Divine Storm |
| Cleric | Faith | 10 | Healing, holy damage, shadow form | Divine Word, Holy Fire, Divine Intervention |
| Mage | Arcane Charges | 5 | Offensive spells | Arcane Barrage, Evocation, Arcane Blast |
| Ranger | Focus | 100 | Per hit (+10), passive (+5), dodge (+15) | Aimed Shot, Kill Command, Rapid Fire |
| Warrior | Rage | 100 | Dealing/taking damage | Execute, Mortal Strike, Shield Wall, Battle Cry |
| Bard | Inspiration | 10 | Songs, combat hits, ally actions | Crescendo, Encore, Discordant Note, Magnum Opus |

### Talent Trees (27 per class, 243 total)
All 9 classes × 3 trees × 9 talents = 243 unique talents redesigned.

### Paladin Oath System
- `oath vengeance` — +15% damage, -10% healing, faster Holy Power
- `oath devotion` — +20% healing, +10% damage reduction
- `oath justice` — Balanced +10%/+10%

### Cleric Shadow Form
- `shadowform` toggle — +25% shadow damage, -30% healing, damage builds Faith

### Warrior Stances
- `stance battle` — +5% damage, +5% Rage gen
- `stance defensive` — -15% damage taken, -20% dealt
- `stance berserker` — +25% dealt, +15% taken, +10% Rage gen

### Help System
532 total help topics. Updated class overviews and resource guides for all 9 classes.

### Known Gaps (minor, non-blocking)
- Luck decay after combat not yet tick-based (needs regen_tick hook)
- Faith generation from healing spells needs hook in heal command
- Arcane Charges from spellcasting needs hook in cast command
- Inspiration from ally heal/kill needs proximity check
- These are all enhancements to make the systems feel tighter — core mechanics work
