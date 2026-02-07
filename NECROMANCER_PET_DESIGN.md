# Necromancer Pet & Spell Design
**Created:** February 2, 2026

## Current Undead Pet Types

### 1. Bone Knight (Undead Warrior)
**Role:** Tank/Damage Absorber
**Stats:**
- Level: 90% of necromancer's level
- HP: 12d8+70 (very tanky)
- Damage: 2d6
- Duration: 1 hour

**Abilities:**
- **Shield Wall** (Special): Taunts enemies and reduces damage taken by 50% for 3 rounds. Can protect the necromancer by forcing enemies to target the knight instead.
- **Undead Resilience**: Immune to poison, disease, fear, and charm. Takes reduced damage from physical attacks.
- **Guard Owner**: Automatically interposes when necromancer is attacked

**Tactics:** Front-line tank. Best for solo play or tanking dungeon bosses.

### 2. Wraith Healer (Undead Healer)
**Role:** Support/Healer
**Stats:**
- Level: 70% of necromancer's level
- HP: 7d8+30 (fragile)
- Damage: 1d6 (minimal)
- Duration: 1 hour

**Abilities:**
- **Dark Heal** (Special): Heals the necromancer or another undead pet for 2d8+10 HP every 2 rounds during combat. Uses necrotic energy rather than divine magic.
- **Life Leech Aura**: Passive - The wraith's attacks drain small amounts of HP and transfer them to the necromancer (1-3 HP per hit).
- **Undead Resilience**: Standard undead immunities

**Tactics:** Backline support. Keeps necromancer and other pets alive during extended fights.

### 3. Lich Acolyte (Undead Caster)
**Role:** Ranged DPS/Debuffer
**Stats:**
- Level: 80% of necromancer's level
- HP: 6d8+25 (low)
- Damage: 1d4+1 (base melee, rarely used)
- Duration: 1 hour

**Abilities:**
- **Necrotic Bolt** (Special): Casts a bolt of death magic dealing 3d6+level damage. Can cast every 1-2 rounds.
- **Curse of Weakness**: 20% chance on hit to apply -2 STR debuff to target for 3 rounds
- **Mana Battery**: The lich can sacrifice 10% of its HP to restore 20 mana to the necromancer once per combat
- **Undead Resilience**: Standard undead immunities

**Tactics:** High damage from range. Glass cannon - needs protection.

### 4. Shadow Stalker (Undead Rogue)
**Role:** Burst DPS/Utility
**Stats:**
- Level: 85% of necromancer's level
- HP: 7d8+35 (moderate)
- Damage: 2d4 (can backstab for 4x damage)
- Duration: 1 hour

**Abilities:**
- **Backstab** (Special): If attacking from stealth or flanking, deals 4x damage. Requires repositioning (2-3 round cooldown).
- **Shadow Stealth**: Automatically enters stealth when combat begins. Can re-stealth if no attacks for 2 rounds.
- **Poison Touch**: Attacks have 15% chance to poison target (2d4 damage over 4 rounds)
- **Undead Resilience**: Standard undead immunities

**Tactics:** Assassin-style play. Best against low-armor casters and vulnerable targets.

---

## New Necromancer Spells (Pet Support)

### 1. **Death Pact**
**Mana Cost:** 40  
**Target:** Self/Pet  
**Duration:** 5 minutes  

**Description:**
Create a dark bond between you and your undead servant. While active:
- Damage taken by the necromancer is split 50/50 with the bonded pet
- Pet gains +3 damage and +20% attack speed
- If pet dies while bonded, necromancer takes 20% of their max HP as backlash damage

**Usage:** `cast death_pact <pet_name>`

**Tactical Use:** Turns your tankiest pet into a damage sponge while boosting its offense. Risk/reward - if the pet dies, you suffer.

---

### 2. **Dark Mending**
**Mana Cost:** 35  
**Target:** Undead pet  
**Healing:** 3d8+level  

**Description:**
Channel necrotic energy to repair your undead servant's damaged form. Unlike divine healing which harms undead, dark mending knits bone and shadow back together.

**Usage:** `cast dark_mending <pet_name>`

**Tactical Use:** Direct emergency healing for pets. Essential for keeping expensive/powerful pets alive through tough fights.

---

### 3. **Unholy Might**
**Mana Cost:** 50  
**Target:** Undead pet  
**Duration:** 10 minutes  

**Description:**
Infuse your undead servant with overwhelming dark power.

**Effects:**
- +5 to hit
- +8 damage
- +25% attack speed
- Pet's attacks deal an additional 1d6 necrotic damage

**Usage:** `cast unholy_might <pet_name>`

**Tactical Use:** Turn any pet into a DPS machine. Stack with Death Pact for massive damage output from your warrior or rogue.

---

### 4. **Corpse Explosion**
**Mana Cost:** 60  
**Target:** Corpse or dying pet  
**Damage:** 5d8 + (pet's remaining HP/2)  
**Area:** All enemies in room  

**Description:**
Detonate a corpse or sacrifice a dying undead servant in a devastating explosion of necrotic energy. The stronger the corpse/pet, the bigger the blast.

**Usage:** 
- `cast corpse_explosion` (targets corpse in room)
- `cast corpse_explosion <pet_name>` (sacrifices pet for bigger explosion)

**Tactical Use:** Finish fights with a bang. If your tank is about to die anyway, blow it up for massive AoE damage. Also works on enemy corpses for cleanup.

---

### 5. **Siphon Unlife**
**Mana Cost:** 45  
**Target:** Undead pet  
**Effect:** Transfer HP between necromancer and pet  

**Description:**
Create a temporary conduit between yourself and your undead servant, allowing life force to flow in either direction.

**Modes:**
- `siphon from <pet>` - Drain HP from pet to heal yourself (transfers 50% of pet's current HP to you)
- `siphon to <pet>` - Transfer your HP to heal pet (transfers up to 40% of your current HP)

**Usage:** `cast siphon_unlife <from/to> <pet_name>`

**Tactical Use:** Emergency healing that works both ways. Sacrifice pet HP to stay alive, or share your HP to save a valuable pet.

---

### 6. **Mass Animate** (High-level spell)
**Mana Cost:** 100  
**Target:** Room  
**Level Required:** 20  

**Description:**
Raise multiple corpses at once, creating a small army of basic undead (up to 3 corpses). These zombies are weaker than normal animated dead (50% stats) but numerous.

**Usage:** `cast mass_animate`

**Tactical Use:** Swarm tactics. Great for overwhelming single strong enemies or handling multiple weaker foes.

---

## New Necromancer Skills

### 1. **Dark Ritual** (Active Skill)
**Type:** Active  
**Cooldown:** 5 minutes  
**Cost:** 30 mana + 15% max HP  

**Description:**
Perform a blood ritual to empower all your undead servants at once. For the next 2 minutes:
- All pets gain +3 to all stats
- All pets regenerate 5% HP per round
- Necromancer cannot cast other spells during ritual (channeling)
- If interrupted, necromancer is stunned for 1 round

**Usage:** `ritual` or `dark ritual`

**Skill Progression:**
- Level 1-25: 1 minute duration
- Level 26-50: 1.5 minute duration
- Level 51-75: 2 minute duration
- Level 76+: 2.5 minute duration, -5% HP cost

**Tactical Use:** Pre-buff before boss fights. High risk (channeling, HP cost) but massive payoff for sustained fights.

---

### 2. **Soul Harvest** (Passive Skill)
**Type:** Passive  
**Trigger:** When enemy dies near necromancer  

**Description:**
Your mastery of death magic allows you to harvest soul fragments from slain enemies.

**Effects:**
- 25% chance when an enemy dies to gain a "Soul Fragment" (max 5 stacks)
- Each fragment reduces next spell mana cost by 10%
- Each fragment increases next undead pet summon duration by 20%
- Fragments last 10 minutes

**Usage:** Passive - always active

**Skill Progression:**
- Level 1-25: 25% chance, max 3 fragments
- Level 26-50: 30% chance, max 4 fragments
- Level 51-75: 35% chance, max 5 fragments
- Level 76+: 40% chance, max 5 fragments, fragments last 15 minutes

**Tactical Use:** Resource management. Extended dungeon crawls become more sustainable as you harvest souls.

---

## Pet Command System

### Existing Commands (to document):
- `animate_dead <warrior/healer/caster/rogue>` - Raise a corpse with specific role
- `pets` - List all your current undead servants
- `dismiss <pet_name>` - Destroy an undead servant

### Recommended New Commands:
- `pet attack <pet_name> <target>` - Direct a specific pet to attack
- `pet defend <pet_name>` - Order pet into defensive stance (tank mode)
- `pet follow <pet_name>` - Pet follows you (default)
- `pet stay <pet_name>` - Pet guards current location
- `pet passive <pet_name>` - Pet won't auto-attack
- `pet aggressive <pet_name>` - Pet attacks anything hostile

---

## Balance Notes

**Pet Limits:**
- Base: 1 undead servant
- +1 per 10 levels (level 10 = 2, level 20 = 3, level 30 = 4, etc.)
- Max 5 simultaneous undead

**Mana Management:**
- Necromancers should be mana-starved without Soul Harvest
- Spells cost enough that buffing 3+ pets drains resources
- Risk/reward: powerful pets require investment

**Pet Persistence:**
- Undead last 1 hour (3600 seconds) unless dismissed or killed
- Can't resummon same pet type for 5 minutes after it expires
- Corpses required - farming corpses is part of the gameplay loop

**PvP Considerations:**
- Pets can be targeted and killed separately
- Corpse Explosion provides counter-play against massed pets
- Dark Ritual's channeling makes necromancer vulnerable
- Death Pact can backfire spectacularly

---

## Implementation Priority

**Phase 1 (Core):**
1. Implement pet special abilities (shield_wall, dark_heal, necrotic_bolt, backstab)
2. Add Dark Mending (essential healing)
3. Add basic pet commands (attack, defend, stay)

**Phase 2 (Enhancement):**
4. Add Unholy Might (pet buff)
5. Add Death Pact (risk/reward bonding)
6. Implement Soul Harvest skill

**Phase 3 (Advanced):**
7. Add Siphon Unlife (HP transfer)
8. Add Corpse Explosion (AoE)
9. Implement Dark Ritual skill
10. Add Mass Animate (high level)

---

## Help Files Needed

All new spells and skills need help entries following the same format as the generated help files. Include:
- Clear descriptions
- Exact mechanics (damage, healing, duration)
- Tactical use cases
- Mana costs and cooldowns
- Usage examples

Would you like me to generate the help files for these new necromancer spells and skills?
