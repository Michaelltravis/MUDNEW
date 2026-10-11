"""Live test: /play is the only web client, and a web connection's text is not hard-wrapped.

Needs a running server (./run.sh) and the gauntlet admin account (tools/gauntlet/README.md).
    python3 tests/test_web_client.py
Checks: the retired 2D clients' URLs (/platformer, /2d, /iso) redirect to /play; /play loads
its shared scripts from /v/<commit>/shared/ and nothing from the old 2D folder; a telnet
connection's long lines are wrapped at 80 columns, and a connection that announced itself
as the web bridge (server.WEB_MARK, as web_client.py does) gets them whole.
"""
import asyncio
import http.client
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from server import WEB_MARK  # noqa: E402
from test_webmove import Telnet, check, failures, HOST, MAP, ANSI  # noqa: E402


def get(path):
    """(status, headers, body) of a GET on the map server, redirects not followed."""
    c = http.client.HTTPConnection(HOST, MAP, timeout=10)
    c.request('GET', path)
    r = c.getresponse()
    body = r.read()
    c.close()
    return r.status, dict(r.getheaders()), body


def pages():
    for path in ('/platformer', '/platformer?gauntlet=1', '/platformer/net.js', '/2d', '/iso', '/isometric'):
        status, headers, _ = get(path)
        check(status == 302 and headers.get('Location') == '/play', f'{path} redirects to /play ({status} {headers.get("Location")})')
    status, _, body = get('/play')
    page = body.decode(errors='ignore')
    check(status == 200, '/play loads')
    check('/platformer' not in page, '/play loads nothing from the old 2D folder')
    shared = re.findall(r'src="(/v/[^/]+/shared/[a-z-]+\.js)"', page)
    check(len(shared) == 5, f'/play loads its five shared scripts from /v/<commit>/shared/ ({len(shared)})')
    for src in shared:
        status, headers, body = get(src)
        check(status == 200 and 'javascript' in headers.get('Content-Type', '') and len(body) > 1000,
              f'{src} is served ({status}, {headers.get("Content-Type")}, {len(body)} bytes)')
    status, _, _ = get('/shared/../server.py')
    check(status == 404, 'no way out of the shared folder')


LONG = 'the mist ' * 16     # 144 characters: past any 80-column wrap


async def said(web):
    """What `say <LONG>` echoes back, as lines, on a telnet or a web connection."""
    tn = Telnet()
    tn.r, tn.w = await asyncio.open_connection(HOST, 4000)
    tn.buf = ''
    if web:
        tn.w.write(WEB_MARK + b'\r\n')
        await tn.w.drain()
    await tn.read(1.5)
    for line in ('gauntlet', 'gauntlet1', 'play Gauntlet'):
        await tn.cmd(line, 1.2)
    text = await tn.cmd('say ' + LONG.strip(), 1.2)
    await tn.cmd('quit', 0.8)
    tn.w.close()
    return [ANSI.sub('', l) for l in text.replace('\r', '').split('\n')]


async def wrapping():
    lines = await said(web=False)
    hit = [l for l in lines if 'the mist the mist' in l]
    check(hit and all(len(l) <= 80 for l in lines), f'telnet: a long line is wrapped at 80 columns ({[len(l) for l in hit]})')
    lines = await said(web=True)
    hit = [l for l in lines if 'the mist' in l]      # the command's echo, and what you said
    check(any(l.startswith('You say') for l in hit) and all(LONG.strip() in l for l in hit),
          f'web: the same line arrives whole ({[len(l) for l in hit]})')


async def main():
    pages()
    await wrapping()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
