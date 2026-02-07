#!/usr/bin/env python3
"""Complete audit of spells, skills, and their help coverage."""

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from spells import SPELLS
from help_data import HELP_TOPICS

# Combat skills found in code
COMBAT_SKILLS = [
    'sneak',
    'hide',
    'backstab',
    'bash',
    'kick',
    'garrote',
    'assassinate',
    'envenom',
    'mark_target',
    'shadow_step',
    'detect_traps',
]

# Crafting/gathering skills
CRAFT_SKILLS = [
    'mining',
    'herbalism',
    'skinning',
    'blacksmithing',
    'alchemy',
    'leatherworking',
]

def audit():
    """Complete audit."""
    
    all_skills = sorted(COMBAT_SKILLS + CRAFT_SKILLS)
    spell_names = sorted(SPELLS.keys())
    help_topics = set(HELP_TOPICS.keys())
    
    # Missing help for spells
    spells_no_help = [s for s in spell_names if s not in help_topics]
    
    # Missing help for skills
    skills_no_help = [s for s in all_skills if s not in help_topics]
    
    print("=" * 80)
    print("COMPLETE SPELL & SKILL HELP AUDIT")
    print("=" * 80)
    print(f"\n📊 TOTALS:")
    print(f"   Spells: {len(spell_names)}")
    print(f"   Skills: {len(all_skills)} ({len(COMBAT_SKILLS)} combat + {len(CRAFT_SKILLS)} crafting)")
    print(f"   Help topics: {len(help_topics)}")
    print()
    print(f"❌ MISSING HELP:")
    print(f"   Spells: {len(spells_no_help)}/{len(spell_names)} ({100*len(spells_no_help)//len(spell_names)}%)")
    print(f"   Skills: {len(skills_no_help)}/{len(all_skills)} ({100*len(skills_no_help)//len(all_skills) if all_skills else 0}%)")
    
    # Group spells by type
    offensive = []
    defensive = []
    utility = []
    
    for spell in spells_no_help:
        data = SPELLS[spell]
        target = data.get('target', 'unknown')
        if target == 'offensive':
            offensive.append(spell)
        elif target in ('defensive', 'self'):
            defensive.append(spell)
        else:
            utility.append(spell)
    
    print("\n" + "=" * 80)
    print("SPELLS MISSING HELP (grouped by type)")
    print("=" * 80)
    
    if offensive:
        print(f"\n🔥 OFFENSIVE ({len(offensive)}):")
        for s in offensive:
            data = SPELLS[s]
            dmg = data.get('damage_dice', '-')
            mana = data.get('mana_cost', '?')
            print(f"   {s:20} - {data['name']:30} (Mana: {mana}, Damage: {dmg})")
    
    if defensive:
        print(f"\n🛡️  DEFENSIVE/BUFF ({len(defensive)}):")
        for s in defensive:
            data = SPELLS[s]
            mana = data.get('mana_cost', '?')
            duration = data.get('duration_ticks', '-')
            print(f"   {s:20} - {data['name']:30} (Mana: {mana}, Duration: {duration})")
    
    if utility:
        print(f"\n🔧 UTILITY/OTHER ({len(utility)}):")
        for s in utility:
            data = SPELLS[s]
            mana = data.get('mana_cost', '?')
            print(f"   {s:20} - {data['name']:30} (Mana: {mana})")
    
    print("\n" + "=" * 80)
    print("SKILLS MISSING HELP")
    print("=" * 80)
    
    combat_missing = [s for s in COMBAT_SKILLS if s in skills_no_help]
    craft_missing = [s for s in CRAFT_SKILLS if s in skills_no_help]
    
    if combat_missing:
        print(f"\n⚔️  COMBAT ({len(combat_missing)}):")
        for s in combat_missing:
            print(f"   {s}")
    
    if craft_missing:
        print(f"\n🔨 CRAFTING ({len(craft_missing)}):")
        for s in craft_missing:
            print(f"   {s}")
    
    print("\n" + "=" * 80)
    print("HELP FILES NEEDED")
    print("=" * 80)
    print(f"\nTotal help files to create: {len(spells_no_help) + len(skills_no_help)}")
    print()
    
    return {
        'spells_missing': spells_no_help,
        'skills_missing': skills_no_help,
        'offensive': offensive,
        'defensive': defensive,
        'utility': utility,
    }

if __name__ == '__main__':
    results = audit()
