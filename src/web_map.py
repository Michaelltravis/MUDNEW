"""
Web map server for RealmsMUD.
Serves a lightweight HTML/JS interface and a minimal WebSocket for live updates.
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
from typing import Optional
from urllib.parse import parse_qs, urlparse

from map_system import build_map_payload

logger = logging.getLogger('RealmsMUD.WebMap')


class WebMapClient:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.player_name: Optional[str] = None
        self.mode: str = 'full'


class WebMapServer:
    def __init__(self, world, config):
        self.world = world
        self.config = config
        self.server = None
        self.clients = set()

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.config.MAP_HOST, self.config.MAP_PORT, reuse_address=True)
        logger.info(f"Web map server listening on {self.config.MAP_HOST}:{self.config.MAP_PORT}")
        # Start background ping task to detect dead connections
        self._ping_task = asyncio.create_task(self._ping_clients_loop())

    async def _ping_clients_loop(self):
        """Periodically ping all WebSocket clients to detect dead connections."""
        while True:
            await asyncio.sleep(30)  # Ping every 30 seconds
            dead_clients = []
            for client in list(self.clients):
                success = await self._ws_ping(client.writer)
                if not success:
                    dead_clients.append(client)
            for client in dead_clients:
                self.clients.discard(client)
                logger.info(f"Removed stale WebSocket client for '{client.player_name}' (ping failed)")
                try:
                    client.writer.close()
                except Exception:
                    pass

    async def _ws_ping(self, writer):
        """Send a WebSocket ping frame. Returns True on success."""
        try:
            # Opcode 0x9 is ping, 0 length
            writer.write(bytes([0x89, 0x00]))
            await writer.drain()
            return True
        except Exception:
            return False

    async def stop(self):
        # Cancel ping task
        if hasattr(self, '_ping_task') and self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        # Close all clients
        for client in list(self.clients):
            try:
                client.writer.close()
            except Exception:
                pass
        self.clients.clear()

    async def notify_player(self, player):
        matching_clients = 0
        dead_clients = []
        client_names = [c.player_name for c in self.clients if c.player_name]
        logger.info(f"notify_player called for '{player.name}', connected clients: {client_names}")
        for client in list(self.clients):
            if not client.player_name:
                continue
            if client.player_name.lower() != player.name.lower():
                continue
            matching_clients += 1
            try:
                payload = build_map_payload(player, mode=client.mode)
                logger.info(f"notify_player: sending {len(payload.get('rooms', []))} rooms to '{client.player_name}'")
                success = await self._ws_send(client.writer, json.dumps(payload))
                if not success:
                    dead_clients.append(client)
                    logger.warning(f"notify_player: send failed for '{client.player_name}'")
                else:
                    logger.info(f"notify_player: send SUCCESS for '{client.player_name}'")
            except Exception as e:
                logger.error(f"notify_player exception for '{client.player_name}': {e}")
                dead_clients.append(client)
        # Clean up dead clients
        for client in dead_clients:
            self.clients.discard(client)
            logger.info(f"Removed dead WebSocket client for '{client.player_name}'")
        if matching_clients == 0:
            logger.warning(f"notify_player: NO connected clients for '{player.name}' (total clients: {len(self.clients)}, names: {client_names})")

    async def _handle_client(self, reader, writer):
        try:
            request = await reader.readline()
            if not request:
                writer.close()
                return
            request_line = request.decode(errors='ignore').strip()
            parts = request_line.split(' ', 2)
            if len(parts) < 2:
                writer.close()
                return
            method = parts[0]
            path = parts[1]

            headers = {}
            while True:
                line = await reader.readline()
                if not line:
                    break
                line = line.decode(errors='ignore').strip()
                if line == '':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            if headers.get('upgrade', '').lower() == 'websocket':
                await self._handle_websocket(reader, writer, headers)
                return

            if method != 'GET':
                await self._http_response(writer, 405, 'Method Not Allowed', 'Method Not Allowed')
                return

            if path.startswith('/map.js'):
                await self._http_response(writer, 200, 'OK', self._js(), content_type='application/javascript')
            elif path.startswith('/map.css'):
                await self._http_response(writer, 200, 'OK', self._css(), content_type='text/css')
            elif path.startswith('/state'):
                parsed = urlparse(path)
                query = parse_qs(parsed.query)
                player_name = (query.get('player') or [''])[0]
                logger.info(f"HTTP /state request: player='{player_name}'")
                if not player_name:
                    await self._http_response(writer, 400, 'Bad Request', 'Missing player parameter')
                    return
                player = self.world.players.get(player_name.lower())
                if not player:
                    logger.warning(f"/state: Player '{player_name}' not found (online: {list(self.world.players.keys())})")
                    await self._http_response(writer, 404, 'Not Found', 'Player not found')
                    return
                # Ensure current room is in explored_rooms
                if player.room and hasattr(player, 'explored_rooms'):
                    if player.room.vnum not in player.explored_rooms:
                        player.explored_rooms.add(player.room.vnum)
                payload = build_map_payload(player, mode='full')
                logger.info(f"/state: returning {len(payload.get('rooms', []))} rooms for '{player_name}'")
                await self._http_response(writer, 200, 'OK', json.dumps(payload), content_type='application/json')
            elif path.startswith('/sprites/'):
                # Serve sprite images
                sprite_file = path.replace('/sprites/', '')
                sprite_path = os.path.join(os.path.dirname(__file__), 'web_isometric', 'sprites', sprite_file)
                try:
                    with open(sprite_path, 'rb') as f:
                        data = f.read()
                    ext = sprite_file.rsplit('.', 1)[-1].lower()
                    ct = {'png': 'image/png', 'jpg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp'}.get(ext, 'image/png')
                    writer.write(f"HTTP/1.1 200 OK\r\nContent-Type: {ct}\r\nContent-Length: {len(data)}\r\nAccess-Control-Allow-Origin: *\r\n\r\n".encode())
                    writer.write(data)
                    await writer.drain()
                    return
                except FileNotFoundError:
                    await self._http_response(writer, 404, 'Not Found', 'Sprite not found')
            elif path.startswith('/iso') or path.startswith('/isometric'):
                # Serve the isometric 3D view
                iso_path = os.path.join(os.path.dirname(__file__), 'web_isometric', 'index.html')
                try:
                    with open(iso_path, 'r', encoding='utf-8') as f:
                        iso_html = f.read()
                    await self._http_response(writer, 200, 'OK', iso_html, content_type='text/html')
                except FileNotFoundError:
                    await self._http_response(writer, 404, 'Not Found', 'Isometric view not found')
            else:
                await self._http_response(writer, 200, 'OK', self._html(), content_type='text/html')

        except Exception as e:
            logger.error(f"Web map client error: {e}")
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def _http_response(self, writer, status_code, status_text, body, content_type='text/plain'):
        data = body.encode('utf-8')
        headers = [
            f"HTTP/1.1 {status_code} {status_text}",
            f"Content-Type: {content_type}; charset=utf-8",
            f"Content-Length: {len(data)}",
            "Cache-Control: no-store, no-cache, must-revalidate, max-age=0",
            "Pragma: no-cache",
            "Connection: close",
            "Access-Control-Allow-Origin: *",
            "Access-Control-Allow-Methods: GET, POST, OPTIONS",
            "Access-Control-Allow-Headers: Content-Type",
            "X-Frame-Options: ALLOWALL",
            "",
            "",
        ]
        writer.write("\r\n".join(headers).encode('utf-8') + data)
        await writer.drain()

    async def _handle_websocket(self, reader, writer, headers):
        key = headers.get('sec-websocket-key')
        if not key:
            writer.close()
            return
        accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()

        client = WebMapClient(reader, writer)
        self.clients.add(client)

        try:
            while True:
                message = await self._ws_read(reader)
                if message is None:
                    logger.info(f"WebSocket message is None, closing connection for client")
                    break
                if message == '':
                    # Control frame (ping/pong), continue waiting
                    continue
                try:
                    payload = json.loads(message)
                except Exception as e:
                    logger.debug(f"Failed to parse WebSocket message: {e}")
                    continue

                if payload.get('type') == 'subscribe':
                    client.player_name = payload.get('player')
                    client.mode = payload.get('mode', 'full')
                    logger.info(f"WebSocket subscribe: player='{client.player_name}' mode='{client.mode}'")
                    player = None
                    if client.player_name:
                        player = self.world.players.get(client.player_name.lower())
                    if player:
                        # Ensure current room is in explored_rooms for initial map
                        if player.room and hasattr(player, 'explored_rooms'):
                            if player.room.vnum not in player.explored_rooms:
                                player.explored_rooms.add(player.room.vnum)
                                logger.info(f"Added current room {player.room.vnum} to explored_rooms")
                        map_payload = build_map_payload(player, mode=client.mode)
                        logger.info(f"Sending initial map: {len(map_payload.get('rooms', []))} rooms")
                        await self._ws_send(writer, json.dumps(map_payload))
                    else:
                        logger.warning(f"Player '{client.player_name}' not found in world.players (online: {list(self.world.players.keys())})")
        finally:
            self.clients.discard(client)
            try:
                writer.close()
            except Exception:
                pass

    async def _ws_read(self, reader):
        """Read a WebSocket frame. Returns message text, empty string for control frames, or None on close/error."""
        try:
            header = await reader.readexactly(2)
            if not header:
                logger.info("WebSocket: empty header received")
                return None
            b1, b2 = header[0], header[1]
            opcode = b1 & 0x0F
            masked = b2 & 0x80
            length = b2 & 0x7F
            
            logger.debug(f"WebSocket frame: opcode={opcode}, masked={masked}, length={length}")
            
            # Handle close frame
            if opcode == 0x8:
                logger.info("WebSocket close frame received from client")
                return None
            
            if length == 126:
                length = int.from_bytes(await reader.readexactly(2), 'big')
            elif length == 127:
                length = int.from_bytes(await reader.readexactly(8), 'big')
            
            mask = b''
            if masked:
                mask = await reader.readexactly(4)
            
            data = await reader.readexactly(length) if length > 0 else b''
            if masked and data:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            
            # Handle ping - respond with pong
            if opcode == 0x9:
                logger.debug("WebSocket ping received, sending pong")
                return ''  # Return empty string to continue loop
            
            # Handle pong - just ignore
            if opcode == 0xA:
                logger.debug("WebSocket pong received")
                return ''  # Return empty string to continue loop
            
            return data.decode('utf-8', errors='ignore')
        except asyncio.IncompleteReadError as e:
            logger.info(f"WebSocket connection closed (incomplete read): {e}")
            return None
        except (ConnectionResetError, BrokenPipeError, ConnectionError, OSError) as e:
            logger.info(f"WebSocket read error: {e}")
            return None
        except Exception as e:
            logger.warning(f"WebSocket read unexpected error: {e}")
            return None

    async def _ws_send(self, writer, text):
        """Send a WebSocket text frame. Returns True on success, False on failure."""
        try:
            payload = text.encode('utf-8')
            length = len(payload)
            if length < 126:
                header = bytes([0x81, length])
            elif length < (1 << 16):
                header = bytes([0x81, 126]) + length.to_bytes(2, 'big')
            else:
                header = bytes([0x81, 127]) + length.to_bytes(8, 'big')
            writer.write(header + payload)
            await writer.drain()
            return True
        except (ConnectionResetError, BrokenPipeError, ConnectionError, OSError) as e:
            logger.debug(f"WebSocket send failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"WebSocket send unexpected error: {e}")
            return False

    def _html(self):
        return """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>RealmsMUD Map</title>
  <link rel=\"stylesheet\" href=\"/map.css\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">
</head>
<body>
  <div id=\"app\">
    <header>
      <h1>⚔️ RealmsMUD</h1>
      <div class=\"controls\">
        <label>Level <select id=\"zSelect\"></select></label>
        <label>Zoom <input id=\"zoom\" type=\"range\" min=\"0.3\" max=\"3\" step=\"0.1\" value=\"1\" /></label>
        <label><input id=\"iconMode\" type=\"checkbox\" checked /> Icons</label>
        <label><input id=\"fogMode\" type=\"checkbox\" checked /> Fog</label>
        <label><input id=\"zoneMode\" type=\"checkbox\" checked /> Zones</label>
        <label><input id=\"minimapToggle\" type=\"checkbox\" checked /> Minimap</label>
      </div>
      <div class=\"status-bar\">
        <span id=\"wsStatus\" class=\"status connecting\">WS: connecting</span>
        <span id=\"playerWarning\" class=\"warning hidden\">⚠️ Add ?player=Name to URL</span>
      </div>
    </header>
    <div class=\"content\">
      <canvas id=\"mapCanvas\"></canvas>
      <aside>
        <div id=\"zoneInfo\" class=\"zone-info\"></div>
        <h2>📍 Room Details</h2>
        <div id=\"roomDetails\">Click a room to see details.<br/><br/><em style=\"color:#6b7280\">Right-click to set destination and see path.</em></div>
        <div id=\"pathInfo\" class=\"path-info hidden\"></div>
        <div class=\"legend\">
          <h3>Legend</h3>
          <div class=\"legend-grid\">
            <span>🏛️ City</span><span>🏠 Indoor</span>
            <span>🌲 Forest</span><span>🌊 Water</span>
            <span>⛰️ Mountain</span><span>🕯️ Dungeon</span>
            <span>🛒 Shop</span><span>⭐ Quest</span>
            <span>👹 Boss</span><span>💀 Danger</span>
            <span>🌀 Portal</span><span></span>
          </div>
        </div>
        <div id=\"zoneFilter\" class=\"zone-filter\">
          <h3>🗺️ Zone Filter</h3>
          <div id=\"zoneFilterList\"></div>
        </div>
        <div id=\"zoneList\" class=\"zone-list\"></div>
      </aside>
    </div>
    <canvas id=\"minimap\"></canvas>
    <canvas id=\"zoneOverview\"></canvas>
    <div id=\"debugPanel\" class=\"debug-panel hidden\">
      <div><span class=\"label\">WS</span> <span id=\"debugWs\">-</span></div>
      <div><span class=\"label\">Poll</span> <span id=\"debugPoll\">-</span></div>
      <div><span class=\"label\">Payload</span> <span id=\"debugPayload\">-</span></div>
      <div><span class=\"label\">Error</span> <span id=\"debugError\">-</span></div>
    </div>
  </div>
  <script src=\"/map.js\"></script>
</body>
</html>"""

    def _css(self):
        return """
*{box-sizing:border-box}
body{margin:0;background:#0a0e14;color:#e6edf3;font-family:'Inter',system-ui,-apple-system,sans-serif}
#app{display:flex;flex-direction:column;min-height:100vh}
header{padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.08);background:linear-gradient(180deg,#12171f 0%,#0d1117 100%);display:flex;flex-wrap:wrap;align-items:center;gap:18px;backdrop-filter:blur(8px)}
header h1{margin:0;font-size:24px;font-weight:700;letter-spacing:-0.5px}
header .controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
header label{font-size:12px;opacity:.75;font-weight:500;display:flex;align-items:center;gap:4px;cursor:pointer}
header input[type=checkbox]{width:16px;height:16px;accent-color:#6366f1;cursor:pointer}
header select,header input[type=range]{background:#1a1f2e;border:1px solid #2d3748;border-radius:6px;color:#e6edf3;padding:4px 8px;cursor:pointer;transition:border-color 0.2s,box-shadow 0.2s}
header select:hover,header input:hover{border-color:#6366f1}
header select:focus,header input:focus{outline:none;border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,0.2)}
.status-bar{margin-left:auto;display:flex;gap:12px;align-items:center;font-size:11px;font-weight:500}
.status{padding:5px 12px;border-radius:999px;border:1px solid;text-transform:uppercase;letter-spacing:.6px;font-weight:600;transition:all 0.3s}
.status.connecting{color:#f0b429;border-color:#8b6b1a;background:rgba(240,180,41,0.1);animation:pulse 2s infinite}
.status.connected{color:#4ade80;border-color:#22c55e;background:rgba(74,222,128,0.1)}
.status.disconnected{color:#f87171;border-color:#ef4444;background:rgba(248,113,113,0.1)}
.status.polling{color:#60a5fa;border-color:#3b82f6;background:rgba(96,165,250,0.1)}
.warning{color:#fca5a5;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);padding:6px 12px;border-radius:8px;font-size:12px}
.hidden{display:none}
#mapCanvas{flex:1;min-height:65vh;width:100%;background:radial-gradient(ellipse at center,#0f1419 0%,#050709 100%);border:1px solid rgba(255,255,255,0.06);border-radius:12px;cursor:grab}
#mapCanvas:active{cursor:grabbing}
#minimap{position:fixed;right:18px;bottom:18px;width:220px;height:220px;border:1px solid rgba(255,255,255,0.1);background:rgba(10,14,20,0.95);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.5);backdrop-filter:blur(12px)}
#minimap.hidden{display:none}
.content{display:flex;gap:14px;padding:14px;flex:1}
aside{width:320px;background:linear-gradient(180deg,#12171f 0%,#0f1318 100%);border:1px solid rgba(255,255,255,0.06);padding:16px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.3);display:flex;flex-direction:column;gap:12px;max-height:calc(100vh - 120px);overflow-y:auto}
aside h2{margin:0;font-size:15px;font-weight:600;color:#a5b4fc}
aside h3{font-size:12px;color:#6b7280;margin:8px 0 6px 0;text-transform:uppercase;letter-spacing:0.5px}
.zone-info{background:linear-gradient(135deg,rgba(99,102,241,0.15) 0%,rgba(139,92,246,0.1) 100%);border:1px solid rgba(99,102,241,0.3);border-radius:10px;padding:12px;font-size:13px}
.zone-info .zone-name{font-weight:600;font-size:15px;margin-bottom:4px}
.zone-info .zone-stats{color:#8b949e;font-size:12px}
.path-info{background:linear-gradient(135deg,rgba(34,197,94,0.15) 0%,rgba(16,185,129,0.1) 100%);border:1px solid rgba(34,197,94,0.3);border-radius:10px;padding:12px;font-size:13px}
.path-info .path-title{font-weight:600;color:#4ade80;margin-bottom:4px}
.path-info .path-steps{color:#8b949e;font-size:12px}
#roomDetails{background:rgba(0,0,0,0.25);border-radius:10px;padding:14px;font-size:13px;line-height:1.7}
.legend{background:rgba(0,0,0,0.15);border-radius:10px;padding:12px}
.legend-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12px}
.legend-grid span{display:flex;align-items:center;gap:4px}
.zone-list{background:rgba(0,0,0,0.15);border-radius:10px;padding:12px}
.zone-list h3{margin-top:0}
.zone-item{display:flex;align-items:center;gap:8px;padding:6px 0;font-size:12px;border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer;transition:background 0.15s;padding:6px 8px;border-radius:6px;margin:1px 0}
.zone-item:hover{background:rgba(255,255,255,0.06)}
.zone-item.active{background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.4)}
.zone-item:last-child{border-bottom:none}
.zone-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}
.zone-filter{background:rgba(0,0,0,0.15);border-radius:10px;padding:12px}
.zone-filter h3{margin-top:0}
.zone-filter-item{display:flex;align-items:center;gap:8px;padding:5px 8px;font-size:12px;cursor:pointer;border-radius:6px;transition:background 0.15s;margin:2px 0}
.zone-filter-item:hover{background:rgba(255,255,255,0.06)}
.zone-filter-item.active{background:rgba(99,102,241,0.25);border:1px solid rgba(99,102,241,0.4)}
.zone-filter-item .zf-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.zone-filter-item .zf-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.zone-filter-item .zf-count{color:#6b7280;font-size:11px}
#zoneOverview{position:fixed;left:18px;bottom:18px;width:140px;height:140px;border:1px solid rgba(255,255,255,0.1);background:rgba(10,14,20,0.95);border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.5);backdrop-filter:blur(12px);cursor:pointer;z-index:10}
#zoneOverview.hidden{display:none}
#tooltip{position:fixed;background:rgba(12,15,20,0.98);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:12px 16px;font-size:13px;pointer-events:none;z-index:1000;box-shadow:0 12px 40px rgba(0,0,0,0.6);backdrop-filter:blur(16px);max-width:280px;opacity:0;transition:opacity 0.2s}
#tooltip.visible{opacity:1}
#tooltip .tt-icon{font-size:24px;margin-bottom:6px}
#tooltip .tt-name{font-weight:600;color:#e6edf3;font-size:14px;margin-bottom:6px}
#tooltip .tt-zone{color:#a5b4fc;font-size:11px;margin-bottom:6px}
#tooltip .tt-info{color:#8b949e;font-size:12px;line-height:1.5}
.debug-panel{position:fixed;left:18px;bottom:18px;background:rgba(10,14,20,0.95);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 14px;font-size:11px;min-width:180px;box-shadow:0 4px 20px rgba(0,0,0,0.4);backdrop-filter:blur(12px)}
.debug-panel .label{display:inline-block;width:56px;color:#6b7280;text-transform:uppercase;letter-spacing:.4px;font-weight:500}
.debug-panel div{margin-bottom:5px}
.debug-panel div:last-child{margin-bottom:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.6}}
@keyframes reveal{0%{transform:scale(0);opacity:0}100%{transform:scale(1);opacity:1}}
@media(max-width:900px){header{flex-direction:column;align-items:flex-start}.status-bar{margin-left:0}.content{flex-direction:column}aside{width:100%;max-height:none}#minimap{position:static;width:100%;height:180px;margin:8px 0;border-radius:12px}}
"""

    def _js(self):
        return r"""(() => {
  const canvas = document.getElementById('mapCanvas');
  const ctx = canvas.getContext('2d');
  const minimap = document.getElementById('minimap');
  const miniCtx = minimap.getContext('2d');
  const zoneOverview = document.getElementById('zoneOverview');
  const zoCtx = zoneOverview.getContext('2d');
  const zSelect = document.getElementById('zSelect');
  const zoomControl = document.getElementById('zoom');
  const minimapToggle = document.getElementById('minimapToggle');
  const iconMode = document.getElementById('iconMode');
  const fogMode = document.getElementById('fogMode');
  const zoneMode = document.getElementById('zoneMode');
  const roomDetails = document.getElementById('roomDetails');
  const pathInfo = document.getElementById('pathInfo');
  const zoneInfo = document.getElementById('zoneInfo');
  const zoneList = document.getElementById('zoneList');
  const zoneFilterList = document.getElementById('zoneFilterList');
  const wsStatus = document.getElementById('wsStatus');
  const playerWarning = document.getElementById('playerWarning');
  const debugPanel = document.getElementById('debugPanel');
  const debugWs = document.getElementById('debugWs');
  const debugPoll = document.getElementById('debugPoll');
  const debugPayload = document.getElementById('debugPayload');
  const debugError = document.getElementById('debugError');

  // Create tooltip
  const tooltip = document.createElement('div');
  tooltip.id = 'tooltip';
  tooltip.innerHTML = '<div class="tt-icon"></div><div class="tt-name"></div><div class="tt-zone"></div><div class="tt-info"></div>';
  document.body.appendChild(tooltip);

  let state = { rooms: [], frontier: [], zones: [], player: null };
  let pan = { x: 0, y: 0 };
  let targetPan = { x: 0, y: 0 };
  let zoom = 1;
  let targetZoom = 1;
  let selectedZ = 0;
  let activeZone = null; // null = all zones, number = specific zone id
  let revealed = new Map();
  let hoveredRoom = null;
  let selectedRoom = null;
  let pathRooms = new Set();
  let pulsePhase = 0;
  let useIcons = true;
  let showFog = true;
  let showZones = true;
  let portalRooms = new Set(); // vnums of rooms that connect to other zones (shown as portals when filtering)
  let crossZoneExits = []; // {fromVnum, toVnum, fromZone, toZone, dir} for portal markers

  const ROOM_SIZE = 36;
  const ROOM_SPACING = 56;
  const ROOM_RADIUS = 8;

  const getZoneColor = (zoneId) => {
    const zone = state.zones.find(z => z.id === zoneId);
    return zone ? zone.color : '#6366f1';
  };
  const getZoneName = (zoneId) => {
    const zone = state.zones.find(z => z.id === zoneId);
    return zone ? zone.name : 'Zone ' + zoneId;
  };

  const dirOffsets = {
    north: [0, -1, 0], south: [0, 1, 0],
    east: [1, 0, 0], west: [-1, 0, 0],
    up: [0, 0, 1], down: [0, 0, -1]
  };

  const stamp = () => new Date().toLocaleTimeString();
  const setDebug = (el, v) => { if (el) el.textContent = v; };
  const setDebugError = (v) => setDebug(debugError, v || '-');
  const markPayload = () => setDebug(debugPayload, stamp());
  const lerp = (a, b, t) => a + (b - a) * t;

  const setWsStatus = (st, label) => {
    wsStatus.classList.remove('connecting', 'connected', 'disconnected', 'polling');
    wsStatus.classList.add(st);
    wsStatus.textContent = 'WS: ' + label;
    setDebug(debugWs, label);
  };

  // Build cross-zone exit index
  const buildCrossZoneIndex = () => {
    crossZoneExits = [];
    portalRooms = new Set();
    const roomMap = new Map();
    const coordMap = new Map();
    state.rooms.forEach(r => { roomMap.set(r.vnum, r); coordMap.set(r.x + ',' + r.y + ',' + r.z, r); });
    state.rooms.forEach(room => {
      (room.exits || []).forEach(dir => {
        const off = dirOffsets[dir];
        if (!off) return;
        const target = coordMap.get((room.x + off[0]) + ',' + (room.y + off[1]) + ',' + (room.z + off[2]));
        if (target && target.zone !== room.zone) {
          crossZoneExits.push({ fromVnum: room.vnum, toVnum: target.vnum, fromZone: room.zone, toZone: target.zone, dir });
          portalRooms.add(room.vnum);
          portalRooms.add(target.vnum);
        }
      });
    });
  };

  // Get visible rooms based on zone filter
  const getVisibleRooms = () => {
    if (activeZone === null) return state.rooms;
    // Show rooms in active zone + portal rooms from adjacent zones
    const adjacentPortalVnums = new Set();
    crossZoneExits.forEach(cx => {
      if (cx.fromZone === activeZone) adjacentPortalVnums.add(cx.toVnum);
      if (cx.toZone === activeZone) adjacentPortalVnums.add(cx.fromVnum);
    });
    return state.rooms.filter(r => r.zone === activeZone || adjacentPortalVnums.has(r.vnum));
  };

  const setActiveZone = (zoneId) => {
    activeZone = zoneId;
    // Re-center on zone centroid
    const zoneRooms = zoneId === null ? state.rooms : state.rooms.filter(r => r.zone === zoneId);
    if (zoneRooms.length > 0) {
      const cx = zoneRooms.reduce((s, r) => s + r.x, 0) / zoneRooms.length;
      const cy = zoneRooms.reduce((s, r) => s + r.y, 0) / zoneRooms.length;
      targetPan.x = canvas.clientWidth / 2 - (cx * ROOM_SPACING * zoom);
      targetPan.y = canvas.clientHeight / 2 - (cy * ROOM_SPACING * zoom);
    }
    updateUI();
    renderZoneOverview();
  };

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    minimap.width = minimap.clientWidth * dpr;
    minimap.height = minimap.clientHeight * dpr;
    miniCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    zoneOverview.width = zoneOverview.clientWidth * dpr;
    zoneOverview.height = zoneOverview.clientHeight * dpr;
    zoCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resize);
  setTimeout(resize, 0);

  zoomControl.addEventListener('input', (e) => { targetZoom = parseFloat(e.target.value); });
  minimapToggle.addEventListener('change', (e) => { minimap.classList.toggle('hidden', !e.target.checked); zoneOverview.classList.toggle('hidden', !e.target.checked); });
  iconMode.addEventListener('change', (e) => { useIcons = e.target.checked; });
  fogMode.addEventListener('change', (e) => { showFog = e.target.checked; });
  zoneMode.addEventListener('change', (e) => { showZones = e.target.checked; });

  let dragging = false;
  let last = { x: 0, y: 0 };
  canvas.addEventListener('mousedown', (e) => { dragging = true; last = { x: e.clientX, y: e.clientY }; });
  window.addEventListener('mouseup', () => dragging = false);

  const hitTest = (mx, my) => {
    const visible = getVisibleRooms().filter(r => r.z === selectedZ);
    return visible.find(r =>
      Math.abs(r.x * ROOM_SPACING - mx) < ROOM_SIZE/2 + 6 &&
      Math.abs(r.y * ROOM_SPACING - my) < ROOM_SIZE/2 + 6);
  };

  window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - pan.x) / zoom;
    const my = (e.clientY - rect.top - pan.y) / zoom;
    const hit = hitTest(mx, my);

    if (hit && !dragging) {
      hoveredRoom = hit;
      tooltip.querySelector('.tt-icon').textContent = hit.icon || '';
      tooltip.querySelector('.tt-name').textContent = hit.name;
      tooltip.querySelector('.tt-zone').textContent = '\u{1F4CD} ' + (hit.zoneName || 'Unknown Zone');
      const isPortal = activeZone !== null && hit.zone !== activeZone;
      tooltip.querySelector('.tt-info').innerHTML =
        (isPortal ? '<b style="color:#c084fc">\u{1F300} Portal from ' + getZoneName(hit.zone) + '</b><br>' : '') +
        '<b>Sector:</b> ' + hit.sector + '<br><b>Exits:</b> ' + hit.exits.join(', ') +
        '<br><b>VNUM:</b> ' + hit.vnum;
      tooltip.style.left = Math.min(e.clientX + 16, window.innerWidth - 300) + 'px';
      tooltip.style.top = Math.min(e.clientY + 16, window.innerHeight - 150) + 'px';
      tooltip.classList.add('visible');
    } else {
      hoveredRoom = null;
      tooltip.classList.remove('visible');
    }
    if (!dragging) return;
    targetPan.x += e.clientX - last.x;
    targetPan.y += e.clientY - last.y;
    last = { x: e.clientX, y: e.clientY };
  });

  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - pan.x) / zoom;
    const my = (e.clientY - rect.top - pan.y) / zoom;
    const hit = hitTest(mx, my);
    if (hit) {
      selectedRoom = hit;
      const isPortal = activeZone !== null && hit.zone !== activeZone;
      roomDetails.innerHTML =
        '<div style="font-size:24px;margin-bottom:8px">' + (isPortal ? '\u{1F300}' : (hit.icon || '\u{1F4CD}')) + '</div>' +
        '<strong style="font-size:15px">' + hit.name + '</strong><br/>' +
        '<span style="color:#a5b4fc">' + (hit.zoneName || '') + '</span>' +
        (isPortal ? '<br/><span style="color:#c084fc;font-size:12px">Portal entry — click to switch zone</span>' : '') +
        '<br/><br/>' +
        '<span style="color:#6b7280">Sector:</span> ' + hit.sector + '<br/>' +
        '<span style="color:#6b7280">Exits:</span> ' + hit.exits.join(', ') + '<br/>' +
        '<span style="color:#6b7280">VNUM:</span> ' + hit.vnum;
      // Double-click portal room to switch to that zone
      if (isPortal) {
        setTimeout(() => { setActiveZone(hit.zone); }, 300);
      }
    }
  });

  canvas.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - pan.x) / zoom;
    const my = (e.clientY - rect.top - pan.y) / zoom;
    const hit = hitTest(mx, my);
    if (hit && state.player) {
      computePath(state.player.vnum, hit.vnum);
    }
  });

  const computePath = (startVnum, endVnum) => {
    pathRooms.clear();
    if (startVnum === endVnum) { pathInfo.classList.add('hidden'); return; }
    const roomMap = new Map();
    state.rooms.forEach(r => roomMap.set(r.vnum, r));
    const coordMap = new Map();
    state.rooms.forEach(r => coordMap.set(r.x + ',' + r.y + ',' + r.z, r));
    const visited = new Set([startVnum]);
    const queue = [[startVnum, [startVnum]]];
    let foundPath = null;
    while (queue.length > 0) {
      const [current, path] = queue.shift();
      const room = roomMap.get(current);
      if (!room) continue;
      for (const dir of room.exits) {
        const off = dirOffsets[dir];
        if (!off) continue;
        const neighbor = coordMap.get((room.x + off[0]) + ',' + (room.y + off[1]) + ',' + (room.z + off[2]));
        if (!neighbor || visited.has(neighbor.vnum)) continue;
        const newPath = [...path, neighbor.vnum];
        if (neighbor.vnum === endVnum) { foundPath = newPath; break; }
        visited.add(neighbor.vnum);
        queue.push([neighbor.vnum, newPath]);
      }
      if (foundPath) break;
    }
    if (foundPath) {
      foundPath.forEach(v => pathRooms.add(v));
      const dest = roomMap.get(endVnum);
      pathInfo.innerHTML =
        '<div class="path-title">\u{1F9ED} Path to ' + (dest ? dest.name : 'destination') + '</div>' +
        '<div class="path-steps">' + (foundPath.length - 1) + ' rooms away</div>';
      pathInfo.classList.remove('hidden');
    } else {
      pathInfo.innerHTML = '<div class="path-title">\u274C No path found</div>';
      pathInfo.classList.remove('hidden');
    }
  };

  const roundRect = (x, y, w, h, r) => {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
  };

  const render = () => {
    pan.x = lerp(pan.x, targetPan.x, 0.12);
    pan.y = lerp(pan.y, targetPan.y, 0.12);
    zoom = lerp(zoom, targetZoom, 0.1);
    pulsePhase += 0.06;
    const now = Date.now();
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#050709';
    ctx.fillRect(0, 0, w, h);
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.02)';
    ctx.lineWidth = 1;
    const gridSize = ROOM_SPACING;
    const startX = Math.floor(-pan.x / zoom / gridSize) * gridSize - gridSize;
    const startY = Math.floor(-pan.y / zoom / gridSize) * gridSize - gridSize;
    const endX = startX + w / zoom + gridSize * 2;
    const endY = startY + h / zoom + gridSize * 2;
    for (let gx = startX; gx < endX; gx += gridSize) { ctx.beginPath(); ctx.moveTo(gx, startY); ctx.lineTo(gx, endY); ctx.stroke(); }
    for (let gy = startY; gy < endY; gy += gridSize) { ctx.beginPath(); ctx.moveTo(startX, gy); ctx.lineTo(endX, gy); ctx.stroke(); }

    const visibleAll = getVisibleRooms();
    const rooms = visibleAll.filter(r => r.z === selectedZ);
    const frontier = state.frontier.filter(r => r.z === selectedZ);
    const roomMap = new Map();
    const coordMap = new Map();
    rooms.forEach(r => { roomMap.set(r.vnum, r); coordMap.set(r.x + ',' + r.y + ',' + r.z, r); });

    // Zone boundaries
    if (showZones && state.zones.length > 0) {
      const zoneRooms = {};
      rooms.forEach(r => { if (!zoneRooms[r.zone]) zoneRooms[r.zone] = []; zoneRooms[r.zone].push(r); });
      Object.entries(zoneRooms).forEach(([zoneId, zRooms]) => {
        if (zRooms.length < 2) return;
        const zid = parseInt(zoneId);
        const color = getZoneColor(zid);
        const isActive = activeZone === null || activeZone === zid;
        const xs = zRooms.map(r => r.x * ROOM_SPACING);
        const ys = zRooms.map(r => r.y * ROOM_SPACING);
        const minX = Math.min(...xs) - ROOM_SIZE;
        const maxX = Math.max(...xs) + ROOM_SIZE;
        const minY = Math.min(...ys) - ROOM_SIZE;
        const maxY = Math.max(...ys) + ROOM_SIZE;
        ctx.strokeStyle = color + (isActive ? '40' : '20');
        ctx.fillStyle = color + (isActive ? '08' : '04');
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        roundRect(minX, minY, maxX - minX, maxY - minY, 16);
        ctx.fill(); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = color + (isActive ? 'aa' : '44');
        ctx.font = 'bold 11px Inter, system-ui';
        ctx.textAlign = 'left'; ctx.textBaseline = 'top';
        const zone = state.zones.find(z => z.id === zid);
        if (zone) ctx.fillText(zone.name, minX + 8, minY + 6);
      });
    }

    // Fog of war
    if (showFog) {
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(startX, startY, endX - startX, endY - startY);
      ctx.globalCompositeOperation = 'destination-out';
      rooms.forEach(room => {
        const px = room.x * ROOM_SPACING;
        const py = room.y * ROOM_SPACING;
        const revealTime = revealed.get(room.vnum) || now;
        const age = Math.min((now - revealTime) / 500, 1);
        const radius = (ROOM_SPACING * 0.8) * age;
        const grad = ctx.createRadialGradient(px, py, 0, px, py, radius);
        grad.addColorStop(0, 'rgba(0,0,0,1)');
        grad.addColorStop(0.7, 'rgba(0,0,0,0.8)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath(); ctx.arc(px, py, radius, 0, Math.PI * 2); ctx.fill();
      });
      ctx.globalCompositeOperation = 'source-over';
    }

    // Connections
    ctx.lineCap = 'round';
    const drawn = new Set();
    const oneWayDrawn = new Set();
    const drawArrow = (fromX, fromY, toX, toY, color) => {
      const headLen = 12;
      const angle = Math.atan2(toY - fromY, toX - fromX);
      const arrowX = fromX + (toX - fromX) * 0.65;
      const arrowY = fromY + (toY - fromY) * 0.65;
      ctx.save(); ctx.fillStyle = color; ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(arrowX - headLen * Math.cos(angle - Math.PI / 6), arrowY - headLen * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(arrowX - headLen * Math.cos(angle + Math.PI / 6), arrowY - headLen * Math.sin(angle + Math.PI / 6));
      ctx.closePath(); ctx.fill(); ctx.restore();
    };

    rooms.forEach(room => {
      const oneWay = room.oneWayExits || [];
      room.exits.forEach(dir => {
        const off = dirOffsets[dir];
        if (!off) return;
        const target = coordMap.get((room.x + off[0]) + ',' + (room.y + off[1]) + ',' + (room.z + off[2]));
        if (!target) return;
        const isOneWay = oneWay.includes(dir);
        const isCrossZone = room.zone !== target.zone;
        const isPath = pathRooms.has(room.vnum) && pathRooms.has(target.vnum);
        if (!isOneWay) {
          const pair = room.vnum < target.vnum ? room.vnum + '-' + target.vnum : target.vnum + '-' + room.vnum;
          if (drawn.has(pair)) return;
          drawn.add(pair);
        } else {
          const key = room.vnum + '->' + target.vnum;
          if (oneWayDrawn.has(key)) return;
          oneWayDrawn.add(key);
        }
        const x1 = room.x * ROOM_SPACING, y1 = room.y * ROOM_SPACING;
        const x2 = target.x * ROOM_SPACING, y2 = target.y * ROOM_SPACING;
        ctx.lineWidth = isPath ? 5 : (isCrossZone ? 4 : 3);
        let lineColor;
        if (isPath) {
          ctx.strokeStyle = '#22c55e'; ctx.shadowColor = '#22c55e'; ctx.shadowBlur = 10;
          lineColor = '#22c55e';
        } else if (isCrossZone) {
          // Portal connections: dashed purple/pink
          ctx.strokeStyle = '#c084fc';
          ctx.setLineDash([8, 6]);
          ctx.shadowBlur = 0;
          lineColor = '#c084fc';
        } else if (isOneWay) {
          ctx.strokeStyle = '#f59e0b'; ctx.shadowBlur = 0; lineColor = '#f59e0b';
        } else {
          const grad = ctx.createLinearGradient(x1, y1, x2, y2);
          grad.addColorStop(0, 'rgba(99,102,241,0.4)');
          grad.addColorStop(1, 'rgba(168,85,247,0.4)');
          ctx.strokeStyle = grad; ctx.shadowBlur = 0;
          lineColor = 'rgba(168,85,247,0.6)';
        }
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        ctx.shadowBlur = 0; ctx.setLineDash([]);
        if (isOneWay) drawArrow(x1, y1, x2, y2, lineColor);
      });
    });

    // Rooms
    rooms.forEach(room => {
      const px = room.x * ROOM_SPACING;
      const py = room.y * ROOM_SPACING;
      const isHovered = hoveredRoom && hoveredRoom.vnum === room.vnum;
      const isSelected = selectedRoom && selectedRoom.vnum === room.vnum;
      const isPath = pathRooms.has(room.vnum);
      const zoneColor = getZoneColor(room.zone);
      const isPortalGhost = activeZone !== null && room.zone !== activeZone;

      if (!revealed.has(room.vnum)) revealed.set(room.vnum, now);
      const revealAge = Math.min((now - revealed.get(room.vnum)) / 400, 1);
      const scale = 0.3 + revealAge * 0.7;

      ctx.save();
      ctx.translate(px, py);
      ctx.scale(scale, scale);
      if (isPortalGhost) ctx.globalAlpha = 0.5;

      ctx.shadowColor = isPath ? '#22c55e' : (isHovered ? zoneColor : 'rgba(0,0,0,0.6)');
      ctx.shadowBlur = isHovered || isPath ? 24 : 16;
      ctx.shadowOffsetY = 4;

      const grad = ctx.createLinearGradient(-ROOM_SIZE/2, -ROOM_SIZE/2, ROOM_SIZE/2, ROOM_SIZE/2);
      if (isPath) { grad.addColorStop(0, '#22c55e'); grad.addColorStop(1, '#15803d'); }
      else { grad.addColorStop(0, zoneColor); grad.addColorStop(1, zoneColor + '60'); }
      ctx.fillStyle = grad;
      roundRect(-ROOM_SIZE/2, -ROOM_SIZE/2, ROOM_SIZE, ROOM_SIZE, ROOM_RADIUS);
      ctx.fill();

      ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      ctx.strokeStyle = isHovered || isSelected ? '#fff' : (isPath ? '#4ade80' : zoneColor + 'aa');
      ctx.lineWidth = isHovered || isSelected ? 3 : 1.5;
      roundRect(-ROOM_SIZE/2, -ROOM_SIZE/2, ROOM_SIZE, ROOM_SIZE, ROOM_RADIUS);
      ctx.stroke();

      // Portal diamond overlay
      if (isPortalGhost) {
        ctx.fillStyle = '#c084fc';
        ctx.font = '14px system-ui';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('\u{1F300}', 0, 2);
      } else if (useIcons && room.icon) {
        ctx.font = '20px system-ui';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillStyle = '#fff';
        ctx.fillText(room.icon, 0, 2);
      } else {
        ctx.fillStyle = '#0a0e14';
        ctx.font = 'bold 16px system-ui';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(room.symbol, 0, 2);
      }

      ctx.restore();
    });

    // Vertical exit indicators
    const verticalExitRooms = rooms.filter(r => r.exits && (r.exits.includes('up') || r.exits.includes('down')));
    // Frontier
    frontier.forEach(room => {
      const px = room.x * ROOM_SPACING;
      const py = room.y * ROOM_SPACING;
      if (room.deathtrap) {
        // Deathtrap frontier - red dashed border with skull
        ctx.strokeStyle = 'rgba(239,68,68,0.6)'; ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        roundRect(px - ROOM_SIZE/2 + 4, py - ROOM_SIZE/2 + 4, ROOM_SIZE - 8, ROOM_SIZE - 8, ROOM_RADIUS - 2);
        ctx.stroke(); ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(239,68,68,0.7)';
        ctx.font = 'bold 20px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('💀', px, py + 2);
      } else {
        // Normal frontier - gray dashed border with ?
        ctx.strokeStyle = 'rgba(100,116,139,0.3)'; ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        roundRect(px - ROOM_SIZE/2 + 4, py - ROOM_SIZE/2 + 4, ROOM_SIZE - 8, ROOM_SIZE - 8, ROOM_RADIUS - 2);
        ctx.stroke(); ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(100,116,139,0.5)';
        ctx.font = 'bold 18px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('?', px, py + 2);
      }
    });

    // Player
    if (state.player && state.player.z === selectedZ) {
      const px = state.player.x * ROOM_SPACING;
      const py = state.player.y * ROOM_SPACING;
      const pulse = Math.sin(pulsePhase) * 0.35 + 0.65;
      const pulseSize = 12 + Math.sin(pulsePhase * 1.3) * 4;
      for (let i = 3; i >= 0; i--) {
        ctx.fillStyle = 'rgba(251,191,36,' + (0.08 * pulse * (4 - i)) + ')';
        ctx.beginPath(); ctx.arc(px, py, pulseSize + 12 + i * 8, 0, Math.PI * 2); ctx.fill();
      }
      ctx.shadowColor = '#f59e0b'; ctx.shadowBlur = 30 * pulse;
      const pGrad = ctx.createRadialGradient(px, py, 0, px, py, pulseSize);
      pGrad.addColorStop(0, '#fef3c7'); pGrad.addColorStop(0.4, '#fbbf24');
      pGrad.addColorStop(0.8, '#f59e0b'); pGrad.addColorStop(1, '#b45309');
      ctx.fillStyle = pGrad;
      ctx.beginPath(); ctx.arc(px, py, pulseSize, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#1c1917'; ctx.font = 'bold 14px system-ui';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('@', px, py + 1);
    }

    // Up/down indicators
    verticalExitRooms.forEach(room => {
      const px = room.x * ROOM_SPACING;
      const py = room.y * ROOM_SPACING;
      ctx.font = 'bold 11px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      if (room.exits.includes('up')) {
        const ux = px + ROOM_SIZE/2 - 2, uy = py - ROOM_SIZE/2 + 2;
        ctx.fillStyle = '#22d3ee'; ctx.beginPath(); ctx.arc(ux, uy, 8, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#0a0e14'; ctx.fillText('\u2191', ux, uy + 1);
      }
      if (room.exits.includes('down')) {
        const dx = px + ROOM_SIZE/2 - 2, dy = py + ROOM_SIZE/2 - 2;
        ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.arc(dx, dy, 9, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#fff'; ctx.fillText('\u2193', dx, dy + 1);
      }
    });

    ctx.restore();
    renderMinimap(rooms);
    requestAnimationFrame(render);
  };

  const renderMinimap = (rooms) => {
    const mw = minimap.clientWidth;
    const mh = minimap.clientHeight;
    miniCtx.clearRect(0, 0, mw, mh);
    if (rooms.length === 0) return;
    miniCtx.fillStyle = 'rgba(8,11,16,0.95)';
    miniCtx.fillRect(0, 0, mw, mh);
    const xs = rooms.map(r => r.x), ys = rooms.map(r => r.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const width = maxX - minX + 1, height = maxY - minY + 1;
    const scale = Math.min((mw - 32) / (width * 10), (mh - 32) / (height * 10));
    miniCtx.save(); miniCtx.translate(16, 16); miniCtx.scale(scale, scale);
    if (showZones) {
      const zoneRooms = {};
      rooms.forEach(r => { if (!zoneRooms[r.zone]) zoneRooms[r.zone] = []; zoneRooms[r.zone].push(r); });
      Object.entries(zoneRooms).forEach(([zid, zRooms]) => {
        miniCtx.fillStyle = getZoneColor(parseInt(zid)) + '20';
        zRooms.forEach(r => { miniCtx.fillRect((r.x - minX) * 10, (r.y - minY) * 10, 8, 8); });
      });
    }
    rooms.forEach(room => {
      const color = pathRooms.has(room.vnum) ? '#22c55e' : getZoneColor(room.zone);
      miniCtx.fillStyle = color;
      miniCtx.beginPath(); miniCtx.arc((room.x - minX) * 10 + 4, (room.y - minY) * 10 + 4, 3, 0, Math.PI * 2); miniCtx.fill();
    });
    if (state.player && state.player.z === selectedZ) {
      const pulse = Math.sin(pulsePhase) * 0.3 + 0.7;
      miniCtx.fillStyle = 'rgba(251,191,36,' + pulse + ')';
      miniCtx.beginPath(); miniCtx.arc((state.player.x - minX) * 10 + 4, (state.player.y - minY) * 10 + 4, 6, 0, Math.PI * 2); miniCtx.fill();
    }
    miniCtx.strokeStyle = 'rgba(255,255,255,0.25)'; miniCtx.lineWidth = 1.5 / scale;
    const vpX = (-pan.x / zoom / ROOM_SPACING - minX) * 10;
    const vpY = (-pan.y / zoom / ROOM_SPACING - minY) * 10;
    const vpW = (canvas.clientWidth / zoom / ROOM_SPACING) * 10;
    const vpH = (canvas.clientHeight / zoom / ROOM_SPACING) * 10;
    miniCtx.strokeRect(vpX, vpY, vpW, vpH);
    miniCtx.restore();
  };

  // Zone overview mini-map (all zones as clusters)
  const renderZoneOverview = () => {
    const ow = zoneOverview.clientWidth;
    const oh = zoneOverview.clientHeight;
    zoCtx.clearRect(0, 0, ow, oh);
    zoCtx.fillStyle = 'rgba(8,11,16,0.95)';
    zoCtx.fillRect(0, 0, ow, oh);
    if (state.zones.length === 0) return;

    // Compute zone centroids from all rooms
    const zoneCentroids = {};
    const zoneCounts = {};
    state.rooms.forEach(r => {
      if (!zoneCentroids[r.zone]) { zoneCentroids[r.zone] = { x: 0, y: 0 }; zoneCounts[r.zone] = 0; }
      zoneCentroids[r.zone].x += r.x;
      zoneCentroids[r.zone].y += r.y;
      zoneCounts[r.zone]++;
    });
    const centroids = [];
    Object.keys(zoneCentroids).forEach(zid => {
      const n = zoneCounts[zid];
      centroids.push({ zone: parseInt(zid), x: zoneCentroids[zid].x / n, y: zoneCentroids[zid].y / n, count: n });
    });
    if (centroids.length === 0) return;

    const xs = centroids.map(c => c.x), ys = centroids.map(c => c.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const rangeX = maxX - minX || 1, rangeY = maxY - minY || 1;
    const pad = 20;
    const scaleX = (ow - pad * 2) / rangeX;
    const scaleY = (oh - pad * 2) / rangeY;
    const sc = Math.min(scaleX, scaleY);

    // Draw cross-zone connections
    zoCtx.strokeStyle = 'rgba(255,255,255,0.1)';
    zoCtx.lineWidth = 1;
    const connectedPairs = new Set();
    crossZoneExits.forEach(cx => {
      const pair = Math.min(cx.fromZone, cx.toZone) + '-' + Math.max(cx.fromZone, cx.toZone);
      if (connectedPairs.has(pair)) return;
      connectedPairs.add(pair);
      const from = centroids.find(c => c.zone === cx.fromZone);
      const to = centroids.find(c => c.zone === cx.toZone);
      if (!from || !to) return;
      zoCtx.beginPath();
      zoCtx.moveTo(pad + (from.x - minX) * sc, pad + (from.y - minY) * sc);
      zoCtx.lineTo(pad + (to.x - minX) * sc, pad + (to.y - minY) * sc);
      zoCtx.stroke();
    });

    // Store centroid positions for click detection
    zoneOverview._centroids = [];
    centroids.forEach(c => {
      const cx = pad + (c.x - minX) * sc;
      const cy = pad + (c.y - minY) * sc;
      const color = getZoneColor(c.zone);
      const isActive = activeZone === c.zone;
      const radius = Math.max(4, Math.min(12, Math.sqrt(c.count) * 1.5));
      zoneOverview._centroids.push({ zone: c.zone, cx, cy, radius });

      if (isActive) {
        zoCtx.fillStyle = color + '40';
        zoCtx.beginPath(); zoCtx.arc(cx, cy, radius + 6, 0, Math.PI * 2); zoCtx.fill();
      }
      zoCtx.fillStyle = isActive ? color : color + '99';
      zoCtx.beginPath(); zoCtx.arc(cx, cy, radius, 0, Math.PI * 2); zoCtx.fill();
      if (isActive) {
        zoCtx.strokeStyle = '#fff'; zoCtx.lineWidth = 2;
        zoCtx.beginPath(); zoCtx.arc(cx, cy, radius, 0, Math.PI * 2); zoCtx.stroke();
      }
    });

    // Title
    zoCtx.fillStyle = 'rgba(255,255,255,0.4)';
    zoCtx.font = '10px Inter, system-ui';
    zoCtx.textAlign = 'left'; zoCtx.textBaseline = 'top';
    zoCtx.fillText('Zone Overview' + (activeZone !== null ? ' \u2022 ' + getZoneName(activeZone) : ' \u2022 All'), 6, 4);
  };

  // Click on zone overview to switch zones
  zoneOverview.addEventListener('click', (e) => {
    const rect = zoneOverview.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const centroids = zoneOverview._centroids || [];
    let clicked = null;
    for (const c of centroids) {
      if (Math.hypot(mx - c.cx, my - c.cy) < c.radius + 4) { clicked = c.zone; break; }
    }
    if (clicked !== null) {
      setActiveZone(clicked === activeZone ? null : clicked);
    } else {
      setActiveZone(null);
    }
  });

  const updateUI = () => {
    // Level select
    const visibleRooms = getVisibleRooms();
    const zs = [...new Set(visibleRooms.map(r => r.z))].sort((a,b) => a - b);
    zSelect.innerHTML = zs.map(z =>
      '<option value="' + z + '"' + (z === selectedZ ? ' selected' : '') + '>Level ' + z + '</option>'
    ).join('');

    // Zone info
    if (state.player && state.rooms.length > 0) {
      const playerRoom = state.rooms.find(r => r.vnum === state.player.vnum);
      if (playerRoom) {
        const zone = state.zones.find(z => z.id === playerRoom.zone);
        const zoneRoomCount = state.rooms.filter(r => r.zone === playerRoom.zone).length;
        zoneInfo.innerHTML =
          '<div class="zone-name" style="color:' + (zone ? zone.color : '#a5b4fc') + '">' +
          (playerRoom.zoneName || 'Unknown Zone') + '</div>' +
          '<div class="zone-stats">' + zoneRoomCount + ' rooms explored' +
          (activeZone !== null ? ' \u2022 <span style="color:#c084fc">Filtering: ' + getZoneName(activeZone) + '</span>' : '') +
          '</div>';
      }
    }

    // Zone filter list
    if (state.zones.length > 0) {
      const zoneCounts = {};
      state.rooms.forEach(r => { zoneCounts[r.zone] = (zoneCounts[r.zone] || 0) + 1; });
      let html = '<div class="zone-filter-item' + (activeZone === null ? ' active' : '') + '" data-zone="all">' +
        '<span class="zf-dot" style="background:linear-gradient(135deg,#6366f1,#a855f7)"></span>' +
        '<span class="zf-name">All Zones</span>' +
        '<span class="zf-count">' + state.rooms.length + '</span></div>';
      // Sort by room count descending
      const sorted = [...state.zones].sort((a, b) => (zoneCounts[b.id] || 0) - (zoneCounts[a.id] || 0));
      sorted.forEach(z => {
        const count = zoneCounts[z.id] || 0;
        const isPlayerZone = state.player && state.rooms.find(r => r.vnum === state.player.vnum && r.zone === z.id);
        html += '<div class="zone-filter-item' + (activeZone === z.id ? ' active' : '') + '" data-zone="' + z.id + '">' +
          '<span class="zf-dot" style="background:' + z.color + '"></span>' +
          '<span class="zf-name">' + (isPlayerZone ? '\u{1F4CD} ' : '') + z.name + '</span>' +
          '<span class="zf-count">' + count + '</span></div>';
      });
      zoneFilterList.innerHTML = html;
      // Attach click handlers
      zoneFilterList.querySelectorAll('.zone-filter-item').forEach(el => {
        el.addEventListener('click', () => {
          const zv = el.dataset.zone;
          setActiveZone(zv === 'all' ? null : parseInt(zv));
        });
      });
    }

    // Zone list (bottom)
    if (state.zones.length > 0) {
      zoneList.innerHTML = '<h3>Zones Explored</h3>' + state.zones.map(z =>
        '<div class="zone-item' + (activeZone === z.id ? ' active' : '') + '" data-zone="' + z.id + '"><span class="zone-dot" style="background:' + z.color + '"></span>' + z.name + '</div>'
      ).join('');
      zoneList.querySelectorAll('.zone-item').forEach(el => {
        el.addEventListener('click', () => {
          const zv = parseInt(el.dataset.zone);
          setActiveZone(zv === activeZone ? null : zv);
        });
      });
    }
  };

  zSelect.addEventListener('change', (e) => { selectedZ = parseInt(e.target.value, 10); });

  const urlParams = new URLSearchParams(window.location.search);
  const player = urlParams.get('player') || '';
  const debugEnabled = urlParams.get('debug') === '1';
  if (debugPanel && debugEnabled) debugPanel.classList.remove('hidden');
  if (!player) playerWarning.classList.remove('hidden');

  const applyState = (data) => {
    if (data.type === 'map_data') {
      state = data;
      buildCrossZoneIndex();
      if (state.player) {
        selectedZ = state.player.z;
        // Default to player's current zone on first load or zone change
        const playerRoom = state.rooms.find(r => r.vnum === state.player.vnum);
        if (playerRoom && state.rooms.length > 50) {
          // Auto-switch zone filter when player changes zones
          if (activeZone === null || (playerRoom.zone !== activeZone)) {
            activeZone = playerRoom.zone;
          }
        }
        // Center on player or zone centroid
        if (activeZone !== null) {
          const zoneRooms = state.rooms.filter(r => r.zone === activeZone);
          if (zoneRooms.length > 0) {
            // Center on player if in this zone, else zone centroid
            if (playerRoom && playerRoom.zone === activeZone) {
              targetPan.x = canvas.clientWidth / 2 - (state.player.x * ROOM_SPACING * zoom);
              targetPan.y = canvas.clientHeight / 2 - (state.player.y * ROOM_SPACING * zoom);
            } else {
              const cx = zoneRooms.reduce((s, r) => s + r.x, 0) / zoneRooms.length;
              const cy = zoneRooms.reduce((s, r) => s + r.y, 0) / zoneRooms.length;
              targetPan.x = canvas.clientWidth / 2 - (cx * ROOM_SPACING * zoom);
              targetPan.y = canvas.clientHeight / 2 - (cy * ROOM_SPACING * zoom);
            }
          }
        } else {
          targetPan.x = canvas.clientWidth / 2 - (state.player.x * ROOM_SPACING * zoom);
          targetPan.y = canvas.clientHeight / 2 - (state.player.y * ROOM_SPACING * zoom);
        }
      }
      updateUI();
      renderZoneOverview();
      markPayload();
    }
  };

  let pollTimer = null;
  const startPolling = () => {
    if (pollTimer || !player) return;
    setWsStatus('polling', 'polling');
    const fetchState = () => {
      fetch('/state?player=' + encodeURIComponent(player))
        .then(r => { setDebug(debugPoll, 'HTTP ' + r.status); return r.ok ? r.json() : null; })
        .then(data => { if (data) applyState(data); })
        .catch(() => setDebugError('poll error'));
    };
    fetchState();
    pollTimer = setInterval(fetchState, 2000);
  };
  const stopPolling = () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } };

  let ws = null;
  let wsConnected = false;
  let reconnectAttempts = 0;
  const maxReconnectDelay = 30000;

  const connectWebSocket = () => {
    setWsStatus('connecting', 'connecting');
    ws = new WebSocket('ws://' + window.location.host);
    const fallbackTimer = setTimeout(() => { if (!wsConnected) startPolling(); }, 3000);
    ws.addEventListener('open', () => {
      wsConnected = true; reconnectAttempts = 0;
      clearTimeout(fallbackTimer); stopPolling();
      setWsStatus('connected', 'connected');
      if (player) ws.send(JSON.stringify({ type: 'subscribe', player, mode: 'full' }));
    });
    ws.addEventListener('close', () => {
      wsConnected = false;
      setWsStatus('disconnected', 'reconnecting...');
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxReconnectDelay);
      reconnectAttempts++;
      setTimeout(connectWebSocket, delay);
    });
    ws.addEventListener('error', (e) => { console.error('WebSocket error:', e); });
    ws.addEventListener('message', (e) => applyState(JSON.parse(e.data)));
  };

  connectWebSocket();
  render();
})();"""
