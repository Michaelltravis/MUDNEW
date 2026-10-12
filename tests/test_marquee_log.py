"""Offline test of the marquee quest log (src/marquee_log.py): what real quests take.
    python3 tests/test_marquee_log.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import marquee_log as ml  # noqa: E402

failures = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        failures.append(what)


class P:
    def __init__(self, name):
        self.name = name


def main():
    path = os.path.join(tempfile.mkdtemp(), 'runs.jsonl')
    t0 = int(time.time())
    a = {'id': 'mq_mage', 'cls': 'mage', 'n': 1, 'classes': ['mage'], 'level': 45, 'stage': 0, 'accepted': t0 - 3600}
    b = {'id': 'mq_mage', 'cls': 'mage', 'n': 1, 'classes': ['mage'], 'level': 50, 'stage': 0, 'accepted': t0 - 1800}
    c = {'id': 'mq_warrior', 'cls': 'warrior', 'n': 3, 'classes': ['warrior', 'cleric', 'mage'], 'level': 45, 'stage': 0, 'accepted': t0 - 600}
    ml.record('accept', P('Ann'), a, path=path)
    ml.record('accept', P('Bo'), b, path=path)
    ml.record('accept', P('Cy'), c, path=path)
    for i in range(3):
        a['stage'] = i + 1
        ml.record('stage', P('Ann'), a, path=path)
    ml.record('death', P('Ann'), a, path=path)
    ml.record('death', P('Ann'), a, path=path)
    ml.record('finish', P('Ann'), a, path=path)
    ml.record('finish', P('Bo'), b, path=path)
    rs = ml.runs(path)
    check(len(rs) == 3, f'three quests in the log ({len(rs)})')
    ann = next(r for r in rs if r['accept']['owner'] == 'Ann')
    check(len(ann['stages']) == 3 and ann['deaths'] == 2 and ann['end']['kind'] == 'finish', "Ann's stages, deaths and finish")
    check(ann['accept']['mode'] in ('rounds', 'action'), 'the combat mode is written down')
    lines = ml.summary(path)
    check(any(l.startswith('mage') and '2 done' in l and '1.0 deaths' in l for l in lines), f'mages: two finished, a death each on average ({lines})')
    check(all(len(l) + 2 <= 80 for l in lines), 'each line fits a telnet line')
    check(not any(l.startswith('warrior') for l in lines) and '1 quest under way' in lines[-1], 'the warrior party is still out')
    ml.record('accept', P('X'), None, path=path)          # no quest: nothing written
    check(len(ml.runs(path)) == 3, 'a missing quest writes nothing')
    imm = P('Imm')
    imm.is_immortal = True
    ml.record('accept', imm, dict(a, accepted=t0), path=path)
    check(len(ml.runs(path)) == 3, "an immortal's quest (a test) isn't written")
    check(ml.summary(os.path.join(tempfile.mkdtemp(), 'none.jsonl'))[-1].startswith('0 quests'), 'no log yet: an empty summary')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
