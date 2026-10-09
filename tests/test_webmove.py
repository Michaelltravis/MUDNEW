"""Live test for the 3D client's server contract: /zonemap and `webmove <from> <to>`.

Needs a running server (./run.sh) and the gauntlet admin account (tools/gauntlet/README.md).
    python3 tests/test_webmove.py
Checks: /zonemap invariants for every zone; a legal webmove moves you and answers
move_result ok on the map socket with no input echo and no full room description; an
out-of-step `from`, an exit that does not exist, a closed door and sleeping are refused with
the server's own reason; near-mode map payloads carry `nearby` rooms with mob ids.
"""
import asyncio
import json
import re
import sys
import urllib.request

import aiohttp

HOST, TELNET, MAP = 'localhost', 4000, 4001
ACCOUNT, PASSWORD, CHAR = 'gauntlet', 'gauntlet1', 'Gauntlet'
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07')
CARD = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
REV = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
failures = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        failures.append(what)


def get_json(path):
    with urllib.request.urlopen(f'http://{HOST}:{MAP}{path}', timeout=20) as r:
        return json.loads(r.read())


def zonemap_invariants():
    atlas = get_json('/atlas')
    zones = sorted({r['zone'] for r in atlas['rooms']})
    bad = 0
    for zn in zones:
        zm = get_json(f'/zonemap?zone={zn}')
        byv = {r['vnum']: r for r in zm['rooms']}
        cells = [tuple(r['cell']) for r in zm['rooms']]
        if len(cells) != len(set(cells)):
            bad += 1
            print(f'  zone {zn}: two rooms share a cell')
        for r in zm['rooms']:
            for d, e in r['exits'].items():
                if e['kind'] not in ('open', 'passage', 'zone'):
                    bad += 1
                if e['kind'] == 'open':
                    t = byv.get(e['to'])
                    dx, dy = CARD[d]
                    if not t or t['cell'] != [r['cell'][0] + dx, r['cell'][1] + dy] \
                            or t['exits'].get(REV[d], {}).get('to') != r['vnum']:
                        bad += 1
                        print(f"  zone {zn}: open exit {r['vnum']} {d} is not mutual+adjacent")
    check(bad == 0, f'/zonemap invariants hold for all {len(zones)} zones')


class Telnet:
    async def open(self):
        self.r, self.w = await asyncio.open_connection(HOST, TELNET)
        self.buf = ''
        await self.read(1.5)
        for line in (ACCOUNT, PASSWORD, f'play {CHAR}'):
            await self.cmd(line, 1.2)

    async def read(self, secs):
        out = ''
        end = asyncio.get_event_loop().time() + secs
        while True:
            left = end - asyncio.get_event_loop().time()
            if left <= 0:
                break
            try:
                data = await asyncio.wait_for(self.r.read(65536), timeout=left)
            except asyncio.TimeoutError:
                break
            if not data:
                break
            out += data.decode(errors='ignore')
        return ANSI.sub('', out)

    async def cmd(self, line, secs=0.8):
        self.w.write((line + '\r\n').encode())
        await self.w.drain()
        return await self.read(secs)


async def main():
    zonemap_invariants()
    tn = Telnet()
    await tn.open()
    await tn.cmd('wake', 0.4)
    await tn.cmd('stand', 0.4)
    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(f'ws://{HOST}:{MAP}/') as ws:
            await ws.send_str(json.dumps({'type': 'subscribe', 'player': CHAR, 'mode': 'near'}))
            events = []

            async def pump():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        events.append(json.loads(msg.data))
            pumper = asyncio.create_task(pump())

            async def result_after(line, secs=1.5):
                events.clear()
                text = await tn.cmd(line, secs)
                res = [e for e in events if e.get('type') == 'move_result']
                return (res[-1] if res else None), text, list(events)

            # start in the temple of Midgaard and find an open exit
            await tn.cmd('goto 3001', 1.0)
            zm = get_json('/zonemap?vnum=3001')
            byv = {r['vnum']: r for r in zm['rooms']}
            here = byv[3001]
            d, e = next((d, e) for d, e in here['exits'].items() if e['kind'] == 'open' and not e.get('door'))
            res, text, evs = await result_after(f'webmove 3001 {e["to"]}')
            check(res and res['ok'] and res['room'] == e['to'], f'legal webmove 3001 -> {e["to"]} ({d}) is ok')
            check('> webmove' not in text, 'no input echo for webmove')
            check(byv[e['to']]['name'] in text and 'Exits:' not in text, 'quiet move prints the room name, not the full look')
            maps = [m for m in evs if m.get('type') == 'map_data']
            check(len(maps) == 1, f'one map payload per move (got {len(maps)})')
            if maps:
                near = maps[-1].get('nearby') or []
                check(len(near) > 1, f'near payload lists {len(near)} nearby rooms')
                ids = [m.get('id') for r in near for m in r['mobs']]
                check(all(isinstance(i, int) for i in ids), f'every nearby mob has an id ({len(ids)} mobs)')

            res, _, _ = await result_after(f'webmove 3001 {e["to"]}')
            check(res and not res['ok'] and res['room'] == e['to'], 'out-of-step from is refused and reports the real room')
            res, _, _ = await result_after(f'webmove {e["to"]} 999999')
            check(res and not res['ok'] and "can't go" in res['reason'].lower(), f'no such exit refused: {res and res["reason"]!r}')

            # a door: find one in this zone, close it, try to walk through
            door_room = next(((r, dd, ee) for r in zm['rooms'] for dd, ee in r['exits'].items()
                              if ee.get('door') and not ee['door']['locked'] and dd in CARD), None)
            if door_room:
                r, dd, ee = door_room
                await tn.cmd(f'goto {r["vnum"]}', 1.0)
                await tn.cmd(f'close {dd}', 0.8)
                res, _, _ = await result_after(f'webmove {r["vnum"]} {ee["to"]}')
                check(res and not res['ok'] and 'closed' in res['reason'].lower(), f'closed door refused: {res and res["reason"]!r}')
                await tn.cmd(f'open {dd}', 0.8)
            else:
                print('skip closed-door check (no unlocked door in this zone)')

            await tn.cmd('goto 3001', 1.0)
            await tn.cmd('sleep', 0.6)
            res, _, _ = await result_after(f'webmove 3001 {e["to"]}')
            check(res and not res['ok'] and 'sleep' in res['reason'].lower(), f'sleeping refused: {res and res["reason"]!r}')
            await tn.cmd('wake', 0.6)
            await tn.cmd('stand', 0.4)
            pumper.cancel()
    tn.w.close()
    print('\n%d failure(s)' % len(failures))
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
