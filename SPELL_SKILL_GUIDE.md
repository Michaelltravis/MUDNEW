# RealmsMUD Complete Spell & Skill Guide

## Table of Contents
- [Mage Spells](#mage-spells)
- [Cleric Spells](#cleric-spells)
- [Necromancer Spells](#necromancer-spells)
- [Bard Spells](#bard-spells)
- [Ranger Spells](#ranger-spells)
- [Paladin Spells](#paladin-spells)
- [Warrior Skills](#warrior-skills)
- [Thief/Assassin Skills](#thiefassassin-skills)

---

## Mage Spells

### Offensive Spells

**Magic Missile** (Level 1, 10 mana)
- Damage: 1d4+1 + 1/level
- Unerring bolts of magical force
- Number of missiles increases with level (max 5)
- Never misses target
- Usage: `cast magic missile <target>`

**Burning Hands** (Level 3, 15 mana)
- Damage: 1d6+2 + 2/level
- Short-range fire attack
- Affects weather: +20% in hot, -20% in rain
- Usage: `cast burning hands <target>`

**Chill Touch** (Level 5, 15 mana)
- Damage: 1d8 + 2/level
- Drains body heat from target
- May cause strength loss
- Usage: `cast chill touch <target>`

**Color Spray** (Level 7, 25 mana)
- Damage: 2d6 + 2/level
- Dazzling array of colors
- May confuse low-level targets
- Usage: `cast color spray <target>`

**Fireball** (Level 12, 40 mana)
- Damage: 3d6+5 + 3/level
- Classic area-effect fire spell
- Weather: +30% in clear, -20% in rain, -30% in storm
- Usage: `cast fireball <target>`

**Lightning Bolt** (Level 15, 35 mana)
- Damage: 3d6+3 + 3/level
- Electric damage in a line
- Weather: +20% in rain, +50% in storm
- Usage: `cast lightning bolt <target>`

**Meteor Swarm** (Level 25, 80 mana)
- Damage: 8d6+10 + 4/level
- Devastating area bombardment
- Highest damage mage spell
- Usage: `cast meteor swarm <target>`

**Chain Lightning** (Level 22, 70 mana)
- Damage: 6d6+8 + 3/level
- Chains to multiple enemies
- Each jump does reduced damage
- Usage: `cast chain lightning <target>`

### Defensive Spells

**Armor** (Level 1, 15 mana, 24 ticks)
- Effect: -20 AC
- Basic magical protection
- Stacks with other armor spells
- Duration: 2 minutes
- Usage: `cast armor` or `cast armor <target>`

**Shield** (Level 5, 25 mana, 24 ticks)
- Effect: -30 AC
- Superior to armor
- Creates shimmering force barrier
- Duration: 2 minutes
- Usage: `cast shield` or `cast shield <target>`

**Stoneskin** (Level 12, 60 mana, 12 ticks)
- Effect: Absorbs 100 damage
- Skin becomes hard as stone
- Damage absorbed before HP loss
- Duration: 1 minute
- Usage: `cast stoneskin` or `cast stoneskin <target>`

**Mirror Image** (Level 10, 40 mana, 12 ticks)
- Effect: Creates 3 illusory duplicates
- Each image absorbs one attack
- Increases survivability significantly
- Duration: 1 minute
- Usage: `cast mirror image`

**Displacement** (Level 8, 35 mana, 18 ticks)
- Effect: 25% miss chance
- Appear a few feet from actual position
- Hard to target accurately
- Duration: 1.5 minutes
- Usage: `cast displacement`

**Mana Shield** (Level 15, 50 mana, 10 ticks)
- Effect: 50% damage converted to mana loss
- 2 mana lost per 1 HP saved
- Excellent for high-mana builds
- Duration: 50 seconds
- Usage: `cast mana shield`

**Ice Armor** (Level 14, 45 mana, 18 ticks)
- Effect: -25 AC + slows melee attackers
- Cold-based protection
- Damages attackers slightly
- Duration: 1.5 minutes
- Usage: `cast ice armor` or `cast ice armor <target>`

**Fire Shield** (Level 16, 50 mana, 15 ticks)
- Effect: -20 AC + burns melee attackers
- Fire-based retaliation damage
- 10-20 damage per hit received
- Duration: 1.25 minutes
- Usage: `cast fire shield`

**Spell Reflection** (Level 20, 70 mana, 8 ticks)
- Effect: 50% chance to reflect spells
- Reflects spell back at caster
- Very mana intensive
- Duration: 40 seconds
- Usage: `cast spell reflection`

**Blink** (Level 18, 30 mana, 12 ticks)
- Effect: 30% miss chance
- Phase in/out of reality
- Works against physical and magical attacks
- Duration: 1 minute
- Usage: `cast blink`

**Protection from Evil** (Level 6, 30 mana, 24 ticks)
- Effect: -10 AC + bonus vs evil creatures
- Holy aura surrounds you
- +2 saving throw vs evil
- Duration: 2 minutes
- Usage: `cast protection from evil` or `cast protection from evil <target>`

**Protection from Good** (Level 6, 30 mana, 24 ticks)
- Effect: -10 AC + bonus vs good creatures
- Dark aura surrounds you
- +2 saving throw vs good
- Duration: 2 minutes
- Usage: `cast protection from good` or `cast protection from good <target>`

### Utility Spells

**Fly** (Level 10, 30 mana, 24 ticks)
- Grants ability to fly
- Access to aerial rooms
- Fall protection
- Duration: 2 minutes
- Usage: `cast fly` or `cast fly <target>`

**Invisibility** (Level 8, 35 mana, 24 ticks)
- Become invisible
- Broken by offensive actions
- +50% to hide/sneak
- Duration: 2 minutes
- Usage: `cast invisibility` or `cast invisibility <target>`

**Detect Magic** (Level 3, 10 mana, 24 ticks)
- See magical auras
- Identify enchanted items
- Detect magical traps
- Duration: 2 minutes
- Usage: `cast detect magic`

**Identify** (Level 12, 20 mana)
- Reveals full item properties
- Shows stats, bonuses, and effects
- Works on inventory and equipped items
- Instant effect
- Usage: `cast identify <item>`

**Enchant Weapon** (Level 18, 100 mana)
- Permanently adds +2 hitroll, +2 damroll
- One-time enchantment per weapon
- Cannot be stacked
- Permanent effect
- Usage: `cast enchant weapon <weapon>`

**Teleport** (Level 20, 50 mana)
- Random teleportation
- Can land anywhere in world
- Dangerous but useful for escape
- Instant effect
- Usage: `cast teleport`

**Sleep** (Level 5, 20 mana, 6 ticks)
- Target falls asleep
- Cannot act while sleeping
- Saving throw applies
- Duration: 30 seconds
- Usage: `cast sleep <target>`

---

## Cleric Spells

### Healing Spells

**Cure Light Wounds** (Level 1, 10 mana)
- Healing: 1d8+2 + 1/level
- Basic healing spell
- Can target self or others
- Usage: `cast cure light` or `cast cure light <target>`

**Cure Serious Wounds** (Level 5, 20 mana)
- Healing: 2d8+4 + 2/level
- Moderate healing
- 2x cure light effectiveness
- Usage: `cast cure serious` or `cast cure serious <target>`

**Cure Critical Wounds** (Level 10, 35 mana)
- Healing: 3d8+6 + 2/level
- Strong healing spell
- Emergency situations
- Usage: `cast cure critical` or `cast cure critical <target>`

**Heal** (Level 15, 50 mana)
- Healing: Full HP restoration
- Completely restores hit points
- Most powerful single-target heal
- Usage: `cast heal` or `cast heal <target>`

**Group Heal** (Level 20, 80 mana)
- Healing: 2d8+10 + 2/level to all group members
- Affects entire party
- High mana cost but efficient for groups
- Usage: `cast group heal`

**Lay Hands** (Paladin, Level 5, 40 mana)
- Healing: 50 HP
- Touch-based healing
- Can only target one person
- Usage: `cast lay hands <target>`

### Defensive Spells

**Bless** (Level 3, 15 mana, 24 ticks)
- Effect: +2 hitroll, +1 damroll
- Divine favor
- Increased combat effectiveness
- Duration: 2 minutes
- Usage: `cast bless` or `cast bless <target>`

**Sanctuary** (Level 18, 75 mana, 12 ticks)
- Effect: 50% damage reduction
- White aura of protection
- Very powerful defensive spell
- Duration: 1 minute
- Usage: `cast sanctuary` or `cast sanctuary <target>`

**Shield of Faith** (Level 8, 35 mana, 18 ticks)
- Effect: -25 AC, +2 saving throws
- Divine protective shield
- Good all-around defense
- Duration: 1.5 minutes
- Usage: `cast shield of faith` or `cast shield of faith <target>`

**Divine Shield** (Level 15, 75 mana, 6 ticks)
- Effect: Absorbs 150 damage
- Radiant barrier
- Strongest absorption spell
- Duration: 30 seconds
- Usage: `cast divine shield`

**Barkskin** (Level 10, 40 mana, 24 ticks)
- Effect: -35 AC
- Natural armor like tree bark
- Excellent AC bonus
- Duration: 2 minutes
- Usage: `cast barkskin` or `cast barkskin <target>`

**Righteous Fury** (Level 12, 55 mana, 12 ticks)
- Effect: 5 damage reduction, +3 damroll
- Offensive + defensive combination
- Holy power courses through you
- Duration: 1 minute
- Usage: `cast righteous fury`

**Divine Protection** (Level 25, 100 mana, 3 ticks)
- Effect: 95% damage reduction
- Nearly invulnerable
- Emergency use only (high cost, short duration)
- Duration: 15 seconds
- Usage: `cast divine protection`

**Aegis** (Level 16, 65 mana, 15 ticks)
- Effect: 30% spell resistance
- Magical wards
- Reduces spell damage
- Duration: 1.25 minutes
- Usage: `cast aegis` or `cast aegis <target>`

**Holy Aura** (Level 22, 80 mana, 12 ticks)
- Effect: -40 AC, +4 saving throws, 20% spell resist
- Most powerful cleric defense
- Combination of multiple protections
- Duration: 1 minute
- Usage: `cast holy aura` or `cast holy aura <target>`

### Offensive Spells

**Harm** (Level 18, 50 mana)
- Damage: 5d8
- Divine wrath
- Effective against undead (+50%)
- Usage: `cast harm <target>`

**Dispel Evil** (Level 14, 40 mana)
- Damage: 4d8 + 3/level
- Only affects evil creatures
- 2x damage to evil alignment
- Usage: `cast dispel evil <target>`

**Earthquake** (Level 20, 90 mana)
- Damage: 5d8 + 2/level
- Room-wide damage
- Affects all enemies in room
- Usage: `cast earthquake`

**Flamestrike** (Level 16, 60 mana)
- Damage: 4d8+10 + 2/level
- Column of holy fire
- Combines divine and fire damage
- Usage: `cast flamestrike <target>`

### Utility Spells

**Remove Curse** (Level 8, 35 mana)
- Removes curse effects
- Cleanses magical debuffs
- Also works on cursed items
- Usage: `cast remove curse <target>`

**Remove Poison** (Level 6, 30 mana)
- Cures poison status
- Removes poison damage over time
- Essential for dungeon delving
- Usage: `cast remove poison <target>`

**Create Food** (Level 5, 10 mana)
- Conjures bread (12 hours food)
- Never go hungry
- Basic sustenance
- Usage: `cast create food`

**Create Water** (Level 5, 10 mana)
- Fills waterskin or creates one
- 20 drinks of water
- Essential for survival
- Usage: `cast create water`

**Summon** (Level 20, 75 mana)
- Teleports player to your location
- Requires target not in combat
- Group formation tool
- Usage: `cast summon <player>`

**Word of Recall** (Level 10, 15 mana)
- Instant teleport to temple
- Emergency escape
- Always works unless in no-recall room
- Usage: `cast word of recall` or just `recall`

**Dispel Magic** (Level 15, 50 mana)
- Removes magical effects
- Based on caster level
- Can dispel buffs or debuffs
- Usage: `cast dispel magic <target>`

---

## Necromancer Spells

### Offensive/Drain Spells

**Chill Touch** (Level 1, 15 mana)
- Damage: 1d8 + 2/level
- Draining cold damage
- May weaken strength temporarily
- Usage: `cast chill touch <target>`

**Vampiric Touch** (Level 10, 30 mana)
- Damage: 2d6+2 + 1/level
- Heals caster for 50% of damage dealt
- Life drain effect
- Usage: `cast vampiric touch <target>`

**Energy Drain** (Level 18, 60 mana)
- Damage: 3d8 + 2/level
- Also drains XP (level×100)
- Very powerful against players
- Usage: `cast energy drain <target>`

**Death Grip** (Level 15, 45 mana)
- Damage: 3d8+3 + 2/level
- Also stuns target for 2 ticks
- Dark energy immobilizes foe
- Usage: `cast death grip <target>`

**Finger of Death** (Level 30, 150 mana)
- Damage: 10d8+20 + 5/level
- Ultimate necromancer spell
- Saving throw for half damage
- Usage: `cast finger of death <target>`

### Debuff Spells

**Poison** (Level 8, 25 mana, 12 ticks)
- Effect: 5 damage/tick, -2 STR
- Constant damage over time
- Weakens target
- Duration: 1 minute
- Usage: `cast poison <target>`

**Weaken** (Level 5, 20 mana, 12 ticks)
- Effect: -4 STR
- Reduces physical damage
- Useful against warriors
- Duration: 1 minute
- Usage: `cast weaken <target>`

**Blindness** (Level 10, 25 mana, 12 ticks)
- Effect: Cannot see, -4 hitroll
- Severe combat penalty
- Target fights blind
- Duration: 1 minute
- Usage: `cast blindness <target>`

**Fear** (Level 12, 30 mana)
- Effect: Target flees in terror
- Forces enemy to run away
- Saves vs spell to resist
- Usage: `cast fear <target>`

**Enervation** (Level 14, 35 mana, 12 ticks)
- Effect: -3 STR, -3 DEX
- Drains vitality
- Reduces combat effectiveness
- Duration: 1 minute
- Usage: `cast enervation <target>`

### Utility Spells

**Animate Dead** (Level 15, 50 mana)
- Creates undead servant from a corpse in the room
- Temporary combat ally (30-60 min)
- Power scales with caster level
- Servant types: bone knight (warrior), wraith healer, lich acolyte (caster), shadow stalker (rogue)
- Servant limit: 1 + floor(level/10) undead servants
- Usage: `cast animate dead [warrior|healer|caster|rogue]` or `raise <type>`

**Armor/Shield** (shared with Mage)
- Basic defensive spells
- Usage: `cast armor`, `cast shield`

---

## Bard Spells

### Buff Spells

**Heroism** (Level 10, 40 mana, 18 ticks)
- Effect: +3 hitroll, +3 damroll, +20 max HP
- Inspirational song
- Strong offensive buff
- Duration: 1.5 minutes
- Usage: `cast heroism <target>`

**Haste** (Level 12, 50 mana, 12 ticks)
- Effect: Extra attacks per round
- Move faster
- +1 attack/round
- Duration: 1 minute
- Usage: `cast haste <target>`

### Control Spells

**Charm Person** (Level 8, 30 mana, 12 ticks)
- Effect: Target becomes friendly
- Won't attack charmer
- Saving throw applies
- Duration: 1 minute
- Usage: `cast charm person <target>`

**Mass Charm** (Level 20, 100 mana)
- Effect: Attempts to charm all enemies
- Area charm effect
- Each target gets saving throw
- Usage: `cast mass charm`

**Sleep** (Level 5, 20 mana, 6 ticks)
- Target falls unconscious
- Easy to hit sleeping targets
- Saving throw applies
- Duration: 30 seconds
- Usage: `cast sleep <target>`

**Slow** (Level 10, 35 mana, 12 ticks)
- Effect: -1 attack/round, -2 hitroll
- Reduces combat speed
- Opposite of haste
- Duration: 1 minute
- Usage: `cast slow <target>`

### Utility Spells

**Invisibility**, **Cure Light** (shared with other classes)
- Basic utility spells
- Usage: `cast invisibility`, `cast cure light`

---

## Ranger Spells

### Nature Magic

**Barkskin** (Level 5, 40 mana, 24 ticks)
- Effect: -35 AC
- Natural armor like tree bark
- Ranger's primary defense
- Duration: 2 minutes
- Usage: `cast barkskin`

**Entangle** (Level 8, 25 mana, 6 ticks)
- Effect: Roots hold target in place
- Reduces movement and attacks
- Saving throw applies
- Duration: 30 seconds
- Usage: `cast entangle <target>`

**Call Lightning** (Level 12, 45 mana)
- Damage: 4d6+5 + 2/level
- Calls lightning from sky
- Only works outdoors
- Usage: `cast call lightning <target>`

**Faerie Fire** (Level 6, 20 mana, 12 ticks)
- Effect: +20 AC penalty to target (easier to hit)
- Glowing outline
- Cannot hide or be invisible
- Duration: 1 minute
- Usage: `cast faerie fire <target>`

---

## Paladin Spells

### Holy Magic

**Detect Evil** (Level 3, 10 mana, 24 ticks)
- See evil auras
- Identify evil creatures
- Helps target undead
- Duration: 2 minutes
- Usage: `cast detect evil`

**Protection from Evil** (Level 5, 30 mana, 24 ticks)
- Effect: -10 AC + bonus vs evil
- Primary paladin defense
- Stacks with other protections
- Duration: 2 minutes
- Usage: `cast protection from evil`

**Shield of Faith** (Level 8, 35 mana, 18 ticks)
- Effect: -25 AC, +2 saves
- Divine shield
- Strong defensive spell
- Duration: 1.5 minutes
- Usage: `cast shield of faith`

**Divine Shield** (Level 15, 75 mana, 6 ticks)
- Effect: Absorbs 150 damage
- Emergency protection
- Short but powerful
- Duration: 30 seconds
- Usage: `cast divine shield`

---

## Warrior Skills

Warriors don't use magic but have powerful combat skills:

### Offensive Skills

**Bash** (Level 5)
- Attempts to knock target down
- Target prone for 1 round
- 20% failure causes self to fall
- Uses: Interrupt spellcasting, crowd control
- Usage: `bash <target>`

**Kick** (Level 3)
- Extra damage attack
- Damage: 1d6 + STR bonus
- Can be used every round
- Uses: Additional damage output
- Usage: `kick <target>`

**Disarm** (Level 10)
- Knock weapon from target's hand
- Target's weapon goes to ground
- Based on DEX vs DEX roll
- Uses: Disable armed opponents
- Usage: `disarm <target>`

### Defensive Skills

**Parry** (Passive, Level 8)
- Automatically deflect attacks with weapon
- Chance: DEX-based (10-40%)
- No action required
- Better with higher weapon skill
- Uses: Passive damage avoidance

**Rescue** (Level 6)
- Take aggro from party member
- Forces enemy to attack you
- Tank ability
- Requires target being attacked
- Usage: `rescue <ally>`

**Second Attack** (Passive, Level 10)
- Gain second attack per round
- 75% chance to trigger at max skill
- Passive: always active
- Uses: Increased damage output

**Third Attack** (Passive, Level 20)
- Gain third attack per round
- 50% chance to trigger at max skill
- Requires Second Attack
- Uses: Maximum damage output

---

## Thief/Assassin Skills

### Stealth Skills

**Sneak** (Level 1)
- Move silently without arrival/departure messages
- Skill check each room
- +10% bonus over base skill
- Broken by offensive actions
- Usage: `sneak` (toggle)

**Hide** (Level 1)
- Become hidden in current room
- Cannot be seen by others
- Broken by movement or offensive actions
- NPCs may detect based on level vs skill
- Usage: `hide`

### Offensive Skills

**Backstab** (Level 5)
- Massive damage from behind
- Damage: weapon × (2 + level/8)
- Must be hidden or sneaking
- Can only be used once per combat
- Usage: `backstab <target>`

**Circle** (Level 15)
- Backstab during combat
- Lower multiplier than backstab
- Requires target fighting someone else
- Can be used repeatedly
- Usage: `circle <target>`

**Envenom** (Level 10)
- Apply poison to weapon
- Adds poison effect to attacks
- Requires poison vial
- Lasts 10 hits or 5 minutes
- Usage: `envenom <weapon> <poison>`

**Garrote** (Assassin, Level 15)
- Silent kill from behind
- Instant kill on success (NPCs only)
- 50% HP damage on failure
- Very difficult skill check
- Usage: `garrote <target>`

**Assassinate** (Assassin, Level 20)
- Lethal attack on marked target
- Requires Mark Target first
- 3× normal backstab damage
- One per mark
- Usage: `assassinate <target>`

### Utility Skills

**Pick Lock** (Level 3)
- Open locked doors/containers
- Difficulty-based on lock complexity
- May trigger traps
- Requires lockpicks
- Usage: `pick <door|container>`

**Steal** (Level 5)
- Take items/gold from others
- Skill vs victim's perception
- Failure alerts target
- Cannot steal equipped items
- Usage: `steal <item> <target>`

**Detect Traps** (Level 8)
- Reveal hidden traps
- Shows trap difficulty
- Required before disarming
- Usage: `detect traps`

---

## Skill/Spell Advancement

### Learning Spells/Skills
- Practice at your guildmaster with practice points
- Each practice increases skill by 5%
- Maximum skill: 95% (1-5% failure chance)
- Cost increases with skill level

### Improving Through Use
- Successful use grants small chance to improve
- Improvement chance: 5% per successful use
- Only improves if skill below 95%
- Higher difficulty = better improvement chance

### Failure Mechanics
- Roll d100 against skill percentage
- Critical failure (roll 1-5): Always fails
- Critical success (roll 96-100): Always succeeds
- Normal: Success if roll ≤ skill percentage

---

## Combat Strategy Tips

### Mages
1. Cast Shield → Stoneskin → Mirror Image before combat
2. Use Mana Shield if high mana pool
3. Blink or Displacement for additional dodge
4. Save Spell Reflection for boss fights
5. Offensive: Start with Color Spray, then Fireball, save Meteor Swarm

### Clerics
1. Cast Holy Aura or Shield of Faith before dangerous areas
2. Keep Sanctuary for emergencies
3. Divine Protection is panic button (3 ticks only!)
4. Group: Use Group Heal, Bless all members
5. Solo: Barkskin + Shield of Faith + Bless = excellent defense

### Warriors
1. Bash spellcasters to interrupt
2. Use Rescue to protect weaker party members
3. Kick on cooldown for extra damage
4. Disarm dangerous weapon users
5. Let Parry work passively

### Thieves/Assassins
1. Always approach hidden or sneaking
2. Backstab → flee → hide → backstab (repeat)
3. Circle if target fighting ally
4. Envenom weapon before tough fights
5. Use Garrote for silent kills (assassins)

### Rangers
1. Cast Barkskin at start of day (long duration)
2. Entangle dangerous melee enemies
3. Call Lightning outdoors only
4. Faerie Fire before backstab attempts by party
5. Track skill for finding NPCs/players

### Paladins
1. Protection from Evil against undead
2. Shield of Faith for general defense
3. Lay Hands for emergency healing
4. Detect Evil to identify threats
5. Tank role: Rescue + high HP

---

## Status Effects Reference

### Positive Effects
- **Armor/Shield**: Reduced AC (harder to hit)
- **Bless**: Improved hit/damage
- **Haste**: Extra attacks
- **Fly**: Aerial movement
- **Sanctuary**: 50% damage reduction
- **Stoneskin**: Damage absorption
- **Mirror Image**: Absorb hits
- **Heroism**: Combat bonuses

### Negative Effects
- **Poison**: Damage over time, -STR
- **Blind**: Cannot see, -hitroll
- **Weaken**: -STR
- **Slow**: Fewer attacks
- **Curse**: -hit/-damage
- **Entangled**: Movement/attack penalty
- **Charmed**: Friendly to caster
- **Stunned**: Cannot act

---

## Advanced Combinations

### The Invincible Mage
```
cast armor
cast shield
cast stoneskin
cast mirror image
cast blink
cast spell reflection
```
Result: 100+ AC reduction, 100 damage absorbed, 3 image charges, 30% dodge, 50% spell reflect

### The Tank Cleric
```
cast holy aura
cast barkskin
cast sanctuary
cast righteous fury
```
Result: 75+ AC reduction, 50% damage reduction, 5 damage reduction flat

### The Glass Cannon
```
cast bless (or heroism for bard)
cast haste
bash target
second_attack triggers
third_attack triggers
kick
```
Result: 5-6 attacks per round with bonuses

---

## Mana Management

### Mana Costs by Tier
- **Low (10-20)**: Basic utility, minor heals, armor
- **Medium (25-50)**: Combat spells, moderate heals, good buffs
- **High (60-80)**: Powerful offense, strong defenses, area effects
- **Very High (100+)**: Ultimate spells, divine protection, enchantments

### Mana Regeneration
- Base: 1 mana per 5 seconds
- Resting: 2× base
- Sleeping: 4× base
- INT bonus: +1% per point above 15
- Weather: Clear +10%, Storm -10%

### Potion Use
- Mana potions restore 50-100 mana
- No cooldown (can chug multiple)
- Expensive (500-1000 gold each)
- Found in shops or as loot

---

This guide covers all spells and skills currently implemented in RealmsMUD!
