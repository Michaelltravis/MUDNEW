#!/usr/bin/env python3
"""Gauntlet evidence: the FIRST HOUR as numbers (telnet, no browser).

A fresh level-1 character walks the newcomer ladder — training dummy, then the
level 1–5 creatures of Midgaard — fighting each once, resting when hurt, and
we record what "easy to start, hard to master" actually costs: seconds per
fight, HP left, rests, deaths, and when levels 2..5 arrive.

  python3 tools/gauntlet/curve.py --run progression-01 [--name Gauntletb --password gauntlet1] [--max 90]

Writes docs/gauntlet/<run>/curve.json and curve.md. The character is reset to
level 1 (admin `advance`) and left wherever the ladder ends.
"""
import argparse, json, os, re, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from test_suite import MUDClient  # noqa: E402

ANSI = re.compile(r'\x1b\[[0-9;]*m')
def strip(s): return ANSI.sub('', s or '')

# vnum, keyword, what a newcomer sees it as
LADDER = [
    (3078, 'dummy', 'training dummy (tutorial)'),
    (3012, 'fido', 'fido, Main Street'),
    (3074, 'rat', 'rat, Forgotten Passage'),
    (3007, 'drunk', 'drunk, Grunting Boar'),
    (3024, 'urchin', 'street urchin, Poor Alley'),
    (3048, 'patron', 'drunk patron, Grubby Inn'),
    (3032, 'rottweiler', 'rottweiler, Pet Shop'),
    (3032, 'wolf', 'wolf, Pet Shop'),
    (3026, 'pickpocket', 'pickpocket, Dark Alley'),
    (3026, 'mercenary', 'mercenary, Dark Alley'),
    (3012, 'fido', 'fido again (second lap)'),
    (3024, 'urchin', 'street urchin again'),
]
DEATH = re.compile(r'\bis dead\b|has been slain|You killed|is DEAD', re.I)
PDEATH = re.compile(r'soul slipping away|You have died|You are dead', re.I)
LEVEL_UP = re.compile(r'LEVEL UP|You (?:have )?(?:gained|reached|advance to) level|You rise to level', re.I)
PROMPT = re.compile(r'(\d+)/(\d+)hp')

def login(c, name, pw):
    c.connect(); time.sleep(1); c.receive(2)
    for cmd in (name, pw, f'play {name}'): c.send_and_receive(cmd, 1.0)
    c.send_and_receive('settime 14', 0.3); c.send_and_receive('setweather clear', 0.3)

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

def fight(c, vnum, kw, max_s):
    c.send_and_receive('stand', 0.4); c.send_and_receive(f'goto {vnum}', 1.0); c.send_and_receive('zreset', 1.2)
    consider = strip(c.send_and_receive(f'consider {kw}', 1.0))
    threat = re.search(r'Threat:\s*([^|]+)\|', consider)
    before = score(c)
    c.send(f'kill {kw}'); t0 = time.time(); body = []; ended = 'timeout'; levelled = False
    while time.time() - t0 < max_s:
        out = strip(c.receive(1.0))
        if out.strip():
            body.append(out)
            if LEVEL_UP.search(out): levelled = True
            if PDEATH.search(out): ended = 'player_died'; break
            if DEATH.search(out): ended = 'mob_killed'; break
    text = '\n'.join(body); dur = round(time.time() - t0, 1)
    prompts = PROMPT.findall(text)
    rounds = len(re.findall(r'\d+/\d+hp \d+/\d+mp', text))
    if ended == 'timeout': c.send_and_receive('flee', 0.8)
    if ended == 'player_died':
        # a real newcomer respawns at the temple; we restore so the ladder continues
        c.send_and_receive(f'restore {CHAR}', 0.8)
    time.sleep(0.8)
    after = score(c)
    return {
        'vnum': vnum, 'target': kw, 'threat': threat.group(1).strip() if threat else consider.strip()[-80:],
        'level_before': before['level'], 'level_after': after['level'], 'levelled': levelled or (after['level'] or 0) > (before['level'] or 0),
        'exp_before': before['exp'], 'exp_after': after['exp'],
        'duration_s': dur, 'rounds': rounds, 'ended': ended,
        'hp_start': int(prompts[0][0]) if prompts else before['hp'], 'hp_end': int(prompts[-1][0]) if prompts else after['hp'], 'maxhp': after['maxhp'],
    }

def main():
    global CHAR
    ap = argparse.ArgumentParser(); ap.add_argument('--run', default='progression-01')
    ap.add_argument('--name', default='Gauntletb'); ap.add_argument('--password', default='gauntlet1'); ap.add_argument('--max', type=int, default=90)
    a = ap.parse_args(); CHAR = a.name
    out_dir = os.path.join(ROOT, 'docs', 'gauntlet', a.run); os.makedirs(out_dir, exist_ok=True)
    c = MUDClient('localhost', 4000); login(c, a.name, a.password)
    c.send_and_receive(f'advance {a.name} 1', 0.8); c.send_and_receive(f'restore {a.name}', 0.8)
    start = score(c); t_start = time.time(); fights = []; rests = []; deaths = 0; level_times = {}
    for vnum, kw, label in LADDER:
        f = fight(c, vnum, kw, a.max); f['label'] = label; f['t_elapsed_s'] = round(time.time() - t_start, 1)
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
    md = [f"# {a.run} — the first hour as numbers\n", f"Character: {a.name}, reset to level 1. Ladder of {len(LADDER)} fights, resting when under 60% HP.\n",
          f"**Level reached: {end['level']}** · deaths: {deaths} · total {summary['total_s']}s (fighting {summary['active_fight_s']}s, resting {summary['rest_s']}s)\n",
          'Time to level: ' + ', '.join(f"L{k} at {v}s" for k, v in sorted(level_times.items())) + '\n',
          '| # | fight | threat | lvl | rounds | s | HP end | result |', '|---|---|---|---|---|---|---|---|']
    for i, f in enumerate(fights, 1):
        md.append(f"| {i} | {f['label']} | {f['threat']} | {f['level_before']}→{f['level_after']} | {f['rounds']} | {f['duration_s']} | {f['hp_end']}/{f['maxhp']} | {f['ended']}{' ↑' if f['levelled'] else ''} |")
    if rests: md.append('\nRests: ' + ', '.join(f"{r['seconds']}s after {r['after']}" for r in rests))
    open(os.path.join(out_dir, 'curve.md'), 'w').write('\n'.join(md) + '\n')
    print('wrote', os.path.relpath(out_dir, ROOT))
    try: c.send_and_receive('quit', 0.5)
    except Exception: pass

if __name__ == '__main__':
    main()
