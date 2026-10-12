"""The admin dashboard: nothing under /api/ answers without the admin token.

Offline (no game server needed, only aiohttp): the dashboard's own app is served on a free
local port with a fake world and a known token.
    python3 tests/test_admin_dashboard.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402
import admin_dashboard  # noqa: E402
from config import Config  # noqa: E402

TOKEN = 'test-token-not-a-real-one'
failures = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        failures.append(what)


class FakePlayer:
    def __init__(self, name):
        self.name, self.level, self.hp, self.max_hp, self.room = name, 1, 10, 10, None
        self.heard = []

    async def send(self, message, newline=True):
        self.heard.append(message)


class FakeWorld:
    def __init__(self):
        # like World.players: lower-case name -> Player
        self.players = {'ann': FakePlayer('Ann'), 'bob': FakePlayer('Bob')}
        self.rooms, self.npcs = {}, []


def bearer(token):
    return {'Authorization': f'Bearer {token}'}


async def run():
    check(Config.ADMIN_DASHBOARD_HOST == '127.0.0.1' or 'MISTHOLLOW_ADMIN_HOST' in os.environ,
          'the dashboard is local only by default (Config.ADMIN_DASHBOARD_HOST)')

    world = FakeWorld()
    dash = admin_dashboard.AdminDashboard(world, key=TOKEN)
    check(dash.host == '127.0.0.1' or 'MISTHOLLOW_ADMIN_HOST' in os.environ, '…and binds 127.0.0.1 when given no host')
    heard = lambda: [m for p in world.players.values() for m in p.heard]  # noqa: E731

    async with TestClient(TestServer(dash.app)) as http:
        routes = [('GET', '/api/stats'), ('GET', '/api/players'), ('GET', '/api/logs'), ('POST', '/api/broadcast')]
        for method, path in routes:
            body = {'json': {'message': 'hello'}} if method == 'POST' else {}
            r = await http.request(method, path, **body)
            check(r.status == 401, f'{method} {path} without a token: 401')
            r = await http.request(method, path, headers=bearer('wrong'), **body)
            check(r.status == 403, f'{method} {path} with a wrong token: 403')
            r = await http.request(method, path, headers=bearer(TOKEN[:-1]), **body)
            check(r.status == 403, f'{method} {path} with part of the token: 403')
        check(heard() == [], 'no refused broadcast reached a player')

        r = await http.post('/api/broadcast', headers=bearer(TOKEN), json={'message': 'hello there'})
        check(r.status == 200, 'broadcast with the right token: 200')
        check(all(len(p.heard) == 1 and 'hello there' in p.heard[0] for p in world.players.values()),
              '…and it reaches every player (Player objects, not dict keys)')

        r = await http.get('/api/players', headers=bearer(TOKEN))
        check(r.status == 200 and sorted(p['name'] for p in await r.json()) == ['Ann', 'Bob'],
              'the player list answers with the right token')
        r = await http.get('/api/players', headers={'X-Admin-Key': TOKEN})
        check(r.status == 200, 'the older X-Admin-Key header still works')

        r = await http.post('/api/shutdown', headers=bearer(TOKEN), json={})
        check(r.status in (404, 405), 'there is no shutdown endpoint')
        r = await http.post('/api/broadcast', headers={**bearer(TOKEN), 'Origin': 'http://evil.example'}, json={'message': 'x'})
        check(r.status == 403, 'a POST from another site is refused even with the token')

    # no token configured: every API call is refused, whatever the caller sends
    world = FakeWorld()
    dash = admin_dashboard.AdminDashboard(world, key='')
    async with TestClient(TestServer(dash.app)) as http:
        for headers in ({}, bearer(''), bearer('anything'), {'X-Admin-Key': ''}):
            r = await http.get('/api/players', headers=headers)
            check(r.status in (401, 403), f'no token configured: GET /api/players refused ({headers or "no header"})')
            r = await http.post('/api/broadcast', headers=headers, json={'message': 'x'})
            check(r.status in (401, 403), f'no token configured: broadcast refused ({headers or "no header"})')
        check(all(p.heard == [] for p in world.players.values()), '…and nobody heard anything')

    # where the token comes from: the environment first, else lib/admin_key
    saved = os.environ.get('MISTHOLLOW_ADMIN_TOKEN')
    os.environ['MISTHOLLOW_ADMIN_TOKEN'] = ' from-env '
    try:
        check(admin_dashboard._load_key() == 'from-env', 'MISTHOLLOW_ADMIN_TOKEN is the token when set')
    finally:
        if saved is None:
            del os.environ['MISTHOLLOW_ADMIN_TOKEN']
        else:
            os.environ['MISTHOLLOW_ADMIN_TOKEN'] = saved


def test_admin_dashboard():  # for pytest
    asyncio.run(run())
    assert not failures, failures


if __name__ == '__main__':
    asyncio.run(run())
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)
