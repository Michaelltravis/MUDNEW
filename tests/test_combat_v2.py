"""Live test for combat v2 (the 3D client's fights): reach, structured events, wind-ups.

Needs a running server (./run.sh) and the gauntlet admin account (tools/gauntlet/README.md);
it fights as the level-6 warrior Gauntletb on the `gauntletb` account.
    python3 tests/test_combat_v2.py
Checks: the cast parser honours quotes and multi-word spells; a melee hero out of reach gets
no blow and an 'oor' event while the creature walks in ('move' events); in reach, swings
arrive as 'attack' events followed by their 'dmg' with the health left; a skill aimed at a
creature you are not fighting opens the fight; a wind-up marks the ground and, stepped out
of, resolves with the hero 'dodged' (or is broken with a 'cancel').
"""
import asyncio
import json
import os
import sys
import time
import types

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import test_webmove as tw  # noqa: E402  (Telnet helper, check(), failures)

ROOM, SPECTRE = 18620, 18610          # a quiet crypt room; "the dark spectre", level 6
check, failures = tw.check, tw.failures


async def cast_parser():
    """`cast 'lightning bolt' orc` once looked for a target called "bolt orc"."""
    import commands
    seen = []

    class FakeSpells:
        @staticmethod
        async def cast_spell(player, spell, target):
            seen.append((spell, target))

    real = sys.modules.get('spells')
    sys.modules['spells'] = types.SimpleNamespace(SpellHandler=FakeSpells, SPELLS={})

    class P:
        spells = {'magic_missile': 50, 'lightning_bolt': 50, 'fireball': 50, 'animate_dead': 50, 'cure_light': 50}
        config = types.SimpleNamespace(COLORS={'red': '', 'cyan': '', 'reset': '', 'yellow': ''})

        async def send(self, m):
            pass
    try:
        for line, want in (("'lightning bolt' orc", ('lightning_bolt', 'orc')),
                           ("'magic missile' sage aldric", ('magic_missile', 'sage aldric')),
                           ("magic missile orc", ('magic_missile', 'orc')),
                           ("fire orc", ('fireball', 'orc')),
                           ("animate dead knight", ('animate_dead', 'knight')),
                           ("cure light", ('cure_light', None))):
            seen.clear()
            await commands.CommandHandler.cmd_cast(P(), line.split())
            check(seen == [want], f'cast {line} -> {want}')
    finally:
        if real is not None:
            sys.modules['spells'] = real
        else:
            sys.modules.pop('spells', None)


async def main():
    await cast_parser()
    tw.ACCOUNT, tw.PASSWORD, tw.CHAR = 'gauntletb', 'gauntlet1', 'Gauntletb'
    tn = tw.Telnet()
    await tn.open()
    for line in ('wake', 'stand', f'goto {ROOM}', 'purge', 'restore'):
        await tn.cmd(line, 0.6)
    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(f'ws://{tw.HOST}:{tw.MAP}/') as ws:
            await ws.send_str(json.dumps({'type': 'subscribe', 'player': tw.CHAR, 'mode': 'near'}))
            got = []

            async def pump():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        d = json.loads(msg.data)
                        d['_t'] = time.time()
                        got.append(d)
            pumper = asyncio.create_task(pump())

            def events(kind=None):
                out = [dict(e, _t=d['_t']) for d in got if d.get('type') == 'combat_events' for e in d['events']]
                return [e for e in out if kind is None or e['k'] == kind]

            async def spawn():
                await tn.cmd(f'mload {SPECTRE}', 0.6)
                got.clear()
                # a fresh subscribe answers with the current map (look sends none)
                await ws.send_str(json.dumps({'type': 'subscribe', 'player': tw.CHAR, 'mode': 'near'}))
                for _ in range(50):          # a busy machine can be slow to answer
                    maps = [d for d in got if d.get('type') == 'map_data']
                    room = next((r for d in reversed(maps) for r in (d.get('nearby') or []) if r['vnum'] == ROOM), None)
                    mob = next((m for m in (room or {}).get('mobs', []) if 'spectre' in m['name'].lower()), None)
                    if mob:
                        return mob
                    await asyncio.sleep(0.2)
                return None

            async def place(hero, mob_id=None, mob_at=None):
                await ws.send_str(json.dumps({'type': 'pos', 'vnum': ROOM, 'x': hero[0], 'z': hero[1]}))
                if mob_id is not None:
                    await ws.send_str(json.dumps({'type': 'mobpos', 'vnum': ROOM, 'mobs': [{'id': mob_id, 'x': mob_at[0], 'z': mob_at[1]}]}))
                await asyncio.sleep(0.3)

            # 1. out of reach: no blow, an 'oor' event, the creature walks in, then blows land
            mob = await spawn()
            check(mob is not None, 'a spectre appears in the near-mode payload with an id')
            if mob:
                await place((3.0, 7.0), mob['id'], (20.0, 7.0))
                got.clear()
                text = await tn.cmd('kill spectre', 0.8)
                check('out of reach' in text, 'a melee swing at 17 m is refused: "out of reach"')
                oor = events('oor')
                check(bool(oor) and oor[0].get('auto') and oor[0].get('need') == 2.5, "…with an 'oor' event (need 2.5 m)")
                t0 = time.time()
                while time.time() - t0 < 15 and not [e for e in events('attack') if e.get('src') == {'m': mob['id']}]:
                    await asyncio.sleep(0.2)
                moves = [e for e in events('move') if e.get('src') == {'m': mob['id']}]
                check(bool(moves) and min(abs(m['x'] - 3.0) for m in moves) < 2.6, "the spectre walks in ('move' events) to reach")
                hits = events('attack')
                check(bool(hits), "in reach, swings arrive as 'attack' events")
                dmg = events('dmg')
                check(bool(dmg) and all('left' in d for d in dmg), "wounds arrive as 'dmg' with the health left")

                # 2. a wind-up: step out of the marked ground before it lands (only a fresh
                # one counts: one marked earlier may already have landed)
                await place((3.0, 7.0))
                got.clear()
                t0, wu, hero = time.time(), None, None
                while time.time() - t0 < 24 and wu is None:
                    await tn.cmd('restore', 0.3)
                    wu = next((e for e in events('windup') if e.get('area') and e['area'].get('x') is not None), None)
                if wu:
                    a = wu['area']
                    hero = (min(22.0, a['x'] + a['r'] + 3.0), a['z'])
                    await place(hero)
                    t1 = time.time()
                    end = None
                    while time.time() - t1 < 7 and end is None:
                        await asyncio.sleep(0.2)
                        end = next((e for e in events() if e['k'] in ('resolve', 'cancel') and e.get('src') == wu['src']), None)
                    check(end is not None and (end['k'] == 'cancel' or {'p': tw.CHAR} in (end.get('dodged') or [])),
                          f"a {wu.get('kind')} wind-up stepped out of resolves dodged (or is broken): {end and end['k']}")
                    if end is not None and end['k'] == 'resolve':
                        dt = end['_t'] - wu['_t']
                        check(abs(dt - wu['ms'] / 1000) < 0.6, f"it lands when the mark said ({dt:.2f} s vs {wu['ms'] / 1000:.1f} s)")
                else:
                    print('skip no wind-up declared in 24 s (it is a dice roll)')
            await tn.cmd('restore', 0.3)
            await tn.cmd('purge', 0.6)
            await asyncio.sleep(3.5)        # let the fight end

            # 3. a skill opens a fight
            mob = await spawn()
            if mob:
                await place((10.0, 7.0), mob['id'], (11.5, 7.0))
                got.clear()
                text = await tn.cmd('bash spectre', 1.0)
                ab = events('ability')
                check(bool(ab) and ab[0].get('ability') == 'bash', "'bash spectre' when not fighting sends an 'ability' event")
                check('must be fighting' not in text.lower(), '…and opens the fight instead of refusing')
            await tn.cmd('restore', 0.3)
            await tn.cmd('purge', 0.6)
            pumper.cancel()
    tn.w.close()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
