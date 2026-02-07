# Generated help entries
# Add these to help_data.py HELP_TOPICS dictionary

HELP_TOPICS_NEW = {
    'aegis': {
        'keywords': ['aegis', 'aegis'],
        'text': '''
Spell: Aegis
============

Description:
  Aegis grants magical effects that enhance you or an ally.
  Effects:
    - Grants spell resist
  Duration: 15 game ticks (~7 minutes)

Mana Cost: 65
Target: Defensive

Usage:
  cast aegis [target]    - Target yourself or an ally
  Example: cast aegis         - Cast on yourself
  Example: cast aegis friend  - Cast on an ally
'''
    },
    'barkskin': {
        'keywords': ['barkskin', 'barkskin'],
        'text': '''
Spell: Barkskin
===============

Description:
  Barkskin grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 35
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 40
Target: Defensive

Usage:
  cast barkskin [target]    - Target yourself or an ally
  Example: cast barkskin         - Cast on yourself
  Example: cast barkskin friend  - Cast on an ally
'''
    },
    'blindness': {
        'keywords': ['blindness', 'blindness'],
        'text': '''
Spell: Blindness
================

Description:
  Blindness grants magical effects that weaken or hinder your target.
  Effects:
    - Grants blind
    - Decreases attack accuracy by 4
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 25
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast blindness <target>
  Example: cast blindness goblin
'''
    },
    'blink': {
        'keywords': ['blink', 'blink'],
        'text': '''
Spell: Blink
============

Description:
  Blink grants magical effects that enhance you or an ally.
  Effects:
    - Grants blink
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 30
Target: Self

Usage:
  cast blink
'''
    },
    'block_door': {
        'keywords': ['block_door', 'block door'],
        'text': '''
Spell: Block Door
=================

Description:
  Block Door provides special magical effects.
  Affects doors and barriers with magical force.

Mana Cost: 50
Target: Door
Level Required: 10

Usage:
  cast block_door <direction>
  Example: cast block_door north
'''
    },
    'break_door': {
        'keywords': ['break_door', 'break door'],
        'text': '''
Spell: Break Door
=================

Description:
  Break Door provides special magical effects.
  Affects doors and barriers with magical force.

Mana Cost: 40
Target: Door
Level Required: 8

Usage:
  cast break_door <direction>
  Example: cast break_door north
'''
    },
    'burning_hands': {
        'keywords': ['burning_hands', 'burning hands'],
        'text': '''
Spell: Burning Hands
====================

Description:
  Burning Hands is an offensive spell that deals magical damage to your target.
  Base damage: 1d6+2 (+2 per level)
  Harness the power of fire to burn your enemies.

Mana Cost: 15
Target: Offensive

Usage:
  cast burning_hands <target>
  Example: cast burning_hands goblin
'''
    },
    'call_lightning': {
        'keywords': ['call_lightning', 'call lightning'],
        'text': '''
Spell: Call Lightning
=====================

Description:
  Call Lightning is an offensive spell that deals magical damage to your target.
  Base damage: 4d6+5 (+2 per level)
  Call down the fury of lightning upon your target.

Mana Cost: 45
Target: Offensive

Usage:
  cast call_lightning <target>
  Example: cast call_lightning goblin
'''
    },
    'chain_lightning': {
        'keywords': ['chain_lightning', 'chain lightning'],
        'text': '''
Spell: Chain Lightning
======================

Description:
  Chain Lightning is an offensive spell that deals magical damage to your target.
  Base damage: 6d6+8 (+3 per level)
  Call down the fury of lightning upon your target.

Mana Cost: 70
Target: Offensive

Usage:
  cast chain_lightning <target>
  Example: cast chain_lightning goblin
'''
    },
    'charm_person': {
        'keywords': ['charm_person', 'charm person'],
        'text': '''
Spell: Charm Person
===================

Description:
  Charm Person grants magical effects that weaken or hinder your target.
  Effects:
    - Grants charmed
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 30
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast charm_person <target>
  Example: cast charm_person goblin
'''
    },
    'chill_touch': {
        'keywords': ['chill_touch', 'chill touch'],
        'text': '''
Spell: Chill Touch
==================

Description:
  Chill Touch is an offensive spell that deals magical damage to your target.
  Base damage: 1d8 (+2 per level)
  Channel freezing cold to damage your foes.

Mana Cost: 15
Target: Offensive

Usage:
  cast chill_touch <target>
  Example: cast chill_touch goblin
'''
    },
    'color_spray': {
        'keywords': ['color_spray', 'color spray'],
        'text': '''
Spell: Color Spray
==================

Description:
  Color Spray is an offensive spell that deals magical damage to your target.
  Base damage: 2d6 (+2 per level)

Mana Cost: 25
Target: Offensive

Usage:
  cast color_spray <target>
  Example: cast color_spray goblin
'''
    },
    'create_food': {
        'keywords': ['create_food', 'create food'],
        'text': '''
Spell: Create Food
==================

Description:
  Create Food provides special magical effects.
  Conjures nourishing food from thin air.

Mana Cost: 10
Target: Self

Usage:
  cast create_food
'''
    },
    'create_water': {
        'keywords': ['create_water', 'create water'],
        'text': '''
Spell: Create Water
===================

Description:
  Create Water provides special magical effects.
  Creates fresh drinking water.

Mana Cost: 10
Target: Self

Usage:
  cast create_water
'''
    },
    'cure_critical': {
        'keywords': ['cure_critical', 'cure critical wounds'],
        'text': '''
Spell: Cure Critical Wounds
===========================

Description:
  Cure Critical Wounds restores health to you or an ally.
  Base healing: 3d8+6 (+2 per level)

Mana Cost: 35
Target: Defensive

Usage:
  cast cure_critical [target]    - Target yourself or an ally
  Example: cast cure_critical         - Cast on yourself
  Example: cast cure_critical friend  - Cast on an ally
'''
    },
    'death_grip': {
        'keywords': ['death_grip', 'death grip'],
        'text': '''
Spell: Death Grip
=================

Description:
  Death Grip is an offensive spell that deals magical damage to your target.
  Base damage: 3d8+3 (+2 per level)
  Wield the forces of death and decay.

Mana Cost: 45
Target: Offensive

Usage:
  cast death_grip <target>
  Example: cast death_grip goblin
'''
    },
    'detect_evil': {
        'keywords': ['detect_evil', 'detect evil'],
        'text': '''
Spell: Detect Evil
==================

Description:
  Detect Evil grants magical effects that enhance you or an ally.
  Effects:
    - Grants detect evil
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 10
Target: Self

Usage:
  cast detect_evil
'''
    },
    'detect_magic': {
        'keywords': ['detect_magic', 'detect magic'],
        'text': '''
Spell: Detect Magic
===================

Description:
  Detect Magic grants magical effects that enhance you or an ally.
  Effects:
    - Grants detect magic
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 10
Target: Self

Usage:
  cast detect_magic
'''
    },
    'dispel_evil': {
        'keywords': ['dispel_evil', 'dispel evil'],
        'text': '''
Spell: Dispel Evil
==================

Description:
  Dispel Evil is an offensive spell that deals magical damage to your target.
  Base damage: 4d8 (+3 per level)

Mana Cost: 40
Target: Offensive

Usage:
  cast dispel_evil <target>
  Example: cast dispel_evil goblin
'''
    },
    'dispel_magic': {
        'keywords': ['dispel_magic', 'dispel magic'],
        'text': '''
Spell: Dispel Magic
===================

Description:
  Dispel Magic provides special magical effects.
  Removes magical effects from the target.

Mana Cost: 50
Target: Defensive

Usage:
  cast dispel_magic [target]    - Target yourself or an ally
  Example: cast dispel_magic         - Cast on yourself
  Example: cast dispel_magic friend  - Cast on an ally
'''
    },
    'displacement': {
        'keywords': ['displacement', 'displacement'],
        'text': '''
Spell: Displacement
===================

Description:
  Displacement grants magical effects that enhance you or an ally.
  Effects:
    - Grants displacement
  Duration: 18 game ticks (~9 minutes)

Mana Cost: 35
Target: Self

Usage:
  cast displacement
'''
    },
    'divine_protection': {
        'keywords': ['divine_protection', 'divine protection'],
        'text': '''
Spell: Divine Protection
========================

Description:
  Divine Protection grants magical effects that enhance you or an ally.
  Effects:
    - Grants invulnerable
  Duration: 3 game ticks (~1 minutes)

Mana Cost: 100
Target: Self

Usage:
  cast divine_protection
'''
    },
    'divine_shield': {
        'keywords': ['divine_shield', 'divine shield'],
        'text': '''
Spell: Divine Shield
====================

Description:
  Divine Shield grants magical effects that enhance you or an ally.
  Effects:
    - Grants divine shield
  Duration: 6 game ticks (~3 minutes)

Mana Cost: 75
Target: Self

Usage:
  cast divine_shield
'''
    },
    'earthquake': {
        'keywords': ['earthquake', 'earthquake'],
        'text': '''
Spell: Earthquake
=================

Description:
  Earthquake is an offensive spell that deals magical damage to your target.
  Base damage: 5d8 (+2 per level)

Mana Cost: 90
Target: Room

Usage:
  cast earthquake
'''
    },
    'enchant_weapon': {
        'keywords': ['enchant_weapon', 'enchant weapon'],
        'text': '''
Spell: Enchant Weapon
=====================

Description:
  Enchant Weapon provides special magical effects.
  Permanently enhances a weapon with magical properties.

Mana Cost: 100
Target: Object

Usage:
  cast enchant_weapon <item>
  Example: cast enchant_weapon sword
'''
    },
    'energy_drain': {
        'keywords': ['energy_drain', 'energy drain'],
        'text': '''
Spell: Energy Drain
===================

Description:
  Energy Drain is an offensive spell that deals magical damage to your target.
  Base damage: 3d8 (+2 per level)

Mana Cost: 60
Target: Offensive

Usage:
  cast energy_drain <target>
  Example: cast energy_drain goblin
'''
    },
    'enervation': {
        'keywords': ['enervation', 'enervation'],
        'text': '''
Spell: Enervation
=================

Description:
  Enervation grants magical effects that weaken or hinder your target.
  Effects:
    - Decreases Strength by 3
    - Decreases Dexterity by 3
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 35
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast enervation <target>
  Example: cast enervation goblin
'''
    },
    'entangle': {
        'keywords': ['entangle', 'entangle'],
        'text': '''
Spell: Entangle
===============

Description:
  Entangle grants magical effects that weaken or hinder your target.
  Effects:
    - Grants entangled
  Duration: 6 game ticks (~3 minutes)

Mana Cost: 25
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast entangle <target>
  Example: cast entangle goblin
'''
    },
    'faerie_fire': {
        'keywords': ['faerie_fire', 'faerie fire'],
        'text': '''
Spell: Faerie Fire
==================

Description:
  Faerie Fire grants magical effects that weaken or hinder your target.
  Effects:
    - Reduces armor class by 20
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 20
Target: Offensive

Usage:
  cast faerie_fire <target>
  Example: cast faerie_fire goblin
'''
    },
    'fear': {
        'keywords': ['fear', 'fear'],
        'text': '''
Spell: Fear
===========

Description:
  Fear provides special magical effects.

Mana Cost: 30
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast fear <target>
  Example: cast fear goblin
'''
    },
    'finger_of_death': {
        'keywords': ['finger_of_death', 'finger of death'],
        'text': '''
Spell: Finger of Death
======================

Description:
  Finger of Death is an offensive spell that deals magical damage to your target.
  Base damage: 10d8+20 (+5 per level)
  Wield the forces of death and decay.

Mana Cost: 150
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast finger_of_death <target>
  Example: cast finger_of_death goblin
'''
    },
    'fire_shield': {
        'keywords': ['fire_shield', 'fire shield'],
        'text': '''
Spell: Fire Shield
==================

Description:
  Fire Shield grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 20
    - Grants fire shield
  Duration: 15 game ticks (~7 minutes)

Mana Cost: 50
Target: Self

Usage:
  cast fire_shield
'''
    },
    'flamestrike': {
        'keywords': ['flamestrike', 'flamestrike'],
        'text': '''
Spell: Flamestrike
==================

Description:
  Flamestrike is an offensive spell that deals magical damage to your target.
  Base damage: 4d8+10 (+2 per level)
  Harness the power of fire to burn your enemies.

Mana Cost: 60
Target: Offensive

Usage:
  cast flamestrike <target>
  Example: cast flamestrike goblin
'''
    },
    'fly': {
        'keywords': ['fly', 'fly'],
        'text': '''
Spell: Fly
==========

Description:
  Fly grants magical effects that enhance you or an ally.
  Effects:
    - Grants fly
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 30
Target: Defensive

Usage:
  cast fly [target]    - Target yourself or an ally
  Example: cast fly         - Cast on yourself
  Example: cast fly friend  - Cast on an ally
'''
    },
    'group_heal': {
        'keywords': ['group_heal', 'group heal'],
        'text': '''
Spell: Group Heal
=================

Description:
  Group Heal restores health to you or an ally.
  Base healing: 2d8+10 (+2 per level)

Mana Cost: 80
Target: Group

Usage:
  cast group_heal [target]    - Target yourself or an ally
  Example: cast group_heal         - Cast on yourself
  Example: cast group_heal friend  - Cast on an ally
'''
    },
    'harm': {
        'keywords': ['harm', 'harm'],
        'text': '''
Spell: Harm
===========

Description:
  Harm is an offensive spell that deals magical damage to your target.
  Base damage: 5d8 (+0 per level)
  Wield the forces of death and decay.

Mana Cost: 50
Target: Offensive

Usage:
  cast harm <target>
  Example: cast harm goblin
'''
    },
    'heroism': {
        'keywords': ['heroism', 'heroism'],
        'text': '''
Spell: Heroism
==============

Description:
  Heroism grants magical effects that enhance you or an ally.
  Effects:
    - Increases attack accuracy by 3
    - Increases damage by 3
    - Grants max hp
  Duration: 18 game ticks (~9 minutes)

Mana Cost: 40
Target: Defensive

Usage:
  cast heroism [target]    - Target yourself or an ally
  Example: cast heroism         - Cast on yourself
  Example: cast heroism friend  - Cast on an ally
'''
    },
    'holy_aura': {
        'keywords': ['holy_aura', 'holy aura'],
        'text': '''
Spell: Holy Aura
================

Description:
  Holy Aura grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 40
    - Grants saving throw
    - Grants spell resist
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 80
Target: Defensive

Usage:
  cast holy_aura [target]    - Target yourself or an ally
  Example: cast holy_aura         - Cast on yourself
  Example: cast holy_aura friend  - Cast on an ally
'''
    },
    'ice_armor': {
        'keywords': ['ice_armor', 'ice armor'],
        'text': '''
Spell: Ice Armor
================

Description:
  Ice Armor grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 25
    - Grants ice armor
  Duration: 18 game ticks (~9 minutes)

Mana Cost: 45
Target: Defensive

Usage:
  cast ice_armor [target]    - Target yourself or an ally
  Example: cast ice_armor         - Cast on yourself
  Example: cast ice_armor friend  - Cast on an ally
'''
    },
    'identify': {
        'keywords': ['identify', 'identify'],
        'text': '''
Spell: Identify
===============

Description:
  Identify provides special magical effects.
  Reveals the magical properties of an item.

Mana Cost: 20
Target: Object

Usage:
  cast identify <item>
  Example: cast identify sword
'''
    },
    'lay_hands': {
        'keywords': ['lay_hands', 'lay hands'],
        'text': '''
Spell: Lay Hands
================

Description:
  Lay Hands restores health to you or an ally.
  Base healing: 50

Mana Cost: 40
Target: Defensive

Usage:
  cast lay_hands [target]    - Target yourself or an ally
  Example: cast lay_hands         - Cast on yourself
  Example: cast lay_hands friend  - Cast on an ally
'''
    },
    'mana_shield': {
        'keywords': ['mana_shield', 'mana shield'],
        'text': '''
Spell: Mana Shield
==================

Description:
  Mana Shield grants magical effects that enhance you or an ally.
  Effects:
    - Grants mana shield
  Duration: 10 game ticks (~5 minutes)

Mana Cost: 50
Target: Self

Usage:
  cast mana_shield
'''
    },
    'mass_charm': {
        'keywords': ['mass_charm', 'mass charm'],
        'text': '''
Spell: Mass Charm
=================

Description:
  Mass Charm provides special magical effects.

Mana Cost: 100
Target: Room

Usage:
  cast mass_charm
'''
    },
    'meteor_swarm': {
        'keywords': ['meteor_swarm', 'meteor swarm'],
        'text': '''
Spell: Meteor Swarm
===================

Description:
  Meteor Swarm is an offensive spell that deals magical damage to your target.
  Base damage: 8d6+10 (+4 per level)

Mana Cost: 80
Target: Offensive

Usage:
  cast meteor_swarm <target>
  Example: cast meteor_swarm goblin
'''
    },
    'mirror_image': {
        'keywords': ['mirror_image', 'mirror image'],
        'text': '''
Spell: Mirror Image
===================

Description:
  Mirror Image grants magical effects that enhance you or an ally.
  Effects:
    - Grants mirror image
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 40
Target: Self

Usage:
  cast mirror_image
'''
    },
    'poison': {
        'keywords': ['poison', 'poison'],
        'text': '''
Spell: Poison
=============

Description:
  Poison grants magical effects that weaken or hinder your target.
  Effects:
    - Grants poison
    - Decreases Strength by 2
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 25
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast poison <target>
  Example: cast poison goblin
'''
    },
    'protection_from_evil': {
        'keywords': ['protection_from_evil', 'protection from evil'],
        'text': '''
Spell: Protection from Evil
===========================

Description:
  Protection from Evil grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 10
    - Grants prot evil
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 30
Target: Defensive

Usage:
  cast protection_from_evil [target]    - Target yourself or an ally
  Example: cast protection_from_evil         - Cast on yourself
  Example: cast protection_from_evil friend  - Cast on an ally
'''
    },
    'protection_from_good': {
        'keywords': ['protection_from_good', 'protection from good'],
        'text': '''
Spell: Protection from Good
===========================

Description:
  Protection from Good grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 10
    - Grants prot good
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 30
Target: Defensive

Usage:
  cast protection_from_good [target]    - Target yourself or an ally
  Example: cast protection_from_good         - Cast on yourself
  Example: cast protection_from_good friend  - Cast on an ally
'''
    },
    'remove_curse': {
        'keywords': ['remove_curse', 'remove curse'],
        'text': '''
Spell: Remove Curse
===================

Description:
  Remove Curse provides special magical effects.

Mana Cost: 35
Target: Defensive

Usage:
  cast remove_curse [target]    - Target yourself or an ally
  Example: cast remove_curse         - Cast on yourself
  Example: cast remove_curse friend  - Cast on an ally
'''
    },
    'remove_poison': {
        'keywords': ['remove_poison', 'remove poison'],
        'text': '''
Spell: Remove Poison
====================

Description:
  Remove Poison provides special magical effects.

Mana Cost: 30
Target: Defensive

Usage:
  cast remove_poison [target]    - Target yourself or an ally
  Example: cast remove_poison         - Cast on yourself
  Example: cast remove_poison friend  - Cast on an ally
'''
    },
    'resurrect': {
        'keywords': ['resurrect', 'resurrect'],
        'text': '''
Spell: Resurrect
================

Description:
  Resurrect provides special magical effects.

Mana Cost: 150
Target: Special

Usage:
  cast resurrect
'''
    },
    'righteous_fury': {
        'keywords': ['righteous_fury', 'righteous fury'],
        'text': '''
Spell: Righteous Fury
=====================

Description:
  Righteous Fury grants magical effects that enhance you or an ally.
  Effects:
    - Grants damage reduction
    - Increases damage by 3
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 55
Target: Self

Usage:
  cast righteous_fury
'''
    },
    'sanctuary': {
        'keywords': ['sanctuary', 'sanctuary'],
        'text': '''
Spell: Sanctuary
================

Description:
  Sanctuary grants magical effects that enhance you or an ally.
  Effects:
    - Grants sanctuary
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 75
Target: Defensive

Usage:
  cast sanctuary [target]    - Target yourself or an ally
  Example: cast sanctuary         - Cast on yourself
  Example: cast sanctuary friend  - Cast on an ally
'''
    },
    'shield': {
        'keywords': ['shield', 'shield'],
        'text': '''
Spell: Shield
=============

Description:
  Shield grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 30
  Duration: 24 game ticks (~12 minutes)

Mana Cost: 25
Target: Defensive

Usage:
  cast shield [target]    - Target yourself or an ally
  Example: cast shield         - Cast on yourself
  Example: cast shield friend  - Cast on an ally
'''
    },
    'shield_of_faith': {
        'keywords': ['shield_of_faith', 'shield of faith'],
        'text': '''
Spell: Shield of Faith
======================

Description:
  Shield of Faith grants magical effects that enhance you or an ally.
  Effects:
    - Improves armor class by 25
    - Grants saving throw
  Duration: 18 game ticks (~9 minutes)

Mana Cost: 35
Target: Defensive

Usage:
  cast shield_of_faith [target]    - Target yourself or an ally
  Example: cast shield_of_faith         - Cast on yourself
  Example: cast shield_of_faith friend  - Cast on an ally
'''
    },
    'sleep': {
        'keywords': ['sleep', 'sleep'],
        'text': '''
Spell: Sleep
============

Description:
  Sleep grants magical effects that weaken or hinder your target.
  Effects:
    - Grants sleep
  Duration: 6 game ticks (~3 minutes)

Mana Cost: 20
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast sleep <target>
  Example: cast sleep goblin
'''
    },
    'slow': {
        'keywords': ['slow', 'slow'],
        'text': '''
Spell: Slow
===========

Description:
  Slow grants magical effects that weaken or hinder your target.
  Effects:
    - Grants slow
    - Decreases attack accuracy by 2
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 35
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast slow <target>
  Example: cast slow goblin
'''
    },
    'spell_reflection': {
        'keywords': ['spell_reflection', 'spell reflection'],
        'text': '''
Spell: Spell Reflection
=======================

Description:
  Spell Reflection grants magical effects that enhance you or an ally.
  Effects:
    - Grants spell reflect
  Duration: 8 game ticks (~4 minutes)

Mana Cost: 70
Target: Self

Usage:
  cast spell_reflection
'''
    },
    'stoneskin': {
        'keywords': ['stoneskin', 'stoneskin'],
        'text': '''
Spell: Stoneskin
================

Description:
  Stoneskin grants magical effects that enhance you or an ally.
  Effects:
    - Grants stoneskin
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 60
Target: Defensive

Usage:
  cast stoneskin [target]    - Target yourself or an ally
  Example: cast stoneskin         - Cast on yourself
  Example: cast stoneskin friend  - Cast on an ally
'''
    },
    'summon': {
        'keywords': ['summon', 'summon'],
        'text': '''
Spell: Summon
=============

Description:
  Summon provides special magical effects.
  Summons a target to your location.

Mana Cost: 75
Target: Special

Usage:
  cast summon
'''
    },
    'vampiric_touch': {
        'keywords': ['vampiric_touch', 'vampiric touch'],
        'text': '''
Spell: Vampiric Touch
=====================

Description:
  Vampiric Touch is an offensive spell that deals magical damage to your target.
  Base damage: 2d6+2 (+1 per level)

Mana Cost: 30
Target: Offensive

Usage:
  cast vampiric_touch <target>
  Example: cast vampiric_touch goblin
'''
    },
    'weaken': {
        'keywords': ['weaken', 'weaken'],
        'text': '''
Spell: Weaken
=============

Description:
  Weaken grants magical effects that weaken or hinder your target.
  Effects:
    - Decreases Strength by 4
  Duration: 12 game ticks (~6 minutes)

Mana Cost: 20
Target: Offensive
Saving Throw: Yes (target may resist)

Usage:
  cast weaken <target>
  Example: cast weaken goblin
'''
    },
    'word_of_recall': {
        'keywords': ['word_of_recall', 'word of recall'],
        'text': '''
Spell: Word of Recall
=====================

Description:
  Word of Recall provides special magical effects.
  Instantly transports you to a safe recall point.

Mana Cost: 15
Target: Self

Usage:
  cast word_of_recall
'''
    },
    'alchemy': {
        'keywords': ['alchemy', 'alchemy'],
        'text': '''
Skill: Alchemy
==============

Class: Crafting

Description:
  Brew potions, elixirs, and poisons from gathered herbs and ingredients. Master alchemists can create powerful consumables and rare transmutations. Experimentation unlocks new recipes.

Requirements:
  Alchemy station. Herbs and reagents needed.

Usage:
  brew <potion>
  mix <ingredients>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'assassinate': {
        'keywords': ['assassinate', 'assassinate'],
        'text': '''
Skill: Assassinate
==================

Class: Assassin

Description:
  The ultimate assassination ability. When mastered, assassinate has a chance to instantly kill a target below a certain health threshold. Even if it fails to kill, it deals devastating damage. Can only be used from stealth.

Requirements:
  Must not be in combat. High skill level recommended.

Usage:
  assassinate <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'backstab': {
        'keywords': ['backstab', 'backstab'],
        'text': '''
Skill: Backstab
===============

Class: Thief/Assassin

Description:
  The signature ability of thieves and assassins. Backstab must be performed from hiding or on an unaware target before combat begins. A successful backstab deals massive damage multiplied by your skill level. Can only be performed with piercing weapons.

Requirements:
  Must not be in combat. Piercing weapon required.

Usage:
  backstab <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'bash': {
        'keywords': ['bash', 'bash'],
        'text': '''
Skill: Bash
===========

Class: Warrior

Description:
  Bash is a warrior skill that allows you to slam your shield or weapon into an enemy, potentially stunning them briefly. A successful bash will interrupt spellcasting and give you a combat advantage. Higher skill levels increase success rate and stun duration.

Usage:
  bash
  bash <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'blacksmithing': {
        'keywords': ['blacksmithing', 'blacksmithing'],
        'text': '''
Skill: Blacksmithing
====================

Class: Crafting

Description:
  Forge weapons and armor from metal ore. Skilled blacksmiths can create powerful equipment and repair damaged gear. Higher levels unlock rare recipes and improve crafting quality.

Requirements:
  Forge and hammer required. Materials needed.

Usage:
  forge <recipe>
  repair <item>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'detect_traps': {
        'keywords': ['detect_traps', 'detect traps'],
        'text': '''
Skill: Detect Traps
===================

Class: Thief/Ranger

Description:
  Your heightened senses allow you to notice hidden traps, secret doors, and other dangers. Passive skill that automatically checks for traps as you explore. Higher skill levels detect more subtle dangers.

Usage:
  Passive skill - Always active

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'envenom': {
        'keywords': ['envenom', 'envenom'],
        'text': '''
Skill: Envenom
==============

Class: Assassin/Thief

Description:
  Coat your weapon with deadly poison. Each successful hit has a chance to poison your target, dealing damage over time and weakening them. The poison type and potency depend on your skill level and available materials.

Usage:
  envenom

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'garrote': {
        'keywords': ['garrote', 'garrote'],
        'text': '''
Skill: Garrote
==============

Class: Assassin

Description:
  An advanced assassination technique. Garrote is a silent killing method that deals extreme damage over several rounds while silencing the victim. Like backstab, it can only be initiated from stealth.

Requirements:
  Must not be in combat. Must be hidden or sneaking.

Usage:
  garrote <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'herbalism': {
        'keywords': ['herbalism', 'herbalism'],
        'text': '''
Skill: Herbalism
================

Class: Crafting

Description:
  Gather herbs, flowers, and plants for alchemy and other crafts. Skilled herbalists can identify rare plants and gather more materials per node. Essential for potion-making.

Usage:
  gather
  gather herbs

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'hide': {
        'keywords': ['hide', 'hide'],
        'text': '''
Skill: Hide
===========

Class: Thief/Assassin/Ranger

Description:
  Conceal yourself in shadows and remain undetected. When hidden, you are invisible to others until you reveal yourself or take action. Perfect for ambushes and avoiding combat. Skill level determines success rate.

Usage:
  hide - Attempt to hide
  visible - Reveal yourself

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'kick': {
        'keywords': ['kick', 'kick'],
        'text': '''
Skill: Kick
===========

Class: Warrior/Monk

Description:
  A basic combat maneuver available to warriors and monks. Kick deals additional damage during combat and can be used as a secondary attack. The damage increases with your level and skill proficiency.

Usage:
  kick
  kick <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'leatherworking': {
        'keywords': ['leatherworking', 'leatherworking'],
        'text': '''
Skill: Leatherworking
=====================

Class: Crafting

Description:
  Craft leather armor, bags, and other useful items from hides. Leatherworkers create medium armor with balanced protection and flexibility. Advanced recipes require rare materials.

Requirements:
  Leatherworking tools. Processed hides needed.

Usage:
  craft <item>
  tan <hide>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'mark_target': {
        'keywords': ['mark_target', 'mark target'],
        'text': '''
Skill: Mark Target
==================

Class: Ranger/Assassin

Description:
  Mark an enemy for death, increasing all damage they take from you and your allies. Marked targets are easier to track and harder for them to escape. Higher skill levels increase the damage bonus and tracking duration.

Usage:
  mark <target>
  unmark

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'mining': {
        'keywords': ['mining', 'mining'],
        'text': '''
Skill: Mining
=============

Class: Crafting

Description:
  Extract valuable ores and gems from mining nodes. Higher skill levels yield better quality materials and increase the chance of finding rare minerals. Requires a mining pick.

Tools: Mining pick required

Usage:
  mine
  mine <node>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'shadow_step': {
        'keywords': ['shadow_step', 'shadow step'],
        'text': '''
Skill: Shadow Step
==================

Class: Assassin

Description:
  Teleport through shadows to appear behind an enemy or escape danger. Shadow step allows you to reposition instantly in combat, potentially triggering backstab opportunities. Requires shadows or darkness to use effectively.

Usage:
  shadowstep <target>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'skinning': {
        'keywords': ['skinning', 'skinning'],
        'text': '''
Skill: Skinning
===============

Class: Crafting

Description:
  Harvest leather, hides, and other materials from slain beasts. Higher skill allows you to skin tougher creatures and extract rare materials. Skinning must be done immediately after combat.

Tools: Skinning knife recommended

Usage:
  skin <corpse>

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
    'sneak': {
        'keywords': ['sneak', 'sneak'],
        'text': '''
Skill: Sneak
============

Class: Thief/Assassin/Ranger

Description:
  Move silently and avoid detection. While sneaking, you are harder to notice when entering or leaving rooms. Higher skill levels make you nearly impossible to detect. Sneaking is essential for setting up backstabs and other stealth attacks.

Usage:
  sneak - Toggle sneak mode on/off

Skill Improvement:
  Your skill level increases through practice. The more you use this
  skill, the better you become at it. Higher levels improve success
  rate and effectiveness.
'''
    },
}
