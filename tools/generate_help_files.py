#!/usr/bin/env python3
"""Generate comprehensive help files for all spells and skills."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from spells import SPELLS

def generate_spell_help(spell_key, spell_data):
    """Generate help text for a spell."""
    name = spell_data.get('name', spell_key.replace('_', ' ').title())
    mana = spell_data.get('mana_cost', '?')
    target_type = spell_data.get('target', 'unknown')
    
    # Determine spell category
    if 'damage_dice' in spell_data:
        category = "Offensive"
    elif 'heal_dice' in spell_data:
        category = "Healing"
    elif 'affects' in spell_data:
        category = "Buff/Debuff"
    else:
        category = "Utility"
    
    help_text = f"    '{spell_key}': {{\n"
    help_text += f"        'keywords': ['{spell_key}', '{name.lower()}'],\n"
    help_text += f"        'text': '''\n"
    help_text += f"Spell: {name}\n"
    help_text += f"{'=' * (7 + len(name))}\n\n"
    
    # Description based on spell effects
    help_text += "Description:\n"
    
    if 'damage_dice' in spell_data:
        dmg = spell_data['damage_dice']
        help_text += f"  {name} is an offensive spell that deals magical damage to your target.\n"
        help_text += f"  Base damage: {dmg}"
        if 'damage_per_level' in spell_data:
            help_text += f" (+{spell_data['damage_per_level']} per level)"
        help_text += "\n"
        
        # Add flavor based on spell name
        if 'fire' in spell_key or 'flame' in spell_key or 'burning' in spell_key:
            help_text += "  Harness the power of fire to burn your enemies.\n"
        elif 'ice' in spell_key or 'chill' in spell_key or 'frost' in spell_key:
            help_text += "  Channel freezing cold to damage your foes.\n"
        elif 'lightning' in spell_key or 'shock' in spell_key:
            help_text += "  Call down the fury of lightning upon your target.\n"
        elif 'death' in spell_key or 'harm' in spell_key or 'necro' in spell_key:
            help_text += "  Wield the forces of death and decay.\n"
        
    elif 'heal_dice' in spell_data:
        heal = spell_data['heal_dice']
        help_text += f"  {name} restores health to you or an ally.\n"
        if heal == '100':
            help_text += "  This powerful spell provides complete healing.\n"
        else:
            help_text += f"  Base healing: {heal}"
            if 'heal_per_level' in spell_data:
                help_text += f" (+{spell_data['heal_per_level']} per level)"
            help_text += "\n"
    
    elif 'affects' in spell_data:
        affects = spell_data['affects']
        help_text += f"  {name} grants magical effects"
        
        if target_type == 'offensive':
            help_text += " that weaken or hinder your target.\n"
        else:
            help_text += " that enhance you or an ally.\n"
        
        help_text += "  Effects:\n"
        for affect in affects:
            aff_type = affect.get('type', 'unknown')
            value = affect.get('value', 0)
            
            # Translate effect types
            if aff_type == 'ac':
                if value < 0:
                    help_text += f"    - Improves armor class by {abs(value)}\n"
                else:
                    help_text += f"    - Reduces armor class by {value}\n"
            elif aff_type in ('hitroll', 'damroll'):
                stat = 'attack accuracy' if aff_type == 'hitroll' else 'damage'
                if value > 0:
                    help_text += f"    - Increases {stat} by {value}\n"
                else:
                    help_text += f"    - Decreases {stat} by {abs(value)}\n"
            elif aff_type in ('str', 'dex', 'con', 'int', 'wis', 'cha'):
                stat_name = {'str': 'Strength', 'dex': 'Dexterity', 'con': 'Constitution',
                           'int': 'Intelligence', 'wis': 'Wisdom', 'cha': 'Charisma'}[aff_type]
                if value > 0:
                    help_text += f"    - Increases {stat_name} by {value}\n"
                else:
                    help_text += f"    - Decreases {stat_name} by {abs(value)}\n"
            else:
                help_text += f"    - Grants {aff_type.replace('_', ' ')}\n"
        
        if 'duration_ticks' in spell_data:
            duration = spell_data['duration_ticks']
            help_text += f"  Duration: {duration} game ticks (~{duration//2} minutes)\n"
    
    else:
        # Generic utility spell
        help_text += f"  {name} provides special magical effects.\n"
        
        if 'recall' in spell_key:
            help_text += "  Instantly transports you to a safe recall point.\n"
        elif 'teleport' in spell_key:
            help_text += "  Transports you to a random location.\n"
        elif 'summon' in spell_key:
            help_text += "  Summons a target to your location.\n"
        elif 'animate' in spell_key:
            help_text += "  Raises corpses to serve as your undead minions.\n"
        elif 'enchant' in spell_key:
            help_text += "  Permanently enhances a weapon with magical properties.\n"
        elif 'identify' in spell_key:
            help_text += "  Reveals the magical properties of an item.\n"
        elif 'create_food' in spell_key:
            help_text += "  Conjures nourishing food from thin air.\n"
        elif 'create_water' in spell_key:
            help_text += "  Creates fresh drinking water.\n"
        elif 'door' in spell_key:
            help_text += "  Affects doors and barriers with magical force.\n"
        elif 'dispel' in spell_key:
            help_text += "  Removes magical effects from the target.\n"
        elif 'detect' in spell_key:
            help_text += "  Enhances your senses to detect hidden properties.\n"
    
    help_text += "\n"
    help_text += f"Mana Cost: {mana}\n"
    help_text += f"Target: {target_type.title()}\n"
    
    if 'level_required' in spell_data:
        help_text += f"Level Required: {spell_data['level_required']}\n"
    
    if spell_data.get('save'):
        help_text += "Saving Throw: Yes (target may resist)\n"
    
    help_text += "\n"
    help_text += "Usage:\n"
    if target_type == 'offensive':
        help_text += f"  cast {spell_key} <target>\n"
        help_text += f"  Example: cast {spell_key} goblin\n"
    elif target_type in ('defensive', 'group'):
        help_text += f"  cast {spell_key} [target]    - Target yourself or an ally\n"
        help_text += f"  Example: cast {spell_key}         - Cast on yourself\n"
        help_text += f"  Example: cast {spell_key} friend  - Cast on an ally\n"
    elif target_type == 'self':
        help_text += f"  cast {spell_key}\n"
    elif target_type == 'object':
        help_text += f"  cast {spell_key} <item>\n"
        help_text += f"  Example: cast {spell_key} sword\n"
    elif target_type == 'door':
        help_text += f"  cast {spell_key} <direction>\n"
        help_text += f"  Example: cast {spell_key} north\n"
    else:
        help_text += f"  cast {spell_key}\n"
    
    help_text += "'''\n"
    help_text += "    },\n"
    
    return help_text

# Skill definitions with descriptions
SKILL_HELP = {
    'bash': {
        'name': 'Bash',
        'description': 'Bash is a warrior skill that allows you to slam your shield or weapon into an enemy, potentially stunning them briefly. A successful bash will interrupt spellcasting and give you a combat advantage. Higher skill levels increase success rate and stun duration.',
        'usage': ['bash', 'bash <target>'],
        'class': 'Warrior',
    },
    'kick': {
        'name': 'Kick',
        'description': 'A basic combat maneuver available to warriors and monks. Kick deals additional damage during combat and can be used as a secondary attack. The damage increases with your level and skill proficiency.',
        'usage': ['kick', 'kick <target>'],
        'class': 'Warrior/Monk',
    },
    'backstab': {
        'name': 'Backstab',
        'description': 'The signature ability of thieves and assassins. Backstab must be performed from hiding or on an unaware target before combat begins. A successful backstab deals massive damage multiplied by your skill level. Can only be performed with piercing weapons.',
        'usage': ['backstab <target>'],
        'class': 'Thief/Assassin',
        'requirements': 'Must not be in combat. Piercing weapon required.',
    },
    'garrote': {
        'name': 'Garrote',
        'description': 'An advanced assassination technique. Garrote is a silent killing method that deals extreme damage over several rounds while silencing the victim. Like backstab, it can only be initiated from stealth.',
        'usage': ['garrote <target>'],
        'class': 'Assassin',
        'requirements': 'Must not be in combat. Must be hidden or sneaking.',
    },
    'assassinate': {
        'name': 'Assassinate',
        'description': 'The ultimate assassination ability. When mastered, assassinate has a chance to instantly kill a target below a certain health threshold. Even if it fails to kill, it deals devastating damage. Can only be used from stealth.',
        'usage': ['assassinate <target>'],
        'class': 'Assassin',
        'requirements': 'Must not be in combat. High skill level recommended.',
    },
    'envenom': {
        'name': 'Envenom',
        'description': 'Coat your weapon with deadly poison. Each successful hit has a chance to poison your target, dealing damage over time and weakening them. The poison type and potency depend on your skill level and available materials.',
        'usage': ['envenom'],
        'class': 'Assassin/Thief',
    },
    'mark_target': {
        'name': 'Mark Target',
        'description': 'Mark an enemy for death, increasing all damage they take from you and your allies. Marked targets are easier to track and harder for them to escape. Higher skill levels increase the damage bonus and tracking duration.',
        'usage': ['mark <target>', 'unmark'],
        'class': 'Ranger/Assassin',
    },
    'shadow_step': {
        'name': 'Shadow Step',
        'description': 'Teleport through shadows to appear behind an enemy or escape danger. Shadow step allows you to reposition instantly in combat, potentially triggering backstab opportunities. Requires shadows or darkness to use effectively.',
        'usage': ['shadowstep <target>'],
        'class': 'Assassin',
    },
    'sneak': {
        'name': 'Sneak',
        'description': 'Move silently and avoid detection. While sneaking, you are harder to notice when entering or leaving rooms. Higher skill levels make you nearly impossible to detect. Sneaking is essential for setting up backstabs and other stealth attacks.',
        'usage': ['sneak - Toggle sneak mode on/off'],
        'class': 'Thief/Assassin/Ranger',
    },
    'hide': {
        'name': 'Hide',
        'description': 'Conceal yourself in shadows and remain undetected. When hidden, you are invisible to others until you reveal yourself or take action. Perfect for ambushes and avoiding combat. Skill level determines success rate.',
        'usage': ['hide - Attempt to hide', 'visible - Reveal yourself'],
        'class': 'Thief/Assassin/Ranger',
    },
    'detect_traps': {
        'name': 'Detect Traps',
        'description': 'Your heightened senses allow you to notice hidden traps, secret doors, and other dangers. Passive skill that automatically checks for traps as you explore. Higher skill levels detect more subtle dangers.',
        'usage': ['Passive skill - Always active'],
        'class': 'Thief/Ranger',
    },
    'mining': {
        'name': 'Mining',
        'description': 'Extract valuable ores and gems from mining nodes. Higher skill levels yield better quality materials and increase the chance of finding rare minerals. Requires a mining pick.',
        'usage': ['mine', 'mine <node>'],
        'class': 'Crafting',
        'tools': 'Mining pick required',
    },
    'herbalism': {
        'name': 'Herbalism',
        'description': 'Gather herbs, flowers, and plants for alchemy and other crafts. Skilled herbalists can identify rare plants and gather more materials per node. Essential for potion-making.',
        'usage': ['gather', 'gather herbs'],
        'class': 'Crafting',
    },
    'skinning': {
        'name': 'Skinning',
        'description': 'Harvest leather, hides, and other materials from slain beasts. Higher skill allows you to skin tougher creatures and extract rare materials. Skinning must be done immediately after combat.',
        'usage': ['skin <corpse>'],
        'class': 'Crafting',
        'tools': 'Skinning knife recommended',
    },
    'blacksmithing': {
        'name': 'Blacksmithing',
        'description': 'Forge weapons and armor from metal ore. Skilled blacksmiths can create powerful equipment and repair damaged gear. Higher levels unlock rare recipes and improve crafting quality.',
        'usage': ['forge <recipe>', 'repair <item>'],
        'class': 'Crafting',
        'requirements': 'Forge and hammer required. Materials needed.',
    },
    'alchemy': {
        'name': 'Alchemy',
        'description': 'Brew potions, elixirs, and poisons from gathered herbs and ingredients. Master alchemists can create powerful consumables and rare transmutations. Experimentation unlocks new recipes.',
        'usage': ['brew <potion>', 'mix <ingredients>'],
        'class': 'Crafting',
        'requirements': 'Alchemy station. Herbs and reagents needed.',
    },
    'leatherworking': {
        'name': 'Leatherworking',
        'description': 'Craft leather armor, bags, and other useful items from hides. Leatherworkers create medium armor with balanced protection and flexibility. Advanced recipes require rare materials.',
        'usage': ['craft <item>', 'tan <hide>'],
        'class': 'Crafting',
        'requirements': 'Leatherworking tools. Processed hides needed.',
    },
}

def generate_skill_help(skill_key):
    """Generate help text for a skill."""
    skill = SKILL_HELP[skill_key]
    name = skill['name']
    
    help_text = f"    '{skill_key}': {{\n"
    help_text += f"        'keywords': ['{skill_key}', '{name.lower()}'],\n"
    help_text += f"        'text': '''\n"
    help_text += f"Skill: {name}\n"
    help_text += f"{'=' * (7 + len(name))}\n\n"
    
    help_text += f"Class: {skill['class']}\n\n"
    
    help_text += "Description:\n"
    help_text += f"  {skill['description']}\n\n"
    
    if 'requirements' in skill:
        help_text += "Requirements:\n"
        help_text += f"  {skill['requirements']}\n\n"
    
    if 'tools' in skill:
        help_text += f"Tools: {skill['tools']}\n\n"
    
    help_text += "Usage:\n"
    for usage in skill['usage']:
        help_text += f"  {usage}\n"
    
    help_text += "\n"
    help_text += "Skill Improvement:\n"
    help_text += "  Your skill level increases through practice. The more you use this\n"
    help_text += "  skill, the better you become at it. Higher levels improve success\n"
    help_text += "  rate and effectiveness.\n"
    
    help_text += "'''\n"
    help_text += "    },\n"
    
    return help_text

def main():
    """Generate all help files."""
    output = []
    
    print("Generating help files for spells...")
    spell_count = 0
    for spell_key in sorted(SPELLS.keys()):
        if spell_key in ['animate_dead', 'armor', 'bless', 'cure_light', 'cure_serious',
                        'curse', 'fireball', 'haste', 'heal', 'invisibility',
                        'lightning_bolt', 'magic_missile', 'teleport']:
            continue  # Skip spells that already have help
        
        output.append(generate_spell_help(spell_key, SPELLS[spell_key]))
        spell_count += 1
    
    print(f"Generated {spell_count} spell help files")
    
    print("Generating help files for skills...")
    skill_count = 0
    for skill_key in sorted(SKILL_HELP.keys()):
        output.append(generate_skill_help(skill_key))
        skill_count += 1
    
    print(f"Generated {skill_count} skill help files")
    
    # Write to file
    output_path = BASE_DIR / 'tools' / 'generated_help.py'
    with open(output_path, 'w') as f:
        f.write("# Generated help entries\n")
        f.write("# Add these to help_data.py HELP_TOPICS dictionary\n\n")
        f.write("HELP_TOPICS_NEW = {\n")
        f.write(''.join(output))
        f.write("}\n")
    
    print(f"\n✅ Generated {spell_count + skill_count} help files")
    print(f"📄 Saved to: {output_path}")
    print(f"\nNext step: Merge these into src/help_data.py")

if __name__ == '__main__':
    main()
