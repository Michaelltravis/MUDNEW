#!/usr/bin/env python3
"""Reputation from kills (factions.FactionManager.kill_words): a creature counts as what its own name
says, word by word, never by its room line or by part of a longer word.

    python3 tests/test_faction_kills.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from factions import FactionManager  # noqa: E402

FAILED = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        FAILED.append(what)


class Victim:
    def __init__(self, name, short, long_desc='', flags=()):
        self.name, self.short_desc, self.long_desc, self.flags = name, short, long_desc, list(flags)
        self.keywords = (name + ' ' + short + ' ' + long_desc).lower().split()


def kinds(*a, **k):
    return FactionManager.kill_words(Victim(*a, **k))


check('guard' not in kinds('death knight morkai', 'a death knight of Morkai', 'A death knight stands guard here.', ['undead']),
      'a creature that "stands guard" in its room line is no guard')
check('undead' in kinds('death knight morkai', 'a death knight of Morkai', flags=['undead']), 'an undead creature counts as undead')
check(not kinds('guardian', 'the guardian'), 'a guardian is not a guard')
check(not kinds('torchbearer', 'a trembling torchbearer'), 'a torchbearer is no bear and no orc')
check(not kinds('grocer', 'the grocer') and not kinds('bulwark imperial', 'an imperial bulwark'), 'a grocer or an imperial is no imp')
check('guard' in kinds('guard city', 'a city guard'), 'a city guard is a guard')
check('bandit' in kinds('bandits', 'two bandits'), 'a plural counts')
check('ghost' in kinds('servant ghostly', "a ghostly pharaoh's servant"), 'a ghostly servant counts as a ghost')
check('lich' in kinds('dracolich', 'the dracolich') and 'goblin' in kinds('hobgoblin', 'the hobgoblin'),
      'a name ending in a kind counts (the dracolich, the hobgoblin)')
check({'orc', 'skeleton'} <= kinds('skeleton skeletal orc warrior', 'a skeletal orc warrior'), 'every kind in the name counts')

print('\nALL OK' if not FAILED else f'\n{len(FAILED)} FAILED')
sys.exit(1 if FAILED else 0)
