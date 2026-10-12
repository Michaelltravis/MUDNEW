"""What real marquee quests take: the simulation (tools/balance/sim.py) can only guess at how
long a player spends reading, finding the way and looting, so the quest engine (marquee.py)
writes down what happens. Each acceptance, every stage's end, every death on the quest and its
finish (or abandonment) is a line in lib/marquee_runs.jsonl (runtime data, not in git), with
the party, its classes, its level and how they fight (rounds or real time).

An immortal's quests are tests (stages skipped with `marquee stage`), so they aren't written.
`marquee stats` (immortals) sums it up: quests finished by class and party size, their median
minutes and range, deaths a quest and the combat mode. ROUNDS in marquee_scale.py can then be
tuned from real play (docs/balance/marquee.md, "Time and the two-hour goal").
"""
import json
import os
import statistics
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'marquee_runs.jsonl')


def _mode(owner):
    try:
        import action_combat
        return 'action' if action_combat.active(owner) else 'rounds'
    except Exception:
        return 'rounds'


def record(kind, owner, m, path=LOG, **extra):
    """One line of the log: kind is 'accept', 'stage', 'death', 'finish' or 'abandon'."""
    if not m or getattr(owner, 'is_immortal', False):
        return              # no quest, or an immortal's: a test (stages skipped), not play
    who_owns = extra.pop('owner_name', None) or getattr(owner, 'name', '?')     # a helper's death counts to the owner's quest
    row = {'t': int(time.time()), 'kind': kind, 'owner': who_owns, 'quest': m.get('id'),
           'cls': m.get('cls'), 'n': m.get('n', 1), 'classes': m.get('classes'), 'level': m.get('level'),
           'stage': m.get('stage', 0), 'accepted': m.get('accepted'), 'mode': _mode(owner)}
    row.update(extra)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a') as f:
            f.write(json.dumps(row) + '\n')
    except OSError:
        pass        # a full disk must not stop a quest


def runs(path=LOG):
    """The log's quests, each {'accept': row, 'stages': [rows], 'deaths': n, 'end': row or None}."""
    out = {}
    try:
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                key = (r.get('owner'), r.get('accepted'))
                q = out.setdefault(key, {'accept': None, 'stages': [], 'deaths': 0, 'end': None})
                if r['kind'] == 'accept':
                    q['accept'] = r
                elif r['kind'] == 'stage':
                    q['stages'].append(r)
                elif r['kind'] == 'death':
                    q['deaths'] += 1
                elif r['kind'] in ('finish', 'abandon'):
                    q['end'] = r
    except OSError:
        pass
    return [q for q in out.values() if q['accept']]


def summary(path=LOG):
    """Lines for `marquee stats`: finished quests by class and party size, minutes and deaths."""
    groups = {}
    for q in runs(path):
        if not q['end'] or q['end']['kind'] != 'finish':
            continue
        a = q['accept']
        groups.setdefault((a['cls'], a['n']), []).append(q)
    lines = []
    for (cls, n), qs in sorted(groups.items()):
        mins = [(q['end']['t'] - q['accept']['t']) / 60 for q in qs]
        deaths = [q['deaths'] for q in qs]
        modes = sorted({q['accept'].get('mode', 'rounds') for q in qs})
        # short enough for a telnet line: '  necromancer  x3: 12 done, median 64 min (41-118), 0.3 deaths, rounds'
        lines.append(f"{cls:12} x{n}: {len(qs)} done, median {statistics.median(mins):.0f} min "
                     f"({min(mins):.0f}-{max(mins):.0f}), {statistics.mean(deaths):.1f} deaths, {'/'.join(modes)}")
    open_now = sum(1 for q in runs(path) if not q['end'])
    lines.append(f"{open_now} quest{'s' if open_now != 1 else ''} under way or never finished.")
    return lines
