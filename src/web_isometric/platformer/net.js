// Misthollow platformer: networking layer.
// Dual sockets: MUD command/output bridge (:4003/ws) + structured map stream (:4001).
// Ported from client2d.html with the same proxy-aware host detection.
(() => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname || 'localhost';
  const isBehindProxy = !window.location.port || window.location.port == 80 || window.location.port == 443;
  const mudHost = isBehindProxy ? host.replace('map.', 'mud.') : host;

  const MH = window.MH = window.MH || {};
  MH.urls = {
    mudWs: isBehindProxy ? `${protocol}//${mudHost}/ws` : `${protocol}//${host}:4003/ws`,
    mapWs: isBehindProxy ? `${protocol}//${host}` : `${protocol}//${host}:4001`,
    state: name => (isBehindProxy ? `/state?player=${encodeURIComponent(name)}`
                                  : `${window.location.protocol}//${host}:4001/state?player=${encodeURIComponent(name)}`),
  };

  // --- tiny event bus ---
  const listeners = {};
  MH.bus = {
    on(event, fn) { (listeners[event] = listeners[event] || []).push(fn); },
    emit(event, payload) {
      for (const fn of (listeners[event] || [])) {
        try { fn(payload); } catch (err) { console.error(`[bus:${event}]`, err); }
      }
    },
  };

  // --- shared state ---
  MH.state = {
    playerName: '',
    playerPassword: '',
    creatingAccount: false,
    isLoggedIn: false,
    loginSequenceStarted: false,
    mudSocket: null,
    mapSocket: null,
    mapResubscribeInterval: null,
    mapRetryTimers: [],
    lastMapDataAt: 0,
    lastPayload: null,
    currentRoom: null,       // current_room block from payload
    player: null,            // player block from payload
    inCombat: false,
    combatPollTimer: null,
    pendingMove: null,       // {dir, sentAt} while a movement command is in flight
  };

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function decodeHtmlEntities(text) {
    const el = document.createElement('textarea');
    el.innerHTML = String(text || '');
    return el.value;
  }
  MH.stripServerMarkup = function stripServerMarkup(text) {
    return decodeHtmlEntities(
      String(text || '')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<\/p>/gi, '\n')
        .replace(/<[^>]+>/g, '')
    ).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  };

  // --- command sending ---
  MH.sendCommand = function sendCommand(command, echo = true) {
    const trimmed = String(command || '').trim();
    const sock = MH.state.mudSocket;
    if (!trimmed || !sock || sock.readyState !== WebSocket.OPEN) return false;
    sock.send(trimmed);
    if (echo) MH.bus.emit('terminal.echo', trimmed);
    return true;
  };

  // --- scripted login (same dance as client2d) ---
  async function runLoginSequence() {
    const st = MH.state;
    if (st.loginSequenceStarted || !st.mudSocket || st.mudSocket.readyState !== WebSocket.OPEN) return;
    st.loginSequenceStarted = true;
    MH.bus.emit('login.status', st.creatingAccount ? 'Forging a new soul…' : 'Opening the gate…');
    await sleep(500);
    MH.sendCommand(st.playerName, false);
    await sleep(500);
    if (st.creatingAccount) {
      MH.sendCommand('y', false);
      await sleep(500);
      MH.sendCommand(st.playerPassword, false);
      await sleep(500);
      MH.sendCommand(st.playerPassword, false);
    } else {
      MH.sendCommand(st.playerPassword, false);
    }
  }

  const ROOM_LOGIN_PATTERNS = [/^\[[0-9]+\]\s+/m, /\bExits?:\b/i, /You are in/i, /Obvious exits:/i];

  // pre-game prompts the scripted login should answer on the player's behalf
  const LOGIN_PROMPT_RESPONDERS = [
    { test: /create an account for multiple characters\?\s*\(y\/n\)/i, send: 'n' },
    { test: /press (?:enter|return) to continue/i, send: '' },
    { test: /\[\s*press (?:enter|return)\s*\]/i, send: '' },
  ];
  function answerLoginPrompts(text) {
    if (MH.state.isLoggedIn) return;
    for (const { test, send } of LOGIN_PROMPT_RESPONDERS) {
      if (test.test(text)) {
        setTimeout(() => {
          const sock = MH.state.mudSocket;
          if (sock && sock.readyState === WebSocket.OPEN) sock.send(send);
        }, 300);
        return;
      }
    }
  }
  function inferLoginSuccess(text) {
    const st = MH.state;
    if (st.isLoggedIn) return;
    // mapsync is the authoritative signal; room-looking output is the fallback.
    // (a bare /welcome/i match would false-positive on the splash banner)
    if (ROOM_LOGIN_PATTERNS.some(p => p.test(text))) {
      st.isLoggedIn = true;
      MH.bus.emit('login.success', st.playerName);
    }
  }

  // --- map socket ---
  function stopResubscribe() {
    if (MH.state.mapResubscribeInterval) {
      clearInterval(MH.state.mapResubscribeInterval);
      MH.state.mapResubscribeInterval = null;
    }
  }
  function clearRetryTimers() {
    MH.state.mapRetryTimers.forEach(t => clearTimeout(t));
    MH.state.mapRetryTimers = [];
  }
  function sendMapSubscribe() {
    const st = MH.state;
    if (!st.playerName || !st.mapSocket || st.mapSocket.readyState !== WebSocket.OPEN) return;
    st.mapSocket.send(JSON.stringify({ type: 'subscribe', player: st.playerName, mode: 'full' }));
  }
  function startResubscribe() {
    stopResubscribe();
    MH.state.mapResubscribeInterval = setInterval(() => {
      const st = MH.state;
      if (!st.mapSocket || st.mapSocket.readyState !== WebSocket.OPEN) return;
      if (st.lastPayload && (Date.now() - st.lastMapDataAt) < 5000) return;
      sendMapSubscribe();
    }, 2000);
  }

  function handleMapData(payload) {
    const st = MH.state;
    clearRetryTimers();
    st.lastMapDataAt = Date.now();
    st.lastPayload = payload;
    if (payload.player) st.player = payload.player;
    if (payload.current_room) st.currentRoom = payload.current_room;
    // authoritative combat state rides every payload - no more stuck chips
    if (payload.player && payload.player.in_combat != null) MH.setCombat(!!payload.player.in_combat);
    if (st.player && st.lastPayload) stopResubscribe();
    MH.bus.emit('map', payload);
  }

  // server pushes these every combat round: vitals + current-room entities
  function handleCombatUpdate(payload) {
    const st = MH.state;
    if (st.player && payload.player) Object.assign(st.player, payload.player);
    if (payload.in_combat != null) MH.setCombat(!!payload.in_combat);
    MH.bus.emit('combat.update', payload);
  }

  function ensureMapSocket() {
    const st = MH.state;
    if (!st.playerName) return;
    if (st.mapSocket && (st.mapSocket.readyState === WebSocket.OPEN || st.mapSocket.readyState === WebSocket.CONNECTING)) return;
    st.mapSocket = new WebSocket(MH.urls.mapWs);
    st.mapSocket.addEventListener('open', () => {
      sendMapSubscribe();
      clearRetryTimers();
      [500, 1500, 3000].forEach(delay => {
        st.mapRetryTimers.push(setTimeout(() => {
          if (!st.lastPayload || (Date.now() - st.lastMapDataAt) > 2000) sendMapSubscribe();
        }, delay));
      });
      startResubscribe();
    });
    st.mapSocket.addEventListener('message', event => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'map_data') handleMapData(payload);
        else if (payload.type === 'combat_update') handleCombatUpdate(payload);
        else if (payload.type === 'mob_move') MH.bus.emit('mob.move', payload);
        else if (payload.type === 'ambient') MH.bus.emit('ambient.echo', payload.text || '');
      } catch (err) {
        console.warn('map socket parse error', err);
      }
    });
    const onDown = () => { clearRetryTimers(); stopResubscribe(); setTimeout(ensureMapSocket, 2000); };
    st.mapSocket.addEventListener('close', onDown);
    st.mapSocket.addEventListener('error', () => {});
  }

  // --- combat HP polling: map pushes only fire on movement, so poll /state mid-fight ---
  MH.setCombat = function setCombat(on) {
    const st = MH.state;
    if (st.inCombat === on) return;
    st.inCombat = on;
    MH.bus.emit('combat.state', on);
    // fallback only: the server now pushes combat_update every round,
    // so this just guards against missed frames
    if (on && !st.combatPollTimer) {
      st.combatPollTimer = setInterval(async () => {
        if (!st.playerName) return;
        try {
          const res = await fetch(MH.urls.state(st.playerName));
          if (res.ok) handleMapData(await res.json());
        } catch (_) { /* server hiccup; next tick retries */ }
      }, 4000);
    } else if (!on && st.combatPollTimer) {
      clearInterval(st.combatPollTimer);
      st.combatPollTimer = null;
    }
  };
  // One-shot refresh (used after deaths, purchases, etc.)
  MH.refreshState = async function refreshState() {
    const st = MH.state;
    if (!st.playerName) return;
    try {
      const res = await fetch(MH.urls.state(st.playerName));
      if (res.ok) handleMapData(await res.json());
    } catch (_) {}
  };

  // --- MUD socket ---
  function handleMudMessage(raw) {
    let payload;
    try { payload = JSON.parse(raw); } catch (_) { payload = { type: 'output', data: raw }; }
    if (payload.type === 'output') {
      const text = MH.stripServerMarkup(payload.data || '');
      MH.bus.emit('terminal.output', { html: payload.data, text });
      const lines = text.split('\n').filter(l => l.trim());
      // chunkLen lets the parser treat short standalone chunks as ambient
      // narrative while ignoring look/score dumps
      for (const line of lines) MH.bus.emit('mud.line', { line, chunkLen: lines.length });
      answerLoginPrompts(text);
      inferLoginSuccess(text);
    } else if (payload.type === 'mapsync') {
      if (payload.player) MH.state.playerName = payload.player;
      if (!MH.state.isLoggedIn) {
        MH.state.isLoggedIn = true;
        MH.bus.emit('login.success', MH.state.playerName);
      }
      ensureMapSocket();
      sendMapSubscribe();
      startResubscribe();
    }
  }

  MH.connect = function connect(name, password, createAccount) {
    const st = MH.state;
    st.playerName = name;
    st.playerPassword = password;
    st.creatingAccount = !!createAccount;
    st.loginSequenceStarted = false;
    st.isLoggedIn = false;
    if (st.mudSocket) { try { st.mudSocket.close(); } catch (_) {} }
    MH.bus.emit('login.status', `Connecting to ${MH.urls.mudWs}…`);
    st.mudSocket = new WebSocket(MH.urls.mudWs);
    st.mudSocket.addEventListener('open', () => runLoginSequence());
    st.mudSocket.addEventListener('message', e => handleMudMessage(e.data));
    st.mudSocket.addEventListener('close', () => MH.bus.emit('login.status', 'World socket closed.'));
    st.mudSocket.addEventListener('error', () => MH.bus.emit('login.error', 'Could not reach the gate. Is the server up?'));
  };
})();
