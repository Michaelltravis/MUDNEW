#!/usr/bin/env python3
"""Progression for EVERY class: forge a fresh level-1 character of each class through
the real creation wizard (tools/gauntlet/capture-onboard.js), then walk the newcomer
ladder with that class's own button 3 as the opener (tools/gauntlet/curve.py).

  python3 tools/gauntlet/curve_all.py [--classes warrior,mage,...] [--run progression-01]

Writes docs/gauntlet/<run>/classes/<class>/{curve.md,curve.json,fights/} and a summary table
docs/gauntlet/<run>/classes/README.md.
"""
import argparse, json, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# button 3 per class = the first entry of the client's CLASS_KIT_ORDER (ui.js), in command form
OPENER = {
    'warrior': 'bash', 'paladin': 'censure', 'ranger': "cast 'truesight shot'", 'thief': 'backstab', 'assassin': 'backstab',
    'mage': "cast 'magic missile'", 'necromancer': "cast 'soul bolt'", 'cleric': "cast 'holy smite'", 'bard': 'mockery',
}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', default='progression-01'); ap.add_argument('--classes', default=','.join(OPENER))
    a = ap.parse_args()
    base = os.path.join(ROOT, 'docs', 'gauntlet', a.run, 'classes'); os.makedirs(base, exist_ok=True)
    rows = []
    for cls in [c for c in a.classes.split(',') if c]:
        print('==', cls, flush=True)
        env = dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules')
        r = subprocess.run(['xvfb-run', '-a', 'node', 'tools/gauntlet/capture-onboard.js', '--run', 'scratch', '--round', 'forge', '--class', cls], cwd=ROOT, env=env, capture_output=True, text=True, timeout=400)
        m = re.search(r'^mh (\w+) ', r.stdout, re.M)
        if not m: print('forge failed', cls, r.stdout[-300:], r.stderr[-300:]); rows.append((cls, 'forge failed', '', '', '')); continue
        name = m.group(1); out = os.path.join(base, cls)
        r2 = subprocess.run([sys.executable, 'tools/gauntlet/curve.py', '--run', a.run, '--name', name, '--password', 'newcomer1', '--open', OPENER[cls], '--out', out], cwd=ROOT, capture_output=True, text=True, timeout=1500)
        try:
            d = json.load(open(os.path.join(out, 'curve.json')))
            l5 = d['time_to_level'].get('5'); 
            rows.append((cls, name, d['level_reached'], d['deaths'], f"{l5}s" if l5 else '—', sum(1 for f in d['fights'] if f['ended'] == 'mob_killed')))
            print(cls, name, 'level', d['level_reached'], 'deaths', d['deaths'], 'L5', l5, flush=True)
        except Exception as e:
            print('curve failed', cls, e, r2.stdout[-300:], r2.stderr[-300:]); rows.append((cls, name, 'failed', '', '', ''))
    md = ['# progression-01 — every class on the newcomer ladder\n', 'Fresh level-1 character of each class, forged through the live wizard, playing attack + its own button 3 + brace on the wind-up prompt. Ladder: training dummy, then the Newbie Zone (the tutorial\'s route). Newcomer XP ramp 250/350/500/650.\n',
          '| class | character | opener | level reached | deaths | time to L5 | wins /12 |', '|---|---|---|---|---|---|---|']
    for row in rows:
        cls = row[0]; md.append(f"| {cls} | {row[1]} | `{OPENER.get(cls, '')}` | {row[2]} | {row[3]} | {row[4]} | {row[5] if len(row) > 5 else ''} |")
    open(os.path.join(base, 'README.md'), 'w').write('\n'.join(md) + '\n'); print('wrote', os.path.relpath(base, ROOT))
if __name__ == '__main__': main()
