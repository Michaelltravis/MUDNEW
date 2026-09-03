#!/usr/bin/env python3
"""Gauntlet evidence: scripted fight transcript + pacing stats (telnet, no browser).

  python3 tools/gauntlet/fight.py --run playability-01 --round 1 [--target keeper --vnum 14002] [--max 120]

Writes docs/gauntlet/<run>/round-<n>/fight/<label>.txt (timestamped transcript, ANSI stripped)
and <label>.json (stats the critic can check against the answer key).
"""
import argparse, json, os, re, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from test_suite import MUDClient  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))
ANSI = re.compile(r'\x1b\[[0-9;]*m')
FIGHTS = CFG.get('fights') or [
    {'label': 'fight_keeper', 'vnum': 14002, 'target': 'keeper'},
    {'label': 'fight_bear', 'vnum': 27021, 'target': 'grimclaw'},
]
PATTERNS = {
    'telegraph': re.compile(r'⚠|rears back|winds up|plants its feet|begins to|prepares to|\(brace or sidestep', re.I),
    'reaction_prompt': re.compile(r'brace or sidestep|interrupt', re.I),
    'stagger': re.compile(r'STAGGER|reels|wide open', re.I),
    'perfect': re.compile(r'PERFECT STRIKE', re.I),
    'guard': re.compile(r'snaps into a guard|🛡', re.I),
    'player_hit': re.compile(r'^Your .* \[\d+ damage\]|^You .*\[\d+\]', re.I | re.M),
    'player_miss': re.compile(r'^Your attack (misses|goes wide)|^You miss|dodges your attack', re.I | re.M),
    'mob_hit': re.compile(r"'s .* (hits|slams into|strikes) .*\[\d+", re.I),
    'low_hp_nag': re.compile(r'Your health is low', re.I),
    'death': re.compile(r'\bis dead\b|has been slain|You killed|is DEAD', re.I),
    'player_death': re.compile(r'soul slipping away|You have died|You are dead', re.I),
}
def strip(s): return ANSI.sub('', s or '')

def login(c):
    c.connect(); time.sleep(1); c.receive(2)
    ch = CFG['character']
    for cmd in (ch['name'], ch['password'], f"play {ch['name']}"):
        c.send_and_receive(cmd, 1.0)
    for cmd in CFG.get('setup', []): c.send_and_receive(cmd, 0.4)
    c.send_and_receive(f"advance {ch['name']} {ch['level']}", 0.4)
    for vnum in CFG.get('gear', []):
        c.send_and_receive(f'oload {vnum}', 0.4)
    c.send_and_receive('wear all', 0.6); c.send_and_receive('wield sword', 0.6)

def run_fight(c, f, max_s):
    c.send_and_receive(f"restore {CFG['character']['name']}", 0.6)
    c.send_and_receive(f"goto {f['vnum']}", 1.0)
    consider = strip(c.send_and_receive(f"consider {f['target']}", 1.0))
    c.send(f"kill {f['target']}"); t0 = time.time(); chunks = []; ended = 'timeout'
    while time.time() - t0 < max_s:
        out = strip(c.receive(1.0))
        if out.strip():
            chunks.append((round(time.time() - t0, 1), out))
            if PATTERNS['player_death'].search(out): ended = 'player_died'; break
            if PATTERNS['death'].search(out): ended = 'mob_killed'; break
    text = '\n'.join(f'[t={t:6.1f}s] {line}' for t, o in chunks for line in o.splitlines() if line.strip())
    body = '\n'.join(o for _, o in chunks)
    prompts = re.findall(r'(\d+)/(\d+)hp', body)
    hp_start = int(prompts[0][0]) if prompts else None; hp_end = int(prompts[-1][0]) if prompts else None
    rounds = len(re.findall(r'\d+/\d+hp \d+/\d+mp', body))
    stats = {
        'label': f['label'], 'target': f['target'], 'vnum': f['vnum'], 'consider': consider.strip()[-200:],
        'duration_s': round(chunks[-1][0], 1) if chunks else 0, 'ended': ended, 'rounds': rounds,
        'player_hp_start': hp_start, 'player_hp_end': hp_end,
        **{k: len(PATTERNS[k].findall(body)) for k in ('telegraph', 'reaction_prompt', 'stagger', 'perfect', 'guard', 'player_hit', 'player_miss', 'mob_hit', 'low_hp_nag')},
        'distinct_lines': len(set(l.strip() for l in body.splitlines() if l.strip() and not re.match(r'^\d+/\d+hp', l))),
        'total_lines': len([l for l in body.splitlines() if l.strip()]),
    }
    stats['decision_rounds'] = stats['telegraph'] + stats['stagger']
    stats['rounds_without_decision_pct'] = round(100 * max(0, rounds - stats['decision_rounds']) / rounds) if rounds else None
    if ended != 'player_died': c.send_and_receive('flee', 0.8)
    c.send_and_receive(f"restore {CFG['character']['name']}", 0.6)   # full heal between fights (immortal)
    c.send_and_receive('goto 3001', 0.8)
    return text, stats

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', default='smoke'); ap.add_argument('--round', default='0')
    ap.add_argument('--max', type=int, default=120); ap.add_argument('--only', default='')
    a = ap.parse_args()
    out = os.path.join(ROOT, 'docs', 'gauntlet', a.run, f'round-{a.round}', 'fight'); os.makedirs(out, exist_ok=True)
    c = MUDClient(CFG['mud']['host'], CFG['mud']['telnetPort']); login(c)
    summary = []
    for f in FIGHTS:
        if a.only and f['label'] not in a.only.split(','): continue
        text, stats = run_fight(c, f, a.max)
        open(os.path.join(out, f"{f['label']}.txt"), 'w').write(text + '\n')
        json.dump(stats, open(os.path.join(out, f"{f['label']}.json"), 'w'), indent=2)
        summary.append(stats); print(f"{f['label']:14} {stats['ended']:8} {stats['duration_s']:6.1f}s rounds={stats['rounds']} telegraphs={stats['telegraph']} staggers={stats['stagger']} hp {stats['player_hp_start']}->{stats['player_hp_end']}")
    c.send_and_receive('quit', 0.5)
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=2)
    print('wrote', os.path.relpath(out, ROOT))

if __name__ == '__main__': main()
