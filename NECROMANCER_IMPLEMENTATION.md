# Necromancer System Implementation Guide
**Created:** February 2, 2026

## Files Added/Modified

### ✅ Completed:
1. **spells.py** - Added 6 new necromancer spells to SPELLS dictionary
2. **tools/necromancer_help.py** - Generated help files for all spells and skills
3. **NECROMANCER_PET_DESIGN.md** - Complete design document

### 🔨 To Implement:

#### 1. Pet Special Abilities (pets.py)
Need to implement the special abilities that are currently just listed:

```python
# Add to pets.py in Pet class or combat handling

async def use_special_ability(self, ability_name, target=None):
    """Execute a pet's special ability."""
    
    if ability_name == 'shield_wall':
        # Bone Knight - Taunt and damage reduction
        if not hasattr(self, 'shield_wall_active'):
            self.shield_wall_active = 0
        
        if self.shield_wall_active > 0:
            return  # Already active
        
        self.shield_wall_active = 3  # 3 rounds
        # Add affect for 50% damage reduction
        from affects import AffectManager
        await AffectManager.apply_affect(
            self,
            'shield_wall',
            duration=3,
            modifiers=[{'type': 'damage_reduction', 'value': 50}]
        )
        
        # Taunt all enemies in room to attack this pet
        if self.room:
            for char in self.room.characters:
                if hasattr(char, 'is_fighting') and char != self and char != self.owner:
                    if char.is_fighting:
                        char.target = self
        
        await self.room.send_to_room(
            f"{self.name} raises its shield and braces for impact!",
            exclude=[]
        )
    
    elif ability_name == 'dark_heal':
        # Wraith Healer - Heal owner or other pet
        if not self.owner or not self.owner.room:
            return
        
        # Find lowest HP target (owner or other pets)
        targets = [self.owner]
        for char in self.owner.room.characters:
            if hasattr(char, 'owner') and char.owner == self.owner:
                targets.append(char)
        
        target = min(targets, key=lambda t: t.hp / t.max_hp if t.max_hp > 0 else 1)
        
        # Heal for 2d8+10
        import random
        heal_amount = sum(random.randint(1, 8) for _ in range(2)) + 10
        target.hp = min(target.max_hp, target.hp + heal_amount)
        
        c = Config().COLORS
        await target.send(f"{c['green']}The wraith's dark magic mends your wounds for {heal_amount} HP!{c['reset']}")
        if target != self:
            await self.room.send_to_room(
                f"{self.name} channels healing energy into {target.name}.",
                exclude=[target]
            )
    
    elif ability_name == 'necrotic_bolt':
        # Lich Acolyte - Ranged damage attack
        if not target:
            return
        
        import random
        damage = sum(random.randint(1, 6) for _ in range(3)) + self.level
        
        c = Config().COLORS
        await self.room.send_to_room(
            f"{self.name} fires a bolt of death magic at {target.name}!",
            exclude=[]
        )
        
        # Apply damage to target
        target.hp -= damage
        await target.send(f"{c['red']}The necrotic bolt hits you for {damage} damage!{c['reset']}")
        
        # 20% chance to apply weakness curse
        if random.randint(1, 100) <= 20:
            from affects import AffectManager
            await AffectManager.apply_affect(
                target,
                'curse_of_weakness',
                duration=3,
                modifiers=[{'type': 'str', 'value': -2}]
            )
            await target.send(f"{c['yellow']}You feel weakened by the curse!{c['reset']}")
    
    elif ability_name == 'backstab':
        # Shadow Stalker - Backstab from stealth
        if not target:
            return
        
        # Check if hidden/sneaking
        is_stealthy = 'hidden' in self.flags or 'sneaking' in self.flags
        
        import random
        base_damage = sum(random.randint(1, 4) for _ in range(2))
        
        if is_stealthy:
            # 4x damage from stealth
            damage = base_damage * 4
            self.flags.discard('hidden')  # Break stealth
            await self.room.send_to_room(
                f"{self.name} materializes behind {target.name} and backstabs!",
                exclude=[]
            )
        else:
            damage = base_damage
        
        target.hp -= damage
        c = Config().COLORS
        await target.send(f"{c['red']}{self.name} backstabs you for {damage} damage!{c['reset']}")
        
        # Re-stealth after 2-3 rounds if not in combat
        self.backstab_cooldown = random.randint(2, 3)
```

#### 2. Spell Handlers (spells.py)
Add handling for the new special effects in the `cast_spell` method:

```python
# Add to SpellManager.cast_spell after existing special handling

        if special == 'heal_undead':
            # Dark Mending - heal undead pet
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only mend undead servants!{c['reset']}")
                return
            
            heal_amount = Mobile.roll_dice(spell_data.get('heal_dice', '3d8'))
            heal_amount += caster.level * spell_data.get('heal_per_level', 1)
            
            target.hp = min(target.max_hp, target.hp + heal_amount)
            await caster.send(msg_self.replace('$N', target.name))
            await caster.room.send_to_room(
                msg_room.replace('$n', caster.name).replace('$N', target.name),
                exclude=[caster]
            )
        
        elif special == 'death_pact':
            # Create bond between caster and pet
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only bond with undead servants!{c['reset']}")
                return
            
            # Apply the pact as a special affect
            if not hasattr(caster, 'death_pact_target'):
                caster.death_pact_target = None
            
            caster.death_pact_target = target
            target.death_pact_master = caster
            
            # Apply damage buff to pet (handled by affects)
            from affects import AffectManager
            await AffectManager.apply_affect(
                target,
                'death_pact',
                duration=spell_data.get('duration_ticks', 10),
                modifiers=spell_data.get('affects', [])
            )
        
        elif special == 'siphon_hp':
            # Siphon Unlife - bidirectional HP transfer
            if not target or not hasattr(target, 'pet_type') or target.pet_type != 'undead':
                await caster.send(f"{c['red']}You can only siphon from undead servants!{c['reset']}")
                return
            
            # Parse target_name for direction (from/to)
            direction = 'from'  # default
            if isinstance(target_name, str):
                parts = target_name.lower().split()
                if 'to' in parts:
                    direction = 'to'
                elif 'from' in parts:
                    direction = 'from'
            
            if direction == 'from':
                # Drain from pet to heal caster
                transfer = int(target.hp * 0.5)
                target.hp -= transfer
                caster.hp = min(caster.max_hp, caster.hp + transfer)
                await caster.send(f"{c['green']}You drain {transfer} HP from {target.name}!{c['reset']}")
            else:
                # Transfer from caster to heal pet
                transfer = int(caster.hp * 0.4)
                caster.hp -= transfer
                target.hp = min(target.max_hp, target.hp + transfer)
                await caster.send(f"{c['yellow']}You transfer {transfer} HP to {target.name}!{c['reset']}")
        
        elif special == 'explode_corpse':
            # Corpse Explosion - AoE damage
            damage = Mobile.roll_dice(spell_data.get('damage_dice', '5d8'))
            
            # If target is a pet, add its remaining HP to damage
            if target and hasattr(target, 'pet_type'):
                damage += int(target.hp / 2)
                # Remove the pet
                if target.room:
                    target.room.characters.remove(target)
                if hasattr(target, 'owner'):
                    target.owner.world.npcs.remove(target)
            
            # Hit all enemies in room
            if caster.room:
                for char in list(caster.room.characters):
                    if char != caster and not (hasattr(char, 'owner') and char.owner == caster):
                        if hasattr(char, 'hp'):
                            char.hp -= damage
                            await char.send(f"{c['red']}The explosion hits you for {damage} damage!{c['reset']}")
        
        elif special == 'mass_animate':
            # Mass Animate - raise 3 weak zombies
            if caster.level < spell_data.get('level_required', 20):
                await caster.send(f"{c['red']}You must be level {spell_data['level_required']} to use this spell!{c['reset']}")
                return
            
            # Find corpses in room
            corpses = []
            for item in caster.room.items:
                if hasattr(item, 'item_type') and item.item_type == 'container':
                    if 'corpse' in item.name.lower():
                        corpses.append(item)
            
            if len(corpses) < 3:
                await caster.send(f"{c['yellow']}You need at least 3 corpses to use mass animate!{c['reset']}")
                return
            
            # Raise 3 weak zombies
            from pets import PetManager
            raised = 0
            for i in range(min(3, len(corpses))):
                # Create weak zombie (50% stats of normal)
                zombie = await PetManager.summon_pet(
                    caster,
                    'undead_warrior',
                    duration_minutes=60
                )
                if zombie:
                    # Reduce stats to 50%
                    zombie.max_hp = int(zombie.max_hp * 0.5)
                    zombie.hp = zombie.max_hp
                    zombie.name = f"zombie {i+1}"
                    zombie.short_desc = f"a shambling zombie"
                    raised += 1
                    caster.room.items.remove(corpses[i])
            
            await caster.send(f"{c['bright_magenta']}You raise {raised} zombie servants!{c['reset']}")
```

#### 3. Skills System (player.py or new skills.py)
Need to add Dark Ritual and Soul Harvest:

```python
# Add to Player class

async def use_dark_ritual(self):
    """Perform dark ritual to buff all undead pets."""
    c = Config().COLORS
    
    # Check cooldown
    if hasattr(self, 'dark_ritual_cooldown') and self.dark_ritual_cooldown > 0:
        await self.send(f"{c['red']}Dark ritual is on cooldown!{c['reset']}")
        return
    
    # Check mana and HP cost
    mana_cost = 30
    hp_cost = int(self.max_hp * 0.15)
    
    if self.mana < mana_cost:
        await self.send(f"{c['red']}You need {mana_cost} mana!{c['reset']}")
        return
    
    if self.hp <= hp_cost:
        await self.send(f"{c['red']}The ritual would kill you!{c['reset']}")
        return
    
    # Pay costs
    self.mana -= mana_cost
    self.hp -= hp_cost
    
    # Apply ritual buff to all undead pets
    from pets import PetManager
    pets = PetManager.get_player_pets(self)
    undead_pets = [p for p in pets if p.pet_type == 'undead']
    
    if not undead_pets:
        await self.send(f"{c['yellow']}You have no undead servants to empower!{c['reset']}")
        return
    
    # Calculate duration based on skill level
    skill_level = self.skills.get('dark_ritual', 1)
    if skill_level < 26:
        duration = 2  # 1 minute
    elif skill_level < 51:
        duration = 3  # 1.5 minutes  
    elif skill_level < 76:
        duration = 4  # 2 minutes
    else:
        duration = 5  # 2.5 minutes
    
    # Set channeling state
    self.channeling_ritual = duration
    
    # Buff all pets
    from affects import AffectManager
    for pet in undead_pets:
        await AffectManager.apply_affect(
            pet,
            'dark_ritual',
            duration=duration,
            modifiers=[
                {'type': 'str', 'value': 3},
                {'type': 'dex', 'value': 3},
                {'type': 'con', 'value': 3},
                {'type': 'regen', 'value': 5}  # 5% HP per round
            ]
        )
    
    await self.send(f"{c['bright_magenta']}You begin the dark ritual!{c['reset']}")
    await self.room.send_to_room(
        f"{self.name} begins chanting in a guttural tongue, dark energy swirling!",
        exclude=[self]
    )
    
    # Set cooldown (5 minutes)
    self.dark_ritual_cooldown = 10  # game ticks

# Add soul harvest to combat/kill handler
async def on_enemy_death(self, enemy):
    """Called when an enemy dies near the player."""
    
    # Soul Harvest check for necromancers
    if self.char_class == 'necromancer':
        skill_level = self.skills.get('soul_harvest', 0)
        if skill_level > 0:
            import random
            
            # Calculate chance based on skill level
            if skill_level < 26:
                chance = 25
                max_frags = 3
            elif skill_level < 51:
                chance = 30
                max_frags = 4
            elif skill_level < 76:
                chance = 35
                max_frags = 5
            else:
                chance = 40
                max_frags = 5
            
            if random.randint(1, 100) <= chance:
                if not hasattr(self, 'soul_fragments'):
                    self.soul_fragments = 0
                
                if self.soul_fragments < max_frags:
                    self.soul_fragments += 1
                    c = Config().COLORS
                    await self.send(
                        f"{c['bright_cyan']}You harvest a soul fragment! ({self.soul_fragments}/{max_frags}){c['reset']}"
                    )
```

#### 4. Pet AI Updates (pets.py)
Need to make pets use their abilities automatically in combat:

```python
# Add to Pet.ai_combat or combat tick handler

async def ai_combat_tick(self):
    """AI behavior during combat."""
    if not self.is_fighting or not self.target:
        return
    
    # Use special abilities based on role
    if 'shield_wall' in self.special_abilities:
        # Bone Knight - use shield wall when low HP or owner under attack
        if self.hp < self.max_hp * 0.5 or (self.owner and self.owner.is_fighting):
            await self.use_special_ability('shield_wall')
    
    elif 'dark_heal' in self.special_abilities:
        # Wraith Healer - heal when owner or pets below 60% HP
        if self.owner:
            needs_heal = self.owner.hp < self.owner.max_hp * 0.6
            if not needs_heal:
                # Check other pets
                from pets import PetManager
                pets = PetManager.get_player_pets(self.owner)
                for pet in pets:
                    if pet != self and pet.hp < pet.max_hp * 0.6:
                        needs_heal = True
                        break
            
            if needs_heal:
                await self.use_special_ability('dark_heal')
    
    elif 'necrotic_bolt' in self.special_abilities:
        # Lich - cast bolt on cooldown
        if not hasattr(self, 'bolt_cooldown'):
            self.bolt_cooldown = 0
        
        if self.bolt_cooldown == 0:
            await self.use_special_ability('necrotic_bolt', self.target)
            self.bolt_cooldown = 2  # 2 round cooldown
        else:
            self.bolt_cooldown -= 1
    
    elif 'backstab' in self.special_abilities:
        # Shadow Stalker - backstab from stealth
        if 'hidden' in self.flags or 'sneaking' in self.flags:
            await self.use_special_ability('backstab', self.target)
```

## Testing Checklist

### Spells:
- [ ] dark_mending heals undead pets only
- [ ] unholy_might applies all buff effects
- [ ] death_pact splits damage correctly and has backlash on pet death
- [ ] siphon_unlife works in both directions (to/from)
- [ ] corpse_explosion hits all enemies and bonus damage from pet sacrifice
- [ ] mass_animate raises 3 weak zombies from corpses

### Skills:
- [ ] dark_ritual buffs all pets and prevents other spellcasting
- [ ] soul_harvest procs on enemy deaths and reduces costs

### Pet Abilities:
- [ ] Bone Knight shield_wall taunts and reduces damage
- [ ] Wraith dark_heal heals owner and pets
- [ ] Lich necrotic_bolt casts on cooldown
- [ ] Shadow Stalker backstabs from stealth

### Help Files:
- [ ] All 8 new entries (6 spells + 2 skills) added to help_data.py
- [ ] Help accessible via `help dark_mending`, `help soul_harvest`, etc.

## Priority Implementation Order

**Phase 1 (Core Functionality):**
1. ✅ Add spells to SPELLS dictionary
2. ✅ Generate help files
3. Implement heal_undead handler (dark_mending)
4. Implement pet special abilities (shield_wall, dark_heal, necrotic_bolt, backstab)
5. Add pet AI to use abilities automatically

**Phase 2 (Advanced Spells):**
6. Implement unholy_might buff application
7. Implement death_pact damage splitting
8. Implement siphon_unlife HP transfer

**Phase 3 (High-Level Features):**
9. Implement corpse_explosion AoE
10. Implement mass_animate multi-summon
11. Implement dark_ritual skill
12. Implement soul_harvest skill

## Files to Modify

1. **src/spells.py** - ✅ Spell definitions added
2. **src/spells.py** - Special effect handlers (heal_undead, death_pact, etc.)
3. **src/pets.py** - Pet special abilities implementation
4. **src/pets.py** - Pet AI combat behavior
5. **src/player.py** or **src/skills.py** - Dark ritual and soul harvest
6. **src/help_data.py** - Merge necromancer_help.py entries
7. **src/commands.py** - Add `ritual` command if needed

## Notes

- All spells need class restriction check (`caster.char_class == 'necromancer'`)
- Pet abilities should trigger automatically via AI, not require player commands
- Soul fragments should be visible in `score` command
- Death pact backlash should show dramatic message
- Corpse explosion should have visual flair (it's an explosion!)

---

**Status:** Spells defined, help files generated. Ready for implementation of handlers and abilities.
