"""
Misthollow Admin Dashboard
Web-based admin interface on port 4002.

Local only by default (127.0.0.1; MISTHOLLOW_ADMIN_HOST overrides), and every API call needs
the key in lib/admin_key (made on first start) in an X-Admin-Key header: the page asks for it
once. Requests must name this machine in their Host header (no DNS rebinding), and a POST
from another site's page is refused.
"""

import hmac
import json
import os
import re
import secrets
import time
from aiohttp import web
from datetime import timedelta

KEY_FILE = os.path.join(os.path.dirname(__file__), '..', 'lib', 'admin_key')
LOG_FILES = [os.path.join(os.path.dirname(__file__), '..', 'server.log'),
             os.path.join(os.path.dirname(__file__), '..', 'log', 'mud.log')]

# secrets that can turn up in a log line: a map session token in a path, the hidden signals
_REDACT = [(re.compile(r'([?&](?:t|token)=)[^&\s\']+'), r'\1…'),
           (re.compile(r'(MAPSYNC:[^:\x07\s]+:)[^\x07\s]+'), r'\1…'),
           (re.compile(r'(RESUME:)[^\x07\s]+'), r'\1…')]


def _load_key() -> str:
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
        if key:
            return key
    except OSError:
        pass
    key = secrets.token_urlsafe(24)
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(key + '\n')
    return key


def redact(text: str) -> str:
    for pattern, sub in _REDACT:
        text = pattern.sub(sub, text)
    return text


class AdminDashboard:
    def __init__(self, world, port=4002, host=None):
        self.world = world
        self.port = port
        self.host = host or os.environ.get('MISTHOLLOW_ADMIN_HOST', '127.0.0.1')
        self.key = _load_key()
        # the names this dashboard answers to (Host header); more via MISTHOLLOW_ADMIN_HOSTS
        self.hosts = {'127.0.0.1', 'localhost', '::1', '[::1]', self.host}
        self.hosts |= {h.strip() for h in os.environ.get('MISTHOLLOW_ADMIN_HOSTS', '').split(',') if h.strip()}
        self.app = web.Application(middlewares=[self.guard])
        self.start_time = time.time()
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/', self.dashboard_page)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/players', self.api_players)
        self.app.router.add_get('/api/logs', self.api_logs)
        self.app.router.add_post('/api/broadcast', self.api_broadcast)

    @web.middleware
    async def guard(self, request, handler):
        raw = request.host or ''
        host = raw.split(']')[0] + ']' if raw.startswith('[') else raw.rsplit(':', 1)[0]
        if host not in self.hosts:
            return web.Response(status=421, text='Misdirected request')
        if request.path.startswith('/api/'):
            if not hmac.compare_digest(request.headers.get('X-Admin-Key', '').encode(), self.key.encode()):
                return web.json_response({'error': 'key required'}, status=401)
            if request.method == 'POST':
                origin = request.headers.get('Origin')
                if origin and origin.split('://', 1)[-1] != request.host:
                    return web.json_response({'error': 'cross-site request refused'}, status=403)
                if request.content_type != 'application/json':
                    return web.json_response({'error': 'JSON only'}, status=415)
        response = await handler(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        return response

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"Admin dashboard on http://{self.host}:{self.port} (key: lib/admin_key)")

    def get_uptime(self):
        delta = timedelta(seconds=int(time.time() - self.start_time))
        return str(delta)

    def _players(self):
        players = getattr(self.world, 'players', {}) or {}
        return list(players.values()) if isinstance(players, dict) else list(players)

    async def dashboard_page(self, request):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Misthollow Admin Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #16213e; border-radius: 10px; padding: 20px; }
        .card h2 { color: #00d4ff; font-size: 14px; text-transform: uppercase; margin-bottom: 15px; }
        .stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #0f3460; }
        .stat:last-child { border-bottom: none; }
        .stat-value { color: #00ff88; font-weight: bold; }
        .player-list { max-height: 300px; overflow-y: auto; }
        .player { padding: 10px; background: #0f3460; margin-bottom: 5px; border-radius: 5px; }
        .player-name { font-weight: bold; color: #00d4ff; }
        .player-info { font-size: 12px; color: #888; }
        .logs { background: #000; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
        .actions { display: flex; gap: 10px; flex-wrap: wrap; }
        button { background: #00d4ff; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #00a8cc; }
        input[type="text"], input[type="password"] { background: #0f3460; border: 1px solid #00d4ff; padding: 10px; border-radius: 5px; color: #fff; width: 100%; margin-bottom: 10px; }
        #keybox { max-width: 420px; margin: 40px auto; }
        #keybox p { color: #aaa; margin-bottom: 12px; font-size: 14px; }
        .hidden { display: none; }
        .muted { color: #888; }
    </style>
</head>
<body>
    <h1>🎮 Misthollow Admin Dashboard</h1>

    <div id="keybox" class="card hidden">
        <h2>Admin key</h2>
        <p>Paste the key from <b>lib/admin_key</b> on the server. This browser remembers it.</p>
        <input type="password" id="key-input" placeholder="admin key" autocomplete="off">
        <button id="key-save">Unlock</button>
    </div>

    <div id="board" class="grid hidden">
        <div class="card">
            <h2>Server Status</h2>
            <div id="stats">Loading...</div>
        </div>

        <div class="card">
            <h2>Online Players (<span id="player-count">0</span>)</h2>
            <div id="players" class="player-list">Loading...</div>
        </div>

        <div class="card">
            <h2>Quick Actions</h2>
            <div class="actions">
                <div style="width: 100%;">
                    <input type="text" id="broadcast-msg" placeholder="Broadcast message to all players...">
                    <button id="broadcast-btn">📢 Broadcast</button>
                </div>
                <button id="refresh-btn">🔄 Refresh</button>
                <button id="forget-btn">🔒 Forget key</button>
            </div>
        </div>

        <div class="card" style="grid-column: 1 / -1;">
            <h2>Recent Logs</h2>
            <div id="logs" class="logs">Loading...</div>
        </div>
    </div>

    <script>
        const KEY = 'mh_admin_key';
        const getKey = () => { try { return localStorage.getItem(KEY) || ''; } catch (_) { return ''; } };
        const $ = id => document.getElementById(id);
        function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
        function locked(on) { $('keybox').classList.toggle('hidden', !on); $('board').classList.toggle('hidden', on); }

        async function api(path, opts = {}) {
            const res = await fetch(path, { ...opts, headers: { ...(opts.headers || {}), 'X-Admin-Key': getKey() } });
            if (res.status === 401) { locked(true); throw new Error('locked'); }
            return res.json();
        }

        async function fetchStats() {
            const d = await api('/api/stats');
            const box = $('stats'); box.textContent = '';
            [['Status', '● Online'], ['Uptime', d.uptime], ['Players Online', d.players_online], ['Total Rooms', d.total_rooms],
             ['Total NPCs', d.total_npcs], ['Active Combats', d.active_combats], ['Memory', d.memory_mb + ' MB']].forEach(([k, v]) => {
                const row = el('div', 'stat'); row.append(el('span', '', k), el('span', 'stat-value', String(v))); box.append(row);
            });
        }

        async function fetchPlayers() {
            const data = await api('/api/players');
            $('player-count').textContent = data.length;
            const box = $('players'); box.textContent = '';
            if (!data.length) { box.append(el('div', 'muted', 'No players online')); return; }
            for (const p of data) {
                const row = el('div', 'player');
                row.append(el('div', 'player-name', p.name),
                           el('div', 'player-info', `Level ${p.level} ${p.class} | HP: ${p.hp}/${p.max_hp} | Room: ${p.room}`));
                box.append(row);
            }
        }

        async function fetchLogs() {
            const data = await api('/api/logs');
            $('logs').textContent = data.logs;
        }

        async function broadcast() {
            const msg = $('broadcast-msg').value;
            if (!msg) return;
            await api('/api/broadcast', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
            $('broadcast-msg').value = '';
            alert('Message broadcast!');
        }

        function refresh() {
            if (!getKey()) { locked(true); return; }
            locked(false);
            fetchStats().catch(() => {}); fetchPlayers().catch(() => {}); fetchLogs().catch(() => {});
        }

        $('key-save').addEventListener('click', () => {
            try { localStorage.setItem(KEY, $('key-input').value.trim()); } catch (_) {}
            $('key-input').value = '';
            refresh();
        });
        $('key-input').addEventListener('keydown', e => { if (e.key === 'Enter') $('key-save').click(); });
        $('broadcast-btn').addEventListener('click', broadcast);
        $('refresh-btn').addEventListener('click', refresh);
        $('forget-btn').addEventListener('click', () => { try { localStorage.removeItem(KEY); } catch (_) {} locked(true); });

        refresh();
        setInterval(() => { if (getKey()) refresh(); }, 10000);
    </script>
</body>
</html>'''
        return web.Response(text=html, content_type='text/html')

    async def api_stats(self, request):
        import resource
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024  # MB on macOS

        players = self._players()
        active_combats = sum(1 for p in players if getattr(p, 'fighting', None))

        return web.json_response({
            'uptime': self.get_uptime(),
            'players_online': len(players),
            'total_rooms': len(getattr(self.world, 'rooms', {}) or {}),
            'total_npcs': len(getattr(self.world, 'npcs', []) or []),
            'active_combats': active_combats,
            'memory_mb': round(mem, 1)
        })

    async def api_players(self, request):
        players = []
        for p in self._players():
            room = getattr(p, 'room', None)
            players.append({
                'name': getattr(p, 'name', '?'),
                'level': getattr(p, 'level', 0),
                'class': getattr(p, 'char_class', 'unknown'),
                'hp': getattr(p, 'hp', 0),
                'max_hp': getattr(p, 'max_hp', 0),
                'room': getattr(room, 'name', 'Unknown') if room else 'Unknown'
            })
        return web.json_response(players)

    async def api_logs(self, request):
        for log_file in LOG_FILES:
            try:
                with open(log_file, 'r', errors='replace') as f:
                    lines = f.readlines()
                return web.json_response({'logs': redact(''.join(lines[-50:]))})
            except OSError:
                continue
        return web.json_response({'logs': '(no logs available)'})

    async def api_broadcast(self, request):
        try:
            data = await request.json()
        except (ValueError, json.JSONDecodeError):
            return web.json_response({'error': 'bad JSON'}, status=400)
        message = str(data.get('message', '') if isinstance(data, dict) else '')
        message = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', message)[:400]
        if message:
            for player in self._players():
                try:
                    await player.send(f"\n[ADMIN BROADCAST] {message}\n")
                except Exception:
                    pass
        return web.json_response({'status': 'ok'})
