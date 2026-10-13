#!/usr/bin/env python3
"""Zone bosses: each dungeon boss of the world's zones (up to the mortal level cap, not a marquee
quest's) fought by a lone hero of every class at the boss's level, with the game's own combat code
on a simulated clock (sim.py: the same heroes, rotation, wind-ups and world ticks), sized as the
game sizes it (bosses.size_zone_boss).

    python3 tools/balance/bosses.py                         # every boss, every class, one run each
    python3 tools/balance/bosses.py --runs 2 --report docs/balance/bosses.md
    python3 tools/balance/bosses.py --calibrate             # each boss's share (bosses.ZONE_BOSS_DAMAGE)

Per boss: its level and health, and per class the minutes the fight took, the most of the hero's
health it took at the worst moment (a death is all of it), and deaths; then a party of three
(warrior, cleric, mage) at its level for comparison. --calibrate tries, boss by boss, a grid of
shares of its own blows and abilities and takes the one at which the median lone hero loses
--target of their health, or --max-deaths of them die, whichever comes first; it prints the
table for bosses.py. Findings: docs/balance/marquee.md, "Zone bosses".
"""
import argparse
import asyncio
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402

PARTY = ['warrior', 'cleric', 'mage']
_n = [0]


def zone_bosses(world, only=None):
    """(level, vnum, name, health) of every boss the game sizes as a zone boss."""
    from bosses import create_mob_from_prototype
    out = []
    for vnum, proto in world.mob_prototypes.items():
        if 'boss' not in (proto.get('flags') or []) and not proto.get('boss'):
            continue
        if only and vnum not in only:
            continue
        m = create_mob_from_prototype(dict(proto), world)
        if getattr(m, 'zone_sized', False):
            out.append((m.level, vnum, m.name, m.max_hp))
    return sorted(out)


def _leave(world, heroes):
    from pets import PetManager
    for h in heroes:
        for pet in PetManager.get_player_pets(h):
            if pet in world.npcs:
                world.npcs.remove(pet)
            if pet.room is not None and pet in pet.room.characters:
                pet.room.characters.remove(pet)
        world.players.pop(h.name.lower(), None)
        if h.room is not None and h in h.room.characters:
            h.room.characters.remove(h)


async def duel(world, vnum, classes, level, seed, a, share=None):
    """One fight: the heroes of these classes (one: alone) against the boss. Returns the seconds it
    took, the most any hero lost at the worst moment (1 for a death), the deaths, the boss felled."""
    from bosses import create_mob_from_prototype
    room = world.rooms.get(3054) or next(iter(world.rooms.values()))
    random.seed(seed)
    heroes = []
    for cls in classes:
        _n[0] += 1
        heroes.append(await sim.make_hero(world, cls, max(1, level), f'Zb{cls[:3].title()}{_n[0]}', a.gear))
    foe = create_mob_from_prototype(dict(world.mob_prototypes[vnum]), world)
    if share is not None:
        foe._dmg_scale = share
    # a call for help (boss_mechanics.CallGuards) raises its followers here: the temple's
    # neighbours aren't the boss's, and those who came would be gone for the next fight
    for m in getattr(foe, 'mechanics', ()):
        if m.spec.get('type') == 'call_guards':
            m.spec = dict(m.spec, rooms=0)
    sim.DEATHS.clear()
    secs = await sim.fight(world, room, heroes, [foe], a.mode, a.dodge, {}, max_secs=a.max_minutes * 60)
    dead = len(sim.DEATHS)
    worst = max(1.0 if h.name in sim.DEATHS else 1 - getattr(h, '_low', h.hp) / max(1, h.max_hp) for h in heroes)
    _leave(world, heroes)
    return secs, worst, dead, foe.hp <= 0


async def alone(world, vnum, level, a, share=None):
    """Every class alone: [(class, secs, worst, died, felled)] over --runs."""
    rows = []
    for cls in a.classes.split(','):
        for r in range(a.runs):
            secs, worst, dead, felled = await duel(world, vnum, [cls], level, 4000 + r, a, share)
            rows.append((cls, secs, worst, dead > 0, felled))
    return rows


async def calibrate(world, bosses, a):
    grid = [float(x) for x in a.grid.split(',')]
    table = {}
    for level, vnum, name, hp in bosses:
        curve = []
        for share in grid:
            rows = await alone(world, vnum, level, a, share)
            cost = statistics.median(w for _, _, w, _, _ in rows)
            deaths = sum(d for _, _, _, d, _ in rows) / len(rows)
            curve.append((share, cost, deaths))
            if cost >= a.target and deaths >= a.max_deaths:
                break
        x = min(sim._crossing([(s, c) for s, c, _ in curve], a.target), sim._crossing([(s, d) for s, _, d in curve], a.max_deaths))
        table[vnum] = (round(x, 2), name, level)
        print(f"L{level:>2} {vnum:>6} {name[:28]:28} " + ' '.join(f"{s:g}:{100 * c:.0f}%/{100 * d:.0f}%d" for s, c, d in curve)
              + f"  -> {x:.2f}", flush=True)
    print('\nZONE_BOSS_DAMAGE = {')
    for vnum, (x, name, level) in table.items():
        print(f"    {vnum}: {x},{' ' * (6 - len(str(x)))}# L{level} {name}")
    print('}')


async def report(world, bosses, a):
    classes = a.classes.split(',')
    lines = ['| boss | level | health | ' + ' | '.join(classes) + ' | lone heroes: median worst, deaths | party of three |',
             '|---|---|---|' + '---|' * len(classes) + '---|---|']
    every_w, every_d, n = [], 0, 0
    for level, vnum, name, hp in bosses:
        rows = await alone(world, vnum, level, a)
        by = {}
        for cls, secs, w, d, felled in rows:
            by.setdefault(cls, []).append((secs, w, d, felled))
        cells = []
        for cls in classes:
            rs = by[cls]
            secs = statistics.median(s for s, _, _, _ in rs)
            w = statistics.median(x for _, x, _, _ in rs)
            d = sum(x for _, _, x, _ in rs)
            lived = not any(f for _, _, _, f in rs) and not d
            cells.append(f"{secs / 60:.1f}m {100 * w:.0f}%" + (f" {d}†" if d else '') + (' (lived)' if lived else ''))
        ws = [w for _, _, w, _, _ in rows]
        ds = sum(d for _, _, _, d, _ in rows)
        every_w += ws
        every_d += ds
        n += len(rows)
        psecs, pw, pd, _ = await duel(world, vnum, PARTY, level, 4100, a)
        party = f"{psecs / 60:.1f}m {100 * pw:.0f}%" + (f" {pd}†" if pd else '')
        lines.append(f"| {name} | {level} | {hp} | " + ' | '.join(cells) + f" | {100 * statistics.median(ws):.0f}%, {ds}/{len(rows)} | {party} |")
        print(f"L{level:>2} {vnum:>6} {name[:28]:28} hp {hp:>6}  " + '  '.join(f"{c[:4]} {x}" for c, x in zip(classes, cells))
              + f"   | median {100 * statistics.median(ws):.0f}% deaths {ds}/{len(rows)} | party {party}", flush=True)
    summary = f"All: a lone hero's median worst {100 * statistics.median(every_w):.0f}%, deaths {every_d}/{n}."
    print('\n' + summary)
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        head = ('# Zone bosses, measured\n\n'
                f'`python3 tools/balance/bosses.py --runs {a.runs} --report ...`: each zone boss against a lone hero of every '
                "class at the boss's level, then a party of three (warrior, cleric, mage), with the game's own combat code "
                '(`tools/balance/sim.py`). Each cell: the minutes the fight took, the most of the hero\'s health it took at '
                'the worst moment (a death is all of it), and deaths (†) over the runs; "(lived)" is a fight called off at '
                f'{a.max_minutes:g} minutes. Why the bosses are sized so: `docs/balance/marquee.md`, "Zone bosses".\n\n')
        with open(a.report, 'w') as f:
            f.write(head + '\n'.join(lines) + '\n\n' + summary + '\n')


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--classes', default=','.join(sim.CLASSES))
    ap.add_argument('--bosses', default='', help='only these vnums, e.g. 5318,27015')
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--mode', choices=['rounds', 'action'], default='rounds')
    ap.add_argument('--dodge', type=float, default=0.6, help='chance a hero steps out of a marked blow')
    ap.add_argument('--gear', type=float, default=0.75, help='percentile of the gear a slot offers at the level')
    ap.add_argument('--max-minutes', type=float, default=15, help='a fight longer than this is called off')
    ap.add_argument('--report', default=None, help='write the table (markdown) here too')
    ap.add_argument('--calibrate', action='store_true', help="each boss's share of its own damage (bosses.ZONE_BOSS_DAMAGE)")
    ap.add_argument('--target', type=float, default=0.5, help="--calibrate: the share of a lone hero's health the median fight costs")
    ap.add_argument('--max-deaths', type=float, default=0.25, help="--calibrate: ...or the share of lone heroes it may kill")
    ap.add_argument('--grid', default='0.04,0.06,0.08,0.1,0.12,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.8,1.0,1.25,1.6,2.0,2.5,3.2,4.0', help='--calibrate: the shares tried')
    a = ap.parse_args()
    world = await sim.load_world()
    sim.patch_deaths(world)
    sim.patch_damage()
    only = {int(x) for x in a.bosses.split(',') if x.strip()}
    bosses = zone_bosses(world, only)
    print(f"{len(bosses)} zone bosses; lone {', '.join(a.classes.split(','))} at the boss's level, {a.runs} run(s) each", flush=True)
    if a.calibrate:
        await calibrate(world, bosses, a)
    else:
        await report(world, bosses, a)


if __name__ == '__main__':
    asyncio.run(main())
