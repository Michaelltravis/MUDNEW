"""
Help system data for RealmsMUD.
Contains detailed information about commands, skills, spells, and game mechanics.
"""

HELP_TOPICS = {
    # ==================== SKILLS ====================
    'sneak': {
        'category': 'skill',
        'classes': ['thief', 'assassin', 'ranger'],
        'title': 'Sneak',
        'syntax': 'sneak',
        'description': '''
Sneak allows you to move silently and avoid detection by enemies and other players.

MECHANICS:
- When activated, you gain the 'sneaking' flag
- Success chance is based on your sneak skill percentage
- Higher skill = better chance of remaining undetected
- Sneaking reduces chance of random mob aggro
- Breaking stealth: Attacking, talking, or failed skill checks break sneak

USAGE:
- Type 'sneak' to toggle sneaking on
- Type 'sneak' again or 'visible' to turn it off
- Moving while sneaking has a chance to fail based on skill level

SKILL IMPROVEMENT:
- Improves through use (difficulty: 3)
- Each successful sneak attempt has a chance to increase skill
- Maximum skill: 95%

TIPS:
- Use with 'hide' for complete stealth
- Higher DEX improves effectiveness
- Essential for backstab attempts
''',
    },

    'hide': {
        'category': 'skill',
        'classes': ['thief', 'assassin', 'ranger'],
        'title': 'Hide',
        'syntax': 'hide',
        'description': '''
Hide allows you to conceal yourself in shadows, making you invisible to others.

MECHANICS:
- Success chance based on hide skill percentage
- Adds 'hidden' flag to your character
- While hidden, you are invisible to look/who commands
- Moving while hidden will break hiding
- Attacking breaks hiding

USAGE:
- Type 'hide' to attempt to hide
- Success message: "You attempt to hide in the shadows..."
- Failure message: "You fail to conceal yourself."
- Type 'visible' to reveal yourself

SKILL IMPROVEMENT:
- Improves through use (difficulty: 3)
- Each successful hide attempt has a chance to increase skill
- Maximum skill: 95%

SYNERGY:
- Combine with sneak for maximum stealth
- Required for effective backstab attempts
- Works best in dark or cluttered environments
''',
    },

    'backstab': {
        'category': 'skill',
        'classes': ['thief', 'assassin'],
        'title': 'Backstab',
        'syntax': 'backstab <target>',
        'description': '''
Backstab is a devastating attack that deals massive damage when executed from hiding.

MECHANICS:
- Base damage: 1x to 3x your level
- Damage multiplier: 3x to 6x (based on skill level)
  - Skill 0-24: 3x damage
  - Skill 25-49: 4x damage
  - Skill 50-74: 5x damage
  - Skill 75+: 6x damage
- Must not be fighting to use
- Works best from hidden/sneaking state

REQUIREMENTS:
- Must have backstab skill
- Target must be alive and present
- Cannot backstab while already in combat

USAGE:
- hide (optional but recommended)
- sneak (optional but recommended)
- backstab <target>
- Follow up with normal combat

SKILL IMPROVEMENT:
- Improves through use (difficulty: 5)
- Each backstab attempt has a chance to increase skill
- Success or failure both can improve skill

TIPS:
- Hide before backstabbing for surprise advantage
- Use a piercing weapon (dagger) for best results
- Opens combat, so be ready to fight or flee
- Most effective against unaware targets
''',
    },

    'pick_lock': {
        'category': 'skill',
        'classes': ['thief', 'assassin'],
        'title': 'Pick Lock',
        'syntax': 'pick <door/container>',
        'description': '''
Pick Lock allows you to open locked doors and containers without a key.

MECHANICS:
- Success based on pick_lock skill vs lock difficulty
- Roll 1d100, need: roll ≤ skill AND roll + skill ≥ difficulty
- Each lock has a difficulty rating (typically 20-80)
- Failure wastes time but can be retried

USAGE:
- pick door north - Pick door in that direction
- pick chest - Pick a container in the room
- pick <container name> - Pick specific container

LOCK DIFFICULTIES:
- Easy locks: 20-30 difficulty
- Medium locks: 40-60 difficulty
- Hard locks: 70-90 difficulty

SKILL IMPROVEMENT:
- Improves through use
- Both successes and failures can improve skill
- More difficult locks = better skill gains

TIPS:
- Save keys when possible - picking isn't guaranteed
- Some magical locks cannot be picked
- Pair with search to find hidden locks
''',
    },

    # ==================== SPELLS ====================
    'armor': {
        'category': 'spell',
        'classes': ['cleric', 'mage'],
        'level': 1,
        'mana': 10,
        'title': 'Armor',
        'syntax': 'cast armor [target]',
        'description': '''
Armor surrounds the target with a protective magical field.

MECHANICS:
- Reduces AC by 20 points (better armor class)
- Duration: 24 game hours (24 ticks)
- Affects: Armor Class
- Can target self or others

MANA COST: 10
CASTING TIME: 1 round
DURATION: 24 hours

USAGE:
- cast armor - Casts on yourself
- cast armor <name> - Casts on target player

TIPS:
- Essential buff for any adventurer
- Stacks with physical armor
- Recast before duration expires
- Low mana cost makes it efficient
''',
    },

    'heal': {
        'category': 'spell',
        'classes': ['cleric'],
        'level': 5,
        'mana': 50,
        'title': 'Heal',
        'syntax': 'cast heal [target]',
        'description': '''
Heal channels divine energy to restore hit points to the target.

MECHANICS:
- Restores 100 HP instantly
- Can target self or others
- No healing over time component
- Cannot exceed maximum HP

MANA COST: 50
CASTING TIME: 1 round
EFFECT: Restores 100 HP

USAGE:
- cast heal - Heals yourself
- cast heal <name> - Heals target player
- Most effective during/after combat

TIPS:
- Primary healing spell for Clerics
- More efficient than multiple cure light wounds
- Save mana by resting when out of combat
- Essential for group survival
''',
    },

    'cure_light': {
        'category': 'spell',
        'classes': ['cleric', 'druid'],
        'level': 1,
        'mana': 10,
        'title': 'Cure Light Wounds',
        'syntax': 'cast cure light [target]',
        'description': '''
Cure Light Wounds heals minor injuries with divine magic.

MECHANICS:
- Heals 1d8 + level HP (average: 4 + level)
- Level 1: ~5 HP
- Level 5: ~9 HP
- Level 10: ~14 HP
- Can target self or others

MANA COST: 10
CASTING TIME: 1 round
HEALING: 1d8 + caster level

USAGE:
- cast cure light - Heals yourself
- cast cure light <name> - Heals target
- Good for minor healing needs

EFFICIENCY:
- Low level: Most efficient healing per mana
- High level: Less efficient than Heal
- Good for topping off HP between fights
''',
    },

    'cure_serious': {
        'category': 'spell',
        'classes': ['cleric', 'druid'],
        'level': 7,
        'mana': 25,
        'title': 'Cure Serious Wounds',
        'syntax': 'cast cure serious [target]',
        'description': '''
Cure Serious Wounds heals moderate injuries with divine magic.

MECHANICS:
- Heals 3d8 + level HP (average: 13 + level)
- Level 7: ~20 HP
- Level 10: ~23 HP
- Level 15: ~28 HP
- Can target self or others

MANA COST: 25
CASTING TIME: 1 round
HEALING: 3d8 + caster level

USAGE:
- cast cure serious - Heals yourself
- cast cure serious <name> - Heals target
- Mid-combat emergency healing

EFFICIENCY:
- Better healing per mana than cure light
- Not as efficient as Heal at high levels
- Good middle-ground option
''',
    },

    'magic_missile': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 1,
        'mana': 10,
        'title': 'Magic Missile',
        'syntax': 'cast magic missile <target>',
        'description': '''
Magic Missile launches unerring bolts of magical force at a target.

MECHANICS:
- Damage: (1d4 + 1) x missiles
- Number of missiles: level / 2 (minimum 1, maximum 5)
  - Level 1-2: 1 missile (1d4+1 damage)
  - Level 3-4: 2 missiles (2d4+2 damage)
  - Level 5-6: 3 missiles (3d4+3 damage)
  - Level 7-8: 4 missiles (4d4+4 damage)
  - Level 9+: 5 missiles (5d4+5 damage)
- Never misses
- Ignores armor

MANA COST: 10
CASTING TIME: 1 round
DAMAGE TYPE: Force (unblockable)

USAGE:
- cast magic missile <target>
- Excellent against high-AC enemies
- Reliable damage source

TIPS:
- Scales with level automatically
- Cannot be resisted or dodged
- Low mana cost makes it efficient
- Good opening spell in combat
''',
    },

    'fireball': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 8,
        'mana': 30,
        'title': 'Fireball',
        'syntax': 'cast fireball <target>',
        'description': '''
Fireball hurls an explosive sphere of flame at a target.

MECHANICS:
- Damage: 8d6 + level (average: 28 + level)
- Level 8: ~36 damage
- Level 10: ~38 damage
- Level 15: ~43 damage
- Saving throw: INT-based for half damage
- Area effect (single target in this implementation)

MANA COST: 30
CASTING TIME: 1 round
DAMAGE TYPE: Fire

WEATHER MODIFIERS:
- Rainy: -20% damage
- Stormy: -30% damage
- Clear: Normal damage
- Hot/Dry: +10% damage

USAGE:
- cast fireball <target>
- High damage, high mana cost
- Best used against single tough enemies

TIPS:
- Check weather before casting
- Most powerful low-level damage spell
- Save for tough encounters
- Enemies may resist fire
''',
    },

    'lightning_bolt': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 10,
        'mana': 35,
        'title': 'Lightning Bolt',
        'syntax': 'cast lightning bolt <target>',
        'description': '''
Lightning Bolt calls down a crackling bolt of electricity.

MECHANICS:
- Damage: 10d6 + level (average: 35 + level)
- Level 10: ~45 damage
- Level 15: ~50 damage
- Level 20: ~55 damage
- Saving throw: DEX-based for half damage

MANA COST: 35
CASTING TIME: 1 round
DAMAGE TYPE: Lightning

WEATHER MODIFIERS:
- Stormy: +50% damage
- Rainy: +20% damage
- Clear: Normal damage
- Dry: -10% damage

USAGE:
- cast lightning bolt <target>
- Highest single-target damage
- Best during storms

TIPS:
- Storm weather dramatically increases damage
- More reliable than fireball in rain
- DEX save is easier than INT for many enemies
- Expensive but devastating
''',
    },

    'bless': {
        'category': 'spell',
        'classes': ['cleric', 'paladin'],
        'level': 3,
        'mana': 15,
        'title': 'Bless',
        'syntax': 'cast bless [target]',
        'description': '''
Bless imbues the target with divine favor, improving combat ability.

MECHANICS:
- +10 bonus to hit rolls
- Duration: 12 game hours
- Can target self or others
- Stacks with other bonuses

MANA COST: 15
CASTING TIME: 1 round
DURATION: 12 hours
AFFECTS: Hit Roll +10

USAGE:
- cast bless - Blesses yourself
- cast bless <name> - Blesses target
- Cast before combat for best results

TIPS:
- Essential buff for warriors
- Combines well with armor spell
- Recast when duration expires
- Group benefit - bless all party members
''',
    },

    'curse': {
        'category': 'spell',
        'classes': ['cleric', 'mage'],
        'level': 7,
        'mana': 25,
        'title': 'Curse',
        'syntax': 'cast curse <target>',
        'description': '''
Curse afflicts a target with supernatural misfortune.

MECHANICS:
- -10 penalty to hit rolls
- -10 penalty to saving throws
- Duration: 12 game hours
- Offensive spell (hostile action)

MANA COST: 25
CASTING TIME: 1 round
DURATION: 12 hours
AFFECTS: Hit Roll -10, Saves -10

USAGE:
- cast curse <target>
- Debilitates enemy combatants
- Initiate combat

TIPS:
- Use before major fights
- Stacks with other debuffs
- Makes enemies easier to hit
- Opposite of bless
''',
    },

    'invisibility': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 5,
        'mana': 30,
        'title': 'Invisibility',
        'syntax': 'cast invisibility [target]',
        'description': '''
Invisibility bends light around the target, rendering them unseen.

MECHANICS:
- Target becomes invisible
- Duration: 24 game hours or until combat
- Attacking breaks invisibility
- Movement does NOT break invisibility
- +50 bonus to sneak checks while invisible

MANA COST: 30
CASTING TIME: 1 round
DURATION: 24 hours (or until combat)

USAGE:
- cast invisibility - Turn yourself invisible
- cast invisibility <name> - Turn target invisible
- Scout areas safely

TIPS:
- Perfect for reconnaissance
- Broken by any aggressive action
- Use for escaping dangerous situations
- Combines with sneak for maximum stealth
''',
    },

    'haste': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 12,
        'mana': 40,
        'title': 'Haste',
        'syntax': 'cast haste [target]',
        'description': '''
Haste magically accelerates the target's movement and actions.

MECHANICS:
- +2 extra attacks per combat round
- +20 to initiative
- Duration: 10 game hours
- Movement speed increased 50%

MANA COST: 40
CASTING TIME: 1 round
DURATION: 10 hours (affected by weather)
AFFECTS: +2 attacks/round, +20 initiative

WEATHER EFFECTS:
- Storm: Duration doubled (20 hours)
- Clear: Normal duration
- Used in conjunction with combat for devastating effect

USAGE:
- cast haste - Haste yourself
- cast haste <name> - Haste target
- Pre-buff before boss fights

TIPS:
- Dramatically increases damage output
- Essential for damage dealers
- Expensive but game-changing
- Cast during storms for longer duration
''',
    },

    'teleport': {
        'category': 'spell',
        'classes': ['mage', 'sorcerer'],
        'level': 15,
        'mana': 50,
        'title': 'Teleport',
        'syntax': 'cast teleport <target>',
        'description': '''
Teleport instantly transports the caster to a target location.

MECHANICS:
- Instantly travel to target room
- Must know room vnum or have been there before
- Cannot teleport into no-teleport zones
- Cannot teleport while in combat
- 5% chance of mishap (random destination)

MANA COST: 50
CASTING TIME: 1 round
RANGE: Anywhere in world

RESTRICTIONS:
- Cannot use in no-magic zones
- Cannot use in combat
- Cannot teleport to private rooms
- Some zones block teleportation

USAGE:
- cast teleport 3001 - Teleport to room 3001
- Escape mechanism
- Fast travel

TIPS:
- Memorize important room vnums
- Have recall scroll as backup
- Don't use during combat
- Risky but fast
''',
    },

    # ==================== COMMANDS ====================
    'movement': {
        'category': 'basic',
        'title': 'Movement Commands',
        'syntax': 'north, south, east, west, up, down (or n, s, e, w, u, d)',
        'description': '''
Movement commands allow you to navigate through the world.

BASIC MOVEMENT:
- north (n) - Move north
- south (s) - Move south
- east (e) - Move east
- west (w) - Move west
- up (u) - Move up
- down (d) - Move down

RESTRICTIONS:
- Cannot move while sleeping (wake first)
- Cannot move while fighting (flee first)
- Need to stand if sitting/resting
- Doors must be opened first
- Some rooms require special conditions

MOVEMENT COSTS:
- Move points consumed per room
- More in difficult terrain
- Weather affects movement cost:
  - Clear: Normal cost
  - Rain: +20% cost
  - Storm: +50% cost
  - Snow: +40% cost

TIPS:
- Check 'exits' to see available directions
- Use 'look <direction>' to peek ahead
- Open doors before trying to move through them
- Rest to recover movement points
''',
    },

    'combat': {
        'category': 'basic',
        'title': 'Combat System',
        'syntax': 'kill <target>, flee',
        'description': '''
Combat in RealmsMUD is automatic once initiated.

STARTING COMBAT:
- kill <target> - Attack a target
- backstab <target> - Sneak attack (thieves)
- cast <offensive spell> <target> - Magical attack

DURING COMBAT:
- Combat rounds occur automatically every 2 seconds
- Damage based on weapon, stats, and skills
- Hit chance based on: your hit bonus vs their AC
- Can cast spells or use items during combat
- Cannot move (must flee first)

COMBAT STATS:
- HP: Hit points - when 0, you die
- AC: Armor class - lower is better
- Hitroll: Bonus to hit attacks
- Damroll: Bonus damage on hits

ENDING COMBAT:
- Kill your opponent
- Use 'flee' command to escape
- Fleeing costs XP and goes random direction
- Opponent gets free attack when you flee

DEATH:
- Lose experience points
- Drop corpse with your items
- Respawn at recall point
- Can retrieve items from corpse

TIPS:
- Check opponent condition: 'consider <target>'
- Flee before dying to save XP
- Use healing spells/potions during combat
- Buffs (bless, armor) applied before combat help
''',
    },

    'doors': {
        'category': 'basic',
        'title': 'Doors and Locks',
        'syntax': 'open/close/lock/unlock/pick <door/direction>',
        'description': '''
Doors can be opened, closed, locked, and picked.

DOOR COMMANDS:
- open door north - Open door to the north
- close door south - Close door to the south
- lock door east - Lock door (requires key)
- unlock door west - Unlock door (requires key)
- pick door north - Pick lock (thieves only)

DOOR STATES:
- Open: Can pass through freely
- Closed: Blocks movement and sight
- Locked: Requires key or picking
- Broken: Permanently open (from break door spell)
- Blocked: Magically sealed (from block door spell)

KEYS:
- Required for locking/unlocking
- Must be in inventory
- Each lock has specific key
- Keys not consumed when used

PICKING LOCKS:
- Requires pick_lock skill (thieves/assassins)
- Success based on skill vs difficulty
- Can retry if failed
- Improves skill over time

TIPS:
- Close doors behind you for privacy
- Lock valuables in containers
- Thieves can pick most locks
- Some magical locks cannot be picked
- 'exits' shows door states
''',
    },

    'containers': {
        'category': 'basic',
        'title': 'Containers and Storage',
        'syntax': 'open/close <container>, put/get <item> [container]',
        'description': '''
Containers store items and can be locked for security.

BASIC COMMANDS:
- open chest - Open a container
- close chest - Close a container
- put sword chest - Put item in container
- get sword chest - Get item from container
- get all chest - Get all items from container
- look in chest - See what's inside

CONTAINER TYPES:
- Chests: Large storage containers
- Bags: Portable containers
- Corpses: Special containers from dead mobs/players
- Backpacks: Wearable storage

CONTAINER PROPERTIES:
- Capacity: Maximum weight it can hold
- Closed state: Can be opened/closed
- Locked state: Requires key or picking
- Contents: Items and gold inside

GOLD IN CONTAINERS:
- Containers can hold gold coins
- get gold chest - Get gold from container
- put 100 gold chest - Put gold in container
- get all chest - Gets items AND gold

CORPSES:
- Contain items from dead mobs/players
- Decay after 30 minutes (game time)
- Can loot, get all, or sacrifice
- sacrifice corpse - Destroys corpse, gives 1 gold

TIPS:
- Use containers to organize inventory
- Lock important containers
- Check corpses quickly before decay
- Sacrifice empty corpses for gold
''',
    },

    'aliases': {
        'category': 'basic',
        'title': 'Alias System',
        'syntax': 'alias <word> <command>, unalias <word>',
        'description': '''
Aliases let you create shortcuts for frequently used commands.

CREATING ALIASES:
- alias k kill - Creates 'k' as shortcut for 'kill'
- alias op open - Creates 'op' for open
- alias bs backstab - Creates 'bs' for backstab
- alias n north - Creates 'n' for north

USING ALIASES:
- Type your alias word + arguments
- k goblin - Executes 'kill goblin'
- op door north - Executes 'open door north'
- Arguments are appended automatically

VIEWING ALIASES:
- alias - Shows all your aliases
- alias k - Shows what 'k' is aliased to

REMOVING ALIASES:
- unalias k - Removes the 'k' alias
- unalias <word> - Removes any alias

COMMON ALIASES:
- alias n north
- alias s south
- alias e east
- alias w west
- alias k kill
- alias cl cast cure light
- alias cs cast cure serious

TIPS:
- Aliases save with your character
- Can't create aliases for non-existent commands
- Can't use reserved command names
- Keep aliases short (1-3 letters)
- Speeds up gameplay significantly
''',
    },

    'communication': {
        'category': 'basic',
        'title': 'Communication',
        'syntax': 'say/tell/emote/shout',
        'description': '''
Multiple channels of communication are available.

SAY:
- say <message> - Talk to people in same room
- ' <message> - Shortcut for say
- Everyone in room sees message

TELL:
- tell <player> <message> - Private message
- reply <message> - Reply to last tell
- Only target player sees message

SHOUT:
- shout <message> - Yell across the zone
- Everyone in zone hears
- Costs movement points

EMOTE:
- emote <action> - Perform an action
- : <action> - Shortcut for emote
- Example: "emote waves" shows "Sorin waves."

SOCIAL COMMANDS:
- smile, wave, bow, hug, etc.
- Interactive social actions
- Can target other players
- smile sorin - "You smile at Sorin."

GROUP CHAT:
- gtell <message> - Message your group
- All group members receive message
- Essential for group coordination

TIPS:
- Use tell for private conversations
- Use say for local chatter
- Emotes add personality
- Don't spam shout
''',
    },

    'equipment': {
        'category': 'basic',
        'title': 'Equipment and Inventory',
        'syntax': 'wear/remove/wield, inventory, equipment',
        'description': '''
Manage your character's equipment and possessions.

INVENTORY COMMANDS:
- inventory (i) - List items you're carrying
- equipment (eq) - Show worn/wielded equipment
- look <item> - Examine an item

EQUIPPING ITEMS:
- wear armor - Wear an armor piece
- wield sword - Equip a weapon in main hand
- hold shield - Hold item in off-hand
- remove armor - Remove equipped item
- remove all - Remove all equipment

EQUIPMENT SLOTS:
- light - Light source
- finger1, finger2 - Rings
- neck1, neck2 - Amulets/necklaces
- body - Chest armor
- head - Helmet
- legs - Leg armor
- feet - Boots
- hands - Gloves
- arms - Arm guards
- shield - Shield (off-hand)
- about - Cloak/cape
- waist - Belt
- wrist1, wrist2 - Bracers
- wield - Primary weapon
- hold - Secondary item

ITEM PROPERTIES:
- Armor: Reduces damage taken (AC bonus)
- Weapons: Damage dice and type
- Magic items: Special effects/stat bonuses
- Weight: Affects how much you can carry

TIPS:
- Better equipment = better survival
- Check item stats before equipping
- Magical items have colored descriptions
- Weight affects movement
- Some items have level requirements
''',
    },
}

# Category index for help listing
HELP_CATEGORIES = {
    'skills': ['sneak', 'hide', 'backstab', 'pick_lock', 'kick', 'bash', 'rescue',
               'disarm', 'second_attack', 'third_attack', 'parry', 'steal', 'detect_traps',
               'trip', 'circle', 'track', 'dual_wield', 'turn_undead', 'lay_hands',
               'envenom', 'assassinate', 'garrote', 'shadow_step', 'mark_target', 'lore', 'scribe'],
    'spells': ['armor', 'heal', 'cure_light', 'cure_serious', 'cure_critical', 'group_heal',
               'bless', 'curse', 'sanctuary', 'remove_curse', 'remove_poison',
               'magic_missile', 'burning_hands', 'chill_touch', 'fireball', 'lightning_bolt',
               'meteor_swarm', 'chain_lightning', 'sleep', 'color_spray', 'charm_person',
               'teleport', 'fly', 'invisibility', 'haste', 'slow', 'detect_magic', 'identify',
               'enchant_weapon', 'create_food', 'create_water', 'summon', 'word_of_recall',
               'resurrect', 'harm', 'dispel_evil', 'earthquake', 'flamestrike',
               'faerie_fire', 'call_lightning', 'barkskin', 'entangle', 'detect_evil',
               'protection_from_evil', 'animate_dead', 'vampiric_touch', 'enervation',
               'death_grip', 'summon_undead', 'finger_of_death', 'energy_drain',
               'poison', 'weaken', 'blindness', 'fear', 'heroism', 'mass_charm'],
    'basic': ['movement', 'combat', 'doors', 'containers', 'aliases',
              'communication', 'equipment'],
}


def get_help_text(topic: str) -> str:
    """Get formatted help text for a topic."""
    topic = topic.lower().replace(' ', '_')

    if topic in HELP_TOPICS:
        help_data = HELP_TOPICS[topic]
        output = []
        output.append(f"{'=' * 70}")
        output.append(f"{help_data['title'].center(70)}")
        output.append(f"{'=' * 70}")

        if 'syntax' in help_data:
            output.append(f"\nSYNTAX: {help_data['syntax']}")

        if help_data['category'] == 'skill':
            output.append(f"AVAILABLE TO: {', '.join(help_data['classes'])}")
        elif help_data['category'] == 'spell':
            output.append(f"AVAILABLE TO: {', '.join(help_data['classes'])}")
            output.append(f"LEVEL: {help_data['level']} | MANA: {help_data['mana']}")

        output.append(help_data['description'])
        output.append(f"{'=' * 70}")

        return '\n'.join(output)

    # Check if it's a valid spell/skill that just doesn't have help yet
    for category, topics in HELP_CATEGORIES.items():
        if topic in topics:
            return f'''{'=' * 70}
{topic.replace('_', ' ').title().center(70)}
{'=' * 70}

This {category[:-1]} is available in the game but detailed help documentation
is still being written.

Try 'help' for a full list of topics with documentation.
{'=' * 70}'''

    return None


def get_help_index() -> str:
    """Get a categorized index of all help topics."""
    output = []
    output.append(f"{'=' * 70}")
    output.append("HELP SYSTEM".center(70))
    output.append(f"{'=' * 70}")
    output.append("\nType 'help <topic>' for detailed information.\n")

    output.append("SKILLS:")
    for topic in HELP_CATEGORIES['skills']:
        output.append(f"  {topic}")

    output.append("\nSPELLS:")
    for topic in HELP_CATEGORIES['spells']:
        output.append(f"  {topic}")

    output.append("\nBASIC COMMANDS:")
    for topic in HELP_CATEGORIES['basic']:
        output.append(f"  {topic}")

    output.append(f"\n{'=' * 70}")

    return '\n'.join(output)
