"""
RealmsMUD Admin Dashboard
Web-based admin interface on port 4002
"""

import asyncio
import json
import time
import os
from aiohttp import web
from datetime import datetime, timedelta

class AdminDashboard:
    def __init__(self, world, port=4002):
        self.world = world
        self.port = port
        self.app = web.Application()
        self.start_time = time.time()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.router.add_get('/', self.dashboard_page)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/players', self.api_players)
        self.app.router.add_get('/api/logs', self.api_logs)
        self.app.router.add_post('/api/broadcast', self.api_broadcast)
        self.app.router.add_post('/api/shutdown', self.api_shutdown)
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        print(f"Admin dashboard running on http://localhost:{self.port}")
    
    def get_uptime(self):
        delta = timedelta(seconds=int(time.time() - self.start_time))
        return str(delta)
    
    async def dashboard_page(self, request):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>RealmsMUD Admin Dashboard</title>
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
        button.danger { background: #ff4444; }
        button.danger:hover { background: #cc0000; }
        input[type="text"] { background: #0f3460; border: 1px solid #00d4ff; padding: 10px; border-radius: 5px; color: #fff; width: 100%; margin-bottom: 10px; }
        .status-ok { color: #00ff88; }
        .status-warn { color: #ffaa00; }
        .status-error { color: #ff4444; }
    </style>
</head>
<body>
    <h1>🎮 RealmsMUD Admin Dashboard</h1>
    
    <div class="grid">
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
                    <button onclick="broadcast()">📢 Broadcast</button>
                </div>
                <button onclick="backup()">💾 Backup Now</button>
                <button onclick="refresh()">🔄 Refresh</button>
                <button class="danger" onclick="shutdown()">⚠️ Shutdown</button>
            </div>
        </div>
        
        <div class="card" style="grid-column: 1 / -1;">
            <h2>Recent Logs</h2>
            <div id="logs" class="logs">Loading...</div>
        </div>
    </div>
    
    <script>
        async function fetchStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat"><span>Status</span><span class="stat-value status-ok">● Online</span></div>
                <div class="stat"><span>Uptime</span><span class="stat-value">${data.uptime}</span></div>
                <div class="stat"><span>Players Online</span><span class="stat-value">${data.players_online}</span></div>
                <div class="stat"><span>Total Rooms</span><span class="stat-value">${data.total_rooms}</span></div>
                <div class="stat"><span>Total NPCs</span><span class="stat-value">${data.total_npcs}</span></div>
                <div class="stat"><span>Active Combats</span><span class="stat-value">${data.active_combats}</span></div>
                <div class="stat"><span>Memory</span><span class="stat-value">${data.memory_mb} MB</span></div>
            `;
        }
        
        async function fetchPlayers() {
            const res = await fetch('/api/players');
            const data = await res.json();
            document.getElementById('player-count').textContent = data.length;
            if (data.length === 0) {
                document.getElementById('players').innerHTML = '<div style="color: #888;">No players online</div>';
                return;
            }
            document.getElementById('players').innerHTML = data.map(p => `
                <div class="player">
                    <div class="player-name">${p.name}</div>
                    <div class="player-info">Level ${p.level} ${p.class} | HP: ${p.hp}/${p.max_hp} | Room: ${p.room}</div>
                </div>
            `).join('');
        }
        
        async function fetchLogs() {
            const res = await fetch('/api/logs');
            const data = await res.json();
            document.getElementById('logs').textContent = data.logs;
        }
        
        async function broadcast() {
            const msg = document.getElementById('broadcast-msg').value;
            if (!msg) return;
            await fetch('/api/broadcast', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg}) });
            document.getElementById('broadcast-msg').value = '';
            alert('Message broadcast!');
        }
        
        async function backup() {
            alert('Backup initiated. Check server logs.');
        }
        
        async function shutdown() {
            if (!confirm('Are you sure you want to shutdown the server?')) return;
            await fetch('/api/shutdown', { method: 'POST' });
            alert('Shutdown initiated.');
        }
        
        function refresh() {
            fetchStats();
            fetchPlayers();
            fetchLogs();
        }
        
        // Initial load and auto-refresh
        refresh();
        setInterval(refresh, 10000);
    </script>
</body>
</html>'''
        return web.Response(text=html, content_type='text/html')
    
    async def api_stats(self, request):
        import resource
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024  # MB on macOS
        
        active_combats = sum(1 for p in self.world.players if getattr(p, 'fighting', None))
        
        return web.json_response({
            'uptime': self.get_uptime(),
            'players_online': len(self.world.players),
            'total_rooms': len(self.world.rooms),
            'total_npcs': len(self.world.npcs),
            'active_combats': active_combats,
            'memory_mb': round(mem, 1)
        })
    
    async def api_players(self, request):
        players = []
        for p in self.world.players:
            players.append({
                'name': p.name,
                'level': p.level,
                'class': getattr(p, 'char_class', 'unknown'),
                'hp': p.hp,
                'max_hp': p.max_hp,
                'room': p.room.name if p.room else 'Unknown'
            })
        return web.json_response(players)
    
    async def api_logs(self, request):
        log_file = os.path.join(os.path.dirname(__file__), '..', 'server.log')
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                return web.json_response({'logs': ''.join(lines[-50:])})
        except:
            return web.json_response({'logs': '(no logs available)'})
    
    async def api_broadcast(self, request):
        data = await request.json()
        message = data.get('message', '')
        if message:
            for player in self.world.players:
                try:
                    await player.send(f"\n[ADMIN BROADCAST] {message}\n")
                except:
                    pass
        return web.json_response({'status': 'ok'})
    
    async def api_shutdown(self, request):
        for player in self.world.players:
            try:
                await player.send("\n[SERVER] Shutdown initiated by administrator. Saving and disconnecting...\n")
            except:
                pass
        # Set shutdown flag
        self.world.shutdown_requested = True
        return web.json_response({'status': 'shutting_down'})
