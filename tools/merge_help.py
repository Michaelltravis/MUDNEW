#!/usr/bin/env python3
"""Merge generated help entries into help_data.py."""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / 'src'

# Import the generated help
sys.path.insert(0, str(BASE_DIR / 'tools'))
from generated_help import HELP_TOPICS_NEW

def merge_help():
    """Merge new help topics into help_data.py."""
    
    help_file = SRC_DIR / 'help_data.py'
    
    # Read current file
    with open(help_file, 'r') as f:
        lines = f.readlines()
    
    # Find the line with just "}" after HELP_TOPICS entries
    insert_pos = None
    for i, line in enumerate(lines):
        # Look for the closing brace of HELP_TOPICS (line 952)
        if line.strip() == '}' and i > 900 and i < 960:
            # Check if previous lines look like help topic entries
            if i > 5 and ("'text'" in lines[i-3] or "'keywords'" in lines[i-5]):
                insert_pos = i
                break
    
    if not insert_pos:
        print("❌ Could not find HELP_TOPICS closing brace")
        print("Looking for '}' around line 952...")
        return False
    
    # Generate new entries in the same format as existing help_data.py
    new_entries = []
    for key, value in sorted(HELP_TOPICS_NEW.items()):
        new_entries.append(f"\n    '{key}': {{\n")
        new_entries.append(f"        'keywords': {value['keywords']},\n")
        # Escape any triple quotes in the text
        text = value['text'].replace("'''", "\\'\\'\\'")
        new_entries.append(f"        'text': '''{value['text']}'''\n")
        new_entries.append(f"    }},\n")
    
    # Insert new entries before the closing brace
    lines.insert(insert_pos, ''.join(new_entries))
    
    # Write back
    with open(help_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Merged {len(HELP_TOPICS_NEW)} new help entries into help_data.py")
    return True

if __name__ == '__main__':
    success = merge_help()
    sys.exit(0 if success else 1)
