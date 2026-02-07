#!/usr/bin/env python3
"""Audit all spells and skills for help file coverage."""

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from spells import SPELLS
from help_data import HELP_TOPICS

def audit():
    """Audit spells and skills for help coverage."""
    
    # Get all spell names
    spell_names = set(SPELLS.keys())
    
    # Get all help topics
    help_topics = set(HELP_TOPICS.keys())
    
    # Check for spells without help
    spells_no_help = []
    for spell in sorted(spell_names):
        if spell not in help_topics:
            spell_data = SPELLS[spell]
            spells_no_help.append((spell, spell_data.get('name', spell)))
    
    # Print results
    print("=" * 80)
    print("SPELL & SKILL HELP FILE AUDIT")
    print("=" * 80)
    print(f"\nTotal spells: {len(spell_names)}")
    print(f"Total help topics: {len(help_topics)}")
    print(f"Spells without help: {len(spells_no_help)}")
    
    if spells_no_help:
        print("\n" + "=" * 80)
        print("SPELLS MISSING HELP FILES")
        print("=" * 80)
        for spell_key, spell_name in spells_no_help:
            spell_data = SPELLS[spell_key]
            mana = spell_data.get('mana_cost', '?')
            target = spell_data.get('target', '?')
            print(f"\n  {spell_key}")
            print(f"    Name: {spell_name}")
            print(f"    Mana: {mana}  Target: {target}")
            if 'damage_dice' in spell_data:
                print(f"    Damage: {spell_data['damage_dice']}")
            if 'heal_dice' in spell_data:
                print(f"    Heal: {spell_data['heal_dice']}")
            if 'affects' in spell_data:
                print(f"    Effects: {spell_data['affects']}")
    
    # Check which help topics exist for spells
    spell_helps = []
    for topic in sorted(help_topics):
        if topic in spell_names:
            spell_helps.append(topic)
    
    print(f"\n" + "=" * 80)
    print(f"SPELLS WITH HELP FILES: {len(spell_helps)}")
    print("=" * 80)
    for spell in spell_helps:
        print(f"  ✓ {spell}: {SPELLS[spell].get('name', spell)}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    audit()
