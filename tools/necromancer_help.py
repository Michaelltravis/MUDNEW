#!/usr/bin/env python3
"""Generate help files for new necromancer spells and skills."""

NECROMANCER_HELP = {
    'dark_mending': {
        'keywords': ['dark_mending', 'dark mending'],
        'text': '''
Spell: Dark Mending
===================

Description:
  Dark Mending is a necromancer-specific healing spell that repairs your
  undead servants. Unlike divine healing which harms undead, dark mending
  uses necrotic energy to knit bone and shadow back together.
  
  Base healing: 3d8 (+1 per level)
  
  This spell ONLY works on undead pets. It cannot heal living creatures.

Mana Cost: 35
Target: Undead pet
Class: Necromancer

Usage:
  cast dark_mending <pet_name>
  Example: cast dark_mending knight
  Example: cast dark_mending wraith

Tactical Use:
  Essential for keeping expensive or powerful pets alive through tough
  fights. Much more mana-efficient than re-summoning a new pet.
'''
    },
    
    'unholy_might': {
        'keywords': ['unholy_might', 'unholy might'],
        'text': '''
Spell: Unholy Might
===================

Description:
  Infuse your undead servant with overwhelming dark power, dramatically
  boosting its combat effectiveness for 10 minutes.
  
  Effects:
    - +5 to hit (better accuracy)
    - +8 damage per attack
    - +25% attack speed (haste effect)
    - +1d6 necrotic damage per hit
  
  Duration: 20 game ticks (~10 minutes)

Mana Cost: 50
Target: Undead pet
Class: Necromancer

Usage:
  cast unholy_might <pet_name>
  Example: cast unholy_might knight
  Example: cast unholy_might stalker

Tactical Use:
  Turn any pet into a DPS machine. Stack with Death Pact for massive
  damage output. Best used on warrior or rogue pets. Powerful pre-buff
  before boss fights.
'''
    },
    
    'death_pact': {
        'keywords': ['death_pact', 'death pact'],
        'text': '''
Spell: Death Pact
=================

Description:
  Create a dark bond between you and your undead servant. While active,
  damage is split between you and the bonded pet, but the pet gains
  offensive bonuses.
  
  Effects:
    - Damage to you is split 50/50 with bonded pet
    - Pet gains +3 damage
    - If pet dies while bonded, you take 20% of your max HP as backlash
  
  Duration: 10 game ticks (~5 minutes)

Mana Cost: 40
Target: Undead pet
Class: Necromancer
Warning: Dangerous if pet dies!

Usage:
  cast death_pact <pet_name>
  Example: cast death_pact knight

Tactical Use:
  High risk, high reward. Turn your tankiest pet (bone knight) into a
  damage sponge while boosting its offense. Watch the pet's HP carefully -
  if it dies, you suffer heavy backlash damage. Best combined with Dark
  Mending to keep bonded pet alive.
'''
    },
    
    'siphon_unlife': {
        'keywords': ['siphon_unlife', 'siphon unlife', 'siphon'],
        'text': '''
Spell: Siphon Unlife
====================

Description:
  Create a temporary conduit between yourself and your undead servant,
  allowing life force to flow in either direction.
  
  Modes:
    FROM: Drain HP from pet to heal yourself
          Transfers 50% of pet's current HP to you
    
    TO:   Transfer your HP to heal pet
          Transfers up to 40% of your current HP to pet

Mana Cost: 45
Target: Undead pet
Class: Necromancer

Usage:
  cast siphon_unlife from <pet_name>  - Drain pet to heal yourself
  cast siphon_unlife to <pet_name>    - Transfer your HP to pet
  
  Examples:
    cast siphon from knight    - Emergency self-heal
    cast siphon to wraith      - Save a dying pet

Tactical Use:
  Emergency healing that works both ways. Sacrifice pet HP when you're
  dying, or share your HP to save a valuable pet. The bidirectional
  nature makes it very versatile but requires good judgment.
'''
    },
    
    'corpse_explosion': {
        'keywords': ['corpse_explosion', 'corpse explosion'],
        'text': '''
Spell: Corpse Explosion
=======================

Description:
  Detonate a corpse or sacrifice a dying undead servant in a devastating
  explosion of necrotic energy that hits ALL enemies in the room.
  
  Base damage: 5d8
  Bonus: +(pet's remaining HP / 2) if sacrificing a pet
  
  This is an AREA OF EFFECT spell - hits every enemy in the room!

Mana Cost: 60
Target: Corpse in room, or specific pet to sacrifice
Class: Necromancer

Usage:
  cast corpse_explosion              - Explode corpse in room
  cast corpse_explosion <pet_name>   - Sacrifice pet for bigger blast
  
  Examples:
    cast corpse_explosion         - Use enemy corpse
    cast corpse_explosion knight  - Sacrifice dying knight

Tactical Use:
  Massive AoE damage for finishing fights. If your tank is about to die
  anyway, blow it up for one last devastating attack. The more HP the
  pet has remaining, the bigger the explosion. Can also use enemy corpses
  for free AoE damage during cleanup.

Warning: This destroys the targeted corpse or pet permanently!
'''
    },
    
    'mass_animate': {
        'keywords': ['mass_animate', 'mass animate'],
        'text': '''
Spell: Mass Animate
===================

Description:
  Raise multiple corpses at once, creating a small army of basic undead
  zombies. These zombies are weaker than normal animated dead (50% stats
  of regular pets) but make up for it with numbers.
  
  Raises: Up to 3 corpses at once
  Stats: 50% of normal animated dead stats
  Duration: 1 hour
  
  The zombies are basic warriors - no special abilities, but they swarm.

Mana Cost: 100
Target: Room (all corpses)
Class: Necromancer
Level Required: 20

Usage:
  cast mass_animate
  
  Note: You must have at least 3 corpses in the room. The spell will
        raise up to 3 corpses as weak zombie servants.

Tactical Use:
  Swarm tactics. Great for overwhelming single strong enemies with numbers
  or handling multiple weaker foes. The mass of bodies can absorb damage
  while you and your main pets deal damage safely. Best used after a big
  fight where multiple corpses are available.

Warning: Counts toward your total pet limit! Clear out weak pets first.
'''
    },
    
    'dark_ritual': {
        'keywords': ['dark_ritual', 'dark ritual', 'ritual'],
        'text': '''
Skill: Dark Ritual
==================

Class: Necromancer
Type: Active channeled skill
Cooldown: 5 minutes

Description:
  Perform a blood ritual to empower ALL your undead servants at once.
  While channeling this ritual, you cannot cast other spells or move.
  
  Cost: 30 mana + 15% of your max HP
  Duration: 2 minutes (extends with skill level)
  
  While active:
    - All undead pets gain +3 to all stats
    - All pets regenerate 5% HP per round
    - You cannot cast spells (channeling)
    - If interrupted, you are stunned for 1 round

Usage:
  ritual
  dark ritual
  
  To cancel early: cast any spell or move

Skill Improvement:
  Level 1-25:  1 minute duration
  Level 26-50: 1.5 minute duration
  Level 51-75: 2 minute duration
  Level 76+:   2.5 minute duration, reduced to 10% HP cost

Tactical Use:
  Powerful pre-buff before boss fights or difficult encounters. The
  channeling requirement makes you vulnerable, so use it when you have
  a moment of safety. The HP cost is significant - make sure you can
  afford it. Best used with multiple pets to get maximum value.

Warning: High risk! Being interrupted wastes the resources and stuns you.
'''
    },
    
    'soul_harvest': {
        'keywords': ['soul_harvest', 'soul harvest'],
        'text': '''
Skill: Soul Harvest
===================

Class: Necromancer
Type: Passive skill

Description:
  Your mastery of death magic allows you to harvest soul fragments from
  slain enemies automatically. These fragments empower your necromancy.
  
  Trigger: 25-40% chance when any enemy dies near you
  Max Stacks: 5 soul fragments
  Duration: 10 minutes per fragment
  
  Each soul fragment provides:
    - 10% reduced mana cost on your next spell
    - 20% increased duration on your next undead pet summon
  
  Fragments are consumed when you cast spells or summon pets.

Usage:
  Passive - always active
  
  Check your fragments: score
  
Skill Improvement:
  Level 1-25:  25% chance, max 3 fragments
  Level 26-50: 30% chance, max 4 fragments
  Level 51-75: 35% chance, max 5 fragments
  Level 76+:   40% chance, max 5 fragments, 15 minute duration

Tactical Use:
  Resource management for extended dungeon crawls. The more you fight,
  the more souls you harvest, making your spells cheaper and pets longer-
  lasting. Stack up fragments before summoning expensive pets or casting
  costly spells. Great for sustained gameplay and farming sessions.

Tips:
  - Let fragments stack to 5 before using expensive spells
  - Use for pet summoning to get extra duration
  - Fragments make Dark Ritual more affordable (reduces mana cost)
'''
    },
}

if __name__ == '__main__':
    import json
    print("# Necromancer Help Entries")
    print("# Add these to help_data.py HELP_TOPICS dictionary\n")
    print("NECROMANCER_HELP = {")
    for key in sorted(NECROMANCER_HELP.keys()):
        entry = NECROMANCER_HELP[key]
        print(f"    '{key}': {{")
        print(f"        'keywords': {entry['keywords']},")
        print(f"        'text': '''{entry['text']}'''")
        print(f"    }},")
    print("}")
