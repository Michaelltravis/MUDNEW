#!/usr/bin/env python3
"""Gauntlet evidence: the FIRST HOUR as numbers (telnet, no browser).

A fresh level-1 character walks the newcomer ladder — training dummy, then the
level 1–5 creatures of Midgaard — fighting each once, resting when hurt, and
we record what "easy to start, hard to master" actually costs: seconds per
fight, HP left, rests, deaths, and when levels 2..5 arrive.

  python3 tools/gauntlet/curve.py --run progression-01 [--name NewYzxgo --password newcomer1] [--admin Gauntletb --admin-password gauntlet1] [--max 90]

Two telnet sessions: the NEWCOMER (a real level-1 character forged through the
creation flow, with its starting kit — `advance` only levels up, so no admin
can make one) does every fight; the ADMIN stands in each ladder room, repops
it, transfers the newcomer in, and restores them after a death (a real player
would respawn at the temple; we keep the ladder going and count the death).
Writes docs/gauntlet/<run>/curve.json, curve.md and fights/<n>_<target>.txt.
"""
import argparse, json, os, re, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from test_suite import MUDClient  # noqa: E402

ANSI = re.compile(r'\x1b\[[0-9;]*m')
def strip(s): return ANSI.sub('', s or '')

# vnum, keyword, what a newcomer sees it as
# each step: label, then (vnum, keyword) candidates — the first one present is fought
# (fidos and drunks wander; a sentinel alternative keeps the ladder measurable)
LADDER = [
    # the tutorial's own route: training dummy, then the Newbie Zone the chain sends you to
    ('training dummy (tutorial)', [(3078, 'dummy')]),
    ('newbie zone: crawler (L1)', [(18602, 'crawler'), (18606, 'crawler'), (18609, 'crawler')]),
    ('newbie zone: newbie (L2)', [(18600, 'newbie'), (18607, 'newbie'), (18646, 'newbie')]),
    ('newbie zone: crawler (L1)', [(18609, 'crawler'), (18606, 'crawler'), (18602, 'crawler')]),
    ('newbie zone: newbie (L2)', [(18607, 'newbie'), (18646, 'newbie'), (18600, 'newbie')]),
    ('newbie zone: keeper (L3)', [(18606, 'keeper'), (18640, 'newbie')]),
    ('newbie zone: quasit (L3)', [(18621, 'quasit'), (18627, 'quasit'), (18636, 'quasit')]),
    ('newbie zone: newbie (L4)', [(18604, 'newbie'), (18620, 'newbie'), (18624, 'newbie')]),
    ('newbie zone: quasit (L3)', [(18638, 'quasit'), (18627, 'quasit'), (18636, 'quasit')]),
    ('newbie zone: newbie (L4)', [(18633, 'newbie'), (18637, 'newbie'), (18620, 'newbie')]),
    ('newbie zone: pitbeast (L5)', [(18605, 'pitbeast'), (18645, 'newbie')]),
    ('newbie zone: balcony newbie (L5)', [(18645, 'newbie'), (18605, 'pitbeast')]),
]
TELEGRAPH = re.compile(r'\(brace or sidestep', re.I)
DEATH = re.compile(r'\bis dead\b|has been slain|You killed|is DEAD', re.I)
PDEATH = re.compile(r'soul slipping away|You have died|You are dead', re.I)
LEVEL_UP = re.compile(r'LEVEL UP|You (?:have )?(?:gained|reached|advance to) level|You rise to level', re.I)
PROMPT = re.compile(r'(\d+)/(\d+)hp')

def login(c, name, pw):
    c.connect(); time.sleep(1); c.receive(2)
    for cmd in (name, pw, f'play {name}'): c.send_and_receive(cmd, 1.0)

def score(c):
    out = strip(c.send_and_receive('score', 1.0))
    lv = re.search(r'Level:\s*(\d+)', out); xp = re.search(r'Experience:\s*(\d+)', out)
    hp = PROMPT.findall(out)
    return {'level': int(lv.group(1)) if lv else None, 'exp': int(xp.group(1)) if xp else None,
            'hp': int(hp[-1][0]) if hp else None, 'maxhp': int(hp[-1][1]) if hp else None}

def rest_up(c, max_s=150):
    """rest until ≥ 90% HP; returns seconds spent"""
    t0 = time.time(); c.send_and_receive('rest', 0.8)
    while time.time() - t0 < max_s:
        out = strip(c.receive(2.0)); m = PROMPT.findall(out)
        if m and int(m[-1][0]) >= 0.9 * int(m[-1][1]): break
        c.send('')   # nudge a prompt
    c.send_and_receive('stand', 0.6)
    return round(time.time() - t0, 1)

def fight(adm, c, name, cands, max_s, out_path, smart=True):
    c.send_and_receive('stand', 0.4)
    consider = ''; vnum = kw = None
    for v, k in cands:
        adm.send_and_receive(f'goto {v}', 1.0); adm.send_and_receive('zreset', 1.2); adm.send_and_receive(f'transfer {name}', 1.0)
        c.receive(1.0)
        consider = strip(c.send_and_receive(f'consider {k}', 1.0))
        if "don't see" not in consider: vnum, kw = v, k; break
    if vnum is None:
        return {'vnum': cands[0][0], 'target': cands[0][1], 'threat': 'absent (every candidate wandered off)', 'ended': 'absent', 'duration_s': 0, 'rounds': 0,
                'level_before': score(c)['level'], 'level_after': None, 'levelled': False, 'exp_before': None, 'exp_after': None, 'hp_start': None, 'hp_end': None, 'maxhp': None}
    threat = re.search(r'Threat:\s*([^|]+)\|', consider)
    before = score(c)
    c.send(f'kill {kw}'); t0 = time.time(); body = []; ended = 'timeout'; levelled = False
    # "three buttons": a newcomer opens with bash (button 3) and answers the
    # wind-up prompt with brace — the client's Guide and reaction chips teach exactly this
    last_bash = -99; braces = 0; bashes = 0
    while time.time() - t0 < max_s:
        out = strip(c.receive(1.0))
        if smart:
            if TELEGRAPH.search(out): c.send('brace'); braces += 1
            elif time.time() - t0 - last_bash > 9 and 'collapse' not in out: c.send(f'bash {kw}'); last_bash = time.time() - t0; bashes += 1
        if out.strip():
            body.append((round(time.time() - t0, 1), out))
            if LEVEL_UP.search(out): levelled = True
            if PDEATH.search(out): ended = 'player_died'; break
            if DEATH.search(out): ended = 'mob_killed'; break
    text = '\n'.join(o for _, o in body); dur = round(time.time() - t0, 1)
    open(out_path, 'w').write(consider + '\n' + '\n'.join(f'[t={t:6.1f}s] {line}' for t, o in body for line in o.splitlines() if line.strip()) + '\n')
    prompts = PROMPT.findall(text)
    rounds = len(re.findall(r'\d+/\d+hp \d+/\d+mp', text))
    if ended == 'timeout': c.send_and_receive('flee', 0.8)
    if ended == 'player_died':
        time.sleep(2.0); c.receive(2.0)
        adm.send_and_receive(f'restore {name}', 0.8)
    time.sleep(0.8)
    after = score(c)
    return {
        'vnum': vnum, 'target': kw, 'threat': threat.group(1).strip() if threat else consider.strip()[-80:],
        'level_before': before['level'], 'level_after': after['level'], 'levelled': levelled or (after['level'] or 0) > (before['level'] or 0),
        'exp_before': before['exp'], 'exp_after': after['exp'],
        'duration_s': dur, 'rounds': rounds, 'ended': ended, 'bashes': bashes, 'braces': braces,
        'hp_start': int(prompts[0][0]) if prompts else before['hp'], 'hp_end': int(prompts[-1][0]) if prompts else after['hp'], 'maxhp': after['maxhp'],
    }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', default='progression-01')
    ap.add_argument('--name', default='NewYzxgo'); ap.add_argument('--password', default='newcomer1')
    ap.add_argument('--admin', default='Gauntletb'); ap.add_argument('--admin-password', default='gauntlet1'); ap.add_argument('--max', type=int, default=90); ap.add_argument('--dumb', action='store_true', help='auto-attack only (no bash, no brace)')
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, 'docs', 'gauntlet', a.run); os.makedirs(os.path.join(out_dir, 'fights'), exist_ok=True)
    adm = MUDClient('localhost', 4000); login(adm, a.admin, a.admin_password)
    adm.send_and_receive('settime 14', 0.3); adm.send_and_receive('setweather clear', 0.3)
    c = MUDClient('localhost', 4000); login(c, a.name, a.password)
    adm.send_and_receive(f'restore {a.name}', 0.8)
    start = score(c); t_start = time.time(); fights = []; rests = []; deaths = 0; level_times = {}
    for i, (label, cands) in enumerate(LADDER, 1):
        f = fight(adm, c, a.name, cands, a.max, os.path.join(out_dir, 'fights', f'{i:02d}_{cands[0][1]}.txt'), smart=not a.dumb)
        f['label'] = label; f['t_elapsed_s'] = round(time.time() - t_start, 1)
        fights.append(f); print(json.dumps(f))
        if f['ended'] == 'player_died': deaths += 1
        for lv in range(2, 11):
            if f['level_after'] and f['level_after'] >= lv and lv not in level_times: level_times[lv] = f['t_elapsed_s']
        if f['hp_end'] is not None and f['maxhp'] and f['hp_end'] < 0.6 * f['maxhp'] and f['ended'] != 'player_died':
            r = rest_up(c); rests.append({'after': label, 'seconds': r}); print(json.dumps({'rest': r}))
    end = score(c)
    summary = {'run': a.run, 'character': a.name, 'start': start, 'end': end, 'fights': fights, 'rests': rests, 'deaths': deaths,
               'level_reached': end['level'], 'time_to_level': level_times, 'total_s': round(time.time() - t_start, 1),
               'active_fight_s': round(sum(f['duration_s'] for f in fights), 1), 'rest_s': round(sum(r['seconds'] for r in rests), 1)}
    json.dump(summary, open(os.path.join(out_dir, 'curve.json'), 'w'), indent=2)
    md = [f"# {a.run} — the first hour as numbers\n", f"Character: {a.name}, a real level-{start['level']} character with its starting kit. Ladder of {len(LADDER)} fights, resting when under 60% HP; a death is restored by an admin so the ladder continues (a real player respawns at the temple).\n",
          f"**Level reached: {end['level']}** · deaths: {deaths} · total {summary['total_s']}s (fighting {summary['active_fight_s']}s, resting {summary['rest_s']}s)\n",
          'Time to level: ' + (', '.join(f"L{k} at {v}s" for k, v in sorted(level_times.items())) or 'no level gained') + '\n',
          '| # | fight | target | threat | lvl | rounds | s | bash/brace | HP end | result |', '|---|---|---|---|---|---|---|---|---|---|']
    for i, f in enumerate(fights, 1):
        md.append(f"| {i} | {f['label']} | {f['target']} | {f['threat']} | {f['level_before']}→{f['level_after']} | {f['rounds']} | {f['duration_s']} | {f.get('bashes', 0)}/{f.get('braces', 0)} | {f['hp_end']}/{f['maxhp']} | {f['ended']}{' ↑' if f['levelled'] else ''} |")
    if rests: md.append('\nRests: ' + ', '.join(f"{r['seconds']}s after {r['after']}" for r in rests))
    open(os.path.join(out_dir, 'curve.md'), 'w').write('\n'.join(md) + '\n')
    print('wrote', os.path.relpath(out_dir, ROOT))
    for cl in (c, adm):
        try: cl.send_and_receive('quit', 0.5)
        except Exception: pass

if __name__ == '__main__':
    main()
