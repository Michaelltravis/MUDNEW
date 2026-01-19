"""
RealmsMUD Mobiles (NPCs)
========================
Non-player characters and monsters.
"""

import random
import logging
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world import World, Room

from config import Config
from player import Character
from affects import AffectManager
from regeneration import RegenerationCalculator

logger = logging.getLogger('RealmsMUD.Mobs')


class Mobile(Character):
    """Non-player character (mob)."""
    
    def __init__(self, vnum: int, world: 'World'):
        super().__init__()
        self.vnum = vnum
        self.world = world
        self.config = Config()
        
        # Mob-specific attributes
        self.short_desc = "a generic mob"
        self.long_desc = "A generic mob stands here."
        self.description = ""
        self.keywords = []  # List of keywords for targeting
        
        # Behavior flags
        self.flags = set()
        self.special = None  # Special behavior (shopkeeper, healer, etc.)
        
        # AI state
        self.hate_list = []  # Characters this mob is angry at
        self.memory = {}  # Remember things about players
        self.home_room = None
        self.home_zone = None  # Zone number this mob belongs to
        self.ai_config = {}  # AI configuration (patrol routes, behaviors, etc.)
        self.ai_state = {}  # Runtime AI state (patrol index, buffed status, etc.)
        self.ai_controller = None  # AIController instance

        # Combat
        self.damage_dice = '1d4'
        
    @classmethod
    def from_prototype(cls, proto: dict, world: 'World') -> 'Mobile':
        """Create a mobile from a prototype dictionary."""
        mob = cls(proto.get('vnum', 0), world)
        
        mob.name = proto.get('name', 'a creature')
        mob.short_desc = proto.get('short_desc', mob.name)
        mob.long_desc = proto.get('long_desc', f"{mob.name} is here.")
        mob.description = proto.get('description', '')

        # Generate keywords from name and short_desc for better targeting
        # Remove articles (a, an, the) and split into words
        keywords = set()
        for text in [mob.name, mob.short_desc]:
            words = text.lower().replace(',', '').replace('.', '').split()
            for word in words:
                if word not in ['a', 'an', 'the', 'is', 'are']:
                    keywords.add(word)
        mob.keywords = list(keywords)
        
        mob.level = proto.get('level', 1)
        mob.alignment = proto.get('alignment', 0)
        mob.gold = proto.get('gold', 0)
        mob.exp = proto.get('exp', mob.level * 100)
        
        # Parse HP dice
        hp_dice = proto.get('hp_dice', f'{mob.level}d10+{mob.level * 5}')
        mob.max_hp = cls.roll_dice(hp_dice)
        mob.hp = mob.max_hp
        
        # Mana and movement
        mob.max_mana = mob.level * 10
        mob.mana = mob.max_mana
        mob.max_move = 100
        mob.move = mob.max_move
        
        # Parse damage dice
        mob.damage_dice = proto.get('damage_dice', '1d6')
        
        # Stats based on level
        mob.str = 10 + mob.level // 5
        mob.int = 10 + mob.level // 5
        mob.wis = 10 + mob.level // 5
        mob.dex = 10 + mob.level // 5
        mob.con = 10 + mob.level // 5
        mob.cha = 10 + mob.level // 5
        
        # Armor class improves with level
        mob.armor_class = 100 - mob.level * 2
        
        # Flags
        mob.flags = set(proto.get('flags', []))
        mob.special = proto.get('special')

        # Load AI configuration
        mob.ai_config = proto.get('ai_config', {})

        # Create AI controller if AI config exists
        if mob.ai_config:
            from ai import AIController
            mob.ai_controller = AIController.create_from_config(mob, mob.ai_config)

        # Load equipment
        equipment_data = proto.get('equipment', {})
        if equipment_data:
            from objects import create_object
            for slot, obj_vnum in equipment_data.items():
                # Create object from vnum using the objects module function
                obj = create_object(obj_vnum, world)
                if obj:
                    mob.equipment[slot] = obj

        # Initialize shop if this mob is a shopkeeper
        shop_config = proto.get('shop_config')
        if shop_config and mob.special == 'shopkeeper':
            from shops import ShopManager
            ShopManager.create_shop(mob, shop_config, world)

        return mob
        
    @staticmethod
    def roll_dice(dice_str: str) -> int:
        """Roll dice from a string like '2d6+4'."""
        try:
            if '+' in dice_str:
                dice_part, bonus = dice_str.split('+')
                bonus = int(bonus)
            elif '-' in dice_str:
                dice_part, penalty = dice_str.split('-')
                bonus = -int(penalty)
            else:
                dice_part = dice_str
                bonus = 0
                
            num_dice, die_size = dice_part.split('d')
            num_dice = int(num_dice)
            die_size = int(die_size)
            
            total = sum(random.randint(1, die_size) for _ in range(num_dice))
            return max(1, total + bonus)
            
        except Exception:
            return random.randint(10, 50)
            
    async def process_ai(self):
        """Process mob AI behaviors."""
        if not self.is_alive:
            return

        if self.position in ('sleeping', 'stunned', 'incapacitated'):
            return

        # Use advanced AI controller if available
        if self.ai_controller:
            await self.ai_controller.process()
            return

        # Otherwise, use simple fallback AI
        # If fighting, just fight
        if self.is_fighting:
            await self.combat_ai()
            return

        # Random chance to act each tick
        if random.randint(1, 100) > 10:
            return

        # Check for aggressive behavior
        if 'aggressive' in self.flags:
            await self.aggressive_ai()
            return

        # Check for special behaviors
        if self.special:
            await self.special_ai()
            return

        # Wander behavior
        if 'sentinel' not in self.flags:
            await self.wander_ai()
            
    async def combat_ai(self):
        """AI behavior during combat."""
        if not self.fighting or not self.fighting.is_alive:
            self.fighting = None
            self.position = 'standing'
            return
            
        # Cast spells if caster
        if 'caster' in self.flags and self.mana > 20:
            if random.randint(1, 100) <= 30:
                await self.cast_mob_spell()
                return
                
        # Special attacks
        if random.randint(1, 100) <= 20:
            await self.special_attack()
            
    async def aggressive_ai(self):
        """Check for and attack valid targets."""
        if not self.room:
            return

        # Find potential targets (excluding hidden/sneaking players who pass their check)
        targets = []
        for char in self.room.characters:
            if char == self or not hasattr(char, 'connection') or char.is_fighting:
                continue

            # Check if player is hidden or sneaking
            if 'hidden' in char.flags or 'sneaking' in char.flags:
                # Mob tries to detect the player
                # Detection chance = mob level vs player skill
                # Base detection = (mob_level * 5) vs (player_skill)
                detection_chance = self.level * 5

                # Player's best stealth skill
                hide_skill = char.skills.get('hide', 0)
                sneak_skill = char.skills.get('sneak', 0)
                stealth_skill = max(hide_skill, sneak_skill)

                # Roll detection check
                mob_roll = random.randint(1, 100) + detection_chance
                player_roll = random.randint(1, 100) + stealth_skill

                # If mob fails to detect, skip this player
                if player_roll >= mob_roll:
                    continue

                # Mob detected the player! Reveal them
                if 'hidden' in char.flags:
                    char.flags.remove('hidden')
                    c = self.config.COLORS
                    await char.send(f"{c['yellow']}{self.name} spots you!{c['reset']}")
                    await self.room.send_to_room(
                        f"{c['yellow']}{self.name} spots {char.name} hiding!{c['reset']}",
                        exclude=[char]
                    )

            # Add to targets
            targets.append(char)

        if not targets:
            return

        # Don't attack if room is peaceful
        if 'peaceful' in self.room.flags:
            return

        # Pick a random target
        target = random.choice(targets)

        # Announce and attack
        c = self.config.COLORS
        await self.room.send_to_room(
            f"{c['bright_red']}{self.name} attacks {target.name}!{c['reset']}"
        )

        from combat import CombatHandler
        await CombatHandler.start_combat(self, target)
        
    async def wander_ai(self):
        """Randomly move to adjacent rooms."""
        if not self.room or not self.room.exits:
            return
            
        # Get valid exits
        valid_exits = []
        for direction, exit_data in self.room.exits.items():
            if exit_data and exit_data.get('room'):
                target_room = exit_data['room']
                # Don't wander into no_mob rooms
                if 'no_mob' in target_room.flags:
                    continue
                # Don't wander out of home zone (unless no home zone set)
                if self.home_zone is not None:
                    target_zone = target_room.vnum // 100  # Calculate zone from room vnum
                    if target_zone != self.home_zone:
                        continue
                valid_exits.append((direction, target_room))
                    
        if not valid_exits:
            return
            
        # Small chance to wander
        if random.randint(1, 100) > 10:
            return
            
        direction, target_room = random.choice(valid_exits)
        
        # Leave current room
        await self.room.send_to_room(f"{self.name} leaves {direction}.")
        self.room.characters.remove(self)
        
        # Enter new room
        self.room = target_room
        target_room.characters.append(self)
        
        opposite = self.config.DIRECTIONS.get(direction, {}).get('opposite', 'somewhere')
        await target_room.send_to_room(f"{self.name} arrives from the {opposite}.")
        
    async def special_ai(self):
        """Handle special mob behaviors."""
        if self.special == 'healer':
            await self.healer_ai()
        elif self.special == 'shopkeeper':
            pass  # Shopkeepers handled by commands
        elif self.special == 'trainer':
            pass  # Trainers handled by commands
        elif self.special == 'druid':
            await self.druid_ai()
            
    async def healer_ai(self):
        """Healer NPC AI - offer healing to wounded players."""
        if not self.room:
            return
            
        for char in self.room.characters:
            if hasattr(char, 'connection'):  # Is a player
                if char.hp < char.max_hp * 0.5:
                    c = self.config.COLORS
                    await char.send(f"\r\n{c['bright_cyan']}{self.name} says, 'You look wounded, traveler. Say \"heal\" and I shall aid you.'{c['reset']}")
                    break
                    
    async def druid_ai(self):
        """Druid NPC AI."""
        if not self.room:
            return
            
        if random.randint(1, 100) <= 5:
            messages = [
                "hums a tune that seems to resonate with the forest.",
                "touches a nearby tree and whispers ancient words.",
                "scatters seeds that seem to glow faintly.",
                "communes silently with nature.",
            ]
            c = self.config.COLORS
            await self.room.send_to_room(f"{c['green']}{self.name} {random.choice(messages)}{c['reset']}")
            
    async def cast_mob_spell(self):
        """Cast a spell during combat."""
        if not self.fighting:
            return
            
        c = self.config.COLORS
        target = self.fighting
        
        # Different spells based on mob type
        if self.special == 'necromancer':
            spells = ['chill_touch', 'energy_drain', 'fear']
        elif self.special == 'shaman':
            spells = ['poison', 'blindness', 'weaken']
        elif 'dragon' in self.name.lower():
            spells = ['fireball', 'fear']
        else:
            spells = ['magic_missile', 'chill_touch']
            
        spell = random.choice(spells)
        
        # Calculate damage
        damage = random.randint(self.level, self.level * 3)
        
        await self.room.send_to_room(
            f"{c['bright_magenta']}{self.name} casts {spell.replace('_', ' ')}!{c['reset']}"
        )
        
        if hasattr(target, 'send'):
            await target.send(f"{c['bright_red']}{self.name}'s spell hits you for {damage} damage!{c['reset']}")
            
        self.mana -= 20
        
        killed = await target.take_damage(damage, self)
        if killed:
            from combat import CombatHandler
            await CombatHandler.handle_death(self, target)
            
    async def special_attack(self):
        """Perform a special attack based on mob type."""
        if not self.fighting:
            return
            
        c = self.config.COLORS
        target = self.fighting
        
        attack_type = None
        damage_mult = 1.0
        
        if 'poison' in self.flags or self.special == 'poison':
            attack_type = 'poisons'
            damage_mult = 0.5
            # TODO: Apply poison effect
        elif 'dragon' in self.name.lower() or self.special == 'firebreath':
            attack_type = 'breathes fire on'
            damage_mult = 2.0
        elif 'troll' in self.name.lower() or self.special == 'regenerate':
            # Trolls regenerate during combat
            regen = self.max_hp // 10
            self.hp = min(self.max_hp, self.hp + regen)
            await self.room.send_to_room(
                f"{c['green']}{self.name}'s wounds begin to close.{c['reset']}"
            )
            return
        elif self.special == 'paralyze':
            attack_type = 'tries to paralyze'
            if random.randint(1, 100) <= 20:
                if hasattr(target, 'position'):
                    target.position = 'stunned'
                await self.room.send_to_room(
                    f"{c['yellow']}{target.name} is paralyzed!{c['reset']}"
                )
            return
            
        if attack_type:
            damage = int(self.roll_dice(self.damage_dice) * damage_mult)
            await self.room.send_to_room(
                f"{c['bright_red']}{self.name} {attack_type} {target.name}! [{damage}]{c['reset']}"
            )
            
            killed = await target.take_damage(damage, self)
            if killed:
                from combat import CombatHandler
                await CombatHandler.handle_death(self, target)
                
    async def take_damage(self, amount: int, attacker: 'Character' = None) -> bool:
        """Take damage, return True if killed."""
        self.hp -= amount
        
        # Wimpy mobs flee
        if 'wimpy' in self.flags and self.hp < self.max_hp * 0.2:
            if self.fighting:
                self.fighting.fighting = None
            self.fighting = None
            self.position = 'standing'
            # Try to flee
            await self.flee()
            return False
            
        if self.hp <= 0:
            await self.die(attacker)
            return True
        return False
        
    async def flee(self):
        """Attempt to flee from combat."""
        if not self.room or not self.room.exits:
            return
            
        valid_exits = [
            (d, e['room']) for d, e in self.room.exits.items() 
            if e and e.get('room') and 'no_mob' not in e['room'].flags
        ]
        
        if valid_exits:
            direction, target_room = random.choice(valid_exits)
            
            c = self.config.COLORS
            await self.room.send_to_room(f"{c['yellow']}{self.name} flees {direction}!{c['reset']}")
            
            self.room.characters.remove(self)
            self.room = target_room
            target_room.characters.append(self)
            
    async def die(self, killer: 'Character' = None):
        """Handle mob death."""
        if self.fighting:
            self.fighting.fighting = None
            self.fighting = None
            
        self.position = 'dead'
        
        c = self.config.COLORS
        if self.room:
            await self.room.send_to_room(
                f"{c['red']}{self.name} is DEAD!{c['reset']}"
            )
            
    async def regen_tick(self):
        """Regenerate HP/mana and process affects."""
        # Process affects (damage over time, healing over time, expiration)
        await AffectManager.tick_affects(self)

        if not self.is_fighting:
            # Simple regen for mobs (5% HP, 10% mana)
            # Could use enhanced regen but keep it simpler for NPCs
            self.hp = min(self.max_hp, self.hp + max(1, self.max_hp // 20))
            self.mana = min(self.max_mana, self.mana + max(1, self.max_mana // 10))
            
    def get_hit_bonus(self):
        """Calculate hit bonus (to hit / THAC0)."""
        bonus = self.level // 2
        # DEX is primary factor for accuracy
        bonus += (self.dex - 10) // 2
        # STR provides minor bonus
        bonus += (self.str - 10) // 4
        return bonus

    def get_damage_bonus(self):
        """Calculate damage bonus."""
        bonus = self.level // 4
        # STR is primary factor for damage
        bonus += (self.str - 10) // 2
        return bonus
        
    def get_armor_class(self):
        """Get effective armor class (lower is better)."""
        ac = self.armor_class
        # DEX improves AC (makes you harder to hit)
        ac -= (self.dex - 10) // 2 * 10
        return ac
